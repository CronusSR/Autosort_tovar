# fix_arrow_serialization.py
"""
Исправление ошибки сериализации DataFrame в Arrow для Streamlit
"""

def fix_dataframe_for_streamlit(df):
    """
    Исправляет DataFrame для корректного отображения в Streamlit
    
    Args:
        df: DataFrame с потенциальными проблемами типов данных
        
    Returns:
        df: Исправленный DataFrame
    """
    
    if df is None or df.empty:
        return df
    
    df_fixed = df.copy()
    
    # Исправляем колонку "Месяцев запаса"
    if 'Месяцев запаса' in df_fixed.columns:
        # Заменяем infinity символы на числовое значение
        df_fixed['Месяцев запаса'] = df_fixed['Месяцев запаса'].astype(str)
        df_fixed['Месяцев запаса'] = df_fixed['Месяцев запаса'].replace('∞', '999+')
        df_fixed['Месяцев запаса'] = df_fixed['Месяцев запаса'].replace('inf', '999+')
        df_fixed['Месяцев запаса'] = df_fixed['Месяцев запаса'].replace('nan', '0')
        
        # Преобразуем в строковый тип для безопасности
        df_fixed['Месяцев запаса'] = df_fixed['Месяцев запаса'].astype(str)
    
    # Исправляем другие проблемные колонки
    for col in df_fixed.columns:
        if df_fixed[col].dtype == 'object':
            # Заменяем NaN на пустые строки
            df_fixed[col] = df_fixed[col].fillna('')
            
            # Преобразуем все в строки для object колонок
            df_fixed[col] = df_fixed[col].astype(str)
            
            # Заменяем проблемные значения
            df_fixed[col] = df_fixed[col].replace('nan', '')
            df_fixed[col] = df_fixed[col].replace('None', '')
    
    return df_fixed

def safe_streamlit_dataframe(df, **kwargs):
    """
    Безопасное отображение DataFrame в Streamlit
    
    Args:
        df: DataFrame для отображения
        **kwargs: Дополнительные параметры для st.dataframe()
    """
    
    import streamlit as st
    
    if df is None or df.empty:
        st.info("📝 Нет данных для отображения")
        return
    
    try:
        # Пробуем исправить DataFrame
        df_fixed = fix_dataframe_for_streamlit(df)
        
        # Отображаем исправленный DataFrame
        st.dataframe(df_fixed, **kwargs)
        
    except Exception as e:
        # Если все еще ошибка, показываем как таблицу HTML
        st.warning(f"⚠️ Проблема отображения таблицы: {e}")
        st.write("📊 Отображение в альтернативном формате:")
        
        # Конвертируем в HTML таблицу
        html_table = df.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

def apply_dataframe_fix_to_warehouse_analysis():
    """
    Применяет исправления DataFrame к модулю анализа складов
    """
    
    try:
        import warehouse_analysis
        import streamlit as st
        
        # Сохраняем оригинальную функцию st.dataframe
        if not hasattr(st, '_original_dataframe'):
            st._original_dataframe = st.dataframe
        
        # Заменяем на безопасную версию
        st.dataframe = safe_streamlit_dataframe
        
        print("✅ Исправление отображения DataFrame применено")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения исправления DataFrame: {e}")
        return False

