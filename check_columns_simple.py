#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая проверка колонок из описания пользователя
"""

def test_column_mapping():
    """Тестируем маппинг на основе описанных колонок"""
    
    # Колонки из описания пользователя
    columns = [
        "КАТЕГОРИЯ",
        "ПОДКАТЕГОРИЯ", 
        "Номенклатура",
        "ТД Казыбаева ФУРНИТУРА магазин ( продажи 01.07.2024-01.07.2025 гг.)",
        "Казыбаева Склад Фурнитура TRADE ( продажи 01.07.2024-01.07.2025 гг.)",
        "Барыс Склад Фурнитура TRADE ( продажи 01.07.2024-01.07.2025 гг.)",
        "АО Склад Фурнитура TRADE ( продажи 01.07.2024-01.07.2025 гг.)",
        "Магазин фурнитуры ( продажи 01.07.2024-01.07.2025 гг.)",
        "склад фурнитура № 1 ( продажи 01.07.2024-01.07.2025 гг.)",
        "6 Склад фурнитуры Овощная база Магазин ( продажи 01.07.2024-01.07.2025 гг.)",
        "4 Склад фурнитуры АЗМ Шымкент Овощная база ( продажи 01.07.2024-01.07.2025 гг.)"
    ]
    
    print("📋 Тестируем маппинг колонок...")
    print(f"Всего колонок: {len(columns)}")
    
    # Тестируем наш маппинг
    branch_column_mapping = {
        'казыбаева.*магазин': 'казыбаева_магазин',
        'казыбаева.*склад.*trade': 'казыбаева_склад', 
        'барыс.*склад.*trade': 'барыс',
        'ао.*склад.*trade': 'ао_склад',
        'магазин фурнитуры': 'астана_магазин',
        'склад фурнитура № 1': 'астана_склад',
        'овощная база магазин': 'шымкент_магазин',
        'азм шымкент.*овощная база': 'шымкент_склад'
    }
    
    import re
    
    branch_columns = {}
    
    for column in columns:
        column_lower = column.lower()
        
        # Пропускаем служебные колонки
        if any(skip in column_lower for skip in ['категория', 'подкатегория', 'номенклатура']):
            print(f"⏭️  Пропуск: {column}")
            continue
        
        # Ищем соответствие с филиалами по ключевым словам
        found = False
        for pattern, system_name in branch_column_mapping.items():
            if re.search(pattern, column_lower):
                branch_columns[column] = system_name
                print(f"✅ {system_name}: {column}")
                found = True
                break
        
        if not found:
            print(f"❌ НЕ НАЙДЕНО: {column}")
    
    print(f"\n📊 Результат:")
    print(f"Определено филиалов: {len(branch_columns)}")
    print(f"Не определено: {len([c for c in columns if 'категория' not in c.lower() and 'номенклатура' not in c.lower()]) - len(branch_columns)}")
    
    # Улучшенный маппинг
    print(f"\n🔧 Предлагаю улучшенный маппинг:")
    
    improved_mapping = {
        r'тд казыбаева.*магазин': 'казыбаева_магазин',
        r'казыбаева.*склад.*trade': 'казыбаева_склад', 
        r'барыс.*склад.*trade': 'барыс',
        r'ао.*склад.*trade': 'ао_склад',
        r'магазин фурнитуры': 'астана_магазин',
        r'склад фурнитура № 1': 'астана_склад',
        r'6.*склад.*овощная база.*магазин': 'шымкент_магазин',
        r'4.*склад.*азм.*шымкент.*овощная база': 'шымкент_склад'
    }
    
    print("Новый маппинг:")
    for pattern, name in improved_mapping.items():
        print(f"  {name}: {pattern}")
    
    # Тестируем улучшенный маппинг
    print(f"\n🧪 Тестируем улучшенный маппинг:")
    
    improved_branches = {}
    for column in columns:
        column_lower = column.lower()
        
        if any(skip in column_lower for skip in ['категория', 'подкатегория', 'номенклатура']):
            continue
        
        found = False
        for pattern, system_name in improved_mapping.items():
            if re.search(pattern, column_lower):
                improved_branches[column] = system_name
                print(f"✅ {system_name}: {column}")
                found = True
                break
        
        if not found:
            print(f"❌ НЕ НАЙДЕНО: {column}")
    
    print(f"\nИтого определено: {len(improved_branches)} из {len([c for c in columns if 'категория' not in c.lower() and 'номенклатура' not in c.lower()])}")

if __name__ == "__main__":
    test_column_mapping()