#!/bin/bash
# Скрипт исправления зависимостей и запуска системы

echo "🔧 Исправление системы анализа складов"
echo "===================================="

# Работаем на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "📋 Проверяем текущее состояние..."
echo "Содержимое папки:"
ls -la

echo ""
echo "🔍 Проверяем установленные пакеты Python..."
python3 -m pip list | grep -E "(flask|streamlit|pandas)"

echo ""
echo "📝 Обновляем requirements.txt..."

# Создаем обновленный requirements.txt
cat > requirements.txt << 'REQ_EOF'
# Система анализа складов - все зависимости
# Основные фреймворки
streamlit>=1.28.0
flask>=2.3.0
gunicorn>=21.0.0

# Обработка данных
pandas>=2.0.0
numpy>=1.24.0

# Excel файлы
openpyxl>=3.1.0
xlrd>=2.0.1

# Визуализация и графики
plotly>=5.15.0

# Веб и API
requests>=2.31.0
python-dotenv>=1.0.0

# База данных
sqlite3

# Дополнительные библиотеки для аналитики
scipy>=1.11.0
python-dateutil>=2.8.2

# Логирование
loguru>=0.7.0

# Утилиты
pillow>=10.0.0
kaleido>=0.2.1
REQ_EOF

echo "✅ requirements.txt обновлен"

echo ""
echo "🔧 Устанавливаем зависимости..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "🔍 Проверяем установку критичных пакетов..."
python3 -c "
try:
    import flask
    print('✅ Flask установлен:', flask.__version__)
except ImportError:
    print('❌ Flask НЕ установлен')

try:
    import streamlit
    print('✅ Streamlit установлен:', streamlit.__version__)
except ImportError:
    print('❌ Streamlit НЕ установлен')

try:
    import pandas
    print('✅ Pandas установлен:', pandas.__version__)
except ImportError:
    print('❌ Pandas НЕ установлен')

try:
    import plotly
    print('✅ Plotly установлен:', plotly.__version__)
except ImportError:
    print('❌ Plotly НЕ установлен')
"

echo ""
echo "🔍 Проверяем синтаксис основных файлов..."

echo "Проверка webhook_receiver.py:"
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_receiver.py', doraise=True)
    print('✅ webhook_receiver.py - синтаксис OK')
except Exception as e:
    print(f'❌ webhook_receiver.py - ошибка: {e}')
"

echo "Проверка webhook_persistent_app.py:"
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_persistent_app.py', doraise=True)
    print('✅ webhook_persistent_app.py - синтаксис OK')
except Exception as e:
    print(f'❌ webhook_persistent_app.py - ошибка: {e}')
"

echo ""
echo "🛑 Останавливаем старые процессы..."
pkill -f "webhook_receiver"
pkill -f "webhook_persistent_app"
pkill -f "streamlit.*8502"
pkill -f "flask.*5000"
sleep 3

echo ""
echo "🚀 Запускаем вебхук сервер (порт 5000)..."
nohup python3 webhook_receiver.py > webhook_5000.log 2>&1 &
WEBHOOK_PID=$!
echo "Webhook сервер запущен с PID: $WEBHOOK_PID"

echo ""
echo "🚀 Запускаем Streamlit интерфейс (порт 8502)..."
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
STREAMLIT_PID=$!
echo "Streamlit запущен с PID: $STREAMLIT_PID"

echo ""
echo "⏳ Ждем запуска сервисов..."
sleep 5

echo ""
echo "🔍 Проверяем запущенные процессы..."
ps aux | grep -E "(webhook_receiver|streamlit.*8502)" | grep -v grep

echo ""
echo "🔍 Проверяем открытые порты..."
netstat -tulpn | grep -E ":(5000|8502)"

echo ""
echo "📋 Последние строки логов..."
echo "=== webhook_5000.log ==="
tail -n 10 webhook_5000.log 2>/dev/null || echo "Лог пустой"

echo ""
echo "=== webhook_8502.log ==="
tail -n 10 webhook_8502.log 2>/dev/null || echo "Лог пустой"

echo ""
echo "🌐 Тестируем доступность сервисов..."

echo "Тест вебхука (порт 5000):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/webhook/status || echo "Недоступен"

echo ""
echo "Тест Streamlit (порт 8502):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8502 || echo "Недоступен"

echo ""
echo "✅ СИСТЕМА ЗАПУЩЕНА!"
echo "🌐 Вебхук: http://217.114.1.117:5000"
echo "📊 Интерфейс: http://217.114.1.117:8502"
echo ""
echo "📋 Для мониторинга:"
echo "   tail -f webhook_5000.log"
echo "   tail -f webhook_8502.log"

REMOTE_EOF

echo ""
echo "🎉 Исправление системы завершено!"
echo ""
echo "🔗 Ссылки для проверки:"
echo "   Вебхук статус: http://217.114.1.117:5000/webhook/status"
echo "   Интерфейс: http://217.114.1.117:8502"
echo ""
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_5000.log'"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"