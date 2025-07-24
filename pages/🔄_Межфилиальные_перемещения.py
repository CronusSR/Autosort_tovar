import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import time
import sys
import os

# Добавляем путь к родительской директории для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from modular_inventory_system import ModularInventorySystem
    ADS_AVAILABLE = True
except ImportError:
    ADS_AVAILABLE = False
    st.warning("⚠️ Модуль ADS расчетов не найден")

st.set_page_config(
    page_title="Межфилиальные перемещения",
    page_icon="🔄",
    layout="wide"
)

# Иерархия складов - ПРАВИЛЬНАЯ СТРУКТУРА
WAREHOUSE_HIERARCHY = {
    # 🏢 ГЛАВНЫЙ ХАБ (г.Алматы) - пополняет все склады 2-го уровня
    "hub": "База Склад Фурнитура Комплект (г.Алматы)",
    
    # 📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба)
    "level2_warehouses": {
        "Казыбаева Склад Фурнитура TRADE (г.Казыбаева)": ["ТД Казыбаева ФУРНИТУРА магазин"],
        "склад фурнитура № 1 (г.Астана)": ["Магазин фурнитуры (г.Астана)"],
        "4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)": ["6 Склад фурнитуры \"Овощная база\" Магазин"]
    },
    
    # 🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов)
    "direct_stores_from_hub": [
        "Барыс Склад Фурнитура TRADE (г.Барыс)",
        "АО Склад Фурнитура TRADE (г.Алматы)"
    ]
}

def normalize_branch_name(name):
    """Нормализация названий филиалов для сопоставления"""
    # Убираем лишние пробелы и приводим к нижнему регистру для сравнения
    name = str(name).strip()
    
    # Словарь соответствий для разных вариантов написания
    mappings = {
        # Основной хаб
        "База Склад Фурнитура Комплект": "База Склад Фурнитура Комплект (г.Алматы)",
        
        # Склады 2-го уровня
        "Казыбаева Склад Фурнитура TRADE": "Казыбаева Склад Фурнитура TRADE (г.Казыбаева)",
        "склад фурнитура №1": "склад фурнитура № 1 (г.Астана)",
        "склад фурнитура N 1": "склад фурнитура № 1 (г.Астана)",
        "склад фурнитура № 1": "склад фурнитура № 1 (г.Астана)",
        "4 Склад фурнитуры АЗМ Шымкент": "4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)",
        "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"": "4 Склад фурнитуры АЗМ Шымкент (г.Шымкент)",
        
        # Магазины от хаба
        "Барыс Склад Фурнитура TRADE": "Барыс Склад Фурнитура TRADE (г.Барыс)",
        "АО Склад Фурнитура TRADE": "АО Склад Фурнитура TRADE (г.Алматы)",
        
        # Магазины 3-го уровня
        "Магазин фурнитуры": "Магазин фурнитуры (г.Астана)",
        "6 Склад фурнитуры \"Овощная база\" Магазин продажи": "6 Склад фурнитуры \"Овощная база\" Магазин",
        "6 Склад фурнитуры \"Овощная база\" Магазин": "6 Склад фурнитуры \"Овощная база\" Магазин",
    }
    
    for old, new in mappings.items():
        if old.lower() in name.lower():
            return new
    
    return name

def get_branch_type(branch_name):
    """Определяет тип филиала: хаб, склад, магазин_от_хаба, магазин_3_уровня"""
    normalized = normalize_branch_name(branch_name)
    
    # 🏢 Главный хаб
    if normalized == WAREHOUSE_HIERARCHY["hub"]:
        return "хаб"
    
    # 📦 Склады 2-го уровня
    if normalized in WAREHOUSE_HIERARCHY["level2_warehouses"]:
        return "склад"
    
    # 🏪 Магазины напрямую от хаба
    if normalized in WAREHOUSE_HIERARCHY["direct_stores_from_hub"]:
        return "магазин_от_хаба"
    
    # 🏪 Магазины 3-го уровня (от складов 2-го уровня)
    for warehouse, stores in WAREHOUSE_HIERARCHY["level2_warehouses"].items():
        if normalized in stores:
            return "магазин_3_уровня"
    
    return "неизвестно"

def get_parent_warehouse(branch_name):
    """Возвращает родительский склад для филиала"""
    normalized = normalize_branch_name(branch_name)
    
    # 📦 Для складов 2-го уровня - родитель это хаб
    if normalized in WAREHOUSE_HIERARCHY["level2_warehouses"]:
        return WAREHOUSE_HIERARCHY["hub"]
    
    # 🏪 Для магазинов напрямую от хаба - родитель это хаб
    if normalized in WAREHOUSE_HIERARCHY["direct_stores_from_hub"]:
        return WAREHOUSE_HIERARCHY["hub"]
    
    # 🏪 Для магазинов 3-го уровня - родитель это их склад 2-го уровня
    for warehouse, stores in WAREHOUSE_HIERARCHY["level2_warehouses"].items():
        if normalized in stores:
            return warehouse
    
    return None

def load_json_file(uploaded_file):
    """Загрузка и парсинг JSON файла"""
    try:
        content = uploaded_file.read()
        # Обработка BOM (byte order mark)
        data = json.loads(content.decode('utf-8-sig'))
        return data
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {str(e)}")
        return None

