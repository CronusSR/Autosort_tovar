#!/bin/bash
# Скрипт для применения исправления формулы оборачиваемости на сервере

echo "🔧 Применение исправления формулы оборачиваемости"
echo "================================================="
echo ""

# Создаем резервную копию локально
echo "📋 Создаем резервную копию..."
cp webhook_persistent_app.py webhook_persistent_app_backup_$(date +%Y%m%d_%H%M%S).py

# Копируем в ssh2 папку для отслеживания
mkdir -p ssh2
cp webhook_persistent_app.py ssh2/

echo "✅ Локальное исправление готово"
echo ""
echo "📊 Изменения:"
echo "   • Формула изменена с: (stock_quantity / daily_sales) * period_days"
echo "   • На новую формулу: (stock_quantity / total_sales) * 30.5"
echo "   • Добавлена обратная совместимость для daily_sales"
echo ""

# Синхронизация с сервером
echo "🌐 Синхронизация с сервером..."
echo "==============================="

# Отправляем файл на сервер
echo "📤 Отправляем исправленный файл на сервер..."
scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/ 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно загружен на сервер"
    
    # Перезапускаем Streamlit приложение
    echo "🔄 Перезапускаем Streamlit приложение..."
    ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f 'streamlit run webhook_persistent_app.py' && sleep 3 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Приложение перезапущено"
        
        # Ждем несколько секунд и проверяем
        echo "⏳ Проверяем запуск приложения (10 секунд)..."
        sleep 10
        
        # Проверяем доступность приложения
        response=$(curl -s -o /dev/null -w "%{http_code}" http://217.114.1.117:8502 2>/dev/null)
        if [ "$response" = "200" ]; then
            echo "✅ Приложение успешно запущено и доступно"
        else
            echo "⚠️ Приложение может еще загружаться (код ответа: $response)"
        fi
    else
        echo "⚠️ Не удалось перезапустить приложение автоматически"
        echo ""
        echo "💡 Выполните вручную на сервере:"
        echo "   ssh root@217.114.1.117"
        echo "   cd /opt/inventory_system"
        echo "   pkill -f 'streamlit run webhook_persistent_app.py'"
        echo "   nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &"
    fi
else
    echo "❌ Ошибка при загрузке на сервер"
    echo "💡 Попробуйте использовать: ./sync_with_server.sh up"
fi

echo ""
echo "✅ Исправление применено!"
echo ""
echo "🔍 Проверьте работу:"
echo "   • Локально: функция calculate_turnover в webhook_persistent_app.py:96"
echo "   • На сервере: http://217.114.1.117:8502"
echo "   • Раздел 'Анализ оборачиваемости' теперь использует формулу:"
echo "     (остатки / продажи) * 30.5"
echo ""
echo "📁 Резервная копия: webhook_persistent_app_backup_*.py"