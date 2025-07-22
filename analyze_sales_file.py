import pandas as pd
import numpy as np
from datetime import datetime

# Путь к файлу
file_path = "/mnt/f/Работа-Никита/Autosort_tovar/6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx"

print("=== АНАЛИЗ ФАЙЛА ПРОДАЖ ===")
print(f"Файл: {file_path.split('/')[-1]}")
print()

try:
    # Читаем файл
    df = pd.read_excel(file_path)
    
    print("1. СТРУКТУРА ФАЙЛА:")
    print(f"   - Количество строк: {len(df)}")
    print(f"   - Количество колонок: {len(df.columns)}")
    print()
    
    print("2. КОЛОНКИ В ФАЙЛЕ:")
    for i, col in enumerate(df.columns):
        print(f"   {i+1}. {col}")
    print()
    
    print("3. ТИПЫ ДАННЫХ:")
    for col in df.columns:
        print(f"   - {col}: {df[col].dtype}")
    print()
    
    print("4. ПЕРВЫЕ 15 СТРОК ДАННЫХ:")
    print(df.head(15).to_string())
    print()
    
    # Анализ дат
    print("5. АНАЛИЗ ДАТ:")
    date_columns = [col for col in df.columns if 'дата' in col.lower() or 'date' in col.lower()]
    if date_columns:
        for col in date_columns:
            try:
                # Преобразуем в datetime если еще не datetime
                if df[col].dtype == 'object':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                
                print(f"   Колонка '{col}':")
                print(f"   - Минимальная дата: {df[col].min()}")
                print(f"   - Максимальная дата: {df[col].max()}")
                print(f"   - Количество уникальных дат: {df[col].nunique()}")
            except:
                print(f"   - Не удалось проанализировать даты в колонке '{col}'")
    else:
        print("   - Колонки с датами не найдены")
    print()
    
    # Анализ номенклатуры
    print("6. АНАЛИЗ НОМЕНКЛАТУРЫ:")
    nomenclature_columns = [col for col in df.columns if 'номенклатура' in col.lower() or 'товар' in col.lower() or 'наименование' in col.lower()]
    if nomenclature_columns:
        for col in nomenclature_columns:
            print(f"   Колонка '{col}':")
            print(f"   - Количество уникальных товаров: {df[col].nunique()}")
            print(f"   - Примеры товаров:")
            for item in df[col].unique()[:5]:
                print(f"     • {item}")
    print()
    
    # Анализ количества и цен
    print("7. АНАЛИЗ КОЛИЧЕСТВА И ЦЕН:")
    quantity_columns = [col for col in df.columns if 'количество' in col.lower() or 'кол-во' in col.lower() or 'qty' in col.lower()]
    price_columns = [col for col in df.columns if 'цена' in col.lower() or 'стоимость' in col.lower() or 'сумма' in col.lower() or 'price' in col.lower()]
    
    if quantity_columns:
        for col in quantity_columns:
            print(f"   Колонка '{col}':")
            print(f"   - Общее количество: {df[col].sum()}")
            print(f"   - Среднее количество: {df[col].mean():.2f}")
    
    if price_columns:
        for col in price_columns:
            print(f"   Колонка '{col}':")
            print(f"   - Общая сумма: {df[col].sum():,.2f}")
            print(f"   - Средняя сумма: {df[col].mean():,.2f}")
    print()
    
    # Проверка на пустые значения
    print("8. АНАЛИЗ ПУСТЫХ ЗНАЧЕНИЙ:")
    null_counts = df.isnull().sum()
    for col in df.columns:
        if null_counts[col] > 0:
            print(f"   - {col}: {null_counts[col]} пустых значений ({null_counts[col]/len(df)*100:.1f}%)")
    
    # Сохраняем образец данных для детального изучения
    print("\n9. СОХРАНЕНИЕ ОБРАЗЦА ДАННЫХ:")
    sample_file = "/mnt/f/Работа-Никита/Autosort_tovar/sample_sales_data.csv"
    df.head(50).to_csv(sample_file, index=False, encoding='utf-8-sig')
    print(f"   Образец данных (первые 50 строк) сохранен в: {sample_file}")
    
except Exception as e:
    print(f"Ошибка при чтении файла: {e}")
    print("\nПопытка прочитать файл с другими параметрами...")
    
    try:
        # Пробуем прочитать с указанием листа
        xl_file = pd.ExcelFile(file_path)
        print(f"Листы в файле: {xl_file.sheet_names}")
        
        # Читаем первый лист
        df = pd.read_excel(file_path, sheet_name=0)
        print(f"Успешно прочитан лист: {xl_file.sheet_names[0]}")
        
    except Exception as e2:
        print(f"Повторная ошибка: {e2}")