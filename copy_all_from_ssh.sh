#\!/bin/bash
# Копирование ВСЕХ файлов из папки ssh на сервер

echo "📤 Копирование ВСЕХ файлов из папки ssh на сервер"
echo "================================================"

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"
SOURCE_DIR="ssh/"

echo "📋 Получаем список всех файлов в папке ssh/..."

# Получаем список всех .py файлов
PY_FILES=($(find "${SOURCE_DIR}" -name "*.py" -type f -exec basename {} \;))

echo "Найдено ${#PY_FILES[@]} Python файлов:"
for file in "${PY_FILES[@]}"; do
    echo "   - $file"
done

echo ""
echo "📤 Копируем все Python файлы..."

# Копируем все .py файлы
for file in "${PY_FILES[@]}"; do
    if [ -f "${SOURCE_DIR}${file}" ]; then
        echo "   📄 Копируем ${file}..."
        scp "${SOURCE_DIR}${file}" "${SERVER}:${TARGET_DIR}${file}"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ ${file} скопирован"
        else
            echo "   ❌ Ошибка копирования ${file}"
        fi
    fi
done

echo ""
echo "📋 Копируем также скрипты (.sh файлы)..."

# Получаем список всех .sh файлов
SH_FILES=($(find "${SOURCE_DIR}" -name "*.sh" -type f -exec basename {} \;))

for file in "${SH_FILES[@]}"; do
    if [ -f "${SOURCE_DIR}${file}" ]; then
        echo "   📄 Копируем ${file}..."
        scp "${SOURCE_DIR}${file}" "${SERVER}:${TARGET_DIR}${file}"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ ${file} скопирован"
        else
            echo "   ❌ Ошибка копирования ${file}"
        fi
    fi
done

echo ""
echo "📋 Проверяем что основной файл webhook_persistent_app.py скопировался..."
ssh "${SERVER}" "ls -la ${TARGET_DIR}webhook_persistent_app.py"

echo ""
echo "🔄 Перезапускаем webhook приложение на сервере..."
ssh "${SERVER}" "cd ${TARGET_DIR} && pkill -f webhook_persistent_app && sleep 3 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'Запущен с PID: \$\!'"

echo ""
echo "✅ ГОТОВО\! ВСЕ файлы из папки ssh скопированы на сервер"
echo ""
echo "📊 Статистика:"
echo "   - Python файлов: ${#PY_FILES[@]}"
echo "   - Shell скриптов: ${#SH_FILES[@]}"
echo ""
echo "📋 Для проверки логов:"
echo "   ssh ${SERVER} 'tail -f ${TARGET_DIR}webhook_8502.log'"
echo ""
echo "🌐 Приложение доступно на порту 8502"
