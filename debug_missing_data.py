#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка проблемы "не найдены исходные данные в файлах"
"""

import streamlit as st
import pandas as pd
import io

def debug_multiple_files_data(system):
    """
    Отлаживает структуру данных множественных файлов
    """
    st.header("🔍 Отладка множественных файлов")
    
    if not hasattr(system, 'multiple_files_data'):
        st.error("❌ У системы нет атрибута multiple_files_data")
        return
    
    if not system.multiple_files_data:
        st.error("❌ multiple_files_data пуст")
        return
    
    st.success(f"✅ multiple_files_data найден")
    
    # Показываем структуру
    st.subheader("📊 Структура multiple_files_data")
    
    for key, value in system.multiple_files_data.items():
        st.write(f"**{key}:** {type(value)} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
    
    # Проверяем processed_results
    processed_results = system.multiple_files_data.get('processed_results', {})
    
    if not processed_results:
        st.error("❌ processed_results пуст")
        return
    
    st.success(f"✅ processed_results найден: {len(processed_results)} файлов")
    
    # Анализируем каждый файл
    st.subheader("📁 Анализ файлов в processed_results")
    
    for filename, file_data in processed_results.items():
        st.write(f"\n**📄 Файл: {filename}**")
        
        if isinstance(file_data, dict):
            st.write("   Это словарь с ключами:")
            for key in file_data.keys():
                value = file_data[key]
                if hasattr(value, 'shape'):
                    st.write(f"     - {key}: DataFrame {value.shape}")
                elif hasattr(value, '__len__'):
                    st.write(f"     - {key}: {type(value)} длина {len(value)}")
                else:
                    st.write(f"     - {key}: {type(value)}")
            
            # Ищем исходные данные
            st.write("   🔍 Поиск исходных данных:")
            source_data = None
            
            # Проверяем разные ключи
            for key in ['source_data', 'raw_data', 'original_data', 'data']:
                if key in file_data and file_data[key] is not None:
                    source_data = file_data[key]
                    st.write(f"     ✅ Найдено в '{key}': {type(source_data)}")
                    if hasattr(source_data, 'shape'):
                        st.write(f"       Размер: {source_data.shape}")
                        if hasattr(source_data, 'columns'):
                            st.write(f"       Колонки: {len(source_data.columns)}")
                            if len(source_data.columns) >= 12:
                                col_12_name = source_data.columns[11]
                                st.write(f"       12-я колонка: '{col_12_name}'")
                    break
                else:
                    st.write(f"     ❌ Нет в '{key}'")
            
            if source_data is None:
                st.write("     ⚠️ Исходные данные не найдены, ищем в обработанных...")
                for key in ['calculated_ads', 'result', 'processed_data']:
                    if key in file_data and file_data[key] is not None:
                        data = file_data[key]
                        if hasattr(data, 'shape'):
                            st.write(f"     📊 Есть '{key}': {data.shape}")
                            if hasattr(data, 'columns'):
                                cols_with_price = [col for col in data.columns if 'price' in str(col).lower() or 'цена' in str(col).lower() or 'закуп' in str(col).lower()]
                                if cols_with_price:
                                    st.write(f"       💰 Колонки с ценами: {cols_with_price}")
                                else:
                                    st.write("       ❌ Колонки с ценами не найдены")
        
        elif hasattr(file_data, 'shape'):
            st.write(f"   Это DataFrame: {file_data.shape}")
            if hasattr(file_data, 'columns'):
                st.write(f"   Колонки: {len(file_data.columns)}")
                if len(file_data.columns) >= 12:
                    col_12_name = file_data.columns[11]
                    st.write(f"   12-я колонка: '{col_12_name}'")
        else:
            st.write(f"   Неизвестный тип: {type(file_data)}")

def test_process_single_file():
    """
    Тестирует process_single_file_safe на реальном файле
    """
    st.subheader("🧪 Тест process_single_file_safe")
    
    barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    try:
        # Читаем файл как байты (как делает система)
        with open(barys_file, 'rb') as f:
            file_content = f.read()
        
        st.write(f"📁 Файл загружен: {len(file_content)} байт")
        
        # Импортируем и тестируем функцию
        from integration_patch import process_single_file_safe
        
        result = process_single_file_safe(file_content, "барыс - прод с мая24-май25.xlsx", "Алматы_Барыс")
        
        st.write("📊 Результат process_single_file_safe:")
        st.json(result)
        
        if result.get('success'):
            data = result.get('data')
            if data is not None and hasattr(data, 'shape'):
                st.success(f"✅ Данные извлечены: {data.shape}")
                
                # Проверяем цены
                if 'last_purchase_price' in data.columns:
                    prices_found = (data['last_purchase_price'] > 0).sum()
                    st.success(f"💰 Цены найдены: {prices_found}/{len(data)}")
                    
                    if prices_found > 0:
                        st.write("Примеры цен:")
                        price_examples = data[data['last_purchase_price'] > 0].head(5)
                        for _, row in price_examples.iterrows():
                            st.write(f"  {row['номенклатура']}: {row['last_purchase_price']:,.0f} ₸")
                else:
                    st.warning("⚠️ Колонка last_purchase_price не найдена")
        else:
            st.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
    
    except Exception as e:
        st.error(f"❌ Ошибка тестирования: {str(e)}")
        import traceback
        st.text(traceback.format_exc())

def main():
    st.title("🔍 Отладка проблемы с исходными данными")
    
    # Создаем mock system для тестирования
    class MockSystem:
        def __init__(self):
            self.multiple_files_data = None
    
    system = MockSystem()
    
    if st.button("🧪 Тест process_single_file_safe"):
        test_process_single_file()
    
    st.markdown("---")
    st.write("Для полной отладки загрузите файлы через 'Множественный анализ'")

if __name__ == "__main__":
    main()