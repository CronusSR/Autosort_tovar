#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры файла продаж конкретного филиала
"""

import sys
import os

def analyze_excel_without_pandas(filename):
    """Анализ Excel файла без использования pandas"""
    print(f"=== Анализ файла: {filename} ===\n")
    
    # Проверяем существование файла
    if not os.path.exists(filename):
        print(f"Файл не найден: {filename}")
        return
    
    # Информация о файле
    file_size = os.path.getsize(filename)
    print(f"Размер файла: {file_size:,} байт ({file_size/1024/1024:.2f} МБ)")
    
    # Попытка прочитать как ZIP (Excel файлы - это ZIP архивы)
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        with zipfile.ZipFile(filename, 'r') as zip_file:
            # Список файлов в архиве
            file_list = zip_file.namelist()
            print(f"\nСтруктура Excel файла (ZIP):")
            
            # Ищем файлы с данными
            worksheet_files = [f for f in file_list if 'worksheets/sheet' in f and f.endswith('.xml')]
            print(f"Найдено листов: {len(worksheet_files)}")
            
            # Читаем первый лист
            if worksheet_files:
                sheet_xml = zip_file.read(worksheet_files[0])
                root = ET.fromstring(sheet_xml)
                
                # Пространство имен для Excel
                ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                
                # Считаем количество строк
                rows = root.findall('.//row', ns)
                print(f"\nКоличество строк на первом листе: {len(rows)}")
                
                # Читаем первые несколько строк
                print("\nПервые строки данных:")
                for i, row in enumerate(rows[:10]):
                    cells = row.findall('.//c', ns)
                    row_data = []
                    for cell in cells:
                        v = cell.find('.//v', ns)
                        if v is not None:
                            row_data.append(v.text)
                    if row_data:
                        print(f"Строка {i+1}: {' | '.join(row_data[:5])}...")
            
            # Читаем shared strings (текстовые значения)
            if 'xl/sharedStrings.xml' in file_list:
                strings_xml = zip_file.read('xl/sharedStrings.xml')
                strings_root = ET.fromstring(strings_xml)
                
                # Получаем первые текстовые значения
                strings = []
                for si in strings_root.findall('.//si', ns)[:50]:
                    t = si.find('.//t', ns)
                    if t is not None:
                        strings.append(t.text)
                
                print("\nПримеры текстовых значений (возможные заголовки):")
                for i, s in enumerate(strings[:20]):
                    print(f"{i}: {s}")
    
    except Exception as e:
        print(f"\nОшибка при чтении структуры Excel: {e}")
    
    # Альтернативный метод - попытка прочитать через систему
    print("\n=== Попытка конвертации ===")
    print("Для полного анализа необходимо установить pandas:")
    print("1. sudo apt-get update")
    print("2. sudo apt-get install python3-pip python3-pandas python3-openpyxl")
    print("или")
    print("3. python3 -m venv venv")
    print("4. source venv/bin/activate")
    print("5. pip install pandas openpyxl")

if __name__ == "__main__":
    filename = "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    
    # Проверяем наличие файла
    if os.path.exists(filename):
        analyze_excel_without_pandas(filename)
    else:
        print(f"Файл не найден: {filename}")
        print(f"Текущая директория: {os.getcwd()}")
        print("\nДоступные Excel файлы:")
        for f in os.listdir('.'):
            if f.endswith(('.xlsx', '.xls')):
                print(f"- {f}")