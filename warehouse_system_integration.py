# warehouse_system_integration.py
"""
🔧 ИНТЕГРАЦИЯ УЛУЧШЕННОЙ СИСТЕМЫ АНАЛИЗА СКЛАДОВ
Показывает как подключить все улучшения к существующей системе
"""

import streamlit as st
from enhanced_warehouse_interface import apply_enhanced_warehouse_interface, create_enhanced_warehouse_page
from warehouse_complete_solution import apply_complete_warehouse_solution


def integrate_complete_warehouse_system(system):
    """
    Полная интеграция улучшенной системы анализа складов
    """
    
    st.header("🔧 Интеграция улучшенной системы складов")
    
    integration_steps = []
    
    # Шаг 1: Базовое решение анализа складов
    if not hasattr(system, '_warehouse_complete_solution_applied'):
        with st.spinner("Применяю базовое решение анализа складов..."):
            success = apply_complete_warehouse_solution(system)
            if success:
                integration_steps.append("✅ Базовое решение анализа складов")
            else:
                integration_steps.append("❌ Ошибка базового решения")
    else:
        integration_steps.append("✅ Базовое решение анализа складов (уже применено)")
    
    # Шаг 2: Улучшенный интерфейс
    if not hasattr(system, '_enhanced_warehouse_interface_applied'):
        with st.spinner("Применяю улучшенный интерфейс..."):
            success = apply_enhanced_warehouse_interface(system)
            if success:
                integration_steps.append("✅ Улучшенный интерфейс с ценами")
            else:
                integration_steps.append("❌ Ошибка улучшенного интерфейса")
    else:
        integration_steps.append("✅ Улучшенный интерфейс с ценами (уже применен)")
    
    # Показываем результаты интеграции
    st.subheader("📋 Результаты интеграции:")
    for step in integration_steps:
        st.write(step)
    
    # Проверка готовности системы
    system_ready = (
        hasattr(system, '_warehouse_complete_solution_applied') and
        hasattr(system, '_enhanced_warehouse_interface_applied')
    )
    
    if system_ready:
        st.success("🎉 **Система полностью готова!** Все улучшения применены.")
        
        # Показываем возможности системы
        show_system_capabilities(system)
        
        return True
    else:
        st.error("❌ Система не готова. Не все компоненты применены.")
        return False


def show_system_capabilities(system):
    """
    Показывает возможности улучшенной системы
    """
    
    st.subheader("🚀 Возможности улучшенной системы:")
    
    capabilities = [
        "📊 **Умное чтение файлов остатков** - автоматически определяет любую структуру",
        "💰 **Автоматический поиск цен** - находит цены в ADS данных и файлах магазинов", 
        "📈 **MIN/MAX остатки** - персональные настройки для каждого склада",
        "🎯 **Объяснение расчетов** - показывает как рассчитывается 'к заказу'",
        "📋 **Отображение ВСЕХ товаров** - без ограничений количества",
        "🔍 **Мощные фильтры** - по статусу, складу, ценам",
        "📊 **Детальная аналитика** - графики, сводки, ТОП списки",
        "💾 **Excel экспорт** - полные отчеты с ценами и расчетами",
        "🎨 **Современный интерфейс** - цветовая кодировка, иконки статусов"
    ]
    
    for capability in capabilities:
        st.write(capability)
    
    # Кнопки быстрого доступа
    st.subheader("⚡ Быстрый доступ:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Найти цены в системе"):
            if hasattr(system, 'find_and_display_prices'):
                system.find_and_display_prices()
            else:
                st.error("Метод поиска цен не найден")
    
    with col2:
        if st.button("📊 Объяснить расчеты"):
            if hasattr(system, 'show_order_calculation_help'):
                system.show_order_calculation_help()
            else:
                st.error("Метод объяснения расчетов не найден")
    
    with col3:
        if st.button("📋 Показать последний анализ"):
            if hasattr(system, '_last_warehouse_analysis') and system._last_warehouse_analysis:
                if hasattr(system, 'display_enhanced_results'):
                    system.display_enhanced_results(system._last_warehouse_analysis)
                else:
                    st.error("Метод отображения результатов не найден")
            else:
                st.info("Нет сохраненных результатов анализа")


def create_warehouse_integration_page(system):
    """
    Создает страницу интеграции для анализа складов
    """
    
    st.header("🔧 Интеграция системы анализа складов")
    st.markdown("*Подключение всех улучшений и проверка готовности*")
    
    # Диагностика текущего состояния
    st.subheader("🔍 Диагностика системы")
    
    diagnostics = {
        "Система инициализирована": hasattr(st.session_state, 'inventory_system'),
        "ADS данные загружены": hasattr(system, 'calculated_ads') and system.calculated_ads is not None,
        "Базовое решение складов": hasattr(system, '_warehouse_complete_solution_applied'),
        "Улучшенный интерфейс": hasattr(system, '_enhanced_warehouse_interface_applied'),
        "Методы поиска цен": hasattr(system, 'find_and_display_prices'),
        "Методы отображения": hasattr(system, 'display_enhanced_results'),
        "Последний анализ": hasattr(system, '_last_warehouse_analysis')
    }
    
    for check, status in diagnostics.items():
        icon = "✅" if status else "❌"
        st.write(f"{icon} {check}")
    
    # Кнопка полной интеграции
    st.markdown("---")
    
    if st.button("🚀 Применить все улучшения", type="primary"):
        integrate_complete_warehouse_system(system)
    
    # Если система готова, показываем дополнительные возможности
    all_ready = all(diagnostics.values())
    
    if all_ready:
        st.markdown("---")
        show_system_capabilities(system)
    
    # Инструкции по использованию
    st.markdown("---")
    show_usage_instructions()


