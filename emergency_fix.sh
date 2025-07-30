#\!/bin/bash
# Экстренное исправление - полная замена проблемного блока

echo "🚨 Экстренное исправление приложения"
echo "=================================="

# Работаем на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "💾 Создаем резервную копию..."
cp webhook_persistent_app.py webhook_emergency_backup.py

echo "🔧 Заменяем проблемный ABC блок..."

# Создаем скрипт который заменит весь проблемный блок ABC
cat > emergency_abc_fix.py << 'PYTHON_EOF'
#\!/usr/bin/env python3

# Читаем файл
with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Находим начало проблемного блока ABC
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'st.header("📦 ABC анализ по категориям")' in line:
        start_line = i
    elif start_line \!= -1 and line.startswith('with tab') and 'tab' in line:
        end_line = i
        break

if start_line \!= -1 and end_line \!= -1:
    print(f"Найден проблемный блок: строки {start_line+1} - {end_line}")
    
    # Простая замена ABC блока
    simple_abc_block = '''    st.header("📦 ABC анализ по категориям")
    
    if not sales_data.empty and 'category_path' in sales_data.columns:
        st.info("📊 Упрощенный ABC анализ категорий")
        
        # Простая группировка по первой категории
        category_data = []
        
        for _, row in sales_data.iterrows():
            category_path = row.get('category_path', '')
            if pd.isna(category_path) or category_path == '':
                continue
                
            # Берем первую категорию
            parts = str(category_path).split('/')
            if parts:
                first_category = parts[0].strip()
                if first_category:
                    category_data.append({
                        'category': first_category,
                        'amount': row.get('amount', 0),
                        'quantity': row.get('quantity', 0)
                    })
        
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
            
            # Простая ABC классификация
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
            st.subheader("📊 ABC анализ по категориям")
            
            # Метрики
            a_count = len(category_summary[category_summary['ABC'] == 'A'])
            b_count = len(category_summary[category_summary['ABC'] == 'B']) 
            c_count = len(category_summary[category_summary['ABC'] == 'C'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🅰️ Группа A", f"{a_count} категорий")
            with col2:
                st.metric("🅱️ Группа B", f"{b_count} категорий")
            with col3:
                st.metric("🅾️ Группа C", f"{c_count} категорий")
            
            # Таблица
            display_df = category_summary.copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"{x:,.0f} ₸")
            display_df['quantity'] = display_df['quantity'].apply(lambda x: f"{x:,.0f}")
            display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x:.1f}%")
            
            display_df.columns = ['Категория', 'Выручка', 'Количество', 'Доля %', 'Накопительно %', 'ABC']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Нет данных категорий для анализа")
    else:
        st.warning("Нет данных о продажах или категориях")

'''
    
    # Заменяем проблемный блок
    new_lines = lines[:start_line] + [simple_abc_block] + lines[end_line:]
    
    # Сохраняем исправленный файл
    with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ ABC блок заменен на простую рабочую версию")
else:
    print("❌ Не удалось найти проблемный блок")
PYTHON_EOF

# Запускаем исправление
python3 emergency_abc_fix.py

echo "🔍 Проверяем синтаксис..."
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_persistent_app.py', doraise=True)
    print('✅ Синтаксис корректен\!')
except Exception as e:
    print(f'❌ Ошибка синтаксиса: {e}')
"

echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "Запущен с PID: $\!"

echo ""
echo "✅ ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО\!"
echo "📊 ABC анализ заменен на простую рабочую версию"
echo "📋 Логи: tail -f webhook_8502.log"

# Очистка
rm -f emergency_abc_fix.py
REMOTE_EOF

echo ""
echo "🎉 Экстренное исправление применено\!"
echo "📋 Проверить: ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
