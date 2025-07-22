import pandas as pd
import numpy as np

def analyze_excel_formula():
    """
    Анализ формулы СУММЕСЛИМН из Excel файла оборачиваемости
    """
    file_path = '/mnt/f/Работа-Никита/Autosort_tovar/ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx'
    
    print('=== АНАЛИЗ ФОРМУЛЫ СУММЕСЛИМН ===')
    print('Формула: =СУММЕСЛИМН(ОСТАТКИ!AD:AD;ОСТАТКИ!Q:Q;"ABC ПО СКЛАДАМ"!A:A;ОСТАТКИ!S:S;"ABC ПО СКЛАДАМ"!C$3)')
    print()
    
    # Читаем все листы
    xl_file = pd.ExcelFile(file_path)
    
    # Лист ОСТАТКИ - ищем правильные заголовки
    print('=== АНАЛИЗ ЛИСТА ОСТАТКИ ===')
    df_ostatok_raw = pd.read_excel(file_path, sheet_name='ОСТАТКИ')
    
    # Найдем строку с номенклатурой (заголовок)
    header_row = None
    for i in range(len(df_ostatok_raw)):
        if pd.notna(df_ostatok_raw.iloc[i, 0]) and 'Номенклатура' in str(df_ostatok_raw.iloc[i, 0]):
            header_row = i
            break
    
    if header_row is not None:
        print(f'Заголовки найдены в строке {header_row}')
        # Читаем с правильными заголовками
        df_ostatok = pd.read_excel(file_path, sheet_name='ОСТАТКИ', header=header_row)
        
        # Очищаем от пустых строк в начале
        df_ostatok = df_ostatok.dropna(how='all').reset_index(drop=True)
        
        print(f'Размер данных ОСТАТКИ: {df_ostatok.shape}')
        print('Столбцы листа ОСТАТКИ:')
        for i, col in enumerate(df_ostatok.columns):
            excel_col = ''
            if i < 26:
                excel_col = chr(65 + i)  # A-Z
            else:
                excel_col = chr(65 + (i // 26) - 1) + chr(65 + (i % 26))  # AA, AB, etc.
            print(f'  {excel_col} ({i}): {col}')
            
        # Найдем столбцы Q (16), S (18), AD (29)
        print()
        print('Анализ столбцов формулы:')
        if len(df_ostatok.columns) > 16:
            print(f'Столбец Q (17): {df_ostatok.columns[16]}')
            print(f'  Пример: {df_ostatok.iloc[:3, 16].values}')
            
        if len(df_ostatok.columns) > 18:
            print(f'Столбец S (19): {df_ostatok.columns[18]}')
            print(f'  Пример: {df_ostatok.iloc[:3, 18].values}')
            
        if len(df_ostatok.columns) > 29:
            print(f'Столбец AD (30): {df_ostatok.columns[29]}')
            print(f'  Пример: {df_ostatok.iloc[:3, 29].values}')
    
    print()
    print('=== АНАЛИЗ ЛИСТА ABC ПО СКЛАДАМ ===')
    df_abc = pd.read_excel(file_path, sheet_name='ABC ПО СКЛАДАМ')
    
    print(f'Размер ABC ПО СКЛАДАМ: {df_abc.shape}')
    print('Столбец A (категории):')
    print(df_abc.iloc[:10, 0].values)
    
    print()
    print('Столбец C, строка 3:')
    if len(df_abc) > 2 and len(df_abc.columns) > 2:
        print(f'  Значение: {df_abc.iloc[2, 2]}')
    
    print()
    print('=== ЛОГИКА ФОРМУЛЫ ===')
    print('СУММЕСЛИМН работает так:')
    print('1. Суммирует значения из ОСТАТКИ!AD:AD (столбец 30)')
    print('2. Где ОСТАТКИ!Q:Q (столбец 17) = "ABC ПО СКЛАДАМ"!A:A (категория)')
    print('3. И ОСТАТКИ!S:S (столбец 19) = "ABC ПО СКЛАДАМ"!C$3 (ABC класс)')
    print()
    print('Это значит: суммирует остатки товаров определенной категории и ABC класса')
    
    return df_ostatok if header_row is not None else None, df_abc

if __name__ == '__main__':
    df_ostatok, df_abc = analyze_excel_formula()