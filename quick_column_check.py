#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка колонки 12 в файле Барыс
"""

import pandas as pd

def quick_check():
    """Быстрая проверка данных в колонке 12"""
    
    print("🔍 Быстрая проверка колонки 12 в файле Барыс")
    print("=" * 50)
    
    try:
        # Читаем файл
        # Поддержка как Linux, так и Windows путей
        import os
        if os.name == 'nt':  # Windows
            barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
        else:  # Linux/WSL
            barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
        df = pd.read_excel(barys_file)
        
        print(f"✅ Файл загружен: {df.shape}")
        
        if len(df.columns) < 12:
            print(f"❌ Недостаточно колонок: {len(df.columns)}")
            return
        
        # Колонка 12 (индекс 11)
        col_12_name = df.columns[11]
        print(f"📋 Название 12-й колонки: '{col_12_name}'")
        
        # Показываем данные с L4 (строка 4, индекс 3)
        print(f"\n📊 Данные в колонке 12, начиная с L4:")
        print("-" * 60)
        
        for i in range(3, min(15, len(df))):  # L4-L15
            row_num = i + 1
            nomenclature = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
            value = df.iloc[i, 11]  # Колонка 12
            
            # Простая проверка на число
            is_number = False
            converted_value = 0
            
            if pd.notna(value):
                try:
                    converted_value = float(value)
                    if converted_value > 0:
                        is_number = True
                except:
                    pass
            
            status = "✅" if is_number else "❌"
            print(f"{status} L{row_num}: {nomenclature[:25]:25} | {str(value)[:15]:15} | Тип: {type(value).__name__:10} | {converted_value if is_number else 'Не число'}")
        
        print("\n" + "=" * 50)
        
        # Анализ всех данных с L4
        all_data = df.iloc[3:, 11]  # Все данные начиная с L4
        total_rows = len(all_data)
        
        valid_numbers = 0
        for value in all_data:
            if pd.notna(value):
                try:
                    num_val = float(value)
                    if num_val > 0:
                        valid_numbers += 1
                except:
                    pass
        
        print(f"📈 ИТОГО:")
        print(f"   Всего строк с L4: {total_rows}")
        print(f"   Валидных цен: {valid_numbers}")
        print(f"   Покрытие: {valid_numbers/total_rows*100:.1f}%" if total_rows > 0 else "   Покрытие: 0%")
        
        if valid_numbers == 0:
            print(f"\n❌ ПРОБЛЕМА: Ни одной валидной цены не найдено!")
            print(f"🔍 Возможные причины:")
            print(f"   1. Цены находятся в другой колонке")
            print(f"   2. Цены имеют нестандартный формат")
            print(f"   3. Данные начинаются не с L4")
            
            # Ищем цены в других колонках
            print(f"\n🔍 Поиск цен в других колонках:")
            for col_idx in range(min(15, len(df.columns))):
                col_name = df.columns[col_idx]
                if 'цена' in str(col_name).lower() or 'price' in str(col_name).lower() or 'закуп' in str(col_name).lower():
                    print(f"   Колонка {col_idx+1} ({chr(65+col_idx)}): '{col_name}' - возможно содержит цены")
        else:
            print(f"\n✅ Цены найдены! Логика извлечения должна работать.")
    
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_check()