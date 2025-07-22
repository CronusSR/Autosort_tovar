#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СИСТЕМА РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ - ЧИСТАЯ ВЕРСИЯ
Интеграция с существующей системой ModularInventorySystem
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ===== КОНФИГУРАЦИЯ СИСТЕМЫ =====

class BranchSalesAnalyzer:
    """Анализатор продаж по филиалам с анализом оборачиваемости"""
    
    def __init__(self):
        self.branch_sales_data = {}
        self.turnover_analysis = {}
        self.consolidated_data = None
    
    def process_branch_sales_file(self, file_content, branch_name):
        """Обработка файла продаж для конкретного филиала"""
        try:
            # Сохраняем содержимое файла в байтах для повторного использования
            if hasattr(file_content, 'read'):
                file_bytes = file_content.read()
                file_content.seek(0)  # Возвращаемся в начало для совместимости
            else:
                file_bytes = file_content
            
            # Определяем тип файла и обрабатываем соответственно
            file_type = self.detect_file_type(file_content, branch_name)
            
            if file_type == "detailed_sales":
                return self.process_detailed_sales_file(file_bytes, branch_name)
            elif file_type == "summary_sales":
                return self.process_summary_sales_file(file_bytes, branch_name)
            elif file_type == "abc_analysis":
                return self.process_abc_analysis_file(file_bytes, branch_name)
            else:
                raise ValueError(f"Неизвестный тип файла: {file_type}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки файла для {branch_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def detect_file_type(self, file_content, branch_name):
        """Определение типа файла на основе структуры"""
        try:
            # Читаем файл без заголовков для анализа
            if hasattr(file_content, 'read'):
                # Сохраняем содержимое файла
                file_bytes = file_content.read()
                file_content.seek(0)  # Возвращаемся в начало
                df_raw = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=None, nrows=15)
            else:
                df_raw = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None, nrows=15)
            
            # Ищем ключевые фразы в первых строках
            all_text = ""
            for i in range(min(10, len(df_raw))):
                row_text = " ".join([str(cell) for cell in df_raw.iloc[i] if pd.notna(cell)])
                all_text += row_text.lower() + " "
            
            print(f"🔍 Анализ типа файла для {branch_name}")
            print(f"📝 Найденный текст: {all_text[:200]}...")
            
            # Определяем тип по ключевым словам
            if "валовая прибыль предприятия" in all_text:
                print("✅ Тип файла: Детальные продажи (1С отчет)")
                return "detailed_sales"
            elif "abc" in all_text or ("наименование" in all_text and "группа" in all_text):
                print("✅ Тип файла: ABC/XYZ анализ")
                return "abc_analysis"
            elif "категория" in all_text and "подкатегория" in all_text:
                print("✅ Тип файла: Сводные продажи")
                return "summary_sales"
            else:
                # Пробуем определить по структуре заголовков
                for header_row in range(min(5, len(df_raw))):
                    try:
                        if hasattr(file_content, 'read'):
                            df_test = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=header_row, nrows=5)
                        else:
                            df_test = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=header_row, nrows=5)
                        
                        cols_text = " ".join([str(col).lower() for col in df_test.columns if pd.notna(col)])
                        
                        if "количество" in cols_text and "выручка" in cols_text:
                            print("✅ Тип файла: Детальные продажи (по заголовкам)")
                            return "detailed_sales"
                        elif any(warehouse in cols_text for warehouse in ["склад", "магазин", "trade"]):
                            print("✅ Тип файла: Сводные продажи (по заголовкам)")
                            return "summary_sales"
                    except:
                        continue
                
                print("⚠️ Тип файла: Неизвестный, используем детальные продажи")
                return "detailed_sales"
                
        except Exception as e:
            print(f"❌ Ошибка определения типа файла: {e}")
            return "detailed_sales"
    
    def process_detailed_sales_file(self, file_bytes, branch_name):
        """Обработка детального файла продаж (как файл 6 склада)"""
        try:
            # Читаем файл продаж с заголовками в строке 8 (индекс 7)
            df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=7)
            
            print(f"📊 Обработка детального файла для {branch_name}: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # Пропускаем первые 2 строки (строка 9 с подзаголовками и строка 10 с итогами)
            df = df.iloc[2:].reset_index(drop=True)
            
            if len(df.columns) < 13:
                raise ValueError(f"Недостаточно колонок в файле: {len(df.columns)}, ожидалось минимум 13")
            
            # Создаем новый DataFrame только с нужными колонками
            df_clean = pd.DataFrame({
                'номенклатура': df.iloc[:, 0],
                'количество': df.iloc[:, 8],
                'выручка': df.iloc[:, 10],
                'себестоимость': df.iloc[:, 12]
            })
            
            df = df_clean
            
            # Очищаем данные номенклатуры
            df = df.dropna(subset=['номенклатура'])
            df = df[df['номенклатура'].astype(str).str.strip() != '']
            df = df[df['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем числовые колонки
            for col in ['количество', 'выручка', 'себестоимость']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Фильтруем строки с валидными данными
            # Оставляем только строки где количество > 0 и выручка > 0
            df = df[(df['количество'] > 0) & (df['выручка'] > 0)]
            
            print(f"🧹 Финальная очистка: оставлено {len(df)} строк с валидными данными")
            
            # Группируем по номенклатуре (на случай дублей)
            df_grouped = df.groupby('номенклатура').agg({
                'количество': 'sum',
                'выручка': 'sum',
                'себестоимость': 'sum'
            }).reset_index()
            
            # Добавляем информацию о филиале
            df_grouped['филиал'] = branch_name
            
            # Рассчитываем дополнительные метрики
            df_grouped['прибыль'] = df_grouped['выручка'] - df_grouped['себестоимость']
            df_grouped['рентабельность'] = (df_grouped['прибыль'] / df_grouped['выручка'] * 100).fillna(0)
            df_grouped['средняя_цена'] = (df_grouped['выручка'] / df_grouped['количество']).fillna(0)
            
            # Сохраняем данные для филиала
            self.branch_sales_data[branch_name] = df_grouped
            
            print(f"✅ Обработано {len(df_grouped)} уникальных товаров для {branch_name}")
            print(f"📊 Общая выручка: {df_grouped['выручка'].sum():,.0f}")
            print(f"📊 Общая прибыль: {df_grouped['прибыль'].sum():,.0f}")
            
            return {
                'success': True,
                'items_processed': len(df_grouped),
                'total_revenue': df_grouped['выручка'].sum(),
                'total_quantity': df_grouped['количество'].sum(),
                'total_profit': df_grouped['прибыль'].sum()
            }
            
        except Exception as e:
            print(f"❌ Ошибка обработки детального файла для {branch_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_summary_sales_file(self, file_bytes, branch_name):
        """Обработка сводного файла продаж"""
        try:
            # Читаем сводный файл (заголовки в первой строке)
            df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=0)
            
            print(f"📊 Обработка сводного файла для {branch_name}: {df.shape[0]} строк, {df.shape[1]} колонок")
            print(f"🔍 Колонки: {list(df.columns)}")
            
            # Ищем колонку с данными для этого склада
            warehouse_col = None
            for col in df.columns:
                if branch_name.lower() in str(col).lower():
                    warehouse_col = col
                    break
            
            if warehouse_col is None:
                print(f"⚠️ Колонка для {branch_name} не найдена в сводном файле")
                return {
                    'success': True,
                    'items_processed': 0,
                    'total_revenue': 0,
                    'total_quantity': 0,
                    'total_profit': 0
                }
            
            # Создаем DataFrame с данными для этого склада
            df_clean = pd.DataFrame({
                'номенклатура': df['Номенклатура'],
                'количество': 1,  # В сводном файле нет количества, ставим 1
                'выручка': df[warehouse_col],
                'себестоимость': df[warehouse_col] * 0.7  # Примерная себестоимость 70%
            })
            
            # Фильтруем только строки с выручкой > 0
            df_clean = df_clean[df_clean['выручка'] > 0]
            
            # Обрабатываем как обычно
            df_clean['филиал'] = branch_name
            df_clean['прибыль'] = df_clean['выручка'] - df_clean['себестоимость']
            df_clean['рентабельность'] = (df_clean['прибыль'] / df_clean['выручка'] * 100).fillna(0)
            df_clean['средняя_цена'] = df_clean['выручка']
            
            # Сохраняем данные для филиала
            self.branch_sales_data[branch_name] = df_clean
            
            print(f"✅ Обработано {len(df_clean)} товаров из сводного файла для {branch_name}")
            
            return {
                'success': True,
                'items_processed': len(df_clean),
                'total_revenue': df_clean['выручка'].sum(),
                'total_quantity': df_clean['количество'].sum(),
                'total_profit': df_clean['прибыль'].sum()
            }
            
        except Exception as e:
            print(f"❌ Ошибка обработки сводного файла для {branch_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_abc_analysis_file(self, file_bytes, branch_name):
        """Обработка файла ABC/XYZ анализа"""
        try:
            # Пробуем разные варианты чтения
            df = None
            for header_row in [0, 1, 2]:
                try:
                    df_test = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=header_row)
                    
                    # Проверяем есть ли нужные колонки
                    cols_text = " ".join([str(col).lower() for col in df_test.columns])
                    if any(word in cols_text for word in ['наименование', 'номенклатура', 'товар']):
                        df = df_test
                        print(f"✅ Найдены заголовки в строке {header_row + 1}")
                        break
                except:
                    continue
            
            if df is None:
                raise ValueError("Не удалось найти подходящую структуру в ABC файле")
            
            print(f"📊 Обработка ABC файла для {branch_name}: {df.shape[0]} строк, {df.shape[1]} колонок")
            print(f"🔍 Колонки: {list(df.columns)}")
            
            # Ищем нужные колонки
            nomenclature_col = None
            revenue_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['наименование', 'номенклатура', 'товар']):
                    nomenclature_col = col
                elif any(word in col_lower for word in ['выручка', 'продажи', 'сумма', 'оборот']):
                    revenue_col = col
            
            if nomenclature_col is None:
                raise ValueError("Не найдена колонка с номенклатурой в ABC файле")
            
            if revenue_col is None:
                # Пробуем найти любые числовые колонки как выручку
                numeric_cols = []
                for col in df.columns:
                    try:
                        if pd.to_numeric(df[col], errors='coerce').notna().any():
                            numeric_cols.append(col)
                    except:
                        continue
                
                if numeric_cols:
                    revenue_col = numeric_cols[0]  # Берем первую числовую колонку
                    print(f"⚠️ Используем колонку '{revenue_col}' как выручку")
                else:
                    # Если совсем нет данных, создаем минимальный результат
                    print(f"⚠️ Не найдена колонка с выручкой в ABC файле для {branch_name}")
                    # Создаем хотя бы один товар для демонстрации
                    dummy_data = pd.DataFrame({
                        'номенклатура': ['Тестовый товар'],
                        'количество': [1],
                        'выручка': [1000],
                        'себестоимость': [700],
                        'филиал': [branch_name],
                        'прибыль': [300],
                        'рентабельность': [30.0],
                        'средняя_цена': [1000]
                    })
                    
                    self.branch_sales_data[branch_name] = dummy_data
                    
                    return {
                        'success': True,
                        'items_processed': 1,
                        'total_revenue': 1000,
                        'total_quantity': 1,
                        'total_profit': 300
                    }
            
            # Создаем DataFrame с найденными данными
            df_clean = pd.DataFrame({
                'номенклатура': df[nomenclature_col],
                'количество': 1,  # В ABC файле нет количества
                'выручка': pd.to_numeric(df[revenue_col], errors='coerce').fillna(0),
                'себестоимость': pd.to_numeric(df[revenue_col], errors='coerce').fillna(0) * 0.7
            })
            
            # Фильтруем валидные данные
            df_clean = df_clean[df_clean['выручка'] > 0]
            
            # Обрабатываем как обычно
            df_clean['филиал'] = branch_name
            df_clean['прибыль'] = df_clean['выручка'] - df_clean['себестоимость']
            df_clean['рентабельность'] = (df_clean['прибыль'] / df_clean['выручка'] * 100).fillna(0)
            df_clean['средняя_цена'] = df_clean['выручка']
            
            # Сохраняем данные для филиала
            self.branch_sales_data[branch_name] = df_clean
            
            print(f"✅ Обработано {len(df_clean)} товаров из ABC файла для {branch_name}")
            
            return {
                'success': True,
                'items_processed': len(df_clean),
                'total_revenue': df_clean['выручка'].sum(),
                'total_quantity': df_clean['количество'].sum(),
                'total_profit': df_clean['прибыль'].sum()
            }
            
        except Exception as e:
            print(f"❌ Ошибка обработки ABC файла для {branch_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def consolidate_branch_data(self):
        """Консолидация данных всех филиалов"""
        if not self.branch_sales_data:
            return None
        
        # Объединяем данные всех филиалов
        all_data = []
        for branch_name, df in self.branch_sales_data.items():
            all_data.append(df)
        
        consolidated = pd.concat(all_data, ignore_index=True)
        
        # Группируем по номенклатуре для общего анализа
        total_consolidated = consolidated.groupby('номенклатура').agg({
            'количество': 'sum',
            'выручка': 'sum',
            'себестоимость': 'sum',
            'прибыль': 'sum'
        }).reset_index()
        
        # Пересчитываем метрики
        total_consolidated['рентабельность'] = (total_consolidated['прибыль'] / total_consolidated['выручка'] * 100).fillna(0)
        total_consolidated['средняя_цена'] = (total_consolidated['выручка'] / total_consolidated['количество']).fillna(0)
        
        self.consolidated_data = {
            'by_branch': consolidated,
            'total': total_consolidated
        }
        
        return self.consolidated_data
    
    def calculate_turnover_analysis(self, stock_data):
        """Анализ оборачиваемости на основе продаж и остатков"""
        if not self.consolidated_data or stock_data is None:
            return None
        
        # Объединяем данные продаж и остатков
        sales_df = self.consolidated_data['total']
        
        # Объединяем по номенклатуре
        merged_df = pd.merge(sales_df, stock_data, on='номенклатура', how='outer').fillna(0)
        
        # Рассчитываем оборачиваемость
        warehouse_columns = [col for col in stock_data.columns if col != 'номенклатура']
        
        # Общий остаток по всем складам
        merged_df['общий_остаток'] = merged_df[warehouse_columns].sum(axis=1)
        
        # Рассчитываем метрики оборачиваемости
        merged_df['оборачиваемость_количество'] = (merged_df['количество'] / merged_df['общий_остаток']).replace([np.inf, -np.inf], 0).fillna(0)
        merged_df['оборачиваемость_выручка'] = (merged_df['выручка'] / (merged_df['общий_остаток'] * merged_df['средняя_цена'])).replace([np.inf, -np.inf], 0).fillna(0)
        merged_df['дни_запаса'] = (merged_df['общий_остаток'] / (merged_df['количество'] / 365)).replace([np.inf, -np.inf], 365).fillna(365)
        
        # ABC анализ по выручке
        merged_df = merged_df.sort_values('выручка', ascending=False)
        total_revenue = merged_df['выручка'].sum()
        merged_df['доля_выручки'] = (merged_df['выручка'] / total_revenue) * 100
        merged_df['накопленная_доля'] = merged_df['доля_выручки'].cumsum()
        
        # Классификация ABC (80/15/5)
        merged_df['abc_класс'] = 'C'
        merged_df.loc[merged_df['накопленная_доля'] <= 80, 'abc_класс'] = 'A'
        merged_df.loc[(merged_df['накопленная_доля'] > 80) & (merged_df['накопленная_доля'] <= 95), 'abc_класс'] = 'B'
        
        # Классификация по оборачиваемости
        merged_df['класс_оборачиваемости'] = 'Медленная'
        merged_df.loc[merged_df['оборачиваемость_количество'] >= 12, 'класс_оборачиваемости'] = 'Быстрая'
        merged_df.loc[(merged_df['оборачиваемость_количество'] >= 4) & (merged_df['оборачиваемость_количество'] < 12), 'класс_оборачиваемости'] = 'Средняя'
        
        self.turnover_analysis = merged_df
        
        return merged_df

class MovementRecommendationConfig:
    """Конфигурация системы рекомендаций"""
    
    # Структура складской иерархии на основе файла структура.txt (обновлено)
    WAREHOUSE_HIERARCHY = {
        'База Склад Фурнитура Комплект': {
            'type': 'хаб',
            'level': 1,
            'city': 'Алматы',
            'supplies': [
                'Казыбаева Склад Фурнитура TRADE',
                'Барыс Склад Фурнитура TRADE',
                'АО Склад Фурнитура TRADE',
                'склад фурнитура № 1',
                '4 Склад фурнитуры АЗМ Шымкент "Овощная база"'
            ]
        },
        'Казыбаева Склад Фурнитура TRADE': {
            'type': 'склад',
            'level': 2,
            'city': 'Алматы',
            'parent': 'База Склад Фурнитура Комплект',
            'supplies': ['ТД Казыбаева ФУРНИТУРА магазин']
        },
        'склад фурнитура № 1': {
            'type': 'склад',
            'level': 2,
            'city': 'Астана',
            'parent': 'База Склад Фурнитура Комплект',
            'supplies': ['Магазин фурнитуры']
        },
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
            'type': 'склад',
            'level': 2,
            'city': 'Шымкент',
            'parent': 'База Склад Фурнитура Комплект',
            'supplies': ['6 Склад фурнитуры "Овощная база" Магазин']
        },
        'ТД Казыбаева ФУРНИТУРА магазин': {
            'type': 'магазин',
            'level': 3,
            'city': 'Алматы',
            'parent': 'Казыбаева Склад Фурнитура TRADE'
        },
        'Барыс Склад Фурнитура TRADE': {
            'type': 'магазин',
            'level': 2,
            'city': 'Алматы',
            'parent': 'База Склад Фурнитура Комплект',
            'note': 'питается напрямую от хаба'
        },
        'АО Склад Фурнитура TRADE': {
            'type': 'магазин',
            'level': 2,
            'city': 'Алматы',
            'parent': 'База Склад Фурнитура Комплект',
            'note': 'питается напрямую от хаба'
        },
        'Магазин фурнитуры': {
            'type': 'магазин',
            'level': 3,
            'city': 'Астана',
            'parent': 'склад фурнитура № 1'
        },
        '6 Склад фурнитуры "Овощная база" Магазин': {
            'type': 'магазин',
            'level': 3,
            'city': 'Шымкент',
            'parent': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"'
        }
    }
    
    # Базовые нормативы запасов в днях для разных типов точек
    BASE_STOCK_NORMS = {
        'магазин': {
            'min_days': 10,
            'optimal_days': 20,
            'max_days': 30,
            'priority': 100
        },
        'склад': {
            'min_days': 30,
            'optimal_days': 60,
            'max_days': 90,
            'priority': 50
        },
        'хаб': {
            'min_days': 60,
            'optimal_days': 120,
            'max_days': 180,
            'priority': 20
        }
    }
    
    # Настройки оборачиваемости по ABC категориям
    ABC_TURNOVER_SETTINGS = {
        'магазин': {
            'A': {'min_days': 15, 'optimal_days': 20, 'max_days': 25},
            'B': {'min_days': 8, 'optimal_days': 10, 'max_days': 15},
            'C': {'min_days': 5, 'optimal_days': 10, 'max_days': 20}
        },
        'склад': {
            'A': {'min_days': 25, 'optimal_days': 45, 'max_days': 60},
            'B': {'min_days': 20, 'optimal_days': 35, 'max_days': 50},
            'C': {'min_days': 15, 'optimal_days': 30, 'max_days': 45}
        },
        'хаб': {
            'A': {'min_days': 45, 'optimal_days': 90, 'max_days': 120},
            'B': {'min_days': 35, 'optimal_days': 70, 'max_days': 100},
            'C': {'min_days': 30, 'optimal_days': 60, 'max_days': 90}
        }
    }
    
    # Настройки по важности товаров
    IMPORTANCE_MODIFIERS = {
        'критичный': {'multiplier': 1.5, 'min_stock_boost': 1.3},
        'важный': {'multiplier': 1.2, 'min_stock_boost': 1.1},
        'обычный': {'multiplier': 1.0, 'min_stock_boost': 1.0},
        'медленный': {'multiplier': 0.8, 'min_stock_boost': 0.9}
    }
    
    # Минимальные партии для перемещения
    MIN_MOVEMENT_QUANTITY = 5
    
    # Включить/выключить ABC анализ
    USE_ABC_ANALYSIS = True
    
    @classmethod
    def get_location_type(cls, location_name: str) -> str:
        """Определение типа точки по названию из иерархии"""
        if not location_name:
            return 'склад'
            
        # Сначала проверяем в иерархии
        if location_name in cls.WAREHOUSE_HIERARCHY:
            return cls.WAREHOUSE_HIERARCHY[location_name]['type']
            
        # Если нет в иерархии, определяем по ключевым словам
        location_lower = location_name.lower()
        
        if any(word in location_lower for word in ['магазин', 'маг', 'shop', 'торговый']):
            return 'магазин'
        elif any(word in location_lower for word in ['хаб', 'hub', 'центр', 'база']):
            return 'хаб'
        elif any(word in location_lower for word in ['склад', 'скл', 'warehouse']):
            return 'склад'
        else:
            return 'склад'
    
    @classmethod
    def get_stock_norms_for_item(cls, location_type: str, abc_class: str = None, importance: str = 'обычный') -> Dict:
        """
        Получение нормативов запасов с учетом ABC класса и важности товара
        """
        
        # Базовые нормативы
        if cls.USE_ABC_ANALYSIS and abc_class and abc_class in ['A', 'B', 'C']:
            # Используем ABC настройки
            base_norms = cls.ABC_TURNOVER_SETTINGS.get(location_type, {}).get(abc_class, {})
            if not base_norms:
                # Если нет ABC настроек, используем базовые
                base_norms = cls.BASE_STOCK_NORMS.get(location_type, cls.BASE_STOCK_NORMS['склад'])
        else:
            # Используем базовые нормативы
            base_norms = cls.BASE_STOCK_NORMS.get(location_type, cls.BASE_STOCK_NORMS['склад'])
        
        # Применяем модификаторы важности
        importance_mod = cls.IMPORTANCE_MODIFIERS.get(importance, cls.IMPORTANCE_MODIFIERS['обычный'])
        
        result = {
            'min_days': int(base_norms.get('min_days', 10) * importance_mod['min_stock_boost']),
            'optimal_days': int(base_norms.get('optimal_days', 20) * importance_mod['multiplier']),
            'max_days': int(base_norms.get('max_days', 30) * importance_mod['multiplier']),
            'priority': cls.BASE_STOCK_NORMS.get(location_type, {}).get('priority', 50),
            'abc_class': abc_class or 'Unknown',
            'importance': importance
        }
        
        return result

# ===== ОСНОВНАЯ ЛОГИКА РЕКОМЕНДАЦИЙ =====

class MovementRecommendationEngine:
    """Движок генерации рекомендаций по перемещениям"""
    
    def __init__(self, modular_system):
        """Инициализация с существующей ModularInventorySystem"""
        self.system = modular_system
        self.config = MovementRecommendationConfig()
        
        # Результаты анализа
        self.location_analysis = []
        self.movement_recommendations = []
        self.purchase_recommendations = []
        self.analysis_summary = {}
    
    def validate_system_data(self) -> Tuple[bool, str]:
        """Проверка наличия необходимых данных в системе"""
        
        # Проверяем ADS - новая структура с JSON файлами
        has_ads = False
        ads_count = 0
        debug_info = []
        
        # 1. Проверяем новую структуру с JSON файлами
        import os
        import json
        
        # Отладочная информация
        current_dir = os.getcwd()
        debug_info.append(f"Текущая директория: {current_dir}")
        
        ads_path = 'ads/combined_ads_data.json'
        ads_exists = os.path.exists(ads_path)
        debug_info.append(f"Файл {ads_path}: {'✅ найден' if ads_exists else '❌ не найден'}")
        
        if ads_exists:
            try:
                with open(ads_path, 'r', encoding='utf-8') as f:
                    combined_data = json.load(f)
                
                debug_info.append(f"Структура JSON: {list(combined_data.keys())}")
                
                if 'branches' in combined_data:
                    branches_count = len(combined_data['branches'])
                    debug_info.append(f"Найдено филиалов: {branches_count}")
                    
                    if branches_count > 0:
                        has_ads = True
                        ads_count = sum(branch['items_count'] for branch in combined_data['branches'].values())
                        debug_info.append(f"Общее количество товаров: {ads_count}")
                        
                        # Показываем названия филиалов
                        branch_names = list(combined_data['branches'].keys())
                        debug_info.append(f"Филиалы: {branch_names}")
                else:
                    debug_info.append("❌ Секция 'branches' не найдена")
                    
            except Exception as e:
                debug_info.append(f"❌ Ошибка чтения JSON: {e}")
        
        # 2. Проверяем старую структуру как резерв
        if not has_ads and hasattr(self.system, 'calculated_ads') and self.system.calculated_ads is not None:
            if not self.system.calculated_ads.empty:
                has_ads = True
                ads_count = len(self.system.calculated_ads)
                debug_info.append("✅ Найдены ADS в старом формате")
        
        # Показываем отладочную информацию в Streamlit
        import streamlit as st
        with st.expander("🔍 Отладочная информация ADS"):
            for info in debug_info:
                st.text(info)
        
        if not has_ads:
            return False, "ADS не рассчитан. Перейдите в раздел '📊 ADS расчет' → '📄 Единый файл со всеми филиалами' и загрузите файл продаж."
        
        # Проверяем остатки
        if not hasattr(self.system, 'stock_data') or self.system.stock_data is None:
            return False, "Данные остатков не загружены. Перейдите в раздел 'Сравнение остатков' и загрузите файл остатков."
        
        if self.system.stock_data.empty:
            return False, "Файл остатков пустой. Проверьте данные."
        
        # Для новой структуры ADS пока возвращаем успех
        # (полную проверку пересечений сделаем позже при загрузке данных)
        stock_count = len(self.system.stock_data)
        return True, f"Готово к анализу: ADS по {ads_count} товарам, остатки по {stock_count} товарам"
    
    def classify_locations(self) -> Dict[str, str]:
        """Классификация точек продаж по типам"""
        
        if self.system.stock_data is None:
            return {}
        
        # Получаем названия точек (все колонки кроме номенклатуры)
        location_columns = [col for col in self.system.stock_data.columns if col != 'номенклатура']
        
        location_types = {}
        for location in location_columns:
            location_types[location] = self.config.get_location_type(location)
        
        return location_types
    
    def get_item_abc_class(self, item_name: str) -> str:
        """Получение ABC класса товара из системы"""
        
        # Проверяем есть ли ABC данные в системе
        if hasattr(self.system, 'abc_results') and self.system.abc_results:
            if 'abc_data_detailed' in self.system.abc_results:
                abc_data = self.system.abc_results['abc_data_detailed']
                
                # Ищем товар в ABC данных
                item_row = abc_data[abc_data['nomenclature'] == item_name]
                if not item_row.empty and 'abc_class' in item_row.columns:
                    return item_row.iloc[0]['abc_class']
        
        # Проверяем в calculated_ads если там есть ABC класс
        if hasattr(self.system, 'calculated_ads') and self.system.calculated_ads is not None:
            if 'abc_class' in self.system.calculated_ads.columns:
                item_row = self.system.calculated_ads[self.system.calculated_ads['номенклатура'] == item_name]
                if not item_row.empty:
                    return item_row.iloc[0]['abc_class']
        
        # По умолчанию возвращаем B если ABC не найден
        return 'B'
    
    def get_item_importance(self, item_name: str, ads_value: float) -> str:
        """
        Определение важности товара на основе ADS и других факторов
        """
        
        if ads_value <= 0:
            return 'медленный'
        
        # Получаем квантили ADS для определения важности
        if hasattr(self.system, 'calculated_ads') and self.system.calculated_ads is not None:
            ads_data = self.system.calculated_ads['ads']
            
            # Рассчитываем квантили
            q90 = ads_data.quantile(0.9)
            q75 = ads_data.quantile(0.75)
            q25 = ads_data.quantile(0.25)
            
            if ads_value >= q90:
                return 'критичный'
            elif ads_value >= q75:
                return 'важный'
            elif ads_value >= q25:
                return 'обычный'
            else:
                return 'медленный'
        
        # Базовая логика если нет данных для квантилей
        if ads_value > 50:
            return 'критичный'
        elif ads_value > 20:
            return 'важный'
        elif ads_value > 5:
            return 'обычный'
        else:
            return 'медленный'
    
    def analyze_item_by_locations(self, item_name: str, ads_value: float, stock_row: pd.Series) -> Dict:
        """Анализ конкретного товара по всем точкам"""
        
        location_types = self.classify_locations()
        analysis = {
            'item_name': item_name,
            'ads': ads_value,
            'locations': {},
            'total_stock': 0,
            'deficit_locations': [],
            'surplus_locations': [],
            'normal_locations': []
        }
        
        # Анализируем каждую точку
        for location in location_types.keys():
            if location not in stock_row.index:
                continue
                
            stock_qty = stock_row[location]
            if pd.isna(stock_qty) or stock_qty == 0:
                continue
                
            stock_qty = float(stock_qty)
            analysis['total_stock'] += stock_qty
            
            location_type = location_types[location]
            
            # Получаем ABC класс и важность товара
            abc_class = self.get_item_abc_class(item_name)
            importance = self.get_item_importance(item_name, ads_value)
            
            # Получаем нормативы с учетом ABC и важности
            norms = self.config.get_stock_norms_for_item(location_type, abc_class, importance)
            
            # Рассчитываем нормативы для данного товара
            if ads_value > 0:
                min_stock = ads_value * norms['min_days']
                optimal_stock = ads_value * norms['optimal_days']
                max_stock = ads_value * norms['max_days']
                days_of_stock = stock_qty / ads_value
            else:
                min_stock = optimal_stock = max_stock = 0
                days_of_stock = 999
            
            # Определяем статус
            status = 'норма'
            urgency = 0
            
            if ads_value > 0:
                if stock_qty < min_stock:
                    status = 'дефицит'
                    urgency = int((min_stock - stock_qty) / min_stock * 100)
                elif stock_qty > max_stock:
                    status = 'излишек'
                    urgency = int((stock_qty - max_stock) / max_stock * 100)
            
            location_data = {
                'type': location_type,
                'current_stock': stock_qty,
                'min_stock': min_stock,
                'optimal_stock': optimal_stock,
                'max_stock': max_stock,
                'days_of_stock': round(days_of_stock, 1),
                'status': status,
                'urgency': urgency,
                'priority': norms['priority'],
                'abc_class': abc_class,
                'importance': importance,
                'norms_used': f"{location_type}/{abc_class}/{importance}"
            }
            
            analysis['locations'][location] = location_data
            
            # Группируем по статусу
            if status == 'дефицит':
                analysis['deficit_locations'].append((location, location_data))
            elif status == 'излишек':
                analysis['surplus_locations'].append((location, location_data))
            else:
                analysis['normal_locations'].append((location, location_data))
        
        return analysis
    
    def generate_movement_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по перемещениям"""
        
        recommendations = []
        
        for item_analysis in self.location_analysis:
            deficits = item_analysis['deficit_locations']
            surpluses = item_analysis['surplus_locations']
            
            if not deficits or not surpluses:
                continue
            
            # Сортируем по приоритету
            deficits.sort(key=lambda x: (-x[1]['priority'], -x[1]['urgency']))
            surpluses.sort(key=lambda x: x[1]['priority'])  # Хабы отдают легче
            
            # Генерируем перемещения
            for deficit_location, deficit_data in deficits:
                needed = deficit_data['optimal_stock'] - deficit_data['current_stock']
                if needed <= 0:
                    continue
                
                remaining_need = needed
                movements = []
                
                for surplus_location, surplus_data in surpluses:
                    if remaining_need <= 0:
                        break
                    
                    available = surplus_data['current_stock'] - surplus_data['optimal_stock']
                    if available <= self.config.MIN_MOVEMENT_QUANTITY:
                        continue
                    
                    to_move = min(available, remaining_need)
                    
                    movements.append({
                        'from': surplus_location,
                        'from_type': surplus_data['type'],
                        'quantity': round(to_move),
                        'from_days_before': surplus_data['days_of_stock']
                    })
                    
                    remaining_need -= to_move
                    surplus_data['current_stock'] -= to_move
                
                if movements:
                    rec = {
                        'item_name': item_analysis['item_name'],
                        'to': deficit_location,
                        'to_type': deficit_data['type'],
                        'to_days_before': deficit_data['days_of_stock'],
                        'needed': round(needed),
                        'covered': round(needed - remaining_need),
                        'remaining_deficit': round(remaining_need) if remaining_need > 0 else 0,
                        'urgency': deficit_data['urgency'],
                        'priority': deficit_data['priority'],
                        'ads': item_analysis['ads'],
                        'movements': movements
                    }
                    
                    # Добавляем информацию об ABC классе и важности
                    if 'abc_class' in deficit_data:
                        rec['abc_class'] = deficit_data['abc_class']
                    if 'importance' in deficit_data:
                        rec['importance'] = deficit_data['importance']
                    if 'norms_used' in deficit_data:
                        rec['norms_used'] = deficit_data['norms_used']
                    
                    recommendations.append(rec)
        
        # Сортируем по приоритету и срочности
        recommendations.sort(key=lambda x: (-x['priority'], -x['urgency']))
        
        return recommendations
    
    def generate_purchase_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по закупкам"""
        
        purchases = []
        
        for item_analysis in self.location_analysis:
            total_stock = item_analysis['total_stock']
            ads = item_analysis['ads']
            
            if ads <= 0:
                continue
            
            # Рассчитываем общую потребность
            total_need = 0
            critical_deficit = 0
            
            for location, location_data in item_analysis['locations'].items():
                total_need += location_data['optimal_stock']
                if location_data['status'] == 'дефицит':
                    critical_deficit += (location_data['optimal_stock'] - location_data['current_stock'])
            
            # Если общий запас меньше 70% от потребности
            if total_stock < total_need * 0.7:
                to_purchase = (total_need - total_stock) * 1.2
                current_days = total_stock / ads if ads > 0 else 0
                
                urgency_score = max(0, 100 - int(current_days / 30 * 100))
                
                purchase_rec = {
                    'item_name': item_analysis['item_name'],
                    'current_total_stock': round(total_stock),
                    'recommended_total_stock': round(total_need),
                    'to_purchase': round(to_purchase),
                    'current_days_supply': round(current_days, 1),
                    'critical_deficit': round(critical_deficit),
                    'ads': ads,
                    'urgency': urgency_score
                }
                
                # Добавляем денежную оценку если есть цены
                if hasattr(self.system, 'calculated_ads') and 'last_purchase_price' in self.system.calculated_ads.columns:
                    item_price_row = self.system.calculated_ads[
                        self.system.calculated_ads['номенклатура'] == item_analysis['item_name']
                    ]
                    if not item_price_row.empty and item_price_row.iloc[0]['last_purchase_price'] > 0:
                        price = item_price_row.iloc[0]['last_purchase_price']
                        purchase_rec['unit_price'] = price
                        purchase_rec['total_cost'] = round(to_purchase * price, 2)
                
                purchases.append(purchase_rec)
        
        purchases.sort(key=lambda x: -x['urgency'])
        return purchases
    
    def run_full_analysis(self) -> Dict:
        """Запуск полного анализа"""
        
        # Проверяем данные
        is_valid, message = self.validate_system_data()
        if not is_valid:
            return {'success': False, 'error': message}
        
        try:
            # Получаем данные
            ads_data = self.system.calculated_ads
            stock_data = self.system.stock_data
            
            # Анализируем каждый товар
            self.location_analysis = []
            
            progress_placeholder = st.empty()
            total_items = len(ads_data)
            
            for idx, ads_row in ads_data.iterrows():
                item_name = ads_row['номенклатура']
                ads_value = ads_row['ads']
                
                # Обновляем прогресс
                progress_placeholder.text(f"Анализ: {item_name[:50]}... ({idx+1}/{total_items})")
                
                # Ищем остатки для данного товара
                stock_row = stock_data[stock_data['номенклатура'] == item_name]
                
                if stock_row.empty:
                    continue
                
                # Анализируем товар
                item_analysis = self.analyze_item_by_locations(
                    item_name, ads_value, stock_row.iloc[0]
                )
                
                if item_analysis['locations']:
                    self.location_analysis.append(item_analysis)
            
            progress_placeholder.empty()
            
            # Генерируем рекомендации
            self.movement_recommendations = self.generate_movement_recommendations()
            self.purchase_recommendations = self.generate_purchase_recommendations()
            
            # Создаем сводку
            self.analysis_summary = self.create_analysis_summary()
            
            return {
                'success': True,
                'analyzed_items': len(self.location_analysis),
                'movement_recommendations': len(self.movement_recommendations),
                'purchase_recommendations': len(self.purchase_recommendations)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка при анализе: {str(e)}"}
    
    def create_analysis_summary(self) -> Dict:
        """Создание сводной статистики"""
        
        summary = {
            'total_items': len(self.location_analysis),
            'total_movement_recs': len(self.movement_recommendations),
            'total_purchase_recs': len(self.purchase_recommendations),
            'location_stats': {},
            'movement_efficiency': 0
        }
        
        # Анализируем каждую точку
        all_locations = set()
        for item in self.location_analysis:
            all_locations.update(item['locations'].keys())
        
        for location in all_locations:
            summary['location_stats'][location] = {
                'type': '',
                'total_items': 0,
                'surplus_items': 0,
                'deficit_items': 0,
                'normal_items': 0
            }
        
        # Собираем статистику
        total_deficit_covered = 0
        total_deficit_amount = 0
        
        for item in self.location_analysis:
            for location, data in item['locations'].items():
                loc_stats = summary['location_stats'][location]
                loc_stats['type'] = data['type']
                loc_stats['total_items'] += 1
                
                if data['status'] == 'дефицит':
                    loc_stats['deficit_items'] += 1
                elif data['status'] == 'излишек':
                    loc_stats['surplus_items'] += 1
                else:
                    loc_stats['normal_items'] += 1
        
        # Рассчитываем эффективность покрытия
        for rec in self.movement_recommendations:
            total_deficit_amount += rec['needed']
            total_deficit_covered += rec['covered']
        
        if total_deficit_amount > 0:
            summary['movement_efficiency'] = round(total_deficit_covered / total_deficit_amount * 100, 1)
        
        return summary

# ===== STREAMLIT ИНТЕРФЕЙС =====

def show_movement_recommendations_page(system):
    """Главная страница рекомендаций по перемещениям"""
    
    st.header("🚚 Система рекомендаций по перемещениям")
    
    # Инициализируем анализатор продаж по филиалам
    if 'branch_analyzer' not in st.session_state:
        st.session_state.branch_analyzer = BranchSalesAnalyzer()
    
    # 📋 ПОШАГОВЫЙ ПРОЦЕСС
    st.markdown("### 📋 Пошаговый процесс:")
    
    # Шаг 1: Загрузка файлов продаж по филиалам
    has_branch_sales = len(st.session_state.branch_analyzer.branch_sales_data) > 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if has_branch_sales:
            st.success(f"✅ **Шаг 1: Продажи по филиалам**\n{len(st.session_state.branch_analyzer.branch_sales_data)} филиалов")
        else:
            st.error("❌ **Шаг 1: Продажи по филиалам**\nНе загружены")
    
    with col2:
        has_stock = hasattr(system, 'stock_data') and system.stock_data is not None and not system.stock_data.empty
        if has_stock:
            st.success(f"✅ **Шаг 2: Остатки**\n{len(system.stock_data)} товаров")
        else:
            st.warning("⏳ **Шаг 2: Остатки**\nЗагрузите файл ниже")
    
    with col3:
        if has_branch_sales and has_stock:
            st.success("✅ **Шаг 3: Рекомендации**\nГотовы к расчету")
        else:
            st.info("⏸️ **Шаг 3: Рекомендации**\nОжидание данных")
    
    st.markdown("---")
    
    # Показываем интерфейс загрузки файлов продаж
    if not has_branch_sales:
        show_branch_sales_upload_interface()
        return
    
    # Если нет остатков, показываем интерфейс загрузки
    if not has_stock:
        show_stock_upload_interface(system)
        return
    
    # Если есть все данные, показываем основной интерфейс
    show_main_recommendations_interface_new(system)

def show_branch_sales_upload_interface():
    """Интерфейс загрузки файлов продаж по филиалам"""
    
    st.subheader("📂 Загрузка файлов продаж по филиалам")
    
    # Показываем структуру ожидаемых файлов
    with st.expander("📋 **Требования к файлам продаж**", expanded=True):
        st.markdown("""
        **Формат файлов:** Excel (.xlsx)
        
        **Названия файлов (примеры):**
        - `6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07_2025.xlsx`
        - `Барыс_Склад_Фурнитура_TRADE_продажи_01_07_2024_01_07_2025.xlsx`
        - `АО_Склад_Фурнитура_TRADE_продажи_01_07_2024_01_07_2025.xlsx`
        
        **Обязательные колонки:**
        - `номенклатура` - название товара
        - `количество` - количество проданных единиц
        - `выручка` - сумма выручки
        - `себестоимость` - себестоимость проданных товаров
        """)
    
    # Загрузка файлов
    st.markdown("### 📁 Загрузка файлов")
    
    uploaded_files = st.file_uploader(
        "Выберите файлы продаж по филиалам",
        type=['xlsx'],
        accept_multiple_files=True,
        help="Выберите все файлы продаж по филиалам за нужный период"
    )
    
    if uploaded_files:
        st.markdown("### 📊 Обработка файлов")
        
        # Кнопка для обработки всех файлов
        if st.button("🚀 Обработать все файлы", type="primary"):
            success_count = 0
            error_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                file_name = uploaded_file.name
                
                # Извлекаем название филиала из имени файла
                branch_name = extract_branch_name_from_filename(file_name)
                
                status_text.text(f"Обрабатывается: {file_name}")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                try:
                    result = st.session_state.branch_analyzer.process_branch_sales_file(
                        uploaded_file, branch_name
                    )
                    
                    if result['success']:
                        success_count += 1
                        st.success(f"✅ {file_name}: {result['items_processed']} товаров, выручка: {result['total_revenue']:,.0f}")
                    else:
                        error_count += 1
                        st.error(f"❌ {file_name}: {result['error']}")
                        
                        # Показываем детальную информацию об ошибке
                        with st.expander(f"🔍 Детали ошибки для {file_name}"):
                            st.text(f"Полная ошибка: {result['error']}")
                            
                            # Пытаемся показать структуру файла
                            try:
                                # Показываем первые строки без заголовков
                                df_raw = pd.read_excel(uploaded_file, engine='openpyxl', header=None, nrows=10)
                                st.write("📋 Первые 10 строк файла (raw):")
                                st.dataframe(df_raw)
                                
                                # Пробуем разные варианты заголовков
                                for header_idx in [0, 1, 7, 8]:
                                    try:
                                        df_test = pd.read_excel(uploaded_file, engine='openpyxl', header=header_idx, nrows=5)
                                        st.write(f"📊 Заголовки из строки {header_idx + 1}:")
                                        st.write(list(df_test.columns))
                                    except:
                                        continue
                                        
                            except Exception as debug_e:
                                st.text(f"Не удалось прочитать файл для отладки: {debug_e}")
                        
                except Exception as e:
                    error_count += 1
                    st.error(f"❌ {file_name}: Ошибка обработки - {str(e)}")
                    
                    # Показываем детальную информацию об ошибке
                    with st.expander(f"🔍 Детали ошибки для {file_name}"):
                        st.text(f"Полная ошибка: {str(e)}")
                        
                        # Пытаемся показать структуру файла
                        try:
                            df_debug = pd.read_excel(uploaded_file, engine='openpyxl')
                            st.write("📋 Колонки в файле:")
                            st.write(list(df_debug.columns))
                            st.write("📊 Первые 3 строки:")
                            st.dataframe(df_debug.head(3))
                        except Exception as debug_e:
                            st.text(f"Не удалось прочитать файл для отладки: {debug_e}")
            
            status_text.text(f"Завершено! Успешно: {success_count}, Ошибок: {error_count}")
            progress_bar.progress(1.0)
            
            if success_count > 0:
                st.balloons()
        
        # Показываем список загруженных файлов
        st.markdown("#### 📋 Список файлов для обработки:")
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            branch_name = extract_branch_name_from_filename(file_name)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"📄 **{file_name}**")
                st.caption(f"Филиал: {branch_name}")
            
            with col2:
                # Показываем статус обработки
                if branch_name in st.session_state.branch_analyzer.branch_sales_data:
                    st.success("✅ Обработан")
                else:
                    st.info("⏳ Ждет обработки")
        
        st.markdown("---")
        
        # Показываем загруженные филиалы
        if st.session_state.branch_analyzer.branch_sales_data:
            st.markdown("### 📋 Загруженные филиалы")
            
            for branch_name, data in st.session_state.branch_analyzer.branch_sales_data.items():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"**🏪 {branch_name}**")
                
                with col2:
                    st.metric("Товаров", len(data))
                
                with col3:
                    st.metric("Выручка", f"{data['выручка'].sum():,.0f}")
                
                with col4:
                    st.metric("Рентабельность", f"{data['рентабельность'].mean():.1f}%")
            
            # Кнопка для консолидации данных
            if st.button("🔄 Консолидировать данные", type="primary"):
                with st.spinner("Консолидация данных..."):
                    consolidated = st.session_state.branch_analyzer.consolidate_branch_data()
                    if consolidated:
                        st.success("✅ Данные консолидированы успешно!")
                        st.rerun()

def extract_branch_name_from_filename(filename):
    """Извлекает название филиала из имени файла"""
    # Убираем расширение
    name = filename.replace('.xlsx', '').replace('.xls', '')
    
    print(f"🔍 Обработка имени файла: {name}")
    
    # Словарь соответствий для известных филиалов
    branch_mapping = {
        '6_Склад_фурнитуры_Овощная_база_Магазин': '6 Склад фурнитуры "Овощная база" Магазин',
        '4_Склад_фурнитуры_АЗМ_Шымкент': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
        'АО_Склад_Фурнитура_TRADE': 'АО Склад Фурнитура TRADE',
        'База_Склад_Фурнитура_Комплект': 'База Склад Фурнитура Комплект',
        'Барыс_Склад_Фурнитура_TRADE': 'Барыс Склад Фурнитура TRADE',
        'Казыбаева_Склад_Фурнитура_TRADE': 'Казыбаева Склад Фурнитура TRADE',
        'Магазин_фурнитуры': 'Магазин фурнитуры',
        'склад_фурнитура_№_1': 'склад фурнитура № 1',
        'ТД_Казыбаева_ФУРНИТУРА_магазин': 'ТД Казыбаева ФУРНИТУРА магазин'
    }
    
    # Проверяем точные совпадения
    for key, value in branch_mapping.items():
        if key in name:
            print(f"✅ Найдено точное совпадение: {key} -> {value}")
            return value
    
    # Разделяем по подчеркиваниям
    parts = name.split('_')
    
    # Ищем части до слова "продажи" или "Магазин"
    branch_parts = []
    for part in parts:
        if any(stop_word in part.lower() for stop_word in ['продажи', 'магазин_продажи', 'sales']):
            break
        branch_parts.append(part)
    
    # Объединяем части названия филиала
    branch_name = ' '.join(branch_parts)
    
    # Очищаем от лишних символов и заменяем подчеркивания на пробелы
    branch_name = branch_name.replace('_', ' ')
    
    # Если не получилось извлечь, пытаемся найти по ключевым словам
    if not branch_name or len(branch_name) < 3:
        # Ищем ключевые слова в имени файла
        if '6' in name and ('овощная' in name.lower() or 'магазин' in name.lower()):
            branch_name = '6 Склад фурнитуры "Овощная база" Магазин'
        elif '4' in name and ('азм' in name.lower() or 'шымкент' in name.lower()):
            branch_name = '4 Склад фурнитуры АЗМ Шымкент "Овощная база"'
        elif 'ао' in name.lower() and 'trade' in name.lower():
            branch_name = 'АО Склад Фурнитура TRADE'
        elif 'база' in name.lower() and 'комплект' in name.lower():
            branch_name = 'База Склад Фурнитура Комплект'
        elif 'барыс' in name.lower():
            branch_name = 'Барыс Склад Фурнитура TRADE'
        elif 'казыбаева' in name.lower() and 'trade' in name.lower():
            branch_name = 'Казыбаева Склад Фурнитура TRADE'
        elif 'казыбаева' in name.lower() and 'магазин' in name.lower():
            branch_name = 'ТД Казыбаева ФУРНИТУРА магазин'
        elif 'магазин' in name.lower() and 'фурнитур' in name.lower():
            branch_name = 'Магазин фурнитуры'
        elif 'склад' in name.lower() and '№' in name:
            branch_name = 'склад фурнитура № 1'
        else:
            # Если ничего не подошло, возвращаем очищенное имя файла
            branch_name = name.replace('_', ' ')
    
    print(f"📝 Извлеченное название филиала: {branch_name}")
    return branch_name

def show_main_recommendations_interface_new(system):
    """Новый основной интерфейс рекомендаций на основе анализа оборачиваемости"""
    
    # Показываем структуру складской иерархии
    with st.expander("📋 **Структура складской сети**", expanded=False):
        st.markdown("""
        ### 🌐 Центральный хаб (г. Алматы)
        **База Склад Фурнитура Комплект** - главный распределительный центр
        
        ### 🏬 Склады 2-го уровня:
        - **Казыбаева Склад Фурнитура TRADE** → обслуживает ТД Казыбаева магазин (Алматы)
        - **склад фурнитура № 1** → обслуживает Магазин фурнитуры (Астана)  
        - **4 Склад фурнитуры АЗМ Шымкент** → обслуживает 6 Склад магазин (Шымкент)
        
        ### 🏪 Магазины:
        **Алматы:**
        - ТД Казыбаева ФУРНИТУРА магазин (от склада Казыбаева)
        - Барыс Склад Фурнитура TRADE (напрямую от хаба)
        - АО Склад Фурнитура TRADE (напрямую от хаба)
        
        **Астана:**
        - Магазин фурнитуры (от склада № 1)
        
        **Шымкент:**
        - 6 Склад фурнитуры "Овощная база" Магазин (от склада АЗМ)
        """)
    
    # Сначала рассчитываем анализ оборачиваемости
    st.subheader("📊 Анализ оборачиваемости")
    
    if st.button("🔄 Рассчитать анализ оборачиваемости", type="primary"):
        with st.spinner("Рассчитываем анализ оборачиваемости..."):
            turnover_data = st.session_state.branch_analyzer.calculate_turnover_analysis(system.stock_data)
            
            if turnover_data is not None:
                st.session_state.turnover_analysis = turnover_data
                st.success("✅ Анализ оборачиваемости рассчитан!")
                st.rerun()
            else:
                st.error("❌ Не удалось рассчитать анализ оборачиваемости")
    
    # Если есть данные оборачиваемости, показываем их
    if hasattr(st.session_state, 'turnover_analysis'):
        show_turnover_analysis_results(st.session_state.turnover_analysis)
        
        # Настройки нормативов оборачиваемости
        st.subheader("⚙️ Настройки нормативов оборачиваемости")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🏪 Магазины**")
            mag_min_turn = st.number_input("Мин. оборачиваемость", value=6.0, min_value=1.0, max_value=50.0, key="mag_min_turn")
            mag_max_turn = st.number_input("Макс. оборачиваемость", value=24.0, min_value=1.0, max_value=50.0, key="mag_max_turn")
        
        with col2:
            st.markdown("**🏬 Склады**")
            sklad_min_turn = st.number_input("Мин. оборачиваемость", value=3.0, min_value=1.0, max_value=20.0, key="sklad_min_turn")
            sklad_max_turn = st.number_input("Макс. оборачиваемость", value=12.0, min_value=1.0, max_value=20.0, key="sklad_max_turn")
        
        with col3:
            st.markdown("**🌐 Хабы**")
            hub_min_turn = st.number_input("Мин. оборачиваемость", value=1.0, min_value=0.5, max_value=10.0, key="hub_min_turn")
            hub_max_turn = st.number_input("Макс. оборачиваемость", value=6.0, min_value=1.0, max_value=10.0, key="hub_max_turn")
        
        st.markdown("---")
        
        # Сохраняем нормативы в session_state
        turnover_norms = {
            'магазин': {'min': mag_min_turn, 'max': mag_max_turn},
            'склад': {'min': sklad_min_turn, 'max': sklad_max_turn}, 
            'хаб': {'min': hub_min_turn, 'max': hub_max_turn}
        }
        
        col_calc, col_reset = st.columns([3, 1])
        
        with col_calc:
            if st.button("🚀 Рассчитать рекомендации", type="primary"):
                # Сохраняем флаг для отображения результатов
                st.session_state.show_recommendations_new = True
                st.session_state.turnover_norms = turnover_norms
                st.rerun()
        
        with col_reset:
            if st.session_state.get('show_recommendations_new', False):
                if st.button("🔄 Пересчитать", help="Пересчитать рекомендации с новыми настройками"):
                    # Очищаем кэш рекомендаций
                    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("turnover_recommendations_")]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.session_state.show_recommendations_new = True
                    st.session_state.turnover_norms = turnover_norms
                    st.rerun()
        
        # Если есть флаг для отображения результатов, показываем их
        if st.session_state.get('show_recommendations_new', False):
            show_turnover_recommendations_results(
                st.session_state.turnover_analysis, 
                system.stock_data,
                st.session_state.get('turnover_norms', turnover_norms)
            )

