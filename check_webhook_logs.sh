#!/bin/bash

# Проверка логов и состояния webhook
SERVER="217.114.1.117"
USER="root"

echo "🔍 ДИАГНОСТИКА WEBHOOK СЕРВЕРА"
echo "📅 Время: $(date)"
echo ""

echo "📋 Проверка состояния webhook сервиса:"
ssh "$USER@$SERVER" "
    echo '=== Статус сервиса ==='
    systemctl status webhook-receiver --no-pager | head -15
    
    echo ''
    echo '=== Последние логи webhook.log ==='
    tail -20 /opt/inventory_system/webhook.log 2>/dev/null || echo 'Лог файл не найден'
    
    echo ''
    echo '=== Системные логи сервиса ==='
    journalctl -u webhook-receiver -n 20 --no-pager
    
    echo ''
    echo '=== Проверка процесса ==='
    ps aux | grep webhook_receiver | grep -v grep
    
    echo ''
    echo '=== Использование памяти ==='
    free -h
    
    echo ''
    echo '=== Место на диске ==='
    df -h /opt/inventory_system
"

echo ""
echo "🔧 Проверка настроек Flask:"
ssh "$USER@$SERVER" "
    cd /opt/inventory_system
    grep -i 'max_content_length\\|timeout' webhook_receiver.py 2>/dev/null || echo 'Лимиты не установлены'
"