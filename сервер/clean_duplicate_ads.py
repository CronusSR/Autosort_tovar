# clean_duplicate_ads.py
"""
Очистка дублированных ADS данных и правильная группировка по категориям
"""

def clean_and_organize_store_ads(store_ads_by_city):
    """
    Очищает дублированные данные и правильно организует ADS по категориям
    
    Args:
        store_ads_by_city: Словарь с ADS данными по городам
        
    Returns:
        dict: Очищенные и организованные данные
    """
    
    print("🧹 Очистка и организация ADS данных...")
    
    cleaned_data = {
        'города': {},
        'объединенные': [],
        'дополнительные': []
    }
    
    unique_ads_data = {}  # Для отслеживания уникальных данных
    
    for category, stores in store_ads_by_city.items():
        print(f"📂 Обрабатываем категорию: {category}")
        
        for store in stores:
            store_name = store['branch_name']
            ads_data = store['ads_data']
            
            # Создаем уникальный идентификатор для данных
            data_id = create_data_identifier(ads_data)
            
            # Определяем тип данных
            filename = store.get('filename', '')  # Безопасное получение filename
            if is_combined_data(store_name, filename):
                # Это объединенные данные
                if data_id not in unique_ads_data:
                    cleaned_data['объединенные'].append({
                        'name': 'Объединенные ADS данные',
                        'description': 'Общие данные продаж по всей сети',
                        'store_type': 'объединенные',
                        'ads_data': ads_data,
                        'items_count': len(ads_data),
                        'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
                    })
                    unique_ads_data[data_id] = 'объединенные'
                    print(f"  ✅ Добавлены объединенные данные: {len(ads_data)} товаров")
            
            elif category in ['алматы', 'шымкент', 'астана']:
                # Это данные конкретного города
                if category not in cleaned_data['города']:
                    cleaned_data['города'][category] = []
                
                # Проверяем уникальность в рамках города
                city_data_id = f"{category}_{data_id}"
                if city_data_id not in unique_ads_data:
                    cleaned_data['города'][category].append({
                        'name': store_name,
                        'description': f"Данные {store['store_type']} в г.{category.title()}",
                        'store_type': store['store_type'],
                        'ads_data': ads_data,
                        'items_count': len(ads_data),
                        'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0,
                        'filename': store.get('filename', 'unknown')
                    })
                    unique_ads_data[city_data_id] = category
                    print(f"  ✅ Добавлен {store_name} в {category}: {len(ads_data)} товаров")
                else:
                    print(f"  ⚠️ Пропущен дубликат {store_name} в {category}")
            
            else:
                # Дополнительные данные
                if data_id not in unique_ads_data:
                    cleaned_data['дополнительные'].append({
                        'name': store_name,
                        'description': f"Дополнительные данные ({category})",
                        'store_type': store['store_type'],
                        'ads_data': ads_data,
                        'items_count': len(ads_data),
                        'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
                    })
                    unique_ads_data[data_id] = 'дополнительные'
                    print(f"  ✅ Добавлены дополнительные данные {store_name}: {len(ads_data)} товаров")
    
    # Статистика очистки
    print(f"\n📊 Результаты очистки:")
    print(f"  🏙️ Городов с данными: {len(cleaned_data['города'])}")
    print(f"  📊 Объединенных источников: {len(cleaned_data['объединенные'])}")
    print(f"  📁 Дополнительных источников: {len(cleaned_data['дополнительные'])}")
    
    for city, stores in cleaned_data['города'].items():
        print(f"    {city.title()}: {len(stores)} источников")
    
    return cleaned_data

def create_data_identifier(ads_data):
    """
    Создает уникальный идентификатор для ADS данных
    """
    
    if ads_data is None or ads_data.empty:
        return "empty_data"
    
    # Используем размер + сумму ADS + первые несколько названий товаров
    size = len(ads_data)
    ads_sum = ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
    
    # Берем первые 3 названия товаров для идентификации
    first_items = ""
    if 'номенклатура' in ads_data.columns:
        first_items = "_".join(ads_data['номенклатура'].head(3).astype(str))[:50]
    
    identifier = f"{size}_{ads_sum:.2f}_{hash(first_items) % 10000}"
    return identifier

