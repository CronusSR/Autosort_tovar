#!/bin/bash

# Быстрое исправление синтаксической ошибки
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ"
echo "📅 Время: $(date)"
echo ""

# Загружаем исправленный файл
echo "📤 Загрузка исправленного файла..."

scp webhook_app_enhanced_analytics.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    exit 1
}

echo "✅ Файл загружен"

# Перезапускаем сервис
echo ""
echo "🔄 Перезапуск сервиса..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔄 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    sleep 3
    
    echo '🚀 Запуск исправленного сервиса...'
    systemctl start webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса...'
    systemctl status webhook-analytics --no-pager | head -10
"

# Проверка результата
echo ""
echo "🔍 Проверка исправления..."

sleep 10

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ СИНТАКСИЧЕСКАЯ ОШИБКА ИСПРАВЛЕНА!"
    echo ""
    echo "🌐 Приложение доступно: http://$SERVER:8502"
} || {
    echo "⚠️ Все еще есть проблемы, проверяем логи..."
    ssh "$USER@$SERVER" "
        echo '📝 Последние ошибки:'
        journalctl -u webhook-analytics --no-pager -n 15
    "
}

echo ""
echo "✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"