#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры файлов для понимания формата цен
"""

import streamlit as st
import pandas as pd
import numpy as np

def analyze_ads_file_structure(file_path):
    """
    Анализирует структуру ADS файла для понимания где находятся цены
    """
    try:
        st.write(f"📊 Анализирую файл: {file_path}")
        
        # Читаем файл
        df = pd.read_excel(file_path)
        
        st.write(f"📐 Размер файла: {len(df)} строк, {len(df.columns)} колонок")
        
        # Показываем первые строки
        st.subheader("🔍 Первые 10 строк файла")
        st.dataframe(df.head(10))
        
        # Показываем названия колонок
        st.subheader("📋 Структура колонок")
        col_info = []
        for i, col in enumerate(df.columns):
            col_info.append({
                'Номер': i + 1,
                'Название': str(col),
                'Тип данных': str(df[col].dtype),
                'Пример значения': str(df[col].iloc[0]) if len(df) > 0 else 'N/A'
            })
        
        col_df = pd.DataFrame(col_info)
        st.dataframe(col_df)
        
        # Анализируем 12-ю колонку специально
        st.subheader("🎯 Анализ 12-й колонки (где должны быть цены)")
        
        if len(df.columns) >= 12:
            col_12 = df.iloc[:, 11]  # 12-я колонка (индекс 11)
            col_name = df.columns[11]
            
            st.write(f"**Название 12-й колонки:** {col_name}")
            st.write(f"**Тип данных:** {col_12.dtype}")
            
            # Показываем значения с 4-й строки
            st.write("**Значения начиная с 4-й строки:**")
            values_from_4th = col_12.iloc[3:13]  # строки 4-13
            
            values_info = []
            for idx, val in enumerate(values_from_4th):
                values_info.append({
                    'Строка в файле': idx + 4,
                    'Значение': str(val),
                    'Тип': type(val).__name__,
                    'Пустое?': pd.isna(val),
                    'Число?': pd.api.types.is_numeric_dtype(type(val)) if not pd.isna(val) else False
                })
            
            values_df = pd.DataFrame(values_info)
            st.dataframe(values_df)
            
            # Статистика по ценам
            numeric_values = []
            for val in col_12.iloc[3:]:
                if pd.notna(val):
                    try:
                        # Пробуем преобразовать в число
                        if isinstance(val, (int, float)):
                            numeric_values.append(float(val))
                        else:
                            val_str = str(val).replace(' ', '').replace(',', '.')
                            val_clean = ''.join(c for c in val_str if c.isdigit() or c == '.')
                            if val_clean:
                                numeric_values.append(float(val_clean))
                    except:
                        pass
            
            if numeric_values:
                st.success(f"✅ Найдено {len(numeric_values)} числовых значений")
                st.write(f"Минимум: {min(numeric_values):,.2f}")
                st.write(f"Максимум: {max(numeric_values):,.2f}")
                st.write(f"Среднее: {np.mean(numeric_values):,.2f}")
            else:
                st.error("❌ Числовые значения не найдены в 12-й колонке")
        else:
            st.error(f"❌ В файле только {len(df.columns)} колонок, 12-й колонки нет")
        
        # Ищем колонки которые могут содержать цены
        st.subheader("🔍 Поиск возможных ценовых колонок")
        
        price_keywords = ['цена', 'price', 'стоимость', 'cost', 'сумма', 'закуп', 'руб', 'тенге', 'сред']
        possible_price_cols = []
        
        for i, col in enumerate(df.columns):
            col_str = str(col).lower()
            for keyword in price_keywords:
                if keyword in col_str:
                    possible_price_cols.append({
                        'Номер колонки': i + 1,
                        'Название': str(col),
                        'Ключевое слово': keyword,
                        'Пример значения': str(df[col].iloc[3]) if len(df) > 3 else 'N/A'
                    })
                    break
        
        if possible_price_cols:
            st.write("**Найдены возможные ценовые колонки:**")
            price_cols_df = pd.DataFrame(possible_price_cols)
            st.dataframe(price_cols_df)
        else:
            st.warning("⚠️ Колонки с ценовыми ключевыми словами не найдены")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Ошибка анализа файла: {str(e)}")
        return None


def analyze_warehouse_file_structure(file_path):
    """
    Анализирует структуру файла остатков
    """
    try:
        st.write(f"🏪 Анализирую файл остатков: {file_path}")
        
        # Читаем файл
        df = pd.read_excel(file_path)
        
        st.write(f"📐 Размер файла: {len(df)} строк, {len(df.columns)} колонок")
        
        # Показываем первые строки
        st.subheader("🔍 Первые 15 строк файла остатков")
        st.dataframe(df.head(15))
        
        # Анализируем структуру заголовков
        st.subheader("📋 Анализ заголовков")
        
        # Ищем строку с заголовками (7-я строка по умолчанию)
        for row_idx in range(min(10, len(df))):
            st.write(f"**Строка {row_idx + 1}:**")
            row_data = df.iloc[row_idx].tolist()
            st.write(row_data[:10])  # Показываем первые 10 значений
        
        # Ищем склады в заголовках
        st.subheader("🏪 Поиск складов в заголовках")
        
        warehouse_keywords = [
            'склад', 'магазин', 'база', 'барыс', 'казыбаева', 'овощная', 'комплект', 
            'trade', 'шымкент', 'астана', 'алматы'
        ]
        
        found_warehouses = []
        
        for row_idx in range(min(10, len(df))):
            for col_idx, cell_value in enumerate(df.iloc[row_idx]):
                if pd.notna(cell_value):
                    cell_str = str(cell_value).lower()
                    for keyword in warehouse_keywords:
                        if keyword in cell_str:
                            found_warehouses.append({
                                'Строка': row_idx + 1,
                                'Колонка': col_idx + 1,
                                'Значение': str(cell_value),
                                'Ключевое слово': keyword
                            })
        
        if found_warehouses:
            warehouses_df = pd.DataFrame(found_warehouses)
            st.dataframe(warehouses_df)
        else:
            st.warning("⚠️ Склады в заголовках не найдены")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Ошибка анализа файла остатков: {str(e)}")
        return None


def main():
    st.header("🔍 Анализ структуры файлов")
    st.caption("Анализируем ваши файлы для понимания формата данных")
    
    # Анализ ADS файла
    st.subheader("📊 Анализ ADS файла (Барыс)")
    ads_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("🔍 Анализировать ADS файл"):
        with st.spinner("Анализирую ADS файл..."):
            ads_df = analyze_ads_file_structure(ads_file)
    
    st.markdown("---")
    
    # Анализ файла остатков
    st.subheader("🏪 Анализ файла остатков")
    warehouse_file = "/mnt/f/Работа-Никита/Autosort_tovar/ост 22 мая вед.xlsx"
    
    if st.button("🔍 Анализировать файл остатков"):
        with st.spinner("Анализирую файл остатков..."):
            warehouse_df = analyze_warehouse_file_structure(warehouse_file)

if __name__ == "__main__":
    main()