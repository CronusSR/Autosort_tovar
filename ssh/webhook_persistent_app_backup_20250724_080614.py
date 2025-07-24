#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенное веб-приложение с полной логикой межфилиальных перемещений
Интегрирует всю аналитику из основного приложения
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

# Импорт логики межфилиальных перемещений
try:
    from modular_inventory_system import ModularInventorySystem
    INVENTORY_SYSTEM_AVAILABLE = True
except ImportError:
    INVENTORY_SYSTEM_AVAILABLE = False

# Конфигурация страницы
st.set_page_config(
    page_title="Полная система анализа с вебхуками",
    page_icon="🚀",
    layout="wide"
)

# Иерархия складов - ПОЛНАЯ КОПИЯ ИЗ МЕЖФИЛИАЛЬНЫХ ПЕРЕМЕЩЕНИЙ
WAREHOUSE_HIERARCHY = {
    # 🏢 ГЛАВНЫЙ ХАБ (г.Алматы) - пополняет все склады 2-го уровня
    "hub": "База Склад Фурнитура Комплект",
    
    # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба)
    "level2_warehouses": {
        "Казыбаева Склад Фурнитура TRADE": ["ТД Казыбаева ФУРНИТУРА магазин"],  # г.Алматы
        "склад фурнитура № 1": ["Магазин фурнитуры"],  # г.Астана  
        "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"": ["6 Склад фурнитуры \"Овощная база\" Магазин продажи"]  # г.Шымкент
    },
    
    # 🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов 2-го уровня)
    "direct_stores_from_hub": [
        "Барыс Склад Фурнитура TRADE",  # г.Алматы
        "АО Склад Фурнитура TRADE"  # г.Алматы - Алтын Орда
    ]
}

def normalize_branch_name(name):
    """Нормализация названий филиалов для сопоставления"""
    name = str(name).strip()
    
    mappings = {
        "4 Склад фурнитуры АЗМ Шымкент": "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"",
        "6 Склад фурнитуры \"Овощная база\" Магазин": "6 Склад фурнитуры \"Овощная база\" Магазин продажи",
        "склад фурнитура №1": "склад фурнитура № 1",
        "склад фурнитура N 1": "склад фурнитура № 1",
    }
    
    for old, new in mappings.items():
        if old.lower() in name.lower():
            return new
    
    return name

def get_branch_type(branch_name):
    """Определяет тип филиала: хаб, склад, магазин_от_хаба, магазин_3_уровня"""
    normalized = normalize_branch_name(branch_name)
    
    if normalized == WAREHOUSE_HIERARCHY["hub"]:
        return "хаб"
    
    if normalized in WAREHOUSE_HIERARCHY["level2_warehouses"]:
        return "склад"
    
    if normalized in WAREHOUSE_HIERARCHY["direct_stores_from_hub"]:
        return "магазин_от_хаба"
    
    for warehouse, stores in WAREHOUSE_HIERARCHY["level2_warehouses"].items():
        if normalized in stores:
            return "магазин_3_уровня"
    
    return "неизвестно"

def get_parent_warehouse(branch_name):
    """Возвращает родительский склад для филиала"""
    normalized = normalize_branch_name(branch_name)
    
    if normalized in WAREHOUSE_HIERARCHY["level2_warehouses"]:
        return WAREHOUSE_HIERARCHY["hub"]
    
    if normalized in WAREHOUSE_HIERARCHY["direct_stores_from_hub"]:
        return WAREHOUSE_HIERARCHY["hub"]
    
    for warehouse, stores in WAREHOUSE_HIERARCHY["level2_warehouses"].items():
        if normalized in stores:
            return warehouse
    
    return None

def calculate_ads_from_sales(sales_data, days_period=30):
    """Расчет ADS из данных о продажах"""
    if sales_data.empty:
        return pd.DataFrame()
    
    # Группируем по товарам и суммируем продажи
    ads_calc = sales_data.groupby(['item_code', 'item_name']).agg({
        'quantity': 'sum',
        'amount': 'sum'
    }).reset_index()
    
    # Рассчитываем ADS
    ads_calc['ads'] = ads_calc['quantity'] / days_period
    ads_calc['total_sales'] = ads_calc['amount']
    
    return ads_calc

