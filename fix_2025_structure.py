#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление системы для работы с новой структурой файлов остатков 2025
Автоматическое обновление для корректной обработки
"""

import streamlit as st
import pandas as pd
from updated_warehouse_analysis_2025 import UpdatedWarehouseAnalyzer2025, apply_updated_warehouse_analysis_2025

def detect_file_structure_2025(file_data):
    """
    Определяет структуру файла остатков (старая или новая 2025)
    """
    try:
        if len(file_data) < 10:
            return "unknown"
        
        # Проверяем строку 6 на наличие названий складов
        if len(file_data) > 5:
            row_6 = file_data[5]  # Строка 6
            # Проверяем на характерные названия складов 2025
            row_6_str = ' '.join([str(cell) for cell in row_6 if cell and str(cell).strip()])
            
            keywords_2025 = ['главный Хаб', 'магазин ШЫМКЕНТ', 'Казыбаева', 'Астана', 'Барыс']
            if any(keyword in row_6_str for keyword in keywords_2025):
                return "2025_new"
        
        # Проверяем строку 7 на старую структуру
        if len(file_data) > 6:
            row_7 = file_data[6]  # Строка 7
            row_7_str = ' '.join([str(cell) for cell in row_7 if cell and str(cell).strip()])
            
            old_keywords = ['АЗМ Шымкент', 'Овощная база', 'TRADE', 'Комплект']
            if any(keyword in row_7_str for keyword in old_keywords):
                return "2024_old"
        
        return "unknown"
        
    except Exception as e:
        print(f"Ошибка определения структуры файла: {e}")
        return "unknown"

def create_safe_remains_parser_2025():
    """
    Создает безопасный парсер файлов остатков с автоопределением структуры
    """
    def safe_parse_remains_2025(file_data, debug_mode=False):
        """
        Безопасный парсер с автоопределением структуры файла
        """
        try:
            if debug_mode:
                st.write("🔍 **Анализ структуры файла остатков...**")
            
            # Определяем структуру файла
            file_structure = detect_file_structure_2025(file_data)
            
            if debug_mode:
                st.write(f"📋 Определена структура: **{file_structure}**")
            
            if file_structure == "2025_new":
                # Используем новый анализатор 2025
                analyzer = UpdatedWarehouseAnalyzer2025()
                result = analyzer.parse_remains_file_2025(file_data)
                
                if debug_mode:
                    st.success("✅ Использован анализатор 2025")
                
                return result
                
            elif file_structure == "2024_old":
                # Используем старый анализатор (импортируем если нужно)
                if debug_mode:
                    st.info("ℹ️ Обнаружена старая структура файла")
                
                # Fallback к простому парсингу
                return simple_fallback_parser(file_data, debug_mode)
                
            else:
                if debug_mode:
                    st.warning("⚠️ Неизвестная структура файла, используем fallback")
                
                return simple_fallback_parser(file_data, debug_mode)
                
        except Exception as e:
            if debug_mode:
                st.error(f"❌ Ошибка парсинга: {e}")
            
            return simple_fallback_parser(file_data, debug_mode)
    
    return safe_parse_remains_2025

def simple_fallback_parser(file_data, debug_mode=False):
    """
    Простой fallback парсер для любой структуры файла
    """
    try:
        remains_data = []
        
        # Ищем номенклатуру в первых 10 строках
        nomenclature_col = 0
        data_start_row = 8  # По умолчанию
        
        # Пытаемся найти строку с "Номенклатура"
        for row_idx in range(min(10, len(file_data))):
            row = file_data[row_idx]
            for col_idx in range(min(5, len(row))):
                cell_value = str(row[col_idx]).lower() if row[col_idx] else ""
                if 'номенклатура' in cell_value:
                    data_start_row = row_idx + 1
                    nomenclature_col = col_idx
                    break
            if data_start_row != 8:
                break
        
        if debug_mode:
            st.write(f"📍 Номенклатура в колонке {nomenclature_col}, данные с строки {data_start_row + 1}")
        
        # Читаем данные
        for i in range(data_start_row, len(file_data)):
            try:
                row = file_data[i]
                if not row or len(row) <= nomenclature_col:
                    continue
                
                item_name = str(row[nomenclature_col]).strip()
                if not item_name or item_name.lower() in ['', 'nan', 'none', 'итого']:
                    continue
                
                # Ищем числовые значения в других колонках
                total_stock = 0
                stock_data = {'номенклатура': item_name}
                
                for col_idx in range(len(row)):
                    if col_idx != nomenclature_col:
                        try:
                            value = float(row[col_idx]) if row[col_idx] and pd.notna(row[col_idx]) else 0
                            if value > 0:
                                total_stock += value
                                stock_data[f'склад_{col_idx}_остаток'] = value
                        except:
                            continue
                
                stock_data['итого_остаток'] = total_stock
                remains_data.append(stock_data)
                
                if len(remains_data) >= 5000:  # Лимит безопасности
                    break
                    
            except Exception as e:
                if debug_mode:
                    st.write(f"⚠️ Ошибка строки {i}: {e}")
                continue
        
        if debug_mode:
            st.write(f"📊 Обработано товаров: {len(remains_data)}")
        
        return pd.DataFrame(remains_data) if remains_data else pd.DataFrame()
        
    except Exception as e:
        if debug_mode:
            st.error(f"❌ Критическая ошибка fallback парсера: {e}")
        return pd.DataFrame()

def fix_system_for_2025_structure(system):
    """
    Исправляет систему для работы с новой структурой файлов 2025
    """
    try:
        st.header("🔧 Исправление системы для файлов остатков 2025")
        
        with st.spinner("Применяем исправления..."):
            
            # 1. Обновляем анализатор складов
            success = apply_updated_warehouse_analysis_2025(system)
            if not success:
                st.error("❌ Не удалось обновить анализатор складов")
                return False
            
            # 2. Заменяем парсер файлов на безопасный
            safe_parser = create_safe_remains_parser_2025()
            
            # Обновляем методы в системе
            if hasattr(system, 'warehouse_analyzer'):
                system.warehouse_analyzer.parse_remains_file = safe_parser
            
            # Добавляем безопасный парсер напрямую к системе
            system.safe_parse_remains_2025 = safe_parser
            
            # 3. Добавляем метод определения структуры
            system.detect_file_structure = detect_file_structure_2025
            
            # 4. Отмечаем что исправления применены
            system._structure_2025_fixed = True
            system._fix_version = "2025.01.structure_fix"
            
        st.success("✅ Система успешно обновлена для работы с файлами остатков 2025!")
        
        # Показываем что исправлено
        st.info("🔧 **Примененные исправления:**")
        st.write("• ✅ Обновлен анализатор складов под структуру 2025")
        st.write("• ✅ Добавлено автоопределение структуры файла")
        st.write("• ✅ Исправлены индексы строк и колонок")
        st.write("• ✅ Обновлена конфигурация складов")
        st.write("• ✅ Добавлен fallback парсер для совместимости")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка исправления системы: {str(e)}")
        return False

def create_2025_fix_page():
    """
    Создает страницу для исправления системы под файлы 2025
    """
    st.title("🔧 Исправление системы для файлов остатков 2025")
    
    st.markdown("""
    ### Проблема
    Система была настроена под старую структуру файлов остатков, 
    но новый файл "остатки на 08.07.2025.xlsx" имеет другую структуру:
    
    **Изменения в структуре:**
    - Строка 6: названия складов (раньше строка 7)
    - Строка 9: начало данных (раньше строка 10)  
    - Колонка 12: итоговые остатки (раньше колонка 14)
    - Новые названия складов и их расположение
    
    ### Решение
    Этот модуль автоматически обновит систему для корректной работы с новой структурой.
    """)
    
    if 'inventory_system' not in st.session_state:
        st.error("❌ Система не инициализирована. Сначала загрузите систему.")
        return
    
    system = st.session_state.inventory_system
    
    # Проверяем текущее состояние
    if hasattr(system, '_structure_2025_fixed'):
        st.success("✅ Исправления уже применены!")
        st.info(f"Версия исправлений: {getattr(system, '_fix_version', 'неизвестно')}")
        
        if st.button("🔄 Применить повторно"):
            fix_system_for_2025_structure(system)
    else:
        st.warning("⚠️ Система требует обновления для работы с файлами 2025")
        
        if st.button("🔧 Применить исправления", type="primary"):
            fix_system_for_2025_structure(system)

if __name__ == "__main__":
    create_2025_fix_page()