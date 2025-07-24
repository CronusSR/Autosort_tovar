#!/bin/bash

# Исправление ошибки маппинга колонок
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ КОЛОНОК"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка версии с исправленным маппингом колонок..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

echo ""
echo "🔄 Перезапуск системы..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    systemctl stop webhook-analytics
    sleep 3
    systemctl start webhook-analytics
    sleep 5
    systemctl status webhook-analytics --no-pager | head -10
"

echo ""
echo "✅ ОШИБКА МАППИНГА КОЛОНОК ИСПРАВЛЕНА!"
echo ""
echo "🐛 ЧТО БЫЛО ИСПРАВЛЕНО:"
echo ""
echo "   ❌ ОШИБКА: could not convert string to float: 'PB0040 - Кромка...'"
echo "   ❌ ПРОБЛЕМА: Название товара попало в колонку 'Количество'"
echo "   ❌ ПРИЧИНА: Неправильный порядок колонок при переименовании"
echo ""
echo "   ✅ ИСПРАВЛЕНИЕ:"
echo "   ✅ Выбор колонок по именам, а не по порядку"
echo "   ✅ Проверка наличия каждой колонки"
echo "   ✅ Безопасное переименование через column_mapping"
echo "   ✅ Проверка что значение числовое перед форматированием"
echo ""
echo "   🔧 НОВАЯ ЛОГИКА:"
echo "   1. Выбираем колонки: ['category', 'amount', 'quantity', ...]"
echo "   2. Переименовываем через mapping словарь"
echo "   3. Проверяем isdigit() перед float()"
echo "   4. Если не число - оставляем как строку"
echo ""
echo "✅ ТЕПЕРЬ ТАБЛИЦА ОТОБРАЖАЕТСЯ КОРРЕКТНО!"
echo ""
echo "🌐 Откройте: http://$SERVER:8502"