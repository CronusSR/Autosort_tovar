# restore_detailed_warehouse_analysis.py
"""
Восстановление детального анализа складов с деньгами и подробностями по каждому складу
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

class DetailedWarehouseAnalyzer:
    """
    Детальный анализатор складов с деньгами и индивидуальным анализом каждого склада
    """
    
    def __init__(self):
        # Конфигурация складов из вашего оригинального кода
        self.warehouse_config = {
            'База_Комплект': {
                'name': 'База Склад Фурнитура Комплект',
                'short_name': 'База Комплект',
                'city': 'алматы',
                'type': 'hub'
            },
            'Казыбаева_TRADE': {
                'name': 'Казыбаева Склад Фурнитура TRADE',
                'short_name': 'Казыбаева Склад',
                'city': 'алматы',
                'type': 'warehouse'
            },
            'Казыбаева_магазин': {
                'name': 'ТД Казыбаева ФУРНИТУРА магазин',
                'short_name': 'Казыбаева ТД',
                'city': 'алматы',
                'type': 'store'
            },
            'Барыс_TRADE': {
                'name': 'Барыс Склад Фурнитура TRADE',
                'short_name': 'Барыс',
                'city': 'алматы',
                'type': 'store_warehouse'
            },
            'АО_TRADE': {
                'name': 'АО Склад Фурнитура TRADE',
                'short_name': 'АО Склад',
                'city': 'алматы',
                'type': 'specialized_store'
            },
            'Шымкент_Овощная_база': {
                'name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'short_name': 'Шымкент Склад',
                'city': 'шымкент',
                'type': 'warehouse'
            },
            'Овощная_база_Магазин': {
                'name': '6 Склад фурнитуры "Овощная база" Магазин',
                'short_name': 'Шымкент Магазин',
                'city': 'шымкент',
                'type': 'store'
            },
            'Склад_1': {
                'name': 'склад фурнитура № 1',
                'short_name': 'Астана Склад',
                'city': 'астана',
                'type': 'warehouse'
            },
            'Магазин_фурнитуры': {
                'name': 'Магазин фурнитуры',
                'short_name': 'Астана Магазин',
                'city': 'астана',
                'type': 'store'
            }
        }
        
        self.warehouse_analysis = None
        self.warehouse_recommendations = None
    
    def analyze_warehouse_stock_detailed(self, remains_df, ads_data, store_ads_by_city, min_days=10, max_days=50):
        """
        Детальный анализ складов с учетом ADS данных и цен
        """
        
        if remains_df is None or remains_df.empty:
            return None
        
        print(f"🔄 Начало детального анализа складов")
        print(f"📊 Товаров в остатках: {len(remains_df)}")
        
        # Проверяем наличие ценовых данных
        price_columns = ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']
        has_prices = False
        price_column = None
        
        if ads_data is not None:
            for col in price_columns:
                if col in ads_data.columns:
                    has_prices = True
                    price_column = col
                    print(f"💰 Найдена ценовая колонка: {col}")
                    break
        
        analysis_results = []
        processed_items = 0
        
        for _, item in remains_df.iterrows():
            item_name = item['номенклатура']
            total_stock = item.get('итого_остаток', 0)
            
            # Получаем ADS для товара
            ads_value = 0
            item_price = 0
            
            if ads_data is not None and not ads_data.empty:
                ads_match = ads_data[ads_data['номенклатура'] == item_name]
                if not ads_match.empty:
                    ads_value = ads_match.iloc[0].get('ads', 0)
                    if has_prices and price_column:
                        item_price = ads_match.iloc[0].get(price_column, 0)
            
            item_analysis = {
                'номенклатура': item_name,
                'итого_остаток': total_stock,
                'ads': ads_value,
                'price': item_price,
                'warehouses': {}
            }
            
            # Анализируем каждый склад индивидуально
            for warehouse_key, config in self.warehouse_config.items():
                stock_col = f'{warehouse_key}_остаток'
                current_stock = item.get(stock_col, 0)
                
                if current_stock > 0 or ads_value > 0:  # Анализируем если есть остаток или ADS
                    
                    # Рассчитываем MIN и MAX для склада
                    min_stock = ads_value * min_days if ads_value > 0 else 0
                    max_stock = ads_value * max_days if ads_value > 0 else 0
                    
                    # Дефицит/избыток
                    min_deficit = max(0, min_stock - current_stock)
                    max_deficit = max(0, max_stock - current_stock)
                    
                    # Месяцы запаса
                    months_of_stock = 0
                    if ads_value > 0:
                        months_of_stock = current_stock / (ads_value * 30)
                    elif current_stock > 0:
                        months_of_stock = 999
                    
                    # Статус склада
                    status = self._determine_warehouse_status(current_stock, min_stock, max_stock)
                    
                    # Количество к заказу
                    order_quantity = 0
                    if status in ['critical', 'warning']:
                        order_quantity = max_stock - current_stock
                    
                    # Денежные расчеты
                    min_deficit_cost = min_deficit * item_price if has_prices else 0
                    max_deficit_cost = max_deficit * item_price if has_prices else 0
                    order_cost = order_quantity * item_price if has_prices else 0
                    stock_value = current_stock * item_price if has_prices else 0
                    
                    item_analysis['warehouses'][warehouse_key] = {
                        'name': config['name'],
                        'short_name': config['short_name'],
                        'city': config['city'],
                        'type': config['type'],
                        'current_stock': current_stock,
                        'min_stock': min_stock,
                        'max_stock': max_stock,
                        'min_deficit': min_deficit,
                        'max_deficit': max_deficit,
                        'months_of_stock': months_of_stock,
                        'status': status,
                        'order_quantity': order_quantity,
                        'ads': ads_value,
                        'price': item_price,
                        'min_deficit_cost': min_deficit_cost,
                        'max_deficit_cost': max_deficit_cost,
                        'order_cost': order_cost,
                        'stock_value': stock_value
                    }
            
            analysis_results.append(item_analysis)
            processed_items += 1
            
            if processed_items % 100 == 0:
                print(f"📊 Обработано товаров: {processed_items}")
        
        self.warehouse_analysis = analysis_results
        print(f"✅ Анализ завершен. Обработано товаров: {processed_items}")
        
        return analysis_results
    
    def _determine_warehouse_status(self, current_stock, min_stock, max_stock):
        """Определяет статус склада"""
        
        if current_stock < min_stock * 0.5:
            return 'critical'
        elif current_stock < min_stock:
            return 'warning'
        elif current_stock > max_stock:
            return 'excess'
        else:
            return 'good'
    
    def get_warehouse_recommendations(self):
        """Формирует рекомендации по каждому складу с учетом MIN/MAX"""
        
        if not self.warehouse_analysis:
            return None
        
        warehouse_recommendations = {}
        
        # Инициализируем словари для каждого склада
        for warehouse_key, config in self.warehouse_config.items():
            warehouse_recommendations[warehouse_key] = {
                'name': config['name'],
                'short_name': config['short_name'],
                'city': config['city'],
                'type': config['type'],
                'critical_items': [],
                'warning_items': [],
                'excess_items': [],
                'good_items': [],
                'total_order_value': 0,
                'total_excess_value': 0,
                'total_stock_value': 0,
                'total_min_deficit': 0,
                'total_max_deficit': 0
            }
        
        # Заполняем рекомендации
        for item in self.warehouse_analysis:
            for warehouse_key, warehouse_data in item['warehouses'].items():
                
                if warehouse_key not in warehouse_recommendations:
                    continue
                
                rec = warehouse_recommendations[warehouse_key]
                
                # Накапливаем денежные данные
                rec['total_order_value'] += warehouse_data.get('order_cost', 0)
                rec['total_stock_value'] += warehouse_data.get('stock_value', 0)
                rec['total_min_deficit'] += warehouse_data.get('min_deficit_cost', 0)
                rec['total_max_deficit'] += warehouse_data.get('max_deficit_cost', 0)
                
                item_data = {
                    'item': item['номенклатура'],
                    'current_stock': warehouse_data['current_stock'],
                    'min_stock': warehouse_data['min_stock'],
                    'max_stock': warehouse_data['max_stock'],
                    'min_deficit': warehouse_data['min_deficit'],
                    'max_deficit': warehouse_data['max_deficit'],
                    'months_left': warehouse_data['months_of_stock'],
                    'order_quantity': warehouse_data['order_quantity'],
                    'ads': warehouse_data['ads'],
                    'price': warehouse_data.get('price', 0),
                    'order_cost': warehouse_data.get('order_cost', 0),
                    'stock_value': warehouse_data.get('stock_value', 0)
                }
                
                # Распределяем по категориям
                if warehouse_data['status'] == 'critical':
                    rec['critical_items'].append(item_data)
                elif warehouse_data['status'] == 'warning':
                    rec['warning_items'].append(item_data)
                elif warehouse_data['status'] == 'excess':
                    rec['excess_items'].append(item_data)
                else:
                    rec['good_items'].append(item_data)
        
        # Сортируем товары по денежному дефициту (если есть цены) или по количеству
        for warehouse_key in warehouse_recommendations:
            rec = warehouse_recommendations[warehouse_key]
            
            # Сортируем критичные товары по order_cost (убывание)
            rec['critical_items'].sort(key=lambda x: x.get('order_cost', x['order_quantity']), reverse=True)
            rec['warning_items'].sort(key=lambda x: x.get('order_cost', x['order_quantity']), reverse=True)
            rec['excess_items'].sort(key=lambda x: x.get('stock_value', x['current_stock']), reverse=True)
        
        self.warehouse_recommendations = warehouse_recommendations
        return warehouse_recommendations
    
    def get_warehouse_summary_stats(self):
        """Получает сводную статистику по складам"""
        
        if not self.warehouse_recommendations:
            return None
        
        summary_stats = {}
        
        for warehouse_key, rec in self.warehouse_recommendations.items():
            summary_stats[warehouse_key] = {
                'name': rec['name'],
                'short_name': rec['short_name'],
                'city': rec['city'],
                'type': rec['type'],
                'total_items': len(rec['critical_items']) + len(rec['warning_items']) + len(rec['good_items']) + len(rec['excess_items']),
                'critical_count': len(rec['critical_items']),
                'warning_count': len(rec['warning_items']),
                'good_count': len(rec['good_items']),
                'excess_count': len(rec['excess_items']),
                'total_order_value': rec['total_order_value'],
                'total_stock_value': rec['total_stock_value'],
                'total_min_deficit': rec['total_min_deficit'],
                'total_max_deficit': rec['total_max_deficit']
            }
        
        return summary_stats

def display_detailed_warehouse_analysis(system, analysis_results, recommendations):
    """
    Отображает детальный анализ складов с деньгами и подробностями
    """
    
    st.subheader("📊 Детальный анализ по складам")
    
    if not analysis_results or not recommendations:
        st.error("❌ Нет данных для анализа")
        return
    
    # Получаем сводную статистику
    analyzer = system.warehouse_analyzer
    summary_stats = analyzer.get_warehouse_summary_stats()
    
    # Проверяем наличие цен
    has_prices = False
    if analysis_results:
        for item in analysis_results:
            for warehouse_data in item['warehouses'].values():
                if warehouse_data.get('price', 0) > 0:
                    has_prices = True
                    break
            if has_prices:
                break
    
    # Общая сводка
    st.markdown("### 📈 Общая сводка по складам")
    
    # Создаем таблицу сводки
    summary_data = []
    total_order_value = 0
    total_stock_value = 0
    
    for warehouse_key, stats in summary_stats.items():
        summary_data.append({
            'Склад': stats['short_name'],
            'Город': stats['city'].title(),
            'Тип': stats['type'],
            'Всего товаров': stats['total_items'],
            'Критичные': stats['critical_count'],
            'Внимание': stats['warning_count'],
            'Норма': stats['good_count'],
            'Избыток': stats['excess_count'],
            'К заказу (₸)': f"{stats['total_order_value']:,.0f}" if has_prices else "Нет цен",
            'Стоимость остатков (₸)': f"{stats['total_stock_value']:,.0f}" if has_prices else "Нет цен"
        })
        
        total_order_value += stats['total_order_value']
        total_stock_value += stats['total_stock_value']
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Общие метрики
    col1, col2, col3, col4 = st.columns(4)
    
    total_critical = sum(stats['critical_count'] for stats in summary_stats.values())
    total_warning = sum(stats['warning_count'] for stats in summary_stats.values())
    total_items = sum(stats['total_items'] for stats in summary_stats.values())
    
    with col1:
        st.metric("🔴 Критичные товары", total_critical)
    with col2:
        st.metric("🟡 Требуют внимания", total_warning)
    with col3:
        if has_prices:
            st.metric("💰 К заказу", f"{total_order_value:,.0f} ₸")
        else:
            st.metric("📦 К заказу", "Нет цен")
    with col4:
        if has_prices:
            st.metric("💎 Стоимость остатков", f"{total_stock_value:,.0f} ₸")
        else:
            st.metric("📦 Всего товаров", total_items)
    
    # Детальный анализ по каждому складу
    st.markdown("### 🏪 Детальный анализ по складам")
    
    # Выбор склада для детального анализа
    warehouse_options = {config['short_name']: key for key, config in analyzer.warehouse_config.items()}
    selected_warehouse_name = st.selectbox(
        "Выберите склад для детального анализа:",
        options=list(warehouse_options.keys())
    )
    
    selected_warehouse_key = warehouse_options[selected_warehouse_name]
    warehouse_rec = recommendations[selected_warehouse_key]
    warehouse_stats = summary_stats[selected_warehouse_key]
    
    # Информация о выбранном складе
    st.markdown(f"#### 🏪 {warehouse_rec['name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Всего товаров", warehouse_stats['total_items'])
    with col2:
        st.metric("🔴 Критичные", warehouse_stats['critical_count'])
    with col3:
        st.metric("🟡 Внимание", warehouse_stats['warning_count'])
    with col4:
        if has_prices:
            st.metric("💰 К заказу", f"{warehouse_stats['total_order_value']:,.0f} ₸")
        else:
            st.metric("📦 К заказу", len(warehouse_rec['critical_items']) + len(warehouse_rec['warning_items']))
    
    # Вкладки для разных категорий товаров
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Критичные", "🟡 Внимание", "🟢 Норма", "🔵 Избыток"])
    
    with tab1:
        if warehouse_rec['critical_items']:
            st.write(f"**Критичных товаров: {len(warehouse_rec['critical_items'])}**")
            
            # Создаем DataFrame для критичных товаров
            critical_data = []
            for item in warehouse_rec['critical_items']:
                critical_data.append({
                    'Товар': item['item'][:50] + '...' if len(item['item']) > 50 else item['item'],
                    'Остаток': int(item['current_stock']),
                    'MIN': int(item['min_stock']),
                    'Дефицит': int(item['min_deficit']),
                    'К заказу': int(item['order_quantity']),
                    'ADS': f"{item['ads']:.3f}",
                    'Месяцев': f"{item['months_left']:.1f}" if item['months_left'] < 99 else "999+",
                    'Цена': f"{item['price']:.2f}" if has_prices else "Нет",
                    'Стоимость заказа': f"{item['order_cost']:,.0f}" if has_prices else "Нет"
                })
            
            if critical_data:
                critical_df = pd.DataFrame(critical_data)
                st.dataframe(critical_df, use_container_width=True)
            
            if has_prices:
                total_critical_cost = sum(item['order_cost'] for item in warehouse_rec['critical_items'])
                st.metric("💰 Общая стоимость критичных заказов", f"{total_critical_cost:,.0f} ₸")
        else:
            st.info("✅ Нет критичных товаров на этом складе")
    
    with tab2:
        if warehouse_rec['warning_items']:
            st.write(f"**Товаров требующих внимания: {len(warehouse_rec['warning_items'])}**")
            
            warning_data = []
            for item in warehouse_rec['warning_items']:
                warning_data.append({
                    'Товар': item['item'][:50] + '...' if len(item['item']) > 50 else item['item'],
                    'Остаток': int(item['current_stock']),
                    'MIN': int(item['min_stock']),
                    'Дефицит': int(item['min_deficit']),
                    'К заказу': int(item['order_quantity']),
                    'ADS': f"{item['ads']:.3f}",
                    'Месяцев': f"{item['months_left']:.1f}" if item['months_left'] < 99 else "999+",
                    'Цена': f"{item['price']:.2f}" if has_prices else "Нет",
                    'Стоимость заказа': f"{item['order_cost']:,.0f}" if has_prices else "Нет"
                })
            
            if warning_data:
                warning_df = pd.DataFrame(warning_data)
                st.dataframe(warning_df, use_container_width=True)
        else:
            st.info("✅ Нет товаров требующих внимания на этом складе")
    
    with tab3:
        if warehouse_rec['good_items']:
            st.write(f"**Товаров в норме: {len(warehouse_rec['good_items'])}**")
            st.info(f"Все {len(warehouse_rec['good_items'])} товаров находятся в пределах нормы")
        else:
            st.info("📝 Нет товаров в категории 'норма'")
    
    with tab4:
        if warehouse_rec['excess_items']:
            st.write(f"**Избыточных товаров: {len(warehouse_rec['excess_items'])}**")
            
            excess_data = []
            for item in warehouse_rec['excess_items']:
                excess_data.append({
                    'Товар': item['item'][:50] + '...' if len(item['item']) > 50 else item['item'],
                    'Остаток': int(item['current_stock']),
                    'MAX': int(item['max_stock']),
                    'Избыток': int(item['current_stock'] - item['max_stock']),
                    'ADS': f"{item['ads']:.3f}",
                    'Месяцев': f"{item['months_left']:.1f}" if item['months_left'] < 99 else "999+",
                    'Стоимость остатка': f"{item['stock_value']:,.0f}" if has_prices else "Нет"
                })
            
            if excess_data:
                excess_df = pd.DataFrame(excess_data)
                st.dataframe(excess_df, use_container_width=True)
        else:
            st.info("✅ Нет избыточных товаров на этом складе")

def restore_original_warehouse_analysis_to_system(system):
    """
    Восстанавливает оригинальный детальный анализ складов в системе
    """
    
    # Заменяем анализатор на детальный
    system.warehouse_analyzer = DetailedWarehouseAnalyzer()
    
    # Добавляем метод детального анализа К СИСТЕМЕ
    def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city, min_days=10, max_days=50):
        """Анализ складов с полными деталями"""
        
        try:
            analysis = system.warehouse_analyzer.analyze_warehouse_stock_detailed(
                remains_df, ads_data, store_ads_by_city, min_days, max_days
            )
            
            if analysis:
                recommendations = system.warehouse_analyzer.get_warehouse_recommendations()
                return analysis, recommendations
            
            return None, None
            
        except Exception as e:
            print(f"❌ Ошибка анализа складов: {e}")
            return None, None
    
    # ВАЖНО: Добавляем метод КАК АТРИБУТ системы
    system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
    
    print("✅ Детальный анализ складов восстановлен")
    return True

if __name__ == "__main__":
    print("🏪 Модуль восстановления детального анализа складов")
    print("📋 Использование:")
    print("   from restore_detailed_warehouse_analysis import restore_original_warehouse_analysis_to_system")
    print("   restore_original_warehouse_analysis_to_system(system)")