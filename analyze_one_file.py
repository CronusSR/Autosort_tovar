#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ одного конкретного файла
"""

import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

def read_excel_simple(file_path, max_rows=30):
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

def analyze_file(file_path):
    """Анализ файла"""
    print(f"=== ФАЙЛ: {file_path} ===")
    
    rows = read_excel_simple(file_path, 30)
    
    if not rows:
        print("Не удалось прочитать данные")
        return
    
    print(f"\nПрочитано строк: {len(rows)}")
    print("\nСТРУКТУРА ФАЙЛА (первые 20 строк):")
    print("-" * 120)
    
    for i, row in enumerate(rows[:20]):
        # Показываем первые 10 колонок
        display_row = []
        for j, cell in enumerate(row[:10]):
            if cell:
                cell_str = str(cell)
                if len(cell_str) > 12:
                    cell_str = cell_str[:9] + "..."
                display_row.append(cell_str)
            else:
                display_row.append("")
        
        print(f"Строка {i:2d}: {' | '.join(f'{val:12s}' for val in display_row)}")
    
    print("\n" + "=" * 120)
    print("АНАЛИЗ ЗАГОЛОВКОВ:")
    print("-" * 60)
    
    # Ищем строки с заголовками
    header_candidates = []
    for i, row in enumerate(rows[:15]):
        non_empty = [str(cell).strip() for cell in row if cell and str(cell).strip()]
        if len(non_empty) >= 3:
            row_text = ' '.join(cell.lower() for cell in non_empty[:8])
            header_score = 0
            
            # Проверяем ключевые слова
            keywords = ['наименование', 'код', 'артикул', 'название', 'товар', 'сумма', 'количество', 'выручка', 'категория', 'подкатегория']
            for keyword in keywords:
                if keyword in row_text:
                    header_score += 1
            
            if header_score > 0:
                header_candidates.append((i, non_empty[:8], header_score))
    
    # Сортируем кандидатов по score
    header_candidates.sort(key=lambda x: x[2], reverse=True)
    
    for i, headers, score in header_candidates:
        print(f"Строка {i:2d} (score={score}): {headers}")
    
    print("\n" + "=" * 120)
    print("СТРУКТУРА КОЛОНОК (на основе лучшего заголовка):")
    print("-" * 60)
    
    if header_candidates:
        best_header_row = header_candidates[0][0]
        headers = rows[best_header_row]
        
        print(f"Заголовки из строки {best_header_row}:")
        for j, header in enumerate(headers[:15]):
            if header and str(header).strip():
                print(f"  Колонка {j+1:2d}: {header}")
    
    return rows, header_candidates

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Введите путь к файлу: ")
    
    if Path(file_path).exists():
        analyze_file(file_path)
    else:
        print(f"Файл не найден: {file_path}")