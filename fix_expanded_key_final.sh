#\!/bin/bash
# Финальное исправление expanded_key в webhook_persistent_app.py

echo "🔧 Исправление ошибки expanded_key"
echo "=================================="

# Используем версию из ssh папки
cp ssh/webhook_persistent_app.py webhook_persistent_app.py

# Создаем Python скрипт для исправления
cat > /tmp/fix_expanded_final.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

file_path = 'webhook_persistent_app.py'

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Найдем контекст где используется expanded_key и добавим его определение
# Ищем блок кода с is_expanded = expanded_key
pattern = r'(\s+)# Кнопка раскрытия/сворачивания\n(\s+)is_expanded = expanded_key in st\.session_state\.expanded_categories'

# Проверяем, есть ли такой паттерн
if 'is_expanded = expanded_key in st.session_state.expanded_categories' in content:
    # Добавляем определение expanded_key перед использованием
    # Ищем цикл for который должен определять item и idx
    for_loop_pattern = r'(for (?:idx, )?item in (?:enumerate\()?abc_data(?:\[:20\])?\)?:)'
    
    # Заменяем паттерн, добавляя определение expanded_key
    replacement = r'\1\n                    # Определяем ключ для expanded состояния\n                    expanded_key = f"{parent_path}/{item[\'name\']}" if parent_path else item[\'name\']'
    
    content = re.sub(for_loop_pattern, replacement, content)
    
    # Альтернативный подход - найти место где начинается обработка item
    if 'expanded_key' not in content or content.count('expanded_key =') == 0:
        # Ищем место после начала цикла по элементам
        indent_pattern = r'(\n\s+)(with col1:\n\s+# Кнопка раскрытия/сворачивания)'
        if re.search(indent_pattern, content):
            content = re.sub(
                indent_pattern,
                r'\1# Определяем expanded_key для текущего элемента\1expanded_key = f"{parent_path}/{item[\'name\']}" if parent_path else item[\'name\']\1\2',
                content
            )

# Также нужно добавить переменные indent, icon, idx если их нет
if 'indent = ' not in content:
    # Находим место где используется indent в кнопке
    button_pattern = r'(if st\.button\(f"{indent}{expand_symbol})'
    if re.search(button_pattern, content):
        # Добавляем определения перед блоком with col1
        col1_pattern = r'(\n\s+)(with col1:)'
        replacement = r'\1# Настройки отображения\1indent = "　" * level  # Отступ для уровня\1icon = "📁" if item.get("has_children", False) else "📄"\1\2'
        content = re.sub(col1_pattern, replacement, content, count=1)

# Добавляем idx если используется enumerate
if 'for item in abc_data' in content and 'for idx, item' not in content:
    content = re.sub(
        r'for item in abc_data(\[:20\])?:',
        r'for idx, item in enumerate(abc_data\1):',
        content
    )

# Сохраняем исправленный файл
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправления применены\!")
PYTHON_EOF

# Запускаем исправление
python3 /tmp/fix_expanded_final.py

# Проверяем синтаксис
echo "🔍 Проверяем синтаксис..."
python3 -m py_compile webhook_persistent_app.py
if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен\!"
else
    echo "❌ Ошибка синтаксиса\!"
    exit 1
fi

# Копируем на сервер
echo "📤 Копируем файл на сервер..."
scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/

# Перезапускаем на сервере
echo "🔄 Перезапускаем приложение на сервере..."
ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ ГОТОВО\!"
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"

rm -f /tmp/fix_expanded_final.py
