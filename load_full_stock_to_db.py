#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная загрузка данных остатков в базу данных webhook системы
"""

import json
import pandas as pd
from datetime import datetime
import sys
import os
from pathlib import Path

# Импортируем webhook accumulator
sys.path.append('/mnt/f/Работа-Никита/Autosort_tovar')

try:
    from webhook_data_accumulator import WebhookDataAccumulator
    print("✅ WebhookDataAccumulator импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта WebhookDataAccumulator: {e}")
    exit(1)

def clear_and_load_full_data():
    """Очищает БД и загружает полные данные из файла остатков"""
    print("🔄 ПОЛНАЯ ПЕРЕЗАГРУЗКА ДАННЫХ")
    print("=" * 50)
    
    # Инициализируем accumulator
    accumulator = WebhookDataAccumulator()
    
    # Очищаем существующие данные
    print("🗑️ Очистка существующих данных...")
    import sqlite3
    
    with sqlite3.connect(accumulator.db_path) as conn:
        conn.execute("DELETE FROM sales")
        conn.execute("DELETE FROM stock") 
        conn.execute("DELETE FROM upload_history")
        conn.commit()
        print("✅ Данные очищены")
    
    # Загружаем файл остатков
    stock_file = "/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30 (4).json"
    
    if not os.path.exists(stock_file):
        print(f"❌ Файл не найден: {stock_file}")
        return False
    
    print(f"📁 Загрузка файла: {stock_file}")
    
    with open(stock_file, 'r', encoding='utf-8-sig') as f:
        stock_data = json.load(f)
    
    print(f"📊 Дата остатков: {stock_data.get('ДатаОстатков', 'Не указана')}")
    
    # Обрабатываем и загружаем остатки
    stock_records = []
    
    for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
        warehouse = warehouse_data.get('Склад', '')
        
        for item in warehouse_data.get('Остатки', []):
            # Обрабатываем путь категорий
            category_path = item.get('ПутьКатегорий', '')
            
            if category_path:
                parts = [p.strip() for p in category_path.split('/') if p.strip()]
                
                # Убираем "Мебельная фурнитура" если это последний элемент
                if parts and parts[-1] == "Мебельная фурнитура":
                    parts = parts[:-1]
                
                # Переворачиваем для правильного порядка: от общего к частному
                if parts:
                    category_path = '/'.join(reversed(parts)) + '/'
                else:
                    category_path = 'Неопределенная категория/'
            
            stock_record = {
                'date': '2025-06-30',  # Дата из файла
                'warehouse': warehouse,
                'item_code': item.get('Артикул', ''),
                'item_name': item.get('Номенклатура', ''),
                'quantity': float(item.get('Количество', 0)),
                'price': float(item.get('Стоимость', 0)) / max(float(item.get('Количество', 1)), 1)  # Цена за единицу
            }
            stock_records.append(stock_record)
    
    print(f"📦 Обработано {len(stock_records)} записей остатков")
    
    # Загружаем остатки в БД напрямую
    with sqlite3.connect(accumulator.db_path) as conn:
        for record in stock_records:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO stock (date, warehouse, item_code, item_name, quantity, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record['date'],
                    record['warehouse'], 
                    record['item_code'],
                    record['item_name'],
                    record['quantity'],
                    record['price']
                ))
            except Exception as e:
                print(f"⚠️ Ошибка загрузки остатка {record['item_code']}: {e}")
        
        conn.commit()
    
    print("✅ Остатки загружены в БД")
    
    # Создаем тестовые продажи с category_path
    print("🛒 Создание тестовых продаж...")
    
    # Берем топ товары по стоимости
    df_stock = pd.DataFrame(stock_records)
    df_stock['total_value'] = df_stock['quantity'] * df_stock['price']
    df_stock = df_stock.sort_values('total_value', ascending=False)
    
    top_items = df_stock.head(500)  # Топ 500 товаров
    
    sales_records = []
    
    for _, row in top_items.iterrows():
        # Получаем путь категорий для этого товара из оригинальных данных
        category_path = 'Неопределенная категория/'
        
        # Ищем категорию в оригинальных данных
        for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
            if warehouse_data.get('Склад', '') == row['warehouse']:
                for item in warehouse_data.get('Остатки', []):
                    if item.get('Артикул', '') == row['item_code']:
                        orig_path = item.get('ПутьКатегорий', '')
                        if orig_path:
                            parts = [p.strip() for p in orig_path.split('/') if p.strip()]
                            if parts and parts[-1] == "Мебельная фурнитура":
                                parts = parts[:-1]
                            if parts:
                                category_path = '/'.join(reversed(parts)) + '/'
                        break
        
        # Создаем фиктивные продажи (10% от остатка)
        sales_quantity = max(1, row['quantity'] * 0.1)
        sales_amount = row['total_value'] * 0.1
        
        sales_record = {
            'date': '2025-06-30',
            'branch': row['warehouse'],  # Используем склад как филиал
            'item_code': row['item_code'],
            'item_name': row['item_name'],
            'quantity': sales_quantity,
            'amount': sales_amount,
            'category': category_path.split('/')[0] if category_path else 'Неопределенная',
            'category_path': category_path,
            'data_hash': f"test_{row['item_code']}"
        }
        sales_records.append(sales_record)
    
    print(f"🛒 Создано {len(sales_records)} записей продаж")
    
    # Загружаем продажи в БД напрямую
    with sqlite3.connect(accumulator.db_path) as conn:
        for record in sales_records:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO sales (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['date'],
                    record['branch'],
                    record['item_code'], 
                    record['item_name'],
                    record['quantity'],
                    record['amount'],
                    record['category'],
                    record['category_path'],
                    record['data_hash']
                ))
            except Exception as e:
                print(f"⚠️ Ошибка загрузки продажи {record['item_code']}: {e}")
        
        conn.commit()
    
    print("✅ Продажи загружены в БД")
    
    # Проверяем результат
    print("\n📊 ПРОВЕРКА РЕЗУЛЬТАТА:")
    print("-" * 30)
    
    with sqlite3.connect(accumulator.db_path) as conn:
        cursor = conn.cursor()
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM stock")
        stock_count = cursor.fetchone()[0]
        print(f"📦 Остатков в БД: {stock_count}")
        
        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]
        print(f"🛒 Продаж в БД: {sales_count}")
        
        # Проверяем category_path
        cursor.execute("SELECT COUNT(*) FROM sales WHERE category_path IS NOT NULL AND category_path != ''")
        cat_count = cursor.fetchone()[0]
        print(f"📂 Продаж с category_path: {cat_count}")
        
        # Показываем примеры категорий
        cursor.execute("SELECT DISTINCT category_path FROM sales WHERE category_path IS NOT NULL LIMIT 10")
        categories = cursor.fetchall()
        print("📋 Примеры category_path:")
        for cat, in categories:
            print(f"   - {cat}")
    
    return True

if __name__ == "__main__":
    if clear_and_load_full_data():
        print("\n✅ ПОЛНАЯ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print("🎯 Теперь все аналитические функции должны работать:")
        print("   - 🔄 Оборачиваемость")
        print("   - 🏙️ Анализ по городам") 
        print("   - 🔀 Межфилиальные перемещения")
        print("   - 📦 ABC анализ категорий")
    else:
        print("\n❌ ОШИБКА ЗАГРУЗКИ!")