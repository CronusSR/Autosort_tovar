#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СТРАНИЦА СИСТЕМЫ РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ
Отдельная страница для Streamlit multipage app

Файл: pages/🚚_Рекомендации_по_перемещениям.py
"""

import sys
import os

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Импортируем нашу систему рекомендаций
try:
    from movement_recommendations import (
        MovementRecommendationEngine, 
        MovementConfig,
        show_movement_recommendations_page
    )
except ImportError:
    st.error("❌ Не удалось импортировать модуль movement_recommendations.py")
    st.info("Убедитесь, что файл movement_recommendations.py находится в корневой папке проекта")
    st.stop()

# ===== КОНФИГУРАЦИЯ СТРАНИЦЫ =====

st.set_page_config(
    page_title="Рекомендации по перемещениям",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ОСНОВНАЯ ЛОГИКА СТРАНИЦЫ =====

def main():
    """Основная функция страницы"""
    
    # Заголовок страницы
    st.title("🚚 Система рекомендаций по складским перемещениям")
    st.markdown("---")
    
    # Проверяем наличие системы в session_state
    if 'inventory_system' not in st.session_state:
        show_system_not_initialized()
        return
    
    # Проверяем наличие необходимых данных
    system = st.session_state.inventory_system
    
    data_status = check_data_availability(system)
    
    if not data_status['has_ads'] or not data_status['has_stock']:
        show_missing_data_info(data_status)
        return
    
    # Если все данные есть, показываем основной интерфейс
    show_movement_recommendations_page()

def show_system_not_initialized():
    """Показать сообщение о неинициализированной системе"""
    
    st.error("❌ Система анализа запасов не инициализирована")
    
    st.markdown("""
    ### Как исправить:
    
    1. **Перейдите на главную страницу** приложения
    2. **Загрузите необходимые файлы:**
       - Файл с данными продаж (для расчета ADS)
       - Файл с текущими остатками по точкам
    3. **Выполните расчет ADS** и загрузку остатков
    4. **Вернитесь на эту страницу** для анализа рекомендаций
    """)
    
    # Кнопка для перехода на главную
    if st.button("🏠 Перейти на главную страницу", type="primary"):
        st.switch_page("streamlit_modular_app.py")  # Замените на имя вашего главного файла
    
    # Показываем инструкцию по быстрому старту
    with st.expander("📖 Инструкция по быстрому старту"):
        st.markdown("""
        ### Быстрый старт системы рекомендаций:
        
        #### 1. Подготовка данных
        - **ADS файл**: Excel с колонками 'Наименование' и продажами за период
        - **Файл остатков**: Excel с номенклатурой и остатками по точкам продаж
        
        #### 2. Загрузка в систему
        1. На главной странице выберите "Расчет ADS"
        2. Загрузите файл продаж
        3. Рассчитайте среднедневные продажи (ADS)
        4. Перейдите в "Остатки" и загрузите файл остатков
        
        #### 3. Анализ рекомендаций
        1. Вернитесь на эту страницу
        2. Настройте нормативы запасов под ваш бизнес
        3. Запустите анализ рекомендаций
        4. Получите полный отчет с рекомендациями
        
        #### 4. Что вы получите:
        - 🔍 **Автоматическое определение излишков** в подразделениях
        - 🚚 **Конкретные рекомендации** по перемещению между филиалами  
        - 🛒 **Логику "вытягивания"**: магазин → склад → хаб → заказ поставщику
        - 📊 **Полный отчет** с визуализацией и экспортом в Excel
        """)

def check_data_availability(system) -> dict:
    """Проверка наличия необходимых данных"""
    
    status = {
        'has_ads': False,
        'has_stock': False,
        'ads_count': 0,
        'stock_count': 0,
        'common_items': 0,
        'locations_count': 0
    }
    
    # Проверяем ADS
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        if not system.calculated_ads.empty and 'ads' in system.calculated_ads.columns:
            status['has_ads'] = True
            status['ads_count'] = len(system.calculated_ads)
    
    # Проверяем остатки  
    if hasattr(system, 'stock_data') and system.stock_data is not None:
        if not system.stock_data.empty:
            status['has_stock'] = True
            status['stock_count'] = len(system.stock_data)
            status['locations_count'] = len([col for col in system.stock_data.columns if col != 'номенклатура'])
    
    # Считаем пересечения
    if status['has_ads'] and status['has_stock']:
        ads_items = set(system.calculated_ads['номенклатура'].tolist())
        stock_items = set(system.stock_data['номенклатура'].tolist())
        status['common_items'] = len(ads_items & stock_items)
    
    return status

def show_missing_data_info(data_status: dict):
    """Показать информацию о недостающих данных"""
    
    st.warning("⚠️ Не все необходимые данные загружены")
    
    # Показываем статус данных
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Данные продаж (ADS)")
        if data_status['has_ads']:
            st.success(f"✅ Загружено: {data_status['ads_count']} товаров")
        else:
            st.error("❌ ADS не рассчитан")
            st.markdown("""
            **Необходимо:**
            1. Перейти в раздел "Расчет ADS"
            2. Загрузить файл продаж
            3. Рассчитать среднедневные продажи
            """)
    
    with col2:
        st.subheader("📦 Данные остатков")
        if data_status['has_stock']:
            st.success(f"✅ Загружено: {data_status['stock_count']} товаров по {data_status['locations_count']} точкам")
        else:
            st.error("❌ Остатки не загружены")
            st.markdown("""
            **Необходимо:**
            1. Перейти в раздел "Остатки"
            2. Загрузить файл остатков
            3. Убедиться в корректности данных
            """)
    
    # Общая информация
    if data_status['has_ads'] and data_status['has_stock']:
        if data_status['common_items'] > 0:
            st.info(f"📊 Готово к анализу: {data_status['common_items']} товаров имеют и ADS, и остатки")
            st.success("✅ Все данные загружены! Обновите страницу для запуска анализа.")
            
            if st.button("🔄 Обновить страницу", type="primary"):
                st.rerun()
        else:
            st.error("❌ Нет товаров с совпадающими названиями в файлах ADS и остатков")
            st.markdown("""
            **Возможные причины:**
            - Разные названия товаров в файлах
            - Ошибки в именах колонок
            - Пустые данные в файлах
            
            **Решение:** Проверьте соответствие названий товаров в обоих файлах
            """)
    
    # Кнопки навигации
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 Перейти к расчету ADS", type="secondary", disabled=data_status['has_ads']):
            # Навигация к разделу ADS
            pass
    
    with col2:
        if st.button("📦 Перейти к загрузке остатков", type="secondary", disabled=data_status['has_stock']):
            # Навигация к разделу остатков
            pass

def show_integration_info():
    """Показать информацию об интеграции"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ О системе")
    
    st.sidebar.markdown("""
    **Система рекомендаций v1.0**
    
    **Возможности:**
    - 🔍 Определение излишков
    - 🚚 Рекомендации по перемещению  
    - 🛒 Логика "вытягивания"
    - 📊 Полный отчет с визуализацией
    
    **Интеграция:**
    - ✅ Использует данные основной системы
    - ✅ Совместим с ADS расчетами
    - ✅ Поддержка цен (если доступны)
    - ✅ Экспорт в Excel
    """)
    
    with st.sidebar.expander("🔧 Техническая информация"):
        st.markdown("""
        **Требования к данным:**
        - ADS: calculated_ads DataFrame
        - Остатки: stock_data DataFrame
        - Общие товары в обоих файлах
        
        **Алгоритм:**
        1. Классификация точек по типам
        2. Применение нормативов запасов
        3. Поиск дефицитов и излишков
        4. Генерация рекомендаций
        5. Приоритизация по важности
        """)

