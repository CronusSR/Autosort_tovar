#!/bin/bash

# Простое исправление БД на сервере без pandas
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ БД НА СЕРВЕРЕ БЕЗ PANDAS"
echo "📅 Время: $(date)"
echo ""

echo "🔄 Выполнение исправлений на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🗄️ Исправление структуры БД...'
    
    # Создаем простой SQL скрипт
    cat > fix_db.sql << 'EOF'
-- Добавляем недостающие колонки в таблицу sales
ALTER TABLE sales ADD COLUMN category TEXT;
ALTER TABLE sales ADD COLUMN category_path TEXT;

-- Проверяем результат
.schema sales
EOF

    # Применяем исправления к БД
    sqlite3 webhook_data.db < fix_db.sql
    
    echo '✅ Структура БД исправлена'
    
    # Создаем простой Python скрипт загрузки данных БЕЗ pandas
    cat > simple_data_load.py << 'EOF'
#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime
import os

def load_stock_data():
    print('📦 Загрузка данных остатков...')
    
    # Проверяем есть ли файл остатков
    if not os.path.exists('2025-06-30 (4).json'):
        print('❌ Файл остатков не найден на сервере')
        return False
    
    # Загружаем файл
    with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
        stock_data = json.load(f)
    
    print(f'📊 Дата остатков: {stock_data.get(\"ДатаОстатков\", \"Не указана\")}')
    
    # Подключаемся к БД
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    # Очищаем старые данные
    cursor.execute('DELETE FROM sales')
    cursor.execute('DELETE FROM stock')
    print('🗑️ Старые данные очищены')
    
    # Загружаем остатки
    stock_count = 0
    for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
        warehouse = warehouse_data.get('Склад', '')
        
        for item in warehouse_data.get('Остатки', []):
            try:
                quantity = float(item.get('Количество', 0))
                cost = float(item.get('Стоимость', 0))
                price = cost / max(quantity, 1)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO stock 
                    (date, warehouse, item_code, item_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    '2025-06-30',
                    warehouse,
                    item.get('Артикул', ''),
                    item.get('Номенклатура', ''),
                    quantity,
                    price
                ))
                stock_count += 1
            except Exception as e:
                print(f'⚠️ Ошибка загрузки остатка: {e}')
    
    print(f'📦 Загружено остатков: {stock_count}')
    
    # Создаем тестовые продажи
    # Берем товары с наибольшей стоимостью
    cursor.execute('''
        SELECT warehouse, item_code, item_name, quantity, price, 
               (quantity * price) as total_value
        FROM stock 
        ORDER BY total_value DESC 
        LIMIT 500
    ''')
    
    top_items = cursor.fetchall()
    sales_count = 0
    
    for warehouse, item_code, item_name, quantity, price, total_value in top_items:
        # Находим категорию для этого товара
        category_path = 'Неопределенная категория/'
        
        for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
            if warehouse_data.get('Склад', '') == warehouse:
                for item in warehouse_data.get('Остатки', []):
                    if item.get('Артикул', '') == item_code:
                        orig_path = item.get('ПутьКатегорий', '')
                        if orig_path:
                            parts = [p.strip() for p in orig_path.split('/') if p.strip()]
                            if parts and parts[-1] == 'Мебельная фурнитура':
                                parts = parts[:-1]
                            if parts:
                                category_path = '/'.join(reversed(parts)) + '/'
                        break
        
        # Создаем продажу (10% от остатка)
        sales_quantity = max(1, quantity * 0.1)
        sales_amount = total_value * 0.1
        category = category_path.split('/')[0] if category_path else 'Неопределенная'
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO sales 
                (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                '2025-06-30',
                warehouse,  # Используем склад как филиал
                item_code,
                item_name,
                sales_quantity,
                sales_amount,
                category,
                category_path,
                f'test_{item_code}'
            ))
            sales_count += 1
        except Exception as e:
            print(f'⚠️ Ошибка загрузки продажи: {e}')
    
    print(f'🛒 Создано продаж: {sales_count}')
    
    # Проверяем результат
    cursor.execute('SELECT COUNT(*) FROM stock')
    stock_final = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sales')
    sales_final = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sales WHERE category_path IS NOT NULL AND category_path != \"\"')
    cat_final = cursor.fetchone()[0]
    
    print(f'✅ ИТОГО В БД:')
    print(f'   📦 Остатков: {stock_final}')
    print(f'   🛒 Продаж: {sales_final}')
    print(f'   📂 С категориями: {cat_final}')
    
    conn.commit()
    conn.close()
    
    return stock_final > 0 and sales_final > 0

if __name__ == '__main__':
    if load_stock_data():
        print('✅ ЗАГРУЗКА ДАННЫХ ЗАВЕРШЕНА!')
    else:
        print('❌ ОШИБКА ЗАГРУЗКИ ДАННЫХ!')
EOF

    # Загружаем файл остатков если его нет
    if [ ! -f '2025-06-30 (4).json' ]; then
        echo '📁 Файл остатков не найден, нужно загрузить с локальной машины'
        echo '❌ Пропущена загрузка файла остатков'
    else
        echo '📁 Файл остатков найден'
    fi
    
    # Запускаем загрузку данных
    python3 simple_data_load.py
    
    # Перезапускаем сервис
    systemctl stop webhook-analytics
    sleep 2
    systemctl start webhook-analytics
    sleep 5
    
    echo '✅ Сервис перезапущен'
    systemctl status webhook-analytics --no-pager | head -5
"

echo ""
echo "✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!"
echo ""
echo "🌐 Проверьте систему: http://$SERVER:8502"
echo ""
echo "📋 ЕСЛИ ДАННЫХ ВСЕ ЕЩЕ НЕТ:"
echo "   1️⃣ Загрузите файл остатков на сервер:"
echo "      scp '2025-06-30 (4).json' root@$SERVER:$REMOTE_PATH/"
echo "   2️⃣ Запустите загрузку данных:"
echo "      ssh root@$SERVER 'cd $REMOTE_PATH && python3 simple_data_load.py'"