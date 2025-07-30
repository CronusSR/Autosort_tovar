#!/bin/bash
# Быстрая проверка синхронизации локальных файлов с сервером

echo "⚡ Быстрая проверка синхронизации"
echo "================================"

echo "📊 Локальные файлы:"
echo "-------------------"
for file in webhook_receiver.py webhook_persistent_app.py webhook_data_accumulator.py requirements.txt; do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        lines=$(wc -l < "$file")
        modified=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
        modified_date=$(date -d "@$modified" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "$modified" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "unknown")
        
        # Проверяем версию в webhook_receiver.py
        version=""
        if [ "$file" = "webhook_receiver.py" ]; then
            if grep -q "version.*2\.1.*раздельные папки" "$file" 2>/dev/null; then
                version=" [v2.1 раздельные папки]"
            elif grep -q "version.*2\.0" "$file" 2>/dev/null; then
                version=" [v2.0 ZIP support]"
            fi
        fi
        
        echo "✅ $file: $size байт, $lines строк, изменен $modified_date$version"
    else
        echo "❌ $file: НЕ НАЙДЕН"
    fi
done

echo ""
echo "🌐 Сервер (API проверка):"
echo "-------------------------"

# Проверяем версию через API
api_response=$(curl -s http://217.114.1.117:5000/webhook/status 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$api_response" ]; then
    api_version=$(echo "$api_response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null)
    api_status=$(echo "$api_response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
    api_files=$(echo "$api_response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('total_files', 'unknown'))" 2>/dev/null)
    
    echo "✅ API доступен: $api_status"
    echo "📊 Версия: $api_version"
    echo "📁 Файлов в системе: $api_files"
    
    # Проверяем главную страницу (есть только в v2.1)
    main_page=$(curl -s http://217.114.1.117:5000/ 2>/dev/null)
    if echo "$main_page" | grep -q "404 Not Found" 2>/dev/null; then
        echo "🏠 Главная страница: ❌ 404 (версия 2.0)"
    elif echo "$main_page" | grep -q "service.*Webhook" 2>/dev/null; then
        echo "🏠 Главная страница: ✅ работает (версия 2.1)"
    else
        echo "🏠 Главная страница: ❓ неизвестно"
    fi
    
    # Проверяем структуру папок через SSH (быстро)
    folder_structure=$(ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/ 2>/dev/null | grep -E '(sales|stock|archive)'" 2>/dev/null)
    if [ ! -z "$folder_structure" ]; then
        echo "📁 Раздельные папки: ✅ найдены"
        echo "$folder_structure" | while read line; do
            echo "   $line"
        done
    else
        echo "📁 Раздельные папки: ❌ не найдены"
    fi
    
else
    echo "❌ API недоступен или не отвечает"
fi

echo ""
echo "📋 Статус синхронизации:"
echo "========================"

# Анализируем состояние
local_version=""
if [ -f "webhook_receiver.py" ]; then
    if grep -q "version.*2\.1.*раздельные папки" "webhook_receiver.py" 2>/dev/null; then
        local_version="2.1"
    elif grep -q "version.*2\.0" "webhook_receiver.py" 2>/dev/null; then
        local_version="2.0"
    fi
fi

server_version=""
if [ ! -z "$api_version" ]; then
    if [[ "$api_version" == *"2.1"* ]]; then
        server_version="2.1"
    elif [[ "$api_version" == *"2.0"* ]]; then
        server_version="2.0"
    fi
fi

echo "🔍 Локальная версия: ${local_version:-неизвестно}"
echo "🌐 Серверная версия: ${server_version:-неизвестно}"

if [ "$local_version" = "$server_version" ] && [ ! -z "$local_version" ]; then
    echo "✅ СИНХРОНИЗИРОВАНО - версии совпадают"
elif [ "$local_version" = "2.1" ] && [ "$server_version" = "2.0" ]; then
    echo "🔄 ТРЕБУЕТСЯ ОБНОВЛЕНИЕ СЕРВЕРА"
    echo "💡 Выполните: ./sync_with_server.sh up или используйте apply_webhook_update.txt"
elif [ "$local_version" = "2.0" ] && [ "$server_version" = "2.1" ]; then
    echo "📥 СЕРВЕР НОВЕЕ - обновите локальные файлы"
    echo "💡 Выполните: ./sync_with_server.sh down"
else
    echo "❓ СОСТОЯНИЕ НЕЯСНО - требуется детальная проверка"
    echo "💡 Выполните: ./compare_local_vs_server.sh"
fi

echo ""
echo "⚡ Быстрая проверка завершена!"
echo ""
echo "🔗 Доступные команды:"
echo "   ./compare_local_vs_server.sh  - детальное сравнение"
echo "   ./sync_with_server.sh down    - загрузить с сервера"
echo "   ./sync_with_server.sh up      - отправить на сервер"
echo "   ./sync_with_server.sh test    - протестировать API"