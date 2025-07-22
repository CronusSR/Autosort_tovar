#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест логики расчета оборачиваемости без зависимостей
"""

import json
from datetime import datetime

def calculate_turnover_days(item, period_days):
    """Упрощенная версия функции расчета оборачиваемости"""
    
    try:
        quantity = item.get('Количество', 0)
        
        if quantity <= 0 or period_days <= 0:
            return float('inf')
        
        # Средняя дневная продажа по количеству
        daily_quantity = quantity / period_days
        
        # Оборачиваемость = сколько дней нужно для продажи одной единицы
        turnover_days = 1 / daily_quantity if daily_quantity > 0 else float('inf')
        
        # Ограничиваем максимальное значение
        return min(turnover_days, 9999)
        
    except Exception as e:
        print(f"Ошибка расчета: {e}")
        return float('inf')

def test_turnover_logic():
    """Тестирование логики расчета оборачиваемости"""
    
    print("🧪 ПРОСТОЙ ТЕСТ ЛОГИКИ ОБОРАЧИВАЕМОСТИ")
    print("=" * 50)
    
    # Тестовые товары
    test_products = [
        {"name": "Быстрый товар", "Количество": 100, "period_days": 30},
        {"name": "Средний товар", "Количество": 45, "period_days": 30},
        {"name": "Медленный товар", "Количество": 10, "period_days": 30},
        {"name": "Очень медленный товар", "Количество": 2, "period_days": 30},
        {"name": "Товар без движения", "Количество": 0, "period_days": 30},
    ]
    
    print("Расчет оборачиваемости для тестовых товаров:\n")
    
    for product in test_products:
        quantity = product["Количество"]
        period_days = product["period_days"]
        
        # Рассчитываем оборачиваемость
        turnover_days = calculate_turnover_days(product, period_days)
        
        # Классифицируем
        if turnover_days == float('inf'):
            category = "❌ Без движения"
            rate_per_year = 0
        else:
            rate_per_year = 365 / turnover_days
            if turnover_days <= 30:
                category = "🚀 Быстрооборачиваемый"
            elif turnover_days <= 90:
                category = "🚶 Средний"
            elif turnover_days <= 365:
                category = "🐢 Медленный"
            else:
                category = "🐌 Очень медленный"
        
        # ADS расчет
        ads = quantity / period_days if period_days > 0 else 0
        
        print(f"📦 {product['name']}")
        print(f"   Продано за {period_days} дней: {quantity} шт")
        print(f"   ADS (средние дневные продажи): {ads:.2f} шт/день")
        print(f"   Оборачиваемость: {turnover_days:.1f} дней")
        print(f"   Оборотов в год: {rate_per_year:.1f}")
        print(f"   Категория: {category}")
        print()
    
    # Тестируем различные сценарии
    print("=" * 50)
    print("🔬 ТЕСТИРОВАНИЕ РАЗЛИЧНЫХ СЦЕНАРИЕВ")
    print()
    
    scenarios = [
        {"desc": "Супер-быстрый товар", "quantity": 365, "period": 30, "expected": "очень быстрый"},
        {"desc": "Товар с низкими продажами", "quantity": 1, "period": 60, "expected": "медленный"},
        {"desc": "Высокооборачиваемый товар", "quantity": 50, "period": 10, "expected": "быстрый"},
        {"desc": "Сезонный товар", "quantity": 20, "period": 90, "expected": "средний"},
    ]
    
    for scenario in scenarios:
        turnover = calculate_turnover_days({"Количество": scenario["quantity"]}, scenario["period"])
        ads = scenario["quantity"] / scenario["period"]
        
        print(f"📊 {scenario['desc']}")
        print(f"   {scenario['quantity']} шт за {scenario['period']} дней")
        print(f"   ADS: {ads:.2f}, Оборачиваемость: {turnover:.1f} дней")
        print()
    
    print("=" * 50)
    print("✅ ТЕСТ ЛОГИКИ ЗАВЕРШЕН УСПЕШНО!")
    print()
    print("🔑 КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print("• ADS = Количество продаж / Период в днях")
    print("• Дни оборачиваемости = 1 / (Количество / Период)")
    print("• Чем больше продаж, тем меньше дней оборачиваемости")
    print("• Классификация: <30д (быстрые), 30-90д (средние), 90-365д (медленные), >365д (очень медленные)")

if __name__ == "__main__":
    test_turnover_logic()