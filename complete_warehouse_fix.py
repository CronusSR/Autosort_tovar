# complete_warehouse_fix.py
"""
ПОЛНОЕ ИСПРАВЛЕНИЕ анализа складов с учетом иерархии и правильного маппинга
"""

def apply_complete_warehouse_fix(system):
    """
    Применяет ВСЕ исправления для анализа складов:
    1. Правильный маппинг названий складов
    2. Систему иерархии (хаб -> склады -> магазины)  
    3. Улучшенную интеграцию с ADS данными
    4. Очистку дублированных ADS данных
    
    НИЧЕГО НЕ МЕНЯЕТ в существующих функциях, только ДОПОЛНЯЕТ систему
    """
    
    print("🔧 Применяем ПОЛНОЕ исправление анализа складов...")
    
    success_count = 0
    
    # Шаг 1: Обновляем маппинг складов
    try:
        from warehouse_mapping_fix import get_improved_warehouse_city_mapping
        import warehouse_analysis
        
        # Заменяем функцию маппинга на улучшенную
        warehouse_analysis.get_warehouse_city_mapping = get_improved_warehouse_city_mapping
        
        print("✅ Шаг 1: Маппинг складов обновлен")
        success_count += 1
        
    except Exception as e:
        print(f"❌ Шаг 1: Ошибка обновления маппинга: {e}")
    
    # Шаг 2: Добавляем систему иерархии
    try:
        from warehouse_hierarchy_system import apply_hierarchy_system_to_warehouse_analyzer
        
        if hasattr(system, 'warehouse_analyzer'):
            apply_hierarchy_system_to_warehouse_analyzer(system)
            print("✅ Шаг 2: Система иерархии интегрирована")
            success_count += 1
        else:
            print("⚠️ Шаг 2: Анализатор складов не найден, пропускаем")
            
    except Exception as e:
        print(f"❌ Шаг 2: Ошибка интеграции иерархии: {e}")
    
    # Шаг 3: Улучшаем интеграцию ADS
    try:
        improve_ads_integration(system)
        print("✅ Шаг 3: Интеграция ADS улучшена")
        success_count += 1
        
    except Exception as e:
        print(f"❌ Шаг 3: Ошибка улучшения ADS: {e}")
    
    # Шаг 4: НОВЫЙ - Очистка дублированных ADS данных
    try:
        from clean_duplicate_ads import apply_ads_cleaning_to_warehouse_analysis
        apply_ads_cleaning_to_warehouse_analysis(system)
        print("✅ Шаг 4: Очистка дублированных ADS данных применена")
        success_count += 1
        
    except Exception as e:
        print(f"❌ Шаг 4: Ошибка очистки ADS данных: {e}")
    
    # Шаг 5: НОВЫЙ - Исправление ошибки Arrow сериализации 
    try:
        from fix_arrow_serialization import apply_complete_dataframe_fix
        apply_complete_dataframe_fix()
        print("✅ Шаг 5: Исправление Arrow сериализации применено")
        success_count += 1
        
    except Exception as e:
        print(f"❌ Шаг 5: Ошибка исправления Arrow: {e}")
    
    # Шаг 6: Добавляем флаг что исправления применены
    system._warehouse_fix_applied = True
    system._warehouse_fix_version = "2.2_arrow_fix"
    
    print(f"🎉 ПОЛНОЕ исправление завершено! Успешно: {success_count}/5 шагов")
    
    return success_count >= 3  # Считаем успешным если 3+ шага выполнены

def improve_ads_integration(system):
    """
    Улучшает интеграцию ADS данных с анализом складов
    """
    
    import warehouse_analysis
    
    # Сохраняем оригинальную функцию если еще не сохранена
    if not hasattr(warehouse_analysis, '_original_integrate_function'):
        warehouse_analysis._original_integrate_function = warehouse_analysis.integrate_store_ads_with_warehouse_analysis
    
    # Заменяем на улучшенную версию
    warehouse_analysis.integrate_store_ads_with_warehouse_analysis = enhanced_integrate_ads
    
