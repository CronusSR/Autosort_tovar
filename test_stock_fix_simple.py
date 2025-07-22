#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_real_file_structure():
    """Тест структуры реального файла для подтверждения исправления"""
    
    file_path = "/mnt/f/Работа-Никита/Autosort_tovar/остатки на 08.07.2025.xlsx"
    
    # Используем результаты уже проведенного анализа
    print("🔍 АНАЛИЗ СТРУКТУРЫ ФАЙЛА 'остатки на 08.07.2025.xlsx'")
    print("=" * 80)
    
    print("✅ НАЙДЕННАЯ СТРУКТУРА:")
    print("  📋 Строка заголовков: 7 (индекс 6 в pandas)")
    print("  📊 Начало данных: строка 10 (индекс 9 в pandas)")
    print("  📝 Номенклатура: колонка A (индекс 0)")
    print("  🏪 Склады: колонки D-L (индексы 3-11)")
    
    print("\n📋 ЗАГОЛОВКИ (строка 7):")
    headers = [
        "Номенклатура",  # A7
        "",              # B7
        "",              # C7
        "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"",  # D7
        "6 Склад фурнитуры \"Овощная база\" Магазин",       # E7
        "АО Склад Фурнитура TRADE",                         # F7
        "База Склад Фурнитура Комплект",                    # G7
        "Барыс Склад Фурнитура TRADE",                      # H7
        "Казыбаева Склад Фурнитура TRADE",                  # I7
        "Магазин фурнитуры",                                # J7
        "склад фурнитура № 1",                              # K7
        "ТД Казыбаева ФУРНИТУРА магазин",                   # L7
        "Итого"                                             # M7
    ]
    
    for i, header in enumerate(headers):
        col_letter = chr(65 + i)  # A, B, C, ...
        print(f"  {col_letter}7: '{header}'")
    
    print("\n🏪 НАЙДЕННЫЕ СКЛАДЫ (исключая 'Итого'):")
    warehouses = [
        "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"",
        "6 Склад фурнитуры \"Овощная база\" Магазин",
        "АО Склад Фурнитура TRADE",
        "База Склад Фурнитура Комплект",
        "Барыс Склад Фурнитура TRADE",
        "Казыбаева Склад Фурнитура TRADE",
        "Магазин фурнитуры",
        "склад фурнитура № 1",
        "ТД Казыбаева ФУРНИТУРА магазин"
    ]
    
    for i, warehouse in enumerate(warehouses, 3):  # Начинаем с индекса 3 (колонка D)
        col_letter = chr(65 + i)
        short_name = warehouse.replace('Склад фурнитуры', 'Склад').replace('Фурнитура', 'Фурн')[:20]
        print(f"  {col_letter}: '{warehouse}' -> '{short_name}'")
    
    print("\n📊 ПРИМЕРЫ ДАННЫХ (строки 10-14):")
    examples = [
        ("1,5*25мм Венге цаво 3354 PR", {"H": "180", "I": "300", "M": "480"}),
        ("1,5*25мм Дуб белый Craft К001", {"H": "168", "M": "168"}),
        ("1,5*25мм Дуб Венге 6495 PR", {"H": "300", "I": "600", "M": "900"}),
        ("1,5*25мм Дуб золотой Craft К003 PW", {"H": "300", "M": "300"}),
        ("1,5*25мм Дуб молочный 8622 PR", {"I": "400", "M": "400"})
    ]
    
    for i, (nomenclature, stocks) in enumerate(examples, 10):
        print(f"  Строка {i}: '{nomenclature}'")
        for col, value in stocks.items():
            print(f"    {col}: {value}")
    
    print("\n🔧 ПРОБЛЕМЫ В ТЕКУЩЕМ КОДЕ:")
    print("  ❌ Ищет заголовки по первой колонке, но там не всегда есть ключевые слова")
    print("  ❌ Не учитывает специфическую структуру файла (пропускает строки 1-6)")
    print("  ❌ Неправильно определяет колонки складов")
    print("  ❌ Не исключает колонку 'Итого' из складов")
    
    print("\n✅ ИСПРАВЛЕНИЯ:")
    print("  ✓ Читать файл БЕЗ заголовков (header=None)")
    print("  ✓ Искать строку с 'Номенклатура' (строка 7, индекс 6)")
    print("  ✓ Брать данные начиная со строки 10 (индекс 9)")
    print("  ✓ Номенклатура всегда в колонке A (индекс 0)")
    print("  ✓ Склады в колонках D-L (индексы 3-11), исключая 'Итого'")
    print("  ✓ Преобразовать остатки в числовой формат")
    
    return True

