#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизированный процессор данных для работы с большими объемами
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import datetime, timedelta
import streamlit as st
from webhook_data_accumulator import WebhookDataAccumulator

class OptimizedDataProcessor:
    """Оптимизированный процессор для больших объемов данных"""
    
    def __init__(self, accumulator: WebhookDataAccumulator):
        self.accumulator = accumulator
        self.cache = {}
        
    @st.cache_data(ttl=300, max_entries=10)  # Кеш на 5 минут
    def get_aggregated_sales_data(_self, start_date: str = None, end_date: str = None, 
                                  aggregation_level: str = 'daily') -> pd.DataFrame:
        """
        Получение агрегированных данных о продажах с различными уровнями детализации
        
        aggregation_level: 'daily', 'weekly', 'monthly'
        """
        
        with sqlite3.connect(_self.accumulator.db_path) as conn:
            # Базовый запрос с агрегацией на уровне БД
            if aggregation_level == 'daily':
                query = """
                    SELECT 
                        date,
                        branch,
                        category,
                        SUM(amount) as total_amount,
                        SUM(quantity) as total_quantity,
                        COUNT(DISTINCT item_code) as unique_items
                    FROM sales
                    WHERE 1=1
                """
                group_by = "GROUP BY date, branch, category"
                
            elif aggregation_level == 'weekly':
                query = """
                    SELECT 
                        strftime('%Y-W%W', date) as week,
                        branch,
                        category,
                        SUM(amount) as total_amount,
                        SUM(quantity) as total_quantity,
                        COUNT(DISTINCT item_code) as unique_items,
                        MIN(date) as start_date,
                        MAX(date) as end_date
                    FROM sales
                    WHERE 1=1
                """
                group_by = "GROUP BY strftime('%Y-W%W', date), branch, category"
                
            else:  # monthly
                query = """
                    SELECT 
                        strftime('%Y-%m', date) as month,
                        branch,
                        category,
                        SUM(amount) as total_amount,
                        SUM(quantity) as total_quantity,
                        COUNT(DISTINCT item_code) as unique_items,
                        MIN(date) as start_date,
                        MAX(date) as end_date
                    FROM sales
                    WHERE 1=1
                """
                group_by = "GROUP BY strftime('%Y-%m', date), branch, category"
            
            # Добавляем фильтры по датам
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += f" {group_by} ORDER BY 1"
            
            return pd.read_sql_query(query, conn, params=params)
    
    @st.cache_data(ttl=300)
    def get_top_items_summary(_self, start_date: str = None, end_date: str = None, 
                             limit: int = 1000) -> pd.DataFrame:
        """Получение топ товаров с агрегацией в БД"""
        
        with sqlite3.connect(_self.accumulator.db_path) as conn:
            query = """
                SELECT 
                    item_code,
                    item_name,
                    category,
                    SUM(amount) as total_amount,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT branch) as branches_count,
                    COUNT(DISTINCT date) as sales_days
                FROM sales
                WHERE 1=1
            """
            
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += f"""
                GROUP BY item_code, item_name, category
                ORDER BY total_amount DESC
                LIMIT {limit}
            """
            
            return pd.read_sql_query(query, conn, params=params)
    
    @st.cache_data(ttl=300)
    def get_category_abc_summary(_self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """ABC анализ по категориям с агрегацией в БД"""
        
        with sqlite3.connect(_self.accumulator.db_path) as conn:
            query = """
                SELECT 
                    category,
                    SUM(amount) as total_amount,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT item_code) as unique_items,
                    COUNT(*) as total_records
                FROM sales
                WHERE category IS NOT NULL AND category != ''
            """
            
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " GROUP BY category ORDER BY total_amount DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                # ABC классификация
                df['cumsum_amount'] = df['total_amount'].cumsum()
                total_amount = df['total_amount'].sum()
                df['percent'] = (df['cumsum_amount'] / total_amount * 100).round(2)
                
                # Определяем ABC группы
                df['abc_class'] = 'C'
                df.loc[df['percent'] <= 80, 'abc_class'] = 'A'
                df.loc[(df['percent'] > 80) & (df['percent'] <= 95), 'abc_class'] = 'B'
                
            return df
    
    @st.cache_data(ttl=300)
    def get_turnover_summary(_self, start_date: str = None, end_date: str = None, 
                           stock_data: pd.DataFrame = None) -> pd.DataFrame:
        """Расчет оборачиваемости с агрегацией"""
        
        if stock_data is None or stock_data.empty:
            return pd.DataFrame()
        
        # Получаем агрегированные продажи по товарам
        with sqlite3.connect(_self.accumulator.db_path) as conn:
            query = """
                SELECT 
                    item_code,
                    item_name,
                    SUM(quantity) as total_sales_qty,
                    SUM(amount) as total_sales_amount,
                    COUNT(DISTINCT date) as sales_days
                FROM sales
                WHERE 1=1
            """
            
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " GROUP BY item_code, item_name"
            
            sales_summary = pd.read_sql_query(query, conn, params=params)
        
        if sales_summary.empty:
            return pd.DataFrame()
        
        # Агрегируем остатки
        stock_summary = stock_data.groupby(['item_code', 'item_name']).agg({
            'quantity': 'sum'
        }).reset_index()
        stock_summary.rename(columns={'quantity': 'stock_quantity'}, inplace=True)
        
        # Объединяем
        turnover_data = pd.merge(
            stock_summary,
            sales_summary,
            on=['item_code', 'item_name'],
            how='inner'
        )
        
        # Расчет оборачиваемости
        turnover_data['daily_sales'] = turnover_data['total_sales_qty'] / 30.5
        turnover_data['turnover_days'] = np.where(
            turnover_data['daily_sales'] > 0,
            turnover_data['stock_quantity'] / turnover_data['daily_sales'],
            999999
        )
        
        # Категоризация
        turnover_data['turnover_category'] = pd.cut(
            turnover_data['turnover_days'],
            bins=[0, 30, 60, 90, 180, 365, 999999],
            labels=['Высокая (< 30)', 'Хорошая (30-60)', 'Средняя (60-90)', 
                   'Низкая (90-180)', 'Очень низкая (180-365)', 'Критическая (> 365)']
        )
        
        return turnover_data
    
    def get_data_statistics(self) -> Dict:
        """Получение общей статистики данных"""
        
        with sqlite3.connect(self.accumulator.db_path) as conn:
            stats = {}
            
            # Основная статистика
            cursor = conn.cursor()
            
            # Общее количество записей
            cursor.execute("SELECT COUNT(*) FROM sales")
            stats['total_records'] = cursor.fetchone()[0]
            
            # Диапазон дат
            cursor.execute("SELECT MIN(date), MAX(date) FROM sales")
            date_range = cursor.fetchone()
            stats['date_range'] = {
                'start': date_range[0],
                'end': date_range[1]
            }
            
            # Количество уникальных значений
            cursor.execute("SELECT COUNT(DISTINCT item_code) FROM sales")
            stats['unique_items'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT branch) FROM sales")
            stats['unique_branches'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT category) FROM sales WHERE category IS NOT NULL AND category != ''")
            stats['unique_categories'] = cursor.fetchone()[0]
            
            # Размер данных по периодам
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN date >= date('now', '-30 days') THEN '30_days'
                        WHEN date >= date('now', '-90 days') THEN '90_days'
                        WHEN date >= date('now', '-180 days') THEN '180_days'
                        ELSE 'older'
                    END as period,
                    COUNT(*) as count
                FROM sales
                GROUP BY 1
            """)
            
            period_stats = cursor.fetchall()
            stats['period_breakdown'] = {period: count for period, count in period_stats}
            
            return stats
    
    def sample_data_for_visualization(self, df: pd.DataFrame, 
                                    max_points: int = 10000,
                                    sampling_method: str = 'random') -> pd.DataFrame:
        """Умная выборка данных для визуализации"""
        
        if len(df) <= max_points:
            return df
        
        if sampling_method == 'random':
            return df.sample(n=max_points, random_state=42)
        
        elif sampling_method == 'systematic':
            # Систематическая выборка
            step = len(df) // max_points
            return df.iloc[::step].head(max_points)
        
        elif sampling_method == 'stratified':
            # Стратифицированная выборка по важным полям
            if 'amount' in df.columns:
                # Сортируем по сумме и берем равномерно
                df_sorted = df.sort_values('amount', ascending=False)
                step = len(df_sorted) // max_points
                return df_sorted.iloc[::step].head(max_points)
        
        return df.head(max_points)
    
    def get_recommended_aggregation_level(self, start_date: str = None, 
                                        end_date: str = None) -> str:
        """Рекомендуемый уровень агрегации на основе объема данных"""
        
        stats = self.get_data_statistics()
        
        if start_date and end_date:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            days_diff = (end_dt - start_dt).days
        else:
            # Полный период
            if stats['date_range']['start'] and stats['date_range']['end']:
                start_dt = pd.to_datetime(stats['date_range']['start'])
                end_dt = pd.to_datetime(stats['date_range']['end'])
                days_diff = (end_dt - start_dt).days
            else:
                days_diff = 365  # По умолчанию
        
        total_records = stats['total_records']
        
        # Логика рекомендации
        if days_diff <= 90 and total_records <= 50000:
            return 'daily'
        elif days_diff <= 365 and total_records <= 200000:
            return 'weekly'
        else:
            return 'monthly'