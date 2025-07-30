#\!/bin/bash
# Улучшение ABC анализа категорий и межфилиальных перемещений

echo "🔧 Улучшение ABC анализа и межфилиальных перемещений"
echo "=================================================="

# Python скрипт для улучшений
cat > /tmp/improve_features.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("📄 Размер файла:", len(content), "символов")

# 1. УЛУЧШАЕМ ABC АНАЛИЗ КАТЕГОРИЙ
# Находим функцию build_category_tree и заменяем на улучшенную версию
improved_build_category_tree = '''def build_category_tree(_df):
    """Строит многоуровневое дерево категорий для навигации"""
    tree = {}
    
    if _df.empty or 'category_path' not in _df.columns:
        return tree
    
    # Берем все данные для полного анализа
    df_sample = _df.copy()
    
    for _, row in df_sample.iterrows():
        if pd.isna(row.get('category_path', '')) or row.get('category_path', '') == '':
            continue
            
        # Разбиваем путь категории
        category_path = str(row['category_path']).strip()
        if not category_path:
            continue
            
        # Парсим путь - убираем "Мебельная фурнитура" если есть и разворачиваем
        parts = [p.strip() for p in category_path.split('/') if p.strip()]
        
        # Убираем "Мебельная фурнитура" если это последний элемент
        if parts and parts[-1] == "Мебельная фурнитура":
            parts = parts[:-1]
        
        # Разворачиваем для правильной иерархии (от общего к частному)
        parts = list(reversed(parts))
        
        if not parts:
            continue
        
        # Строим дерево по уровням
        current_level = tree
        for i, part in enumerate(parts):
            if part not in current_level:
                current_level[part] = {
                    'children': {},
                    'items': [],
                    'total_amount': 0,
                    'total_quantity': 0,
                    'level': i,
                    'full_path': parts[:i+1]
                }
            
            # Добавляем товар к категории всех уровней
            current_level[part]['items'].append(row)
            current_level[part]['total_amount'] += row.get('amount', 0)
            current_level[part]['total_quantity'] += row.get('quantity', 0)
            
            # Переходим на следующий уровень
            current_level = current_level[part]['children']
    
    return tree'''

# Заменяем функцию build_category_tree
pattern = r'def build_category_tree.*?(?=\n\ndef  < /dev/null | \nwith tab|\n# |$)'
content = re.sub(pattern, improved_build_category_tree, content, flags=re.DOTALL)
print("✅ Улучшена функция build_category_tree")

