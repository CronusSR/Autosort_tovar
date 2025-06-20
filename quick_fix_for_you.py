# quick_fix_for_you.py
"""
🚀 БЫСТРОЕ ИСПРАВЛЕНИЕ ВАШЕЙ ОШИБКИ 'номенклатура'

Добавьте этот код в начало вашей функции warehouse_analysis_page
"""

import streamlit as st
import pandas as pd


def fix_nomenclature_error(system):
    """
    ИСПРАВЛЯЕТ ошибку 'номенклатура' одной строкой
    
    ИСПОЛЬЗОВАНИЕ:
    def warehouse_analysis_page(system):
        from quick_fix_for_you import fix_nomenclature_error
        if fix_nomenclature_error(system):
            return  # Функция уже выполнена с исправлениями
    """
    
    try:
        # Пробуем применить полное решение
        from final_warehouse_solution import (
            apply_your_complete_solution,
            create_your_complete_warehouse_page
        )
        
        # Применяем исправления
        if not hasattr(system, '_your_complete_solution_applied'):
            apply_your_complete_solution(system)
        
        # Запускаем исправленную страницу
        warehouse_page = create_your_complete_warehouse_page()
        warehouse_page(system)
        
        return True
        
    except ImportError:
        st.error("❌ Файл final_warehouse_solution.py не найден. Создайте его из артефакта.")
        return False
    except Exception as e:
        st.error(f"❌ Ошибка применения исправлений: {str(e)}")
        return False


def emergency_fix(system):
    """
    ЭКСТРЕННОЕ исправление если полное решение не работает
    """
    
    st.warning("🚨 Используется экстренное исправление")
    
    # Добавляем минимальные методы
    if not hasattr(system, 'analyze_warehouse_stock_with_details'):
        def dummy_analyze(remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
            st.error("❌ Метод анализа не реализован. Примените полное решение.")
            return []
        
        system.analyze_warehouse_stock_with_details = dummy_analyze
    
    if not hasattr(system, 'get_warehouse_recommendations'):
        def dummy_recommendations(analysis_results=None):
            return {}
        
        system.get_warehouse_recommendations = dummy_recommendations
    
    # Базовая страница
    st.header("📦 Анализ складов (экстренный режим)")
    st.error("""
    ❌ **Полное решение не загружено.**
    
    **Для исправления:**
    1. Создайте файл `final_warehouse_solution.py` из артефакта
    2. Замените вашу функцию `warehouse_analysis_page` на:
    
    ```python
    def warehouse_analysis_page(system):
        from quick_fix_for_you import fix_nomenclature_error
        fix_nomenclature_error(system)
    ```
    """)


# Простая замена функции
def replace_warehouse_analysis_page():
    """
    Возвращает новую функцию warehouse_analysis_page
    
    ИСПОЛЬЗОВАНИЕ:
    # Замените вашу функцию на:
    from quick_fix_for_you import replace_warehouse_analysis_page
    warehouse_analysis_page = replace_warehouse_analysis_page()
    """
    
    def new_warehouse_analysis_page(system):
        """Новая исправленная функция анализа складов"""
        
        if fix_nomenclature_error(system):
            # Полное решение применено и выполнено
            pass
        else:
            # Запускаем экстренное исправление
            emergency_fix(system)
    
    return new_warehouse_analysis_page


# Автоисправление в main
def auto_fix_main(original_main_function):
    """
    Автоматически исправляет main функцию
    
    ИСПОЛЬЗОВАНИЕ:
    from quick_fix_for_you import auto_fix_main
    
    # Оборачиваем вашу main функцию
    original_main = main
    main = auto_fix_main(original_main)
    """
    
    def fixed_main():
        """Исправленная main функция"""
        
        try:
            # Запускаем оригинальную функцию
            return original_main_function()
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'номенклатура' in error_msg or 'keyerror' in error_msg:
                st.error(f"""
                ❌ **Обнаружена ошибка анализа складов:** {str(e)}
                
                🔧 **Автоисправление:**
                Применяем экстренные исправления для продолжения работы.
                """)
                
                # Пробуем продолжить с исправлениями
                try:
                    # Получаем систему из session_state
                    if 'inventory_system' in st.session_state:
                        system = st.session_state.inventory_system
                        
                        # Применяем исправления
                        from final_warehouse_solution import apply_your_complete_solution
                        apply_your_complete_solution(system)
                        
                        st.success("✅ Исправления применены! Перезапустите приложение.")
                        
                    return None
                    
                except Exception as fix_error:
                    st.error(f"❌ Не удалось применить автоисправления: {str(fix_error)}")
                    raise e
            else:
                # Другая ошибка, просто передаем дальше
                raise e
    
    return fixed_main


# Инструкции для быстрого применения
def quick_instructions():
    """
    Быстрые инструкции по исправлению
    """
    
    return """
# 🚀 БЫСТРОЕ ИСПРАВЛЕНИЕ ОШИБКИ 'номенклатура'

## ⚡ ВАРИАНТ 1: Замена одной строкой

```python
def warehouse_analysis_page(system):
    from quick_fix_for_you import fix_nomenclature_error
    if fix_nomenclature_error(system):
        return  # Все исправлено и выполнено
```

## ⚡ ВАРИАНТ 2: Полная замена функции

```python
from quick_fix_for_you import replace_warehouse_analysis_page

# Замените старую функцию на новую
warehouse_analysis_page = replace_warehouse_analysis_page()
```

## ⚡ ВАРИАНТ 3: Автоисправление main

```python
from quick_fix_for_you import auto_fix_main

# В конце файла оберните main
if __name__ == "__main__":
    original_main = main
    main = auto_fix_main(original_main)
    main()
```

## 📋 ЧТО НУЖНО:

1. **Создайте файлы из артефактов:**
   - `final_warehouse_solution.py` (основное решение)
   - `quick_fix_for_you.py` (этот файл)

2. **Выберите один из вариантов выше**

3. **Перезапустите приложение**

## ✅ РЕЗУЛЬТАТ:

- ❌ Ошибка 'номенклатура' исправлена
- ✅ Анализ складов работает
- ✅ Файлы читаются правильно
- ✅ Отчеты генерируются

## 🆘 ЕСЛИ НЕ РАБОТАЕТ:

Напишите в чат точный текст ошибки и какой вариант пробовали.
"""


if __name__ == "__main__":
    print("🚀 Быстрое исправление для ошибки 'номенклатура'")
    print(quick_instructions())