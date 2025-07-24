#!/bin/bash

# ДИАГНОСТИКА РАСЧЕТА ОБОРАЧИВАЕМОСТИ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 ДИАГНОСТИКА РАСЧЕТА ОБОРАЧИВАЕМОСТИ"
echo "===================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 Проблема: 9 остатков, 62.39 продаж/день → 0.1 оборачиваемость (неправильно)"
echo "🎯 Правильно должно быть: (9 / 62.39) * 30.5 = 4.4 дня"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '📋 АНАЛИЗ ФАЙЛОВОЙ СТРУКТУРЫ'
    echo '============================'
    echo 'Основные файлы приложения:'
    ls -la *.py | grep -E 'webhook|streamlit|modular' | head -5
    echo ''
    
    echo '🔍 ПОИСК ОСНОВНОГО ПРИЛОЖЕНИЯ'
    echo '============================='
    
    # Ищем активное приложение
    if ps aux | grep -q 'streamlit.*modular'; then
        MAIN_APP='streamlit_modular_app.py'
        echo \"✅ Активное приложение: \$MAIN_APP\"
    elif ps aux | grep -q 'webhook.*persistent'; then
        MAIN_APP='webhook_persistent_app.py'
        echo \"✅ Активное приложение: \$MAIN_APP\"
    else
        MAIN_APP=\$(ls -t *.py | grep -E 'streamlit.*modular|webhook.*persistent' | head -1)
        echo \"🔍 Предполагаемое основное приложение: \$MAIN_APP\"
    fi
    
    echo ''
    echo '🧮 ПОИСК ФОРМУЛ ОБОРАЧИВАЕМОСТИ'
    echo '==============================='
    
    if [ -n \"\$MAIN_APP\" ] && [ -f \"\$MAIN_APP\" ]; then
        echo \"Анализируем файл: \$MAIN_APP\"
        echo ''
        
        echo '1. Поиск функций расчета оборачиваемости:'
        grep -n -A5 -B2 'def.*turnover\\|def.*оборач' \"\$MAIN_APP\" 2>/dev/null || echo 'Функции не найдены'
        echo ''
        
        echo '2. Поиск математических операций:'
        grep -n -C3 '\\*.*30\\.5\\|/.*30\\.5\\|turnover.*=' \"\$MAIN_APP\" | head -10
        echo ''
        
        echo '3. Поиск проблемных формул (без умножения на 30.5):'
        grep -n -C2 'turnover.*=.*[^*]\\s*/' \"\$MAIN_APP\" | head -5
        echo ''
        
        echo '4. Поиск расчетов с делением остатков на продажи:'
        grep -n -C2 'stock.*/.* sales\\|остаток.*/.* продаж' \"\$MAIN_APP\" | head -5
        echo ''
        
    else
        echo '❌ Основное приложение не найдено'
    fi
    
    echo '🔧 СОЗДАНИЕ ДИАГНОСТИЧЕСКОГО СКРИПТА'
    echo '==================================='
    
    cat > turnover_diagnostic.py << 'PYTHON_END'
#!/usr/bin/env python3
import os
import re
import glob

def find_turnover_calculations():
    \"\"\"Находит все расчеты оборачиваемости в файлах\"\"\"
    print(\"🔍 ПОИСК РАСЧЕТОВ ОБОРАЧИВАЕМОСТИ\")
    print(\"=\" * 40)
    
    # Ищем Python файлы
    python_files = glob.glob('*.py')
    main_files = ['streamlit_modular_app.py', 'webhook_persistent_app.py', 'modular_inventory_system.py']
    
    # Приоритет основным файлам
    priority_files = [f for f in main_files if f in python_files]
    other_files = [f for f in python_files if f not in main_files]
    all_files = priority_files + other_files
    
    print(f\"📂 Анализируем {len(all_files)} файлов\")
    print()
    
    problematic_patterns = []
    correct_patterns = []
    
    for filepath in all_files[:10]:  # Первые 10 файлов
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\\n')
            
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                # Ищем подозрительные паттерны
                if 'turnover' in line_lower or 'оборач' in line_lower:
                    # Проверяем на проблемные формулы
                    if re.search(r'[^*]\\s*/\\s*[^*]', line) and ('stock' in line_lower or 'sales' in line_lower):
                        if not re.search(r'\\*\\s*30\\.5', line) and not re.search(r'\\*\\s*period', line):
                            problematic_patterns.append({
                                'file': filepath,
                                'line': i,
                                'content': line.strip(),
                                'issue': 'Деление без умножения на период'
                            })
                    
                    # Ищем правильные формулы
                    elif re.search(r'\\*\\s*30\\.5', line):
                        correct_patterns.append({
                            'file': filepath, 
                            'line': i,
                            'content': line.strip()
                        })
                    
                    # Ищем формулы с переменным периодом
                    elif re.search(r'\\*\\s*period', line):
                        correct_patterns.append({
                            'file': filepath,
                            'line': i, 
                            'content': line.strip()
                        })
        
        except Exception as e:
            continue
    
    print(\"❌ ПРОБЛЕМНЫЕ ФОРМУЛЫ:\")
    print(\"-\" * 30)
    if problematic_patterns:
        for pattern in problematic_patterns:
            print(f\"📁 {pattern['file']}:{pattern['line']}\")
            print(f\"   {pattern['content']}\")
            print(f\"   🚨 {pattern['issue']}\")
            print()
    else:
        print(\"Не найдено\")
    
    print()
    print(\"✅ ПРАВИЛЬНЫЕ ФОРМУЛЫ:\")
    print(\"-\" * 30)
    if correct_patterns:
        for pattern in correct_patterns[:5]:  # Первые 5
            print(f\"📁 {pattern['file']}:{pattern['line']}\")
            print(f\"   {pattern['content']}\")
            print()
    else:
        print(\"Не найдено\")
    
    print()
    print(\"🧮 ТЕСТ ПРАВИЛЬНОГО РАСЧЕТА:\")
    print(\"-\" * 30)
    stock = 9
    daily_sales = 62.39
    period = 30.5
    
    wrong_calc = stock / daily_sales
    correct_calc = (stock / daily_sales) * period
    
    print(f\"📊 Данные: Остатки={stock}, Продажи/день={daily_sales}\")
    print(f\"❌ Неправильно: {stock} / {daily_sales} = {wrong_calc:.2f}\")
    print(f\"✅ Правильно: ({stock} / {daily_sales}) * {period} = {correct_calc:.2f} дней\")
    
    return len(problematic_patterns), len(correct_patterns)

if __name__ == \"__main__\":
    problematic, correct = find_turnover_calculations()
    
    print()
    print(\"📊 ИТОГО:\")
    print(f\"   ❌ Проблемных формул: {problematic}\")
    print(f\"   ✅ Правильных формул: {correct}\")
    
    if problematic > 0:
        print()
        print(\"🔧 РЕКОМЕНДАЦИИ:\")
        print(\"   1. Найдены формулы без умножения на период\")
        print(\"   2. Нужно исправить: result = stock / sales\")
        print(\"   3. На правильное: result = (stock / sales) * 30.5\")
PYTHON_END
    
    echo '🔄 ЗАПУСК ДИАГНОСТИКИ'
    echo '===================='
    python3 turnover_diagnostic.py
    
    echo ''
    echo '📊 ПРОВЕРКА ТЕКУЩИХ ПРОЦЕССОВ'
    echo '============================='
    
    echo 'Активные Python процессы:'
    ps aux | grep python | grep -v grep | head -3
    echo ''
    
    echo 'Streamlit процессы:'
    ps aux | grep streamlit | grep -v grep
    echo ''
    
    echo '🔍 ПРОВЕРКА ЛОГОВ'
    echo '================='
    
    if [ -f 'streamlit.log' ]; then
        echo 'Последние записи streamlit.log:'
        tail -5 streamlit.log
    fi
    echo ''
    
    if [ -f 'webhook.log' ]; then
        echo 'Последние записи webhook.log:'
        tail -5 webhook.log
    fi
    
    # Очистка
    rm -f turnover_diagnostic.py
"

echo ""
echo "✅ СКРИПТ ДИАГНОСТИКИ ОБОРАЧИВАЕМОСТИ СОЗДАН!"
echo ""
echo "🎯 Этот скрипт:"
echo "   - Найдет основное приложение на сервере"
echo "   - Проанализирует все формулы оборачиваемости"
echo "   - Выявит проблемные расчеты без умножения на 30.5"
echo "   - Покажет правильный расчет: (9 / 62.39) * 30.5 = 4.4 дня"
echo ""