#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ИНТЕГРАЦИЯ ЦЕН - обновленная версия
Включает исправление load_sales_file_updated + все денежные расчеты
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import types
from datetime import datetime

# ===== ШАГИ ИНТЕГРАЦИИ =====

def complete_price_integration_setup(system):
    """
    ПОЛНАЯ настройка системы для работы с ценами
    Включает ВСЕ необходимые исправления
    """
    
    print("🚀 ПОЛНАЯ ИНТЕГРАЦИЯ ЦЕН - СТАРТ")
    print("=" * 50)
    
    # Шаг 1: Исправляем метод загрузки ADS
    print("🔧 Шаг 1: Исправление load_sales_file_updated...")
    apply_ads_price_fix_to_system(system)
    
    # Шаг 2: Исправляем методы расчетов
    print("🔧 Шаг 2: Исправление методов расчета...")
    apply_calculation_price_fixes(system)
    
    # Шаг 3: Добавляем вспомогательные методы
    print("🔧 Шаг 3: Добавление вспомогательных методов...")
    add_price_helper_methods(system)
    
    print("✅ ПОЛНАЯ ИНТЕГРАЦИЯ ЦЕН ЗАВЕРШЕНА!")
    print("💰 Система готова к работе с денежным выражением дефицита")
    
    return True

# ===== ИСПРАВЛЕНИЕ 1: МЕТОД ЗАГРУЗКИ ADS С ЦЕНАМИ =====

def load_sales_file_updated_with_prices(self, file_content) -> dict:
    """ИСПРАВЛЕННЫЙ метод загрузки ADS с извлечением цен из колонки 12"""
    try:
        print("🔄 Обработка файла с поддержкой цен (колонка 12 'Посл. закупка')...")
    
        # Читаем Excel файл
        if hasattr(file_content, 'read'):
            df = pd.read_excel(file_content, engine='openpyxl')
        else:
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
    
        print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # Параметры обработки
        start_col_index = 12  # Колонка M (продажи)
        end_col_index = 28    # Колонка AB+1 (не включается)
        start_row = 3         # Строка 4 (индекс 3)
        nomenclature_col = 1  # Колонка B (номенклатура)
        price_col = 11        # НОВОЕ: Колонка 12 "Посл. закупка" (индекс 11)
        
        print(f"📋 Параметры обработки:")
        print(f"   • Номенклатура: Колонка B (индекс {nomenclature_col})")
        print(f"   • ЦЕНЫ: Колонка L 'Посл. закупка' (индекс {price_col})")
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
        
        # НОВОЕ: Получаем цены из колонки L (индекс 11)
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
            
            # НОВОЕ: Извлекаем цену для данного товара
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
            
            # Формула ADS: среднее значение / 30.5
            average_value = row_sales_numeric.mean()
            ads_value = average_value / 30.5
            
            sales_data_list.append({
                'номенклатура': item_name,
                'ads': ads_value,
                'average_value': average_value,
                'total_sales': row_sales_numeric.sum(),
                'monthly_data': row_sales_numeric.tolist(),
                'last_purchase_price': float(item_price)  # НОВОЕ: ЦЕНА!
            })
        
        # Создаем DataFrame
        ads_df = pd.DataFrame(sales_data_list)
        
        # Сохраняем результаты в системе
        self.sales_data = ads_df
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
        
        # Топ товары с ценами
        if prices_found > 0:
            print(f"\n🏆 Топ-5 товаров по ADS (с ценами):")
            top_with_prices = ads_df[ads_df['last_purchase_price'] > 0].nlargest(5, 'ads')
            for i, (_, row) in enumerate(top_with_prices.iterrows(), 1):
                print(f"  {i}. {row['номенклатура'][:40]:<40} | ADS: {row['ads']:>6.2f} | Цена: {row['last_purchase_price']:>8.2f} ₽")
        
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

# ===== ИСПРАВЛЕНИЕ 2: МЕТОДЫ РАСЧЕТОВ С ЦЕНАМИ =====

