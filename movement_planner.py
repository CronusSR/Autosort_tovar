#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система планирования перемещений товаров между филиалами
на основе данных продаж и прогнозируемых остатков
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
# import pandas as pd  # Не используется в этом скрипте

class MovementPlanner:
    """Планировщик перемещений товаров"""
    
    def __init__(self):
        self.sales_data = {}
        self.branch_hierarchy = self._get_branch_hierarchy()
        self.supply_chains = self._get_supply_chains()
        
    def _get_branch_hierarchy(self):
        """Иерархия филиалов с характеристиками"""
        return {
            'База Склад Фурнитура Комплект': {
                'type': 'hub',
                'level': 1,
                'city': 'Алматы',
                'min_days_stock': 45,
                'max_days_stock': 90,
                'safety_multiplier': 1.5,
                'can_supply_to': ['all']
            },
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Алматы',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'can_supply_to': ['ТД Казыбаева ФУРНИТУРА магазин']
            },
            'склад фурнитура № 1': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Астана',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'can_supply_to': ['Магазин фурнитуры']
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Шымкент',
                'min_days_stock': 20,
                'max_days_stock': 45,
                'safety_multiplier': 1.3,
                'can_supply_to': ['6 Склад фурнитуры "Овощная база" Магазин']
            },
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Алматы',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'can_supply_to': []
            },
            'Магазин фурнитуры': {
                'type': 'store',
                'level': 3,
                'city': 'Астана',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'can_supply_to': []
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Шымкент',
                'min_days_stock': 10,
                'max_days_stock': 25,
                'safety_multiplier': 1.2,
                'can_supply_to': []
            }
        }
    
    def _get_supply_chains(self):
        """Цепочки поставок"""
        return {
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'primary_supplier': 'Казыбаева Склад Фурнитура TRADE',
                'secondary_suppliers': ['База Склад Фурнитура Комплект'],
                'delivery_time': 1  # дни
            },
            'Магазин фурнитуры': {
                'primary_supplier': 'склад фурнитура № 1',
                'secondary_suppliers': ['База Склад Фурнитура Комплект'],
                'delivery_time': 2  # дни
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'primary_supplier': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'secondary_suppliers': ['База Склад Фурнитура Комплект'],
                'delivery_time': 1  # дни
            },
            'Казыбаева Склад Фурнитура TRADE': {
                'primary_supplier': 'База Склад Фурнитура Комплект',
                'secondary_suppliers': [],
                'delivery_time': 1  # дни
            },
            'склад фурнитура № 1': {
                'primary_supplier': 'База Склад Фурнитура Комплект',
                'secondary_suppliers': [],
                'delivery_time': 2  # дни
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'primary_supplier': 'База Склад Фурнитура Комплект',
                'secondary_suppliers': [],
                'delivery_time': 2  # дни
            }
        }
    
    def load_sales_data(self, json_file_path):
        """Загрузка данных продаж"""
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Обрабатываем данные (избегаем дублирования)
        processed_branches = set()
        
        for branch_data in data:
            branch_name = branch_data.get('Филиал')
            
            if branch_name in processed_branches:
                continue
            processed_branches.add(branch_name)
            
            # Рассчитываем период
            start_date = datetime.strptime(branch_data['НачалоПериода'], '%Y-%m-%d')
            end_date = datetime.strptime(branch_data['КонецПериода'], '%Y-%m-%d')
            period_days = (end_date - start_date).days + 1
            
            # Инициализируем данные филиала
            self.sales_data[branch_name] = {
                'products': {},
                'period_days': period_days,
                'total_revenue': 0,
                'total_ads': 0
            }
            
            # Обрабатываем товары
            for product in branch_data.get('Продажи', []):
                product_name = product.get('Номенклатура')
                revenue = product.get('Выручка', 0)
                quantity = product.get('Количество', 0)
                ads = revenue / period_days if period_days > 0 else 0
                
                if ads > 0:  # Только товары с продажами
                    self.sales_data[branch_name]['products'][product_name] = {
                        'ads': ads,
                        'revenue': revenue,
                        'quantity': quantity,
                        'unit': product.get('ЕдиницаИзмерения', 'шт'),
                        'category_path': product.get('ПутьКатегорий', ''),
                        'margin': product.get('Рентабельность', 0),
                        'cost': product.get('Себестоимость', 0)
                    }
                    
                    self.sales_data[branch_name]['total_revenue'] += revenue
                    self.sales_data[branch_name]['total_ads'] += ads
        
        return len(processed_branches)
    
    def calculate_stock_norms(self, branch_name):
        """Расчет нормативов запасов для филиала"""
        
        if branch_name not in self.sales_data or branch_name not in self.branch_hierarchy:
            return {}
        
        branch_config = self.branch_hierarchy[branch_name]
        branch_sales = self.sales_data[branch_name]['products']
        
        stock_norms = {}
        
        for product_name, product_data in branch_sales.items():
            ads = product_data['ads']
            
            # Рассчитываем нормативы
            min_stock = ads * branch_config['min_days_stock'] * branch_config['safety_multiplier']
            max_stock = ads * branch_config['max_days_stock'] * branch_config['safety_multiplier']
            
            # Определяем точку заказа с учетом времени доставки
            supply_chain = self.supply_chains.get(branch_name, {})
            delivery_time = supply_chain.get('delivery_time', 3)
            reorder_point = ads * (branch_config['min_days_stock'] + delivery_time)
            
            stock_norms[product_name] = {
                'min_stock': min_stock,
                'max_stock': max_stock,
                'reorder_point': reorder_point,
                'ads': ads,
                'unit': product_data['unit'],
                'category_path': product_data['category_path'],
                'revenue': product_data['revenue'],
                'delivery_time': delivery_time
            }
        
        return stock_norms
    
    def generate_movement_plan(self, forecast_horizon_days=30):
        """Генерация плана перемещений на основе прогноза"""
        
        movement_plan = {
            'horizon_days': forecast_horizon_days,
            'movements': [],
            'procurement_needs': {},
            'summary': {}
        }
        
        # Рассчитываем нормативы для всех филиалов
        all_stock_norms = {}
        for branch_name in self.sales_data.keys():
            all_stock_norms[branch_name] = self.calculate_stock_norms(branch_name)
        
        # Прогнозируем потребности
        for branch_name, stock_norms in all_stock_norms.items():
            branch_config = self.branch_hierarchy[branch_name]
            supply_chain = self.supply_chains.get(branch_name, {})
            
            for product_name, norms in stock_norms.items():
                # Прогнозируем потребление на горизонт планирования
                forecast_consumption = norms['ads'] * forecast_horizon_days
                
                # Рассчитываем потребность в поставках
                if forecast_consumption > norms['min_stock']:
                    # Определяем количество для заказа
                    order_quantity = norms['max_stock'] - norms['min_stock']
                    
                    # Определяем поставщика
                    primary_supplier = supply_chain.get('primary_supplier')
                    
                    if primary_supplier:
                        # Создаем запись о перемещении
                        movement = {
                            'product_name': product_name,
                            'from_location': primary_supplier,
                            'to_location': branch_name,
                            'quantity': order_quantity,
                            'unit': norms['unit'],
                            'priority': self._calculate_priority(norms['ads']),
                            'deadline': datetime.now() + timedelta(days=norms['delivery_time']),
                            'reason': f"Прогноз потребления: {forecast_consumption:.0f} {norms['unit']}",
                            'category_path': norms['category_path'],
                            'type': 'planned'
                        }
                        
                        movement_plan['movements'].append(movement)
                        
                        # Добавляем в потребности поставщика
                        if primary_supplier not in movement_plan['procurement_needs']:
                            movement_plan['procurement_needs'][primary_supplier] = []
                        
                        movement_plan['procurement_needs'][primary_supplier].append({
                            'product_name': product_name,
                            'quantity': order_quantity,
                            'unit': norms['unit'],
                            'for_branch': branch_name,
                            'deadline': datetime.now() + timedelta(days=norms['delivery_time'])
                        })
        
        # Генерируем сводку
        movement_plan['summary'] = self._generate_movement_summary(movement_plan['movements'])
        
        return movement_plan
    
    def _calculate_priority(self, ads):
        """Расчет приоритета товара"""
        if ads >= 1000:
            return 'high'
        elif ads >= 100:
            return 'medium'
        else:
            return 'low'
    
    def _generate_movement_summary(self, movements):
        """Генерация сводки по перемещениям"""
        
        summary = {
            'total_movements': len(movements),
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_destination': {},
            'by_source': {}
        }
        
        for movement in movements:
            # По приоритету
            priority = movement['priority']
            summary['by_priority'][priority] += 1
            
            # По назначению
            destination = movement['to_location']
            if destination not in summary['by_destination']:
                summary['by_destination'][destination] = 0
            summary['by_destination'][destination] += 1
            
            # По источнику
            source = movement['from_location']
            if source not in summary['by_source']:
                summary['by_source'][source] = 0
            summary['by_source'][source] += 1
        
        return summary
    
    def print_movement_plan(self, movement_plan):
        """Вывод плана перемещений"""
        
        print("=== ПЛАН ПЕРЕМЕЩЕНИЙ ТОВАРОВ ===")
        print(f"Горизонт планирования: {movement_plan['horizon_days']} дней")
        print(f"Дата составления: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Сводка
        summary = movement_plan['summary']
        print(f"\n📊 Сводка:")
        print(f"   Всего перемещений: {summary['total_movements']}")
        print(f"   По приоритету: Высокий: {summary['by_priority']['high']}, Средний: {summary['by_priority']['medium']}, Низкий: {summary['by_priority']['low']}")
        
        # По назначению
        print(f"\n🎯 Перемещения по назначению:")
        for destination, count in summary['by_destination'].items():
            print(f"   {destination}: {count} перемещений")
        
        # По источнику
        print(f"\n📦 Перемещения по источнику:")
        for source, count in summary['by_source'].items():
            print(f"   {source}: {count} перемещений")
        
        # Топ-10 перемещений по приоритету
        print(f"\n🔝 Топ-10 приоритетных перемещений:")
        movements_by_priority = sorted(
            movement_plan['movements'], 
            key=lambda x: ('high', 'medium', 'low').index(x['priority'])
        )
        
        for i, movement in enumerate(movements_by_priority[:10], 1):
            print(f"   {i}. {movement['product_name'][:50]}...")
            print(f"      {movement['from_location']} → {movement['to_location']}")
            print(f"      Количество: {movement['quantity']:.0f} {movement['unit']}")
            print(f"      Приоритет: {movement['priority']} | Срок: {movement['deadline'].strftime('%Y-%m-%d')}")
        
        # Потребности в закупках
        print(f"\n🛒 Потребности в закупках:")
        for supplier, needs in movement_plan['procurement_needs'].items():
            print(f"   {supplier}:")
            print(f"      Товаров к закупке: {len(needs)}")
            
            # Группируем по категориям
            categories = {}
            for need in needs:
                category = need.get('category_path', 'Прочее')
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            for category, count in list(categories.items())[:3]:  # Топ-3 категории
                print(f"         {category}: {count} товаров")
        
        return movement_plan

def main():
    """Основная функция"""
    
    planner = MovementPlanner()
    
    # Загружаем данные
    json_file = '2025-06-30 (3).json'
    if os.path.exists(json_file):
        branches_count = planner.load_sales_data(json_file)
        print(f"✅ Загружено {branches_count} филиалов")
        
        # Генерируем план перемещений
        movement_plan = planner.generate_movement_plan(forecast_horizon_days=30)
        
        # Выводим план
        planner.print_movement_plan(movement_plan)
        
        return movement_plan
    else:
        print(f"❌ Файл {json_file} не найден")
        return None

if __name__ == "__main__":
    main()