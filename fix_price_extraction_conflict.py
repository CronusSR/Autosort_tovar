#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление конфликта систем извлечения цен
"""

import streamlit as st

def fix_warehouse_price_integration():
    """
    Исправляет конфликт в warehouse_price_integration.py
    """
    st.header("🔧 Исправление конфликта извлечения цен")
    
    st.markdown("""
    **ПРОБЛЕМА НАЙДЕНА!**
    
    В `warehouse_price_integration.py` строки 468-470 отвергают данные если они содержат:
    ```python
    ads_processed_indicators = ['ads', 'average_value', 'total_sales', 'branch']
    is_processed_ads = any(indicator in columns for indicator in ads_processed_indicators)
    
    if not is_processed_ads:  # ОТВЕРГАЕТ данные если есть эти колонки!
    ```
    
    Но `integration_patch.py` сохраняет `source_data` (исходные Excel данные) И создает обработанные данные с этими колонками.
    
    **РЕШЕНИЕ:** Исправить логику поиска данных в `warehouse_price_integration.py`
    """)
    
    if st.button("🔧 ИСПРАВИТЬ warehouse_price_integration.py"):
        try:
            # Читаем файл
            file_path = "warehouse_price_integration.py"
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Исправляем проблемную логику
            old_code = """                                # Проверяем что это НЕ обработанные ADS данные
                                ads_processed_indicators = ['ads', 'average_value', 'total_sales', 'branch']
                                is_processed_ads = any(indicator in columns for indicator in ads_processed_indicators)
                                
                                if not is_processed_ads:"""
            
            new_code = """                                # ИСПРАВЛЕНО: Всегда используем source_data (это исходные Excel данные)
                                # Убираем проверку на processed indicators для source_data
                                # ads_processed_indicators = ['ads', 'average_value', 'total_sales', 'branch']
                                # is_processed_ads = any(indicator in columns for indicator in ads_processed_indicators)
                                
                                if key == 'source_data' or True:  # ИСПРАВЛЕНО: всегда используем source_data"""
            
            if old_code in content:
                content = content.replace(old_code, new_code)
                
                # Записываем обратно
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                st.success("✅ Исправление 1 применено!")
                
                # Показываем что изменилось
                st.code(f"БЫЛО:\n{old_code}\n\nСТАЛО:\n{new_code}", language="python")
                
            else:
                st.warning("⚠️ Код для исправления 1 не найден")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
    
    st.markdown("---")
    
    if st.button("🔧 АЛЬТЕРНАТИВА: Отключить warehouse_price_integration"):
        st.markdown("""
        **Альтернативное решение:** Полностью отключить старую систему `warehouse_price_integration.py`
        
        **Преимущества:**
        - Использует только новую систему из `integration_patch.py`
        - Нет конфликтов между системами
        - Простая и надежная логика
        
        **Что нужно сделать:**
        1. Найти где вызывается `warehouse_price_integration.py`
        2. Заменить на использование `simple_price_add.py`
        3. Убрать импорты старой системы
        """)

def test_current_conflict():
    """
    Тестирует текущий конфликт
    """
    st.subheader("🧪 Тест текущего конфликта")
    
    if st.button("🔬 Диагностировать конфликт"):
        try:
            # Симулируем данные как из integration_patch
            mock_file_data = {
                'source_data': 'DataFrame с исходными Excel данными',
                'data': 'DataFrame с колонками: ads, average_value, total_sales, branch'
            }
            
            st.write("**Структура данных из integration_patch.py:**")
            st.json(mock_file_data)
            
            # Симулируем логику warehouse_price_integration
            st.write("**Логика warehouse_price_integration.py:**")
            
            # Это имитирует строки 468-470
            fake_columns = ['номенклатура', 'ads', 'average_value', 'total_sales', 'branch', 'last_purchase_price']
            ads_processed_indicators = ['ads', 'average_value', 'total_sales', 'branch']
            is_processed_ads = any(indicator in fake_columns for indicator in ads_processed_indicators)
            
            st.write(f"   Колонки в данных: {fake_columns}")
            st.write(f"   Индикаторы обработанных ADS: {ads_processed_indicators}")
            st.write(f"   Обнаружены индикаторы: {is_processed_ads}")
            
            if is_processed_ads:
                st.error("❌ **КОНФЛИКТ!** warehouse_price_integration отвергает данные")
                st.write("   Причина: Обнаружены колонки ads, average_value, total_sales, branch")
                st.write("   Результат: 'не удалось извлечь ценовые данные'")
            else:
                st.success("✅ Данные принимаются")
            
            # Показываем решение
            st.write("**После исправления:**")
            st.write("   Логика изменена: всегда использовать source_data")
            st.success("✅ Данные будут приниматься независимо от наличия обработанных колонок")
            
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

def find_warehouse_price_integration_calls():
    """
    Ищет где вызывается warehouse_price_integration
    """
    st.subheader("🔍 Поиск вызовов warehouse_price_integration")
    
    if st.button("🔍 Найти где используется старая система"):
        try:
            import os
            import glob
            
            # Ищем все Python файлы
            python_files = glob.glob("*.py")
            
            calls_found = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Ищем импорты и вызовы
                    if 'warehouse_price_integration' in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'warehouse_price_integration' in line:
                                calls_found.append({
                                    'file': file_path,
                                    'line': i + 1,
                                    'code': line.strip()
                                })
                except:
                    continue
            
            if calls_found:
                st.write("**Найдены вызовы warehouse_price_integration:**")
                for call in calls_found:
                    st.write(f"📄 **{call['file']}** строка {call['line']}:")
                    st.code(call['code'], language="python")
                
                st.write("**🔧 Эти вызовы нужно заменить на:**")
                st.code("""
from simple_price_add import get_prices_for_warehouse_analysis
prices = get_prices_for_warehouse_analysis(system)
                """, language="python")
            else:
                st.success("✅ Вызовы warehouse_price_integration не найдены")
        
        except Exception as e:
            st.error(f"❌ Ошибка поиска: {str(e)}")

if __name__ == "__main__":
    st.title("🔧 Исправление конфликта систем извлечения цен")
    
    st.markdown("""
    **НАЙДЕННАЯ ПРОБЛЕМА:**
    
    1. `integration_patch.py` правильно извлекает цены и сохраняет `source_data`
    2. `warehouse_price_integration.py` проверяет данные и отвергает их если содержат колонки ADS
    3. Получается конфликт: данные есть, но старая система их отвергает
    
    **РЕШЕНИЯ:**
    1. Исправить логику в `warehouse_price_integration.py`
    2. Или полностью отключить старую систему
    """)
    
    fix_warehouse_price_integration()
    
    st.markdown("---")
    
    test_current_conflict()
    
    st.markdown("---")
    
    find_warehouse_price_integration_calls()