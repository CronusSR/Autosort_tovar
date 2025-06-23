#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск файла Барыс и быстрая проверка колонки 12
"""

import pandas as pd
import streamlit as st
import os
import glob

def find_barys_file():
    """Найти файл Барыс в разных местах"""
    
    # Возможные пути к файлу
    possible_paths = [
        # Windows пути
        r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx",
        r"F:\Работа-Никита\Autosort_tovar\барыс*.xlsx", 
        r".\барыс - прод с мая24-май25.xlsx",
        r".\барыс*.xlsx",
        # Linux пути
        "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx",
        "/mnt/f/Работа-Никита/Autosort_tovar/барыс*.xlsx"
    ]
    
    st.header("🔍 Поиск файла Барыс")
    
    found_files = []
    
    # Поиск по точным путям
    for path in possible_paths:
        if '*' not in path:
            if os.path.exists(path):
                found_files.append(path)
                st.success(f"✅ Найден: {path}")
        else:
            # Поиск по маске
            try:
                matches = glob.glob(path)
                for match in matches:
                    if 'барыс' in match.lower():
                        found_files.append(match)
                        st.success(f"✅ Найден: {match}")
            except:
                pass
    
    # Поиск в текущей директории
    try:
        current_dir_files = glob.glob("*барыс*.xlsx")
        for file in current_dir_files:
            if file not in found_files:
                found_files.append(file)
                st.success(f"✅ Найден в текущей папке: {file}")
    except:
        pass
    
    if not found_files:
        st.error("❌ Файл Барыс не найден!")
        st.write("🔍 Попробуйте:")
        st.write("1. Загрузить файл через интерфейс ниже")
        st.write("2. Проверить что файл находится в папке с проектом")
        st.write("3. Использовать загрузку файла")
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "📁 Загрузите файл Барыс",
            type=['xlsx', 'xls'],
            help="Выберите файл 'барыс - прод с мая24-май25.xlsx'"
        )
        
        if uploaded_file is not None:
            return analyze_uploaded_file(uploaded_file)
    else:
        st.write(f"**Найдено файлов: {len(found_files)}**")
        
        # Позволяем выбрать файл
        if len(found_files) == 1:
            selected_file = found_files[0]
        else:
            selected_file = st.selectbox("Выберите файл для анализа:", found_files)
        
        if st.button("📊 Анализировать выбранный файл"):
            return analyze_file(selected_file)
    
    return None

def analyze_file(file_path):
    """Анализирует файл по пути"""
    try:
        st.info(f"📁 Анализирую файл: {file_path}")
        
        df = pd.read_excel(file_path)
        st.success(f"✅ Файл загружен: {df.shape}")
        
        return analyze_dataframe(df)
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки файла: {str(e)}")
        return None

def analyze_uploaded_file(uploaded_file):
    """Анализирует загруженный файл"""
    try:
        st.info(f"📁 Анализирую загруженный файл: {uploaded_file.name}")
        
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Файл загружен: {df.shape}")
        
        return analyze_dataframe(df)
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки файла: {str(e)}")
        return None

def analyze_dataframe(df):
    """Анализирует DataFrame"""
    st.subheader("📊 Анализ колонки 12")
    
    if len(df.columns) < 12:
        st.error(f"❌ В файле только {len(df.columns)} колонок, 12-й нет")
        return None
    
    # Колонка 12 (индекс 11)
    col_12_name = df.columns[11]
    st.info(f"📋 Название 12-й колонки: **'{col_12_name}'**")
    
    # Анализируем данные с L4 (строка 4, индекс 3)
    st.write("🎯 **Данные в колонке 12, начиная с L4:**")
    
    prices_found = 0
    total_checked = 0
    
    for i in range(3, min(15, len(df))):  # L4-L15
        row_num = i + 1
        nomenclature = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
        value = df.iloc[i, 11]  # Колонка 12
        
        # Проверяем можно ли извлечь цену
        price_extracted = False
        extracted_price = 0
        
        if pd.notna(value):
            try:
                extracted_price = float(value)
                if extracted_price > 0:
                    price_extracted = True
                    prices_found += 1
            except:
                # Пробуем очистить строку
                try:
                    clean_str = str(value).replace(',', '.').replace(' ', '')
                    clean_str = ''.join(c for c in clean_str if c.isdigit() or c == '.')
                    if clean_str:
                        extracted_price = float(clean_str)
                        if extracted_price > 0:
                            price_extracted = True
                            prices_found += 1
                except:
                    pass
        
        total_checked += 1
        
        status = "✅" if price_extracted else "❌"
        price_display = f"{extracted_price:,.0f} ₸" if price_extracted else "Не извлечено"
        
        st.write(f"{status} L{row_num}: {str(nomenclature)[:25]:25} | Значение: {str(value)[:15]:15} | Цена: {price_display}")
    
    # Итоговая статистика
    st.subheader("📈 Результат")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Проверено строк", total_checked)
    
    with col2:
        st.metric("Извлечено цен", prices_found)
    
    with col3:
        coverage = (prices_found / total_checked * 100) if total_checked > 0 else 0
        st.metric("Успешность", f"{coverage:.1f}%")
    
    if prices_found > 0:
        st.success(f"🎉 **Цены извлекаются успешно!** Найдено {prices_found} из {total_checked}")
        st.info("✅ Логика извлечения цен должна работать в основной системе")
    else:
        st.error("❌ **Цены не извлекаются!**")
        st.write("🔍 **Возможные причины:**")
        st.write("1. Цены находятся в другой колонке")
        st.write("2. Данные имеют нестандартный формат")
        st.write("3. Цены начинаются не с L4")
        
        # Поиск цен в других колонках
        st.write("\n🔍 **Поиск колонок с ценами:**")
        for col_idx in range(min(15, len(df.columns))):
            col_name = df.columns[col_idx]
            col_name_lower = str(col_name).lower()
            if any(word in col_name_lower for word in ['цена', 'price', 'стоимость', 'закуп', 'посл']):
                st.write(f"   Колонка {col_idx+1} ({chr(65+col_idx)}): **'{col_name}'** - возможно содержит цены")
    
    return df

if __name__ == "__main__":
    st.title("🔍 Поиск и анализ файла Барыс")
    
    st.markdown("""
    **Цель:** Найти файл Барыс и проверить данные в колонке 12.
    
    **Проверяем:**
    - Существует ли файл
    - Что находится в колонке 12
    - Можно ли извлечь цены из колонки 12
    """)
    
    find_barys_file()