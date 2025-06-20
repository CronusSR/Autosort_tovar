# warehouse_analysis.py
# Дополнительный модуль для анализа остатков по складам
# Интегрируется с существующей Streamlit системой

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openpyxl
import traceback
from io import BytesIO


class WarehouseAnalyzer:
    """
    Класс для анализа остатков по складам с учетом структуры файла:
    - Заголовки складов в 7й строке (индекс 6)
    - Товары начинают идти с 10й строки (индекс 9)
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
            print(f"📊 Начало парсинга файла остатков. Всего строк: {len(file_data)}")
            
            # Проверяем что файл достаточно большой
            if len(file_data) < 10:
                raise ValueError("Файл слишком мал. Должно быть минимум 10 строк.")
            
            # Проверяем заголовки складов в 7й строке (индекс 6)
            if len(file_data) > 6:
                header_row = file_data[6]  # 7я строка
                print(f"📋 7я строка (заголовки): {header_row[:5]}...")
            
            # Читаем данные начиная с 9 строки (товары с 10й строки)
            remains_data = []
            processed_items = 0
            
            for i in range(9, len(file_data)):  # начинаем с индекса 9 (10я строка Excel)
                row = file_data[i]
                
                # Проверяем что строка не пустая
                if not row or len(row) == 0:
                    continue
                    
                # Проверяем что первая ячейка (номенклатура) не пустая
                if not row[0] or pd.isna(row[0]):
                    continue
                    
                item_name = str(row[0]).strip()
                if not item_name or item_name.lower() in ['', 'nan', 'none']:
                    continue
                
                # Безопасно получаем итоговый остаток (колонка 14 = индекс 14)
                try:
                    total_stock = row[14] if len(row) > 14 and row[14] is not None else 0
                    total_stock = float(total_stock) if pd.notna(total_stock) else 0
                except (ValueError, TypeError, IndexError):
                    total_stock = 0
                
                item_data = {
                    'номенклатура': item_name,
                    'итого_остаток': total_stock
                }
                
                # Добавляем остатки по складам с безопасной обработкой
                for warehouse_key, config in self.warehouse_config.items():
                    col_idx = config['col']
                    try:
                        if len(row) > col_idx and row[col_idx] is not None:
                            quantity = float(row[col_idx]) if pd.notna(row[col_idx]) else 0
                        else:
                            quantity = 0
                    except (ValueError, TypeError, IndexError):
                        quantity = 0
                    
                    item_data[f'{warehouse_key}_остаток'] = quantity
                
                remains_data.append(item_data)
                processed_items += 1
            
            print(f"✅ Обработано товаров: {processed_items}")
            
            if not remains_data:
                raise ValueError("Не найдено ни одного товара с данными. Проверьте структуру файла.")
            
            result_df = pd.DataFrame(remains_data)
            print(f"📊 Создан DataFrame: {len(result_df)} строк, {len(result_df.columns)} колонок")
            
            return result_df
            
        except Exception as e:
            print(f"❌ Ошибка парсинга файла остатков: {e}")
            st.error(f"Ошибка парсинга файла остатков: {e}")
            return None

    def analyze_warehouse_stock(self, remains_df, ads_data, min_days=10, max_days=50):
        """
        Анализирует остатки по складам с учетом ADS и расчетом MIN/MAX запасов
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
            
            # Рассчитываем MIN и MAX запасы
            min_stock = ads_value * min_days if ads_value > 0 else 0
            max_stock = ads_value * max_days if ads_value > 0 else 0
            
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
                
                # Сравнение с MIN/MAX запасами
                min_deficit = max(0, min_stock - current_stock)
                max_surplus = max(0, current_stock - max_stock)
                
                # Определение статуса с учетом MIN/MAX
                status = 'good'
                recommendation = ''
                order_quantity = 0
                
                if ads_value > 0:
                    if current_stock < min_stock:
                        if current_stock < min_stock * 0.5:  # меньше 50% от MIN
                            status = 'critical'
                            order_quantity = max_stock - current_stock  # заказываем до MAX
                            recommendation = f'КРИТИЧНО! Остаток {current_stock:.0f} < MIN {min_stock:.0f}. Заказать до MAX: {order_quantity:.0f}'
                        else:
                            status = 'warning'
                            order_quantity = min_stock - current_stock  # заказываем до MIN
                            recommendation = f'Ниже MIN! Остаток {current_stock:.0f} < MIN {min_stock:.0f}. Заказать: {order_quantity:.0f}'
                    elif current_stock > max_stock:
                        status = 'excess'
                        recommendation = f'Избыток! Остаток {current_stock:.0f} > MAX {max_stock:.0f} (избыток: {max_surplus:.0f})'
                    else:
                        recommendation = f'В норме: {current_stock:.0f} (MIN: {min_stock:.0f}, MAX: {max_stock:.0f})'
                elif current_stock > 0:
                    status = 'no_sales'
                    recommendation = f'Нет продаж. Остаток: {current_stock:.0f}'
                else:
                    recommendation = 'Нет остатков и продаж'
                
                warehouse_analysis[warehouse_key] = {
                    'warehouse_name': config['name'],
                    'short_name': config['short_name'],
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'min_deficit': min_deficit,
                    'max_surplus': max_surplus,
                    'months_of_stock': months_of_stock,
                    'status': status,
                    'recommendation': recommendation,
                    'order_quantity': order_quantity
                }
            
            # Общий анализ товара - исправление для ошибки min() empty
            months_list = [w['months_of_stock'] for w in warehouse_analysis.values() if w['months_of_stock'] < 999]
            if months_list:
                min_months = min(months_list)
            else:
                min_months = 0
            
            overall_status = 'good'
            if ads_value > 0:
                critical_warehouses = sum(1 for w in warehouse_analysis.values() if w['status'] == 'critical')
                warning_warehouses = sum(1 for w in warehouse_analysis.values() if w['status'] == 'warning')
                
                if critical_warehouses > 0:
                    overall_status = 'critical'
                elif warning_warehouses > 0:
                    overall_status = 'warning'
            
            analysis_results.append({
                'номенклатура': item_name,
                'total_stock': total_stock,
                'ads': ads_value,
                'min_stock_calculated': min_stock,
                'max_stock_calculated': max_stock,
                'min_months_across_warehouses': min_months,
                'overall_status': overall_status,
                'warehouses': warehouse_analysis,
                'parameters': {
                    'min_days': min_days,
                    'max_days': max_days
                }
            })
        
        self.warehouse_analysis = analysis_results
        return analysis_results
    
    def get_warehouse_recommendations(self):
        """Формирует рекомендации по каждому складу с учетом MIN/MAX"""
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
                'excess_items': [],
                'total_order_value': 0,
                'total_excess_value': 0
            }
        
        # Заполняем рекомендации
        for item in self.warehouse_analysis:
            for warehouse_key, warehouse_data in item['warehouses'].items():
                if warehouse_data['status'] == 'critical':
                    warehouse_recommendations[warehouse_key]['critical_items'].append({
                        'item': item['номенклатура'],
                        'current_stock': warehouse_data['current_stock'],
                        'min_stock': warehouse_data['min_stock'],
                        'max_stock': warehouse_data['max_stock'],
                        'min_deficit': warehouse_data['min_deficit'],
                        'months_left': warehouse_data['months_of_stock'],
                        'order_quantity': warehouse_data['order_quantity'],
                        'ads': item['ads']
                    })
                elif warehouse_data['status'] == 'warning':
                    warehouse_recommendations[warehouse_key]['warning_items'].append({
                        'item': item['номенклатура'],
                        'current_stock': warehouse_data['current_stock'],
                        'min_stock': warehouse_data['min_stock'],
                        'max_stock': warehouse_data['max_stock'],
                        'min_deficit': warehouse_data['min_deficit'],
                        'months_left': warehouse_data['months_of_stock'],
                        'order_quantity': warehouse_data['order_quantity'],
                        'ads': item['ads']
                    })
                elif warehouse_data['status'] == 'excess':
                    warehouse_recommendations[warehouse_key]['excess_items'].append({
                        'item': item['номенклатура'],
                        'current_stock': warehouse_data['current_stock'],
                        'min_stock': warehouse_data['min_stock'],
                        'max_stock': warehouse_data['max_stock'],
                        'max_surplus': warehouse_data['max_surplus'],
                        'ads': item['ads']
                    })
                
                warehouse_recommendations[warehouse_key]['total_order_value'] += warehouse_data['order_quantity']
                warehouse_recommendations[warehouse_key]['total_excess_value'] += warehouse_data.get('max_surplus', 0)
        
        self.recommendations = warehouse_recommendations
        return warehouse_recommendations

    def create_warehouse_dashboard(self):
        """Создает дашборд для анализа складов с MIN/MAX"""
        if not self.warehouse_analysis or not self.recommendations:
            return None
        
        # Общая статистика
        total_items = len(self.warehouse_analysis)
        critical_items = sum(1 for item in self.warehouse_analysis if item['overall_status'] == 'critical')
        warning_items = sum(1 for item in self.warehouse_analysis if item['overall_status'] == 'warning')
        excess_items = sum(1 for item in self.warehouse_analysis if 
                          any(w['status'] == 'excess' for w in item['warehouses'].values()))
        good_items = total_items - critical_items - warning_items - excess_items
        
        # Статистика по складам
        warehouse_stats = []
        for warehouse_key, rec in self.recommendations.items():
            warehouse_stats.append({
                'Склад': rec['short_name'],
                'Критичных товаров': len(rec['critical_items']),
                'Товаров требующих внимания': len(rec['warning_items']),
                'Товаров с избытком': len(rec['excess_items']),
                'Общий объем к заказу': rec['total_order_value'],
                'Общий избыток': rec['total_excess_value']
            })
        
        warehouse_stats_df = pd.DataFrame(warehouse_stats)
        
        return {
            'summary': {
                'total_items': total_items,
                'critical_items': critical_items,
                'warning_items': warning_items,
                'excess_items': excess_items,
                'good_items': good_items
            },
            'warehouse_stats': warehouse_stats_df
        }
    def analyze_warehouse_with_store_integration(self, remains_df, store_ads_by_city, min_days=10, max_days=50):
        """
        Анализ складов с интеграцией ADS данных из магазинов по городам
        """
        if remains_df is None or remains_df.empty:
            return None
        
        print(f"🔄 Начало анализа складов с интеграцией магазинов")
        print(f"📊 Товаров в остатках: {len(remains_df)}")
        print(f"🌍 Городов с ADS данными: {len(store_ads_by_city) if store_ads_by_city else 0}")
        
        # Получаем объединенные ADS по городам
        unified_ads = create_unified_ads_by_city(store_ads_by_city) if store_ads_by_city else {}
        
        # Маппинг складов по городам
        warehouse_city_mapping = get_warehouse_city_mapping()
        
        analysis_results = []
        processed_items = 0
        
        for _, item in remains_df.iterrows():
            item_name = item['номенклатура']
            
            item_analysis = {
                'номенклатура': item_name,
                'итого_остаток': item['итого_остаток'],
                'warehouses': {}
            }
            
            # Анализируем каждый склад
            for warehouse_key, config in self.warehouse_config.items():
                stock_col = f'{warehouse_key}_остаток'
                current_stock = item.get(stock_col, 0)
                
                # Определяем к какому городу относится склад
                warehouse_city = None
                for city, warehouses in warehouse_city_mapping.items():
                    if warehouse_key in warehouses:
                        warehouse_city = city
                        break
                
                # Получаем ADS для товара из соответствующего города
                ads_value = 0
                ads_source = "нет данных"
                
                if warehouse_city and warehouse_city in unified_ads:
                    city_ads = unified_ads[warehouse_city]
                    ads_match = city_ads[city_ads['номенклатура'] == item_name]
                    if not ads_match.empty:
                        ads_value = ads_match.iloc[0].get('ads', 0)
                        ads_source = f"город {warehouse_city}"
                
                # Если нет ADS для города, пробуем общие данные
                if ads_value == 0 and 'общие' in unified_ads:
                    general_ads = unified_ads['общие']
                    ads_match = general_ads[general_ads['номенклатура'] == item_name]
                    if not ads_match.empty:
                        ads_value = ads_match.iloc[0].get('ads', 0)
                        ads_source = "общие данные"
                
                # Если все еще нет ADS, пробуем все города
                if ads_value == 0:
                    for city, city_ads in unified_ads.items():
                        ads_match = city_ads[city_ads['номенклатура'] == item_name]
                        if not ads_match.empty:
                            ads_value = ads_match.iloc[0].get('ads', 0)
                            ads_source = f"другой город {city}"
                            break
                
                # Рассчитываем MIN и MAX запасы
                min_stock = ads_value * min_days if ads_value > 0 else 0
                max_stock = ads_value * max_days if ads_value > 0 else 0
                
                # Анализ остатков
                months_of_stock = 0
                if ads_value > 0:
                    months_of_stock = current_stock / (ads_value * 30)  # Месяцы запаса
                elif current_stock > 0:
                    months_of_stock = 999
                
                # Определение статуса
                status = 'good'
                recommendation = ''
                order_quantity = 0
                
                if ads_value > 0:
                    if current_stock < min_stock:
                        if current_stock < min_stock * 0.5:
                            status = 'critical'
                            order_quantity = max_stock - current_stock
                            recommendation = f'КРИТИЧНО! Заказать {order_quantity:.0f} единиц (ADS: {ads_source})'
                        else:
                            status = 'warning'
                            order_quantity = min_stock - current_stock
                            recommendation = f'Заказать {order_quantity:.0f} до MIN (ADS: {ads_source})'
                    elif current_stock > max_stock:
                        status = 'excess'
                        excess_amount = current_stock - max_stock
                        recommendation = f'Избыток {excess_amount:.0f} единиц (ADS: {ads_source})'
                    else:
                        status = 'good'
                        recommendation = f'В норме (ADS: {ads_source})'
                else:
                    if current_stock > 0:
                        status = 'no_ads'
                        recommendation = 'Есть остатки, но нет данных продаж'
                    else:
                        status = 'no_ads'
                        recommendation = 'Нет остатков и данных продаж'
                
                item_analysis['warehouses'][warehouse_key] = {
                    'city': warehouse_city or 'общий',
                    'current_stock': current_stock,
                    'ads': ads_value,
                    'ads_source': ads_source,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'months_of_stock': months_of_stock,
                    'status': status,
                    'recommendation': recommendation,
                    'order_quantity': order_quantity,
                    'short_name': config['short_name']
                }
            
            analysis_results.append(item_analysis)
            processed_items += 1
            
            if processed_items % 100 == 0:
                print(f"📊 Обработано товаров: {processed_items}")
        
        print(f"✅ Анализ завершен. Обработано товаров: {processed_items}")
        return analysis_results



