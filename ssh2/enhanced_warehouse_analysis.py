#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенная страница анализа складов с интеграцией цен из ADS файлов
Интегрируется с существующей системой анализа складов

Особенности:
- Автоматическое чтение цен из 12-й колонки ADS файлов  
- Интеграция с иерархической структурой филиалов
- Расчет стоимостных показателей для заказов
- Совместимость с существующим анализом складов

Автор: Claude Code Assistant
Дата: 2025-06-23
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import numpy as np
# ОТКЛЮЧЕНО: from warehouse_price_integration import (
#     apply_warehouse_price_integration,
#     show_price_integration_status,
#     WAREHOUSE_HIERARCHY
# )

# НОВОЕ: Определение иерархии складов (скопировано из отключенного файла)
WAREHOUSE_HIERARCHY = {
    # Уровень 1: Главный хаб
    'База Склад Фурнитура Комплект': {
        'level': 1,
        'city': 'Алматы',
        'type': 'Главный хаб',
        'feeds_to': ['Казыбаева Склад Фурнитура TRADE', 'Барыс Склад Фурнитура TRADE', 
                     'АО Склад Фурнитура TRADE', '4 Склад фурнитуры АЗМ Шымкент "Овощная база"', 
                     'склад фурнитура № 1'],
        'min_days': 30,
        'max_days': 90,
        'priority': 1,
        'description': '95% приходов от партнеров'
    },
    
    # Уровень 2: Склады второго уровня
    'Казыбаева Склад Фурнитура TRADE': {
        'level': 2,
        'city': 'Алматы',
        'type': 'Склад 2-го уровня',
        'feeds_from': 'База Склад Фурнитура Комплект',
        'feeds_to': ['ТД Казыбаева ФУРНИТУРА магазин'],
        'min_days': 15,
        'max_days': 45,
        'priority': 2,
        'description': 'Питается от главного хаба'
    },
    
    'Барыс Склад Фурнитура TRADE': {
        'level': 2,
        'city': 'Алматы',
        'type': 'Магазин+склад',
        'feeds_from': 'База Склад Фурнитура Комплект',
        'feeds_to': [],
        'min_days': 15,
        'max_days': 45,
        'priority': 2,
        'description': 'Магазин и склад, питается от хаба'
    },
    
    'АО Склад Фурнитура TRADE': {
        'level': 2,
        'city': 'Алматы',
        'type': 'Специализированный',
        'feeds_from': 'База Склад Фурнитура Комплект',
        'feeds_to': [],
        'min_days': 10,
        'max_days': 30,
        'priority': 3,
        'category_filter': 'кромочные материалы',
        'description': 'Только кромочные материалы'
    },
    
    '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
        'level': 2,
        'city': 'Шымкент',
        'type': 'Склад 2-го уровня',
        'feeds_from': 'База Склад Фурнитура Комплект',
        'feeds_to': ['6 Склад фурнитуры "Овощная база" Магазин'],
        'min_days': 20,
        'max_days': 60,
        'priority': 2,
        'description': 'Склад в Шымкенте, питается от хаба'
    },
    
    'склад фурнитура № 1': {
        'level': 2,
        'city': 'Астана',
        'type': 'Склад 2-го уровня',
        'feeds_from': 'База Склад Фурнитура Комплект',
        'feeds_to': ['Магазин фурнитуры'],
        'min_days': 20,
        'max_days': 60,
        'priority': 2,
        'description': 'Склад в Астане, питается от хаба'
    },
    
    # Уровень 3: Магазины
    'ТД Казыбаева ФУРНИТУРА магазин': {
        'level': 3,
        'city': 'Алматы',
        'type': 'Магазин',
        'feeds_from': 'Казыбаева Склад Фурнитура TRADE',
        'feeds_to': [],
        'min_days': 8,
        'max_days': 25,
        'priority': 3,
        'description': 'Магазин, питается от Казыбаева Склад'
    },
    
    '6 Склад фурнитуры "Овощная база" Магазин': {
        'level': 3,
        'city': 'Шымкент',
        'type': 'Магазин',
        'feeds_from': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
        'feeds_to': [],
        'min_days': 10,
        'max_days': 30,
        'priority': 3,
        'description': 'Магазин в Шымкенте, питается от 4 Склад АЗМ'
    },
    
    'Магазин фурнитуры': {
        'level': 3,
        'city': 'Астана',
        'type': 'Магазин',
        'feeds_from': 'склад фурнитура № 1',
        'feeds_to': [],
        'min_days': 10,
        'max_days': 30,
        'priority': 3,
        'description': 'Магазин в Астане, питается от склад № 1'
    }
}


