# warehouse_analysis.py
# Дополнительный модуль для анализа остатков по складам
# Интегрируется с существующей Streamlit системой

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class WarehouseAnalyzer:
    """
    Класс для анализа остатков по складам с учетом структуры файла:
    - Заголовки складов в 7й строке (индекс 6)
    - Товары начинаются с 10й строки (индекс 9)
    """
    
    def __init__(self):
        # Конфигурация складов с правильными индексами колонок
        self.warehouse_config = {
            'Шымкент_Овощная_база': { 
                'col': 3, 
                'name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'short_name': 'Шымкент Овощная'
            },
            'Овощная_база_Магазин': { 
                'col': 4, 
                'name': '6 Склад фурнитуры "Овощная база" Магазин',
                'short_name': 'Овощная Магазин'
            },
            'АО_TRADE': { 
                'col': 6, 
                'name': 'АО Склад Фурнитура TRADE',
                'short_name': 'АО TRADE'
            },
            'База_Комплект': { 
                'col': 8, 
                'name': 'База Склад Фурнитура Комплект',
                'short_name': 'База Комплект'
            },
            'Барыс_TRADE': { 
                'col': 9, 
                'name': 'Барыс Склад Фурнитура TRADE',
                'short_name': 'Барыс TRADE'
            },
            'Казыбаева_TRADE': { 
                'col': 10, 
                'name': 'Казыбаева Склад Фурнитура TRADE',
                'short_name': 'Казыбаева TRADE'
            },
            'Магазин_фурнитуры': { 
                'col': 11, 
                'name': 'Магазин фурнитуры',
                'short_name': 'Магазин'
            },
            'Склад_1': { 
                'col': 12, 
                'name': 'склад фурнитура № 1',
                'short_name': 'Склад №1'
            },
            'Казыбаева_магазин': { 
                'col': 13, 
                'name': 'ТД Казыбаева ФУРНИТУРА магазин',
                'short_name': 'Казыбаева магазин'
            }
        }
        
        self.warehouse_analysis = None
        self.recommendations = None
    
    def parse_remains_file(self, file_data):
        """
        Парсит файл остатков с учетом правильной структуры:
        - 7я строка (индекс 6) - заголовки складов  
        - 10я строка (индекс 9) - начало данных товаров
        """
        try:
            # Читаем данные начиная с 9 строки (товары с 10й строки)
            remains_data = []
            
            for i in range(9, len(file_data)):  # начинаем с индекса 9 (10я строка Excel)
                row = file_data[i]
                if not row or len(row) == 0 or not row[0]:
                    continue
                    
                item_name = str(row[0]).strip()
                if not item_name:
                    continue
                
                item_data = {
                    'номенклатура': item_name,
                    'итого_остаток': row[14] if len(row) > 14 and row[14] else 0  # колонка "Итого"
                }
                
                # Добавляем остатки по складам
                for warehouse_key, config in self.warehouse_config.items():
                    col_idx = config['col']
                    quantity = row[col_idx] if len(row) > col_idx and row[col_idx] else 0
                    item_data[f'{warehouse_key}_остаток'] = quantity
                
                remains_data.append(item_data)
            
            return pd.DataFrame(remains_data)
            
        except Exception as e:
            st.error(f"Ошибка парсинга файла остатков: {e}")
            return None
    
    def analyze_warehouse_stock(self, remains_df, ads_data):
        """
        Анализирует остатки по складам с учетом ADS
        """
        if remains_df is None or remains_df.empty:
            return None
        
        analysis_results = []
        
        for _, item in remains_df.iterrows():
            item_name = item['номенклатура']
            
            # Получаем ADS для товара
            ads_value = 0
            if ads_data is not None and not ads_data.empty:
                ads_match = ads_data[ads_data['номенклатура'] == item_name]
                if not ads_match.empty:
                    ads_value = ads_match.iloc[0].get('ads', 0)
            
            # Анализ по каждому складу
            warehouse_analysis = {}
            total_stock = item['итого_остаток']
            
            for warehouse_key, config in self.warehouse_config.items():
                stock_col = f'{warehouse_key}_остаток'
                current_stock = item.get(stock_col, 0)
                
                # Расчет месяцев запаса
                months_of_stock = 0
                if ads_value > 0:
                    months_of_stock = current_stock / ads_value
                elif current_stock > 0:
                    months_of_stock = 999  # бесконечно если нет продаж
                
                # Определение статуса
                status = 'good'
                recommendation = ''
                order_quantity = 0
                
                if ads_value > 0:
                    if months_of_stock < 1:
                        status = 'critical'
                        order_quantity = max(0, ads_value * 3 - current_stock)  # 3 месяца запаса
                        recommendation = f'КРИТИЧНО! Остатков на {months_of_stock:.1f} мес. Заказать: {order_quantity:.0f}'
                    elif months_of_stock < 2:
                        status = 'warning'
                        order_quantity = max(0, ads_value * 3 - current_stock)
                        recommendation = f'Внимание! Остатков на {months_of_stock:.1f} мес. Заказать: {order_quantity:.0f}'
                    else:
                        recommendation = f'Достаточно на {months_of_stock:.1f} мес.'
                elif current_stock > 0:
                    status = 'no_sales'
                    recommendation = f'Нет продаж. Остаток: {current_stock}'
                else:
                    recommendation = 'Нет остатков и продаж'
                
                warehouse_analysis[warehouse_key] = {
                    'warehouse_name': config['name'],
                    'short_name': config['short_name'],
                    'current_stock': current_stock,
                    'months_of_stock': months_of_stock,
                    'status': status,
                    'recommendation': recommendation,
                    'order_quantity': order_quantity
                }
            
            # Общий анализ товара
            min_months = min([w['months_of_stock'] for w in warehouse_analysis.values() if w['months_of_stock'] < 999])
            if not min_months:
                min_months = 0
            
            overall_status = 'good'
            if ads_value > 0:
                if min_months < 1:
                    overall_status = 'critical'
                elif min_months < 2:
                    overall_status = 'warning'
            
            analysis_results.append({
                'номенклатура': item_name,
                'total_stock': total_stock,
                'ads': ads_value,
                'min_months_across_warehouses': min_months,
                'overall_status': overall_status,
                'warehouses': warehouse_analysis
            })
        
        self.warehouse_analysis = analysis_results
        return analysis_results
    
    def get_warehouse_recommendations(self):
        """Формирует рекомендации по каждому складу"""
        if not self.warehouse_analysis:
            return None
        
        warehouse_recommendations = {}
        
        # Инициализируем словари для каждого склада
        for warehouse_key, config in self.warehouse_config.items():
            warehouse_recommendations[warehouse_key] = {
                'name': config['name'],
                'short_name': config['short_name'],
                'critical_items': [],
                'warning_items': [],
                'total_order_value': 0
            }
        
        # Заполняем рекомендации
        for item in self.warehouse_analysis:
            for warehouse_key, warehouse_data in item['warehouses'].items():
                if warehouse_data['status'] == 'critical':
                    warehouse_recommendations[warehouse_key]['critical_items'].append({
                        'item': item['номенклатура'],
                        'current_stock': warehouse_data['current_stock'],
                        'months_left': warehouse_data['months_of_stock'],
                        'order_quantity': warehouse_data['order_quantity'],
                        'ads': item['ads']
                    })
                elif warehouse_data['status'] == 'warning':
                    warehouse_recommendations[warehouse_key]['warning_items'].append({
                        'item': item['номенклатура'],
                        'current_stock': warehouse_data['current_stock'],
                        'months_left': warehouse_data['months_of_stock'],
                        'order_quantity': warehouse_data['order_quantity'],
                        'ads': item['ads']
                    })
                
                warehouse_recommendations[warehouse_key]['total_order_value'] += warehouse_data['order_quantity']
        
        self.recommendations = warehouse_recommendations
        return warehouse_recommendations
    
    def create_warehouse_dashboard(self):
        """Создает дашборд для анализа складов"""
        if not self.warehouse_analysis or not self.recommendations:
            return None
        
        # Общая статистика
        total_items = len(self.warehouse_analysis)
        critical_items = sum(1 for item in self.warehouse_analysis if item['overall_status'] == 'critical')
        warning_items = sum(1 for item in self.warehouse_analysis if item['overall_status'] == 'warning')
        good_items = total_items - critical_items - warning_items
        
        # Статистика по складам
        warehouse_stats = []
        for warehouse_key, rec in self.recommendations.items():
            warehouse_stats.append({
                'Склад': rec['short_name'],
                'Критичных товаров': len(rec['critical_items']),
                'Товаров требующих внимания': len(rec['warning_items']),
                'Общий объем к заказу': rec['total_order_value']
            })
        
        warehouse_stats_df = pd.DataFrame(warehouse_stats)
        
        return {
            'summary': {
                'total_items': total_items,
                'critical_items': critical_items,
                'warning_items': warning_items,
                'good_items': good_items
            },
            'warehouse_stats': warehouse_stats_df
        }

