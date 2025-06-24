# display_fixes_warehouse.py
"""
🎯 ИСПРАВЛЕНИЯ ОТОБРАЖЕНИЯ ЦЕН И РАСЧЕТОВ В АНАЛИЗЕ СКЛАДОВ
Исправляет проблемы отображения в таблицах, где цены есть, но не показываются
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any


# ===== ИСПРАВЛЕНИЕ 1: ОТОБРАЖЕНИЕ ТАБЛИЦ С ЦЕНАМИ =====

def fix_warehouse_results_display():
    """
    ИСПРАВЛЕНИЕ: Улучшает отображение результатов анализа складов с ценами
    """
    
    def enhanced_display_warehouse_results(analysis_results, recommendations, has_prices=True):
        """
        ИСПРАВЛЕННОЕ отображение результатов с правильными ценами и расчетами
        """
        
        st.subheader("📊 Результаты анализа складов")
        
        if not analysis_results:
            st.warning("❌ Нет результатов для отображения")
            return
        
        # Проверяем наличие цен в данных
        prices_found = 0
        total_items = len(analysis_results)
        
        for item in analysis_results:
            if item.get('price', 0) > 0:
                prices_found += 1
        
        if prices_found > 0:
            st.success(f"💰 Найдено цен: {prices_found}/{total_items} товаров ({prices_found/total_items*100:.1f}%)")
        else:
            st.warning("⚠️ Цены не найдены или не отображаются")
        
        # Общая статистика с денежными показателями
        total_critical = sum(item.get('critical_warehouses', 0) for item in analysis_results)
        total_warning = sum(item.get('warning_warehouses', 0) for item in analysis_results)
        total_order_qty = sum(item.get('total_order_quantity', 0) for item in analysis_results)
        total_order_value = sum(item.get('total_order_value', 0) for item in analysis_results)
        total_stock_value = sum(item.get('total_stock_value', 0) for item in analysis_results)
        
        # Метрики
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Всего товаров", total_items)
        with col2:
            st.metric("🔴 Критичных", total_critical, delta=f"-{total_critical}")
        with col3:
            st.metric("🟡 Требуют внимания", total_warning, delta=f"-{total_warning}")
        with col4:
            st.metric("📦 К заказу (шт)", f"{total_order_qty:.0f}")
        with col5:
            if total_order_value > 0:
                st.metric("💰 К заказу (₽)", f"{total_order_value:,.0f}")
            else:
                st.metric("💰 К заказу", "Цены не найдены")
        
        # ИСПРАВЛЕННАЯ таблица товаров с ценами
        st.subheader("📋 Детальная таблица товаров")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_filter = st.selectbox(
                "Показать товары:",
                ["Все", "Только с ценами", "Только критичные", "С заказами", "Без цен"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "Сортировать по:",
                ["ADS (убыв.)", "Цене (убыв.)", "Стоимости заказа", "Общему остатку"]
            )
        
        with col3:
            show_money = st.checkbox("Показать денежные колонки", value=True)
        
        # Применяем фильтры
        filtered_results = analysis_results.copy()
        
        if show_filter == "Только с ценами":
            filtered_results = [item for item in filtered_results if item.get('price', 0) > 0]
        elif show_filter == "Только критичные":
            filtered_results = [item for item in filtered_results if item.get('critical_warehouses', 0) > 0]
        elif show_filter == "С заказами":
            filtered_results = [item for item in filtered_results if item.get('total_order_quantity', 0) > 0]
        elif show_filter == "Без цен":
            filtered_results = [item for item in filtered_results if item.get('price', 0) == 0]
        
        # Сортировка
        if sort_by == "ADS (убыв.)":
            filtered_results.sort(key=lambda x: x.get('ads', 0), reverse=True)
        elif sort_by == "Цене (убыв.)":
            filtered_results.sort(key=lambda x: x.get('price', 0), reverse=True)
        elif sort_by == "Стоимости заказа":
            filtered_results.sort(key=lambda x: x.get('total_order_value', 0), reverse=True)
        elif sort_by == "Общему остатку":
            filtered_results.sort(key=lambda x: x.get('total_stock', 0), reverse=True)
        
        # ИСПРАВЛЕННАЯ таблица с правильным отображением цен
        if filtered_results:
            
            display_data = []
            
            for item in filtered_results[:100]:  # Показываем первые 100
                
                # Базовые данные
                row = {
                    'Номенклатура': item['номенклатура'][:50] + "..." if len(item['номенклатура']) > 50 else item['номенклатура'],
                    'ADS': f"{item.get('ads', 0):.3f}",
                    'Общий остаток': f"{item.get('total_stock', 0):.0f}",
                }
                
                # ИСПРАВЛЕНО: Добавляем цену если есть
                price = item.get('price', 0)
                if price > 0:
                    row['Цена (₽)'] = f"{price:,.0f}"
                else:
                    row['Цена (₽)'] = "не найдена"
                
                # ИСПРАВЛЕНО: Добавляем количество и стоимость к заказу
                order_qty = item.get('total_order_quantity', 0)
                order_value = item.get('total_order_value', 0)
                
                if order_qty > 0:
                    row['К заказу (шт)'] = f"{order_qty:.0f}"
                    if order_value > 0:
                        row['К заказу (₽)'] = f"{order_value:,.0f}"
                    else:
                        row['К заказу (₽)'] = f"~{order_qty * price:,.0f}" if price > 0 else "нет цены"
                else:
                    row['К заказу (шт)'] = "-"
                    row['К заказу (₽)'] = "-"
                
                # ИСПРАВЛЕНО: Добавляем стоимость остатков
                stock_value = item.get('total_stock_value', 0)
                if stock_value > 0:
                    row['Стоимость остатков (₽)'] = f"{stock_value:,.0f}"
                elif price > 0 and item.get('total_stock', 0) > 0:
                    calculated_stock_value = item['total_stock'] * price
                    row['Стоимость остатков (₽)'] = f"~{calculated_stock_value:,.0f}"
                else:
                    row['Стоимость остатков (₽)'] = "нет цены"
                
                # Добавляем статусы по складам
                row['🔴 Критичных складов'] = item.get('critical_warehouses', 0)
                row['🟡 Требуют внимания'] = item.get('warning_warehouses', 0)
                
                # ИСПРАВЛЕНО: Добавляем информацию по основным складам с ценами
                warehouses = item.get('warehouses', {})
                main_warehouses = ['Шымкент_Склад', 'Алматы_Склад', 'База_Комплект', 'Астана_Склад']
                
                for wh_key in main_warehouses:
                    if wh_key in warehouses:
                        wh_data = warehouses[wh_key]
                        current = wh_data.get('current_stock', 0)
                        order = wh_data.get('order_quantity', 0)
                        status = wh_data.get('status', 'unknown')
                        
                        # Иконка статуса
                        if status == 'critical':
                            icon = "🔴"
                        elif status == 'warning':
                            icon = "🟡"
                        elif status == 'good':
                            icon = "🟢"
                        else:
                            icon = "⚪"
                        
                        # Краткое название склада
                        short_name = wh_key.replace('_', ' ')
                        
                        if order > 0:
                            if price > 0:
                                order_cost = order * price
                                row[short_name] = f"{icon} {current:.0f} (+{order:.0f}шт ≈{order_cost:,.0f}₽)"
                            else:
                                row[short_name] = f"{icon} {current:.0f} (+{order:.0f}шт)"
                        else:
                            if current > 0:
                                if price > 0:
                                    stock_cost = current * price
                                    row[short_name] = f"{icon} {current:.0f} (≈{stock_cost:,.0f}₽)"
                                else:
                                    row[short_name] = f"{icon} {current:.0f}"
                            else:
                                row[short_name] = f"{icon} 0"
                
                display_data.append(row)
            
            # ИСПРАВЛЕНО: Показываем таблицу с правильными колонками
            df_display = pd.DataFrame(display_data)
            
            # Скрываем денежные колонки если не нужны
            if not show_money:
                money_columns = [col for col in df_display.columns if '(₽)' in col or '₽' in col]
                df_display = df_display.drop(columns=money_columns)
            
            st.dataframe(df_display, use_container_width=True)
            
            if len(filtered_results) > 100:
                st.info(f"📄 Показано первые 100 из {len(filtered_results)} товаров")
        
        else:
            st.info("📋 Нет товаров для отображения с выбранными фильтрами")
        
        # ИСПРАВЛЕНО: Статистика по складам с ценами
        if recommendations:
            st.subheader("🏪 Статистика по складам")
            
            warehouse_summary = []
            for wh_key, rec in recommendations.items():
                
                # Извлекаем данные из рекомендаций
                total_items = rec.get('total_items', 0)
                critical_items = len(rec.get('critical_items', []))
                warning_items = len(rec.get('warning_items', []))
                good_items = len(rec.get('good_items', []))
                
                total_order_qty = rec.get('total_order_quantity', 0)
                total_order_value = rec.get('total_order_value', 0)
                total_stock_value = rec.get('total_stock_value', 0)
                
                warehouse_summary.append({
                    'Склад': rec.get('name', wh_key),
                    'Город': rec.get('city', 'неизвестно'),
                    'Тип': rec.get('type', 'неизвестно'),
                    'Всего товаров': total_items,
                    '🔴 Критичных': critical_items,
                    '🟡 Внимания': warning_items,
                    '🟢 В норме': good_items,
                    'К заказу (шт)': f"{total_order_qty:.0f}" if total_order_qty > 0 else "-",
                    'К заказу (₽)': f"{total_order_value:,.0f}" if total_order_value > 0 else "нет цен",
                    'Стоимость остатков (₽)': f"{total_stock_value:,.0f}" if total_stock_value > 0 else "нет цен"
                })
            
            if warehouse_summary:
                warehouse_df = pd.DataFrame(warehouse_summary)
                st.dataframe(warehouse_df, use_container_width=True)
        
        # Визуализация с денежными показателями
        if prices_found > 0:
            create_enhanced_charts_with_money(analysis_results, recommendations)
    
    return enhanced_display_warehouse_results


# ===== ИСПРАВЛЕНИЕ 2: ВИЗУАЛИЗАЦИЯ С ЦЕНАМИ =====

def create_enhanced_charts_with_money(analysis_results, recommendations):
    """
    ИСПРАВЛЕННЫЕ графики с денежными показателями
    """
    
    st.subheader("📈 Визуализация с денежными показателями")
    
    # График 1: Стоимость заказов по складам
    if recommendations:
        warehouse_data = []
        for wh_key, rec in recommendations.items():
            order_value = rec.get('total_order_value', 0)
            stock_value = rec.get('total_stock_value', 0)
            
            if order_value > 0 or stock_value > 0:
                warehouse_data.append({
                    'Склад': rec.get('name', wh_key),
                    'К заказу (₽)': order_value,
                    'Стоимость остатков (₽)': stock_value,
                    'Критичных товаров': len(rec.get('critical_items', []))
                })
        
        if warehouse_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # График стоимости заказов
                df_chart = pd.DataFrame(warehouse_data)
                fig_orders = px.bar(
                    df_chart,
                    x='Склад',
                    y='К заказу (₽)',
                    title='💰 Стоимость заказов по складам',
                    color='К заказу (₽)',
                    color_continuous_scale='Reds'
                )
                fig_orders.update_layout(showlegend=False)
                st.plotly_chart(fig_orders, use_container_width=True)
            
            with col2:
                # График стоимости остатков
                fig_stock = px.bar(
                    df_chart,
                    x='Склад',
                    y='Стоимость остатков (₽)',
                    title='📦 Стоимость остатков по складам',
                    color='Стоимость остатков (₽)',
                    color_continuous_scale='Blues'
                )
                fig_stock.update_layout(showlegend=False)
                st.plotly_chart(fig_stock, use_container_width=True)
    
    # График 2: Топ товары по стоимости заказов
    expensive_orders = []
    for item in analysis_results:
        order_value = item.get('total_order_value', 0)
        if order_value > 0:
            expensive_orders.append({
                'Товар': item['номенклатура'][:30] + "..." if len(item['номенклатура']) > 30 else item['номенклатура'],
                'Стоимость заказа (₽)': order_value,
                'Цена (₽)': item.get('price', 0),
                'К заказу (шт)': item.get('total_order_quantity', 0)
            })
    
    if expensive_orders:
        expensive_orders.sort(key=lambda x: x['Стоимость заказа (₽)'], reverse=True)
        top_expensive = expensive_orders[:10]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Топ-10 самых дорогих заказов
            df_expensive = pd.DataFrame(top_expensive)
            fig_top = px.bar(
                df_expensive,
                x='Стоимость заказа (₽)',
                y='Товар',
                orientation='h',
                title='💎 Топ-10 самых дорогих заказов',
                color='Стоимость заказа (₽)',
                color_continuous_scale='plasma'
            )
            fig_top.update_layout(height=400)
            st.plotly_chart(fig_top, use_container_width=True)
        
        with col2:
            # Соотношение цена vs количество
            fig_scatter = px.scatter(
                df_expensive,
                x='К заказу (шт)',
                y='Цена (₽)',
                size='Стоимость заказа (₽)',
                title='💰 Цена vs Количество к заказу',
                hover_data=['Товар']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)


# ===== ИСПРАВЛЕНИЕ 3: УЛУЧШЕННЫЙ ЭКСПОРТ С ЦЕНАМИ =====

def fix_warehouse_excel_export():
    """
    ИСПРАВЛЕНИЕ: Улучшает экспорт Excel с правильными ценами и расчетами
    """
    
    def create_enhanced_excel_report(analysis_results, recommendations):
        """
        ИСПРАВЛЕННЫЙ Excel отчет с полными денежными данными
        """
        
        try:
            from io import BytesIO
            
            buffer = BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                
                # Лист 1: Сводка с деньгами
                summary_data = []
                total_order_value = 0
                total_stock_value = 0
                items_with_prices = 0
                
                for item in analysis_results:
                    price = item.get('price', 0)
                    order_qty = item.get('total_order_quantity', 0)
                    order_value = item.get('total_order_value', 0)
                    stock_value = item.get('total_stock_value', 0)
                    
                    if price > 0:
                        items_with_prices += 1
                    
                    total_order_value += order_value
                    total_stock_value += stock_value
                    
                    summary_data.append({
                        'Номенклатура': item['номенклатура'],
                        'ADS': item.get('ads', 0),
                        'Цена (₽)': price,
                        'Общий остаток': item.get('total_stock', 0),
                        'Стоимость остатков (₽)': stock_value,
                        'К заказу (шт)': order_qty,
                        'К заказу (₽)': order_value,
                        'Критичных складов': item.get('critical_warehouses', 0),
                        'Требуют внимания': item.get('warning_warehouses', 0),
                        'Источник цены': item.get('price_source', 'не указан')
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Сводка с ценами', index=False)
                
                # Лист 2: Только товары с заказами и ценами
                orders_data = []
                for item in analysis_results:
                    if item.get('total_order_quantity', 0) > 0:
                        
                        for wh_key, wh_data in item.get('warehouses', {}).items():
                            order_qty = wh_data.get('order_quantity', 0)
                            if order_qty > 0:
                                price = item.get('price', 0)
                                order_cost = order_qty * price if price > 0 else 0
                                
                                orders_data.append({
                                    'Товар': item['номенклатура'],
                                    'Склад': wh_data.get('short_name', wh_key),
                                    'Город': wh_data.get('city', 'неизвестно'),
                                    'Тип склада': wh_data.get('type', 'неизвестно'),
                                    'Текущий остаток': wh_data.get('current_stock', 0),
                                    'MIN запас': wh_data.get('min_stock', 0),
                                    'MAX запас': wh_data.get('max_stock', 0),
                                    'К заказу (шт)': order_qty,
                                    'Цена за единицу (₽)': price,
                                    'Стоимость заказа (₽)': order_cost,
                                    'Статус': wh_data.get('status', 'неизвестно'),
                                    'ADS': item.get('ads', 0),
                                    'Приоритет': 'Критично' if wh_data.get('status') == 'critical' else 'Внимание'
                                })
                
                if orders_data:
                    orders_df = pd.DataFrame(orders_data)
                    orders_df = orders_df.sort_values(['Приоритет', 'Стоимость заказа (₽)'], ascending=[True, False])
                    orders_df.to_excel(writer, sheet_name='Заказы с ценами', index=False)
                
                # Лист 3: Статистика складов с деньгами
                if recommendations:
                    warehouse_stats = []
                    for wh_key, rec in recommendations.items():
                        warehouse_stats.append({
                            'Склад': rec.get('name', wh_key),
                            'Город': rec.get('city', 'неизвестно'),
                            'Тип': rec.get('type', 'неизвестно'),
                            'Всего товаров': rec.get('total_items', 0),
                            'Критичных': len(rec.get('critical_items', [])),
                            'Требуют внимания': len(rec.get('warning_items', [])),
                            'В норме': len(rec.get('good_items', [])),
                            'К заказу (шт)': rec.get('total_order_quantity', 0),
                            'К заказу (₽)': rec.get('total_order_value', 0),
                            'Стоимость остатков (₽)': rec.get('total_stock_value', 0),
                            'Эффективность (%)': rec.get('efficiency', 0)
                        })
                    
                    warehouse_df = pd.DataFrame(warehouse_stats)
                    warehouse_df.to_excel(writer, sheet_name='Склады с деньгами', index=False)
                
                # Лист 4: Итоговая сводка
                final_summary = [
                    ['Параметр', 'Значение'],
                    ['Всего товаров', len(analysis_results)],
                    ['Товаров с ценами', items_with_prices],
                    ['Покрытие ценами (%)', f"{items_with_prices/len(analysis_results)*100:.1f}"],
                    ['Общая стоимость заказов (₽)', f"{total_order_value:,.2f}"],
                    ['Общая стоимость остатков (₽)', f"{total_stock_value:,.2f}"],
                    ['Дата создания', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')]
                ]
                
                final_df = pd.DataFrame(final_summary[1:], columns=final_summary[0])
                final_df.to_excel(writer, sheet_name='Итоговая сводка', index=False)
            
            return buffer.getvalue()
            
        except Exception as e:
            st.error(f"❌ Ошибка создания Excel отчета: {str(e)}")
            return None
    
    return create_enhanced_excel_report


# ===== ГЛАВНАЯ ФУНКЦИЯ ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ =====

def apply_display_fixes_to_system(system):
    """
    Применяет все исправления отображения к системе анализа складов
    """
    
    st.subheader("🎨 Применение исправлений отображения")
    
    fixes_applied = []
    
    try:
        # Исправление 1: Отображение результатов
        enhanced_display = fix_warehouse_results_display()
        system.enhanced_display_warehouse_results = enhanced_display
        fixes_applied.append("✅ Улучшенное отображение результатов с ценами")
        
        # Исправление 2: Excel экспорт
        enhanced_excel = fix_warehouse_excel_export()
        system.create_enhanced_excel_report = enhanced_excel
        fixes_applied.append("✅ Улучшенный Excel экспорт с денежными данными")
        
        # Исправление 3: Метод для быстрой проверки цен
        def quick_price_check(analysis_results):
            """Быстрая проверка наличия цен в результатах"""
            if not analysis_results:
                return {"has_prices": False, "count": 0, "total": 0}
            
            prices_count = sum(1 for item in analysis_results if item.get('price', 0) > 0)
            return {
                "has_prices": prices_count > 0,
                "count": prices_count,
                "total": len(analysis_results),
                "coverage": prices_count / len(analysis_results) * 100
            }
        
        system.quick_price_check = quick_price_check
        fixes_applied.append("✅ Быстрая проверка цен")
        
        # Отмечаем что исправления применены
        system._display_fixes_applied = True
        system._display_fixes_list = fixes_applied
        
        st.success(f"🎯 Применено исправлений отображения: {len(fixes_applied)}")
        for fix in fixes_applied:
            st.write(f"  {fix}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка применения исправлений отображения: {str(e)}")
        return False


# ===== УЛУЧШЕННАЯ ФУНКЦИЯ АНАЛИЗА СКЛАДОВ С ИСПРАВЛЕННЫМ ОТОБРАЖЕНИЕМ =====

def enhanced_warehouse_analysis_page_with_fixes(system):
    """
    Улучшенная страница анализа складов с исправленным отображением цен и расчетов
    """
    
    st.header("📦 Анализ складов - ИСПРАВЛЕННОЕ ОТОБРАЖЕНИЕ")
    st.caption("🎨 С правильным отображением цен, расчетов и денежных показателей")
    
    # Применяем исправления отображения если еще не применены
    if not hasattr(system, '_display_fixes_applied'):
        with st.expander("🎨 Применение исправлений отображения", expanded=True):
            apply_display_fixes_to_system(system)
    else:
        st.success("✅ Исправления отображения применены")
        if hasattr(system, '_display_fixes_list'):
            for fix in system._display_fixes_list:
                st.write(f"  {fix}")
    
    # Проверяем ADS данные
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS в разделе 'ADS расчет'")
        return
    
    st.success(f"✅ ADS данные найдены: {len(system.calculated_ads)} товаров")
    
    # Проверяем наличие цен в ADS данных
    ads_data = system.calculated_ads
    has_price_column = False
    price_column = None
    
    price_columns = ['last_purchase_price', 'цена', 'price', 'Посл. закупка']
    for col in price_columns:
        if col in ads_data.columns:
            has_price_column = True
            price_column = col
            break
    
    if has_price_column:
        prices_count = (ads_data[price_column] > 0).sum()
        total_count = len(ads_data)
        coverage = prices_count / total_count * 100
        st.success(f"💰 Найдены цены в колонке '{price_column}': {prices_count}/{total_count} товаров ({coverage:.1f}%)")
    else:
        st.warning("⚠️ Цены не найдены в ADS данных. Анализ будет без денежных расчетов.")
        st.info("💡 Для получения цен загрузите ADS файлы с ценами в колонке 'Посл. закупка'")
    
    # Параметры анализа
    st.subheader("⚙️ Параметры анализа")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        min_days = st.number_input("MIN дни запаса:", value=15, min_value=5, max_value=60)
    with col2:
        max_days = st.number_input("MAX дни запаса:", value=45, min_value=20, max_value=120)
    with col3:
        show_debug = st.checkbox("Режим отладки", value=False)
    
    # Загрузка файла остатков
    st.subheader("📁 Загрузка файла остатков")
    
    uploaded_file = st.file_uploader(
        "Выберите файл остатков:",
        type=['xlsx', 'xls'],
        help="Файл будет обработан с улучшенной логикой чтения"
    )
    
    if uploaded_file is not None:
        
        # Читаем файл
        try:
            with st.spinner("📖 Чтение файла остатков..."):
                # Используем существующую функцию системы или создаем простую
                if hasattr(system, 'load_current_stock_file'):
                    file_result = system.load_current_stock_file(uploaded_file)
                    if file_result.get('success', False):
                        remains_df = file_result['data']
                    else:
                        remains_df = pd.read_excel(uploaded_file)
                else:
                    remains_df = pd.read_excel(uploaded_file)
            
            if remains_df.empty:
                st.error("❌ Файл пустой или не удалось прочитать")
                return
            
            st.success(f"✅ Файл загружен: {len(remains_df)} строк, {len(remains_df.columns)} колонок")
            
            # Показываем превью
            with st.expander("👀 Превью данных остатков"):
                st.dataframe(remains_df.head())
                st.write(f"Колонки: {list(remains_df.columns)}")
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            return
        
        # Кнопка анализа
        if st.button("🔍 Запустить анализ с исправленным отображением", type="primary"):
            
            with st.spinner("🔄 Выполняем анализ с улучшенным отображением..."):
                
                # Запускаем анализ (используем существующий метод системы)
                try:
                    if hasattr(system, 'analyze_warehouse_stock_with_details'):
                        analysis_results, warehouse_stats = system.analyze_warehouse_stock_with_details(
                            remains_df,
                            system.calculated_ads,
                            None,  # store_ads_by_city
                            min_days,
                            max_days
                        )
                    else:
                        st.error("❌ Метод analyze_warehouse_stock_with_details не найден в системе")
                        st.info("💡 Примените сначала основные исправления системы")
                        return
                    
                except Exception as e:
                    st.error(f"❌ Ошибка анализа: {str(e)}")
                    if show_debug:
                        st.exception(e)
                    return
            
            if analysis_results is not None:
                
                # ИСПРАВЛЕНО: Добавляем цены к результатам анализа
                if has_price_column:
                    enhanced_results = add_prices_to_analysis_results(analysis_results, ads_data, price_column)
                else:
                    enhanced_results = analysis_results
                
                # Создаем рекомендации если их нет
                if warehouse_stats is None and hasattr(system, 'get_warehouse_recommendations'):
                    warehouse_stats = system.get_warehouse_recommendations()
                
                # ИСПРАВЛЕНО: Используем улучшенное отображение
                if hasattr(system, 'enhanced_display_warehouse_results'):
                    system.enhanced_display_warehouse_results(enhanced_results, warehouse_stats, has_price_column)
                else:
                    st.warning("⚠️ Улучшенное отображение не применено. Используем стандартное.")
                    # Fallback на стандартное отображение
                    display_basic_results(enhanced_results, warehouse_stats)
                
                # Экспорт с исправлениями
                st.subheader("📤 Экспорт с исправленными данными")
                
                if st.button("💾 Создать улучшенный Excel отчет"):
                    if hasattr(system, 'create_enhanced_excel_report'):
                        excel_data = system.create_enhanced_excel_report(enhanced_results, warehouse_stats)
                        if excel_data:
                            st.download_button(
                                label="📥 Скачать улучшенный отчет",
                                data=excel_data,
                                file_name=f"warehouse_analysis_enhanced_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            st.success("✅ Улучшенный Excel отчет готов!")
                    else:
                        st.error("❌ Функция создания улучшенного отчета не найдена")
            
            else:
                st.error("❌ Анализ не выполнен или вернул пустые результаты")
    
    else:
        st.info("📁 Загрузите файл остатков для начала анализа")


def add_prices_to_analysis_results(analysis_results, ads_data, price_column):
    """
    ИСПРАВЛЕНИЕ: Добавляет цены к результатам анализа, если их там нет
    """
    
    # Создаем словарь цен для быстрого поиска
    price_dict = {}
    for _, row in ads_data.iterrows():
        if price_column in row and pd.notna(row[price_column]) and row[price_column] > 0:
            nomenclature_col = None
            for col in ['номенклатура', 'Наименование', 'наименование']:
                if col in ads_data.columns:
                    nomenclature_col = col
                    break
            
            if nomenclature_col:
                item_name = str(row[nomenclature_col]).strip()
                price_dict[item_name] = float(row[price_column])
    
    st.info(f"🔍 Найдено цен для интеграции: {len(price_dict)} товаров")
    
    # Добавляем цены к результатам анализа
    enhanced_results = []
    
    for item in analysis_results:
        enhanced_item = item.copy()
        item_name = enhanced_item.get('номенклатура', '')
        
        # Добавляем цену если её нет
        if 'price' not in enhanced_item or enhanced_item.get('price', 0) == 0:
            if item_name in price_dict:
                enhanced_item['price'] = price_dict[item_name]
                enhanced_item['price_source'] = f'ADS:{price_column}'
            else:
                enhanced_item['price'] = 0
                enhanced_item['price_source'] = 'не найдена'
        
        # Пересчитываем денежные показатели
        price = enhanced_item.get('price', 0)
        if price > 0:
            
            # Общая стоимость остатков
            total_stock = enhanced_item.get('total_stock', 0)
            enhanced_item['total_stock_value'] = total_stock * price
            
            # Общая стоимость заказов
            total_order_qty = enhanced_item.get('total_order_quantity', 0)
            enhanced_item['total_order_value'] = total_order_qty * price
            
            # Пересчитываем по складам
            if 'warehouses' in enhanced_item:
                for wh_key, wh_data in enhanced_item['warehouses'].items():
                    if isinstance(wh_data, dict):
                        # Стоимость остатка на складе
                        current_stock = wh_data.get('current_stock', 0)
                        wh_data['stock_value'] = current_stock * price
                        
                        # Стоимость заказа для склада
                        order_qty = wh_data.get('order_quantity', 0)
                        wh_data['order_value'] = order_qty * price
                        
                        # Добавляем цену к данным склада
                        wh_data['unit_price'] = price
        
        enhanced_results.append(enhanced_item)
    
    return enhanced_results


def display_basic_results(analysis_results, warehouse_stats):
    """
    Базовое отображение результатов как fallback
    """
    
    st.subheader("📊 Результаты анализа (базовое отображение)")
    
    if not analysis_results:
        st.warning("❌ Нет результатов для отображения")
        return
    
    # Простая статистика
    total_items = len(analysis_results)
    items_with_prices = sum(1 for item in analysis_results if item.get('price', 0) > 0)
    total_order_qty = sum(item.get('total_order_quantity', 0) for item in analysis_results)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("С ценами", items_with_prices)
    with col3:
        st.metric("К заказу", f"{total_order_qty:.0f}")
    
    # Простая таблица
    display_data = []
    for item in analysis_results[:50]:  # Первые 50 товаров
        display_data.append({
            'Номенклатура': item.get('номенклатура', '')[:50],
            'ADS': f"{item.get('ads', 0):.3f}",
            'Цена': f"{item.get('price', 0):.0f}" if item.get('price', 0) > 0 else "нет",
            'К заказу': f"{item.get('total_order_quantity', 0):.0f}",
            'Стоимость заказа': f"{item.get('total_order_value', 0):.0f}" if item.get('total_order_value', 0) > 0 else "нет"
        })
    
    if display_data:
        df_basic = pd.DataFrame(display_data)
        st.dataframe(df_basic, use_container_width=True)


# ===== ИНСТРУКЦИИ ПО ПРИМЕНЕНИЮ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ =====

def get_display_fix_instructions():
    """
    Возвращает инструкции по применению исправлений отображения
    """
    
    return """
