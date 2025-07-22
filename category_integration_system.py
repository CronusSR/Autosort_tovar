"""
СИСТЕМА ИНТЕГРАЦИИ КАТЕГОРИЙ В МЕЖФИЛИАЛЬНЫЕ ПЕРЕМЕЩЕНИЯ
Реализует логику формулы СУММЕСЛИМН для работы с категориями товаров
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json


class CategoryIntegrationSystem:
    """
    Система интеграции категорий товаров в анализ межфилиальных перемещений
    """
    
    def __init__(self):
        self.turnover_data = None
        self.category_mapping = {}
        self.abc_analysis_by_warehouse = {}
        
    def load_turnover_data(self, excel_file_path: str):
        """
        Загружает данные оборачиваемости из Excel файла
        """
        try:
            # Загружаем все листы
            xl_file = pd.ExcelFile(excel_file_path)
            
            self.turnover_data = {}
            
            # Лист "ИЗ ОСНОВЫ НОМЕНКЛАТУР" - основная номенклатура с категориями
            df_nomenclature = pd.read_excel(excel_file_path, sheet_name='ИЗ ОСНОВЫ НОМЕНКЛАТУР')
            self.turnover_data['nomenclature'] = df_nomenclature
            
            # Лист "ОСТАТКИ" - остатки по складам
            df_stock = pd.read_excel(excel_file_path, sheet_name='ОСТАТКИ')
            self.turnover_data['stock'] = df_stock
            
            # Лист "ABC ПО СКЛАДАМ" - ABC анализ по складам
            df_abc_warehouses = pd.read_excel(excel_file_path, sheet_name='ABC ПО СКЛАДАМ')
            self.turnover_data['abc_warehouses'] = df_abc_warehouses
            
            # Лист "ОБОРАЧИВ ПО СЕТИ+ABC" - общий ABC анализ
            df_abc_network = pd.read_excel(excel_file_path, sheet_name='ОБОРАЧИВ ПО СЕТИ+ABC')
            self.turnover_data['abc_network'] = df_abc_network
            
            print(f"✅ Загружены данные оборачиваемости:")
            print(f"   - Номенклатура: {len(df_nomenclature)} записей")
            print(f"   - Остатки: {len(df_stock)} записей")
            print(f"   - ABC по складам: {len(df_abc_warehouses)} записей")
            print(f"   - ABC по сети: {len(df_abc_network)} записей")
            
            # Создаем маппинг категорий
            self._create_category_mapping()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных оборачиваемости: {e}")
            return False
    
    def _create_category_mapping(self):
        """
        Создает маппинг категорий из листа номенклатуры
        """
        if 'nomenclature' not in self.turnover_data:
            return
            
        df = self.turnover_data['nomenclature']
        
        # Очищаем данные от заголовков
        df_clean = df[df['Unnamed: 7'] != 'abc'].copy()
        df_clean = df_clean.dropna(subset=['Номенклатура'])
        
        self.category_mapping = {}
        
        for _, row in df_clean.iterrows():
            nomenclature = row['Номенклатура']
            category = row['КАТЕГОРИЯ']
            subcat = row['КАТ-2'] 
            abc_class = row['Unnamed: 7']  # ABC класс
            
            if pd.notna(nomenclature) and pd.notna(category):
                self.category_mapping[nomenclature] = {
                    'category': category,
                    'subcategory': subcat if pd.notna(subcat) else None,
                    'abc_class': abc_class if pd.notna(abc_class) else 'C'
                }
        
        print(f"✅ Создан маппинг для {len(self.category_mapping)} товаров")
    
    def implement_sumproduct_logic(self, target_category: str, target_abc_class: str, 
                                 warehouse_name: str = None) -> Dict[str, Any]:
        """
        Реализует логику формулы СУММЕСЛИМН:
        =СУММЕСЛИМН(ОСТАТКИ!AD:AD;ОСТАТКИ!Q:Q;"ABC ПО СКЛАДАМ"!A:A;ОСТАТКИ!S:S;"ABC ПО СКЛАДАМ"!C$3)
        
        Суммирует остатки товаров:
        - где категория (Q) = target_category
        - и ABC класс (S) = target_abc_class
        """
        if 'stock' not in self.turnover_data:
            return {'error': 'Данные остатков не загружены'}
        
        df_stock = self.turnover_data['stock']
        
        # Находим строку с заголовками
        header_row = None
        for i in range(len(df_stock)):
            if pd.notna(df_stock.iloc[i, 0]) and 'Номенклатура' in str(df_stock.iloc[i, 0]):
                header_row = i
                break
        
        if header_row is None:
            return {'error': 'Не найдены заголовки в данных остатков'}
        
        # Читаем данные с правильными заголовками
        df_clean = df_stock.iloc[header_row+1:].copy()
        df_clean.columns = df_stock.iloc[header_row].values
        df_clean = df_clean.dropna(subset=['Номенклатура']).reset_index(drop=True)
        
        # Результаты
        results = {
            'target_category': target_category,
            'target_abc_class': target_abc_class,
            'warehouse_results': {},
            'total_stock_value': 0,
            'total_stock_qty': 0,
            'matched_products': []
        }
        
        # Проходим по товарам и находим совпадения
        for _, row in df_clean.iterrows():
            nomenclature = row['Номенклатура']
            
            # Ищем категорию и ABC класс товара
            if nomenclature in self.category_mapping:
                product_info = self.category_mapping[nomenclature]
                
                # Проверяем условия формулы
                if (product_info['category'] == target_category and 
                    product_info['abc_class'] == target_abc_class):
                    
                    # Считаем остатки по всем складам для этого товара
                    for col in df_clean.columns:
                        if col not in ['Номенклатура']:
                            try:
                                col_value = row[col]
                                if pd.notna(col_value):
                                    stock_value = float(col_value)
                                    if stock_value > 0:
                                        if col not in results['warehouse_results']:
                                            results['warehouse_results'][col] = {
                                                'stock_value': 0,
                                                'products_count': 0,
                                                'products': []
                                            }
                                        
                                        results['warehouse_results'][col]['stock_value'] += stock_value
                                        results['warehouse_results'][col]['products_count'] += 1
                                        results['warehouse_results'][col]['products'].append({
                                            'nomenclature': nomenclature,
                                            'stock_value': stock_value,
                                            'category': product_info['category'],
                                            'subcategory': product_info['subcategory'],
                                            'abc_class': product_info['abc_class']
                                        })
                                        
                                        results['total_stock_value'] += stock_value
                            except (ValueError, TypeError):
                                continue
                    
                    results['matched_products'].append({
                        'nomenclature': nomenclature,
                        'category': product_info['category'],
                        'subcategory': product_info['subcategory'],
                        'abc_class': product_info['abc_class']
                    })
        
        results['matched_products_count'] = len(results['matched_products'])
        results['warehouses_count'] = len(results['warehouse_results'])
        
        return results
    
    def get_category_abc_summary(self) -> Dict[str, Any]:
        """
        Получает сводку по всем категориям и ABC классам
        """
        if not self.category_mapping:
            return {'error': 'Маппинг категорий не создан'}
        
        summary = {
            'categories': {},
            'abc_classes': {'A': 0, 'B': 0, 'C': 0},
            'total_products': len(self.category_mapping)
        }
        
        for product, info in self.category_mapping.items():
            category = info['category']
            abc_class = info['abc_class']
            
            # Подсчет по категориям
            if category not in summary['categories']:
                summary['categories'][category] = {
                    'total': 0,
                    'A': 0, 'B': 0, 'C': 0,
                    'subcategories': {}
                }
            
            summary['categories'][category]['total'] += 1
            summary['categories'][category][abc_class] += 1
            
            # Подсчет подкатегорий
            subcat = info['subcategory']
            if subcat and subcat not in summary['categories'][category]['subcategories']:
                summary['categories'][category]['subcategories'][subcat] = {
                    'total': 0, 'A': 0, 'B': 0, 'C': 0
                }
            
            if subcat:
                summary['categories'][category]['subcategories'][subcat]['total'] += 1
                summary['categories'][category]['subcategories'][subcat][abc_class] += 1
            
            # Общий подсчет ABC
            summary['abc_classes'][abc_class] += 1
        
        return summary
    
    def calculate_warehouse_abc_analysis(self, warehouse_name: str = None) -> Dict[str, Any]:
        """
        Рассчитывает ABC анализ для конкретного склада или всех складов
        """
        results = {}
        
        # Получаем все уникальные категории
        categories = set(info['category'] for info in self.category_mapping.values())
        
        for category in categories:
            category_results = {}
            
            for abc_class in ['A', 'B', 'C']:
                formula_result = self.implement_sumproduct_logic(category, abc_class, warehouse_name)
                
                if 'error' not in formula_result:
                    category_results[abc_class] = {
                        'total_stock_value': formula_result['total_stock_value'],
                        'products_count': formula_result['matched_products_count'],
                        'warehouses': formula_result['warehouse_results']
                    }
                else:
                    category_results[abc_class] = {'error': formula_result['error']}
            
            # Подсчитываем итоги по категории
            total_value = sum(
                category_results[abc]['total_stock_value'] 
                for abc in ['A', 'B', 'C'] 
                if 'total_stock_value' in category_results[abc]
            )
            
            total_products = sum(
                category_results[abc]['products_count'] 
                for abc in ['A', 'B', 'C'] 
                if 'products_count' in category_results[abc]
            )
            
            category_results['TOTAL'] = {
                'total_stock_value': total_value,
                'products_count': total_products
            }
            
            # Рассчитываем проценты
            for abc_class in ['A', 'B', 'C']:
                if 'total_stock_value' in category_results[abc_class] and total_value > 0:
                    category_results[abc_class]['percentage'] = (
                        category_results[abc_class]['total_stock_value'] / total_value * 100
                    )
            
            results[category] = category_results
        
        return results
    
    def integrate_with_movement_system(self, stock_data: Dict, sales_data: Dict) -> Dict[str, Any]:
        """
        Интегрирует категории в систему межфилиальных перемещений
        """
        enhanced_data = {
            'stock_with_categories': {},
            'sales_with_categories': {},
            'category_analysis': {},
            'movement_recommendations_by_category': {}
        }
        
        # Обогащаем данные остатков категориями
        if 'ОстаткиПоСкладам' in stock_data:
            for warehouse in stock_data['ОстаткиПоСкладам']:
                wh_name = warehouse['Склад']
                enhanced_data['stock_with_categories'][wh_name] = []
                
                for item in warehouse['Остатки']:
                    nomenclature = item['Номенклатура']
                    enhanced_item = item.copy()
                    
                    # Добавляем информацию о категории
                    if nomenclature in self.category_mapping:
                        enhanced_item.update(self.category_mapping[nomenclature])
                    else:
                        enhanced_item.update({
                            'category': 'Без категории',
                            'subcategory': None,
                            'abc_class': 'C'
                        })
                    
                    enhanced_data['stock_with_categories'][wh_name].append(enhanced_item)
        
        # Обогащаем данные продаж категориями
        for branch_name, branch_sales in sales_data.items():
            if branch_name == '_category_avg_ads':
                continue
                
            enhanced_data['sales_with_categories'][branch_name] = {}
            
            for article, sale_info in branch_sales.items():
                if article == '_category_avg_ads':
                    continue
                
                enhanced_sale = sale_info.copy()
                
                # Ищем товар в маппинге категорий
                found_in_mapping = False
                for nomenclature, cat_info in self.category_mapping.items():
                    if article in nomenclature or nomenclature in article:
                        enhanced_sale.update(cat_info)
                        found_in_mapping = True
                        break
                
                if not found_in_mapping:
                    enhanced_sale.update({
                        'category': enhanced_sale.get('category', 'Без категории'),
                        'subcategory': None,
                        'abc_class': 'C'
                    })
                
                enhanced_data['sales_with_categories'][branch_name][article] = enhanced_sale
        
        # Анализ по категориям
        enhanced_data['category_analysis'] = self.get_category_abc_summary()
        
        # ABC анализ по складам
        enhanced_data['abc_analysis_by_warehouses'] = self.calculate_warehouse_abc_analysis()
        
        return enhanced_data

    def export_category_data_to_csv(self, output_path: str = None):
        """
        Экспортирует данные категорий в CSV для анализа
        """
        if not output_path:
            from datetime import datetime
            output_path = f"category_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        # Создаем DataFrame с данными категорий
        export_data = []
        
        for nomenclature, info in self.category_mapping.items():
            export_data.append({
                'Номенклатура': nomenclature,
                'Категория': info['category'],
                'Подкатегория': info['subcategory'] or '',
                'ABC класс': info['abc_class']
            })
        
        df = pd.DataFrame(export_data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ Данные категорий экспортированы в {output_path}")
        return output_path


def test_category_integration():
    """
    Тестирование системы интеграции категорий
    """
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ИНТЕГРАЦИИ КАТЕГОРИЙ")
    print("=" * 50)
    
    # Инициализация
    system = CategoryIntegrationSystem()
    
    # Загрузка данных
    excel_path = '/mnt/f/Работа-Никита/Autosort_tovar/ОБОРАЧИВАЕМОСТЬ 10.07.2025.xlsx'
    
    if system.load_turnover_data(excel_path):
        print("\n📊 АНАЛИЗ КАТЕГОРИЙ")
        print("-" * 30)
        
        # Получаем сводку по категориям
        summary = system.get_category_abc_summary()
        
        if 'error' not in summary:
            print(f"Всего товаров: {summary['total_products']}")
            print(f"ABC классы: A={summary['abc_classes']['A']}, B={summary['abc_classes']['B']}, C={summary['abc_classes']['C']}")
            print(f"Категорий: {len(summary['categories'])}")
            
            print("\nТоп-5 категорий по количеству товаров:")
            sorted_categories = sorted(
                summary['categories'].items(), 
                key=lambda x: x[1]['total'], 
                reverse=True
            )
            
            for i, (cat_name, cat_data) in enumerate(sorted_categories[:5], 1):
                print(f"{i}. {cat_name}: {cat_data['total']} товаров (A={cat_data['A']}, B={cat_data['B']}, C={cat_data['C']})")
        
        print("\n🔍 ТЕСТ ФОРМУЛЫ СУММЕСЛИМН")
        print("-" * 30)
        
        # Тестируем формулу для кромочных материалов категории A
        test_result = system.implement_sumproduct_logic(
            target_category='Кромочные материалы',
            target_abc_class='A'
        )
        
        if 'error' not in test_result:
            print(f"Категория: {test_result['target_category']}")
            print(f"ABC класс: {test_result['target_abc_class']}")
            print(f"Найдено товаров: {test_result['matched_products_count']}")
            print(f"Складов с остатками: {test_result['warehouses_count']}")
            print(f"Общая стоимость остатков: {test_result['total_stock_value']:,.0f}")
            
            # Показываем топ-3 склада по стоимости
            warehouse_sorted = sorted(
                test_result['warehouse_results'].items(),
                key=lambda x: x[1]['stock_value'],
                reverse=True
            )
            
            print("\nТоп-3 склада по стоимости остатков:")
            for i, (wh_name, wh_data) in enumerate(warehouse_sorted[:3], 1):
                print(f"{i}. {wh_name}: {wh_data['stock_value']:,.0f} ({wh_data['products_count']} товаров)")
        else:
            print(f"Ошибка: {test_result['error']}")
            
        print("\n💾 ЭКСПОРТ ДАННЫХ")
        print("-" * 20)
        system.export_category_data_to_csv()
        
        return system
    
    else:
        print("❌ Не удалось загрузить данные")
        return None


if __name__ == '__main__':
    test_system = test_category_integration()