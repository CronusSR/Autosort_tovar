# enhanced_warehouse_interface.py
"""
🎯 УЛУЧШЕННЫЙ ИНТЕРФЕЙС АНАЛИЗА СКЛАДОВ
Решает все задачи:
- Добавляет отображение цен в интерфейс  
- Показывает максимальные и минимальные остатки
- Объясняет расчет колонки "к заказу"
- Отображает ВСЕ товары без ограничений
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from io import BytesIO
from datetime import datetime
import traceback


class EnhancedWarehouseInterface:
    """
    Улучшенный интерфейс для анализа складов с полной функциональностью
    """
    
    def __init__(self):
        self.price_data = {}
        self.analysis_results = None
        self.show_all_items = True  # По умолчанию показываем ВСЕ товары
        
    def find_price_data_comprehensive(self, system):
        """
        Всесторонний поиск ценовых данных в системе
        """
        
        found_prices = {}
        price_sources = []
        
        st.write("🔍 **Поиск ценовых данных в системе:**")
        
        # 1. Основные ADS данные
        if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
            ads_df = system.calculated_ads
            price_cols = self._find_price_columns(ads_df)
            
            if price_cols:
                prices_found = self._extract_prices_from_dataframe(ads_df, price_cols[0])
                found_prices.update(prices_found)
                price_sources.append(f"calculated_ads ({len(prices_found)} товаров)")
                st.write(f"✅ ADS данные: найдено {len(prices_found)} цен")
            else:
                st.write(f"⚠️ ADS данные: ценовые колонки не найдены")
        
        # 2. Данные по магазинам
        if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
            store_prices = 0
            
            if 'processed_results' in system.multiple_files_data:
                for filename, result_data in system.multiple_files_data['processed_results'].items():
                    store_price_data = self._extract_store_prices(result_data)
                    found_prices.update(store_price_data)
                    if store_price_data:
                        store_prices += len(store_price_data)
            
            if store_prices > 0:
                price_sources.append(f"данные магазинов ({store_prices} товаров)")
                st.write(f"✅ Данные магазинов: найдено {store_prices} цен")
        
        # 3. Другие источники данных
        other_sources = ['sales_data', 'processed_sales', 'price_data', 'last_purchases']
        for attr_name in other_sources:
            if hasattr(system, attr_name):
                attr_data = getattr(system, attr_name)
                if attr_data is not None and hasattr(attr_data, 'columns'):
                    price_cols = self._find_price_columns(attr_data)
                    if price_cols:
                        prices = self._extract_prices_from_dataframe(attr_data, price_cols[0])
                        found_prices.update(prices)
                        if prices:
                            price_sources.append(f"{attr_name} ({len(prices)} товаров)")
                            st.write(f"✅ {attr_name}: найдено {len(prices)} цен")
        
        # Итоговая статистика
        total_prices = len(found_prices)
        if total_prices > 0:
            st.success(f"💰 **Найдено цен:** {total_prices} товаров из источников: {', '.join(price_sources)}")
            
            # Показываем статистику цен
            prices_values = list(found_prices.values())
            avg_price = np.mean(prices_values)
            min_price = np.min(prices_values)
            max_price = np.max(prices_values)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Средняя цена", f"{avg_price:,.0f} ₸")
            with col2:
                st.metric("Мин. цена", f"{min_price:,.0f} ₸")
            with col3:
                st.metric("Макс. цена", f"{max_price:,.0f} ₸")
        else:
            st.warning("⚠️ **Ценовые данные не найдены** в системе")
        
        self.price_data = found_prices
        return found_prices
    
    def _find_price_columns(self, df):
        """Находит колонки с ценами в DataFrame"""
        price_keywords = [
            'цена', 'price', 'стоимость', 'cost', 'закупка', 'purchase',
            'last_purchase_price', 'себестоимость', 'unit_price', 'руб', 'тенге'
        ]
        
        price_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in price_keywords):
                price_cols.append(col)
        
        return price_cols
    
    def _extract_prices_from_dataframe(self, df, price_col):
        """Извлекает цены из DataFrame"""
        prices = {}
        
        if 'номенклатура' not in df.columns:
            return prices
        
        for _, row in df.iterrows():
            try:
                item_name = str(row['номенклатура']).strip()
                price_value = float(row[price_col])
                
                if pd.notna(price_value) and price_value > 0:
                    prices[item_name] = price_value
            except (ValueError, TypeError, KeyError):
                continue
        
        return prices
    
    def _extract_store_prices(self, result_data):
        """Извлекает цены из данных магазинов"""
        prices = {}
        
        # Попытка найти данные в различных структурах
        data_sources = []
        
        if isinstance(result_data, dict):
            for key in ['calculated_ads', 'ads_data', 'data', 'result']:
                if key in result_data:
                    data_sources.append(result_data[key])
        elif hasattr(result_data, 'columns'):
            data_sources.append(result_data)
        
        for data in data_sources:
            if hasattr(data, 'columns'):
                price_cols = self._find_price_columns(data)
                if price_cols:
                    extracted = self._extract_prices_from_dataframe(data, price_cols[0])
                    prices.update(extracted)
        
        return prices
    
    def display_order_calculation_explanation(self):
        """
        Объясняет как рассчитывается колонка "к заказу"
        """
        
        st.subheader("📊 Как рассчитывается колонка 'К заказу'")
        
        with st.expander("🔍 Подробное объяснение расчетов", expanded=True):
            
            st.markdown("""
            ### 🎯 **Логика расчета количества к заказу:**
            
            #### 1️⃣ **Расчет MIN и MAX запасов:**
            - **MIN запас** = ADS × MIN_дней (например: ADS × 15 дней)
            - **MAX запас** = ADS × MAX_дней (например: ADS × 45 дней)
            
            #### 2️⃣ **Определение статуса товара:**
            
            **🔴 КРИТИЧНЫЙ** - Остаток < 50% от MIN запаса:
            - **К заказу** = MAX запас - Текущий остаток *(заказываем до MAX)*
            
            **🟡 ВНИМАНИЕ** - Остаток < MIN запаса:  
            - **К заказу** = MIN запас - Текущий остаток *(заказываем до MIN)*
            
            **🟢 В НОРМЕ** - MIN ≤ Остаток ≤ MAX:
            - **К заказу** = 0 *(заказывать не нужно)*
            
            **🟠 ИЗБЫТОК** - Остаток > MAX запаса:
            - **К заказу** = 0 *(есть избыток, не заказываем)*
            
            #### 3️⃣ **Пример расчета:**
            """)
            
            # Создаем пример расчета
            example_data = {
                'Товар': 'Пример товара',
                'ADS': 2.5,
                'MIN дней': 15,
                'MAX дней': 45,
                'MIN запас': 2.5 * 15,
                'MAX запас': 2.5 * 45,
                'Текущий остаток': 20,
                'Статус': 'КРИТИЧНЫЙ (20 < 18.75)',
                'К заказу': 112.5 - 20
            }
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Исходные данные:**")
                st.write(f"- Товар: {example_data['Товар']}")
                st.write(f"- ADS: {example_data['ADS']} шт/день")
                st.write(f"- MIN дней: {example_data['MIN дней']}")
                st.write(f"- MAX дней: {example_data['MAX дней']}")
                st.write(f"- Текущий остаток: {example_data['Текущий остаток']} шт")
            
            with col2:
                st.markdown("**Расчеты:**")
                st.write(f"- MIN запас: {example_data['ADS']} × {example_data['MIN дней']} = **{example_data['MIN запас']} шт**")
                st.write(f"- MAX запас: {example_data['ADS']} × {example_data['MAX дней']} = **{example_data['MAX запас']} шт**")
                st.write(f"- Статус: **{example_data['Статус']}**")
                st.write(f"- К заказу: {example_data['MAX запас']} - {example_data['Текущий остаток']} = **{example_data['К заказу']} шт**")
            
            st.markdown("""
            #### 💡 **Особенности:**
            - Если ADS = 0 (нет продаж), то К заказу = 0
            - Разные склады могут иметь разные MIN/MAX дни
            - Расчет происходит для каждого склада отдельно
            """)
    
    def create_enhanced_warehouse_display(self, analysis_results, system, show_prices=True):
        """
        Создает улучшенное отображение результатов анализа складов
        """
        
        if not analysis_results:
            st.error("❌ Нет данных для отображения")
            return
        
        # Статистика по всем товарам
        total_items = len(analysis_results)
        items_with_orders = sum(1 for item in analysis_results if item.get('total_order_quantity', 0) > 0)
        items_with_critical = sum(1 for item in analysis_results if item.get('critical_warehouses', 0) > 0)
        
        st.subheader("📊 Общая статистика по складам")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего товаров", f"{total_items:,}")
        with col2:
            st.metric("Товаров к заказу", f"{items_with_orders:,}")
        with col3:
            st.metric("Критичных товаров", f"{items_with_critical:,}")
        with col4:
            if self.price_data:
                items_with_prices = sum(1 for item in analysis_results 
                                      if item['номенклатура'] in self.price_data)
                coverage = (items_with_prices / total_items) * 100 if total_items > 0 else 0
                st.metric("Покрытие ценами", f"{coverage:.1f}%")
            else:
                st.metric("Цены", "Не найдены")
        
        # Настройки отображения
        st.subheader("⚙️ Настройки отображения")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_filter = st.selectbox(
                "Показать товары:",
                ["Все товары", "Только с заказами", "Только критичные", "Только избыток", "Без продаж"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "Сортировать по:",
                ["ADS (убыв.)", "Количеству к заказу", "Общему остатку", "Стоимости заказа"]
            )
        
        with col3:
            items_per_page = st.selectbox(
                "Товаров на странице:",
                [50, 100, 200, 500, "Все"], 
                index=1
            )
        
        # Применяем фильтры
        filtered_results = self._apply_filters(analysis_results, show_filter)
        sorted_results = self._apply_sorting(filtered_results, sort_by)
        
        # Пагинация
        if items_per_page != "Все":
            page_size = items_per_page
            total_pages = (len(sorted_results) + page_size - 1) // page_size
            
            if total_pages > 1:
                page = st.selectbox(
                    f"Страница (всего {total_pages}):",
                    range(1, total_pages + 1)
                )
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                display_results = sorted_results[start_idx:end_idx]
            else:
                display_results = sorted_results
        else:
            display_results = sorted_results
        
        # Отображаем результаты
        if display_results:
            st.subheader(f"📋 Результаты анализа ({len(display_results)} из {len(sorted_results)} товаров)")
            
            # Создаем детальную таблицу
            display_df = self._create_display_dataframe(display_results, show_prices)
            
            # Применяем стили для улучшения читаемости
            if len(display_df) < 1000:  # Применяем стили только для небольших таблиц
                styled_df = self._apply_table_styles(display_df)
                st.dataframe(styled_df, use_container_width=True, height=600)
            else:
                st.dataframe(display_df, use_container_width=True, height=600)
            
            # Показываем MIN/MAX остатки отдельно
            self._display_min_max_analysis(display_results)
            
        else:
            st.info("📋 Нет товаров, соответствующих выбранным фильтрам")
    
    def _apply_filters(self, analysis_results, show_filter):
        """Применяет фильтры к результатам"""
        
        if show_filter == "Все товары":
            return analysis_results
        elif show_filter == "Только с заказами":
            return [item for item in analysis_results if item.get('total_order_quantity', 0) > 0]
        elif show_filter == "Только критичные":
            return [item for item in analysis_results if item.get('critical_warehouses', 0) > 0]
        elif show_filter == "Только избыток":
            return [item for item in analysis_results 
                   if any(wh.get('status') == 'excess' for wh in item.get('warehouses', {}).values())]
        elif show_filter == "Без продаж":
            return [item for item in analysis_results if item.get('ads', 0) == 0]
        else:
            return analysis_results
    
    def _apply_sorting(self, results, sort_by):
        """Применяет сортировку к результатам"""
        
        if sort_by == "ADS (убыв.)":
            return sorted(results, key=lambda x: x.get('ads', 0), reverse=True)
        elif sort_by == "Количеству к заказу":
            return sorted(results, key=lambda x: x.get('total_order_quantity', 0), reverse=True)
        elif sort_by == "Общему остатку":
            return sorted(results, key=lambda x: x.get('total_stock', 0), reverse=True)
        elif sort_by == "Стоимости заказа":
            def get_order_value(item):
                total_value = 0
                item_price = self.price_data.get(item['номенклатура'], 0)
                if item_price > 0:
                    total_value = item.get('total_order_quantity', 0) * item_price
                return total_value
            return sorted(results, key=get_order_value, reverse=True)
        else:
            return results
    
    def _create_display_dataframe(self, results, show_prices):
        """Создает DataFrame для отображения"""
        
        display_data = []
        
        for item in results:
            # Основная информация о товаре
            item_price = self.price_data.get(item['номенклатура'], 0)
            order_value = item.get('total_order_quantity', 0) * item_price if item_price > 0 else 0
            
            row = {
                'Номенклатура': item['номенклатура'][:60] + "..." if len(item['номенклатура']) > 60 else item['номенклатура'],
                'ADS': f"{item.get('ads', 0):.2f}",
                'Общий остаток': f"{item.get('total_stock', 0):.0f}",
                'К заказу (всего)': f"{item.get('total_order_quantity', 0):.0f}",
            }
            
            if show_prices and item_price > 0:
                row['Цена за ед.'] = f"{item_price:,.0f} ₸"
                row['Стоимость заказа'] = f"{order_value:,.0f} ₸"
            
            # Информация по складам (основные склады)
            warehouses = item.get('warehouses', {})
            main_warehouses = ['База_Комплект', 'Шымкент_Склад', 'Алматы_Склад', 'Астана_Склад']
            
            for wh_key in main_warehouses:
                if wh_key in warehouses:
                    wh_data = warehouses[wh_key]
                    current = wh_data.get('current_stock', 0)
                    order = wh_data.get('order_quantity', 0)
                    status = wh_data.get('status', 'unknown')
                    
                    # Определяем иконку статуса
                    status_icons = {
                        'critical': '🔴',
                        'warning': '🟡', 
                        'good': '🟢',
                        'excess': '🟠',
                        'no_sales': '⚪',
                        'empty': '⚫'
                    }
                    
                    icon = status_icons.get(status, '❓')
                    
                    if order > 0:
                        row[wh_key] = f"{icon} {current:.0f} (+{order:.0f})"
                    elif current > 0:
                        row[wh_key] = f"{icon} {current:.0f}"
                    else:
                        row[wh_key] = f"{icon} 0"
            
            display_data.append(row)
        
        return pd.DataFrame(display_data)
    
    def _apply_table_styles(self, df):
        """Применяет стили к таблице"""
        
        def highlight_critical(val):
            if '🔴' in str(val):
                return 'background-color: #ffebee'
            elif '🟡' in str(val):
                return 'background-color: #fff3e0'
            elif '🟠' in str(val):
                return 'background-color: #fce4ec'
            elif '🟢' in str(val):
                return 'background-color: #e8f5e8'
            else:
                return ''
        
        # Применяем стили к колонкам складов
        warehouse_cols = [col for col in df.columns if any(wh in col for wh in ['База_Комплект', 'Шымкент', 'Алматы', 'Астана'])]
        
        styled = df.style
        for col in warehouse_cols:
            styled = styled.applymap(highlight_critical, subset=[col])
        
        return styled
    
    def _display_min_max_analysis(self, results):
        """Отображает анализ MIN/MAX остатков"""
        
        st.subheader("📊 Анализ MIN/MAX остатков по складам")
        
        # Собираем статистику по MIN/MAX
        min_max_data = []
        
        for item in results[:50]:  # Показываем первые 50 товаров для MIN/MAX анализа
            for wh_key, wh_data in item.get('warehouses', {}).items():
                min_max_data.append({
                    'Товар': item['номенклатура'][:40] + "..." if len(item['номенклатура']) > 40 else item['номенклатура'],
                    'Склад': wh_key,
                    'Текущий остаток': wh_data.get('current_stock', 0),
                    'MIN запас': wh_data.get('min_stock', 0),
                    'MAX запас': wh_data.get('max_stock', 0),
                    'Статус': wh_data.get('status', 'unknown'),
                    'К заказу': wh_data.get('order_quantity', 0),
                    'ADS': item.get('ads', 0)
                })
        
        if min_max_data:
            min_max_df = pd.DataFrame(min_max_data)
            
            # Фильтры для MIN/MAX таблицы
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.selectbox(
                    "Фильтр по статусу MIN/MAX:",
                    ["Все"] + list(min_max_df['Статус'].unique())
                )
            
            with col2:
                warehouse_filter = st.selectbox(
                    "Фильтр по складу MIN/MAX:",
                    ["Все"] + list(min_max_df['Склад'].unique())
                )
            
            # Применяем фильтры
            filtered_min_max = min_max_df.copy()
            
            if status_filter != "Все":
                filtered_min_max = filtered_min_max[filtered_min_max['Статус'] == status_filter]
            
            if warehouse_filter != "Все":
                filtered_min_max = filtered_min_max[filtered_min_max['Склад'] == warehouse_filter]
            
            # Показываем таблицу MIN/MAX
            st.dataframe(filtered_min_max, use_container_width=True)
            
            # Визуализация MIN/MAX
            self._create_min_max_charts(filtered_min_max)
    
    def _create_min_max_charts(self, min_max_df):
        """Создает графики MIN/MAX анализа"""
        
        st.subheader("📈 Визуализация MIN/MAX остатков")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # График текущий vs MIN/MAX
            fig1 = go.Figure()
            
            fig1.add_trace(go.Scatter(
                x=min_max_df['MIN запас'],
                y=min_max_df['Текущий остаток'],
                mode='markers',
                name='Текущий vs MIN',
                text=min_max_df['Товар'],
                hovertemplate='<b>%{text}</b><br>MIN: %{x}<br>Текущий: %{y}<extra></extra>'
            ))
            
            # Линия идеального соответствия
            max_val = max(min_max_df['MIN запас'].max(), min_max_df['Текущий остаток'].max())
            fig1.add_trace(go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode='lines',
                name='Идеальная линия',
                line=dict(dash='dash', color='red')
            ))
            
            fig1.update_layout(
                title='Текущий остаток vs MIN запас',
                xaxis_title='MIN запас',
                yaxis_title='Текущий остаток',
                height=400
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # График статусов по складам
            status_counts = min_max_df.groupby(['Склад', 'Статус']).size().reset_index(name='Количество')
            
            fig2 = px.bar(
                status_counts,
                x='Склад',
                y='Количество',
                color='Статус',
                title='Распределение статусов по складам',
                color_discrete_map={
                    'critical': 'red',
                    'warning': 'orange', 
                    'good': 'green',
                    'excess': 'purple',
                    'no_sales': 'gray'
                }
            )
            
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    def create_price_integration_summary(self, analysis_results):
        """Создает сводку по ценовой интеграции"""
        
        st.subheader("💰 Сводка по ценовой интеграции")
        
        if not self.price_data:
            st.warning("⚠️ Ценовые данные не найдены")
            return
        
        # Статистика по ценам
        items_with_prices = 0
        total_order_value = 0
        total_stock_value = 0
        
        for item in analysis_results:
            item_name = item['номенклатура']
            if item_name in self.price_data:
                items_with_prices += 1
                item_price = self.price_data[item_name]
                
                order_qty = item.get('total_order_quantity', 0)
                stock_qty = item.get('total_stock', 0)
                
                total_order_value += order_qty * item_price
                total_stock_value += stock_qty * item_price
        
        # Показываем метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            coverage = (items_with_prices / len(analysis_results)) * 100 if analysis_results else 0
            st.metric("Покрытие ценами", f"{coverage:.1f}%")
        
        with col2:
            st.metric("Товаров с ценами", f"{items_with_prices:,}")
        
        with col3:
            st.metric("Стоимость заказов", f"{total_order_value:,.0f} ₸")
        
        with col4:
            st.metric("Стоимость остатков", f"{total_stock_value:,.0f} ₸")
        
        # ТОП товары по стоимости заказа
        if total_order_value > 0:
            st.markdown("### 🏆 ТОП товары по стоимости заказа")
            
            top_items = []
            for item in analysis_results:
                item_name = item['номенклатура']
                if item_name in self.price_data:
                    item_price = self.price_data[item_name]
                    order_qty = item.get('total_order_quantity', 0)
                    order_value = order_qty * item_price
                    
                    if order_value > 0:
                        top_items.append({
                            'Товар': item_name[:50] + "..." if len(item_name) > 50 else item_name,
                            'К заказу': f"{order_qty:.0f}",
                            'Цена': f"{item_price:,.0f} ₸",
                            'Стоимость': f"{order_value:,.0f} ₸",
                            'ADS': f"{item.get('ads', 0):.2f}"
                        })
            
            # Сортируем по стоимости
            top_items.sort(key=lambda x: float(x['Стоимость'].replace(' ₸', '').replace(',', '')), reverse=True)
            
            # Показываем ТОП 20
            if top_items:
                top_df = pd.DataFrame(top_items[:20])
                st.dataframe(top_df, use_container_width=True)


def apply_enhanced_warehouse_interface(system):
    """
    Применяет улучшенный интерфейс к системе анализа складов
    """
    
    # Создаем экземпляр улучшенного интерфейса
    enhanced_interface = EnhancedWarehouseInterface()
    
    # Добавляем к системе
    system.enhanced_warehouse_interface = enhanced_interface
    
    # Добавляем методы к системе
    def find_and_display_prices():
        """Находит и отображает ценовые данные"""
        return enhanced_interface.find_price_data_comprehensive(system)
    
    def display_enhanced_results(analysis_results, show_prices=True):
        """Отображает улучшенные результаты анализа"""
        enhanced_interface.create_enhanced_warehouse_display(analysis_results, system, show_prices)
    
    def show_order_calculation_help():
        """Показывает объяснение расчета колонки 'к заказу'"""
        enhanced_interface.display_order_calculation_explanation()
    
    def show_price_integration_summary(analysis_results):
        """Показывает сводку по ценовой интеграции"""
        enhanced_interface.create_price_integration_summary(analysis_results)
    
    # Привязываем методы к системе
    system.find_and_display_prices = find_and_display_prices
    system.display_enhanced_results = display_enhanced_results  
    system.show_order_calculation_help = show_order_calculation_help
    system.show_price_integration_summary = show_price_integration_summary
    
    # Отмечаем что интерфейс применен
    system._enhanced_warehouse_interface_applied = True
    
    st.success("✅ Улучшенный интерфейс анализа складов подключен!")
    
    return True


def create_enhanced_warehouse_page(system):
    """
    Создает улучшенную страницу анализа складов
    """
    
    st.header("📦 Улучшенный анализ складов")
    st.markdown("*С ценами, MIN/MAX остатками и полным отображением товаров*")
    
    # Применяем улучшенный интерфейс если еще не применен
    if not hasattr(system, '_enhanced_warehouse_interface_applied'):
        apply_enhanced_warehouse_interface(system)
    
    # Проверяем ADS данные
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS на странице 'ADS расчет'")
        return
    
    # Объяснение расчета "к заказу"
    system.show_order_calculation_help()
    
    st.markdown("---")
    
    # Поиск и отображение ценовых данных
    st.subheader("💰 Ценовые данные")
    if st.button("🔍 Найти ценовые данные в системе"):
        with st.spinner("Поиск ценовых данных..."):
            system.find_and_display_prices()
    
    st.markdown("---")
    
    # Если есть результаты анализа, показываем их
    if hasattr(system, '_last_warehouse_analysis') and system._last_warehouse_analysis:
        st.subheader("📊 Результаты последнего анализа")
        
        # Показываем улучшенные результаты
        system.display_enhanced_results(system._last_warehouse_analysis, show_prices=True)
        
        # Показываем ценовую сводку
        system.show_price_integration_summary(system._last_warehouse_analysis)
        
    else:
        st.info("📋 Выполните анализ складов на основной странице анализа, затем вернитесь сюда для просмотра улучшенных результатов")


# Интеграция с существующей системой
def integrate_enhanced_interface_with_warehouse_analysis():
    """
    Интегрирует улучшенный интерфейс с существующим анализом складов
    """
    
    return """
    # Добавьте в вашу функцию warehouse_analysis_page():
    
    # После выполнения анализа добавьте:
    if analysis_results:
        # Сохраняем результаты для улучшенного интерфейса
        system._last_warehouse_analysis = analysis_results
        
        # Показываем кнопку для улучшенного просмотра
        if st.button("🚀 Показать улучшенный интерфейс"):
            from enhanced_warehouse_interface import apply_enhanced_warehouse_interface
            
            if not hasattr(system, '_enhanced_warehouse_interface_applied'):
                apply_enhanced_warehouse_interface(system)
            
            system.display_enhanced_results(analysis_results, show_prices=True)
            system.show_price_integration_summary(analysis_results)
    """


if __name__ == "__main__":
    print("🎯 Улучшенный интерфейс анализа складов загружен")
    print("Функции: цены + MIN/MAX + полное отображение + объяснение расчетов")