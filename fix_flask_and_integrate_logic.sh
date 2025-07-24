#!/bin/bash

# Скрипт исправления Flask и интеграции логики межфилиальных перемещений
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 Исправление Flask и интеграция полной логики анализа..."

# Создаем временную директорию
TEMP_DIR="/tmp/webhook_update_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📦 Подготовка обновленных файлов..."

# Копируем все необходимые файлы для полного анализа
cp webhook_receiver.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_receiver.py"
cp webhook_data_accumulator.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_data_accumulator.py"
cp webhook_persistent_app.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_persistent_app.py"
cp modular_inventory_system.py "$TEMP_DIR/" 2>/dev/null && echo "✅ modular_inventory_system.py"
cp single_file_ads_processor.py "$TEMP_DIR/" 2>/dev/null && echo "✅ single_file_ads_processor.py"

# Копируем логику межфилиальных перемещений
cp "pages/🔄_Межфилиальные_перемещения.py" "$TEMP_DIR/inter_branch_logic.py" 2>/dev/null && echo "✅ Логика межфилиальных перемещений"

# Все дополнительные модули для полного анализа
cp ads_category_fix_improved.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_category_fix_improved.py"
cp streamlit_improved_ads_ui.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_improved_ads_ui.py"
cp enhanced_warehouse_analysis.py "$TEMP_DIR/" 2>/dev/null && echo "✅ enhanced_warehouse_analysis.py"

# Создаем скрипт установки на сервере
cat > "$TEMP_DIR/install_and_fix.sh" << 'EOF'
#!/bin/bash

echo "🔧 Установка зависимостей и исправление проблем..."

# Активируем виртуальное окружение и устанавливаем зависимости
source venv/bin/activate

echo "📦 Установка Flask и других зависимостей..."
pip install flask python-dotenv plotly

echo "🔄 Остановка сервисов..."
systemctl stop webhook-receiver
systemctl stop webhook-analytics

echo "📁 Создание необходимых директорий..."
mkdir -p webhook_uploads
mkdir -p automated_reports
mkdir -p backups
mkdir -p logs

echo "🔐 Проверка файла конфигурации..."
if [ ! -f .env ]; then
    echo "WEBHOOK_SECRET=furniture_company_secret_key_2025" > .env
    chmod 600 .env
fi

echo "🔄 Запуск сервисов..."
systemctl start webhook-receiver
systemctl start webhook-analytics

sleep 5

echo "📊 Проверка статуса сервисов..."
echo "=== Webhook Receiver ==="
systemctl status webhook-receiver --no-pager | head -10

echo ""
echo "=== Webhook Analytics ==="
systemctl status webhook-analytics --no-pager | head -10

echo ""
echo "🌐 Проверка доступности..."
curl -s http://localhost:5000/webhook/status && echo "" || echo "Webhook receiver не отвечает"

echo ""
echo "✅ Установка завершена!"
EOF

chmod +x "$TEMP_DIR/install_and_fix.sh"

# Создаем архив
echo -e "\n📦 Создание архива..."
cd "$TEMP_DIR"
tar -czf webhook_update.tar.gz * || { echo "❌ Ошибка создания архива"; exit 1; }

# Загружаем на сервер
echo -e "\n📤 Загрузка обновлений на сервер..."
scp webhook_update.tar.gz "$USER@$SERVER:$REMOTE_PATH/" || { echo "❌ Ошибка загрузки"; exit 1; }

# Устанавливаем на сервере
echo -e "\n🔧 Установка на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    tar -xzf webhook_update.tar.gz && 
    rm webhook_update.tar.gz &&
    chmod +x install_and_fix.sh &&
    ./install_and_fix.sh
"

# Проверяем результат
echo -e "\n🔍 Проверка результата..."
sleep 5

echo "Проверка webhook сервера..."
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:5000/webhook/status" | grep -q "200" && {
    echo "✅ Webhook сервер работает!"
    curl -s "http://$SERVER:5000/webhook/status" | head -5
} || {
    echo "⚠️  Webhook сервер еще запускается или есть проблемы"
}

echo -e "\nПроверка аналитического приложения..."
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Аналитическое приложение работает!"
} || {
    echo "⚠️  Аналитическое приложение недоступно"
}

# Очистка
rm -rf "$TEMP_DIR"

echo -e "\n🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🔗 Ваши адреса:"
echo "   • Webhook: http://$SERVER:5000/webhook/status"
echo "   • Аналитика: http://$SERVER:8502"
echo ""
echo "📝 Для тестирования webhook:"
echo "   curl -X POST http://$SERVER:5000/webhook/sales \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'X-Hub-Signature-256: sha256=test' \\"
echo "     -d '[{\"test\": \"data\"}]'"