# quick_warehouse_upgrade.py
"""
⚡ БЫСТРОЕ ОБНОВЛЕНИЕ АНАЛИЗА СКЛАДОВ
Один файл для полного обновления системы анализа складов
"""

import streamlit as st


def apply_quick_warehouse_upgrade():
    """
    Быстрое применение всех улучшений анализа складов
    """
    
    st.header("⚡ Быстрое обновление анализа складов")
    st.markdown("*Применение всех улучшений одной кнопкой*")
    
    if st.button("🚀 Применить ВСЕ улучшения анализа складов", type="primary"):
        
        success_count = 0
        total_steps = 4
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Шаг 1: Базовое решение складов
            status_text.text("1/4 Применяю базовое решение анализа складов...")
            progress_bar.progress(0.25)
            
            try:
                from warehouse_complete_solution import apply_complete_warehouse_solution
                
                system = st.session_state.inventory_system
                if apply_complete_warehouse_solution(system):
                    success_count += 1
                    st.write("✅ Базовое решение анализа складов применено")
                else:
                    st.write("❌ Ошибка базового решения")
            except Exception as e:
                st.write(f"❌ Ошибка базового решения: {e}")
            
            # Шаг 2: Улучшенный интерфейс
            status_text.text("2/4 Применяю улучшенный интерфейс...")
            progress_bar.progress(0.5)
            
            try:
                from enhanced_warehouse_interface import apply_enhanced_warehouse_interface
                
                if apply_enhanced_warehouse_interface(system):
                    success_count += 1
                    st.write("✅ Улучшенный интерфейс с ценами применен")
                else:
                    st.write("❌ Ошибка улучшенного интерфейса")
            except Exception as e:
                st.write(f"❌ Ошибка улучшенного интерфейса: {e}")
            
            # Шаг 3: Поиск ценовых данных
            status_text.text("3/4 Ищу ценовые данные в системе...")
            progress_bar.progress(0.75)
            
            try:
                if hasattr(system, 'find_and_display_prices'):
                    system.find_and_display_prices()
                    success_count += 1
                    st.write("✅ Ценовые данные найдены и проанализированы")
                else:
                    st.write("⚠️ Функция поиска цен недоступна")
            except Exception as e:
                st.write(f"❌ Ошибка поиска цен: {e}")
            
            # Шаг 4: Проверка готовности
            status_text.text("4/4 Проверяю готовность системы...")
            progress_bar.progress(1.0)
            
            # Проверяем все компоненты
            checks = {
                "Базовое решение": hasattr(system, '_warehouse_complete_solution_applied'),
                "Улучшенный интерфейс": hasattr(system, '_enhanced_warehouse_interface_applied'),
                "Методы поиска цен": hasattr(system, 'find_and_display_prices'),
                "Методы отображения": hasattr(system, 'display_enhanced_results'),
                "Объяснение расчетов": hasattr(system, 'show_order_calculation_help')
            }
            
            passed_checks = sum(checks.values())
            if passed_checks >= 4:
                success_count += 1
                st.write("✅ Система полностью готова к работе")
            else:
                st.write(f"⚠️ Система частично готова ({passed_checks}/5 компонентов)")
            
            # Финальный результат
            progress_bar.empty()
            status_text.empty()
            
            if success_count >= 3:
                st.success(f"🎉 Обновление завершено успешно! ({success_count}/{total_steps} шагов)")
                
                # Показываем новые возможности
                show_new_capabilities()
                
                # Кнопка для перехода к анализу
                if st.button("🏪 Перейти к улучшенному анализу складов"):
                    st.session_state.goto_enhanced_warehouse = True
                    st.rerun()
                    
            else:
                st.warning(f"⚠️ Обновление частично применено ({success_count}/{total_steps} шагов)")
                st.info("💡 Некоторые функции могут быть недоступны")
        
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Критическая ошибка обновления: {e}")


