#!/bin/bash

# Быстрое исправление основного файла приложения
# Выполнять с локального ПК

SERVER="root@217.114.1.117"
LOCAL_DIR="/mnt/f/Работа-Никита/Autosort_tovar"

echo "🔧 Быстрое исправление ModuleNotFoundError..."

# Загрузка только исправленного основного файла
echo "⬆️ Загрузка исправленного streamlit_modular_app.py..."
scp "$LOCAL_DIR/streamlit_modular_app.py" "$SERVER:/opt/inventory_system/"

# Перезапуск системы
echo "🔄 Перезапуск системы..."
ssh "$SERVER" << 'EOF'
    cd /opt/inventory_system
    
    # Остановка
    pkill -f "streamlit run streamlit_modular_app.py" || echo "Процесс не найден"
    sleep 3
    
    # Запуск
    source venv/bin/activate
    nohup streamlit run streamlit_modular_app.py --server.port=8501 --server.address=0.0.0.0 > streamlit.log 2>&1 &
    
    sleep 5
    ps aux | grep streamlit | grep -v grep || echo "❌ Не запущен"
EOF

echo "✅ Быстрое исправление завершено!"
echo "🌐 Проверьте: http://217.114.1.117:8501"