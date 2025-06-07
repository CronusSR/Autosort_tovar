#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНЫЕ ИСПРАВЛЕНИЯ для системы анализа товарных запасов
Решает проблемы:
1. Топ товары не из файла
2. Ошибка 'last_purchase_price' при сравнении остатков
3. Множественные интеграции цен

Файл: complete_system_fixes.py
"""

import pandas as pd
import numpy as np
import io
import types
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# ===== КЛАСС ИСПРАВЛЕНИЙ =====

class SystemFixer:
    """Класс для применения всех исправлений к системе"""
    
    def __init__(self):
        self.fixes_applied = {}
    
    def apply_all_fixes(self, system):
        """Применить все исправления к системе"""
        print("🚀 ПРИМЕНЕНИЕ ПОЛНЫХ ИСПРАВЛЕНИЙ СИСТЕМЫ")
        print("=" * 60)
        
        # 1. Исправление методов сравнения остатков
        self.fix_stock_comparison_method(system)
        
        # 2. Исправление метода расчета MIN запасов
        self.fix_min_stock_calculation_method(system)
        
        # 3. Исправление метода загрузки ADS
        self.fix_ads_loading_method(system)
        
        # 4. Добавление отладочных методов
        self.add_debug_methods(system)
        
        # 5. Установка флага предотвращения повторных интеграций
        system._price_integration_applied = True
        system._fixes_applied = True
        
        print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
        return True
    
    def fix_stock_comparison_method(self, system):
        """Исправление метода сравнения остатков"""
        print("🔧 Исправление метода compare_stock_vs_min...")
        
        def compare_stock_vs_min_fixed(self) -> Dict:
            """ИСПРАВЛЕННЫЙ метод сравнения остатков с безопасной работой с ценами"""
            if self.calculated_min_stock is None:
                return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
            
            if self.stock_data is None:
                return {'success': False, 'error': 'Текущие остатки не загружены'}
            
            try:
                print("💰 Сравнение остатков с БЕЗОПАСНОЙ обработкой цен...")
                
                # Получаем данные
                min_stock_df = self.calculated_min_stock.copy()
                current_stock_df = self.stock_data[['номенклатура', 'total_current_stock']].copy()
                
                print(f"📊 MIN запасы: {len(min_stock_df)} товаров")
                print(f"📊 Остатки: {len(current_stock_df)} товаров")
                
                # КРИТИЧНО: Проверяем наличие цен в MIN запасах
                price_in_min_stock = 'last_purchase_price' in min_stock_df.columns
                print(f"💰 Цены в MIN запасах: {'✅' if price_in_min_stock else '❌'}")
                
                # Если цен нет в MIN запасах, пытаемся получить из ADS
                if not price_in_min_stock and hasattr(self, 'calculated_ads') and self.calculated_ads is not None:
                    if 'last_purchase_price' in self.calculated_ads.columns:
                        print("🔧 Добавляем цены из ADS данных...")
                        price_df = self.calculated_ads[['номенклатура', 'last_purchase_price']].copy()
                        min_stock_df = pd.merge(min_stock_df, price_df, on='номенклатура', how='left')
                        min_stock_df['last_purchase_price'] = pd.to_numeric(min_stock_df['last_purchase_price'], errors='coerce').fillna(0)
                        price_in_min_stock = True
                        
                        items_with_price = len(min_stock_df[min_stock_df['last_purchase_price'] > 0])
                        print(f"✅ Цены добавлены: {items_with_price} товаров с ценами")
                
                # Объединяем MIN запасы с остатками
                comparison = pd.merge(min_stock_df, current_stock_df, on='номенклатура', how='left')
                comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
                
                print(f"📊 После объединения: {len(comparison)} товаров")
                
                # Основные расчеты
                comparison['stock_deficit'] = comparison['min_stock_total'] - comparison['total_current_stock']
                comparison['stock_deficit'] = comparison['stock_deficit'].apply(lambda x: max(0, x))
                
                # БЕЗОПАСНАЯ РАБОТА С ЦЕНАМИ
                has_prices = 'last_purchase_price' in comparison.columns
                print(f"🔍 Итоговое наличие цен: {'✅' if has_prices else '❌'}")
                
                if has_prices:
                    print("💰 Выполняем денежные расчеты...")
                    
                    # Убеждаемся что цены в правильном формате
                    comparison['last_purchase_price'] = pd.to_numeric(comparison['last_purchase_price'], errors='coerce').fillna(0)
                    
                    # Денежные расчеты
                    comparison['stock_deficit_money'] = comparison['stock_deficit'] * comparison['last_purchase_price']
                    comparison['min_stock_money'] = comparison['min_stock_total'] * comparison['last_purchase_price']
                    comparison['current_stock_money'] = comparison['total_current_stock'] * comparison['last_purchase_price']
                    
                    # Статистика цен
                    items_with_price = len(comparison[comparison['last_purchase_price'] > 0])
                    total_items = len(comparison)
                    price_coverage = (items_with_price / total_items) * 100
                    
                    print(f"💰 Товаров с ценами: {items_with_price}/{total_items} ({price_coverage:.1f}%)")
                    
                    total_deficit_money = comparison['stock_deficit_money'].sum()
                    print(f"💰 Общий денежный дефицит: {total_deficit_money:,.2f} ₽")
                    
                else:
                    print("⚠️ Цены недоступны, работаем только с количественными данными")
                    comparison['stock_deficit_money'] = 0
                    comparison['min_stock_money'] = 0
                    comparison['current_stock_money'] = 0
                
                # Дни остатка
                comparison['current_stock_days'] = np.where(
                    comparison['ads'] > 0,
                    comparison['total_current_stock'] / comparison['ads'],
                    0
                )
                
                # Статус товара
                def determine_status(row):
                    if row['stock_deficit'] > 0:
                        if row['current_stock_days'] < row['ip_target_days']:
                            return 'КРИТИЧНО'
                        else:
                            return 'НЕДОСТАТОК'
                    else:
                        return 'ДОСТАТОЧНО'
                
                comparison['status'] = comparison.apply(determine_status, axis=1)
                
                # Рекомендуемый заказ
                safety_factor = getattr(self, 'default_params', {}).get('safety_factor', 1.0)
                comparison['recommended_order'] = comparison['stock_deficit'] * safety_factor
                comparison['recommended_order'] = comparison['recommended_order'].apply(lambda x: max(0, x))
                
                # Денежное выражение заказа
                if has_prices:
                    comparison['recommended_order_money'] = comparison['recommended_order'] * comparison['last_purchase_price']
                else:
                    comparison['recommended_order_money'] = 0
                
                # Приоритет заказа
                comparison['order_priority'] = comparison.apply(
                    lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                               else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                               else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                               else 'НЕ ТРЕБУЕТСЯ', axis=1
                )
                
                # Сортировка
                priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
                comparison['status_priority'] = comparison['status'].map(priority_order)
                
                if has_prices and comparison['stock_deficit_money'].sum() > 0:
                    print("📊 Сортировка по денежному дефициту")
                    comparison = comparison.sort_values(['status_priority', 'stock_deficit_money'], ascending=[False, False])
                else:
                    print("📊 Сортировка по количественному дефициту")
                    comparison = comparison.sort_values(['status_priority', 'stock_deficit'], ascending=[False, False])
                
                comparison = comparison.drop('status_priority', axis=1)
                
                # Сохраняем результат
                self.stock_comparison = comparison
                
                # Статистика
                total_items = len(comparison)
                deficit_items = len(comparison[comparison['stock_deficit'] > 0])
                critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
                total_deficit_qty = comparison['stock_deficit'].sum()
                
                result = {
                    'success': True,
                    'total_items': total_items,
                    'deficit_items': deficit_items,
                    'critical_items': critical_items,
                    'total_deficit_qty': total_deficit_qty,
                    'has_price_data': has_prices,
                    'deficit_percentage': (deficit_items / total_items) * 100,
                    'critical_percentage': (critical_items / total_items) * 100,
                    'top_deficit_items': comparison[comparison['stock_deficit'] > 0].head(10)[
                        ['номенклатура', 'stock_deficit', 'current_stock_days', 'status', 'order_priority']
                    ].to_dict('records')
                }
                
                # Добавляем денежные метрики если есть цены
                if has_prices:
                    total_deficit_money = comparison['stock_deficit_money'].sum()
                    total_recommended_order_money = comparison['recommended_order_money'].sum()
                    items_with_price = len(comparison[comparison['last_purchase_price'] > 0])
                    
                    result.update({
                        'total_deficit_money': total_deficit_money,
                        'total_recommended_order_money': total_recommended_order_money,
                        'items_with_price': items_with_price,
                        'price_coverage_percentage': (items_with_price / total_items) * 100
                    })
                
                print(f"\n📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
                print(f"   Всего товаров: {total_items}")
                print(f"   С дефицитом: {deficit_items}")
                print(f"   Критичных: {critical_items}")
                print(f"   Дефицит (шт): {total_deficit_qty:,.0f}")
                
                if has_prices:
                    print(f"   Дефицит (₽): {result['total_deficit_money']:,.2f}")
                    print(f"   К заказу (₽): {result['total_recommended_order_money']:,.2f}")
                
                return result
                
            except Exception as e:
                print(f"❌ Ошибка сравнения: {str(e)}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': f"Ошибка сравнения остатков: {str(e)}"}
        
        # Применяем исправление
        system.compare_stock_vs_min = types.MethodType(compare_stock_vs_min_fixed, system)
        print("✅ Метод compare_stock_vs_min исправлен")
    
    def fix_min_stock_calculation_method(self, system):
        """Исправление метода расчета минимальных запасов"""
        print("🔧 Исправление метода calculate_min_stock...")
        
        def calculate_min_stock_fixed(self, ip_target_days=None, min_stock_days=None) -> Dict:
            """ИСПРАВЛЕННЫЙ расчет минимальных запасов с ценами"""
            if self.calculated_ads is None:
                return {'success': False, 'error': 'ADS не рассчитан'}
            
            try:
                ip_days = ip_target_days or getattr(self, 'default_params', {}).get('ip_target_days', 7)
                stock_days = min_stock_days or getattr(self, 'default_params', {}).get('min_stock_days', 30)
                
                df = self.calculated_ads.copy()
                
                # Базовые расчеты
                df['ip_target_days'] = ip_days
                df['min_stock_days'] = stock_days
                df['transit_consumption'] = df['ads'] * ip_days
                df['min_stock_base'] = df['ads'] * stock_days
                df['min_stock_total'] = df['min_stock_base'] + df['transit_consumption']
                
                # Денежные расчеты (если есть цены)
                if 'last_purchase_price' in df.columns:
                    print("💰 Добавляем денежные расчеты минимальных запасов...")
                    df['min_stock_money'] = df['min_stock_total'] * df['last_purchase_price']
                    df['transit_consumption_money'] = df['transit_consumption'] * df['last_purchase_price']
                    df['min_stock_base_money'] = df['min_stock_base'] * df['last_purchase_price']
                    
                    total_min_stock_money = df['min_stock_money'].sum()
                    items_with_price = len(df[df['last_purchase_price'] > 0])
                    
                    print(f"💰 Стоимость MIN запасов: {total_min_stock_money:,.2f} ₽")
                    print(f"💰 Товаров с ценами: {items_with_price}")
                
                df['priority'] = df['ads'].apply(
                    lambda x: 'ВЫСОКИЙ' if x > df['ads'].quantile(0.8) else 
                             'СРЕДНИЙ' if x > df['ads'].quantile(0.5) else 'НИЗКИЙ'
                )
                
                self.calculated_min_stock = df
                
                result = {
                    'success': True,
                    'total_items': len(df),
                    'total_min_stock': df['min_stock_total'].sum(),
                    'parameters': {'ip_target_days': ip_days, 'min_stock_days': stock_days}
                }
                
                if 'min_stock_money' in df.columns:
                    result['money_metrics'] = {
                        'total_min_stock_money': df['min_stock_money'].sum(),
                        'items_with_price': len(df[df['last_purchase_price'] > 0])
                    }
                
                return result
                
            except Exception as e:
                return {'success': False, 'error': f"Ошибка расчета: {str(e)}"}
        
        # Применяем исправление
        system.calculate_min_stock = types.MethodType(calculate_min_stock_fixed, system)
        print("✅ Метод calculate_min_stock исправлен")
    
    def fix_ads_loading_method(self, system):
        """Исправление метода загрузки ADS файла"""
        print("🔧 Исправление метода load_sales_file_updated...")
        
        def load_sales_file_updated_fixed(self, file_content) -> dict:
            """ИСПРАВЛЕННЫЙ метод загрузки файла продаж с извлечением цен"""
            try:
                print("🔄 Обработка файла с логикой B-колонка + цены...")
            
                # Читаем Excel файл
                if hasattr(file_content, 'read'):
                    df = pd.read_excel(file_content, engine='openpyxl')
                else:
                    df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
                print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
                
                # Параметры обработки
                start_col_index = 12  # Колонка M
                end_col_index = 28    # Колонка AB+1
                start_row = 3         # Строка 4 (индекс 3)
                nomenclature_col = 1  # Колонка B (индекс 1)
                price_col = 11        # Колонка 12 "Посл. закупка" (индекс 11)
                
                print(f"📋 Параметры обработки:")
                print(f"   • Номенклатура: Колонка B (индекс {nomenclature_col})")
                print(f"   • ЦЕНЫ: Колонка 12 'Посл. закупка' (индекс {price_col})")
                print(f"   • Данные продаж: колонки {start_col_index}:{end_col_index} (M:AB)")
                print(f"   • Начальная строка: {start_row+1}")
                
                # Проверяем достаточность колонок
                if df.shape[1] <= max(end_col_index, price_col, nomenclature_col):
                    return {
                        'success': False,
                        'error': f'Недостаточно колонок в файле. Нужно минимум {max(end_col_index, price_col)+1}, есть {df.shape[1]}'
                    }
                
                # Получаем номенклатуру из колонки B
                nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
                
                # Получаем цены из колонки 12
                price_data = df.iloc[start_row:, price_col].copy()
                print(f"💰 Извлечение цен из колонки {price_col+1} (L - 'Посл. закупка')...")
                
                # Очищаем номенклатуру
                print("🧹 Очистка номенклатуры...")
                nomenclature_clean = nomenclature_data.dropna()
                nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
                nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
                
                # Исключаем последнюю строчку
                if len(nomenclature_clean) > 0:
                    nomenclature_clean = nomenclature_clean[:-1]
                    print("✅ Исключена последняя строчка")
                
                valid_indices = nomenclature_clean.index
                print(f"📊 После очистки: {len(nomenclature_clean)} товаров")
                
                if len(nomenclature_clean) == 0:
                    return {
                        'success': False,
                        'error': 'Нет валидных товаров после очистки номенклатуры'
                    }
                
                # Обрабатываем данные товаров
                print("📈 Обработка данных товаров с ценами...")
                
                sales_data_list = []
                prices_processed = 0
                prices_found = 0
                
                for idx in valid_indices:
                    item_name = str(nomenclature_clean.loc[idx]).strip()
                    
                    # Извлекаем данные продаж из колонок M:AB
                    row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                    row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                    
                    # Извлекаем цену для данного товара
                    try:
                        item_price = pd.to_numeric(price_data.loc[idx], errors='coerce')
                        if pd.isna(item_price) or item_price < 0:
                            item_price = 0.0
                        else:
                            prices_found += 1
                        prices_processed += 1
                    except:
                        item_price = 0.0
                        prices_processed += 1
                    
                    # Формула ADS: среднее значение / 30
                    average_value = row_sales_numeric.mean()
                    ads_value = average_value / 30
                    
                    sales_data_list.append({
                        'номенклатура': item_name,
                        'ads': ads_value,
                        'average_value': average_value,
                        'total_sales': row_sales_numeric.sum(),
                        'monthly_data': row_sales_numeric.tolist(),
                        'last_purchase_price': float(item_price)
                    })
                
                # Создаем DataFrame
                ads_df = pd.DataFrame(sales_data_list)
                
                # Сохраняем результаты в системе
                self.sales_data = ads_df  # ВАЖНО: сохраняем для правильного отображения топ товаров
                self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales', 'last_purchase_price']].copy()
                
                # Статистика по ценам
                print(f"\n💰 СТАТИСТИКА ЦЕН:")
                print(f"   Обработано: {prices_processed} товаров")
                print(f"   С ценами: {prices_found} товаров")
                print(f"   Покрытие: {(prices_found/prices_processed*100):.1f}%")
                
                if prices_found > 0:
                    valid_prices = ads_df[ads_df['last_purchase_price'] > 0]['last_purchase_price']
                    print(f"   Средняя цена: {valid_prices.mean():.2f} ₽")
                    print(f"   Диапазон цен: {valid_prices.min():.2f} - {valid_prices.max():.2f} ₽")
                
                # JSON данные с ценами
                json_output = {
                    'metadata': {
                        'file_processed_at': pd.Timestamp.now().isoformat(),
                        'total_items': len(ads_df),
                        'nomenclature_column': 'B',
                        'price_column': 'L (12) - Посл. закупка',
                        'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                        'calculation_method': 'average_monthly_divided_by_30_with_prices',
                        'formula': 'ADS = (среднее от M:AB) / 30',
                        'prices_extracted': True,
                        'prices_found': prices_found,
                        'price_coverage': f"{(prices_found/prices_processed*100):.1f}%"
                    },
                    'summary_stats': {
                        'total_ads': float(ads_df['ads'].sum()),
                        'average_ads': float(ads_df['ads'].mean()),
                        'total_inventory_value': float((ads_df['ads'] * 30 * ads_df['last_purchase_price']).sum()),
                        'average_price': float(valid_prices.mean()) if prices_found > 0 else 0
                    },
                    'items': [
                        {
                            'nomenclature': row['номенклатура'],
                            'ads_daily': row['ads'],
                            'average_monthly': row['average_value'],
                            'last_purchase_price': row['last_purchase_price']
                        }
                        for _, row in ads_df.iterrows()
                    ]
                }
                
                # Сохраняем JSON
                if not hasattr(self, '_json_data'):
                    self._json_data = {}
                self._json_data['ads'] = json_output
                
                positive_ads_count = len(ads_df[ads_df['ads'] > 0])
                
                print(f"\n📊 РЕЗУЛЬТАТЫ:")
                print("=" * 60)
                print(f"✅ Обработано товаров: {len(ads_df)}")
                print(f"✅ С положительным ADS: {positive_ads_count}")
                print(f"💰 С ценами: {prices_found}/{len(ads_df)} ({(prices_found/len(ads_df)*100):.1f}%)")
                print(f"📈 Общий ADS: {ads_df['ads'].sum():.2f}")
                
                return {
                    'success': True,
                    'total_items': len(ads_df),
                    'nomenclature_column': 'B',
                    'price_column': 'L (12) - Посл. закупка',
                    'calculation_method': 'average_monthly_divided_by_30_with_prices',
                    'total_ads': ads_df['ads'].sum(),
                    'average_ads': ads_df['ads'].mean(),
                    'items_with_positive_ads': positive_ads_count,
                    'prices_extracted': True,
                    'prices_found': prices_found,
                    'price_coverage_percentage': (prices_found/prices_processed*100) if prices_processed > 0 else 0,
                    'total_inventory_value': float((ads_df['ads'] * 30 * ads_df['last_purchase_price']).sum())
                }
                
            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': f"Ошибка загрузки файла: {str(e)}"}
        
        # Применяем исправление
        system.load_sales_file_updated = types.MethodType(load_sales_file_updated_fixed, system)
        print("✅ Метод load_sales_file_updated исправлен")
    
    def add_debug_methods(self, system):
        """Добавление отладочных методов"""
        print("🔧 Добавление отладочных методов...")
        
        def debug_price_flow(self):
            """Отладка потока цен через систему"""
            print("\n" + "="*60)
            print("🔍 ДИАГНОСТИКА ПОТОКА ЦЕН В СИСТЕМЕ")
            print("="*60)
            
            # 1. Проверяем исходные ADS данные
            if hasattr(self, 'calculated_ads') and self.calculated_ads is not None:
                ads_has_price = 'last_purchase_price' in self.calculated_ads.columns
                print(f"1️⃣ ADS данные ({len(self.calculated_ads)} товаров):")
                print(f"   Цены: {'✅' if ads_has_price else '❌'}")
                
                if ads_has_price:
                    price_count = len(self.calculated_ads[self.calculated_ads['last_purchase_price'] > 0])
                    print(f"   С ценами > 0: {price_count}")
                    print(f"   Пример: {self.calculated_ads['last_purchase_price'].head(3).tolist()}")
            else:
                print("1️⃣ ADS данные: ❌ Отсутствуют")
            
            # 2. Проверяем MIN запасы
            if hasattr(self, 'calculated_min_stock') and self.calculated_min_stock is not None:
                min_has_price = 'last_purchase_price' in self.calculated_min_stock.columns
                print(f"2️⃣ MIN запасы ({len(self.calculated_min_stock)} товаров):")
                print(f"   Цены: {'✅' if min_has_price else '❌'}")
                
                if min_has_price:
                    price_count = len(self.calculated_min_stock[self.calculated_min_stock['last_purchase_price'] > 0])
                    print(f"   С ценами > 0: {price_count}")
            else:
                print("2️⃣ MIN запасы: ❌ Отсутствуют")
            
            # 3. Проверяем остатки
            if hasattr(self, 'stock_data') and self.stock_data is not None:
                stock_has_price = 'last_purchase_price' in self.stock_data.columns
                print(f"3️⃣ Остатки ({len(self.stock_data)} товаров):")
                print(f"   Цены: {'✅' if stock_has_price else '❌'} (должно быть ❌)")
            else:
                print("3️⃣ Остатки: ❌ Отсутствуют")
            
            # 4. Проверяем результат сравнения
            if hasattr(self, 'stock_comparison') and self.stock_comparison is not None:
                comp_has_price = 'last_purchase_price' in self.stock_comparison.columns
                print(f"4️⃣ Сравнение ({len(self.stock_comparison)} товаров):")
                print(f"   Цены: {'✅' if comp_has_price else '❌'}")
                
                if comp_has_price:
                    deficit_money = self.stock_comparison['stock_deficit_money'].sum()
                    print(f"   Денежный дефицит: {deficit_money:,.2f} ₽")
            else:
                print("4️⃣ Сравнение: ❌ Отсутствует")
            
            print("="*60)
            
            return {
                'ads_has_price': hasattr(self, 'calculated_ads') and self.calculated_ads is not None and 'last_purchase_price' in self.calculated_ads.columns,
                'min_has_price': hasattr(self, 'calculated_min_stock') and self.calculated_min_stock is not None and 'last_purchase_price' in self.calculated_min_stock.columns,
                'stock_has_price': hasattr(self, 'stock_data') and self.stock_data is not None and 'last_purchase_price' in self.stock_data.columns,
                'comparison_has_price': hasattr(self, 'stock_comparison') and self.stock_comparison is not None and 'last_purchase_price' in self.stock_comparison.columns
            }
        
        def get_price_statistics(self):
            """Получение статистики по ценам"""
            if not hasattr(self, 'calculated_ads') or self.calculated_ads is None:
                return {}
            
            if 'last_purchase_price' not in self.calculated_ads.columns:
                return {'error': 'Цены не найдены'}
            
            ads_data = self.calculated_ads
            items_with_price = ads_data[ads_data['last_purchase_price'] > 0]
            
            if len(items_with_price) == 0:
                return {'items_with_price': 0, 'total_items': len(ads_data)}
            
            return {
                'total_items': len(ads_data),
                'items_with_price': len(items_with_price),
                'items_without_price': len(ads_data) - len(items_with_price),
                'coverage_percentage': (len(items_with_price) / len(ads_data)) * 100,
                'average_price': items_with_price['last_purchase_price'].mean(),
                'min_price': items_with_price['last_purchase_price'].min(),
                'max_price': items_with_price['last_purchase_price'].max(),
                'total_inventory_value': (ads_data['ads'] * 30 * ads_data['last_purchase_price']).sum()
            }
        
        def check_integration_status(self):
            """Проверка статуса интеграции"""
            checks = {
                "ADS рассчитан": hasattr(self, 'calculated_ads') and self.calculated_ads is not None,
                "Цены в ADS": False,
                "MIN запасы": hasattr(self, 'calculated_min_stock') and self.calculated_min_stock is not None,
                "Сравнение остатков": hasattr(self, 'stock_comparison') and self.stock_comparison is not None,
                "Денежные расчеты": False,
                "Исправления применены": hasattr(self, '_fixes_applied') and self._fixes_applied
            }
            
            # Проверяем цены в ADS
            if checks["ADS рассчитан"]:
                checks["Цены в ADS"] = 'last_purchase_price' in self.calculated_ads.columns
            
            # Проверяем денежные расчеты в сравнении
            if checks["Сравнение остатков"]:
                checks["Денежные расчеты"] = 'stock_deficit_money' in self.stock_comparison.columns
            
            return checks
        
        # Применяем отладочные методы
        system.debug_price_flow = types.MethodType(debug_price_flow, system)
        system.get_price_statistics = types.MethodType(get_price_statistics, system)
        system.check_integration_status = types.MethodType(check_integration_status, system)
        
        print("✅ Отладочные методы добавлены")


# ===== ИСПРАВЛЕНИЯ ДЛЯ STREAMLIT =====

def create_fixed_ads_page():
    """Создает исправленную функцию для страницы ADS расчета"""
    
    def ads_calculation_page_fixed(system):
        st.header("📊 Расчет ADS")
        
        st.markdown("""
        **🔢 ФОРМУЛА ADS:**
        - **Номенклатура:** Читается из колонки B 
        - **Цены:** Читаются из колонки L (12) "Посл. закупка"
        - **Диапазон данных:** M4:AB4 до последнего товара
        - **Формула:** ADS = (среднее значение от M4:AB4) / 30
        - **Исключения:** Последняя строка автоматически исключается
        """)
        
        # Показываем структуру файла
        with st.expander("📋 Требуемая структура Excel файла"):
            st.markdown("""
            ```
            Колонка A: Коды товаров (не используется)
            Колонка B: НОМЕНКЛАТУРА ТОВАРОВ (основная)
            Колонка L (12): ЦЕНЫ "Посл. закупка" (для денежных расчетов)
            Колонки M-AB: Месячные данные продаж
            Строка 4: Начало данных
            Последняя строка: Исключается автоматически
            ```
            """)
        
        status = system.get_system_status()
        
        if status['sales_analysis']['ads_calculated']:
            # ADS уже рассчитан
            st.success("✅ ADS рассчитан!")
            
            ads_data = system.calculated_ads
            
            # Информация о ценах
            if 'last_purchase_price' in ads_data.columns:
                st.success("✅ Найдены цены из колонки 'Посл. закупка'")
                
                price_stats = system.get_price_statistics()
                if 'error' not in price_stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Товаров", price_stats['total_items'])
                    with col2:
                        st.metric("С ценами", price_stats['items_with_price'])
                    with col3:
                        st.metric("Покрытие", f"{price_stats['coverage_percentage']:.1f}%")
                    with col4:
                        st.metric("Средняя цена", f"{price_stats['average_price']:,.2f} ₽")
            else:
                st.warning("⚠️ Цены не найдены в ADS данных")
            
            # Показываем информацию о методе
            if hasattr(system, '_json_data') and 'ads' in system._json_data:
                metadata = system._json_data['ads']['metadata']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Товаров", len(ads_data))
                with col2:
                    st.metric("Общий ADS", f"{ads_data['ads'].sum():.2f}")
                with col3:
                    st.metric("Средний ADS", f"{ads_data['ads'].mean():.4f}")
                
                # Показываем детали обработки
                st.subheader("📊 Детали обработки")
                
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.info(f"""
                    **Параметры обработки:**
                    - Диапазон: {metadata.get('range_used', 'M4:AB4')}
                    - Формула: {metadata.get('formula', 'ADS = среднее/30')}
                    - Метод: {metadata.get('calculation_method', 'исправленный')}
                    """)
                
                with info_col2:
                    st.info(f"""
                    **Статистика:**
                    - Обработано: {metadata.get('total_items', 0)} товаров
                    - С ценами: {metadata.get('prices_found', 0)} товаров
                    - Покрытие ценами: {metadata.get('price_coverage', '0%')}
                    """)
            
            # Топ товары по ADS - ИСПРАВЛЕННАЯ ВЕРСИЯ
            st.subheader("🏆 Топ товары по ADS")
            
            # ИСПРАВЛЕНИЕ: Используем sales_data (исходный файл)
            if hasattr(system, 'sales_data') and system.sales_data is not None:
                print("🔍 Используем данные из sales_data (исходный файл)")
                
                # Фильтруем товары с положительным ADS из исходного файла
                source_data = system.sales_data
                positive_ads_data = source_data[source_data['ads'] > 0]
                
                if len(positive_ads_data) == 0:
                    st.warning("⚠️ В загруженном файле нет товаров с положительным ADS")
                else:
                    # Берем топ-10 из исходного файла
                    top_ads = positive_ads_data.nlargest(10, 'ads')
                    
                    st.info(f"📊 Показаны топ-{len(top_ads)} товаров из загруженного файла (всего с ADS > 0: {len(positive_ads_data)})")
                    
                    fig_ads = px.bar(
                        top_ads,
                        x='ads',
                        y='номенклатура',
                        orientation='h',
                        title=f'Топ-{len(top_ads)} товаров по ADS (из загруженного файла)',
                        labels={'ads': 'Среднедневные продажи', 'номенклатура': 'Товар'}
                    )
                    fig_ads.update_layout(height=600)
                    st.plotly_chart(fig_ads, use_container_width=True)
                    
                    # Показываем статистику
                    st.write(f"**Статистика из файла:**")
                    st.write(f"- Всего товаров в файле: {len(source_data)}")
                    st.write(f"- С положительным ADS: {len(positive_ads_data)}")
                    st.write(f"- Средний ADS файла: {positive_ads_data['ads'].mean():.4f}")
                    st.write(f"- Общий ADS файла: {positive_ads_data['ads'].sum():.2f}")
            
            elif hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
                st.warning("⚠️ Используем calculated_ads (могут быть товары не из файла)")
                
                # Фильтруем только товары с положительным ADS
                ads_data = system.calculated_ads
                top_ads = ads_data[ads_data['ads'] > 0].nlargest(10, 'ads')
                
                if len(top_ads) == 0:
                    st.warning("⚠️ Нет товаров с положительным ADS")
                else:
                    fig_ads = px.bar(
                        top_ads,
                        x='ads',
                        y='номенклатура',
                        orientation='h',
                        title='Топ-10 товаров по ADS (из calculated_ads)',
                        labels={'ads': 'Среднедневные продажи', 'номенклатура': 'Товар'}
                    )
                    st.plotly_chart(fig_ads, use_container_width=True)
            
            else:
                st.error("❌ Нет данных ADS для отображения")
            
            # Детальная таблица
            with st.expander("📋 Детальные данные ADS"):
                ads_data_russian = ads_data.copy()
                
                # Маппинг колонок для ADS
                ads_mapping = {
                    'номенклатура': 'Номенклатура',
                    'ads': 'ADS',
                    'average_value': 'Среднемесячные продажи',
                    'total_sales': 'Общие продажи за период',
                    'last_purchase_price': 'Цена закупки (₽)'
                }
                
                # Переименовываем только существующие колонки
                existing_mappings = {k: v for k, v in ads_mapping.items() if k in ads_data_russian.columns}
                ads_data_russian = ads_data_russian.rename(columns=existing_mappings)
         
                st.dataframe(ads_data_russian, use_container_width=True)
            
            # Кнопки для экспорта
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Экспорт в Excel с ценами", key="export_excel_prices"):
                    try:
                        excel_buffer = system.export_all_results()
                        
                        st.download_button(
                            label="💾 Скачать Excel с ценовыми данными",
                            data=excel_buffer,
                            file_name=f"ads_with_prices_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка экспорта: {str(e)}")
            
            with col2:
                if st.button("🔄 Загрузить новый файл", key="reload_ads"):
                    # Очищаем данные для новой загрузки
                    system.sales_data = None
                    system.calculated_ads = None
                    if hasattr(system, '_json_data'):
                        system._json_data.pop('ads', None)
                    st.rerun()
        
        else:
            # ADS не рассчитан
            st.info("Загрузите файл с данными продаж для расчета ADS")
            
            st.warning("""
            ⚠️ **ВАЖНО: Проверьте структуру файла!**
            
            - Номенклатура должна быть в **колонке B**
            - Цены должны быть в **колонке L (12) "Посл. закупка"**
            - Данные продаж в колонках M-AB
            - Данные начинаются с 4-й строки
            """)
            
            sales_file = st.file_uploader(
                "Выберите файл продаж",
                type=['xlsx', 'xls'],
                help="Файл должен содержать номенклатуру в колонке B, цены в колонке L и данные продаж в колонках M-AB",
                key="sales_file_fixed"
            )
            
            if sales_file is not None:
                with st.spinner("Обработка файла с исправленной логикой ADS + цены..."):
                    # Используем исправленный метод
                    load_result = system.load_sales_file_updated(sales_file)
                    
                    if load_result['success']:
                        st.success(f"✅ ADS рассчитан для {load_result['total_items']} товаров")
                        
                        # Показываем детали результата
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Товаров", load_result['total_items'])
                        with col2:
                            st.metric("Номенклатура из", load_result.get('nomenclature_column', 'B'))
                        with col3:
                            st.metric("Общий ADS", f"{load_result.get('total_ads', 0):.2f}")
                        with col4:
                            st.metric("С ценами", f"{load_result.get('prices_found', 0)}")
                        
                        # Информация о обработке
                        st.success(f"""
                        **✅ Результаты обработки с ценами:**
                        - Формула: {load_result.get('formula', 'ADS = среднее/30')}
                        - Источник цен: {load_result.get('price_column', 'Колонка 12')}
                        - Покрытие ценами: {load_result.get('price_coverage_percentage', 0):.1f}%
                        - С положительным ADS: {load_result.get('items_with_positive_ads', 0)} товаров
                        - Стоимость запасов: {load_result.get('total_inventory_value', 0):,.2f} ₽
                        """)
                        
                        st.rerun()
                    else:
                        st.error(f"❌ {load_result['error']}")
    
    return ads_calculation_page_fixed


def create_fixed_comparison_page():
    """Создает исправленную функцию для страницы сравнения остатков"""
    
    def stock_comparison_page_fixed(system):
        st.header("⚖️💰 Сравнение остатков с денежным выражением")
        
        status = system.get_system_status()
        
        if not status['min_stock_analysis']['calculated']:
            st.warning("⚠️ Сначала необходимо рассчитать минимальные запасы")
            if st.button("📋 Перейти к расчету MIN запасов"):
                st.switch_page("MIN запасы")
            return
        
        # Проверяем статус интеграции
        if hasattr(system, 'check_integration_status'):
            integration_status = system.check_integration_status()
            
            if not integration_status.get('Исправления применены', False):
                st.warning("⚠️ Исправления не применены. Применяем автоматически...")
                fixer = SystemFixer()
                fixer.apply_all_fixes(system)
                st.success("✅ Исправления применены!")
        
        # Загрузка файла остатков
        if not status['stock_analysis']['loaded']:
            st.info("Загрузите файл текущих остатков (например: остатки.xlsx)")
            
            stock_file = st.file_uploader(
                "Выберите файл остатков",
                type=['xlsx', 'xls'],
                help="Файл должен содержать текущие остатки товаров на складах"
            )
            
            if stock_file is not None:
                with st.spinner("Загрузка данных остатков..."):
                    load_result = system.load_current_stock_file(stock_file)
                    
                    if load_result['success']:
                        st.success(f"✅ Остатки загружены: {load_result['total_items']} товаров")
                        st.rerun()
                    else:
                        st.error(f"❌ {load_result['error']}")
            return
        
        # Выполнение сравнения
        if not status['stock_analysis']['compared']:
            if st.button("▶️ Выполнить сравнение остатков с денежным расчетом"):
                with st.spinner("Сравнение остатков с минимальными запасами..."):
                    comparison_result = system.compare_stock_vs_min()
                    
                    if comparison_result['success']:
                        st.success("✅ Сравнение завершено с поддержкой денежного выражения!")
                        st.rerun()
                    else:
                        st.error(f"❌ {comparison_result['error']}")
            return
        
        # Показываем результаты сравнения с денежными метриками
        comparison_data = system.stock_comparison
        
        st.subheader("📊 Результаты анализа с денежным выражением")
        
        # Проверяем наличие ценовых данных
        has_price_data = 'last_purchase_price' in comparison_data.columns and 'stock_deficit_money' in comparison_data.columns
        
        if has_price_data:
            st.success("✅ Найдены цены - показываем денежное выражение")
        else:
            st.warning("⚠️ Цены не найдены - показываем только количественные данные")
        
        # Общая статистика
        total_items = len(comparison_data)
        deficit_items = len(comparison_data[comparison_data['stock_deficit'] > 0])
        critical_items = len(comparison_data[comparison_data['status'] == 'КРИТИЧНО'])
        sufficient_items = len(comparison_data[comparison_data['status'] == 'ДОСТАТОЧНО'])
        
        # Метрики в две строки
        st.subheader("📈 Количественные показатели")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего товаров", total_items)
        with col2:
            st.metric("С дефицитом", f"{deficit_items} ({deficit_items/total_items*100:.1f}%)")
        with col3:
            st.metric("Критично", f"{critical_items} ({critical_items/total_items*100:.1f}%)")
        with col4:
            total_deficit_qty = comparison_data['stock_deficit'].sum()
            st.metric("Общий дефицит (шт)", f"{total_deficit_qty:,.0f}")
        
        # Денежные показатели (если есть данные)
        if has_price_data:
            st.subheader("💰 Денежные показатели")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_deficit_money = comparison_data['stock_deficit_money'].sum()
                st.metric("Общий дефицит (₽)", f"{total_deficit_money:,.2f}")
            
            with col2:
                total_recommended_order_money = comparison_data['recommended_order_money'].sum()
                st.metric("К заказу (₽)", f"{total_recommended_order_money:,.2f}")
            
            with col3:
                items_with_price = len(comparison_data[comparison_data['last_purchase_price'] > 0])
                price_coverage = (items_with_price / total_items) * 100
                st.metric("Покрытие ценами", f"{price_coverage:.1f}%")
            
            with col4:
                if items_with_price > 0:
                    avg_price = comparison_data[comparison_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                    st.metric("Средняя цена", f"{avg_price:,.2f} ₽")
                else:
                    st.metric("Средняя цена", "Нет данных")
            
            # Дополнительная информация о ценах
            deficit_items_with_price = len(comparison_data[
                (comparison_data['stock_deficit'] > 0) & 
                (comparison_data['last_purchase_price'] > 0)
            ])
            
            st.info(f"""
            💰 **Детали по ценам:**
            - Дефицитных товаров с ценами: **{deficit_items_with_price}** из {deficit_items}
            - Источник цен: колонка "Посл. закупка" из ADS файла
            - Денежные расчеты доступны для **{(deficit_items_with_price/deficit_items*100):.1f}%** дефицитных товаров
            """)
        
        # Визуализации
        st.subheader("📊 Визуализация дефицита")
        
        # Создаем визуализации
        visualizations = system.create_visualizations()
        
        # Статус распределения
        if 'stock_status' in visualizations:
            st.plotly_chart(visualizations['stock_status'], use_container_width=True)
        
        # Специальная визуализация с денежным выражением
        if has_price_data:
            deficit_data = comparison_data[comparison_data['stock_deficit'] > 0]
            
            if len(deficit_data) > 0:
                # Топ по денежному дефициту
                top_deficit_money = deficit_data.nlargest(20, 'stock_deficit_money')
                
                # Создаем двойной график
                from plotly.subplots import make_subplots
                
                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('Дефицит в штуках', 'Дефицит в деньгах'),
                    horizontal_spacing=0.15
                )
                
                # График дефицита в штуках
                fig.add_trace(
                    go.Bar(
                        y=top_deficit_money['номенклатура'],
                        x=top_deficit_money['stock_deficit'],
                        orientation='h',
                        name='Дефицит (шт)',
                        marker_color='lightcoral',
                        text=top_deficit_money['stock_deficit'],
                        textposition='outside'
                    ),
                    row=1, col=1
                )
                
                # График дефицита в деньгах
                fig.add_trace(
                    go.Bar(
                        y=top_deficit_money['номенклатура'],
                        x=top_deficit_money['stock_deficit_money'],
                        orientation='h',
                        name='Дефицит (₽)',
                        marker_color='gold',
                        text=[f"{x:,.0f} ₽" for x in top_deficit_money['stock_deficit_money']],
                        textposition='outside'
                    ),
                    row=1, col=2
                )
                
                fig.update_layout(
                    title_text="🔝 Топ-20 товаров по дефициту: количество vs денежное выражение",
                    height=800,
                    showlegend=False
                )
                
                fig.update_xaxes(title_text="Количество (штук)", row=1, col=1)
                fig.update_xaxes(title_text="Денежное выражение (₽)", row=1, col=2)
                fig.update_yaxes(title_text="Товары", row=1, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Обычная визуализация дефицита (если нет денежных данных)
        elif 'deficit_analysis' in visualizations:
            st.plotly_chart(visualizations['deficit_analysis'], use_container_width=True)
        
        # Детальные результаты
        st.subheader("📋 Детальные результаты")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Фильтр по статусу",
                options=['Все', 'КРИТИЧНО', 'НЕДОСТАТОК', 'ДОСТАТОЧНО']
            )
        
        with col2:
            priority_filter = st.selectbox(
                "Фильтр по приоритету",
                options=['Все', 'СРОЧНО', 'ВЫСОКИЙ', 'СРЕДНИЙ', 'НЕ ТРЕБУЕТСЯ']
            )
        
        with col3:
            if has_price_data:
                min_deficit_money = st.number_input(
                    "Минимальный дефицит (₽)",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Показать товары с денежным дефицитом больше указанной суммы"
                )
            else:
                min_deficit = st.number_input(
                    "Минимальный дефицит (шт)",
                    min_value=0,
                    value=0,
                    help="Показать товары с дефицитом больше указанного количества"
                )
        
        # Применяем фильтры
        filtered_data = comparison_data.copy()
        
        if status_filter != 'Все':
            filtered_data = filtered_data[filtered_data['status'] == status_filter]
        
        if priority_filter != 'Все':
            filtered_data = filtered_data[filtered_data['order_priority'] == priority_filter]
        
        if has_price_data and min_deficit_money > 0:
            filtered_data = filtered_data[filtered_data['stock_deficit_money'] >= min_deficit_money]
        elif not has_price_data and 'min_deficit' in locals() and min_deficit > 0:
            filtered_data = filtered_data[filtered_data['stock_deficit'] >= min_deficit]
        
        # Сортировка
        if has_price_data:
            filtered_data = filtered_data.sort_values('stock_deficit_money', ascending=False)
            sort_info = "Сортировка: по денежному дефициту (убывание)"
        else:
            filtered_data = filtered_data.sort_values('stock_deficit', ascending=False)
            sort_info = "Сортировка: по количественному дефициту (убывание)"
        
        st.caption(sort_info)
        
        # Выбираем колонки для отображения
        display_columns = [
            'номенклатура', 'ads', 'min_stock_total', 'total_current_stock', 
            'stock_deficit', 'current_stock_days', 'status', 'order_priority', 'recommended_order'
        ]
        
        column_config = {
            'номенклатура': 'Товар',
            'ads': 'ADS',
            'min_stock_total': 'MIN запас',
            'total_current_stock': 'Текущий остаток',
            'stock_deficit': 'Дефицит (шт)',
            'current_stock_days': 'Дни остатка',
            'status': 'Статус',
            'order_priority': 'Приоритет',
            'recommended_order': 'Рекомендуемый заказ (шт)'
        }
        
        # Добавляем денежные колонки если есть данные
        if has_price_data:
            display_columns.extend([
                'last_purchase_price', 'stock_deficit_money', 'recommended_order_money'
            ])
            column_config.update({
                'last_purchase_price': st.column_config.NumberColumn(
                    'Цена (₽)',
                    format="%.2f"
                ),
                'stock_deficit_money': st.column_config.NumberColumn(
                    'Дефицит (₽)',
                    format="%.2f"
                ),
                'recommended_order_money': st.column_config.NumberColumn(
                    'К заказу (₽)',
                    format="%.2f"
                )
            })
        
        # Отображаем таблицу
        st.dataframe(
            filtered_data[display_columns], 
            use_container_width=True,
            column_config=column_config
        )
        
        if len(filtered_data) != len(comparison_data):
            st.info(f"Показано {len(filtered_data)} из {len(comparison_data)} товаров")
        
        # Быстрая статистика по отфильтрованным данным
        if len(filtered_data) > 0:
            st.subheader("📊 Статистика по отфильтрованным данным")
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                filtered_deficit = filtered_data['stock_deficit'].sum()
                st.metric("Дефицит (шт)", f"{filtered_deficit:,.0f}")
            
            with stat_col2:
                if has_price_data:
                    filtered_deficit_money = filtered_data['stock_deficit_money'].sum()
                    st.metric("Дефицит (₽)", f"{filtered_deficit_money:,.2f}")
                else:
                    st.metric("Дефицит (₽)", "Нет данных")
            
            with stat_col3:
                filtered_recommended = filtered_data['recommended_order'].sum()
                st.metric("К заказу (шт)", f"{filtered_recommended:,.0f}")
            
            with stat_col4:
                if has_price_data:
                    filtered_recommended_money = filtered_data['recommended_order_money'].sum()
                    st.metric("К заказу (₽)", f"{filtered_recommended_money:,.2f}")
                else:
                    st.metric("К заказу (₽)", "Нет данных")
        
        # Экспорт результатов
        st.subheader("📤 Экспорт результатов")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Экспорт дефицита в Excel", use_container_width=True):
                try:
                    excel_buffer = system.export_all_results()
                    
                    st.download_button(
                        label="💾 Скачать отчет по дефициту",
                        data=excel_buffer,
                        file_name=f"deficit_report_with_money_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success("✅ Excel файл с денежными данными готов!")
                    
                except Exception as e:
                    st.error(f"❌ Ошибка экспорта: {str(e)}")
        
        with col2:
            if st.button("🔧 Диагностика цен", use_container_width=True):
                if hasattr(system, 'debug_price_flow'):
                    with st.expander("🔍 Диагностика потока цен"):
                        debug_info = system.debug_price_flow()
                        
                        st.write("**Статус компонентов:**")
                        for component, status in debug_info.items():
                            st.write(f"{'✅' if status else '❌'} {component}")
                else:
                    st.error("Метод диагностики недоступен")
    
    return stock_comparison_page_fixed


def create_fixed_main_function():
    """Создает исправленную главную функцию"""
    
    def main_fixed():
        """ИСПРАВЛЕННАЯ основная функция приложения"""
        # Инициализация системы
        system = init_system()

        # ИСПРАВЛЕНИЕ: Применяем интеграцию ТОЛЬКО ОДИН раз
        if not hasattr(system, '_fixes_applied') or not system._fixes_applied:
            print("🔧 Применяем полные исправления системы (однократно)...")
            
            fixer = SystemFixer()
            fixer.apply_all_fixes(system)
            
            print("✅ Все исправления применены!")
        else:
            print("✅ Исправления уже применены, пропускаем")
        
        # Заголовок
        st.title("📦 Модульная система анализа товарных запасов")
        st.markdown("*Пошаговый анализ с выбором типа операции (ИСПРАВЛЕННАЯ ВЕРСИЯ)*")
        
        # Боковая панель с навигацией
        with st.sidebar:
            st.header("🧭 Навигация")
            
            # Показываем статус системы
            st.subheader("📊 Статус системы")
            show_system_status(system)

            # Показываем статус исправлений
            if hasattr(system, 'check_integration_status'):
                st.subheader("🔧 Статус исправлений")
                integration_status = system.check_integration_status()
                
                for check_name, status in integration_status.items():
                    status_icon = "✅" if status else "❌"
                    st.write(f"{status_icon} {check_name}")
            
            st.markdown("---")
            
            # Навигация
            page = st.selectbox(
                "Выберите раздел:",
                [
                    "🔤 ABC анализ",
                    "📊 ADS расчет", 
                    "📋 MIN запасы",
                    "⚖️ Сравнение остатков",
                    "🔤📊 ABC подкатегории",
                    "📤 Экспорт результатов",
                    "⚙️ Настройки"
                ]
            )
            
            st.markdown("---")
            
            # Быстрые действия
            st.subheader("⚡ Быстрые действия")
            
            status = system.get_system_status()
            
            if not status['abc_analysis']['analyzed']:
                st.button("🔤 Начать с ABC", key="quick_abc")
            elif not status['subcategory_analysis']['analyzed']:
                st.button("📊 Анализ подкатегорий", key="quick_subcategory")
            elif not status['sales_analysis']['ads_calculated']:
                st.button("📊 Рассчитать ADS", key="quick_ads")
            elif not status['min_stock_analysis']['calculated']:
                st.button("📋 MIN запасы", key="quick_min")
            elif not status['stock_analysis']['compared']:
                st.button("⚖️ Сравнить остатки", key="quick_compare")
            else:
                st.button("📤 Экспорт", key="quick_export")
            
            # Отладочные кнопки
            st.markdown("---")
            st.subheader("🔧 Отладка")
            
            if st.button("🔍 Диагностика цен"):
                if hasattr(system, 'debug_price_flow'):
                    system.debug_price_flow()
                else:
                    st.error("Метод диагностики недоступен")
            
            if st.button("📊 Статистика цен"):
                if hasattr(system, 'get_price_statistics'):
                    price_stats = system.get_price_statistics()
                    if 'error' not in price_stats:
                        st.json(price_stats)
                    else:
                        st.error(price_stats['error'])
                else:
                    st.error("Метод статистики недоступен")
        
        # Основной контент с исправленными функциями
        if page == "🔤 ABC анализ":
            abc_analysis_page_updated(system)
        elif page == "📊 ADS расчет":
            # Используем исправленную функцию ADS
            ads_page_fixed = create_fixed_ads_page()
            ads_page_fixed(system)
        elif page == "📋 MIN запасы":
            min_stock_calculation_page(system)
        elif page == "⚖️ Сравнение остатков":
            # Используем исправленную функцию сравнения
            comparison_page_fixed = create_fixed_comparison_page()
            comparison_page_fixed(system)
        elif page == "🔤📊 ABC подкатегории":  
            subcategory_abc_analysis_page(system)
        elif page == "📤 Экспорт результатов":
            export_page(system)
        elif page == "⚙️ Настройки":
            settings_page(system)
        
        # Футер
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🆘 Помощь"):
                st.info("""
                **Последовательность работы (ИСПРАВЛЕННАЯ):**
                1. 🔤 ABC анализ (опционально)
                2. 🔤📊 ABC анализ по подкатегориям (детализация)
                3. 📊 Расчет ADS из файла продаж + цены
                4. 📋 Расчет минимальных запасов + цены
                5. ⚖️ Загрузка остатков и сравнение + деньги
                6. 📤 Экспорт результатов с ценами
                """)
        
        with col2:
            status = system.get_system_status()
            progress = status['overall']['progress_percentage']
            if progress == 100:
                st.success("✅ Все этапы завершены!")
            else:
                st.info(f"📊 Прогресс: {progress:.0f}%")
        
        with col3:
            if hasattr(system, '_fixes_applied'):
                st.caption(f"✅ ИСПРАВЛЕНО v2.0 | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                st.caption(f"⚠️ НЕ ИСПРАВЛЕНО | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    
    return main_fixed


# ===== ИНСТРУКЦИИ ПО ПРИМЕНЕНИЮ =====

def get_application_instructions():
    """Инструкции по применению исправлений"""
    
    return """
