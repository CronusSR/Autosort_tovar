#!/bin/bash

# Быстрое обновление для поддержки ZIP
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🚀 Быстрое обновление для поддержки ZIP..."

# Загружаем только необходимые файлы
echo "📤 Загрузка обработчика ZIP..."

scp webhook_zip_handler.py "$USER@$SERVER:$REMOTE_PATH/" || exit 1
scp webhook_receiver_zip_updated.py "$USER@$SERVER:$REMOTE_PATH/webhook_receiver_new.py" || exit 1

echo ""
echo "🔧 Обновление на сервере..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '💾 Создание резервной копии...'
    cp webhook_receiver.py webhook_receiver_backup_$(date +%Y%m%d_%H%M%S).py
    
    echo '🔄 Обновление webhook_receiver.py...'
    cp webhook_receiver_new.py webhook_receiver.py
    
    echo '🔄 Перезапуск webhook сервиса...'
    systemctl restart webhook-receiver
    
    sleep 3
    
    echo '📊 Проверка статуса...'
    systemctl status webhook-receiver --no-pager | head -10
    
    echo ''
    echo '🔍 Проверка поддержки ZIP:'
    curl -s localhost:5000/webhook/status | grep -o '\"supported_formats\".*' || echo 'Формат ответа изменен'
"

echo ""
echo "✅ Обновление завершено!"
echo "🧪 Теперь можно запустить: ./test_real_webhook.sh"