#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенное веб-приложение с улучшенной аналитикой
Включает анализ оборачиваемости, ABC анализ по категориям
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from webhook_data_accumulator import WebhookDataAccumulator
import json
import time

# Импорт системы инвентаризации
try:
    from modular_inventory_system import ModularInventorySystem
    INVENTORY_SYSTEM_AVAILABLE = True
except ImportError:
    INVENTORY_SYSTEM_AVAILABLE = False

# Конфигурация страницы
st.set_page_config(
    page_title="Система анализа с расширенной аналитикой",
    page_icon="📊",
    layout="wide"
)

# Словарь городов по филиалам
BRANCH_CITIES = {
    "База Склад Фурнитура Комплект": "Алматы",
    "Казыбаева Склад Фурнитура TRADE": "Алматы",
    "ТД Казыбаева ФУРНИТУРА магазин": "Алматы",
    "Барыс Склад Фурнитура TRADE": "Алматы",
    "АО Склад Фурнитура TRADE": "Алматы",
    "склад фурнитура № 1": "Астана",
    "Магазин фурнитуры": "Астана",
    "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"": "Шымкент",
    "6 Склад фурнитуры \"Овощная база\" Магазин продажи": "Шымкент"
}

def get_city_from_branch(branch_name):
    """Определение города по названию филиала"""
    for key, city in BRANCH_CITIES.items():
        if key in branch_name or branch_name in key:
            return city
    
    # Попытка определить по ключевым словам
    if "Шымкент" in branch_name:
        return "Шымкент"
    elif "Астана" in branch_name:
        return "Астана"
    elif any(word in branch_name for word in ["Казыбаева", "Барыс", "АО", "База"]):
        return "Алматы"
    
    return "Другой"

def calculate_turnover(stock_data, sales_data, period_days=30.5):
    """
    ИСПРАВЛЕНО: Расчет оборачиваемости по формуле: (остатки / продажи) * 30.5
    Где:
    - остатки - текущее количество товара на складе
    - продажи - общее количество продаж за период
    - 30.5 - фиксированный коэффициент (средний месяц)
    Результат - количество дней, за которые продается текущий остаток
    """
    if sales_data.empty or stock_data.empty:
        return pd.DataFrame()
    
    # Группируем продажи по товарам
    sales_summary = sales_data.groupby(['item_code', 'item_name']).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).reset_index()
    
    # Переименовываем для ясности
    sales_summary.rename(columns={'quantity': 'total_sales'}, inplace=True)
    
    # Группируем остатки по товарам
    stock_summary = stock_data.groupby(['item_code', 'item_name']).agg({
        'quantity': 'sum'
    }).reset_index()
    stock_summary.rename(columns={'quantity': 'stock_quantity'}, inplace=True)
    
    # Объединяем данные
    turnover_data = pd.merge(
        stock_summary,
        sales_summary,
        on=['item_code', 'item_name'],
        how='inner'
    )
    
    # Расчет оборачиваемости по формуле: (остатки / продажи) * 30.5
    turnover_data['turnover_days'] = np.where(
        turnover_data['total_sales'] > 0,
        (turnover_data['stock_quantity'] / turnover_data['total_sales']) * 30.5,
        999999  # Если нет продаж
    )
    
    # Для обратной совместимости добавляем поле daily_sales
    turnover_data['daily_sales'] = turnover_data['total_sales'] / period_days
    
    # Классификация оборачиваемости
    turnover_data['turnover_category'] = pd.cut(
        turnover_data['turnover_days'],
        bins=[0, 30, 60, 90, 180, 365, 999999],
        labels=['Высокая (< 30 дней)', 'Хорошая (30-60)', 'Средняя (60-90)', 
                'Низкая (90-180)', 'Очень низкая (180-365)', 'Критическая (> 365)']
    )
    
    return turnover_data

