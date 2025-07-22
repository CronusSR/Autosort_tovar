#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест JSON файлов без pandas
"""

import json
import os

def test_json_structure():
    """Тест структуры JSON файлов"""
    
    print("=== Тестирование структуры JSON файлов ===")
    
    # Проверяем файлы
    json_files = ['2025-06-30 (2).json', '2025-06-30 (3).json']
    
    for filename in json_files:
        if os.path.exists(filename):
            print(f"\n📄 Файл: {filename}")
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Проверяем тип данных
                print(f"✅ Тип данных: {type(data)}")
                
                if isinstance(data, list):
                    print(f"✅ Элементов в массиве: {len(data)}")
                    if data:
                        first_element = data[0]
                        print(f"✅ Первый элемент - филиал: {first_element.get('Филиал', 'не найден')}")
                        print(f"✅ Дата выгрузки: {first_element.get('ДатаВыгрузки', 'не найдена')}")
                        print(f"✅ Период: {first_element.get('НачалоПериода', 'не найден')} - {first_element.get('КонецПериода', 'не найден')}")
                        
                        # Проверяем продажи
                        sales = first_element.get('Продажи', [])
                        print(f"✅ Товаров в продажах: {len(sales)}")
                        
                        if sales:
                            print("✅ Первый товар:")
                            first_item = sales[0]
                            print(f"   - Номенклатура: {first_item.get('Номенклатура', 'не найдена')}")
                            print(f"   - Количество: {first_item.get('Количество', 'не найдено')}")
                            print(f"   - Выручка: {first_item.get('Выручка', 'не найдена')}")
                            print(f"   - Путь категорий: {first_item.get('ПутьКатегорий', 'не найден')}")
                            
                            # Считаем ADS для первого товара
                            if 'НачалоПериода' in first_element and 'КонецПериода' in first_element:
                                from datetime import datetime
                                start = datetime.strptime(first_element['НачалоПериода'], '%Y-%m-%d')
                                end = datetime.strptime(first_element['КонецПериода'], '%Y-%m-%d')
                                days = (end - start).days + 1
                                
                                revenue = first_item.get('Выручка', 0)
                                ads = revenue / days if days > 0 else 0
                                print(f"   - ADS (расчетный): {ads:.2f}")
                                print(f"   - Период дней: {days}")
                else:
                    # Одиночный объект
                    print(f"✅ Дата выгрузки: {data.get('ДатаВыгрузки', 'не найдена')}")
                    print(f"✅ Период: {data.get('НачалоПериода', 'не найден')} - {data.get('КонецПериода', 'не найден')}")
                    print(f"✅ Филиал: {data.get('Филиал', 'не найден')}")
                    
                    # Проверяем продажи
                    sales = data.get('Продажи', [])
                    print(f"✅ Товаров в продажах: {len(sales)}")
                    
                    if sales:
                        print("✅ Первый товар:")
                        first_item = sales[0]
                        print(f"   - Номенклатура: {first_item.get('Номенклатура', 'не найдена')}")
                        print(f"   - Количество: {first_item.get('Количество', 'не найдено')}")
                        print(f"   - Выручка: {first_item.get('Выручка', 'не найдена')}")
                        print(f"   - Путь категорий: {first_item.get('ПутьКатегорий', 'не найден')}")
                        
                        # Считаем ADS для первого товара
                        if 'НачалоПериода' in data and 'КонецПериода' in data:
                            from datetime import datetime
                            start = datetime.strptime(data['НачалоПериода'], '%Y-%m-%d')
                            end = datetime.strptime(data['КонецПериода'], '%Y-%m-%d')
                            days = (end - start).days + 1
                            
                            revenue = first_item.get('Выручка', 0)
                            ads = revenue / days if days > 0 else 0
                            print(f"   - ADS (расчетный): {ads:.2f}")
                            print(f"   - Период дней: {days}")
                
            except Exception as e:
                print(f"❌ Ошибка чтения файла {filename}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Файл {filename} не найден")

if __name__ == "__main__":
    test_json_structure()