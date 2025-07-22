#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест нового JSON формата остатков
"""

import json
import os
from json_1c_parser import Json1CParser

def test_stock_json_format():
    """Тест парсинга JSON файла остатков"""
    
    print("=== Тестирование нового JSON формата остатков ===")
    
    filename = 'stock_example_2025-07-08.json'
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return
    
    try:
        parser = Json1CParser()
        
        # Читаем файл
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Файл {filename} успешно прочитан")
        
        # Проверяем структуру
        print(f"✅ Дата остатков: {data.get('ДатаОстатков')}")
        print(f"✅ Дата выгрузки: {data.get('ДатаВыгрузки')}")
        print(f"✅ Организация: {data.get('Организация')}")
        print(f"✅ Складов: {len(data.get('ОстаткиПоСкладам', []))}")
        
        # Парсим данные
        result = parser.parse_stock_json_from_dict(data)
        
        print(f"\n📊 Результат парсинга:")
        print(f"✅ Дата остатков: {result['date']}")
        print(f"✅ Дата выгрузки: {result['created_at']}")
        print(f"✅ Организация: {result['organization']}")
        print(f"✅ Складов обработано: {len(result['stock_by_warehouse'])}")
        
        # Анализируем склады
        print(f"\n📋 Детальная информация по складам:")
        for warehouse_name, products in result['stock_by_warehouse'].items():
            warehouse_info = result['warehouse_info'].get(warehouse_name, {})
            city = warehouse_info.get('city', '')
            warehouse_type = warehouse_info.get('type', '')
            
            print(f"  🏢 {warehouse_name}")
            if city:
                print(f"     📍 Город: {city}")
            if warehouse_type:
                print(f"     🏷️  Тип: {warehouse_type}")
            print(f"     📦 Товаров: {len(products)}")
            
            # Показываем первые 3 товара
            for i, product in enumerate(products[:3]):
                print(f"     {i+1}. {product['product_name'][:50]}... | Остаток: {product['quantity']} {product['unit']}")
            
            if len(products) > 3:
                print(f"     ... и еще {len(products) - 3} товаров")
            print()
        
        # Общая статистика
        total_products = sum(len(products) for products in result['stock_by_warehouse'].values())
        unique_products = set()
        for products in result['stock_by_warehouse'].values():
            for product in products:
                unique_products.add(product['product_name'])
        
        print(f"📊 Общая статистика:")
        print(f"✅ Всего товаров с остатками: {total_products}")
        print(f"✅ Уникальных товаров: {len(unique_products)}")
        print(f"✅ Средний остаток на склад: {total_products / len(result['stock_by_warehouse']):.1f}")
        
        # Проверим несколько товаров по остаткам
        print(f"\n🔍 Анализ остатков по товарам:")
        for product_name in list(unique_products)[:3]:
            print(f"  📦 {product_name}:")
            total_qty = 0
            for warehouse_name, products in result['stock_by_warehouse'].items():
                for product in products:
                    if product['product_name'] == product_name:
                        print(f"     - {warehouse_name}: {product['quantity']} {product['unit']}")
                        total_qty += product['quantity']
            print(f"     📊 Общий остаток: {total_qty}")
            print()
        
        print("✅ Тест успешно завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stock_json_format()