# Функции для интеграции со Streamlit приложением

def add_warehouse_analysis_to_system(system):
    """Добавляет анализ складов к существующей системе"""
    system.warehouse_analyzer = WarehouseAnalyzer()
    system._warehouse_analysis_ready = True

def warehouse_analysis_page(system):
    """Страница анализа остатков по складам"""
    st.header("🏪 Анализ остатков по складам")
    
    # Проверка готовности системы
    if not hasattr(system, '_warehouse_analysis_ready'):
        add_warehouse_analysis_to_system(system)
    
    st.markdown("""
    **Анализ остатков по складам** позволяет:
    - 📊 Проанализировать остатки на каждом складе отдельно
    - ⚠️ Выявить критичные товары по складам
    - 📋 Получить рекомендации по заказу для каждого склада
    - 📈 Сравнить эффективность складов
    """)
    
    # Проверяем наличие ADS
    status = system.get_system_status()
    if not status['sales_analysis']['ads_calculated']:
        st.warning("⚠️ Для анализа складов необходимо сначала рассчитать ADS")
        if st.button("📊 Перейти к расчету ADS"):
            st.switch_page("ADS расчет")
        return
    
    # Загрузка файла остатков
    st.subheader("📂 Загрузка файла остатков")
    
    remains_file = st.file_uploader(
        "Выберите файл остатков (Excel)",
        type=['xlsx', 'xls'],
        help="Файл должен содержать заголовки складов в 7й строке и данные товаров начиная с 10й строки"
    )
    
    if remains_file is not None:
        with st.spinner("Обработка файла остатков..."):
            try:
                # Читаем Excel файл
                import openpyxl
                file_data = pd.read_excel(remains_file, header=None)
                file_data = file_data.values.tolist()
                
                # Парсим остатки с правильной структурой
                remains_df = system.warehouse_analyzer.parse_remains_file(file_data)
                
                if remains_df is not None and not remains_df.empty:
                    st.success(f"✅ Файл обработан! Найдено {len(remains_df)} товаров")
                    
                    # Показываем превью данных
                    with st.expander("👀 Превью данных остатков"):
                        st.dataframe(remains_df.head(10), use_container_width=True)
                    
                    # Кнопка анализа
                    if st.button("🔍 Проанализировать остатки по складам"):
                        with st.spinner("Анализ остатков по складам..."):
                            # Получаем ADS данные
                            ads_data = system.calculated_ads if hasattr(system, 'calculated_ads') else None
                            
                            # Выполняем анализ
                            analysis = system.warehouse_analyzer.analyze_warehouse_stock(remains_df, ads_data)
                            
                            if analysis:
                                recommendations = system.warehouse_analyzer.get_warehouse_recommendations()
                                dashboard_data = system.warehouse_analyzer.create_warehouse_dashboard()
                                
                                st.success("✅ Анализ складов завершен!")
                                
                                # Отображаем результаты
                                display_warehouse_analysis_results(dashboard_data, recommendations, analysis)
                            else:
                                st.error("❌ Ошибка анализа остатков")
                else:
                    st.error("❌ Не удалось обработать файл остатков")
                    
            except Exception as e:
                st.error(f"❌ Ошибка обработки файла: {e}")

