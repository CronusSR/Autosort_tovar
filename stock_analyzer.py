#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
АНАЛИЗАТОР ОСТАТКОВ С РЕКОМЕНДАЦИЯМИ ПО ЗАКУПКАМ И ПЕРЕМЕЩЕНИЯМ
Сравнение текущих остатков с нормативами на основе ADS
"""

import json
import os
from datetime import datetime
from collections import defaultdict
import math

class StockAnalyzer:
    """Анализатор остатков и рекомендаций"""
    
    def __init__(self):
        self.sales_data = {}
        self.stock_data = {}
        self.recommendations = {}
        self.branch_hierarchy = self._get_branch_hierarchy()
        
    def _get_branch_hierarchy(self):
        """Иерархия филиалов"""
        return {
            # 🏢 ГЛАВНЫЙ ХАБ
            'База Склад Фурнитура Комплект': {
                'type': 'hub', 'level': 1, 'city': 'Алматы',
                'min_days_stock': 45, 'max_days_stock': 90, 'safety_multiplier': 1.5,
                'supplier': None, 'delivery_days': 0
            },
            
            # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3,
                'supplier': 'База Склад Фурнитура Комплект', 'delivery_days': 1
            },
            'склад фурнитура № 1': {
                'type': 'warehouse', 'level': 2, 'city': 'Астана',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3,
                'supplier': 'База Склад Фурнитура Комплект', 'delivery_days': 2
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse', 'level': 2, 'city': 'Шымкент',
                'min_days_stock': 20, 'max_days_stock': 45, 'safety_multiplier': 1.3,
                'supplier': 'База Склад Фурнитура Комплект', 'delivery_days': 3
            },
            
            # 🏪 МАГАЗИНЫ ОТ ХАБА
            'Барыс Склад Фурнитура TRADE': {
                'type': 'store_direct', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 15, 'max_days_stock': 35, 'safety_multiplier': 1.2,
                'supplier': 'База Склад Фурнитура Комплект', 'delivery_days': 1
            },
            'АО Склад Фурнитура TRADE': {
                'type': 'store_direct', 'level': 2, 'city': 'Алматы',
                'min_days_stock': 15, 'max_days_stock': 35, 'safety_multiplier': 1.2,
                'supplier': 'База Склад Фурнитура Комплект', 'delivery_days': 1
            },
            
            # 🏪 МАГАЗИНЫ 3-ГО УРОВНЯ
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store', 'level': 3, 'city': 'Алматы',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2,
                'supplier': 'Казыбаева Склад Фурнитура TRADE', 'delivery_days': 1
            },
            'Магазин фурнитуры': {
                'type': 'store', 'level': 3, 'city': 'Астана',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2,
                'supplier': 'склад фурнитура № 1', 'delivery_days': 1
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store', 'level': 3, 'city': 'Шымкент',
                'min_days_stock': 10, 'max_days_stock': 25, 'safety_multiplier': 1.2,
                'supplier': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"', 'delivery_days': 1
            }
        }
    
    def load_sales_data(self, sales_file_path):
        """Загрузка данных продаж"""
        
        if not os.path.exists(sales_file_path):
            print(f"❌ Файл продаж {sales_file_path} не найден")
            return False
        
        print(f"📈 Загружаем данные продаж: {sales_file_path}")
        
        try:
            with open(sales_file_path, 'r', encoding='utf-8') as f:
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
                
                self.sales_data[branch_name] = {'products': {}}
                # Обрабатываем товары
                for product in branch_data.get('Продажи', []):
                    product_name = product.get('Номенклатура', '')
                    revenue = product.get('Выручка', 0)
                    quantity = product.get('Количество', 0)
                    
                    if revenue > 0:  # Только товары с продажами
                        ads = revenue / period_days if period_days > 0 else 0
                        
                        self.sales_data[branch_name]['products'][product_name] = {
                            'ads': ads,
                            'revenue': revenue,
                            'quantity': quantity,
                            'unit': product.get('ЕдиницаИзмерения', 'шт'),
                            'daily_quantity': quantity / period_days if period_days > 0 else 0
                        }
            
            print(f"✅ Загружено {len(self.sales_data)} филиалов с данными продаж")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки продаж: {e}")
            return False
    
    def load_stock_data(self, stock_file_path):
        """Загрузка данных остатков (JSON формат)"""
        
        if not os.path.exists(stock_file_path):
            print(f"❌ Файл остатков {stock_file_path} не найден")
            return False
        
        print(f"📦 Загружаем данные остатков: {stock_file_path}")
        
        try:
            with open(stock_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обрабатываем остатки по филиалам
            for branch_data in data:
                branch_name = branch_data.get('Филиал', branch_data.get('Склад'))
                
                if not branch_name:
                    continue
                
                self.stock_data[branch_name] = {'products': {}}
                # Обрабатываем товары в остатках
                products = branch_data.get('Остатки', branch_data.get('Товары', []))
                
                for product in products:
                    product_name = product.get('Номенклатура', product.get('Товар', ''))
                    quantity = product.get('Количество', product.get('Остаток', 0))
                    
                    if quantity > 0:  # Только товары с остатками
                        self.stock_data[branch_name]['products'][product_name] = {
                            'current_stock': quantity,
                            'unit': product.get('ЕдиницаИзмерения', product.get('Единица', 'шт')),
                            'cost': product.get('Себестоимость', 0),
                            'article': product.get('Артикул', ''),
                            'category': product.get('Категория', '')
                        }
            
            print(f"✅ Загружено {len(self.stock_data)} филиалов с данными остатков")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки остатков: {e}")
            return False
    
    def calculate_stock_norms_with_current(self, branch_name):
        """Расчет нормативов с учетом текущих остатков"""
        
        if branch_name not in self.sales_data:
            return None
        
        branch_config = self.branch_hierarchy.get(branch_name, {
            'type': 'store', 'min_days_stock': 10, 'max_days_stock': 25, 
            'safety_multiplier': 1.2, 'delivery_days': 1
        })
        
        sales_products = self.sales_data[branch_name]['products']
        stock_products = self.stock_data.get(branch_name, {}).get('products', {})
        
        analysis = {
            'branch_name': branch_name,
            'branch_config': branch_config,
            'products': {},
            'summary': {
                'total_products_sales': len(sales_products),
                'total_products_stock': len(stock_products),
                'products_with_both': 0,
                'products_need_purchase': 0,
                'products_excess': 0,
                'products_normal': 0
            }
        }
        
        # Анализируем товары с продажами
        for product_name, sales_data in sales_products.items():
            ads = sales_data['ads']
            current_stock = stock_products.get(product_name, {}).get('current_stock', 0)
            unit = sales_data['unit']
            
            # Рассчитываем нормативы
            min_stock = ads * branch_config['min_days_stock'] * branch_config['safety_multiplier']
            max_stock = ads * branch_config['max_days_stock'] * branch_config['safety_multiplier']
            optimal_stock = (min_stock + max_stock) / 2
            reorder_point = min_stock + (ads * branch_config['delivery_days'])
            
            # Определяем статус
            if current_stock < min_stock:
                if current_stock <= reorder_point:
                    status = 'urgent_purchase'  # Критический дефицит
                else:
                    status = 'need_purchase'    # Нужна закупка
                analysis['summary']['products_need_purchase'] += 1
            elif current_stock > max_stock:
                status = 'excess'               # Избыток
                analysis['summary']['products_excess'] += 1
            else:
                status = 'normal'               # Нормальный уровень
                analysis['summary']['products_normal'] += 1
            
            # Рассчитываем рекомендуемое количество для закупки/перемещения
            if status in ['urgent_purchase', 'need_purchase']:
                recommended_quantity = optimal_stock - current_stock
                days_stock_current = current_stock / ads if ads > 0 else 0
            elif status == 'excess':
                recommended_quantity = current_stock - optimal_stock
                days_stock_current = current_stock / ads if ads > 0 else 0
            else:
                recommended_quantity = 0
                days_stock_current = current_stock / ads if ads > 0 else 0
            
            # Определяем приоритет
            if ads >= 1000:
                priority = 'high'
                category = 'A'
            elif ads >= 100:
                priority = 'medium'
                category = 'B'
            else:
                priority = 'low'
                category = 'C'
            
            analysis['products'][product_name] = {
                'ads': ads,
                'current_stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'optimal_stock': optimal_stock,
                'reorder_point': reorder_point,
                'status': status,
                'recommended_quantity': abs(recommended_quantity),
                'days_stock_current': days_stock_current,
                'priority': priority,
                'category': category,
                'unit': unit,
                'revenue': sales_data['revenue'],
                'daily_quantity': sales_data['daily_quantity']
            }
            
            if current_stock > 0:
                analysis['summary']['products_with_both'] += 1
        
        return analysis
    
    def generate_purchase_recommendations(self, branch_name):
        """Генерация рекомендаций по закупкам"""
        
        analysis = self.calculate_stock_norms_with_current(branch_name)
        if not analysis:
            return None
        
        # Фильтруем товары, требующие закупки
        purchase_items = []
        urgent_items = []
        
        for product_name, data in analysis['products'].items():
            if data['status'] in ['urgent_purchase', 'need_purchase']:
                item = {
                    'product_name': product_name,
                    'ads': data['ads'],
                    'current_stock': data['current_stock'],
                    'recommended_quantity': data['recommended_quantity'],
                    'priority': data['priority'],
                    'category': data['category'],
                    'unit': data['unit'],
                    'days_stock_current': data['days_stock_current'],
                    'status': data['status']
                }
                
                if data['status'] == 'urgent_purchase':
                    urgent_items.append(item)
                else:
                    purchase_items.append(item)
        
        # Сортируем по приоритету (ADS)
        urgent_items.sort(key=lambda x: x['ads'], reverse=True)
        purchase_items.sort(key=lambda x: x['ads'], reverse=True)
        
        return {
            'branch_name': branch_name,
            'urgent_purchases': urgent_items,
            'regular_purchases': purchase_items,
            'total_urgent': len(urgent_items),
            'total_regular': len(purchase_items),
            'analysis_summary': analysis['summary']
        }
    
    def generate_movement_recommendations(self):
        """Генерация рекомендаций по перемещениям между филиалами"""
        
        # Собираем данные по всем филиалам
        all_analyses = {}
        for branch_name in self.sales_data.keys():
            analysis = self.calculate_stock_norms_with_current(branch_name)
            if analysis:
                all_analyses[branch_name] = analysis
        
        movement_opportunities = []
        
        # Ищем возможности перемещений
        for product_name in set().union(*[analysis['products'].keys() for analysis in all_analyses.values()]):
            
            # Собираем данные по товару во всех филиалах
            product_data = {}
            for branch_name, analysis in all_analyses.items():
                if product_name in analysis['products']:
                    product_data[branch_name] = analysis['products'][product_name]
            
            if len(product_data) < 2:  # Товар должен быть минимум в 2 филиалах
                continue
            
            # Ищем филиалы с избытком и дефицитом
            excess_branches = []
            deficit_branches = []
            
            for branch_name, data in product_data.items():
                if data['status'] == 'excess':
                    excess_branches.append({
                        'branch': branch_name,
                        'excess_quantity': data['recommended_quantity'],
                        'current_stock': data['current_stock'],
                        'ads': data['ads']
                    })
                elif data['status'] in ['urgent_purchase', 'need_purchase']:
                    deficit_branches.append({
                        'branch': branch_name,
                        'deficit_quantity': data['recommended_quantity'],
                        'current_stock': data['current_stock'],
                        'ads': data['ads'],
                        'urgency': data['status']
                    })
            
            # Генерируем рекомендации по перемещениям
            if excess_branches and deficit_branches:
                
                # Сортируем по приоритету
                excess_branches.sort(key=lambda x: x['excess_quantity'], reverse=True)
                deficit_branches.sort(key=lambda x: (x['urgency'] == 'urgent_purchase', x['ads']), reverse=True)
                
                for deficit in deficit_branches:
                    for excess in excess_branches:
                        if excess['excess_quantity'] > 0 and deficit['deficit_quantity'] > 0:
                            
                            # Рассчитываем оптимальное количество для перемещения
                            move_quantity = min(excess['excess_quantity'], deficit['deficit_quantity'])
                            
                            if move_quantity > 0:
                                movement_opportunities.append({
                                    'product_name': product_name,
                                    'from_branch': excess['branch'],
                                    'to_branch': deficit['branch'],
                                    'move_quantity': move_quantity,
                                    'from_excess': excess['excess_quantity'],
                                    'to_deficit': deficit['deficit_quantity'],
                                    'urgency': deficit['urgency'],
                                    'to_ads': deficit['ads'],
                                    'from_ads': excess['ads'],
                                    'priority_score': deficit['ads'] + (100000 if deficit['urgency'] == 'urgent_purchase' else 0)
                                })
                                
                                # Обновляем остатки после перемещения
                                excess['excess_quantity'] -= move_quantity
                                deficit['deficit_quantity'] -= move_quantity
        
        # Сортируем по приоритету
        movement_opportunities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return movement_opportunities
    
    def print_branch_stock_analysis(self, branch_name):
        """Детальный анализ остатков филиала"""
        
        analysis = self.calculate_stock_norms_with_current(branch_name)
        if not analysis:
            print(f"❌ Нет данных для анализа филиала {branch_name}")
            return
        
        branch_config = analysis['branch_config']
        summary = analysis['summary']
        
        print(f"\n{'='*80}")
        print(f"📦 АНАЛИЗ ОСТАТКОВ: {branch_name}")
        print(f"{'='*80}")
        
        # Основная информация
        print(f"\n📊 ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print(f"   Тип филиала: {branch_config['type']}")
        print(f"   Город: {branch_config['city']}")
        print(f"   Поставщик: {branch_config.get('supplier', 'внешний')}")
        print(f"   Время доставки: {branch_config['delivery_days']} дней")
        print(f"   Нормативы запасов: {branch_config['min_days_stock']}-{branch_config['max_days_stock']} дней")
        
        # Статистика
        print(f"\n📈 СТАТИСТИКА ОСТАТКОВ:")
        print(f"   Товаров с продажами: {summary['total_products_sales']}")
        print(f"   Товаров в остатках: {summary['total_products_stock']}")
        print(f"   Товаров с данными продаж и остатков: {summary['products_with_both']}")
        print(f"   Товаров требуют закупки: {summary['products_need_purchase']}")
        print(f"   Товаров с избытком: {summary['products_excess']}")
        print(f"   Товаров в норме: {summary['products_normal']}")
        
        # Рекомендации по закупкам
        purchase_recs = self.generate_purchase_recommendations(branch_name)
        if purchase_recs:
            print(f"\n🚨 СРОЧНЫЕ ЗАКУПКИ ({purchase_recs['total_urgent']} товаров):")
            for i, item in enumerate(purchase_recs['urgent_purchases'][:10], 1):
                print(f"   {i:2}. {item['product_name'][:50]}...")
                print(f"       Текущий остаток: {item['current_stock']:.0f} {item['unit']} ({item['days_stock_current']:.1f} дней)")
                print(f"       Рекомендуется докупить: {item['recommended_quantity']:.0f} {item['unit']}")
                print(f"       ADS: {item['ads']:.2f} | Категория: {item['category']}")
            
            if purchase_recs['total_regular'] > 0:
                print(f"\n📋 ПЛАНОВЫЕ ЗАКУПКИ ({purchase_recs['total_regular']} товаров):")
                for i, item in enumerate(purchase_recs['regular_purchases'][:5], 1):
                    print(f"   {i:2}. {item['product_name'][:50]}...")
                    print(f"       Текущий остаток: {item['current_stock']:.0f} {item['unit']} ({item['days_stock_current']:.1f} дней)")
                    print(f"       Рекомендуется докупить: {item['recommended_quantity']:.0f} {item['unit']}")
                    print(f"       ADS: {item['ads']:.2f} | Категория: {item['category']}")
        
        # Товары с избытком
        excess_products = [
            (name, data) for name, data in analysis['products'].items() 
            if data['status'] == 'excess'
        ]
        
        if excess_products:
            excess_products.sort(key=lambda x: x[1]['recommended_quantity'], reverse=True)
            print(f"\n📈 ТОВАРЫ С ИЗБЫТКОМ ({len(excess_products)} товаров):")
            for i, (product_name, data) in enumerate(excess_products[:5], 1):
                print(f"   {i:2}. {product_name[:50]}...")
                print(f"       Текущий остаток: {data['current_stock']:.0f} {data['unit']} ({data['days_stock_current']:.1f} дней)")
                print(f"       Избыток: {data['recommended_quantity']:.0f} {data['unit']}")
                print(f"       ADS: {data['ads']:.2f} | Категория: {data['category']}")
    
    def print_movement_recommendations(self):
        """Отчет по рекомендациям перемещений"""
        
        movements = self.generate_movement_recommendations()
        
        print(f"\n{'='*100}")
        print(f"🚚 РЕКОМЕНДАЦИИ ПО МЕЖФИЛИАЛЬНЫМ ПЕРЕМЕЩЕНИЯМ")
        print(f"{'='*100}")
        
        if not movements:
            print("ℹ️ Возможностей для перемещений не найдено")
            return
        
        print(f"✅ Найдено {len(movements)} возможностей для перемещений")
        
        # Группируем по срочности
        urgent_movements = [m for m in movements if m['urgency'] == 'urgent_purchase']
        regular_movements = [m for m in movements if m['urgency'] == 'need_purchase']
        
        if urgent_movements:
            print(f"\n🚨 СРОЧНЫЕ ПЕРЕМЕЩЕНИЯ ({len(urgent_movements)} товаров):")
            for i, move in enumerate(urgent_movements[:10], 1):
                print(f"   {i:2}. {move['product_name'][:50]}...")
                print(f"       {move['from_branch']} → {move['to_branch']}")
                print(f"       Количество: {move['move_quantity']:.0f}")
                print(f"       Получатель ADS: {move['to_ads']:.2f} | Отправитель ADS: {move['from_ads']:.2f}")
        
        if regular_movements:
            print(f"\n📋 ПЛАНОВЫЕ ПЕРЕМЕЩЕНИЯ ({len(regular_movements)} товаров):")
            for i, move in enumerate(regular_movements[:10], 1):
                print(f"   {i:2}. {move['product_name'][:50]}...")
                print(f"       {move['from_branch']} → {move['to_branch']}")
                print(f"       Количество: {move['move_quantity']:.0f}")
                print(f"       Получатель ADS: {move['to_ads']:.2f} | Отправитель ADS: {move['from_ads']:.2f}")
        
        return movements

def main():
    """Основная функция"""
    
    print("=" * 100)
    print("🏭 СИСТЕМА АНАЛИЗА ОСТАТКОВ И РЕКОМЕНДАЦИЙ")
    print("=" * 100)
    
    analyzer = StockAnalyzer()
    
    # Загружаем данные продаж
    if not analyzer.load_sales_data('2025-06-30.json'):
        return
    
    # Попытка загрузить остатки (если файл существует)
    stock_files = ['остатки.json', 'stock.json', 'остатки на 08.07.2025.xlsx']  # Возможные названия
    
    stock_loaded = False
    for stock_file in stock_files:
        if os.path.exists(stock_file):
            if stock_file.endswith('.json'):
                if analyzer.load_stock_data(stock_file):
                    stock_loaded = True
                    break
            else:
                print(f"⚠️ Файл {stock_file} найден, но поддерживается только JSON формат остатков")
    
    if not stock_loaded:
        print("⚠️ Файлы остатков не найдены. Создаем анализ только на основе продаж.")
        print("📝 Для полного анализа загрузите файл остатков в JSON формате.")
        
        # Показываем только нормативы без текущих остатков
        for branch_name in analyzer.sales_data.keys():
            print(f"\n📊 НОРМАТИВЫ ЗАПАСОВ: {branch_name}")
            branch_config = analyzer.branch_hierarchy.get(branch_name, {})
            sales_products = analyzer.sales_data[branch_name]['products']
            
            # Топ-5 товаров по ADS
            top_products = sorted(sales_products.items(), key=lambda x: x[1]['ads'], reverse=True)[:5]
            
            for i, (product_name, data) in enumerate(top_products, 1):
                ads = data['ads']
                min_stock = ads * branch_config.get('min_days_stock', 10) * branch_config.get('safety_multiplier', 1.2)
                max_stock = ads * branch_config.get('max_days_stock', 25) * branch_config.get('safety_multiplier', 1.2)
                
                print(f"   {i}. {product_name[:50]}...")
                print(f"      ADS: {ads:.2f} | Мин: {min_stock:.0f} | Макс: {max_stock:.0f} {data['unit']}")
        
        return
    
    # Анализ по каждому филиалу
    for branch_name in analyzer.sales_data.keys():
        analyzer.print_branch_stock_analysis(branch_name)
    
    # Рекомендации по перемещениям
    analyzer.print_movement_recommendations()
    
    print(f"\n{'='*100}")
    print(f"✅ АНАЛИЗ ЗАВЕРШЕН")
    print(f"{'='*100}")

if __name__ == "__main__":
    main()