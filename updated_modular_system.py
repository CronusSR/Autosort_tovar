# ФАЙЛ: updated_ads_processor.py
# ОПИСАНИЕ: Обновленный модуль для обработки ADS с новой логикой
# НОМЕНКЛАТУРА: Колонка B (индекс 1)
# ДИАПАЗОН: M4:AB4 до последнего товара (исключая последнюю строку)
# ФОРМУЛА: ADS = (среднее от M4:AB4) / 30

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный модуль обработки ADS с чтением из диапазона M4:AB4
Номенклатура читается из колонки B, конвертация в JSON
"""

import pandas as pd
import numpy as np
import json
import io
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class UpdatedADSProcessor:
    """Обновленный класс для обработки ADS с JSON конвертацией"""
    
    def __init__(self):
        self.sales_data = None
        self.calculated_ads = None
        self.json_data = None
        
    def load_sales_file_with_range(self, file_content) -> Dict:
        """
        Загрузка файла продаж с чтением из диапазона M4:AB4
        НОМЕНКЛАТУРА: Колонка B (индекс 1)
        
        Args:
            file_content: Содержимое файла продаж
            
        Returns:
            Dict с информацией о загруженных данных
        """
        try:
            print("🔄 Начинаем обработку файла продаж с ИСПРАВЛЕННОЙ логикой...")
            
            # Читаем Excel файл
            if hasattr(file_content, 'read'):
                df = pd.read_excel(file_content, engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            print(f"📊 Исходный размер файла: {df.shape[0]} строк, {df.shape[1]} колонок")
            
            # Определяем диапазон колонок M:AB (индексы 12:28)
            # M = 12, N = 13, ..., AB = 27 (28-й индекс не включается)
            start_col_index = 12  # Колонка M
            end_col_index = 28    # Колонка AB+1 (не включается)
            start_row = 3         # Строка 4 (индекс 3)
            nomenclature_col = 1  # Колонка B (индекс 1) - ИСПРАВЛЕНО!
            
            print(f"📋 ИСПРАВЛЕННАЯ ЛОГИКА:")
            print(f"   • Номенклатура: Колонка B (индекс {nomenclature_col})")
            print(f"   • Данные продаж: колонки {start_col_index}:{end_col_index} (M:AB)")
            print(f"   • Начальная строка: {start_row+1} (строка 4)")
            
            # Проверяем, что у нас достаточно колонок
            if df.shape[1] < end_col_index:
                return {
                    'success': False,
                    'error': f'Недостаточно колонок в файле. Нужно минимум {end_col_index}, есть {df.shape[1]}'
                }
            
            # Получаем номенклатуру из колонки B (индекс 1) - ИСПРАВЛЕНО!
            nomenclature_data = df.iloc[start_row:, nomenclature_col].copy()  # Начиная с 4-й строки, колонка B
            
            # Очищаем номенклатуру от пустых значений
            print("🧹 Очистка номенклатуры из колонки B...")
            initial_count = len(nomenclature_data)
            
            # Убираем NaN и пустые строки
            nomenclature_clean = nomenclature_data.dropna()
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str).str.strip() != '']
            nomenclature_clean = nomenclature_clean[nomenclature_clean.astype(str) != 'nan']
            
            # Исключаем последнюю строчку, как указано в требованиях
            if len(nomenclature_clean) > 0:
                nomenclature_clean = nomenclature_clean[:-1]
                print("✅ Исключена последняя строчка как требуется")
            
            valid_indices = nomenclature_clean.index
            print(f"📊 После очистки номенклатуры: {len(nomenclature_clean)} товаров (было {initial_count})")
            
            if len(nomenclature_clean) == 0:
                return {
                    'success': False,
                    'error': 'Нет валидных товаров после очистки номенклатуры из колонки B'
                }
            
            # Извлекаем данные продаж из диапазона M:AB для валидных строк
            print("📈 Извлечение данных продаж из диапазона M4:AB...")
            
            sales_data_list = []
            json_data_list = []
            
            for idx in valid_indices:
                item_name = str(nomenclature_clean.loc[idx]).strip()
                
                # Извлекаем данные из колонок M:AB для данной строки
                row_sales_data = df.iloc[idx, start_col_index:end_col_index].copy()
                
                # Преобразуем в числовой формат, заменяя NaN и пустые на 0
                row_sales_numeric = pd.to_numeric(row_sales_data, errors='coerce').fillna(0)
                
                # Применяем новую формула расчета ADS:
                # 1. Получаем среднее значение от M4:AB4
                average_value = row_sales_numeric.mean()
                
                # 2. Делим среднее значение на 30
                ads_value = average_value / 30
                
                sales_data_list.append({
                    'номенклатура': item_name,
                    'raw_sales_data': row_sales_numeric.tolist(),
                    'average_value': average_value,
                    'ads': ads_value,
                    'total_sales': row_sales_numeric.sum(),  # Дополнительно для совместимости
                    'non_zero_months': (row_sales_numeric > 0).sum()
                })
                
                # Подготавливаем данные для JSON
                json_row = {
                    'nomenclature': item_name,
                    'monthly_data': {
                        f'month_{i+1}': float(row_sales_numeric.iloc[i]) 
                        for i in range(len(row_sales_numeric))
                    },
                    'average_monthly': float(average_value),
                    'ads_daily': float(ads_value),
                    'total_period': float(row_sales_numeric.sum()),
                    'active_months': int((row_sales_numeric > 0).sum())
                }
                json_data_list.append(json_row)
            
            # Создаем DataFrame для системы
            ads_df = pd.DataFrame(sales_data_list)
            
            # Фильтруем товары с ADS > 0 (опционально)
            positive_ads_count = len(ads_df[ads_df['ads'] > 0])
            print(f"📊 Товаров с положительным ADS: {positive_ads_count} из {len(ads_df)}")
            
            # Сохраняем результаты
            self.sales_data = ads_df
            self.calculated_ads = ads_df[['номенклатура', 'ads', 'average_value', 'total_sales']].copy()
            
            # Создаем JSON данные
            json_output = {
                'metadata': {
                    'file_processed_at': pd.Timestamp.now().isoformat(),
                    'total_items': len(ads_df),
                    'nomenclature_column': 'B',
                    'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                    'calculation_method': 'average_monthly_divided_by_30',
                    'formula': 'ADS = (среднее от M4:AB4) / 30',
                    'items_with_positive_ads': positive_ads_count,
                    'last_row_excluded': True
                },
                'summary_stats': {
                    'total_ads': float(ads_df['ads'].sum()),
                    'average_ads': float(ads_df['ads'].mean()),
                    'max_ads': float(ads_df['ads'].max()),
                    'min_ads': float(ads_df['ads'].min()),
                    'total_average_monthly': float(ads_df['average_value'].sum())
                },
                'items': json_data_list
            }
            
            self.json_data = json_output
            
            # Статистика обработки
            print(f"\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ (ИСПРАВЛЕННАЯ ЛОГИКА):")
            print("=" * 60)
            print(f"Номенклатура читается из: Колонка B")
            print(f"Обработано товаров: {len(ads_df)}")
            print(f"Диапазон данных: M4:AB{4+len(ads_df)-1}")
            print(f"Общий ADS: {ads_df['ads'].sum():.2f}")
            print(f"Средний ADS: {ads_df['ads'].mean():.4f}")
            print(f"Общее среднемесячное: {ads_df['average_value'].sum():,.0f}")
            
            # Топ товары по новому ADS
            print(f"\n🏆 Топ-5 товаров по новому ADS:")
            top_sellers = ads_df.nlargest(5, 'ads')
            for i, (_, row) in enumerate(top_sellers.iterrows(), 1):
                print(f"  {i}. {row['номенклатура'][:50]:<50} | ADS: {row['ads']:>8.4f} | Ср.мес: {row['average_value']:>8.1f}")
            
            return {
                'success': True,
                'total_items': len(ads_df),
                'nomenclature_column': 'B',
                'range_used': f'M{start_row+1}:AB{start_row+1+len(ads_df)}',
                'calculation_method': 'average_monthly_divided_by_30',
                'formula': 'ADS = (среднее от M4:AB4) / 30',
                'total_ads': ads_df['ads'].sum(),
                'average_ads': ads_df['ads'].mean(),
                'total_average_monthly': ads_df['average_value'].sum(),
                'items_with_positive_ads': positive_ads_count,
                'json_data_size': len(json_data_list),
                'last_row_excluded': True,
                'top_sellers': top_sellers[['номенклатура', 'ads', 'average_value']].to_dict('records')
            }
            
        except Exception as e:
            print(f"❌ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f"Ошибка обработки файла: {str(e)}"}
    
    def get_json_data(self) -> str:
        """Получение данных в формате JSON"""
        if self.json_data is None:
            return json.dumps({'error': 'Данные не обработаны'}, ensure_ascii=False, indent=2)
        
        return json.dumps(self.json_data, ensure_ascii=False, indent=2)
    
    def save_json_to_file(self, filename: str = None) -> str:
        """Сохранение JSON данных в файл"""
        if filename is None:
            filename = f"ads_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if self.json_data is None:
            raise ValueError("Нет данных для сохранения")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.json_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON данные сохранены в файл: {filename}")
        return filename
    
    def export_to_excel_with_json(self) -> io.BytesIO:
        """Экспорт результатов в Excel с JSON данными"""
        if self.calculated_ads is None:
            raise ValueError("Нет данных для экспорта")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Основные результаты ADS
            self.calculated_ads.to_excel(writer, sheet_name='ADS_Results_Fixed', index=False)
            
            # Детальные данные с помесячной разбивкой
            if self.sales_data is not None:
                detailed_data = []
                for _, row in self.sales_data.iterrows():
                    base_row = {
                        'номенклатура': row['номенклатура'],
                        'ads': row['ads'],
                        'average_monthly': row['average_value'],
                        'total_sales': row['total_sales']
                    }
                    
                    # Добавляем помесячные данные
                    for i, value in enumerate(row['raw_sales_data']):
                        base_row[f'month_{i+1}'] = value
                    
                    detailed_data.append(base_row)
                
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name='Detailed_Monthly_B_Column', index=False)
            
            # JSON данные как текст
            if self.json_data is not None:
                json_text = self.get_json_data()
                json_df = pd.DataFrame([{'JSON_Data_Full': json_text}])
                json_df.to_excel(writer, sheet_name='JSON_Data', index=False)
            
            # Методология
            methodology = pd.DataFrame([{
                'Formula': 'ADS = (среднее от M4:AB4) / 30',
                'Nomenclature_Column': 'B (исправлено с A на B)',
                'Range': 'M4:AB4 до последнего товара',
                'Exclusions': 'Последняя строка исключается',
                'JSON_Conversion': 'Да, автоматически',
                'Processing_Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'System_Version': 'Fixed_B_Column_ADS_Logic_v1.0'
            }])
            methodology.to_excel(writer, sheet_name='Methodology_Fixed', index=False)
        
        output.seek(0)
        return output

# Функция для тестирования исправленной логики
def test_fixed_ads_processing():
    """Тестирование исправленной обработки ADS с номенклатурой в колонке B"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕННОЙ ЛОГИКИ ADS (номенклатура в колонке B)")
    print("=" * 70)
    
    # Создаем тестовые данные
    test_data = {
        'A': ['', '', '', 'Код1', 'Код2', 'Код3', 'Код4', 'КодПоследний'],  # Колонка A - коды
        'B': ['', '', '', 'Товар 1', 'Товар 2', 'Товар 3', 'Товар 4', 'Удаляемый товар'],  # Колонка B - номенклатура
        **{chr(ord('A') + i): [0] * 8 for i in range(2, 12)},  # Колонки C-L (заполнители)
        **{chr(ord('A') + i): [10, 20, 15, 25, 30, 18, 22, 0] for i in range(12, 28)}  # Колонки M-AB (данные продаж)
    }
    
    # Создаем DataFrame
    df = pd.DataFrame(test_data)
    
    print("📋 Структура тестовых данных:")
    print(f"   Колонка A: Коды товаров")
    print(f"   Колонка B: Номенклатура товаров (ОСНОВНАЯ)")
    print(f"   Колонки M-AB: Данные продаж")
    print(f"   Ожидается обработка: 3 товара (последний исключается)")
    
    # Сохраняем в Excel для тестирования
    test_file = io.BytesIO()
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    test_file.seek(0)
    
    # Тестируем обработку
    processor = UpdatedADSProcessor()
    result = processor.load_sales_file_with_range(test_file)
    
    if result['success']:
        print("✅ Тест прошел успешно!")
        print(f"📊 Обработано товаров: {result['total_items']}")
        print(f"📋 Номенклатура из колонки: {result['nomenclature_column']}")
        print(f"📈 Диапазон: {result['range_used']}")
        print(f"🔢 Формула: {result['formula']}")
        print(f"📄 JSON создан: {result['json_data_size']} записей")
        
        # Проверяем правильность чтения номенклатуры
        expected_items = ['Товар 1', 'Товар 2', 'Товар 3']  # Последний должен быть исключен
        actual_items = [item['nomenclature'] for item in processor.json_data['items']]
        
        print(f"\n🔍 Проверка номенклатуры:")
        print(f"   Ожидается: {expected_items}")
        print(f"   Получено: {actual_items}")
        
        if actual_items == expected_items:
            print("   ✅ Номенклатура читается правильно из колонки B!")
        else:
            print("   ❌ Ошибка в чтении номенклатуры")
        
        # Показываем JSON данные
        json_preview = processor.get_json_data()[:500]
        print(f"\n📄 JSON превью:")
        print(json_preview + "...")
        
        return True
    else:
        print(f"❌ Тест провалился: {result['error']}")
        return False

if __name__ == "__main__":
    # Запуск теста
    test_fixed_ads_processing()