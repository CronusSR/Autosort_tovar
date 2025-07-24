#!/bin/bash

# Развертывание системы с быстрой загрузкой
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🚀 РАЗВЕРТЫВАНИЕ СИСТЕМЫ С БЫСТРОЙ ЗАГРУЗКОЙ"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка оптимизированной версии..."
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
echo "✅ СИСТЕМА С БЫСТРОЙ ЗАГРУЗКОЙ РАЗВЕРНУТА!"
echo ""
echo "⚡ ОПТИМИЗАЦИИ:"
echo "   ✅ @st.cache_data для build_category_tree()"
echo "   ✅ Выборка 20,000 записей для больших данных (>50,000)"
echo "   ✅ Ограничение глубины категорий до 3 уровней"
echo "   ✅ Показ только топ-20 категорий на уровень"
echo "   ✅ Показ только топ-5 товаров в категории"
echo ""
echo "🎯 РЕШАЕТ ПРОБЛЕМУ: 'очень долго грузит'"
echo ""
echo "🌐 Откройте: http://$SERVER:8502"