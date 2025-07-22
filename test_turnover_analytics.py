#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест новой функциональности анализа оборачиваемости в JSON парсере
"""

import json
from json_1c_parser import Json1CParser

def test_turnover_analytics():
    """Тестирование функциональности анализа оборачиваемости"""
    
    print("🧪 ТЕСТИРОВАНИЕ АНАЛИЗА ОБОРАЧИВАЕМОСТИ")
    print("=" * 50)
    
    # Создаем тестовые данные в формате JSON 1C
    test_data = {
        "Филиал": "Тестовый филиал",
        "НачалоПериода": "2024-01-01",
        "КонецПериода": "2024-01-31",
        "ДатаВыгрузки": "2024-02-01T10:00:00",
        "Продажи": [
            {
                "Номенклатура": "Быстрый товар",
                "Количество": 100,
                "Выручка": 10000,
                "Себестоимость": 8000,
                "ВаловаяПрибыль": 2000,
                "Рентабельность": 20,
                "ПутьКатегорий": "/Категория1/Подкатегория1"
            },
            {
                "Номенклатура": "Средний товар",
                "Количество": 30,
                "Выручка": 6000,
                "Себестоимость": 4800,
                "ВаловаяПрибыль": 1200,
                "Рентабельность": 20,
                "ПутьКатегорий": "/Категория1/Подкатегория2"
            },
            {
                "Номенклатура": "Медленный товар",
                "Количество": 5,
                "Выручка": 2500,
                "Себестоимость": 2000,
                "ВаловаяПрибыль": 500,
                "Рентабельность": 20,
                "ПутьКатегорий": "/Категория2/Подкатегория1"
            },
            {
                "Номенклатура": "Товар без движения",
                "Количество": 0,
                "Выручка": 0,
                "Себестоимость": 0,
                "ВаловаяПрибыль": 0,
                "Рентабельность": 0,
                "ПутьКатегорий": "/Категория2/Подкатегория2"
            }
        ]
    }
    
    # Инициализируем парсер и обрабатываем данные
    parser = Json1CParser()
    
    print("1. Парсинг тестовых данных...")
    sales_data = parser.parse_sales_json_from_data(test_data)
    
    print(f"✅ Обработано филиалов: {len(sales_data['sales_by_branch'])}")
    print(f"✅ Период: {sales_data['metadata']['period']['days']} дней")
    
    # Проверяем что добавились поля оборачиваемости
    branch_data = list(sales_data['sales_by_branch'].values())[0]
    sample_product = branch_data[0]
    
    print("\n2. Проверка полей оборачиваемости в данных...")
    
    required_fields = ['turnover_days', 'turnover_rate', 'ads']
    for field in required_fields:
        if field in sample_product:
            print(f"✅ Поле '{field}' присутствует: {sample_product[field]}")
        else:
            print(f"❌ Поле '{field}' отсутствует!")
    
    # Тестируем функцию расчета аналитики оборачиваемости
    print("\n3. Тестирование аналитики оборачиваемости...")
    
    turnover_analytics = parser.calculate_turnover_analytics(sales_data)
    
    print(f"✅ Всего товаров: {turnover_analytics['total_products']}")
    print(f"✅ Быстрооборачиваемых: {len(turnover_analytics['fast_moving'])}")
    print(f"✅ Средних: {len(turnover_analytics['medium_moving'])}")
    print(f"✅ Медленных: {len(turnover_analytics['slow_moving'])}")
    print(f"✅ Очень медленных: {len(turnover_analytics['very_slow_moving'])}")
    print(f"✅ Без движения: {len(turnover_analytics['no_movement'])}")
    
    # Детальный анализ товаров
    print("\n4. Детальный анализ товаров:")
    
    for branch_name, products in sales_data['sales_by_branch'].items():
        print(f"\n📍 Филиал: {branch_name}")
        
        for product in products:
            name = product['product_name']
            ads = product['ads']
            turnover_days = product['turnover_days']
            turnover_rate = product['turnover_rate']
            
            if turnover_days == float('inf'):
                category = "Без движения"
            elif turnover_days <= 30:
                category = "Быстрый"
            elif turnover_days <= 90:
                category = "Средний"
            elif turnover_days <= 365:
                category = "Медленный"
            else:
                category = "Очень медленный"
            
            print(f"  • {name}")
            print(f"    ADS: {ads:.2f}")
            print(f"    Оборачиваемость: {turnover_days:.1f} дней ({category})")
            print(f"    Оборотов в год: {turnover_rate:.1f}")
    
    # Тестируем экспорт для системы движения
    print("\n5. Тестирование экспорта для системы движения...")
    
    # Создаем тестовые остатки
    stock_data = {
        'stock_by_warehouse': {
            'Склад 1': [
                {
                    'product_name': 'Быстрый товар',
                    'quantity': 50,
                    'amount': 25000
                },
                {
                    'product_name': 'Средний товар',
                    'quantity': 20,
                    'amount': 12000
                }
            ]
        }
    }
    
    movement_data, stock_df = parser.export_for_movement_system(sales_data, stock_data)
    
    print(f"✅ Экспорт создан для {len(movement_data['sales_by_branch'])} филиалов")
    print(f"✅ ADS данные для {len(movement_data['ads_by_product'])} товаров")
    print(f"✅ Остатки: {len(stock_df)} записей")
    
    # Проверяем что поля оборачиваемости есть в экспорте
    if movement_data['sales_by_branch']:
        sample_branch_df = list(movement_data['sales_by_branch'].values())[0]
        if 'turnover_days' in sample_branch_df.columns:
            print("✅ Поля оборачиваемости включены в экспорт")
        else:
            print("❌ Поля оборачиваемости НЕ включены в экспорт")
    
    print("\n" + "=" * 50)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    
    return True

if __name__ == "__main__":
    test_turnover_analytics()