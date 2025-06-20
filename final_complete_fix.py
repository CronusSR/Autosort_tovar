# final_complete_fix.py
"""
🎯 ФИНАЛЬНОЕ ПОЛНОЕ ИСПРАВЛЕНИЕ
Исправляет ВСЕ: загрузку ADS с ценами + русский интерфейс + анализ складов
"""

import pandas as pd
import streamlit as st
import io
import types
from typing import Dict, List, Any, Optional


def apply_complete_final_fix(system):
    """
    ГЛАВНАЯ ФУНКЦИЯ: Применяет ВСЕ исправления сразу
    """
    
    st.info("🎯 Применяем ПОЛНОЕ исправление системы...")
    
    # 1. Исправляем загрузку ADS с ценами
    fix_ads_loading_with_prices(system)
    
    # 2. Добавляем анализатор складов
    add_warehouse_analyzer(system)
    
    # 3. Отмечаем что все исправлено
    system._complete_final_fix_applied = True
    
    st.success("✅ ПОЛНОЕ исправление применено!")
    st.info("""
    🎯 **Что исправлено:**
    - ✅ Загрузка ADS с ценами из колонки 12 "Посл. закупка"
    - ✅ Анализ складов с русскими названиями в таблицах
    - ✅ Правильный поиск и отображение цен
    - ✅ Полная функциональность анализа по складам
    """)
    
    return True


