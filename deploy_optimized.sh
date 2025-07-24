#!/bin/bash

# Развертывание оптимизированной системы
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🚀 РАЗВЕРТЫВАНИЕ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка оптимизированной версии..."

scp webhook_persistent_app.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    exit 1
}

echo "✅ Файл загружен"

echo ""
echo "🔄 Перезапуск системы..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔄 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    sleep 3
    
    echo '🚀 Запуск оптимизированной системы...'
    systemctl start webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса...'
    systemctl status webhook-analytics --no-pager | head -10
"

echo ""
echo "🔍 Проверка работы..."

sleep 15

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ ОПТИМИЗИРОВАННАЯ СИСТЕМА РАЗВЕРНУТА!"
    echo ""
    echo "🌐 Откройте: http://$SERVER:8502"
    echo ""
    echo "⚡ ОПТИМИЗАЦИИ ЗАГРУЗКИ:"
    echo "   ✅ Кеширование построения дерева категорий"
    echo "   ✅ Выборка данных для больших объемов (>50,000)"
    echo "   ✅ Ограничение глубины категорий до 3 уровней"
    echo "   ✅ Показ только топ-20 категорий на уровень"
    echo "   ✅ Ограничение товаров до 5 на категорию"
    echo ""
    echo "🎯 ТЕПЕРЬ СИСТЕМА ЗАГРУЖАЕТСЯ БЫСТРЕЕ!"
    
} || {
    echo "⚠️ Проблемы с запуском, проверяем логи..."
    ssh "$USER@$SERVER" "
        echo '📝 Последние ошибки:'
        journalctl -u webhook-analytics --no-pager -n 15
    "
}

echo ""
echo "✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"