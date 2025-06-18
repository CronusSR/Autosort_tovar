# warehouse_mapping_fix.py
"""
Исправление маппинга складов для корректного распознавания названий из файла остатков
"""

def get_improved_warehouse_city_mapping():
    """
    Маппинг складов по городам с учетом РЕАЛЬНОЙ структуры сети
    
    СТРУКТУРА:
    🏢 ГЛАВНЫЙ ХАБ (Алматы): База Склад Фурнитура Комплект
    🏪 РЕГИОНАЛЬНЫЕ СКЛАДЫ: питаются от главного хаба
    🛒 МАГАЗИНЫ: питаются от региональных складов или напрямую от хаба
    📊 ОБЪЕДИНЕННЫЕ: общие ADS данные для всей сети
    """
    return {
        'алматы': [
            # 🏢 ГЛАВНЫЙ ХАБ - База Склад Фурнитура Комплект
            'База Склад Фурнитура Комплект',
            'База_Комплект',
            
            # 🛒 МАГАЗИНЫ В АЛМАТЫ
            'ТД Казыбаева ФУРНИТУРА магазин',  # магазин
            'Казыбаева_магазин',
            
            'Барыс Склад Фурнитура TRADE',     # магазин+склад
            'Барыс_TRADE',
            
            'АО Склад Фурнитура TRADE',        # магазин (кромочные материалы)
            'АО_TRADE',
            
            # 🏪 РЕГИОНАЛЬНЫЙ СКЛАД для магазина Казыбаева
            'Казыбаева Склад Фурнитура TRADE', # склад 2-го уровня
            'Казыбаева_TRADE',
            
            # Поиск по ключевым словам
            'алматы',
            'казыбаева',
            'барыс',
            'база',
            'комплект'
        ],
        'шымкент': [
            # 🛒 МАГАЗИН В ШЫМКЕНТЕ
            '6 Склад фурнитуры "Овощная база" Магазин',  # магазин
            'Овощная_база_Магазин',
            
            # 🏪 РЕГИОНАЛЬНЫЙ СКЛАД для Шымкента
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',  # склад 2-го уровня
            'Шымкент_Овощная_база',
            
            # Поиск по ключевым словам
            'шымкент',
            'овощная'
        ],
        'астана': [
            # 🛒 МАГАЗИН В АСТАНЕ
            'Магазин фурнитуры',              # магазин
            'Магазин_фурнитуры',
            
            # 🏪 РЕГИОНАЛЬНЫЙ СКЛАД для Астаны
            'склад фурнитура № 1',            # склад 2-го уровня
            'Склад_1',
            
            # Поиск по ключевым словам
            'астана',
            'фурнитура'
        ],
        'объединенные': [
            # 📊 ОБЪЕДИНЕННЫЕ ADS ДАННЫЕ для всей сети
            'calculated_ads_общий',
            'sales_data',
            'общий_ads',
            'объединенные_данные',
            
            # Поиск по ключевым словам
            'calculated',
            'общий',
            'объединенные'
        ]
    }

def smart_warehouse_mapping(warehouse_name, warehouse_city_mapping):
    """
    Умное сопоставление названия склада с городом с использованием ключевых слов
    
    Args:
        warehouse_name (str): Название склада из файла остатков
        warehouse_city_mapping (dict): Маппинг городов и складов
        
    Returns:
        str or None: Найденный город или None
    """
    
    if not isinstance(warehouse_name, str):
        return None
        
    warehouse_name_lower = warehouse_name.lower()
    
    # Проходим по каждому городу и его складам
    for city, warehouses in warehouse_city_mapping.items():
        for warehouse_pattern in warehouses:
            warehouse_pattern_lower = warehouse_pattern.lower()
            
            # Точное совпадение
            if warehouse_name_lower == warehouse_pattern_lower:
                return city
                
            # Поиск вхождения ключевых слов
            if len(warehouse_pattern_lower) <= 15:  # Короткие строки считаем ключевыми словами
                if warehouse_pattern_lower in warehouse_name_lower:
                    return city
    
    # Если не найден точный маппинг, используем эвристику
    if 'шымкент' in warehouse_name_lower or 'овощная' in warehouse_name_lower:
        return 'шымкент'
    elif 'барыс' in warehouse_name_lower:
        return 'барыс'  
    elif 'казыбаева' in warehouse_name_lower:
        return 'казыбаева'
    elif 'астана' in warehouse_name_lower or 'ао' in warehouse_name_lower:
        return 'астана'
    elif any(word in warehouse_name_lower for word in ['фурнитура', 'склад', 'база', 'комплект']):
        return 'общие'
    
    return None

