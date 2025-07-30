#\!/bin/bash
# Исправление ABC анализа - использование правильных категорий

echo "🔧 Исправление ABC анализа категорий"
echo "==================================="

# Работаем на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "💾 Создаем резервную копию..."
cp webhook_persistent_app.py webhook_persistent_app_before_category_fix.py

echo "🔧 Исправляем логику категорий в ABC анализе..."

# Создаем скрипт для исправления
cat > fix_category_logic.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и заменяем логику обработки категорий
# Ищем блок где обрабатывается category_path

# Новая логика для правильного извлечения категорий
new_category_logic = '''        # Простая группировка по ПРАВИЛЬНОЙ категории (предпоследняя в пути)
        category_data = []
        
        for _, row in sales_data.iterrows():
            category_path = row.get('category_path', '')
            if pd.isna(category_path) or category_path == '':
                continue
                
            # Разбиваем путь категории
            # Пример: "19*0,8мм ПВХ/Кромка ПВХ Китай/Кромка ПВХ/Кромочные материалы/Мебельная фурнитура/"
            # Нужна категория: "Кромочные материалы" (предпоследняя, исключая "Мебельная фурнитура")
            parts = [p.strip() for p in str(category_path).split('/') if p.strip()]
            
            target_category = None
            
            if len(parts) >= 2:
                # Убираем "Мебельная фурнитура" если она последняя
                if parts[-1] == "Мебельная фурнитура":
                    parts = parts[:-1]
                
                # Теперь берем последнюю оставшуюся категорию
                if parts:
                    target_category = parts[-1]  # Например: "Кромочные материалы", "Ручки, крючки, опоры"
            
            if target_category:
                category_data.append({
                    'category': target_category,
                    'amount': row.get('amount', 0),
                    'quantity': row.get('quantity', 0),
                    'item_code': row.get('item_code', ''),
                    'item_name': row.get('item_name', ''),
                    'branch': row.get('branch', ''),
                    'original_path': category_path  # Для отладки
                })'''

# Ищем существующую логику категорий и заменяем
import re

# Паттерн для поиска блока обработки категорий
old_pattern = r'# Простая группировка по первой категории.*?target_category = parts\[0\]\.strip\(\)'
if re.search(old_pattern, content, re.DOTALL):
    content = re.sub(old_pattern, new_category_logic.strip(), content, flags=re.DOTALL)
    print("✅ Заменена логика обработки категорий")
else:
    # Если не найден точный паттерн, ищем альтернативный
    alt_pattern = r'# Берем первую категорию.*?first_category = parts\[0\]\.strip\(\)'
    if re.search(alt_pattern, content, re.DOTALL):
        content = re.sub(alt_pattern, new_category_logic.strip(), content, flags=re.DOTALL)
        print("✅ Заменена альтернативная логика категорий")
    else:
        print("⚠️ Не найден блок обработки категорий, добавляем в ABC раздел...")
        
        # Ищем ABC блок и вставляем правильную логику
        abc_pattern = r'(if not sales_data\.empty and \'category_path\' in sales_data\.columns:.*?st\.info\("📊 Упрощенный ABC анализ категорий"\))'
        if re.search(abc_pattern, content, re.DOTALL):
            replacement = r'\1\n' + new_category_logic
            content = re.sub(abc_pattern, replacement, content, flags=re.DOTALL)
            print("✅ Добавлена правильная логика категорий в ABC блок")

# Также добавляем отладочную информацию
debug_info = '''
        # Отладочная информация о категориях
        if st.checkbox("🔍 Показать примеры категорий", key="debug_categories"):
            st.write("**Примеры обработки путей категорий:**")
            
            sample_paths = sales_data['category_path'].dropna().unique()[:5]
            for i, path in enumerate(sample_paths):
                parts = [p.strip() for p in str(path).split('/') if p.strip()]
                
                # Применяем ту же логику что и в основном коде
                if parts and parts[-1] == "Мебельная фурнитура":
                    parts = parts[:-1]
                
                target_category = parts[-1] if parts else "Не определена"
                
                st.write(f"{i+1}. `{path}`")
                st.write(f"   → Выбранная категория: **{target_category}**")
                st.write(f"   → Все части: {parts}")
                st.write("---")
'''

# Вставляем отладочную информацию после логики категорий
if 'category_data.append({' in content:
    insertion_point = content.find('if category_data:')
    if insertion_point \!= -1:
        content = content[:insertion_point] + debug_info + '\n        ' + content[insertion_point:]
        print("✅ Добавлена отладочная информация")

# Сохраняем исправленный файл
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Логика категорий исправлена\!")
PYTHON_EOF

# Запускаем исправление
python3 fix_category_logic.py

echo ""
echo "🔍 Проверяем синтаксис..."
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_persistent_app.py', doraise=True)
    print('✅ Синтаксис корректен\!')
except Exception as e:
    print(f'❌ Ошибка синтаксиса: {e}')
"

echo ""
echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "Запущен с PID: $\!"

echo ""
echo "✅ ABC АНАЛИЗ ИСПРАВЛЕН\!"
echo "📊 Теперь используются правильные категории:"
echo "   - Ручки, крючки, опоры"
echo "   - Кромочные материалы"
echo "   - и другие предпоследние категории"
echo ""
echo "📋 Логи: tail -f webhook_8502.log"

# Очистка
rm -f fix_category_logic.py
REMOTE_EOF

echo ""
echo "🎉 ABC анализ исправлен для правильных категорий\!"
echo "📋 Проверить: ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
