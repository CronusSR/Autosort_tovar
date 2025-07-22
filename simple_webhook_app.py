#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенное приложение для мониторинга webhook данных
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import time

# Настройка страницы
st.set_page_config(
    page_title="🤖 Webhook мониторинг",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 Мониторинг Webhook данных от 1С")
    st.markdown("*Отслеживание файлов, получаемых от 1С через webhook*")
    
    # Статус webhook сервера
    st.markdown("### 🔌 Статус webhook системы")
    
    webhook_status = check_webhook_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if webhook_status['running']:
            st.success("✅ Директория webhook найдена")
        else:
            st.error("❌ Директория webhook отсутствует")
    
    with col2:
        st.metric("Последнее обновление", webhook_status['last_update'])
    
    with col3:
        st.metric("Файлов найдено", f"{webhook_status['files_count']}")
    
    # Информация о файлах
    st.markdown("### 📁 Доступные файлы")
    
    webhook_dir = Path('./webhook_uploads')
    
    if webhook_dir.exists():
        files = list(webhook_dir.glob('*.json'))
        
        if files:
            # Создаем таблицу файлов
            file_data = []
            
            for file_path in files:
                stat = file_path.stat()
                file_type = "Продажи" if file_path.name.startswith('sales_') else "Остатки" if file_path.name.startswith('stock_') else "Неизвестно"
                
                file_data.append({
                    'Имя файла': file_path.name,
                    'Тип': file_type,
                    'Размер (байт)': stat.st_size,
                    'Дата изменения': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Сортируем по дате изменения
            file_data.sort(key=lambda x: x['Дата изменения'], reverse=True)
            
            df = pd.DataFrame(file_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Кнопки действий
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Обновить список"):
                    st.rerun()
            
            with col2:
                selected_file = st.selectbox("Выберите файл для просмотра:", [f['Имя файла'] for f in file_data])
            
            # Просмотр содержимого файла
            if selected_file and st.button("👁️ Просмотреть содержимое"):
                show_file_content(webhook_dir / selected_file)
                
        else:
            st.info("📭 Нет загруженных файлов")
            st.markdown("**Инструкции для программиста 1С:**")
            st.code("""
POST http://your-server:5000/webhook/sales
Content-Type: application/json
X-Hub-Signature-256: sha256=<signature>

POST http://your-server:5000/webhook/stock
Content-Type: application/json  
X-Hub-Signature-256: sha256=<signature>
            """)
    
    else:
        st.warning("⚠️ Директория webhook_uploads не найдена")
        st.info("Запустите webhook сервер: `python webhook_receiver.py`")
    
    # Автоматическое обновление
    auto_refresh = st.checkbox("🔄 Автоматическое обновление (каждые 30 сек)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()

def check_webhook_status():
    """Проверяет статус webhook директории"""
    webhook_dir = Path('./webhook_uploads')
    
    status = {
        'running': webhook_dir.exists(),
        'last_update': 'Никогда',
        'files_count': 0
    }
    
    if webhook_dir.exists():
        files = list(webhook_dir.glob('*.json'))
        status['files_count'] = len(files)
        
        if files:
            # Находим самый новый файл
            newest_file = max(files, key=lambda x: x.stat().st_mtime)
            last_modified = datetime.fromtimestamp(newest_file.stat().st_mtime)
            status['last_update'] = last_modified.strftime('%Y-%m-%d %H:%M:%S')
    
    return status

def show_file_content(file_path):
    """Показывает содержимое файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.markdown(f"### 📄 Содержимое файла: {file_path.name}")
        
        # Показываем структуру данных
        if isinstance(data, list):
            st.info(f"📋 Массив из {len(data)} элементов")
            if len(data) > 0:
                st.json(data[0])  # Показываем первый элемент
        elif isinstance(data, dict):
            st.info("📋 Объект JSON")
            st.json(data)
        
        # Показываем первые несколько строк как текст
        st.markdown("**Превью файла:**")
        with open(file_path, 'r', encoding='utf-8') as f:
            preview = f.read()[:2000]  # Первые 2000 символов
            st.code(preview, language='json')
            
    except Exception as e:
        st.error(f"❌ Ошибка чтения файла: {e}")

if __name__ == "__main__":
    main()