# 🛠️ ИНСТРУКЦИЯ ПО ПРИМЕНЕНИЮ ПОЛНЫХ ИСПРАВЛЕНИЙ

## 📁 Структура файлов:

### 1. Создайте файл `complete_system_fixes.py`
Скопируйте весь код из артефакта complete_fixes

### 2. Обновите `modular_inventory_system.py`
Добавьте в начало файла:
```python
from complete_system_fixes import SystemFixer
```

В метод `__init__` класса `ModularInventorySystem` добавьте:
```python
def __init__(self):
    # ... существующий код ...
    self._fixes_applied = False
```

### 3. Обновите `streamlit_modular_app.py`
Добавьте в начало файла:
```python
from complete_system_fixes import (
    SystemFixer, 
    create_fixed_ads_page, 
    create_fixed_comparison_page, 
    create_fixed_main_function
)
```

Замените функцию `main()`:
```python
def main():
    main_fixed = create_fixed_main_function()
    main_fixed()
```

## 🚀 АВТОМАТИЧЕСКОЕ ПРИМЕНЕНИЕ:

### Вариант A: Через инициализацию системы
```python
def init_system():
    if 'inventory_system' not in st.session_state:
        st.session_state.inventory_system = ModularInventorySystem()
        
        # Применяем все исправления автоматически
        fixer = SystemFixer()
        fixer.apply_all_fixes(st.session_state.inventory_system)
        
    return st.session_state.inventory_system
```

