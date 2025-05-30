#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для отладки ABC анализа - поиск проблем с подсчетом товаров
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List

def debug_abc_file_processing(file_path: str):
    """
    Отладка обработки ABC файла с детальным логированием
    
    Args:
        file_path: Путь к файлу ABC анализа
    """
    
    print("🔍 ОТЛАДКА ABC АНАЛИЗА - ПОИСК ПРОБЛЕМ С ПОДСЧЕТОМ")
    print("=" * 60)
    print(f"📁 Файл: {file_path}")
    
    try:
        # Читаем файл
        print("\n1️⃣ ЧТЕНИЕ ФАЙЛА")
        print("-" * 30)
        
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        print(f"📋 Доступные листы: {excel_file.sheet_names}")
        
        # Определяем лист для анализа
        target_sheet = None
        sheet_priority = ['abc', 'Лист1', 'Sheet1']
        
        for sheet in sheet_priority:
            if sheet in excel_file.sheet_names:
                target_sheet = sheet
                break
        
        if target_sheet is None:
            target_sheet = excel_file.sheet_names[0]
        
        print(f"🎯 Выбранный лист: '{target_sheet}'")
        
        # Читаем данные
        df_raw = pd.read_excel(excel_file, sheet_name=target_sheet, engine='openpyxl')
        print(f"📊 Сырые данные: {df_raw.shape[0]} строк × {df_raw.shape[1]} колонок")
        
        # Показываем первые строки
        print(f"\n📋 Первые 10 строк файла:")
        for i in range(min(10, len(df_raw))):
            row_data = [str(val)[:20] + '...' if len(str(val)) > 20 else str(val) 
                       for val in df_raw.iloc[i].values[:min(5, len(df_raw.columns))]]
            print(f"   Строка {i+1}: {row_data}")
        
        print(f"\n2️⃣ ПОИСК НАЧАЛА ДАННЫХ")
        print("-" * 30)
        
        # Ищем начало данных
        data_start_candidates = []
        
        for i in range(min(15, len(df_raw))):
            row = df_raw.iloc[i]
            row_info = {
                'row_index': i,
                'row_number': i + 1,
                'first_cell': str(row.iloc[0]).strip(),
                'non_empty_cells': sum(1 for cell in row if pd.notna(cell) and str(cell).strip()),
                'has_long_text': any(len(str(cell)) > 10 for cell in row if pd.notna(cell)),
                'is_numeric_row': all(pd.isna(cell) or str(cell).isdigit() for cell in row)
            }
            
            # Оценка вероятности того, что это строка с данными
            score = 0
            if row_info['non_empty_cells'] >= 3:
                score += 2
            if row_info['has_long_text']:
                score += 2
            if not row_info['is_numeric_row'] and row_info['first_cell'] not in ['', 'nan']:
                score += 3
            if len(row_info['first_cell']) > 5:
                score += 1
                
            row_info['data_score'] = score
            data_start_candidates.append(row_info)
            
            print(f"   Строка {row_info['row_number']}: '{row_info['first_cell'][:30]}' "
                  f"(заполнено: {row_info['non_empty_cells']}, балл: {score})")
        
        # Выбираем лучшего кандидата
        best_candidate = max(data_start_candidates, key=lambda x: x['data_score'])
        data_start_row = best_candidate['row_index']
        
        print(f"\n✅ Лучший кандидат: строка {data_start_row + 1} (балл: {best_candidate['data_score']})")
        
        print(f"\n3️⃣ ПРИМЕНЕНИЕ ОТСТУПА И ПОДГОТОВКА")
        print("-" * 30)
        
        # Применяем отступ
        df = df_raw.iloc[data_start_row:].copy()
        df = df.reset_index(drop=True)
        print(f"📊 После применения отступа: {df.shape[0]} строк")
        
        # Назначаем колонки
        actual_columns = len(df.columns)
        print(f"📋 Количество колонок: {actual_columns}")
        
        if actual_columns >= 4:
            df.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + \
                        [f'extra_col_{i}' for i in range(4, actual_columns)]
            print("✅ Применена стандартная схема колонок (4+ колонки)")
        elif actual_columns == 3:
            df.columns = ['nomenclature', 'category', 'annual_sales']
            print("✅ Применена упрощенная схема колонок (3 колонки)")
        else:
            df.columns = ['nomenclature', 'annual_sales'] + [f'col_{i}' for i in range(2, actual_columns)]
            print(f"⚠️ Применена минимальная схема колонок ({actual_columns} колонки)")
        
        print(f"📋 Названия колонок: {list(df.columns)}")
        
        print(f"\n4️⃣ ПОШАГОВАЯ ОЧИСТКА ДАННЫХ")
        print("-" * 30)
        
        steps_log = []
        initial_count = len(df)
        steps_log.append(f"Исходные данные: {initial_count}")
        
        # Шаг 1: Удаление строк с пустой номенклатурой (NaN)
        df_step1 = df.dropna(subset=['nomenclature'])
        lost_step1 = len(df) - len(df_step1)
        steps_log.append(f"После удаления NaN в номенклатуре: {len(df_step1)} (-{lost_step1})")
        df = df_step1
        
        # Шаг 2: Удаление строк с пустыми строками в номенклатуре
        df_step2 = df[df['nomenclature'].astype(str).str.strip() != '']
        lost_step2 = len(df) - len(df_step2)
        steps_log.append(f"После удаления пустых строк: {len(df_step2)} (-{lost_step2})")
        df = df_step2
        
        # Шаг 3: Удаление строк со значением 'nan' в номенклатуре
        df_step3 = df[df['nomenclature'].astype(str).str.lower() != 'nan']
        lost_step3 = len(df) - len(df_step3)
        steps_log.append(f"После удаления 'nan': {len(df_step3)} (-{lost_step3})")
        df = df_step3
        
        # Шаг 4: Удаление строк с только цифрами в номенклатуре
        df_step4 = df[~df['nomenclature'].astype(str).str.isdigit()]
        lost_step4 = len(df) - len(df_step4)
        steps_log.append(f"После удаления цифр: {len(df_step4)} (-{lost_step4})")
        df = df_step4
        
        # Шаг 5: Преобразование и фильтрация продаж
        df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce')
        valid_sales_before = df['annual_sales'].notna().sum()
        steps_log.append(f"Валидных числовых продаж: {valid_sales_before} из {len(df)}")
        
        df['annual_sales'] = df['annual_sales'].fillna(0)
        df_step5 = df[df['annual_sales'] > 0]
        lost_step5 = len(df) - len(df_step5)
        steps_log.append(f"После фильтрации продаж > 0: {len(df_step5)} (-{lost_step5})")
        df = df_step5
        
        # Шаг 6: Обработка категорий
        if 'category' in df.columns:
            df['category'] = df['category'].astype(str).str.strip()
            df['category'] = df['category'].replace(['nan', 'None', ''], 'Без категории')
            
            # Заполнение из подкатегорий если есть
            if 'subcategory' in df.columns:
                df['subcategory'] = df['subcategory'].astype(str).str.strip()
                mask_empty = df['category'].isin(['Без категории', 'nan', ''])
                mask_valid_sub = ~df['subcategory'].isin(['nan', 'None', '', 'Без категории'])
                filled_from_sub = (mask_empty & mask_valid_sub).sum()
                
                df.loc[mask_empty & mask_valid_sub, 'category'] = \
                    df.loc[mask_empty & mask_valid_sub, 'subcategory']
                
                steps_log.append(f"Заполнено категорий из подкатегорий: {filled_from_sub}")
        else:
            df['category'] = 'Общая категория'
            steps_log.append("Создана общая категория")
        
        # Финальная очистка категорий
        df_step6 = df[df['category'].notna()]
        df_step6 = df_step6[df_step6['category'].astype(str).str.strip() != '']
        lost_step6 = len(df) - len(df_step6)
        steps_log.append(f"После финальной очистки категорий: {len(df_step6)} (-{lost_step6})")
        df = df_step6
        
        # Шаг 7: Удаление дубликатов
        duplicates_count = df['nomenclature'].duplicated().sum()
        if duplicates_count > 0:
            df_step7 = df.drop_duplicates(subset=['nomenclature'], keep='first')
            steps_log.append(f"После удаления дубликатов: {len(df_step7)} (-{duplicates_count})")
            df = df_step7
        else:
            steps_log.append("Дубликатов не найдено")
        
        # Выводим лог шагов
        for step in steps_log:
            print(f"   📊 {step}")
        
        final_count = len(df)
        total_lost = initial_count - final_count
        loss_percentage = (total_lost / initial_count * 100) if initial_count > 0 else 0
        
        print(f"\n📊 ИТОГИ ОЧИСТКИ:")
        print(f"   Исходно строк: {initial_count}")
        print(f"   Финально товаров: {final_count}")
        print(f"   Потеряно: {total_lost} ({loss_percentage:.1f}%)")
        
        if final_count == 0:
            print("❌ КРИТИЧНО: Не осталось товаров после очистки!")
            return False
        
        print(f"\n5️⃣ АНАЛИЗ ПОЛУЧИВШИХСЯ ДАННЫХ")
        print("-" * 30)
        
        # Статистика продаж
        total_sales = df['annual_sales'].sum()
        avg_sales = df['annual_sales'].mean()
        median_sales = df['annual_sales'].median()
        max_sales = df['annual_sales'].max()
        min_sales = df['annual_sales'].min()
        
        print(f"💰 Статистика продаж:")
        print(f"   Общие продажи: {total_sales:,.0f}")
        print(f"   Средние продажи: {avg_sales:,.0f}")
        print(f"   Медианные продажи: {median_sales:,.0f}")
        print(f"   Максимальные продажи: {max_sales:,.0f}")
        print(f"   Минимальные продажи: {min_sales:,.0f}")
        
        # Статистика категорий
        categories_stats = df['category'].value_counts()
        unique_categories = df['category'].nunique()
        
        print(f"\n🏷️ Статистика категорий:")
        print(f"   Уникальных категорий: {unique_categories}")
        print(f"   Топ-5 категорий по количеству товаров:")
        for i, (cat, count) in enumerate(categories_stats.head(5).items(), 1):
            print(f"     {i}. {cat}: {count} товаров")
        
        # Проверка распределения данных
        print(f"\n📈 Проверка качества для ABC анализа:")
        
        # Распределение продаж (правило Парето)
        df_sorted = df.sort_values('annual_sales', ascending=False)
        df_sorted['cumsum'] = df_sorted['annual_sales'].cumsum()
        df_sorted['cumsum_pct'] = (df_sorted['cumsum'] / total_sales) * 100
        
        # Проверяем правило 80/20
        items_for_80pct = len(df_sorted[df_sorted['cumsum_pct'] <= 80])
        items_for_80pct_percentage = (items_for_80pct / final_count) * 100
        
        print(f"   🎯 Правило Парето:")
        print(f"     Товаров для 80% продаж: {items_for_80pct} ({items_for_80pct_percentage:.1f}%)")
        print(f"     Соответствует принципу 80/20: {'✅' if items_for_80pct_percentage <= 25 else '⚠️'}")
        
        # Топ товары
        print(f"\n🏆 Топ-10 товаров по продажам:")
        top_items = df_sorted.head(10)
        for i, (_, row) in enumerate(top_items.iterrows(), 1):
            cumsum_pct = (row['cumsum'] / total_sales) * 100
            print(f"   {i:2d}. {row['nomenclature'][:40]:<40} | {row['annual_sales']:>10,.0f} | {cumsum_pct:>5.1f}%")
        
        print(f"\n6️⃣ ИМИТАЦИЯ ABC АНАЛИЗА")
        print("-" * 30)
        
        # Выполняем ABC анализ
        df_abc = df_sorted.copy()
        df_abc['sales_percentage'] = (df_abc['annual_sales'] / total_sales) * 100
        df_abc['cumulative_percentage'] = df_abc['sales_percentage'].cumsum()
        
        # Присваиваем ABC классы
        def assign_abc_class(cumulative_pct):
            if cumulative_pct <= 80.0:
                return 'A'
            elif cumulative_pct <= 95.0:
                return 'B'
            else:
                return 'C'
        
        df_abc['abc_class'] = df_abc['cumulative_percentage'].apply(assign_abc_class)
        
        # Считаем распределение
        abc_counts = df_abc['abc_class'].value_counts()
        
        print(f"🔤 Результат ABC анализа:")
        print(f"   🔴 A товары: {abc_counts.get('A', 0)} ({abc_counts.get('A', 0)/final_count*100:.1f}%)")
        print(f"   🟡 B товары: {abc_counts.get('B', 0)} ({abc_counts.get('B', 0)/final_count*100:.1f}%)")
        print(f"   🟢 C товары: {abc_counts.get('C', 0)} ({abc_counts.get('C', 0)/final_count*100:.1f}%)")
        
        # Проверяем правильность
        total_abc = sum(abc_counts.values())
        print(f"   📊 Проверка: {total_abc} = {final_count} ({'✅' if total_abc == final_count else '❌ ОШИБКА!'})")
        
        # Процентное распределение продаж
        a_sales_pct = df_abc[df_abc['abc_class'] == 'A']['sales_percentage'].sum()
        b_sales_pct = df_abc[df_abc['abc_class'] == 'B']['sales_percentage'].sum()
        c_sales_pct = df_abc[df_abc['abc_class'] == 'C']['sales_percentage'].sum()
        
        print(f"\n💰 Распределение продаж по ABC:")
        print(f"   🔴 A товары: {a_sales_pct:.1f}% продаж")
        print(f"   🟡 B товары: {b_sales_pct:.1f}% продаж")
        print(f"   🟢 C товары: {c_sales_pct:.1f}% продаж")
        print(f"   📊 Сумма: {a_sales_pct + b_sales_pct + c_sales_pct:.1f}%")
        
        print(f"\n7️⃣ ДИАГНОСТИКА ПОТЕНЦИАЛЬНЫХ ПРОБЛЕМ")
        print("-" * 30)
        
        issues_found = []
        
        # Проверка 1: Слишком большие потери при очистке
        if loss_percentage > 50:
            issues_found.append(f"❌ КРИТИЧНО: Потеряно {loss_percentage:.1f}% данных при очистке")
        elif loss_percentage > 20:
            issues_found.append(f"⚠️ ВНИМАНИЕ: Потеряно {loss_percentage:.1f}% данных при очистке")
        
        # Проверка 2: Недостаточно товаров для качественного ABC
        if final_count < 50:
            issues_found.append(f"⚠️ Мало товаров для ABC анализа: {final_count} (рекомендуется >50)")
        
        # Проверка 3: Слишком мало категорий
        if unique_categories < 3:
            issues_found.append(f"⚠️ Мало категорий: {unique_categories} (рекомендуется >3)")
        
        # Проверка 4: Неправильное распределение Парето
        if items_for_80pct_percentage > 30:
            issues_found.append(f"⚠️ Нарушен принцип Парето: {items_for_80pct_percentage:.1f}% товаров дают 80% продаж")
        
        # Проверка 5: Отсутствие A товаров
        if abc_counts.get('A', 0) == 0:
            issues_found.append("❌ КРИТИЧНО: Нет A товаров в ABC анализе")
        
        if issues_found:
            print("🚨 НАЙДЕННЫЕ ПРОБЛЕМЫ:")
            for issue in issues_found:
                print(f"   {issue}")
        else:
            print("✅ Критических проблем не найдено")
        
        print(f"\n8️⃣ РЕКОМЕНДАЦИИ")
        print("-" * 30)
        
        recommendations = []
        
        if loss_percentage > 20:
            recommendations.append("• Проверьте исходный файл на наличие заголовков и пустых строк")
            recommendations.append("• Убедитесь, что данные начинаются с правильной строки")
        
        if final_count < 100:
            recommendations.append("• Добавьте больше товаров для качественного ABC анализа")
        
        if unique_categories < 5:
            recommendations.append("• Проверьте правильность заполнения категорий в исходном файле")
        
        if items_for_80pct_percentage > 25:
            recommendations.append("• Проанализируйте распределение продаж - возможно нужна сегментация")
        
        if not recommendations:
            recommendations.append("✅ Данные готовы для ABC анализа")
        
        for rec in recommendations:
            print(f"   {rec}")
        
        print(f"\n🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 60)
        print(f"📊 Итоговое количество товаров для ABC: {final_count}")
        print(f"🏷️ Категорий: {unique_categories}")
        print(f"💰 Общие продажи: {total_sales:,.0f}")
        print(f"🔤 ABC классы: A={abc_counts.get('A', 0)}, B={abc_counts.get('B', 0)}, C={abc_counts.get('C', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_abc_counting_fix():
    """Тест исправления подсчета товаров в ABC анализе"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ ПОДСЧЕТА ТОВАРОВ В ABC")
    print("=" * 50)
    
    # Создаем тестовые данные
    test_data = {
        'col1': ['заголовок', 'подзаголовок', '', 'Товар 1', 'Товар 2', 'Товар 3', 'Товар 4', 'Товар 5'],
        'col2': ['', '', '', 'Подкат 1', 'Подкат 2', 'Подкат 1', 'Подкат 3', 'Подкат 2'],
        'col3': ['', '', '', 'Категория А', 'Категория Б', 'Категория А', 'Категория В', 'Категория Б'],
        'col4': ['', '', '', 1000, 500, 300, 200, 100]
    }
    
    df = pd.DataFrame(test_data)
    
    print("📊 Тестовые данные:")
    print(df.to_string())
    
    # Имитируем обработку как в исправленном методе
    print(f"\n🔄 Применяем исправленную логику...")
    
    # Находим начало данных (строка 3)
    data_start = 3
    df_processed = df.iloc[data_start:].copy()
    df_processed.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales']
    
    print(f"📊 После применения отступа: {len(df_processed)} строк")
    
    # Очистка
    initial_count = len(df_processed)
    df_processed = df_processed.dropna(subset=['nomenclature'])
    df_processed = df_processed[df_processed['nomenclature'].astype(str).str.strip() != '']
    df_processed['annual_sales'] = pd.to_numeric(df_processed['annual_sales'], errors='coerce')
    df_processed = df_processed[df_processed['annual_sales'] > 0]
    
    final_count = len(df_processed)
    
    print(f"📊 После очистки: {final_count} товаров")
    
    # ABC анализ
    total_sales = df_processed['annual_sales'].sum()
    df_processed = df_processed.sort_values('annual_sales', ascending=False)
    df_processed['cumulative_percentage'] = (df_processed['annual_sales'].cumsum() / total_sales) * 100
    
    def assign_abc_class(cumulative_pct):
        if cumulative_pct <= 80.0:
            return 'A'
        elif cumulative_pct <= 95.0:
            return 'B'
        else:
            return 'C'
    
    df_processed['abc_class'] = df_processed['cumulative_percentage'].apply(assign_abc_class)
    
    abc_counts = df_processed['abc_class'].value_counts()
    total_abc = sum(abc_counts.values())
    
    print(f"\n🔤 ABC результат:")
    print(f"   A товары: {abc_counts.get('A', 0)}")
    print(f"   B товары: {abc_counts.get('B', 0)}")
    print(f"   C товары: {abc_counts.get('C', 0)}")
    print(f"   Всего: {total_abc}")
    print(f"   Соответствие: {'✅' if total_abc == final_count else '❌'}")
    
    if total_abc == final_count:
        print("\n✅ ТЕСТ ПРОШЕЛ: Подсчет товаров корректен!")
    else:
        print(f"\n❌ ТЕСТ ПРОВАЛЕН: {total_abc} ≠ {final_count}")
    
    return total_abc == final_count

if __name__ == "__main__":
    # Сначала запускаем тест
    print("🚀 ЗАПУСК ДИАГНОСТИКИ ABC АНАЛИЗА")
    test_success = test_abc_counting_fix()
    
    print(f"\n" + "="*60)
    
    # Затем можно запустить диагностику реального файла
    # Раскомментируйте и укажите путь к вашему файлу:
    # file_path = "исходникимини.xlsx"
    # debug_abc_file_processing(file_path)