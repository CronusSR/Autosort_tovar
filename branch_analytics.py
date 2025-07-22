#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальная аналитика по филиалам с ABC анализом, рейтингами и анализом оборачиваемости
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from typing import Dict, List, Any
import numpy as np

class BranchAnalytics:
    """Система детальной аналитики по филиалам"""
    
    def __init__(self):
        self.abc_thresholds = {
            'A': 0.86,  # 86% от общих продаж
            'B': 0.14,  # средний уровень  
            'C': 0.00   # низкий уровень
        }
        
    def load_branch_data(self, branch_key: str) -> Dict[str, Any]:
        """Загрузка данных филиала"""
        try:
            # Читаем основную информацию
            with open('ads/combined_ads_data.json', 'r', encoding='utf-8') as f:
                combined_data = json.load(f)
            
            if branch_key not in combined_data['branches']:
                return {'success': False, 'error': f'Филиал {branch_key} не найден'}
            
            branch_info = combined_data['branches'][branch_key]
            
            # Читаем данные ADS филиала
            ads_file = f"ads/{branch_info['ads_file']}"
            if not os.path.exists(ads_file):
                return {'success': False, 'error': f'Файл данных {ads_file} не найден'}
            
            with open(ads_file, 'r', encoding='utf-8') as f:
                ads_data = json.load(f)
            
            return {
                'success': True,
                'branch_info': branch_info,
                'ads_data': ads_data['ads_data'],
                'updated': ads_data.get('updated', 'Неизвестно')
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_abc_analysis(self, ads_data: Dict) -> Dict[str, Any]:
        """Расчет ABC анализа для филиала"""
        if not ads_data:
            return {'success': False, 'error': 'Нет данных для анализа'}
        
        # Преобразуем в DataFrame
        items_data = []
        for item_name, item_info in ads_data.items():
            items_data.append({
                'товар': item_name,
                'ads': item_info['среднедневные_продажи'],
                'общие_продажи': item_info['общие_продажи'],
                'категория': item_info.get('категория', 'Без категории'),
                'подкатегория': item_info.get('подкатегория', 'Без подкатегории'),
                'источник_ads': item_info.get('источник_ads', 'продажи')
            })
        
        df = pd.DataFrame(items_data)
        
        # Сортируем по общим продажам по убыванию
        df = df.sort_values('общие_продажи', ascending=False)
        
        # Рассчитываем кумулятивные проценты
        total_sales = df['общие_продажи'].sum()
        df['процент_от_общих'] = (df['общие_продажи'] / total_sales) * 100
        df['кумулятивный_процент'] = df['процент_от_общих'].cumsum()
        
        # КАРДИНАЛЬНО НОВЫЙ ПОДХОД: ABC анализ на основе ADS с учетом продаж
        # Сначала создаем временный индекс важности для сортировки
        max_sales = df['общие_продажи'].max()
        max_ads = df['ads'].max()
        
        # Нормализуем показатели к шкале 0-100
        df['norm_sales'] = (df['общие_продажи'] / max_sales) * 100
        df['norm_ads'] = (df['ads'] / max_ads) * 100
        
        # Формула для сортировки (для правильного порядка)
        df['importance_index'] = (df['norm_sales'] * 0.5) + (df['norm_ads'] * 0.5)
        
        # Пересортировка по индексу важности
        df = df.sort_values('importance_index', ascending=False)
        
        # ПРАВИЛЬНЫЙ ABC АНАЛИЗ ПО ПАРЕТО (80/20)
        df['abc_класс'] = 'C'  # По умолчанию все C
        
        # Сортируем по продажам для правильного кумулятивного расчета
        df = df.sort_values('общие_продажи', ascending=False)
        
        # Пересчитываем кумулятивные проценты после сортировки по продажам
        df['кумулятивный_процент'] = df['процент_от_общих'].cumsum()
        
        # КЛАССИЧЕСКИЙ ABC АНАЛИЗ ПО ПАРЕТО
        # A класс: товары, которые дают 80% от общих продаж
        df.loc[df['кумулятивный_процент'] <= 80, 'abc_класс'] = 'A'
        
        # B класс: товары от 80% до 95% кумулятивных продаж
        df.loc[(df['кумулятивный_процент'] > 80) & (df['кумулятивный_процент'] <= 95), 'abc_класс'] = 'B'
        
        # C класс: остальные товары (от 95% до 100%)
        
        # Теперь пересортировываем по индексу важности для отображения
        df = df.sort_values('importance_index', ascending=False)
        
        # ДИАГНОСТИКА: проверяем несколько первых товаров
        print("=== ДИАГНОСТИКА ABC АНАЛИЗА ===")
        print("Первые 10 товаров:")
        for i, row in df.head(10).iterrows():
            print(f"{row['товар'][:50]}... | Продажи: {row['общие_продажи']:,.0f} | Кумулятивный %: {row['кумулятивный_процент']:.1f} | ABC: {row['abc_класс']}")
        
        print("\nПоследние 10 товаров:")
        for i, row in df.tail(10).iterrows():
            print(f"{row['товар'][:50]}... | Продажи: {row['общие_продажи']:,.0f} | Кумулятивный %: {row['кумулятивный_процент']:.1f} | ABC: {row['abc_класс']}")
        
        # Проверяем товары с высоким ADS в классе C
        high_ads_c_items = df[(df['abc_класс'] == 'C') & (df['ads'] > 5)]
        if len(high_ads_c_items) > 0:
            print(f"\n❌ ПРОБЛЕМА: {len(high_ads_c_items)} товаров класса C с ADS > 5:")
            for i, row in high_ads_c_items.head(5).iterrows():
                print(f"  {row['товар'][:50]}... | ADS: {row['ads']:.3f} | Продажи: {row['общие_продажи']:,.0f} | Кумулятивный %: {row['кумулятивный_процент']:.1f}")
        
        # Рассчитываем индивидуальный рейтинг товара (0-100)
        max_sales = df['общие_продажи'].max()
        df['рейтинг_товара'] = ((df['общие_продажи'] / max_sales) * 100).round(1)
        
        # Анализ оборачиваемости (продажи в день)
        df['оборачиваемость'] = df['ads'].round(3)
        
        # Статус оборачиваемости
        median_turnover = df['оборачиваемость'].median()
        df['статус_оборачиваемости'] = 'Средняя'
        df.loc[df['оборачиваемость'] > median_turnover * 1.5, 'статус_оборачиваемости'] = 'Высокая'
        df.loc[df['оборачиваемость'] < median_turnover * 0.5, 'статус_оборачиваемости'] = 'Низкая'
        
        # Статистика по ABC классам
        abc_stats = {
            'A': {
                'товаров': len(df[df['abc_класс'] == 'A']),
                'процент_товаров': round((len(df[df['abc_класс'] == 'A']) / len(df)) * 100, 1),
                'процент_продаж': round(df[df['abc_класс'] == 'A']['процент_от_общих'].sum(), 1),
                'средний_ads': round(df[df['abc_класс'] == 'A']['ads'].mean(), 3)
            },
            'B': {
                'товаров': len(df[df['abc_класс'] == 'B']),
                'процент_товаров': round((len(df[df['abc_класс'] == 'B']) / len(df)) * 100, 1),
                'процент_продаж': round(df[df['abc_класс'] == 'B']['процент_от_общих'].sum(), 1),
                'средний_ads': round(df[df['abc_класс'] == 'B']['ads'].mean(), 3)
            },
            'C': {
                'товаров': len(df[df['abc_класс'] == 'C']),
                'процент_товаров': round((len(df[df['abc_класс'] == 'C']) / len(df)) * 100, 1),
                'процент_продаж': round(df[df['abc_класс'] == 'C']['процент_от_общих'].sum(), 1),
                'средний_ads': round(df[df['abc_класс'] == 'C']['ads'].mean(), 3)
            }
        }
        
        # Анализ по категориям
        category_analysis = df.groupby('категория').agg({
            'товар': 'count',
            'общие_продажи': 'sum',
            'ads': 'mean'
        }).rename(columns={
            'товар': 'количество_товаров',
            'общие_продажи': 'общие_продажи_категории',
            'ads': 'средний_ads_категории'
        }).round(3)
        
        # Анализ по подкатегориям
        subcategory_analysis = df.groupby(['категория', 'подкатегория']).agg({
            'товар': 'count',
            'общие_продажи': 'sum',
            'ads': 'mean'
        }).rename(columns={
            'товар': 'количество_товаров',
            'общие_продажи': 'общие_продажи_подкатегории',
            'ads': 'средний_ads_подкатегории'
        }).round(3)
        
        return {
            'success': True,
            'dataframe': df,
            'abc_stats': abc_stats,
            'category_analysis': category_analysis,
            'subcategory_analysis': subcategory_analysis,
            'total_items': len(df),
            'total_sales': total_sales,
            'avg_turnover': median_turnover
        }
    
    def show_all_branches_a_category_summary(self, combined_data: Dict):
        """Показывает товары A категории по всем филиалам"""
        st.write("**📊 Сводка по товарам высокого приоритета (класс A) в каждом филиале:**")
        
        # Загружаем данные всех филиалов
        all_a_items = {}
        friendly_names = {
            'казыбаева_магазин': '🏪 ТД Казыбаева Магазин',
            'казыбаева_склад': '📦 ТД Казыбаева Склад', 
            'барыс': '🏢 Барыс Склад',
            'ао_склад': '🏭 АО Склад',
            'астана_магазин': '🏪 Астана Магазин',
            'астана_склад': '📦 Астана Склад',
            'шымкент_магазин': '🏪 Шымкент Магазин',
            'шымкент_склад': '📦 Шымкент Склад'
        }
        
        for branch_key, branch_info in combined_data['branches'].items():
            branch_data = self.load_branch_data(branch_key)
            if branch_data['success']:
                analysis = self.calculate_abc_analysis(branch_data['ads_data'])
                if analysis['success']:
                    df = analysis['dataframe']
                    a_items = df[df['abc_класс'] == 'A']
                    
                    friendly_name = friendly_names.get(branch_key, branch_key)
                    all_a_items[friendly_name] = {
                        'items': a_items,
                        'count': len(a_items),
                        'total_sales': a_items['общие_продажи'].sum() if len(a_items) > 0 else 0,
                        'avg_ads': a_items['ads'].mean() if len(a_items) > 0 else 0
                    }
        
        # Показываем статистику
        st.subheader("📈 Общая статистика по A-товарам")
        col1, col2, col3, col4 = st.columns(4)
        
        total_a_items = sum([data['count'] for data in all_a_items.values()])
        total_a_sales = sum([data['total_sales'] for data in all_a_items.values()])
        avg_a_items_per_branch = total_a_items / len(all_a_items) if all_a_items else 0
        
        with col1:
            st.metric("🏆 Всего A-товаров", total_a_items)
        with col2:
            st.metric("💰 Общие продажи A", f"{total_a_sales:,.0f}")
        with col3:
            st.metric("📊 Среднее на филиал", f"{avg_a_items_per_branch:.1f}")
        with col4:
            st.metric("🏢 Филиалов", len(all_a_items))
        
        # Показываем детали по каждому филиалу
        st.subheader("🏪 A-товары по филиалам")
        
        for branch_name, data in all_a_items.items():
            with st.expander(f"{branch_name} - {data['count']} товаров класса A", expanded=False):
                if data['count'] > 0:
                    col1, col2 = st.columns([3, 1])
                    
                    with col2:
                        st.metric("Количество", data['count'])
                        st.metric("Продажи", f"{data['total_sales']:,.0f}")
                        st.metric("Средний ADS", f"{data['avg_ads']:.3f}")
                    
                    with col1:
                        st.write("**🏆 ВСЕ товары класса A:**")
                        for i, (_, item) in enumerate(data['items'].iterrows(), 1):
                            st.write(f"**{i}.** {item['товар']}")
                            st.caption(f"ADS: {item['ads']:.3f} | Продажи: {item['общие_продажи']:,.0f} | Важность: {item['importance_index']:.1f}")
                else:
                    st.write("❌ Нет товаров класса A")
    
    def create_branch_analytics_page(self):
        """Создание страницы аналитики филиалов"""
        st.header("🏪 Детальная аналитика по филиалам")
        
        # Проверяем наличие данных
        if not os.path.exists('ads/combined_ads_data.json'):
            st.warning("⚠️ Данные филиалов не найдены. Сначала загрузите единый файл продаж.")
            return
        
        # Загружаем список филиалов
        with open('ads/combined_ads_data.json', 'r', encoding='utf-8') as f:
            combined_data = json.load(f)
        
        st.success(f"""
        🎯 **Система готова к анализу: {combined_data['branches_count']} филиалов**
        
        **Классический ABC анализ по Парето:**
        • 📊 Чистый принцип 80/20 по кумулятивной доле продаж
        • 🥇 Класс A: товары дающие 80% от общих продаж
        • 🥈 Класс B: товары дающие 80-95% от общих продаж
        • 🥉 Класс C: товары дающие 95-100% от общих продаж
        • 💡 Основа для принятия решений по управлению запасами
        
        *Обновлено: {combined_data['updated']}*
        """)
        
        # Быстрые кнопки для переключения между филиалами
        st.subheader("🚀 Быстрый выбор филиала")
        
        cols = st.columns(4)
        branch_friendly_names = {
            'казыбаева_магазин': '🏪 Казыбаева Маг.',
            'казыбаева_склад': '📦 Казыбаева Скл.', 
            'барыс': '🏢 Барыс',
            'ао_склад': '🏭 АО Склад',
            'астана_магазин': '🏪 Астана Маг.',
            'астана_склад': '📦 Астана Скл.',
            'шымкент_магазин': '🏪 Шымкент Маг.',
            'шымкент_склад': '📦 Шымкент Скл.'
        }
        
        branch_keys = list(combined_data['branches'].keys())
        for i, branch_key in enumerate(branch_keys):
            col_idx = i % 4
            with cols[col_idx]:
                branch_info = combined_data['branches'][branch_key]
                friendly = branch_friendly_names.get(branch_key, branch_key)
                if st.button(f"{friendly}\n{branch_info['items_count']} тов.", 
                           key=f"quick_{branch_key}", 
                           use_container_width=True):
                    st.session_state.selected_branch_quick = branch_key
        
        # Основной селектор
        branch_options = {}
        for branch_key, branch_info in combined_data['branches'].items():
            friendly_name = branch_friendly_names.get(branch_key, branch_key)
            display_name = f"{friendly_name} ({branch_info['items_count']} товаров)"
            branch_options[display_name] = branch_key
        
        # Устанавливаем значение из быстрых кнопок если есть
        default_index = 0
        if 'selected_branch_quick' in st.session_state:
            for idx, (display, key) in enumerate(branch_options.items()):
                if key == st.session_state.selected_branch_quick:
                    default_index = idx
                    break
        
        selected_display = st.selectbox(
            "🎯 Или выберите из списка:",
            options=list(branch_options.keys()),
            key="branch_selector",
            help="Выберите филиал для получения ABC анализа и практических рекомендаций",
            index=default_index
        )
        
        # Показываем сводку по товарам A категории во всех филиалах
        with st.expander("🏆 Товары класса A по всем филиалам", expanded=True):
            self.show_all_branches_a_category_summary(combined_data)
        
        st.markdown("---")
        st.header("📊 Детальный анализ выбранного филиала")
        st.info("👇 **Выберите филиал выше и получите полный ABC анализ с графиками и рекомендациями**")
        
        if selected_display:
            selected_branch = branch_options[selected_display]
            with st.spinner(f'Загрузка анализа для {selected_display}...'):
                self.show_branch_detailed_analysis(selected_branch)
        else:
            st.warning("⚠️ Выберите филиал из списка выше для детального анализа")
    
    def show_branch_detailed_analysis(self, branch_key: str):
        """Показ детального анализа филиала"""
        
        # Загружаем данные филиала
        branch_data = self.load_branch_data(branch_key)
        
        if not branch_data['success']:
            st.error(f"❌ {branch_data['error']}")
            return
        
        # Выполняем ABC анализ
        analysis = self.calculate_abc_analysis(branch_data['ads_data'])
        
        if not analysis['success']:
            st.error(f"❌ {analysis['error']}")
            return
        
        # Заголовок филиала с понятным названием
        friendly_names = {
            'казыбаева_магазин': '🏪 ТД Казыбаева Магазин',
            'казыбаева_склад': '📦 ТД Казыбаева Склад', 
            'барыс': '🏢 Барыс Склад',
            'ао_склад': '🏭 АО Склад',
            'астана_магазин': '🏪 Астана Магазин',
            'астана_склад': '📦 Астана Склад',
            'шымкент_магазин': '🏪 Шымкент Магазин',
            'шымкент_склад': '📦 Шымкент Склад'
        }
        
        friendly_name = friendly_names.get(branch_key, branch_key)
        st.header(f"📊 Анализ: {friendly_name}")
        
        # Основные метрики в более понятном виде
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Ассортимент", f"{analysis['total_items']} товаров")
        with col2:
            st.metric("💰 Продажи за год", f"{analysis['total_sales']:,.0f}")
        with col3:
            st.metric("📈 Оборот в день", f"{analysis['avg_turnover']:.2f}")
        with col4:
            st.metric("📂 Категорий", len(analysis['category_analysis']))
        
        # Диагностическая информация
        df = analysis['dataframe']
        
        # Информация о ABC анализе
        st.info(f"""
        📊 **Результаты классического ABC анализа по Парето:**
        
        • **A товары**: {len(df[df['abc_класс'] == 'A'])} позиций ({len(df[df['abc_класс'] == 'A'])/len(df)*100:.1f}% ассортимента)
        • **B товары**: {len(df[df['abc_класс'] == 'B'])} позиций ({len(df[df['abc_класс'] == 'B'])/len(df)*100:.1f}% ассортимента)  
        • **C товары**: {len(df[df['abc_класс'] == 'C'])} позиций ({len(df[df['abc_класс'] == 'C'])/len(df)*100:.1f}% ассортимента)
        
        *Распределение основано исключительно на кумулятивной доле продаж (принцип Парето 80/20)*
        """)
        
        
        # ПОЛНЫЙ СПИСОК A ТОВАРОВ - ВЫШЕ ВСЕГО!
        df = analysis['dataframe']
        a_items_full = df[df['abc_класс'] == 'A']
        
        if len(a_items_full) > 0:
            st.markdown("---")
            st.header(f"🏆 Полный список товаров класса A: {len(a_items_full)} позиций")
            
            st.info(f"""
            **🎯 Это ваши САМЫЕ ВАЖНЫЕ товары!**
            
            Товары попали в класс A по принципу Парето:
            • 📊 Дают 80% от общих продаж филиала
            • 🎯 Это классический ABC анализ (правило 80/20)
            
            **Общая статистика A-товаров:**
            • Общий доход: {a_items_full['общие_продажи'].sum():,.0f}
            • Средний ADS: {a_items_full['ads'].mean():.2f}
            • Доля в продажах: {a_items_full['процент_от_общих'].sum():.1f}%
            """)
            
            # Красивое оформление списка A товаров
            st.subheader("📋 Детальный список")
            
            # Пояснение статусов
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
                <h4 style="margin: 0 0 10px 0; color: #1f2937;">📊 Статусы товаров по интенсивности продаж (ADS):</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div style="color: #1f2937;">🔴 <strong>ГОРЯЧИЙ</strong> - ADS ≥ 100 (экстремальный спрос)</div>
                    <div style="color: #1f2937;">🟢 <strong>СТАБИЛЬНЫЙ</strong> - ADS 50-100 (высокий спрос)</div>
                    <div style="color: #1f2937;">🔵 <strong>ЦЕННЫЙ</strong> - ADS 30-50 (хороший оборот)</div>
                    <div style="color: #1f2937;">🟡 <strong>ВАЖНЫЙ</strong> - ADS < 30 (важен по объему продаж)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Группируем по категориям для красоты
            categories = a_items_full['категория'].unique()
            
            for category in sorted(categories):
                category_items = a_items_full[a_items_full['категория'] == category]
                
                with st.expander(f"📂 {category} ({len(category_items)} товаров)", expanded=True):
                    # Сортируем по важности внутри категории
                    category_items = category_items.sort_values('importance_index', ascending=False)
                    
                    cols = st.columns(2)
                    for i, (_, item) in enumerate(category_items.iterrows()):
                        col_idx = i % 2
                        
                        with cols[col_idx]:
                            # Определяем статус по ADS
                            if item['ads'] >= 100:
                                status = "🔥 ГОРЯЧИЙ"
                                color = "🔴"
                            elif item['ads'] >= 50:
                                status = "📈 СТАБИЛЬНЫЙ"
                                color = "🟢"
                            elif item['ads'] >= 30:
                                status = "💎 ЦЕННЫЙ"
                                color = "🔵"
                            else:
                                status = "⭐ ВАЖНЫЙ"
                                color = "🟡"
                            
                            st.markdown(f"""
                            <div style="border: 2px solid #ff6b6b; border-radius: 10px; padding: 15px; margin: 10px 0; background: linear-gradient(45deg, #fff5f5, #ffffff);">
                                <h4 style="margin: 0; color: #d63031;">{color} {item['товар']}</h4>
                                <p style="margin: 5px 0; font-size: 14px; color: #2d3436;">
                                    <strong>Статус:</strong> {status}<br>
                                    <strong>ADS:</strong> {item['ads']:.3f} шт/день<br>
                                    <strong>Продажи:</strong> {item['общие_продажи']:,.0f}<br>
                                    <strong>Подкатегория:</strong> {item['подкатегория']}<br>
                                    <strong>Важность:</strong> {item['importance_index']:.1f}/100
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Кнопка экспорта
            st.markdown("---")
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                if st.button("📤 Экспорт всех A-товаров в Excel", type="primary", use_container_width=True):
                    # Подготавливаем данные для экспорта
                    export_data = a_items_full[['товар', 'ads', 'общие_продажи', 'рейтинг_товара', 
                                             'категория', 'подкатегория', 'importance_index']].copy()
                    export_data.columns = ['Товар', 'ADS (шт/день)', 'Общие продажи', 'Рейтинг', 
                                         'Категория', 'Подкатегория', 'Индекс важности']
                    export_data = export_data.round(3)
                    
                    # Конвертируем в CSV
                    csv = export_data.to_csv(index=False, encoding='utf-8-sig')
                    
                    import datetime
                    
                    st.download_button(
                        label="💾 Скачать A-товары",
                        data=csv,
                        file_name=f"A_товары_приоритет_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        # Графики
        self.create_abc_charts(analysis)
        
        # Анализ по категориям
        self.show_category_analysis(analysis)
        
        # Детальная таблица товаров
        self.show_detailed_items_table(analysis)
    
    def create_abc_charts(self, analysis: Dict):
        """Создание понятных графиков ABC анализа"""
        df = analysis['dataframe']
        
        # 1. Простое ABC распределение в виде метрик
        st.subheader("📊 ABC Анализ - Ключевые показатели")
        
        abc_a = df[df['abc_класс'] == 'A']
        abc_b = df[df['abc_класс'] == 'B'] 
        abc_c = df[df['abc_класс'] == 'C']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🥇 Класс A - Высокая важность
            **Товары с максимальной значимостью**
            """)
            st.metric("Товаров", len(abc_a))
            st.metric("% от продаж", f"{abc_a['процент_от_общих'].sum():.1f}%")
            st.metric("Средний ADS", f"{abc_a['ads'].mean():.3f}")
            st.metric("Индекс важности", f"{abc_a['importance_index'].mean():.1f}")
        
        with col2:
            st.markdown("""
            ### 🥈 Класс B - Средняя важность
            **Товары с умеренной значимостью**
            """)
            st.metric("Товаров", len(abc_b))
            st.metric("% от продаж", f"{abc_b['процент_от_общих'].sum():.1f}%")
            st.metric("Средний ADS", f"{abc_b['ads'].mean():.3f}")
            st.metric("Индекс важности", f"{abc_b['importance_index'].mean():.1f}")
        
        with col3:
            st.markdown("""
            ### 🥉 Класс C - Низкая важность
            **Товары для оптимизации**
            """)
            st.metric("Товаров", len(abc_c))
            st.metric("% от продаж", f"{abc_c['процент_от_общих'].sum():.1f}%")
            st.metric("Средний ADS", f"{abc_c['ads'].mean():.3f}")
            st.metric("Индекс важности", f"{abc_c['importance_index'].mean():.1f}")
        
        # 2. Простая гистограмма топ товаров
        st.subheader("🏆 Топ-10 товаров по продажам")
        
        top_items = df.head(10)
        
        fig_top = px.bar(
            top_items,
            x='общие_продажи',
            y='товар',
            orientation='h',
            title='Лидеры продаж',
            labels={'общие_продажи': 'Продажи', 'товар': 'Товар'},
            color='abc_класс',
            color_discrete_map={'A': '#2E8B57', 'B': '#4682B4', 'C': '#CD853F'}
        )
        fig_top.update_layout(height=400, showlegend=True)
        st.plotly_chart(fig_top, use_container_width=True)
    
    def show_category_analysis(self, analysis: Dict):
        """Показ простого анализа по категориям"""
        st.subheader("📂 Анализ по категориям")
        
        category_df = analysis['category_analysis'].reset_index()
        category_df['процент_от_общих_продаж'] = (
            category_df['общие_продажи_категории'] / analysis['total_sales'] * 100
        ).round(1)
        
        # Сортируем по продажам
        category_df = category_df.sort_values('общие_продажи_категории', ascending=False)
        
        # Показываем топ-5 категорий в метриках
        st.write("**🏆 Топ-5 категорий по продажам:**")
        
        top_categories = category_df.head(5)
        cols = st.columns(min(len(top_categories), 5))
        
        for i, (_, cat) in enumerate(top_categories.iterrows()):
            if i < len(cols):
                with cols[i]:
                    st.metric(
                        f"#{i+1} {cat['категория'][:15]}...",
                        f"{cat['процент_от_общих_продаж']:.1f}%"
                    )
                    st.caption(f"Товаров: {cat['количество_товаров']}")
        
        # Простая таблица
        with st.expander("📋 Полная таблица категорий", expanded=False):
            display_df = category_df[['категория', 'количество_товаров', 'процент_от_общих_продаж', 'средний_ads_категории']]
            display_df.columns = ['Категория', 'Товаров', '% продаж', 'Средний ADS']
            st.dataframe(display_df, use_container_width=True)
    
    def show_detailed_items_table(self, analysis: Dict):
        """Показ детальной таблицы товаров"""
        st.subheader("📋 Детальная таблица товаров")
        
        df = analysis['dataframe']
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            abc_filter = st.selectbox(
                "ABC класс:",
                options=['Все'] + list(df['abc_класс'].unique()),
                key="abc_filter"
            )
        
        with col2:
            turnover_filter = st.selectbox(
                "Оборачиваемость:",
                options=['Все'] + list(df['статус_оборачиваемости'].unique()),
                key="turnover_filter"
            )
        
        with col3:
            category_filter = st.selectbox(
                "Категория:",
                options=['Все'] + list(df['категория'].unique()),
                key="detailed_category_filter"
            )
        
        # Применяем фильтры
        filtered_df = df.copy()
        
        if abc_filter != 'Все':
            filtered_df = filtered_df[filtered_df['abc_класс'] == abc_filter]
        
        if turnover_filter != 'Все':
            filtered_df = filtered_df[filtered_df['статус_оборачиваемости'] == turnover_filter]
        
        if category_filter != 'Все':
            filtered_df = filtered_df[filtered_df['категория'] == category_filter]
        
        # Сортировка
        sort_by = st.selectbox(
            "Сортировать по:",
            options=['общие_продажи', 'рейтинг_товара', 'оборачиваемость', 'кумулятивный_процент'],
            index=0,
            key="sort_filter"
        )
        
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)
        
        # Показываем таблицу
        st.write(f"**Показано {len(filtered_df)} из {len(df)} товаров**")
        
        # Объяснение кумулятивного процента
        st.info("""
        💡 **Что такое кумулятивный процент?**
        
        Это **накопленная доля продаж** от начала списка. Например:
        • 1-й товар: 5% продаж → кумулятивный процент = 5%
        • 2-й товар: 3% продаж → кумулятивный процент = 8% (5% + 3%)
        • 3-й товар: 2% продаж → кумулятивный процент = 10% (8% + 2%)
        
        Используется для определения ABC классов:
        • **A класс**: товары до 80% кумулятивных продаж
        • **B класс**: товары с 80% до 95% кумулятивных продаж
        • **C класс**: товары с 95% до 100% кумулятивных продаж
        """)
        
        # Выбираем колонки для отображения
        display_columns = [
            'товар', 'abc_класс', 'рейтинг_товара', 'общие_продажи', 
            'оборачиваемость', 'статус_оборачиваемости', 'категория', 
            'подкатегория', 'процент_от_общих', 'кумулятивный_процент'
        ]
        
        # Переименовываем колонки для понятности
        display_df = filtered_df[display_columns].head(100).copy()
        display_df.columns = [
            'Товар', 'ABC', 'Рейтинг', 'Продажи', 
            'ADS', 'Оборачиваемость', 'Категория', 
            'Подкатегория', 'Доля %', 'Накопленная доля %'
        ]
        
        st.dataframe(display_df, use_container_width=True)
        
        if len(filtered_df) > 100:
            st.info(f"ℹ️ Показаны первые 100 товаров из {len(filtered_df)}")
        
        # Практичный отчет по топ товарам
        st.subheader("🎯 Практические рекомендации")
        
        # Рекомендации по ABC классам
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🥇 Класс A - Приоритеты")
            a_items = filtered_df[filtered_df['abc_класс'] == 'A']
            if len(a_items) > 0:
                st.write("**Приоритетные товары:**")
                for i, (_, item) in enumerate(a_items.head(3).iterrows(), 1):
                    st.write(f"• {item['товар'][:30]}...")
                    st.caption(f"ADS: {item['оборачиваемость']:.3f}")
                st.info("💡 **Рекомендация:** Максимальный контроль запасов - эти товары приносят основную прибыль")
                
                # Полный список товаров A категории
                with st.expander(f"📋 Полный список товаров класса A ({len(a_items)} позиций)", expanded=False):
                    st.write("**🏆 ВСЕ товары высокого приоритета:**")
                    for i, (_, item) in enumerate(a_items.iterrows(), 1):
                        # Определяем цвет по рейтингу
                        if item['рейтинг_товара'] >= 80:
                            color = "🔥"  # Топ товары
                        elif item['рейтинг_товара'] >= 50:
                            color = "⭐"  # Хорошие товары
                        else:
                            color = "📈"  # Растущие товары
                        
                        st.write(f"""
                        **{i}. {color} {item['товар']}**
                        - ADS: {item['оборачиваемость']:.3f} | Продажи: {item['общие_продажи']:,.0f} | Рейтинг: {item['рейтинг_товара']:.1f}
                        - Категория: {item['категория']} → {item['подкатегория']}
                        - Важность: {item['importance_index']:.1f} | Доля: {item['процент_от_общих']:.2f}%
                        """)
                    
                    # Итоговая статистика
                    st.info(f"""
                    **📊 Статистика класса A:**
                    - Общий объем продаж: {a_items['общие_продажи'].sum():,.0f}
                    - Средний ADS: {a_items['ads'].mean():.3f}
                    - Максимальный ADS: {a_items['ads'].max():.3f}
                    - Средний рейтинг: {a_items['рейтинг_товара'].mean():.1f}
                    - Категорий представлено: {a_items['категория'].nunique()}
                    """)
                    
                    # Кнопка экспорта товаров класса A
                    if st.button(f"📤 Экспорт товаров класса A ({len(a_items)} позиций)", key=f"export_a_main"):
                        # Подготавливаем данные для экспорта
                        export_data = a_items[['товар', 'ads', 'общие_продажи', 'рейтинг_товара', 
                                             'категория', 'подкатегория', 'importance_index', 'процент_от_общих']].copy()
                        export_data.columns = ['Товар', 'ADS', 'Общие продажи', 'Рейтинг', 
                                             'Категория', 'Подкатегория', 'Индекс важности', 'Доля %']
                        export_data = export_data.round(3)
                        
                        # Конвертируем в CSV
                        csv = export_data.to_csv(index=False, encoding='utf-8-sig')
                        
                        import datetime
                        
                        st.download_button(
                            label=f"💾 Скачать список A-товаров",
                            data=csv,
                            file_name=f"A_товары_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
        with col2:
            st.markdown("### 🥈 Класс B - Баланс")
            b_items = filtered_df[filtered_df['abc_класс'] == 'B']
            if len(b_items) > 0:
                st.write("**Стабильные товары:**")
                for i, (_, item) in enumerate(b_items.head(3).iterrows(), 1):
                    st.write(f"• {item['товар'][:30]}...")
                    st.caption(f"ADS: {item['оборачиваемость']:.3f}")
                st.info("💡 **Рекомендация:** Стабильные поставки - товары с предсказуемым спросом")
            
        with col3:
            st.markdown("### 🥉 Класс C - Оптимизация")
            c_items = filtered_df[filtered_df['abc_класс'] == 'C']
            if len(c_items) > 0:
                st.write("**Медленные товары:**")
                for i, (_, item) in enumerate(c_items.head(3).iterrows(), 1):
                    st.write(f"• {item['товар'][:30]}...")
                    st.caption(f"ADS: {item['оборачиваемость']:.3f}")
                st.warning("💡 **Рекомендация:** Минимальные остатки - товары медленно оборачиваются, замораживают капитал")
        
        # Быстрый поиск товара
        with st.expander("🔍 Быстрый поиск товара", expanded=False):
            search_term = st.text_input("Введите часть названия товара:")
            if search_term:
                found_items = filtered_df[filtered_df['товар'].str.contains(search_term, case=False, na=False)]
                if len(found_items) > 0:
                    st.write(f"**Найдено {len(found_items)} товаров:**")
                    for i, (_, item) in enumerate(found_items.head(10).iterrows(), 1):
                        # Определяем цвет рамки по ABC классу
                        if item['abc_класс'] == 'A':
                            st.success(f"""
                            **{i}. {item['товар']}**
                            
                            🥇 ABC: **{item['abc_класс']}** | 📈 ADS: **{item['оборачиваемость']:.3f}** | 💰 Продажи: **{item['общие_продажи']:,.0f}**
                            
                            📂 {item['категория']} → {item['подкатегория']}
                            """)
                        elif item['abc_класс'] == 'B':
                            st.info(f"""
                            **{i}. {item['товар']}**
                            
                            🥈 ABC: **{item['abc_класс']}** | 📈 ADS: **{item['оборачиваемость']:.3f}** | 💰 Продажи: **{item['общие_продажи']:,.0f}**
                            
                            📂 {item['категория']} → {item['подкатегория']}
                            """)
                        else:
                            st.warning(f"""
                            **{i}. {item['товар']}**
                            
                            🥉 ABC: **{item['abc_класс']}** | 📈 ADS: **{item['оборачиваемость']:.3f}** | 💰 Продажи: **{item['общие_продажи']:,.0f}**
                            
                            📂 {item['категория']} → {item['подкатегория']}
                            """)
                    
                    if len(found_items) > 10:
                        st.caption(f"Показаны первые 10 из {len(found_items)} найденных товаров")
                else:
                    st.write("❌ Товары не найдены")

# Функция для интеграции в основное приложение
def integrate_branch_analytics():
    """Интеграция аналитики филиалов в основное приложение"""
    analytics = BranchAnalytics()
    analytics.create_branch_analytics_page()

if __name__ == "__main__":
    # Тестовый запуск
    st.set_page_config(page_title="Аналитика филиалов", layout="wide")
    integrate_branch_analytics()