def fix_ads_loading_with_prices(system):
    """
    Исправляет метод load_sales_file_updated для извлечения цен из колонки 12
    """
    
    def load_sales_file_updated_with_prices(self, file_content) -> dict:
        """
        ИСПРАВЛЕННЫЙ метод загрузки ADS файла с ценами из колонки 12
        """
        try:
            st.info("🔄 Обработка файла с извлечением цен из колонки 12 'Посл. закупка'...")
        
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
            st.write(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # Параметры обработки
            start_col_index = 12  # Колонка M (продажи)
            end_col_index = 28    # Колонка AB+1
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (номенклатура)
            price_col = 11        # Колонка L (12) "Посл. закупка" (индекс 11)
            
            st.info(f"""
            📋 **Параметры обработки:**
            - Номенклатура: Колонка B
            - **Цены: Колонка L (12) "Посл. закупка"**
            - Данные продаж: колонки M:AB
            - Начальная строка: 4
            """)
            
            # Обрабатываем данные
            sales_data_list = []
            prices_found = 0
            prices_processed = 0
            
            for idx in range(start_row, df.shape[0]):
                row = df.iloc[idx]
                
                # Номенклатура из колонки B
                nomenclature = row.iloc[nomenclature_col] if nomenclature_col < len(row) else None
                if pd.isna(nomenclature) or str(nomenclature).strip() == '':
                    continue
                
                item_name = str(nomenclature).strip()
                
                # ЦЕНА из колонки 12 "Посл. закупка"
                try:
                    raw_price = row.iloc[price_col] if price_col < len(row) else None
                    if pd.notna(raw_price) and str(raw_price).strip() != '':
                        item_price = float(raw_price)
                        if item_price > 0:
                            prices_found += 1
                    else:
                        item_price = 0.0
                    prices_processed += 1
                except (ValueError, TypeError, IndexError):
                    item_price = 0.0
                    prices_processed += 1
                
                # Данные продаж из колонок M:AB
                row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                
                # Формула ADS: среднее / 30
                average_value = row_sales_numeric.mean()
                ads_value = average_value / 30
                
                sales_data_list.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_sales_numeric.sum(),
                    'monthly_data': row_sales_numeric.tolist(),
                    'last_purchase_price': float(item_price)  # КЛЮЧЕВОЕ: добавляем цену
                })
            
            # Создаем DataFrame
            ads_df = pd.DataFrame(sales_data_list)
            
            # Исключаем последнюю строку
            if len(ads_df) > 1:
                ads_df = ads_df.iloc[:-1].copy()
            
            # СОХРАНЯЕМ в системе
            self.sales_data = ads_df  # Для топ товаров
            self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales', 'last_purchase_price']].copy()
            
            # Результат
            if prices_found > 0:
                st.success(f"""
                ✅ **ADS с ценами загружен успешно!**
                - Всего товаров: {len(ads_df)}
                - **С ценами: {prices_found} из {prices_processed}**
                - **Покрытие ценами: {(prices_found/prices_processed*100):.1f}%**
                - Общий ADS: {ads_df['ads'].sum():.2f}
                """)
            else:
                st.warning(f"""
                ⚠️ **ADS загружен, но ЦЕНЫ НЕ НАЙДЕНЫ!**
                - Товаров обработано: {len(ads_df)}
                - Цен найдено: {prices_found} из {prices_processed}
                
                **Проверьте колонку L (12) "Посл. закупка" в файле!**
                """)
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'prices_found': prices_found,
                'price_coverage_percentage': (prices_found/prices_processed*100) if prices_processed > 0 else 0,
                'total_ads': ads_df['ads'].sum()
            }
            
        except Exception as e:
            st.error(f"❌ Ошибка загрузки файла: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Заменяем метод в системе
    system.load_sales_file_updated = types.MethodType(load_sales_file_updated_with_prices, system)
    st.success("✅ Метод load_sales_file_updated исправлен для работы с ценами!")


def add_warehouse_analyzer(system):
    """
    Добавляет анализатор складов с правильным поиском цен
    """
    
    # Конфигурация складов
    warehouse_config = {
        'Шымкент_Склад': {
            'name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
            'short_name': 'Шымкент Склад',
            'city': 'шымкент',
            'col': 3,
            'min_days': 15,
            'max_days': 45
        },
        'Шымкент_Магазин': {
            'name': '6 Склад фурнитуры "Овощная база" Магазин',
            'short_name': 'Шымкент Магазин',
            'city': 'шымкент',
            'col': 4,
            'min_days': 10,
            'max_days': 30
        },
        'Алматы_Склад': {
            'name': 'АО Склад Фурнитура TRADE',
            'short_name': 'Алматы Склад',
            'city': 'алматы',
            'col': 6,
            'min_days': 20,
            'max_days': 60
        },
        'База_Комплект': {
            'name': 'База Склад Фурнитура Комплект',
            'short_name': 'База Комплект',
            'city': 'алматы',
            'col': 8,
            'min_days': 25,
            'max_days': 75
        },
        'Барыс_Склад': {
            'name': 'Барыс Склад Фурнитура TRADE',
            'short_name': 'Барыс Склад',
            'city': 'алматы',
            'col': 9,
            'min_days': 15,
            'max_days': 40
        },
        'Казыбаева_Склад': {
            'name': 'Казыбаева Склад Фурнитура TRADE',
            'short_name': 'Казыбаева Склад',
            'city': 'алматы',
            'col': 10,
            'min_days': 12,
            'max_days': 35
        },
        'Астана_Магазин': {
            'name': 'Магазин фурнитуры',
            'short_name': 'Астана Магазин',
            'city': 'астана',
            'col': 11,
            'min_days': 10,
            'max_days': 30
        },
        'Астана_Склад': {
            'name': 'склад фурнитура № 1',
            'short_name': 'Астана Склад',
            'city': 'астана',
            'col': 12,
            'min_days': 15,
            'max_days': 45
        },
        'Казыбаева_Магазин': {
            'name': 'ТД Казыбаева ФУРНИТУРА магазин',
            'short_name': 'Казыбаева Магазин',
            'city': 'алматы',
            'col': 13,
            'min_days': 8,
            'max_days': 25
        }
    }
    
    def read_remains_file_exact(uploaded_file):
        """Читает файл остатков с точной структурой"""
        try:
            st.info("📖 Читаем файл остатков...")
            
            # Читаем файл
            if uploaded_file.name.endswith('.xlsx'):
                file_data = pd.read_excel(uploaded_file, header=None).values.tolist()
            else:
                file_data = pd.read_excel(uploaded_file, engine='xlrd', header=None).values.tolist()
            
            st.success(f"✅ Файл прочитан: {len(file_data)} строк")
            
            # Читаем данные начиная с 4й строки (индекс 3)
            remains_data = []
            for i in range(3, len(file_data)):
                row = file_data[i]
                
                if not row or len(row) == 0 or not row[0] or pd.isna(row[0]):
                    continue
                    
                item_name = str(row[0]).strip()
                if not item_name:
                    continue
                
                # Итоговый остаток (колонка 15, индекс 14)
                try:
                    total_stock = row[14] if len(row) > 14 and row[14] is not None else 0
                    total_stock = float(total_stock) if pd.notna(total_stock) else 0
                except (ValueError, TypeError, IndexError):
                    total_stock = 0
                
                item_data = {
                    'номенклатура': item_name,
                    'итого_остаток': total_stock
                }
                
                # Остатки по складам
                for warehouse_key, config in warehouse_config.items():
                    col_idx = config['col']
                    try:
                        if len(row) > col_idx and row[col_idx] is not None:
                            quantity = float(row[col_idx]) if pd.notna(row[col_idx]) else 0
                        else:
                            quantity = 0
                    except (ValueError, TypeError, IndexError):
                        quantity = 0
                    
                    item_data[f'{warehouse_key}_остаток'] = quantity
                
                remains_data.append(item_data)
            
            if not remains_data:
                raise ValueError("Не найдено товаров с данными")
            
            df = pd.DataFrame(remains_data)
            st.success(f"✅ Обработано товаров: {len(df)}")
            
            return df
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            return pd.DataFrame()
    
    def find_prices_in_ads(ads_data):
        """ПРАВИЛЬНО находит цены в ADS данных"""
        if ads_data is None or ads_data.empty:
            return False, None
        
        # Список возможных названий колонок с ценами
        price_columns = [
            'last_purchase_price',
            'посл_закупка',
            'Посл. закупка', 
            'цена',
            'price',
            'стоимость'
        ]
        
        for col in price_columns:
            if col in ads_data.columns:
                prices_count = (ads_data[col] > 0).sum()
                if prices_count > 0:
                    st.success(f"💰 Найдена колонка с ценами: '{col}' ({prices_count} товаров)")
                    return True, col
        
        st.warning("⚠️ Цены в ADS данных не найдены")
        return False, None
    
    def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city=None, 
                                           min_days=10, max_days=50):
        """ПОЛНЫЙ анализ складов с ценами"""
        if remains_df.empty or 'номенклатура' not in remains_df.columns:
            st.error("❌ Проблема с данными остатков")
            return []
        
        # Проверяем ADS и цены
        has_ads = ads_data is not None and not ads_data.empty
        has_prices, price_column = find_prices_in_ads(ads_data) if has_ads else (False, None)
        
        st.info(f"🔄 Анализируем {len(remains_df)} товаров по {len(warehouse_config)} складам...")
        
        if has_ads:
            st.success(f"✅ ADS данные: {len(ads_data)} товаров")
        if has_prices:
            st.success(f"💰 Цены найдены в колонке: {price_column}")
        
        results = []
        progress_bar = st.progress(0)
        
        # Анализируем каждый товар
        for idx, (_, item) in enumerate(remains_df.iterrows()):
            progress = (idx + 1) / len(remains_df)
            progress_bar.progress(progress)
            
            item_name = str(item['номенклатура']).strip()
            total_stock = float(item.get('итого_остаток', 0))
            
            # Получаем ADS и цену
            ads_value = 0
            item_price = 0
            
            if has_ads:
                ads_match = ads_data[ads_data['номенклатура'] == item_name]
                if not ads_match.empty:
                    ads_value = float(ads_match.iloc[0].get('ads', 0))
                    if has_prices and price_column:
                        try:
                            item_price = float(ads_match.iloc[0].get(price_column, 0))
                        except (ValueError, TypeError):
                            item_price = 0
            
            # Анализ по складам
            warehouses_analysis = {}
            critical_count = 0
            warning_count = 0
            total_order_qty = 0
            total_order_value = 0
            
            for warehouse_key, config in warehouse_config.items():
                stock_col = f"{warehouse_key}_остаток"
                current_stock = float(item.get(stock_col, 0))
                
                # Настройки склада
                wh_min_days = config.get('min_days', min_days)
                wh_max_days = config.get('max_days', max_days)
                
                # Расчеты
                min_stock = ads_value * wh_min_days if ads_value > 0 else 0
                max_stock = ads_value * wh_max_days if ads_value > 0 else 0
                min_deficit = max(0, min_stock - current_stock)
                surplus = max(0, current_stock - max_stock)
                
                # Месяцы запаса
                if ads_value > 0:
                    months_of_stock = current_stock / (ads_value * 30)
                elif current_stock > 0:
                    months_of_stock = 999
                else:
                    months_of_stock = 0
                
                # Статус
                if ads_value > 0:
                    if current_stock < min_stock:
                        if min_deficit > ads_value * 7:
                            status = 'critical'
                            critical_count += 1
                        else:
                            status = 'warning'
                            warning_count += 1
                    elif current_stock > max_stock:
                        status = 'excess'
                    else:
                        status = 'good'
                elif current_stock > 0:
                    status = 'no_sales'
                else:
                    status = 'empty'
                
                # К заказу
                order_quantity = min_deficit if status in ['critical', 'warning'] else 0
                total_order_qty += order_quantity
                
                # Денежные расчеты
                stock_value = current_stock * item_price if item_price > 0 else 0
                order_value = order_quantity * item_price if item_price > 0 else 0
                total_order_value += order_value
                
                warehouses_analysis[warehouse_key] = {
                    'warehouse_name': config['name'],
                    'short_name': config['short_name'],
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'order_quantity': order_quantity,
                    'stock_value': stock_value,
                    'order_value': order_value,
                    'months_of_stock': months_of_stock,
                    'status': status
                }
            
            # Общий статус
            if critical_count > 0:
                overall_status = 'critical'
            elif warning_count > 0:
                overall_status = 'warning'
            else:
                overall_status = 'good'
            
            # Минимальные месяцы
            months_list = [w['months_of_stock'] for w in warehouses_analysis.values() if w['months_of_stock'] < 999]
            min_months = min(months_list) if months_list else 0
            
            results.append({
                'номенклатура': item_name,
                'total_stock': total_stock,
                'ads': ads_value,
                'price': item_price,
                'total_stock_value': total_stock * item_price if item_price > 0 else 0,
                'total_order_quantity': total_order_qty,
                'total_order_value': total_order_value,
                'min_months_across_warehouses': min_months,
                'overall_status': overall_status,
                'warehouses': warehouses_analysis
            })
        
        progress_bar.progress(1.0)
        
        # Статистика
        total_items = len(results)
        critical_items = sum(1 for item in results if item['overall_status'] == 'critical')
        warning_items = sum(1 for item in results if item['overall_status'] == 'warning')
        total_stock_value = sum(item['total_stock_value'] for item in results)
        total_order_value = sum(item['total_order_value'] for item in results)
        
        st.success(f"""
        ✅ **Анализ завершен!**
        - Товаров: {total_items}
        - 🔴 Критичных: {critical_items}
        - 🟡 Требуют внимания: {warning_items}
        - 💰 Стоимость остатков: {total_stock_value:,.0f} ₽
        - 🛒 К заказу: {total_order_value:,.0f} ₽
        """)
        
        return results
    
    def get_warehouse_recommendations(analysis_results=None):
        """Рекомендации по складам"""
        if not analysis_results:
            return {}
        
        warehouse_stats = {}
        for warehouse_key, config in warehouse_config.items():
            warehouse_stats[warehouse_key] = {
                'name': config['short_name'],
                'total_items': 0,
                'critical_items': 0,
                'warning_items': 0,
                'total_order_quantity': 0,
                'total_order_value': 0,
                'total_stock_value': 0
            }
        
        for item in analysis_results:
            for warehouse_key, wh_data in item.get('warehouses', {}).items():
                if warehouse_key in warehouse_stats:
                    stats = warehouse_stats[warehouse_key]
                    stats['total_items'] += 1
                    
                    if wh_data['status'] == 'critical':
                        stats['critical_items'] += 1
                    elif wh_data['status'] == 'warning':
                        stats['warning_items'] += 1
                    
                    stats['total_order_quantity'] += wh_data.get('order_quantity', 0)
                    stats['total_order_value'] += wh_data.get('order_value', 0)
                    stats['total_stock_value'] += wh_data.get('stock_value', 0)
        
        return warehouse_stats
    
    # Добавляем методы к системе
    system.read_remains_file_exact = read_remains_file_exact
    system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
    system.get_warehouse_recommendations = get_warehouse_recommendations
    system.warehouse_config = warehouse_config
    
    st.success("✅ Анализатор складов добавлен!")


