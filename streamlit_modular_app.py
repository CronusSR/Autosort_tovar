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
from subcategory_abc import create_subcategory_abc_interface
try:
    from price_integration_fix import apply_price_fixes_to_system, quick_price_check
    from streamlit_deficit_money_update import (
        stock_comparison_page_with_money, 
        add_price_info_to_ads_page,
        update_export_page_with_money,
        show_money_integration_status,
        integration_instructions
    )
    PRICE_FEATURES_AVAILABLE = True
except ImportError:
    PRICE_FEATURES_AVAILABLE = False
    print("⚠️ Модули цен не найдены")

try:
    from ads_category_fix import apply_category_average_ads_fix, revert_category_ads_fix
    from streamlit_category_ads_ui import (
        show_category_ads_fix_ui,
        show_category_ads_statistics_ui, 
        show_revert_ads_fix_ui
    )
    CATEGORY_FIX_AVAILABLE = True
except ImportError:
    CATEGORY_FIX_AVAILABLE = False
try:
    from complete_price_integration import complete_price_integration_setup, show_price_integration_status_in_streamlit
    PRICE_INTEGRATION_AVAILABLE = True
except ImportError:
    PRICE_INTEGRATION_AVAILABLE = False
    print("⚠️ Модуль полной интеграции цен не найден")
warnings.filterwarnings('ignore')

try:
    from ads_category_fix_improved import quick_ads_category_fix, get_categories_preview
    from streamlit_improved_ads_ui import (
        show_improved_category_ads_fix_ui,
        show_improved_category_statistics_ui,
        show_improved_revert_ui,
        quick_streamlit_integration
    )
    IMPROVED_ADS_FIX_AVAILABLE = True
except ImportError:
    IMPROVED_ADS_FIX_AVAILABLE = False


from movement_recommendations_streamlit import show_movement_recommendations_page

from column_names_fix_correct import apply_correct_column_fix, check_correct_fix_status

from real_fix_for_your_system import (
    apply_complete_fix_to_system, 
    check_complete_fix_status,
    diagnose_system_issues
)

from warehouse_analysis import warehouse_analysis_page, add_warehouse_analysis_to_system

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
    """Инициализация системы с полным исправлением"""
    if 'inventory_system' not in st.session_state:
        st.session_state.inventory_system = ModularInventorySystem()
        
        # 🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ ВСЕХ МЕТОДОВ ЗАГРУЗКИ
        apply_complete_fix_to_system(st.session_state.inventory_system)
        add_warehouse_analysis_to_system(st.session_state.inventory_system)
    return st.session_state.inventory_system

