#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправленного извлечения цен
"""

import streamlit as st
import pandas as pd
# ОТКЛЮЧЕНО: from warehouse_price_integration import extract_prices_from_ads_file, determine_branch_from_filename

def test_price_extraction():
    """
    Тестирует исправленное извлечение цен
    """
    
    st.header("🧪 Тест исправленного извлечения цен")
    
    # Тест определения филиала
    st.subheader("🏪 Тест определения филиала")
    
    test_filenames = [
        "барыс - прод с мая24-май25.xlsx",
        "казыбаева продажи.xlsx", 
        "база комплект данные.xlsx",
        "шымкент овощная продажи.xlsx",
        "астана магазин.xlsx"
    ]
    
    for filename in test_filenames:
        branch = determine_branch_from_filename(filename)
        st.write(f"📁 {filename} → {branch}")
    
    # Тест извлечения цен из файла Барыс
    st.subheader("💰 Тест извлечения цен из файла Барыс")
    
    barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("🔍 Тест извлечения цен"):
        with st.spinner("Извлекаю цены из файла Барыс..."):
            try:
                # Читаем файл
                df = pd.read_excel(barys_file)
                
                # Показываем базовую информацию
                st.info(f"📊 Файл: {len(df)} строк, {len(df.columns)} колонок")
                
                # Показываем первые строки
                with st.expander("👀 Первые строки файла"):
                    st.dataframe(df.head(10))
                
                # Показываем названия колонок
                with st.expander("📋 Названия колонок"):
                    for i, col in enumerate(df.columns):
                        st.write(f"{i+1:2d}. {col}")
                
                # Тестируем извлечение цен
        # ОТКЛЮЧЕНО: prices_df = extract_prices_from_ads_file(df, "барыс - прод с мая24-май25.xlsx")
                prices_df = pd.DataFrame()  # Пустой DataFrame для совместимости
                
                if not prices_df.empty:
                    # Показываем статистику
                    items_with_prices = (prices_df['цена'] > 0).sum()
                    total_items = len(prices_df)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Всего товаров", total_items)
                    with col2:
                        st.metric("С ценами", items_with_prices)
                    with col3:
                        coverage = (items_with_prices / total_items * 100) if total_items > 0 else 0
                        st.metric("Покрытие", f"{coverage:.1f}%")
                    with col4:
                        if items_with_prices > 0:
                            avg_price = prices_df[prices_df['цена'] > 0]['цена'].mean()
                            st.metric("Средняя цена", f"{avg_price:,.0f} ₸")
                    
                    # Показываем примеры извлеченных цен
                    st.subheader("📋 Примеры извлеченных цен")
                    
                    # Товары с ценами
                    items_with_prices_df = prices_df[prices_df['цена'] > 0].head(10)
                    if not items_with_prices_df.empty:
                        st.write("**Товары с ценами:**")
                        st.dataframe(items_with_prices_df[['наименование', 'цена', 'филиал', 'колонка_цены']])
                    
                    # Товары без цен
                    items_without_prices_df = prices_df[prices_df['цена'] == 0].head(5)
                    if not items_without_prices_df.empty:
                        st.write("**Товары без цен:**")
                        st.dataframe(items_without_prices_df[['наименование', 'цена', 'филиал', 'колонка_цены']])
                    
                    st.success("✅ Извлечение цен работает!")
                    
                else:
                    st.error("❌ Не удалось извлечь цены")
                    
            except Exception as e:
                st.error(f"❌ Ошибка тестирования: {str(e)}")
                import traceback
                st.text(traceback.format_exc())

if __name__ == "__main__":
    test_price_extraction()