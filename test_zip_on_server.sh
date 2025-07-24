#!/bin/bash

# Тестирование ZIP системы на работающем сервере
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🧪 ТЕСТИРОВАНИЕ ZIP НА РАБОЧЕМ СЕРВЕРЕ"
echo "📅 Время: $(date)"
echo ""

# Проверяем что работает на сервере
echo "🔍 Проверка работающих сервисов:"
echo "Port 8501: $(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8501")"
echo "Port 8502: $(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502")"
echo "Port 5000: $(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:5000")"

echo ""
echo "📋 Проверка процессов на сервере:"
ssh "$USER@$SERVER" "
    echo '=== Запущенные Streamlit процессы ==='
    ps aux | grep streamlit | grep -v grep
    
    echo ''
    echo '=== Запущенные Python процессы ==='
    ps aux | grep python | grep -v grep | head -5
    
    echo ''
    echo '=== Systemd сервисы ==='
    systemctl list-units --type=service --state=running | grep -E '(webhook|inventory|streamlit)'
    
    echo ''
    echo '=== Проверка портов ==='
    netstat -tlnp | grep -E ':(5000|8501|8502)'
"

echo ""
echo "📁 Загрузка ZIP файла на сервер для тестирования:"

# Загружаем ZIP файл на сервер
scp "Выгрузка JSON.zip" "$USER@$SERVER:$REMOTE_PATH/test_zip.zip" || {
    echo "❌ Ошибка загрузки ZIP файла"
    exit 1
}

echo "✅ ZIP файл загружен на сервер"

# Загружаем тестовый скрипт
scp test_zip_processing.py "$USER@$SERVER:$REMOTE_PATH/" || {
    echo "❌ Ошибка загрузки тестового скрипта"
    exit 1
}

# Загружаем обработчик ZIP
scp webhook_zip_handler.py "$USER@$SERVER:$REMOTE_PATH/" || {
    echo "❌ Ошибка загрузки обработчика ZIP"
    exit 1
}

echo ""
echo "🧪 Запуск тестирования на сервере:"

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔧 Активация виртуального окружения...'
    source venv/bin/activate
    
    echo '🧪 Запуск теста ZIP обработки...'
    python3 -c \"
import sys
sys.path.append('.')
from webhook_zip_handler import WebhookZipHandler

# Тестируем ZIP файл
with open('test_zip.zip', 'rb') as f:
    zip_data = f.read()

handler = WebhookZipHandler(upload_dir='./webhook_uploads')
result = handler.process_zip_file(zip_data, 'test_zip.zip')

print('📊 Результат обработки ZIP:')
print(f'   Статус: {result.get(\"status\")}')
print(f'   Файлов: {result.get(\"files_processed\", 0)}')
print(f'   Записей: {result.get(\"total_records\", 0)}')

if result.get('status') == 'success':
    print('✅ ZIP успешно обработан на сервере!')
else:
    print(f'❌ Ошибка: {result.get(\"message\")}')
\"
    
    echo ''
    echo '📁 Проверка созданных файлов:'
    ls -la webhook_uploads/*.json 2>/dev/null | wc -l | xargs echo 'Создано JSON файлов:'
    ls -la webhook_uploads/*.json 2>/dev/null | head -5
"

echo ""
echo "🔄 Проверка интеграции с накопителем данных:"

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    source venv/bin/activate
    
    python3 -c \"
import sys
sys.path.append('.')

try:
    from webhook_data_accumulator import WebhookDataAccumulator
    accumulator = WebhookDataAccumulator()
    
    summary = accumulator.get_data_summary()
    print('📊 Статистика накопителя:')
    print(f'   Продажи: {summary[\"sales\"][\"total_records\"]} записей')
    print(f'   Остатки: {summary[\"stock\"][\"total_records\"]} записей')
    print(f'   Период: {summary[\"sales\"].get(\"first_date\", \"Н/Д\")} - {summary[\"sales\"].get(\"last_date\", \"Н/Д\")}')
    print('✅ Накопитель данных работает!')
    
except ImportError:
    print('⚠️  Накопитель данных не найден')
except Exception as e:
    print(f'❌ Ошибка накопителя: {e}')
\"
"

echo ""
echo "🎯 ИТОГИ ТЕСТИРОВАНИЯ НА СЕРВЕРЕ:"
echo "Проверьте результаты выше для определения следующих шагов."