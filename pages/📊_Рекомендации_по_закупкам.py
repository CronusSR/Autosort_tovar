#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СТРАНИЦА РЕКОМЕНДАЦИЙ ПО ЗАКУПКАМ НА ОСНОВЕ ПРОДАЖ
Работает с данными продаж без остатков
"""

import sys
import os

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import plotly.express as px
import plotly.graph_objects as go
from json_1c_parser import Json1CParser
from multi_branch_analyzer import MultiBranchAnalyzer

# ===== КОНФИГУРАЦИЯ СТРАНИЦЫ =====

st.set_page_config(
    page_title="Рекомендации по закупкам",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ИЕРАРХИЯ ФИЛИАЛОВ =====

def get_branch_hierarchy():
    """Правильная иерархия филиалов для рекомендаций"""
    return {
        # 🏢 ГЛАВНЫЙ ХАБ
        'База Склад Фурнитура Комплект': {
            'type': 'hub',
            'level': 1,
            'city': 'Алматы',
            'supplier': 'external',
            'parent': None,
            'min_days_stock': 45,
            'max_days_stock': 90,
            'safety_multiplier': 1.5,
            'exclude_categories': False
        },
        
        # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба)
        'Казыбаева Склад Фурнитура TRADE': {
            'type': 'warehouse',
            'level': 2,
            'city': 'Алматы',
            'supplier': 'База Склад Фурнитура Комплект',
            'parent': 'База Склад Фурнитура Комплект',
            'min_days_stock': 20,
            'max_days_stock': 45,
            'safety_multiplier': 1.3,
            'exclude_categories': False
        },
        'склад фурнитура № 1': {
            'type': 'warehouse',
            'level': 2,
            'city': 'Астана',
            'supplier': 'База Склад Фурнитура Комплект',
            'parent': 'База Склад Фурнитура Комплект',
            'min_days_stock': 20,
            'max_days_stock': 45,
            'safety_multiplier': 1.3,
            'exclude_categories': False
        },
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
            'type': 'warehouse',
            'level': 2,
            'city': 'Шымкент',
            'supplier': 'База Склад Фурнитура Комплект',
            'parent': 'База Склад Фурнитура Комплект',
            'min_days_stock': 20,
            'max_days_stock': 45,
            'safety_multiplier': 1.3,
            'exclude_categories': True  # Особенность Шымкента
        },
        
        # 🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов)
        'Барыс Склад Фурнитура TRADE': {
            'type': 'store_direct',
            'level': 2,
            'city': 'Алматы',
            'supplier': 'База Склад Фурнитура Комплект',
            'parent': 'База Склад Фурнитура Комплект',
            'min_days_stock': 15,
            'max_days_stock': 35,
            'safety_multiplier': 1.2,
            'exclude_categories': False
        },
        'АО Склад Фурнитура TRADE': {  # Алтын Орда
            'type': 'store_direct',
            'level': 2,
            'city': 'Алматы',
            'supplier': 'База Склад Фурнитура Комплект',
            'parent': 'База Склад Фурнитура Комплект',
            'min_days_stock': 15,
            'max_days_stock': 35,
            'safety_multiplier': 1.2,
            'exclude_categories': True  # Особенность АО
        },
        
        # 🏪 МАГАЗИНЫ 3-ГО УРОВНЯ (питаются от складов 2-го уровня)
        'ТД Казыбаева ФУРНИТУРА магазин': {
            'type': 'store',
            'level': 3,
            'city': 'Алматы',
            'supplier': 'Казыбаева Склад Фурнитура TRADE',
            'parent': 'Казыбаева Склад Фурнитура TRADE',
            'min_days_stock': 10,
            'max_days_stock': 25,
            'safety_multiplier': 1.2,
            'exclude_categories': False
        },
        'Магазин фурнитуры': {
            'type': 'store',
            'level': 3,
            'city': 'Астана',
            'supplier': 'склад фурнитура № 1',
            'parent': 'склад фурнитура № 1',
            'min_days_stock': 10,
            'max_days_stock': 25,
            'safety_multiplier': 1.2,
            'exclude_categories': False
        },
        '6 Склад фурнитуры "Овощная база" Магазин': {
            'type': 'store',
            'level': 3,
            'city': 'Шымкент',
            'supplier': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
            'parent': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
            'min_days_stock': 10,
            'max_days_stock': 25,
            'safety_multiplier': 1.2,
            'exclude_categories': False
        }
    }

# ===== ОСНОВНАЯ ЛОГИКА =====

def main():
    """Основная функция страницы"""
    
    st.title("📊 Рекомендации по закупкам на основе продаж")
    st.markdown("---")
    
    # Загрузка данных продаж
    st.subheader("📈 Загрузка данных продаж")
    st.info("Загрузите JSON файлы с продажами для генерации рекомендаций по закупкам")
    
    uploaded_files = st.file_uploader(
        "Выберите JSON файлы с продажами",
        type=['json'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Обрабатываем данные
        sales_data = process_sales_files(uploaded_files)
        
        if sales_data:
            st.success(f"✅ Загружено {len(sales_data)} товаров из {len(uploaded_files)} файлов")
            
            # Выбор филиала для анализа
            st.subheader("🏢 Выбор филиала для анализа")
            
            available_branches = list(sales_data.keys())
            selected_branch = st.selectbox(
                "Выберите филиал:",
                available_branches,
                index=0 if available_branches else None
            )
            
            if selected_branch:
                branch_data = sales_data[selected_branch]
                
                # Показываем информацию о филиале
                hierarchy = get_branch_hierarchy()
                branch_config = hierarchy.get(selected_branch, {})
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Товаров", len(branch_data))
                with col2:
                    total_ads = sum(p['ads'] for p in branch_data.values())
                    st.metric("Общий ADS", f"{total_ads:.2f}")
                with col3:
                    total_revenue = sum(p['revenue'] for p in branch_data.values())
                    st.metric("Общая выручка", f"{total_revenue:,.0f}")
                
                # Информация о филиале
                if branch_config:
                    st.info(f"""
                    🏢 **{selected_branch}** ({branch_config.get('city', 'Неизвестно')})
                    - Тип: {branch_config.get('type', 'неизвестен')}
                    - Поставщик: {branch_config.get('supplier', 'неизвестен')}
                    - Нормативы запасов: {branch_config.get('min_days_stock', 0)}-{branch_config.get('max_days_stock', 0)} дней
                    """)
                
                # Настройки рекомендаций
                st.subheader("⚙️ Настройки рекомендаций")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    safety_multiplier = st.slider(
                        "Коэффициент безопасности",
                        0.8, 2.0, 
                        branch_config.get('safety_multiplier', 1.2), 
                        0.1
                    )
                
                with col2:
                    min_ads_threshold = st.number_input(
                        "Минимальный ADS для рекомендаций",
                        min_value=0.0,
                        value=10.0,
                        step=1.0
                    )
                
                # Генерация рекомендаций
                if st.button("🚀 Сгенерировать рекомендации", type="primary"):
                    with st.spinner("Генерация рекомендаций..."):
                        recommendations = generate_procurement_recommendations(
                            branch_data, 
                            branch_config, 
                            safety_multiplier, 
                            min_ads_threshold
                        )
                        
                        if recommendations:
                            st.session_state['current_recommendations'] = recommendations
                            st.session_state['current_branch'] = selected_branch
                            st.success(f"✅ Создано {len(recommendations)} рекомендаций!")
                            show_recommendations(recommendations, selected_branch)
                        else:
                            st.warning("⚠️ Рекомендации не найдены с текущими настройками")
                
                # Показываем сохраненные рекомендации
                if 'current_recommendations' in st.session_state:
                    st.markdown("---")
                    st.subheader("💾 Сохраненные рекомендации")
                    show_recommendations(
                        st.session_state['current_recommendations'], 
                        st.session_state['current_branch']
                    )
                    
                    # Экспорт
                    st.markdown("---")
                    if st.button("📥 Экспорт в Excel"):
                        export_recommendations_to_excel(
                            st.session_state['current_recommendations'],
                            st.session_state['current_branch']
                        )
                
                # ABC анализ
                st.markdown("---")
                st.subheader("📈 ABC анализ")
                show_abc_analysis(branch_data)
    
    else:
        st.warning("⚠️ Загрузите JSON файлы с продажами для начала работы")
    
    # Боковая панель
    show_sidebar_info()

def process_sales_files(uploaded_files):
    """Обработка загруженных файлов продаж"""
    
    parser = Json1CParser()
    all_sales_data = {}
    
    try:
        for file in uploaded_files:
            # Читаем JSON файл
            content = json.loads(file.read())
            
            # Парсим данные
            sales_result = parser.parse_sales_json_from_data(content)
            
            # Объединяем данные
            for branch_name, products in sales_result['sales_by_branch'].items():
                if branch_name not in all_sales_data:
                    all_sales_data[branch_name] = {}
                
                for product in products:
                    product_name = product['product_name']
                    
                    if product_name not in all_sales_data[branch_name]:
                        all_sales_data[branch_name][product_name] = {
                            'ads': 0,
                            'revenue': 0,
                            'quantity': 0,
                            'unit': product.get('unit', 'шт'),
                            'category_path': product.get('category_path', ''),
                            'article': product.get('article', ''),
                            'manufacturer': product.get('manufacturer', '')
                        }
                    
                    # Суммируем данные
                    all_sales_data[branch_name][product_name]['ads'] += product['ads']
                    all_sales_data[branch_name][product_name]['revenue'] += product['revenue']
                    all_sales_data[branch_name][product_name]['quantity'] += product['quantity']
        
        return all_sales_data
        
    except Exception as e:
        st.error(f"❌ Ошибка обработки файлов: {str(e)}")
        return None

def generate_procurement_recommendations(branch_data, branch_config, safety_multiplier, min_ads_threshold):
    """Генерация рекомендаций по закупкам"""
    
    recommendations = []
    
    # Получаем только товары выше порога ADS
    filtered_products = {
        name: data for name, data in branch_data.items() 
        if data['ads'] >= min_ads_threshold
    }
    
    # Сортируем по ADS
    sorted_products = sorted(filtered_products.items(), key=lambda x: x[1]['ads'], reverse=True)
    
    for product_name, product_data in sorted_products:
        ads = product_data['ads']
        
        # Рассчитываем нормативы
        min_stock = ads * branch_config.get('min_days_stock', 15) * safety_multiplier
        max_stock = ads * branch_config.get('max_days_stock', 30) * safety_multiplier
        reorder_point = ads * (branch_config.get('min_days_stock', 15) + 5)  # +5 дней на доставку
        
        # Определяем приоритет
        if ads >= 1000:
            priority = 'Высокий'
        elif ads >= 100:
            priority = 'Средний'
        else:
            priority = 'Низкий'
        
        # Определяем категорию ABC
        # Будет рассчитано позже в show_abc_analysis
        
        recommendations.append({
            'product_name': product_name,
            'ads': ads,
            'min_stock': min_stock,
            'max_stock': max_stock,
            'reorder_point': reorder_point,
            'priority': priority,
            'unit': product_data['unit'],
            'category_path': product_data['category_path'],
            'revenue': product_data['revenue'],
            'quantity': product_data['quantity'],
            'article': product_data['article'],
            'manufacturer': product_data['manufacturer']
        })
    
    return recommendations

def show_recommendations(recommendations, branch_name):
    """Отображение рекомендаций"""
    
    if not recommendations:
        st.warning("Нет рекомендаций для отображения")
        return
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        priority_filter = st.selectbox(
            "Фильтр по приоритету",
            ['Все', 'Высокий', 'Средний', 'Низкий']
        )
    
    with col2:
        show_count = st.selectbox(
            "Количество товаров",
            [10, 25, 50, 100, 'Все']
        )
    
    # Применяем фильтры
    filtered_recs = recommendations
    if priority_filter != 'Все':
        filtered_recs = [r for r in filtered_recs if r['priority'] == priority_filter]
    
    if show_count != 'Все':
        filtered_recs = filtered_recs[:show_count]
    
    # Создаем DataFrame для отображения
    display_data = []
    for rec in filtered_recs:
        display_data.append({
            'Товар': rec['product_name'][:60] + '...' if len(rec['product_name']) > 60 else rec['product_name'],
            'ADS': f"{rec['ads']:.2f}",
            'Мин. запас': f"{rec['min_stock']:.0f}",
            'Макс. запас': f"{rec['max_stock']:.0f}",
            'Точка заказа': f"{rec['reorder_point']:.0f}",
            'Единица': rec['unit'],
            'Приоритет': rec['priority'],
            'Выручка': f"{rec['revenue']:,.0f}"
        })
    
    if display_data:
        st.dataframe(
            pd.DataFrame(display_data),
            use_container_width=True,
            height=400
        )
        
        # Статистика
        st.subheader("📊 Статистика рекомендаций")
        
        high_priority = len([r for r in filtered_recs if r['priority'] == 'Высокий'])
        medium_priority = len([r for r in filtered_recs if r['priority'] == 'Средний'])
        low_priority = len([r for r in filtered_recs if r['priority'] == 'Низкий'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего товаров", len(filtered_recs))
        with col2:
            st.metric("Высокий приоритет", high_priority)
        with col3:
            st.metric("Средний приоритет", medium_priority)
        with col4:
            st.metric("Низкий приоритет", low_priority)

def show_abc_analysis(branch_data):
    """Показать ABC анализ"""
    
    # Подготавливаем данные для ABC анализа
    products_list = []
    for product_name, data in branch_data.items():
        products_list.append({
            'product_name': product_name,
            'revenue': data['revenue'],
            'ads': data['ads']
        })
    
    # Сортируем по выручке
    products_list.sort(key=lambda x: x['revenue'], reverse=True)
    
    # Рассчитываем накопленную выручку
    total_revenue = sum(p['revenue'] for p in products_list)
    cumulative_revenue = 0
    
    abc_categories = {'A': [], 'B': [], 'C': []}
    
    for product in products_list:
        cumulative_revenue += product['revenue']
        cumulative_percent = (cumulative_revenue / total_revenue) * 100
        
        if cumulative_percent <= 80:
            abc_categories['A'].append(product)
        elif cumulative_percent <= 95:
            abc_categories['B'].append(product)
        else:
            abc_categories['C'].append(product)
    
    # Отображаем результаты
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("A категория (80% выручки)", len(abc_categories['A']))
    with col2:
        st.metric("B категория (15% выручки)", len(abc_categories['B']))
    with col3:
        st.metric("C категория (5% выручки)", len(abc_categories['C']))
    
    # График ABC анализа
    fig = go.Figure()
    
    categories = ['A', 'B', 'C']
    counts = [len(abc_categories[cat]) for cat in categories]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    fig.add_trace(go.Bar(
        x=categories,
        y=counts,
        marker_color=colors,
        text=counts,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Распределение товаров по категориям ABC",
        xaxis_title="Категория",
        yaxis_title="Количество товаров",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def export_recommendations_to_excel(recommendations, branch_name):
    """Экспорт рекомендаций в Excel"""
    
    from io import BytesIO
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Рекомендации
        df_recommendations = pd.DataFrame(recommendations)
        df_recommendations.to_excel(writer, sheet_name='Рекомендации', index=False)
    
    output.seek(0)
    
    st.download_button(
        label="📥 Скачать рекомендации Excel",
        data=output.getvalue(),
        file_name=f"procurement_recommendations_{branch_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def show_sidebar_info():
    """Информация в боковой панели"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ О системе")
    
    st.sidebar.markdown("""
    **Система рекомендаций по закупкам**
    
    Генерирует рекомендации на основе:
    - ADS (Average Daily Sales)
    - Нормативов запасов по типам филиалов
    - Коэффициентов безопасности
    - ABC анализа товаров
    
    **Типы филиалов:**
    - Магазин: 10-25 дней запаса
    - Склад: 20-45 дней запаса  
    - Хаб: 45-90 дней запаса
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Метрики")
    
    st.sidebar.markdown("""
    **ADS** - Средние дневные продажи
    **Мин. запас** - Минимальный запас товара
    **Макс. запас** - Максимальный запас товара
    **Точка заказа** - Остаток для нового заказа
    """)

# ===== ЗАПУСК СТРАНИЦЫ =====

if __name__ == "__main__":
    main()