"""
Тест системы аналитики оборачиваемости
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from turnover_analytics_system import TurnoverAnalyticsSystem
import pandas as pd

def test_system():
    print("🧪 Тестирование системы аналитики оборачиваемости...")
    
    # Инициализация
    system = TurnoverAnalyticsSystem()
    print("✅ Система инициализирована")
    
    # Тест загрузки файла остатков
    try:
        stock_data = system.load_stock_data('2025-06-30 (4).json')
        print(f"✅ Файл остатков загружен: {len(stock_data['ОстаткиПоСкладам'])} складов")
        
        # Проверим структуру данных
        total_items = sum(len(wh['Остатки']) for wh in stock_data['ОстаткиПоСкладам'])
        print(f"   Всего товарных позиций: {total_items}")
        
        # Проверим иерархию категорий
        sample_item = stock_data['ОстаткиПоСкладам'][0]['Остатки'][0]
        cat1, cat2, cat3 = system.extract_category_hierarchy(sample_item['ПутьКатегорий'])
        print(f"   Пример категории: {cat3} -> {cat2} -> {cat1}")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки остатков: {e}")
        return False
    
    # Тест загрузки файла продаж (создадим пустой для теста)
    try:
        # Создаем тестовые данные продаж
        test_sales_data = pd.DataFrame({
            'Артикул': ['AP740.1242F3', 'AP740.1276F3'],
            'Продажи склад 1': [1000, 2000],
            'Продажи склад 2': [500, 1500]
        })
        print("✅ Тестовые данные продаж созданы")
        
    except Exception as e:
        print(f"❌ Ошибка создания тестовых данных: {e}")
        return False
    
    # Тест расчета оборачиваемости по категориям
    try:
        turnover_df = system.calculate_turnover_by_category(stock_data, test_sales_data)
        print(f"✅ Оборачиваемость по категориям рассчитана: {len(turnover_df)} категорий")
        
        if len(turnover_df) > 0:
            print(f"   Топ категория: {turnover_df.iloc[0]['Категория товара']}")
            print(f"   Остаток: {turnover_df.iloc[0]['Остаток (себестоимость)']:,.0f} ₸")
        
    except Exception as e:
        print(f"❌ Ошибка расчета оборачиваемости категорий: {e}")
        return False
    
    # Тест расчета оборачиваемости складов
    try:
        warehouse_turnover_df = system.calculate_warehouse_turnover(stock_data, test_sales_data)
        print(f"✅ Оборачиваемость складов рассчитана: {len(warehouse_turnover_df)} складов")
        
        if len(warehouse_turnover_df) > 0:
            print(f"   Пример склада: {warehouse_turnover_df.iloc[0]['Склад']}")
            print(f"   Город: {warehouse_turnover_df.iloc[0]['Город']}")
        
    except Exception as e:
        print(f"❌ Ошибка расчета оборачиваемости складов: {e}")
        return False
    
    # Тест ABC-анализа
    try:
        abc_results = system.calculate_abc_by_warehouse(stock_data, test_sales_data)
        print(f"✅ ABC-анализ выполнен для {len(abc_results)} складов")
        
        if abc_results:
            first_warehouse = list(abc_results.keys())[0]
            abc_df = abc_results[first_warehouse]
            print(f"   Пример склада: {first_warehouse}")
            print(f"   Категорий в анализе: {len(abc_df)}")
        
    except Exception as e:
        print(f"❌ Ошибка ABC-анализа: {e}")
        return False
    
    # Тест генерации рекомендаций
    try:
        recommendations_df = system.generate_movement_recommendations(stock_data, test_sales_data)
        print(f"✅ Рекомендации сгенерированы: {len(recommendations_df)} позиций")
        
        if len(recommendations_df) > 0:
            print(f"   Пример рекомендации:")
            rec = recommendations_df.iloc[0]
            print(f"   {rec['Артикул']}: {rec['Откуда']} -> {rec['Куда']}")
            print(f"   Количество: {rec['Количество к перемещению']}")
        
    except Exception as e:
        print(f"❌ Ошибка генерации рекомендаций: {e}")
        return False
    
    print("\n🎉 Все тесты пройдены успешно!")
    return True

if __name__ == "__main__":
    test_system()