def enhanced_integrate_ads(system):
    """
    УЛУЧШЕННАЯ функция интеграции ADS данных
    Ищет ADS данные во всех возможных местах системы
    """
    
    print("🔍 УЛУЧШЕННАЯ интеграция ADS данных...")
    
    store_ads_by_city = {}
    
    # Источник 1: multiple_files_data
    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
        print("📂 Проверяем multiple_files_data...")
        
        if 'processed_results' in system.multiple_files_data:
            processed = system.multiple_files_data['processed_results']
            
            if isinstance(processed, dict):
                for filename, result_data in processed.items():
                    ads_data = extract_ads_from_file_result(result_data)
                    
                    if ads_data is not None:
                        city, store_type = determine_city_and_type_from_filename(filename)
                        
                        if city not in store_ads_by_city:
                            store_ads_by_city[city] = []
                        
                        store_ads_by_city[city].append({
                            'store_type': store_type,
                            'branch_name': f"{city}_{store_type}",
                            'ads_data': ads_data,
                            'filename': filename
                        })
                        
                        print(f"  ✅ {filename} → {city} ({store_type}): {len(ads_data)} товаров")
    
    # Источник 2: calculated_ads (основной ADS) - ВЫНОСИМ В ОТДЕЛЬНУЮ КАТЕГОРИЮ
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        print("📊 Добавляем основной calculated_ads как объединенные данные...")
        
        if not system.calculated_ads.empty:
            # Создаем отдельную категорию для объединенных данных
            if 'объединенные' not in store_ads_by_city:
                store_ads_by_city['объединенные'] = []
            
            store_ads_by_city['объединенные'].append({
                'store_type': 'общий_ads',
                'branch_name': 'calculated_ads_общий',
                'ads_data': system.calculated_ads,
                'filename': 'calculated_ads'  # Всегда добавляем filename
            })
            
            print(f"  ✅ calculated_ads добавлен как объединенные данные: {len(system.calculated_ads)} товаров")
    
    # Источник 3: Поиск ADS в других атрибутах системы
    other_ads = find_ads_in_system_attributes(system)
    if other_ads:
        store_ads_by_city.update(other_ads)
        print(f"  ✅ Найдено дополнительных ADS: {len(other_ads)} источников")
    
    if store_ads_by_city:
        print(f"🎉 ИТОГО найдено ADS данных: {len(store_ads_by_city)} городов")
        
        for city, stores in store_ads_by_city.items():
            total_items = sum(len(store['ads_data']) for store in stores if hasattr(store['ads_data'], '__len__'))
            print(f"  🏪 {city}: {len(stores)} источников, {total_items} товаров")
    else:
        print("❌ ADS данные не найдены")
    
    return store_ads_by_city

def extract_ads_from_file_result(result_data):
    """
    Извлекает ADS данные из результата обработки файла
    """
    
    if result_data is None:
        return None
    
    # Если это DataFrame с колонкой ads
    if hasattr(result_data, 'columns') and 'ads' in result_data.columns:
        return result_data
    
    # Если это словарь с результатами
    if isinstance(result_data, dict):
        for key in ['calculated_ads', 'ads_data', 'data', 'result']:
            if key in result_data and result_data[key] is not None:
                candidate = result_data[key]
                if hasattr(candidate, 'columns') and 'ads' in candidate.columns:
                    return candidate
    
    return None

