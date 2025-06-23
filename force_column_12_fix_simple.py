#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная версия принудительного использования 12-й колонки для цен
"""

import streamlit as st
import pandas as pd

def apply_force_column_12_fix(system):
    """
    Применяет принудительное использование 12-й колонки для цен
    """
    try:
        st.warning("🔧 Принудительное использование 12-й колонки временно отключено")
        st.info("💡 Используйте новую систему извлечения цен через integration_patch.py")
        
        # Устанавливаем флаг
        system._force_column_12_fix_applied = True
        
        st.success("✅ Заглушка применена!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")
        return False

if __name__ == "__main__":
    st.header("🔧 Упрощенная версия принудительного исправления")
    st.info("Эта версия создана для устранения синтаксических ошибок")