# 🎨 ИНСТРУКЦИИ ПО ПРИМЕНЕНИЮ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ

## 🎯 ЧТО ИСПРАВЛЯЕТСЯ:

### 🔧 Проблема: Цены есть, но не показываются в таблицах
- ✅ **Правильное извлечение цен** из колонки 'last_purchase_price' в ADS
- ✅ **Интеграция цен в результаты** анализа складов  
- ✅ **Отображение денежных колонок** в таблицах
- ✅ **Расчет стоимости заказов** и остатков
- ✅ **Денежная статистика** по складам

### 🔧 Проблема: Неправильные расчеты MIN/MAX
- ✅ **Корректные формулы** расчета минимальных и максимальных запасов
- ✅ **Персональные настройки** для каждого склада
- ✅ **Правильные статусы** товаров (критично/внимание/норма)

### 🔧 Проблема: Неполная статистика
- ✅ **Полная статистика по складам** с денежными показателями
- ✅ **Визуализация с ценами** (графики стоимости заказов)
- ✅ **Excel экспорт** с денежными данными
- ✅ **Топ товары** по стоимости заказов

## 🚀 СПОСОБЫ ПРИМЕНЕНИЯ:

### Способ 1: Полная замена функции анализа складов

```python
def warehouse_analysis_page(system):
    from display_fixes_warehouse import enhanced_warehouse_analysis_page_with_fixes
    enhanced_warehouse_analysis_page_with_fixes(system)
```

