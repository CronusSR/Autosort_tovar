#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка полного потока обработки файлов в системе
"""

import streamlit as st
import pandas as pd
import io

def debug_full_system_flow():
    """
    Отлаживает полный поток от загрузки файла до извлечения цен
    """
    st.header("🔍 Отладка полного потока системы")
    
    st.markdown("""
    **Проблема:** Файл анализируется успешно отдельно, но система пишет "не удалось извлечь ценовые данные"
    
    **Цель:** Найти где именно в системе происходит сбой
    """)
    
    if st.button("🧪 Тестировать полный поток"):
        try:
            # Шаг 1: Загружаем файл как в реальной системе
            st.subheader("📁 Шаг 1: Загрузка файла")
            
            # Получаем путь к файлу
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            with open(barys_file, 'rb') as f:
                file_content = f.read()
            
            st.success(f"✅ Файл загружен: {len(file_content)} байт")
            
            # Шаг 2: Тестируем integration_patch.process_single_file_safe
            st.subheader("🔧 Шаг 2: Тест integration_patch.process_single_file_safe")
            
            from integration_patch import process_single_file_safe
            
            result = process_single_file_safe(file_content, "барыс - прод с мая24-май25.xlsx", "Алматы_Барыс")
            
            st.write("📊 **Результат process_single_file_safe:**")
            if result.get('success'):
                st.success("✅ process_single_file_safe выполнен успешно")
                
                # Проверяем что именно вернулось
                st.write(f"   📈 Товаров обработано: {result.get('total_items', 'N/A')}")
                st.write(f"   💰 Цен найдено: {result.get('prices_found', 'N/A')}")
                st.write(f"   📊 Покрытие: {result.get('price_coverage', 'N/A'):.1f}%")
                
                # Проверяем структуру данных
                if 'data' in result:
                    data = result['data']
                    st.write(f"   📋 Обработанные данные: {data.shape}")
                    
                    if 'last_purchase_price' in data.columns:
                        prices_in_data = (data['last_purchase_price'] > 0).sum()
                        st.success(f"   ✅ В обработанных данных есть цены: {prices_in_data}/{len(data)}")
                        
                        # Показываем примеры
                        if prices_in_data > 0:
                            st.write("   **Примеры найденных цен:**")
                            examples = data[data['last_purchase_price'] > 0].head(3)
                            for _, row in examples.iterrows():
                                st.write(f"     {row['номенклатура']}: {row['last_purchase_price']:,.0f} ₸")
                    else:
                        st.error("   ❌ В обработанных данных НЕТ колонки last_purchase_price")
                
                # Проверяем исходные данные
                if 'source_data' in result:
                    source_data = result['source_data']
                    st.success(f"   ✅ Исходные данные сохранены: {source_data.shape}")
                else:
                    st.error("   ❌ Исходные данные НЕ сохранены")
                
            else:
                st.error(f"❌ process_single_file_safe FAILED: {result.get('error', 'Неизвестная ошибка')}")
                return
            
            # Шаг 3: Симулируем сохранение в system.multiple_files_data
            st.subheader("💾 Шаг 3: Симуляция сохранения в систему")
            
            # Создаем mock системы
            class MockSystem:
                def __init__(self):
                    self.multiple_files_data = {
                        'processed_results': {
                            'барыс - прод с мая24-май25.xlsx': result
                        }
                    }
            
            mock_system = MockSystem()
            st.success("✅ Mock система создана с результатами")
            
            # Шаг 4: Тестируем force_column_12_fix
            st.subheader("🔧 Шаг 4: Тест force_column_12_fix")
            
            # Проверяем что видит force_column_12_fix
            processed_results = mock_system.multiple_files_data.get('processed_results', {})
            
            if processed_results:
                st.write("📋 **Что видит force_column_12_fix:**")
                
                for filename, file_data in processed_results.items():
                    st.write(f"   📄 Файл: {filename}")
                    
                    if isinstance(file_data, dict):
                        st.write("     📊 Структура данных:")
                        for key in file_data.keys():
                            value = file_data[key]
                            if hasattr(value, 'shape'):
                                st.write(f"       {key}: DataFrame {value.shape}")
                            else:
                                st.write(f"       {key}: {type(value)}")
                        
                        # Ищем исходные данные
                        source_data = None
                        if 'source_data' in file_data and file_data['source_data'] is not None:
                            source_data = file_data['source_data']
                            st.success(f"     ✅ source_data найден: {source_data.shape}")
                            
                            # Проверяем колонку 12
                            if len(source_data.columns) >= 12:
                                col_12_name = source_data.columns[11]
                                st.write(f"       12-я колонка: '{col_12_name}'")
                                
                                # Тестируем извлечение цен из source_data
                                st.write("     🧪 **Тест извлечения цен из source_data:**")
                                
                                test_prices = []
                                for i in range(3, min(8, len(source_data))):  # L4-L8
                                    try:
                                        nomenclature = source_data.iloc[i, 1]
                                        price_raw = source_data.iloc[i, 11]
                                        
                                        if pd.notna(price_raw):
                                            price_value = float(price_raw)
                                            if price_value > 0:
                                                test_prices.append((nomenclature, price_value))
                                    except:
                                        pass
                                
                                if test_prices:
                                    st.success(f"       ✅ Извлечено {len(test_prices)} тестовых цен")
                                    for name, price in test_prices[:3]:
                                        st.write(f"         {name}: {price:,.0f} ₸")
                                else:
                                    st.error("       ❌ Не удалось извлечь тестовые цены")
                            else:
                                st.error(f"       ❌ Недостаточно колонок в source_data: {len(source_data.columns)}")
                        else:
                            st.error("     ❌ source_data НЕ найден")
            
            # Шаг 5: Тестируем get_prices_for_warehouse_analysis
            st.subheader("🏢 Шаг 5: Тест get_prices_for_warehouse_analysis")
            
            from simple_price_add import get_prices_for_warehouse_analysis
            
            prices_dict = get_prices_for_warehouse_analysis(mock_system)
            
            if prices_dict:
                st.success(f"✅ get_prices_for_warehouse_analysis нашел {len(prices_dict)} цен")
                
                # Показываем примеры
                st.write("**Примеры цен:**")
                for i, (name, price) in enumerate(list(prices_dict.items())[:5]):
                    st.write(f"  {name}: {price:,.0f} ₸")
            else:
                st.error("❌ get_prices_for_warehouse_analysis НЕ нашел цены")
                
                # Диагностика почему не нашел
                st.write("🔍 **Диагностика проблемы:**")
                
                # Проверяем calculated_ads
                if hasattr(mock_system, 'calculated_ads'):
                    st.write("   ✅ У системы есть calculated_ads")
                else:
                    st.write("   ❌ У системы НЕТ calculated_ads")
                
                # Проверяем multiple_files_data
                if hasattr(mock_system, 'multiple_files_data'):
                    st.write("   ✅ У системы есть multiple_files_data")
                    
                    combined_data = mock_system.multiple_files_data.get('combined_data')
                    if combined_data is not None:
                        st.write("   ✅ Есть combined_data")
                        if 'last_purchase_price' in combined_data.columns:
                            st.write("   ✅ В combined_data есть last_purchase_price")
                        else:
                            st.write("   ❌ В combined_data НЕТ last_purchase_price")
                    else:
                        st.write("   ❌ НЕТ combined_data - нужно запустить combine_data_safe")
                        
                        # Попробуем запустить combine_data_safe
                        st.write("   🔧 Пробуем запустить combine_data_safe...")
                        
                        from integration_patch import combine_data_safe
                        combine_data_safe(mock_system)
                        
                        # Проверяем еще раз
                        prices_dict_after = get_prices_for_warehouse_analysis(mock_system)
                        if prices_dict_after:
                            st.success(f"   ✅ После combine_data_safe найдено {len(prices_dict_after)} цен!")
                        else:
                            st.error("   ❌ Даже после combine_data_safe цены не найдены")
                else:
                    st.write("   ❌ У системы НЕТ multiple_files_data")
            
            # Итоговый диагноз
            st.subheader("🎯 Итоговый диагноз")
            
            if prices_dict or 'prices_dict_after' in locals() and prices_dict_after:
                st.success("🎉 **СИСТЕМА РАБОТАЕТ!** Цены извлекаются корректно")
                st.info("💡 Возможно проблема была в том, что не запускался combine_data_safe после обработки файлов")
            else:
                st.error("🚨 **НАЙДЕНА ПРОБЛЕМА!** Где-то в цепочке цены теряются")
                st.write("🔍 **Следующие шаги для исправления:**")
                st.write("1. Проверить что combine_data_safe вызывается после обработки файлов")
                st.write("2. Убедиться что last_purchase_price правильно агрегируется")
                st.write("3. Проверить логику в get_prices_for_warehouse_analysis")
        
        except Exception as e:
            st.error(f"❌ Ошибка отладки: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔍 Отладка полного потока системы")
    
    debug_full_system_flow()