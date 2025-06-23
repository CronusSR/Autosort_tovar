#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕННЫЙ анализ складов с правильным расчетом min/max запасов и интеграцией цен
Исправляет все проблемы:
1. Неправильный расчет min/max запаса (теперь индивидуальный для каждого склада)
2. Цены = 0 (теперь автоматически интегрируются из ADS)
3. Противоречивая статистика (исправлена логика суммирования)
4. Отрицательные значения в норме (добавлены проверки)

Автор: Claude Code Assistant
Дата: 2025-06-23
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class FixedWarehouseAnalyzer:
    """
    ИСПРАВЛЕННЫЙ анализатор складов с правильной логикой расчетов
    """
    
    def __init__(self):
        # ИСПРАВЛЕНО: Добавлены min_days и max_days для каждого склада согласно иерархии
        self.warehouse_config = {
            'База_Комплект': { 
                'col': 8, 
                'name': 'База Склад Фурнитура Комплект',
                'short_name': 'База Комплект',
                'min_days': 30,  # Главный хаб - больше запас
                'max_days': 90,
                'level': 1,
                'type': 'Главный хаб'
            },
            'Барыс_TRADE': { 
                'col': 9, 
                'name': 'Барыс Склад Фурнитура TRADE',
                'short_name': 'Барыс TRADE',
                'min_days': 15,  # Склад 2-го уровня
                'max_days': 45,
                'level': 2,
                'type': 'Магазин+склад'
            },
            'Казыбаева_TRADE': { 
                'col': 10, 
                'name': 'Казыбаева Склад Фурнитура TRADE',
                'short_name': 'Казыбаева TRADE',
                'min_days': 15,  # Склад 2-го уровня
                'max_days': 45,
                'level': 2,
                'type': 'Склад 2-го уровня'
            },
            'АО_TRADE': { 
                'col': 6, 
                'name': 'АО Склад Фурнитура TRADE',
                'short_name': 'АО TRADE',
                'min_days': 10,  # Специализированный - меньше запас
                'max_days': 30,
                'level': 2,
                'type': 'Специализированный'
            },
            'Шымкент_Овощная_база': { 
                'col': 3, 
                'name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'short_name': 'Шымкент Овощная',
                'min_days': 20,  # Региональный склад
                'max_days': 60,
                'level': 2,
                'type': 'Склад 2-го уровня'
            },
            'Овощная_база_Магазин': { 
                'col': 4, 
                'name': '6 Склад фурнитуры "Овощная база" Магазин',
                'short_name': 'Овощная Магазин',
                'min_days': 10,  # Магазин - минимальный запас
                'max_days': 30,
                'level': 3,
                'type': 'Магазин'
            }
        }
    
    def get_price_from_ads(self, item_name: str, ads_data: pd.DataFrame) -> float:
        """
        ИСПРАВЛЕНО: Правильное извлечение цен из ADS данных
        """
        if ads_data is None or ads_data.empty:
            return 0.0
        
        # Ищем товар в ADS данных
        price_match = ads_data[ads_data['номенклатура'] == item_name]
        
        if not price_match.empty:
            # Приоритетный список колонок с ценами
            price_columns = [
                'last_purchase_price',    # Из integration_patch.py
                'цена',                   # Стандартная колонка
                'price',
                'закупочная_цена',
                'стоимость'
            ]
            
            for col in price_columns:
                if col in price_match.columns:
                    price_value = price_match.iloc[0][col]
                    if pd.notna(price_value) and price_value > 0:
                        return float(price_value)
        
        return 0.0
    
    def analyze_warehouse_stock_fixed(self, remains_df: pd.DataFrame, ads_data: pd.DataFrame) -> Dict:
        """
        ИСПРАВЛЕННЫЙ анализ остатков по складам с правильным расчетом min/max запасов
        """
        if remains_df is None or remains_df.empty:
            st.error("❌ Нет данных остатков для анализа")
            return None
        
        if ads_data is None or ads_data.empty:
            st.warning("⚠️ Нет ADS данных, анализ будет выполнен без норм запаса")
        
        st.info("🔄 Выполняю исправленный анализ складов...")
        
        analysis_results = []
        price_stats = {'found': 0, 'missing': 0, 'total_value': 0}
        
        for idx, item in remains_df.iterrows():
            item_name = item['номенклатура']
            
            # ИСПРАВЛЕНО: Получаем ADS и цену для товара
            ads_value = 0
            item_price = 0
            
            if ads_data is not None and not ads_data.empty:
                ads_match = ads_data[ads_data['номенклатура'] == item_name]
                if not ads_match.empty:
                    ads_value = ads_match.iloc[0].get('ads', 0)
                    item_price = self.get_price_from_ads(item_name, ads_data)
                    
                    if item_price > 0:
                        price_stats['found'] += 1
                        price_stats['total_value'] += item_price
                    else:
                        price_stats['missing'] += 1
            
            # Анализ по каждому складу с ИНДИВИДУАЛЬНЫМИ нормами
            warehouse_analysis = {}
            total_stock = item.get('итого_остаток', 0)
            
            for warehouse_key, config in self.warehouse_config.items():
                stock_col = f'{warehouse_key}_остаток'
                current_stock = item.get(stock_col, 0)
                
                # ИСПРАВЛЕНО: Индивидуальные min/max для каждого склада
                warehouse_min_days = config.get('min_days', 15)
                warehouse_max_days = config.get('max_days', 45)
                
                min_stock = ads_value * warehouse_min_days if ads_value > 0 else 0
                max_stock = ads_value * warehouse_max_days if ads_value > 0 else 0
                
                # ИСПРАВЛЕНО: Правильный расчет месяцев запаса
                months_of_stock = 0
                if ads_value > 0:
                    months_of_stock = current_stock / ads_value
                elif current_stock > 0:
                    months_of_stock = 999  # Бесконечность при отсутствии продаж
                
                # ИСПРАВЛЕНО: Правильные расчеты дефицита и избытка
                deficit = max(0, min_stock - current_stock)
                surplus = max(0, current_stock - max_stock)
                
                # ИСПРАВЛЕНО: Корректная логика определения статуса
                status = 'good'
                order_quantity = 0
                price_to_order = 0
                recommendation = ''
                
                if ads_value > 0:  # Только если есть продажи
                    if current_stock < min_stock:
                        if current_stock < min_stock * 0.5:
                            status = 'critical'
                            order_quantity = max_stock - current_stock
                            recommendation = f'КРИТИЧНО! Остаток {current_stock:.0f} < MIN {min_stock:.0f}. Заказать: {order_quantity:.0f}'
                        else:
                            status = 'warning'
                            order_quantity = min_stock - current_stock
                            recommendation = f'Предупреждение! Остаток {current_stock:.0f} < MIN {min_stock:.0f}. Заказать: {order_quantity:.0f}'
                    elif current_stock > max_stock:
                        status = 'excess'
                        recommendation = f'Избыток! Остаток {current_stock:.0f} > MAX {max_stock:.0f}. Избыток: {surplus:.0f}'
                    else:
                        status = 'good'
                        recommendation = f'В норме. Остаток {current_stock:.0f} между MIN {min_stock:.0f} и MAX {max_stock:.0f}'
                else:
                    # ИСПРАВЛЕНО: Обработка товаров без продаж
                    if current_stock > 0:
                        status = 'no_sales'
                        recommendation = f'Нет продаж, остаток {current_stock:.0f}'
                    else:
                        status = 'empty'
                        recommendation = 'Пустой остаток, нет продаж'
                
                # ИСПРАВЛЕНО: Правильный расчет стоимости заказа
                if order_quantity > 0 and item_price > 0:
                    price_to_order = order_quantity * item_price
                
                warehouse_analysis[warehouse_key] = {
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'months_of_stock': months_of_stock,
                    'deficit': deficit,
                    'surplus': surplus,
                    'status': status,
                    'order_quantity': order_quantity,
                    'price_to_order': price_to_order,
                    'recommendation': recommendation,
                    'warehouse_config': config
                }
            
            analysis_results.append({
                'номенклатура': item_name,
                'ads': ads_value,
                'price': item_price,
                'total_stock': total_stock,
                'warehouses': warehouse_analysis
            })
            
            # Показываем прогресс
            if (idx + 1) % 100 == 0:
                st.write(f"Обработано {idx + 1} товаров...")
        
        # ИСПРАВЛЕНО: Правильная статистика
        total_items = len(analysis_results)
        items_with_ads = sum(1 for item in analysis_results if item['ads'] > 0)
        items_with_prices = price_stats['found']
        
        st.success(f"✅ Анализ завершен: {total_items} товаров, {items_with_ads} с ADS, {items_with_prices} с ценами")
        
        return {
            'analysis': analysis_results,
            'stats': {
                'total_items': total_items,
                'items_with_ads': items_with_ads,
                'items_with_prices': items_with_prices,
                'avg_price': price_stats['total_value'] / max(1, items_with_prices),
                'price_coverage': (items_with_prices / max(1, total_items)) * 100
            }
        }
    
    def create_fixed_summary(self, analysis_results: Dict) -> Dict:
        """
        ИСПРАВЛЕННАЯ сводка с правильными расчетами
        """
        if not analysis_results or 'analysis' not in analysis_results:
            return {}
        
        analysis = analysis_results['analysis']
        warehouse_summaries = {}
        
        # ИСПРАВЛЕНО: Инициализация сводки для каждого склада
        for warehouse_key, config in self.warehouse_config.items():
            warehouse_summaries[warehouse_key] = {
                'name': config['name'],
                'short_name': config['short_name'],
                'level': config.get('level', 0),
                'type': config.get('type', 'Склад'),
                'critical_items': [],
                'warning_items': [],
                'good_items': [],
                'excess_items': [],
                'no_sales_items': [],
                'total_to_order': 0,
                'total_cost_to_order': 0,
                'item_count': 0
            }
        
        # ИСПРАВЛЕНО: Правильный подсчет по каждому товару и складу
        for item in analysis:
            for warehouse_key, warehouse_data in item['warehouses'].items():
                if warehouse_key not in warehouse_summaries:
                    continue
                
                summary = warehouse_summaries[warehouse_key]
                summary['item_count'] += 1
                
                status = warehouse_data['status']
                order_qty = warehouse_data.get('order_quantity', 0)
                order_cost = warehouse_data.get('price_to_order', 0)
                
                # ИСПРАВЛЕНО: Правильная категоризация
                item_info = {
                    'номенклатура': item['номенклатура'],
                    'current_stock': warehouse_data['current_stock'],
                    'min_stock': warehouse_data['min_stock'],
                    'max_stock': warehouse_data['max_stock'],
                    'order_quantity': order_qty,
                    'price_to_order': order_cost,
                    'recommendation': warehouse_data['recommendation']
                }
                
                if status == 'critical':
                    summary['critical_items'].append(item_info)
                elif status == 'warning':
                    summary['warning_items'].append(item_info)
                elif status == 'excess':
                    summary['excess_items'].append(item_info)
                elif status == 'good':
                    summary['good_items'].append(item_info)
                elif status in ['no_sales', 'empty']:
                    summary['no_sales_items'].append(item_info)
                
                # ИСПРАВЛЕНО: Суммируем только реальные заказы
                if order_qty > 0:
                    summary['total_to_order'] += order_qty
                    summary['total_cost_to_order'] += order_cost
        
        # ИСПРАВЛЕНО: Общая статистика
        total_summary = {
            'total_warehouses': len(warehouse_summaries),
            'total_items_to_order': 0,
            'total_quantity_to_order': 0,
            'total_cost_to_order': 0,
            'critical_count': 0,
            'warning_count': 0,
            'good_count': 0,
            'excess_count': 0
        }
        
        for summary in warehouse_summaries.values():
            total_summary['total_items_to_order'] += len(summary['critical_items']) + len(summary['warning_items'])
            total_summary['total_quantity_to_order'] += summary['total_to_order']
            total_summary['total_cost_to_order'] += summary['total_cost_to_order']
            total_summary['critical_count'] += len(summary['critical_items'])
            total_summary['warning_count'] += len(summary['warning_items'])
            total_summary['good_count'] += len(summary['good_items'])
            total_summary['excess_count'] += len(summary['excess_items'])
        
        return {
            'warehouses': warehouse_summaries,
            'total': total_summary
        }