def calculate_abc_by_categories(sales_data, stock_data=None):
    """ABC анализ по категориям товаров"""
    if sales_data.empty:
        return pd.DataFrame()
    
    # Проверяем есть ли поле category в данных из БД
    if 'category' not in sales_data.columns:
        # Если нет категорий в данных, возвращаем пустой DataFrame
        return pd.DataFrame()
    
    # Заменяем пустые категории
    sales_with_category = sales_data.copy()
    sales_with_category['category'] = sales_with_category['category'].fillna('Без категории')
    sales_with_category['category'] = sales_with_category['category'].replace('', 'Без категории')
    
    # Группируем по категориям
    category_summary = sales_with_category.groupby('category').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'item_code': 'nunique'
    }).reset_index()
    
    category_summary.columns = ['Категория', 'Выручка', 'Количество', 'Товаров']
    
    # Сортируем по выручке
    category_summary = category_summary.sort_values('Выручка', ascending=False)
    
    # Расчет накопительной суммы и процентов
    category_summary['Накопительная выручка'] = category_summary['Выручка'].cumsum()
    total_revenue = category_summary['Выручка'].sum()
    category_summary['% от общей выручки'] = (category_summary['Выручка'] / total_revenue * 100).round(2)
    category_summary['Накопительный %'] = (category_summary['Накопительная выручка'] / total_revenue * 100).round(2)
    
    # ABC классификация
    category_summary['ABC'] = 'C'
    category_summary.loc[category_summary['Накопительный %'] <= 80, 'ABC'] = 'A'
    category_summary.loc[(category_summary['Накопительный %'] > 80) & (category_summary['Накопительный %'] <= 95), 'ABC'] = 'B'
    
    return category_summary

def parse_category_path(category_path):
    """Парсит путь категории в иерархию"""
    if pd.isna(category_path) or category_path == '':
        return ['Без категории']
    
    # Разделяем по слешам и очищаем пустые элементы
    parts = [part.strip() for part in str(category_path).split('/') if part.strip()]
    return parts if parts else ['Без категории']

def get_subcategories(sales_data, parent_path=None, level=0):
    """Получает подкатегории для данного уровня"""
    if 'category_path' not in sales_data.columns:
        return pd.DataFrame()
    
    # Парсим пути категорий
    category_data = []
    for idx, row in sales_data.iterrows():
        path_parts = parse_category_path(row['category_path'])
        
        # Если задан родительский путь, проверяем соответствие
        if parent_path:
            if len(path_parts) <= level or path_parts[:level] != parent_path:
                continue
        
        # Берем категорию на нужном уровне
        if len(path_parts) > level:
            current_category = path_parts[level]
            category_data.append({
                'category': current_category,
                'full_path': path_parts,
                'amount': row['amount'],
                'quantity': row['quantity'],
                'item_code': row['item_code'],
                'item_name': row['item_name']
            })
    
    if not category_data:
        return pd.DataFrame()
    
    # Преобразуем в DataFrame и группируем
    df = pd.DataFrame(category_data)
    
    result = df.groupby('category').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'item_code': 'nunique'
    }).reset_index()
    
    result.columns = ['Категория', 'Выручка', 'Количество', 'Товаров']
    result = result.sort_values('Выручка', ascending=False)
    
    # ABC классификация
    result['Накопительная выручка'] = result['Выручка'].cumsum()
    total_revenue = result['Выручка'].sum()
    result['% от общей выручки'] = (result['Выручка'] / total_revenue * 100).round(2)
    result['Накопительный %'] = (result['Накопительная выручка'] / total_revenue * 100).round(2)
    
    result['ABC'] = 'C'
    result.loc[result['Накопительный %'] <= 80, 'ABC'] = 'A'
    result.loc[(result['Накопительный %'] > 80) & (result['Накопительный %'] <= 95), 'ABC'] = 'B'
    
    return result

def get_items_in_category(sales_data, category_path):
    """Получает товары в конкретной категории"""
    if 'category_path' not in sales_data.columns:
        return pd.DataFrame()
    
    # Фильтруем данные по пути категории
    filtered_data = []
    for idx, row in sales_data.iterrows():
        path_parts = parse_category_path(row['category_path'])
        if len(path_parts) >= len(category_path) and path_parts[:len(category_path)] == category_path:
            filtered_data.append(row)
    
    if not filtered_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(filtered_data)
    
    # Группируем по товарам
    result = df.groupby(['item_code', 'item_name']).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    result.columns = ['Код товара', 'Наименование', 'Выручка', 'Количество']
    result = result.sort_values('Выручка', ascending=False)
    
    # ABC классификация товаров
    result['Накопительная выручка'] = result['Выручка'].cumsum()
    total_revenue = result['Выручка'].sum()
    result['% от общей выручки'] = (result['Выручка'] / total_revenue * 100).round(2)
    result['Накопительный %'] = (result['Накопительная выручка'] / total_revenue * 100).round(2)
    
    result['ABC'] = 'C'
    result.loc[result['Накопительный %'] <= 80, 'ABC'] = 'A'
    result.loc[(result['Накопительный %'] > 80) & (result['Накопительный %'] <= 95), 'ABC'] = 'B'
    
    return result

