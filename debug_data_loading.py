#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика загрузки данных в webhook системе
"""

import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к webhook_data_accumulator
sys.path.append('/mnt/f/Работа-Никита/Autosort_tovar')

try:
    from webhook_data_accumulator import WebhookDataAccumulator
    print("✅ WebhookDataAccumulator импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта WebhookDataAccumulator: {e}")
    exit(1)

def diagnose_data():
    """Диагностирует состояние данных в системе"""
    print("🔍 ДИАГНОСТИКА ДАННЫХ В WEBHOOK СИСТЕМЕ")
    print("=" * 60)
    
    try:
        # Инициализируем accumulator
        accumulator = WebhookDataAccumulator()
        print("✅ Подключение к базе данных успешно")
        
        # Проверяем продажи
        print("\n📊 ПРОВЕРКА ПРОДАЖ:")
        print("-" * 30)
        
        try:
            sales_data = accumulator.get_sales_data()
            print(f"✅ Загружено продаж: {len(sales_data)} записей")
            
            if not sales_data.empty:
                print(f"📅 Период данных: {sales_data['date'].min()} - {sales_data['date'].max()}")
                print(f"🏢 Филиалы: {sales_data['branch'].nunique()} уникальных")
                print(f"📦 Товары: {sales_data['item_code'].nunique()} уникальных")
                print(f"💰 Общая выручка: {sales_data['amount'].sum():,.0f} ₸")
                
                # Проверяем наличие category_path
                if 'category_path' in sales_data.columns:
                    categories = sales_data['category_path'].dropna().nunique()
                    print(f"📂 Категории с путями: {categories}")
                    
                    # Показываем примеры категорий
                    sample_categories = sales_data['category_path'].dropna().unique()[:5]
                    print("📋 Примеры путей категорий:")
                    for cat in sample_categories:
                        print(f"   - {cat}")
                else:
                    print("❌ Поле category_path отсутствует в данных продаж")
                
                # Проверяем филиалы
                print("🏢 Филиалы в данных:")
                branches = sales_data['branch'].value_counts().head(10)
                for branch, count in branches.items():
                    print(f"   - {branch}: {count} записей")
                    
            else:
                print("⚠️ Данные продаж пустые")
                
        except Exception as e:
            print(f"❌ Ошибка загрузки продаж: {e}")
        
        # Проверяем остатки
        print("\n📦 ПРОВЕРКА ОСТАТКОВ:")
        print("-" * 30)
        
        try:
            stock_data = accumulator.get_latest_stock()
            print(f"✅ Загружено остатков: {len(stock_data)} записей")
            
            if not stock_data.empty:
                print(f"📅 Дата остатков: {stock_data['date'].unique()}")
                print(f"🏪 Склады: {stock_data['warehouse'].nunique()} уникальных")
                print(f"📦 Товары: {stock_data['item_code'].nunique()} уникальных")
                print(f"📊 Общее количество: {stock_data['quantity'].sum():,.0f}")
                
                # Проверяем склады
                print("🏪 Склады в данных:")
                warehouses = stock_data['warehouse'].value_counts().head(10)
                for warehouse, count in warehouses.items():
                    print(f"   - {warehouse}: {count} товаров")
                    
            else:
                print("⚠️ Данные остатков пустые")
                
        except Exception as e:
            print(f"❌ Ошибка загрузки остатков: {e}")
        
        # Проверяем пересечения данных
        print("\n🔗 ПРОВЕРКА ПЕРЕСЕЧЕНИЙ:")
        print("-" * 30)
        
        if not sales_data.empty and not stock_data.empty:
            # Общие товары
            sales_items = set(sales_data['item_code'].unique())
            stock_items = set(stock_data['item_code'].unique())
            common_items = sales_items.intersection(stock_items)
            
            print(f"📦 Товары только в продажах: {len(sales_items - stock_items)}")
            print(f"📦 Товары только в остатках: {len(stock_items - sales_items)}")
            print(f"📦 Общие товары: {len(common_items)}")
            
            if len(common_items) > 0:
                print("✅ Есть общие товары - расчет оборачиваемости возможен")
            else:
                print("❌ Нет общих товаров - расчет оборачиваемости невозможен")
        
        # Проверяем структуру БД
        print("\n🗄️ СТРУКТУРА БАЗЫ ДАННЫХ:")
        print("-" * 30)
        
        import sqlite3
        db_path = accumulator.db_path
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Таблицы в БД: {[t[0] for t in tables]}")
            
            # Количество записей в таблицах
            for table_name, in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}: {count} записей")
                
                # Для sales показываем структуру
                if table_name == 'sales':
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    print(f"     Колонки: {[col[1] for col in columns]}")
        
        # Итоговая диагностика
        print("\n🎯 ИТОГОВАЯ ДИАГНОСТИКА:")
        print("=" * 60)
        
        sales_ok = not sales_data.empty if sales_data is not None else False
        stock_ok = not stock_data.empty if stock_data is not None else False
        
        print(f"📊 Продажи загружены: {'✅' if sales_ok else '❌'}")
        print(f"📦 Остатки загружены: {'✅' if stock_ok else '❌'}")
        
        if sales_ok and stock_ok:
            print("✅ ВСЕ АНАЛИТИЧЕСКИЕ ФУНКЦИИ ДОЛЖНЫ РАБОТАТЬ")
        elif sales_ok and not stock_ok:
            print("⚠️ Работают только анализы на основе продаж")
        elif not sales_ok and stock_ok:
            print("⚠️ Работают только анализы на основе остатков")
        else:
            print("❌ АНАЛИТИЧЕСКИЕ ФУНКЦИИ НЕ РАБОТАЮТ - НЕТ ДАННЫХ")
        
        return sales_ok, stock_ok
        
    except Exception as e:
        print(f"❌ Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()
        return False, False

if __name__ == "__main__":
    diagnose_data()