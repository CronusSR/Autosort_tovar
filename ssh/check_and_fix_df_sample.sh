#\!/bin/bash
# Проверка и исправление ошибки df_sample

echo "🔍 Проверяем функцию build_category_tree на сервере..."
echo "======================================================"

# Сначала проверим текущее состояние функции
echo "📋 Получаем функцию с сервера..."
ssh root@217.114.1.117 "sed -n '/def build_category_tree/,/^def /p' /opt/inventory_system/webhook_persistent_app.py  < /dev/null |  head -60" > /tmp/current_function.txt

echo "📄 Текущая функция:"
cat /tmp/current_function.txt

echo ""
echo "🔧 Создаем исправленную версию..."

# Создаем исправленную функцию
cat > /tmp/fix_build_category_tree.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Правильная версия функции build_category_tree
fixed_function = '''        def build_category_tree(_df):
            """Строит дерево категорий из данных с продвинутым кэшированием"""
            # Проверяем нужно ли обновить кэш или была нажата кнопка обновления
            force_update = st.session_state.get('force_abc_update', False)
            
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
                    
                    # Сохраняем результат в кэш
                    if save_abc_cache(tree):
                        now_time = datetime.now(VLADIVOSTOK_TZ) if VLADIVOSTOK_TZ else datetime.now()
                        st.success(f"✅ ABC анализ обновлен в {now_time.strftime('%H:%M')} {'(Владивосток)' if VLADIVOSTOK_TZ else ''}")
                    
                    # Сбрасываем флаг принудительного обновления
                    if 'force_abc_update' in st.session_state:
                        st.session_state.force_abc_update = False
                    
                    return tree
            else:
                # Загружаем из кэша
                cached_tree, cache_time = load_abc_cache()
                if cached_tree is not None:
                    if cache_time:
                        st.info(f"📊 Загружен из кэша (обновлен: {cache_time.strftime('%d.%m.%Y %H:%M')})")
                    return cached_tree
                else:
                    # Фолбэк - строим дерево если кэш недоступен
                    st.session_state.force_abc_update = True
                    return build_category_tree(_df)
'''

# Читаем файл с сервера
import subprocess
result = subprocess.run(['ssh', 'root@217.114.1.117', 'cat /opt/inventory_system/webhook_persistent_app.py'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    content = result.stdout
    
    # Находим и заменяем функцию build_category_tree
    import re
    
    # Паттерн для поиска функции
    pattern = r'(\s*)def build_category_tree\(_df\):.*?(?=\n\s*def|\n\s*#|\Z)'
    
    # Заменяем функцию
    content = re.sub(pattern, fixed_function, content, flags=re.DOTALL)
    
    # Сохраняем локально
    with open('webhook_persistent_app_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Файл исправлен и сохранен как webhook_persistent_app_fixed.py")
else:
    print("❌ Не удалось получить файл с сервера")
    exit(1)
PYTHON_EOF

# Запускаем исправление
python3 /tmp/fix_build_category_tree.py

if [ -f webhook_persistent_app_fixed.py ]; then
    echo "📤 Копируем исправленный файл на сервер..."
    scp webhook_persistent_app_fixed.py root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py
    
    echo "🔄 Перезапускаем приложение..."
    ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"
    
    echo ""
    echo "✅ ГОТОВО\!"
    
    # Очистка
    rm -f webhook_persistent_app_fixed.py
else
    echo "❌ Файл не был создан"
fi

rm -f /tmp/fix_build_category_tree.py /tmp/current_function.txt
