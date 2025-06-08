#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 МОДУЛЬ РАСЧЕТА МАКСИМАЛЬНЫХ ОСТАТКОВ

Функционал:
- Расчет MAX остатков по типам точек (хабы, склады, магазины)
- Разные показатели оборачиваемости для категорий ABC
- Совместимость с существующим сравнением остатков
- Настраиваемые параметры для каждого типа точки

Формула:
MIN = ADS × дни_минимального_запаса
MAX = ADS × дни_максимального_запаса
"""

import pandas as pd
import numpy as np
import types
from typing import Dict, Any, List

class MaxStockCalculator:
    """
    Калькулятор максимальных остатков с учетом типов точек и ABC категорий
    """
    
    def __init__(self):
        # Настройки по умолчанию для разных типов точек
        self.default_settings = {
            'хабы': {
                'A': {'min_days': 30, 'max_days': 90},
                'B': {'min_days': 20, 'max_days': 60}, 
                'C': {'min_days': 15, 'max_days': 45}
            },
            'склады': {
                'A': {'min_days': 25, 'max_days': 75},
                'B': {'min_days': 15, 'max_days': 45},
                'C': {'min_days': 10, 'max_days': 30}
            },
            'магазины': {
                'A': {'min_days': 20, 'max_days': 50},  # По требованию
                'B': {'min_days': 10, 'max_days': 25},  # По требованию
                'C': {'min_days': 10, 'max_days': 25}   # По требованию
            }
        }

    def set_custom_settings(self, point_type: str, category: str, min_days: int, max_days: int):
        """Настройка пользовательских параметров"""
        if point_type not in self.default_settings:
            self.default_settings[point_type] = {}
        
        self.default_settings[point_type][category] = {
            'min_days': min_days,
            'max_days': max_days
        }

    def get_settings_for_point_and_category(self, point_type: str, category: str) -> Dict:
        """Получить настройки для конкретного типа точки и категории"""
        if point_type in self.default_settings and category in self.default_settings[point_type]:
            return self.default_settings[point_type][category]
        else:
            return {'min_days': 15, 'max_days': 45}

    def calculate_max_stock_for_system(self, system, point_type: str = 'склады') -> Dict:
        """Рассчитать максимальные остатки для всей системы"""
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан'}
        
        try:
            # Берем данные ADS
            df = system.calculated_ads.copy()
            
            # Проверяем наличие ABC категорий
            if not hasattr(system, 'abc_data') or system.abc_data is None:
                df['abc_category'] = 'C'
            else:
                # Добавляем методы в систему
    system.calculate_max_stock = types.MethodType(calculate_max_stock, system)
    system.compare_with_max_stock = types.MethodType(compare_with_max_stock, system)
    system.set_max_stock_settings = types.MethodType(set_max_stock_settings, system)
    system.show_max_stock_settings = types.MethodType(show_max_stock_settings, system)
    
    # Устанавливаем настройки по требованиям
    system.set_max_stock_settings('магазины', 'A', 20, 50)  # 20 дней MIN, 50 дней MAX
    system.set_max_stock_settings('магазины', 'B', 10, 25)  # 10 дней MIN, 25 дней MAX
    system.set_max_stock_settings('магазины', 'C', 10, 25)  # 10 дней MIN, 25 дней MAX


# =============================================================================
# СОВМЕСТИМОСТЬ С СУЩЕСТВУЮЩИМ СРАВНЕНИЕМ
# =============================================================================

def add_max_stock_compatibility_to_comparison(system):
    """
    Добавить совместимость MAX остатков в существующее сравнение остатков
    Вызывается автоматически при наличии MAX данных
    """
    if (hasattr(system, 'stock_comparison') and system.stock_comparison is not None and
        hasattr(system, 'calculated_max_stock') and system.calculated_max_stock is not None):
        
        try:
            # Получаем существующее сравнение
            comparison = system.stock_comparison.copy()
            
            # Добавляем MAX данные
            max_stock_df = system.calculated_max_stock[['номенклатура', 'max_stock', 'abc_category']].copy()
            comparison = pd.merge(comparison, max_stock_df, on='номенклатура', how='left')
            comparison['max_stock'] = comparison['max_stock'].fillna(0)
            
            # Обновляем статус с учетом MAX
            def determine_full_status(row):
                current = row['total_current_stock']
                min_stock = row.get('min_stock_total', 0)
                max_stock = row.get('max_stock', 0)
                
                if current < min_stock:
                    return 'НЕДОСТАТОК'
                elif max_stock > 0 and current > max_stock:
                    return 'ИЗБЫТОК'
                else:
                    return row.get('status', 'НОРМА')
            
            comparison['full_status'] = comparison.apply(determine_full_status, axis=1)
            
            # Добавляем избыток
            comparison['excess'] = np.where(
                comparison['total_current_stock'] > comparison['max_stock'],
                comparison['total_current_stock'] - comparison['max_stock'],
                0
            )
            
            # Денежный избыток
            if 'last_purchase_price' in comparison.columns:
                comparison['excess_money'] = comparison['excess'] * comparison['last_purchase_price']
            
            # Обновляем сравнение в системе
            system.stock_comparison = comparison
            
            return True
            
        except Exception as e:
            return False
    
    return False


# =============================================================================
# ЭКСПОРТ И ОТЧЕТЫ
# =============================================================================

def create_max_stock_excel_export(system):
    """Создать Excel экспорт с данными максимальных остатков"""
    if not hasattr(system, 'calculated_max_stock') or system.calculated_max_stock is None:
        return None
    
    try:
        import io
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Лист 1: Максимальные остатки
            max_stock_export = system.calculated_max_stock.copy()
            max_stock_export.to_excel(writer, sheet_name='Максимальные_остатки', index=False)
            
            # Лист 2: Сравнение (если есть)
            if hasattr(system, 'max_stock_comparison') and system.max_stock_comparison is not None:
                comparison_export = system.max_stock_comparison.copy()
                comparison_export.to_excel(writer, sheet_name='Сравнение_MIN_MAX', index=False)
                
                # Лист 3: Только товары с недостатком
                shortage_items = comparison_export[comparison_export['stock_status'] == 'НЕДОСТАТОК']
                if not shortage_items.empty:
                    shortage_items.to_excel(writer, sheet_name='Товары_с_недостатком', index=False)
                
                # Лист 4: Только товары с избытком
                excess_items = comparison_export[comparison_export['stock_status'] == 'ИЗБЫТОК']
                if not excess_items.empty:
                    excess_items.to_excel(writer, sheet_name='Товары_с_избытком', index=False)
            
            # Лист 5: Сводка по категориям
            if hasattr(system.max_stock_calculator, 'default_settings'):
                summary_data = []
                
                for point_type, categories in system.max_stock_calculator.default_settings.items():
                    for category, settings in categories.items():
                        summary_data.append({
                            'Тип_точки': point_type,
                            'ABC_категория': category,
                            'MIN_дни': settings['min_days'],
                            'MAX_дни': settings['max_days'],
                            'Пример_ADS_5_MIN': 5 * settings['min_days'],
                            'Пример_ADS_5_MAX': 5 * settings['max_days']
                        })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Настройки_параметров', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        return None


# =============================================================================
# ИНТЕГРАЦИЯ В СУЩЕСТВУЮЩИЕ МЕТОДЫ
# =============================================================================

def integrate_max_stock_into_existing_comparison(system):
    """
    Интегрировать MAX остатки в существующий метод compare_stock_vs_min
    """
    if hasattr(system, 'compare_stock_vs_min'):
        original_method = system.compare_stock_vs_min
        
        def enhanced_compare_stock_vs_min(self):
            """Улучшенное сравнение с поддержкой MAX остатков"""
            # Вызываем оригинальный метод
            result = original_method()
            
            # Добавляем совместимость с MAX остатками
            add_max_stock_compatibility_to_comparison(self)
            
            return result
        
        # Заменяем метод на улучшенную версию
        system.compare_stock_vs_min = types.MethodType(enhanced_compare_stock_vs_min, system)


def complete_max_stock_integration(system):
    """
    Полная интеграция всех функций MAX остатков
    """
    # Добавляем основные методы
    add_max_stock_methods_to_system(system)
    
    # Интегрируем в существующие методы
    integrate_max_stock_into_existing_comparison(system)
    
    # Добавляем метод экспорта
    def create_max_stock_export(self):
        """Метод экспорта MAX остатков"""
        return create_max_stock_excel_export(self)
    
    system.create_max_stock_export = types.MethodType(create_max_stock_export, system)
    
    # Устанавливаем флаг интеграции
    system._max_stock_integrated = Trueем ABC категории
                abc_df = system.abc_data[['номенклатура', 'abc_category']].copy()
                df = pd.merge(df, abc_df, on='номенклатура', how='left')
                df['abc_category'] = df['abc_category'].fillna('C')
            
            # Рассчитываем MIN и MAX для каждого товара
            max_stock_data = []
            
            for _, row in df.iterrows():
                nomenclature = row['номенклатура']
                ads = row['ads']
                category = row.get('abc_category', 'C')
                
                # Получаем настройки для данной категории и типа точки
                settings = self.get_settings_for_point_and_category(point_type, category)
                
                # Рассчитываем MIN и MAX
                min_stock = ads * settings['min_days']
                max_stock = ads * settings['max_days']
                
                max_stock_data.append({
                    'номенклатура': nomenclature,
                    'ads': ads,
                    'abc_category': category,
                    'point_type': point_type,
                    'min_days': settings['min_days'],
                    'max_days': settings['max_days'],
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'stock_range': max_stock - min_stock,
                    'last_purchase_price': row.get('last_purchase_price', 0)
                })
            
            # Создаем DataFrame с результатами
            max_stock_df = pd.DataFrame(max_stock_data)
            
            # Добавляем денежные расчеты если есть цены
            if 'last_purchase_price' in max_stock_df.columns:
                max_stock_df['min_stock_money'] = max_stock_df['min_stock'] * max_stock_df['last_purchase_price']
                max_stock_df['max_stock_money'] = max_stock_df['max_stock'] * max_stock_df['last_purchase_price']
                max_stock_df['stock_range_money'] = max_stock_df['stock_range'] * max_stock_df['last_purchase_price']
            
            # Сохраняем в системе
            system.calculated_max_stock = max_stock_df
            
            # Статистика по категориям
            category_stats = max_stock_df.groupby('abc_category').agg({
                'min_stock': 'sum',
                'max_stock': 'sum',
                'stock_range': 'sum',
                'номенклатура': 'count'
            }).rename(columns={'номенклатура': 'товаров'})
            
            total_min = max_stock_df['min_stock'].sum()
            total_max = max_stock_df['max_stock'].sum()
            total_range = max_stock_df['stock_range'].sum()
            
            # Денежная статистика
            money_stats = {}
            if 'min_stock_money' in max_stock_df.columns:
                total_min_money = max_stock_df['min_stock_money'].sum()
                total_max_money = max_stock_df['max_stock_money'].sum()
                
                money_stats = {
                    'total_min_stock_money': total_min_money,
                    'total_max_stock_money': total_max_money,
                    'items_with_price': len(max_stock_df[max_stock_df['last_purchase_price'] > 0])
                }
            
            return {
                'success': True,
                'total_items': len(max_stock_df),
                'point_type': point_type,
                'total_min_stock': total_min,
                'total_max_stock': total_max,
                'total_stock_range': total_range,
                'category_stats': category_stats.to_dict('index'),
                'money_stats': money_stats,
                'settings_used': self.default_settings[point_type] if point_type in self.default_settings else {}
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка: {str(e)}"}

    def compare_current_vs_max_stock(self, system) -> Dict:
        """Сравнить текущие остатки с минимальными и максимальными"""
        if not hasattr(system, 'calculated_max_stock') or system.calculated_max_stock is None:
            return {'success': False, 'error': 'Максимальные остатки не рассчитаны'}
        
        if not hasattr(system, 'stock_data') or system.stock_data is None:
            return {'success': False, 'error': 'Текущие остатки не загружены'}
        
        try:
            # Данные для сравнения
            max_stock_df = system.calculated_max_stock.copy()
            current_stock_df = system.stock_data[['номенклатура', 'total_current_stock']].copy()
            
            # Объединяем данные
            comparison = pd.merge(max_stock_df, current_stock_df, on='номенклатура', how='left')
            comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
            
            # Определяем статус запасов
            def determine_stock_status(row):
                current = row['total_current_stock']
                min_stock = row['min_stock']
                max_stock = row['max_stock']
                
                if current < min_stock:
                    return 'НЕДОСТАТОК'
                elif current > max_stock:
                    return 'ИЗБЫТОК'
                else:
                    return 'НОРМА'
            
            comparison['stock_status'] = comparison.apply(determine_stock_status, axis=1)
            
            # Рассчитываем отклонения
            comparison['shortage'] = np.where(
                comparison['total_current_stock'] < comparison['min_stock'],
                comparison['min_stock'] - comparison['total_current_stock'],
                0
            )
            
            comparison['excess'] = np.where(
                comparison['total_current_stock'] > comparison['max_stock'],
                comparison['total_current_stock'] - comparison['max_stock'],
                0
            )
            
            # Денежные расчеты
            if 'last_purchase_price' in comparison.columns:
                comparison['shortage_money'] = comparison['shortage'] * comparison['last_purchase_price']
                comparison['excess_money'] = comparison['excess'] * comparison['last_purchase_price']
            
            # Сохраняем результат для совместимости
            system.max_stock_comparison = comparison
            
            # Статистика
            total_items = len(comparison)
            shortage_items = len(comparison[comparison['stock_status'] == 'НЕДОСТАТОК'])
            excess_items = len(comparison[comparison['stock_status'] == 'ИЗБЫТОК'])
            normal_items = len(comparison[comparison['stock_status'] == 'НОРМА'])
            
            total_shortage = comparison['shortage'].sum()
            total_excess = comparison['excess'].sum()
            
            result = {
                'success': True,
                'total_items': total_items,
                'shortage_items': shortage_items,
                'excess_items': excess_items,
                'normal_items': normal_items,
                'total_shortage': total_shortage,
                'total_excess': total_excess,
                'shortage_percentage': shortage_items/total_items*100,
                'excess_percentage': excess_items/total_items*100,
                'normal_percentage': normal_items/total_items*100
            }
            
            # Денежная статистика
            if 'shortage_money' in comparison.columns:
                total_shortage_money = comparison['shortage_money'].sum()
                total_excess_money = comparison['excess_money'].sum()
                
                result['money_stats'] = {
                    'total_shortage_money': total_shortage_money,
                    'total_excess_money': total_excess_money
                }
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка: {str(e)}"}

    def show_settings_summary(self):
        """Показать текущие настройки калькулятора"""
        print("\n" + "="*60)
        print("📋 ТЕКУЩИЕ НАСТРОЙКИ МАКСИМАЛЬНЫХ ОСТАТКОВ")
        print("="*60)
        
        for point_type, categories in self.default_settings.items():
            print(f"\n🏪 {point_type.upper()}:")
            for category, settings in categories.items():
                print(f"   📦 Категория {category}: MIN={settings['min_days']}д, MAX={settings['max_days']}д")
        
        print("\n" + "="*60)


# =============================================================================
# ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
# =============================================================================

def add_max_stock_methods_to_system(system):
    """Добавить методы расчета максимальных остатков в основную систему"""
    
    # Создаем калькулятор
    system.max_stock_calculator = MaxStockCalculator()
    
    def calculate_max_stock(self, point_type: str = 'склады') -> Dict:
        """Метод для расчета максимальных остатков"""
        return self.max_stock_calculator.calculate_max_stock_for_system(self, point_type)
    
    def compare_with_max_stock(self) -> Dict:
        """Метод для сравнения с максимальными остатками"""
        return self.max_stock_calculator.compare_current_vs_max_stock(self)
    
    def set_max_stock_settings(self, point_type: str, category: str, min_days: int, max_days: int):
        """Метод для настройки параметров максимальных остатков"""
        self.max_stock_calculator.set_custom_settings(point_type, category, min_days, max_days)
    
    def show_max_stock_settings(self):
        """Метод для показа настроек"""
        self.max_stock_calculator.show_settings_summary()
    
    # Добавля#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 МОДУЛЬ РАСЧЕТА МАКСИМАЛЬНЫХ ОСТАТКОВ

Функционал:
- Расчет MAX остатков по типам точек (хабы, склады, магазины)
- Разные показатели оборачиваемости для категорий ABC
- Настраиваемые параметры для каждого типа точки

Формула:
MIN = ADS × дни_минимального_запаса
MAX = ADS × дни_максимального_запаса

Пример:
Если ADS = 5, минимум на 10 дней → MIN = 50
Если ADS = 5, максимум на 50 дней → MAX = 250
"""

