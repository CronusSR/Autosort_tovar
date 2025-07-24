#!/bin/bash

# ДИАГНОСТИКА СТРУКТУРЫ JSON ФАЙЛОВ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 ДИАГНОСТИКА СТРУКТУРЫ JSON ФАЙЛОВ"
echo "==================================="
echo "📅 Время: $(date)"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '📂 АНАЛИЗ ФАЙЛОВ В WEBHOOK_UPLOADS'
    echo '================================='
    
    # Проверяем несколько файлов
    echo '1️⃣ Список всех JSON файлов:'
    ls -la webhook_uploads/*.json | head -5
    echo ''
    
    echo '2️⃣ Размеры файлов:'
    du -h webhook_uploads/*.json | head -5
    echo ''
    
    echo '3️⃣ Проверка структуры первого файла (первые 500 символов):'
    FIRST_FILE=\$(ls webhook_uploads/*.json | head -1)
    echo \"Анализируем файл: \$FIRST_FILE\"
    head -c 500 \"\$FIRST_FILE\"
    echo ''
    echo ''
    
    echo '4️⃣ Поиск ключевых слов в файлах:'
    echo 'Ищем \"Филиал\":' 
    grep -l \"Филиал\" webhook_uploads/*.json | head -3
    echo ''
    
    echo 'Ищем \"ПродажиПоДням\":'
    grep -l \"ПродажиПоДням\" webhook_uploads/*.json | head -3
    echo ''
    
    echo 'Ищем \"Продажи\":'
    grep -l \"Продажи\" webhook_uploads/*.json | head -3
    echo ''
    
    echo 'Ищем \"ОстаткиПоСкладам\":'
    grep -l \"ОстаткиПоСкладам\" webhook_uploads/*.json | head -3
    echo ''
    
    echo '5️⃣ Детальный анализ одного файла:'
    SAMPLE_FILE=\$(ls webhook_uploads/*.json | head -1)
    echo \"Анализируем файл: \$SAMPLE_FILE\"
    
    # Проверяем является ли файл валидным JSON
    python3 -c \"
import json
try:
    with open('\$SAMPLE_FILE', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    print('✅ Файл является валидным JSON')
    print(f'📊 Тип данных: {type(data)}')
    
    if isinstance(data, list):
        print(f'📊 Элементов в массиве: {len(data)}')
        if len(data) > 0:
            print('📊 Ключи первого элемента:', list(data[0].keys()) if isinstance(data[0], dict) else 'Не словарь')
    elif isinstance(data, dict):
        print('📊 Ключи корневого объекта:', list(data.keys()))
    
except Exception as e:
    print(f'❌ Ошибка парсинга JSON: {e}')
\"
    echo ''
    
    echo '6️⃣ Проверка конкретного файла продаж:'
    # Ищем файл который точно должен быть продажами
    SALES_FILE=\$(find webhook_uploads/ -name \"2024-01-31.json\" | head -1)
    if [ -n \"\$SALES_FILE\" ]; then
        echo \"Детальный анализ файла продаж: \$SALES_FILE\"
        python3 -c \"
import json
try:
    with open('\$SALES_FILE', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    print('✅ Файл загружен')
    print(f'Тип: {type(data)}')
    
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        print('Ключи первого элемента:', list(first_item.keys()))
        
        if 'Филиал' in first_item:
            print(f'Филиал: {first_item[\\\"Филиал\\\"]}')
        
        if 'Продажи' in first_item:
            sales = first_item['Продажи']
            print(f'Продаж дней: {len(sales)}')
            if len(sales) > 0:
                first_day = sales[0]
                print('Структура первого дня:', list(first_day.keys()))
                if 'ПродажиПоДням' in first_day:
                    daily_sales = first_day['ПродажиПоДням']
                    print(f'Товаров в первый день: {len(daily_sales)}')
                    if len(daily_sales) > 0:
                        print('Структура товара:', list(daily_sales[0].keys()))
                        
except Exception as e:
    print(f'❌ Ошибка: {e}')
\"
    else
        echo '❌ Файл 2024-01-31.json не найден'
    fi
"

echo ""
echo "✅ ДИАГНОСТИКА ЗАВЕРШЕНА!"
echo ""
echo "🎯 На основе результатов создам исправленный скрипт загрузки"
echo ""