def display_warehouse_analysis_results(dashboard_data, recommendations, analysis):
    """Отображает результаты анализа складов"""
    
    # Общая статистика
    st.subheader("📊 Общая статистика")
    
    summary = dashboard_data['summary']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего товаров", summary['total_items'])
    with col2:
        st.metric("Критичные", summary['critical_items'], delta=f"-{summary['critical_items']}")
    with col3:
        st.metric("Требуют внимания", summary['warning_items'], delta=f"-{summary['warning_items']}")
    with col4:
        st.metric("В норме", summary['good_items'], delta=f"+{summary['good_items']}")
    
    # Статистика по складам
    st.subheader("🏪 Статистика по складам")
    
    warehouse_stats = dashboard_data['warehouse_stats']
    st.dataframe(warehouse_stats, use_container_width=True)
    
    # Визуализация
    st.subheader("📈 Визуализация")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # График критичных товаров по складам
        fig_critical = px.bar(
            warehouse_stats,
            x='Склад',
            y='Критичных товаров',
            title='Критичные товары по складам',
            color='Критичных товаров',
            color_continuous_scale='Reds'
        )
        fig_critical.update_layout(showlegend=False)
        st.plotly_chart(fig_critical, use_container_width=True)
    
    with col2:
        # График объемов к заказу
        fig_order = px.bar(
            warehouse_stats,
            x='Склад',
            y='Общий объем к заказу',
            title='Объем к заказу по складам',
            color='Общий объем к заказу',
            color_continuous_scale='Blues'
        )
        fig_order.update_layout(showlegend=False)
        st.plotly_chart(fig_order, use_container_width=True)
    
    # Детальные рекомендации по складам
    st.subheader("📋 Рекомендации по складам")
    
    for warehouse_key, rec in recommendations.items():
        if rec['critical_items'] or rec['warning_items']:
            with st.expander(f"🏪 {rec['short_name']} - {len(rec['critical_items'] + rec['warning_items'])} товаров к заказу"):
                
                if rec['critical_items']:
                    st.markdown("**🚨 Критичные товары:**")
                    critical_df = pd.DataFrame(rec['critical_items'])
                    critical_df['Приоритет'] = 'Критично'
                    st.dataframe(critical_df, use_container_width=True)
                
                if rec['warning_items']:
                    st.markdown("**⚠️ Требуют внимания:**")
                    warning_df = pd.DataFrame(rec['warning_items'])
                    warning_df['Приоритет'] = 'Внимание'
                    st.dataframe(warning_df, use_container_width=True)
                
                st.metric(
                    "Общий объем к заказу с этого склада",
                    f"{rec['total_order_value']:,.0f}",
                    help="Рекомендуемое количество к заказу по всем товарам"
                )
        else:
            st.success(f"✅ {rec['short_name']} - все товары в достаточном количестве")
    
    # Экспорт результатов
    st.subheader("📤 Экспорт результатов")
    
    if st.button("📊 Экспортировать анализ складов"):
        export_warehouse_analysis(recommendations, analysis, warehouse_stats)

