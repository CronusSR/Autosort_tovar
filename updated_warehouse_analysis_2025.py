#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный анализатор складов для новой структуры файлов остатков 2025
Адаптирован под файл "остатки на 08.07.2025.xlsx"
"""

import pandas as pd
import streamlit as st
import numpy as np
from typing import Dict, List, Tuple, Optional

class UpdatedWarehouseAnalyzer2025:
    """
    Обновленный анализатор для новой структуры файлов остатков 2025
    """
    
    def __init__(self):
        # ОБНОВЛЕННАЯ конфигурация складов согласно новой структуре файла
        self.warehouse_config = {
            'магазин_ШЫМКЕНТ': {
                'col': 1,
                'name': 'магазин ШЫМКЕНТ',
                'short_name': 'Шымкент',
                'city': 'Шымкент',
                'type': 'Магазин',
                'level': 3,
                'min_days': 7,
                'max_days': 21
            },
            'магазин_Алтын_Орда': {
                'col': 2,
                'name': 'магазин Алтын Орда, (нет склада) питается напрямую от главного Хаба',
                'short_name': 'Алтын Орда',
                'city': 'Алматы',
                'type': 'Магазин',
                'level': 3,
                'min_days': 5,
                'max_days': 15,
                'note': 'питается от главного Хаба'
            },
            'главный_Хаб': {
                'col': 3,
                'name': 'главный Хаб',
                'short_name': 'Главный Хаб',
                'city': 'Алматы',
                'type': 'Главный склад',
                'level': 1,
                'min_days': 30,
                'max_days': 90
            },
            'магазин_Барыс': {
                'col': 4,
                'name': 'магазин Барыс,  (нет склада) питается напрямую от главного Хаба',
                'short_name': 'Барыс',
                'city': 'Алматы',
                'type': 'Магазин',
                'level': 3,
                'min_days': 5,
                'max_days': 15,
                'note': 'питается от главного Хаба'
            },
            'Казыбаева_склад': {
                'col': 5,
                'name': 'Казыбаева (г.Алматы), склад второго уровня',
                'short_name': 'Казыбаева склад',
                'city': 'Алматы',
                'type': 'Региональный склад',
                'level': 2,
                'min_days': 15,
                'max_days': 45
            },
            'Магазин_Астана': {
                'col': 6,
                'name': 'Магазин г.Астана',
                'short_name': 'Астана магазин',
                'city': 'Астана',
                'type': 'Магазин',
                'level': 3,
                'min_days': 7,
                'max_days': 21
            },
            'Астана_склад': {
                'col': 7,
                'name': 'г.Астана, склад второго уровня',
                'short_name': 'Астана склад',
                'city': 'Астана',
                'type': 'Региональный склад',
                'level': 2,
                'min_days': 15,
                'max_days': 45
            },
            'магазин_Казыбаева': {
                'col': 8,
                'name': 'магазин Казыбаева (г.Алматы)',
                'short_name': 'Казыбаева магазин',
                'city': 'Алматы',
                'type': 'Магазин',
                'level': 3,
                'min_days': 7,
                'max_days': 21
            }
        }
        
        # Колонка с итоговыми остатками в новом файле
        self.total_stock_column = 12  # Колонка "Итого"
        
        # Строки для структуры файла
        self.warehouse_names_row = 5  # Строка 6 (индекс 5)
        self.column_headers_row = 6   # Строка 7 (индекс 6)
        self.units_row = 7           # Строка 8 (индекс 7)
        self.data_start_row = 8      # Строка 9 (индекс 8)
        
        self.warehouse_analysis = None
        self.recommendations = None
    
    def parse_remains_file_2025(self, file_data):
        """
        Парсит файл остатков новой структуры 2025:
        - Строка 6 (индекс 5) - названия складов
        - Строка 7 (индекс 6) - заголовки колонок  
        - Строка 8 (индекс 7) - единицы измерения
        - Строка 9+ (индекс 8+) - данные товаров
        """
        try:
            print(f"📊 Начало парсинга файла остатков 2025. Всего строк: {len(file_data)}")
            
            # Проверяем что файл достаточно большой
            if len(file_data) < self.data_start_row + 1:
                raise ValueError(f"Файл слишком мал. Должно быть минимум {self.data_start_row + 1} строк.")
            
            # Проверяем структуру заголовков
            if len(file_data) > self.warehouse_names_row:
                warehouse_row = file_data[self.warehouse_names_row]  # Строка 6
                print(f"📋 Строка 6 (склады): {warehouse_row[:5]}...")
            
            if len(file_data) > self.column_headers_row:
                header_row = file_data[self.column_headers_row]  # Строка 7
                print(f"📋 Строка 7 (заголовки): {header_row[:5]}...")
            
            # Читаем данные начиная с строки 9 (индекс 8)
            remains_data = []
            processed_items = 0
            
            for i in range(self.data_start_row, len(file_data)):
                row = file_data[i]
                
                # Проверяем что строка не пустая
                if not row or len(row) == 0:
                    continue
                    
                # Проверяем что первая ячейка (номенклатура) не пустая
                if not row[0] or pd.isna(row[0]):
                    continue
                    
                item_name = str(row[0]).strip()
                if not item_name or item_name.lower() in ['', 'nan', 'none', 'итого', 'всего']:
                    continue
                
                # Безопасно получаем итоговый остаток (колонка 12)
                try:
                    if len(row) > self.total_stock_column and row[self.total_stock_column] is not None:
                        total_stock = float(row[self.total_stock_column])
                    else:
                        total_stock = 0
                except (ValueError, TypeError, IndexError):
                    total_stock = 0
                
                item_data = {
                    'номенклатура': item_name,
                    'итого_остаток': total_stock
                }
                
                # Добавляем остатки по складам с использованием новой конфигурации
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
                
                # Лимит для безопасности
                if processed_items >= 10000:
                    break
            
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

    def analyze_warehouse_stock_2025(self, remains_df, ads_data=None, prices_data=None):
        """
        Анализирует остатки по складам с учетом новой структуры 2025
        """
        if remains_df is None or remains_df.empty:
            return None
        
        analysis_results = []
        
        for idx, item in remains_df.iterrows():
            item_name = item['номенклатура']
            
            # Получаем ADS для товара
            ads_value = 0
            if ads_data is not None and not ads_data.empty:
                ads_match = ads_data[ads_data['номенклатура'] == item_name]
                if not ads_match.empty:
                    ads_value = ads_match.iloc[0].get('ads', 0)
            
            # Получаем цену товара
            item_price = 0
            if prices_data is not None and not prices_data.empty:
                price_match = prices_data[prices_data['номенклатура'] == item_name]
                if not price_match.empty:
                    item_price = price_match.iloc[0].get('цена', 0)
            
            # Анализ по каждому складу с индивидуальными нормами
            warehouse_analysis = {}
            total_stock = item.get('итого_остаток', 0)
            total_order_quantity = 0
            overall_critical_count = 0
            overall_warning_count = 0
            
            for warehouse_key, config in self.warehouse_config.items():
                stock_col = f'{warehouse_key}_остаток'
                current_stock = item.get(stock_col, 0)
                
                # Индивидуальные min/max для каждого склада
                warehouse_min_days = config.get('min_days', 15)
                warehouse_max_days = config.get('max_days', 45)
                
                min_stock = ads_value * warehouse_min_days if ads_value > 0 else 0
                max_stock = ads_value * warehouse_max_days if ads_value > 0 else 0
                
                # Расчет месяцев запаса
                months_of_stock = 0
                if ads_value > 0:
                    months_of_stock = current_stock / ads_value
                elif current_stock > 0:
                    months_of_stock = 999  # Товар есть, но не продается
                
                # Определение статуса с учетом уровня склада
                status = 'Неизвестно'
                deficit = 0
                surplus = 0
                order_quantity = 0
                recommendation = ''
                
                if ads_value > 0:
                    if current_stock <= min_stock * 0.3:
                        status = 'Критично'
                        deficit = min_stock - current_stock
                        order_quantity = deficit * 1.2  # С запасом
                        recommendation = f'СРОЧНО пополнить: {order_quantity:.0f} шт'
                        overall_critical_count += 1
                    elif current_stock <= min_stock:
                        status = 'Мало'
                        deficit = min_stock - current_stock
                        order_quantity = deficit
                        recommendation = f'Пополнить: {order_quantity:.0f} шт'
                        overall_warning_count += 1
                    elif current_stock <= max_stock:
                        status = 'Норма'
                        recommendation = 'Запас в норме'
                    else:
                        status = 'Избыток'
                        surplus = current_stock - max_stock
                        recommendation = f'Избыток: {surplus:.0f} шт'
                elif current_stock > 0:
                    status = 'Нет продаж'
                    recommendation = 'Товар не продается'
                else:
                    status = 'Пустой'
                    recommendation = 'Нет остатков и продаж'
                
                # Расчет стоимости заказа
                price_to_order = order_quantity * item_price if order_quantity > 0 and item_price > 0 else 0
                total_order_quantity += order_quantity
                
                warehouse_analysis[warehouse_key] = {
                    'name': config['name'],
                    'short_name': config['short_name'],
                    'city': config['city'],
                    'type': config['type'],
                    'level': config['level'],
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'min_days': warehouse_min_days,
                    'max_days': warehouse_max_days,
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
                'total_order_quantity': total_order_quantity,
                'critical_warehouses': overall_critical_count,
                'warning_warehouses': overall_warning_count,
                'warehouses': warehouse_analysis,
                'parameters': {
                    'file_structure': '2025_new',
                    'warehouses_count': len(self.warehouse_config),
                    'data_start_row': self.data_start_row + 1,
                    'total_column': self.total_stock_column + 1
                }
            })
        
        self.warehouse_analysis = {
            'analysis': analysis_results,
            'total_items': len(analysis_results),
            'file_version': '2025_new_structure',
            'warehouse_config': self.warehouse_config
        }
        
        return self.warehouse_analysis

    def get_warehouse_recommendations_2025(self):
        """
        Генерирует рекомендации по складам для новой структуры 2025
        """
        if not self.warehouse_analysis:
            return None
        
        analysis = self.warehouse_analysis['analysis']
        warehouse_summaries = {}
        
        # Инициализация сводки для каждого склада
        for warehouse_key, config in self.warehouse_config.items():
            warehouse_summaries[warehouse_key] = {
                'name': config['name'],
                'short_name': config['short_name'],
                'city': config['city'],
                'type': config['type'],
                'level': config.get('level', 0),
                'min_days': config.get('min_days', 15),
                'max_days': config.get('max_days', 45),
                'critical_items': [],
                'warning_items': [],
                'good_items': [],
                'excess_items': [],
                'no_sales_items': [],
                'total_to_order': 0,
                'total_cost_to_order': 0,
                'item_count': 0
            }
        
        # Заполняем статистику по каждому товару
        for item_analysis in analysis:
            item_name = item_analysis['номенклатура']
            warehouses = item_analysis['warehouses']
            
            for warehouse_key, warehouse_data in warehouses.items():
                if warehouse_key in warehouse_summaries:
                    summary = warehouse_summaries[warehouse_key]
                    summary['item_count'] += 1
                    
                    status = warehouse_data['status']
                    order_quantity = warehouse_data.get('order_quantity', 0)
                    price_to_order = warehouse_data.get('price_to_order', 0)
                    
                    item_info = {
                        'номенклатура': item_name,
                        'current_stock': warehouse_data['current_stock'],
                        'order_quantity': order_quantity,
                        'price_to_order': price_to_order,
                        'months_of_stock': warehouse_data['months_of_stock'],
                        'recommendation': warehouse_data['recommendation']
                    }
                    
                    if status == 'Критично':
                        summary['critical_items'].append(item_info)
                    elif status == 'Мало':
                        summary['warning_items'].append(item_info)
                    elif status == 'Норма':
                        summary['good_items'].append(item_info)
                    elif status == 'Избыток':
                        summary['excess_items'].append(item_info)
                    elif status == 'Нет продаж':
                        summary['no_sales_items'].append(item_info)
                    
                    summary['total_to_order'] += order_quantity
                    summary['total_cost_to_order'] += price_to_order
        
        # Сортируем товары по количеству заказа
        for warehouse_key, summary in warehouse_summaries.items():
            for item_list in ['critical_items', 'warning_items']:
                summary[item_list].sort(key=lambda x: x['order_quantity'], reverse=True)
        
        self.recommendations = {
            'warehouse_summaries': warehouse_summaries,
            'overall_stats': {
                'total_warehouses': len(warehouse_summaries),
                'total_items_analyzed': len(analysis),
                'file_structure': '2025_new',
                'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        return self.recommendations

    def get_warehouse_hierarchy_2025(self):
        """
        Возвращает иерархию складов для новой структуры 2025
        """
        hierarchy = {
            'level_1_main': [],
            'level_2_regional': [],
            'level_3_stores': []
        }
        
        for warehouse_key, config in self.warehouse_config.items():
            warehouse_info = {
                'key': warehouse_key,
                'name': config['name'],
                'short_name': config['short_name'],
                'city': config['city'],
                'type': config['type'],
                'min_days': config['min_days'],
                'max_days': config['max_days'],
                'column': config['col']
            }
            
            level = config.get('level', 3)
            if level == 1:
                hierarchy['level_1_main'].append(warehouse_info)
            elif level == 2:
                hierarchy['level_2_regional'].append(warehouse_info)
            else:
                hierarchy['level_3_stores'].append(warehouse_info)
        
        return hierarchy

def apply_updated_warehouse_analysis_2025(system):
    """
    Применяет обновленный анализатор складов для файлов 2025
    """
    try:
        st.header("🔄 Применение обновленного анализатора складов 2025")
        
        # Создаем новый анализатор
        updated_analyzer = UpdatedWarehouseAnalyzer2025()
        
        # Заменяем анализатор в системе
        system.warehouse_analyzer = updated_analyzer
        
        # Обновляем методы
        system.warehouse_analyzer.parse_remains_file = updated_analyzer.parse_remains_file_2025
        system.warehouse_analyzer.analyze_warehouse_stock = updated_analyzer.analyze_warehouse_stock_2025
        system.warehouse_analyzer.get_warehouse_recommendations = updated_analyzer.get_warehouse_recommendations_2025
        
        # Добавляем новые методы
        system.get_warehouse_hierarchy = updated_analyzer.get_warehouse_hierarchy_2025
        
        # Обновляем конфигурацию
        system.warehouse_config = updated_analyzer.warehouse_config
        
        # Отмечаем что обновления применены
        system._warehouse_2025_update_applied = True
        system._warehouse_analyzer_version = "2025.01.updated"
        
        st.success("✅ Обновленный анализатор складов 2025 применен!")
        
        # Показываем информацию о новой структуре
        st.info("🔄 **Обновления:**")
        st.write("• Адаптирован под новую структуру файла остатков 2025")
        st.write("• Обновлены названия и расположение складов")
        st.write("• Исправлены индексы строк и колонок")
        st.write("• Добавлена классификация складов по уровням")
        
        with st.expander("📋 Конфигурация складов 2025"):
            hierarchy = updated_analyzer.get_warehouse_hierarchy_2025()
            
            st.subheader("🏢 Уровень 1: Главные склады")
            for warehouse in hierarchy['level_1_main']:
                st.write(f"• **{warehouse['short_name']}** ({warehouse['city']}) - колонка {warehouse['column']+1}")
            
            st.subheader("🏬 Уровень 2: Региональные склады")
            for warehouse in hierarchy['level_2_regional']:
                st.write(f"• **{warehouse['short_name']}** ({warehouse['city']}) - колонка {warehouse['column']+1}")
            
            st.subheader("🏪 Уровень 3: Магазины")
            for warehouse in hierarchy['level_3_stores']:
                st.write(f"• **{warehouse['short_name']}** ({warehouse['city']}) - колонка {warehouse['column']+1}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка применения обновленного анализатора: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Обновленный анализатор складов 2025 загружен")