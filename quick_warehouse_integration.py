# quick_warehouse_integration.py
"""
🚀 БЫСТРАЯ ИНТЕГРАЦИЯ ИСПРАВЛЕНИЙ АНАЛИЗА СКЛАДОВ

Этот файл содержит готовые функции для замены проблемных частей кода
"""

import streamlit as st
import pandas as pd


def fix_warehouse_analysis_page_in_place(system):
    """
    БЫСТРОЕ ИСПРАВЛЕНИЕ - добавьте этот вызов в начало вашей warehouse_analysis_page
    
    ИСПОЛЬЗОВАНИЕ:
    def warehouse_analysis_page(system):
        from quick_warehouse_integration import fix_warehouse_analysis_page_in_place
        return fix_warehouse_analysis_page_in_place(system)
    """
    
    # Применяем основные исправления
    if not hasattr(system, '_warehouse_fix_applied'):
        try:
            from warehouse_complete_fix import apply_warehouse_complete_fix
            apply_warehouse_complete_fix(system)
            st.success("✅ Исправления анализа складов применены!")
        except ImportError:
            st.error("❌ Файл warehouse_complete_fix.py не найден. Создайте его из артефакта.")
            return False
    
    # Вызываем исправленную страницу
    try:
        from warehouse_complete_fix import create_fixed_warehouse_analysis_page
        fixed_page = create_fixed_warehouse_analysis_page()
        fixed_page(system)
        return True
    except ImportError:
        st.error("❌ Не удалось загрузить исправленные функции")
        return False


