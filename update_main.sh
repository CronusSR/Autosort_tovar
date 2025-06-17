#!/bin/bash
# 📤 ЗАГРУЖАЕМ ОТСУТСТВУЮЩИЙ ФАЙЛ movement_recommendations_streamlit.py

REMOTE_USER="root"
REMOTE_HOST="217.114.1.117"
REMOTE_PATH="/opt/inventory_system"

echo "📤 ЗАГРУЖАЕМ movement_recommendations_streamlit.py"
echo "=============================================="

# Проверяем наличие файла локально
if [ ! -f "movement_recommendations_streamlit.py" ]; then
    echo "❌ ФАЙЛ movement_recommendations_streamlit.py НЕ НАЙДЕН!"
    echo ""
    echo "🔍 Проверяем что есть в текущей папке:"
    ls -la *movement* 2>/dev/null || echo "Файлов с movement в имени не найдено"
    echo ""
    echo "📁 Все Python файлы:"
    ls -la *.py | head -10
    exit 1
fi

echo "✅ Файл найден локально"

# Показываем размер и дату изменения
echo "📊 Информация о файле:"
ls -lh movement_recommendations_streamlit.py
echo ""

# Загружаем на сервер
echo "📤 Загружаем файл на сервер..."
if scp -o StrictHostKeyChecking=no movement_recommendations_streamlit.py "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"; then
    echo "✅ Файл загружен успешно!"
else
    echo "❌ Ошибка загрузки файла"
    exit 1
fi

# Проверяем что файл появился на сервере
echo ""
echo "🔍 Проверяем файл на сервере..."
ssh "$REMOTE_USER@$REMOTE_HOST" bash << 'EOF'
cd /opt/inventory_system

if [ -f "movement_recommendations_streamlit.py" ]; then
    echo "✅ Файл найден на сервере:"
    ls -lh movement_recommendations_streamlit.py
    
    echo ""
    echo "📝 Проверяем содержимое (первые 10 строк):"
    head -10 movement_recommendations_streamlit.py
else
    echo "❌ Файл не найден на сервере!"
    exit 1
fi
EOF

echo ""
echo "🔄 ПЕРЕЗАПУСКАЕМ СЕРВИС..."
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl restart inventory-system.service"

echo "⏳ Ждем запуска (15 секунд)..."
sleep 15

echo ""
echo "🔍 ПРОВЕРЯЕМ РЕЗУЛЬТАТ:"
ssh "$REMOTE_USER@$REMOTE_HOST" bash << 'EOF'
echo "🔧 Статус сервиса:"
if systemctl is-active --quiet inventory-system.service; then
    echo "  ✅ Сервис работает"
else
    echo "  ❌ Сервис не работает"
    echo ""
    echo "📜 Последние ошибки:"
    journalctl -u inventory-system.service --no-pager -n 10 | grep -E "(Error|error|ModuleNotFoundError)" || echo "Ошибок импорта не найдено"
fi

echo ""
echo "🌐 Проверка порта:"
if netstat -tlnp 2>/dev/null | grep ':8501' >/dev/null; then
    echo "  ✅ Порт 8501 открыт"
else
    echo "  ❌ Порт 8501 не прослушивается"
fi

echo ""
echo "📜 Последние 5 логов:"
journalctl -u inventory-system.service --no-pager -n 5
EOF

echo ""
echo "🌐 ТЕСТИРУЕМ ПРИЛОЖЕНИЕ:"
if curl -s --connect-timeout 10 "http://$REMOTE_HOST:8501" >/dev/null 2>&1; then
    echo "✅ Приложение отвечает!"
    echo ""
    echo "🎉 ФАЙЛ ЗАГРУЖЕН И ПРИЛОЖЕНИЕ РАБОТАЕТ!"
    echo "====================================="
    echo ""
    echo "🌐 Откройте: http://$REMOTE_HOST:8501"
    echo ""
    echo "✅ Теперь страница '🚚 Рекомендации по перемещениям' должна работать"
else
    echo "⚠️ Приложение пока не отвечает"
    echo ""
    echo "🔧 Дополнительная диагностика:"
    echo "   ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u inventory-system.service -f'"
fi

echo ""
echo "📊 ИТОГ:"
echo "  📤 Файл: movement_recommendations_streamlit.py загружен"
echo "  🌐 URL: http://$REMOTE_HOST:8501"
echo "  📋 Проверьте работу страницы рекомендаций"