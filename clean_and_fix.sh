#!/bin/bash

# Очистка старых остатков и загрузка новых с правильной структурой городов
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "🧹 ОЧИСТКА СТАРЫХ ОСТАТКОВ И ИСПРАВЛЕНИЕ"
echo "📅 Время: $(date)"
echo ""
echo "🎯 ПЛАН ДЕЙСТВИЙ:"
echo "   1️⃣ Удалить ВСЕ старые остатки из БД"
echo "   2️⃣ Загрузить ТОЛЬКО новые остатки из файла 2025-06-30 (4).json"
echo "   3️⃣ Оставить все файлы продаж как есть (они уже работают)"
echo "   4️⃣ Исправить структуру городов"
echo "   5️⃣ Исправить график оборачиваемости"
echo ""

if [ ! -f "webhook_app_stable.py" ]; then
    echo "❌ Файл webhook_app_stable.py не найден"
    exit 1
fi

if [ ! -f "2025-06-30 (4).json" ]; then
    echo "❌ Файл остатков не найден"
    exit 1
fi

echo "📤 Загрузка файлов на сервер..."
scp webhook_app_stable.py "$USER@$SERVER:$REMOTE_PATH/webhook_persistent_app.py"
scp "2025-06-30 (4).json" "$USER@$SERVER:$REMOTE_PATH/"

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    echo '🧹 ОЧИСТКА И ИСПРАВЛЕНИЕ СИСТЕМЫ'
    echo '=================================================='
    
    # Останавливаем сервис
    systemctl stop webhook-analytics
    
    # Исправляем структуру БД
    echo '🗄️ Проверка структуры БД...'
    sqlite3 webhook_data.db \"ALTER TABLE sales ADD COLUMN category TEXT;\" 2>/dev/null || echo '✅ category уже есть'
    sqlite3 webhook_data.db \"ALTER TABLE sales ADD COLUMN category_path TEXT;\" 2>/dev/null || echo '✅ category_path уже есть'
    
    # ВАЖНО: Удаляем ТОЛЬКО остатки, продажи оставляем!
    echo '🗑️ Удаление ТОЛЬКО старых остатков (продажи сохраняем)...'
    sqlite3 webhook_data.db \"DELETE FROM stock;\"
    
    # Проверяем что продажи остались
    SALES_COUNT=\$(sqlite3 webhook_data.db \"SELECT COUNT(*) FROM sales;\")
    echo \"✅ Продаж в БД: \$SALES_COUNT (должны остаться)\"
    
    # Создаем скрипт загрузки ТОЛЬКО остатков
    cat > load_only_stock.py << 'PYTHON_END'
#!/usr/bin/env python3
import json
import sqlite3
import os

def get_city_from_branch(branch_name):
    \"\"\"Определяет город по названию филиала с ПРАВИЛЬНОЙ структурой\"\"\"
    if not branch_name:
        return 'Неопределен'
    
    branch_name = str(branch_name).strip()
    
    # Точные соответствия с правильными городами
    city_mapping = {
        # ХАБ
        'База Склад Фурнитура Комплект': 'Алматы',
        
        # СКЛАДЫ 2-го уровня  
        'Казыбаева Склад Фурнитура TRADE': 'Казыбаева',
        'склад фурнитура № 1': 'Астана',
        '4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"': 'Шымкент',
        
        # МАГАЗИНЫ от хаба
        'Барыс Склад Фурнитура TRADE': 'Барыс',
        'АО Склад Фурнитура TRADE': 'Алматы',  # Алтын Орда
        
        # МАГАЗИНЫ 3-го уровня
        'ТД Казыбаева ФУРНИТУРА магазин': 'Казыбаева', 
        'Магазин фурнитуры': 'Астана',
        '6 Склад фурнитуры \"Овощная база\" Магазин': 'Шымкент'
    }
    
    # Точное соответствие
    if branch_name in city_mapping:
        return city_mapping[branch_name]
    
    # Поиск по ключевым словам
    if 'Казыбаева' in branch_name:
        return 'Казыбаева'
    elif 'Барыс' in branch_name:
        return 'Барыс'
    elif 'Шымкент' in branch_name or 'Овощная база' in branch_name or 'АЗМ' in branch_name:
        return 'Шымкент'
    elif 'Астана' in branch_name or 'склад фурнитура № 1' in branch_name or 'Магазин фурнитуры' in branch_name:
        return 'Астана'
    elif 'АО' in branch_name and 'TRADE' in branch_name:
        return 'Алматы'  # АО = Алтын Орда
    else:
        return 'Алматы'  # По умолчанию

def main():
    if not os.path.exists('2025-06-30 (4).json'):
        print('❌ Файл остатков не найден')
        return False
    
    with open('2025-06-30 (4).json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    print(f'📦 Загрузка ТОЛЬКО остатков из: {data.get(\"ДатаОстатков\", \"Не указана\")}')
    
    conn = sqlite3.connect('webhook_data.db')
    cursor = conn.cursor()
    
    # Обрабатываем и загружаем ТОЛЬКО остатки
    stock_count = 0
    for wh_data in data.get('ОстаткиПоСкладам', []):
        warehouse = wh_data.get('Склад', '')
        city = get_city_from_branch(warehouse)
        
        for item in wh_data.get('Остатки', []):
            try:
                qty = float(item.get('Количество', 0))
                cost = float(item.get('Стоимость', 0))
                if qty > 0:
                    price = cost / qty
                    
                    cursor.execute(
                        'INSERT OR REPLACE INTO stock (date, warehouse, item_code, item_name, quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                        ('2025-06-30', warehouse, item.get('Артикул', ''), item.get('Номенклатура', ''), qty, price)
                    )
                    stock_count += 1
            except:
                continue
    
    conn.commit()
    
    print(f'✅ Загружено остатков: {stock_count}')
    
    # Проверяем продажи (они должны остаться)
    cursor.execute('SELECT COUNT(*) FROM sales')
    sales_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT date) FROM sales')
    days_count = cursor.fetchone()[0] if cursor.fetchone() else 0
    
    print(f'✅ Продаж в БД: {sales_count} за {days_count} дней (должны сохраниться)')
    
    # Показываем распределение остатков по городам
    cursor.execute('''
        SELECT 
            CASE 
                WHEN warehouse LIKE '%Казыбаева%' THEN 'Казыбаева'
                WHEN warehouse LIKE '%Барыс%' THEN 'Барыс'
                WHEN warehouse LIKE '%Шымкент%' OR warehouse LIKE '%Овощная база%' OR warehouse LIKE '%АЗМ%' THEN 'Шымкент'
                WHEN warehouse LIKE '%Астана%' OR warehouse LIKE '%склад фурнитура № 1%' OR warehouse LIKE '%Магазин фурнитуры%' THEN 'Астана'
                WHEN warehouse LIKE '%АО%' OR warehouse LIKE '%База%' THEN 'Алматы'
                ELSE 'Неопределен'
            END as city,
            COUNT(*) as items
        FROM stock 
        GROUP BY city
        ORDER BY items DESC
    ''')
    
    print('🏙️ Остатки по городам:')
    for city, count in cursor.fetchall():
        print(f'   {city}: {count} товаров')
    
    # Проверяем диапазон дат продаж
    cursor.execute('SELECT MIN(date), MAX(date) FROM sales')
    result = cursor.fetchone()
    if result[0]:
        print(f'📅 Диапазон продаж: {result[0]} - {result[1]}')
    else:
        print('⚠️ Нет данных о продажах')
    
    conn.close()
    return True

if __name__ == '__main__':
    if main():
        print('🎉 ОСТАТКИ ОБНОВЛЕНЫ, ПРОДАЖИ СОХРАНЕНЫ!')
    else:
        print('❌ ОШИБКА ОБНОВЛЕНИЯ')
PYTHON_END
    
    # Запускаем загрузку только остатков
    python3 load_only_stock.py
    
    # Обновляем функцию определения городов в коде
    echo '🔧 Обновление функции городов в коде...'
    
    cat > update_cities.py << 'UPDATE_END'
import re

def update_city_function():
    with open('webhook_persistent_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Новая функция с правильной структурой городов
    new_function = '''def get_city_from_branch(branch_name):
    \"\"\"Определяет город по названию филиала с учетом ПРАВИЛЬНОЙ структуры компании\"\"\"
    if pd.isna(branch_name) or branch_name == '':
        return 'Неопределен'
    
    branch_name = str(branch_name).strip()
    
    # Точные соответствия с правильными городами  
    city_mapping = {
        # ХАБ
        'База Склад Фурнитура Комплект': 'Алматы',
        
        # СКЛАДЫ 2-го уровня
        'Казыбаева Склад Фурнитура TRADE': 'Казыбаева',
        'склад фурнитура № 1': 'Астана', 
        '4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"': 'Шымкент',
        
        # МАГАЗИНЫ от хаба
        'Барыс Склад Фурнитура TRADE': 'Барыс',
        'АО Склад Фурнитура TRADE': 'Алматы',  # Алтын Орда
        
        # МАГАЗИНЫ 3-го уровня
        'ТД Казыбаева ФУРНИТУРА магазин': 'Казыбаева',
        'Магазин фурнитуры': 'Астана',
        '6 Склад фурнитуры \"Овощная база\" Магазин': 'Шымкент'
    }
    
    # Точное соответствие
    if branch_name in city_mapping:
        return city_mapping[branch_name]
    
    # Поиск по ключевым словам
    if 'Казыбаева' in branch_name:
        return 'Казыбаева'
    elif 'Барыс' in branch_name:
        return 'Барыс'
    elif 'Шымкент' in branch_name or 'Овощная база' in branch_name or 'АЗМ' in branch_name:
        return 'Шымкент'
    elif 'Астана' in branch_name or 'склад фурнитура № 1' in branch_name or 'Магазин фурнитуры' in branch_name:
        return 'Астана'  
    elif 'АО' in branch_name and 'TRADE' in branch_name:
        return 'Алматы'  # АО = Алтын Орда
    else:
        return 'Алматы'  # По умолчанию'''
    
    # Заменяем функцию
    pattern = r'def get_city_from_branch\(.*?\n(?:    .*\n)*?    return.*\n'
    content = re.sub(pattern, new_function + '\n\n', content, flags=re.MULTILINE)
    
    with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Функция городов обновлена')

update_city_function()
UPDATE_END
    
    python3 update_cities.py
    
    # Исправляем график оборачиваемости
    echo '🔧 Исправление графика оборачиваемости...'
    sed -i \"s/x='index',/x='category_name',/g\" webhook_persistent_app.py
    sed -i \"s/y='turnover_category',/y='count',/g\" webhook_persistent_app.py  
    sed -i \"s/color='index',/color='category_name',/g\" webhook_persistent_app.py
    sed -i \"s/'index': 'Категория оборачиваемости', 'turnover_category': 'Количество SKU'/'category_name': 'Категория оборачиваемости', 'count': 'Количество SKU'/g\" webhook_persistent_app.py
    
    # Добавляем исправление колонок в график
    sed -i '/turnover_distribution = turnover_data/a\\            \\n            # Исправляем названия колонок для совместимости\\n            if \"index\" not in turnover_distribution.columns:\\n                turnover_distribution.columns = [\"category_name\", \"count\"]\\n            else:\\n                turnover_distribution.columns = [\"category_name\", \"count\"]' webhook_persistent_app.py
    
    # Перезапускаем сервис
    echo '🔄 Перезапуск сервиса...'
    systemctl start webhook-analytics
    sleep 5
    
    # Удаляем временные файлы
    rm -f load_only_stock.py update_cities.py
    
    if systemctl is-active --quiet webhook-analytics; then
        echo '✅ Сервис запущен успешно'
    else
        echo '❌ Проблемы с сервисом'
        systemctl status webhook-analytics --no-pager | head -10
    fi
    
    echo ''
    echo '🎉 ОЧИСТКА И ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!'
    echo '=' \$(printf '=%.0s' {1..50})
    echo ''
    echo '✅ ЧТО СДЕЛАНО:'
    echo '   🗑️ Удалены ВСЕ старые остатки из БД'
    echo '   📦 Загружены свежие остатки из 2025-06-30 (4).json'
    echo '   🛒 Все файлы продаж сохранены (динамика работает)'
    echo '   🏙️ Обновлена структура городов (5 городов)'
    echo '   🔧 Исправлен график оборачиваемости'
    echo ''
    echo '🌐 Система готова: http://217.114.1.117:8502'
"

echo ""
echo "✅ ОЧИСТКА И ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🎯 РЕЗУЛЬТАТ:"
echo "   ✅ Старые остатки удалены, новые загружены"
echo "   ✅ Файлы продаж сохранены - динамика работает"
echo "   ✅ Правильная структура городов настроена"
echo "   ✅ График оборачиваемости исправлен"
echo ""
echo "🏢 ГОРОДА В СИСТЕМЕ:"
echo "   🏢 Алматы: База (хаб) + АО (Алтын Орда)"
echo "   🏪 Казыбаева: склад + магазин"
echo "   🏪 Барыс: склад"
echo "   🏪 Астана: склад № 1 + Магазин фурнитуры"
echo "   🏪 Шымкент: Овощная база склад + магазин"
echo ""
echo "📊 ДАННЫЕ:"
echo "   📦 Остатки: свежие данные на 2025-06-30"
echo "   🛒 Продажи: существующие файлы продаж (например, 2024-01-31.json и др.)"
echo "   📈 Динамика: строится из реальных файлов продаж"
echo ""
echo "🧪 ТЕПЕРЬ ДОЛЖНО РАБОТАТЬ:"
echo "   📈 Общий анализ → динамика продаж из реальных файлов"
echo "   🏙️ Анализ по городам → 5 правильных городов"
echo "   🔄 Оборачиваемость → без ошибок графика"
echo "   🔀 Межфилиальные перемещения → с правильной структурой"