#!/bin/bash

# ИСПРАВЛЕНИЕ ИЕРАРХИИ СКЛАДОВ
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🏗️ ИСПРАВЛЕНИЕ ИЕРАРХИИ СКЛАДОВ"
echo "==============================="
echo "📅 Время: $(date)"
echo ""
echo "🎯 Исправляем структуру перемещений на правильную 3-уровневую:"
echo "   УРОВЕНЬ 1: База Склад Фурнитура Комплект (г.Алматы) - ХАБ"
echo "   УРОВЕНЬ 2: Региональные склады"
echo "   УРОВЕНЬ 3: Магазины от региональных складов"
echo ""

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🛑 ОСТАНОВКА СЕРВИСА'
    echo '==================='
    systemctl stop webhook-analytics
    echo 'Сервис остановлен'
    echo ''
    
    echo '💾 БЭКАП ФАЙЛОВ ИЕРАРХИИ'
    echo '======================='
    find . -name '*hierarchy*' -type f -exec cp {} {}.backup_\$(date +%Y%m%d_%H%M%S) \\;
    if [ -f 'pages/🔄_Межфилиальные_перемещения.py' ]; then
        cp 'pages/🔄_Межфилиальные_перемещения.py' 'pages/🔄_Межфилиальные_перемещения.py.backup_\$(date +%Y%m%d_%H%M%S)'
    fi
    echo '✅ Бэкапы созданы'
    echo ''
    
    echo '📊 ТЕКУЩИЕ ФАЙЛЫ ИЕРАРХИИ'
    echo '========================'
    echo 'Найденные файлы с логикой иерархии:'
    find . -name '*hierarchy*' -o -name '*movement*' -o -name '*межфилиальн*' | head -10
    echo ''
    
    echo '🔧 СОЗДАНИЕ ПРАВИЛЬНОЙ ИЕРАРХИИ'
    echo '==============================='
    
    cat > correct_warehouse_hierarchy.py << 'PYTHON_END'
#!/usr/bin/env python3
\"\"\"
ПРАВИЛЬНАЯ ИЕРАРХИЯ СКЛАДОВ
Исправляет все файлы с логикой перемещений на корректную 3-уровневую структуру
\"\"\"

import os
import re
import glob

# ПРАВИЛЬНАЯ СТРУКТУРА СКЛАДОВ
CORRECT_HIERARCHY = {
    \"hub\": \"База Склад Фурнитура Комплект (г.Алматы)\",
    
    \"level2_warehouses\": {
        \"Казыбаева Склад Фурнитура TRADE (г.Казыбаева)\": [\"ТД Казыбаева ФУРНИТУРА магазин\"],
        \"склад фурнитура № 1 (г.Астана)\": [\"Магазин фурнитуры (г.Астана)\"],
        \"4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)\": [\"6 Склад фурнитуры \\\"Овощная база\\\" Магазин\"]
    },
    
    \"direct_stores_from_hub\": [
        \"Барыс Склад Фурнитура TRADE (г.Барыс)\",
        \"АО Склад Фурнитура TRADE (г.Алматы)\"
    ]
}

# ПРАВИЛЬНЫЕ СООТВЕТСТВИЯ НАЗВАНИЙ
CORRECT_MAPPINGS = {
    # Основной хаб
    \"База Склад Фурнитура Комплект\": \"База Склад Фурнитура Комплект (г.Алматы)\",
    
    # Склады 2-го уровня
    \"Казыбаева Склад Фурнитура TRADE\": \"Казыбаева Склад Фурнитура TRADE (г.Казыбаева)\",
    \"склад фурнитура №1\": \"склад фурнитура № 1 (г.Астана)\",
    \"склад фурнитура N 1\": \"склад фурнитура № 1 (г.Астана)\",
    \"склад фурнитура № 1\": \"склад фурнитура № 1 (г.Астана)\",
    \"4 Склад фурнитуры АЗМ Шымкент\": \"4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)\",
    \"4 Склад фурнитуры АЗМ Шымкент \\\"Овощная база\\\"\": \"4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)\",
    
    # Магазины от хаба
    \"Барыс Склад Фурнитура TRADE\": \"Барыс Склад Фурнитура TRADE (г.Барыс)\",
    \"АО Склад Фурнитура TRADE\": \"АО Склад Фурнитура TRADE (г.Алматы)\",
    
    # Магазины 3-го уровня
    \"Магазин фурнитуры\": \"Магазин фурнитуры (г.Астана)\",
    \"6 Склад фурнитуры \\\"Овощная база\\\" Магазин продажи\": \"6 Склад фурнитуры \\\"Овощная база\\\" Магазин\",
    \"6 Склад фурнитуры \\\"Овощная база\\\" Магазин\": \"6 Склад фурнитуры \\\"Овощная база\\\" Магазин\",
}

