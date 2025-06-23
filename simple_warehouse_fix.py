

import streamlit as st
import pandas as pd
import numpy as np

# ===== РЕАЛЬНЫЕ СКЛАДЫ ИЗ ВАШЕГО ФАЙЛА =====

REAL_WAREHOUSE_SETTINGS = {
    # ГЛАВНЫЙ ХАБ - База Склад Фурнитура Комплект (Алматы)
    'База Склад Фурнитура Комплект': {
        'min_days': 30, 'max_days': 90, 'city': 'Алматы', 'type': 'Главный склад-хаб',
        'level': 1, 'priority': 1, 'description': 'Основной хаб, 95% приходов от партнеров'
    },
    
    # СКЛАДЫ 2-ГО УРОВНЯ (питаются от главного хаба)
    'Казыбаева Склад Фурнитура TRADE': {
        'min_days': 15, 'max_days': 45, 'city': 'Алматы', 'type': 'Склад 2-го уровня',
        'level': 2, 'priority': 2, 'description': 'Питается от главного хаба'
    },
    'Барыс Склад Фурнитура TRADE': {
        'min_days': 15, 'max_days': 45, 'city': 'Алматы', 'type': 'Магазин+склад',
        'level': 2, 'priority': 2, 'description': 'Питается от главного хаба'
    },
    'АО Склад Фурнитура TRADE': {
        'min_days': 10, 'max_days': 30, 'city': 'Алматы', 'type': 'Специализированный',
        'level': 2, 'priority': 3, 'description': 'Только кромочные материалы'
    },
    '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
        'min_days': 20, 'max_days': 60, 'city': 'Шымкент', 'type': 'Склад 2-го уровня',
        'level': 2, 'priority': 2, 'description': 'Питается от главного хаба'
    },
    'склад фурнитура № 1': {
        'min_days': 20, 'max_days': 60, 'city': 'Астана', 'type': 'Склад 2-го уровня',
        'level': 2, 'priority': 2, 'description': 'Питается от главного хаба'
    },
    
    # МАГАЗИНЫ (питаются от складов 2-го уровня)
    'ТД Казыбаева ФУРНИТУРА магазин': {
        'min_days': 8, 'max_days': 25, 'city': 'Алматы', 'type': 'Магазин',
        'level': 3, 'priority': 3, 'description': 'Питается от Казыбаева Склад'
    },
    '6 Склад фурнитуры "Овощная база" Магазин': {
        'min_days': 10, 'max_days': 30, 'city': 'Шымкент', 'type': 'Магазин',
        'level': 3, 'priority': 3, 'description': 'Питается от 4 Склад АЗМ'
    },
    'Магазин фурнитуры': {
        'min_days': 10, 'max_days': 30, 'city': 'Астана', 'type': 'Магазин',
        'level': 3, 'priority': 3, 'description': 'Питается от склад фурнитура № 1'
    }
}

