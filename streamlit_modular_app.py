#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульное Streamlit приложение для системы анализа товарных запасов v3.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modular_inventory_system import ModularInventorySystem
import io
import warnings
warnings.filterwarnings('ignore')

# Конфигурация страницы
st.set_page_config(
    page_title="Модульная система анализа товарных запасов v3.0",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    """Инициализация системы в session_state"""
    if 'inventory_system' not in st.session_state:
        st.session_state.inventory_system = ModularInventorySystem()
    return st.session_state.inventory_system

def show_system_status(system):
    """Отображение статуса системы"""
    status = system.get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        abc_status = "✅" if status['abc_analysis']['analyzed'] else "❌"
        st.metric(
            "ABC анализ", 
            f"{abc_status} {status['abc_analysis']['items_count']} товаров"
        )
    
    with col2:
        ads_status = "✅" if status['sales_analysis']['ads_calculated'] else "❌"
        st.metric(
            "ADS расчет", 
            f"{ads_status} {status['sales_analysis']['items_count']} товаров"
        )
    
    with col3:
        min_status = "✅" if status['min_stock_analysis']['calculated'] else "❌"
        st.metric(
            "MIN запасы", 
            f"{min_status} {status['min_stock_analysis']['items_count']} товаров"
        )
    
    with col4:
        stock_status = "✅" if status['stock_analysis']['compared'] else "❌"
        st.metric(
            "Сравнение", 
            f"{stock_status} {status['stock_analysis']['items_count']} товаров"
        )
    
    # Прогресс-бар
    progress = status['overall']['progress_percentage']
    st.progress(progress / 100)
    st.write(f"**Общий прогресс:** {progress:.0f}% ({status['overall']['completed_steps']}/4 этапов)")

def abc_analysis_page(system):
    """Страница ABC анализа"""
    st.header("🔤 ABC анализ товаров")
    
    st.markdown("""
    **ABC анализ** помогает классифицировать товары по принципу Парето (80/20):
    - **A товары** - 80% продаж (обычно 20% товаров)
    - **B товары** - 15% продаж  
    - **C товары** - 5% продаж
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            a_count = abc_summary.get('A', 0)
            st.metric("A товары", f"{a_count} ({a_count/total_items*100:.1f}%)")
        with col2:
            b_count = abc_summary.get('B', 0)
            st.metric("B товары", f"{b_count} ({b_count/total_items*100:.1f}%)")
        with col3:
            c_count = abc_summary.get('C', 0)
            st.metric("C товары", f"{c_count} ({c_count/total_items*100:.1f}%)")
        
        # Визуализации
        visualizations = system.create_visualizations()
        
        if 'abc_distribution' in visualizations:
            st.plotly_chart(visualizations['abc_distribution'], use_container_width=True)
        
        if 'pareto_analysis' in visualizations:
            st.plotly_chart(visualizations['pareto_analysis'], use_container_width=True)
        
        # Анализ по категориям
        st.subheader("📊 Анализ по категориям")
        category_analysis = abc_results['category_analysis']
        
        category_data = []
        for cat, data in category_analysis.items():
            category_data.append({
                'Категория': cat,
                'Всего товаров': data['total_items'],
                'Общие продажи': f"{data['total_sales']:,.0f}",
                'Доля продаж %': f"{data['sales_percentage']:.2f}%",
                'A товары': data['abc_distribution']['A'],
                'B товары': data['abc_distribution']['B'],
                'C товары': data['abc_distribution']['C']
            })
        
        category_df = pd.DataFrame(category_data)
        category_df = category_df.sort_values('Доля продаж %', ascending=False)
        st.dataframe(category_df, use_container_width=True)
        
        # Кнопка для перезагрузки
        if st.button("🔄 Загрузить новый ABC файл"):
            system.abc_data = None
            system.abc_results = None
            st.rerun()
    
    else:
        # ABC анализ не выполнен
        st.info("Загрузите файл для ABC анализа (например: исходникимини.xlsx)")
        
        abc_file = st.file_uploader(
            "Выберите файл для ABC анализа",
            type=['xlsx', 'xls'],
            help="Файл должен содержать: Наименование, Категория, Объем продаж"
        )
        
        if abc_file is not None:
            with st.spinner("Загрузка и анализ ABC данных..."):
                # Загружаем файл
                load_result = system.load_abc_file(abc_file)
                
                if load_result['success']:
                    st.success(f"✅ Файл загружен: {load_result['total_items']} товаров")
                    
                    # Показываем детали загрузки
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Товаров", load_result['total_items'])
                    with col2:
                        st.metric("Категорий", load_result['categories'])
                    with col3:
                        st.metric("Использован лист", load_result.get('sheet_used', 'неизвестно'))
                    
                    # Показываем топ категории
                    if 'sample_categories' in load_result:
                        with st.expander("📊 Топ категории по количеству товаров"):
                            sample_cats = load_result['sample_categories']
                            cats_df = pd.DataFrame(list(sample_cats.items()), 
                                                 columns=['Категория', 'Количество товаров'])
                            st.dataframe(cats_df, use_container_width=True)
                    
                    # Выполняем ABC анализ
                    analysis_result = system.perform_abc_analysis()
                    
                    if analysis_result['success']:
                        st.success("✅ ABC анализ завершен!")
                        st.rerun()
                    else:
                        st.error(f"❌ {analysis_result['error']}")
                else:
                    st.error(f"❌ {load_result['error']}")

def ads_calculation_page(system):
    """Страница расчета ADS с поддержкой множественных файлов"""
    st.header("📊 Расчет ADS (Среднедневные продажи)")
    
    st.markdown("""
    **ADS (Average Daily Sales)** - ключевой показатель для планирования запасов.
    Рассчитывается на основе исторических данных продаж по всем филиалам.
    
    📁 **Множественная загрузка**: Вы можете загрузить несколько файлов продаж от разных филиалов/складов.
    """)
    
    status = system.get_system_status()
    
    if status['sales_analysis']['ads_calculated']:
        # ADS уже рассчитан
        st.success("✅ ADS рассчитан!")
        
        ads_data = system.calculated_ads
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Товаров", len(ads_data))
        with col2:
            st.metric("Общий ADS", f"{ads_data['ads'].sum():.1f}")
        with col3:
            st.metric("Средний ADS", f"{ads_data['ads'].mean():.2f}")
        
        # Показываем информацию о филиалах, если есть
        if hasattr(system, 'sales_files_data') and system.sales_files_data:
            st.subheader("🏪 Статистика по филиалам")
            
            branch_stats = []
            for branch, data in system.sales_files_data.items():
                if data['success']:
                    branch_stats.append({
                        'Филиал': branch,
                        'Товаров': data['total_items'],
                        'Общее количество': f"{data['total_quantity_sold']:,.0f}",
                        'ADS филиала': f"{data['total_ads']:.1f}",
                        'Колонка': data.get('quantity_column_used', 'неизвестно')
                    })
            
            if branch_stats:
                branch_df = pd.DataFrame(branch_stats)
                st.dataframe(branch_df, use_container_width=True)
        
        # Топ товары по ADS
        st.subheader("🏆 Топ товары по ADS")
        top_ads = ads_data.nlargest(10, 'ads')
        
        fig_ads = px.bar(
            top_ads,
            x='ads',
            y='номенклатура',
            orientation='h',
            title='Топ-10 товаров по среднедневным продажам (все филиалы)'
        )
        st.plotly_chart(fig_ads, use_container_width=True)
        
        # Детальная таблица
        with st.expander("📋 Детальные данные ADS"):
            st.dataframe(ads_data, use_container_width=True)
        
        # Кнопка для перезагрузки
        if st.button("🔄 Загрузить новые файлы продаж"):
            system.sales_data = None
            system.calculated_ads = None
            system.sales_files_data = {}
            system.combined_sales_data = None
            st.rerun()
    
    else:
        # ADS не рассчитан
        st.info("Загрузите файлы с данными продаж по филиалам")
        
        # Выбор режима загрузки
        upload_mode = st.radio(
            "Режим загрузки:",
            ["📁 Один файл", "📁 Множественные файлы"],
            help="Выберите один файл или загрузите несколько файлов от разных филиалов"
        )
        
        if upload_mode == "📁 Один файл":
            # Режим одного файла (старая логика)
            sales_file = st.file_uploader(
                "Выберите файл продаж",
                type=['xlsx', 'xls'],
                help="Файл должен содержать данные продаж по месяцам или общее количество"
            )
            
            if sales_file is not None:
                with st.spinner("Обработка данных продаж..."):
                    load_result = system.load_sales_file(sales_file)
                    
                    if load_result['success']:
                        st.success(f"✅ ADS рассчитан для {load_result['total_items']} товаров")
                        
                        # Показываем какая колонка использовалась
                        if 'quantity_column_used' in load_result:
                            st.info(f"📊 Использована колонка: {load_result['quantity_column_used']}")
                        
                        # Показываем статистику в зависимости от типа данных
                        if 'total_quantity_sold' in load_result:
                            st.metric("Общее количество продаж", f"{load_result['total_quantity_sold']:,.0f} единиц")
                            st.metric("Общий ADS", f"{load_result['total_ads']:.1f} единиц/день")
                        else:
                            st.warning("⚠️ Возможно, используются денежные суммы вместо количества товаров")
                        
                        st.rerun()
                    else:
                        st.error(f"❌ {load_result['error']}")
        
        else:
            # Режим множественных файлов
            st.markdown("### 📁 Загрузка файлов по филиалам")
            st.markdown("Загрузите файлы продаж для каждого филиала/склада:")
            
            # Множественная загрузка файлов
            uploaded_files = st.file_uploader(
                "Выберите файлы продаж",
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                help="Загрузите все файлы продаж от разных филиалов одновременно"
            )
            
            if uploaded_files:
                st.write(f"📁 Загружено файлов: {len(uploaded_files)}")
                
                # Показываем список файлов
                with st.expander("📋 Список загруженных файлов"):
                    for i, file in enumerate(uploaded_files, 1):
                        st.write(f"{i}. {file.name} ({file.size / 1024 / 1024:.1f} MB)")
                
                if st.button("🔄 Обработать все файлы"):
                    with st.spinner("Обработка множественных файлов продаж..."):
                        # Подготавливаем словарь файлов
                        files_dict = {}
                        for file in uploaded_files:
                            # Извлекаем название филиала из имени файла
                            branch_name = _extract_branch_name(file.name)
                            files_dict[branch_name] = file
                        
                        # Обрабатываем все файлы
                        load_result = system.load_multiple_sales_files(files_dict)
                        
                        if load_result['success']:
                            st.success(f"✅ Обработано {load_result['files_processed']} из {load_result['total_files']} файлов")
                            
                            # Показываем общую статистику
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Уникальных товаров", load_result['combined_items'])
                            with col2:
                                st.metric("Общее количество", f"{load_result['total_quantity_all_branches']:,.0f}")
                            with col3:
                                st.metric("Общий ADS", f"{load_result['total_ads_all_branches']:.1f}")
                            
                            # Показываем результаты по филиалам
                            st.subheader("📊 Результаты по филиалам")
                            branch_results = []
                            for branch, result in load_result['branch_results'].items():
                                if result['success']:
                                    branch_results.append({
                                        'Филиал': branch,
                                        'Статус': '✅ Успешно',
                                        'Товаров': result['total_items'],
                                        'Количество': f"{result['total_quantity_sold']:,.0f}",
                                        'ADS': f"{result['total_ads']:.1f}"
                                    })
                                else:
                                    branch_results.append({
                                        'Филиал': branch,
                                        'Статус': '❌ Ошибка',
                                        'Товаров': 0,
                                        'Количество': result['error'][:50] + "...",
                                        'ADS': 0
                                    })
                            
                            results_df = pd.DataFrame(branch_results)
                            st.dataframe(results_df, use_container_width=True)
                            
                            st.rerun()
                        else:
                            st.error(f"❌ {load_result['error']}")

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
    """Страница сравнения остатков"""
    st.header("⚖️ Сравнение остатков с минимальными запасами")
    
    status = system.get_system_status()
    
    if not status['min_stock_analysis']['calculated']:
        st.warning("⚠️ Сначала необходимо рассчитать минимальные запасы")
        if st.button("📋 Перейти к расчету MIN запасов"):
            st.switch_page("MIN запасы")
        return
    
    # Загрузка файла остатков
    if not status['stock_analysis']['loaded']:
        st.info("Загрузите файл текущих остатков (например: остатки мини.xlsx)")
        
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
            with st.spinner("Сравнение остатков с минимальными запасами..."):
                comparison_result = system.compare_stock_vs_min()
                
                if comparison_result['success']:
                    st.success("✅ Сравнение завершено!")
                    st.rerun()
                else:
                    st.error(f"❌ {comparison_result['error']}")
        return
    
    # Показываем результаты сравнения
    comparison_data = system.stock_comparison
    
    st.subheader("📊 Результаты анализа")
    
    # Общая статистика
    total_items = len(comparison_data)
    deficit_items = len(comparison_data[comparison_data['stock_deficit'] > 0])
    critical_items = len(comparison_data[comparison_data['status'] == 'КРИТИЧНО'])
    sufficient_items = len(comparison_data[comparison_data['status'] == 'ДОСТАТОЧНО'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("С дефицитом", f"{deficit_items} ({deficit_items/total_items*100:.1f}%)")
    with col3:
        st.metric("Критично", f"{critical_items} ({critical_items/total_items*100:.1f}%)")
    with col4:
        total_deficit = comparison_data['stock_deficit'].sum()
        st.metric("Общий дефицит", f"{total_deficit:,.0f}")
    
    # Визуализации
    visualizations = system.create_visualizations()
    
    if 'stock_status' in visualizations:
        st.plotly_chart(visualizations['stock_status'], use_container_width=True)
    
    if 'deficit_analysis' in visualizations:
        st.plotly_chart(visualizations['deficit_analysis'], use_container_width=True)
    
    # Детальные результаты
    st.subheader("📋 Детальные результаты")
    
    # Фильтры
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
        min_deficit = st.number_input(
            "Минимальный дефицит",
            min_value=0,
            value=0,
            help="Показать товары с дефицитом больше указанного значения"
        )
    
    # Применяем фильтры
    filtered_data = comparison_data.copy()
    
    if status_filter != 'Все':
        filtered_data = filtered_data[filtered_data['status'] == status_filter]
    
    if priority_filter != 'Все':
        filtered_data = filtered_data[filtered_data['order_priority'] == priority_filter]
    
    if min_deficit > 0:
        filtered_data = filtered_data[filtered_data['stock_deficit'] >= min_deficit]
    
    # Отображаем отфильтрованные данные
    display_columns = [
        'номенклатура', 'ads', 'min_stock_total', 'total_current_stock', 
        'stock_deficit', 'current_stock_days', 'status', 'order_priority', 'recommended_order'
    ]
    
    st.dataframe(
        filtered_data[display_columns], 
        use_container_width=True,
        column_config={
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
    )
    
    if len(filtered_data) != len(comparison_data):
        st.info(f"Показано {len(filtered_data)} из {len(comparison_data)} товаров")

def export_page(system):
    """Страница экспорта результатов"""
    st.header("📤 Экспорт результатов")
    
    status = system.get_system_status()
    
    if not status['overall']['ready_for_export']:
        st.warning("⚠️ Недостаточно данных для экспорта. Выполните хотя бы расчет ADS и один из анализов.")
        return
    
    # Общий отчет
    st.subheader("📊 Итоговый отчет")
    
    summary = system.get_summary_report()
    
    # Отображаем сводку
    if 'abc_analysis' in summary:
        abc = summary['abc_analysis']
        st.write(f"**ABC анализ**: {abc['total_items']} товаров, {abc['categories_analyzed']} категорий")
        st.write(f"- A товары: {abc['distribution']['A_items']} ({abc['distribution']['A_percentage']:.1f}%)")
        st.write(f"- B товары: {abc['distribution']['B_items']} ({abc['distribution']['B_percentage']:.1f}%)")
        st.write(f"- C товары: {abc['distribution']['C_items']} ({abc['distribution']['C_percentage']:.1f}%)")
    
    if 'ads_analysis' in summary:
        ads = summary['ads_analysis']
        st.write(f"**ADS анализ**: {ads['total_items']} товаров, общий ADS: {ads['total_ads']:.1f}")
        st.write(f"- Топ товар: {ads['top_seller']['item']} (ADS: {ads['top_seller']['ads_value']:.2f})")
    
    if 'min_stock_analysis' in summary:
        min_stock = summary['min_stock_analysis']
        st.write(f"**Минимальные запасы**: {min_stock['total_items']} товаров")
        st.write(f"- Общий MIN запас: {min_stock['total_min_stock']:,.0f}")
        st.write(f"- Параметры: {min_stock['parameters']['stock_days']} дней + {min_stock['parameters']['ip_days']} дней IP")
    
    if 'stock_comparison' in summary:
        comparison = summary['stock_comparison']
        st.write(f"**Сравнение остатков**: {comparison['total_items']} товаров")
        st.write(f"- С дефицитом: {comparison['deficit_items']} ({comparison['deficit_percentage']:.1f}%)")
        st.write(f"- Критично: {comparison['critical_items']} ({comparison['critical_percentage']:.1f}%)")
        st.write(f"- Рекомендуемый заказ: {comparison['total_recommended_order']:,.0f}")
    
    # Рекомендации
    st.subheader("💡 Рекомендации")
    recommendations = system.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
    
    # Экспорт в Excel
    st.subheader("📥 Скачать Excel файл")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Подготовить полный отчет", use_container_width=True):
            with st.spinner("Создание Excel файла..."):
                try:
                    excel_buffer = system.export_all_results()
                    
                    st.download_button(
                        label="💾 Скачать Excel файл",
                        data=excel_buffer,
                        file_name=f"inventory_analysis_full_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success("✅ Excel файл готов к скачиванию!")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка создания файла: {str(e)}")
    
    with col2:
        # Информация о содержимом файла
        st.info("""
        **Содержимое Excel файла:**
        - Общий статус системы
        - ABC анализ (если выполнен)
        - ADS расчеты
        - Минимальные запасы
        - Сравнение остатков
        - Товары с дефицитом
        - Критичные товары  
        - Рекомендации по заказу
        """)

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
    
    # Управление данными
    st.subheader("🗂️ Управление данными")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Очистить все данные", use_container_width=True):
            system.clear_all_data()
            st.success("✅ Все данные очищены!")
            st.rerun()
    
    with col2:
        status = system.get_system_status()
        if status['overall']['progress_percentage'] > 0:
            st.metric("Загружено данных", f"{status['overall']['progress_percentage']:.0f}%")
        else:
            st.info("Данные не загружены")
    
    # Информация о системе
    st.subheader("ℹ️ Информация о системе")
    
    st.markdown("""
    **Модульная система анализа товарных запасов v3.0**
    
    **Возможности:**
    - 🔤 ABC анализ по принципу Парето
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
    """)

def main():
    """Основная функция приложения"""
    # Инициализация системы
    system = init_system()
    
    # Заголовок
    st.title("📦 Модульная система анализа товарных запасов v3.0")
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
        abc_analysis_page(system)
    elif page == "📊 ADS расчет":
        ads_calculation_page(system)
    elif page == "📋 MIN запасы":
        min_stock_calculation_page(system)
    elif page == "⚖️ Сравнение остатков":
        stock_comparison_page(system)
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
        st.caption(f"Система v3.0 | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()