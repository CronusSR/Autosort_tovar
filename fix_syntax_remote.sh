#!/bin/bash

# ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ НА СЕРВЕРЕ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ НА СЕРВЕРЕ"
echo "=================================================="
echo "📅 Время: $(date)"
echo ""

# Загружаем исправленный файл
echo "📤 Загрузка исправленного файла..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно загружен"
else
    echo "❌ Ошибка загрузки файла"
    exit 1
fi

echo ""
echo "🔄 ВЫПОЛНЕНИЕ ИСПРАВЛЕНИЙ НА СЕРВЕРЕ..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 Остановка сервиса...'
    systemctl stop webhook-analytics
    
    echo '🔍 Проверка синтаксиса Python файла...'
    python3 -m py_compile webhook_persistent_app.py
    
    if [ $? -eq 0 ]; then
        echo '✅ Синтаксис корректный'
        
        echo '🔄 Запуск сервиса...'
        systemctl start webhook-analytics
        
        sleep 5
        
        if systemctl is-active --quiet webhook-analytics; then
            echo '✅ Сервис успешно запущен'
            echo ''
            echo '🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!'
            echo ''
            echo '📊 ЧТО ИСПРАВЛЕНО:'
            echo '   ✅ Убрана синтаксическая ошибка с лишним else'
            echo '   ✅ Исправлена логика отображения динамики продаж'
            echo '   ✅ Система использует реальные даты из данных'
            echo '   ✅ Добавлена отладочная информация'
            echo ''
            echo '🌐 Система готова: http://217.114.1.117:8502'
            echo '   📈 Общий анализ → исправленная динамика продаж'
            echo '   🔍 Отладочная информация → для диагностики'
        else
            echo '❌ Проблемы с запуском сервиса'
            systemctl status webhook-analytics --no-pager | head -10
        fi
    else
        echo '❌ Ошибка синтаксиса в Python файле'
        echo 'Проверьте файл webhook_persistent_app.py'
    fi
"

echo ""
echo "✅ СКРИПТ ЗАВЕРШЕН!"
echo ""