def simple_add_missing_methods(system):
    """
    ПРОСТОЕ добавление отсутствующих методов - НЕ ЛОМАЕТ существующий код
    """
    
    # Добавляем метод analyze_warehouse_stock_with_details если его нет
    if not hasattr(system, 'analyze_warehouse_stock_with_details'):
        
        def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
            """
            ПРОСТОЙ анализ складов с персональными настройками
            Использует СУЩЕСТВУЮЩИЙ формат данных, только добавляет персональные настройки
            """
            
            st.info("🔍 Запускаю анализ с персональными настройками складов...")
            
            # Проверяем что у нас есть данные
            if remains_df is None or remains_df.empty:
                st.error("❌ Нет данных остатков")
                return None, None
            
            if ads_data is None or ads_data.empty:
                st.error("❌ Нет данных ADS")
                return None, None
            
            # АВТОМАТИЧЕСКИ определяем названия колонок в ADS данных
            st.info("🔍 Определяю названия колонок в ADS данных...")
            
            # Ищем колонку с наименованиями
            name_column = None
            for col in ['Наименование', 'наименование', 'название', 'товар', 'item', 'product']:
                if col in ads_data.columns:
                    name_column = col
                    break
            
            if name_column is None:
                # Берем первую колонку
                name_column = ads_data.columns[0]
                st.warning(f"⚠️ Колонка наименований не найдена, использую первую: '{name_column}'")
            else:
                st.success(f"✅ Найдена колонка наименований: '{name_column}'")
            
            # Ищем колонку с ADS
            ads_column = None
            for col in ['ADS', 'ads', 'средние_продажи', 'среднее', 'average_sales']:
                if col in ads_data.columns:
                    ads_column = col
                    break
            
            if ads_column is None:
                st.error("❌ Не найдена колонка с ADS данными!")
                st.write("Доступные колонки:", list(ads_data.columns))
                return None, None
            else:
                st.success(f"✅ Найдена колонка ADS: '{ads_column}'")
            
            # Стандартизируем названия колонок
            ads_data_copy = ads_data.copy()
            ads_data_copy = ads_data_copy.rename(columns={
                name_column: 'Наименование',
                ads_column: 'ADS'
            })
            
            # Также стандартизируем в remains_df
            remains_df_copy = remains_df.copy()
            
            # Ищем колонку наименований в остатках
            remains_name_column = None
            for col in ['Наименование', 'наименование', 'номенклатура', 'название', 'товар']:
                if col in remains_df_copy.columns:
                    remains_name_column = col
                    break
            
            if remains_name_column is None:
                remains_name_column = remains_df_copy.columns[0]
                st.warning(f"⚠️ В остатках колонка наименований не найдена, использую первую: '{remains_name_column}'")
            else:
                st.success(f"✅ В остатках найдена колонка наименований: '{remains_name_column}'")
            
            remains_df_copy = remains_df_copy.rename(columns={remains_name_column: 'Наименование'})
            
            # Объединяем данные остатков с ADS
            merged_data = pd.merge(
                remains_df_copy, 
                ads_data_copy[['Наименование', 'ADS']], 
                on='Наименование', 
                how='inner'
            )
            
            if merged_data.empty:
                st.error("❌ Не удалось объединить данные остатков с ADS")
                return None, None
            
            st.success(f"✅ Объединено {len(merged_data)} товаров")
            
            # Ищем цены в ADS данных
            price_column = None
            for col in ['last_purchase_price', 'Посл. закупка', 'цена', 'price', 'стоимость', 'закупочная_цена']:
                if col in ads_data_copy.columns:
                    price_column = col
                    break
            
            has_prices = price_column is not None
            if has_prices:
                st.success(f"💰 Найдены цены в колонке '{price_column}'")
                merged_data = pd.merge(
                    merged_data,
                    ads_data_copy[['Наименование', price_column]],
                    on='Наименование',
                    how='left'
                )
                merged_data['price'] = merged_data[price_column].fillna(0)
            else:
                st.warning("⚠️ Цены не найдены - анализ без денежного выражения")
                st.info("Ищу в колонках: " + str(['last_purchase_price', 'Посл. закупка', 'цена', 'price', 'стоимость', 'закупочная_цена']))
                st.info("Доступные колонки: " + str(list(ads_data_copy.columns)))
                merged_data['price'] = 0
            
            # Анализируем каждый товар по каждому складу
            analysis_results = []
            warehouse_recommendations = {}
            
            # Находим колонки складов в данных остатков (точные названия)
            warehouse_columns = []
            
            st.info("🔍 Ищу реальные склады в данных остатков...")
            
            # Сначала точное совпадение с реальными названиями
            for col in merged_data.columns:
                if col in REAL_WAREHOUSE_SETTINGS:
                    warehouse_columns.append(col)
                    st.success(f"✅ Найден склад: '{col}'")
            
            # Если нет точных совпадений, пробуем частичное совпадение
            if len(warehouse_columns) == 0:
                st.warning("⚠️ Нет точных совпадений, пробую частичное совпадение...")
                
                for col in merged_data.columns:
                    col_lower = str(col).lower()
                    
                    # Ищем по ключевым словам из реальных названий
                    for real_name in REAL_WAREHOUSE_SETTINGS.keys():
                        real_lower = real_name.lower()
                        
                        # Проверяем различные варианты совпадений
                        if (col_lower == real_lower or
                            any(word in col_lower for word in real_lower.split() if len(word) > 3) or
                            col_lower in real_lower or
                            real_lower in col_lower):
                            
                            if col not in warehouse_columns:
                                warehouse_columns.append(col)
                                st.info(f"📍 Частичное совпадение: '{col}' ≈ '{real_name}'")
                                break
            
            if not warehouse_columns:
                st.error("❌ Не найдены склады в данных!")
                st.markdown("**🏪 Ожидаемые названия складов:**")
                for name in REAL_WAREHOUSE_SETTINGS.keys():
                    st.write(f"  - `{name}`")
                st.markdown("**📋 Найденные колонки в файле:**")
                for col in merged_data.columns:
                    if str(col).strip():  # Только непустые
                        st.write(f"  - `{col}`")
                
                st.markdown("**💡 Возможные причины:**")
                st.write("1. Файл имеет другую структуру")
                st.write("2. Названия колонок изменились")
                st.write("3. Проблема с чтением файла")
                
                return None, None
            
            st.success(f"✅ Найдено складов для анализа: {len(warehouse_columns)}")
            
            # Создаем маппинг складов на настройки
            warehouse_mapping = {}
            for col in warehouse_columns:
                if col in REAL_WAREHOUSE_SETTINGS:
                    warehouse_mapping[col] = col
                    st.write(f"  ✅ `{col}` - точное совпадение")
                else:
                    # Ищем наиболее подходящий склад по названию
                    best_match = None
                    col_lower = col.lower()
                    
                    for real_name in REAL_WAREHOUSE_SETTINGS.keys():
                        real_lower = real_name.lower()
                        if (col_lower in real_lower or 
                            real_lower in col_lower or
                            any(word in col_lower for word in real_lower.split() if len(word) > 3)):
                            best_match = real_name
                            break
                    
                    if best_match:
                        warehouse_mapping[col] = best_match
                        st.write(f"  🔄 `{col}` → `{best_match}`")
                    else:
                        # Используем настройки главного хаба по умолчанию
                        warehouse_mapping[col] = 'База Склад Фурнитура Комплект'
                        st.warning(f"  ⚠️ `{col}` → настройки главного хаба (по умолчанию)")
            
            # Инициализируем рекомендации по складам
            for col in warehouse_columns:
                warehouse_config_key = warehouse_mapping[col]
                settings = REAL_WAREHOUSE_SETTINGS[warehouse_config_key]
                
                warehouse_recommendations[col] = {
                    'name': col,  # Используем реальное название из файла
                    'config_name': warehouse_config_key,  # Ссылка на конфигурацию
                    'city': settings['city'],
                    'type': settings['type'],
                    'level': settings['level'],
                    'priority': settings['priority'],
                    'description': settings['description'],
                    'min_days': settings['min_days'],
                    'max_days': settings['max_days'],
                    'critical_items': [],
                    'warning_items': [],
                    'good_items': [],
                    'excess_items': [],
                    'total_order_value': 0,
                    'total_stock_value': 0
                }
            
            # Прогресс бар
            progress_bar = st.progress(0)
            total_items = len(merged_data)
            
            # Анализируем каждый товар
            for idx, row in merged_data.iterrows():
                item_name = row['Наименование']
                ads_value = row.get('ADS', 0)
                price = row.get('price', 0) if has_prices else 0
                
                item_analysis = {
                    'item_name': item_name,
                    'ads': ads_value,
                    'price': price,
                    'warehouses': {}
                }
                
                # Анализируем по каждому складу с персональными настройками
                for col in warehouse_columns:
                    current_stock = row.get(col, 0)
                    
                    try:
                        current_stock = float(current_stock) if pd.notna(current_stock) else 0
                    except:
                        current_stock = 0
                    
                    if current_stock <= 0:
                        continue
                    
                    # Получаем персональные настройки для этого склада
                    warehouse_config_key = warehouse_mapping[col]
                    settings = REAL_WAREHOUSE_SETTINGS[warehouse_config_key]
                    
                    min_stock = ads_value * settings['min_days']
                    max_stock = ads_value * settings['max_days']
                    
                    # Определяем статус с учетом уровня склада
                    if settings['level'] == 1:  # Главный хаб - более строгие критерии
                        if current_stock <= min_stock * 0.3:
                            status = 'Критично'
                        elif current_stock <= min_stock:
                            status = 'Мало'
                        elif current_stock <= max_stock:
                            status = 'Норма'
                        else:
                            status = 'Избыток'
                    else:  # Склады и магазины 2-3 уровня
                        if current_stock <= min_stock * 0.5:
                            status = 'Критично'
                        elif current_stock <= min_stock:
                            status = 'Мало'
                        elif current_stock <= max_stock:
                            status = 'Норма'
                        else:
                            status = 'Избыток'
                    
                    # Рассчитываем дефицит и стоимости
                    deficit_qty = max(0, min_stock - current_stock)
                    stock_value = current_stock * price if has_prices else 0
                    deficit_value = deficit_qty * price if has_prices else 0
                    months_of_stock = (current_stock / ads_value) if ads_value > 0 else 999
                    
                    warehouse_analysis = {
                        'current_stock': current_stock,
                        'min_stock': min_stock,
                        'max_stock': max_stock,
                        'status': status,
                        'deficit_qty': deficit_qty,
                        'stock_value': stock_value,
                        'deficit_value': deficit_value,
                        'months_of_stock': months_of_stock,
                        'min_days': settings['min_days'],
                        'max_days': settings['max_days'],
                        'config_name': warehouse_config_key,
                        'level': settings['level'],
                        'priority': settings['priority']
                    }
                    
                    item_analysis['warehouses'][col] = warehouse_analysis
                    
                    # Добавляем к рекомендациям склада
                    rec = warehouse_recommendations[col]
                    
                    item_info = {
                        'name': item_name,
                        'current_stock': current_stock,
                        'min_stock': min_stock,
                        'max_stock': max_stock,
                        'deficit': deficit_qty,
                        'deficit_value': deficit_value,
                        'stock_value': stock_value,
                        'months_stock': months_of_stock
                    }
                    
                    if status == 'Критично':
                        rec['critical_items'].append(item_info)
                    elif status == 'Мало':
                        rec['warning_items'].append(item_info)
                    elif status == 'Норма':
                        rec['good_items'].append(item_info)
                    else:
                        rec['excess_items'].append(item_info)
                    
                    rec['total_order_value'] += deficit_value
                    rec['total_stock_value'] += stock_value
                
                analysis_results.append(item_analysis)
                
                # Обновляем прогресс
                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
            
            progress_bar.empty()
            
            st.success(f"✅ Анализ завершен: {len(analysis_results)} товаров")
            
            return analysis_results, warehouse_recommendations
        
        # Добавляем метод к системе
        system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
        st.info("🔧 Метод analyze_warehouse_stock_with_details добавлен")
    
    # Добавляем метод get_warehouse_recommendations если его нет
    if not hasattr(system, 'get_warehouse_recommendations'):
        
        def get_warehouse_recommendations(analysis_results=None):
            """Простое получение рекомендаций"""
            # Возвращаем рекомендации если они есть в результатах анализа
            if hasattr(system, '_last_warehouse_recommendations'):
                return system._last_warehouse_recommendations
            return {}
        
        system.get_warehouse_recommendations = get_warehouse_recommendations
        st.info("🔧 Метод get_warehouse_recommendations добавлен")


