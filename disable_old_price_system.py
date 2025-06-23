#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отключение старой системы извлечения цен
"""

import streamlit as st
import os
import glob

def find_old_system_usage():
    """
    Находит все места где используется старая система warehouse_price_integration
    """
    st.header("🔍 Поиск использования старой системы")
    
    if st.button("🔍 Найти все импорты warehouse_price_integration"):
        try:
            # Ищем все Python файлы
            python_files = glob.glob("*.py")
            
            usage_found = []
            
            for file_path in python_files:
                if file_path == "warehouse_price_integration.py":
                    continue  # Пропускаем сам файл
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Ищем импорты и использование
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in [
                            'warehouse_price_integration',
        # ОТКЛЮЧЕНО:                             'apply_warehouse_price_integration',
        # ОТКЛЮЧЕНО:                             'collect_prices_from_multiple_ads_files',
        # ОТКЛЮЧЕНО:                             'extract_prices_from_ads_file',
                            'show_price_integration_status'
                        ]):
                            usage_found.append({
                                'file': file_path,
                                'line': i + 1,
                                'code': line.strip(),
                                'type': 'import' if 'import' in line else 'usage'
                            })
                except:
                    continue
            
            if usage_found:
                st.warning(f"⚠️ **Найдено {len(usage_found)} использований старой системы:**")
                
                # Группируем по файлам
                files_with_usage = {}
                for usage in usage_found:
                    file_name = usage['file']
                    if file_name not in files_with_usage:
                        files_with_usage[file_name] = []
                    files_with_usage[file_name].append(usage)
                
                for file_name, usages in files_with_usage.items():
                    st.write(f"📄 **{file_name}**:")
                    for usage in usages:
                        icon = "📥" if usage['type'] == 'import' else "🔧"
                        st.write(f"   {icon} Строка {usage['line']}: `{usage['code']}`")
                
                # Предлагаем решения
                st.subheader("🔧 Как исправить:")
                st.markdown("""
                **1. Замените импорты:**
                ```python
                # СТАРОЕ - удалить:
                # ОТКЛЮЧЕНО: from warehouse_price_integration import apply_warehouse_price_integration
                # ОТКЛЮЧЕНО: from warehouse_price_integration import show_price_integration_status
                
                # НОВОЕ - добавить:
                from simple_price_add import get_prices_for_warehouse_analysis
                from simple_price_add import show_price_integration_status
                ```
                
                **2. Замените вызовы функций:**
                ```python
                # СТАРОЕ - удалить:
        # ОТКЛЮЧЕНО:                 apply_warehouse_price_integration(system)
                
                # НОВОЕ - использовать:
                prices = get_prices_for_warehouse_analysis(system)
                ```
                """)
            else:
                st.success("✅ Использование старой системы не найдено!")
            
            return usage_found
            
        except Exception as e:
            st.error(f"❌ Ошибка поиска: {str(e)}")
            return []

def disable_old_system_automatically():
    """
    Автоматически отключает старую систему
    """
    st.subheader("🔧 Автоматическое отключение")
    
    if st.button("🔧 ОТКЛЮЧИТЬ старую систему автоматически"):
        try:
            # Находим использование
            usage_found = []
            python_files = glob.glob("*.py")
            
            for file_path in python_files:
                if file_path == "warehouse_price_integration.py":
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Комментируем импорты старой системы
                    content = content.replace(
                        "# ОТКЛЮЧЕНО: from warehouse_price_integration import",
                        "# ОТКЛЮЧЕНО: # ОТКЛЮЧЕНО: from warehouse_price_integration import"
                    )
                    content = content.replace(
                        "# ОТКЛЮЧЕНО: import warehouse_price_integration",
                        "# ОТКЛЮЧЕНО: # ОТКЛЮЧЕНО: import warehouse_price_integration"
                    )
                    
                    # Комментируем вызовы функций
                    lines = content.split('\n')
                    modified_lines = []
                    
                    for line in lines:
                        if any(func in line for func in [
        # ОТКЛЮЧЕНО:                             'apply_warehouse_price_integration',
        # ОТКЛЮЧЕНО:                             'collect_prices_from_multiple_ads_files',
        # ОТКЛЮЧЕНО:                             'extract_prices_from_ads_file'
                        ]) and not line.strip().startswith('#'):
                            modified_lines.append(f"        # ОТКЛЮЧЕНО: {line}")
                        else:
                            modified_lines.append(line)
                    
                    content = '\n'.join(modified_lines)
                    
                    # Сохраняем если были изменения
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        usage_found.append(file_path)
                        st.success(f"✅ Отключено в файле: {file_path}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка в файле {file_path}: {str(e)}")
            
            if usage_found:
                st.success(f"🎉 **Старая система отключена в {len(usage_found)} файлах!**")
                
                # Добавляем новые импорты в нужные места
                st.write("📝 **Теперь добавьте новые импорты где нужно:**")
                st.code("""
