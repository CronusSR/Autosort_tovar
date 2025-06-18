# warehouse_hierarchy_system.py
"""
Система учета иерархии складов и распределения товаров
"""

def get_warehouse_hierarchy_config():
    """
    Конфигурация иерархии складов с типами точек и связями
    """
    return {
        # 🏢 ГЛАВНЫЙ ХАБ (уровень 1)
        'main_hub': {
            'name': 'База Склад Фурнитура Комплект',
            'city': 'алматы',
            'type': 'hub',
            'level': 1,
            'description': 'Главный распределительный центр',
            'supplies_to': [
                'kazybayeva_warehouse', 'shymkent_warehouse', 'astana_warehouse',
                'baris_store', 'ao_store'  # некоторые магазины питаются напрямую
            ],
            'receives_from': ['suppliers'],  # от поставщиков
            'ads_multiplier': 1.5,  # коэффициент запаса для хаба
            'min_days': 45,
            'max_days': 90
        },
        
        # 🏪 РЕГИОНАЛЬНЫЕ СКЛАДЫ (уровень 2)
        'kazybayeva_warehouse': {
            'name': 'Казыбаева Склад Фурнитура TRADE',
            'city': 'алматы', 
            'type': 'warehouse',
            'level': 2,
            'description': 'Региональный склад для магазина Казыбаева',
            'supplies_to': ['kazybayeva_store'],
            'receives_from': ['main_hub'],
            'ads_multiplier': 1.2,
            'min_days': 20,
            'max_days': 45
        },
        
        'shymkent_warehouse': {
            'name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
            'city': 'шымкент',
            'type': 'warehouse', 
            'level': 2,
            'description': 'Региональный склад для Шымкента',
            'supplies_to': ['shymkent_store'],
            'receives_from': ['main_hub'],
            'ads_multiplier': 1.2,
            'min_days': 20,
            'max_days': 45
        },
        
        'astana_warehouse': {
            'name': 'склад фурнитура № 1',
            'city': 'астана',
            'type': 'warehouse',
            'level': 2, 
            'description': 'Региональный склад для Астаны',
            'supplies_to': ['astana_store'],
            'receives_from': ['main_hub'],
            'ads_multiplier': 1.2,
            'min_days': 20,
            'max_days': 45
        },
        
        # 🛒 МАГАЗИНЫ (уровень 3)
        'kazybayeva_store': {
            'name': 'ТД Казыбаева ФУРНИТУРА магазин',
            'city': 'алматы',
            'type': 'store',
            'level': 3,
            'description': 'Магазин в Алматы',
            'supplies_to': ['customers'],
            'receives_from': ['kazybayeva_warehouse'],
            'ads_multiplier': 1.0,  # ADS магазина = базовый ADS
            'min_days': 10,
            'max_days': 25
        },
        
        'shymkent_store': {
            'name': '6 Склад фурнитуры "Овощная база" Магазин',
            'city': 'шымкент',
            'type': 'store',
            'level': 3,
            'description': 'Магазин в Шымкенте',
            'supplies_to': ['customers'],
            'receives_from': ['shymkent_warehouse'],
            'ads_multiplier': 1.0,
            'min_days': 10,
            'max_days': 25
        },
        
        'astana_store': {
            'name': 'Магазин фурнитуры',
            'city': 'астана',
            'type': 'store',
            'level': 3,
            'description': 'Магазин в Астане',
            'supplies_to': ['customers'],
            'receives_from': ['astana_warehouse'],
            'ads_multiplier': 1.0,
            'min_days': 10,
            'max_days': 25
        },
        
        # 🛒 КОМБИНИРОВАННЫЕ ТОЧКИ (магазин+склад)
        'baris_store': {
            'name': 'Барыс Склад Фурнитура TRADE',
            'city': 'алматы',
            'type': 'store_warehouse',  # комбинированный тип
            'level': 2.5,  # между складом и магазином
            'description': 'Магазин+склад в Алматы',
            'supplies_to': ['customers'],
            'receives_from': ['main_hub'],
            'ads_multiplier': 1.1,
            'min_days': 15,
            'max_days': 35
        },
        
        'ao_store': {
            'name': 'АО Склад Фурнитура TRADE',
            'city': 'алматы',
            'type': 'specialized_store',  # специализированный магазин
            'level': 3,
            'description': 'Специализированный магазин (кромочные материалы)',
            'supplies_to': ['customers'],
            'receives_from': ['main_hub'],
            'ads_multiplier': 1.0,
            'min_days': 10,
            'max_days': 25,
            'specialization': 'кромочные материалы'
        }
    }

