#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование системы рекомендаций с JSON файлами
"""

from json_1c_parser import Json1CParser
import json
import pandas as pd

def test_json_parsing():
    """Тест парсинга JSON файлов"""
    
    parser = Json1CParser()
    
    # Тестируем файл продаж
    print("=== Тестирование парсинга файла продаж ===")
    
    try:
        with open('2025-06-30 (2).json', 'r', encoding='utf-8') as f:
            sales_data = json.load(f)
        
        # Парсим данные
        result = parser._parse_new_format(sales_data)
        
        print(f"✅ Формат: {result['metadata']['format']}")
        print(f"✅ Дата выгрузки: {result['metadata']['created_at']}")
        print(f"✅ Период: {result['metadata']['period']}")
        print(f"✅ Филиалы: {result['metadata']['branches']}")
        
        # Проверяем данные продаж
        total_products = 0
        for branch, products in result['sales_by_branch'].items():
            print(f"\n📍 Филиал: {branch}")
            print(f"   Товаров: {len(products)}")
            total_products += len(products)
            
            # Показываем топ-3 товара по ADS
            if products:
                df = pd.DataFrame(products)
                top_3 = df.nlargest(3, 'ads')[['product_name', 'ads', 'revenue']]
                print("   Топ-3 по ADS:")
                for _, row in top_3.iterrows():
                    print(f"   - {row['product_name'][:50]}... | ADS: {row['ads']:.2f} | Выручка: {row['revenue']:.0f}")
        
        print(f"\n✅ Всего товаров: {total_products}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    # Тестируем второй файл
    print("\n\n=== Тестирование второго файла продаж ===")
    
    try:
        with open('2025-06-30 (3).json', 'r', encoding='utf-8') as f:
            sales_data2 = json.load(f)
        
        result2 = parser._parse_new_format(sales_data2)
        
        print(f"✅ Филиал: {result2['metadata']['branches']}")
        print(f"✅ Товаров: {len(result2['sales_by_branch'][result2['metadata']['branches'][0]])}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестируем объединение данных из нескольких файлов
    print("\n\n=== Тестирование объединения данных ===")
    
    all_products = {}
    
    for result in [result, result2]:
        for branch_name, products in result['sales_by_branch'].items():
            for product in products:
                product_name = product['product_name']
                
                if product_name not in all_products:
                    all_products[product_name] = {
                        'total_ads': 0,
                        'branches': set(),
                        'revenue': 0
                    }
                
                all_products[product_name]['total_ads'] += product['ads']
                all_products[product_name]['branches'].add(branch_name)
                all_products[product_name]['revenue'] += product['revenue']
    
    print(f"✅ Уникальных товаров: {len(all_products)}")
    print(f"✅ Филиалов: {len(set().union(*[p['branches'] for p in all_products.values()]))}")
    
    # Топ-5 товаров по общему ADS
    ads_list = []
    for product_name, data in all_products.items():
        ads_list.append({
            'product_name': product_name,
            'ads': data['total_ads'],
            'branches': len(data['branches']),
            'revenue': data['revenue']
        })
    
    df = pd.DataFrame(ads_list)
    df = df.sort_values('ads', ascending=False)
    
    print("\n🔝 Топ-5 товаров по общему ADS:")
    for _, row in df.head(5).iterrows():
        print(f"- {row['product_name'][:50]}... | ADS: {row['ads']:.2f} | Филиалов: {row['branches']}")

if __name__ == "__main__":
    test_json_parsing()