def show_fixed_warehouse_analysis(system):
    """
    ИСПРАВЛЕННАЯ страница анализа складов
    """
    st.header("🔧 ИСПРАВЛЕННЫЙ анализ складов")
    st.caption("✨ Правильный расчет min/max запасов, интеграция цен из ADS, корректная статистика")
    
    # Проверяем данные
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS в разделе 'ADS расчет'")
        return
    
    if not hasattr(system, 'multiple_files_data') or not system.multiple_files_data:
        st.warning("⚠️ Для получения цен загрузите ADS файлы в разделе 'Множественный анализ'")
    
    # Загрузка файла остатков
    st.subheader("📁 Загрузка файла остатков")
    remains_file = st.file_uploader("Загрузите файл остатков (Excel):", type=['xlsx', 'xls'])
    
    if remains_file is not None:
        try:
            remains_df = pd.read_excel(remains_file)
            st.success(f"✅ Загружен файл остатков: {len(remains_df)} строк")
            
            # Показываем структуру
            with st.expander("📊 Структура файла остатков"):
                st.write("**Колонки:**")
                for i, col in enumerate(remains_df.columns):
                    st.write(f"{i+1:2d}. {col}")
            
            # Создаем исправленный анализатор
            analyzer = FixedWarehouseAnalyzer()
            
            if st.button("🚀 Запустить ИСПРАВЛЕННЫЙ анализ", type="primary"):
                with st.spinner("🔄 Выполняю исправленный анализ..."):
                    
                    # Получаем ADS данные с ценами
                    ads_with_prices = system.calculated_ads
                    
                    # Пытаемся получить цены из новой системы
                    try:
                        from simple_price_add import get_prices_for_warehouse_analysis
                        prices = get_prices_for_warehouse_analysis(system)
                        if prices:
                            # Добавляем цены в ADS данные
                            for idx, row in ads_with_prices.iterrows():
                                item_name = row['номенклатура']
                                if item_name in prices:
                                    ads_with_prices.at[idx, 'last_purchase_price'] = prices[item_name]
                            st.success(f"✅ Интегрировано {len(prices)} цен из новой системы")
                    except Exception as e:
                        st.warning(f"⚠️ Не удалось получить цены из новой системы: {e}")
                    
                    # Выполняем исправленный анализ
                    analysis_result = analyzer.analyze_warehouse_stock_fixed(remains_df, ads_with_prices)
                    
                    if analysis_result:
                        # Создаем исправленную сводку
                        summary = analyzer.create_fixed_summary(analysis_result)
                        
                        # Показываем результаты
                        st.markdown("---")
                        st.subheader("📊 ИСПРАВЛЕННЫЕ результаты анализа")
                        
                        # Общая статистика
                        if 'total' in summary:
                            total = summary['total']
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Товаров к заказу", total['total_items_to_order'])
                            with col2:
                                st.metric("Общее кол-во", f"{total['total_quantity_to_order']:,.0f}")
                            with col3:
                                st.metric("Стоимость заказа", f"{total['total_cost_to_order']:,.0f} ₸")
                            with col4:
                                st.metric("Критичных", total['critical_count'])
                        
                        # Детали по складам
                        st.subheader("🏪 Детали по складам")
                        
                        if 'warehouses' in summary:
                            for warehouse_key, warehouse_summary in summary['warehouses'].items():
                                with st.expander(f"📦 {warehouse_summary['name']} ({warehouse_summary['type']})"):
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Критичных", len(warehouse_summary['critical_items']))
                                    with col2:
                                        st.metric("К заказу", f"{warehouse_summary['total_to_order']:,.0f}")
                                    with col3:
                                        st.metric("Стоимость", f"{warehouse_summary['total_cost_to_order']:,.0f} ₸")
                                    
                                    # Показываем критичные товары
                                    if warehouse_summary['critical_items']:
                                        st.write("🔴 **Критичные товары:**")
                                        for item in warehouse_summary['critical_items'][:10]:
                                            st.write(f"• {item['номенклатура']}: {item['current_stock']:.0f} → заказать {item['order_quantity']:.0f} ({item['price_to_order']:,.0f} ₸)")
                    
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

if __name__ == "__main__":
    st.title("🔧 ИСПРАВЛЕННЫЙ анализ складов")
    st.write("Standalone версия для тестирования исправлений")