#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import xml.etree.ElementTree as ET
import os

def analyze_xlsx_basic():
    """Базовый анализ XLSX файла через ZIP архив"""
    
    file_path = "/mnt/f/Работа-Никита/Autosort_tovar/остатки на 08.07.2025.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return
    
    print(f"📁 Анализ файла: остатки на 08.07.2025.xlsx")
    print("=" * 80)
    
    try:
        # XLSX файл - это ZIP архив
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            print("📦 Содержимое ZIP архива (XLSX):")
            for filename in zip_file.namelist():
                print(f"  - {filename}")
            
            # Читаем основной лист (обычно sheet1.xml)
            sheet_files = [f for f in zip_file.namelist() if f.startswith('xl/worksheets/')]
            if not sheet_files:
                print("❌ Не найдены листы Excel")
                return
            
            print(f"\n📋 Найдены листы: {sheet_files}")
            
            # Анализируем первый лист
            first_sheet = sheet_files[0]
            print(f"\n🔍 Анализ листа: {first_sheet}")
            
            # Читаем shared strings (общие строки)
            shared_strings = []
            try:
                with zip_file.open('xl/sharedStrings.xml') as ss_file:
                    ss_content = ss_file.read().decode('utf-8')
                    # Простой парсинг shared strings
                    root = ET.fromstring(ss_content)
                    
                    # Ищем все текстовые элементы
                    for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                        text_elem = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                        if text_elem is not None and text_elem.text:
                            shared_strings.append(text_elem.text)
                    
                    print(f"📝 Найдено общих строк: {len(shared_strings)}")
                    print("📝 Первые 20 строк:")
                    for i, text in enumerate(shared_strings[:20]):
                        print(f"  {i}: '{text}'")
                    
            except Exception as e:
                print(f"❌ Ошибка чтения shared strings: {e}")
            
            # Читаем основной лист
            try:
                with zip_file.open(first_sheet) as sheet_file:
                    sheet_content = sheet_file.read().decode('utf-8')
                    
                    # Парсим XML листа
                    root = ET.fromstring(sheet_content)
                    
                    # Ищем все ячейки
                    cells = []
                    for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                        row_num = row.get('r')
                        row_cells = []
                        
                        for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            cell_ref = cell.get('r')  # A1, B1, etc.
                            cell_type = cell.get('t')  # s = shared string, n = number, etc.
                            
                            value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if value_elem is not None and value_elem.text:
                                value = value_elem.text
                                
                                # Если это shared string, получаем текст
                                if cell_type == 's' and value.isdigit():
                                    idx = int(value)
                                    if idx < len(shared_strings):
                                        value = shared_strings[idx]
                                
                                row_cells.append((cell_ref, value))
                        
                        if row_cells and int(row_num) <= 25:  # Первые 25 строк
                            cells.append((row_num, row_cells))
                    
                    print(f"\n📊 Данные первых строк:")
                    for row_num, row_cells in cells:
                        print(f"\nСтрока {row_num}:")
                        for cell_ref, value in row_cells:
                            print(f"  {cell_ref}: '{value}'")
                    
                    # Анализ заголовков
                    print(f"\n🔍 ПОИСК ЗАГОЛОВКОВ:")
                    keywords = ["номенклатура", "наименование", "склад", "остаток", "количество"]
                    
                    for row_num, row_cells in cells:
                        row_text = " ".join([value for _, value in row_cells]).lower()
                        if any(keyword in row_text for keyword in keywords):
                            print(f"⭐ Потенциальные заголовки в строке {row_num}:")
                            for cell_ref, value in row_cells:
                                print(f"  {cell_ref}: '{value}'")
                    
            except Exception as e:
                print(f"❌ Ошибка чтения листа: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_xlsx_basic()