#\!/bin/bash
# Окончательное исправление ошибки df_sample

echo "🔧 Исправление ошибки df_sample в build_category_tree"
echo "===================================================="

# Исправляем прямо на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "🔍 Создаем резервную копию..."
cp webhook_persistent_app.py webhook_persistent_app.py.backup_df_fix

echo "🔧 Исправляем функцию build_category_tree..."

# Создаем Python скрипт для исправления
cat > fix_build_category_tree.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправленная функция build_category_tree без кеширования
fixed_function = '''        def build_category_tree(_df):
            """Строит дерево категорий из данных"""
            tree = {}
            
            if _df.empty or 'category_path' not in _df.columns:
                return tree
            
            # Определяем df_sample ОБЯЗАТЕЛЬНО
            if len(_df) > 50000:
                df_sample = _df.sample(n=20000, random_state=42)
                st.info("📊 Для ускорения ABC анализа используется выборка данных")
            else:
                df_sample = _df.copy()
            
            # Теперь можем безопасно использовать df_sample
            for _, row in df_sample.iterrows():
                if pd.isna(row.get('category_path', '')) or row.get('category_path', '') == '':
                    continue
                    
                # Разбиваем путь на части (только первые 3 уровня для скорости)
                parts = [p.strip() for p in str(row['category_path']).split('/') if p.strip()][:3]
                
                # Строим дерево
                current_node = tree
                for i, part in enumerate(parts):
                    if part not in current_node:
                        current_node[part] = {
                            'children': {},
                            'items': [],
                            'total_amount': 0,
                            'total_quantity': 0,
                            'level': i,
                            'path': parts[:i+1]
                        }
                    
                    current_node[part]['items'].append(row)
                    current_node[part]['total_amount'] += row.get('amount', 0)
                    current_node[part]['total_quantity'] += row.get('quantity', 0)
                    current_node = current_node[part]['children']
            
            return tree'''

# Удаляем декоратор @st.cache_data и заменяем функцию
# Сначала удаляем декоратор
content = re.sub(r'@st\.cache_data\(ttl=300\)\s*\n\s*def build_category_tree', 'def build_category_tree', content)

# Затем заменяем функцию
pattern = r'def build_category_tree\(_df\):.*?return tree'
content = re.sub(pattern, fixed_function.strip(), content, flags=re.DOTALL)

# Сохраняем исправленный файл
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Функция build_category_tree исправлена\!")
PYTHON_EOF

# Запускаем исправление
python3 fix_build_category_tree.py

echo "🔍 Проверяем исправление..."
if grep -A5 "def build_category_tree" webhook_persistent_app.py  < /dev/null |  grep -q "df_sample = _df.copy()"; then
    echo "✅ Функция успешно исправлена"
else
    echo "⚠️  Проверьте исправления вручную"
fi

echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "PID: $\!"

echo ""
echo "✅ ГОТОВО\! Исправление применено"
echo "📋 Проверьте логи: tail -f webhook_8502.log"

# Очистка
rm -f fix_build_category_tree.py
REMOTE_EOF

echo ""
echo "✅ Исправление df_sample применено на сервере\!"
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