def get_warehouse_name_mapping():
    """
    Маппинг всех возможных названий складов к их ключам в иерархии
    """
    return {
        # Главный хаб
        'База Склад Фурнитура Комплект': 'main_hub',
        'База_Комплект': 'main_hub',
        
        # Региональные склады
        'Казыбаева Склад Фурнитура TRADE': 'kazybayeva_warehouse',
        'Казыбаева_TRADE': 'kazybayeva_warehouse',
        
        '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': 'shymkent_warehouse',
        'Шымкент_Овощная_база': 'shymkent_warehouse',
        
        'склад фурнитура № 1': 'astana_warehouse', 
        'Склад_1': 'astana_warehouse',
        
        # Магазины
        'ТД Казыбаева ФУРНИТУРА магазин': 'kazybayeva_store',
        'Казыбаева_магазин': 'kazybayeva_store',
        
        '6 Склад фурнитуры "Овощная база" Магазин': 'shymkent_store',
        'Овощная_база_Магазин': 'shymkent_store',
        
        'Магазин фурнитуры': 'astana_store',
        'Магазин_фурнитуры': 'astana_store',
        
        # Комбинированные точки
        'Барыс Склад Фурнитура TRADE': 'baris_store',
        'Барыс_TRADE': 'baris_store',
        
        'АО Склад Фурнитура TRADE': 'ao_store',
        'АО_TRADE': 'ao_store'
    }

def analyze_warehouse_with_hierarchy(item_name, item_stock_data, ads_value, hierarchy_config):
    """
    Анализирует остатки товара с учетом иерархии складов
    
    Args:
        item_name: Название товара
        item_stock_data: Словарь {warehouse_name: stock_quantity}
        ads_value: ADS товара
        hierarchy_config: Конфигурация иерархии
        
    Returns:
        dict: Анализ с рекомендациями по перемещениям
    """
    
    name_mapping = get_warehouse_name_mapping()
    analysis = {
        'item_name': item_name,
        'ads': ads_value,
        'warehouses': {},
        'movement_recommendations': [],
        'total_stock': 0,
        'total_needed': 0,
        'surplus': {},
        'deficit': {}
    }
    
    # Анализируем каждый склад
    for warehouse_name, stock_qty in item_stock_data.items():
        if stock_qty <= 0:
            continue
            
        # Находим конфигурацию склада
        warehouse_key = find_warehouse_key(warehouse_name, name_mapping)
        if not warehouse_key or warehouse_key not in hierarchy_config:
            continue
            
        config = hierarchy_config[warehouse_key]
        
        # Рассчитываем потребности склада
        warehouse_ads = ads_value * config['ads_multiplier']
        min_stock = warehouse_ads * config['min_days']
        max_stock = warehouse_ads * config['max_days']
        
        # Анализ состояния склада
        status = analyze_warehouse_status(stock_qty, min_stock, max_stock)
        
        analysis['warehouses'][warehouse_key] = {
            'name': config['name'],
            'city': config['city'],
            'type': config['type'],
            'level': config['level'],
            'current_stock': stock_qty,
            'warehouse_ads': warehouse_ads,
            'min_stock': min_stock,
            'max_stock': max_stock,
            'status': status,
            'surplus_deficit': stock_qty - min_stock,
            'days_of_stock': stock_qty / warehouse_ads if warehouse_ads > 0 else 999
        }
        
        analysis['total_stock'] += stock_qty
        analysis['total_needed'] += min_stock
        
        # Определяем излишки и дефициты
        if stock_qty > max_stock:
            analysis['surplus'][warehouse_key] = stock_qty - max_stock
        elif stock_qty < min_stock:
            analysis['deficit'][warehouse_key] = min_stock - stock_qty
    
    # Генерируем рекомендации по перемещениям
    analysis['movement_recommendations'] = generate_movement_recommendations(
        analysis, hierarchy_config
    )
    
    return analysis

def find_warehouse_key(warehouse_name, name_mapping):
    """
    Находит ключ склада по его названию с умным поиском
    """
    
    # Точное совпадение
    if warehouse_name in name_mapping:
        return name_mapping[warehouse_name]
    
    # Поиск по частичному совпадению
    warehouse_name_lower = warehouse_name.lower()
    
    for mapped_name, key in name_mapping.items():
        if mapped_name.lower() in warehouse_name_lower or warehouse_name_lower in mapped_name.lower():
            return key
    
    # Поиск по ключевым словам
    if 'база' in warehouse_name_lower and 'комплект' in warehouse_name_lower:
        return 'main_hub'
    elif 'казыбаева' in warehouse_name_lower:
        if 'магазин' in warehouse_name_lower or 'тд' in warehouse_name_lower:
            return 'kazybayeva_store'
        else:
            return 'kazybayeva_warehouse'
    elif 'шымкент' in warehouse_name_lower or 'овощная' in warehouse_name_lower:
        if 'магазин' in warehouse_name_lower:
            return 'shymkent_store'
        else:
            return 'shymkent_warehouse'
    elif 'астана' in warehouse_name_lower or ('магазин' in warehouse_name_lower and 'фурнитур' in warehouse_name_lower):
        if 'магазин' in warehouse_name_lower:
            return 'astana_store'
        else:
            return 'astana_warehouse'
    elif 'барыс' in warehouse_name_lower:
        return 'baris_store'
    elif 'ао' in warehouse_name_lower:
        return 'ao_store'
    
    return None

def analyze_warehouse_status(current_stock, min_stock, max_stock):
    """
    Анализирует статус склада
    """
    
    if current_stock < min_stock * 0.5:
        return 'critical'
    elif current_stock < min_stock:
        return 'low'
    elif current_stock > max_stock:
        return 'excess'
    elif current_stock > max_stock * 0.8:
        return 'high'
    else:
        return 'normal'

