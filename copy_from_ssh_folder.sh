#\!/bin/bash
# Простое копирование файлов из папки ssh на сервер

echo "📤 Копирование файлов из папки ssh на сервер"
echo "============================================="

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"
SOURCE_DIR="ssh/"

# Основные файлы для копирования
FILES=(
    "webhook_persistent_app.py"
    "webhook_data_accumulator.py"
    "modular_inventory_system.py"
    "webhook_receiver.py"
)

echo "📋 Копируем файлы из папки ssh/..."

for file in "${FILES[@]}"; do
    if [ -f "${SOURCE_DIR}${file}" ]; then
        echo "   📄 Копируем ${file}..."
        scp "${SOURCE_DIR}${file}" "${SERVER}:${TARGET_DIR}${file}"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ ${file} скопирован успешно"
        else
            echo "   ❌ Ошибка копирования ${file}"
        fi
    else
        echo "   ⚠️  Файл ${file} не найден в папке ssh/"
    fi
done

echo ""
echo "🔄 Перезапускаем webhook приложение на сервере..."
ssh "${SERVER}" "cd ${TARGET_DIR} && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'Запущен с PID: \$\!'"

echo ""
echo "✅ ГОТОВО\! Файлы из папки ssh скопированы на сервер"
echo ""
echo "📋 Для проверки логов:"
echo "   ssh ${SERVER} 'tail -f ${TARGET_DIR}webhook_8502.log'"
echo ""
echo "🌐 Приложение доступно на порту 8502"
