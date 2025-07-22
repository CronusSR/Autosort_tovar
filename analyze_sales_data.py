#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ данных продаж из 2025-06-30 (3).json для системы рекомендаций
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def analyze_sales_data():
    """Детальный анализ данных продаж"""
    
    print("=== Анализ данных продаж для рекомендаций ===")
    
    filename = '2025-06-30 (3).json'
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return
    
    try:
        # Читаем файл
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Файл {filename} загружен")
        print(f"✅ Тип данных: {type(data)}")
        print(f"✅ Количество филиалов: {len(data)}")
        
        # Анализируем каждый филиал
        all_branches = {}
        all_products = {}
        period_days = 30  # По умолчанию
        
        for branch_data in data:
            branch_name = branch_data.get('Филиал')
            sales = branch_data.get('Продажи', [])
            
            print(f"\n🏢 Филиал: {branch_name}")
            print(f"   📅 Период: {branch_data.get('НачалоПериода')} - {branch_data.get('КонецПериода')}")
            print(f"   📦 Товаров: {len(sales)}")
            
            # Рассчитываем период
            if 'НачалоПериода' in branch_data and 'КонецПериода' in branch_data:
                start = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
                end = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
                period_days = (end - start).days + 1
                print(f"   📊 Период дней: {period_days}")
            
            # Анализируем продажи
            branch_stats = {
                'total_revenue': 0,
                'total_quantity': 0,
                'product_count': len(sales),
                'top_products': []
            }
            
            for product in sales:
                product_name = product.get('Номенклатура')
                revenue = product.get('Выручка', 0)
                quantity = product.get('Количество', 0)
                ads = revenue / period_days if period_days > 0 else 0
                
                branch_stats['total_revenue'] += revenue
                branch_stats['total_quantity'] += quantity
                
                # Сохраняем данные по товарам
                if product_name not in all_products:
                    all_products[product_name] = {
                        'branches': {},
                        'total_ads': 0,
                        'total_revenue': 0,
                        'total_quantity': 0,
                        'category_path': product.get('ПутьКатегорий', ''),
                        'unit': product.get('ЕдиницаИзмерения', 'шт')
                    }
                
                all_products[product_name]['branches'][branch_name] = {
                    'revenue': revenue,
                    'quantity': quantity,
                    'ads': ads,
                    'margin': product.get('Рентабельность', 0)
                }
                
                all_products[product_name]['total_ads'] += ads
                all_products[product_name]['total_revenue'] += revenue
                all_products[product_name]['total_quantity'] += quantity
                
                # Добавляем в топ товары филиала
                branch_stats['top_products'].append({
                    'name': product_name,
                    'revenue': revenue,
                    'ads': ads,
                    'quantity': quantity
                })
            
            # Сортируем топ товары по ADS
            branch_stats['top_products'].sort(key=lambda x: x['ads'], reverse=True)
            
            all_branches[branch_name] = branch_stats
            
            # Показываем статистику филиала
            print(f"   💰 Общая выручка: {branch_stats['total_revenue']:,.0f}")
            print(f"   📈 Средний ADS: {branch_stats['total_revenue'] / period_days:.2f}")
            
            # Топ-3 товара по ADS
            print(f"   🔝 Топ-3 товара по ADS:")
            for i, product in enumerate(branch_stats['top_products'][:3], 1):
                print(f"      {i}. {product['name'][:40]}... | ADS: {product['ads']:.2f}")
        
        # Общая аналитика
        print(f"\n📊 Общая аналитика:")
        print(f"✅ Всего филиалов: {len(all_branches)}")
        print(f"✅ Всего уникальных товаров: {len(all_products)}")
        
        total_revenue = sum(branch['total_revenue'] for branch in all_branches.values())
        print(f"✅ Общая выручка: {total_revenue:,.0f}")
        print(f"✅ Общий ADS: {total_revenue / period_days:.2f}")
        
        # Топ товары общие
        sorted_products = sorted(all_products.items(), key=lambda x: x[1]['total_ads'], reverse=True)
        print(f"\n🏆 Топ-10 товаров по общему ADS:")
        for i, (product_name, data) in enumerate(sorted_products[:10], 1):
            branches_count = len(data['branches'])
            print(f"   {i}. {product_name[:50]}...")
            print(f"      ADS: {data['total_ads']:.2f} | Филиалов: {branches_count} | Выручка: {data['total_revenue']:,.0f}")
        
        # Анализ по филиалам - кто что продает лучше
        print(f"\n🎯 Анализ специализации филиалов:")
        for branch_name, branch_stats in all_branches.items():
            print(f"   🏢 {branch_name}:")
            print(f"      💰 Доля от общей выручки: {branch_stats['total_revenue'] / total_revenue * 100:.1f}%")
            print(f"      📊 Средний ADS: {branch_stats['total_revenue'] / period_days:.2f}")
            
            # Лучший товар филиала
            if branch_stats['top_products']:
                best_product = branch_stats['top_products'][0]
                print(f"      🥇 Лучший товар: {best_product['name'][:40]}... (ADS: {best_product['ads']:.2f})")
        
        # Анализ потенциала для перемещений
        print(f"\n🚚 Потенциал для перемещений:")
        
        # Находим товары, которые продаются в нескольких филиалах
        multi_branch_products = [(name, data) for name, data in all_products.items() 
                               if len(data['branches']) > 1]
        
        print(f"✅ Товаров, продающихся в нескольких филиалах: {len(multi_branch_products)}")
        
        # Показываем товары с наибольшим разбросом ADS между филиалами
        products_with_variance = []
        for product_name, data in multi_branch_products:
            ads_values = [branch_data['ads'] for branch_data in data['branches'].values()]
            if len(ads_values) > 1:
                max_ads = max(ads_values)
                min_ads = min(ads_values)
                variance = max_ads - min_ads
                products_with_variance.append((product_name, variance, max_ads, min_ads, data))
        
        products_with_variance.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n📈 Товары с наибольшим разбросом ADS между филиалами:")
        for i, (product_name, variance, max_ads, min_ads, data) in enumerate(products_with_variance[:5], 1):
            print(f"   {i}. {product_name[:50]}...")
            print(f"      Разброс ADS: {variance:.2f} (мин: {min_ads:.2f}, макс: {max_ads:.2f})")
            
            # Показываем какие филиалы продают этот товар
            print(f"      Филиалы:")
            for branch_name, branch_data in data['branches'].items():
                print(f"         - {branch_name}: ADS {branch_data['ads']:.2f}")
        
        print(f"\n✅ Анализ завершен!")
        
        return {
            'branches': all_branches,
            'products': all_products,
            'period_days': period_days,
            'total_revenue': total_revenue
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_sales_data()