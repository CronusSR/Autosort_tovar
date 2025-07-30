# ads_category_fix_improved.py
# Улучшенная версия исправления ADS с автоматическим извлечением категорий

import pandas as pd
import numpy as np

def extract_categories_from_system(system):
    """
    Извлекает категории из любых доступных источников в системе
    
    Приоритет источников:
    1. abc_data (если загружен ABC анализ)
    2. source_data (если загружены исходники)
    3. Создание категорий из самих данных ADS
    """
    
    category_mapping = {}
    source_info = ""
    
    # Источник 1: ABC данные (приоритет)
    if hasattr(system, 'abc_data') and system.abc_data is not None:
        print("📋 Используем категории из ABC анализа")
        source_info = "ABC анализ"
        
        abc_data = system.abc_data
        for _, row in abc_data.iterrows():
            nomenclature = str(row.get('nomenclature', row.get('номенклатура', ''))).strip()
            category = str(row.get('category', row.get('категория', ''))).strip()
            
            if nomenclature and category and nomenclature != 'nan' and category != 'nan':
                category_mapping[nomenclature] = category
    
    # Источник 2: Исходные данные
    elif hasattr(system, 'source_data') and system.source_data is not None:
        print("📋 Используем категории из исходных данных")
        source_info = "Файл исходников"
        
        source_data = system.source_data
        for _, row in source_data.iterrows():
            nomenclature = str(row.get('номенклатура', '')).strip()
            # Пробуем разные варианты колонки категории
            category = ''
            for cat_col in ['category', 'категория', 'подкатегория', 'subcategory']:
                if cat_col in row and pd.notna(row[cat_col]):
                    category = str(row[cat_col]).strip()
                    break
            
            if nomenclature and category and nomenclature != 'nan' and category != 'nan':
                category_mapping[nomenclature] = category
    
    # Источник 3: Автоматическое создание категорий
    else:
        print("📋 Создаем категории автоматически из данных ADS")
        source_info = "Автоматические категории"
        
        if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
            ads_data = system.calculated_ads
            
            # Создаем категории на основе первых слов в названии товара
            for _, row in ads_data.iterrows():
                nomenclature = str(row.get('номенклатура', '')).strip()
                if nomenclature and nomenclature != 'nan':
                    # Извлекаем первые 2-3 слова как категорию
                    words = nomenclature.split()
                    if len(words) >= 2:
                        category = ' '.join(words[:2])  # Первые 2 слова
                    elif len(words) == 1:
                        category = words[0]
                    else:
                        category = 'Общая категория'
                    
                    category_mapping[nomenclature] = category
    
    return category_mapping, source_info


