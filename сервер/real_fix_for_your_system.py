#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
real_fix_for_your_system.py - НАСТОЯЩЕЕ ИСПРАВЛЕНИЕ
Патчит ВСЕ методы загрузки остатков в системе
"""

import pandas as pd
import types
import io

def load_stock_data_completely_fixed(self, file):
    """
    ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ версия load_stock_data
    Читает заголовки из 7-й строки и сохраняет реальные названия
    """
    try:
        print("📦 ИСПРАВЛЕННАЯ ЗАГРУЗКА ОСТАТКОВ - load_stock_data")
        
        # Чтение файла
        if hasattr(file, 'read'):
            df = pd.read_excel(file, engine='openpyxl', header=None)
        else:
            df = pd.read_excel(file, engine='openpyxl', header=None)
        
        print(f"📊 Исходный размер: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # ВАЖНО: Заголовки в 7-й строке (индекс 6)
        header_row_index = 6
        
        if df.shape[0] <= header_row_index:
            return {'success': False, 'error': f'В файле недостаточно строк для чтения заголовков из 7-й строки'}
        
        # Извлекаем заголовки из 7-й строки
        headers_row = df.iloc[header_row_index]
        print(f"\n📋 ЗАГОЛОВКИ ИЗ 7-Й СТРОКИ:")
        
        # НЕ ПРИМЕНЯЕМ LOWER() - СОХРАНЯЕМ ОРИГИНАЛЬНЫЕ НАЗВАНИЯ!
        corrected_columns = []
        for i, header in enumerate(headers_row):
            if pd.notna(header) and str(header).strip():
                # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: НЕ ПРИМЕНЯЕМ .lower()
                clean_name = str(header).strip()
                corrected_columns.append(clean_name)
                col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                print(f"   {col_letter}: '{clean_name}'")
            else:
                col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                tech_name = f'empty_{col_letter}'
                corrected_columns.append(tech_name)
                print(f"   {col_letter}: '{tech_name}' (пустая)")
        
        # Берем данные с 8-й строки
        data_start_row = header_row_index + 1
        df = df.iloc[data_start_row:].copy()
        df.columns = corrected_columns[:len(df.columns)]
        
        print(f"\n📊 Данные с {data_start_row + 1}-й строки: {len(df)} строк")
        
        # Находим номенклатуру
        nomenclature_col = None
        for col in df.columns:
            if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                nomenclature_col = col
                print(f"✅ Номенклатура: '{nomenclature_col}'")
                break
        
        if nomenclature_col is None:
            nomenclature_col = df.columns[0]
            print(f"⚠️ Используется первая колонка: '{nomenclature_col}'")
        
        df = df.rename(columns={nomenclature_col: 'номенклатура'})
        
        # Ищем точки продаж (все числовые колонки кроме номенклатуры)
        stock_columns = []
        print(f"\n📦 ПОИСК ТОЧЕК ПРОДАЖ:")
        
        for col in df.columns:
            if col != 'номенклатура':
                try:
                    numeric_data = pd.to_numeric(df[col], errors='coerce')
                    non_nan_count = (~numeric_data.isna()).sum()
                    
                    if non_nan_count > 0:
                        stock_columns.append(col)
                        print(f"   ✅ '{col}' ({non_nan_count} значений)")
                    else:
                        print(f"   ❌ '{col}' (нет данных)")
                except:
                    print(f"   ❌ '{col}' (ошибка)")
        
        print(f"\n🎯 НАЙДЕНО {len(stock_columns)} ТОЧЕК ПРОДАЖ")
        
        # Очистка и обработка
        df = df.dropna(subset=['номенклатура'])
        df = df[df['номенклатура'].astype(str).str.strip() != '']
        df = df[df['номенклатура'].astype(str) != 'nan']
        
        for col in stock_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if stock_columns:
            df['total_current_stock'] = df[stock_columns].sum(axis=1)
        else:
            df['total_current_stock'] = 0
        
        self.stock_data = df
        
        print(f"\n✅ ЗАГРУЗКА ЗАВЕРШЕНА:")
        print(f"   • Товаров: {len(df)}")
        print(f"   • Точек продаж: {len(stock_columns)}")
        print(f"   • Реальные названия: СОХРАНЕНЫ ✅")
        
        return {
            'success': True,
            'total_items': len(df),
            'stock_columns_found': len(stock_columns),
            'stock_columns': stock_columns,
            'total_stock': df['total_current_stock'].sum(),
            'items_with_stock': len(df[df['total_current_stock'] > 0]),
            'avg_stock': df['total_current_stock'].mean(),
            'real_names_preserved': True
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def load_current_stock_file_completely_fixed(self, file_content):
    """
    ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ версия load_current_stock_file
    """
    try:
        print("📦 ИСПРАВЛЕННАЯ ЗАГРУЗКА ОСТАТКОВ - load_current_stock_file")
        
        # Чтение файла
        if hasattr(file_content, 'read'):
            df = pd.read_excel(file_content, engine='openpyxl', header=None)
        else:
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None)
        
        print(f"📊 Исходный размер: {df.shape[0]} строк, {df.shape[1]} колонок")
        
        # Заголовки в 7-й строке
        header_row_index = 6
        
        if df.shape[0] <= header_row_index:
            return {'success': False, 'error': 'Недостаточно строк для чтения заголовков из 7-й строки'}
        
        # Извлекаем заголовки БЕЗ LOWER()
        headers_row = df.iloc[header_row_index]
        corrected_columns = []
        
        for i, header in enumerate(headers_row):
            if pd.notna(header) and str(header).strip():
                clean_name = str(header).strip()  # БЕЗ .lower()!
                corrected_columns.append(clean_name)
            else:
                col_letter = chr(65 + i) if i < 26 else f"Col{i}"
                corrected_columns.append(f'empty_{col_letter}')
        
        # Данные с 8-й строки
        data_start_row = header_row_index + 1
        df = df.iloc[data_start_row:].copy()
        df.columns = corrected_columns[:len(df.columns)]
        
        # Находим номенклатуру
        nomenclature_col = None
        for col in df.columns:
            if any(word in str(col).lower() for word in ['номенклатура', 'наименование', 'товар']):
                nomenclature_col = col
                break
        
        if nomenclature_col is None:
            nomenclature_col = df.columns[0]
        
        df = df.rename(columns={nomenclature_col: 'номенклатура'})
        
        # Ищем точки продаж
        stock_columns = []
        for col in df.columns:
            if col != 'номенклатура':
                try:
                    numeric_data = pd.to_numeric(df[col], errors='coerce')
                    if not numeric_data.isna().all():
                        stock_columns.append(col)
                except:
                    continue
        
        # Очистка данных
        df = df.dropna(subset=['номенклатура'])
        df = df[df['номенклатура'].astype(str).str.strip() != '']
        df = df[df['номенклатура'].astype(str) != 'nan']
        
        for col in stock_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if stock_columns:
            df['total_current_stock'] = df[stock_columns].sum(axis=1)
        else:
            df['total_current_stock'] = 0
        
        self.stock_data = df
        
        print(f"✅ load_current_stock_file: {len(df)} товаров, {len(stock_columns)} точек")
        
        return {
            'success': True,
            'total_items': len(df),
            'stock_columns_found': len(stock_columns),
            'stock_columns': stock_columns,
            'total_stock': df['total_current_stock'].sum(),
            'items_with_stock': len(df[df['total_current_stock'] > 0]),
            'avg_stock': df['total_current_stock'].mean()
        }
        
    except Exception as e:
        print(f"❌ Ошибка load_current_stock_file: {str(e)}")
        return {'success': False, 'error': str(e)}


def apply_complete_fix_to_system(system):
    """
    ПРИМЕНЕНИЕ ПОЛНОГО ИСПРАВЛЕНИЯ КО ВСЕМ МЕТОДАМ СИСТЕМЫ
    """
    print("🔧 ПРИМЕНЕНИЕ ПОЛНОГО ИСПРАВЛЕНИЯ...")
    print("🎯 Цель: Сохранить реальные названия точек продаж")
    
    # Заменяем ОБА метода загрузки остатков
    system.load_stock_data = types.MethodType(load_stock_data_completely_fixed, system)
    system.load_current_stock_file = types.MethodType(load_current_stock_file_completely_fixed, system)
    
    # Устанавливаем флаги
    system._complete_fix_applied = True
    system._header_row_position = 7
    system._real_names_preserved = True
    
    print("✅ ПОЛНОЕ ИСПРАВЛЕНИЕ ПРИМЕНЕНО!")
    print("📋 Исправлены методы:")
    print("   - load_stock_data")
    print("   - load_current_stock_file")
    print("🎯 Теперь система будет:")
    print("   - Читать заголовки из 7-й строки")
    print("   - Сохранять реальные названия точек")
    print("   - НЕ применять .lower() к названиям")
    
    return True


def check_complete_fix_status(system):
    """Проверка статуса полного исправления"""
    return (hasattr(system, '_complete_fix_applied') and 
            system._complete_fix_applied and
            hasattr(system, '_real_names_preserved') and 
            system._real_names_preserved)


def force_reload_stock_data(system):
    """
    Принудительная перезагрузка данных остатков с исправлениями
    ИСПОЛЬЗУЙТЕ ЕСЛИ ДАННЫЕ УЖЕ ЗАГРУЖЕНЫ С col_* НАЗВАНИЯМИ
    """
    if hasattr(system, 'stock_data') and system.stock_data is not None:
        print("⚠️ Внимание: Данные остатков уже загружены с col_* названиями")
        print("🔄 Для применения исправления нужно перезагрузить файл остатков")
        print("📋 Перейдите в 'Сравнение остатков' и загрузите файл заново")
        return False
    else:
        print("✅ Данные остатков не загружены - исправление будет применено при загрузке")
        return True


# Функция для диагностики проблем
def diagnose_system_issues(system):
    """Диагностика проблем с названиями колонок"""
    
    print("\n" + "="*60)
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМ С НАЗВАНИЯМИ ТОЧЕК")
    print("="*60)
    
    # 1. Проверяем какие методы используются
    print("1️⃣ МЕТОДЫ ЗАГРУЗКИ:")
    print(f"   load_stock_data: {hasattr(system, 'load_stock_data')}")
    print(f"   load_current_stock_file: {hasattr(system, 'load_current_stock_file')}")
    
    # 2. Проверяем статус исправлений
    print("\n2️⃣ СТАТУС ИСПРАВЛЕНИЙ:")
    print(f"   _complete_fix_applied: {getattr(system, '_complete_fix_applied', False)}")
    print(f"   _real_names_preserved: {getattr(system, '_real_names_preserved', False)}")
    
    # 3. Проверяем загруженные данные
    print("\n3️⃣ ЗАГРУЖЕННЫЕ ДАННЫЕ:")
    if hasattr(system, 'stock_data') and system.stock_data is not None:
        print(f"   Остатки загружены: ✅ ({len(system.stock_data)} товаров)")
        
        # Проверяем названия колонок
        stock_columns = [col for col in system.stock_data.columns if col != 'номенклатура' and col != 'total_current_stock']
        print(f"   Точек продаж: {len(stock_columns)}")
        
        # Анализируем названия
        col_star_count = sum(1 for col in stock_columns if col.startswith('col_'))
        real_names_count = sum(1 for col in stock_columns if not col.startswith('col_') and not col.startswith('empty_'))
        
        print(f"   С названиями col_*: {col_star_count}")
        print(f"   С реальными названиями: {real_names_count}")
        
        if col_star_count > 0:
            print("   ❌ ПРОБЛЕМА: Найдены col_* названия!")
            print("   🔄 РЕШЕНИЕ: Перезагрузите файл остатков после применения исправления")
        else:
            print("   ✅ Все названия реальные!")
            
        # Показываем примеры названий
        print("\n   📋 ПРИМЕРЫ НАЗВАНИЙ:")
        for i, col in enumerate(stock_columns[:5]):
            print(f"      {i+1}. '{col}'")
            
    else:
        print("   Остатки: ❌ Не загружены")
    
    print("\n" + "="*60)
    
    return {
        'has_col_star_names': col_star_count > 0 if 'col_star_count' in locals() else False,
        'needs_reload': hasattr(system, 'stock_data') and system.stock_data is not None,
        'fix_applied': check_complete_fix_status(system)
    }