# fix_file_reading.py
"""
🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ ЧТЕНИЯ ФАЙЛОВ ОСТАТКОВ
Восстанавливает работоспособность чтения файлов остатков
"""

import pandas as pd
import streamlit as st


def fix_warehouse_file_reading(system):
    """
    Быстро исправляет чтение файлов остатков
    """
    
    def safe_parse_remains_file(uploaded_file, debug_mode=False):
        """
        Безопасное чтение файла остатков с несколькими fallback методами
        """
        
        if debug_mode:
            st.write("🔍 **Отладка чтения файла:**")
        
        try:
            # Метод 1: Простое чтение Excel с автоопределением структуры
            if debug_mode:
                st.write("1️⃣ Пробуем простое чтение Excel...")
                
            df = pd.read_excel(uploaded_file, header=None)
            
            if debug_mode:
                st.write(f"📊 Прочитано строк: {len(df)}, колонок: {len(df.columns)}")
            
            # Ищем строку с "Номенклатура"
            nomenclature_row = None
            nomenclature_col = None
            
            for row_idx in range(min(15, len(df))):  # Проверяем первые 15 строк
                for col_idx in range(min(10, len(df.columns))):  # Первые 10 колонок
                    try:
                        cell_value = str(df.iloc[row_idx, col_idx]).lower().strip()
                        if 'номенклатура' in cell_value or 'наименование' in cell_value:
                            nomenclature_row = row_idx
                            nomenclature_col = col_idx
                            break
                    except:
                        continue
                if nomenclature_row is not None:
                    break
            
            if debug_mode:
                if nomenclature_row is not None:
                    st.write(f"✅ Номенклатура найдена: строка {nomenclature_row + 1}, колонка {nomenclature_col + 1}")
                else:
                    st.write("⚠️ Номенклатура не найдена, используем первую колонку")
            
            # Если не нашли номенклатуру, используем defaults
            if nomenclature_row is None:
                nomenclature_row = 0  # Начинаем с первой строки
                nomenclature_col = 0  # Первая колонка
            
            # Определяем строку начала данных
            data_start_row = nomenclature_row + 1
            
            # Собираем данные товаров
            remains_data = []
            processed_count = 0
            
            for row_idx in range(data_start_row, len(df)):
                try:
                    # Получаем номенклатуру
                    nomenclature = str(df.iloc[row_idx, nomenclature_col]).strip()
                    
                    # Пропускаем пустые строки и служебные
                    if (not nomenclature or 
                        nomenclature.lower() in ['nan', '', 'none', 'итого', 'всего'] or
                        len(nomenclature) < 2):
                        continue
                    
                    # Базовая запись товара
                    item_data = {
                        'номенклатура': nomenclature,
                        'итого_остаток': 0
                    }
                    
                    # Пытаемся найти остатки в других колонках
                    total_stock = 0
                    for col_idx in range(len(df.columns)):
                        if col_idx != nomenclature_col:  # Пропускаем колонку номенклатуры
                            try:
                                cell_value = df.iloc[row_idx, col_idx]
                                if pd.notna(cell_value):
                                    numeric_value = float(cell_value)
                                    if numeric_value > 0:
                                        total_stock += numeric_value
                                        # Добавляем как остаток склада
                                        item_data[f'склад_{col_idx}_остаток'] = numeric_value
                            except (ValueError, TypeError):
                                continue
                    
                    item_data['итого_остаток'] = total_stock
                    remains_data.append(item_data)
                    processed_count += 1
                    
                    # Ограничиваем количество для безопасности
                    if processed_count >= 10000:
                        break
                        
                except Exception as e:
                    if debug_mode:
                        st.write(f"⚠️ Ошибка обработки строки {row_idx}: {e}")
                    continue
            
            if debug_mode:
                st.write(f"✅ Обработано товаров: {processed_count}")
            
            if remains_data:
                result_df = pd.DataFrame(remains_data)
                return result_df
            else:
                if debug_mode:
                    st.write("❌ Не найдено товаров для обработки")
                return pd.DataFrame()
                
        except Exception as e:
            if debug_mode:
                st.write(f"❌ Критическая ошибка чтения: {e}")
            
            # Последний fallback - минимальное чтение
            try:
                if debug_mode:
                    st.write("🔄 Пробуем минимальное чтение...")
                
                df_simple = pd.read_excel(uploaded_file)
                if len(df_simple) > 0:
                    # Берем первую колонку как номенклатуру
                    first_col = df_simple.columns[0]
                    simple_data = []
                    
                    for _, row in df_simple.head(1000).iterrows():  # Максимум 1000 строк
                        item_name = str(row[first_col]).strip()
                        if item_name and item_name.lower() not in ['nan', '', 'none']:
                            simple_data.append({
                                'номенклатура': item_name,
                                'итого_остаток': 0
                            })
                    
                    if simple_data:
                        return pd.DataFrame(simple_data)
                
            except Exception as e2:
                if debug_mode:
                    st.write(f"❌ Минимальное чтение не удалось: {e2}")
            
            return pd.DataFrame()
    
    # Заменяем метод чтения в системе
    if hasattr(system, 'warehouse_analyzer'):
        system.warehouse_analyzer.parse_remains_file = lambda file_data: safe_parse_remains_file(file_data, False)
    
    # Добавляем безопасный метод напрямую к системе
    system.safe_parse_remains_file = safe_parse_remains_file
    
    st.success("✅ Исправление чтения файлов применено!")
    
    return True


