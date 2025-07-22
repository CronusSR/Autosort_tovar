#!/usr/bin/env python3
"""
Простой парсер Excel файлов без внешних зависимостей
"""

from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re

class SimpleExcelReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.sheets = {}
        self.shared_strings = []
        
    def read_shared_strings(self, zip_file):
        """Читает shared strings из Excel файла"""
        try:
            shared_strings_xml = zip_file.read('xl/sharedStrings.xml')
            root = ET.fromstring(shared_strings_xml)
            
            # Ищем все текстовые элементы
            for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                t_elem = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                if t_elem is not None:
                    self.shared_strings.append(t_elem.text or '')
                else:
                    self.shared_strings.append('')
                    
        except Exception:
            # Пробуем без namespace
            try:
                shared_strings_xml = zip_file.read('xl/sharedStrings.xml')
                root = ET.fromstring(shared_strings_xml)
                
                for si in root.findall('.//si'):
                    t_elem = si.find('.//t')
                    if t_elem is not None:
                        self.shared_strings.append(t_elem.text or '')
                    else:
                        self.shared_strings.append('')
            except Exception as e:
                print(f"Не удалось прочитать shared strings: {e}")
    
    def parse_cell_value(self, cell):
        """Парсит значение ячейки"""
        cell_type = cell.get('t', '')
        value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
        
        if value_elem is None:
            value_elem = cell.find('.//v')
            
        if value_elem is None:
            return ''
            
        value = value_elem.text or ''
        
        if cell_type == 's':  # Shared string
            try:
                index = int(value)
                if 0 <= index < len(self.shared_strings):
                    return self.shared_strings[index]
            except (ValueError, IndexError):
                pass
        
        return value
    
    def column_index_to_letter(self, index):
        """Преобразует индекс колонки в букву"""
        result = ""
        while index > 0:
            index -= 1
            result = chr(index % 26 + ord('A')) + result
            index //= 26
        return result
    
    def parse_cell_reference(self, ref):
        """Парсит ссылку на ячейку (например, A1 -> (0, 0))"""
        match = re.match(r'([A-Z]+)(\d+)', ref)
        if not match:
            return 0, 0
            
        col_letters, row_num = match.groups()
        
        # Преобразуем буквы в индекс колонки
        col_index = 0
        for char in col_letters:
            col_index = col_index * 26 + (ord(char) - ord('A') + 1)
        col_index -= 1  # Делаем 0-based
        
        row_index = int(row_num) - 1  # Делаем 0-based
        
        return row_index, col_index
    
    def read_sheet(self, zip_file, sheet_name, sheet_rel_id):
        """Читает данные листа"""
        try:
            # Получаем путь к файлу листа
            sheet_file = f'xl/worksheets/sheet{sheet_rel_id}.xml'
            
            try:
                sheet_xml = zip_file.read(sheet_file)
            except KeyError:
                # Пробуем другой формат
                sheet_file = f'xl/worksheets/sheet{int(sheet_rel_id)}.xml'
                sheet_xml = zip_file.read(sheet_file)
                
            root = ET.fromstring(sheet_xml)
            
            # Ищем все строки
            rows_data = {}
            
            # Пробуем с namespace
            for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                row_num = int(row.get('r', 0)) - 1  # 0-based
                
                for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                    cell_ref = cell.get('r', '')
                    if cell_ref:
                        r, c = self.parse_cell_reference(cell_ref)
                        value = self.parse_cell_value(cell)
                        
                        if r not in rows_data:
                            rows_data[r] = {}
                        rows_data[r][c] = value
            
            # Если не нашли с namespace, пробуем без него
            if not rows_data:
                for row in root.findall('.//row'):
                    row_num = int(row.get('r', 0)) - 1
                    
                    for cell in row.findall('.//c'):
                        cell_ref = cell.get('r', '')
                        if cell_ref:
                            r, c = self.parse_cell_reference(cell_ref)
                            value = self.parse_cell_value(cell)
                            
                            if r not in rows_data:
                                rows_data[r] = {}
                            rows_data[r][c] = value
            
            return rows_data
            
        except Exception as e:
            print(f"Ошибка чтения листа {sheet_name}: {e}")
            return {}
    
    def get_sheet_names(self):
        """Получает список имен листов"""
        with ZipFile(self.file_path, 'r') as zip_file:
            workbook_xml = zip_file.read('xl/workbook.xml')
            root = ET.fromstring(workbook_xml)
            
            sheets = []
            # Пробуем с namespace
            for sheet in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet'):
                name = sheet.get('name')
                sheet_id = sheet.get('sheetId')
                rel_id = sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', '')
                if rel_id.startswith('rId'):
                    rel_id = rel_id[3:]  # Убираем 'rId'
                sheets.append((name, sheet_id, rel_id))
            
            # Если не нашли с namespace
            if not sheets:
                for sheet in root.findall('.//sheet'):
                    name = sheet.get('name')
                    sheet_id = sheet.get('sheetId')
                    rel_id = sheet.get('id', '').replace('rId', '')
                    sheets.append((name, sheet_id, rel_id))
            
            return sheets
    
    def read_all_sheets(self, max_rows=20, max_cols=50):
        """Читает все листы с ограничением по строкам"""
        with ZipFile(self.file_path, 'r') as zip_file:
            # Читаем shared strings
            self.read_shared_strings(zip_file)
            
            # Получаем информацию о листах
            sheets_info = self.get_sheet_names()
            
            result = {}
            for sheet_name, sheet_id, rel_id in sheets_info:
                print(f"\nЧитаю лист: {sheet_name}")
                sheet_data = self.read_sheet(zip_file, sheet_name, rel_id)
                
                # Преобразуем в читаемый формат
                formatted_data = []
                max_row = min(max(sheet_data.keys()) if sheet_data else 0, max_rows - 1)
                
                for r in range(max_row + 1):
                    row = []
                    if r in sheet_data:
                        max_col = min(max(sheet_data[r].keys()) if sheet_data[r] else 0, max_cols - 1)
                        for c in range(max_col + 1):
                            row.append(sheet_data[r].get(c, ''))
                    formatted_data.append(row)
                
                result[sheet_name] = formatted_data
                
            return result

if __name__ == "__main__":
    import sys
    
    file_path = './ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx'
    reader = SimpleExcelReader(file_path)
    
    print("=== АНАЛИЗ ФАЙЛА ОБОРАЧИВАЕМОСТЬ ===")
    
    try:
        # Читаем все листы
        all_data = reader.read_all_sheets(max_rows=20, max_cols=30)
        
        for sheet_name, data in all_data.items():
            print(f"\n{'='*60}")
            print(f"ЛИСТ: {sheet_name}")
            print(f"{'='*60}")
            
            if data:
                # Показываем первые несколько строк
                for i, row in enumerate(data[:20]):
                    if any(cell.strip() for cell in row if cell):  # Показываем только непустые строки
                        print(f"Строка {i+1:2d}: {row[:15]}")  # Показываем первые 15 колонок
                        
                print(f"\nВсего строк данных: {len(data)}")
            else:
                print("Нет данных для отображения")
                
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()