#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный скрипт для анализа структуры файла остатков
"""

import pandas as pd
import sys
import os

def debug_stock_file():
    """Детальный анализ файла остатков"""
    
    filename = 'остатки на 08.07.2025.xlsx'
    
    if not os.path.exists(filename):
        print(f"❌ Файл {filename} не найден")
        return
    
    try:
        # Читаем файл
        df = pd.read_excel(filename, engine='openpyxl')
        
        print("=== АНАЛИЗ ФАЙЛА ОСТАТКОВ ===")
        print(f"Файл: {filename}")
        print(f"Размер: {df.shape[0]} строк, {df.shape[1]} колонок")
        print()
        
        print("=== ПЕРВЫЕ 15 СТРОК ПОЛНОСТЬЮ ===")
        for i in range(min(15, len(df))):
            print(f"Строка {i}:")
            row = df.iloc[i]
            for j, value in enumerate(row):
                if pd.notna(value) and str(value).strip():
                    print(f"  Колонка {j}: {value}")
            print()
        
        print("=== ПОИСК ЗАГОЛОВКОВ ===")
        for i in range(min(20, len(df))):
            row = df.iloc[i]
            has_nomenclature = any('номенклатура' in str(cell).lower() for cell in row if pd.notna(cell))
            has_numbers = sum(1 for cell in row if pd.notna(cell) and str(cell).replace('.', '').replace(',', '').replace('-', '').isdigit()) >= 3
            
            print(f"Строка {i}: Номенклатура={has_nomenclature}, Числа={has_numbers}")
            if has_nomenclature:
                print(f"  Содержимое: {[str(cell) for cell in row if pd.notna(cell)]}")
        
        print("\n=== АНАЛИЗ КОЛОНОК ===")
        print("Названия колонок по умолчанию:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        print("\n=== ПОИСК ДАННЫХ ТОВАРОВ ===")
        for i in range(min(50, len(df))):
            row = df.iloc[i]
            # Ищем строки с текстом в первой колонке и числами в других
            first_col = row.iloc[0] if len(row) > 0 else None
            if pd.notna(first_col) and len(str(first_col)) > 5:  # Предполагаем что название товара > 5 символов
                numbers_count = sum(1 for cell in row[1:8] if pd.notna(cell) and str(cell).replace('.', '').replace(',', '').isdigit())
                if numbers_count >= 2:
                    print(f"Строка {i} (возможный товар): {str(first_col)[:50]}... | Чисел: {numbers_count}")
                    print(f"  Данные: {[cell for cell in row[1:9] if pd.notna(cell)]}")
                    if i > 40:  # Показываем только первые несколько
                        break
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_stock_file()