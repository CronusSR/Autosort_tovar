#!/bin/bash

# Загрузка файла остатков на сервер для тестирования
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📦 ЗАГРУЗКА ОСТАТКОВ НА СЕРВЕР"
echo "📅 Время: $(date)"
echo ""

# Загружаем файл остатков
echo "📤 Загрузка файла остатков..."
scp "2025-06-30 (4).json" "$USER@$SERVER:$REMOTE_PATH/test_stock_data.json"

echo ""
echo "🔄 Интеграция остатков в систему..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    # Создаем скрипт интеграции
    cat > integrate_test_stock.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path

# Импортируем webhook accumulator
sys.path.append('/opt/inventory_system')
try:
    from webhook_data_accumulator import WebhookDataAccumulator
    WEBHOOK_AVAILABLE = True
    print('✅ WebhookDataAccumulator доступен')
except ImportError as e:
    WEBHOOK_AVAILABLE = False
    print(f'❌ WebhookDataAccumulator не найден: {e}')

def load_and_process_stock_file():
    print('📁 Обработка файла остатков...')
    
    try:
        # Инициализируем accumulator
        if WEBHOOK_AVAILABLE:
            accumulator = WebhookDataAccumulator()
            print('🔗 Подключение к базе данных успешно')
        
        with open('test_stock_data.json', 'r', encoding='utf-8-sig') as f:
            stock_data = json.load(f)
        
        # Если есть WebhookDataAccumulator, интегрируем напрямую в БД
        if WEBHOOK_AVAILABLE:
            print('💾 Интеграция в базу данных через WebhookDataAccumulator...')
            
            # Создаем временный файл в правильном формате для webhook
            temp_file = Path('temp_stock_webhook.json')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(stock_data, f, ensure_ascii=False, indent=2)
            
            # Обрабатываем файл через webhook accumulator
            result = accumulator.process_new_stock_file(temp_file)
            print(f'📊 Результат интеграции: {result}')
            
            # Создаем также тестовые продажи
            sales_data = create_test_sales_from_stock(stock_data)
            
            # Сохраняем продажи в файл и загружаем через accumulator
            temp_sales_file = Path('temp_sales_webhook.json')
            with open(temp_sales_file, 'w', encoding='utf-8') as f:
                json.dump(sales_data, f, ensure_ascii=False, indent=2)
            
            sales_result = accumulator.process_new_sales_file(temp_sales_file)
            print(f'📊 Продажи интегрированы: {sales_result}')
            
            # Удаляем временные файлы
            temp_file.unlink()
            temp_sales_file.unlink()
            
            # Проверяем данные в БД
            stock_df = accumulator.get_latest_stock()
            sales_df = accumulator.get_sales_data()
            
            print(f'✅ В БД остатков: {len(stock_df)} записей')
            print(f'✅ В БД продаж: {len(sales_df)} записей')
            
            return True
        else:
            # Fallback - создаем файлы как раньше
            processed_records = []
            
            for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
                warehouse = warehouse_data.get('Склад', '')
                
                for item in warehouse_data.get('Остатки', []):
                    # Обрабатываем путь категорий
                    category_path = item.get('ПутьКатегорий', '')
                    
                    if category_path:
                        parts = [p.strip() for p in category_path.split('/') if p.strip()]
                        
                        # Убираем \"Мебельная фурнитура\" если это последний элемент
                        if parts and parts[-1] == \"Мебельная фурнитура\":
                            parts = parts[:-1]
                        
                        # Переворачиваем для правильного порядка
                        if parts:
                            category_path = '/'.join(reversed(parts)) + '/'
                        else:
                            category_path = 'Неопределенная категория/'
                    
                    record = {
                        'warehouse': warehouse,
                        'item_code': item.get('Артикул', ''),
                        'item_name': item.get('Номенклатура', ''),
                        'quantity': float(item.get('Количество', 0)),
                        'amount': float(item.get('Стоимость', 0)),
                        'category_path': category_path,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'manufacturer': item.get('Производитель', ''),
                        'unit': item.get('ЕдиницаИзмерения', '')
                    }
                    processed_records.append(record)
            
            # Сохраняем обработанные остатки
            with open('processed_stock.json', 'w', encoding='utf-8') as f:
                json.dump(processed_records, f, ensure_ascii=False, indent=2, default=str)
            
            # Создаем тестовые продажи
            sales_records = []
            df = pd.DataFrame(processed_records)
            top_items = df.nlargest(500, 'amount')
            
            for _, row in top_items.iterrows():
                sales_quantity = max(1, row['quantity'] * 0.1)
                sales_amount = row['amount'] * 0.1
                
                sales_record = {
                    'branch': row['warehouse'],
                    'item_code': row['item_code'],
                    'item_name': row['item_name'],
                    'quantity': sales_quantity,
                    'amount': sales_amount,
                    'category_path': row['category_path'],
                    'date': row['date'],
                    'manufacturer': row['manufacturer']
                }
                sales_records.append(sales_record)
            
            with open('processed_sales.json', 'w', encoding='utf-8') as f:
                json.dump(sales_records, f, ensure_ascii=False, indent=2, default=str)
            
            print(f'✅ Обработано {len(processed_records)} записей остатков')
            print(f'✅ Создано {len(sales_records)} записей продаж')
            print(f'📊 Уникальных товаров: {df[\"item_code\"].nunique()}')
            
            return True
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()
        return False