def calculate_turnover_by_city(stock_data, sales_data, period_days=30.5):
    """Расчет оборачиваемости по городам"""
    if sales_data.empty or stock_data.empty:
        return pd.DataFrame()
    
    # Добавляем города к данным
    sales_data['city'] = sales_data['branch'].apply(get_city_from_branch)
    stock_data['city'] = stock_data['warehouse'].apply(get_city_from_branch)
    
    # Группируем по городам
    sales_by_city = sales_data.groupby('city').agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).reset_index()
    sales_by_city.rename(columns={'quantity': 'total_sales'}, inplace=True)
    
    stock_by_city = stock_data.groupby('city').agg({
        'quantity': 'sum'
    }).reset_index()
    stock_by_city.rename(columns={'quantity': 'stock_quantity'}, inplace=True)
    
    # Объединяем
    city_turnover = pd.merge(
        stock_by_city,
        sales_by_city,
        on='city',
        how='inner'
    )
    
    # ИСПРАВЛЕНО: Расчет оборачиваемости по формуле: (остатки / продажи) * 30.5
    city_turnover['turnover_days'] = np.where(
        city_turnover['total_sales'] > 0,
        (city_turnover['stock_quantity'] / city_turnover['total_sales']) * 30.5,
        999999
    )
    
    # Для обратной совместимости добавляем поле daily_sales
    city_turnover['daily_sales'] = city_turnover['total_sales'] / period_days
    
    # Расчет стоимости остатков (примерная)
    city_turnover['stock_value'] = city_turnover['stock_quantity'] * (city_turnover['amount'] / city_turnover['total_sales'])
    
    return city_turnover

def calculate_turnover_by_branch(stock_data, sales_data, period_days=30.5):
    """
    Расчет оборачиваемости по филиалам
    Возвращает детальную оборачиваемость каждого товара в каждом филиале
    """
    if sales_data.empty or stock_data.empty:
        return pd.DataFrame()
    
    # Подготовка данных продаж по филиалам и товарам
    sales_by_branch = sales_data.groupby(['branch', 'item_code', 'item_name']).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).reset_index()
    sales_by_branch.rename(columns={'quantity': 'total_sales'}, inplace=True)
    
    # Подготовка данных остатков по филиалам и товарам
    # В остатках филиал называется 'warehouse'
    stock_by_branch = stock_data.groupby(['warehouse', 'item_code', 'item_name']).agg({
        'quantity': 'sum'
    }).reset_index()
    stock_by_branch.rename(columns={'warehouse': 'branch', 'quantity': 'stock_quantity'}, inplace=True)
    
    # Объединяем данные по филиалам и товарам
    branch_turnover = pd.merge(
        stock_by_branch,
        sales_by_branch,
        on=['branch', 'item_code', 'item_name'],
        how='outer'  # outer join чтобы видеть товары без продаж или остатков
    ).fillna(0)
    
    # Исключаем записи где и остатки и продажи = 0
    branch_turnover = branch_turnover[(branch_turnover['stock_quantity'] > 0) | (branch_turnover['total_sales'] > 0)]
    
    # Расчет оборачиваемости по формуле: (остатки / продажи) * 30.5
    branch_turnover['turnover_days'] = np.where(
        branch_turnover['total_sales'] > 0,
        (branch_turnover['stock_quantity'] / branch_turnover['total_sales']) * 30.5,
        999999  # Если нет продаж
    )
    
    # Для обратной совместимости добавляем поле daily_sales
    branch_turnover['daily_sales'] = branch_turnover['total_sales'] / period_days
    
    # Классификация оборачиваемости
    branch_turnover['turnover_category'] = pd.cut(
        branch_turnover['turnover_days'],
        bins=[0, 30, 60, 90, 180, 365, 999999],
        labels=['Высокая (< 30 дней)', 'Хорошая (30-60)', 'Средняя (60-90)', 
                'Низкая (90-180)', 'Очень низкая (180-365)', 'Критическая (> 365)']
    )
    
    # Добавляем информацию о городах
    branch_turnover['city'] = branch_turnover['branch'].apply(get_city_from_branch)
    
    return branch_turnover

# Инициализация накопителя данных
@st.cache_resource
def init_accumulator():
    accumulator = WebhookDataAccumulator()
    from webhook_data_accumulator import setup_auto_processing
    setup_auto_processing(accumulator)
    return accumulator

accumulator = init_accumulator()

# Автообновление
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

if datetime.now() - st.session_state.last_update > timedelta(minutes=5):
    st.session_state.last_update = datetime.now()
    st.rerun()

