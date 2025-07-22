"""Анализ нового формата файла остатков для понимания структуры"""

import json
from collections import defaultdict

def analyze_stock_file():
    # Читаем файл
    with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    print(f"Дата остатков: {data['ДатаОстатков']}")
    print(f"Дата выгрузки: {data['ДатаВыгрузки']}")
    print(f"Всего складов: {len(data['ОстаткиПоСкладам'])}\n")
    
    # Анализ каждого склада
    for idx, warehouse in enumerate(data['ОстаткиПоСкладам']):
        print(f"\n{idx+1}. Склад: {warehouse['Склад']}")
        print(f"   Город: {warehouse.get('Город', 'Не указан')}")
        print(f"   Количество позиций: {len(warehouse['Остатки'])}")
        
        # Подсчет по категориям
        categories = defaultdict(int)
        total_cost = 0
        total_qty = 0
        
        for item in warehouse['Остатки']:
            # Извлекаем основную категорию
            path_parts = item['ПутьКатегорий'].strip('/').split('/')
            if path_parts:
                main_category = path_parts[-1] if path_parts[-1] else path_parts[-2]
                categories[main_category] += 1
            
            total_cost += item['Стоимость']
            total_qty += item['Количество']
        
        print(f"   Общая стоимость: {total_cost:,.2f}")
        print(f"   Общее количество: {total_qty:,}")
        print(f"   Топ категорий:")
        
        # Показываем топ-5 категорий
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in sorted_cats:
            print(f"      - {cat}: {count} позиций")
    
    # Пример структуры товара
    print("\n\nПример структуры товара:")
    if data['ОстаткиПоСкладам'] and data['ОстаткиПоСкладам'][0]['Остатки']:
        example = data['ОстаткиПоСкладам'][0]['Остатки'][0]
        for key, value in example.items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    analyze_stock_file()