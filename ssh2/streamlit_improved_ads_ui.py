# streamlit_improved_ads_ui.py
# Улучшенный UI для исправления ADS с автоматическим поиском категорий

import streamlit as st
import pandas as pd
import plotly.express as px

def show_improved_category_ads_fix_ui(system):
    """
    Улучшенный UI для работы с исправлением ADS по категориям
    """
    
    st.subheader("🔧 Умное исправление ADS = 0")
    
    # Проверяем готовность данных
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.error("❌ Сначала рассчитайте ADS")
        return
    
    ads_data = system.calculated_ads
    zero_ads_count = len(ads_data[ads_data['ads'] == 0])
    total_count = len(ads_data)
    
    # Показываем статус
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего товаров", total_count)
    
    with col2:
        if zero_ads_count > 0:
            st.metric("С ADS = 0", zero_ads_count, delta=f"-{(zero_ads_count/total_count*100):.1f}%")
        else:
            st.metric("С ADS = 0", zero_ads_count, delta="✅ Отлично!")
    
    with col3:
        # Проверяем источники категорий
        sources_available = []
        if hasattr(system, 'abc_data') and system.abc_data is not None:
            sources_available.append("ABC анализ")
        if hasattr(system, 'source_data') and system.source_data is not None:
            sources_available.append("Исходники")
        if not sources_available:
            sources_available.append("Авто-категории")
        
        st.metric("Источник категорий", len(sources_available), delta=", ".join(sources_available))
    
    if zero_ads_count == 0:
        st.success("✅ Все товары имеют положительный ADS!")
        
        # Показываем информацию о последнем исправлении, если было
        if hasattr(system, '_ads_fix_applied') and system._ads_fix_applied:
            with st.expander("ℹ️ Информация о последнем исправлении"):
                if hasattr(system, '_ads_fix_stats'):
                    stats = system._ads_fix_stats
                    st.info(f"""
                    **Последнее исправление:**
                    - Исправлено товаров: {stats['fixed_count']}
                    - Использовано категорий: {stats['categories_used']}
                    - Источник данных: {getattr(system, '_ads_fix_source', 'Неизвестно')}
                    """)
        return
    
    # Предварительный просмотр категорий
    st.subheader("🔍 Предварительный просмотр")
    
    if st.button("🔍 Проверить доступные категории", type="secondary"):
        with st.spinner("Анализируем источники категорий..."):
            try:
                from ads_category_fix_improved import get_categories_preview
                
                categories = get_categories_preview(system)
                
                if categories:
                    st.success(f"✅ Найдено {len(categories)} категорий")
                    
                    # Показываем распределение товаров по категориям
                    category_counts = {cat: len(items) for cat, items in categories.items()}
                    
                    df_preview = pd.DataFrame([
                        {"Категория": cat, "Количество товаров": count}
                        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                    ])
                    
                    # График распределения
                    fig = px.bar(
                        df_preview.head(10), 
                        x='Количество товаров', 
                        y='Категория',
                        orientation='h',
                        title='Топ-10 категорий по количеству товаров'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Детальная таблица
                    with st.expander("📋 Все категории"):
                        st.dataframe(df_preview, use_container_width=True)
                else:
                    st.error("❌ Категории не найдены")
                    
            except ImportError:
                st.error("❌ Модуль ads_category_fix_improved не найден")
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")
    
    # Основная кнопка исправления
    st.subheader("🚀 Применение исправления")
    
    # Показываем что будет исправлено
    if st.checkbox("📋 Показать товары с ADS = 0"):
        zero_ads_items = ads_data[ads_data['ads'] == 0][['номенклатура']].head(20)
        st.dataframe(zero_ads_items, use_container_width=True)
        
        if zero_ads_count > 20:
            st.info(f"Показаны первые 20 из {zero_ads_count} товаров")
    
    # Кнопка применения исправления
    if st.button("🔧 Заменить ADS = 0 на средний по категории", type="primary", use_container_width=True):
        
        with st.spinner("Применяем умное исправление..."):
            
            try:
                from ads_category_fix_improved import apply_category_average_ads_fix_improved
                
                success = apply_category_average_ads_fix_improved(system)
                
                if success:
                    st.success("✅ Исправление применено успешно!")
                    
                    # Показываем результаты
                    if hasattr(system, '_ads_fix_stats'):
                        stats = system._ads_fix_stats
                        source = getattr(system, '_ads_fix_source', 'Неизвестно')
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Исправлено", stats['fixed_count'])
                        with col2:
                            st.metric("Использовано категорий", stats['categories_used'])
                        with col3:
                            st.metric("Источник", source)
                    
                    st.rerun()  # Обновляем интерфейс
                else:
                    st.error("❌ Ошибка при применении исправления")
                    
            except ImportError:
                st.error("❌ Модуль ads_category_fix_improved не найден")
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")


def show_improved_category_statistics_ui(system):
    """
    Улучшенная статистика по категориям с визуализацией
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("❌ Сначала рассчитайте ADS")
        return
    
    ads_data = system.calculated_ads
    
    # Проверяем есть ли колонка категории
    if 'category' not in ads_data.columns:
        st.info("ℹ️ Категории не добавлены. Примените исправление ADS сначала")
        return
    
    st.subheader("📊 Умная статистика по категориям")
    
    # Показываем источник данных
    if hasattr(system, '_ads_fix_source'):
        st.info(f"📋 Источник категорий: {system._ads_fix_source}")
    
    # Группируем по категориям
    category_stats = ads_data.groupby('category').agg({
        'ads': ['count', 'sum', 'mean', 'min', 'max'],
        'номенклатура': 'count'
    }).round(4)
    
    category_stats.columns = ['Количество', 'Общий ADS', 'Средний ADS', 'Мин ADS', 'Макс ADS', 'Товаров']
    
    # Добавляем долю в общем ADS
    total_ads = ads_data['ads'].sum()
    category_stats['Доля %'] = (category_stats['Общий ADS'] / total_ads * 100).round(2)
    
    category_stats = category_stats.sort_values('Общий ADS', ascending=False).reset_index()
    
    # Визуализации
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 ТОП по общему ADS")
        top_total = category_stats.head(8)
        
        fig_total = px.bar(
            top_total, 
            y='category', 
            x='Общий ADS',
            orientation='h',
            title='Топ-8 категорий по общему ADS',
            color='Доля %',
            color_continuous_scale='viridis'
        )
        fig_total.update_layout(height=400)
        st.plotly_chart(fig_total, use_container_width=True)
    
    with col2:
        st.subheader("📈 ТОП по среднему ADS")
        top_avg = category_stats.sort_values('Средний ADS', ascending=False).head(8)
        
        fig_avg = px.bar(
            top_avg, 
            y='category', 
            x='Средний ADS',
            orientation='h',
            title='Топ-8 категорий по среднему ADS',
            color='Средний ADS',
            color_continuous_scale='plasma'
        )
        fig_avg.update_layout(height=400)
        st.plotly_chart(fig_avg, use_container_width=True)
    
    # Круговая диаграмма долей
    st.subheader("🥧 Распределение ADS по категориям")
    
    # Берем топ-10 для читаемости
    top_10 = category_stats.head(10)
    other_sum = category_stats.iloc[10:]['Общий ADS'].sum() if len(category_stats) > 10 else 0
    
    if other_sum > 0:
        pie_data = top_10.copy()
        pie_data.loc[len(pie_data)] = ['Остальные', 0, other_sum, 0, 0, 0, 0, (other_sum/total_ads*100)]
    else:
        pie_data = top_10
    
    fig_pie = px.pie(
        pie_data, 
        values='Общий ADS', 
        names='category',
        title='Доля категорий в общем ADS',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Детальная таблица
    with st.expander("📋 Детальная статистика по всем категориям"):
        st.dataframe(category_stats, use_container_width=True)
    
    # Общая статистика
    st.subheader("📊 Сводная статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего категорий", len(category_stats))
    
    with col2:
        st.metric("Общий ADS", f"{total_ads:.2f}")
    
    with col3:
        avg_ads = ads_data['ads'].mean()
        st.metric("Средний ADS", f"{avg_ads:.4f}")
    
    with col4:
        zero_ads = len(ads_data[ads_data['ads'] == 0])
        st.metric("Товаров с ADS = 0", zero_ads)
    
    # Анализ качества категоризации
    if hasattr(system, '_ads_fix_stats'):
        st.subheader("🎯 Качество исправления")
        stats = system._ads_fix_stats
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Исправлено", stats['fixed_count'])
        with col2:
            st.metric("Не исправлено", stats['not_fixed_count'])
        with col3:
            success_rate = (stats['fixed_count'] / (stats['fixed_count'] + stats['not_fixed_count']) * 100) if (stats['fixed_count'] + stats['not_fixed_count']) > 0 else 0
            st.metric("Успешность", f"{success_rate:.1f}%")


def show_improved_revert_ui(system):
    """
    Улучшенный UI для отмены исправления
    """
    
    if not hasattr(system, 'original_calculated_ads'):
        st.info("ℹ️ Нет резервной копии для отмены")
        return
    
    st.subheader("🔄 Отмена исправления")
    
    # Показываем информацию о текущем исправлении
    if hasattr(system, '_ads_fix_applied') and system._ads_fix_applied:
        if hasattr(system, '_ads_fix_stats'):
            stats = system._ads_fix_stats
            source = getattr(system, '_ads_fix_source', 'Неизвестно')
            
            st.warning(f"""
            ⚠️ **Текущее исправление будет отменено:**
            - Исправлено товаров: {stats['fixed_count']}
            - Источник категорий: {source}
            - Это действие восстановит оригинальные значения ADS (включая нулевые)
            """)
        else:
            st.warning("⚠️ Это действие восстановит оригинальные значения ADS (включая нулевые)")
    
    if st.button("🔄 Отменить исправление ADS", type="secondary"):
        
        try:
            from ads_category_fix_improved import revert_category_ads_fix
            
            success = revert_category_ads_fix(system)
            
            if success:
                st.success("✅ Оригинальные значения ADS восстановлены")
                st.rerun()
            else:
                st.error("❌ Ошибка при отмене исправления")
                
        except ImportError:
            st.error("❌ Модуль ads_category_fix_improved не найден")
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")


def integrate_improved_ads_fix_to_streamlit():
    """
    Код для интеграции в основной streamlit файл
    
    ДОБАВЬТЕ В ads_calculation_page_updated ПОСЛЕ st.success("✅ ADS рассчитан!"):
    """
    
    return """
    # === УЛУЧШЕННОЕ ИСПРАВЛЕНИЕ ADS ПО КАТЕГОРИЯМ ===
    try:
        from streamlit_improved_ads_ui import (
            show_improved_category_ads_fix_ui,
            show_improved_category_statistics_ui,
            show_improved_revert_ui
        )
        
        st.markdown("---")
        st.subheader("🧠 Умная работа с категориями")
        
        # Вкладки для организации интерфейса
        tab1, tab2, tab3 = st.tabs([
            "🔧 Умное исправление ADS = 0", 
            "📊 Умная статистика категорий", 
            "🔄 Отмена изменений"
        ])
        
        with tab1:
            show_improved_category_ads_fix_ui(system)
        
        with tab2:
            show_improved_category_statistics_ui(system)
        
        with tab3:
            show_improved_revert_ui(system)
            
    except ImportError:
        st.info("ℹ️ Для умной работы с категориями добавьте файлы ads_category_fix_improved.py и streamlit_improved_ads_ui.py")
    # === КОНЕЦ УЛУЧШЕННОГО ИСПРАВЛЕНИЯ ===
    """


def quick_streamlit_integration(system):
    """
    Быстрая интеграция - минимальный код для добавления в streamlit
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        return
    
    zero_ads_count = len(system.calculated_ads[system.calculated_ads['ads'] == 0])
    
    if zero_ads_count > 0:
        st.warning(f"⚠️ Найдено {zero_ads_count} товаров с ADS = 0")
        st.info("💡 Система может автоматически заменить их на средний ADS по категории")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 Умное исправление ADS", type="primary"):
                try:
                    from ads_category_fix_improved import quick_ads_category_fix
                    
                    with st.spinner("Применяем исправление..."):
                        success, message = quick_ads_category_fix(system)
                        
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        
                except ImportError:
                    st.error("❌ Файл ads_category_fix_improved.py не найден")
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")
        
        with col2:
            if st.button("🔍 Предварительный просмотр"):
                try:
                    from ads_category_fix_improved import get_categories_preview
                    
                    categories = get_categories_preview(system)
                    if categories:
                        st.success(f"✅ Найдено {len(categories)} категорий")
                    else:
                        st.warning("⚠️ Категории не найдены")
                        
                except Exception as e:
                    st.error(f"❌ Ошибка: {str(e)}")


# Пример использования
if __name__ == "__main__":
    st.write("## Инструкция по интеграции улучшенного исправления ADS")
    
    st.code(integrate_improved_ads_fix_to_streamlit(), language="python")
    
    st.write("### Быстрая интеграция (минимальный код):")
    st.write("Добавьте в ads_calculation_page_updated после st.success('✅ ADS рассчитан!'):")
    
    st.code("""
    # Быстрое умное исправление ADS
    from streamlit_improved_ads_ui import quick_streamlit_integration
    quick_streamlit_integration(system)
    """, language="python")