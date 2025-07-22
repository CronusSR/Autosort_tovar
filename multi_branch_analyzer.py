#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система анализа всех филиалов с расчетом мин/макс остатков
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class MultiBranchAnalyzer:
    """Анализатор всех филиалов с расчетом нормативов остатков"""
    
    def __init__(self):
        self.branches_data = {}
        self.products_data = {}
        self.branch_hierarchy = self._get_branch_hierarchy()
        
    def _get_branch_hierarchy(self):
        """Правильная иерархия филиалов согласно структуре сети"""
        return {
            # 🏢 ГЛАВНЫЙ ХАБ
            'База Склад Фурнитура Комплект': {
                'type': 'hub',
                'level': 1,
                'city': 'Алматы',
                'parent': None,
                'min_days_stock': 45,
                'max_days_stock': 90,
                'safety_multiplier': 1.5,
                'exclude_categories': False
            },
            
            # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба)
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'exclude_categories': False
            },
            'склад фурнитура № 1': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Астана',
                'parent': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'exclude_categories': False
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Шымкент',
                'parent': 'База Склад Фурнитура Комплект',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'exclude_categories': True  # Особенность Шымкента
            },
            
            # 🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов)
            'Барыс Склад Фурнитура TRADE': {
                'type': 'store_direct',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'min_days_stock': 15,
                'max_days_stock': 35,
                'safety_multiplier': 1.2,
                'exclude_categories': False
            },
            'АО Склад Фурнитура TRADE': {  # Алтын Орда
                'type': 'store_direct',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'min_days_stock': 15,
                'max_days_stock': 35,
                'safety_multiplier': 1.2,
                'exclude_categories': True  # Особенность АО
            },
            
            # 🏪 МАГАЗИНЫ 3-ГО УРОВНЯ (питаются от складов 2-го уровня)
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Алматы',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'exclude_categories': False
            },
            'Магазин фурнитуры': {
                'type': 'store',
                'level': 3,
                'city': 'Астана',
                'parent': 'склад фурнитура № 1',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'exclude_categories': False
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Шымкент',
                'parent': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'exclude_categories': False
            }
        }
    
    def load_multiple_json_files(self, file_paths):
        """Загрузка данных из нескольких JSON файлов"""
        
        processed_branches = set()
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"⚠️ Файл {file_path} не найден")
                continue
            
            print(f"📁 Обрабатываем файл: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Преобразуем данные в единый формат (массив)
            if isinstance(data, dict):
                # Файл содержит один объект - преобразуем в массив
                data = [data]
            elif not isinstance(data, list):
                print(f"   ❌ Неизвестная структура данных в файле {file_path}")
                continue
            
            # Обрабатываем данные (избегаем дубликатов)
            file_branches = set()
            
            for branch_data in data:
                branch_name = branch_data.get('Филиал')
                
                # Проверяем дубликаты в текущем файле
                if branch_name in file_branches:
                    continue
                file_branches.add(branch_name)
                
                # Проверяем глобальные дубликаты
                if branch_name in processed_branches:
                    print(f"   ⚠️ Филиал {branch_name} уже обработан, пропускаем")
                    continue
                processed_branches.add(branch_name)
                
                # Рассчитываем период
                start_date = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
                end_date = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
                period_days = (end_date - start_date).days + 1
                
                # Сохраняем данные филиала
                self.branches_data[branch_name] = {
                    'period_days': period_days,
                    'period_start': branch_data['НачалоПериода'],
                    'period_end': branch_data['КонецПериода'],
                    'export_date': branch_data.get('ДатаВыгрузки'),
                    'products': {},
                    'total_revenue': 0,
                    'total_quantity': 0,
                    'products_count': 0
                }
                
                # Обрабатываем товары
                for product in branch_data.get('Продажи', []):
                    product_name = product.get('Номенклатура')
                    revenue = product.get('Выручка', 0)
                    quantity = product.get('Количество', 0)
                    ads = revenue / period_days if period_days > 0 else 0
                    
                    if ads > 0:  # Только товары с продажами
                        # Сохраняем данные товара в филиале
                        self.branches_data[branch_name]['products'][product_name] = {
                            'ads': ads,
                            'revenue': revenue,
                            'quantity': quantity,
                            'unit': product.get('ЕдиницаИзмерения', 'шт'),
                            'category_path': product.get('ПутьКатегорий', ''),
                            'margin': product.get('Рентабельность', 0),
                            'cost': product.get('Себестоимость', 0),
                            'profit': product.get('ВаловаяПрибыль', 0),
                            'article': product.get('Артикул', ''),
                            'manufacturer': product.get('Производитель', '')
                        }
                        
                        # Обновляем общие данные филиала
                        self.branches_data[branch_name]['total_revenue'] += revenue
                        self.branches_data[branch_name]['total_quantity'] += quantity
                        self.branches_data[branch_name]['products_count'] += 1
                        
                        # Сохраняем в общие данные товаров
                        if product_name not in self.products_data:
                            self.products_data[product_name] = {
                                'branches': {},
                                'total_ads': 0,
                                'total_revenue': 0,
                                'total_quantity': 0,
                                'unit': product.get('ЕдиницаИзмерения', 'шт'),
                                'category_path': product.get('ПутьКатегорий', ''),
                                'article': product.get('Артикул', ''),
                                'manufacturer': product.get('Производитель', '')
                            }
                        
                        self.products_data[product_name]['branches'][branch_name] = {
                            'ads': ads,
                            'revenue': revenue,
                            'quantity': quantity,
                            'margin': product.get('Рентабельность', 0)
                        }
                        
                        self.products_data[product_name]['total_ads'] += ads
                        self.products_data[product_name]['total_revenue'] += revenue
                        self.products_data[product_name]['total_quantity'] += quantity
            
            print(f"   ✅ Обработано филиалов: {len(file_branches)}")
        
        print(f"\n✅ Всего загружено филиалов: {len(self.branches_data)}")
        print(f"✅ Всего уникальных товаров: {len(self.products_data)}")
        
        return len(self.branches_data)
    
    def calculate_stock_norms_for_all(self):
        """Расчет нормативов остатков для всех филиалов и товаров"""
        
        stock_norms = {}
        
        for branch_name, branch_data in self.branches_data.items():
            # Получаем конфигурацию филиала
            branch_config = self._get_branch_config(branch_name)
            
            stock_norms[branch_name] = {}
            
            for product_name, product_data in branch_data['products'].items():
                ads = product_data['ads']
                
                # Рассчитываем нормативы для филиала
                min_stock = ads * branch_config['min_days_stock'] * branch_config['safety_multiplier']
                max_stock = ads * branch_config['max_days_stock'] * branch_config['safety_multiplier']
                
                # Рассчитываем оптимальный запас и точку заказа
                optimal_stock = (min_stock + max_stock) / 2
                reorder_point = min_stock + (ads * 5)  # +5 дней на доставку
                
                # Определяем категорию товара по ADS
                if ads >= 1000:
                    category = 'A'  # Высокооборотные
                    priority = 'high'
                elif ads >= 100:
                    category = 'B'  # Среднеоборотные
                    priority = 'medium'
                else:
                    category = 'C'  # Низкооборотные
                    priority = 'low'
                
                stock_norms[branch_name][product_name] = {
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'optimal_stock': optimal_stock,
                    'reorder_point': reorder_point,
                    'ads': ads,
                    'category': category,
                    'priority': priority,
                    'unit': product_data['unit'],
                    'revenue': product_data['revenue'],
                    'quantity': product_data['quantity'],
                    'margin': product_data['margin'],
                    'branch_config': branch_config
                }
        
        return stock_norms
    
    def _get_branch_config(self, branch_name):
        """Получение конфигурации филиала"""
        
        # Точное совпадение
        if branch_name in self.branch_hierarchy:
            return self.branch_hierarchy[branch_name]
        
        # Поиск по частичному совпадению
        branch_lower = branch_name.lower()
        
        for config_name, config in self.branch_hierarchy.items():
            if config_name.lower() in branch_lower or branch_lower in config_name.lower():
                return config
        
        # По умолчанию - магазин
        return {
            'type': 'store',
            'level': 3,
            'city': 'Неизвестно',
            'min_days_stock': 10,
            'max_days_stock': 25,
            'safety_multiplier': 1.2
        }
    
    def generate_comparative_analysis(self):
        """Сравнительный анализ между филиалами"""
        
        analysis = {
            'branches_summary': {},
            'top_products_by_ads': [],
            'multi_branch_products': [],
            'branch_specialization': {},
            'movement_opportunities': []
        }
        
        # Сводка по филиалам
        for branch_name, branch_data in self.branches_data.items():
            branch_config = self._get_branch_config(branch_name)
            
            analysis['branches_summary'][branch_name] = {
                'type': branch_config['type'],
                'city': branch_config['city'],
                'products_count': branch_data['products_count'],
                'total_revenue': branch_data['total_revenue'],
                'total_ads': branch_data['total_revenue'] / branch_data['period_days'],
                'avg_ads_per_product': (branch_data['total_revenue'] / branch_data['period_days']) / branch_data['products_count'] if branch_data['products_count'] > 0 else 0
            }
        
        # Топ товары по общему ADS
        products_total_ads = []
        for product_name, product_data in self.products_data.items():
            products_total_ads.append({
                'name': product_name,
                'total_ads': product_data['total_ads'],
                'total_revenue': product_data['total_revenue'],
                'branches_count': len(product_data['branches']),
                'branches': list(product_data['branches'].keys()),
                'unit': product_data['unit']
            })
        
        products_total_ads.sort(key=lambda x: x['total_ads'], reverse=True)
        analysis['top_products_by_ads'] = products_total_ads[:20]  # Топ-20
        
        # Товары в нескольких филиалах
        multi_branch_products = [
            product for product in products_total_ads 
            if product['branches_count'] > 1
        ]
        analysis['multi_branch_products'] = multi_branch_products
        
        # Возможности для перемещений
        for product in multi_branch_products:
            product_name = product['name']
            product_branches = self.products_data[product_name]['branches']
            
            # Находим филиалы с максимальным и минимальным ADS
            max_ads_branch = max(product_branches.items(), key=lambda x: x[1]['ads'])
            min_ads_branch = min(product_branches.items(), key=lambda x: x[1]['ads'])
            
            ads_difference = max_ads_branch[1]['ads'] - min_ads_branch[1]['ads']
            
            if ads_difference > 100:  # Значимая разница
                analysis['movement_opportunities'].append({
                    'product_name': product_name,
                    'from_branch': max_ads_branch[0],
                    'to_branch': min_ads_branch[0],
                    'from_ads': max_ads_branch[1]['ads'],
                    'to_ads': min_ads_branch[1]['ads'],
                    'ads_difference': ads_difference,
                    'unit': product['unit']
                })
        
        # Сортируем возможности по разнице ADS
        analysis['movement_opportunities'].sort(key=lambda x: x['ads_difference'], reverse=True)
        
        return analysis
    
    def print_full_analysis(self):
        """Полный анализ с выводом результатов"""
        
        print("=== ПОЛНЫЙ АНАЛИЗ ВСЕХ ФИЛИАЛОВ ===")
        print(f"Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Сводка по филиалам
        print(f"\n🏢 Сводка по филиалам:")
        for branch_name, branch_data in self.branches_data.items():
            branch_config = self._get_branch_config(branch_name)
            print(f"\n   📍 {branch_name}")
            print(f"      Тип: {branch_config['type']} | Город: {branch_config['city']}")
            print(f"      Товаров: {branch_data['products_count']:,}")
            print(f"      Выручка: {branch_data['total_revenue']:,.0f}")
            print(f"      ADS филиала: {branch_data['total_revenue'] / branch_data['period_days']:.2f}")
            print(f"      Нормативы: {branch_config['min_days_stock']}-{branch_config['max_days_stock']} дней")
        
        # Расчет нормативов
        print(f"\n📊 Расчет нормативов остатков:")
        stock_norms = self.calculate_stock_norms_for_all()
        
        for branch_name, branch_norms in stock_norms.items():
            print(f"\n   🏢 {branch_name}:")
            
            # Статистика по категориям
            categories = {'A': 0, 'B': 0, 'C': 0}
            for product_norms in branch_norms.values():
                categories[product_norms['category']] += 1
            
            print(f"      Категории ABC: A:{categories['A']}, B:{categories['B']}, C:{categories['C']}")
            
            # Топ-5 товаров по ADS
            top_products = sorted(branch_norms.items(), key=lambda x: x[1]['ads'], reverse=True)[:5]
            print(f"      Топ-5 товаров по ADS:")
            
            for i, (product_name, norms) in enumerate(top_products, 1):
                print(f"         {i}. {product_name[:40]}...")
                print(f"            ADS: {norms['ads']:.2f} | Категория: {norms['category']}")
                print(f"            Мин: {norms['min_stock']:.0f} | Макс: {norms['max_stock']:.0f} {norms['unit']}")
                print(f"            Оптимальный запас: {norms['optimal_stock']:.0f} {norms['unit']}")
        
        # Сравнительный анализ
        comparative_analysis = self.generate_comparative_analysis()
        
        print(f"\n🔍 Сравнительный анализ:")
        print(f"   Товаров в нескольких филиалах: {len(comparative_analysis['multi_branch_products'])}")
        print(f"   Возможностей для перемещений: {len(comparative_analysis['movement_opportunities'])}")
        
        # Топ возможности перемещений
        if comparative_analysis['movement_opportunities']:
            print(f"\n🚚 Топ-5 возможностей для перемещений:")
            for i, opportunity in enumerate(comparative_analysis['movement_opportunities'][:5], 1):
                print(f"   {i}. {opportunity['product_name'][:50]}...")
                print(f"      {opportunity['from_branch']} (ADS: {opportunity['from_ads']:.2f})")
                print(f"      → {opportunity['to_branch']} (ADS: {opportunity['to_ads']:.2f})")
                print(f"      Разница ADS: {opportunity['ads_difference']:.2f}")
        
        # Общие топ товары
        print(f"\n🏆 Топ-10 товаров по общему ADS:")
        for i, product in enumerate(comparative_analysis['top_products_by_ads'][:10], 1):
            print(f"   {i}. {product['name'][:50]}...")
            print(f"      Общий ADS: {product['total_ads']:.2f}")
            print(f"      Выручка: {product['total_revenue']:,.0f}")
            print(f"      Филиалов: {product['branches_count']}")
            if product['branches_count'] > 1:
                print(f"      Продается в: {', '.join(product['branches'])}")
        
        return {
            'stock_norms': stock_norms,
            'comparative_analysis': comparative_analysis
        }

def main():
    """Основная функция"""
    
    analyzer = MultiBranchAnalyzer()
    
    # Загружаем данные из нового JSON файла
    json_files = ['2025-06-30.json']
    
    branches_count = analyzer.load_multiple_json_files(json_files)
    
    if branches_count > 0:
        # Выполняем полный анализ
        results = analyzer.print_full_analysis()
        return results
    else:
        print("❌ Не удалось загрузить данные")
        return None

if __name__ == "__main__":
    main()