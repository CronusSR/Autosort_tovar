#!/bin/bash

# Копирование диагностических скриптов на SSH сервер
echo "📋 Копирование диагностических скриптов на сервер..."

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"

FILES=(
    "diagnose_hierarchy_on_server.py"
    "restart_services_with_new_hierarchy.sh"
    "restart_webhook_with_hierarchy.sh"
)

echo "📤 Копируем диагностические скрипты:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  🔄 Копируем $file..."
        scp "$file" "$SERVER:$TARGET_DIR"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ $file успешно скопирован"
        else
            echo "  ❌ Ошибка копирования $file"
        fi
    else
        echo "  ⚠️  Файл $file не найден"
    fi
done

echo ""
echo "🎯 СЛЕДУЮЩИЕ ШАГИ НА СЕРВЕРЕ:"
echo "1. ssh $SERVER"
echo "2. cd $TARGET_DIR"
echo "3. python3 diagnose_hierarchy_on_server.py  # Диагностика"
echo "4. bash restart_webhook_with_hierarchy.sh  # Перезапуск webhook приложения"
echo ""
echo "ИЛИ для других сервисов:"
echo "4. bash restart_services_with_new_hierarchy.sh  # Перезапуск всех сервисов"