#!/bin/bash

# Реальный тест отправки ZIP на webhook
SERVER="217.114.1.117"
WEBHOOK_URL="http://$SERVER:5000/webhook/sales"
SECRET_KEY="furniture_company_secret_key_2025"

echo "🚀 ТЕСТИРОВАНИЕ РЕАЛЬНОГО WEBHOOK"
echo "📅 Время: $(date)"
echo ""

# Проверяем доступность webhook
echo "🔍 Проверка webhook сервера:"
curl -s "$SERVER:5000/webhook/status" | head -20 || echo "Статус недоступен"

echo ""
echo "📦 Подготовка к отправке ZIP файла..."

# Генерируем подпись для ZIP файла
ZIP_FILE="Выгрузка JSON.zip"

# Вычисляем HMAC-SHA256 подпись
# На Linux/WSL используем openssl
SIGNATURE=$(openssl dgst -sha256 -hmac "$SECRET_KEY" -binary "$ZIP_FILE" | xxd -p -c 256)

echo "📊 Информация о файле:"
echo "   Файл: $ZIP_FILE"
echo "   Размер: $(ls -lh "$ZIP_FILE" | awk '{print $5}')"
echo "   Подпись: sha256=$SIGNATURE"

echo ""
echo "📤 Отправка ZIP на webhook..."

# Отправляем ZIP файл
RESPONSE=$(curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/zip" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  --data-binary "@$ZIP_FILE" \
  -w "\n\nHTTP Code: %{http_code}\n" \
  2>/dev/null)

echo "📨 Ответ сервера:"
echo "$RESPONSE"

echo ""
echo "🔍 Проверка результата на сервере:"

# Проверяем что создалось на сервере
ssh root@$SERVER "
    cd /opt/inventory_system
    
    echo '📁 Последние файлы в webhook_uploads:'
    ls -la webhook_uploads/*.json | tail -5
    
    echo ''
    echo '📊 Проверка базы данных:'
    if [ -f webhook_data.db ]; then
        echo 'База данных существует:'
        ls -lh webhook_data.db
        
        # Проверяем количество записей
        sqlite3 webhook_data.db 'SELECT COUNT(*) as total FROM sales' 2>/dev/null || echo 'Таблица sales еще не создана'
    else
        echo 'База данных еще не создана'
    fi
"

echo ""
echo "🌐 Проверка аналитики на порту 8502:"
echo "Откройте в браузере: http://$SERVER:8502"
echo ""
echo "✅ Тест завершен!"