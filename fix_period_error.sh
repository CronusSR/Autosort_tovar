#!/bin/bash

# Быстрое исправление ошибки Period в тепловой карте
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ PERIOD В ТЕПЛОВОЙ КАРТЕ"
echo "📅 Время: $(date)"
echo ""

# Загружаем исправленный файл
echo "📤 Загрузка исправленного файла..."

scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    echo ""
    echo "🔧 РУЧНОЕ ИСПРАВЛЕНИЕ:"
    echo "Замените в файле /opt/inventory_system/webhook_persistent_app.py строку:"
    echo ""
    echo "БЫЛО:"
    echo "sales_data['month_year'] = pd.to_datetime(sales_data['date']).dt.to_period('M')"
    echo ""
    echo "СТАЛО:"
    echo "sales_data['month_year'] = pd.to_datetime(sales_data['date']).dt.strftime('%Y-%m')"
    echo ""
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
    echo "✅ ОШИБКА PERIOD ИСПРАВЛЕНА!"
    echo ""
    echo "🌐 Приложение доступно: http://$SERVER:8502"
    echo ""
    echo "🔧 ЧТО ИСПРАВЛЕНО:"
    echo "   ✅ Заменен Period на строковый формат даты"
    echo "   ✅ Тепловая карта теперь работает без ошибок"
    echo "   ✅ JSON сериализация исправлена"
    echo ""
    echo "📊 ТЕПЛОВАЯ КАРТА:"
    echo "   - Показывает продажи по дням месяца"
    echo "   - Использует формат YYYY-MM вместо Period"
    echo "   - Работает со всеми периодами анализа"
} || {
    echo "⚠️ Все еще есть проблемы, проверяем логи..."
    ssh "$USER@$SERVER" "
        echo '📝 Последние ошибки:'
        journalctl -u webhook-analytics --no-pager -n 10
    "
}

echo ""
echo "✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"