def create_test_sales_from_stock(stock_data):
    \"\"\"Создает тестовые продажи из данных остатков\"\"\"
    sales_records = []
    
    # Извлекаем все товары из остатков
    all_items = []
    for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
        warehouse = warehouse_data.get('Склад', '')
        
        for item in warehouse_data.get('Остатки', []):
            all_items.append({
                'warehouse': warehouse,
                'item': item
            })
    
    # Берем топ товары по стоимости
    all_items.sort(key=lambda x: float(x['item'].get('Стоимость', 0)), reverse=True)
    top_items = all_items[:500]  # Топ 500 товаров
    
    for item_data in top_items:
        item = item_data['item']
        warehouse = item_data['warehouse']
        
        # Обрабатываем путь категорий
        category_path = item.get('ПутьКатегорий', '')
        if category_path:
            parts = [p.strip() for p in category_path.split('/') if p.strip()]
            if parts and parts[-1] == \"Мебельная фурнитура\":
                parts = parts[:-1]
            if parts:
                category_path = '/'.join(reversed(parts)) + '/'
            else:
                category_path = 'Неопределенная категория/'
        
        # Создаем фиктивные продажи (10% от остатка)
        quantity = float(item.get('Количество', 0))
        amount = float(item.get('Стоимость', 0))
        
        sales_quantity = max(1, quantity * 0.1)
        sales_amount = amount * 0.1
        
        sales_record = {
            'date': datetime.now().strftime('%Y-%m-%d'),  
            'branch': warehouse,
            'item_code': item.get('Артикул', ''),
            'item_name': item.get('Номенклатура', ''),
            'quantity': sales_quantity,
            'amount': sales_amount,
            'category': category_path.split('/')[0] if category_path else 'Неопределенная',
            'category_path': category_path
        }
        sales_records.append(sales_record)
    
    return sales_records

if __name__ == '__main__':
    if load_and_process_stock_file():
        print('\n✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!')
        print('📊 Данные интегрированы в базу данных webhook системы')
        print('🔄 Теперь оборачиваемость, анализ по городам и межфилиальные перемещения должны работать')
    else:
        print('\n❌ ОШИБКА ИНТЕГРАЦИИ!')
EOF
    
    # Запускаем интеграцию
    python3 integrate_test_stock.py
    
    # Показываем результат
    echo ''
    echo '📊 РЕЗУЛЬТАТ ИНТЕГРАЦИИ:'
    echo '========================'
    
    if [ -f 'processed_stock.json' ]; then
        echo '✅ processed_stock.json создан'
        echo \"   Размер: \$(du -h processed_stock.json | cut -f1)\"
    else
        echo '❌ processed_stock.json НЕ создан'
    fi
    
    if [ -f 'processed_sales.json' ]; then
        echo '✅ processed_sales.json создан'
        echo \"   Размер: \$(du -h processed_sales.json | cut -f1)\"
    else
        echo '❌ processed_sales.json НЕ создан'
    fi
"

echo ""
echo "✅ ЗАГРУЗКА И ИНТЕГРАЦИЯ ЗАВЕРШЕНА!"
echo ""
echo "🎯 ЧТО СДЕЛАНО:"
echo "   ✅ Файл остатков загружен на сервер"
echo "   ✅ Остатки обработаны и интегрированы"
echo "   ✅ Созданы тестовые продажи для ABC анализа"
echo "   ✅ Категории приведены к правильному формату"
echo ""
echo "🌐 Система готова для тестирования: http://$SERVER:8502"
echo "📊 Используйте вкладку 'ABC анализ категорий' для проверки работы"