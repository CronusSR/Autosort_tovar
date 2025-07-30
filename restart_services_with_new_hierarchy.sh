#!/bin/bash

# Быстрый перезапуск сервисов с обновленной иерархией складов
# Использовать: bash restart_services_with_new_hierarchy.sh

echo "🔄 ПЕРЕЗАПУСК СЕРВИСОВ С НОВОЙ ИЕРАРХИЕЙ СКЛАДОВ"
echo "================================================"

echo "1️⃣ Остановка всех Python процессов..."
pkill -f streamlit 2>/dev/null || echo "   ℹ️  Streamlit процессы не найдены"
pkill -f python 2>/dev/null || echo "   ℹ️  Python процессы не найдены"

echo "2️⃣ Ожидание завершения процессов..."
sleep 3

echo "3️⃣ Проверка обновленной иерархии..."
cd /opt/inventory_system

python3 -c "
try:
    from hierarchical_movement_system import HierarchicalMovementSystem
    hms = HierarchicalMovementSystem()
    hierarchy = hms.warehouse_hierarchy
    
    main_hubs = [name for name, info in hierarchy.items() if info.get('level') == 1]
    print(f'✅ Главные хабы: {main_hubs}')
    
    if 'База Склад Фурнитура Комплект' in main_hubs:
        print('✅ ИЕРАРХИЯ ОБНОВЛЕНА ПРАВИЛЬНО!')
    else:
        print('❌ ОШИБКА: Иерархия не обновлена')
        exit(1)
        
    print(f'📊 Всего складов в иерархии: {len(hierarchy)}')
    
except Exception as e:
    print(f'❌ Ошибка загрузки иерархии: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "4️⃣ Запуск основного Streamlit приложения..."
    nohup streamlit run streamlit_modular_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
    
    echo "5️⃣ Ожидание запуска сервиса..."
    sleep 5
    
    echo "6️⃣ Проверка доступности веб-интерфейса..."
    if curl -s http://localhost:8501 | grep -q "Streamlit\|html"; then
        echo "✅ Веб-интерфейс доступен на http://localhost:8501"
    else
        echo "⚠️  Веб-интерфейс может быть еще недоступен, проверьте через несколько секунд"
    fi
    
    echo ""
    echo "🎉 ПЕРЕЗАПУСК ЗАВЕРШЕН!"
    echo "📋 Основные изменения:"
    echo "   🏢 База Склад Фурнитура Комплект - главный хаб"
    echo "   📦 Казыбаева, Астана, Шымкент - склады 2-го уровня"
    echo "   🏪 Барыс, АО - магазины напрямую от хаба"
    echo ""
    echo "🔍 Для диагностики используйте:"
    echo "   python3 diagnose_hierarchy_on_server.py"
    echo ""
    echo "📊 Проверить логи:"
    echo "   tail -f streamlit.log"
    
else
    echo "❌ ОШИБКА: Не удалось загрузить обновленную иерархию"
    echo "💡 Проверьте что файл hierarchical_movement_system.py скопирован правильно"
    exit 1
fi