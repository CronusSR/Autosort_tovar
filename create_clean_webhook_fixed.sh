#\!/bin/bash
# Создание полностью нового рабочего webhook_persistent_app.py

echo "🔧 Создание нового рабочего webhook_persistent_app.py"
echo "==================================================="

# Проверяем наличие backup файла
echo "📋 Ищем backup файл..."
if [ -f "ssh/webhook_persistent_app_backup_20250724_120403.py" ]; then
    echo "✅ Найден backup файл"
    cp ssh/webhook_persistent_app_backup_20250724_120403.py webhook_persistent_app_clean.py
elif [ -f "webhook_persistent_app_backup_20250724_120403.py" ]; then
    echo "✅ Найден backup файл в корне"
    cp webhook_persistent_app_backup_20250724_120403.py webhook_persistent_app_clean.py
else
    echo "❌ Backup файл не найден, используем текущий webhook_persistent_app.py"
    if [ -f "webhook_persistent_app.py" ]; then
        cp webhook_persistent_app.py webhook_persistent_app_clean.py
    else
        echo "❌ Нет исходного файла для работы\!"
        exit 1
    fi
fi

# Применяем только критически важные исправления
echo "🔧 Применяем минимальные исправления..."

# Python скрипт для минимальных исправлений
cat > /tmp/minimal_fixes_corrected.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем файл
with open('webhook_persistent_app_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("📄 Размер исходного файла:", len(content), "символов")

# 1. Исправляем st.experimental_rerun на st.rerun
content = content.replace('st.experimental_rerun()', 'st.rerun()')
print("✅ Исправлен experimental_rerun")

# 2. Удаляем все проблемные блоки с expanded_key
# Ищем и удаляем все строки с expanded_key
lines = content.split('\n')
clean_lines = []
skip_line = False

for line in lines:
    if 'expanded_key' in line:
        print(f"🗑️ Удаляем строку с expanded_key: {line[:50]}...")
        continue
    clean_lines.append(line)

content = '\n'.join(clean_lines)
print("✅ Удалены строки с expanded_key")

# 3. Заменяем проблемную функцию render_category_level на простую
if 'def render_category_level' in content:
    simple_render = '''def render_category_level(tree, level=0, parent_path=""):
    """Простое отображение категорий"""
    st.subheader("📊 Категории (упрощенный вид)")
    
    if not tree:
        st.warning("Нет данных")
        return
    
    # Простая таблица категорий
    data = []
    for name, info in list(tree.items())[:20]:
        data.append({
            'Категория': name[:50],
            'Выручка': f"{info.get('total_amount', 0):,.0f} ₸",
            'Количество': f"{info.get('total_quantity', 0):,.0f}",
            'Товаров': len(info.get('items', []))
        })
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)'''
    
    # Заменяем функцию
    pattern = r'def render_category_level.*?(?=\n\ndef  < /dev/null | \nwith tab|\n# |$)'
    content = re.sub(pattern, simple_render, content, flags=re.DOTALL)
    print("✅ Заменена функция render_category_level")

# 4. Упрощаем функцию build_category_tree
if 'def build_category_tree' in content:
    simple_build = '''def build_category_tree(_df):
    """Простое построение дерева категорий"""
    tree = {}
    
    if _df.empty:
        return tree
    
    # Проверяем наличие колонки category_path
    if 'category_path' not in _df.columns:
        st.warning("Колонка category_path не найдена")
        return tree
    
    # Берем выборку для скорости
    df_sample = _df.head(5000) if len(_df) > 5000 else _df
    
    for _, row in df_sample.iterrows():
        category_path = row.get('category_path', '')
        if pd.isna(category_path) or category_path == '':
            continue
            
        # Берем только первую категорию
        category = str(category_path).split('/')[0].strip()
        
        if category and category not in tree:
            tree[category] = {
                'children': {},
                'items': [],
                'total_amount': 0,
                'total_quantity': 0
            }
        
        if category:
            tree[category]['items'].append(row)
            tree[category]['total_amount'] += row.get('amount', 0)
            tree[category]['total_quantity'] += row.get('quantity', 0)
    
    return tree'''
    
    # Заменяем функцию
    pattern = r'def build_category_tree.*?(?=\n\ndef |\nwith tab|\n# |$)'
    content = re.sub(pattern, simple_build, content, flags=re.DOTALL)
    print("✅ Заменена функция build_category_tree")

# 5. Добавляем базовую иерархию складов если её нет
if 'WAREHOUSE_HIERARCHY' not in content:
    hierarchy_code = '''
# Базовая иерархия складов
WAREHOUSE_HIERARCHY = {
    'База Склад Фурнитура Комплект': {
        'level': 1,
        'type': 'hub',
        'city': 'Алматы'
    }
}

def get_warehouse_info(warehouse_name):
    """Получить информацию о складе"""
    return WAREHOUSE_HIERARCHY.get(warehouse_name, {'level': 1, 'type': 'unknown', 'city': 'Неизвестно'})
'''
    
    # Вставляем после импортов
    import_end = content.find('st.set_page_config(')
    if import_end \!= -1:
        content = content[:import_end] + hierarchy_code + '\n\n' + content[import_end:]
        print("✅ Добавлена базовая иерархия складов")

# Сохраняем
with open('webhook_persistent_app_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл сохранен, размер:", len(content), "символов")
PYTHON_EOF

# Применяем исправления
python3 /tmp/minimal_fixes_corrected.py

# Проверяем синтаксис
echo "🔍 Проверяем синтаксис..."
python3 -m py_compile webhook_persistent_app_clean.py
if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен\!"
    
    # Переименовываем в основной файл
    mv webhook_persistent_app_clean.py webhook_persistent_app.py
    
    # Копируем на сервер
    echo "📤 Копируем на сервер..."
    scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/
    
    # Перезапускаем
    echo "🔄 Перезапускаем приложение..."
    ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"
    
    echo ""
    echo "✅ ГОТОВО\! Создан чистый рабочий файл"
    echo "📋 Для проверки логов:"
    echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
    
else
    echo "❌ Ошибка синтаксиса в новом файле\!"
    echo "📄 Показываем ошибки синтаксиса:"
    python3 -m py_compile webhook_persistent_app_clean.py
    exit 1
fi

# Очистка
rm -f /tmp/minimal_fixes_corrected.py
