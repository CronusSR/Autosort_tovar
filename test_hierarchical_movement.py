"""
Тест новой системы иерархических перемещений
"""

import json
from hierarchical_movement_system import HierarchicalMovementSystem

def test_hierarchical_system():
    print("🧪 Тестирование системы иерархических перемещений...")
    
    # Инициализация системы
    movement_system = HierarchicalMovementSystem()
    
    # Загружаем остатки
    try:
        with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
            stock_data = json.load(f)
        print("✅ Файл остатков загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки остатков: {e}")
        return False
    
    # Симулируем простые данные продаж для теста
    sales_data = {
        'Казыбаева Склад Фурнитура TRADE': {
            'AP740.1242F3': {'ads': 10, 'revenue': 24800, 'sold_qty': 300},
            'АК097': {'ads': 50, 'revenue': 150000, 'sold_qty': 1500}
        },
        'ТД Казыбаева ФУРНИТУРА магазин': {
            'AP740.1242F3': {'ads': 2, 'revenue': 4960, 'sold_qty': 60},
            'АК097': {'ads': 15, 'revenue': 45000, 'sold_qty': 450}
        },
        'склад фурнитура № 1': {
            'АК097': {'ads': 30, 'revenue': 90000, 'sold_qty': 900}
        },
        'Магазин фурнитуры': {
            'АК097': {'ads': 5, 'revenue': 15000, 'sold_qty': 150}
        }
    }
    
    # Тест расчета требований к остаткам
    print("\n📊 Тест расчета нормативов остатков:")
    
    test_cases = [
        ('hub', 10),      # Хаб с ADS=10
        ('warehouse', 10), # Склад с ADS=10
        ('shop', 10)      # Магазин с ADS=10
    ]
    
    for wh_type, ads in test_cases:
        min_stock, max_stock = movement_system.calculate_stock_requirements(ads, wh_type)
        print(f"   {wh_type}: ADS={ads} -> Мин={min_stock:.0f}, Макс={max_stock:.0f}")
    
    # Тест анализа состояния склада
    print("\n🔍 Тест анализа состояния:")
    
    test_states = [
        (100, 10, 'shop'),     # 10 дней остатка - норма для магазина
        (50, 10, 'shop'),      # 5 дней остатка - дефицит для магазина
        (300, 10, 'shop'),     # 30 дней остатка - избыток для магазина
        (500, 10, 'warehouse'), # 50 дней остатка - избыток для склада
        (150, 10, 'warehouse'), # 15 дней остатка - дефицит для склада
    ]
    
    for stock, ads, wh_type in test_states:
        state = movement_system.analyze_warehouse_state(stock, ads, wh_type)
        print(f"   {wh_type}: Остаток={stock}, ADS={ads} -> {state['state']} ({state['days_of_stock']:.1f} дней)")
    
    # Тест генерации рекомендаций
    print("\n🚚 Тест генерации рекомендаций:")
    
    result = movement_system.generate_hierarchical_recommendations(stock_data, sales_data)
    
    print(f"   Всего рекомендаций: {len(result['recommendations'])}")
    print(f"   Высокий приоритет: {result['high_priority']}")
    print(f"   Обработано складов: {len(result['warehouse_reports'])}")
    
    # Показываем примеры рекомендаций
    if result['recommendations']:
        print("\n📋 Примеры рекомендаций:")
        
        # Группируем по типам
        by_type = {'deficit_replenishment': [], 'excess_return': [], 'redistribution': []}
        for rec in result['recommendations']:
            by_type[rec['type']].append(rec)
        
        for rec_type, recs in by_type.items():
            if recs:
                print(f"\n   {rec_type}:")
                for rec in recs[:3]:  # Первые 3
                    print(f"      {rec['article']} - {rec['quantity']} шт")
                    print(f"      {rec['from_warehouse']} -> {rec['to_warehouse']}")
                    print(f"      Причина: {rec['reason']}")
                    print(f"      Приоритет: {rec['priority']}")
    
    # Показываем отчет по одному складу
    if result['warehouse_reports']:
        print("\n📊 Пример отчета по складу:")
        
        # Берем первый склад с рекомендациями
        for wh_name, report in result['warehouse_reports'].items():
            if report['recommendations_in'] or report['recommendations_out']:
                print(f"\n   {wh_name}:")
                print(f"   Тип: {report['type']}, Уровень: {report['level']}")
                print(f"   Город: {report['city']}")
                print(f"   Общая стоимость: {report['total_stock_cost']:,.0f} ₸")
                
                # Анализ состояний
                states = {'deficit': 0, 'normal': 0, 'excess': 0, 'no_sales': 0}
                for product in report['products_analysis']:
                    states[product['state']] += 1
                
                print(f"   Состояния товаров:")
                print(f"      Дефицит: {states['deficit']}")
                print(f"      Норма: {states['normal']}")
                print(f"      Избыток: {states['excess']}")
                print(f"      Нет продаж: {states['no_sales']}")
                
                if report['recommendations_in']:
                    print(f"   Входящие рекомендации: {len(report['recommendations_in'])}")
                
                if report['recommendations_out']:
                    print(f"   Исходящие рекомендации: {len(report['recommendations_out'])}")
                
                break
    
    print("\n✅ Тестирование завершено успешно!")
    return True

