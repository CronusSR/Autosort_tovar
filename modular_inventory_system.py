#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модульный обработчик данных для системы анализа товарных запасов v3.0
Поддерживает пошаговый анализ с выбором типа операции
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import warnings
import plotly.express as px
import plotly.graph_objects as go
warnings.filterwarnings('ignore')

class ModularInventorySystem:
    """Модульная система анализа товарных запасов"""
    
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
        
        # Множественные файлы продаж
        self.sales_files_data = {}  # Хранилище данных по филиалам
        self.combined_sales_data = None
        
        # Параметры по умолчанию
        self.default_params = {
            'ip_target_days': 7,    # Транзитное время
            'min_stock_days': 30,   # Дни запаса
            'safety_factor': 1.0    # Коэффициент безопасности
        }
    
    def load_sales_file_updated(self, file_content) -> Dict:
        """
        ОБНОВЛЕННАЯ загрузка файла продаж с новой логикой ADS
        НОМЕНКЛАТУРА: Колонка B (индекс 1) - ИСПРАВЛЕНО!
        ДИАПАЗОН: M4:AB4 до последнего товара (исключая последнюю строку)
        ФОРМУЛА: ADS = (среднее от M4:AB4) / 30
        """
        try:
            print("🔄 Обработка файла с ИСПРАВЛЕННОЙ логикой ADS (номенклатура в колонке B)...")
        
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
            print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # ИСПРАВЛЕННЫЕ параметры
            start_col_index = 12  # Колонка M
            end_col_index = 28    # Колонка AB+1 (не включается)
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (индекс 1) - ИСПРАВЛЕНО!
            
            print(f"📋 ИСПРАВЛЕННАЯ ЛОГИКА:")
            print(f"   • Номенклатура: Колонка B (индекс {nomenclature_col})")
            print(f"   • Данные продаж: колонки {start_col_index}:{end_col_index} (M:AB)")
            print(f"   • Начальная строка: {start_row+1}")
            
            # Проверяем достаточность колонок
            if df.shape[1] < end_col_index:
                return {
                    'success': False,
                    'error': f'Недостаточно колонок в файле. Нужно минимум {end_col_index}, есть {df.shape[1]}'
                }
            
            # Получаем номенклатуру из колонки B (индекс 1) - ИСПРАВЛЕНО!
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
            
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
            
            # Извлекаем данные продаж из диапазона M:AB
            print("📈 Извлечение данных из диапазона M4:AB...")
            
            sales_data_list = []
            
            for idx in valid_indices:
                item_name = str(nomenclature_clean.loc[idx]).strip()
                
                # Извлекаем данные из колонок M:AB для данной строки
                row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                
                # Преобразуем в числовой формат, заменяя NaN и пустые на 0
                row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                
                # НОВАЯ ФОРМУЛА РАСЧЕТА ADS:
                # 1. Получаем среднее значение от M4:AB4
                average_value = row_sales_numeric.mean()
                
                # 2. Делим среднее значение на 30
                ads_value = average_value / 30
                
                sales_data_list.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_sales_numeric.sum(),  # Для совместимости
                    'monthly_data': row_sales_numeric.tolist()
                })
            
            # Создаем DataFrame
            ads_df = pd.DataFrame(sales_data_list)
            
            # Сохраняем результаты в системе
            self.sales_data = ads_df
            self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales']].copy()
            
            # Создаем JSON данные для системы
            json_output = {
                'metadata': {
                    'file_processed_at': pd.Timestamp.now().isoformat(),
                    'total_items': len(ads_df),
                    'nomenclature_column': 'B',
                    'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                    'calculation_method': 'average_monthly_divided_by_30',
                    'formula': 'ADS = (среднее от M4:AB4) / 30',
                    'last_row_excluded': True
                },
                'summary_stats': {
                    'total_ads': float(ads_df['ads'].sum()),
                    'average_ads': float(ads_df['ads'].mean()),
                    'max_ads': float(ads_df['ads'].max()),
                    'min_ads': float(ads_df['ads'].min())
                },
                'items': [
                    {
                        'nomenclature': row['номенклатура'],
                        'ads_daily': row['ads'],
                        'average_monthly': row['average_value'],
                        'total_period': row['total_sales'],
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
            
            print(f"\n📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕННОЙ ЛОГИКИ:")
            print("=" * 60)
            print(f"Номенклатура читается из: Колонка B")
            print(f"Обработано товаров: {len(ads_df)}")
            print(f"Диапазон: M{start_row+1}:AB{start_row+1+len(ads_df)}")
            print(f"Формула: ADS = (среднее месячное) / 30")
            print(f"Общий ADS: {ads_df['ads'].sum():.2f}")
            print(f"Средний ADS: {ads_df['ads'].mean():.4f}")
            print(f"Товаров с положительным ADS: {positive_ads_count}")
            
            # Топ товары
            print(f"\n🏆 Топ-5 товаров по новому ADS:")
            top_sellers = ads_df.nlargest(5, 'ads')
            for i, (_, row) in enumerate(top_sellers.iterrows(), 1):
                print(f"  {i}. {row['номенклатура'][:50]:<50} | ADS: {row['ads']:>8.4f}")
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'nomenclature_column': 'B',
                'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                'calculation_method': 'average_monthly_divided_by_30_fixed',
                'formula': 'ADS = (среднее от M4:AB4) / 30',
                'total_ads': ads_df['ads'].sum(),
                'average_ads': ads_df['ads'].mean(),
                'items_with_positive_ads': positive_ads_count,
                'json_data_created': True,
                'last_row_excluded': True
            }
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка загрузки файла продаж: {str(e)}"}

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
        """
        Экспорт результатов с исправленной логикой ADS и JSON
        Добавьте этот метод в класс ModularInventorySystem
        """
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
        ИСПРАВЛЕННАЯ загрузка и обработка файла для ABC анализа
        ВАЖНО: Пустые ячейки продаж заменяются на нули, товары НЕ исключаются
        
        Args:
            file_content: Содержимое файла (bytes или file-like объект)
            
        Returns:
            Dict с информацией о загруженных данных
        """
        try:
            print("🔄 Начинаем загрузку ABC файла с ИСПРАВЛЕННОЙ логикой обработки пустых продаж...")
            
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                excel_file = pd.ExcelFile(file_content, engine='openpyxl')
            else:
                excel_file = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
            
            print(f"📋 Листы в файле: {excel_file.sheet_names}")
            
            # Автоматический выбор листа по приоритету
            target_sheet = None
            sheet_priority = ['abc', 'Лист1', 'Sheet1', 'лист1']
            
            for priority_sheet in sheet_priority:
                if priority_sheet in excel_file.sheet_names:
                    target_sheet = priority_sheet
                    print(f"✅ Найден лист по приоритету: '{target_sheet}'")
                    break
            
            if target_sheet is None:
                target_sheet = excel_file.sheet_names[0]
                print(f"✅ Используем первый доступный лист: '{target_sheet}'")
            
            # Читаем выбранный лист
            df = pd.read_excel(excel_file, sheet_name=target_sheet, engine='openpyxl')
            print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # ИСПРАВЛЕННАЯ логика определения начала данных
            data_start_row = None
            
            # Ищем строку с данными (содержащую номенклатуру)
            for i in range(min(20, len(df))):  # Проверяем первые 20 строк
                row = df.iloc[i]
                
                # Проверяем первые несколько колонок на наличие текстовых данных
                for j in range(min(4, len(row))):
                    cell_value = str(row.iloc[j]).strip().lower()
                    
                    # Пропускаем явно служебные строки
                    if (pd.isna(row.iloc[j]) or 
                        cell_value in ['', 'nan', 'none'] or
                        'заголовок' in cell_value or
                        'header' in cell_value or
                        len(cell_value) < 2):
                        continue
                    
                    # Если нашли строку с осмысленными данными
                    if (len(cell_value) >= 2 and 
                        not cell_value.isdigit() and
                        cell_value not in ['колонка', 'column', 'столбец']):
                        data_start_row = i
                        print(f"✅ ИСПРАВЛЕНО: Найдено начало данных на строке {i+1}")
                        print(f"   Первая номенклатура: '{cell_value[:50]}'")
                        break
                
                if data_start_row is not None:
                    break
            
            # Если автоматически не нашли, используем стандартные отступы
            if data_start_row is None:
                if target_sheet.lower() == 'abc':
                    data_start_row = 6  # Стандартный отступ для листа abc
                    print("⚠️ Используем стандартный отступ для листа 'abc': строка 7")
                else:
                    data_start_row = 5  # Стандартный отступ для других листов
                    print("⚠️ Используем стандартный отступ: строка 6")
            
            # Применяем найденное начало данных
            df = df.iloc[data_start_row:].copy()
            df = df.reset_index(drop=True)
            print(f"📊 После применения отступа: {df.shape[0]} строк данных")
            
            # ИСПРАВЛЕННАЯ логика определения колонок
            print("🔍 Определяем структуру колонок...")
            
            # Проверяем количество колонок и их содержимое
            actual_columns = len(df.columns)
            print(f"📊 Доступно колонок: {actual_columns}")
            
            # Анализируем первые строки для понимания структуры
            sample_data = df.head(3)
            print("📋 Образец первых строк:")
            for i, (idx, row) in enumerate(sample_data.iterrows()):
                row_preview = [str(val)[:20] + '...' if len(str(val)) > 20 else str(val) 
                              for val in row.values[:min(6, len(row))]]
                print(f"   Строка {i+1}: {row_preview}")
            
            # Адаптивное назначение колонок в зависимости от структуры
            if actual_columns >= 4:
                # Стандартная структура: номенклатура, подкатегория, категория, продажи
                df.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + \
                            [f'extra_col_{i}' for i in range(4, actual_columns)]
                print("✅ Применена стандартная схема колонок (4+ колонки)")
                
            elif actual_columns == 3:
                # Упрощенная структура: номенклатура, категория, продажи
                df.columns = ['nomenclature', 'category', 'annual_sales']
                print("✅ Применена упрощенная схема колонок (3 колонки)")
                
            else:
                # Минимальная структура
                base_names = ['nomenclature', 'annual_sales']
                df.columns = base_names[:actual_columns] + \
                            [f'col_{i}' for i in range(len(base_names), actual_columns)]
                print(f"⚠️ Применена минимальная схема колонок ({actual_columns} колонки)")
            
            print(f"📋 ИСПРАВЛЕНО: Назначены колонки: {list(df.columns)}")
            
            # КРИТИЧЕСКИ ВАЖНАЯ очистка данных с СОХРАНЕНИЕМ товаров с нулевыми продажами
            print("🧹 ИСПРАВЛЕННАЯ очистка данных с сохранением товаров с пустыми продажами...")
            initial_count = len(df)
            print(f"📊 Начальное количество строк: {initial_count}")
            
            # Шаг 1: Очистка номенклатуры (НЕ ТРОГАЕМ ПРОДАЖИ!)
            print("   1️⃣ Очистка номенклатуры...")
            df_before_nomenclature = len(df)
            
            # Убираем строки с пустой номенклатурой
            df = df.dropna(subset=['nomenclature'])
            after_dropna = len(df)
            print(f"      После dropna: {after_dropna} (-{df_before_nomenclature - after_dropna})")
            
            # Убираем строки с пустыми строками
            df = df[df['nomenclature'].astype(str).str.strip() != '']
            after_empty = len(df)
            print(f"      После удаления пустых: {after_empty} (-{after_dropna - after_empty})")
            
            # Убираем строки со значением 'nan'
            df = df[df['nomenclature'].astype(str).str.lower() != 'nan']
            after_nan = len(df)
            print(f"      После удаления 'nan': {after_nan} (-{after_empty - after_nan})")
            
            # Убираем строки с числовыми значениями в номенклатуре (возможные ошибки)
            df = df[~df['nomenclature'].astype(str).str.isdigit()]
            after_digits = len(df)
            print(f"      После удаления цифр: {after_digits} (-{after_nan - after_digits})")
            
            # Шаг 2: ИСПРАВЛЕННАЯ обработка годовых продаж - НЕ ИСКЛЮЧАЕМ товары с пустыми продажами!
            print("   2️⃣ ИСПРАВЛЕННАЯ обработка колонки продаж (пустые = 0, товары сохраняются)...")
            df_before_sales = len(df)
            
            # Преобразуем в числовой формат, но НЕ исключаем NaN
            print(f"      Исходная колонка продаж: {df['annual_sales'].dtype}")
            
            # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Заменяем NaN на 0 ПЕРЕД проверкой валидности
            df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')
            nan_count_before = df['annual_sales'].isna().sum()
            print(f"      Найдено NaN значений в продажах: {nan_count_before}")
            
            # ЗАМЕНЯЕМ NaN на 0 вместо исключения товаров
            df['annual_sales'] = df['annual_sales'].fillna(0)
            print(f"      ✅ ИСПРАВЛЕНО: Все NaN заменены на 0")
            
            # Проверяем отрицательные значения и заменяем на 0
            negative_count = (df['annual_sales'] < 0).sum()
            if negative_count > 0:
                print(f"      Найдено отрицательных значений: {negative_count}")
                df.loc[df['annual_sales'] < 0, 'annual_sales'] = 0
                print(f"      ✅ Отрицательные значения заменены на 0")
            
            # ВАЖНО: НЕ исключаем товары с нулевыми продажами для ABC анализа
            zero_sales_count = (df['annual_sales'] == 0).sum()
            positive_sales_count = (df['annual_sales'] > 0).sum()
            
            print(f"      📊 Статистика продаж после обработки:")
            print(f"         Товаров с продажами > 0: {positive_sales_count}")
            print(f"         Товаров с продажами = 0: {zero_sales_count}")
            print(f"         ✅ ВСЕ ТОВАРЫ СОХРАНЕНЫ для ABC анализа")
            
            after_sales_processing = len(df)
            print(f"      После обработки продаж: {after_sales_processing} товаров (потеряно: 0)")
            
            # Шаг 3: Обработка категорий (как раньше)
            print("   3️⃣ Обработка категорий...")
            
            # Очищаем категории
            if 'category' in df.columns:
                # Заполняем пустые категории
                df['category'] = df['category'].astype(str).str.strip()
                df['category'] = df['category'].replace(['nan', 'None', ''], 'Без категории')
                
                # Если есть subcategory, используем её для заполнения пустых category
                if 'subcategory' in df.columns:
                    df['subcategory'] = df['subcategory'].astype(str).str.strip()
                    mask_empty_category = df['category'].isin(['Без категории', 'nan', ''])
                    mask_valid_subcategory = ~df['subcategory'].isin(['nan', 'None', '', 'Без категории'])
                    
                    filled_count = (mask_empty_category & mask_valid_subcategory).sum()
                    df.loc[mask_empty_category & mask_valid_subcategory, 'category'] = \
                        df.loc[mask_empty_category & mask_valid_subcategory, 'subcategory']
                    
                    print(f"      Заполнено категорий из подкатегорий: {filled_count}")
            else:
                # Если нет колонки category, создаем её
                df['category'] = 'Общая категория'
                print("      Создана общая категория")
            
            # Финальная проверка категорий (но не исключаем товары)
            df = df[df['category'].notna()]
            df = df[df['category'].astype(str).str.strip() != '']
            final_count = len(df)
            
            print(f"📊 ИТОГО после всех очисток: {final_count} товаров")
            print(f"📊 Потеряно в процессе очистки: {initial_count - final_count} строк ({((initial_count - final_count) / initial_count * 100):.1f}%)")
            
            if final_count == 0:
                return {
                    'success': False,
                    'error': 'Не осталось валидных товаров после очистки данных. Проверьте структуру файла.'
                }
            
            # Проверяем дубликаты
            duplicates_count = df['nomenclature'].duplicated().sum()
            if duplicates_count > 0:
                print(f"⚠️ Найдено дубликатов по номенклатуре: {duplicates_count}")
                df = df.drop_duplicates(subset=['nomenclature'], keep='first')
                print(f"✅ После удаления дубликатов: {len(df)} товаров")
            
            # Сохраняем очищенные данные
            self.abc_data = df
            
            # Рассчитываем статистику
            total_sales = df['annual_sales'].sum()
            categories_count = df['category'].nunique()
            avg_sales = df['annual_sales'].mean()
            
            # ВАЖНАЯ СТАТИСТИКА: Показываем товары с нулевыми продажами
            zero_sales_final = (df['annual_sales'] == 0).sum()
            positive_sales_final = (df['annual_sales'] > 0).sum()
            
            print(f"\n📊 ИСПРАВЛЕННАЯ СТАТИСТИКА:")
            print("=" * 50)
            print(f"✅ Финальное количество товаров: {final_count}")
            print(f"💰 Товаров с продажами > 0: {positive_sales_final}")
            print(f"🔄 Товаров с продажами = 0: {zero_sales_final} (СОХРАНЕНЫ для ABC)")
            print(f"📈 Общие продажи: {total_sales:,.0f}")
            print(f"📊 Средние продажи на товар: {avg_sales:,.0f}")
            print(f"🏷️ Уникальных категорий: {categories_count}")
            
            # Топ категории
            top_categories = df['category'].value_counts().head(5)
            print(f"\n🏆 Топ-5 категорий по количеству товаров:")
            for i, (cat, count) in enumerate(top_categories.items(), 1):
                print(f"  {i}. {cat}: {count} товаров")
            
            # Топ товары (только с продажами > 0)
            if positive_sales_final > 0:
                top_items = df[df['annual_sales'] > 0].nlargest(3, 'annual_sales')
                print(f"\n💰 Топ-3 товара по продажам:")
                for i, (_, row) in enumerate(top_items.iterrows(), 1):
                    print(f"  {i}. {row['nomenclature'][:40]}: {row['annual_sales']:,.0f}")
            
            # Показываем примеры товаров с нулевыми продажами
            if zero_sales_final > 0:
                zero_sales_items = df[df['annual_sales'] == 0].head(3)
                print(f"\n🔄 Примеры товаров с нулевыми продажами (включены в ABC):")
                for i, (_, row) in enumerate(zero_sales_items.iterrows(), 1):
                    print(f"  {i}. {row['nomenclature'][:40]}: {row['annual_sales']}")
            
            return {
                'success': True,
                'total_items': final_count,  # ИСПРАВЛЕНО: используем финальное количество
                'items_with_sales': positive_sales_final,
                'items_with_zero_sales': zero_sales_final,
                'categories': categories_count,
                'total_sales': total_sales,
                'average_sales': avg_sales,
                'sheet_used': target_sheet,
                'data_start_row': data_start_row + 1,  # +1 для пользователя (строки с 1)
                'duplicates_removed': duplicates_count,
                'cleaning_stats': {
                    'initial_rows': initial_count,
                    'final_rows': final_count,
                    'rows_lost': initial_count - final_count,
                    'loss_percentage': ((initial_count - final_count) / initial_count * 100) if initial_count > 0 else 0
                },
                'sales_distribution': {
                    'positive_sales': positive_sales_final,
                    'zero_sales': zero_sales_final,
                    'total_sales_value': float(total_sales)
                },
                'top_items': top_items[['nomenclature', 'annual_sales']].to_dict('records') if positive_sales_final > 0 else [],
                'sample_categories': df['category'].value_counts().head(10).to_dict(),
                'columns_used': list(df.columns),
                'zero_sales_included': True  # Флаг что товары с нулевыми продажами включены
            }
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Ошибка загрузки ABC файла: {str(e)}"
            }
        
    def perform_abc_analysis(self) -> Dict:
        """
        ИСПРАВЛЕННОЕ выполнение ABC анализа по загруженным данным
        
        Returns:
            Dict с результатами ABC анализа
        """
        if self.abc_data is None:
            return {'success': False, 'error': 'ABC данные не загружены'}
        
        try:
            print("🔤 Начинаем ИСПРАВЛЕННЫЙ ABC анализ...")
            
            df = self.abc_data.copy()
            initial_items = len(df)
            print(f"📊 Исходное количество товаров: {initial_items}")
            
            # Дополнительная валидация данных перед анализом
            print("🔍 Валидация данных перед ABC анализом...")
            
            # Проверяем наличие продаж
            valid_sales_mask = (df['annual_sales'] > 0) & df['annual_sales'].notna()
            valid_sales_count = valid_sales_mask.sum()
            
            if valid_sales_count == 0:
                return {
                    'success': False, 
                    'error': 'Нет товаров с положительными продажами для ABC анализа'
                }
            
            if valid_sales_count < initial_items:
                print(f"⚠️ Отфильтровано товаров без продаж: {initial_items - valid_sales_count}")
                df = df[valid_sales_mask].copy()
            
            final_items = len(df)
            print(f"📊 Финальное количество для ABC: {final_items}")
            
            # Сортируем по объему продаж (по убыванию)
            df = df.sort_values('annual_sales', ascending=False)
            print("✅ Товары отсортированы по продажам")
            
            # Рассчитываем проценты
            total_sales = df['annual_sales'].sum()
            print(f"💰 Общие продажи: {total_sales:,.0f}")
            
            df['sales_percentage'] = (df['annual_sales'] / total_sales) * 100
            df['cumulative_percentage'] = df['sales_percentage'].cumsum()
            
            # ИСПРАВЛЕННОЕ присвоение ABC классов по принципу Парето
            def assign_abc_class_fixed(cumulative_pct):
                """Исправленная функция присвоения ABC классов"""
                if cumulative_pct <= 80.0:
                    return 'A'
                elif cumulative_pct <= 95.0:
                    return 'B'
                else:
                    return 'C'
            
            df['abc_class'] = df['cumulative_percentage'].apply(assign_abc_class_fixed)
            
            # Проверяем распределение ABC
            abc_counts = df['abc_class'].value_counts()
            print(f"\n📊 ИСПРАВЛЕННОЕ ABC распределение:")
            print(f"🔴 A товары: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/final_items*100:.1f}%)")
            print(f"🟡 B товары: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/final_items*100:.1f}%)")
            print(f"🟢 C товары: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/final_items*100:.1f}%)")
            
            # Проверяем правильность Парето принципа
            a_sales_percentage = df[df['abc_class'] == 'A']['sales_percentage'].sum()
            b_sales_percentage = df[df['abc_class'] == 'B']['sales_percentage'].sum()
            c_sales_percentage = df[df['abc_class'] == 'C']['sales_percentage'].sum()
            
            print(f"\n💰 Проверка принципа Парето:")
            print(f"🔴 A товары: {a_sales_percentage:.1f}% продаж")
            print(f"🟡 B товары: {b_sales_percentage:.1f}% продаж")  
            print(f"🟢 C товары: {c_sales_percentage:.1f}% продаж")
            
            # ИСПРАВЛЕННЫЙ анализ по категориям
            print(f"\n📊 Анализ по категориям...")
            category_results = {}
            unique_categories = df['category'].dropna().unique()
            processed_categories = 0
            
            for category in unique_categories:
                try:
                    category_data = df[df['category'] == category].copy()
                    category_items = len(category_data)
                    
                    if category_items == 0:
                        continue
                    
                    category_sales = category_data['annual_sales'].sum()
                    category_sales_pct = (category_sales / total_sales) * 100
                    
                    # ABC распределение в категории
                    abc_distribution = {
                        'A': len(category_data[category_data['abc_class'] == 'A']),
                        'B': len(category_data[category_data['abc_class'] == 'B']),
                        'C': len(category_data[category_data['abc_class'] == 'C'])
                    }
                    
                    # Проверяем, что сумма распределения совпадает с количеством товаров
                    total_abc_items = sum(abc_distribution.values())
                    if total_abc_items != category_items:
                        print(f"⚠️ Несоответствие в категории '{category}': {total_abc_items} vs {category_items}")
                    
                    category_results[str(category)] = {
                        'total_items': category_items,
                        'total_sales': float(category_sales),
                        'sales_percentage': float(category_sales_pct),
                        'abc_distribution': abc_distribution,
                        'avg_sales': float(category_data['annual_sales'].mean()),
                        'max_sales': float(category_data['annual_sales'].max()),
                        'min_sales': float(category_data['annual_sales'].min()),
                        'top_items': category_data.head(3)[['nomenclature', 'annual_sales', 'abc_class']].to_dict('records')
                    }
                    
                    processed_categories += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка обработки категории '{category}': {str(e)}")
                    continue
            
            print(f"✅ Обработано категорий: {processed_categories}")
            
            # ИСПРАВЛЕННАЯ общая статистика ABC
            abc_summary = {
                'A': int(abc_counts.get('A', 0)),
                'B': int(abc_counts.get('B', 0)),
                'C': int(abc_counts.get('C', 0))
            }
            
            # Дополнительная статистика
            pareto_stats = {
                'a_items_percentage': (abc_summary['A'] / final_items) * 100,
                'a_sales_percentage': float(a_sales_percentage),
                'b_items_percentage': (abc_summary['B'] / final_items) * 100,
                'b_sales_percentage': float(b_sales_percentage),
                'c_items_percentage': (abc_summary['C'] / final_items) * 100,
                'c_sales_percentage': float(c_sales_percentage),
                'pareto_achieved': a_sales_percentage >= 70.0  # Мягкий критерий для Парето
            }
            
            # Сохраняем результаты
            self.abc_results = {
                'abc_data_detailed': df,
                'category_analysis': category_results,
                'abc_summary': abc_summary,
                'pareto_stats': pareto_stats,
                'total_sales': float(total_sales),
                'total_items': final_items,
                'analysis_date': pd.Timestamp.now().isoformat()
            }
            
            print(f"\n✅ ABC анализ завершен успешно!")
            print(f"📊 Итоговая статистика:")
            print(f"   • Товаров проанализировано: {final_items}")
            print(f"   • Категорий обработано: {processed_categories}")
            print(f"   • Принцип Парето: {'✅ соблюден' if pareto_stats['pareto_achieved'] else '⚠️ не идеален'}")
            
            return {
                'success': True,
                'abc_summary': abc_summary,
                'category_count': processed_categories,
                'total_sales': float(total_sales),
                'total_items': final_items,  # ИСПРАВЛЕНО: правильное количество
                'pareto_achieved': pareto_stats['pareto_achieved'],
                'pareto_stats': pareto_stats
            }
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ABC анализа: {str(e)}")
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
            
            # Приоритет заказа
            comparison['order_priority'] = comparison.apply(
                lambda row: 'СРОЧНО' if row['status'] == 'КРИТИЧНО'
                           else 'ВЫСОКИЙ' if row['status'] == 'НЕДОСТАТОК' and row['ads'] > comparison['ads'].quantile(0.7)
                           else 'СРЕДНИЙ' if row['status'] == 'НЕДОСТАТОК'
                           else 'НЕ ТРЕБУЕТСЯ', axis=1
            )
            
            # Сортируем по критичности
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