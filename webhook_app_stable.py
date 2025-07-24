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
    Расчет оборачиваемости по формуле: (остатки / продажи) * период
    Период = 30.5 дней (средний месяц)
    Результат - количество дней, за которые продается текущий остаток
    """
    if sales_data.empty or stock_data.empty:
        return pd.DataFrame()
    
    # Группируем продажи по товарам
    sales_summary = sales_data.groupby(['item_code', 'item_name']).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).reset_index()
    
    # Средние продажи за день
    sales_summary['daily_sales'] = sales_summary['quantity'] / period_days
    
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
    
    # Расчет оборачиваемости
    turnover_data['turnover_days'] = np.where(
        turnover_data['daily_sales'] > 0,
        turnover_data['stock_quantity'] / turnover_data['daily_sales'],
        999999  # Если нет продаж
    )
    
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
    sales_by_city['daily_sales'] = sales_by_city['quantity'] / period_days
    
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
    
    # Расчет оборачиваемости
    city_turnover['turnover_days'] = np.where(
        city_turnover['daily_sales'] > 0,
        city_turnover['stock_quantity'] / city_turnover['daily_sales'],
        999999
    )
    
    # Расчет стоимости остатков (примерная)
    city_turnover['stock_value'] = city_turnover['stock_quantity'] * (city_turnover['amount'] / city_turnover['quantity'])
    
    return city_turnover

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
    
    # Рассчитываем даты на основе имеющихся данных
    # Сначала получаем информацию о доступных данных
    data_summary = accumulator.get_data_summary()
    
    if data_summary['sales']['last_date']:
        # Используем последнюю дату из данных как конечную точку
        end_date = pd.to_datetime(data_summary['sales']['last_date']).date()
    else:
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Общий анализ",
    "🔄 Оборачиваемость", 
    "🏙️ Анализ по городам",
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
        
        if sales_data.empty:
            st.warning("Нет данных о продажах за выбранный период")
        else:
            daily_sales = sales_data.groupby('date').agg({
                'amount': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            # Сортируем по дате для правильного отображения
            daily_sales = daily_sales.sort_values('date')
            
            # Показываем статистику по периоду
            st.info(f"📊 Данные за период: {daily_sales['date'].min()} - {daily_sales['date'].max()} ({len(daily_sales)} дней)")
        
            # График с двумя осями (только если есть данные)
            if not daily_sales.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=daily_sales['date'],
                    y=daily_sales['amount'],
                    mode='lines+markers',
                    name='Выручка (₸)',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4)
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_sales['date'],
                    y=daily_sales['quantity'],
                    mode='lines+markers',
                    name='Количество',
                    line=dict(color='#ff7f0e', width=2),
                    marker=dict(size=4),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title=f'Динамика продаж по дням ({len(daily_sales)} точек данных)',
                    xaxis_title='Дата',
                    yaxis_title='Выручка (₸)',
                    yaxis2=dict(
                        title='Количество (шт)',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Нет данных для построения графика динамики")
        
        # Отладочная информация (можно убрать после исправления)
        with st.expander("🔍 Отладочная информация"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Параметры запроса:**")
                st.write(f"- Начальная дата: {start_date}")
                st.write(f"- Конечная дата: {end_date}")
                st.write(f"- Выбранный период: {period_option}")
            
            with col2:
                st.write("**Статистика данных:**")
                if not sales_data.empty:
                    st.write(f"- Записей загружено: {len(sales_data)}")
                    st.write(f"- Уникальных дат: {sales_data['date'].nunique()}")
                    st.write(f"- Первая дата: {sales_data['date'].min()}")
                    st.write(f"- Последняя дата: {sales_data['date'].max()}")
                else:
                    st.write("- Нет данных для отображения")
        
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
        # Расчет периода - используем 30.5 дней как средний месяц
        period_days = 30.5  # Стандартный период - средний месяц
        
        # Расчет оборачиваемости
        turnover_data = calculate_turnover(stock_data, sales_data, period_days)
        
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
                total_stock_value = (turnover_data['stock_quantity'] * turnover_data['amount'] / turnover_data['quantity']).sum()
                st.metric("💰 Стоимость остатков", f"{total_stock_value:,.0f} ₸")
            
            # График распределения оборачиваемости
            st.subheader("📊 Распределение товаров по оборачиваемости")
            
            turnover_distribution = turnover_data['turnover_category'].value_counts().reset_index()
            
            # Исправляем названия колонок для совместимости
            if 'index' not in turnover_distribution.columns:
                turnover_distribution.columns = ['category_name', 'count']
            else:
                turnover_distribution.columns = ['category_name', 'count']
            
            fig_dist = px.bar(
                turnover_distribution,
                x='category_name',
                y='count',
                title='Распределение товаров по скорости оборачиваемости',
                labels={'category_name': 'Категория оборачиваемости', 'count': 'Количество SKU'},
                color='category_name',
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
            display_turnover = filtered_turnover[['item_name', 'stock_quantity', 'daily_sales', 
                                                 'turnover_days', 'turnover_category', 'amount']].copy()
            display_turnover.columns = ['Товар', 'Остаток', 'Продажи/день', 
                                       'Оборачиваемость (дней)', 'Категория', 'Выручка']
            
            # Форматирование чисел
            display_turnover['Остаток'] = display_turnover['Остаток'].round(0).astype(int)
            display_turnover['Продажи/день'] = display_turnover['Продажи/день'].round(2)
            display_turnover['Оборачиваемость (дней)'] = display_turnover['Оборачиваемость (дней)'].round(1)
            display_turnover['Выручка'] = display_turnover['Выручка'].round(0).astype(int)
            
            st.dataframe(display_turnover, hide_index=True, height=400)
            
            # Экспорт
            csv = filtered_turnover.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Скачать анализ оборачиваемости",
                data=csv,
                file_name=f"turnover_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ Недостаточно данных для анализа оборачиваемости")

with tab3:
    st.header("🏙️ Анализ по городам")
    
    if not sales_data.empty and not stock_data.empty:
        # Расчет оборачиваемости по городам (используем стандартный период 30.5 дней)
        city_turnover = calculate_turnover_by_city(stock_data, sales_data, 30.5)
        
        if not city_turnover.empty:
            # Метрики по городам
            st.subheader("📊 Показатели по городам")
            
            for idx, city_row in city_turnover.iterrows():
                city = city_row['city']
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(f"🏙️ {city}", f"{city_row['amount']:,.0f} ₸", "Выручка")
                
                with col2:
                    st.metric("📦 Остатки", f"{city_row['stock_quantity']:,.0f} шт")
                
                with col3:
                    st.metric("🔄 Оборачиваемость", f"{city_row['turnover_days']:.1f} дней")
                
                with col4:
                    st.metric("💰 Стоимость остатков", f"{city_row['stock_value']:,.0f} ₸")
            
            # Сравнительные графики
            col1, col2 = st.columns(2)
            
            with col1:
                # График выручки по городам
                fig_revenue = px.pie(
                    city_turnover,
                    values='amount',
                    names='city',
                    title='Распределение выручки по городам'
                )
                st.plotly_chart(fig_revenue, use_container_width=True)
            
            with col2:
                # График оборачиваемости по городам
                fig_turnover = px.bar(
                    city_turnover,
                    x='city',
                    y='turnover_days',
                    title='Оборачиваемость по городам (дней)',
                    labels={'turnover_days': 'Дней', 'city': 'Город'},
                    color='turnover_days',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_turnover, use_container_width=True)
            
            # Детальный анализ по выбранному городу
            st.subheader("🔍 Детальный анализ по городу")
            
            selected_city = st.selectbox("Выберите город", city_turnover['city'].tolist())
            
            if selected_city:
                # Фильтруем данные по городу
                city_sales = sales_data[sales_data['branch'].apply(get_city_from_branch) == selected_city]
                city_stock = stock_data[stock_data['warehouse'].apply(get_city_from_branch) == selected_city]
                
                # Топ товаров в городе
                city_top_items = city_sales.groupby(['item_code', 'item_name']).agg({
                    'amount': 'sum',
                    'quantity': 'sum'
                }).reset_index().nlargest(10, 'amount')
                
                fig_city_top = px.bar(
                    city_top_items,
                    y='item_name',
                    x='amount',
                    orientation='h',
                    title=f'Топ-10 товаров в городе {selected_city}',
                    labels={'amount': 'Выручка (₸)', 'item_name': 'Товар'}
                )
                st.plotly_chart(fig_city_top, use_container_width=True)
    else:
        st.warning("⚠️ Недостаточно данных для анализа по городам")

with tab4:
    st.header("📦 ABC анализ по категориям")
    
    if not sales_data.empty and 'category_path' in sales_data.columns:
        # Инициализация навигации и постоянного кеша
        if 'abc_current_path' not in st.session_state:
            st.session_state.abc_current_path = []
        if 'abc_cache' not in st.session_state:
            st.session_state.abc_cache = {}
        
        # Путь к файлу постоянного кеша
        import os
        import hashlib
        
        CACHE_DIR = "/tmp/abc_cache"
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        def get_data_hash(df):
            """Создает хеш данных для определения изменений"""
            return hashlib.md5(str(df.shape[0]).encode() + str(df['amount'].sum()).encode()).hexdigest()[:10]
        
        def save_persistent_cache(cache_key, data, data_hash):
            """Сохраняет анализ в постоянный файл"""
            try:
                cache_file = os.path.join(CACHE_DIR, f"abc_{cache_key}_{data_hash}.json")
                
                # Преобразуем DataFrame в словарь для JSON
                if isinstance(data[0], pd.DataFrame):
                    df_dict = data[0].to_dict('records')
                    breadcrumbs = data[1]
                    cache_data = {'dataframe': df_dict, 'breadcrumbs': breadcrumbs}
                    
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, default=str)
                    
                    return cache_file
            except Exception as e:
                st.warning(f"⚠️ Не удалось сохранить кеш: {e}")
            return None
        
        def load_persistent_cache(cache_key, data_hash):
            """Загружает анализ из постоянного файла"""
            try:
                cache_file = os.path.join(CACHE_DIR, f"abc_{cache_key}_{data_hash}.json")
                
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # Восстанавливаем DataFrame из словаря
                    df = pd.DataFrame(cache_data['dataframe'])
                    breadcrumbs = cache_data['breadcrumbs']
                    
                    return (df, breadcrumbs)
            except Exception as e:
                st.warning(f"⚠️ Не удалось загрузить кеш: {e}")
            return None
        
        def clean_old_cache_files():
            """Очищает старые файлы кеша (старше 24 часов)"""
            try:
                import time
                current_time = time.time()
                for filename in os.listdir(CACHE_DIR):
                    file_path = os.path.join(CACHE_DIR, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > 24 * 3600:  # 24 часа
                            os.remove(file_path)
            except Exception:
                pass  # Игнорируем ошибки очистки
        
        def calculate_abc_with_hierarchy(_sales_df, level_path=None):
            """Расчет ABC анализа с поддержкой иерархии и постоянного кеширования"""
            if level_path is None:
                level_path = []
            
            # Создаем ключ для кеша и хеш данных
            safe_path = '_'.join([p.replace(' ', '_').replace('/', '_') for p in level_path])
            cache_key = f"{len(level_path)}_{safe_path}" if safe_path else f"{len(level_path)}_root"
            data_hash = get_data_hash(_sales_df)
            
            # Проверяем session_state кеш
            session_cache_key = f"abc_{cache_key}"
            if session_cache_key in st.session_state.abc_cache:
                return st.session_state.abc_cache[session_cache_key]
            
            # Проверяем постоянный кеш
            persistent_result = load_persistent_cache(cache_key, data_hash)
            if persistent_result is not None:
                # Сохраняем в session_state для быстрого доступа
                st.session_state.abc_cache[session_cache_key] = persistent_result
                return persistent_result
            
            # Создаем копию данных
            df_work = _sales_df.copy()
            
            # Определяем текущий уровень для анализа (обратный порядок в JSON)
            current_level = len(level_path)
            categories_data = []
            
            for _, row in df_work.iterrows():
                if pd.isna(row['category_path']) or row['category_path'] == '':
                    continue
                
                # Разбиваем путь категорий (в JSON путь от конкретного к общему)
                parts = [p.strip() for p in str(row['category_path']).split('/') if p.strip()]
                
                # В JSON структура: "Конкретная/Подкатегория/Основная/Мебельная фурнитура/"
                # Нам нужна "Основная" как корневая категория, а "Мебельная фурнитура" - это всегда последняя
                if len(parts) > 1 and parts[-1] == "Мебельная фурнитура":
                    # Убираем "Мебельная фурнитура" и разворачиваем остальное
                    actual_parts = parts[:-1]  # Убираем последний элемент
                    parts = list(reversed(actual_parts))  # Разворачиваем
                else:
                    # Если структура другая, просто разворачиваем
                    parts = list(reversed(parts))
                
                # Проверяем соответствие текущему пути навигации
                if level_path:
                    # Проверяем что путь соответствует
                    path_matches = True
                    for i, path_part in enumerate(level_path):
                        if i >= len(parts) or parts[i] != path_part:
                            path_matches = False
                            break
                    if not path_matches:
                        continue
                
                # Берем категорию нужного уровня
                if len(parts) > current_level:
                    category_name = parts[current_level]
                    categories_data.append({
                        'category': category_name,
                        'amount': row['amount'],
                        'quantity': row['quantity'],
                        'full_path': '/'.join(parts[:current_level+1]),
                        'has_children': len(parts) > current_level + 1,
                        'item_code': row.get('item_code', ''),
                        'item_name': row.get('item_name', ''),
                        'original_parts': parts  # Для отладки
                    })
                elif len(parts) == current_level and current_level > 0:
                    # Это товары на последнем уровне
                    categories_data.append({
                        'category': f"{row.get('item_code', 'N/A')} - {row.get('item_name', 'N/A')}",
                        'amount': row['amount'],
                        'quantity': row['quantity'],
                        'full_path': '',
                        'has_children': False,
                        'item_code': row.get('item_code', ''),
                        'item_name': row.get('item_name', ''),
                        'original_parts': parts
                    })
            
            if not categories_data:
                return pd.DataFrame(), []
            
            # Группируем данные
            cat_df = pd.DataFrame(categories_data)
            
            # Если это уровень товаров (нет детей), группируем по товарам
            if not cat_df['has_children'].any() and current_level > 0:
                # Уровень товаров
                category_summary = cat_df.groupby(['item_code', 'item_name']).agg({
                    'amount': 'sum',
                    'quantity': 'sum'
                }).reset_index()
                category_summary['category'] = category_summary['item_code'] + ' - ' + category_summary['item_name']
                category_summary['has_children'] = False
                category_summary['full_path'] = ''
            else:
                # Уровень категорий
                category_summary = cat_df.groupby(['category', 'full_path']).agg({
                    'amount': 'sum',
                    'quantity': 'sum',
                    'has_children': 'first'
                }).reset_index()
            
            # Сортируем по выручке
            category_summary = category_summary.sort_values('amount', ascending=False)
            
            # Добавляем ABC классификацию
            total_amount = category_summary['amount'].sum()
            
            # Рассчитываем проценты только если есть выручка
            if total_amount > 0:
                category_summary['percentage'] = (category_summary['amount'] / total_amount) * 100
                category_summary['cumulative_percentage'] = category_summary['percentage'].cumsum()
                
                # ABC классификация по накопительному проценту
                def assign_abc(row):
                    cum_perc = row['cumulative_percentage']
                    if cum_perc <= 80:
                        return 'A'
                    elif cum_perc <= 95:
                        return 'B'
                    else:
                        return 'C'
                
                category_summary['ABC'] = category_summary.apply(assign_abc, axis=1)
            else:
                # Если нет выручки, все в группу C
                category_summary['percentage'] = 0
                category_summary['cumulative_percentage'] = 0
                category_summary['ABC'] = 'C'
            
            # Возвращаем данные и хлебные крошки
            breadcrumbs = level_path.copy()
            
            result = (category_summary, breadcrumbs)
            
            # Сохраняем в session_state кеш
            st.session_state.abc_cache[session_cache_key] = result
            
            # Сохраняем в постоянный кеш
            save_persistent_cache(cache_key, result, data_hash)
            
            return result
        
        # Очищаем старые файлы кеша при каждом запуске
        clean_old_cache_files()
        
        # Получаем данные для текущего уровня
        abc_categories, breadcrumbs = calculate_abc_with_hierarchy(sales_data, st.session_state.abc_current_path)
        
        # Отладочная информация
        if st.checkbox("🔍 Показать отладочную информацию", key="debug_abc"):
            st.write(f"**Текущий путь навигации:** {st.session_state.abc_current_path}")
            st.write(f"**Количество строк в sales_data:** {len(sales_data)}")
            st.write(f"**Есть ли category_path:** {'category_path' in sales_data.columns}")
            
            # Информация о кешировании
            safe_path = '_'.join([p.replace(' ', '_').replace('/', '_') for p in st.session_state.abc_current_path])
            cache_key = f"{len(st.session_state.abc_current_path)}_{safe_path}" if safe_path else f"{len(st.session_state.abc_current_path)}_root"
            session_cache_key = f"abc_{cache_key}"
            data_hash = get_data_hash(sales_data)
            
            st.write(f"**Ключ кеша:** `{cache_key}`")
            st.write(f"**Хеш данных:** `{data_hash}`")
            st.write(f"**Session кеш:** {len(st.session_state.abc_cache)} записей")
            st.write(f"**Данные из session:** {'Да' if session_cache_key in st.session_state.abc_cache else 'Нет'}")
            
            # Проверяем постоянный кеш
            persistent_file = os.path.join(CACHE_DIR, f"abc_{cache_key}_{data_hash}.json")
            st.write(f"**Постоянный файл:** {'Существует' if os.path.exists(persistent_file) else 'Не найден'}")
            
            # Показываем файлы в кеш-директории
            cache_files = os.listdir(CACHE_DIR) if os.path.exists(CACHE_DIR) else []
            st.write(f"**Файлов в кеше:** {len(cache_files)}")
            
            # Показываем примеры путей категорий из данных
            sample_paths = sales_data['category_path'].dropna().unique()[:5]
            st.write("**Примеры путей категорий из данных:**")
            for i, path in enumerate(sample_paths):
                parts = [p.strip() for p in str(path).split('/') if p.strip()]
                st.write(f"{i+1}. `{path}` → {parts}")
            
            if not abc_categories.empty:
                st.write(f"**Количество найденных элементов:** {len(abc_categories)}")
                
                # Проверяем странные проценты
                strange_percentages = abc_categories[abc_categories['percentage'] < 0.001]
                if not strange_percentages.empty:
                    st.warning(f"⚠️ Найдено {len(strange_percentages)} элементов с очень маленькими процентами (<0.001%)")
                    st.write("**Примеры:**")
                    st.write(strange_percentages.head(3))
            else:
                st.write("**abc_categories пустой!**")
        
        if not abc_categories.empty:
            # Хлебные крошки навигации
            if breadcrumbs:
                st.subheader("🧭 Навигация:")
                nav_col1, nav_col2 = st.columns([1, 4])
                
                with nav_col1:
                    if st.button("🏠 Корень", key="nav_root_button"):
                        st.session_state.abc_current_path = []
                        st.cache_data.clear()
                        st.rerun()
                
                with nav_col2:
                    breadcrumb_text = " → ".join(breadcrumbs)
                    st.write(f"**Текущий путь:** {breadcrumb_text}")
                        
            # Кнопки управления и информация о кеше
            col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 1])
            
            with col_nav1:
                if st.button("🏠 Корень", key="nav_to_root"):
                    st.session_state.abc_current_path = []
                    st.rerun()
            
            with col_nav2:
                if st.session_state.abc_current_path and st.button("⬅️ Назад", key="nav_back"):
                    st.session_state.abc_current_path.pop()
                    st.rerun()
            
            with col_nav3:
                if st.button("🔄 Очистить кеш", key="clear_cache"):
                    # Очищаем session_state кеш
                    st.session_state.abc_cache = {}
                    
                    # Очищаем постоянные файлы кеша
                    try:
                        import shutil
                        if os.path.exists(CACHE_DIR):
                            shutil.rmtree(CACHE_DIR)
                            os.makedirs(CACHE_DIR)
                        st.success("🗑️ Весь кеш очищен! Данные будут пересчитаны.")
                    except Exception as e:
                        st.warning(f"⚠️ Ошибка очистки: {e}")
                        st.success("✅ Session кеш очищен!")
                    
                    st.rerun()
            
            with col_nav4:
                cache_size = len(st.session_state.abc_cache) if 'abc_cache' in st.session_state else 0
                st.info(f"💾 Кеш: {cache_size} уровней")
            
            # Заголовок текущего уровня
            if breadcrumbs:
                current_level_name = " → ".join(breadcrumbs)
                st.subheader(f"📊 ABC анализ: {current_level_name}")
            else:
                st.subheader("📊 ABC анализ: Основные категории")
            
            # Метрики ABC
            col1, col2, col3 = st.columns(3)
            
            a_categories = abc_categories[abc_categories['ABC'] == 'A']
            b_categories = abc_categories[abc_categories['ABC'] == 'B'] 
            c_categories = abc_categories[abc_categories['ABC'] == 'C']
            
            with col1:
                st.metric("🅰️ Группа A", f"{len(a_categories)}",
                         f"{a_categories['percentage'].sum():.1f}% выручки")
            with col2:
                st.metric("🅱️ Группа B", f"{len(b_categories)}",
                         f"{b_categories['percentage'].sum():.1f}% выручки")
            with col3:
                st.metric("🅾️ Группа C", f"{len(c_categories)}",
                         f"{c_categories['percentage'].sum():.1f}% выручки")
            
            # Графики
            col1, col2 = st.columns(2)
            
            with col1:
                # Круговая диаграмма распределения по ABC
                abc_summary = abc_categories.groupby('ABC')['amount'].sum().reset_index()
                
                fig_abc = px.pie(
                    abc_summary,
                    values='amount',
                    names='ABC',
                    title='Распределение выручки по ABC группам',
                    color='ABC',
                    color_discrete_map={'A': '#28a745', 'B': '#ffc107', 'C': '#dc3545'}
                )
                st.plotly_chart(fig_abc, use_container_width=True)
            
            with col2:
                # Столбчатая диаграмма топ-10 категорий
                top_categories = abc_categories.head(10)
                
                fig_top = px.bar(
                    top_categories,
                    x='amount',
                    y='category',
                    title='Топ-10 категорий по выручке',
                    orientation='h',
                    color='ABC',
                    color_discrete_map={'A': '#28a745', 'B': '#ffc107', 'C': '#dc3545'}
                )
                fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_top, use_container_width=True)
            
            # Удобная таблица с навигацией
            st.subheader("📊 ABC анализ - таблица данных")
            
            # Подготавливаем данные для таблицы
            display_data = abc_categories.copy()
            
            # Добавляем кнопки навигации для категорий с детьми
            if not display_data.empty:
                # Показываем кнопки навигации только для категорий с детьми
                has_navigable_categories = display_data['has_children'].any()
                
                if has_navigable_categories:
                    st.write("**🧭 Навигация по категориям:**")
                    
                    # Создаем кнопки для всех категорий с детьми
                    nav_cols = st.columns(min(4, len(display_data[display_data['has_children'] == True])))
                    nav_col_idx = 0
                    
                    for idx, row in display_data.iterrows():
                        if row.get('has_children', False):
                            safe_category = str(row['category']).replace(' ', '_').replace('/', '_')
                            button_key = f"nav_{safe_category}_{len(st.session_state.abc_current_path)}_{idx}"
                            
                            with nav_cols[nav_col_idx % len(nav_cols)]:
                                if st.button(f"➡️ {row['category']}", key=button_key):
                                    st.session_state.abc_current_path.append(row['category'])
                                    st.rerun()
                            
                            nav_col_idx += 1
                    
                    st.write("---")  # Разделитель
                
                # Форматируем данные для показа
                # Сначала выбираем только нужные колонки в правильном порядке
                needed_columns = ['category', 'amount', 'quantity', 'percentage', 'cumulative_percentage', 'ABC']
                
                # Проверяем наличие всех нужных колонок
                available_columns = []
                for col in needed_columns:
                    if col in display_data.columns:
                        available_columns.append(col)
                
                # Выбираем только доступные колонки
                if available_columns:
                    display_data = display_data[available_columns]
                
                # Переименовываем колонки
                column_mapping = {
                    'category': 'Категория/Товар',
                    'amount': 'Выручка (₸)',
                    'quantity': 'Количество',
                    'percentage': '% выручки',
                    'cumulative_percentage': '% накопительный',
                    'ABC': 'ABC группа'
                }
                
                display_data = display_data.rename(columns=column_mapping)
                
                # Форматируем числа (с проверкой типов и наличия колонок)
                if 'Выручка (₸)' in display_data.columns:
                    display_data['Выручка (₸)'] = display_data['Выручка (₸)'].apply(
                        lambda x: f"{float(x):,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)
                    )
                
                if 'Количество' in display_data.columns:
                    display_data['Количество'] = display_data['Количество'].apply(
                        lambda x: f"{float(x):,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)
                    )
                
                if '% выручки' in display_data.columns:
                    display_data['% выручки'] = display_data['% выручки'].apply(
                        lambda x: f"{float(x):.2f}%" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)
                    )
                
                if '% накопительный' in display_data.columns:
                    display_data['% накопительный'] = display_data['% накопительный'].apply(
                        lambda x: f"{float(x):.1f}%" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)
                    )
                
                # Показываем таблицу
                st.dataframe(
                    display_data, 
                    hide_index=True, 
                    height=min(600, len(display_data) * 35 + 100),
                    use_container_width=True
                )
                
                # Информация о количестве элементов
                current_path_str = ' → '.join(st.session_state.abc_current_path) if st.session_state.abc_current_path else 'Корень'
                st.info(f"📊 Показано {len(abc_categories)} элементов на уровне: **{current_path_str}**")
                
                # Статистика по ABC группам
                abc_stats = abc_categories.groupby('ABC').agg({
                    'amount': 'sum',
                    'quantity': 'sum',
                    'category': 'count'
                }).reset_index()
                
                st.subheader("📈 Статистика по ABC группам")
                col1, col2, col3 = st.columns(3)
                
                for idx, stat_row in abc_stats.iterrows():
                    abc_group = stat_row['ABC']
                    count = stat_row['category']
                    amount = stat_row['amount']
                    
                    if idx == 0:
                        with col1:
                            st.metric(f"🅰️ Группа {abc_group}", f"{count} элементов", f"{amount:,.0f} ₸")
                    elif idx == 1:
                        with col2:
                            st.metric(f"🅱️ Группа {abc_group}", f"{count} элементов", f"{amount:,.0f} ₸")
                    else:
                        with col3:
                            st.metric(f"🅾️ Группа {abc_group}", f"{count} элементов", f"{amount:,.0f} ₸")
            
            # Экспорт
            csv = abc_categories.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Скачать ABC анализ категорий",
                data=csv,
                file_name=f"abc_categories_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Нет данных о категориях для ABC анализа")
        
    elif not sales_data.empty:
        # Fallback на старый метод если нет category_path
        category_abc = calculate_abc_by_categories(sales_data, stock_data)
        
        if not category_abc.empty:
            # Старый интерфейс ABC
            col1, col2, col3 = st.columns(3)
            
            a_categories = category_abc[category_abc['ABC'] == 'A']
            b_categories = category_abc[category_abc['ABC'] == 'B'] 
            c_categories = category_abc[category_abc['ABC'] == 'C']
            
            with col1:
                st.metric("🅰️ Категории A", f"{len(a_categories)} кат.",
                         f"{a_categories['% от общей выручки'].sum():.1f}% выручки")
            with col2:
                st.metric("🅱️ Категории B", f"{len(b_categories)} кат.",
                         f"{b_categories['% от общей выручки'].sum():.1f}% выручки")
            with col3:
                st.metric("🅾️ Категории C", f"{len(c_categories)} кат.",
                         f"{c_categories['% от общей выручки'].sum():.1f}% выручки")
            
            st.dataframe(category_abc, hide_index=True, height=400)
        else:
            st.warning("⚠️ Нет данных о категориях для ABC анализа")
    else:
        st.warning("⚠️ Недостаточно данных для ABC анализа")

with tab5:
    st.header("🔀 Межфилиальные перемещения")
    
    if not sales_data.empty and not stock_data.empty:
        # Алгоритм межфилиальных перемещений на основе продаж и остатков
        st.info("💡 **Логика рекомендаций:** Анализируем продажи и остатки по филиалам для выявления дисбаланса")
        
        # Группируем продажи по филиалам и товарам
        sales_by_branch = sales_data.groupby(['branch', 'item_code', 'item_name']).agg({
            'quantity': 'sum',
            'amount': 'sum'
        }).reset_index()
        
        # Группируем остатки по складам и товарам
        stock_by_warehouse = stock_data.groupby(['warehouse', 'item_code', 'item_name']).agg({
            'quantity': 'sum'
        }).reset_index()
        stock_by_warehouse.rename(columns={'warehouse': 'branch', 'quantity': 'stock_quantity'}, inplace=True)
        
        # Объединяем данные о продажах и остатках
        movement_data = pd.merge(
            sales_by_branch,
            stock_by_warehouse,
            on=['branch', 'item_code', 'item_name'],
            how='outer'
        ).fillna(0)
        
        # Добавляем города
        movement_data['city'] = movement_data['branch'].apply(get_city_from_branch)
        
        # Рассчитываем среднедневные продажи и дни до истощения
        movement_data['daily_sales'] = movement_data['quantity'] / 30.5  # За месяц
        movement_data['days_until_empty'] = np.where(
            movement_data['daily_sales'] > 0,
            movement_data['stock_quantity'] / movement_data['daily_sales'],
            999999
        )
        
        # Рассчитываем потребность в перемещениях
        movement_data['needs_stock'] = (movement_data['daily_sales'] > 0) & (movement_data['days_until_empty'] < 30)
        movement_data['has_excess'] = (movement_data['daily_sales'] == 0) & (movement_data['stock_quantity'] > 0)
        movement_data['excess_ratio'] = movement_data['stock_quantity'] / (movement_data['daily_sales'] + 0.001)
        
        if not movement_data.empty:
            # Метрики перемещений
            col1, col2, col3, col4 = st.columns(4)
            
            total_needs = movement_data['needs_stock'].sum()
            total_excess = movement_data['has_excess'].sum()
            total_branches = movement_data['branch'].nunique()
            potential_moves = min(total_needs, total_excess)
            
            with col1:
                st.metric("🔴 Нужен товар", f"{total_needs} позиций")
            
            with col2:
                st.metric("🟢 Избыток товара", f"{total_excess} позиций")
            
            with col3:
                st.metric("🏪 Филиалов", f"{total_branches}")
            
            with col4:
                st.metric("🔄 Возможных перемещений", f"{potential_moves}")
            
            # Анализ по городам
            st.subheader("🏙️ Дисбаланс по городам")
            
            city_balance = movement_data.groupby('city').agg({
                'needs_stock': 'sum',
                'has_excess': 'sum',
                'stock_quantity': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            city_balance['balance_ratio'] = city_balance['has_excess'] / (city_balance['needs_stock'] + 1)
            city_balance = city_balance.sort_values('balance_ratio', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_needs = px.bar(
                    city_balance,
                    x='city',
                    y='needs_stock',
                    title='Потребность в товаре по городам',
                    labels={'needs_stock': 'Позиций нужно', 'city': 'Город'},
                    color='needs_stock',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_needs, use_container_width=True)
            
            with col2:
                fig_excess = px.bar(
                    city_balance,
                    x='city',
                    y='has_excess',
                    title='Избыток товара по городам',
                    labels={'has_excess': 'Позиций избыток', 'city': 'Город'},
                    color='has_excess',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig_excess, use_container_width=True)
            
            # Конкретные рекомендации по перемещениям
            st.subheader("📋 Рекомендации по перемещениям")
            
            # Фильтры для рекомендаций
            col1, col2 = st.columns(2)
            with col1:
                selected_city = st.selectbox(
                    "Фильтр по городу",
                    options=['Все города'] + list(movement_data['city'].unique())
                )
            
            with col2:
                urgency_filter = st.selectbox(
                    "Уровень срочности",
                    ["Все", "Критично (< 7 дней)", "Срочно (< 14 дней)", "Внимание (< 30 дней)"]
                )
            
            # Применяем фильтры
            filtered_data = movement_data.copy()
            
            if selected_city != 'Все города':
                filtered_data = filtered_data[filtered_data['city'] == selected_city]
            
            if urgency_filter == "Критично (< 7 дней)":
                filtered_data = filtered_data[filtered_data['days_until_empty'] < 7]
            elif urgency_filter == "Срочно (< 14 дней)":
                filtered_data = filtered_data[filtered_data['days_until_empty'] < 14]
            elif urgency_filter == "Внимание (< 30 дней)":
                filtered_data = filtered_data[filtered_data['days_until_empty'] < 30]
            
            # Товары которые нужно завезти
            needs_items = filtered_data[filtered_data['needs_stock']].sort_values('days_until_empty')
            
            if not needs_items.empty:
                st.subheader("🔴 Товары требующие пополнения")
                
                display_needs = needs_items[['item_name', 'branch', 'city', 'stock_quantity', 
                                           'daily_sales', 'days_until_empty']].copy()
                display_needs.columns = ['Товар', 'Филиал', 'Город', 'Остаток', 
                                       'Продажи/день', 'Дней до истощения']
                
                display_needs['Остаток'] = display_needs['Остаток'].round(0).astype(int)
                display_needs['Продажи/день'] = display_needs['Продажи/день'].round(2)
                display_needs['Дней до истощения'] = display_needs['Дней до истощения'].round(1)
                
                # Цветовое кодирование по срочности
                def color_urgency(val):
                    if val < 7:
                        return 'background-color: #ffcccc'  # Красный - критично
                    elif val < 14:
                        return 'background-color: #ffe6cc'  # Оранжевый - срочно  
                    elif val < 30:
                        return 'background-color: #ffffcc'  # Желтый - внимание
                    else:
                        return ''
                
                styled_needs = display_needs.style.applymap(
                    color_urgency, subset=['Дней до истощения']
                )
                
                st.dataframe(styled_needs, hide_index=True, height=300)
            
            # Товары с избытком (источники для перемещений)
            excess_items = filtered_data[filtered_data['has_excess']].sort_values('stock_quantity', ascending=False)
            
            if not excess_items.empty:
                st.subheader("🟢 Товары с избытком (источники перемещений)")
                
                display_excess = excess_items[['item_name', 'branch', 'city', 'stock_quantity']].head(20)
                display_excess.columns = ['Товар', 'Филиал', 'Город', 'Избыток']
                display_excess['Избыток'] = display_excess['Избыток'].round(0).astype(int)
                
                st.dataframe(display_excess, hide_index=True, height=300)
            
            # Экспорт рекомендаций
            if not needs_items.empty:
                csv_needs = needs_items.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Скачать рекомендации по пополнению",
                    data=csv_needs,
                    file_name=f"movement_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ Недостаточно данных для анализа перемещений")
    else:
        st.warning("⚠️ Для анализа перемещений нужны данные о продажах и остатках")

with tab6:
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