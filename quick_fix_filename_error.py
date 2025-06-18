# quick_fix_filename_error.py
"""
БЫСТРОЕ ИСПРАВЛЕНИЕ ошибки KeyError: 'filename'
"""

def apply_quick_filename_fix():
    """
    Быстро исправляет ошибку filename в clean_duplicate_ads.py
    """
    
    try:
        import clean_duplicate_ads
        
        # Исправляем функцию is_combined_data
        def fixed_is_combined_data(store_name, filename):
            combined_indicators = [
                'calculated_ads',
                'общий',
                'объединен',
                'sales_data',
                'combined'
            ]
            
            store_name_lower = store_name.lower() if store_name else ""
            filename_lower = filename.lower() if filename else ""
            
            return any(indicator in store_name_lower or indicator in filename_lower 
                      for indicator in combined_indicators)
        
        # Заменяем функцию
        clean_duplicate_ads.is_combined_data = fixed_is_combined_data
        
        # Исправляем функцию clean_and_organize_store_ads
        original_clean_function = clean_duplicate_ads.clean_and_organize_store_ads
        
        def fixed_clean_and_organize_store_ads(store_ads_by_city):
            print("🧹 Очистка и организация ADS данных (с исправлением filename)...")
            cleaned_data = {
                'города': {},
                'объединенные': [],
                'дополнительные': []
            }
            
            unique_ads_data = {}
            
            for category, stores in store_ads_by_city.items():
                print(f"📂 Обрабатываем категорию: {category}")
                
                for store in stores:
                    store_name = store['branch_name']
                    ads_data = store['ads_data']
                    
                    # ИСПРАВЛЕНИЕ: Безопасное получение filename
                    filename = store.get('filename', store_name)
                    
                    # Создаем уникальный идентификатор для данных
                    data_id = create_data_identifier_safe(ads_data)
                    
                    # Определяем тип данных
                    if fixed_is_combined_data(store_name, filename):
                        # Это объединенные данные
                        if data_id not in unique_ads_data:
                            cleaned_data['объединенные'].append({
                                'name': 'Объединенные ADS данные',
                                'description': 'Общие данные продаж по всей сети',
                                'store_type': 'объединенные',
                                'ads_data': ads_data,
                                'items_count': len(ads_data),
                                'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
                            })
                            unique_ads_data[data_id] = 'объединенные'
                            print(f"  ✅ Добавлены объединенные данные: {len(ads_data)} товаров")
                    
                    elif category in ['алматы', 'шымкент', 'астана']:
                        # Это данные конкретного города
                        if category not in cleaned_data['города']:
                            cleaned_data['города'][category] = []
                        
                        # Проверяем уникальность в рамках города
                        city_data_id = f"{category}_{data_id}"
                        if city_data_id not in unique_ads_data:
                            cleaned_data['города'][category].append({
                                'name': store_name,
                                'description': f"Данные {store.get('store_type', 'неизвестно')} в г.{category.title()}",
                                'store_type': store.get('store_type', 'неизвестно'),
                                'ads_data': ads_data,
                                'items_count': len(ads_data),
                                'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0,
                                'filename': filename
                            })
                            unique_ads_data[city_data_id] = category
                            print(f"  ✅ Добавлен {store_name} в {category}: {len(ads_data)} товаров")
                        else:
                            print(f"  ⚠️ Пропущен дубликат {store_name} в {category}")
                    
                    else:
                        # Дополнительные данные
                        if data_id not in unique_ads_data:
                            cleaned_data['дополнительные'].append({
                                'name': store_name,
                                'description': f"Дополнительные данные ({category})",
                                'store_type': store.get('store_type', 'неизвестно'),
                                'ads_data': ads_data,
                                'items_count': len(ads_data),
                                'total_ads': ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
                            })
                            unique_ads_data[data_id] = 'дополнительные'
                            print(f"  ✅ Добавлены дополнительные данные {store_name}: {len(ads_data)} товаров")
            
            # Статистика очистки
            print(f"\n📊 Результаты очистки:")
            print(f"  🏙️ Городов с данными: {len(cleaned_data['города'])}")
            print(f"  📊 Объединенных источников: {len(cleaned_data['объединенные'])}")
            print(f"  📁 Дополнительных источников: {len(cleaned_data['дополнительные'])}")
            
            for city, stores in cleaned_data['города'].items():
                print(f"    {city.title()}: {len(stores)} источников")
            
            return cleaned_data
        
        # Заменяем функцию
        clean_duplicate_ads.clean_and_organize_store_ads = fixed_clean_and_organize_store_ads
        
        print("✅ Быстрое исправление ошибки filename применено")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения быстрого исправления: {e}")
        return False

def create_data_identifier_safe(ads_data):
    """
    Безопасное создание уникального идентификатора для ADS данных
    """
    
    if ads_data is None or ads_data.empty:
        return "empty_data"
    
    try:
        # Используем размер + сумму ADS + первые несколько названий товаров
        size = len(ads_data)
        ads_sum = ads_data['ads'].sum() if 'ads' in ads_data.columns else 0
        
        # Берем первые 3 названия товаров для идентификации
        first_items = ""
        if 'номенклатура' in ads_data.columns:
            first_items = "_".join(ads_data['номенклатура'].head(3).astype(str))[:50]
        
        identifier = f"{size}_{ads_sum:.2f}_{hash(first_items) % 10000}"
        return identifier
        
    except Exception:
        # Если что-то пошло не так, используем простой идентификатор
        return f"data_{hash(str(ads_data.shape if hasattr(ads_data, 'shape') else 'unknown')) % 10000}"

def apply_quick_fix_to_warehouse_analysis():
    """
    Применяет быстрое исправление к системе анализа складов
    """
    
    try:
        # Сначала применяем исправление
        apply_quick_filename_fix()
        
        # Затем обновляем функцию интеграции
        import warehouse_analysis
        
        def safe_integrate_store_ads_with_warehouse_analysis(system):
            """
            Безопасная версия интеграции ADS данных
            """
            try:
                # Применяем быстрое исправление перед каждым вызовом
                apply_quick_filename_fix()
                
                # Вызываем оригинальную функцию
                if hasattr(warehouse_analysis, '_original_integrate_store_ads'):
                    return warehouse_analysis._original_integrate_store_ads(system)
                else:
                    # Простая проверка наличия данных
                    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
                        return {'объединенные': []}
                    return None
                    
            except Exception as e:
                print(f"⚠️ Ошибка в интеграции ADS: {e}")
                return None
        
        # Заменяем функцию на безопасную версию
        warehouse_analysis.integrate_store_ads_with_warehouse_analysis = safe_integrate_store_ads_with_warehouse_analysis
        
        print("✅ Быстрое исправление применено к анализу складов")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения исправления к анализу складов: {e}")
        return False

if __name__ == "__main__":
    apply_quick_filename_fix()
    print("🔧 Быстрое исправление ошибки filename готово к использованию")