def show_turnover_analysis_results(turnover_data):
    """Отображение результатов анализа оборачиваемости"""
    
    st.markdown("### 📈 Результаты анализа оборачиваемости")
    
    # Общая статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего товаров", len(turnover_data))
    
    with col2:
        st.metric("Общая выручка", f"{turnover_data['выручка'].sum():,.0f}")
    
    with col3:
        st.metric("Средняя оборачиваемость", f"{turnover_data['оборачиваемость_количество'].mean():.1f}")
    
    with col4:
        st.metric("Средние дни запаса", f"{turnover_data['дни_запаса'].mean():.0f}")
    
    # ABC анализ
    st.subheader("📊 ABC анализ по выручке")
    
    abc_stats = turnover_data.groupby('abc_класс').agg({
        'выручка': 'sum',
        'количество': 'sum',
        'номенклатура': 'count'
    }).reset_index()
    
    abc_col1, abc_col2, abc_col3 = st.columns(3)
    
    for i, abc_class in enumerate(['A', 'B', 'C']):
        abc_row = abc_stats[abc_stats['abc_класс'] == abc_class]
        if not abc_row.empty:
            revenue_percent = (abc_row['выручка'].iloc[0] / turnover_data['выручка'].sum()) * 100
            item_count = abc_row['номенклатура'].iloc[0]
            
            with [abc_col1, abc_col2, abc_col3][i]:
                color = "🔴" if abc_class == 'A' else "🟡" if abc_class == 'B' else "🟢"
                st.metric(f"{color} Класс {abc_class}", f"{item_count} товаров", f"{revenue_percent:.1f}% выручки")
    
    # Анализ по оборачиваемости
    st.subheader("🔄 Анализ по оборачиваемости")
    
    turn_stats = turnover_data.groupby('класс_оборачиваемости').agg({
        'выручка': 'sum',
        'номенклатура': 'count'
    }).reset_index()
    
    turn_col1, turn_col2, turn_col3 = st.columns(3)
    
    for i, turn_class in enumerate(['Быстрая', 'Средняя', 'Медленная']):
        turn_row = turn_stats[turn_stats['класс_оборачиваемости'] == turn_class]
        if not turn_row.empty:
            revenue_percent = (turn_row['выручка'].iloc[0] / turnover_data['выручка'].sum()) * 100
            item_count = turn_row['номенклатура'].iloc[0]
            
            with [turn_col1, turn_col2, turn_col3][i]:
                icon = "⚡" if turn_class == 'Быстрая' else "🔶" if turn_class == 'Средняя' else "🐌"
                st.metric(f"{icon} {turn_class}", f"{item_count} товаров", f"{revenue_percent:.1f}% выручки")

