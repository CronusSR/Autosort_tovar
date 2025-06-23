#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОДНА СТРОКА - ИСПРАВЛЕНИЕ ЦЕН
Добавьте ТОЛЬКО ЭТУ СТРОКУ в ваш существующий код

Автор: Ваш FullStack программист
Дата: 2025-06-20
"""

# ===== ОДНА СТРОКА ДЛЯ ИСПРАВЛЕНИЯ =====

def fix_price_column_name(ads_data):
    """
    ОДНА СТРОКА для исправления названия колонки с ценами
    """
    if 'Посл. закупка' in ads_data.columns:
        ads_data['last_purchase_price'] = ads_data['Посл. закупка']
    return ads_data

# ===== ИНСТРУКЦИЯ =====

def get_one_line_fix_instruction():
    """
    Инструкция где добавить одну строку
    """
    
    return """
# 🎯 ОДНА СТРОКА - ИСПРАВЛЕНИЕ ЦЕН

## 📍 ГДЕ ДОБАВИТЬ:

В вашей функции `analyze_warehouse_stock_with_details` найдите место где используется `ads_data` и добавьте ОДНУ строку:

```python
def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
    
    # ДОБАВИТЬ ЭТУ СТРОКУ В САМОМ НАЧАЛЕ:
    if 'Посл. закупка' in ads_data.columns:
        ads_data['last_purchase_price'] = ads_data['Посл. закупка']
    
    # ... ваш существующий код остается как есть ...
```

## 🎯 АЛЬТЕРНАТИВА - в начале функции warehouse_analysis_page:

```python
def warehouse_analysis_page(system):
    
    # ДОБАВИТЬ ЭТИ 3 СТРОКИ В САМОМ НАЧАЛЕ:
    if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        if 'Посл. закупка' in system.calculated_ads.columns:
            system.calculated_ads['last_purchase_price'] = system.calculated_ads['Посл. закупка']
    
    # ... ваш существующий код остается как есть ...
```

## ✅ РЕЗУЛЬТАТ:

- ✅ Система найдет цены в колонке "Посл. закупка"
- ✅ Переименует её в "last_purchase_price" 
- ✅ Ваш существующий код заработает с ценами
- ✅ НИЧЕГО больше менять не нужно!

## 💡 ЧТО ДЕЛАЕТ:

Просто переименовывает колонку "Посл. закупка" в "last_purchase_price", которую ищет ваша система.

Всё! Больше ничего менять не нужно!
"""

if __name__ == "__main__":
    print("🎯 Одна строка для исправления цен")
    print(get_one_line_fix_instruction())