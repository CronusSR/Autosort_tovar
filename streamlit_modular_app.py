#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульное Streamlit приложение для системы анализа товарных запасов
"""
import json
import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modular_inventory_system import ModularInventorySystem
from integration_patch import add_multiple_files_interface_to_existing
import io
import time
import warnings
from subcategory_abc import create_subcategory_abc_interface
from typing import Dict, List, Optional 
warnings.filterwarnings('ignore')

# Конфигурация страницы
st.set_page_config(
    page_title="Модульная система анализа товарных запасов",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)
def safe_rerun():
    time.sleep(0.1)
    st.rerun()
def _extract_branch_name(filename: str) -> str:
    """Извлечение названия филиала из имени файла"""
    # Убираем расширение
    name = filename.lower().replace('.xlsx', '').replace('.xls', '')
    
    # Ищем ключевые слова филиалов
    if 'шымкент' in name:
        if 'скл' in name:
            return 'шымкент_склад'
        elif 'маг' in name:
            return 'шымкент_магазин'
        else:
            return 'шымкент'
    elif 'астана' in name:
        if 'скл' in name:
            return 'астана_склад'
        else:
            return 'астана'
    elif 'барыс' in name:
        return 'барыс'
    elif 'казыб' in name:
        if 'скл' in name:
            return 'казыбаева_склад'
        elif 'тд' in name:
            return 'казыбаева_тд'
        else:
            return 'казыбаева'
    else:
        # Если не удалось определить, используем имя файла
        return name.replace(' ', '_').replace('-', '_')


def init_system():
    """Инициализация системы"""
    if 'inventory_system' not in st.session_state:
        st.session_state.inventory_system = ModularInventorySystem()
    return st.session_state.inventory_system

def subcategory_abc_analysis_page(system):
    """Страница ABC анализа по подкатегориям"""
    st.header("🔤📊 ABC анализ по подкатегориям")
    
    st.markdown("""
    **Расширенный ABC анализ** с детализацией до подкатегорий позволяет:
    - 🎯 Более точно управлять ассортиментом на уровне подгрупп
    - 📈 Выявлять эффективные и неэффективные подкатегории
    - 🔍 Анализировать концентрацию продаж внутри категорий
    - 💡 Получать рекомендации по оптимизации структуры товаров
    """)
    
    status = system.get_system_status()
    
    # Проверяем наличие ABC данных
    if not status['abc_analysis']['analyzed']:
        st.warning("⚠️ Сначала необходимо выполнить основной ABC анализ")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔤 Перейти к ABC анализу"):
                st.info("Переключитесь на вкладку 'ABC анализ' для загрузки данных")
        
        with col2:
            st.info("""
            **Для анализа подкатегорий нужны:**
            - Основной ABC анализ
            - Данные с подкатегориями товаров
            - Информация о продажах
            """)
        return
    
    # Проверяем статус анализа подкатегорий
    subcategory_status = status.get('subcategory_analysis', {})
    
    if not subcategory_status.get('analyzed', False):
        # Анализ еще не выполнен
        st.info("📊 Основной ABC анализ выполнен. Готов к анализу подкатегорий.")
        
        # Показываем информацию о доступных данных
        if hasattr(system, 'abc_data') and system.abc_data is not None:
            abc_data = system.abc_data
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров в ABC", len(abc_data))
            with col2:
                categories_count = abc_data['category'].nunique() if 'category' in abc_data.columns else 0
                st.metric("Категорий", categories_count)
            with col3:
                subcategories_count = abc_data['subcategory'].nunique() if 'subcategory' in abc_data.columns else 0
                st.metric("Подкатегорий", subcategories_count)
            with col4:
                ratio = subcategories_count / categories_count if categories_count > 0 else 0
                st.metric("Подкат./Категория", f"{ratio:.1f}")
            
            # Предварительный анализ структуры
            if 'subcategory' in abc_data.columns:
                st.success("✅ Данные содержат информацию о подкатегориях")
                
                # Показываем примеры подкатегорий
                with st.expander("👁️ Предварительный просмотр подкатегорий"):
                    sample_subcategories = abc_data.groupby(['category', 'subcategory']).size().reset_index(name='товаров')
                    sample_subcategories = sample_subcategories.head(10)
                    st.dataframe(sample_subcategories, use_container_width=True)
                
            else:
                st.warning("""
                ⚠️ **Колонка 'subcategory' не найдена**
                
                Система попытается создать подкатегории из категорий.
                Для лучших результатов убедитесь что в исходных данных есть:
                - Колонка 'subcategory' с названиями подкатегорий
                - Логичная иерархия: категория → подкатегория → товар
                """)
            
            # Кнопка запуска анализа
            if st.button("🚀 Выполнить анализ подкатегорий", use_container_width=True):
                with st.spinner("Выполнение ABC анализа по подкатегориям..."):
                    analysis_result = system.perform_subcategory_abc_analysis()
                    
                    if analysis_result['success']:
                        st.success("✅ Анализ подкатегорий завершен успешно!")
                        
                        # Показываем краткие результаты
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Подкатегорий проанализировано", analysis_result['total_subcategories'])
                        with col2:
                            st.metric("Товаров обработано", analysis_result['total_items'])
                        with col3:
                            st.metric("Категорий охвачено", analysis_result['categories_analyzed'])
                        
                        st.rerun()
                    else:
                        st.error(f"❌ {analysis_result['error']}")
        else:
            st.error("❌ Данные ABC анализа недоступны")
    
    else:
        # Анализ выполнен - показываем результаты
        st.success("✅ Анализ подкатегорий выполнен!")
        
        # Получаем сводку
        subcategory_summary = system.get_subcategory_summary_report()
        
        if subcategory_summary and 'error' not in subcategory_summary:
            # Общая статистика
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Подкатегорий", subcategory_summary['total_subcategories'])
            with col2:
                st.metric("Эффективных", f"{subcategory_summary['efficient_subcategories']}")
            with col3:
                st.metric("Эффективность", f"{subcategory_summary['efficiency_percentage']:.1f}%")
            with col4:
                st.metric("Товаров/Подкат.", f"{subcategory_summary['average_items_per_subcategory']:.1f}")
            with col5:
                st.metric("Категорий", subcategory_summary['categories_analyzed'])
            
            # ABC распределение
            st.subheader("🔤 ABC распределение по подкатегориям")
            abc_dist = subcategory_summary['abc_distribution']
            
            abc_col1, abc_col2, abc_col3 = st.columns(3)
            with abc_col1:
                st.metric("🔴 A товары", abc_dist['A'])
            with abc_col2:
                st.metric("🟡 B товары", abc_dist['B'])
            with abc_col3:
                st.metric("🟢 C товары", abc_dist['C'])
            
            # Визуализация ABC распределения
            if hasattr(system, 'subcategory_analyzer'):
                visualizations = system.subcategory_analyzer.create_subcategory_visualizations()
                
                if 'abc_distribution' in visualizations:
                    st.plotly_chart(
                        visualizations['abc_distribution'], 
                        use_container_width=True,
                        key="main_page_subcategory_abc_distribution"
                    )
        
        # Основной интерфейс анализа подкатегорий
        st.markdown("---")
        
        # Используем ABC данные из системы
        if hasattr(system, 'abc_data') and system.abc_data is not None:
            create_subcategory_abc_interface(system.abc_data)
        
        # Дополнительные действия
        st.subheader("📤 Экспорт и управление")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Экспорт подкатегорий Excel"):
                excel_buffer = system.export_subcategory_results()
                
                if excel_buffer:
                    st.download_button(
                        label="💾 Скачать отчет подкатегорий",
                        data=excel_buffer,
                        file_name=f"subcategory_abc_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Ошибка создания Excel файла")
        
        with col2:
            if st.button("🔄 Пересчитать анализ"):
                # Очищаем результаты для пересчета
                if hasattr(system, 'subcategory_results'):
                    system.subcategory_results = None
                if hasattr(system, 'subcategory_analyzer'):
                    system.subcategory_analyzer.subcategory_results = None
                st.success("✅ Данные очищены. Нажмите 'Выполнить анализ' для пересчета.")
                st.rerun()
        
        with col3:
            # Показываем краткие рекомендации
            if hasattr(system, 'subcategory_results') and system.subcategory_results:
                recommendations = system.subcategory_results.get('recommendations', [])
                if recommendations:
                    with st.popover("💡 Рекомендации"):
                        for i, rec in enumerate(recommendations[:3], 1):
                            st.write(f"**{i}.** {rec}")
                        if len(recommendations) > 3:
                            st.write(f"... и еще {len(recommendations) - 3} рекомендаций")

def show_system_status(system):
    """Отображение статуса системы с информацией о ценах"""
    status = system.get_system_status()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        abc_status = "✅" if status['abc_analysis']['analyzed'] else "❌"
        st.metric(
            "ABC анализ", 
            f"{abc_status} {status['abc_analysis']['items_count']} товаров"
        )
    
    with col2:
        ads_status = "✅" if status['sales_analysis']['ads_calculated'] else "❌"
        # НОВОЕ: Показываем информацию о ценах в ADS
        price_info = ""
        if (status['sales_analysis']['ads_calculated'] and 
            hasattr(system, 'calculated_ads') and 
            system.calculated_ads is not None and
            'last_purchase_price' in system.calculated_ads.columns):
            
            items_with_price = len(system.calculated_ads[system.calculated_ads['last_purchase_price'] > 0])
            if items_with_price > 0:
                price_info = f" 💰{items_with_price}"
        
        st.metric(
            "ADS расчет", 
            f"{ads_status} {status['sales_analysis']['items_count']} товаров{price_info}"
        )
    
    with col3:
        min_status = "✅" if status['min_stock_analysis']['calculated'] else "❌"
        st.metric(
            "MIN запасы", 
            f"{min_status} {status['min_stock_analysis']['items_count']} товаров"
        )
    
    with col4:
        stock_status = "✅" if status['stock_analysis']['compared'] else "❌"
        # НОВОЕ: Показываем информацию о денежных расчетах
        money_info = ""
        if (status['stock_analysis']['compared'] and 
            hasattr(system, 'stock_comparison') and 
            system.stock_comparison is not None and
            'stock_deficit_money' in system.stock_comparison.columns):
            
            total_deficit_money = system.stock_comparison['stock_deficit_money'].sum()
            if total_deficit_money > 0:
                money_info = f" 💰{total_deficit_money:,.0f}₸"
        
        st.metric(
            "Сравнение", 
            f"{stock_status} {status['stock_analysis']['items_count']} товаров{money_info}"
        )

    with col5:
        subcat_status = "✅" if status['subcategory_analysis']['analyzed'] else "❌"
        subcat_count = status['subcategory_analysis']['subcategories_count']
        st.metric(
            "Подкатегории", 
            f"{subcat_status} {subcat_count} подкат."
        )
    
    # Прогресс-бар
    progress = status['overall']['progress_percentage']
    st.progress(progress / 100)
    
    # НОВОЕ: Показываем информацию о денежных возможностях
    money_status = ""
    if (hasattr(system, 'calculated_ads') and 
        system.calculated_ads is not None and
        'last_purchase_price' in system.calculated_ads.columns):
        
        items_with_price = len(system.calculated_ads[system.calculated_ads['last_purchase_price'] > 0])
        total_items = len(system.calculated_ads)
        coverage = (items_with_price / total_items) * 100 if total_items > 0 else 0
        
        if coverage > 80:
            money_status = f" | 💰 Денежные расчеты доступны ({coverage:.0f}% покрытия)"
        elif coverage > 50:
            money_status = f" | 💰 Частичные денежные расчеты ({coverage:.0f}% покрытия)"
        elif coverage > 0:
            money_status = f" | 💰 Ограниченные денежные расчеты ({coverage:.0f}% покрытия)"
    
    st.write(f"**Общий прогресс:** {progress:.0f}% ({status['overall']['completed_steps']}/5 этапов){money_status}")

def abc_analysis_page_updated(system):
    """Обновленная страница ABC анализа с информацией о ценах"""
    st.header("🔤 ABC анализ товаров (включая цены из колонки 'Посл. закупка')")
    
    st.markdown("""
    **ABC анализ** помогает классифицировать товары по принципу Парето (80/20):
    - **A товары** - 80% продаж (обычно 20% товаров)
    - **B товары** - 15% продаж  
    - **C товары** - 5% продаж + **все товары с нулевыми продажами**
    
    ✅ **Новое**: 
    - Товары с пустыми ячейками продаж автоматически получают значение 0 и класс C
    - 💰 **Загрузка цен** из колонки 12 "Посл. закупка" для денежных расчетов
    """)
    
    # Проверяем статус ABC анализа
    status = system.get_system_status()
    
    if status['abc_analysis']['analyzed']:
        # ABC анализ уже выполнен
        st.success("✅ ABC анализ завершен!")
        
        # Показываем результаты
        abc_results = system.abc_results
        abc_summary = abc_results['abc_summary']
        total_items = sum(abc_summary.values())
        
        # Проверяем наличие информации о нулевых продажах и ценах
        zero_sales_count = abc_results.get('items_with_zero_sales', 0)
        items_with_sales = abc_results.get('items_with_sales', total_items)
        items_with_price = abc_results.get('items_with_price', 0)
        items_without_price = abc_results.get('items_without_price', 0)
        
        # Расширенная статистика
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            a_count = abc_summary.get('A', 0)
            st.metric("A товары", f"{a_count} ({a_count/total_items*100:.1f}%)")
        with col2:
            b_count = abc_summary.get('B', 0)
            st.metric("B товары", f"{b_count} ({b_count/total_items*100:.1f}%)")
        with col3:
            c_count = abc_summary.get('C', 0)
            st.metric("C товары", f"{c_count} ({c_count/total_items*100:.1f}%)")
        with col4:
            st.metric("Всего товаров", f"{total_items}")
        
        # НОВАЯ информация о ценах
        if items_with_price > 0:
            st.success(f"""
            💰 **Информация о ценах загружена:**
            - Товаров с ценой > 0: **{items_with_price}** ({items_with_price/total_items*100:.1f}%)
            - Товаров без цены: **{items_without_price}** ({items_without_price/total_items*100:.1f}%)
            - Средняя цена: **{abc_results.get('average_price', 0):,.2f}** ₸
            - Денежные расчеты дефицита: **Доступны** ✅
            """)
        else:
            st.warning("""
            💰 **Цены не загружены:**
            - Колонка 'Посл. закупка' не найдена или пуста
            - Денежные расчеты дефицита будут недоступны
            - Рекомендуется проверить структуру файла
            """)
        
        # Остальной код страницы остается без изменений...
        # (визуализации, анализ по категориям и т.д.)
        
    else:
        # ABC анализ не выполнен
        st.info("Загрузите файл для ABC анализа (например: исходники.xlsx)")
        
        st.success("""
        ✅ **Улучшения в обработке данных:**
        
        - **Пустые ячейки продаж** автоматически заменяются на **0**
        - **Все товары** включаются в ABC анализ (даже с нулевыми продажами)
        - Товары с нулевыми продажами получают **класс C**
        - 💰 **Загрузка цен** из колонки 12 "Посл. закупка"
        - Принцип Парето рассчитывается только для товаров с продажами > 0
        """)
        
        with st.expander("📋 Требуемая структура файла с ценами"):
            st.markdown("""
            **Структура Excel файла:**
            - Колонка 1: Номенклатура товара
            - Колонка 2: Подкатегория (опционально)
            - Колонка 3: Категория
            - Колонка 4: Годовые продажи
            - **Колонка 12: "Посл. закупка" (ЦЕНЫ)** 💰
            
            **Важно:** Цены должны быть в 12-й колонке для корректных денежных расчетов дефицита!
            """)
        
        abc_file = st.file_uploader(
            "Выберите файл для ABC анализа",
            type=['xlsx', 'xls'],
            help="Файл должен содержать: Наименование, Категория, Объем продаж, Цены в колонке 12"
        )
        
        if abc_file is not None:
            with st.spinner("Загрузка и анализ ABC данных с ценами..."):
                # Загружаем файл с обновленным методом
                load_result = system.load_abc_file(abc_file)
                
                if load_result['success']:
                    st.success(f"✅ Файл загружен: {load_result['total_items']} товаров")
                    
                    # Показываем детали загрузки
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Всего товаров", load_result['total_items'])
                    with col2:
                        st.metric("С ценами", load_result.get('items_with_price', 0))
                    with col3:
                        st.metric("Средняя цена", f"{load_result.get('average_price', 0):,.0f} ₸")
                    with col4:
                        st.metric("Категорий", load_result['categories'])
                    
                    # Показываем информацию о ценах
                    if load_result.get('price_data_loaded'):
                        st.info(f"""
                        💰 **Статистика цен:**
                        - С ценой > 0: {load_result['items_with_price']} товаров
                        - Без цены: {load_result['items_without_price']} товаров
                        - Средняя цена: {load_result['average_price']:,.2f} ₸
                        - Денежные расчеты: **Включены** ✅
                        """)
                    
                    # Выполняем ABC анализ
                    analysis_result = system.perform_abc_analysis()
                    
                    if analysis_result['success']:
                        st.success("✅ ABC анализ завершен с загрузкой цен!")
                        st.rerun()
                    else:
                        st.error(f"❌ {analysis_result['error']}")
                else:
                    st.error(f"❌ {load_result['error']}")
# Дополнительная функция для создания специализированных визуализаций
def create_zero_sales_visualization(abc_data):
    """Создание визуализации для товаров с нулевыми продажами"""
    
    zero_sales_items = abc_data[abc_data['annual_sales'] == 0]
    
    if len(zero_sales_items) == 0:
        return None
    
    # Распределение по категориям
    zero_by_category = zero_sales_items['category'].value_counts().head(15)
    
    fig = px.bar(
        x=zero_by_category.values,
        y=zero_by_category.index,
        orientation='h',
        title=f'Товары с нулевыми продажами по категориям (всего: {len(zero_sales_items)})',
        labels={'x': 'Количество товаров', 'y': 'Категория'},
        color=zero_by_category.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        height=600,
        showlegend=False
    )
    
    return fig

def add_ads_fix_button_to_streamlit(system):
        """
        Добавьте этот код на страницу расчета ADS в Streamlit
        """
        if system.calculated_ads is not None:
            zero_ads_count = (system.calculated_ads['ads'] == 0).sum()
            
            if zero_ads_count > 0:
                st.warning(f"⚠️ Найдено {zero_ads_count} товаров с ADS = 0")
                
                if st.button("🔧 Исправить нулевые ADS средними по категориям"):
                    # Добавляем метод если его нет
                    if not hasattr(system, 'fix_zero_ads_with_category_average'):
                        apply_ads_category_fix_to_system(system)
                    
                    # Применяем исправление
                    with st.spinner("Исправление нулевых ADS..."):
                        success = system.fix_zero_ads_with_category_average()
                        
                        if success:
                            st.success("✅ ADS исправлены!")
                            st.rerun()  # Обновляем страницу
                        else:
                            st.error("❌ Не удалось исправить ADS")

def ads_calculation_page_updated(system):
    st.header("📊 Расчет ADS с ценами")
    
    try:
        from integration_patch import add_multiple_files_interface_to_existing
        
        if add_multiple_files_interface_to_existing():
            return  # Если используются множественные файлы, выходим
    except Exception as e:
        st.error(f"Ошибка загрузки множественных файлов: {e}")

    st.markdown("""
    **🔢 ФОРМУЛА ADS С ЦЕНАМИ:**
    - **Номенклатура:** Читается из колонки B 
    - **Цены:** Читаются из колонки 12 "Посл. закупка" 💰
    - **Диапазон данных:** M4:AB4 до последнего товара
    - **Формула:** ADS = (среднее значение от M4:AB4) / 30
    - **Исключения:** Последняя строка автоматически исключается
    """)
    
    # Показываем структуру файла
    with st.expander("📋 Требуемая структура Excel файла с ценами"):
        st.markdown("""
        ```
        Колонка A: Коды товаров (не используется)
        Колонка B: НОМЕНКЛАТУРА ТОВАРОВ (основная)
        Колонка 12: ЦЕНЫ "Посл. закупка" 💰
        Колонки M-AB: Месячные данные продаж
        Строка 4: Начало данных
        Последняя строка: Исключается автоматически
        ```
        """)
    
    status = system.get_system_status()
    
    if status['sales_analysis']['ads_calculated']:
        # ADS уже рассчитан
        st.success("✅ ADS с ценами рассчитан!")
        
        ads_data = system.calculated_ads
        
        # НОВОЕ: Проверяем наличие цен в ADS данных
        has_prices = 'last_purchase_price' in ads_data.columns
        
        if has_prices:
            items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
            items_without_price = len(ads_data[ads_data['last_purchase_price'] == 0])
            avg_price = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
            
            # Показываем информацию о ценах
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров", len(ads_data))
            with col2:
                st.metric("С ценами", f"{items_with_price}/{len(ads_data)}")
            with col3:
                st.metric("Общий ADS", f"{ads_data['ads'].sum():.2f}")
            with col4:
                st.metric("Средняя цена", f"{avg_price:,.2f} ₸" if not pd.isna(avg_price) else "0 ₸")
            
            # Успешное сообщение о ценах
            price_coverage = (items_with_price / len(ads_data)) * 100
            st.success(f"""
            💰 **Цены успешно загружены из ADS файла:**
            - Товаров с ценой > 0: {items_with_price} ({price_coverage:.1f}%)
            - Товаров без цены: {items_without_price} ({100-price_coverage:.1f}%)
            - Средняя цена: {avg_price:,.2f} ₸
            - Денежные расчеты дефицита: **Доступны** ✅
            """)
            
            # Топ товары с ценами
            st.subheader("🏆 Топ товары по ADS (с ценами)")
            top_ads_with_prices = ads_data[ads_data['last_purchase_price'] > 0].nlargest(10, 'ads')
            
            if not top_ads_with_prices.empty:
                # Добавляем колонку стоимости месячных продаж
                top_ads_with_prices = top_ads_with_prices.copy()
                top_ads_with_prices['monthly_value'] = top_ads_with_prices['ads'] * top_ads_with_prices['last_purchase_price'] * 30
                
                fig_ads_money = px.scatter(
                    top_ads_with_prices,
                    x='ads',
                    y='last_purchase_price',
                    size='monthly_value',
                    hover_name='номенклатура',
                    title='ADS vs Цена (размер = месячная стоимость продаж)',
                    labels={
                        'ads': 'ADS (среднедневные продажи)',
                        'last_purchase_price': 'Цена (₸)',
                        'monthly_value': 'Месячная стоимость (₸)'
                    }
                )
                st.plotly_chart(fig_ads_money, use_container_width=True)
        else:
            # Цены не загружены
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров", len(ads_data))
            with col2:
                st.metric("Общий ADS", f"{ads_data['ads'].sum():.2f}")
            with col3:
                st.metric("Средний ADS", f"{ads_data['ads'].mean():.4f}")
            with col4:
                st.metric("Цены", "Не загружены")
            
            st.warning("""
            💰 **Цены не найдены в ADS файле:**
            - Колонка 12 "Посл. закупка" отсутствует или пуста
            - Денежные расчеты дефицита будут недоступны
            - Перезагрузите файл с ценами в колонке 12
            """)
        
        # Остальной код остается без изменений...
        
    else:
        # ADS не рассчитан
        st.info("Загрузите файл с данными продаж для расчета ADS с ценами")
        
        st.success("""
        ✅ **Обновленная обработка данных:**
        
        - **Номенклатура** читается из колонки B
        - **Цены** читаются из колонки 12 "Посл. закупка" 💰
        - **ADS** рассчитывается по формуле: (среднее M:AB) / 30
        - **Денежные расчеты** автоматически включаются при наличии цен
        """)
        
        st.warning("""
        ⚠️ **ВАЖНО: Структура файла с ценами!**
        
        - Номенклатура в **колонке B**
        - **Цены в колонке 12** "Посл. закупка" 💰
        - Данные продаж в колонках M-AB
        - Данные начинаются с 4-й строки
        """)
        
        sales_file = st.file_uploader(
            "Выберите файл продаж с ценами",
            type=['xlsx', 'xls'],
            help="Файл должен содержать номенклатуру в колонке B, цены в колонке 12, и данные продаж в колонках M-AB",
            key="sales_file_with_prices"
        )
        
        if sales_file is not None:
            with st.spinner("Обработка файла ADS с ценами..."):
                # Используем обновленный метод
                load_result = system.load_sales_file_updated(sales_file)
                
                if load_result['success']:
                    st.success(f"✅ ADS с ценами рассчитан для {load_result['total_items']} товаров")
                    
                    # Показываем детали результата
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Товаров", load_result['total_items'])
                    with col2:
                        st.metric("С ценами", f"{load_result.get('items_with_price', 0)}/{load_result['total_items']}")
                    with col3:
                        st.metric("Общий ADS", f"{load_result['total_ads']:.2f}")
                    with col4:
                        st.metric("Средняя цена", f"{load_result.get('average_price', 0):,.2f} ₸")
                    
                    # Показываем информацию о ценах и стоимости
                    if load_result.get('price_data_loaded'):
                        st.success(f"""
                        💰 **Цены успешно загружены из колонки 12:**
                        - С ценой > 0: {load_result['items_with_price']} товаров ({load_result['price_coverage_percentage']:.1f}%)
                        - Без цены: {load_result['items_without_price']} товаров
                        - Средняя цена: {load_result['average_price']:,.2f} ₸
                        - Общая стоимость запасов (месяц): {load_result['total_inventory_value']:,.0f} ₸
                        - Денежные расчеты: **Включены** ✅
                        """)
                    else:
                        st.warning("💰 Цены не найдены в колонке 12 или все равны нулю")
                    
                    # Информация о обработке
                    st.info(f"""
                    **Результаты обработки:**
                    - Источник цен: {load_result.get('price_column', 'Колонка 12')}
                    - Формула: {load_result['formula']}
                    - Диапазон: {load_result['range_used']}
                    - Последняя строка исключена: {'✅' if load_result['last_row_excluded'] else '❌'}
                    - С положительным ADS: {load_result['items_with_positive_ads']} товаров
                    """)
                    
                    st.rerun()
                else:
                    st.error(f"❌ {load_result['error']}")

def show_ads_comparison(old_ads_data, new_ads_data):
    """Функция для сравнения старых и новых результатов ADS"""
    
    st.subheader("📊 Сравнение старой и новой логики ADS")
    
    if old_ads_data is not None and new_ads_data is not None:
        # Объединяем данные для сравнения
        comparison_df = pd.merge(
            old_ads_data[['номенклатура', 'ads']].rename(columns={'ads': 'ads_old'}),
            new_ads_data[['номенклатура', 'ads']].rename(columns={'ads': 'ads_new'}),
            on='номенклатура',
            how='outer'
        ).fillna(0)
        
        # Рассчитываем разности
        comparison_df['ads_diff'] = comparison_df['ads_new'] - comparison_df['ads_old']
        comparison_df['ads_diff_percent'] = np.where(
            comparison_df['ads_old'] > 0,
            (comparison_df['ads_diff'] / comparison_df['ads_old'] * 100),
            0
        )
        
        # Статистика сравнения
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            correlation = comparison_df[['ads_old', 'ads_new']].corr().iloc[0, 1]
            st.metric("Корреляция", f"{correlation:.3f}")
        
        with col2:
            mean_diff = comparison_df['ads_diff'].mean()
            st.metric("Средняя разность", f"{mean_diff:.4f}")
        
        with col3:
            mean_diff_percent = comparison_df['ads_diff_percent'].mean()
            st.metric("Средняя разность %", f"{mean_diff_percent:.1f}%")
        
        with col4:
            items_changed = len(comparison_df[abs(comparison_df['ads_diff_percent']) > 5])
            st.metric("Изменения >5%", items_changed)
        
        # График сравнения
        fig_comparison = px.scatter(
            comparison_df,
            x='ads_old',
            y='ads_new',
            title='Сравнение старой и новой логики ADS',
            labels={'ads_old': 'ADS (старая логика)', 'ads_new': 'ADS (новая логика)'},
            hover_data=['номенклатура', 'ads_diff_percent']
        )
        
        # Добавляем линию y=x для идеального соответствия
        min_val = min(comparison_df['ads_old'].min(), comparison_df['ads_new'].min())
        max_val = max(comparison_df['ads_old'].max(), comparison_df['ads_new'].max())
        fig_comparison.add_shape(
            type="line",
            x0=min_val, y0=min_val,
            x1=max_val, y1=max_val,
            line=dict(color="red", dash="dash")
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Таблица с наибольшими изменениями
        st.subheader("📋 Товары с наибольшими изменениями")
        
        top_changes = comparison_df.reindex(
            comparison_df['ads_diff_percent'].abs().sort_values(ascending=False).index
        ).head(10)
        
        st.dataframe(
            top_changes[['номенклатура', 'ads_old', 'ads_new', 'ads_diff', 'ads_diff_percent']],
            use_container_width=True
        )
    
    else:
        st.warning("Недостаточно данных для сравнения")

def add_json_export_section(system):
    """Добавить секцию для работы с JSON данными"""
    
    st.subheader("📄 Работа с JSON данными")
    
    if hasattr(system, '_json_data') and 'ads' in system._json_data:
        
        # Информация о JSON
        json_data = system._json_data['ads']
        metadata = json_data.get('metadata', {})
        
        st.info(f"""
        **JSON статистика:**
        - Товаров: {metadata.get('total_items', 0)}
        - Метод: {metadata.get('calculation_method', 'неизвестно')}
        - Формула: {metadata.get('formula', 'неизвестно')}
        - Обработка: {metadata.get('file_processed_at', 'неизвестно')}
        """)
        
        # Кнопки для работы с JSON
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️ Просмотр JSON"):
                st.json(json_data)
        
        with col2:
            if st.button("💾 Сохранить JSON"):
                try:
                    filename = system.save_ads_json_to_file()
                    st.success(f"✅ Сохранено: {filename}")
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")
        
        with col3:
            # Создаем JSON для скачивания
            json_str = system.get_ads_json_data()
            st.download_button(
                label="⬇️ Скачать JSON",
                data=json_str.encode('utf-8'),
                file_name=f"ads_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        
        # API интеграция (пример)
        with st.expander("🔌 API интеграция"):
            st.markdown("""
            **Пример использования JSON в API:**
            
            ```python
            import requests
            import json
            
            # Получение JSON данных
            json_data = system.get_ads_json_data()
            data = json.loads(json_data)
            
            # Отправка в API
            response = requests.post(
                'https://api.company.com/ads',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            ```
            """)
    
    else:
        st.warning("JSON данные недоступны. Сначала обработайте файл ADS.")
def min_stock_calculation_page(system):
    """Страница расчета минимальных запасов"""
    st.header("📋 Расчет минимальных запасов")
    
    st.markdown("""
    **Минимальные запасы** рассчитываются по формуле:
    
    **MIN = ADS × (дни запаса + транзитное время)**
    """)
    
    status = system.get_system_status()
    
    if not status['sales_analysis']['ads_calculated']:
        st.warning("⚠️ Сначала необходимо рассчитать ADS")
        if st.button("📊 Перейти к расчету ADS"):
            st.switch_page("ADS расчет")
        return
    
    # Параметры расчета
    st.subheader("⚙️ Параметры расчета")
    
    col1, col2 = st.columns(2)
    with col1:
        ip_days = st.slider(
            "Транзитное время (IP), дни",
            min_value=1,
            max_value=30,
            value=7,
            help="Время доставки товара от заказа до поступления на склад"
        )
    
    with col2:
        stock_days = st.slider(
            "Дни запаса",
            min_value=5,
            max_value=60,
            value=30,
            help="На сколько дней должен хватать минимальный запас"
        )
    
    if status['min_stock_analysis']['calculated']:
        current_params = system.calculated_min_stock.iloc[0]
        if (current_params['ip_target_days'] != ip_days or 
            current_params['min_stock_days'] != stock_days):
            st.info("Параметры изменены. Нажмите кнопку для пересчета.")
    
    # Кнопка расчета
    if st.button("📋 Рассчитать минимальные запасы"):
        with st.spinner("Расчет минимальных запасов..."):
            calc_result = system.calculate_min_stock(ip_days, stock_days)
            
            if calc_result['success']:
                st.success("✅ Минимальные запасы рассчитаны!")
                st.rerun()
            else:
                st.error(f"❌ {calc_result['error']}")
    
    # Показываем результаты если есть
    if status['min_stock_analysis']['calculated']:
        min_stock_data = system.calculated_min_stock
        
        st.subheader("📊 Результаты расчета")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Товаров", len(min_stock_data))
        with col2:
            st.metric("Общий MIN запас", f"{min_stock_data['min_stock_total'].sum():,.0f}")
        with col3:
            st.metric("Транзитное потребление", f"{min_stock_data['transit_consumption'].sum():,.0f}")
        with col4:
            st.metric("Базовый запас", f"{min_stock_data['min_stock_base'].sum():,.0f}")
        
        # Топ товары по минимальному запасу
        st.subheader("📈 Топ товары по минимальному запасу")
        top_min_stock = min_stock_data.nlargest(10, 'min_stock_total')
        
        fig_min = px.bar(
            top_min_stock,
            x='min_stock_total',
            y='номенклатура',
            orientation='h',
            title='Топ-10 товаров по минимальному запасу'
        )
        st.plotly_chart(fig_min, use_container_width=True)
        
        # Детальная таблица
        with st.expander("📋 Детальные расчеты"):
            display_cols = ['номенклатура', 'ads', 'min_stock_base', 'transit_consumption', 'min_stock_total', 'priority']
            st.dataframe(min_stock_data[display_cols], use_container_width=True)

def stock_comparison_page(system):
    """ОБНОВЛЕННАЯ страница сравнения остатков с денежными показателями"""
    st.header("⚖️ Сравнение остатков с минимальными запасами")
    
    status = system.get_system_status()
    
    if not status['min_stock_analysis']['calculated']:
        st.warning("⚠️ Сначала необходимо рассчитать минимальные запасы")
        if st.button("📋 Перейти к расчету MIN запасов"):
            st.switch_page("MIN запасы")
        return
    
    # Загрузка файла остатков (код остается без изменений)
    if not status['stock_analysis']['loaded']:
        st.info("Загрузите файл текущих остатков (например: остатки.xlsx)")
        
        stock_file = st.file_uploader(
            "Выберите файл остатков",
            type=['xlsx', 'xls'],
            help="Файл должен содержать текущие остатки товаров на складах"
        )
        
        if stock_file is not None:
            with st.spinner("Загрузка данных остатков..."):
                load_result = system.load_current_stock_file(stock_file)
                
                if load_result['success']:
                    st.success(f"✅ Остатки загружены: {load_result['total_items']} товаров")
                    st.rerun()
                else:
                    st.error(f"❌ {load_result['error']}")
        return
    
    # Выполнение сравнения
    if not status['stock_analysis']['compared']:
        if st.button("▶️ Выполнить сравнение остатков"):
            with st.spinner("Сравнение остатков с расчетом денежного выражения..."):
                comparison_result = system.compare_stock_vs_min()
                
                if comparison_result['success']:
                    st.success("✅ Сравнение завершено с денежными расчетами!")
                    st.rerun()
                else:
                    st.error(f"❌ {comparison_result['error']}")
        return
    
    # Показываем результаты сравнения с денежными показателями
    comparison_data = system.stock_comparison
    
    st.subheader("📊 Результаты анализа")
    
    # ОБНОВЛЕННАЯ общая статистика с денежными показателями
    total_items = len(comparison_data)
    deficit_items = len(comparison_data[comparison_data['stock_deficit'] > 0])
    critical_items = len(comparison_data[comparison_data['status'] == 'КРИТИЧНО'])
    sufficient_items = len(comparison_data[comparison_data['status'] == 'ДОСТАТОЧНО'])
    
    # Денежные показатели
    has_money_data = 'stock_deficit_money' in comparison_data.columns
    total_deficit_money = comparison_data['stock_deficit_money'].sum() if has_money_data else 0
    total_order_money = comparison_data['recommended_order_money'].sum() if has_money_data else 0
    items_with_price = len(comparison_data[comparison_data['last_purchase_price'] > 0]) if 'last_purchase_price' in comparison_data.columns else 0
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("С дефицитом", f"{deficit_items} ({deficit_items/total_items*100:.1f}%)")
    with col3:
        st.metric("Критично", f"{critical_items} ({critical_items/total_items*100:.1f}%)")
    with col4:
        total_deficit = comparison_data['stock_deficit'].sum()
        st.metric("Общий дефицит (шт)", f"{total_deficit:,.0f}")
    
    # НОВЫЕ денежные метрики
    if has_money_data and total_deficit_money > 0:
        st.subheader("💰 Денежное выражение дефицита")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Дефицит в деньгах", f"{total_deficit_money:,.0f} ₸")
        with col2:
            st.metric("Заказ в деньгах", f"{total_order_money:,.0f} ₸")
        with col3:
            st.metric("Товаров с ценами", f"{items_with_price}/{total_items}")
        with col4:
            price_coverage = (items_with_price / total_items * 100) if total_items > 0 else 0
            st.metric("Покрытие ценами", f"{price_coverage:.1f}%")
        
        # Топ товары по денежному дефициту
        if deficit_items > 0:
            st.subheader("💸 Топ товары по денежному дефициту")
            
            top_deficit_money = comparison_data[
                comparison_data['stock_deficit_money'] > 0
            ].nlargest(10, 'stock_deficit_money')
            
            if not top_deficit_money.empty:
                fig_money_deficit = px.bar(
                    top_deficit_money,
                    x='stock_deficit_money',
                    y='номенклатура',
                    orientation='h',
                    title='Топ-10 товаров по денежному дефициту',
                    labels={'stock_deficit_money': 'Дефицит (₸)', 'номенклатура': 'Товар'},
                    color='order_priority',
                    color_discrete_map={
                        'СРОЧНО': '#ff0000',
                        'ВЫСОКИЙ': '#ff8800',
                        'СРЕДНИЙ': '#ffcc00'
                    }
                )
                fig_money_deficit.update_layout(height=600)
                st.plotly_chart(fig_money_deficit, use_container_width=True)
    
    elif has_money_data:
        st.info("💰 Денежные расчеты доступны, но дефицита в денежном выражении нет")
    else:
        st.warning("""
        💰 **Денежные расчеты недоступны**
        
        Возможные причины:
        - Не загружены цены из ABC файла
        - Колонка 'Посл. закупка' отсутствует или пуста
        - Все цены равны нулю
        
        Для включения денежных расчетов перезагрузите ABC файл с ценами в колонке 12.
        """)
    
    # Остальные визуализации (обычные)
    visualizations = system.create_visualizations()
    
    if 'stock_status' in visualizations:
        st.plotly_chart(visualizations['stock_status'], use_container_width=True)
    
    if 'deficit_analysis' in visualizations:
        st.plotly_chart(visualizations['deficit_analysis'], use_container_width=True)
    
    # ОБНОВЛЕННЫЕ детальные результаты с денежными колонками
    st.subheader("📋 Детальные результаты")
    
    # Фильтры (остаются без изменений)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Фильтр по статусу",
            options=['Все', 'КРИТИЧНО', 'НЕДОСТАТОК', 'ДОСТАТОЧНО']
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Фильтр по приоритету",
            options=['Все', 'СРОЧНО', 'ВЫСОКИЙ', 'СРЕДНИЙ', 'НЕ ТРЕБУЕТСЯ']
        )
    
    with col3:
        # Переключатель для фильтра по деньгам или штукам
        filter_by_money = st.checkbox("Фильтр по денежному дефициту", value=has_money_data)
        
        if filter_by_money and has_money_data:
            min_deficit = st.number_input(
                "Минимальный дефицит (₸)",
                min_value=0,
                value=0,
                help="Показать товары с денежным дефицитом больше указанного"
            )
        else:
            min_deficit = st.number_input(
                "Минимальный дефицит (шт)",
                min_value=0,
                value=0,
                help="Показать товары с дефицитом больше указанного количества"
            )
    
    # Применяем фильтры
    filtered_data = comparison_data.copy()
    
    if status_filter != 'Все':
        filtered_data = filtered_data[filtered_data['status'] == status_filter]
    
    if priority_filter != 'Все':
        filtered_data = filtered_data[filtered_data['order_priority'] == priority_filter]
    
    if min_deficit > 0:
        if filter_by_money and has_money_data:
            filtered_data = filtered_data[filtered_data['stock_deficit_money'] >= min_deficit]
        else:
            filtered_data = filtered_data[filtered_data['stock_deficit'] >= min_deficit]
    
    # ОБНОВЛЕННЫЕ колонки для отображения с денежными данными
    if has_money_data:
        display_columns = [
            'номенклатура', 'ads', 'min_stock_total', 'total_current_stock', 
            'stock_deficit', 'stock_deficit_money', 'current_stock_days', 
            'status', 'order_priority', 'recommended_order', 'recommended_order_money',
            'last_purchase_price'
        ]
        
        column_config = {
            'номенклатура': 'Товар',
            'ads': 'ADS',
            'min_stock_total': 'MIN запас',
            'total_current_stock': 'Текущий остаток',
            'stock_deficit': 'Дефицит (шт)',
            'stock_deficit_money': st.column_config.NumberColumn(
                'Дефицит (₸)',
                format="%.0f ₸"
            ),
            'current_stock_days': 'Дни остатка',
            'status': 'Статус',
            'order_priority': 'Приоритет',
            'recommended_order': 'Заказ (шт)',
            'recommended_order_money': st.column_config.NumberColumn(
                'Заказ (₸)',
                format="%.0f ₸"
            ),
            'last_purchase_price': st.column_config.NumberColumn(
                'Цена',
                format="%.2f ₸"
            )
        }
    else:
        display_columns = [
            'номенклатура', 'ads', 'min_stock_total', 'total_current_stock', 
            'stock_deficit', 'current_stock_days', 'status', 'order_priority', 'recommended_order'
        ]
        
        column_config = {
            'номенклатура': 'Товар',
            'ads': 'ADS',
            'min_stock_total': 'MIN запас',
            'total_current_stock': 'Текущий остаток',
            'stock_deficit': 'Дефицит',
            'current_stock_days': 'Дни остатка',
            'status': 'Статус',
            'order_priority': 'Приоритет',
            'recommended_order': 'Рекомендуемый заказ'
        }
    
    # Отображаем отфильтрованные данные
    st.dataframe(
        filtered_data[display_columns], 
        use_container_width=True,
        column_config=column_config
    )
    
    if len(filtered_data) != len(comparison_data):
        st.info(f"Показано {len(filtered_data)} из {len(comparison_data)} товаров")
    
    # НОВАЯ сводка по денежным показателям для отфильтрованных данных
    if has_money_data and len(filtered_data) > 0:
        with st.expander("💰 Денежная сводка по отфильтрованным товарам"):
            filtered_deficit_money = filtered_data['stock_deficit_money'].sum()
            filtered_order_money = filtered_data['recommended_order_money'].sum()
            filtered_items_with_price = len(filtered_data[filtered_data['last_purchase_price'] > 0])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Дефицит (₸)", f"{filtered_deficit_money:,.0f}")
            with col2:
                st.metric("К заказу (₸)", f"{filtered_order_money:,.0f}")
            with col3:
                st.metric("С ценами", f"{filtered_items_with_price}/{len(filtered_data)}")
def export_page(system):
    """ОБНОВЛЕННАЯ страница экспорта результатов с денежными показателями"""
    st.header("📤 Экспорт результатов")
    
    status = system.get_system_status()
    
    if not status['overall']['ready_for_export']:
        st.warning("⚠️ Недостаточно данных для экспорта. Выполните хотя бы расчет ADS и один из анализов.")
        return
    
    # Общий отчет
    st.subheader("📊 Итоговый отчет")
    
    summary = system.get_summary_report()
    
    # Отображаем сводку с денежными показателями
    if 'abc_analysis' in summary:
        abc = summary['abc_analysis']
        st.write(f"**ABC анализ**: {abc['total_items']} товаров, {abc['categories_analyzed']} категорий")
        st.write(f"- A товары: {abc['distribution']['A_items']} ({abc['distribution']['A_percentage']:.1f}%)")
        st.write(f"- B товары: {abc['distribution']['B_items']} ({abc['distribution']['B_percentage']:.1f}%)")
        st.write(f"- C товары: {abc['distribution']['C_items']} ({abc['distribution']['C_percentage']:.1f}%)")
        
        # НОВОЕ: Информация о ценах
        if 'price_info' in abc:
            price_info = abc['price_info']
            st.write(f"💰 **Ценовая информация:**")
            st.write(f"- Товаров с ценами: {price_info['items_with_price']} ({price_info['price_coverage_percentage']:.1f}%)")
            st.write(f"- Средняя цена: {price_info['average_price']:,.2f} ₸")
            st.write(f"- Общая стоимость запасов: {price_info['total_inventory_value']:,.0f} ₸")
    
    if 'ads_analysis' in summary:
        ads = summary['ads_analysis']
        st.write(f"**ADS анализ**: {ads['total_items']} товаров, общий ADS: {ads['total_ads']:.1f}")
        st.write(f"- Топ товар: {ads['top_seller']['item']} (ADS: {ads['top_seller']['ads_value']:.2f})")

    if 'subcategory_analysis' in summary:
        subcat = summary['subcategory_analysis']
        st.write(f"**ABC анализ подкатегорий**: {subcat['total_subcategories']} подкатегорий в {subcat['categories_with_subcategories']} категориях")
        st.write(f"- Эффективных подкатегорий: {subcat['efficient_subcategories']} ({subcat['efficiency_percentage']:.1f}%)")

    if 'min_stock_analysis' in summary:
        min_stock = summary['min_stock_analysis']
        st.write(f"**Минимальные запасы**: {min_stock['total_items']} товаров")
        st.write(f"- Общий MIN запас: {min_stock['total_min_stock']:,.0f} шт")
        st.write(f"- Параметры: {min_stock['parameters']['stock_days']} дней + {min_stock['parameters']['ip_days']} дней IP")
        
        # НОВОЕ: Денежные показатели минимальных запасов
        if 'money_metrics' in min_stock:
            money_metrics = min_stock['money_metrics']
            st.write(f"💰 **Минимальные запасы в деньгах**: {money_metrics['total_min_stock_money']:,.0f} ₸")
            st.write(f"- Товаров с ценами: {money_metrics['items_with_price']}")
    
    if 'stock_comparison' in summary:
        comparison = summary['stock_comparison']
        st.write(f"**Сравнение остатков**: {comparison['total_items']} товаров")
        st.write(f"- С дефицитом: {comparison['deficit_items']} ({comparison['deficit_percentage']:.1f}%)")
        st.write(f"- Критично: {comparison['critical_items']} ({comparison['critical_percentage']:.1f}%)")
        st.write(f"- Рекомендуемый заказ: {comparison['total_recommended_order']:,.0f} шт")
        
        # НОВЫЕ денежные показатели
        if 'money_metrics' in comparison:
            money_metrics = comparison['money_metrics']
            st.write(f"💰 **Денежное выражение дефицита:**")
            st.write(f"- Общий дефицит: {money_metrics['total_deficit_money']:,.0f} ₸")
            st.write(f"- К заказу: {money_metrics['total_recommended_order_money']:,.0f} ₸")
            st.write(f"- Покрытие ценами: {money_metrics['price_coverage_percentage']:.1f}%")
            
            # Топ дефицитные товары по деньгам
            if 'top_deficit_money_items' in money_metrics:
                st.write(f"📊 **Топ-3 товара по денежному дефициту:**")
                for i, item in enumerate(money_metrics['top_deficit_money_items'][:3], 1):
                    st.write(f"   {i}. {item['item']}: {item['deficit_money']:,.0f} ₸ ({item['deficit_quantity']:.0f} шт × {item['price']:.2f} ₸)")
    
    # Рекомендации
    st.subheader("💡 Рекомендации")
    recommendations = system.get_recommendations()
    
    # ДОПОЛНЯЕМ рекомендациями по денежным показателям
    if 'stock_comparison' in summary and 'money_metrics' in summary['stock_comparison']:
        money_metrics = summary['stock_comparison']['money_metrics']
        
        if money_metrics['total_deficit_money'] > 1000000:  # > 1 млн
            recommendations.insert(0, f"💰 Критический денежный дефицит: {money_metrics['total_deficit_money']:,.0f} ₸. Требуется срочное пополнение бюджета закупок.")
        
        if money_metrics['price_coverage_percentage'] < 80:
            recommendations.append(f"💰 Низкое покрытие ценами ({money_metrics['price_coverage_percentage']:.1f}%). Обновите прайс-лист для точных денежных расчетов.")
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
    
    # ОБНОВЛЕННЫЙ экспорт в Excel
    st.subheader("📥 Скачать Excel файл")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Полный отчет с ценами", use_container_width=True):
            with st.spinner("Создание Excel файла с денежными расчетами..."):
                try:
                    excel_buffer = system.export_all_results()
                    
                    st.download_button(
                        label="💾 Скачать Excel с денежными данными",
                        data=excel_buffer,
                        file_name=f"inventory_analysis_money_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success("✅ Excel файл с денежными расчетами готов!")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка создания файла: {str(e)}")
    
    with col2:
        # ОБНОВЛЕННАЯ информация о содержимом файла
        st.info("""
        **Содержимое Excel файла:**
        - Общий статус системы
        - ABC анализ с ценами 💰
        - ADS расчеты с ценами 💰
        - Минимальные запасы (шт + ₸) 💰
        - Сравнение остатков (шт + ₸) 💰
        - Товары с дефицитом (шт + ₸) 💰
        - Критичные товары (шт + ₸) 💰
        - Рекомендации заказа (шт + ₸) 💰
        - **Денежная сводка** 💰
        - Подкатегории (если есть)
        
        💰 = Новые денежные расчеты
        """)
        
        if status['subcategory_analysis']['analyzed']:
            if st.button("🔤📊 Отчет подкатегорий", use_container_width=True):
                with st.spinner("Создание отчета подкатегорий..."):
                    try:
                        excel_buffer = system.export_subcategory_results()
                        
                        if excel_buffer:
                            st.download_button(
                                label="💾 Скачать отчет подкатегорий",
                                data=excel_buffer,
                                file_name=f"subcategory_abc_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            
                            st.success("✅ Отчет подкатегорий готов!")
                        else:
                            st.error("❌ Ошибка создания отчета подкатегорий")
                            
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
        else:
            st.info("Выполните анализ подкатегорий для экспорта")
    
    with col3:
        # Предварительный просмотр денежных данных
        if 'stock_comparison' in summary and 'money_metrics' in summary['stock_comparison']:
            money_metrics = summary['stock_comparison']['money_metrics']
            
            st.metric("💰 Дефицит", f"{money_metrics['total_deficit_money']:,.0f} ₸")
            st.metric("💰 К заказу", f"{money_metrics['total_recommended_order_money']:,.0f} ₸")
            st.metric("📊 Покрытие", f"{money_metrics['price_coverage_percentage']:.1f}%")
        else:
            st.info("""
            **Для денежных расчетов:**
            1. Загрузите ABC файл с ценами
            2. Выполните сравнение остатков
            3. Получите отчет с денежными данными
            """)

def create_money_visualizations(system) -> Dict:
    """
    Создание специальных визуализаций для денежных показателей
    """
    visualizations = {}
    
    if (system.stock_comparison is not None and 
        'stock_deficit_money' in system.stock_comparison.columns):
        
        comparison_data = system.stock_comparison
        
        # 1. График денежного дефицита vs количественного
        deficit_data = comparison_data[comparison_data['stock_deficit'] > 0].copy()
        
        if not deficit_data.empty and len(deficit_data) > 5:
            fig_money_vs_quantity = px.scatter(
                deficit_data.head(50),  # Топ-50 для читаемости
                x='stock_deficit',
                y='stock_deficit_money',
                hover_name='номенклатура',
                title='Денежный дефицит vs Количественный дефицит',
                labels={
                    'stock_deficit': 'Дефицит (штук)',
                    'stock_deficit_money': 'Дефицит (₸)'
                },
                color='order_priority',
                size='last_purchase_price',
                color_discrete_map={
                    'СРОЧНО': '#ff0000',
                    'ВЫСОКИЙ': '#ff8800',
                    'СРЕДНИЙ': '#ffcc00'
                }
            )
            visualizations['money_vs_quantity'] = fig_money_vs_quantity
        
        # 2. Топ товары по денежному дефициту (пирамида)
        top_money_deficit = deficit_data.nlargest(15, 'stock_deficit_money')
        
        if not top_money_deficit.empty:
            fig_money_pyramid = px.funnel(
                top_money_deficit,
                y='номенклатура',
                x='stock_deficit_money',
                title='Пирамида денежного дефицита (Топ-15)',
                labels={'stock_deficit_money': 'Дефицит (₸)'}
            )
            visualizations['money_pyramid'] = fig_money_pyramid
        
        # 3. Сравнение текущих остатков и минимальных запасов в деньгах
        money_comparison_data = comparison_data[
            (comparison_data['last_purchase_price'] > 0) & 
            (comparison_data['min_stock_money'] > 0)
        ].head(20)
        
        if not money_comparison_data.empty:
            fig_money_comparison = go.Figure()
            
            # Текущие остатки в деньгах
            fig_money_comparison.add_trace(go.Bar(
                name='Текущий остаток (₸)',
                x=money_comparison_data['номенклатура'],
                y=money_comparison_data['current_stock_money'],
                marker_color='lightblue'
            ))
            
            # Минимальные запасы в деньгах
            fig_money_comparison.add_trace(go.Bar(
                name='Минимальный запас (₸)',
                x=money_comparison_data['номенклатура'],
                y=money_comparison_data['min_stock_money'],
                marker_color='orange'
            ))
            
            fig_money_comparison.update_layout(
                title='Сравнение остатков и минимумов в денежном выражении',
                xaxis_title='Товары',
                yaxis_title='Стоимость (₸)',
                barmode='group',
                xaxis_tickangle=45
            )
            
            visualizations['money_comparison'] = fig_money_comparison
        
        # 4. Круговая диаграмма распределения денежного дефицита по приоритетам
        priority_money = deficit_data.groupby('order_priority')['stock_deficit_money'].sum().reset_index()
        
        if not priority_money.empty:
            fig_priority_money = px.pie(
                priority_money,
                values='stock_deficit_money',
                names='order_priority',
                title='Распределение денежного дефицита по приоритетам',
                color_discrete_map={
                    'СРОЧНО': '#ff0000',
                    'ВЫСОКИЙ': '#ff8800',
                    'СРЕДНИЙ': '#ffcc00'
                }
            )
            visualizations['priority_money'] = fig_priority_money
    
    return visualizations

def create_money_analytics_page(system):
    """
    Создание специальной страницы для денежной аналитики
    """
    if not hasattr(system, 'stock_comparison') or system.stock_comparison is None:
        st.warning("⚠️ Сначала выполните сравнение остатков")
        return
    
    if 'stock_deficit_money' not in system.stock_comparison.columns:
        st.warning("💰 Денежные данные недоступны. Загрузите ABC файл с ценами.")
        return
    
    st.header("💰 Денежная аналитика дефицита")
    
    comparison_data = system.stock_comparison
    
    # Основные KPI
    total_deficit_money = comparison_data['stock_deficit_money'].sum()
    total_order_money = comparison_data['recommended_order_money'].sum()
    items_with_price = len(comparison_data[comparison_data['last_purchase_price'] > 0])
    avg_price = comparison_data[comparison_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💸 Общий дефицит", f"{total_deficit_money:,.0f} ₸")
    with col2:
        st.metric("🛒 К заказу", f"{total_order_money:,.0f} ₸")
    with col3:
        st.metric("🏷️ Средняя цена", f"{avg_price:,.2f} ₸" if not pd.isna(avg_price) else "0 ₸")
    with col4:
        st.metric("📊 Товаров с ценами", f"{items_with_price}/{len(comparison_data)}")
    
    # Денежные визуализации
    money_visualizations = create_money_visualizations(system)
    
    if money_visualizations:
        st.subheader("📈 Денежные визуализации")
        
        for viz_name, viz in money_visualizations.items():
            st.plotly_chart(viz, use_container_width=True, key=f"money_viz_{viz_name}")
    
    # ABC анализ дефицита по деньгам
    st.subheader("🔤 ABC анализ денежного дефицита")
    
    deficit_items = comparison_data[comparison_data['stock_deficit_money'] > 0].copy()
    
    if not deficit_items.empty:
        deficit_items = deficit_items.sort_values('stock_deficit_money', ascending=False)
        deficit_items['money_cumulative_pct'] = deficit_items['stock_deficit_money'].cumsum() / deficit_items['stock_deficit_money'].sum() * 100
        
        # Присваиваем ABC классы по денежному дефициту
        deficit_items['money_abc_class'] = deficit_items['money_cumulative_pct'].apply(
            lambda x: 'A' if x <= 80 else 'B' if x <= 95 else 'C'
        )
        
        money_abc_counts = deficit_items['money_abc_class'].value_counts()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            a_money = deficit_items[deficit_items['money_abc_class'] == 'A']['stock_deficit_money'].sum()
            st.metric("A товары (80%)", f"{money_abc_counts.get('A', 0)} | {a_money:,.0f} ₸")
        with col2:
            b_money = deficit_items[deficit_items['money_abc_class'] == 'B']['stock_deficit_money'].sum()
            st.metric("B товары (15%)", f"{money_abc_counts.get('B', 0)} | {b_money:,.0f} ₸")
        with col3:
            c_money = deficit_items[deficit_items['money_abc_class'] == 'C']['stock_deficit_money'].sum()
            st.metric("C товары (5%)", f"{money_abc_counts.get('C', 0)} | {c_money:,.0f} ₸")
        
        # Таблица A товаров по денежному дефициту
        st.subheader("🔴 A товары по денежному дефициту")
        a_items_money = deficit_items[deficit_items['money_abc_class'] == 'A'][[
            'номенклатура', 'stock_deficit_money', 'stock_deficit', 'last_purchase_price', 'order_priority'
        ]]
        st.dataframe(a_items_money, use_container_width=True)

def settings_page(system):
    """Страница настроек"""
    st.header("⚙️ Настройки системы")
    
    # Текущие параметры
    current_params = system.default_params
    
    st.subheader("📋 Параметры расчета")
    
    with st.form("settings_form"):
        ip_days = st.slider(
            "Транзитное время (IP), дни",
            min_value=1,
            max_value=30,
            value=current_params['ip_target_days'],
            help="Время доставки товара от заказа до поступления на склад"
        )
        
        stock_days = st.slider(
            "Дни запаса",
            min_value=5,
            max_value=60,
            value=current_params['min_stock_days'],
            help="На сколько дней должен хватать минимальный запас"
        )
        
        safety_factor = st.slider(
            "Коэффициент безопасности",
            min_value=1.0,
            max_value=2.0,
            value=current_params['safety_factor'],
            step=0.1,
            help="Коэффициент для увеличения заказа сверх расчетной потребности"
        )
        
        submitted = st.form_submit_button("💾 Сохранить настройки")
        
        if submitted:
            system.update_parameters(
                ip_target_days=ip_days,
                min_stock_days=stock_days,
                safety_factor=safety_factor
            )
            st.success("✅ Настройки сохранены!")
            st.rerun()
    st.subheader("🔤📊 Настройки анализа подкатегорий")
    
    status = system.get_system_status()
    subcategory_status = status.get('subcategory_analysis', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        if subcategory_status.get('analyzed', False):
            st.success("✅ Анализ подкатегорий выполнен")
            
            # Показываем краткую статистику
            if hasattr(system, 'subcategory_results') and system.subcategory_results:
                subcategory_summary = system.get_subcategory_summary_report()
                
                if subcategory_summary and 'error' not in subcategory_summary:
                    st.metric("Подкатегорий", subcategory_summary['total_subcategories'])
                    st.metric("Эффективность", f"{subcategory_summary['efficiency_percentage']:.1f}%")
        else:
            st.info("Анализ подкатегорий не выполнен")
    
    with col2:
        if st.button("🗑️ Очистить анализ подкатегорий"):
            if hasattr(system, 'subcategory_results'):
                system.subcategory_results = None
            if hasattr(system, 'subcategory_analyzer'):
                system.subcategory_analyzer.subcategory_results = None
                system.subcategory_analyzer.abc_data = None
            st.success("✅ Анализ подкатегорий очищен!")
            st.rerun()
    # Управление данными
    st.subheader("🗂️ Управление данными")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Очистить все данные", use_container_width=True):
            system.clear_all_data()
            # Также очищаем данные подкатегорий
            if hasattr(system, 'subcategory_results'):
                system.subcategory_results = None
            if hasattr(system, 'subcategory_analyzer'):
                del system.subcategory_analyzer
            st.success("✅ Все данные очищены!")
            st.rerun()
    
    with col2:
        status = system.get_system_status()
        if status['overall']['progress_percentage'] > 0:
            st.metric("Загружено данных", f"{status['overall']['progress_percentage']:.0f}%")
        else:
            st.info("Данные не загружены")
    
    with col3:
        # Диагностика системы
        if st.button("🔍 Диагностика системы"):
            st.subheader("🔧 Диагностическая информация")
            
            # Проверяем все компоненты
            components_status = {
                'ABC данные': hasattr(system, 'abc_data') and system.abc_data is not None,
                'ABC результаты': hasattr(system, 'abc_results') and system.abc_results is not None,
                'ADS данные': hasattr(system, 'calculated_ads') and system.calculated_ads is not None,
                'MIN запасы': hasattr(system, 'calculated_min_stock') and system.calculated_min_stock is not None,
                'Остатки': hasattr(system, 'stock_data') and system.stock_data is not None,
                'Сравнение остатков': hasattr(system, 'stock_comparison') and system.stock_comparison is not None,
                'Анализатор подкатегорий': hasattr(system, 'subcategory_analyzer'),
                'Результаты подкатегорий': hasattr(system, 'subcategory_results') and system.subcategory_results is not None
            }
            
            for component, status_val in components_status.items():
                status_icon = "✅" if status_val else "❌"
                st.write(f"{status_icon} {component}")
    
    # Информация о системе
    st.subheader("ℹ️ Информация о системе")
    
    st.markdown("""
    **Модульная система анализа товарных запасов v2.0**
    
    **Возможности:**
    - 🔤 ABC анализ по принципу Парето
    - 🔤📊 **ABC анализ по подкатегориям** ✨
    - 📊 Расчет ADS из исторических данных
    - 📋 Расчет минимальных запасов с учетом IP
    - ⚖️ Сравнение с текущими остатками
    - 📤 Экспорт расширенных отчетов
    
    **Поддерживаемые файлы:**
    - ABC анализ: исходникимини.xlsx
    - Расчет ADS: файлы продаж по месяцам
    - Остатки: остатки мини.xlsx
    
    **Формулы:**
    - ADS = Общие продажи / 365 дней
    - MIN = ADS × (дни запаса + транзитное время)
    - Дефицит = MIN - текущий остаток
    - Рекомендуемый заказ = Дефицит × коэффициент безопасности
    
    **Новое в v2.0:**
    - ✨ Анализ ABC по подкатегориям
    - ✨ Парето-анализ подкатегорий  
    - ✨ Рекомендации по оптимизации структуры
    - ✨ Анализ эффективности подкатегорий
    """)

def main():
    """Основная функция приложения"""
    # Инициализация системы
    system = init_system()
    # Заголовок
    st.title("📦 Модульная система анализа товарных запасов")
    st.markdown("*Пошаговый анализ с выбором типа операции*")
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("🧭 Навигация")
        
        # Показываем статус системы
        st.subheader("📊 Статус системы")
        show_system_status(system)
        
        st.markdown("---")
        
        # Меню навигации
        page = st.selectbox(
            "Выберите раздел:",
            [
                "🔤 ABC анализ",
                "📊 ADS расчет", 
                "📋 MIN запасы",
                "⚖️ Сравнение остатков",
                "🔤📊 ABC подкатегории",
                "💰 Денежная аналитика",
                "📤 Экспорт результатов",
                "⚙️ Настройки"
            ]
        )
        
        st.markdown("---")
        
        # Быстрые действия
        st.subheader("⚡ Быстрые действия")
        
        status = system.get_system_status()
        
        if not status['abc_analysis']['analyzed']:
            st.button("🔤 Начать с ABC", key="quick_abc")
        elif not status['subcategory_analysis']['analyzed']:
            st.button("📊 Анализ подкатегорий", key="quick_subcategory")
        elif not status['sales_analysis']['ads_calculated']:
            st.button("📊 Рассчитать ADS", key="quick_ads")
        elif not status['min_stock_analysis']['calculated']:
            st.button("📋 MIN запасы", key="quick_min")
        elif not status['stock_analysis']['compared']:
            st.button("⚖️ Сравнить остатки", key="quick_compare")
        else:
            st.button("📤 Экспорт", key="quick_export")
    
    # Основной контент в зависимости от выбранной страницы
    if page == "🔤 ABC анализ":
        abc_analysis_page_updated(system)
    elif page == "📊 ADS расчет":
        ads_calculation_page_updated(system)
    elif page == "📋 MIN запасы":
        min_stock_calculation_page(system)
    elif page == "⚖️ Сравнение остатков":
        stock_comparison_page(system)
    elif page == "🔤📊 ABC подкатегории":  
        subcategory_abc_analysis_page(system)
    elif page == "💰 Денежная аналитика": 
        create_money_analytics_page(system)
    elif page == "📤 Экспорт результатов":
        export_page(system)
    elif page == "⚙️ Настройки":
        settings_page(system)
    
    # Футер
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆘 Помощь"):
            st.info("""
            **Последовательность работы:**
            1. 🔤 ABC анализ (опционально)
            2. 🔤📊 ABC анализ по подкатегориям (детализация)
            2. 📊 Расчет ADS из файла продаж
            3. 📋 Расчет минимальных запасов
            4. ⚖️ Загрузка остатков и сравнение
            5. 📤 Экспорт результатов
            """)
    
    with col2:
        progress = status['overall']['progress_percentage']
        if progress == 100:
            st.success("✅ Все этапы завершены!")
        else:
            st.info(f"📊 Прогресс: {progress:.0f}%")
    
    with col3:
        st.caption(f"Система v2.0 | SIRIUS {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()