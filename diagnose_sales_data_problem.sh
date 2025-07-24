#!/bin/bash

# ДИАГНОСТИКА ПРОБЛЕМЫ С ДАННЫМИ ПРОДАЖ И ОСТАТКОВ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С ДАННЫМИ ПРОДАЖ"
echo "========================================"
echo "📅 Время: $(date)"
echo ""
echo "❓ ПРОБЛЕМА: Система использует только остатки вместо продаж и остатков"
echo "💡 ГИПОТЕЗА: Файлы с одинаковыми названиями перезаписали друг друга"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔍 АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ ДАННЫХ'
    echo '=================================='
    
    # Устанавливаем sqlite3 если его нет
    if ! command -v sqlite3 &> /dev/null; then
        echo 'Установка sqlite3...'
        apt-get update -qq && apt-get install -y sqlite3 -qq
    fi
    
    # Проверяем данные в таблице sales
    echo '1️⃣ ДАННЫЕ В ТАБЛИЦЕ SALES:'
    echo '-------------------------'
    sqlite3 webhook_data.db \"
        SELECT 
            'Всего записей в sales:' as info, 
            COUNT(*) as value 
        FROM sales
        UNION ALL
        SELECT 
            'Уникальных дат:', 
            COUNT(DISTINCT date) 
        FROM sales
        UNION ALL
        SELECT 
            'Период данных:', 
            MIN(date) || ' - ' || MAX(date) 
        FROM sales
        UNION ALL
        SELECT 
            'Уникальных филиалов:', 
            COUNT(DISTINCT branch) 
        FROM sales;
    \"
    echo ''
    
    # Проверяем данные в таблице stock  
    echo '2️⃣ ДАННЫЕ В ТАБЛИЦЕ STOCK:'
    echo '-------------------------'
    sqlite3 webhook_data.db \"
        SELECT 
            'Всего записей в stock:' as info, 
            COUNT(*) as value 
        FROM stock
        UNION ALL
        SELECT 
            'Уникальных дат:', 
            COUNT(DISTINCT date) 
        FROM stock
        UNION ALL
        SELECT 
            'Период данных:', 
            MIN(date) || ' - ' || MAX(date) 
        FROM stock
        UNION ALL
        SELECT 
            'Уникальных складов:', 
            COUNT(DISTINCT warehouse) 
        FROM stock;
    \"
    echo ''
    
    # Проверяем структуру данных в sales - похоже ли на продажи или остатки?
    echo '3️⃣ АНАЛИЗ СТРУКТУРЫ ДАННЫХ В SALES:'
    echo '---------------------------------'
    sqlite3 webhook_data.db \"
        SELECT 
            'Примеры записей sales (первые 5):' as info;
            
        SELECT 
            date, branch, item_name, quantity, amount, data_hash
        FROM sales 
        LIMIT 5;
    \"
    echo ''
    
    # Проверяем есть ли реальные файлы продаж в webhook_uploads
    echo '4️⃣ ФАЙЛЫ В ДИРЕКТОРИИ WEBHOOK_UPLOADS:'
    echo '------------------------------------'
    if [ -d webhook_uploads ]; then
        echo 'Файлы в webhook_uploads:'
        ls -la webhook_uploads/ | head -10
        echo ''
        
        # Проверяем есть ли JSON файлы
        echo 'JSON файлы в webhook_uploads:'
        find webhook_uploads/ -name \"*.json\" -type f | head -5
        echo ''
    else
        echo '❌ Директория webhook_uploads не найдена'
    fi
    
    # Проверяем историю загрузок
    echo '5️⃣ ИСТОРИЯ ЗАГРУЗОК:'
    echo '-------------------'
    sqlite3 webhook_data.db \"
        SELECT 
            upload_type, 
            filename, 
            records_processed, 
            upload_time 
        FROM upload_history 
        ORDER BY upload_time DESC 
        LIMIT 10;
    \"
    echo ''
    
    # Проверяем data_hash в sales - если все начинается с 'test_' то это синтетические данные
    echo '6️⃣ АНАЛИЗ ТИПА ДАННЫХ (РЕАЛЬНЫЕ ИЛИ СИНТЕТИЧЕСКИЕ):'
    echo '-------------------------------------------------'
    sqlite3 webhook_data.db \"
        SELECT 
            CASE 
                WHEN data_hash LIKE 'test_%' THEN 'Синтетические (test_)'
                WHEN data_hash LIKE 'real_%' THEN 'Реальные (real_)'
                WHEN data_hash LIKE 'extended_%' THEN 'Расширенные (extended_)'
                ELSE 'Другие'
            END as data_type,
            COUNT(*) as count
        FROM sales 
        GROUP BY 
            CASE 
                WHEN data_hash LIKE 'test_%' THEN 'Синтетические (test_)'
                WHEN data_hash LIKE 'real_%' THEN 'Реальные (real_)'
                WHEN data_hash LIKE 'extended_%' THEN 'Расширенные (extended_)'
                ELSE 'Другие'
            END
        ORDER BY count DESC;
    \"
    echo ''
    
    # Проверяем есть ли файлы с реальными продажами
    echo '7️⃣ ПОИСК ФАЙЛОВ ПРОДАЖ:'
    echo '----------------------'
    echo 'Поиск JSON файлов со структурой продаж:'
    find . -name \"*.json\" -type f -exec grep -l \"ПродажиПоДням\\|Выгрузка\\|НачалоПериода\" {} \\; 2>/dev/null | head -5
    echo ''
    
    echo '8️⃣ ПОИСК ZIP ФАЙЛОВ ПРОДАЖ:'
    echo '---------------------------'
    find . -name \"*.zip\" -type f | head -5
    echo ''
