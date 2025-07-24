#!/bin/bash

# АНАЛИЗ РЕАЛЬНОЙ СТРУКТУРЫ ФАЙЛОВ ПРОДАЖ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 АНАЛИЗ СТРУКТУРЫ ФАЙЛОВ ПРОДАЖ"
echo "================================="
echo "📅 Время: $(date)"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '📂 ДЕТАЛЬНЫЙ АНАЛИЗ ФАЙЛОВ ПРОДАЖ'
    echo '================================='
    
    # Создаем скрипт для анализа структуры
    cat > analyze_structure.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import os

def analyze_file(filepath):
    try:
        print(f\"\\n📁 АНАЛИЗ ФАЙЛА: {os.path.basename(filepath)}\")
        print(\"=\" * 50)
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        print(f\"📊 Тип данных: {type(data)}\")
        print(f\"📏 Размер файла: {os.path.getsize(filepath)} байт\")
        
        if isinstance(data, list):
            print(f\"📋 Элементов в массиве: {len(data)}\")
            if len(data) > 0:
                first_item = data[0]
                print(f\"📊 Тип первого элемента: {type(first_item)}\")
                if isinstance(first_item, dict):
                    print(f\"🔑 Ключи первого элемента: {list(first_item.keys())}\")
                    
                    # Анализируем каждый ключ
                    for key, value in first_item.items():
                        print(f\"   {key}: {type(value)} - {str(value)[:100]}...\")
                        
                        # Если это список, анализируем его структуру
                        if isinstance(value, list) and len(value) > 0:
                            print(f\"     └─ Элементов в {key}: {len(value)}\")
                            if isinstance(value[0], dict):
                                print(f\"     └─ Ключи в {key}[0]: {list(value[0].keys())}\")
                                
                                # Если это может быть продажи по дням
                                if any(k in value[0] for k in ['День', 'ПродажиПоДням', 'Продажи']):
                                    print(f\"     └─ 🎯 ВОЗМОЖНЫЕ ПРОДАЖИ НАЙДЕНЫ!\")
                                    for subkey, subvalue in value[0].items():
                                        print(f\"        {subkey}: {type(subvalue)}\")
                                        if isinstance(subvalue, list) and len(subvalue) > 0:
                                            print(f\"          └─ Элементов: {len(subvalue)}\")
                                            if isinstance(subvalue[0], dict):
                                                print(f\"          └─ Ключи товара: {list(subvalue[0].keys())}\")
                
        elif isinstance(data, dict):
            print(f\"🔑 Ключи корневого объекта: {list(data.keys())}\")
            
            # Анализируем каждый ключ
            for key, value in data.items():
                print(f\"   {key}: {type(value)}\")
                if isinstance(value, str):
                    print(f\"     └─ Значение: {value}\")
                elif isinstance(value, list):
                    print(f\"     └─ Элементов: {len(value)}\")
                    if len(value) > 0 and isinstance(value[0], dict):
                        print(f\"     └─ Ключи первого элемента: {list(value[0].keys())}\")
        
        print(\"\\n✅ Анализ завершен\")
        
    except Exception as e:
        print(f\"❌ Ошибка анализа файла {filepath}: {e}\")

# Анализируем несколько файлов
files_to_analyze = [
    'webhook_uploads/2024-01-31.json',
    'webhook_uploads/2024-02-29.json', 
    'webhook_uploads/2025-06-30.json'
]

print(\"🔍 АНАЛИЗ СТРУКТУРЫ JSON ФАЙЛОВ\")
print(\"=\" * 60)

for filepath in files_to_analyze:
    if os.path.exists(filepath):
        analyze_file(filepath)
    else:
        print(f\"❌ Файл не найден: {filepath}\")

print(\"\\n🎯 ПОИСК ПРИЗНАКОВ ПРОДАЖ\")
print(\"=\" * 30)

# Ищем файлы с признаками продаж
import glob
for filepath in glob.glob('webhook_uploads/*.json'):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read(1000)  # Первые 1000 символов
            
        sales_indicators = [
            'Филиал', 'Продажи', 'ПродажиПоДням', 'День', 
            'Выручка', 'Количество', 'НачалоПериода', 'КонецПериода'
        ]
        
        found_indicators = [ind for ind in sales_indicators if ind in content]
        
        if found_indicators:
            print(f\"📁 {os.path.basename(filepath)}: {found_indicators}\")
            
    except Exception as e:
        continue

print(\"\\n✅ АНАЛИЗ ЗАВЕРШЕН\")
PYTHON_END
    
    echo '🔄 ЗАПУСК АНАЛИЗА СТРУКТУРЫ'
    echo '==========================='
    python3 analyze_structure.py
    
    echo ''
    echo '📋 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА'
    echo '============================='
    
    # Проверяем один файл вручную
    echo '📖 Проверяем содержимое одного файла:'
    SAMPLE_FILE=\$(ls webhook_uploads/*.json | head -1)
    echo \"Файл: \$SAMPLE_FILE\"
    echo \"Первые 20 строк:\"
    head -20 \"\$SAMPLE_FILE\"
    
    echo ''
    echo '🔍 Поиск ключевых слов:'
    echo 'Поиск \"Филиал\":'
    grep -n \"Филиал\" \"\$SAMPLE_FILE\" | head -3
    
    echo 'Поиск \"Продажи\":'
    grep -n \"Продажи\" \"\$SAMPLE_FILE\" | head -3
    
    echo 'Поиск \"ПродажиПоДням\":'
    grep -n \"ПродажиПоДням\" \"\$SAMPLE_FILE\" | head -3
    
    # Очистка
    rm -f analyze_structure.py
"

echo ""
echo "✅ АНАЛИЗ ЗАВЕРШЕН!"
echo ""
echo "🎯 На основе результатов создам правильный загрузчик"
echo ""