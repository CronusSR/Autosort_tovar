#!/bin/bash

# ИСПРАВЛЕНИЕ ФОРМУЛЫ ОБОРАЧИВАЕМОСТИ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🔧 ИСПРАВЛЕНИЕ ФОРМУЛЫ ОБОРАЧИВАЕМОСТИ"
echo "===================================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 Исправляем: (остатки/продажи) → (остатки/продажи)*30.5"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '💾 БЭКАП ФАЙЛОВ'
    echo '==============='
    cp turnover_report_generator.py turnover_report_generator_backup_\$(date +%Y%m%d_%H%M%S).py
    cp automated_report_system.py automated_report_system_backup_\$(date +%Y%m%d_%H%M%S).py
    echo '✅ Бэкапы созданы'
    echo ''
    
    echo '🔧 ИСПРАВЛЕНИЕ turnover_report_generator.py'
    echo '=========================================='
    
    # Исправляем формулу в turnover_report_generator.py
    sed -i 's/turnover_days = (cat_stock \* 30) \/ cat_sales_cost/turnover_days = (cat_stock * 30.5) \/ cat_sales_cost/g' turnover_report_generator.py
    sed -i 's/total_turnover_days = (total_stock \* 30) \/ total_sales_cost/total_turnover_days = (total_stock * 30.5) \/ total_sales_cost/g' turnover_report_generator.py
    sed -i 's/# Период = 30 дней (месяц)/# Период = 30.5 дней (средний месяц)/g' turnover_report_generator.py
    
    echo '✅ Исправлен turnover_report_generator.py'
    
    echo ''
    echo '🔧 ИСПРАВЛЕНИЕ automated_report_system.py'
    echo '========================================'
    
    # Исправляем period_days в automated_report_system.py
    sed -i 's/period_days = 30/period_days = 30.5/g' automated_report_system.py
    sed -i 's/, 30$/, 30.5/g' automated_report_system.py
    
    echo '✅ Исправлен automated_report_system.py'
    
    echo ''
    echo '🔍 ПРОВЕРКА ИЗМЕНЕНИЙ'
    echo '===================='
    
    echo 'turnover_report_generator.py:'
    grep -n '30\.5' turnover_report_generator.py | head -3
    echo ''
    
    echo 'automated_report_system.py:'
    grep -n '30\.5' automated_report_system.py | head -3
    echo ''
    
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ФОРМУЛА ОБОРАЧИВАЕМОСТИ ИСПРАВЛЕНА!'
        echo ''
        echo '📊 ИЗМЕНЕНИЯ:'
        echo '   ❌ Старая формула: (остатки/продажи)'
        echo '   ✅ Новая формула: (остатки/продажи)*30.5'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
        echo '   Теперь оборачиваемость рассчитывается правильно'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
"

echo ""
echo "✅ СКРИПТ ИСПРАВЛЕНИЯ ФОРМУЛЫ СОЗДАН!"
echo ""
echo "🎯 Исправлена формула оборачиваемости:"
echo "   Период расчета: 30 → 30.5 дней"
echo "   Учитывает реальную длину месяца"
echo ""