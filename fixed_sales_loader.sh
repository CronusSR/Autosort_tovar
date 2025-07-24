#!/bin/bash

# ИСПРАВЛЕННЫЙ ЗАГРУЗЧИК ПРОДАЖ НА ОСНОВЕ АНАЛИЗА
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕННЫЙ ЗАГРУЗЧИК ПРОДАЖ"
echo "==============================="
echo "📅 Время: $(date)"
echo ""
echo "💡 На основе анализа создаем правильный парсер для JSON структуры"
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
    cp webhook_data.db webhook_data_backup_fixed_\$(date +%Y%m%d_%H%M%S).db
    echo '✅ Бэкап создан'
    echo ''
    
    echo '🗑️ ОЧИСТКА ДАННЫХ'
    echo '================='
    sqlite3 webhook_data.db \"
        DELETE FROM sales;
        DELETE FROM stock;
        DELETE FROM upload_history;
    \"
    echo '✅ Данные очищены'
    echo ''
    
    echo '📥 СОЗДАНИЕ УНИВЕРСАЛЬНОГО ЗАГРУЗЧИКА'
    echo '===================================='
    
    cat > universal_loader.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import os
import glob
from datetime import datetime

def analyze_and_load_file(filepath):
    \"\"\"Универсальный анализ и загрузка файла\"\"\"
    try:
        filename = os.path.basename(filepath)
        print(f\"📁 Анализируем: {filename}\")
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('webhook_data.db')
        cursor = conn.cursor()
        
        sales_count = 0
        stock_count = 0
        
        # Определяем тип файла по содержимому
        if isinstance(data, dict):
            # Это файл остатков
            if 'ОстаткиПоСкладам' in data:
                print(f\"   📦 Тип: Файл остатков\")
                
                # Очищаем старые остатки
                cursor.execute('DELETE FROM stock')
                
                stock_date = data.get('ДатаОстатков', '').split('T')[0]
                if not stock_date:
                    stock_date = filename.replace('.json', '')
                
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
                            
        elif isinstance(data, list):
            print(f\"   💰 Тип: Файл продаж (массив из {len(data)} элементов)\")
            
            # Анализируем структуру первого элемента
            if len(data) > 0:
                first_item = data[0]
                print(f\"   🔑 Ключи: {list(first_item.keys())}\")
                
                # Пробуем разные варианты структуры продаж
                for branch_data in data:
                    if not isinstance(branch_data, dict):
                        continue
                        
                    branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
                    
                    # Вариант 1: {\"Филиал\": \"...\", \"Продажи\": [{\"День\": \"...\", \"ПродажиПоДням\": [...]}]}
                    if 'Продажи' in branch_data:
                        print(f\"   📊 Структура: Филиал -> Продажи -> День -> ПродажиПоДням\")
                        for day_data in branch_data.get('Продажи', []):
                            date = day_data.get('День', '')
                            daily_sales = day_data.get('ПродажиПоДням', [])
                            
                            for item in daily_sales:
                                sales_count += process_sale_item(cursor, item, date, branch_name, filename)
                    
                    # Вариант 2: {\"Филиал\": \"...\", \"ПродажиПоДням\": [...]}
                    elif 'ПродажиПоДням' in branch_data:
                        print(f\"   📊 Структура: Филиал -> ПродажиПоДням\")
                        date = filename.replace('.json', '')  # Дата из имени файла
                        daily_sales = branch_data.get('ПродажиПоДням', [])
                        
                        for item in daily_sales:
                            sales_count += process_sale_item(cursor, item, date, branch_name, filename)
                    
                    # Вариант 3: Прямой массив товаров без филиалов
                    elif any(key in branch_data for key in ['Артикул', 'Номенклатура', 'Количество']):
                        print(f\"   📊 Структура: Прямой массив товаров\")
                        date = filename.replace('.json', '')
                        branch_name = 'Все филиалы'
                        
                        sales_count += process_sale_item(cursor, branch_data, date, branch_name, filename)
        
        # Сохраняем в историю
        if sales_count > 0:
            cursor.execute(\"\"\"
                INSERT INTO upload_history (upload_type, filename, records_processed)
                VALUES (?, ?, ?)
            \"\"\", ('sales', filename, sales_count))
            
        if stock_count > 0:
            cursor.execute(\"\"\"
                INSERT INTO upload_history (upload_type, filename, records_processed)
                VALUES (?, ?, ?)
            \"\"\", ('stock', filename, stock_count))
        
        conn.commit()
        conn.close()
        
        if sales_count > 0:
            print(f\"   ✅ Продаж: {sales_count}\")
        if stock_count > 0:
            print(f\"   ✅ Остатков: {stock_count}\")
        if sales_count == 0 and stock_count == 0:
            print(f\"   ⚠️ Не удалось загрузить данные\")
            
        return sales_count + stock_count
        
    except Exception as e:
        print(f\"   ❌ Ошибка: {e}\")
        return 0

def process_sale_item(cursor, item, date, branch_name, filename):
    \"\"\"Обрабатывает один товар из продаж\"\"\"
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
        return 1
    except Exception as e:
        return 0

def main():
    print(\"🔄 УНИВЕРСАЛЬНАЯ ЗАГРУЗКА JSON ФАЙЛОВ\")
    print(\"=\" * 40)
    
    total_loaded = 0
    
    # Загружаем из webhook_uploads
    json_files = glob.glob('webhook_uploads/*.json')
    
    # Также проверяем корневую директорию
    json_files.extend(glob.glob('*.json'))
    
    print(f\"📂 Найдено файлов: {len(json_files)}\")
    
    for filepath in json_files:
        total_loaded += analyze_and_load_file(filepath)
    
    print(f\"\\n📊 ИТОГО ОБРАБОТАНО: {total_loaded} записей\")
    
    # Проверяем результат
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM sales')
    sales_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stock') 
    stock_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(date), MAX(date) FROM sales WHERE date != \"\"')
    date_range = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(DISTINCT branch) FROM sales')
    branches = cursor.fetchone()[0]
    
    print(f\"\\n📈 РЕЗУЛЬТАТ:\")
    print(f\"   💰 Продаж в БД: {sales_total}\")
    print(f\"   📦 Остатков в БД: {stock_total}\")
    if date_range[0]:
        print(f\"   📅 Период продаж: {date_range[0]} - {date_range[1]}\")
    print(f\"   🏢 Филиалов: {branches}\")
    
    conn.close()

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК УНИВЕРСАЛЬНОЙ ЗАГРУЗКИ'
    echo '==============================='
    python3 universal_loader.py
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ИСПРАВЛЕННАЯ ЗАГРУЗКА ЗАВЕРШЕНА!'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f universal_loader.py
"

echo ""
echo "✅ ИСПРАВЛЕННЫЙ ЗАГРУЗЧИК СОЗДАН!"
echo ""
echo "🎯 Этот скрипт использует универсальный подход для загрузки"
echo "   - Автоматически определяет тип файла (продажи/остатки)"
echo "   - Поддерживает разные структуры JSON"
echo "   - Обрабатывает файлы с любой вложенностью"
echo ""