def fix_warehouse_analysis_dataframes():
    """
    Исправляет все DataFrame в функциях анализа складов
    """
    
    try:
        import warehouse_analysis
        
        # Находим и исправляем функцию display_enhanced_warehouse_results
        if hasattr(warehouse_analysis, 'display_enhanced_warehouse_results'):
            original_display = warehouse_analysis.display_enhanced_warehouse_results
            
            def fixed_display_enhanced_warehouse_results(analysis, store_ads_by_city):
                """
                Исправленная версия отображения результатов анализа складов
                """
                import streamlit as st
                
                st.subheader("📊 Результаты анализа по городам")
                
                # Группируем результаты по городам
                results_by_city = {}
                
                for item in analysis:
                    for warehouse_key, warehouse_data in item['warehouses'].items():
                        city = warehouse_data['city'] or 'общие'
                        
                        if city not in results_by_city:
                            results_by_city[city] = {
                                'critical': 0,
                                'warning': 0,
                                'good': 0,
                                'excess': 0,
                                'no_ads': 0,
                                'total_order': 0,
                                'warehouses': []
                            }
                        
                        status = warehouse_data['status']
                        results_by_city[city][status] += 1
                        results_by_city[city]['total_order'] += warehouse_data['order_quantity']
                        
                        if warehouse_data['short_name'] not in results_by_city[city]['warehouses']:
                            results_by_city[city]['warehouses'].append(warehouse_data['short_name'])
                
                # Показываем результаты по городам
                for city, data in results_by_city.items():
                    st.write(f"### {city.title()}")
                    st.write(f"*Склады: {', '.join(data['warehouses'])}*")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("🔴 Критичные", data['critical'])
                    with col2:
                        st.metric("🟡 Внимание", data['warning'])
                    with col3:
                        st.metric("🟢 Норма", data['good'])
                    with col4:
                        st.metric("🔵 Избыток", data['excess'])
                    with col5:
                        st.metric("📦 К заказу", f"{data['total_order']:.0f}")
                
                # Детальная таблица с исправлением
                st.subheader("📋 Детальные результаты")
                
                detailed_results = []
                for item in analysis:
                    for warehouse_key, warehouse_data in item['warehouses'].items():
                        if warehouse_data['current_stock'] > 0 or warehouse_data['order_quantity'] > 0:
                            
                            # ИСПРАВЛЕНИЕ: Безопасное форматирование месяцев запаса
                            months_stock = warehouse_data['months_of_stock']
                            if months_stock >= 99:
                                months_display = "999+"
                            else:
                                months_display = f"{months_stock:.1f}"
                            
                            detailed_results.append({
                                'Товар': item['номенклатура'][:50],
                                'Склад': warehouse_data['short_name'],
                                'Город': warehouse_data['city'] or 'общий',
                                'Остаток': int(warehouse_data['current_stock']),
                                'ADS': f"{warehouse_data['ads']:.4f}",
                                'MIN': int(warehouse_data['min_stock']),
                                'MAX': int(warehouse_data['max_stock']),
                                'Статус': warehouse_data['status'],
                                'К заказу': int(warehouse_data['order_quantity']),
                                'Месяцев запаса': months_display  # ИСПРАВЛЕННОЕ ПОЛЕ
                            })
                
                if detailed_results:
                    import pandas as pd
                    df_results = pd.DataFrame(detailed_results)
                    
                    # Фильтры для таблицы
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        city_filter = st.selectbox("Фильтр по городу:", ['Все'] + list(results_by_city.keys()))
                    with col2:
                        status_filter = st.selectbox("Фильтр по статусу:", ['Все', 'critical', 'warning', 'good', 'excess', 'no_ads'])
                    with col3:
                        warehouse_filter = st.selectbox("Фильтр по складу:", ['Все'] + df_results['Склад'].unique().tolist())
                    
                    # Применяем фильтры
                    filtered_df = df_results.copy()
                    
                    if city_filter != 'Все':
                        filtered_df = filtered_df[filtered_df['Город'] == city_filter]
                    
                    if status_filter != 'Все':
                        filtered_df = filtered_df[filtered_df['Статус'] == status_filter]
                        
                    if warehouse_filter != 'Все':
                        filtered_df = filtered_df[filtered_df['Склад'] == warehouse_filter]
                    
                    st.write(f"Показано записей: {len(filtered_df)} из {len(df_results)}")
                    
                    # ИСПРАВЛЕННОЕ ОТОБРАЖЕНИЕ DATAFRAME
                    safe_streamlit_dataframe(filtered_df, use_container_width=True)
                    
                    # Экспорт
                    if st.button("📊 Экспорт результатов в Excel"):
                        from io import BytesIO
                        import pandas as pd
                        
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Исправляем DataFrame перед экспортом
                            export_df = fix_dataframe_for_streamlit(df_results)
                            export_df.to_excel(writer, sheet_name='Анализ_складов', index=False)
                            
                            # Добавляем сводку по городам
                            summary_data = []
                            for city, data in results_by_city.items():
                                summary_data.append({
                                    'Город': city,
                                    'Склады': ', '.join(data['warehouses']),
                                    'Критичные': data['critical'],
                                    'Внимание': data['warning'],
                                    'Норма': data['good'],
                                    'Избыток': data['excess'],
                                    'К_заказу': data['total_order']
                                })
                            
                            summary_df = pd.DataFrame(summary_data)
                            summary_df.to_excel(writer, sheet_name='Сводка_по_городам', index=False)
                        
                        output.seek(0)
                        st.download_button(
                            label="💾 Скачать анализ складов",
                            data=output,
                            file_name=f"warehouse_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            
            # Заменяем функцию
            warehouse_analysis.display_enhanced_warehouse_results = fixed_display_enhanced_warehouse_results
            
        print("✅ Исправления DataFrame в анализе складов применены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка исправления функций анализа складов: {e}")
        return False

def apply_complete_dataframe_fix():
    """
    Применяет все исправления для DataFrame
    """
    
    print("🔧 Применяем исправления DataFrame...")
    
    success_count = 0
    
    # Исправление 1: Безопасное отображение DataFrame
    if apply_dataframe_fix_to_warehouse_analysis():
        success_count += 1
    
    # Исправление 2: Исправление функций анализа складов
    if fix_warehouse_analysis_dataframes():
        success_count += 1
    
    print(f"✅ Применено {success_count}/2 исправлений DataFrame")
    
    return success_count >= 1

# Функция для быстрого применения
def quick_fix_arrow_error():
    """
    Быстрое исправление ошибки Arrow в одну строку
    """
    
    try:
        import streamlit as st
        import pandas as pd
        
        # Переопределяем st.dataframe глобально
        original_dataframe = st.dataframe
        
        def safe_dataframe(data, **kwargs):
            if isinstance(data, pd.DataFrame):
                # Исправляем проблемные колонки
                data_fixed = data.copy()
                for col in data_fixed.columns:
                    if data_fixed[col].dtype == 'object':
                        data_fixed[col] = data_fixed[col].astype(str)
                        data_fixed[col] = data_fixed[col].replace('∞', '999+')
                        data_fixed[col] = data_fixed[col].replace('inf', '999+')
                        data_fixed[col] = data_fixed[col].replace('nan', '')
                
                return original_dataframe(data_fixed, **kwargs)
            else:
                return original_dataframe(data, **kwargs)
        
        st.dataframe = safe_dataframe
        
        print("✅ Быстрое исправление Arrow ошибки применено")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка быстрого исправления: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Модуль исправления ошибок сериализации DataFrame")
    print("📋 Использование:")
    print("   from fix_arrow_serialization import quick_fix_arrow_error")
    print("   quick_fix_arrow_error()")