import pandas as pd
import numpy as np
import types
from typing import Dict, Any, List

class MaxStockCalculator:
    """
    Калькулятор максимальных остатков с учетом типов точек и ABC категорий
    """
    
    def __init__(self):
        # Настройки по умолчанию для разных типов точек
        self.default_settings = {
            'хабы': {
                'A': {'min_days': 30, 'max_days': 90},
                'B': {'min_days': 20, 'max_days': 60}, 
                'C': {'min_days': 15, 'max_days': 45}
            },
            'склады': {
                'A': {'min_days': 25, 'max_days': 75},
                'B': {'min_days': 15, 'max_days': 45},
                'C': {'min_days': 10, 'max_days': 30}
            },
            'магазины': {
                'A': {'min_days': 20, 'max_days': 50},  # По вашему требованию
                'B': {'min_days': 10, 'max_days': 25},  # По вашему требованию
                'C': {'min_days': 10, 'max_days': 25}   # По вашему требованию
            }
        }
        
        print("📦 Калькулятор максимальных остатков инициализирован")
        print("🏪 Поддерживаемые типы точек: хабы, склады, магазины")
        print("🔤 Поддерживаемые ABC категории: A, B, C")

    def set_custom_settings(self, point_type: str, category: str, min_days: int, max_days: int):
        """
        Настройка пользовательских параметров для типа точки и категории
        
        Args:
            point_type: тип точки (хабы, склады, магазины)
            category: ABC категория (A, B, C)
            min_days: дни для минимального запаса
            max_days: дни для максимального запаса
        """
        if point_type not in self.default_settings:
            self.default_settings[point_type] = {}
        
        self.default_settings[point_type][category] = {
            'min_days': min_days,
            'max_days': max_days
        }
        
        print(f"✅ Настройки обновлены: {point_type} / {category} = MIN:{min_days}д, MAX:{max_days}д")

    def get_settings_for_point_and_category(self, point_type: str, category: str) -> Dict:
        """
        Получить настройки для конкретного типа точки и категории
        """
        if point_type in self.default_settings and category in self.default_settings[point_type]:
            return self.default_settings[point_type][category]
        else:
            # Возвращаем настройки по умолчанию
            return {'min_days': 15, 'max_days': 45}

    def calculate_max_stock_for_system(self, system, point_type: str = 'склады') -> Dict:
        """
        Рассчитать максимальные остатки для всей системы
        
        Args:
            system: система с рассчитанными ADS и ABC данными
            point_type: тип точки для расчета (хабы, склады, магазины)
        
        Returns:
            Dict с результатами расчета
        """
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан'}
        
        try:
            print(f"📦 Расчет максимальных остатков для типа точек: {point_type}")
            
            # Берем данные ADS
            df = system.calculated_ads.copy()
            
            # Проверяем наличие ABC категорий
            if not hasattr(system, 'abc_data') or system.abc_data is None:
                print("⚠️ ABC анализ не выполнен, присваиваем категорию C всем товарам")
                df['abc_category'] = 'C'
            else:
                # Добавляем ABC категории
                abc_df = system.abc_data[['номенклатура', 'abc_category']].copy()
                df = pd.merge(df, abc_df, on='номенклатура', how='left')
                df['abc_category'] = df['abc_category'].fillna('C')
            
            # Рассчитываем MIN и MAX для каждого товара
            max_stock_data = []
            
            for _, row in df.iterrows():
                nomenclature = row['номенклатура']
                ads = row['ads']
                category = row.get('abc_category', 'C')
                
                # Получаем настройки для данной категории и типа точки
                settings = self.get_settings_for_point_and_category(point_type, category)
                
                # Рассчитываем MIN и MAX
                min_stock = ads * settings['min_days']
                max_stock = ads * settings['max_days']
                
                max_stock_data.append({
                    'номенклатура': nomenclature,
                    'ads': ads,
                    'abc_category': category,
                    'point_type': point_type,
                    'min_days': settings['min_days'],
                    'max_days': settings['max_days'],
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'stock_range': max_stock - min_stock,
                    'last_purchase_price': row.get('last_purchase_price', 0)
                })
            
            # Создаем DataFrame с результатами
            max_stock_df = pd.DataFrame(max_stock_data)
            
            # Добавляем денежные расчеты если есть цены
            if 'last_purchase_price' in max_stock_df.columns:
                max_stock_df['min_stock_money'] = max_stock_df['min_stock'] * max_stock_df['last_purchase_price']
                max_stock_df['max_stock_money'] = max_stock_df['max_stock'] * max_stock_df['last_purchase_price']
                max_stock_df['stock_range_money'] = max_stock_df['stock_range'] * max_stock_df['last_purchase_price']
            
            # Сохраняем в системе
            system.calculated_max_stock = max_stock_df
            
            # Статистика по категориям
            category_stats = max_stock_df.groupby('abc_category').agg({
                'min_stock': 'sum',
                'max_stock': 'sum',
                'stock_range': 'sum',
                'номенклатура': 'count'
            }).rename(columns={'номенклатура': 'товаров'})
            
            total_min = max_stock_df['min_stock'].sum()
            total_max = max_stock_df['max_stock'].sum()
            total_range = max_stock_df['stock_range'].sum()
            
            print(f"✅ Максимальные остатки рассчитаны для {len(max_stock_df)} товаров")
            print(f"📊 Общие показатели:")
            print(f"   MIN запасы: {total_min:,.0f} шт")
            print(f"   MAX запасы: {total_max:,.0f} шт")
            print(f"   Диапазон: {total_range:,.0f} шт")
            
            print(f"\n📋 По категориям:")
            for cat in ['A', 'B', 'C']:
                if cat in category_stats.index:
                    stats = category_stats.loc[cat]
                    print(f"   {cat}: {stats['товаров']} товаров, MIN:{stats['min_stock']:,.0f}, MAX:{stats['max_stock']:,.0f}")
            
            # Денежная статистика
            money_stats = {}
            if 'min_stock_money' in max_stock_df.columns:
                total_min_money = max_stock_df['min_stock_money'].sum()
                total_max_money = max_stock_df['max_stock_money'].sum()
                
                money_stats = {
                    'total_min_stock_money': total_min_money,
                    'total_max_stock_money': total_max_money,
                    'items_with_price': len(max_stock_df[max_stock_df['last_purchase_price'] > 0])
                }
                
                print(f"\n💰 Денежные показатели:")
                print(f"   MIN запасы: {total_min_money:,.2f} ₽")
                print(f"   MAX запасы: {total_max_money:,.2f} ₽")
            
            return {
                'success': True,
                'total_items': len(max_stock_df),
                'point_type': point_type,
                'total_min_stock': total_min,
                'total_max_stock': total_max,
                'total_stock_range': total_range,
                'category_stats': category_stats.to_dict('index'),
                'money_stats': money_stats,
                'settings_used': self.default_settings[point_type] if point_type in self.default_settings else {}
            }
            
        except Exception as e:
            print(f"❌ Ошибка расчета максимальных остатков: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка: {str(e)}"}

    def compare_current_vs_max_stock(self, system) -> Dict:
        """
        Сравнить текущие остатки с минимальными и максимальными
        """
        if not hasattr(system, 'calculated_max_stock') or system.calculated_max_stock is None:
            return {'success': False, 'error': 'Максимальные остатки не рассчитаны'}
        
        if not hasattr(system, 'stock_data') or system.stock_data is None:
            return {'success': False, 'error': 'Текущие остатки не загружены'}
        
        try:
            print("📊 Сравнение текущих остатков с MIN и MAX...")
            
            # Данные для сравнения
            max_stock_df = system.calculated_max_stock.copy()
            current_stock_df = system.stock_data[['номенклатура', 'total_current_stock']].copy()
            
            # Объединяем данные
            comparison = pd.merge(max_stock_df, current_stock_df, on='номенклатура', how='left')
            comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
            
            # Определяем статус запасов
            def determine_stock_status(row):
                current = row['total_current_stock']
                min_stock = row['min_stock']
                max_stock = row['max_stock']
                
                if current < min_stock:
                    return 'НЕДОСТАТОК'
                elif current > max_stock:
                    return 'ИЗБЫТОК'
                else:
                    return 'НОРМА'
            
            comparison['stock_status'] = comparison.apply(determine_stock_status, axis=1)
            
            # Рассчитываем отклонения
            comparison['shortage'] = np.where(
                comparison['total_current_stock'] < comparison['min_stock'],
                comparison['min_stock'] - comparison['total_current_stock'],
                0
            )
            
            comparison['excess'] = np.where(
                comparison['total_current_stock'] > comparison['max_stock'],
                comparison['total_current_stock'] - comparison['max_stock'],
                0
            )
            
            # Денежные расчеты
            if 'last_purchase_price' in comparison.columns:
                comparison['shortage_money'] = comparison['shortage'] * comparison['last_purchase_price']
                comparison['excess_money'] = comparison['excess'] * comparison['last_purchase_price']
            
            # Сохраняем результат
            system.max_stock_comparison = comparison
            
            # Статистика
            total_items = len(comparison)
            shortage_items = len(comparison[comparison['stock_status'] == 'НЕДОСТАТОК'])
            excess_items = len(comparison[comparison['stock_status'] == 'ИЗБЫТОК'])
            normal_items = len(comparison[comparison['stock_status'] == 'НОРМА'])
            
            total_shortage = comparison['shortage'].sum()
            total_excess = comparison['excess'].sum()
            
            print(f"📊 Результаты сравнения:")
            print(f"   Всего товаров: {total_items}")
            print(f"   Недостаток: {shortage_items} товаров ({shortage_items/total_items*100:.1f}%)")
            print(f"   Избыток: {excess_items} товаров ({excess_items/total_items*100:.1f}%)")
            print(f"   Норма: {normal_items} товаров ({normal_items/total_items*100:.1f}%)")
            print(f"   Общий недостаток: {total_shortage:,.0f} шт")
            print(f"   Общий избыток: {total_excess:,.0f} шт")
            
            result = {
                'success': True,
                'total_items': total_items,
                'shortage_items': shortage_items,
                'excess_items': excess_items,
                'normal_items': normal_items,
                'total_shortage': total_shortage,
                'total_excess': total_excess,
                'shortage_percentage': shortage_items/total_items*100,
                'excess_percentage': excess_items/total_items*100,
                'normal_percentage': normal_items/total_items*100
            }
            
            # Денежная статистика
            if 'shortage_money' in comparison.columns:
                total_shortage_money = comparison['shortage_money'].sum()
                total_excess_money = comparison['excess_money'].sum()
                
                result['money_stats'] = {
                    'total_shortage_money': total_shortage_money,
                    'total_excess_money': total_excess_money
                }
                
                print(f"💰 Денежные показатели:")
                print(f"   Недостаток: {total_shortage_money:,.2f} ₽")
                print(f"   Избыток: {total_excess_money:,.2f} ₽")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка сравнения: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка: {str(e)}"}

    def show_settings_summary(self):
        """
        Показать текущие настройки калькулятора
        """
        print("\n" + "="*60)
        print("📋 ТЕКУЩИЕ НАСТРОЙКИ МАКСИМАЛЬНЫХ ОСТАТКОВ")
        print("="*60)
        
        for point_type, categories in self.default_settings.items():
            print(f"\n🏪 {point_type.upper()}:")
            for category, settings in categories.items():
                print(f"   📦 Категория {category}: MIN={settings['min_days']}д, MAX={settings['max_days']}д")
                print(f"      Пример: ADS=5 → MIN={5*settings['min_days']}, MAX={5*settings['max_days']}")
        
        print("\n" + "="*60)


