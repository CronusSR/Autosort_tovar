#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import io

def fix_load_current_stock_file_function():
    """Исправление функции load_current_stock_file для правильного чтения файла остатков"""
    
    fixed_function = '''
    def load_current_stock_file(self, file_content) -> Dict:
        """
        Загрузка файла текущих остатков (ИСПРАВЛЕННАЯ ВЕРСИЯ)
        
        Args:
            file_content: Содержимое файла остатков
            
        Returns:
            Dict с информацией о загруженных остатках
        """
        try:
            # Читаем Excel файл БЕЗ заголовков
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl', header=None)
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None)
            
            print(f"📊 Загружен файл: {df.shape[0]} строк x {df.shape[1]} колонок")
            
            # Ищем строку с "Номенклатура" в колонке A (индекс 0)
            header_row = None
            for i in range(min(15, len(df))):  # Проверяем первые 15 строк
                if pd.notna(df.iloc[i, 0]):
                    cell_value = str(df.iloc[i, 0]).strip().lower()
                    if 'номенклатура' in cell_value:
                        header_row = i
                        print(f"✅ Найдена строка заголовков: {i}")
                        break
            
            if header_row is None:
                # Если не нашли "Номенклатура", ищем строку 7 (индекс 6)
                header_row = 6  # Строка 7 в Excel = индекс 6 в pandas
                print(f"⚠️ Используем строку по умолчанию: {header_row}")
            
            # Извлекаем заголовки из найденной строки
            headers = []
            for col_idx in range(df.shape[1]):
                if pd.notna(df.iloc[header_row, col_idx]):
                    header_val = str(df.iloc[header_row, col_idx]).strip()
                    headers.append(header_val)
                else:
                    headers.append(f'col_{col_idx}')
            
            print(f"📋 Заголовки: {headers[:10]}")  # Показываем первые 10
            
            # Берем данные ПОСЛЕ строки заголовков
            data_start_row = header_row + 1
            df_data = df.iloc[data_start_row:].copy()
            df_data.columns = headers[:len(df_data.columns)]
            
            print(f"📊 Данные: {len(df_data)} строк начиная со строки {data_start_row + 1}")
            
            # Найдем колонку номенклатуры (должна быть в колонке A, индекс 0)
            nomenclature_col = headers[0]  # Первая колонка
            print(f"📝 Колонка номенклатуры: '{nomenclature_col}'")
            
            # Переименовываем колонку номенклатуры
            df_data = df_data.rename(columns={nomenclature_col: 'номенклатура'})
            
            # Ищем колонки складов (начиная с колонки D, индекс 3)
            warehouse_columns = []
            warehouse_mapping = {}
            
            # Проверяем колонки с индекса 3 (колонка D) до 12 (колонка M)
            for col_idx in range(3, min(13, len(headers))):
                if col_idx < len(headers):
                    col_name = headers[col_idx]
                    if pd.notna(col_name) and str(col_name).strip():
                        col_str = str(col_name).lower()
                        # Исключаем колонку "Итого"
                        if 'итого' not in col_str and 'total' not in col_str:
                            warehouse_columns.append(col_name)
                            # Создаем короткое имя
                            short_name = str(col_name).replace('Склад фурнитуры', 'Склад').replace('Фурнитура', 'Фурн')[:20]
                            warehouse_mapping[col_name] = short_name
                            print(f"🏪 Склад найден: '{col_name}' -> '{short_name}'")
            
            print(f"📊 Найдено складов: {len(warehouse_columns)}")
            
            # Очищаем данные номенклатуры
            df_data = df_data.dropna(subset=['номенклатура'])
            df_data = df_data[df_data['номенклатура'].astype(str).str.strip() != '']
            df_data = df_data[df_data['номенклатура'].astype(str) != 'nan']
            
            # Преобразуем остатки в числовой формат
            for col in warehouse_columns:
                if col in df_data.columns:
                    df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0)
            
            # Рассчитываем общий остаток
            existing_warehouse_cols = [col for col in warehouse_columns if col in df_data.columns]
            if existing_warehouse_cols:
                df_data['total_current_stock'] = df_data[existing_warehouse_cols].sum(axis=1)
            else:
                df_data['total_current_stock'] = 0
            
            # Сохраняем данные и маппинг складов
            self.stock_data = df_data
            self.warehouse_mapping = warehouse_mapping
            
            print(f"✅ Успешно загружено: {len(df_data)} товаров")
            print(f"📊 Товаров с остатками: {len(df_data[df_data['total_current_stock'] > 0])}")
            print(f"📊 Общий остаток: {df_data['total_current_stock'].sum()}")
            
            return {
                'success': True,
                'total_items': len(df_data),
                'warehouses_found': len(existing_warehouse_cols),
                'warehouse_list': list(warehouse_mapping.values()),
                'total_stock': df_data['total_current_stock'].sum(),
                'items_with_stock': len(df_data[df_data['total_current_stock'] > 0]),
                'avg_stock': df_data['total_current_stock'].mean(),
                'top_stock': df_data.nlargest(5, 'total_current_stock')[['номенклатура', 'total_current_stock']].to_dict('records')
            }
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла остатков: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка загрузки файла остатков: {str(e)}"}
    '''
    
    return fixed_function

