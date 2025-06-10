#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STREAMLIT UI для функционала замены ADS=0 на средний по категории
Пользовательский интерфейс для работы с заменой ADS=0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def show_ads_zero_replacement_ui(system):
    """
    Основной UI для замены ADS=0 на средний по категории
    
    Args:
        system: Объект системы инвентаря
    """
    
    st.markdown("---")
    st.subheader("🔧 Замена ADS = 0 на средний по категории")
    
    # Проверяем наличие данных ADS
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("⚠️ Сначала необходимо рассчитать ADS")
        return
    
    ads_data = system.calculated_ads
    total_items = len(ads_data)
    zero_ads_count = len(ads_data[ads_data['ads'] == 0])
    positive_ads_count = total_items - zero_ads_count
    
    # Показываем текущую статистику
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего товаров", total_items)
    
    with col2:
        st.metric("С ADS = 0", zero_ads_count, 
                 delta=f"{(zero_ads_count/total_items*100):.1f}%" if total_items > 0 else "0%")
    
    with col3:
        st.metric("С ADS > 0", positive_ads_count)
    
    with col4:
        if zero_ads_count > 0:
            st.metric("Требует замены", "ДА", delta="🔧")
        else:
            st.metric("Требует замены", "НЕТ", delta="✅")
    
    if zero_ads_count == 0:
        st.success("✅ Все товары имеют рассчитанный ADS. Замена не требуется.")
        return
    
    # Интегрируем функционал если еще не интегрирован
    if not hasattr(system, 'ads_zero_replacer'):
        from ads_zero_category_replacement import integrate_ads_zero_category_replacement_to_system
        integrate_ads_zero_category_replacement_to_system(system)
    
    # Показываем источники категорий
    st.markdown("### 📋 Источники категорий")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Проверяем ABC данные
        has_abc = hasattr(system, 'abc_data') and system.abc_data is not None
        if has_abc:
            st.success("✅ ABC анализ загружен")
            st.caption(f"Доступно {len(system.abc_data)} товаров с категориями")
        else:
            st.info("📊 ABC анализ не загружен")
    
    with col2:
        # Проверяем возможность автоматического создания категорий
        st.info("🤖 Автоматическое создание категорий")
        st.caption("Из названий товаров (резервный вариант)")
    
    # Кнопка предварительного просмотра
    if st.button("🔍 Предварительный просмотр категорий", type="secondary"):
        with st.spinner("Анализируем источники категорий..."):
            category_mapping, source_info = system.ads_zero_replacer.extract_categories_from_sources(system)
            
            if category_mapping:
                st.success(f"✅ Найдено {len(category_mapping)} товаров с категориями")
                st.info(f"📋 Источник: {source_info}")
                
                # Показываем статистику по категориям
                categories_df = pd.DataFrame([
                    {'номенклатура': k, 'категория': v} 
                    for k, v in list(category_mapping.items())[:10]
                ])
                
                st.markdown("**Примеры категорий:**")
                st.dataframe(categories_df, use_container_width=True)
                
                # Статистика по количеству товаров в категориях
                category_counts = pd.Series(list(category_mapping.values())).value_counts().head(10)
                
                fig = px.bar(
                    x=category_counts.values,
                    y=category_counts.index,
                    orientation='h',
                    title="Топ-10 категорий по количеству товаров",
                    labels={'x': 'Количество товаров', 'y': 'Категория'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("❌ Не удалось найти категории. Загрузите ABC анализ.")
    
    st.markdown("---")
    
    # Основная кнопка замены
    st.markdown("### 🚀 Выполнить замену")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Заменить ADS = 0 на средний по категории", 
                    type="primary", 
                    use_container_width=True):
            
            with st.spinner("Выполняем замену ADS = 0..."):
                result = system.replace_zero_ads_with_category_avg()
                
                if result['success']:
                    st.success(f"✅ Замена выполнена успешно!")
                    
                    # Показываем результаты
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Заменено", result['zero_ads_replaced'])
                    
                    with col2:
                        st.metric("Не заменено", result['zero_ads_not_replaced'])
                    
                    with col3:
                        st.metric("Категорий использовано", result['categories_used'])
                    
                    st.info(f"📋 Источник категорий: {result['source_info']}")
                    
                    # Показываем примеры замен
                    if 'replacement_log' in result and result['replacement_log']:
                        st.markdown("**Примеры выполненных замен:**")
                        replacement_df = pd.DataFrame(result['replacement_log'])
                        st.dataframe(replacement_df, use_container_width=True)
                    
                    # Обновляем статистику
                    st.rerun()
                
                else:
                    st.error(f"❌ Ошибка замены: {result.get('error', 'Неизвестная ошибка')}")
    
    with col2:
        # Проверяем есть ли замены для отмены
        has_replacements = (hasattr(system, 'ads_zero_replacer') and 
                          system.ads_zero_replacer.original_ads_data is not None)
        
        if has_replacements:
            if st.button("↩️ Отменить замены", 
                        type="secondary", 
                        use_container_width=True):
                
                if system.revert_ads_zero_replacement():
                    st.success("✅ Замены отменены, восстановлены оригинальные данные")
                    st.rerun()
                else:
                    st.error("❌ Ошибка отмены замен")
        else:
            st.button("↩️ Отменить замены", 
                     disabled=True, 
                     use_container_width=True,
                     help="Сначала выполните замены")


def show_ads_zero_statistics_ui(system):
    """
    UI для отображения статистики замен ADS=0
    
    Args:
        system: Объект системы инвентаря
    """
    
    if not hasattr(system, 'ads_zero_replacer'):
        return
    
    # Получаем статистику замен
    stats = system.get_ads_replacement_stats()
    
    if 'error' in stats:
        return
    
    st.markdown("---")
    st.subheader("📊 Статистика замен ADS = 0")
    
    # Общая статистика
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего замен", stats['total_replacements'])
    
    with col2:
        st.metric("Категорий задействовано", stats['categories_used'])
    
    with col3:
        st.metric("Средний новый ADS", f"{stats['average_new_ads']:.4f}")
    
    # Детальная статистика по категориям
    if 'category_statistics' in stats and stats['category_statistics']:
        st.markdown("### 📋 Статистика по категориям")
        
        category_stats = stats['category_statistics']
        
        # Создаем DataFrame для отображения
        category_df = pd.DataFrame([
            {
                'Категория': category,
                'Замен выполнено': data['count'],
                'Средний ADS': data['avg_new_ads'],
                'Общий ADS': data['total_new_ads']
            }
            for category, data in category_stats.items()
        ])
        
        # Сортируем по количеству замен
        category_df = category_df.sort_values('Замен выполнено', ascending=False)
        
        # Показываем таблицу
        st.dataframe(category_df, use_container_width=True)
        
        # Визуализация - количество замен по категориям
        if len(category_df) > 1:
            fig1 = px.bar(
                category_df.head(10),
                x='Категория',
                y='Замен выполнено',
                title="Количество замен по категориям (топ-10)",
                color='Замен выполнено',
                color_continuous_scale='viridis'
            )
            fig1.update_layout(height=400)
            fig1.update_xaxis(tickangle=45)
            st.plotly_chart(fig1, use_container_width=True)
            
            # Визуализация - средний ADS по категориям
            fig2 = px.scatter(
                category_df.head(15),
                x='Замен выполнено',
                y='Средний ADS',
                size='Общий ADS',
                hover_name='Категория',
                title="Соотношение количества замен и среднего ADS по категориям",
                labels={'Замен выполнено': 'Количество замен', 'Средний ADS': 'Средний ADS'}
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)


def show_ads_comparison_before_after_ui(system):
    """
    UI для сравнения ADS до и после замен
    
    Args:
        system: Объект системы инвентаря
    """
    
    if not hasattr(system, 'ads_zero_replacer') or system.ads_zero_replacer.original_ads_data is None:
        return
    
    st.markdown("---")
    st.subheader("🔍 Сравнение до и после замен")
    
    original_data = system.ads_zero_replacer.original_ads_data
    current_data = system.calculated_ads
    
    # Общая статистика сравнения
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**До замен:**")
        orig_zero = len(original_data[original_data['ads'] == 0])
        orig_positive = len(original_data[original_data['ads'] > 0])
        orig_total_ads = original_data['ads'].sum()
        
        st.metric("Товаров с ADS = 0", orig_zero)
        st.metric("Товаров с ADS > 0", orig_positive)
        st.metric("Общий ADS", f"{orig_total_ads:.2f}")
    
    with col2:
        st.markdown("**После замен:**")
        curr_zero = len(current_data[current_data['ads'] == 0])
        curr_positive = len(current_data[current_data['ads'] > 0])
        curr_total_ads = current_data['ads'].sum()
        
        st.metric("Товаров с ADS = 0", curr_zero, delta=curr_zero - orig_zero)
        st.metric("Товаров с ADS > 0", curr_positive, delta=curr_positive - orig_positive)
        st.metric("Общий ADS", f"{curr_total_ads:.2f}", delta=f"{curr_total_ads - orig_total_ads:.2f}")
    
    # Визуализация сравнения
    comparison_data = {
        'Состояние': ['До замен', 'После замен'],
        'ADS = 0': [orig_zero, curr_zero],
        'ADS > 0': [orig_positive, curr_positive],
        'Общий ADS': [orig_total_ads, curr_total_ads]
    }
    
    # График сравнения количества товаров
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        name='ADS = 0',
        x=comparison_data['Состояние'],
        y=comparison_data['ADS = 0'],
        marker_color='red'
    ))
    
    fig1.add_trace(go.Bar(
        name='ADS > 0',
        x=comparison_data['Состояние'],
        y=comparison_data['ADS > 0'],
        marker_color='green'
    ))
    
    fig1.update_layout(
        title='Сравнение количества товаров до и после замен',
        xaxis_title='Состояние',
        yaxis_title='Количество товаров',
        barmode='stack',
        height=400
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # График изменения общего ADS
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=comparison_data['Состояние'],
        y=comparison_data['Общий ADS'],
        mode='lines+markers',
        name='Общий ADS',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    
    fig2.update_layout(
        title='Изменение общего ADS после замен',
        xaxis_title='Состояние',
        yaxis_title='Общий ADS',
        height=300
    )
    
    st.plotly_chart(fig2, use_container_width=True)


def show_ads_zero_export_ui(system):
    """
    UI для экспорта отчета о заменах ADS=0
    
    Args:
        system: Объект системы инвентаря
    """
    
    if not hasattr(system, 'ads_zero_replacer'):
        return
    
    report_df = system.export_ads_replacement_report()
    
    if report_df.empty:
        return
    
    st.markdown("---")
    st.subheader("📤 Экспорт отчета о заменах")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"📋 Доступно {len(report_df)} записей для экспорта")
    
    with col2:
        # Кнопка экспорта
        if st.button("📥 Скачать отчет Excel", type="secondary"):
            try:
                # Создаем Excel файл
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    report_df.to_excel(writer, sheet_name='Замены_ADS_0', index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="💾 Скачать файл",
                    data=excel_data,
                    file_name=f"ads_zero_replacements_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Ошибка создания Excel файла: {str(e)}")
    
    # Предварительный просмотр отчета
    if st.checkbox("👁️ Показать предварительный просмотр"):
        st.dataframe(report_df.head(20), use_container_width=True)


