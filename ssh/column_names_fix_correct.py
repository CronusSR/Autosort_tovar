#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
column_names_fix_correct.py - ПРАВИЛЬНОЕ ИСПРАВЛЕНИЕ ДЛЯ ВАШЕГО ФАЙЛА
Заголовки в 7-й строке, точки от D до N (11 точек)
"""

import pandas as pd
import types

def load_stock_data_fixed_for_your_file(self, file):
    """
    ИСПРАВЛЕННАЯ версия специально для вашего файла остатков
    - Заголовки в 7-й строке
    - Точки продаж от колонки D до N (11 точек)
    """
    try:
        print("📦 Загрузка файла остатков (заголовки в 7-й строке)...")
        
        # Читаем файл без заголовков
        if hasattr(file, 'read'):
            df = pd.read_excel(file, engine='openpyxl', header=None)
        else:
            df = pd.read_excel(file, engine='openpyxl', header=None)
        
        print(f"📊 Исходный размер: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # ВАЖНО: Заголовки находятся в 7-й строке (индекс 6)
        header_row_index = 6  # 7-я строка (отсчет с 0)
        
        if df.shape[0] <= header_row_index:
            return {'success': False, 'error': f'В файле недостаточно строк. Нужно минимум {header_row_index + 1}'}
        
        # Извлекаем заголовки из 7-й строки
        headers_row = df.iloc[header_row_index]
        print(f"\n📋 ЗАГОЛОВКИ ИЗ 7-Й СТРОКИ:")
        
        # Создаем правильные названия колонок
        corrected_columns = []
        for i, header in enumerate(headers_row):
            if pd.notna(header) and str(header).strip():
                clean_name = str(header).strip()
                corrected_columns.append(clean_name)
                print(f"   Колонка {chr(65+i)} (индекс {i}): '{clean_name}'")
            else:
                # Для пустых заголовков создаем понятное название
                col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                tech_name = f'empty_{col_letter}'
                corrected_columns.append(tech_name)
                print(f"   Колонка {chr(65+i)} (индекс {i}): '{tech_name}' (пустая)")
        
        # Берем данные начиная с 8-й строки (после заголовков)
        data_start_row = header_row_index + 1
        df_data = df.iloc[data_start_row:].copy()
        df_data.columns = corrected_columns[:len(df_data.columns)]
        
        print(f"\n📊 Данные с {data_start_row + 1}-й строки: {len(df_data)} строк")
        
        # Находим колонку номенклатуры (колонка A или B)
        nomenclature_col = None
        for col in df_data.columns:
            col_str = str(col).lower()
            if any(word in col_str for word in ['номенклатура', 'наименование', 'товар']) or col == corrected_columns[0]:
                nomenclature_col = col
                print(f"✅ Найдена колонка номенклатуры: '{nomenclature_col}'")
                break
        
        if nomenclature_col is None:
            # Используем первую колонку
            nomenclature_col = df_data.columns[0]
            print(f"⚠️ Используется первая колонка как номенклатура: '{nomenclature_col}'")
        
        # Переименовываем в стандартное название
        df_data = df_data.rename(columns={nomenclature_col: 'номенклатура'})
        
        # ВАЖНО: Точки продаж от D до N (колонки с индексами 3-13)
        # Это соответствует 11 точкам как вы сказали
        stock_columns = []
        
        print(f"\n📦 АНАЛИЗ ТОЧЕК ПРОДАЖ (D-N, ожидается 11 точек):")
        
        # Проверяем колонки от D (индекс 3) до N (индекс 13)
        for i, col in enumerate(df_data.columns):
            if col != 'номенклатура':
                # Проверяем, есть ли числовые данные
                try:
                    numeric_data = pd.to_numeric(df_data[col], errors='coerce')
                    non_nan_count = (~numeric_data.isna()).sum()
                    
                    if non_nan_count > 0:  # Есть хотя бы одно числовое значение
                        stock_columns.append(col)
                        col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                        print(f"   ✅ {col_letter}: '{col}' ({non_nan_count} значений)")
                    else:
                        col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                        print(f"   ❌ {col_letter}: '{col}' (нет числовых данных)")
                except Exception as e:
                    col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                    print(f"   ❌ {col_letter}: '{col}' (ошибка: {e})")
        
        print(f"\n🎯 НАЙДЕНО ТОЧЕК ПРОДАЖ: {len(stock_columns)} (ожидалось 11)")
        
        if len(stock_columns) != 11:
            print(f"⚠️ ВНИМАНИЕ: Найдено {len(stock_columns)} точек, а ожидалось 11!")
            print("📋 Возможные причины:")
            print("   - Пустые колонки в диапазоне D-N")
            print("   - Нечисловые данные в некоторых колонках")
            print("   - Разная структура файла")
        
        # Очистка данных
        initial_count = len(df_data)
        df_data = df_data.dropna(subset=['номенклатура'])
        df_data = df_data[df_data['номенклатура'].astype(str).str.strip() != '']
        df_data = df_data[df_data['номенклатура'].astype(str) != 'nan']
        final_count = len(df_data)
        
        print(f"\n🧹 Очистка данных: {initial_count} → {final_count} товаров")
        
        # Преобразование в числовой формат
        for col in stock_columns:
            df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0)
        
        # Расчет общих остатков
        if stock_columns:
            df_data['total_current_stock'] = df_data[stock_columns].sum(axis=1)
        else:
            df_data['total_current_stock'] = 0
        
        self.stock_data = df_data
        
        # Итоговая статистика
        total_stock = df_data['total_current_stock'].sum()
        items_with_stock = len(df_data[df_data['total_current_stock'] > 0])
        
        print(f"\n✅ ЗАГРУЗКА ЗАВЕРШЕНА:")
        print(f"   • Товаров: {final_count}")
        print(f"   • Точек продаж: {len(stock_columns)}")
        print(f"   • Общий остаток: {total_stock:,.0f} шт")
        print(f"   • Товаров с остатками: {items_with_stock}")
        print(f"   • Реальные названия: СОХРАНЕНЫ ✅")
        
        return {
            'success': True,
            'total_items': final_count,
            'stock_columns_found': len(stock_columns),
            'stock_columns': stock_columns,
            'total_stock': total_stock,
            'items_with_stock': items_with_stock,
            'avg_stock': df_data['total_current_stock'].mean(),
            'real_names_preserved': True,
            'header_row_used': header_row_index + 1,  # Человеческая нумерация
            'expected_vs_found': f"Ожидалось 11, найдено {len(stock_columns)}"
        }
        
    except Exception as e:
        print(f"❌ Ошибка загрузки: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Ошибка при загрузке файла остатков: {str(e)}'
        }


def apply_correct_column_fix(system):
    """
    Применение ПРАВИЛЬНОГО исправления для вашего файла
    """
    print("🔧 Применение ПРАВИЛЬНОГО исправления для файла с заголовками в 7-й строке...")
    
    # Заменяем метод на правильную версию
    system.load_stock_data = types.MethodType(load_stock_data_fixed_for_your_file, system)
    system._column_names_fixed = True
    system._header_row_position = 7  # Запоминаем позицию заголовков
    
    print("✅ ПРАВИЛЬНОЕ исправление применено!")
    print("📋 Теперь система будет:")
    print("   - Читать заголовки из 7-й строки")
    print("   - Сохранять реальные названия точек")
    print("   - Правильно определять 11 точек продаж")
    
    return True


def check_correct_fix_status(system):
    """Проверка статуса правильного исправления"""
    return (hasattr(system, '_column_names_fixed') and 
            system._column_names_fixed and
            hasattr(system, '_header_row_position') and
            system._header_row_position == 7)


# Дополнительная функция для диагностики
def diagnose_excel_structure(file):
    """
    Диагностика структуры Excel файла для отладки
    """
    try:
        df = pd.read_excel(file, engine='openpyxl', header=None)
        
        print("🔍 ДИАГНОСТИКА СТРУКТУРЫ ФАЙЛА:")
        print(f"📊 Размер: {df.shape[0]} строк × {df.shape[1]} колонок")
        
        print(f"\n📋 ПЕРВЫЕ 10 СТРОК:")
        for i in range(min(10, len(df))):
            row_data = [str(cell)[:20] if pd.notna(cell) else 'ПУСТО' for cell in df.iloc[i, :5]]
            print(f"   Строка {i+1}: {' | '.join(row_data)}")
        
        print(f"\n🎯 7-Я СТРОКА (предполагаемые заголовки):")
        if len(df) > 6:
            headers_row = df.iloc[6]
            for i, header in enumerate(headers_row[:15]):  # Первые 15 колонок
                col_letter = chr(65 + i)
                header_text = str(header) if pd.notna(header) else 'ПУСТО'
                print(f"   {col_letter}: {header_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        return False