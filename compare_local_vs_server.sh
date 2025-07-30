#!/bin/bash
# Скрипт для сравнения локальных файлов с файлами на сервере

echo "🔍 Сравнение локальных файлов с серверными"
echo "=========================================="

# Создаем временную папку для сравнения
TEMP_DIR="temp_server_comparison"
mkdir -p "$TEMP_DIR"

echo "📥 Загружаем файлы с сервера для сравнения..."

# Загружаем основные файлы с сервера
scp root@217.114.1.117:/opt/inventory_system/webhook_receiver.py "$TEMP_DIR/" 2>/dev/null || echo "❌ webhook_receiver.py не загружен"
scp root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py "$TEMP_DIR/" 2>/dev/null || echo "❌ webhook_persistent_app.py не загружен"  
scp root@217.114.1.117:/opt/inventory_system/webhook_data_accumulator.py "$TEMP_DIR/" 2>/dev/null || echo "❌ webhook_data_accumulator.py не загружен"
scp root@217.114.1.117:/opt/inventory_system/requirements.txt "$TEMP_DIR/" 2>/dev/null || echo "❌ requirements.txt не загружен"

echo ""
echo "📊 Результаты сравнения:"
echo "========================="

# Функция для сравнения файлов
compare_file() {
    local filename="$1"
    local local_file="$filename"
    local server_file="$TEMP_DIR/$filename"
    
    echo ""
    echo "🔍 Файл: $filename"
    echo "-------------------"
    
    if [ ! -f "$local_file" ]; then
        echo "❌ Локальный файл НЕ НАЙДЕН"
        return
    fi
    
    if [ ! -f "$server_file" ]; then
        echo "❌ Серверный файл НЕ НАЙДЕН"
        return
    fi
    
    # Размеры файлов
    local_size=$(wc -c < "$local_file" 2>/dev/null || echo "0")
    server_size=$(wc -c < "$server_file" 2>/dev/null || echo "0")
    
    echo "📏 Размеры:"
    echo "   Локально:  $local_size байт"
    echo "   На сервере: $server_size байт"
    
    # Количество строк
    local_lines=$(wc -l < "$local_file" 2>/dev/null || echo "0")
    server_lines=$(wc -l < "$server_file" 2>/dev/null || echo "0")
    
    echo "📄 Строки:"
    echo "   Локально:  $local_lines строк"
    echo "   На сервере: $server_lines строк"
    
    # MD5 хеши для точного сравнения
    if command -v md5sum >/dev/null 2>&1; then
        local_md5=$(md5sum "$local_file" | cut -d' ' -f1)
        server_md5=$(md5sum "$server_file" | cut -d' ' -f1)
        
        echo "🔐 MD5 хеши:"
        echo "   Локально:  $local_md5"
        echo "   На сервере: $server_md5"
        
        if [ "$local_md5" = "$server_md5" ]; then
            echo "✅ ФАЙЛЫ ИДЕНТИЧНЫ"
        else
            echo "❌ ФАЙЛЫ ОТЛИЧАЮТСЯ"
            
            # Показываем различия
            echo ""
            echo "📋 Основные различия:"
            if command -v diff >/dev/null 2>&1; then
                diff_output=$(diff "$local_file" "$server_file" | head -10)
                if [ ! -z "$diff_output" ]; then
                    echo "$diff_output"
                    echo "..."
                else
                    echo "   (различия в кодировке или пробелах)"
                fi
            fi
        fi
    else
        # Если md5sum недоступен, сравниваем размеры
        if [ "$local_size" = "$server_size" ] && [ "$local_lines" = "$server_lines" ]; then
            echo "✅ РАЗМЕРЫ И СТРОКИ СОВПАДАЮТ (вероятно идентичны)"
        else
            echo "❌ РАЗМЕРЫ ИЛИ СТРОКИ ОТЛИЧАЮТСЯ"
        fi
    fi
    
    # Проверяем дату модификации локального файла
    if [ -f "$local_file" ]; then
        local_date=$(stat -c %Y "$local_file" 2>/dev/null || stat -f %m "$local_file" 2>/dev/null || echo "unknown")
        if [ "$local_date" != "unknown" ]; then
            local_date_readable=$(date -d "@$local_date" 2>/dev/null || date -r "$local_date" 2>/dev/null || echo "unknown")
            echo "📅 Локальный файл изменен: $local_date_readable"
        fi
    fi
}