# =============================================================================
# ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
# =============================================================================

def add_max_stock_methods_to_system(system):
    """
    Добавить методы расчета максимальных остатков в основную систему
    """
    print("🔧 Интеграция методов максимальных остатков в систему...")
    
    # Создаем калькулятор
    system.max_stock_calculator = MaxStockCalculator()
    
    def calculate_max_stock(self, point_type: str = 'склады') -> Dict:
        """Метод для расчета максимальных остатков"""
        return self.max_stock_calculator.calculate_max_stock_for_system(self, point_type)
    
    def compare_with_max_stock(self) -> Dict:
        """Метод для сравнения с максимальными остатками"""
        return self.max_stock_calculator.compare_current_vs_max_stock(self)
    
    def set_max_stock_settings(self, point_type: str, category: str, min_days: int, max_days: int):
        """Метод для настройки параметров максимальных остатков"""
        self.max_stock_calculator.set_custom_settings(point_type, category, min_days, max_days)
    
    def show_max_stock_settings(self):
        """Метод для показа настроек"""
        self.max_stock_calculator.show_settings_summary()
    
    # Добавляем методы в систему
    system.calculate_max_stock = types.MethodType(calculate_max_stock, system)
    system.compare_with_max_stock = types.MethodType(compare_with_max_stock, system)
    system.set_max_stock_settings = types.MethodType(set_max_stock_settings, system)
    system.show_max_stock_settings = types.MethodType(show_max_stock_settings, system)
    
    print("✅ Методы максимальных остатков добавлены в систему:")
    print("   - system.calculate_max_stock(point_type)")
    print("   - system.compare_with_max_stock()")
    print("   - system.set_max_stock_settings(point_type, category, min_days, max_days)")
    print("   - system.show_max_stock_settings()")


