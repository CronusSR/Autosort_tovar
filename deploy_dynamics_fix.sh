#!/bin/bash

# ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ДИНАМИКИ ПРОДАЖ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ДИНАМИКИ ПРОДАЖ"
echo "Проблема: неправильное отображение динамики продаж"
echo "Решение: исправление логики фильтрации по периоду"
echo ""

# Загружаем исправленный файл
echo "📤 Загрузка исправленного приложения..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    echo '🔄 Перезапуск сервиса с исправлениями...'
    systemctl start webhook-analytics
    
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис успешно перезапущен'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -10
    fi
    
    echo ''
    echo '✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!'
    echo ''
    echo '📊 ЧТО ИСПРАВЛЕНО:'
    echo '   ✅ Логика выбора периода учитывает имеющиеся данные'
    echo '   ✅ Добавлена информация о периоде данных'
    echo '   ✅ Улучшена динамика продаж с проверками'
    echo '   ✅ Добавлена отладочная информация'
    echo ''
    echo '🌐 Проверьте: http://217.114.1.117:8502'
    echo '   📈 Общий анализ → должна правильно показывать динамику'
    echo '   📅 Разные периоды → корректная фильтрация'
    echo '   🔍 Отладочная информация → для диагностики'
"

echo ""
echo "✅ ИСПРАВЛЕНИЯ РАЗВЕРНУТЫ!"
echo "Динамика продаж теперь должна отображаться корректно"
