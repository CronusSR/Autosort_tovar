#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДЕТАЛЬНЫЙ АНАЛИЗАТОР ПРОДАЖ ПО ФИЛИАЛАМ
Анализ продаж, ABC категоризация, оборачиваемость для каждого филиала отдельно
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import math

class DetailedSalesAnalyzer:
    """Детальный анализатор продаж по филиалам"""
    
    def __init__(self):
        self.sales_data = {}
        self.branch_hierarchy = self._get_branch_hierarchy()
        
    def _get_branch_hierarchy(self):
        """Иерархия филиалов"""
        return {
            # 🏢 ГЛАВНЫЙ ХАБ
            'База Склад Фурнитура Комплект': {
                'type': 'hub', 'level': 1, 'city': 'Алматы',
                'min_days_stock': 45, 'max_days_stock': 90, 'safety_multiplier': 1.5
            },
            
            # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3
            },
            'склад фурнитура № 1': {
                'type': 'warehouse', 'level': 2, 'city': 'Астана',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse', 'level': 2, 'city': 'Шымкент',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3
            },
            
            # 🏪 МАГАЗИНЫ ОТ ХАБА
            'Барыс Склад Фурнитура TRADE': {
                'type': 'store_direct', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 15, 'max_days_stock': 35, 'safety_multiplier': 1.2
            },
            'АО Склад Фурнитура TRADE': {
                'type': 'store_direct', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 15, 'max_days_stock': 35, 'safety_multiplier': 1.2
            },
            
            # 🏪 МАГАЗИНЫ 3-ГО УРОВНЯ
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store', 'level': 3, 'city': 'Алматы',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2
            },
            'Магазин фурнитуры': {
                'type': 'store', 'level': 3, 'city': 'Астана',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store', 'level': 3, 'city': 'Шымкент',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2
            }
        }
    
    def load_sales_file(self, file_path):
        """Загрузка файла продаж"""
        
        if not os.path.exists(file_path):
            print(f"❌ Файл {file_path} не найден")
            return False
        
        print(f"📁 Загружаем файл продаж: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обрабатываем каждый филиал
            for branch_data in data:
                branch_name = branch_data.get('Филиал')
                
                if not branch_name:
                    continue
                
                # Рассчитываем период
                start_date = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
                end_date = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
                period_days = (end_date - start_date).days + 1
                
                # Инициализируем данные филиала
                self.sales_data[branch_name] = {
                    'period_days': period_days,
                    'period_start': branch_data['НачалоПериода'],
                    'period_end': branch_data['КонецПериода'],
                    'export_date': branch_data.get('ДатаВыгрузки'),
                    'products': {},
                    'total_revenue': 0,
                    'total_quantity': 0,
                    'total_cost': 0,
                    'total_profit': 0
                }
                
                # Обрабатываем товары
                for product in branch_data.get('Продажи', []):
                    product_name = product.get('Номенклатура', '')
                    revenue = product.get('Выручка', 0)
                    quantity = product.get('Количество', 0)
                    cost = product.get('Себестоимость', 0)
                    profit = product.get('ВаловаяПрибыль', 0)
                    margin = product.get('Рентабельность', 0)
                    
                    if revenue > 0:  # Только товары с продажами
                        ads = revenue / period_days if period_days > 0 else 0
                        
                        self.sales_data[branch_name]['products'][product_name] = {
                            'revenue': revenue,
                            'quantity': quantity,
                            'cost': cost,
                            'profit': profit,
                            'margin': margin,
                            'ads': ads,
                            'unit': product.get('ЕдиницаИзмерения', 'шт'),
                            'category_path': product.get('ПутьКатегорий', ''),
                            'article': product.get('Артикул', ''),
                            'manufacturer': product.get('Производитель', ''),
                            # Рассчитываем дополнительные метрики
                            'avg_price': revenue / quantity if quantity > 0 else 0,
                            'daily_quantity': quantity / period_days if period_days > 0 else 0,
                            'profit_margin_percent': (profit / revenue * 100) if revenue > 0 else 0
                        }
                        
                        # Обновляем общие суммы филиала
                        self.sales_data[branch_name]['total_revenue'] += revenue
                        self.sales_data[branch_name]['total_quantity'] += quantity
                        self.sales_data[branch_name]['total_cost'] += cost
                        self.sales_data[branch_name]['total_profit'] += profit
            
            print(f"✅ Загружено {len(self.sales_data)} филиалов")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
            return False
    
    def calculate_abc_analysis(self, branch_name):
        """ABC анализ для филиала"""
        
        if branch_name not in self.sales_data:
            return None
        
        products = self.sales_data[branch_name]['products']
        
        # Сортируем товары по выручке
        sorted_products = sorted(products.items(), key=lambda x: x[1]['revenue'], reverse=True)
        
        total_revenue = sum(p[1]['revenue'] for p in sorted_products)
        cumulative_revenue = 0
        
        abc_results = {
            'A': {'products': [], 'revenue': 0, 'count': 0, 'percent_revenue': 0},
            'B': {'products': [], 'revenue': 0, 'count': 0, 'percent_revenue': 0},
            'C': {'products': [], 'revenue': 0, 'count': 0, 'percent_revenue': 0}
        }
        
        for product_name, data in sorted_products:
            cumulative_revenue += data['revenue']
            cumulative_percent = (cumulative_revenue / total_revenue) * 100
            
            # Определяем категорию
            if cumulative_percent <= 80:
                category = 'A'
            elif cumulative_percent <= 95:
                category = 'B'
            else:
                category = 'C'
            
            # Добавляем товар в категорию
            product_with_category = data.copy()
            product_with_category['name'] = product_name
            product_with_category['category'] = category
            product_with_category['cumulative_percent'] = cumulative_percent
            
            abc_results[category]['products'].append(product_with_category)
            abc_results[category]['revenue'] += data['revenue']
            abc_results[category]['count'] += 1
        
        # Рассчитываем проценты
        for category in abc_results:
            abc_results[category]['percent_revenue'] = (abc_results[category]['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
        
        return abc_results
    
    def calculate_turnover_analysis(self, branch_name):
        """Анализ оборачиваемости для филиала"""
        
        if branch_name not in self.sales_data:
            return None
        
        branch_data = self.sales_data[branch_name]
        products = branch_data['products']
        period_days = branch_data['period_days']
        
        turnover_analysis = {
            'high_turnover': [],  # Высокая оборачиваемость (> 1000 тенге/день)
            'medium_turnover': [], # Средняя оборачиваемость (100-1000 тенге/день)
            'low_turnover': [],   # Низкая оборачиваемость (< 100 тенге/день)
            'total_products': len(products),
            'avg_ads': sum(p['ads'] for p in products.values()) / len(products) if products else 0
        }
        
        for product_name, data in products.items():
            ads = data['ads']
            
            turnover_data = {
                'name': product_name,
                'ads': ads,
                'revenue': data['revenue'],
                'quantity': data['quantity'],
                'daily_quantity': data['daily_quantity'],
                'unit': data['unit'],
                'margin': data['margin'],
                'avg_price': data['avg_price'],
                'category_path': data['category_path']
            }
            
            if ads >= 1000:
                turnover_analysis['high_turnover'].append(turnover_data)
            elif ads >= 100:
                turnover_analysis['medium_turnover'].append(turnover_data)
            else:
                turnover_analysis['low_turnover'].append(turnover_data)
        
        # Сортируем по ADS
        for category in ['high_turnover', 'medium_turnover', 'low_turnover']:
            turnover_analysis[category].sort(key=lambda x: x['ads'], reverse=True)
        
        return turnover_analysis
    
    def calculate_stock_norms(self, branch_name):
        """Расчет нормативов запасов для филиала"""
        
        if branch_name not in self.sales_data:
            return None
        
        branch_config = self.branch_hierarchy.get(branch_name, {
            'type': 'store', 'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2
        })
        
        products = self.sales_data[branch_name]['products']
        stock_norms = {}
        
        for product_name, data in products.items():
            ads = data['ads']
            
            # Рассчитываем нормативы
            min_stock = ads * branch_config['min_days_stock'] * branch_config['safety_multiplier']
            max_stock = ads * branch_config['max_days_stock'] * branch_config['safety_multiplier']
            optimal_stock = (min_stock + max_stock) / 2
            reorder_point = min_stock + (ads * 5)  # +5 дней на доставку
            
            # Определяем приоритет по ADS
            if ads >= 1000:
                priority = 'high'
                category = 'A'
            elif ads >= 100:
                priority = 'medium'
                category = 'B'
            else:
                priority = 'low'
                category = 'C'
            
            stock_norms[product_name] = {
                'ads': ads,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'optimal_stock': optimal_stock,
                'reorder_point': reorder_point,
                'priority': priority,
                'category': category,
                'unit': data['unit'],
                'revenue': data['revenue'],
                'margin': data['margin'],
                'branch_type': branch_config['type']
            }
        
        return stock_norms
    
    def print_branch_analysis(self, branch_name):
        """Детальный анализ филиала"""
        
        if branch_name not in self.sales_data:
            print(f"❌ Филиал {branch_name} не найден в данных")
            return
        
        branch_data = self.sales_data[branch_name]
        branch_config = self.branch_hierarchy.get(branch_name, {})
        
        print(f"\n{'='*80}")
        print(f"🏢 ДЕТАЛЬНЫЙ АНАЛИЗ ФИЛИАЛА: {branch_name}")
        print(f"{'='*80}")
        
        # Основная информация
        print(f"\n📊 ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print(f"   Тип филиала: {branch_config.get('type', 'неизвестен')}")
        print(f"   Город: {branch_config.get('city', 'неизвестен')}")
        print(f"   Период анализа: {branch_data['period_start']} - {branch_data['period_end']} ({branch_data['period_days']} дней)")
        print(f"   Дата выгрузки: {branch_data['export_date']}")
        
        # Финансовые показатели
        total_revenue = branch_data['total_revenue']
        total_cost = branch_data['total_cost']
        total_profit = branch_data['total_profit']
        avg_ads = total_revenue / branch_data['period_days']
        
        print(f"\n💰 ФИНАНСОВЫЕ ПОКАЗАТЕЛИ:")
        print(f"   Общая выручка: {total_revenue:,.0f} тенге")
        print(f"   Общая себестоимость: {total_cost:,.0f} тенге")
        print(f"   Валовая прибыль: {total_profit:,.0f} тенге")
        print(f"   Рентабельность: {(total_profit/total_revenue*100):.2f}%")
        print(f"   Средний ADS: {avg_ads:.2f} тенге/день")
        print(f"   Товаров с продажами: {len(branch_data['products']):,}")
        
        # ABC анализ
        abc_analysis = self.calculate_abc_analysis(branch_name)
        if abc_analysis:
            print(f"\n🎯 ABC АНАЛИЗ:")
            for category in ['A', 'B', 'C']:
                data = abc_analysis[category]
                print(f"   Категория {category}: {data['count']} товаров ({data['percent_revenue']:.1f}% выручки)")
            
            # Топ товары категории A
            if abc_analysis['A']['products']:
                print(f"\n   🔥 ТОП-10 ТОВАРОВ КАТЕГОРИИ A:")
                for i, product in enumerate(abc_analysis['A']['products'][:10], 1):
                    print(f"      {i:2}. {product['name'][:50]}...")
                    print(f"          ADS: {product['ads']:.2f} | Выручка: {product['revenue']:,.0f} | Рентабельность: {product['margin']:.1f}%")
        
        # Анализ оборачиваемости
        turnover_analysis = self.calculate_turnover_analysis(branch_name)
        if turnover_analysis:
            print(f"\n⚡ АНАЛИЗ ОБОРАЧИВАЕМОСТИ:")
            print(f"   Высокая оборачиваемость (>1000 тенге/день): {len(turnover_analysis['high_turnover'])} товаров")
            print(f"   Средняя оборачиваемость (100-1000 тенге/день): {len(turnover_analysis['medium_turnover'])} товаров")
            print(f"   Низкая оборачиваемость (<100 тенге/день): {len(turnover_analysis['low_turnover'])} товаров")
            print(f"   Средний ADS по филиалу: {turnover_analysis['avg_ads']:.2f} тенге/день")
            
            # Топ высокооборотных товаров
            if turnover_analysis['high_turnover']:
                print(f"\n   🚀 ТОП-5 ВЫСОКООБОРОТНЫХ ТОВАРОВ:")
                for i, product in enumerate(turnover_analysis['high_turnover'][:5], 1):
                    print(f"      {i}. {product['name'][:50]}...")
                    print(f"         ADS: {product['ads']:.2f} | Дневное кол-во: {product['daily_quantity']:.2f} {product['unit']}")
        
        # Нормативы запасов
        stock_norms = self.calculate_stock_norms(branch_name)
        if stock_norms:
            print(f"\n📦 НОРМАТИВЫ ЗАПАСОВ:")
            print(f"   Тип филиала: {branch_config.get('type', 'неизвестен')}")
            print(f"   Нормативы: {branch_config.get('min_days_stock', 0)}-{branch_config.get('max_days_stock', 0)} дней")
            print(f"   Коэффициент безопасности: {branch_config.get('safety_multiplier', 1.0)}")
            
            # Статистика по приоритетам
            high_priority = sum(1 for p in stock_norms.values() if p['priority'] == 'high')
            medium_priority = sum(1 for p in stock_norms.values() if p['priority'] == 'medium')
            low_priority = sum(1 for p in stock_norms.values() if p['priority'] == 'low')
            
            print(f"   Высокий приоритет: {high_priority} товаров")
            print(f"   Средний приоритет: {medium_priority} товаров")
            print(f"   Низкий приоритет: {low_priority} товаров")
            
            # Топ товары по нормативам
            sorted_norms = sorted(stock_norms.items(), key=lambda x: x[1]['ads'], reverse=True)
            print(f"\n   📋 ТОП-5 ТОВАРОВ ПО НОРМАТИВАМ ЗАПАСОВ:")
            for i, (product_name, norms) in enumerate(sorted_norms[:5], 1):
                print(f"      {i}. {product_name[:50]}...")
                print(f"         ADS: {norms['ads']:.2f} | Мин: {norms['min_stock']:.0f} | Макс: {norms['max_stock']:.0f} {norms['unit']}")
                print(f"         Оптимальный запас: {norms['optimal_stock']:.0f} {norms['unit']} | Точка заказа: {norms['reorder_point']:.0f} {norms['unit']}")
    
    def print_all_branches_summary(self):
        """Сводка по всем филиалам"""
        
        print(f"\n{'='*100}")
        print(f"📈 СВОДКА ПО ВСЕМ ФИЛИАЛАМ")
        print(f"{'='*100}")
        
        total_revenue = 0
        total_products = 0
        
        for branch_name, branch_data in self.sales_data.items():
            branch_config = self.branch_hierarchy.get(branch_name, {})
            revenue = branch_data['total_revenue']
            products_count = len(branch_data['products'])
            ads = revenue / branch_data['period_days']
            
            total_revenue += revenue
            total_products += products_count
            
            print(f"\n🏢 {branch_name}")
            print(f"   Тип: {branch_config.get('type', 'неизвестен'):15} | Город: {branch_config.get('city', 'неизвестен'):10}")
            print(f"   Товаров: {products_count:4} | Выручка: {revenue:>12,.0f} | ADS: {ads:>10,.2f}")
        
        print(f"\n📊 ОБЩИЕ ИТОГИ:")
        print(f"   Всего филиалов: {len(self.sales_data)}")
        print(f"   Общая выручка: {total_revenue:,.0f} тенге")
        print(f"   Всего товаров: {total_products:,}")
        print(f"   Средняя выручка на филиал: {total_revenue/len(self.sales_data):,.0f} тенге")

def main():
    """Основная функция"""
    
    analyzer = DetailedSalesAnalyzer()
    
    # Загружаем файл продаж
    if analyzer.load_sales_file('2025-06-30.json'):
        
        # Общая сводка
        analyzer.print_all_branches_summary()
        
        # Детальный анализ каждого филиала
        for branch_name in analyzer.sales_data.keys():
            analyzer.print_branch_analysis(branch_name)
        
        print(f"\n{'='*100}")
        print(f"✅ АНАЛИЗ ЗАВЕРШЕН")
        print(f"{'='*100}")
    
    else:
        print("❌ Не удалось загрузить данные продаж")

if __name__ == "__main__":
    main()