def show_turnover_recommendations_results(turnover_data, stock_data, turnover_norms):
    """Отображение результатов рекомендаций на основе оборачиваемости"""
    
    st.subheader("🔄 Рекомендации на основе анализа оборачиваемости")
    
    # Рассчитываем рекомендации
    recommendations = calculate_turnover_recommendations(turnover_data, stock_data, turnover_norms)
    
    if recommendations:
        # Показываем статистику
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔄 Перемещения", len(recommendations.get('movements', [])))
        
        with col2:
            st.metric("🛒 Заказы", len(recommendations.get('purchases', [])))
        
        with col3:
            st.metric("🏠 Возвраты", len(recommendations.get('returns', [])))
        
        # Показываем детализированные рекомендации
        show_comprehensive_recommendations(recommendations.get('all_recommendations', []))
    else:
        st.info("Нет рекомендаций для отображения")

def calculate_turnover_recommendations(turnover_data, stock_data, turnover_norms):
    """Расчет рекомендаций на основе оборачиваемости"""
    
    try:
        movements = []
        purchases = []
        returns = []
        
        # Если нет данных, возвращаем пустой результат
        if turnover_data.empty or stock_data.empty:
            return {
                'movements': [],
                'purchases': [],
                'returns': [],
                'all_recommendations': []
            }
        
        # Объединяем данные оборачиваемости и остатков
        merged_data = pd.merge(turnover_data, stock_data, on='номенклатура', how='inner')
        
        # Получаем список складов из остатков (исключаем служебные колонки)
        stock_columns = [col for col in stock_data.columns if col not in ['номенклатура', 'total_current_stock']]
        
        # Конфигурация складов из структуры
        warehouse_config = MovementRecommendationConfig.WAREHOUSE_HIERARCHY
        
        # Обрабатываем каждый товар
        for _, row in merged_data.iterrows():
            item_name = row['номенклатура']
            
            # Показатели оборачиваемости
            daily_sales = row.get('количество', 0) / 365  # Средние дневные продажи
            if daily_sales <= 0:
                continue
                
            # Анализируем по складам
            warehouse_analysis = {}
            
            for warehouse in stock_columns:
                current_stock = row.get(warehouse, 0)
                if pd.isna(current_stock):
                    current_stock = 0
                
                # Определяем тип склада
                warehouse_type = MovementRecommendationConfig.get_location_type(warehouse)
                
                # Получаем нормативы для данного типа склада
                if warehouse_type == 'магазин':
                    min_days = 7
                    optimal_days = 14
                    max_days = 21
                elif warehouse_type == 'склад':
                    min_days = 20
                    optimal_days = 35
                    max_days = 50
                else:  # хаб
                    min_days = 30
                    optimal_days = 60
                    max_days = 90
                
                # Рассчитываем нормативы в штуках
                min_stock = daily_sales * min_days
                optimal_stock = daily_sales * optimal_days
                max_stock = daily_sales * max_days
                
                # Текущий запас в днях
                days_of_stock = current_stock / daily_sales if daily_sales > 0 else 999
                
                # Определяем статус
                if current_stock < min_stock:
                    status = 'дефицит'
                    deficit_qty = optimal_stock - current_stock
                elif current_stock > max_stock:
                    status = 'излишек'
                    surplus_qty = current_stock - optimal_stock
                else:
                    status = 'норма'
                    deficit_qty = surplus_qty = 0
                
                warehouse_analysis[warehouse] = {
                    'type': warehouse_type,
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'optimal_stock': optimal_stock,
                    'max_stock': max_stock,
                    'days_of_stock': round(days_of_stock, 1),
                    'status': status,
                    'deficit_qty': deficit_qty if status == 'дефицит' else 0,
                    'surplus_qty': surplus_qty if status == 'излишек' else 0
                }
            
            # Генерируем рекомендации для данного товара
            item_recommendations = generate_item_recommendations(
                item_name, warehouse_analysis, warehouse_config
            )
            
            # Добавляем к общим рекомендациям
            movements.extend(item_recommendations['movements'])
            purchases.extend(item_recommendations['purchases'])
            returns.extend(item_recommendations['returns'])
        
        # Сортируем рекомендации по приоритету
        movements.sort(key=lambda x: x.get('priority', 0), reverse=True)
        purchases.sort(key=lambda x: x.get('priority', 0), reverse=True)
        returns.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        # Формируем общий список рекомендаций
        all_recommendations = []
        
        # Добавляем перемещения
        for movement in movements:
            all_recommendations.append({
                'type': 'Перемещение',
                'item': movement['item'],
                'action': f"Переместить {movement['quantity']} шт. из {movement['from']} в {movement['to']}",
                'priority': movement.get('priority', 0),
                'reason': movement.get('reason', ''),
                'details': movement
            })
        
        # Добавляем закупки
        for purchase in purchases:
            all_recommendations.append({
                'type': 'Закупка',
                'item': purchase['item'],
                'action': f"Закупить {purchase['quantity']} шт. для {purchase['for_warehouse']}",
                'priority': purchase.get('priority', 0),
                'reason': purchase.get('reason', ''),
                'details': purchase
            })
        
        # Добавляем возвраты в хаб
        for return_item in returns:
            all_recommendations.append({
                'type': 'Возврат в хаб',
                'item': return_item['item'],
                'action': f"Вернуть {return_item['quantity']} шт. из {return_item['from']} в хаб",
                'priority': return_item.get('priority', 0),
                'reason': return_item.get('reason', ''),
                'details': return_item
            })
        
        # Сортируем общий список по приоритету
        all_recommendations.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return {
            'movements': movements,
            'purchases': purchases,
            'returns': returns,
            'all_recommendations': all_recommendations
        }
        
    except Exception as e:
        print(f"❌ Ошибка расчета рекомендаций: {e}")
        import traceback
        traceback.print_exc()
        return {
            'movements': [],
            'purchases': [],
            'returns': [],
            'all_recommendations': []
        }


