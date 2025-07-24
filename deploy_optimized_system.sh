#!/bin/bash

# Развертывание оптимизированной системы для обработки больших объемов данных
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "⚡ РАЗВЕРТЫВАНИЕ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ"
echo "📅 Время: $(date)"
echo ""
echo "🎯 ЦЕЛЬ: Оптимизация для обработки больших объемов данных"
echo ""

# Создаем резервную копию
echo "💾 Создание резервной копии текущей системы..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    if [ -f webhook_persistent_app.py ]; then
        cp webhook_persistent_app.py webhook_persistent_app_backup_optimized_$(date +%Y%m%d_%H%M%S).py
        echo '✅ Резервная копия основного приложения создана'
    fi
    
    if [ -f optimized_data_processor.py ]; then
        cp optimized_data_processor.py optimized_data_processor_backup_$(date +%Y%m%d_%H%M%S).py
        echo '✅ Резервная копия процессора создана'
    fi
"

echo ""
echo "📤 Загрузка оптимизированных файлов..."

# Загружаем новый оптимизированный процессор данных
scp optimized_data_processor.py "$USER@$SERVER:$REMOTE_PATH/" || {
    echo "❌ Ошибка загрузки optimized_data_processor.py"
    exit 1
}

# Загружаем обновленное основное приложение
scp webhook_app_enhanced_analytics.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py" || {
    echo "❌ Ошибка загрузки основного приложения"
    exit 1
}

echo "✅ Файлы загружены"

# Обновляем зависимости
echo ""
echo "📦 Проверка и установка зависимостей..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    source venv/bin/activate
    
    echo '🔧 Проверка зависимостей Python...'
    
    # Проверяем что все нужные библиотеки установлены
    python3 -c 'import pandas, numpy, streamlit, plotly, sqlite3' 2>/dev/null && {
        echo '✅ Все зависимости установлены'
    } || {
        echo '⚠️ Устанавливаем недостающие зависимости...'
        pip install pandas numpy streamlit plotly
    }
"

# Перезапускаем сервис
echo ""
echo "🔄 Перезапуск оптимизированного сервиса..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🔄 Остановка текущего сервиса...'
    systemctl stop webhook-analytics
    
    # Небольшая пауза для корректной остановки
    sleep 3
    
    echo '🚀 Запуск оптимизированного сервиса...'
    systemctl start webhook-analytics
    
    sleep 5
    
    echo '📊 Проверка статуса сервиса...'
    systemctl status webhook-analytics --no-pager | head -15
"

# Проверка результата
echo ""
echo "🔍 Тестирование оптимизированной системы..."

sleep 15

curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ ОПТИМИЗИРОВАННАЯ СИСТЕМА РАБОТАЕТ!"
    echo ""
    echo "🌐 Откройте: http://$SERVER:8502"
    echo ""
    echo "⚡ НОВЫЕ ВОЗМОЖНОСТИ ОПТИМИЗАЦИИ:"
    echo ""
    echo "   📊 УМНАЯ ОБРАБОТКА ДАННЫХ:"
    echo "   ✅ Автоматическое определение оптимального уровня агрегации"
    echo "   ✅ Кеширование результатов запросов (TTL 5 минут)"
    echo "   ✅ Агрегация на уровне базы данных для больших объемов"
    echo "   ✅ Умная выборка данных для визуализаций (max 10k точек)"
    echo ""
    echo "   🎯 АДАПТИВНЫЙ ИНТЕРФЕЙС:"
    echo "   ✅ Автоматическое упрощение графиков для >50k записей"
    echo "   ✅ Предупреждения о производительности"
    echo "   ✅ Ограничения на отображение таблиц (max 5k строк)"
    echo "   ✅ Показ статистики вместо детальных данных при больших объемах"
    echo ""
    echo "   💡 РЕКОМЕНДАЦИИ ПО АГРЕГАЦИИ:"
    echo "   ✅ Ежедневно: периоды ≤90 дней, данных ≤50k"
    echo "   ✅ Еженедельно: периоды ≤365 дней, данных ≤200k"
    echo "   ✅ Ежемесячно: большие периоды и объемы"
    echo ""
    echo "   🔧 ОПТИМИЗАЦИИ ПРОИЗВОДИТЕЛЬНОСТИ:"
    echo "   ✅ Системная/стратифицированная выборка для графиков"
    echo "   ✅ Кеширование запросов к базе данных"
    echo "   ✅ Оптимизированные SQL-запросы с GROUP BY"
    echo "   ✅ Индексы и агрегация на уровне БД"
    echo ""
    echo "📈 ПОДДЕРЖИВАЕМЫЕ ОБЪЕМЫ:"
    echo "   🟢 Отлично: до 50,000 записей (полная функциональность)"
    echo "   🟡 Хорошо: 50k-200k записей (упрощенные визуализации)"
    echo "   🟠 Удовлетворительно: 200k+ записей (агрегированные данные)"
    echo ""
    echo "💡 ДЛЯ МАКСИМАЛЬНОЙ ПРОИЗВОДИТЕЛЬНОСТИ:"
    echo "   - Используйте периоды 30-90 дней для детального анализа"
    echo "   - Период 'Весь период' автоматически использует агрегацию"
    echo "   - Большие таблицы ограничены первыми 5000 строк"
    echo "   - Кеш обновляется каждые 5 минут"
    
} || {
    echo "⚠️ Сервис еще запускается или есть проблемы"
    echo ""
    echo "🔍 ДИАГНОСТИКА:"
    echo ""
    ssh "$USER@$SERVER" "
        echo '📊 Проверка статуса сервиса:'
        systemctl status webhook-analytics --no-pager
        echo ''
        echo '📁 Проверка файлов:'
        ls -la $REMOTE_PATH/webhook_persistent_app.py
        ls -la $REMOTE_PATH/optimized_data_processor.py
        echo ''
        echo '📝 Последние 10 строк логов:'
        journalctl -u webhook-analytics --no-pager -n 10
    "
}

echo ""
echo "✅ РАЗВЕРТЫВАНИЕ ОПТИМИЗИРОВАННОЙ СИСТЕМЫ ЗАВЕРШЕНО!"
echo ""
echo "📚 ДОКУМЕНТАЦИЯ ПО ОПТИМИЗАЦИИ:"
echo "   - Система автоматически выбирает оптимальный режим работы"
echo "   - При больших объемах данных включается агрегация"
echo "   - Визуализации адаптируются под размер данных"
echo "   - Кеширование ускоряет повторные запросы"
echo ""
echo "🎛️ МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ:"
echo "   - Следите за предупреждениями в интерфейсе"
echo "   - Система покажет статистику вместо графиков при нагрузке"
echo "   - Используйте рекомендуемые периоды для анализа"