# Главный заголовок
st.title("📊 Расширенная система анализа")
st.caption(f"Последнее обновление: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Боковая панель
with st.sidebar:
    st.header("🔄 Управление данными")
    
    if st.button("🔄 Обновить данные", type="primary"):
        with st.spinner("Обновление..."):
            accumulator.monitor_and_process_new_files()
            st.success("✅ Данные обновлены")
            time.sleep(1)
            st.rerun()
    
    # Статистика
    summary = accumulator.get_data_summary()
    
    st.subheader("📊 Статистика базы данных")
    if summary['sales']['total_records'] > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Записей", f"{summary['sales']['total_records']:,}")
            st.metric("Дней", summary['sales']['days_count'])
        with col2:
            st.metric("Филиалов", summary['sales']['branches_count'])
            st.metric("Товаров", summary['sales']['items_count'])
        
        st.info(f"📅 {summary['sales']['first_date']} - {summary['sales']['last_date']}")
    
    # Фильтры периода с сохранением состояния
    st.subheader("⏱️ Период анализа")
    
    # Инициализация состояния периода
    if 'selected_period' not in st.session_state:
        st.session_state.selected_period = "Весь период"
    
    period_option = st.selectbox(
        "Выберите период",
        ["Последние 30 дней", "Последние 60 дней", "Последние 90 дней", 
         "Последние 180 дней", "Весь период"],
        index=["Последние 30 дней", "Последние 60 дней", "Последние 90 дней", 
               "Последние 180 дней", "Весь период"].index(st.session_state.selected_period),
        key="period_selector"
    )
    
    # Обновляем состояние
    st.session_state.selected_period = period_option
    
    # Рассчитываем даты
    end_date = datetime.now().date()
    if period_option == "Последние 30 дней":
        start_date = end_date - timedelta(days=30)
    elif period_option == "Последние 60 дней":
        start_date = end_date - timedelta(days=60)
    elif period_option == "Последние 90 дней":
        start_date = end_date - timedelta(days=90)
    elif period_option == "Последние 180 дней":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = None
        end_date = None

# Загружаем данные с индикатором прогресса
with st.spinner("Загрузка данных..."):
    try:
        # Показываем прогресс
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Загружаем продажи
        status_text.text("Загружаем данные о продажах...")
        progress_bar.progress(25)
        
        sales_data = accumulator.get_sales_data(
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None
        )
        
        progress_bar.progress(50)
        status_text.text("Загружаем данные об остатках...")
        
        # Загружаем остатки
        stock_data = accumulator.get_latest_stock()
        
        progress_bar.progress(75)
        status_text.text("Обработка данных...")
        
        # Обработка данных завершена
        
        progress_bar.progress(100)
        status_text.text("Данные загружены!")
        
        # Убираем индикаторы прогресса
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки данных: {e}")
        st.stop()

# Основные вкладки
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Общий анализ",
    "🔄 Оборачиваемость", 
    "📦 ABC категорий",
    "🔀 Межфилиальные перемещения",
    "📈 Детальная аналитика"
])

