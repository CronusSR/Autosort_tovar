#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Исправленный блок ABC анализа
abc_block = '''    st.header("📦 ABC анализ по категориям")
    
    if not sales_data.empty and 'category_path' in sales_data.columns:
        st.info("📊 ABC анализ категорий (исправленная версия)")
        
        # Правильная группировка по категориям (предпоследняя в пути)
        category_data = []
        
        for _, row in sales_data.iterrows():
            category_path = row.get('category_path', '')
            if pd.isna(category_path) or category_path == '':
                continue
                
            # Разбиваем путь категории
            # Пример: "19*0,8мм ПВХ/Кромка ПВХ Китай/Кромка ПВХ/Кромочные материалы/Мебельная фурнитура/"
            # Нужна: "Кромочные материалы" (предпоследняя, исключая "Мебельная фурнитура")
            parts = [p.strip() for p in str(category_path).split('/') if p.strip()]
            
            target_category = None
            
            if len(parts) >= 2:
                # Убираем "Мебельная фурнитура" если она последняя
                if parts[-1] == "Мебельная фурнитура":
                    parts = parts[:-1]
                
                # Берем последнюю оставшуюся категорию
                if parts:
                    target_category = parts[-1]  # "Кромочные материалы", "Ручки, крючки, опоры"
            
            if target_category:
                category_data.append({
                    'category': target_category,
                    'amount': row.get('amount', 0),
                    'quantity': row.get('quantity', 0),
                    'original_path': category_path
                })
        
        # Отладочная информация
        if st.checkbox("🔍 Показать примеры обработки категорий", key="debug_categories"):
            st.write("**Примеры обработки путей категорий:**")
            
            sample_paths = sales_data['category_path'].dropna().unique()[:5]
            for i, path in enumerate(sample_paths):
                parts = [p.strip() for p in str(path).split('/') if p.strip()]
                
                # Применяем ту же логику
                if parts and parts[-1] == "Мебельная фурнитура":
                    parts = parts[:-1]
                
                target_category = parts[-1] if parts else "Не определена"
                
                st.write(f"{i+1}. `{path}`")
                st.write(f"   → **Выбранная категория: {target_category}**")
                st.write("---")
        
        if category_data:
            # Группируем данные
            import pandas as pd
            cat_df = pd.DataFrame(category_data)
            category_summary = cat_df.groupby('category').agg({
                'amount': 'sum',
                'quantity': 'sum'
            }).reset_index()
            
            # Сортируем по выручке
            category_summary = category_summary.sort_values('amount', ascending=False)
            
            # ABC классификация
            total_amount = category_summary['amount'].sum()
            category_summary['percentage'] = (category_summary['amount'] / total_amount * 100) if total_amount > 0 else 0
            category_summary['cumulative'] = category_summary['percentage'].cumsum()
            
            # ABC группы
            def get_abc(cum_perc):
                if cum_perc <= 80:
                    return 'A'
                elif cum_perc <= 95:
                    return 'B'
                else:
                    return 'C'
            
            category_summary['ABC'] = category_summary['cumulative'].apply(get_abc)
            
            # Показываем результаты
            st.subheader("📊 ABC анализ по правильным категориям")
            
            # Метрики
            a_count = len(category_summary[category_summary['ABC'] == 'A'])
            b_count = len(category_summary[category_summary['ABC'] == 'B']) 
            c_count = len(category_summary[category_summary['ABC'] == 'C'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                a_amount = category_summary[category_summary['ABC'] == 'A']['amount'].sum()
                st.metric("🅰️ Группа A", f"{a_count} категорий", f"{a_amount:,.0f} ₸")
            with col2:
                b_amount = category_summary[category_summary['ABC'] == 'B']['amount'].sum()
                st.metric("🅱️ Группа B", f"{b_count} категорий", f"{b_amount:,.0f} ₸")
            with col3:
                c_amount = category_summary[category_summary['ABC'] == 'C']['amount'].sum()
                st.metric("🅾️ Группа C", f"{c_count} категорий", f"{c_amount:,.0f} ₸")
            
            # Таблица
            display_df = category_summary.copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"{x:,.0f} ₸")
            display_df['quantity'] = display_df['quantity'].apply(lambda x: f"{x:,.0f}")
            display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x:.1f}%")
            display_df['cumulative'] = display_df['cumulative'].apply(lambda x: f"{x:.1f}%")
            
            display_df.columns = ['Категория', 'Выручка', 'Количество', 'Доля %', 'Накопительно %', 'ABC']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # График
            st.subheader("📈 Топ-10 категорий по выручке")
            top_10 = category_summary.head(10)
            
            fig = px.bar(
                top_10,
                x='category',
                y='amount',
                color='ABC',
                title='Топ-10 категорий по выручке',
                color_discrete_map={'A': '#28a745', 'B': '#ffc107', 'C': '#dc3545'}
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Нет данных категорий для анализа")
    else:
        st.warning("Нет данных о продажах или категориях")
'''

# Читаем текущий файл
with open('/opt/inventory_system/webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим ABC блок и заменяем его
import re

# Ищем начало ABC блока
start_pattern = r'st\.header\("📦 ABC анализ по категориям"\)'
start_match = re.search(start_pattern, content)

if start_match:
    start_pos = start_match.start()
    
    # Ищем конец блока (следующий with tab или конец файла)
    remaining_content = content[start_pos:]
    end_pattern = r'\nwith tab\d+:'
    end_match = re.search(end_pattern, remaining_content)
    
    if end_match:
        end_pos = start_pos + end_match.start()
        # Заменяем блок
        new_content = content[:start_pos] + abc_block + content[end_pos:]
    else:
        # Если не найден конец, заменяем до конца файла
        new_content = content[:start_pos] + abc_block
    
    # Сохраняем
    with open('/opt/inventory_system/webhook_persistent_app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ ABC блок успешно заменен\!")
else:
    print("❌ ABC блок не найден")
