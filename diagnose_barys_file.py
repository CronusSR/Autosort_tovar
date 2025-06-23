#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая диагностика файла Барыс для понимания структуры
"""

import streamlit as st
import pandas as pd

def diagnose_barys_file():
    """
    Диагностирует файл Барыс для понимания где находятся цены
    """
    
    st.header("🔍 Диагностика файла Барыс")
    
    barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("📊 Анализировать файл"):
        try:
            # Читаем файл
            df = pd.read_excel(barys_file)
            
            st.success(f"✅ Файл загружен: {len(df)} строк, {len(df.columns)} колонок")
            
            # Показываем все названия колонок
            st.subheader("📋 Все колонки файла")
            
            for idx, col_name in enumerate(df.columns):
                col_letter = chr(65 + idx)  # A, B, C, D...
                col_name_str = str(col_name).strip()
                
                # Выделяем 12-ю колонку (L)
                if idx == 11:
                    st.write(f"**{idx+1:2d}. {col_letter} - {col_name_str} ← 12-я колонка (L)**")
                else:
                    st.write(f"{idx+1:2d}. {col_letter} - {col_name_str}")
            
            # Показываем данные в 12-й колонке (L)
            st.subheader("🎯 Данные в 12-й колонке (L)")
            
            if len(df.columns) >= 12:
                col_12 = df.iloc[:, 11]  # 12-я колонка
                col_12_name = df.columns[11]
                
                st.write(f"**Название 12-й колонки:** {col_12_name}")
                
                # Показываем первые 15 строк
                st.write("**Первые 15 строк в колонке L:**")
                for i in range(min(15, len(col_12))):
                    value = col_12.iloc[i]
                    st.write(f"L{i+1:2d}: {value} (тип: {type(value).__name__})")
                
                # Специально анализируем с L4
                st.write("**Анализ данных начиная с L4:**")
                
                data_from_L4 = col_12.iloc[3:15]  # L4-L15
                numeric_count = 0
                numeric_values = []
                
                for i, val in enumerate(data_from_L4):
                    row_num = i + 4
                    is_numeric = False
                    
                    if pd.notna(val):
                        try:
                            if isinstance(val, (int, float)) and val > 0:
                                numeric_count += 1
                                numeric_values.append(float(val))
                                is_numeric = True
                            elif isinstance(val, str):
                                # Пробуем извлечь число
                                val_clean = str(val).replace(' ', '').replace(',', '.')
                                val_clean = ''.join(c for c in val_clean if c.isdigit() or c == '.')
                                if val_clean:
                                    num_val = float(val_clean)
                                    if num_val > 0:
                                        numeric_count += 1
                                        numeric_values.append(num_val)
                                        is_numeric = True
                        except:
                            pass
                    
                    icon = "✅" if is_numeric else "❌"
                    st.write(f"{icon} L{row_num}: {val}")
                
                if numeric_values:
                    st.success(f"✅ Найдено {numeric_count} числовых значений")
                    st.write(f"Среднее: {sum(numeric_values)/len(numeric_values):,.2f}")
                    st.write(f"Минимум: {min(numeric_values):,.2f}")
                    st.write(f"Максимум: {max(numeric_values):,.2f}")
                else:
                    st.error("❌ Числовые значения не найдены в L4-L15")
            
            # Ищем колонки содержащие "посл" и "закуп"
            st.subheader("🔍 Поиск колонок со словами 'посл' и 'закуп'")
            
            found_posled = False
            for idx, col_name in enumerate(df.columns):
                col_name_str = str(col_name).strip().lower()
                if 'посл' in col_name_str:
                    st.write(f"✅ Колонка {idx+1}: '{df.columns[idx]}' содержит 'посл'")
                    found_posled = True
                if 'закуп' in col_name_str:
                    st.write(f"✅ Колонка {idx+1}: '{df.columns[idx]}' содержит 'закуп'")
                    found_posled = True
                if 'посл' in col_name_str and 'закуп' in col_name_str:
                    st.success(f"🎯 НАЙДЕНА: Колонка {idx+1} '{df.columns[idx]}' содержит И 'посл' И 'закуп'")
            
            if not found_posled:
                st.warning("⚠️ Колонки с 'посл' или 'закуп' не найдены")
            
            # Дополнительный поиск ценовых колонок
            st.subheader("💰 Поиск возможных ценовых колонок")
            
            price_keywords = ['цена', 'price', 'стоимость', 'сумма', 'средн', 'сред', 'руб', 'тенге', 'cost']
            
            for idx, col_name in enumerate(df.columns):
                col_name_str = str(col_name).strip().lower()
                
                matching_words = []
                for keyword in price_keywords:
                    if keyword in col_name_str:
                        matching_words.append(keyword)
                
                if matching_words:
                    st.write(f"💰 Колонка {idx+1}: '{df.columns[idx]}' содержит: {matching_words}")
                    
                    # Быстрый анализ данных
                    col_data = df.iloc[:, idx].iloc[3:10]  # С 4-й строки
                    numeric_count = sum(1 for val in col_data if pd.notna(val) and isinstance(val, (int, float)) and val > 0)
                    st.write(f"   Числовых значений с 4-й строки: {numeric_count}/7")
            
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    diagnose_barys_file()