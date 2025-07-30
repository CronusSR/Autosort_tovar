#!/bin/bash

# Быстрое исправление и перезапуск webhook_persistent_app.py на порtu 8502
echo "🔧 Быстрое исправление и перезапуск webhook_persistent_app"

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"

echo "1️⃣ Копируем исправленный webhook_persistent_app.py..."
scp webhook_persistent_app.py $SERVER:$TARGET_DIR

echo "2️⃣ Перезапускаем приложение на сервере..."
ssh $SERVER "cd $TARGET_DIR && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &"

echo "3️⃣ Ждем запуска..."
sleep 5

echo "✅ Готово! Приложение доступно на http://your-server:8502"
echo "📋 Для проверки логов: ssh $SERVER 'tail -f $TARGET_DIR/webhook_8502.log'"