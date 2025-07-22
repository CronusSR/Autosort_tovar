import pandas as pd
import numpy as np

# Читаем файл без заголовков
df = pd.read_excel('6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx', header=None)

print('=== РАЗМЕР ФАЙЛА ===')
print(f'Строк: {len(df)}, Колонок: {len(df.columns)}')
print()

print('=== ПЕРВЫЕ 15 СТРОК ===')
for idx in range(min(15, len(df))):
    print(f'\n--- Строка {idx} ---')
    row = df.iloc[idx]
    # Показываем только непустые ячейки
    non_empty = []
    for col, val in enumerate(row):
        if pd.notna(val) and str(val).strip() != '':
            non_empty.append((col, val))
    
    if non_empty:
        for col, val in non_empty:
            print(f'  Колонка {col}: {val}')
    else:
        print('  (пустая строка)')

print('\n\n=== АНАЛИЗ ЗАГОЛОВКОВ ===')
# Ищем строку с заголовками
for idx in range(min(20, len(df))):
    row = df.iloc[idx]
    row_str = ' '.join([str(val) for val in row if pd.notna(val)])
    if any(keyword in row_str for keyword in ['Номенклатура', 'Количество', 'Выручка', 'Себестоимость']):
        print(f'\nВозможные заголовки найдены в строке {idx}:')
        for col, val in enumerate(row):
            if pd.notna(val) and str(val).strip() != '':
                print(f'  Колонка {col}: {val}')
        break