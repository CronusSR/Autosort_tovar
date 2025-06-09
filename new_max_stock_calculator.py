#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
НОВЫЙ МОДУЛЬ МАКСИМАЛЬНЫХ ОСТАТКОВ
Формулы: MIN = ADS × дни_минимального_запаса, MAX = ADS × дни_максимального_запаса
Пример: ADS=5, нужно на 10 дней → MIN=50, ADS=5, нужно на 50 дней → MAX=250
"""

import pandas as pd
import numpy as np
import types
from typing import Dict, Any, List

class NewMaxStockCalculator:
    """
    Новый калькулятор максимальных остатков по типам точек
    """
    
    def __init__(self):
        # Настройки по умолчанию для разных типов точек
        self.default_settings = {
            'хабы': {
                'min_days': 30,
                'max_days': 90,
                'description': 'Центральные распределительные центры'
            },
            'склады': {
                'min_days': 20,
                'max_days': 60,
                'description': 'Региональные склады'
            },
            'магазины': {
                'min_days': 10,
                'max_days': 25,
                'description': 'Розничные точки'
            }
        }
        
        print("📦 Новый калькулятор максимальных остатков инициализирован")
        print("🏪 Поддерживаемые типы точек: хабы, склады, магазины")

    def show_settings_summary(self):
        """Показать все настройки калькулятора"""
        print("\n📋 Настройки нового калькулятора максимальных остатков:")
        print("-" * 60)
        
        for point_type, settings in self.default_settings.items():
            min_days = settings['min_days']
            max_days = settings['max_days']
            description = settings['description']
            print(f"\n🏪 {point_type.upper()}: {description}")
            print(f"   MIN: {min_days} дней, MAX: {max_days} дней")

    def update_settings(self, point_type: str, min_days: int, max_days: int):
        """
        Обновление настроек для типа точки
        
        Args:
            point_type: Тип точки (хабы, склады, магазины)
            min_days: Дни минимального запаса
            max_days: Дни максимального запаса
        """
        if point_type not in self.default_settings:
            self.default_settings[point_type] = {'description': f'Пользовательский тип: {point_type}'}
        
        self.default_settings[point_type]['min_days'] = min_days
        self.default_settings[point_type]['max_days'] = max_days
        
        print(f"✅ Обновлены настройки для '{point_type}': MIN={min_days}д, MAX={max_days}д")

    def calculate_max_stock_for_system(self, system) -> Dict:
        """
        Расчет максимальных остатков для системы
        
        Args:
            system: Объект системы с calculated_ads
            
        Returns:
            Dict с результатами расчета
        """
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан. Сначала рассчитайте ADS.'}
        
        try:
            print("📈 Расчет новых максимальных остатков...")
            
            df = system.calculated_ads.copy()
            
            # Рассчитываем MIN и MAX для каждого типа точки
            for point_type, settings in self.default_settings.items():
                min_days = settings['min_days']
                max_days = settings['max_days']
                
                # Формулы: MIN = ADS × min_days, MAX = ADS × max_days
                df[f'{point_type}_min_days'] = min_days
                df[f'{point_type}_max_days'] = max_days
                df[f'{point_type}_min_stock'] = df['ads'] * min_days
                df[f'{point_type}_max_stock'] = df['ads'] * max_days
                df[f'{point_type}_range'] = df[f'{point_type}_max_stock'] - df[f'{point_type}_min_stock']
            
            # Общие средние значения по всем типам точек
            all_min_days = [settings['min_days'] for settings in self.default_settings.values()]
            all_max_days = [settings['max_days'] for settings in self.default_settings.values()]
            
            avg_min_days = np.mean(all_min_days)
            avg_max_days = np.mean(all_max_days)
            
            df['avg_min_days'] = avg_min_days
            df['avg_max_days'] = avg_max_days
            df['avg_min_stock'] = df['ads'] * avg_min_days
            df['avg_max_stock'] = df['ads'] * avg_max_days
            df['avg_range'] = df['avg_max_stock'] - df['avg_min_stock']
            
            # Сохраняем результат в системе
            system.new_calculated_max_stock = df
            
            # Статистика
            total_items = len(df)
            total_avg_max = df['avg_max_stock'].sum()
            avg_max_per_item = df['avg_max_stock'].mean()
            
            print(f"✅ Новые MAX остатки рассчитаны для {total_items} товаров")
            print(f"📊 Общий средний MAX запас: {total_avg_max:,.0f}")
            print(f"📊 Средний MAX на товар: {avg_max_per_item:.1f}")
            
            return {
                'success': True,
                'total_items': total_items,
                'total_avg_max_stock': total_avg_max,
                'avg_max_per_item': avg_max_per_item,
                'settings_used': self.default_settings.copy()
            }
            
        except Exception as e:
            error_msg = f"Ошибка расчета новых MAX остатков: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}

    def get_max_stock_summary(self, system) -> Dict:
        """Получение сводки по рассчитанным максимальным остаткам"""
        if not hasattr(system, 'new_calculated_max_stock') or system.new_calculated_max_stock is None:
            return {'error': 'Новые MAX остатки не рассчитаны'}
        
        df = system.new_calculated_max_stock
        
        summary = {
            'total_items': len(df),
            'location_types': list(self.default_settings.keys()),
            'avg_parameters': {
                'min_days': df['avg_min_days'].iloc[0],
                'max_days': df['avg_max_days'].iloc[0]
            },
            'totals': {
                'avg_min_stock': df['avg_min_stock'].sum(),
                'avg_max_stock': df['avg_max_stock'].sum(),
                'avg_range': df['avg_range'].sum()
            },
            'per_location': {}
        }
        
        # Статистика по типам точек
        for point_type in self.default_settings.keys():
            min_stock_col = f'{point_type}_min_stock'
            max_stock_col = f'{point_type}_max_stock'
            
            if min_stock_col in df.columns and max_stock_col in df.columns:
                summary['per_location'][point_type] = {
                    'min_days': self.default_settings[point_type]['min_days'],
                    'max_days': self.default_settings[point_type]['max_days'],
                    'total_min_stock': df[min_stock_col].sum(),
                    'total_max_stock': df[max_stock_col].sum(),
                    'avg_min_stock': df[min_stock_col].mean(),
                    'avg_max_stock': df[max_stock_col].mean()
                }
        
        return summary


def add_new_max_stock_to_system(system):
    """
    Добавление нового функционала максимальных остатков к системе
    """
    
    # Создаем экземпляр нового калькулятора
    system.new_max_stock_calculator = NewMaxStockCalculator()
    
    # Добавляем методы к системе
    def calculate_new_max_stock(self, custom_settings: Dict = None) -> Dict:
        """
        Расчет новых максимальных остатков
        
        Args:
            custom_settings: Пользовательские настройки {point_type: {min_days: X, max_days: Y}}
        """
        if custom_settings:
            # Временно обновляем настройки
            original_settings = self.new_max_stock_calculator.default_settings.copy()
            
            for point_type, settings in custom_settings.items():
                if 'min_days' in settings and 'max_days' in settings:
                    self.new_max_stock_calculator.update_settings(
                        point_type, 
                        settings['min_days'], 
                        settings['max_days']
                    )
        
        result = self.new_max_stock_calculator.calculate_max_stock_for_system(self)
        
        if custom_settings:
            # Восстанавливаем оригинальные настройки
            self.new_max_stock_calculator.default_settings = original_settings
        
        return result
    
    def update_new_max_stock_settings(self, point_type: str, min_days: int, max_days: int):
        """Обновление настроек для типа точки"""
        self.new_max_stock_calculator.update_settings(point_type, min_days, max_days)
    
    def get_new_max_stock_summary(self) -> Dict:
        """Получение сводки по новым максимальным остаткам"""
        return self.new_max_stock_calculator.get_max_stock_summary(self)
    
    def show_new_max_stock_settings(self):
        """Показать настройки нового калькулятора"""
        self.new_max_stock_calculator.show_settings_summary()
    
    # Привязываем методы к системе
    system.calculate_new_max_stock = types.MethodType(calculate_new_max_stock, system)
    system.update_new_max_stock_settings = types.MethodType(update_new_max_stock_settings, system)
    system.get_new_max_stock_summary = types.MethodType(get_new_max_stock_summary, system)
    system.show_new_max_stock_settings = types.MethodType(show_new_max_stock_settings, system)
    
    # Устанавливаем флаг интеграции
    system._new_max_stock_integrated = True
    
    print("✅ Новый функционал максимальных остатков добавлен к системе!")
    return True


def remove_old_max_stock_from_system(system):
    """
    Удаление старого функционала максимальных остатков
    """
    
    # Список старых атрибутов и методов для удаления
    old_attributes = [
        'calculated_max_stock',
        'stock_limits_config',
        'max_stock_calculator',
        '_max_stock_integrated'
    ]
    
    old_methods = [
        'calculate_max_stock',
        'calculate_max_stock_simple',
        'update_stock_limits',
        'get_max_stock_summary',
        'set_max_stock_settings',
        'show_max_stock_settings',
        'compare_with_max_stock',
        'create_max_stock_export'
    ]
    
    # Удаляем старые атрибуты
    for attr in old_attributes:
        if hasattr(system, attr):
            delattr(system, attr)
            print(f"❌ Удален старый атрибут: {attr}")
    
    # Удаляем старые методы
    for method in old_methods:
        if hasattr(system, method):
            delattr(system, method)
            print(f"❌ Удален старый метод: {method}")
    
    print("🗑️ Старый функционал максимальных остатков удален")


def replace_max_stock_functionality(system):
    """
    ГЛАВНАЯ ФУНКЦИЯ: Замена старого функционала максимальных остатков на новый
    """
    
    print("🔄 ЗАМЕНА ФУНКЦИОНАЛА МАКСИМАЛЬНЫХ ОСТАТКОВ")
    print("=" * 50)
    
    # 1. Удаляем старый функционал
    print("1️⃣ Удаление старого функционала...")
    remove_old_max_stock_from_system(system)
    
    # 2. Добавляем новый функционал
    print("\n2️⃣ Добавление нового функционала...")
    add_new_max_stock_to_system(system)
    
    print("\n✅ ЗАМЕНА ЗАВЕРШЕНА!")
    print("🎯 Новые методы доступны:")
    print("   - system.calculate_new_max_stock()")
    print("   - system.update_new_max_stock_settings()")
    print("   - system.get_new_max_stock_summary()")
    print("   - system.show_new_max_stock_settings()")
    
    return True


# =============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    print("📦 Тестирование нового калькулятора максимальных остатков")
    
    # Создаем калькулятор
    calculator = NewMaxStockCalculator()
    
    # Показываем настройки по умолчанию
    calculator.show_settings_summary()
    
    # Пример изменения настроек
    print("\n🔧 Изменение настроек согласно требованиям:")
    calculator.update_settings('магазины', 10, 25)  # MIN 10 дней, MAX 25 дней
    
    calculator.show_settings_summary()