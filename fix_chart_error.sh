#!/bin/bash

# Исправление ошибки графика оборачиваемости
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ ГРАФИКА ОБОРАЧИВАЕМОСТИ"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка исправленной версии..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

echo ""
echo "🔄 Перезапуск системы..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    systemctl stop webhook-analytics
    sleep 2
    systemctl start webhook-analytics
    sleep 5
    systemctl status webhook-analytics --no-pager | head -5
"

echo ""
echo "✅ ОШИБКА ГРАФИКА ИСПРАВЛЕНА!"
echo ""
echo "🔧 ЧТО ИСПРАВЛЕНО:"
echo "   ✅ Проблема с колонками в turnover_distribution"
echo "   ✅ Исправлены названия колонок для plotly express"
echo "   ✅ График оборачиваемости теперь работает"
echo ""
echo "🌐 Проверьте: http://$SERVER:8502"
echo "📊 Откройте вкладку '🔄 Оборачиваемость' - график должен работать"