# =============================================================================
# ДЕМОНСТРАЦИЯ И ТЕСТИРОВАНИЕ
# =============================================================================

def demo_max_stock_calculator():
    """
    Демонстрация работы калькулятора максимальных остатков
    """
    print("🎭 ДЕМОНСТРАЦИЯ КАЛЬКУЛЯТОРА МАКСИМАЛЬНЫХ ОСТАТКОВ")
    print("=" * 70)
    
    # Создаем калькулятор
    calculator = MaxStockCalculator()
    
    # Показываем настройки по умолчанию
    calculator.show_settings_summary()
    
    # Пример настройки пользовательских параметров
    print("\n🔧 Пример настройки пользовательских параметров:")
    calculator.set_custom_settings('магазины', 'A', 20, 50)  # Ваши требования
    calculator.set_custom_settings('магазины', 'B', 10, 25)  # Ваши требования
    calculator.set_custom_settings('магазины', 'C', 10, 25)  # Ваши требования
    
    print("\n📊 Пример расчета:")
    print("Если ADS = 5:")
    
    for point_type in ['хабы', 'склады', 'магазины']:
        print(f"\n🏪 {point_type}:")
        for category in ['A', 'B', 'C']:
            settings = calculator.get_settings_for_point_and_category(point_type, category)
            min_stock = 5 * settings['min_days']
            max_stock = 5 * settings['max_days']
            print(f"   📦 {category}: MIN={min_stock}, MAX={max_stock}")


if __name__ == "__main__":
    demo_max_stock_calculator()