def export_warehouse_analysis(recommendations, analysis, warehouse_stats):
    """Экспортирует результаты анализа складов в Excel"""
    try:
        from io import BytesIO
        import xlsxwriter
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Лист со статистикой по складам
            warehouse_stats.to_excel(writer, sheet_name='Статистика складов', index=False)
            
            # Листы с рекомендациями по каждому складу
            for warehouse_key, rec in recommendations.items():
                if rec['critical_items'] or rec['warning_items']:
                    all_items = []
                    
                    for item in rec['critical_items']:
                        item['Приоритет'] = 'Критично'
                        all_items.append(item)
                    
                    for item in rec['warning_items']:
                        item['Приоритет'] = 'Внимание'
                        all_items.append(item)
                    
                    if all_items:
                        items_df = pd.DataFrame(all_items)
                        sheet_name = rec['short_name'][:31]  # Ограничение Excel
                        items_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Общий лист с анализом всех товаров
            all_analysis = []
            for item in analysis:
                for warehouse_key, warehouse_data in item['warehouses'].items():
                    all_analysis.append({
                        'Товар': item['номенклатура'],
                        'Склад': warehouse_data['short_name'],
                        'Остаток': warehouse_data['current_stock'],
                        'Месяцев запаса': warehouse_data['months_of_stock'],
                        'Статус': warehouse_data['status'],
                        'К заказу': warehouse_data['order_quantity'],
                        'ADS': item['ads']
                    })
            
            if all_analysis:
                analysis_df = pd.DataFrame(all_analysis)
                analysis_df.to_excel(writer, sheet_name='Детальный анализ', index=False)
        
        output.seek(0)
        
        st.download_button(
            label="📥 Скачать Excel файл",
            data=output.getvalue(),
            file_name=f"анализ_складов_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Файл готов к скачиванию!")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта: {e}")

# Функция для интеграции в основное приложение
def integrate_warehouse_analysis():
    """
    Инструкция для интеграции анализа складов в основное приложение:
    
    1. В streamlit_modular_app.py добавить в навигацию:
       "🏪 Анализ складов"
    
    2. В обработку страниц добавить:
       elif page == "🏪 Анализ складов":
           warehouse_analysis_page(system)
    
    3. В функцию init_system() добавить:
       add_warehouse_analysis_to_system(st.session_state.inventory_system)
    """
    pass