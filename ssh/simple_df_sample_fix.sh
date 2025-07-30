#\!/bin/bash
# Простое исправление df_sample через SSH

echo "🔧 Простое исправление ошибки df_sample"
echo "======================================="

# Создаем патч прямо на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

# Создаем резервную копию
cp webhook_persistent_app.py webhook_persistent_app.py.backup_df_sample

# Создаем Python скрипт для исправления
cat > fix_df_sample_inline.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим функцию build_category_tree
func_start = content.find('def build_category_tree(_df):')
if func_start \!= -1:
    # Находим конец функции
    # Ищем следующий def на том же уровне отступа
    lines = content[func_start:].split('\n')
    func_lines = [lines[0]]  # def build_category_tree(_df):
    
    base_indent = len(lines[0]) - len(lines[0].lstrip())
    
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() and not line.startswith(' ' * (base_indent + 1)):
            # Нашли конец функции
            break
        func_lines.append(line)
    
    # Заменяем функцию на исправленную версию
    new_function = '''def build_category_tree(_df):
    """Строит дерево категорий из данных с продвинутым кэшированием"""
    force_update = st.session_state.get('force_abc_update', False)
    
    # Проверяем нужно ли обновить кэш
    if should_update_abc_cache() or force_update:
        with st.spinner("🔄 Обновление ABC анализа..."):
            tree = {}
            
            # Определяем df_sample ДО цикла
            if len(_df) > 50000:
                df_sample = _df.sample(n=30000, random_state=42)
                st.info("📊 Используется выборка для ускорения")
            else:
                df_sample = _df
            
            # Теперь можем использовать df_sample
            for _, row in df_sample.iterrows():
                if pd.isna(row.get('category_path', '')) or not row.get('category_path', ''):
                    continue
                
                parts = [p.strip() for p in str(row['category_path']).split('/') if p.strip()][:3]
                
                current_node = tree
                for i, part in enumerate(parts):
                    if part not in current_node:
                        current_node[part] = {
                            'children': {},
                            'items': [],
                            'total_amount': 0,
                            'total_quantity': 0
                        }
                    
                    current_node[part]['items'].append(row)
                    current_node[part]['total_amount'] += row.get('amount', 0)
                    current_node[part]['total_quantity'] += row.get('quantity', 0)
                    current_node = current_node[part]['children']
            
            save_abc_cache(tree)
            return tree
    else:
        # Загружаем из кэша
        cached_tree, _ = load_abc_cache()
        if cached_tree is not None:
            return cached_tree
        else:
            # Если кэша нет, строим дерево
            st.session_state.force_abc_update = True
            return build_category_tree(_df)'''
    
    # Находим конец старой функции
    func_end = func_start + len('\n'.join(func_lines))
    
    # Заменяем функцию
    content = content[:func_start] + new_function + content[func_end:]

# Сохраняем
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Функция исправлена\!")
PYTHON_EOF

# Запускаем исправление
python3 fix_df_sample_inline.py

# Проверяем результат
echo "🔍 Проверяем исправление..."
if grep -A5 "def build_category_tree" webhook_persistent_app.py  < /dev/null |  grep -q "force_update"; then
    echo "✅ Функция успешно обновлена"
else
    echo "❌ Что-то пошло не так"
fi

# Перезапускаем приложение
echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "PID: $\!"

# Очистка
rm -f fix_df_sample_inline.py

echo ""
echo "✅ ГОТОВО\!"
echo "📋 Проверьте логи: tail -f webhook_8502.log"
REMOTE_EOF

echo ""
echo "✅ Исправление применено на сервере\!"
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