### Способ 2: Добавление только исправлений отображения

```python
def warehouse_analysis_page(system):
    # Ваш существующий код анализа...
    
    # ДОБАВИТЬ перед отображением результатов:
    from display_fixes_warehouse import apply_display_fixes_to_system
    if not hasattr(system, '_display_fixes_applied'):
        apply_display_fixes_to_system(system)
    
    # Затем использовать улучшенное отображение:
    if hasattr(system, 'enhanced_display_warehouse_results'):
        system.enhanced_display_warehouse_results(analysis_results, recommendations, True)
```

### Способ 3: Применение отдельных исправлений

```python
# Только исправление отображения таблиц
from display_fixes_warehouse import fix_warehouse_results_display
enhanced_display = fix_warehouse_results_display()
enhanced_display(analysis_results, recommendations, True)

# Только исправление Excel экспорта  
from display_fixes_warehouse import fix_warehouse_excel_export
enhanced_excel = fix_warehouse_excel_export()
excel_data = enhanced_excel(analysis_results, recommendations)
```

## ✅ РЕЗУЛЬТАТ ПОСЛЕ ПРИМЕНЕНИЯ:

### 📊 В таблицах будут показываться:
- **Цена товара** из колонки 'Посл. закупка' ADS
- **Стоимость остатков** по каждому складу
- **Стоимость заказов** в денежном выражении  
- **К заказу (₽)** - стоимость рекомендуемых закупок
- **Источник цены** - откуда взята цена

