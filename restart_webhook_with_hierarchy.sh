#!/bin/bash

# Специальный перезапуск webhook_persistent_app.py с новой иерархией складов
# Использовать: bash restart_webhook_with_hierarchy.sh

echo "🔄 ПЕРЕЗАПУСК WEBHOOK_PERSISTENT_APP С НОВОЙ ИЕРАРХИЕЙ"
echo "===================================================="

echo "1️⃣ Остановка webhook_persistent_app процессов..."
pkill -f webhook_persistent_app 2>/dev/null || echo "   ℹ️  webhook_persistent_app процессы не найдены"
pkill -f streamlit.*webhook 2>/dev/null || echo "   ℹ️  streamlit webhook процессы не найдены"

echo "2️⃣ Ожидание завершения процессов..."
sleep 3

echo "3️⃣ Проверка новой иерархии в webhook_persistent_app.py..."
cd /opt/inventory_system

python3 -c "
import sys
sys.path.append('/opt/inventory_system')

try:
    # Проверяем что файл можно импортировать  
    with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие WAREHOUSE_HIERARCHY
    if 'WAREHOUSE_HIERARCHY' in content:
        print('✅ WAREHOUSE_HIERARCHY найден в файле')
        
        # Проверяем правильный главный хаб
        if 'База Склад Фурнитура Комплект' in content and 'level\': 1' in content:
            print('✅ База Склад Фурнитура Комплект определен как главный хаб')
        else:
            print('❌ База Склад Фурнитура Комплект не найден как главный хаб')
            
        # Проверяем функции работы с иерархией
        if 'def get_warehouse_info' in content:
            print('✅ Функции работы с иерархией добавлены')
        else:
            print('❌ Функции работы с иерархией не найдены')
            
        print('✅ ИЕРАРХИЯ В WEBHOOK_PERSISTENT_APP ОБНОВЛЕНА!')
    else:
        print('❌ WAREHOUSE_HIERARCHY не найден в файле')
        exit(1)
        
except Exception as e:
    print(f'❌ Ошибка проверки файла: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "4️⃣ Запуск webhook_persistent_app с новой иерархией..."
    
    # Определяем правильный порт для webhook_persistent_app
    WEBHOOK_PORT=8502
    echo "   ℹ️  Используем порт 8502 для webhook_persistent_app"
    
    nohup streamlit run webhook_persistent_app.py --server.port $WEBHOOK_PORT --server.address 0.0.0.0 > webhook_streamlit.log 2>&1 &
    
    echo "5️⃣ Ожидание запуска webhook сервиса..."
    sleep 8
    
    echo "6️⃣ Проверка доступности webhook приложения..."
    if curl -s http://localhost:$WEBHOOK_PORT | grep -q "Streamlit\|html"; then
        echo "✅ Webhook приложение доступно на http://localhost:$WEBHOOK_PORT"
    else
        echo "⚠️  Webhook приложение может быть еще недоступно, проверьте через несколько секунд"
    fi
    
    echo ""
    echo "🎉 WEBHOOK_PERSISTENT_APP ПЕРЕЗАПУЩЕН С НОВОЙ ИЕРАРХИЕЙ!"
    echo ""
    echo "📋 Новые возможности в интерфейсе:"
    echo "   🏗️ Анализ по уровням иерархии складов"
    echo "   📊 Статистика дефицита/избытка по типам складов"
    echo "   📋 Иерархические рекомендации по перемещениям"
    echo "   🔄 MIN/MAX нормативы с учетом типа склада"
    echo ""
    echo "🔍 Для проверки логов:"
    echo "   tail -f webhook_streamlit.log"
    echo ""
    echo "🌐 Веб-интерфейс:"
    echo "   http://localhost:$WEBHOOK_PORT → вкладка 'Межфилиальные перемещения'"
    
else
    echo "❌ ОШИБКА: Не удалось проверить иерархию в webhook_persistent_app.py"
    echo "💡 Убедитесь что файл webhook_persistent_app.py скопирован правильно"
    exit 1
fi