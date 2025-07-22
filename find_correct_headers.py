#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск правильных заголовков колонок в файле продаж
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

def find_headers_and_data(filename):
    """Поиск заголовков и данных с правильным определением структуры"""
    print(f"=== ДЕТАЛЬНЫЙ АНАЛИЗ СТРУКТУРЫ ФАЙЛА ===")
    print(f"Файл: {filename}\n")
    
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            # 1. Читаем shared strings
            strings = []
            if 'xl/sharedStrings.xml' in zip_file.namelist():
                strings_xml = zip_file.read('xl/sharedStrings.xml')
                strings_root = ET.fromstring(strings_xml)
                
                for si in strings_root.findall('.//si', ns):
                    t = si.find('.//t', ns)
                    if t is not None:
                        strings.append(t.text)
            
            # Выводим строки, которые похожи на заголовки
            print("=== ПОТЕНЦИАЛЬНЫЕ ЗАГОЛОВКИ КОЛОНОК ===")
            header_candidates = []
            for idx, s in enumerate(strings[:50]):
                if any(word in s for word in ['Номенклатура', 'Количество', 'Выручка', 'Себестоимость', 
                                               'прибыль', 'Рентабельность', 'Стоимость', 'расход']):
                    header_candidates.append((idx, s))
                    print(f"String[{idx}]: {s}")
            
            # 2. Читаем лист
            worksheet_files = [f for f in zip_file.namelist() if 'worksheets/sheet' in f and f.endswith('.xml')]
            
            if worksheet_files:
                sheet_xml = zip_file.read(worksheet_files[0])
                root = ET.fromstring(sheet_xml)
                
                rows = root.findall('.//row', ns)
                
                # Читаем каждую строку и ищем строку с заголовками
                print("\n=== АНАЛИЗ СТРОК (первые 20) ===")
                
                for row_idx in range(min(20, len(rows))):
                    row = rows[row_idx]
                    row_attr = row.attrib
                    row_num = row_attr.get('r', row_idx + 1)
                    
                    cells = row.findall('.//c', ns)
                    
                    # Собираем значения из ячеек
                    cell_values = {}
                    for cell in cells:
                        cell_ref = cell.get('r', '')  # Например, A1, B1, C1
                        v = cell.find('.//v', ns)
                        t = cell.get('t')
                        
                        if v is not None:
                            if t == 's':  # Строковое значение
                                idx = int(v.text)
                                if idx < len(strings):
                                    value = strings[idx]
                                else:
                                    value = f"[string {idx}]"
                            else:
                                value = v.text
                            
                            # Извлекаем букву колонки из ссылки (A, B, C...)
                            col_letter = ''.join(c for c in cell_ref if c.isalpha())
                            if col_letter:
                                cell_values[col_letter] = value
                    
                    # Выводим строку, если в ней есть значения
                    if cell_values:
                        values_str = " | ".join([f"{k}:{v[:30]}" for k, v in sorted(cell_values.items())[:5]])
                        print(f"Строка {row_num}: {values_str}")
                        
                        # Проверяем, является ли это строкой заголовков
                        values_list = list(cell_values.values())
                        if any('Количество' in str(v) or 'Выручка' in str(v) for v in values_list):
                            print(f"\n*** НАЙДЕНА СТРОКА ЗАГОЛОВКОВ: {row_num} ***")
                            print("Колонки:")
                            for col, val in sorted(cell_values.items()):
                                print(f"  {col}: {val}")
                            
                            # Читаем несколько строк данных после заголовков
                            print("\n=== ДАННЫЕ (5 строк после заголовков) ===")
                            data_count = 0
                            
                            for data_idx in range(row_idx + 1, min(row_idx + 30, len(rows))):
                                data_row = rows[data_idx]
                                data_cells = data_row.findall('.//c', ns)
                                
                                data_values = {}
                                for cell in data_cells:
                                    cell_ref = cell.get('r', '')
                                    v = cell.find('.//v', ns)
                                    t = cell.get('t')
                                    
                                    if v is not None:
                                        if t == 's':
                                            idx = int(v.text)
                                            if idx < len(strings):
                                                value = strings[idx]
                                        else:
                                            value = v.text
                                        
                                        col_letter = ''.join(c for c in cell_ref if c.isalpha())
                                        if col_letter:
                                            data_values[col_letter] = value
                                
                                # Выводим только строки с числовыми данными
                                if len(data_values) > 2 and any(v for k, v in data_values.items() if k != 'A'):
                                    data_count += 1
                                    print(f"\nДанные строка {data_count}:")
                                    # Сопоставляем с заголовками
                                    for col in sorted(set(list(cell_values.keys()) + list(data_values.keys()))):
                                        header = cell_values.get(col, '')
                                        value = data_values.get(col, '')
                                        if value:
                                            print(f"  {col} ({header[:30] if header else 'Нет заголовка'}): {value[:50]}")
                                    
                                    if data_count >= 5:
                                        break
                            
                            break
                
                print("\n=== ИТОГОВАЯ ИНФОРМАЦИЯ ===")
                print(f"Общее количество строк в файле: {len(rows)}")
                print(f"Количество текстовых значений: {len(strings)}")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    filename = "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    
    if os.path.exists(filename):
        find_headers_and_data(filename)
    else:
        print(f"Файл не найден: {filename}")