with tab1:
    st.header("📊 Общий анализ")
    
    if not sales_data.empty:
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        total_amount = sales_data['amount'].sum()
        total_qty = sales_data['quantity'].sum()
        unique_items = sales_data['item_code'].nunique()
        unique_branches = sales_data['branch'].nunique()
        
        with col1:
            st.metric("💰 Общие продажи", f"{total_amount:,.0f} ₸")
            
        with col2:
            st.metric("📦 Продано товаров", f"{total_qty:,.0f} шт")
        
        with col3:
            st.metric("🛍️ Уникальных SKU", f"{unique_items:,}")
        
        with col4:
            st.metric("🏪 Активных филиалов", unique_branches)
        
        # Динамика продаж
        st.subheader("📈 Динамика продаж")
        
        daily_sales = sales_data.groupby('date').agg({
            'amount': 'sum',
            'quantity': 'sum'
        }).reset_index()
        
        # График с двумя осями
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_sales['date'],
            y=daily_sales['amount'],
            mode='lines',
            name='Выручка (₸)',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_sales['date'],
            y=daily_sales['quantity'],
            mode='lines',
            name='Количество',
            line=dict(color='#ff7f0e', width=2),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Динамика продаж по дням',
            xaxis_title='Дата',
            yaxis_title='Выручка (₸)',
            yaxis2=dict(
                title='Количество (шт)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Топ товаров
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Топ-10 товаров по выручке")
            top_items_revenue = sales_data.groupby(['item_code', 'item_name']).agg({
                'amount': 'sum'
            }).reset_index().nlargest(10, 'amount')
            
            fig_top_revenue = px.bar(
                top_items_revenue, 
                y='item_name', 
                x='amount',
                orientation='h',
                title='Топ товаров по выручке',
                labels={'amount': 'Выручка (₸)', 'item_name': 'Товар'}
            )
            st.plotly_chart(fig_top_revenue, use_container_width=True)
        
        with col2:
            st.subheader("📦 Топ-10 товаров по количеству")
            top_items_qty = sales_data.groupby(['item_code', 'item_name']).agg({
                'quantity': 'sum'
            }).reset_index().nlargest(10, 'quantity')
            
            fig_top_qty = px.bar(
                top_items_qty,
                y='item_name',
                x='quantity',
                orientation='h',
                title='Топ товаров по количеству',
                labels={'quantity': 'Количество (шт)', 'item_name': 'Товар'}
            )
            st.plotly_chart(fig_top_qty, use_container_width=True)

with tab2:
    st.header("🔄 Анализ оборачиваемости")
    
    st.info("📋 **Формула оборачиваемости:** (Остатки ÷ Продажи) × 30.5 дней (средний месяц)")
    
    if not sales_data.empty and not stock_data.empty:
        # Выбор типа анализа
        analysis_type = st.selectbox(
            "🎯 Выберите тип анализа оборачиваемости:",
            ["📊 Общий анализ", "🏙️ По городам", "🏢 По филиалам"]
        )
        
        # Общий анализ оборачиваемости
        if analysis_type == "📊 Общий анализ":
            turnover_data = calculate_turnover(stock_data, sales_data, 30.5)
            
            if not turnover_data.empty:
                # Общие метрики оборачиваемости
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_turnover = turnover_data['turnover_days'].mean()
                    st.metric("📊 Средняя оборачиваемость", f"{avg_turnover:.1f} дней")
                
                with col2:
                    fast_items = len(turnover_data[turnover_data['turnover_days'] <= 30])
                    st.metric("⚡ Быстрые товары", f"{fast_items} SKU")
                
                with col3:
                    slow_items = len(turnover_data[turnover_data['turnover_days'] > 180])
                    st.metric("🐌 Медленные товары", f"{slow_items} SKU")
                
                with col4:
                    total_stock_value = (turnover_data['stock_quantity'] * turnover_data['amount'] / turnover_data['total_sales']).sum()
                    st.metric("💰 Стоимость остатков", f"{total_stock_value:,.0f} ₸")
                
                # График распределения оборачиваемости
                st.subheader("📊 Распределение товаров по оборачиваемости")
                
                turnover_distribution = turnover_data['turnover_category'].value_counts().reset_index()
                turnover_distribution.columns = ['category', 'count']
                
                fig_dist = px.bar(
                    turnover_distribution,
                    x='category',
                    y='count',
                    title='Распределение товаров по скорости оборачиваемости',
                    labels={'category': 'Категория оборачиваемости', 'count': 'Количество SKU'},
                    color='category',
                    color_discrete_map={
                        'Высокая (< 30 дней)': '#2ecc71',
                        'Хорошая (30-60)': '#3498db',
                        'Средняя (60-90)': '#f39c12',
                        'Низкая (90-180)': '#e74c3c',
                        'Очень низкая (180-365)': '#c0392b',
                        'Критическая (> 365)': '#7f8c8d'
                    }
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Детальная таблица
                st.subheader("📋 Детальный анализ оборачиваемости")
                
                # Фильтры
                col1, col2 = st.columns(2)
                with col1:
                    selected_categories = st.multiselect(
                        "Фильтр по категориям оборачиваемости",
                        options=turnover_data['turnover_category'].unique(),
                        default=turnover_data['turnover_category'].unique()
                    )
                
                with col2:
                    sort_by = st.selectbox(
                        "Сортировка",
                        ["Оборачиваемость (возр.)", "Оборачиваемость (убыв.)", 
                         "Остаток (убыв.)", "Выручка (убыв.)"]
                    )
                
                # Применяем фильтры
                filtered_turnover = turnover_data[turnover_data['turnover_category'].isin(selected_categories)]
                
                # Сортировка
                if sort_by == "Оборачиваемость (возр.)":
                    filtered_turnover = filtered_turnover.sort_values('turnover_days')
                elif sort_by == "Оборачиваемость (убыв.)":
                    filtered_turnover = filtered_turnover.sort_values('turnover_days', ascending=False)
                elif sort_by == "Остаток (убыв.)":
                    filtered_turnover = filtered_turnover.sort_values('stock_quantity', ascending=False)
                else:
                    filtered_turnover = filtered_turnover.sort_values('amount', ascending=False)
                
                # Форматирование для отображения
                display_turnover = filtered_turnover[['item_name', 'stock_quantity', 'total_sales', 
                                                     'turnover_days', 'turnover_category', 'amount']].copy()
                display_turnover.columns = ['Товар', 'Остаток', 'Общие продажи', 
                                           'Оборачиваемость (дней)', 'Категория', 'Выручка']
                
                # Форматирование чисел
                display_turnover['Остаток'] = display_turnover['Остаток'].round(0).astype(int)
                display_turnover['Общие продажи'] = display_turnover['Общие продажи'].round(2)
                display_turnover['Оборачиваемость (дней)'] = display_turnover['Оборачиваемость (дней)'].round(1)
                display_turnover['Выручка'] = display_turnover['Выручка'].round(0).astype(int)
                
                st.dataframe(display_turnover, hide_index=True, height=400)
                
                # Экспорт
                csv = filtered_turnover.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Скачать общий анализ",
                    data=csv,
                    file_name=f"turnover_general_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        # Анализ по городам
        elif analysis_type == "🏙️ По городам":
            city_turnover = calculate_turnover_by_city(stock_data, sales_data, 30.5)
            
            if not city_turnover.empty:
                st.subheader("🏙️ Выберите город для анализа")
                
                # Выбор города
                available_cities = sorted(city_turnover['city'].unique())
                selected_city = st.selectbox("Город:", available_cities)
                
                if selected_city:
                    # Фильтруем данные по городу
                    city_data = city_turnover[city_turnover['city'] == selected_city]
                    
                    # Метрики по городу
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🏙️ Город", selected_city)
                    with col2:
                        st.metric("📊 Средняя оборачиваемость", f"{city_data['turnover_days'].mean():.1f} дней")
                    with col3:
                        st.metric("📦 Общий остаток", f"{int(city_data['stock_quantity'].sum())} шт")
                    
                    # Таблица по городу
                    display_city = city_data[['city', 'stock_quantity', 'total_sales', 'turnover_days']].copy()
                    display_city.columns = ['Город', 'Остаток', 'Продажи', 'Оборачиваемость (дн)']
                    display_city['Остаток'] = display_city['Остаток'].round(0).astype(int)
                    display_city['Продажи'] = display_city['Продажи'].round(2)
                    display_city['Оборачиваемость (дн)'] = display_city['Оборачиваемость (дн)'].round(1)
                    
                    st.dataframe(display_city, hide_index=True)
                    
                    # Экспорт по городам
                    csv = city_data.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 Скачать анализ по городу {selected_city}",
                        data=csv,
                        file_name=f"turnover_city_{selected_city}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("⚠️ Недостаточно данных для анализа по городам")
        
        # Анализ по филиалам
        elif analysis_type == "🏢 По филиалам":
            branch_turnover = calculate_turnover_by_branch(stock_data, sales_data, 30.5)
            
            if not branch_turnover.empty:
                st.subheader("🏢 Выберите филиал для анализа")
                
                # Выбор филиала
                available_branches = sorted(branch_turnover['branch'].unique())
                selected_branch = st.selectbox("Филиал:", available_branches)
                
                if selected_branch:
                    # Фильтруем данные по филиалу
                    branch_data = branch_turnover[branch_turnover['branch'] == selected_branch]
                    
                    # Метрики по филиалу
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🏢 Филиал", selected_branch[:20] + "...")
                    with col2:
                        city = branch_data['city'].iloc[0] if not branch_data.empty else "Не определен"
                        st.metric("🏙️ Город", city)
                    with col3:
                        st.metric("📊 Средняя оборачиваемость", f"{branch_data['turnover_days'].mean():.1f} дней")
                    with col4:
                        st.metric("📦 Общий остаток", f"{int(branch_data['stock_quantity'].sum())} шт")
                    
                    # Фильтры для товаров в филиале
                    col1, col2 = st.columns(2)
                    with col1:
                        # Фильтр по категориям оборачиваемости
                        available_categories = branch_data['turnover_category'].unique()
                        selected_categories = st.multiselect(
                            "Категории оборачиваемости",
                            options=available_categories,
                            default=available_categories
                        )
                    with col2:
                        # Поиск по товару
                        search_item = st.text_input("🔍 Поиск товара", "")
                    
                    # Применяем фильтры
                    filtered_branch_data = branch_data[branch_data['turnover_category'].isin(selected_categories)]
                    
                    if search_item:
                        filtered_branch_data = filtered_branch_data[
                            filtered_branch_data['item_name'].str.contains(search_item, case=False, na=False)
                        ]
                    
                    if not filtered_branch_data.empty:
                        # Таблица товаров в филиале
                        st.subheader(f"📋 Товары в филиале: {selected_branch}")
                        
                        display_branch = filtered_branch_data[[
                            'item_name', 'stock_quantity', 'total_sales', 
                            'turnover_days', 'turnover_category'
                        ]].copy()
                        display_branch.columns = [
                            'Товар', 'Остаток', 'Продажи', 'Оборачиваемость (дн)', 'Категория'
                        ]
                        
                        # Форматирование
                        display_branch['Остаток'] = display_branch['Остаток'].round(0).astype(int)
                        display_branch['Продажи'] = display_branch['Продажи'].round(2)
                        display_branch['Оборачиваемость (дн)'] = display_branch['Оборачиваемость (дн)'].round(1)
                        
                        # Сортировка
                        sort_option = st.selectbox(
                            "Сортировка",
                            ["Оборачиваемость (возр.)", "Оборачиваемость (убыв.)", 
                             "Остаток (убыв.)", "Продажи (убыв.)"]
                        )
                        
                        if sort_option == "Оборачиваемость (возр.)":
                            display_branch = display_branch.sort_values('Оборачиваемость (дн)')
                        elif sort_option == "Оборачиваемость (убыв.)":
                            display_branch = display_branch.sort_values('Оборачиваемость (дн)', ascending=False)
                        elif sort_option == "Остаток (убыв.)":
                            display_branch = display_branch.sort_values('Остаток', ascending=False)
                        else:
                            display_branch = display_branch.sort_values('Продажи', ascending=False)
                        
                        st.dataframe(display_branch, hide_index=True, height=500)
                        
                        # График распределения в филиале
                        if len(filtered_branch_data) > 1:
                            st.subheader("📊 Распределение оборачиваемости в филиале")
                            
                            fig_branch = px.histogram(
                                filtered_branch_data,
                                x='turnover_days',
                                nbins=20,
                                title=f'Распределение оборачиваемости в филиале {selected_branch}',
                                labels={'turnover_days': 'Оборачиваемость (дней)', 'count': 'Количество товаров'}
                            )
                            st.plotly_chart(fig_branch, use_container_width=True)
                        
                        # Экспорт по филиалу
                        csv = filtered_branch_data.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label=f"📥 Скачать анализ филиала",
                            data=csv,
                            file_name=f"turnover_branch_{selected_branch[:10]}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("⚠️ Нет товаров по выбранным фильтрам")
            else:
                st.warning("⚠️ Недостаточно данных для анализа по филиалам")
    else:
        st.warning("⚠️ Недостаточно данных для анализа оборачиваемости")

with tab3:
    st.header("📦 ABC анализ по категориям")
    
    if not sales_data.empty:
        # Простой ABC анализ без иерархии
        st.subheader("📊 ABC анализ товаров")
        
        # Группируем товары по выручке
        abc_data = sales_data.groupby(['item_code', 'item_name']).agg({
            'quantity': 'sum',
            'amount': 'sum'
        }).reset_index()
        
        # Сортируем по выручке
        abc_data = abc_data.sort_values('amount', ascending=False)
        
        # Рассчитываем накопительную долю
        abc_data['cumsum_amount'] = abc_data['amount'].cumsum()
        total_amount = abc_data['amount'].sum()
        abc_data['percent'] = (abc_data['cumsum_amount'] / total_amount * 100)
        
        # Присваиваем ABC класс
        abc_data['ABC'] = 'C'
        abc_data.loc[abc_data['percent'] <= 80, 'ABC'] = 'A'
        abc_data.loc[(abc_data['percent'] > 80) & (abc_data['percent'] <= 95), 'ABC'] = 'B'
        
        # Метрики ABC
        a_items = abc_data[abc_data['ABC'] == 'A']
        b_items = abc_data[abc_data['ABC'] == 'B']
        c_items = abc_data[abc_data['ABC'] == 'C']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🅰️ Группа A", f"{len(a_items)} товаров", 
                     f"{(a_items['amount'].sum()/total_amount*100):.1f}% выручки")
        with col2:
            st.metric("🅱️ Группа B", f"{len(b_items)} товаров", 
                     f"{(b_items['amount'].sum()/total_amount*100):.1f}% выручки")
        with col3:
            st.metric("🅾️ Группа C", f"{len(c_items)} товаров", 
                     f"{(c_items['amount'].sum()/total_amount*100):.1f}% выручки")
        
        # График ABC
        fig_abc = px.bar(
            abc_data.groupby('ABC').size().reset_index(name='count'),
            x='ABC',
            y='count',
            title='Распределение товаров по группам ABC',
            color='ABC',
            color_discrete_map={'A': '#2ecc71', 'B': '#f39c12', 'C': '#e74c3c'}
        )
        st.plotly_chart(fig_abc, use_container_width=True)
        
        # Фильтр по группам ABC
        selected_abc = st.multiselect(
            "Выберите группы ABC:",
            options=['A', 'B', 'C'],
            default=['A', 'B', 'C']
        )
        
        filtered_abc = abc_data[abc_data['ABC'].isin(selected_abc)]
        
        # Таблица ABC
        display_abc = filtered_abc[['item_name', 'ABC', 'amount', 'quantity', 'percent']].copy()
        display_abc.columns = ['Товар', 'ABC', 'Выручка', 'Количество', '% накопительно']
        display_abc['Выручка'] = display_abc['Выручка'].round(0).astype(int)
        display_abc['Количество'] = display_abc['Количество'].round(0).astype(int)
        display_abc['% накопительно'] = display_abc['% накопительно'].round(1)
        
        st.dataframe(display_abc, hide_index=True, height=400)
        
        # Экспорт ABC
        csv = filtered_abc.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Скачать ABC анализ",
            data=csv,
            file_name=f"abc_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Недостаточно данных для ABC анализа")

