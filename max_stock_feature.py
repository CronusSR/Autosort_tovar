#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УПРОЩЕННЫЙ МОДУЛЬ MAX ОСТАТКОВ
Только настройка параметров и расчет максимальных значений
БЕЗ сравнений с текущими остатками
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import io

# ===== КОНФИГУРАЦИЯ ЛИМИТОВ =====

class StockLimitsConfig:
    """Конфигурация лимитов запасов для разных типов точек"""
    
    DEFAULT_LIMITS = {
        'хаб': {
            'min_days': 15,
            'max_days': 45,
            'description': 'Центральный склад с высокой оборачиваемостью'
        },
        'склад': {
            'min_days': 20,
            'max_days': 60,
            'description': 'Региональный склад'
        },
        'магазин': {
            'min_days': 10,
            'max_days': 30,
            'description': 'Розничная точка продаж'
        },
        'супермаркет': {
            'min_days': 12,
            'max_days': 35,
            'description': 'Крупная розничная точка'
        },
        'мини-маркет': {
            'min_days': 8,
            'max_days': 25,
            'description': 'Малый розничный формат'
        }
    }

# ===== ОСНОВНОЙ ФУНКЦИОНАЛ =====

def add_max_stock_functionality_to_system(system):
    """Добавление функционала максимальных остатков к существующей системе"""
    
    # Добавляем конфигурацию лимитов
    if not hasattr(system, 'stock_limits_config'):
        system.stock_limits_config = StockLimitsConfig.DEFAULT_LIMITS.copy()
    
    # Добавляем методы
    import types
    
    def calculate_max_stock_simple(self, custom_limits: Dict = None) -> Dict:
        """
        Простой расчет максимальных остатков
        
        Args:
            custom_limits: Пользовательские лимиты для типов точек
            
        Returns:
            Dict с результатами расчета MAX остатков
        """
        if self.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан'}
        
        try:
            print("📈 Расчет максимальных остатков...")
            
            # Используем пользовательские лимиты или значения по умолчанию
            limits = custom_limits or self.stock_limits_config
            
            df = self.calculated_ads.copy()
            
            # Рассчитываем MAX для каждого типа точки
            for location_type, config in limits.items():
                min_days = config['min_days']
                max_days = config['max_days']
                
                # Колонки для этого типа точки
                df[f'{location_type}_min_days'] = min_days
                df[f'{location_type}_max_days'] = max_days
                df[f'{location_type}_min_stock'] = df['ads'] * min_days
                df[f'{location_type}_max_stock'] = df['ads'] * max_days
                df[f'{location_type}_range'] = df[f'{location_type}_max_stock'] - df[f'{location_type}_min_stock']
            
            # Общие средние значения
            avg_min_days = np.mean([limits[t]['min_days'] for t in limits])
            avg_max_days = np.mean([limits[t]['max_days'] for t in limits])
            
            df['avg_min_days'] = avg_min_days
            df['avg_max_days'] = avg_max_days
            df['avg_min_stock'] = df['ads'] * avg_min_days
            df['avg_max_stock'] = df['ads'] * avg_max_days
            df['avg_range'] = df['avg_max_stock'] - df['avg_min_stock']
            
            # Целевая зона (между 60% MIN и 80% MAX)
            df['target_zone_lower'] = df['avg_min_stock'] * 1.2
            df['target_zone_upper'] = df['avg_max_stock'] * 0.8
            
            self.calculated_max_stock = df
            
            # Статистика
            total_items = len(df)
            avg_max_stock = df['avg_max_stock'].mean()
            total_max_stock = df['avg_max_stock'].sum()
            
            print(f"✅ MAX остатки рассчитаны для {total_items} товаров")
            print(f"📊 Средний MAX запас: {avg_max_stock:.1f}")
            print(f"📊 Общий MAX запас: {total_max_stock:.0f}")
            
            return {
                'success': True,
                'total_items': total_items,
                'total_max_stock': total_max_stock,
                'avg_max_stock': avg_max_stock,
                'limits_used': limits,
                'location_types_count': len(limits)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка расчета MAX остатков: {str(e)}"}
    
    def update_stock_limits(self, location_type: str, min_days: int, max_days: int):
        """Обновление лимитов для типа точки"""
        if location_type not in self.stock_limits_config:
            self.stock_limits_config[location_type] = {}
        
        self.stock_limits_config[location_type]['min_days'] = min_days
        self.stock_limits_config[location_type]['max_days'] = max_days
        
        print(f"✅ Обновлены лимиты для '{location_type}': MIN={min_days} дней, MAX={max_days} дней")
    
    def get_max_stock_summary(self) -> Dict:
        """Получение сводки по максимальным остаткам"""
        if not hasattr(self, 'calculated_max_stock') or self.calculated_max_stock is None:
            return {'error': 'MAX остатки не рассчитаны'}
        
        df = self.calculated_max_stock
        limits = self.stock_limits_config
        
        summary = {
            'total_items': len(df),
            'location_types': list(limits.keys()),
            'avg_parameters': {
                'min_days': df['avg_min_days'].iloc[0],
                'max_days': df['avg_max_days'].iloc[0]
            },
            'totals': {
                'avg_min_stock': df['avg_min_stock'].sum(),
                'avg_max_stock': df['avg_max_stock'].sum(),
                'range_capacity': df['avg_range'].sum()
            },
            'per_location': {}
        }
        
        # Статистика по типам точек
        for location_type in limits.keys():
            if f'{location_type}_max_stock' in df.columns:
                summary['per_location'][location_type] = {
                    'min_days': limits[location_type]['min_days'],
                    'max_days': limits[location_type]['max_days'],
                    'total_min_stock': df[f'{location_type}_min_stock'].sum(),
                    'total_max_stock': df[f'{location_type}_max_stock'].sum(),
                    'avg_min_stock': df[f'{location_type}_min_stock'].mean(),
                    'avg_max_stock': df[f'{location_type}_max_stock'].mean()
                }
        
        return summary
    
    # Привязываем методы к системе
    system.calculate_max_stock_simple = types.MethodType(calculate_max_stock_simple, system)
    system.update_stock_limits = types.MethodType(update_stock_limits, system)
    system.get_max_stock_summary = types.MethodType(get_max_stock_summary, system)
    
    print("✅ Упрощенный функционал MAX остатков добавлен к системе!")
    return True

# ===== STREAMLIT ИНТЕРФЕЙСЫ =====

def max_stock_settings_page(system):
    """Страница настройки максимальных остатков"""
    st.header("📈 Настройка максимальных остатков")
    
    st.markdown("""
    **Максимальные остатки** - это верхние лимиты для планирования закупок:
    - **MIN дни** - минимальное количество дней запаса
    - **MAX дни** - максимальное количество дней запаса  
    - **Диапазон** - разница между MIN и MAX для гибкого планирования
    
    💡 MAX остатки помогают избежать переизбытка и замораживания средств.
    """)
    
    # Проверяем что ADS рассчитан
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("⚠️ Сначала необходимо рассчитать ADS")
        return
    
    # Инициализируем функционал если нужно
    if not hasattr(system, 'calculate_max_stock_simple'):
        add_max_stock_functionality_to_system(system)
    
    # Настройка лимитов для каждого типа точек
    st.subheader("⚙️ Настройка лимитов по типам точек")
    
    # Создаем форму для настройки
    with st.form("max_stock_limits_form"):
        st.write("**Настройте количество дней запаса для каждого типа точки:**")
        
        updated_limits = {}
        
        # Отображаем настройки для каждого типа
        for location_type, config in StockLimitsConfig.DEFAULT_LIMITS.items():
            st.write(f"**{location_type.upper()}** - {config['description']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_days = st.slider(
                    f"MIN дни для {location_type}",
                    min_value=5,
                    max_value=60,
                    value=config['min_days'],
                    step=1,
                    key=f"min_{location_type}"
                )
            
            with col2:
                max_days = st.slider(
                    f"MAX дни для {location_type}",
                    min_value=min_days + 5,  # Минимум на 5 дней больше MIN
                    max_value=120,
                    value=config['max_days'],
                    step=1,
                    key=f"max_{location_type}"
                )
            
            updated_limits[location_type] = {
                'min_days': min_days,
                'max_days': max_days,
                'description': config['description']
            }
            
            # Показываем пример расчета
            example_ads = system.calculated_ads['ads'].median()
            example_min = example_ads * min_days
            example_max = example_ads * max_days
            
            st.info(f"""
            **Пример для {location_type}** (медианный ADS = {example_ads:.2f}):
            - MIN запас: {example_min:.0f} единиц ({min_days} дней)
            - MAX запас: {example_max:.0f} единиц ({max_days} дней)
            - Рабочий диапазон: {example_max - example_min:.0f} единиц
            """)
            
            st.markdown("---")
        
        # Кнопка применения настроек
        if st.form_submit_button("💾 Применить настройки и рассчитать MAX", use_container_width=True):
            # Обновляем конфигурацию системы
            system.stock_limits_config = updated_limits
            
            # Рассчитываем MAX остатки
            calc_result = system.calculate_max_stock_simple(updated_limits)
            
            if calc_result['success']:
                st.success("✅ Максимальные остатки рассчитаны!")
                
                # Показываем результаты
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Товаров", calc_result['total_items'])
                with col2:
                    st.metric("Общий MAX запас", f"{calc_result['total_max_stock']:,.0f}")
                with col3:
                    st.metric("Средний MAX", f"{calc_result['avg_max_stock']:.1f}")
                with col4:
                    st.metric("Типов точек", calc_result['location_types_count'])
                
                st.rerun()
            else:
                st.error(f"❌ {calc_result['error']}")

def max_stock_analysis_page(system):
    """Страница анализа максимальных остатков"""
    st.header("📊 Анализ максимальных остатков")
    
    # Проверяем что MAX остатки рассчитаны
    if not hasattr(system, 'calculated_max_stock') or system.calculated_max_stock is None:
        st.warning("⚠️ Сначала настройте и рассчитайте максимальные остатки")
        if st.button("⚙️ Перейти к настройкам"):
            st.info("Переключитесь на вкладку 'MAX остатки - настройки'")
        return
    
    # Получаем сводку
    summary = system.get_max_stock_summary()
    
    if 'error' in summary:
        st.error(f"❌ {summary['error']}")
        return
    
    # Общая статистика
    st.subheader("📈 Общая статистика MAX остатков")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Товаров", summary['total_items'])
    
    with col2:
        avg_min = summary['totals']['avg_min_stock']
        st.metric("Общий MIN запас", f"{avg_min:,.0f}")
    
    with col3:
        avg_max = summary['totals']['avg_max_stock']
        st.metric("Общий MAX запас", f"{avg_max:,.0f}")
    
    with col4:
        range_capacity = summary['totals']['range_capacity']
        st.metric("Рабочий диапазон", f"{range_capacity:,.0f}")
    
    # Параметры
    st.info(f"""
    **Средние параметры:**
    - MIN дни: {summary['avg_parameters']['min_days']:.1f}
    - MAX дни: {summary['avg_parameters']['max_days']:.1f}
    - Типов точек настроено: {len(summary['location_types'])}
    """)
    
    # Анализ по типам точек
    st.subheader("🏪 Анализ по типам точек")
    
    if summary['per_location']:
        # Таблица сравнения типов точек
        location_data = []
        
        for location_type, data in summary['per_location'].items():
            location_data.append({
                'Тип точки': location_type.capitalize(),
                'MIN дни': data['min_days'],
                'MAX дни': data['max_days'],
                'Общий MIN запас': data['total_min_stock'],
                'Общий MAX запас': data['total_max_stock'],
                'Средний MIN': f"{data['avg_min_stock']:.1f}",
                'Средний MAX': f"{data['avg_max_stock']:.1f}"
            })
        
        location_df = pd.DataFrame(location_data)
        st.dataframe(location_df, use_container_width=True)
        
        # График сравнения типов точек
        fig_comparison = px.bar(
            location_df,
            x='Тип точки',
            y=['MIN дни', 'MAX дни'],
            title='Сравнение параметров по типам точек',
            barmode='group',
            color_discrete_map={'MIN дни': '#ff6b6b', 'MAX дни': '#4ecdc4'}
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Детальная таблица товаров
    st.subheader("📋 Детальная таблица MAX остатков")
    
    max_data = system.calculated_max_stock
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        location_type_filter = st.selectbox(
            "Показать данные для типа точки:",
            options=['Средние значения'] + list(summary['location_types'])
        )
    
    with col2:
        min_ads_filter = st.number_input(
            "Минимальный ADS:",
            min_value=0.0,
            value=0.0,
            step=0.1,
            help="Показать товары с ADS больше указанного"
        )
    
    # Применяем фильтры
    filtered_data = max_data.copy()
    
    if min_ads_filter > 0:
        filtered_data = filtered_data[filtered_data['ads'] >= min_ads_filter]
    
    # Выбираем колонки для отображения
    if location_type_filter == 'Средние значения':
        display_columns = [
            'номенклатура', 'ads', 'avg_min_days', 'avg_max_days',
            'avg_min_stock', 'avg_max_stock', 'avg_range'
        ]
        column_config = {
            'номенклатура': 'Товар',
            'ads': 'ADS',
            'avg_min_days': 'MIN дни',
            'avg_max_days': 'MAX дни',
            'avg_min_stock': 'MIN запас',
            'avg_max_stock': 'MAX запас',
            'avg_range': 'Диапазон'
        }
    else:
        # Колонки для конкретного типа точки
        type_prefix = location_type_filter.lower()
        display_columns = [
            'номенклатура', 'ads', 
            f'{type_prefix}_min_days', f'{type_prefix}_max_days',
            f'{type_prefix}_min_stock', f'{type_prefix}_max_stock', f'{type_prefix}_range'
        ]
        column_config = {
            'номенклатура': 'Товар',
            'ads': 'ADS',
            f'{type_prefix}_min_days': 'MIN дни',
            f'{type_prefix}_max_days': 'MAX дни',
            f'{type_prefix}_min_stock': 'MIN запас',
            f'{type_prefix}_max_stock': 'MAX запас',
            f'{type_prefix}_range': 'Диапазон'
        }
    
    # Проверяем что все колонки существуют
    available_columns = [col for col in display_columns if col in filtered_data.columns]
    
    if available_columns:
        st.dataframe(
            filtered_data[available_columns].head(100),  # Показываем первые 100
            use_container_width=True,
            column_config=column_config
        )
        
        if len(filtered_data) > 100:
            st.info(f"Показано 100 из {len(filtered_data)} товаров")
    else:
        st.warning(f"Данные для типа '{location_type_filter}' не найдены")
    
    # Топ товары по MAX запасу
    st.subheader("🔝 Топ-20 товаров по MAX запасу")
    
    if location_type_filter == 'Средние значения':
        top_max = filtered_data.nlargest(20, 'avg_max_stock')
        
        fig_top = px.bar(
            top_max,
            x='avg_max_stock',
            y='номенклатура',
            orientation='h',
            title='Топ-20 товаров по среднему MAX запасу',
            labels={'avg_max_stock': 'MAX запас', 'номенклатура': 'Товар'},
            color='avg_max_stock',
            color_continuous_scale='Blues'
        )
    else:
        type_prefix = location_type_filter.lower()
        max_col = f'{type_prefix}_max_stock'
        
        if max_col in filtered_data.columns:
            top_max = filtered_data.nlargest(20, max_col)
            
            fig_top = px.bar(
                top_max,
                x=max_col,
                y='номенклатура',
                orientation='h',
                title=f'Топ-20 товаров по MAX запасу для {location_type_filter}',
                labels={max_col: 'MAX запас', 'номенклатура': 'Товар'},
                color=max_col,
                color_continuous_scale='Blues'
            )
        else:
            fig_top = None
    
    if fig_top:
        fig_top.update_layout(height=600)
        st.plotly_chart(fig_top, use_container_width=True)

# ===== СОЗДАНИЕ ВИЗУАЛИЗАЦИЙ =====

def create_max_stock_charts(system):
    """Создание графиков для MAX остатков"""
    
    if not hasattr(system, 'calculated_max_stock'):
        return {}
    
    charts = {}
    df = system.calculated_max_stock.head(50)  # Топ-50 для читаемости
    
    # 1. Сравнение MIN vs MAX
    fig_comparison = go.Figure()
    
    # MIN полосы
    fig_comparison.add_trace(go.Bar(
        x=df['номенклатура'],
        y=df['avg_min_stock'],
        name='MIN запас',
        marker_color='lightcoral'
    ))
    
    # MAX полосы
    fig_comparison.add_trace(go.Bar(
        x=df['номенклатура'],
        y=df['avg_max_stock'],
        name='MAX запас',
        marker_color='lightblue',
        opacity=0.7
    ))
    
    fig_comparison.update_layout(
        title='Сравнение MIN и MAX запасов',
        xaxis_title='Товары',
        yaxis_title='Количество',
        xaxis={'tickangle': 45},
        height=500
    )
    charts['min_vs_max'] = fig_comparison
    
    # 2. Диапазон запасов
    fig_range = px.bar(
        df.head(20),
        x='номенклатура',
        y='avg_range',
        title='Рабочий диапазон запасов (MAX - MIN)',
        labels={'avg_range': 'Диапазон', 'номенклатура': 'Товар'},
        color='avg_range',
        color_continuous_scale='Greens'
    )
    fig_range.update_layout(xaxis={'tickangle': 45}, height=500)
    charts['range_analysis'] = fig_range
    
    return charts

# ===== ЭКСПОРТ =====

def export_max_stock_to_excel(system) -> io.BytesIO:
    """Экспорт MAX остатков в Excel"""
    
    if not hasattr(system, 'calculated_max_stock'):
        return None
    
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Основные данные
            system.calculated_max_stock.to_excel(writer, sheet_name='MAX_остатки_детально', index=False)
            
            # Сводка
            summary = system.get_max_stock_summary()
            if 'error' not in summary:
                summary_df = pd.DataFrame([{
                    'Параметр': 'Товаров всего',
                    'Значение': summary['total_items']
                }, {
                    'Параметр': 'Общий MIN запас',
                    'Значение': summary['totals']['avg_min_stock']
                }, {
                    'Параметр': 'Общий MAX запас',
                    'Значение': summary['totals']['avg_max_stock']
                }, {
                    'Параметр': 'Средние MIN дни',
                    'Значение': summary['avg_parameters']['min_days']
                }, {
                    'Параметр': 'Средние MAX дни',
                    'Значение': summary['avg_parameters']['max_days']
                }])
                summary_df.to_excel(writer, sheet_name='Сводка_MAX', index=False)
                
                # По типам точек
                if summary['per_location']:
                    location_data = []
                    for loc_type, data in summary['per_location'].items():
                        location_data.append({
                            'Тип_точки': loc_type,
                            'MIN_дни': data['min_days'],
                            'MAX_дни': data['max_days'],
                            'Общий_MIN': data['total_min_stock'],
                            'Общий_MAX': data['total_max_stock']
                        })
                    
                    location_df = pd.DataFrame(location_data)
                    location_df.to_excel(writer, sheet_name='По_типам_точек', index=False)
        
        output.seek(0)
        return output
        
    except Exception as e:
        print(f"Ошибка экспорта MAX остатков: {str(e)}")
        return None

# ===== ПРИМЕР ИСПОЛЬЗОВАНИЯ =====

if __name__ == "__main__":
    print("📈 Упрощенный модуль MAX остатков готов!")
    print("\n🎯 ФУНКЦИОНАЛЬНОСТЬ:")
    print("✅ Настройка MIN/MAX дней для разных типов точек")
    print("✅ Расчет максимальных остатков на основе ADS")
    print("✅ Анализ и визуализация лимитов")
    print("✅ Экспорт в Excel")
    print("❌ НЕТ сравнений с текущими остатками")
    print("❌ НЕТ анализа эффективности")
    print("\n💡 Только планирование верхних границ запасов!")