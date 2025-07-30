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
    Период = 30.5.5 дней (средний месяц)
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

# Загружаем данные с предупреждением о больших периодах
if period_option in ["Последние 180 дней", "Весь период"]:
    st.warning("⚠️ Загрузка большого объема данных может занять время...")

with st.spinner("Загрузка данных..."):
    try:
        # Добавляем лимит для очень больших запросов
        if period_option == "Весь период":
            # Для полного периода предупреждаем и ограничиваем
            st.info("💡 Для ускорения анализа больших объемов некоторые визуализации могут быть упрощены")
        
        sales_data = accumulator.get_sales_data(
            start_date=str(start_date) if start_date else None,
            end_date=str(end_date) if end_date else None
        )
        
        stock_data = accumulator.get_latest_stock()
        
        # Предупреждение о размере данных
        if len(sales_data) > 100000:
            st.warning(f"⚠️ Загружено {len(sales_data):,} записей. Некоторые визуализации могут работать медленно.")
            
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
            delta_percent = 0  # Можно добавить сравнение с прошлым периодом
            
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
            st.subheader("📊 Топ-10 товаров по количеству")
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
                avg_turnover = turnover_data[turnover_data['turnover_days'] < 999999]['turnover_days'].mean()
                st.metric("📊 Средняя оборачиваемость", f"{avg_turnover:.1f} дней")
            
            with col2:
                fast_items = len(turnover_data[turnover_data['turnover_days'] < 30])
                st.metric("🚀 Быстрые товары", f"{fast_items} SKU")
            
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
    
    if not sales_data.empty:
        # ABC анализ категорий
        category_abc = calculate_abc_by_categories(sales_data, stock_data)
        
        if not category_abc.empty:
            # Метрики ABC
            col1, col2, col3 = st.columns(3)
            
            a_categories = category_abc[category_abc['ABC'] == 'A']
            b_categories = category_abc[category_abc['ABC'] == 'B']
            c_categories = category_abc[category_abc['ABC'] == 'C']
            
            with col1:
                st.metric(
                    "🅰️ Категории A",
                    f"{len(a_categories)} кат.",
                    f"{a_categories['% от общей выручки'].sum():.1f}% выручки"
                )
            
            with col2:
                st.metric(
                    "🅱️ Категории B", 
                    f"{len(b_categories)} кат.",
                    f"{b_categories['% от общей выручки'].sum():.1f}% выручки"
                )
            
            with col3:
                st.metric(
                    "🅾️ Категории C",
                    f"{len(c_categories)} кат.",
                    f"{c_categories['% от общей выручки'].sum():.1f}% выручки"
                )
            
            # График ABC
            st.subheader("📊 ABC анализ категорий")
            
            # Парето диаграмма
            fig_pareto = go.Figure()
            
            # Столбцы выручки
            fig_pareto.add_trace(go.Bar(
                x=category_abc['Категория'],
                y=category_abc['Выручка'],
                name='Выручка',
                marker_color=['#e74c3c' if x == 'A' else '#f39c12' if x == 'B' else '#95a5a6' 
                             for x in category_abc['ABC']]
            ))
            
            # Линия накопительного процента
            fig_pareto.add_trace(go.Scatter(
                x=category_abc['Категория'],
                y=category_abc['Накопительный %'],
                name='Накопительный %',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='#2c3e50', width=2)
            ))
            
            # Линии 80% и 95%
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="red", 
                                annotation_text="80%", yref='y2')
            fig_pareto.add_hline(y=95, line_dash="dash", line_color="orange", 
                                annotation_text="95%", yref='y2')
            
            fig_pareto.update_layout(
                title='Парето-диаграмма категорий',
                xaxis_title='Категория',
                yaxis_title='Выручка (₸)',
                yaxis2=dict(
                    title='Накопительный %',
                    overlaying='y',
                    side='right',
                    range=[0, 100]
                ),
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig_pareto, use_container_width=True)
            
            # Таблица ABC
            st.subheader("📋 Детальный ABC анализ категорий")
            
            # Форматирование для отображения
            display_abc = category_abc[['Категория', 'ABC', 'Выручка', '% от общей выручки', 
                                       'Товаров', 'Количество']].copy()
            
            # Цветовое кодирование
            def color_abc(val):
                if val == 'A':
                    return 'background-color: #ffcccc'
                elif val == 'B':
                    return 'background-color: #ffffcc'
                else:
                    return 'background-color: #cccccc'
            
            styled_abc = display_abc.style.applymap(color_abc, subset=['ABC'])
            st.dataframe(styled_abc, hide_index=True, height=400)
            
            # Рекомендации по категориям
            st.subheader("💡 Рекомендации по управлению категориями")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("""
                **🅰️ Категории A:**
                - Приоритетный контроль остатков
                - Минимизация дефицита
                - Частая инвентаризация
                - Премиальное размещение
                """)
            
            with col2:
                st.warning("""
                **🅱️ Категории B:**
                - Умеренный контроль
                - Периодический анализ
                - Оптимизация запасов
                - Стандартное размещение
                """)
            
            with col3:
                st.success("""
                **🅾️ Категории C:**
                - Минимальные запасы
                - Редкая инвентаризация
                - Возможность исключения
                - Компактное хранение
                """)
    else:
        st.warning("⚠️ Недостаточно данных для ABC анализа")

