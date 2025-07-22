#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ структуры Excel файла для поиска подкатегорий
"""

import zipfile
import xml.etree.ElementTree as ET

def detailed_analysis(file_path):
    """Детальный анализ структуры файла"""
    print(f"ДЕТАЛЬНЫЙ АНАЛИЗ ФАЙЛА: {file_path}")
    print("=" * 100)
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Читаем shared strings
            shared_strings = {}
            with zip_file.open('xl/sharedStrings.xml') as ss_file:
                ss_content = ss_file.read().decode('utf-8')
                ss_root = ET.fromstring(ss_content)
                
                for i, si in enumerate(ss_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si')):
                    t_elem = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                    if t_elem is not None:
                        shared_strings[i] = t_elem.text
            
            # Читаем первый лист
            with zip_file.open('xl/worksheets/sheet1.xml') as sheet_file:
                sheet_content = sheet_file.read().decode('utf-8')
                sheet_root = ET.fromstring(sheet_content)
                
                rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                
                print("АНАЛИЗ СТРУКТУРЫ ДАННЫХ:")
                print("-" * 80)
                print("Заголовки в строке 1:")
                
                # Анализируем заголовки
                first_row = rows[0]
                header_cells = first_row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                headers = {}
                
                for cell in header_cells:
                    cell_ref = cell.get('r', '')
                    col_letter = ''.join([c for c in cell_ref if c.isalpha()])
                    cell_type = cell.get('t', '')
                    
                    v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    if v_elem is not None:
                        value = v_elem.text
                        if cell_type == 's' and value and value.isdigit():
                            string_idx = int(value)
                            if string_idx in shared_strings:
                                value = shared_strings[string_idx]
                        headers[col_letter] = value
                
                for col, header in sorted(headers.items()):
                    print(f"  Колонка {col}: {header}")
                
                print("\n" + "-" * 80)
                print("ПОИСК ПОДКАТЕГОРИЙ В КОЛОНКЕ B:")
                print("-" * 80)
                
                subcategories = []
                current_category = None
                
                for row_idx, row in enumerate(rows[1:], start=2):  # Пропускаем заголовок
                    row_num = row.get('r', str(row_idx))
                    cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                    
                    # Получаем значения колонок A, B, C
                    a_value = None
                    b_value = None
                    c_value = None
                    
                    for cell in cells:
                        cell_ref = cell.get('r', '')
                        col_letter = ''.join([c for c in cell_ref if c.isalpha()])
                        cell_type = cell.get('t', '')
                        
                        v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if v_elem is not None:
                            value = v_elem.text
                            if cell_type == 's' and value and value.isdigit():
                                string_idx = int(value)
                                if string_idx in shared_strings:
                                    value = shared_strings[string_idx]
                            
                            if col_letter == 'A':
                                a_value = value
                            elif col_letter == 'B':
                                b_value = value
                            elif col_letter == 'C':
                                c_value = value
                    
                    # Определяем тип строки
                    if a_value and not b_value and not c_value:
                        current_category = a_value
                        print(f"Строка {row_num:4s}: КАТЕГОРИЯ = '{a_value}'")
                    elif a_value and b_value and not c_value:
                        subcategories.append({
                            'row': row_num,
                            'category': a_value,
                            'subcategory': b_value
                        })
                        print(f"Строка {row_num:4s}: ПОДКАТЕГОРИЯ = '{b_value}' (категория: '{a_value}')")
                    elif a_value and c_value:
                        print(f"Строка {row_num:4s}: ТОВАР = '{c_value[:30]}...' (категория: '{a_value}', подкатегория: '{b_value or "Не указана"}')")
                    
                    # Показываем только первые 100 строк для анализа
                    if row_idx > 100:
                        break
                
                print("\n" + "=" * 100)
                print("РЕЗЮМЕ НАЙДЕННЫХ ПОДКАТЕГОРИЙ:")
                print("-" * 80)
                
                categories_dict = {}
                for sub in subcategories:
                    cat = sub['category']
                    subcat = sub['subcategory']
                    if cat not in categories_dict:
                        categories_dict[cat] = []
                    if subcat not in categories_dict[cat]:
                        categories_dict[cat].append(subcat)
                
                for category, subs in categories_dict.items():
                    print(f"\nКатегория: {category}")
                    for sub in subs:
                        print(f"  → {sub}")
                
                print("\n" + "=" * 100)
                print("ЛОГИКА ОПРЕДЕЛЕНИЯ ПОДКАТЕГОРИИ:")
                print("-" * 80)
                print("1. Строка является ПОДКАТЕГОРИЕЙ если:")
                print("   - В колонке A есть значение (категория)")
                print("   - В колонке B есть значение (подкатегория)")
                print("   - В колонке C НЕТ значения (пустая)")
                print("")
                print("2. Строка является ТОВАРОМ если:")
                print("   - В колонке A есть значение (категория)")
                print("   - В колонке B может быть пустой")
                print("   - В колонке C есть значение (номенклатура товара)")
                print("")
                print("3. Подкатегория действует для всех следующих товаров до:")
                print("   - Появления новой подкатегории в той же категории")
                print("   - Появления новой категории")
                
                # Найдем несколько примеров товаров с подкатегориями
                print("\n" + "-" * 80)
                print("ПРИМЕРЫ ТОВАРОВ С ПОДКАТЕГОРИЯМИ:")
                print("-" * 80)
                
                current_category = None
                current_subcategory = None
                examples_found = 0
                
                for row_idx, row in enumerate(rows[1:], start=2):
                    if examples_found >= 10:
                        break
                        
                    row_num = row.get('r', str(row_idx))
                    cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                    
                    a_value = None
                    b_value = None
                    c_value = None
                    
                    for cell in cells:
                        cell_ref = cell.get('r', '')
                        col_letter = ''.join([c for c in cell_ref if c.isalpha()])
                        cell_type = cell.get('t', '')
                        
                        v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if v_elem is not None:
                            value = v_elem.text
                            if cell_type == 's' and value and value.isdigit():
                                string_idx = int(value)
                                if string_idx in shared_strings:
                                    value = shared_strings[string_idx]
                            
                            if col_letter == 'A':
                                a_value = value
                            elif col_letter == 'B':
                                b_value = value
                            elif col_letter == 'C':
                                c_value = value
                    
                    # Обновляем текущую категорию и подкатегорию
                    if a_value and b_value and not c_value:
                        current_category = a_value
                        current_subcategory = b_value
                    elif a_value and c_value:
                        if current_subcategory:
                            print(f"Товар: '{c_value[:40]}...'")
                            print(f"  → Категория: {current_category}")
                            print(f"  → Подкатегория: {current_subcategory}")
                            print()
                            examples_found += 1
                        current_category = a_value
                
    except Exception as e:
        print(f"Ошибка при анализе: {e}")

if __name__ == "__main__":
    file_path = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    detailed_analysis(file_path)