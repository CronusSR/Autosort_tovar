"""
Система аналитики оборачиваемости товаров
Включает:
- Расчет оборачиваемости по категориям
- Оборачиваемость по складам с указанием городов
- ABC-анализ по складам
- Интеграция с системой перемещений
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import streamlit as st
from typing import Dict, List, Tuple, Optional

class TurnoverAnalyticsSystem:
    def __init__(self):
        self.warehouse_cities = {
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': 'Шымкент',
            '6 Склад фурнитуры "Овощная база" Магазин': 'Шымкент',
            'АО Склад Фурнитура TRADE': 'Астана',
            'Барыс Склад Фурнитура TRADE': 'Астана',
            'Казыбаева Склад Фурнитура TRADE': 'Астана',
            'Магазин фурнитуры': 'Астана',
            'склад фурнитура № 1': 'Астана',
            'ТД Казыбаева ФУРНИТУРА магазин': 'Астана'
        }
        
    def load_stock_data(self, file_path: str) -> Dict:
        """Загрузка данных остатков из JSON файла"""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    
    def load_sales_data(self, file_path: str) -> pd.DataFrame:
        """Загрузка данных продаж из Excel файла"""
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, skiprows=2)
            
            # Стандартизация названий колонок
            df.columns = df.columns.str.strip()
            
            # Поиск колонок с продажами (содержат 'прод' в названии)
            sales_columns = [col for col in df.columns if 'прод' in col.lower()]
            
            return df
        except Exception as e:
            st.error(f"Ошибка при загрузке файла продаж: {e}")
            return pd.DataFrame()
    
    def extract_category_hierarchy(self, path: str) -> Tuple[str, str, str]:
        """Извлечение иерархии категорий из пути"""
        parts = path.strip('/').split('/')
        parts = [p for p in parts if p]  # Убираем пустые элементы
        
        if len(parts) >= 3:
            return parts[-1], parts[-2], parts[-3]
        elif len(parts) == 2:
            return parts[-1], parts[-2], "Общее"
        elif len(parts) == 1:
            return parts[0], "Общее", "Общее"
        else:
            return "Неизвестно", "Общее", "Общее"
    
    def calculate_turnover_by_category(self, stock_data: Dict, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Расчет оборачиваемости по категориям
        Возвращает DataFrame с колонками:
        - Категория
        - Подкатегория
        - Остаток (себестоимость)
        - Продажи (за период)
        - % от общего остатка
        - Оборачиваемость (дни)
        """
        category_data = defaultdict(lambda: {
            'stock_cost': 0,
            'stock_qty': 0,
            'sales_qty': 0,
            'sales_sum': 0,
            'items': set()
        })
        
        # Собираем данные по остаткам
        total_stock_cost = 0
        for warehouse in stock_data['ОстаткиПоСкладам']:
            for item in warehouse['Остатки']:
                cat1, cat2, cat3 = self.extract_category_hierarchy(item['ПутьКатегорий'])
                key = f"{cat3}/{cat2}/{cat1}"
                
                category_data[key]['stock_cost'] += item['Стоимость']
                category_data[key]['stock_qty'] += item['Количество']
                category_data[key]['items'].add(item['Артикул'])
                total_stock_cost += item['Стоимость']
        
        # Собираем данные по продажам
        if not sales_df.empty:
            sales_columns = [col for col in sales_df.columns if 'прод' in col.lower()]
            
            for _, row in sales_df.iterrows():
                if pd.notna(row.get('Артикул')):
                    article = str(row['Артикул'])
                    
                    # Находим категорию по артикулу
                    for key, data in category_data.items():
                        if article in data['items']:
                            # Суммируем продажи по всем складам
                            for col in sales_columns:
                                if pd.notna(row.get(col)):
                                    try:
                                        sales_value = float(row[col])
                                        if 'шт' in col.lower():
                                            data['sales_qty'] += sales_value
                                        else:
                                            data['sales_sum'] += sales_value
                                    except:
                                        pass
                            break
        
        # Формируем результат
        results = []
        for category, data in category_data.items():
            cat_parts = category.split('/')
            
            # Расчет оборачиваемости в днях
            if data['sales_sum'] > 0:
                # Оборачиваемость = (Остатки * 365) / Продажи
                turnover_days = (data['stock_cost'] * 365) / data['sales_sum']
            else:
                turnover_days = 999999  # Нет продаж
            
            # Процент от общего остатка
            percent_of_total = (data['stock_cost'] / total_stock_cost * 100) if total_stock_cost > 0 else 0
            
            results.append({
                'Основная категория': cat_parts[0] if len(cat_parts) > 0 else 'Неизвестно',
                'Подкатегория': cat_parts[1] if len(cat_parts) > 1 else 'Общее',
                'Категория товара': cat_parts[2] if len(cat_parts) > 2 else 'Общее',
                'Остаток (себестоимость)': data['stock_cost'],
                'Остаток (количество)': data['stock_qty'],
                'Продажи (сумма)': data['sales_sum'],
                'Продажи (количество)': data['sales_qty'],
                '% от общего остатка': percent_of_total,
                'Оборачиваемость (дни)': turnover_days
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Остаток (себестоимость)', ascending=False)
    
    def calculate_warehouse_turnover(self, stock_data: Dict, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Расчет оборачиваемости по складам
        Возвращает DataFrame с колонками:
        - Склад
        - Город
        - Тотальные продажи
        - Тотальные остатки
        - Оборачиваемость (дни)
        """
        warehouse_data = defaultdict(lambda: {
            'city': '',
            'stock_cost': 0,
            'stock_qty': 0,
            'sales_sum': 0,
            'articles': set()
        })
        
        # Собираем данные по остаткам
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            city = self.warehouse_cities.get(wh_name, 'Не указан')
            
            warehouse_data[wh_name]['city'] = city
            
            for item in warehouse['Остатки']:
                warehouse_data[wh_name]['stock_cost'] += item['Стоимость']
                warehouse_data[wh_name]['stock_qty'] += item['Количество']
                warehouse_data[wh_name]['articles'].add(item['Артикул'])
        
        # Собираем данные по продажам
        if not sales_df.empty:
            for wh_name, wh_data in warehouse_data.items():
                # Ищем колонки продаж для этого склада
                sales_columns = [col for col in sales_df.columns 
                               if 'прод' in col.lower() and any(part in col.lower() 
                               for part in wh_name.lower().split())]
                
                if sales_columns:
                    for _, row in sales_df.iterrows():
                        if pd.notna(row.get('Артикул')) and str(row['Артикул']) in wh_data['articles']:
                            for col in sales_columns:
                                if pd.notna(row.get(col)) and 'сумм' in col.lower():
                                    try:
                                        wh_data['sales_sum'] += float(row[col])
                                    except:
                                        pass
        
        # Формируем результат
        results = []
        for wh_name, data in warehouse_data.items():
            # Расчет оборачиваемости
            if data['sales_sum'] > 0:
                turnover_days = (data['stock_cost'] * 365) / data['sales_sum']
            else:
                turnover_days = 999999
            
            results.append({
                'Склад': wh_name,
                'Город': data['city'],
                'Остатки (себестоимость)': data['stock_cost'],
                'Остатки (количество)': data['stock_qty'],
                'Продажи (сумма)': data['sales_sum'],
                'Оборачиваемость (дни)': turnover_days
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Остатки (себестоимость)', ascending=False)
    
    def calculate_abc_by_warehouse(self, stock_data: Dict, sales_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        ABC-анализ по каждому складу
        Возвращает словарь {склад: DataFrame с ABC-анализом}
        """
        abc_results = {}
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            city = self.warehouse_cities.get(wh_name, 'Не указан')
            
            # Собираем данные по категориям для склада
            category_data = defaultdict(lambda: {
                'stock_cost': 0,
                'sales_sum': 0,
                'items': []
            })
            
            total_stock = 0
            for item in warehouse['Остатки']:
                cat1, cat2, cat3 = self.extract_category_hierarchy(item['ПутьКатегорий'])
                key = f"{cat3}/{cat2}/{cat1}"
                
                category_data[key]['stock_cost'] += item['Стоимость']
                category_data[key]['items'].append({
                    'article': item['Артикул'],
                    'name': item['Номенклатура'],
                    'cost': item['Стоимость']
                })
                total_stock += item['Стоимость']
            
            # Считаем продажи если есть данные
            if not sales_df.empty:
                sales_columns = [col for col in sales_df.columns 
                               if 'прод' in col.lower() and any(part in col.lower() 
                               for part in wh_name.lower().split())]
                
                if sales_columns:
                    for _, row in sales_df.iterrows():
                        if pd.notna(row.get('Артикул')):
                            article = str(row['Артикул'])
                            
                            for key, data in category_data.items():
                                if any(item['article'] == article for item in data['items']):
                                    for col in sales_columns:
                                        if pd.notna(row.get(col)) and 'сумм' in col.lower():
                                            try:
                                                data['sales_sum'] += float(row[col])
                                            except:
                                                pass
                                    break
            
            # Формируем ABC-анализ
            categories = []
            for category, data in category_data.items():
                cat_parts = category.split('/')
                categories.append({
                    'Категория': cat_parts[2] if len(cat_parts) > 2 else 'Общее',
                    'Подкатегория': cat_parts[1] if len(cat_parts) > 1 else 'Общее',
                    'Остаток': data['stock_cost'],
                    'Продажи': data['sales_sum'],
                    'Доля в остатках': (data['stock_cost'] / total_stock * 100) if total_stock > 0 else 0
                })
            
            df = pd.DataFrame(categories)
            df = df.sort_values('Остаток', ascending=False)
            
            # Присваиваем ABC-категории
            df['Накопленная доля'] = df['Доля в остатках'].cumsum()
            df['ABC категория'] = pd.cut(df['Накопленная доля'], 
                                         bins=[0, 80, 95, 100], 
                                         labels=['A', 'B', 'C'])
            
            abc_results[f"{wh_name} ({city})"] = df
        
        return abc_results
    
    def generate_movement_recommendations(self, stock_data: Dict, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Генерация рекомендаций по перемещениям на основе оборачиваемости
        """
        recommendations = []
        
        # Анализируем товары с низкой оборачиваемостью по складам
        warehouse_items = defaultdict(list)
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            city = self.warehouse_cities.get(wh_name, 'Не указан')
            
            for item in warehouse['Остатки']:
                item_data = {
                    'warehouse': wh_name,
                    'city': city,
                    'article': item['Артикул'],
                    'name': item['Номенклатура'],
                    'category': item['ПутьКатегорий'],
                    'quantity': item['Количество'],
                    'cost': item['Стоимость'],
                    'avg_price': item['СредняяЦена']
                }
                warehouse_items[item['Артикул']].append(item_data)
        
        # Анализируем товары присутствующие на нескольких складах
        for article, locations in warehouse_items.items():
            if len(locations) > 1:
                # Находим продажи по артикулу
                sales_by_warehouse = defaultdict(float)
                
                if not sales_df.empty:
                    article_row = sales_df[sales_df['Артикул'] == article]
                    if not article_row.empty:
                        for wh_data in locations:
                            wh_name = wh_data['warehouse']
                            sales_columns = [col for col in sales_df.columns 
                                           if 'прод' in col.lower() and 'сумм' in col.lower()
                                           and any(part in col.lower() for part in wh_name.lower().split())]
                            
                            for col in sales_columns:
                                if pd.notna(article_row.iloc[0].get(col)):
                                    try:
                                        sales_by_warehouse[wh_name] += float(article_row.iloc[0][col])
                                    except:
                                        pass
                
                # Находим склады с высокими и низкими продажами
                total_stock = sum(loc['quantity'] for loc in locations)
                
                for loc in locations:
                    wh_sales = sales_by_warehouse.get(loc['warehouse'], 0)
                    
                    # Если на складе большой остаток но низкие продажи
                    if loc['quantity'] > total_stock * 0.3 and wh_sales < sum(sales_by_warehouse.values()) * 0.1:
                        # Ищем склад с высокими продажами но низким остатком
                        for target_loc in locations:
                            if target_loc['warehouse'] != loc['warehouse']:
                                target_sales = sales_by_warehouse.get(target_loc['warehouse'], 0)
                                
                                if (target_sales > sum(sales_by_warehouse.values()) * 0.3 and 
                                    target_loc['quantity'] < total_stock * 0.2):
                                    
                                    # Рекомендуем перемещение
                                    move_qty = min(
                                        loc['quantity'] * 0.3,  # Не более 30% остатка
                                        total_stock * 0.15      # Не более 15% общего остатка
                                    )
                                    
                                    recommendations.append({
                                        'Артикул': article,
                                        'Наименование': loc['name'],
                                        'Категория': loc['category'].split('/')[0],
                                        'Откуда': f"{loc['warehouse']} ({loc['city']})",
                                        'Куда': f"{target_loc['warehouse']} ({target_loc['city']})",
                                        'Количество к перемещению': int(move_qty),
                                        'Остаток на складе-источнике': loc['quantity'],
                                        'Остаток на складе-получателе': target_loc['quantity'],
                                        'Продажи источник': wh_sales,
                                        'Продажи получатель': target_sales,
                                        'Приоритет': 'Высокий' if target_sales > wh_sales * 3 else 'Средний'
                                    })
        
        df = pd.DataFrame(recommendations)
        if not df.empty:
            df = df.sort_values(['Приоритет', 'Продажи получатель'], ascending=[True, False])
        
        return df