#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для обработки Excel данных
Специализированный для работы с файлами системы Саната
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ExcelDataProcessor:
    """Класс для обработки Excel данных системы управления запасами"""
    
    def __init__(self):
        self.raw_data = {}
        self.processed_data = {}
        
    def load_excel_file(self, file_path: str) -> Dict:
        """Загрузка всех листов из Excel файла"""
        try:
            # Читаем все листы
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            self.raw_data = excel_data
            
            # Анализируем структуру
            structure_info = {}
            for sheet_name, df in excel_data.items():
                structure_info[sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': list(df.columns),
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
                }
            
            return structure_info
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки Excel файла: {str(e)}")
    
    def process_ads_data(self, sheet_name: str = None) -> pd.DataFrame:
        """Обработка данных ADS (среднедневные продажи)"""
        if not self.raw_data:
            raise Exception("Данные не загружены")
        
        # Автоматически находим лист с ADS данными
        if sheet_name is None:
            ads_sheets = [name for name in self.raw_data.keys() 
                         if 'ads' in name.lower()]
            if not ads_sheets:
                raise Exception("Не найден лист с ADS данными")
            sheet_name = ads_sheets[0]
        
        df = self.raw_data[sheet_name].copy()
        
        # Стандартизируем названия колонок
        df.columns = df.columns.str.strip().str.lower()
        
        # Ищем ключевые колонки
        column_mapping = self._identify_columns(df.columns)
        
        # Переименовываем колонки для стандартизации
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Очищаем данные
        df = self._clean_dataframe(df)
        
        self.processed_data['ads'] = df
        return df
    
    def process_stock_data(self, sheet_name: str = None) -> pd.DataFrame:
        """Обработка данных остатков"""
        if not self.raw_data:
            raise Exception("Данные не загружены")
        
        # Автоматически находим лист с остатками
        if sheet_name is None:
            stock_sheets = [name for name in self.raw_data.keys() 
                           if any(word in name.lower() for word in ['stock', 'balance', 'остат', 'склад'])]
            if not stock_sheets:
                raise Exception("Не найден лист с данными остатков")
            sheet_name = stock_sheets[0]
        
        df = self.raw_data[sheet_name].copy()
        df.columns = df.columns.str.strip().str.lower()
        
        # Обработка данных остатков
        df = self._clean_dataframe(df)
        
        self.processed_data['stock'] = df
        return df
    
    def process_min_target_data(self, sheet_name: str = None) -> pd.DataFrame:
        """Обработка данных min-target"""
        if not self.raw_data:
            raise Exception("Данные не загружены")
        
        # Автоматически находим лист с min-target данными
        if sheet_name is None:
            target_sheets = [name for name in self.raw_data.keys() 
                            if any(word in name.lower() for word in ['min', 'target', 'цел', 'миним'])]
            if not target_sheets:
                raise Exception("Не найден лист с min-target данными")
            sheet_name = target_sheets[0]
        
        df = self.raw_data[sheet_name].copy()
        df.columns = df.columns.str.strip().str.lower()
        
        df = self._clean_dataframe(df)
        
        self.processed_data['min_target'] = df
        return df
    
    def _identify_columns(self, columns: List[str]) -> Dict[str, str]:
        """Автоматическое определение типов колонок"""
        column_mapping = {}
        
        # Словарь для поиска колонок по ключевым словам
        column_patterns = {
            'sku': ['sku', 'код', 'артикул', 'id', 'номер'],
            'name': ['наименование', 'название', 'name', 'товар', 'продукт'],
            'category': ['категория', 'category', 'группа', 'group', 'класс'],
            'ads': ['ads', 'средн', 'продаж', 'sales', 'день'],
            'price': ['цена', 'price', 'стоимость', 'cost'],
            'stock': ['остаток', 'stock', 'количество', 'qty', 'balance'],
            'branch': ['филиал', 'branch', 'магазин', 'store', 'склад']
        }
        
        for col in columns:
            col_lower = col.lower()
            for standard_name, patterns in column_patterns.items():
                if any(pattern in col_lower for pattern in patterns):
                    column_mapping[col] = standard_name
                    break
        
        return column_mapping
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Очистка данных DataFrame"""
        # Удаляем полностью пустые строки и колонки
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Заполняем пропуски в числовых колонках нулями
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Заполняем пропуски в текстовых колонках
        text_columns = df.select_dtypes(include=['object']).columns
        df[text_columns] = df[text_columns].fillna('Unknown')
        
        return df
    
    def calculate_category_analysis(self) -> Dict:
        """Анализ категорий товаров"""
        if 'ads' not in self.processed_data:
            raise Exception("ADS данные не обработаны")
        
        df = self.processed_data['ads']
        
        # Проверяем наличие колонки категорий
        if 'category' not in df.columns:
            raise Exception("Не найдена колонка с категориями")
        
        # Подсчитываем статистику по категориям
        category_stats = {}
        total_items = len(df)
        
        category_groups = df.groupby('category').agg({
            'sku': 'count',
            'ads': ['sum', 'mean'],
            'price': 'mean' if 'price' in df.columns else lambda x: 0
        }).round(2)
        
        for category in category_groups.index:
            item_count = category_groups.loc[category, ('sku', 'count')]
            total_ads = category_groups.loc[category, ('ads', 'sum')]
            avg_ads = category_groups.loc[category, ('ads', 'mean')]
            
            category_stats[category] = {
                'item_count': item_count,
                'percentage': round((item_count / total_items) * 100, 2),
                'total_ads': total_ads,
                'avg_ads': avg_ads,
                'ads_percentage': round((total_ads / df['ads'].sum()) * 100, 2)
            }
        
        return category_stats
    
    def calculate_space_distribution(self, total_shelves: int, 
                                   category_stats: Dict) -> Dict:
        """Расчет распределения торгового пространства"""
        space_distribution = {}
        
        for category, stats in category_stats.items():
            # Распределяем полки пропорционально доле продаж (ADS)
            allocated_shelves = int((stats['ads_percentage'] / 100) * total_shelves)
            
            space_distribution[category] = {
                'shelves': allocated_shelves,
                'percentage': stats['ads_percentage'],
                'items_per_shelf': stats['item_count'] / max(allocated_shelves, 1)
            }
        
        return space_distribution
    
    def calculate_minimum_stock(self, days_supply: int = 10) -> pd.DataFrame:
        """Расчет неснижаемого товарного запаса"""
        if 'ads' not in self.processed_data:
            raise Exception("ADS данные не обработаны")
        
        df = self.processed_data['ads'].copy()
        
        # Расчет неснижаемого запаса
        df['min_stock'] = df['ads'] * days_supply
        df['days_supply'] = days_supply
        
        # Добавляем категории для группировки
        if 'category' in df.columns:
            df['category_min_stock'] = df.groupby('category')['min_stock'].transform('sum')
        
        return df
    
    def generate_order_list(self, min_stock_df: pd.DataFrame, 
                           safety_factor: float = 1.2) -> pd.DataFrame:
        """Генерация списка заказов"""
        # Получаем текущие остатки
        if 'stock' not in self.processed_data:
            # Если нет данных об остатках, генерируем заказы на основе минимального запаса
            orders = min_stock_df.copy()
            orders['current_stock'] = 0
            orders['order_quantity'] = orders['min_stock'] * safety_factor
        else:
            stock_df = self.processed_data['stock']
            
            # Объединяем данные о минимальных запасах и остатках
            if 'sku' in min_stock_df.columns and 'sku' in stock_df.columns:
                orders = pd.merge(min_stock_df, stock_df, on='sku', how='left', suffixes=('', '_stock'))
                orders['current_stock'] = orders.get('stock', 0)
            else:
                orders = min_stock_df.copy()
                orders['current_stock'] = 0
        
        # Расчет количества для заказа
        orders['stock_deficit'] = orders['min_stock'] - orders['current_stock']
        orders['order_quantity'] = orders['stock_deficit'].apply(lambda x: max(0, x * safety_factor))
        
        # Фильтруем только позиции, которые нужно заказать
        orders = orders[orders['order_quantity'] > 0].copy()
        
        # Добавляем расчет стоимости заказа
        if 'price' in orders.columns:
            orders['order_value'] = orders['order_quantity'] * orders['price']
        else:
            orders['order_value'] = 0
        
        # Сортируем по категориям и важности
        if 'category' in orders.columns:
            orders = orders.sort_values(['category', 'order_quantity'], ascending=[True, False])
        
        return orders
    
    def apply_package_multiples(self, orders_df: pd.DataFrame, 
                               package_multiples: Dict = None) -> pd.DataFrame:
        """Применение кратности упаковки"""
        if package_multiples is None:
            # Если не указаны кратности, используем стандартные значения
            package_multiples = {}
        
        orders = orders_df.copy()
        
        def round_to_multiple(quantity, multiple):
            if multiple <= 1:
                return quantity
            return int(np.ceil(quantity / multiple) * multiple)
        
        # Применяем кратность упаковки
        for index, row in orders.iterrows():
            sku = row.get('sku', '')
            multiple = package_multiples.get(sku, 1)  # По умолчанию кратность 1
            
            original_qty = row['order_quantity']
            rounded_qty = round_to_multiple(original_qty, multiple)
            
            orders.at[index, 'order_quantity'] = rounded_qty
            orders.at[index, 'package_multiple'] = multiple
            
            # Пересчитываем стоимость
            if 'price' in orders.columns:
                orders.at[index, 'order_value'] = rounded_qty * row.get('price', 0)
        
        return orders
    
    def export_results(self, orders_df: pd.DataFrame, 
                      category_stats: Dict = None,
                      space_distribution: Dict = None) -> Dict:
        """Подготовка данных для экспорта"""
        export_data = {
            'orders': orders_df,
            'summary': {
                'total_positions': len(orders_df),
                'total_quantity': orders_df['order_quantity'].sum(),
                'total_value': orders_df['order_value'].sum() if 'order_value' in orders_df.columns else 0
            }
        }
        
        if category_stats:
            export_data['category_analysis'] = pd.DataFrame.from_dict(category_stats, orient='index')
        
        if space_distribution:
            export_data['space_distribution'] = pd.DataFrame.from_dict(space_distribution, orient='index')
        
        return export_data
    
    def get_processing_summary(self) -> Dict:
        """Получение сводки по обработанным данным"""
        summary = {
            'loaded_sheets': list(self.raw_data.keys()),
            'processed_datasets': list(self.processed_data.keys()),
            'data_quality': {}
        }
        
        for dataset_name, df in self.processed_data.items():
            summary['data_quality'][dataset_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'missing_values': df.isnull().sum().sum(),
                'data_types': df.dtypes.to_dict()
            }
        
        return summary