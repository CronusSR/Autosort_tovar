#!/bin/bash

# ПРАВИЛЬНАЯ НАСТРОЙКА ДАННЫХ ПРОДАЖ И ОСТАТКОВ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ПРАВИЛЬНАЯ НАСТРОЙКА ДАННЫХ"
echo "=============================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 ПЛАН:"
echo "   1️⃣ Продажи: webhook_uploads/*.json (2024-01-31.json и др.)"
echo "   2️⃣ Остатки: 2025-06-30 (4).json"
echo "   3️⃣ Удалить: test_stock_data.json"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '💾 БЭКАП БАЗЫ'
    echo '============='
    cp webhook_data.db webhook_data_backup_correct_\$(date +%Y%m%d_%H%M%S).db
    echo '✅ Бэкап создан'
    echo ''
    
    echo '🗑️ УДАЛЕНИЕ ТЕСТОВЫХ ФАЙЛОВ'
    echo '============================'
    if [ -f 'test_stock_data.json' ]; then
        rm -f test_stock_data.json
        echo '✅ Удален test_stock_data.json'
    else
        echo '⚠️ test_stock_data.json не найден'
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
    
    echo '📋 АНАЛИЗ ДОСТУПНЫХ ФАЙЛОВ'
    echo '=========================='
    echo 'Файлы продаж в webhook_uploads/:'
    ls -la webhook_uploads/*.json 2>/dev/null || echo 'Нет JSON файлов в webhook_uploads/'
    echo ''
    echo 'Файл остатков в корне:'
    ls -la \"2025-06-30 (4).json\" 2>/dev/null || echo 'Файл остатков не найден'
    echo ''
    
    echo '📥 СОЗДАНИЕ ТОЧЕЧНОГО ЗАГРУЗЧИКА'
    echo '==============================='
    
    cat > precise_loader.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import os
import glob
from datetime import datetime

def load_sales_from_webhook(webhook_dir='webhook_uploads'):
    \"\"\"Загружает продажи из webhook_uploads/*.json\"\"\"
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    sales_count = 0
    files_processed = 0
    
    print(f\"📂 Загрузка продаж из {webhook_dir}/\")
    
    # Ищем все JSON файлы в webhook_uploads
    json_files = glob.glob(f'{webhook_dir}/*.json')
    
    if not json_files:
        print(f\"   ❌ Нет JSON файлов в {webhook_dir}/\")
        return 0, 0
    
    print(f\"   📊 Найдено файлов: {len(json_files)}\")
    
    for filepath in json_files:
        try:
            filename = os.path.basename(filepath)
            print(f\"   📁 Обрабатываем: {filename}\")
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            file_sales = 0
            
            # Ожидаем структуру: [{{\"Филиал\": \"...\", \"Продажи\": [{{\"День\": \"...\", \"ПродажиПоДням\": [...]}}]}}]
            if isinstance(data, list):
                for branch_data in data:
                    if not isinstance(branch_data, dict):
                        continue
                        
                    branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
                    sales_data = branch_data.get('Продажи', [])
                    
                    for day_data in sales_data:
                        date = day_data.get('День', '')
                        daily_sales = day_data.get('ПродажиПоДням', [])
                        
                        for item in daily_sales:
                            try:
                                # Обрабатываем категорию
                                category_path = item.get('ПутьКатегорий', '')
                                category = 'Неопределенная'
                                
                                if category_path:
                                    parts = [p.strip() for p in category_path.split('/') if p.strip()]
                                    if parts and parts[-1] == 'Мебельная фурнитура':
                                        parts = parts[:-1]
                                    if parts:
                                        category_path = '/'.join(reversed(parts)) + '/'
                                        category = parts[-1] if parts else 'Неопределенная'
                                
                                data_hash = f\"webhook_{date}_{branch_name}_{item.get('Артикул', '')}_{filename}\"
                                
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
                                file_sales += 1
                                sales_count += 1
                            except Exception as e:
                                continue
            
            if file_sales > 0:
                # Записываем в историю
                cursor.execute(\"\"\"
                    INSERT INTO upload_history (upload_type, filename, records_processed)
                    VALUES (?, ?, ?)
                \"\"\", ('sales', filename, file_sales))
                
                print(f\"      ✅ Загружено: {file_sales} продаж\")
                files_processed += 1
            else:
                print(f\"      ⚠️ Не найдено продаж в файле\")
                
        except Exception as e:
            print(f\"      ❌ Ошибка: {e}\")
            continue
    
    conn.commit()
    conn.close()
    
    return sales_count, files_processed

def load_stock_from_file(stock_file='2025-06-30 (4).json'):
    \"\"\"Загружает остатки из конкретного файла\"\"\"
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    stock_count = 0
    
    print(f\"📦 Загрузка остатков из {stock_file}\")
    
    if not os.path.exists(stock_file):
        print(f\"   ❌ Файл {stock_file} не найден\")
        return 0
    
    try:
        with open(stock_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        # Очищаем старые остатки
        cursor.execute('DELETE FROM stock')
        
        # Ожидаем структуру: {{\"ДатаОстатков\": \"...\", \"ОстаткиПоСкладам\": [...]}}
        if isinstance(data, dict) and 'ОстаткиПоСкладам' in data:
            stock_date = data.get('ДатаОстатков', '').split('T')[0]
            if not stock_date:
                stock_date = '2025-06-30'  # По умолчанию из имени файла
            
            print(f\"   📅 Дата остатков: {stock_date}\")
            
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
            
            # Записываем в историю
            cursor.execute(\"\"\"
                INSERT INTO upload_history (upload_type, filename, records_processed)
                VALUES (?, ?, ?)
            \"\"\", ('stock', os.path.basename(stock_file), stock_count))
            
            print(f\"   ✅ Загружено: {stock_count} остатков\")
        else:
            print(f\"   ❌ Неправильная структура файла остатков\")
            
    except Exception as e:
        print(f\"   ❌ Ошибка: {e}\")
    
    conn.commit()
    conn.close()
    
    return stock_count

def main():
    print(\"🔄 ТОЧЕЧНАЯ ЗАГРУЗКА ДАННЫХ\")
    print(\"=\" * 30)
    
    # Загружаем продажи из webhook_uploads
    sales_total, sales_files = load_sales_from_webhook()
    
    print()
    
    # Загружаем остатки из конкретного файла
    stock_total = load_stock_from_file()
    
    print()
    print(\"📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:\")
    print(f\"   💰 Продаж загружено: {sales_total} из {sales_files} файлов\")
    print(f\"   📦 Остатков загружено: {stock_total}\")
    
    # Финальная проверка
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT MIN(date), MAX(date) FROM sales WHERE date != \"\"')
    date_range = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(DISTINCT branch) FROM sales')
    branches = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT warehouse) FROM stock')
    warehouses = cursor.fetchone()[0]
    
    print()
    print(\"📈 ДЕТАЛЬНАЯ СТАТИСТИКА:\")
    if date_range[0]:
        print(f\"   📅 Период продаж: {date_range[0]} - {date_range[1]}\")
    print(f\"   🏢 Филиалов с продажами: {branches}\")
    print(f\"   🏭 Складов с остатками: {warehouses}\")
    
    conn.close()

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК ТОЧЕЧНОЙ ЗАГРУЗКИ'
    echo '=========================='
    python3 precise_loader.py
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ПРАВИЛЬНАЯ НАСТРОЙКА ЗАВЕРШЕНА!'
        echo ''
        echo '📊 КОНФИГУРАЦИЯ:'
        echo '   💰 Продажи: webhook_uploads/*.json'
        echo '   📦 Остатки: 2025-06-30 (4).json'
        echo '   🗑️ Удален: test_stock_data.json'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f precise_loader.py
"

echo ""
echo "✅ СКРИПТ ПРАВИЛЬНОЙ НАСТРОЙКИ СОЗДАН!"
echo ""
echo "🎯 Данный скрипт:"
echo "   - Использует файлы webhook_uploads/*.json как продажи"
echo "   - Использует 2025-06-30 (4).json как остатки"
echo "   - Удаляет test_stock_data.json"
echo ""