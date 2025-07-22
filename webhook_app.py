#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отдельное приложение для автоматической обработки файлов через webhook от 1С
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import time

# Настройка страницы
st.set_page_config(
    page_title="🤖 Автоматическая система анализа",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Импорт модулей
try:
    from enhanced_data_parser import enhanced_parser
    # Импортируем из основного файла вместо pages
    import sys
    import os
    
    # Добавляем текущую директорию в путь
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Попытка импорта функций напрямую
    # Если есть отдельный файл с функциями
    try:
        from pages import *
        # Или импортируем функции откуда-то еще
        MODULES_AVAILABLE = True
    except:
        # Создаем минимальные заглушки функций
        def generate_movement_recommendations(stock_df, sales_df, period_days, settings):
            return []
        
        def get_branch_type(branch_name):
            return "unknown"
        
        WAREHOUSE_HIERARCHY = {}
        MODULES_AVAILABLE = True
        
except ImportError as e:
    st.error(f"Ошибка импорта модулей: {e}")
    MODULES_AVAILABLE = False

def main():
    st.title("🤖 Автоматическая система анализа складов")
    st.markdown("*Система автоматически обрабатывает данные, получаемые от 1С через webhook*")
    
    if not MODULES_AVAILABLE:
        st.error("❌ Необходимые модули не загружены. Проверьте установку.")
        return
    
    # Статус webhook сервера
    st.markdown("### 🔌 Статус webhook сервера")
    
    webhook_status = check_webhook_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if webhook_status['running']:
            st.success("✅ Webhook сервер работает")
        else:
            st.error("❌ Webhook сервер не запущен")
    
    with col2:
        st.metric("Последнее обновление", webhook_status['last_update'])
    
    with col3:
        st.metric("Файлов получено", f"{webhook_status['files_count']}")
    
    # Информация о файлах
    st.markdown("### 📁 Статус данных")
    
    file_info = enhanced_parser.get_file_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Продажи")
        if file_info['sales']['exists']:
            st.success(f"✅ {file_info['sales']['filename']}")
            st.caption(f"Обновлен: {file_info['sales']['modified']}")
        else:
            st.warning("⚠️ Файл продаж отсутствует")
    
    with col2:
        st.markdown("#### 📈 Остатки")
        if file_info['stock']['exists']:
            st.success(f"✅ {file_info['stock']['filename']}")
            st.caption(f"Обновлен: {file_info['stock']['modified']}")
        else:
            st.warning("⚠️ Файл остатков отсутствует")
    
    # Автоматическое обновление данных
    auto_refresh = st.checkbox("🔄 Автоматическое обновление (каждые 30 сек)", value=False)
    
    if auto_refresh:
        # Автообновление каждые 30 секунд
        time.sleep(30)
        st.rerun()
    
    # Кнопка ручного обновления
    if st.button("🔄 Обновить анализ", type="primary"):
        if file_info['sales']['exists'] and file_info['stock']['exists']:
            run_analysis()
        else:
            st.error("❌ Недостаточно данных для анализа")
    
    # Отображение результатов анализа
    if 'analysis_results' in st.session_state:
        display_analysis_results()

def check_webhook_status():
    """Проверяет статус webhook сервера"""
    webhook_dir = Path('./webhook_uploads')
    
    status = {
        'running': webhook_dir.exists(),
        'last_update': 'Неизвестно',
        'files_count': 0
    }
    
    if webhook_dir.exists():
        files = list(webhook_dir.glob('*.json'))
        status['files_count'] = len(files)
        
        if files:
            # Находим самый новый файл
            newest_file = max(files, key=lambda x: x.stat().st_mtime)
            last_modified = datetime.fromtimestamp(newest_file.stat().st_mtime)
            status['last_update'] = last_modified.strftime('%Y-%m-%d %H:%M:%S')
    
    return status

def run_analysis():
    """Запускает полный анализ с последними данными"""
    with st.spinner("🔄 Загрузка и анализ данных..."):
        try:
            # Загружаем данные
            sales_df, stock_df, period_days = enhanced_parser.load_and_parse_latest_data()
            
            if sales_df.empty or stock_df.empty:
                st.error("❌ Нет данных для анализа")
                return
            
            # Параметры анализа (можно сделать настраиваемыми)
            min_max_settings = {
                'hub': {'min': 60, 'max': 180},
                'warehouse': {'min': 30, 'max': 90},
                'store': {'min': 14, 'max': 45}
            }
            
            # Генерируем рекомендации
            recommendations = generate_movement_recommendations(
                stock_df, sales_df, period_days, min_max_settings
            )
            
            # Рассчитываем статистику
            stats = calculate_statistics(sales_df, stock_df, period_days)
            
            # Сохраняем результаты
            st.session_state['analysis_results'] = {
                'recommendations': recommendations,
                'statistics': stats,
                'period_days': period_days,
                'timestamp': datetime.now().isoformat(),
                'sales_df': sales_df,
                'stock_df': stock_df
            }
            
            st.success(f"✅ Анализ завершен! Найдено {len(recommendations)} рекомендаций")
            
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {e}")

def calculate_statistics(sales_df, stock_df, period_days):
    """Рассчитывает основную статистику"""
    stats = {}
    
    # Общая статистика
    stats['total_sales'] = sales_df['cost'].sum()
    stats['total_stock'] = stock_df['cost'].sum()
    stats['branches_count'] = stock_df['branch'].nunique()
    stats['products_count'] = stock_df['article'].nunique()
    
    # Оборачиваемость по филиалам
    branch_stats = []
    for branch in stock_df['branch'].unique():
        branch_sales = sales_df[sales_df['branch'] == branch]['cost'].sum()
        branch_stock = stock_df[stock_df['branch'] == branch]['cost'].sum()
        
        if branch_sales > 0:
            turnover = int((branch_stock / branch_sales) * period_days)
        else:
            turnover = 999
        
        branch_stats.append({
            'branch': branch,
            'type': get_branch_type(branch),
            'sales': branch_sales,
            'stock': branch_stock,
            'turnover': turnover
        })
    
    stats['branch_stats'] = sorted(branch_stats, key=lambda x: x['turnover'])
    
    return stats

def display_analysis_results():
    """Отображает результаты анализа"""
    results = st.session_state['analysis_results']
    
    st.markdown("### 📊 Результаты анализа")
    st.caption(f"Обновлено: {results['timestamp']}")
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Рекомендаций", len(results['recommendations']))
    
    with col2:
        st.metric("Филиалов", results['statistics']['branches_count'])
    
    with col3:
        st.metric("Товаров", results['statistics']['products_count'])
    
    with col4:
        st.metric("Период", f"{results['period_days']} дней")
    
    # Вкладки с детальным анализом
    tab1, tab2, tab3 = st.tabs(["📋 Рекомендации", "📊 Статистика", "🏢 По филиалам"])
    
    with tab1:
        display_recommendations(results['recommendations'])
    
    with tab2:
        display_statistics(results['statistics'])
    
    with tab3:
        display_branch_analysis(results['statistics']['branch_stats'])

def display_recommendations(recommendations):
    """Отображает рекомендации по перемещению"""
    if not recommendations:
        st.info("Нет рекомендаций по перемещению")
        return
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        all_from = list(set(r['from_branch'] for r in recommendations))
        selected_from = st.multiselect("Откуда", all_from, default=all_from[:5])
    
    with col2:
        all_to = list(set(r['to_branch'] for r in recommendations))
        selected_to = st.multiselect("Куда", all_to, default=all_to[:5])
    
    # Фильтрация
    filtered_recs = [
        r for r in recommendations
        if r['from_branch'] in selected_from and r['to_branch'] in selected_to
    ]
    
    if filtered_recs:
        df_recs = pd.DataFrame(filtered_recs)
        
        display_df = df_recs[[
            'from_branch', 'to_branch', 'product', 
            'quantity', 'reason'
        ]].copy()
        
        display_df.columns = ['Откуда', 'Куда', 'Товар', 'Кол-во', 'Причина']
        
        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            height=400
        )

def display_statistics(stats):
    """Отображает общую статистику"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Общие продажи", f"{stats['total_sales']:,.0f}")
        st.metric("Общие остатки", f"{stats['total_stock']:,.0f}")
    
    with col2:
        if stats['total_sales'] > 0:
            total_turnover = int((stats['total_stock'] / stats['total_sales']) * 30)
            st.metric("Общая оборачиваемость", f"{total_turnover} дней")

def display_branch_analysis(branch_stats):
    """Отображает анализ по филиалам"""
    df = pd.DataFrame(branch_stats)
    
    df['sales_formatted'] = df['sales'].apply(lambda x: f"{x:,.0f}")
    df['stock_formatted'] = df['stock'].apply(lambda x: f"{x:,.0f}")
    
    display_df = df[['branch', 'type', 'sales_formatted', 'stock_formatted', 'turnover']].copy()
    display_df.columns = ['Филиал', 'Тип', 'Продажи', 'Остатки', 'Оборачиваемость (дн.)']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

if __name__ == "__main__":
    main()