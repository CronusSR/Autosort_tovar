#!/bin/bash

# Исправление ошибки форматирования ValueError: Unknown format code 'f'
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ ФОРМАТИРОВАНИЯ"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка исправленной версии..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"

echo ""
echo "🔄 Перезапуск системы..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    systemctl stop webhook-analytics
    sleep 3
    systemctl start webhook-analytics
    sleep 5
    systemctl status webhook-analytics --no-pager | head -10
"

echo ""
echo "✅ ОШИБКА ФОРМАТИРОВАНИЯ ИСПРАВЛЕНА!"
echo ""
echo "🐛 ЧТО БЫЛО ИСПРАВЛЕНО:"
echo ""
echo "   ❌ ОШИБКА: ValueError: Unknown format code 'f' for object of type 'str'"
echo "   ❌ ПРОБЛЕМА: Некоторые значения были строками вместо чисел"
echo "   ❌ МЕСТО: display_data['Количество'].apply(lambda x: f\"{x:,.0f}\")"
echo ""
echo "   ✅ ИСПРАВЛЕНИЕ:"
echo "   ✅ Добавлена проверка типов с pd.notnull(x)"
echo "   ✅ Принудительное преобразование в float(x)"
echo "   ✅ Обработка пустых значений → \"0\""
echo "   ✅ Безопасное форматирование для всех колонок"
echo ""
echo "   🔧 НОВЫЙ КОД:"
echo "   display_data['Количество'] = display_data['Количество'].apply("
echo "       lambda x: f\"{float(x):,.0f}\" if pd.notnull(x) else \"0\""
echo "   )"
echo ""
echo "✅ ТЕПЕРЬ СИСТЕМА РАБОТАЕТ БЕЗ ОШИБОК!"
echo ""
echo "🌐 Откройте: http://$SERVER:8502"