#!/bin/bash

# Скрипт обновления раздела ADS анализа на сервере
# Автор: Assistant
# Дата: $(date +%Y-%m-%d)

SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"
SERVICE_NAME="inventory-system.service"

echo "🚀 Начинаем обновление раздела ADS анализа..."
echo "📅 Время: $(date)"

# Создаем временную директорию для архива
TEMP_DIR="/tmp/ads_update_$(date +%s)"
mkdir -p "$TEMP_DIR"

# Список файлов для обновления ADS функционала
echo "📦 Подготовка файлов для обновления..."

# Основные файлы приложения
cp streamlit_modular_app.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_modular_app.py"

# Модули ADS анализа
cp ads_category_fix.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_category_fix.py"
cp streamlit_category_ads_ui.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_category_ads_ui.py"
cp integration_patch.py "$TEMP_DIR/" 2>/dev/null && echo "✅ integration_patch.py"
cp streamlit_deficit_money_update.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_deficit_money_update.py"

# Дополнительные модули для ADS
cp subcategory_abc.py "$TEMP_DIR/" 2>/dev/null && echo "✅ subcategory_abc.py"
cp modular_inventory_system.py "$TEMP_DIR/" 2>/dev/null && echo "✅ modular_inventory_system.py"

# Страницы с ADS функционалом
mkdir -p "$TEMP_DIR/pages"
cp "pages/🔄_Межфилиальные_перемещения.py" "$TEMP_DIR/pages/" 2>/dev/null && echo "✅ Страница межфилиальных перемещений"

# ADS конфигурации если есть
mkdir -p "$TEMP_DIR/ads"
cp ads/*.json "$TEMP_DIR/ads/" 2>/dev/null && echo "✅ ADS конфигурации"

# Создаем архив
echo -e "\n📦 Создание архива..."
cd "$TEMP_DIR"
tar -czf ads_update.tar.gz * || { echo "❌ Ошибка создания архива"; exit 1; }

# Создаем резервную копию на сервере
echo -e "\n💾 Создание резервной копии на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    mkdir -p backups && 
    tar -czf backups/backup_ads_$(date +%Y%m%d_%H%M%S).tar.gz \
        streamlit_modular_app.py \
        ads_category_fix.py \
        streamlit_category_ads_ui.py \
        integration_patch.py \
        streamlit_deficit_money_update.py \
        subcategory_abc.py \
        modular_inventory_system.py \
        pages/ \
        ads/ \
        2>/dev/null || echo 'Некоторые файлы не найдены для резервного копирования'
"

# Загружаем архив на сервер
echo -e "\n📤 Загрузка обновлений на сервер..."
scp ads_update.tar.gz "$USER@$SERVER:$REMOTE_PATH/" || { echo "❌ Ошибка загрузки"; exit 1; }

# Распаковываем и применяем обновления
echo -e "\n🔧 Применение обновлений..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    tar -xzf ads_update.tar.gz && 
    rm ads_update.tar.gz &&
    echo '✅ Файлы обновлены'
"

# Перезапускаем сервис
echo -e "\n🔄 Перезапуск сервиса..."
ssh "$USER@$SERVER" "
    systemctl restart $SERVICE_NAME && 
    sleep 5 &&
    systemctl status $SERVICE_NAME --no-pager | head -10
"

# Проверяем доступность приложения
echo -e "\n🔍 Проверка доступности приложения..."
sleep 5
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8501" | grep -q "200" && {
    echo "✅ Приложение доступно на http://$SERVER:8501"
} || {
    echo "⚠️  Приложение может быть еще не готово. Проверьте через минуту."
}

# Очистка временных файлов
echo -e "\n🧹 Очистка временных файлов..."
rm -rf "$TEMP_DIR"

echo -e "\n✨ Обновление ADS анализа завершено!"
echo "📊 Проверьте раздел 'Анализ ADS по магазинам' в приложении"
echo "🔗 URL: http://$SERVER:8501"