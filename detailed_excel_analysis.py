#!/usr/bin/env python3
"""
Детальный анализ файла ОБОРАЧИВАЕМОСТЬ для понимания структуры системы
"""

from excel_reader import SimpleExcelReader

def analyze_sheet_structure(sheet_name, data, max_rows=50):
    """Анализирует структуру конкретного листа"""
    print(f"\n{'='*80}")
    print(f"ДЕТАЛЬНЫЙ АНАЛИЗ ЛИСТА: {sheet_name}")
    print(f"{'='*80}")
    
    if not data:
        print("Нет данных для анализа")
        return
    
    # Определяем количество колонок
    max_cols = max(len(row) for row in data if row)
    non_empty_rows = [i for i, row in enumerate(data) if any(cell.strip() for cell in row if cell)]
    
    print(f"Общая информация:")
    print(f"- Максимальное количество колонок: {max_cols}")
    print(f"- Количество непустых строк: {len(non_empty_rows)}")
    print(f"- Общее количество строк: {len(data)}")
    
    # Анализируем заголовки
    print(f"\nСтруктура заголовков:")
    for i in range(min(5, len(data))):
        if any(cell.strip() for cell in data[i] if cell):
            print(f"Строка {i+1:2d}: {[cell for cell in data[i][:20] if cell.strip()]}")
    
    # Ищем данные (пропускаем пустые строки и заголовки)
    data_start_row = None
    for i, row in enumerate(data):
        # Пропускаем строки с заголовками или полностью пустые
        if i < 10:  # Первые 10 строк обычно заголовки
            continue
        if any(cell.strip() and not cell.strip().startswith('=') for cell in row if cell):
            data_start_row = i
            break
    
    if data_start_row:
        print(f"\nДанные начинаются с строки: {data_start_row + 1}")
        print("Примеры данных:")
        count = 0
        for i in range(data_start_row, min(data_start_row + 10, len(data))):
            if any(cell.strip() for cell in data[i] if cell):
                print(f"Строка {i+1:2d}: {data[i][:15]}")
                count += 1
                if count >= 5:
                    break
    
    # Анализируем типы данных в колонках
    print(f"\nАнализ типов данных:")
    for col in range(min(15, max_cols)):
        col_data = [row[col] if col < len(row) else '' for row in data]
        col_data = [cell for cell in col_data if cell.strip()]
        
        if col_data:
            # Определяем тип данных
            numeric_count = sum(1 for cell in col_data if is_numeric(cell))
            text_count = len(col_data) - numeric_count
            
            col_type = "ЧИСЛОВАЯ" if numeric_count > text_count else "ТЕКСТОВАЯ"
            sample = col_data[0] if col_data else ""
            
            print(f"Колонка {col+1:2d}: {col_type:10s} (пример: '{sample[:30]}')")

def is_numeric(value):
    """Проверяет, является ли значение числовым"""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip().replace(',', '.')
    try:
        float(value)
        return True
    except:
        return False

def analyze_formulas_and_calculations(data):
    """Анализирует формулы и расчеты"""
    print(f"\nФормулы и расчеты:")
    formula_count = 0
    
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            if cell and str(cell).startswith('='):
                print(f"Строка {i+1}, Колонка {j+1}: {cell}")
                formula_count += 1
                if formula_count >= 10:  # Ограничиваем вывод
                    break
        if formula_count >= 10:
            break
    
    if formula_count == 0:
        print("Формулы не найдены (возможно, показаны только значения)")

def main():
    file_path = './ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx'
    reader = SimpleExcelReader(file_path)
    
    print("ПОЛНЫЙ АНАЛИЗ СИСТЕМЫ ОБОРАЧИВАЕМОСТИ")
    print("="*80)
    
    try:
        # Читаем все листы с большим количеством строк
        all_data = reader.read_all_sheets(max_rows=100, max_cols=50)
        
        # Анализируем каждый лист подробно
        for sheet_name, data in all_data.items():
            analyze_sheet_structure(sheet_name, data)
            analyze_formulas_and_calculations(data)
            
            # Специальный анализ для ключевых листов
            if "ОБОРАЧ" in sheet_name.upper():
                print(f"\n>>> СПЕЦИАЛЬНЫЙ АНАЛИЗ ЛИСТА ОБОРАЧИВАЕМОСТИ <<<")
                analyze_turnover_sheet(data)
            elif "ABC" in sheet_name.upper():
                print(f"\n>>> СПЕЦИАЛЬНЫЙ АНАЛИЗ ABC ЛИСТА <<<")
                analyze_abc_sheet(data)
        
        # Общие выводы
        print(f"\n{'='*80}")
        print("ОБЩИЕ ВЫВОДЫ О СИСТЕМЕ")
        print(f"{'='*80}")
        
        print(f"1. Структура системы:")
        for i, sheet_name in enumerate(all_data.keys(), 1):
            print(f"   {i}. {sheet_name}")
        
        print(f"\n2. Основные компоненты:")
        print(f"   - Справочник номенклатуры")
        print(f"   - Данные об остатках по складам")
        print(f"   - История продаж")
        print(f"   - Расчеты оборачиваемости")
        print(f"   - ABC-анализ")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

def analyze_turnover_sheet(data):
    """Специальный анализ листа оборачиваемости"""
    print("Анализ расчетов оборачиваемости:")
    
    # Ищем ключевые колонки
    for i, row in enumerate(data[:10]):
        if any('ОБОРАЧ' in str(cell).upper() for cell in row if cell):
            print(f"Строка с оборачиваемостью {i+1}: {row}")
        if any('ДН' in str(cell).upper() for cell in row if cell):
            print(f"Строка с днями {i+1}: {row}")

def analyze_abc_sheet(data):
    """Специальный анализ ABC листа"""
    print("Анализ ABC-классификации:")
    
    # Ищем процентные значения и категории A, B, C
    for i, row in enumerate(data[:20]):
        if any(str(cell) in ['A', 'B', 'C'] for cell in row if cell):
            print(f"ABC строка {i+1}: {row}")

if __name__ == "__main__":
    main()