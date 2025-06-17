#!/bin/bash
# 📤 ЗАГРУЖАЕМ ВСЕ РЕАЛЬНЫЕ МОДУЛИ

REMOTE_USER="root"
REMOTE_HOST="217.114.1.117"
REMOTE_PATH="/opt/inventory_system"

echo "📤 ЗАГРУЗКА ВСЕХ МОДУЛЕЙ НА СЕРВЕР"
echo "================================="

# Список ВСЕХ возможных модулей
all_modules=(
    "subcategory_abc.py"
    "integration_patch.py"
    "json_download_fix.py"
    "movement_recommendations.py"
    "price_integration_fix.py"
    "streamlit_deficit_money_update.py"
    "ads_category_fix.py"
    "streamlit_category_ads_ui.py"
    "ads_category_fix_improved.py"
    "streamlit_improved_ads_ui.py"
    "complete_price_integration.py"
    "max_stock_feature.py"
    "warehouse_analysis.py"
    "warehouse_ui.py"
    "real_fix_for_your_system.py"
    "column_names_fix_correct.py"
    "telegram_bot_modular.py"
)

echo "🔍 ПРОВЕРЯЕМ ЛОКАЛЬНЫЕ ФАЙЛЫ:"
echo "============================="

found_files=()
missing_files=()

for file in "${all_modules[@]}"; do
    if [ -f "$file" ]; then
        found_files+=("$file")
        echo "  ✅ $file"
    else
        missing_files+=("$file")
        echo "  ❌ $file (не найден)"
    fi
done

echo ""
echo "📊 СТАТИСТИКА:"
echo "  ✅ Найдено: ${#found_files[@]} файлов"
echo "  ❌ Отсутствует: ${#missing_files[@]} файлов"
echo ""

if [ ${#found_files[@]} -eq 0 ]; then
    echo "❌ НИ ОДНОГО МОДУЛЯ НЕ НАЙДЕНО!"
    echo ""
    echo "🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:"
    echo "  - Вы находитесь не в папке с проектом"
    echo "  - Файлы имеют другие имена"
    echo "  - Модули еще не созданы"
    echo ""
    echo "📁 Текущая папка: $(pwd)"
    echo "📄 Python файлы в текущей папке:"
    ls -la *.py 2>/dev/null || echo "   Нет Python файлов"
    exit 1
fi

echo "❓ ОТСУТСТВУЮЩИЕ МОДУЛИ:"
if [ ${#missing_files[@]} -gt 0 ]; then
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    echo ""
fi

read -p "Продолжить загрузку ${#found_files[@]} найденных модулей? (y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    exit 0
fi

echo ""
echo "📤 ЗАГРУЖАЕМ МОДУЛИ НА СЕРВЕР:"
echo "============================="

uploaded=0
failed=0

for file in "${found_files[@]}"; do
    echo "📤 Загружаем: $file"
    if scp -o StrictHostKeyChecking=no "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"; then
        ((uploaded++))
        echo "   ✅ Успешно"
    else
        ((failed++))
        echo "   ❌ Ошибка"
    fi
    echo ""
done

echo "📊 РЕЗУЛЬТАТ ЗАГРУЗКИ:"
echo "  ✅ Загружено: $uploaded файлов"
echo "  ❌ Ошибок: $failed файлов"
echo ""

if [ $uploaded -eq 0 ]; then
    echo "❌ НИ ОДИН ФАЙЛ НЕ ЗАГРУЖЕН!"
    exit 1
fi

echo "🔄 ПЕРЕЗАПУСКАЕМ СЕРВИС..."
ssh "$REMOTE_USER@$REMOTE_HOST" "systemctl restart inventory-system.service"

echo "⏳ Ждем запуска сервиса (15 секунд)..."
sleep 15

echo ""
echo "🔍 ПРОВЕРЯЕМ РЕЗУЛЬТАТ:"
echo "======================"

ssh "$REMOTE_USER@$REMOTE_HOST" bash << 'EOF'
cd /opt/inventory_system

echo "📁 Python файлы на сервере:"
ls -la *.py | head -15

echo ""
echo "🔧 Статус сервиса:"
if systemctl is-active --quiet inventory-system.service; then
    echo "  ✅ РАБОТАЕТ"
else
    echo "  ❌ НЕ РАБОТАЕТ"
    echo ""
    echo "📜 Ошибки в логах:"
    journalctl -u inventory-system.service --no-pager -n 10 | grep -i error || echo "Нет ошибок в последних 10 записях"
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
echo "🎯 ФИНАЛЬНАЯ ПРОВЕРКА:"
echo "====================="

# Простая проверка HTTP
if curl -s --connect-timeout 10 "http://$REMOTE_HOST:8501" >/dev/null 2>&1; then
    echo "✅ Приложение отвечает!"
    echo "🌐 Откройте: http://$REMOTE_HOST:8501"
else
    echo "⚠️ Приложение не отвечает"
    echo ""
    echo "🔧 Попробуйте:"
    echo "  1. Подождите еще 30 секунд и обновите страницу"
    echo "  2. Проверьте логи: ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u inventory-system.service -f'"
    echo "  3. Перезапустите: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl restart inventory-system.service'"
fi

echo ""
echo "📊 ИТОГОВАЯ СТАТИСТИКА:"
echo "  📤 Загружено модулей: $uploaded"
echo "  🖥️ Сервер: $REMOTE_HOST"
echo "  🌐 URL: http://$REMOTE_HOST:8501"
echo ""

if [ $uploaded -ge 5 ]; then
    echo "🎉 ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!"
else
    echo "⚠️ Загружено мало модулей - возможны ошибки"
fi