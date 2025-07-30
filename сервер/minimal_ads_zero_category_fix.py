#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МИНИМАЛЬНЫЙ ФУНКЦИОНАЛ - Замена ADS=0 на средний по категории
Интеграция в существующую страницу ADS без создания отдельных страниц
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict

def add_ads_zero_fix_to_system(system):
    """
    Добавляет минимальный функционал замены ADS=0 в существующую систему
    
    Args:
        system: Объект ModularInventorySystem
    """
    
    def fix_zero_ads_with_category_average(self):
        """
        Заменяет товары с ADS=0 на средний ADS их категории
        """
        
        if not hasattr(self, 'calculated_ads') or self.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан'}
        
        ads_data = self.calculated_ads.copy()
        zero_ads_mask = ads_data['ads'] == 0
        zero_count = zero_ads_mask.sum()
        
        if zero_count == 0:
            return {'success': True, 'message': 'Товаров с ADS=0 не найдено', 'fixed': 0}
        
        print(f"🔧 Исправляем {zero_count} товаров с ADS=0...")
        
        # Извлекаем категории из ABC данных или создаем автоматически
        category_mapping = {}
        
        # Источник 1: ABC данные
        if hasattr(self, 'abc_data') and self.abc_data is not None:
            for _, row in self.abc_data.iterrows():
                # Находим номенклатуру и категорию в любых колонках
                nomenclature = None
                category = None
                
                for col in ['nomenclature', 'номенклатура']:
                    if col in row and pd.notna(row[col]):
                        nomenclature = str(row[col]).strip()
                        break
                
                for col in ['category', 'категория', 'subcategory', 'подкатегория']:
                    if col in row and pd.notna(row[col]):
                        category = str(row[col]).strip()
                        break
                
                if nomenclature and category and len(category) > 2:
                    category_mapping[nomenclature] = category
        
        # Источник 2: Автоматическое создание из названий
        if not category_mapping:
            for _, row in ads_data.iterrows():
                nomenclature = str(row['номенклатура']).strip()
                
                # ФИЛЬТР: Пропускаем служебные записи
                nomenclature_clean = nomenclature.lower()
                skip_words = ['неисп', 'не исп', 'неопределен', 'итого', 'всего', 'сумма', 'общий']
                
                if any(skip_word in nomenclature_clean for skip_word in skip_words):
                    continue
                
                # Пропускаем слишком короткие названия
                if len(nomenclature.strip()) < 5:
                    continue
                
                words = nomenclature.split()
                
                if len(words) >= 2:
                    category = ' '.join(words[:2])  # Первые 2 слова
                elif len(words) == 1:
                    category = words[0]
                else:
                    continue  # Пропускаем если нет нормальных слов
                
                category_mapping[nomenclature] = category
        
        if not category_mapping:
            return {'success': False, 'error': 'Не удалось создать категории'}
        
        # Добавляем категории к данным ADS
        ads_data['category'] = ads_data['номенклатура'].map(category_mapping)
        
        # ФИЛЬТР: Убираем товары без категории и служебные записи
        ads_data = ads_data.dropna(subset=['category'])
        
        # Дополнительная очистка - убираем категории со служебными словами
        skip_categories = ['неисп', 'не исп', 'неопределен', 'итого', 'всего', 'сумма']
        ads_data = ads_data[~ads_data['category'].str.lower().str.contains('|'.join(skip_categories), na=False)]
        
        # Рассчитываем средний ADS по категориям (только для товаров с ADS > 0)
        positive_ads = ads_data[ads_data['ads'] > 0]
        category_avg_ads = positive_ads.groupby('category')['ads'].mean()
        
        # Исправляем товары с ADS = 0
        fixed_count = 0
        
        for idx in ads_data[zero_ads_mask].index:
            nomenclature = ads_data.loc[idx, 'номенклатура']
            category = ads_data.loc[idx, 'category']
            
            # ФИЛЬТР: Пропускаем служебные записи и неопределенные товары
            nomenclature_clean = str(nomenclature).strip().lower()
            category_clean = str(category).strip().lower()
            
            # Пропускаем если содержит служебные слова
            skip_words = ['неисп', 'не исп', 'неопределен', 'без категории', 'общая', 'итого', 'всего', 'сумма']
            
            if any(skip_word in nomenclature_clean for skip_word in skip_words):
                continue
                
            if any(skip_word in category_clean for skip_word in skip_words):
                continue
            
            # Пропускаем слишком короткие названия (служебные записи)
            if len(nomenclature_clean) < 5:
                continue
            
            # Исправляем только если есть нормальная категория
            if category in category_avg_ads.index:
                new_ads = category_avg_ads[category]
                ads_data.loc[idx, 'ads'] = new_ads
                fixed_count += 1
        
        # Удаляем временную колонку категории
        ads_data = ads_data.drop('category', axis=1)
        
        # Обновляем данные в системе
        self.calculated_ads = ads_data
        
        remaining_zero = (ads_data['ads'] == 0).sum()
        
        print(f"✅ Исправлено: {fixed_count}, осталось ADS=0: {remaining_zero}")
        
        return {
            'success': True,
            'fixed': fixed_count,
            'remaining_zero': remaining_zero,
            'categories_used': len(category_avg_ads),
            'source': 'ABC анализ' if hasattr(self, 'abc_data') and self.abc_data is not None else 'Автоматически'
        }
    
    # Добавляем метод в систему
    import types
    system.fix_zero_ads_with_category_average = types.MethodType(fix_zero_ads_with_category_average, system)