def apply_category_average_ads_fix_improved(system):
    """
    Улучшенная версия исправления ADS = 0 с автоматическим поиском категорий
    """
    
    print("🔧 Применяем улучшенное исправление для ADS = 0...")
    
    # Проверяем наличие ADS данных
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        print("❌ Сначала нужно рассчитать ADS")
        return False
    
    # Создаем копию данных ADS
    ads_data = system.calculated_ads.copy()
    
    zero_ads_count = len(ads_data[ads_data['ads'] == 0])
    print(f"📊 Исходные данные:")
    print(f"   - Товаров с ADS: {len(ads_data)}")
    print(f"   - Товаров с ADS = 0: {zero_ads_count}")
    
    if zero_ads_count == 0:
        print("✅ Товаров с ADS = 0 не найдено")
        return True
    
    # Извлекаем категории из доступных источников
    category_mapping, source_info = extract_categories_from_system(system)
    
    if not category_mapping:
        print("❌ Не удалось найти информацию о категориях")
        return False
    
    print(f"📋 Создан маппинг из источника: {source_info}")
    print(f"   - Товаров с категориями: {len(category_mapping)}")
    
    # Добавляем колонку категории к данным ADS
    ads_data['category'] = ads_data['номенклатура'].map(category_mapping)
    
    # Находим товары без категории
    no_category = ads_data['category'].isna().sum()
    if no_category > 0:
        print(f"⚠️ Товаров без категории: {no_category}")
        # Присваиваем общую категорию товарам без категории
        ads_data['category'] = ads_data['category'].fillna('Общая категория')
    
    # Рассчитываем средний ADS по категориям (только из товаров с ADS > 0)
    positive_ads_data = ads_data[ads_data['ads'] > 0]
    category_avg_ads = positive_ads_data.groupby('category')['ads'].mean()
    
    print(f"\n📊 Средний ADS по категориям (из {len(positive_ads_data)} товаров с ADS > 0):")
    for category, avg_ads in category_avg_ads.head(10).items():
        count = len(positive_ads_data[positive_ads_data['category'] == category])
        print(f"   {category}: {avg_ads:.4f} (товаров: {count})")
    
    # Исправляем товары с ADS = 0
    zero_ads_mask = ads_data['ads'] == 0
    
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
            
            print(f"   ✅ {nomenclature[:40]}... | {category} | {old_ads} → {new_ads:.4f}")
            fixed_count += 1
        else:
            # Если нет данных по категории, используем общий средний ADS
            overall_avg = positive_ads_data['ads'].mean()
            if overall_avg > 0:
                ads_data.loc[idx, 'ads'] = overall_avg
                print(f"   🔄 {nomenclature[:40]}... | Общий средний | 0 → {overall_avg:.4f}")
                fixed_count += 1
            else:
                print(f"   ❌ {nomenclature[:40]}... | Нет данных для исправления")
                not_fixed_count += 1
    
    print(f"\n📊 Результаты исправления:")
    print(f"   ✅ Исправлено: {fixed_count}")
    print(f"   ❌ Не исправлено: {not_fixed_count}")
    print(f"   📈 Общий ADS до: {system.calculated_ads['ads'].sum():.2f}")
    print(f"   📈 Общий ADS после: {ads_data['ads'].sum():.2f}")
    print(f"   📋 Источник категорий: {source_info}")
    
    # Сохраняем исправленные данные
    system.calculated_ads = ads_data
    
    # Создаем резервную копию оригинальных данных
    if not hasattr(system, 'original_calculated_ads'):
        system.original_calculated_ads = system.calculated_ads.copy()
    
    # Сохраняем информацию об исправлении
    system._ads_fix_applied = True
    system._ads_fix_source = source_info
    system._ads_fix_stats = {
        'fixed_count': fixed_count,
        'not_fixed_count': not_fixed_count,
        'categories_used': len(category_avg_ads),
        'total_categories': len(category_mapping)
    }
    
    print("✅ Исправление применено успешно!")
    return True