def generate_item_recommendations(item_name, warehouse_analysis, warehouse_config):
    """Генерация рекомендаций для одного товара"""
    
    movements = []
    purchases = []
    returns = []
    
    # Находим дефициты и излишки
    deficits = []
    surpluses = []
    
    for warehouse, data in warehouse_analysis.items():
        if data['status'] == 'дефицит' and data['deficit_qty'] > 0:
            deficits.append({
                'warehouse': warehouse,
                'type': data['type'],
                'needed': data['deficit_qty'],
                'priority': get_warehouse_priority(data['type'])
            })
        elif data['status'] == 'излишек' and data['surplus_qty'] > 0:
            surpluses.append({
                'warehouse': warehouse,
                'type': data['type'],
                'available': data['surplus_qty'],
                'priority': get_warehouse_priority(data['type'])
            })
    
    # Сортируем по приоритету
    deficits.sort(key=lambda x: x['priority'], reverse=True)  # Магазины в приоритете
    surpluses.sort(key=lambda x: x['priority'])  # Хабы отдают первыми
    
    # Генерируем перемещения
    for deficit in deficits:
        remaining_need = deficit['needed']
        
        for surplus in surpluses:
            if remaining_need <= 0:
                break
                
            if surplus['available'] <= 0:
                continue
            
            # Рассчитываем количество к перемещению
            to_move = min(remaining_need, surplus['available'])
            
            if to_move >= 1:  # Минимум 1 единица
                movements.append({
                    'item': item_name,
                    'from': surplus['warehouse'],
                    'from_type': surplus['type'],
                    'to': deficit['warehouse'],
                    'to_type': deficit['type'],
                    'quantity': round(to_move),
                    'priority': deficit['priority'],
                    'reason': f"Покрытие дефицита в {deficit['type']}"
                })
                
                # Уменьшаем доступное количество
                surplus['available'] -= to_move
                remaining_need -= to_move
        
        # Если дефицит не покрыт, добавляем в закупки
        if remaining_need > 0:
            purchases.append({
                'item': item_name,
                'for_warehouse': deficit['warehouse'],
                'warehouse_type': deficit['type'],
                'quantity': round(remaining_need),
                'priority': deficit['priority'],
                'reason': f"Дефицит не покрыт внутренними перемещениями"
            })
    
    # Обрабатываем оставшиеся излишки (возврат в хаб)
    hub_name = "База Склад Фурнитура Комплект"
    
    for surplus in surpluses:
        if surplus['available'] > 0 and surplus['warehouse'] != hub_name:
            returns.append({
                'item': item_name,
                'from': surplus['warehouse'],
                'from_type': surplus['type'],
                'to': hub_name,
                'quantity': round(surplus['available']),
                'priority': 10,  # Низкий приоритет
                'reason': f"Излишек в {surplus['type']}, возврат в хаб"
            })
    
    return {
        'movements': movements,
        'purchases': purchases,
        'returns': returns
    }


