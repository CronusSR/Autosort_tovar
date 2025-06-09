#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 МОДУЛЬ РАСЧЕТА МАКСИМАЛЬНЫХ ОСТАТКОВ - ИСПРАВЛЕННАЯ ВЕРСИЯ

Функционал:
- Расчет MAX остатков по типам точек (хабы, склады, магазины)
- Разные показатели оборачиваемости для категорий ABC
- Настраиваемые параметры для каждого типа точки
- Исправлена ошибка с названиями колонок

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
import io

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
        
        print("📦 Калькулятор максимальных остатков инициализирован (исправленная версия)")
        print("🏪 Поддерживаемые типы точек: хабы, склады, магазины")
        print("🔤 Поддерживаемые ABC категории: A, B, C")

    def show_settings_summary(self):
        """Показать все настройки калькулятора"""
        print("\n📋 Настройки калькулятора максимальных остатков:")
        print("-" * 60)
        
        for point_type, categories in self.default_settings.items():
            print(f"\n🏪 {point_type.upper()}:")
            for category, settings in categories.items():
                min_days = settings['min_days']
                max_days = settings['max_days']
                print(f"   {category}: MIN={min_days}д, MAX={max_days}д")

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

    def detect_column_names(self, df, expected_columns):
        """
        Определить правильные названия колонок в DataFrame
        
        Args:
            df: DataFrame для анализа
            expected_columns: список ожидаемых колонок
        
        Returns:
            dict: соответствие ожидаемых колонок реальным
        """
        column_mapping = {}
        
        # Общие варианты названий колонок
        name_variants = {
            'номенклатура': ['номенклатура', 'nomenclature', 'наименование', 'название', 'товар', 'продукт'],
            'abc_category': ['abc_category', 'abc', 'категория_abc', 'abc_класс', 'класс']
        }
        
        for expected_col in expected_columns:
            found = False
            
            # Ищем точное совпадение
            if expected_col in df.columns:
                column_mapping[expected_col] = expected_col
                found = True
            else:
                # Ищем по вариантам
                variants = name_variants.get(expected_col, [expected_col])
                for variant in variants:
                    # Проверяем точное совпадение и частичное (регистронезависимое)
                    matching_cols = [col for col in df.columns 
                                   if variant.lower() in col.lower() or col.lower() in variant.lower()]
                    if matching_cols:
                        column_mapping[expected_col] = matching_cols[0]
                        found = True
                        break
            
            if not found:
                print(f"⚠️ Колонка '{expected_col}' не найдена в DataFrame")
                print(f"Доступные колонки: {list(df.columns)}")
        
        return column_mapping

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
            print(f"📊 Обрабатываем {len(df)} товаров с ADS")
            print(f"Колонки в ADS: {list(df.columns)}")
            
            # Проверяем наличие ABC категорий с исправленной логикой
            if not hasattr(system, 'abc_data') or system.abc_data is None:
                print("⚠️ ABC анализ не выполнен, присваиваем категорию C всем товарам")
                df['abc_category'] = 'C'
            else:
                print("📋 Добавляем ABC категории...")
                print(f"Колонки в ABC данных: {list(system.abc_data.columns)}")
                
                # ИСПРАВЛЕНИЕ: Используем интеллектуальное определение колонок
                required_cols = ['номенклатура', 'abc_category']
                column_mapping = self.detect_column_names(system.abc_data, required_cols)
                
                if len(column_mapping) == 2:
                    # Создаем правильный DataFrame для слияния
                    abc_df = system.abc_data[[
                        column_mapping['номенклатура'], 
                        column_mapping['abc_category']
                    ]].copy()
                    
                    # Переименовываем колонки в стандартные
                    abc_df.columns = ['номенклатура', 'abc_category']
                    
                    # Убираем дубликаты и пустые значения
                    abc_df = abc_df.dropna().drop_duplicates(subset=['номенклатура'])
                    
                    print(f"✅ Найдено {len(abc_df)} товаров с ABC категориями")
                    
                    # Объединяем данные
                    df = pd.merge(df, abc_df, on='номенклатура', how='left')
                    df['abc_category'] = df['abc_category'].fillna('C')
                    
                    # Статистика по категориям
                    abc_stats = df['abc_category'].value_counts()
                    print(f"📊 Распределение по ABC: {abc_stats.to_dict()}")
                else:
                    print("⚠️ Не удалось найти нужные колонки в ABC данных, присваиваем категорию C")
                    df['abc_category'] = 'C'
            
            # Рассчитываем MIN и MAX для каждого товара
            max_stock_data = []
            
            print("🔧 Рассчитываем MIN и MAX остатки...")
            
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
            
            # Сохраняем результат сравнения
            system.max_stock_comparison = comparison
            
            # Статистика
            status_stats = comparison['stock_status'].value_counts()
            total_shortage = comparison['shortage'].sum()
            total_excess = comparison['excess'].sum()
            
            print(f"✅ Сравнение завершено для {len(comparison)} товаров")
            print(f"📊 Статистика по статусам:")
            for status, count in status_stats.items():
                print(f"   {status}: {count} товаров")
            
            print(f"\n📉 Общие показатели:")
            print(f"   Общий недостаток: {total_shortage:,.0f} шт")
            print(f"   Общий избыток: {total_excess:,.0f} шт")
            
            return {
                'success': True,
                'total_items': len(comparison),
                'status_stats': status_stats.to_dict(),
                'total_shortage': total_shortage,
                'total_excess': total_excess,
                'critical_items': len(comparison[comparison['stock_status'] == 'НЕДОСТАТОК'])
            }
            
        except Exception as e:
            print(f"❌ Ошибка сравнения: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка: {str(e)}"}

    def create_max_stock_excel_export(self, system) -> bytes:
        """
        Создать Excel отчет с максимальными остатками
        """
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Основные расчеты
                if hasattr(system, 'calculated_max_stock') and system.calculated_max_stock is not None:
                    system.calculated_max_stock.to_excel(writer, sheet_name='MAX_остатки', index=False)
                
                # Сравнение с текущими остатками
                if hasattr(system, 'max_stock_comparison') and system.max_stock_comparison is not None:
                    system.max_stock_comparison.to_excel(writer, sheet_name='Сравнение_MAX', index=False)
                
                # Товары с недостатком
                if hasattr(system, 'max_stock_comparison') and system.max_stock_comparison is not None:
                    shortage_items = system.max_stock_comparison[
                        system.max_stock_comparison['stock_status'] == 'НЕДОСТАТОК'
                    ].copy()
                    if not shortage_items.empty:
                        shortage_items = shortage_items.sort_values('shortage', ascending=False)
                        shortage_items.to_excel(writer, sheet_name='Товары_с_недостатком', index=False)
                
                # Товары с избытком
                if hasattr(system, 'max_stock_comparison') and system.max_stock_comparison is not None:
                    excess_items = system.max_stock_comparison[
                        system.max_stock_comparison['stock_status'] == 'ИЗБЫТОК'
                    ].copy()
                    if not excess_items.empty:
                        excess_items = excess_items.sort_values('excess', ascending=False)
                        excess_items.to_excel(writer, sheet_name='Товары_с_избытком', index=False)
                
                # Настройки калькулятора
                summary_data = []
                for point_type, categories in self.default_settings.items():
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
            print(f"❌ Ошибка создания Excel: {str(e)}")
            return None


