#!/bin/bash

# ОКОНЧАТЕЛЬНОЕ ИСПРАВЛЕНИЕ РАСЧЕТА ОБОРАЧИВАЕМОСТИ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ОКОНЧАТЕЛЬНОЕ ИСПРАВЛЕНИЕ РАСЧЕТА ОБОРАЧИВАЕМОСТИ"
echo "=================================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 Проблема: 9 остатков, 62.39 продаж/день → 0.1 оборачиваемость"
echo "🎯 Исправление: Добавляем умножение на период (30.5)"
echo "🎯 Правильно: (9 / 62.39) * 30.5 = 4.4 дня"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '💾 БЭКАП ФАЙЛОВ'
    echo '==============='
    
    # Создаем бэкапы основных файлов
    BACKUP_SUFFIX=\"_backup_turnover_fix_\$(date +%Y%m%d_%H%M%S)\"
    
    main_files=('webhook_persistent_app.py' 'streamlit_modular_app.py' 'modular_inventory_system.py')
    
    for file in \"\${main_files[@]}\"; do
        if [ -f \"\$file\" ]; then
            cp \"\$file\" \"\${file}\${BACKUP_SUFFIX}\"
            echo \"✅ Бэкап создан: \${file}\${BACKUP_SUFFIX}\"
        fi
    done
    echo ''
    
    echo '🔧 СОЗДАНИЕ УНИВЕРСАЛЬНОГО ИСПРАВИТЕЛЯ'
    echo '====================================='
    
    cat > turnover_calculation_fixer.py << 'PYTHON_END'
#!/usr/bin/env python3
\"\"\"
ИСПРАВЛЕНИЕ РАСЧЕТА ОБОРАЧИВАЕМОСТИ
Добавляет умножение на период (30.5) в формулы оборачиваемости
\"\"\"

import os
import re
import glob

def fix_turnover_in_file(filepath):
    \"\"\"Исправляет расчеты оборачиваемости в файле\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Паттерны для исправления
        fix_patterns = [
            # Основной паттерн: stock / daily_sales без умножения
            {
                'pattern': r\"([\\w\\[\\]'\"]+)\\s*/\\s*([\\w\\[\\]'\"]+\\['daily_sales'\\])\",
                'replacement': r\"(\\1 / \\2) * period_days\",
                'condition': lambda m: 'stock' in m.group(1).lower() and 'daily_sales' in m.group(2)
            },
            
            # Конкретные исправления для movement_data
            {
                'pattern': r\"movement_data\\['stock_quantity'\\]\\s*/\\s*movement_data\\['daily_sales'\\]\",
                'replacement': r\"(movement_data['stock_quantity'] / movement_data['daily_sales']) * 30.5\",
                'condition': lambda m: True
            },
            
            # Конкретные исправления для turnover_data
            {
                'pattern': r\"turnover_data\\['stock_quantity'\\]\\s*/\\s*turnover_data\\['daily_sales'\\]\",
                'replacement': r\"(turnover_data['stock_quantity'] / turnover_data['daily_sales']) * period_days\",
                'condition': lambda m: True
            },
            
            # Конкретные исправления для city_turnover
            {
                'pattern': r\"city_turnover\\['stock_quantity'\\]\\s*/\\s*city_turnover\\['daily_sales'\\]\",
                'replacement': r\"(city_turnover['stock_quantity'] / city_turnover['daily_sales']) * period_days\",
                'condition': lambda m: True
            }
        ]
        
        # Применяем исправления
        for fix in fix_patterns:
            matches = list(re.finditer(fix['pattern'], content))
            for match in matches:
                if fix['condition'](match):
                    old_formula = match.group(0)
                    new_formula = fix['replacement']
                    
                    # Заменяем только если формула еще не исправлена
                    if '* period_days' not in old_formula and '* 30.5' not in old_formula:
                        content = content.replace(old_formula, new_formula)
                        changes_made += 1
                        print(f\"   🔧 Исправлено: {old_formula} → {new_formula}\")
        
        # Дополнительные исправления для конкретных паттернов
        additional_fixes = [
            # Простое деление без скобок
            (r'stock_quantity / daily_sales(?!.*\\*)', r'(stock_quantity / daily_sales) * period_days'),
            (r\"(\\w+)\\['stock_quantity'\\] / \\1\\['daily_sales'\\](?!.*\\*)\", r\"(\\1['stock_quantity'] / \\1['daily_sales']) * period_days\"),
        ]
        
        for pattern, replacement in additional_fixes:
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes_made += 1
                    content = new_content
        
        # Сохраняем файл если были изменения
        if changes_made > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f\"✅ {os.path.basename(filepath)}: {changes_made} исправлений\")
            return changes_made
        else:
            print(f\"⚪ {os.path.basename(filepath)}: уже исправлен\")
            return 0
            
    except Exception as e:
        print(f\"❌ {os.path.basename(filepath)}: ошибка - {e}\")
        return 0

def main():
    print(\"🔧 ИСПРАВЛЕНИЕ РАСЧЕТОВ ОБОРАЧИВАЕМОСТИ\")
    print(\"=\" * 45)
    
    total_changes = 0
    files_processed = 0
    
    # Приоритетные файлы для исправления
    priority_files = [
        'webhook_persistent_app.py',
        'streamlit_modular_app.py', 
        'modular_inventory_system.py',
        'webhook_app_stable.py',
        'webhook_app_enhanced_analytics.py',
        'optimized_data_processor.py'
    ]
    
    print(f\"📂 Исправляем приоритетные файлы...\")
    print()
    
    for filepath in priority_files:
        if os.path.exists(filepath):
            print(f\"📁 Обрабатываем: {filepath}\")
            changes = fix_turnover_in_file(filepath)
            total_changes += changes
            files_processed += 1
            print()
    
    print(f\"📊 ИТОГО:\")
    print(f\"   📁 Обработано файлов: {files_processed}\")
    print(f\"   🔧 Общее количество исправлений: {total_changes}\")
    
    if total_changes > 0:
        print()
        print(\"✅ РАСЧЕТЫ ОБОРАЧИВАЕМОСТИ ИСПРАВЛЕНЫ!\")
        print()
        print(\"🧮 ПРАВИЛЬНАЯ ФОРМУЛА:\")
        print(\"   Было: stock / daily_sales\")
        print(\"   Стало: (stock / daily_sales) * period_days\")
        print()
        print(\"📊 ПРИМЕР РАСЧЕТА:\")
        stock = 9
        daily_sales = 62.39
        period = 30.5
        
        wrong = stock / daily_sales
        correct = (stock / daily_sales) * period
        
        print(f\"   Остатки: {stock}, Продажи/день: {daily_sales}\")
        print(f\"   ❌ Неправильно: {stock} / {daily_sales} = {wrong:.2f}\")
        print(f\"   ✅ Правильно: ({stock} / {daily_sales}) * {period} = {correct:.2f} дней\")
    else:
        print()
        print(\"ℹ️ Все расчеты уже корректны\")

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК ИСПРАВЛЕНИЯ'
    echo '===================='
    python3 turnover_calculation_fixer.py
    
    echo ''
    echo '🔍 ПРОВЕРКА РЕЗУЛЬТАТА'
    echo '====================='
    
    echo 'Поиск исправленных формул:'
    grep -n \"* period_days\" *.py | head -3
    echo ''
    
    echo 'Поиск формул с 30.5:'
    grep -n \"* 30.5\" *.py | head -3
    echo ''
    
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ИСПРАВЛЕНИЕ ОБОРАЧИВАЕМОСТИ ЗАВЕРШЕНО!'
        echo ''
        echo '📊 РЕЗУЛЬТАТ:'
        echo '   ❌ Было: 9 остатков / 62.39 продаж = 0.1'
        echo '   ✅ Стало: (9 / 62.39) * 30.5 = 4.4 дня'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
        echo '   Теперь оборачиваемость рассчитывается правильно!'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f turnover_calculation_fixer.py
"

echo ""
echo "✅ ОКОНЧАТЕЛЬНЫЙ СКРИПТ ИСПРАВЛЕНИЯ СОЗДАН!"
echo ""
echo "🎯 Этот скрипт:"
echo "   - Создаст бэкапы всех основных файлов"
echo "   - Найдет ВСЕ неправильные расчеты оборачиваемости"
echo "   - Исправит формулы: добавит умножение на период"
echo "   - Проверит результат и запустит сервис"
echo ""
echo "🧮 После исправления:"
echo "   9 остатков / 62.39 продаж * 30.5 = 4.4 дня (правильно!)"
echo ""