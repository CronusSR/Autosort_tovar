#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сравнение структуры разных файлов филиалов
"""

import streamlit as st
import pandas as pd
import os

def get_file_path(filename_pattern):
    """Получает путь к файлу для текущей ОС"""
    if os.name == 'nt':  # Windows
        base_path = r"F:\Работа-Никита\Autosort_tovar"
    else:  # Linux/WSL
        base_path = "/mnt/f/Работа-Никита/Autosort_tovar"
    
    return os.path.join(base_path, filename_pattern)

def analyze_file_structure(file_path, file_name):
    """Анализирует структуру одного файла"""
    try:
        if not os.path.exists(file_path):
            return None, f"Файл не найден: {file_path}"
        
        df = pd.read_excel(file_path)
        
        # Базовая информация
        info = {
            'filename': file_name,
            'shape': df.shape,
            'columns_count': len(df.columns)
        }
        
        # Анализ колонки 12 (индекс 11)
        if len(df.columns) >= 12:
            col_12_name = df.columns[11]
            info['col_12_name'] = col_12_name
            info['col_12_has_poslezakupka'] = 'посл' in str(col_12_name).lower() and 'закуп' in str(col_12_name).lower()
            
            # Анализ данных в колонке 12 начиная с разных строк
            for start_row in [2, 3, 4]:  # Строки 3, 4, 5
                prices_found = 0
                total_checked = 0
                
                for i in range(start_row, min(start_row + 20, len(df))):
                    value = df.iloc[i, 11]
                    total_checked += 1
                    
                    if pd.notna(value):
                        try:
                            price_val = float(value)
                            if price_val > 0:
                                prices_found += 1
                        except:
                            pass
                
                info[f'prices_from_row_{start_row+1}'] = {
                    'found': prices_found,
                    'total': total_checked,
                    'coverage': (prices_found / total_checked * 100) if total_checked > 0 else 0
                }
        else:
            info['col_12_name'] = "НЕТ"
            info['col_12_has_poslezakupka'] = False
        
        # Поиск колонок с ценами
        price_columns = []
        for i, col_name in enumerate(df.columns):
            col_lower = str(col_name).lower()
            if any(word in col_lower for word in ['цена', 'price', 'стоимость', 'закуп', 'посл']):
                price_columns.append({
                    'index': i,
                    'letter': chr(65 + i) if i < 26 else f"A{chr(65 + i - 26)}",
                    'name': col_name
                })
        
        info['price_columns'] = price_columns
        
        # Анализ номенклатуры
        nomenclature_info = {}
        for start_row in [2, 3, 4]:  # Строки 3, 4, 5
            try:
                nomenclature_data = df.iloc[start_row:, 1].copy()  # Колонка B
                nomenclature_clean = nomenclature_data.dropna()
                nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
                nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
                
                nomenclature_info[f'from_row_{start_row+1}'] = len(nomenclature_clean)
            except:
                nomenclature_info[f'from_row_{start_row+1}'] = 0
        
        info['nomenclature_counts'] = nomenclature_info
        
        return info, None
        
    except Exception as e:
        return None, f"Ошибка анализа: {str(e)}"

def compare_files():
    """Сравнивает структуру файлов разных филиалов"""
    st.header("🔍 Сравнение структуры файлов филиалов")
    
    # Файлы для анализа
    files_to_check = [
        ("барыс - прод с мая24-май25.xlsx", "Барыс (работает)"),
        ("астана - прод с мая24-май25.xlsx", "Астана (не работает)"),
    ]
    
    if st.button("📊 Анализировать файлы"):
        results = []
        
        for filename, description in files_to_check:
            file_path = get_file_path(filename)
            st.write(f"🔍 Анализирую: {description}")
            
            info, error = analyze_file_structure(file_path, description)
            
            if error:
                st.error(f"❌ {description}: {error}")
            else:
                results.append(info)
                st.success(f"✅ {description}: анализ завершен")
        
        if len(results) >= 2:
            # Сравнительная таблица
            st.subheader("📊 Сравнительная таблица")
            
            comparison_data = []
            
            for info in results:
                row = {
                    'Файл': info['filename'],
                    'Размер': f"{info['shape'][0]}x{info['shape'][1]}",
                    'Колонок': info['columns_count'],
                    'Колонка 12': info.get('col_12_name', 'НЕТ'),
                    '"Посл. закупка"': "✅" if info.get('col_12_has_poslezakupka', False) else "❌"
                }
                
                # Добавляем информацию о ценах
                for start_row in [3, 4, 5]:
                    price_info = info.get(f'prices_from_row_{start_row}', {})
                    coverage = price_info.get('coverage', 0)
                    row[f'Цены с строки {start_row}'] = f"{coverage:.1f}%"
                
                # Номенклатура
                for start_row in [3, 4, 5]:
                    count = info['nomenclature_counts'].get(f'from_row_{start_row}', 0)
                    row[f'Товаров с строки {start_row}'] = count
                
                comparison_data.append(row)
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
            
            # Детальный анализ различий
            st.subheader("🔍 Анализ различий")
            
            barys_info = results[0] if results[0]['filename'].startswith('Барыс') else results[1]
            astana_info = results[1] if results[1]['filename'].startswith('Астана') else results[0]
            
            # Сравнение колонки 12
            st.write("**Колонка 12:**")
            st.write(f"  Барыс: '{barys_info.get('col_12_name', 'НЕТ')}'")
            st.write(f"  Астана: '{astana_info.get('col_12_name', 'НЕТ')}'")
            
            if barys_info.get('col_12_name') != astana_info.get('col_12_name'):
                st.warning("⚠️ **Названия колонки 12 отличаются!**")
            
            # Сравнение цен
            st.write("**Извлечение цен из колонки 12:**")
            for start_row in [3, 4, 5]:
                barys_prices = barys_info.get(f'prices_from_row_{start_row}', {})
                astana_prices = astana_info.get(f'prices_from_row_{start_row}', {})
                
                st.write(f"  Строка {start_row}:")
                st.write(f"    Барыс: {barys_prices.get('coverage', 0):.1f}% ({barys_prices.get('found', 0)}/{barys_prices.get('total', 0)})")
                st.write(f"    Астана: {astana_prices.get('coverage', 0):.1f}% ({astana_prices.get('found', 0)}/{astana_prices.get('total', 0)})")
            
            # Поиск альтернативных колонок с ценами
            st.write("**Колонки с ценами в файлах:**")
            
            st.write("  Барыс:")
            for col_info in barys_info.get('price_columns', []):
                st.write(f"    {col_info['index']+1} ({col_info['letter']}): '{col_info['name']}'")
            
            st.write("  Астана:")
            for col_info in astana_info.get('price_columns', []):
                st.write(f"    {col_info['index']+1} ({col_info['letter']}): '{col_info['name']}'")
            
            # Рекомендации
            st.subheader("💡 Рекомендации")
            
            astana_prices_best = max([astana_info.get(f'prices_from_row_{r}', {}).get('coverage', 0) for r in [3, 4, 5]])
            
            if astana_prices_best < 10:  # Меньше 10% цен
                st.error("🚨 **Проблема найдена!** В файле Астаны очень мало цен в колонке 12")
                
                astana_price_cols = astana_info.get('price_columns', [])
                if len(astana_price_cols) > 1:
                    st.write("🔧 **Возможные решения:**")
                    st.write("1. Использовать другую колонку для цен в файле Астаны:")
                    for col_info in astana_price_cols:
                        if col_info['index'] != 11:  # Не колонка 12
                            st.write(f"   - Колонка {col_info['index']+1} ({col_info['letter']}): '{col_info['name']}'")
                    
                    st.write("2. Создать адаптивную логику определения колонки с ценами")
                    st.write("3. Проверить что в файле Астаны цены находятся в правильном формате")
                else:
                    st.write("🔧 **Решение:** Проверить формат данных в файле Астаны")
            else:
                st.success("✅ В файле Астаны есть цены в колонке 12, проблема может быть в другом")

def test_astana_file():
    """Детальный тест файла Астаны"""
    st.subheader("🧪 Детальный тест файла Астаны")
    
    if st.button("🔬 Анализировать файл Астаны"):
        try:
            astana_file = get_file_path("астана - прод с мая24-май25.xlsx")
            
            if not os.path.exists(astana_file):
                st.error(f"❌ Файл не найден: {astana_file}")
                return
            
            df = pd.read_excel(astana_file)
            st.success(f"✅ Файл Астаны загружен: {df.shape}")
            
            # Показываем колонки
            st.write("**Все колонки файла Астаны:**")
            for i, col in enumerate(df.columns):
                marker = " ← 12-я колонка" if i == 11 else ""
                st.write(f"  {i+1}. {chr(65+i) if i < 26 else f'A{chr(65+i-26)}'}: {col}{marker}")
            
            # Показываем данные в колонке 12
            if len(df.columns) >= 12:
                st.write("**Данные в колонке 12 (первые 15 строк):**")
                col_12_name = df.columns[11]
                st.write(f"Название: '{col_12_name}'")
                
                for i in range(min(15, len(df))):
                    value = df.iloc[i, 11]
                    nomenclature = df.iloc[i, 1] if len(df.columns) > 1 else "N/A"
                    
                    # Пробуем извлечь цену
                    price_status = "❌"
                    if pd.notna(value):
                        try:
                            price_val = float(value)
                            if price_val > 0:
                                price_status = "✅"
                        except:
                            pass
                    
                    st.write(f"  {price_status} Строка {i+1}: {str(nomenclature)[:20]:20} | {str(value)[:15]:15}")
            
            # Тестируем извлечение как в integration_patch
            st.write("**Тест извлечения как в integration_patch:**")
            
            start_row = 2  # Как в исправленной версии
            nomenclature_col = 1
            price_col = 11
            
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
            nomenclature_clean = nomenclature_data.dropna()
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            
            # Исключаем последнюю строку (как в integration_patch)
            if len(nomenclature_clean) > 0:
                nomenclature_clean = nomenclature_clean[:-1]
            
            st.write(f"Найдено товаров: {len(nomenclature_clean)}")
            
            # Извлекаем цены
            prices_found = 0
            total_items = 0
            
            for idx in list(nomenclature_clean.index)[:20]:  # Первые 20 для теста
                try:
                    item_name = str(nomenclature_clean.loc[idx]).strip()
                    
                    price_value = 0
                    if df.shape[1] > price_col:
                        try:
                            price_raw = df.iloc[idx, price_col]
                            if pd.notna(price_raw):
                                price_value = float(price_raw)
                                if price_value > 0:
                                    prices_found += 1
                        except (ValueError, TypeError):
                            price_value = 0
                    
                    total_items += 1
                    
                    status = "✅" if price_value > 0 else "❌"
                    st.write(f"  {status} {item_name[:30]:30} | Цена: {price_value}")
                    
                except Exception as e:
                    st.write(f"  ❌ Ошибка обработки строки {idx}: {str(e)}")
            
            # Результат
            coverage = (prices_found / total_items * 100) if total_items > 0 else 0
            st.write(f"**Результат:** {prices_found}/{total_items} цен найдено ({coverage:.1f}%)")
            
            if prices_found == 0:
                st.error("🚨 **ПРОБЛЕМА:** Ни одной цены не извлечено из файла Астаны!")
                st.write("🔧 **Это объясняет ошибку 'не удалось извлечь ценовые данные'**")
            else:
                st.success(f"✅ Цены извлекаются ({coverage:.1f}%), проблема может быть в другом месте")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔍 Сравнение структуры файлов филиалов")
    
    st.markdown("""
    **Проблема:** Файл Барыс работает (5560 цен), файл Астаны не работает ("не удалось извлечь ценовые данные").
    
    **Цель:** Найти различия в структуре файлов и понять почему Астана не работает.
    """)
    
    compare_files()
    
    st.markdown("---")
    
    test_astana_file()