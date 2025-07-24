#!/bin/bash

# ПОЛНАЯ ПЕРЕЗАГРУЗКА ДАННЫХ ИЗ ZIP ФАЙЛА
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔄 ПОЛНАЯ ПЕРЕЗАГРУЗКА ДАННЫХ ИЗ ZIP"
echo "==================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 ПЛАН:"
echo "   1️⃣ Остановить сервис"
echo "   2️⃣ Очистить все данные продаж"
echo "   3️⃣ Найти и распаковать 'Выгрузка JSON.zip'"
echo "   4️⃣ Загрузить все файлы продаж заново"
echo "   5️⃣ Обновить остатки из правильного файла"
echo "   6️⃣ Запустить сервис"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '💾 СОЗДАНИЕ БЭКАПА'
    echo '=================='
    cp webhook_data.db webhook_data_backup_full_\$(date +%Y%m%d_%H%M%S).db
    echo '✅ Создан полный бэкап базы данных'
    echo ''
    
    echo '🗑️ ОЧИСТКА ТЕКУЩИХ ДАННЫХ'
    echo '========================='
    
    # Очищаем таблицы
    sqlite3 webhook_data.db \"
        DELETE FROM sales;
        DELETE FROM stock;  
        DELETE FROM upload_history;
    \"
    
    echo '✅ Очищены таблицы: sales, stock, upload_history'
    echo ''
    
    echo '📂 ПОИСК ZIP ФАЙЛА С ВЫГРУЗКОЙ'
    echo '=============================='
    
    # Ищем ZIP файл с выгрузкой
    ZIP_FILE=\$(find . -name \"*выгрузка*json*.zip\" -o -name \"*Выгрузка*JSON*.zip\" -o -name \"*ВЫГРУЗКА*JSON*.zip\" 2>/dev/null | head -1)
    
    if [ -z \"\$ZIP_FILE\" ]; then
        echo '⚠️ Не найден ZIP файл \"Выгрузка JSON.zip\"'
        echo ''
        echo '🔍 Ищем другие ZIP файлы:'
        find . -name \"*.zip\" -type f | head -5
        echo ''
        echo '💡 Попробуем использовать существующие JSON файлы из webhook_uploads/'
        
        # Используем существующие файлы
        JSON_FILES=(\$(find webhook_uploads/ -name \"*.json\" 2>/dev/null))
        
    else
        echo \"✅ Найден ZIP файл: \$ZIP_FILE\"
        
        # Создаем временную директорию для распаковки
        mkdir -p temp_extract
        
        echo '📦 Распаковка ZIP файла...'
        unzip -q \"\$ZIP_FILE\" -d temp_extract/
        
        if [ \$? -eq 0 ]; then
            echo '✅ ZIP файл успешно распакован'
            
            # Перемещаем JSON файлы в webhook_uploads
            mkdir -p webhook_uploads
            find temp_extract/ -name \"*.json\" -exec mv {} webhook_uploads/ \\;
            
            # Удаляем временную директорию
            rm -rf temp_extract/
            
            echo '✅ JSON файлы перемещены в webhook_uploads/'
        else
            echo '❌ Ошибка распаковки ZIP файла'
        fi
        
        # Получаем список JSON файлов
        JSON_FILES=(\$(find webhook_uploads/ -name \"*.json\" 2>/dev/null))
    fi
    
    echo ''
    echo \"📊 Найдено JSON файлов: \${#JSON_FILES[@]}\"
    echo ''
    
    if [ \${#JSON_FILES[@]} -gt 0 ]; then
        echo '📥 ЗАГРУЗКА ВСЕХ ФАЙЛОВ ПРОДАЖ'
        echo '============================='
        
        # Создаем улучшенный скрипт загрузки
        cat > load_all_sales.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import sys
import os
from datetime import datetime
import hashlib

def is_sales_file(filepath):
    \"\"\"Проверяет, является ли файл файлом продаж\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read(1000)  # Читаем первые 1000 символов
            return any(keyword in content for keyword in ['ПродажиПоДням', 'Выгрузка', 'НачалоПериода', 'Продажи'])
    except:
        return False

def is_stock_file(filepath):
    \"\"\"Проверяет, является ли файл файлом остатков\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read(1000)
            return any(keyword in content for keyword in ['ОстаткиПоСкладам', 'ДатаОстатков'])
    except:
        return False

def load_sales_file(filepath):
    \"\"\"Загружает файл продаж\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('webhook_data.db')
        cursor = conn.cursor()
        
        sales_count = 0
        filename = os.path.basename(filepath)
        
        print(f\"📁 Загружаем продажи: {filename}\")
        
        # Определяем структуру файла
        if isinstance(data, list):
            # Массив филиалов
            for branch_data in data:
                branch_name = branch_data.get('Филиал', '')
                sales_data = branch_data.get('Продажи', [])
                
                for day_data in sales_data:
                    date = day_data.get('День', '')
                    daily_sales = day_data.get('ПродажиПоДням', [])
                    
                    for item in daily_sales:
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
                        
                        # Уникальный хеш
                        data_hash = f\"webhook_{date}_{branch_name}_{item.get('Артикул', '')}_{filename}\"
                        
                        try:
                            cursor.execute(\"\"\"
                                INSERT OR REPLACE INTO sales 
                                (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            \"\"\", (
                                date, branch_name, item.get('Артикул', ''),
                                item.get('Номенклатура', ''), 
                                float(item.get('Количество', 0)),
                                float(item.get('Выручка', 0)),
                                category, category_path, data_hash
                            ))
                            sales_count += 1
                        except Exception as e:
                            continue
        
        conn.commit()
        
        # Записываем в историю
        cursor.execute(\"\"\"
            INSERT INTO upload_history (upload_type, filename, records_processed)
            VALUES (?, ?, ?)
        \"\"\", ('sales', filename, sales_count))
        
        conn.commit()
        conn.close()
        
        print(f\"   ✅ Загружено: {sales_count} записей\")
        return sales_count
        
    except Exception as e:
        print(f\"   ❌ Ошибка: {e}\")
        return 0

def load_stock_file(filepath):
    \"\"\"Загружает файл остатков\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('webhook_data.db')
        cursor = conn.cursor()
        
        stock_count = 0
        filename = os.path.basename(filepath)
        
        print(f\"📦 Загружаем остатки: {filename}\")
        
        # Очищаем старые остатки
        cursor.execute('DELETE FROM stock')
        
        stock_date = data.get('ДатаОстатков', '').split('T')[0]
        
        for warehouse_data in data.get('ОстаткиПоСкладам', []):
            warehouse = warehouse_data.get('Склад', '')
            
            for item in warehouse_data.get('Остатки', []):
                try:
                    qty = float(item.get('Количество', 0))
                    cost = float(item.get('Стоимость', 0))
                    if qty > 0:
                        price = cost / qty
                        
                        cursor.execute(\"\"\"
                            INSERT OR REPLACE INTO stock 
                            (date, warehouse, item_code, item_name, quantity, price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        \"\"\", (
                            stock_date, warehouse, item.get('Артикул', ''),
                            item.get('Номенклатура', ''), qty, price
                        ))
                        stock_count += 1
                except:
                    continue
        
        conn.commit()
        
        # Записываем в историю
        cursor.execute(\"\"\"
            INSERT INTO upload_history (upload_type, filename, records_processed)
            VALUES (?, ?, ?)
        \"\"\", ('stock', filename, stock_count))
        
        conn.commit()
        conn.close()
        
        print(f\"   ✅ Загружено: {stock_count} записей\")
        return stock_count
        
    except Exception as e:
        print(f\"   ❌ Ошибка: {e}\")
        return 0

if __name__ == \"__main__\":
    total_sales = 0
    total_stock = 0
    
    print(\"🔍 Анализируем и загружаем файлы...\")
    print(\"=\" * 40)
    
    for filepath in sys.argv[1:]:
        if is_sales_file(filepath):
            total_sales += load_sales_file(filepath)
        elif is_stock_file(filepath):
            total_stock += load_stock_file(filepath)
        else:
            print(f\"⚠️ Неизвестный тип файла: {os.path.basename(filepath)}\")
    
    print(\"\\n📊 ИТОГО ЗАГРУЖЕНО:\")
    print(f\"   💰 Продаж: {total_sales} записей\")
    print(f\"   📦 Остатков: {total_stock} записей\")
PYTHON_END
        
        # Загружаем все файлы
        python3 load_all_sales.py \"\${JSON_FILES[@]}\"
        
        echo ''
        echo '📊 ПРОВЕРКА РЕЗУЛЬТАТА'
        echo '====================='
        
        sqlite3 webhook_data.db \"
            SELECT 'Продаж загружено:' as info, COUNT(*) as count FROM sales
            UNION ALL
            SELECT 'Остатков загружено:', COUNT(*) FROM stock  
            UNION ALL
            SELECT 'Период продаж:', MIN(date) || ' - ' || MAX(date) FROM sales
            UNION ALL
            SELECT 'Уникальных филиалов:', COUNT(DISTINCT branch) FROM sales
            UNION ALL
            SELECT 'Уникальных товаров:', COUNT(DISTINCT item_code) FROM sales;
        \"
        
    else
        echo '❌ НЕ НАЙДЕНО JSON ФАЙЛОВ'
        echo 'Проверьте наличие файлов продаж'
    fi
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================'
    
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис успешно запущен'
        echo ''
        echo '🎉 ПОЛНАЯ ПЕРЕЗАГРУЗКА ЗАВЕРШЕНА!'
        echo ''
        echo '📊 РЕЗУЛЬТАТ:'
        echo '   🗑️ Очищены все старые данные'
        echo '   📦 Загружены файлы из ZIP архива'
        echo '   💰 Восстановлены реальные продажи'  
        echo '   📈 Система готова к анализу'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
        echo '   📊 Общий анализ → полная динамика продаж'
        echo '   🔍 Отладочная информация → новые данные'
        echo '   📅 Разные периоды → реальные тренды'
    else
        echo '❌ Проблемы с запуском сервиса'
        systemctl status webhook-analytics --no-pager | head -10
    fi
    
    # Очищаем временные файлы
    rm -f load_all_sales.py
"

echo ""
echo "✅ СКРИПТ ПОЛНОЙ ПЕРЕЗАГРУЗКИ ЗАВЕРШЕН!"
echo ""
echo "🎯 СЛЕДУЮЩИЕ ШАГИ:"
echo "   1. Проверьте результаты загрузки"
echo "   2. Откройте систему и проверьте динамику продаж"
echo "   3. Убедитесь что период анализа работает корректно"
echo ""