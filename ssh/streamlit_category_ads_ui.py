# streamlit_category_ads_ui.py
# UI компоненты для работы с исправлением ADS по категориям

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_category_ads_fix_ui(system):
    """
    Показывает UI для работы с исправлением ADS по категориям
    """
    
    st.subheader("🔧 Исправление ADS = 0")
    
    # Проверяем готовность данных
    has_ads = hasattr(system, 'calculated_ads') and system.calculated_ads is not None
    has_source = hasattr(system, 'source_data') and system.source_data is not None
    
    if not has_ads:
        st.error("❌ Сначала рассчитайте ADS")
        return
        
    if not has_source:
        st.error("❌ Сначала загрузите файл исходников с категориями")
        return
    
    # Показываем текущую статистику
    ads_data = system.calculated_ads
    zero_ads_count = len(ads_data[ads_data['ads'] == 0])
    total_count = len(ads_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего товаров", total_count)
    
    with col2:
        st.metric("С ADS = 0", zero_ads_count)
    
    with col3:
        st.metric("% с нулевым ADS", f"{(zero_ads_count/total_count*100):.1f}%")
    
    if zero_ads_count == 0:
        st.success("✅ Все товары имеют положительный ADS")
        return
    
    # Кнопка применения исправления
    if st.button("🔧 Заменить ADS = 0 на средний по категории", type="primary"):
        
        with st.spinner("Применяем исправление..."):
            
            # Импортируем и применяем исправление
            try:
                from ads_category_fix import apply_category_average_ads_fix
                
                success = apply_category_average_ads_fix(system)
                
                if success:
                    st.success("✅ Исправление применено успешно!")
                    st.rerun()  # Обновляем интерфейс
                else:
                    st.error("❌ Ошибка при применении исправления")
                    
            except ImportError:
                st.error("❌ Модуль ads_category_fix не найден")
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")
    
    # Показываем превью товаров с ADS = 0
    if zero_ads_count > 0:
        with st.expander(f"📋 Товары с ADS = 0 ({zero_ads_count} шт.)"):
            zero_ads_items = ads_data[ads_data['ads'] == 0][['номенклатура']].head(20)
            st.dataframe(zero_ads_items, use_container_width=True)
            
            if zero_ads_count > 20:
                st.info(f"Показаны первые 20 из {zero_ads_count} товаров")


def show_category_ads_statistics_ui(system):
    """
    Показывает UI со статистикой по категориям
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        st.warning("❌ Сначала рассчитайте ADS")
        return
    
    ads_data = system.calculated_ads
    
    # Проверяем есть ли колонка категории
    if 'category' not in ads_data.columns:
        st.info("ℹ️ Категории не добавлены. Примените исправление ADS сначала")
        return
    
    st.subheader("📊 Статистика по категориям")
    
    # Группируем по категориям
    category_stats = ads_data.groupby('category').agg({
        'ads': ['count', 'sum', 'mean', 'min', 'max'],
        'номенклатура': 'count'
    }).round(4)
    
    category_stats.columns = ['Количество', 'Общий ADS', 'Средний ADS', 'Мин ADS', 'Макс ADS', 'Товаров']
    category_stats = category_stats.sort_values('Общий ADS', ascending=False).reset_index()
    
    # Показываем топ категории
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 ТОП по общему ADS")
        top_total = category_stats.head(10)
        
        fig_total = px.bar(
            top_total, 
            y='category', 
            x='Общий ADS',
            orientation='h',
            title='Топ-10 категорий по общему ADS'
        )
        fig_total.update_layout(height=400)
        st.plotly_chart(fig_total, use_container_width=True)
    
    with col2:
        st.subheader("📈 ТОП по среднему ADS")
        top_avg = category_stats.sort_values('Средний ADS', ascending=False).head(10)
        
        fig_avg = px.bar(
            top_avg, 
            y='category', 
            x='Средний ADS',
            orientation='h',
            title='Топ-10 категорий по среднему ADS',
            color='Средний ADS',
            color_continuous_scale='viridis'
        )
        fig_avg.update_layout(height=400)
        st.plotly_chart(fig_avg, use_container_width=True)
    
    # Детальная таблица
    with st.expander("📋 Детальная статистика по всем категориям"):
        st.dataframe(category_stats, use_container_width=True)
    
    # Общая статистика
    total_categories = len(category_stats)
    total_ads = ads_data['ads'].sum()
    avg_ads = ads_data['ads'].mean()
    
    st.subheader("📊 Общая статистика")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего категорий", total_categories)
    
    with col2:
        st.metric("Общий ADS", f"{total_ads:.2f}")
    
    with col3:
        st.metric("Средний ADS", f"{avg_ads:.4f}")


def show_revert_ads_fix_ui(system):
    """
    UI для отмены исправления ADS
    """
    
    if not hasattr(system, 'original_calculated_ads'):
        st.info("ℹ️ Нет резервной копии для отмены")
        return
    
    st.subheader("🔄 Отмена исправления")
    
    st.warning("⚠️ Это действие восстановит оригинальные значения ADS (включая нулевые)")
    
    if st.button("🔄 Отменить исправление ADS", type="secondary"):
        
        try:
            from ads_category_fix import revert_category_ads_fix
            
            success = revert_category_ads_fix(system)
            
            if success:
                st.success("✅ Оригинальные значения ADS восстановлены")
                st.rerun()
            else:
                st.error("❌ Ошибка при отмене исправления")
                
        except ImportError:
            st.error("❌ Модуль ads_category_fix не найден")
        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")


def integrate_category_ads_fix_to_streamlit():
    """
    Интегрирует исправление ADS в основной streamlit интерфейс
    
    ИНСТРУКЦИЯ:
    Добавьте этот код в ваш основной streamlit файл в раздел ADS:
    
    # В разделе где показывается ADS статистика, добавьте:
    
    if st.session_state.analysis_system.calculated_ads is not None:
        
        # Существующий код показа ADS...
        
        # НОВОЕ: Добавляем исправление ADS
        st.markdown("---")
        
        # Показываем UI исправления
        show_category_ads_fix_ui(st.session_state.analysis_system)
        
        # Показываем статистику по категориям
        show_category_ads_statistics_ui(st.session_state.analysis_system)
        
        # Показываем возможность отмены
        show_revert_ads_fix_ui(st.session_state.analysis_system)
    """
    
    return """
    # Добавьте в ваш streamlit файл в раздел ADS:
    
    # После существующего кода показа ADS добавьте:
    st.markdown("---")
    
    # Исправление ADS = 0
    show_category_ads_fix_ui(st.session_state.analysis_system)
    
    # Статистика по категориям  
    show_category_ads_statistics_ui(st.session_state.analysis_system)
    
    # Отмена исправления
    show_revert_ads_fix_ui(st.session_state.analysis_system)
    """


# Пример использования в основном streamlit приложении
def example_usage_in_streamlit():
    """
    Пример как добавить в основной streamlit файл
    """
    
    st.write("""
    ## Инструкция по интеграции:
    
    ### 1. Сохраните код в файлы:
    - `ads_category_fix.py` - основная логика
    - `streamlit_category_ads_ui.py` - UI компоненты
    
    ### 2. В вашем основном streamlit файле:
    
    ```python
    # Импорты в начале файла
    from streamlit_category_ads_ui import (
        show_category_ads_fix_ui,
        show_category_ads_statistics_ui, 
        show_revert_ads_fix_ui
    )
    
    # В разделе где показывается ADS, после существующего кода добавьте:
    
    if st.session_state.analysis_system.calculated_ads is not None:
        
        # Ваш существующий код показа ADS...
        
        # НОВОЕ: Исправление ADS
        st.markdown("---")
        st.subheader("🔧 Работа с категориями")
        
        show_category_ads_fix_ui(st.session_state.analysis_system)
        show_category_ads_statistics_ui(st.session_state.analysis_system)
        show_revert_ads_fix_ui(st.session_state.analysis_system)
    ```
    
    ### 3. Использование:
    1. Загрузите файл исходников с категориями
    2. Рассчитайте ADS как обычно
    3. Нажмите кнопку "Заменить ADS = 0 на средний по категории"
    4. Проверьте статистику по категориям
    5. При необходимости отмените изменения
    """)


if __name__ == "__main__":
    example_usage_in_streamlit()