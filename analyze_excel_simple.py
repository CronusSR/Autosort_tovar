#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой анализ структуры Excel файла без pandas
"""

import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def read_excel_simple(file_path, max_rows=20):
    """Простое чтение Excel файла через zip"""
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Читаем shared strings
            shared_strings = []
            try:
                with zip_file.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        t = si.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                        if t is not None:
                            shared_strings.append(t.text or '')
                        else:
                            shared_strings.append('')
            except:
                shared_strings = []
            
            # Читаем первый лист
            try:
                with zip_file.open('xl/worksheets/sheet1.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    
                    rows_data = []
                    for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                        row_num = int(row.get('r', 0))
                        if row_num > max_rows:
                            break
                            
                        row_data = [''] * 20  # До 20 колонок
                        
                        for cell in row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            cell_ref = cell.get('r', '')
                            col_idx = 0
                            if cell_ref:
                                # Извлекаем номер колонки из A1, B1 и т.д.
                                col_letter = ''.join(c for c in cell_ref if c.isalpha())
                                col_idx = sum((ord(c) - ord('A') + 1) * (26 ** i) for i, c in enumerate(reversed(col_letter))) - 1
                            
                            if col_idx < len(row_data):
                                value_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                if value_elem is not None:
                                    value = value_elem.text or ''
                                    cell_type = cell.get('t', '')
                                    
                                    if cell_type == 's' and shared_strings:  # Shared string
                                        try:
                                            idx = int(value)
                                            if 0 <= idx < len(shared_strings):
                                                value = shared_strings[idx]
                                        except:
                                            pass
                                    
                                    row_data[col_idx] = value
                        
                        rows_data.append(row_data)
                    
                    return rows_data
            except Exception as e:
                print(f"Ошибка чтения листа: {e}")
                return []
                
    except Exception as e:
        print(f"Ошибка открытия файла: {e}")
        return []

def analyze_simple_structure(file_path):
    """Анализ структуры файла"""
    print(f"=== АНАЛИЗ ФАЙЛА: {file_path} ===")
    
    if not Path(file_path).exists():
        print(f"Файл не найден: {file_path}")
        return
    
    rows = read_excel_simple(file_path)
    
    if not rows:
        print("Не удалось прочитать данные из файла")
        return
    
    print(f"Прочитано строк: {len(rows)}")
    print("\nПЕРВЫЕ 15 СТРОК:")
    print("-" * 100)
    
    for i, row in enumerate(rows[:15]):
        # Показываем только первые 8 колонок для читаемости
        display_row = []
        for j, cell in enumerate(row[:8]):
            if cell and len(str(cell)) > 15:
                display_row.append(str(cell)[:12] + "...")
            else:
                display_row.append(str(cell) if cell else "")
        
        print(f"Строка {i:2d}: {' | '.join(f'{val:15s}' for val in display_row)}")
    
    print("\n" + "=" * 100)
    print("ПОИСК ЗАГОЛОВКОВ:")
    print("-" * 50)
    
    # Ищем строки с возможными заголовками
    for i, row in enumerate(rows[:15]):
        non_empty = [cell for cell in row if cell and str(cell).strip()]
        if len(non_empty) >= 3:  # Строка с несколькими значениями
            row_text = ' '.join(str(cell).lower() for cell in non_empty[:6])
            if any(keyword in row_text for keyword in ['наименование', 'код', 'артикул', 'название', 'товар', 'сумма', 'количество']):
                print(f"Строка {i:2d} (заголовки): {non_empty[:6]}")
    
    print("\n" + "=" * 100)
    print("АНАЛИЗ ПОДКАТЕГОРИЙ:")
    print("-" * 50)
    
    # Ищем строки с подкатегориями (мало данных, но есть текст)
    for i, row in enumerate(rows[:20]):
        non_empty = [cell for cell in row if cell and str(cell).strip()]
        if 1 <= len(non_empty) <= 2:  # Строки с 1-2 значениями
            print(f"Строка {i:2d} (подкатегория?): {non_empty}")

if __name__ == "__main__":
    # Анализируем файлы
    files_to_analyze = [
        "барыс - прод с мая24-май25.xlsx",
        "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx",
        "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    ]
    
    for file_path in files_to_analyze:
        if Path(file_path).exists():
            analyze_simple_structure(file_path)
            print("\n" + "=" * 120 + "\n")
        else:
            print(f"Файл не найден: {file_path}")