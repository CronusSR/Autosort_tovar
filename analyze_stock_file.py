#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys

def analyze_stock_file():
    try:
        # Читаем файл остатков
        df = pd.read_excel('остатки на 08.07.2025.xlsx')
        
        print('=== СТРУКТУРА ФАЙЛА ОСТАТКОВ ===')
        print(f'Размер: {df.shape[0]} строк, {df.shape[1]} колонок')
        print()
        
        print('=== НАЗВАНИЯ КОЛОНОК ===')
        for i, col in enumerate(df.columns):
            print(f'{i:2d}: {repr(col)}')
        print()
        
        print('=== ПЕРВЫЕ 10 СТРОК (только первые 5 колонок) ===')
        print(df.iloc[:10, :5].to_string())
        print()
        
        print('=== ПОИСК КОЛОНКИ С НАИМЕНОВАНИЯМИ ===')
        potential_name_cols = []
        
        for i, col in enumerate(df.columns):
            col_name = str(col).lower()
            # Проверяем наличие ключевых слов
            if any(keyword in col_name for keyword in ['наименование', 'номенклатура', 'товар', 'name', 'product']):
                potential_name_cols.append((i, col))
                print(f'✅ Найдена потенциальная колонка с наименованиями: {i} - {repr(col)}')
        
        if not potential_name_cols:
            print('❌ Не найдено колонок с ключевыми словами')
            print('🔍 Анализируем содержимое первых колонок...')
            
            for i in range(min(5, len(df.columns))):
                col = df.columns[i]
                print(f'\nКолонка {i}: {repr(col)}')
                # Показываем первые несколько значений
                sample_values = df[col].dropna().head(5).tolist()
                print(f'Примеры значений: {sample_values}')
                
                # Проверяем, похоже ли на наименования товаров
                if df[col].dtype == 'object':  # текстовая колонка
                    non_null_count = df[col].notna().sum()
                    unique_count = df[col].nunique()
                    print(f'Непустых значений: {non_null_count}, Уникальных: {unique_count}')
                    
                    if non_null_count > 0 and unique_count > 1:
                        print('✅ Похоже на колонку с наименованиями товаров')
        
        print('\n=== АНАЛИЗ ЧИСЛОВЫХ КОЛОНОК (возможные остатки) ===')
        numeric_cols = []
        for i, col in enumerate(df.columns):
            if df[col].dtype in ['int64', 'float64'] or pd.to_numeric(df[col], errors='coerce').notna().any():
                sum_val = pd.to_numeric(df[col], errors='coerce').sum()
                if sum_val > 0:
                    numeric_cols.append((i, col, sum_val))
                    print(f'Колонка {i:2d}: {repr(col):50} | Сумма: {sum_val:,.0f}')
        
        print(f'\nНайдено {len(numeric_cols)} колонок с числовыми данными')
        
    except Exception as e:
        print(f'❌ Ошибка анализа файла: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_stock_file()