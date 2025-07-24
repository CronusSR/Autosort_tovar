#!/bin/bash

# Развертывание расширенной аналитики на сервере
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📊 РАЗВЕРТЫВАНИЕ РАСШИРЕННОЙ АНАЛИТИКИ"
echo "📅 Время: $(date)"
echo ""

# Создаем резервную копию старого приложения
echo "💾 Создание резервной копии..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    # Создаем резервную копию
    if [ -f webhook_persistent_app.py ]; then
        cp webhook_persistent_app.py webhook_persistent_app_backup_$(date +%Y%m%d_%H%M%S).py
        echo '✅ Резервная копия создана'
    fi
"

# Загружаем новое приложение
echo "📤 Загрузка расширенной аналитики..."

scp webhook_app_enhanced_analytics.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    exit 1
}

echo "✅ Новое приложение загружено"

# Перезапускаем сервис
echo ""
echo "🔄 Перезапуск аналитического сервиса..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔄 Остановка старого сервиса...'
    systemctl stop webhook-analytics
    
    echo '🚀 Запуск нового сервиса...'
    systemctl start webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса сервиса...'
    systemctl status webhook-analytics --no-pager | head -15
"

# Проверяем доступность
echo ""
echo "🔍 Проверка доступности расширенной аналитики..."

sleep 10

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Расширенная аналитика доступна!"
    echo ""
    echo "🌐 Откройте в браузере: http://$SERVER:8502"
    echo ""
    echo "🆕 НОВЫЕ ВОЗМОЖНОСТИ:"
    echo "   📊 Расширенный общий анализ"
    echo "   🔄 Анализ оборачиваемости по формуле (остатки/продажи)*период"
    echo "   🏙️ Анализ оборачиваемости по городам"
    echo "   📦 ABC анализ по категориям товаров"
    echo "   📈 Детальная аналитика (дни недели, тепловые карты)"
    echo "   💰 Стоимостный анализ остатков"
} || {
    echo "⚠️  Сервис еще запускается или есть проблемы"
    echo "🔍 Проверьте логи:"
    echo "   ssh $USER@$SERVER 'journalctl -u webhook-analytics -f'"
}

echo ""
echo "✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"