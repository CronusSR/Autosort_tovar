#!/bin/bash

# Развертывание простого ABC анализа
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🚀 РАЗВЕРТЫВАНИЕ ПРОСТОГО ABC АНАЛИЗА"
echo "📅 Время: $(date)"
echo ""

echo "📤 Загрузка простой версии ABC анализа..."
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
echo "✅ ПРОСТОЙ ABC АНАЛИЗ РАЗВЕРНУТ!"
echo ""
echo "📊 ЧТО ИЗМЕНИЛОСЬ:"
echo "   ❌ Убрана сложная иерархическая навигация"
echo "   ❌ Убраны раскрывающиеся строки и кнопки"
echo "   ❌ Убрано управление состоянием (session state)"
echo ""
echo "✅ НОВЫЙ ПРОСТОЙ ИНТЕРФЕЙС:"
echo "   📊 Простая таблица основных категорий"
echo "   📈 Круговая диаграмма ABC распределения"
echo "   📊 Столбчатая диаграмма топ-10 категорий"
echo "   📋 Чистая таблица с экспортом в CSV"
echo ""
echo "🎯 ОСНОВАНО НА ПЕРВОЙ КАТЕГОРИИ ИЗ ПутьКатегорий"
echo "   - Например: 'Мебельная фурнитура/Ручки/Крючки/' → 'Мебельная фурнитура'"
echo "   - ABC анализ: A=80%, B=15%, C=5%"
echo ""
echo "🌐 Откройте: http://$SERVER:8502"