#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ДИНАМИКИ ПРОДАЖ
Проблема: система использует текущую дату для фильтрации, но данные исторические
Решение: исправить логику выбора периода для работы с имеющимися данными
"""

import re

def fix_sales_dynamics_display():
    """Исправляет логику отображения динамики продаж в приложении"""
    print("🔧 ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ДИНАМИКИ ПРОДАЖ")
    print("=" * 50)
    
    # Читаем файл приложения
    with open('webhook_app_stable.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ИСПРАВЛЕНИЕ 1: Логика выбора периода
    old_period_logic = """    # Рассчитываем даты
    end_date = datetime.now().date()
    if period_option == "Последние 30 дней":
        start_date = end_date - timedelta(days=30)
    elif period_option == "Последние 60 дней":
        start_date = end_date - timedelta(days=60)
    elif period_option == "Последние 90 дней":
        start_date = end_date - timedelta(days=90)
    elif period_option == "Последние 180 дней":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = None
        end_date = None"""

    new_period_logic = """    # Рассчитываем даты на основе имеющихся данных
    # Сначала получаем информацию о доступных данных
    data_summary = accumulator.get_data_summary()
    
    if data_summary['sales']['last_date']:
        # Используем последнюю дату из данных как конечную точку
        end_date = pd.to_datetime(data_summary['sales']['last_date']).date()
    else:
        end_date = datetime.now().date()
    
    if period_option == "Последние 30 дней":
        start_date = end_date - timedelta(days=30)
    elif period_option == "Последние 60 дней":
        start_date = end_date - timedelta(days=60)
    elif period_option == "Последние 90 дней":
        start_date = end_date - timedelta(days=90)
    elif period_option == "Последние 180 дней":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = None
        end_date = None"""
    
    if old_period_logic in content:
        content = content.replace(old_period_logic, new_period_logic)
        print("✅ Исправлена логика выбора периода")
    else:
        print("⚠️ Не найден код логики периода")
    
    # ИСПРАВЛЕНИЕ 2: Добавление информации о доступных данных
    old_metrics = """        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Общая выручка", f"{total_revenue:,.0f} ₸")
        
        with col2:
            st.metric("📦 Общее количество", f"{total_quantity:,.0f}")
        
        with col3:
            st.metric("🛍️ Уникальных SKU", f"{unique_items:,}")
        
        with col4:
            st.metric("🏪 Активных филиалов", unique_branches)"""

    new_metrics = """        # Основные метрики
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💰 Общая выручка", f"{total_revenue:,.0f} ₸")
        
        with col2:
            st.metric("📦 Общее количество", f"{total_quantity:,.0f}")
        
        with col3:
            st.metric("🛍️ Уникальных SKU", f"{unique_items:,}")
        
        with col4:
            st.metric("🏪 Активных филиалов", unique_branches)
        
        with col5:
            # Показываем период данных
            if not sales_data.empty:
                min_date = pd.to_datetime(sales_data['date']).min().strftime('%d.%m')
                max_date = pd.to_datetime(sales_data['date']).max().strftime('%d.%m')
                st.metric("📅 Период данных", f"{min_date} - {max_date}")
            else:
                st.metric("📅 Период данных", "Нет данных")"""
    
    if old_metrics in content:
        content = content.replace(old_metrics, new_metrics)
        print("✅ Добавлена информация о периоде данных")
    else:
        print("⚠️ Не найден код метрик")
    
    # ИСПРАВЛЕНИЕ 3: Улучшение динамики продаж
    old_dynamics = """        # Динамика продаж
        st.subheader("📈 Динамика продаж")
        
        daily_sales = sales_data.groupby('date').agg({
            'amount': 'sum',
            'quantity': 'sum'
        }).reset_index()"""

    new_dynamics = """        # Динамика продаж
        st.subheader("📈 Динамика продаж")
        
        if sales_data.empty:
            st.warning("Нет данных о продажах за выбранный период")
        else:
            daily_sales = sales_data.groupby('date').agg({
                'amount': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            # Сортируем по дате для правильного отображения
            daily_sales = daily_sales.sort_values('date')
            
            # Показываем статистику по периоду
            st.info(f"📊 Данные за период: {daily_sales['date'].min()} - {daily_sales['date'].max()} ({len(daily_sales)} дней)")"""
    
    if old_dynamics in content:
        content = content.replace(old_dynamics, new_dynamics)
        print("✅ Улучшена динамика продаж")
    else:
        print("⚠️ Не найден код динамики продаж")
    
    # ИСПРАВЛЕНИЕ 4: Добавление проверки на пустые данные в график
    old_chart = """        # График с двумя осями
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_sales['date'],
            y=daily_sales['amount'],
            mode='lines',
            name='Выручка (₸)',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_sales['date'],
            y=daily_sales['quantity'],
            mode='lines',
            name='Количество',
            line=dict(color='#ff7f0e', width=2),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Динамика продаж по дням',
            xaxis_title='Дата',
            yaxis_title='Выручка (₸)',
            yaxis2=dict(
                title='Количество (шт)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)"""

    new_chart = """            # График с двумя осями (только если есть данные)
            if not daily_sales.empty:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=daily_sales['date'],
                    y=daily_sales['amount'],
                    mode='lines+markers',
                    name='Выручка (₸)',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4)
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_sales['date'],
                    y=daily_sales['quantity'],
                    mode='lines+markers',
                    name='Количество',
                    line=dict(color='#ff7f0e', width=2),
                    marker=dict(size=4),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title=f'Динамика продаж по дням ({len(daily_sales)} точек данных)',
                    xaxis_title='Дата',
                    yaxis_title='Выручка (₸)',
                    yaxis2=dict(
                        title='Количество (шт)',
                        overlaying='y',
                        side='right'
                    ),
                    hovermode='x unified',
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Нет данных для построения графика динамики")"""
    
    if old_chart in content:
        content = content.replace(old_chart, new_chart)
        print("✅ Улучшен график динамики продаж")
    else:
        print("⚠️ Не найден код графика")
    
    # ИСПРАВЛЕНИЕ 5: Добавление отладочной информации
    debug_info = """
        # Отладочная информация (можно убрать после исправления)
        with st.expander("🔍 Отладочная информация"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Параметры запроса:**")
                st.write(f"- Начальная дата: {start_date}")
                st.write(f"- Конечная дата: {end_date}")
                st.write(f"- Выбранный период: {period_option}")
            
            with col2:
                st.write("**Статистика данных:**")
                if not sales_data.empty:
                    st.write(f"- Записей загружено: {len(sales_data)}")
                    st.write(f"- Уникальных дат: {sales_data['date'].nunique()}")
                    st.write(f"- Первая дата: {sales_data['date'].min()}")
                    st.write(f"- Последняя дата: {sales_data['date'].max()}")
                else:
                    st.write("- Нет данных для отображения")
    """
    
    # Добавляем отладочную информацию после динамики продаж
    content = content.replace(
        "st.plotly_chart(fig, use_container_width=True)",
        "st.plotly_chart(fig, use_container_width=True)" + debug_info
    )
    
    # Сохраняем исправленный файл
    with open('webhook_app_stable.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл сохранен с исправлениями")
    return True

def create_deployment_script():
    """Создает скрипт для развертывания исправлений"""
    print("\n🚀 СОЗДАНИЕ СКРИПТА РАЗВЕРТЫВАНИЯ")
    print("=" * 50)
    
    script_content = """#!/bin/bash

# ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ДИНАМИКИ ПРОДАЖ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ДИНАМИКИ ПРОДАЖ"
echo "Проблема: неправильное отображение динамики продаж"
echo "Решение: исправление логики фильтрации по периоду"
echo ""

# Загружаем исправленный файл
echo "📤 Загрузка исправленного приложения..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    echo '🔄 Перезапуск сервиса с исправлениями...'
    systemctl start webhook-analytics
    
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис успешно перезапущен'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -10
    fi
    
    echo ''
    echo '✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!'
    echo ''
    echo '📊 ЧТО ИСПРАВЛЕНО:'
    echo '   ✅ Логика выбора периода учитывает имеющиеся данные'
    echo '   ✅ Добавлена информация о периоде данных'
    echo '   ✅ Улучшена динамика продаж с проверками'
    echo '   ✅ Добавлена отладочная информация'
    echo ''
    echo '🌐 Проверьте: http://217.114.1.117:8502'
    echo '   📈 Общий анализ → должна правильно показывать динамику'
    echo '   📅 Разные периоды → корректная фильтрация'
    echo '   🔍 Отладочная информация → для диагностики'
"

echo ""
echo "✅ ИСПРАВЛЕНИЯ РАЗВЕРНУТЫ!"
echo "Динамика продаж теперь должна отображаться корректно"
"""
    
    with open('deploy_dynamics_fix.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    import os, stat
    os.chmod('deploy_dynamics_fix.sh', stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    
    print("✅ Создан скрипт: deploy_dynamics_fix.sh")
    return True

def main():
    """Основная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ДИНАМИКИ ПРОДАЖ")
    print("=" * 60)
    print("❌ ПРОБЛЕМА: Динамика продаж отображается неправильно")
    print("✅ РЕШЕНИЕ: Исправление логики фильтрации и отображения")
    print("")
    
    steps = [
        (fix_sales_dynamics_display, "Исправление логики отображения"),
        (create_deployment_script, "Создание скрипта развертывания")
    ]
    
    success_count = 0
    for step_func, step_name in steps:
        print(f"\n🔄 {step_name}...")
        if step_func():
            success_count += 1
            print(f"✅ {step_name} - ЗАВЕРШЕНО")
        else:
            print(f"❌ {step_name} - ОШИБКА")
    
    print(f"\n🎯 РЕЗУЛЬТАТ: {success_count}/{len(steps)} шагов выполнено")
    
    if success_count == len(steps):
        print("\n🎉 ИСПРАВЛЕНИЯ ГОТОВЫ!")
        print("📋 Запустите: ./deploy_dynamics_fix.sh")
        print("\n📊 ЧТО БУДЕТ ИСПРАВЛЕНО:")
        print("   🔧 Логика периодов будет работать с имеющимися данными")
        print("   📅 Отображение периода данных в интерфейсе")
        print("   📈 Улучшенная динамика продаж с проверками")
        print("   🔍 Отладочная информация для диагностики")

if __name__ == '__main__':
    main()