#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДОБАВЛЕНИЕ ФУНКЦИОНАЛА МАКСИМАЛЬНЫХ ОСТАТКОВ
Расширение системы для расчета MAX остатков с учетом типов точек продаж
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional
import io

# ===== НОВЫЕ ПАРАМЕТРЫ СИСТЕМЫ =====

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
    
    @classmethod
    def get_location_type(cls, location_name: str) -> str:
        """Определение типа точки по названию"""
        location_lower = location_name.lower()
        
        if any(word in location_lower for word in ['хаб', 'hub', 'центр']):
            return 'хаб'
        elif any(word in location_lower for word in ['склад', 'warehouse', 'скл']):
            return 'склад'
        elif any(word in location_lower for word in ['супер', 'super', 'гипер']):
            return 'супермаркет'
        elif any(word in location_lower for word in ['мини', 'mini', 'экспресс']):
            return 'мини-маркет'
        elif any(word in location_lower for word in ['магазин', 'shop', 'маг']):
            return 'магазин'
        else:
            return 'магазин'  # По умолчанию

# ===== РАСШИРЕНИЕ КЛАССА СИСТЕМЫ =====

def add_max_stock_functionality_to_system(system):
    """Добавление функционала максимальных остатков к существующей системе"""
    
    # Добавляем конфигурацию лимитов
    if not hasattr(system, 'stock_limits_config'):
        system.stock_limits_config = StockLimitsConfig.DEFAULT_LIMITS.copy()
    
    # Добавляем методы
    import types
    
    def calculate_max_stock_with_types(self, custom_limits: Dict = None) -> Dict:
        """
        Расчет максимальных остатков с учетом типов точек
        
        Args:
            custom_limits: Пользовательские лимиты для типов точек
            
        Returns:
            Dict с результатами расчета MAX остатков
        """
        if self.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан'}
        
        try:
            print("📈 Расчет максимальных остатков с типами точек...")
            
            # Используем пользовательские лимиты или значения по умолчанию
            limits = custom_limits or self.stock_limits_config
            
            df = self.calculated_ads.copy()
            
            # Если есть информация о локациях из stock_data
            if hasattr(self, 'stock_data') and self.stock_data is not None:
                # Определяем типы точек из колонок остатков
                stock_columns = [col for col in self.stock_data.columns 
                               if col != 'номенклатура' and col != 'total_current_stock']
                
                # Добавляем расчеты для каждого типа точки
                for location_col in stock_columns:
                    location_type = StockLimitsConfig.get_location_type(location_col)
                    
                    if location_type in limits:
                        min_days = limits[location_type]['min_days']
                        max_days = limits[location_type]['max_days']
                        
                        # Рассчитываем MIN и MAX для этой точки
                        df[f'{location_col}_type'] = location_type
                        df[f'{location_col}_min_stock'] = df['ads'] * min_days
                        df[f'{location_col}_max_stock'] = df['ads'] * max_days
                        df[f'{location_col}_optimal_range'] = df[f'{location_col}_max_stock'] - df[f'{location_col}_min_stock']
            
            # Общие расчеты (если не определены конкретные локации)
            if 'general_min_days' not in df.columns:
                # Используем средние значения по всем типам точек
                avg_min_days = np.mean([limits[t]['min_days'] for t in limits])
                avg_max_days = np.mean([limits[t]['max_days'] for t in limits])
                
                df['general_min_days'] = avg_min_days
                df['general_max_days'] = avg_max_days
                df['general_min_stock'] = df['ads'] * avg_min_days
                df['general_max_stock'] = df['ads'] * avg_max_days
                df['general_optimal_range'] = df['general_max_stock'] - df['general_min_stock']
            
            # Рассчитываем целевые зоны
            df['target_zone_lower'] = df['general_min_stock'] * 1.2  # 20% выше минимума
            df['target_zone_upper'] = df['general_max_stock'] * 0.8  # 80% от максимума
            
            # Статус по максимальным остаткам
            if hasattr(self, 'stock_comparison') and self.stock_comparison is not None:
                # Объединяем с текущими остатками
                comparison = self.stock_comparison.copy()
                comparison = pd.merge(comparison, df[['номенклатура', 'general_max_stock', 'target_zone_upper']], 
                                    on='номенклатура', how='left')
                
                # Определяем статус относительно максимума
                def determine_max_status(row):
                    current = row['total_current_stock']
                    max_stock = row.get('general_max_stock', 0)
                    target_upper = row.get('target_zone_upper', 0)
                    
                    if current > max_stock:
                        return 'ПЕРЕИЗБЫТОК'
                    elif current > target_upper:
                        return 'ВЫСОКИЙ'
                    elif current >= row.get('min_stock_total', 0):
                        return 'ОПТИМАЛЬНЫЙ'
                    else:
                        return 'НЕДОСТАТОК'
                
                comparison['max_stock_status'] = comparison.apply(determine_max_status, axis=1)
                comparison['excess_stock'] = np.maximum(0, 
                    comparison['total_current_stock'] - comparison['general_max_stock'].fillna(0))
                
                self.stock_comparison_with_max = comparison
            
            self.calculated_max_stock = df
            
            # Статистика
            total_items = len(df)
            avg_max_stock = df['general_max_stock'].mean()
            total_max_stock = df['general_max_stock'].sum()
            
            print(f"✅ MAX остатки рассчитаны для {total_items} товаров")
            print(f"📊 Средний MAX запас: {avg_max_stock:.1f}")
            print(f"📊 Общий MAX запас: {total_max_stock:.0f}")
            
            return {
                'success': True,
                'total_items': total_items,
                'total_max_stock': total_max_stock,
                'avg_max_stock': avg_max_stock,
                'limits_used': limits,
                'location_types_detected': len([col for col in df.columns if col.endswith('_type')])
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
    
    def get_stock_efficiency_analysis(self) -> Dict:
        """Анализ эффективности запасов"""
        if not hasattr(self, 'stock_comparison_with_max') or self.stock_comparison_with_max is None:
            return {'error': 'Сравнение с MAX остатками не выполнено'}
        
        comparison = self.stock_comparison_with_max
        
        # Статистика по статусам
        status_counts = comparison['max_stock_status'].value_counts()
        total_items = len(comparison)
        
        # Переизбыток товаров
        excess_items = comparison[comparison['max_stock_status'] == 'ПЕРЕИЗБЫТОК']
        total_excess_value = excess_items['excess_stock'].sum()
        
        # Оптимальные остатки
        optimal_items = comparison[comparison['max_stock_status'] == 'ОПТИМАЛЬНЫЙ']
        
        # Недостаток
        deficit_items = comparison[comparison['max_stock_status'] == 'НЕДОСТАТОК']
        
        return {
            'total_items': total_items,
            'status_distribution': {
                'переизбыток': status_counts.get('ПЕРЕИЗБЫТОК', 0),
                'высокий': status_counts.get('ВЫСОКИЙ', 0),
                'оптимальный': status_counts.get('ОПТИМАЛЬНЫЙ', 0),
                'недостаток': status_counts.get('НЕДОСТАТОК', 0)
            },
            'efficiency_metrics': {
                'optimal_percentage': (len(optimal_items) / total_items) * 100,
                'excess_percentage': (len(excess_items) / total_items) * 100,
                'deficit_percentage': (len(deficit_items) / total_items) * 100
            },
            'financial_impact': {
                'total_excess_units': total_excess_value,
                'excess_items_count': len(excess_items),
                'avg_excess_per_item': excess_items['excess_stock'].mean() if len(excess_items) > 0 else 0
            },
            'top_excess_items': excess_items.nlargest(10, 'excess_stock')[
                ['номенклатура', 'total_current_stock', 'general_max_stock', 'excess_stock']
            ].to_dict('records') if len(excess_items) > 0 else []
        }
    
    # Привязываем методы к системе
    system.calculate_max_stock_with_types = types.MethodType(calculate_max_stock_with_types, system)
    system.update_stock_limits = types.MethodType(update_stock_limits, system)
    system.get_stock_efficiency_analysis = types.MethodType(get_stock_efficiency_analysis, system)
    
    print("✅ Функционал максимальных остатков добавлен к системе!")
    return True

# ===== STREAMLIT ИНТЕРФЕЙС =====

def max_stock_settings_page(system):
    """Страница настройки максимальных остатков"""
    st.header("📈 Настройка максимальных остатков")
    
    st.markdown("""
    **Максимальные остатки** помогают избежать переизбытка товаров и оптимизировать оборачиваемость:
    - **MIN** - минимальный запас для бесперебойных продаж
    - **MAX** - максимальный запас для избежания замораживания средств
    - **Оптимальная зона** - между MIN и MAX для эффективной работы
    """)
    
    # Проверяем что ADS рассчитан
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("⚠️ Сначала необходимо рассчитать ADS")
        return
    
    # Инициализируем функционал если нужно
    if not hasattr(system, 'calculate_max_stock_with_types'):
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
            if hasattr(system, 'calculated_ads'):
                example_ads = system.calculated_ads['ads'].median()
                example_min = example_ads * min_days
                example_max = example_ads * max_days
                
                st.info(f"""
                **Пример для {location_type}** (ADS = {example_ads:.2f}):
                - MIN запас: {example_min:.0f} единиц ({min_days} дней)
                - MAX запас: {example_max:.0f} единиц ({max_days} дней)
                - Оптимальная зона: {example_max - example_min:.0f} единиц
                """)
            
            st.markdown("---")
        
        # Кнопка применения настроек
        if st.form_submit_button("💾 Применить настройки", use_container_width=True):
            # Обновляем конфигурацию системы
            system.stock_limits_config = updated_limits
            
            # Пересчитываем MAX остатки
            calc_result = system.calculate_max_stock_with_types(updated_limits)
            
            if calc_result['success']:
                st.success("✅ Максимальные остатки пересчитаны с новыми настройками!")
                
                # Показываем результаты
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Товаров", calc_result['total_items'])
                with col2:
                    st.metric("Общий MAX запас", f"{calc_result['total_max_stock']:,.0f}")
                with col3:
                    st.metric("Средний MAX", f"{calc_result['avg_max_stock']:.1f}")
                
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
            st.switch_page("MAX настройки")
        return
    
    # Получаем анализ эффективности
    efficiency = system.get_stock_efficiency_analysis()
    
    if 'error' in efficiency:
        st.error(f"❌ {efficiency['error']}")
        return
    
    # Общая статистика
    st.subheader("📈 Общая эффективность запасов")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        optimal_pct = efficiency['efficiency_metrics']['optimal_percentage']
        st.metric("Оптимальные остатки", f"{optimal_pct:.1f}%", 
                 delta=f"{optimal_pct - 60:.1f}%" if optimal_pct >= 60 else None)
    
    with col2:
        excess_pct = efficiency['efficiency_metrics']['excess_percentage']
        st.metric("Переизбыток", f"{excess_pct:.1f}%",
                 delta=f"-{excess_pct:.1f}%" if excess_pct > 0 else "0%")
    
    with col3:
        deficit_pct = efficiency['efficiency_metrics']['deficit_percentage']
        st.metric("Недостаток", f"{deficit_pct:.1f}%",
                 delta=f"-{deficit_pct:.1f}%" if deficit_pct > 0 else "0%")
    
    with col4:
        excess_units = efficiency['financial_impact']['total_excess_units']
        st.metric("Избыток (единиц)", f"{excess_units:,.0f}")
    
    # Визуализация распределения статусов
    st.subheader("📊 Распределение товаров по статусам остатков")
    
    status_dist = efficiency['status_distribution']
    
    # Круговая диаграмма
    fig_pie = px.pie(
        values=list(status_dist.values()),
        names=list(status_dist.keys()),
        title="Распределение товаров по эффективности запасов",
        color_discrete_map={
            'оптимальный': '#00aa44',
            'высокий': '#ffaa00',
            'недостаток': '#ff4444',
            'переизбыток': '#aa0044'
        }
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Анализ товаров с переизбытком
    if efficiency['financial_impact']['excess_items_count'] > 0:
        st.subheader("⚠️ Товары с переизбытком")
        
        st.warning(f"""
        **Найдено {efficiency['financial_impact']['excess_items_count']} товаров с переизбытком:**
        - Общий избыток: {efficiency['financial_impact']['total_excess_units']:,.0f} единиц
        - Средний избыток на товар: {efficiency['financial_impact']['avg_excess_per_item']:.1f} единиц
        """)
        
        # Топ товары с переизбытком
        top_excess = efficiency['top_excess_items']
        
        if top_excess:
            excess_df = pd.DataFrame(top_excess)
            excess_df = excess_df.rename(columns={
                'номенклатура': 'Товар',
                'total_current_stock': 'Текущий остаток',
                'general_max_stock': 'MAX остаток',
                'excess_stock': 'Переизбыток'
            })
            
            st.dataframe(excess_df, use_container_width=True)
            
            # График топ переизбытков
            fig_excess = px.bar(
                excess_df.head(10),
                x='Переизбыток',
                y='Товар',
                orientation='h',
                title='Топ-10 товаров с наибольшим переизбытком',
                color='Переизбыток',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_excess, use_container_width=True)
    
    # Рекомендации по оптимизации
    st.subheader("💡 Рекомендации по оптимизации")
    
    recommendations = []
    
    if excess_pct > 15:
        recommendations.append(f"🔴 Высокий уровень переизбытка ({excess_pct:.1f}%). Сократите заказы товаров с избытком.")
    
    if optimal_pct < 50:
        recommendations.append(f"🟡 Низкая доля оптимальных остатков ({optimal_pct:.1f}%). Пересмотрите параметры MIN/MAX.")
    
    if deficit_pct > 25:
        recommendations.append(f"🔴 Много товаров с недостатком ({deficit_pct:.1f}%). Увеличьте частоту заказов.")
    
    if excess_pct < 5 and deficit_pct < 10 and optimal_pct > 70:
        recommendations.append("✅ Отличная эффективность запасов! Продолжайте текущую стратегию.")
    
    if not recommendations:
        recommendations.append("📊 Проанализируйте данные для получения рекомендаций.")
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"**{i}.** {rec}")

def create_max_stock_visualization(system):
    """Создание расширенной визуализации с MIN/MAX зонами"""
    
    if not hasattr(system, 'stock_comparison_with_max'):
        return None
    
    comparison = system.stock_comparison_with_max.head(20)  # Топ-20 для читаемости
    
    # Создаем subplot
    fig = go.Figure()
    
    # Добавляем полосы зон
    for i, (_, row) in enumerate(comparison.iterrows()):
        # Зона недостатка (красная)
        fig.add_shape(
            type="rect",
            x0=i-0.4, x1=i+0.4,
            y0=0, y1=row.get('min_stock_total', 0),
            fillcolor="rgba(255, 68, 68, 0.3)",
            line=dict(color="rgba(255, 68, 68, 0.3)")
        )
        
        # Оптимальная зона (зеленая)
        fig.add_shape(
            type="rect",
            x0=i-0.4, x1=i+0.4,
            y0=row.get('min_stock_total', 0), y1=row.get('general_max_stock', 0),
            fillcolor="rgba(0, 170, 68, 0.3)",
            line=dict(color="rgba(0, 170, 68, 0.3)")
        )
        
        # Зона переизбытка (оранжевая)
        max_val = max(row.get('general_max_stock', 0), row.get('total_current_stock', 0)) * 1.2
        fig.add_shape(
            type="rect",
            x0=i-0.4, x1=i+0.4,
            y0=row.get('general_max_stock', 0), y1=max_val,
            fillcolor="rgba(255, 170, 0, 0.3)",
            line=dict(color="rgba(255, 170, 0, 0.3)")
        )
    
    # Текущие остатки (столбцы)
    fig.add_trace(go.Bar(
        x=list(range(len(comparison))),
        y=comparison['total_current_stock'],
        name='Текущий остаток',
        marker_color='lightblue',
        width=0.6
    ))
    
    # MIN линия
    fig.add_trace(go.Scatter(
        x=list(range(len(comparison))),
        y=comparison.get('min_stock_total', [0]*len(comparison)),
        mode='lines+markers',
        name='MIN остаток',
        line=dict(color='red', dash='dash', width=2)
    ))
    
    # MAX линия
    fig.add_trace(go.Scatter(
        x=list(range(len(comparison))),
        y=comparison.get('general_max_stock', [0]*len(comparison)),
        mode='lines+markers',
        name='MAX остаток',
        line=dict(color='orange', dash='dash', width=2)
    ))
    
    # Настройка осей
    fig.update_layout(
        title='Анализ текущих остатков в зонах MIN/MAX',
        xaxis_title='Товары',
        yaxis_title='Количество',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(comparison))),
            ticktext=[name[:20] + '...' if len(name) > 20 else name 
                     for name in comparison['номенклатура']],
            tickangle=45
        ),
        height=600,
        showlegend=True
    )
    
    # Добавляем аннотации зон
    fig.add_annotation(
        x=len(comparison)-1, y=comparison['min_stock_total'].iloc[-1] / 2,
        text="НЕДОСТАТОК", showarrow=False,
        font=dict(color="white", size=12, family="Arial Black"),
        bgcolor="rgba(255, 68, 68, 0.8)", bordercolor="white"
    )
    
    fig.add_annotation(
        x=len(comparison)-1, 
        y=(comparison['min_stock_total'].iloc[-1] + comparison['general_max_stock'].iloc[-1]) / 2,
        text="ОПТИМАЛЬНО", showarrow=False,
        font=dict(color="white", size=12, family="Arial Black"),
        bgcolor="rgba(0, 170, 68, 0.8)", bordercolor="white"
    )
    
    return fig