def max_stock_page(system):
    """Исправленная страница для работы с новыми максимальными остатками"""
    st.header("📦 Новые максимальные остатки")
    
    # Проверка инициализации НОВЫХ максимальных остатков
    if not hasattr(system, '_new_max_stock_ready') or not system._new_max_stock_ready:
        st.error("❌ Новые максимальные остатки не инициализированы")
        if st.button("🔄 Переинициализировать"):
            try:
                from new_max_stock_calculator import replace_max_stock_functionality
                replace_max_stock_functionality(system)
                system._new_max_stock_ready = True
                st.success("✅ Новые максимальные остатки подключены")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
        return
    
    # Настройки параметров
    st.subheader("⚙️ Настройки параметров")
    
    col1, col2 = st.columns(2)
    with col1:
        point_type = st.selectbox("Тип точки:", ['хабы', 'склады', 'магазины'])
    with col2:
        # ИСПРАВЛЕНО: показ настроек в Streamlit, а не в терминале
        if st.button("📋 Показать настройки"):
            if hasattr(system, 'new_max_stock_calculator'):
                # Получаем настройки из калькулятора
                settings = system.new_max_stock_calculator.default_settings
                
                st.write("**📋 Текущие настройки максимальных остатков:**")
                for ptype, config in settings.items():
                    st.write(f"**🏪 {ptype.upper()}:** {config.get('description', '')}")
                    st.write(f"   - MIN: {config['min_days']} дней")
                    st.write(f"   - MAX: {config['max_days']} дней")
                    st.write("---")
            else:
                st.warning("Калькулятор не инициализирован")

    col3, col4 = st.columns(2)
    with col3:
        min_days = st.number_input("Дни MIN запаса:", min_value=1, max_value=180, value=10)
    with col4:
        max_days = st.number_input("Дни MAX запаса:", min_value=min_days, max_value=365, value=25)

    if st.button("💾 Обновить настройки"):
        try:
            system.update_new_max_stock_settings(point_type, min_days, max_days)
            st.success(f"✅ Настройки обновлены: {point_type} = MIN:{min_days}д, MAX:{max_days}д")
        except Exception as e:
            st.error(f"❌ Ошибка обновления настроек: {e}")

    st.divider()

    # РАСЧЕТ новых максимальных остатков
    st.subheader("📊 Расчет новых максимальных остатков")

    if st.button("🔄 Рассчитать НОВЫЕ MAX остатки"):
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            st.error("❌ Сначала рассчитайте ADS")
        else:
            with st.spinner("Расчет новых максимальных остатков..."):
                result = system.calculate_new_max_stock()
                
                if result['success']:
                    st.success("✅ Новые максимальные остатки рассчитаны!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Товаров", result['total_items'])
                    with col2:
                        st.metric("Общий MAX запас", f"{result['total_avg_max_stock']:,.0f}")
                    with col3:
                        st.metric("Средний MAX на товар", f"{result['avg_max_per_item']:.1f}")
                            
                else:
                    st.error(f"❌ {result['error']}")
    
    # ВЫНЕСЛИ КНОПКУ ДЕТАЛЬНОЙ СВОДКИ ОТДЕЛЬНО
    st.subheader("📊 Анализ рассчитанных остатков")
    
    # Проверяем что остатки рассчитаны
    if hasattr(system, 'new_calculated_max_stock') and system.new_calculated_max_stock is not None:
        st.info("✅ Новые максимальные остатки рассчитаны и готовы для анализа")
        
        if st.button("📊 Показать детальную сводку"):
            summary = system.get_new_max_stock_summary()
            if 'error' not in summary:
                st.write("**📊 Детальная сводка MAX остатков:**")
                
                # Общие параметры
                st.write(f"**Общие параметры:**")
                st.write(f"- Товаров: {summary['total_items']}")
                st.write(f"- Средние дни MIN: {summary['avg_parameters']['min_days']:.1f}")
                st.write(f"- Средние дни MAX: {summary['avg_parameters']['max_days']:.1f}")
                
                # Общие итоги
                st.write(f"**Общие итоги:**")
                st.write(f"- Общий MIN запас: {summary['totals']['avg_min_stock']:,.0f}")
                st.write(f"- Общий MAX запас: {summary['totals']['avg_max_stock']:,.0f}")
                st.write(f"- Рабочий диапазон: {summary['totals']['avg_range']:,.0f}")
                
                # По типам точек
                if summary['per_location']:
                    st.write(f"**По типам точек:**")
                    for loc_type, data in summary['per_location'].items():
                        with st.expander(f"🏪 {loc_type.upper()}"):
                            st.write(f"- MIN дни: {data['min_days']}")
                            st.write(f"- MAX дни: {data['max_days']}")
                            st.write(f"- Общий MIN запас: {data['total_min_stock']:,.0f}")
                            st.write(f"- Общий MAX запас: {data['total_max_stock']:,.0f}")
                            st.write(f"- Средний MIN: {data['avg_min_stock']:.1f}")
                            st.write(f"- Средний MAX: {data['avg_max_stock']:.1f}")
            else:
                st.error(f"❌ {summary['error']}")
        
        # Показать сами данные в таблице
        if st.button("📋 Показать таблицу MAX остатков"):
            st.write("**📋 Таблица рассчитанных максимальных остатков:**")
            display_cols = ['номенклатура', 'ads', 'avg_min_stock', 'avg_max_stock', 'avg_range']
            
            # Фильтруем только нужные колонки, которые есть в данных
            available_cols = [col for col in display_cols if col in system.new_calculated_max_stock.columns]
            
            if available_cols:
                st.dataframe(
                    system.new_calculated_max_stock[available_cols].head(20),
                    use_container_width=True
                )
            else:
                st.error("❌ Не найдены ожидаемые колонки в данных")
    else:
        st.warning("⚠️ Новые максимальные остатки не рассчитаны. Нажмите кнопку 'Рассчитать НОВЫЕ MAX остатки' выше.")
    
    st.divider()
    
    # ИСПРАВЛЕНО: Сравнение с НОВЫМИ максимальными остатками
    st.subheader("⚖️ Сравнение с текущими остатками")
    
    if st.button("📊 Сравнить с НОВЫМИ MIN/MAX"):
        # ИСПРАВЛЕНО: проверяем НОВЫЕ максимальные остатки
        if not hasattr(system, 'new_calculated_max_stock') or system.new_calculated_max_stock is None:
            st.error("❌ Сначала рассчитайте НОВЫЕ максимальные остатки")
        elif not hasattr(system, 'stock_data') or system.stock_data is None:
            st.error("❌ Сначала загрузите текущие остатки")
        else:
            # Создаем простое сравнение с новыми максимальными остатками
            try:
                max_data = system.new_calculated_max_stock
                stock_data = system.stock_data
                
                # Объединяем данные
                comparison = pd.merge(
                    max_data[['номенклатура', 'avg_min_stock', 'avg_max_stock']],
                    stock_data[['номенклатура', 'total_current_stock']],
                    on='номенклатура',
                    how='inner'
                )
                
                # Определяем статусы
                comparison['status'] = 'НОРМА'
                comparison.loc[comparison['total_current_stock'] < comparison['avg_min_stock'], 'status'] = 'НЕДОСТАТОК'
                comparison.loc[comparison['total_current_stock'] > comparison['avg_max_stock'], 'status'] = 'ИЗБЫТОК'
                
                # Подсчитываем статистику
                status_counts = comparison['status'].value_counts()
                
                st.success("✅ Сравнение с НОВЫМИ максимальными остатками выполнено!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Недостаток", status_counts.get('НЕДОСТАТОК', 0))
                with col2:
                    st.metric("Избыток", status_counts.get('ИЗБЫТОК', 0))
                with col3:
                    st.metric("Норма", status_counts.get('НОРМА', 0))
                
                # Показываем детали
                with st.expander("📋 Детали сравнения"):
                    st.dataframe(comparison[['номенклатура', 'total_current_stock', 'avg_min_stock', 'avg_max_stock', 'status']])
                
            except Exception as e:
                st.error(f"❌ Ошибка сравнения: {e}")

    # Показать состояние системы
    if st.checkbox("🔍 Показать отладочную информацию"):
        st.write("**Состояние системы:**")
        st.write(f"- _new_max_stock_ready: {getattr(system, '_new_max_stock_ready', 'НЕТ')}")
        st.write(f"- new_max_stock_calculator: {hasattr(system, 'new_max_stock_calculator')}")
        st.write(f"- new_calculated_max_stock: {hasattr(system, 'new_calculated_max_stock')}")
        st.write(f"- calculated_ads: {hasattr(system, 'calculated_ads') and system.calculated_ads is not None}")
        st.write(f"- stock_data: {hasattr(system, 'stock_data') and system.stock_data is not None}")
