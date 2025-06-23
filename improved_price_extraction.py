#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная функция извлечения цен с детальной диагностикой
"""

import pandas as pd
import streamlit as st
import io

def improved_process_single_file_safe(file_content: bytes, filename: str, branch_name: str, show_debug=True) -> dict:
    """
    Улучшенная версия process_single_file_safe с детальной диагностикой
    """
    try:
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
        if show_debug:
            st.info(f"📁 Обрабатываю файл: {filename}")
            st.write(f"   Размер: {df.shape}")
        
        # Параметры обработки
        start_col_index = 12  # M
        end_col_index = 28    # AB
        start_row = 3         # Строка 4
        nomenclature_col = 1  # B
        price_col = 11        # L (12-я колонка, индекс 11)
        
        # Проверки
        if df.shape[1] < end_col_index:
            return {'success': False, 'error': f'Недостаточно колонок: {df.shape[1]} < {end_col_index}'}
        
        if df.shape[0] <= start_row:
            return {'success': False, 'error': f'Недостаточно строк: {df.shape[0]} <= {start_row}'}
        
        if show_debug:
            col_12_name = df.columns[11] if len(df.columns) > 11 else "НЕТ"
            st.write(f"   12-я колонка (L): '{col_12_name}'")
        
        # Получаем номенклатуру
        nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
        nomenclature_clean = nomenclature_data.dropna()
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
        
        # Исключаем последнюю строку
        if len(nomenclature_clean) > 0:
            nomenclature_clean = nomenclature_clean[:-1]
        
        if len(nomenclature_clean) == 0:
            return {'success': False, 'error': 'Нет валидных товаров'}
        
        if show_debug:
            st.write(f"   Номенклатура: {len(nomenclature_clean)} товаров")
        
        # Обрабатываем данные с детальной диагностикой цен
        sales_data = []
        prices_found = 0
        price_errors = []
        price_debug_info = []
        
        for idx in nomenclature_clean.index:
            try:
                item_name = str(nomenclature_clean.loc[idx]).strip()
                row_sales = df.iloc[idx, start_col_index:end_col_index].copy()
                row_numeric = pd.to_numeric(row_sales, errors='coerce').fillna(0)
                
                # УЛУЧШЕННОЕ извлечение цены с диагностикой
                price_value = 0
                price_debug = {
                    'row': idx,
                    'item': item_name[:30],
                    'raw_value': None,
                    'value_type': None,
                    'conversion_result': 0,
                    'error': None
                }
                
                if df.shape[1] > price_col:
                    try:
                        price_raw = df.iloc[idx, price_col]
                        price_debug['raw_value'] = price_raw
                        price_debug['value_type'] = type(price_raw).__name__
                        
                        if pd.notna(price_raw):
                            # Способ 1: Прямая конвертация
                            if isinstance(price_raw, (int, float)):
                                price_value = float(price_raw)
                                price_debug['conversion_result'] = price_value
                                
                                if price_value > 0:
                                    prices_found += 1
                                else:
                                    price_debug['error'] = f"Число <= 0: {price_value}"
                                    price_value = 0
                            
                            # Способ 2: Конвертация строки
                            elif isinstance(price_raw, str):
                                # Простая конвертация
                                try:
                                    price_value = float(price_raw.strip())
                                    price_debug['conversion_result'] = price_value
                                    
                                    if price_value > 0:
                                        prices_found += 1
                                    else:
                                        price_debug['error'] = f"Строка дает <= 0: {price_value}"
                                        price_value = 0
                                        
                                except ValueError:
                                    # Продвинутая очистка строки
                                    try:
                                        clean_str = str(price_raw).strip()
                                        # Заменяем запятые на точки
                                        clean_str = clean_str.replace(',', '.')
                                        # Убираем пробелы
                                        clean_str = clean_str.replace(' ', '')
                                        # Убираем все кроме цифр и точек
                                        clean_str = ''.join(c for c in clean_str if c.isdigit() or c == '.')
                                        
                                        if clean_str:
                                            # Если несколько точек, оставляем только последнюю
                                            if clean_str.count('.') > 1:
                                                parts = clean_str.split('.')
                                                clean_str = ''.join(parts[:-1]) + '.' + parts[-1]
                                            
                                            price_value = float(clean_str)
                                            price_debug['conversion_result'] = price_value
                                            
                                            if price_value > 0:
                                                prices_found += 1
                                            else:
                                                price_debug['error'] = f"Очищенная строка <= 0: {price_value}"
                                                price_value = 0
                                        else:
                                            price_debug['error'] = f"Строка не содержит цифр: '{price_raw}'"
                                    except Exception as e:
                                        price_debug['error'] = f"Ошибка очистки: {str(e)}"
                            else:
                                price_debug['error'] = f"Неподдерживаемый тип: {type(price_raw)}"
                        else:
                            price_debug['error'] = "Значение пустое (NaN)"
                    
                    except Exception as e:
                        price_debug['error'] = f"Общая ошибка: {str(e)}"
                        price_errors.append(f"Строка {idx}: {str(e)}")
                        price_value = 0
                else:
                    price_debug['error'] = f"Колонка {price_col} не существует"
                
                price_debug_info.append(price_debug)
                
                average_value = row_numeric.mean()
                ads_value = average_value / 30
                
                sales_data.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_numeric.sum(),
                    'last_purchase_price': price_value,
                    'branch': branch_name,
                    'source_file': filename
                })
                
            except Exception as e:
                price_errors.append(f"Общая ошибка обработки строки {idx}: {str(e)}")
                continue
        
        if not sales_data:
            return {'success': False, 'error': 'Не удалось обработать данные'}
        
        result_df = pd.DataFrame(sales_data)
        
        # Диагностическая информация
        if show_debug:
            st.write(f"   🎯 Результат извлечения цен:")
            st.write(f"      Обработано товаров: {len(sales_data)}")
            st.write(f"      Найдено цен: {prices_found}")
            st.write(f"      Покрытие: {prices_found/len(sales_data)*100:.1f}%" if sales_data else "0%")
            
            if prices_found == 0 and show_debug:
                st.error("❌ Ни одной цены не извлечено!")
                
                # Показываем примеры ошибок
                if price_debug_info:
                    st.write("🔍 Анализ первых 5 строк:")
                    for debug in price_debug_info[:5]:
                        st.write(f"   Строка {debug['row']}: {debug['item']} | "
                               f"Тип: {debug['value_type']} | "
                               f"Значение: {debug['raw_value']} | "
                               f"Ошибка: {debug['error']}")
                
                if price_errors:
                    st.write("❌ Ошибки обработки:")
                    for error in price_errors[:3]:
                        st.write(f"   {error}")
            
            elif prices_found > 0:
                st.success(f"✅ Найдено {prices_found} цен!")
                # Показываем примеры успешных извлечений
                successful_prices = [d for d in price_debug_info if d['conversion_result'] > 0][:3]
                if successful_prices:
                    st.write("💰 Примеры найденных цен:")
                    for debug in successful_prices:
                        st.write(f"   {debug['item']}: {debug['conversion_result']:,.0f} ₸")
        
        return {
            'success': True,
            'total_items': len(result_df),
            'total_ads': result_df['ads'].sum(),
            'average_ads': result_df['ads'].mean(),
            'prices_found': prices_found,
            'price_coverage': (prices_found / len(result_df) * 100) if len(result_df) > 0 else 0,
            'data': result_df,
            'source_data': df,
            'branch_name': branch_name,
            'price_debug_info': price_debug_info,  # Диагностическая информация
            'price_errors': price_errors
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Ошибка: {str(e)}'}

def test_improved_extraction():
    """Тестирует улучшенную функцию извлечения"""
    st.header("🧪 Тест улучшенной функции извлечения цен")
    
    if st.button("🔬 Тестировать улучшенную версию"):
        try:
            # Поддержка как Linux, так и Windows путей
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            with open(barys_file, 'rb') as f:
                file_content = f.read()
            
            result = improved_process_single_file_safe(
                file_content, 
                "барыс - прод с мая24-май25.xlsx", 
                "Алматы_Барыс",
                show_debug=True
            )
            
            st.subheader("📊 Результат тестирования")
            
            if result['success']:
                st.success("✅ Обработка завершена успешно")
                
                # Основная статистика
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Товаров", result['total_items'])
                with col2:
                    st.metric("Цен найдено", result['prices_found'])
                with col3:
                    st.metric("Покрытие", f"{result['price_coverage']:.1f}%")
                
                # Диагностическая информация
                if 'price_debug_info' in result and st.checkbox("🔍 Показать детальную диагностику"):
                    debug_df = pd.DataFrame(result['price_debug_info'])
                    st.dataframe(debug_df, use_container_width=True)
                
                if result['prices_found'] == 0:
                    st.error("🚨 ПРОБЛЕМА: Цены не извлекаются!")
                    
                    if 'price_errors' in result and result['price_errors']:
                        st.write("❌ Ошибки:")
                        for error in result['price_errors'][:5]:
                            st.write(f"  {error}")
                
            else:
                st.error(f"❌ Ошибка: {result['error']}")
        
        except Exception as e:
            st.error(f"❌ Ошибка тестирования: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔬 Улучшенная диагностика извлечения цен")
    
    st.markdown("""
    **Цель:** Понять почему система находит колонку 12, но не может извлечь цены.
    
    **Улучшения:**
    - Детальная диагностика каждого значения
    - Показ точных ошибок конвертации
    - Анализ типов данных в колонке
    - Улучшенная очистка строковых значений
    """)
    
    test_improved_extraction()