def integrate_ads_zero_ui_to_streamlit_app():
    """
    Инструкция по интеграции UI в основное Streamlit приложение
    """
    
    instructions = """
    🔧 ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ UI ЗАМЕНЫ ADS=0:
    
    1. Добавьте импорт в начало вашего streamlit файла:
       from streamlit_ads_zero_category_ui import (
           show_ads_zero_replacement_ui,
           show_ads_zero_statistics_ui,
           show_ads_comparison_before_after_ui,
           show_ads_zero_export_ui
       )
    
    2. В страницу ADS расчета добавьте после основного контента:
       
       # В функции ads_calculation_page_updated(system):
       # ... существующий код расчета ADS ...
       
       # НОВОЕ: Добавляем UI замены ADS=0
       if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
           show_ads_zero_replacement_ui(system)
           show_ads_zero_statistics_ui(system)
           show_ads_comparison_before_after_ui(system)
           show_ads_zero_export_ui(system)
    
    3. Или создайте отдельную страницу:
       
       elif page == "🔧 Замена ADS = 0":
           st.header("🔧 Замена ADS = 0 на средний по категории")
           
           if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
               st.warning("Сначала рассчитайте ADS на странице 'ADS расчет'")
           else:
               show_ads_zero_replacement_ui(system)
               show_ads_zero_statistics_ui(system)
               show_ads_comparison_before_after_ui(system)
               show_ads_zero_export_ui(system)
    
    4. РЕЗУЛЬТАТ:
       ✅ Полный UI для работы с заменой ADS=0
       ✅ Предварительный просмотр категорий
       ✅ Статистика и визуализации замен
       ✅ Сравнение до/после замен
       ✅ Экспорт отчетов
       ✅ Возможность отмены изменений
    
    5. ТРЕБОВАНИЯ:
       - Файл ads_zero_category_replacement.py должен быть доступен
       - Система должна иметь рассчитанный ADS
       - Для категорий желательно иметь ABC анализ
    """
    
    return instructions