def diagnose_warehouse_system(system):
    """Диагностирует состояние системы анализа складов"""
    st.subheader("🔍 Диагностика системы")
    
    if st.button("🔍 Проверить состояние системы"):
        with st.expander("📊 Результаты диагностики"):
            
            # Проверяем основные компоненты
            checks = {
                'Система инициализирована': hasattr(st.session_state, 'inventory_system'),
                'Анализатор складов подключен': hasattr(system, 'warehouse_analyzer') if system else False,
                'ADS данные доступны': hasattr(system, 'calculated_ads') and system.calculated_ads is not None if system else False,
                'Система готова к анализу': hasattr(system, '_warehouse_analysis_ready') if system else False
            }
            
            # Отображаем основные проверки
            for check, status in checks.items():
                status_icon = "✅" if status else "❌"
                st.write(f"{status_icon} {check}")
            
            if system and hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
                ads_data = system.calculated_ads
                
                # Проверяем доступность цен
                price_columns = ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']
                available_price_cols = [col for col in price_columns if col in ads_data.columns]
                
                st.write(f"📊 **ADS данные**: {len(ads_data)} товаров")
                st.write(f"💰 **Доступные ценовые колонки**: {', '.join(available_price_cols) if available_price_cols else 'Нет'}")
                
                if available_price_cols:
                    for col in available_price_cols:
                        items_with_price = (ads_data[col] > 0).sum()
                        percentage = (items_with_price / len(ads_data)) * 100
                        st.write(f"   - {col}: {items_with_price} товаров ({percentage:.1f}%)")
                
                # Показываем колонки ADS данных
                with st.expander("📋 Структура ADS данных"):
                    st.write("**Доступные колонки:**")
                    for i, col in enumerate(ads_data.columns):
                        st.write(f"{i+1}. {col}")
            
            # Рекомендации
            st.write("💡 **Рекомендации:**")
            
            if not checks['Система инициализирована']:
                st.write("- Перезапустите приложение")
            elif not checks['Анализатор складов подключен']:
                st.write("- Система анализа складов не подключена")
            elif not checks['ADS данные доступны']:
                st.write("- Загрузите файл продаж и рассчитайте ADS")
            elif not available_price_cols if system and hasattr(system, 'calculated_ads') else True:
                st.write("- Убедитесь что файл продаж содержит ценовую информацию")
            else:
                st.write("- Система готова к анализу складов! 🚀")


def add_warehouse_analysis_to_system(system):
    """Добавляет анализ складов к существующей системе"""
    if not hasattr(system, 'warehouse_analyzer'):
        system.warehouse_analyzer = WarehouseAnalyzer()
        system._warehouse_analysis_ready = True
        
        # Добавляем диагностические методы
        system.diagnose_warehouse_system = lambda: diagnose_warehouse_system(system)
        
        print("✅ Анализ складов успешно подключен к системе")

