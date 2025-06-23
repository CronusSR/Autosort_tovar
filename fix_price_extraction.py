#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление извлечения цен на основе реальной структуры файлов
Адаптированный под ваши файлы без зависимости от внешних библиотек
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def diagnose_ads_file_structure(file_data, filename: str):
    """
    Диагностирует структуру ADS файла для понимания где находятся цены
    """
    try:
        st.write(f"🔍 Диагностика файла: {filename}")
        
        # Читаем файл если это путь
        if isinstance(file_data, str):
            df = pd.read_excel(file_data)
        elif hasattr(file_data, 'read'):
            df = pd.read_excel(file_data)
        else:
            df = file_data.copy()
        
        st.info(f"📐 Размер файла: {len(df)} строк, {len(df.columns)} колонок")
        
        # Показываем первые строки
        with st.expander("🔍 Первые 10 строк файла"):
            st.dataframe(df.head(10))
        
        # Показываем структуру колонок
        with st.expander("📋 Структура колонок"):
            col_info = []
            for i, col in enumerate(df.columns):
                sample_val = df[col].iloc[0] if len(df) > 0 else None
                col_info.append({
                    'Номер': i + 1,
                    'Название': str(col),
                    'Тип': str(df[col].dtype),
                    'Пример': str(sample_val)[:50] if sample_val is not None else 'N/A'
                })
            
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df)
        
        # Анализируем различные колонки на предмет цен
        st.subheader("🎯 Поиск ценовых данных")
        
        price_analysis = []
        
        # Проверяем каждую колонку
        for col_idx, col_name in enumerate(df.columns):
            col_data = df[col_name]
            
            # Пропускаем первые 3 строки и берем данные с 4-й
            data_from_4th = col_data.iloc[3:] if len(col_data) > 3 else col_data
            
            # Анализируем на числовые значения
            numeric_count = 0
            numeric_values = []
            
            for val in data_from_4th:
                if pd.notna(val):
                    try:
                        # Пробуем преобразовать в число
                        if isinstance(val, (int, float)):
                            numeric_values.append(float(val))
                            numeric_count += 1
                        elif isinstance(val, str):
                            # Пробуем извлечь число из строки
                            val_clean = val.replace(' ', '').replace(',', '.')
                            val_clean = ''.join(c for c in val_clean if c.isdigit() or c == '.')
                            if val_clean and '.' in val_clean:
                                numeric_values.append(float(val_clean))
                                numeric_count += 1
                            elif val_clean:
                                numeric_values.append(float(val_clean))
                                numeric_count += 1
                    except:
                        pass
            
            # Определяем вероятность что это цены
            price_probability = 0
            col_name_lower = str(col_name).lower()
            
            # Проверяем название колонки
            price_keywords = ['цена', 'price', 'стоимость', 'сумма', 'средн', 'сред']
            if any(keyword in col_name_lower for keyword in price_keywords):
                price_probability += 40
            
            # Проверяем числовые значения
            if numeric_count > 0:
                price_probability += 30
                
                # Проверяем диапазон значений (цены обычно > 0 и < 1000000)
                if numeric_values:
                    avg_val = np.mean(numeric_values)
                    if 1 < avg_val < 1000000:
                        price_probability += 20
                    
                    # Проверяем что большинство значений положительные
                    positive_count = sum(1 for v in numeric_values if v > 0)
                    if positive_count / len(numeric_values) > 0.7:
                        price_probability += 10
            
            price_analysis.append({
                'Колонка': col_idx + 1,
                'Название': str(col_name),
                'Числовых значений': numeric_count,
                'Среднее значение': f"{np.mean(numeric_values):,.2f}" if numeric_values else "N/A",
                'Мин/Макс': f"{min(numeric_values):,.0f} - {max(numeric_values):,.0f}" if numeric_values else "N/A",
                'Вероятность цены': f"{price_probability}%"
            })
        
        # Сортируем по вероятности
        price_analysis.sort(key=lambda x: int(x['Вероятность цены'].replace('%', '')), reverse=True)
        
        price_df = pd.DataFrame(price_analysis)
        st.dataframe(price_df)
        
        # Находим наиболее вероятную колонку с ценами
        best_price_col = None
        if price_analysis:
            best_candidate = price_analysis[0]
            best_probability = int(best_candidate['Вероятность цены'].replace('%', ''))
            
            if best_probability >= 50:
                best_price_col = best_candidate['Колонка'] - 1  # Переводим в индекс (0-based)
                st.success(f"✅ Наиболее вероятная ценовая колонка: {best_candidate['Колонка']} - '{best_candidate['Название']}'")
            else:
                st.warning(f"⚠️ Лучшая колонка имеет только {best_probability}% вероятности быть ценовой")
        
        # Специально проверяем 12-ю колонку
        st.subheader("🎯 Специальная проверка 12-й колонки")
        
        if len(df.columns) >= 12:
            col_12_data = df.iloc[:, 11]  # 12-я колонка (индекс 11)
            col_12_name = df.columns[11]
            
            st.write(f"**Название 12-й колонки:** {col_12_name}")
            
            # Показываем данные с 4-й строки
            data_from_4th = col_12_data.iloc[3:13] if len(col_12_data) > 3 else col_12_data
            
            st.write("**Данные в 12-й колонке (строки 4-13):**")
            for idx, val in enumerate(data_from_4th):
                row_num = idx + 4
                st.write(f"  Строка {row_num}: {val} (тип: {type(val).__name__})")
            
            # Пробуем извлечь числовые значения
            numeric_values_12 = []
            for val in col_12_data.iloc[3:]:
                if pd.notna(val):
                    try:
                        if isinstance(val, (int, float)):
                            numeric_values_12.append(float(val))
                        elif isinstance(val, str):
                            val_clean = val.replace(' ', '').replace(',', '.')
                            val_clean = ''.join(c for c in val_clean if c.isdigit() or c == '.')
                            if val_clean:
                                numeric_values_12.append(float(val_clean))
                    except:
                        pass
            
            if numeric_values_12:
                st.success(f"✅ В 12-й колонке найдено {len(numeric_values_12)} числовых значений")
                st.write(f"Среднее: {np.mean(numeric_values_12):,.2f}")
                st.write(f"Диапазон: {min(numeric_values_12):,.0f} - {max(numeric_values_12):,.0f}")
            else:
                st.error("❌ В 12-й колонке числовые значения не найдены")
        else:
            st.error(f"❌ В файле только {len(df.columns)} колонок, 12-й нет")
        
        return best_price_col, df
        
    except Exception as e:
        st.error(f"❌ Ошибка диагностики: {str(e)}")
        return None, None


