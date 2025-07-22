#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа структуры Excel файла с продажами
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_excel_structure(file_path):
    """Анализирует структуру Excel файла"""
    print(f"Анализ файла: {file_path}")
    print("=" * 80)
    
    try:
        # Загружаем Excel файл
        excel_file = pd.ExcelFile(file_path)
        
        print(f"Листы в файле: {excel_file.sheet_names}")
        print("-" * 40)
        
        # Анализируем первый лист
        sheet_name = excel_file.sheet_names[0]
        print(f"Анализ листа: {sheet_name}")
        
        # Читаем данные без заголовков для полного анализа
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        print(f"Размер данных: {df_raw.shape[0]} строк, {df_raw.shape[1]} колонок")
        print("-" * 40)
        
        # Показываем первые 30 строк для анализа структуры
        print("ПЕРВЫЕ 30 СТРОК ФАЙЛА:")
        print("=" * 80)
        
        for i in range(min(30, len(df_raw))):
            row_data = []
            for j in range(min(10, len(df_raw.columns))):  # Первые 10 колонок
                cell_value = df_raw.iloc[i, j]
                if pd.isna(cell_value):
                    cell_value = "NaN"
                else:
                    cell_value = str(cell_value)
                    if len(cell_value) > 20:
                        cell_value = cell_value[:17] + "..."
                row_data.append(cell_value)
            
            print(f"Строка {i:2d}: {' | '.join(f'{val:20s}' for val in row_data)}")
        
        print("\n" + "=" * 80)
        
        # Анализируем колонки
        print("АНАЛИЗ КОЛОНОК:")
        print("-" * 40)
        
        # Ищем строки с заголовками колонок
        potential_headers = []
        for i in range(min(15, len(df_raw))):
            row = df_raw.iloc[i].dropna()
            if len(row) > 5:  # Если в строке много непустых значений
                potential_headers.append((i, row.tolist()))
        
        for idx, headers in potential_headers:
            print(f"Строка {idx} (возможные заголовки): {headers[:8]}")
        
        print("\n" + "=" * 80)
        
        # Анализируем подкатегории в отдельных строках
        print("ПОИСК ПОДКАТЕГОРИЙ В ЗАГОЛОВКАХ:")
        print("-" * 40)
        
        for i in range(min(50, len(df_raw))):
            # Проверяем строки где в колонке B (индекс 1) есть значение, а остальные пустые
            if len(df_raw.columns) > 1:
                b_cell = df_raw.iloc[i, 1]  # Колонка B
                if not pd.isna(b_cell):
                    # Проверяем, что в соседних колонках мало данных (признак заголовка)
                    row_values = df_raw.iloc[i].dropna()
                    if len(row_values) <= 3:  # Мало значений в строке = вероятно заголовок
                        print(f"Строка {i:2d}: B={b_cell} (возможная подкатегория)")
        
        print("\n" + "=" * 80)
        
        # Анализируем данные о товарах
        print("ПОИСК ТОВАРНЫХ ДАННЫХ:")
        print("-" * 40)
        
        for i in range(min(50, len(df_raw))):
            row = df_raw.iloc[i]
            non_na_count = row.count()
            
            if non_na_count > 5:  # Строки с большим количеством данных
                values = []
                for j in range(min(6, len(row))):
                    val = row.iloc[j]
                    if pd.isna(val):
                        val = "NaN"
                    else:
                        val = str(val)
                        if len(val) > 15:
                            val = val[:12] + "..."
                    values.append(val)
                print(f"Строка {i:2d}: {' | '.join(f'{v:15s}' for v in values)} (товар?)")
        
        # Читаем с автоопределением заголовков для дополнительного анализа
        print("\n" + "=" * 80)
        print("АНАЛИЗ С АВТООПРЕДЕЛЕНИЕМ ЗАГОЛОВКОВ:")
        print("-" * 40)
        
        try:
            df_auto = pd.read_excel(file_path, sheet_name=sheet_name)
            print("Колонки при автоопределении заголовков:")
            for i, col in enumerate(df_auto.columns):
                print(f"  {i}: {col}")
            
            print(f"\nПервые 5 строк с автозаголовками:")
            print(df_auto.head())
            
        except Exception as e:
            print(f"Ошибка при автоопределении заголовков: {e}")
        
    except Exception as e:
        print(f"Ошибка при анализе файла: {e}")

if __name__ == "__main__":
    file_path = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    analyze_excel_structure(file_path)