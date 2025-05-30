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

def abc_analysis_page_updated(system):
    """Обновленная страница ABC анализа с поддержкой товаров с нулевыми продажами"""
    st.header("🔤 ABC анализ товаров (включая товары с нулевыми продажами)")
    
    st.markdown("""
    **ABC анализ** помогает классифицировать товары по принципу Парето (80/20):
    - **A товары** - 80% продаж (обычно 20% товаров)
    - **B товары** - 15% продаж  
    - **C товары** - 5% продаж + **все товары с нулевыми продажами**
    
    ✅ **Новое**: Товары с пустыми ячейками продаж автоматически получают значение 0 и класс C
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
        
        # Проверяем наличие информации о нулевых продажах
        zero_sales_count = abc_results.get('items_with_zero_sales', 0)
        items_with_sales = abc_results.get('items_with_sales', total_items)
        
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
        
        # Информация о нулевых продажах
        if zero_sales_count > 0:
            st.info(f"""
            📊 **Обработка товаров с нулевыми продажами:**
            - Товаров с продажами > 0: **{items_with_sales}**
            - Товаров с продажами = 0: **{zero_sales_count}** (автоматически класс C)
            - Все товары включены в анализ: **✅**
            """)
        
        # Визуализации
        visualizations = system.create_visualizations()
        
        if 'abc_distribution' in visualizations:
            st.plotly_chart(visualizations['abc_distribution'], use_container_width=True)
        
        if 'pareto_analysis' in visualizations:
            st.plotly_chart(visualizations['pareto_analysis'], use_container_width=True)
        
        # Анализ по категориям с учетом нулевых продаж
        st.subheader("📊 Анализ по категориям (включая товары с нулевыми продажами)")
        category_analysis = abc_results['category_analysis']
        
        category_data = []
        for cat, data in category_analysis.items():
            # Получаем информацию о нулевых продажах в категории
            zero_sales_in_cat = data.get('items_with_zero_sales', 0)
            items_with_sales_in_cat = data.get('items_with_sales', data['total_items'])
            
            category_data.append({
                'Категория': cat,
                'Всего товаров': data['total_items'],
                'С продажами': items_with_sales_in_cat,
                'Нулевые продажи': zero_sales_in_cat,
                'Общие продажи': f"{data['total_sales']:,.0f}",
                'Доля продаж %': f"{data['sales_percentage']:.2f}%",
                'A товары': data['abc_distribution']['A'],
                'B товары': data['abc_distribution']['B'],
                'C товары': data['abc_distribution']['C']
            })
        
        category_df = pd.DataFrame(category_data)
        category_df = category_df.sort_values('Доля продаж %', ascending=False)
        st.dataframe(category_df, use_container_width=True)
        
        # Дополнительная аналитика по нулевым продажам
        if zero_sales_count > 0:
            with st.expander("🔍 Детальный анализ товаров с нулевыми продажами"):
                abc_detailed = abc_results['abc_data_detailed']
                zero_sales_items = abc_detailed[abc_detailed['annual_sales'] == 0]
                
                st.write(f"**Найдено {len(zero_sales_items)} товаров с нулевыми продажами:**")
                
                # Группировка по категориям
                zero_by_category = zero_sales_items['category'].value_counts()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Распределение по категориям:**")
                    for category, count in zero_by_category.head(10).items():
                        st.write(f"• {category}: {count} товаров")
                
                with col2:
                    # График распределения нулевых продаж
                    if len(zero_by_category) > 0:
                        fig_zero = px.bar(
                            x=zero_by_category.head(10).values,
                            y=zero_by_category.head(10).index,
                            orientation='h',
                            title='Топ-10 категорий с товарами без продаж',
                            labels={'x': 'Количество товаров', 'y': 'Категория'}
                        )
                        st.plotly_chart(fig_zero, use_container_width=True)
                
                # Таблица товаров с нулевыми продажами
                st.write("**Примеры товаров с нулевыми продажами:**")
                display_zero = zero_sales_items[['nomenclature', 'category', 'annual_sales', 'abc_class']].head(20)
                st.dataframe(display_zero, use_container_width=True)
        
        # Кнопка для перезагрузки
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Загрузить новый ABC файл"):
                system.abc_data = None
                system.abc_results = None
                st.rerun()
        
        with col2:
            if st.button("📊 Показать только товары с продажами"):
                # Фильтр для показа только товаров с продажами > 0
                abc_detailed = abc_results['abc_data_detailed']
                items_with_sales_only = abc_detailed[abc_detailed['annual_sales'] > 0]
                
                st.write(f"**Товары только с продажами > 0: {len(items_with_sales_only)} из {len(abc_detailed)}**")
                
                # Пересчитываем ABC для товаров только с продажами
                if len(items_with_sales_only) > 0:
                    sales_only_summary = items_with_sales_only['abc_class'].value_counts()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("A (только с продажами)", sales_only_summary.get('A', 0))
                    with col2:
                        st.metric("B (только с продажами)", sales_only_summary.get('B', 0))
                    with col3:
                        c_with_sales = sales_only_summary.get('C', 0)
                        st.metric("C (только с продажами)", c_with_sales)
                    
                    items_display = items_with_sales_only[['nomenclature', 'category', 'annual_sales', 'abc_class']].head(20).copy()
            
                    # Переименовываем колонки на русские
                    items_display.columns = ['Номенклатура', 'Категория', 'Годовые продажи', 'ABC класс']
                    
                    st.dataframe(
                        items_display,
                        use_container_width=True
                    )
    
    else:
        # ABC анализ не выполнен
        st.info("Загрузите файл для ABC анализа (например: исходники.xlsx)")
        
        st.success("""
        ✅ **Улучшения в обработке данных:**
        
        - **Пустые ячейки продаж** автоматически заменяются на **0**
        - **Все товары** включаются в ABC анализ (даже с нулевыми продажами)
        - Товары с нулевыми продажами получают **класс C**
        - Принцип Парето рассчитывается только для товаров с продажами > 0
        """)
        
        abc_file = st.file_uploader(
            "Выберите файл для ABC анализа",
            type=['xlsx', 'xls'],
            help="Файл должен содержать: Наименование, Категория, Объем продаж (пустые ячейки = 0)"
        )
        
        if abc_file is not None:
            with st.spinner("Загрузка и анализ ABC данных с обработкой нулевых продаж..."):
                # Загружаем файл
                load_result = system.load_abc_file(abc_file)
                
                if load_result['success']:
                    st.success(f"✅ Файл загружен: {load_result['total_items']} товаров")
                    
                    # Показываем детали загрузки с информацией о нулевых продажах
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Всего товаров", load_result['total_items'])
                    with col2:
                        st.metric("С продажами > 0", load_result.get('items_with_sales', '?'))
                    with col3:
                        st.metric("С продажами = 0", load_result.get('items_with_zero_sales', '?'))
                    with col4:
                        st.metric("Категорий", load_result['categories'])
                    
                    # Показываем информацию о распределении продаж
                    if 'sales_distribution' in load_result:
                        sales_dist = load_result['sales_distribution']
                        st.info(f"""
                        📊 **Распределение продаж:**
                        - Товаров с продажами > 0: {sales_dist['positive_sales']}
                        - Товаров с продажами = 0: {sales_dist['zero_sales']} (будут класса C)
                        - Общая стоимость продаж: {sales_dist['total_sales_value']:,.0f}
                        """)
                    
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
                        st.success("✅ ABC анализ завершен с включением всех товаров!")
                        
                        # Показываем краткую статистику результата
                        if analysis_result.get('zero_sales_included'):
                            st.info(f"""
                            🎯 **Результат анализа:**
                            - Всего проанализировано: {analysis_result['total_items']} товаров
                            - С продажами: {analysis_result['items_with_sales']} товаров
                            - С нулевыми продажами: {analysis_result['items_with_zero_sales']} товаров (класс C)
                            - A товары: {analysis_result['abc_summary']['A']}
                            - B товары: {analysis_result['abc_summary']['B']}
                            - C товары: {analysis_result['abc_summary']['C']}
                            """)
                        
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
def ads_calculation_page_updated(system):

    st.header("📊 Расчет ADS")
    
    try:
        from integration_patch import add_multiple_files_interface_to_existing
        
        if add_multiple_files_interface_to_existing():
            return  # Если используются множественные файлы, выходим
    except Exception as e:
        st.error(f"Ошибка загрузки множественных файлов: {e}")

    st.markdown("""
    **🔢 ФОРМУЛА ADS:**
    - **Номенклатура:** Читается из колонки B 
    - **Диапазон данных:** M4:AB4 до последнего товара
    - **Формула:** ADS = (среднее значение от M4:AB4) / 30
    - **Исключения:** Последняя строка автоматически исключается
    """)
    
    # Показываем структуру файла
    with st.expander("📋 Требуемая структура Excel файла"):
        st.markdown("""
        ```
        Колонка A: Коды товаров (не используется)
        Колонка B: НОМЕНКЛАТУРА ТОВАРОВ (основная)
        Колонки M-AB: Месячные данные продаж
        Строка 4: Начало данных
        Последняя строка: Исключается автоматически
        ```
        """)
    
    status = system.get_system_status()
    
    if status['sales_analysis']['ads_calculated']:
        # ADS уже рассчитан
        st.success("✅ ADS рассчитан!")
        
        ads_data = system.calculated_ads
        
        # Показываем информацию о методе
        if hasattr(system, '_json_data') and 'ads' in system._json_data:
            metadata = system._json_data['ads']['metadata']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров", len(ads_data))
            with col3:
                st.metric("Общий ADS", f"{ads_data['ads'].sum():.2f}")
            with col4:
                st.metric("Средний ADS", f"{ads_data['ads'].mean():.4f}")
            
            # Показываем детали обработки
            st.subheader("📊 Детали обработки")
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.info(f"""
                **Параметры обработки:**
                - Диапазон: {metadata.get('range_used', 'M4:AB4')}
                - Формула: {metadata.get('formula', 'ADS = среднее/30')}
                - Метод: {metadata.get('calculation_method', 'новый')}
                """)
            
            with info_col2:
                st.info(f"""
                **Статистика:**
                - Обработано: {metadata.get('total_items', 0)} товаров
                - С положительным ADS: {metadata.get('items_with_positive_ads', 0)}
                - Последняя строка исключена: {'✅' if metadata.get('last_row_excluded') else '❌'}
                """)
        
        # JSON данные
        st.subheader("📄 JSON данные")
        
        if st.button("📄 Показать JSON данные", key="show_json"):
            try:
                json_data = system.get_ads_json_data()
                
                # Показываем превью JSON
                st.subheader("📄 JSON превью")
                json_preview = json.loads(json_data)
                
                # Метаданные
                if 'metadata' in json_preview:
                    st.write("**Метаданные:**")
                    st.json(json_preview['metadata'])
                
                # Статистика
                if 'summary_stats' in json_preview:
                    st.write("**Статистика:**")
                    st.json(json_preview['summary_stats'])
                
                # Первые несколько товаров
                if 'items' in json_preview and len(json_preview['items']) > 0:
                    st.write("**Первые 3 товара:**")
                    st.json(json_preview['items'][:3])
                
                # Кнопка скачивания JSON
                if st.button("💾 Скачать JSON файл"):
                    json_filename = system.save_ads_json_to_file()
                    st.success(f"✅ JSON сохранен в файл: {json_filename}")
                    
            except Exception as e:
                st.error(f"❌ Ошибка отображения JSON: {str(e)}")
        
        # Топ товары по ADS
        st.subheader("🏆 Топ товары по ADS")
        top_ads = ads_data.nlargest(10, 'ads')

        fig_ads = px.bar(
            top_ads,
            x='ads',
            y='номенклатура',
            orientation='h',
            title='Топ-10 товаров по ADS',
            labels={'ads': 'Среднедневные продажи', 'номенклатура': 'Товар'}  # Русифицируем подписи осей
        )
        st.plotly_chart(fig_ads, use_container_width=True)
        
        # Детальная таблица
        with st.expander("📋 Детальные данные ADS"):
            # Русифицируем колонки ADS данных
            ads_data_russian = ads_data.copy()
            
            # Маппинг колонок для ADS
            ads_mapping = {
                'номенклатура': 'Номенклатура',
                'ads': 'ADS',
                'average_value': 'Среднемесячные продажи',
                'total_sales': 'Общие продажи за период'
            }
            
            # Переименовываем только существующие колонки
            existing_mappings = {k: v for k, v in ads_mapping.items() if k in ads_data_russian.columns}
            ads_data_russian = ads_data_russian.rename(columns=existing_mappings)
     
            st.dataframe(ads_data_russian, use_container_width=True)
        
        # Кнопки для экспорта
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Экспорт в Excel с JSON", key="export_excel_json"):
                try:
                    excel_buffer = system.export_enhanced_results_with_fixed_ads()
                    
                    st.download_button(
                        label="💾 Скачать Excel с исправленной логикой",
                        data=excel_buffer,
                        file_name=f"ads_fixed_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Ошибка экспорта: {str(e)}")
        
        with col2:
            if st.button("🔄 Загрузить новый файл", key="reload_ads"):
                # Очищаем данные для новой загрузки
                system.sales_data = None
                system.calculated_ads = None
                if hasattr(system, '_json_data'):
                    system._json_data.pop('ads', None)
                st.rerun()
    
    else:
        # ADS не рассчитан
        st.info("Загрузите файл с данными продаж для расчета ADS")
        
        st.warning("""
        ⚠️ **ВАЖНО: Проверьте структуру файла!**
        
        - Номенклатура должна быть в **колонке B**
        - Данные продаж в колонках M-AB
        - Данные начинаются с 4-й строки
        """)
        
        sales_file = st.file_uploader(
            "Выберите файл продаж",
            type=['xlsx', 'xls'],
            help="Файл должен содержать номенклатуру в колонке B и данные продаж в колонках M-AB",
            key="sales_file_updated"
        )
        
        if sales_file is not None:
            with st.spinner("Обработка файла с логикой ADS..."):
                # Используем обновленный метод
                load_result = system.load_sales_file_updated(sales_file)
                
                if load_result['success']:
                    st.success(f"✅ ADS рассчитан для {load_result['total_items']} товаров")
                    
                    # Показываем детали результата
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Товаров", load_result['total_items'])
                    with col2:
                        st.metric("Номенклатура из", load_result['nomenclature_column'])
                    with col3:
                        st.metric("Общий ADS", f"{load_result['total_ads']:.2f}")
                    with col4:
                        st.metric("JSON создан", "✅" if load_result['json_data_created'] else "❌")
                    
                    # Информация о обработке
                    st.info(f"""
                    **Результаты обработки:**
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
    **Модульная система анализа товарных запасов**
    
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
        abc_analysis_page_updated(system)
    elif page == "📊 ADS расчет":
        ads_calculation_page_updated(system)
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
        st.caption(f"Система v1.0 | SIRIUS {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()