def generate_movement_recommendations(analysis, hierarchy_config):
    """
    Генерирует рекомендации по перемещениям товаров между складами
    """
    
    recommendations = []
    
    # Логика перемещений: от избытка к дефициту с учетом иерархии
    
    # 1. Перемещения внутри города (между уровнями)
    city_movements = generate_city_internal_movements(analysis, hierarchy_config)
    recommendations.extend(city_movements)
    
    # 2. Перемещения между городами (через главный хаб)
    inter_city_movements = generate_inter_city_movements(analysis, hierarchy_config)
    recommendations.extend(inter_city_movements)
    
    # 3. Заказы от поставщиков (если общий дефицит)
    supplier_orders = generate_supplier_orders(analysis, hierarchy_config)
    recommendations.extend(supplier_orders)
    
    return recommendations

def generate_city_internal_movements(analysis, hierarchy_config):
    """
    Генерирует рекомендации по перемещениям внутри города
    """
    
    movements = []
    warehouses = analysis['warehouses']
    
    # Группируем склады по городам
    cities = {}
    for key, data in warehouses.items():
        city = data['city']
        if city not in cities:
            cities[city] = []
        cities[city].append((key, data))
    
    # Анализируем каждый город
    for city, city_warehouses in cities.items():
        if len(city_warehouses) < 2:
            continue
            
        # Сортируем по уровню иерархии (хаб -> склад -> магазин)
        city_warehouses.sort(key=lambda x: x[1]['level'])
        
        # Ищем возможности перемещений
        for i, (from_key, from_data) in enumerate(city_warehouses):
            if from_data['status'] in ['excess', 'high']:
                # Ищем получателей на нижних уровнях
                for j, (to_key, to_data) in enumerate(city_warehouses[i+1:], i+1):
                    if to_data['status'] in ['critical', 'low']:
                        # Рассчитываем количество для перемещения
                        available = analysis['surplus'].get(from_key, 0)
                        needed = analysis['deficit'].get(to_key, 0)
                        
                        if available > 0 and needed > 0:
                            move_qty = min(available, needed)
                            
                            movements.append({
                                'type': 'internal_movement',
                                'from': from_data['name'],
                                'to': to_data['name'],
                                'quantity': move_qty,
                                'reason': f"Перемещение излишка в {city}",
                                'priority': 'high' if to_data['status'] == 'critical' else 'medium'
                            })
    
    return movements

def generate_inter_city_movements(analysis, hierarchy_config):
    """
    Генерирует рекомендации по перемещениям между городами
    """
    
    movements = []
    
    # Межгородские перемещения всегда идут через главный хаб
    main_hub_data = None
    critical_warehouses = []
    
    for key, data in analysis['warehouses'].items():
        if key == 'main_hub':
            main_hub_data = data
        elif data['status'] == 'critical':
            critical_warehouses.append((key, data))
    
    if main_hub_data and critical_warehouses:
        hub_surplus = analysis['surplus'].get('main_hub', 0)
        
        for warehouse_key, warehouse_data in critical_warehouses:
            if warehouse_data['city'] != 'алматы':  # Не в том же городе что хаб
                needed = analysis['deficit'].get(warehouse_key, 0)
                
                if hub_surplus > 0 and needed > 0:
                    move_qty = min(hub_surplus, needed)
                    
                    movements.append({
                        'type': 'inter_city_movement',
                        'from': main_hub_data['name'],
                        'to': warehouse_data['name'],
                        'quantity': move_qty,
                        'reason': f"Экстренная поставка в {warehouse_data['city']}",
                        'priority': 'critical'
                    })
                    
                    hub_surplus -= move_qty
    
    return movements

def generate_supplier_orders(analysis, hierarchy_config):
    """
    Генерирует рекомендации по заказам от поставщиков
    """
    
    orders = []
    
    # Заказываем на главный хаб если есть общий дефицит
    total_deficit = sum(analysis['deficit'].values())
    
    if total_deficit > 0:
        orders.append({
            'type': 'supplier_order',
            'to': 'База Склад Фурнитура Комплект',
            'quantity': total_deficit * 1.2,  # С запасом 20%
            'reason': 'Восполнение общего дефицита в сети',
            'priority': 'medium'
        })
    
    return orders

def apply_hierarchy_system_to_warehouse_analyzer(system):
    """
    Интегрирует систему иерархии в анализатор складов
    """
    
    if not hasattr(system, 'warehouse_analyzer'):
        print("❌ Анализатор складов не найден")
        return False
    
    # Добавляем новые методы к анализатору
    system.warehouse_analyzer.hierarchy_config = get_warehouse_hierarchy_config()
    system.warehouse_analyzer.name_mapping = get_warehouse_name_mapping()
    system.warehouse_analyzer.analyze_with_hierarchy = lambda item_name, stock_data, ads: analyze_warehouse_with_hierarchy(
        item_name, stock_data, ads, system.warehouse_analyzer.hierarchy_config
    )
    
    print("✅ Система иерархии складов интегрирована в анализатор")
    return True