def parse_stock_data(stock_json):
    """Парсинг данных об остатках из JSON"""
    all_stock = []
    
    try:
        if "ОстаткиПоСкладам" in stock_json:
            for warehouse_data in stock_json["ОстаткиПоСкладам"]:
                branch = normalize_branch_name(warehouse_data.get("Склад", ""))
                
                for item in warehouse_data.get("Остатки", []):
                    try:
                        # Обработка стоимости - может быть строкой с запятой
                        cost_value = item.get("Стоимость", 0)
                        if isinstance(cost_value, str):
                            cost_value = cost_value.replace(",", "").replace(" ", "")
                        cost = float(cost_value) if cost_value else 0
                        
                        all_stock.append({
                            "branch": branch,
                            "product": item.get("Номенклатура", ""),
                            "article": item.get("Артикул", ""),
                            "quantity": float(item.get("Количество", 0)),
                            "cost": cost,
                            "category_path": item.get("ПутьКатегорий", ""),
                            "unit": item.get("ЕдиницаИзмерения", "шт")
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Ошибка обработки товара: {e}, данные: {item}")
                        continue
        else:
            print(f"Не найдена структура 'ОстаткиПоСкладам' в JSON. Доступные ключи: {list(stock_json.keys())}")
    except Exception as e:
        print(f"Общая ошибка парсинга остатков: {e}")
    
    return pd.DataFrame(all_stock)

def parse_sales_data(sales_json):
    """Парсинг данных о продажах из JSON и определение периода"""
    all_sales = []
    period_start = None
    period_end = None
    
    # Проверяем, является ли это массивом филиалов
    if isinstance(sales_json, list):
        for branch_data in sales_json:
            branch = normalize_branch_name(branch_data.get("Филиал", ""))
            
            # Определяем период из данных
            if "НачалоПериода" in branch_data and "КонецПериода" in branch_data:
                start = pd.to_datetime(branch_data["НачалоПериода"])
                end = pd.to_datetime(branch_data["КонецПериода"])
                
                if period_start is None or start < period_start:
                    period_start = start
                if period_end is None or end > period_end:
                    period_end = end
            
            # Обработка продаж по дням или общих продаж
            if "ПродажиПоДням" in branch_data:
                # Суммируем продажи по всем дням
                daily_sales = {}
                for date, sales in branch_data["ПродажиПоДням"].items():
                    for sale in sales:
                        key = (sale.get("Номенклатура", ""), sale.get("Артикул", ""))
                        if key not in daily_sales:
                            daily_sales[key] = {
                                "product": sale.get("Номенклатура", ""),
                                "article": sale.get("Артикул", ""),
                                "quantity": 0,
                                "revenue": 0,
                                "cost": 0,
                                "category_path": sale.get("ПутьКатегорий", ""),
                                "unit": sale.get("ЕдиницаИзмерения", "шт")
                            }
                        daily_sales[key]["quantity"] += float(sale.get("Количество", 0))
                        daily_sales[key]["revenue"] += float(sale.get("Выручка", 0))
                        daily_sales[key]["cost"] += float(sale.get("Себестоимость", 0))
                
                for item_data in daily_sales.values():
                    all_sales.append({
                        "branch": branch,
                        **item_data
                    })
            
            elif "Продажи" in branch_data:
                # Обработка общих продаж
                for sale in branch_data["Продажи"]:
                    all_sales.append({
                        "branch": branch,
                        "product": sale.get("Номенклатура", ""),
                        "article": sale.get("Артикул", ""),
                        "quantity": float(sale.get("Количество", 0)),
                        "revenue": float(sale.get("Выручка", 0)),
                        "cost": float(sale.get("Себестоимость", 0)),
                        "category_path": sale.get("ПутьКатегорий", ""),
                        "unit": sale.get("ЕдиницаИзмерения", "шт")
                    })
    
    # Рассчитываем период в днях
    period_days = 30  # по умолчанию
    if period_start and period_end:
        period_days = (period_end - period_start).days + 1
    
    return pd.DataFrame(all_sales), period_days

def calculate_simple_ads_from_sales(sales_df, period_days=30):
    """Простой расчет ADS из файла продаж"""
    print(f"Расчет ADS из {len(sales_df)} продаж за {period_days} дней")
    
    if sales_df.empty:
        return pd.DataFrame()
    
    # Группируем по филиалам и товарам
    ads_data = []
    
    for branch in sales_df['branch'].unique():
        branch_sales = sales_df[sales_df['branch'] == branch]
        
        for _, sale in branch_sales.iterrows():
            # ADS = среднедневное количество продаж
            daily_quantity = sale['quantity'] / period_days
            
            ads_data.append({
                'Филиал': branch,
                'Товар': sale['product'],
                'Артикул': sale['article'], 
                'Продано за период': sale['quantity'],
                'Себестоимость за период': sale['cost'],
                'ADS (шт/день)': round(daily_quantity, 2),
                'Категория': sale.get('category_path', '').split('/')[0] if sale.get('category_path') else 'Без категории'
            })
    
    ads_df = pd.DataFrame(ads_data)
    
    if not ads_df.empty:
        # Сортируем по ADS по убыванию
        ads_df = ads_df.sort_values('ADS (шт/день)', ascending=False)
        total_ads = ads_df['ADS (шт/день)'].sum()
        print(f"✅ Общий ADS системы: {total_ads:.2f} шт/день")
    
    return ads_df

def calculate_turnover_and_ads(stock_df, sales_df, period_days=30):
    """Старая функция для совместимости с рекомендациями"""
    print(f"Расчет оборачиваемости для {len(stock_df)} остатков и {len(sales_df)} продаж за {period_days} дней")
    
    # Группируем продажи по филиалу и артикулу
    sales_grouped = sales_df.groupby(['branch', 'article']).agg({
        'quantity': 'sum',
        'cost': 'sum'  
    }).reset_index()
    
    # Объединяем с остатками
    merged = pd.merge(stock_df, sales_grouped, on=['branch', 'article'], how='left')
    
    # Заполняем пропуски
    merged['quantity_y'] = merged['quantity_y'].fillna(0)  # продажи
    merged['cost_y'] = merged['cost_y'].fillna(0)  # себестоимость продаж
    
    # Переименовываем для ясности
    merged.rename(columns={
        'quantity_x': 'quantity',  # остатки
        'cost_x': 'cost',          # стоимость остатков  
        'quantity_y': 'sales_qty', # количество продаж
        'cost_y': 'sales_cost'     # себестоимость продаж
    }, inplace=True)
    
    # Рассчитываем ADS
    merged['daily_sales_qty'] = merged['sales_qty'] / period_days
    merged['daily_sales_cost'] = merged['sales_cost'] / period_days  
    merged['ads'] = merged['daily_sales_cost']  # ADS = среднедневная себестоимость
    
    # Оборачиваемость
    merged['turnover_days'] = np.where(
        merged['daily_sales_qty'] > 0,
        merged['quantity'] / merged['daily_sales_qty'],
        999
    )
    
    return merged

def generate_movement_recommendations(stock_df, sales_df, period_days=30, 
                                    hub_min_days=60, hub_max_days=180,
                                    warehouse_min_days=30, warehouse_max_days=90,
                                    store_min_days=14, store_max_days=45):
    """Генерация рекомендаций по перемещениям с учетом иерархии"""
    
    print(f"Начинаем расчет оборачиваемости и ADS для {len(stock_df)} остатков и {len(sales_df)} продаж")
    
    # Рассчитываем оборачиваемость и ADS одновременно
    turnover_df = calculate_turnover_and_ads(stock_df, sales_df, period_days)
    
    # Предварительная фильтрация - оставляем только товары с остатками или продажами
    turnover_df = turnover_df[(turnover_df['quantity'] > 0) | (turnover_df['sales_qty'] > 0)]
    print(f"После фильтрации осталось {len(turnover_df)} записей")
    print(f"Всего ADS по системе: {turnover_df['ads'].sum():.2f} тенге/день")
    
    recommendations = []
    unique_articles = turnover_df['article'].unique()
    
    print(f"Анализируем {len(unique_articles)} уникальных товаров...")
    
    # Ограничиваем количество товаров для анализа
    max_articles = 200  # Увеличиваем до 200 товаров
    start_time = time.time()
    timeout_seconds = 30  # 30 секунд максимум
    
    # Группируем по товарам
    for i, article in enumerate(unique_articles[:max_articles]):
        # Проверяем таймаут
        if time.time() - start_time > timeout_seconds:
            print(f"⚠️ Таймаут: анализ прерван после {timeout_seconds} секунд на товаре {i}")
            break
        if i % 5 == 0:  # Выводим прогресс каждые 5 товаров
            print(f"Обработано {i}/{min(max_articles, len(unique_articles))} товаров")
            
        article_data = turnover_df[turnover_df['article'] == article]
        
        # Пропускаем товары без остатков
        if article_data['quantity'].sum() == 0:
            continue
        
        # Определяем филиалы с избытком и дефицитом
        excess_branches = []
        deficit_branches = []
        
        for _, row in article_data.iterrows():
            branch_type = get_branch_type(row['branch'])
            
            # Преобразуем pandas Series в словарь для избежания проблем с итерацией
            row_dict = row.to_dict()
            
            # Критерии для разных типов филиалов
            if branch_type == "хаб":
                # 🏢 Главный хаб
                if row['turnover_days'] < hub_min_days and row['daily_sales_qty'] > 0:
                    deficit_branches.append(row_dict)
                elif row['turnover_days'] > hub_max_days:
                    excess_branches.append(row_dict)
            
            elif branch_type == "склад":
                # 📦 Склады 2-го уровня
                if row['turnover_days'] < warehouse_min_days and row['daily_sales_qty'] > 0:
                    deficit_branches.append(row_dict)
                elif row['turnover_days'] > warehouse_max_days:
                    excess_branches.append(row_dict)
            
            elif branch_type in ["магазин_от_хаба", "магазин_3_уровня"]:
                # 🏪 Магазины (напрямую от хаба или 3-го уровня)
                if row['turnover_days'] < store_min_days and row['daily_sales_qty'] > 0:
                    deficit_branches.append(row_dict)
                elif row['turnover_days'] > store_max_days:
                    excess_branches.append(row_dict)
        
        # НОВАЯ ЛОГИКА: анализируем потребности и распределяем избытки
        try:
            print(f"  Товар {article}: найдено {len(deficit_branches)} дефицитных и {len(excess_branches)} избыточных филиалов")
            
            # 1. Сначала обрабатываем все филиалы с избытком
            for excess in excess_branches:
                excess_type = get_branch_type(excess['branch'])
                available_qty = excess['quantity']
                
                # Минимум для перемещения
                if available_qty < 5:
                    continue
                
                # Ищем кому нужен этот товар (приоритет по типу филиала)
                needs_fulfilled = False
                
                # Приоритет 1: Сначала проверяем дочерние филиалы (если отправитель - родитель)
                if excess_type in ["хаб", "склад"]:
                    for deficit in deficit_branches:
                        deficit_type = get_branch_type(deficit['branch'])
                        parent = get_parent_warehouse(deficit['branch'])
                        
                        # Если дефицитный филиал - дочерний для текущего избыточного
                        if parent == excess['branch']:
                            # Рассчитываем потребность
                            target_days = 30 if deficit_type == "склад" else 21
                            needed_qty = max(5, int(deficit['daily_sales_qty'] * target_days - deficit['quantity']))
                            transfer_qty = min(needed_qty, int(available_qty * 0.4))  # До 40% от избытка
                            
                            if transfer_qty >= 5:
                                reason = f"Пополнение дочернего {deficit_type} от {excess_type}. "
                                reason += f"Получатель: {deficit['turnover_days']:.0f} дней (нехватка), "
                                reason += f"отправитель: {excess['turnover_days']:.0f} дней (избыток)"
                                
                                recommendations.append({
                                    'from_branch': excess['branch'],
                                    'to_branch': deficit['branch'],
                                    'article': excess.get('article', article),
                                    'product': deficit['product'],
                                    'quantity': transfer_qty,
                                    'reason': reason,
                                    'current_turnover_from': excess['turnover_days'],
                                    'current_turnover_to': deficit['turnover_days'],
                                    'improvement_days': (transfer_qty / deficit['daily_sales_qty']) if deficit['daily_sales_qty'] > 0 else 0,
                                    'priority': 'high'
                                })
                                available_qty -= transfer_qty
                                needs_fulfilled = True
                                break
                
                # Приоритет 2: Если еще есть избыток, ищем среди филиалов одного уровня
                if available_qty >= 5 and not needs_fulfilled:
                    for deficit in deficit_branches:
                        deficit_type = get_branch_type(deficit['branch'])
                        
                        # Перемещения между равными уровнями
                        if (deficit_type == excess_type and 
                            deficit['turnover_days'] < 15 and  # Острая нехватка
                            excess['turnover_days'] > 90):     # Значительный избыток
                            
                            needed_qty = max(5, int(deficit['daily_sales_qty'] * 21))
                            transfer_qty = min(needed_qty, int(available_qty * 0.3))
                            
                            if transfer_qty >= 5:
                                reason = f"Перемещение между {excess_type}. "
                                reason += f"Получатель: острая нехватка ({deficit['turnover_days']:.0f} дней), "
                                reason += f"отправитель: избыток ({excess['turnover_days']:.0f} дней)"
                                
                                recommendations.append({
                                    'from_branch': excess['branch'],
                                    'to_branch': deficit['branch'],
                                    'article': excess.get('article', article),
                                    'product': deficit['product'],
                                    'quantity': transfer_qty,
                                    'reason': reason,
                                    'current_turnover_from': excess['turnover_days'],
                                    'current_turnover_to': deficit['turnover_days'],
                                    'improvement_days': (transfer_qty / deficit['daily_sales_qty']) if deficit['daily_sales_qty'] > 0 else 0,
                                    'priority': 'medium'
                                })
                                available_qty -= transfer_qty
                                needs_fulfilled = True
                                break
                
                # Приоритет 3: Если товар все еще никому не нужен - отправляем в хаб
                hub_name = WAREHOUSE_HIERARCHY["hub"]
                if (available_qty >= 10 and not needs_fulfilled and 
                    excess['branch'] != hub_name and  # Не отправляем из хаба в хаб
                    excess['turnover_days'] > 120):   # Только при большом избытке
                    
                    # Отправляем в хаб максимум 50% от избытка
                    return_qty = min(int(available_qty * 0.5), int(excess['quantity'] * 0.5))
                    
                    if return_qty >= 10:
                        reason = f"Возврат неликвидного товара в хаб. "
                        reason += f"У отправителя ({excess_type}) избыток {excess['turnover_days']:.0f} дней, "
                        reason += f"товар не требуется другим филиалам"
                        
                        recommendations.append({
                            'from_branch': excess['branch'],
                            'to_branch': hub_name,
                            'article': excess.get('article', article),
                            'product': excess['product'],
                            'quantity': return_qty,
                            'reason': reason,
                            'current_turnover_from': excess['turnover_days'],
                            'current_turnover_to': 999,  # Хаб не продает напрямую
                            'improvement_days': 0,
                            'priority': 'low'
                        })
        
        except Exception as e:
            print(f"  Ошибка при обработке товара {article}: {e}")
            continue
    
    print(f"Анализ завершен. Создано {len(recommendations)} рекомендаций.")
    return recommendations, turnover_df

def main():
    st.title("🔄 Межфилиальные перемещения")
    st.markdown("*Анализ и рекомендации по оптимизации товарных запасов между филиалами*")
    
    # Загрузка файлов
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Загрузка данных об остатках")
        st.info("📋 Файл остатков должен содержать структуру 'ОстаткиПоСкладам'")
        stock_file = st.file_uploader(
            "Выберите файл остатков (JSON)",
            type=['json'],
            key="stock_file",
            help="Например: 2025-06-30 (4).json - файл с остатками"
        )
    
    with col2:
        st.subheader("📁 Загрузка данных о продажах")
        st.info("📋 Файл продаж должен содержать массив филиалов с 'Продажи'")
        sales_file = st.file_uploader(
            "Выберите файл продаж (JSON)",
            type=['json'],
            key="sales_file",
            help="Например: 2025-06-30.json - файл с продажами"
        )
    
    # Параметры анализа
    with st.expander("⚙️ Настройки оборачиваемости (в днях)", expanded=True):
        st.markdown("### 🏢 Настройки для главного хаба")
        col1, col2 = st.columns(2)
        with col1:
            hub_min_days = st.number_input("Минимум дней запаса", value=60, min_value=30, max_value=180, key="hub_min")
        with col2:
            hub_max_days = st.number_input("Максимум дней запаса", value=180, min_value=90, max_value=365, key="hub_max")
        
        st.markdown("### 📦 Настройки для складов 2-го уровня")
        col1, col2 = st.columns(2)
        with col1:
            warehouse_min_days = st.number_input("Минимум дней запаса", value=30, min_value=14, max_value=90, key="wh_min")
        with col2:
            warehouse_max_days = st.number_input("Максимум дней запаса", value=90, min_value=45, max_value=180, key="wh_max")
        
        st.markdown("### 🏪 Настройки для магазинов")
        col1, col2 = st.columns(2)
        with col1:
            store_min_days = st.number_input("Минимум дней запаса", value=14, min_value=7, max_value=30, key="store_min")
        with col2:
            store_max_days = st.number_input("Максимум дней запаса", value=45, min_value=30, max_value=90, key="store_max")
    

    if stock_file and sales_file:
        # Загружаем данные
        stock_json = load_json_file(stock_file)
        sales_json = load_json_file(sales_file)
        
        if stock_json and sales_json:
            # Парсим данные
            stock_df = parse_stock_data(stock_json)
            sales_df, detected_period_days = parse_sales_data(sales_json)
            
            # Отладка - показываем что получилось
            st.write("**Отладка парсинга:**")
            st.write(f"Stock DataFrame columns: {list(stock_df.columns) if not stock_df.empty else 'ПУСТОЙ'}")
            st.write(f"Stock DataFrame shape: {stock_df.shape}")
            st.write(f"Sales DataFrame columns: {list(sales_df.columns) if not sales_df.empty else 'ПУСТОЙ'}")
            st.write(f"Sales DataFrame shape: {sales_df.shape}")
            
            if stock_df.empty:
                st.error("❌ Данные об остатках не найдены или не распознаны")
                
                # Проверяем, не загружен ли файл продаж вместо остатков
                if isinstance(stock_json, list) and len(stock_json) > 0:
                    if "Продажи" in stock_json[0]:
                        st.warning("⚠️ Похоже, вы загрузили файл ПРОДАЖ в поле для остатков. Загрузите файл остатков (должен содержать 'ОстаткиПоСкладам')")
                        return
                
                st.write("**Структура загруженного файла остатков:**")
                if isinstance(stock_json, dict):
                    st.write(f"Ключи в JSON: {list(stock_json.keys())}")
                elif isinstance(stock_json, list):
                    st.write(f"Это массив из {len(stock_json)} элементов")
                    if len(stock_json) > 0:
                        st.write(f"Ключи первого элемента: {list(stock_json[0].keys()) if isinstance(stock_json[0], dict) else 'не объект'}")
                
                return
            
            if sales_df.empty:
                st.error("❌ Данные о продажах не найдены или не распознаны")
                st.json(sales_json)  # Показываем структуру
                return
            
            # Показываем статистику
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📦 Филиалов", stock_df['branch'].nunique())
            
            with col2:
                st.metric("🏷️ Товаров", stock_df['article'].nunique())
            
            with col3:
                st.metric("📊 Общий остаток", f"{stock_df['quantity'].sum():,.0f} шт")
            
            with col4:
                st.metric("💰 Стоимость остатков", f"{stock_df['cost'].sum():,.0f} ₸")
                
            with col5:
                st.metric("📅 Период", f"{detected_period_days} дней")
            
            # Инициализируем переменные для использования во всех табах
            recommendations = []
            turnover_df = pd.DataFrame()
            
            # Генерируем рекомендации
            with st.spinner("Анализ оптимальных перемещений..."):
                try:
                    st.write(f"Начинаем анализ для {stock_df.shape[0]} остатков и {sales_df.shape[0]} продаж...")
                    
                    recommendations, turnover_df = generate_movement_recommendations(
                        stock_df, sales_df, detected_period_days,
                        hub_min_days, hub_max_days,
                        warehouse_min_days, warehouse_max_days,
                        store_min_days, store_max_days
                    )
                    
                    st.write(f"Анализ завершен, найдено {len(recommendations)} рекомендаций")
                    
                except Exception as e:
                    st.error(f"Ошибка при анализе: {str(e)}")
                    # Даже при ошибке пытаемся рассчитать базовые ADS данные
                    try:
                        turnover_df = calculate_turnover_and_ads(stock_df, sales_df, detected_period_days)
                        st.info("Базовые ADS данные рассчитаны, несмотря на ошибку в рекомендациях")
                    except:
                        pass
                    return
            
            st.write(f"🔍 Отладка: получено {len(recommendations) if recommendations else 0} рекомендаций")
            
            if recommendations:
                st.success(f"✅ Найдено {len(recommendations)} рекомендаций по перемещению")
                
                # Вкладки для разных представлений
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    "📊 Сводка рекомендаций",
                    "📋 Детальный список", 
                    "🗺️ Визуализация",
                    "📈 Анализ по филиалам",
                    "🔄 ABC анализ по категориям",
                    "🏢 Оборачиваемость складов",
                    "💰 ADS анализ"
                ])
                
                with tab1:
                    # Общая статистика
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📋 Всего рекомендаций", len(recommendations))
                    
                    with col2:
                        total_quantity = sum(r['quantity'] for r in recommendations)
                        st.metric("📦 Общий объем", f"{total_quantity:,} единиц")
                    
                    with col3:
                        unique_routes = len(set(f"{r['from_branch']} → {r['to_branch']}" for r in recommendations))
                        st.metric("🔄 Уникальных маршрутов", unique_routes)
                    
                    # Топ маршруты
                    st.markdown("### 🏆 Топ маршруты по количеству перемещений")
                    routes = {}
                    for rec in recommendations:
                        route = f"{rec['from_branch']} → {rec['to_branch']}"
                        if route not in routes:
                            routes[route] = {'count': 0, 'quantity': 0}
                        routes[route]['count'] += 1
                        routes[route]['quantity'] += rec['quantity']
                    
                    routes_df = pd.DataFrame([
                        {'Маршрут': k, 'Позиций': v['count'], 'Товаров': v['quantity']}
                        for k, v in sorted(routes.items(), key=lambda x: x[1]['quantity'], reverse=True)[:10]
                    ])
                    
                    st.dataframe(routes_df, use_container_width=True, hide_index=True)
                
                with tab2:
                    # Детальный список рекомендаций
                    st.markdown("### 📋 Детальные рекомендации по перемещению")
                    
                    # Фильтры
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        all_from = list(set(r['from_branch'] for r in recommendations))
                        selected_from = st.multiselect("Откуда", all_from, default=all_from)
                    
                    with col2:
                        all_to = list(set(r['to_branch'] for r in recommendations))
                        selected_to = st.multiselect("Куда", all_to, default=all_to)
                    
                    # Фильтрация
                    filtered_recs = [
                        r for r in recommendations
                        if r['from_branch'] in selected_from 
                        and r['to_branch'] in selected_to
                    ]
                    
                    # Создаем DataFrame
                    if filtered_recs:
                        df_recs = pd.DataFrame(filtered_recs)
                        
                        # Форматируем для отображения
                        display_df = df_recs[[
                            'from_branch', 'to_branch', 'product', 
                            'quantity', 'reason', 'improvement_days'
                        ]].copy()
                        
                        display_df.columns = [
                            'Откуда', 'Куда', 'Товар', 
                            'Кол-во', 'Причина', 'Улучшение (дней)'
                        ]
                        
                        st.dataframe(
                            display_df, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "Причина": st.column_config.TextColumn(
                                    "Причина",
                                    width="large",
                                    help="Подробное описание причины рекомендации"
                                ),
                                "Товар": st.column_config.TextColumn(
                                    "Товар",
                                    width="medium"
                                ),
                                "Откуда": st.column_config.TextColumn(
                                    "Откуда",
                                    width="medium"
                                ),
                                "Куда": st.column_config.TextColumn(
                                    "Куда", 
                                    width="medium"
                                )
                            }
                        )
                        
                        # Экспорт в Excel
                        if st.button("📥 Скачать рекомендации (Excel)"):
                            output = pd.ExcelWriter('Межфилиальные_перемещения.xlsx', engine='xlsxwriter')
                            display_df.to_excel(output, sheet_name='Рекомендации', index=False)
                            
                            workbook = output.book
                            worksheet = output.sheets['Рекомендации']
                            
                            # Автоподбор ширины
                            for i, col in enumerate(display_df.columns):
                                max_len = max(
                                    display_df[col].astype(str).str.len().max(),
                                    len(col)
                                ) + 2
                                worksheet.set_column(i, i, max_len)
                            
                            output.close()
                            
                            with open('Межфилиальные_перемещения.xlsx', 'rb') as f:
                                st.download_button(
                                    label="📥 Скачать Excel",
                                    data=f.read(),
                                    file_name=f"Межфилиальные_перемещения_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                
                with tab3:
                    # Простая схема работы рекомендаций
                    st.markdown("### 🗺️ Схема рекомендаций по перемещениям")
                    
                    if recommendations:
                        # Анализируем типы перемещений
                        movement_types = {
                            'Пополнение нуждающихся': 0,
                            'Перемещение между равными': 0,
                            'Возврат неликвида в хаб': 0
                        }
                        
                        for rec in recommendations:
                            reason = rec['reason']
                            if 'Пополнение дочернего' in reason:
                                movement_types['Пополнение нуждающихся'] += 1
                            elif 'Перемещение между' in reason:
                                movement_types['Перемещение между равными'] += 1
                            elif 'Возврат неликвидного' in reason:
                                movement_types['Возврат неликвида в хаб'] += 1
                        
                        # Диаграмма типов перемещений
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=list(movement_types.keys()),
                                    y=list(movement_types.values()),
                                    marker_color=['#2E86AB', '#A23B72', '#F18F01'],
                                    text=list(movement_types.values()),
                                    textposition='auto'
                                )
                            ])
                            
                            fig.update_layout(
                                title="Типы рекомендаций",
                                height=400,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # Схема иерархии (текстовая)
                            st.markdown("""
                            ### 📋 Схема складской иерархии
                            
                            **🏢 ГЛАВНЫЙ ХАБ**
                            - База Склад Фурнитура Комплект (г.Алматы) - пополняет все склады 2-го уровня
                            
                            **📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба):**
                            1. Казыбаева Склад Фурнитура TRADE (г.Алматы) → пополняет магазин Казыбаева
                            2. склад фурнитура № 1 (г.Астана) → пополняет Магазин фурнитуры
                            3. 4 Склад фурнитуры АЗМ Шымкент (г.Шымкент) → пополняет магазин в Шымкенте
                            
                            **🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов):**
                            - Барыс Склад Фурнитура TRADE (г.Алматы)
                            - АО Склад Фурнитура TRADE (г.Алматы) - Алтын Орда
                            
                            **🏪 МАГАЗИНЫ 3-ГО УРОВНЯ (питаются от складов 2-го уровня):**
                            1. ТД Казыбаева ФУРНИТУРА магазин ← от Казыбаева склад
                            2. Магазин фурнитуры (г.Астана) ← от склад № 1
                            3. 6 Склад фурнитуры "Овощная база" Магазин ← от Шымкент склад
                            """)
                        
                        # Топ направлений
                        st.markdown("### 🎯 Топ направлений перемещений")
                        
                        # Группируем по направлениям
                        directions = {}
                        for rec in recommendations:
                            from_short = rec['from_branch'].split()[0]
                            to_short = rec['to_branch'].split()[0] 
                            direction = f"{from_short} → {to_short}"
                            if direction not in directions:
                                directions[direction] = {'count': 0, 'total_qty': 0}
                            directions[direction]['count'] += 1
                            directions[direction]['total_qty'] += rec['quantity']
                        
                        # Сортируем по количеству товара
                        top_directions = sorted(directions.items(), key=lambda x: x[1]['total_qty'], reverse=True)[:5]
                        
                        for i, (direction, data) in enumerate(top_directions, 1):
                            st.markdown(f"""
                            **{i}. {direction}**
                            - Рекомендаций: {data['count']} | Объем: {data['total_qty']} единиц
                            """)
                    
                    else:
                        st.info("Нет рекомендаций для отображения схемы")
                
                with tab4:
                    # Анализ по филиалам
                    st.markdown("### 📈 Анализ загруженности филиалов")
                    
                    # Собираем статистику по филиалам
                    branch_stats = []
                    
                    for branch in stock_df['branch'].unique():
                        branch_stock = stock_df[stock_df['branch'] == branch]
                        branch_sales = sales_df[sales_df['branch'] == branch] if not sales_df.empty else pd.DataFrame()
                        
                        outgoing = sum(r['quantity'] for r in recommendations if r['from_branch'] == branch)
                        incoming = sum(r['quantity'] for r in recommendations if r['to_branch'] == branch)
                        
                        branch_stats.append({
                            'Филиал': branch,
                            'Тип': get_branch_type(branch),
                            'Товаров': branch_stock['article'].nunique(),
                            'Остаток': branch_stock['quantity'].sum(),
                            'Продажи за период': branch_sales['quantity'].sum() if not branch_sales.empty else 0,
                            'К отправке': outgoing,
                            'К получению': incoming,
                            'Баланс': incoming - outgoing
                        })
                    
                    stats_df = pd.DataFrame(branch_stats)
                    
                    # Сортируем по типу и названию
                    type_order = {'hub': 0, 'warehouse': 1, 'store': 2, 'unknown': 3}
                    stats_df['sort_order'] = stats_df['Тип'].map(type_order)
                    stats_df = stats_df.sort_values(['sort_order', 'Филиал']).drop('sort_order', axis=1)
                    
                    # Форматируем числа
                    for col in ['Остаток', 'Продажи за период', 'К отправке', 'К получению', 'Баланс']:
                        stats_df[col] = stats_df[col].apply(lambda x: f"{int(x):,}")
                    
                    st.dataframe(
                        stats_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Баланс": st.column_config.TextColumn(
                                "Баланс",
                                help="Положительный - получает больше, отрицательный - отдает больше"
                            )
                        }
                    )
                
                with tab5:
                    # Анализ оборачиваемости по категориям
                    st.markdown("### 🔄 Оборачиваемость по категориям")
                    
                    # Выбор филиала для анализа
                    available_branches = ['Все филиалы'] + list(stock_df['branch'].unique()) if not stock_df.empty else ['Все филиалы']
                    selected_branch = st.selectbox(
                        "Выберите филиал для анализа:",
                        available_branches,
                        key="branch_selector"
                    )
                    
                    if not stock_df.empty and not sales_df.empty:
                        # Извлекаем категории из пути категорий
                        def extract_main_category(path):
                            if pd.isna(path) or path == "":
                                return "Без категории"
                            parts = str(path).split('/')
                            return parts[0] if parts and parts[0] else "Без категории"
                        
                        # Добавляем категории к данным
                        stock_with_cat = stock_df.copy()
                        sales_with_cat = sales_df.copy()
                        
                        # Фильтруем по выбранному филиалу
                        if selected_branch != 'Все филиалы':
                            stock_with_cat = stock_with_cat[stock_with_cat['branch'] == selected_branch]
                            sales_with_cat = sales_with_cat[sales_with_cat['branch'] == selected_branch]
                        
                        stock_with_cat['category'] = stock_with_cat['category_path'].apply(extract_main_category)
                        sales_with_cat['category'] = sales_with_cat['category_path'].apply(extract_main_category)
                        
                        # Рассчитываем продажи по себестоимости 
                        # В данных продаж используем поле 'cost' (себестоимость)
                        sales_cost = sales_with_cat.groupby(['category']).agg({
                            'cost': 'sum',     # Себестоимость продаж (аналог ПРОДАЖИ!AB:AB)
                            'revenue': 'sum',  # Выручка
                            'quantity': 'sum'  # Количество
                        }).reset_index()
                        
                        # Рассчитываем остатки по себестоимости
                        # В данных остатков используем поле 'cost' (стоимость остатков)
                        stock_cost = stock_with_cat.groupby(['category']).agg({
                            'cost': 'sum',     # Стоимость остатков (аналог ОСТАТКИ!AE:AE)
                            'quantity': 'sum'  # Количество остатков
                        }).reset_index()
                        
                        # ABC анализ товаров по оборачиваемости
                        def calculate_abc_analysis():
                            # Группируем товары по категориям и филиалам для ABC анализа
                            product_analysis = []
                            
                            for category in sorted(stock_with_cat['category'].unique()):
                                cat_stock = stock_with_cat[stock_with_cat['category'] == category]
                                cat_sales = sales_with_cat[sales_with_cat['category'] == category]
                                
                                for _, stock_item in cat_stock.iterrows():
                                    article = stock_item['article']
                                    branch = stock_item['branch']
                                    
                                    # Находим продажи этого товара в этом филиале
                                    sales_item = cat_sales[
                                        (cat_sales['article'] == article) & 
                                        (cat_sales['branch'] == branch)
                                    ]
                                    
                                    sales_cost = sales_item['cost'].sum() if not sales_item.empty else 0
                                    stock_cost = stock_item['cost']
                                    
                                    # Оборачиваемость в днях
                                    if sales_cost > 0:
                                        turnover_days = int((stock_cost / sales_cost) * detected_period_days)
                                    else:
                                        turnover_days = 999
                                    
                                    product_analysis.append({
                                        'category': category,
                                        'article': article,
                                        'branch': branch,
                                        'sales_cost': sales_cost,
                                        'stock_cost': stock_cost,
                                        'turnover_days': turnover_days
                                    })
                            
                            # Создаем DataFrame для анализа
                            products_df = pd.DataFrame(product_analysis)
                            
                            # ABC классификация по оборачиваемости
                            def classify_abc(turnover):
                                if turnover <= 90:
                                    return 'A'
                                elif turnover <= 180:
                                    return 'B'
                                else:
                                    return 'C'
                            
                            products_df['abc_class'] = products_df['turnover_days'].apply(classify_abc)
                            
                            return products_df
                        
                        products_df = calculate_abc_analysis()
                        
                        # Статистика по категориям с разбивкой по ABC
                        category_summary = []
                        
                        for category in sorted(stock_with_cat['category'].unique()):
                            cat_products = products_df[products_df['category'] == category]
                            
                            # Общие итоги по категории
                            total_sales_cost = cat_products['sales_cost'].sum()
                            total_stock_cost = cat_products['stock_cost'].sum()
                            total_turnover = int((total_stock_cost / total_sales_cost) * detected_period_days) if total_sales_cost > 0 else 999
                            
                            # Процент от общих продаж и остатков
                            total_all_sales = products_df['sales_cost'].sum()
                            total_all_stock = products_df['stock_cost'].sum()
                            sales_pct = (total_sales_cost / total_all_sales * 100) if total_all_sales > 0 else 0
                            stock_pct = (total_stock_cost / total_all_stock * 100) if total_all_stock > 0 else 0
                            
                            # ABC разбивка
                            abc_data = []
                            for abc_class in ['A', 'B', 'C']:
                                abc_products = cat_products[cat_products['abc_class'] == abc_class]
                                
                                abc_sales = abc_products['sales_cost'].sum()
                                abc_stock = abc_products['stock_cost'].sum()
                                abc_pct = (abc_sales / total_sales_cost * 100) if total_sales_cost > 0 else 0
                                abc_turnover = int((abc_stock / abc_sales) * detected_period_days) if abc_sales > 0 else 999
                                
                                abc_data.extend([
                                    f"{abc_sales:,.0f}",     # Продажи
                                    f"{abc_stock:,.0f}",     # Остатки
                                    f"{abc_pct:.0f}%",       # % от категории
                                    f"{abc_turnover}"        # Оборачиваемость
                                ])
                            
                            category_summary.append([
                                category,
                                f"{total_sales_cost:,.0f}",  # Общие продажи
                                f"{sales_pct:.1f}%",         # % продаж
                                f"{total_stock_cost:,.0f}",  # Общие остатки
                                f"{stock_pct:.1f}%",         # % остатков
                                f"{total_turnover}"          # Общая оборачиваемость
                            ] + abc_data)
                        
                        # Создаем DataFrame для отображения
                        columns = ['КАТЕГОРИИ', 'ПРОДАЖИ по Себ.Ст', 'ПРОДАЖИ %', 'ОСТАТКИ по Себ.Ст.', 'ОСТАТКИ %', 'ОБОРАЧИВАЕМОСТЬ (дн.)']
                        
                        # Добавляем колонки ABC
                        for abc_class in ['A', 'B', 'C']:
                            columns.extend([
                                f'{abc_class}_ПРОД',
                                f'{abc_class}_ОСТАТ', 
                                f'{abc_class}_%',
                                f'{abc_class}_ОБОР'
                            ])
                        
                        summary_df = pd.DataFrame(category_summary, columns=columns)
                        
                        # Отображаем информацию о выбранном филиале
                        if selected_branch != 'Все филиалы':
                            st.info(f"📍 Анализ для филиала: **{selected_branch}**")
                        else:
                            st.info("📍 Анализ по всем филиалам")
                        
                        # Информация об ABC классификации
                        st.markdown("""
                        **📊 ABC классификация по оборачиваемости:**
                        - **A**: до 90 дней (быстрооборачиваемые)
                        - **B**: 91-180 дней (среднеоборачиваемые)  
                        - **C**: свыше 180 дней (медленнооборачиваемые)
                        """)
                        
                        # Отображаем таблицу с прокруткой по горизонтали
                        st.dataframe(
                            summary_df,
                            use_container_width=True,
                            hide_index=True,
                            height=600,
                            column_config={
                                "КАТЕГОРИИ": st.column_config.TextColumn(
                                    "КАТЕГОРИИ",
                                    width="medium"
                                ),
                                "A_ПРОД": st.column_config.TextColumn("A ПРОД", width="small"),
                                "A_ОСТАТ": st.column_config.TextColumn("A ОСТАТ", width="small"),
                                "A_%": st.column_config.TextColumn("A %", width="small"),
                                "A_ОБОР": st.column_config.TextColumn("A ОБОР", width="small"),
                                "B_ПРОД": st.column_config.TextColumn("B ПРОД", width="small"),
                                "B_ОСТАТ": st.column_config.TextColumn("B ОСТАТ", width="small"),
                                "B_%": st.column_config.TextColumn("B %", width="small"),
                                "B_ОБОР": st.column_config.TextColumn("B ОБОР", width="small"),
                                "C_ПРОД": st.column_config.TextColumn("C ПРОД", width="small"),
                                "C_ОСТАТ": st.column_config.TextColumn("C ОСТАТ", width="small"),
                                "C_%": st.column_config.TextColumn("C %", width="small"),
                                "C_ОБОР": st.column_config.TextColumn("C ОБОР", width="small")
                            }
                        )
                        
                        # ABC статистика
                        st.markdown("### 📊 ABC статистика")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        # Считаем общую статистику по ABC
                        total_a_sales = products_df[products_df['abc_class'] == 'A']['sales_cost'].sum()
                        total_b_sales = products_df[products_df['abc_class'] == 'B']['sales_cost'].sum()
                        total_c_sales = products_df[products_df['abc_class'] == 'C']['sales_cost'].sum()
                        total_sales = products_df['sales_cost'].sum()
                        
                        total_a_stock = products_df[products_df['abc_class'] == 'A']['stock_cost'].sum()
                        total_b_stock = products_df[products_df['abc_class'] == 'B']['stock_cost'].sum()
                        total_c_stock = products_df[products_df['abc_class'] == 'C']['stock_cost'].sum()
                        total_stock = products_df['stock_cost'].sum()
                        
                        with col1:
                            st.metric(
                                "🔥 Класс A (быстрые)",
                                f"{total_a_sales / total_sales * 100:.1f}%" if total_sales > 0 else "0%",
                                f"от продаж"
                            )
                            st.write(f"Остатки: {total_a_stock / total_stock * 100:.1f}%" if total_stock > 0 else "Остатки: 0%")
                        
                        with col2:
                            st.metric(
                                "⚡ Класс B (средние)",
                                f"{total_b_sales / total_sales * 100:.1f}%" if total_sales > 0 else "0%",
                                f"от продаж"
                            )
                            st.write(f"Остатки: {total_b_stock / total_stock * 100:.1f}%" if total_stock > 0 else "Остатки: 0%")
                        
                        with col3:
                            st.metric(
                                "🐌 Класс C (медленные)",
                                f"{total_c_sales / total_sales * 100:.1f}%" if total_sales > 0 else "0%",
                                f"от продаж"
                            )
                            st.write(f"Остатки: {total_c_stock / total_stock * 100:.1f}%" if total_stock > 0 else "Остатки: 0%")
                    
                    else:
                        st.info("Недостаточно данных для анализа оборачиваемости по категориям")
                
                with tab6:
                    # Оборачиваемость складов по категориям
                    st.markdown("### 🏢 Оборачиваемость складов по категориям")
                    
                    if not stock_df.empty and not sales_df.empty:
                        # Извлекаем категории из пути категорий
                        def extract_main_category(path):
                            if pd.isna(path) or path == "":
                                return "Без категории"
                            parts = str(path).split('/')
                            return parts[0] if parts and parts[0] else "Без категории"
                        
                        # Подготавливаем данные с категориями
                        stock_cat = stock_df.copy()
                        sales_cat = sales_df.copy()
                        
                        stock_cat['category'] = stock_cat['category_path'].apply(extract_main_category)
                        sales_cat['category'] = sales_cat['category_path'].apply(extract_main_category)
                        
                        # Выбор типа анализа
                        analysis_type = st.radio(
                            "Выберите тип анализа:",
                            ["📊 Общий по всем складам", "🏢 По отдельным филиалам"],
                            horizontal=True
                        )
                        
                        if analysis_type == "📊 Общий по всем складам":
                            # Группируем по категориям (общие итоги по всем складам)
                            category_turnover = []
                            
                            for category in sorted(stock_cat['category'].unique()):
                                cat_stock_data = stock_cat[stock_cat['category'] == category]
                                cat_sales_data = sales_cat[sales_cat['category'] == category]
                                
                                # Суммы по себестоимости
                                total_sales_cost = cat_sales_data['cost'].sum()  # Продажи по себестоимости
                                total_stock_cost = cat_stock_data['cost'].sum()  # Остатки по себестоимости
                                
                                # Оборачиваемость в днях
                                if total_sales_cost > 0:
                                    turnover_days = int((total_stock_cost / total_sales_cost) * detected_period_days)
                                else:
                                    turnover_days = 999
                                
                                category_turnover.append({
                                    'КАТЕГОРИИ': category,
                                    'ПРОД': f"{total_sales_cost:,.0f}",
                                    'ТОТ ОСТ': f"{total_stock_cost:,.0f}",
                                    'ОБОР ДН': turnover_days
                                })
                            
                            # Сортируем по оборачиваемости
                            category_turnover.sort(key=lambda x: x['ОБОР ДН'])
                            
                            # Создаем DataFrame
                            turnover_df = pd.DataFrame(category_turnover)
                            
                            # Рассчитываем итоги
                            total_sales_all = sales_cat['cost'].sum()
                            total_stock_all = stock_cat['cost'].sum()
                            total_turnover_all = int((total_stock_all / total_sales_all) * detected_period_days) if total_sales_all > 0 else 999
                            
                            # Добавляем строку ИТОГО
                            totals_row = pd.DataFrame([{
                                'КАТЕГОРИИ': 'ИТОГО:',
                                'ПРОД': f"{total_sales_all:,.0f}",
                                'ТОТ ОСТ': f"{total_stock_all:,.0f}",
                                'ОБОР ДН': total_turnover_all
                            }])
                            
                            turnover_df = pd.concat([turnover_df, totals_row], ignore_index=True)
                            
                        else:
                            # Анализ по отдельным филиалам
                            available_branches = ['Все филиалы'] + list(stock_cat['branch'].unique())
                            selected_branch = st.selectbox(
                                "Выберите филиал:",
                                available_branches,
                                key="branch_turnover_selector"
                            )
                            
                            if selected_branch == 'Все филиалы':
                                # Показываем все филиалы по отдельности
                                all_branches_data = []
                                
                                for branch in sorted(stock_cat['branch'].unique()):
                                    branch_stock = stock_cat[stock_cat['branch'] == branch]
                                    branch_sales = sales_cat[sales_cat['branch'] == branch]
                                    
                                    for category in sorted(branch_stock['category'].unique()):
                                        cat_stock_data = branch_stock[branch_stock['category'] == category]
                                        cat_sales_data = branch_sales[branch_sales['category'] == category]
                                        
                                        # Суммы по себестоимости
                                        total_sales_cost = cat_sales_data['cost'].sum()
                                        total_stock_cost = cat_stock_data['cost'].sum()
                                        
                                        # Оборачиваемость в днях
                                        if total_sales_cost > 0:
                                            turnover_days = int((total_stock_cost / total_sales_cost) * detected_period_days)
                                        else:
                                            turnover_days = 999
                                        
                                        if total_sales_cost > 0 or total_stock_cost > 0:  # Показываем только если есть данные
                                            all_branches_data.append({
                                                'ФИЛИАЛ': branch,
                                                'КАТЕГОРИИ': category,
                                                'ПРОД': f"{total_sales_cost:,.0f}",
                                                'ТОТ ОСТ': f"{total_stock_cost:,.0f}",
                                                'ОБОР ДН': turnover_days
                                            })
                                
                                turnover_df = pd.DataFrame(all_branches_data)
                                
                            else:
                                # Показываем конкретный филиал
                                branch_stock = stock_cat[stock_cat['branch'] == selected_branch]
                                branch_sales = sales_cat[sales_cat['branch'] == selected_branch]
                                
                                category_turnover = []
                                
                                for category in sorted(branch_stock['category'].unique()):
                                    cat_stock_data = branch_stock[branch_stock['category'] == category]
                                    cat_sales_data = branch_sales[branch_sales['category'] == category]
                                    
                                    # Суммы по себестоимости
                                    total_sales_cost = cat_sales_data['cost'].sum()
                                    total_stock_cost = cat_stock_data['cost'].sum()
                                    
                                    # Оборачиваемость в днях
                                    if total_sales_cost > 0:
                                        turnover_days = int((total_stock_cost / total_sales_cost) * detected_period_days)
                                    else:
                                        turnover_days = 999
                                    
                                    category_turnover.append({
                                        'КАТЕГОРИИ': category,
                                        'ПРОД': f"{total_sales_cost:,.0f}",
                                        'ТОТ ОСТ': f"{total_stock_cost:,.0f}",
                                        'ОБОР ДН': turnover_days
                                    })
                                
                                # Сортируем по оборачиваемости
                                category_turnover.sort(key=lambda x: x['ОБОР ДН'])
                                turnover_df = pd.DataFrame(category_turnover)
                                
                                # Добавляем итоги для филиала
                                total_sales_branch = branch_sales['cost'].sum()
                                total_stock_branch = branch_stock['cost'].sum()
                                total_turnover_branch = int((total_stock_branch / total_sales_branch) * detected_period_days) if total_sales_branch > 0 else 999
                                
                                totals_row = pd.DataFrame([{
                                    'КАТЕГОРИИ': f'ИТОГО ({selected_branch}):',
                                    'ПРОД': f"{total_sales_branch:,.0f}",
                                    'ТОТ ОСТ': f"{total_stock_branch:,.0f}",
                                    'ОБОР ДН': total_turnover_branch
                                }])
                                
                                turnover_df = pd.concat([turnover_df, totals_row], ignore_index=True)
                        
                        # Отображаем таблицу
                        if analysis_type == "🏢 По отдельным филиалам" and selected_branch == 'Все филиалы':
                            # Специальная конфигурация для таблицы с филиалами
                            st.dataframe(
                                turnover_df,
                                use_container_width=True,
                                hide_index=True,
                                height=600,
                                column_config={
                                    "ФИЛИАЛ": st.column_config.TextColumn(
                                        "ФИЛИАЛ",
                                        width="large"
                                    ),
                                    "КАТЕГОРИИ": st.column_config.TextColumn(
                                        "КАТЕГОРИИ",
                                        width="large"
                                    ),
                                    "ПРОД": st.column_config.TextColumn(
                                        "ПРОД",
                                        help="Продажи по себестоимости",
                                        width="medium"
                                    ),
                                    "ТОТ ОСТ": st.column_config.TextColumn(
                                        "ТОТ ОСТ",
                                        help="Остатки по себестоимости",
                                        width="medium"
                                    ),
                                    "ОБОР ДН": st.column_config.NumberColumn(
                                        "ОБОР ДН",
                                        help="Оборачиваемость в днях",
                                        width="small"
                                    )
                                }
                            )
                        else:
                            # Обычная конфигурация для общих данных или отдельного филиала
                            st.dataframe(
                                turnover_df,
                                use_container_width=True,
                                hide_index=True,
                                height=500,
                                column_config={
                                    "КАТЕГОРИИ": st.column_config.TextColumn(
                                        "КАТЕГОРИИ",
                                        width="large"
                                    ),
                                    "ПРОД": st.column_config.TextColumn(
                                        "ПРОД",
                                        help="Продажи по себестоимости",
                                        width="medium"
                                    ),
                                    "ТОТ ОСТ": st.column_config.TextColumn(
                                        "ТОТ ОСТ",
                                        help="Остатки по себестоимости",
                                        width="medium"
                                    ),
                                    "ОБОР ДН": st.column_config.NumberColumn(
                                        "ОБОР ДН",
                                        help="Оборачиваемость в днях",
                                        width="small"
                                    )
                                }
                            )
                        
                        # Дополнительная аналитика только для общих данных или отдельного филиала
                        if analysis_type == "📊 Общий по всем складам" or (analysis_type == "🏢 По отдельным филиалам" and selected_branch != 'Все филиалы'):
                            st.markdown("### 📊 Аналитика по оборачиваемости")
                            
                            # Для анализа используем данные из turnover_df
                            if analysis_type == "📊 Общий по всем складам":
                                analysis_data = category_turnover
                            else:
                                # Для отдельного филиала
                                analysis_data = category_turnover
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**🔥 Быстрооборачиваемые категории (до 120 дней):**")
                                fast_cats = [cat for cat in analysis_data if cat['ОБОР ДН'] <= 120]
                                for cat in fast_cats[:5]:
                                    st.write(f"• {cat['КАТЕГОРИИ']}: {cat['ОБОР ДН']} дней")
                            
                            with col2:
                                st.markdown("**🐌 Медленнооборачиваемые категории (свыше 300 дней):**")
                                slow_cats = [cat for cat in analysis_data if cat['ОБОР ДН'] > 300 and cat['ОБОР ДН'] < 999]
                                slow_cats.sort(key=lambda x: x['ОБОР ДН'], reverse=True)
                                for cat in slow_cats[:5]:
                                    st.write(f"• {cat['КАТЕГОРИИ']}: {cat['ОБОР ДН']} дней")
                            
                            # Общая статистика
                            st.markdown("### 📈 Статистика")
                            col1, col2, col3 = st.columns(3)
                            
                            valid_turnovers = [cat['ОБОР ДН'] for cat in analysis_data if cat['ОБОР ДН'] < 999]
                            
                            with col1:
                                if valid_turnovers:
                                    avg_turnover = sum(valid_turnovers) / len(valid_turnovers)
                                    st.metric("Средняя оборачиваемость", f"{avg_turnover:.0f} дней")
                                else:
                                    st.metric("Средняя оборачиваемость", "Нет данных")
                            
                            with col2:
                                fast_count = len([cat for cat in analysis_data if cat['ОБОР ДН'] <= 180])
                                total_cats = len([cat for cat in analysis_data if not cat['КАТЕГОРИИ'].startswith('ИТОГО')])
                                st.metric("Быстрых категорий", f"{fast_count} из {total_cats}")
                            
                            with col3:
                                slow_count = len([cat for cat in analysis_data if cat['ОБОР ДН'] > 300])
                                st.metric("Медленных категорий", f"{slow_count} из {total_cats}")
                        
                        elif analysis_type == "🏢 По отдельным филиалам" and selected_branch == 'Все филиалы':
                            # Краткая статистика для всех филиалов
                            st.markdown("### 📊 Краткая статистика по всем филиалам")
                            
                            # Подсчитываем количество записей по филиалам
                            branch_counts = turnover_df['ФИЛИАЛ'].value_counts()
                            
                            st.write(f"**Всего записей:** {len(turnover_df)}")
                            st.write(f"**Филиалов:** {len(branch_counts)}")
                            
                            # Топ-3 филиала по количеству категорий
                            st.markdown("**Филиалы с наибольшим количеством категорий:**")
                            for branch, count in branch_counts.head(3).items():
                                st.write(f"• {branch}: {count} категорий")
                    
                    else:
                        st.info("Недостаточно данных для анализа оборачиваемости складов")
                
                with tab7:
                    # Простой ADS анализ напрямую из файла продаж
                    st.subheader("💰 ADS (Average Daily Sales) Анализ")
                    
                    if not sales_df.empty:
                        # Рассчитываем простые ADS из файла продаж
                        with st.spinner("Расчет ADS из файла продаж..."):
                            ads_df = calculate_simple_ads_from_sales(sales_df, detected_period_days)
                        
                        if not ads_df.empty:
                            # Общая статистика
                            total_ads = ads_df['ADS (шт/день)'].sum()
                            total_items = len(ads_df)
                            branches_count = ads_df['Филиал'].nunique()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Общий ADS системы", f"{total_ads:.2f} шт/день")
                            with col2:
                                st.metric("Товаров с продажами", f"{total_items}")
                            with col3:
                                st.metric("Филиалов", f"{branches_count}")
                            
                            # Выбор филиала
                            st.markdown("### 📊 ADS по филиалам")
                            
                            # Список филиалов для выбора
                            branch_options = ['Все филиалы'] + sorted(ads_df['Филиал'].unique())
                            selected_branch = st.selectbox(
                                "Выберите филиал для анализа:",
                                branch_options,
                                key="ads_branch_selector"
                            )
                            
                            # Фильтрация данных по выбранному филиалу
                            if selected_branch == 'Все филиалы':
                                display_data = ads_df.copy()
                                st.info(f"📍 Показаны данные по всем филиалам ({len(display_data)} товаров)")
                            else:
                                display_data = ads_df[ads_df['Филиал'] == selected_branch].copy()
                                branch_total = display_data['ADS (шт/день)'].sum()
                                st.info(f"📍 Филиал: **{selected_branch}** | Общий ADS: **{branch_total:.2f} шт/день** | Товаров: **{len(display_data)}**")
                            
                            # Отображение всех товаров в виде таблицы
                            if not display_data.empty:
                                st.dataframe(
                                    display_data[['Филиал', 'Товар', 'Артикул', 'ADS (шт/день)', 'Продано за период', 'Себестоимость за период', 'Категория']], 
                                    use_container_width=True, 
                                    hide_index=True,
                                    height=600
                                )
                            else:
                                st.warning("Нет данных для выбранного филиала")
                        else:
                            st.warning("⚠️ Не удалось рассчитать ADS из данных продаж")
                    else:
                        st.warning("⚠️ Нет данных о продажах для расчета ADS")
            
            else:
                st.warning("⚠️ Нет рекомендаций по перемещению при текущих параметрах")
                
                # Отладочная информация
                with st.expander("🔍 Отладочная информация"):
                    st.write(f"Записей остатков: {len(stock_df)}")
                    st.write(f"Записей продаж: {len(sales_df)}")
                    st.write(f"Филиалов в остатках: {stock_df['branch'].nunique() if not stock_df.empty else 0}")
                    st.write(f"Филиалов в продажах: {sales_df['branch'].nunique() if not sales_df.empty else 0}")
                    
                    if not stock_df.empty:
                        st.write("Филиалы в остатках:", stock_df['branch'].unique().tolist())
                    if not sales_df.empty:
                        st.write("Филиалы в продажах:", sales_df['branch'].unique().tolist())
    
    else:
        # Инструкция
        st.info("""
        ### 📋 Инструкция по использованию
        
        1. **Загрузите файл остатков** - JSON файл с текущими остатками по всем филиалам
        2. **Загрузите файл продаж** - JSON файл с продажами за анализируемый период
        3. **Настройте параметры** - период анализа и минимальное количество для перемещения
        4. **Получите рекомендации** - система проанализирует данные и предложит оптимальные перемещения
        
        ### 🏢 Учитываемая иерархия филиалов:
        
        **🏢 ГЛАВНЫЙ ХАБ:**
        - База Склад Фурнитура Комплект (г.Алматы) - пополняет все склады 2-го уровня
        
        **📦 СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба):**
        1. Казыбаева Склад Фурнитура TRADE (г.Алматы) → пополняет магазин Казыбаева
        2. склад фурнитура № 1 (г.Астана) → пополняет Магазин фурнитуры  
        3. 4 Склад фурнитуры АЗМ Шымкент (г.Шымкент) → пополняет магазин в Шымкенте
        
        **🏪 МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА (без своих складов):**
        - Барыс Склад Фурнитура TRADE (г.Алматы)
        - АО Склад Фурнитура TRADE (г.Алматы) - Алтын Орда
        
        **🏪 МАГАЗИНЫ 3-ГО УРОВНЯ (питаются от складов 2-го уровня):**
        1. ТД Казыбаева ФУРНИТУРА магазин ← от Казыбаева склад
        2. Магазин фурнитуры (г.Астана) ← от склад № 1
        3. 6 Склад фурнитуры "Овощная база" Магазин ← от Шымкент склад
        """)

if __name__ == "__main__":
    main()