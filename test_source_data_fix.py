#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправления сохранения исходных данных
"""

import streamlit as st
import pandas as pd

def test_source_data_saving():
    """
    Тестирует сохранение исходных данных в process_single_file_safe
    """
    st.header("🔍 Тест сохранения исходных данных")
    
    if st.button("🧪 Тестировать"):
        try:
            # Импортируем функцию
            from integration_patch import process_single_file_safe
            
            # Загружаем реальный файл
            # Поддержка как Linux, так и Windows путей
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            with open(barys_file, 'rb') as f:
                file_content = f.read()
            
            st.info(f"📁 Файл загружен: {len(file_content)} байт")
            
            # Обрабатываем файл
            result = process_single_file_safe(file_content, "барыс - прод с мая24-май25.xlsx", "Алматы_Барыс")
            
            st.subheader("📊 Результат обработки")
            
            if result.get('success'):
                st.success("✅ Обработка успешна")
                
                # Проверяем наличие исходных данных
                if 'source_data' in result:
                    source_data = result['source_data']
                    st.success(f"✅ **Исходные данные сохранены!** Размер: {source_data.shape}")
                    
                    # Проверяем 12-ю колонку
                    if len(source_data.columns) >= 12:
                        col_12_name = source_data.columns[11]
                        st.info(f"💡 12-я колонка: '{col_12_name}'")
                        
                        # Проверяем данные в L4-L10
                        st.write("**Данные в колонке 12 (L4-L10):**")
                        for i in range(3, min(10, len(source_data))):
                            value = source_data.iloc[i, 11]
                            nomenclature = source_data.iloc[i, 1] if len(source_data.columns) > 1 else "N/A"
                            st.write(f"  L{i+1}: {nomenclature} = {value}")
                    else:
                        st.error(f"❌ Недостаточно колонок: {len(source_data.columns)}")
                
                else:
                    st.error("❌ Исходные данные не сохранены в результате")
                
                # Проверяем обработанные данные
                if 'data' in result:
                    processed_data = result['data']
                    st.info(f"📈 Обработанные данные: {processed_data.shape}")
                    
                    # Проверяем цены в обработанных данных
                    if 'last_purchase_price' in processed_data.columns:
                        prices_found = (processed_data['last_purchase_price'] > 0).sum()
                        st.success(f"💰 Цены в обработанных данных: {prices_found}/{len(processed_data)}")
                        
                        if prices_found > 0:
                            avg_price = processed_data[processed_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                            st.write(f"  Средняя цена: {avg_price:,.0f} ₸")
                            
                            # Показываем примеры
                            examples = processed_data[processed_data['last_purchase_price'] > 0].head(3)
                            st.write("  **Примеры:**")
                            for _, row in examples.iterrows():
                                st.write(f"    {row['номенклатура']}: {row['last_purchase_price']:,.0f} ₸")
                    else:
                        st.warning("⚠️ Колонка last_purchase_price не найдена в обработанных данных")
                
                # Показываем статистику
                st.subheader("📈 Статистика")
                for key, value in result.items():
                    if key not in ['data', 'source_data']:
                        st.write(f"**{key}:** {value}")
            
            else:
                st.error(f"❌ Ошибка обработки: {result.get('error', 'Неизвестная ошибка')}")
        
        except Exception as e:
            st.error(f"❌ Ошибка теста: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

def test_price_extraction_from_source():
    """
    Тестирует извлечение цен из сохраненных исходных данных
    """
    st.subheader("🧪 Тест извлечения цен из исходных данных")
    
    if st.button("🔧 Тестировать принудительное извлечение"):
        try:
            # Создаем mock систему с исходными данными
            class MockSystem:
                def __init__(self):
                    # Загружаем файл напрямую
                    # Поддержка как Linux, так и Windows путей
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
                    source_df = pd.read_excel(barys_file)
                    
                    self.multiple_files_data = {
                        'processed_results': {
                            'барыс - прод с мая24-май25.xlsx': {
                                'success': True,
                                'source_data': source_df,  # Исходные данные сохранены!
                                'data': pd.DataFrame()  # Пустые обработанные данные для теста
                            }
                        }
                    }
            
            system = MockSystem()
            st.success("✅ Mock система создана с исходными данными")
            
            # Тестируем принудительное извлечение
            from force_column_12_fix import apply_force_column_12_fix
            
            success = apply_force_column_12_fix(system)
            
            if success:
                st.success("✅ Принудительное извлечение применено!")
            else:
                st.error("❌ Ошибка применения принудительного извлечения")
        
        except Exception as e:
            st.error(f"❌ Ошибка теста: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔧 Тест исправления исходных данных")
    
    st.markdown("""
    **Проблема:** Система не находила исходные данные в файлах для извлечения цен.
    
    **Исправление:** Теперь `process_single_file_safe` сохраняет исходные данные в ключе `source_data`.
    
    **Результат:** Принудительное извлечение цен может работать с реальными Excel данными.
    """)
    
    test_source_data_saving()
    
    st.markdown("---")
    
    test_price_extraction_from_source()