#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОБНОВЛЕНИЕ Streamlit интерфейса для поддержки денежного выражения дефицита
Добавляет в существующее приложение полную поддержку цен из колонки "Посл. закупка"
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def stock_comparison_page_with_money(system):
    """
    ОБНОВЛЕННАЯ страница сравнения остатков с денежным выражением
    Заменяет существующую функцию stock_comparison_page
    """
    st.header("⚖️💰 Сравнение остатков с денежным выражением")
    
    status = system.get_system_status()
    
    if not status['min_stock_analysis']['calculated']:
        st.warning("⚠️ Сначала необходимо рассчитать минимальные запасы")
        if st.button("📋 Перейти к расчету MIN запасов"):
            st.switch_page("MIN запасы")
        return
    
    # Применяем исправления для работы с ценами
    try:
        from price_integration_fix import apply_price_fixes_to_system
        apply_price_fixes_to_system(system)
    except ImportError:
        st.error("❌ Модуль price_integration_fix не найден. Применим базовую логику.")
    
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
        if st.button("▶️ Выполнить сравнение остатков с денежным расчетом"):
            with st.spinner("Сравнение остатков с минимальными запасами..."):
                comparison_result = system.compare_stock_vs_min()
                
                if comparison_result['success']:
                    st.success("✅ Сравнение завершено с поддержкой денежного выражения!")
                    st.rerun()
                else:
                    st.error(f"❌ {comparison_result['error']}")
        return
    
    # Показываем результаты сравнения с денежными метриками
    comparison_data = system.stock_comparison
    
    st.subheader("📊 Результаты анализа с денежным выражением")
    
    # Проверяем наличие ценовых данных
    has_price_data = 'last_purchase_price' in comparison_data.columns and 'stock_deficit_money' in comparison_data.columns
    
    if has_price_data:
        st.success("✅ Найдены цены из колонки 'Посл. закупка' - показываем денежное выражение")
    else:
        st.warning("⚠️ Цены не найдены - показываем только количественные данные")
    
    # Общая статистика
    total_items = len(comparison_data)
    deficit_items = len(comparison_data[comparison_data['stock_deficit'] > 0])
    critical_items = len(comparison_data[comparison_data['status'] == 'КРИТИЧНО'])
    sufficient_items = len(comparison_data[comparison_data['status'] == 'ДОСТАТОЧНО'])
    
    # Метрики в две строки
    st.subheader("📈 Количественные показатели")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("С дефицитом", f"{deficit_items} ({deficit_items/total_items*100:.1f}%)")
    with col3:
        st.metric("Критично", f"{critical_items} ({critical_items/total_items*100:.1f}%)")
    with col4:
        total_deficit_qty = comparison_data['stock_deficit'].sum()
        st.metric("Общий дефицит (шт)", f"{total_deficit_qty:,.0f}")
    
    # Денежные показатели (если есть данные)
    if has_price_data:
        st.subheader("💰 Денежные показатели")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_deficit_money = comparison_data['stock_deficit_money'].sum()
            st.metric("Общий дефицит (₽)", f"{total_deficit_money:,.2f}")
        
        with col2:
            total_recommended_order_money = comparison_data['recommended_order_money'].sum()
            st.metric("К заказу (₽)", f"{total_recommended_order_money:,.2f}")
        
        with col3:
            items_with_price = len(comparison_data[comparison_data['last_purchase_price'] > 0])
            price_coverage = (items_with_price / total_items) * 100
            st.metric("Покрытие ценами", f"{price_coverage:.1f}%")
        
        with col4:
            if items_with_price > 0:
                avg_price = comparison_data[comparison_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                st.metric("Средняя цена", f"{avg_price:,.2f} ₽")
            else:
                st.metric("Средняя цена", "Нет данных")
        
        # Дополнительная информация о ценах
        deficit_items_with_price = len(comparison_data[
            (comparison_data['stock_deficit'] > 0) & 
            (comparison_data['last_purchase_price'] > 0)
        ])
        
        st.info(f"""
        💰 **Детали по ценам:**
        - Дефицитных товаров с ценами: **{deficit_items_with_price}** из {deficit_items}
        - Источник цен: колонка "Посл. закупка" из ADS файла
        - Денежные расчеты доступны для **{(deficit_items_with_price/deficit_items*100):.1f}%** дефицитных товаров
        """)
    
    # Визуализации
    st.subheader("📊 Визуализация дефицита")
    
    # Создаем визуализации
    visualizations = system.create_visualizations()
    
    # Статус распределения
    if 'stock_status' in visualizations:
        st.plotly_chart(visualizations['stock_status'], use_container_width=True)
    
    # Специальная визуализация с денежным выражением
    if has_price_data:
        deficit_data = comparison_data[comparison_data['stock_deficit'] > 0]
        
        if len(deficit_data) > 0:
            # Топ по денежному дефициту
            top_deficit_money = deficit_data.nlargest(20, 'stock_deficit_money')
            
            # Создаем двойной график
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Дефицит в штуках', 'Дефицит в деньгах'),
                horizontal_spacing=0.15
            )
            
            # График дефицита в штуках
            fig.add_trace(
                go.Bar(
                    y=top_deficit_money['номенклатура'],
                    x=top_deficit_money['stock_deficit'],
                    orientation='h',
                    name='Дефицит (шт)',
                    marker_color='lightcoral',
                    text=top_deficit_money['stock_deficit'],
                    textposition='outside'
                ),
                row=1, col=1
            )
            
            # График дефицита в деньгах
            fig.add_trace(
                go.Bar(
                    y=top_deficit_money['номенклатура'],
                    x=top_deficit_money['stock_deficit_money'],
                    orientation='h',
                    name='Дефицит (₽)',
                    marker_color='gold',
                    text=[f"{x:,.0f} ₽" for x in top_deficit_money['stock_deficit_money']],
                    textposition='outside'
                ),
                row=1, col=2
            )
            
            fig.update_layout(
                title_text="🔝 Топ-20 товаров по дефициту: количество vs денежное выражение",
                height=800,
                showlegend=False
            )
            
            fig.update_xaxes(title_text="Количество (штук)", row=1, col=1)
            fig.update_xaxes(title_text="Денежное выражение (₽)", row=1, col=2)
            fig.update_yaxes(title_text="Товары", row=1, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Обычная визуализация дефицита (если нет денежных данных)
    elif 'deficit_analysis' in visualizations:
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
        if has_price_data:
            min_deficit_money = st.number_input(
                "Минимальный дефицит (₽)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Показать товары с денежным дефицитом больше указанной суммы"
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
    
    if has_price_data and min_deficit_money > 0:
        filtered_data = filtered_data[filtered_data['stock_deficit_money'] >= min_deficit_money]
    elif not has_price_data and 'min_deficit' in locals() and min_deficit > 0:
        filtered_data = filtered_data[filtered_data['stock_deficit'] >= min_deficit]
    
    # Сортировка
    if has_price_data:
        filtered_data = filtered_data.sort_values('stock_deficit_money', ascending=False)
        sort_info = "Сортировка: по денежному дефициту (убывание)"
    else:
        filtered_data = filtered_data.sort_values('stock_deficit', ascending=False)
        sort_info = "Сортировка: по количественному дефициту (убывание)"
    
    st.caption(sort_info)
    
    # Выбираем колонки для отображения
    display_columns = [
        'номенклатура', 'ads', 'min_stock_total', 'total_current_stock', 
        'stock_deficit', 'current_stock_days', 'status', 'order_priority', 'recommended_order'
    ]
    
    column_config = {
        'номенклатура': 'Товар',
        'ads': 'ADS',
        'min_stock_total': 'MIN запас',
        'total_current_stock': 'Текущий остаток',
        'stock_deficit': 'Дефицит (шт)',
        'current_stock_days': 'Дни остатка',
        'status': 'Статус',
        'order_priority': 'Приоритет',
        'recommended_order': 'Рекомендуемый заказ (шт)'
    }
    
    # Добавляем денежные колонки если есть данные
    if has_price_data:
        display_columns.extend([
            'last_purchase_price', 'stock_deficit_money', 'recommended_order_money'
        ])
        column_config.update({
            'last_purchase_price': st.column_config.NumberColumn(
                'Цена (₽)',
                format="%.2f"
            ),
            'stock_deficit_money': st.column_config.NumberColumn(
                'Дефицит (₽)',
                format="%.2f"
            ),
            'recommended_order_money': st.column_config.NumberColumn(
                'К заказу (₽)',
                format="%.2f"
            )
        })
    
    # Отображаем таблицу
    st.dataframe(
        filtered_data[display_columns], 
        use_container_width=True,
        column_config=column_config
    )
    
    if len(filtered_data) != len(comparison_data):
        st.info(f"Показано {len(filtered_data)} из {len(comparison_data)} товаров")
    
    # Быстрая статистика по отфильтрованным данным
    if len(filtered_data) > 0:
        st.subheader("📊 Статистика по отфильтрованным данным")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            filtered_deficit = filtered_data['stock_deficit'].sum()
            st.metric("Дефицит (шт)", f"{filtered_deficit:,.0f}")
        
        with stat_col2:
            if has_price_data:
                filtered_deficit_money = filtered_data['stock_deficit_money'].sum()
                st.metric("Дефицит (₽)", f"{filtered_deficit_money:,.2f}")
            else:
                st.metric("Дефицит (₽)", "Нет данных")
        
        with stat_col3:
            filtered_recommended = filtered_data['recommended_order'].sum()
            st.metric("К заказу (шт)", f"{filtered_recommended:,.0f}")
        
        with stat_col4:
            if has_price_data:
                filtered_recommended_money = filtered_data['recommended_order_money'].sum()
                st.metric("К заказу (₽)", f"{filtered_recommended_money:,.2f}")
            else:
                st.metric("К заказу (₽)", "Нет данных")
    
    # Экспорт результатов
    st.subheader("📤 Экспорт результатов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Экспорт дефицита в Excel", use_container_width=True):
            try:
                # Используем обновленную функцию экспорта с денежными данными
                from price_integration_fix import create_deficit_excel_export
                excel_buffer = create_deficit_excel_export(system)
                
                st.download_button(
                    label="💾 Скачать отчет по дефициту",
                    data=excel_buffer,
                    file_name=f"deficit_report_with_money_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.success("✅ Excel файл с денежными данными готов!")
                
            except Exception as e:
                st.error(f"❌ Ошибка экспорта: {str(e)}")
                
                # Fallback к стандартному экспорту
                try:
                    excel_buffer = system.export_all_results()
                    
                    st.download_button(
                        label="💾 Скачать стандартный отчет",
                        data=excel_buffer,
                        file_name=f"standard_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                except Exception as e2:
                    st.error(f"❌ Ошибка fallback экспорта: {str(e2)}")
    
    with col2:
        if st.button("🔄 Пересчитать с новыми ценами", use_container_width=True):
            if st.button("✅ Подтвердить пересчет"):
                with st.spinner("Пересчет сравнения остатков..."):
                    comparison_result = system.compare_stock_vs_min()
                    
                    if comparison_result['success']:
                        st.success("✅ Пересчет завершен!")
                        st.rerun()
                    else:
                        st.error(f"❌ {comparison_result['error']}")

def add_price_info_to_ads_page(system):
    """
    Добавление информации о ценах на страницу ADS расчета
    """
    if system.calculated_ads is None:
        return
    
    # Проверяем наличие ценовых данных
    if 'last_purchase_price' in system.calculated_ads.columns:
        st.subheader("💰 Информация о ценах")
        
        ads_data = system.calculated_ads
        items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
        items_without_price = len(ads_data[ads_data['last_purchase_price'] == 0])
        total_items = len(ads_data)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("С ценами", f"{items_with_price}")
        
        with col2:
            st.metric("Без цены", f"{items_without_price}")
        
        with col3:
            coverage = (items_with_price / total_items) * 100
            st.metric("Покрытие", f"{coverage:.1f}%")
        
        with col4:
            if items_with_price > 0:
                avg_price = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                st.metric("Средняя цена", f"{avg_price:,.2f} ₽")
            else:
                st.metric("Средняя цена", "0 ₽")
        
        # Дополнительная информация
        st.info(f"""
        💰 **Источник цен:** Колонка 12 "Посл. закупка" из ADS файла
        
        **Статистика:**
        - Товаров с ценами: {items_with_price} из {total_items}
        - Товаров без цены: {items_without_price}
        - Минимальная цена: {ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price'].min():.2f} ₽
        - Максимальная цена: {ads_data['last_purchase_price'].max():.2f} ₽
        """)
        
        # Топ товары по цене
        if items_with_price > 0:
            with st.expander("💎 Топ-10 самых дорогих товаров"):
                top_expensive = ads_data[ads_data['last_purchase_price'] > 0].nlargest(10, 'last_purchase_price')
                
                for i, (_, row) in enumerate(top_expensive.iterrows(), 1):
                    st.write(f"**{i}.** {row['номенклатура'][:50]}...")
                    st.write(f"   💰 Цена: {row['last_purchase_price']:,.2f} ₽ | ADS: {row['ads']:.4f}")
                    st.write("---")
        
        # Расчет потенциальной стоимости запасов
        if 'min_stock_total' in ads_data.columns:
            st.subheader("📊 Расчет стоимости запасов")
            
            # Стоимость текущих запасов (если есть минимальные запасы)
            inventory_value = (ads_data['min_stock_total'] * ads_data['last_purchase_price']).sum()
            monthly_sales_value = (ads_data['ads'] * 30 * ads_data['last_purchase_price']).sum()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Стоимость MIN запасов", 
                    f"{inventory_value:,.2f} ₽",
                    help="Общая стоимость минимальных запасов по закупочным ценам"
                )
            
            with col2:
                st.metric(
                    "Месячные продажи (стоимость)", 
                    f"{monthly_sales_value:,.2f} ₽",
                    help="Стоимость месячных продаж по закупочным ценам"
                )

def update_export_page_with_money(system):
    """
    Обновление страницы экспорта для включения денежных данных
    """
    st.subheader("💰 Экспорт с денежными данными")
    
    # Проверяем наличие ценовых данных
    has_price_data = False
    if (system.calculated_ads is not None and 
        'last_purchase_price' in system.calculated_ads.columns):
        has_price_data = True
    
    if has_price_data:
        st.success("✅ Найдены ценовые данные - экспорт будет включать денежное выражение")
        
        # Статистика по ценам
        ads_data = system.calculated_ads
        items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
        total_items = len(ads_data)
        
        st.info(f"""
        💰 **Денежные данные в экспорте:**
        - Товаров с ценами: {items_with_price}/{total_items}
        - Источник: колонка "Посл. закупка" (колонка 12)
        - Включено: дефицит в ₽, минимальные запасы в ₽, рекомендуемые заказы в ₽
        """)
    else:
        st.warning("⚠️ Ценовые данные не найдены - экспорт будет содержать только количественные показатели")
    
    # Кнопки экспорта
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Полный отчет с деньгами", use_container_width=True):
            with st.spinner("Создание расширенного Excel отчета..."):
                try:
                    excel_buffer = system.export_all_results()
                    
                    st.download_button(
                        label="💾 Скачать полный отчет",
                        data=excel_buffer,
                        file_name=f"full_report_with_money_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success("✅ Полный отчет с денежными данными готов!")
                    
                    # Показываем что включено в отчет
                    st.info("""
                    📋 **Содержимое отчета:**
                    - ABC анализ с ценами
                    - ADS расчеты с ценовыми данными
                    - Минимальные запасы (шт + ₽)
                    - Сравнение остатков (шт + ₽)
                    - Дефицитные товары с денежным выражением
                    - Денежная сводка по статусам
                    - Топ товары по денежному дефициту
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Ошибка создания отчета: {str(e)}")
    
    with col2:
        if st.button("💰 Только дефицит с деньгами", use_container_width=True):
            if system.stock_comparison is not None:
                with st.spinner("Создание отчета по дефициту..."):
                    try:
                        from price_integration_fix import create_deficit_excel_export
                        excel_buffer = create_deficit_excel_export(system)
                        
                        st.download_button(
                            label="💾 Скачать отчет дефицита",
                            data=excel_buffer,
                            file_name=f"deficit_money_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                        st.success("✅ Отчет по дефициту с денежными данными готов!")
                        
                        st.info("""
                        📋 **Содержимое отчета дефицита:**
                        - Все дефицитные товары (шт + ₽)
                        - Критичные товары с приоритизацией по деньгам
                        - Денежная сводка по статусам
                        - Топ-50 товаров по денежному дефициту
                        - Рекомендации по заказу в денежном выражении
                        """)
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка создания отчета дефицита: {str(e)}")
            else:
                st.warning("⚠️ Сравнение остатков не выполнено")

def show_money_integration_status(system):
    """
    Показать статус интеграции денежных данных в системе
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Статус цен")
    
    # Проверяем все компоненты
    checks = {
        "ADS с ценами": False,
        "MIN запасы с ₽": False,
        "Дефицит с ₽": False
    }
    
    # Проверяем ADS
    if (system.calculated_ads is not None and 
        'last_purchase_price' in system.calculated_ads.columns):
        checks["ADS с ценами"] = True
        
        items_with_price = len(system.calculated_ads[system.calculated_ads['last_purchase_price'] > 0])
        total_items = len(system.calculated_ads)
        
        st.sidebar.metric(
            "Товаров с ценами", 
            f"{items_with_price}/{total_items}",
            f"{(items_with_price/total_items*100):.1f}%"
        )
    
    # Проверяем минимальные запасы
    if (system.calculated_min_stock is not None and 
        'last_purchase_price' in system.calculated_min_stock.columns):
        checks["MIN запасы с ₽"] = True
    
    # Проверяем дефицит
    if (system.stock_comparison is not None and 
        'stock_deficit_money' in system.stock_comparison.columns):
        checks["Дефицит с ₽"] = True
        
        # Показываем общий денежный дефицит
        total_deficit_money = system.stock_comparison['stock_deficit_money'].sum()
        st.sidebar.metric(
            "Общий дефицит", 
            f"{total_deficit_money:,.0f} ₽"
        )
    
    # Статус индикаторы
    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        st.sidebar.write(f"{icon} {check_name}")
    
    # Рекомендации
    if not checks["ADS с ценами"]:
        st.sidebar.warning("💡 Загрузите ADS файл с колонкой 'Посл. закупка'")
    elif all(checks.values()):
        st.sidebar.success("🎉 Все денежные расчеты активны!")

def integration_instructions():
    """
    Инструкции по интеграции денежных данных
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📖 Как добавить цены")
    
    with st.sidebar.expander("💡 Инструкция"):
        st.markdown("""
        **Для работы с ценами:**
        
        1. **ADS файл** должен содержать:
           - Колонка B: Номенклатура
           - Колонка 12: "Посл. закупка" (цены)
           - Колонки M-AB: Данные продаж
        
        2. **Загрузите ADS файл** на странице "ADS расчет"
        
        3. **Система автоматически**:
           - Извлечет цены из колонки 12
           - Добавит денежные расчеты
           - Обновит все отчеты
        
        4. **Результат**:
           - Дефицит в ₽
           - MIN запасы в ₽  
           - Приоритизация по деньгам
           - Детальные денежные отчеты
        """)

# ===== ГЛАВНАЯ ФУНКЦИЯ ИНТЕГРАЦИИ =====

def integrate_money_features_to_streamlit_app():
    """
    Главная функция для интеграции денежных функций в Streamlit приложение
    
    Добавьте этот вызов в ваше основное Streamlit приложение:
    
    ```python
    from streamlit_deficit_money_update import integrate_money_features_to_streamlit_app
    
    # В вашей функции main():
    integrate_money_features_to_streamlit_app()
    ```
    """
    
    # Инструкция по применению
    instructions = """
    🔧 ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ ДЕНЕЖНЫХ ФУНКЦИЙ:
    
    1. Замените функцию stock_comparison_page на stock_comparison_page_with_money
    2. Добавьте add_price_info_to_ads_page в ADS страницу  
    3. Обновите export_page с update_export_page_with_money
    4. Добавьте show_money_integration_status в sidebar
    5. Добавьте integration_instructions в sidebar
    
    ПРИМЕР ИНТЕГРАЦИИ:
    
    ```python
    # В основном приложении streamlit_modular_app.py
    
    def main():
        system = init_system()
        
        # Добавляем статус цен в sidebar
        show_money_integration_status(system)
        integration_instructions()
        
        # В зависимости от выбранной страницы:
        if page == "⚖️ Сравнение остатков":
            stock_comparison_page_with_money(system)  # НОВАЯ ФУНКЦИЯ
        elif page == "📊 ADS расчет":
            ads_calculation_page_updated(system)
            add_price_info_to_ads_page(system)  # ДОБАВЛЯЕМ ЦЕНЫ
        elif page == "📤 Экспорт результатов":
            export_page(system)
            update_export_page_with_money(system)  # ДОБАВЛЯЕМ ДЕНЕЖНЫЙ ЭКСПОРТ
    ```
    
    РЕЗУЛЬТАТ:
    ✅ Полная поддержка цен из колонки "Посл. закупка"
    ✅ Дефицит в денежном выражении
    ✅ Сортировка по денежному дефициту  
    ✅ Визуализация количество vs деньги
    ✅ Excel отчеты с денежными данными
    ✅ Статус интеграции в sidebar
    """
    
    return instructions

if __name__ == "__main__":
    print(integrate_money_features_to_streamlit_app())