#!/usr/bin/env python3
"""Анализ структуры файла остатков"""

import pandas as pd
import json
from pathlib import Path

def analyze_inventory_file(file_path):
    """Детальный анализ файла остатков"""
    
    print(f"Анализ файла: {file_path}")
    print("=" * 80)
    
    try:
        # Читаем файл
        df = pd.read_excel(file_path)
        
        # 1. Основная информация
        print("\n1. ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print(f"   - Количество строк: {len(df)}")
        print(f"   - Количество колонок: {len(df.columns)}")
        
        # 2. Структура колонок
        print("\n2. СТРУКТУРА КОЛОНОК:")
        for i, col in enumerate(df.columns):
            print(f"   [{i}] {col}")
            
        # 3. Типы данных
        print("\n3. ТИПЫ ДАННЫХ:")
        for col in df.columns:
            print(f"   - {col}: {df[col].dtype}")
            
        # 4. Первые 15 строк
        print("\n4. ПЕРВЫЕ 15 СТРОК:")
        print(df.head(15).to_string())
        
        # 5. Анализ складов/филиалов
        print("\n5. АНАЛИЗ СКЛАДОВ/ФИЛИАЛОВ:")
        
        # Ищем колонки со складами
        warehouse_cols = []
        for col in df.columns:
            if 'склад' in str(col).lower() or 'филиал' in str(col).lower() or 'магазин' in str(col).lower():
                warehouse_cols.append(col)
                
        if warehouse_cols:
            print(f"   Найдены колонки складов: {warehouse_cols}")
            for col in warehouse_cols:
                unique_values = df[col].dropna().unique()
                print(f"\n   {col}:")
                for val in unique_values[:10]:  # Первые 10 значений
                    print(f"      - {val}")
                if len(unique_values) > 10:
                    print(f"      ... и еще {len(unique_values) - 10} значений")
        
        # 6. Поиск колонок с остатками
        print("\n6. ПОИСК КОЛОНОК С ОСТАТКАМИ:")
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        print(f"   Числовые колонки: {list(numeric_cols)}")
        
        # 7. Анализ номенклатуры
        print("\n7. АНАЛИЗ НОМЕНКЛАТУРЫ:")
        
        # Ищем колонки с названиями товаров
        product_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['товар', 'номенклатура', 'наименование', 'название', 'артикул']):
                product_cols.append(col)
                
        if product_cols:
            print(f"   Найдены колонки товаров: {product_cols}")
            for col in product_cols:
                unique_count = df[col].nunique()
                print(f"   - {col}: {unique_count} уникальных значений")
                print(f"     Примеры:")
                for val in df[col].dropna().head(5):
                    print(f"       • {val}")
                    
        # 8. Поиск категорий
        print("\n8. ПОИСК КАТЕГОРИЙ:")
        category_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ['категория', 'группа', 'раздел', 'тип']):
                category_cols.append(col)
                
        if category_cols:
            print(f"   Найдены колонки категорий: {category_cols}")
            for col in category_cols:
                unique_count = df[col].nunique()
                print(f"   - {col}: {unique_count} уникальных значений")
                print(f"     Примеры:")
                for val in df[col].dropna().unique()[:5]:
                    print(f"       • {val}")
                    
        # 9. Структура данных остатков
        print("\n9. СТРУКТУРА ДАННЫХ ОСТАТКОВ:")
        
        # Проверяем, есть ли отдельные колонки для каждого склада
        all_cols = list(df.columns)
        warehouse_stock_cols = []
        
        # Ищем паттерны типа "Склад 1", "Магазин Барыс" и т.д.
        for col in all_cols:
            col_str = str(col)
            if any(char.isdigit() for char in col_str) or any(word in col_str.lower() for word in ['барыс', 'абая', 'айнабулак']):
                if not any(word in col_str.lower() for word in ['артикул', 'код', 'дата', 'цена']):
                    warehouse_stock_cols.append(col)
                    
        if warehouse_stock_cols:
            print(f"   Возможные колонки остатков по складам: {len(warehouse_stock_cols)} шт.")
            print("   Примеры:")
            for col in warehouse_stock_cols[:10]:
                print(f"     - {col}")
                
        # 10. Проверка формата остатков
        print("\n10. ПРОВЕРКА ФОРМАТА ОСТАТКОВ:")
        
        # Берем первую числовую колонку для анализа
        if len(numeric_cols) > 0:
            sample_col = numeric_cols[0]
            print(f"   Анализ колонки '{sample_col}':")
            print(f"     - Минимум: {df[sample_col].min()}")
            print(f"     - Максимум: {df[sample_col].max()}")
            print(f"     - Среднее: {df[sample_col].mean():.2f}")
            print(f"     - Есть дробные числа: {(df[sample_col] % 1 != 0).any()}")
            
        # 11. Сохраняем структуру в JSON
        structure = {
            "file_name": str(file_path),
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "data_types": {col: str(df[col].dtype) for col in df.columns},
            "warehouse_columns": warehouse_cols,
            "product_columns": product_cols,
            "category_columns": category_cols,
            "numeric_columns": list(numeric_cols),
            "possible_warehouse_stock_columns": warehouse_stock_cols[:20]  # Первые 20
        }
        
        with open('inventory_structure.json', 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)
            
        print("\n✅ Структура сохранена в файл 'inventory_structure.json'")
        
    except Exception as e:
        print(f"\n❌ Ошибка при анализе файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    file_path = Path("остатки на 08.07.2025.xlsx")
    if file_path.exists():
        analyze_inventory_file(file_path)
    else:
        print(f"❌ Файл не найден: {file_path}")