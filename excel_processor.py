#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для обработки Excel данных системы Саната
Адаптированный под реальную структуру файлов с филиалами
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ExcelDataProcessor:
    """Класс для обработки Excel данных системы управления запасами с филиалами"""
    
    def __init__(self):
        self.raw_data = {}
        self.processed_data = {}
        self.branches = ['казыбаева', 'барыс', 'астана', 'шымкент']  # Основные филиалы
        
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
                    'column_names': [str(col) for col in df.columns],
                    'sheet_type': self._identify_sheet_type(sheet_name),
                    'sample_data': df.head(2).to_dict('records') if len(df) > 0 else []
                }
            
            return structure_info
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки Excel файла: {str(e)}")
    
    def _identify_sheet_type(self, sheet_name: str) -> str:
        """Определение типа листа по названию"""
        sheet_name_lower = sheet_name.lower()
        
        if 'адс' in sheet_name_lower or 'ads' in sheet_name_lower:
            return 'ads'
        elif 'ост' in sheet_name_lower or 'остат' in sheet_name_lower:
            return 'stock'
        elif 'мин' in sheet_name_lower and 'запас' in sheet_name_lower:
            return 'min_stock_main'  # Основной лист с логикой
        elif 'orderlist' in sheet_name_lower or 'заказ' in sheet_name_lower:
            return 'orders'
        elif 'покрытие' in sheet_name_lower or 'категор' in sheet_name_lower:
            return 'categories'
        elif any(branch in sheet_name_lower for branch in self.branches):
            return 'branch_data'
        else:
            return 'unknown'
    
    def process_main_data(self, sheet_name: str = 'мин запасы') -> pd.DataFrame:
        """Обработка основного листа с минимальными запасами - содержит всю логику"""
        if sheet_name not in self.raw_data:
            raise Exception(f"Лист '{sheet_name}' не найден")
        
        df = self.raw_data[sheet_name].copy()
        
        # Пропускаем первые строки с заголовками и берем данные с 3-й строки
        df = df.iloc[2:].copy()  # Строки 3+ содержат данные
        df = df.reset_index(drop=True)
        
        # Создаем правильные названия колонок на основе структуры
        column_names = [
            'name',           # A: Наименование товара
            'check',          # B: Проверка (1/0)
            'active',         # C: Активный/нет
            'category',       # D: Категория
            'subcategory',    # E: Подкатегория
            'duplicates',     # F: Дубли
            'ads_kaz',        # G: ADS казыбаева
            'ads_bar',        # H: ADS барыс
            'ads_ast',        # I: ADS астана
            'ads_shy',        # J: ADS шымкент
            'days_target',    # K: Дни запаса (таргет)
            'min_kaz',        # L: Мин запас казыбаева
            'min_bar',        # M: Мин запас барыс
            'min_ast',        # N: Мин запас астана
            'min_shy',        # O: Мин запас шымкент
            'stock_kaz',      # P: Остатки казыбаева
            'stock_bar',      # Q: Остатки барыс
            'stock_ast',      # R: Остатки астана
            'stock_shy',      # S: Остатки шымкент
            'other_stock'     # T: Комплект и др.
        ]
        
        # Применяем названия колонок (добираем до нужного количества)
        if len(df.columns) >= len(column_names):
            df.columns = column_names + [f'col_{i}' for i in range(len(column_names), len(df.columns))]
        else:
            df.columns = column_names[:len(df.columns)]
        
        # Очищаем данные
        df = self._clean_main_dataframe(df)
        
        # Убираем строки без наименования товара
        df = df.dropna(subset=['name'])
        df = df[df['name'].astype(str).str.strip() != '']
        
        self.processed_data['main'] = df
        return df
    
    def _clean_main_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Специальная очистка основного DataFrame"""
        # Заполняем пропуски
        numeric_cols = ['ads_kaz', 'ads_bar', 'ads_ast', 'ads_shy', 'days_target',
                       'min_kaz', 'min_bar', 'min_ast', 'min_shy',
                       'stock_kaz', 'stock_bar', 'stock_ast', 'stock_shy']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Очищаем текстовые поля
        text_cols = ['name', 'category', 'subcategory', 'active']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'None', ''], np.nan)
        
        return df
    
    def calculate_category_analysis(self) -> Dict:
        """Анализ категорий товаров на основе основного листа"""
        if 'main' not in self.processed_data:
            raise Exception("Основные данные не обработаны")
        
        df = self.processed_data['main']
        
        if 'category' not in df.columns:
            raise Exception("Не найдена колонка с категориями")
        
        # Считаем общие ADS по всем филиалам
        ads_cols = ['ads_kaz', 'ads_bar', 'ads_ast', 'ads_shy']
        df['total_ads'] = df[ads_cols].sum(axis=1)
        
        # Статистика по категориям
        category_stats = {}
        total_items = len(df[df['category'].notna()])
        total_ads = df['total_ads'].sum()
        
        for category in df['category'].dropna().unique():
            if str(category).strip() == '':
                continue
                
            category_df = df[df['category'] == category]
            item_count = len(category_df)
            category_ads = category_df['total_ads'].sum()
            avg_ads = category_df['total_ads'].mean()
            
            category_stats[str(category)] = {
                'item_count': item_count,
                'percentage': round((item_count / total_items) * 100, 2) if total_items > 0 else 0,
                'total_ads': round(category_ads, 2),
                'avg_ads': round(avg_ads, 2),
                'ads_percentage': round((category_ads / total_ads) * 100, 2) if total_ads > 0 else 0
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
                'items_per_shelf': round(stats['item_count'] / max(allocated_shelves, 1), 2)
            }
        
        return space_distribution
    
    def calculate_minimum_stock_by_branch(self, days_supply: int = None) -> pd.DataFrame:
        """Расчет неснижаемого товарного запаса по филиалам"""
        if 'main' not in self.processed_data:
            raise Exception("Основные данные не обработаны")
        
        df = self.processed_data['main'].copy()
        
        # Используем значение days_target из файла или переданное значение
        if days_supply is not None:
            df['days_supply'] = days_supply
        else:
            df['days_supply'] = df['days_target'].fillna(10)
        
        # Рассчитываем минимальные запасы для каждого филиала
        for branch in self.branches:
            ads_col = f'ads_{branch[:3]}'  # ads_kaz, ads_bar, etc.
            min_col = f'min_stock_{branch}'
            
            if ads_col in df.columns:
                df[min_col] = df[ads_col] * df['days_supply']
        
        # Общий минимальный запас
        min_cols = [f'min_stock_{branch}' for branch in self.branches]
        existing_min_cols = [col for col in min_cols if col in df.columns]
        df['total_min_stock'] = df[existing_min_cols].sum(axis=1)
        
        # Общий ADS
        ads_cols = [f'ads_{branch[:3]}' for branch in self.branches]
        existing_ads_cols = [col for col in ads_cols if col in df.columns]
        df['total_ads'] = df[existing_ads_cols].sum(axis=1)
        
        return df
    
    def generate_orders_by_branch(self, min_stock_df: pd.DataFrame, 
                                 safety_factor: float = 1.2) -> pd.DataFrame:
        """Генерация заказов по филиалам на основе логики Саната"""
        
        orders_list = []
        
        for index, row in min_stock_df.iterrows():
            try:
                name = str(row.get('name', '')).strip()
                if not name or name == 'nan':
                    continue
                
                category = str(row.get('category', 'Unknown')).strip()
                
                # Обрабатываем каждый филиал отдельно
                for branch in self.branches:
                    branch_short = branch[:3]  # kaz, bar, ast, shy
                    
                    ads_col = f'ads_{branch_short}'
                    min_stock_col = f'min_stock_{branch}'
                    stock_col = f'stock_{branch_short}'
                    
                    # Получаем данные для филиала
                    ads_value = row.get(ads_col, 0) or 0
                    min_stock = row.get(min_stock_col, 0) or 0
                    current_stock = row.get(stock_col, 0) or 0
                    
                    # Если нет min_stock, рассчитываем на основе ADS
                    if min_stock == 0 and ads_value > 0:
                        days_supply = row.get('days_supply', 30)
                        min_stock = ads_value * days_supply
                    
                    # Логика формирования заказа
                    stock_deficit = max(0, min_stock - current_stock)
                    
                    if stock_deficit > 0:
                        order_quantity = stock_deficit * safety_factor
                        
                        orders_list.append({
                            'name': name,
                            'category': category,
                            'branch': branch,
                            'ads': ads_value,
                            'min_stock': min_stock,
                            'current_stock': current_stock,
                            'stock_deficit': stock_deficit,
                            'order_quantity': round(order_quantity, 2),
                            'days_supply': row.get('days_supply', 30)
                        })
                        
            except Exception as e:
                # Пропускаем проблемные строки
                continue
        
        orders_df = pd.DataFrame(orders_list)
        
        # Сортируем по филиалам, категориям и количеству заказа
        if not orders_df.empty:
            orders_df = orders_df.sort_values(['branch', 'category', 'order_quantity'], 
                                            ascending=[True, True, False])
        
        return orders_df
    
    def get_branch_summary(self, orders_df: pd.DataFrame) -> Dict:
        """Получение сводки по филиалам"""
        if orders_df.empty:
            return {}
        
        branch_summary = {}
        
        for branch in orders_df['branch'].unique():
            branch_orders = orders_df[orders_df['branch'] == branch]
            
            branch_summary[branch] = {
                'total_positions': len(branch_orders),
                'total_quantity': round(branch_orders['order_quantity'].sum(), 2),
                'categories_count': branch_orders['category'].nunique(),
                'avg_order_size': round(branch_orders['order_quantity'].mean(), 2),
                'total_deficit': round(branch_orders['stock_deficit'].sum(), 2)
            }
        
        return branch_summary
    
    def apply_package_multiples(self, orders_df: pd.DataFrame, 
                               package_multiples: Dict = None) -> pd.DataFrame:
        """Применение кратности упаковки"""
        if package_multiples is None or orders_df.empty:
            return orders_df
        
        orders = orders_df.copy()
        
        def round_to_multiple(quantity, multiple):
            if multiple <= 1:
                return quantity
            return int(np.ceil(quantity / multiple) * multiple)
        
        # Применяем кратность упаковки
        for index, row in orders.iterrows():
            name = row.get('name', '')
            multiple = package_multiples.get(name, 1)
            
            original_qty = row['order_quantity']
            rounded_qty = round_to_multiple(original_qty, multiple)
            
            orders.at[index, 'order_quantity'] = rounded_qty
            orders.at[index, 'package_multiple'] = multiple
        
        return orders
    
    def export_results_by_branch(self, orders_df: pd.DataFrame, 
                                category_stats: Dict = None,
                                space_distribution: Dict = None,
                                branch_summary: Dict = None) -> Dict:
        """Подготовка данных для экспорта с разбивкой по филиалам"""
        
        export_data = {
            'orders_all': orders_df,
            'summary': {
                'total_positions': len(orders_df),
                'total_quantity': round(orders_df['order_quantity'].sum(), 2) if not orders_df.empty else 0,
                'branches_count': orders_df['branch'].nunique() if not orders_df.empty else 0,
                'categories_count': orders_df['category'].nunique() if not orders_df.empty else 0
            }
        }
        
        # Создаем отдельные листы для каждого филиала
        if not orders_df.empty:
            for branch in orders_df['branch'].unique():
                branch_orders = orders_df[orders_df['branch'] == branch]
                export_data[f'orders_{branch}'] = branch_orders
        
        # Добавляем анализы
        if category_stats:
            export_data['category_analysis'] = pd.DataFrame.from_dict(category_stats, orient='index')
        
        if space_distribution:
            export_data['space_distribution'] = pd.DataFrame.from_dict(space_distribution, orient='index')
        
        if branch_summary:
            export_data['branch_summary'] = pd.DataFrame.from_dict(branch_summary, orient='index')
        
        return export_data
    
    def get_processing_summary(self) -> Dict:
        """Получение сводки по обработанным данным"""
        summary = {
            'loaded_sheets': list(self.raw_data.keys()),
            'processed_datasets': list(self.processed_data.keys()),
            'branches': self.branches,
            'data_quality': {}
        }
        
        # Качество данных
        for dataset_name, df in self.processed_data.items():
            summary['data_quality'][dataset_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'missing_values': int(df.isnull().sum().sum()),
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                'text_columns': len(df.select_dtypes(include=['object']).columns)
            }
            
            # Специальная статистика для основного листа
            if dataset_name == 'main':
                ads_cols = [col for col in df.columns if 'ads_' in col]
                stock_cols = [col for col in df.columns if 'stock_' in col]
                
                summary['data_quality'][dataset_name].update({
                    'items_with_ads': len(df[df[ads_cols].sum(axis=1) > 0]),
                    'items_with_stock': len(df[df[stock_cols].sum(axis=1) > 0]),
                    'categories_count': df['category'].nunique() if 'category' in df.columns else 0
                })
        
        return summary