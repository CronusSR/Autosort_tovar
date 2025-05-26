#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный модуль для обработки Excel данных системы Саната
С поддержкой ABC анализа и полной логики из детализации.txt
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ExcelDataProcessorV2:
    """Обновленный класс для обработки Excel данных с ABC анализом"""
    
    def __init__(self):
        self.raw_data = {}
        self.processed_data = {}
        self.branches = ['казыбаева', 'барыс', 'астана', 'шымкент']
        self.abc_data = None
        
    def load_excel_file(self, file_path: str) -> Dict:
        """Загрузка всех листов из Excel файла"""
        try:
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            self.raw_data = excel_data
            
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
        elif 'ост' in sheet_name_lower:
            return 'stock'
        elif 'мин' in sheet_name_lower and 'запас' in sheet_name_lower:
            return 'min_stock_main'
        elif 'покрытие' in sheet_name_lower and 'категор' in sheet_name_lower:
            return 'category_coverage'
        elif any(branch in sheet_name_lower for branch in self.branches):
            return 'branch_data'
        else:
            return 'unknown'
    
    def process_main_data(self, sheet_name: str = 'мин запасы') -> pd.DataFrame:
        """Обработка основного листа согласно детализации"""
        if sheet_name not in self.raw_data:
            raise Exception(f"Лист '{sheet_name}' не найден")
        
        df = self.raw_data[sheet_name].copy()
        
        # Пропускаем заголовки и берем данные с 3-й строки
        df = df.iloc[2:].copy()
        df = df.reset_index(drop=True)
        
        # Создаем правильные названия колонок согласно детализации
        column_names = [
            'nomenclature',           # A: Номенклатура - название товара
            'check',                  # B: 1/0 проверка  
            'active_assortment',      # C: Ассортимент активный или нет (YES/NO)
            'category',               # D: Группа - категория товаров
            'subcategory',            # E: Подкатегория
            'duplicates',             # F: Дубли
            'ads_kaz',               # G: ADS казыбаева
            'ads_bar',               # H: ADS барыс  
            'ads_ast',               # I: ADS астана
            'ads_shy',               # J: ADS шымкент
            'days_target',           # K: дни запаса - количество дней по плану
            'min_kaz',               # L: MIN казыбаева - минимальное количество
            'min_bar',               # M: MIN барыс
            'min_ast',               # N: MIN астана  
            'min_shy',               # O: MIN шымкент
            'stock_kaz',             # P: фактические остатки казыбаева
            'stock_bar',             # Q: фактические остатки барыс
            'stock_ast',             # R: фактические остатки астана
            'stock_shy',             # S: фактические остатки шымкент
            'other_stock'            # T: Комплект и др.
        ]
        
        # Применяем названия колонок
        if len(df.columns) >= len(column_names):
            df.columns = column_names + [f'col_{i}' for i in range(len(column_names), len(df.columns))]
        else:
            df.columns = column_names[:len(df.columns)]
        
        # Очищаем данные
        df = self._clean_main_dataframe(df)
        
        # Убираем строки без номенклатуры
        df = df.dropna(subset=['nomenclature'])
        df = df[df['nomenclature'].astype(str).str.strip() != '']
        
        # Добавляем расчетные поля согласно детализации
        df = self._add_calculated_fields(df)
        
        self.processed_data['main'] = df
        return df
    
    def _clean_main_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Очистка основного DataFrame"""
        # Заполняем пропуски
        numeric_cols = ['ads_kaz', 'ads_bar', 'ads_ast', 'ads_shy', 'days_target',
                       'min_kaz', 'min_bar', 'min_ast', 'min_shy',
                       'stock_kaz', 'stock_bar', 'stock_ast', 'stock_shy']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Очищаем текстовые поля
        text_cols = ['nomenclature', 'category', 'subcategory', 'active_assortment']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'None', ''], np.nan)
        
        return df
    
    def _add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавление расчетных полей согласно детализации"""
        
        # Общий ADS по всем филиалам
        ads_cols = ['ads_kaz', 'ads_bar', 'ads_ast', 'ads_shy']
        df['total_ads'] = df[ads_cols].sum(axis=1)
        
        # Общие остатки  
        stock_cols = ['stock_kaz', 'stock_bar', 'stock_ast', 'stock_shy']
        df['total_current_stock'] = df[stock_cols].sum(axis=1)
        
        # Общий минимальный запас
        min_cols = ['min_kaz', 'min_bar', 'min_ast', 'min_shy']
        df['total_min_stock'] = df[min_cols].sum(axis=1)
        
        # Товарный запас в днях для каждого филиала
        for branch in ['kaz', 'bar', 'ast', 'shy']:
            ads_col = f'ads_{branch}'
            stock_col = f'stock_{branch}'
            days_col = f'stock_days_{branch}'
            
            # Товарный запас = фактическое количество / среднедневная продажа
            df[days_col] = np.where(
                df[ads_col] > 0,
                df[stock_col] / df[ads_col],
                0
            )
        
        return df
    
    def load_abc_analysis_data(self, file_path: str) -> pd.DataFrame:
        """Загрузка данных для ABC анализа из исходников мини"""
        try:
            # Читаем файл ABC анализа
            abc_df = pd.read_excel(file_path, sheet_name='Лист1', engine='openpyxl')
            
            # Пропускаем заголовки и берем данные
            abc_df = abc_df.iloc[5:].copy()  # Данные начинаются с 6-й строки
            abc_df = abc_df.reset_index(drop=True)
            
            # Устанавливаем правильные названия колонок
            abc_df.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales']
            
            # Очищаем данные
            abc_df = abc_df.dropna(subset=['nomenclature'])
            abc_df = abc_df[abc_df['nomenclature'].astype(str).str.strip() != '']
            
            # Преобразуем объемы продаж в числовой формат
            abc_df['annual_sales'] = pd.to_numeric(abc_df['annual_sales'], errors='coerce').fillna(0)
            
            # Убираем строки с нулевыми продажами
            abc_df = abc_df[abc_df['annual_sales'] > 0]
            
            self.abc_data = abc_df
            return abc_df
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки ABC данных: {str(e)}")
    
    def calculate_abc_analysis(self) -> Dict:
        """Выполнение ABC анализа по категориям"""
        if self.abc_data is None:
            raise Exception("ABC данные не загружены")
        
        abc_results = {}
        
        # Сортируем по объему продаж
        sorted_data = self.abc_data.sort_values('annual_sales', ascending=False)
        
        # Рассчитываем накопительные проценты
        total_sales = sorted_data['annual_sales'].sum()
        sorted_data['sales_percentage'] = (sorted_data['annual_sales'] / total_sales) * 100
        sorted_data['cumulative_percentage'] = sorted_data['sales_percentage'].cumsum()
        
        # Присваиваем ABC классы
        def assign_abc_class(cumulative_pct):
            if cumulative_pct <= 80:
                return 'A'
            elif cumulative_pct <= 95:
                return 'B'
            else:
                return 'C'
        
        sorted_data['abc_class'] = sorted_data['cumulative_percentage'].apply(assign_abc_class)
        
        # Анализ по категориям
        for category in sorted_data['category'].unique():
            if pd.isna(category):
                continue
                
            category_data = sorted_data[sorted_data['category'] == category]
            
            abc_results[str(category)] = {
                'total_items': len(category_data),
                'total_sales': category_data['annual_sales'].sum(),
                'sales_percentage': (category_data['annual_sales'].sum() / total_sales) * 100,
                'abc_distribution': {
                    'A': len(category_data[category_data['abc_class'] == 'A']),
                    'B': len(category_data[category_data['abc_class'] == 'B']),
                    'C': len(category_data[category_data['abc_class'] == 'C'])
                },
                'top_items': category_data.head(5)[['nomenclature', 'annual_sales', 'abc_class']].to_dict('records')
            }
        
        # Сохраняем обогащенные данные
        self.processed_data['abc_analysis'] = sorted_data
        
        return abc_results
    
    def calculate_branch_orders_with_logic(self, safety_factor: float = 1.2, 
                                         transit_time_days: int = 7) -> pd.DataFrame:
        """Формирование заказов согласно полной логике из детализации"""
        if 'main' not in self.processed_data:
            raise Exception("Основные данные не обработаны")
        
        df = self.processed_data['main'].copy()
        orders_list = []
        
        for index, row in df.iterrows():
            try:
                nomenclature = str(row.get('nomenclature', '')).strip()
                if not nomenclature or nomenclature == 'nan':
                    continue
                
                # Проверяем активность ассортимента
                active = str(row.get('active_assortment', '')).upper()
                if active == 'NO':
                    continue  # Пропускаем неактивные товары
                
                category = str(row.get('category', 'Unknown')).strip()
                
                # Обрабатываем каждый филиал
                for branch in self.branches:
                    branch_short = branch[:3]  # kaz, bar, ast, shy
                    
                    ads_col = f'ads_{branch_short}'
                    stock_col = f'stock_{branch_short}'
                    min_col = f'min_{branch_short}'
                    
                    ads_value = row.get(ads_col, 0) or 0
                    current_stock = row.get(stock_col, 0) or 0
                    min_stock = row.get(min_col, 0) or 0
                    days_supply = row.get('days_target', 30) or 30
                    
                    # Если нет ADS, пропускаем
                    if ads_value <= 0:
                        continue
                    
                    # Рассчитываем чистую потребность (сколько продастся пока товар едет)
                    transit_consumption = ads_value * transit_time_days
                    
                    # Товарный запас в днях
                    stock_days = current_stock / ads_value if ads_value > 0 else 0
                    
                    # Потребность = MIN - текущие остатки + чистая потребность
                    need = max(0, min_stock - current_stock + transit_consumption)
                    
                    # Предзаказ с коэффициентом безопасности
                    pre_order = need * safety_factor if need > 0 else 0
                    
                    if pre_order > 0:
                        orders_list.append({
                            'nomenclature': nomenclature,
                            'category': category,
                            'branch': branch,
                            'ads': ads_value,
                            'min_stock': min_stock,
                            'current_stock': current_stock,
                            'stock_days': round(stock_days, 2),
                            'transit_consumption': round(transit_consumption, 2),
                            'need': round(need, 2),
                            'pre_order': round(pre_order, 2),
                            'days_supply': days_supply,
                            'active_assortment': active,
                            'transit_time': transit_time_days
                        })
                        
            except Exception as e:
                print(f"Ошибка обработки строки {index}: {str(e)}")
                continue
        
        orders_df = pd.DataFrame(orders_list)
        
        if not orders_df.empty:
            orders_df = orders_df.sort_values(['branch', 'category', 'pre_order'], 
                                            ascending=[True, True, False])
        
        return orders_df
    
    def enrich_orders_with_abc(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Обогащение заказов данными ABC анализа"""
        if self.abc_data is None or orders_df.empty:
            return orders_df
        
        # Создаем словарь ABC классов
        abc_dict = {}
        if 'abc_analysis' in self.processed_data:
            abc_data = self.processed_data['abc_analysis']
            for _, row in abc_data.iterrows():
                abc_dict[row['nomenclature']] = {
                    'abc_class': row['abc_class'],
                    'annual_sales': row['annual_sales'],
                    'sales_percentage': row['sales_percentage']
                }
        
        # Добавляем ABC информацию к заказам
        orders_enriched = orders_df.copy()
        
        abc_classes = []
        annual_sales = []
        sales_percentages = []
        
        for nomenclature in orders_enriched['nomenclature']:
            abc_info = abc_dict.get(nomenclature, {})
            abc_classes.append(abc_info.get('abc_class', 'Unknown'))
            annual_sales.append(abc_info.get('annual_sales', 0))
            sales_percentages.append(abc_info.get('sales_percentage', 0))
        
        orders_enriched['abc_class'] = abc_classes
        orders_enriched['annual_sales'] = annual_sales
        orders_enriched['sales_percentage'] = sales_percentages
        
        return orders_enriched
    
    def get_category_analysis_with_abc(self) -> Dict:
        """Анализ категорий с учетом ABC классификации"""
        if 'main' not in self.processed_data:
            raise Exception("Основные данные не обработаны")
        
        df = self.processed_data['main']
        category_stats = {}
        
        # Общие показатели
        total_items = len(df[df['category'].notna()])
        total_ads = df['total_ads'].sum()
        
        # Словарь ABC классов
        abc_dict = {}
        if 'abc_analysis' in self.processed_data:
            abc_data = self.processed_data['abc_analysis']
            for _, row in abc_data.iterrows():
                abc_dict[row['nomenclature']] = row['abc_class']
        
        for category in df['category'].dropna().unique():
            if str(category).strip() == '':
                continue
                
            category_df = df[df['category'] == category]
            item_count = len(category_df)
            category_ads = category_df['total_ads'].sum()
            avg_ads = category_df['total_ads'].mean()
            
            # ABC распределение в категории
            abc_distribution = {'A': 0, 'B': 0, 'C': 0, 'Unknown': 0}
            for nomenclature in category_df['nomenclature']:
                abc_class = abc_dict.get(nomenclature, 'Unknown')
                abc_distribution[abc_class] += 1
            
            category_stats[str(category)] = {
                'item_count': item_count,
                'percentage': round((item_count / total_items) * 100, 2) if total_items > 0 else 0,
                'total_ads': round(category_ads, 2),
                'avg_ads': round(avg_ads, 2),
                'ads_percentage': round((category_ads / total_ads) * 100, 2) if total_ads > 0 else 0,
                'abc_distribution': abc_distribution,
                'abc_percentage': {
                    'A': round((abc_distribution['A'] / item_count) * 100, 1) if item_count > 0 else 0,
                    'B': round((abc_distribution['B'] / item_count) * 100, 1) if item_count > 0 else 0,
                    'C': round((abc_distribution['C'] / item_count) * 100, 1) if item_count > 0 else 0
                }
            }
        
        return category_stats
    
    def calculate_space_distribution_with_abc(self, total_shelves: int, 
                                            category_stats: Dict) -> Dict:
        """Расчет распределения пространства с учетом ABC анализа"""
        space_distribution = {}
        
        for category, stats in category_stats.items():
            # Базовое распределение по ADS
            base_shelves = int((stats['ads_percentage'] / 100) * total_shelves)
            
            # Корректировка по ABC классам (A товары получают больше места)
            abc_dist = stats['abc_distribution']
            total_items = stats['item_count']
            
            if total_items > 0:
                # Коэффициент важности категории (больше A товаров = больше места)
                abc_weight = (abc_dist['A'] * 1.5 + abc_dist['B'] * 1.0 + abc_dist['C'] * 0.7) / total_items
                adjusted_shelves = int(base_shelves * abc_weight)
            else:
                adjusted_shelves = base_shelves
            
            space_distribution[category] = {
                'base_shelves': base_shelves,
                'adjusted_shelves': adjusted_shelves,
                'abc_weight': round(abc_weight, 2) if total_items > 0 else 1.0,
                'percentage': stats['ads_percentage'],
                'items_per_shelf': round(stats['item_count'] / max(adjusted_shelves, 1), 2),
                'abc_distribution': abc_dist
            }
        
        return space_distribution
    
    def generate_branch_summary_with_abc(self, orders_df: pd.DataFrame) -> Dict:
        """Сводка по филиалам с ABC анализом"""
        if orders_df.empty:
            return {}
        
        branch_summary = {}
        
        for branch in orders_df['branch'].unique():
            branch_orders = orders_df[orders_df['branch'] == branch]
            
            # Базовая статистика
            total_positions = len(branch_orders)
            total_quantity = branch_orders['pre_order'].sum()
            
            # ABC статистика
            abc_stats = {'A': 0, 'B': 0, 'C': 0, 'Unknown': 0}
            abc_values = {'A': 0, 'B': 0, 'C': 0, 'Unknown': 0}
            
            for _, order in branch_orders.iterrows():
                abc_class = order.get('abc_class', 'Unknown')
                abc_stats[abc_class] += 1
                abc_values[abc_class] += order['pre_order']
            
            branch_summary[branch] = {
                'total_positions': total_positions,
                'total_quantity': round(total_quantity, 2),
                'categories_count': branch_orders['category'].nunique(),
                'avg_order_size': round(branch_orders['pre_order'].mean(), 2),
                'total_need': round(branch_orders['need'].sum(), 2),
                'abc_positions': abc_stats,
                'abc_quantities': {k: round(v, 2) for k, v in abc_values.items()},
                'abc_percentages': {
                    k: round((v / total_positions) * 100, 1) if total_positions > 0 else 0 
                    for k, v in abc_stats.items()
                }
            }
        
        return branch_summary
    
    def export_enhanced_results(self, orders_df: pd.DataFrame, 
                              category_stats: Dict = None,
                              space_distribution: Dict = None,
                              branch_summary: Dict = None,
                              abc_results: Dict = None) -> Dict:
        """Экспорт результатов с расширенной аналитикой"""
        
        export_data = {
            'orders_all': orders_df,
            'summary': {
                'total_positions': len(orders_df),
                'total_quantity': round(orders_df['pre_order'].sum(), 2) if not orders_df.empty else 0,
                'branches_count': orders_df['branch'].nunique() if not orders_df.empty else 0,
                'categories_count': orders_df['category'].nunique() if not orders_df.empty else 0,
                'abc_distribution': {}
            }
        }
        
        # ABC распределение в заказах
        if not orders_df.empty and 'abc_class' in orders_df.columns:
            abc_dist = orders_df['abc_class'].value_counts().to_dict()
            export_data['summary']['abc_distribution'] = abc_dist
        
        # Заказы по филиалам
        if not orders_df.empty:
            for branch in orders_df['branch'].unique():
                branch_orders = orders_df[orders_df['branch'] == branch]
                export_data[f'orders_{branch}'] = branch_orders
        
        # Аналитические данные
        if category_stats:
            export_data['category_analysis'] = pd.DataFrame.from_dict(category_stats, orient='index')
        
        if space_distribution:
            export_data['space_distribution'] = pd.DataFrame.from_dict(space_distribution, orient='index')
        
        if branch_summary:
            export_data['branch_summary'] = pd.DataFrame.from_dict(branch_summary, orient='index')
        
        if abc_results:
            export_data['abc_analysis'] = pd.DataFrame.from_dict(abc_results, orient='index')
        
        # ABC детали
        if 'abc_analysis' in self.processed_data:
            export_data['abc_details'] = self.processed_data['abc_analysis']
        
        return export_data
    
    def validate_data_quality(self) -> Dict:
        """Валидация качества данных"""
        quality_report = {
            'main_data': {},
            'abc_data': {},
            'issues': [],
            'recommendations': []
        }
        
        # Проверка основных данных
        if 'main' in self.processed_data:
            main_df = self.processed_data['main']
            
            quality_report['main_data'] = {
                'total_items': len(main_df),
                'items_with_ads': len(main_df[main_df['total_ads'] > 0]),
                'items_with_stock': len(main_df[main_df['total_current_stock'] > 0]),
                'active_items': len(main_df[main_df['active_assortment'].str.upper() == 'YES']),
                'categories_count': main_df['category'].nunique(),
                'missing_categories': len(main_df[main_df['category'].isna()])
            }
            
            # Проверяем проблемы
            if quality_report['main_data']['missing_categories'] > 0:
                quality_report['issues'].append(
                    f"Найдено {quality_report['main_data']['missing_categories']} товаров без категории"
                )
            
            ads_coverage = (quality_report['main_data']['items_with_ads'] / 
                          quality_report['main_data']['total_items']) * 100
            if ads_coverage < 50:
                quality_report['issues'].append(
                    f"Низкое покрытие ADS данными: {ads_coverage:.1f}%"
                )
        
        # Проверка ABC данных
        if self.abc_data is not None:
            quality_report['abc_data'] = {
                'total_items': len(self.abc_data),
                'items_with_sales': len(self.abc_data[self.abc_data['annual_sales'] > 0]),
                'categories_count': self.abc_data['category'].nunique()
            }
            
            # Соответствие между основными данными и ABC
            if 'main' in self.processed_data:
                main_items = set(self.processed_data['main']['nomenclature'].dropna())
                abc_items = set(self.abc_data['nomenclature'].dropna())
                
                overlap = len(main_items & abc_items)
                total_main = len(main_items)
                
                coverage = (overlap / total_main) * 100 if total_main > 0 else 0
                quality_report['abc_coverage'] = round(coverage, 1)
                
                if coverage < 70:
                    quality_report['issues'].append(
                        f"Низкое покрытие ABC анализом: {coverage:.1f}%"
                    )
        
        # Рекомендации
        if len(quality_report['issues']) == 0:
            quality_report['recommendations'].append("Качество данных хорошее")
        else:
            quality_report['recommendations'].extend([
                "Проверьте правильность названий товаров",
                "Убедитесь в полноте ADS данных",
                "Заполните отсутствующие категории"
            ])
        
        return quality_report
    
    def get_processing_summary(self) -> Dict:
        """Получение сводки по обработанным данным"""
        summary = {
            'loaded_sheets': list(self.raw_data.keys()),
            'processed_datasets': list(self.processed_data.keys()),
            'branches': self.branches,
            'data_quality': self.validate_data_quality(),
            'abc_loaded': self.abc_data is not None
        }
        
        return summary