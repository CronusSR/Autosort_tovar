#!/usr/bin/env python3
"""Детальный анализ файла остатков с поиском заголовков"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path

def analyze_xlsx_detailed(file_path):
    """Детальный анализ XLSX файла с поиском заголовков"""
    
    print(f"Анализ файла: {file_path}")
    print("=" * 80)
    
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
                            
            print(f"Загружено {len(shared_strings)} общих строк")
            
            # Анализируем первый лист
            worksheet_files = [f for f in zip_file.namelist() if f.startswith('xl/worksheets/') and f.endswith('.xml')]
            
            if worksheet_files:
                with zip_file.open(worksheet_files[0]) as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    rows = root.findall('.//ns:row', ns)
                    print(f"\nВсего строк в файле: {len(rows)}")
                    
                    # Ищем строку с заголовками
                    print("\n🔍 ПОИСК ЗАГОЛОВКОВ...")
                    
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
                    
                    # Анализируем первые 20 строк для поиска заголовков
                    header_row_idx = None
                    header_keywords = ['номенклатура', 'наименование', 'товар', 'артикул', 'склад', 'остаток']
                    
                    for row_idx in range(min(20, len(rows))):
                        row = rows[row_idx]
                        cells = row.findall('.//ns:c', ns)
                        
                        if len(cells) > 5:  # Строка с заголовками должна иметь много колонок
                            row_values = []
                            for cell in cells[:10]:  # Проверяем первые 10 ячеек
                                value = get_cell_value(cell)
                                row_values.append(value)
                            
                            # Проверяем, есть ли ключевые слова заголовков
                            keyword_count = 0
                            for value in row_values:
                                value_lower = str(value).lower()
                                for keyword in header_keywords:
                                    if keyword in value_lower:
                                        keyword_count += 1
                                        break
                            
                            print(f"Строка {row_idx + 1}: {len(cells)} колонок, {keyword_count} ключевых слов")
                            print(f"  Первые значения: {row_values[:5]}")
                            
                            if keyword_count >= 2:  # Если нашли минимум 2 ключевых слова
                                header_row_idx = row_idx
                                print(f"  ✅ Возможная строка заголовков!")
                                break
                    
                    if header_row_idx is None:
                        print("⚠️ Заголовки не найдены автоматически. Пробуем другой метод...")
                        
                        # Ищем строку с максимальным количеством непустых ячеек
                        max_cells = 0
                        for row_idx in range(min(20, len(rows))):
                            row = rows[row_idx]
                            cells = row.findall('.//ns:c', ns)
                            non_empty = sum(1 for cell in cells if get_cell_value(cell).strip())
                            
                            if non_empty > max_cells:
                                max_cells = non_empty
                                header_row_idx = row_idx
                                
                        print(f"Выбрана строка {header_row_idx + 1} с {max_cells} непустыми ячейками")
                    
                    # Извлекаем заголовки
                    if header_row_idx is not None:
                        header_row = rows[header_row_idx]
                        header_cells = header_row.findall('.//ns:c', ns)
                        
                        headers = []
                        for cell in header_cells:
                            value = get_cell_value(cell)
                            headers.append(value)
                            
                        print(f"\n📋 ЗАГОЛОВКИ (строка {header_row_idx + 1}):")
                        for i, header in enumerate(headers):
                            if header.strip():
                                print(f"   [{i}] {header}")
                                
                        # Анализ складов
                        print("\n🏭 АНАЛИЗ СКЛАДОВ:")
                        warehouse_keywords = ['склад', 'филиал', 'магазин', 'барыс', 'абая', 
                                            'айнабулак', 'казыбаева', 'астана', 'шымкент']
                        
                        warehouse_cols = []
                        for i, header in enumerate(headers):
                            header_lower = str(header).lower()
                            for keyword in warehouse_keywords:
                                if keyword in header_lower and header.strip():
                                    warehouse_cols.append((i, header))
                                    break
                                    
                        if warehouse_cols:
                            print(f"   Найдено {len(warehouse_cols)} колонок складов:")
                            for idx, name in warehouse_cols:
                                print(f"     [{idx}] {name}")
                        else:
                            print("   ⚠️ Колонки складов не найдены в заголовках")
                            
                        # Анализ товаров
                        print("\n📦 АНАЛИЗ НОМЕНКЛАТУРЫ:")
                        product_keywords = ['номенклатура', 'наименование', 'товар', 'артикул', 'продукт']
                        
                        product_cols = []
                        for i, header in enumerate(headers):
                            header_lower = str(header).lower()
                            for keyword in product_keywords:
                                if keyword in header_lower and header.strip():
                                    product_cols.append((i, header))
                                    break
                                    
                        if product_cols:
                            print(f"   Найдено {len(product_cols)} колонок товаров:")
                            for idx, name in product_cols:
                                print(f"     [{idx}] {name}")
                                
                        # Показываем примеры данных
                        print("\n📊 ПРИМЕРЫ ДАННЫХ:")
                        
                        data_start_row = header_row_idx + 1
                        for row_idx in range(data_start_row, min(data_start_row + 10, len(rows))):
                            if row_idx < len(rows):
                                row = rows[row_idx]
                                cells = row.findall('.//ns:c', ns)
                                
                                print(f"\n   Строка {row_idx + 1}:")
                                
                                # Показываем только важные колонки
                                important_indices = []
                                if product_cols:
                                    important_indices.extend([idx for idx, _ in product_cols[:2]])
                                if warehouse_cols:
                                    important_indices.extend([idx for idx, _ in warehouse_cols[:3]])
                                    
                                if not important_indices:
                                    important_indices = list(range(min(6, len(headers))))
                                
                                for i in important_indices:
                                    if i < len(cells):
                                        value = get_cell_value(cells[i])
                                        header_name = headers[i] if i < len(headers) else f"Column {i}"
                                        print(f"      {header_name}: {value}")
                                        
                        # Сохраняем результаты
                        structure = {
                            "file_name": str(file_path),
                            "header_row": header_row_idx + 1,
                            "total_rows": len(rows),
                            "data_rows": len(rows) - header_row_idx - 1,
                            "total_columns": len(headers),
                            "headers": headers,
                            "warehouse_columns": [{"index": idx, "name": name} for idx, name in warehouse_cols],
                            "product_columns": [{"index": idx, "name": name} for idx, name in product_cols],
                            "shared_strings_count": len(shared_strings)
                        }
                        
                        with open('inventory_detailed_structure.json', 'w', encoding='utf-8') as f:
                            json.dump(structure, f, ensure_ascii=False, indent=2)
                            
                        print(f"\n✅ Детальная структура сохранена в файл 'inventory_detailed_structure.json'")
                        print(f"\n📈 ИТОГОВАЯ СТАТИСТИКА:")
                        print(f"   - Строка заголовков: {header_row_idx + 1}")
                        print(f"   - Всего строк: {len(rows)}")
                        print(f"   - Строк с данными: {len(rows) - header_row_idx - 1}")
                        print(f"   - Колонок: {len(headers)}")
                        print(f"   - Складов найдено: {len(warehouse_cols)}")
                        print(f"   - Колонок товаров: {len(product_cols)}")
                            
    except Exception as e:
        print(f"\n❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = Path("остатки на 08.07.2025.xlsx")
    if file_path.exists():
        analyze_xlsx_detailed(file_path)
    else:
        print(f"❌ Файл не найден: {file_path}")