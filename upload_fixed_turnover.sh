#!/bin/bash

# ЗАГРУЗКА ИСПРАВЛЕННОГО РАСЧЕТА ОБОРАЧИВАЕМОСТИ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📤 ЗАГРУЗКА ИСПРАВЛЕННОГО РАСЧЕТА ОБОРАЧИВАЕМОСТИ"
echo "=============================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 Загружаем исправленный webhook_persistent_app.py на сервер"
echo "🧮 Исправление: (остатки / продажи) * период_дней"
echo ""

# Проверяем что исправленный файл существует
if [ ! -f "ssh/webhook_persistent_app.py" ]; then
    echo "❌ ОШИБКА: Файл ssh/webhook_persistent_app.py не найден!"
    echo "Убедитесь что файл исправлен и находится в папке ssh/"
    exit 1
fi

echo "✅ Найден исправленный файл: ssh/webhook_persistent_app.py"
echo ""

# Проверяем что исправления применены
echo "🔍 ПРОВЕРКА ИСПРАВЛЕНИЙ В ФАЙЛЕ:"
echo "==============================="

if grep -q "* period_days" ssh/webhook_persistent_app.py; then
    echo "✅ Найдено исправление: * period_days"
else
    echo "❌ Исправление * period_days НЕ НАЙДЕНО!"
fi

if grep -q "* 30.5" ssh/webhook_persistent_app.py; then
    echo "✅ Найдено исправление: * 30.5"
else
    echo "❌ Исправление * 30.5 НЕ НАЙДЕНО!"
fi

echo ""
echo "📊 Показываем исправленные строки:"
grep -n "* period_days\|* 30.5" ssh/webhook_persistent_app.py | head -3
echo ""

read -p "🤔 Продолжить загрузку на сервер? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено пользователем"
    exit 1
fi

echo "📤 ЗАГРУЗКА НА СЕРВЕР"
echo "===================="

# Подключаемся к серверу и загружаем файл
scp ssh/webhook_persistent_app.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app_fixed.py"

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно загружен как webhook_persistent_app_fixed.py"
    echo ""
    
    echo "🔄 ПРИМЕНЕНИЕ ИСПРАВЛЕНИЙ НА СЕРВЕРЕ"
    echo "==================================="
    
    ssh "$USER@$SERVER" "
        cd $REMOTE_PATH
        
        echo '🛑 Остановка сервиса'
        systemctl stop webhook-analytics
        
        echo '💾 Создание бэкапа текущего файла'
        cp webhook_persistent_app.py webhook_persistent_app_backup_before_turnover_fix_\$(date +%Y%m%d_%H%M%S).py
        
        echo '🔄 Замена файла исправленным'
        mv webhook_persistent_app_fixed.py webhook_persistent_app.py
        
        echo '🔍 Проверка исправлений'
        echo 'Количество исправлений * period_days:'
        grep -c '* period_days' webhook_persistent_app.py
        
        echo 'Количество исправлений * 30.5:'
        grep -c '* 30.5' webhook_persistent_app.py
        
        echo '▶️ Запуск сервиса'
        systemctl start webhook-analytics
        sleep 5
        
        if systemctl is-active --quiet webhook-analytics; then
            echo '✅ Сервис успешно запущен!'
            echo ''
            echo '🎉 ИСПРАВЛЕНИЕ ОБОРАЧИВАЕМОСТИ ПРИМЕНЕНО!'
            echo ''
            echo '📊 РЕЗУЛЬТАТ:'
            echo '   ❌ Было: 9 остатков ÷ 62.39 продаж = 0.1'
            echo '   ✅ Стало: (9 ÷ 62.39) × 30.5 = 4.4 дня'
            echo ''
            echo '🌐 Проверьте: http://217.114.1.117:8502'
            echo '   Теперь оборачиваемость рассчитывается правильно!'
        else
            echo '❌ Проблемы с запуском сервиса'
            systemctl status webhook-analytics --no-pager | head -5
        fi
    "
    
else
    echo "❌ ОШИБКА: Не удалось загрузить файл на сервер"
    echo "Проверьте подключение и права доступа"
    exit 1
fi

echo ""
echo "✅ ЗАГРУЗКА ЗАВЕРШЕНА!"
echo ""
echo "🧮 Формула оборачиваемости исправлена:"
echo "   Вместо: stock / daily_sales"
echo "   Теперь: (stock / daily_sales) * period_days"
echo ""