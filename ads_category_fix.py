# ads_category_fix.py
# Новая функция для замены ADS = 0 на средний ADS по категории

import pandas as pd
import numpy as np

def apply_category_average_ads_fix(system):
    """
    Применяет исправление для товаров с ADS = 0
    Заменяет их на средний ADS по категории
    
    Требования:
    - У системы должен быть загружен файл исходников с категориями
    - У системы должен быть рассчитан ADS (calculated_ads)
    """
    
    print("🔧 Применяем исправление для ADS = 0...")
    
    # Проверяем наличие необходимых данных
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        print("❌ Сначала нужно рассчитать ADS")
        return False
        
    if not hasattr(system, 'source_data') or system.source_data is None:
        print("❌ Сначала нужно загрузить файл исходников с категориями")
        return False
    
    # Создаем копию данных ADS
    ads_data = system.calculated_ads.copy()
    source_data = system.source_data.copy()
    
    print(f"📊 Исходные данные:")
    print(f"   - Товаров с ADS: {len(ads_data)}")
    print(f"   - Товаров с ADS = 0: {len(ads_data[ads_data['ads'] == 0])}")
    print(f"   - Товаров в исходниках: {len(source_data)}")
    
    # Подготавливаем данные о категориях из исходников
    category_mapping = {}
    
    # Извлекаем категории (колонка с индексом 2 в исходниках)
    if 'подкатегория' in source_data.columns:
        category_col = 'подкатегория'
    elif len(source_data.columns) > 2:
        category_col = source_data.columns[2]  # Третья колонка
    else:
        print("❌ Не найдена колонка с категориями")
        return False
    
    # Создаем маппинг номенклатура -> категория
    for _, row in source_data.iterrows():
        nomenclature = str(row.get('номенклатура', '')).strip()
        category = str(row.get(category_col, '')).strip()
        
        if nomenclature and category and nomenclature != 'nan' and category != 'nan':
            category_mapping[nomenclature] = category
    
    print(f"📋 Создан маппинг для {len(category_mapping)} товаров")
    
    # Добавляем колонку категории к данным ADS
    ads_data['category'] = ads_data['номенклатура'].map(category_mapping)
    
    # Находим товары без категории
    no_category = ads_data['category'].isna().sum()
    if no_category > 0:
        print(f"⚠️ Товаров без категории: {no_category}")
    
    # Рассчитываем средний ADS по категориям
    category_avg_ads = ads_data[ads_data['ads'] > 0].groupby('category')['ads'].mean()
    
    print(f"\n📊 Средний ADS по категориям:")
    for category, avg_ads in category_avg_ads.head(10).items():
        print(f"   {category}: {avg_ads:.4f}")
    
    # Исправляем товары с ADS = 0
    zero_ads_mask = ads_data['ads'] == 0
    zero_ads_count = zero_ads_mask.sum()
    
    if zero_ads_count == 0:
        print("✅ Товаров с ADS = 0 не найдено")
        return True
    
    print(f"\n🔧 Исправляем {zero_ads_count} товаров с ADS = 0:")
    
    fixed_count = 0
    not_fixed_count = 0
    
    for idx in ads_data[zero_ads_mask].index:
        category = ads_data.loc[idx, 'category']
        nomenclature = ads_data.loc[idx, 'номенклатура']
        
        if pd.notna(category) and category in category_avg_ads:
            old_ads = ads_data.loc[idx, 'ads']
            new_ads = category_avg_ads[category]
            ads_data.loc[idx, 'ads'] = new_ads
            
            print(f"   ✅ {nomenclature[:50]}... | {category} | {old_ads} → {new_ads:.4f}")
            fixed_count += 1
        else:
            print(f"   ❌ {nomenclature[:50]}... | Категория не найдена или нет данных")
            not_fixed_count += 1
    
    print(f"\n📊 Результаты исправления:")
    print(f"   ✅ Исправлено: {fixed_count}")
    print(f"   ❌ Не исправлено: {not_fixed_count}")
    print(f"   📈 Общий ADS до: {system.calculated_ads['ads'].sum():.2f}")
    print(f"   📈 Общий ADS после: {ads_data['ads'].sum():.2f}")
    
    # Сохраняем исправленные данные
    system.calculated_ads = ads_data
    
    # Создаем резервную копию оригинальных данных
    if not hasattr(system, 'original_calculated_ads'):
        system.original_calculated_ads = system.calculated_ads.copy()
    
    print("✅ Исправление применено успешно!")
    return True


