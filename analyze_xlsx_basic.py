import zipfile
import xml.etree.ElementTree as ET
import re

def read_xlsx_basic(filename):
    """Читает Excel файл используя базовые библиотеки Python"""
    
    with zipfile.ZipFile(filename, 'r') as z:
        # Читаем shared strings (общие строки)
        shared_strings = []
        try:
            with z.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                    t = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                    if t is not None:
                        shared_strings.append(t.text)
        except:
            pass
        
        # Читаем данные листа
        with z.open('xl/worksheets/sheet1.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            # Находим все строки
            rows = []
            for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                row_data = []
                row_num = int(row.get('r', 0))
                
                # Читаем ячейки в строке
                cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                
                # Создаем словарь для ячеек
                cell_dict = {}
                for cell in cells:
                    cell_ref = cell.get('r', '')
                    # Извлекаем номер колонки из ссылки (например, A1 -> 0, B1 -> 1)
                    col_letter = re.match(r'([A-Z]+)', cell_ref)
                    if col_letter:
                        col_num = 0
                        for char in col_letter.group(1):
                            col_num = col_num * 26 + ord(char) - ord('A') + 1
                        col_num -= 1  # 0-based index
                        
                        # Получаем значение ячейки
                        cell_type = cell.get('t', '')
                        v = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        
                        if v is not None:
                            if cell_type == 's':  # shared string
                                try:
                                    idx = int(v.text)
                                    value = shared_strings[idx] if idx < len(shared_strings) else v.text
                                except:
                                    value = v.text
                            else:
                                value = v.text
                        else:
                            value = ''
                        
                        cell_dict[col_num] = value
                
                # Создаем полную строку с правильным количеством колонок
                if cell_dict:
                    max_col = max(cell_dict.keys())
                    row_data = [''] * (max_col + 1)
                    for col, val in cell_dict.items():
                        row_data[col] = val
                    rows.append((row_num, row_data))
            
            return rows

# Читаем файл
filename = '6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx'
rows = read_xlsx_basic(filename)

print('=== РАЗМЕР ФАЙЛА ===')
print(f'Всего строк с данными: {len(rows)}')
if rows:
    print(f'Максимальное количество колонок: {max(len(row[1]) for row in rows)}')
print()

print('=== ПЕРВЫЕ 15 СТРОК ===')
for i, (row_num, row_data) in enumerate(rows[:15]):
    print(f'\n--- Строка {row_num-1} (индекс {i}) ---')
    non_empty = [(col, val) for col, val in enumerate(row_data) if val and str(val).strip()]
    if non_empty:
        for col, val in non_empty:
            print(f'  Колонка {col}: {val}')
    else:
        print('  (пустая строка)')

print('\n\n=== АНАЛИЗ ЗАГОЛОВКОВ ===')
# Ищем строку с заголовками
header_row_idx = None
for i, (row_num, row_data) in enumerate(rows[:20]):
    row_str = ' '.join(str(val) for val in row_data if val)
    # Ищем строку где есть "Номенклатура" в начале и "Количество" где-то дальше
    if len(row_data) > 0 and row_data[0] == 'Номенклатура' and 'Количество' in row_str:
        header_row_idx = i
        print(f'\nЗаголовки найдены в строке {row_num-1} (индекс {i}):')
        for col, val in enumerate(row_data):
            if val and str(val).strip():
                print(f'  Колонка {col}: {val}')
        
        # Проверяем следующую строку тоже, так как заголовки могут быть в двух строках
        if i + 1 < len(rows):
            next_row_num, next_row_data = rows[i + 1]
            print(f'\nДополнительные заголовки в строке {next_row_num-1} (индекс {i+1}):')
            for col, val in enumerate(next_row_data):
                if val and str(val).strip():
                    print(f'  Колонка {col}: {val}')
        break

if header_row_idx is not None:
    print('\n\n=== ПЕРВЫЕ 5 СТРОК С ДАННЫМИ ТОВАРОВ ===')
    # Начинаем с header_row_idx + 2 (пропускаем заголовки и подзаголовки)
    start_idx = header_row_idx + 2
    
    # Ищем первую строку с данными товара (не итоговую строку)
    data_start_idx = None
    for i in range(start_idx, min(start_idx + 10, len(rows))):
        row_num, row_data = rows[i]
        if row_data and row_data[0] and not row_data[0].startswith('Мебельная фурнитура'):
            data_start_idx = i
            break
    
    if data_start_idx:
        for i in range(data_start_idx, min(data_start_idx + 5, len(rows))):
            row_num, row_data = rows[i]
            print(f'\n--- Строка {row_num-1} (индекс {i}) ---')
            for col, val in enumerate(row_data):
                if val and str(val).strip():
                    print(f'  Колонка {col}: {val}')

print('\n\n=== ТОЧНЫЕ ИНДЕКСЫ КОЛОНОК ===')
if header_row_idx is not None:
    row_num, header_data = rows[header_row_idx]
    print('Основные колонки:')
    print(f'  Номенклатура: колонка 0')
    for col, val in enumerate(header_data):
        if val:
            if 'Количество' in val:
                print(f'  Количество: колонка {col}')
            elif 'Выручка' in val:
                print(f'  Выручка: колонка {col}')
            elif 'Себестоимость' in val:
                print(f'  Себестоимость товаров: колонка {col}')
                
    # Показываем подколонки себестоимости
    if header_row_idx + 1 < len(rows):
        _, subheader_data = rows[header_row_idx + 1]
        print('\nПодколонки себестоимости:')
        for col, val in enumerate(subheader_data):
            if val and str(val).strip():
                print(f'  {val}: колонка {col}')

# Дополнительный анализ структуры данных
print('\n\n=== СТРУКТУРА ДАННЫХ ===')
print('Файл содержит иерархическую структуру:')
print('1. Строка 8 (индекс 5) - основные заголовки')
print('2. Строка 9 (индекс 6) - подзаголовки для себестоимости')
print('3. Строка 10 (индекс 7) - итоговая строка "Мебельная фурнитура"')
print('4. Строки 11+ (индекс 8+) - детализация по категориям и товарам')
print('\nДанные начинаются со строки 11 (индекс 8)')
print('Первая категория - "Аксессуары для столешниц" - это группировка')
print('Детальные товары начинаются со строки 13 (индекс 10) - "Плинтус пластик 3м Берилл бежевый AP740 TP"')

# Показываем больше примеров данных
print('\n\n=== ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ ДАННЫХ (строки 20-25) ===')
for i in range(19, min(25, len(rows))):
    row_num, row_data = rows[i]
    print(f'\n--- Строка {row_num-1} (индекс {i}) ---')
    non_empty = []
    for col, val in enumerate(row_data):
        if val and str(val).strip():
            non_empty.append((col, val))
    if non_empty:
        for col, val in non_empty:
            print(f'  Колонка {col}: {val}')