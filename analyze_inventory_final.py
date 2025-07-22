#!/usr/bin/env python3
"""Финальный анализ файла остатков с правильной структурой"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path

def analyze_xlsx_final(file_path):
    """Финальный анализ XLSX файла с полным пониманием структуры"""
    
    print(f"ДЕТАЛЬНЫЙ АНАЛИЗ ФАЙЛА ОСТАТКОВ")
    print("=" * 80)
    print(f"Файл: {file_path}")
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Читаем shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in zip_file.namelist():
                with zip_file.open('xl/sharedStrings.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in root.findall('.//ns:si', ns):
                        t = si.find('.//ns:t', ns)
                        if t is not None and t.text:
                            shared_strings.append(t.text)
            
            # Анализируем первый лист
            worksheet_files = [f for f in zip_file.namelist() if f.startswith('xl/worksheets/') and f.endswith('.xml')]
            
            if worksheet_files:
                with zip_file.open(worksheet_files[0]) as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    rows = root.findall('.//ns:row', ns)
                    
                    def get_cell_value(cell):
                        """Получение значения ячейки"""
                        cell_type = cell.get('t', '')
                        value_elem = cell.find('.//ns:v', ns)
                        
                        if value_elem is not None and value_elem.text:
                            if cell_type == 's':
                                idx = int(value_elem.text)
                                if idx < len(shared_strings):
                                    return shared_strings[idx]
                                else:
                                    return f"String index {idx}"
                            else:
                                return value_elem.text
                        return ''
                    
                    # Анализируем строки 5-8 для понимания структуры заголовков
                    print("\n1. СТРУКТУРА ЗАГОЛОВКОВ:")
                    print("-" * 50)
                    
                    # Строка 6 - названия складов
                    warehouse_row = rows[5]  # строка 6
                    warehouse_cells = warehouse_row.findall('.//ns:c', ns)
                    warehouses = []
                    for cell in warehouse_cells:
                        value = get_cell_value(cell)
                        warehouses.append(value)
                    
                    print("СКЛАДЫ/ФИЛИАЛЫ (строка 6):")
                    for i, warehouse in enumerate(warehouses):
                        if warehouse.strip():
                            print(f"   [{i}] {warehouse}")
                    
                    # Строка 7 - заголовки колонок
                    header_row = rows[6]  # строка 7
                    header_cells = header_row.findall('.//ns:c', ns)
                    headers = []
                    for cell in header_cells:
                        value = get_cell_value(cell)
                        headers.append(value)
                    
                    print("\nЗАГОЛОВКИ КОЛОНОК (строка 7):")
                    for i, header in enumerate(headers):
                        if header.strip():
                            print(f"   [{i}] {header}")
                    
                    # Строка 8 - единицы измерения (если есть)
                    units_row = rows[7]  # строка 8
                    units_cells = units_row.findall('.//ns:c', ns)
                    units = []
                    for cell in units_cells:
                        value = get_cell_value(cell)
                        units.append(value)
                    
                    print("\nЕДИНИЦЫ ИЗМЕРЕНИЯ (строка 8):")
                    for i, unit in enumerate(units):
                        if unit.strip():
                            print(f"   [{i}] {unit}")
                    
                    # Определяем структуру данных
                    print("\n2. СТРУКТУРА ДАННЫХ:")
                    print("-" * 50)
                    
                    # Номенклатура обычно в первой колонке
                    nomenclature_col = 0
                    print(f"Колонка номенклатуры: [{nomenclature_col}]")
                    
                    # Склады с остатками - остальные колонки
                    stock_cols = []
                    for i in range(1, len(warehouses)):
                        if warehouses[i].strip():
                            stock_cols.append((i, warehouses[i]))
                    
                    print(f"Колонки с остатками: {len(stock_cols)} шт.")
                    for idx, name in stock_cols:
                        print(f"   [{idx}] {name}")
                    
                    # Анализируем данные (начиная с строки 9)
                    print("\n3. АНАЛИЗ ДАННЫХ:")
                    print("-" * 50)
                    
                    data_start_row = 8  # строка 9
                    total_items = 0
                    items_with_stock = 0
                    sample_items = []
                    
                    for row_idx in range(data_start_row, min(data_start_row + 100, len(rows))):
                        if row_idx < len(rows):
                            row = rows[row_idx]
                            cells = row.findall('.//ns:c', ns)
                            
                            if len(cells) > 0:
                                # Получаем номенклатуру
                                nomenclature = get_cell_value(cells[0]) if len(cells) > 0 else ''
                                
                                if nomenclature.strip():
                                    total_items += 1
                                    
                                    # Проверяем остатки
                                    has_stock = False
                                    stock_values = {}
                                    
                                    for col_idx, warehouse_name in stock_cols:
                                        if col_idx < len(cells):
                                            stock_value = get_cell_value(cells[col_idx])
                                            try:
                                                stock_num = float(stock_value) if stock_value else 0
                                                stock_values[warehouse_name] = stock_num
                                                if stock_num > 0:
                                                    has_stock = True
                                            except:
                                                stock_values[warehouse_name] = stock_value
                                    
                                    if has_stock:
                                        items_with_stock += 1
                                    
                                    # Сохраняем примеры
                                    if len(sample_items) < 15:
                                        sample_items.append({
                                            'nomenclature': nomenclature,
                                            'stock': stock_values,
                                            'has_stock': has_stock
                                        })
                    
                    print(f"Проанализировано строк: {min(100, len(rows) - data_start_row)}")
                    print(f"Найдено товаров: {total_items}")
                    print(f"Товаров с остатками: {items_with_stock}")
                    
                    # Показываем примеры
                    print("\n4. ПРИМЕРЫ ТОВАРОВ:")
                    print("-" * 50)
                    
                    for i, item in enumerate(sample_items):
                        print(f"\n{i+1}. {item['nomenclature']}")
                        print(f"   Есть остатки: {'Да' if item['has_stock'] else 'Нет'}")
                        
                        # Показываем остатки по складам
                        for warehouse, stock in item['stock'].items():
                            if stock and str(stock) != '0':
                                print(f"   {warehouse}: {stock}")
                    
                    # Анализ складов
                    print("\n5. АНАЛИЗ СКЛАДОВ:")
                    print("-" * 50)
                    
                    warehouse_types = {
                        'Основные склады': [],
                        'Магазины': [],
                        'Региональные': []
                    }
                    
                    for idx, name in stock_cols:
                        name_lower = name.lower()
                        if 'магазин' in name_lower:
                            warehouse_types['Магазины'].append((idx, name))
                        elif any(region in name_lower for region in ['шымкент', 'астана', 'алматы']):
                            warehouse_types['Региональные'].append((idx, name))
                        else:
                            warehouse_types['Основные склады'].append((idx, name))
                    
                    for category, warehouses in warehouse_types.items():
                        if warehouses:
                            print(f"\n{category}: {len(warehouses)} шт.")
                            for idx, name in warehouses:
                                print(f"   [{idx}] {name}")
                    
                    # Определяем категории товаров
                    print("\n6. АНАЛИЗ КАТЕГОРИЙ ТОВАРОВ:")
                    print("-" * 50)
                    
                    categories = set()
                    for item in sample_items:
                        name = item['nomenclature']
                        # Простой анализ по ключевым словам
                        if any(word in name.lower() for word in ['мм', 'см']):
                            categories.add('Фурнитура с размерами')
                        elif 'дуб' in name.lower():
                            categories.add('Дубовые изделия')
                        elif 'венге' in name.lower():
                            categories.add('Венге')
                        elif any(wood in name.lower() for wood in ['ясень', 'сонома']):
                            categories.add('Другие породы дерева')
                        else:
                            categories.add('Прочие')
                    
                    print(f"Найдено категорий: {len(categories)}")
                    for category in sorted(categories):
                        print(f"   • {category}")
                    
                    # Финальная структура
                    structure = {
                        "file_info": {
                            "file_name": str(file_path),
                            "total_rows": len(rows),
                            "data_start_row": data_start_row + 1,
                            "header_rows": {
                                "warehouses": 6,
                                "column_headers": 7,
                                "units": 8
                            }
                        },
                        "data_structure": {
                            "nomenclature_column": 0,
                            "stock_columns": len(stock_cols),
                            "total_items_analyzed": total_items,
                            "items_with_stock": items_with_stock
                        },
                        "warehouses": [{"index": idx, "name": name} for idx, name in stock_cols],
                        "warehouse_categories": {
                            "main_warehouses": [{"index": idx, "name": name} for idx, name in warehouse_types['Основные склады']],
                            "stores": [{"index": idx, "name": name} for idx, name in warehouse_types['Магазины']],
                            "regional": [{"index": idx, "name": name} for idx, name in warehouse_types['Региональные']]
                        },
                        "sample_items": sample_items[:5],
                        "categories_found": list(categories)
                    }
                    
                    with open('inventory_final_structure.json', 'w', encoding='utf-8') as f:
                        json.dump(structure, f, ensure_ascii=False, indent=2)
                    
                    print(f"\n✅ ИТОГОВАЯ СТРУКТУРА:")
                    print(f"   📁 Файл: остатки на 08.07.2025.xlsx")
                    print(f"   📊 Всего строк: {len(rows)}")
                    print(f"   📦 Товаров (в выборке): {total_items}")
                    print(f"   📈 С остатками: {items_with_stock}")
                    print(f"   🏭 Складов/филиалов: {len(stock_cols)}")
                    print(f"   📂 Категорий найдено: {len(categories)}")
                    print(f"   🎯 Начало данных: строка {data_start_row + 1}")
                    
                    print(f"\n💾 Структура сохранена в: inventory_final_structure.json")
                            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = Path("остатки на 08.07.2025.xlsx")
    if file_path.exists():
        analyze_xlsx_final(file_path)
    else:
        print(f"❌ Файл не найден: {file_path}")