def show_usage_instructions():
    """
    Показывает инструкции по использованию улучшенной системы
    """
    
    st.subheader("📖 Инструкции по использованию")
    
    with st.expander("🎯 Пошаговое руководство", expanded=False):
        st.markdown("""
        ### 1️⃣ **Подготовка данных:**
        - Загрузите файлы продаж на странице "ADS расчет" 
        - Рассчитайте ADS для всех товаров
        - Убедитесь что в файлах есть ценовая информация
        
        ### 2️⃣ **Интеграция системы:**
        - Нажмите кнопку "Применить все улучшения" на этой странице
        - Дождитесь завершения интеграции всех компонентов
        - Проверьте что все пункты диагностики отмечены ✅
        
        ### 3️⃣ **Анализ складов:**
        - Перейдите на страницу "Анализ складов"
        - Загрузите файл остатков (поддерживается любая структура)
        - Запустите анализ с нужными параметрами MIN/MAX дней
        
        ### 4️⃣ **Просмотр результатов:**
        - Изучите объяснение расчета "к заказу"
        - Найдите ценовые данные в системе
        - Используйте фильтры и сортировку для анализа
        - Просмотрите MIN/MAX остатки по складам
        
        ### 5️⃣ **Экспорт и отчеты:**
        - Создайте Excel отчет с полной аналитикой
        - Просмотрите ТОП товары по стоимости заказа
        - Изучите ценовую сводку по складам
        """)
    
    with st.expander("🔧 Технические детали", expanded=False):
        st.markdown("""
        ### 🎯 **Что улучшено:**
        
        **Расчет колонки "К заказу":**
        - 🔴 КРИТИЧНЫЙ: остаток < 50% MIN → заказать до MAX
        - 🟡 ВНИМАНИЕ: остаток < MIN → заказать до MIN  
        - 🟢 В НОРМЕ: MIN ≤ остаток ≤ MAX → не заказывать
        - 🟠 ИЗБЫТОК: остаток > MAX → не заказывать
        
        **Поиск цен:**
        - Автоматически ищет в ADS данных
        - Проверяет данные всех магазинов
        - Поддерживает различные названия ценовых колонок
        - Рассчитывает стоимость заказов
        
        **MIN/MAX остатки:**
        - Каждый склад имеет персональные настройки дней
        - Автоматический расчет на основе ADS
        - Визуализация соответствия нормам
        - Приоритизация складов для закупок
        
        **Отображение товаров:**
        - Убрано ограничение в 100 товаров
        - Пагинация для больших объемов данных
        - Мощные фильтры и сортировка
        - Цветовая кодировка статусов
        """)
    
    with st.expander("⚠️ Решение проблем", expanded=False):
        st.markdown("""
        ### 🚨 **Частые проблемы:**
        
        **Проблема:** Не найдены ценовые данные
        **Решение:** 
        - Убедитесь что в файлах продаж есть колонки с ценами
        - Проверьте названия колонок: 'цена', 'price', 'last_purchase_price'
        - Перезагрузите файлы продаж
        
        **Проблема:** Неправильно определяются склады
        **Решение:**
        - Проверьте заголовки в файле остатков
        - Убедитесь что названия складов содержат ключевые слова
        - Включите режим отладки при чтении файла
        
        **Проблема:** Большая таблица тормозит
        **Решение:**
        - Используйте фильтры для уменьшения количества строк
        - Измените количество товаров на странице
        - Отключите цветовую кодировку для больших таблиц
        
        **Проблема:** ADS не рассчитан
        **Решение:**
        - Перейдите на страницу "ADS расчет"
        - Загрузите файлы продаж
        - Нажмите кнопку расчета ADS
        """)


def quick_warehouse_system_setup(system):
    """
    Быстрая настройка системы анализа складов
    """
    
    st.markdown("### ⚡ Быстрая настройка")
    
    if st.button("🚀 Настроить систему одной кнопкой"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Шаг 1: Базовое решение
            status_text.text("Применяю базовое решение...")
            progress_bar.progress(33)
            
            if not hasattr(system, '_warehouse_complete_solution_applied'):
                apply_complete_warehouse_solution(system)
            
            # Шаг 2: Улучшенный интерфейс  
            status_text.text("Применяю улучшенный интерфейс...")
            progress_bar.progress(66)
            
            if not hasattr(system, '_enhanced_warehouse_interface_applied'):
                apply_enhanced_warehouse_interface(system)
            
            # Шаг 3: Поиск цен
            status_text.text("Ищу ценовые данные...")
            progress_bar.progress(100)
            
            if hasattr(system, 'find_and_display_prices'):
                system.find_and_display_prices()
            
            # Завершение
            progress_bar.empty()
            status_text.empty()
            
            st.success("🎉 Система полностью настроена и готова к работе!")
            
        except Exception as e:
            st.error(f"❌ Ошибка настройки: {str(e)}")
            progress_bar.empty()
            status_text.empty()


# Функция для добавления в основное меню приложения
def add_enhanced_warehouse_menu_item():
    """
    Добавляет пункт улучшенного анализа складов в меню
    """
    
    return {
        "title": "📦 Улучшенный анализ складов",
        "icon": "📦",
        "description": "Анализ с ценами, MIN/MAX остатками и полным отображением",
        "page_function": create_warehouse_integration_page
    }


if __name__ == "__main__":
    print("🔧 Интеграция улучшенной системы анализа складов загружена")
    print("Функции: полная интеграция + диагностика + инструкции")