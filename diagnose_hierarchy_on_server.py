#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика состояния иерархии складов на SSH сервере
Проверяет что изменения применились правильно
"""

import os
import sys
import json
from datetime import datetime

def check_file_exists_and_modified():
    """Проверяет существование и время модификации файлов"""
    files_to_check = [
        'hierarchical_movement_system.py',
        'enhanced_warehouse_analysis.py', 
        'warehouse_hierarchy_system.py',
        'new_movement_system.py'
    ]
    
    print("🔍 ПРОВЕРКА ФАЙЛОВ НА СЕРВЕРЕ")
    print("=" * 50)
    
    for filename in files_to_check:
        if os.path.exists(filename):
            stat_info = os.stat(filename)
            mod_time = datetime.fromtimestamp(stat_info.st_mtime)
            print(f"✅ {filename}")
            print(f"   📅 Изменен: {mod_time}")
            print(f"   📏 Размер: {stat_info.st_size} байт")
        else:
            print(f"❌ {filename} - НЕ НАЙДЕН")
        print()

def test_hierarchy_import():
    """Тестирует импорт и проверяет иерархию"""
    print("🧪 ТЕСТИРОВАНИЕ ИМПОРТА И ИЕРАРХИИ")
    print("=" * 50)
    
    try:
        # Пытаемся импортировать
        from hierarchical_movement_system import HierarchicalMovementSystem
        print("✅ Импорт hierarchical_movement_system - ОК")
        
        # Создаем объект
        hms = HierarchicalMovementSystem()
        print("✅ Создание объекта - ОК")
        
        # Проверяем иерархию
        hierarchy = hms.warehouse_hierarchy
        print(f"✅ Загружена иерархия: {len(hierarchy)} складов")
        
        # Проверяем главный хаб
        main_hubs = [name for name, info in hierarchy.items() if info.get('level') == 1]
        print(f"🏢 Главные хабы: {main_hubs}")
        
        if 'База Склад Фурнитура Комплект' in main_hubs:
            print("✅ ПРАВИЛЬНО: База Склад Фурнитура Комплект - главный хаб")
        else:
            print("❌ ОШИБКА: База Склад Фурнитура Комплект не является главным хабом")
            
        if 'Казыбаева Склад Фурнитура TRADE' in main_hubs:
            print("❌ ОШИБКА: Казыбаева все еще считается главным хабом")
        else:
            print("✅ ПРАВИЛЬНО: Казыбаева не является главным хабом")
            
        # Показываем полную структуру
        print("\n📋 ПОЛНАЯ СТРУКТУРА ИЕРАРХИИ:")
        for name, info in hierarchy.items():
            level = info.get('level', 'unknown')
            type_info = info.get('type', 'unknown')
            city = info.get('city', 'unknown')
            print(f"  Уровень {level}: {name} ({type_info}, {city})")
            
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_running_processes():
    """Проверяет запущенные процессы Python"""
    print("\n🔄 ПРОВЕРКА ЗАПУЩЕННЫХ ПРОЦЕССОВ")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        python_processes = []
        for line in lines:
            if 'python' in line.lower() and ('streamlit' in line or 'warehouse' in line or 'inventory' in line):
                python_processes.append(line.strip())
                
        if python_processes:
            print(f"🔍 Найдено {len(python_processes)} Python процессов:")
            for i, process in enumerate(python_processes, 1):
                print(f"  {i}. {process}")
                
            print("\n⚠️  ВОЗМОЖНАЯ ПРИЧИНА: Запущенные процессы используют старые файлы в памяти")
            print("💡 РЕШЕНИЕ: Перезапустите Streamlit и другие сервисы:")
            print("   pkill -f streamlit")
            print("   pkill -f python")
            print("   # Затем запустите заново")
        else:
            print("ℹ️  Python процессы с warehouse/inventory не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка проверки процессов: {e}")

def generate_restart_commands():
    """Генерирует команды для перезапуска сервисов"""
    print("\n🚀 КОМАНДЫ ДЛЯ ПЕРЕЗАПУСКА СЕРВИСОВ")
    print("=" * 50)
    
    commands = [
        "# Остановить все Python процессы",
        "pkill -f streamlit",
        "pkill -f python",
        "",
        "# Подождать 2 секунды", 
        "sleep 2",
        "",
        "# Перезапустить основной Streamlit",
        "cd /opt/inventory_system",
        "nohup streamlit run streamlit_modular_app.py --server.port 8501 --server.address 0.0.0.0 &",
        "",
        "# Проверить что все работает",
        "python3 -c \"from hierarchical_movement_system import HierarchicalMovementSystem; hms = HierarchicalMovementSystem(); print('✅ Иерархия загружена:', len(hms.warehouse_hierarchy), 'складов')\"",
        "",
        "# Проверить веб-интерфейс",
        "curl -s http://localhost:8501 | head -5"
    ]
    
    for cmd in commands:
        print(cmd)

def main():
    """Основная функция диагностики"""
    print("🔍 ДИАГНОСТИКА ИЕРАРХИИ СКЛАДОВ НА СЕРВЕРЕ")
    print(f"📅 Время: {datetime.now()}")
    print(f"📂 Директория: {os.getcwd()}")
    print("=" * 60)
    
    # Проверяем файлы
    check_file_exists_and_modified()
    
    # Тестируем импорт и иерархию
    hierarchy_ok = test_hierarchy_import()
    
    # Проверяем процессы
    check_running_processes()
    
    # Генерируем команды перезапуска
    generate_restart_commands()
    
    print("\n" + "=" * 60)
    if hierarchy_ok:
        print("✅ СТАТУС: Файлы обновлены правильно")
        print("💡 РЕКОМЕНДАЦИЯ: Перезапустите сервисы для применения изменений")
    else:
        print("❌ СТАТУС: Проблемы с файлами или импортом")
        print("💡 РЕКОМЕНДАЦИЯ: Проверьте правильность копирования файлов")

if __name__ == "__main__":
    main()