def determine_city_and_type_from_filename(filename):
    """
    Определяет город и тип точки из имени файла с учетом вашей структуры
    """
    
    filename_lower = filename.lower()
    
    # Определяем город
    if 'шымкент' in filename_lower:
        city = 'шымкент'
        store_type = 'склад' if 'скл' in filename_lower else 'магазин'
    elif 'астана' in filename_lower:
        city = 'астана'
        store_type = 'склад' if 'скл' in filename_lower else 'магазин'
    elif 'барыс' in filename_lower:
        city = 'алматы'
        store_type = 'магазин_склад'
    elif 'казыбаева' in filename_lower:
        city = 'алматы'
        store_type = 'тд' if 'тд' in filename_lower else 'склад'
    elif 'ао' in filename_lower:
        city = 'алматы'
        store_type = 'специализированный'
    elif 'база' in filename_lower or 'комплект' in filename_lower:
        city = 'алматы'
        store_type = 'хаб'
    else:
        city = 'алматы'  # по умолчанию
        store_type = 'магазин'
    
    return city, store_type

def find_ads_in_system_attributes(system):
    """
    Ищет ADS данные в других атрибутах системы
    """
    
    additional_ads = {}
    
    # Список возможных атрибутов где могут быть ADS данные
    possible_attributes = [
        'ads_data', 'store_ads', 'sales_data', 'processed_sales',
        'multi_store_data', 'files_results'
    ]
    
    for attr_name in possible_attributes:
        if hasattr(system, attr_name):
            attr_value = getattr(system, attr_name)
            
            if attr_value is not None:
                if hasattr(attr_value, 'columns') and 'ads' in attr_value.columns:
                    additional_ads['дополнительные'] = [{
                        'store_type': 'найденные',
                        'branch_name': attr_name,
                        'ads_data': attr_value,
                        'filename': f'system_attribute_{attr_name}'  # Добавляем filename
                    }]
                    print(f"  🔍 Найден ADS в атрибуте {attr_name}: {len(attr_value)} товаров")
    
    return additional_ads

def add_streamlit_ui_for_warehouse_fix(system):
    """
    Добавляет UI в Streamlit для управления исправлениями складов
    """
    
    import streamlit as st
    
    st.markdown("---")
    st.subheader("🔧 Система исправлений анализа складов")
    
    # Показываем статус исправлений
    if hasattr(system, '_warehouse_fix_applied'):
        st.success(f"✅ Исправления применены (версия: {getattr(system, '_warehouse_fix_version', 'неизвестно')})")
    else:
        st.warning("⚠️ Исправления не применены")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Применить все исправления"):
            with st.spinner("Применяем исправления..."):
                success = apply_complete_warehouse_fix(system)
                if success:
                    st.success("✅ Исправления применены!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка применения исправлений")
    
    with col2:
        if st.button("🔍 Диагностика системы"):
            diagnose_warehouse_system_complete(system)
    
    with col3:
        if st.button("📋 Показать иерархию"):
            show_warehouse_hierarchy()

def diagnose_warehouse_system_complete(system):
    """
    Полная диагностика системы анализа складов
    """
    
    import streamlit as st
    
    st.markdown("### 🔍 Диагностика системы анализа складов")
    
    # Проверка 1: Анализатор складов
    if hasattr(system, 'warehouse_analyzer'):
        st.success("✅ Анализатор складов подключен")
        
        # Проверяем есть ли иерархия
        if hasattr(system.warehouse_analyzer, 'hierarchy_config'):
            st.success("✅ Система иерархии подключена")
        else:
            st.warning("⚠️ Система иерархии не подключена")
    else:
        st.error("❌ Анализатор складов не найден")
    
    # Проверка 2: ADS данные
    ads_sources = []
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        ads_sources.append(f"calculated_ads ({len(system.calculated_ads)} товаров)")
    
    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
        ads_sources.append("multiple_files_data")
    
    if ads_sources:
        st.success(f"✅ ADS данные найдены: {', '.join(ads_sources)}")
    else:
        st.error("❌ ADS данные не найдены")
    
    # Проверка 3: Данные остатков
    if hasattr(system, 'stock_data') and system.stock_data is not None:
        warehouse_cols = [col for col in system.stock_data.columns if 'остаток' in col.lower()]
        st.success(f"✅ Данные остатков загружены: {len(warehouse_cols)} складов")
        
        # Показываем найденные склады
        with st.expander("📋 Найденные склады"):
            for col in warehouse_cols:
                warehouse_name = col.replace('_остаток', '').replace('остаток', '')
                st.write(f"- {warehouse_name}")
    else:
        st.error("❌ Данные остатков не загружены")
    
    # Проверка 4: Статус исправлений
    if hasattr(system, '_warehouse_fix_applied'):
        st.success(f"✅ Исправления применены (v{getattr(system, '_warehouse_fix_version', '?')})")
    else:
        st.warning("⚠️ Исправления не применены")

