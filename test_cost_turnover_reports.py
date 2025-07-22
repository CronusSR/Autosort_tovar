#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТИРОВАНИЕ РАСШИРЕННОГО ГЕНЕРАТОРА ОТЧЕТОВ ПО СЕБЕСТОИМОСТИ
"""

import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from turnover_report_generator import TurnoverReportGenerator


def test_cost_based_turnover_reports():
    """Тестирование расширенного генератора отчетов с себестоимостью"""
    print("🧪 ТЕСТИРОВАНИЕ РАСШИРЕННОГО ГЕНЕРАТОРА ОТЧЕТОВ ПО СЕБЕСТОИМОСТИ")
    print("=" * 70)
    
    generator = TurnoverReportGenerator()
    
    # Загружаем данные
    sales_path = '2025-06-30.json'
    stock_path = '2025-06-30 (4).json'
    
    if generator.load_data(sales_path, stock_path):
        
        # Генерируем расширенные отчеты для всех складов
        print("\n📊 Генерируем расширенные отчеты с себестоимостью...")
        all_cost_reports = generator.generate_all_cost_based_reports()
        
        print(f"\n💰 СГЕНЕРИРОВАНО РАСШИРЕННЫХ ОТЧЕТОВ: {len(all_cost_reports)}")
        print("-" * 50)
        
        # Показываем первый отчет как пример
        if all_cost_reports:
            first_warehouse = list(all_cost_reports.keys())[0]
            first_report = all_cost_reports[first_warehouse]
            
            print(f"\n🏢 ПРИМЕР ОТЧЕТА: {first_warehouse}")
            print("-" * 40)
            print(f"Категорий: {first_report['categories_count']}")
            print(f"Продажи (себ.): {first_report['total_sales_cost']:,.0f} ₸")
            print(f"Остатки (себ.): {first_report['total_stock_cost']:,.0f} ₸")
            print(f"Оборачиваемость: {first_report['avg_turnover_days']:.0f} дней")
            print()
            
            # Показываем топ-10 категорий
            print("🏆 ТОП-10 КАТЕГОРИЙ:")
            print("-" * 90)
            print(f"{'КАТЕГОРИИ':<40} {'ПРОДАЖА ПО Себ.Ст':>15} {'%':>5} {'ОСТАТОК по Себ.Ст.':>15} {'%':>5} {'ОБОР ДН':>8}")
            print("-" * 90)
            
            for i, item in enumerate(first_report['data'][:10]):
                category = item['КАТЕГОРИЯ'][:38] + ".." if len(item['КАТЕГОРИЯ']) > 38 else item['КАТЕГОРИЯ']
                sales_cost = f"{item['ПРОДАЖА_СЕБЕСТ']:,.0f}"
                sales_percent = f"{item['ПРОДАЖА_ПРОЦЕНТ']:.0f}%"
                stock_cost = f"{item['ОСТАТОК_СЕБЕСТ']:,.0f}"
                stock_percent = f"{item['ОСТАТОК_ПРОЦЕНТ']:.0f}%"
                turnover = f"{item['ОБОРАЧИВАЕМОСТЬ_ДН']:.0f}" if item['ОБОРАЧИВАЕМОСТЬ_ДН'] != 9999 else "∞"
                
                print(f"{category:<40} {sales_cost:>15} {sales_percent:>5} {stock_cost:>15} {stock_percent:>5} {turnover:>8}")
        
        # Экспортируем расширенные отчеты
        print(f"\n💾 ЭКСПОРТ РАСШИРЕННЫХ ОТЧЕТОВ")
        print("-" * 30)
        exported_files = generator.export_cost_based_to_xlsx(all_cost_reports)
        
        print(f"\n✅ Экспортировано {len(exported_files)} расширенных отчетов:")
        for file in exported_files:
            print(f"   - {file}")
        
        # Сравнение базовых и расширенных отчетов
        print(f"\n🔍 СРАВНЕНИЕ ОТЧЕТОВ")
        print("-" * 25)
        
        # Генерируем обычные отчеты для сравнения
        basic_reports = generator.generate_all_warehouses_reports()
        
        print(f"Базовых отчетов: {len(basic_reports)}")
        print(f"Расширенных отчетов: {len(all_cost_reports)}")
        
        # Сравниваем первый склад
        if basic_reports and all_cost_reports:
            warehouse_name = list(basic_reports.keys())[0]
            basic = basic_reports[warehouse_name]
            cost = all_cost_reports[warehouse_name]
            
            print(f"\nСравнение для {warehouse_name}:")
            print(f"Базовый отчет - Продажи: {basic['total_sales']:,.0f} ₸, Оборачиваемость: {basic['avg_turnover_days']:.0f} дней")
            print(f"Расширенный - Продажи (себ.): {cost['total_sales_cost']:,.0f} ₸, Оборачиваемость: {cost['avg_turnover_days']:.0f} дней")
    
    else:
        print("❌ Не удалось загрузить данные")


if __name__ == "__main__":
    test_cost_based_turnover_reports()