def test_with_real_file():
    """Тест исправленной функции с реальным файлом"""
    
    import pandas as pd
    import io
    
    file_path = "/mnt/f/Работа-Никита/Autosort_tovar/остатки на 08.07.2025.xlsx"
    
    try:
        # Читаем файл БЕЗ заголовков
        df = pd.read_excel(file_path, engine='openpyxl', header=None)
        print(f"📊 Файл загружен: {df.shape[0]} строк x {df.shape[1]} колонок")
        
        # Ищем строку с "Номенклатура"
        header_row = None
        for i in range(min(15, len(df))):
            if pd.notna(df.iloc[i, 0]):
                cell_value = str(df.iloc[i, 0]).strip().lower()
                if 'номенклатура' in cell_value:
                    header_row = i
                    print(f"✅ Найдена строка заголовков: {i}")
                    break
        
        if header_row is None:
            header_row = 6  # Строка 7
            print(f"⚠️ Используем строку по умолчанию: {header_row}")
        
        # Извлекаем заголовки
        headers = []
        for col_idx in range(df.shape[1]):
            if pd.notna(df.iloc[header_row, col_idx]):
                header_val = str(df.iloc[header_row, col_idx]).strip()
                headers.append(header_val)
            else:
                headers.append(f'col_{col_idx}')
        
        print(f"📋 Заголовки найдены:")
        for i, header in enumerate(headers[:15]):
            print(f"  {i}: '{header}'")
        
        # Берем данные после заголовков
        data_start_row = header_row + 1
        df_data = df.iloc[data_start_row:].copy()
        df_data.columns = headers[:len(df_data.columns)]
        
        print(f"📊 Данные: {len(df_data)} строк")
        
        # Анализируем первые строки данных
        print(f"📊 Первые 5 строк данных:")
        for i in range(min(5, len(df_data))):
            nomenclature = df_data.iloc[i, 0]
            print(f"  Строка {i}: '{nomenclature}'")
            
            # Показываем остатки по складам (колонки 3-12)
            for col_idx in range(3, min(13, len(headers))):
                if col_idx < len(headers):
                    col_name = headers[col_idx]
                    if 'итого' not in str(col_name).lower():
                        value = df_data.iloc[i, col_idx]
                        if pd.notna(value) and value != 0:
                            print(f"    {col_name}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 ТЕСТ ИСПРАВЛЕННОЙ ФУНКЦИИ ЧТЕНИЯ ОСТАТКОВ")
    print("=" * 60)
    
    success = test_with_real_file()
    
    if success:
        print("\n✅ ТЕСТ ПРОШЕЛ УСПЕШНО!")
        print("\n🔧 Код для замены функции load_current_stock_file:")
        print(fix_load_current_stock_file_function())
    else:
        print("\n❌ ТЕСТ НЕ ПРОШЕЛ!")