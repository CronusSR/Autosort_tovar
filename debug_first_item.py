#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика проблемы с пропуском первого товара
"""

import streamlit as st
import pandas as pd

def debug_first_item_issue():
    """
    Диагностирует почему пропускается первый товар
    """
    st.header("🔍 Диагностика пропуска первого товара")
    
    if st.button("📊 Анализировать структуру файла"):
        try:
            # Загружаем файл
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            df = pd.read_excel(barys_file)
            st.success(f"✅ Файл загружен: {df.shape}")
            
            # Анализируем структуру файла
            st.subheader("📋 Анализ структуры файла")
            
            st.write("**Первые 10 строк колонки B (номенклатура):**")
            for i in range(min(10, len(df))):
                value = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
                st.write(f"Строка {i+1} (B{i+1}): {value}")
            
            # Параметры как в integration_patch
            start_row = 3  # Строка 4
            nomenclature_col = 1  # B
            
            st.subheader(f"🎯 Логика integration_patch (start_row={start_row})")
            
            # Шаг 1: Получаем данные начиная со start_row
            st.write(f"**Шаг 1: df.iloc[{start_row}:, {nomenclature_col}]**")
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
            st.write(f"Получено {len(nomenclature_data)} строк начиная с строки {start_row+1}")
            
            # Показываем первые элементы
            st.write("Первые 5 элементов:")
            for i, (idx, value) in enumerate(nomenclature_data.head().items()):
                original_row = idx + 1
                st.write(f"  {i+1}. Строка {original_row}: {value}")
            
            # Шаг 2: Убираем пустые
            st.write(f"**Шаг 2: dropna() и очистка**")
            nomenclature_clean = nomenclature_data.dropna()
            st.write(f"После dropna(): {len(nomenclature_clean)} строк")
            
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            st.write(f"После удаления пустых строк: {len(nomenclature_clean)} строк")
            
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            st.write(f"После удаления 'nan': {len(nomenclature_clean)} строк")
            
            # Показываем что осталось
            st.write("Первые 5 элементов после очистки:")
            for i, (idx, value) in enumerate(nomenclature_clean.head().items()):
                original_row = idx + 1
                st.write(f"  {i+1}. Строка {original_row}: {value}")
            
            # Шаг 3: Исключаем последнюю строку
            st.write(f"**Шаг 3: Исключение последней строки [:-1]**")
            if len(nomenclature_clean) > 0:
                last_item_before = nomenclature_clean.iloc[-1]
                last_row_before = nomenclature_clean.index[-1] + 1
                
                nomenclature_clean = nomenclature_clean[:-1]
                st.write(f"Исключена последняя строка {last_row_before}: '{last_item_before}'")
                st.write(f"Осталось: {len(nomenclature_clean)} товаров")
            
            # Финальный результат
            st.write(f"**ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:**")
            
            if len(nomenclature_clean) > 0:
                st.write("Товары которые БУДУТ обработаны:")
                for i, (idx, value) in enumerate(nomenclature_clean.head(10).items()):
                    original_row = idx + 1
                    st.write(f"  {i+1}. Строка {original_row}: {value}")
                
                if len(nomenclature_clean) > 10:
                    st.write(f"  ... и еще {len(nomenclature_clean) - 10} товаров")
            
            # Проверим что пропускается
            st.subheader("🚨 Анализ пропущенных товаров")
            
            # Товары в строках 1-3 (до start_row)
            st.write("**Товары в строках 1-3 (пропускаются из-за start_row=3):**")
            for i in range(3):
                if i < len(df):
                    value = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
                    is_valid = pd.notna(value) and str(value).strip() != '' and str(value) != 'nan'
                    status = "✅ Валидный товар" if is_valid else "❌ Не товар"
                    st.write(f"  Строка {i+1} (B{i+1}): {value} - {status}")
            
            # Самый первый товар который обрабатывается
            if len(nomenclature_clean) > 0:
                first_processed_idx = nomenclature_clean.index[0]
                first_processed_row = first_processed_idx + 1
                first_processed_value = nomenclature_clean.iloc[0]
                
                st.write(f"**Первый обрабатываемый товар:**")
                st.write(f"  Строка {first_processed_row}: '{first_processed_value}'")
                
                # Проверяем есть ли товары выше
                st.write(f"**Проверка товаров выше строки {first_processed_row}:**")
                found_earlier_products = []
                
                for i in range(first_processed_idx):
                    value = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
                    if pd.notna(value) and str(value).strip() != '' and str(value) != 'nan':
                        # Простая проверка что это похоже на товар
                        if len(str(value)) > 3 and not str(value).lower() in ['номенклатура', 'наименование', 'товар']:
                            found_earlier_products.append((i+1, value))
                
                if found_earlier_products:
                    st.error(f"🚨 **НАЙДЕНЫ ПРОПУЩЕННЫЕ ТОВАРЫ!**")
                    st.write("Товары которые пропускаются:")
                    for row_num, product in found_earlier_products:
                        st.write(f"  ❌ Строка {row_num}: '{product}'")
                    
                    st.write(f"**💡 РЕШЕНИЕ:**")
                    st.write(f"Нужно изменить start_row с {start_row} на {found_earlier_products[0][0]-1}")
                else:
                    st.success("✅ Пропущенных товаров не найдено")
            
            # Рекомендации
            st.subheader("💡 Рекомендации")
            
            # Найдем первую строку с товаром
            first_product_row = None
            for i in range(len(df)):
                value = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
                if pd.notna(value) and str(value).strip() != '' and str(value) != 'nan':
                    # Простая проверка что это товар, а не заголовок
                    if len(str(value)) > 3 and not any(word in str(value).lower() for word in ['номенклатура', 'наименование', 'товар', 'название']):
                        first_product_row = i
                        break
            
            if first_product_row is not None:
                st.write(f"🎯 **Первый товар найден в строке {first_product_row + 1}**: '{df.iloc[first_product_row, 1]}'")
                
                if first_product_row != start_row:
                    st.warning(f"⚠️ Текущий start_row={start_row} (строка {start_row+1}), но первый товар в строке {first_product_row+1}")
                    st.write(f"**Рекомендация:** изменить start_row с {start_row} на {first_product_row}")
                else:
                    st.success(f"✅ start_row настроен правильно")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

def test_different_start_rows():
    """Тестирует разные значения start_row"""
    st.subheader("🧪 Тест разных start_row")
    
    start_row_to_test = st.number_input(
        "Тестовый start_row", 
        min_value=0, 
        max_value=10, 
        value=3,
        help="Попробуйте разные значения start_row"
    )
    
    if st.button(f"🔬 Тестировать start_row={start_row_to_test}"):
        try:
            # Загружаем файл
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            df = pd.read_excel(barys_file)
            
            # Тестируем с новым start_row
            nomenclature_col = 1
            
            nomenclature_data = df.iloc[start_row_to_test:, nomenclature_col].copy()
            nomenclature_clean = nomenclature_data.dropna()
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            
            # Исключаем последнюю строку
            if len(nomenclature_clean) > 0:
                nomenclature_clean = nomenclature_clean[:-1]
            
            st.write(f"📊 **Результат с start_row={start_row_to_test}:**")
            st.write(f"Найдено товаров: {len(nomenclature_clean)}")
            
            if len(nomenclature_clean) > 0:
                st.write("**Первые 10 товаров:**")
                for i, (idx, value) in enumerate(nomenclature_clean.head(10).items()):
                    original_row = idx + 1
                    st.write(f"  {i+1}. Строка {original_row}: {value}")
            else:
                st.error("❌ Товары не найдены")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    st.title("🔍 Диагностика пропуска первого товара")
    
    st.markdown("""
    **Проблема:** Система пропускает самый первый товар, начинает со второго.
    
    **Возможные причины:**
    1. `start_row = 3` - начинаем не с той строки
    2. `nomenclature_clean[:-1]` - исключаем не ту строку
    3. Структура файла отличается от ожидаемой
    """)
    
    debug_first_item_issue()
    
    st.markdown("---")
    
    test_different_start_rows()