def emergency_warehouse_reader(uploaded_file):
    """
    ЭКСТРЕННЫЙ РИДЕР файлов остатков - используйте если основной не работает
    
    ИСПОЛЬЗОВАНИЕ:
    if uploaded_file:
        from quick_warehouse_integration import emergency_warehouse_reader
        remains_df = emergency_warehouse_reader(uploaded_file)
    """
    
    st.warning("🚨 Используется экстренный режим чтения файла")
    
    try:
        # Читаем файл как есть
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, header=None)
        else:
            df = pd.read_excel(uploaded_file, engine='xlrd', header=None)
        
        st.write(f"📊 Прочитано: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # Показываем первые строки для ручного анализа
        st.write("🔍 Первые 10 строк файла:")
        st.dataframe(df.head(10))
        
        # Ищем номенклатуру вручную
        nomenclature_row = st.number_input(
            "В какой строке находится 'Номенклатура'? (начиная с 1):",
            min_value=1, max_value=20, value=1
        ) - 1
        
        nomenclature_col = st.number_input(
            "В какой колонке находится 'Номенклатура'? (начиная с 1):",
            min_value=1, max_value=20, value=1
        ) - 1
        
        data_start_row = st.number_input(
            "С какой строки начинаются данные товаров? (начиная с 1):",
            min_value=1, max_value=50, value=4
        ) - 1
        
        if st.button("🔄 Обработать с указанными параметрами"):
            
            # Извлекаем названия складов из заголовков
            header_row = df.iloc[nomenclature_row]
            
            warehouses = []
            for i, cell in enumerate(header_row):
                if pd.notna(cell) and ('склад' in str(cell).lower() or 'магазин' in str(cell).lower()):
                    warehouses.append({
                        'index': i,
                        'name': str(cell),
                        'short_name': f"Склад_{len(warehouses)+1}"
                    })
            
            st.write(f"🏪 Найдено складов: {len(warehouses)}")
            for wh in warehouses:
                st.write(f"  - {wh['name']} (колонка {wh['index']+1})")
            
            # Читаем данные товаров
            items_data = []
            
            for i in range(data_start_row, len(df)):
                row = df.iloc[i]
                
                # Проверяем номенклатуру
                if nomenclature_col < len(row):
                    nomenclature = row.iloc[nomenclature_col]
                    if pd.notna(nomenclature) and str(nomenclature).strip():
                        
                        item_data = {'номенклатура': str(nomenclature).strip()}
                        
                        # Добавляем остатки по складам
                        total_stock = 0
                        for wh in warehouses:
                            if wh['index'] < len(row):
                                try:
                                    stock = float(row.iloc[wh['index']]) if pd.notna(row.iloc[wh['index']]) else 0
                                    total_stock += stock
                                except:
                                    stock = 0
                                item_data[f"{wh['short_name']}_остаток"] = stock
                        
                        item_data['итого_остаток'] = total_stock
                        items_data.append(item_data)
            
            if items_data:
                result_df = pd.DataFrame(items_data)
                st.success(f"✅ Обработано {len(result_df)} товаров")
                
                with st.expander("👀 Результат обработки"):
                    st.dataframe(result_df.head())
                
                return result_df
            else:
                st.error("❌ Не найдено товаров")
                return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Ошибка экстренного чтения: {str(e)}")
        return pd.DataFrame()


def add_missing_warehouse_methods(system):
    """
    ДОБАВЛЯЕТ ОТСУТСТВУЮЩИЕ МЕТОДЫ к системе
    
    ИСПОЛЬЗОВАНИЕ:
    # В начале вашей warehouse_analysis_page добавьте:
    from quick_warehouse_integration import add_missing_warehouse_methods
    add_missing_warehouse_methods(system)
    """
    
    st.info("🔧 Добавляем отсутствующие методы...")
    
    # Метод analyze_warehouse_stock_with_details
    if not hasattr(system, 'analyze_warehouse_stock_with_details'):
        
        def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
            """Простой анализ складов"""
            
            try:
                if remains_df.empty or 'номенклатура' not in remains_df.columns:
                    st.error("❌ Проблема с данными остатков")
                    return []
                
                if ads_data is None or ads_data.empty:
                    st.warning("⚠️ Нет ADS данных")
                    return []
                
                st.info(f"🔄 Анализируем {len(remains_df)} товаров...")
                
                results = []
                
                # Простой анализ каждого товара
                for _, item in remains_df.iterrows():
                    item_name = str(item['номенклатура']).strip()
                    
                    # Получаем ADS
                    ads_value = 0
                    if not ads_data.empty:
                        ads_match = ads_data[ads_data['номенклатура'] == item_name]
                        if not ads_match.empty:
                            ads_value = float(ads_match.iloc[0].get('ads', 0))
                    
                    # Общий остаток
                    total_stock = float(item.get('итого_остаток', 0))
                    
                    # Анализ по складам
                    warehouses = {}
                    warehouse_cols = [col for col in item.index if col.endswith('_остаток') and col != 'итого_остаток']
                    
                    for col in warehouse_cols:
                        warehouse_name = col.replace('_остаток', '')
                        current_stock = float(item.get(col, 0))
                        
                        # Простые расчеты
                        min_stock = ads_value * min_days if ads_value > 0 else 0
                        max_stock = ads_value * max_days if ads_value > 0 else 0
                        deficit = max(0, min_stock - current_stock)
                        
                        # Статус
                        if current_stock < min_stock and ads_value > 0:
                            status = 'critical' if deficit > ads_value * 5 else 'warning'
                        elif current_stock > max_stock:
                            status = 'excess'
                        else:
                            status = 'good'
                        
                        warehouses[warehouse_name] = {
                            'warehouse_name': warehouse_name,
                            'short_name': warehouse_name,
                            'current_stock': current_stock,
                            'min_stock': min_stock,
                            'max_stock': max_stock,
                            'order_quantity': deficit,
                            'status': status
                        }
                    
                    # Общий статус
                    critical_count = sum(1 for w in warehouses.values() if w['status'] == 'critical')
                    warning_count = sum(1 for w in warehouses.values() if w['status'] == 'warning')
                    
                    overall_status = 'critical' if critical_count > 0 else ('warning' if warning_count > 0 else 'good')
                    
                    results.append({
                        'номенклатура': item_name,
                        'total_stock': total_stock,
                        'ads': ads_value,
                        'overall_status': overall_status,
                        'warehouses': warehouses
                    })
                
                st.success(f"✅ Анализ завершен: {len(results)} товаров")
                return results
                
            except Exception as e:
                st.error(f"❌ Ошибка анализа: {str(e)}")
                return []
        
        system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
        st.success("✅ Метод analyze_warehouse_stock_with_details добавлен")
    
    # Метод get_warehouse_recommendations
    if not hasattr(system, 'get_warehouse_recommendations'):
        
        def get_warehouse_recommendations(analysis_results=None):
            """Простые рекомендации по складам"""
            
            if not analysis_results:
                return {}
            
            warehouse_stats = {}
            
            for item in analysis_results:
                for warehouse_key, wh_data in item.get('warehouses', {}).items():
                    if warehouse_key not in warehouse_stats:
                        warehouse_stats[warehouse_key] = {
                            'name': wh_data['short_name'],
                            'total_items': 0,
                            'critical_items': 0,
                            'warning_items': 0,
                            'total_order_quantity': 0
                        }
                    
                    stats = warehouse_stats[warehouse_key]
                    stats['total_items'] += 1
                    
                    if wh_data['status'] == 'critical':
                        stats['critical_items'] += 1
                    elif wh_data['status'] == 'warning':
                        stats['warning_items'] += 1
                    
                    stats['total_order_quantity'] += wh_data.get('order_quantity', 0)
            
            return warehouse_stats
        
        system.get_warehouse_recommendations = get_warehouse_recommendations
        st.success("✅ Метод get_warehouse_recommendations добавлен")


def show_simple_warehouse_results(analysis_results, recommendations=None):
    """
    ПРОСТОЕ ОТОБРАЖЕНИЕ результатов анализа
    
    ИСПОЛЬЗОВАНИЕ:
    if analysis_results:
        from quick_warehouse_integration import show_simple_warehouse_results
        show_simple_warehouse_results(analysis_results, recommendations)
    """
    
    st.subheader("📊 Результаты анализа складов")
    
    if not analysis_results:
        st.warning("⚠️ Нет результатов анализа")
        return
    
    # Общая статистика
    total_items = len(analysis_results)
    critical_items = sum(1 for item in analysis_results if item.get('overall_status') == 'critical')
    warning_items = sum(1 for item in analysis_results if item.get('overall_status') == 'warning')
    good_items = total_items - critical_items - warning_items
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего товаров", total_items)
    with col2:
        st.metric("🔴 Критичных", critical_items)
    with col3:
        st.metric("🟡 Требуют внимания", warning_items)
    with col4:
        st.metric("🟢 В норме", good_items)
    
    # Таблица товаров
    st.subheader("📋 Список товаров")
    
    # Фильтр по статусу
    status_filter = st.selectbox(
        "Показать:",
        ["Все товары", "Только критичные", "Только требующие внимания", "Только в норме"]
    )
    
    # Фильтруем результаты
    filtered_results = analysis_results
    if status_filter == "Только критичные":
        filtered_results = [item for item in analysis_results if item.get('overall_status') == 'critical']
    elif status_filter == "Только требующие внимания":
        filtered_results = [item for item in analysis_results if item.get('overall_status') == 'warning']
    elif status_filter == "Только в норме":
        filtered_results = [item for item in analysis_results if item.get('overall_status') == 'good']
    
    # Создаем таблицу
    table_data = []
    for item in filtered_results:
        # Эмодзи статуса
        status_emoji = {
            'critical': '🔴',
            'warning': '🟡',
            'good': '🟢'
        }.get(item.get('overall_status', 'good'), '⚪')
        
        row = {
            'Статус': status_emoji,
            'Номенклатура': item.get('номенклатура', '')[:50],
            'ADS': f"{item.get('ads', 0):.2f}",
            'Общий остаток': f"{item.get('total_stock', 0):.0f}"
        }
        
        # Добавляем данные по складам
        warehouses = item.get('warehouses', {})
        for warehouse_key, wh_data in warehouses.items():
            current_stock = wh_data.get('current_stock', 0)
            order_qty = wh_data.get('order_quantity', 0)
            
            if order_qty > 0:
                row[f"{warehouse_key}"] = f"{current_stock:.0f} ⚠️ +{order_qty:.0f}"
            else:
                row[f"{warehouse_key}"] = f"{current_stock:.0f}"
        
        table_data.append(row)
    
    if table_data:
        df_display = pd.DataFrame(table_data)
        st.dataframe(df_display, use_container_width=True)
        
        # Кнопка экспорта
        if st.button("📤 Экспорт в CSV"):
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="💾 Скачать CSV",
                data=csv,
                file_name=f"warehouse_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.info("📋 Нет данных для отображения с выбранным фильтром")
    
    # Рекомендации по складам
    if recommendations:
        st.subheader("🏪 Рекомендации по складам")
        
        rec_data = []
        for warehouse_key, data in recommendations.items():
            rec_data.append({
                'Склад': data.get('name', warehouse_key),
                'Всего товаров': data.get('total_items', 0),
                'Критичных': data.get('critical_items', 0),
                'Требуют внимания': data.get('warning_items', 0),
                'К заказу (шт)': f"{data.get('total_order_quantity', 0):.0f}"
            })
        
        if rec_data:
            st.dataframe(pd.DataFrame(rec_data), use_container_width=True)


def create_emergency_warehouse_page():
    """
    ЭКСТРЕННАЯ СТРАНИЦА анализа складов - используйте если основная не работает
    
    ИСПОЛЬЗОВАНИЕ:
    from quick_warehouse_integration import create_emergency_warehouse_page
    
    def warehouse_analysis_page(system):
        emergency_page = create_emergency_warehouse_page()
        emergency_page(system)
    """
    
    def emergency_warehouse_page(system):
        st.header("🚨 Экстренный анализ складов")
        st.warning("Используется упрощенная версия анализа")
        
        # Проверяем ADS
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            st.error("❌ Сначала рассчитайте ADS в разделе 'ADS расчет'")
            return
        
        st.success(f"✅ ADS данные найдены: {len(system.calculated_ads)} товаров")
        
        # Добавляем недостающие методы
        add_missing_warehouse_methods(system)
        
        # Параметры
        st.subheader("⚙️ Параметры")
        col1, col2 = st.columns(2)
        with col1:
            min_days = st.number_input("Минимум дней:", value=15, min_value=5, max_value=60)
        with col2:
            max_days = st.number_input("Максимум дней:", value=45, min_value=20, max_value=120)
        
        # Загрузка файла
        st.subheader("📂 Файл остатков")
        uploaded_file = st.file_uploader("Выберите файл остатков:", type=['xlsx', 'xls'])
        
        if uploaded_file:
            # Пробуем умное чтение
            try:
                from warehouse_complete_fix import WarehouseFileReader
                reader = WarehouseFileReader()
                reader.debug_mode = True
                remains_df = reader.read_remains_file_smart(uploaded_file)
                
                if not remains_df.empty:
                    st.success(f"✅ Файл прочитан: {len(remains_df)} товаров")
                else:
                    st.warning("⚠️ Попробуем экстренное чтение...")
                    remains_df = emergency_warehouse_reader(uploaded_file)
                    
            except ImportError:
                st.warning("⚠️ Основной ридер недоступен. Используем экстренный.")
                remains_df = emergency_warehouse_reader(uploaded_file)
            
            if not remains_df.empty and st.button("🚀 Запустить анализ"):
                
                with st.spinner("🔄 Выполняем анализ..."):
                    # Запускаем анализ
                    analysis_results = system.analyze_warehouse_stock_with_details(
                        remains_df, system.calculated_ads, None, min_days, max_days
                    )
                    
                    if analysis_results:
                        # Получаем рекомендации
                        recommendations = system.get_warehouse_recommendations(analysis_results)
                        
                        # Сохраняем в системе
                        system.warehouse_analysis_results = analysis_results
                        system.warehouse_recommendations = recommendations
                        
                        # Показываем результаты
                        show_simple_warehouse_results(analysis_results, recommendations)
                    else:
                        st.error("❌ Анализ не дал результатов")
        
        # Показываем сохраненные результаты
        if hasattr(system, 'warehouse_analysis_results') and system.warehouse_analysis_results:
            st.markdown("---")
            st.subheader("📊 Последние результаты")
            
            if st.button("🔄 Показать сохраненные результаты"):
                show_simple_warehouse_results(
                    system.warehouse_analysis_results,
                    getattr(system, 'warehouse_recommendations', {})
                )
    
    return emergency_warehouse_page


# Функция для автоматического исправления
def auto_fix_warehouse_system(system):
    """
    АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ всей системы анализа складов
    
    ИСПОЛЬЗОВАНИЕ:
    # В начале main() или init_system():
    from quick_warehouse_integration import auto_fix_warehouse_system
    auto_fix_warehouse_system(system)
    """
    
    if hasattr(system, '_warehouse_auto_fixed'):
        return True
    
    try:
        st.info("🔧 Применяем автоисправления анализа складов...")
        
        # Пробуем применить полные исправления
        try:
            from warehouse_complete_fix import apply_warehouse_complete_fix
            success = apply_warehouse_complete_fix(system)
            if success:
                st.success("✅ Полные исправления применены!")
                system._warehouse_auto_fixed = True
                return True
        except ImportError:
            st.warning("⚠️ Файл warehouse_complete_fix.py не найден")
        
        # Применяем базовые исправления
        add_missing_warehouse_methods(system)
        system._warehouse_auto_fixed = True
        st.success("✅ Базовые исправления применены!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка автоисправлений: {str(e)}")
        return False


# Пример использования
def integration_examples():
    """
    Примеры использования исправлений
    """
    
    return """
# 🚀 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ИСПРАВЛЕНИЙ

## 1. БЫСТРОЕ ИСПРАВЛЕНИЕ СУЩЕСТВУЮЩЕЙ ФУНКЦИИ

```python
def warehouse_analysis_page(system):
    # Добавьте эту строку в начало функции:
    from quick_warehouse_integration import fix_warehouse_analysis_page_in_place
    return fix_warehouse_analysis_page_in_place(system)
```

## 2. ЭКСТРЕННАЯ ЗАМЕНА ФУНКЦИИ

```python
def warehouse_analysis_page(system):
    # Если ничего не работает:
    from quick_warehouse_integration import create_emergency_warehouse_page
    emergency_page = create_emergency_warehouse_page()
    emergency_page(system)
```

## 3. АВТОИСПРАВЛЕНИЕ В MAIN

```python
def main():
    system = init_system()
    
    # Добавьте эту строку:
    from quick_warehouse_integration import auto_fix_warehouse_system
    auto_fix_warehouse_system(system)
    
    # ... остальной код ...
```

## 4. РУЧНОЕ ДОБАВЛЕНИЕ МЕТОДОВ

```python
def warehouse_analysis_page(system):
    # Если отсутствуют методы:
    from quick_warehouse_integration import add_missing_warehouse_methods
    add_missing_warehouse_methods(system)
    
    # ... ваш код анализа ...
```

## 5. ЭКСТРЕННОЕ ЧТЕНИЕ ФАЙЛОВ

```python
if uploaded_file:
    # Если стандартное чтение не работает:
    from quick_warehouse_integration import emergency_warehouse_reader
    remains_df = emergency_warehouse_reader(uploaded_file)
```

## ⚡ ПРИОРИТЕТ ИСПРАВЛЕНИЙ:

1. **Сначала попробуйте:** warehouse_complete_fix.py (полное решение)
2. **Если не работает:** fix_warehouse_analysis_page_in_place (быстрое)
3. **В крайнем случае:** create_emergency_warehouse_page (экстренное)

## 🎯 РЕЗУЛЬТАТ:

После применения любого из исправлений вы получите:
- ✅ Работающий анализ складов
- ✅ Правильное чтение файлов остатков
- ✅ Отображение результатов
- ✅ Базовый экспорт данных
"""


if __name__ == "__main__":
    print("🚀 Модуль быстрых исправлений анализа складов")
    print(integration_examples())  