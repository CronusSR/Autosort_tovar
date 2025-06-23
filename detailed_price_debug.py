#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальная диагностика извлечения цен из колонки 12
"""

import streamlit as st
import pandas as pd
import numpy as np

def analyze_column_12_data():
    """
    Детально анализирует данные в колонке 12 файла Барыс
    """
    st.header("🔍 Детальный анализ колонки 12")
    
    # Поддержка как Linux, так и Windows путей
    import os
    if os.name == 'nt':  # Windows
        barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
    else:  # Linux/WSL
        barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("📊 Анализировать данные в колонке 12"):
        try:
            # Читаем файл
            df = pd.read_excel(barys_file)
            st.success(f"✅ Файл загружен: {df.shape}")
            
            # Проверяем колонку 12
            if len(df.columns) < 12:
                st.error(f"❌ В файле только {len(df.columns)} колонок, 12-й нет")
                return
            
            col_12_name = df.columns[11]
            col_12_data = df.iloc[:, 11]
            
            st.info(f"📋 Название 12-й колонки: **'{col_12_name}'**")
            st.info(f"📊 Всего строк в колонке: {len(col_12_data)}")
            
            # Анализируем данные начиная с L4 (строка 4, индекс 3)
            st.subheader("🎯 Анализ данных с L4 (строка 4)")
            
            data_from_L4 = col_12_data.iloc[3:20]  # L4-L20 для анализа
            
            st.write("**Первые 17 значений начиная с L4:**")
            
            valid_prices = []
            analysis_results = []
            
            for i, value in enumerate(data_from_L4):
                row_num = i + 4  # Реальный номер строки
                
                # Получаем номенклатуру для контекста
                nomenclature = df.iloc[i + 3, 1] if len(df.columns) > 1 else "N/A"
                
                # Детальный анализ значения
                analysis = {
                    'row': row_num,
                    'nomenclature': str(nomenclature)[:30],
                    'raw_value': value,
                    'value_type': type(value).__name__,
                    'is_na': pd.isna(value),
                    'converted_price': 0,
                    'conversion_method': 'none',
                    'error': None
                }
                
                if pd.isna(value):
                    analysis['error'] = "Значение пустое (NaN)"
                else:
                    # Пробуем разные способы конвертации
                    
                    # Способ 1: Прямая конвертация числа
                    if isinstance(value, (int, float)):
                        if value > 0:
                            analysis['converted_price'] = float(value)
                            analysis['conversion_method'] = 'direct_number'
                            valid_prices.append(float(value))
                        else:
                            analysis['error'] = f"Число <= 0: {value}"
                    
                    # Способ 2: Конвертация строки
                    elif isinstance(value, str):
                        try:
                            # Простая конвертация
                            price_val = float(value)
                            if price_val > 0:
                                analysis['converted_price'] = price_val
                                analysis['conversion_method'] = 'string_to_float'
                                valid_prices.append(price_val)
                            else:
                                analysis['error'] = f"Строка дает число <= 0: {price_val}"
                        except ValueError:
                            # Очистка строки
                            try:
                                clean_str = str(value).strip()
                                # Убираем пробелы, заменяем запятые на точки
                                clean_str = clean_str.replace(' ', '').replace(',', '.')
                                # Убираем все кроме цифр и точек
                                clean_str = ''.join(c for c in clean_str if c.isdigit() or c == '.')
                                
                                if clean_str:
                                    # Если несколько точек, оставляем только последнюю
                                    if clean_str.count('.') > 1:
                                        parts = clean_str.split('.')
                                        clean_str = ''.join(parts[:-1]) + '.' + parts[-1]
                                    
                                    price_val = float(clean_str)
                                    if price_val > 0:
                                        analysis['converted_price'] = price_val
                                        analysis['conversion_method'] = 'cleaned_string'
                                        valid_prices.append(price_val)
                                    else:
                                        analysis['error'] = f"Очищенная строка дает <= 0: {price_val}"
                                else:
                                    analysis['error'] = f"Строка не содержит цифр: '{value}'"
                            except Exception as e:
                                analysis['error'] = f"Ошибка очистки строки: {str(e)}"
                    else:
                        analysis['error'] = f"Неизвестный тип: {type(value)}"
                
                analysis_results.append(analysis)
                
                # Показываем результат
                if analysis['converted_price'] > 0:
                    st.write(f"✅ L{row_num}: {analysis['nomenclature']} | **{analysis['converted_price']:,.0f} ₸** | {analysis['conversion_method']} | Исходное: {value}")
                else:
                    st.write(f"❌ L{row_num}: {analysis['nomenclature']} | {analysis['error']} | Исходное: {value}")
            
            # Общая статистика
            st.subheader("📈 Результаты анализа")
            
            total_analyzed = len(analysis_results)
            prices_found = len(valid_prices)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Проанализировано строк", total_analyzed)
            
            with col2:
                st.metric("Найдено цен", prices_found)
            
            with col3:
                coverage = (prices_found / total_analyzed * 100) if total_analyzed > 0 else 0
                st.metric("Покрытие", f"{coverage:.1f}%")
            
            if valid_prices:
                st.success(f"✅ **Успешно извлечено {prices_found} цен!**")
                st.write(f"Средняя цена: {np.mean(valid_prices):,.0f} ₸")
                st.write(f"Минимум: {min(valid_prices):,.0f} ₸")
                st.write(f"Максимум: {max(valid_prices):,.0f} ₸")
                
                # Показываем примеры найденных цен
                st.write("**Найденные цены:**")
                price_examples = [r for r in analysis_results if r['converted_price'] > 0][:10]
                for result in price_examples:
                    st.write(f"  {result['nomenclature']}: {result['converted_price']:,.0f} ₸")
            else:
                st.error("❌ **Ни одной цены не извлечено!**")
                
                # Анализируем причины
                st.write("**Анализ ошибок:**")
                error_counts = {}
                for result in analysis_results:
                    if result['error']:
                        error_type = result['error'].split(':')[0] if ':' in result['error'] else result['error']
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                for error, count in error_counts.items():
                    st.write(f"  {error}: {count} случаев")
            
            # Показываем типы данных в колонке
            st.subheader("🔍 Анализ типов данных")
            
            type_counts = {}
            for result in analysis_results:
                vtype = result['value_type']
                type_counts[vtype] = type_counts.get(vtype, 0) + 1
            
            for vtype, count in type_counts.items():
                st.write(f"**{vtype}:** {count} значений")
            
            # Детальная таблица для анализа
            if st.checkbox("📋 Показать детальную таблицу"):
                df_analysis = pd.DataFrame(analysis_results)
                st.dataframe(df_analysis, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

def test_integration_patch_extraction():
    """
    Тестирует точно ту же логику, что используется в integration_patch.py
    """
    st.subheader("🧪 Тест логики integration_patch.py")
    
    if st.button("🔧 Тестировать extraction как в integration_patch"):
        try:
            # Читаем файл точно как в integration_patch
            # Поддержка как Linux, так и Windows путей
    import os
    if os.name == 'nt':  # Windows
        barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
    else:  # Linux/WSL
        barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            with open(barys_file, 'rb') as f:
                file_content = f.read()
            
            # Имитируем точную логику из process_single_file_safe
            import io
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # Параметры точно как в коде
            start_col_index = 12  # M
            end_col_index = 28    # AB
            start_row = 3         # Строка 4
            nomenclature_col = 1  # B
            price_col = 11        # L (12-я колонка, индекс 11)
            
            st.info(f"📊 Файл: {df.shape}, price_col={price_col}")
            
            # Получаем номенклатуру точно как в коде
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
            nomenclature_clean = nomenclature_data.dropna()
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            
            # Исключаем последнюю строку
            if len(nomenclature_clean) > 0:
                nomenclature_clean = nomenclature_clean[:-1]
            
            st.success(f"✅ Номенклатура: {len(nomenclature_clean)} товаров")
            
            # Извлекаем цены точно как в коде
            prices_found = 0
            price_examples = []
            
            for i, idx in enumerate(nomenclature_clean.index[:15]):  # Первые 15 для теста
                item_name = str(nomenclature_clean.loc[idx]).strip()
                
                # Извлекаем цену точно как в integration_patch
                price_value = 0
                if df.shape[1] > price_col:
                    try:
                        price_raw = df.iloc[idx, price_col]
                        st.write(f"Строка {idx}: {item_name[:30]} | Сырая цена: {price_raw} (тип: {type(price_raw)})")
                        
                        if pd.notna(price_raw):
                            price_value = float(price_raw)
                            if price_value > 0:
                                prices_found += 1
                                price_examples.append((item_name, price_value))
                                st.write(f"  ✅ Конвертировано: {price_value:,.0f} ₸")
                            else:
                                st.write(f"  ❌ Цена <= 0: {price_value}")
                        else:
                            st.write(f"  ❌ Значение пустое")
                    except (ValueError, TypeError) as e:
                        st.write(f"  ❌ Ошибка конвертации: {str(e)}")
                        price_value = 0
            
            st.markdown("---")
            if prices_found > 0:
                st.success(f"🎉 **Найдено {prices_found} цен из первых 15 товаров!**")
                st.write("**Примеры:**")
                for name, price in price_examples[:5]:
                    st.write(f"  {name}: {price:,.0f} ₸")
            else:
                st.error("❌ **Ни одной цены не найдено!**")
                st.write("Проблема в логике конвертации данных из колонки 12")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔍 Детальная диагностика извлечения цен")
    
    st.markdown("""
    **Проблема:** Система находит колонку 12, но не может извлечь ценовые данные.
    
    **Цель:** Понять что именно содержится в колонке 12 и почему цены не извлекаются.
    """)
    
    analyze_column_12_data()
    
    st.markdown("---")
    
    test_integration_patch_extraction()