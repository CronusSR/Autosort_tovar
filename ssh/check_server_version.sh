#\!/bin/bash
# Проверка версии файла на сервере

echo "📊 Проверка версии webhook_persistent_app.py на сервере"
echo "====================================================="

echo "🔍 Размер файла на сервере:"
ssh root@217.114.1.117 "ls -la /opt/inventory_system/webhook_persistent_app.py"

echo ""
echo "🔍 Первые строки файла на сервере:"
ssh root@217.114.1.117 "head -20 /opt/inventory_system/webhook_persistent_app.py  < /dev/null |  grep -E '(import|PYTZ|expanded_key)'"

echo ""
echo "🔍 Проверка наличия expanded_key на сервере:"
ssh root@217.114.1.117 "grep -n 'expanded_key' /opt/inventory_system/webhook_persistent_app.py | head -5"

echo ""
echo "🔍 Проверка запущенного процесса:"
ssh root@217.114.1.117 "ps aux | grep webhook_persistent_app | grep -v grep"