# 2. УЛУЧШАЕМ ФУНКЦИЮ render_category_level для табличной навигации
improved_render_category_level = '''def render_category_level(tree, level=0, parent_path=""):
    """Отображает категории в табличном виде с возможностью раскрытия"""
    
    if not tree:
        st.warning("Нет данных для отображения")
        return
    
    # Подготавливаем данные для ABC анализа
    level_data = []
    for name, data in tree.items():
        level_data.append({
            'name': name,
            'total_amount': data.get('total_amount', 0),
            'total_quantity': data.get('total_quantity', 0),
            'items_count': len(data.get('items', [])),
            'has_children': bool(data.get('children', {})),
            'path': f"{parent_path}/{name}" if parent_path else name
        })
    
    if not level_data:
        return
    
    # Сортируем по выручке
    level_data.sort(key=lambda x: x['total_amount'], reverse=True)
    
    # Вычисляем ABC классификацию
    total_revenue = sum(item['total_amount'] for item in level_data)
    cumsum = 0
    for item in level_data:
        cumsum += item['total_amount']
        percent = (cumsum / total_revenue * 100) if total_revenue > 0 else 0
        
        if percent <= 80:
            item['abc'] = 'A'
        elif percent <= 95:
            item['abc'] = 'B'
        else:
            item['abc'] = 'C'
            
        item['percent'] = (item['total_amount'] / total_revenue * 100) if total_revenue > 0 else 0
    
    # Показываем метрики ABC для корневого уровня
    if level == 0:
        a_items = [item for item in level_data if item['abc'] == 'A']
        b_items = [item for item in level_data if item['abc'] == 'B']
        c_items = [item for item in level_data if item['abc'] == 'C']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🅰️ Группа A", f"{len(a_items)}", 
                     f"{sum(item['percent'] for item in a_items):.1f}% выручки")
        with col2:
            st.metric("🅱️ Группа B", f"{len(b_items)}", 
                     f"{sum(item['percent'] for item in b_items):.1f}% выручки")
        with col3:
            st.metric("🅾️ Группа C", f"{len(c_items)}", 
                     f"{sum(item['percent'] for item in c_items):.1f}% выручки")
    
    # Создаем таблицу категорий
    st.subheader(f"📊 {'Основные категории' if level == 0 else f'Подкатегории уровня {level + 1}'}")
    
    # Подготавливаем данные для отображения
    table_data = []
    for item in level_data[:50]:  # Показываем до 50 элементов
        abc_color = {'A': '🟢', 'B': '🟡', 'C': '🔴'}[item['abc']]
        table_data.append({
            'Категория': item['name'][:60],
            'ABC': f"{abc_color} {item['abc']}",
            'Выручка': f"{item['total_amount']:,.0f} ₸",
            'Количество': f"{item['total_quantity']:,.0f}",
            'Доля %': f"{item['percent']:.1f}%",
            'Товаров': item['items_count'],
            'Есть подкатегории': '✅ Да' if item['has_children'] else '❌ Нет'
        })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True, height=400)
        
        # Навигация по категориям с детьми
        categories_with_children = [item for item in level_data if item['has_children']]
        if categories_with_children:
            st.subheader("🔍 Перейти в подкатегорию")
            
            # Создаем кнопки для навигации
            cols = st.columns(min(4, len(categories_with_children)))
            for idx, item in enumerate(categories_with_children[:12]):  # Максимум 12 кнопок
                with cols[idx % 4]:
                    if st.button(f"➡️ {item['name'][:20]}", key=f"nav_{item['name']}_{level}_{idx}"):
                        st.session_state.abc_current_path.append(item['name'])
                        st.rerun()
        
        # Показываем товары в выбранной категории
        st.subheader("🛍️ Показать товары в категории")
        category_names = [item['name'] for item in level_data]
        
        selected_category = st.selectbox(
            "Выберите категорию для просмотра товаров:",
            options=[''] + category_names,
            key=f"product_view_level_{level}"
        )
        
        if selected_category and selected_category in tree:
            items = tree[selected_category].get('items', [])
            if items:
                st.write(f"**Товары в категории '{selected_category}' ({len(items)} товаров):**")
                
                # Топ-20 товаров по выручке
                sorted_items = sorted(items, key=lambda x: x.get('amount', 0), reverse=True)[:20]
                
                product_data = []
                for i, product in enumerate(sorted_items):
                    # ABC для товаров
                    if i < len(sorted_items) * 0.2:
                        abc_class = 'A'
                    elif i < len(sorted_items) * 0.5:
                        abc_class = 'B'
                    else:
                        abc_class = 'C'
                    
                    abc_color = {'A': '🟢', 'B': '🟡', 'C': '🔴'}[abc_class]
                    
                    product_data.append({
                        'Артикул': product.get('item_code', 'N/A'),
                        'Наименование': str(product.get('item_name', 'N/A'))[:50],
                        'ABC': f"{abc_color} {abc_class}",
                        'Выручка': f"{product.get('amount', 0):,.0f} ₸",
                        'Количество': f"{product.get('quantity', 0):,.0f}",
                        'Филиал': product.get('branch', 'N/A')
                    })
                
                if product_data:
                    df_products = pd.DataFrame(product_data)
                    st.dataframe(df_products, use_container_width=True, hide_index=True, height=300)'''

# Заменяем функцию render_category_level
pattern = r'def render_category_level.*?(?=\n\ndef |\nwith tab|\n# |$)'
content = re.sub(pattern, improved_render_category_level, content, flags=re.DOTALL)
print("✅ Улучшена функция render_category_level")

