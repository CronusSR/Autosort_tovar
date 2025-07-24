#!/bin/bash

# Тест с маленьким ZIP файлом
SERVER="217.114.1.117"
WEBHOOK_URL="http://$SERVER:5000/webhook/sales"
SECRET_KEY="furniture_company_secret_key_2025"

echo "🧪 ТЕСТ С МАЛЕНЬКИМ ZIP ФАЙЛОМ"
echo ""

# Создаем маленький тестовый ZIP
echo "📦 Создание тестового ZIP..."
mkdir -p test_json
cp "2024-01-31.json" test_json/ 2>/dev/null || {
    # Если файла нет, создаем тестовый JSON
    echo '[{"ДатаВыгрузки":"2025-07-24","НачалоПериода":"2025-07-01","КонецПериода":"2025-07-24","Филиал":"Тест","Продажи":[]}]' > test_json/test.json
}

cd test_json
zip -r ../test_small.zip *.json
cd ..

echo "📊 Размер тестового ZIP: $(ls -lh test_small.zip | awk '{print $5}')"

# Генерируем подпись
SIGNATURE=$(openssl dgst -sha256 -hmac "$SECRET_KEY" -binary "test_small.zip" | xxd -p -c 256)

echo ""
echo "📤 Отправка маленького ZIP..."

# Отправляем с таймаутом
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/zip" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  --data-binary "@test_small.zip" \
  --max-time 30 \
  -w "\n\nHTTP Code: %{http_code}\nTime: %{time_total}s\n" \
  -v 2>&1 | tail -20

# Очистка
rm -rf test_json test_small.zip

echo ""
echo "✅ Тест с маленьким файлом завершен"

echo ""
echo "💡 АЛЬТЕРНАТИВА: Загрузка ZIP напрямую на сервер"
echo ""
echo "Вы можете загрузить ZIP на сервер и обработать локально:"
echo "1. scp 'Выгрузка JSON.zip' root@$SERVER:/opt/inventory_system/"
echo "2. ssh root@$SERVER"
echo "3. cd /opt/inventory_system"
echo "4. python3 -c 'from webhook_zip_handler import handle_zip_upload; import open; handle_zip_upload(open(\"Выгрузка JSON.zip\", \"rb\").read())'"