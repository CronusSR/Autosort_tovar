#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест полной интеграции нового обработчика единого файла
"""

import sys
import os

def test_full_integration():
    """Тестируем полную интеграцию системы"""
    
    print("🧪 Тестирование полной интеграции единого файла ADS...")
    
    # 1. Проверяем наличие всех модулей
    modules_to_check = [
        'single_file_ads_processor',
        'modular_inventory_system', 
        'streamlit_modular_app',
        'integration_patch'
    ]
    
    print("\n📦 Проверка модулей:")
    missing_modules = []
    
    for module in modules_to_check:
        if os.path.exists(f"{module}.py"):
            print(f"✅ {module}.py")
        else:
            print(f"❌ {module}.py - НЕ НАЙДЕН")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Отсутствуют модули: {missing_modules}")
        return False
    
    # 2. Проверяем папку ads
    print(f"\n📁 Проверка папки ads:")
    if os.path.exists('ads'):
        print("✅ Папка ads существует")
        
        # Проверяем содержимое
        ads_files = [f for f in os.listdir('ads') if f.endswith('.json')]
        if ads_files:
            print(f"📄 Найдены файлы ADS: {len(ads_files)}")
            for f in ads_files:
                print(f"  • {f}")
        else:
            print("ℹ️ Папка ads пуста")
    else:
        print("❌ Папка ads не существует")
    
    # 3. Тестируем импорты
    print(f"\n🔍 Тестирование импортов:")
    
    try:
        from single_file_ads_processor import SingleFileADSProcessor
        print("✅ SingleFileADSProcessor импортирован")
        
        # Тестируем создание объекта
        processor = SingleFileADSProcessor()
        print("✅ Объект SingleFileADSProcessor создан")
        
        # Тестируем маппинг
        test_columns = [
            "КАТЕГОРИЯ",
            "Номенклатура", 
            "ТД Казыбаева ФУРНИТУРА магазин ( продажи 01.07.2024-01.07.2025 гг.)",
            "Барыс Склад Фурнитура TRADE ( продажи 01.07.2024-01.07.2025 гг.)"
        ]
        
        branch_columns = processor.identify_branch_columns(test_columns)
        print(f"✅ Маппинг работает: найдено {len(branch_columns)} филиалов")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта SingleFileADSProcessor: {e}")
        return False
    
    try:
        from modular_inventory_system import ModularInventorySystem
        print("✅ ModularInventorySystem импортирован")
        
        # Тестируем создание системы
        system = ModularInventorySystem()
        print("✅ Объект ModularInventorySystem создан")
        
        # Проверяем наличие нового метода
        if hasattr(system, 'load_ads_from_single_file'):
            print("✅ Метод load_ads_from_single_file присутствует")
        else:
            print("❌ Метод load_ads_from_single_file отсутствует")
            return False
            
    except ImportError as e:
        print(f"❌ Ошибка импорта ModularInventorySystem: {e}")
        return False
    
    # 4. Проверяем файл данных для тестирования
    print(f"\n📊 Проверка тестовых данных:")
    test_file = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    
    if os.path.exists(test_file):
        print(f"✅ Тестовый файл найден: {test_file}")
        print(f"📏 Размер файла: {os.path.getsize(test_file)} байт")
    else:
        print(f"❌ Тестовый файл не найден: {test_file}")
        print("ℹ️ Полный тест невозможен без файла данных")
    
    # 5. Проверяем streamlit интеграцию
    print(f"\n🎯 Проверка Streamlit интеграции:")
    
    try:
        # Читаем код streamlit_modular_app.py для проверки интеграции
        with open('streamlit_modular_app.py', 'r', encoding='utf-8') as f:
            streamlit_code = f.read()
        
        if 'SingleFileADSProcessor' in streamlit_code:
            print("✅ SingleFileADSProcessor интегрирован в Streamlit")
        else:
            print("❌ SingleFileADSProcessor НЕ интегрирован в Streamlit")
        
        if 'load_ads_from_single_file' in streamlit_code:
            print("✅ Метод load_ads_from_single_file используется в Streamlit")
        else:
            print("❌ Метод load_ads_from_single_file НЕ используется в Streamlit")
            
    except Exception as e:
        print(f"❌ Ошибка проверки Streamlit: {e}")
    
    print(f"\n🎉 Интеграция завершена!")
    print(f"\n📋 Следующие шаги:")
    print(f"1. Запустите: streamlit run streamlit_modular_app.py")
    print(f"2. Перейдите в раздел 'ADS расчет'")
    print(f"3. Выберите 'Единый файл со всеми филиалами'")
    print(f"4. Загрузите файл {test_file}")
    print(f"5. Проверьте результаты обработки")
    
    return True

if __name__ == "__main__":
    test_full_integration()