def show_new_capabilities():
    """Показывает новые возможности системы"""
    
    st.subheader("🎯 Новые возможности:")
    
    capabilities = [
        "💰 **Автоматический поиск цен** в ADS данных и файлах магазинов",
        "📊 **MIN/MAX остатки** с персональными настройками складов",
        "🔍 **Объяснение расчета** колонки 'к заказу' с примерами",
        "📋 **Отображение ВСЕХ товаров** без ограничения в 100 единиц",
        "🎨 **Цветовая кодировка** статусов складов с иконками",
        "📈 **Детальная аналитика** с графиками и ТОП списками",
        "💾 **Улучшенный Excel экспорт** с ценами и полной аналитикой",
        "🔧 **Умное чтение файлов** остатков любой структуры"
    ]
    
    for capability in capabilities:
        st.write(capability)


def show_upgrade_status():
    """Показывает статус обновления"""
    
    if 'inventory_system' not in st.session_state:
        st.error("❌ Система не инициализирована")
        return
    
    system = st.session_state.inventory_system
    
    st.subheader("📋 Статус обновления:")
    
    checks = {
        "🔧 Базовое решение складов": hasattr(system, '_warehouse_complete_solution_applied'),
        "🎨 Улучшенный интерфейс": hasattr(system, '_enhanced_warehouse_interface_applied'),
        "💰 Поиск ценовых данных": hasattr(system, 'find_and_display_prices'),
        "📊 Улучшенное отображение": hasattr(system, 'display_enhanced_results'),
        "🔍 Объяснение расчетов": hasattr(system, 'show_order_calculation_help'),
        "📈 Ценовая аналитика": hasattr(system, 'show_price_integration_summary')
    }
    
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        st.write(f"{icon} {check}")
    
    ready_count = sum(checks.values())
    total_count = len(checks)
    
    if ready_count == total_count:
        st.success("🎉 Система полностью обновлена и готова к работе!")
        return True
    else:
        st.warning(f"⚠️ Готовность: {ready_count}/{total_count} компонентов")
        return False


def create_quick_upgrade_page(system):
    """Создает страницу быстрого обновления"""
    
    st.header("⚡ Быстрое обновление анализа складов")
    st.markdown("*Полное обновление системы одной кнопкой*")
    
    # Показываем текущий статус
    is_ready = show_upgrade_status()
    
    if not is_ready:
        st.markdown("---")
        apply_quick_warehouse_upgrade()
    else:
        st.markdown("---")
        st.subheader("🚀 Система готова!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏪 Обычный анализ складов"):
                st.session_state.goto_warehouse = True
                st.rerun()
        
        with col2:
            if st.button("🚀 Улучшенный анализ складов"):
                st.session_state.goto_enhanced_warehouse = True
                st.rerun()
        
        # Показываем быстрые действия
        st.markdown("---")
        st.subheader("⚡ Быстрые действия:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Найти цены"):
                if hasattr(system, 'find_and_display_prices'):
                    system.find_and_display_prices()
        
        with col2:
            if st.button("📊 Объяснить расчеты"):
                if hasattr(system, 'show_order_calculation_help'):
                    system.show_order_calculation_help()
        
        with col3:
            if st.button("📋 Последний анализ"):
                if hasattr(system, '_last_warehouse_analysis') and system._last_warehouse_analysis:
                    if hasattr(system, 'display_enhanced_results'):
                        st.subheader("📊 Результаты последнего анализа")
                        system.display_enhanced_results(system._last_warehouse_analysis)
                else:
                    st.info("Нет сохраненных результатов анализа")


# Функция для добавления в главное меню
def add_quick_upgrade_to_menu():
    """Добавляет быстрое обновление в главное меню"""
    
    # Проверяем нужно ли обновление
    if 'inventory_system' in st.session_state:
        system = st.session_state.inventory_system
        
        needs_upgrade = not (
            hasattr(system, '_warehouse_complete_solution_applied') and
            hasattr(system, '_enhanced_warehouse_interface_applied')
        )
        
        if needs_upgrade:
            st.sidebar.markdown("---")
            st.sidebar.subheader("⚡ Обновление складов")
            
            if st.sidebar.button("🚀 Обновить анализ складов"):
                st.session_state.goto_upgrade = True
                st.rerun()


if __name__ == "__main__":
    print("⚡ Быстрое обновление анализа складов загружено")
    print("Функции: автоматическое применение всех улучшений")