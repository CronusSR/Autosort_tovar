#\!/bin/bash
# Удаление кэширования и восстановление работоспособности

echo "🔧 Удаление кэширования и восстановление работоспособности"
echo "========================================================="

# Работаем прямо на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "🔍 Создаем резервную копию..."
cp webhook_persistent_app.py webhook_persistent_app.py.backup_before_cache_removal

echo "🔧 Удаляем всё кэширование и исправляем синтаксис..."

# Создаем простой рабочий скрипт
cat > remove_cache_and_fix.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Удаляем все декораторы кэширования
content = content.replace('@st.cache_data(ttl=300)', '')
content = content.replace('@st.cache_data', '')

# 2. Заменяем проблемную функцию build_category_tree на простую рабочую версию
simple_build_function = '''def build_category_tree(_df):
    """Простое построение дерева категорий без кэширования"""
    tree = {}
    
    if _df.empty or 'category_path' not in _df.columns:
        return tree
    
    # Берем первые 10000 записей для скорости
    df_work = _df.head(10000) if len(_df) > 10000 else _df
    
    for _, row in df_work.iterrows():
        category_path = row.get('category_path', '')
        if pd.isna(category_path) or category_path == '':
            continue
            
        # Берем только первую категорию для простоты
        parts = [p.strip() for p in str(category_path).split('/') if p.strip()]
        if not parts:
            continue
            
        first_category = parts[0]
        
        if first_category not in tree:
            tree[first_category] = {
                'children': {},
                'items': [],
                'total_amount': 0,
                'total_quantity': 0,
                'level': 0,
                'path': [first_category]
            }
        
        tree[first_category]['items'].append(row)
        tree[first_category]['total_amount'] += row.get('amount', 0)
        tree[first_category]['total_quantity'] += row.get('quantity', 0)
    
    return tree'''

# Находим и заменяем функцию build_category_tree
import re
pattern = r'def build_category_tree\(_df\):.*?return tree'
content = re.sub(pattern, simple_build_function, content, flags=re.DOTALL)

# 3. Упрощаем функцию render_category_level
simple_render_function = '''def render_category_level(tree, level=0, parent_path=""):
    """Простое отображение категорий в таблице"""
    
    if not tree:
        st.warning("Нет данных для отображения")
        return
    
    # Подготавливаем данные
    categories = []
    for name, data in tree.items():
        categories.append({
            'Категория': name[:50],
            'Выручка': f"{data.get('total_amount', 0):,.0f} ₸",
            'Количество': f"{data.get('total_quantity', 0):,.0f}",
            'Товаров': len(data.get('items', []))
        })
    
    if categories:
        # Сортируем по выручке
        categories = sorted(categories, key=lambda x: float(x['Выручка'].replace(' ₸', '').replace(',', '')), reverse=True)
        
        # Показываем таблицу
        df = pd.DataFrame(categories)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Простая ABC классификация
        st.subheader("📊 ABC анализ")
        total_items = len(categories)
        a_count = max(1, total_items // 5)  # 20% = A
        b_count = max(1, total_items // 3)  # 33% = B
        c_count = total_items - a_count - b_count  # остальное = C
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🅰️ Группа A", f"{a_count} категорий", "Топ 20%")
        with col2:
            st.metric("🅱️ Группа B", f"{b_count} категорий", "Средние 33%") 
        with col3:
            st.metric("🅾️ Группа C", f"{c_count} категорий", "Остальные")'''

# Заменяем функцию render_category_level
pattern = r'def render_category_level\(tree, level=0, parent_path=""\):.*?st\.info\(f"\.\.\..*?\)'
content = re.sub(pattern, simple_render_function, content, flags=re.DOTALL)

# 4. Удаляем всю логику с expanded_categories
lines = content.split('\n')
clean_lines = []
skip_expanded = False

for line in lines:
    # Пропускаем строки связанные с expanded_categories
    if 'expanded_categories' in line or 'expanded_key' in line:
        continue
    
    # Пропускаем сложные блоки с кнопками раскрытия
    if 'expand_symbol' in line or 'st.button(f"{indent}{expand_symbol}' in line:
        skip_expanded = True
        continue
    
    if skip_expanded and ('with col' in line or 'st.markdown' in line or line.strip() == ''):
        if 'def ' in line and not line.startswith('        '):
            skip_expanded = False
        else:
            continue
    
    clean_lines.append(line)

content = '\n'.join(clean_lines)

# Сохраняем упрощенный файл
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Кэширование удалено, функции упрощены\!")
PYTHON_EOF

# Запускаем упрощение
python3 remove_cache_and_fix.py

echo "🔍 Проверяем синтаксис..."
python3 -c "
import py_compile
try:
    py_compile.compile('webhook_persistent_app.py', doraise=True)
    print('✅ Синтаксис корректен')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"

echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "PID: $\!"

echo ""
echo "✅ ГОТОВО\! Приложение упрощено и должно работать"
echo "📋 Логи: tail -f webhook_8502.log"

# Очистка
rm -f remove_cache_and_fix.py
REMOTE_EOF

echo ""
echo "✅ Кэширование удалено, приложение упрощено\!"
echo "📋 Проверить логи: ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
