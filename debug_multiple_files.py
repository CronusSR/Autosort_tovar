#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка обработки множественных файлов
"""

import pandas as pd
import numpy as np
import io
import sys
import traceback

# Добавляем путь к модулю, если нужно
try:
    from modular_inventory_system import ModularInventorySystem
except ImportError:
    print("❌ Не удается импортировать modular_inventory_system")
    print("   Убедитесь, что файл modular_inventory_system.py находится в той же папке")
    sys.exit(1)

def create_test_excel_file(branch_name: str, products: list) -> bytes:
    """Создание тестового Excel файла"""
    
    print(f"  📄 Создаем файл для {branch_name}...")
    
    # Создаем тестовые данные с заголовками
    data = {
        '': ['заголовок1', 'заголовок2', 'номенклатура'] + [f"{product} {branch_name}" for product in products],
        'A': ['', '', 'колонка A'] + [''] * len(products),
        'B': ['', '', 'колонка B'] + [''] * len(products),
        'янв_2024': ['', '', 'янв 2024'] + list(np.random.randint(10, 100, len(products))),
        'фев_2024': ['', '', 'фев 2024'] + list(np.random.randint(10, 100, len(products))),
        'мар_2024': ['', '', 'мар 2024'] + list(np.random.randint(10, 100, len(products))),
        'апр_2024': ['', '', 'апр 2024'] + list(np.random.randint(10, 100, len(products))),
        'май_2024': ['', '', 'май 2024'] + list(np.random.randint(10, 100, len(products))),
        'июн_2024': ['', '', 'июн 2024'] + list(np.random.randint(10, 100, len(products)))
    }
    
    df = pd.DataFrame(data)
    
    # Сохраняем в Excel формат
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def detailed_test():
    """Детальное тестирование с выводом на каждом шаге"""
    
    print("🧪 ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ МНОЖЕСТВЕННЫХ ФАЙЛОВ")
    print("="*60)
    
    # Создаем систему
    print("\n1️⃣ Создание системы...")
    try:
        system = ModularInventorySystem()
        print("✅ Система создана")
    except Exception as e:
        print(f"❌ Ошибка создания системы: {e}")
        return False
    
    # Создаем тестовые файлы
    print("\n2️⃣ Создание тестовых файлов...")
    products = ['Конфирмат', 'ПВХ кромка', 'Полкодержатель']
    branches = ['шымкент_склад', 'астана_склад']
    
    files_dict = {}
    
    try:
        for branch in branches:
            file_bytes = create_test_excel_file(branch, products)
            files_dict[branch] = file_bytes
            print(f"  ✅ {branch}: {len(file_bytes):,} байт")
    except Exception as e:
        print(f"❌ Ошибка создания файлов: {e}")
        return False
    
    # Тестируем обработку одного файла
    print(f"\n3️⃣ Тест обработки одного файла...")
    try:
        print("  🔄 Обрабатываем первый файл...")
        single_result = system._process_single_sales_file(files_dict['шымкент_склад'], 'тест_шымкент')
        
        print(f"  📊 Результат: success = {single_result['success']}")
        
        if single_result['success']:
            print("  ✅ Одиночная обработка успешна")
            print(f"     Товаров: {single_result['total_items']}")
            print(f"     ADS: {single_result['total_ads']:.2f}")
            print(f"     Метод: {single_result.get('calculation_method', 'не указан')}")
            
            # Проверяем структуру данных
            data_columns = single_result['data'].columns.tolist()
            print(f"     Колонки в данных: {data_columns}")
            
            # Проверяем первые строки данных
            print("     Первые 2 строки данных:")
            print(single_result['data'].head(2).to_string())
            
        else:
            print(f"  ❌ Ошибка одиночной обработки: {single_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при одиночной обработке:")
        print(f"   {str(e)}")
        traceback.print_exc()
        return False
    
    # Тестируем множественную обработку
    print(f"\n4️⃣ Тест множественной обработки...")
    try:
        print("  🔄 Обрабатываем все файлы...")
        multiple_result = system.load_multiple_sales_files(files_dict)
        
        print(f"  📊 Результат: success = {multiple_result['success']}")
        
        if multiple_result['success']:
            print("  ✅ Множественная обработка успешна")
            print(f"     Файлов обработано: {multiple_result['files_processed']}")
            print(f"     Уникальных товаров: {multiple_result['combined_items']}")
            print(f"     Общий ADS: {multiple_result['total_ads_all_branches']:.2f}")
            
            # Проверяем структуру calculated_ads
            if system.calculated_ads is not None:
                calc_columns = system.calculated_ads.columns.tolist()
                print(f"     Колонки в calculated_ads: {calc_columns}")
                
                print("     Первые 3 строки calculated_ads:")
                print(system.calculated_ads.head(3).to_string())
                
                # Проверяем наличие проблемных колонок
                problematic_columns = ['total_quantity_sold', 'quantity_column_used', 'total_sales']
                found_problematic = [col for col in calc_columns if col in problematic_columns]
                
                if found_problematic:
                    print(f"     ⚠️ Найдены старые колонки: {found_problematic}")
                else:
                    print("     ✅ Нет старых колонок")
                    
            else:
                print("     ❌ calculated_ads равен None")
                return False
        else:
            print(f"  ❌ Ошибка множественной обработки: {multiple_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при множественной обработке:")
        print(f"   {str(e)}")
        traceback.print_exc()
        return False
    
    # Тестируем генерацию отчета
    print(f"\n5️⃣ Тест генерации отчета...")
    try:
        print("  🔄 Создаем отчет...")
        summary = system.get_summary_report()
        
        if 'ads_analysis' in summary:
            ads_info = summary['ads_analysis']
            print("  ✅ Отчет создан успешно")
            print(f"     Товаров: {ads_info.get('total_items', 0)}")
            print(f"     Общий ADS: {ads_info.get('total_ads', 0):.2f}")
            
            # Проверяем какие метрики есть
            metrics = [key for key in ads_info.keys() if 'total' in key]
            print(f"     Доступные метрики: {metrics}")
            
        else:
            print("  ❌ Нет раздела ads_analysis в отчете")
            print(f"     Доступные разделы: {list(summary.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка генерации отчета:")
        print(f"   {str(e)}")
        traceback.print_exc()
        return False
    
    print(f"\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("="*60)
    return True

if __name__ == "__main__":
    print("🔍 Поиск устаревших ссылок на колонки:")
    print("="*50)
    
    old_patterns = ['total_quantity_sold', 'quantity_column_used', 'total_sales']
    
    for pattern in old_patterns:
        print(f"🔎 Ищем '{pattern}' - нужно заменить на новые колонки")
    
    print(f"\n" + "="*60)
    
    # Запускаем детальный тест
    success = detailed_test()
    
    if not success:
        print("\n💥 ТЕСТЫ ПРОВАЛИЛИСЬ!")
        print("Проверьте ошибки выше для диагностики проблемы.")
    else:
        print("\n✨ Система работает корректно!")