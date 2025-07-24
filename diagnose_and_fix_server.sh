#!/bin/bash

# ДИАГНОСТИКА И ИСПРАВЛЕНИЕ СИСТЕМЫ НА СЕРВЕРЕ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔍 ДИАГНОСТИКА И ИСПРАВЛЕНИЕ СИСТЕМЫ"
echo "===================================="
echo "📅 Время: $(date)"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔍 ДИАГНОСТИКА СИСТЕМЫ'
    echo '======================'
    
    # Проверяем текущий статус сервиса
    echo '1️⃣ Статус сервиса:'
    systemctl status webhook-analytics --no-pager | head -3
    echo ''
    
    # Проверяем синтаксис текущего файла
    echo '2️⃣ Проверка синтаксиса webhook_persistent_app.py:'
    python3 -m py_compile webhook_persistent_app.py 2>&1
    if [ \$? -eq 0 ]; then
        echo '✅ Синтаксис корректный'
    else
        echo '❌ Есть синтаксические ошибки'
    fi
    echo ''
    
    # Проверяем размер и дату файла
    echo '3️⃣ Информация о файле:'
    ls -la webhook_persistent_app.py
    echo ''
    
    # Проверяем базу данных
    echo '4️⃣ Данные в базе:'
    sqlite3 webhook_data.db \"
        SELECT 'Продаж:' as type, COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date FROM sales
        UNION ALL
        SELECT 'Остатков:', COUNT(*), MIN(date), MAX(date) FROM stock;
    \"
    echo ''
    
    # Проверяем логи
    echo '5️⃣ Последние ошибки в логах:'
    if [ -f webhook.log ]; then
        tail -10 webhook.log | grep -i error || echo 'Нет ошибок в webhook.log'
    fi
    
    if [ -f streamlit.log ]; then
        tail -10 streamlit.log | grep -i error || echo 'Нет ошибок в streamlit.log'
    fi
    echo ''
    
    # Проверяем процессы
    echo '6️⃣ Активные процессы:'
    ps aux | grep -E '(streamlit|python.*webhook)' | grep -v grep || echo 'Нет активных процессов'
    echo ''
"

echo ""
echo "📤 ЗАГРУЗКА ИСПРАВЛЕННОГО ФАЙЛА..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app_fixed.py"

if [ $? -ne 0 ]; then
    echo "❌ Ошибка загрузки файла"
    exit 1
fi

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔧 ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ'
    echo '========================='
    
    # Проверяем синтаксис нового файла
    echo '1️⃣ Проверка синтаксиса исправленного файла:'
    python3 -m py_compile webhook_persistent_app_fixed.py 2>&1
    
    if [ \$? -eq 0 ]; then
        echo '✅ Синтаксис исправленного файла корректный'
        
        # Создаем бэкап текущего файла
        echo '2️⃣ Создание бэкапа текущего файла...'
        cp webhook_persistent_app.py webhook_persistent_app_backup_\$(date +%Y%m%d_%H%M%S).py
        
        # Заменяем файл
        echo '3️⃣ Замена файла...'
        mv webhook_persistent_app_fixed.py webhook_persistent_app.py
        
        # Перезапускаем сервис
        echo '4️⃣ Перезапуск сервиса...'
        systemctl stop webhook-analytics
        sleep 2
        systemctl start webhook-analytics
        sleep 5
        
        # Проверяем статус
        if systemctl is-active --quiet webhook-analytics; then
            echo '✅ Сервис успешно запущен'
            echo ''
            echo '🎉 ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!'
            echo ''
            echo '📊 ЧТО ИСПРАВЛЕНО:'
            echo '   ✅ Синтаксическая ошибка устранена'
            echo '   ✅ Логика периодов использует реальные даты из БД'
            echo '   ✅ Добавлена отладочная информация'
            echo '   ✅ Улучшено отображение динамики продаж'
            echo ''
            echo '🌐 Система готова: http://217.114.1.117:8502'
            echo ''
            echo '🔍 ДЛЯ ПРОВЕРКИ:'
            echo '   1. Откройте вкладку \"📊 Общий анализ\"'
            echo '   2. Выберите разные периоды анализа'
            echo '   3. Проверьте раздел \"🔍 Отладочная информация\"'
            echo '   4. Убедитесь что динамика продаж показывает реальные данные'
        else
            echo '❌ Проблемы с запуском сервиса'
            echo 'Статус сервиса:'
            systemctl status webhook-analytics --no-pager | head -10
            
            echo ''
            echo 'Последние строки лога:'
            journalctl -u webhook-analytics --no-pager | tail -10
        fi
    else
        echo '❌ Ошибка синтаксиса в исправленном файле'
        echo 'Исправленный файл не будет применен'
        rm -f webhook_persistent_app_fixed.py
    fi
"

echo ""
echo "✅ ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ЗАВЕРШЕНЫ!"
echo ""