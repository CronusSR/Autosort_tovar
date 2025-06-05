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

    def initialize_subcategory_analyzer(self):
        """Инициализация анализатора подкатегорий"""
        if not hasattr(self, 'subcategory_analyzer'):
            self.subcategory_analyzer = SubcategoryABCAnalyzer()
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
        
    def fix_zero_ads_with_category_average(self):
        """
        Простая функция для заполнения товаров с ADS=0 средним ADS по категории
        Добавьте этот метод в класс ModularInventorySystem
        """
        if self.calculated_ads is None:
            print("❌ ADS не рассчитан")
            return False
        
        # Проверяем есть ли товары с нулевым ADS
        zero_ads_items = self.calculated_ads[self.calculated_ads['ads'] == 0]
        if len(zero_ads_items) == 0:
            print("✅ Все товары имеют положительный ADS")
            return True
        
        print(f"🔄 Найдено {len(zero_ads_items)} товаров с ADS=0")
        
        # Если есть ABC данные с категориями
        if self.abc_results is not None and 'abc_data_detailed' in self.abc_results:
            abc_data = self.abc_results['abc_data_detailed']
            
            # Объединяем ADS с категориями
            merged_data = pd.merge(
                self.calculated_ads,
                abc_data[['nomenclature', 'category']],
                left_on='номенклатура',
                right_on='nomenclature',
                how='left'
            )
            
            # Заполняем пропущенные категории
            merged_data['category'] = merged_data['category'].fillna('Без категории')
            
            # Рассчитываем средний ADS по категориям (только для товаров с ADS > 0)
            category_avg = merged_data[merged_data['ads'] > 0].groupby('category')['ads'].mean()
            
            corrections_made = 0
            
            # Исправляем товары с ADS = 0
            for idx, row in merged_data.iterrows():
                if row['ads'] == 0:
                    category = row['category']
                    
                    if category in category_avg and category_avg[category] > 0:
                        # Используем 80% от среднего по категории (консервативный подход)
                        new_ads = category_avg[category] * 0.8
                        merged_data.at[idx, 'ads'] = new_ads
                        corrections_made += 1
                    else:
                        # Если в категории нет товаров с ADS > 0, используем общий средний
                        overall_avg = merged_data[merged_data['ads'] > 0]['ads'].mean()
                        if pd.notna(overall_avg) and overall_avg > 0:
                            new_ads = overall_avg * 0.5  # 50% от общего среднего
                            merged_data.at[idx, 'ads'] = new_ads
                            corrections_made += 1
            
            # Обновляем данные в системе
            self.calculated_ads = merged_data[['номенклатура', 'ads', 'average_value', 'total_sales']].copy()
            
            # Пересчитываем минимальные запасы если они были рассчитаны
            if self.calculated_min_stock is not None:
                print("🔄 Пересчитываем минимальные запасы...")
                self.calculate_min_stock()
            
            print(f"✅ Исправлено {corrections_made} товаров")
            return True
        
        else:
            print("⚠️ ABC данные недоступны, корректировка невозможна")
            return False


    def apply_ads_category_fix_to_system(system):
        """
        Простая функция для добавления метода в существующую систему
        Используйте так: apply_ads_category_fix_to_system(ваша_система)
        """
        # Добавляем метод в экземпляр класса
        import types
        system.fix_zero_ads_with_category_average = types.MethodType(fix_zero_ads_with_category_average, system)
        
        print("✅ Функция исправления ADS добавлена в систему")
        print("   Используйте: system.fix_zero_ads_with_category_average()")


    

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
        try:
            print("🔄 Обработка ADS файла с ценами из колонки 12 'Посл. закупка'...")
        
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
            print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # ИСПРАВЛЕННЫЕ параметры
            start_col_index = 12  # Колонка M (продажи)
            end_col_index = 28    # Колонка AB+1 (не включается)
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (индекс 1)
            price_col = 11        # Колонка 12 "Посл. закупка" (индекс 11) ← НОВОЕ
            
            print(f"📋 ОБНОВЛЕННАЯ ЛОГИКА:")
            print(f"   • Номенклатура: Колонка B (индекс {nomenclature_col})")
            print(f"   • Данные продаж: колонки {start_col_index}:{end_col_index} (M:AB)")
            print(f"   • Цены: Колонка 12 (индекс {price_col}) - 'Посл. закупка'")  # ← НОВОЕ
            print(f"   • Начальная строка: {start_row+1}")
            
            # Проверяем достаточность колонок
            required_columns = max(end_col_index, price_col + 1)
            if df.shape[1] < required_columns:
                return {
                    'success': False,
                    'error': f'Недостаточно колонок в файле. Нужно минимум {required_columns}, есть {df.shape[1]}'
                }
            
            # Получаем номенклатуру из колонки B (индекс 1)
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
            
            # НОВОЕ: Получаем цены из колонки 12 (индекс 11)
            price_data = df.iloc[start_row:, price_col].copy()
            
            # Очищаем номенклатуру
            print("🧹 Очистка номенклатуры из колонки B...")
            initial_count = len(nomenclature_data)
            
            nomenclature_clean = nomenclature_data.dropna()
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            
            # Исключаем последнюю строчку
            if len(nomenclature_clean) > 0:
                nomenclature_clean = nomenclature_clean[:-1]
                print("✅ Исключена последняя строчка")
            
            valid_indices = nomenclature_clean.index
            print(f"📊 После очистки: {len(nomenclature_clean)} товаров (было {initial_count})")
            
            if len(nomenclature_clean) == 0:
                return {
                    'success': False,
                    'error': 'Нет валидных товаров после очистки номенклатуры из колонки B'
                }
            
            # НОВОЕ: Обрабатываем цены
            print("💰 Обработка цен из колонки 12...")
            
            # Извлекаем цены для валидных индексов
            price_clean = price_data.loc[valid_indices].copy()
            
            # Преобразуем цены в числовой формат
            price_clean = pd.to_numeric(price_clean, errors='coerce').fillna(0)
            price_clean = price_clean.apply(lambda x: max(0, x))  # Убираем отрицательные
            
            # Статистика по ценам
            price_stats = {
                'items_with_price': len(price_clean[price_clean > 0]),
                'items_without_price': len(price_clean[price_clean == 0]),
                'average_price': price_clean[price_clean > 0].mean() if len(price_clean[price_clean > 0]) > 0 else 0,
                'max_price': price_clean.max(),
                'min_price': price_clean[price_clean > 0].min() if len(price_clean[price_clean > 0]) > 0 else 0
            }
            
            print(f"💰 Статистика цен:")
            print(f"   - С ценой > 0: {price_stats['items_with_price']}")
            print(f"   - Без цены: {price_stats['items_without_price']}")
            print(f"   - Средняя цена: {price_stats['average_price']:,.2f}")
            print(f"   - Макс цена: {price_stats['max_price']:,.2f}")
            
            # Извлекаем данные продаж из диапазона M:AB
            print("📈 Извлечение данных из диапазона M4:AB...")
            
            sales_data_list = []
            
            for idx in valid_indices:
                item_name = str(nomenclature_clean.loc[idx]).strip()
                item_price = float(price_clean.loc[idx])  # НОВОЕ: цена товара
                
                # Извлекаем данные из колонок M:AB для данной строки
                row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                
                # Преобразуем в числовой формат, заменяя NaN и пустые на 0
                row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                
                # ФОРМУЛА РАСЧЕТА ADS:
                # 1. Получаем среднее значение от M4:AB4
                average_value = row_sales_numeric.mean()
                
                # 2. Делим среднее значение на 30
                ads_value = average_value / 30
                
                sales_data_list.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_sales_numeric.sum(),
                    'last_purchase_price': item_price,  # НОВОЕ: добавляем цену
                    'monthly_data': row_sales_numeric.tolist()
                })
            
            # Создаем DataFrame
            ads_df = pd.DataFrame(sales_data_list)
            
            # Сохраняем результаты в системе
            self.sales_data = ads_df
            self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales', 'last_purchase_price']].copy()
            
            # Создаем JSON данные для системы
            json_output = {
                'metadata': {
                    'file_processed_at': pd.Timestamp.now().isoformat(),
                    'total_items': len(ads_df),
                    'nomenclature_column': 'B',
                    'price_column': '12 (Посл. закупка)',  # НОВОЕ
                    'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                    'calculation_method': 'average_monthly_divided_by_30_with_prices',
                    'formula': 'ADS = (среднее от M4:AB4) / 30',
                    'last_row_excluded': True,
                    'price_data_included': True  # НОВОЕ
                },
                'summary_stats': {
                    'total_ads': float(ads_df['ads'].sum()),
                    'average_ads': float(ads_df['ads'].mean()),
                    'max_ads': float(ads_df['ads'].max()),
                    'min_ads': float(ads_df['ads'].min()),
                    # НОВОЕ: статистика цен
                    'total_inventory_value': float((ads_df['ads'] * ads_df['last_purchase_price'] * 30).sum()),
                    'average_price': float(price_stats['average_price']),
                    'items_with_price': price_stats['items_with_price'],
                    'price_coverage_percentage': (price_stats['items_with_price'] / len(ads_df)) * 100
                },
                'items': [
                    {
                        'nomenclature': row['номенклатура'],
                        'ads_daily': row['ads'],
                        'average_monthly': row['average_value'],
                        'total_period': row['total_sales'],
                        'last_purchase_price': row['last_purchase_price'],  # НОВОЕ
                        'monthly_data': row['monthly_data']
                    }
                    for _, row in ads_df.iterrows()
                ]
            }
            
            # Сохраняем JSON в системе
            if not hasattr(self, '_json_data'):
                self._json_data = {}
            self._json_data['ads'] = json_output
            
            # Статистика
            positive_ads_count = len(ads_df[ads_df['ads'] > 0])
            
            print(f"\n📊 РЕЗУЛЬТАТЫ С ЦЕНАМИ:")
            print("=" * 60)
            print(f"Номенклатура читается из: Колонка B")
            print(f"Цены читаются из: Колонка 12 (Посл. закупка)")  # НОВОЕ
            print(f"Обработано товаров: {len(ads_df)}")
            print(f"Диапазон: M{start_row+1}:AB{start_row+1+len(ads_df)}")
            print(f"Формула: ADS = (среднее месячное) / 30")
            print(f"Общий ADS: {ads_df['ads'].sum():.2f}")
            print(f"Средний ADS: {ads_df['ads'].mean():.4f}")
            print(f"Товаров с положительным ADS: {positive_ads_count}")
            print(f"Товаров с ценами: {price_stats['items_with_price']}")  # НОВОЕ
            print(f"Общая стоимость запасов (месяц): {json_output['summary_stats']['total_inventory_value']:,.0f}")  # НОВОЕ
            
            # Топ товары
            print(f"\n🏆 Топ-5 товаров по новому ADS:")
            top_sellers = ads_df.nlargest(5, 'ads')
            for i, (_, row) in enumerate(top_sellers.iterrows(), 1):
                price_info = f" (цена: {row['last_purchase_price']:,.2f})" if row['last_purchase_price'] > 0 else " (без цены)"
                print(f"  {i}. {row['номенклатура'][:50]:<50} | ADS: {row['ads']:>8.4f}{price_info}")
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'nomenclature_column': 'B',
                'price_column': '12 (Посл. закупка)',  # НОВОЕ
                'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                'calculation_method': 'average_monthly_divided_by_30_with_prices',
                'formula': 'ADS = (среднее от M4:AB4) / 30',
                'total_ads': ads_df['ads'].sum(),
                'average_ads': ads_df['ads'].mean(),
                'items_with_positive_ads': positive_ads_count,
                'json_data_created': True,
                'last_row_excluded': True,
                # НОВОЕ: информация о ценах
                'price_data_loaded': True,
                'items_with_price': price_stats['items_with_price'],
                'items_without_price': price_stats['items_without_price'],
                'average_price': price_stats['average_price'],
                'total_inventory_value': json_output['summary_stats']['total_inventory_value'],
                'price_coverage_percentage': (price_stats['items_with_price'] / len(ads_df)) * 100
            }
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка загрузки файла ADS с ценами: {str(e)}"}
    
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
        ОБНОВЛЕННАЯ загрузка ABC файла с ценами из колонки 12
        """
        try:
            print("🔄 Загрузка ABC файла с ценами из колонки 'Посл. закупка'...")
            
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
            
            # ОБНОВЛЕННОЕ назначение колонок с ценой
            if len(df.columns) >= 13:  # Нужно минимум 13 колонок для цены в колонке 12
                df.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + \
                            [f'extra_col_{i}' for i in range(4, 12)] + \
                            ['last_purchase_price'] + \
                            [f'extra_col_{i}' for i in range(13, len(df.columns))]
            elif len(df.columns) >= 4:
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
            
            # Обработка продаж
            before_sales = len(df)
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')
            nan_count = df['annual_sales'].isna().sum()
            df['annual_sales'] = df['annual_sales'].fillna(0)
            df.loc[df['annual_sales'] < 0, 'annual_sales'] = 0
            print(f"💰 NaN в продажах заменено на 0: {nan_count}")
            
            # НОВОЕ: Обработка цен из колонки 12
            if 'last_purchase_price' in df.columns:
                print("💰 Обрабатываем цены из колонки 'Посл. закупка'...")
                
                # Преобразуем цены в числовой формат
                df['last_purchase_price'] = pd.to_numeric(df['last_purchase_price'], errors='coerce')
                
                # Заменяем NaN и отрицательные цены на 0
                price_nan_count = df['last_purchase_price'].isna().sum()
                df['last_purchase_price'] = df['last_purchase_price'].fillna(0)
                df.loc[df['last_purchase_price'] < 0, 'last_purchase_price'] = 0
                
                # Статистика по ценам
                price_stats = {
                    'items_with_price': len(df[df['last_purchase_price'] > 0]),
                    'items_without_price': len(df[df['last_purchase_price'] == 0]),
                    'average_price': df[df['last_purchase_price'] > 0]['last_purchase_price'].mean() if len(df[df['last_purchase_price'] > 0]) > 0 else 0,
                    'max_price': df['last_purchase_price'].max(),
                    'nan_replaced': price_nan_count
                }
                
                print(f"💰 Статистика цен:")
                print(f"   - С ценой > 0: {price_stats['items_with_price']}")
                print(f"   - Без цены: {price_stats['items_without_price']}")
                print(f"   - Средняя цена: {price_stats['average_price']:,.2f}")
                print(f"   - NaN заменено на 0: {price_stats['nan_replaced']}")
                
            else:
                # Если колонки с ценой нет, создаем с нулями
                df['last_purchase_price'] = 0
                print("⚠️ Колонка 'Посл. закупка' не найдена, цены установлены в 0")
                price_stats = {
                    'items_with_price': 0,
                    'items_without_price': len(df),
                    'average_price': 0,
                    'max_price': 0,
                    'nan_replaced': 0
                }
            
            # Обработка категорий
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
            print(f"   С ценами > 0: {price_stats['items_with_price']}")
            print(f"   Дубликатов удалено: {duplicates_count}")
            
            return {
                'success': True,
                'total_items': final_count,
                'items_with_sales': positive_sales,
                'items_with_zero_sales': zero_sales,
                'items_with_price': price_stats['items_with_price'],
                'items_without_price': price_stats['items_without_price'],
                'average_price': price_stats['average_price'],
                'categories': df['category'].nunique(),
                'total_sales': float(df['annual_sales'].sum()),
                'average_sales': float(df['annual_sales'].mean()),
                'sheet_used': target_sheet,
                'duplicates_removed': duplicates_count,
                'zero_sales_included': True,
                'price_data_loaded': True
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
            df.columns = [str(col).lower().strip() if pd.notna(col) else f'col_{i}' for i, col in enumerate(df.columns)]
            
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
        Загрузка файла текущих остатков
        
        Args:
            file_content: Содержимое файла остатков
            
        Returns:
            Dict с информацией о загруженных остатках
        """
        try:
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # Ищем заголовки
            header_row = None
            for i, row in df.iterrows():
                row_str = str(row.iloc[0]).lower()
                if pd.notna(row.iloc[0]) and any(word in row_str for word in ['номенклатура', 'наименование', 'товар']):
                    header_row = i
                    break
            
            if header_row is not None:
                headers = df.iloc[header_row].tolist()
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
            
            # Стандартизируем названия колонок
            df.columns = [str(col).lower().strip() if pd.notna(col) else f'col_{i}' for i, col in enumerate(df.columns)]
            
            # Ищем колонку номенклатуры
            nomenclature_col = None
            for col in df.columns:
                if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                    nomenclature_col = col
                    break
            
            if nomenclature_col is None:
                nomenclature_col = df.columns[0]
            
            df = df.rename(columns={nomenclature_col: 'номенклатура'})
            
            # Ищем колонки с остатками
            stock_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(word in col_str for word in ['остаток', 'stock', 'balance', 'склад', 'количество']):
                    stock_columns.append(col)
                # Также проверяем числовые колонки (кроме номенклатуры)
                elif col != 'номенклатура':
                    try:
                        # Проверяем, содержит ли колонка числовые данные
                        numeric_data = pd.to_numeric(df[col], errors='coerce')
                        if not numeric_data.isna().all():
                            stock_columns.append(col)
                    except:
                        continue
            
            # Очищаем данные
            df = df.dropna(subset=['номенклатура'])
            df = df[df['номенклатура'].astype(str).str.strip() != '']
            df = df[df['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем остатки в числовой формат
            for col in stock_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Рассчитываем общий остаток
            if stock_columns:
                df['total_current_stock'] = df[stock_columns].sum(axis=1)
            else:
                df['total_current_stock'] = 0
            
            self.stock_data = df
            
            return {
                'success': True,
                'total_items': len(df),
                'stock_columns_found': len(stock_columns),
                'total_stock': df['total_current_stock'].sum(),
                'items_with_stock': len(df[df['total_current_stock'] > 0]),
                'avg_stock': df['total_current_stock'].mean(),
                'top_stock': df.nlargest(5, 'total_current_stock')[['номенклатура', 'total_current_stock']].to_dict('records')
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка загрузки файла остатков: {str(e)}"}
    
    def compare_stock_vs_min(self) -> Dict:
        """
        ОБНОВЛЕННОЕ сравнение остатков с использованием цен из ADS данных
        """
        if self.calculated_ads is None:
            return {'success': False, 'error': 'Минимальные запасы не рассчитаны'}
        
        if self.stock_data is None:
            return {'success': False, 'error': 'Текущие остатки не загружены'}
        
        try:
            # Объединяем данные по номенклатуре
            min_stock_df = self.calculated_min_stock.copy()
            current_stock_df = self.stock_data[['номенклатура', 'total_current_stock']].copy()
            
            # ИЗМЕНЕНО: Добавляем информацию о ценах из ADS данных (вместо ABC)
            if (self.calculated_ads is not None and 
                'last_purchase_price' in self.calculated_ads.columns):
                
                price_df = self.calculated_ads[['номенклатура', 'last_purchase_price']].copy()
                
                # Merge с ценами из ADS
                min_stock_df = pd.merge(
                    min_stock_df,
                    price_df,
                    on='номенклатура',
                    how='left'
                )
                
                # Заполняем отсутствующие цены нулями
                min_stock_df['last_purchase_price'] = min_stock_df['last_purchase_price'].fillna(0)
                
                print(f"💰 Добавлены цены из ADS: {len(min_stock_df[min_stock_df['last_purchase_price'] > 0])} товаров с ценой")
                
            else:
                # Если цен нет, устанавливаем 0
                min_stock_df['last_purchase_price'] = 0
                print("⚠️ Цены не найдены в ADS данных, денежные расчеты будут равны 0")
            
            # Merge с остатками
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
            
            # ДЕНЕЖНОЕ ВЫРАЖЕНИЕ дефицита
            comparison['stock_deficit_money'] = comparison['stock_deficit'] * comparison['last_purchase_price']
            
            # Денежное выражение минимального запаса
            comparison['min_stock_money'] = comparison['min_stock_total'] * comparison['last_purchase_price']
            
            # Денежное выражение текущего остатка
            comparison['current_stock_money'] = comparison['total_current_stock'] * comparison['last_purchase_price']
            
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
            
            # Денежное выражение рекомендуемого заказа
            comparison['recommended_order_money'] = comparison['recommended_order'] * comparison['last_purchase_price']
            
            # Приоритет заказа
            comparison['order_priority'] = comparison.apply(
                lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                           else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                           else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                           else 'НЕ ТРЕБУЕТСЯ', axis=1
            )
            
            # Сортируем по критичности и денежному дефициту
            priority_order = {'КРИТИЧНО': 4, 'НЕДОСТАТОК': 3, 'ДОСТАТОЧНО': 2}
            comparison['status_priority'] = comparison['status'].map(priority_order)
            comparison = comparison.sort_values(['status_priority', 'stock_deficit_money'], ascending=[False, False])
            comparison = comparison.drop('status_priority', axis=1)
            
            self.stock_comparison = comparison
            
            # Статистика результатов
            total_items = len(comparison)
            deficit_items = len(comparison[comparison['stock_deficit'] > 0])
            critical_items = len(comparison[comparison['status'] == 'КРИТИЧНО'])
            sufficient_items = len(comparison[comparison['status'] == 'ДОСТАТОЧНО'])
            
            total_deficit_value = comparison['stock_deficit'].sum()
            total_deficit_money = comparison['stock_deficit_money'].sum()
            total_recommended_order = comparison['recommended_order'].sum()
            total_recommended_order_money = comparison['recommended_order_money'].sum()
            
            # Статистика по товарам с ценами
            items_with_price = len(comparison[comparison['last_purchase_price'] > 0])
            deficit_items_with_price = len(comparison[
                (comparison['stock_deficit'] > 0) & 
                (comparison['last_purchase_price'] > 0)
            ])
            
            print(f"\n💰 ДЕНЕЖНАЯ СТАТИСТИКА (из ADS файла):")
            print(f"   Общий дефицит в деньгах: {total_deficit_money:,.2f}")
            print(f"   Рекомендуемый заказ в деньгах: {total_recommended_order_money:,.2f}")
            print(f"   Товаров с ценами: {items_with_price}/{total_items}")
            print(f"   Дефицитных товаров с ценами: {deficit_items_with_price}/{deficit_items}")
            
            return {
                'success': True,
                'total_items': total_items,
                'deficit_items': deficit_items,
                'critical_items': critical_items,
                'sufficient_items': sufficient_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'total_deficit_value': total_deficit_value,
                'total_deficit_money': total_deficit_money,
                'total_recommended_order': total_recommended_order,
                'total_recommended_order_money': total_recommended_order_money,
                'items_with_price': items_with_price,
                'deficit_items_with_price': deficit_items_with_price,
                'price_coverage_percentage': (items_with_price / total_items) * 100 if total_items > 0 else 0,
                'price_source': 'ADS_file',  # НОВОЕ: указываем источник цен
                'top_deficit_items': comparison[comparison['stock_deficit'] > 0].head(10)[
                    ['номенклатура', 'stock_deficit', 'stock_deficit_money', 'current_stock_days', 'status', 'order_priority']
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
        ОБНОВЛЕННЫЙ экспорт всех результатов с денежными расчетами
        """
        output = io.BytesIO()
        
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Общий статус системы
                status = self.get_system_status()
                status_df = pd.DataFrame([status['overall']])
                status_df.to_excel(writer, sheet_name='Общий_статус', index=False)
                
                # ABC анализ с ценами
                if self.abc_results is not None:
                    # Детальные данные ABC с ценами
                    abc_detailed = self.abc_results['abc_data_detailed'].copy()
                    
                    # Переименовываем колонки для русского интерфейса
                    abc_columns_mapping = {
                        'nomenclature': 'Номенклатура',
                        'category': 'Категория',
                        'subcategory': 'Подкатегория',
                        'annual_sales': 'Годовые_продажи',
                        'abc_class': 'ABC_класс',
                        'sales_percentage': 'Процент_продаж',
                        'cumulative_percentage': 'Накопительный_процент',
                        'last_purchase_price': 'Последняя_цена_закупки'
                    }
                    
                    existing_columns = {k: v for k, v in abc_columns_mapping.items() if k in abc_detailed.columns}
                    abc_detailed = abc_detailed.rename(columns=existing_columns)
                    
                    abc_detailed.to_excel(writer, sheet_name='ABC_детально_с_ценами', index=False)
                    
                    # Анализ по категориям
                    if self.abc_results['category_analysis']:
                        category_df = pd.DataFrame.from_dict(
                            self.abc_results['category_analysis'], 
                            orient='index'
                        )
                        category_df.to_excel(writer, sheet_name='ABC_по_категориям', index=True)
                
                # ADS расчеты
                if self.calculated_ads is not None:
                    ads_export = self.calculated_ads.copy()
                    
                    # Добавляем цены к ADS данным если есть ABC данные
                    if (self.abc_data is not None and 
                        'last_purchase_price' in self.abc_data.columns):
                        
                        price_mapping = self.abc_data[['nomenclature', 'last_purchase_price']].copy()
                        price_mapping = price_mapping.rename(columns={'nomenclature': 'номенклатура'})
                        
                        ads_export = pd.merge(
                            ads_export,
                            price_mapping,
                            on='номенклатура',
                            how='left'
                        )
                        
                        ads_export['last_purchase_price'] = ads_export['last_purchase_price'].fillna(0)
                        
                        # Переименовываем колонки
                        ads_columns_mapping = {
                            'номенклатура': 'Номенклатура',
                            'ads': 'ADS',
                            'total_sales': 'Общие_продажи',
                            'average_value': 'Среднемесячные_продажи',
                            'last_purchase_price': 'Последняя_цена_закупки'
                        }
                        
                        existing_ads_columns = {k: v for k, v in ads_columns_mapping.items() if k in ads_export.columns}
                        ads_export = ads_export.rename(columns=existing_ads_columns)
                    
                    ads_export.to_excel(writer, sheet_name='ADS_расчет_с_ценами', index=False)
                
                # Минимальные запасы с денежным выражением
                if self.calculated_min_stock is not None:
                    min_stock_export = self.calculated_min_stock.copy()
                    
                    # Переименовываем колонки
                    min_stock_columns_mapping = {
                        'номенклатура': 'Номенклатура',
                        'ads': 'ADS',
                        'min_stock_total': 'Минимальный_запас_шт',
                        'min_stock_base': 'Базовый_запас_шт',
                        'transit_consumption': 'Транзитное_потребление_шт',
                        'ip_target_days': 'Дни_транзита',
                        'min_stock_days': 'Дни_запаса',
                        'priority': 'Приоритет'
                    }
                    
                    if 'last_purchase_price' in min_stock_export.columns:
                        # Добавляем денежные расчеты
                        min_stock_export['min_stock_money'] = min_stock_export['min_stock_total'] * min_stock_export['last_purchase_price']
                        min_stock_export['transit_consumption_money'] = min_stock_export['transit_consumption'] * min_stock_export['last_purchase_price']
                        
                        min_stock_columns_mapping.update({
                            'last_purchase_price': 'Последняя_цена_закупки',
                            'min_stock_money': 'Минимальный_запас_деньги',
                            'transit_consumption_money': 'Транзитное_потребление_деньги'
                        })
                    
                    existing_min_columns = {k: v for k, v in min_stock_columns_mapping.items() if k in min_stock_export.columns}
                    min_stock_export = min_stock_export.rename(columns=existing_min_columns)
                    
                    min_stock_export.to_excel(writer, sheet_name='Минимальные_запасы', index=False)
                
                # Текущие остатки
                if self.stock_data is not None:
                    stock_export = self.stock_data[['номенклатура', 'total_current_stock']].copy()
                    stock_export = stock_export.rename(columns={
                        'номенклатура': 'Номенклатура',
                        'total_current_stock': 'Текущий_остаток'
                    })
                    stock_export.to_excel(writer, sheet_name='Текущие_остатки', index=False)
                
                # ОБНОВЛЕННОЕ сравнение остатков с денежными расчетами
                if self.stock_comparison is not None:
                    comparison_export = self.stock_comparison.copy()
                    
                    # Переименовываем колонки для русского интерфейса
                    comparison_columns_mapping = {
                        'номенклатура': 'Номенклатура',
                        'ads': 'ADS',
                        'min_stock_total': 'Минимальный_запас_шт',
                        'total_current_stock': 'Текущий_остаток_шт',
                        'stock_deficit': 'Дефицит_шт',
                        'stock_deficit_money': 'Дефицит_деньги',  # НОВОЕ
                        'min_stock_money': 'Минимальный_запас_деньги',  # НОВОЕ
                        'current_stock_money': 'Текущий_остаток_деньги',  # НОВОЕ
                        'current_stock_days': 'Дни_остатка',
                        'status': 'Статус',
                        'order_priority': 'Приоритет_заказа',
                        'recommended_order': 'Рекомендуемый_заказ_шт',
                        'recommended_order_money': 'Рекомендуемый_заказ_деньги',  # НОВОЕ
                        'last_purchase_price': 'Последняя_цена_закупки'
                    }
                    
                    existing_comparison_columns = {k: v for k, v in comparison_columns_mapping.items() if k in comparison_export.columns}
                    comparison_export = comparison_export.rename(columns=existing_comparison_columns)
                    
                    comparison_export.to_excel(writer, sheet_name='Полное_сравнение', index=False)
                    
                    # Товары с дефицитом (с денежными расчетами)
                    deficit_items = self.stock_comparison[self.stock_comparison['stock_deficit'] > 0].copy()
                    if not deficit_items.empty:
                        deficit_export = deficit_items.rename(columns=existing_comparison_columns)
                        # Сортируем по денежному дефициту (убывание)
                        if 'Дефицит_деньги' in deficit_export.columns:
                            deficit_export = deficit_export.sort_values('Дефицит_деньги', ascending=False)
                        
                        deficit_export.to_excel(writer, sheet_name='Товары_с_дефицитом', index=False)
                    
                    # Критичные товары
                    critical_items = self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'].copy()
                    if not critical_items.empty:
                        critical_export = critical_items.rename(columns=existing_comparison_columns)
                        if 'Дефицит_деньги' in critical_export.columns:
                            critical_export = critical_export.sort_values('Дефицит_деньги', ascending=False)
                        
                        critical_export.to_excel(writer, sheet_name='Критичные_товары', index=False)
                    
                    # ОБНОВЛЕННЫЕ рекомендации по заказу с денежными суммами
                    order_recommendations = self.stock_comparison[
                        self.stock_comparison['recommended_order'] > 0
                    ].copy()
                    
                    if not order_recommendations.empty:
                        order_export = order_recommendations[[
                            'номенклатура', 'recommended_order', 'recommended_order_money', 
                            'order_priority', 'ads', 'current_stock_days', 'last_purchase_price'
                        ]].copy()
                        
                        order_export = order_export.rename(columns=existing_comparison_columns)
                        
                        # Сортируем по денежной сумме заказа (убывание)
                        if 'Рекомендуемый_заказ_деньги' in order_export.columns:
                            order_export = order_export.sort_values('Рекомендуемый_заказ_деньги', ascending=False)
                        
                        order_export.to_excel(writer, sheet_name='Рекомендации_заказа', index=False)
                    
                    # НОВЫЙ ЛИСТ: Сводка по денежному выражению
                    if 'stock_deficit_money' in self.stock_comparison.columns:
                        money_summary = []
                        
                        # Общая статистика
                        total_deficit_money = self.stock_comparison['stock_deficit_money'].sum()
                        total_order_money = self.stock_comparison['recommended_order_money'].sum()
                        items_with_price = len(self.stock_comparison[self.stock_comparison['last_purchase_price'] > 0])
                        
                        # По статусам
                        for status in ['КРИТИЧНО', 'НЕДОСТАТОК', 'ДОСТАТОЧНО']:
                            status_data = self.stock_comparison[self.stock_comparison['status'] == status]
                            money_summary.append({
                                'Категория': f'Товары_{status}',
                                'Количество_товаров': len(status_data),
                                'Дефицит_штук': status_data['stock_deficit'].sum(),
                                'Дефицит_деньги': status_data['stock_deficit_money'].sum(),
                                'Рекомендуемый_заказ_штук': status_data['recommended_order'].sum(),
                                'Рекомендуемый_заказ_деньги': status_data['recommended_order_money'].sum()
                            })
                        
                        # Общие итоги
                        money_summary.append({
                            'Категория': 'ИТОГО',
                            'Количество_товаров': len(self.stock_comparison),
                            'Дефицит_штук': self.stock_comparison['stock_deficit'].sum(),
                            'Дефицит_деньги': total_deficit_money,
                            'Рекомендуемый_заказ_штук': self.stock_comparison['recommended_order'].sum(),
                            'Рекомендуемый_заказ_деньги': total_order_money
                        })
                        
                        money_summary_df = pd.DataFrame(money_summary)
                        money_summary_df.to_excel(writer, sheet_name='Денежная_сводка', index=False)
                
                # Подкатегории (если есть)
                if hasattr(self, 'subcategory_analyzer') and self.subcategory_analyzer.subcategory_results:
                    subcategory_export_df = self.subcategory_analyzer.export_subcategory_analysis()
                    if not subcategory_export_df.empty:
                        subcategory_export_df.to_excel(writer, sheet_name='Подкатегории_ABC', index=False)

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
        ОБНОВЛЕННОЕ получение итогового отчета с денежными метриками
        """
        report = {
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
            'system_status': self.get_system_status()
        }
        
        # ABC анализ сводка
        if self.abc_results is not None:
            abc_summary = self.abc_results['abc_summary']
            total_abc_items = sum(abc_summary.values())
            
            abc_report = {
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
            
            # НОВОЕ: Добавляем информацию о ценах
            if (self.abc_data is not None and 
                'last_purchase_price' in self.abc_data.columns):
                
                items_with_price = len(self.abc_data[self.abc_data['last_purchase_price'] > 0])
                total_items = len(self.abc_data)
                avg_price = self.abc_data[self.abc_data['last_purchase_price'] > 0]['last_purchase_price'].mean()
                
                abc_report['price_info'] = {
                    'items_with_price': items_with_price,
                    'price_coverage_percentage': (items_with_price / total_items) * 100 if total_items > 0 else 0,
                    'average_price': float(avg_price) if not pd.isna(avg_price) else 0,
                    'max_price': float(self.abc_data['last_purchase_price'].max()),
                    'total_inventory_value': float((self.abc_data['annual_sales'] * self.abc_data['last_purchase_price']).sum())
                }
            
            report['abc_analysis'] = abc_report
        
        # ADS анализ сводка
        if self.calculated_ads is not None:
            ads_columns = self.calculated_ads.columns.tolist()
            
            ads_report = {
                'total_items': len(self.calculated_ads),
                'total_ads': self.calculated_ads['ads'].sum(),
                'avg_ads': self.calculated_ads['ads'].mean()
            }
            
            if 'total_quantity_sold' in ads_columns:
                ads_report['total_quantity_sold'] = self.calculated_ads['total_quantity_sold'].sum()
            
            if 'total_sales' in ads_columns:
                ads_report['total_sales_period'] = self.calculated_ads['total_sales'].sum()
            
            # Топ товар по ADS
            top_ads_idx = self.calculated_ads['ads'].idxmax()
            ads_report['top_seller'] = {
                'item': self.calculated_ads.loc[top_ads_idx, 'номенклатура'],
                'ads_value': self.calculated_ads.loc[top_ads_idx, 'ads']
            }
            
            if hasattr(self, 'sales_files_data') and self.sales_files_data:
                ads_report['files_processed'] = len(self.sales_files_data)
                successful_files = sum(1 for r in self.sales_files_data.values() if r['success'])
                ads_report['successful_files'] = successful_files
            
            report['ads_analysis'] = ads_report
        
        # Минимальные запасы сводка
        if self.calculated_min_stock is not None:
            min_stock_report = {
                'total_items': len(self.calculated_min_stock),
                'total_min_stock': self.calculated_min_stock['min_stock_total'].sum(),
                'total_transit_consumption': self.calculated_min_stock['transit_consumption'].sum(),
                'parameters': {
                    'ip_days': self.calculated_min_stock['ip_target_days'].iloc[0],
                    'stock_days': self.calculated_min_stock['min_stock_days'].iloc[0]
                }
            }
            
            # НОВОЕ: Добавляем денежные метрики для минимальных запасов
            if 'last_purchase_price' in self.calculated_min_stock.columns:
                total_min_stock_money = (self.calculated_min_stock['min_stock_total'] * 
                                       self.calculated_min_stock['last_purchase_price']).sum()
                
                min_stock_report['money_metrics'] = {
                    'total_min_stock_money': float(total_min_stock_money),
                    'items_with_price': len(self.calculated_min_stock[self.calculated_min_stock['last_purchase_price'] > 0])
                }
            
            report['min_stock_analysis'] = min_stock_report
        
        # ОБНОВЛЕННАЯ сравнение остатков сводка с денежными метриками
        if self.stock_comparison is not None:
            total_items = len(self.stock_comparison)
            deficit_items = len(self.stock_comparison[self.stock_comparison['stock_deficit'] > 0])
            critical_items = len(self.stock_comparison[self.stock_comparison['status'] == 'КРИТИЧНО'])
            
            comparison_report = {
                'total_items': total_items,
                'deficit_items': deficit_items,
                'deficit_percentage': (deficit_items / total_items) * 100,
                'critical_items': critical_items,
                'critical_percentage': (critical_items / total_items) * 100,
                'total_deficit_value': self.stock_comparison['stock_deficit'].sum(),
                'total_recommended_order': self.stock_comparison['recommended_order'].sum(),
                'priority_distribution': self.stock_comparison['order_priority'].value_counts().to_dict()
            }
            
            # НОВОЕ: Денежные метрики
            if 'stock_deficit_money' in self.stock_comparison.columns:
                total_deficit_money = self.stock_comparison['stock_deficit_money'].sum()
                total_order_money = self.stock_comparison['recommended_order_money'].sum()
                items_with_price = len(self.stock_comparison[self.stock_comparison['last_purchase_price'] > 0])
                deficit_items_with_price = len(self.stock_comparison[
                    (self.stock_comparison['stock_deficit'] > 0) & 
                    (self.stock_comparison['last_purchase_price'] > 0)
                ])
                
                comparison_report['money_metrics'] = {
                    'total_deficit_money': float(total_deficit_money),
                    'total_recommended_order_money': float(total_order_money),
                    'items_with_price': items_with_price,
                    'deficit_items_with_price': deficit_items_with_price,
                    'price_coverage_percentage': (items_with_price / total_items) * 100 if total_items > 0 else 0,
                    'deficit_price_coverage_percentage': (deficit_items_with_price / deficit_items) * 100 if deficit_items > 0 else 0
                }
                
                # Топ дефицитные товары по денежному выражению
                top_deficit_money = self.stock_comparison[
                    self.stock_comparison['stock_deficit_money'] > 0
                ].nlargest(5, 'stock_deficit_money')
                
                if not top_deficit_money.empty:
                    comparison_report['money_metrics']['top_deficit_money_items'] = [
                        {
                            'item': row['номенклатура'],
                            'deficit_money': row['stock_deficit_money'],
                            'deficit_quantity': row['stock_deficit'],
                            'price': row['last_purchase_price']
                        }
                        for _, row in top_deficit_money.iterrows()
                    ]
            
            report['stock_comparison'] = comparison_report
        
        # Подкатегории (если есть)
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