def apply_emergency_fix():
    """
    Экстренное исправление для восстановления чтения файлов
    """
    
    st.header("🔧 Экстренное исправление чтения файлов")
    
    if 'inventory_system' not in st.session_state:
        st.error("❌ Система не инициализирована")
        return
    
    system = st.session_state.inventory_system
    
    if st.button("🔧 Применить экстренное исправление", type="primary"):
        with st.spinner("Применяем исправление..."):
            success = fix_warehouse_file_reading(system)
            
            if success:
                st.success("✅ Исправление применено! Попробуйте загрузить файл снова.")
                st.info("💡 Теперь можете вернуться к анализу складов")
            else:
                st.error("❌ Не удалось применить исправление")


def create_safe_warehouse_reader():
    """
    Создает безопасный ридер файлов складов
    """
    
    def read_warehouse_file_safe(uploaded_file, debug_mode=False):
        """
        Максимально безопасное чтение файла складов
        """
        
        try:
            # Читаем как pandas DataFrame
            df = pd.read_excel(uploaded_file)
            
            if df.empty:
                return pd.DataFrame()
            
            # Ищем колонку с номенклатурой
            nomenclature_col = None
            
            # Проверяем заголовки
            for col in df.columns:
                col_str = str(col).lower()
                if any(word in col_str for word in ['номенклатура', 'наименование', 'товар', 'артикул']):
                    nomenclature_col = col
                    break
            
            # Если не нашли по заголовку, берем первую колонку
            if nomenclature_col is None:
                nomenclature_col = df.columns[0]
            
            # Создаем результат
            result_data = []
            
            for _, row in df.iterrows():
                try:
                    item_name = str(row[nomenclature_col]).strip()
                    
                    if item_name and item_name.lower() not in ['nan', '', 'none', 'итого']:
                        result_data.append({
                            'номенклатура': item_name,
                            'итого_остаток': 0
                        })
                except:
                    continue
            
            return pd.DataFrame(result_data) if result_data else pd.DataFrame()
            
        except Exception as e:
            if debug_mode:
                st.error(f"Ошибка чтения: {e}")
            return pd.DataFrame()
    
    return read_warehouse_file_safe


if __name__ == "__main__":
    print("🔧 Исправление чтения файлов складов загружено")
    apply_emergency_fix()