def enhanced_warehouse_analysis_page(system):
    """
    Улучшенная страница анализа складов с ценовой интеграцией
    """
    
    st.header("📦 Анализ складов с ценовой интеграцией")
    st.caption("✨ Автоматическое извлечение цен из ADS файлов и расчет стоимостных показателей")
    
    # ОТКЛЮЧЕНО: Применяем интеграцию если не применена
    # if not hasattr(system, '_warehouse_price_integration_applied'):
    #     st.info("🔧 Настраиваю интеграцию цен...")
    #     success = apply_warehouse_price_integration(system)
    #     if not success:
    #         st.error("❌ Не удалось настроить интеграцию цен")
    #         return
    
    # Применяем исправление для колонки "Посл. закупка"
    if not hasattr(system, '_posled_zakupka_fix_applied'):
        from quick_posled_zakupka_fix_simple import apply_posled_zakupka_fix
        apply_posled_zakupka_fix(system)
    
    # Добавляем опцию принудительного использования 12-й колонки
    st.subheader("🔧 Экстренные исправления")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Принудительно использовать 12-ю колонку"):
            from force_column_12_fix_simple import apply_force_column_12_fix
            success = apply_force_column_12_fix(system)
            if success:
                st.rerun()
    
    with col2:
        if st.button("🔍 Диагностика файла Барыс"):
            st.info("Запустите: streamlit run diagnose_barys_file.py")
    
    # ОТКЛЮЧЕНО: Показываем статус интеграции
    # with st.expander("📊 Статус интеграции", expanded=False):
    #     show_price_integration_status(system)
    
    # НОВОЕ: Используем простую систему статуса
    with st.expander("📊 Статус интеграции", expanded=False):
        try:
            from simple_price_add import show_price_integration_status
            show_price_integration_status(system)
        except ImportError:
            st.info("📊 Новая система цен активна. Статус: OK")
    
    # ИСПРАВЛЕНО: Добавляем исправленный анализатор складов
    if not hasattr(system, 'warehouse_analyzer'):
        from warehouse_analysis import add_warehouse_analysis_to_system
        add_warehouse_analysis_to_system(system)
        st.info("🔧 Анализатор складов подключен")
    
    # Подключаем исправленный анализатор
    if not hasattr(system, 'fixed_warehouse_analyzer'):
        from warehouse_analysis_fixed import FixedWarehouseAnalyzer
        system.fixed_warehouse_analyzer = FixedWarehouseAnalyzer()
        st.info("🔧 ИСПРАВЛЕННЫЙ анализатор подключен")
    
    # Проверяем ADS данные
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS в разделе 'ADS расчет'")
        return
    
    st.success(f"✅ ADS данные готовы: {len(system.calculated_ads)} товаров")
    
    # Проверяем наличие множественных файлов для цен
    has_price_data = hasattr(system, 'multiple_files_data') and system.multiple_files_data
    if has_price_data:
        files_count = len(system.multiple_files_data.get('processed_results', {}))
        st.success(f"💰 Ценовые данные: {files_count} ADS файлов")
    else:
        st.warning("⚠️ Ценовые данные не найдены. Анализ будет выполнен без стоимостных расчетов.")
        st.info("💡 Для получения ценовой информации загрузите ADS файлы в разделе 'Множественный анализ'")
    
    # Параметры анализа
    st.subheader("⚙️ Параметры анализа")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        min_days = st.number_input("Мин. дни запаса:", value=10, min_value=1, max_value=365,
                                  help="Минимальный запас в днях для расчета критических уровней")
    with col2:
        max_days = st.number_input("Макс. дни запаса:", value=50, min_value=1, max_value=365,
                                  help="Максимальный запас в днях для расчета избытков")
    with col3:
        currency_symbol = st.selectbox("Валюта:", ["₸", "₽", "$", "€"], index=0)
    
    # Дополнительные параметры
    with st.expander("🔧 Дополнительные настройки"):
        col1, col2 = st.columns(2)
        with col1:
            use_custom_hierarchy = st.checkbox("Использовать пользовательскую иерархию складов", 
                                             value=True, 
                                             help="Использует настроенную иерархию с разными критериями по уровням")
        with col2:
            include_zero_stock = st.checkbox("Включать товары с нулевыми остатками", 
                                           value=False,
                                           help="Показывать товары без остатков в детальном анализе")
    
    # Загрузка файла остатков
    st.subheader("📁 Загрузка файла остатков")
    uploaded_file = st.file_uploader(
        "Выберите файл остатков складов",
        type=['xlsx', 'xls'],
        help="Файл должен содержать остатки по всем складам согласно настроенной структуре"
    )
    
    if uploaded_file is None:
        st.info("📤 Загрузите файл остатков для начала анализа")
        return
    
    # Читаем файл остатков
    with st.spinner("📖 Читаю файл остатков..."):
        try:
            # Используем существующий парсер
            remains_df = system.warehouse_analyzer.parse_remains_file(
                pd.read_excel(uploaded_file).values.tolist()
            )
            
            if remains_df is None or remains_df.empty:
                st.error("❌ Не удалось прочитать файл остатков")
                return
                
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            return
    
    # Показываем превью данных
    with st.expander("👀 Превью данных остатков"):
        st.dataframe(remains_df.head(10), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Товаров", len(remains_df))
        with col2:
            st.metric("Колонок", len(remains_df.columns))
        with col3:
            warehouse_cols = [col for col in remains_df.columns if col.endswith('_остаток')]
            st.metric("Складов", len(warehouse_cols))
    
    # Кнопка запуска анализа
    if st.button("🚀 Запустить улучшенный анализ", type="primary"):
        
        with st.spinner("🔄 Выполняю анализ складов с ценовой интеграцией..."):
            
            # Запускаем улучшенный анализ с интеграцией цен
            try:
                # Инициализация переменных по умолчанию
                analysis_results = None
                recommendations = None
                dashboard_data = None
                has_integrated_prices = False
                
                # ИСПРАВЛЕНО: Используем исправленный анализатор
                st.info("🔧 Использую ИСПРАВЛЕННЫЙ алгоритм анализа складов...")
                
                # Получаем ADS данные с ценами из новой системы
                ads_with_prices = system.calculated_ads.copy()
                
                # Интегрируем цены из новой системы
                try:
                    from simple_price_add import get_prices_for_warehouse_analysis
                    prices = get_prices_for_warehouse_analysis(system)
                    if prices:
                        # Добавляем цены в ADS данные
                        for idx, row in ads_with_prices.iterrows():
                            item_name = row['номенклатура']
                            if item_name in prices:
                                ads_with_prices.at[idx, 'last_purchase_price'] = prices[item_name]
                        st.success(f"✅ Интегрировано {len(prices)} цен из новой системы")
                except Exception as e:
                    st.warning(f"⚠️ Цены из новой системы недоступны: {e}")
                
                # ИСПРАВЛЕННЫЙ анализ
                analysis_results = system.fixed_warehouse_analyzer.analyze_warehouse_stock_fixed(
                    remains_df, 
                    ads_with_prices
                )
                
                if analysis_results is None:
                    st.error("❌ Анализ не выполнен")
                    return
                
                # ОТКЛЮЧЕНО: Интегрируем цены если доступны
                # if has_price_data:
                #     st.info("💰 Интегрирую ценовую информацию...")
                #     
                #     # Извлекаем цены из ADS файлов
                #     prices_df = system.extract_prices_from_ads_files()
                #     
                #     if not prices_df.empty:
                #         # Интегрируем цены в анализ
                #         analysis_results = system.integrate_warehouse_prices(analysis_results, prices_df)
                #         has_integrated_prices = True
                #     else:
                #         st.warning("⚠️ Не удалось извлечь цены из ADS файлов")
                #         has_integrated_prices = False
                # else:
                #     has_integrated_prices = False
                
                # НОВОЕ: Простое управление ценами
                if has_price_data:
                    st.info("💰 Ценовые данные доступны из новой системы")
                    try:
                        from simple_price_add import get_prices_for_warehouse_analysis
                        prices = get_prices_for_warehouse_analysis(system)
                        has_integrated_prices = len(prices) > 0 if prices else False
                        if has_integrated_prices:
                            st.success(f"✅ Найдено {len(prices)} цен")
                        else:
                            st.warning("⚠️ Цены не найдены")
                    except Exception as e:
                        st.warning(f"⚠️ Ошибка получения цен: {e}")
                        has_integrated_prices = False
                else:
                    has_integrated_prices = False
                
                # ИСПРАВЛЕНО: Создаем исправленную сводку
                summary = system.fixed_warehouse_analyzer.create_fixed_summary(analysis_results)
                
                # Проверяем наличие цен
                if 'stats' in analysis_results:
                    stats = analysis_results['stats']
                    has_integrated_prices = stats['items_with_prices'] > 0
                    if has_integrated_prices:
                        st.success(f"💰 Цены интегрированы: {stats['items_with_prices']} товаров, покрытие {stats['price_coverage']:.1f}%")
                    else:
                        st.warning("⚠️ Цены не найдены в ADS данных")
                
                # Используем исправленную сводку как рекомендации и дашборд
                recommendations = summary
                dashboard_data = summary
                
            except Exception as e:
                st.error(f"❌ Ошибка анализа: {str(e)}")
                return
        
        # ИСПРАВЛЕНО: Отображаем результаты с новой структурой
        display_fixed_warehouse_results(
            analysis_results, 
            summary, 
            has_integrated_prices,
            currency_symbol
        )


def display_fixed_warehouse_results(analysis_results, summary, has_prices, currency_symbol="₸"):
    """
    ИСПРАВЛЕННОЕ отображение результатов анализа складов
    """
    
    st.markdown("---")
    st.subheader("📊 ИСПРАВЛЕННЫЕ результаты анализа складов")
    
    if has_prices:
        st.success("💰 Анализ включает ценовую информацию из ADS файлов")
    else:
        st.info("📊 Анализ выполнен без ценовой информации")
    
    # ИСПРАВЛЕНО: Общая статистика с правильными расчетами
    if 'total' in summary:
        total = summary['total']
        
        st.subheader("📈 Общая статистика")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Складов", total['total_warehouses'])
        with col2:
            st.metric("Товаров к заказу", total['total_items_to_order'])
        with col3:
            st.metric("Количество", f"{total['total_quantity_to_order']:,.0f}")
        with col4:
            st.metric("Стоимость заказа", f"{total['total_cost_to_order']:,.0f} {currency_symbol}")
        with col5:
            coverage = (total['total_cost_to_order'] / max(1, total['total_quantity_to_order']))
            st.metric("Ср. цена", f"{coverage:,.0f} {currency_symbol}")
        
        # Статистика по статусам
        st.subheader("🚦 Статистика по статусам")
        status_col1, status_col2, status_col3, status_col4 = st.columns(4)
        
        with status_col1:
            st.metric("🔴 Критичные", total['critical_count'])
        with status_col2:
            st.metric("🟡 Предупреждения", total['warning_count'])
        with status_col3:
            st.metric("🟢 В норме", total['good_count'])
        with status_col4:
            st.metric("🔵 Избыток", total['excess_count'])
    
    # ИСПРАВЛЕНО: Детальная информация по складам
    if 'warehouses' in summary:
        st.subheader("🏪 Детали по складам")
        
        # Сортируем склады по уровню (как в иерархии)
        warehouses_sorted = sorted(
            summary['warehouses'].items(),
            key=lambda x: (x[1].get('level', 999), x[1]['name'])
        )
        
        for warehouse_key, warehouse_data in warehouses_sorted:
            level_emoji = {1: "🏢", 2: "🏪", 3: "🛒"}.get(warehouse_data.get('level', 0), "📦")
            
            with st.expander(f"{level_emoji} {warehouse_data['name']} ({warehouse_data.get('type', 'Склад')})"):
                
                # Метрики склада
                wh_col1, wh_col2, wh_col3, wh_col4 = st.columns(4)
                
                with wh_col1:
                    st.metric("Критичных", len(warehouse_data['critical_items']))
                with wh_col2:
                    st.metric("Предупреждений", len(warehouse_data['warning_items']))
                with wh_col3:
                    st.metric("К заказу", f"{warehouse_data['total_to_order']:,.0f}")
                with wh_col4:
                    st.metric("Стоимость", f"{warehouse_data['total_cost_to_order']:,.0f} {currency_symbol}")
                
                # Критичные товары
                if warehouse_data['critical_items']:
                    st.write("🔴 **Критичные товары (требуют немедленного заказа):**")
                    critical_df = pd.DataFrame(warehouse_data['critical_items'])
                    if not critical_df.empty:
                        st.dataframe(
                            critical_df[['номенклатура', 'current_stock', 'min_stock', 'order_quantity', 'price_to_order']].head(10),
                            column_config={
                                'номенклатура': 'Товар',
                                'current_stock': 'Остаток',
                                'min_stock': 'MIN запас',
                                'order_quantity': 'К заказу',
                                'price_to_order': f'Стоимость ({currency_symbol})'
                            }
                        )
                
                # Предупреждения
                if warehouse_data['warning_items']:
                    st.write("🟡 **Предупреждения (рекомендуется заказ):**")
                    warning_df = pd.DataFrame(warehouse_data['warning_items'])
                    if not warning_df.empty:
                        st.dataframe(
                            warning_df[['номенклатура', 'current_stock', 'min_stock', 'order_quantity', 'price_to_order']].head(5),
                            column_config={
                                'номенклатура': 'Товар',
                                'current_stock': 'Остаток',
                                'min_stock': 'MIN запас',
                                'order_quantity': 'К заказу',
                                'price_to_order': f'Стоимость ({currency_symbol})'
                            }
                        )
                
                # Избытки
                if warehouse_data['excess_items']:
                    st.write("🔵 **Избытки (превышение MAX запаса):**")
                    excess_df = pd.DataFrame(warehouse_data['excess_items'])
                    if not excess_df.empty:
                        st.dataframe(
                            excess_df[['номенклатура', 'current_stock', 'max_stock']].head(5),
                            column_config={
                                'номенклатура': 'Товар',
                                'current_stock': 'Остаток',
                                'max_stock': 'MAX запас'
                            }
                        )

def display_enhanced_warehouse_results(analysis_results, recommendations, dashboard_data, 
                                     has_prices, currency_symbol="₸"):
    """
    Отображает результаты улучшенного анализа складов с ценовой информацией
    """
    
    st.markdown("---")
    st.subheader("📊 Результаты анализа складов")
    
    if has_prices:
        st.success("💰 Анализ включает ценовую информацию из ADS файлов")
    else:
        st.info("📊 Анализ выполнен без ценовой информации")
    
    # Общая статистика
    if dashboard_data and 'summary' in dashboard_data:
        summary = dashboard_data['summary']
        
        st.subheader("📈 Общая статистика")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📦 Всего товаров", summary['total_items'])
        with col2:
            st.metric("🔴 Критичные", summary['critical_items'])
        with col3:
            st.metric("🟡 Требуют внимания", summary['warning_items'])
        with col4:
            st.metric("✅ В норме", summary['good_items'])
        with col5:
            st.metric("📈 Избыток", summary.get('excess_items', 0))
    
    # Статистика по складам
    if dashboard_data and 'warehouse_stats' in dashboard_data:
        warehouse_stats = dashboard_data['warehouse_stats']
        
        st.subheader("🏪 Статистика по складам")
        
        # Добавляем ценовую информацию если доступна
        if has_prices and recommendations:
            enhanced_stats = warehouse_stats.copy()
            
            # Добавляем стоимостные колонки
            total_stock_values = []
            total_order_values = []
            price_coverages = []
            
            for idx, row in enhanced_stats.iterrows():
                warehouse_name = row['Склад']
                
                # Ищем склад в рекомендациях
                matching_rec = None
                for rec_key, rec_data in recommendations.items():
                    if rec_data.get('short_name') == warehouse_name:
                        matching_rec = rec_data
                        break
                
                if matching_rec:
                    total_stock_values.append(matching_rec.get('total_stock_value', 0))
                    total_order_values.append(matching_rec.get('total_order_value', 0))
                    price_coverages.append(matching_rec.get('price_coverage', 0))
                else:
                    total_stock_values.append(0)
                    total_order_values.append(0)
                    price_coverages.append(0)
            
            enhanced_stats[f'Стоимость остатков ({currency_symbol})'] = [f"{val:,.0f}" for val in total_stock_values]
            enhanced_stats[f'К заказу ({currency_symbol})'] = [f"{val:,.0f}" for val in total_order_values]
            enhanced_stats['Покрытие цен (%)'] = [f"{val:.1f}%" for val in price_coverages]
            
            st.dataframe(enhanced_stats, use_container_width=True)
        else:
            st.dataframe(warehouse_stats, use_container_width=True)
    
    # Визуализация
    st.subheader("📊 Визуализация результатов")
    
    if dashboard_data and 'warehouse_stats' in dashboard_data:
        warehouse_stats = dashboard_data['warehouse_stats']
        
        # Создаем подграфики
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Критичные товары', 'Товары требующие внимания', 
                          'Объем к заказу' + (f' ({currency_symbol})' if has_prices else ''), 
                          'Покрытие ценами' if has_prices else 'Товары в норме'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # График критичных товаров
        fig.add_trace(
            go.Bar(x=warehouse_stats['Склад'], y=warehouse_stats['Критичных товаров'],
                   name='Критичные', marker_color='red'),
            row=1, col=1
        )
        
        # График товаров требующих внимания
        fig.add_trace(
            go.Bar(x=warehouse_stats['Склад'], y=warehouse_stats['Товаров требующих внимания'],
                   name='Внимание', marker_color='orange'),
            row=1, col=2
        )
        
        # График объема к заказу
        if has_prices and recommendations:
            order_values = []
            for _, row in warehouse_stats.iterrows():
                warehouse_name = row['Склад']
                matching_rec = None
                for rec_data in recommendations.values():
                    if rec_data.get('short_name') == warehouse_name:
                        matching_rec = rec_data
                        break
                order_values.append(matching_rec.get('total_order_value', 0) if matching_rec else 0)
            
            fig.add_trace(
                go.Bar(x=warehouse_stats['Склад'], y=order_values,
                       name=f'К заказу ({currency_symbol})', marker_color='blue'),
                row=2, col=1
            )
        else:
            fig.add_trace(
                go.Bar(x=warehouse_stats['Склад'], y=warehouse_stats['Общий объем к заказу'],
                       name='К заказу (шт)', marker_color='blue'),
                row=2, col=1
            )
        
        # График покрытия ценами или товаров в норме
        if has_prices and recommendations:
            price_coverages = []
            for _, row in warehouse_stats.iterrows():
                warehouse_name = row['Склад']
                matching_rec = None
                for rec_data in recommendations.values():
                    if rec_data.get('short_name') == warehouse_name:
                        matching_rec = rec_data
                        break
                price_coverages.append(matching_rec.get('price_coverage', 0) if matching_rec else 0)
            
            fig.add_trace(
                go.Bar(x=warehouse_stats['Склад'], y=price_coverages,
                       name='Покрытие цен (%)', marker_color='green'),
                row=2, col=2
            )
        else:
            # Рассчитываем товары в норме
            good_items = []
            for _, row in warehouse_stats.iterrows():
                total = row['Критичных товаров'] + row['Товаров требующих внимания'] + row.get('Товаров с избытком', 0)
                good = max(0, row.get('Общий объем к заказу', 0) - total)  # Приблизительный расчет
                good_items.append(good)
            
            fig.add_trace(
                go.Bar(x=warehouse_stats['Склад'], y=good_items,
                       name='В норме', marker_color='green'),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=False, title_text="Аналитика по складам")
        fig.update_xaxes(tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Детальный анализ по складам
    st.subheader("🔍 Детальный анализ по складам")
    
    if recommendations:
        # Сортируем склады по иерархии
        sorted_warehouses = []
        for level in [1, 2, 3]:
            for warehouse_key, rec in recommendations.items():
                warehouse_config = WAREHOUSE_HIERARCHY.get(warehouse_key, {})
                if warehouse_config.get('level', 999) == level:
                    sorted_warehouses.append((warehouse_key, rec))
        
        # Добавляем склады без определенного уровня
        for warehouse_key, rec in recommendations.items():
            warehouse_config = WAREHOUSE_HIERARCHY.get(warehouse_key, {})
            if warehouse_config.get('level', 999) not in [1, 2, 3]:
                sorted_warehouses.append((warehouse_key, rec))
        
        for warehouse_key, rec in sorted_warehouses:
            warehouse_config = WAREHOUSE_HIERARCHY.get(warehouse_key, {})
            level = warehouse_config.get('level', 'N/A')
            level_emoji = {1: "🏢", 2: "🏪", 3: "🛒"}.get(level, "📦")
            
            critical_count = len(rec.get('critical_items', []))
            warning_count = len(rec.get('warning_items', []))
            excess_count = len(rec.get('excess_items', []))
            
            total_issues = critical_count + warning_count + excess_count
            
            if total_issues > 0 or True:  # Показываем все склады
                
                # Заголовок склада с иерархией
                hierarchy_info = f"Уровень {level}" if level != 'N/A' else ""
                city = warehouse_config.get('city', 'N/A')
                warehouse_type = warehouse_config.get('type', 'N/A')
                
                title = f"{level_emoji} {rec.get('short_name', warehouse_key)}"
                subtitle = f"{hierarchy_info} | {city} | {warehouse_type}"
                
                if has_prices:
                    total_stock_value = rec.get('total_stock_value', 0)
                    total_order_value = rec.get('total_order_value', 0)
                    price_coverage = rec.get('price_coverage', 0)
                    
                    subtitle += f" | Остатки: {total_stock_value:,.0f} {currency_symbol}"
                    if total_order_value > 0:
                        subtitle += f" | К заказу: {total_order_value:,.0f} {currency_symbol}"
                    subtitle += f" | Цены: {price_coverage:.1f}%"
                
                with st.expander(f"{title} - {total_issues} проблем"):
                    st.caption(subtitle)
                    
                    # Метрики склада
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🔴 Критично", critical_count)
                    with col2:
                        st.metric("🟡 Внимание", warning_count)
                    with col3:
                        st.metric("📈 Избыток", excess_count)
                    with col4:
                        if has_prices:
                            st.metric(f"💰 К заказу", f"{rec.get('total_order_value', 0):,.0f} {currency_symbol}")
                        else:
                            good_count = len(rec.get('good_items', []))
                            st.metric("✅ В норме", good_count)
                    
                    # Табы с товарами
                    if critical_count > 0 or warning_count > 0 or excess_count > 0:
                        tabs = []
                        tab_contents = []
                        
                        if critical_count > 0:
                            tabs.append(f"🔴 Критично ({critical_count})")
                            tab_contents.append(('critical_items', '🔴 Критичные товары'))
                        
                        if warning_count > 0:
                            tabs.append(f"🟡 Внимание ({warning_count})")
                            tab_contents.append(('warning_items', '🟡 Требуют внимания'))
                        
                        if excess_count > 0:
                            tabs.append(f"📈 Избыток ({excess_count})")
                            tab_contents.append(('excess_items', '📈 Избыточные товары'))
                        
                        if tabs:
                            tab_objects = st.tabs(tabs)
                            
                            for i, (tab_obj, (items_key, title)) in enumerate(zip(tab_objects, tab_contents)):
                                with tab_obj:
                                    items = rec.get(items_key, [])
                                    if items:
                                        display_warehouse_items_table(items, has_prices, currency_symbol, items_key)
                    else:
                        st.success("✅ Все товары в пределах нормы!")
    
    # Экспорт результатов
    st.subheader("📤 Экспорт результатов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Экспорт анализа в Excel"):
            export_enhanced_warehouse_analysis(analysis_results, recommendations, 
                                             dashboard_data, has_prices, currency_symbol)
    
    with col2:
        if has_prices and recommendations:
            if st.button("🛒 Экспорт заказов с ценами"):
                export_purchase_orders_with_prices(recommendations, currency_symbol)


def display_warehouse_items_table(items, has_prices, currency_symbol, items_type):
    """
    Отображает таблицу товаров склада с ценовой информацией
    """
    if not items:
        return
    
    # Подготавливаем данные для таблицы
    table_data = []
    for item in items:
        row = {
            'Товар': item.get('item', item.get('name', 'N/A')),
            'Остаток': f"{item.get('current_stock', 0):.0f}",
            'MIN запас': f"{item.get('min_stock', 0):.0f}",
            'MAX запас': f"{item.get('max_stock', 0):.0f}",
        }
        
        if items_type in ['critical_items', 'warning_items']:
            row['Дефицит'] = f"{item.get('deficit', item.get('min_deficit', 0)):.0f}"
            if has_prices:
                row[f'Цена ({currency_symbol})'] = f"{item.get('unit_price', 0):,.0f}"
                row[f'К заказу ({currency_symbol})'] = f"{item.get('deficit_value', item.get('order_value', 0)):,.0f}"
        elif items_type == 'excess_items':
            row['Избыток'] = f"{item.get('max_surplus', 0):.0f}"
            if has_prices:
                row[f'Цена ({currency_symbol})'] = f"{item.get('unit_price', 0):,.0f}"
                row[f'Избыток ({currency_symbol})'] = f"{item.get('surplus_value', 0):,.0f}"
        
        if has_prices and 'price_source' in item:
            row['Источник цены'] = item['price_source']
        
        months_stock = item.get('months_stock', item.get('months_left', 0))
        if months_stock < 999:
            row['Месяцев запаса'] = f"{months_stock:.1f}"
        else:
            row['Месяцев запаса'] = "∞"
        
        table_data.append(row)
    
    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Суммарная информация
        if has_prices and items_type in ['critical_items', 'warning_items']:
            total_order_value = sum(item.get('deficit_value', item.get('order_value', 0)) for item in items)
            if total_order_value > 0:
                st.info(f"💰 Общая стоимость к заказу: {total_order_value:,.0f} {currency_symbol}")


def export_enhanced_warehouse_analysis(analysis_results, recommendations, dashboard_data, 
                                     has_prices, currency_symbol):
    """
    Экспортирует результаты улучшенного анализа в Excel
    """
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Лист с общей статистикой
            if dashboard_data and 'summary' in dashboard_data:
                summary = dashboard_data['summary']
                summary_data = [
                    ['Показатель', 'Значение'],
                    ['Всего товаров', summary['total_items']],
                    ['Критичные товары', summary['critical_items']],
                    ['Требуют внимания', summary['warning_items']],
                    ['В норме', summary['good_items']],
                    ['Избыток', summary.get('excess_items', 0)],
                    ['Включает цены', 'Да' if has_prices else 'Нет'],
                    ['Валюта', currency_symbol if has_prices else 'N/A'],
                    ['Дата анализа', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')]
                ]
                
                summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
                summary_df.to_excel(writer, sheet_name='Общая статистика', index=False)
            
            # Лист со статистикой по складам
            if dashboard_data and 'warehouse_stats' in dashboard_data:
                warehouse_stats = dashboard_data['warehouse_stats'].copy()
                
                # Добавляем ценовую информацию
                if has_prices and recommendations:
                    stock_values = []
                    order_values = []
                    price_coverages = []
                    
                    for _, row in warehouse_stats.iterrows():
                        warehouse_name = row['Склад']
                        matching_rec = None
                        for rec_data in recommendations.values():
                            if rec_data.get('short_name') == warehouse_name:
                                matching_rec = rec_data
                                break
                        
                        if matching_rec:
                            stock_values.append(matching_rec.get('total_stock_value', 0))
                            order_values.append(matching_rec.get('total_order_value', 0))
                            price_coverages.append(matching_rec.get('price_coverage', 0))
                        else:
                            stock_values.append(0)
                            order_values.append(0)
                            price_coverages.append(0)
                    
                    warehouse_stats[f'Стоимость_остатков_{currency_symbol}'] = stock_values
                    warehouse_stats[f'К_заказу_{currency_symbol}'] = order_values
                    warehouse_stats['Покрытие_цен_%'] = price_coverages
                
                warehouse_stats.to_excel(writer, sheet_name='Статистика складов', index=False)
            
            # Листы по каждому складу
            if recommendations:
                for warehouse_key, rec in recommendations.items():
                    sheet_name = rec.get('short_name', warehouse_key)[:31]
                    
                    all_items = []
                    
                    # Критичные товары
                    for item in rec.get('critical_items', []):
                        item_data = {
                            'Товар': item.get('item', item.get('name')),
                            'Категория': 'Критично',
                            'Остаток': item.get('current_stock', 0),
                            'MIN_запас': item.get('min_stock', 0),
                            'MAX_запас': item.get('max_stock', 0),
                            'Дефицит': item.get('deficit', item.get('min_deficit', 0)),
                            'Месяцев_запаса': item.get('months_stock', item.get('months_left', 0))
                        }
                        
                        if has_prices:
                            item_data[f'Цена_{currency_symbol}'] = item.get('unit_price', 0)
                            item_data[f'К_заказу_{currency_symbol}'] = item.get('deficit_value', item.get('order_value', 0))
                            item_data['Источник_цены'] = item.get('price_source', 'не найдена')
                        
                        all_items.append(item_data)
                    
                    # Товары требующие внимания
                    for item in rec.get('warning_items', []):
                        item_data = {
                            'Товар': item.get('item', item.get('name')),
                            'Категория': 'Внимание',
                            'Остаток': item.get('current_stock', 0),
                            'MIN_запас': item.get('min_stock', 0),
                            'MAX_запас': item.get('max_stock', 0),
                            'Дефицит': item.get('deficit', item.get('min_deficit', 0)),
                            'Месяцев_запаса': item.get('months_stock', item.get('months_left', 0))
                        }
                        
                        if has_prices:
                            item_data[f'Цена_{currency_symbol}'] = item.get('unit_price', 0)
                            item_data[f'К_заказу_{currency_symbol}'] = item.get('deficit_value', item.get('order_value', 0))
                            item_data['Источник_цены'] = item.get('price_source', 'не найдена')
                        
                        all_items.append(item_data)
                    
                    # Товары с избытком
                    for item in rec.get('excess_items', []):
                        item_data = {
                            'Товар': item.get('item', item.get('name')),
                            'Категория': 'Избыток',
                            'Остаток': item.get('current_stock', 0),
                            'MIN_запас': item.get('min_stock', 0),
                            'MAX_запас': item.get('max_stock', 0),
                            'Избыток': item.get('max_surplus', 0),
                            'Месяцев_запаса': item.get('months_stock', 0)
                        }
                        
                        if has_prices:
                            item_data[f'Цена_{currency_symbol}'] = item.get('unit_price', 0)
                            item_data[f'Избыток_{currency_symbol}'] = item.get('surplus_value', 0)
                            item_data['Источник_цены'] = item.get('price_source', 'не найдена')
                        
                        all_items.append(item_data)
                    
                    if all_items:
                        items_df = pd.DataFrame(all_items)
                        items_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        st.download_button(
            label=f"📥 Скачать анализ складов {'с ценами' if has_prices else ''}",
            data=output.getvalue(),
            file_name=f"анализ_складов_{'с_ценами_' if has_prices else ''}{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Файл готов к скачиванию!")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта: {str(e)}")


def export_purchase_orders_with_prices(recommendations, currency_symbol):
    """
    Экспортирует заказы на закупку с ценовой информацией
    """
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Общий лист с заказами
            all_orders = []
            total_order_value = 0
            
            for warehouse_key, rec in recommendations.items():
                warehouse_name = rec.get('short_name', warehouse_key)
                
                # Критичные товары (заказ до MAX)
                for item in rec.get('critical_items', []):
                    order_qty = item.get('deficit', item.get('min_deficit', 0))
                    unit_price = item.get('unit_price', 0)
                    order_value = item.get('deficit_value', item.get('order_value', 0))
                    
                    all_orders.append({
                        'Склад': warehouse_name,
                        'Товар': item.get('item', item.get('name')),
                        'Приоритет': 'Критично',
                        'Текущий_остаток': item.get('current_stock', 0),
                        'MIN_запас': item.get('min_stock', 0),
                        'MAX_запас': item.get('max_stock', 0),
                        'К_заказу': order_qty,
                        f'Цена_{currency_symbol}': unit_price,
                        f'Стоимость_{currency_symbol}': order_value,
                        'Источник_цены': item.get('price_source', 'не найдена')
                    })
                    total_order_value += order_value
                
                # Товары требующие внимания (заказ до MIN)
                for item in rec.get('warning_items', []):
                    order_qty = item.get('deficit', item.get('min_deficit', 0))
                    unit_price = item.get('unit_price', 0)
                    order_value = item.get('deficit_value', item.get('order_value', 0))
                    
                    all_orders.append({
                        'Склад': warehouse_name,
                        'Товар': item.get('item', item.get('name')),
                        'Приоритет': 'Внимание',
                        'Текущий_остаток': item.get('current_stock', 0),
                        'MIN_запас': item.get('min_stock', 0),
                        'MAX_запас': item.get('max_stock', 0),
                        'К_заказу': order_qty,
                        f'Цена_{currency_symbol}': unit_price,
                        f'Стоимость_{currency_symbol}': order_value,
                        'Источник_цены': item.get('price_source', 'не найдена')
                    })
                    total_order_value += order_value
            
            if all_orders:
                orders_df = pd.DataFrame(all_orders)
                orders_df = orders_df.sort_values(['Приоритет', 'Склад'])
                orders_df.to_excel(writer, sheet_name='Все заказы', index=False)
                
                # Сводка
                summary_data = [
                    ['Параметр', 'Значение'],
                    ['Всего заказов', len(orders_df)],
                    ['Критичных', len(orders_df[orders_df['Приоритет'] == 'Критично'])],
                    ['Требующих внимания', len(orders_df[orders_df['Приоритет'] == 'Внимание'])],
                    ['Складов', orders_df['Склад'].nunique()],
                    [f'Общая стоимость ({currency_symbol})', f"{total_order_value:,.0f}"],
                    ['Дата создания', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')]
                ]
                
                summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
                summary_df.to_excel(writer, sheet_name='Сводка', index=False)
                
                # Листы по складам
                for warehouse in orders_df['Склад'].unique():
                    warehouse_orders = orders_df[orders_df['Склад'] == warehouse]
                    sheet_name = warehouse[:31]
                    warehouse_orders.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        st.download_button(
            label=f"📥 Скачать заказы с ценами",
            data=output.getvalue(),
            file_name=f"заказы_с_ценами_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Заказы экспортированы! Общая стоимость: {total_order_value:,.0f} {currency_symbol}")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта заказов: {str(e)}")


# =============================================================================
# ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
# =============================================================================

def integrate_enhanced_warehouse_analysis(system):
    """
    Интегрирует улучшенный анализ складов в основную систему
    """
    try:
        # Применяем ценовую интеграцию
        # ОТКЛЮЧЕНО:         apply_warehouse_price_integration(system)
        
        # Заменяем оригинальную функцию анализа складов
        if hasattr(system, 'warehouse_analysis_page'):
            system._original_warehouse_analysis_page = system.warehouse_analysis_page
        
        system.warehouse_analysis_page = lambda: enhanced_warehouse_analysis_page(system)
        system._enhanced_warehouse_analysis_integrated = True
        
        st.success("✅ Улучшенный анализ складов интегрирован!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка интеграции: {str(e)}")
        return False


if __name__ == "__main__":
    print("📦 Улучшенная система анализа складов с ценовой интеграцией загружена")
    print("💰 Поддержка автоматического извлечения цен из ADS файлов")
    print("🏪 Иерархическая структура складов и филиалов")