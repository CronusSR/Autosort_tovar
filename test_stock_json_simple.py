#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест нового JSON формата остатков без pandas
"""

import json
import os

def test_stock_json_simple():
    """Простой тест JSON остатков"""
    
    print("=== Тестирование структуры JSON остатков ===")
    
    filename = 'stock_example_2025-07-08.json'
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return
    
    try:
        # Читаем файл
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Файл {filename} успешно прочитан")
        
        # Проверяем корневую структуру
        print(f"✅ Дата остатков: {data.get('ДатаОстатков')}")
        print(f"✅ Дата выгрузки: {data.get('ДатаВыгрузки')}")
        print(f"✅ Организация: {data.get('Организация')}")
        
        warehouses = data.get('ОстаткиПоСкладам', [])
        print(f"✅ Складов: {len(warehouses)}")
        
        # Анализируем склады
        print(f"\n📋 Детальная информация по складам:")
        total_products = 0
        unique_products = set()
        
        for warehouse_data in warehouses:
            warehouse_name = warehouse_data.get('Склад', 'Неизвестный склад')
            city = warehouse_data.get('Город', '')
            warehouse_type = warehouse_data.get('ТипСклада', '')
            products = warehouse_data.get('Остатки', [])
            
            print(f"  🏢 {warehouse_name}")
            if city:
                print(f"     📍 Город: {city}")
            if warehouse_type:
                print(f"     🏷️  Тип: {warehouse_type}")
            print(f"     📦 Товаров: {len(products)}")
            
            total_products += len(products)
            
            # Показываем первые 3 товара
            for i, product in enumerate(products[:3]):
                product_name = product.get('Номенклатура', 'Неизвестный товар')
                quantity = product.get('Количество', 0)
                unit = product.get('ЕдиницаИзмерения', 'шт')
                price = product.get('СредняяЦена', 0)
                
                unique_products.add(product_name)
                
                print(f"     {i+1}. {product_name[:50]}...")
                print(f"        Остаток: {quantity} {unit}")
                if price > 0:
                    print(f"        Цена: {price}")
            
            if len(products) > 3:
                print(f"     ... и еще {len(products) - 3} товаров")
            print()
        
        # Общая статистика
        print(f"📊 Общая статистика:")
        print(f"✅ Всего товаров с остатками: {total_products}")
        print(f"✅ Уникальных товаров: {len(unique_products)}")
        print(f"✅ Средний остаток на склад: {total_products / len(warehouses):.1f}")
        
        # Проверим структуру одного товара
        if warehouses and warehouses[0].get('Остатки'):
            sample_product = warehouses[0]['Остатки'][0]
            print(f"\n🔍 Структура товара (пример):")
            for key, value in sample_product.items():
                print(f"  {key}: {value}")
        
        print("\n✅ Тест JSON структуры успешно завершен!")
        
        # Проверим совместимость с системой
        print(f"\n🔄 Тестирование совместимости с системой:")
        
        # Имитируем преобразование в формат системы
        stock_by_warehouse = {}
        
        for warehouse_data in warehouses:
            warehouse_name = warehouse_data.get('Склад')
            stock_by_warehouse[warehouse_name] = []
            
            for product in warehouse_data.get('Остатки', []):
                if product.get('Количество', 0) > 0:  # Только товары с остатками
                    stock_by_warehouse[warehouse_name].append({
                        'product_name': product.get('Номенклатура'),
                        'quantity': product.get('Количество', 0),
                        'amount': product.get('Сумма', 0),
                        'unit': product.get('ЕдиницаИзмерения', 'шт')
                    })
        
        print(f"✅ Формат системы создан успешно")
        print(f"✅ Складов в системе: {len(stock_by_warehouse)}")
        
        # Проверим первый склад
        first_warehouse = next(iter(stock_by_warehouse.values())) if stock_by_warehouse else []
        if first_warehouse:
            print(f"✅ Первый склад содержит {len(first_warehouse)} товаров")
            print(f"✅ Первый товар: {first_warehouse[0]['product_name'][:50]}...")
        
        print("✅ Тест совместимости завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stock_json_simple()