# Сравниваем основные файлы
compare_file "webhook_receiver.py"
compare_file "webhook_persistent_app.py" 
compare_file "webhook_data_accumulator.py"
compare_file "requirements.txt"

echo ""
echo "🌐 Дополнительная информация с сервера:"
echo "======================================="

# Получаем информацию о версии с сервера
echo "📊 Текущая версия API на сервере:"
curl -s http://217.114.1.117:5000/webhook/status | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f\"   Версия: {data.get('version', 'неизвестно')}\")
    print(f\"   Статус: {data.get('status', 'неизвестно')}\")
    print(f\"   Всего файлов: {data.get('total_files', 'неизвестно')}\")
    if 'structure' in data:
        print(f\"   Папка загрузок: {data['structure'].get('upload_directory', 'неизвестно')}\")
except:
    print('   Ошибка получения данных')
" 2>/dev/null || echo "   Не удалось получить информацию"

echo ""
echo "📁 Структура папок на сервере:"
ssh root@217.114.1.117 "cd /opt/inventory_system && find webhook_uploads -type d 2>/dev/null" 2>/dev/null || echo "   Не удалось получить структуру папок"

echo ""
echo "⏰ Процессы webhook на сервере:"
ssh root@217.114.1.117 "ps aux | grep -E '(webhook_receiver|webhook_persistent)' | grep -v grep" 2>/dev/null || echo "   Не удалось получить информацию о процессах"

echo ""
echo "🧹 Очистка временных файлов..."
rm -rf "$TEMP_DIR"

echo ""
echo "📋 РЕЗЮМЕ СРАВНЕНИЯ:"
echo "===================="
echo ""

# Анализируем общее состояние
if [ -f "webhook_receiver.py" ] && [ -f "$TEMP_DIR/webhook_receiver.py" ] 2>/dev/null; then
    echo "🔍 Анализ синхронизации:"
    
    # Проверяем наличие ключевых изменений в локальном файле
    if grep -q "version.*2\.1.*раздельные папки" "webhook_receiver.py" 2>/dev/null; then
        echo "   ✅ Локальный файл содержит обновления (версия 2.1)"
    else
        echo "   ❌ Локальный файл не содержит обновлений"
    fi
    
    # Проверяем API версию
    api_version=$(curl -s http://217.114.1.117:5000/webhook/status | python3 -c "import json, sys; print(json.load(sys.stdin).get('version', ''))" 2>/dev/null)
    if [[ "$api_version" == *"2.1"* ]]; then
        echo "   ✅ Сервер использует новую версию (2.1)"
    elif [[ "$api_version" == *"2.0"* ]]; then
        echo "   ❌ Сервер использует старую версию (2.0)"
    else
        echo "   ❓ Не удалось определить версию сервера"
    fi
    
    echo ""
    echo "💡 Рекомендации:"
    if [[ "$api_version" == *"2.0"* ]] && grep -q "version.*2\.1" "webhook_receiver.py" 2>/dev/null; then
        echo "   🔄 Нужно применить обновления на сервере"
        echo "   📋 Используйте: ./sync_with_server.sh up"
        echo "   📋 Или: apply_webhook_update.txt"
    elif [[ "$api_version" == *"2.1"* ]]; then
        echo "   ✅ Сервер обновлен, файлы синхронизированы"
    else
        echo "   🔍 Требуется дополнительная проверка"
    fi
else
    echo "❌ Не удалось выполнить полное сравнение"
fi

echo ""
echo "✅ Сравнение завершено!"