with tab5:
    st.header("🔀 Межфилиальные перемещения")
    
    # Здесь можно интегрировать логику межфилиальных перемещений
    st.info("📝 Раздел межфилиальных перемещений. Интеграция с основной логикой.")

with tab6:
    st.header("📈 Детальная аналитика")
    
    if not sales_data.empty:
        # Анализ по дням недели
        st.subheader("📅 Анализ по дням недели")
        
        sales_data['weekday'] = pd.to_datetime(sales_data['date']).dt.day_name()
        weekday_sales = sales_data.groupby('weekday')['amount'].sum().reset_index()
        
        # Правильный порядок дней
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_sales['weekday'] = pd.Categorical(weekday_sales['weekday'], categories=weekday_order, ordered=True)
        weekday_sales = weekday_sales.sort_values('weekday')
        
        fig_weekday = px.bar(
            weekday_sales,
            x='weekday',
            y='amount',
            title='Продажи по дням недели',
            labels={'amount': 'Выручка (₸)', 'weekday': 'День недели'}
        )
        st.plotly_chart(fig_weekday, use_container_width=True)
        
        # Тепловая карта продаж - показывать только если данных не слишком много
        if len(sales_data) < 50000:  # Ограничение для производительности
            st.subheader("🗓️ Тепловая карта продаж")
            
            # Подготовка данных - используем только реальные даты
            sales_data_copy = sales_data.copy()
            sales_data_copy['date_parsed'] = pd.to_datetime(sales_data_copy['date'])
            
            # Группируем по дням для получения реальных дат с продажами
            daily_sales = sales_data_copy.groupby('date')['amount'].sum().reset_index()
            
            if len(daily_sales) > 0:
                # Создаем колонки для отображения
                daily_sales['date_parsed'] = pd.to_datetime(daily_sales['date'])
                daily_sales['year_month'] = daily_sales['date_parsed'].dt.to_period('M').astype(str)
                daily_sales['day_of_month'] = daily_sales['date_parsed'].dt.day
                daily_sales['weekday'] = daily_sales['date_parsed'].dt.day_name()
                daily_sales['date_str'] = daily_sales['date_parsed'].dt.strftime('%d.%m.%Y')
                
                # Ограничиваем количество дат для отображения
                if len(daily_sales) > 200:  # Если слишком много дней
                    st.warning(f"⚠️ Слишком много дней для тепловой карты ({len(daily_sales)}). Показаны последние 200 дней.")
                    daily_sales = daily_sales.nlargest(200, 'date_parsed')
                
                # Создаем альтернативную визуализацию - календарная тепловая карта
                pivot_data = daily_sales.pivot_table(
                    index='day_of_month', 
                    columns='year_month', 
                    values='amount', 
                    aggfunc='sum'
                ).fillna(0)
                
                # Фильтруем только существующие дни в каждом месяце
                filtered_pivot = pd.DataFrame()
                for col in pivot_data.columns:
                    # Берем только те дни, где есть данные
                    month_data = pivot_data[col]
                    month_data = month_data[month_data > 0]  # Только дни с продажами
                    if not month_data.empty:
                        filtered_pivot[col] = pivot_data[col]
                
                if not filtered_pivot.empty:
                    # Создаем тепловую карту только с реальными данными
                    fig_heatmap = px.imshow(
                        filtered_pivot,
                        labels=dict(x="Месяц", y="День", color="Выручка (₸)"),
                        title=f"Тепловая карта продаж (только дни с продажами)",
                        color_continuous_scale='YlOrRd',
                        aspect='auto'
                    )
                    
                    # Настройки отображения
                    fig_heatmap.update_layout(
                        height=500,
                        xaxis_title="Месяц",
                        yaxis_title="День месяца"
                    )
                    
                    # Поворачиваем подписи если много месяцев
                    if len(filtered_pivot.columns) > 8:
                        fig_heatmap.update_layout(
                            xaxis=dict(tickangle=45)
                        )
                    
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    # Альтернативная визуализация - календарь
                    st.subheader("📅 Календарный вид продаж")
                    
                    # Создаем более простую визуализацию по неделям
                    daily_sales['week'] = daily_sales['date_parsed'].dt.isocalendar().week
                    daily_sales['year'] = daily_sales['date_parsed'].dt.year
                    daily_sales['year_week'] = daily_sales['year'].astype(str) + '-W' + daily_sales['week'].astype(str).str.zfill(2)
                    
                    # Ограничиваем до последних 24 недель для производительности
                    recent_weeks = daily_sales.nlargest(24*7, 'date_parsed')
                    
                    fig_calendar = px.scatter(
                        recent_weeks,
                        x='weekday',
                        y='year_week',
                        size='amount',
                        color='amount',
                        hover_data=['date_str', 'amount'],
                        title="Календарный вид продаж (размер = сумма продаж)",
                        color_continuous_scale='YlOrRd'
                    )
                    
                    fig_calendar.update_layout(
                        height=400,
                        xaxis_title="День недели",
                        yaxis_title="Неделя"
                    )
                    
                    st.plotly_chart(fig_calendar, use_container_width=True)
                    
                    # Статистика
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📅 Дней с продажами", len(daily_sales))
                    with col2:
                        avg_daily = daily_sales['amount'].mean()
                        st.metric("💰 Средняя выручка/день", f"{avg_daily:,.0f} ₸")
                    with col3:
                        max_day = daily_sales.loc[daily_sales['amount'].idxmax()]
                        st.metric("📈 Лучший день", f"{max_day['date_str']}")
                        st.caption(f"{max_day['amount']:,.0f} ₸")
                    
                else:
                    st.warning("⚠️ Нет данных для построения тепловой карты")
            else:
                st.warning("⚠️ Нет данных о ежедневных продажах")
        else:
            st.info("ℹ️ Тепловая карта скрыта из-за большого объема данных (>50,000 записей). Выберите более короткий период для просмотра.")
            
            # Показываем только основную статистику
            col1, col2, col3 = st.columns(3)
            with col1:
                unique_dates = sales_data['date'].nunique()
                st.metric("📅 Уникальных дней", unique_dates)
            with col2:
                date_range = pd.to_datetime(sales_data['date'])
                period_days = (date_range.max() - date_range.min()).days
                st.metric("📊 Период (дней)", period_days)
            with col3:
                st.metric("📋 Записей", f"{len(sales_data):,}")

# Футер
st.markdown("---")
st.caption("""
🔗 **Система аналитики товарных запасов**
- Автоматическое обновление каждые 5 минут
- Формула оборачиваемости: (Остатки / Продажи) × 30.5 дней (средний месяц)
- Данные накапливаются из webhook системы
""")