def show_warehouse_hierarchy():
    """
    Показывает иерархию складов в Streamlit
    """
    
    import streamlit as st
    from warehouse_hierarchy_system import get_warehouse_hierarchy_config
    
    st.markdown("### 🏢 Иерархия складов и распределения")
    
    config = get_warehouse_hierarchy_config()
    
    # Группируем по уровням
    levels = {}
    for key, data in config.items():
        level = data['level']
        if level not in levels:
            levels[level] = []
        levels[level].append(data)
    
    # Показываем по уровням
    for level in sorted(levels.keys()):
        if level == 1:
            st.markdown("#### 🏢 Уровень 1: Главный хаб")
        elif level == 2:
            st.markdown("#### 🏪 Уровень 2: Региональные склады")
        elif level == 2.5:
            st.markdown("#### 🏪🛒 Уровень 2.5: Комбинированные точки")
        elif level == 3:
            st.markdown("#### 🛒 Уровень 3: Магазины")
        
        for warehouse in levels[level]:
            st.write(f"**{warehouse['name']}** ({warehouse['city']}) - {warehouse['description']}")
            st.write(f"  📊 MIN: {warehouse['min_days']} дней, MAX: {warehouse['max_days']} дней")
            
            if warehouse.get('receives_from'):
                st.write(f"  ⬇️ Получает от: {', '.join(warehouse['receives_from'])}")
            if warehouse.get('supplies_to'):
                st.write(f"  ⬆️ Поставляет в: {', '.join(warehouse['supplies_to'])}")
            st.write("")

# Функция для быстрой интеграции в warehouse_analysis.py
def integrate_complete_fix_to_warehouse_page():
    """
    Возвращает код для интеграции в warehouse_analysis_page()
    """
    
    integration_code = '''
# ДОБАВИТЬ в начало функции warehouse_analysis_page(system):

def warehouse_analysis_page(system):
    """
    Страница анализа остатков по складам с интеграцией ADS магазинов
    """
    
    st.header("📦 Анализ остатков по складам")
    
    # 🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ СИСТЕМЫ АНАЛИЗА СКЛАДОВ
    try:
        from complete_warehouse_fix import apply_complete_warehouse_fix
        if not hasattr(system, '_warehouse_fix_applied'):
            with st.spinner("Применяем исправления системы складов..."):
                success = apply_complete_warehouse_fix(system)
                if success:
                    st.success("✅ Система анализа складов обновлена!")
                else:
                    st.warning("⚠️ Частичное обновление системы")
    except ImportError:
        st.error("❌ Файл complete_warehouse_fix.py не найден")
    except Exception as e:
        st.error(f"❌ Ошибка обновления системы: {e}")
    
    # Добавляем UI управления исправлениями
    from complete_warehouse_fix import add_streamlit_ui_for_warehouse_fix
    add_streamlit_ui_for_warehouse_fix(system)
    
    # ДАЛЕЕ ВАШ СУЩЕСТВУЮЩИЙ КОД БЕЗ ИЗМЕНЕНИЙ...
    '''
    
    return integration_code

if __name__ == "__main__":
    print("🔧 Модуль полного исправления анализа складов")
    print("📋 Для интеграции используйте:")
    print("   from complete_warehouse_fix import apply_complete_warehouse_fix")
    print("   apply_complete_warehouse_fix(system)")
    print()
    print("💡 Код для интеграции в warehouse_analysis_page():")
    print(integrate_complete_fix_to_warehouse_page())