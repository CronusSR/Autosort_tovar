"""
Базовый тест системы аналитики без pandas
"""

import json
from collections import defaultdict

def test_basic_functionality():
    print("🧪 Базовое тестирование системы...")
    
    # Загрузка файла остатков
    try:
        with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
            stock_data = json.load(f)
        
        print(f"✅ Файл остатков загружен")
        print(f"   Дата остатков: {stock_data['ДатаОстатков']}")
        print(f"   Количество складов: {len(stock_data['ОстаткиПоСкладам'])}")
        
        # Базовая статистика
        total_items = 0
        total_cost = 0
        categories = set()
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            wh_items = len(warehouse['Остатки'])
            total_items += wh_items
            
            wh_cost = sum(item['Стоимость'] for item in warehouse['Остатки'])
            total_cost += wh_cost
            
            print(f"   📦 {wh_name}: {wh_items} позиций, {wh_cost:,.0f} ₸")
            
            # Собираем категории
            for item in warehouse['Остатки']:
                path_parts = item['ПутьКатегорий'].strip('/').split('/')
                if path_parts:
                    categories.add(path_parts[-1] if path_parts[-1] else path_parts[-2])
        
        print(f"\n📊 Общая статистика:")
        print(f"   Всего позиций: {total_items:,}")
        print(f"   Общая стоимость: {total_cost:,.0f} ₸")
        print(f"   Уникальных категорий: {len(categories)}")
        
        # Тест анализа по складам
        print(f"\n🏭 Анализ складов:")
        warehouse_stats = []
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            
            # Определяем город
            city = 'Не указан'
            if 'Шымкент' in wh_name or 'Овощная база' in wh_name:
                city = 'Шымкент'
            elif any(word in wh_name for word in ['Казыбаева', 'Барыс', 'АО', 'фурнитура № 1', 'Магазин фурнитуры']):
                city = 'Астана'
            
            wh_cost = sum(item['Стоимость'] for item in warehouse['Остатки'])
            wh_qty = sum(item['Количество'] for item in warehouse['Остатки'])
            
            warehouse_stats.append({
                'name': wh_name,
                'city': city,
                'cost': wh_cost,
                'qty': wh_qty,
                'items': len(warehouse['Остатки'])
            })
        
        # Сортируем по стоимости
        warehouse_stats.sort(key=lambda x: x['cost'], reverse=True)
        
        for wh in warehouse_stats[:5]:  # Топ-5
            print(f"   🏆 {wh['name']} ({wh['city']})")
            print(f"      Стоимость: {wh['cost']:,.0f} ₸")
            print(f"      Позиций: {wh['items']:,}")
        
        # Тест анализа категорий
        print(f"\n📦 Анализ категорий:")
        category_stats = defaultdict(lambda: {'cost': 0, 'qty': 0, 'items': 0})
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            for item in warehouse['Остатки']:
                path_parts = item['ПутьКатегорий'].strip('/').split('/')
                main_category = path_parts[-1] if path_parts and path_parts[-1] else 'Неизвестно'
                
                category_stats[main_category]['cost'] += item['Стоимость']
                category_stats[main_category]['qty'] += item['Количество']
                category_stats[main_category]['items'] += 1
        
        # Топ-10 категорий по стоимости
        top_categories = sorted(category_stats.items(), key=lambda x: x[1]['cost'], reverse=True)[:10]
        
        for i, (cat, stats) in enumerate(top_categories, 1):
            percent = (stats['cost'] / total_cost * 100) if total_cost > 0 else 0
            print(f"   {i:2d}. {cat}")
            print(f"       Стоимость: {stats['cost']:,.0f} ₸ ({percent:.1f}%)")
            print(f"       Позиций: {stats['items']:,}")
        
        print(f"\n🎯 Потенциал для перемещений:")
        
        # Анализируем товары, присутствующие на нескольких складах
        article_locations = defaultdict(list)
        
        for warehouse in stock_data['ОстаткиПоСкладам']:
            wh_name = warehouse['Склад']
            for item in warehouse['Остатки']:
                article_locations[item['Артикул']].append({
                    'warehouse': wh_name,
                    'qty': item['Количество'],
                    'cost': item['Стоимость'],
                    'name': item['Номенклатура']
                })
        
        # Находим товары на нескольких складах
        multi_warehouse_items = {art: locs for art, locs in article_locations.items() if len(locs) > 1}
        
        print(f"   Товаров на нескольких складах: {len(multi_warehouse_items):,}")
        
        # Анализируем потенциал перемещений
        high_potential = []
        
        for article, locations in list(multi_warehouse_items.items())[:100]:  # Первые 100 для примера
            if len(locations) >= 2:
                total_qty = sum(loc['qty'] for loc in locations)
                
                # Находим склады с большими и маленькими остатками
                max_loc = max(locations, key=lambda x: x['qty'])
                min_loc = min(locations, key=lambda x: x['qty'])
                
                # Если разница существенная
                if max_loc['qty'] > total_qty * 0.7 and min_loc['qty'] < total_qty * 0.1:
                    potential_move = min(max_loc['qty'] * 0.3, total_qty * 0.2)
                    
                    if potential_move >= 5:  # Минимум 5 единиц
                        high_potential.append({
                            'article': article,
                            'name': max_loc['name'],
                            'from': max_loc['warehouse'],
                            'to': min_loc['warehouse'],
                            'qty': int(potential_move),
                            'from_qty': max_loc['qty'],
                            'to_qty': min_loc['qty']
                        })
        
        # Сортируем по количеству к перемещению
        high_potential.sort(key=lambda x: x['qty'], reverse=True)
        
        print(f"   Выявлено рекомендаций: {len(high_potential)}")
        
        # Показываем топ-10 рекомендаций
        for i, rec in enumerate(high_potential[:10], 1):
            print(f"   {i:2d}. {rec['article']}")
            print(f"       {rec['name'][:50]}...")
            print(f"       {rec['from'][:30]}... -> {rec['to'][:30]}...")
            print(f"       К перемещению: {rec['qty']}")
            print(f"       Остатки: {rec['from_qty']} -> {rec['to_qty']}")
        
        print(f"\n✅ Базовое тестирование завершено успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_functionality()