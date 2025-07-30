#\!/bin/bash
# Используем рабочую backup версию

echo "🔧 Восстановление рабочей версии"
echo "================================="

# Копируем стабильную версию из локальной папки ssh
echo "📋 Используем стабильную backup версию..."
scp ssh/webhook_persistent_app_backup_20250724_120403.py root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py

# Перезапускаем приложение на сервере
echo "🔄 Перезапускаем приложение..."
ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ Восстановлена стабильная версия\!"
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
echo ""
echo "ℹ️  Это базовая версия без новых функций, но она должна работать стабильно"