# 3. УЛУЧШАЕМ МЕЖФИЛИАЛЬНЫЕ ПЕРЕМЕЩЕНИЯ
# Добавляем иерархические функции для складов
warehouse_functions = '''
# Базовая иерархия складов
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
        ]
    },
    'Казыбаева Склад Фурнитуры TRADE': {
        'level': 2,
        'type': 'warehouse', 
        'city': 'Алматы',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['ТД Казыбаева ФУРНИТУРА магазин']
    }
}

def get_warehouse_info(warehouse_name):
    """Получить информацию о складе"""
    for name, info in WAREHOUSE_HIERARCHY.items():
        if name in warehouse_name or warehouse_name in name:
            return info
    return {'level': 1, 'type': 'unknown', 'city': 'Неизвестно', 'parent': None}

def get_movement_reason(row):
    """Определяет причину перемещения"""
    if row['days_until_empty'] < 7:
        return "🚨 Критический дефицит (< 7 дней)"
    elif row['days_until_empty'] < 14:
        return "⚠️ Срочный дефицит (< 14 дней)"
    elif row['days_until_empty'] < 30:
        return "⏰ Плановое пополнение (< 30 дней)"
    elif row['has_excess']:
        return "📦 Оптимизация остатков"
    else:
        return "📊 Балансировка"

def calculate_movement_priority(row):
    """Рассчитывает приоритет перемещения"""
    if row['days_until_empty'] < 7:
        return "🔴 Высокий"
    elif row['days_until_empty'] < 14:
        return "🟡 Средний"
    else:
        return "🟢 Низкий"
'''

# Вставляем функции после импортов
if 'def get_warehouse_info' not in content:
    import_end = content.find('st.set_page_config(')
    if import_end \!= -1:
        content = content[:import_end] + warehouse_functions + '\n\n' + content[import_end:]
        print("✅ Добавлены функции для работы с иерархией складов")