# ===== ИНТЕГРАЦИЯ В ОСНОВНОЕ ПРИЛОЖЕНИЕ =====

def integrate_max_stock_to_main_app():
    """
    Инструкция по интеграции MAX остатков в основное приложение
    """
    
    integration_code = '''
# ===== ДОБАВИТЬ В streamlit_modular_app.py =====

# 1. Импорт в начале файла:
from max_stock_feature import (
    add_max_stock_functionality_to_system,
    max_stock_settings_page, 
    max_stock_analysis_page,
    create_max_stock_visualization
)

# 2. В функции main(), после инициализации системы:
def main():
    system = init_system()
    
    # ДОБАВИТЬ: Инициализация MAX остатков
    add_max_stock_functionality_to_system(system)
    
    # ... остальной код ...
    
    # 3. В навигации sidebar добавить новые страницы:
    page = st.selectbox(
        "Выберите раздел:",
        [
            "🔤 ABC анализ",
            "📊 ADS расчет", 
            "📋 MIN запасы",
            "📈 MAX остатки - настройки",     # НОВАЯ СТРАНИЦА
            "📊 MAX остатки - анализ",        # НОВАЯ СТРАНИЦА
            "⚖️ Сравнение остатков",
            "🔤📊 ABC подкатегории",
            "📤 Экспорт результатов",
            "⚙️ Настройки"
        ]
    )
    
    # 4. В обработке страниц добавить:
    elif page == "📈 MAX остатки - настройки":
        max_stock_settings_page(system)
    elif page == "📊 MAX остатки - анализ":
        max_stock_analysis_page(system)

# ===== ДОБАВИТЬ В modular_inventory_system.py =====

# В метод get_system_status() добавить:
def get_system_status(self):
    # ... существующий код ...
    
    status = {
        # ... существующие статусы ...
        'max_stock_analysis': {
            'calculated': hasattr(self, 'calculated_max_stock') and self.calculated_max_stock is not None,
            'items_count': len(self.calculated_max_stock) if hasattr(self, 'calculated_max_stock') and self.calculated_max_stock is not None else 0,
            'efficiency_analyzed': hasattr(self, 'stock_comparison_with_max') and self.stock_comparison_with_max is not None
        }
    }
    
    # Обновляем общий прогресс (теперь 6 этапов)
    completed_steps = sum([
        status['abc_analysis']['analyzed'],
        status['sales_analysis']['ads_calculated'],
        status['min_stock_analysis']['calculated'],
        status['max_stock_analysis']['calculated'],  # НОВЫЙ этап
        status['stock_analysis']['compared'],
        status['subcategory_analysis']['analyzed']
    ])
    
    status['overall'] = {
        'completed_steps': completed_steps,
        'total_steps': 6,  # Увеличиваем до 6
        'progress_percentage': (completed_steps / 6) * 100,
        'ready_for_export': completed_steps >= 3
    }

# В метод export_all_results() добавить:
def export_all_results(self):
    # ... в блоке with pd.ExcelWriter(output, engine='openpyxl') as writer: ...
    
    # Максимальные остатки
    if hasattr(self, 'calculated_max_stock') and self.calculated_max_stock is not None:
        self.calculated_max_stock.to_excel(writer, sheet_name='Максимальные_запасы', index=False)
    
    # Анализ эффективности остатков
    if hasattr(self, 'stock_comparison_with_max') and self.stock_comparison_with_max is not None:
        # Полное сравнение с MIN/MAX
        self.stock_comparison_with_max.to_excel(writer, sheet_name='Сравнение_MIN_MAX', index=False)
        
        # Товары с переизбытком
        excess_items = self.stock_comparison_with_max[
            self.stock_comparison_with_max['max_stock_status'] == 'ПЕРЕИЗБЫТОК'
        ]
        if not excess_items.empty:
            excess_items.to_excel(writer, sheet_name='Товары_с_переизбытком', index=False)
        
        # Оптимальные остатки
        optimal_items = self.stock_comparison_with_max[
            self.stock_comparison_with_max['max_stock_status'] == 'ОПТИМАЛЬНЫЙ'
        ]
        if not optimal_items.empty:
            optimal_items.to_excel(writer, sheet_name='Оптимальные_остатки', index=False)
        
        # Сводка эффективности
        efficiency = self.get_stock_efficiency_analysis()
        if 'error' not in efficiency:
            efficiency_df = pd.DataFrame([{
                'Метрика': 'Оптимальные остатки (%)',
                'Значение': efficiency['efficiency_metrics']['optimal_percentage']
            }, {
                'Метрика': 'Переизбыток (%)',
                'Значение': efficiency['efficiency_metrics']['excess_percentage']
            }, {
                'Метрика': 'Недостаток (%)',
                'Значение': efficiency['efficiency_metrics']['deficit_percentage']
            }, {
                'Метрика': 'Товаров с переизбытком',
                'Значение': efficiency['financial_impact']['excess_items_count']
            }, {
                'Метрика': 'Общий избыток (единиц)',
                'Значение': efficiency['financial_impact']['total_excess_units']
            }])
            efficiency_df.to_excel(writer, sheet_name='Сводка_эффективности', index=False)
    '''
    
    return integration_code

# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====

def create_stock_zones_dashboard(system):
    """Создание дашборда с зонами остатков"""
    
    if not hasattr(system, 'stock_comparison_with_max'):
        return None
    
    comparison = system.stock_comparison_with_max
    
    # Подготавливаем данные для дашборда
    dashboard_data = []
    
    for _, row in comparison.iterrows():
        current = row['total_current_stock']
        min_stock = row.get('min_stock_total', 0)
        max_stock = row.get('general_max_stock', 0)
        
        # Определяем в какой зоне находится товар
        if current < min_stock:
            zone = 'Недостаток'
            zone_percentage = (current / min_stock * 100) if min_stock > 0 else 0
        elif current <= max_stock:
            zone = 'Оптимальная'
            zone_percentage = ((current - min_stock) / (max_stock - min_stock) * 100) if (max_stock - min_stock) > 0 else 50
        else:
            zone = 'Переизбыток'
            zone_percentage = 100 + ((current - max_stock) / max_stock * 100) if max_stock > 0 else 100
        
        dashboard_data.append({
            'товар': row['номенклатура'],
            'текущий_остаток': current,
            'min_остаток': min_stock,
            'max_остаток': max_stock,
            'зона': zone,
            'зона_процент': zone_percentage,
            'ads': row.get('ads', 0),
            'статус': row.get('max_stock_status', 'Неизвестно')
        })
    
    return pd.DataFrame(dashboard_data)

