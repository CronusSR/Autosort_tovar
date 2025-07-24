#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграция файла остатков в webhook систему для тестирования
"""

import json
import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append('/mnt/f/Работа-Никита/Autosort_tovar')

try:
    from webhook_data_accumulator import WebhookDataAccumulator
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False
    print("⚠️ WebhookDataAccumulator не найден, создаем тестовую интеграцию")

def load_and_process_stock_file(file_path):
    """Загружает файл остатков и обрабатывает для webhook системы"""
    print(f"📁 Обработка файла остатков: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            stock_data = json.load(f)
        
        processed_records = []
        
        for warehouse_data in stock_data.get('ОстаткиПоСкладам', []):
            warehouse = warehouse_data.get('Склад', '')
            
            for item in warehouse_data.get('Остатки', []):
                # Обрабатываем путь категорий - убираем "Мебельная фурнитура" как общий корень
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
                
                record = {
                    'warehouse': warehouse,
                    'item_code': item.get('Артикул', ''),
                    'item_name': item.get('Номенклатура', ''),
                    'quantity': float(item.get('Количество', 0)),
                    'amount': float(item.get('Стоимость', 0)),  # Используем стоимость
                    'category_path': category_path,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'manufacturer': item.get('Производитель', ''),
                    'unit': item.get('ЕдиницаИзмерения', '')
                }
                processed_records.append(record)
        
        df = pd.DataFrame(processed_records)
        
        print(f"✅ Обработано {len(df)} записей остатков")
        print(f"📦 Уникальных товаров: {df['item_code'].nunique()}")
        
        # Анализируем новую структуру категорий
        print(f"\n📂 СТРУКТУРА КАТЕГОРИЙ ПОСЛЕ ОБРАБОТКИ:")
        categories = df['category_path'].apply(lambda x: x.split('/')[0] if x else 'Неопределенная').value_counts().head(15)
        for cat, count in categories.items():
            print(f"  {cat}: {count} товаров")
        
        return df
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return None

def create_test_webhook_data(stock_df):
    """Создает тестовые данные в формате webhook системы"""
    print(f"\n🔄 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ WEBHOOK СИСТЕМЫ:")
    print("=" * 60)
    
    # Подготавливаем stock данные
    stock_records = []
    for _, row in stock_df.iterrows():
        stock_record = {
            'warehouse': row['warehouse'],
            'item_code': row['item_code'], 
            'item_name': row['item_name'],
            'quantity': row['quantity'],
            'category_path': row['category_path'],
            'date': row['date'],
            'manufacturer': row['manufacturer'],
            'unit': row['unit']
        }
        stock_records.append(stock_record)
    
    # Создаем также минимальные sales данные для тестирования ABC анализа
    sales_records = []
    
    # Берем топ товары по стоимости и создаем фиктивные продажи
    top_items = stock_df.nlargest(500, 'amount')  # Топ 500 товаров
    
    for _, row in top_items.iterrows():
        # Создаем фиктивные продажи (10% от остатка)
        sales_quantity = max(1, row['quantity'] * 0.1)
        sales_amount = row['amount'] * 0.1
        
        sales_record = {
            'branch': row['warehouse'],  # Используем склад как филиал
            'item_code': row['item_code'],
            'item_name': row['item_name'],
            'quantity': sales_quantity,
            'amount': sales_amount,
            'category_path': row['category_path'],
            'date': row['date'],
            'manufacturer': row['manufacturer']
        }
        sales_records.append(sales_record)
    
    # Сохраняем в файлы для тестирования
    test_stock_file = '/tmp/test_stock_webhook.json'
    test_sales_file = '/tmp/test_sales_webhook.json'
    
    with open(test_stock_file, 'w', encoding='utf-8') as f:
        json.dump(stock_records, f, ensure_ascii=False, indent=2, default=str)
    
    with open(test_sales_file, 'w', encoding='utf-8') as f:
        json.dump(sales_records, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ Остатки сохранены: {test_stock_file} ({len(stock_records)} записей)")
    print(f"✅ Продажи сохранены: {test_sales_file} ({len(sales_records)} записей)")
    
    return stock_records, sales_records

def analyze_categories_for_abc(stock_df):
    """Анализирует категории для ABC анализа"""
    print(f"\n📊 АНАЛИЗ КАТЕГОРИЙ ДЛЯ ABC:")
    print("=" * 50)
    
    # Извлекаем основную категорию (первую в пути)
    stock_df_copy = stock_df.copy()
    stock_df_copy['main_category'] = stock_df_copy['category_path'].apply(
        lambda x: x.split('/')[0] if x and x != 'Неопределенная категория/' else 'Неопределенная'
    )
    
    # ABC анализ по основным категориям
    category_abc = stock_df_copy.groupby('main_category').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'item_code': 'nunique'
    }).reset_index()
    
    category_abc = category_abc.sort_values('amount', ascending=False)
    
    # Добавляем ABC классификацию
    total_amount = category_abc['amount'].sum()
    category_abc['percentage'] = (category_abc['amount'] / total_amount) * 100
    category_abc['cumulative_percentage'] = category_abc['percentage'].cumsum()
    
    def assign_abc(cum_perc):
        if cum_perc <= 80:
            return 'A'
        elif cum_perc <= 95:
            return 'B'
        else:
            return 'C'
    
    category_abc['ABC'] = category_abc['cumulative_percentage'].apply(assign_abc)
    
    print(f"{'Категория':<25} | {'Стоимость':>12} | {'Товаров':>8} | {'%':>6} | {'ABC':>3}")
    print("-" * 70)
    
    for _, row in category_abc.head(20).iterrows():
        print(f"{row['main_category'][:25]:<25} | {row['amount']:>12,.0f} | {row['item_code']:>8} | {row['percentage']:>5.1f}% | {row['ABC']:>3}")
    
    if len(category_abc) > 20:
        print(f"... и еще {len(category_abc) - 20} категорий")
    
    # Статистика ABC
    abc_stats = category_abc.groupby('ABC').agg({
        'amount': 'sum',
        'main_category': 'count'
    })
    
    print(f"\n📈 ABC СТАТИСТИКА:")
    for abc_group, stats in abc_stats.iterrows():
        percentage = (stats['amount'] / total_amount) * 100
        print(f"  Группа {abc_group}: {stats['main_category']} категорий, {percentage:.1f}% стоимости")

def main():
    """Основная функция интеграции"""
    print("🔗 ИНТЕГРАЦИЯ ОСТАТКОВ В WEBHOOK СИСТЕМУ")
    print("=" * 70)
    
    stock_file = "/mnt/f/Работа-Никита/Autosort_tovar/2025-06-30 (4).json"
    
    if not os.path.exists(stock_file):
        print(f"❌ Файл не найден: {stock_file}")
        return
    
    # Загружаем и обрабатываем файл остатков
    stock_df = load_and_process_stock_file(stock_file)
    if stock_df is None:
        return
    
    # Анализируем категории для ABC
    analyze_categories_for_abc(stock_df)
    
    # Создаем тестовые данные
    stock_records, sales_records = create_test_webhook_data(stock_df)
    
    print(f"\n✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
    print(f"📊 Готово для тестирования:")
    print(f"   - {len(stock_records)} записей остатков")
    print(f"   - {len(sales_records)} записей продаж")
    print(f"   - Данные в формате webhook системы")
    print(f"📂 Файлы сохранены в /tmp/ для импорта в систему")

if __name__ == "__main__":
    main()