def test_warehouse_hierarchy():
    """Тест правильности иерархии складов"""
    print("\n🏭 Проверка иерархии складов...")
    
    movement_system = HierarchicalMovementSystem()
    hierarchy = movement_system.warehouse_hierarchy
    
    # Проверяем структуру
    print("\n📊 Структура сети:")
    
    # Хаб
    hub = [wh for wh, info in hierarchy.items() if info['type'] == 'hub']
    print(f"\n🏢 ХАБ (уровень 1):")
    for wh in hub:
        info = hierarchy[wh]
        print(f"   {wh} (г.{info['city']})")
        print(f"   Дети: {len(info['children'])}")
    
    # Склады 2-го уровня
    level2_warehouses = [wh for wh, info in hierarchy.items() if info['level'] == 2 and info['type'] == 'warehouse']
    print(f"\n📦 СКЛАДЫ 2-го уровня:")
    for wh in level2_warehouses:
        info = hierarchy[wh]
        print(f"   {wh} (г.{info['city']})")
        print(f"   Родитель: {info['parent']}")
        print(f"   Дети: {info['children']}")
    
    # Магазины напрямую от хаба
    direct_shops = [wh for wh, info in hierarchy.items() if info['level'] == 2 and info['type'] == 'shop']
    print(f"\n🏪 МАГАЗИНЫ от хаба (уровень 2):")
    for wh in direct_shops:
        info = hierarchy[wh]
        print(f"   {wh} (г.{info['city']})")
    
    # Магазины 3-го уровня
    level3_shops = [wh for wh, info in hierarchy.items() if info['level'] == 3]
    print(f"\n🏪 МАГАЗИНЫ 3-го уровня:")
    for wh in level3_shops:
        info = hierarchy[wh]
        print(f"   {wh} (г.{info['city']})")
        print(f"   Родитель: {info['parent']}")
    
    # Проверяем связи
    print(f"\n🔗 Проверка связей:")
    errors = 0
    
    for wh, info in hierarchy.items():
        # Проверяем что у всех кроме хаба есть родитель
        if info['level'] > 1 and not info['parent']:
            print(f"   ❌ {wh} не имеет родителя!")
            errors += 1
        
        # Проверяем что родитель существует
        if info['parent'] and info['parent'] not in hierarchy:
            print(f"   ❌ Родитель {info['parent']} для {wh} не найден!")
            errors += 1
        
        # Проверяем что все дети существуют
        for child in info['children']:
            if child not in hierarchy:
                print(f"   ❌ Ребенок {child} для {wh} не найден!")
                errors += 1
    
    if errors == 0:
        print("   ✅ Все связи корректны!")
    
    return errors == 0

if __name__ == "__main__":
    print("🧪 Комплексное тестирование системы иерархических перемещений...\n")
    
    success1 = test_warehouse_hierarchy()
    success2 = test_hierarchical_system()
    
    if success1 and success2:
        print("\n🎉 Все тесты пройдены успешно!")
        print("✅ Система готова к использованию!")
    else:
        print("\n⚠️ Есть проблемы, требующие внимания")