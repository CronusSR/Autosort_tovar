"""
Система иерархических перемещений товаров между филиалами
Учитывает правильную структуру и потоки товаров
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import json

class HierarchicalMovementSystem:
    def __init__(self):
        # Иерархия складов (адаптированная под реальные данные)
        self.warehouse_hierarchy = {
            # ХАБ (уровень 1) - главный склад
            'Казыбаева Склад Фурнитура TRADE': {
                'level': 1,
                'type': 'hub',
                'city': 'Алматы',
                'parent': None,
                'children': [
                    'ТД Казыбаева ФУРНИТУРА магазин',
                    'склад фурнитура № 1',
                    '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                    'Барыс Склад Фурнитура TRADE',
                    'АО Склад Фурнитура TRADE'
                ]
            },
            
            # СКЛАДЫ 2-го уровня
            'Барыс Склад Фурнитура TRADE': {
                'level': 2,
                'type': 'warehouse',
                'city': 'Алматы',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': []
            },
            'склад фурнитура № 1': {
                'level': 2,
                'type': 'warehouse',
                'city': 'Астана',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': ['Магазин фурнитуры']
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'level': 2,
                'type': 'warehouse',
                'city': 'Шымкент',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': ['6 Склад фурнитуры "Овощная база" Магазин']
            },
            'АО Склад Фурнитура TRADE': {
                'level': 2,
                'type': 'warehouse',
                'city': 'Алматы',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': []
            },
            
            # МАГАЗИНЫ 2-го уровня (напрямую от хаба)
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'level': 2,
                'type': 'shop',
                'city': 'Алматы',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': []
            },
            
            # МАГАЗИНЫ 3-го уровня
            'Магазин фурнитуры': {
                'level': 3,
                'type': 'shop',
                'city': 'Астана',
                'parent': 'склад фурнитура № 1',
                'children': []
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'level': 3,
                'type': 'shop',
                'city': 'Шымкент',
                'parent': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'children': []
            }
        }
        
        # Нормативы остатков по типам филиалов (в днях)
        self.stock_norms = {
            'hub': {'min_days': 45, 'max_days': 90},
            'warehouse': {'min_days': 20, 'max_days': 45},
            'shop': {'min_days': 7, 'max_days': 20}
        }
    
    def calculate_stock_requirements(self, ads: float, warehouse_type: str) -> Tuple[float, float]:
        """Расчет минимальных и максимальных остатков на основе ADS"""
        norms = self.stock_norms.get(warehouse_type, self.stock_norms['shop'])
        min_stock = ads * norms['min_days']
        max_stock = ads * norms['max_days']
        return min_stock, max_stock
    
    def analyze_warehouse_state(self, current_stock: float, ads: float, warehouse_type: str) -> Dict:
        """Анализ состояния склада: недостаток, норма или избыток"""
        if ads <= 0:
            # Для товаров без продаж считаем избытком если много остатков
            state = 'избыток' if current_stock > 100 else 'нет_продаж'
            return {
                'state': state,
                'deficit': 0,
                'excess': current_stock - 50 if current_stock > 100 else 0,  # Считаем избытком >50 шт
                'days_of_stock': 999999 if current_stock > 0 else 0,
                'min_stock': 0,
                'max_stock': 50  # Максимум для товаров без продаж
            }
        
        min_stock, max_stock = self.calculate_stock_requirements(ads, warehouse_type)
        days_of_stock = current_stock / ads
        
        if current_stock < min_stock:
            return {
                'state': 'дефицит',
                'deficit': min_stock - current_stock,
                'excess': 0,
                'days_of_stock': days_of_stock,
                'min_stock': min_stock,
                'max_stock': max_stock
            }
        elif current_stock > max_stock:
            return {
                'state': 'избыток',
                'deficit': 0,
                'excess': current_stock - max_stock,
                'days_of_stock': days_of_stock,
                'min_stock': min_stock,
                'max_stock': max_stock
            }
        else:
            return {
                'state': 'норма',
                'deficit': 0,
                'excess': 0,
                'days_of_stock': days_of_stock,
                'min_stock': min_stock,
                'max_stock': max_stock
            }
    
    def generate_hierarchical_recommendations(self, stock_data: Dict, sales_data: Dict) -> Dict:
        """
        Генерация рекомендаций по перемещениям с учетом иерархии
        
        Правила:
        1. При недостатке - берем из родительского склада
        2. При избытке - отдаем в родительский склад (или вверх по иерархии)
        3. Хаб может перераспределять между своими детьми
        """
        recommendations = []
        warehouse_reports = {}
        
        # Анализируем каждый склад
        for warehouse_name, warehouse_info in self.warehouse_hierarchy.items():
            warehouse_type = warehouse_info['type']
            
            # Находим остатки и продажи для этого склада
            warehouse_stock = self._get_warehouse_stock(warehouse_name, stock_data)
            warehouse_sales = sales_data.get(warehouse_name, {})
            
            # Создаем отчет по складу
            warehouse_report = {
                'name': warehouse_name,
                'type': warehouse_type,
                'level': warehouse_info['level'],
                'city': warehouse_info['city'],
                'parent': warehouse_info['parent'],
                'children': warehouse_info['children'],
                'total_stock_cost': 0,
                'total_stock_qty': 0,
                'products_analysis': [],
                'recommendations_in': [],  # Рекомендации на получение
                'recommendations_out': []  # Рекомендации на отдачу
            }
            
            # Анализируем каждый товар на складе
            for article, stock_item in warehouse_stock.items():
                current_stock = stock_item['qty']
                stock_cost = stock_item['cost']
                
                # Получаем ADS для товара
                ads = warehouse_sales.get(article, {}).get('ads', 0)
                
                # Если ADS = 0, пытаемся использовать среднее по категории
                if ads == 0:
                    product_category = stock_item.get('category', '')
                    category_avg_ads = warehouse_sales.get('_category_avg_ads', {})
                    if product_category and product_category in category_avg_ads:
                        ads = category_avg_ads[product_category]
                
                # Анализируем состояние
                state_analysis = self.analyze_warehouse_state(
                    current_stock, ads, warehouse_type
                )
                
                # Получаем выручку из данных продаж для этого товара
                sales_info = warehouse_sales.get(article, {})
                monthly_revenue = sales_info.get('revenue', 0)  # Фактическая выручка за период
                
                # Извлекаем последний элемент из пути категории
                full_category_path = stock_item.get('category', 'Без категории')
                category_name = self._extract_last_category(full_category_path)
                
                product_analysis = {
                    'article': article,
                    'name': stock_item['name'],
                    'category': category_name,
                    'current_stock': current_stock,
                    'stock_cost': stock_cost,
                    'ads': ads,
                    'monthly_revenue': monthly_revenue,  # Добавляем фактическую выручку
                    'state': state_analysis['state'],
                    'days_of_stock': state_analysis['days_of_stock'],
                    'min_stock': state_analysis.get('min_stock', 0),
                    'max_stock': state_analysis.get('max_stock', 0),
                    'deficit': state_analysis['deficit'],
                    'excess': state_analysis['excess']
                }
                
                warehouse_report['products_analysis'].append(product_analysis)
                warehouse_report['total_stock_cost'] += stock_cost
                warehouse_report['total_stock_qty'] += current_stock
                
                # Генерируем рекомендации по перемещениям
                
                # Для товаров без продаж с большими остатками - централизация
                if state_analysis['state'] == 'избыток' and ads == 0 and current_stock > 100:
                    parent = warehouse_info['parent']
                    if parent and warehouse_info['level'] > 1:  # Не для хаба
                        # Перемещаем избыток товаров без продаж в хаб
                        move_qty = min(state_analysis['excess'], current_stock * 0.7)
                        
                        if move_qty >= 20:
                            recommendation = {
                                'type': 'возврат_избытка',
                                'article': article,
                                'name': stock_item['name'],
                                'from_warehouse': warehouse_name,
                                'to_warehouse': parent,
                                'quantity': int(move_qty),
                                'reason': f'Централизация товара без продаж (избыток: {current_stock:.0f} шт)',
                                'priority': 'Низкий',
                                'from_stock': current_stock,
                                'to_stock': self._get_product_stock(parent, article, stock_data)['qty'] if self._get_product_stock(parent, article, stock_data) else 0,
                                'excess': move_qty,
                                'ads': 0
                            }
                            recommendations.append(recommendation)
                            warehouse_report['recommendations_out'].append(recommendation)
                
                elif state_analysis['state'] == 'дефицит' and state_analysis['deficit'] > 5:
                    # НЕДОСТАТОК - нужно взять из родительского склада
                    parent = warehouse_info['parent']
                    if parent:
                        # Проверяем наличие товара на родительском складе
                        parent_stock = self._get_product_stock(parent, article, stock_data)
                        if parent_stock and parent_stock['qty'] > 0:
                            # Проверяем состояние родительского склада
                            parent_type = self.warehouse_hierarchy[parent]['type']
                            parent_ads = sales_data.get(parent, {}).get(article, {}).get('ads', 0)
                            parent_state = self.analyze_warehouse_state(
                                parent_stock['qty'], parent_ads, parent_type
                            )
                            
                            # Можем взять если у родителя норма или избыток
                            if parent_state['state'] in ['норма', 'избыток']:
                                available_qty = min(
                                    state_analysis['deficit'],
                                    parent_state['excess'] if parent_state['state'] == 'избыток' 
                                    else parent_stock['qty'] * 0.2  # Максимум 20% от нормального остатка
                                )
                                
                                if available_qty >= 5:
                                    recommendation = {
                                        'type': 'пополнение_дефицита',
                                        'article': article,
                                        'name': stock_item['name'],
                                        'from_warehouse': parent,
                                        'to_warehouse': warehouse_name,
                                        'quantity': int(available_qty),
                                        'reason': f'Пополнение дефицита ({state_analysis["days_of_stock"]:.1f} дней остатка)',
                                        'priority': 'Высокий' if state_analysis['days_of_stock'] < 3 else 'Средний',
                                        'from_stock': parent_stock['qty'],
                                        'to_stock': current_stock,
                                        'deficit': state_analysis['deficit'],
                                        'ads': ads
                                    }
                                    recommendations.append(recommendation)
                                    warehouse_report['recommendations_in'].append(recommendation)
                
                elif state_analysis['state'] == 'избыток' and state_analysis['excess'] > 10:
                    # ИЗБЫТОК - нужно отдать в родительский склад или распределить
                    parent = warehouse_info['parent']
                    
                    if parent:
                        # Отдаем избыток родителю
                        move_qty = min(state_analysis['excess'] * 0.8, current_stock * 0.3)
                        
                        if move_qty >= 10:
                            recommendation = {
                                'type': 'возврат_избытка',
                                'article': article,
                                'name': stock_item['name'],
                                'from_warehouse': warehouse_name,
                                'to_warehouse': parent,
                                'quantity': int(move_qty),
                                'reason': f'Возврат избытка ({state_analysis["days_of_stock"]:.1f} дней остатка)',
                                'priority': 'Средний',
                                'from_stock': current_stock,
                                'to_stock': self._get_product_stock(parent, article, stock_data)['qty'] if self._get_product_stock(parent, article, stock_data) else 0,
                                'excess': state_analysis['excess'],
                                'ads': ads
                            }
                            recommendations.append(recommendation)
                            warehouse_report['recommendations_out'].append(recommendation)
                    
                    # Если это хаб или склад 2-го уровня, можем распределить детям
                    if warehouse_info['children'] and warehouse_info['level'] <= 2:
                        for child in warehouse_info['children']:
                            child_stock = self._get_product_stock(child, article, stock_data)
                            if child_stock:
                                child_ads = sales_data.get(child, {}).get(article, {}).get('ads', 0)
                                child_type = self.warehouse_hierarchy[child]['type']
                                child_state = self.analyze_warehouse_state(
                                    child_stock['qty'], child_ads, child_type
                                )
                                
                                if child_state['state'] == 'дефицит':
                                    move_qty = min(
                                        child_state['deficit'],
                                        state_analysis['excess'] * 0.5
                                    )
                                    
                                    if move_qty >= 5:
                                        recommendation = {
                                            'type': 'перераспределение',
                                            'article': article,
                                            'name': stock_item['name'],
                                            'from_warehouse': warehouse_name,
                                            'to_warehouse': child,
                                            'quantity': int(move_qty),
                                            'reason': f'Перераспределение избытка дочернему филиалу',
                                            'priority': 'Высокий',
                                            'from_stock': current_stock,
                                            'to_stock': child_stock['qty'],
                                            'deficit': child_state['deficit'],
                                            'ads': child_ads
                                        }
                                        recommendations.append(recommendation)
                                        warehouse_report['recommendations_out'].append(recommendation)
            
            warehouse_reports[warehouse_name] = warehouse_report
        
        # Добавляем ABC-анализ
        abc_analysis = self.calculate_abc_analysis(warehouse_reports)
        
        return {
            'recommendations': recommendations,
            'warehouse_reports': warehouse_reports,
            'abc_analysis': abc_analysis,
            'total_recommendations': len(recommendations),
            'high_priority': len([r for r in recommendations if r['priority'] == 'Высокий'])
        }
    
    def _get_warehouse_stock(self, warehouse_name: str, stock_data: Dict) -> Dict:
        """Получить остатки для конкретного склада"""
        stock_items = {}
        
        for warehouse in stock_data.get('ОстаткиПоСкладам', []):
            if warehouse['Склад'] == warehouse_name:
                for item in warehouse['Остатки']:
                    stock_items[item['Артикул']] = {
                        'name': item['Номенклатура'],
                        'qty': item['Количество'],
                        'cost': item['Стоимость'],
                        'category': item['ПутьКатегорий']
                    }
                break
        
        return stock_items
    
    def _get_product_stock(self, warehouse_name: str, article: str, stock_data: Dict) -> Optional[Dict]:
        """Получить остаток конкретного товара на складе"""
        warehouse_stock = self._get_warehouse_stock(warehouse_name, stock_data)
        return warehouse_stock.get(article)
    
    def calculate_abc_analysis(self, warehouse_reports: Dict) -> Dict:
        """Расчет ABC-анализа для каждого склада"""
        abc_results = {}
        
        for warehouse_name, report in warehouse_reports.items():
            products_with_revenue = []
            
            # Собираем товары с оборотом
            for product in report['products_analysis']:
                if product['ads'] > 0:  # Только товары с продажами
                    # Используем фактическую выручку из данных продаж
                    monthly_revenue = product.get('monthly_revenue', 0)
                    
                    # Для отладки: показываем как рассчитывается оборот
                    if monthly_revenue == 0:
                        # Фолбэк: рассчитываем через ADS и стоимость остатка
                        unit_cost = product['stock_cost'] / product['current_stock'] if product['current_stock'] > 0 else 0
                        monthly_revenue = product['ads'] * 30 * unit_cost
                        print(f"Отладка {product['article']}: ADS={product['ads']:.2f}, unit_cost={unit_cost:.2f}, monthly_revenue={monthly_revenue:.2f}")
                    else:
                        print(f"Отладка {product['article']}: фактическая выручка={monthly_revenue:.2f}")
                    
                    # Извлекаем последний элемент из пути категории
                    full_category_path = product.get('category', 'Без категории')
                    category_name = self._extract_last_category(full_category_path)
                    
                    products_with_revenue.append({
                        'article': product['article'],
                        'name': product['name'],
                        'category': category_name,
                        'current_stock': product['current_stock'],
                        'stock_cost': product['stock_cost'],
                        'ads': product['ads'],
                        'monthly_revenue': monthly_revenue,
                        'state': product['state']
                    })
            
            if not products_with_revenue:
                abc_results[warehouse_name] = {
                    'A': [], 'B': [], 'C': [],
                    'total_revenue': 0,
                    'A_revenue': 0, 'B_revenue': 0, 'C_revenue': 0,
                    'by_category': {}
                }
                continue
            
            # Сортируем по убыванию оборота
            products_with_revenue.sort(key=lambda x: x['monthly_revenue'], reverse=True)
            
            # Расчет ABC по правилу 80/15/5
            total_revenue = sum(p['monthly_revenue'] for p in products_with_revenue)
            
            cumulative_revenue = 0
            A_products, B_products, C_products = [], [], []
            
            for product in products_with_revenue:
                cumulative_revenue += product['monthly_revenue']
                cumulative_percent = (cumulative_revenue / total_revenue) * 100
                
                if cumulative_percent <= 80:
                    product['abc_category'] = 'A'
                    A_products.append(product)
                elif cumulative_percent <= 95:
                    product['abc_category'] = 'B'
                    B_products.append(product)
                else:
                    product['abc_category'] = 'C'
                    C_products.append(product)
            
            # Анализ по категориям
            by_category = self.calculate_abc_by_categories(products_with_revenue, total_revenue)
            
            abc_results[warehouse_name] = {
                'A': A_products,
                'B': B_products, 
                'C': C_products,
                'total_revenue': total_revenue,
                'A_revenue': sum(p['monthly_revenue'] for p in A_products),
                'B_revenue': sum(p['monthly_revenue'] for p in B_products),
                'C_revenue': sum(p['monthly_revenue'] for p in C_products),
                'warehouse_info': {
                    'type': report['type'],
                    'level': report['level'],
                    'city': report['city']
                },
                'by_category': by_category
            }
        
        return abc_results
    
    def calculate_abc_by_categories(self, products: List[Dict], total_revenue: float) -> Dict:
        """Расчет ABC-анализа по категориям товаров"""
        # Группируем по категориям
        categories = {}
        
        for product in products:
            category = product['category']
            if category not in categories:
                categories[category] = {
                    'products': [],
                    'total_revenue': 0,
                    'A_revenue': 0,
                    'B_revenue': 0,
                    'C_revenue': 0,
                    'A_count': 0,
                    'B_count': 0,
                    'C_count': 0
                }
            
            categories[category]['products'].append(product)
            categories[category]['total_revenue'] += product['monthly_revenue']
            
            # Подсчет по ABC категориям
            abc_cat = product.get('abc_category', 'C')
            categories[category][f'{abc_cat}_revenue'] += product['monthly_revenue']
            categories[category][f'{abc_cat}_count'] += 1
        
        # Добавляем проценты для каждой категории
        for cat_name, cat_data in categories.items():
            cat_total = cat_data['total_revenue']
            if cat_total > 0:
                cat_data['A_percent'] = (cat_data['A_revenue'] / cat_total) * 100
                cat_data['B_percent'] = (cat_data['B_revenue'] / cat_total) * 100
                cat_data['C_percent'] = (cat_data['C_revenue'] / cat_total) * 100
            else:
                cat_data['A_percent'] = 0
                cat_data['B_percent'] = 0
                cat_data['C_percent'] = 0
            
            # Процент от общего оборота склада
            cat_data['percent_of_total'] = (cat_total / total_revenue * 100) if total_revenue > 0 else 0
        
        return categories
    
    def _extract_last_category(self, category_path: str) -> str:
        """Извлекает последний элемент из пути категории"""
        if not category_path or category_path == 'Без категории':
            return 'Без категории'
        
        # Убираем слэши в начале и конце, разбиваем по слэшам
        clean_path = category_path.strip('/')
        if not clean_path:
            return 'Без категории'
        
        # Берем первый элемент (самый специфичный)
        parts = clean_path.split('/')
        return parts[0] if parts else 'Без категории'