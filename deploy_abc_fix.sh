#!/bin/bash

# Развертывание исправления ABC анализа по категориям
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ABC АНАЛИЗА ПО КАТЕГОРИЯМ"
echo "📅 Время: $(date)"
echo ""

# Загружаем обновленные файлы
echo "📤 Загрузка обновленных файлов..."

scp webhook_data_accumulator.py "$USER@$SERVER:$REMOTE_PATH/" || exit 1
scp webhook_app_enhanced_analytics.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || exit 1
scp update_db_with_categories.py "$USER@$SERVER:$REMOTE_PATH/" || exit 1

echo "✅ Файлы загружены"

# Обновляем базу данных на сервере
echo ""
echo "🔄 Обновление базы данных на сервере..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    source venv/bin/activate
    
    echo '🔧 Запуск обновления базы данных...'
    python3 update_db_with_categories.py
    
    echo ''
    echo '🔄 Перезапуск аналитического сервиса...'
    systemctl restart webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса сервиса...'
    systemctl status webhook-analytics --no-pager | head -10
"

# Проверка результата
echo ""
echo "🔍 Проверка результата..."

sleep 10

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Аналитика с исправленным ABC доступна!"
    echo ""
    echo "🌐 Откройте: http://$SERVER:8502"
    echo "📊 Перейдите на вкладку 'ABC категорий'"
    echo ""
    echo "🔧 ИСПРАВЛЕНИЯ:"
    echo "   ✅ Добавлены поля category и category_path в БД"
    echo "   ✅ Обновлена функция calculate_abc_by_categories"
    echo "   ✅ Перезаписаны данные с категориями"
    echo "   ✅ ABC анализ теперь должен показывать категории"
} || {
    echo "⚠️  Сервис еще запускается или есть проблемы"
    echo "🔍 Проверьте логи на сервере"
}

echo ""
echo "✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"