#!/bin/bash

# Развертывание исправлений UI
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 РАЗВЕРТЫВАНИЕ ИСПРАВЛЕНИЙ UI"
echo "📅 Время: $(date)"
echo ""

# Создаем резервную копию
echo "💾 Создание резервной копии..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    if [ -f webhook_persistent_app.py ]; then
        cp webhook_persistent_app.py webhook_persistent_app_backup_ui_$(date +%Y%m%d_%H%M%S).py
        echo '✅ Резервная копия создана'
    fi
"

# Загружаем исправленное приложение
echo "📤 Загрузка исправленного приложения..."

scp webhook_app_enhanced_analytics.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    exit 1
}

echo "✅ Файл загружен"

# Перезапускаем сервис
echo ""
echo "🔄 Перезапуск аналитического сервиса..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔄 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    echo '🚀 Запуск обновленного сервиса...'
    systemctl start webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса...'
    systemctl status webhook-analytics --no-pager | head -10
"

# Проверка результата
echo ""
echo "🔍 Проверка исправлений..."

sleep 10

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Приложение с исправлениями доступно!"
    echo ""
    echo "🌐 Откройте: http://$SERVER:8502"
    echo ""
    echo "🔧 ИСПРАВЛЕНИЯ:"
    echo "   ✅ Тепловая карта поддерживает любое количество месяцев"
    echo "   ✅ Период анализа сохраняется при обновлении данных"
    echo "   ✅ Убрана опция 'Выбрать даты' из селектора периода"
    echo "   ✅ Улучшено отображение для периодов > 12 месяцев"
    echo "   ✅ Добавлена информация о количестве месяцев в тепловой карте"
} || {
    echo "⚠️  Сервис еще запускается или есть проблемы"
    echo "🔍 Проверьте логи на сервере"
}

echo ""
echo "✅ РАЗВЕРТЫВАНИЕ ИСПРАВЛЕНИЙ ЗАВЕРШЕНО!"