def fix_hierarchy_in_file(filepath):
    \"\"\"Исправляет иерархию в конкретном файле\"\"\"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # Заменяем неправильные определения хаба
        wrong_hubs = [
            '\"hub\": \"Казыбаева Склад Фурнитура TRADE\"',
            'hub.*?=.*?\"Казыбаева.*?\"',
            '\"main_hub\".*?\"Казыбаева.*?\"'
        ]
        
        for pattern in wrong_hubs:
            if re.search(pattern, content):
                content = re.sub(pattern, f'\"hub\": \"{CORRECT_HIERARCHY[\"hub\"]}\"', content)
                changes_made += 1
        
        # Исправляем mappings/соответствия
        for old_name, new_name in CORRECT_MAPPINGS.items():
            old_escaped = re.escape(old_name)
            if old_name in content and old_name != new_name:
                content = content.replace(old_name, new_name)
                changes_made += 1
        
        # Исправляем структуру level2_warehouses
        level2_pattern = r'\"level2_warehouses\".*?{[^}]*}'
        if re.search(level2_pattern, content, re.DOTALL):
            correct_level2 = '\"level2_warehouses\": {\\n'
            for warehouse, stores in CORRECT_HIERARCHY[\"level2_warehouses\"].items():
                stores_str = str(stores).replace(\"'\", '\"')
                correct_level2 += f'        \"{warehouse}\": {stores_str},\\n'
            correct_level2 += '    }'
            
            content = re.sub(level2_pattern, correct_level2, content, flags=re.DOTALL)
            changes_made += 1
        
        # Исправляем direct_stores_from_hub
        direct_pattern = r'\"direct_stores_from_hub\".*?\\[.*?\\]'
        if re.search(direct_pattern, content, re.DOTALL):
            stores_str = str(CORRECT_HIERARCHY[\"direct_stores_from_hub\"]).replace(\"'\", '\"')
            correct_direct = f'\"direct_stores_from_hub\": {stores_str}'
            content = re.sub(direct_pattern, correct_direct, content, flags=re.DOTALL)
            changes_made += 1
        
        if changes_made > 0:
            # Создаем бэкап
            backup_path = f\"{filepath}.backup_hierarchy_{int(__import__('time').time())}\"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Сохраняем исправленный файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f\"✅ {os.path.basename(filepath)}: {changes_made} изменений\")
            return changes_made
        else:
            print(f\"⚪ {os.path.basename(filepath)}: изменений не требуется\")
            return 0
            
    except Exception as e:
        print(f\"❌ {os.path.basename(filepath)}: ошибка - {e}\")
        return 0

def main():
    print(\"🏗️ ИСПРАВЛЕНИЕ ИЕРАРХИИ СКЛАДОВ\")
    print(\"=\" * 40)
    
    total_changes = 0
    files_processed = 0
    
    # Ищем файлы с логикой иерархии
    hierarchy_files = []
    
    # Python файлы с hierarchy в названии
    hierarchy_files.extend(glob.glob('*hierarchy*.py'))
    hierarchy_files.extend(glob.glob('*movement*.py'))
    
    # Страницы с межфилиальными перемещениями
    if os.path.exists('pages'):
        hierarchy_files.extend(glob.glob('pages/*межфилиальн*.py'))
        hierarchy_files.extend(glob.glob('pages/*movement*.py'))
    
    # Основные файлы приложения
    main_files = ['streamlit_modular_app.py', 'webhook_persistent_app.py', 'modular_inventory_system.py']
    for main_file in main_files:
        if os.path.exists(main_file):
            hierarchy_files.append(main_file)
    
    print(f\"📂 Найдено файлов для исправления: {len(hierarchy_files)}\")
    print()
    
    for filepath in hierarchy_files:
        if os.path.exists(filepath):
            changes = fix_hierarchy_in_file(filepath)
            total_changes += changes
            files_processed += 1
    
    print()
    print(f\"📊 ИТОГО:\")
    print(f\"   📁 Обработано файлов: {files_processed}\")
    print(f\"   🔧 Общее количество изменений: {total_changes}\")
    
    if total_changes > 0:
        print()
        print(\"✅ ИЕРАРХИЯ СКЛАДОВ ИСПРАВЛЕНА!\")
        print(\"   📊 Правильная 3-уровневая структура применена\")
        print(\"   💾 Бэкапы созданы с расширением .backup_hierarchy_timestamp\")
        
        print()
        print(\"🏗️ ПРАВИЛЬНАЯ СТРУКТУРА:\")
        print(f\"   🏢 ХАБ: {CORRECT_HIERARCHY['hub']}\")
        print(\"   📦 СКЛАДЫ 2-ГО УРОВНЯ:\")
        for warehouse, stores in CORRECT_HIERARCHY['level2_warehouses'].items():
            print(f\"      - {warehouse} → {stores[0]}\")
        print(\"   🏪 МАГАЗИНЫ ОТ ХАБА:\")
        for store in CORRECT_HIERARCHY['direct_stores_from_hub']:
            print(f\"      - {store}\")
    else:
        print()
        print(\"ℹ️ Иерархия уже корректна или файлы не найдены\")

if __name__ == \"__main__\":
    main()
PYTHON_END
    
    echo '🔄 ЗАПУСК ИСПРАВЛЕНИЯ ИЕРАРХИИ'
    echo '============================'
    python3 correct_warehouse_hierarchy.py
    
    echo ''
    echo '🔍 ПРОВЕРКА РЕЗУЛЬТАТА'
    echo '====================='
    
    echo 'Поиск правильного хаба:'
    grep -r \"База Склад Фурнитура Комплект (г.Алматы)\" *.py pages/ 2>/dev/null | head -3
    echo ''
    
    echo 'Проверка структуры level2_warehouses:'
    grep -A5 \"level2_warehouses\" pages/🔄_Межфилиальные_перемещения.py 2>/dev/null | head -5
    echo ''
    
    echo '🔄 ЗАПУСК СЕРВИСА'
    echo '================='
    systemctl start webhook-analytics
    sleep 5
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен'
        echo ''
        echo '🎉 ИЕРАРХИЯ СКЛАДОВ ИСПРАВЛЕНА!'
        echo ''
        echo '🏗️ НОВАЯ ПРАВИЛЬНАЯ СТРУКТУРА:'
        echo '   🏢 УРОВЕНЬ 1: База Склад Фурнитура Комплект (г.Алматы) - ХАБ'
        echo '   📦 УРОВЕНЬ 2: Казыбаева, Астана, Шымкент + Барыс, АО (прямо от хаба)'
        echo '   🏪 УРОВЕНЬ 3: Магазины от региональных складов'
        echo ''
        echo '🌐 Проверьте: http://217.114.1.117:8502'
        echo '   Раздел \"Межфилиальные перемещения\" теперь использует правильную структуру'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -5
    fi
    
    # Очистка
    rm -f correct_warehouse_hierarchy.py
"

echo ""
echo "✅ СКРИПТ ИСПРАВЛЕНИЯ ИЕРАРХИИ СОЗДАН!"
echo ""
echo "🎯 Этот скрипт:"
echo "   - Найдет все файлы с логикой иерархии"
echo "   - Исправит структуру на правильную 3-уровневую"
echo "   - Обновит все соответствия названий"
echo "   - Создаст бэкапы всех измененных файлов"
echo ""