def auto_fix_ads_zero_and_show_result(system):
    """
    АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Исправляет ADS=0 и показывает результат
    Работает автоматически без кнопок
    
    Args:
        system: Объект системы
    """
    
    # Проверяем есть ли данные ADS
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        return
    
    ads_data = system.calculated_ads
    zero_count = (ads_data['ads'] == 0).sum()
    
    # Если нет товаров с ADS=0, ничего не делаем
    if zero_count == 0:
        return
    
    # Добавляем функционал если еще не добавлен
    if not hasattr(system, 'fix_zero_ads_with_category_average'):
        add_ads_zero_fix_to_system(system)
    
    # Проверяем был ли уже выполнен автофикс для этой сессии
    if not hasattr(system, '_ads_zero_autofix_applied'):
        
        # Выполняем автоматическое исправление
        result = system.fix_zero_ads_with_category_average()
        
        # Отмечаем что автофикс был применен
        system._ads_zero_autofix_applied = True
        
        # Показываем результат
        if result['success']:
            if 'message' in result:
                st.info(f"🔧 {result['message']}")
            else:
                st.success(f"🔧 **Автоматически исправлено:** {result['fixed']} товаров с ADS=0 → средний по категории (источник: {result['source']})")
                
                # Дополнительная информация в expander
                with st.expander("📊 Детали автоисправления"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Исправлено товаров", result['fixed'])
                    with col2:
                        st.metric("Осталось ADS=0", result['remaining_zero'])
                    with col3:
                        st.metric("Категорий использовано", result['categories_used'])
        else:
            st.warning(f"⚠️ Не удалось автоматически исправить ADS=0: {result['error']}")
    
    else:
        # Показываем что автофикс уже был применен
        current_zero_count = (system.calculated_ads['ads'] == 0).sum()
        if current_zero_count == 0:
            st.info("✅ **Все товары имеют рассчитанный ADS** (автоисправление применено)")
        else:
            st.info(f"🔧 **Автоисправление применено** (осталось {current_zero_count} товаров с ADS=0)")


# Удаляем старую функцию с кнопкой - больше не нужна
# Оставляем только автоматическое исправление


# ФУНКЦИЯ ДЛЯ АВТОМАТИЧЕСКОЙ ИНТЕГРАЦИИ В СУЩЕСТВУЮЩУЮ СТРАНИЦУ ADS
def integrate_auto_ads_zero_fix_to_ads_page():
    """
    ИНСТРУКЦИЯ: Добавьте эти 4 строки в конец ads_calculation_page_updated()
    для АВТОМАТИЧЕСКОГО исправления ADS=0
    
    ```python
    # В конце функции ads_calculation_page_updated(system):
    
    try:
        from minimal_ads_zero_category_fix import auto_fix_ads_zero_and_show_result
        auto_fix_ads_zero_and_show_result(system)
    except ImportError:
        pass
    ```
    """
    
    return """
# ДОБАВЬТЕ В КОНЕЦ ads_calculation_page_updated(system):

try:
    from minimal_ads_zero_category_fix import auto_fix_ads_zero_and_show_result
    auto_fix_ads_zero_and_show_result(system)
except ImportError:
    pass
"""


def test_ads_zero_fix():
    """
    Тестирование функционала
    """
    
    st.set_page_config(page_title="Тест ADS=0 Fix", layout="wide")
    st.title("🧪 Тест минимального исправления ADS=0")
    
    # Создаем тестовые данные
    test_ads_data = pd.DataFrame({
        'номенклатура': [
            'Винт оцинкованный 6x20',
            'Винт оцинкованный 6x30', 
            'Винт черный 4x16',
            'Гвоздь строительный 50мм',
            'Гвоздь строительный 70мм',
            'Гвоздь финишный 40мм',
            'Саморез универсальный 3x25',
            'Саморез универсальный 4x30'
        ],
        'ads': [0.0, 0.15, 0.0, 0.25, 0.0, 0.18, 0.0, 0.22]
    })
    
    st.markdown("**Тестовые данные:**")
    st.dataframe(test_ads_data, use_container_width=True)
    
    # Создаем mock систему
    class MockSystem:
        def __init__(self):
            self.calculated_ads = test_ads_data.copy()
            self.abc_data = None
    
    mock_system = MockSystem()
    
    # Показываем UI
    st.markdown("### 🔧 Тестирование автоматического исправления:")
    auto_fix_ads_zero_and_show_result(mock_system)
    
    # Показываем результат
    if mock_system.calculated_ads is not None:
        st.markdown("**Текущие данные:**")
        st.dataframe(mock_system.calculated_ads, use_container_width=True)
        
        zero_count = (mock_system.calculated_ads['ads'] == 0).sum()
        st.metric("Осталось товаров с ADS=0", zero_count)


if __name__ == "__main__":
    test_ads_zero_fix()