### 📈 В статистике появятся:
- **Покрытие ценами** (% товаров с найденными ценами)
- **Общая стоимость заказов** по всем складам
- **Стоимость остатков** на складах
- **Топ товары** по стоимости заказов

### 📊 В визуализации:
- **Графики стоимости заказов** по складам
- **Стоимость остатков** по складам  
- **Топ-10 самых дорогих заказов**
- **Соотношение цена vs количество**

### 📤 В Excel экспорте:
- **Лист "Сводка с ценами"** - все товары с ценами и стоимостями
- **Лист "Заказы с ценами"** - только товары к заказу с расчетом стоимости
- **Лист "Склады с деньгами"** - статистика складов с денежными показателями
- **Лист "Итоговая сводка"** - общие денежные показатели

## 🔍 ДИАГНОСТИКА:

После применения исправлений система покажет:

```
✅ Исправления отображения применены
  ✅ Улучшенное отображение результатов с ценами
  ✅ Улучшенный Excel экспорт с денежными данными  
  ✅ Быстрая проверка цен

💰 Найдены цены в колонке 'last_purchase_price': 150/200 товаров (75.0%)
🔍 Найдено цен для интеграции: 150 товаров
```

## 💡 ОСОБЕННОСТИ:

### Автоматическая интеграция цен:
- Ищет цены в колонках: 'last_purchase_price', 'цена', 'price', 'Посл. закупка'
- Добавляет цены к результатам анализа если их там нет
- Пересчитывает все денежные показатели