def apply_improved_warehouse_mapping_to_system(system):
    """
    Применяет улучшенный маппинг складов к системе анализа складов
    """
    
    if not hasattr(system, 'warehouse_analyzer'):
        print("❌ Анализатор складов не найден в системе")
        return False
    
    # Заменяем функцию get_warehouse_city_mapping в warehouse_analysis.py
    import warehouse_analysis
    warehouse_analysis.get_warehouse_city_mapping = get_improved_warehouse_city_mapping
    
    # Также можем добавить smart_warehouse_mapping как вспомогательную функцию
    warehouse_analysis.smart_warehouse_mapping = smart_warehouse_mapping
    
    print("✅ Улучшенный маппинг складов применен к системе")
    print("📋 Теперь система распознает:")
    
    mapping = get_improved_warehouse_city_mapping()
    for city, warehouses in mapping.items():
        print(f"  🏪 {city.upper()}:")
        for warehouse in warehouses[:3]:  # Показываем первые 3 для краткости
            print(f"    - {warehouse}")
        if len(warehouses) > 3:
            print(f"    ... и еще {len(warehouses)-3} вариантов")
    
    return True

def diagnose_warehouse_mapping_issues(system, remains_df):
    """
    Диагностирует проблемы с маппингом складов
    
    Args:
        system: Система анализа
        remains_df: DataFrame с остатками
    """
    
    print("🔍 Диагностика маппинга складов...")
    
    if remains_df is None or remains_df.empty:
        print("❌ Файл остатков не загружен")
        return
    
    # Получаем все колонки, которые могут быть складами
    potential_warehouse_cols = [col for col in remains_df.columns 
                               if 'остаток' in col.lower() or 'склад' in col.lower()]
    
    print(f"📊 Найдено потенциальных складов: {len(potential_warehouse_cols)}")
    
    # Анализируем каждую колонку
    warehouse_city_mapping = get_improved_warehouse_city_mapping()
    
    recognized_warehouses = 0
    unrecognized_warehouses = []
    
    for col in potential_warehouse_cols:
        # Извлекаем название склада из имени колонки
        warehouse_name = col.replace('_остаток', '').replace('остаток', '').strip()
        
        # Проверяем маппинг
        city = smart_warehouse_mapping(warehouse_name, warehouse_city_mapping)
        
        if city:
            recognized_warehouses += 1
            print(f"  ✅ {warehouse_name} → {city}")
        else:
            unrecognized_warehouses.append(warehouse_name)
            print(f"  ❌ {warehouse_name} → НЕ РАСПОЗНАН")
    
    print(f"\n📈 Результаты диагностики:")
    print(f"  ✅ Распознано: {recognized_warehouses}")
    print(f"  ❌ Не распознано: {len(unrecognized_warehouses)}")
    
    if unrecognized_warehouses:
        print(f"\n🔧 Нераспознанные склады:")
        for warehouse in unrecognized_warehouses:
            print(f"  - '{warehouse}'")
        
        print(f"\n💡 Рекомендация: Добавьте эти склады в функцию get_improved_warehouse_city_mapping()")

def test_warehouse_mapping():
    """
    Тестирует маппинг складов на примерах из вашего описания
    """
    
    print("🧪 Тестирование маппинга складов...")
    
    test_warehouses = [
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
        '6 Склад фурнитуры "Овощная база" Магазин', 
        'АО Склад Фурнитура TRADE',
        'База Склад Фурнитура Комплект',
        'Барыс Склад Фурнитура TRADE',
        'Казыбаева Склад Фурнитура TRADE',
        'Магазин фурнитуры',
        'склад фурнитура № 1',
        'ТД Казыбаева ФУРНИТУРА магазин'
    ]
    
    warehouse_city_mapping = get_improved_warehouse_city_mapping()
    
    for warehouse in test_warehouses:
        city = smart_warehouse_mapping(warehouse, warehouse_city_mapping)
        status = "✅" if city else "❌"
        city_name = city if city else "НЕ РАСПОЗНАН"
        print(f"  {status} '{warehouse}' → {city_name}")

if __name__ == "__main__":
    test_warehouse_mapping()