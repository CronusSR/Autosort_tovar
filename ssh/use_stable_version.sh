#\!/bin/bash
# Использование стабильной версии webhook_persistent_app.py

echo "🔧 Использование стабильной версии webhook_persistent_app.py"
echo "=========================================================="

# Используем самую большую backup версию (120403) как основу
echo "📋 Копируем стабильную версию..."
cp ssh/webhook_persistent_app_backup_20250724_120403.py webhook_persistent_app_stable.py

# Добавляем наши улучшения (иерархия складов, кэширование ABC)
echo "🔧 Добавляем улучшения..."

# Создаем патч с нашими улучшениями
cat > /tmp/add_improvements.py << 'PYTHON_EOF'
#\!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Читаем стабильную версию
with open('webhook_persistent_app_stable.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем импорт pytz с проверкой
if 'import pytz' in content and 'PYTZ_AVAILABLE' not in content:
    content = content.replace(
        'import os',
        '''import os
import pickle

# Импорт pytz с fallback
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    # Fallback для работы без pytz
    class SimpleTimezone:
        def __init__(self, name):
            self.name = name
        def localize(self, dt):
            return dt
    pytz = type('pytz', (), {'timezone': lambda name: SimpleTimezone(name)})()'''
    )

# 2. Добавляем WAREHOUSE_HIERARCHY если его нет
if 'WAREHOUSE_HIERARCHY' not in content:
    hierarchy_code = '''
# Иерархическая структура складов
WAREHOUSE_HIERARCHY = {
    # ХАБ (уровень 1) - главный склад
    'База Склад Фурнитура Комплект': {
        'level': 1,
        'type': 'hub',
        'city': 'Алматы',
        'parent': None,
        'children': [
            'Казыбаева Склад Фурнитура TRADE',
            'склад фурнитура № 1',
            '4 Склад фурнитуры АЗМ Шымкент',
            'Барыс Склад Фурнитура TRADE',
            'АО Склад Фурнитура TRADE'
        ],
        'min_days': 30,
        'max_days': 90,
        'description': 'Главный хаб - пополняет все склады 2-го уровня'
    },
    
    # СКЛАДЫ 2-го уровня (питаются от хаба)
    'Казыбаева Склад Фурнитура TRADE': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Алматы',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['ТД Казыбаева ФУРНИТУРА магазин'],
        'min_days': 15,
        'max_days': 45,
        'description': 'Склад 2-го уровня → пополняет магазин Казыбаева'
    },
    'склад фурнитура № 1': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Астана',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['Магазин фурнитуры'],
        'min_days': 20,
        'max_days': 60,
        'description': 'Склад 2-го уровня → пополняет Магазин фурнитуры'
    },
    '4 Склад фурнитуры АЗМ Шымкент': {
        'level': 2,
        'type': 'warehouse',
        'city': 'Шымкент',
        'parent': 'База Склад Фурнитура Комплект',
        'children': ['6 Склад фурнитуры "Овощная база" Магазин'],
        'min_days': 20,
        'max_days': 60,
        'description': 'Склад 2-го уровня → пополняет магазин в Шымкенте'
    },
    
    # МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов)
    'Барыс Склад Фурнитура TRADE': {
        'level': 2,
        'type': 'shop',
        'city': 'Барыс',
        'parent': 'База Склад Фурнитура Комплект',
        'children': [],
        'min_days': 15,
        'max_days': 45,
        'description': 'Магазин напрямую от хаба'
    },
    'АО Склад Фурнитура TRADE': {
        'level': 2,
        'type': 'shop',
        'city': 'Алтын Орда',
        'parent': 'База Склад Фурнитура Комплект',
        'children': [],
        'min_days': 10,
        'max_days': 30,
        'description': 'Магазин напрямую от хаба (кромочные материалы)'
    },
    
    # МАГАЗИНЫ 3-го уровня (питаются от складов 2-го уровня)
    'ТД Казыбаева ФУРНИТУРА магазин': {
        'level': 3,
        'type': 'shop',
        'city': 'Алматы',
        'parent': 'Казыбаева Склад Фурнитура TRADE',
        'children': [],
        'min_days': 8,
        'max_days': 30,
        'description': 'Магазин 3-го уровня ← от Казыбаева склад'
    },
    'Магазин фурнитуры': {
        'level': 3,
        'type': 'shop',
        'city': 'Астана',
        'parent': 'склад фурнитура № 1',
        'children': [],
        'min_days': 8,
        'max_days': 30,
        'description': 'Магазин 3-го уровня ← от склад № 1'
    },
    '6 Склад фурнитуры "Овощная база" Магазин': {
        'level': 3,
        'type': 'shop',
        'city': 'Шымкент',
        'parent': '4 Склад фурнитуры АЗМ Шымкент',
        'children': [],
        'min_days': 8,
        'max_days': 30,
        'description': 'Магазин 3-го уровня ← от Шымкент склад'
    }
}

def get_warehouse_info(warehouse_name):
    """Получить информацию о складе из иерархии"""
    for name, info in WAREHOUSE_HIERARCHY.items():
        if name in warehouse_name or warehouse_name in name:
            return info
    return None

def get_warehouse_level(warehouse_name):
    """Получить уровень склада в иерархии"""
    info = get_warehouse_info(warehouse_name)
    return info['level'] if info else 0

def get_warehouse_type(warehouse_name):
    """Получить тип склада (hub/warehouse/shop)"""
    info = get_warehouse_info(warehouse_name)
    return info['type'] if info else 'unknown'

def get_parent_warehouse(warehouse_name):
    """Получить родительский склад"""
    info = get_warehouse_info(warehouse_name)
    return info['parent'] if info else None

def get_children_warehouses(warehouse_name):
    """Получить дочерние склады"""
    info = get_warehouse_info(warehouse_name)
    return info['children'] if info else []

def calculate_stock_requirements(ads, warehouse_name):
    """Расчет минимальных и максимальных остатков на основе ADS и типа склада"""
    info = get_warehouse_info(warehouse_name)
    if not info:
        # Дефолтные значения для неизвестных складов
        min_days, max_days = 8, 30
    else:
        min_days, max_days = info['min_days'], info['max_days']
    
    min_stock = ads * min_days
    max_stock = ads * max_days
    return min_stock, max_stock
'''
    # Вставляем после BRANCH_CITIES
    if 'BRANCH_CITIES' in content:
        pos = content.find('BRANCH_CITIES = {')
        if pos \!= -1:
            # Находим конец словаря
            end_pos = content.find('\n}', pos) + 2
            content = content[:end_pos] + '\n' + hierarchy_code + content[end_pos:]

# 3. Добавляем систему кэширования ABC
if 'CACHE_DIR = "cache"' not in content:
    cache_code = '''
# Система кэширования ABC анализа
CACHE_DIR = "cache"
ABC_CACHE_FILE = os.path.join(CACHE_DIR, "abc_analysis_cache.pkl")
VLADIVOSTOK_TZ = pytz.timezone('Asia/Vladivostok') if PYTZ_AVAILABLE else None

def ensure_cache_dir():
    """Создает директорию для кэша если её нет"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def should_update_abc_cache():
    """Проверяет нужно ли обновить кэш ABC анализа"""
    if not PYTZ_AVAILABLE:
        return True
    
    if not os.path.exists(ABC_CACHE_FILE):
        return True
    
    # Получаем время последнего обновления кэша
    cache_time = datetime.fromtimestamp(os.path.getmtime(ABC_CACHE_FILE))
    if VLADIVOSTOK_TZ:
        cache_time_vl = VLADIVOSTOK_TZ.localize(cache_time)
        now_vl = datetime.now(VLADIVOSTOK_TZ)
    else:
        cache_time_vl = cache_time
        now_vl = datetime.now()
    
    # Проверяем прошло ли время для автообновления (20:00 по Владивостоку)
    today_update_time = now_vl.replace(hour=20, minute=0, second=0, microsecond=0)
    
    # Если кэш старше чем сегодняшние 20:00 и уже наступило время обновления
    if cache_time_vl < today_update_time and now_vl >= today_update_time:
        return True
    
    # Если кэш старше 24 часов
    if now_vl - cache_time_vl > timedelta(hours=24):
        return True
    
    return False

def save_abc_cache(abc_data):
    """Сохраняет результаты ABC анализа в кэш"""
    if not PYTZ_AVAILABLE:
        return None
    
    ensure_cache_dir()
    try:
        with open(ABC_CACHE_FILE, 'wb') as f:
            pickle.dump({
                'data': abc_data,
                'timestamp': datetime.now(VLADIVOSTOK_TZ) if VLADIVOSTOK_TZ else datetime.now(),
                'version': '1.0'
            }, f)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения кэша: {e}")
        return False

def load_abc_cache():
    """Загружает результаты ABC анализа из кэша"""
    if not PYTZ_AVAILABLE:
        return None, None
    
    try:
        if os.path.exists(ABC_CACHE_FILE):
            with open(ABC_CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
                return cache['data'], cache['timestamp']
    except Exception as e:
        st.error(f"Ошибка загрузки кэша: {e}")
    return None, None

def get_cache_status():
    """Возвращает информацию о состоянии кэша"""
    if not PYTZ_AVAILABLE:
        return None
    
    if not os.path.exists(ABC_CACHE_FILE):
        return "Кэш не создан"
    
    cache_time = datetime.fromtimestamp(os.path.getmtime(ABC_CACHE_FILE))
    if VLADIVOSTOK_TZ:
        cache_time_vl = VLADIVOSTOK_TZ.localize(cache_time)
        now_vl = datetime.now(VLADIVOSTOK_TZ)
    else:
        cache_time_vl = cache_time
        now_vl = datetime.now()
    
    age = now_vl - cache_time_vl
    
    if age < timedelta(hours=1):
        return f"Обновлен {int(age.total_seconds() / 60)} мин назад"
    elif age < timedelta(days=1):
        return f"Обновлен {int(age.total_seconds() / 3600)} ч назад"
    else:
        return f"Обновлен {age.days} дн назад"
'''
    # Вставляем после функций иерархии
    if 'calculate_stock_requirements' in content:
        pos = content.find('def calculate_stock_requirements')
        if pos \!= -1:
            # Находим конец функции
            end_pos = content.find('\n\ndef ', pos)
            if end_pos == -1:
                end_pos = content.find('\n\n# ', pos)
            content = content[:end_pos] + '\n' + cache_code + content[end_pos:]

# Исправляем использование st.experimental_rerun на st.rerun
content = content.replace('st.experimental_rerun()', 'st.rerun()')

# Сохраняем как новый файл
with open('webhook_persistent_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Улучшения добавлены\!")
PYTHON_EOF

# Запускаем патч
python3 /tmp/add_improvements.py

# Проверяем синтаксис
echo "🔍 Проверяем синтаксис..."
python3 -m py_compile webhook_persistent_app.py
if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен\!"
else
    echo "❌ Ошибка синтаксиса\!"
    exit 1
fi

# Копируем на сервер
echo "📤 Копируем файл на сервер..."
scp webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/

# Перезапускаем на сервере
echo "🔄 Перезапускаем приложение на сервере..."
ssh root@217.114.1.117 "cd /opt/inventory_system && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ ГОТОВО\! Используется стабильная версия с улучшениями"
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"

rm -f /tmp/add_improvements.py webhook_persistent_app_stable.py