from simple_price_add import get_prices_for_warehouse_analysis
from simple_price_add import show_price_integration_status

# Использование:
prices = get_prices_for_warehouse_analysis(system)
show_price_integration_status(system)
                """, language="python")
            else:
                st.info("ℹ️ Использование старой системы не найдено для отключения")
        
        except Exception as e:
            st.error(f"❌ Ошибка автоматического отключения: {str(e)}")

def rename_old_system_file():
    """
    Переименовывает старый файл чтобы он не мешал
    """
    st.subheader("📁 Переименование старого файла")
    
    old_file = "warehouse_price_integration.py"
    new_file = "warehouse_price_integration.py.disabled"
    
    if os.path.exists(old_file):
        if st.button(f"📁 Переименовать {old_file} → {new_file}"):
            try:
                os.rename(old_file, new_file)
                st.success(f"✅ Файл переименован: {old_file} → {new_file}")
                st.info("💡 Теперь старая система полностью отключена")
            except Exception as e:
                st.error(f"❌ Ошибка переименования: {str(e)}")
    else:
        st.info(f"ℹ️ Файл {old_file} не найден")

def test_new_system():
    """
    Тестирует новую систему извлечения цен
    """
    st.subheader("🧪 Тест новой системы")
    
    if st.button("🔬 Протестировать новую систему"):
        try:
            # Создаем mock систему
            class MockSystem:
                def __init__(self):
                    # Симулируем данные как из integration_patch
                    self.multiple_files_data = {
                        'combined_data': None,
                        'processed_results': {}
                    }
                    
                    # Симулируем calculated_ads с ценами
                    import pandas as pd
                    self.calculated_ads = pd.DataFrame({
                        'номенклатура': ['Товар 1', 'Товар 2', 'Товар 3'],
                        'ads': [1.5, 2.3, 0.8],
                        'last_purchase_price': [1000, 1500, 2000]
                    })
            
            mock_system = MockSystem()
            
            # Тестируем новую функцию
            from simple_price_add import get_prices_for_warehouse_analysis
            
            prices = get_prices_for_warehouse_analysis(mock_system)
            
            if prices:
                st.success(f"✅ **Новая система работает!** Найдено {len(prices)} цен")
                
                st.write("**Найденные цены:**")
                for name, price in list(prices.items())[:5]:
                    st.write(f"  {name}: {price:,.0f} ₸")
                
                # Тестируем статус
                st.write("**Тест статуса интеграции:**")
                from simple_price_add import show_price_integration_status
                show_price_integration_status(mock_system)
                
            else:
                st.warning("⚠️ Новая система не нашла цены (но это нормально для mock данных)")
                st.success("✅ Новая система запускается без ошибок")
        
        except Exception as e:
            st.error(f"❌ Ошибка тестирования новой системы: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔧 Отключение старой системы извлечения цен")
    
    st.markdown("""
    **ПЛАН ДЕЙСТВИЙ:**
    
    1. 🔍 **Найти** все места где используется `warehouse_price_integration.py`
    2. 🔧 **Отключить** старые импорты и вызовы функций
    3. 📁 **Переименовать** старый файл чтобы он не мешал
    4. 🧪 **Протестировать** новую систему
    
    **РЕЗУЛЬТАТ:** Будет работать только новая простая система из `integration_patch.py` + `simple_price_add.py`
    """)
    
    # Шаг 1: Поиск
    usage_found = find_old_system_usage()
    
    st.markdown("---")
    
    # Шаг 2: Автоматическое отключение
    disable_old_system_automatically()
    
    st.markdown("---")
    
    # Шаг 3: Переименование файла
    rename_old_system_file()
    
    st.markdown("---")
    
    # Шаг 4: Тест новой системы
    test_new_system()
    
    st.markdown("---")
    
    st.success("""
    ✅ **После выполнения всех шагов:**
    
    - Старая система `warehouse_price_integration.py` будет отключена
    - Новая система `integration_patch.py` + `simple_price_add.py` будет работать
    - Цены будут извлекаться из сохраненных `source_data` и `last_purchase_price`
    - Никаких конфликтов между системами
    """)