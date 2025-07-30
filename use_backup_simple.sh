#\!/bin/bash
# Простое восстановление из backup версии

echo "🔄 Восстановление из стабильной backup версии"
echo "=============================================="

# Работаем на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "📋 Проверяем доступные backup файлы..."
ls -la webhook_persistent_app*.py

echo ""
echo "🔄 Используем backup версию 120403 (самая стабильная)..."

# Проверяем есть ли backup версия
if [ -f "webhook_persistent_app_backup_20250724_120403.py" ]; then
    echo "✅ Найден backup файл webhook_persistent_app_backup_20250724_120403.py"
    
    # Заменяем основной файл на backup
    cp webhook_persistent_app_backup_20250724_120403.py webhook_persistent_app.py
    
    echo "✅ Файл заменен на стабильную backup версию"
    
elif [ -f "webhook_persistent_app_backup_ui_20250724_081953.py" ]; then
    echo "✅ Используем UI backup версию"
    cp webhook_persistent_app_backup_ui_20250724_081953.py webhook_persistent_app.py
    
else
    echo "❌ Backup файлы не найдены, создаем минимальный рабочий файл..."
    
    # Создаем минимальный рабочий файл
    cat > webhook_persistent_app.py << 'MINIMAL_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from webhook_data_accumulator import WebhookDataAccumulator

# Конфигурация страницы
st.set_page_config(
    page_title="Система анализа",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Система анализа складов")

# Инициализация аккумулятора данных
if 'accumulator' not in st.session_state:
    st.session_state.accumulator = WebhookDataAccumulator()

accumulator = st.session_state.accumulator

# Загрузка данных
st.header("📈 Анализ данных")

sales_data = accumulator.get_sales_data()
stock_data = accumulator.get_stock_data()

if not sales_data.empty:
    st.success(f"✅ Загружено {len(sales_data)} записей продаж")
    
    # Основные метрики
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_amount = sales_data['amount'].sum()
        st.metric("💰 Общая выручка", f"{total_amount:,.0f} ₸")
    
    with col2:
        total_quantity = sales_data['quantity'].sum()
        st.metric("📦 Общее количество", f"{total_quantity:,.0f}")
    
    with col3:
        unique_items = sales_data['item_code'].nunique()
        st.metric("🛍️ Уникальных товаров", f"{unique_items:,}")
    
    # Простая таблица топ товаров
    st.subheader("🏆 Топ-20 товаров по выручке")
    
    top_items = sales_data.groupby(['item_code', 'item_name']).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).reset_index().nlargest(20, 'amount')
    
    top_items['amount'] = top_items['amount'].apply(lambda x: f"{x:,.0f} ₸")
    top_items['quantity'] = top_items['quantity'].apply(lambda x: f"{x:,.0f}")
    top_items.columns = ['Код', 'Наименование', 'Выручка', 'Количество']
    
    st.dataframe(top_items, use_container_width=True, hide_index=True)
    
else:
    st.warning("⚠️ Нет данных о продажах")

if not stock_data.empty:
    st.success(f"✅ Загружено {len(stock_data)} записей остатков")
else:
    st.warning("⚠️ Нет данных об остатках")

st.info("📊 Базовая версия приложения восстановлена")
MINIMAL_EOF
    
    echo "✅ Создан минимальный рабочий файл"
fi

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
sleep 3
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "Запущен с PID: $\!"

echo ""
echo "✅ ПРИЛОЖЕНИЕ ВОССТАНОВЛЕНО\!"
echo "📋 Логи: tail -f webhook_8502.log"
REMOTE_EOF

echo ""
echo "🎉 Стабильная версия восстановлена\!"
echo "📋 Проверить: ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
