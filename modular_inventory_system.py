#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульный обработчик данных для системы анализа товарных запасов 
Поддерживает пошаговый анализ с выбором типа операции
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
import plotly.express as px
import plotly.graph_objects as go
from subcategory_abc import SubcategoryABCAnalyzer


warnings.filterwarnings('ignore')

class ModularInventorySystem:
    """Модульная система анализа товарных запасов"""
    def update_modular_inventory_system():
        """
        Дополнения для modular_inventory_system.py:
        """
        
        def analyze_warehouse_distribution(self):
            """Анализирует распределение остатков по складам"""
            if not hasattr(self, 'warehouse_analyzer'):
                return None
            
            if not self.warehouse_analyzer.warehouse_analysis:
                return None
            
            warehouse_distribution = {}
            
            for warehouse_key, config in self.warehouse_analyzer.warehouse_config.items():
                warehouse_distribution[warehouse_key] = {
                    'name': config['name'],
                    'short_name': config['short_name'],
                    'total_items': 0,
                    'total_stock': 0,
                    'critical_items': 0,
                    'warning_items': 0,
                    'good_items': 0
                }
            
            # Подсчитываем статистику
            for item in self.warehouse_analyzer.warehouse_analysis:
                for warehouse_key, warehouse_data in item['warehouses'].items():
                    stats = warehouse_distribution[warehouse_key]
                    stats['total_items'] += 1
                    stats['total_stock'] += warehouse_data['current_stock']
                    
                    if warehouse_data['status'] == 'critical':
                        stats['critical_items'] += 1
                    elif warehouse_data['status'] == 'warning':
                        stats['warning_items'] += 1
                    else:
                        stats['good_items'] += 1
            
            return warehouse_distribution
        
        def get_warehouse_efficiency_report(self):
            """Формирует отчет об эффективности складов"""
            distribution = self.analyze_warehouse_distribution()
            if not distribution:
                return None
            
            efficiency_report = []
            
            for warehouse_key, stats in distribution.items():
                if stats['total_items'] > 0:
                    critical_rate = (stats['critical_items'] / stats['total_items']) * 100
                    warning_rate = (stats['warning_items'] / stats['total_items']) * 100
                    efficiency_score = 100 - critical_rate - (warning_rate * 0.5)  # Штраф за проблемы
                    
                    efficiency_report.append({
                        'Склад': stats['short_name'],
                        'Полное название': stats['name'],
                        'Всего товаров': stats['total_items'],
                        'Общий остаток': stats['total_stock'],
                        'Критичных (%)': critical_rate,
                        'Внимания (%)': warning_rate,
                        'Эффективность (%)': efficiency_score,
                        'Рейтинг': 'Отлично' if efficiency_score >= 90 else 
                                  'Хорошо' if efficiency_score >= 75 else
                                  'Удовлетворительно' if efficiency_score >= 60 else 'Требует внимания'
                    })
            
            return pd.DataFrame(efficiency_report).sort_values('Эффективность (%)', ascending=False)
    
    def initialize_subcategory_analyzer(self):
        """Инициализация анализатора подкатегорий"""
        if not hasattr(self, 'subcategory_analyzer'):
            self.subcategory_analyzer = SubcategoryABCAnalyzer()
    
    def load_ads_from_single_file(self):
        """Загрузка ADS данных из обработанных файлов единого файла продаж"""
        import json
        import os
        
        all_ads_data = {}
        
        # Читаем данные каждого филиала
        if os.path.exists('ads/combined_ads_data.json'):
            with open('ads/combined_ads_data.json', 'r', encoding='utf-8') as f:
                combined_info = json.load(f)
            
            for branch_key, branch_info in combined_info['branches'].items():
                branch_file = f"ads/{branch_info['ads_file']}"
                
                if os.path.exists(branch_file):
                    with open(branch_file, 'r', encoding='utf-8') as f:
                        branch_data = json.load(f)
                    
                    # Преобразуем данные филиала в формат системы
                    branch_ads = []
                    for item_name, item_data in branch_data['ads_data'].items():
                        branch_ads.append({
                            'номенклатура': item_data['название'],
                            'ads': item_data['среднедневные_продажи'],
                            'общие_продажи': item_data['общие_продажи'],
                            'период_дней': item_data['период_дней'],
                            'филиал': branch_key
                        })
                    
                    # Сохраняем данные филиала
                    all_ads_data[branch_key] = {
                        'ads_data': pd.DataFrame(branch_ads),
                        'total_items': len(branch_ads),
                        'branch_name': branch_info['name']
                    }
        
        # Объединяем все данные в общий ADS
        if all_ads_data:
            # Создаем объединенный датафрейм
            combined_ads = []
            for branch_key, branch_data in all_ads_data.items():
                branch_df = branch_data['ads_data'].copy()
                branch_df['филиал'] = branch_key
                combined_ads.append(branch_df)
            
            if combined_ads:
                self.calculated_ads = pd.concat(combined_ads, ignore_index=True)
                
                # Группируем по товарам, суммируя ADS по всем филиалам
                grouped_ads = self.calculated_ads.groupby('номенклатура').agg({
                    'ads': 'sum',
                    'общие_продажи': 'sum',
                    'период_дней': 'first'
                }).reset_index()
                
                # Сохраняем как основные ADS данные
                self.sales_data = grouped_ads
                
                # Сохраняем данные по филиалам отдельно
                self.multiple_files_data = all_ads_data
                self.is_multiple_files_mode = True
                
                return all_ads_data
        
        return None
    def __init__(self):
        # Данные по этапам
        self.abc_data = None
        self.sales_data = None
        self.stock_data = None
        
        # Результаты расчетов
        self.abc_results = None
        self.calculated_ads = None
        self.calculated_min_stock = None
        self.stock_comparison = None
        
        # Данные для множественных файлов
        self.multiple_files_data = {}  # Хранилище по филиалам
        self.combined_sales_data = None
        self.is_multiple_files_mode = False
        self.processing_log = []
        
        # Параметры по умолчанию
        self.default_params = {
            'ip_target_days': 7,
            'min_stock_days': 30,
            'safety_factor': 1.0
        }
        
        try:
            from new_max_stock_calculator import replace_max_stock_functionality
            replace_max_stock_functionality(self)
            self._new_max_stock_ready = True
        except Exception as e:
            print(f"⚠️ Ошибка инициализации новых MAX остатков: {e}")
            self._new_max_stock_ready = False
    
    def perform_subcategory_abc_analysis(self) -> Dict:
        """
        Выполнение ABC анализа по подкатегориям
        
        Returns:
            Dict с результатами анализа подкатегорий
        """
        if self.abc_data is None:
            return {'success': False, 'error': 'Сначала выполните основной ABC анализ'}
        
        try:
            # Инициализируем анализатор
            self.initialize_subcategory_analyzer()
            
            # Загружаем данные
            load_result = self.subcategory_analyzer.load_data_with_subcategories(self.abc_data)
            
            if not load_result['success']:
                return load_result
            
            # Выполняем анализ
            analysis_result = self.subcategory_analyzer.perform_subcategory_abc_analysis()
            
            if analysis_result['success']:
                # Сохраняем результаты в основной системе
                if not hasattr(self, 'subcategory_results'):
                    self.subcategory_results = {}
                
                self.subcategory_results = {
                    'analysis_data': analysis_result,
                    'subcategory_details': self.subcategory_analyzer.subcategory_results,
                    'pareto_analysis': self.subcategory_analyzer.get_subcategory_pareto_analysis(),
                    'category_analysis': self.subcategory_analyzer.get_subcategory_analysis_by_category(),
                    'recommendations': self.subcategory_analyzer.get_subcategory_recommendations()
                }
            
            return analysis_result
            
        except Exception as e:
            return {'success': False, 'error': f'Ошибка анализа подкатегорий: {str(e)}'}

    def get_subcategory_summary_report(self) -> Dict:
        """Получение сводного отчета по подкатегориям"""
        if not hasattr(self, 'subcategory_results') or not self.subcategory_results:
            return {}
        
        try:
            analysis_data = self.subcategory_results['analysis_data']
            subcategory_details = self.subcategory_results['subcategory_details']
            
            # Базовая статистика
            total_subcategories = len(subcategory_details) if subcategory_details else 0
            total_items = sum(data['total_items'] for data in subcategory_details.values()) if subcategory_details else 0
            total_sales = sum(data['total_sales'] for data in subcategory_details.values()) if subcategory_details else 0
            
            # ABC распределение по подкатегориям
            abc_distribution = {'A': 0, 'B': 0, 'C': 0}
            if subcategory_details:
                for data in subcategory_details.values():
                    for abc_class, count in data['abc_distribution'].items():
                        abc_distribution[abc_class] += count
            
            # Эффективность подкатегорий
            efficient_subcategories = 0
            if subcategory_details:
                for data in subcategory_details.values():
                    if data['total_items'] > 0:
                        a_percentage = (data['abc_distribution']['A'] / data['total_items']) * 100
                        if a_percentage > 20:  # Считаем эффективной если >20% A товаров
                            efficient_subcategories += 1
            
            return {
                'total_subcategories': total_subcategories,
                'total_items': total_items,
                'total_sales': float(total_sales),
                'abc_distribution': abc_distribution,
                'efficient_subcategories': efficient_subcategories,
                'efficiency_percentage': (efficient_subcategories / total_subcategories * 100) if total_subcategories > 0 else 0,
                'average_items_per_subcategory': total_items / total_subcategories if total_subcategories > 0 else 0,
                'categories_analyzed': len(set(data['category'] for data in subcategory_details.values())) if subcategory_details else 0
            }
            
        except Exception as e:
            return {'error': f'Ошибка создания отчета: {str(e)}'}

    def export_subcategory_results(self) -> io.BytesIO:
        """Экспорт результатов анализа подкатегорий в Excel"""
        if not hasattr(self, 'subcategory_analyzer') or not self.subcategory_analyzer.subcategory_results:
            return None
        
        try:
            from subcategory_abc import create_subcategory_excel_report
            excel_buffer = create_subcategory_excel_report(self.subcategory_analyzer)
            
            if excel_buffer:
                return io.BytesIO(excel_buffer)
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка экспорта подкатегорий: {str(e)}")
            return None

    def load_sales_file_updated(self, file_content) -> Dict:
        """
        ИСПРАВЛЕННАЯ загрузка файла продаж с извлечением цен из колонки 12
        """
        try:
            print("🔄 Обработка файла с поддержкой цен...")
            
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # Параметры обработки
            start_col_index = 12  # Колонка M (продажи)
            end_col_index = 28    # Колонка AB+1
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (номенклатура)
            price_col = 11        # 🔧 НОВОЕ: Колонка 12 "Посл. закупка" (индекс 11)
            
            print(f"📋 Параметры обработки:")
            print(f"   • Номенклатура: Колонка B")
            print(f"   • ЦЕНЫ: Колонка 12 'Посл. закупка'")  # 🔧 НОВОЕ
            print(f"   • Данные продаж: колонки M:AB")
            
            # Проверяем достаточность колонок
            if df.shape[1] <= max(end_col_index, price_col, nomenclature_col):
                return {
                    'success': False,
                    'error': f'Недостаточно колонок в файле. Нужно минимум {max(end_col_index, price_col, nomenclature_col)+1} колонок.'
                }
            
            # Получаем номенклатуру (колонка B)
            nomenclature_series = df.iloc[start_row:, nomenclature_col]
            valid_nomenclature = nomenclature_series.dropna()
            
            if len(valid_nomenclature) == 0:
                return {'success': False, 'error': 'Не найдена номенклатура в колонке B начиная с 4-й строки'}
            
            # 🔧 НОВОЕ: Получаем цены (колонка 12)
            price_series = df.iloc[start_row:start_row+len(valid_nomenclature), price_col]
            
            # Получаем данные продаж (колонки M:AB)
            sales_columns = df.iloc[start_row:start_row+len(valid_nomenclature), start_col_index:end_col_index]
            
            # Создаем DataFrame для обработки
            ads_data = []
            prices_found = 0
            
            for i, (idx, name) in enumerate(valid_nomenclature.items()):
                if pd.isna(name) or str(name).strip() == '':
                    continue
                
                # Получаем продажи
                sales_row = sales_columns.iloc[i]
                numeric_sales = pd.to_numeric(sales_row, errors='coerce').fillna(0)
                
                # 🔧 НОВОЕ: Получаем цену
                price = price_series.iloc[i] if i < len(price_series) else None
                price_value = 0
                
                if pd.notna(price):
                    try:
                        price_value = float(price)
                        if price_value > 0:
                            prices_found += 1
                    except (ValueError, TypeError):
                        price_value = 0
                
                # Рассчитываем ADS
                if len(numeric_sales) > 0:
                    monthly_avg = numeric_sales.mean()
                    ads = monthly_avg / 30
                    total_sales = numeric_sales.sum()
                else:
                    monthly_avg = 0
                    ads = 0
                    total_sales = 0
                
                ads_data.append({
                    'номенклатура': str(name).strip(),
                    'total_quantity_sold': total_sales,
                    'total_sales': total_sales,  # Для совместимости
                    'monthly_average': monthly_avg,
                    'ads': ads,
                    'last_purchase_price': price_value  # 🔧 НОВОЕ: Добавляем цену
                })
            
            # Создаем итоговый DataFrame
            ads_df = pd.DataFrame(ads_data)
            
            # Исключаем последнюю строку (как в оригинале)
            if len(ads_df) > 1:
                ads_df = ads_df.iloc[:-1].copy()
            
            # 🔧 НОВОЕ: Автоматическое заполнение ADS=0 по подкатегориям
            print("🔄 Применяем автозаполнение по подкатегориям для товаров с ADS=0...")
            filled_count = self._apply_subcategory_autofill(ads_df)
            if filled_count > 0:
                print(f"✅ Автозаполнено {filled_count} товаров с ADS=0 средними значениями по подкатегориям")
            
            # Сохраняем результат
            self.calculated_ads = ads_df
            self.sales_data = ads_df  # Для совместимости
            
            # Статистика с учетом автозаполнения
            positive_ads_count = len(ads_df[ads_df['ads'] > 0])
            zero_ads_count = len(ads_df[ads_df['ads'] == 0])
            
            print(f"✅ Обработка завершена:")
            print(f"   Товаров: {len(ads_df)}")
            print(f"   С положительным ADS: {positive_ads_count} (после автозаполнения)")
            print(f"   С ADS=0: {zero_ads_count}")
            print(f"   📊 Общий ADS: {ads_df['ads'].sum():.2f}")
            print(f"   💰 ЦЕНЫ: найдено {prices_found} из {len(ads_df)} товаров")  # 🔧 НОВОЕ
            
            # 🔧 НОВОЕ: Топ товары с ценами
            if prices_found > 0:
                print(f"\n🏆 Топ-3 товара по ADS (с ценами):")
                top_with_prices = ads_df[ads_df['last_purchase_price'] > 0].nlargest(3, 'ads')
                for i, (_, row) in enumerate(top_with_prices.iterrows(), 1):
                    print(f"  {i}. {row['номенклатура'][:40]} | ADS: {row['ads']:.4f} | Цена: {row['last_purchase_price']:.2f} ₽")
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'nomenclature_column': 'B',
                'price_column': '12 (Посл. закупка)',  # 🔧 НОВОЕ
                'calculation_method': 'average_monthly_divided_by_30_with_prices',  # 🔧 ОБНОВЛЕНО
                'total_ads': ads_df['ads'].sum(),
                'average_ads': ads_df['ads'].mean(),
                'items_with_positive_ads': positive_ads_count,
                'prices_extracted': True,  # 🔧 НОВОЕ
                'prices_found': prices_found,  # 🔧 НОВОЕ
                'price_coverage_percentage': (prices_found/len(ads_df)*100) if len(ads_df) > 0 else 0,  # 🔧 НОВОЕ
                'total_inventory_value': float((ads_df['ads'] * 30 * ads_df['last_purchase_price']).sum())  # 🔧 НОВОЕ
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка загрузки файла: {str(e)}"}
    
    def _apply_subcategory_autofill(self, ads_df):
        """
        Применяет автозаполнение ADS=0 товаров средними значениями по подкатегориям
        """
        filled_count = 0
        
        try:
            # Проверяем наличие данных
            if ads_df is None or ads_df.empty:
                return 0
            
            # Проверяем наличие нужных колонок
            if 'номенклатура' not in ads_df.columns or 'ads' not in ads_df.columns:
                print("⚠️ Отсутствуют необходимые колонки для автозаполнения")
                return 0
            
            # Собираем ADS по подкатегориям (только товары с ADS > 0)
            subcategory_ads = {}
            for _, row in ads_df.iterrows():
                try:
                    item_name = str(row['номенклатура'])
                    ads_value = float(row['ads']) if pd.notna(row['ads']) else 0.0
                    
                    if ads_value > 0:
                        # Извлекаем подкатегорию из названия (первые 2 слова)
                        words = item_name.split()
                        subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                        
                        if subcategory not in subcategory_ads:
                            subcategory_ads[subcategory] = []
                        subcategory_ads[subcategory].append(ads_value)
                except (ValueError, TypeError):
                    continue
            
            # Рассчитываем средние по подкатегориям
            subcategory_averages = {}
            for subcategory, ads_values in subcategory_ads.items():
                if ads_values:
                    subcategory_averages[subcategory] = sum(ads_values) / len(ads_values)
            
            print(f"📊 Найдено {len(subcategory_averages)} подкатегорий с положительным ADS")
            
            # Заполняем товары с ADS=0
            for idx, row in ads_df.iterrows():
                try:
                    ads_value = float(row['ads']) if pd.notna(row['ads']) else 0.0
                    
                    if ads_value == 0:
                        item_name = str(row['номенклатура'])
                        words = item_name.split()
                        
                        # Пробуем несколько вариантов поиска подкатегории
                        found_replacement = False
                        
                        # 1. Точная подкатегория (2 слова)
                        subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                        if subcategory in subcategory_averages:
                            ads_df.at[idx, 'ads'] = subcategory_averages[subcategory]
                            filled_count += 1
                            found_replacement = True
                        
                        # 2. Первое слово (более широкая категория)
                        elif not found_replacement and words:
                            first_word = words[0]
                            if first_word in subcategory_averages:
                                ads_df.at[idx, 'ads'] = subcategory_averages[first_word]
                                filled_count += 1
                                found_replacement = True
                        
                        # 3. Минимальный ADS (5% от общего среднего)
                        if not found_replacement and subcategory_averages:
                            overall_avg = sum(subcategory_averages.values()) / len(subcategory_averages)
                            if overall_avg > 0:
                                ads_df.at[idx, 'ads'] = max(0.01, overall_avg * 0.05)
                                filled_count += 1
                                
                except (ValueError, TypeError, KeyError):
                    continue
            
            return filled_count
            
        except Exception as e:
            print(f"⚠️ Ошибка автозаполнения: {str(e)}")
            return 0
        
    def apply_ads_price_fix_to_system(system):
        """
        Применение исправленного метода load_sales_file_updated к системе
        """
        import types
        
        print("🔧 Применяем исправление ADS с поддержкой цен...")
        
        # Заменяем метод в системе
        system.load_sales_file_updated = types.MethodType(load_sales_file_updated_with_prices, system)
        
        print("✅ Метод load_sales_file_updated обновлен!")
        print("💰 Теперь поддерживается:")
        print("   - Извлечение цен из колонки 12 'Посл. закупка'")
        print("   - Добавление цен в ADS расчеты")
        print("   - Статистика по ценам")
        print("   - JSON с ценовой информацией")
        print("   - Расчет стоимости запасов")
        
        return True
    
    def check_prices_in_ads_data(system):
        """
        Проверка наличия ценовых данных в рассчитанном ADS
        """
        print("🔍 ПРОВЕРКА ЦЕНОВЫХ ДАННЫХ В ADS")
        print("-" * 40)
        
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            print("❌ ADS не рассчитан")
            return False
        
        ads_data = system.calculated_ads
        
        # Проверяем наличие колонки цен
        has_price_column = 'last_purchase_price' in ads_data.columns
        print(f"{'✅' if has_price_column else '❌'} Колонка 'last_purchase_price' в ADS: {has_price_column}")
        
        if has_price_column:
            total_items = len(ads_data)
            items_with_price = len(ads_data[ads_data['last_purchase_price'] > 0])
            items_without_price = total_items - items_with_price
            
            print(f"📊 Статистика цен:")
            print(f"   Всего товаров: {total_items}")
            print(f"   С ценами: {items_with_price}")
            print(f"   Без цен: {items_without_price}")
            print(f"   Покрытие: {(items_with_price/total_items*100):.1f}%")
            
            if items_with_price > 0:
                valid_prices = ads_data[ads_data['last_purchase_price'] > 0]['last_purchase_price']
                print(f"   Средняя цена: {valid_prices.mean():.2f} ₽")
                print(f"   Мин. цена: {valid_prices.min():.2f} ₽")
                print(f"   Макс. цена: {valid_prices.max():.2f} ₽")
                
                # Топ-3 по цене
                print(f"\n💎 Топ-3 самых дорогих товара:")
                top_expensive = ads_data[ads_data['last_purchase_price'] > 0].nlargest(3, 'last_purchase_price')
                for i, (_, row) in enumerate(top_expensive.iterrows(), 1):
                    print(f"   {i}. {row['номенклатура'][:50]} - {row['last_purchase_price']:.2f} ₽")
            
            return True
        else:
            print("💡 Рекомендации:")
            print("   1. Убедитесь что ADS файл содержит колонку 12 'Посл. закупка'")
            print("   2. Примените исправление: apply_ads_price_fix_to_system(system)")
            print("   3. Перезагрузите ADS файл")
            
            return False
        
    def demo_ads_with_prices(system):
        """
        Демонстрация работы ADS с ценами
        """
        print("🎭 ДЕМОНСТРАЦИЯ ADS С ЦЕНАМИ")
        print("=" * 50)
        
        # Применяем исправление
        apply_ads_price_fix_to_system(system)
        
        # Проверяем состояние
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            print("⚠️ ADS не рассчитан. Загрузите файл продаж.")
            return False
        
        # Проверяем цены
        has_prices = check_prices_in_ads_data(system)
        
        if has_prices:
            print("\n🎯 СИСТЕМА ГОТОВА К РАБОТЕ С ЦЕНАМИ!")
            print("   Теперь можно:")
            print("   - Рассчитывать минимальные запасы в денежном выражении")
            print("   - Сравнивать остатки с учетом стоимости")
            print("   - Приоритизировать дефицит по денежному выражению")
            print("   - Экспортировать отчеты с ценами")
        else:
            print("\n⚠️ ЦЕНЫ НЕ НАЙДЕНЫ")
            print("   Проверьте структуру ADS файла и перезагрузите его")
        
        return has_prices

    def instructions_for_ads_price_fix():
        """
        Инструкции по применению исправления ADS с ценами
        """
        
        print("""
        🔧 ИНСТРУКЦИЯ ПО ИСПРАВЛЕНИЮ LOAD_SALES_FILE_UPDATED:
        
        1. ПРОБЛЕМА:
           В текущем коде load_sales_file_updated отсутствует обработка цен
           
        2. РЕШЕНИЕ:
           Заменить метод на версию с поддержкой колонки 12 "Посл. закупка"
           
        3. ПРИМЕНЕНИЕ:
           
           # В вашем коде добавьте:
           from ads_price_fix import apply_ads_price_fix_to_system
           
           # Примените исправление:
           apply_ads_price_fix_to_system(system)
           
           # Проверьте результат:
           check_prices_in_ads_data(system)
        
        4. СТРУКТУРА ADS ФАЙЛА:
           
           | A   | B            | ... | L (12)      | M   | N   | ... | AB  |
           |-----|--------------|-----|-------------|-----|-----|-----|-----|
           | Код | Номенклатура | ... | Посл.закупка| Янв | Фев | ... | Дек |
           | 001 | Товар 1      | ... | 150.50      | 10  | 15  | ... | 20  |
           | 002 | Товар 2      | ... | 89.30       | 5   | 8   | ... | 12  |
        
        5. РЕЗУЛЬТАТ:
           ✅ ADS расчеты будут содержать колонку 'last_purchase_price'
           ✅ Все последующие денежные расчеты будут работать
           ✅ Отчеты будут включать денежное выражение
        
        6. ПРОВЕРКА:
           После применения исправления убедитесь что:
           - system.calculated_ads содержит колонку 'last_purchase_price'
           - В колонке есть числовые значения > 0
           - Покрытие ценами > 0%
        """)

    if __name__ == "__main__":
        instructions_for_ads_price_fix()

    def get_ads_json_data(self) -> str:
        """
        Получение ADS данных в формате JSON
        Добавьте этот метод в класс ModularInventorySystem
        """
        if hasattr(self, '_json_data') and 'ads' in self._json_data:
            import json
            return json.dumps(self._json_data['ads'], ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                'error': 'JSON данные недоступны',
                'message': 'Сначала обработайте файл ADS с новой логикой'
            }, ensure_ascii=False, indent=2)

    def save_ads_json_to_file(self, filename: str = None) -> str:
        """
        Сохранение ADS JSON данных в файл
        Добавьте этот метод в класс ModularInventorySystem
        """
        import json
        import pandas as pd
        
        if filename is None:
            filename = f"ads_data_fixed_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not hasattr(self, '_json_data') or 'ads' not in self._json_data:
            raise ValueError("Нет JSON данных для сохранения")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self._json_data['ads'], f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON данные сохранены в файл: {filename}")
        return filename

    def export_enhanced_results_with_fixed_ads(self) -> io.BytesIO:
        
        if self.calculated_ads is None:
            raise ValueError("Нет данных для экспорта")
        
        output = io.BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 1. Основные результаты ADS с исправленной логикой
                self.calculated_ads.to_excel(writer, sheet_name='ADS_Fixed_B_Column', index=False)
                
                # 2. Детальные данные с помесячной разбивкой
                if hasattr(self, 'sales_data') and self.sales_data is not None:
                    detailed_data = []
                    for _, row in self.sales_data.iterrows():
                        base_row = {
                            'номенклатура': row['номенклатура'],
                            'ads': row['ads'],
                            'average_monthly': row['average_value'],
                            'total_sales': row['total_sales']
                        }
                        
                        # Добавляем помесячные данные если есть
                        if 'monthly_data' in row and isinstance(row['monthly_data'], list):
                            for i, month_val in enumerate(row['monthly_data']):
                                base_row[f'month_{i+1}'] = month_val
                        
                        detailed_data.append(base_row)
                    
                    detailed_df = pd.DataFrame(detailed_data)
                    detailed_df.to_excel(writer, sheet_name='Monthly_Data_B_Column', index=False)
                
                # 3. JSON данные как текст
                if hasattr(self, '_json_data') and 'ads' in self._json_data:
                    json_text = self.get_ads_json_data()
                    json_df = pd.DataFrame([{'JSON_ADS_Data': json_text}])
                    json_df.to_excel(writer, sheet_name='JSON_ADS_Data', index=False)
                
                # 4. Методология и исправления
                methodology = pd.DataFrame([{
                    'Original_Issue': 'Номенклатура читалась из колонки A',
                    'Fixed_Version': 'Номенклатура читается из колонки B',
                    'Formula': 'ADS = (среднее от M4:AB4) / 30',
                    'Range': 'M4:AB4 до последнего товара',
                    'Exclusions': 'Последняя строка исключается',
                    'JSON_Conversion': 'Да, автоматически',
                    'Processing_Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Fix_Version': 'B_Column_Fix_v1.0'
                }])
                methodology.to_excel(writer, sheet_name='Fix_Methodology', index=False)
                
                # 5. Остальные данные системы (если есть)
                if self.abc_results is not None:
                    if 'abc_data_detailed' in self.abc_results:
                        abc_df = self.abc_results['abc_data_detailed']
                        abc_df.to_excel(writer, sheet_name='ABC_Analysis', index=False)
                
                if self.calculated_min_stock is not None:
                    self.calculated_min_stock.to_excel(writer, sheet_name='Min_Stock', index=False)
                
                if self.stock_comparison is not None:
                    self.stock_comparison.to_excel(writer, sheet_name='Stock_Comparison', index=False)
            
            output.seek(0)
            print("📤 Excel файл с исправленной логикой ADS создан успешно!")
            return output
            
        except Exception as e:
            raise Exception(f"Ошибка экспорта с исправленной логикой: {str(e)}")
    
    def _find_quantity_column_improved(self, df: pd.DataFrame, branch_name: str) -> str:
        """
        УЛУЧШЕННЫЙ поиск колонки с количеством продаж в файле
        
        Args:
            df: DataFrame с данными
            branch_name: Название филиала для логирования
            
        Returns:
            Название найденной колонки или None
        """
        print(f"🔍 {branch_name}: Поиск колонки количества среди {len(df.columns)} колонок")
        
        # 1. ПРИОРИТЕТ: колонка AD (индекс 30)
        if len(df.columns) > 30:
            col_ad = df.columns[30]
            print(f"  📊 Проверяем колонку AD (индекс 30): '{col_ad}'")
            
            try:
                test_data = pd.to_numeric(df[col_ad], errors='coerce')
                valid_count = test_data.count()
                total_count = len(test_data)
                
                if valid_count > 0:
                    non_zero_count = (test_data > 0).sum()
                    valid_percentage = (valid_count / total_count) * 100
                    non_zero_percentage = (non_zero_count / valid_count) * 100 if valid_count > 0 else 0
                    
                    print(f"    ✓ AD: {valid_count}/{total_count} ({valid_percentage:.1f}%) валидных")
                    print(f"    ✓ AD: {non_zero_count}/{valid_count} ({non_zero_percentage:.1f}%) положительных")
                    
                    # Показываем примеры значений
                    sample_values = test_data.dropna().head(3).tolist()
                    print(f"    📋 Примеры AD: {sample_values}")
                    
                    # Если более 30% валидных данных и более 20% положительных - используем
                    if valid_percentage > 30 and non_zero_percentage > 20:
                        print(f"  ✅ {branch_name}: Используем колонку AD")
                        return col_ad
                    else:
                        print(f"  ⚠️ AD колонка имеет низкое качество данных")
                else:
                    print(f"  ❌ AD колонка не содержит числовых данных")
            except Exception as e:
                print(f"  ❌ Ошибка проверки AD: {str(e)}")
        else:
            print(f"  ❌ Недостаточно колонок для AD (нужно >30, есть {len(df.columns)})")
        
        # 2. Поиск по ключевым словам (РАСШИРЕННЫЙ)
        print(f"  🔤 Поиск по ключевым словам...")
        quantity_patterns = [
            # Русские варианты (основные)
            'количество', 'кол-во', 'кол_во', 'кол.во', 'кол во', 'кол',
            'штук', 'шт', 'штуки', 'штука', 'единиц', 'ед', 'единица',
            'продано', 'проданы', 'продажи', 'продаж', 'прод',
            'итого', 'сумма', 'всего', 'общее', 'общий',
            'объем', 'объём', 'оборот',
            # Английские варианты
            'qty', 'quantity', 'amount', 'total', 'sold', 'sales',
            'pieces', 'units', 'count', 'sum', 'volume',
            # Сокращения и специфичные
            'реализовано', 'реализация', 'отгружено', 'отгрузка',
            'выручка', 'оборот', 'тираж'
        ]
        
        pattern_matches = []
        
        for col in df.columns:
            col_str = str(col).lower().strip()
            
            for pattern in quantity_patterns:
                if pattern in col_str:
                    try:
                        test_data = pd.to_numeric(df[col], errors='coerce')
                        valid_count = test_data.count()
                        
                        if valid_count > 0:
                            non_zero_count = (test_data > 0).sum()
                            total_count = len(test_data)
                            
                            valid_percentage = (valid_count / total_count) * 100
                            non_zero_percentage = (non_zero_count / valid_count) * 100 if valid_count > 0 else 0
                            
                            # Качество = валидность * положительность * бонус за хорошие паттерны
                            pattern_bonus = 1.5 if pattern in ['количество', 'кол-во', 'qty', 'sold'] else 1.0
                            quality_score = (valid_percentage / 100) * (non_zero_percentage / 100) * pattern_bonus
                            
                            pattern_matches.append({
                                'column': col,
                                'pattern': pattern,
                                'valid_count': valid_count,
                                'non_zero_count': non_zero_count,
                                'quality_score': quality_score,
                                'valid_percentage': valid_percentage,
                                'non_zero_percentage': non_zero_percentage
                            })
                            
                            print(f"    ✓ '{col}' ('{pattern}'): {quality_score:.3f} качества")
                            break
                    except:
                        continue
        
        # Выбираем лучший вариант по ключевым словам
        if pattern_matches:
            best_match = max(pattern_matches, key=lambda x: x['quality_score'])
            
            if best_match['quality_score'] > 0.1:  # Минимальное качество 10%
                print(f"  ✅ {branch_name}: Найдена по ключевому слову '{best_match['column']}'")
                print(f"    📊 Качество: {best_match['quality_score']:.3f}, валидных: {best_match['valid_percentage']:.1f}%")
                return best_match['column']
        
        # 3. Поиск среди всех числовых колонок
        print(f"  🔢 Поиск среди числовых колонок...")
        numeric_candidates = []
        
        for col in df.columns:
            if col == 'номенклатура':
                continue
                
            try:
                test_data = pd.to_numeric(df[col], errors='coerce').dropna()
                
                if len(test_data) > 0:
                    mean_val = test_data.mean()
                    median_val = test_data.median()
                    std_val = test_data.std()
                    min_val = test_data.min()
                    max_val = test_data.max()
                    
                    # Разумность значений для количества товара
                    is_reasonable = (
                        0.01 <= mean_val <= 1000000 and    # Разумный средний объем
                        min_val >= 0 and                   # Не отрицательные
                        max_val <= 10000000 and            # Не астрономические
                        (std_val < mean_val * 50 if mean_val > 0 else True)  # Разумный разброс
                    )
                    
                    if is_reasonable:
                        coverage = len(test_data) / len(df)  # Покрытие данных
                        
                        # Предпочитаем средние значения в разумном диапазоне (1-10000)
                        mean_score = 1.0
                        if 1 <= mean_val <= 10000:
                            mean_score = 1.5
                        elif 0.1 <= mean_val < 1 or 10000 < mean_val <= 100000:
                            mean_score = 1.2
                        elif mean_val < 0.1 or mean_val > 100000:
                            mean_score = 0.8
                        
                        quality_score = coverage * mean_score
                        
                        numeric_candidates.append({
                            'column': col,
                            'mean': mean_val,
                            'median': median_val,
                            'count': len(test_data),
                            'coverage': coverage,
                            'quality_score': quality_score
                        })
                        
                        print(f"    ✓ '{col}': ср={mean_val:.1f}, покрытие={coverage:.1%}, качество={quality_score:.3f}")
            except:
                continue
        
        # Выбираем лучший числовой вариант
        if numeric_candidates:
            best_numeric = max(numeric_candidates, key=lambda x: x['quality_score'])
            
            if best_numeric['quality_score'] > 0.2:  # Минимальное качество 20%
                print(f"  ✅ {branch_name}: Используем числовую колонку '{best_numeric['column']}'")
                print(f"    📊 Среднее: {best_numeric['mean']:.1f}, покрытие: {best_numeric['coverage']:.1%}")
                return best_numeric['column']
        
        # 4. Последняя попытка - любая колонка с достаточным количеством положительных чисел
        print(f"  🔄 Последняя попытка...")
        
        fallback_candidates = []
        
        for col in df.columns:
            if col == 'номенклатура':
                continue
                
            try:
                test_data = pd.to_numeric(df[col], errors='coerce')
                positive_data = test_data[test_data > 0]
                
                if len(positive_data) > max(50, len(df) * 0.1):  # Минимум 50 или 10% от всех строк
                    coverage = len(positive_data) / len(df)
                    fallback_candidates.append({
                        'column': col,
                        'positive_count': len(positive_data),
                        'coverage': coverage
                    })
            except:
                continue
        
        if fallback_candidates:
            best_fallback = max(fallback_candidates, key=lambda x: x['coverage'])
            print(f"  ⚠️ {branch_name}: Используем fallback колонку '{best_fallback['column']}'")
            print(f"    📊 Положительных значений: {best_fallback['positive_count']}, покрытие: {best_fallback['coverage']:.1%}")
            return best_fallback['column']
        
        print(f"  ❌ {branch_name}: НЕ НАЙДЕНА подходящая колонка количества")
        return None

    def load_abc_file(self, file_content) -> Dict:
        """
        ИСПРАВЛЕННАЯ загрузка ABC файла - все товары сохраняются
        """
        try:
            print("🔄 Загрузка ABC файла с сохранением ВСЕХ товаров...")
            
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                excel_file = pd.ExcelFile(file_content, engine='openpyxl')
            else:
                excel_file = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
            
            # Выбираем лист
            target_sheet = None
            sheet_priority = ['abc', 'Лист1', 'Sheet1']
            
            for priority_sheet in sheet_priority:
                if priority_sheet in excel_file.sheet_names:
                    target_sheet = priority_sheet
                    break
            
            if target_sheet is None:
                target_sheet = excel_file.sheet_names[0]
            
            # Читаем лист
            df = pd.read_excel(excel_file, sheet_name=target_sheet, engine='openpyxl')
            initial_rows = len(df)
            print(f"📊 Исходный размер: {initial_rows} строк")
            
            # Находим начало данных
            data_start_row = None
            for i in range(min(20, len(df))):
                first_cell = str(df.iloc[i, 0]).strip()
                if (len(first_cell) > 5 and 
                    first_cell.lower() != 'nan' and
                    first_cell != ''):
                    data_start_row = i
                    print(f"✅ Начало данных: строка {i+1}")
                    break
            
            if data_start_row is None:
                data_start_row = 5
            
            # Применяем отступ
            df = df.iloc[data_start_row:].copy()
            df = df.reset_index(drop=True)
            rows_after_offset = len(df)
            print(f"📊 После отступа: {rows_after_offset} строк")
            
            # Назначаем колонки
            if len(df.columns) >= 4:
                df.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + \
                            [f'extra_col_{i}' for i in range(4, len(df.columns))]
            elif len(df.columns) == 3:
                df.columns = ['nomenclature', 'category', 'annual_sales']
            else:
                df.columns = ['nomenclature', 'annual_sales'] + [f'col_{i}' for i in range(2, len(df.columns))]
            
            # Минимальная очистка номенклатуры
            before_nomenclature = len(df)
            df = df[df['nomenclature'].notna()]
            df = df[df['nomenclature'].astype(str).str.strip() != '']
            after_nomenclature = len(df)
            print(f"📊 После очистки номенклатуры: {after_nomenclature} строк")
            
            # ИСПРАВЛЕННАЯ обработка продаж - заменяем NaN на 0
            before_sales = len(df)
            
            # Преобразуем в числовой формат
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')
            
            # Заменяем NaN на 0
            nan_count = df['annual_sales'].isna().sum()
            df['annual_sales'] = df['annual_sales'].fillna(0)
            print(f"💰 NaN заменено на 0: {nan_count}")
            
            # Заменяем отрицательные на 0
            df.loc[df['annual_sales'] < 0, 'annual_sales'] = 0
            
            after_sales = len(df)
            print(f"📊 После обработки продаж: {after_sales} строк")
            
            # ИСПРАВЛЕННАЯ обработка категорий - заменяем пустые на 'Без категории'
            if 'category' in df.columns:
                df['category'] = df['category'].astype(str).str.strip()
                df['category'] = df['category'].replace(['nan', 'None', ''], 'Без категории')
                
                # Заполнение из подкатегорий
                if 'subcategory' in df.columns:
                    df['subcategory'] = df['subcategory'].astype(str).str.strip()
                    empty_cat_mask = df['category'] == 'Без категории'
                    valid_subcat_mask = ~df['subcategory'].isin(['nan', 'None', '', 'Без категории'])
                    fill_mask = empty_cat_mask & valid_subcat_mask
                    df.loc[fill_mask, 'category'] = df.loc[fill_mask, 'subcategory']
            else:
                df['category'] = 'Общая категория'
            
            # НЕ УДАЛЯЕМ строки с пустыми категориями!
            
            # Удаление дубликатов
            duplicates_count = df['nomenclature'].duplicated().sum()
            if duplicates_count > 0:
                df = df.drop_duplicates(subset=['nomenclature'], keep='first')
            
            final_count = len(df)
            
            # Статистика
            zero_sales = (df['annual_sales'] == 0).sum()
            positive_sales = (df['annual_sales'] > 0).sum()
            
            # Сохраняем данные
            self.abc_data = df
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   Финальное количество: {final_count} товаров")
            print(f"   С продажами = 0: {zero_sales}")
            print(f"   С продажами > 0: {positive_sales}")
            print(f"   Дубликатов удалено: {duplicates_count}")
            
            return {
                'success': True,
                'total_items': final_count,
                'items_with_sales': positive_sales,
                'items_with_zero_sales': zero_sales,
                'categories': df['category'].nunique(),
                'total_sales': float(df['annual_sales'].sum()),
                'average_sales': float(df['annual_sales'].mean()),
                'sheet_used': target_sheet,
                'duplicates_removed': duplicates_count,
                'zero_sales_included': True
            }
            
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            return {'success': False, 'error': f"Ошибка загрузки: {str(e)}"}

    def perform_abc_analysis(self) -> Dict:
        """
        ИСПРАВЛЕННЫЙ ABC анализ без ошибок numpy
        """
        if self.abc_data is None:
            return {'success': False, 'error': 'ABC данные не загружены'}
        
        try:
            print("🔤 ABC анализ для всех товаров...")
            
            df = self.abc_data.copy()
            initial_items = len(df)
            print(f"📊 Товаров для анализа: {initial_items}")
            
            # Убеждаемся что продажи в правильном формате
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce').fillna(0)
            
            # Статистика продаж
            zero_sales_count = (df['annual_sales'] == 0).sum()
            positive_sales_count = (df['annual_sales'] > 0).sum()
            
            print(f"💰 С продажами = 0: {zero_sales_count}")
            print(f"💰 С продажами > 0: {positive_sales_count}")
            
            # Сортируем по продажам
            df = df.sort_values('annual_sales', ascending=False)
            
            # Рассчитываем проценты
            if positive_sales_count > 0:
                total_sales = df[df['annual_sales'] > 0]['annual_sales'].sum()
                
                # Проценты продаж
                df['sales_percentage'] = 0.0
                positive_mask = df['annual_sales'] > 0
                df.loc[positive_mask, 'sales_percentage'] = (df.loc[positive_mask, 'annual_sales'] / total_sales) * 100
                
                # Накопительный процент
                df['cumulative_percentage'] = 0.0
                df.loc[positive_mask, 'cumulative_percentage'] = df.loc[positive_mask, 'sales_percentage'].cumsum()
                df.loc[~positive_mask, 'cumulative_percentage'] = 100.0
                
                # ABC классы - ИСПРАВЛЕННАЯ версия без apply
                df['abc_class'] = 'C'  # По умолчанию все C
                
                # Присваиваем классы по условиям
                df.loc[(df['annual_sales'] > 0) & (df['cumulative_percentage'] <= 80), 'abc_class'] = 'A'
                df.loc[(df['annual_sales'] > 0) & (df['cumulative_percentage'] > 80) & (df['cumulative_percentage'] <= 95), 'abc_class'] = 'B'
                # Товары с annual_sales == 0 остаются класса C
                
            else:
                # Если нет товаров с продажами, все получают класс C
                df['sales_percentage'] = 0.0
                df['cumulative_percentage'] = 100.0
                df['abc_class'] = 'C'
                total_sales = 0
            
            # Проверяем распределение ABC
            abc_counts = df['abc_class'].value_counts()
            final_items = len(df)
            
            print(f"\n🔤 ABC РАСПРЕДЕЛЕНИЕ:")
            print(f"   🔴 A товары: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/final_items*100:.1f}%)")
            print(f"   🟡 B товары: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/final_items*100:.1f}%)")
            print(f"   🟢 C товары: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/final_items*100:.1f}%)")
            
            # Анализ по категориям
            category_results = {}
            unique_categories = df['category'].dropna().unique()
            
            for category in unique_categories:
                category_data = df[df['category'] == category].copy()
                category_items = len(category_data)
                
                if category_items == 0:
                    continue
                
                category_sales = category_data['annual_sales'].sum()
                category_sales_pct = (category_sales / total_sales) * 100 if total_sales > 0 else 0
                
                abc_distribution = {
                    'A': len(category_data[category_data['abc_class'] == 'A']),
                    'B': len(category_data[category_data['abc_class'] == 'B']),
                    'C': len(category_data[category_data['abc_class'] == 'C'])
                }
                
                zero_sales_in_category = len(category_data[category_data['annual_sales'] == 0])
                positive_sales_in_category = len(category_data[category_data['annual_sales'] > 0])
                
                category_results[str(category)] = {
                    'total_items': category_items,
                    'items_with_sales': positive_sales_in_category,
                    'items_with_zero_sales': zero_sales_in_category,
                    'total_sales': float(category_sales),
                    'sales_percentage': float(category_sales_pct),
                    'abc_distribution': abc_distribution,
                    'avg_sales': float(category_data['annual_sales'].mean()),
                    'max_sales': float(category_data['annual_sales'].max()),
                    'min_sales': float(category_data['annual_sales'].min()),
                    'top_items': category_data.head(3)[['nomenclature', 'annual_sales', 'abc_class']].to_dict('records')
                }
            
            # Итоговая статистика
            abc_summary = {
                'A': int(abc_counts.get('A', 0)),
                'B': int(abc_counts.get('B', 0)),
                'C': int(abc_counts.get('C', 0))
            }
            
            pareto_stats = {
                'total_items_analyzed': final_items,
                'items_with_sales': positive_sales_count,
                'items_with_zero_sales': zero_sales_count,
                'a_items_percentage': (abc_summary['A'] / final_items) * 100,
                'a_sales_percentage': float(df[df['abc_class'] == 'A']['sales_percentage'].sum()),
                'pareto_achieved': positive_sales_count > 0 and df[df['abc_class'] == 'A']['sales_percentage'].sum() >= 70.0
            }
            
            # Сохраняем результаты
            self.abc_results = {
                'abc_data_detailed': df,
                'category_analysis': category_results,
                'abc_summary': abc_summary,
                'pareto_stats': pareto_stats,
                'total_sales': float(total_sales),
                'total_items': final_items,
                'items_with_zero_sales': zero_sales_count,
                'analysis_date': pd.Timestamp.now().isoformat(),
                'zero_sales_included': True
            }
            
            print(f"✅ ABC анализ завершен: {final_items} товаров")
            
            return {
                'success': True,
                'abc_summary': abc_summary,
                'category_count': len(category_results),
                'total_sales': float(total_sales),
                'total_items': final_items,
                'items_with_sales': positive_sales_count,
                'items_with_zero_sales': zero_sales_count,
                'pareto_achieved': pareto_stats['pareto_achieved'],
                'zero_sales_included': True
            }
            
        except Exception as e:
            print(f"❌ Ошибка ABC анализа: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка ABC анализа: {str(e)}"}
    
    def load_sales_file(self, file_content) -> Dict:
        """
        Загрузка файла продаж для расчета ADS
        
        Args:
            file_content: Содержимое файла продаж
            
        Returns:
            Dict с информацией о загруженных данных продаж
        """
        try:
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # Ищем строку с заголовками
            header_row = None
            for i, row in df.iterrows():
                row_str = str(row.iloc[0]).lower()
                if pd.notna(row.iloc[0]) and any(word in row_str for word in ['номенклатура', 'наименование', 'товар']):
                    header_row = i
                    break
            
            if header_row is not None:
                # Устанавливаем заголовки
                headers = df.iloc[header_row].tolist()
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
            
            # Стандартизируем названия колонок
            df.columns = [str(col).strip() if pd.notna(col) and str(col).strip() else f'empty_col_{i}' for i, col in enumerate(df.columns)]
            
            # Ищем колонки с данными по месяцам
            month_patterns = [
                'янв', 'фев', 'мар', 'апр', 'май', 'июн', 
                'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
                'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                '01', '02', '03', '04', '05', '06',
                '07', '08', '09', '10', '11', '12'
            ]
            
            sales_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(pattern in col_str for pattern in month_patterns):
                    sales_columns.append(col)
            
            # Если не найдены месячные колонки, ищем числовые
            if not sales_columns:
                for col in df.columns:
                    if col not in ['номенклатура', 'наименование', 'товар', 'категория']:
                        # Проверяем, есть ли числовые данные
                        try:
                            pd.to_numeric(df[col], errors='coerce')
                            sales_columns.append(col)
                        except:
                            continue
            
            # Очищаем основные данные
            nomenclature_col = None
            for col in df.columns:
                if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                    nomenclature_col = col
                    break
            
            if nomenclature_col is None:
                nomenclature_col = df.columns[0]  # Берем первую колонку
            
            # Переименовываем колонку номенклатуры
            df = df.rename(columns={nomenclature_col: 'номенклатура'})
            
            # Фильтруем данные
            df = df.dropna(subset=['номенклатура'])
            df = df[df['номенклатура'].astype(str).str.strip() != '']
            df = df[df['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем колонки продаж в числовой формат
            for col in sales_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Рассчитываем общие продажи за период
            if sales_columns:
                df['total_sales'] = df[sales_columns].sum(axis=1)
                # Предполагаем, что данные за год (365 дней)
                df['ads'] = df['total_sales'] / 365
            else:
                df['total_sales'] = 0
                df['ads'] = 0
            
            # Убираем товары без продаж
            df = df[df['total_sales'] > 0]
            
            self.sales_data = df
            self.calculated_ads = df[['номенклатура', 'ads', 'total_sales']].copy()
            
            return {
                'success': True,
                'total_items': len(df),
                'sales_columns_found': len(sales_columns),
                'total_sales': df['total_sales'].sum(),
                'total_ads': df['ads'].sum(),
                'avg_ads': df['ads'].mean(),
                'top_sellers': df.nlargest(5, 'ads')[['номенклатура', 'ads']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка загрузки файла продаж: {str(e)}"}
    
    def calculate_min_stock(self, ip_target_days: int = None, min_stock_days: int = None) -> Dict:
        """
        Расчет минимальных запасов на основе ADS
        
        Args:
            ip_target_days: Транзитное время в днях
            min_stock_days: Количество дней запаса
            
        Returns:
            Dict с результатами расчета минимальных запасов
        """
        if self.calculated_ads is None:
            return {'success': False, 'error': 'ADS не рассчитан. Сначала загрузите файл продаж.'}
        
        try:
            # Используем переданные параметры или значения по умолчанию
            ip_days = ip_target_days or self.default_params['ip_target_days']
            stock_days = min_stock_days or self.default_params['min_stock_days']
            
            df = self.calculated_ads.copy()
            
            # Рассчитываем компоненты минимального запаса
            df['ip_target_days'] = ip_days
            df['min_stock_days'] = stock_days
            
            # Транзитное потребление = ADS × транзитное время
            df['transit_consumption'] = df['ads'] * ip_days
            
            # Базовый минимальный запас = ADS × дни запаса  
            df['min_stock_base'] = df['ads'] * stock_days
            
            # Итоговый минимальный запас = базовый запас + транзитное потребление
            df['min_stock_total'] = df['min_stock_base'] + df['transit_consumption']
            
            # Добавляем статус и приоритет
            df['priority'] = df['ads'].apply(lambda x: 'Высокий' if x > df['ads'].quantile(0.8) else 
                                           'Средний' if x > df['ads'].quantile(0.5) else 'Низкий')
            
            self.calculated_min_stock = df
            
            return {
                'success': True,
                'total_items': len(df),
                'total_min_stock': df['min_stock_total'].sum(),
                'total_transit_consumption': df['transit_consumption'].sum(),
                'total_base_stock': df['min_stock_base'].sum(),
                'parameters': {
                    'ip_target_days': ip_days,
                    'min_stock_days': stock_days
                },
                'top_min_stock': df.nlargest(5, 'min_stock_total')[['номенклатура', 'min_stock_total', 'ads']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка расчета минимальных запасов: {str(e)}"}
    
    def load_current_stock_file(self, file_content) -> Dict:
        """
        Загрузка файла текущих остатков (ИСПРАВЛЕННАЯ ВЕРСИЯ для файла 08.07.2025)
        
        Args:
            file_content: Содержимое файла остатков
            
        Returns:
            Dict с информацией о загруженных остатках
        """
        try:
            # Читаем Excel файл БЕЗ заголовков - КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ!
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl', header=None)
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None)
            
            print(f"📊 Загружен файл: {df.shape[0]} строк x {df.shape[1]} колонок")
            
            # ИСПРАВЛЕНИЕ: Ищем строку с "Номенклатура" (обычно строка 7)
            header_row = None
            for i in range(min(15, len(df))):
                if pd.notna(df.iloc[i, 0]):
                    cell_value = str(df.iloc[i, 0]).strip().lower()
                    if 'номенклатура' in cell_value:
                        header_row = i
                        print(f"✅ Найдена строка заголовков: {i + 1}")
                        break
            
            # Если не нашли, используем строку 7 (индекс 6)
            if header_row is None:
                header_row = 6  # Строка 7 в Excel = индекс 6 в pandas
                print(f"⚠️ Используем строку заголовков по умолчанию: {header_row + 1}")
            
            # ИСПРАВЛЕНИЕ: Правильно извлекаем заголовки
            headers = []
            for col_idx in range(df.shape[1]):
                if pd.notna(df.iloc[header_row, col_idx]):
                    header_val = str(df.iloc[header_row, col_idx]).strip()
                    headers.append(header_val)
                else:
                    headers.append(f'col_{col_idx}')
            
            print(f"📋 Найдено заголовков: {len([h for h in headers if not h.startswith('col_')])}")
            
            # ИСПРАВЛЕНИЕ: Данные начинаются ПОСЛЕ строки заголовков
            data_start_row = header_row + 1
            df_data = df.iloc[data_start_row:].copy()
            
            # Устанавливаем заголовки
            df_data.columns = headers[:len(df_data.columns)]
            
            print(f"📊 Строк данных: {len(df_data)} (начиная со строки {data_start_row + 1})")
            
            # ИСПРАВЛЕНИЕ: Номенклатура всегда в первой колонке
            nomenclature_col = headers[0]
            df_data = df_data.rename(columns={nomenclature_col: 'номенклатура'})
            print(f"📝 Колонка номенклатуры: '{nomenclature_col}'")
            
            # ИСПРАВЛЕНИЕ: Ищем склады в колонках D-L (индексы 3-11), исключая "Итого"
            warehouse_columns = []
            warehouse_mapping = {}
            
            for col_idx in range(3, min(13, len(headers))):  # Колонки D-L
                if col_idx < len(headers):
                    col_name = headers[col_idx]
                    if pd.notna(col_name) and str(col_name).strip():
                        col_str = str(col_name).lower()
                        # ИСПРАВЛЕНИЕ: Исключаем "Итого"
                        if 'итого' not in col_str and 'total' not in col_str and len(col_str) > 3:
                            warehouse_columns.append(col_name)
                            # Создаем короткое имя для отображения
                            short_name = (str(col_name)
                                        .replace('Склад фурнитуры', 'Склад')
                                        .replace('Фурнитура', 'Фурн')
                                        .replace('TRADE', 'TR')[:25])
                            warehouse_mapping[col_name] = short_name
                            print(f"🏪 Склад: '{short_name}'")
            
            print(f"📊 Найдено складов: {len(warehouse_columns)}")
            
            # Очищаем данные
            initial_count = len(df_data)
            df_data = df_data.dropna(subset=['номенклатура'])
            df_data = df_data[df_data['номенклатура'].astype(str).str.strip() != '']
            df_data = df_data[df_data['номенклатура'].astype(str) != 'nan']
            print(f"📊 Очищено: {initial_count} -> {len(df_data)} строк")
            
            # ИСПРАВЛЕНИЕ: Преобразуем остатки в числовой формат
            for col in warehouse_columns:
                if col in df_data.columns:
                    df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0)
            
            # Рассчитываем общий остаток
            existing_warehouse_cols = [col for col in warehouse_columns if col in df_data.columns]
            if existing_warehouse_cols:
                df_data['total_current_stock'] = df_data[existing_warehouse_cols].sum(axis=1)
            else:
                df_data['total_current_stock'] = 0
            
            # Сохраняем данные
            self.stock_data = df_data
            self.warehouse_mapping = warehouse_mapping
            
            items_with_stock = len(df_data[df_data['total_current_stock'] > 0])
            total_stock = df_data['total_current_stock'].sum()
            
            print(f"✅ УСПЕШНО ЗАГРУЖЕНО:")
            print(f"  📊 Всего товаров: {len(df_data)}")
            print(f"  📊 С остатками: {items_with_stock}")
            print(f"  📊 Общий остаток: {total_stock:,.0f}")
            print(f"  📊 Складов: {len(existing_warehouse_cols)}")
            
            return {
                'success': True,
                'total_items': len(df_data),
                'warehouses_found': len(existing_warehouse_cols),
                'warehouse_list': list(warehouse_mapping.values()),
                'total_stock': total_stock,
                'items_with_stock': items_with_stock,
                'avg_stock': df_data['total_current_stock'].mean(),
                'top_stock': df_data.nlargest(5, 'total_current_stock')[['номенклатура', 'total_current_stock']].to_dict('records')
            }
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла остатков: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка загрузки файла остатков: {str(e)}"}
    
    def compare_stock_vs_min(self) -> Dict:
        """
        Сравнение текущих остатков с минимальными запасами
        
        Returns:
            Dict с результатами сравнения
        """
        if self.calculated_min_stock is None:
            return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
        
        if self.stock_data is None:
            return {'success': False, 'error': 'Текущие остатки не загружены'}
        
        try:
            # Объединяем данные по номенклатуре
            min_stock_df = self.calculated_min_stock.copy()
            current_stock_df = self.stock_data[['номенклатура', 'total_current_stock']].copy()
            
            # Merge данных
            comparison = pd.merge(
                min_stock_df,
                current_stock_df,
                on='номенклатура',
                how='left'
            )
            
            # Заполняем пропуски нулями
            comparison['total_current_stock'] = comparison['total_current_stock'].fillna(0)
            
            # Рассчитываем метрики сравнения
            comparison['stock_deficit'] = comparison['min_stock_total'] - comparison['total_current_stock']
            comparison['stock_deficit'] = comparison['stock_deficit'].apply(lambda x: max(0, x))
            
            if 'last_purchase_price' in comparison.columns:
                comparison['stock_deficit_money'] = comparison['stock_deficit'] * comparison['last_purchase_price']
                comparison['min_stock_money'] = comparison['min_stock_total'] * comparison['last_purchase_price']
                comparison['current_stock_money'] = comparison['total_current_stock'] * comparison['last_purchase_price']
            else:
                comparison['stock_deficit_money'] = 0
                comparison['min_stock_money'] = 0  
                comparison['current_stock_money'] = 0

            # Текущий запас в днях
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
            
            # Рекомендуемый заказ с учетом коэффициента безопасности
            safety_factor = self.default_params['safety_factor']
            comparison['recommended_order'] = comparison['stock_deficit'] * safety_factor
            comparison['recommended_order'] = comparison['recommended_order'].apply(lambda x: max(0, x))
            
            if 'last_purchase_price' in comparison.columns:
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
            
            
            # Сортировка по денежному дефициту если есть цены
            if 'stock_deficit_money' in comparison.columns and comparison['stock_deficit_money'].sum() > 0:
                priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
                comparison['status_priority'] = comparison['status'].map(priority_order)
                comparison = comparison.sort_values(['status_priority', 'stock_deficit_money'], ascending=[False, False])
                comparison = comparison.drop('status_priority', axis=1)
            else:
                # Обычная сортировка по количественному дефициту
                priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
                comparison['status_priority'] = comparison['status'].map(priority_order)
                comparison = comparison.sort_values(['status_priority', 'stock_deficit'], ascending=[False, False])
                comparison = comparison.drop('status_priority', axis=1)
            
            self.stock_comparison = comparison
            
            # Статистика результатов
            total_items = len(comparison)
            deficit_items = len(comparison[comparison['stock_deficit'] > 0])
            critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
            sufficient_items = len(comparison[comparison['status'] == 'ДОСТАТОЧНО'])
            
            total_deficit_value = comparison['stock_deficit'].sum()
            total_recommended_order = comparison['recommended_order'].sum()
            
            return {
                'success': True,
                'total_items': total_items,
                'deficit_items': deficit_items,
                'critical_items': critical_items,
                'sufficient_items': sufficient_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'total_deficit_value': total_deficit_value,
                'total_recommended_order': total_recommended_order,
                'top_deficit_items': comparison[comparison['stock_deficit'] > 0].head(10)[
                    ['номенклатура', 'stock_deficit', 'current_stock_days', 'status', 'order_priority']
                ].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка сравнения остатков: {str(e)}"}
    
    def get_system_status(self) -> Dict:
        """
        Получение статуса всей системы
        
        Returns:
            Dict со статусом всех модулей
        """
        status = {
            'abc_analysis': {
                'loaded': self.abc_data is not None,
                'analyzed': self.abc_results is not None,
                'items_count': len(self.abc_data) if self.abc_data is not None else 0
            },
            'sales_analysis': {
                'loaded': self.sales_data is not None or (hasattr(self, 'sales_files_data') and self.sales_files_data),
                'ads_calculated': self.calculated_ads is not None,
                'items_count': len(self.calculated_ads) if self.calculated_ads is not None else 0,
                'multiple_files': hasattr(self, 'sales_files_data') and bool(self.sales_files_data)
            },
            'min_stock_analysis': {
                'calculated': self.calculated_min_stock is not None,
                'items_count': len(self.calculated_min_stock) if self.calculated_min_stock is not None else 0
            },
            'stock_analysis': {
                'loaded': self.stock_data is not None,
                'compared': self.stock_comparison is not None,
                'items_count': len(self.stock_data) if self.stock_data is not None else 0
            },
            'subcategory_analysis': {
                'analyzed': hasattr(self, 'subcategory_results') and bool(self.subcategory_results),
                'subcategories_count': 0,
                'analyzer_loaded': hasattr(self, 'subcategory_analyzer')
            }
        }
        
        # Общий прогресс
        completed_steps = sum([
            status['abc_analysis']['analyzed'],
            status['sales_analysis']['ads_calculated'],
            status['min_stock_analysis']['calculated'],
            status['stock_analysis']['compared']
        ])
        
        status['overall'] = {
            'completed_steps': completed_steps,
            'total_steps': 4,
            'progress_percentage': (completed_steps / 4) * 100,
            'ready_for_export': completed_steps >= 2  # Минимум ADS + один из анализов
        }
        if status['subcategory_analysis']['analyzed']:
            subcategory_summary = self.get_subcategory_summary_report()
            if subcategory_summary and 'error' not in subcategory_summary:
                status['subcategory_analysis']['subcategories_count'] = subcategory_summary['total_subcategories']
        
        # Обновляем общий прогресс (теперь 5 этапов вместо 4)
        completed_steps = sum([
            status['abc_analysis']['analyzed'],
            status['sales_analysis']['ads_calculated'],
            status['min_stock_analysis']['calculated'],
            status['stock_analysis']['compared'],
            status['subcategory_analysis']['analyzed']  # НОВЫЙ этап
        ])
        
        status['overall'] = {
            'completed_steps': completed_steps,
            'total_steps': 5,  # Увеличиваем до 5
            'progress_percentage': (completed_steps / 5) * 100,
            'ready_for_export': completed_steps >= 2
        }
        
        return status
    
    def export_all_results(self) -> io.BytesIO:
        """
        Экспорт всех результатов в Excel файл
        
        Returns:
            io.BytesIO с Excel файлом
        """
        output = io.BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Общий статус системы
                status = self.get_system_status()
                status_df = pd.DataFrame([status['overall']])
                status_df.to_excel(writer, sheet_name='Общий_статус', index=False)
                
                # ABC анализ
                if self.abc_results is not None:
                    # Детальные данные ABC
                    abc_detailed = self.abc_results['abc_data_detailed']
                    abc_detailed.to_excel(writer, sheet_name='ABC_детально', index=False)
                    
                    # Анализ по категориям
                    if self.abc_results['category_analysis']:
                        category_df = pd.DataFrame.from_dict(
                            self.abc_results['category_analysis'], 
                            orient='index'
                        )
                        category_df.to_excel(writer, sheet_name='ABC_по_категориям', index=True)
                
                # ADS расчеты
                if self.calculated_ads is not None:
                    self.calculated_ads.to_excel(writer, sheet_name='ADS_расчет', index=False)
                
                # Данные по филиалам (если есть множественные файлы)
                if hasattr(self, 'sales_files_data') and self.sales_files_data:
                    branch_summary_data = []
                    for branch, result in self.sales_files_data.items():
                        if result['success']:
                            branch_summary_data.append({
                                'Филиал': branch,
                                'Товаров': result['total_items'],
                                'Общее_количество': result['total_quantity_sold'],
                                'ADS_филиала': result['total_ads'],
                                'Колонка_количества': result.get('quantity_column_used', 'неизвестно')
                            })
                    
                    if branch_summary_data:
                        branch_df = pd.DataFrame(branch_summary_data)
                        branch_df.to_excel(writer, sheet_name='Статистика_филиалов', index=False)
                
                # Объединенные данные по филиалам
                if hasattr(self, 'combined_sales_data') and self.combined_sales_data is not None:
                    self.combined_sales_data.to_excel(writer, sheet_name='Объединенные_продажи', index=False)
                
                # Минимальные запасы
                if self.calculated_min_stock is not None:
                    self.calculated_min_stock.to_excel(writer, sheet_name='Минимальные_запасы', index=False)
                
                # Текущие остатки
                if self.stock_data is not None:
                    stock_export = self.stock_data[['номенклатура', 'total_current_stock']].copy()
                    stock_export.to_excel(writer, sheet_name='Текущие_остатки', index=False)
                
                # Сравнение остатков
                if self.stock_comparison is not None:
                    # Полное сравнение
                    self.stock_comparison.to_excel(writer, sheet_name='Полное_сравнение', index=False)
                    
                    # Товары с дефицитом
                    deficit_items = self.stock_comparison[self.stock_comparison['stock_deficit'] > 0]
                    if not deficit_items.empty:
                        deficit_items.to_excel(writer, sheet_name='Товары_с_дефицитом', index=False)
                    
                    # Критичные товары
                    critical_items = self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО']
                    if not critical_items.empty:
                        critical_items.to_excel(writer, sheet_name='Критичные_товары', index=False)
                    
                    # Рекомендации по заказу
                    order_recommendations = self.stock_comparison[
                        self.stock_comparison['recommended_order'] > 0
                    ][['номенклатура', 'recommended_order', 'order_priority', 'ads', 'current_stock_days']]
                    
                    if not order_recommendations.empty:
                        order_recommendations = order_recommendations.sort_values('recommended_order', ascending=False)
                        order_recommendations.to_excel(writer, sheet_name='Рекомендации_заказа', index=False)
                if hasattr(self, 'subcategory_analyzer') and self.subcategory_analyzer.subcategory_results:
                    # Сводная таблица подкатегорий
                    subcategory_export_df = self.subcategory_analyzer.export_subcategory_analysis()
                    if not subcategory_export_df.empty:
                        subcategory_export_df.to_excel(writer, sheet_name='Подкатегории_ABC', index=False)
                    
                    # Парето-анализ подкатегорий
                    pareto_data = self.subcategory_analyzer.get_subcategory_pareto_analysis()
                    if pareto_data:
                        # A подкатегории
                        if pareto_data['pareto_80']:
                            a_df = pd.DataFrame(pareto_data['pareto_80'])
                            a_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_%', 'Категория', 'Товаров']
                            a_df.to_excel(writer, sheet_name='A_подкатегории', index=False)
                        
                        # B и C подкатегории
                        if pareto_data['pareto_95']:
                            b_df = pd.DataFrame(pareto_data['pareto_95'])
                            b_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_%', 'Категория', 'Товаров']
                            b_df.to_excel(writer, sheet_name='B_подкатегории', index=False)
                        
                        if pareto_data['pareto_100']:
                            c_df = pd.DataFrame(pareto_data['pareto_100'])
                            c_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_%', 'Категория', 'Товаров']
                            c_df.to_excel(writer, sheet_name='C_подкатегории', index=False)
                    
                    # Анализ по категориям
                    category_analysis = self.subcategory_analyzer.get_subcategory_analysis_by_category()
                    if category_analysis:
                        category_summary = []
                        for category, data in category_analysis.items():
                            category_summary.append({
                                'Категория': category,
                                'Подкатегорий': data['subcategories_count'],
                                'Товаров': data['total_items'],
                                'Продажи': data['total_sales'],
                                'A_товары': data['abc_distribution_total']['A'],
                                'B_товары': data['abc_distribution_total']['B'],
                                'C_товары': data['abc_distribution_total']['C']
                            })
                        
                        if category_summary:
                            category_df = pd.DataFrame(category_summary)
                            category_df.to_excel(writer, sheet_name='Категории_с_подкатегориями', index=False)

            output.seek(0)
            return output
            
        except Exception as e:
            raise Exception(f"Ошибка экспорта: {str(e)}")
    
    def create_visualizations(self) -> Dict:
        """
        Создание визуализаций для анализа
        
        Returns:
            Dict с объектами графиков Plotly
        """
        visualizations = {}
        
        try:
            # ABC анализ - распределение классов
            if self.abc_results is not None:
                abc_summary = self.abc_results['abc_summary']
                
                # Круговая диаграмма ABC классов
                fig_abc_pie = px.pie(
                    values=list(abc_summary.values()),
                    names=list(abc_summary.keys()),
                    title="Распределение товаров по ABC классам",
                    color_discrete_map={'A': '#ff4444', 'B': '#ffaa00', 'C': '#00aa44'}
                )
                visualizations['abc_distribution'] = fig_abc_pie
                
                # Парето-диаграмма
                abc_data = self.abc_results['abc_data_detailed']
                pareto_data = abc_data.head(50)  # Топ-50 для читаемости
                
                fig_pareto = go.Figure()
                
                # Столбцы продаж
                fig_pareto.add_trace(go.Bar(
                    x=list(range(len(pareto_data))),
                    y=pareto_data['annual_sales'],
                    name='Продажи',
                    marker_color='lightblue',
                    yaxis='y'
                ))
                
                # Линия накопительного процента
                fig_pareto.add_trace(go.Scatter(
                    x=list(range(len(pareto_data))),
                    y=pareto_data['cumulative_percentage'],
                    mode='lines+markers',
                    name='Накопительный %',
                    line=dict(color='red', width=2),
                    yaxis='y2'
                ))
                
                fig_pareto.update_layout(
                    title='Парето-анализ товаров (принцип 80/20)',
                    xaxis_title='Товары (ранжированные по продажам)',
                    yaxis=dict(title='Объем продаж', side='left'),
                    yaxis2=dict(title='Накопительный процент (%)', side='right', overlaying='y', range=[0, 100]),
                    showlegend=True
                )
                
                visualizations['pareto_analysis'] = fig_pareto
            
            # ADS анализ - топ товары
            if self.calculated_ads is not None:
                top_ads = self.calculated_ads.nlargest(20, 'ads')
                
                fig_ads = px.bar(
                    top_ads,
                    x='ads',
                    y='номенклатура',
                    orientation='h',
                    title='Топ-20 товаров по ADS (среднедневные продажи)',
                    labels={'ads': 'ADS', 'номенклатура': 'Товар'}
                )
                fig_ads.update_layout(height=600)
                visualizations['top_ads'] = fig_ads
            
            # Сравнение остатков - статусы товаров
            if self.stock_comparison is not None:
                status_counts = self.stock_comparison['status'].value_counts()
                
                fig_status = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title='Распределение товаров по статусам остатков',
                    labels={'x': 'Статус', 'y': 'Количество товаров'},
                    color=status_counts.index,
                    color_discrete_map={
                        'КРИТИЧНО': '#ff4444',
                        'НЕДОСТАТОК': '#ffaa00', 
                        'ДОСТАТОЧНО': '#00aa44'
                    }
                )
                visualizations['stock_status'] = fig_status
                
                # График дефицита по товарам
                deficit_data = self.stock_comparison[self.stock_comparison['stock_deficit'] > 0].head(20)
                
                if not deficit_data.empty:
                    fig_deficit = px.bar(
                        deficit_data,
                        x='stock_deficit',
                        y='номенклатура',
                        orientation='h',
                        title='Топ-20 товаров с наибольшим дефицитом',
                        labels={'stock_deficit': 'Дефицит', 'номенклатура': 'Товар'},
                        color='order_priority',
                        color_discrete_map={
                            'СРОЧНО': '#ff0000',
                            'ВЫСОКИЙ': '#ff8800',
                            'СРЕДНИЙ': '#ffcc00'
                        }
                    )
                    fig_deficit.update_layout(height=600)
                    visualizations['deficit_analysis'] = fig_deficit
            
            return visualizations
            
        except Exception as e:
            print(f"Ошибка создания визуализаций: {str(e)}")
            return {}
    
    def get_summary_report(self) -> Dict:
        """
        Получение итогового отчета по всем анализам
        
        Returns:
            Dict с итоговой сводкой
        """
        report = {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
            'system_status': self.get_system_status()
        }
        
        # ABC анализ сводка
        if self.abc_results is not None:
            abc_summary = self.abc_results['abc_summary']
            total_abc_items = sum(abc_summary.values())
            
            report['abc_analysis'] = {
                'total_items': total_abc_items,
                'total_sales': self.abc_results['total_sales'],
                'distribution': {
                    'A_items': abc_summary.get('A', 0),
                    'A_percentage': (abc_summary.get('A', 0) / total_abc_items) * 100,
                    'B_items': abc_summary.get('B', 0),
                    'B_percentage': (abc_summary.get('B', 0) / total_abc_items) * 100,
                    'C_items': abc_summary.get('C', 0),
                    'C_percentage': (abc_summary.get('C', 0) / total_abc_items) * 100
                },
                'categories_analyzed': len(self.abc_results['category_analysis'])
            }
        
        # ADS анализ сводка
        if self.calculated_ads is not None:
            # Проверяем, какие колонки есть в данных
            ads_columns = self.calculated_ads.columns.tolist()
            
            report['ads_analysis'] = {
                'total_items': len(self.calculated_ads),
                'total_ads': self.calculated_ads['ads'].sum(),
                'avg_ads': self.calculated_ads['ads'].mean()
            }
            
            # Добавляем дополнительные метрики, если колонки существуют
            if 'total_quantity_sold' in ads_columns:
                report['ads_analysis']['total_quantity_sold'] = self.calculated_ads['total_quantity_sold'].sum()
            
            if 'total_sales' in ads_columns:
                report['ads_analysis']['total_sales_period'] = self.calculated_ads['total_sales'].sum()
            
            # Топ товар по ADS
            top_ads_idx = self.calculated_ads['ads'].idxmax()
            report['ads_analysis']['top_seller'] = {
                'item': self.calculated_ads.loc[top_ads_idx, 'номенклатура'],
                'ads_value': self.calculated_ads.loc[top_ads_idx, 'ads']
            }
            
            # Добавляем информацию о множественных файлах, если есть
            if hasattr(self, 'sales_files_data') and self.sales_files_data:
                report['ads_analysis']['files_processed'] = len(self.sales_files_data)
                successful_files = sum(1 for r in self.sales_files_data.values() if r['success'])
                report['ads_analysis']['successful_files'] = successful_files
        
        # Минимальные запасы сводка
        if self.calculated_min_stock is not None:
            report['min_stock_analysis'] = {
                'total_items': len(self.calculated_min_stock),
                'total_min_stock': self.calculated_min_stock['min_stock_total'].sum(),
                'total_transit_consumption': self.calculated_min_stock['transit_consumption'].sum(),
                'parameters': {
                    'ip_days': self.calculated_min_stock['ip_target_days'].iloc[0],
                    'stock_days': self.calculated_min_stock['min_stock_days'].iloc[0]
                }
            }
        
        # Сравнение остатков сводка
        if self.stock_comparison is not None:
            total_items = len(self.stock_comparison)
            deficit_items = len(self.stock_comparison[self.stock_comparison['stock_deficit'] > 0])
            critical_items = len(self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'])
            
            report['stock_comparison'] = {
                'total_items': total_items,
                'deficit_items': deficit_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'critical_items': critical_items,
                'critical_percentage': (critical_items / total_items) * 100,
                'total_deficit_value': self.stock_comparison['stock_deficit'].sum(),
                'total_recommended_order': self.stock_comparison['recommended_order'].sum(),
                'priority_distribution': self.stock_comparison['order_priority'].value_counts().to_dict()
            }
        if hasattr(self, 'subcategory_results') and self.subcategory_results:
            subcategory_summary = self.get_subcategory_summary_report()
            
            if subcategory_summary and 'error' not in subcategory_summary:
                report['subcategory_analysis'] = {
                    'total_subcategories': subcategory_summary['total_subcategories'],
                    'efficient_subcategories': subcategory_summary['efficient_subcategories'],
                    'efficiency_percentage': subcategory_summary['efficiency_percentage'],
                    'categories_with_subcategories': subcategory_summary['categories_analyzed'],
                    'avg_items_per_subcategory': subcategory_summary['average_items_per_subcategory'],
                    'subcategory_abc_distribution': subcategory_summary['abc_distribution']
                }

        return report
    
    def clear_all_data(self):
        """Очистка всех загруженных данных и результатов"""
        self.abc_data = None
        self.sales_data = None
        self.stock_data = None
        self.abc_results = None
        self.calculated_ads = None
        self.calculated_min_stock = None
        self.stock_comparison = None
    
    def update_parameters(self, **kwargs):
        """
        Обновление параметров системы
        
        Args:
            **kwargs: Параметры для обновления (ip_target_days, min_stock_days, safety_factor)
        """
        for key, value in kwargs.items():
            if key in self.default_params:
                self.default_params[key] = value
    
    def get_russian_columns_mapping(self):
        """Получение маппинга колонок для русификации"""
        return {
            # ABC анализ
            'nomenclature': 'Номенклатура',
            'category': 'Категория',
            'subcategory': 'Подкатегория', 
            'annual_sales': 'Годовые продажи',
            'abc_class': 'ABC класс',
            'sales_percentage': 'Процент продаж (%)',
            'cumulative_percentage': 'Накопительный процент (%)',
            
            # ADS расчеты
            'ads': 'Среднедневные продажи',
            'total_sales': 'Общие продажи',
            'average_value': 'Среднемесячные продажи',
            
            # Минимальные запасы
            'min_stock_total': 'Минимальный запас',
            'min_stock_base': 'Базовый минимум',
            'transit_consumption': 'Транзитное потребление',
            'ip_target_days': 'Дни транзита',
            'min_stock_days': 'Дни запаса',
            'priority': 'Приоритет',
            
            # Остатки и сравнение
            'total_current_stock': 'Текущий остаток',
            'stock_deficit': 'Дефицит',
            'current_stock_days': 'Дни остатка',
            'status': 'Статус',
            'recommended_order': 'Рекомендуемый заказ',
            'order_priority': 'Приоритет заказа',
            
            # Заказы по филиалам
            'branch': 'Филиал',
            'pre_order': 'Предзаказ', 
            'need': 'Потребность',
            'days_supply': 'Дни запаса',
            'active_assortment': 'Активный ассортимент'
        }

    def export_russian_dataframes(self):
        """Экспорт всех DataFrame с русскими заголовками"""
        russian_mapping = self.get_russian_columns_mapping()
        
        results = {}
        
        if self.calculated_ads is not None:
            results['ADS_расчеты'] = self.calculated_ads.rename(columns=russian_mapping)
        
        if self.abc_results is not None and 'abc_data_detailed' in self.abc_results:
            results['ABC_детально'] = self.abc_results['abc_data_detailed'].rename(columns=russian_mapping)
        
        if self.calculated_min_stock is not None:
            results['Минимальные_запасы'] = self.calculated_min_stock.rename(columns=russian_mapping)
        
        if self.stock_comparison is not None:
            results['Сравнение_остатков'] = self.stock_comparison.rename(columns=russian_mapping)
        
        return results

    def get_recommendations(self) -> List[str]:
        """
        Получение рекомендаций по улучшению системы
        
        Returns:
            List рекомендаций
        """
        recommendations = []
        
        status = self.get_system_status()
        
        # Проверяем полноту анализа
        if not status['abc_analysis']['analyzed']:
            recommendations.append("Выполните ABC анализ для лучшей классификации товаров")
        
        if not status['sales_analysis']['ads_calculated']:
            recommendations.append("Загрузите данные продаж для расчета ADS")
        
        if not status['min_stock_analysis']['calculated']:
            recommendations.append("Рассчитайте минимальные запасы на основе ADS")
        
        if not status['stock_analysis']['compared']:
            recommendations.append("Загрузите текущие остатки для сравнения с минимальными запасами")
        
        # Анализируем результаты сравнения
        if self.stock_comparison is not None:
            critical_count = len(self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'])
            total_count = len(self.stock_comparison)
            
            if critical_count > total_count * 0.1:  # Более 10% критичных товаров
                recommendations.append(f"Критическая ситуация: {critical_count} товаров требуют срочного пополнения")
            
            deficit_count = len(self.stock_comparison[self.stock_comparison['stock_deficit'] > 0])
            if deficit_count > total_count * 0.3:  # Более 30% товаров с дефицитом
                recommendations.append("Рассмотрите увеличение частоты заказов или коэффициента безопасности")
        
        # ABC анализ рекомендации
        if self.abc_results is not None:
            abc_summary = self.abc_results['abc_summary']
            total_items = sum(abc_summary.values())
            a_percentage = (abc_summary.get('A', 0) / total_items) * 100
            
            if a_percentage < 15:
                recommendations.append("Низкая доля A товаров - проверьте ассортиментную политику")
            elif a_percentage > 25:
                recommendations.append("Высокая доля A товаров - возможно избыточная концентрация продаж")
        
        if not recommendations:
            recommendations.append("Система настроена оптимально. Регулярно обновляйте данные.")
        
        return recommendations