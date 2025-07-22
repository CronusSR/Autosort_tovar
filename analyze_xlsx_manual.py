#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ Excel файла через распаковку ZIP и парсинг XML
"""

import zipfile
import xml.etree.ElementTree as ET
import os
from pathlib import Path

def analyze_xlsx_structure(file_path):
    """Анализирует структуру XLSX файла"""
    print(f"Анализ файла: {file_path}")
    print("=" * 80)
    
    try:
        # XLSX файл - это ZIP архив
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            print("Содержимое XLSX архива:")
            for file_info in zip_file.filelist:
                print(f"  {file_info.filename}")
            
            print("\n" + "-" * 40)
            
            # Читаем shared strings (строковые значения)
            shared_strings = {}
            try:
                with zip_file.open('xl/sharedStrings.xml') as ss_file:
                    ss_content = ss_file.read().decode('utf-8')
                    ss_root = ET.fromstring(ss_content)
                    
                    for i, si in enumerate(ss_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si')):
                        t_elem = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                        if t_elem is not None:
                            shared_strings[i] = t_elem.text
                
                print(f"Найдено {len(shared_strings)} строковых значений")
                print("Первые 20 строковых значений:")
                for i, (idx, value) in enumerate(shared_strings.items()):
                    if i >= 20:
                        break
                    print(f"  {idx}: {value[:50]}{'...' if len(value) > 50 else ''}")
                    
            except Exception as e:
                print(f"Ошибка при чтении shared strings: {e}")
            
            print("\n" + "-" * 40)
            
            # Читаем первый лист
            try:
                with zip_file.open('xl/worksheets/sheet1.xml') as sheet_file:
                    sheet_content = sheet_file.read().decode('utf-8')
                    sheet_root = ET.fromstring(sheet_content)
                    
                    print("Анализ первого листа:")
                    
                    # Находим все строки
                    rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                    print(f"Найдено строк: {len(rows)}")
                    
                    print("\nПервые 30 строк данных:")
                    print("=" * 80)
                    
                    for row_idx, row in enumerate(rows[:30]):
                        row_num = row.get('r', str(row_idx + 1))
                        cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                        
                        row_data = []
                        for cell in cells[:10]:  # Первые 10 колонок
                            cell_ref = cell.get('r', '')
                            cell_type = cell.get('t', '')
                            
                            v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if v_elem is not None:
                                value = v_elem.text
                                
                                # Если это ссылка на shared string
                                if cell_type == 's' and value and value.isdigit():
                                    string_idx = int(value)
                                    if string_idx in shared_strings:
                                        value = shared_strings[string_idx]
                                
                                # Ограничиваем длину для вывода
                                if value and len(str(value)) > 20:
                                    value = str(value)[:17] + "..."
                                    
                                row_data.append(f"{cell_ref}:{value}")
                            else:
                                row_data.append(f"{cell_ref}:пусто")
                        
                        if row_data:  # Показываем только непустые строки
                            print(f"Строка {row_num:2s}: {' | '.join(row_data)}")
                    
                    print("\n" + "=" * 80)
                    print("ПОИСК ПОДКАТЕГОРИЙ:")
                    print("-" * 40)
                    
                    # Ищем строки с подкатегориями (мало ячеек, но есть данные в колонке B)
                    for row_idx, row in enumerate(rows[:100]):
                        row_num = row.get('r', str(row_idx + 1))
                        cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                        
                        # Проверяем есть ли данные в колонке B
                        b_cell_value = None
                        total_cells = len(cells)
                        
                        for cell in cells:
                            cell_ref = cell.get('r', '')
                            if cell_ref.startswith('B'):
                                cell_type = cell.get('t', '')
                                v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                if v_elem is not None:
                                    value = v_elem.text
                                    if cell_type == 's' and value and value.isdigit():
                                        string_idx = int(value)
                                        if string_idx in shared_strings:
                                            b_cell_value = shared_strings[string_idx]
                                    else:
                                        b_cell_value = value
                                break
                        
                        # Если в B есть значение и мало всего ячеек - возможно подкатегория
                        if b_cell_value and total_cells <= 3:
                            print(f"Строка {row_num}: B={b_cell_value} (возможная подкатегория, ячеек: {total_cells})")
                    
            except Exception as e:
                print(f"Ошибка при чтении листа: {e}")
            
    except Exception as e:
        print(f"Ошибка при анализе файла: {e}")

if __name__ == "__main__":
    file_path = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    analyze_xlsx_structure(file_path)