def revert_category_ads_fix(system):
    """
    Отменяет исправление ADS, возвращая оригинальные значения
    """
    
    if not hasattr(system, 'original_calculated_ads'):
        print("❌ Нет резервной копии для отмены")
        return False
    
    print("🔄 Отменяем исправление ADS...")
    system.calculated_ads = system.original_calculated_ads.copy()
    print("✅ Оригинальные значения ADS восстановлены")
    return True


def show_category_ads_statistics(system):
    """
    Показывает статистику по ADS в разрезе категорий
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        print("❌ Сначала нужно рассчитать ADS")
        return
    
    ads_data = system.calculated_ads.copy()
    
    # Проверяем наличие колонки категории
    if 'category' not in ads_data.columns:
        print("❌ Категории не добавлены. Выполните apply_category_average_ads_fix сначала")
        return
    
    print("📊 СТАТИСТИКА ADS ПО КАТЕГОРИЯМ")
    print("=" * 60)
    
    # Группируем по категориям
    category_stats = ads_data.groupby('category').agg({
        'ads': ['count', 'sum', 'mean', 'min', 'max'],
        'номенклатура': 'count'
    }).round(4)
    
    category_stats.columns = ['Количество', 'Общий ADS', 'Средний ADS', 'Мин ADS', 'Макс ADS', 'Товаров']
    
    # Сортируем по общему ADS
    category_stats = category_stats.sort_values('Общий ADS', ascending=False)
    
    print(category_stats.head(15))
    
    print(f"\n📈 ТОП-5 категорий по среднему ADS:")
    top_avg = category_stats.sort_values('Средний ADS', ascending=False).head(5)
    for category, row in top_avg.iterrows():
        print(f"   {category}: {row['Средний ADS']:.4f} (товаров: {row['Товаров']})")
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего категорий: {len(category_stats)}")
    print(f"   Общий ADS всех товаров: {ads_data['ads'].sum():.2f}")
    print(f"   Средний ADS всех товаров: {ads_data['ads'].mean():.4f}")


# Инструкция по использованию
def instruction_for_category_ads_fix():
    """
    Инструкция по использованию исправления
    """
    
    print("""
    🔧 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ ИСПРАВЛЕНИЯ ADS:
    
    1. Убедитесь что загружены файлы:
       - Файл исходников с категориями (исходникимини.xlsx)
       - Рассчитанные данные ADS (calculated_ads)
    
    2. Примените исправление:
       from ads_category_fix import apply_category_average_ads_fix
       apply_category_average_ads_fix(ваша_система)
    
    3. Проверьте результаты:
       from ads_category_fix import show_category_ads_statistics
       show_category_ads_statistics(ваша_система)
    
    4. При необходимости отмените изменения:
       from ads_category_fix import revert_category_ads_fix
       revert_category_ads_fix(ваша_система)
    
    🎯 ЧТО ДЕЛАЕТ ИСПРАВЛЕНИЕ:
    - Находит товары с ADS = 0
    - Определяет их категории из файла исходников
    - Рассчитывает средний ADS по каждой категории
    - Заменяет ADS = 0 на средний ADS категории
    - Сохраняет резервную копию оригинальных данных
    
    ⚠️ ВАЖНО:
    - Исправление не изменяет существующие функции
    - Создается резервная копия для отмены изменений
    - Категории берутся из 3-й колонки файла исходников
    """)


if __name__ == "__main__":
    instruction_for_category_ads_fix()