"

echo ""
echo "📋 СОЗДАНИЕ ПЛАНА ВОССТАНОВЛЕНИЯ..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '📋 ПЛАН ВОССТАНОВЛЕНИЯ ДАННЫХ'
    echo '============================='
    echo ''
    echo 'На основе диагностики определяем:'
    echo ''
    
    # Подсчитываем синтетические данные
    SYNTHETIC_COUNT=\$(sqlite3 webhook_data.db \"SELECT COUNT(*) FROM sales WHERE data_hash LIKE 'test_%' OR data_hash LIKE 'extended_%';\")
    REAL_COUNT=\$(sqlite3 webhook_data.db \"SELECT COUNT(*) FROM sales WHERE data_hash LIKE 'real_%';\")
    
    echo \"📊 ТЕКУЩЕЕ СОСТОЯНИЕ:\"
    echo \"   🤖 Синтетических записей: \$SYNTHETIC_COUNT\"
    echo \"   📈 Реальных записей: \$REAL_COUNT\"
    echo \"\"
    
    if [ \$SYNTHETIC_COUNT -gt \$REAL_COUNT ]; then
        echo \"❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА: Больше синтетических данных чем реальных\"
        echo \"\"
        echo \"🔧 ПЛАН ДЕЙСТВИЙ:\"
        echo \"   1️⃣ Найти оригинальные файлы продаж\"
        echo \"   2️⃣ Очистить синтетические данные\"
        echo \"   3️⃣ Загрузить реальные файлы продаж\"
        echo \"   4️⃣ Обновить остатки из правильного файла\"
        echo \"   5️⃣ Настроить систему для корректной работы\"
    else
        echo \"✅ Данные выглядят корректно\"
    fi
"

echo ""
echo "✅ ДИАГНОСТИКА ЗАВЕРШЕНА!"
echo ""
echo "🎯 СЛЕДУЮЩИЕ ШАГИ:"
echo "   1. Проанализируйте результаты диагностики"
echo "   2. Если проблема подтверждена - запустите скрипт восстановления"
echo "   3. Найдите оригинальные файлы продаж для восстановления"
echo ""