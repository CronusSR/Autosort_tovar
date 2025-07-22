#!/usr/bin/env python3
"""Базовый анализ файла остатков без внешних библиотек"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path

def analyze_xlsx_structure(file_path):
    """Анализ структуры XLSX файла через базовые библиотеки"""
    
    print(f"Анализ файла: {file_path}")
    print("=" * 80)
    
    try:
        # XLSX это ZIP архив
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Получаем список файлов в архиве
            file_list = zip_file.namelist()
            
            print("\n1. СТРУКТУРА XLSX АРХИВА:")
            print(f"   Количество файлов: {len(file_list)}")
            
            # Ищем файлы с данными листов
            worksheet_files = [f for f in file_list if f.startswith('xl/worksheets/') and f.endswith('.xml')]
            print(f"   Количество листов: {len(worksheet_files)}")
            
            # Читаем shared strings (общие строки)
            shared_strings = []
            if 'xl/sharedStrings.xml' in file_list:
                with zip_file.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    # Namespace для Excel
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in root.findall('.//ns:si', ns):
                        t = si.find('.//ns:t', ns)
                        if t is not None and t.text:
                            shared_strings.append(t.text)
                            
            print(f"   Количество общих строк: {len(shared_strings)}")
            
            # Анализируем первый лист
            if worksheet_files:
                print("\n2. АНАЛИЗ ПЕРВОГО ЛИСТА:")
                
                with zip_file.open(worksheet_files[0]) as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    # Получаем все строки
                    rows = root.findall('.//ns:row', ns)
                    print(f"   Количество строк: {len(rows)}")
                    
                    # Анализируем первую строку (заголовки)
                    if rows:
                        first_row = rows[0]
                        cells = first_row.findall('.//ns:c', ns)
                        print(f"   Количество колонок в первой строке: {len(cells)}")
                        
                        print("\n3. ЗАГОЛОВКИ (первая строка):")
                        headers = []
                        for i, cell in enumerate(cells):
                            cell_type = cell.get('t', '')
                            value_elem = cell.find('.//ns:v', ns)
                            
                            if value_elem is not None and value_elem.text:
                                if cell_type == 's':  # shared string
                                    idx = int(value_elem.text)
                                    if idx < len(shared_strings):
                                        value = shared_strings[idx]
                                    else:
                                        value = f"String index {idx}"
                                else:
                                    value = value_elem.text
                            else:
                                value = ''
                                
                            headers.append(value)
                            print(f"   [{i}] {value}")
                            
                        # Анализируем несколько строк данных
                        print("\n4. ПРИМЕРЫ ДАННЫХ (строки 2-5):")
                        for row_idx in range(1, min(5, len(rows))):
                            row = rows[row_idx]
                            cells = row.findall('.//ns:c', ns)
                            
                            print(f"\n   Строка {row_idx + 1}:")
                            for i, cell in enumerate(cells[:6]):  # Первые 6 колонок
                                cell_type = cell.get('t', '')
                                value_elem = cell.find('.//ns:v', ns)
                                
                                if value_elem is not None and value_elem.text:
                                    if cell_type == 's':  # shared string
                                        idx = int(value_elem.text)
                                        if idx < len(shared_strings):
                                            value = shared_strings[idx]
                                        else:
                                            value = f"String index {idx}"
                                    else:
                                        value = value_elem.text
                                else:
                                    value = ''
                                    
                                if i < len(headers):
                                    header = headers[i]
                                else:
                                    header = f"Column {i}"
                                    
                                print(f"      {header}: {value}")
                                
                        # Анализ складов и филиалов
                        print("\n5. ПОИСК СКЛАДОВ/ФИЛИАЛОВ В ЗАГОЛОВКАХ:")
                        warehouse_keywords = ['склад', 'филиал', 'магазин', 'барыс', 'абая', 
                                            'айнабулак', 'казыбаева', 'астана', 'шымкент']
                        
                        found_warehouses = []
                        for i, header in enumerate(headers):
                            header_lower = str(header).lower()
                            for keyword in warehouse_keywords:
                                if keyword in header_lower:
                                    found_warehouses.append((i, header))
                                    break
                                    
                        if found_warehouses:
                            print("   Найдены колонки складов:")
                            for idx, name in found_warehouses:
                                print(f"     [{idx}] {name}")
                                
                        # Поиск категорий
                        print("\n6. ПОИСК КАТЕГОРИЙ В ЗАГОЛОВКАХ:")
                        category_keywords = ['категория', 'группа', 'раздел', 'тип', 'класс']
                        
                        found_categories = []
                        for i, header in enumerate(headers):
                            header_lower = str(header).lower()
                            for keyword in category_keywords:
                                if keyword in header_lower:
                                    found_categories.append((i, header))
                                    break
                                    
                        if found_categories:
                            print("   Найдены колонки категорий:")
                            for idx, name in found_categories:
                                print(f"     [{idx}] {name}")
                                
                        # Сохраняем результаты
                        structure = {
                            "file_name": str(file_path),
                            "total_rows": len(rows),
                            "total_columns": len(headers),
                            "headers": headers,
                            "warehouse_columns": [{"index": idx, "name": name} for idx, name in found_warehouses],
                            "category_columns": [{"index": idx, "name": name} for idx, name in found_categories],
                            "shared_strings_count": len(shared_strings)
                        }
                        
                        with open('inventory_basic_structure.json', 'w', encoding='utf-8') as f:
                            json.dump(structure, f, ensure_ascii=False, indent=2)
                            
                        print("\n✅ Структура сохранена в файл 'inventory_basic_structure.json'")
                            
    except Exception as e:
        print(f"\n❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = Path("остатки на 08.07.2025.xlsx")
    if file_path.exists():
        analyze_xlsx_structure(file_path)
    else:
        print(f"❌ Файл не найден: {file_path}")