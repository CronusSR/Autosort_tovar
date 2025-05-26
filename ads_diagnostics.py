#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправленной обработки ADS файла
"""

import pandas as pd
import numpy as np
import io
from typing import Dict

def test_fixed_ads_processing(file_path: str):
    """
    Тест исправленной обработки ADS
    
    Args:
        file_path: Путь к файлу для тестирования
    """
    
    print("🧪 ТЕСТ ИСПРАВЛЕННОЙ ОБРАБОТКИ ADS")
    print("=" * 60)
    print(f"📁 Файл: {file_path}")
    
    # Создаем временный класс с исправленными методами
    class TestProcessor:
        def __init__(self):
            self.sales_data = None
            self.calculated_ads = None
        
        def _find_quantity_column_improved(self, df: pd.DataFrame, branch_name: str) -> str:
            """Исправленный поиск колонки количества"""
            print(f"🔍 {branch_name}: Поиск колонки количества среди {len(df.columns)} колонок")
            
            # 1. Приоритет: колонка AD (индекс 30)
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
            
            # Если AD не подходит, ищем по ключевым словам
            quantity_patterns = [
                'количество', 'кол-во', 'кол_во', 'штук', 'шт', 'продано', 'продажи',
                'qty', 'quantity', 'sold', 'sales', 'итого', 'сумма'
            ]
            
            for col in df.columns:
                col_str = str(col).lower().strip()
                for pattern in quantity_patterns:
                    if pattern in col_str:
                        try:
                            test_data = pd.to_numeric(df[col], errors='coerce')
                            if test_data.count() > 0:
                                print(f"  ✅ {branch_name}: Найдена по ключевому слову '{col}'")
                                return col
                        except:
                            continue
                        break
            
            print(f"  ❌ {branch_name}: Колонка количества не найдена")
            return None
        
        def load_sales_file_fixed(self, file_content):
            """Исправленная загрузка файла продаж"""
            try:
                print("🔄 Начинаем обработку файла продаж...")
                
                # Читаем Excel файл
                df = pd.read_excel(file_content, engine='openpyxl')
                print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
                
                # Поиск заголовков
                header_row = None
                print("🔍 Поиск строки с заголовками...")
                
                for i in range(min(15, len(df))):
                    if df.iloc[i].isna().all():
                        continue
                        
                    first_cell = None
                    for cell in df.iloc[i]:
                        if pd.notna(cell) and str(cell).strip():
                            first_cell = str(cell).lower().strip()
                            break
                    
                    if first_cell:
                        print(f"   Строка {i}: '{first_cell[:50]}{'...' if len(first_cell) > 50 else ''}'")
                        
                        header_keywords = [
                            'номенклатура', 'наименование', 'товар', 'название', 'продукт',
                            'item', 'product', 'name', 'nomenclature', 'артикул', 'код'
                        ]
                        
                        if any(keyword in first_cell for keyword in header_keywords):
                            header_row = i
                            print(f"   ✅ НАЙДЕН ЗАГОЛОВОК на строке {i}")
                            break
                
                if header_row is None:
                    print("   ⚠️ Заголовок не найден, используем строку 0")
                    header_row = 0
                
                # Применяем заголовки
                print(f"📋 Применяем заголовки с строки {header_row}...")
                headers = df.iloc[header_row].tolist()
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
                
                print(f"✅ После применения заголовков: {df.shape[0]} строк")
                
                # Стандартизируем названия колонок
                df.columns = [str(col).lower().strip() if pd.notna(col) else f'col_{i}' 
                             for i, col in enumerate(df.columns)]
                
                # Поиск колонки номенклатуры
                print("🔍 Поиск колонки номенклатуры...")
                nomenclature_col = None
                
                nomenclature_keywords = [
                    'номенклатура', 'наименование', 'товар', 'название', 'продукт',
                    'item', 'product', 'name', 'nomenclature', 'артикул', 'код'
                ]
                
                for col in df.columns:
                    col_str = str(col).lower().strip()
                    for keyword in nomenclature_keywords:
                        if keyword in col_str:
                            nomenclature_col = col
                            print(f"   ✅ Найдена колонка номенклатуры: '{col}'")
                            break
                    if nomenclature_col:
                        break
                
                if nomenclature_col is None:
                    nomenclature_col = df.columns[0]
                    print(f"   ⚠️ Используем первую колонку: '{nomenclature_col}'")
                
                df = df.rename(columns={nomenclature_col: 'номенклатура'})
                
                # ОСТОРОЖНАЯ очистка номенклатуры
                print("🧹 Очистка данных номенклатуры...")
                initial_count = len(df)
                
                # Статистика ДО очистки
                nomenclature_series = df['номенклатура']
                nan_count = nomenclature_series.isna().sum()
                empty_count = sum(nomenclature_series.astype(str).str.strip() == '')
                nan_str_count = sum(nomenclature_series.astype(str) == 'nan')
                
                print(f"   Анализ качества номенклатуры:")
                print(f"     • NaN значений: {nan_count}")
                print(f"     • Пустых строк: {empty_count}")
                print(f"     • Строк 'nan': {nan_str_count}")
                
                # Пошаговая очистка
                df = df.dropna(subset=['номенклатура'])
                lost_nan = initial_count - len(df)
                print(f"   После удаления NaN: {len(df)} (-{lost_nan})")
                
                df = df[df['номенклатура'].astype(str).str.strip() != '']
                lost_empty = initial_count - lost_nan - len(df)
                print(f"   После удаления пустых: {len(df)} (-{lost_empty})")
                
                df = df[df['номенклатура'].astype(str) != 'nan']
                lost_nan_str = initial_count - lost_nan - lost_empty - len(df)
                print(f"   После удаления 'nan': {len(df)} (-{lost_nan_str})")
                
                total_lost_nomenclature = initial_count - len(df)
                print(f"   📊 Итого потеряно на номенклатуре: {total_lost_nomenclature} строк")
                
                # Поиск колонки количества
                print("🔍 Поиск колонки количества...")
                quantity_column = self._find_quantity_column_improved(df, "test_file")
                
                if quantity_column is None:
                    return {
                        'success': False, 
                        'error': 'Не найдена колонка с количеством продаж'
                    }
                
                print(f"✅ Используем колонку количества: '{quantity_column}'")
                
                # Обработка количества
                print("🔢 Обработка данных количества...")
                df['total_sales'] = pd.to_numeric(df[quantity_column], errors='coerce')
                
                total_before_filter = len(df)
                valid_numeric = df['total_sales'].notna().sum()
                positive_values = (df['total_sales'] > 0).sum()
                
                print(f"   Анализ колонки '{quantity_column}':")
                print(f"     • Всего строк: {total_before_filter}")
                print(f"     • Числовых значений: {valid_numeric}")
                print(f"     • Положительных значений: {positive_values}")
                
                # Фильтруем положительные
                df['total_sales'] = df['total_sales'].fillna(0)
                df = df[df['total_sales'] > 0].copy()
                
                lost_quantity = total_before_filter - len(df)
                print(f"   После фильтрации количества: {len(df)} (-{lost_quantity})")
                
                # Рассчитываем ADS
                df['ads'] = df['total_sales'] / 365
                
                # Убираем дубликаты
                initial_final_count = len(df)
                df = df.drop_duplicates(subset=['номенклатура'], keep='first')
                duplicates_removed = initial_final_count - len(df)
                
                if duplicates_removed > 0:
                    print(f"   Удалено дубликатов: {duplicates_removed}")
                
                # Итоговая статистика
                print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
                print("=" * 50)
                print(f"Исходно строк: {initial_count}")
                print(f"Потеряно на номенклатуре: {total_lost_nomenclature}")
                print(f"Потеряно на количестве: {lost_quantity}")
                print(f"Удалено дубликатов: {duplicates_removed}")
                print(f"ИТОГО товаров: {len(df)}")
                print(f"Общий ADS: {df['ads'].sum():.2f}")
                print(f"Общее количество продаж: {df['total_sales'].sum():,.0f}")
                
                # Топ товары
                print(f"\n🏆 Топ-5 товаров по продажам:")
                top_sellers = df.nlargest(5, 'total_sales')
                for i, (_, row) in enumerate(top_sellers.iterrows(), 1):
                    print(f"  {i}. {row['номенклатура'][:60]:<60} | {row['total_sales']:>8,.0f}")
                
                return {
                    'success': True,
                    'total_items': len(df),
                    'quantity_column_used': quantity_column,
                    'total_quantity_sold': df['total_sales'].sum(),
                    'total_ads': df['ads'].sum(),
                    'processing_stats': {
                        'initial_rows': initial_count,
                        'lost_nomenclature': total_lost_nomenclature,
                        'lost_quantity': lost_quantity,
                        'duplicates_removed': duplicates_removed,
                        'final_items': len(df)
                    }
                }
                
            except Exception as e:
                print(f"❌ ОШИБКА: {str(e)}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
    
    # Тестируем
    processor = TestProcessor()
    result = processor.load_sales_file_fixed(file_path)
    
    # Сравниваем с ожидаемым результатом
    expected_items = 8943
    
    if result['success']:
        actual_items = result['total_items']
        difference = expected_items - actual_items
        
        print(f"\n🎯 СРАВНЕНИЕ С ОЖИДАЕМЫМ:")
        print(f"Ожидалось: {expected_items:,} товаров")
        print(f"Получилось: {actual_items:,} товаров")
        print(f"Разница: {difference:,} товаров")
        
        if difference <= 500:  # Допустимая погрешность
            print("✅ УСПЕХ: Количество товаров в пределах нормы!")
        elif difference <= 1500:
            print("⚠️ ВНИМАНИЕ: Умеренная потеря товаров")
        else:
            print("❌ ПРОБЛЕМА: Значительная потеря товаров")
            
        loss_percentage = (difference / expected_items) * 100 if expected_items > 0 else 0
        print(f"Потеря составляет: {loss_percentage:.1f}%")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        stats = result['processing_stats']
        
        if stats['lost_nomenclature'] > 1000:
            print("⚠️ Большие потери на очистке номенклатуры - проверьте качество данных")
        
        if stats['lost_quantity'] > 2000:
            print("⚠️ Большие потери на фильтрации количества - возможно неправильная колонка")
        
        if difference > 1000:
            print("⚠️ Рассмотрите возможность более мягких критериев фильтрации")
            print("⚠️ Проверьте правильность определения колонки AD (индекс 30)")
    else:
        print(f"❌ ОШИБКА ОБРАБОТКИ: {result['error']}")
    
    return result

if __name__ == "__main__":
    # Укажите путь к вашему файлу
    file_path = "шымкент скл  прод мая 24май 25 мини.xlsx"  # Замените на ваш файл
    
    print("🚀 ЗАПУСК ТЕСТА ИСПРАВЛЕННОЙ ОБРАБОТКИ")
    result = test_fixed_ads_processing(file_path)
    
    print(f"\n✨ Тест завершен!")