def generate_movement_recommendations(sales_data, stock_data, target_days=30):
    """Генерация рекомендаций по перемещениям"""
    if sales_data.empty or stock_data.empty:
        return pd.DataFrame()
    
    # Расчет ADS
    ads_data = calculate_ads_from_sales(sales_data)
    
    # Объединяем с остатками
    stock_summary = stock_data.groupby(['item_code', 'warehouse']).agg({
        'quantity': 'sum'
    }).reset_index()
    
    recommendations = []
    
    for _, stock_item in stock_summary.iterrows():
        item_code = stock_item['item_code']
        warehouse = stock_item['warehouse']
        stock_qty = stock_item['quantity']
        
        # Находим ADS для этого товара
        ads_item = ads_data[ads_data['item_code'] == item_code]
        if ads_item.empty:
            continue
        
        ads_value = ads_item.iloc[0]['ads']
        if ads_value <= 0:
            continue
        
        # Рассчитываем дни запаса
        days_stock = stock_qty / ads_value if ads_value > 0 else 0
        
        # Определяем тип филиала
        branch_type = get_branch_type(warehouse)
        parent = get_parent_warehouse(warehouse)
        
        # Логика рекомендаций
        if days_stock < 7:  # Критически мало
            recommendations.append({
                'item_code': item_code,
                'item_name': ads_item.iloc[0]['item_name'],
                'from_warehouse': parent if parent else WAREHOUSE_HIERARCHY["hub"],
                'to_warehouse': warehouse,
                'current_stock': stock_qty,
                'ads': ads_value,
                'days_stock': days_stock,
                'recommended_qty': max(1, int(ads_value * target_days - stock_qty)),
                'priority': 'ВЫСОКИЙ' if days_stock < 3 else 'СРЕДНИЙ',
                'reason': f'Запас на {days_stock:.1f} дней (критично)' if days_stock < 3 else f'Запас на {days_stock:.1f} дней (мало)'
            })
    
    return pd.DataFrame(recommendations)

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
st.title("🚀 Полная система анализа с автоматическими данными")
st.caption(f"Последнее обновление: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Боковая панель
with st.sidebar:
    st.header("🔄 Управление данными")
    
    if st.button("🔄 Обновить данные"):
        with st.spinner("Проверка новых файлов..."):
            accumulator.monitor_and_process_new_files()
            st.success("✅ Данные обновлены")
            time.sleep(1)
            st.rerun()
    
    # Статистика
    summary = accumulator.get_data_summary()
    
    st.subheader("📊 Статистика данных")
    if summary['sales']['total_records'] > 0:
        st.metric("Дней продаж", summary['sales']['days_count'])
        st.metric("Филиалов", summary['sales']['branches_count'])
        st.metric("Товаров", summary['sales']['items_count'])
        st.info(f"Период: {summary['sales']['first_date']} - {summary['sales']['last_date']}")
    
    if summary['stock']['total_records'] > 0:
        st.metric("Последние остатки", summary['stock']['latest_date'])
        st.metric("Складов", summary['stock']['warehouses_count'])

# Основные вкладки
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Общий анализ", 
    "🔄 Межфилиальные перемещения", 
    "📈 ADS анализ", 
    "🏪 Анализ по филиалам",
    "⚙️ Система"
])

with tab1:
    st.header("📊 Общий анализ")
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        period_option = st.selectbox(
            "Период анализа",
            ["Последние 7 дней", "Последние 30 дней", "Последние 90 дней", "Весь период"]
        )
        
        end_date = datetime.now().date()
        if period_option == "Последние 7 дней":
            start_date = end_date - timedelta(days=7)
        elif period_option == "Последние 30 дней":
            start_date = end_date - timedelta(days=30)
        elif period_option == "Последние 90 дней":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = None
            end_date = None
    
    # Загружаем данные
    sales_data = accumulator.get_sales_data(
        start_date=str(start_date) if start_date else None,
        end_date=str(end_date) if end_date else None
    )
    
    stock_data = accumulator.get_latest_stock()
    
    if not sales_data.empty:
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_amount = sales_data['amount'].sum()
            st.metric("Общие продажи", f"{total_amount:,.0f} ₸")
        
        with col2:
            total_qty = sales_data['quantity'].sum()
            st.metric("Продано товаров", f"{total_qty:,.0f}")
        
        with col3:
            unique_items = sales_data['item_code'].nunique()
            st.metric("Уникальных товаров", unique_items)
        
        with col4:
            avg_check = total_amount / len(sales_data) if len(sales_data) > 0 else 0
            st.metric("Средний чек", f"{avg_check:,.0f} ₸")
        
        # Динамика продаж
        st.subheader("📈 Динамика продаж")
        daily_sales = sales_data.groupby('date')['amount'].sum().reset_index()
        
        fig = px.line(daily_sales, x='date', y='amount', 
                     title='Продажи по дням')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("🔄 Межфилиальные перемещения")
    
    if not sales_data.empty and not stock_data.empty:
        # Генерируем рекомендации
        recommendations = generate_movement_recommendations(sales_data, stock_data)
        
        if not recommendations.empty:
            st.success(f"✅ Сгенерировано {len(recommendations)} рекомендаций")
            
            # Фильтры
            col1, col2 = st.columns(2)
            
            with col1:
                priority_filter = st.multiselect(
                    "Приоритет",
                    options=recommendations['priority'].unique(),
                    default=recommendations['priority'].unique()
                )
            
            with col2:
                warehouse_filter = st.multiselect(
                    "Склад назначения",
                    options=recommendations['to_warehouse'].unique(),
                    default=recommendations['to_warehouse'].unique()
                )
            
            # Применяем фильтры
            filtered_recs = recommendations[
                (recommendations['priority'].isin(priority_filter)) &
                (recommendations['to_warehouse'].isin(warehouse_filter))
            ]
            
            # Показываем рекомендации
            st.subheader("📋 Рекомендации по перемещениям")
            
            for priority in ['ВЫСОКИЙ', 'СРЕДНИЙ']:
                priority_recs = filtered_recs[filtered_recs['priority'] == priority]
                if not priority_recs.empty:
                    if priority == 'ВЫСОКИЙ':
                        st.error(f"🚨 КРИТИЧНО - {len(priority_recs)} рекомендаций")
                    else:
                        st.warning(f"⚠️ ВНИМАНИЕ - {len(priority_recs)} рекомендаций")
                    
                    st.dataframe(
                        priority_recs[[
                            'item_name', 'from_warehouse', 'to_warehouse', 
                            'current_stock', 'recommended_qty', 'days_stock', 'reason'
                        ]],
                        hide_index=True
                    )
        else:
            st.info("📝 Рекомендации по перемещениям будут сгенерированы после накопления данных")
    else:
        st.info("📝 Загрузите данные о продажах и остатках для анализа перемещений")

