#!/bin/bash

# Скрипт для исправления ошибки ModuleNotFoundError на сервере
# Выполнять с локального ПК

SERVER="root@217.114.1.117"
SERVER_DIR="/opt/inventory_system"
LOCAL_DIR="/mnt/f/Работа-Никита/Autosort_tovar"

echo "🚀 Исправляем ModuleNotFoundError на сервере..."

# 1. Создание архива с исправленными файлами
echo "📦 Создание архива с исправленными файлами..."
cd "$LOCAL_DIR"
tar -czf system_fix.tar.gz \
  streamlit_modular_app.py \
  modular_inventory_system.py \
  "pages/🔄_Межфилиальные_перемещения.py" \
  warehouse_analysis_fixed_mapping.py \
  real_fix_for_your_system.py \
  --exclude="venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc"

echo "📋 Архив содержит:"
tar -tzf system_fix.tar.gz

# 2. Загрузка архива на сервер
echo "⬆️ Загрузка файлов на сервер..."
scp system_fix.tar.gz "$SERVER:/tmp/"

# 3. Выполнение команд на сервере
echo "🔧 Исправление системы на сервере..."
ssh "$SERVER" << 'EOF'
    echo "💾 Создание бэкапа..."
    cd /opt/inventory_system
    mkdir -p backup_$(date +%Y%m%d_%H%M%S)
    cp *.py backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || echo "Некоторые .py файлы отсутствуют"
    cp -r pages backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || echo "pages директория отсутствует"
    
    echo "📂 Распаковка исправленных файлов..."
    cd /tmp
    tar -xzf system_fix.tar.gz
    
    echo "🔄 Обновление файлов..."
    # Копируем исправленные файлы
    cp streamlit_modular_app.py /opt/inventory_system/
    cp modular_inventory_system.py /opt/inventory_system/
    cp warehouse_analysis_fixed_mapping.py /opt/inventory_system/ 2>/dev/null || echo "warehouse_analysis_fixed_mapping.py не найден в архиве"
    cp real_fix_for_your_system.py /opt/inventory_system/ 2>/dev/null || echo "real_fix_for_your_system.py не найден в архиве"
    
    # Обновляем pages
    mkdir -p /opt/inventory_system/pages
    cp -r pages/* /opt/inventory_system/pages/ 2>/dev/null || echo "pages не найдены в архиве"
    
    # Устанавливаем права
    chown -R root:root /opt/inventory_system/
    chmod +x /opt/inventory_system/*.py
    
    echo "🗑️ Очистка временных файлов..."
    rm -f /tmp/system_fix.tar.gz
    rm -f /tmp/*.py
    rm -rf /tmp/pages
    
    echo "🔄 Перезапуск системы..."
    cd /opt/inventory_system
    
    # Остановка текущего процесса
    pkill -f "streamlit run streamlit_modular_app.py" || echo "Процесс не найден"
    
    sleep 3
    
    # Запуск с виртуальным окружением
    source venv/bin/activate
    
    # Проверка доступности модулей
    python3 -c "import streamlit, pandas, numpy, plotly" && echo "✅ Основные модули доступны" || echo "❌ Проблемы с модулями"
    
    # Запуск системы
    nohup streamlit run streamlit_modular_app.py --server.port=8501 --server.address=0.0.0.0 > streamlit.log 2>&1 &
    
    echo "⏳ Ожидание запуска..."
    sleep 10
    
    echo "✅ Проверка статуса..."
    ps aux | grep streamlit | grep -v grep || echo "❌ Streamlit не запущен"
    
    echo "📋 Последние строки лога:"
    tail -20 streamlit.log
    
    echo "🌐 Система должна быть доступна: http://217.114.1.117:8501"
EOF

# 4. Очистка локальных файлов
echo "🧹 Очистка локальных файлов..."
rm -f "$LOCAL_DIR/system_fix.tar.gz"

echo "✅ Исправление завершено!"
echo ""
echo "🔍 Проверьте работу системы:"
echo "   1. Откройте: http://217.114.1.117:8501"
echo "   2. Убедитесь что главная страница загружается без ошибок"
echo "   3. Перейдите в 'Межфилиальные перемещения' → 'ADS анализ'"
echo "   4. Загрузите файл продаж и проверьте ADS в шт/день"