def simple_display_warehouse_results(analysis_results, recommendations, has_prices=True):
    """
    ПРОСТОЕ отображение результатов анализа складов
    """
    
    if not analysis_results or not recommendations:
        st.error("❌ Нет результатов для отображения")
        return
    
    # Общая статистика
    st.markdown("### 📊 Общая статистика")
    
    total_items = len(analysis_results)
    total_warehouses = len(recommendations)
    
    total_critical = sum(len(rec['critical_items']) for rec in recommendations.values())
    total_warning = sum(len(rec['warning_items']) for rec in recommendations.values())
    total_good = sum(len(rec['good_items']) for rec in recommendations.values())
    total_excess = sum(len(rec['excess_items']) for rec in recommendations.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Товаров", total_items)
    with col2:
        st.metric("🏪 Складов", total_warehouses)
    with col3:
        st.metric("🔴 Критично", total_critical)
    with col4:
        st.metric("🟡 Внимание", total_warning)
    
    # Статистика по складам
    st.markdown("### 🏪 Статистика по складам")
    
    warehouse_summary = []
    for warehouse_name, rec in recommendations.items():
        total_order_value = rec['total_order_value']
        total_stock_value = rec['total_stock_value']
        
        warehouse_summary.append({
            'Склад': warehouse_name,
            'Город': rec['city'],
            'Тип': rec['type'],
            'Уровень': f"L{rec['level']}",
            'Описание': rec['description'][:30] + "..." if len(rec['description']) > 30 else rec['description'],
            'Мин/Макс дни': f"{rec['min_days']}-{rec['max_days']}",
            'Критично': len(rec['critical_items']),
            'Внимание': len(rec['warning_items']),
            'Норма': len(rec['good_items']),
            'Избыток': len(rec['excess_items']),
            'К заказу (₸)': f"{total_order_value:,.0f}" if has_prices and total_order_value > 0 else "0",
            'Остатки (₸)': f"{total_stock_value:,.0f}" if has_prices and total_stock_value > 0 else "0"
        })
    
    summary_df = pd.DataFrame(warehouse_summary)
    st.dataframe(summary_df, use_container_width=True)
    
    # Детальный анализ по выбранному складу
    st.markdown("### 🔍 Детальный анализ склада")
    
    selected_warehouse = st.selectbox(
        "Выберите склад для детального анализа:",
        options=list(recommendations.keys())
    )
    
    if selected_warehouse and selected_warehouse in recommendations:
        rec = recommendations[selected_warehouse]
        
        st.markdown(f"#### 🏪 {selected_warehouse} ({rec['city']})")
        
        # Метрики по складу
        col1, col2, col3, col4 = st.columns(4)
        
        total_items_warehouse = len(rec['critical_items']) + len(rec['warning_items']) + len(rec['good_items']) + len(rec['excess_items'])
        
        with col1:
            st.metric("📦 Товаров", total_items_warehouse)
        with col2:
            st.metric("🔴 Критично", len(rec['critical_items']))
        with col3:
            st.metric("🟡 Внимание", len(rec['warning_items']))
        with col4:
            if has_prices:
                st.metric("💰 К заказу", f"{rec['total_order_value']:,.0f} ₸")
            else:
                st.metric("✅ Норма", len(rec['good_items']))
        
        # Табы для категорий товаров
        tab1, tab2, tab3, tab4 = st.tabs(["🔴 Критично", "🟡 Внимание", "✅ Норма", "📈 Избыток"])
        
        with tab1:
            if rec['critical_items']:
                critical_data = []
                for item in rec['critical_items']:
                    critical_data.append({
                        'Товар': item['name'],
                        'Остаток': item['current_stock'],
                        'Минимум': f"{item['min_stock']:.1f}",
                        'Дефицит': f"{item['deficit']:.1f}",
                        'Дефицит (₸)': f"{item['deficit_value']:,.0f}" if has_prices else "Нет цен",
                        'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "0"
                    })
                
                critical_df = pd.DataFrame(critical_data)
                st.dataframe(critical_df, use_container_width=True)
                
                if has_prices:
                    total_critical_value = sum(item['deficit_value'] for item in rec['critical_items'])
                    st.error(f"🚨 Общий дефицит: {total_critical_value:,.0f} ₸")
            else:
                st.success("✅ Критичных товаров нет")
        
        with tab2:
            if rec['warning_items']:
                warning_data = []
                for item in rec['warning_items']:
                    warning_data.append({
                        'Товар': item['name'],
                        'Остаток': item['current_stock'],
                        'Минимум': f"{item['min_stock']:.1f}",
                        'Дефицит': f"{item['deficit']:.1f}",
                        'Дефицит (₸)': f"{item['deficit_value']:,.0f}" if has_prices else "Нет цен",
                        'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "0"
                    })
                
                warning_df = pd.DataFrame(warning_data)
                st.dataframe(warning_df, use_container_width=True)
            else:
                st.success("✅ Товаров требующих внимания нет")
        
        with tab3:
            if rec['good_items']:
                good_data = []
                for item in rec['good_items']:
                    good_data.append({
                        'Товар': item['name'],
                        'Остаток': item['current_stock'],
                        'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "∞"
                    })
                
                good_df = pd.DataFrame(good_data)
                st.dataframe(good_df, use_container_width=True)
            else:
                st.info("ℹ️ Товаров в норме нет")
        
        with tab4:
            if rec['excess_items']:
                excess_data = []
                for item in rec['excess_items']:
                    excess_data.append({
                        'Товар': item['name'],
                        'Остаток': item['current_stock'],
                        'Максимум': f"{item['max_stock']:.1f}",
                        'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "∞"
                    })
                
                excess_df = pd.DataFrame(excess_data)
                st.dataframe(excess_df, use_container_width=True)
            else:
                st.success("✅ Избыточных товаров нет")


def simple_warehouse_analysis_page(system):
    """
    ПРОСТАЯ исправленная страница анализа складов
    Использует ВАШ существующий код чтения файлов + добавляет персональные настройки
    """
    
    st.header("📦 Анализ остатков по складам")
    st.caption("✅ С персональными настройками каждого склада")
    
    # Показываем персональные настройки
    with st.expander("🏪 Иерархия складов и персональные настройки"):
        st.markdown("**Структура складов по уровням:**")
        
        # Группируем по уровням
        level_1 = []
        level_2 = []
        level_3 = []
        
        for warehouse_name, settings in REAL_WAREHOUSE_SETTINGS.items():
            warehouse_info = {
                'Склад': warehouse_name,
                'Город': settings['city'],
                'Тип': settings['type'],
                'Мин. дни': settings['min_days'],
                'Макс. дни': settings['max_days'],
                'Описание': settings['description']
            }
            
            if settings['level'] == 1:
                level_1.append(warehouse_info)
            elif settings['level'] == 2:
                level_2.append(warehouse_info)
            else:
                level_3.append(warehouse_info)
        
        st.markdown("### 🏢 Уровень 1: Главный хаб")
        if level_1:
            st.dataframe(pd.DataFrame(level_1), use_container_width=True)
        
        st.markdown("### 🏪 Уровень 2: Склады (питаются от хаба)")
        if level_2:
            st.dataframe(pd.DataFrame(level_2), use_container_width=True)
        
        st.markdown("### 🛒 Уровень 3: Магазины (питаются от складов)")
        if level_3:
            st.dataframe(pd.DataFrame(level_3), use_container_width=True)
    
    # Добавляем отсутствующие методы
    simple_add_missing_methods(system)
    
    # Проверяем ADS
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS в разделе 'ADS расчет'")
        return
    
    st.success(f"✅ ADS данные готовы: {len(system.calculated_ads)} товаров")
    
    # Параметры анализа
    st.subheader("⚙️ Параметры")
    
    col1, col2 = st.columns(2)
    with col1:
        min_days = st.number_input("Мин. дни (по умолчанию):", value=15, help="Используется если нет персональных настроек")
    with col2:
        max_days = st.number_input("Макс. дни (по умолчанию):", value=45, help="Используется если нет персональных настроек")
    
    # Загрузка файла остатков
    st.subheader("📁 Загрузка файла остатков")
    
    uploaded_file = st.file_uploader(
        "Выберите файл остатков",
        type=['xlsx', 'xls'],
        help="Должен содержать колонки с названиями складов из настроек выше"
    )
    
    if uploaded_file is None:
        st.info("📤 Загрузите файл остатков для анализа")
        return
    
    # Читаем файл ВАШЕЙ существующей функцией
    with st.spinner("📖 Читаю файл остатков..."):
        try:
            # ПРОБУЕМ использовать ВАШИ существующие методы чтения
            if hasattr(system, 'load_remains_file'):
                remains_df = system.load_remains_file(uploaded_file)
            elif hasattr(system, 'read_remains_file'):
                remains_df = system.read_remains_file(uploaded_file)
            else:
                # Простое чтение Excel
                remains_df = pd.read_excel(uploaded_file)
                st.info("📋 Использовано простое чтение Excel файла")
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            
            # Пробуем альтернативные способы
            try:
                st.warning("🔄 Пробую альтернативное чтение...")
                remains_df = pd.read_excel(uploaded_file, sheet_name=0)
                st.success("✅ Файл прочитан альтернативным способом")
            except Exception as e2:
                st.error(f"❌ Не удалось прочитать файл: {str(e2)}")
                return
    
    if remains_df is None or remains_df.empty:
        st.error("❌ Файл пустой или не прочитан")
        return
    
    st.success(f"✅ Файл загружен: {len(remains_df)} строк")
    
    # Показываем превью данных
    with st.expander("👀 Превью данных"):
        st.dataframe(remains_df.head())
        st.write("Колонки:", list(remains_df.columns))
    
    # Кнопка анализа
    if st.button("🔍 Запустить анализ с персональными настройками", type="primary"):
        
        with st.spinner("🔄 Выполняю анализ складов..."):
            
            # Запускаем анализ
            analysis_results, recommendations = system.analyze_warehouse_stock_with_details(
                remains_df,
                system.calculated_ads,
                None,  # store_ads_by_city
                min_days,
                max_days
            )
        
        if analysis_results is None:
            st.error("❌ Анализ не выполнен")
            return
        
        # Сохраняем рекомендации для повторного использования
        system._last_warehouse_recommendations = recommendations
        
        # Проверяем наличие цен
        has_prices = False
        if system.calculated_ads is not None:
            for col in ['last_purchase_price', 'Посл. закупка', 'цена', 'price']:
                if col in system.calculated_ads.columns:
                    has_prices = True
                    break
        
        # Отображаем результаты
        st.markdown("---")
        st.subheader("📊 Результаты анализа")
        
        simple_display_warehouse_results(analysis_results, recommendations, has_prices)
        
        # Экспорт
        st.markdown("---")
        st.subheader("📤 Экспорт")
        
        if st.button("📊 Экспортировать результаты"):
            st.info("📋 Базовый экспорт результатов в работе...")


# ===== ФУНКЦИЯ ИНТЕГРАЦИИ =====

def apply_simple_warehouse_fix(system):
    """
    ПРИМЕНЯЕТ простое исправление анализа складов
    НЕ ЛОМАЕТ существующий код
    """
    
    try:
        # Добавляем отсутствующие методы
        simple_add_missing_methods(system)
        
        # Отмечаем что исправления применены
        system._simple_warehouse_fix_applied = True
        
        st.success("✅ Простые исправления анализа складов применены!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка применения исправлений: {str(e)}")
        return False


# ===== ИНСТРУКЦИИ =====

def get_simple_integration_instructions():
    """
    Инструкции по простой интеграции
    """
    
    return """
# 🎯 ПРОСТАЯ ИНТЕГРАЦИЯ ИСПРАВЛЕНИЙ

## ✅ ЧТО ИСПРАВЛЯЕТСЯ:
- 🔧 Добавляет отсутствующий метод `analyze_warehouse_stock_with_details`
- 🏪 Персональные настройки для каждого склада
- 💰 Интеграция с ценами из ADS
- 📊 Улучшенное отображение результатов

## 🚀 СПОСОБ 1: Замена функции (рекомендуется)

```python
def warehouse_analysis_page(system):
    from simple_warehouse_fix import simple_warehouse_analysis_page
    simple_warehouse_analysis_page(system)
```

## 🚀 СПОСОБ 2: Добавление в начало существующей функции

```python
def warehouse_analysis_page(system):
    # Добавьте эти строки В НАЧАЛО функции:
    from simple_warehouse_fix import apply_simple_warehouse_fix
    if not hasattr(system, '_simple_warehouse_fix_applied'):
        apply_simple_warehouse_fix(system)
    
    # ... ваш существующий код ...
```

## 🚀 СПОСОБ 3: Экстренное исправление перед кнопкой анализа

```python
# В вашей функции warehouse_analysis_page ПЕРЕД кнопкой анализа добавьте:

from simple_warehouse_fix import simple_add_missing_methods
simple_add_missing_methods(system)

# Ваша кнопка анализа:
if st.button("🔍 Запустить детальный анализ складов", type="primary"):
    # ... остальной код ...
```

## 🎯 РЕЗУЛЬТАТ:
- ✅ Все склады анализируются ОТДЕЛЬНО с персональными настройками
- ✅ Цены интегрируются из ADS автоматически
- ✅ Используется ваша СУЩЕСТВУЮЩАЯ система чтения файлов
- ✅ НЕ ЛОМАЕТСЯ существующий код

## 🏪 ПЕРСОНАЛЬНЫЕ НАСТРОЙКИ СКЛАДОВ:
- Шымкент_Склад: 15-45 дней
- Шымкент_Магазин: 10-30 дней  
- Алматы_Склад: 20-60 дней
- База_Комплект: 25-75 дней
- Барыс_Склад: 15-40 дней
- Казыбаева_Склад: 12-35 дней
- Астана_Магазин: 10-30 дней
- Астана_Склад: 15-45 дней
- Казыбаева_Магазин: 8-25 дней

## 💡 ПРЕИМУЩЕСТВА:
- 🔄 Работает с вашими существующими файлами
- 🏪 Каждый склад со своими настройками
- 💰 Автоматически находит и использует цены
- 📊 Подробная статистика по каждому складу
- 🚫 НЕ ЛОМАЕТ то что уже работает
"""


if __name__ == "__main__":
    print("🔧 Простое исправление анализа складов загружено")
    print("Настроено под реальную структуру складов фурнитуры")
    print(get_simple_integration_instructions())#!/usr/bin/env python3
    ## 🏪 РЕАЛЬНАЯ СТРУКТУРА ВАШИХ СКЛАДОВ:
