#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ структуры файла продаж филиала
"""

import sys
import os
import zipfile
import xml.etree.ElementTree as ET

def analyze_excel_detailed(filename):
    """Детальный анализ Excel файла"""
    print(f"=== ДЕТАЛЬНЫЙ АНАЛИЗ ФАЙЛА ПРОДАЖ ===")
    print(f"Файл: {filename}")
    print(f"Размер: {os.path.getsize(filename):,} байт\n")
    
    try:
        with zipfile.ZipFile(filename, 'r') as zip_file:
            # Пространство имен
            ns = {'': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            # 1. Читаем shared strings для получения текстовых значений
            strings = []
            if 'xl/sharedStrings.xml' in zip_file.namelist():
                strings_xml = zip_file.read('xl/sharedStrings.xml')
                strings_root = ET.fromstring(strings_xml)
                
                for si in strings_root.findall('.//si', ns):
                    t = si.find('.//t', ns)
                    if t is not None:
                        strings.append(t.text)
            
            print(f"Количество уникальных текстовых значений: {len(strings)}")
            
            # 2. Читаем данные листа
            worksheet_files = [f for f in zip_file.namelist() if 'worksheets/sheet' in f and f.endswith('.xml')]
            
            if worksheet_files:
                sheet_xml = zip_file.read(worksheet_files[0])
                root = ET.fromstring(sheet_xml)
                
                rows = root.findall('.//row', ns)
                print(f"Всего строк в файле: {len(rows)}")
                
                # Анализируем структуру данных
                print("\n=== СТРУКТУРА ДАННЫХ ===")
                
                # Читаем заголовки (строки 7-8 судя по данным)
                headers = []
                header_row = None
                
                # Ищем строку с заголовками
                for i, row in enumerate(rows[:20]):
                    cells = row.findall('.//c', ns)
                    row_values = []
                    
                    for cell in cells:
                        v = cell.find('.//v', ns)
                        t = cell.get('t')  # тип ячейки
                        
                        if v is not None:
                            if t == 's':  # строковое значение
                                idx = int(v.text)
                                if idx < len(strings):
                                    row_values.append(strings[idx])
                            else:
                                row_values.append(v.text)
                    
                    # Проверяем, является ли это строкой заголовков
                    if any('Номенклатура' in str(val) for val in row_values):
                        header_row = i
                        headers = row_values
                        break
                
                if headers:
                    print(f"\nЗаголовки найдены в строке {header_row + 1}:")
                    for j, header in enumerate(headers):
                        print(f"  Колонка {j+1}: {header}")
                
                # Читаем первые строки данных
                print("\n=== ПРИМЕРЫ ДАННЫХ (первые 10 записей после заголовков) ===")
                
                data_start = header_row + 1 if header_row else 9
                data_rows = []
                
                for i, row in enumerate(rows[data_start:data_start+15]):
                    cells = row.findall('.//c', ns)
                    row_data = []
                    
                    for cell in cells:
                        v = cell.find('.//v', ns)
                        t = cell.get('t')
                        
                        if v is not None:
                            if t == 's':  # строковое значение
                                idx = int(v.text)
                                if idx < len(strings):
                                    value = strings[idx]
                                else:
                                    value = f"[string {idx}]"
                            else:
                                value = v.text
                            row_data.append(value)
                        else:
                            row_data.append("")
                    
                    if any(row_data):  # Если строка не пустая
                        data_rows.append(row_data)
                        print(f"\nСтрока {data_start + i + 1}:")
                        for j, val in enumerate(row_data[:6]):  # Первые 6 колонок
                            if val:
                                print(f"  [{j+1}] {val}")
                
                # Анализ периода данных
                print("\n=== АНАЛИЗ ПЕРИОДА ДАННЫХ ===")
                
                # Ищем информацию о периоде в первых строках
                for i, row in enumerate(rows[:10]):
                    cells = row.findall('.//c', ns)
                    for cell in cells:
                        v = cell.find('.//v', ns)
                        t = cell.get('t')
                        
                        if v is not None and t == 's':
                            idx = int(v.text)
                            if idx < len(strings):
                                text = strings[idx]
                                if 'Период' in text or 'период' in text:
                                    print(f"Найдена информация о периоде: {text}")
                
                # Подсчет товаров
                print("\n=== СТАТИСТИКА ===")
                
                # Считаем непустые строки данных
                non_empty_data_rows = 0
                for row in rows[data_start:]:
                    cells = row.findall('.//c', ns)
                    if len(cells) > 0:
                        has_data = False
                        for cell in cells:
                            v = cell.find('.//v', ns)
                            if v is not None and v.text:
                                has_data = True
                                break
                        if has_data:
                            non_empty_data_rows += 1
                
                print(f"Количество строк с данными: {non_empty_data_rows}")
                
                # Выводим уникальные категории товаров
                print("\n=== КАТЕГОРИИ ТОВАРОВ (первые 20) ===")
                categories = set()
                
                for text in strings:
                    if text and not any(x in text for x in ['Период', 'Параметры', 'Валовая', 'Рентабельность', 'Количество', 'Выручка']):
                        # Исключаем служебные строки
                        if len(text) > 3 and not text.isdigit():
                            categories.add(text)
                
                for i, cat in enumerate(sorted(list(categories)[:20])):
                    print(f"{i+1}. {cat}")
                
    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    filename = "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    
    if os.path.exists(filename):
        analyze_excel_detailed(filename)
    else:
        print(f"Файл не найден: {filename}")