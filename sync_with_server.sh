#!/bin/bash
# Скрипт для синхронизации файлов между локальной папкой и SSH сервером

echo "🔄 Синхронизация с SSH сервером"
echo "================================"

# Параметр: up (на сервер) или down (с сервера)
DIRECTION=${1:-"down"}

case $DIRECTION in
    "up")
        echo "📤 Отправка файлов НА сервер..."
        
        # Отправляем основные файлы
        if [ -f "webhook_receiver.py" ]; then
            echo "📋 Отправляем webhook_receiver.py..."
            scp webhook_receiver.py root@217.114.1.117:/opt/inventory_system/
        fi
        
        if [ -f "webhook_persistent_app.py" ]; then
            echo "📋 Отправляем webhook_persistent_app.py..."
            scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/
        fi
        
        if [ -f "webhook_data_accumulator.py" ]; then
            echo "📋 Отправляем webhook_data_accumulator.py..."
            scp webhook_data_accumulator.py root@217.114.1.117:/opt/inventory_system/
        fi
        
        if [ -f "requirements.txt" ]; then
            echo "📋 Отправляем requirements.txt..."
            scp requirements.txt root@217.114.1.117:/opt/inventory_system/
        fi
        
        echo "✅ Файлы отправлены на сервер"
        
        # Перезапускаем сервисы
        echo "🔄 Перезапускаем сервисы на сервере..."
        ssh root@217.114.1.117 << 'RESTART_EOF'
cd /opt/inventory_system
pkill -f webhook_receiver
sleep 2
nohup python3 webhook_receiver.py > webhook_5000.log 2>&1 &
echo "Webhook сервер перезапущен с PID: $!"
RESTART_EOF
        ;;
        
    "down")
        echo "📥 Загрузка файлов С сервера..."
        
        # Создаем папку для загрузки
        mkdir -p ssh_sync
        
        # Загружаем основные файлы
        echo "📋 Загружаем основные файлы..."
        scp root@217.114.1.117:/opt/inventory_system/webhook_receiver.py ./ssh_sync/
        scp root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py ./ssh_sync/
        scp root@217.114.1.117:/opt/inventory_system/webhook_data_accumulator.py ./ssh_sync/
        scp root@217.114.1.117:/opt/inventory_system/requirements.txt ./ssh_sync/
        
        # Загружаем логи
        echo "📋 Загружаем логи..."
        scp root@217.114.1.117:/opt/inventory_system/webhook_5000.log ./ssh_sync/ 2>/dev/null || echo "webhook_5000.log не найден"
        scp root@217.114.1.117:/opt/inventory_system/webhook_8502.log ./ssh_sync/ 2>/dev/null || echo "webhook_8502.log не найден"
        scp root@217.114.1.117:/opt/inventory_system/webhook.log ./ssh_sync/ 2>/dev/null || echo "webhook.log не найден"
        
        # Загружаем backup файлы (последние)
        echo "📋 Загружаем последние backup файлы..."
        ssh root@217.114.1.117 "cd /opt/inventory_system && ls -t webhook_*backup*.py | head -5" | while read backup_file; do
            if [ ! -z "$backup_file" ]; then
                scp "root@217.114.1.117:/opt/inventory_system/$backup_file" ./ssh_sync/ 2>/dev/null
            fi
        done
        
        # Получаем информацию о структуре
        echo "📋 Получаем информацию о структуре..."
        ssh root@217.114.1.117 "cd /opt/inventory_system && find webhook_uploads -type d 2>/dev/null" > ./ssh_sync/folder_structure.txt
        ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/ 2>/dev/null" > ./ssh_sync/uploads_listing.txt
        ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/sales/ 2>/dev/null" > ./ssh_sync/sales_listing.txt
        ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/stock/ 2>/dev/null" > ./ssh_sync/stock_listing.txt
        
        # Получаем статус процессов
        echo "📋 Получаем статус процессов..."
        ssh root@217.114.1.117 "ps aux | grep -E '(streamlit|webhook|python)' | grep -v grep" > ./ssh_sync/processes_status.txt
        ssh root@217.114.1.117 "netstat -tulpn | grep -E ':(5000|8502)'" > ./ssh_sync/ports_status.txt
        
        echo "✅ Файлы загружены в папку ssh_sync/"
        
        # Показываем что загружено
        echo ""
        echo "📊 Загруженные файлы:"
        ls -la ssh_sync/
        ;;
        
    "status")
        echo "📊 Статус синхронизации..."
        
        echo "🌐 Статус сервера:"
        ssh root@217.114.1.117 "cd /opt/inventory_system && echo 'Процессы:' && ps aux | grep -E '(streamlit|webhook)' | grep -v grep && echo '' && echo 'Порты:' && netstat -tulpn | grep -E ':(5000|8502)'"
        
        echo ""
        echo "📁 Структура папок на сервере:"
        ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/ 2>/dev/null && echo '' && echo 'Sales:' && ls -la webhook_uploads/sales/ 2>/dev/null && echo '' && echo 'Stock:' && ls -la webhook_uploads/stock/ 2>/dev/null"
        
        echo ""
        echo "🔗 Тест доступности:"
        curl -s -w "HTTP %{http_code} - %{time_total}s\n" -o /dev/null http://217.114.1.117:5000/webhook/status
        curl -s -w "HTTP %{http_code} - %{time_total}s\n" -o /dev/null http://217.114.1.117:8502
        ;;
        
    "test")
        echo "🧪 Тестирование системы..."
        
        echo "📋 Тестируем вебхук статус..."
        curl -s http://217.114.1.117:5000/webhook/status | python3 -m json.tool 2>/dev/null || curl -s http://217.114.1.117:5000/webhook/status
        
        echo ""
        echo "📋 Тестируем главную страницу..."
        curl -s http://217.114.1.117:5000/ | python3 -m json.tool 2>/dev/null || curl -s http://217.114.1.117:5000/
        ;;
        
    *)
        echo "❌ Неизвестный параметр: $DIRECTION"
        echo ""
        echo "Использование:"
        echo "  $0 up      - отправить файлы на сервер"
        echo "  $0 down    - загрузить файлы с сервера (по умолчанию)"
        echo "  $0 status  - показать статус сервера"
        echo "  $0 test    - протестировать API"
        exit 1
        ;;
esac

echo ""
echo "✅ Операция завершена!"
echo ""
echo "🔗 Полезные команды:"
echo "  ./sync_with_server.sh up     - отправить на сервер"
echo "  ./sync_with_server.sh down   - скачать с сервера"
echo "  ./sync_with_server.sh status - статус сервера"
echo "  ./sync_with_server.sh test   - тест API"