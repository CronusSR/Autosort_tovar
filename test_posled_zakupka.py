#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специальный тест для проверки извлечения цен из колонки "Посл. закупка"
"""

import streamlit as st
import pandas as pd
# ОТКЛЮЧЕНО: from warehouse_price_integration import extract_prices_from_ads_file

def test_posled_zakupka_extraction():
    """
    Тестирует извлечение цен из колонки "Посл. закупка"
    """
    
    st.header("🧪 Тест извлечения цен из колонки 'Посл. закупка'")
    
    # Тестируем на файле Барыс
    barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("🔍 Анализ файла Барыс"):
        with st.spinner("Анализирую файл..."):
            try:
                # Читаем файл
                df = pd.read_excel(barys_file)
                
                st.success(f"📊 Файл загружен: {len(df)} строк, {len(df.columns)} колонок")
                
                # Ищем колонку "Посл. закупка"
                posled_zakupka_col = None
                posled_zakupka_idx = None
                
                for idx, col_name in enumerate(df.columns):
                    col_name_clean = str(col_name).strip().lower()
                    if 'посл' in col_name_clean and 'закуп' in col_name_clean:
                        posled_zakupka_col = col_name
                        posled_zakupka_idx = idx
                        break
                
                if posled_zakupka_col:
                    st.success(f"✅ Найдена колонка 'Посл. закупка': {posled_zakupka_idx + 1} - '{posled_zakupka_col}'")
                    
                    # Анализируем данные в этой колонке
                    col_data = df[posled_zakupka_col]
                    
                    st.subheader("📋 Анализ колонки 'Посл. закупка'")
                    
                    # Показываем первые 15 значений
                    st.write("**Первые 15 значений:**")
                    first_15 = col_data.head(15)
                    for i, val in enumerate(first_15):
                        st.write(f"Строка {i+1}: {val} (тип: {type(val).__name__})")
                    
                    # Анализируем данные с 4-й строки (L4)
                    st.write("**Данные начиная с L4 (строка 4):**")
                    data_from_L4 = col_data.iloc[3:13]  # Строки 4-13
                    
                    numeric_count = 0
                    numeric_values = []
                    
                    for i, val in enumerate(data_from_L4):
                        row_num = i + 4
                        st.write(f"L{row_num}: {val}")
                        
                        if pd.notna(val):
                            try:
                                if isinstance(val, (int, float)) and val > 0:
                                    numeric_count += 1
                                    numeric_values.append(float(val))
                                elif isinstance(val, str):
                                    val_clean = str(val).replace(' ', '').replace(',', '.')
                                    val_clean = ''.join(c for c in val_clean if c.isdigit() or c == '.')
                                    if val_clean:
                                        num_val = float(val_clean)
                                        if num_val > 0:
                                            numeric_count += 1
                                            numeric_values.append(num_val)
                            except:
                                pass
                    
                    st.info(f"📊 Найдено {numeric_count} числовых значений из {len(data_from_L4)}")
                    
                    if numeric_values:
                        st.write(f"Среднее значение: {sum(numeric_values)/len(numeric_values):,.2f}")
                        st.write(f"Минимум: {min(numeric_values):,.2f}")
                        st.write(f"Максимум: {max(numeric_values):,.2f}")
                    
                    # Тестируем извлечение цен
                    st.subheader("💰 Тест извлечения цен")
                    
                    if st.button("🚀 Извлечь цены"):
                        with st.spinner("Извлекаю цены..."):
        # ОТКЛЮЧЕНО: prices_df = extract_prices_from_ads_file(df, "барыс - прод с мая24-май25.xlsx")
                            prices_df = pd.DataFrame()  # Пустой DataFrame для совместимости
                            
                            if not prices_df.empty:
                                items_with_prices = (prices_df['цена'] > 0).sum()
                                
                                st.success(f"✅ Извлечено цен: {items_with_prices} из {len(prices_df)} товаров")
                                
                                # Показываем примеры
                                st.subheader("📋 Примеры извлеченных цен")
                                
                                price_examples = prices_df[prices_df['цена'] > 0].head(10)
                                if not price_examples.empty:
                                    st.dataframe(price_examples[['наименование', 'цена', 'колонка_цены', 'строка_в_файле']])
                                
                                # Статистика
                                if items_with_prices > 0:
                                    avg_price = prices_df[prices_df['цена'] > 0]['цена'].mean()
                                    st.metric("Средняя цена", f"{avg_price:,.0f} ₸")
                            else:
                                st.error("❌ Не удалось извлечь цены")
                
                else:
                    st.error("❌ Колонка 'Посл. закупка' не найдена")
                    
                    # Показываем все колонки для диагностики
                    st.subheader("📋 Все колонки файла")
                    for idx, col_name in enumerate(df.columns):
                        is_12th = " (12-я колонка)" if idx == 11 else ""
                        st.write(f"{idx+1:2d}. {col_name}{is_12th}")
                    
                    # Проверяем 12-ю колонку специально
                    if len(df.columns) >= 12:
                        col_12_name = df.columns[11]
                        st.subheader(f"🎯 Анализ 12-й колонки: '{col_12_name}'")
                        
                        col_12_data = df.iloc[:, 11].iloc[3:13]  # Строки 4-13
                        for i, val in enumerate(col_12_data):
                            row_num = i + 4
                            st.write(f"Строка {row_num}: {val}")
                
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")
                import traceback
                st.text(traceback.format_exc())

if __name__ == "__main__":
    test_posled_zakupka_extraction()