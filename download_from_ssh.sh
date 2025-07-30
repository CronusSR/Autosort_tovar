#!/bin/bash
# Скрипт для загрузки всех файлов с SSH сервера для анализа

echo "📥 Загрузка файлов с SSH сервера"
echo "================================"

# Создаем папку сервер
mkdir -p сервер
cd сервер

echo "🔗 Подключаемся к серверу root@217.114.1.117..."

# Проверяем доступность сервера
if ! ping -c 1 217.114.1.117 &> /dev/null; then
    echo "❌ Сервер недоступен"
    exit 1
fi

echo "✅ Сервер доступен"
echo ""

# Загружаем основные файлы приложения
echo "📋 Загружаем основные файлы приложения..."
scp root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py ./
scp root@217.114.1.117:/opt/inventory_system/webhook_data_accumulator.py ./
scp root@217.114.1.117:/opt/inventory_system/requirements.txt ./

echo ""
echo "📋 Загружаем backup файлы (если есть)..."
scp root@217.114.1.117:/opt/inventory_system/webhook_persistent_app_*.py ./ 2>/dev/null || echo "⚠️ Backup файлы не найдены"

echo ""
echo "📋 Загружаем логи..."
scp root@217.114.1.117:/opt/inventory_system/webhook_8502.log ./ 2>/dev/null || echo "⚠️ webhook_8502.log не найден"
scp root@217.114.1.117:/opt/inventory_system/webhook_5000.log ./ 2>/dev/null || echo "⚠️ webhook_5000.log не найден"
scp root@217.114.1.117:/opt/inventory_system/nohup.out ./ 2>/dev/null || echo "⚠️ nohup.out не найден"

echo ""
echo "📋 Загружаем данные JSON (если есть)..."
scp root@217.114.1.117:/opt/inventory_system/*.json ./ 2>/dev/null || echo "⚠️ JSON файлы не найдены"

echo ""
echo "📋 Загружаем конфигурационные файлы..."
scp root@217.114.1.117:/opt/inventory_system/.streamlit/config.toml ./ 2>/dev/null || echo "⚠️ config.toml не найден"

echo ""
echo "📋 Проверяем структуру папки на сервере..."
ssh root@217.114.1.117 "cd /opt/inventory_system && echo '📁 Содержимое /opt/inventory_system:' && ls -la"

echo ""
echo "📋 Проверяем запущенные процессы..."
ssh root@217.114.1.117 "echo '🔄 Запущенные процессы:' && ps aux | grep -E '(streamlit|webhook|python)' | grep -v grep"

echo ""
echo "📋 Проверяем последние строки логов..."
echo "--- webhook_8502.log (последние 10 строк) ---"
ssh root@217.114.1.117 "tail -n 10 /opt/inventory_system/webhook_8502.log 2>/dev/null || echo 'Лог не найден'"

echo ""
echo "--- webhook_5000.log (последние 10 строк) ---"
ssh root@217.114.1.117 "tail -n 10 /opt/inventory_system/webhook_5000.log 2>/dev/null || echo 'Лог не найден'"

echo ""
echo "📋 Проверяем доступность портов..."
ssh root@217.114.1.117 "netstat -tulpn | grep -E ':(5000|8502)' || echo 'Порты не прослушиваются'"

echo ""
echo "📋 Проверяем размеры файлов..."
ssh root@217.114.1.117 "cd /opt/inventory_system && du -sh * 2>/dev/null | sort -hr"

echo ""
echo "📋 Загружаем дополнительные Python файлы..."
scp root@217.114.1.117:/opt/inventory_system/*.py ./ 2>/dev/null || echo "⚠️ Дополнительные Python файлы не найдены"

cd ..

echo ""
echo "📊 Анализ загруженных файлов:"
echo "=============================="

echo "📁 Содержимое папки 'сервер':"
ls -la сервер/

echo ""
if [ -f "сервер/webhook_persistent_app.py" ]; then
    echo "✅ Основной файл приложения загружен"
    echo "📏 Размер: $(wc -l < сервер/webhook_persistent_app.py) строк"
    
    echo ""
    echo "🔍 Последние изменения в коде:"
    tail -n 20 сервер/webhook_persistent_app.py
else
    echo "❌ Основной файл приложения НЕ загружен"
fi

echo ""
if [ -f "сервер/webhook_data_accumulator.py" ]; then
    echo "✅ Аккумулятор данных загружен"
    echo "📏 Размер: $(wc -l < сервер/webhook_data_accumulator.py) строк"
else
    echo "❌ Аккумулятор данных НЕ загружен"
fi

echo ""
echo "📋 Backup файлы:"
ls -la сервер/webhook_persistent_app_*.py 2>/dev/null || echo "❌ Backup файлы не найдены"

echo ""
echo "📋 JSON файлы данных:"
ls -la сервер/*.json 2>/dev/null || echo "❌ JSON файлы не найдены"

echo ""
echo "📋 Логи:"
if [ -f "сервер/webhook_8502.log" ]; then
    echo "✅ webhook_8502.log ($(wc -l < сервер/webhook_8502.log) строк)"
else
    echo "❌ webhook_8502.log не найден"
fi

if [ -f "сервер/webhook_5000.log" ]; then
    echo "✅ webhook_5000.log ($(wc -l < сервер/webhook_5000.log) строк)"
else
    echo "❌ webhook_5000.log не найден"
fi

echo ""
echo "🎉 ЗАГРУЗКА ЗАВЕРШЕНА!"
echo "📁 Все файлы находятся в папке: ./сервер/"
echo "🔍 Для анализа можете изучить файлы локально"