### Вариант B: Ручное применение
```python
# В любом месте кода
from complete_system_fixes import SystemFixer

system = st.session_state.inventory_system
fixer = SystemFixer()
fixer.apply_all_fixes(system)
```

## ✅ РЕЗУЛЬТАТ ПОСЛЕ ПРИМЕНЕНИЯ:

1. **Исправлена ошибка KeyError: 'last_purchase_price'**
   - Безопасное объединение данных с ценами
   - Корректная передача цен от ADS к MIN запасам и сравнению

2. **Исправлен показ топ товаров**
   - Топ товары берутся из исходного файла (sales_data)
   - Отображаются только товары из загруженного файла

3. **Предотвращены множественные интеграции**
   - Исправления применяются только один раз
   - Нет повторных вызовов интеграции цен

4. **Добавлены отладочные методы**
   - system.debug_price_flow() - диагностика потока цен
   - system.get_price_statistics() - статистика по ценам
   - system.check_integration_status() - статус исправлений

## 🔍 ПРОВЕРКА РАБОТЫ:

После применения исправлений:
```python
# Проверяем статус
system.check_integration_status()

# Диагностируем поток цен
system.debug_price_flow()

# Получаем статистику
system.get_price_statistics()
```

## 🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:

✅ Загрузка ADS файла с ценами работает
✅ Топ товары отображаются из исходного файла  
✅ MIN запасы рассчитываются с ценами
✅ Сравнение остатков работает с денежным выражением
✅ Нет ошибок KeyError
✅ Нет множественных интеграций
✅ Полная поддержка денежных расчетов