def create_complete_warehouse_page():
    """
    Создает ПОЛНУЮ страницу анализа складов с русскими названиями
    """
    
    def complete_warehouse_analysis_page(system):
        """
        ПОЛНАЯ страница анализа складов
        """
        
        st.header("📦 Анализ складов")
        st.caption("Полная версия с ценами из ADS + русские названия")
        
        # Применяем исправления
        if not hasattr(system, '_complete_final_fix_applied'):
            with st.spinner("🔧 Применяем все исправления..."):
                apply_complete_final_fix(system)
        
        # Проверяем ADS
        has_ads = hasattr(system, 'calculated_ads') and system.calculated_ads is not None
        
        if has_ads:
            st.success(f"✅ ADS данные готовы: {len(system.calculated_ads)} товаров")
            
            # Проверяем цены
            if 'last_purchase_price' in system.calculated_ads.columns:
                prices_count = (system.calculated_ads['last_purchase_price'] > 0).sum()
                if prices_count > 0:
                    st.success(f"💰 Цены найдены: {prices_count} товаров с ценами")
                else:
                    st.warning("⚠️ Колонка цен найдена, но все цены = 0")
            else:
                st.error("❌ Цены не найдены - перезагрузите файл продаж!")
        else:
            st.warning("⚠️ ADS не рассчитан - сначала рассчитайте ADS")
        
        # Настройки
        st.subheader("⚙️ Настройки анализа")
        col1, col2 = st.columns(2)
        with col1:
            min_days = st.number_input("Минимум дней:", value=10, min_value=5, max_value=60)
        with col2:
            max_days = st.number_input("Максимум дней:", value=50, min_value=15, max_value=120)
        
        # Загрузка файла
        st.subheader("📂 Загрузка файла остатков")
        uploaded_file = st.file_uploader(
            "Выберите файл остатков:",
            type=['xlsx', 'xls'],
            help="Файл с номенклатурой в A1, данные с 4й строки"
        )
        
        if uploaded_file:
            # Читаем файл
            with st.spinner("📖 Читаем файл остатков..."):
                remains_df = system.read_remains_file_exact(uploaded_file)
            
            if remains_df.empty:
                st.error("❌ Не удалось прочитать файл")
                return
            
            # Статистика
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров", len(remains_df))
            with col2:
                warehouse_cols = [col for col in remains_df.columns if col.endswith('_остаток')]
                st.metric("Складов", len(warehouse_cols))
            with col3:
                total_stock = remains_df['итого_остаток'].sum()
                st.metric("Общий остаток", f"{total_stock:,.0f}")
            with col4:
                items_with_stock = (remains_df['итого_остаток'] > 0).sum()
                st.metric("С остатками", items_with_stock)
            
            # Анализ
            if st.button("🚀 Запустить анализ складов", type="primary"):
                ads_data = getattr(system, 'calculated_ads', pd.DataFrame())
                
                with st.spinner("🔄 Выполняем анализ..."):
                    results = system.analyze_warehouse_stock_with_details(
                        remains_df, ads_data, None, min_days, max_days
                    )
                
                if results:
                    system.warehouse_analysis_results = results
                    recommendations = system.get_warehouse_recommendations(results)
                    system.warehouse_recommendations = recommendations
                    
                    # Показываем результаты с РУССКИМИ НАЗВАНИЯМИ
                    show_results_with_russian_names(results, recommendations)
                else:
                    st.error("❌ Анализ не дал результатов")
        
        # Показываем сохраненные результаты
        if hasattr(system, 'warehouse_analysis_results') and system.warehouse_analysis_results:
            st.markdown("---")
            if st.button("🔄 Показать последние результаты"):
                show_results_with_russian_names(
                    system.warehouse_analysis_results,
                    getattr(system, 'warehouse_recommendations', {})
                )
    
    return complete_warehouse_analysis_page