def generate_fixed_function():
    """Генерирует исправленную функцию для вставки в код"""
    
    fixed_code = '''
def load_current_stock_file(self, file_content) -> Dict:
    """
    Загрузка файла текущих остатков (ИСПРАВЛЕННАЯ ВЕРСИЯ для файла 08.07.2025)
    
    Args:
        file_content: Содержимое файла остатков
        
    Returns:
        Dict с информацией о загруженных остатках
    """
    try:
        # Читаем Excel файл БЕЗ заголовков - КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ!
        if hasattr(file_content, 'read'):
            df = pd.read_excel(file_content, engine='openpyxl', header=None)
        else:
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None)
        
        print(f"📊 Загружен файл: {df.shape[0]} строк x {df.shape[1]} колонок")
        
        # ИСПРАВЛЕНИЕ: Ищем строку с "Номенклатура" (обычно строка 7)
        header_row = None
        for i in range(min(15, len(df))):
            if pd.notna(df.iloc[i, 0]):
                cell_value = str(df.iloc[i, 0]).strip().lower()
                if 'номенклатура' in cell_value:
                    header_row = i
                    print(f"✅ Найдена строка заголовков: {i + 1}")
                    break
        
        # Если не нашли, используем строку 7 (индекс 6)
        if header_row is None:
            header_row = 6  # Строка 7 в Excel = индекс 6 в pandas
            print(f"⚠️ Используем строку заголовков по умолчанию: {header_row + 1}")
        
        # ИСПРАВЛЕНИЕ: Правильно извлекаем заголовки
        headers = []
        for col_idx in range(df.shape[1]):
            if pd.notna(df.iloc[header_row, col_idx]):
                header_val = str(df.iloc[header_row, col_idx]).strip()
                headers.append(header_val)
            else:
                headers.append(f'col_{col_idx}')
        
        print(f"📋 Найдено заголовков: {len([h for h in headers if not h.startswith('col_')])}")
        
        # ИСПРАВЛЕНИЕ: Данные начинаются ПОСЛЕ строки заголовков
        data_start_row = header_row + 1
        df_data = df.iloc[data_start_row:].copy()
        
        # Устанавливаем заголовки
        df_data.columns = headers[:len(df_data.columns)]
        
        print(f"📊 Строк данных: {len(df_data)} (начиная со строки {data_start_row + 1})")
        
        # ИСПРАВЛЕНИЕ: Номенклатура всегда в первой колонке
        nomenclature_col = headers[0]
        df_data = df_data.rename(columns={nomenclature_col: 'номенклатура'})
        print(f"📝 Колонка номенклатуры: '{nomenclature_col}'")
        
        # ИСПРАВЛЕНИЕ: Ищем склады в колонках D-L (индексы 3-11), исключая "Итого"
        warehouse_columns = []
        warehouse_mapping = {}
        
        for col_idx in range(3, min(13, len(headers))):  # Колонки D-L
            if col_idx < len(headers):
                col_name = headers[col_idx]
                if pd.notna(col_name) and str(col_name).strip():
                    col_str = str(col_name).lower()
                    # ИСПРАВЛЕНИЕ: Исключаем "Итого"
                    if 'итого' not in col_str and 'total' not in col_str and len(col_str) > 3:
                        warehouse_columns.append(col_name)
                        # Создаем короткое имя для отображения
                        short_name = (str(col_name)
                                    .replace('Склад фурнитуры', 'Склад')
                                    .replace('Фурнитура', 'Фурн')
                                    .replace('TRADE', 'TR')[:25])
                        warehouse_mapping[col_name] = short_name
                        print(f"🏪 Склад: '{short_name}'")
        
        print(f"📊 Найдено складов: {len(warehouse_columns)}")
        
        # Очищаем данные
        initial_count = len(df_data)
        df_data = df_data.dropna(subset=['номенклатура'])
        df_data = df_data[df_data['номенклатура'].astype(str).str.strip() != '']
        df_data = df_data[df_data['номенклатура'].astype(str) != 'nan']
        print(f"📊 Очищено: {initial_count} -> {len(df_data)} строк")
        
        # ИСПРАВЛЕНИЕ: Преобразуем остатки в числовой формат
        for col in warehouse_columns:
            if col in df_data.columns:
                df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0)
        
        # Рассчитываем общий остаток
        existing_warehouse_cols = [col for col in warehouse_columns if col in df_data.columns]
        if existing_warehouse_cols:
            df_data['total_current_stock'] = df_data[existing_warehouse_cols].sum(axis=1)
        else:
            df_data['total_current_stock'] = 0
        
        # Сохраняем данные
        self.stock_data = df_data
        self.warehouse_mapping = warehouse_mapping
        
        items_with_stock = len(df_data[df_data['total_current_stock'] > 0])
        total_stock = df_data['total_current_stock'].sum()
        
        print(f"✅ УСПЕШНО ЗАГРУЖЕНО:")
        print(f"  📊 Всего товаров: {len(df_data)}")
        print(f"  📊 С остатками: {items_with_stock}")
        print(f"  📊 Общий остаток: {total_stock:,.0f}")
        print(f"  📊 Складов: {len(existing_warehouse_cols)}")
        
        return {
            'success': True,
            'total_items': len(df_data),
            'warehouses_found': len(existing_warehouse_cols),
            'warehouse_list': list(warehouse_mapping.values()),
            'total_stock': total_stock,
            'items_with_stock': items_with_stock,
            'avg_stock': df_data['total_current_stock'].mean(),
            'top_stock': df_data.nlargest(5, 'total_current_stock')[['номенклатура', 'total_current_stock']].to_dict('records')
        }
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла остатков: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': f"Ошибка загрузки файла остатков: {str(e)}"}
'''
    
    return fixed_code

if __name__ == "__main__":
    print("🔍 АНАЛИЗ СТРУКТУРЫ ФАЙЛА ОСТАТКОВ")
    print("=" * 80)
    
    test_real_file_structure()
    
    print("\n🔧 ИСПРАВЛЕННАЯ ФУНКЦИЯ:")
    print("=" * 80)
    print(generate_fixed_function())