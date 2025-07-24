#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление базы данных для добавления полей категорий
"""

import sqlite3
import json
from pathlib import Path
from webhook_data_accumulator import WebhookDataAccumulator

def update_database_schema():
    """Обновляет схему базы данных для добавления полей категорий"""
    
    db_path = "webhook_data.db"
    
    print("🔧 Обновление схемы базы данных...")
    
    with sqlite3.connect(db_path) as conn:
        # Проверяем текущую структуру таблицы
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Текущие колонки: {columns}")
        
        # Добавляем новые колонки если их нет
        if 'category' not in columns:
            print("➕ Добавляем колонку 'category'...")
            conn.execute("ALTER TABLE sales ADD COLUMN category TEXT")
        
        if 'category_path' not in columns:
            print("➕ Добавляем колонку 'category_path'...")
            conn.execute("ALTER TABLE sales ADD COLUMN category_path TEXT")
        
        print("✅ Схема базы данных обновлена")

def reprocess_existing_files():
    """Перезаписывает данные из существующих JSON файлов с категориями"""
    
    print("\n🔄 Перезапись данных с категориями...")
    
    # Создаем новый накопитель с обновленной схемой
    accumulator = WebhookDataAccumulator()
    
    # Удаляем старые данные
    with sqlite3.connect(accumulator.db_path) as conn:
        conn.execute("DELETE FROM sales")
        print("🗑️ Старые данные удалены")
    
    # Обрабатываем все JSON файлы заново
    webhook_dir = Path("./webhook_uploads")
    json_files = list(webhook_dir.glob("*.json"))
    
    print(f"📁 Найдено {len(json_files)} JSON файлов для обработки")
    
    processed_count = 0
    total_records = 0
    
    for json_file in json_files:
        print(f"⚙️ Обработка {json_file.name}...")
        
        try:
            result = accumulator.process_new_sales_file(json_file)
            
            if result['status'] == 'success':
                processed_count += 1
                total_records += result.get('records_added', 0)
                print(f"   ✅ {result.get('records_added', 0)} записей добавлено")
            else:
                print(f"   ❌ Ошибка: {result.get('message')}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    print(f"\n📊 Итого:")
    print(f"   Обработано файлов: {processed_count}/{len(json_files)}")
    print(f"   Всего записей: {total_records}")
    
    # Проверяем результат
    with sqlite3.connect(accumulator.db_path) as conn:
        cursor = conn.cursor()
        
        # Общее количество записей
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_count = cursor.fetchone()[0]
        
        # Записи с категориями
        cursor.execute("SELECT COUNT(*) FROM sales WHERE category IS NOT NULL AND category != ''")
        with_category = cursor.fetchone()[0]
        
        # Уникальные категории
        cursor.execute("SELECT COUNT(DISTINCT category) FROM sales WHERE category IS NOT NULL AND category != ''")
        unique_categories = cursor.fetchone()[0]
        
        print(f"\n📈 Статистика базы данных:")
        print(f"   Всего записей: {total_count}")
        print(f"   С категориями: {with_category}")
        print(f"   Уникальных категорий: {unique_categories}")
        
        # Топ категории
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM sales 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        top_categories = cursor.fetchall()
        if top_categories:
            print(f"\n🏆 Топ категорий:")
            for category, count in top_categories:
                print(f"   {category}: {count} записей")

if __name__ == "__main__":
    print("🚀 ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ ДЛЯ ПОДДЕРЖКИ КАТЕГОРИЙ")
    print("=" * 60)
    
    # Шаг 1: Обновляем схему
    update_database_schema()
    
    # Шаг 2: Перезаписываем данные
    reprocess_existing_files()
    
    print("\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print("📊 Теперь ABC анализ по категориям должен работать")