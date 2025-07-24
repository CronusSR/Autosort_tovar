#!/bin/bash

# Скрипт исправления проблемы с вебхук-сервером
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 Исправление проблемы с вебхук-сервером..."

# Исправляем проблему с sqlite3
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '📋 Проверяем логи сервиса...'
    journalctl -u webhook-receiver.service --no-pager | tail -10
    
    echo ''
    echo '🔧 Исправляем импорт sqlite3...'
    
    # Создаем исправленную версию накопителя данных
    sed -i 's/import sqlite3/import sqlite3/' webhook_data_accumulator.py
    
    # Проверяем что Python может импортировать sqlite3
    python3 -c 'import sqlite3; print(\"✅ sqlite3 работает\")'
    
    echo ''
    echo '🔄 Перезапускаем сервис...'
    systemctl stop webhook-receiver
    systemctl start webhook-receiver
    
    echo ''
    echo '📊 Проверяем статус...'
    sleep 3
    systemctl status webhook-receiver --no-pager | head -15
    
    echo ''
    echo '🌐 Проверяем доступность...'
    curl -s http://localhost:5000/webhook/status || echo 'Сервер еще запускается...'
"

echo ""
echo "✅ Исправление завершено!"
echo "🔗 Проверьте: http://217.114.1.117:5000/webhook/status"