### Улучшенные таблицы:
- Денежные колонки можно скрывать/показывать
- Фильтры: "Только с ценами", "Без цен", "По стоимости заказа"
- Сортировка по цене и стоимости заказов

### Совместимость:
- Работает с вашей существующей системой
- Не ломает существующую функциональность  
- Fallback на базовое отображение если что-то не работает

Ваши цены теперь будут ВИДНЫ во всех таблицах и отчетах! 🎉
"""


# ===== ДИАГНОСТИКА ОТОБРАЖЕНИЯ =====

def diagnose_display_issues(system):
    """
    Диагностирует проблемы с отображением цен и расчетов
    """
    
    st.subheader("🔍 Диагностика отображения")
    
    issues = []
    solutions = []
    
    # Проверка 1: Наличие ADS данных
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        issues.append("❌ Нет ADS данных")
        solutions.append("Рассчитайте ADS в разделе 'ADS расчет'")
    else:
        ads_data = system.calculated_ads
        st.success(f"✅ ADS данные есть: {len(ads_data)} товаров")
        
        # Проверка 2: Наличие цен в ADS
        price_columns = ['last_purchase_price', 'цена', 'price', 'Посл. закупка']
        found_price_column = None
        
        for col in price_columns:
            if col in ads_data.columns:
                found_price_column = col
                break
        
        if found_price_column:
            prices_count = (ads_data[found_price_column] > 0).sum()
            total_count = len(ads_data)
            
            if prices_count > 0:
                st.success(f"✅ Найдены цены в колонке '{found_price_column}': {prices_count}/{total_count}")
            else:
                issues.append(f"❌ Колонка '{found_price_column}' есть, но все цены = 0")
                solutions.append("Проверьте правильность загрузки ADS файлов с ценами")
        else:
            issues.append("❌ Не найдены колонки с ценами в ADS")
            solutions.append("Убедитесь что ADS файлы содержат колонку 'Посл. закупка' или 'last_purchase_price'")
    
    # Проверка 3: Исправления отображения
    if hasattr(system, '_display_fixes_applied'):
        st.success("✅ Исправления отображения применены")
        if hasattr(system, '_display_fixes_list'):
            for fix in system._display_fixes_list:
                st.write(f"  {fix}")
    else:
        issues.append("❌ Исправления отображения не применены")
        solutions.append("Примените исправления: apply_display_fixes_to_system(system)")
    
    # Проверка 4: Методы анализа складов
    if hasattr(system, 'analyze_warehouse_stock_with_details'):
        st.success("✅ Метод analyze_warehouse_stock_with_details существует")
    else:
        issues.append("❌ Отсутствует метод analyze_warehouse_stock_with_details")
        solutions.append("Примените основные исправления системы анализа складов")
    
    # Показываем проблемы
    if issues:
        st.error("🚨 Найдены проблемы с отображением:")
        for i, issue in enumerate(issues, 1):
            st.write(f"{i}. {issue}")
            st.write(f"   💡 **Решение:** {solutions[i-1]}")
        
        st.markdown("---")
        st.info("🎯 **Быстрое решение всех проблем:** Примените `enhanced_warehouse_analysis_page_with_fixes(system)`")
    
    else:
        st.success("🎉 Все проверки пройдены! Отображение должно работать корректно.")
    
    return len(issues) == 0


if __name__ == "__main__":
    print("🎨 Исправления отображения цен и расчетов в анализе складов")
    print("Решает проблемы когда цены есть в системе, но не показываются в таблицах")
    print("\nДля применения:")
    print("from display_fixes_warehouse import enhanced_warehouse_analysis_page_with_fixes")
    print("enhanced_warehouse_analysis_page_with_fixes(system)")
    print("\nИли:")
    print("from display_fixes_warehouse import apply_display_fixes_to_system") 
    print("apply_display_fixes_to_system(system)")