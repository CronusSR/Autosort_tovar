
# -*- coding: utf-8 -*-
"""
Система автоматизации управления товарными запасами
Версия 1.0

Автор: AI Assistant
Описание: Автоматизация логики Саната для предотвращения out-of-stock ситуаций
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional
import io
import warnings
from excel_processor import ExcelDataProcessor
warnings.filterwarnings('ignore')

class InventoryAutomationSystem:
    """Основной класс системы автоматизации товарных запасов"""
    
    def __init__(self):
        self.processor = ExcelDataProcessor()
        self.category_analysis = None
        self.space_distribution = None
        self.min_stock_data = None
        self.orders_data = None
        
    def load_excel_data(self, uploaded_file) -> bool:
        """Загрузка данных из Excel файла"""
        try:
            # Сохраняем загруженный файл временно
            with open("temp_data.xlsx", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Используем новый процессор для загрузки
            structure_info = self.processor.load_excel_file("temp_data.xlsx")
            
            st.success("✅ Файл успешно загружен!")
            
            # Отображаем информацию о структуре
            with st.expander("📊 Структура загруженных данных"):
                for sheet_name, info in structure_info.items():
                    st.write(f"**{sheet_name}**: {info['rows']} строк, {info['columns']} колонок")
                    if info['column_names']:
                        st.write(f"Колонки: {', '.join(info['column_names'][:10])}{'...' if len(info['column_names']) > 10 else ''}")
            
            # Обрабатываем каждый тип данных
            try:
                ads_df = self.processor.process_ads_data()
                st.success(f"✅ Обработаны ADS данные: {len(ads_df)} записей")
            except Exception as e:
                st.warning(f"⚠️ ADS данные: {str(e)}")
            
            try:
                stock_df = self.processor.process_stock_data()
                st.success(f"✅ Обработаны данные остатков: {len(stock_df)} записей")
            except Exception as e:
                st.warning(f"⚠️ Данные остатков: {str(e)}")
            
            try:
                target_df = self.processor.process_min_target_data()
                st.success(f"✅ Обработаны min-target данные: {len(target_df)} записей")
            except Exception as e:
                st.warning(f"⚠️ Min-target данные: {str(e)}")
            
            return True
            
        except Exception as e:
            st.error(f"Ошибка загрузки файла: {str(e)}")
            return False
    
    def analyze_categories(self) -> Dict:
        """Анализ категорий товаров и их долей"""
        try:
            self.category_analysis = self.processor.calculate_category_analysis()
            return self.category_analysis
        except Exception as e:
            st.error(f"Ошибка анализа категорий: {str(e)}")
            return {}
    
    def calculate_space_distribution(self, total_shelves: int) -> Dict:
        """Распределение торгового пространства по категориям"""
        if not self.category_analysis:
            return {}
        
        try:
            self.space_distribution = self.processor.calculate_space_distribution(
                total_shelves, self.category_analysis
            )
            return self.space_distribution
        except Exception as e:
            st.error(f"Ошибка распределения пространства: {str(e)}")
            return {}
    
    def calculate_minimum_stock(self, days_supply: int = 10) -> pd.DataFrame:
        """Расчет неснижаемого товарного запаса"""
        try:
            self.min_stock_data = self.processor.calculate_minimum_stock(days_supply)
            return self.min_stock_data
        except Exception as e:
            st.error(f"Ошибка расчета минимального запаса: {str(e)}")
            return pd.DataFrame()
    
    def generate_orders(self, safety_factor: float = 1.2, 
                       package_multiples: Dict = None) -> pd.DataFrame:
        """Формирование заказов на основе расчетов"""
        if self.min_stock_data is None or self.min_stock_data.empty:
            return pd.DataFrame()
        
        try:
            # Генерируем базовый список заказов
            orders_df = self.processor.generate_order_list(
                self.min_stock_data, safety_factor
            )
            
            # Применяем кратность упаковки если указана
            if package_multiples:
                orders_df = self.processor.apply_package_multiples(
                    orders_df, package_multiples
                )
            
            self.orders_data = orders_df
            return orders_df
            
        except Exception as e:
            st.error(f"Ошибка генерации заказов: {str(e)}")
            return pd.DataFrame()
    
    def export_results(self) -> io.BytesIO:
        """Экспорт результатов в Excel"""
        if self.orders_data is None or self.orders_data.empty:
            return None
        
        try:
            # Подготавливаем данные для экспорта
            export_data = self.processor.export_results(
                self.orders_data,
                self.category_analysis,
                self.space_distribution
            )
            
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Основной лист с заказами
                export_data['orders'].to_excel(writer, sheet_name='Orders', index=False)
                
                # Лист с анализом категорий
                if 'category_analysis' in export_data:
                    export_data['category_analysis'].to_excel(
                        writer, sheet_name='Category_Analysis', index=True
                    )
                
                # Лист с распределением пространства
                if 'space_distribution' in export_data:
                    export_data['space_distribution'].to_excel(
                        writer, sheet_name='Space_Distribution', index=True
                    )
                
                # Лист со сводкой
                summary_df = pd.DataFrame([export_data['summary']])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            return output
            
        except Exception as e:
            st.error(f"Ошибка экспорта: {str(e)}")
            return None

def main():
    """Главная функция Streamlit приложения"""
    st.set_page_config(
        page_title="Система автоматизации товарных запасов",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 Система автоматизации товарных запасов")
    st.markdown("*Автоматизация логики Саната для предотвращения out-of-stock ситуаций*")
    
    # Инициализация системы
    if 'system' not in st.session_state:
        st.session_state.system = InventoryAutomationSystem()
    
    system = st.session_state.system
    
    # Боковая панель для параметров
    with st.sidebar:
        st.header("⚙️ Параметры системы")
        
        days_supply = st.slider(
            "Количество дней запаса",
            min_value=5,
            max_value=30,
            value=10,
            help="На сколько дней должен хватать товарный запас"
        )
        
        safety_factor = st.slider(
            "Коэффициент безопасности",
            min_value=1.0,
            max_value=2.0,
            value=1.2,
            step=0.1,
            help="Коэффициент для увеличения заказа сверх минимального запаса"
        )
        
        st.markdown("---")
        
        # Настройки кратности упаковки
        st.subheader("🎁 Кратность упаковки")
        use_package_multiples = st.checkbox("Учитывать кратность упаковки")
        
        package_multiple_default = 1
        if use_package_multiples:
            package_multiple_default = st.number_input(
                "Стандартная кратность",
                min_value=1,
                max_value=50,
                value=4,
                help="Стандартная кратность упаковки для всех товаров"
            )
    
    # Основной интерфейс
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Загрузка данных", "📊 Анализ", "📋 Заказы", "📤 Экспорт"])
    
    with tab1:
        st.header("Загрузка исходных данных")
        
        uploaded_file = st.file_uploader(
            "Выберите Excel файл с данными",
            type=['xlsx', 'xls'],
            help="Файл должен содержать листы: ADS, Stock Balance, Min-Target"
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Загрузить и обработать данные"):
                with st.spinner("Загрузка данных..."):
                    success = system.load_excel_data(uploaded_file)
                    
                    if success:
                        st.success("✅ Данные успешно загружены!")
                        st.session_state.data_loaded = True
    
    with tab2:
        st.header("Анализ товарных категорий")
        
        if hasattr(st.session_state, 'data_loaded') and st.session_state.data_loaded:
            if st.button("📊 Выполнить анализ категорий"):
                with st.spinner("Анализ данных..."):
                    # Анализ категорий
                    category_analysis = system.analyze_categories()
                    
                    if category_analysis:
                        st.session_state.category_analysis = category_analysis
                        
                        # Отображение результатов анализа
                        st.subheader("📈 Распределение товаров по категориям")
                        
                        categories_df = pd.DataFrame.from_dict(category_analysis, orient='index')
                        st.dataframe(categories_df, use_container_width=True)
                        
                        # Распределение пространства
                        space_dist = system.calculate_space_distribution(total_shelves)
                        
                        if space_dist:
                            st.session_state.space_distribution = space_dist
                            
                            st.subheader("🏪 Распределение торгового пространства")
                            space_df = pd.DataFrame.from_dict(space_dist, orient='index')
                            st.dataframe(space_df, use_container_width=True)
                            
                            # Визуализация
                            st.subheader("📊 Диаграммы распределения")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**По количеству товаров**")
                                items_chart = pd.DataFrame({
                                    'Category': list(category_analysis.keys()),
                                    'Items': [data['item_count'] for data in category_analysis.values()]
                                })
                                st.bar_chart(items_chart.set_index('Category'))
                            
                            with col2:
                                st.write("**По объему продаж (ADS)**")
                                sales_chart = pd.DataFrame({
                                    'Category': list(category_analysis.keys()),
                                    'ADS_Percentage': [data['ads_percentage'] for data in category_analysis.values()]
                                })
                                st.bar_chart(sales_chart.set_index('Category'))
        else:
            st.info("👆 Сначала загрузите данные на вкладке 'Загрузка данных'")
    
    with tab3:
        st.header("Формирование заказов")
        
        if hasattr(st.session_state, 'data_loaded') and st.session_state.data_loaded:
            if st.button("📋 Сформировать заказы"):
                with st.spinner("Расчет заказов..."):
                    # Расчет минимальных запасов
                    min_stock_df = system.calculate_minimum_stock(days_supply)
                    
                    if not min_stock_df.empty:
                        st.session_state.min_stock_df = min_stock_df
                        
                        st.subheader("📊 Минимальные товарные запасы")
                        
                        # Показываем топ-20 позиций для предварительного просмотра
                        preview_df = min_stock_df.head(20)
                        st.dataframe(preview_df, use_container_width=True)
                        
                        if len(min_stock_df) > 20:
                            st.info(f"Показано 20 из {len(min_stock_df)} позиций")
                        
                        # Подготавливаем кратности упаковки
                        package_multiples = None
                        if use_package_multiples:
                            # Создаем словарь с одинаковой кратностью для всех товаров
                            package_multiples = {}
                            if 'sku' in min_stock_df.columns:
                                for sku in min_stock_df['sku']:
                                    package_multiples[sku] = package_multiple_default
                        
                        # Генерация заказов
                        orders_df = system.generate_orders(safety_factor, package_multiples)
                        
                        if not orders_df.empty:
                            st.session_state.orders_df = orders_df
                            
                            st.subheader("📋 Сформированные заказы по филиалам")
                            
                            # Показываем общую статистику
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Всего позиций", len(orders_df))
                            with col2:
                                total_qty = orders_df['order_quantity'].sum()
                                st.metric("Общее количество", f"{total_qty:,.2f}")
                            with col3:
                                branches_count = orders_df['branch'].nunique()
                                st.metric("Филиалов", branches_count)
                            with col4:
                                categories_count = orders_df['category'].nunique()
                                st.metric("Категорий", categories_count)
                            
                            # Статистика по филиалам
                            branch_summary = system.get_branch_summary()
                            if branch_summary:
                                st.subheader("🏪 Статистика по филиалам")
                                branch_df = pd.DataFrame.from_dict(branch_summary, orient='index')
                                st.dataframe(branch_df, use_container_width=True)
                            
                            # Детальные заказы с возможностью фильтрации
                            st.subheader("📊 Детальные заказы")
                            
                            # Фильтры
                            col1, col2 = st.columns(2)
                            with col1:
                                selected_branch = st.selectbox(
                                    "Выбрать филиал:",
                                    options=['Все'] + list(orders_df['branch'].unique())
                                )
                            with col2:
                                selected_category = st.selectbox(
                                    "Выбрать категорию:",
                                    options=['Все'] + list(orders_df['category'].unique())
                                )
                            
                            # Применяем фильтры
                            filtered_df = orders_df.copy()
                            if selected_branch != 'Все':
                                filtered_df = filtered_df[filtered_df['branch'] == selected_branch]
                            if selected_category != 'Все':
                                filtered_df = filtered_df[filtered_df['category'] == selected_category]
                            
                            st.dataframe(filtered_df, use_container_width=True)
                            
                            # Показываем количество отфильтрованных записей
                            if len(filtered_df) != len(orders_df):
                                st.info(f"Показано {len(filtered_df)} из {len(orders_df)} позиций")
                        else:
                            st.warning("⚠️ Не найдено позиций для заказа")
                    else:
                        st.error("❌ Не удалось рассчитать минимальные запасы")
        else:
            st.info("👆 Сначала загрузите данные на вкладке 'Загрузка данных'")
    
    with tab4:
        st.header("Экспорт результатов")
        
        if hasattr(st.session_state, 'orders_df') and not st.session_state.orders_df.empty:
            st.success("✅ Заказы готовы к экспорту")
            
            # Предварительный просмотр данных для экспорта
            orders_df = st.session_state.orders_df
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Позиций в заказе", len(orders_df))
            with col2:
                if 'order_value' in orders_df.columns:
                    st.metric("Общая стоимость", f"{orders_df['order_value'].sum():,.2f}")
            
            # Кнопка для экспорта
            if st.button("📤 Подготовить Excel файл"):
                with st.spinner("Формирование Excel файла..."):
                    excel_buffer = system.export_results()
                    
                    if excel_buffer:
                        st.success("✅ Excel файл готов к скачиванию!")
                        
                        # Информация о содержимом файла
                        st.info("""
                        📁 **Содержимое Excel файла:**
                        - **Все_заказы**: Полный список заказов по всем филиалам
                        - **Заказы_[филиал]**: Отдельные листы для каждого филиала
                        - **Сводка_филиалов**: Статистика по филиалам
                        - **Анализ_категорий**: Анализ категорий товаров  
                        - **Распределение_полок**: Распределение торгового пространства
                        - **Общая_сводка**: Общая сводная информация
                        """)
                        
                        # Кнопка скачивания
                        st.download_button(
                            label="💾 Скачать Excel файл",
                            data=excel_buffer,
                            file_name=f"inventory_orders_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Ошибка при создании Excel файла")
            
            # Дополнительные опции экспорта
            with st.expander("🔧 Дополнительные опции"):
                st.subheader("Ручные корректировки заказов")
                
                # Возможность редактирования конкретных позиций
                if st.checkbox("Включить режим редактирования"):
                    st.warning("⚠️ Режим редактирования позволяет изменять количества заказов")
                    
                    # Выбор позиции для редактирования
                    if 'sku' in orders_df.columns:
                        selected_sku = st.selectbox(
                            "Выберите SKU для редактирования:",
                            options=orders_df['sku'].tolist()
                        )
                        
                        if selected_sku:
                            current_qty = orders_df[orders_df['sku'] == selected_sku]['order_quantity'].iloc[0]
                            new_qty = st.number_input(
                                f"Новое количество для {selected_sku}:",
                                min_value=0,
                                value=int(current_qty),
                                step=1
                            )
                            
                            if st.button("✏️ Применить изменение"):
                                # Обновляем количество в данных
                                idx = orders_df[orders_df['sku'] == selected_sku].index[0]
                                st.session_state.orders_df.at[idx, 'order_quantity'] = new_qty
                                
                                # Пересчитываем стоимость если есть цена
                                if 'price' in orders_df.columns:
                                    price = orders_df.at[idx, 'price']
                                    st.session_state.orders_df.at[idx, 'order_value'] = new_qty * price
                                
                                st.success(f"✅ Количество для {selected_sku} обновлено на {new_qty}")
                                st.experimental_rerun()
        else:
            st.info("👆 Сначала сформируйте заказы на вкладке 'Заказы'")
    
    # Информация о системе
    with st.expander("ℹ️ О системе"):
        st.markdown("""
        ### Функциональность системы:
        
        1. **Загрузка данных**: Импорт данных из Excel файлов (поддержка русской структуры)
        2. **Анализ по филиалам**: Обработка данных для каждого филиала отдельно
        3. **Расчет минимальных запасов**: ADS × Дни запаса для каждого филиала
        4. **Формирование заказов**: Автоматические заказы с учетом остатков по филиалам
        5. **Экспорт по филиалам**: Отдельные листы Excel для каждого филиала
        6. **Ручные корректировки**: Возможность редактирования заказов
        
        ### Поддерживаемые филиалы:
        - 🏪 **Казыбаева** - основной филиал
        - 🏪 **Барыс** - филиал Барыс
        - 🏪 **Астана** - филиал в Астане
        - 🏪 **Шымкент** - филиал в Шымкенте
        
        ### Логика расчетов:
        - **Неснижаемый запас** = ADS филиала × Количество дней запаса
        - **Потребность заказа** = Минимальный запас - Текущие остатки
        - **Количество к заказу** = Потребность × Коэффициент безопасности
        - **Распределение пространства** пропорционально долям продаж (ADS)
        
        ### Структура входных данных:
        Система автоматически распознает листы:
        - **"мин запасы"** - основной лист с ADS, остатками и минимальными запасами
        - **"адс"** - данные среднедневных продаж по филиалам
        - **"ост"** - текущие остатки на складах
        - **"покрытие категории"** - анализ категорий товаров
        """)

if __name__ == "__main__":
    main()