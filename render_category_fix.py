# Исправленная функция render_category_level

def render_category_level(tree, level=0, parent_path=""):
    """Рендерит уровень категорий с табличным отображением"""
    
    # Подготавливаем данные для ABC анализа
    level_data = []
    for name, data in tree.items():
        level_data.append({
            'name': name,
            'total_amount': data['total_amount'],
            'total_quantity': data['total_quantity'],
            'items_count': len(data['items']),
            'has_children': bool(data['children']),
            'path': parent_path + "/" + name if parent_path else name
        })
    
    # Вычисляем ABC
    abc_data = calculate_abc_for_level(level_data)
    
    if not abc_data:
        return
    
    # Метрики ABC
    if level == 0:  # Показываем метрики только на корневом уровне
        a_items = [item for item in abc_data if item['abc'] == 'A']
        b_items = [item for item in abc_data if item['abc'] == 'B']
        c_items = [item for item in abc_data if item['abc'] == 'C']
        
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
    
    # Показываем данные в табличном виде
    if level == 0:
        st.subheader("📋 Категории верхнего уровня")
    else:
        st.subheader(f"📋 Подкатегории (уровень {level + 1})")
    
    # Создаем DataFrame для таблицы
    table_data = []
    for item in abc_data[:20]:  # Ограничиваем количество
        table_data.append({
            'Категория': item['name'][:50],
            'ABC': item['abc'],
            'Выручка': f"{item['total_amount']:,.0f} ₸",
            'Количество': f"{item['total_quantity']:,.0f}",
            'Доля %': f"{item['percent']:.1f}%",
            'Товаров': item['items_count'],
            'Есть подкатегории': '✅' if item['has_children'] else '❌'
        })
    
    # Отображаем таблицу
    if table_data:
        df_table = pd.DataFrame(table_data)
        
        # Стилизуем таблицу по ABC
        def style_abc(row):
            if row['ABC'] == 'A':
                return ['background-color: #d4edda'] * len(row)
            elif row['ABC'] == 'B':
                return ['background-color: #fff3cd'] * len(row)
            else:
                return ['background-color: #f8d7da'] * len(row)
        
        styled_df = df_table.style.apply(style_abc, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Добавляем возможность перехода на следующий уровень
        st.subheader("🔍 Детальный просмотр")
        
        category_names = [item['name'] for item in abc_data if item['has_children']]
        if category_names:
            selected_category = st.selectbox(
                "Выберите категорию для детального просмотра:",
                options=[''] + category_names,
                key=f"category_select_level_{level}"
            )
            
            if selected_category:
                st.write(f"**Переход в категорию: {selected_category}**")
                if selected_category in tree:
                    render_category_level(tree[selected_category]['children'], level + 1, f"{parent_path}/{selected_category}" if parent_path else selected_category)
        
        # Показываем товары в выбранной категории
        product_category_names = [item['name'] for item in abc_data]
        if product_category_names:
            selected_product_category = st.selectbox(
                "Показать товары в категории:",
                options=[''] + product_category_names,
                key=f"product_select_level_{level}"
            )
            
            if selected_product_category and selected_product_category in tree:
                items = tree[selected_product_category]['items']
                if items:
                    st.subheader(f"🛍️ Товары в категории '{selected_product_category}'")
                    
                    # Создаем таблицу товаров
                    product_data = []
                    sorted_items = sorted(items, key=lambda x: x['amount'], reverse=True)[:50]  # Топ-50 товаров
                    
                    for i, product in enumerate(sorted_items):
                        # Простая ABC для товаров
                        if i < len(sorted_items) * 0.2:  # Топ 20%
                            abc_class = 'A'
                        elif i < len(sorted_items) * 0.5:  # Следующие 30%
                            abc_class = 'B'
                        else:
                            abc_class = 'C'
                        
                        product_data.append({
                            'Артикул': product['item_code'],
                            'Наименование': product['item_name'][:40],
                            'ABC': abc_class,
                            'Выручка': f"{product['amount']:,.0f} ₸",
                            'Количество': f"{product['quantity']:,.0f}",
                            'Филиал': product['branch']
                        })
                    
                    if product_data:
                        df_products = pd.DataFrame(product_data)
                        
                        def style_product_abc(row):
                            if row['ABC'] == 'A':
                                return ['background-color: #d4edda'] * len(row)
                            elif row['ABC'] == 'B':
                                return ['background-color: #fff3cd'] * len(row)
                            else:
                                return ['background-color: #f8d7da'] * len(row)
                        
                        styled_products = df_products.style.apply(style_product_abc, axis=1)
                        st.dataframe(styled_products, use_container_width=True, hide_index=True)