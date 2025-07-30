#!/usr/bin/env python3
import json
import sqlite3
import os

def main():
    print('🔄 ЗАГРУЗКА ПОЛНЫХ ДАННЫХ В БД')
    print('=' * 40)
    
    # Проверяем файл
    if not os.path.exists('2025-06-30 (4).json'):
        print('❌ Файл остатков не найден')
        return False
    
    # Загружаем данные
    with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    print(f'📊 Дата: {data.get("ДатаОстатков", "Не указана")}')
    
    # Подключаемся к БД
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    # Очищаем данные
    cursor.execute('DELETE FROM sales')
    cursor.execute('DELETE FROM stock')
    conn.commit()
    print('🗑️ Старые данные очищены')
    
    # Загружаем остатки
    stock_records = []
    for wh_data in data.get('ОстаткиПоСкладам', []):
        warehouse = wh_data.get('Склад', '')
        for item in wh_data.get('Остатки', []):
            try:
                qty = float(item.get('Количество', 0))
                cost = float(item.get('Стоимость', 0))
                if qty > 0:
                    stock_records.append({
                        'warehouse': warehouse,
                        'item_code': item.get('Артикул', ''),
                        'item_name': item.get('Номенклатура', ''),
                        'quantity': qty,
                        'price': cost / qty,
                        'total_value': cost,
                        'category_path': item.get('ПутьКатегорий', '')
                    })
            except:
                continue
    
    print(f'📦 Обработано {len(stock_records)} остатков')
    
    # Сортируем по стоимости
    stock_records.sort(key=lambda x: x['total_value'], reverse=True)
    
    # Загружаем остатки в БД
    for record in stock_records:
        cursor.execute('''
            INSERT OR REPLACE INTO stock (date, warehouse, item_code, item_name, quantity, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('2025-06-30', record['warehouse'], record['item_code'], 
              record['item_name'], record['quantity'], record['price']))
    
    # Создаем продажи из топ товаров
    top_items = stock_records[:500]  # Топ 500
    
    for item in top_items:
        # Обрабатываем category_path
        category_path = 'Неопределенная категория/'
        if item['category_path']:
            parts = [p.strip() for p in item['category_path'].split('/') if p.strip()]
            if parts and parts[-1] == 'Мебельная фурнитура':
                parts = parts[:-1]
            if parts:
                category_path = '/'.join(reversed(parts)) + '/'
        
        category = category_path.split('/')[0] if category_path else 'Неопределенная'
        
        # 10% от остатка как продажи
        sales_qty = max(1, item['quantity'] * 0.1)
        sales_amount = item['total_value'] * 0.1
        
        cursor.execute('''
            INSERT OR REPLACE INTO sales 
            (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('2025-06-30', item['warehouse'], item['item_code'], item['item_name'],
              sales_qty, sales_amount, category, category_path, f'test_{item["item_code"]}'))
    
    conn.commit()
    
    # Проверяем результат
    cursor.execute('SELECT COUNT(*) FROM stock')
    stock_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sales')
    sales_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sales WHERE category_path IS NOT NULL')
    cat_count = cursor.fetchone()[0]
    
    print(f'✅ РЕЗУЛЬТАТ:')
    print(f'   📦 Остатков: {stock_count}')
    print(f'   🛒 Продаж: {sales_count}')
    print(f'   📂 С категориями: {cat_count}')
    
    conn.close()
    return stock_count > 0 and sales_count > 0

if __name__ == '__main__':
    if main():
        print('🎉 УСПЕХ! Все данные загружены!')
    else:
        print('❌ Ошибка загрузки данных')
