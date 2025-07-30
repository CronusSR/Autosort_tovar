# ФАЙЛ: json_download_fix.py


import streamlit as st
import json
import pandas as pd
from datetime import datetime

def create_json_download_section(system):
    """
    Создает секцию для скачивания JSON с несколькими способами
    Замените этой функцией проблемную часть в вашем Streamlit коде
    """
    
    st.subheader("📄 Скачивание JSON данных")
    
    # Проверяем наличие JSON данных
    if not hasattr(system, '_json_data') or 'ads' not in system._json_data:
        st.warning("JSON данные недоступны. Сначала обработайте файл ADS.")
        return
    
    try:
        # Получаем JSON данные
        json_data = system._json_data['ads']
        
        # Создаем JSON строку
        json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        # Информация о JSON
        st.info(f"""
        **JSON готов к скачиванию:**
        - Размер: {len(json_string):,} символов
        - Товаров: {json_data.get('metadata', {}).get('total_items', 0)}
        - Метод: {json_data.get('metadata', {}).get('calculation_method', 'неизвестно')}
        """)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ads_data_{timestamp}.json"
        
        # СПОСОБ 1: Стандартная кнопка скачивания
        st.subheader("🔹 Способ 1: Прямое скачивание")
        
        download_success = st.download_button(
            label="💾 Скачать JSON файл",
            data=json_string.encode('utf-8'),
            file_name=filename,
            mime="application/json",
            key="json_download_main"
        )
        
        if download_success:
            st.success("✅ Файл готов к скачиванию!")
        
        # СПОСОБ 2: Текстовая область для копирования
        st.subheader("🔹 Способ 2: Копирование текста")
        
        with st.expander("📋 JSON для копирования"):
            st.text_area(
                "Скопируйте JSON данные:",
                value=json_string,
                height=200,
                key="json_copy_area"
            )
            st.info("💡 Выделите весь текст (Ctrl+A), скопируйте (Ctrl+C) и сохраните в файл .json")
        
        # СПОСОБ 3: Отображение по частям
        st.subheader("🔹 Способ 3: Просмотр по частям")
        
        # Показываем метаданные
        if st.button("👁️ Показать метаданные", key="show_metadata"):
            st.json(json_data.get('metadata', {}))
        
        # Показываем статистику
        if st.button("📊 Показать статистику", key="show_stats"):
            st.json(json_data.get('summary_stats', {}))
        
        # Показываем образцы товаров
        if st.button("📦 Показать примеры товаров", key="show_items"):
            items = json_data.get('items', [])
            if items:
                sample_items = items[:5]  # Первые 5 товаров
                st.json(sample_items)
                st.info(f"Показано 5 из {len(items)} товаров")
        
        # СПОСОБ 4: Сохранение на сервере (если есть доступ)
        st.subheader("🔹 Способ 4: Сохранение локально")
        
        if st.button("💾 Сохранить на сервере", key="save_local"):
            try:
                # Пытаемся сохранить файл локально
                local_filename = f"json_exports/{filename}"
                
                # Создаем папку если её нет
                import os
                os.makedirs("json_exports", exist_ok=True)
                
                # Сохраняем файл
                with open(local_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ Файл сохранен как: {local_filename}")
                st.info("Найдите файл в папке json_exports/ на сервере")
                
            except Exception as e:
                st.error(f"❌ Не удалось сохранить локально: {str(e)}")
        
        # СПОСОБ 5: Разбивка на части для больших файлов
        if len(json_string) > 100000:  # Если файл большой (>100KB)
            st.subheader("🔹 Способ 5: Скачивание частями")
            st.warning("Файл большой, скачиваем по частям")
            
            # Метаданные отдельно
            metadata_json = json.dumps(json_data.get('metadata', {}), ensure_ascii=False, indent=2)
            st.download_button(
                "📋 Скачать метаданные",
                data=metadata_json.encode('utf-8'),
                file_name=f"metadata_{timestamp}.json",
                mime="application/json",
                key="download_metadata"
            )
            
            # Статистика отдельно
            stats_json = json.dumps(json_data.get('summary_stats', {}), ensure_ascii=False, indent=2)
            st.download_button(
                "📊 Скачать статистику", 
                data=stats_json.encode('utf-8'),
                file_name=f"stats_{timestamp}.json",
                mime="application/json",
                key="download_stats"
            )
            
            # Товары частями
            items = json_data.get('items', [])
            if items:
                chunk_size = 1000  # По 1000 товаров
                chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
                
                for i, chunk in enumerate(chunks):
                    chunk_json = json.dumps(chunk, ensure_ascii=False, indent=2)
                    st.download_button(
                        f"📦 Скачать товары {i+1}/{len(chunks)} ({len(chunk)} шт)",
                        data=chunk_json.encode('utf-8'),
                        file_name=f"items_part_{i+1}_{timestamp}.json",
                        mime="application/json",
                        key=f"download_chunk_{i}"
                    )
        
    except Exception as e:
        st.error(f"❌ Ошибка при подготовке JSON: {str(e)}")
        
        # Диагностическая информация
        st.subheader("🔧 Диагностика")
        st.write("**Доступные атрибуты системы:**")
        attrs = [attr for attr in dir(system) if not attr.startswith('_')]
        st.write(attrs)
        
        if hasattr(system, '_json_data'):
            st.write("**Ключи в _json_data:**")
            st.write(list(system._json_data.keys()))

def simple_json_download(json_data, filename=None):
    """
    Простая функция для скачивания JSON
    Используйте эту функцию если остальные способы не работают
    """
    
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ads_data_{timestamp}.json"
    
    # Преобразуем в строку
    if isinstance(json_data, dict):
        json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
    else:
        json_string = str(json_data)
    
    # Кнопка скачивания
    return st.download_button(
        label=f"💾 Скачать {filename}",
        data=json_string.encode('utf-8'),
        file_name=filename,
        mime="application/json",
        help="Нажмите для скачивания JSON файла"
    )

def debug_json_system(system):
    """
    Отладочная функция для диагностики проблем с JSON
    """
    
    st.subheader("🔧 Диагностика JSON системы")
    
    # Проверяем наличие атрибутов
    has_json_data = hasattr(system, '_json_data')
    st.write(f"**Атрибут _json_data существует:** {'✅' if has_json_data else '❌'}")
    
    if has_json_data:
        json_data = system._json_data
        st.write(f"**Тип _json_data:** {type(json_data)}")
        st.write(f"**Ключи в _json_data:** {list(json_data.keys())}")
        
        if 'ads' in json_data:
            ads_data = json_data['ads']
            st.write(f"**Тип ads данных:** {type(ads_data)}")
            st.write(f"**Размер ads данных:** {len(str(ads_data))} символов")
            
            # Проверяем структуру
            if isinstance(ads_data, dict):
                st.write(f"**Ключи в ads:** {list(ads_data.keys())}")
                
                if 'items' in ads_data:
                    items = ads_data['items']
                    st.write(f"**Количество товаров:** {len(items)}")
    
    # Проверяем другие атрибуты
    has_calculated_ads = hasattr(system, 'calculated_ads')
    st.write(f"**Атрибут calculated_ads существует:** {'✅' if has_calculated_ads else '❌'}")
    
    if has_calculated_ads and system.calculated_ads is not None:
        st.write(f"**Размер calculated_ads:** {len(system.calculated_ads)} строк")

