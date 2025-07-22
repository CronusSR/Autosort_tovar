"""
ГЕНЕРАТОР ОТЧЕТОВ ПО ОБОРАЧИВАЕМОСТИ СКЛАДОВ
Создает отчеты в формате: 
- КАТЕГОРИИ | ТОТ ПРОД | ТОТ ОСТ | ОБОР ДН
- КАТЕГОРИИ | ПРОДАЖА ПО Себ.Ст | ОСТАТОК по Себ.Ст. | ОБОРАЧИВАЕМОСТЬ (дн.)
"""

import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional
from collections import defaultdict
from json_category_extractor import JSONCategoryExtractor


class TurnoverReportGenerator:
    """
    Генератор отчетов по оборачиваемости складов
    """
    
    def __init__(self):
        self.category_extractor = JSONCategoryExtractor()
        self.turnover_reports = {}
    
    def create_safe_filename(self, name: str, max_length: int = 50) -> str:
        """Создает безопасное имя файла, удаляя недопустимые символы"""
        # Удаляем недопустимые символы для файловой системы
        safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Заменяем кавычки и специальные символы
        safe_name = safe_name.replace('"', '').replace("'", '').replace('№', 'N')
        # Заменяем пробелы на подчеркивания
        safe_name = re.sub(r'\s+', '_', safe_name)
        # Удаляем повторяющиеся подчеркивания
        safe_name = re.sub(r'_+', '_', safe_name)
        # Убираем подчеркивания в начале и конце
        safe_name = safe_name.strip('_')
        # Ограничиваем длину
        return safe_name[:max_length]
        
    def load_data(self, sales_file_path: str, stock_file_path: str) -> bool:
        """Загружает данные продаж и остатков"""
        try:
            # Загружаем данные через category_extractor
            sales_loaded = self.category_extractor.load_sales_data(sales_file_path)
            stock_loaded = self.category_extractor.load_stock_data(stock_file_path)
            
            if sales_loaded and stock_loaded:
                self.category_extractor.create_category_mapping()
                print("✅ Данные загружены успешно")
                return True
            else:
                print("❌ Ошибка загрузки данных")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False
    
    def calculate_warehouse_turnover_report(self, warehouse_name: str) -> Dict[str, Any]:
        """
        Рассчитывает отчет по оборачиваемости для конкретного склада
        """
        print(f"📊 Расчет оборачиваемости для склада: {warehouse_name}")
        
        # Собираем продажи по категориям для склада
        category_sales = defaultdict(float)
        category_sales_cost = defaultdict(float)  # Продажи по себестоимости
        
        for branch in self.category_extractor.sales_data:
            branch_name = branch.get('Филиал', '')
            
            # Проверяем, относится ли этот филиал к складу
            if warehouse_name.lower() in branch_name.lower() or branch_name.lower() in warehouse_name.lower():
                
                for sale in branch.get('Продажи', []):
                    article = sale.get('Артикул', '')
                    revenue = sale.get('Выручка', 0)
                    cost = sale.get('Себестоимость', 0)
                    category_path = sale.get('ПутьКатегорий', '')
                    
                    if article and revenue > 0:
                        categories = self.category_extractor.extract_categories_from_path(category_path)
                        main_category = categories['main_category']
                        category_sales[main_category] += revenue
                        category_sales_cost[main_category] += cost
        
        # Собираем остатки по категориям для склада
        category_stock = defaultdict(float)
        
        for warehouse in self.category_extractor.stock_data.get('ОстаткиПоСкладам', []):
            wh_name = warehouse.get('Склад', '')
            
            # Проверяем, это ли нужный склад
            if warehouse_name.lower() in wh_name.lower() or wh_name.lower() in warehouse_name.lower():
                
                for item in warehouse.get('Остатки', []):
                    article = item.get('Артикул', '')
                    stock_cost = item.get('Стоимость', 0)
                    category_path = item.get('ПутьКатегорий', '')
                    
                    if article and stock_cost > 0:
                        categories = self.category_extractor.extract_categories_from_path(category_path)
                        main_category = categories['main_category']
                        category_stock[main_category] += stock_cost
        
        # Рассчитываем оборачиваемость
        turnover_data = []
        total_sales = 0
        total_stock = 0
        total_sales_cost = 0
        
        # Объединяем все категории
        all_categories = set(category_sales.keys()) | set(category_stock.keys())
        
        for category in sorted(all_categories):
            cat_sales = category_sales.get(category, 0)
            cat_stock = category_stock.get(category, 0)
            cat_sales_cost = category_sales_cost.get(category, 0)
            
            # Рассчитываем дни оборачиваемости
            # ОБОР ДН = (Остаток * Период) / Продажи (по себестоимости)
            # Период = 30 дней (месяц)
            if cat_sales_cost > 0:
                turnover_days = (cat_stock * 30) / cat_sales_cost
            else:
                turnover_days = 0 if cat_stock == 0 else 9999  # Бесконечность для товаров без продаж
            
            turnover_data.append({
                'КАТЕГОРИЯ': category,
                'ТОТ_ПРОД': cat_sales,
                'ТОТ_ОСТ': cat_stock,
                'ОБОР_ДН': turnover_days,
                'ПРОДАЖА_СЕБЕСТ': cat_sales_cost,
                'ОСТАТОК_СЕБЕСТ': cat_stock
            })
            
            total_sales += cat_sales
            total_stock += cat_stock
            total_sales_cost += cat_sales_cost
        
        # Добавляем итоговую строку
        if total_sales_cost > 0:
            total_turnover_days = (total_stock * 30) / total_sales_cost
        else:
            total_turnover_days = 0
        
        turnover_data.append({
            'КАТЕГОРИЯ': 'ИТОГО:',
            'ТОТ_ПРОД': total_sales,
            'ТОТ_ОСТ': total_stock,
            'ОБОР_ДН': total_turnover_days,
            'ПРОДАЖА_СЕБЕСТ': total_sales_cost,
            'ОСТАТОК_СЕБЕСТ': total_stock
        })
        
        # Сортируем по убыванию продаж по себестоимости (кроме итоговой строки)
        turnover_data_sorted = sorted(turnover_data[:-1], key=lambda x: x['ПРОДАЖА_СЕБЕСТ'], reverse=True)
        turnover_data_sorted.append(turnover_data[-1])  # Добавляем итог в конец
        
        return {
            'warehouse_name': warehouse_name,
            'data': turnover_data_sorted,
            'total_sales': total_sales,
            'total_stock': total_stock,
            'avg_turnover_days': total_turnover_days,
            'categories_count': len(all_categories)
        }
    
    def generate_all_warehouses_reports(self) -> Dict[str, Any]:
        """Генерирует отчеты для всех складов"""
        print("📊 Генерация отчетов по всем складам...")
        
        # Получаем список всех складов
        warehouses = []
        for warehouse in self.category_extractor.stock_data.get('ОстаткиПоСкладам', []):
            warehouses.append(warehouse.get('Склад', ''))
        
        all_reports = {}
        
        for warehouse_name in warehouses:
            if warehouse_name:
                try:
                    report = self.calculate_warehouse_turnover_report(warehouse_name)
                    all_reports[warehouse_name] = report
                except Exception as e:
                    print(f"❌ Ошибка для склада {warehouse_name}: {e}")
        
        return all_reports
    
    def format_turnover_report(self, report_data: Dict[str, Any]) -> str:
        """Форматирует отчет в текстовом виде"""
        warehouse_name = report_data['warehouse_name']
        data = report_data['data']
        
        output = []
        output.append(f"📊 ОТЧЕТ ПО ОБОРАЧИВАЕМОСТИ: {warehouse_name}")
        output.append("=" * 80)
        output.append("")
        output.append(f"{'КАТЕГОРИИ':<40} {'ТОТ ПРОД':>15} {'ТОТ ОСТ':>15} {'ОБОР ДН':>10}")
        output.append("-" * 80)
        
        for item in data:
            category = item['КАТЕГОРИЯ']
            if len(category) > 38:
                category = category[:38] + ".."
            
            tot_prod = f"{item['ТОТ_ПРОД']:,.0f}"
            tot_ost = f"{item['ТОТ_ОСТ']:,.0f}"
            
            if item['ОБОР_ДН'] == 9999:
                obor_dn = "∞"
            else:
                obor_dn = f"{item['ОБОР_ДН']:.0f}"
            
            # Выделяем итоговую строку
            if category == 'ИТОГО:':
                output.append("-" * 80)
            
            output.append(f"{category:<40} {tot_prod:>15} {tot_ost:>15} {obor_dn:>10}")
        
        output.append("")
        output.append(f"Категорий: {report_data['categories_count']}")
        output.append(f"Средняя оборачиваемость: {report_data['avg_turnover_days']:.0f} дней")
        output.append("")
        
        return "\n".join(output)
    
    def export_to_xlsx(self, reports: Dict[str, Any], output_prefix: str = "turnover_reports") -> List[str]:
        """Экспортирует отчеты в XLSX файлы"""
        from datetime import datetime
        import os
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Создаем папку Downloads если не существует
        downloads_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads_path):
            downloads_path = os.getcwd()  # Используем текущую папку если Downloads не найдена
        
        exported_files = []
        
        for warehouse_name, report_data in reports.items():
            # Создаем безопасное имя файла
            safe_name = self.create_safe_filename(warehouse_name)
            
            # Создаем DataFrame
            df = pd.DataFrame(report_data['data'])
            
            # Форматируем числа (оставляем как числа для Excel)
            df_export = df[['КАТЕГОРИЯ', 'ТОТ_ПРОД', 'ТОТ_ОСТ', 'ОБОР_ДН']].copy()
            
            # Заменяем бесконечность на текст для Excel
            df_export['ОБОР_ДН'] = df_export['ОБОР_ДН'].apply(lambda x: "∞" if x == 9999 else x)
            
            # Переименовываем столбцы
            df_export.columns = ['КАТЕГОРИЯ', 'ТОТ_ПРОД', 'ТОТ_ОСТ', 'ОБОР_ДН']
            
            # Экспортируем в Downloads
            filename = f"{output_prefix}_{safe_name}_{timestamp}.xlsx"
            filepath = os.path.join(downloads_path, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_export.to_excel(writer, sheet_name='Оборачиваемость', index=False)
                
                # Форматируем Excel файл
                workbook = writer.book
                worksheet = writer.sheets['Оборачиваемость']
                
                # Автоширина колонок
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            exported_files.append(filepath)
            print(f"✅ Экспортирован отчет: {filepath}")
        
        return exported_files
    
    def generate_cost_based_turnover_report(self, warehouse_name: str) -> Dict[str, Any]:
        """
        Генерирует расширенный отчет с себестоимостью и процентами
        Формат: КАТЕГОРИИ | ПРОДАЖА ПО Себ.Ст | % | ОСТАТОК по Себ.Ст. | % | ОБОРАЧИВАЕМОСТЬ (дн.)
        """
        basic_report = self.calculate_warehouse_turnover_report(warehouse_name)
        
        if not basic_report or not basic_report['data']:
            return {}
        
        # Данные без итоговой строки
        data_without_total = basic_report['data'][:-1]
        total_row = basic_report['data'][-1]
        
        # Общие суммы для расчета процентов
        total_sales_cost = total_row['ПРОДАЖА_СЕБЕСТ']
        total_stock_cost = total_row['ОСТАТОК_СЕБЕСТ']
        
        # Расширенные данные с процентами
        enhanced_data = []
        
        for item in data_without_total:
            sales_cost = item['ПРОДАЖА_СЕБЕСТ']
            stock_cost = item['ОСТАТОК_СЕБЕСТ']
            
            # Рассчитываем проценты
            sales_percent = (sales_cost / total_sales_cost * 100) if total_sales_cost > 0 else 0
            stock_percent = (stock_cost / total_stock_cost * 100) if total_stock_cost > 0 else 0
            
            enhanced_data.append({
                'КАТЕГОРИЯ': item['КАТЕГОРИЯ'],
                'ПРОДАЖА_СЕБЕСТ': sales_cost,
                'ПРОДАЖА_ПРОЦЕНТ': sales_percent,
                'ОСТАТОК_СЕБЕСТ': stock_cost,
                'ОСТАТОК_ПРОЦЕНТ': stock_percent,
                'ОБОРАЧИВАЕМОСТЬ_ДН': item['ОБОР_ДН']
            })
        
        # Добавляем итоговую строку
        enhanced_data.append({
            'КАТЕГОРИЯ': 'ИТОГО:',
            'ПРОДАЖА_СЕБЕСТ': total_sales_cost,
            'ПРОДАЖА_ПРОЦЕНТ': 100.0,
            'ОСТАТОК_СЕБЕСТ': total_stock_cost,
            'ОСТАТОК_ПРОЦЕНТ': 100.0,
            'ОБОРАЧИВАЕМОСТЬ_ДН': total_row['ОБОР_ДН']
        })
        
        return {
            'warehouse_name': warehouse_name,
            'data': enhanced_data,
            'total_sales_cost': total_sales_cost,
            'total_stock_cost': total_stock_cost,
            'avg_turnover_days': basic_report['avg_turnover_days'],
            'categories_count': len(data_without_total)
        }
    
    def generate_summary_report(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует сводный отчет по всем складам"""
        summary_data = []
        
        for warehouse_name, report_data in reports.items():
            summary_data.append({
                'Склад': warehouse_name,
                'Категорий': report_data['categories_count'],
                'Общие_продажи': report_data['total_sales'],
                'Общие_остатки': report_data['total_stock'],
                'Средняя_оборачиваемость': report_data['avg_turnover_days']
            })
        
        # Сортируем по убыванию продаж
        summary_data.sort(key=lambda x: x['Общие_продажи'], reverse=True)
        
        return {
            'summary': summary_data,
            'total_warehouses': len(summary_data),
            'total_sales_all': sum(item['Общие_продажи'] for item in summary_data),
            'total_stock_all': sum(item['Общие_остатки'] for item in summary_data),
            'avg_turnover_all': sum(item['Средняя_оборачиваемость'] for item in summary_data) / len(summary_data) if summary_data else 0
        }
    
    def get_warehouse_names(self) -> List[str]:
        """Получает список уникальных названий складов"""
        warehouses = set()
        
        # Собираем названия складов из данных остатков
        for warehouse in self.category_extractor.stock_data.get('ОстаткиПоСкладам', []):
            warehouse_name = warehouse.get('Склад', '')
            if warehouse_name:
                warehouses.add(warehouse_name)
        
        return sorted(list(warehouses))
    
    def generate_all_cost_based_reports(self) -> Dict[str, Any]:
        """Генерирует расширенные отчеты с себестоимостью для всех складов"""
        warehouses = self.get_warehouse_names()
        cost_reports = {}
        
        for warehouse_name in warehouses:
            print(f"📊 Генерируем расширенный отчет для: {warehouse_name}")
            report = self.generate_cost_based_turnover_report(warehouse_name)
            if report:
                cost_reports[warehouse_name] = report
        
        return cost_reports
    
    def export_cost_based_to_xlsx(self, reports: Dict[str, Any], output_prefix: str = "cost_turnover_reports") -> List[str]:
        """Экспортирует расширенные отчеты с себестоимостью в XLSX"""
        from datetime import datetime
        import os
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Создаем папку Downloads если не существует
        downloads_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads_path):
            downloads_path = os.getcwd()
        
        exported_files = []
        
        for warehouse_name, report_data in reports.items():
            # Создаем безопасное имя файла
            safe_name = self.create_safe_filename(warehouse_name)
            
            # Создаем DataFrame
            df = pd.DataFrame(report_data['data'])
            
            # Подготавливаем данные для Excel
            df_export = df.copy()
            df_export['ПРОДАЖА_ПРОЦЕНТ'] = df_export['ПРОДАЖА_ПРОЦЕНТ'] / 100  # Переводим в десятичные доли для Excel
            df_export['ОСТАТОК_ПРОЦЕНТ'] = df_export['ОСТАТОК_ПРОЦЕНТ'] / 100
            df_export['ОБОРАЧИВАЕМОСТЬ_ДН'] = df_export['ОБОРАЧИВАЕМОСТЬ_ДН'].apply(lambda x: "∞" if x == 9999 else x)
            
            # Выбираем и переименовываем столбцы
            df_final = df_export[['КАТЕГОРИЯ', 'ПРОДАЖА_СЕБЕСТ', 'ПРОДАЖА_ПРОЦЕНТ', 
                                'ОСТАТОК_СЕБЕСТ', 'ОСТАТОК_ПРОЦЕНТ', 'ОБОРАЧИВАЕМОСТЬ_ДН']].copy()
            df_final.columns = ['КАТЕГОРИИ', 'ПРОДАЖА ПО Себ.Ст', '%', 'ОСТАТОК по Себ.Ст.', '% ', 'ОБОРАЧИВАЕМОСТЬ (дн.)']
            
            # Экспортируем в Downloads
            filename = f"{output_prefix}_{safe_name}_{timestamp}.xlsx"
            filepath = os.path.join(downloads_path, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_final.to_excel(writer, sheet_name='Себестоимость', index=False)
                
                # Форматируем Excel файл
                workbook = writer.book
                worksheet = writer.sheets['Себестоимость']
                
                # Форматируем процентные столбцы
                from openpyxl.styles import NamedStyle
                percent_style = NamedStyle(name="percent", number_format="0%")
                
                for row in range(2, len(df_final) + 2):  # Начинаем с 2-й строки (после заголовков)
                    worksheet[f'C{row}'].style = percent_style  # Колонка %
                    worksheet[f'E{row}'].style = percent_style  # Колонка % 
                
                # Автоширина колонок
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            exported_files.append(filepath)
            print(f"✅ Экспортирован расширенный отчет: {filepath}")
        
        return exported_files


def test_turnover_reports():
    """Тестирование генератора отчетов оборачиваемости"""
    print("🧪 ТЕСТИРОВАНИЕ ГЕНЕРАТОРА ОТЧЕТОВ ОБОРАЧИВАЕМОСТИ")
    print("=" * 60)
    
    generator = TurnoverReportGenerator()
    
    # Загружаем данные
    sales_path = '/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30.json'
    stock_path = '/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30 (4).json'
    
    if generator.load_data(sales_path, stock_path):
        
        # Генерируем отчеты для всех складов
        all_reports = generator.generate_all_warehouses_reports()
        
        print(f"\n📊 СГЕНЕРИРОВАНО ОТЧЕТОВ: {len(all_reports)}")
        print("-" * 40)
        
        # Показываем первый отчет как пример
        if all_reports:
            first_warehouse = list(all_reports.keys())[0]
            first_report = all_reports[first_warehouse]
            
            print(generator.format_turnover_report(first_report))
        
        # Генерируем сводный отчет
        summary = generator.generate_summary_report(all_reports)
        
        print("\n📋 СВОДНЫЙ ОТЧЕТ ПО СКЛАДАМ")
        print("-" * 80)
        for item in summary['summary']:
            print(f"{item['Склад'][:40]:<40} {item['Общие_продажи']:>12,.0f} {item['Общие_остатки']:>12,.0f} {item['Средняя_оборачиваемость']:>8.0f}")
        
        print(f"\nВсего складов: {summary['total_warehouses']}")
        print(f"Общие продажи: {summary['total_sales_all']:,.0f} ₸")
        print(f"Общие остатки: {summary['total_stock_all']:,.0f} ₸")
        print(f"Средняя оборачиваемость: {summary['avg_turnover_all']:.0f} дней")
        
        # Экспортируем
        print(f"\n💾 ЭКСПОРТ ОТЧЕТОВ")
        print("-" * 20)
        exported_files = generator.export_to_xlsx(all_reports)
        
        return generator, all_reports
    
    else:
        print("❌ Не удалось загрузить данные")
        return None, None


if __name__ == '__main__':
    test_generator, test_reports = test_turnover_reports()