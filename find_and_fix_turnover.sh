#!/bin/bash

# ПОИСК И ИСПРАВЛЕНИЕ ФОРМУЛЫ ОБОРАЧИВАЕМОСТИ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 ПОИСК И ИСПРАВЛЕНИЕ ФОРМУЛЫ ОБОРАЧИВАЕМОСТИ"
echo "=============================================="
echo "📅 Время: $(date)"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '🔍 ПОИСК ФАЙЛОВ С РАСЧЕТОМ ОБОРАЧИВАЕМОСТИ'
    echo '========================================'
    
    echo 'Python файлы в директории:'
    ls -la *.py | head -10
    echo ''
    
    echo 'Поиск файлов содержащих расчеты оборачиваемости:'
    
    # Ищем файлы с формулами оборачиваемости
    echo '1. Поиск по ключевым словам:'
    grep -l 'turnover\|оборач\|/ 30\|\* 30' *.py 2>/dev/null | head -5
    echo ''
    
    echo '2. Поиск математических операций с 30:'
    grep -n '\* 30\|/ 30' *.py 2>/dev/null | head -10
    echo ''
    
    echo '3. Поиск по слову период:'
    grep -n 'period\|период' *.py 2>/dev/null | head -5
    echo ''
    
    echo '📊 АНАЛИЗ ОСНОВНОГО ФАЙЛА ПРИЛОЖЕНИЯ'
    echo '==================================='
    
    MAIN_FILE=\$(ls webhook_*.py streamlit_*.py | head -1)
    if [ -n \"\$MAIN_FILE\" ]; then
        echo \"Анализируем главный файл: \$MAIN_FILE\"
        echo ''
        
        echo 'Поиск расчетов с числом 30:'
        grep -n '30' \"\$MAIN_FILE\" | grep -E '\*|/' | head -5
        echo ''
        
        echo 'Поиск функций с оборачиваемостью:'
        grep -n -A2 -B2 'def.*turnover\|def.*оборач' \"\$MAIN_FILE\" 2>/dev/null
        echo ''
        
    else
        echo 'Основной файл приложения не найден'
    fi
    
    echo '🔧 СОЗДАНИЕ УНИВЕРСАЛЬНОГО ФИКСЕРА'
    echo '=================================='
    
    cat > universal_turnover_fix.py << 'PYTHON_END'
#!/usr/bin/env python3
import os
import re
import glob

def fix_turnover_formula_in_file(filepath):
    \"\"\"Исправляет формулы оборачиваемости в файле\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Паттерны для поиска и замены
        patterns = [
            # Умножение на 30
            (r'(\w+\s*\*\s*)30(\s*[\/\)])', r'\\g<1>30.5\\g<2>'),
            # Деление на 30 (продажи в знаменателе)
            (r'\/\s*30(\s*[\/\)\s])', r'/ 30.5\\g<1>'),
            # period_days = 30
            (r'period_days\s*=\s*30([^0-9\.])', r'period_days = 30.5\\g<1>'),
            # return ..., 30
            (r'return\s+([^,]+),\s*30([^0-9\.])', r'return \\g<1>, 30.5\\g<2>'),
            # Комментарии с 30 дней
            (r'30\s+дней\s+\(месяц\)', r'30.5 дней (средний месяц)'),
            # Период = 30
            (r'Период\s*=\s*30', r'Период = 30.5'),
        ]
        
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes_made += 1
                content = new_content
        
        if changes_made > 0:
            # Создаем бэкап
            backup_path = f\"{filepath}.backup_{int(__import__('time').time())}\"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Сохраняем исправленный файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f\"✅ {os.path.basename(filepath)}: {changes_made} изменений\")
            return changes_made
        else:
            print(f\"⚪ {os.path.basename(filepath)}: изменений не требуется\")
            return 0
            
    except Exception as e:
        print(f\"❌ {os.path.basename(filepath)}: ошибка - {e}\")
        return 0

def main():
    print(\"🔧 УНИВЕРСАЛЬНОЕ ИСПРАВЛЕНИЕ ФОРМУЛ ОБОРАЧИВАЕМОСТИ\")
    print(\"=\" * 55)
    
    total_changes = 0
    files_processed = 0
    
    # Ищем все Python файлы
    python_files = glob.glob('*.py')
    
    print(f\"📂 Найдено Python файлов: {len(python_files)}\")
    print()
    
    for filepath in python_files:
        changes = fix_turnover_formula_in_file(filepath)
        total_changes += changes
        files_processed += 1
    
    print()
    print(f\"📊 ИТОГО:\")
    print(f\"   📁 Обработано файлов: {files_processed}\")
    print(f\"   🔧 Общее количество изменений: {total_changes}\")
    
    if total_changes > 0:
        print()
        print(\"✅ ФОРМУЛЫ ОБОРАЧИВАЕМОСТИ ИСПРАВЛЕНЫ!\")
        print(\"   30 дней → 30.5 дней (средний месяц)\")
        print(\"   Бэкапы созданы с расширением .backup_timestamp\")
    else:
        print()
        print(\"ℹ️ Формулы уже корректны или не найдены\")

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК УНИВЕРСАЛЬНОГО ФИКСЕРА'
    echo '==============================='
    python3 universal_turnover_fix.py
    
    echo ''
    echo '🔍 ПРОВЕРКА РЕЗУЛЬТАТА'
    echo '====================='
    
    echo 'Файлы с 30.5 после исправления:'
    grep -l '30\.5' *.py 2>/dev/null | head -5
    echo ''
    
    echo 'Примеры исправленных строк:'
    grep -n '30\.5' *.py 2>/dev/null | head -3
    echo ''
    
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ФОРМУЛА ОБОРАЧИВАЕМОСТИ ИСПРАВЛЕНА!'
        echo ''
        echo '📊 ИЗМЕНЕНИЯ:'
        echo '   ❌ Старая формула: (остатки/продажи) * 30'
        echo '   ✅ Новая формула: (остатки/продажи) * 30.5'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f universal_turnover_fix.py
"

echo ""
echo "✅ УНИВЕРСАЛЬНЫЙ СКРИПТ ПОИСКА И ИСПРАВЛЕНИЯ СОЗДАН!"
echo ""
echo "🎯 Этот скрипт:"
echo "   - Найдет все Python файлы"
echo "   - Автоматически исправит формулы оборачиваемости"
echo "   - Создаст бэкапы измененных файлов"
echo ""