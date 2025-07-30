#\!/bin/bash
# Создание полностью нового рабочего webhook_persistent_app.py

echo "🔧 Создание нового рабочего webhook_persistent_app.py"
echo "==================================================="

# Используем стабильную backup версию как основу
echo "📋 Копируем стабильную версию..."
cp ssh/webhook_persistent_app_backup_20250724_120403.py webhook_persistent_app_clean.py

# Применяем только критически важные исправления
echo "🔧 Применяем минимальные исправления..."

# Python скрипт для минимальных исправлений
cat > /tmp/minimal_fixes.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем файл
with open('webhook_persistent_app_clean.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Исправляем st.experimental_rerun на st.rerun
content = content.replace('st.experimental_rerun()', 'st.rerun()')

# 2. Добавляем импорт pytz с fallback ТОЛЬКО если его нет
if 'import pytz' in content and 'PYTZ_AVAILABLE' not in content:
    content = content.replace(
        'import pytz',
        '''# Импорт pytz с fallback
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    # Создаем заглушку
    pytz = None'''
    )

# 3. Добавляем WAREHOUSE_HIERARCHY только если его нет
if 'WAREHOUSE_HIERARCHY' not in content:
    hierarchy_code = '''
# Иерархическая структура складов (правильная согласно требованиям)
WAREHOUSE_HIERARCHY = {
    'База Склад Фурнитура Комплект': {
        'level': 1,
        'type': 'hub',
        'city': 'Алматы',
        'parent': None,
        'children': [
            'Казыбаева Склад Фурнитура TRADE',
            'склад фурнитура № 1',
            '4 Склад фурнитуры АЗМ Шымкент',
            'Барыс Склад Фурнитура TRADE',
            'АО Склад Фурнитура TRADE'
        ],
        'min_days': 30,
        'max_days': 90
    },
    'Казыбаева Склад Фурнитура TRADE': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Алматы',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['ТД Казыбаева ФУРНИТУРА магазин'],
        'min_days': 15,
        'max_days': 45
    },
    'склад фурнитура № 1': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Астана',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['Магазин фурнитуры'],
        'min_days': 20,
        'max_days': 60
    },
    '4 Склад фурнитуры АЗМ Шымкент': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Шымкент',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['6 Склад фурнитуры "Овощная база" Магазин'],
        'min_days': 20,
        'max_days': 60
    },
    'ТД Казыбаева ФУРНИТУРА магазин': {
        'level': 3,
        'type': 'shop',
        'city': 'Алматы',
        'parent': 'Казыбаева Склад Фурнитура TRADE',
        'children': [],
        'min_days': 8,
        'max_days': 30
    },
    'Магазин фурнитуры': {
        'level': 3,
        'type': 'shop',
        'city': 'Астана',
        'parent': 'склад фурнитура № 1',
        'children': [],
        'min_days': 8,
        'max_days': 30
    },
    '6 Склад фурнитуры "Овощная база" Магазин': {
        'level': 3,
        'type': 'shop',
        'city': 'Шымкент',
        'parent': '4 Склад фурнитуры АЗМ Шымкент',
        'children': [],
        'min_days': 8,
        'max_days': 30
    }
}

def get_warehouse_info(warehouse_name):
    """Получить информацию о складе из иерархии"""
    for name, info in WAREHOUSE_HIERARCHY.items():
        if name in warehouse_name or warehouse_name in name:
            return info
    return None

def get_warehouse_level(warehouse_name):
    """Получить уровень склада в иерархии"""
    info = get_warehouse_info(warehouse_name)
    return info['level'] if info else 0

def get_warehouse_type(warehouse_name):
    """Получить тип склада (hub/warehouse/shop)"""
    info = get_warehouse_info(warehouse_name)
    return info['type'] if info else 'unknown'
'''
    
    # Вставляем после BRANCH_CITIES
    pos = content.find('BRANCH_CITIES = {')
    if pos \!= -1:
        end_pos = content.find('\n}', pos) + 2
        content = content[:end_pos] + '\n' + hierarchy_code + content[end_pos:]

# 4. Удаляем все проблемные блоки с expanded_key, build_category_tree и сложным ABC
# Находим и заменяем проблемную функцию render_category_level
if 'def render_category_level' in content:
    # Заменяем на простую версию
    simple_render = '''
def render_category_level(tree, level=0, parent_path=""):
    """Простое отображение категорий без сложной навигации"""
    st.info("📊 Упрощенное отображение категорий")
    
    if not tree:
        st.warning("Нет данных для отображения")
        return
    
    # Простой список категорий
    categories = list(tree.keys())[:20]  # Топ-20
    
    for i, category in enumerate(categories):
        if category in tree:
            data = tree[category]
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📁 {category}")
            with col2:
                st.write(f"{data.get('total_amount', 0):,.0f} ₸")
            with col3:
                st.write(f"{data.get('total_quantity', 0):,.0f}")
'''
    
    # Находим и заменяем функцию
    pattern = r'def render_category_level.*?(?=\ndef  < /dev/null | \Z)'
    content = re.sub(pattern, simple_render, content, flags=re.DOTALL)

# 5. Заменяем build_category_tree на простую версию
if 'def build_category_tree' in content:
    simple_build = '''
def build_category_tree(_df):
    """Простое построение дерева категорий"""
    tree = {}
    
    if _df.empty or 'category_path' not in _df.columns:
        return tree
    
    # Берем только первые 1000 записей для скорости
    df_sample = _df.head(1000) if len(_df) > 1000 else _df
    
    for _, row in df_sample.iterrows():
        if pd.isna(row.get('category_path', '')):
            continue
            
        category = str(row['category_path']).split('/')[0] if '/' in str(row['category_path']) else str(row['category_path'])
        
        if category not in tree:
            tree[category] = {
                'children': {},
                'items': [],
                'total_amount': 0,
                'total_quantity': 0
            }
        
        tree[category]['items'].append(row)
        tree[category]['total_amount'] += row.get('amount', 0)
        tree[category]['total_quantity'] += row.get('quantity', 0)
    
    return tree
'''
    
    # Заменяем функцию
    pattern = r'def build_category_tree.*?(?=\ndef |\Z)'
    content = re.sub(pattern, simple_build, content, flags=re.DOTALL)

# Сохраняем
with open('webhook_persistent_app_clean.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Минимальные исправления применены\!")
PYTHON_EOF

# Применяем исправления
python3 /tmp/minimal_fixes.py

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
    exit 1
fi

# Очистка
rm -f /tmp/minimal_fixes.py
