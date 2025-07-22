"""
Новые функции для отображения интегрированного анализа с учетом иерархии
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def show_integrated_analysis(integrated_analysis):
    """Отображение интегрированного анализа остатков и продаж с учетом иерархии"""
    
    st.subheader("🔗 Интегрированный анализ остатков и продаж")
    
    # Проверяем структуру данных
    recommendations = integrated_analysis.get('recommendations', [])
    warehouse_reports = integrated_analysis.get('warehouse_reports', {})
    
    # Создаем вкладки для разных видов отчетов
    tab1, tab2, tab3 = st.tabs([
        "📊 Общие рекомендации",
        "🏢 Отчеты по филиалам", 
        "📈 Анализ состояния"
    ])
    
    with tab1:
        st.subheader("📊 Рекомендации по перемещениям с учетом иерархии")
        
        # Метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего рекомендаций", len(recommendations))
        
        with col2:
            high_priority = len([r for r in recommendations if r['priority'] == 'Высокий'])
            st.metric("Высокий приоритет", high_priority)
        
        with col3:
            deficit_count = len([r for r in recommendations if r['type'] == 'deficit_replenishment'])
            st.metric("Пополнение дефицита", deficit_count)
        
        with col4:
            excess_count = len([r for r in recommendations if r['type'] == 'excess_return'])
            st.metric("Возврат избытка", excess_count)
        
        if recommendations:
            # Фильтры
            st.subheader("⚙️ Фильтры")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                type_filter = st.multiselect(
                    "Тип перемещения",
                    ['deficit_replenishment', 'excess_return', 'redistribution'],
                    format_func=lambda x: {
                        'deficit_replenishment': 'Пополнение дефицита',
                        'excess_return': 'Возврат избытка',
                        'redistribution': 'Перераспределение'
                    }.get(x, x),
                    default=['deficit_replenishment', 'excess_return', 'redistribution']
                )
            
            with col2:
                priority_filter = st.multiselect(
                    "Приоритет",
                    ['Высокий', 'Средний'],
                    default=['Высокий', 'Средний']
                )
            
            with col3:
                min_qty = st.number_input(
                    "Мин. количество",
                    min_value=1,
                    value=5,
                    step=5
                )
            
            # Фильтрация
            filtered_recommendations = [
                r for r in recommendations
                if r['type'] in type_filter 
                and r['priority'] in priority_filter 
                and r['quantity'] >= min_qty
            ]
            
            if filtered_recommendations:
                # Таблица рекомендаций
                st.subheader("📋 Детальные рекомендации")
                
                recommendations_data = []
                for i, rec in enumerate(filtered_recommendations, 1):
                    rec_type_display = {
                        'deficit_replenishment': '📥 Пополнение',
                        'excess_return': '📤 Возврат',
                        'redistribution': '🔄 Перераспределение'
                    }.get(rec['type'], rec['type'])
                    
                    recommendations_data.append({
                        '№': i,
                        'Тип': rec_type_display,
                        'Артикул': rec['article'],
                        'Наименование': rec['name'][:40] + '...' if len(rec['name']) > 40 else rec['name'],
                        'Откуда': rec['from_warehouse'],
                        'Куда': rec['to_warehouse'],
                        'Количество': rec['quantity'],
                        'Остаток (откуда)': rec['from_stock'],
                        'Остаток (куда)': rec['to_stock'],
                        'ADS': f"{rec.get('ads', 0):.1f}",
                        'Приоритет': rec['priority'],
                        'Причина': rec['reason']
                    })
                
                df_recommendations = pd.DataFrame(recommendations_data)
                st.dataframe(df_recommendations, use_container_width=True, height=400)
                
                # Экспорт
                csv = df_recommendations.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Скачать рекомендации",
                    data=csv,
                    file_name=f"hierarchical_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
                # Визуализация потоков
                st.subheader("🔄 Карта перемещений")
                
                # Группируем по типам
                movement_by_type = {
                    'deficit_replenishment': [],
                    'excess_return': [],
                    'redistribution': []
                }
                
                for rec in filtered_recommendations:
                    movement_by_type[rec['type']].append(rec)
                
                # График по типам
                type_counts = [len(movement_by_type[t]) for t in ['deficit_replenishment', 'excess_return', 'redistribution']]
                type_labels = ['Пополнение дефицита', 'Возврат избытка', 'Перераспределение']
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=type_labels,
                        y=type_counts,
                        marker_color=['green', 'orange', 'blue']
                    )
                ])
                fig.update_layout(
                    title="Распределение рекомендаций по типам",
                    xaxis_title="Тип перемещения",
                    yaxis_title="Количество рекомендаций"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("Нет рекомендаций, соответствующих выбранным фильтрам")
        else:
            st.info("Рекомендации по перемещениям не найдены")
    
    with tab2:
        st.subheader("🏢 Отчеты по каждому филиалу")
        
        if warehouse_reports:
            # Выбор склада
            warehouse_names = list(warehouse_reports.keys())
            selected_warehouse = st.selectbox(
                "Выберите филиал",
                warehouse_names,
                format_func=lambda x: f"{x} ({warehouse_reports[x]['type']}, уровень {warehouse_reports[x]['level']})"
            )
            
            if selected_warehouse:
                report = warehouse_reports[selected_warehouse]
                
                # Информация о складе
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Тип", report['type'])
                    st.metric("Уровень", report['level'])
                
                with col2:
                    st.metric("Город", report['city'])
                    st.metric("Родитель", report['parent'] or "Нет")
                
                with col3:
                    st.metric("Общая стоимость", f"{report['total_stock_cost']:,.0f} ₸")
                    st.metric("Общее количество", f"{report['total_stock_qty']:,.0f}")
                
                # Анализ товаров
                st.subheader("📦 Анализ состояния товаров")
                
                if report['products_analysis']:
                    # Группируем по состояниям
                    state_summary = {
                        'deficit': {'count': 0, 'products': []},
                        'normal': {'count': 0, 'products': []},
                        'excess': {'count': 0, 'products': []},
                        'no_sales': {'count': 0, 'products': []}
                    }
                    
                    for product in report['products_analysis']:
                        state = product['state']
                        state_summary[state]['count'] += 1
                        state_summary[state]['products'].append(product)
                    
                    # Метрики состояний
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🔴 Дефицит", state_summary['deficit']['count'])
                    
                    with col2:
                        st.metric("🟢 Норма", state_summary['normal']['count'])
                    
                    with col3:
                        st.metric("🟡 Избыток", state_summary['excess']['count'])
                    
                    with col4:
                        st.metric("⚪ Нет продаж", state_summary['no_sales']['count'])
                    
                    # Детальная таблица
                    product_data = []
                    for product in report['products_analysis']:
                        state_icon = {
                            'deficit': '🔴',
                            'normal': '🟢',
                            'excess': '🟡',
                            'no_sales': '⚪'
                        }.get(product['state'], '')
                        
                        product_data.append({
                            'Состояние': f"{state_icon} {product['state']}",
                            'Артикул': product['article'],
                            'Наименование': product['name'][:40] + '...' if len(product['name']) > 40 else product['name'],
                            'Остаток': product['current_stock'],
                            'Стоимость': f"{product['stock_cost']:,.0f} ₸",
                            'ADS': f"{product['ads']:.1f}",
                            'Дней остатка': f"{product['days_of_stock']:.1f}",
                            'Мин. остаток': f"{product.get('min_stock', 0):.0f}",
                            'Макс. остаток': f"{product.get('max_stock', 0):.0f}",
                            'Дефицит': f"{product['deficit']:.0f}",
                            'Избыток': f"{product['excess']:.0f}"
                        })
                    
                    df_products = pd.DataFrame(product_data)
                    
                    # Фильтр по состоянию
                    state_filter = st.multiselect(
                        "Фильтр по состоянию",
                        ['deficit', 'normal', 'excess', 'no_sales'],
                        format_func=lambda x: {
                            'deficit': '🔴 Дефицит',
                            'normal': '🟢 Норма',
                            'excess': '🟡 Избыток',
                            'no_sales': '⚪ Нет продаж'
                        }.get(x, x),
                        default=['deficit', 'excess']
                    )
                    
                    # Фильтрация
                    filtered_products = [p for p in product_data if any(s in p['Состояние'] for s in state_filter)]
                    
                    if filtered_products:
                        df_filtered = pd.DataFrame(filtered_products)
                        st.dataframe(df_filtered, use_container_width=True, height=400)
                
                # Рекомендации для склада
                st.subheader("🚚 Рекомендации для филиала")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Входящие перемещения:**")
                    if report['recommendations_in']:
                        for rec in report['recommendations_in']:
                            st.write(f"• {rec['article']} - {rec['quantity']} шт из {rec['from_warehouse']}")
                    else:
                        st.write("Нет входящих перемещений")
                
                with col2:
                    st.write("**Исходящие перемещения:**")
                    if report['recommendations_out']:
                        for rec in report['recommendations_out']:
                            st.write(f"• {rec['article']} - {rec['quantity']} шт в {rec['to_warehouse']}")
                    else:
                        st.write("Нет исходящих перемещений")
        
        else:
            st.info("Нет данных по филиалам")
    
    with tab3:
        st.subheader("📈 Общий анализ состояния сети")
        
        if warehouse_reports:
            # Сводная таблица по всем складам
            summary_data = []
            
            for wh_name, report in warehouse_reports.items():
                # Подсчет состояний
                states = {'deficit': 0, 'normal': 0, 'excess': 0, 'no_sales': 0}
                for product in report['products_analysis']:
                    states[product['state']] += 1
                
                summary_data.append({
                    'Филиал': wh_name,
                    'Тип': report['type'],
                    'Уровень': report['level'],
                    'Город': report['city'],
                    'Позиций': len(report['products_analysis']),
                    'Стоимость': f"{report['total_stock_cost']:,.0f} ₸",
                    'Дефицит': states['deficit'],
                    'Норма': states['normal'],
                    'Избыток': states['excess'],
                    'Нет продаж': states['no_sales'],
                    'Вход. рек.': len(report['recommendations_in']),
                    'Исх. рек.': len(report['recommendations_out'])
                })
            
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True)
            
            # Визуализация по типам складов
            fig = px.sunburst(
                df_summary,
                path=['Тип', 'Город', 'Филиал'],
                values='Позиций',
                title="Структура филиальной сети"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Анализ по уровням
            level_analysis = df_summary.groupby('Уровень').agg({
                'Дефицит': 'sum',
                'Норма': 'sum',
                'Избыток': 'sum',
                'Нет продаж': 'sum'
            }).reset_index()
            
            fig = go.Figure(data=[
                go.Bar(name='Дефицит', x=level_analysis['Уровень'], y=level_analysis['Дефицит'], marker_color='red'),
                go.Bar(name='Норма', x=level_analysis['Уровень'], y=level_analysis['Норма'], marker_color='green'),
                go.Bar(name='Избыток', x=level_analysis['Уровень'], y=level_analysis['Избыток'], marker_color='orange'),
                go.Bar(name='Нет продаж', x=level_analysis['Уровень'], y=level_analysis['Нет продаж'], marker_color='gray')
            ])
            
            fig.update_layout(
                barmode='stack',
                title="Распределение состояний товаров по уровням иерархии",
                xaxis_title="Уровень",
                yaxis_title="Количество позиций"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Нет данных для анализа")