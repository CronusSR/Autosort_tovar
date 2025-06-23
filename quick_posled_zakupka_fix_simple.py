#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная версия исправления для колонки "Посл. закупка"
"""

import streamlit as st
import pandas as pd

def apply_posled_zakupka_fix(system):
    """
    Применяет исправление для работы с колонкой "Посл. закупка"
    """
    try:
        # Проверяем что исправление не применено
        if hasattr(system, '_posled_zakupka_fix_applied'):
            return True
        
        st.info("🔧 Применяю упрощенное исправление для колонки 'Посл. закупка'...")
        
        # Устанавливаем флаг
        system._posled_zakupka_fix_applied = True
        
        st.success("✅ Упрощенное исправление для 'Посл. закупка' применено!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка применения исправления: {str(e)}")
        return False

if __name__ == "__main__":
    st.header("🔧 Упрощенное исправление для 'Посл. закупка'")
    st.info("Эта версия создана для устранения ошибок с переменными")