# ===== ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ =====

def show_demo_data_option():
    """Опция создания демо-данных для тестирования"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎭 Демо-режим")
    
    if st.sidebar.button("Создать демо-данные"):
        create_demo_data()
        st.success("✅ Демо-данные созданы!")
        st.rerun()

def create_demo_data():
    """Создание демо-данных для тестирования системы"""
    
    # Создаем демо ADS
    demo_ads = pd.DataFrame({
        'номенклатура': [
            'Конфирмат 6,3*50мм',
            '19*0,8мм ПВХ Белый кромка',
            '1,5*25мм Венге цаво',
            'Петля накладная',
            'Ручка мебельная 128мм'
        ],
        'ads': [125.7, 45.3, 15.5, 22.1, 18.9]
    })
    
    # Создаем демо остатки
    demo_stock = pd.DataFrame({
        'номенклатура': [
            'Конфирмат 6,3*50мм',
            '19*0,8мм ПВХ Белый кромка', 
            '1,5*25мм Венге цаво',
            'Петля накладная',
            'Ручка мебельная 128мм'
        ],
        'Магазин фурнитуры': [800, 150, 25, 50, 80],
        'ТД Казыбаева магазин': [600, 180, 30, 60, 70],
        'склад фурнитура № 1': [8500, 2100, 850, 1200, 950],
        'АО Склад TRADE': [3200, 1800, 420, 800, 640],
        'Хаб Шымкент': [15000, 3500, 1200, 2500, 1800]
    })
    
    # Создаем или получаем систему
    if 'inventory_system' not in st.session_state:
        # Создаем простую систему для демо
        class DemoSystem:
            def __init__(self):
                self.calculated_ads = demo_ads
                self.stock_data = demo_stock
        
        st.session_state.inventory_system = DemoSystem()
    else:
        # Обновляем существующую систему
        st.session_state.inventory_system.calculated_ads = demo_ads
        st.session_state.inventory_system.stock_data = demo_stock

# ===== ЗАПУСК СТРАНИЦЫ =====

if __name__ == "__main__":
    
    # Показываем дополнительную информацию в сайдбаре
    show_integration_info()
    
    # Показываем опцию демо-данных
    show_demo_data_option()
    
    # Запускаем основную логику
    main()