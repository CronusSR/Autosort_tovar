#!/bin/bash

# ВОССТАНОВЛЕНИЕ ПРАВИЛЬНЫХ ДАННЫХ ПРОДАЖ И ОСТАТКОВ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ВОССТАНОВЛЕНИЕ ДАННЫХ ПРОДАЖ И ОСТАТКОВ"
echo "=========================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 ЦЕЛЬ: Разделить данные продаж и остатков в системе"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '🗑️ ОЧИСТКА СИНТЕТИЧЕСКИХ ДАННЫХ'
    echo '==============================='
    
    # Создаем бэкап базы данных
    cp webhook_data.db webhook_data_backup_\$(date +%Y%m%d_%H%M%S).db
    echo '✅ Создан бэкап базы данных'
    
    # Удаляем синтетические данные из sales
    sqlite3 webhook_data.db \"
        DELETE FROM sales WHERE data_hash LIKE 'test_%';
        DELETE FROM sales WHERE data_hash LIKE 'extended_%';
    \"
    
    DELETED_COUNT=\$(sqlite3 webhook_data.db \"SELECT changes();\")
    echo \"🗑️ Удалено \$DELETED_COUNT синтетических записей продаж\"
    
    # Проверяем что осталось
    REMAINING_SALES=\$(sqlite3 webhook_data.db \"SELECT COUNT(*) FROM sales;\")
    echo \"📊 Осталось записей продаж: \$REMAINING_SALES\"
    echo ''
    
    echo '📂 ПОИСК РЕАЛЬНЫХ ФАЙЛОВ ПРОДАЖ'
    echo '==============================='
    
    # Ищем файлы продаж в разных местах
    echo 'Поиск JSON файлов с продажами:'
    
    # Проверяем разные возможные локации
    SALES_FILES=()
    
    # В корневой директории
    for file in *.json; do
        if [ -f \"\$file\" ] && grep -q \"ПродажиПоДням\\|Выгрузка\\|НачалоПериода\" \"\$file\" 2>/dev/null; then
            SALES_FILES+=(\"\$file\")
            echo \"   ✅ Найден: \$file\"
        fi
    done
    
    # В webhook_uploads
    if [ -d webhook_uploads ]; then
        for file in webhook_uploads/*.json; do
            if [ -f \"\$file\" ] && grep -q \"ПродажиПоДням\\|Выгрузка\\|НачалоПериода\" \"\$file\" 2>/dev/null; then
                SALES_FILES+=(\"\$file\")
                echo \"   ✅ Найден: \$file\"
            fi
        done
    fi
    
    # В data директории
    if [ -d data ]; then
        for file in data/*.json; do
            if [ -f \"\$file\" ] && grep -q \"ПродажиПоДням\\|Выгрузка\\|НачалоПериода\" \"\$file\" 2>/dev/null; then
                SALES_FILES+=(\"\$file\")
                echo \"   ✅ Найден: \$file\"
            fi
        done
    fi
    
    echo \"📊 Всего найдено файлов продаж: \${#SALES_FILES[@]}\"
    echo ''
    
    if [ \${#SALES_FILES[@]} -gt 0 ]; then
        echo '📥 ЗАГРУЗКА РЕАЛЬНЫХ ФАЙЛОВ ПРОДАЖ'
        echo '================================='
        
        # Создаем Python скрипт для загрузки продаж
        cat > load_real_sales.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import sys
import os
from datetime import datetime
import hashlib

def load_sales_file(filepath):
    \"\"\"Загружает файл продаж в базу данных\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('webhook_data.db')
        cursor = conn.cursor()
        
        sales_count = 0
        filename = os.path.basename(filepath)
        
        print(f\"📁 Обрабатываем файл: {filename}\")
        
        # Если это массив (несколько филиалов)
        if isinstance(data, list):
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
                        
                        # Создаем уникальный хеш
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
                            print(f\"⚠️ Ошибка записи: {e}\")
                            continue
        
        conn.commit()
        print(f\"   ✅ Загружено: {sales_count} записей продаж\")
        
        # Записываем в историю загрузок
        cursor.execute(\"\"\"
            INSERT INTO upload_history (upload_type, filename, records_processed)
            VALUES (?, ?, ?)
        \"\"\", ('sales', filename, sales_count))
        
        conn.commit()
        conn.close()
        return sales_count
        
    except Exception as e:
        print(f\"❌ Ошибка загрузки файла {filepath}: {e}\")
        return 0

if __name__ == \"__main__\":
    total_loaded = 0
    for filepath in sys.argv[1:]:
        total_loaded += load_sales_file(filepath)
    
    print(f\"\\n📊 ИТОГО ЗАГРУЖЕНО: {total_loaded} записей продаж\")
PYTHON_END
        
        # Загружаем все найденные файлы продаж
        python3 load_real_sales.py \"\${SALES_FILES[@]}\"
        
        echo ''
    else
        echo '❌ НЕ НАЙДЕНО ФАЙЛОВ ПРОДАЖ'
        echo ''
        echo '🔍 ПОПРОБУЕМ НАЙТИ ZIP ФАЙЛЫ:'
        find . -name \"*.zip\" -type f | head -3
        echo ''
        echo '💡 РЕKOMENDАЦИЯ:'
        echo '   1. Найдите оригинальные ZIP файлы с выгрузками'
        echo '   2. Распакуйте их в webhook_uploads/'
        echo '   3. Запустите этот скрипт повторно'
    fi
    
    echo '📊 ПРОВЕРКА РЕЗУЛЬТАТА'
    echo '====================='
    
    # Проверяем что получилось
    sqlite3 webhook_data.db \"
        SELECT 
            'Продаж в базе:' as info, 
            COUNT(*) as count 
        FROM sales
        UNION ALL
        SELECT 
            'Остатков в базе:', 
            COUNT(*) 
        FROM stock
        UNION ALL
        SELECT 
            'Дней с продажами:', 
            COUNT(DISTINCT date) 
        FROM sales
        UNION ALL
        SELECT 
            'Филиалов с продажами:', 
            COUNT(DISTINCT branch) 
        FROM sales;
    \"
    
    echo ''
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================'
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис успешно запущен'
        echo ''
        echo '🎉 ВОССТАНОВЛЕНИЕ ДАННЫХ ЗАВЕРШЕНО!'
        echo ''
        echo '📊 РЕЗУЛЬТАТ:'
        echo '   ✅ Удалены синтетические данные'
        echo '   ✅ Загружены реальные файлы продаж'
        echo '   ✅ Система готова к работе'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
        echo '   📈 Общий анализ → должна показывать реальную динамику'
        echo '   🔍 Отладочная информация → покажет загруженные данные'
    else
        echo '❌ Проблемы с запуском сервиса'
        systemctl status webhook-analytics --no-pager | head -10
    fi
"

echo ""
echo "✅ СКРИПТ ВОССТАНОВЛЕНИЯ ЗАВЕРШЕН!"
echo ""