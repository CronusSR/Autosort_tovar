#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для анализа реального файла продаж
"""

import pandas as pd
import numpy as np

def analyze_sales_file(file_path):
    """Детальный анализ файла продаж"""
    
    print(f"\n{'='*60}")
    print(f"АНАЛИЗ ФАЙЛА: {file_path}")
    print(f"{'='*60}\n")
    
    # Читаем файл без заголовков
    df = pd.read_excel(file_path, header=None)
    
    print(f"📊 Размер файла: {df.shape[0]} строк x {df.shape[1]} колонок\n")
    
    # Показываем первые 15 строк для понимания структуры
    print("🔍 ПЕРВЫЕ 15 СТРОК ФАЙЛА:")
    print("-" * 60)
    for i in range(min(15, len(df))):
        row_data = []
        for j in range(min(5, len(df.columns))):
            val = df.iloc[i, j]
            if pd.notna(val):
                row_data.append(f"{str(val)[:30]}")
            else:
                row_data.append("---")
        print(f"Строка {i+1:2d}: {' | '.join(row_data)}")
    
    # Ищем период в строке 4
    print(f"\n📅 ПОИСК ПЕРИОДА (строка 4):")
    row_4 = df.iloc[3]  # Индекс 3 = строка 4
    for cell in row_4:
        if pd.notna(cell) and 'период' in str(cell).lower():
            print(f"   Найдено: {cell}")
            break
    
    # Анализируем строку 9 с заголовками
    print(f"\n📋 ЗАГОЛОВКИ (строка 9):")
    row_9 = df.iloc[8]  # Индекс 8 = строка 9
    headers = []
    for i, header in enumerate(row_9):
        if pd.notna(header):
            headers.append((i, str(header).strip()))
            print(f"   Колонка {i}: {header}")
    
    # Устанавливаем заголовки и берем данные
    df.columns = [str(h).strip() if pd.notna(h) else f"Col_{i}" for i, h in enumerate(row_9)]
    df_data = df.iloc[9:].reset_index(drop=True)
    
    print(f"\n📊 ДАННЫЕ начинаются со строки 10, всего строк данных: {len(df_data)}")
    
    # Ищем колонку "Выручка"
    revenue_col = None
    for col in df_data.columns:
        if 'выручка' in str(col).lower():
            revenue_col = col
            print(f"\n✅ Найдена колонка 'Выручка': {repr(col)}")
            break
    
    if not revenue_col:
        print("\n❌ Колонка 'Выручка' не найдена!")
        return
    
    # Анализируем данные по выручке
    print(f"\n💰 АНАЛИЗ ВЫРУЧКИ:")
    print("-" * 60)
    
    total_revenue = 0
    product_count = 0
    
    # Показываем примеры строк с выручкой
    print("\nПримеры строк с выручкой:")
    examples_shown = 0
    
    for idx, row in df_data.iterrows():
        nomenclature = str(row.iloc[0])  # Первая колонка - номенклатура
        revenue_value = row[revenue_col]
        
        # Пропускаем пустые строки
        if pd.isna(row.iloc[0]) or nomenclature.strip() == '' or nomenclature == 'nan':
            continue
        
        # Проверяем, является ли это товаром (не категорией)
        # Товары обычно имеют отступы или специфические признаки
        is_product = (nomenclature.startswith(' ') or 
                     nomenclature.startswith('\t') or
                     any(sign in nomenclature.lower() for sign in ['мм', 'см', '*', '№', 'шт']))
        
        if is_product:
            try:
                revenue_numeric = pd.to_numeric(revenue_value, errors='coerce')
                if pd.notna(revenue_numeric) and revenue_numeric > 0:
                    total_revenue += revenue_numeric
                    product_count += 1
                    
                    if examples_shown < 5:
                        print(f"  Товар: {nomenclature[:50]:<50} | Выручка: {revenue_numeric:>15,.2f}")
                        examples_shown += 1
            except:
                pass
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Всего товаров с выручкой: {product_count}")
    print(f"   Общая выручка: {total_revenue:,.2f}")
    print(f"   Средняя выручка на товар: {total_revenue/product_count:,.2f}" if product_count > 0 else "")
    
    # Проверяем общий итог в файле
    print(f"\n🔍 ПОИСК ИТОГОВОЙ СТРОКИ:")
    for idx in range(len(df_data)-5, len(df_data)):
        if idx >= 0 and idx < len(df_data):
            row = df_data.iloc[idx]
            nomenclature = str(row.iloc[0])
            if 'итого' in nomenclature.lower() or 'всего' in nomenclature.lower():
                revenue_value = row[revenue_col]
                print(f"   Найдена итоговая строка: {nomenclature}")
                print(f"   Итоговая выручка в файле: {revenue_value}")
                break
    
    return total_revenue, product_count

# Анализируем файл
if __name__ == "__main__":
    file_path = "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    
    try:
        total_revenue, product_count = analyze_sales_file(file_path)
    except FileNotFoundError:
        print(f"\n❌ Файл не найден: {file_path}")
        print("Убедитесь, что файл находится в текущей директории")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()