def calculate_min_stock_with_prices(self, ip_target_days=None, min_stock_days=None) -> dict:
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
        
        # НОВОЕ: Денежные расчеты
        if 'last_purchase_price' in df.columns:
            df['min_stock_money'] = df['min_stock_total'] * df['last_purchase_price']
            df['transit_consumption_money'] = df['transit_consumption'] * df['last_purchase_price']
            df['min_stock_base_money'] = df['min_stock_base'] * df['last_purchase_price']
            
            total_min_stock_money = df['min_stock_money'].sum()
            items_with_price = len(df[df['last_purchase_price'] > 0])
            
            print(f"💰 Минимальные запасы с ценами:")
            print(f"   Стоимость MIN запасов: {total_min_stock_money:,.2f} ₽")
            print(f"   Товаров с ценами: {items_with_price}")
        
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

def compare_stock_vs_min_with_prices(self) -> dict:
    """ИСПРАВЛЕННОЕ сравнение остатков с ценами"""
    if self.calculated_min_stock is None:
        return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
    
    if self.stock_data is None:
        return {'success': False, 'error': 'Текущие остатки не загружены'}
    
    try:
        print("💰 Сравнение остатков с денежными расчетами...")
        
        min_stock_df = self.calculated_min_stock.copy()
        current_stock_df = self.stock_data[['номенклатура', 'total_current_stock']].copy()
        
        # Объединяем данные
        comparison = pd.merge(min_stock_df, current_stock_df, on='номенклатура', how='left')
        comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
        
        # Основные расчеты
        comparison['stock_deficit'] = comparison['min_stock_total'] - comparison['total_current_stock']
        comparison['stock_deficit'] = comparison['stock_deficit'].apply(lambda x: max(0, x))
        
        # НОВОЕ: Денежные расчеты
        if 'last_purchase_price' in comparison.columns:
            comparison['stock_deficit_money'] = comparison['stock_deficit'] * comparison['last_purchase_price']
            comparison['min_stock_money'] = comparison['min_stock_total'] * comparison['last_purchase_price']
            comparison['current_stock_money'] = comparison['total_current_stock'] * comparison['last_purchase_price']
        
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
        
        # НОВОЕ: Денежное выражение заказа
        if 'last_purchase_price' in comparison.columns:
            comparison['recommended_order_money'] = comparison['recommended_order'] * comparison['last_purchase_price']
        
        # Приоритет заказа
        comparison['order_priority'] = comparison.apply(
            lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                       else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                       else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                       else 'НЕ ТРЕБУЕТСЯ', axis=1
        )
        
        # Сортировка по денежному дефициту если есть цены
        if 'stock_deficit_money' in comparison.columns:
            priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
            comparison['status_priority'] = comparison['status'].map(priority_order)
            comparison = comparison.sort_values(['status_priority', 'stock_deficit_money'], ascending=[False, False])
            comparison = comparison.drop('status_priority', axis=1)
        else:
            comparison = comparison.sort_values('stock_deficit', ascending=False)
        
        self.stock_comparison = comparison
        
        # Статистика
        total_items = len(comparison)
        deficit_items = len(comparison[comparison['stock_deficit'] > 0])
        critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
        
        total_deficit_qty = comparison['stock_deficit'].sum()
        total_deficit_money = comparison['stock_deficit_money'].sum() if 'stock_deficit_money' in comparison.columns else 0
        
        items_with_price = len(comparison[comparison['last_purchase_price'] > 0]) if 'last_purchase_price' in comparison.columns else 0
        
        print(f"📊 Результаты сравнения:")
        print(f"   Всего товаров: {total_items}")
        print(f"   С дефицитом: {deficit_items}")
        print(f"   Критичных: {critical_items}")
        print(f"   Дефицит (шт): {total_deficit_qty:,.0f}")
        if total_deficit_money > 0:
            print(f"   Дефицит (₽): {total_deficit_money:,.2f}")
        if items_with_price > 0:
            print(f"   С ценами: {items_with_price}/{total_items}")
        
        return {
            'success': True,
            'total_items': total_items,
            'deficit_items': deficit_items,
            'critical_items': critical_items,
            'total_deficit_qty': total_deficit_qty,
            'total_deficit_money': total_deficit_money,
            'items_with_price': items_with_price,
            'price_coverage_percentage': (items_with_price / total_items) * 100 if total_items > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Ошибка сравнения: {str(e)}")
        return {'success': False, 'error': f"Ошибка сравнения остатков: {str(e)}"}

# ===== ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ =====

def apply_ads_price_fix_to_system(system):
    """Применение исправленного метода load_sales_file_updated"""
    system.load_sales_file_updated = types.MethodType(load_sales_file_updated_with_prices, system)
    print("✅ Метод load_sales_file_updated обновлен с поддержкой цен")
    return True

def apply_calculation_price_fixes(system):
    """Применение исправленных методов расчетов"""
    system.calculate_min_stock = types.MethodType(calculate_min_stock_with_prices, system)
    system.compare_stock_vs_min = types.MethodType(compare_stock_vs_min_with_prices, system)
    print("✅ Методы расчетов обновлены с поддержкой цен")
    return True

def add_price_helper_methods(system):
    """Добавление вспомогательных методов для работы с ценами"""
    
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
    
    def get_deficit_money_summary(self):
        """Получение сводки по денежному дефициту"""
        if not hasattr(self, 'stock_comparison') or self.stock_comparison is None:
            return {}
        
        comparison = self.stock_comparison
        
        if 'stock_deficit_money' not in comparison.columns:
            return {'error': 'Денежные расчеты не выполнены'}
        
        deficit_items = comparison[comparison['stock_deficit'] > 0]
        
        if len(deficit_items) == 0:
            return {'message': 'Товаров с дефицитом не найдено'}
        
        return {
            'total_deficit_items': len(deficit_items),
            'total_deficit_money': deficit_items['stock_deficit_money'].sum(),
            'critical_deficit_money': deficit_items[deficit_items['status'] == 'КРИТИЧНО']['stock_deficit_money'].sum(),
            'average_deficit_per_item': deficit_items['stock_deficit_money'].mean(),
            'recommended_order_money': deficit_items['recommended_order_money'].sum(),
            'top_deficit_items': deficit_items.nlargest(5, 'stock_deficit_money')[
                ['номенклатура', 'stock_deficit', 'stock_deficit_money', 'status']
            ].to_dict('records')
        }
    
    # Добавляем методы к системе
    system.get_price_statistics = types.MethodType(get_price_statistics, system)
    system.get_deficit_money_summary = types.MethodType(get_deficit_money_summary, system)
    
    print("✅ Вспомогательные методы для работы с ценами добавлены")
    return True

# ===== ПРОВЕРКА И ДИАГНОСТИКА =====

def check_complete_price_integration(system):
    """Проверка полной интеграции цен"""
    print("🔍 ПРОВЕРКА ПОЛНОЙ ИНТЕГРАЦИИ ЦЕН")
    print("-" * 50)
    
    checks = {
        "ADS метод обновлен": hasattr(system, 'load_sales_file_updated'),
        "ADS рассчитан": hasattr(system, 'calculated_ads') and system.calculated_ads is not None,
        "Цены в ADS": False,
        "MIN запасы с ценами": False,
        "Сравнение с ценами": False,
        "Вспомогательные методы": hasattr(system, 'get_price_statistics')
    }
    
    # Проверяем цены в ADS
    if checks["ADS рассчитан"]:
        checks["Цены в ADS"] = 'last_purchase_price' in system.calculated_ads.columns
        
        if checks["Цены в ADS"]:
            price_stats = system.get_price_statistics()
            if 'error' not in price_stats:
                print(f"   💰 Товаров с ценами: {price_stats['items_with_price']}/{price_stats['total_items']}")
                print(f"   💰 Покрытие: {price_stats['coverage_percentage']:.1f}%")
    
    # Проверяем MIN запасы
    if hasattr(system, 'calculated_min_stock') and system.calculated_min_stock is not None:
        checks["MIN запасы с ценами"] = 'min_stock_money' in system.calculated_min_stock.columns
    
    # Проверяем сравнение остатков
    if hasattr(system, 'stock_comparison') and system.stock_comparison is not None:
        checks["Сравнение с ценами"] = 'stock_deficit_money' in system.stock_comparison.columns
        
        if checks["Сравнение с ценами"]:
            deficit_summary = system.get_deficit_money_summary()
            if 'error' not in deficit_summary and 'message' not in deficit_summary:
                print(f"   💰 Общий дефицит: {deficit_summary['total_deficit_money']:,.2f} ₽")
    
    # Выводим результаты
    print(f"\n📋 Результаты проверки:")
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(checks.values())
    
    if all_passed:
        print(f"\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print(f"💰 Система полностью готова к работе с ценами")
    else:
        print(f"\n⚠️ Некоторые проверки не пройдены")
        print(f"💡 Убедитесь что:")
        print(f"   1. ADS файл содержит колонку L 'Посл. закупка'")
        print(f"   2. Все методы применены корректно")
        print(f"   3. Данные загружены в правильном порядке")
    
    return all_passed

# ===== STREAMLIT ИНТЕГРАЦИЯ =====

def show_price_integration_status_in_streamlit(system):
    """Показ статуса интеграции цен в Streamlit"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Интеграция цен")
    
    # Проверяем статус
    integration_status = check_complete_price_integration(system)
    
    if integration_status:
        st.sidebar.success("✅ Цены интегрированы")
        
        # Показываем статистику
        if hasattr(system, 'get_price_statistics'):
            price_stats = system.get_price_statistics()
            if 'error' not in price_stats and 'total_items' in price_stats:
                st.sidebar.metric(
                    "Покрытие ценами",
                    f"{price_stats['items_with_price']}/{price_stats['total_items']}",
                    f"{price_stats['coverage_percentage']:.1f}%"
                )
        
        # Показываем дефицит в деньгах
        if hasattr(system, 'get_deficit_money_summary'):
            deficit_summary = system.get_deficit_money_summary()
            if 'error' not in deficit_summary and 'message' not in deficit_summary:
                st.sidebar.metric(
                    "Дефицит (₽)",
                    f"{deficit_summary['total_deficit_money']:,.0f}"
                )
    else:
        st.sidebar.warning("⚠️ Цены не интегрированы")
        
        if st.sidebar.button("🔧 Применить интеграцию"):
            with st.spinner("Применение интеграции цен..."):
                complete_price_integration_setup(system)
                st.rerun()

# ===== ГЛАВНАЯ ФУНКЦИЯ =====

def integrate_complete_price_support():
    """
    ГЛАВНАЯ ФУНКЦИЯ интеграции полной поддержки цен
    
    Используйте в вашем Streamlit приложении:
    
    ```python
    from complete_price_integration import integrate_complete_price_support
    
    # В функции main():
    system = init_system()
    integrate_complete_price_support(system)
    ```
    """
    
    instructions = """
    🎯 ПОЛНАЯ ИНТЕГРАЦИЯ ЦЕН - ИНСТРУКЦИЯ
    
    1. ИМПОРТ И ПРИМЕНЕНИЕ:
    
    ```python
    from complete_price_integration import complete_price_integration_setup
    
    # В main():
    system = init_system()
    complete_price_integration_setup(system)
    ```
    
    2. РЕЗУЛЬТАТ:
    ✅ Исправлен load_sales_file_updated с поддержкой колонки 12
    ✅ Обновлены все методы расчетов с ценами
    ✅ Добавлены вспомогательные методы
    ✅ Полная поддержка денежного выражения дефицита
    
    3. ПРОВЕРКА:
    ```python
    check_complete_price_integration(system)
    ```
    
    4. STREAMLIT ИНТЕГРАЦИЯ:
    ```python
    show_price_integration_status_in_streamlit(system)
    ```
    
    🎉 После применения система будет полностью работать с ценами!
    """
    
    return instructions

if __name__ == "__main__":
    print(integrate_complete_price_support())