with tab3:
    st.header("📈 ADS анализ")
    
    if not sales_data.empty:
        # Расчет ADS
        ads_data = calculate_ads_from_sales(sales_data, 30)
        
        if not ads_data.empty:
            # Топ товаров по ADS
            top_ads = ads_data.nlargest(20, 'ads')
            
            fig = px.bar(top_ads, x='ads', y='item_name', 
                        orientation='h', title='Топ-20 товаров по ADS')
            st.plotly_chart(fig, use_container_width=True)
            
            # Таблица ADS
            st.subheader("📊 Детальный ADS анализ")
            st.dataframe(ads_data.sort_values('ads', ascending=False), hide_index=True)

with tab4:
    st.header("🏪 Анализ по филиалам")
    
    if not sales_data.empty:
        # Анализ по филиалам
        branch_analysis = sales_data.groupby('branch').agg({
            'amount': 'sum',
            'quantity': 'sum',
            'item_code': 'nunique'
        }).reset_index()
        
        branch_analysis.columns = ['Филиал', 'Сумма продаж', 'Количество', 'Уникальных товаров']
        
        # Добавляем тип филиала
        branch_analysis['Тип филиала'] = branch_analysis['Филиал'].apply(get_branch_type)
        
        # Группировка по типам
        type_summary = branch_analysis.groupby('Тип филиала').agg({
            'Сумма продаж': 'sum',
            'Количество': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 По типам филиалов")
            st.dataframe(type_summary, hide_index=True)
        
        with col2:
            fig = px.pie(type_summary, values='Сумма продаж', names='Тип филиала',
                        title='Распределение продаж по типам филиалов')
            st.plotly_chart(fig, use_container_width=True)
        
        # Детальный анализ
        st.subheader("📋 Детальный анализ по филиалам")
        st.dataframe(branch_analysis.sort_values('Сумма продаж', ascending=False), hide_index=True)

with tab5:
    st.header("⚙️ Система и настройки")
    
    # Информация о системе
    st.subheader("📊 Статус системы")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Статистика данных:**
        - Записей о продажах: {summary['sales']['total_records']:,}
        - Записей об остатках: {summary['stock']['total_records']:,}
        - Период данных: {summary['sales']['first_date']} - {summary['sales']['last_date']}
        """)
    
    with col2:
        st.success(f"""
        **Система работает:**
        - Автоматическое обновление: каждые 5 минут
        - Мониторинг файлов: активен
        - Накопление данных: включено
        """)
    
    # Проблемные данные
    missing_dates = accumulator.check_missing_dates()
    if missing_dates:
        st.warning(f"⚠️ Обнаружено {len(missing_dates)} пропущенных дней")
        with st.expander("Показать пропущенные даты"):
            st.write(missing_dates[:20])  # Показываем первые 20
    else:
        st.success("✅ Пропущенных дней не обнаружено")

# Футер
st.markdown("---")
st.caption("""
🔗 **Постоянные ссылки:**
- Вебхук для 1С: http://217.114.1.117:5000
- Эта аналитика: http://217.114.1.117:8502
""")