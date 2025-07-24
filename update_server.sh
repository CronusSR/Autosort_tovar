#!/bin/bash

# Скрипт для обновления системы на сервере
# Выполнять с локального ПК

SERVER="root@217.114.1.117"
SERVER_DIR="/opt/inventory_system"
LOCAL_DIR="/mnt/f/Работа-Никита/Autosort_tovar"

echo "🚀 Начинаем обновление системы на сервере..."

# 1. Создание архива с обновленными файлами
echo "📦 Создание архива с обновленными файлами..."
cd "$LOCAL_DIR"
tar -czf system_update.tar.gz \
  "pages/🔄_Межфилиальные_перемещения.py" \
  streamlit_modular_app.py \
  modular_inventory_system.py \
  --exclude="venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc"

# 2. Загрузка архива на сервер
echo "⬆️ Загрузка файлов на сервер..."
scp system_update.tar.gz "$SERVER:/tmp/"

# 3. Выполнение команд на сервере
echo "🔧 Обновление системы на сервере..."
ssh "$SERVER" << 'EOF'
    echo "⏹️ Остановка текущей системы..."
    # Остановка streamlit (но не убиваем процесс, чтобы supervisor мог перезапустить)
    pkill -f "streamlit run streamlit_modular_app.py" || echo "Процесс уже остановлен"
    
    echo "💾 Создание бэкапа..."
    cd /opt/inventory_system
    cp -r pages pages_backup_$(date +%Y%m%d_%H%M%S)
    cp streamlit_modular_app.py streamlit_modular_app.py.backup_$(date +%Y%m%d_%H%M%S)
    cp modular_inventory_system.py modular_inventory_system.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "modular_inventory_system.py не найден"
    
    echo "📂 Распаковка новых файлов..."
    cd /tmp
    tar -xzf system_update.tar.gz
    
    echo "🔄 Замена файлов..."
    # Копируем новые файлы
    cp -r pages/* /opt/inventory_system/pages/ 2>/dev/null || mkdir -p /opt/inventory_system/pages && cp -r pages/* /opt/inventory_system/pages/
    cp streamlit_modular_app.py /opt/inventory_system/ 2>/dev/null || echo "streamlit_modular_app.py не найден в архиве"
    cp modular_inventory_system.py /opt/inventory_system/ 2>/dev/null || echo "modular_inventory_system.py не найден в архиве"
    
    # Устанавливаем права
    chown -R root:root /opt/inventory_system/
    chmod +x /opt/inventory_system/*.py
    
    echo "🗑️ Очистка временных файлов..."
    rm -f /tmp/system_update.tar.gz
    rm -rf /tmp/pages
    rm -f /tmp/streamlit_modular_app.py
    rm -f /tmp/modular_inventory_system.py
    
    echo "🔄 Перезапуск системы..."
    # Активируем виртуальное окружение и запускаем
    cd /opt/inventory_system
    source venv/bin/activate
    
    # Supervisor должен автоматически перезапустить процесс
    supervisorctl restart streamlit_app 2>/dev/null || {
        echo "Supervisor не найден, запускаем вручную..."
        nohup streamlit run streamlit_modular_app.py --server.port=8501 --server.address=0.0.0.0 > streamlit.log 2>&1 &
    }
    
    sleep 5
    
    echo "✅ Проверка статуса..."
    ps aux | grep streamlit | grep -v grep
    
    echo "🌐 Система должна быть доступна по адресу: http://217.114.1.117:8501"
EOF

# 4. Очистка локальных временных файлов
echo "🧹 Очистка локальных файлов..."
rm -f "$LOCAL_DIR/system_update.tar.gz"

echo "✅ Обновление завершено!"
echo "🌐 Проверьте работу системы: http://217.114.1.117:8501"
echo "📋 Особенно проверьте таб 'ADS анализ' в разделе 'Межфилиальные перемещения'"