def show_results_with_russian_names(results: List[Dict], recommendations: Dict):
    """
    Показывает результаты с РУССКИМИ НАЗВАНИЯМИ в таблицах
    """
    
    st.subheader("📈 Результаты анализа складов")
    
    # Общая статистика
    total_items = len(results)
    critical_items = sum(1 for item in results if item['overall_status'] == 'critical')
    warning_items = sum(1 for item in results if item['overall_status'] == 'warning')
    good_items = total_items - critical_items - warning_items
    
    total_stock_value = sum(item.get('total_stock_value', 0) for item in results)
    total_order_value = sum(item.get('total_order_value', 0) for item in results)
    
    # Карточки
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("🔴 Критичных", critical_items)
    with col3:
        st.metric("🟡 Требуют внимания", warning_items)
    with col4:
        st.metric("🟢 В норме", good_items)
    with col5:
        st.metric("💰 К заказу", f"{total_order_value:,.0f} ₽")
    
    # Статистика по складам
    if recommendations:
        st.subheader("🏪 Статистика по складам")
        
        warehouse_table = []
        for wh_key, stats in recommendations.items():
            warehouse_table.append({
                'Склад': stats['name'],
                'Всего товаров': stats['total_items'],
                'Критичных': stats['critical_items'],
                'Требуют внимания': stats['warning_items'],
                'К заказу (шт)': f"{stats['total_order_quantity']:,.0f}",
                'К заказу (₽)': f"{stats['total_order_value']:,.0f}",
                'Стоимость остатков (₽)': f"{stats['total_stock_value']:,.0f}"
            })
        
        if warehouse_table:
            st.dataframe(pd.DataFrame(warehouse_table), use_container_width=True)
    
    # Детальная таблица товаров
    st.subheader("📋 Детальная информация по товарам")
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Фильтр:", ["Все", "Критичные", "Требуют внимания", "В норме"])
    with col2:
        sort_by = st.selectbox("Сортировка:", ["Статусу", "ADS", "Стоимости заказа", "Алфавиту"])
    with col3:
        max_items = st.number_input("Показать:", min_value=10, value=100, max_value=500)
    
    # Фильтруем
    filtered_results = results.copy()
    if status_filter == "Критичные":
        filtered_results = [item for item in filtered_results if item['overall_status'] == 'critical']
    elif status_filter == "Требуют внимания":
        filtered_results = [item for item in filtered_results if item['overall_status'] == 'warning']
    elif status_filter == "В норме":
        filtered_results = [item for item in filtered_results if item['overall_status'] == 'good']
    
    # Сортируем
    if sort_by == "Статусу":
        status_order = {'critical': 0, 'warning': 1, 'good': 2}
        filtered_results.sort(key=lambda x: (status_order.get(x['overall_status'], 3), -x.get('total_order_value', 0)))
    elif sort_by == "ADS":
        filtered_results.sort(key=lambda x: -x.get('ads', 0))
    elif sort_by == "Стоимости заказа":
        filtered_results.sort(key=lambda x: -x.get('total_order_value', 0))
    else:
        filtered_results.sort(key=lambda x: x.get('номенклатура', ''))
    
    filtered_results = filtered_results[:max_items]
    
    # Создаем таблицу с РУССКИМИ НАЗВАНИЯМИ
    if filtered_results:
        display_data = []
        
        for item in filtered_results:
            status_emoji = {
                'critical': '🔴',
                'warning': '🟡',
                'good': '🟢'
            }.get(item['overall_status'], '⚪')
            
            row = {
                'Статус': status_emoji,
                'Номенклатура': item['номенклатура'][:50],
                'ADS': f"{item.get('ads', 0):.2f}",
                'Цена (₽)': f"{item.get('price', 0):.2f}" if item.get('price', 0) > 0 else "-",
                'Общий остаток': f"{item.get('total_stock', 0):.0f}",
                'Стоимость остатков (₽)': f"{item.get('total_stock_value', 0):,.0f}" if item.get('total_stock_value', 0) > 0 else "-",
                'К заказу (шт)': f"{item.get('total_order_quantity', 0):.0f}" if item.get('total_order_quantity', 0) > 0 else "-",
                'К заказу (₽)': f"{item.get('total_order_value', 0):,.0f}" if item.get('total_order_value', 0) > 0 else "-"
            }
            
            # Добавляем склады
            warehouses = item.get('warehouses', {})
            for wh_key, wh_data in warehouses.items():
                current = wh_data.get('current_stock', 0)
                order = wh_data.get('order_quantity', 0)
                wh_name = wh_data.get('short_name', wh_key)
                
                if order > 0:
                    row[wh_name] = f"{current:.0f} (+{order:.0f})"
                elif current > 0:
                    row[wh_name] = f"{current:.0f}"
                else:
                    row[wh_name] = "0"
            
            display_data.append(row)
        
        # Показываем таблицу
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True)
        
        st.caption(f"📊 Показано {len(filtered_results)} из {len(results)} товаров")
    
    else:
        st.info("📋 Нет товаров для отображения")


# Главная функция
def quick_complete_fix(system):
    """
    БЫСТРОЕ ПОЛНОЕ ИСПРАВЛЕНИЕ всего сразу
    """
    
    try:
        # Применяем все исправления
        if not hasattr(system, '_complete_final_fix_applied'):
            apply_complete_final_fix(system)
        
        # Создаем страницу
        warehouse_page = create_complete_warehouse_page()
        warehouse_page(system)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка полного исправления: {str(e)}")
        st.error("""
        **Для ручного исправления:**
        1. Создайте файл `final_complete_fix.py` из артефакта
        2. Замените функцию `warehouse_analysis_page` на:
        
        ```python
        def warehouse_analysis_page(system):
            from final_complete_fix import quick_complete_fix
            quick_complete_fix(system)
        ```
        """)
        return False


if __name__ == "__main__":
    print("🎯 Финальное полное исправление")
    print("Исправляет ВСЕ: ADS с ценами + русский интерфейс + анализ складов")
    print("\nДля использования:")
    print("from final_complete_fix import quick_complete_fix")
    print("quick_complete_fix(system)")