def subcategory_abc_analysis_page(system):
    """Страница ABC анализа по подкатегориям"""
    st.header("🔤📊 ABC анализ по подкатегориям")
    
    st.markdown("""
    **Расширенный ABC анализ** с детализацией до подкатегорий позволяет:
    - 🎯 Более точно управлять ассортиментом на уровне подгрупп
    - 📈 Выявлять эффективные и неэффективные подкатегории
    - 🔍 Анализировать концентрацию продаж внутри категорий
    - 💡 Получать рекомендации по оптимизации структуры товаров
    """)
    
    status = system.get_system_status()
    
    # Проверяем наличие ABC данных
    if not status['abc_analysis']['analyzed']:
        st.warning("⚠️ Сначала необходимо выполнить основной ABC анализ")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔤 Перейти к ABC анализу"):
                st.info("Переключитесь на вкладку 'ABC анализ' для загрузки данных")
        
        with col2:
            st.info("""
            **Для анализа подкатегорий нужны:**
            - Основной ABC анализ
            - Данные с подкатегориями товаров
            - Информация о продажах
            """)
        return
    
    # Проверяем статус анализа подкатегорий
    subcategory_status = status.get('subcategory_analysis', {})
    
    if not subcategory_status.get('analyzed', False):
        # Анализ еще не выполнен
        st.info("📊 Основной ABC анализ выполнен. Готов к анализу подкатегорий.")
        
        # Показываем информацию о доступных данных
        if hasattr(system, 'abc_data') and system.abc_data is not None:
            abc_data = system.abc_data
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Товаров в ABC", len(abc_data))
            with col2:
                categories_count = abc_data['category'].nunique() if 'category' in abc_data.columns else 0
                st.metric("Категорий", categories_count)
            with col3:
                subcategories_count = abc_data['subcategory'].nunique() if 'subcategory' in abc_data.columns else 0
                st.metric("Подкатегорий", subcategories_count)
            with col4:
                ratio = subcategories_count / categories_count if categories_count > 0 else 0
                st.metric("Подкат./Категория", f"{ratio:.1f}")
            
            # Предварительный анализ структуры
            if 'subcategory' in abc_data.columns:
                st.success("✅ Данные содержат информацию о подкатегориях")
                
                # Показываем примеры подкатегорий
                with st.expander("👁️ Предварительный просмотр подкатегорий"):
                    sample_subcategories = abc_data.groupby(['category', 'subcategory']).size().reset_index(name='товаров')
                    sample_subcategories = sample_subcategories.head(10)
                    st.dataframe(sample_subcategories, use_container_width=True)
                
            else:
                st.warning("""
                ⚠️ **Колонка 'subcategory' не найдена**
                
                Система попытается создать подкатегории из категорий.
                Для лучших результатов убедитесь что в исходных данных есть:
                - Колонка 'subcategory' с названиями подкатегорий
                - Логичная иерархия: категория → подкатегория → товар
                """)
            
            # Кнопка запуска анализа
            if st.button("🚀 Выполнить анализ подкатегорий", use_container_width=True):
                with st.spinner("Выполнение ABC анализа по подкатегориям..."):
                    analysis_result = system.perform_subcategory_abc_analysis()
                    
                    if analysis_result['success']:
                        st.success("✅ Анализ подкатегорий завершен успешно!")
                        
                        # Показываем краткие результаты
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Подкатегорий проанализировано", analysis_result['total_subcategories'])
                        with col2:
                            st.metric("Товаров обработано", analysis_result['total_items'])
                        with col3:
                            st.metric("Категорий охвачено", analysis_result['categories_analyzed'])
                        
                        st.rerun()
                    else:
                        st.error(f"❌ {analysis_result['error']}")
        else:
            st.error("❌ Данные ABC анализа недоступны")
    
    else:
        # Анализ выполнен - показываем результаты
        st.success("✅ Анализ подкатегорий выполнен!")
        
        # Получаем сводку
        subcategory_summary = system.get_subcategory_summary_report()
        
        if subcategory_summary and 'error' not in subcategory_summary:
            # Общая статистика
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Подкатегорий", subcategory_summary['total_subcategories'])
            with col2:
                st.metric("Эффективных", f"{subcategory_summary['efficient_subcategories']}")
            with col3:
                st.metric("Эффективность", f"{subcategory_summary['efficiency_percentage']:.1f}%")
            with col4:
                st.metric("Товаров/Подкат.", f"{subcategory_summary['average_items_per_subcategory']:.1f}")
            with col5:
                st.metric("Категорий", subcategory_summary['categories_analyzed'])
            
            # ABC распределение
            st.subheader("🔤 ABC распределение по подкатегориям")
            abc_dist = subcategory_summary['abc_distribution']
            
            abc_col1, abc_col2, abc_col3 = st.columns(3)
            with abc_col1:
                st.metric("🔴 A товары", abc_dist['A'])
            with abc_col2:
                st.metric("🟡 B товары", abc_dist['B'])
            with abc_col3:
                st.metric("🟢 C товары", abc_dist['C'])
            
            # Визуализация ABC распределения
            if hasattr(system, 'subcategory_analyzer'):
                visualizations = system.subcategory_analyzer.create_subcategory_visualizations()
                
                if 'abc_distribution' in visualizations:
                    st.plotly_chart(visualizations['abc_distribution'], use_container_width=True)
        
        # Основной интерфейс анализа подкатегорий
        st.markdown("---")
        
        # Используем ABC данные из системы
        if hasattr(system, 'abc_data') and system.abc_data is not None:
            create_subcategory_abc_interface(system.abc_data)
        
        # Дополнительные действия
        st.subheader("📤 Экспорт и управление")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Экспорт подкатегорий Excel"):
                excel_buffer = system.export_subcategory_results()
                
                if excel_buffer:
                    st.download_button(
                        label="💾 Скачать отчет подкатегорий",
                        data=excel_buffer,
                        file_name=f"subcategory_abc_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("❌ Ошибка создания Excel файла")
        
        with col2:
            if st.button("🔄 Пересчитать анализ"):
                # Очищаем результаты для пересчета
                if hasattr(system, 'subcategory_results'):
                    system.subcategory_results = None
                if hasattr(system, 'subcategory_analyzer'):
                    system.subcategory_analyzer.subcategory_results = None
                st.success("✅ Данные очищены. Нажмите 'Выполнить анализ' для пересчета.")
                st.rerun()
        
        with col3:
            # Показываем краткие рекомендации
            if hasattr(system, 'subcategory_results') and system.subcategory_results:
                recommendations = system.subcategory_results.get('recommendations', [])
                if recommendations:
                    with st.popover("💡 Рекомендации"):
                        for i, rec in enumerate(recommendations[:3], 1):
                            st.write(f"**{i}.** {rec}")
                        if len(recommendations) > 3:
                            st.write(f"... и еще {len(recommendations) - 3} рекомендаций")

def show_system_status(system):
    """Отображение статуса системы"""
    status = system.get_system_status()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
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

    with col5:
        subcat_status = "✅" if status['subcategory_analysis']['analyzed'] else "❌"
        subcat_count = status['subcategory_analysis']['subcategories_count']
        st.metric(
            "Подкатегории", 
            f"{subcat_status} {subcat_count} подкат."
        )
    
    # Прогресс-бар
    progress = status['overall']['progress_percentage']
    st.progress(progress / 100)
    st.write(f"**Общий прогресс:** {progress:.0f}% ({status['overall']['completed_steps']}/5 этапов)")

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
        
       
        if IMPROVED_ADS_FIX_AVAILABLE:
            st.markdown("---")
            st.subheader("🧠 Умная работа с категориями")
            
            # Вкладки для организации
            tab1, tab2, tab3 = st.tabs([
                "🔧 Умное исправление", 
                "📊 Статистика категорий", 
                "🔄 Отмена изменений"
            ])
            
            with tab1:
                show_improved_category_ads_fix_ui(system)
            
            with tab2:
                show_improved_category_statistics_ui(system)
            
            with tab3:
                show_improved_revert_ui(system)
        else:
            # Быстрая версия без полного UI
            quick_streamlit_integration(system)

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
        # Фильтруем только товары с положительным ADS из загруженного файла
        top_ads = ads_data[ads_data['ads'] > 0].nlargest(10, 'ads')

        # Дополнительная проверка на валидность данных
        if len(top_ads) == 0:
            st.warning("⚠️ Нет товаров с положительным ADS")
        else:
            fig_ads = px.bar(
                top_ads,
                x='ads',
                y='номенклатура',
                orientation='h',
                title=f'Топ-{len(top_ads)} товаров по ADS (из загруженного файла)',
                labels={'ads': 'Среднедневные продажи', 'номенклатура': 'Товар'}
            )
            st.plotly_chart(fig_ads, use_container_width=True)

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
                        st.metric("Номенклатура из", load_result.get('nomenclature_column', 'B'))
                    with col3:
                        st.metric("Общий ADS", f"{load_result.get('total_ads', 0):.2f}")
                    with col4:
                        st.metric("JSON создан", "✅" if load_result.get('json_data_created', False) else "❌")
                    
                    # Информация о обработке
                    st.info(f"""
                    **Результаты обработки:**
                    - Формула: {load_result.get('formula', 'ADS = среднее/30')}
                    - Диапазон: {load_result.get('range_used', 'M4:AB')}
                    - Последняя строка исключена: {'✅' if load_result.get('last_row_excluded', False) else '❌'}
                    - С положительным ADS: {load_result.get('items_with_positive_ads', 0)} товаров
                    """)
                    
                    st.rerun()
                else:
                    st.error(f"❌ {load_result['error']}")
        try:
            from minimal_ads_zero_category_fix import auto_fix_ads_zero_and_show_result
            auto_fix_ads_zero_and_show_result(system)
        except ImportError:
            pass

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
    # Проверяем наличие ценовых данных
    has_price_data = 'last_purchase_price' in comparison_data.columns and 'stock_deficit_money' in comparison_data.columns

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
    # Добавляем денежные колонки если есть данные
    if has_price_data:
        display_columns.extend(['last_purchase_price', 'stock_deficit_money', 'recommended_order_money'])
        column_config.update({
            'last_purchase_price': 'Цена (₽)',
            'stock_deficit_money': 'Дефицит (₽)', 
            'recommended_order_money': 'К заказу (₽)'
        })
    
    
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

    if 'subcategory_analysis' in summary:
        subcat = summary['subcategory_analysis']
        st.write(f"**ABC анализ подкатегорий**: {subcat['total_subcategories']} подкатегорий в {subcat['categories_with_subcategories']} категориях")
        st.write(f"- Эффективных подкатегорий: {subcat['efficient_subcategories']} ({subcat['efficiency_percentage']:.1f}%)")
        st.write(f"- Среднее товаров на подкатегорию: {subcat['avg_items_per_subcategory']:.1f}")
        
        # ABC распределение по подкатегориям
        subcat_abc = subcat['subcategory_abc_distribution']
        st.write(f"- ABC в подкатегориях: A={subcat_abc['A']}, B={subcat_abc['B']}, C={subcat_abc['C']}")

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
    
    col1, col2, col3 = st.columns(3)
    
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
        if status['subcategory_analysis']['analyzed']:
            if st.button("🔤📊 Отчет подкатегорий", use_container_width=True):
                with st.spinner("Создание отчета подкатегорий..."):
                    try:
                        excel_buffer = system.export_subcategory_results()
                        
                        if excel_buffer:
                            st.download_button(
                                label="💾 Скачать отчет подкатегорий",
                                data=excel_buffer,
                                file_name=f"subcategory_abc_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            
                            st.success("✅ Отчет подкатегорий готов!")
                        else:
                            st.error("❌ Ошибка создания отчета подкатегорий")
                            
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
        else:
            st.info("Выполните анализ подкатегорий для экспорта")
    with col3:
        # Информация о содержимом файлов
        st.info("""
        **Содержимое полного Excel файла:**
        - Общий статус системы
        - ABC анализ (основной)
        - ABC анализ подкатегорий ✨
        - ADS расчеты
        - Минимальные запасы
        - Сравнение остатков
        - Парето анализ подкатегорий ✨
        - Товары с дефицитом
        - Критичные товары  
        - Рекомендации по заказу
        
        ✨ = Новые разделы
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
    st.subheader("🔤📊 Настройки анализа подкатегорий")
    
    status = system.get_system_status()
    subcategory_status = status.get('subcategory_analysis', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        if subcategory_status.get('analyzed', False):
            st.success("✅ Анализ подкатегорий выполнен")
            
            # Показываем краткую статистику
            if hasattr(system, 'subcategory_results') and system.subcategory_results:
                subcategory_summary = system.get_subcategory_summary_report()
                
                if subcategory_summary and 'error' not in subcategory_summary:
                    st.metric("Подкатегорий", subcategory_summary['total_subcategories'])
                    st.metric("Эффективность", f"{subcategory_summary['efficiency_percentage']:.1f}%")
        else:
            st.info("Анализ подкатегорий не выполнен")
    
    with col2:
        if st.button("🗑️ Очистить анализ подкатегорий"):
            if hasattr(system, 'subcategory_results'):
                system.subcategory_results = None
            if hasattr(system, 'subcategory_analyzer'):
                system.subcategory_analyzer.subcategory_results = None
                system.subcategory_analyzer.abc_data = None
            st.success("✅ Анализ подкатегорий очищен!")
            st.rerun()
    # Управление данными
    st.subheader("🗂️ Управление данными")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Очистить все данные", use_container_width=True):
            system.clear_all_data()
            # Также очищаем данные подкатегорий
            if hasattr(system, 'subcategory_results'):
                system.subcategory_results = None
            if hasattr(system, 'subcategory_analyzer'):
                del system.subcategory_analyzer
            st.success("✅ Все данные очищены!")
            st.rerun()
    
    with col2:
        status = system.get_system_status()
        if status['overall']['progress_percentage'] > 0:
            st.metric("Загружено данных", f"{status['overall']['progress_percentage']:.0f}%")
        else:
            st.info("Данные не загружены")
    
    with col3:
        # Диагностика системы
        if st.button("🔍 Диагностика системы"):
            st.subheader("🔧 Диагностическая информация")
            
            # Проверяем все компоненты
            components_status = {
                'ABC данные': hasattr(system, 'abc_data') and system.abc_data is not None,
                'ABC результаты': hasattr(system, 'abc_results') and system.abc_results is not None,
                'ADS данные': hasattr(system, 'calculated_ads') and system.calculated_ads is not None,
                'MIN запасы': hasattr(system, 'calculated_min_stock') and system.calculated_min_stock is not None,
                'Остатки': hasattr(system, 'stock_data') and system.stock_data is not None,
                'Сравнение остатков': hasattr(system, 'stock_comparison') and system.stock_comparison is not None,
                'Анализатор подкатегорий': hasattr(system, 'subcategory_analyzer'),
                'Результаты подкатегорий': hasattr(system, 'subcategory_results') and system.subcategory_results is not None
            }
            
            for component, status_val in components_status.items():
                status_icon = "✅" if status_val else "❌"
                st.write(f"{status_icon} {component}")
    
    # Информация о системе
    st.subheader("ℹ️ Информация о системе")
    
    st.markdown("""
    **Модульная система анализа товарных запасов v2.0**
    
    **Возможности:**
    - 🔤 ABC анализ по принципу Парето
    - 🔤📊 **ABC анализ по подкатегориям** ✨
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
    
    **Новое в v2.0:**
    - ✨ Анализ ABC по подкатегориям
    - ✨ Парето-анализ подкатегорий  
    - ✨ Рекомендации по оптимизации структуры
    - ✨ Анализ эффективности подкатегорий
    """)

def main():
    """Основная функция приложения"""
    # Инициализация системы
    system = init_system()
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Диагностика исправлений")

    if check_complete_fix_status(system):
        st.sidebar.success("✅ Полное исправление активно")
    else:
        st.sidebar.error("❌ Исправление не применено")
        if st.sidebar.button("🔄 Применить полное исправление"):
            apply_complete_fix_to_system(system)
            st.rerun()

    # Кнопка диагностики
    if st.sidebar.button("🔍 Диагностировать проблемы"):
        diagnose_system_issues(system)
    # НОВОЕ: Применяем интеграцию цен (если доступна)
    if PRICE_INTEGRATION_AVAILABLE:
        complete_price_integration_setup(system)
        
        # Показываем статус в sidebar
        show_price_integration_status_in_streamlit(system)

    if PRICE_FEATURES_AVAILABLE:
        apply_price_fixes_to_system(system)
        
        # Добавляем статус цен в sidebar
        show_money_integration_status(system)
        integration_instructions()
    
    # Заголовок
    st.title("📦 Модульная система анализа товарных запасов")
    st.markdown("*Пошаговый анализ с выбором типа операции*")
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("🧭 Навигация")
        
        # Показываем статус системы
        st.subheader("📊 Статус системы")
        show_system_status(system)

        if PRICE_FEATURES_AVAILABLE and st.button("🔍 Проверить цены"):
            quick_price_check(system)
        
        st.markdown("---")
        
        # ВАЖНО: Определяем переменную page ЗДЕСЬ, в sidebar
        page = st.selectbox(
            "Выберите раздел:",
            [
                "🔤 ABC анализ",
                "📊 ADS расчет",
                "🔤📊 ABC подкатегории",
                "📋 MIN запасы",
                "🏪 Анализ складов",
                "⚖️ Сравнение остатков",
                "📦 MAX остатки",
                "🚚 Рекомендации по перемещениям", 
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
        elif not status['subcategory_analysis']['analyzed']:
            st.button("📊 Анализ подкатегорий", key="quick_subcategory")
        elif not status['sales_analysis']['ads_calculated']:
            st.button("📊 Рассчитать ADS", key="quick_ads")
        elif not status['min_stock_analysis']['calculated']:
            st.button("📋 MIN запасы", key="quick_min")
        elif not status['stock_analysis']['compared']:
            st.button("⚖️ Сравнить остатки", key="quick_compare")
        
        else:
            st.button("📤 Экспорт", key="quick_export")
    
    # Основной контент в зависимости от выбранной страницы
    # ТЕПЕРЬ переменная page уже определена выше
    if page == "🔤 ABC анализ":
        abc_analysis_page_updated(system)
    elif page == "📊 ADS расчет":
        ads_calculation_page_updated(system)
        if PRICE_FEATURES_AVAILABLE:
            add_price_info_to_ads_page(system)
    elif page == "🔤📊 ABC подкатегории":  
        subcategory_abc_analysis_page(system)
    elif page == "📋 MIN запасы":
        min_stock_calculation_page(system)
    elif page == "🏪 Анализ складов":
        warehouse_analysis_page(system)
    elif page == "⚖️ Сравнение остатков":
        if PRICE_FEATURES_AVAILABLE:
            stock_comparison_page_with_money(system)  # НОВАЯ ФУНКЦИЯ
        else:
            stock_comparison_page(system)  # Старая функция
    elif page == "📦 MAX остатки":
        max_stock_page(system)
    elif page == "🚚 Рекомендации по перемещениям":
            show_movement_recommendations_page(system)
    elif page == "📤 Экспорт результатов":
        export_page(system)
        if PRICE_FEATURES_AVAILABLE:
            update_export_page_with_money(system)  # ДОБАВЛЯЕМ ДЕНЕЖНЫЙ ЭКСПОРТ
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
            2. 🔤📊 ABC анализ по подкатегориям (детализация)
            3. 📊 Расчет ADS из файла продаж
            4. 📋 Расчет минимальных запасов
            5. ⚖️ Загрузка остатков и сравнение
            6. 📤 Экспорт результатов
            """)
    
    with col2:
        status = system.get_system_status()  # Получаем статус заново
        progress = status['overall']['progress_percentage']
        if progress == 100:
            st.success("✅ Все этапы завершены!")
        else:
            st.info(f"📊 Прогресс: {progress:.0f}%")
    
    with col3:
        st.caption(f"Система v2.0 | SIRIUS {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

def max_stock_page(system):
    """Окончательно исправленная страница для работы с новыми максимальными остатками"""
    st.header("📦 Новые максимальные остатки")
    
    # Проверка инициализации НОВЫХ максимальных остатков
    if not hasattr(system, '_new_max_stock_ready') or not system._new_max_stock_ready:
        st.error("❌ Новые максимальные остатки не инициализированы")
        if st.button("🔄 Переинициализировать"):
            try:
                from new_max_stock_calculator import replace_max_stock_functionality
                replace_max_stock_functionality(system)
                system._new_max_stock_ready = True
                st.success("✅ Новые максимальные остатки подключены")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
        return
    
    # Настройки параметров
    st.subheader("⚙️ Настройки параметров")
    
    col1, col2 = st.columns(2)
    with col1:
        point_type = st.selectbox("Тип точки:", ['хабы', 'склады', 'магазины'])
    with col2:
        # Инициализация session_state для показа настроек
        if 'show_settings' not in st.session_state:
            st.session_state.show_settings = False
            
        if st.button("📋 Показать настройки"):
            st.session_state.show_settings = not st.session_state.show_settings
        
        # Показ настроек если флаг активен
        if st.session_state.show_settings:
            if hasattr(system, 'new_max_stock_calculator'):
                settings = system.new_max_stock_calculator.default_settings
                
                st.write("**📋 Текущие настройки максимальных остатков:**")
                for ptype, config in settings.items():
                    st.write(f"**🏪 {ptype.upper()}:** {config.get('description', '')}")
                    st.write(f"   - MIN: {config['min_days']} дней")
                    st.write(f"   - MAX: {config['max_days']} дней")
                    st.write("---")
            else:
                st.warning("Калькулятор не инициализирован")

    col3, col4 = st.columns(2)
    with col3:
        min_days = st.number_input("Дни MIN запаса:", min_value=1, max_value=180, value=10)
    with col4:
        max_days = st.number_input("Дни MAX запаса:", min_value=min_days, max_value=365, value=25)

    if st.button("💾 Обновить настройки"):
        try:
            system.update_new_max_stock_settings(point_type, min_days, max_days)
            st.success(f"✅ Настройки обновлены: {point_type} = MIN:{min_days}д, MAX:{max_days}д")
        except Exception as e:
            st.error(f"❌ Ошибка обновления настроек: {e}")

    st.divider()

    # РАСЧЕТ новых максимальных остатков
    st.subheader("📊 Расчет новых максимальных остатков")

    if st.button("🔄 Рассчитать НОВЫЕ MAX остатки"):
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            st.error("❌ Сначала рассчитайте ADS")
        else:
            with st.spinner("Расчет новых максимальных остатков..."):
                result = system.calculate_new_max_stock()
                
                if result['success']:
                    st.success("✅ Новые максимальные остатки рассчитаны!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Товаров", result['total_items'])
                    with col2:
                        st.metric("Общий MAX запас", f"{result['total_avg_max_stock']:,.0f}")
                    with col3:
                        st.metric("Средний MAX на товар", f"{result['avg_max_per_item']:.1f}")
                    
                    # Устанавливаем флаг что остатки рассчитаны
                    st.session_state.max_stock_calculated = True
                            
                else:
                    st.error(f"❌ {result['error']}")
    
    st.divider()
    
    # АНАЛИЗ рассчитанных остатков - всегда показываем если остатки есть
    st.subheader("📊 Анализ рассчитанных остатков")
    
    # Проверяем что остатки рассчитаны
    if hasattr(system, 'new_calculated_max_stock') and system.new_calculated_max_stock is not None:
        st.info("✅ Новые максимальные остатки рассчитаны и готовы для анализа")
        
        # Инициализация session_state для показа сводки
        if 'show_summary' not in st.session_state:
            st.session_state.show_summary = False
        if 'show_table' not in st.session_state:
            st.session_state.show_table = False
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Показать детальную сводку"):
                st.session_state.show_summary = not st.session_state.show_summary
        
        with col2:
            if st.button("📋 Показать таблицу MAX остатков"):
                st.session_state.show_table = not st.session_state.show_table
        
        # Показ детальной сводки если флаг активен
        if st.session_state.show_summary:
            try:
                summary = system.get_new_max_stock_summary()
                if 'error' not in summary:
                    st.write("**📊 Детальная сводка MAX остатков:**")
                    
                    # Общие параметры
                    st.write(f"**Общие параметры:**")
                    st.write(f"- Товаров: {summary['total_items']}")
                    st.write(f"- Средние дни MIN: {summary['avg_parameters']['min_days']:.1f}")
                    st.write(f"- Средние дни MAX: {summary['avg_parameters']['max_days']:.1f}")
                    
                    # Общие итоги
                    st.write(f"**Общие итоги:**")
                    st.write(f"- Общий MIN запас: {summary['totals']['avg_min_stock']:,.0f}")
                    st.write(f"- Общий MAX запас: {summary['totals']['avg_max_stock']:,.0f}")
                    st.write(f"- Рабочий диапазон: {summary['totals']['avg_range']:,.0f}")
                    
                    # По типам точек
                    if summary['per_location']:
                        st.write(f"**По типам точек:**")
                        for loc_type, data in summary['per_location'].items():
                            with st.expander(f"🏪 {loc_type.upper()}"):
                                st.write(f"- MIN дни: {data['min_days']}")
                                st.write(f"- MAX дни: {data['max_days']}")
                                st.write(f"- Общий MIN запас: {data['total_min_stock']:,.0f}")
                                st.write(f"- Общий MAX запас: {data['total_max_stock']:,.0f}")
                                st.write(f"- Средний MIN: {data['avg_min_stock']:.1f}")
                                st.write(f"- Средний MAX: {data['avg_max_stock']:.1f}")
                else:
                    st.error(f"❌ {summary['error']}")
            except Exception as e:
                st.error(f"❌ Ошибка получения сводки: {e}")
        
        # Показ таблицы если флаг активен
        if st.session_state.show_table:
            try:
                st.write("**📋 Таблица рассчитанных максимальных остатков:**")
                
                # Определяем доступные колонки
                all_cols = system.new_calculated_max_stock.columns.tolist()
                display_cols = []
                
                # Приоритетные колонки для показа
                priority_cols = ['номенклатура', 'ads', 'avg_min_stock', 'avg_max_stock', 'avg_range']
                
                # Добавляем колонки которые есть в данных
                for col in priority_cols:
                    if col in all_cols:
                        display_cols.append(col)
                
                # Если основных колонок нет, показываем первые 5 доступных
                if not display_cols:
                    display_cols = all_cols[:5]
                
                if display_cols:
                    st.dataframe(
                        system.new_calculated_max_stock[display_cols].head(50),
                        use_container_width=True
                    )
                    st.info(f"Показано первых 50 из {len(system.new_calculated_max_stock)} товаров")
                else:
                    st.error("❌ Не найдены подходящие колонки для отображения")
                    
            except Exception as e:
                st.error(f"❌ Ошибка показа таблицы: {e}")
    else:
        st.warning("⚠️ Новые максимальные остатки не рассчитаны. Нажмите кнопку 'Рассчитать НОВЫЕ MAX остатки' выше.")
    
    st.divider()
    
    # СРАВНЕНИЕ с НОВЫМИ максимальными остатками
    st.subheader("⚖️ Сравнение с текущими остатками")
    
    if st.button("📊 Сравнить с НОВЫМИ MIN/MAX"):
        # Проверяем НОВЫЕ максимальные остатки
        if not hasattr(system, 'new_calculated_max_stock') or system.new_calculated_max_stock is None:
            st.error("❌ Сначала рассчитайте НОВЫЕ максимальные остатки")
        elif not hasattr(system, 'stock_data') or system.stock_data is None:
            st.error("❌ Сначала загрузите текущие остатки")
        else:
            # Создаем простое сравнение с новыми максимальными остатками
            try:
                import pandas as pd
                
                max_data = system.new_calculated_max_stock
                stock_data = system.stock_data
                
                # Объединяем данные
                comparison = pd.merge(
                    max_data[['номенклатура', 'avg_min_stock', 'avg_max_stock']],
                    stock_data[['номенклатура', 'total_current_stock']],
                    on='номенклатура',
                    how='inner'
                )
                
                # Определяем статусы
                comparison['status'] = 'НОРМА'
                comparison.loc[comparison['total_current_stock'] < comparison['avg_min_stock'], 'status'] = 'НЕДОСТАТОК'
                comparison.loc[comparison['total_current_stock'] > comparison['avg_max_stock'], 'status'] = 'ИЗБЫТОК'
                
                # Подсчитываем статистику
                status_counts = comparison['status'].value_counts()
                
                st.success("✅ Сравнение с НОВЫМИ максимальными остатками выполнено!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Недостаток", status_counts.get('НЕДОСТАТОК', 0))
                with col2:
                    st.metric("Избыток", status_counts.get('ИЗБЫТОК', 0))
                with col3:
                    st.metric("Норма", status_counts.get('НОРМА', 0))
                
                # Показываем детали
                with st.expander("📋 Детали сравнения"):
                    st.dataframe(comparison[['номенклатура', 'total_current_stock', 'avg_min_stock', 'avg_max_stock', 'status']])
                
            except Exception as e:
                st.error(f"❌ Ошибка сравнения: {e}")

    # Показать состояние системы
    if st.checkbox("🔍 Показать отладочную информацию"):
        st.write("**Состояние системы:**")
        st.write(f"- _new_max_stock_ready: {getattr(system, '_new_max_stock_ready', 'НЕТ')}")
        st.write(f"- new_max_stock_calculator: {hasattr(system, 'new_max_stock_calculator')}")
        st.write(f"- new_calculated_max_stock: {hasattr(system, 'new_calculated_max_stock')}")
        st.write(f"- calculated_ads: {hasattr(system, 'calculated_ads') and system.calculated_ads is not None}")
        st.write(f"- stock_data: {hasattr(system, 'stock_data') and system.stock_data is not None}")
        
        # Показать session_state
        st.write("**Session State:**")
        st.write(f"- show_settings: {st.session_state.get('show_settings', 'НЕТ')}")
        st.write(f"- show_summary: {st.session_state.get('show_summary', 'НЕТ')}")
        st.write(f"- show_table: {st.session_state.get('show_table', 'НЕТ')}")
        
        # Показать данные если есть
        if hasattr(system, 'new_calculated_max_stock') and system.new_calculated_max_stock is not None:
            st.write(f"**Данные новых MAX остатков:**")
            st.write(f"- Строк: {len(system.new_calculated_max_stock)}")
            st.write(f"- Колонки: {list(system.new_calculated_max_stock.columns)}")
if __name__ == "__main__":
    main()