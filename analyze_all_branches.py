#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ всех филиалов из JSON файла
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def analyze_all_branches():
    """Анализ всех филиалов из JSON файла"""
    
    print("=== АНАЛИЗ ВСЕХ ФИЛИАЛОВ ===")
    
    filename = '2025-06-30 (3).json'
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return
    
    try:
        # Читаем файл
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Файл загружен: {len(data)} элементов")
        
        # Анализируем уникальные филиалы
        branches_info = {}
        duplicate_count = 0
        
        for i, branch_data in enumerate(data):
            branch_name = branch_data.get('Филиал')
            
            if branch_name not in branches_info:
                # Первое вхождение филиала
                branches_info[branch_name] = {
                    'index': i,
                    'date_export': branch_data.get('ДатаВыгрузки'),
                    'period_start': branch_data.get('НачалоПериода'),
                    'period_end': branch_data.get('КонецПериода'),
                    'products_count': len(branch_data.get('Продажи', [])),
                    'total_revenue': 0,
                    'total_quantity': 0,
                    'duplicates': 0
                }
                
                # Рассчитываем общие показатели
                for product in branch_data.get('Продажи', []):
                    branches_info[branch_name]['total_revenue'] += product.get('Выручка', 0)
                    branches_info[branch_name]['total_quantity'] += product.get('Количество', 0)
            else:
                # Дубликат филиала
                branches_info[branch_name]['duplicates'] += 1
                duplicate_count += 1
        
        print(f"\n📊 Результат анализа:")
        print(f"✅ Уникальных филиалов: {len(branches_info)}")
        print(f"⚠️  Дубликатов: {duplicate_count}")
        
        # Детальная информация по каждому филиалу
        print(f"\n🏢 Детальная информация по филиалам:")
        
        for branch_name, info in branches_info.items():
            print(f"\n   📍 {branch_name}")
            print(f"      Дата выгрузки: {info['date_export']}")
            print(f"      Период: {info['period_start']} - {info['period_end']}")
            print(f"      Товаров: {info['products_count']:,}")
            print(f"      Выручка: {info['total_revenue']:,.0f}")
            print(f"      Количество: {info['total_quantity']:,.0f}")
            print(f"      Дубликатов: {info['duplicates']}")
            
            # Рассчитываем период в днях
            if info['period_start'] and info['period_end']:
                start = datetime.strptime(info['period_start'], '%Y-%m-%d')
                end = datetime.strptime(info['period_end'], '%Y-%m-%d')
                period_days = (end - start).days + 1
                ads = info['total_revenue'] / period_days if period_days > 0 else 0
                print(f"      Период дней: {period_days}")
                print(f"      ADS: {ads:.2f}")
        
        # Получаем данные без дубликатов
        unique_branches_data = {}
        processed_branches = set()
        
        for branch_data in data:
            branch_name = branch_data.get('Филиал')
            
            # Пропускаем дубликаты
            if branch_name in processed_branches:
                continue
            processed_branches.add(branch_name)
            
            # Сохраняем данные
            unique_branches_data[branch_name] = branch_data
        
        # Анализируем товары по всем филиалам
        print(f"\n📦 Анализ товаров по всем филиалам:")
        
        all_products = {}  # товар -> {филиал -> данные}
        
        for branch_name, branch_data in unique_branches_data.items():
            # Рассчитываем период
            start = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
            end = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
            period_days = (end - start).days + 1
            
            for product in branch_data.get('Продажи', []):
                product_name = product.get('Номенклатура')
                revenue = product.get('Выручка', 0)
                quantity = product.get('Количество', 0)
                ads = revenue / period_days if period_days > 0 else 0
                
                if product_name not in all_products:
                    all_products[product_name] = {}
                
                all_products[product_name][branch_name] = {
                    'revenue': revenue,
                    'quantity': quantity,
                    'ads': ads,
                    'unit': product.get('ЕдиницаИзмерения', 'шт'),
                    'margin': product.get('Рентабельность', 0),
                    'category_path': product.get('ПутьКатегорий', '')
                }
        
        print(f"✅ Всего уникальных товаров: {len(all_products):,}")
        
        # Найдем товары, которые продаются в нескольких филиалах
        multi_branch_products = {
            name: data for name, data in all_products.items() 
            if len(data) > 1
        }
        
        print(f"✅ Товаров в нескольких филиалах: {len(multi_branch_products):,}")
        
        # Топ товары по общему ADS
        print(f"\n🏆 Топ-10 товаров по общему ADS:")
        
        products_total_ads = []
        for product_name, branches in all_products.items():
            total_ads = sum(branch_data['ads'] for branch_data in branches.values())
            total_revenue = sum(branch_data['revenue'] for branch_data in branches.values())
            branches_count = len(branches)
            
            products_total_ads.append({
                'name': product_name,
                'total_ads': total_ads,
                'total_revenue': total_revenue,
                'branches_count': branches_count,
                'branches': list(branches.keys())
            })
        
        products_total_ads.sort(key=lambda x: x['total_ads'], reverse=True)
        
        for i, product in enumerate(products_total_ads[:10], 1):
            print(f"   {i}. {product['name'][:50]}...")
            print(f"      Общий ADS: {product['total_ads']:.2f}")
            print(f"      Выручка: {product['total_revenue']:,.0f}")
            print(f"      Филиалов: {product['branches_count']}")
            if product['branches_count'] > 1:
                print(f"      Продается в: {', '.join(product['branches'])}")
        
        # Анализ различий между филиалами
        print(f"\n🔍 Анализ различий между филиалами:")
        
        # Найдем товары с наибольшими различиями в ADS между филиалами
        products_with_variance = []
        
        for product_name, branches in multi_branch_products.items():
            ads_values = [branch_data['ads'] for branch_data in branches.values()]
            max_ads = max(ads_values)
            min_ads = min(ads_values)
            variance = max_ads - min_ads
            
            if variance > 100:  # Только значимые различия
                products_with_variance.append({
                    'name': product_name,
                    'variance': variance,
                    'max_ads': max_ads,
                    'min_ads': min_ads,
                    'branches': branches
                })
        
        products_with_variance.sort(key=lambda x: x['variance'], reverse=True)
        
        print(f"   Товаров с значительными различиями в ADS: {len(products_with_variance)}")
        
        if products_with_variance:
            print(f"   Топ-5 товаров с наибольшим разбросом ADS:")
            for i, product in enumerate(products_with_variance[:5], 1):
                print(f"      {i}. {product['name'][:50]}...")
                print(f"         Разброс ADS: {product['variance']:.2f}")
                print(f"         Мин ADS: {product['min_ads']:.2f}, Макс ADS: {product['max_ads']:.2f}")
                
                for branch_name, branch_data in product['branches'].items():
                    print(f"           - {branch_name}: {branch_data['ads']:.2f}")
        
        print(f"\n✅ Анализ завершен!")
        
        return {
            'unique_branches': len(branches_info),
            'duplicates': duplicate_count,
            'total_products': len(all_products),
            'multi_branch_products': len(multi_branch_products),
            'branches_data': unique_branches_data,
            'products_data': all_products
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_all_branches()