# ⚠️ ВАЖНО: Эта функция должна быть НА ЭТОМ УРОВНЕ, не внутри предыдущей!
def warehouse_analysis_page(system):
    """
    ПОЛНАЯ страница анализа остатков по складам с детальным анализом каждого склада
    """
    
    st.header("📦 Детальный анализ остатков по складам")
    
    # 🚨 ИСПРАВЛЕНИЕ ARROW ОШИБКИ
    if 'safe_dataframe_applied' not in st.session_state:
        st.session_state.safe_dataframe_applied = True
        
        original_dataframe = st.dataframe
        
        def safe_dataframe(data, **kwargs):
            if isinstance(data, pd.DataFrame) and not data.empty:
                data_copy = data.copy()
                for col in data_copy.columns:
                    if data_copy[col].dtype == 'object':
                        data_copy[col] = data_copy[col].astype(str)
                        data_copy[col] = data_copy[col].replace(['∞', 'inf', 'nan'], ['999+', '999+', ''])
                
                try:
                    return original_dataframe(data_copy, **kwargs)
                except:
                    st.markdown(data_copy.to_html(escape=False), unsafe_allow_html=True)
            else:
                return original_dataframe(data, **kwargs)
        
        st.dataframe = safe_dataframe
    
    # 🔧 ВОССТАНОВЛЕНИЕ ДЕТАЛЬНОГО АНАЛИЗАТОРА СКЛАДОВ
    try:
        from restore_detailed_warehouse_analysis import (
            restore_original_warehouse_analysis_to_system, 
            display_detailed_warehouse_analysis
        )
        
        # Инициализируем детальный анализатор если его нет
        if not hasattr(system, 'warehouse_analyzer') or not hasattr(system.warehouse_analyzer, 'warehouse_config'):
            restore_original_warehouse_analysis_to_system(system)
            st.success("✅ Детальный анализатор складов инициализирован")
            
    except ImportError:
        st.error("❌ Файл restore_detailed_warehouse_analysis.py не найден. Добавьте его в проект.")
        return
    
    # 🚨 ФУНКЦИЯ ПОИСКА ADS ДАННЫХ
    def simple_integrate_ads(system):
        """Простая функция поиска ADS данных"""
        result = {}
        
        # Ищем в multiple_files_data
        if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
            if 'processed_results' in system.multiple_files_data:
                processed = system.multiple_files_data['processed_results']
                
                for filename, data in processed.items():
                    ads_df = None
                    
                    if isinstance(data, dict):
                        for key in ['calculated_ads', 'ads_data', 'data']:
                            if key in data and hasattr(data[key], 'columns'):
                                if 'ads' in data[key].columns:
                                    ads_df = data[key]
                                    break
                    elif hasattr(data, 'columns') and 'ads' in data.columns:
                        ads_df = data
                    
                    if ads_df is not None:
                        # Определяем город
                        city = 'общие'
                        filename_lower = filename.lower()
                        
                        if 'шымкент' in filename_lower:
                            city = 'шымкент'
                        elif 'астана' in filename_lower:
                            city = 'астана'
                        elif any(word in filename_lower for word in ['алматы', 'барыс', 'казыбаева']):
                            city = 'алматы'
                        
                        if city not in result:
                            result[city] = []
                        
                        result[city].append({
                            'store_type': 'магазин',
                            'branch_name': filename.replace('.xlsx', ''),
                            'ads_data': ads_df,
                            'filename': filename
                        })
        
        # Добавляем calculated_ads
        if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
            if not system.calculated_ads.empty:
                if 'объединенные' not in result:
                    result['объединенные'] = []
                
                result['объединенные'].append({
                    'store_type': 'общий',
                    'branch_name': 'calculated_ads',
                    'ads_data': system.calculated_ads,
                    'filename': 'calculated_ads'
                })
        
        return result if result else None
    
    # Получаем ADS данные
    store_ads_by_city = simple_integrate_ads(system)
    
    if store_ads_by_city:
        st.success(f"✅ Найдены ADS данные по {len(store_ads_by_city)} источникам")
        
        with st.expander("🌍 Найденные ADS данные"):
            for city, stores in store_ads_by_city.items():
                st.write(f"**{city.title()}:** {len(stores)} источников")
                for store in stores:
                    items_count = len(store['ads_data']) if hasattr(store['ads_data'], '__len__') else 0
                    total_ads = store['ads_data']['ads'].sum() if 'ads' in store['ads_data'].columns else 0
                    st.write(f"  - {store['branch_name']} - {items_count} товаров, ADS: {total_ads:.2f}")
    else:
        st.warning("⚠️ Нет данных ADS по магазинам. Загрузите файлы продаж в разделе 'ADS анализ по магазинам'")
        return
    
    # Настройки параметров анализа
    st.subheader("⚙️ Параметры детального анализа")
    
    col1, col2 = st.columns(2)
    with col1:
        min_days = st.number_input("Минимальные дни запаса:", min_value=5, max_value=60, value=10)
    with col2:
        max_days = st.number_input("Максимальные дни запаса:", min_value=20, max_value=120, value=50)
    
    # Загрузка файла остатков
    st.subheader("📂 Загрузка данных остатков")
    
    uploaded_file = st.file_uploader(
        "Выберите файл остатков:",
        type=['xlsx', 'xls'],
        help="Файл должен содержать колонки с остатками по каждому складу"
    )
    
    if uploaded_file:
        try:
            # Читаем файл
            if uploaded_file.name.endswith('.xlsx'):
                remains_df = pd.read_excel(uploaded_file)
            else:
                remains_df = pd.read_excel(uploaded_file, engine='xlrd')
            
            st.success(f"✅ Файл загружен: {len(remains_df)} товаров")
            
            # Показываем превью данных
            with st.expander("👀 Превью данных остатков"):
                st.dataframe(remains_df.head(10), use_container_width=True)
            
            # Показываем найденные склады
            warehouse_cols = [col for col in remains_df.columns if 'остаток' in col.lower()]
            
            with st.expander("🏪 Найденные склады в файле"):
                st.write(f"**Найдено складов: {len(warehouse_cols)}**")
                for col in warehouse_cols:
                    warehouse_name = col.replace('_остаток', '').replace(' остаток', '')
                    total_stock = remains_df[col].sum()
                    items_with_stock = (remains_df[col] > 0).sum()
                    st.write(f"- **{warehouse_name}**: {total_stock:,.0f} единиц на {items_with_stock} товарах")
            
            # 🚨 ИСПРАВЛЕНИЕ ОТСУТСТВУЮЩЕГО МЕТОДА
            if not hasattr(system, 'analyze_warehouse_stock_with_details'):
                
                def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city, min_days=10, max_days=50):
                    """Анализ складов с полными деталями"""
                    
                    try:
                        # Если нет анализатора, создаем его
                        if not hasattr(system, 'warehouse_analyzer'):
                            from restore_detailed_warehouse_analysis import DetailedWarehouseAnalyzer
                            system.warehouse_analyzer = DetailedWarehouseAnalyzer()
                        
                        # Запускаем детальный анализ
                        analysis = system.warehouse_analyzer.analyze_warehouse_stock_detailed(
                            remains_df, ads_data, store_ads_by_city, min_days, max_days
                        )
                        
                        if analysis:
                            recommendations = system.warehouse_analyzer.get_warehouse_recommendations()
                            return analysis, recommendations
                        
                        return None, None
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка анализа: {str(e)}")
                        return None, None
                
                # Добавляем метод к системе
                system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
                st.info("🔧 Метод анализа добавлен к системе")
            
            # Кнопка детального анализа
            if st.button("🔍 Запустить детальный анализ складов", type="primary"):
                with st.spinner("🔄 Выполняется детальный анализ каждого склада..."):
                    
                    try:
                        # Получаем ADS данные для анализа
                        ads_data = system.calculated_ads if hasattr(system, 'calculated_ads') else None
                        
                        # ПРОСТОЙ АНАЛИЗ БЕЗ СЛОЖНЫХ КЛАССОВ
                        analysis_results = simple_warehouse_analysis(remains_df, ads_data, min_days, max_days)
                        
                        if analysis_results:
                            st.success("✅ Анализ складов завершен!")
                            
                            # Отображаем простые результаты
                            display_simple_warehouse_results(analysis_results)
                            
                            # Простой экспорт
                            st.subheader("📤 Экспорт результатов")
                            if st.button("📊 Экспорт результатов в Excel"):
                                export_simple_results(analysis_results)
                        else:
                            st.error("❌ Ошибка при выполнении анализа")
                            
                    except Exception as e:
                        st.error(f"❌ Ошибка анализа: {str(e)}")
                        
        except Exception as e:
            st.error(f"❌ Ошибка при чтении файла: {str(e)}")
    
    # Информация о функционале
    with st.expander("ℹ️ О детальном анализе складов"):
        st.markdown("""
        ### 🎯 Что делает детальный анализ:
        
        1. **Анализирует каждый склад индивидуально**
           - Рассчитывает MIN/MAX запасы для каждого склада
           - Определяет статус каждого товара на каждом складе
           - Показывает денежные метрики (если есть цены)
        
        2. **Категоризирует товары по статусам:**
           - 🔴 **Критичные**: остаток < 50% от MIN
           - 🟡 **Внимание**: остаток < MIN
           - 🟢 **Норма**: остаток между MIN и MAX
           - 🔵 **Избыток**: остаток > MAX
        
        3. **Предоставляет детальную информацию:**
           - Количество месяцев запаса
           - Стоимость дефицита и заказов
           - Рекомендации по каждому складу отдельно
           - Сравнение складов между собой
        
        4. **Экспортирует полные отчеты:**
           - Сводка по всем складам
           - Детальные данные по каждому складу (отдельные листы)
           - Полный анализ всех товаров
           - Денежные расчеты и приоритизация
        
        ### 💰 Работа с ценами:
        
        Если в ADS данных есть цены (колонка "Посл. закупка"), система автоматически:
        - Рассчитывает стоимость дефицита в деньгах
        - Приоритизирует товары по денежному дефициту  
        - Показывает стоимость заказов и остатков
        - Добавляет денежные метрики в отчеты
        
        ### 🏪 Поддерживаемые склады:
        
        - **База Склад Фурнитура Комплект** (Главный хаб, Алматы)
        - **Казыбаева Склад/ТД** (Алматы)
        - **Барыс Склад** (Алматы)
        - **АО Склад** (Алматы, кромочные материалы)
        - **Шымкент Склад/Магазин** (Шымкент)
        - **Астана Склад/Магазин** (Астана)
        """)

