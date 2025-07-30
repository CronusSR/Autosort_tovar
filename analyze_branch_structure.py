#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры файлов продаж и остатков для понимания информации о филиалах
"""

import json
import os
from pprint import pprint

def analyze_sales_file(filepath):
    """Анализ структуры файла продаж"""
    print(f"\n=== АНАЛИЗ ФАЙЛА ПРОДАЖ: {filepath} ===")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Тип данных: {type(data)}")
        
        if isinstance(data, list):
            print(f"Количество элементов: {len(data)}")
            
            # Анализируем структуру каждого филиала
            branches = {}
            for item in data:
                if 'Филиал' in item:
                    branch = item['Филиал']
                    if branch not in branches:
                        branches[branch] = {
                            'structure': {},
                            'sample_data': {}
                        }
                    
                    # Сохраняем структуру филиала
                    for key in item.keys():
                        branches[branch]['structure'][key] = type(item[key]).__name__
                    
                    # Сохраняем образец данных (только ключи верхнего уровня)
                    branches[branch]['sample_data'] = {k: v for k, v in item.items() if k != 'Продажи' and k != 'ПродажиПоДням'}
                    
                    # Анализируем структуру продаж
                    if 'Продажи' in item and item['Продажи']:
                        first_sale_day = item['Продажи'][0]
                        if 'ПродажиПоДням' in first_sale_day and first_sale_day['ПродажиПоДням']:
                            first_product = first_sale_day['ПродажиПоДням'][0]
                            branches[branch]['product_structure'] = list(first_product.keys())
                    
                    if 'ПродажиПоДням' in item:
                        # Новая структура
                        for day, products in item['ПродажиПоДням'].items():
                            if products:
                                branches[branch]['product_structure'] = list(products[0].keys())
                                break
            
            print(f"\nНайдено филиалов: {len(branches)}")
            for branch_name, branch_info in branches.items():
                print(f"\n--- ФИЛИАЛ: {branch_name} ---")
                print("Структура филиала:")
                pprint(branch_info['structure'])
                print("\nОбразец данных филиала:")
                pprint(branch_info['sample_data'])
                if 'product_structure' in branch_info:
                    print(f"\nСтруктура товара: {branch_info['product_structure']}")
                
    except Exception as e:
        print(f"Ошибка при анализе файла продаж: {e}")

def analyze_stock_file(filepath):
    """Анализ структуры файла остатков"""
    print(f"\n=== АНАЛИЗ ФАЙЛА ОСТАТКОВ: {filepath} ===")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Тип данных: {type(data)}")
        print("Ключи верхнего уровня:", list(data.keys()))
        
        if 'ОстаткиПоСкладам' in data:
            warehouses = data['ОстаткиПоСкладам']
            print(f"Количество складов: {len(warehouses)}")
            
            branches = {}
            for warehouse in warehouses:
                branch_name = warehouse.get('Склад', 'Неизвестный склад')
                branches[branch_name] = {
                    'structure': {k: type(v).__name__ for k, v in warehouse.items() if k != 'Остатки'},
                    'sample_data': {k: v for k, v in warehouse.items() if k != 'Остатки'},
                    'product_count': len(warehouse.get('Остатки', []))
                }
                
                # Анализируем структуру товара
                if 'Остатки' in warehouse and warehouse['Остатки']:
                    first_product = warehouse['Остатки'][0]
                    branches[branch_name]['product_structure'] = list(first_product.keys())
            
            print(f"\nНайдено складов: {len(branches)}")
            for branch_name, branch_info in branches.items():
                print(f"\n--- СКЛАД: {branch_name} ---")
                print("Структура склада:")
                pprint(branch_info['structure'])
                print("\nОбразец данных склада:")
                pprint(branch_info['sample_data'])
                print(f"Количество товаров: {branch_info['product_count']}")
                if 'product_structure' in branch_info:
                    print(f"Структура товара: {branch_info['product_structure']}")
                
    except Exception as e:
        print(f"Ошибка при анализе файла остатков: {e}")

def main():
    """Основная функция"""
    base_path = "/mnt/f/Работа-Никита/Autosort_tovar"
    
    # Анализируем файлы продаж
    sales_files = [
        "2024-01-31.json",
        "test_webhook_uploads/2024-01-31.json",
        "webhook_uploads/sales_2025-01-01_2025-01-15.json"
    ]
    
    for sales_file in sales_files:
        filepath = os.path.join(base_path, sales_file)
        if os.path.exists(filepath):
            analyze_sales_file(filepath)
        else:
            print(f"Файл не найден: {filepath}")
    
    # Анализируем файлы остатков
    stock_files = [
        "остатки-2025-06-30 (4).json",
        "webhook_uploads/stock_2025-01-15.json"
    ]
    
    for stock_file in stock_files:
        filepath = os.path.join(base_path, stock_file)
        if os.path.exists(filepath):
            analyze_stock_file(filepath)
        else:
            print(f"Файл не найден: {filepath}")

if __name__ == "__main__":
    main()