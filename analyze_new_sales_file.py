#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры нового файла продаж с всеми филиалами
"""

import sys
import os

# Попытка импорта pandas разными способами
try:
    import pandas as pd
except ImportError:
    print("Pandas не установлен, пытаемся использовать альтернативный метод...")
    # Попробуем прочитать файл как текст
    import csv
    
def analyze_excel_structure(filename):
    """Анализ структуры Excel файла"""
    try:
        # Пытаемся прочитать с pandas
        import pandas as pd
        
        # Читаем файл
        df = pd.read_excel(filename, engine='openpyxl')
        
        print(f"=== Анализ файла: {filename} ===\n")
        print(f"Размер: {df.shape[0]} строк, {df.shape[1]} колонок\n")
        
        print("Колонки:")
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")
        
        print("\n=== Первые 5 строк ===")
        print(df.head())
        
        # Проверяем наличие колонки Филиал
        if 'Филиал' in df.columns:
            print("\n=== Уникальные филиалы ===")
            unique_branches = df['Филиал'].unique()
            for branch in unique_branches:
                count = len(df[df['Филиал'] == branch])
                print(f"- {branch}: {count} записей")
        
        # Проверяем структуру данных
        print("\n=== Типы данных ===")
        print(df.dtypes)
        
        # Проверяем наличие важных колонок
        important_columns = ['Филиал', 'Товар', 'Количество', 'Сумма', 'Цена', 'Дата']
        print("\n=== Проверка важных колонок ===")
        for col in important_columns:
            if col in df.columns:
                print(f"✓ {col} - найдена")
            else:
                # Ищем похожие колонки
                similar = [c for c in df.columns if col.lower() in c.lower()]
                if similar:
                    print(f"? {col} - не найдена, но есть похожие: {similar}")
                else:
                    print(f"✗ {col} - не найдена")
        
        # Сохраняем информацию о структуре
        with open('file_structure_analysis.txt', 'w', encoding='utf-8') as f:
            f.write(f"Файл: {filename}\n")
            f.write(f"Размер: {df.shape[0]} строк, {df.shape[1]} колонок\n\n")
            f.write("Колонки:\n")
            for i, col in enumerate(df.columns):
                f.write(f"{i}: {col}\n")
            
            if 'Филиал' in df.columns:
                f.write("\nФилиалы:\n")
                for branch in unique_branches:
                    count = len(df[df['Филиал'] == branch])
                    f.write(f"- {branch}: {count} записей\n")
        
        print("\n✓ Анализ завершен. Результаты сохранены в file_structure_analysis.txt")
        
    except ImportError:
        print("Pandas не доступен. Используем альтернативный метод...")
        # Простой анализ без pandas
        print(f"Файл: {filename}")
        print(f"Размер файла: {os.path.getsize(filename)} байт")
        print("\nДля полного анализа требуется установка pandas")
        
    except Exception as e:
        print(f"Ошибка при анализе файла: {e}")
        print(f"Тип ошибки: {type(e)}")

if __name__ == "__main__":
    filename = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    
    if os.path.exists(filename):
        analyze_excel_structure(filename)
    else:
        print(f"Файл {filename} не найден!")
        print(f"Текущая директория: {os.getcwd()}")
        print("\nДоступные Excel файлы:")
        for f in os.listdir('.'):
            if f.endswith(('.xlsx', '.xls')):
                print(f"- {f}")