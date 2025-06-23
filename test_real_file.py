#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест реальных файлов для проверки извлечения цен
"""

import pandas as pd
import sys
import os

def test_barys_file():
    """Тестируем файл Барыс"""
    barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if not os.path.exists(barys_file):
        print(f"❌ Файл не найден: {barys_file}")
        return
    
    try:
        print(f"📁 Анализ файла: {barys_file}")
        
        # Читаем файл
        df = pd.read_excel(barys_file, engine='openpyxl')
        print(f"📊 Размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # Показываем заголовки
        print(f"\n📋 Колонки (первые 15):")
        for i, col in enumerate(df.columns[:15]):
            print(f"   {i+1:2d}. {col}")
        
        # Проверяем колонку 12 (индекс 11)
        if df.shape[1] > 11:
            col_12_name = df.columns[11]
            print(f"\n🔍 Колонка 12 (L): '{col_12_name}'")
            
            # Смотрим данные с 4-й строки
            print(f"\n📋 Данные в колонке 12, начиная с строки 4:")
            for i in range(3, min(10, len(df))):  # строки 4-10
                value = df.iloc[i, 11]
                nomenclature = df.iloc[i, 1] if df.shape[1] > 1 else "N/A"
                print(f"   Строка {i+1}: {nomenclature} | Цена: {value}")
        
        # Тестируем функцию из integration_patch
        print(f"\n🧪 Тестируем функцию извлечения цен...")
        
        # Имитируем process_single_file_safe
        start_col_index = 12  # M
        end_col_index = 28    # AB
        start_row = 3         # Строка 4
        nomenclature_col = 1  # B
        price_col = 11        # L (12-я колонка)
        
        # Получаем номенклатуру
        nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
        nomenclature_clean = nomenclature_data.dropna()
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
        
        if len(nomenclature_clean) > 0:
            nomenclature_clean = nomenclature_clean[:-1]  # Исключаем последнюю строку
        
        print(f"✅ Найдено номенклатуры: {len(nomenclature_clean)} товаров")
        
        # Извлекаем цены
        prices_found = 0
        sample_prices = []
        
        for i, idx in enumerate(nomenclature_clean.index[:10]):  # Первые 10 для примера
            item_name = str(nomenclature_clean.loc[idx]).strip()
            
            # Извлекаем цену
            price_value = 0
            if df.shape[1] > price_col:
                try:
                    price_raw = df.iloc[idx, price_col]
                    if pd.notna(price_raw):
                        price_value = float(price_raw)
                        if price_value > 0:
                            prices_found += 1
                            sample_prices.append((item_name, price_value))
                except (ValueError, TypeError):
                    price_value = 0
        
        print(f"💰 Найдено цен: {prices_found} из первых 10 товаров")
        
        if sample_prices:
            print(f"\n📋 Примеры найденных цен:")
            for name, price in sample_prices[:5]:
                print(f"   {name[:40]} = {price:,.0f} ₸")
        else:
            print(f"❌ Цены не найдены в колонке 12")
            
            # Попробуем найти колонку с ценами
            print(f"\n🔍 Поиск колонок с ценами...")
            for i, col in enumerate(df.columns):
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['цена', 'price', 'стоимость', 'закуп']):
                    print(f"   Колонка {i+1}: '{col}' - возможно содержит цены")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_barys_file()