with tab4:
    st.header("🔀 Межфилиальные перемещения")
    st.info("🚧 Этот раздел находится в разработке")

with tab5:
    st.header("📈 Детальная аналитика")
    
    if not sales_data.empty:
        # Подготовка данных для анализа
        sample_data = sales_data
        
        # Тепловая карта продаж по дням месяца
        st.subheader("🔥 Тепловая карта продаж")
        
        # Подготовка данных для тепловой карты
        sample_data_copy = sample_data.copy()
        sample_data_copy['date'] = pd.to_datetime(sample_data_copy['date'])
        sample_data_copy['day'] = sample_data_copy['date'].dt.day
        sample_data_copy['month_year'] = sample_data_copy['date'].dt.strftime('%Y-%m')
        
        # Агрегируем по дням месяца и месяцам
        heatmap_data = sample_data_copy.groupby(['month_year', 'day'])['amount'].sum().reset_index()
        
        if not heatmap_data.empty:
            # Создаем pivot таблицу для тепловой карты
            heatmap_pivot = heatmap_data.pivot(index='month_year', columns='day', values='amount')
            heatmap_pivot = heatmap_pivot.fillna(0)
            
            # Показываем только существующие дни
            existing_days = sorted(heatmap_data['day'].unique())
            heatmap_pivot = heatmap_pivot[existing_days]
            
            if len(heatmap_pivot) > 0:
                # Создаем тепловую карту
                fig_heatmap = px.imshow(
                    heatmap_pivot,
                    title=f'Тепловая карта продаж по дням ({len(existing_days)} дней, {len(heatmap_pivot)} месяцев)',
                    labels=dict(x="День месяца", y="Период", color="Выручка (₸)"),
                    aspect="auto",
                    color_continuous_scale="Viridis"
                )
                
                fig_heatmap.update_layout(height=400)
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Анализ лучших дней
                st.subheader("📊 Анализ по дням месяца")
                
                daily_stats = heatmap_data.groupby('day')['amount'].agg(['sum', 'mean', 'count']).reset_index()
                daily_stats.columns = ['День', 'Общая выручка', 'Средняя выручка', 'Количество месяцев']
                daily_stats = daily_stats.sort_values('Общая выручка', ascending=False)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if not daily_stats.empty:
                        best_day = daily_stats.iloc[0]
                        st.metric("🏆 Лучший день месяца", f"{int(best_day['День'])} число")
                        st.caption(f"{best_day['Общая выручка']:,.0f} ₸")
                
                with col2:
                    avg_daily = daily_stats['Средняя выручка'].mean()
                    st.metric("📊 Средняя выручка/день", f"{avg_daily:,.0f} ₸")
                
                with col3:
                    max_day = daily_stats.loc[daily_stats['Общая выручка'].idxmax()]
                    st.metric("💰 Максимум за день", f"{int(max_day['День'])} число")
                    st.caption(f"{max_day['Общая выручка']:,.0f} ₸")
                
            else:
                st.warning("⚠️ Нет данных для построения тепловой карты")
        else:
            st.warning("⚠️ Нет данных о ежедневных продажах")
    else:
        st.warning("⚠️ Нет данных для анализа")