def is_combined_data(store_name, filename):
    """
    Определяет, являются ли данные объединенными
    """
    
    combined_indicators = [
        'calculated_ads',
        'общий',
        'объединен',
        'sales_data',
        'combined'
    ]
    
    store_name_lower = store_name.lower() if store_name else ""
    filename_lower = filename.lower() if filename else ""
    
    return any(indicator in store_name_lower or indicator in filename_lower 
              for indicator in combined_indicators)

def display_cleaned_ads_data_in_streamlit(cleaned_data):
    """
    Отображает очищенные ADS данные в Streamlit
    """
    
    import streamlit as st
    
    st.subheader("📊 Организованные ADS данные")
    
    # Объединенные данные
    if cleaned_data['объединенные']:
        with st.expander("📊 Объединенные данные по всей сети", expanded=True):
            for data in cleaned_data['объединенные']:
                st.write(f"**{data['name']}**")
                st.write(f"📈 Товаров: {data['items_count']}, Общий ADS: {data['total_ads']:.2f}")
                st.write(f"📝 {data['description']}")
                st.write("---")
    
    # Данные по городам
    if cleaned_data['города']:
        st.subheader("🏙️ Данные по городам")
        
        for city, stores in cleaned_data['города'].items():
            with st.expander(f"🏪 {city.title()}: {len(stores)} источников"):
                for store in stores:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**{store['name']}**")
                        st.write(f"Тип: {store['store_type']}")
                    
                    with col2:
                        st.metric("Товаров", store['items_count'])
                    
                    with col3:
                        st.metric("ADS", f"{store['total_ads']:.2f}")
                    
                    st.write(f"📝 {store['description']}")
                    if 'filename' in store:
                        st.caption(f"Источник: {store['filename']}")
                    st.write("---")
    
    # Дополнительные данные
    if cleaned_data['дополнительные']:
        with st.expander(f"📁 Дополнительные источники ({len(cleaned_data['дополнительные'])})"):
            for data in cleaned_data['дополнительные']:
                st.write(f"**{data['name']}** - {data['items_count']} товаров, ADS: {data['total_ads']:.2f}")

def convert_cleaned_data_to_old_format(cleaned_data):
    """
    Конвертирует очищенные данные в старый формат для совместимости
    """
    
    store_ads_by_city = {}
    
    # Добавляем данные по городам
    for city, stores in cleaned_data['города'].items():
        store_ads_by_city[city] = []
        for store in stores:
            store_ads_by_city[city].append({
                'store_type': store['store_type'],
                'branch_name': store['name'],
                'ads_data': store['ads_data']
            })
    
    # Добавляем объединенные данные
    if cleaned_data['объединенные']:
        store_ads_by_city['объединенные'] = []
        for data in cleaned_data['объединенные']:
            store_ads_by_city['объединенные'].append({
                'store_type': 'объединенные',
                'branch_name': data['name'],
                'ads_data': data['ads_data']
            })
    
    return store_ads_by_city

def apply_ads_cleaning_to_warehouse_analysis(system):
    """
    Применяет очистку ADS данных к системе анализа складов
    """
    
    try:
        import warehouse_analysis
        
        # Сохраняем оригинальную функцию
        if not hasattr(warehouse_analysis, '_original_integrate_store_ads'):
            warehouse_analysis._original_integrate_store_ads = warehouse_analysis.integrate_store_ads_with_warehouse_analysis
        
        # Заменяем на версию с очисткой
        def integrate_with_cleaning(system):
            # Получаем данные обычным способом
            raw_data = warehouse_analysis._original_integrate_store_ads(system)
            
            if raw_data:
                # Очищаем и организуем данные
                cleaned_data = clean_and_organize_store_ads(raw_data)
                
                # Конвертируем обратно в старый формат для совместимости
                return convert_cleaned_data_to_old_format(cleaned_data)
            
            return raw_data
        
        warehouse_analysis.integrate_store_ads_with_warehouse_analysis = integrate_with_cleaning
        
        print("✅ Очистка ADS данных применена к системе анализа складов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения очистки ADS: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Модуль очистки дублированных ADS данных")
    print("📋 Использование:")
    print("   from clean_duplicate_ads import apply_ads_cleaning_to_warehouse_analysis")
    print("   apply_ads_cleaning_to_warehouse_analysis(system)")