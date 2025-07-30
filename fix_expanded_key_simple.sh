#\!/bin/bash
# Простое исправление - удаляем проблемный код с expanded_key

echo "🔧 Простое исправление expanded_key"
echo "===================================="

# Используем версию из ssh
cp ssh/webhook_persistent_app.py webhook_persistent_app.py

# Python скрипт для удаления проблемного блока
cat > /tmp/remove_expanded_key.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

file_path = 'webhook_persistent_app.py'

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Новый список строк без проблемного блока
new_lines = []
skip_block = False
skip_count = 0

for i, line in enumerate(lines):
    # Начало проблемного блока - строки с expanded_key
    if 'with st.container():' in line and i < len(lines) - 10:
        # Проверяем следующие строки на наличие expanded_key
        found_expanded = False
        for j in range(i, min(i + 20, len(lines))):
            if 'expanded_key' in lines[j]:
                found_expanded = True
                break
        
        if found_expanded:
            skip_block = True
            skip_count = 0
            continue
    
    # Пропускаем строки проблемного блока
    if skip_block:
        skip_count += 1
        # Конец блока - когда находим следующий основной элемент
        if ('# Показываем если есть еще категории' in line or 
            'if len(abc_data) > 20:' in line or
            skip_count > 100):
            skip_block = False
        else:
            continue
    
    new_lines.append(line)

# Сохраняем исправленный файл
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Проблемный код с expanded_key удален\!")
PYTHON_EOF

# Запускаем исправление
python3 /tmp/remove_expanded_key.py

# Проверяем что expanded_key больше нет
echo "🔍 Проверяем наличие expanded_key..."
if grep -q "expanded_key" webhook_persistent_app.py; then
    echo "⚠️  expanded_key все еще присутствует, проверьте файл вручную"
else
    echo "✅ expanded_key успешно удален\!"
fi

# Проверяем синтаксис
echo "🔍 Проверяем синтаксис..."
python3 -m py_compile webhook_persistent_app.py
if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен\!"
else
    echo "❌ Ошибка синтаксиса\!"
fi

# Копируем на сервер
echo "📤 Копируем файл на сервер..."
scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/

# Перезапускаем на сервере
echo "🔄 Перезапускаем приложение на сервере..."
ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ ГОТОВО\!"

rm -f /tmp/remove_expanded_key.py
