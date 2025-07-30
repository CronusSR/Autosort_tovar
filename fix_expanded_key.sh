#\!/bin/bash
# Скрипт для исправления ошибки expanded_key

echo "🔧 Исправление ошибки expanded_key в webhook_persistent_app.py"
echo "========================================================="

# Используем файл из папки ssh как основу
echo "📋 Используем версию из папки ssh..."
cp ssh/webhook_persistent_app.py webhook_persistent_app.py

# Создаем Python скрипт для исправления
cat > /tmp/fix_expanded_key.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

file_path = 'webhook_persistent_app.py'

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим функцию render_category_level и исправляем expanded_key
# Ищем строку с expanded_key in st.session_state.expanded_categories
pattern = r'is_expanded = expanded_key in st\.session_state\.expanded_categories'
replacement = '''# Проверяем expanded состояние
            expanded_key = f"{parent_path}/{name}" if parent_path else name
            is_expanded = expanded_key in st.session_state.expanded_categories'''

content = re.sub(pattern, replacement, content)

# Также проверяем, что session_state.expanded_categories инициализирован
if 'if "expanded_categories" not in st.session_state:' not in content:
    # Добавляем инициализацию в начало main или перед использованием
    init_code = '''# Инициализация session state для категорий
if "expanded_categories" not in st.session_state:
    st.session_state.expanded_categories = set()

'''
    # Находим место для вставки - после определения страницы
    insert_pos = content.find('# ABC-анализ категорий')
    if insert_pos \!= -1:
        content = content[:insert_pos] + init_code + content[insert_pos:]

# Сохраняем исправленный файл
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл исправлен\!")
PYTHON_EOF

# Запускаем исправление
python3 /tmp/fix_expanded_key.py

# Добавляем исправления PYTZ если нужно
echo "🔧 Проверяем и добавляем исправления PYTZ..."
if \! grep -q "PYTZ_AVAILABLE" webhook_persistent_app.py; then
    echo "   Добавляем поддержку PYTZ..."
    # Используем предыдущий скрипт исправления PYTZ
    python3 -c "
import re
content = open('webhook_persistent_app.py', 'r', encoding='utf-8').read()

# Заменяем import pytz
old_import = 'import pytz'
new_import = '''# Импорт pytz с fallback
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    class SimpleTimezone:
        def __init__(self, name):
            self.name = name
        def localize(self, dt):
            return dt
    pytz = type('pytz', (), {'timezone': lambda name: SimpleTimezone(name)})()'''

content = re.sub(r'^import pytz$', new_import, content, flags=re.MULTILINE)
content = re.sub(r\"VLADIVOSTOK_TZ = pytz\.timezone\('Asia/Vladivostok'\)\", \"VLADIVOSTOK_TZ = pytz.timezone('Asia/Vladivostok') if PYTZ_AVAILABLE else None\", content)

open('webhook_persistent_app.py', 'w', encoding='utf-8').write(content)
print('✅ PYTZ исправления добавлены')
"
fi

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
echo "📋 Для проверки логов на сервере:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"

# Очистка
rm -f /tmp/fix_expanded_key.py
