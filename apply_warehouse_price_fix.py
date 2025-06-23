#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простое применение исправления ценовой интеграции для анализа складов

Использование:
1. Добавить в начало warehouse_analysis_page функции:
   from apply_warehouse_price_fix import apply_warehouse_price_fix
   apply_warehouse_price_fix(system)

2. Или запустить как отдельную функцию

Автор: Claude Code Assistant  
Дата: 2025-06-23
"""

import streamlit as st
# ОТКЛЮЧЕНО: from warehouse_price_integration import apply_warehouse_price_integration


def apply_warehouse_price_fix(system):
    """
    Быстрое применение ценовой интеграции к существующей системе анализа складов
    """
    try:
        # Проверяем что исправление еще не применено
        if hasattr(system, '_warehouse_price_integration_applied'):
            return True
        
        # Применяем интеграцию цен
        # ОТКЛЮЧЕНО:         success = apply_warehouse_price_integration(system)
        
        if success:
            st.info("🔧 Ценовая интеграция для анализа складов применена")
            return True
        else:
            st.warning("⚠️ Не удалось применить ценовую интеграцию")
            return False
            
    except Exception as e:
        st.error(f"❌ Ошибка применения ценовой интеграции: {str(e)}")
        return False


def show_integration_instructions():
    """
    Показывает инструкции по интеграции
    """
    st.markdown("""
    ## 🔧 Инструкции по интеграции ценовой системы
    
    ### Способ 1: Автоматическое применение
    Добавьте в начало функции `warehouse_analysis_page`:
    ```python
    from apply_warehouse_price_fix import apply_warehouse_price_fix
    apply_warehouse_price_fix(system)
    ```
    
    ### Способ 2: Полная замена
    Замените содержимое функции `warehouse_analysis_page` на:
    ```python
    def warehouse_analysis_page(system):
        from enhanced_warehouse_analysis import enhanced_warehouse_analysis_page
        enhanced_warehouse_analysis_page(system)
    ```
    
    ### Что будет добавлено:
    - ✅ Автоматическое чтение цен из 12-й колонки ADS файлов
    - ✅ Интеграция цен в анализ по наименованиям товаров  
    - ✅ Расчет стоимостных показателей для заказов
    - ✅ Иерархическая структура складов по филиалам
    - ✅ Экспорт заказов с ценовой информацией
    
    ### Требования:
    - 📁 ADS файлы должны быть загружены через "Множественный анализ"
    - 📊 Цены должны находиться в 12-й колонке, начиная с 4-й строки
    - 🏪 Названия складов должны соответствовать настроенной иерархии
    """)


if __name__ == "__main__":
    st.header("🔧 Применение ценовой интеграции для анализа складов")
    
    show_integration_instructions()
    
    if st.button("📖 Показать подробные инструкции"):
        show_integration_instructions()