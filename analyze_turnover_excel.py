#!/usr/bin/env python3
"""
Анализатор файла оборачиваемости для понимания структуры ABC анализа
"""

import pandas as pd
import numpy as np
import sys

def analyze_turnover_file():
    """Анализирует файл оборачиваемости и структуру ABC анализа"""
    
    file_path = "ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx"
    
    try:
        # Получаем список листов
        xl_file = pd.ExcelFile(file_path)
        print(f"📊 Листы в файле: {xl_file.sheet_names}")
        print("=" * 60)
        
        # Анализируем лист ОСТАТКИ
        if 'ОСТАТКИ' in xl_file.sheet_names:
            print("\n🔍 АНАЛИЗ ЛИСТА 'ОСТАТКИ':")
            try:
                df_ostatok = pd.read_excel(file_path, sheet_name='ОСТАТКИ', header=0)
                print(f"Размер: {df_ostatok.shape}")
                print(f"Колонки: {list(df_ostatok.columns)}")
                
                # Анализируем колонки AD, Q, S (в Excel нумерация с 1, в pandas с 0)
                # AD = 30-я колонка (индекс 29)
                # Q = 17-я колонка (индекс 16) 
                # S = 19-я колонка (индекс 18)
                
                if len(df_ostatok.columns) > 29:
                    print(f"\nКолонка AD (индекс 29): {df_ostatok.columns[29] if 29 < len(df_ostatok.columns) else 'НЕТ'}")
                    if 29 < len(df_ostatok.columns):
                        print(f"Примеры значений AD: {df_ostatok.iloc[:5, 29].tolist()}")
                        print(f"Тип данных AD: {df_ostatok.dtypes[29]}")
                
                if len(df_ostatok.columns) > 16:
                    print(f"\nКолонка Q (индекс 16): {df_ostatok.columns[16] if 16 < len(df_ostatok.columns) else 'НЕТ'}")
                    if 16 < len(df_ostatok.columns):
                        print(f"Примеры значений Q: {df_ostatok.iloc[:5, 16].tolist()}")
                        print(f"Уникальные значения Q: {df_ostatok.iloc[:, 16].unique()[:10]}")
                
                if len(df_ostatok.columns) > 18:
                    print(f"\nКолонка S (индекс 18): {df_ostatok.columns[18] if 18 < len(df_ostatok.columns) else 'НЕТ'}")
                    if 18 < len(df_ostatok.columns):
                        print(f"Примеры значений S: {df_ostatok.iloc[:5, 18].tolist()}")
                        print(f"Уникальные значения S: {df_ostatok.iloc[:, 18].unique()[:10]}")
                
                # Выводим первые несколько строк для анализа
                print(f"\n📋 Первые 3 строки данных:")
                print(df_ostatok.head(3).to_string())
                
            except Exception as e:
                print(f"Ошибка при чтении листа ОСТАТКИ: {e}")
        
        # Анализируем лист ABC ПО СКЛАДАМ
        if 'ABC ПО СКЛАДАМ' in xl_file.sheet_names:
            print("\n\n🔍 АНАЛИЗ ЛИСТА 'ABC ПО СКЛАДАМ':")
            try:
                df_abc = pd.read_excel(file_path, sheet_name='ABC ПО СКЛАДАМ', header=0)
                print(f"Размер: {df_abc.shape}")
                print(f"Колонки: {list(df_abc.columns)}")
                
                # Анализируем структуру ABC анализа
                print(f"\n📋 Первые 10 строк ABC анализа:")
                print(df_abc.head(10).to_string())
                
                # Ищем категорию "Клей"
                if not df_abc.empty:
                    # Проверяем первую колонку на наличие "Клей"
                    first_col = df_abc.columns[0]
                    klei_rows = df_abc[df_abc[first_col].astype(str).str.contains('Клей', case=False, na=False)]
                    if not klei_rows.empty:
                        print(f"\n🔍 Найдены строки с 'Клей':")
                        print(klei_rows.to_string())
                    
                    # Также проверяем в строке 3 (индекс 2) колонку C
                    if len(df_abc.columns) > 2 and len(df_abc) > 2:
                        c3_value = df_abc.iloc[2, 2]  # C3 в Excel = индекс [2,2] в pandas
                        print(f"\nЗначение C3: {c3_value}")
                
            except Exception as e:
                print(f"Ошибка при чтении листа ABC ПО СКЛАДАМ: {e}")
        
        # Проверяем другие листы
        for sheet_name in xl_file.sheet_names:
            if sheet_name not in ['ОСТАТКИ', 'ABC ПО СКЛАДАМ']:
                print(f"\n📄 Лист '{sheet_name}':")
                try:
                    df_temp = pd.read_excel(file_path, sheet_name=sheet_name, header=0, nrows=5)
                    print(f"Размер: {df_temp.shape}")
                    print(f"Первые колонки: {list(df_temp.columns[:5])}")
                except Exception as e:
                    print(f"Ошибка при чтении: {e}")
        
    except FileNotFoundError:
        print(f"❌ Файл {file_path} не найден!")
        return
    except Exception as e:
        print(f"❌ Ошибка при анализе файла: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ Анализ завершен!")

if __name__ == "__main__":
    analyze_turnover_file()