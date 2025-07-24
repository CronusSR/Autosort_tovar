#!/bin/bash

# Скрипт обновления раздела ADS расчета на сервере
# Обновляет основную функциональность ADS анализа

SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"
SERVICE_NAME="inventory-system.service"

echo "🚀 Обновление раздела ADS расчета..."
echo "📅 Время: $(date)"

# Создаем временную директорию
TEMP_DIR="/tmp/ads_update_$(date +%s)"
mkdir -p "$TEMP_DIR"

# Список файлов для обновления
echo "📦 Подготовка файлов..."

# Основной файл приложения
cp streamlit_modular_app.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_modular_app.py"

# Основные модули ADS
cp single_file_ads_processor.py "$TEMP_DIR/" 2>/dev/null && echo "✅ single_file_ads_processor.py"
cp ads_category_fix_improved.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_category_fix_improved.py"
cp streamlit_improved_ads_ui.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_improved_ads_ui.py"

# Дополнительные модули ADS
cp ads_category_fix.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_category_fix.py"
cp streamlit_category_ads_ui.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_category_ads_ui.py"
cp ads_price_fix.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_price_fix.py"
cp minimal_ads_zero_category_fix.py "$TEMP_DIR/" 2>/dev/null && echo "✅ minimal_ads_zero_category_fix.py"
cp streamlit_ads_zero_category_ui.py "$TEMP_DIR/" 2>/dev/null && echo "✅ streamlit_ads_zero_category_ui.py"

# Вспомогательные модули
cp integration_patch.py "$TEMP_DIR/" 2>/dev/null && echo "✅ integration_patch.py"
cp modular_inventory_system.py "$TEMP_DIR/" 2>/dev/null && echo "✅ modular_inventory_system.py"

# Утилиты ADS
cp ads_diagnostics.py "$TEMP_DIR/" 2>/dev/null && echo "✅ ads_diagnostics.py"
cp clean_duplicate_ads.py "$TEMP_DIR/" 2>/dev/null && echo "✅ clean_duplicate_ads.py"
cp apply_ads_update.py "$TEMP_DIR/" 2>/dev/null && echo "✅ apply_ads_update.py"

# Создаем архив
echo -e "\n📦 Создание архива..."
cd "$TEMP_DIR"
tar -czf ads_update.tar.gz * || { echo "❌ Ошибка создания архива"; exit 1; }

# Резервное копирование на сервере
echo -e "\n💾 Создание резервной копии..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    mkdir -p backups && 
    tar -czf backups/backup_ads_$(date +%Y%m%d_%H%M%S).tar.gz \
        streamlit_modular_app.py \
        single_file_ads_processor.py \
        ads_category_fix_improved.py \
        streamlit_improved_ads_ui.py \
        ads_category_fix.py \
        streamlit_category_ads_ui.py \
        ads_price_fix.py \
        minimal_ads_zero_category_fix.py \
        streamlit_ads_zero_category_ui.py \
        integration_patch.py \
        modular_inventory_system.py \
        ads_diagnostics.py \
        clean_duplicate_ads.py \
        apply_ads_update.py \
        2>/dev/null || echo 'Некоторые файлы не найдены'
"

# Загрузка на сервер
echo -e "\n📤 Загрузка обновлений..."
scp ads_update.tar.gz "$USER@$SERVER:$REMOTE_PATH/" || { echo "❌ Ошибка загрузки"; exit 1; }

# Распаковка и применение
echo -e "\n🔧 Применение обновлений..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    tar -xzf ads_update.tar.gz && 
    rm ads_update.tar.gz &&
    echo '✅ Файлы обновлены'
"

# Перезапуск сервиса
echo -e "\n🔄 Перезапуск сервиса..."
ssh "$USER@$SERVER" "
    systemctl restart $SERVICE_NAME && 
    sleep 5 &&
    systemctl status $SERVICE_NAME --no-pager | head -10
"

# Проверка доступности
echo -e "\n🔍 Проверка доступности..."
sleep 5
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8501" | grep -q "200" && {
    echo "✅ Приложение доступно на http://$SERVER:8501"
} || {
    echo "⚠️  Приложение может быть еще не готово. Проверьте через минуту."
}

# Очистка
rm -rf "$TEMP_DIR"

echo -e "\n✨ Обновление завершено!"
echo "📊 Проверьте раздел '📊 ADS расчет' в приложении"
echo "🔗 URL: http://$SERVER:8501"