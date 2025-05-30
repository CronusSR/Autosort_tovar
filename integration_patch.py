#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕННЫЙ патч для интеграции системы множественных файлов
Исправляет ошибку KeyError: 'uploaded_files'
"""

import pandas as pd
import streamlit as st
from typing import Dict, List
import io
from datetime import datetime

def patch_existing_system():
    """
    Патч для добавления функциональности множественных файлов в существующую систему
    """
    
    # Проверяем наличие основной системы в session_state
    if 'inventory_system' not in st.session_state:
        try:
            from modular_inventory_system import ModularInventorySystem
            st.session_state.inventory_system = ModularInventorySystem()
        except ImportError:
            st.error("❌ Не найден модуль modular_inventory_system")
            return None
    
    system = st.session_state.inventory_system
    
    # ИСПРАВЛЕНИЕ: Добавляем систему множественных файлов если её нет
    if not hasattr(system, 'multiple_files_data'):
        system.multiple_files_data = {
            'uploaded_files': {},
            'processed_results': {},
            'combined_data': None,
            'processing_log': []
        }
    
    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Убеждаемся что все ключи существуют
    required_keys = ['uploaded_files', 'processed_results', 'combined_data', 'processing_log']
    for key in required_keys:
        if key not in system.multiple_files_data:
            system.multiple_files_data[key] = {} if key in ['uploaded_files', 'processed_results'] else ([] if key == 'processing_log' else None)
    
    return system

def add_multiple_files_interface_to_existing():
    """
    ИСПРАВЛЕННАЯ функция добавления интерфейса множественных файлов
    """
    
    # Инициализируем систему с проверкой ошибок
    system = patch_existing_system()
    if system is None:
        return False
    
    # Добавляем переключатель режимов
    with st.expander("🆕 НОВОЕ: Загрузка множественных файлов", expanded=False):
        st.markdown("""
        **🔥 Новая возможность!** Теперь вы можете загружать несколько файлов продаж одновременно:
        
        - 📁 Файлы из разных филиалов
        - 🔄 Автоматическое определение филиала по имени файла  
        - 📊 Объединение и суммирование ADS
        - 📈 Единый результат для всей сети
        """)
        
        use_multiple = st.checkbox(
            "🔄 Использовать загрузку множественных файлов",
            key="use_multiple_files_mode",
            help="Включите для загрузки файлов из нескольких филиалов"
        )
        
        if use_multiple:
            return render_multiple_files_interface_fixed(system)
    
    return False

def render_multiple_files_interface_fixed(system):
    """ИСПРАВЛЕННАЯ отрисовка интерфейса множественных файлов"""
    
    st.subheader("📂 Множественные файлы ADS")
    
    # ИСПРАВЛЕНИЕ: Безопасная проверка загруженных файлов
    try:
        uploaded_files_dict = system.multiple_files_data.get('uploaded_files', {})
        processed_results_dict = system.multiple_files_data.get('processed_results', {})
        combined_data = system.multiple_files_data.get('combined_data', None)
        processing_log = system.multiple_files_data.get('processing_log', [])
    except (AttributeError, KeyError) as e:
        st.error(f"❌ Ошибка доступа к данным: {e}")
        # Переинициализируем данные
        system.multiple_files_data = {
            'uploaded_files': {},
            'processed_results': {},
            'combined_data': None,
            'processing_log': []
        }
        uploaded_files_dict = {}
        processed_results_dict = {}
        combined_data = None
        processing_log = []
    
    # Показываем загруженные файлы
    if uploaded_files_dict:
        st.write("**📋 Загруженные файлы:**")
        
        files_info = []
        for filename, file_info in uploaded_files_dict.items():
            status = "✅ Обработан" if filename in processed_results_dict else "⏳ Ожидает"
            
            result = processed_results_dict.get(filename, {})
            items_count = result.get('total_items', 0) if result.get('success', False) else 0
            ads_value = result.get('total_ads', 0) if result.get('success', False) else 0
            
            files_info.append({
                'Файл': filename,
                'Филиал': file_info.get('branch_name', 'неопределен'),
                'Статус': status,
                'Товаров': items_count,
                'ADS': f"{ads_value:.2f}" if ads_value > 0 else "0"
            })
        
        if files_info:  # Дополнительная проверка
            files_df = pd.DataFrame(files_info)
            st.dataframe(files_df, use_container_width=True)
        
        # Кнопки управления
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Пересчитать все", key="recalc_multiple"):
                process_all_uploaded_files_fixed(system)
                st.rerun()
        
        with col2:
            if st.button("🗑️ Очистить все", key="clear_multiple"):
                clear_multiple_files_data_fixed(system)
                st.rerun()
    
    # Загрузка новых файлов
    st.write("**➕ Добавить файлы:**")
    
    uploaded_files = st.file_uploader(
        "Выберите файлы продаж",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        key="multiple_files_uploader",
        help="Выберите несколько файлов. Система определит филиал по имени файла."
    )
    
    if uploaded_files:
        st.info(f"📁 Выбрано {len(uploaded_files)} файлов")
        
        # Предварительный просмотр
        for file in uploaded_files:
            branch_name = extract_branch_name_simple(file.name)
            st.write(f"• **{file.name}** → {branch_name}")
        
        if st.button("📊 Обработать файлы", key="process_multiple_files"):
            add_and_process_files_fixed(system, uploaded_files)
            st.rerun()
    
    # Показываем результаты если есть
    if combined_data is not None:
        show_combined_results_fixed(system)
        return True  # Указываем что множественные файлы активны
    
    return False

def extract_branch_name_simple(filename: str) -> str:
    """Простое извлечение названия филиала из имени файла"""
    name = filename.lower().replace('.xlsx', '').replace('.xls', '')
    
    if 'шымкент' in name:
        return 'шымкент'
    elif 'астана' in name:
        return 'астана'
    elif 'алматы' in name:
        return 'алматы'
    elif 'барыс' in name:
        return 'барыс'
    elif 'казыб' in name:
        return 'казыбаева'
    elif 'актобе' in name:
        return 'актобе'
    elif 'караганда' in name:
        return 'караганда'
    else:
        return f"филиал_{name.replace(' ', '_')[:15]}"

def add_and_process_files_fixed(system, uploaded_files):
    """ИСПРАВЛЕННАЯ функция добавления и обработки новых файлов"""
    
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_files = len(uploaded_files)
        successful_count = 0
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Обработка {i+1}/{total_files}: {file.name}")
            
            # Определяем филиал
            branch_name = extract_branch_name_simple(file.name)
            
            # Сохраняем информацию о файле с проверкой
            if 'uploaded_files' not in system.multiple_files_data:
                system.multiple_files_data['uploaded_files'] = {}
            
            system.multiple_files_data['uploaded_files'][file.name] = {
                'branch_name': branch_name,
                'upload_time': datetime.now().isoformat(),
                'file_size': len(file.getvalue())
            }
            
            # Обрабатываем файл
            result = process_single_ads_file_fixed(file.getvalue(), file.name, branch_name)
            
            # Сохраняем результат с проверкой
            if 'processed_results' not in system.multiple_files_data:
                system.multiple_files_data['processed_results'] = {}
            
            system.multiple_files_data['processed_results'][file.name] = result
            
            # Логируем с проверкой
            if 'processing_log' not in system.multiple_files_data:
                system.multiple_files_data['processing_log'] = []
            
            if result['success']:
                successful_count += 1
                system.multiple_files_data['processing_log'].append(
                    f"✅ {file.name}: {result['total_items']} товаров, ADS: {result['total_ads']:.2f}"
                )
                st.success(f"✅ {file.name}: {result['total_items']} товаров")
            else:
                system.multiple_files_data['processing_log'].append(
                    f"❌ {file.name}: {result['error']}"
                )
                st.error(f"❌ {file.name}: {result['error']}")
            
            progress_bar.progress((i + 1) / total_files)
        
        # Очищаем индикаторы прогресса
        progress_bar.empty()
        status_text.empty()
        
        if successful_count > 0:
            # Объединяем данные
            combine_multiple_files_data_fixed(system)
            st.success(f"🎉 Успешно обработано {successful_count} из {total_files} файлов!")
        else:
            st.error("❌ Ни одного файла не удалось обработать")
            
    except Exception as e:
        st.error(f"❌ Критическая ошибка при обработке файлов: {str(e)}")
        # Переинициализируем данные в случае ошибки
        system.multiple_files_data = {
            'uploaded_files': {},
            'processed_results': {},
            'combined_data': None,
            'processing_log': [f"❌ Ошибка обработки: {str(e)}"]
        }

def process_single_ads_file_fixed(file_content: bytes, filename: str, branch_name: str) -> Dict:
    """ИСПРАВЛЕННАЯ обработка одного файла ADS"""
    try:
        # Читаем Excel
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        
        # Используем логику из исходной системы
        start_col_index = 12  # Колонка M
        end_col_index = 28    # Колонка AB+1
        start_row = 3         # Строка 4
        nomenclature_col = 1  # Колонка B
        
        if df.shape[1] < end_col_index:
            return {
                'success': False,
                'error': f'Недостаточно колонок: нужно {end_col_index}, есть {df.shape[1]}'
            }
        
        # Получаем номенклатуру
        if df.shape[0] <= start_row:
            return {
                'success': False,
                'error': f'Недостаточно строк: нужно больше {start_row}, есть {df.shape[0]}'
            }
        
        nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()
        
        # Очищаем
        nomenclature_clean = nomenclature_data.dropna()
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
        nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
        
        # Исключаем последнюю строку
        if len(nomenclature_clean) > 0:
            nomenclature_clean = nomenclature_clean[:-1]
        
        valid_indices = nomenclature_clean.index
        
        if len(nomenclature_clean) == 0:
            return {'success': False, 'error': 'Нет валидных товаров после очистки'}
        
        # Обрабатываем данные продаж
        sales_data = []
        
        for idx in valid_indices:
            try:
                item_name = str(nomenclature_clean.loc[idx]).strip()
                
                # Данные из колонок M:AB
                row_sales = df.iloc[idx, start_col_index:end_col_index].copy()
                row_numeric = pd.to_numeric(row_sales, errors='coerce').fillna(0)
                
                # ADS = среднее / 30
                average_value = row_numeric.mean()
                ads_value = average_value / 30
                
                sales_data.append({
                    'номенклатура': item_name,
                    'ads': ads_value,
                    'average_value': average_value,
                    'total_sales': row_numeric.sum(),
                    'branch': branch_name,
                    'source_file': filename
                })
            except Exception as e:
                # Пропускаем проблемные строки
                continue
        
        if not sales_data:
            return {'success': False, 'error': 'Не удалось обработать ни одного товара'}
        
        # Создаем DataFrame
        result_df = pd.DataFrame(sales_data)
        
        return {
            'success': True,
            'total_items': len(result_df),
            'total_ads': result_df['ads'].sum(),
            'average_ads': result_df['ads'].mean(),
            'data': result_df,
            'branch_name': branch_name
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Ошибка обработки файла: {str(e)}'}

def combine_multiple_files_data_fixed(system):
    """ИСПРАВЛЕННАЯ функция объединения данных из всех обработанных файлов"""
    try:
        all_dataframes = []
        
        # Безопасно получаем результаты обработки
        processed_results = system.multiple_files_data.get('processed_results', {})
        
        # Собираем все успешно обработанные файлы
        for filename, result in processed_results.items():
            if result.get('success', False) and 'data' in result:
                df = result['data']
                if isinstance(df, pd.DataFrame) and not df.empty:
                    all_dataframes.append(df)
        
        if not all_dataframes:
            system.multiple_files_data['combined_data'] = None
            return
        
        # Объединяем
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Обрабатываем дубликаты (суммируем ADS)
        initial_count = len(combined_df)
        
        combined_df = combined_df.groupby('номенклатура').agg({
            'ads': 'sum',
            'average_value': 'sum',
            'total_sales': 'sum',
            'branch': lambda x: ', '.join(x.unique()),
            'source_file': lambda x: ', '.join(x.unique())
        }).reset_index()
        
        final_count = len(combined_df)
        duplicates_merged = initial_count - final_count
        
        # Сохраняем результат
        system.multiple_files_data['combined_data'] = combined_df
        
        # Обновляем основную систему
        if hasattr(system, 'calculated_ads'):
            system.calculated_ads = combined_df[['номенклатура', 'ads', 'average_value', 'total_sales']].copy()
        if hasattr(system, 'sales_data'):
            system.sales_data = combined_df.copy()
        
        # Логируем
        if 'processing_log' not in system.multiple_files_data:
            system.multiple_files_data['processing_log'] = []
        
        system.multiple_files_data['processing_log'].append(
            f"🔄 Объединение: {final_count} уникальных товаров (объединено {duplicates_merged} дубликатов)"
        )
        
    except Exception as e:
        st.error(f"❌ Ошибка объединения данных: {str(e)}")
        if 'processing_log' not in system.multiple_files_data:
            system.multiple_files_data['processing_log'] = []
        system.multiple_files_data['processing_log'].append(f"❌ Ошибка объединения: {str(e)}")

def show_combined_results_fixed(system):
    """ИСПРАВЛЕННАЯ функция показа объединенных результатов"""
    try:
        st.subheader("📊 Объединенные результаты")
        
        combined_data = system.multiple_files_data.get('combined_data', None)
        
        if combined_data is None or combined_data.empty:
            st.warning("Нет объединенных данных")
            return
        
        # Общая статистика
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            processed_results = system.multiple_files_data.get('processed_results', {})
            files_count = len(processed_results)
            st.metric("Файлов обработано", files_count)
        
        with col2:
            st.metric("Уникальных товаров", len(combined_data))
        
        with col3:
            total_ads = combined_data['ads'].sum()
            st.metric("Общий ADS", f"{total_ads:.2f}")
        
        with col4:
            avg_ads = combined_data['ads'].mean()
            st.metric("Средний ADS", f"{avg_ads:.4f}")
        
        # Топ товары
        st.write("**🏆 Топ-10 товаров по суммарному ADS:**")
        
        if len(combined_data) > 0:
            display_columns = ['номенклатура', 'ads']
            if 'branch' in combined_data.columns:
                display_columns.append('branch')
            if 'source_file' in combined_data.columns:
                display_columns.append('source_file')
            
            # Берем только существующие колонки
            available_columns = [col for col in display_columns if col in combined_data.columns]
            
            top_items = combined_data.nlargest(10, 'ads')[available_columns].copy()
            
            # Переименовываем колонки для отображения
            column_mapping = {
                'номенклатура': 'Товар',
                'ads': 'Суммарный ADS',
                'branch': 'Филиалы',
                'source_file': 'Файлы'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in top_items.columns:
                    top_items = top_items.rename(columns={old_name: new_name})
            
            st.dataframe(top_items, use_container_width=True)
        
        # Лог обработки
        processing_log = system.multiple_files_data.get('processing_log', [])
        if processing_log:
            with st.expander("📋 Лог обработки"):
                for log_entry in processing_log:
                    st.write(log_entry)
        
        # Экспорт
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Экспорт в Excel", key="export_combined"):
                try:
                    excel_buffer = create_combined_excel_export_fixed(system)
                    
                    st.download_button(
                        label="💾 Скачать Excel",
                        data=excel_buffer,
                        file_name=f"combined_ads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"❌ Ошибка экспорта Excel: {str(e)}")
        
        with col2:
            if st.button("📄 JSON данные", key="export_json"):
                try:
                    json_data = create_combined_json_export_fixed(system)
                    
                    st.download_button(
                        label="💾 Скачать JSON",
                        data=json_data.encode('utf-8'),
                        file_name=f"combined_ads_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(f"❌ Ошибка экспорта JSON: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Ошибка отображения результатов: {str(e)}")

def create_combined_excel_export_fixed(system) -> bytes:
    """ИСПРАВЛЕННОЕ создание Excel файла с объединенными данными"""
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Объединенные данные
            combined_data = system.multiple_files_data.get('combined_data', None)
            if combined_data is not None and not combined_data.empty:
                combined_data.to_excel(writer, sheet_name='Combined_Data', index=False)
            
            # Отдельные листы по филиалам
            processed_results = system.multiple_files_data.get('processed_results', {})
            for filename, result in processed_results.items():
                if result.get('success', False) and 'data' in result:
                    try:
                        branch_name = result.get('branch_name', 'unknown')[:20]  # Ограничение длины
                        # Убираем недопустимые символы для имени листа Excel
                        safe_branch_name = "".join(c for c in branch_name if c.isalnum() or c in (' ', '_', '-'))[:31]
                        result['data'].to_excel(writer, sheet_name=safe_branch_name, index=False)
                    except Exception as e:
                        # Пропускаем проблемные листы
                        continue
            
            # Сводка
            summary_data = []
            for filename, result in processed_results.items():
                if result.get('success', False):
                    summary_data.append({
                        'Файл': filename,
                        'Филиал': result.get('branch_name', 'неизвестно'),
                        'Товаров': result.get('total_items', 0),
                        'ADS': result.get('total_ads', 0)
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Лог
            processing_log = system.multiple_files_data.get('processing_log', [])
            if processing_log:
                log_df = pd.DataFrame(processing_log, columns=['Log'])
                log_df.to_excel(writer, sheet_name='Processing_Log', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Ошибка создания Excel: {str(e)}")
        return b""

def create_combined_json_export_fixed(system) -> str:
    """ИСПРАВЛЕННОЕ создание JSON данных"""
    import json
    
    try:
        combined_data = system.multiple_files_data.get('combined_data', None)
        
        if combined_data is None or combined_data.empty:
            return json.dumps({'error': 'Нет данных'}, ensure_ascii=False, indent=2)
        
        processed_results = system.multiple_files_data.get('processed_results', {})
        
        json_data = {
            'metadata': {
                'processing_date': datetime.now().isoformat(),
                'files_processed': len(processed_results),
                'total_unique_items': len(combined_data),
                'method': 'multiple_files_combination_fixed'
            },
            'summary_stats': {
                'total_ads': float(combined_data['ads'].sum()),
                'average_ads': float(combined_data['ads'].mean()),
                'max_ads': float(combined_data['ads'].max()),
                'min_ads': float(combined_data['ads'].min())
            },
            'files_info': {},
            'items': []
        }
        
        # Информация о файлах
        for filename, result in processed_results.items():
            if result.get('success', False):
                json_data['files_info'][filename] = {
                    'branch': result.get('branch_name', 'неизвестно'),
                    'items_count': result.get('total_items', 0),
                    'ads_total': float(result.get('total_ads', 0))
                }
        
        # Данные товаров
        for _, row in combined_data.iterrows():
            item_data = {
                'nomenclature': row['номенклатура'],
                'ads_total': float(row['ads']),
                'total_sales': float(row.get('total_sales', 0))
            }
            
            # Добавляем дополнительные поля если они есть
            if 'branch' in row:
                item_data['branches'] = row['branch']
            if 'source_file' in row:
                item_data['source_files'] = row['source_file']
            if 'average_value' in row:
                item_data['average_monthly'] = float(row['average_value'])
            
            json_data['items'].append(item_data)
        
        return json.dumps(json_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({'error': f'Ошибка создания JSON: {str(e)}'}, ensure_ascii=False, indent=2)

def process_all_uploaded_files_fixed(system):
    """ИСПРАВЛЕННАЯ функция пересчета всех загруженных файлов"""
    try:
        # Очищаем результаты
        system.multiple_files_data['processed_results'] = {}
        system.multiple_files_data['processing_log'] = []
        system.multiple_files_data['combined_data'] = None
        
        st.info("🔄 Данные очищены для пересчета. Загрузите файлы заново.")
        
    except Exception as e:
        st.error(f"❌ Ошибка при пересчете: {str(e)}")

def clear_multiple_files_data_fixed(system):
    """ИСПРАВЛЕННАЯ функция очистки всех данных множественных файлов"""
    try:
        # Полная очистка
        system.multiple_files_data = {
            'uploaded_files': {},
            'processed_results': {},
            'combined_data': None,
            'processing_log': []
        }
        
        # Очищаем основные данные системы
        if hasattr(system, 'calculated_ads'):
            system.calculated_ads = None
        if hasattr(system, 'sales_data'):
            system.sales_data = None
        
        st.success("✅ Все данные множественных файлов очищены!")
        
    except Exception as e:
        st.error(f"❌ Ошибка при очистке: {str(e)}")

# Тестовая функция для проверки работоспособности
def test_integration_patch():
    """Тестирование исправленного патча"""
    
    st.title("🧪 Тест исправленного патча")
    
    try:
        system = patch_existing_system()
        
        if system is not None:
            st.success("✅ Система инициализирована успешно")
            
            # Проверяем структуру данных
            if hasattr(system, 'multiple_files_data'):
                st.success("✅ Структура multiple_files_data создана")
                
                required_keys = ['uploaded_files', 'processed_results', 'combined_data', 'processing_log']
                missing_keys = [key for key in required_keys if key not in system.multiple_files_data]
                
                if not missing_keys:
                    st.success("✅ Все необходимые ключи присутствуют")
                    
                    # Показываем структуру
                    st.write("**Структура данных:**")
                    for key, value in system.multiple_files_data.items():
                        data_type = type(value).__name__
                        if isinstance(value, dict):
                            count = len(value)
                            st.write(f"- {key}: {data_type} ({count} элементов)")
                        elif isinstance(value, list):
                            count = len(value)
                            st.write(f"- {key}: {data_type} ({count} элементов)")
                        else:
                            st.write(f"- {key}: {data_type}")
                else:
                    st.error(f"❌ Отсутствуют ключи: {missing_keys}")
            else:
                st.error("❌ Атрибут multiple_files_data не создан")
        else:
            st.error("❌ Не удалось инициализировать систему")
            
    except Exception as e:
        st.error(f"❌ Ошибка тестирования: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    # Запуск тестирования
    test_integration_patch()
    
    st.markdown("""
    ---
    ## 🔧 Инструкция по интеграции (ИСПРАВЛЕННАЯ)
    
    1. **Замените старый файл** `integration_patch.py` этим исправленным кодом
    
    2. **В файле streamlit_modular_app.py** в функции `ads_calculation_page_updated()` добавьте:
    
    ```python
    def ads_calculation_page_updated(system):
        st.header("📊 Расчет ADS")
        
        # ⬇️ ДОБАВЬТЕ ЭТИ СТРОКИ:
        try:
            from integration_patch import add_multiple_files_interface_to_existing
            
            if add_multiple_files_interface_to_existing():
                return  # Если используются множественные файлы, выходим
        except Exception as e:
            st.error(f"Ошибка загрузки множественных файлов: {e}")
        # ⬆️ КОНЕЦ ДОБАВЛЕНИЯ
        
        # Остальной код остается без изменений...
    ```
    
    3. **Перезапустите приложение**
    
    ## ✅ Исправления в этой версии:
    
    - ✅ Исправлена ошибка `KeyError: 'uploaded_files'`
    - ✅ Добавлены проверки существования всех ключей
    - ✅ Безопасная инициализация структуры данных
    - ✅ Обработка ошибок на всех уровнях
    - ✅ Автоматическое восстановление структуры при ошибках
    - ✅ Улучшенное логирование ошибок
    - ✅ Валидация данных перед обработкой
    
    ## 🧪 Тестирование:
    
    После интеграции проверьте:
    1. Отсутствие ошибок при загрузке страницы
    2. Появление раздела "НОВОЕ: Загрузка множественных файлов"
    3. Возможность загрузки и обработки файлов
    4. Корректное отображение результатов
    """)