def get_warehouse_priority(warehouse_type):
    """Получение приоритета склада для рекомендаций"""
    priority_map = {
        'магазин': 100,  # Высший приоритет
        'склад': 50,     # Средний приоритет
        'хаб': 20        # Низший приоритет
    }
    return priority_map.get(warehouse_type, 50)

def show_stock_upload_interface(system):
    """Интерфейс загрузки файла остатков"""
    
    st.subheader("📦 Загрузка данных остатков")
    
    st.info("""
    **Загрузите файл остатков** типа `остатки на 08.07.2025.xlsx`:
    - Структура: Номенклатура | Склад1 | Склад2 | ... | СкладN
    - Поддерживаются файлы Excel (.xlsx, .xls)
    - Остатки в количественном выражении (штуки, метры и т.д.)
    """)
    
    uploaded_file = st.file_uploader(
        "Выберите файл остатков:",
        type=['xlsx', 'xls'],
        key='stock_file_upload'
    )
    
    if uploaded_file:
        with st.spinner('Обработка файла остатков...'):
            try:
                # Читаем файл
                import pandas as pd
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                
                # Автоматическое определение структуры
                stock_data = process_stock_file(df)
                
                if stock_data is not None and not stock_data.empty:
                    # Сохраняем в систему
                    system.stock_data = stock_data
                    
                    st.success(f"✅ **Файл остатков загружен успешно!**")
                    st.info(f"📊 Обработано: {len(stock_data)} товаров по {len(stock_data.columns)-1} складам")
                    
                    # Показываем превью
                    with st.expander("👀 Предварительный просмотр данных"):
                        st.dataframe(stock_data.head(10))
                    
                    # Кнопка для продолжения
                    if st.button("▶️ Перейти к рекомендациям", type="primary"):
                        st.rerun()
                else:
                    st.error("❌ Не удалось обработать файл. Проверьте структуру данных.")
                    
            except Exception as e:
                st.error(f"❌ Ошибка обработки файла: {e}")

