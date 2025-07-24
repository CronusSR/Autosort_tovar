#!/bin/bash

# ЗАМЕНА ФАЙЛОВ ПРОДАЖ ИЗ ВЫГРУЗКА JSON.ZIP
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📦 ЗАМЕНА ФАЙЛОВ ПРОДАЖ ИЗ ZIP АРХИВА"
echo "===================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 ПЛАН:"
echo "   1️⃣ Найти 'Выгрузка JSON.zip'"
echo "   2️⃣ Очистить webhook_uploads/"
echo "   3️⃣ Распаковать новые файлы продаж"
echo "   4️⃣ Загрузить правильные данные"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '🔍 ПОИСК ZIP АРХИВА'
    echo '==================='
    
    # Ищем ZIP файл с выгрузкой
    ZIP_FILE=\$(find . -iname '*выгрузка*json*.zip' -o -iname '*выгрузка*JSON*.zip' 2>/dev/null | head -1)
    
    if [ -z \"\$ZIP_FILE\" ]; then
        echo '⚠️ Не найден \"Выгрузка JSON.zip\"'
        echo ''
        echo '🔍 Ищем другие ZIP файлы:'
        find . -name \"*.zip\" -type f | head -10
        echo ''
        echo '💡 Попробуем найти архивы с любым названием...'
        
        # Ищем любые ZIP файлы
        ZIP_FILE=\$(find . -name \"*.zip\" -type f | head -1)
        
        if [ -z \"\$ZIP_FILE\" ]; then
            echo '❌ НЕ НАЙДЕНО ZIP ФАЙЛОВ'
            echo 'Убедитесь что \"Выгрузка JSON.zip\" находится в /opt/inventory_system/'
            exit 1
        else
            echo \"⚠️ Используем найденный ZIP: \$ZIP_FILE\"
        fi
    else
        echo \"✅ Найден ZIP файл: \$ZIP_FILE\"
    fi
    
    echo ''
    echo '💾 БЭКАП ТЕКУЩИХ ФАЙЛОВ'
    echo '======================='
    
    # Создаем бэкап базы
    cp webhook_data.db webhook_data_backup_zip_\$(date +%Y%m%d_%H%M%S).db
    echo '✅ Бэкап базы создан'
    
    # Бэкап старых файлов webhook_uploads
    if [ -d webhook_uploads ]; then
        mv webhook_uploads webhook_uploads_backup_\$(date +%Y%m%d_%H%M%S)
        echo '✅ Бэкап webhook_uploads создан'
    fi
    
    echo ''
    echo '📦 РАСПАКОВКА ZIP АРХИВА'
    echo '======================='
    
    # Создаем новую директорию webhook_uploads
    mkdir -p webhook_uploads
    
    # Создаем временную директорию для распаковки
    mkdir -p temp_extract_\$(date +%Y%m%d_%H%M%S)
    TEMP_DIR=\"temp_extract_\$(date +%Y%m%d_%H%M%S)\"
    
    echo \"📂 Распаковка \$ZIP_FILE в \$TEMP_DIR\"
    unzip -q \"\$ZIP_FILE\" -d \"\$TEMP_DIR/\"
    
    if [ \$? -eq 0 ]; then
        echo '✅ ZIP файл успешно распакован'
        
        # Показываем что распаковалось
        echo ''
        echo '📋 Содержимое архива:'
        find \"\$TEMP_DIR\" -type f -name \"*.json\" | head -10
        echo ''
        
        # Перемещаем JSON файлы в webhook_uploads
        JSON_COUNT=0
        find \"\$TEMP_DIR\" -name \"*.json\" -type f | while read json_file; do
            mv \"\$json_file\" webhook_uploads/
            JSON_COUNT=\$((JSON_COUNT + 1))
        done
        
        # Удаляем временную директорию
        rm -rf \"\$TEMP_DIR\"
        
        echo \"✅ JSON файлы перемещены в webhook_uploads/\"
        
        # Показываем что получилось
        echo ''
        echo '📊 Новые файлы в webhook_uploads/:'
        ls -la webhook_uploads/*.json | head -5
        echo \"   ... и еще \$(ls webhook_uploads/*.json 2>/dev/null | wc -l) файлов\"
        
    else
        echo '❌ Ошибка распаковки ZIP файла'
        rm -rf \"\$TEMP_DIR\"
        exit 1
    fi
    
    echo ''
    echo '🗑️ ОЧИСТКА БАЗЫ ДАННЫХ'
    echo '======================='
    sqlite3 webhook_data.db \"
        DELETE FROM sales;
        DELETE FROM stock;
        DELETE FROM upload_history;
    \"
    echo '✅ Все таблицы очищены'
    
    echo ''
    echo '📥 СОЗДАНИЕ АДАПТИВНОГО ЗАГРУЗЧИКА'
    echo '=================================='
    
    cat > adaptive_loader.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import os
import glob
from datetime import datetime

def analyze_json_structure(filepath):
    \"\"\"Анализирует структуру JSON файла\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        filename = os.path.basename(filepath)
        print(f\"📁 Анализ: {filename}\")
        
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f\"   📊 Тип: Объект с ключами: {keys[:5]}...\")
            
            # Проверяем на остатки
            if 'ОстаткиПоСкладам' in data:
                print(f\"   🎯 Определен как: ОСТАТКИ\")
                return 'stock', data
            else:
                print(f\"   ⚠️ Неизвестный объект\")
                return 'unknown', data
                
        elif isinstance(data, list):
            print(f\"   📊 Тип: Массив из {len(data)} элементов\")
            
            if len(data) > 0:
                first_item = data[0]
                if isinstance(first_item, dict):
                    item_keys = list(first_item.keys())
                    print(f\"   🔑 Ключи первого элемента: {item_keys}\")
                    
                    # Проверяем разные варианты продаж
                    if 'Филиал' in first_item:
                        if 'Продажи' in first_item:
                            print(f\"   🎯 Определен как: ПРОДАЖИ (Филиал->Продажи)\")
                            return 'sales_v1', data
                        elif 'ПродажиПоДням' in first_item:
                            print(f\"   🎯 Определен как: ПРОДАЖИ (Филиал->ПродажиПоДням)\")
                            return 'sales_v2', data
                        else:
                            print(f\"   ⚠️ Филиал без продаж\")
                            return 'unknown', data
                    elif any(key in first_item for key in ['Артикул', 'Номенклатура', 'Количество']):
                        print(f\"   🎯 Определен как: ПРОДАЖИ (Прямой список товаров)\")
                        return 'sales_v3', data
                    else:
                        print(f\"   ⚠️ Неизвестная структура массива\")
                        return 'unknown', data
        
        return 'unknown', data
        
    except Exception as e:
        print(f\"   ❌ Ошибка анализа: {e}\")
        return 'error', None

def load_sales_v1(data, filename):
    \"\"\"Загружает продажи формата: Филиал->Продажи->День->ПродажиПоДням\"\"\"
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    sales_count = 0
    
    for branch_data in data:
        branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
        sales_data = branch_data.get('Продажи', [])
        
        for day_data in sales_data:
            date = day_data.get('День', '')
            daily_sales = day_data.get('ПродажиПоДням', [])
            
            for item in daily_sales:
                try:
                    category_path = item.get('ПутьКатегорий', '')
                    category = 'Неопределенная'
                    
                    if category_path:
                        parts = [p.strip() for p in category_path.split('/') if p.strip()]
                        if parts and parts[-1] == 'Мебельная фурнитура':
                            parts = parts[:-1]
                        if parts:
                            category_path = '/'.join(reversed(parts)) + '/'
                            category = parts[-1] if parts else 'Неопределенная'
                    
                    data_hash = f\"zip_{date}_{branch_name}_{item.get('Артикул', '')}_{filename}\"
                    
                    cursor.execute(\"\"\"
                        INSERT OR REPLACE INTO sales 
                        (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \"\"\", (
                        date, branch_name, 
                        item.get('Артикул', ''),
                        item.get('Номенклатура', ''),
                        float(item.get('Количество', 0)),
                        float(item.get('Выручка', 0)),
                        category, category_path, data_hash
                    ))
                    sales_count += 1
                except Exception as e:
                    continue
    
    conn.commit()
    conn.close()
    return sales_count

def load_sales_v2(data, filename):
    \"\"\"Загружает продажи формата: Филиал->ПродажиПоДням\"\"\"
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    sales_count = 0
    date = filename.replace('.json', '')  # Дата из имени файла
    
    for branch_data in data:
        branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
        daily_sales = branch_data.get('ПродажиПоДням', [])
        
        for item in daily_sales:
            try:
                category_path = item.get('ПутьКатегорий', '')
                category = 'Неопределенная'
                
                if category_path:
                    parts = [p.strip() for p in category_path.split('/') if p.strip()]
                    if parts and parts[-1] == 'Мебельная фурнитура':
                        parts = parts[:-1]
                    if parts:
                        category_path = '/'.join(reversed(parts)) + '/'
                        category = parts[-1] if parts else 'Неопределенная'
                
                data_hash = f\"zip_{date}_{branch_name}_{item.get('Артикул', '')}_{filename}\"
                
                cursor.execute(\"\"\"
                    INSERT OR REPLACE INTO sales 
                    (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\", (
                    date, branch_name, 
                    item.get('Артикул', ''),
                    item.get('Номенклатура', ''),
                    float(item.get('Количество', 0)),
                    float(item.get('Выручка', 0)),
                    category, category_path, data_hash
                ))
                sales_count += 1
            except Exception as e:
                continue
    
    conn.commit()
    conn.close()
    return sales_count

def load_stock(data, filename):
    \"\"\"Загружает остатки\"\"\"
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    # Очищаем старые остатки
    cursor.execute('DELETE FROM stock')
    
    stock_count = 0
    stock_date = data.get('ДатаОстатков', '').split('T')[0]
    if not stock_date:
        stock_date = '2025-06-30'
    
    for warehouse_data in data.get('ОстаткиПоСкладам', []):
        warehouse = warehouse_data.get('Склад', '')
        
        for item in warehouse_data.get('Остатки', []):
            try:
                qty = float(item.get('Количество', 0))
                cost = float(item.get('Стоимость', 0))
                if qty > 0:
                    price = cost / qty if qty > 0 else 0
                    
                    cursor.execute(\"\"\"
                        INSERT OR REPLACE INTO stock 
                        (date, warehouse, item_code, item_name, quantity, price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    \"\"\", (
                        stock_date, warehouse, 
                        item.get('Артикул', ''),
                        item.get('Номенклатура', ''),
                        qty, price
                    ))
                    stock_count += 1
            except Exception as e:
                continue
    
    conn.commit()
    conn.close()
    return stock_count

def main():
    print(\"🔄 АДАПТИВНАЯ ЗАГРУЗКА ФАЙЛОВ\")
    print(\"=\" * 30)
    
    total_sales = 0
    total_stock = 0
    
    # Загружаем из webhook_uploads
    json_files = glob.glob('webhook_uploads/*.json')
    
    # Также проверяем корневую директорию для остатков
    json_files.extend(glob.glob('*.json'))
    
    print(f\"📂 Найдено файлов: {len(json_files)}\")
    print()
    
    for filepath in json_files:
        file_type, data = analyze_json_structure(filepath)
        filename = os.path.basename(filepath)
        
        if file_type == 'sales_v1':
            count = load_sales_v1(data, filename)
            total_sales += count
            print(f\"   ✅ Загружено продаж: {count}\")
            
        elif file_type == 'sales_v2':
            count = load_sales_v2(data, filename)
            total_sales += count
            print(f\"   ✅ Загружено продаж: {count}\")
            
        elif file_type == 'stock':
            count = load_stock(data, filename)
            total_stock += count
            print(f\"   ✅ Загружено остатков: {count}\")
            
        else:
            print(f\"   ⚠️ Пропущен (неизвестный формат)\")
        
        print()
    
    print(\"📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:\")
    print(f\"   💰 Продаж загружено: {total_sales}\")
    print(f\"   📦 Остатков загружено: {total_stock}\")
    
    # Финальная статистика
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT MIN(date), MAX(date) FROM sales WHERE date != \"\"')
    date_range = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(DISTINCT branch) FROM sales')
    branches = cursor.fetchone()[0]
    
    print()
    print(\"📈 ДЕТАЛЬНАЯ СТАТИСТИКА:\")
    if date_range[0]:
        print(f\"   📅 Период продаж: {date_range[0]} - {date_range[1]}\")
    print(f\"   🏢 Филиалов с продажами: {branches}\")
    
    conn.close()

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК АДАПТИВНОЙ ЗАГРУЗКИ'
    echo '============================'
    python3 adaptive_loader.py
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ЗАМЕНА ФАЙЛОВ ЗАВЕРШЕНА!'
        echo ''
        echo '📊 НОВАЯ КОНФИГУРАЦИЯ:'
        echo '   💰 Продажи: webhook_uploads/*.json (из ZIP архива)'
        echo '   📦 Остатки: 2025-06-30 (4).json'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f adaptive_loader.py
"

echo ""
echo "✅ СКРИПТ ЗАМЕНЫ ФАЙЛОВ ИЗ ZIP СОЗДАН!"
echo ""
echo "🎯 Этот скрипт:"
echo "   - Найдет 'Выгрузка JSON.zip'"
echo "   - Заменит файлы в webhook_uploads/"
echo "   - Загрузит правильные данные продаж"
echo ""