# Демонстрационная функция для тестирования UI
def demo_ads_zero_ui():
    """Демонстрация UI для замены ADS=0"""
    
    st.set_page_config(
        page_title="Замена ADS = 0",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Замена ADS = 0 на средний по категории")
    st.markdown("*Демонстрация пользовательского интерфейса*")
    
    # Инструкции по интеграции
    with st.expander("📖 Инструкции по интеграции"):
        st.code(integrate_ads_zero_ui_to_streamlit_app())
    
    # Информация о функционале
    st.markdown("""
    ### 🎯 Что делает этот функционал:
    
    1. **Анализирует товары с ADS = 0** - находит товары без продаж
    2. **Извлекает категории** - из ABC анализа или создает автоматически
    3. **Рассчитывает средний ADS по категориям** - только из товаров с ADS > 0
    4. **Заменяет ADS = 0** - на средний ADS соответствующей категории
    5. **Ведет полный лог изменений** - с возможностью отмены
    6. **Предоставляет детальную статистику** - и визуализации
    
    ### 📋 Источники категорий (по приоритету):
    1. **ABC анализ** - если загружен (наивысший приоритет)
    2. **Автоматическое создание** - из названий товаров
    
    ### 🔧 Как использовать:
    1. Рассчитайте ADS для товаров
    2. Загрузите ABC анализ (рекомендуется)
    3. Используйте функционал замены ADS = 0
    4. Проверьте результаты и статистику
    """)


if __name__ == "__main__":
    demo_ads_zero_ui()