---

**ВАЖНО:** После применения исправлений перезапустите Streamlit приложение!
"""


# ===== БЫСТРАЯ ДИАГНОСТИКА =====

def quick_diagnostic_check(system):
    """Быстрая проверка системы после исправлений"""
    
    print("\n🔍 БЫСТРАЯ ДИАГНОСТИКА ПОСЛЕ ИСПРАВЛЕНИЙ")
    print("=" * 60)
    
    issues_found = []
    
    # 1. Проверяем наличие исправлений
    if not hasattr(system, '_fixes_applied') or not system._fixes_applied:
        issues_found.append("Исправления не применены")
    else:
        print("✅ Исправления применены")
    
    # 2. Проверяем методы
    required_methods = [
        'debug_price_flow', 
        'get_price_statistics', 
        'check_integration_status'
    ]
    
    for method in required_methods:
        if hasattr(system, method):
            print(f"✅ Метод {method} доступен")
        else:
            issues_found.append(f"Отсутствует метод {method}")
    
    # 3. Проверяем данные
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        if 'last_purchase_price' in system.calculated_ads.columns:
            print("✅ Цены в ADS данных найдены")
        else:
            issues_found.append("Цены в ADS данных отсутствуют")
    
    # 4. Проверяем sales_data для топ товаров
    if hasattr(system, 'sales_data') and system.sales_data is not None:
        print("✅ sales_data доступны для топ товаров")
    else:
        issues_found.append("sales_data недоступны")
    
    print("\n📊 ИТОГ ДИАГНОСТИКИ:")
    if not issues_found:
        print("🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        return True
    else:
        print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        for issue in issues_found:
            print(f"   ❌ {issue}")
        return False


if __name__ == "__main__":
    print(get_application_instructions())