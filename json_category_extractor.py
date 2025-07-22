"""
СИСТЕМА ИЗВЛЕЧЕНИЯ КАТЕГОРИЙ ИЗ JSON ФАЙЛОВ
Извлекает категории товаров из JSON файлов продаж и остатков
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re


class JSONCategoryExtractor:
    """
    Система извлечения и анализа категорий из JSON файлов продаж и остатков
    """
    
    def __init__(self):
        self.sales_data = []
        self.stock_data = {}
        self.category_mapping = {}
        self.category_hierarchy = {}
        self.abc_analysis = {}
        
    def load_sales_data(self, sales_file_path: str) -> bool:
        """Загружает данные продаж из JSON файла"""
        try:
            with open(sales_file_path, 'r', encoding='utf-8-sig') as f:
                self.sales_data = json.load(f)
            
            print(f"✅ Загружены данные продаж: {len(self.sales_data)} филиалов")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла продаж: {e}")
            return False
    
    def load_stock_data(self, stock_file_path: str) -> bool:
        """Загружает данные остатков из JSON файла"""
        try:
            with open(stock_file_path, 'r', encoding='utf-8-sig') as f:
                self.stock_data = json.load(f)
            
            warehouses_count = len(self.stock_data.get('ОстаткиПоСкладам', []))
            print(f"✅ Загружены данные остатков: {warehouses_count} складов")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла остатков: {e}")
            return False
    
    def extract_categories_from_path(self, category_path: str) -> Dict[str, str]:
        """
        Извлекает иерархию категорий из пути
        Пример: "Плинтус пластиковый 3м/Аксессуары для столешниц/Мебельная фурнитура/"
        
        Логика: берем первую (самую специфичную) категорию как основную
        """
        if not category_path:
            return {
                'category_1': 'Без категории',
                'category_2': None,
                'category_3': None,
                'main_category': 'Без категории'
            }
        
        # Убираем лишние слэши и разбиваем
        clean_path = category_path.strip('/')
        parts = [part.strip() for part in clean_path.split('/') if part.strip()]
        
        # Берем ПЕРВУЮ (самую специфичную) категорию как основную
        main_category = parts[0] if parts else 'Без категории'
        
        return {
            'category_1': parts[0] if len(parts) > 0 else 'Без категории',
            'category_2': parts[1] if len(parts) > 1 else None,
            'category_3': parts[2] if len(parts) > 2 else None,
            'main_category': main_category
        }
    
    def create_category_mapping(self):
        """Создает маппинг товаров к категориям на основе продаж и остатков"""
        print("🔄 Создание маппинга категорий...")
        
        # Собираем данные из продаж
        sales_mapping = {}
        total_sales_by_article = defaultdict(float)
        
        for branch in self.sales_data:
            for sale in branch.get('Продажи', []):
                article = sale.get('Артикул', '')
                nomenclature = sale.get('Номенклатура', '')
                category_path = sale.get('ПутьКатегорий', '')
                revenue = sale.get('Выручка', 0)
                
                if article and nomenclature:
                    categories = self.extract_categories_from_path(category_path)
                    
                    sales_mapping[article] = {
                        'nomenclature': nomenclature,
                        'categories': categories,
                        'category_path': category_path
                    }
                    
                    total_sales_by_article[article] += revenue
        
        # Собираем данные из остатков
        stock_mapping = {}
        
        for warehouse in self.stock_data.get('ОстаткиПоСкладам', []):
            for item in warehouse.get('Остатки', []):
                article = item.get('Артикул', '')
                nomenclature = item.get('Номенклатура', '')
                category_path = item.get('ПутьКатегорий', '')
                
                if article and nomenclature:
                    categories = self.extract_categories_from_path(category_path)
                    
                    stock_mapping[article] = {
                        'nomenclature': nomenclature,
                        'categories': categories,
                        'category_path': category_path
                    }
        
        # Объединяем данные
        all_articles = set(sales_mapping.keys()) | set(stock_mapping.keys())
        
        for article in all_articles:
            # Приоритет данным из продаж
            if article in sales_mapping:
                self.category_mapping[article] = sales_mapping[article].copy()
                self.category_mapping[article]['total_sales'] = total_sales_by_article[article]
            elif article in stock_mapping:
                self.category_mapping[article] = stock_mapping[article].copy()
                self.category_mapping[article]['total_sales'] = 0
        
        print(f"✅ Создан маппинг для {len(self.category_mapping)} товаров")
        
        # Создаем иерархию категорий
        self._create_category_hierarchy()
        
        return self.category_mapping
    
    def _create_category_hierarchy(self):
        """Создает иерархию категорий"""
        hierarchy = defaultdict(lambda: {'count': 0, 'subcategories': defaultdict(int), 'products': []})
        
        for article, data in self.category_mapping.items():
            main_cat = data['categories']['main_category']
            cat_1 = data['categories']['category_1']
            
            hierarchy[main_cat]['count'] += 1
            hierarchy[main_cat]['subcategories'][cat_1] += 1
            hierarchy[main_cat]['products'].append({
                'article': article,
                'nomenclature': data['nomenclature'],
                'total_sales': data['total_sales']
            })
        
        self.category_hierarchy = dict(hierarchy)
    
    def calculate_abc_analysis_by_branch(self) -> Dict[str, Dict[str, Any]]:
        """Рассчитывает ABC анализ по категориям для каждого филиала"""
        print("📊 Расчет ABC анализа по категориям и филиалам...")
        
        # Собираем продажи по филиалам и категориям
        branch_category_sales = defaultdict(lambda: defaultdict(list))
        
        for branch in self.sales_data:
            branch_name = branch.get('Филиал', 'Неизвестный филиал')
            
            for sale in branch.get('Продажи', []):
                article = sale.get('Артикул', '')
                nomenclature = sale.get('Номенклатура', '')
                category_path = sale.get('ПутьКатегорий', '')
                revenue = sale.get('Выручка', 0)
                
                if article and revenue > 0:
                    categories = self.extract_categories_from_path(category_path)
                    main_category = categories['main_category']
                    
                    branch_category_sales[branch_name][main_category].append({
                        'article': article,
                        'nomenclature': nomenclature,
                        'total_sales': revenue,
                        'category_path': category_path
                    })
        
        # ABC анализ для каждого филиала и категории
        abc_results_by_branch = {}
        
        for branch_name, categories_data in branch_category_sales.items():
            abc_results_by_branch[branch_name] = {}
            
            for category, products in categories_data.items():
                if not products:
                    continue
                
                # Сортируем по убыванию продаж
                products_sorted = sorted(products, key=lambda x: x['total_sales'], reverse=True)
                
                total_revenue = sum(p['total_sales'] for p in products_sorted)
                cumulative_revenue = 0
                
                abc_data = {'A': [], 'B': [], 'C': []}
                
                for product in products_sorted:
                    cumulative_revenue += product['total_sales']
                    cumulative_percent = (cumulative_revenue / total_revenue) * 100
                    
                    if cumulative_percent <= 80:
                        abc_class = 'A'
                    elif cumulative_percent <= 95:
                        abc_class = 'B'
                    else:
                        abc_class = 'C'
                    
                    product['abc_class'] = abc_class
                    product['cumulative_percent'] = cumulative_percent
                    abc_data[abc_class].append(product)
                
                abc_results_by_branch[branch_name][category] = {
                    'total_revenue': total_revenue,
                    'products_count': len(products_sorted),
                    'A': abc_data['A'],
                    'B': abc_data['B'],
                    'C': abc_data['C'],
                    'A_revenue': sum(p['total_sales'] for p in abc_data['A']),
                    'B_revenue': sum(p['total_sales'] for p in abc_data['B']),
                    'C_revenue': sum(p['total_sales'] for p in abc_data['C'])
                }
        
        return abc_results_by_branch
    
    def calculate_abc_analysis(self) -> Dict[str, Any]:
        """Рассчитывает общий ABC анализ по категориям (для совместимости)"""
        print("📊 Расчет общего ABC анализа по категориям...")
        
        # Группируем по основным категориям
        category_sales = defaultdict(list)
        
        for article, data in self.category_mapping.items():
            main_category = data['categories']['main_category']
            total_sales = data['total_sales']
            
            if total_sales > 0:  # Только товары с продажами
                category_sales[main_category].append({
                    'article': article,
                    'nomenclature': data['nomenclature'],
                    'total_sales': total_sales
                })
        
        # ABC анализ для каждой категории
        abc_results = {}
        
        for category, products in category_sales.items():
            if not products:
                continue
                
            # Сортируем по убыванию продаж
            products_sorted = sorted(products, key=lambda x: x['total_sales'], reverse=True)
            
            total_revenue = sum(p['total_sales'] for p in products_sorted)
            cumulative_revenue = 0
            
            abc_data = {'A': [], 'B': [], 'C': []}
            
            for product in products_sorted:
                cumulative_revenue += product['total_sales']
                cumulative_percent = (cumulative_revenue / total_revenue) * 100
                
                if cumulative_percent <= 80:
                    abc_class = 'A'
                elif cumulative_percent <= 95:
                    abc_class = 'B'
                else:
                    abc_class = 'C'
                
                product['abc_class'] = abc_class
                product['cumulative_percent'] = cumulative_percent
                abc_data[abc_class].append(product)
            
            abc_results[category] = {
                'total_revenue': total_revenue,
                'products_count': len(products_sorted),
                'A': abc_data['A'],
                'B': abc_data['B'],
                'C': abc_data['C'],
                'A_revenue': sum(p['total_sales'] for p in abc_data['A']),
                'B_revenue': sum(p['total_sales'] for p in abc_data['B']),
                'C_revenue': sum(p['total_sales'] for p in abc_data['C'])
            }
        
        self.abc_analysis = abc_results
        return abc_results
    
    def get_category_summary(self) -> Dict[str, Any]:
        """Получает сводку по категориям"""
        if not self.category_mapping:
            return {'error': 'Маппинг категорий не создан'}
        
        summary = {
            'total_products': len(self.category_mapping),
            'categories': {},
            'top_categories': [],
            'products_with_sales': 0,
            'total_revenue': 0
        }
        
        # Анализ по категориям
        category_stats = defaultdict(lambda: {
            'count': 0, 
            'revenue': 0, 
            'products_with_sales': 0,
            'subcategories': set()
        })
        
        for article, data in self.category_mapping.items():
            main_cat = data['categories']['main_category']
            revenue = data['total_sales']
            
            category_stats[main_cat]['count'] += 1
            category_stats[main_cat]['revenue'] += revenue
            
            if revenue > 0:
                category_stats[main_cat]['products_with_sales'] += 1
                summary['products_with_sales'] += 1
            
            summary['total_revenue'] += revenue
            
            # Подкатегории
            if data['categories']['category_1']:
                category_stats[main_cat]['subcategories'].add(data['categories']['category_1'])
        
        # Преобразуем в финальный вид
        for cat_name, stats in category_stats.items():
            summary['categories'][cat_name] = {
                'count': stats['count'],
                'revenue': stats['revenue'],
                'products_with_sales': stats['products_with_sales'],
                'subcategories_count': len(stats['subcategories']),
                'avg_revenue_per_product': stats['revenue'] / stats['count'] if stats['count'] > 0 else 0
            }
        
        # Топ категории по выручке
        summary['top_categories'] = sorted(
            summary['categories'].items(),
            key=lambda x: x[1]['revenue'],
            reverse=True
        )[:10]
        
        return summary
    
    def implement_sumproduct_logic_json(self, target_category: str, abc_class: str = None) -> Dict[str, Any]:
        """
        Реализует логику СУММЕСЛИМН для JSON данных
        Суммирует остатки товаров определенной категории и ABC класса
        """
        if not self.stock_data or not self.category_mapping:
            return {'error': 'Данные не загружены'}
        
        results = {
            'target_category': target_category,
            'target_abc_class': abc_class,
            'warehouse_results': {},
            'total_stock_value': 0,
            'total_stock_qty': 0,
            'matched_products': []
        }
        
        # Если нужен ABC анализ, рассчитываем его
        if abc_class and not self.abc_analysis:
            self.calculate_abc_analysis()
        
        # Проходим по всем складам
        for warehouse in self.stock_data.get('ОстаткиПоСкладам', []):
            warehouse_name = warehouse['Склад']
            warehouse_results = {
                'stock_value': 0,
                'stock_qty': 0,
                'products_count': 0,
                'products': []
            }
            
            # Проверяем остатки на складе
            for item in warehouse.get('Остатки', []):
                article = item.get('Артикул', '')
                
                if article in self.category_mapping:
                    product_data = self.category_mapping[article]
                    product_main_category = product_data['categories']['main_category']
                    
                    # Проверяем категорию
                    if product_main_category == target_category:
                        # Если нужен ABC класс, проверяем его
                        if abc_class:
                            if target_category in self.abc_analysis:
                                product_abc = None
                                # Ищем ABC класс товара
                                for abc_cls in ['A', 'B', 'C']:
                                    for abc_product in self.abc_analysis[target_category][abc_cls]:
                                        if abc_product['article'] == article:
                                            product_abc = abc_cls
                                            break
                                    if product_abc:
                                        break
                                
                                # Если ABC класс не совпадает, пропускаем
                                if product_abc != abc_class:
                                    continue
                        
                        # Добавляем к результатам
                        stock_value = item.get('Стоимость', 0)
                        stock_qty = item.get('Количество', 0)
                        
                        warehouse_results['stock_value'] += stock_value
                        warehouse_results['stock_qty'] += stock_qty
                        warehouse_results['products_count'] += 1
                        
                        warehouse_results['products'].append({
                            'article': article,
                            'nomenclature': item.get('Номенклатура', ''),
                            'stock_value': stock_value,
                            'stock_qty': stock_qty,
                            'category': product_main_category,
                            'abc_class': product_abc if abc_class else None
                        })
                        
                        results['total_stock_value'] += stock_value
                        results['total_stock_qty'] += stock_qty
            
            if warehouse_results['products_count'] > 0:
                results['warehouse_results'][warehouse_name] = warehouse_results
        
        # Собираем уникальные товары
        unique_products = set()
        for wh_data in results['warehouse_results'].values():
            for product in wh_data['products']:
                unique_products.add((product['article'], product['nomenclature']))
        
        results['unique_products_count'] = len(unique_products)
        results['warehouses_count'] = len(results['warehouse_results'])
        
        return results
    
    def export_to_csv(self, output_prefix: str = "category_analysis"):
        """Экспортирует анализ категорий в CSV"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # 1. Маппинг товаров с категориями
        mapping_data = []
        for article, data in self.category_mapping.items():
            mapping_data.append({
                'Артикул': article,
                'Номенклатура': data['nomenclature'],
                'Основная_категория': data['categories']['main_category'],
                'Категория_1': data['categories']['category_1'],
                'Категория_2': data['categories']['category_2'] or '',
                'Категория_3': data['categories']['category_3'] or '',
                'Путь_категорий': data.get('category_path', ''),
                'Общие_продажи': data['total_sales']
            })
        
        df_mapping = pd.DataFrame(mapping_data)
        mapping_file = f"{output_prefix}_mapping_{timestamp}.csv"
        df_mapping.to_csv(mapping_file, index=False, encoding='utf-8-sig')
        print(f"✅ Маппинг товаров экспортирован: {mapping_file}")
        
        # 2. Сводка по категориям
        summary = self.get_category_summary()
        if 'categories' in summary:
            summary_data = []
            for cat_name, cat_data in summary['categories'].items():
                summary_data.append({
                    'Категория': cat_name,
                    'Товаров': cat_data['count'],
                    'С_продажами': cat_data['products_with_sales'],
                    'Выручка': cat_data['revenue'],
                    'Средняя_выручка': cat_data['avg_revenue_per_product'],
                    'Подкатегорий': cat_data['subcategories_count']
                })
            
            df_summary = pd.DataFrame(summary_data)
            summary_file = f"{output_prefix}_summary_{timestamp}.csv"
            df_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
            print(f"✅ Сводка по категориям экспортирована: {summary_file}")
        
        # 3. ABC анализ
        if self.abc_analysis:
            abc_data = []
            for category, abc_info in self.abc_analysis.items():
                abc_data.append({
                    'Категория': category,
                    'Товаров': abc_info['products_count'],
                    'Общая_выручка': abc_info['total_revenue'],
                    'A_товаров': len(abc_info['A']),
                    'A_выручка': abc_info['A_revenue'],
                    'A_процент': (abc_info['A_revenue'] / abc_info['total_revenue'] * 100) if abc_info['total_revenue'] > 0 else 0,
                    'B_товаров': len(abc_info['B']),
                    'B_выручка': abc_info['B_revenue'],
                    'B_процент': (abc_info['B_revenue'] / abc_info['total_revenue'] * 100) if abc_info['total_revenue'] > 0 else 0,
                    'C_товаров': len(abc_info['C']),
                    'C_выручка': abc_info['C_revenue'],
                    'C_процент': (abc_info['C_revenue'] / abc_info['total_revenue'] * 100) if abc_info['total_revenue'] > 0 else 0
                })
            
            df_abc = pd.DataFrame(abc_data)
            abc_file = f"{output_prefix}_abc_{timestamp}.csv"
            df_abc.to_csv(abc_file, index=False, encoding='utf-8-sig')
            print(f"✅ ABC анализ экспортирован: {abc_file}")
        
        return {
            'mapping_file': mapping_file,
            'summary_file': summary_file if 'summary_file' in locals() else None,
            'abc_file': abc_file if 'abc_file' in locals() else None
        }


