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
    
    # Расчет оборачиваемости (остатки / дневные_продажи * период)
    turnover_data['turnover_days'] = np.where(
        turnover_data['daily_sales'] > 0,
        (turnover_data['stock_quantity'] / turnover_data['daily_sales']) * period_days,
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
    
    # Расчет оборачиваемости (остатки / дневные_продажи * период)
    city_turnover['turnover_days'] = np.where(
        city_turnover['daily_sales'] > 0,
        (city_turnover['stock_quantity'] / city_turnover['daily_sales']) * period_days,
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
            
            fig_dist = px.bar(
                turnover_distribution,
                x='index',
                y='turnover_category',
                title='Распределение товаров по скорости оборачиваемости',
                labels={'index': 'Категория оборачиваемости', 'turnover_category': 'Количество SKU'},
                color='index',
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
        # Инициализация состояния раскрытых категорий
        if 'expanded_categories' not in st.session_state:
            st.session_state.expanded_categories = set()
        
        @st.cache_data(ttl=300)
        def build_category_tree(_df):
            """Строит дерево категорий из данных с кешированием"""
            tree = {}
            
            # Берем выборку для ускорения если данных много
            if len(_df) > 50000:
                df_sample = _df.sample(n=20000, random_state=42)
                st.info("📊 Для ускорения ABC анализа используется выборка данных")
            else:
                df_sample = _df
            
            for _, row in df_sample.iterrows():
                if pd.isna(row['category_path']) or row['category_path'] == '':
                    continue
                    
                # Разбиваем путь на части (только первые 3 уровня для скорости)
                parts = [p.strip() for p in str(row['category_path']).split('/') if p.strip()][:3]
                
                # Строим дерево
                current_node = tree
                for i, part in enumerate(parts):
                    if part not in current_node:
                        current_node[part] = {
                            'children': {},
                            'items': [],
                            'total_amount': 0,
                            'total_quantity': 0,
                            'level': i,
                            'path': parts[:i+1]
                        }
                    
                    current_node[part]['items'].append(row)
                    current_node[part]['total_amount'] += row['amount']
                    current_node[part]['total_quantity'] += row['quantity']
                    current_node = current_node[part]['children']
            
            return tree
        
        def calculate_abc_for_level(items_data):
            """Вычисляет ABC для набора элементов"""
            if not items_data:
                return []
            
            # Сортируем по выручке
            sorted_items = sorted(items_data, key=lambda x: x['total_amount'], reverse=True)
            total_revenue = sum(item['total_amount'] for item in sorted_items)
            
            cumsum = 0
            for item in sorted_items:
                cumsum += item['total_amount']
                percent = (cumsum / total_revenue * 100) if total_revenue > 0 else 0
                
                if percent <= 80:
                    item['abc'] = 'A'
                elif percent <= 95:
                    item['abc'] = 'B'
                else:
                    item['abc'] = 'C'
                    
                item['percent'] = (item['total_amount'] / total_revenue * 100) if total_revenue > 0 else 0
            
            return sorted_items
        
        def render_category_level(tree, level=0, parent_path=""):
            """Рендерит уровень категорий с возможностью раскрытия"""
            
            # Подготавливаем данные для ABC анализа
            level_data = []
            for name, data in tree.items():
                level_data.append({
                    'name': name,
                    'total_amount': data['total_amount'],
                    'total_quantity': data['total_quantity'],
                    'items_count': len(data['items']),
                    'has_children': bool(data['children']),
                    'path': parent_path + "/" + name if parent_path else name
                })
            
            # Вычисляем ABC
            abc_data = calculate_abc_for_level(level_data)
            
            if not abc_data:
                return
            
            # Метрики ABC
            if level == 0:  # Показываем метрики только на корневом уровне
                a_items = [item for item in abc_data if item['abc'] == 'A']
                b_items = [item for item in abc_data if item['abc'] == 'B']
                c_items = [item for item in abc_data if item['abc'] == 'C']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🅰️ Группа A", f"{len(a_items)}", 
                             f"{sum(item['percent'] for item in a_items):.1f}% выручки")
                with col2:
                    st.metric("🅱️ Группа B", f"{len(b_items)}", 
                             f"{sum(item['percent'] for item in b_items):.1f}% выручки")
                with col3:
                    st.metric("🅾️ Группа C", f"{len(c_items)}", 
                             f"{sum(item['percent'] for item in c_items):.1f}% выручки")
            
            # Рендерим таблицу с раскрывающимися строками (максимум 20 на уровень)
            for idx, item in enumerate(abc_data[:20]):  # Ограничиваем количество
                # Определяем цвет фона для ABC
                if item['abc'] == 'A':
                    bg_color = '#d4edda'
                elif item['abc'] == 'B':
                    bg_color = '#fff3cd'
                else:
                    bg_color = '#f8d7da'
                
                # Отступ для уровня вложенности
                indent = "　" * level
                
                # Создаем expandable контейнер для каждой категории
                expanded_key = f"{item['path']}_level_{level}"
                
                # Иконка в зависимости от наличия детей
                icon = "📂" if item['has_children'] else "📄"
                
                with st.container():
                    # Основная строка категории
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    with col1:
                        # Кнопка раскрытия/сворачивания
                        is_expanded = expanded_key in st.session_state.expanded_categories
                        expand_symbol = "▼" if is_expanded else "▶"
                        
                        if item['has_children']:
                            if st.button(f"{indent}{expand_symbol} {icon} {item['name'][:50]}", 
                                       key=f"expand_{expanded_key}_{idx}",
                                       help="Нажмите для раскрытия подкатегорий"):
                                if is_expanded:
                                    st.session_state.expanded_categories.remove(expanded_key)
                                else:
                                    st.session_state.expanded_categories.add(expanded_key)
                                st.rerun()
                        else:
                            st.write(f"{indent}{icon} {item['name'][:50]}")
                    
                    with col2:
                        st.markdown(f"<div style='background-color: {bg_color}; padding: 5px; border-radius: 3px; text-align: center;'><b>{item['abc']}</b></div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.write(f"{item['total_amount']:,.0f} ₸")
                    
                    with col4:
                        st.write(f"{item['total_quantity']:,.0f}")
                    
                    with col5:
                        st.write(f"{item['percent']:.1f}%")
                
                # Если категория раскрыта, показываем подкатегории
                if expanded_key in st.session_state.expanded_categories and item['has_children']:
                    category_name = item['name']
                    if category_name in tree:
                        render_category_level(tree[category_name]['children'], level + 1, item['path'])
                
                # Если у категории есть товары и она раскрыта, показываем товары (максимум 5)
                if expanded_key in st.session_state.expanded_categories:
                    category_name = item['name']
                    if category_name in tree:
                        items = tree[category_name]['items']
                        if items and not tree[category_name]['children']:
                            # Быстрый показ топ-5 товаров без полного ABC
                            items_sample = sorted(items, key=lambda x: x['amount'], reverse=True)[:5]
                            
                            for i, product_row in enumerate(items_sample):
                                pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns([3, 1, 1, 1, 1])
                                
                                product_indent = "　" * (level + 1)
                                
                                # Простая ABC для товара
                                if i == 0:
                                    abc_class = 'A'
                                    pbg_color = '#d4edda'
                                elif i <= 2:
                                    abc_class = 'B'
                                    pbg_color = '#fff3cd'
                                else:
                                    abc_class = 'C'
                                    pbg_color = '#f8d7da'
                                
                                with pcol1:
                                    product_name = f"{product_row['item_code']} - {product_row['item_name'][:30]}"
                                    st.write(f"{product_indent}🛍️ {product_name}")
                                with pcol2:
                                    st.markdown(f"<div style='background-color: {pbg_color}; padding: 3px; border-radius: 3px; text-align: center; font-size: 0.8em;'>{abc_class}</div>", unsafe_allow_html=True)
                                with pcol3:
                                    st.write(f"{product_row['amount']:,.0f} ₸")
                                with pcol4:
                                    st.write(f"{product_row['quantity']:,.0f}")
                                with pcol5:
                                    st.write("-")
            
            # Показываем если есть еще категории
            if len(abc_data) > 20:
                st.info(f"... и еще {len(abc_data) - 20} категорий (показаны топ-20 для скорости)")
        
        # Строим дерево категорий
        category_tree = build_category_tree(sales_data)
        
        if category_tree:
            st.subheader("📊 Иерархический ABC анализ")
            st.info("💡 Нажмите на ▶ для раскрытия категории и просмотра подкатегорий")
            
            # Заголовки таблицы
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.write("**Категория**")
            with col2:
                st.write("**ABC**")
            with col3:
                st.write("**Выручка**")
            with col4:
                st.write("**Количество**")
            with col5:
                st.write("**% выручки**")
            
            st.markdown("---")
            
            # Рендерим дерево
            render_category_level(category_tree)
            
            # Кнопки управления
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Раскрыть все категории"):
                    # Собираем все возможные ключи
                    def collect_all_keys(tree, level=0, parent_path=""):
                        keys = []
                        for name, data in tree.items():
                            path = parent_path + "/" + name if parent_path else name
                            key = f"{path}_level_{level}"
                            keys.append(key)
                            if data['children']:
                                keys.extend(collect_all_keys(data['children'], level + 1, path))
                        return keys
                    
                    all_keys = collect_all_keys(category_tree)
                    st.session_state.expanded_categories = set(all_keys)
                    st.rerun()
            
            with col2:
                if st.button("📁 Свернуть все категории"):
                    st.session_state.expanded_categories = set()
                    st.rerun()
        else:
            st.warning("⚠️ Нет данных о путях категорий для анализа")
    
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
            (movement_data['stock_quantity'] / movement_data['daily_sales']) * 30.5,
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