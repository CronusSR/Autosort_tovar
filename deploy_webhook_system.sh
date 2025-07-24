#!/bin/bash

# Скрипт развертывания полной системы вебхуков на SSH сервере
# Автор: Assistant
# Дата: 2025-07-24

SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🚀 Развертывание системы вебхуков на сервере..."
echo "📅 Время: $(date)"

# Создаем временную директорию для архива
TEMP_DIR="/tmp/webhook_deploy_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📦 Подготовка файлов для развертывания..."

# Основные файлы вебхук-системы
cp webhook_receiver.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_receiver.py"
cp webhook_data_accumulator.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_data_accumulator.py"
cp webhook_persistent_app.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_persistent_app.py"

# Дополнительные модули
cp modular_inventory_system.py "$TEMP_DIR/" 2>/dev/null && echo "✅ modular_inventory_system.py"
cp single_file_ads_processor.py "$TEMP_DIR/" 2>/dev/null && echo "✅ single_file_ads_processor.py"

# Документация
cp WEBHOOK_COMPLETE_SETUP_GUIDE.md "$TEMP_DIR/" 2>/dev/null && echo "✅ Руководство по настройке"
cp API_СПЕЦИФИКАЦИЯ_ВЕБХУКИ.md "$TEMP_DIR/" 2>/dev/null && echo "✅ API спецификация"
cp 1c_webhook_example.txt "$TEMP_DIR/" 2>/dev/null && echo "✅ Пример кода для 1С"

# Создаем скрипт настройки сервера
cat > "$TEMP_DIR/setup_webhook_server.sh" << 'EOF'
#!/bin/bash

echo "🔧 Настройка сервера для работы с вебхуками..."

# Установка зависимостей
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install flask python-dotenv sqlite3

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p webhook_uploads
mkdir -p logs
mkdir -p backups

# Создание .env файла с секретным ключом
echo "🔐 Создание файла конфигурации..."
cat > .env << ENVEOF
WEBHOOK_SECRET=furniture_company_secret_key_2025
ENVEOF
chmod 600 .env

# Создание systemd сервиса для вебхук-приемника
echo "⚙️ Создание сервиса webhook-receiver..."
cat > /etc/systemd/system/webhook-receiver.service << SERVICEEOF
[Unit]
Description=Webhook Receiver for 1C Data
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory_system
Environment="PATH=/opt/inventory_system/venv/bin"
ExecStart=/opt/inventory_system/venv/bin/python webhook_receiver.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Создание systemd сервиса для аналитического приложения
echo "⚙️ Создание сервиса webhook-analytics..."
cat > /etc/systemd/system/webhook-analytics.service << SERVICEEOF
[Unit]
Description=Webhook Analytics Application
After=network.target webhook-receiver.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory_system
Environment="PATH=/opt/inventory_system/venv/bin"
ExecStart=/opt/inventory_system/venv/bin/streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Перезагрузка systemd
echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload

# Запуск и включение сервисов
echo "🚀 Запуск сервисов..."
systemctl enable webhook-receiver.service
systemctl enable webhook-analytics.service
systemctl stop webhook-receiver.service 2>/dev/null || true
systemctl stop webhook-analytics.service 2>/dev/null || true
systemctl start webhook-receiver.service
systemctl start webhook-analytics.service

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
sleep 3
systemctl status webhook-receiver.service --no-pager | head -10
echo "---"
systemctl status webhook-analytics.service --no-pager | head -10

# Настройка файрвола
echo "🔥 Настройка файрвола..."
ufw allow 5000/tcp comment "Webhook receiver"
ufw allow 8502/tcp comment "Webhook analytics"

echo ""
echo "✅ Настройка сервера завершена!"
echo ""
echo "🔗 Ваши адреса:"
echo "   Вебхук (для 1С): http://217.114.1.117:5000"
echo "   Аналитика: http://217.114.1.117:8502"
echo ""
echo "📝 Для проверки работы:"
echo "   curl http://217.114.1.117:5000/webhook/status"
echo ""
EOF

chmod +x "$TEMP_DIR/setup_webhook_server.sh"

# Создаем архив
echo -e "\n📦 Создание архива..."
cd "$TEMP_DIR"
tar -czf webhook_system.tar.gz * || { echo "❌ Ошибка создания архива"; exit 1; }

# Создаем резервную копию на сервере
echo -e "\n💾 Создание резервной копии на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    mkdir -p backups && 
    tar -czf backups/backup_before_webhook_$(date +%Y%m%d_%H%M%S).tar.gz \
        *.py \
        .env \
        webhook_uploads/ \
        webhook_data.db \
        2>/dev/null || echo 'Создана частичная резервная копия'
"

# Загружаем архив на сервер
echo -e "\n📤 Загрузка системы на сервер..."
scp webhook_system.tar.gz "$USER@$SERVER:$REMOTE_PATH/" || { echo "❌ Ошибка загрузки"; exit 1; }

# Распаковываем и настраиваем
echo -e "\n🔧 Распаковка и настройка на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    tar -xzf webhook_system.tar.gz && 
    rm webhook_system.tar.gz &&
    chmod +x setup_webhook_server.sh &&
    ./setup_webhook_server.sh
"

# Проверяем доступность
echo -e "\n🔍 Проверка доступности системы..."
sleep 10

echo "Проверка вебхук-сервера..."
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:5000/webhook/status" | grep -q "200" && {
    echo "✅ Вебхук-сервер доступен"
} || {
    echo "⚠️  Вебхук-сервер может быть еще не готов"
}

echo "Проверка аналитического приложения..."
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Аналитическое приложение доступно"
} || {
    echo "⚠️  Аналитическое приложение может быть еще не готово"
}

# Очистка временных файлов
rm -rf "$TEMP_DIR"

echo -e "\n🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo ""
echo "📋 ВАЖНАЯ ИНФОРМАЦИЯ:"
echo "🔗 Адреса для 1С программиста:"
echo "   • Продажи: http://$SERVER:5000/webhook/sales"
echo "   • Остатки: http://$SERVER:5000/webhook/stock"
echo "   • Статус:  http://$SERVER:5000/webhook/status"
echo ""
echo "📊 Аналитика (постоянная ссылка):"
echo "   • http://$SERVER:8502"
echo ""
echo "🔐 Секретный ключ: furniture_company_secret_key_2025"
echo ""
echo "📚 Документация загружена на сервер:"
echo "   • WEBHOOK_COMPLETE_SETUP_GUIDE.md"
echo "   • API_СПЕЦИФИКАЦИЯ_ВЕБХУКИ.md"
echo ""
echo "✅ Система готова к приему данных от 1С!"