def extract_prices_adaptive(file_data, filename: str, suggested_col: int = None) -> pd.DataFrame:
    """
    Адаптивное извлечение цен с автоматическим определением колонки
    """
    try:
        st.info(f"💰 Извлекаю цены из {filename}")
        
        # Читаем файл
        if isinstance(file_data, str):
            df = pd.read_excel(file_data)
        elif hasattr(file_data, 'read'):
            df = pd.read_excel(file_data)
        else:
            df = file_data.copy()
        
        # Определяем колонку с ценами
        price_col_idx = suggested_col
        
        if price_col_idx is None:
            # Автоматически ищем ценовую колонку
            best_col = None
            best_score = 0
            
            for col_idx, col_name in enumerate(df.columns):
                score = 0
                col_data = df[col_name].iloc[3:]  # С 4-й строки
                
                # Проверяем название
                col_name_lower = str(col_name).lower()
                if any(word in col_name_lower for word in ['цена', 'price', 'стоимость', 'сумма']):
                    score += 50
                
                # Проверяем числовые значения
                numeric_count = 0
                for val in col_data:
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                        numeric_count += 1
                
                if numeric_count > len(col_data) * 0.3:  # Больше 30% числовых значений
                    score += numeric_count
                
                if score > best_score:
                    best_score = score
                    best_col = col_idx
            
            price_col_idx = best_col
        
        if price_col_idx is None:
            st.error("❌ Не удалось определить колонку с ценами")
            return pd.DataFrame()
        
        # Извлекаем цены
        nomenclature_col = df.iloc[:, 0]  # Первая колонка - наименования
        price_col = df.iloc[:, price_col_idx]  # Найденная ценовая колонка
        
        price_data = []
        
        # Начинаем с 4-й строки (индекс 3)
        for idx in range(3, len(df)):
            name = nomenclature_col.iloc[idx]
            price_val = price_col.iloc[idx]
            
            # Проверяем наименование
            if pd.isna(name) or str(name).strip() == '':
                continue
            
            name_clean = str(name).strip()
            
            # Обрабатываем цену
            price_clean = 0.0
            if pd.notna(price_val):
                try:
                    if isinstance(price_val, (int, float)):
                        price_clean = float(price_val)
                    else:
                        # Извлекаем число из строки
                        price_str = str(price_val).replace(' ', '').replace(',', '.')
                        price_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
                        if price_str:
                            price_clean = float(price_str)
                except:
                    price_clean = 0.0
            
            # Определяем филиал
            branch = determine_branch_from_filename(filename)
            
            price_data.append({
                'наименование': name_clean,
                'цена': price_clean,
                'филиал': branch,
                'источник': filename,
                'колонка_цены': price_col_idx + 1,
                'строка': idx + 1
            })
        
        result_df = pd.DataFrame(price_data)
        
        if not result_df.empty:
            items_with_prices = (result_df['цена'] > 0).sum()
            avg_price = result_df[result_df['цена'] > 0]['цена'].mean() if items_with_prices > 0 else 0
            
            st.success(f"✅ {filename}: {len(result_df)} товаров, {items_with_prices} с ценами")
            st.info(f"💰 Использована {price_col_idx + 1}-я колонка, средняя цена: {avg_price:,.0f}")
        
        return result_df
        
    except Exception as e:
        st.error(f"❌ Ошибка извлечения цен из {filename}: {str(e)}")
        return pd.DataFrame()


