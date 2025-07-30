#\!/bin/bash
# Исправление ошибки UnboundLocalError: df_sample

echo "🔧 Исправление ошибки df_sample"
echo "==============================="

# Python скрипт для исправления
cat > /tmp/fix_df_sample.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

file_path = 'webhook_persistent_app.py'

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим функцию build_category_tree и исправляем отступы
# Проблема в том, что for цикл находится вне блока if/else

# Паттерн для поиска проблемного участка
pattern = r'(def build_category_tree\(_df\):.*?)(for _, row in df_sample\.iterrows\(\):)'

# Ищем всю функцию build_category_tree
func_start = content.find('def build_category_tree(_df):')
if func_start \!= -1:
    # Находим конец функции (следующий def или конец блока)
    func_end = content.find('\n    def ', func_start)
    if func_end == -1:
        func_end = content.find('\n\ndef ', func_start)
    if func_end == -1:
        func_end = len(content)
    
    # Извлекаем функцию
    func_content = content[func_start:func_end]
    
    # Исправляем функцию
    new_func = '''def build_category_tree(_df):
    """Строит дерево категорий из данных с продвинутым кэшированием"""
    # Проверяем нужно ли обновить кэш или была нажата кнопка обновления
    if should_update_abc_cache() or force_update:
        with st.spinner("🔄 Обновление ABC анализа... Это может занять несколько минут"):
            tree = {}
            
            # Берем выборку для ускорения если данных много
            if len(_df) > 50000:
                df_sample = _df.sample(n=30000, random_state=42)
                st.info("📊 Используется оптимизированная выборка для ABC анализа")
            else:
                df_sample = _df
            
            for _, row in df_sample.iterrows():
                if pd.isna(row['category_path']) or row['category_path'] == '':
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
                    current_node[part]['total_amount'] += row['amount']
                    current_node[part]['total_quantity'] += row['quantity']
                    current_node = current_node[part]['children']
            
            # Сохраняем результат в кэш
            if save_abc_cache(tree):
                now_time = datetime.now(VLADIVOSTOK_TZ) if VLADIVOSTOK_TZ else datetime.now()
                st.success(f"✅ ABC анализ обновлен в {now_time.strftime('%H:%M')} {'(Владивосток)' if VLADIVOSTOK_TZ else ''}")
            
            return tree
    else:
        # Загружаем из кэша
        cached_tree, cache_time = load_abc_cache()
        if cached_tree is not None:
            st.info(f"📊 Загружен из кэша (обновлен: {cache_time.strftime('%d.%m.%Y %H:%M')})")
            return cached_tree
        else:
            # Фолбэк - строим дерево если кэш недоступен
            return build_category_tree(_df)'''
    
    # Заменяем функцию
    content = content[:func_start] + new_func + content[func_end:]

# Сохраняем исправленный файл
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Функция build_category_tree исправлена\!")
PYTHON_EOF

# Запускаем исправление
python3 /tmp/fix_df_sample.py

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

rm -f /tmp/fix_df_sample.py