def test_json_category_extraction():
    """Тестирование извлечения категорий из JSON файлов"""
    print("🧪 ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ КАТЕГОРИЙ ИЗ JSON")
    print("=" * 50)
    
    extractor = JSONCategoryExtractor()
    
    # Загружаем данные
    sales_path = '/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30.json'
    stock_path = '/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30 (4).json'
    
    if extractor.load_sales_data(sales_path) and extractor.load_stock_data(stock_path):
        
        # Создаем маппинг категорий
        extractor.create_category_mapping()
        
        # Получаем сводку
        summary = extractor.get_category_summary()
        
        print(f"\n📊 СВОДКА ПО КАТЕГОРИЯМ")
        print("-" * 30)
        print(f"Всего товаров: {summary['total_products']}")
        print(f"С продажами: {summary['products_with_sales']}")
        print(f"Общая выручка: {summary['total_revenue']:,.0f} ₸")
        print(f"Категорий: {len(summary['categories'])}")
        
        print(f"\n🏆 ТОП-5 КАТЕГОРИЙ ПО ВЫРУЧКЕ:")
        for i, (cat_name, cat_data) in enumerate(summary['top_categories'][:5], 1):
            print(f"{i}. {cat_name}: {cat_data['revenue']:,.0f} ₸ ({cat_data['count']} товаров)")
        
        # ABC анализ
        print(f"\n📈 ABC АНАЛИЗ")
        print("-" * 20)
        abc_results = extractor.calculate_abc_analysis()
        
        print(f"Найдено категорий: {len(abc_results)}")
        for category, abc_data in list(abc_results.items())[:5]:  # Показываем первые 5
            print(f"\n{category}:")
            print(f"  A: {len(abc_data['A'])} товаров ({abc_data['A_revenue']:,.0f} ₸)")
            print(f"  B: {len(abc_data['B'])} товаров ({abc_data['B_revenue']:,.0f} ₸)")
            print(f"  C: {len(abc_data['C'])} товаров ({abc_data['C_revenue']:,.0f} ₸)")
        
        # ABC анализ по филиалам
        print(f"\n📈 ABC АНАЛИЗ ПО ФИЛИАЛАМ")
        print("-" * 30)
        abc_by_branch = extractor.calculate_abc_analysis_by_branch()
        
        for branch_name, branch_abc in list(abc_by_branch.items())[:2]:  # Показываем первые 2 филиала
            print(f"\n{branch_name}:")
            for category, abc_data in list(branch_abc.items())[:3]:  # Первые 3 категории филиала
                print(f"  {category}: A={len(abc_data['A'])}, B={len(abc_data['B'])}, C={len(abc_data['C'])}")
        
        # Тест формулы СУММЕСЛИМН
        print(f"\n🔍 ТЕСТ ФОРМУЛЫ СУММЕСЛИМН")
        print("-" * 30)
        
        # Берем первую категорию с ABC анализом
        if abc_results:
            test_category = list(abc_results.keys())[0]
            
            # Тестируем для класса A
            result = extractor.implement_sumproduct_logic_json(test_category, 'A')
            
            print(f"Категория: {result['target_category']}")
            print(f"ABC класс: {result['target_abc_class']}")
            print(f"Уникальных товаров: {result['unique_products_count']}")
            print(f"Складов с остатками: {result['warehouses_count']}")
            print(f"Общая стоимость: {result['total_stock_value']:,.0f} ₸")
            print(f"Общее количество: {result['total_stock_qty']:,.0f}")
        
        # Экспорт
        print(f"\n💾 ЭКСПОРТ ДАННЫХ")
        print("-" * 20)
        files = extractor.export_to_csv("json_category_analysis")
        
        return extractor
    
    else:
        print("❌ Не удалось загрузить данные")
        return None


if __name__ == '__main__':
    test_extractor = test_json_category_extraction()