def determine_branch_from_filename(filename: str) -> str:
    """
    Улучшенное определение филиала по имени файла
    """
    filename_lower = filename.lower()
    
    # Более точные ключевые слова
    if 'барыс' in filename_lower:
        return 'Алматы_Барыс'
    elif 'казыбаева' in filename_lower:
        return 'Алматы_Казыбаева'
    elif 'база' in filename_lower or 'комплект' in filename_lower:
        return 'Алматы_База'
    elif 'шымкент' in filename_lower or 'овощная' in filename_lower:
        return 'Шымкент'
    elif 'астана' in filename_lower:
        return 'Астана'
    elif 'алматы' in filename_lower:
        return 'Алматы'
    else:
        return 'Неопределен'


def test_price_extraction_fix():
    """
    Тест исправленного извлечения цен
    """
    st.header("🔧 Тест исправленного извлечения цен")
    
    # Тестируем на файле Барыс
    test_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
    
    if st.button("🧪 Тест диагностики файла Барыс"):
        with st.spinner("Диагностирую структуру файла..."):
            best_col, df = diagnose_ads_file_structure(test_file, "барыс - прод с мая24-май25.xlsx")
            
            if best_col is not None:
                st.success(f"🎯 Рекомендуемая колонка для цен: {best_col + 1}")
                
                # Тестируем извлечение
                if st.button("💰 Тест извлечения цен"):
                    with st.spinner("Извлекаю цены..."):
                        prices_df = extract_prices_adaptive(df, "барыс - прод с мая24-май25.xlsx", best_col)
                        
                        if not prices_df.empty:
                            st.success(f"✅ Извлечено {len(prices_df)} записей")
                            
                            # Показываем статистику
                            items_with_prices = (prices_df['цена'] > 0).sum()
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Всего товаров", len(prices_df))
                            with col2:
                                st.metric("С ценами", items_with_prices)
                            with col3:
                                if items_with_prices > 0:
                                    avg_price = prices_df[prices_df['цена'] > 0]['цена'].mean()
                                    st.metric("Средняя цена", f"{avg_price:,.0f} ₸")
                            
                            # Показываем превью
                            st.subheader("👀 Превью извлеченных цен")
                            st.dataframe(prices_df.head(20))
                        else:
                            st.error("❌ Не удалось извлечь цены")


if __name__ == "__main__":
    test_price_extraction_fix()