def show_category_ads_statistics_improved(system):
    """
    Улучшенная статистика по ADS в разрезе категорий
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        print("❌ Сначала нужно рассчитать ADS")
        return
    
    ads_data = system.calculated_ads.copy()
    
    # Проверяем наличие колонки категории
    if 'category' not in ads_data.columns:
        print("❌ Категории не добавлены. Выполните apply_category_average_ads_fix_improved сначала")
        return
    
    print("📊 УЛУЧШЕННАЯ СТАТИСТИКА ADS ПО КАТЕГОРИЯМ")
    print("=" * 70)
    
    # Показываем информацию об источнике категорий
    if hasattr(system, '_ads_fix_source'):
        print(f"📋 Источник категорий: {system._ads_fix_source}")
        
    if hasattr(system, '_ads_fix_stats'):
        stats = system._ads_fix_stats
        print(f"🔧 Последнее исправление: исправлено {stats['fixed_count']}, категорий использовано {stats['categories_used']}")
    
    print()
    
    # Группируем по категориям
    category_stats = ads_data.groupby('category').agg({
        'ads': ['count', 'sum', 'mean', 'min', 'max'],
        'номенклатура': 'count'
    }).round(4)
    
    category_stats.columns = ['Количество', 'Общий ADS', 'Средний ADS', 'Мин ADS', 'Макс ADS', 'Товаров']
    
    # Добавляем информацию о доле в общем ADS
    total_ads = ads_data['ads'].sum()
    category_stats['Доля %'] = (category_stats['Общий ADS'] / total_ads * 100).round(2)
    
    # Сортируем по общему ADS
    category_stats = category_stats.sort_values('Общий ADS', ascending=False)
    
    print(category_stats)
    
    print(f"\n📈 ТОП-5 категорий по среднему ADS:")
    top_avg = category_stats.sort_values('Средний ADS', ascending=False).head(5)
    for category, row in top_avg.iterrows():
        print(f"   {category}: {row['Средний ADS']:.4f} (товаров: {int(row['Товаров'])}, доля: {row['Доля %']:.1f}%)")
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего категорий: {len(category_stats)}")
    print(f"   Общий ADS всех товаров: {ads_data['ads'].sum():.2f}")
    print(f"   Средний ADS всех товаров: {ads_data['ads'].mean():.4f}")
    print(f"   Товаров с ADS = 0: {len(ads_data[ads_data['ads'] == 0])}")


def get_categories_preview(system):
    """
    Предварительный просмотр доступных категорий
    """
    
    print("🔍 ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР КАТЕГОРИЙ")
    print("=" * 50)
    
    category_mapping, source_info = extract_categories_from_system(system)
    
    if not category_mapping:
        print("❌ Категории не найдены")
        return {}
    
    print(f"📋 Источник: {source_info}")
    print(f"📊 Найдено товаров с категориями: {len(category_mapping)}")
    
    # Группируем по категориям
    categories = {}
    for item, category in category_mapping.items():
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    print(f"📊 Уникальных категорий: {len(categories)}")
    print("\n📋 Примеры товаров по категориям:")
    
    for category, items in list(categories.items())[:5]:
        print(f"\n  🏷️ {category} ({len(items)} товаров):")
        for item in items[:3]:
            print(f"    - {item}")
        if len(items) > 3:
            print(f"    ... и еще {len(items) - 3} товаров")
    
    return categories


# Функция для интеграции в Streamlit
def quick_ads_category_fix(system):
    """
    Быстрое исправление для интеграции в Streamlit
    """
    
    if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
        return False, "ADS не рассчитан"
    
    zero_ads_count = len(system.calculated_ads[system.calculated_ads['ads'] == 0])
    
    if zero_ads_count == 0:
        return True, "Нет товаров с ADS = 0"
    
    success = apply_category_average_ads_fix_improved(system)
    
    if success:
        if hasattr(system, '_ads_fix_stats'):
            stats = system._ads_fix_stats
            return True, f"Исправлено {stats['fixed_count']} товаров из {zero_ads_count}"
        else:
            return True, f"Исправление применено для {zero_ads_count} товаров"
    else:
        return False, "Ошибка при исправлении"


# Инструкция по использованию
def instruction_for_improved_category_ads_fix():
    """
    Инструкция по использованию улучшенного исправления
    """
    
    print("""
    🔧 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ УЛУЧШЕННОГО ИСПРАВЛЕНИЯ ADS:
    
    ✨ НОВЫЕ ВОЗМОЖНОСТИ:
    - Автоматический поиск категорий из любых доступных источников
    - Приоритизация источников данных о категориях
    - Создание категорий автоматически, если не найдены
    - Детальная статистика с информацией об источниках
    
    📋 ПОРЯДОК ПОИСКА КАТЕГОРИЙ:
    1. ABC анализ (если выполнен) - приоритет
    2. Файл исходников (если загружен)
    3. Автоматическое создание из названий товаров
    
    🚀 ИСПОЛЬЗОВАНИЕ:
    
    1. Предварительный просмотр:
       get_categories_preview(ваша_система)
    
    2. Применение исправления:
       apply_category_average_ads_fix_improved(ваша_система)
    
    3. Проверка результатов:
       show_category_ads_statistics_improved(ваша_система)
    
    4. Быстрое исправление для Streamlit:
       success, message = quick_ads_category_fix(ваша_система)
    
    💡 ПРЕИМУЩЕСТВА:
    - Работает БЕЗ предварительной загрузки файла исходников
    - Использует уже имеющиеся в системе данные
    - Создает категории автоматически, если нужно
    - Подробная отчетность о процессе исправления
    """)


if __name__ == "__main__":
    instruction_for_improved_category_ads_fix()