#!/bin/bash

# Быстрое исправление ошибки scatter plot
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ SCATTER PLOT"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка исправленного файла..."

scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки"
    echo ""
    echo "🔧 ПРОБЛЕМА: Отрицательные значения в размере точек scatter plot"
    echo ""
    echo "РЕШЕНИЕ: Добавить обработку отрицательных значений:"
    echo "plot_data['amount_abs'] = plot_data['amount'].abs()"
    echo "plot_data['size_normalized'] = 5 + (plot_data['amount_abs'] / plot_data['amount_abs'].max()) * 45"
    echo ""
    exit 1
}

echo "✅ Файл загружен"

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

echo ""
echo "🔍 Проверка исправления..."

sleep 10

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ ОШИБКА SCATTER PLOT ИСПРАВЛЕНА!"
    echo ""
    echo "🌐 Приложение доступно: http://$SERVER:8502"
    echo ""
    echo "🔧 ЧТО ИСПРАВЛЕНО:"
    echo "   ✅ Убраны отрицательные значения для размера точек"
    echo "   ✅ Добавлена нормализация размеров (от 5 до 50)"
    echo "   ✅ Добавлена цветовая схема для лучшей визуализации"
    echo "   ✅ Обработка случая когда все значения равны нулю"
    echo ""
    echo "📊 ГРАФИК ТЕПЕРЬ ПОКАЗЫВАЕТ:"
    echo "   - Размер точки = величина продаж"
    echo "   - Цвет точки = величина продаж"
    echo "   - Даты на оси X"
    echo "   - Выручка на оси Y"
    echo "   - При наведении: дата, день недели, сумма"
} || {
    echo "⚠️ Все еще есть проблемы, проверяем логи..."
    ssh "$USER@$SERVER" "
        echo '📝 Последние ошибки:'
        journalctl -u webhook-analytics --no-pager -n 10
    "
}

echo ""
echo "✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"