# 4. УЛУЧШАЕМ ТАБЛИЦУ МЕЖФИЛИАЛЬНЫХ ПЕРЕМЕЩЕНИЙ
# Ищем раздел с рекомендациями по перемещениям и улучшаем его
movement_improvements = '''
            # Конкретные рекомендации по перемещениям с подробной информацией
            st.subheader("📋 Детальные рекомендации по перемещениям")
            
            # Создаем детальную таблицу перемещений
            if not filtered_data.empty:
                # Товары требующие пополнения
                needs_items = filtered_data[filtered_data['needs_stock']].copy()
                
                if not needs_items.empty:
                    # Добавляем дополнительную информацию
                    needs_items['movement_reason'] = needs_items.apply(get_movement_reason, axis=1)
                    needs_items['priority'] = needs_items.apply(calculate_movement_priority, axis=1)
                    needs_items['recommended_quantity'] = (needs_items['daily_sales'] * 30).round(0)
                    
                    st.subheader("🎯 Рекомендации: КУДА перемещать")
                    
                    # Подготавливаем данные для отображения
                    movement_display = needs_items[[
                        'item_name', 'item_code', 'branch', 'city', 
                        'stock_quantity', 'daily_sales', 'days_until_empty',
                        'recommended_quantity', 'movement_reason', 'priority'
                    ]].copy()
                    
                    movement_display.columns = [
                        'Товар', 'Артикул', 'КУДА (филиал)', 'КУДА (город)', 
                        'Остаток', 'Продажи/день', 'Дней до истощения',
                        'Рекомендуемое количество', 'Причина', 'Приоритет'
                    ]
                    
                    # Форматируем числа
                    movement_display['Остаток'] = movement_display['Остаток'].round(0).astype(int)
                    movement_display['Продажи/день'] = movement_display['Продажи/день'].round(2)
                    movement_display['Дней до истощения'] = movement_display['Дней до истощения'].round(1)
                    movement_display['Рекомендуемое количество'] = movement_display['Рекомендуемое количество'].astype(int)
                    
                    st.dataframe(movement_display, use_container_width=True, hide_index=True, height=400)
                
                # Источники для перемещений
                excess_items = filtered_data[filtered_data['has_excess']].copy()
                
                if not excess_items.empty:
                    excess_items['available_for_movement'] = excess_items['stock_quantity']
                    
                    st.subheader("📦 Источники: ОТКУДА можно взять")
                    
                    source_display = excess_items[[
                        'item_name', 'item_code', 'branch', 'city', 
                        'stock_quantity', 'available_for_movement'
                    ]].head(20).copy()
                    
                    source_display.columns = [
                        'Товар', 'Артикул', 'ОТКУДА (филиал)', 'ОТКУДА (город)',
                        'Общий остаток', 'Доступно для перемещения'
                    ]
                    
                    source_display['Общий остаток'] = source_display['Общий остаток'].round(0).astype(int)
                    source_display['Доступно для перемещения'] = source_display['Доступно для перемещения'].round(0).astype(int)
                    
                    st.dataframe(source_display, use_container_width=True, hide_index=True, height=400)
                
                # Сводная таблица перемещений
                if not needs_items.empty and not excess_items.empty:
                    st.subheader("🔄 Сводка перемещений по товарам")
                    
                    # Группируем по товарам
                    needs_summary = needs_items.groupby(['item_code', 'item_name']).agg({
                        'recommended_quantity': 'sum',
                        'branch': 'count'
                    }).reset_index()
                    needs_summary.columns = ['Артикул', 'Товар', 'Общая потребность', 'Филиалов нуждается']
                    
                    excess_summary = excess_items.groupby(['item_code', 'item_name']).agg({
                        'stock_quantity': 'sum',
                        'branch': 'count'
                    }).reset_index()
                    excess_summary.columns = ['Артикул', 'Товар', 'Общий избыток', 'Филиалов источников']
                    
                    # Объединяем данные
                    movement_summary = pd.merge(
                        needs_summary, excess_summary,
                        on=['Артикул', 'Товар'], how='outer'
                    ).fillna(0)
                    
                    movement_summary['Возможно переместить'] = np.minimum(
                        movement_summary['Общая потребность'], 
                        movement_summary['Общий избыток']
                    )
                    
                    # Форматируем
                    for col in ['Общая потребность', 'Общий избыток', 'Возможно переместить']:
                        movement_summary[col] = movement_summary[col].round(0).astype(int)
                    
                    st.dataframe(movement_summary, use_container_width=True, hide_index=True)
                    
                    # Экспорт детальных рекомендаций
                    if st.button("📥 Экспорт всех рекомендаций"):
                        # Создаем Excel файл с несколькими листами
                        from io import BytesIO
                        
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            if not needs_items.empty:
                                movement_display.to_excel(writer, sheet_name='Куда перемещать', index=False)
                            if not excess_items.empty:
                                source_display.to_excel(writer, sheet_name='Откуда брать', index=False)
                            movement_summary.to_excel(writer, sheet_name='Сводка', index=False)
                        
                        st.download_button(
                            label="📊 Скачать подробные рекомендации (Excel)",
                            data=output.getvalue(),
                            file_name=f"movement_recommendations_detailed_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.info("Примените фильтры для получения рекомендаций")'''

# Заменяем раздел рекомендаций по перемещениям
pattern = r'# Конкретные рекомендации по перемещениям.*?# Экспорт рекомендаций'
content = re.sub(pattern, movement_improvements + '\n            # Экспорт рекомендаций', content, flags=re.DOTALL)
print("✅ Улучшен раздел межфилиальных перемещений")

# Сохраняем улучшенный файл
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Все улучшения применены\!")
print("📊 Новый размер файла:", len(content), "символов")
PYTHON_EOF

# Запускаем улучшения
echo "🔧 Применяем улучшения..."
python3 /tmp/improve_features.py

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
echo "📤 Копируем улучшенный файл на сервер..."
scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/

# Перезапускаем на сервере
echo "🔄 Перезапускаем приложение..."
ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ ГОТОВО\! Улучшения применены:"
echo "   📊 ABC анализ: многоуровневая навигация по категориям в табличном виде"
echo "   🔄 Межфилиальные перемещения: детальные рекомендации ОТКУДА → КУДА с причинами"
echo "   📋 Добавлены приоритеты и причины перемещений"
echo ""
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"

# Очистка
rm -f /tmp/improve_features.py