def create_advanced_stock_charts(system):
    """Создание продвинутых графиков анализа остатков"""
    
    if not hasattr(system, 'stock_comparison_with_max'):
        return {}
    
    charts = {}
    comparison = system.stock_comparison_with_max
    
    # 1. Bubble chart: ADS vs Текущий остаток vs MAX остаток
    fig_bubble = px.scatter(
        comparison.head(50),
        x='ads',
        y='total_current_stock',
        size='general_max_stock',
        color='max_stock_status',
        hover_data=['номенклатура'],
        title='Анализ остатков: ADS vs Текущий vs MAX',
        labels={
            'ads': 'ADS (среднедневные продажи)',
            'total_current_stock': 'Текущий остаток',
            'max_stock_status': 'Статус'
        },
        color_discrete_map={
            'ОПТИМАЛЬНЫЙ': '#00aa44',
            'ВЫСОКИЙ': '#ffaa00',
            'НЕДОСТАТОК': '#ff4444',
            'ПЕРЕИЗБЫТОК': '#aa0044'
        }
    )
    charts['bubble_analysis'] = fig_bubble
    
    # 2. Heatmap эффективности по категориям
    if 'category' in comparison.columns:
        # Группируем по категориям и статусам
        heatmap_data = comparison.groupby(['category', 'max_stock_status']).size().unstack(fill_value=0)
        
        # Нормализуем по строкам (процент в каждой категории)
        heatmap_percentage = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100
        
        fig_heatmap = px.imshow(
            heatmap_percentage.values,
            x=heatmap_percentage.columns,
            y=heatmap_percentage.index,
            color_continuous_scale='RdYlGn_r',
            title='Heatmap эффективности остатков по категориям (%)',
            labels={'color': 'Процент товаров'}
        )
        charts['category_heatmap'] = fig_heatmap
    
    # 3. Waterfall chart изменений остатков
    waterfall_data = []
    total_min = comparison['min_stock_total'].sum()
    total_current = comparison['total_current_stock'].sum()
    total_max = comparison['general_max_stock'].sum()
    
    waterfall_data = [
        ('MIN остатки', total_min, 'relative'),
        ('Текущие остатки', total_current - total_min, 'relative'),
        ('MAX остатки', total_max - total_current, 'relative'),
        ('Итого MAX', total_max, 'total')
    ]
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Анализ остатков",
        orientation="v",
        measure=['relative', 'relative', 'relative', 'total'],
        x=[item[0] for item in waterfall_data],
        y=[item[1] for item in waterfall_data],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig_waterfall.update_layout(
        title="Waterfall анализ: от MIN к MAX остаткам",
        yaxis_title="Количество единиц"
    )
    charts['waterfall'] = fig_waterfall
    
    # 4. Gauge chart общей эффективности
    efficiency = system.get_stock_efficiency_analysis()
    if 'error' not in efficiency:
        optimal_pct = efficiency['efficiency_metrics']['optimal_percentage']
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=optimal_pct,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Эффективность остатков (% оптимальных)"},
            delta={'reference': 70, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        charts['efficiency_gauge'] = fig_gauge
    
    return charts

def generate_stock_optimization_report(system) -> str:
    """Генерация отчета с рекомендациями по оптимизации остатков"""
    
    if not hasattr(system, 'stock_comparison_with_max'):
        return "Анализ MAX остатков не выполнен"
    
    comparison = system.stock_comparison_with_max
    efficiency = system.get_stock_efficiency_analysis()
    
    report = f"""
# 📊 ОТЧЕТ ПО ОПТИМИЗАЦИИ ОСТАТКОВ

## 📈 ОБЩАЯ СТАТИСТИКА

- **Всего товаров:** {len(comparison):,}
- **Оптимальные остатки:** {efficiency['status_distribution']['оптимальный']} ({efficiency['efficiency_metrics']['optimal_percentage']:.1f}%)
- **Переизбыток:** {efficiency['status_distribution']['переизбыток']} ({efficiency['efficiency_metrics']['excess_percentage']:.1f}%)
- **Недостаток:** {efficiency['status_distribution']['недостаток']} ({efficiency['efficiency_metrics']['deficit_percentage']:.1f}%)

## 🎯 КЛЮЧЕВЫЕ ПРОБЛЕМЫ

### 🔴 Товары с переизбытком:
"""
    
    if efficiency['financial_impact']['excess_items_count'] > 0:
        report += f"""
- **Количество:** {efficiency['financial_impact']['excess_items_count']} товаров
- **Общий избыток:** {efficiency['financial_impact']['total_excess_units']:,.0f} единиц
- **Средний избыток:** {efficiency['financial_impact']['avg_excess_per_item']:.1f} единиц на товар

**Топ-5 товаров с наибольшим переизбытком:**
"""
        for i, item in enumerate(efficiency['top_excess_items'][:5], 1):
            report += f"{i}. {item['номенклатура']}: {item['excess_stock']:.0f} единиц избытка\n"
    else:
        report += "✅ Товаров с переизбытком не обнаружено\n"
    
    # Анализ по зонам эффективности
    zone_analysis = comparison['max_stock_status'].value_counts()
    
    report += f"""

## 📊 РАСПРЕДЕЛЕНИЕ ПО ЗОНАМ ЭФФЕКТИВНОСТИ

- **🟢 Оптимальная зона:** {zone_analysis.get('ОПТИМАЛЬНЫЙ', 0)} товаров
- **🟡 Высокие остатки:** {zone_analysis.get('ВЫСОКИЙ', 0)} товаров  
- **🔴 Переизбыток:** {zone_analysis.get('ПЕРЕИЗБЫТОК', 0)} товаров
- **🔴 Недостаток:** {zone_analysis.get('НЕДОСТАТОК', 0)} товаров

## 💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ

### 🎯 Краткосрочные действия (1-2 недели):
"""
    
    # Генерируем рекомендации
    excess_pct = efficiency['efficiency_metrics']['excess_percentage']
    optimal_pct = efficiency['efficiency_metrics']['optimal_percentage']
    deficit_pct = efficiency['efficiency_metrics']['deficit_percentage']
    
    if excess_pct > 15:
        report += f"1. **СРОЧНО:** Прекратить заказы товаров с переизбытком ({efficiency['financial_impact']['excess_items_count']} позиций)\n"
        report += f"2. Организовать распродажу или перераспределение избыточных остатков\n"
    
    if deficit_pct > 20:
        report += f"3. **ПРИОРИТЕТ:** Экстренное пополнение {zone_analysis.get('НЕДОСТАТОК', 0)} товаров с недостатком\n"
    
    report += f"""
### 📈 Среднесрочные действия (1-2 месяца):

4. Пересмотреть параметры MIN/MAX для категорий с низкой эффективностью
5. Внедрить автоматические уведомления при достижении критических уровней
6. Оптимизировать частоту заказов для товаров в зоне "Высокие остатки"

### 🎯 Целевые показатели:

- **Оптимальные остатки:** увеличить до 70%+ (текущий: {optimal_pct:.1f}%)
- **Переизбыток:** снизить до <5% (текущий: {excess_pct:.1f}%)
- **Недостаток:** снизить до <10% (текущий: {deficit_pct:.1f}%)

## 💰 ЭКОНОМИЧЕСКИЙ ЭФФЕКТ

При достижении целевых показателей ожидается:
- Снижение замороженных средств в остатках на {efficiency['financial_impact']['total_excess_units'] * 0.7:.0f} единиц
- Улучшение оборачиваемости на 15-25%
- Снижение риска просрочки товаров
"""
    
    return report

# ===== ПРИМЕР ИСПОЛЬЗОВАНИЯ =====

def demo_max_stock_functionality():
    """Демонстрация работы с максимальными остатками"""
    
    demo_code = '''
# Пример использования функционала MAX остатков:

# 1. Добавляем функционал к системе
add_max_stock_functionality_to_system(system)

# 2. Настраиваем лимиты для разных типов точек
system.update_stock_limits('хаб', min_days=20, max_days=50)
system.update_stock_limits('магазин', min_days=10, max_days=25)

# 3. Рассчитываем MAX остатки
result = system.calculate_max_stock_with_types()

# 4. Анализируем эффективность
efficiency = system.get_stock_efficiency_analysis()

# 5. Создаем визуализации
charts = create_advanced_stock_charts(system)

# 6. Генерируем отчет
report = generate_stock_optimization_report(system)

print("✅ Функционал MAX остатков успешно внедрен!")
'''
    
    return demo_code

# ===== ФИНАЛЬНАЯ ИНТЕГРАЦИЯ =====

if __name__ == "__main__":
    print("📈 Модуль MAX остатков готов к интеграции!")
    print("\n" + "="*50)
    print("ПРЕИМУЩЕСТВА НОВОЙ ФУНКЦИОНАЛЬНОСТИ:")
    print("="*50)
    print("✅ Настраиваемые лимиты для разных типов точек")
    print("✅ Автоматическое определение зон эффективности")
    print("✅ Анализ переизбытка и недостатка товаров")
    print("✅ Продвинутые визуализации и дашборды")
    print("✅ Генерация отчетов с рекомендациями")
    print("✅ Интеграция с существующей системой")
    print("\n" + "="*50)
    print("СЛЕДУЮЩИЕ ШАГИ:")
    print("="*50)
    print("1. Скопировать код в новый файл max_stock_feature.py")
    print("2. Добавить импорты в streamlit_modular_app.py")
    print("3. Добавить новые страницы в навигацию")
    print("4. Обновить метод get_system_status()")
    print("5. Расширить метод export_all_results()")
    print("\n🚀 Готово к запуску!")