#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульный обработчик данных для системы анализа товарных запасов v3.0
Поддерживает пошаговый анализ с выбором типа операции
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
import plotly.express as px
import plotly.graph_objects as go
warnings.filterwarnings('ignore')

class ModularInventorySystem:
    """Модульная система анализа товарных запасов"""
    
    def __init__(self):
        # Данные по этапам
        self.abc_data = None
        self.sales_data = None
        self.stock_data = None
        
        # Результаты расчетов
        self.abc_results = None
        self.calculated_ads = None
        self.calculated_min_stock = None
        self.stock_comparison = None
        
        # Параметры по умолчанию
        self.default_params = {
            'ip_target_days': 7,    # Транзитное время
            'min_stock_days': 30,   # Дни запаса
            'safety_factor': 1.0    # Коэффициент безопасности
        }
        
    def load_abc_file(self, file_content) -> Dict:
        """
        Загрузка и обработка файла для ABC анализа (исходникимини.xlsx)
        
        Args:
            file_content: Содержимое файла (bytes или file-like объект)
            
        Returns:
            Dict с информацией о загруженных данных
        """
        try:
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, sheet_name='Лист1', engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), sheet_name='Лист1', engine='openpyxl')
            
            # Пропускаем заголовки - данные начинаются с 6-й строки
            df = df.iloc[5:].copy()
            df = df.reset_index(drop=True)
            
            # Устанавливаем правильные названия колонок
            expected_columns = ['nomenclature', 'subcategory', 'category', 'annual_sales']
            df.columns = expected_columns[:len(df.columns)]
            
            # Очистка данных
            df = df.dropna(subset=['nomenclature'])
            df = df[df['nomenclature'].astype(str).str.strip() != '']
            df = df[df['nomenclature'].astype(str) != 'nan']
            
            # Преобразуем годовые продажи в числовой формат
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce').fillna(0)
            df = df[df['annual_sales'] > 0]
            
            # Очищаем текстовые поля
            for col in ['nomenclature', 'category', 'subcategory']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace(['nan', 'None', ''], np.nan)
            
            self.abc_data = df
            
            return {
                'success': True,
                'total_items': len(df),
                'categories': df['category'].nunique(),
                'total_sales': df['annual_sales'].sum(),
                'top_items': df.nlargest(5, 'annual_sales')[['nomenclature', 'annual_sales']].to_dict('records')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Ошибка загрузки ABC файла: {str(e)}"
            }
    
    def perform_abc_analysis(self) -> Dict:
        """
        Выполнение ABC анализа по загруженным данным
        
        Returns:
            Dict с результатами ABC анализа
        """
        if self.abc_data is None:
            return {'success': False, 'error': 'ABC данные не загружены'}
        
        try:
            df = self.abc_data.copy()
            
            # Сортируем по объему продаж (по убыванию)
            df = df.sort_values('annual_sales', ascending=False)
            
            # Рассчитываем проценты
            total_sales = df['annual_sales'].sum()
            df['sales_percentage'] = (df['annual_sales'] / total_sales) * 100
            df['cumulative_percentage'] = df['sales_percentage'].cumsum()
            
            # Присваиваем ABC классы по принципу Парето
            def assign_abc_class(cumulative_pct):
                if cumulative_pct <= 80:
                    return 'A'
                elif cumulative_pct <= 95:
                    return 'B'
                else:
                    return 'C'
            
            df['abc_class'] = df['cumulative_percentage'].apply(assign_abc_class)
            
            # Анализ по категориям
            category_results = {}
            for category in df['category'].dropna().unique():
                category_data = df[df['category'] == category]
                
                category_results[str(category)] = {
                    'total_items': len(category_data),
                    'total_sales': category_data['annual_sales'].sum(),
                    'sales_percentage': (category_data['annual_sales'].sum() / total_sales) * 100,
                    'abc_distribution': {
                        'A': len(category_data[category_data['abc_class'] == 'A']),
                        'B': len(category_data[category_data['abc_class'] == 'B']),
                        'C': len(category_data[category_data['abc_class'] == 'C'])
                    },
                    'avg_sales': category_data['annual_sales'].mean(),
                    'top_items': category_data.head(3)[['nomenclature', 'annual_sales', 'abc_class']].to_dict('records')
                }
            
            # Общая статистика ABC
            abc_summary = df['abc_class'].value_counts().to_dict()
            
            self.abc_results = {
                'abc_data_detailed': df,
                'category_analysis': category_results,
                'abc_summary': abc_summary,
                'total_sales': total_sales,
                'total_items': len(df)
            }
            
            return {
                'success': True,
                'abc_summary': abc_summary,
                'category_count': len(category_results),
                'total_sales': total_sales,
                'pareto_achieved': True  # 80/15/5 правило
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка ABC анализа: {str(e)}"}
    
    def load_sales_file(self, file_content) -> Dict:
        """
        Загрузка файла продаж для расчета ADS
        
        Args:
            file_content: Содержимое файла продаж
            
        Returns:
            Dict с информацией о загруженных данных продаж
        """
        try:
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # Ищем строку с заголовками
            header_row = None
            for i, row in df.iterrows():
                row_str = str(row.iloc[0]).lower()
                if pd.notna(row.iloc[0]) and any(word in row_str for word in ['номенклатура', 'наименование', 'товар']):
                    header_row = i
                    break
            
            if header_row is not None:
                # Устанавливаем заголовки
                headers = df.iloc[header_row].tolist()
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
            
            # Стандартизируем названия колонок
            df.columns = [str(col).lower().strip() if pd.notna(col) else f'col_{i}' for i, col in enumerate(df.columns)]
            
            # Ищем колонки с данными по месяцам
            month_patterns = [
                'янв', 'фев', 'мар', 'апр', 'май', 'июн', 
                'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
                'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                '01', '02', '03', '04', '05', '06',
                '07', '08', '09', '10', '11', '12'
            ]
            
            sales_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(pattern in col_str for pattern in month_patterns):
                    sales_columns.append(col)
            
            # Если не найдены месячные колонки, ищем числовые
            if not sales_columns:
                for col in df.columns:
                    if col not in ['номенклатура', 'наименование', 'товар', 'категория']:
                        # Проверяем, есть ли числовые данные
                        try:
                            pd.to_numeric(df[col], errors='coerce')
                            sales_columns.append(col)
                        except:
                            continue
            
            # Очищаем основные данные
            nomenclature_col = None
            for col in df.columns:
                if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                    nomenclature_col = col
                    break
            
            if nomenclature_col is None:
                nomenclature_col = df.columns[0]  # Берем первую колонку
            
            # Переименовываем колонку номенклатуры
            df = df.rename(columns={nomenclature_col: 'номенклатура'})
            
            # Фильтруем данные
            df = df.dropna(subset=['номенклатура'])
            df = df[df['номенклатура'].astype(str).str.strip() != '']
            df = df[df['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем колонки продаж в числовой формат
            for col in sales_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Рассчитываем общие продажи за период
            if sales_columns:
                df['total_sales'] = df[sales_columns].sum(axis=1)
                # Предполагаем, что данные за год (365 дней)
                df['ads'] = df['total_sales'] / 365
            else:
                df['total_sales'] = 0
                df['ads'] = 0
            
            # Убираем товары без продаж
            df = df[df['total_sales'] > 0]
            
            self.sales_data = df
            self.calculated_ads = df[['номенклатура', 'ads', 'total_sales']].copy()
            
            return {
                'success': True,
                'total_items': len(df),
                'sales_columns_found': len(sales_columns),
                'total_sales': df['total_sales'].sum(),
                'total_ads': df['ads'].sum(),
                'avg_ads': df['ads'].mean(),
                'top_sellers': df.nlargest(5, 'ads')[['номенклатура', 'ads']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка загрузки файла продаж: {str(e)}"}
    
    def calculate_min_stock(self, ip_target_days: int = None, min_stock_days: int = None) -> Dict:
        """
        Расчет минимальных запасов на основе ADS
        
        Args:
            ip_target_days: Транзитное время в днях
            min_stock_days: Количество дней запаса
            
        Returns:
            Dict с результатами расчета минимальных запасов
        """
        if self.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан. Сначала загрузите файл продаж.'}
        
        try:
            # Используем переданные параметры или значения по умолчанию
            ip_days = ip_target_days or self.default_params['ip_target_days']
            stock_days = min_stock_days or self.default_params['min_stock_days']
            
            df = self.calculated_ads.copy()
            
            # Рассчитываем компоненты минимального запаса
            df['ip_target_days'] = ip_days
            df['min_stock_days'] = stock_days
            
            # Транзитное потребление = ADS × транзитное время
            df['transit_consumption'] = df['ads'] * ip_days
            
            # Базовый минимальный запас = ADS × дни запаса  
            df['min_stock_base'] = df['ads'] * stock_days
            
            # Итоговый минимальный запас = базовый запас + транзитное потребление
            df['min_stock_total'] = df['min_stock_base'] + df['transit_consumption']
            
            # Добавляем статус и приоритет
            df['priority'] = df['ads'].apply(lambda x: 'Высокий' if x > df['ads'].quantile(0.8) else 
                                           'Средний' if x > df['ads'].quantile(0.5) else 'Низкий')
            
            self.calculated_min_stock = df
            
            return {
                'success': True,
                'total_items': len(df),
                'total_min_stock': df['min_stock_total'].sum(),
                'total_transit_consumption': df['transit_consumption'].sum(),
                'total_base_stock': df['min_stock_base'].sum(),
                'parameters': {
                    'ip_target_days': ip_days,
                    'min_stock_days': stock_days
                },
                'top_min_stock': df.nlargest(5, 'min_stock_total')[['номенклатура', 'min_stock_total', 'ads']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка расчета минимальных запасов: {str(e)}"}
    
    def load_current_stock_file(self, file_content) -> Dict:
        """
        Загрузка файла текущих остатков
        
        Args:
            file_content: Содержимое файла остатков
            
        Returns:
            Dict с информацией о загруженных остатках
        """
        try:
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # Ищем заголовки
            header_row = None
            for i, row in df.iterrows():
                row_str = str(row.iloc[0]).lower()
                if pd.notna(row.iloc[0]) and any(word in row_str for word in ['номенклатура', 'наименование', 'товар']):
                    header_row = i
                    break
            
            if header_row is not None:
                headers = df.iloc[header_row].tolist()
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
            
            # Стандартизируем названия колонок
            df.columns = [str(col).lower().strip() if pd.notna(col) else f'col_{i}' for i, col in enumerate(df.columns)]
            
            # Ищем колонку номенклатуры
            nomenclature_col = None
            for col in df.columns:
                if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                    nomenclature_col = col
                    break
            
            if nomenclature_col is None:
                nomenclature_col = df.columns[0]
            
            df = df.rename(columns={nomenclature_col: 'номенклатура'})
            
            # Ищем колонки с остатками
            stock_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(word in col_str for word in ['остаток', 'stock', 'balance', 'склад', 'количество']):
                    stock_columns.append(col)
                # Также проверяем числовые колонки (кроме номенклатуры)
                elif col != 'номенклатура':
                    try:
                        # Проверяем, содержит ли колонка числовые данные
                        numeric_data = pd.to_numeric(df[col], errors='coerce')
                        if not numeric_data.isna().all():
                            stock_columns.append(col)
                    except:
                        continue
            
            # Очищаем данные
            df = df.dropna(subset=['номенклатура'])
            df = df[df['номенклатура'].astype(str).str.strip() != '']
            df = df[df['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем остатки в числовой формат
            for col in stock_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Рассчитываем общий остаток
            if stock_columns:
                df['total_current_stock'] = df[stock_columns].sum(axis=1)
            else:
                df['total_current_stock'] = 0
            
            self.stock_data = df
            
            return {
                'success': True,
                'total_items': len(df),
                'stock_columns_found': len(stock_columns),
                'total_stock': df['total_current_stock'].sum(),
                'items_with_stock': len(df[df['total_current_stock'] > 0]),
                'avg_stock': df['total_current_stock'].mean(),
                'top_stock': df.nlargest(5, 'total_current_stock')[['номенклатура', 'total_current_stock']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка загрузки файла остатков: {str(e)}"}
    
    def compare_stock_vs_min(self) -> Dict:
        """
        Сравнение текущих остатков с минимальными запасами
        
        Returns:
            Dict с результатами сравнения
        """
        if self.calculated_min_stock is None:
            return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
        
        if self.stock_data is None:
            return {'success': False, 'error': 'Текущие остатки не загружены'}
        
        try:
            # Объединяем данные по номенклатуре
            min_stock_df = self.calculated_min_stock.copy()
            current_stock_df = self.stock_data[['номенклатура', 'total_current_stock']].copy()
            
            # Merge данных
            comparison = pd.merge(
                min_stock_df,
                current_stock_df,
                on='номенклатура',
                how='left'
            )
            
            # Заполняем пропуски нулями
            comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
            
            # Рассчитываем метрики сравнения
            comparison['stock_deficit'] = comparison['min_stock_total'] - comparison['total_current_stock']
            comparison['stock_deficit'] = comparison['stock_deficit'].apply(lambda x: max(0, x))
            
            # Текущий запас в днях
            comparison['current_stock_days'] = np.where(
                comparison['ads'] > 0,
                comparison['total_current_stock'] / comparison['ads'],
                0
            )
            
            # Статус товара
            def determine_status(row):
                if row['stock_deficit'] > 0:
                    if row['current_stock_days'] < row['ip_target_days']:
                        return 'КРИТИЧНО'
                    else:
                        return 'НЕДОСТАТОК'
                else:
                    return 'ДОСТАТОЧНО'
            
            comparison['status'] = comparison.apply(determine_status, axis=1)
            
            # Рекомендуемый заказ с учетом коэффициента безопасности
            safety_factor = self.default_params['safety_factor']
            comparison['recommended_order'] = comparison['stock_deficit'] * safety_factor
            comparison['recommended_order'] = comparison['recommended_order'].apply(lambda x: max(0, x))
            
            # Приоритет заказа
            comparison['order_priority'] = comparison.apply(
                lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                           else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                           else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                           else 'НЕ ТРЕБУЕТСЯ', axis=1
            )
            
            # Сортируем по критичности
            priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
            comparison['status_priority'] = comparison['status'].map(priority_order)
            comparison = comparison.sort_values(['status_priority', 'stock_deficit'], ascending=[False, False])
            comparison = comparison.drop('status_priority', axis=1)
            
            self.stock_comparison = comparison
            
            # Статистика результатов
            total_items = len(comparison)
            deficit_items = len(comparison[comparison['stock_deficit'] > 0])
            critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
            sufficient_items = len(comparison[comparison['status'] == 'ДОСТАТОЧНО'])
            
            total_deficit_value = comparison['stock_deficit'].sum()
            total_recommended_order = comparison['recommended_order'].sum()
            
            return {
                'success': True,
                'total_items': total_items,
                'deficit_items': deficit_items,
                'critical_items': critical_items,
                'sufficient_items': sufficient_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'total_deficit_value': total_deficit_value,
                'total_recommended_order': total_recommended_order,
                'top_deficit_items': comparison[comparison['stock_deficit'] > 0].head(10)[
                    ['номенклатура', 'stock_deficit', 'current_stock_days', 'status', 'order_priority']
                ].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка сравнения остатков: {str(e)}"}
    
    def get_system_status(self) -> Dict:
        """
        Получение статуса всей системы
        
        Returns:
            Dict со статусом всех модулей
        """
        status = {
            'abc_analysis': {
                'loaded': self.abc_data is not None,
                'analyzed': self.abc_results is not None,
                'items_count': len(self.abc_data) if self.abc_data is not None else 0
            },
            'sales_analysis': {
                'loaded': self.sales_data is not None,
                'ads_calculated': self.calculated_ads is not None,
                'items_count': len(self.calculated_ads) if self.calculated_ads is not None else 0
            },
            'min_stock_analysis': {
                'calculated': self.calculated_min_stock is not None,
                'items_count': len(self.calculated_min_stock) if self.calculated_min_stock is not None else 0
            },
            'stock_analysis': {
                'loaded': self.stock_data is not None,
                'compared': self.stock_comparison is not None,
                'items_count': len(self.stock_data) if self.stock_data is not None else 0
            }
        }
        
        # Общий прогресс
        completed_steps = sum([
            status['abc_analysis']['analyzed'],
            status['sales_analysis']['ads_calculated'],
            status['min_stock_analysis']['calculated'],
            status['stock_analysis']['compared']
        ])
        
        status['overall'] = {
            'completed_steps': completed_steps,
            'total_steps': 4,
            'progress_percentage': (completed_steps / 4) * 100,
            'ready_for_export': completed_steps >= 2  # Минимум ADS + один из анализов
        }
        
        return status
    
    def export_all_results(self) -> io.BytesIO:
        """
        Экспорт всех результатов в Excel файл
        
        Returns:
            io.BytesIO с Excel файлом
        """
        output = io.BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Общий статус системы
                status = self.get_system_status()
                status_df = pd.DataFrame([status['overall']])
                status_df.to_excel(writer, sheet_name='Общий_статус', index=False)
                
                # ABC анализ
                if self.abc_results is not None:
                    # Детальные данные ABC
                    abc_detailed = self.abc_results['abc_data_detailed']
                    abc_detailed.to_excel(writer, sheet_name='ABC_детально', index=False)
                    
                    # Анализ по категориям
                    if self.abc_results['category_analysis']:
                        category_df = pd.DataFrame.from_dict(
                            self.abc_results['category_analysis'], 
                            orient='index'
                        )
                        category_df.to_excel(writer, sheet_name='ABC_по_категориям', index=True)
                
                # ADS расчеты
                if self.calculated_ads is not None:
                    self.calculated_ads.to_excel(writer, sheet_name='ADS_расчет', index=False)
                
                # Минимальные запасы
                if self.calculated_min_stock is not None:
                    self.calculated_min_stock.to_excel(writer, sheet_name='Минимальные_запасы', index=False)
                
                # Текущие остатки
                if self.stock_data is not None:
                    stock_export = self.stock_data[['номенклатура', 'total_current_stock']].copy()
                    stock_export.to_excel(writer, sheet_name='Текущие_остатки', index=False)
                
                # Сравнение остатков
                if self.stock_comparison is not None:
                    # Полное сравнение
                    self.stock_comparison.to_excel(writer, sheet_name='Полное_сравнение', index=False)
                    
                    # Товары с дефицитом
                    deficit_items = self.stock_comparison[self.stock_comparison['stock_deficit'] > 0]
                    if not deficit_items.empty:
                        deficit_items.to_excel(writer, sheet_name='Товары_с_дефицитом', index=False)
                    
                    # Критичные товары
                    critical_items = self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО']
                    if not critical_items.empty:
                        critical_items.to_excel(writer, sheet_name='Критичные_товары', index=False)
                    
                    # Рекомендации по заказу
                    order_recommendations = self.stock_comparison[
                        self.stock_comparison['recommended_order'] > 0
                    ][['номенклатура', 'recommended_order', 'order_priority', 'ads', 'current_stock_days']]
                    
                    if not order_recommendations.empty:
                        order_recommendations = order_recommendations.sort_values('recommended_order', ascending=False)
                        order_recommendations.to_excel(writer, sheet_name='Рекомендации_заказа', index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            raise Exception(f"Ошибка экспорта: {str(e)}")
    
    def create_visualizations(self) -> Dict:
        """
        Создание визуализаций для анализа
        
        Returns:
            Dict с объектами графиков Plotly
        """
        visualizations = {}
        
        try:
            # ABC анализ - распределение классов
            if self.abc_results is not None:
                abc_summary = self.abc_results['abc_summary']
                
                # Круговая диаграмма ABC классов
                fig_abc_pie = px.pie(
                    values=list(abc_summary.values()),
                    names=list(abc_summary.keys()),
                    title="Распределение товаров по ABC классам",
                    color_discrete_map={'A': '#ff4444', 'B': '#ffaa00', 'C': '#00aa44'}
                )
                visualizations['abc_distribution'] = fig_abc_pie
                
                # Парето-диаграмма
                abc_data = self.abc_results['abc_data_detailed']
                pareto_data = abc_data.head(50)  # Топ-50 для читаемости
                
                fig_pareto = go.Figure()
                
                # Столбцы продаж
                fig_pareto.add_trace(go.Bar(
                    x=list(range(len(pareto_data))),
                    y=pareto_data['annual_sales'],
                    name='Продажи',
                    marker_color='lightblue',
                    yaxis='y'
                ))
                
                # Линия накопительного процента
                fig_pareto.add_trace(go.Scatter(
                    x=list(range(len(pareto_data))),
                    y=pareto_data['cumulative_percentage'],
                    mode='lines+markers',
                    name='Накопительный %',
                    line=dict(color='red', width=2),
                    yaxis='y2'
                ))
                
                fig_pareto.update_layout(
                    title='Парето-анализ товаров (принцип 80/20)',
                    xaxis_title='Товары (ранжированные по продажам)',
                    yaxis=dict(title='Объем продаж', side='left'),
                    yaxis2=dict(title='Накопительный процент (%)', side='right', overlaying='y', range=[0, 100]),
                    showlegend=True
                )
                
                visualizations['pareto_analysis'] = fig_pareto
            
            # ADS анализ - топ товары
            if self.calculated_ads is not None:
                top_ads = self.calculated_ads.nlargest(20, 'ads')
                
                fig_ads = px.bar(
                    top_ads,
                    x='ads',
                    y='номенклатура',
                    orientation='h',
                    title='Топ-20 товаров по ADS (среднедневные продажи)',
                    labels={'ads': 'ADS', 'номенклатура': 'Товар'}
                )
                fig_ads.update_layout(height=600)
                visualizations['top_ads'] = fig_ads
            
            # Сравнение остатков - статусы товаров
            if self.stock_comparison is not None:
                status_counts = self.stock_comparison['status'].value_counts()
                
                fig_status = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title='Распределение товаров по статусам остатков',
                    labels={'x': 'Статус', 'y': 'Количество товаров'},
                    color=status_counts.index,
                    color_discrete_map={
                        'КРИТИЧНО': '#ff4444',
                        'НЕДОСТАТОК': '#ffaa00', 
                        'ДОСТАТОЧНО': '#00aa44'
                    }
                )
                visualizations['stock_status'] = fig_status
                
                # График дефицита по товарам
                deficit_data = self.stock_comparison[self.stock_comparison['stock_deficit'] > 0].head(20)
                
                if not deficit_data.empty:
                    fig_deficit = px.bar(
                        deficit_data,
                        x='stock_deficit',
                        y='номенклатура',
                        orientation='h',
                        title='Топ-20 товаров с наибольшим дефицитом',
                        labels={'stock_deficit': 'Дефицит', 'номенклатура': 'Товар'},
                        color='order_priority',
                        color_discrete_map={
                            'СРОЧНО': '#ff0000',
                            'ВЫСОКИЙ': '#ff8800',
                            'СРЕДНИЙ': '#ffcc00'
                        }
                    )
                    fig_deficit.update_layout(height=600)
                    visualizations['deficit_analysis'] = fig_deficit
            
            return visualizations
            
        except Exception as e:
            print(f"Ошибка создания визуализаций: {str(e)}")
            return {}
    
    def get_summary_report(self) -> Dict:
        """
        Получение итогового отчета по всем анализам
        
        Returns:
            Dict с итоговой сводкой
        """
        report = {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
            'system_status': self.get_system_status()
        }
        
        # ABC анализ сводка
        if self.abc_results is not None:
            abc_summary = self.abc_results['abc_summary']
            total_abc_items = sum(abc_summary.values())
            
            report['abc_analysis'] = {
                'total_items': total_abc_items,
                'total_sales': self.abc_results['total_sales'],
                'distribution': {
                    'A_items': abc_summary.get('A', 0),
                    'A_percentage': (abc_summary.get('A', 0) / total_abc_items) * 100,
                    'B_items': abc_summary.get('B', 0),
                    'B_percentage': (abc_summary.get('B', 0) / total_abc_items) * 100,
                    'C_items': abc_summary.get('C', 0),
                    'C_percentage': (abc_summary.get('C', 0) / total_abc_items) * 100
                },
                'categories_analyzed': len(self.abc_results['category_analysis'])
            }
        
        # ADS анализ сводка
        if self.calculated_ads is not None:
            report['ads_analysis'] = {
                'total_items': len(self.calculated_ads),
                'total_ads': self.calculated_ads['ads'].sum(),
                'avg_ads': self.calculated_ads['ads'].mean(),
                'total_sales_period': self.calculated_ads['total_sales'].sum(),
                'top_seller': {
                    'item': self.calculated_ads.loc[self.calculated_ads['ads'].idxmax(), 'номенклатура'],
                    'ads_value': self.calculated_ads['ads'].max()
                }
            }
        
        # Минимальные запасы сводка
        if self.calculated_min_stock is not None:
            report['min_stock_analysis'] = {
                'total_items': len(self.calculated_min_stock),
                'total_min_stock': self.calculated_min_stock['min_stock_total'].sum(),
                'total_transit_consumption': self.calculated_min_stock['transit_consumption'].sum(),
                'parameters': {
                    'ip_days': self.calculated_min_stock['ip_target_days'].iloc[0],
                    'stock_days': self.calculated_min_stock['min_stock_days'].iloc[0]
                }
            }
        
        # Сравнение остатков сводка
        if self.stock_comparison is not None:
            total_items = len(self.stock_comparison)
            deficit_items = len(self.stock_comparison[self.stock_comparison['stock_deficit'] > 0])
            critical_items = len(self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'])
            
            report['stock_comparison'] = {
                'total_items': total_items,
                'deficit_items': deficit_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'critical_items': critical_items,
                'critical_percentage': (critical_items / total_items) * 100,
                'total_deficit_value': self.stock_comparison['stock_deficit'].sum(),
                'total_recommended_order': self.stock_comparison['recommended_order'].sum(),
                'priority_distribution': self.stock_comparison['order_priority'].value_counts().to_dict()
            }
        
        return report
    
    def clear_all_data(self):
        """Очистка всех загруженных данных и результатов"""
        self.abc_data = None
        self.sales_data = None
        self.stock_data = None
        self.abc_results = None
        self.calculated_ads = None
        self.calculated_min_stock = None
        self.stock_comparison = None
    
    def update_parameters(self, **kwargs):
        """
        Обновление параметров системы
        
        Args:
            **kwargs: Параметры для обновления (ip_target_days, min_stock_days, safety_factor)
        """
        for key, value in kwargs.items():
            if key in self.default_params:
                self.default_params[key] = value
    
    def get_recommendations(self) -> List[str]:
        """
        Получение рекомендаций по улучшению системы
        
        Returns:
            List рекомендаций
        """
        recommendations = []
        
        status = self.get_system_status()
        
        # Проверяем полноту анализа
        if not status['abc_analysis']['analyzed']:
            recommendations.append("Выполните ABC анализ для лучшей классификации товаров")
        
        if not status['sales_analysis']['ads_calculated']:
            recommendations.append("Загрузите данные продаж для расчета ADS")
        
        if not status['min_stock_analysis']['calculated']:
            recommendations.append("Рассчитайте минимальные запасы на основе ADS")
        
        if not status['stock_analysis']['compared']:
            recommendations.append("Загрузите текущие остатки для сравнения с минимальными запасами")
        
        # Анализируем результаты сравнения
        if self.stock_comparison is not None:
            critical_count = len(self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'])
            total_count = len(self.stock_comparison)
            
            if critical_count > total_count * 0.1:  # Более 10% критичных товаров
                recommendations.append(f"Критическая ситуация: {critical_count} товаров требуют срочного пополнения")
            
            deficit_count = len(self.stock_comparison[self.stock_comparison['stock_deficit'] > 0])
            if deficit_count > total_count * 0.3:  # Более 30% товаров с дефицитом
                recommendations.append("Рассмотрите увеличение частоты заказов или коэффициента безопасности")
        
        # ABC анализ рекомендации
        if self.abc_results is not None:
            abc_summary = self.abc_results['abc_summary']
            total_items = sum(abc_summary.values())
            a_percentage = (abc_summary.get('A', 0) / total_items) * 100
            
            if a_percentage < 15:
                recommendations.append("Низкая доля A товаров - проверьте ассортиментную политику")
            elif a_percentage > 25:
                recommendations.append("Высокая доля A товаров - возможно избыточная концентрация продаж")
        
        if not recommendations:
            recommendations.append("Система настроена оптимально. Регулярно обновляйте данные.")
        
        return recommendations