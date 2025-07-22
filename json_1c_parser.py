#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер для JSON файлов из 1С с поддержкой путей категорий
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re


class Json1CParser:
    """Парсер для обработки JSON выгрузок из 1С"""
    
    def __init__(self):
        self.sales_data = {}
        self.stock_data = {}
        self.category_paths = {}
        self.excluded_categories = set()
        
        # Паттерны для исключения категорий
        self.exclusion_patterns = [
            r'^/[^/]+/кромка пвх/?$',  # Общие категории кромки без детализации
            r'^/[^/]+/\d+\*[\d,]+мм пвх/?$',  # Размеры без цвета/кода
            r'/услуги/',  # Любые услуги
            r'/расходные материалы/',  # Расходники
            r'/сопутствующие товары/',  # Сопутка
        ]
        
    def parse_sales_json(self, json_file_path: str) -> Dict:
        """Парсинг JSON файла с продажами из 1С"""
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.parse_sales_json_from_data(data)
    
    def parse_sales_json_from_data(self, data) -> Dict:
        """Парсинг данных продаж из различных форматов"""
        
        # Определяем формат файла
        if isinstance(data, list):
            # Проверяем, что это за список
            if data and isinstance(data[0], dict):
                # Если первый элемент содержит ключи нового формата
                if 'Филиал' in data[0] and 'Продажи' in data[0]:
                    # Новый формат - массив объектов с филиалами
                    return self._parse_new_array_format(data)
                else:
                    # Старый формат - просто массив товаров
                    return self._parse_old_format(data)
            else:
                return self._parse_old_format(data)
        else:
            # Новый формат с метаданными (один объект)
            return self._parse_new_format(data)
    
    def _parse_old_format(self, data: List[Dict]) -> Dict:
        """Парсинг старого формата (массив объектов)"""
        
        result = {
            'metadata': {
                'format': 'old',
                'period': {'days': 30},  # По умолчанию месяц
                'branches': set()
            },
            'sales_by_branch': {},
            'category_paths': {}
        }
        
        # Группируем по филиалам (если есть поле)
        for item in data:
            # Пытаемся определить филиал
            branch = item.get('Филиал', 'Общий')
            
            if branch not in result['sales_by_branch']:
                result['sales_by_branch'][branch] = []
            
            # Проверяем путь категорий
            category_path = item.get('ПутьКатегорий', '')
            
            # Добавляем товар если он не исключен
            if not self._is_excluded_category(category_path, item['Номенклатура']):
                result['sales_by_branch'][branch].append({
                    'product_name': item['Номенклатура'],
                    'quantity': item.get('Количество', 0),
                    'revenue': item.get('Выручка', 0),
                    'cost': item.get('Себестоимость', 0),
                    'profit': item.get('ВаловаяПрибыль', 0),
                    'margin': item.get('Рентабельность', 0),
                    'category_path': category_path
                })
                
                # Сохраняем путь категории
                if category_path:
                    result['category_paths'][item['Номенклатура']] = category_path
            
            result['metadata']['branches'].add(branch)
        
        return result
    
    def _parse_new_array_format(self, data: List[Dict]) -> Dict:
        """Парсинг нового формата - массив объектов с филиалами"""
        
        result = {
            'metadata': {
                'format': 'new_array',
                'branches': []
            },
            'sales_by_branch': {},
            'category_paths': {}
        }
        
        all_periods = []
        
        # Обрабатываем каждый элемент массива (каждый филиал)
        for branch_data in data:
            branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
            result['metadata']['branches'].append(branch_name)
            result['sales_by_branch'][branch_name] = []
            
            # Извлекаем метаданные
            result['metadata']['created_at'] = branch_data.get('ДатаВыгрузки')
            
            # Рассчитываем период
            period = {
                'НачалоПериода': branch_data.get('НачалоПериода'),
                'КонецПериода': branch_data.get('КонецПериода')
            }
            period_info = self._calculate_period(period)
            all_periods.append(period_info)
            
            # Обрабатываем продажи для этого филиала
            for item in branch_data.get('Продажи', []):
                category_path = item.get('ПутьКатегорий', '')
                
                # Проверяем исключения
                if not self._is_excluded_category(category_path, item['Номенклатура']):
                    # Рассчитываем ADS
                    period_days = period_info['days']
                    ads = item['Выручка'] / period_days if period_days > 0 else 0
                    
                    # Расчет оборачиваемости
                    turnover_days = self._calculate_turnover_days(item, period_days)
                    
                    result['sales_by_branch'][branch_name].append({
                        'product_name': item['Номенклатура'],
                        'quantity': item.get('Количество', 0),
                        'revenue': item.get('Выручка', 0),
                        'cost': item.get('Себестоимость', 0),
                        'profit': item.get('ВаловаяПрибыль', 0),
                        'margin': item.get('Рентабельность', 0),
                        'ads': ads,
                        'turnover_days': turnover_days,
                        'turnover_rate': round(365 / turnover_days, 2) if turnover_days > 0 else 0,
                        'category_path': category_path,
                        'unit': item.get('ЕдиницаИзмерения', 'шт'),
                        'article': item.get('Артикул', ''),
                        'manufacturer': item.get('Производитель', '')
                    })
                    
                    # Сохраняем путь категории
                    if category_path:
                        result['category_paths'][item['Номенклатура']] = category_path
                else:
                    # Логируем исключенные категории
                    self.excluded_categories.add(f"{category_path} | {item['Номенклатура']}")
        
        # Используем период из первого элемента как общий
        if all_periods:
            result['metadata']['period'] = all_periods[0]
        else:
            result['metadata']['period'] = {'days': 30}
        
        return result
    
    def _parse_new_format(self, data: Dict) -> Dict:
        """Парсинг нового формата с метаданными"""
        
        # Определяем структуру: один филиал или несколько
        if 'Филиал' in data and 'Продажи' in data:
            # Формат с одним филиалом (как в файлах 2025-06-30)
            return self._parse_single_branch_format(data)
        else:
            # Формат с несколькими филиалами
            result = {
                'metadata': {
                    'format': 'new',
                    'created_at': data.get('ДатаВыгрузки'),
                    'period': self._calculate_period(data.get('Период', {})),
                    'organization': data.get('Организация'),
                    'branches': []
                },
                'sales_by_branch': {},
                'category_paths': {}
            }
            
            # Обрабатываем продажи по филиалам
            for branch_data in data.get('ПродажиПоФилиалам', []):
                branch_name = branch_data['Филиал']
                result['metadata']['branches'].append(branch_name)
                result['sales_by_branch'][branch_name] = []
                
                for item in branch_data.get('Продажи', []):
                    category_path = item.get('ПутьКатегорий', '')
                    
                    # Проверяем исключения
                    if not self._is_excluded_category(category_path, item['Номенклатура']):
                        # Рассчитываем ADS
                        period_days = result['metadata']['period']['days']
                        ads = item['Выручка'] / period_days if period_days > 0 else 0
                        
                        # Расчет оборачиваемости
                        turnover_days = self._calculate_turnover_days(item, period_days)
                        
                        result['sales_by_branch'][branch_name].append({
                            'product_name': item['Номенклатура'],
                            'quantity': item.get('Количество', 0),
                            'revenue': item.get('Выручка', 0),
                            'cost': item.get('Себестоимость', 0),
                            'profit': item.get('ВаловаяПрибыль', 0),
                            'margin': item.get('Рентабельность', 0),
                            'ads': ads,
                            'turnover_days': turnover_days,
                            'turnover_rate': round(365 / turnover_days, 2) if turnover_days > 0 else 0,
                            'category_path': category_path,
                            'unit': item.get('ЕдиницаИзмерения', 'шт'),
                            'article': item.get('Артикул', ''),
                            'manufacturer': item.get('Производитель', '')
                        })
                        
                        # Сохраняем путь категории
                        if category_path:
                            result['category_paths'][item['Номенклатура']] = category_path
                    else:
                        # Логируем исключенные категории
                        self.excluded_categories.add(f"{category_path} | {item['Номенклатура']}")
            
            return result
    
    def _parse_single_branch_format(self, data: Dict) -> Dict:
        """Парсинг формата с одним филиалом (как в файлах 2025-06-30)"""
        
        # Извлекаем период из дат
        period = {
            'НачалоПериода': data.get('НачалоПериода'),
            'КонецПериода': data.get('КонецПериода')
        }
        
        result = {
            'metadata': {
                'format': 'new_single_branch',
                'created_at': data.get('ДатаВыгрузки'),
                'period': self._calculate_period(period),
                'organization': data.get('Организация'),
                'branches': [data['Филиал']]
            },
            'sales_by_branch': {},
            'category_paths': {}
        }
        
        branch_name = data['Филиал']
        result['sales_by_branch'][branch_name] = []
        
        # Обрабатываем продажи
        for item in data.get('Продажи', []):
            category_path = item.get('ПутьКатегорий', '')
            
            # Проверяем исключения
            if not self._is_excluded_category(category_path, item['Номенклатура']):
                # Рассчитываем ADS
                period_days = result['metadata']['period']['days']
                ads = item['Выручка'] / period_days if period_days > 0 else 0
                
                # Расчет оборачиваемости
                turnover_days = self._calculate_turnover_days(item, period_days)
                
                result['sales_by_branch'][branch_name].append({
                    'product_name': item['Номенклатура'],
                    'quantity': item.get('Количество', 0),
                    'revenue': item.get('Выручка', 0),
                    'cost': item.get('Себестоимость', 0),
                    'profit': item.get('ВаловаяПрибыль', 0),
                    'margin': item.get('Рентабельность', 0),
                    'ads': ads,
                    'turnover_days': turnover_days,
                    'turnover_rate': round(365 / turnover_days, 2) if turnover_days > 0 else 0,
                    'category_path': category_path,
                    'unit': item.get('ЕдиницаИзмерения', 'шт'),
                    'article': item.get('Артикул', ''),
                    'manufacturer': item.get('Производитель', '')
                })
                
                # Сохраняем путь категории
                if category_path:
                    result['category_paths'][item['Номенклатура']] = category_path
            else:
                # Логируем исключенные категории
                self.excluded_categories.add(f"{category_path} | {item['Номенклатура']}")
        
        return result
    
    def parse_stock_json(self, json_file_path: str) -> Dict:
        """Парсинг JSON файла с остатками из 1С"""
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.parse_stock_json_from_dict(data)
    
    def parse_stock_json_from_dict(self, data: Dict) -> Dict:
        """Парсинг остатков из словаря данных"""
        
        result = {
            'date': data.get('ДатаОстатков', datetime.now().strftime('%Y-%m-%d')),
            'created_at': data.get('ДатаВыгрузки', datetime.now().strftime('%Y-%m-%dT%H:%M:%S')),
            'organization': data.get('Организация', ''),
            'stock_by_warehouse': {},
            'warehouse_info': {}
        }
        
        # Обрабатываем остатки по складам
        for warehouse_data in data.get('ОстаткиПоСкладам', []):
            warehouse_name = warehouse_data['Склад']
            result['stock_by_warehouse'][warehouse_name] = []
            
            # Сохраняем информацию о складе
            result['warehouse_info'][warehouse_name] = {
                'city': warehouse_data.get('Город', ''),
                'type': warehouse_data.get('ТипСклада', ''),
                'full_name': warehouse_name
            }
            
            for item in warehouse_data.get('Остатки', []):
                category_path = item.get('ПутьКатегорий', '')
                quantity = item.get('Количество', 0)
                
                # Проверяем исключения и фильтруем нулевые остатки
                if (not self._is_excluded_category(category_path, item['Номенклатура']) and 
                    quantity > 0):
                    
                    result['stock_by_warehouse'][warehouse_name].append({
                        'product_name': item['Номенклатура'],
                        'quantity': quantity,
                        'amount': item.get('Сумма', 0),
                        'avg_price': item.get('СредняяЦена', 0),
                        'category_path': category_path,
                        'unit': item.get('ЕдиницаИзмерения', 'шт'),
                        'article': item.get('Артикул', ''),
                        'manufacturer': item.get('Производитель', '')
                    })
        
        return result
    
    def _calculate_period(self, period_data: Dict) -> Dict:
        """Вычисление периода в днях"""
        
        if not period_data:
            return {'days': 30}  # По умолчанию месяц
        
        try:
            start = datetime.strptime(period_data['НачалоПериода'], '%Y-%m-%d')
            end = datetime.strptime(period_data['КонецПериода'], '%Y-%m-%d')
            days = (end - start).days + 1
            
            return {
                'start': period_data['НачалоПериода'],
                'end': period_data['КонецПериода'],
                'days': days
            }
        except:
            return {'days': 30}
    
    def _is_excluded_category(self, category_path: str, product_name: str) -> bool:
        """Проверка, нужно ли исключить товар по пути категории"""
        
        if not category_path:
            return False
        
        # Проверяем по паттернам исключений
        for pattern in self.exclusion_patterns:
            if re.match(pattern, category_path):
                return True
        
        # Проверяем по логике названия (как в старой системе)
        name_lower = product_name.lower()
        
        # Точные исключения категорий
        exact_exclusions = [
            'кромка пвх', 'кромка', 'плинтус пластиковый 3м',
            'посудосушители', 'фурнитура', 'материалы',
            'итого', 'всего', 'total'
        ]
        
        if name_lower in exact_exclusions:
            return True
        
        # Проверяем короткие общие названия без детализации
        if len(name_lower) <= 15:
            # Категория если есть размер БЕЗ цвета/кода
            size_pattern = r'^\d+\*[\d,]+мм\s+пвх$'
            if re.match(size_pattern, name_lower):
                return True
        
        return False
    
    def _calculate_turnover_days(self, item: Dict, period_days: int) -> float:
        """Расчет дней оборачиваемости товара"""
        
        try:
            # Базовый расчет: если в периоде X дней продали Y единиц,
            # то за сколько дней продадим текущий остаток
            quantity = item.get('Количество', 0)
            
            if quantity <= 0 or period_days <= 0:
                return float('inf')  # Бесконечная оборачиваемость
            
            # Средняя дневная продажа по количеству
            daily_quantity = quantity / period_days
            
            # Для более точного расчета можем использовать среднюю цену
            # и оценить остаток в деньгах, но пока используем количество
            
            # Оборачиваемость = сколько дней нужно для продажи одной единицы
            turnover_days = 1 / daily_quantity if daily_quantity > 0 else float('inf')
            
            # Ограничиваем максимальное значение для практичности
            return min(turnover_days, 9999)
            
        except Exception:
            return float('inf')
    
    def calculate_turnover_analytics(self, sales_data: Dict) -> Dict:
        """Расчет аналитики оборачиваемости по всем товарам"""
        
        turnover_analytics = {
            'total_products': 0,
            'fast_moving': [],  # Быстрооборачиваемые (< 30 дней)
            'medium_moving': [],  # Средние (30-90 дней)
            'slow_moving': [],  # Медленные (90-365 дней)
            'very_slow_moving': [],  # Очень медленные (> 365 дней)
            'no_movement': [],  # Без движения
            'categories_analytics': {}
        }
        
        all_products = []
        
        # Собираем все товары из всех филиалов
        for branch, products in sales_data.get('sales_by_branch', {}).items():
            for product in products:
                product_with_branch = product.copy()
                product_with_branch['branch'] = branch
                all_products.append(product_with_branch)
        
        turnover_analytics['total_products'] = len(all_products)
        
        # Классифицируем по оборачиваемости
        for product in all_products:
            turnover_days = product.get('turnover_days', float('inf'))
            
            product_info = {
                'name': product['product_name'],
                'branch': product['branch'],
                'turnover_days': turnover_days,
                'turnover_rate': product.get('turnover_rate', 0),
                'ads': product.get('ads', 0),
                'revenue': product.get('revenue', 0),
                'category_path': product.get('category_path', '')
            }
            
            if turnover_days == float('inf'):
                turnover_analytics['no_movement'].append(product_info)
            elif turnover_days <= 30:
                turnover_analytics['fast_moving'].append(product_info)
            elif turnover_days <= 90:
                turnover_analytics['medium_moving'].append(product_info)
            elif turnover_days <= 365:
                turnover_analytics['slow_moving'].append(product_info)
            else:
                turnover_analytics['very_slow_moving'].append(product_info)
            
            # Аналитика по категориям
            category = product.get('category_path', 'Без категории').split('/')[1] if '/' in product.get('category_path', '') else 'Без категории'
            if category not in turnover_analytics['categories_analytics']:
                turnover_analytics['categories_analytics'][category] = {
                    'fast_count': 0,
                    'medium_count': 0,
                    'slow_count': 0,
                    'very_slow_count': 0,
                    'no_movement_count': 0,
                    'total_revenue': 0,
                    'avg_turnover_days': 0
                }
            
            cat_stats = turnover_analytics['categories_analytics'][category]
            cat_stats['total_revenue'] += product.get('revenue', 0)
            
            if turnover_days == float('inf'):
                cat_stats['no_movement_count'] += 1
            elif turnover_days <= 30:
                cat_stats['fast_count'] += 1
            elif turnover_days <= 90:
                cat_stats['medium_count'] += 1
            elif turnover_days <= 365:
                cat_stats['slow_count'] += 1
            else:
                cat_stats['very_slow_count'] += 1
        
        # Сортируем списки по оборачиваемости
        for category in ['fast_moving', 'medium_moving', 'slow_moving', 'very_slow_moving']:
            turnover_analytics[category].sort(key=lambda x: x['turnover_days'])
        
        # Сортируем товары без движения по выручке
        turnover_analytics['no_movement'].sort(key=lambda x: x['revenue'], reverse=True)
        
        return turnover_analytics
    
    def get_products_by_category_pattern(self, pattern: str) -> List[Dict]:
        """Получить товары по паттерну категории"""
        
        result = []
        
        for branch, products in self.sales_data.items():
            for product in products:
                if 'category_path' in product:
                    if re.match(pattern, product['category_path']):
                        result.append({
                            'branch': branch,
                            **product
                        })
        
        return result
    
    def get_category_tree(self) -> Dict:
        """Построить дерево категорий из путей"""
        
        tree = {}
        
        for path in self.category_paths.values():
            parts = path.strip('/').split('/')
            current = tree
            
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        return tree
    
    def export_for_movement_system(self, sales_data: Dict, stock_data: Dict) -> Tuple[Dict, pd.DataFrame]:
        """Экспорт данных в формат для системы рекомендаций"""
        
        # Преобразуем продажи для системы движения
        ads_by_product = {}
        sales_by_branch = {}
        
        for branch, products in sales_data['sales_by_branch'].items():
            branch_df_data = []
            
            for product in products:
                # Добавляем в ADS
                if product['product_name'] not in ads_by_product:
                    ads_by_product[product['product_name']] = {}
                
                ads_by_product[product['product_name']][branch] = product.get('ads', 0)
                
                # Добавляем в данные филиала
                branch_df_data.append({
                    'product_name': product['product_name'],
                    'total_sales': product['revenue'],
                    'ads': product.get('ads', 0),
                    'quantity': product['quantity'],
                    'revenue': product['revenue'],
                    'cost': product['cost'],
                    'turnover_days': product.get('turnover_days', float('inf')),
                    'turnover_rate': product.get('turnover_rate', 0),
                    'category_path': product.get('category_path', '')
                })
            
            if branch_df_data:
                sales_by_branch[branch] = pd.DataFrame(branch_df_data)
        
        # Преобразуем остатки
        stock_list = []
        for warehouse, products in stock_data['stock_by_warehouse'].items():
            for product in products:
                stock_list.append({
                    'Склад': warehouse,
                    'Номенклатура': product['product_name'],
                    'Количество': product['quantity'],
                    'Сумма': product['amount']
                })
        
        stock_df = pd.DataFrame(stock_list) if stock_list else pd.DataFrame()
        
        return {
            'sales_by_branch': sales_by_branch,
            'ads_by_product': ads_by_product,
            'metadata': sales_data['metadata']
        }, stock_df


# Пример использования
if __name__ == "__main__":
    parser = Json1CParser()
    
    # Пример парсинга
    # sales_data = parser.parse_sales_json('sales_2025_06.json')
    # stock_data = parser.parse_stock_json('stock_2025_07_08.json')
    
    # Экспорт для системы движения
    # movement_data, stock_df = parser.export_for_movement_system(sales_data, stock_data)
    
    print("Парсер JSON 1C готов к использованию!")