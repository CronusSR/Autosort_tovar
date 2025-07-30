#\!/bin/bash
# Скрипт для исправления ошибки PYTZ_AVAILABLE в webhook_persistent_app.py

echo "🔧 Исправление ошибки PYTZ_AVAILABLE в webhook_persistent_app.py"
echo "========================================================="

# Создаем временный Python скрипт для исправления
cat > /tmp/fix_pytz_inline.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

file_path = 'webhook_persistent_app.py'

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Заменяем простой import pytz на try-except блок
old_import = 'import pytz'
new_import = '''# Импорт pytz с fallback
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    # Fallback для работы без pytz
    class SimpleTimezone:
        def __init__(self, name):
            self.name = name
        def localize(self, dt):
            return dt
    pytz = type('pytz', (), {'timezone': lambda name: SimpleTimezone(name)})()'''

# Заменяем только если это отдельная строка import pytz
content = re.sub(r'^import pytz$', new_import, content, flags=re.MULTILINE)

# 2. Исправляем VLADIVOSTOK_TZ
content = re.sub(
    r"VLADIVOSTOK_TZ = pytz\.timezone\('Asia/Vladivostok'\)$",
    "VLADIVOSTOK_TZ = pytz.timezone('Asia/Vladivostok') if PYTZ_AVAILABLE else None",
    content,
    flags=re.MULTILINE
)

# 3. Добавляем проверки PYTZ_AVAILABLE в функции если их нет
functions_to_check = [
    ('def should_update_abc_cache():', '    if not PYTZ_AVAILABLE:\n        return True\n    \n'),
    ('def save_abc_cache(abc_data):', '    if not PYTZ_AVAILABLE:\n        return None\n    \n'),
    ('def load_abc_cache():', '    if not PYTZ_AVAILABLE:\n        return None\n    \n'),
    ('def get_cache_status():', '    if not PYTZ_AVAILABLE:\n        return None\n    \n')
]

for func_def, check_code in functions_to_check:
    if func_def in content:
        # Находим позицию после docstring
        func_start = content.find(func_def)
        if func_start \!= -1:
            # Ищем конец docstring после определения функции
            doc_start = content.find('"""', func_start)
            if doc_start \!= -1:
                doc_end = content.find('"""', doc_start + 3)
                if doc_end \!= -1:
                    # Проверяем, есть ли уже проверка PYTZ_AVAILABLE
                    check_area = content[doc_end:doc_end+200]
                    if 'if not PYTZ_AVAILABLE:' not in check_area:
                        # Вставляем проверку после docstring
                        insert_pos = doc_end + 3
                        # Находим конец строки после """
                        newline_pos = content.find('\n', insert_pos)
                        if newline_pos \!= -1:
                            content = content[:newline_pos+1] + check_code + content[newline_pos+1:]

# 4. Исправляем использование datetime.now(VLADIVOSTOK_TZ)
content = re.sub(
    r'datetime\.now\(VLADIVOSTOK_TZ\)(?\! if VLADIVOSTOK_TZ else)',
    'datetime.now(VLADIVOSTOK_TZ) if VLADIVOSTOK_TZ else datetime.now()',
    content
)

# 5. Исправляем localize вызовы
content = re.sub(
    r'(\w+) = VLADIVOSTOK_TZ\.localize\((\w+)\)',
    r'if VLADIVOSTOK_TZ:\n        \1 = VLADIVOSTOK_TZ.localize(\2)\n    else:\n        \1 = \2',
    content
)

# Сохраняем исправленный файл
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл исправлен\!")
PYTHON_EOF

# Запускаем Python скрипт
echo "📝 Применяем исправления к webhook_persistent_app.py..."
python3 /tmp/fix_pytz_inline.py

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
rm -f /tmp/fix_pytz_inline.py
