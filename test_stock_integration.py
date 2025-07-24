#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования интеграции с файлом остатков
"""

import json
import pandas as pd
from datetime import datetime
import sys
import os

# Добавляем путь к модулю
sys.path.append('/mnt/f/Работа-Никита/Autosort_tovar')

def load_stock_file(file_path):
    """Загружает файл остатков и преобразует в DataFrame"""
    print(f"📁 Загрузка файла остатков: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            stock_data = json.load(f)
        
        print(f"✅ Файл загружен успешно")
        print(f"📅 Дата остатков: {stock_data.get('ДатаОстатков', 'не указана')}")
        print(f"📅 Дата выгрузки: {stock_data.get('ДатаВыгрузки', 'не указана')}")
        
        # Преобразуем в DataFrame
        stock_records = []
        
        for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
            warehouse = warehouse_data.get('Склад', '')
            city = warehouse_data.get('Город', '')
            
            for item in warehouse_data.get('Остатки', []):
                record = {
                    'warehouse': warehouse,
                    'city': city,
                    'category_path': item.get('ПутьКатегорий', ''),
                    'item_name': item.get('Номенклатура', ''),
                    'item_code': item.get('Артикул', ''),
                    'quantity': item.get('Количество', 0),
                    'cost': item.get('Стоимость', 0),
                    'avg_price': item.get('СредняяЦена', '').replace(' ', '').replace(',', '.') if item.get('СредняяЦена') else '0',
                    'unit': item.get('ЕдиницаИзмерения', ''),
                    'manufacturer': item.get('Производитель', ''),
                    'date': stock_data.get('ДатаОстатков', '')
                }
                stock_records.append(record)
        
        df = pd.DataFrame(stock_records)
        
        print(f"📊 Создан DataFrame с {len(df)} записями")
        print(f"🏪 Количество складов: {df['warehouse'].nunique()}")
        print(f"📦 Количество товаров: {df['item_code'].nunique()}")
        print(f"💰 Общая стоимость остатков: {df['cost'].sum():,.0f}")
        
        return df
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return None

def analyze_stock_structure(df):
    """Анализирует структуру остатков"""
    print("\n📊 АНАЛИЗ СТРУКТУРЫ ОСТАТКОВ:")
    print("=" * 50)
    
    # Анализ по складам
    print("\n🏪 АНАЛИЗ ПО СКЛАДАМ:")
    warehouse_stats = df.groupby('warehouse').agg({
        'quantity': 'sum',
        'cost': 'sum',
        'item_code': 'nunique'
    }).round(2)
    warehouse_stats.columns = ['Количество', 'Стоимость', 'Уникальных товаров']
    print(warehouse_stats)
    
    # Анализ по категориям (основным)
    print("\n📂 АНАЛИЗ ПО ОСНОВНЫМ КАТЕГОРИЯМ:")
    df['main_category'] = df['category_path'].apply(lambda x: 
        x.split('/')[-2] if len(x.split('/')) > 1 else 'Неопределенная'
    )
    
    category_stats = df.groupby('main_category').agg({
        'quantity': 'sum',
        'cost': 'sum',
        'item_code': 'nunique'
    }).sort_values('cost', ascending=False).head(10)
    category_stats.columns = ['Количество', 'Стоимость', 'Уникальных товаров']
    print(category_stats)
    
    # Топ товаров по стоимости
    print("\n💰 ТОП-10 ТОВАРОВ ПО СТОИМОСТИ ОСТАТКОВ:")
    top_items = df.nlargest(10, 'cost')[['item_name', 'quantity', 'cost', 'warehouse']]
    for idx, row in top_items.iterrows():
        print(f"{row['item_name'][:50]:<50} | {row['quantity']:>6} шт | {row['cost']:>12,.0f} ₸ | {row['warehouse']}")

def test_abc_analysis(df):
    """Тестирует ABC анализ на остатках"""
    print("\n🔤 ТЕСТИРОВАНИЕ ABC АНАЛИЗА:")
    print("=" * 50)
    
    # ABC анализ по основным категориям
    df['main_category'] = df['category_path'].apply(lambda x: 
        x.split('/')[-2] if len(x.split('/')) > 1 else 'Неопределенная'
    )
    
    category_summary = df.groupby('main_category').agg({
        'cost': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    # Сортируем по стоимости
    category_summary = category_summary.sort_values('cost', ascending=False)
    
    # Добавляем ABC классификацию
    total_cost = category_summary['cost'].sum()
    category_summary['percentage'] = (category_summary['cost'] / total_cost) * 100
    category_summary['cumulative_percentage'] = category_summary['percentage'].cumsum()
    
    # ABC классификация
    def assign_abc(cum_perc):
        if cum_perc <= 80:
            return 'A'
        elif cum_perc <= 95:
            return 'B'
        else:
            return 'C'
    
    category_summary['ABC'] = category_summary['cumulative_percentage'].apply(assign_abc)
    
    print("ABC АНАЛИЗ ПО КАТЕГОРИЯМ:")
    print(f"{'Категория':<30} | {'Стоимость':>12} | {'%':>6} | {'Накоп %':>8} | {'ABC':>3}")
    print("-" * 70)
    
    for _, row in category_summary.iterrows():
        print(f"{row['main_category'][:30]:<30} | {row['cost']:>12,.0f} | {row['percentage']:>5.1f}% | {row['cumulative_percentage']:>7.1f}% | {row['ABC']:>3}")
    
    # Статистика по ABC группам
    abc_stats = category_summary.groupby('ABC').agg({
        'cost': 'sum',
        'main_category': 'count'
    })
    
    print(f"\n📈 СТАТИСТИКА ПО ABC ГРУППАМ:")
    for abc_group, stats in abc_stats.iterrows():
        percentage = (stats['cost'] / total_cost) * 100
        print(f"Группа {abc_group}: {stats['main_category']} категорий, {stats['cost']:,.0f} ₸ ({percentage:.1f}%)")

def simulate_webhook_data(df):
    """Имитирует данные для webhook системы"""
    print("\n🔄 СИМУЛЯЦИЯ ДАННЫХ ДЛЯ WEBHOOK:")
    print("=" * 50)
    
    # Подготавливаем данные в формате, который ожидает система
    webhook_data = []
    
    for _, row in df.iterrows():
        webhook_record = {
            'warehouse': row['warehouse'],
            'item_code': row['item_code'],
            'item_name': row['item_name'],
            'quantity': row['quantity'],
            'amount': row['cost'],  # Используем стоимость как amount
            'category_path': row['category_path'],
            'date': row['date']
        }
        webhook_data.append(webhook_record)
    
    # Сохраняем в формате для тестирования
    test_file = '/tmp/test_stock_data.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(webhook_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Тестовые данные сохранены в: {test_file}")
    print(f"📊 Записей: {len(webhook_data)}")
    
    return webhook_data

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ С ФАЙЛОМ ОСТАТКОВ")
    print("=" * 60)
    
    # Путь к файлу остатков  
    stock_file = "/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30 (4).json"
    
    if not os.path.exists(stock_file):
        print(f"❌ Файл не найден: {stock_file}")
        return
    
    # Загружаем файл
    df = load_stock_file(stock_file)
    if df is None:
        return
    
    # Анализируем структуру
    analyze_stock_structure(df)
    
    # Тестируем ABC анализ
    test_abc_analysis(df)
    
    # Симулируем webhook данные
    webhook_data = simulate_webhook_data(df)
    
    print(f"\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print(f"📋 Создано {len(webhook_data)} записей для тестирования системы")
    print(f"🔗 Данные готовы для интеграции с webhook системой")

if __name__ == "__main__":
    main()