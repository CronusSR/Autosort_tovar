#!/bin/bash

# ПРОСТОЕ ВОССТАНОВЛЕНИЕ ДАННЫХ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ПРОСТОЕ ВОССТАНОВЛЕНИЕ ДАННЫХ"
echo "================================"
echo "📅 Время: $(date)"
echo ""
echo "💡 На основе диагностики мы знаем что:"
echo "   - Файлы продаж есть в webhook_uploads/"
echo "   - Ранее они успешно загружались"
echo "   - Текущая проблема в логике парсинга"
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
    cp webhook_data.db webhook_data_backup_simple_\$(date +%Y%m%d_%H%M%S).db
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
    
    echo '📥 СОЗДАНИЕ УЛУЧШЕННОГО ЗАГРУЗЧИКА'
    echo '=================================='
    
    cat > simple_loader.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import os
import glob
from datetime import datetime

def load_file(filepath):
    \"\"\"Универсальная загрузка файла\"\"\"
    try:
        filename = os.path.basename(filepath)
        print(f\"📁 Обрабатываем: {filename}\")
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('webhook_data.db')
        cursor = conn.cursor()
        
        sales_count = 0
        stock_count = 0
        
        # Проверяем тип файла по содержимому
        if isinstance(data, list):
            # Вероятно файл продаж (массив филиалов)
            for item in data:
                if isinstance(item, dict):
                    # Ищем признаки файла продаж
                    if any(key in item for key in ['Филиал', 'Продажи', 'ПродажиПоДням']):
                        # Это файл продаж
                        branch_name = item.get('Филиал', 'Неизвестный филиал')
                        
                        # Проверяем разные возможные структуры
                        if 'Продажи' in item:
                            # Структура: [{\"Филиал\": \"...\", \"Продажи\": [{\"День\": \"...\", \"ПродажиПоДням\": [...]}]}]
                            for day_data in item['Продажи']:
                                date = day_data.get('День', '')
                                for sale_item in day_data.get('ПродажиПоДням', []):
                                    try:
                                        category_path = sale_item.get('ПутьКатегорий', '')
                                        category = 'Неопределенная'
                                        
                                        if category_path:
                                            parts = [p.strip() for p in category_path.split('/') if p.strip()]
                                            if parts and parts[-1] == 'Мебельная фурнитура':
                                                parts = parts[:-1]
                                            if parts:
                                                category_path = '/'.join(reversed(parts)) + '/'
                                                category = parts[-1] if parts else 'Неопределенная'
                                        
                                        data_hash = f\"webhook_{date}_{branch_name}_{sale_item.get('Артикул', '')}_{filename}\"
                                        
                                        cursor.execute(\"\"\"
                                            INSERT OR REPLACE INTO sales 
                                            (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        \"\"\", (
                                            date, branch_name, 
                                            sale_item.get('Артикул', ''),
                                            sale_item.get('Номенклатура', ''),
                                            float(sale_item.get('Количество', 0)),
                                            float(sale_item.get('Выручка', 0)),
                                            category, category_path, data_hash
                                        ))
                                        sales_count += 1
                                    except Exception as e:
                                        continue
                                        
                        elif 'ПродажиПоДням' in item:
                            # Альтернативная структура: [{\"Филиал\": \"...\", \"ПродажиПоДням\": [...]}]
                            for sale_item in item.get('ПродажиПоДням', []):
                                try:
                                    # Получаем дату из имени файла или используем текущую
                                    date = filename.replace('.json', '')
                                    
                                    category_path = sale_item.get('ПутьКатегорий', '')
                                    category = 'Неопределенная'
                                    
                                    if category_path:
                                        parts = [p.strip() for p in category_path.split('/') if p.strip()]
                                        if parts and parts[-1] == 'Мебельная фурнитура':
                                            parts = parts[:-1]
                                        if parts:
                                            category_path = '/'.join(reversed(parts)) + '/'
                                            category = parts[-1] if parts else 'Неопределенная'
                                    
                                    data_hash = f\"webhook_{date}_{branch_name}_{sale_item.get('Артикул', '')}_{filename}\"
                                    
                                    cursor.execute(\"\"\"
                                        INSERT OR REPLACE INTO sales 
                                        (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    \"\"\", (
                                        date, branch_name,
                                        sale_item.get('Артикул', ''),
                                        sale_item.get('Номенклатура', ''),
                                        float(sale_item.get('Количество', 0)),
                                        float(sale_item.get('Выручка', 0)),
                                        category, category_path, data_hash
                                    ))
                                    sales_count += 1
                                except Exception as e:
                                    continue
                    else:
                        # Возможно остатки или другие данные
                        print(f\"   ⚠️ Неизвестная структура в {filename}\")
                        
        elif isinstance(data, dict):
            # Проверяем файл остатков
            if 'ОстаткиПоСкладам' in data:
                print(f\"   📦 Обнаружен файл остатков\")
                
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

def main():
    print(\"🔄 ЗАГРУЗКА ВСЕХ JSON ФАЙЛОВ\")
    print(\"=\" * 30)
    
    total_loaded = 0
    
    # Загружаем из webhook_uploads
    json_files = glob.glob('webhook_uploads/*.json')
    
    # Также проверяем корневую директорию
    json_files.extend(glob.glob('*.json'))
    
    print(f\"📂 Найдено файлов: {len(json_files)}\")
    
    for filepath in json_files:
        total_loaded += load_file(filepath)
    
    print(f\"\\n📊 ИТОГО ОБРАБОТАНО: {total_loaded} записей\")
    
    # Проверяем результат
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM sales')
    sales_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stock') 
    stock_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(date), MAX(date) FROM sales')
    date_range = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(DISTINCT branch) FROM sales')
    branches = cursor.fetchone()[0]
    
    print(f\"\\n📈 РЕЗУЛЬТАТ:\")
    print(f\"   💰 Продаж в БД: {sales_total}\")
    print(f\"   📦 Остатков в БД: {stock_total}\")
    print(f\"   📅 Период продаж: {date_range[0]} - {date_range[1]}\")
    print(f\"   🏢 Филиалов: {branches}\")
    
    conn.close()

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК ЗАГРУЗКИ'
    echo '================='
    python3 simple_loader.py
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f simple_loader.py
"

echo ""
echo "✅ ПРОСТОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""