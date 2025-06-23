#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблемы с пропуском первого товара
"""

import streamlit as st

def fix_first_item_issue():
    """
    Исправляет проблему с пропуском первого товара в integration_patch.py
    """
    st.header("🔧 Исправление пропуска первого товара")
    
    st.markdown("""
    **Проблема найдена!**
    
    В `integration_patch.py` есть строка:
    ```python
    # Исключаем последнюю строку
    if len(nomenclature_clean) > 0:
        nomenclature_clean = nomenclature_clean[:-1]
    ```
    
    Но в `modular_inventory_system.py` этой строки НЕТ!
    
    **Также возможна проблема с start_row=3** - может нужно начинать раньше.
    """)
    
    if st.button("🔧 Исправить integration_patch.py"):
        try:
            # Читаем файл
            file_path = "integration_patch.py"
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Комментируем проблемную строку
            old_code = """        # Исключаем последнюю строку
        if len(nomenclature_clean) > 0:
            nomenclature_clean = nomenclature_clean[:-1]"""
            
            new_code = """        # ИСПРАВЛЕНО: НЕ исключаем последнюю строку (как в modular_inventory_system.py)
        # if len(nomenclature_clean) > 0:
        #     nomenclature_clean = nomenclature_clean[:-1]"""
            
            if old_code in content:
                content = content.replace(old_code, new_code)
                
                # Записываем обратно
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                st.success("✅ Исправление применено!")
                st.info("Теперь система НЕ будет исключать последнюю строку, как в оригинальной функции")
                
                # Показываем что изменилось
                st.code(f"БЫЛО:\n{old_code}\n\nСТАЛО:\n{new_code}", language="python")
                
            else:
                st.warning("⚠️ Проблемная строка не найдена - возможно уже исправлена")
        
        except Exception as e:
            st.error(f"❌ Ошибка исправления: {str(e)}")
    
    # Дополнительные варианты
    st.subheader("🔧 Дополнительные варианты исправления")
    
    # Изменение start_row
    new_start_row = st.number_input(
        "Новый start_row (если нужно начинать раньше)", 
        min_value=0, 
        max_value=5, 
        value=3,
        help="Текущий start_row=3 (строка 4). Попробуйте 2 (строка 3) или 1 (строка 2)"
    )
    
    if st.button(f"🔧 Изменить start_row на {new_start_row}"):
        try:
            file_path = "integration_patch.py"
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Заменяем start_row
            old_line = "        start_row = 3         # Строка 4"
            new_line = f"        start_row = {new_start_row}         # Строка {new_start_row + 1} (ИСПРАВЛЕНО)"
            
            if old_line in content:
                content = content.replace(old_line, new_line)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                st.success(f"✅ start_row изменен на {new_start_row}!")
                st.info(f"Теперь обработка начнется со строки {new_start_row + 1}")
            else:
                st.warning("⚠️ Строка start_row не найдена")
        
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

def test_fix():
    """Тестирует исправление"""
    st.subheader("🧪 Тест исправления")
    
    if st.button("🔬 Протестировать исправленную версию"):
        try:
            # Тестируем исправленную функцию
            from integration_patch import process_single_file_safe
            
            # Загружаем файл
            import os
            if os.name == 'nt':  # Windows
                barys_file = r"F:\Работа-Никита\Autosort_tovar\барыс - прод с мая24-май25.xlsx"
            else:  # Linux/WSL
                barys_file = "/mnt/f/Работа-Никита/Autosort_tovar/барыс - прод с мая24-май25.xlsx"
            
            with open(barys_file, 'rb') as f:
                file_content = f.read()
            
            result = process_single_file_safe(file_content, "барыс - прод с мая24-май25.xlsx", "Алматы_Барыс")
            
            if result.get('success'):
                data = result['data']
                st.success(f"✅ Обработано товаров: {len(data)}")
                
                # Показываем первые товары
                st.write("**Первые 5 товаров:**")
                for i, (_, row) in enumerate(data.head().iterrows()):
                    st.write(f"  {i+1}. {row['номенклатура']}")
                
                # Проверяем цены
                if 'last_purchase_price' in data.columns:
                    prices_found = (data['last_purchase_price'] > 0).sum()
                    st.write(f"💰 Цены найдены: {prices_found}/{len(data)}")
                
            else:
                st.error(f"❌ Ошибка: {result.get('error')}")
        
        except Exception as e:
            st.error(f"❌ Ошибка тестирования: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔧 Исправление пропуска первого товара")
    
    st.markdown("""
    **Найденные проблемы:**
    
    1. **Исключение последней строки** - в `integration_patch.py` есть `nomenclature_clean[:-1]`, а в оригинале нет
    2. **Неправильный start_row** - возможно нужно начинать раньше строки 4
    
    **Исправления:**
    - Убрать исключение последней строки
    - Проверить правильность start_row
    """)
    
    fix_first_item_issue()
    
    st.markdown("---")
    
    test_fix()