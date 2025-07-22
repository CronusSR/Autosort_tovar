#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТИРОВАНИЕ ЭКСПОРТА В XLSX
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from turnover_report_generator import TurnoverReportGenerator


def test_xlsx_export():
    """Тестирование экспорта в XLSX"""
    print("🧪 ТЕСТИРОВАНИЕ ЭКСПОРТА В XLSX")
    print("=" * 40)
    
    generator = TurnoverReportGenerator()
    
    # Загружаем данные
    sales_path = '2025-06-30.json'
    stock_path = '2025-06-30 (4).json'
    
    if generator.load_data(sales_path, stock_path):
        
        # Тестируем один склад
        warehouse_name = "Магазин фурнитуры"
        print(f"\n📊 Тестируем экспорт для: {warehouse_name}")
        
        # Генерируем базовый отчет
        basic_report = generator.calculate_warehouse_turnover_report(warehouse_name)
        if basic_report:
            print(f"✅ Базовый отчет создан: {basic_report['categories_count']} категорий")
            
            # Экспортируем в XLSX
            basic_reports = {warehouse_name: basic_report}
            exported_basic = generator.export_to_xlsx(basic_reports, "test_basic")
            print(f"📁 Экспортирован базовый отчет: {exported_basic[0] if exported_basic else 'ОШИБКА'}")
        
        # Генерируем расширенный отчет
        cost_report = generator.generate_cost_based_turnover_report(warehouse_name)
        if cost_report:
            print(f"✅ Расширенный отчет создан: {cost_report['categories_count']} категорий")
            
            # Экспортируем в XLSX
            cost_reports = {warehouse_name: cost_report}
            exported_cost = generator.export_cost_based_to_xlsx(cost_reports, "test_cost")
            print(f"📁 Экспортирован расширенный отчет: {exported_cost[0] if exported_cost else 'ОШИБКА'}")
        
        # Проверяем, что файлы созданы
        print(f"\n🔍 ПРОВЕРКА ФАЙЛОВ")
        print("-" * 25)
        
        downloads_path = os.path.expanduser("~/Downloads")
        if not os.path.exists(downloads_path):
            downloads_path = os.getcwd()
        
        # Ищем созданные файлы
        import glob
        xlsx_files = glob.glob(os.path.join(downloads_path, "test_*.xlsx"))
        
        if xlsx_files:
            print(f"✅ Найдено {len(xlsx_files)} XLSX файлов:")
            for file in xlsx_files:
                file_size = os.path.getsize(file)
                print(f"   - {os.path.basename(file)} ({file_size} байт)")
        else:
            print("❌ XLSX файлы не найдены")
        
        print(f"\n📂 Путь к файлам: {downloads_path}")
    
    else:
        print("❌ Не удалось загрузить данные")


if __name__ == "__main__":
    test_xlsx_export()