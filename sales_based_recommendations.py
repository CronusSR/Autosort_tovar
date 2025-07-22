#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система рекомендаций на основе только данных продаж
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class SalesBasedRecommendations:
    """Система рекомендаций на основе данных продаж"""
    
    def __init__(self):
        self.sales_data = {}
        self.branch_hierarchy = self._get_branch_hierarchy()
        
    def _get_branch_hierarchy(self):
        """Иерархия филиалов и их характеристики"""
        return {
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Алматы',
                'supplier': 'Казыбаева Склад Фурнитура TRADE',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2
            },
            'Магазин фурнитуры': {
                'type': 'store',
                'level': 3,
                'city': 'Астана',
                'supplier': 'склад фурнитура № 1',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Шымкент',
                'supplier': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2
            },
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Алматы',
                'supplier': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3
            },
            'склад фурнитура № 1': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Астана',
                'supplier': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Шымкент',
                'supplier': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3
            },
            'База Склад Фурнитура Комплект': {
                'type': 'hub',
                'level': 1,
                'city': 'Алматы',
                'supplier': 'external',
                'min_days_stock': 45,
                'max_days_stock': 90,
                'safety_multiplier': 1.5
            }
        }
    
    def load_sales_data(self, json_file_path):
        """Загрузка данных продаж из JSON файла"""
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Обрабатываем данные
        all_products = {}
        processed_branches = set()
        
        for branch_data in data:
            branch_name = branch_data.get('Филиал')
            
            # Избегаем дублирования данных
            if branch_name in processed_branches:
                continue
            processed_branches.add(branch_name)
            
            # Рассчитываем период
            start_date = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
            end_date = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
            period_days = (end_date - start_date).days + 1
            
            # Обрабатываем продажи
            for product in branch_data.get('Продажи', []):
                product_name = product.get('Номенклатура')
                revenue = product.get('Выручка', 0)
                quantity = product.get('Количество', 0)
                ads = revenue / period_days if period_days > 0 else 0
                
                # Исключаем товары с нулевыми продажами
                if ads <= 0:
                    continue
                
                # Создаем запись для товара
                if product_name not in all_products:
                    all_products[product_name] = {
                        'branches': {},
                        'category_path': product.get('ПутьКатегорий', ''),
                        'unit': product.get('ЕдиницаИзмерения', 'шт'),
                        'article': product.get('Артикул', ''),
                        'manufacturer': product.get('Производитель', ''),
                        'total_ads': 0,
                        'total_revenue': 0,
                        'total_quantity': 0
                    }
                
                # Добавляем данные филиала
                all_products[product_name]['branches'][branch_name] = {
                    'ads': ads,
                    'revenue': revenue,
                    'quantity': quantity,
                    'margin': product.get('Рентабельность', 0),
                    'cost': product.get('Себестоимость', 0),
                    'profit': product.get('ВаловаяПрибыль', 0)
                }
                
                # Обновляем общие данные
                all_products[product_name]['total_ads'] += ads
                all_products[product_name]['total_revenue'] += revenue
                all_products[product_name]['total_quantity'] += quantity
        
        self.sales_data = all_products
        return len(all_products)
    
    def generate_stock_recommendations(self, branch_name):
        """Генерация рекомендаций по запасам для филиала"""
        
        if branch_name not in self.branch_hierarchy:
            return []
        
        branch_config = self.branch_hierarchy[branch_name]
        recommendations = []
        
        # Находим товары, которые продаются в этом филиале
        branch_products = []
        for product_name, product_data in self.sales_data.items():
            if branch_name in product_data['branches']:
                branch_products.append((product_name, product_data))
        
        # Сортируем по ADS
        branch_products.sort(key=lambda x: x[1]['branches'][branch_name]['ads'], reverse=True)
        
        for product_name, product_data in branch_products:
            branch_sales = product_data['branches'][branch_name]
            ads = branch_sales['ads']
            
            # Рассчитываем рекомендуемые запасы
            min_stock = ads * branch_config['min_days_stock'] * branch_config['safety_multiplier']
            max_stock = ads * branch_config['max_days_stock'] * branch_config['safety_multiplier']
            
            # Рассчитываем точку заказа
            reorder_point = ads * (branch_config['min_days_stock'] + 5)  # +5 дней на доставку
            
            # Определяем приоритет
            if ads >= 1000:  # Высокооборотные товары
                priority = 'high'
            elif ads >= 100:  # Среднеоборотные
                priority = 'medium'
            else:  # Низкооборотные
                priority = 'low'
            
            recommendations.append({
                'product_name': product_name,
                'ads': ads,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'reorder_point': reorder_point,
                'priority': priority,
                'unit': product_data['unit'],
                'category_path': product_data['category_path'],
                'revenue': branch_sales['revenue'],
                'margin': branch_sales['margin'],
                'supplier': branch_config['supplier']
            })
        
        return recommendations
    
    def generate_procurement_recommendations(self):
        """Генерация рекомендаций по закупкам для всех филиалов"""
        
        all_recommendations = {}
        
        for branch_name in self.branch_hierarchy.keys():
            recommendations = self.generate_stock_recommendations(branch_name)
            if recommendations:
                all_recommendations[branch_name] = recommendations
        
        return all_recommendations
    
    def generate_abc_analysis(self, branch_name):
        """ABC анализ товаров для филиала"""
        
        if branch_name not in self.branch_hierarchy:
            return {}
        
        # Получаем товары филиала
        branch_products = []
        for product_name, product_data in self.sales_data.items():
            if branch_name in product_data['branches']:
                branch_sales = product_data['branches'][branch_name]
                branch_products.append({
                    'product_name': product_name,
                    'revenue': branch_sales['revenue'],
                    'ads': branch_sales['ads'],
                    'quantity': branch_sales['quantity']
                })
        
        # Сортируем по выручке
        branch_products.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Рассчитываем накопленную выручку
        total_revenue = sum(p['revenue'] for p in branch_products)
        cumulative_revenue = 0
        
        abc_analysis = {'A': [], 'B': [], 'C': []}
        
        for product in branch_products:
            cumulative_revenue += product['revenue']
            cumulative_percent = (cumulative_revenue / total_revenue) * 100
            
            if cumulative_percent <= 80:
                abc_analysis['A'].append(product)
            elif cumulative_percent <= 95:
                abc_analysis['B'].append(product)
            else:
                abc_analysis['C'].append(product)
        
        return abc_analysis
    
    def print_recommendations_summary(self):
        """Печать сводки рекомендаций"""
        
        print("=== РЕКОМЕНДАЦИИ ПО ЗАКУПКАМ НА ОСНОВЕ ПРОДАЖ ===")
        
        # Общая статистика
        total_products = len(self.sales_data)
        total_ads = sum(p['total_ads'] for p in self.sales_data.values())
        total_revenue = sum(p['total_revenue'] for p in self.sales_data.values())
        
        print(f"📊 Общая статистика:")
        print(f"   Товаров: {total_products}")
        print(f"   Общий ADS: {total_ads:.2f}")
        print(f"   Общая выручка: {total_revenue:,.0f}")
        
        # Рекомендации по филиалам
        recommendations = self.generate_procurement_recommendations()
        
        for branch_name, branch_recs in recommendations.items():
            branch_config = self.branch_hierarchy[branch_name]
            print(f"\n🏢 {branch_name} ({branch_config['city']})")
            print(f"   Тип: {branch_config['type']} | Поставщик: {branch_config['supplier']}")
            print(f"   Товаров: {len(branch_recs)}")
            
            # Топ-5 товаров по приоритету
            high_priority = [r for r in branch_recs if r['priority'] == 'high']
            medium_priority = [r for r in branch_recs if r['priority'] == 'medium']
            low_priority = [r for r in branch_recs if r['priority'] == 'low']
            
            print(f"   Приоритет: Высокий: {len(high_priority)}, Средний: {len(medium_priority)}, Низкий: {len(low_priority)}")
            
            # Показываем топ-3 товара
            print(f"   Топ-3 товара по ADS:")
            for i, rec in enumerate(branch_recs[:3], 1):
                print(f"      {i}. {rec['product_name'][:50]}...")
                print(f"         ADS: {rec['ads']:.2f} | Мин. запас: {rec['min_stock']:.0f} {rec['unit']}")
                print(f"         Точка заказа: {rec['reorder_point']:.0f} | Приоритет: {rec['priority']}")
        
        # ABC анализ для основного филиала
        main_branch = next(iter(recommendations.keys()))
        abc_analysis = self.generate_abc_analysis(main_branch)
        
        print(f"\n📈 ABC анализ для {main_branch}:")
        print(f"   A категория (80% выручки): {len(abc_analysis['A'])} товаров")
        print(f"   B категория (15% выручки): {len(abc_analysis['B'])} товаров")
        print(f"   C категория (5% выручки): {len(abc_analysis['C'])} товаров")
        
        return recommendations

def main():
    """Основная функция"""
    
    # Создаем систему рекомендаций
    recommender = SalesBasedRecommendations()
    
    # Загружаем данные
    json_file = '2025-06-30 (3).json'
    if os.path.exists(json_file):
        products_count = recommender.load_sales_data(json_file)
        print(f"✅ Загружено {products_count} товаров")
        
        # Генерируем рекомендации
        recommendations = recommender.print_recommendations_summary()
        
        return recommendations
    else:
        print(f"❌ Файл {json_file} не найден")
        return None

if __name__ == "__main__":
    main()