# =============================================================================
# ИНТЕГРАЦИЯ В СУЩЕСТВУЮЩУЮ СИСТЕМУ
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
    
    # Добавляем методы в систему
    system.calculate_max_stock = types.MethodType(calculate_max_stock, system)
    system.compare_with_max_stock = types.MethodType(compare_with_max_stock, system)
    system.set_max_stock_settings = types.MethodType(set_max_stock_settings, system)
    system.show_max_stock_settings = types.MethodType(show_max_stock_settings, system)
    
    # Устанавливаем настройки по требованиям
    system.set_max_stock_settings('магазины', 'A', 20, 50)  # 20 дней MIN, 50 дней MAX
    system.set_max_stock_settings('магазины', 'B', 10, 25)  # 10 дней MIN, 25 дней MAX
    system.set_max_stock_settings('магазины', 'C', 10, 25)  # 10 дней MIN, 25 дней MAX


def complete_max_stock_integration(system):
    """
    Полная интеграция всех функций MAX остатков
    """
    # Добавляем основные методы
    add_max_stock_methods_to_system(system)
    
    # Добавляем метод экспорта
    def create_max_stock_export(self):
        """Метод экспорта MAX остатков"""
        return self.max_stock_calculator.create_max_stock_excel_export(self)
    
    system.create_max_stock_export = types.MethodType(create_max_stock_export, system)
    
    # Устанавливаем флаг интеграции
    system._max_stock_integrated = True
    
    print("✅ MAX остатки полностью интегрированы в систему")


# =============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("📦 Тест калькулятора максимальных остатков")
    
    # Создаем тестовый калькулятор
    calculator = MaxStockCalculator()
    
    # Показываем настройки
    calculator.show_settings_summary()
    
    # Изменяем настройки
    calculator.set_custom_settings('магазины', 'A', 25, 60)
    
    print("\n📊 Настройки после изменения:")
    calculator.show_settings_summary()