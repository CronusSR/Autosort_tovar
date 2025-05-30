# -*- coding: utf-8 -*-
"""

"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional
import io
import warnings
import plotly.express as px
import plotly.graph_objects as go
from excel_processor_v2 import ExcelDataProcessorV2
warnings.filterwarnings('ignore')

class InventoryAutomationSystemV2:
    """Обновленный класс системы автоматизации товарных запасов с ABC анализом"""
    
    def __init__(self):
        self.processor = ExcelDataProcessorV2()
        self.category_analysis = None
        self.space_distribution = None
        self.abc_results = None
        self.orders_data = None
        self.branch_summary = None
        
    def load_excel_data(self, uploaded_file) -> bool:
        """Загрузка основных данных из Excel файла"""
        try:
            # Сохраняем загруженный файл временно
            with open("temp_main_data.xlsx", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Используем обновленный процессор
            structure_info = self.processor.load_excel_file("temp_main_data.xlsx")
            
            st.success("✅ Основной файл успешно загружен!")
            
            # Отображаем информацию о структуре
            with st.expander("📊 Структура загруженных данных"):
                for sheet_name, info in structure_info.items():
                    sheet_type = info.get('sheet_type', 'unknown')
                    st.write(f"**{sheet_name}** ({sheet_type}): {info['rows']} строк, {info['columns']} колонок")
            
            # Обрабатываем основной лист
            try:
                main_df = self.processor.process_main_data()
                st.success(f"✅ **Основные данные обработаны**: {len(main_df)} товаров")
                
                # Показываем расширенную статистику
                with st.expander("📈 Статистика основных данных"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_items = len(main_df)
                        st.metric("Всего товаров", total_items)
                    
                    with col2:
                        active_items = len(main_df[main_df['active_assortment'].str.upper() == 'YES'])
                        st.metric("Активных товаров", active_items)
                    
                    with col3:
                        items_with_ads = len(main_df[main_df['total_ads'] > 0])
                        st.metric("С продажами", items_with_ads)
                    
                    with col4:
                        categories = main_df['category'].nunique()
                        st.metric("Категорий", categories)
                    
                    # Показываем распределение по филиалам
                    st.subheader("📊 ADS по филиалам")
                    branch_ads = {
                        'Казыбаева': main_df['ads_kaz'].sum(),
                        'Барыс': main_df['ads_bar'].sum(), 
                        'Астана': main_df['ads_ast'].sum(),
                        'Шымкент': main_df['ads_shy'].sum()
                    }
                    
                    ads_df = pd.DataFrame(list(branch_ads.items()), columns=['Филиал', 'ADS'])
                    st.bar_chart(ads_df.set_index('Филиал'))
                
                st.session_state.main_data_loaded = True
                return True
                
            except Exception as e:
                st.error(f"Ошибка обработки основных данных: {str(e)}")
                return False
            
        except Exception as e:
            st.error(f"Ошибка загрузки файла: {str(e)}")
            return False
    
    def load_abc_data(self, uploaded_file) -> bool:
        """Загрузка данных для ABC анализа"""
        try:
            # Сохраняем файл ABC данных
            with open("temp_abc_data.xlsx", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Загружаем ABC данные
            abc_df = self.processor.load_abc_analysis_data("temp_abc_data.xlsx")
            
            st.success(f"✅ **ABC данные загружены**: {len(abc_df)} товаров")
            
            # Показываем статистику ABC данных
            with st.expander("📊 Статистика ABC данных"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Товаров в ABC", len(abc_df))
                
                with col2:
                    total_sales = abc_df['annual_sales'].sum()
                    st.metric("Общие продажи", f"{total_sales:,.0f}")
                
                with col3:
                    categories_abc = abc_df['category'].nunique()
                    st.metric("Категорий в ABC", categories_abc)
                
                # Топ товаров по продажам
                st.subheader("🏆 Топ-10 товаров по продажам")
                top_items = abc_df.nlargest(10, 'annual_sales')[['nomenclature', 'category', 'annual_sales']]
                st.dataframe(top_items, use_container_width=True)
            
            st.session_state.abc_data_loaded = True
            return True
            
        except Exception as e:
            st.error(f"Ошибка загрузки ABC данных: {str(e)}")
            return False
    
    def perform_abc_analysis(self) -> Dict:
        """Выполнение ABC анализа"""
        try:
            self.abc_results = self.processor.calculate_abc_analysis()
            
            # Показываем результаты ABC анализа
            st.subheader("📊 Результаты ABC анализа по категориям")
            
            abc_summary_data = []
            for category, data in self.abc_results.items():
                abc_summary_data.append({
                    'Категория': category,
                    'Всего товаров': data['total_items'],
                    'Доля продаж %': round(data['sales_percentage'], 2),
                    'A товаров': data['abc_distribution']['A'],
                    'B товаров': data['abc_distribution']['B'], 
                    'C товаров': data['abc_distribution']['C']
                })
            
            abc_summary_df = pd.DataFrame(abc_summary_data)
            abc_summary_df = abc_summary_df.sort_values('Доля продаж %', ascending=False)
            
            st.dataframe(abc_summary_df, use_container_width=True)
            
            # Визуализация ABC распределения
            self._create_abc_visualizations()
            
            return self.abc_results
            
        except Exception as e:
            st.error(f"Ошибка ABC анализа: {str(e)}")
            return {}
    
    def _create_abc_visualizations(self):
        """Создание визуализаций для ABC анализа"""
        if 'abc_analysis' not in self.processor.processed_data:
            return
        
        abc_data = self.processor.processed_data['abc_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 ABC распределение товаров")
            abc_counts = abc_data['abc_class'].value_counts()
            
            fig_pie = px.pie(
                values=abc_counts.values,
                names=abc_counts.index,
                title="Распределение товаров по ABC классам",
                color_discrete_map={'A': '#ff6b6b', 'B': '#4ecdc4', 'C': '#45b7d1'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("💰 ABC распределение продаж")
            abc_sales = abc_data.groupby('abc_class')['annual_sales'].sum()
            
            fig_bar = px.bar(
                x=abc_sales.index,
                y=abc_sales.values,
                title="Объем продаж по ABC классам",
                color=abc_sales.index,
                color_discrete_map={'A': '#ff6b6b', 'B': '#4ecdc4', 'C': '#45b7d1'}
            )
            fig_bar.update_layout(xaxis_title="ABC Класс", yaxis_title="Объем продаж")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Парето-диаграмма
        st.subheader("📊 Парето-анализ (Правило 80/20)")
        
        pareto_data = abc_data.nlargest(50, 'annual_sales')  # Топ-50 для читаемости
        
        fig_pareto = go.Figure()
        
        # Столбцы продаж
        fig_pareto.add_trace(go.Bar(
            x=list(range(len(pareto_data))),
            y=pareto_data['annual_sales'],
            name='Продажи',
            marker_color='lightblue'
        ))
        
        # Линия накопительного процента
        fig_pareto.add_trace(go.Scatter(
            x=list(range(len(pareto_data))),
            y=pareto_data['cumulative_percentage'],
            name='Накопительный %',
            yaxis='y2',
            line=dict(color='red', width=2)
        ))
        
        fig_pareto.update_layout(
            title='Парето-анализ товаров',
            xaxis_title='Товары (ранжированные по продажам)',
            yaxis_title='Объем продаж',
            yaxis2=dict(
                title='Накопительный процент',
                overlaying='y',
                side='right',
                range=[0, 100]
            )
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True)
    
    def analyze_categories_with_abc(self) -> Dict:
        """Анализ категорий с учетом ABC классификации"""
        try:
            self.category_analysis = self.processor.get_category_analysis_with_abc()
            return self.category_analysis
        except Exception as e:
            st.error(f"Ошибка анализа категорий: {str(e)}")
            return {}
    
    def calculate_space_distribution_with_abc(self, total_shelves: int) -> Dict:
        """Распределение торгового пространства с учетом ABC"""
        if not self.category_analysis:
            return {}
        
        try:
            self.space_distribution = self.processor.calculate_space_distribution_with_abc(
                total_shelves, self.category_analysis
            )
            return self.space_distribution
        except Exception as e:
            st.error(f"Ошибка распределения пространства: {str(e)}")
            return {}
    
    def generate_orders_with_full_logic(self, safety_factor: float = 1.2, 
                                      transit_time_days: int = 7) -> pd.DataFrame:
        """Формирование заказов по полной логике из детализации"""
        try:
            # Генерируем заказы
            orders_df = self.processor.calculate_branch_orders_with_logic(
                safety_factor, transit_time_days
            )
            
            # Обогащаем ABC данными
            if not orders_df.empty:
                orders_df = self.processor.enrich_orders_with_abc(orders_df)
            
            self.orders_data = orders_df
            return orders_df
            
        except Exception as e:
            st.error(f"Ошибка генерации заказов: {str(e)}")
            return pd.DataFrame()
    
    def get_enhanced_branch_summary(self) -> Dict:
        """Получение расширенной сводки по филиалам"""
        if self.orders_data is None or self.orders_data.empty:
            return {}
        
        try:
            self.branch_summary = self.processor.generate_branch_summary_with_abc(self.orders_data)
            return self.branch_summary
        except Exception as e:
            st.error(f"Ошибка создания сводки: {str(e)}")
            return {}
    
    def export_enhanced_results(self) -> io.BytesIO:
        """Экспорт результатов с полной аналитикой"""
        if self.orders_data is None or self.orders_data.empty:
            return None
        
        try:
            # Подготавливаем данные для экспорта
            export_data = self.processor.export_enhanced_results(
                self.orders_data,
                self.category_analysis,
                self.space_distribution,
                self.branch_summary,
                self.abc_results
            )
            
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Основной лист со всеми заказами
                export_data['orders_all'].to_excel(writer, sheet_name='Все_заказы', index=False)
                
                # Заказы по филиалам
                branches = ['казыбаева', 'барыс', 'астана', 'шымкент']
                for branch in branches:
                    sheet_key = f'orders_{branch}'
                    if sheet_key in export_data:
                        export_data[sheet_key].to_excel(
                            writer, sheet_name=f'Заказы_{branch}', index=False
                        )
                
                # Аналитические листы
                if 'branch_summary' in export_data:
                    export_data['branch_summary'].to_excel(
                        writer, sheet_name='Сводка_филиалов', index=True
                    )
                
                if 'category_analysis' in export_data:
                    export_data['category_analysis'].to_excel(
                        writer, sheet_name='Анализ_категорий_ABC', index=True
                    )
                
                if 'space_distribution' in export_data:
                    export_data['space_distribution'].to_excel(
                        writer, sheet_name='Распределение_полок_ABC', index=True
                    )
                
                if 'abc_analysis' in export_data:
                    export_data['abc_analysis'].to_excel(
                        writer, sheet_name='ABC_анализ_категорий', index=True
                    )
                
                if 'abc_details' in export_data:
                    export_data['abc_details'].to_excel(
                        writer, sheet_name='ABC_детали', index=False
                    )
                
                # Общая сводка
                summary_df = pd.DataFrame([export_data['summary']])
                summary_df.to_excel(writer, sheet_name='Общая_сводка', index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            st.error(f"Ошибка экспорта: {str(e)}")
            return None
    
    def get_data_quality_report(self) -> Dict:
        """Получение отчета о качестве данных"""
        try:
            return self.processor.validate_data_quality()
        except Exception as e:
            st.error(f"Ошибка анализа качества данных: {str(e)}")
            return {}

def main():
    """Главная функция обновленного Streamlit приложения"""
    st.set_page_config(
        page_title="Система автоматизации товарных запасов v2.0",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 Система автоматизации товарных запасов v2.0")
    st.markdown("*Полная автоматизация логики Саната с ABC анализом по категориям*")
    
    # Информационная панель
    with st.sidebar:
        st.header("ℹ️ О системе v2.0")
        st.markdown("""
        **Новые возможности:**
        - 🔤 ABC анализ по категориям
        - 📊 Парето-анализ товаров
        - 🎯 Умное распределение полок
        - 📈 Расширенная аналитика
        - 🚛 Учет транзитного времени
        - ✅ Проверка активности ассортимента
        """)
        
        st.markdown("---")
        st.header("⚙️ Параметры системы")
        
        days_supply = st.slider(
            "Количество дней запаса",
            min_value=5,
            max_value=30,
            value=10,
            help="На сколько дней должен хватать товарный запас"
        )
        
        total_shelves = st.number_input(
            "Общее количество полок",
            min_value=100,
            max_value=2000,
            value=786,
            help="Общее количество полок в торговых залах"
        )
        
        safety_factor = st.slider(
            "Коэффициент безопасности",
            min_value=1.0,
            max_value=2.0,
            value=1.2,
            step=0.1,
            help="Коэффициент для увеличения заказа сверх минимального запаса"
        )
        
        transit_time = st.slider(
            "Транзитное время (дни)",
            min_value=1,
            max_value=30,
            value=7,
            help="Время доставки товара (IP - транзитное время)"
        )
    
    # Инициализация системы
    if 'system_v2' not in st.session_state:
        st.session_state.system_v2 = InventoryAutomationSystemV2()
    
    system = st.session_state.system_v2
    
    # Основной интерфейс
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📁 Загрузка данных", 
        "🔤 ABC анализ", 
        "📊 Анализ категорий", 
        "📋 Формирование заказов", 
        "📤 Экспорт", 
        "🔍 Качество данных",
        "📚 Справка"
    ])
    
    with tab1:
        st.header("Загрузка исходных данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Основные данные")
            st.markdown("*Файл с минимальными запасами, ADS, остатками*")
            
            main_file = st.file_uploader(
                "Выберите основной Excel файл",
                type=['xlsx', 'xls'],
                help="Файл должен содержать лист 'мин запасы' с полной структурой данных",
                key="main_file"
            )
            
            if main_file is not None:
                if st.button("🔄 Загрузить основные данные", key="load_main"):
                    with st.spinner("Загрузка основных данных..."):
                        success = system.load_excel_data(main_file)
                        if success:
                            st.success("✅ Основные данные загружены!")
        
        with col2:
            st.subheader("🔤 ABC данные")
            st.markdown("*Файл с данными для ABC анализа*")
            
            abc_file = st.file_uploader(
                "Выберите файл для ABC анализа",
                type=['xlsx', 'xls'],
                help="Файл должен содержать данные о годовых продажах товаров",
                key="abc_file"
            )
            
            if abc_file is not None:
                if st.button("🔄 Загрузить ABC данные", key="load_abc"):
                    with st.spinner("Загрузка ABC данных..."):
                        success = system.load_abc_data(abc_file)
                        if success:
                            st.success("✅ ABC данные загружены!")
        
        # Статус загрузки
        st.markdown("---")
        st.subheader("📋 Статус загрузки данных")
        
        col1, col2 = st.columns(2)
        with col1:
            main_status = "✅ Загружены" if hasattr(st.session_state, 'main_data_loaded') else "❌ Не загружены"
            st.write(f"**Основные данные:** {main_status}")
        
        with col2:
            abc_status = "✅ Загружены" if hasattr(st.session_state, 'abc_data_loaded') else "❌ Не загружены"
            st.write(f"**ABC данные:** {abc_status}")
    
    with tab2:
        st.header("🔤 ABC анализ товаров")
        
        if hasattr(st.session_state, 'abc_data_loaded'):
            if st.button("📊 Выполнить ABC анализ", key="perform_abc"):
                with st.spinner("Выполнение ABC анализа..."):
                    abc_results = system.perform_abc_analysis()
                    
                    if abc_results:
                        st.session_state.abc_completed = True
                        
                        # Общая статистика ABC
                        st.subheader("📈 Общая статистика ABC анализа")
                        
                        if 'abc_analysis' in system.processor.processed_data:
                            abc_data = system.processor.processed_data['abc_analysis']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                total_items = len(abc_data)
                                st.metric("Всего товаров", total_items)
                            
                            with col2:
                                a_items = len(abc_data[abc_data['abc_class'] == 'A'])
                                st.metric("A товары", f"{a_items} ({a_items/total_items*100:.1f}%)")
                            
                            with col3:
                                b_items = len(abc_data[abc_data['abc_class'] == 'B'])
                                st.metric("B товары", f"{b_items} ({b_items/total_items*100:.1f}%)")
                            
                            with col4:
                                c_items = len(abc_data[abc_data['abc_class'] == 'C'])
                                st.metric("C товары", f"{c_items} ({c_items/total_items*100:.1f}%)")
                            
                            # Детальная таблица ABC по категориям
                            st.subheader("📊 ABC анализ по категориям")
                            
                            if abc_results:
                                # Создаем сводную таблицу
                                abc_summary = []
                                for category, data in abc_results.items():
                                    abc_summary.append({
                                        'Категория': category,
                                        'Всего товаров': data['total_items'],
                                        'Общие продажи': f"{data['total_sales']:,.0f}",
                                        'Доля продаж %': f"{data['sales_percentage']:.2f}%",
                                        'A товары': data['abc_distribution']['A'],
                                        'B товары': data['abc_distribution']['B'],
                                        'C товары': data['abc_distribution']['C'],
                                        '% A товаров': f"{(data['abc_distribution']['A']/data['total_items']*100):.1f}%"
                                    })
                                
                                abc_summary_df = pd.DataFrame(abc_summary)
                                abc_summary_df = abc_summary_df.sort_values('Доля продаж %', ascending=False)
                                
                                st.dataframe(abc_summary_df, use_container_width=True)
                                
                                # Топ категории по продажам
                                st.subheader("🏆 Топ-10 категорий по объему продаж")
                                top_categories = sorted(abc_results.items(), 
                                                      key=lambda x: x[1]['total_sales'], reverse=True)[:10]
                                
                                top_cat_data = []
                                for cat, data in top_categories:
                                    top_cat_data.append({
                                        'Категория': cat,
                                        'Объем продаж': f"{data['total_sales']:,.0f}",
                                        'Товаров': data['total_items'],
                                        'A товары': data['abc_distribution']['A']
                                    })
                                
                                st.table(pd.DataFrame(top_cat_data))
        else:
            st.info("👆 Сначала загрузите ABC данные на вкладке 'Загрузка данных'")
    
    with tab3:
        st.header("📊 Анализ категорий с ABC классификацией")
        
        if (hasattr(st.session_state, 'main_data_loaded') and 
            hasattr(st.session_state, 'abc_completed')):
            
            if st.button("📊 Выполнить анализ категорий", key="analyze_categories"):
                with st.spinner("Анализ категорий с ABC..."):
                    try:
                        # Анализ категорий
                        category_analysis = system.analyze_categories_with_abc()
                        
                        if category_analysis:
                            st.session_state.category_analysis = category_analysis
                            
                            # Отображение результатов
                            st.subheader("📈 Категории с ABC классификацией")
                            
                            categories_data = []
                            for cat, data in category_analysis.items():
                                categories_data.append({
                                    'Категория': cat,
                                    'Товаров': data['item_count'],
                                    'Доля %': f"{data['percentage']:.1f}%",
                                    'ADS': f"{data['total_ads']:.1f}",
                                    'ADS %': f"{data['ads_percentage']:.1f}%",
                                    'A товары': data['abc_distribution']['A'],
                                    'B товары': data['abc_distribution']['B'],
                                    'C товары': data['abc_distribution']['C'],
                                    '% A': f"{data['abc_percentage']['A']:.1f}%"
                                })
                            
                            categories_df = pd.DataFrame(categories_data)
                            categories_df = categories_df.sort_values('ADS %', ascending=False)
                            st.dataframe(categories_df, use_container_width=True)
                            
                            # Распределение пространства с ABC
                            space_dist = system.calculate_space_distribution_with_abc(total_shelves)
                            
                            if space_dist:
                                st.session_state.space_distribution = space_dist
                                
                                st.subheader("🏪 Умное распределение торгового пространства")
                                st.markdown("*С учетом ABC классификации (A товары получают больше места)*")
                                
                                space_data = []
                                for cat, data in space_dist.items():
                                    space_data.append({
                                        'Категория': cat,
                                        'Базовые полки': data['base_shelves'],
                                        'Скорректированные полки': data['adjusted_shelves'],
                                        'ABC коэффициент': data['abc_weight'],
                                        'Товаров на полку': data['items_per_shelf'],
                                        'A товары': data['abc_distribution']['A'],
                                        'Всего товаров': sum(data['abc_distribution'].values())
                                    })
                                
                                space_df = pd.DataFrame(space_data)
                                space_df = space_df.sort_values('Скорректированные полки', ascending=False)
                                st.dataframe(space_df, use_container_width=True)
                                
                                # Визуализация распределения полок
                                st.subheader("📊 Визуализация распределения полок")
                                
                                fig = px.bar(
                                    space_df.head(15),  # Топ-15 категорий
                                    x='Категория',
                                    y=['Базовые полки', 'Скорректированные полки'],
                                    title="Сравнение базового и ABC-скорректированного распределения полок",
                                    barmode='group'
                                )
                                fig.update_xaxes(tickangle=45)
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("⚠️ Не удалось выполнить анализ категорий")
                    
                    except Exception as e:
                        st.error(f"Ошибка при анализе: {str(e)}")
        else:
            st.info("👆 Сначала загрузите данные и выполните ABC анализ")
    
    with tab4:
        st.header("📋 Формирование заказов по полной логике")
        
        if hasattr(st.session_state, 'main_data_loaded'):
            st.markdown(f"""
            **Параметры формирования заказов:**
            - 🛡️ Коэффициент безопасности: {safety_factor}
            - 🚛 Транзитное время: {transit_time} дней
            - ✅ Учет активности ассортимента: включен
            - 🔤 ABC обогащение: {'включено' if hasattr(st.session_state, 'abc_completed') else 'отключено'}
            """)
            
            if st.button("📋 Сформировать заказы", key="generate_orders"):
                with st.spinner("Формирование заказов по логике Саната..."):
                    try:
                        # Генерируем заказы
                        orders_df = system.generate_orders_with_full_logic(
                            safety_factor, transit_time
                        )
                        
                        if not orders_df.empty:
                            st.session_state.orders_df = orders_df
                            
                            st.subheader("📋 Заказы сформированы успешно!")
                            
                            # Общая статистика
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Всего позиций", len(orders_df))
                            with col2:
                                total_qty = orders_df['pre_order'].sum()
                                st.metric("Общее количество", f"{total_qty:,.0f}")
                            with col3:
                                branches_count = orders_df['branch'].nunique()
                                st.metric("Филиалов", branches_count)
                            with col4:
                                categories_count = orders_df['category'].nunique()
                                st.metric("Категорий", categories_count)
                            
                            # ABC статистика в заказах
                            if 'abc_class' in orders_df.columns:
                                st.subheader("🔤 ABC распределение в заказах")
                                
                                abc_in_orders = orders_df['abc_class'].value_counts()
                                abc_col1, abc_col2, abc_col3, abc_col4 = st.columns(4)
                                
                                with abc_col1:
                                    a_count = abc_in_orders.get('A', 0)
                                    st.metric("A товары", f"{a_count} ({a_count/len(orders_df)*100:.1f}%)")
                                
                                with abc_col2:
                                    b_count = abc_in_orders.get('B', 0)
                                    st.metric("B товары", f"{b_count} ({b_count/len(orders_df)*100:.1f}%)")
                                
                                with abc_col3:
                                    c_count = abc_in_orders.get('C', 0)
                                    st.metric("C товары", f"{c_count} ({c_count/len(orders_df)*100:.1f}%)")
                                
                                with abc_col4:
                                    unknown_count = abc_in_orders.get('Unknown', 0)
                                    st.metric("Не определено", f"{unknown_count}")
                            
                            # Расширенная сводка по филиалам
                            branch_summary = system.get_enhanced_branch_summary()
                            if branch_summary:
                                st.subheader("🏪 Расширенная статистика по филиалам")
                                
                                branch_data = []
                                for branch, data in branch_summary.items():
                                    branch_data.append({
                                        'Филиал': branch,
                                        'Позиций': data['total_positions'],
                                        'Количество': f"{data['total_quantity']:,.0f}",
                                        'Потребность': f"{data['total_need']:,.0f}",
                                        'Категорий': data['categories_count'],
                                        'A товары': data['abc_positions']['A'],
                                        'B товары': data['abc_positions']['B'],
                                        'C товары': data['abc_positions']['C'],
                                        '% A товаров': f"{data['abc_percentages']['A']:.1f}%"
                                    })
                                
                                branch_df = pd.DataFrame(branch_data)
                                st.dataframe(branch_df, use_container_width=True)
                            
                            # Детальные заказы с фильтрацией
                            st.subheader("📊 Детальные заказы")
                            
                            # Фильтры
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                selected_branch = st.selectbox(
                                    "Филиал:",
                                    options=['Все'] + list(orders_df['branch'].unique()),
                                    key="filter_branch"
                                )
                            with col2:
                                selected_category = st.selectbox(
                                    "Категория:",
                                    options=['Все'] + list(orders_df['category'].unique()),
                                    key="filter_category"
                                )
                            with col3:
                                if 'abc_class' in orders_df.columns:
                                    selected_abc = st.selectbox(
                                        "ABC класс:",
                                        options=['Все'] + list(orders_df['abc_class'].unique()),
                                        key="filter_abc"
                                    )
                                else:
                                    selected_abc = 'Все'
                            
                            # Применяем фильтры
                            filtered_df = orders_df.copy()
                            if selected_branch != 'Все':
                                filtered_df = filtered_df[filtered_df['branch'] == selected_branch]
                            if selected_category != 'Все':
                                filtered_df = filtered_df[filtered_df['category'] == selected_category]
                            if selected_abc != 'Все' and 'abc_class' in orders_df.columns:
                                filtered_df = filtered_df[filtered_df['abc_class'] == selected_abc]
                            
                            # Показываем отфильтрованные данные
                            st.dataframe(filtered_df, use_container_width=True)
                            
                            if len(filtered_df) != len(orders_df):
                                st.info(f"Показано {len(filtered_df)} из {len(orders_df)} позиций")
                        else:
                            st.warning("⚠️ Не найдено позиций для заказа")
                            st.info("Возможные причины: все товары имеют достаточные остатки или неактивны")
                            
                    except Exception as e:
                        st.error(f"Ошибка при формировании заказов: {str(e)}")
        else:
            st.info("👆 Сначала загрузите основные данные")
    
    with tab5:
        st.header("📤 Экспорт результатов")
        
        if hasattr(st.session_state, 'orders_df') and not st.session_state.orders_df.empty:
            st.success("✅ Заказы готовы к экспорту")
            
            orders_df = st.session_state.orders_df
            
            # Предварительный просмотр
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Позиций в заказе", len(orders_df))
            with col2:
                total_qty = orders_df['pre_order'].sum()
                st.metric("Общее количество", f"{total_qty:,.0f}")
            with col3:
                if 'abc_class' in orders_df.columns:
                    a_items = len(orders_df[orders_df['abc_class'] == 'A'])
                    st.metric("A товары в заказе", f"{a_items} ({a_items/len(orders_df)*100:.1f}%)")
            
            # Информация о содержимом файла
            st.info("""
            📁 **Содержимое Excel файла будет включать:**
            - **Все_заказы**: Полный список заказов по всем филиалам с ABC классами
            - **Заказы_[филиал]**: Отдельные листы для каждого филиала
            - **Сводка_филиалов**: Расширенная статистика по филиалам с ABC
            - **Анализ_категорий_ABC**: Анализ категорий с ABC классификацией
            - **Распределение_полок_ABC**: Умное распределение торгового пространства
            - **ABC_анализ_категорий**: Результаты ABC анализа по категориям
            - **ABC_детали**: Детальные данные ABC анализа всех товаров
            - **Общая_сводка**: Сводная информация
            """)
            
            # Кнопка экспорта
            if st.button("📤 Подготовить расширенный Excel файл", key="export_enhanced"):
                with st.spinner("Формирование расширенного Excel файла..."):
                    excel_buffer = system.export_enhanced_results()
                    
                    if excel_buffer:
                        st.success("✅ Расширенный Excel файл готов к скачиванию!")
                        
                        # Кнопка скачивания
                        st.download_button(
                            label="💾 Скачать расширенный Excel файл",
                            data=excel_buffer,
                            file_name=f"inventory_orders_enhanced_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Ошибка при создании Excel файла")
        else:
            st.info("👆 Сначала сформируйте заказы на вкладке 'Формирование заказов'")
    
    with tab6:
        st.header("🔍 Анализ качества данных")
        
        if hasattr(st.session_state, 'main_data_loaded'):
            if st.button("🔍 Проверить качество данных", key="check_quality"):
                with st.spinner("Анализ качества данных..."):
                    quality_report = system.get_data_quality_report()
                    
                    if quality_report:
                        # Основная статистика
                        st.subheader("📊 Общая статистика данных")
                        
                        if 'main_data' in quality_report:
                            main_data = quality_report['main_data']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Всего товаров", main_data.get('total_items', 0))
                            with col2:
                                st.metric("С продажами (ADS)", main_data.get('items_with_ads', 0))
                            with col3:
                                st.metric("С остатками", main_data.get('items_with_stock', 0))
                            with col4:
                                st.metric("Активных товаров", main_data.get('active_items', 0))
                        
                        # ABC покрытие
                        if 'abc_coverage' in quality_report:
                            st.subheader("🔤 Покрытие ABC анализом")
                            coverage = quality_report['abc_coverage']
                            
                            if coverage >= 70:
                                st.success(f"✅ Отличное покрытие ABC: {coverage}%")
                            elif coverage >= 50:
                                st.warning(f"⚠️ Удовлетворительное покрытие ABC: {coverage}%")
                            else:
                                st.error(f"❌ Низкое покрытие ABC: {coverage}%")
                        
                        # Проблемы и рекомендации
                        if quality_report.get('issues'):
                            st.subheader("⚠️ Обнаруженные проблемы")
                            for issue in quality_report['issues']:
                                st.warning(f"• {issue}")
                        
                        if quality_report.get('recommendations'):
                            st.subheader("💡 Рекомендации")
                            for rec in quality_report['recommendations']:
                                st.info(f"• {rec}")
                        
                        # Детальный отчет
                        with st.expander("📋 Детальный отчет качества"):
                            st.json(quality_report)
        else:
            st.info("👆 Сначала загрузите основные данные")
    
    with tab7:
        st.header("📚 Справочная информация")
        
        st.markdown("""
        ## 🎯 Логика системы v2.0
        
        ### Основные принципы работы согласно детализации:
        
        **1. Обработка номенклатуры:**
        - ✅ **Ассортимент активный или нет**: Только товары со значением "YES" попадают в заказ
        - 📊 **ADS (среднедневные продажи)**: Базовый показатель для всех расчетов
        - 📅 **Дни запаса**: Количество дней, на которое должен хватать товар
        - 📦 **MIN (минимальное количество)**: ADS × количество дней запаса
        
        **2. Расчет потребности:**
        - 📈 **Товарный запас в днях** = Фактические остатки ÷ ADS
        - 🚛 **Чистая потребность** = ADS × транзитное время (сколько продастся пока товар едет)
        - 📋 **Предзаказ** = (MIN - текущие остатки + чистая потребность) × коэффициент безопасности
        
        **3. ABC анализ по категориям:**
        - 🔴 **A товары (80% продаж)**: Высокий приоритет, больше места на полках
        - 🟡 **B товары (15% продаж)**: Средний приоритет  
        - 🟢 **C товары (5% продаж)**: Низкий приоритет
        
        **4. Умное распределение пространства:**
        - Базовое распределение по доле ADS
        - Корректировка по ABC классам (A товары получают коэффициент 1.5)
        - Оптимизация количества товаров на полку
        
        ---
        
        ## 💡 Советы по использованию
        
        **1. Подготовка данных:**
        - Убедитесь, что все товары имеют корректные названия
        - Проверьте заполненность ADS данных
        - Установите правильные значения "активный/нет" (YES/NO)
        
        **2. ABC анализ:**
        - Используйте данные за полный год для точного ABC
        - Регулярно обновляйте ABC классификацию
        - Учитывайте сезонность товаров
        
        **3. Настройка параметров:**
        - Коэффициент безопасности 1.2-1.5 для большинства категорий
        - Транзитное время зависит от поставщика (обычно 5-10 дней)
        - Дни запаса варьируются по категориям (быстро оборачиваемые - меньше дней)
        
        **4. Анализ результатов:**
        - Обращайте внимание на A товары - они критически важны
        - Контролируйте остатки C товаров - не переполняйте склады
        - Используйте ABC для планирования закупок и размещения
        
        ---
        
        ## 🚀 Новые возможности v2.0
        
        ✨ **ABC анализ**: Автоматическая классификация товаров по принципу Парето
        
        📊 **Умное распределение полок**: Учет важности товаров при размещении
        
        🎯 **Расширенная аналитика**: Детальные отчеты по филиалам и категориям
        
        🔍 **Контроль качества данных**: Автоматическая проверка и рекомендации
        
        📈 **Визуализация**: Графики ABC, Парето-анализ, распределение по категориям
        
        🚛 **Учет логистики**: Транзитное время и чистая потребность
        
        ✅ **Фильтрация ассортимента**: Учет активности товаров
        
        📋 **Детальные отчеты**: Множественные листы Excel с аналитикой
        """)

if __name__ == "__main__":
    main()