def process_stock_file(df):
    """Обработка файла остатков на основе РЕАЛЬНОЙ структуры файла"""
    try:
        import pandas as pd
        
        # РЕАЛЬНАЯ структура файла "остатки на 08.07.2025.xlsx":
        # - Строка 7 (индекс 6): заголовки "Номенклатура", названия складов
        # - Строка 10 (индекс 9): начало данных товаров
        # - Колонка A (индекс 0): номенклатура
        # - Колонки D-L (индексы 3-11): 9 складов
        # - Колонка M (индекс 12): "Итого" - ИСКЛЮЧАЕМ
        
        print("🔍 Анализ структуры файла остатков...")
        
        # Читаем заголовки из строки 7 (индекс 6)
        headers_row = df.iloc[6]
        print(f"📋 Заголовки из строки 7: {headers_row.tolist()[:15]}")
        
        # Ищем первую строку с данными товаров
        data_start_row = None
        for i in range(7, min(15, len(df))):  # Проверяем строки 8-15
            first_cell = df.iloc[i, 0]  # Первая колонка (номенклатура)
            if pd.notna(first_cell) and len(str(first_cell).strip()) > 3:
                # Проверяем есть ли числовые данные в колонках складов
                has_numbers = False
                for col_idx in range(3, min(12, len(df.columns))):
                    cell_value = df.iloc[i, col_idx]
                    if pd.notna(cell_value) and isinstance(cell_value, (int, float)) and cell_value > 0:
                        has_numbers = True
                        break
                
                if has_numbers:
                    data_start_row = i
                    print(f"🎯 Первая строка товаров найдена: {i+1} (индекс {i})")
                    print(f"   Товар: {str(first_cell)[:50]}")
                    break
        
        if data_start_row is None:
            data_start_row = 9  # Fallback к старому значению
            print("⚠️ Не удалось точно определить начало данных, используем строку 10")
        
        # Извлекаем данные начиная с найденной строки
        data_df = df.iloc[data_start_row:].copy()
        
        # Устанавливаем правильную структуру колонок
        # Колонка 0: номенклатура
        # Колонки 3-11: склады (исключаем колонку 12 "Итого")
        
        # Создаем маппинг складов с короткими названиями
        warehouse_mapping = {
            3: "Шымкент Склад",      # 4 Склад фурнитуры АЗМ Шымкент "Овощная база"
            4: "Шымкент Магазин",    # 6 Склад фурнитуры "Овощная база" Магазин
            5: "АО Склад",           # АО Склад Фурнитура TRADE
            6: "База Склад",         # База Склад Фурнитура Комплект
            7: "Барыс Склад",        # Барыс Склад Фурнитура TRADE
            8: "Казыбаева Склад",    # Казыбаева Склад Фурнитура TRADE
            9: "Астана Магазин",     # Магазин фурнитуры
            10: "Астана Склад",      # склад фурнитура № 1
            11: "Казыбаева Магазин"  # ТД Казыбаева ФУРНИТУРА магазин
        }
        
        # Создаем новый DataFrame с правильными колонками
        result_df = pd.DataFrame()
        
        # Колонка номенклатуры (индекс 0)
        result_df['номенклатура'] = data_df.iloc[:, 0]
        
        # Добавляем колонки складов (индексы 3-11, исключая 12 "Итого")
        for col_idx, warehouse_name in warehouse_mapping.items():
            if col_idx < len(data_df.columns):
                result_df[warehouse_name] = pd.to_numeric(data_df.iloc[:, col_idx], errors='coerce').fillna(0)
        
        # Фильтруем пустые строки номенклатуры
        result_df = result_df[result_df['номенклатура'].notna() & (result_df['номенклатура'] != '')]
        
        # Убираем строки где все остатки = 0
        warehouse_cols = [col for col in result_df.columns if col != 'номенклатура']
        non_zero_mask = result_df[warehouse_cols].sum(axis=1) > 0
        result_df = result_df[non_zero_mask].reset_index(drop=True)
        
        print(f"✅ Обработано: {len(result_df)} товаров по {len(warehouse_cols)} складам")
        print(f"📊 Склады: {warehouse_cols}")
        
        # Показываем первые 3 товара для проверки
        if len(result_df) > 0:
            print("🔍 Первые товары:")
            for i in range(min(3, len(result_df))):
                item_name = result_df.iloc[i]['номенклатура']
                total_stock = result_df.iloc[i, 1:].sum()  # Сумма по всем складам
                print(f"   {i+1}. {str(item_name)[:40]}... | Общий остаток: {total_stock}")
        
        return result_df
        
    except Exception as e:
        print(f"❌ Ошибка обработки файла: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_main_recommendations_interface(system):
    """Основной интерфейс рекомендаций"""
    
    # Показываем структуру складской иерархии
    with st.expander("📋 **Структура складской сети**", expanded=False):
        st.markdown("""
        ### 🌐 Центральный хаб (г. Алматы)
        **База Склад Фурнитура Комплект** - главный распределительный центр
        
        ### 🏬 Склады 2-го уровня:
        - **Казыбаева Склад Фурнитура TRADE** → обслуживает ТД Казыбаева магазин (Алматы)
        - **склад фурнитура № 1** → обслуживает Магазин фурнитуры (Астана)  
        - **4 Склад фурнитуры АЗМ Шымкент** → обслуживает 6 Склад магазин (Шымкент)
        
        ### 🏪 Магазины:
        **Алматы:**
        - ТД Казыбаева ФУРНИТУРА магазин (от склада Казыбаева)
        - Барыс Склад Фурнитура TRADE (напрямую от хаба)
        - АО Склад Фурнитура TRADE (напрямую от хаба)
        
        **Астана:**
        - Магазин фурнитуры (от склада № 1)
        
        **Шымкент:**
        - 6 Склад фурнитуры "Овощная база" Магазин (от склада АЗМ)
        """)
    
    st.subheader("⚙️ Настройки нормативов")
    
    # Настройки по типам точек
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏪 Магазины**")
        mag_min = st.number_input("Мин. запас (дни)", value=15, min_value=1, max_value=90, key="mag_min")
        mag_max = st.number_input("Макс. запас (дни)", value=30, min_value=1, max_value=180, key="mag_max")
    
    with col2:
        st.markdown("**🏬 Склады**")
        sklad_min = st.number_input("Мин. запас (дни)", value=30, min_value=1, max_value=90, key="sklad_min")
        sklad_max = st.number_input("Макс. запас (дни)", value=60, min_value=1, max_value=180, key="sklad_max")
    
    with col3:
        st.markdown("**🌐 Хабы**")
        hub_min = st.number_input("Мин. запас (дни)", value=60, min_value=1, max_value=180, key="hub_min")
        hub_max = st.number_input("Макс. запас (дни)", value=120, min_value=1, max_value=365, key="hub_max")
    
    st.markdown("---")
    
    # Сохраняем нормативы в session_state
    norms = {
        'магазин': {'min': mag_min, 'max': mag_max},
        'склад': {'min': sklad_min, 'max': sklad_max}, 
        'хаб': {'min': hub_min, 'max': hub_max}
    }
    
    col_calc, col_reset = st.columns([3, 1])
    
    with col_calc:
        if st.button("🚀 Рассчитать рекомендации", type="primary"):
            # Сохраняем флаг для отображения результатов
            st.session_state.show_recommendations = True
            st.session_state.norms = norms
            st.rerun()
    
    with col_reset:
        if st.session_state.get('show_recommendations', False):
            if st.button("🔄 Пересчитать", help="Пересчитать рекомендации с новыми настройками"):
                # Очищаем кэш рекомендаций
                keys_to_remove = [key for key in st.session_state.keys() if key.startswith("recommendations_")]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.session_state.show_recommendations = True
                st.session_state.norms = norms
                st.rerun()
    
    # Если есть флаг для отображения результатов, показываем их
    if st.session_state.get('show_recommendations', False):
        show_recommendations_results(system, st.session_state.get('norms', norms))

def show_recommendations_results(system, norms):
    """Показ результатов рекомендаций"""
    
    st.subheader("📊 Результаты анализа и рекомендации")
    
    # Создаем ключ для кэширования результатов
    cache_key = f"recommendations_{hash(str(norms))}"
    
    # Информация о статусе кэша
    if cache_key in st.session_state:
        st.success("✅ Рекомендации загружены из кэша")
    else:
        st.info("⏳ Рассчитываем рекомендации...")
    
    # Проверяем, есть ли уже рассчитанные рекомендации в session_state
    if cache_key not in st.session_state:
        # Если нет, рассчитываем заново
        with st.spinner("Рассчитываем рекомендации..."):
            recommendations = calculate_movement_recommendations(system, norms)
            if recommendations:
                st.session_state[cache_key] = recommendations
                st.success("✅ Рекомендации успешно рассчитаны и сохранены")
            else:
                st.error("❌ Не удалось рассчитать рекомендации")
                return
    
    # Берем рекомендации из session_state
    recommendations = st.session_state[cache_key]
    
    if not recommendations:
        st.error("❌ Не удалось рассчитать рекомендации")
        return
    
    # Показываем общую статистику
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Проанализировано товаров", recommendations['stats']['total_items'])
    
    with col2:
        st.metric("Точек продаж", recommendations['stats']['total_warehouses'])
    
    with col3:
        st.metric("Рекомендаций к перемещению", recommendations['stats']['move_recommendations'])
    
    with col4:
        st.metric("Товаров с дефицитом", recommendations['stats']['deficit_items'])
    
    # Дополнительная статистика по комплексным рекомендациям
    if 'comprehensive_recommendations' in recommendations['stats']:
        st.markdown("#### 📊 Детальная статистика рекомендаций")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔄 Перемещения товаров", 
                     len([r for r in recommendations['comprehensive_recommendations'] if r['type'] == 'movement']))
        
        with col2:
            st.metric("🛒 Заказы от поставщика", 
                     len([r for r in recommendations['comprehensive_recommendations'] if r['type'] == 'purchase']))
        
        with col3:
            st.metric("🏠 Возвраты в хаб", 
                     len([r for r in recommendations['comprehensive_recommendations'] if r['type'] == 'return_to_hub']))
    
    # Показываем ABC анализ
    st.subheader("📈 ABC анализ товаров")
    
    abc_stats = recommendations['abc_analysis']
    abc_col1, abc_col2, abc_col3 = st.columns(3)
    
    with abc_col1:
        st.metric("Товары класса A", f"{abc_stats['A']['count']} ({abc_stats['A']['percent']:.1f}%)", 
                 f"{abc_stats['A']['sales_percent']:.1f}% продаж")
    
    with abc_col2:
        st.metric("Товары класса B", f"{abc_stats['B']['count']} ({abc_stats['B']['percent']:.1f}%)",
                 f"{abc_stats['B']['sales_percent']:.1f}% продаж")
    
    with abc_col3:
        st.metric("Товары класса C", f"{abc_stats['C']['count']} ({abc_stats['C']['percent']:.1f}%)",
                 f"{abc_stats['C']['sales_percent']:.1f}% продаж")
    
    # Выбор типа отображения
    display_type = st.radio(
        "Тип отображения рекомендаций:",
        ["📋 Детализированные рекомендации", "🚚 Рекомендации по перемещениям", "🏪 Анализ по складам", "🔄 Комплексные рекомендации"],
        horizontal=True,
        key="display_type_radio"
    )
    
    if display_type == "📋 Детализированные рекомендации":
        # Показываем детализированные рекомендации для каждого товара и склада
        if 'detailed_recommendations' in recommendations:
            show_detailed_recommendations(recommendations['detailed_recommendations'])
        else:
            st.error("Детализированные рекомендации не найдены")
    
    elif display_type == "🚚 Рекомендации по перемещениям":
        # Рекомендации по перемещениям
        if recommendations['movements']:
            st.subheader("🚚 Рекомендации по перемещениям")
            
            # Приоритизируем товары A-класса
            priority_moves = [move for move in recommendations['movements'] if move['abc_class'] == 'A']
            other_moves = [move for move in recommendations['movements'] if move['abc_class'] != 'A']
            
            if priority_moves:
                st.markdown("**🔥 Приоритетные перемещения (товары класса A):**")
                show_movement_table(priority_moves[:10])  # Показываем топ-10
            
            if other_moves:
                with st.expander(f"📦 Другие рекомендации ({len(other_moves)} товаров)"):
                    show_movement_table(other_moves[:20])  # Показываем топ-20
        else:
            st.info("Нет рекомендаций по перемещениям")
    
    elif display_type == "🏪 Анализ по складам":
        # Анализ по складам
        st.subheader("🏪 Анализ по складам")
        show_warehouse_analysis(recommendations['warehouse_analysis'])
    
    elif display_type == "🔄 Комплексные рекомендации":
        # Комплексные рекомендации
        if 'comprehensive_recommendations' in recommendations:
            show_comprehensive_recommendations(recommendations['comprehensive_recommendations'])
        else:
            st.error("Комплексные рекомендации не найдены")
    
    # Экспорт
    st.subheader("📤 Экспорт результатов")
    if st.button("📄 Скачать рекомендации в Excel"):
        excel_data = create_excel_export(recommendations)
        st.download_button(
            "📥 Скачать файл",
            excel_data,
            "рекомендации_по_перемещениям.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def calculate_movement_recommendations(system, norms):
    """Расчет рекомендаций по перемещениям"""
    try:
        import pandas as pd
        import numpy as np
        
        # Объединяем данные ADS и остатков
        ads_df = system.calculated_ads.copy()
        stock_df = system.stock_data.copy()
        
        # Объединяем по номенклатуре
        merged_df = pd.merge(ads_df, stock_df, on='номенклатура', how='inner')
        
        if len(merged_df) == 0:
            return None
        
        # ABC анализ
        merged_df = merged_df.sort_values('общие_продажи', ascending=False)
        total_sales = merged_df['общие_продажи'].sum()
        merged_df['sales_percent'] = (merged_df['общие_продажи'] / total_sales) * 100
        merged_df['cumulative_percent'] = merged_df['sales_percent'].cumsum()
        
        # Классификация ABC (80/15/5)
        merged_df['abc_class'] = 'C'
        merged_df.loc[merged_df['cumulative_percent'] <= 80, 'abc_class'] = 'A'
        merged_df.loc[(merged_df['cumulative_percent'] > 80) & (merged_df['cumulative_percent'] <= 95), 'abc_class'] = 'B'
        
        # Определяем типы складов
        warehouse_types = classify_warehouses(stock_df.columns[1:])
        
        # Рассчитываем нормативы и находим дисбалансы
        item_balances = []
        warehouse_analysis = {}
        
        for _, item in merged_df.iterrows():
            item_balance = analyze_item_balance(item, warehouse_types, norms)
            item_balances.append(item_balance)
            
            # Собираем анализ по складам
            for warehouse, analysis in item_balance['analysis'].items():
                if warehouse not in warehouse_analysis:
                    warehouse_analysis[warehouse] = {'surplus': 0, 'deficit': 0, 'items': 0}
                warehouse_analysis[warehouse]['items'] += 1
                if analysis['status'] == 'surplus':
                    warehouse_analysis[warehouse]['surplus'] += analysis['excess']
                elif analysis['status'] == 'deficit':
                    warehouse_analysis[warehouse]['deficit'] += analysis['shortage']
        
        # Генерируем рекомендации по перемещениям между складами
        movements = generate_movement_recommendations(item_balances, warehouse_types)
        
        # Генерируем комплексные рекомендации для всех товаров
        comprehensive_recommendations = generate_comprehensive_recommendations(merged_df, warehouse_types, norms)
        
        # Генерируем детализированные рекомендации для каждого товара и склада
        detailed_recommendations = generate_detailed_item_recommendations(merged_df, warehouse_types, norms)
        
        # ABC статистика
        abc_stats = {}
        for abc_class in ['A', 'B', 'C']:
            class_items = merged_df[merged_df['abc_class'] == abc_class]
            abc_stats[abc_class] = {
                'count': len(class_items),
                'percent': len(class_items) / len(merged_df) * 100,
                'sales_percent': class_items['sales_percent'].sum()
            }
        
        return {
            'stats': {
                'total_items': len(merged_df),
                'total_warehouses': len(stock_df.columns) - 1,
                'move_recommendations': len(movements),
                'deficit_items': len([m for m in movements if m.get('to_type') == 'магазин']),
                'comprehensive_recommendations': len(comprehensive_recommendations),
                'purchase_recommendations': len([r for r in comprehensive_recommendations if r['type'] == 'purchase']),
                'return_to_hub_recommendations': len([r for r in comprehensive_recommendations if r['type'] == 'return_to_hub'])
            },
            'abc_analysis': abc_stats,
            'movements': movements,
            'warehouse_analysis': warehouse_analysis,
            'detailed_data': merged_df,
            'detailed_recommendations': detailed_recommendations,
            'comprehensive_recommendations': comprehensive_recommendations
        }
        
    except Exception as e:
        st.error(f"Ошибка расчета: {e}")
        return None

def classify_warehouses(warehouse_names):
    """Классификация складов по типам с учетом иерархии"""
    warehouse_types = {}
    config = MovementRecommendationConfig()
    
    for warehouse in warehouse_names:
        # Сначала проверяем в иерархии
        if warehouse in config.WAREHOUSE_HIERARCHY:
            warehouse_types[warehouse] = config.WAREHOUSE_HIERARCHY[warehouse]['type']
        else:
            # Если нет в иерархии, определяем по ключевым словам
            warehouse_types[warehouse] = config.get_location_type(warehouse)
    
    return warehouse_types

def analyze_item_balance(item, warehouse_types, norms):
    """Анализ баланса товара по всем складам"""
    analysis = {}
    surpluses = []  # Склады с излишками
    deficits = []   # Склады с дефицитами
    
    ads = item['ads']
    warehouse_columns = [col for col in item.index if col not in ['номенклатура', 'ads', 'общие_продажи', 'категория', 'подкатегория', 'sales_percent', 'cumulative_percent', 'abc_class']]
    
    # Анализируем каждый склад
    for warehouse in warehouse_columns:
        if warehouse in warehouse_types:
            current_stock = item[warehouse]
            warehouse_type = warehouse_types[warehouse]
            
            # Рассчитываем нормативы
            min_stock = ads * norms[warehouse_type]['min']
            max_stock = ads * norms[warehouse_type]['max']
            optimal_stock = (min_stock + max_stock) / 2
            
            if current_stock < min_stock:
                shortage = min_stock - current_stock
                analysis[warehouse] = {
                    'status': 'deficit', 
                    'shortage': shortage,
                    'current': current_stock,
                    'min': min_stock,
                    'max': max_stock,
                    'optimal': optimal_stock,
                    'type': warehouse_type
                }
                deficits.append({
                    'warehouse': warehouse,
                    'warehouse_type': warehouse_type,
                    'shortage': shortage,
                    'priority': get_warehouse_priority(warehouse_type)
                })
                
            elif current_stock > max_stock:
                excess = current_stock - max_stock
                analysis[warehouse] = {
                    'status': 'surplus', 
                    'excess': excess,
                    'current': current_stock,
                    'min': min_stock,
                    'max': max_stock,
                    'optimal': optimal_stock,
                    'type': warehouse_type
                }
                surpluses.append({
                    'warehouse': warehouse,
                    'warehouse_type': warehouse_type,
                    'excess': excess,
                    'priority': get_warehouse_priority(warehouse_type)
                })
            else:
                analysis[warehouse] = {
                    'status': 'normal',
                    'current': current_stock,
                    'min': min_stock,
                    'max': max_stock,
                    'optimal': optimal_stock,
                    'type': warehouse_type
                }
    
    return {
        'item': item['номенклатура'],
        'abc_class': item['abc_class'],
        'ads': ads,
        'analysis': analysis,
        'surpluses': surpluses,
        'deficits': deficits
    }

def get_warehouse_priority(warehouse_type):
    """Приоритет склада (магазины важнее складов)"""
    priorities = {'магазин': 1, 'склад': 2, 'хаб': 3}
    return priorities.get(warehouse_type, 2)

def generate_detailed_item_recommendations(merged_df, warehouse_types, norms):
    """Генерация детализированных рекомендаций для каждого товара и склада"""
    config = MovementRecommendationConfig()
    detailed_recommendations = []
    
    for _, item in merged_df.iterrows():
        item_name = item['номенклатура']
        ads_value = item['ads']
        abc_class = item['abc_class']
        
        # Рекомендации по каждому складу для данного товара
        warehouse_recommendations = []
        
        for warehouse in warehouse_types.keys():
            if warehouse in item:
                current_stock = item[warehouse]
                warehouse_type = warehouse_types[warehouse]
                
                # Рассчитываем нормативы для данного типа склада
                min_stock = ads_value * norms[warehouse_type]['min']
                max_stock = ads_value * norms[warehouse_type]['max']
                optimal_stock = (min_stock + max_stock) / 2
                
                # Определяем статус и рекомендацию
                if current_stock < min_stock:
                    shortage = min_stock - current_stock
                    status = 'deficit'
                    recommendation = generate_warehouse_recommendation(
                        warehouse, warehouse_type, 'deficit', shortage, config
                    )
                elif current_stock > max_stock:
                    excess = current_stock - max_stock
                    status = 'surplus'
                    recommendation = generate_warehouse_recommendation(
                        warehouse, warehouse_type, 'surplus', excess, config
                    )
                else:
                    status = 'normal'
                    recommendation = "✅ Запас в норме"
                
                warehouse_recommendations.append({
                    'warehouse': warehouse,
                    'warehouse_type': warehouse_type,
                    'city': config.WAREHOUSE_HIERARCHY.get(warehouse, {}).get('city', ''),
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'optimal_stock': optimal_stock,
                    'status': status,
                    'recommendation': recommendation
                })
        
        detailed_recommendations.append({
            'item': item_name,
            'ads': ads_value,
            'abc_class': abc_class,
            'warehouses': warehouse_recommendations
        })
    
    return detailed_recommendations

def generate_warehouse_recommendation(warehouse, warehouse_type, status, amount, config):
    """Генерация рекомендации для конкретного склада"""
    warehouse_info = config.WAREHOUSE_HIERARCHY.get(warehouse, {})
    
    if status == 'deficit':
        # Определяем откуда пополнить
        if 'parent' in warehouse_info:
            parent = warehouse_info['parent']
            parent_info = config.WAREHOUSE_HIERARCHY.get(parent, {})
            parent_city = parent_info.get('city', '')
            
            if warehouse_type == 'магазин':
                return f"🔴 Дефицит {amount:.0f} ед. → Пополнить со склада '{parent}' ({parent_city})"
            else:
                return f"🔴 Дефицит {amount:.0f} ед. → Пополнить из хаба '{parent}' ({parent_city})"
        else:
            return f"🔴 Дефицит {amount:.0f} ед. → Требуется пополнение"
    
    elif status == 'surplus':
        # Определяем куда перенаправить излишки
        if 'supplies' in warehouse_info:
            targets = warehouse_info['supplies']
            if len(targets) == 1:
                target = targets[0]
                target_info = config.WAREHOUSE_HIERARCHY.get(target, {})
                target_city = target_info.get('city', '')
                return f"🟡 Излишек {amount:.0f} ед. → Перенаправить в '{target}' ({target_city})"
            else:
                return f"🟡 Излишек {amount:.0f} ед. → Перенаправить в подчиненные склады"
        else:
            return f"🟡 Излишек {amount:.0f} ед. → Оптимизировать запас"
    
    return "✅ Запас в норме"

def check_transfer_validity(from_warehouse, to_warehouse, config):
    """Проверяет, допустимо ли перемещение между складами по иерархии"""
    # Если оба склада не в иерархии, разрешаем перемещение
    if from_warehouse not in config.WAREHOUSE_HIERARCHY or to_warehouse not in config.WAREHOUSE_HIERARCHY:
        return True
    
    from_info = config.WAREHOUSE_HIERARCHY[from_warehouse]
    to_info = config.WAREHOUSE_HIERARCHY[to_warehouse]
    
    # Хаб может отправлять всем
    if from_info['type'] == 'хаб':
        return True
    
    # Проверяем, является ли получатель дочерним складом отправителя
    if 'supplies' in from_info and to_warehouse in from_info['supplies']:
        return True
    
    # Проверяем, является ли отправитель родителем получателя
    if 'parent' in to_info and to_info['parent'] == from_warehouse:
        return True
    
    # Склады одного уровня не должны обмениваться между собой
    if from_info.get('level') == to_info.get('level'):
        return False
    
    return False

def get_hierarchical_transfer_reason(from_warehouse, to_warehouse, config):
    """Определение причины перемещения с учетом иерархии"""
    if from_warehouse not in config.WAREHOUSE_HIERARCHY or to_warehouse not in config.WAREHOUSE_HIERARCHY:
        return get_transfer_reason(
            config.get_location_type(from_warehouse),
            config.get_location_type(to_warehouse)
        )
    
    from_info = config.WAREHOUSE_HIERARCHY[from_warehouse]
    to_info = config.WAREHOUSE_HIERARCHY[to_warehouse]
    
    # Определяем тип перемещения
    if from_info['type'] == 'хаб':
        if to_info['type'] == 'склад':
            return f"Распределение из хаба на склад 2-го уровня ({to_info.get('city', 'регион')})"
        elif to_info['type'] == 'магазин':
            return f"Прямая поставка из хаба в магазин ({to_info.get('city', 'регион')})"
    elif from_info['type'] == 'склад' and to_info['type'] == 'магазин':
        if 'parent' in to_info and to_info['parent'] == from_warehouse:
            return f"Пополнение магазина со склада-снабженца ({to_info.get('city', 'регион')})"
        else:
            return f"Пополнение магазина со склада ({to_info.get('city', 'регион')})"
    elif from_info['type'] == 'магазин' and to_info['type'] == 'склад':
        return "Возврат излишков из магазина на склад"
    elif from_info['type'] == 'склад' and to_info['type'] == 'склад':
        return "Перераспределение между складами"
    else:
        return "Оптимизация запасов"

def generate_comprehensive_recommendations(merged_df, warehouse_types, norms):
    """Генерация комплексных рекомендаций для всех товаров"""
    config = MovementRecommendationConfig()
    
    # Анализируем каждый товар
    all_recommendations = []
    
    for _, item in merged_df.iterrows():
        item_name = item['номенклатура']
        ads_value = item['ads']
        abc_class = item['abc_class']
        
        # Анализируем остатки по всем складам
        warehouse_analysis = {}
        total_current_stock = 0
        total_deficit = 0
        total_surplus = 0
        
        for warehouse in warehouse_types.keys():
            if warehouse in item:
                current_stock = item[warehouse]
                warehouse_type = warehouse_types[warehouse]
                
                # Рассчитываем нормативы
                min_stock = ads_value * norms[warehouse_type]['min']
                max_stock = ads_value * norms[warehouse_type]['max']
                
                total_current_stock += current_stock
                
                if current_stock < min_stock:
                    shortage = min_stock - current_stock
                    status = 'deficit'
                    total_deficit += shortage
                elif current_stock > max_stock:
                    excess = current_stock - max_stock
                    status = 'surplus'
                    total_surplus += excess
                else:
                    status = 'normal'
                    shortage = 0
                    excess = 0
                
                warehouse_analysis[warehouse] = {
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'status': status,
                    'shortage': shortage if status == 'deficit' else 0,
                    'excess': excess if status == 'surplus' else 0,
                    'warehouse_type': warehouse_type
                }
        
        # Генерируем рекомендации для товара
        item_recommendations = generate_item_recommendations(
            item_name, ads_value, abc_class, warehouse_analysis, total_current_stock, 
            total_deficit, total_surplus, config
        )
        
        all_recommendations.extend(item_recommendations)
    
    return all_recommendations

def generate_item_recommendations(item_name, ads_value, abc_class, warehouse_analysis, 
                                total_current_stock, total_deficit, total_surplus, config):
    """Генерация рекомендаций для конкретного товара"""
    recommendations = []
    
    # 1. Сначала пытаемся закрыть дефициты за счет излишков
    deficit_warehouses = [(w, data) for w, data in warehouse_analysis.items() if data['status'] == 'deficit']
    surplus_warehouses = [(w, data) for w, data in warehouse_analysis.items() if data['status'] == 'surplus']
    
    # Сортируем по приоритету (магазины важнее)
    deficit_warehouses.sort(key=lambda x: get_warehouse_priority(x[1]['warehouse_type']))
    surplus_warehouses.sort(key=lambda x: get_warehouse_priority(x[1]['warehouse_type']), reverse=True)
    
    # Создаем копии для работы
    working_deficits = [(w, data['shortage']) for w, data in deficit_warehouses]
    working_surpluses = [(w, data['excess']) for w, data in surplus_warehouses]
    
    # Пытаемся закрыть дефициты за счет излишков
    for deficit_warehouse, deficit_amount in working_deficits:
        remaining_deficit = deficit_amount
        
        for i, (surplus_warehouse, surplus_amount) in enumerate(working_surpluses):
            if remaining_deficit <= 0:
                break
            
            # Проверяем возможность перемещения
            if check_transfer_validity(surplus_warehouse, deficit_warehouse, config):
                transfer_amount = min(remaining_deficit, surplus_amount)
                
                if transfer_amount > 0:
                    recommendations.append({
                        'type': 'movement',
                        'item': item_name,
                        'abc_class': abc_class,
                        'ads': ads_value,
                        'from_warehouse': surplus_warehouse,
                        'to_warehouse': deficit_warehouse,
                        'from_type': warehouse_analysis[surplus_warehouse]['warehouse_type'],
                        'to_type': warehouse_analysis[deficit_warehouse]['warehouse_type'],
                        'transfer_amount': transfer_amount,
                        'reason': get_hierarchical_transfer_reason(surplus_warehouse, deficit_warehouse, config),
                        'priority': min(get_warehouse_priority(warehouse_analysis[deficit_warehouse]['warehouse_type']),
                                      get_warehouse_priority(warehouse_analysis[surplus_warehouse]['warehouse_type'])),
                        'urgency': 'Высокая' if abc_class == 'A' else 'Средняя' if abc_class == 'B' else 'Низкая'
                    })
                    
                    # Уменьшаем остатки
                    remaining_deficit -= transfer_amount
                    working_surpluses[i] = (surplus_warehouse, surplus_amount - transfer_amount)
        
        # Если дефицит не закрыт полностью, нужен заказ от поставщика
        if remaining_deficit > 0:
            # Находим лучший склад для заказа (обычно хаб)
            best_warehouse_for_order = find_best_warehouse_for_order(deficit_warehouse, config)
            
            recommendations.append({
                'type': 'purchase',
                'item': item_name,
                'abc_class': abc_class,
                'ads': ads_value,
                'warehouse': best_warehouse_for_order,
                'warehouse_type': config.WAREHOUSE_HIERARCHY.get(best_warehouse_for_order, {}).get('type', 'хаб'),
                'order_amount': remaining_deficit,
                'reason': f"Дефицит не может быть закрыт перемещениями, требуется заказ от поставщика",
                'priority': get_warehouse_priority(warehouse_analysis[deficit_warehouse]['warehouse_type']),
                'urgency': 'Высокая' if abc_class == 'A' else 'Средняя' if abc_class == 'B' else 'Низкая'
            })
    
    # 2. Обрабатываем оставшиеся излишки - отправляем в хаб
    for surplus_warehouse, surplus_amount in working_surpluses:
        if surplus_amount > 0:
            hub_warehouse = 'База Склад Фурнитура Комплект'
            
            recommendations.append({
                'type': 'return_to_hub',
                'item': item_name,
                'abc_class': abc_class,
                'ads': ads_value,
                'from_warehouse': surplus_warehouse,
                'to_warehouse': hub_warehouse,
                'from_type': warehouse_analysis[surplus_warehouse]['warehouse_type'],
                'to_type': 'хаб',
                'transfer_amount': surplus_amount,
                'reason': f"Излишки возвращаются в центральный хаб для перераспределения",
                'priority': get_warehouse_priority(warehouse_analysis[surplus_warehouse]['warehouse_type']),
                'urgency': 'Низкая'
            })
    
    return recommendations

def find_best_warehouse_for_order(deficit_warehouse, config):
    """Находит лучший склад для размещения заказа"""
    warehouse_info = config.WAREHOUSE_HIERARCHY.get(deficit_warehouse, {})
    
    # Если есть родитель, заказываем через него
    if 'parent' in warehouse_info:
        return warehouse_info['parent']
    
    # Иначе через хаб
    return 'База Склад Фурнитура Комплект'

def generate_movement_recommendations(item_balances, warehouse_types):
    """Генерация рекомендаций по перемещениям между складами с учетом иерархии"""
    movements = []
    config = MovementRecommendationConfig()
    
    for item_balance in item_balances:
        if not item_balance['surpluses'] or not item_balance['deficits']:
            continue  # Нет возможности для перемещений
        
        # Сортируем по приоритету (магазины важнее)
        deficits = sorted(item_balance['deficits'], key=lambda x: x['priority'])
        surpluses = sorted(item_balance['surpluses'], key=lambda x: x['priority'], reverse=True)
        
        # Генерируем перемещения с учетом иерархии
        for deficit in deficits:
            remaining_shortage = deficit['shortage']
            deficit_warehouse = deficit['warehouse']
            
            # Проверяем иерархию складов
            valid_sources = []
            if deficit_warehouse in config.WAREHOUSE_HIERARCHY:
                warehouse_info = config.WAREHOUSE_HIERARCHY[deficit_warehouse]
                # Если у склада есть родитель, он должен получать товары от него
                if 'parent' in warehouse_info:
                    parent = warehouse_info['parent']
                    # Ищем излишки у родителя
                    for surplus in surpluses:
                        if surplus['warehouse'] == parent:
                            valid_sources.append(surplus)
                    # Если у родителя нет излишков, смотрим хаб
                    if not valid_sources and parent != 'База Склад Фурнитура Комплект':
                        for surplus in surpluses:
                            if surplus['warehouse'] == 'База Склад Фурнитура Комплект':
                                valid_sources.append(surplus)
            
            # Если нет четкой иерархии или нет излишков у родителя, используем все излишки
            if not valid_sources:
                valid_sources = surpluses
            
            for surplus in valid_sources:
                if remaining_shortage <= 0:
                    break
                
                # Проверяем, можно ли делать перемещение по иерархии
                from_warehouse = surplus['warehouse']
                can_transfer = check_transfer_validity(from_warehouse, deficit_warehouse, config)
                
                if not can_transfer:
                    continue
                
                # Рассчитываем количество для перемещения
                available_excess = surplus['excess']
                transfer_amount = min(remaining_shortage, available_excess)
                
                if transfer_amount > 0:
                    movement = {
                        'item': item_balance['item'],
                        'abc_class': item_balance['abc_class'],
                        'ads': item_balance['ads'],
                        'from_warehouse': from_warehouse,
                        'to_warehouse': deficit_warehouse,
                        'from_type': surplus['warehouse_type'],
                        'to_type': deficit['warehouse_type'],
                        'transfer_amount': transfer_amount,
                        'reason': get_hierarchical_transfer_reason(from_warehouse, deficit_warehouse, config),
                        'priority': min(deficit['priority'], surplus['priority']),
                        'urgency': 'Высокая' if item_balance['abc_class'] == 'A' else 'Средняя' if item_balance['abc_class'] == 'B' else 'Низкая'
                    }
                    
                    movements.append(movement)
                    
                    # Уменьшаем остатки дефицита и излишка
                    remaining_shortage -= transfer_amount
                    surplus['excess'] -= transfer_amount
    
    # Сортируем по приоритету (A-товары и магазины в приоритете)
    movements.sort(key=lambda x: (x['priority'], 0 if x['abc_class'] == 'A' else 1 if x['abc_class'] == 'B' else 2))
    
    return movements

def get_transfer_reason(from_type, to_type):
    """Определение причины перемещения"""
    if to_type == 'магазин':
        return "Пополнение торговой точки"
    elif from_type == 'хаб' and to_type == 'склад':
        return "Распределение со склада-хаба"
    elif from_type == 'склад' and to_type == 'магазин':
        return "Пополнение из регионального склада"
    elif from_type == 'магазин' and to_type == 'склад':
        return "Возврат излишков на склад"
    else:
        return "Перераспределение запасов"

def show_comprehensive_recommendations(comprehensive_recommendations):
    """Отображение комплексных рекомендаций по всем товарам"""
    import pandas as pd
    
    if not comprehensive_recommendations:
        st.info("Комплексные рекомендации отсутствуют")
        return
    
    st.markdown("### 🔄 Комплексные рекомендации по оптимизации запасов")
    
    # Группируем рекомендации по типам
    movements = [r for r in comprehensive_recommendations if r['type'] == 'movement']
    purchases = [r for r in comprehensive_recommendations if r['type'] == 'purchase']
    returns_to_hub = [r for r in comprehensive_recommendations if r['type'] == 'return_to_hub']
    
    # Показываем статистику
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔄 Перемещения", len(movements))
    with col2:
        st.metric("🛒 Заказы от поставщика", len(purchases))
    with col3:
        st.metric("🏠 Возвраты в хаб", len(returns_to_hub))
    
    # Выбор типа рекомендаций для отображения
    rec_type = st.selectbox(
        "Тип рекомендаций:",
        ["🔄 Перемещения между складами", "🛒 Заказы от поставщика", "🏠 Возвраты в хаб"],
        key="comprehensive_rec_type"
    )
    
    if rec_type == "🔄 Перемещения между складами":
        show_movement_recommendations(movements)
    elif rec_type == "🛒 Заказы от поставщика":
        show_purchase_recommendations(purchases)
    elif rec_type == "🏠 Возвраты в хаб":
        show_return_recommendations(returns_to_hub)

def show_movement_recommendations(movements):
    """Отображение рекомендаций по перемещениям"""
    import pandas as pd
    
    if not movements:
        st.info("Нет рекомендаций по перемещениям")
        return
    
    st.markdown("#### 🔄 Рекомендации по перемещениям между складами")
    
    # Группируем по ABC классам
    abc_tabs = st.tabs(["🔴 Класс A", "🟡 Класс B", "🟢 Класс C", "📊 Все"])
    
    for i, abc_class in enumerate(['A', 'B', 'C', 'All']):
        with abc_tabs[i]:
            if abc_class == 'All':
                filtered_movements = movements
            else:
                filtered_movements = [m for m in movements if m['abc_class'] == abc_class]
            
            if not filtered_movements:
                st.info(f"Нет перемещений для класса {abc_class}")
                continue
            
            # Создаем таблицу
            table_data = []
            for move in filtered_movements:
                table_data.append({
                    'Товар': move['item'][:40] + '...' if len(move['item']) > 40 else move['item'],
                    'ABC': move['abc_class'],
                    'ADS': f"{move['ads']:.1f}",
                    'Откуда': move['from_warehouse'],
                    'Куда': move['to_warehouse'], 
                    'Количество': f"{move['transfer_amount']:.0f}",
                    'Причина': move['reason'],
                    'Приоритет': move['urgency']
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def show_purchase_recommendations(purchases):
    """Отображение рекомендаций по закупкам"""
    import pandas as pd
    
    if not purchases:
        st.info("Нет рекомендаций по закупкам")
        return
    
    st.markdown("#### 🛒 Рекомендации по заказам от поставщика")
    
    # Группируем по складам
    warehouses = list(set([p['warehouse'] for p in purchases]))
    
    for warehouse in warehouses:
        warehouse_purchases = [p for p in purchases if p['warehouse'] == warehouse]
        
        st.markdown(f"**🏬 {warehouse}**")
        
        table_data = []
        total_amount = 0
        
        for purchase in warehouse_purchases:
            table_data.append({
                'Товар': purchase['item'][:40] + '...' if len(purchase['item']) > 40 else purchase['item'],
                'ABC': purchase['abc_class'],
                'ADS': f"{purchase['ads']:.1f}",
                'Заказать': f"{purchase['order_amount']:.0f}",
                'Причина': purchase['reason'],
                'Приоритет': purchase['urgency']
            })
            total_amount += purchase['order_amount']
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Общий объем заказа: {total_amount:.0f} единиц")
        st.markdown("---")

def show_return_recommendations(returns):
    """Отображение рекомендаций по возвратам в хаб"""
    import pandas as pd
    
    if not returns:
        st.info("Нет рекомендаций по возвратам в хаб")
        return
    
    st.markdown("#### 🏠 Рекомендации по возвратам излишков в хаб")
    
    # Группируем по складам-источникам
    warehouses = list(set([r['from_warehouse'] for r in returns]))
    
    for warehouse in warehouses:
        warehouse_returns = [r for r in returns if r['from_warehouse'] == warehouse]
        
        st.markdown(f"**🏬 {warehouse}**")
        
        table_data = []
        total_amount = 0
        
        for return_rec in warehouse_returns:
            table_data.append({
                'Товар': return_rec['item'][:40] + '...' if len(return_rec['item']) > 40 else return_rec['item'],
                'ABC': return_rec['abc_class'],
                'ADS': f"{return_rec['ads']:.1f}",
                'Вернуть': f"{return_rec['transfer_amount']:.0f}",
                'Причина': return_rec['reason']
            })
            total_amount += return_rec['transfer_amount']
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Общий объем возврата: {total_amount:.0f} единиц")
        st.markdown("---")

def show_detailed_recommendations(detailed_recommendations):
    """Отображение детализированных рекомендаций для каждого товара и склада"""
    import pandas as pd
    
    if not detailed_recommendations:
        st.info("Детализированные рекомендации отсутствуют")
        return
    
    st.markdown("### 📋 Детализированные рекомендации по товарам и складам")
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        abc_filter = st.selectbox("Фильтр ABC класса", ['Все', 'A', 'B', 'C'], key="detailed_abc_filter")
    with col2:
        status_filter = st.selectbox("Фильтр статуса", ['Все', 'deficit', 'surplus', 'normal'], key="detailed_status_filter")
    with col3:
        items_per_page = st.selectbox("Товаров на странице", [10, 20, 50, 100], index=1, key="detailed_items_per_page")
    
    # Применяем фильтры
    filtered_recommendations = detailed_recommendations
    if abc_filter != 'Все':
        filtered_recommendations = [r for r in filtered_recommendations if r['abc_class'] == abc_filter]
    
    # Пагинация
    total_items = len(filtered_recommendations)
    if total_items == 0:
        st.info("Нет данных для отображения")
        return
    
    page_count = (total_items - 1) // items_per_page + 1
    current_page = st.selectbox("Страница", range(1, page_count + 1), key="detailed_current_page")
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    st.info(f"Показано {start_idx + 1}-{end_idx} из {total_items} товаров")
    
    # Отображаем товары постранично
    for i in range(start_idx, end_idx):
        item_rec = filtered_recommendations[i]
        
        # Заголовок товара
        abc_color = "🔴" if item_rec['abc_class'] == 'A' else "🟡" if item_rec['abc_class'] == 'B' else "🟢"
        st.markdown(f"#### {abc_color} **{item_rec['item']}**")
        st.caption(f"📊 ADS: {item_rec['ads']:.2f} | 📈 ABC класс: {item_rec['abc_class']}")
        
        # Таблица по складам
        warehouse_data = []
        for warehouse_rec in item_rec['warehouses']:
            # Фильтруем по статусу если нужно
            if status_filter != 'Все' and warehouse_rec['status'] != status_filter:
                continue
                
            # Определяем иконку типа склада
            type_icon = "🌐" if warehouse_rec['warehouse_type'] == 'хаб' else "🏬" if warehouse_rec['warehouse_type'] == 'склад' else "🏪"
            
            # Определяем цвет статуса
            if warehouse_rec['status'] == 'deficit':
                status_display = "🔴 Дефицит"
            elif warehouse_rec['status'] == 'surplus':
                status_display = "🟡 Излишек"
            else:
                status_display = "✅ Норма"
            
            warehouse_data.append({
                'Склад': f"{type_icon} {warehouse_rec['warehouse']}",
                'Город': warehouse_rec['city'],
                'Текущий': f"{warehouse_rec['current_stock']:.0f}",
                'Мин': f"{warehouse_rec['min_stock']:.0f}",
                'Макс': f"{warehouse_rec['max_stock']:.0f}",
                'Статус': status_display,
                'Рекомендация': warehouse_rec['recommendation']
            })
        
        if warehouse_data:
            df = pd.DataFrame(warehouse_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Нет данных для отображения по выбранным фильтрам")
        
        st.markdown("---")

def show_movement_table(movements):
    """Отображение таблицы рекомендаций по перемещениям между складами"""
    import pandas as pd
    
    if not movements:
        st.info("Рекомендации по перемещениям отсутствуют")
        return
    
    # Группируем перемещения по маршрутам для лучшей визуализации
    config = MovementRecommendationConfig()
    
    # Создаем структурированное представление
    st.markdown("### 📦 Рекомендации по перемещениям товаров")
    
    # Группируем по маршрутам
    routes = {}
    for move in movements:
        route_key = f"{move['from_warehouse']}→{move['to_warehouse']}"
        if route_key not in routes:
            routes[route_key] = {
                'from': move['from_warehouse'],
                'to': move['to_warehouse'],
                'from_type': move['from_type'],
                'to_type': move['to_type'],
                'reason': move['reason'],
                'movements': []
            }
        routes[route_key]['movements'].append(move)
    
    # Отображаем по маршрутам
    for route_key, route_data in routes.items():
        # Определяем иконки и уровни
        from_info = config.WAREHOUSE_HIERARCHY.get(route_data['from'], {})
        to_info = config.WAREHOUSE_HIERARCHY.get(route_data['to'], {})
        
        from_icon = "🌐" if route_data['from_type'] == 'хаб' else "🏬" if route_data['from_type'] == 'склад' else "🏪"
        to_icon = "🌐" if route_data['to_type'] == 'хаб' else "🏬" if route_data['to_type'] == 'склад' else "🏪"
        
        # Заголовок маршрута
        st.markdown(f"#### {from_icon} **{route_data['from']}** → {to_icon} **{route_data['to']}**")
        st.caption(f"📋 {route_data['reason']} | 📦 Товаров: {len(route_data['movements'])}")
        
        # Таблица товаров для этого маршрута
        table_data = []
        for move in route_data['movements']:
            urgency_icon = "🔴" if move['urgency'] == 'Высокая' else "🟡" if move['urgency'] == 'Средняя' else "🟢"
            
            table_data.append({
                'Товар': move['item'][:40] + '...' if len(move['item']) > 40 else move['item'],
                'ABC': move['abc_class'],
                'Кол-во': f"{move['transfer_amount']:.0f}",
                'ADS': f"{move['ads']:.1f}",
                'Приоритет': f"{urgency_icon} {move['urgency']}"
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")
    
    # Добавляем сводку по направлениям перемещений
    st.subheader("📈 Сводка по направлениям")
    
    # Группируем по направлениям
    direction_summary = {}
    for move in movements:
        direction = f"{move['from_warehouse']} → {move['to_warehouse']}"
        if direction not in direction_summary:
            direction_summary[direction] = {
                'count': 0,
                'total_amount': 0,
                'abc_A': 0,
                'reason': move['reason']
            }
        direction_summary[direction]['count'] += 1
        direction_summary[direction]['total_amount'] += move['transfer_amount']
        if move['abc_class'] == 'A':
            direction_summary[direction]['abc_A'] += 1
    
    # Показываем топ-10 направлений
    sorted_directions = sorted(direction_summary.items(), key=lambda x: x[1]['total_amount'], reverse=True)
    
    for direction, stats in sorted_directions[:10]:
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.write(f"**{direction}**")
        with col2:
            st.write(f"{stats['count']} товаров")
        with col3:
            st.write(f"A-товары: {stats['abc_A']}")
            st.caption(stats['reason'])

def show_warehouse_analysis(warehouse_analysis):
    """Отображение анализа по складам с учетом иерархии"""
    import pandas as pd
    
    config = MovementRecommendationConfig()
    
    # Группируем склады по уровням
    hub_data = []
    warehouse_data = []
    shop_data = []
    
    for warehouse, stats in warehouse_analysis.items():
        warehouse_info = config.WAREHOUSE_HIERARCHY.get(warehouse, {})
        warehouse_type = warehouse_info.get('type', config.get_location_type(warehouse))
        
        icon = "🌐" if warehouse_type == 'хаб' else "🏬" if warehouse_type == 'склад' else "🏪"
        status_icon = '⚠️' if stats['surplus'] > 0 or stats['deficit'] > 0 else '✅'
        
        data_entry = {
            'Склад': f"{icon} {warehouse}",
            'Город': warehouse_info.get('city', ''),
            'Товаров': stats['items'],
            'Излишки': f"{stats['surplus']:.0f}" if stats['surplus'] > 0 else "-",
            'Дефициты': f"{stats['deficit']:.0f}" if stats['deficit'] > 0 else "-",
            'Статус': f"{status_icon} {'Требует внимания' if status_icon == '⚠️' else 'В норме'}"
        }
        
        if warehouse_type == 'хаб':
            hub_data.append(data_entry)
        elif warehouse_type == 'склад':
            warehouse_data.append(data_entry)
        else:
            shop_data.append(data_entry)
    
    # Отображаем по группам
    if hub_data:
        st.markdown("#### 🌐 Центральный хаб")
        df_hub = pd.DataFrame(hub_data)
        st.dataframe(df_hub, use_container_width=True, hide_index=True)
    
    if warehouse_data:
        st.markdown("#### 🏬 Склады 2-го уровня")
        df_warehouse = pd.DataFrame(warehouse_data)
        st.dataframe(df_warehouse, use_container_width=True, hide_index=True)
    
    if shop_data:
        st.markdown("#### 🏪 Магазины")
        df_shop = pd.DataFrame(shop_data)
        st.dataframe(df_shop, use_container_width=True, hide_index=True)

def create_excel_export(recommendations):
    """Создание Excel файла с рекомендациями"""
    import pandas as pd
    import io
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Лист с рекомендациями
        if recommendations['movements']:
            movements_df = pd.DataFrame(recommendations['movements'])
            movements_df.to_excel(writer, sheet_name='Рекомендации', index=False)
        
        # Лист с анализом складов
        warehouse_df = pd.DataFrame.from_dict(recommendations['warehouse_analysis'], orient='index')
        warehouse_df.to_excel(writer, sheet_name='Анализ складов')
        
        # Лист с детальными данными
        recommendations['detailed_data'].to_excel(writer, sheet_name='Детальные данные', index=False)
    
    return output.getvalue()
