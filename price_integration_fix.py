#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕНИЕ: Полная интеграция цен из колонки "Посл. закупка" в систему
Обновляет все методы для работы с денежным выражением дефицита
"""

import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===== ИСПРАВЛЕНИЕ 1: Обновляем метод compare_stock_vs_min =====

def compare_stock_vs_min_with_prices(system) -> dict:
    """
    ИСПРАВЛЕННАЯ функция - решает проблему потери цен
    """
    if system.calculated_min_stock is None:
        return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
    
    if system.stock_data is None:
        return {'success': False, 'error': 'Текущие остатки не загружены'}
    
    try:
        print("💰 Начинаем сравнение с интеграцией цен...")
        
        # Получаем базовые данные
        min_stock_df = system.calculated_min_stock.copy()
        current_stock_df = system.stock_data[['номенклатура', 'total_current_stock']].copy()
        
        print(f"📊 MIN запасы: {len(min_stock_df)} товаров")
        print(f"📊 Остатки: {len(current_stock_df)} товаров")
        
        # ОТЛАДКА: Проверяем наличие цен в минимальных запасах
        price_in_min_stock = 'last_purchase_price' in min_stock_df.columns
        print(f"🔍 Цены в MIN запасах: {'✅' if price_in_min_stock else '❌'}")
        
        if price_in_min_stock:
            items_with_price_in_min = len(min_stock_df[min_stock_df['last_purchase_price'] > 0])
            print(f"💰 Товаров с ценами в MIN: {items_with_price_in_min}")
        
        # КРИТИЧНО: Если цен нет в MIN запасах, добавляем из ADS
        if not price_in_min_stock:
            print("🔧 Цены отсутствуют в MIN запасах, добавляем из ADS...")
            
            if (hasattr(system, 'calculated_ads') and 
                system.calculated_ads is not None and 
                'last_purchase_price' in system.calculated_ads.columns):
                
                price_df = system.calculated_ads[['номенклатура', 'last_purchase_price']].copy()
                print(f"✅ Найдены цены в ADS: {len(price_df)} товаров")
                
                # Статистика цен из ADS
                items_with_price_ads = len(price_df[price_df['last_purchase_price'] > 0])
                avg_price = price_df[price_df['last_purchase_price'] > 0]['last_purchase_price'].mean()
                
                print(f"💰 Статистика цен из ADS:")
                print(f"   - С ценой > 0: {items_with_price_ads}")
                print(f"   - Средняя цена: {avg_price:.2f}")
                
                # ДОБАВЛЯЕМ ЦЕНЫ В MIN ЗАПАСЫ
                min_stock_df = pd.merge(min_stock_df, price_df, on='номенклатура', how='left')
                min_stock_df['last_purchase_price'] = pd.to_numeric(
                    min_stock_df['last_purchase_price'], errors='coerce'
                ).fillna(0)
                
                print(f"✅ Цены добавлены в MIN запасы")
                items_after_merge = len(min_stock_df[min_stock_df['last_purchase_price'] > 0])
                print(f"💰 Товаров с ценами после добавления: {items_after_merge}")
            else:
                print("❌ Цены не найдены в ADS, устанавливаем 0")
                min_stock_df['last_purchase_price'] = 0
        
        # Объединяем MIN запасы (уже с ценами) с остатками
        comparison = pd.merge(min_stock_df, current_stock_df, on='номенклатура', how='left')
        comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
        
        # ОТЛАДКА: Проверяем цены после объединения
        final_items_with_price = len(comparison[comparison['last_purchase_price'] > 0])
        print(f"🔍 Товаров с ценами после объединения: {final_items_with_price}")
        
        # Если цены все еще отсутствуют, устанавливаем 0
        if 'last_purchase_price' not in comparison.columns:
            print("⚠️ Колонка last_purchase_price отсутствует, создаем с нулями")
            comparison['last_purchase_price'] = 0
        else:
            # Убеждаемся что цены в правильном формате
            comparison['last_purchase_price'] = pd.to_numeric(
                comparison['last_purchase_price'], errors='coerce'
            ).fillna(0)
        
        # Основные расчеты дефицита
        comparison['stock_deficit'] = comparison['min_stock_total'] - comparison['total_current_stock']
        comparison['stock_deficit'] = comparison['stock_deficit'].apply(lambda x: max(0, x))
        
        # Денежные расчеты (теперь цены точно есть)
        comparison['stock_deficit_money'] = comparison['stock_deficit'] * comparison['last_purchase_price']
        comparison['min_stock_money'] = comparison['min_stock_total'] * comparison['last_purchase_price']
        comparison['current_stock_money'] = comparison['total_current_stock'] * comparison['last_purchase_price']
        
        # Дни остатка
        comparison['current_stock_days'] = np.where(
            comparison['ads'] > 0,
            comparison['total_current_stock'] / comparison['ads'],
            0
        )
        
        # Статус товара
        def determine_status(row):
            if row['stock_deficit'] > 0:
                ip_days = row.get('ip_target_days', 7)
                if row['current_stock_days'] < ip_days:
                    return 'КРИТИЧНО'
                else:
                    return 'НЕДОСТАТОК'
            else:
                return 'ДОСТАТОЧНО'
        
        comparison['status'] = comparison.apply(determine_status, axis=1)
        
        # Рекомендуемый заказ
        safety_factor = getattr(system, 'default_params', {}).get('safety_factor', 1.0)
        comparison['recommended_order'] = comparison['stock_deficit'] * safety_factor
        comparison['recommended_order'] = comparison['recommended_order'].apply(lambda x: max(0, x))
        comparison['recommended_order_money'] = comparison['recommended_order'] * comparison['last_purchase_price']
        
        # Приоритет заказа
        comparison['order_priority'] = comparison.apply(
            lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                       else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                       else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                       else 'НИЗКИЙ', axis=1
        )
        
        # Сохраняем результат
        system.stock_comparison = comparison
        
        # ФИНАЛЬНАЯ СТАТИСТИКА
        total_items = len(comparison)
        deficit_items = len(comparison[comparison['stock_deficit'] > 0])
        critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
        
        total_deficit_qty = comparison['stock_deficit'].sum()
        total_deficit_money = comparison['stock_deficit_money'].sum()
        total_recommended_order_money = comparison['recommended_order_money'].sum()
        
        items_with_price = len(comparison[comparison['last_purchase_price'] > 0])
        deficit_items_with_price = len(comparison[
            (comparison['stock_deficit'] > 0) & (comparison['last_purchase_price'] > 0)
        ])
        
        print(f"\n💰 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Всего товаров: {total_items}")
        print(f"   С дефицитом: {deficit_items}")
        print(f"   Критичных: {critical_items}")
        print(f"   Общий дефицит (шт): {total_deficit_qty:,.0f}")
        print(f"   Общий дефицит (деньги): {total_deficit_money:,.2f}")
        print(f"   Рекомендуемый заказ (деньги): {total_recommended_order_money:,.2f}")
        print(f"   Товаров с ценами: {items_with_price}/{total_items}")
        
        if hasattr(system, 'calculated_max_stock') and system.calculated_max_stock is not None:
            max_stock_df = system.calculated_max_stock[['номенклатура', 'max_stock']].copy()
            comparison = pd.merge(comparison, max_stock_df, on='номенклатура', how='left')
            comparison['max_stock'] = comparison['max_stock'].fillna(0)
            
            # Статус с учетом MAX
            def determine_full_status(row):
                current = row['total_current_stock']
                min_stock = row['min_stock_total']
                max_stock = row.get('max_stock', 0)
                
                if current < min_stock:
                    return 'НЕДОСТАТОК'
                elif max_stock > 0 and current > max_stock:
                    return 'ИЗБЫТОК'
                else:
                    return row['status']  # Существующий статус
            
            comparison['full_status'] = comparison.apply(determine_full_status, axis=1)
        
        # Сохраняем результат
        system.stock_comparison = comparison
        return {
            'success': True,
            'total_items': total_items,
            'deficit_items': deficit_items,
            'critical_items': critical_items,
            'total_deficit_qty': total_deficit_qty,
            'total_deficit_money': total_deficit_money,
            'total_recommended_order_money': total_recommended_order_money,
            'items_with_price': items_with_price,
            'deficit_items_with_price': deficit_items_with_price,
            'price_coverage_percentage': (items_with_price / total_items) * 100 if total_items > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Ошибка сравнения: '{str(e)}'")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f"Ошибка сравнения остатков: {str(e)}"}
# ===== ИСПРАВЛЕНИЕ 2: Обновляем метод calculate_min_stock =====

def calculate_min_stock_with_prices(system, ip_target_days=None, min_stock_days=None) -> dict:
    """
    ИСПРАВЛЕННЫЙ расчет минимальных запасов с добавлением цен
    """
    if system.calculated_ads is None:
        return {'success': False, 'error': 'ADS не рассчитан'}
    
    try:
        print("📋 Расчет минимальных запасов с ценами...")
        
        # Параметры
        ip_days = ip_target_days or getattr(system, 'default_params', {}).get('ip_target_days', 7)
        stock_days = min_stock_days or getattr(system, 'default_params', {}).get('min_stock_days', 30)
        
        # Базовые расчеты
        df = system.calculated_ads.copy()
        
        df['ip_target_days'] = ip_days
        df['min_stock_days'] = stock_days
        df['transit_consumption'] = df['ads'] * ip_days
        df['min_stock_base'] = df['ads'] * stock_days
        df['min_stock_total'] = df['min_stock_base'] + df['transit_consumption']
        
        # НОВОЕ: Добавляем денежные расчеты если есть цены
        if 'last_purchase_price' in df.columns:
            df['min_stock_money'] = df['min_stock_total'] * df['last_purchase_price']
            df['transit_consumption_money'] = df['transit_consumption'] * df['last_purchase_price']
            df['min_stock_base_money'] = df['min_stock_base'] * df['last_purchase_price']
            
            # Статистика денежных расчетов
            total_min_stock_money = df['min_stock_money'].sum()
            items_with_price = len(df[df['last_purchase_price'] > 0])
            
            print(f"💰 Денежные расчеты минимальных запасов:")
            print(f"   - Общая стоимость MIN запасов: {total_min_stock_money:,.2f}")
            print(f"   - Товаров с ценами: {items_with_price}")
        else:
            print("⚠️ Цены не найдены в ADS данных")
        
        # Приоритет
        df['priority'] = df['ads'].apply(
            lambda x: 'ВЫСОКИЙ' if x > df['ads'].quantile(0.8) else 
                     'СРЕДНИЙ' if x > df['ads'].quantile(0.5) else 'НИЗКИЙ'
        )
        
        system.calculated_min_stock = df
        
        result = {
            'success': True,
            'total_items': len(df),
            'total_min_stock': df['min_stock_total'].sum(),
            'parameters': {'ip_target_days': ip_days, 'min_stock_days': stock_days}
        }
        
        # Добавляем денежную информацию если есть
        if 'min_stock_money' in df.columns:
            result['money_metrics'] = {
                'total_min_stock_money': df['min_stock_money'].sum(),
                'items_with_price': len(df[df['last_purchase_price'] > 0])
            }
        
        return result
        
    except Exception as e:
        return {'success': False, 'error': f"Ошибка расчета минимальных запасов: {str(e)}"}

# ===== ИСПРАВЛЕНИЕ 3: Создаем визуализацию дефицита с деньгами =====

def create_deficit_visualization_with_money(system):
    """
    Создание визуализации дефицита с денежным выражением
    """
    if system.stock_comparison is None:
        return None
    
    deficit_data = system.stock_comparison[system.stock_comparison['stock_deficit'] > 0].copy()
    
    if len(deficit_data) == 0:
        return None
    
    # Проверяем наличие денежных данных
    has_money_data = 'stock_deficit_money' in deficit_data.columns
    
    if has_money_data:
        # Топ-20 по денежному дефициту
        top_deficit_money = deficit_data.nlargest(20, 'stock_deficit_money')
        
        # Создаем subplot с двумя осями
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Дефицит в штуках', 'Дефицит в деньгах'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # График дефицита в штуках
        fig.add_trace(
            go.Bar(
                x=top_deficit_money['stock_deficit'],
                y=top_deficit_money['номенклатура'],
                orientation='h',
                name='Дефицит (шт)',
                marker_color='lightcoral'
            ),
            row=1, col=1
        )
        
        # График дефицита в деньгах
        fig.add_trace(
            go.Bar(
                x=top_deficit_money['stock_deficit_money'],
                y=top_deficit_money['номенклатура'],
                orientation='h',
                name='Дефицит (деньги)',
                marker_color='gold'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title_text="Топ-20 товаров по дефициту: количество vs денежное выражение",
            height=800,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Количество", row=1, col=1)
        fig.update_xaxes(title_text="Денежное выражение", row=1, col=2)
        fig.update_yaxes(title_text="Товары", row=1, col=1)
        
        return fig
    
    else:
        # Обычный график без денежных данных
        top_deficit = deficit_data.nlargest(20, 'stock_deficit')
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_deficit['stock_deficit'],
                y=top_deficit['номенклатура'],
                orientation='h',
                marker_color='lightcoral'
            )
        ])
        
        fig.update_layout(
            title="Топ-20 товаров по дефициту (только количество)",
            xaxis_title="Дефицит (штук)",
            yaxis_title="Товары",
            height=600
        )
        
        return fig

# ===== ИСПРАВЛЕНИЕ 4: Streamlit интерфейс с денежными метриками =====

def show_deficit_report_with_money_in_streamlit(system):
    """
    Показ отчета по дефициту с денежными метриками в Streamlit
    """
    import streamlit as st
    
    if system.stock_comparison is None:
        st.warning("⚠️ Сравнение остатков не выполнено")
        return
    
    st.subheader("💰 Отчет по дефициту с денежным выражением")
    
    # Фильтруем дефицитные товары
    deficit_items = system.stock_comparison[system.stock_comparison['stock_deficit'] > 0].copy()
    
    if len(deficit_items) == 0:
        st.success("✅ Товаров с дефицитом не найдено!")
        return
    
    # Проверяем наличие ценовых данных
    has_price_data = 'last_purchase_price' in deficit_items.columns and 'stock_deficit_money' in deficit_items.columns
    
    # Общая статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_deficit_qty = deficit_items['stock_deficit'].sum()
        st.metric("Общий дефицит (шт)", f"{total_deficit_qty:,.0f}")
    
    with col2:
        if has_price_data:
            total_deficit_money = deficit_items['stock_deficit_money'].sum()
            st.metric("Общий дефицит (₽)", f"{total_deficit_money:,.2f}")
        else:
            st.metric("Общий дефицит (₽)", "Нет данных")
    
    with col3:
        critical_items = len(deficit_items[deficit_items['status'] == 'КРИТИЧНО'])
        st.metric("Критичных товаров", critical_items)
    
    with col4:
        if has_price_data:
            items_with_price = len(deficit_items[deficit_items['last_purchase_price'] > 0])
            coverage = (items_with_price / len(deficit_items)) * 100
            st.metric("Покрытие ценами", f"{coverage:.1f}%")
        else:
            st.metric("Покрытие ценами", "0%")
    
    # Информация о ценах
    if has_price_data:
        items_with_price = len(deficit_items[deficit_items['last_purchase_price'] > 0])
        items_without_price = len(deficit_items[deficit_items['last_purchase_price'] == 0])
        
        st.info(f"""
        💰 **Информация о ценах (колонка 'Посл. закупка' из ADS файла):**
        - Товаров с ценами: **{items_with_price}** из {len(deficit_items)}
        - Товаров без цены: **{items_without_price}**
        - Средняя цена: **{deficit_items[deficit_items['last_purchase_price'] > 0]['last_purchase_price'].mean():.2f} ₽**
        """)
    else:
        st.warning("⚠️ Цены не найдены. Убедитесь что ADS файл содержит колонку 'Посл. закупка'")
    
    # Визуализация
    if has_price_data:
        fig = create_deficit_visualization_with_money(system)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Таблица дефицитных товаров
    st.subheader("📋 Детальная таблица дефицита")
    
    # Подготавливаем колонки для отображения
    display_columns = ['номенклатура', 'stock_deficit', 'current_stock_days', 'status', 'order_priority']
    column_config = {
        'номенклатура': 'Товар',
        'stock_deficit': 'Дефицит (шт)',
        'current_stock_days': 'Дни остатка',
        'status': 'Статус',
        'order_priority': 'Приоритет'
    }
    
    if has_price_data:
        display_columns.extend(['last_purchase_price', 'stock_deficit_money', 'recommended_order_money'])
        column_config.update({
            'last_purchase_price': 'Цена (₽)',
            'stock_deficit_money': 'Дефицит (₽)',
            'recommended_order_money': 'К заказу (₽)'
        })
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Фильтр по статусу:",
            options=['Все', 'КРИТИЧНО', 'НЕДОСТАТОК']
        )
    
    with col2:
        if has_price_data:
            min_deficit_money = st.number_input(
                "Мин. дефицит (₽):",
                min_value=0.0,
                value=0.0,
                step=100.0
            )
        else:
            min_deficit_qty = st.number_input(
                "Мин. дефицит (шт):",
                min_value=0,
                value=0
            )
    
    # Применяем фильтры
    filtered_data = deficit_items.copy()
    
    if status_filter != 'Все':
        filtered_data = filtered_data[filtered_data['status'] == status_filter]
    
    if has_price_data and min_deficit_money > 0:
        filtered_data = filtered_data[filtered_data['stock_deficit_money'] >= min_deficit_money]
    elif not has_price_data and 'min_deficit_qty' in locals() and min_deficit_qty > 0:
        filtered_data = filtered_data[filtered_data['stock_deficit'] >= min_deficit_qty]
    
    # Сортируем по денежному дефициту если есть цены
    if has_price_data:
        filtered_data = filtered_data.sort_values('stock_deficit_money', ascending=False)
    else:
        filtered_data = filtered_data.sort_values('stock_deficit', ascending=False)
    
    # Отображаем таблицу
    st.dataframe(
        filtered_data[display_columns],
        use_container_width=True,
        column_config=column_config
    )
    
    # Кнопка экспорта
    if st.button("📥 Экспорт дефицита в Excel"):
        try:
            excel_buffer = create_deficit_excel_export(system)
            
            st.download_button(
                label="💾 Скачать отчет по дефициту",
                data=excel_buffer,
                file_name=f"deficit_report_with_money_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"❌ Ошибка экспорта: {str(e)}")

# ===== ИСПРАВЛЕНИЕ 5: Excel экспорт с денежными данными =====

def create_deficit_excel_export(system):
    """
    Создание Excel отчета по дефициту с денежными данными
    """
    import io
    
    if system.stock_comparison is None:
        raise ValueError("Сравнение остатков не выполнено")
    
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # 1. Все дефицитные товары
            deficit_items = system.stock_comparison[system.stock_comparison['stock_deficit'] > 0].copy()
            
            if not deficit_items.empty:
                # Русифицируем колонки
                deficit_export = deficit_items.copy()
                
                russian_columns = {
                    'номенклатура': 'Номенклатура',
                    'ads': 'ADS',
                    'min_stock_total': 'Минимальный_запас_шт',
                    'total_current_stock': 'Текущий_остаток_шт',
                    'stock_deficit': 'Дефицит_шт',
                    'current_stock_days': 'Дни_остатка',
                    'status': 'Статус',
                    'order_priority': 'Приоритет_заказа',
                    'recommended_order': 'Рекомендуемый_заказ_шт'
                }
                
                # Добавляем денежные колонки если есть
                if 'last_purchase_price' in deficit_export.columns:
                    russian_columns.update({
                        'last_purchase_price': 'Цена_закупки',
                        'stock_deficit_money': 'Дефицит_деньги',
                        'min_stock_money': 'Минимальный_запас_деньги',
                        'current_stock_money': 'Текущий_остаток_деньги',
                        'recommended_order_money': 'Рекомендуемый_заказ_деньги'
                    })
                
                # Переименовываем только существующие колонки
                existing_columns = {k: v for k, v in russian_columns.items() if k in deficit_export.columns}
                deficit_export = deficit_export.rename(columns=existing_columns)
                
                # Сортируем по денежному дефициту если есть
                if 'Дефицит_деньги' in deficit_export.columns:
                    deficit_export = deficit_export.sort_values('Дефицит_деньги', ascending=False)
                else:
                    deficit_export = deficit_export.sort_values('Дефицит_шт', ascending=False)
                
                deficit_export.to_excel(writer, sheet_name='Все_дефицитные_товары', index=False)
            
            # 2. Критичные товары
            critical_items = system.stock_comparison[system.stock_comparison['status'] == 'КРИТИЧНО'].copy()
            
            if not critical_items.empty:
                critical_export = critical_items.rename(columns=existing_columns)
                if 'Дефицит_деньги' in critical_export.columns:
                    critical_export = critical_export.sort_values('Дефицит_деньги', ascending=False)
                
                critical_export.to_excel(writer, sheet_name='Критичные_товары', index=False)
            
            # 3. Сводка по денежному выражению
            if 'stock_deficit_money' in system.stock_comparison.columns:
                money_summary = []
                
                for status in ['КРИТИЧНО', 'НЕДОСТАТОК']:
                    status_data = system.stock_comparison[system.stock_comparison['status'] == status]
                    
                    money_summary.append({
                        'Статус': status,
                        'Количество_товаров': len(status_data),
                        'Дефицит_штук': status_data['stock_deficit'].sum(),
                        'Дефицит_деньги': status_data['stock_deficit_money'].sum(),
                        'Рекомендуемый_заказ_штук': status_data['recommended_order'].sum(),
                        'Рекомендуемый_заказ_деньги': status_data['recommended_order_money'].sum(),
                        'Товаров_с_ценами': len(status_data[status_data['last_purchase_price'] > 0])
                    })
                
                # Общие итоги
                total_deficit = system.stock_comparison[system.stock_comparison['stock_deficit'] > 0]
                money_summary.append({
                    'Статус': 'ИТОГО',
                    'Количество_товаров': len(total_deficit),
                    'Дефицит_штук': total_deficit['stock_deficit'].sum(),
                    'Дефицит_деньги': total_deficit['stock_deficit_money'].sum(),
                    'Рекомендуемый_заказ_штук': total_deficit['recommended_order'].sum(),
                    'Рекомендуемый_заказ_деньги': total_deficit['recommended_order_money'].sum(),
                    'Товаров_с_ценами': len(total_deficit[total_deficit['last_purchase_price'] > 0])
                })
                
                money_summary_df = pd.DataFrame(money_summary)
                money_summary_df.to_excel(writer, sheet_name='Денежная_сводка', index=False)
            
            # 4. Топ по денежному дефициту
            if 'stock_deficit_money' in system.stock_comparison.columns:
                top_money_deficit = system.stock_comparison[
                    system.stock_comparison['stock_deficit_money'] > 0
                ].nlargest(50, 'stock_deficit_money')
                
                if not top_money_deficit.empty:
                    top_export = top_money_deficit.rename(columns=existing_columns)
                    top_export.to_excel(writer, sheet_name='Топ_50_по_деньгам', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        raise Exception(f"Ошибка создания Excel отчета: {str(e)}")

# ===== ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ К СИСТЕМЕ =====

def apply_price_fixes_to_system(system):
    """
    Применение всех исправлений к существующей системе
    """
    import types
    
    print("🔧 Применяем исправления для работы с ценами...")
    
    # Заменяем методы в системе
    system.compare_stock_vs_min = types.MethodType(compare_stock_vs_min_with_prices, system)
    system.calculate_min_stock = types.MethodType(calculate_min_stock_with_prices, system)
    
    # Добавляем новые методы
    system.create_deficit_visualization_with_money = types.MethodType(create_deficit_visualization_with_money, system)
    system.show_deficit_report_with_money = types.MethodType(show_deficit_report_with_money_in_streamlit, system)
    system.create_deficit_excel_export = types.MethodType(create_deficit_excel_export, system)
    
    print("✅ Все методы обновлены для работы с ценами!")
    print("💰 Теперь система поддерживает:")
    print("   - Расчет дефицита в денежном выражении")
    print("   - Сортировку по денежному дефициту")
    print("   - Визуализацию с ценами")
    print("   - Excel экспорт с денежными данными")
    
    return True

# ===== ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ =====

def instruction_for_using_price_fixes():
    """
    Инструкция по использованию исправлений
    """
    
    print("""
    🔧 ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ ИСПРАВЛЕНИЙ:
    
    1. Импортируйте этот модуль:
       from price_integration_fix import apply_price_fixes_to_system
    
    2. Примените исправления к вашей системе:
       apply_price_fixes_to_system(ваша_система)
    
    3. Убедитесь что ADS файл содержит колонку 'Посл. закупка' (колонка 12)
    
    4. Теперь все методы работают с ценами:
       - system.compare_stock_vs_min() - добавляет денежные расчеты
       - system.calculate_min_stock() - считает стоимость минимальных запасов
       - system.show_deficit_report_with_money() - показывает отчет с деньгами
       - system.create_deficit_excel_export() - экспорт с денежными данными
    
    🎯 РЕЗУЛЬТАТ:
    - Дефицит показывается и в штуках, и в деньгах
    - Сортировка по денежному дефициту
    - Полная статистика по ценам
    - Excel отчеты с денежными метриками
    
    ⚠️ ТРЕБОВАНИЯ:
    - ADS файл должен быть загружен с колонкой 'Посл. закупка'
    - Система должна быть инициализирована
    - Должен быть выполнен расчет ADS
    """)

# ===== ДЕМО ФУНКЦИЯ ДЛЯ ТЕСТИРОВАНИЯ =====

def demo_price_integration(system):
    """
    Демонстрация работы с ценами
    """
    print("🎭 ДЕМОНСТРАЦИЯ ИНТЕГРАЦИИ ЦЕН")
    print("=" * 50)
    
    # Применяем исправления
    apply_price_fixes_to_system(system)
    
    # Проверяем наличие данных
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        print("❌ ADS не рассчитан. Загрузите файл продаж.")
        return False
    
    # Проверяем наличие цен
    if 'last_purchase_price' not in system.calculated_ads.columns:
        print("❌ Цены не найдены. Убедитесь что ADS файл содержит колонку 'Посл. закупка'.")
        return False
    
    # Статистика цен
    ads_data = system.calculated_ads
    items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
    total_items = len(ads_data)
    avg_price = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
    
    print(f"✅ Найдено цен: {items_with_price}/{total_items} товаров")
    print(f"💰 Средняя цена: {avg_price:.2f}")
    
    # Пересчитываем минимальные запасы с ценами
    print("\n🔄 Пересчитываем минимальные запасы...")
    min_result = system.calculate_min_stock()
    
    if min_result['success']:
        print("✅ Минимальные запасы пересчитаны с ценами")
        if 'money_metrics' in min_result:
            print(f"💰 Общая стоимость MIN запасов: {min_result['money_metrics']['total_min_stock_money']:,.2f}")
    
    # Проверяем остатки
    if system.stock_data is not None:
        print("\n🔄 Пересчитываем сравнение остатков...")
        comparison_result = system.compare_stock_vs_min()
        
        if comparison_result['success']:
            print("✅ Сравнение остатков обновлено с ценами")
            print(f"💰 Общий дефицит (деньги): {comparison_result['total_deficit_money']:,.2f}")
            print(f"📊 Покрытие ценами: {comparison_result['price_coverage_percentage']:.1f}%")
            
            # Показываем топ дефицитных товаров
            deficit_items = system.stock_comparison[system.stock_comparison['stock_deficit'] > 0]
            
            if len(deficit_items) > 0:
                print(f"\n🔝 Топ-5 дефицитных товаров по деньгам:")
                top_deficit = deficit_items.nlargest(5, 'stock_deficit_money')
                
                for i, (_, row) in enumerate(top_deficit.iterrows(), 1):
                    print(f"   {i}. {row['номенклатура'][:50]}")
                    print(f"      Дефицит: {row['stock_deficit']:.0f} шт = {row['stock_deficit_money']:,.2f} ₽")
        else:
            print(f"❌ Ошибка сравнения: {comparison_result['error']}")
    else:
        print("⚠️ Остатки не загружены, сравнение недоступно")
    
    print("\n🎯 ИНТЕГРАЦИЯ ЦЕН ЗАВЕРШЕНА!")
    return True

# ===== БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ =====

def quick_price_check(system):
    """
    Быстрая проверка наличия ценовых данных в системе
    """
    print("🔍 БЫСТРАЯ ПРОВЕРКА ЦЕНОВЫХ ДАННЫХ")
    print("-" * 40)
    
    checks = {
        "ADS рассчитан": hasattr(system, 'calculated_ads') and system.calculated_ads is not None,
        "Колонка цен в ADS": False,
        "Минимальные запасы": hasattr(system, 'calculated_min_stock') and system.calculated_min_stock is not None,
        "Сравнение остатков": hasattr(system, 'stock_comparison') and system.stock_comparison is not None,
        "Денежные расчеты": False
    }
    
    # Проверяем цены в ADS
    if checks["ADS рассчитан"]:
        checks["Колонка цен в ADS"] = 'last_purchase_price' in system.calculated_ads.columns
        
        if checks["Колонка цен в ADS"]:
            items_with_price = len(system.calculated_ads[system.calculated_ads['last_purchase_price'] > 0])
            total_items = len(system.calculated_ads)
            print(f"   💰 Товаров с ценами: {items_with_price}/{total_items}")
    
    # Проверяем денежные расчеты в сравнении
    if checks["Сравнение остатков"]:
        checks["Денежные расчеты"] = 'stock_deficit_money' in system.stock_comparison.columns
    
    # Выводим результаты
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    
    if not checks["ADS рассчитан"]:
        print("   1. Загрузите файл продаж для расчета ADS")
    elif not checks["Колонка цен в ADS"]:
        print("   1. Убедитесь что ADS файл содержит колонку 'Посл. закупка' (колонка 12)")
        print("   2. Перезагрузите ADS файл с правильной структурой")
    elif not checks["Денежные расчеты"]:
        print("   1. Примените исправления: apply_price_fixes_to_system(system)")
        print("   2. Пересчитайте сравнение остатков")
    else:
        print("   ✅ Все готово для работы с ценами!")
    
    return all(checks.values())

if __name__ == "__main__":
    instruction_for_using_price_fixes()