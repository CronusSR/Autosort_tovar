#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика потери товаров в ABC анализе
Пошаговый анализ где теряются товары: 8942 → 3915
"""

import pandas as pd
import numpy as np
import io
from typing import Dict

def diagnose_abc_data_loss(file_path: str):
    """
    Пошаговая диагностика потери товаров в ABC анализе
    
    Args:
        file_path: Путь к файлу ABC анализа
    """
    
    print("🔍 ДИАГНОСТИКА ПОТЕРИ ТОВАРОВ В ABC АНАЛИЗЕ")
    print("=" * 60)
    print(f"📁 Файл: {file_path}")
    print(f"🎯 Ожидается: 8942 товара")
    print(f"❌ Получается: 3915 товаров")
    print(f"📉 Потеря: {8942 - 3915} товаров ({(8942 - 3915)/8942*100:.1f}%)")
    
    try:
        # Шаг 1: Чтение файла
        print(f"\n1️⃣ ЧТЕНИЕ ИСХОДНОГО ФАЙЛА")
        print("-" * 40)
        
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"📋 Доступные листы: {excel_file.sheet_names}")
        
        # Определяем целевой лист
        target_sheet = None
        sheet_priority = ['abc', 'Лист1', 'Sheet1', 'лист1']
        
        for priority_sheet in sheet_priority:
            if priority_sheet in excel_file.sheet_names:
                target_sheet = priority_sheet
                break
        
        if target_sheet is None:
            target_sheet = excel_file.sheet_names[0]
        
        print(f"🎯 Выбранный лист: '{target_sheet}'")
        
        # Читаем данные
        df_raw = pd.read_excel(excel_file, sheet_name=target_sheet, engine='openpyxl')
        initial_rows = len(df_raw)
        initial_cols = len(df_raw.columns)
        
        print(f"📊 Исходные размеры: {initial_rows} строк × {initial_cols} колонок")
        
        # Анализируем первые 20 строк для понимания структуры
        print(f"\n📋 Анализ первых 20 строк:")
        for i in range(min(20, len(df_raw))):
            row_preview = []
            for j in range(min(5, len(df_raw.columns))):
                cell_val = str(df_raw.iloc[i, j])
                if len(cell_val) > 15:
                    cell_val = cell_val[:15] + "..."
                row_preview.append(cell_val)
            
            row_info = f"   Строка {i+1:2d}: {row_preview}"
            
            # Пытаемся определить является ли строка данными
            first_cell = str(df_raw.iloc[i, 0]).strip().lower()
            is_likely_data = (
                len(first_cell) > 2 and 
                first_cell not in ['', 'nan', 'none'] and
                'заголовок' not in first_cell and
                'header' not in first_cell and
                not first_cell.isdigit()
            )
            
            if is_likely_data:
                row_info += " ← ВОЗМОЖНО ДАННЫЕ"
            
            print(row_info)
        
        # Шаг 2: Поиск начала данных
        print(f"\n2️⃣ ПОИСК НАЧАЛА ДАННЫХ")
        print("-" * 40)
        
        data_start_candidates = []
        
        for i in range(min(25, len(df_raw))):  # Проверяем первые 25 строк
            row = df_raw.iloc[i]
            
            # Анализируем первые несколько ячеек
            analysis = {
                'row_index': i,
                'row_number': i + 1,
                'first_cell': str(row.iloc[0]).strip(),
                'non_empty_cells': sum(1 for cell in row if pd.notna(cell) and str(cell).strip()),
                'has_long_text': any(len(str(cell)) > 10 for cell in row if pd.notna(cell)),
                'all_empty': all(pd.isna(cell) or str(cell).strip() == '' for cell in row),
                'likely_header': any(keyword in str(row.iloc[0]).lower() for keyword in ['заголовок', 'header', 'название', 'наименование']),
                'likely_data': False
            }
            
            # Определяем вероятность того, что это данные
            first_cell_clean = analysis['first_cell'].lower()
            if (len(first_cell_clean) > 3 and 
                not analysis['all_empty'] and
                not analysis['likely_header'] and
                first_cell_clean not in ['', 'nan', 'none'] and
                not first_cell_clean.isdigit() and
                analysis['non_empty_cells'] >= 2):
                analysis['likely_data'] = True
            
            data_start_candidates.append(analysis)
            
            status = "📍 ДАННЫЕ" if analysis['likely_data'] else "📋 заголовок/пустая"
            print(f"   Строка {analysis['row_number']:2d}: '{analysis['first_cell'][:30]}' | "
                  f"Заполнено: {analysis['non_empty_cells']} | {status}")
        
        # Выбираем лучшего кандидата
        data_candidates = [c for c in data_start_candidates if c['likely_data']]
        
        if data_candidates:
            best_candidate = min(data_candidates, key=lambda x: x['row_index'])
            data_start_row = best_candidate['row_index']
            print(f"\n✅ Выбрано начало данных: строка {data_start_row + 1}")
            print(f"   Первая номенклатура: '{best_candidate['first_cell'][:50]}'")
        else:
            data_start_row = 5  # Дефолтное значение
            print(f"\n⚠️ Автоматическое определение не удалось, используем строку {data_start_row + 1}")
        
        # Шаг 3: Применение отступа
        print(f"\n3️⃣ ПРИМЕНЕНИЕ ОТСТУПА")
        print("-" * 40)
        
        df_after_offset = df_raw.iloc[data_start_row:].copy()
        df_after_offset = df_after_offset.reset_index(drop=True)
        
        rows_after_offset = len(df_after_offset)
        lost_in_offset = initial_rows - rows_after_offset
        
        print(f"📊 После применения отступа: {rows_after_offset} строк")
        print(f"📉 Потеряно на отступе: {lost_in_offset} строк")
        
        # Шаг 4: Назначение колонок
        print(f"\n4️⃣ НАЗНАЧЕНИЕ КОЛОНОК")
        print("-" * 40)
        
        actual_columns = len(df_after_offset.columns)
        print(f"📊 Доступно колонок: {actual_columns}")
        
        # Показываем примеры данных в колонках
        print(f"📋 Примеры данных в первых колонках:")
        for j in range(min(6, actual_columns)):
            col_sample = df_after_offset.iloc[:5, j].tolist()
            print(f"   Колонка {j}: {col_sample}")
        
        # Назначаем колонки
        if actual_columns >= 4:
            df_after_offset.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + \
                                    [f'extra_col_{i}' for i in range(4, actual_columns)]
            print("✅ Применена стандартная схема колонок (4+ колонки)")
        elif actual_columns == 3:
            df_after_offset.columns = ['nomenclature', 'category', 'annual_sales']
            print("✅ Применена упрощенная схема колонок (3 колонки)")
        else:
            base_names = ['nomenclature', 'annual_sales']
            df_after_offset.columns = base_names[:actual_columns] + \
                                    [f'col_{i}' for i in range(len(base_names), actual_columns)]
            print(f"⚠️ Применена минимальная схема колонок ({actual_columns} колонки)")
        
        # Шаг 5: Пошаговая очистка номенклатуры
        print(f"\n5️⃣ ОЧИСТКА НОМЕНКЛАТУРЫ (ПОШАГОВО)")
        print("-" * 40)
        
        df_cleaning = df_after_offset.copy()
        cleaning_steps = []
        
        # Исходное состояние
        step0_count = len(df_cleaning)
        cleaning_steps.append(f"Исходно после отступа: {step0_count}")
        print(f"   📊 Исходно: {step0_count} строк")
        
        # Анализируем номенклатуру ДО очистки
        nomenclature_analysis = {
            'total': len(df_cleaning['nomenclature']),
            'nan_values': df_cleaning['nomenclature'].isna().sum(),
            'empty_strings': (df_cleaning['nomenclature'].astype(str).str.strip() == '').sum(),
            'nan_strings': (df_cleaning['nomenclature'].astype(str).str.lower() == 'nan').sum(),
            'none_strings': (df_cleaning['nomenclature'].astype(str).str.lower() == 'none').sum(),
            'digit_only': df_cleaning['nomenclature'].astype(str).str.isdigit().sum(),
            'valid_looking': 0
        }
        
        # Считаем валидные на вид
        for val in df_cleaning['nomenclature']:
            val_str = str(val).strip().lower()
            if (len(val_str) > 2 and 
                val_str not in ['nan', 'none', ''] and 
                not val_str.isdigit() and
                pd.notna(val)):
                nomenclature_analysis['valid_looking'] += 1
        
        print(f"   📋 Анализ номенклатуры ДО очистки:")
        print(f"      • Всего значений: {nomenclature_analysis['total']}")
        print(f"      • NaN значений: {nomenclature_analysis['nan_values']}")
        print(f"      • Пустых строк: {nomenclature_analysis['empty_strings']}")
        print(f"      • Строк 'nan': {nomenclature_analysis['nan_strings']}")
        print(f"      • Строк 'none': {nomenclature_analysis['none_strings']}")
        print(f"      • Только цифры: {nomenclature_analysis['digit_only']}")
        print(f"      • Валидных на вид: {nomenclature_analysis['valid_looking']}")
        
        # Пошаговая очистка
        
        # Шаг 5.1: Удаление NaN
        step1_before = len(df_cleaning)
        df_cleaning = df_cleaning.dropna(subset=['nomenclature'])
        step1_after = len(df_cleaning)
        step1_lost = step1_before - step1_after
        cleaning_steps.append(f"После dropna(): {step1_after} (-{step1_lost})")
        print(f"   🔄 После dropna(): {step1_after} строк (-{step1_lost})")
        
        # Шаг 5.2: Удаление пустых строк
        step2_before = len(df_cleaning)
        df_cleaning = df_cleaning[df_cleaning['nomenclature'].astype(str).str.strip() != '']
        step2_after = len(df_cleaning)
        step2_lost = step2_before - step2_after
        cleaning_steps.append(f"После удаления пустых: {step2_after} (-{step2_lost})")
        print(f"   🔄 После удаления пустых строк: {step2_after} строк (-{step2_lost})")
        
        # Шаг 5.3: Удаление 'nan'
        step3_before = len(df_cleaning)
        df_cleaning = df_cleaning[df_cleaning['nomenclature'].astype(str).str.lower() != 'nan']
        step3_after = len(df_cleaning)
        step3_lost = step3_before - step3_after
        cleaning_steps.append(f"После удаления 'nan': {step3_after} (-{step3_lost})")
        print(f"   🔄 После удаления 'nan': {step3_after} строк (-{step3_lost})")
        
        # Шаг 5.4: Удаление только цифр
        step4_before = len(df_cleaning)
        df_cleaning = df_cleaning[~df_cleaning['nomenclature'].astype(str).str.isdigit()]
        step4_after = len(df_cleaning)
        step4_lost = step4_before - step4_after
        cleaning_steps.append(f"После удаления цифр: {step4_after} (-{step4_lost})")
        print(f"   🔄 После удаления только цифр: {step4_after} строк (-{step4_lost})")
        
        # Показываем примеры оставшейся номенклатуры
        print(f"\n   📋 Примеры оставшейся номенклатуры:")
        remaining_samples = df_cleaning['nomenclature'].head(10).tolist()
        for i, sample in enumerate(remaining_samples, 1):
            print(f"      {i:2d}. {str(sample)[:60]}")
        
        # Шаг 6: Анализ продаж
        print(f"\n6️⃣ АНАЛИЗ КОЛОНКИ ПРОДАЖ")
        print("-" * 40)
        
        sales_column = df_cleaning['annual_sales']
        
        sales_analysis = {
            'total': len(sales_column),
            'nan_values': sales_column.isna().sum(),
            'empty_strings': (sales_column.astype(str).str.strip() == '').sum(),
            'nan_strings': (sales_column.astype(str).str.lower() == 'nan').sum(),
            'none_strings': (sales_column.astype(str).str.lower() == 'none').sum(),
            'zero_values': 0,
            'positive_values': 0,
            'negative_values': 0,
            'convertible_to_numeric': 0
        }
        
        print(f"   📊 Исходный тип колонки продаж: {sales_column.dtype}")
        print(f"   📋 Анализ значений продаж ДО обработки:")
        print(f"      • Всего значений: {sales_analysis['total']}")
        print(f"      • NaN значений: {sales_analysis['nan_values']}")
        print(f"      • Пустых строк: {sales_analysis['empty_strings']}")
        print(f"      • Строк 'nan': {sales_analysis['nan_strings']}")
        print(f"      • Строк 'none': {sales_analysis['none_strings']}")
        
        # Примеры исходных значений
        sample_sales = sales_column.head(15).tolist()
        print(f"   📋 Примеры исходных значений продаж:")
        for i, sample in enumerate(sample_sales, 1):
            print(f"      {i:2d}. '{sample}' (тип: {type(sample).__name__})")
        
        # Тестируем преобразование в числовой формат
        sales_numeric_test = pd.to_numeric(sales_column, errors='coerce')
        convertible_count = sales_numeric_test.notna().sum()
        nan_after_conversion = sales_numeric_test.isna().sum()
        
        print(f"\n   🔢 Тест преобразования в числовой формат:")
        print(f"      • Конвертируемых в числа: {convertible_count}")
        print(f"      • NaN после конвертации: {nan_after_conversion}")
        
        if convertible_count > 0:
            valid_sales = sales_numeric_test.dropna()
            sales_analysis['zero_values'] = (valid_sales == 0).sum()
            sales_analysis['positive_values'] = (valid_sales > 0).sum()
            sales_analysis['negative_values'] = (valid_sales < 0).sum()
            
            print(f"      • Нулевых значений: {sales_analysis['zero_values']}")
            print(f"      • Положительных значений: {sales_analysis['positive_values']}")
            print(f"      • Отрицательных значений: {sales_analysis['negative_values']}")
            
            if len(valid_sales) > 0:
                print(f"      • Минимум: {valid_sales.min()}")
                print(f"      • Максимум: {valid_sales.max()}")
                print(f"      • Среднее: {valid_sales.mean():.2f}")
        
        # Шаг 7: Применяем обработку продаж (БЕЗ ИСКЛЮЧЕНИЯ товаров)
        print(f"\n7️⃣ ИСПРАВЛЕННАЯ ОБРАБОТКА ПРОДАЖ")
        print("-" * 40)
        
        step7_before = len(df_cleaning)
        
        # Преобразуем в числовой формат
        df_cleaning['annual_sales'] = pd.to_numeric(df_cleaning['annual_sales'], errors='coerce')
        
        # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: заменяем NaN на 0, НЕ удаляем строки
        nan_count_before_fill = df_cleaning['annual_sales'].isna().sum()
        df_cleaning['annual_sales'] = df_cleaning['annual_sales'].fillna(0)
        
        # Заменяем отрицательные на 0
        negative_count = (df_cleaning['annual_sales'] < 0).sum()
        df_cleaning.loc[df_cleaning['annual_sales'] < 0, 'annual_sales'] = 0
        
        step7_after = len(df_cleaning)
        step7_lost = step7_before - step7_after
        
        print(f"   📊 ДО обработки продаж: {step7_before} товаров")
        print(f"   🔄 NaN заменено на 0: {nan_count_before_fill}")
        print(f"   🔄 Отрицательных заменено на 0: {negative_count}")
        print(f"   📊 ПОСЛЕ обработки продаж: {step7_after} товаров")
        print(f"   📉 Потеряно товаров: {step7_lost} (ДОЛЖНО БЫТЬ 0!)")
        
        # Финальная статистика продаж
        final_zero_count = (df_cleaning['annual_sales'] == 0).sum()
        final_positive_count = (df_cleaning['annual_sales'] > 0).sum()
        
        print(f"   📊 Финальная статистика продаж:")
        print(f"      • С продажами = 0: {final_zero_count}")
        print(f"      • С продажами > 0: {final_positive_count}")
        print(f"      • Всего: {final_zero_count + final_positive_count}")
        
        # Шаг 8: Обработка категорий
        print(f"\n8️⃣ ОБРАБОТКА КАТЕГОРИЙ")
        print("-" * 40)
        
        step8_before = len(df_cleaning)
        
        if 'category' in df_cleaning.columns:
            # Заполняем пустые категории
            df_cleaning['category'] = df_cleaning['category'].astype(str).str.strip()
            
            category_analysis = {
                'nan_values': (df_cleaning['category'] == 'nan').sum(),
                'empty_values': (df_cleaning['category'] == '').sum(),
                'none_values': (df_cleaning['category'] == 'None').sum()
            }
            
            print(f"   📋 Анализ категорий:")
            print(f"      • 'nan' значений: {category_analysis['nan_values']}")
            print(f"      • Пустых значений: {category_analysis['empty_values']}")
            print(f"      • 'None' значений: {category_analysis['none_values']}")
            
            df_cleaning['category'] = df_cleaning['category'].replace(['nan', 'None', ''], 'Без категории')
            
            # Заполнение из подкатегорий
            if 'subcategory' in df_cleaning.columns:
                df_cleaning['subcategory'] = df_cleaning['subcategory'].astype(str).str.strip()
                mask_empty_category = df_cleaning['category'].isin(['Без категории', 'nan', ''])
                mask_valid_subcategory = ~df_cleaning['subcategory'].isin(['nan', 'None', '', 'Без категории'])
                
                filled_from_sub = (mask_empty_category & mask_valid_subcategory).sum()
                df_cleaning.loc[mask_empty_category & mask_valid_subcategory, 'category'] = \
                    df_cleaning.loc[mask_empty_category & mask_valid_subcategory, 'subcategory']
                
                print(f"      • Заполнено из подкатегорий: {filled_from_sub}")
        else:
            df_cleaning['category'] = 'Общая категория'
            print("      • Создана общая категория")
        
        # ПРОБЛЕМНОЕ МЕСТО: Убираем строки с пустыми категориями
        step8_before_final_filter = len(df_cleaning)
        df_cleaning = df_cleaning[df_cleaning['category'].notna()]
        step8_middle = len(df_cleaning)
        df_cleaning = df_cleaning[df_cleaning['category'].astype(str).str.strip() != '']
        step8_after = len(df_cleaning)
        
        category_lost_notna = step8_before_final_filter - step8_middle
        category_lost_empty = step8_middle - step8_after
        total_category_lost = step8_before - step8_after
        
        print(f"   📊 ДО фильтрации категорий: {step8_before} товаров")
        print(f"   📊 После notna(): {step8_middle} товаров (-{category_lost_notna})")
        print(f"   📊 После удаления пустых: {step8_after} товаров (-{category_lost_empty})")
        print(f"   📉 ВСЕГО потеряно на категориях: {total_category_lost}")
        
        if total_category_lost > 0:
            print(f"   ⚠️ НАЙДЕНА ПРОБЛЕМА: Товары теряются на фильтрации категорий!")
        
        # Шаг 9: Удаление дубликатов
        print(f"\n9️⃣ УДАЛЕНИЕ ДУБЛИКАТОВ")
        print("-" * 40)
        
        step9_before = len(df_cleaning)
        duplicates_count = df_cleaning['nomenclature'].duplicated().sum()
        
        if duplicates_count > 0:
            print(f"   📊 Найдено дубликатов: {duplicates_count}")
            df_cleaning = df_cleaning.drop_duplicates(subset=['nomenclature'], keep='first')
            step9_after = len(df_cleaning)
            print(f"   📊 После удаления дубликатов: {step9_after} товаров (-{duplicates_count})")
        else:
            step9_after = step9_before
            print(f"   ✅ Дубликатов не найдено: {step9_after} товаров")
        
        # ИТОГОВАЯ ДИАГНОСТИКА
        print(f"\n🎯 ИТОГОВАЯ ДИАГНОСТИКА ПОТЕРИ ТОВАРОВ")
        print("=" * 60)
        
        total_lost = initial_rows - step9_after
        loss_percentage = (total_lost / initial_rows) * 100
        
        print(f"📊 БАЛАНС ТОВАРОВ:")
        print(f"   Исходно в файле: {initial_rows:,}")
        print(f"   Финально в ABC: {step9_after:,}")
        print(f"   ПОТЕРЯНО: {total_lost:,} ({loss_percentage:.1f}%)")
        
        print(f"\n📋 ДЕТАЛИЗАЦИЯ ПОТЕРЬ:")
        for step in cleaning_steps:
            print(f"   • {step}")
        print(f"   • После обработки продаж: {step7_after} (-{step7_lost})")
        print(f"   • После обработки категорий: {step8_after} (-{total_category_lost})")
        print(f"   • После удаления дубликатов: {step9_after} (-{duplicates_count})")
        
        # РЕКОМЕНДАЦИИ
        print(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        if step1_lost > 1000:
            print(f"   🔧 Большие потери на NaN номенклатуре ({step1_lost})")
            print(f"      → Проверьте правильность определения начала данных")
        
        if step2_lost > 500:
            print(f"   🔧 Большие потери на пустых строках ({step2_lost})")
            print(f"      → Возможно, в номенклатуре есть валидные пустые значения")
        
        if total_category_lost > 1000:
            print(f"   🔧 КРИТИЧНО: Большие потери на категориях ({total_category_lost})")
            print(f"      → НЕ удаляйте строки с пустыми категориями!")
            print(f"      → Заменяйте пустые категории на 'Без категории'")
        
        if step7_lost > 0:
            print(f"   🔧 КРИТИЧНО: Потери на обработке продаж ({step7_lost})")
            print(f"      → Убедитесь что используете fillna(0) вместо фильтрации")
        
        print(f"\n🔍 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА:")
        
        # Проверяем что происходит если НЕ фильтровать категории
        if total_category_lost > 0:
            print(f"   🧪 Тест без фильтрации категорий:")
            test_df = df_after_offset.copy()
            test_df.columns = df_cleaning.columns
            
            # Применяем только очистку номенклатуры и продаж
            test_df = test_df.dropna(subset=['nomenclature'])
            test_df = test_df[test_df['nomenclature'].astype(str).str.strip() != '']
            test_df = test_df[test_df['nomenclature'].astype(str).str.lower() != 'nan']
            test_df = test_df[~test_df['nomenclature'].astype(str).str.isdigit()]
            
            test_df['annual_sales'] = pd.to_numeric(test_df['annual_sales'], errors='coerce').fillna(0)
            test_df.loc[test_df['annual_sales'] < 0, 'annual_sales'] = 0
            
            # НЕ фильтруем категории, только заполняем
            if 'category' in test_df.columns:
                test_df['category'] = test_df['category'].astype(str).str.strip()
                test_df['category'] = test_df['category'].replace(['nan', 'None', ''], 'Без категории')
            else:
                test_df['category'] = 'Общая категория'
            
            test_df = test_df.drop_duplicates(subset=['nomenclature'], keep='first')
            
            test_final_count = len(test_df)
            test_total_lost = initial_rows - test_final_count
            
            print(f"      БЕЗ фильтрации категорий: {test_final_count:,} товаров")
            print(f"      Потеря сократилась до: {test_total_lost:,} товаров")
            print(f"      Экономия: {total_lost - test_total_lost:,} товаров!")
        
        return df_cleaning
        
    except Exception as e:
        print(f"❌ ОШИБКА ДИАГНОСТИКИ: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Укажите путь к вашему файлу
    file_path = "исходники.xlsx"  # Замените на ваш файл
    
    print("🚀 ЗАПУСК ДИАГНОСТИКИ ПОТЕРИ ТОВАРОВ В ABC")
    result = diagnose_abc_data_loss(file_path)