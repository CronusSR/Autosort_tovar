#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение правильной структуры колонок из файла продаж
"""

import os
import zipfile
import xml.etree.ElementTree as ET

def extract_columns_and_data(filename):
    """Извлечение структуры колонок и примеров данных"""
    print(f"=== АНАЛИЗ СТРУКТУРЫ ФАЙЛА ПРОДАЖ ФИЛИАЛА ===")
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
            
            # 2. Читаем лист с данными
            worksheet_files = [f for f in zip_file.namelist() if 'worksheets/sheet' in f and f.endswith('.xml')]
            
            if worksheet_files:
                sheet_xml = zip_file.read(worksheet_files[0])
                root = ET.fromstring(sheet_xml)
                
                rows = root.findall('.//row', ns)
                
                # Ищем строку с заголовками колонок
                # Основываясь на предыдущем анализе, заголовки должны быть около строки 8-9
                print("=== ПОИСК ЗАГОЛОВКОВ КОЛОНОК ===")
                
                for row_idx in range(5, min(15, len(rows))):
                    row = rows[row_idx]
                    cells = row.findall('.//c', ns)
                    row_values = []
                    
                    for cell in cells:
                        v = cell.find('.//v', ns)
                        t = cell.get('t')
                        
                        if v is not None:
                            if t == 's':
                                idx = int(v.text)
                                if idx < len(strings):
                                    row_values.append(strings[idx])
                            else:
                                row_values.append(v.text)
                        else:
                            row_values.append("")
                    
                    # Проверяем, содержит ли строка заголовки
                    if len(row_values) > 3 and any('Количество' in str(val) or 'Выручка' in str(val) or 'Номенклатура' in str(val) for val in row_values):
                        print(f"\nНайдены заголовки в строке {row_idx + 1}:")
                        for i, val in enumerate(row_values):
                            if val:
                                print(f"  Колонка {i+1}: {val}")
                        
                        # Теперь читаем несколько строк данных после заголовков
                        print("\n=== ПРИМЕРЫ ДАННЫХ (5 строк после заголовков) ===")
                        
                        data_rows_count = 0
                        for data_row_idx in range(row_idx + 1, min(row_idx + 50, len(rows))):
                            data_row = rows[data_row_idx]
                            data_cells = data_row.findall('.//c', ns)
                            data_values = []
                            
                            for cell in data_cells:
                                v = cell.find('.//v', ns)
                                t = cell.get('t')
                                
                                if v is not None:
                                    if t == 's':
                                        idx = int(v.text)
                                        if idx < len(strings):
                                            data_values.append(strings[idx])
                                    else:
                                        data_values.append(v.text)
                                else:
                                    data_values.append("")
                            
                            # Пропускаем пустые строки и строки с категориями
                            if len(data_values) > 3 and any(data_values[1:]):  # Если есть данные кроме первой колонки
                                data_rows_count += 1
                                print(f"\nСтрока данных {data_rows_count}:")
                                for i, (header, value) in enumerate(zip(row_values[:7], data_values[:7])):
                                    if value:
                                        print(f"  {header if header else f'Колонка {i+1}'}: {value}")
                                
                                if data_rows_count >= 5:
                                    break
                        
                        break
                
                # Дополнительный анализ
                print("\n=== ИТОГОВАЯ СТРУКТУРА ФАЙЛА ===")
                print(f"1. Файл: {filename}")
                print(f"2. Период данных: 01.07.2024 - 01.07.2025")
                print(f"3. Филиал: 6 Склад фурнитуры 'Овощная база' Магазин")
                print(f"4. Категория товаров: Мебельная фурнитура")
                print(f"5. Общее количество строк: {len(rows)}")
                print(f"6. Количество уникальных наименований: ~{len(strings)}")
                
                print("\n=== ОБНАРУЖЕННЫЕ КОЛОНКИ ===")
                print("На основе анализа, файл содержит следующие данные:")
                print("- Номенклатура (наименование товара)")
                print("- Количество (проданное количество)")
                print("- Выручка (сумма продаж)")
                print("- Себестоимость товаров")
                print("- Валовая прибыль")
                print("- Рентабельность, %")
                print("- Стоимость закупки")
                print("- Доп. расходы")
                print("- Трудозатраты")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    filename = "6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"
    
    if os.path.exists(filename):
        extract_columns_and_data(filename)
    else:
        print(f"Файл не найден: {filename}")