def display_warehouse_analysis_results(dashboard_data, recommendations, analysis):
    """Отображает результаты анализа складов с MIN/MAX запасами"""
    
    # Общая статистика
    st.subheader("📊 Общая статистика")
    
    summary = dashboard_data['summary']
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Всего товаров", summary['total_items'])
    with col2:
        st.metric("Критичные", summary['critical_items'], delta=f"-{summary['critical_items']}")
    with col3:
        st.metric("Требуют внимания", summary['warning_items'], delta=f"-{summary['warning_items']}")
    with col4:
        st.metric("В норме", summary['good_items'], delta=f"+{summary['good_items']}")
    with col5:
        excess_items = summary.get('excess_items', 0)
        st.metric("Избыток", excess_items, delta=f"⚠️{excess_items}")
    
    # Показываем параметры анализа
    if analysis and len(analysis) > 0:
        params = analysis[0]['parameters']
        st.info(f"📋 Параметры анализа: MIN = {params['min_days']} дней, MAX = {params['max_days']} дней")
    
    # Статистика по складам
    st.subheader("🏪 Статистика по складам")
    warehouse_stats = dashboard_data['warehouse_stats']
    st.dataframe(warehouse_stats, use_container_width=True)
    
    # Визуализация
    st.subheader("📈 Визуализация")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
    
    # График избытков
    if warehouse_stats['Товаров с избытком'].sum() > 0:
        st.subheader("⚠️ Анализ избытков")
        fig_excess = px.bar(
            warehouse_stats,
            x='Склад',
            y='Товаров с избытком',
            title='Товары с избытком по складам',
            color='Товаров с избытком',
            color_continuous_scale='Oranges'
        )
        fig_excess.update_layout(showlegend=False)
        st.plotly_chart(fig_excess, use_container_width=True)
    
    # Детальные рекомендации по складам
    st.subheader("📋 Рекомендации по складам")
    
    if not recommendations:
        st.warning("⚠️ Нет данных для отображения рекомендаций")
        return
    
    for warehouse_key, rec in recommendations.items():
        critical_items = rec.get('critical_items', [])
        warning_items = rec.get('warning_items', [])
        excess_items = rec.get('excess_items', [])
        
        total_issues = len(critical_items) + len(warning_items) + len(excess_items)
        
        if total_issues > 0:
            with st.expander(f"🏪 {rec['short_name']} - {total_issues} товаров требуют внимания"):
                
                # Критичные товары
                if critical_items:
                    st.markdown("**🚨 Критичные товары (ниже 50% от MIN):**")
                    try:
                        critical_df = pd.DataFrame(critical_items)
                        if len(critical_df) > 0:
                            required_cols = ['item', 'current_stock', 'min_stock', 'max_stock', 'order_quantity', 'ads']
                            available_cols = [col for col in required_cols if col in critical_df.columns]
                            if available_cols:
                                display_df = critical_df[available_cols].copy()
                                column_names = ['Товар', 'Остаток', 'MIN запас', 'MAX запас', 'К заказу', 'ADS']
                                display_df.columns = column_names[:len(available_cols)]
                                st.dataframe(display_df, use_container_width=True)
                            else:
                                st.dataframe(critical_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Ошибка отображения критичных товаров: {e}")
                        st.dataframe(pd.DataFrame(critical_items), use_container_width=True)
                
                # Товары требующие внимания
                if warning_items:
                    st.markdown("**⚠️ Ниже MIN запаса:**")
                    try:
                        warning_df = pd.DataFrame(warning_items)
                        if len(warning_df) > 0:
                            required_cols = ['item', 'current_stock', 'min_stock', 'max_stock', 'order_quantity', 'ads']
                            available_cols = [col for col in required_cols if col in warning_df.columns]
                            if available_cols:
                                display_df = warning_df[available_cols].copy()
                                column_names = ['Товар', 'Остаток', 'MIN запас', 'MAX запас', 'К заказу', 'ADS']
                                display_df.columns = column_names[:len(available_cols)]
                                st.dataframe(display_df, use_container_width=True)
                            else:
                                st.dataframe(warning_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Ошибка отображения товаров требующих внимания: {e}")
                        st.dataframe(pd.DataFrame(warning_items), use_container_width=True)
                
                # Товары с избытком
                if excess_items:
                    st.markdown("**📈 Товары с избытком (выше MAX):**")
                    try:
                        excess_df = pd.DataFrame(excess_items)
                        if len(excess_df) > 0:
                            required_cols = ['item', 'current_stock', 'min_stock', 'max_stock', 'max_surplus', 'ads']
                            available_cols = [col for col in required_cols if col in excess_df.columns]
                            if available_cols:
                                display_df = excess_df[available_cols].copy()
                                column_names = ['Товар', 'Остаток', 'MIN запас', 'MAX запас', 'Избыток', 'ADS']
                                display_df.columns = column_names[:len(available_cols)]
                                st.dataframe(display_df, use_container_width=True)
                            else:
                                st.dataframe(excess_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Ошибка отображения товаров с избытком: {e}")
                        st.dataframe(pd.DataFrame(excess_items), use_container_width=True)
                
                # Метрики склада
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_order_value = rec.get('total_order_value', 0)
                    st.metric("К заказу", f"{total_order_value:,.0f}", help="Рекомендуемое количество к заказу")
                with col2:
                    total_excess_value = rec.get('total_excess_value', 0)
                    st.metric("Избыток", f"{total_excess_value:,.0f}", help="Количество товара сверх MAX запаса")
                with col3:
                    efficiency = 100 - (len(critical_items) + len(warning_items)) * 10
                    st.metric("Эффективность", f"{max(0, efficiency):.0f}%", help="Процент товаров в норме")
        else:
            st.success(f"✅ {rec['short_name']} - все товары в пределах MIN/MAX запасов")
    
    # Детальная таблица всех товаров с MIN/MAX
    st.subheader("📋 Детальная информация по всем товарам")
    
    detailed_data = []
    for item in analysis:
        for warehouse_key, warehouse_data in item['warehouses'].items():
            detailed_data.append({
                'Товар': item['номенклатура'],
                'Склад': warehouse_data['short_name'],
                'Остаток': warehouse_data['current_stock'],
                'MIN запас': warehouse_data['min_stock'],
                'MAX запас': warehouse_data['max_stock'],
                'ADS': item['ads'],
                'Статус': warehouse_data['status'],
                'К заказу': warehouse_data['order_quantity'],
                'Рекомендация': warehouse_data['recommendation']
            })
    
    if detailed_data:
        detailed_df = pd.DataFrame(detailed_data)
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Фильтр по статусу:", ['Все'] + list(detailed_df['Статус'].unique()))
        with col2:
            warehouse_filter = st.selectbox("Фильтр по складу:", ['Все'] + list(detailed_df['Склад'].unique()))
        with col3:
            show_only_issues = st.checkbox("Только проблемные товары")
        
        # Применяем фильтры
        filtered_df = detailed_df.copy()
        
        if status_filter != 'Все':
            filtered_df = filtered_df[filtered_df['Статус'] == status_filter]
        
        if warehouse_filter != 'Все':
            filtered_df = filtered_df[filtered_df['Склад'] == warehouse_filter]
        
        if show_only_issues:
            filtered_df = filtered_df[filtered_df['Статус'].isin(['critical', 'warning', 'excess'])]
        
        # Цветовая кодировка статусов - исправление для больших таблиц
        def color_status(val):
            if val == 'critical':
                return 'background-color: #ffebee'
            elif val == 'warning':
                return 'background-color: #fff3e0'
            elif val == 'excess':
                return 'background-color: #fce4ec'
            elif val == 'good':
                return 'background-color: #e8f5e8'
            else:
                return ''
        
        # Проверяем размер таблицы для применения стилей
        max_cells_for_styling = 50000
        total_cells = len(filtered_df) * len(filtered_df.columns)
        
        if total_cells <= max_cells_for_styling:
            styled_df = filtered_df.style.applymap(color_status, subset=['Статус'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.warning(f"⚠️ Таблица слишком большая ({total_cells:,} ячеек) для применения цветовых стилей.")
            st.dataframe(filtered_df, use_container_width=True)
        
        st.info(f"📊 Показано {len(filtered_df)} из {len(detailed_df)} записей")
    
    # Экспорт результатов
    st.subheader("📤 Экспорт результатов")
    
    if st.button("📊 Экспортировать анализ складов"):
        export_warehouse_analysis(recommendations, analysis, warehouse_stats)
    
    # Заказы на закупку с ценами
    st.subheader("🛒 Заказы на закупку")
    
    # Получаем ADS данные с ценами напрямую из анализа складов
    ads_data_with_prices = None
    try:
        # Получаем данные из системы складов (не зависим от сравнения остатков)
        if hasattr(st.session_state, 'inventory_system'):
            system = st.session_state.inventory_system
            if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
                ads_data_with_prices = system.calculated_ads
                
                # Проверяем наличие ценовых колонок
                price_columns = ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']
                has_prices = any(col in ads_data_with_prices.columns for col in price_columns)
                
                if has_prices:
                    items_with_prices = 0
                    for col in price_columns:
                        if col in ads_data_with_prices.columns:
                            items_with_prices += (ads_data_with_prices[col] > 0).sum()
                            break
                    
                    st.info(f"✅ Найдены ADS данные: {len(ads_data_with_prices)} товаров, из них {items_with_prices} с ценами")
                else:
                    st.warning(f"⚠️ ADS данные найдены ({len(ads_data_with_prices)} товаров), но без ценовой информации")
                    ads_data_with_prices = None
            else:
                st.warning("⚠️ ADS данные не найдены в системе")
        else:
            st.warning("⚠️ Система не инициализирована")
    except Exception as e:
        st.error(f"❌ Ошибка получения ADS данных: {e}")
        ads_data_with_prices = None
    
    if ads_data_with_prices is not None:
        # Создаем заказы с ценами
        purchase_orders = create_purchase_orders_from_analysis(analysis, recommendations, ads_data_with_prices)
        
        if purchase_orders:
            # Показываем сводку по заказам
            summary = get_purchase_summary_from_orders(purchase_orders)
            
            st.markdown("**📊 Сводка по заказам:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Складов с заказами", summary['total_warehouses'])
            with col2:
                st.metric("Позиций к заказу", summary['total_items_to_order'])
            with col3:
                st.metric("Общее количество", f"{summary['total_quantity']:,.0f}")
            with col4:
                if summary['total_cost'] > 0:
                    st.metric("Общая стоимость", f"{summary['total_cost']:,.0f} ₸")
                else:
                    st.metric("Общая стоимость", "Цены недоступны")
            
            # Дополнительная информация о ценах
            if summary['items_with_prices'] > 0:
                price_coverage = (summary['items_with_prices'] / summary['total_items_to_order']) * 100
                st.info(f"💰 Ценовое покрытие: {summary['items_with_prices']} из {summary['total_items_to_order']} товаров ({price_coverage:.1f}%)")
            else:
                st.warning("⚠️ Цены не найдены ни для одного товара")
            
            # Показываем заказы по складам
            for warehouse_key, orders in purchase_orders.items():
                if orders['orders']:
                    cost_info = f" - заказ на {orders['total_cost']:,.0f} ₸" if orders['total_cost'] > 0 else " - без ценовой информации"
                    
                    with st.expander(f"🛒 {orders['short_name']}{cost_info}"):
                        
                        orders_df = pd.DataFrame(orders['orders'])
                        
                        # Проверяем наличие ценовой информации
                        if 'unit_price' in orders_df.columns and orders_df['unit_price'].sum() > 0:
                            display_cols = ['item', 'type', 'current_stock', 'target_stock', 
                                          'order_quantity', 'unit_price', 'total_cost']
                            column_names = ['Товар', 'Тип заказа', 'Текущий остаток', 'Целевой остаток', 
                                          'К заказу', 'Цена за ед.', 'Стоимость']
                        else:
                            display_cols = ['item', 'type', 'current_stock', 'target_stock', 'order_quantity']
                            column_names = ['Товар', 'Тип заказа', 'Текущий остаток', 'Целевой остаток', 'К заказу']
                        
                        display_df = orders_df[display_cols].copy()
                        display_df.columns = column_names
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Метрики по складу
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Позиций", len(orders['orders']))
                        with col2:
                            st.metric("Количество", f"{orders['total_quantity']:,.0f}")
                        with col3:
                            if orders['total_cost'] > 0:
                                st.metric("Стоимость", f"{orders['total_cost']:,.0f} ₸")
                            else:
                                st.metric("Стоимость", "Не определена")
            
            # Кнопка экспорта заказов
            if st.button("📥 Экспортировать заказы"):
                export_purchase_orders(purchase_orders, summary)
        else:
            st.info("📋 Нет товаров для заказа")
    else:
        # Альтернативный вариант без цен - показываем только количества
        st.warning("⚠️ Ценовая информация недоступна. Показываем заказы без стоимости.")
        
        # Создаем упрощенные заказы без цен
        simple_orders = create_simple_orders_from_analysis(analysis, recommendations)
        
        if simple_orders:
            st.markdown("**📊 Сводка по заказам (без цен):**")
            col1, col2, col3 = st.columns(3)
            
            total_warehouses = len(simple_orders)
            total_items = sum(len(orders['orders']) for orders in simple_orders.values())
            total_quantity = sum(orders['total_quantity'] for orders in simple_orders.values())
            
            with col1:
                st.metric("Складов с заказами", total_warehouses)
            with col2:
                st.metric("Позиций к заказу", total_items)
            with col3:
                st.metric("Общее количество", f"{total_quantity:,.0f}")
            
            # Показываем упрощенные заказы
            for warehouse_key, orders in simple_orders.items():
                if orders['orders']:
                    with st.expander(f"🛒 {orders['short_name']} - {len(orders['orders'])} позиций"):
                        
                        orders_df = pd.DataFrame(orders['orders'])
                        orders_df = orders_df[['item', 'type', 'current_stock', 'target_stock', 'order_quantity']]
                        orders_df.columns = ['Товар', 'Тип заказа', 'Текущий остаток', 'Целевой остаток', 'К заказу']
                        
                        st.dataframe(orders_df, use_container_width=True)
        else:
            st.info("📋 Нет товаров для заказа")


def create_purchase_orders_from_analysis(analysis, recommendations, ads_data_with_prices):
    """Создает заказы на закупку на основе анализа складов"""
    purchase_orders = {}
    
    for warehouse_key, rec in recommendations.items():
        warehouse_orders = {
            'warehouse_name': rec['name'],
            'short_name': rec['short_name'],
            'orders': [],
            'total_quantity': 0,
            'total_cost': 0
        }
        
        # Обрабатываем критичные товары (заказ до MAX)
        for item in rec.get('critical_items', []):
            price = get_item_price_from_ads(item['item'], ads_data_with_prices)
            order_cost = item['order_quantity'] * price
            
            order_item = {
                'item': item['item'],
                'type': 'Критично - до MAX',
                'current_stock': item['current_stock'],
                'target_stock': item['max_stock'],
                'order_quantity': item['order_quantity'],
                'unit_price': price,
                'total_cost': order_cost,
                'priority': 1
            }
            
            warehouse_orders['orders'].append(order_item)
            warehouse_orders['total_quantity'] += item['order_quantity']
            warehouse_orders['total_cost'] += order_cost
        
        # Обрабатываем товары требующие внимания (заказ до MIN)
        for item in rec.get('warning_items', []):
            price = get_item_price_from_ads(item['item'], ads_data_with_prices)
            order_cost = item['order_quantity'] * price
            
            order_item = {
                'item': item['item'],
                'type': 'Внимание - до MIN',
                'current_stock': item['current_stock'],
                'target_stock': item['min_stock'],
                'order_quantity': item['order_quantity'],
                'unit_price': price,
                'total_cost': order_cost,
                'priority': 2
            }
            
            warehouse_orders['orders'].append(order_item)
            warehouse_orders['total_quantity'] += item['order_quantity']
            warehouse_orders['total_cost'] += order_cost
        
        # Сортируем заказы по приоритету
        warehouse_orders['orders'].sort(key=lambda x: x['priority'])
        
        if warehouse_orders['orders']:
            purchase_orders[warehouse_key] = warehouse_orders
    
    return purchase_orders


def get_item_price_from_ads(item_name, ads_data_with_prices):
    """
    Получает цену товара из ADS данных
    Поддерживает различные колонки с ценами и форматы данных
    """
    if ads_data_with_prices is None or ads_data_with_prices.empty:
        return 0.0
    
    # Ищем товар в ADS данных
    price_match = ads_data_with_prices[ads_data_with_prices['номенклатура'] == item_name]
    
    if not price_match.empty:
        # Расширенный список возможных колонок с ценами
        price_columns = [
            'last_purchase_price',    # Основная колонка
            'цена',                   # Русское название
            'price',                  # Английское название
            'стоимость',             # Альтернативное русское
            'закупочная_цена',       # Специфичная для закупок
            'себестоимость',         # Себестоимость
            'purchase_price',        # Альтернативное английское
            'unit_price',           # Цена за единицу
            'cost'                  # Стоимость
        ]
        
        for col in price_columns:
            if col in price_match.columns:
                try:
                    price_value = price_match.iloc[0][col]
                    
                    # Обрабатываем различные форматы данных
                    if pd.notna(price_value):
                        # Преобразуем в строку для обработки
                        price_str = str(price_value).strip()
                        
                        # Убираем возможные нечисловые символы
                        price_str = price_str.replace(' ', '').replace(',', '.')
                        price_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
                        
                        if price_str:
                            price_float = float(price_str)
                            if price_float > 0:
                                return price_float
                                
                except (ValueError, TypeError, AttributeError):
                    continue  # Пробуем следующую колонку
    
    return 0.0  # Если цена не найдена


def create_simple_orders_from_analysis(analysis, recommendations):
    """Создает упрощенные заказы без ценовой информации"""
    simple_orders = {}
    
    for warehouse_key, rec in recommendations.items():
        warehouse_orders = {
            'warehouse_name': rec['name'],
            'short_name': rec['short_name'],
            'orders': [],
            'total_quantity': 0
        }
        
        # Обрабатываем критичные товары
        for item in rec.get('critical_items', []):
            order_item = {
                'item': item['item'],
                'type': 'Критично - до MAX',
                'current_stock': item['current_stock'],
                'target_stock': item['max_stock'],
                'order_quantity': item['order_quantity'],
                'priority': 1
            }
            
            warehouse_orders['orders'].append(order_item)
            warehouse_orders['total_quantity'] += item['order_quantity']
        
        # Обрабатываем товары требующие внимания
        for item in rec.get('warning_items', []):
            order_item = {
                'item': item['item'],
                'type': 'Внимание - до MIN',
                'current_stock': item['current_stock'],
                'target_stock': item['min_stock'],
                'order_quantity': item['order_quantity'],
                'priority': 2
            }
            
            warehouse_orders['orders'].append(order_item)
            warehouse_orders['total_quantity'] += item['order_quantity']
        
        # Сортируем заказы по приоритету
        warehouse_orders['orders'].sort(key=lambda x: x['priority'])
        
        if warehouse_orders['orders']:
            simple_orders[warehouse_key] = warehouse_orders
    
    return simple_orders


def get_purchase_summary_from_orders(purchase_orders):
    """Создает сводку по заказам с улучшенной обработкой цен"""
    summary = {
        'total_warehouses': len(purchase_orders),
        'total_items_to_order': 0,
        'total_quantity': 0,
        'total_cost': 0,
        'critical_orders': 0,
        'warning_orders': 0,
        'items_with_prices': 0,  # Новое поле
        'most_expensive_warehouse': '',
        'most_expensive_cost': 0
    }
    
    for warehouse_key, orders in purchase_orders.items():
        summary['total_items_to_order'] += len(orders['orders'])
        summary['total_quantity'] += orders['total_quantity']
        summary['total_cost'] += orders.get('total_cost', 0)
        
        # Подсчитываем критичные и предупреждающие заказы
        for order in orders['orders']:
            if order['priority'] == 1:
                summary['critical_orders'] += 1
            else:
                summary['warning_orders'] += 1
            
            # Подсчитываем товары с ценами
            if order.get('unit_price', 0) > 0:
                summary['items_with_prices'] += 1
        
        warehouse_cost = orders.get('total_cost', 0)
        if warehouse_cost > summary['most_expensive_cost']:
            summary['most_expensive_cost'] = warehouse_cost
            summary['most_expensive_warehouse'] = orders['short_name']
    
    return summary


def export_purchase_orders(purchase_orders, summary):
    """Экспортирует заказы на закупку в Excel"""
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Лист с общей сводкой
            summary_data = [
                ['Параметр', 'Значение'],
                ['Складов с заказами', summary['total_warehouses']],
                ['Всего позиций к заказу', summary['total_items_to_order']],
                ['Общее количество', summary['total_quantity']],
                ['Общая стоимость', summary['total_cost']],
                ['Критичных заказов', summary['critical_orders']],
                ['Заказов внимания', summary['warning_orders']],
                ['Самый дорогой склад', summary['most_expensive_warehouse']],
                ['Стоимость самого дорогого', summary['most_expensive_cost']],
                ['Дата создания', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')]
            ]
            
            summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            summary_df.to_excel(writer, sheet_name='Сводка заказов', index=False)
            
            # Листы по каждому складу
            for warehouse_key, orders in purchase_orders.items():
                if orders['orders']:
                    orders_df = pd.DataFrame(orders['orders'])
                    orders_df = orders_df[['item', 'type', 'current_stock', 'target_stock', 
                                          'order_quantity', 'unit_price', 'total_cost']]
                    orders_df.columns = ['Товар', 'Тип_заказа', 'Текущий_остаток', 'Целевой_остаток', 
                                       'К_заказу', 'Цена_за_ед', 'Стоимость']
                    
                    sheet_name = orders['short_name'][:31]
                    orders_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Общий лист со всеми заказами
            all_orders = []
            for warehouse_key, orders in purchase_orders.items():
                for order in orders['orders']:
                    all_orders.append({
                        'Склад': orders['short_name'],
                        'Товар': order['item'],
                        'Тип_заказа': order['type'],
                        'Текущий_остаток': order['current_stock'],
                        'Целевой_остаток': order['target_stock'],
                        'К_заказу': order['order_quantity'],
                        'Цена_за_ед': order['unit_price'],
                        'Стоимость': order['total_cost'],
                        'Приоритет': 'Критично' if order['priority'] == 1 else 'Внимание'
                    })
            
            if all_orders:
                all_orders_df = pd.DataFrame(all_orders)
                all_orders_df.to_excel(writer, sheet_name='Все заказы', index=False)
        
        output.seek(0)
        
        st.download_button(
            label="📥 Скачать заказы Excel",
            data=output.getvalue(),
            file_name=f"заказы_на_закупку_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Файл заказов готов к скачиванию!")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта заказов: {e}")


def export_warehouse_analysis(recommendations, analysis, warehouse_stats):
    """Экспортирует результаты анализа складов в Excel с MIN/MAX данными"""
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Лист со статистикой по складам
            warehouse_stats.to_excel(writer, sheet_name='Статистика складов', index=False)
            
            # Листы с рекомендациями по каждому складу
            for warehouse_key, rec in recommendations.items():
                all_items = []
                
                # Критичные товары
                for item in rec.get('critical_items', []):
                    all_items.append({
                        'Товар': item['item'],
                        'Приоритет': 'Критично',
                        'Остаток': item['current_stock'],
                        'MIN_запас': item['min_stock'],
                        'MAX_запас': item['max_stock'],
                        'К_заказу': item['order_quantity'],
                        'ADS': item['ads'],
                        'Дефицит_MIN': item['min_deficit']
                    })
                
                # Товары требующие внимания
                for item in rec.get('warning_items', []):
                    all_items.append({
                        'Товар': item['item'],
                        'Приоритет': 'Внимание',
                        'Остаток': item['current_stock'],
                        'MIN_запас': item['min_stock'],
                        'MAX_запас': item['max_stock'],
                        'К_заказу': item['order_quantity'],
                        'ADS': item['ads'],
                        'Дефицит_MIN': item['min_deficit']
                    })
                
                # Товары с избытком
                for item in rec.get('excess_items', []):
                    all_items.append({
                        'Товар': item['item'],
                        'Приоритет': 'Избыток',
                        'Остаток': item['current_stock'],
                        'MIN_запас': item['min_stock'],
                        'MAX_запас': item['max_stock'],
                        'К_заказу': 0,
                        'ADS': item['ads'],
                        'Избыток_MAX': item['max_surplus']
                    })
                
                if all_items:
                    items_df = pd.DataFrame(all_items)
                    sheet_name = rec['short_name'][:31]
                    items_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Общий лист с анализом всех товаров
            all_analysis = []
            for item in analysis:
                for warehouse_key, warehouse_data in item['warehouses'].items():
                    all_analysis.append({
                        'Товар': item['номенклатура'],
                        'Склад': warehouse_data['short_name'],
                        'Остаток': warehouse_data['current_stock'],
                        'MIN_запас': warehouse_data['min_stock'],
                        'MAX_запас': warehouse_data['max_stock'],
                        'Статус': warehouse_data['status'],
                        'К_заказу': warehouse_data['order_quantity'],
                        'ADS': item['ads'],
                        'Рекомендация': warehouse_data['recommendation']
                    })
            
            if all_analysis:
                analysis_df = pd.DataFrame(all_analysis)
                analysis_df.to_excel(writer, sheet_name='Детальный анализ', index=False)
            
            # Лист с параметрами анализа
            if analysis and len(analysis) > 0:
                params = analysis[0]['parameters']
                params_data = [
                    ['Параметр', 'Значение'],
                    ['MIN дни запаса', params['min_days']],
                    ['MAX дни запаса', params['max_days']],
                    ['Дата анализа', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')],
                    ['Всего товаров', len(analysis)],
                    ['Общих складов', len(recommendations)]
                ]
                
                params_df = pd.DataFrame(params_data[1:], columns=params_data[0])
                params_df.to_excel(writer, sheet_name='Параметры анализа', index=False)
        
        output.seek(0)
        
        st.download_button(
            label="📥 Скачать Excel файл",
            data=output.getvalue(),
            file_name=f"анализ_складов_MIN_MAX_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Файл готов к скачиванию!")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта: {e}")

def integrate_store_ads_with_warehouse_analysis(system):
    """
    Интегрирует ADS данные из анализа магазинов с анализом складов
    """
    
    # Проверяем есть ли данные по магазинам
    if not hasattr(system, 'multiple_files_data') or not system.multiple_files_data:
        return None
        
    # Получаем ADS данные по городам
    store_ads_by_city = {}
    
    if 'processed_results' in system.multiple_files_data:
        processed_results = system.multiple_files_data['processed_results']
        
        if isinstance(processed_results, dict):
            for filename, result_data in processed_results.items():
                try:
                    # Используем функции из streamlit_modular_app.py
                    from streamlit_modular_app import _extract_branch_name, get_store_type_and_city
                    
                    # Извлекаем информацию о магазине
                    branch_name = _extract_branch_name(filename)
                    city, store_type = get_store_type_and_city(branch_name)
                    
                    # Ищем ADS данные
                    ads_data = None
                    if isinstance(result_data, dict):
                        for key in ['calculated_ads', 'ads_data', 'data', 'result']:
                            if key in result_data and result_data[key] is not None:
                                if hasattr(result_data[key], 'columns'):
                                    ads_data = result_data[key]
                                    break
                    elif hasattr(result_data, 'columns'):
                        ads_data = result_data
                    
                    if ads_data is not None and hasattr(ads_data, 'columns'):
                        # Группируем по городам
                        if city not in store_ads_by_city:
                            store_ads_by_city[city] = []
                        
                        store_ads_by_city[city].append({
                            'store_type': store_type,
                            'branch_name': branch_name,
                            'ads_data': ads_data
                        })
                        
                except Exception as e:
                    continue
    
    return store_ads_by_city

def create_unified_ads_by_city(store_ads_by_city):
    """
    Создает объединенные ADS данные по городам
    """
    unified_ads = {}
    
    for city, stores in store_ads_by_city.items():
        # Объединяем ADS данные всех магазинов города
        city_ads_data = []
        
        for store in stores:
            ads_data = store['ads_data'].copy()
            if 'номенклатура' in ads_data.columns:
                # Добавляем информацию о магазине
                ads_data['source_store'] = store['branch_name']
                ads_data['store_type'] = store['store_type']
                city_ads_data.append(ads_data)
        
        if city_ads_data:
            # Объединяем все данные города
            combined_city_data = pd.concat(city_ads_data, ignore_index=True)
            
            # Группируем по номенклатуре и суммируем ADS
            if 'номенклатура' in combined_city_data.columns and 'ads' in combined_city_data.columns:
                unified_city_ads = combined_city_data.groupby('номенклатура').agg({
                    'ads': 'sum',
                    'total_sales': 'sum' if 'total_sales' in combined_city_data.columns else 'first'
                }).reset_index()
                
                unified_ads[city] = unified_city_ads
    
    return unified_ads

def get_warehouse_city_mapping():
    """
    Создает маппинг складов по городам
    """
    return {
        'шымкент': [
            'Шымкент_Овощная_база',
            'Овощная_база_Магазин'
        ],
        'барыс': [
            'Барыс_TRADE'
        ],
        'казыбаева': [
            'Казыбаева_TRADE',
            'Казыбаева_магазин'
        ],
        'астана': [
            'АО_TRADE',  # Перенесено из общих в астану
        ],
        'общие': [
            'База_Комплект', 
            'Магазин_фурнитуры',
            'Склад_1'
        ]
    }

def display_enhanced_warehouse_results(analysis, store_ads_by_city):
    """
    Отображает результаты улучшенного анализа складов
    """
    
    st.subheader("📊 Результаты анализа по городам")
    
    # Группируем результаты по городам
    results_by_city = {}
    
    for item in analysis:
        for warehouse_key, warehouse_data in item['warehouses'].items():
            city = warehouse_data['city'] or 'общие'
            
            if city not in results_by_city:
                results_by_city[city] = {
                    'critical': 0,
                    'warning': 0,
                    'good': 0,
                    'excess': 0,
                    'no_ads': 0,
                    'total_order': 0,
                    'warehouses': []
                }
            
            status = warehouse_data['status']
            results_by_city[city][status] += 1
            results_by_city[city]['total_order'] += warehouse_data['order_quantity']
            
            if warehouse_data['short_name'] not in results_by_city[city]['warehouses']:
                results_by_city[city]['warehouses'].append(warehouse_data['short_name'])
    
    # Показываем результаты по городам
    for city, data in results_by_city.items():
        st.write(f"### {city.title()}")
        st.write(f"*Склады: {', '.join(data['warehouses'])}*")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("🔴 Критичные", data['critical'])
        with col2:
            st.metric("🟡 Внимание", data['warning']) 
        with col3:
            st.metric("🟢 Норма", data['good'])
        with col4:
            st.metric("🔵 Избыток", data['excess'])
        with col5:
            st.metric("📦 К заказу", f"{data['total_order']:.0f}")
    
    # Детальная таблица
    st.subheader("📋 Детальные результаты")
    
    detailed_results = []
    for item in analysis:
        for warehouse_key, warehouse_data in item['warehouses'].items():
            if warehouse_data['current_stock'] > 0 or warehouse_data['order_quantity'] > 0:  # Показываем только значимые записи
                detailed_results.append({
                    'Товар': item['номенклатура'][:50],  # Обрезаем длинные названия
                    'Склад': warehouse_data['short_name'],
                    'Город': warehouse_data['city'] or 'общий',
                    'Остаток': warehouse_data['current_stock'],
                    'ADS': round(warehouse_data['ads'], 4),
                    'MIN': round(warehouse_data['min_stock'], 0),
                    'MAX': round(warehouse_data['max_stock'], 0),
                    'Статус': warehouse_data['status'],
                    'К заказу': round(warehouse_data['order_quantity'], 0),
                    'Месяцев запаса': round(warehouse_data['months_of_stock'], 1) if warehouse_data['months_of_stock'] < 99 else '∞'
                })
    
    if detailed_results:
        df_results = pd.DataFrame(detailed_results)
        
        # Фильтры для таблицы
        col1, col2, col3 = st.columns(3)
        with col1:
            city_filter = st.selectbox("Фильтр по городу:", ['Все'] + list(results_by_city.keys()))
        with col2:
            status_filter = st.selectbox("Фильтр по статусу:", ['Все', 'critical', 'warning', 'good', 'excess', 'no_ads'])
        with col3:
            warehouse_filter = st.selectbox("Фильтр по складу:", ['Все'] + df_results['Склад'].unique().tolist())
        
        # Применяем фильтры
        filtered_df = df_results.copy()
        
        if city_filter != 'Все':
            filtered_df = filtered_df[filtered_df['Город'] == city_filter]
        
        if status_filter != 'Все':
            filtered_df = filtered_df[filtered_df['Статус'] == status_filter]
            
        if warehouse_filter != 'Все':
            filtered_df = filtered_df[filtered_df['Склад'] == warehouse_filter]
        
        st.write(f"Показано записей: {len(filtered_df)} из {len(df_results)}")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Экспорт
        if st.button("📊 Экспорт результатов в Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_results.to_excel(writer, sheet_name='Анализ_складов', index=False)
                
                # Добавляем сводку по городам
                summary_data = []
                for city, data in results_by_city.items():
                    summary_data.append({
                        'Город': city,
                        'Склады': ', '.join(data['warehouses']),
                        'Критичные': data['critical'],
                        'Внимание': data['warning'],
                        'Норма': data['good'],
                        'Избыток': data['excess'],
                        'К_заказу': data['total_order']
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Сводка_по_городам', index=False)
            
            output.seek(0)
            st.download_button(
                label="💾 Скачать анализ складов",
                data=output,
                file_name=f"warehouse_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
def simple_warehouse_analysis(remains_df, ads_data, min_days=10, max_days=50):
    """
    Простой анализ складов без сложных классов
    """
    
    if remains_df is None or remains_df.empty:
        return None
    
    # Конфигурация складов
    warehouse_config = {
        'База Склад Фурнитура Комплект': {
            'short_name': 'База Комплект',
            'city': 'алматы',
            'type': 'hub'
        },
        'Казыбаева Склад Фурнитура TRADE': {
            'short_name': 'Казыбаева Склад',
            'city': 'алматы',
            'type': 'warehouse'
        },
        'ТД Казыбаева ФУРНИТУРА магазин': {
            'short_name': 'Казыбаева ТД',
            'city': 'алматы',
            'type': 'store'
        },
        'Барыс Склад Фурнитура TRADE': {
            'short_name': 'Барыс',
            'city': 'алматы',
            'type': 'store_warehouse'
        },
        'АО Склад Фурнитура TRADE': {
            'short_name': 'АО Склад',
            'city': 'алматы',
            'type': 'specialized_store'
        },
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
            'short_name': 'Шымкент Склад',
            'city': 'шымкент',
            'type': 'warehouse'
        },
        '6 Склад фурнитуры "Овощная база" Магазин': {
            'short_name': 'Шымкент Магазин',
            'city': 'шымкент',
            'type': 'store'
        },
        'склад фурнитура № 1': {
            'short_name': 'Астана Склад',
            'city': 'астана',
            'type': 'warehouse'
        },
        'Магазин фурнитуры': {
            'short_name': 'Астана Магазин',
            'city': 'астана',
            'type': 'store'
        }
    }
    
    results = []
    print(f"🔄 Начинаем анализ {len(remains_df)} товаров")
    
    for _, item in remains_df.iterrows():
        item_name = item['номенклатура']
        
        # Получаем ADS для товара
        ads_value = 0
        item_price = 0
        
        if ads_data is not None and not ads_data.empty:
            ads_match = ads_data[ads_data['номенклатура'] == item_name]
            if not ads_match.empty:
                ads_value = ads_match.iloc[0].get('ads', 0)
                # Проверяем наличие цен
                price_columns = ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']
                for col in price_columns:
                    if col in ads_match.columns:
                        item_price = ads_match.iloc[0].get(col, 0)
                        break
        
        item_result = {
            'номенклатура': item_name,
            'ads': ads_value,
            'price': item_price,
            'warehouses': []
        }
        
        # Анализируем каждый склад
        for col in remains_df.columns:
            if 'остаток' in col.lower():
                # Извлекаем название склада
                warehouse_name = col.replace('_остаток', '').replace(' остаток', '').strip()
                
                # Ищем конфигурацию склада по ключевым словам
                config = None
                for full_name, conf in warehouse_config.items():
                    # Проверяем точное совпадение или вхождение ключевых слов
                    if (warehouse_name.lower() == full_name.lower() or
                        any(word.lower() in warehouse_name.lower() for word in full_name.split() if len(word) > 3)):
                        config = conf.copy()
                        config['full_name'] = full_name
                        break
                
                # Если не нашли точное совпадение, пробуем по ключевым словам
                if not config:
                    warehouse_lower = warehouse_name.lower()
                    if 'база' in warehouse_lower and 'комплект' in warehouse_lower:
                        config = warehouse_config['База Склад Фурнитура Комплект'].copy()
                        config['full_name'] = warehouse_name
                    elif 'казыбаева' in warehouse_lower:
                        if 'тд' in warehouse_lower or 'магазин' in warehouse_lower:
                            config = warehouse_config['ТД Казыбаева ФУРНИТУРА магазин'].copy()
                        else:
                            config = warehouse_config['Казыбаева Склад Фурнитура TRADE'].copy()
                        config['full_name'] = warehouse_name
                    elif 'барыс' in warehouse_lower:
                        config = warehouse_config['Барыс Склад Фурнитура TRADE'].copy()
                        config['full_name'] = warehouse_name
                    elif 'ао' in warehouse_lower:
                        config = warehouse_config['АО Склад Фурнитура TRADE'].copy()
                        config['full_name'] = warehouse_name
                    elif 'шымкент' in warehouse_lower or 'овощная' in warehouse_lower:
                        if 'магазин' in warehouse_lower:
                            config = warehouse_config['6 Склад фурнитуры "Овощная база" Магазин'].copy()
                        else:
                            config = warehouse_config['4 Склад фурнитуры АЗМ Шымкент "Овощная база"'].copy()
                        config['full_name'] = warehouse_name
                    elif 'астана' in warehouse_lower:
                        if 'магазин' in warehouse_lower:
                            config = warehouse_config['Магазин фурнитуры'].copy()
                        else:
                            config = warehouse_config['склад фурнитура № 1'].copy()
                        config['full_name'] = warehouse_name
                    else:
                        # Неизвестный склад
                        config = {
                            'short_name': warehouse_name,
                            'city': 'неизвестно',
                            'type': 'склад',
                            'full_name': warehouse_name
                        }
                
                current_stock = item.get(col, 0)
                
                if current_stock > 0 or ads_value > 0:
                    # Рассчитываем MIN и MAX
                    min_stock = ads_value * min_days if ads_value > 0 else 0
                    max_stock = ads_value * max_days if ads_value > 0 else 0
                    
                    # Статус
                    status = 'good'
                    if current_stock < min_stock * 0.5:
                        status = 'critical'
                    elif current_stock < min_stock:
                        status = 'warning'
                    elif current_stock > max_stock:
                        status = 'excess'
                    
                    # Дефицит и заказ
                    min_deficit = max(0, min_stock - current_stock)
                    order_quantity = max(0, max_stock - current_stock) if status in ['critical', 'warning'] else 0
                    
                    # Месяцы запаса
                    months_of_stock = 0
                    if ads_value > 0:
                        months_of_stock = current_stock / (ads_value * 30)
                    elif current_stock > 0:
                        months_of_stock = 999
                    
                    # Денежные расчеты
                    deficit_cost = min_deficit * item_price if item_price > 0 else 0
                    order_cost = order_quantity * item_price if item_price > 0 else 0
                    stock_value = current_stock * item_price if item_price > 0 else 0
                    
                    item_result['warehouses'].append({
                        'warehouse_name': warehouse_name,
                        'full_name': config['full_name'],
                        'short_name': config['short_name'],
                        'city': config['city'],
                        'type': config['type'],
                        'current_stock': current_stock,
                        'min_stock': min_stock,
                        'max_stock': max_stock,
                        'min_deficit': min_deficit,
                        'order_quantity': order_quantity,
                        'status': status,
                        'months_of_stock': months_of_stock,
                        'ads': ads_value,
                        'price': item_price,
                        'deficit_cost': deficit_cost,
                        'order_cost': order_cost,
                        'stock_value': stock_value
                    })
        
        if item_result['warehouses']:
            results.append(item_result)
    
    print(f"✅ Анализ завершен: {len(results)} товаров обработано")
    return results

def display_simple_warehouse_results(analysis_results):
    """
    Простое отображение результатов анализа складов
    """
    
    st.subheader("📊 Результаты анализа складов")
    
    # Собираем статистику по складам
    warehouse_stats = {}
    has_prices = False
    
    for item in analysis_results:
        for warehouse in item['warehouses']:
            wh_name = warehouse['short_name']
            
            if wh_name not in warehouse_stats:
                warehouse_stats[wh_name] = {
                    'full_name': warehouse['full_name'],
                    'city': warehouse['city'],
                    'type': warehouse['type'],
                    'critical_count': 0,
                    'warning_count': 0,
                    'good_count': 0,
                    'excess_count': 0,
                    'total_order_cost': 0,
                    'total_stock_value': 0,
                    'total_deficit_cost': 0
                }
            
            stats = warehouse_stats[wh_name]
            
            if warehouse['status'] == 'critical':
                stats['critical_count'] += 1
            elif warehouse['status'] == 'warning':
                stats['warning_count'] += 1
            elif warehouse['status'] == 'excess':
                stats['excess_count'] += 1
            else:
                stats['good_count'] += 1
            
            stats['total_order_cost'] += warehouse.get('order_cost', 0)
            stats['total_stock_value'] += warehouse.get('stock_value', 0)
            stats['total_deficit_cost'] += warehouse.get('deficit_cost', 0)
            
            if warehouse.get('price', 0) > 0:
                has_prices = True
    
    # Показываем сводку по складам
    st.markdown("### 📈 Сводка по складам")
    
    summary_data = []
    for wh_name, stats in warehouse_stats.items():
        total_items = stats['critical_count'] + stats['warning_count'] + stats['good_count'] + stats['excess_count']
        
        summary_data.append({
            'Склад': stats['full_name'],
            'Город': stats['city'].title(),
            'Тип': stats['type'],
            'Всего товаров': total_items,
            'Критичные': stats['critical_count'],
            'Внимание': stats['warning_count'],
            'Норма': stats['good_count'],
            'Избыток': stats['excess_count'],
            'К заказу (₸)': f"{stats['total_order_cost']:,.0f}" if has_prices else "Нет цен",
            'Стоимость остатков (₸)': f"{stats['total_stock_value']:,.0f}" if has_prices else "Нет цен"
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Общие метрики
    total_critical = sum(stats['critical_count'] for stats in warehouse_stats.values())
    total_warning = sum(stats['warning_count'] for stats in warehouse_stats.values())
    total_order_cost = sum(stats['total_order_cost'] for stats in warehouse_stats.values())
    total_stock_value = sum(stats['total_stock_value'] for stats in warehouse_stats.values())
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔴 Критичные товары", total_critical)
    with col2:
        st.metric("🟡 Требуют внимания", total_warning)
    with col3:
        if has_prices:
            st.metric("💰 К заказу", f"{total_order_cost:,.0f} ₸")
        else:
            st.metric("📦 К заказу", "Нет цен")
    with col4:
        if has_prices:
            st.metric("💎 Стоимость остатков", f"{total_stock_value:,.0f} ₸")
        else:
            st.metric("📦 Стоимость остатков", "Нет цен")
    
    # Детальная таблица критичных товаров
    st.markdown("### 🔴 Критичные товары по складам")
    
    critical_items = []
    for item in analysis_results:
        for warehouse in item['warehouses']:
            if warehouse['status'] == 'critical':
                critical_items.append({
                    'Товар': item['номенклатура'][:50] + '...' if len(item['номенклатура']) > 50 else item['номенклатура'],
                    'Склад': warehouse['short_name'],
                    'Город': warehouse['city'],
                    'Остаток': int(warehouse['current_stock']),
                    'MIN': int(warehouse['min_stock']),
                    'Дефицит': int(warehouse['min_deficit']),
                    'К заказу': int(warehouse['order_quantity']),
                    'ADS': f"{warehouse['ads']:.3f}",
                    'Месяцев': f"{warehouse['months_of_stock']:.1f}" if warehouse['months_of_stock'] < 99 else "999+",
                    'Стоимость заказа': f"{warehouse['order_cost']:,.0f}" if has_prices else "Нет"
                })
    
    if critical_items:
        critical_df = pd.DataFrame(critical_items)
        st.dataframe(critical_df, use_container_width=True)
        st.write(f"**Найдено критичных позиций: {len(critical_items)}**")
    else:
        st.info("✅ Критичных товаров не найдено")
    
    # Детальная таблица товаров требующих внимания
    st.markdown("### 🟡 Товары требующие внимания")
    
    warning_items = []
    for item in analysis_results:
        for warehouse in item['warehouses']:
            if warehouse['status'] == 'warning':
                warning_items.append({
                    'Товар': item['номенклатура'][:50] + '...' if len(item['номенклатура']) > 50 else item['номенклатура'],
                    'Склад': warehouse['short_name'],
                    'Город': warehouse['city'],
                    'Остаток': int(warehouse['current_stock']),
                    'MIN': int(warehouse['min_stock']),
                    'Дефицит': int(warehouse['min_deficit']),
                    'К заказу': int(warehouse['order_quantity']),
                    'ADS': f"{warehouse['ads']:.3f}",
                    'Месяцев': f"{warehouse['months_of_stock']:.1f}" if warehouse['months_of_stock'] < 99 else "999+",
                    'Стоимость заказа': f"{warehouse['order_cost']:,.0f}" if has_prices else "Нет"
                })
    
    if warning_items:
        warning_df = pd.DataFrame(warning_items)
        st.dataframe(warning_df, use_container_width=True)
        st.write(f"**Товаров требующих внимания: {len(warning_items)}**")
    else:
        st.info("✅ Товаров требующих внимания не найдено")

def export_simple_results(analysis_results):
    """
    Простой экспорт результатов в Excel
    """
    
    from io import BytesIO
    
    try:
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Лист 1: Детальная таблица всех товаров
            detailed_data = []
            
            for item in analysis_results:
                for warehouse in item['warehouses']:
                    detailed_data.append({
                        'Товар': item['номенклатура'],
                        'Склад': warehouse['short_name'],
                        'Полное название склада': warehouse['full_name'],
                        'Город': warehouse['city'],
                        'Тип': warehouse['type'],
                        'Остаток': warehouse['current_stock'],
                        'MIN': warehouse['min_stock'],
                        'MAX': warehouse['max_stock'],
                        'MIN дефицит': warehouse['min_deficit'],
                        'К заказу': warehouse['order_quantity'],
                        'Статус': warehouse['status'],
                        'ADS': warehouse['ads'],
                        'Месяцев запаса': warehouse['months_of_stock'],
                        'Цена': warehouse['price'],
                        'Стоимость дефицита': warehouse.get('deficit_cost', 0),
                        'Стоимость заказа': warehouse.get('order_cost', 0),
                        'Стоимость остатка': warehouse.get('stock_value', 0)
                    })
            
            if detailed_data:
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name='Детальный анализ', index=False)
            
            # Лист 2: Только критичные товары
            critical_data = [row for row in detailed_data if row['Статус'] == 'critical']
            if critical_data:
                critical_df = pd.DataFrame(critical_data)
                critical_df.to_excel(writer, sheet_name='Критичные товары', index=False)
            
            # Лист 3: Только товары требующие внимания
            warning_data = [row for row in detailed_data if row['Статус'] == 'warning']
            if warning_data:
                warning_df = pd.DataFrame(warning_data)
                warning_df.to_excel(writer, sheet_name='Требуют внимания', index=False)
            
            # Лист 4: Сводка по складам
            warehouse_summary = {}
            for row in detailed_data:
                wh = row['Склад']
                if wh not in warehouse_summary:
                    warehouse_summary[wh] = {
                        'Склад': row['Полное название склада'],
                        'Город': row['Город'],
                        'Тип': row['Тип'],
                        'Всего товаров': 0,
                        'Критичные': 0,
                        'Внимание': 0,
                        'Норма': 0,
                        'Избыток': 0,
                        'Общая стоимость заказов': 0,
                        'Общая стоимость остатков': 0
                    }
                
                warehouse_summary[wh]['Всего товаров'] += 1
                warehouse_summary[wh]['Общая стоимость заказов'] += row['Стоимость заказа']
                warehouse_summary[wh]['Общая стоимость остатков'] += row['Стоимость остатка']
                
                if row['Статус'] == 'critical':
                    warehouse_summary[wh]['Критичные'] += 1
                elif row['Статус'] == 'warning':
                    warehouse_summary[wh]['Внимание'] += 1
                elif row['Статус'] == 'excess':
                    warehouse_summary[wh]['Избыток'] += 1
                else:
                    warehouse_summary[wh]['Норма'] += 1
            
            summary_df = pd.DataFrame(list(warehouse_summary.values()))
            summary_df.to_excel(writer, sheet_name='Сводка по складам', index=False)
        
        output.seek(0)
        
        st.download_button(
            label="💾 Скачать анализ складов",
            data=output,
            file_name=f"warehouse_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Файл готов к скачиванию!")
        
    except Exception as e:
        st.error(f"❌ Ошибка экспорта: {str(e)}")
