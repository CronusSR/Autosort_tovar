#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УЛУЧШЕННАЯ СИСТЕМА РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ
Полная переработка с учетом оборачиваемости, ADS и иерархии складов
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class EnhancedMovementSystem:
    """Улучшенная система анализа перемещений с расчетом оборачиваемости"""
    
    def __init__(self):
        self.sales_data = {}
        self.stock_data = None
        self.ads_data = {}
        self.turnover_data = {}
        self.recommendations = []
        self.hierarchy = self._init_hierarchy()
        
    def _init_hierarchy(self):
        """Инициализация иерархии складов"""
        return {
            'База Склад Фурнитура Комплект': {
                'type': 'hub',
                'level': 1,
                'city': 'Алматы',
                'feeds': [
                    'Казыбаева Склад Фурнитура TRADE',
                    'склад фурнитура № 1',
                    '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                    'Барыс Склад Фурнитура TRADE',
                    'АО Склад Фурнитура TRADE'
                ],
                'min_days': 45,
                'max_days': 90,
                'safety_multiplier': 1.5
            },
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Алматы',
                'feeds': ['ТД Казыбаева ФУРНИТУРА магазин'],
                'fed_by': 'База Склад Фурнитура Комплект',
                'min_days': 20,
                'max_days': 45,
                'safety_multiplier': 1.2
            },
            'склад фурнитура № 1': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Астана',
                'feeds': ['Магазин фурнитуры'],
                'fed_by': 'База Склад Фурнитура Комплект',
                'min_days': 20,
                'max_days': 45,
                'safety_multiplier': 1.2
            },
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Шымкент',
                'feeds': ['6 Склад фурнитуры "Овощная база" Магазин'],
                'fed_by': 'База Склад Фурнитура Комплект',
                'min_days': 20,
                'max_days': 45,
                'safety_multiplier': 1.2
            },
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Алматы',
                'fed_by': 'Казыбаева Склад Фурнитура TRADE',
                'min_days': 10,
                'max_days': 25,
                'safety_multiplier': 1.0
            },
            'Магазин фурнитуры': {
                'type': 'store',
                'level': 3,
                'city': 'Астана',
                'fed_by': 'склад фурнитура № 1',
                'min_days': 10,
                'max_days': 25,
                'safety_multiplier': 1.0
            },
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Шымкент',
                'fed_by': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'min_days': 10,
                'max_days': 25,
                'safety_multiplier': 1.0
            },
            'Барыс Склад Фурнитура TRADE': {
                'type': 'store_combined',
                'level': 2.5,
                'city': 'Алматы',
                'fed_by': 'База Склад Фурнитура Комплект',
                'min_days': 15,
                'max_days': 35,
                'safety_multiplier': 1.1
            },
            'АО Склад Фурнитура TRADE': {
                'type': 'store_combined',
                'level': 2.5,
                'city': 'Алматы',
                'fed_by': 'База Склад Фурнитура Комплект',
                'min_days': 15,
                'max_days': 35,
                'safety_multiplier': 1.1
            }
        }
    
    def load_sales_files(self, sales_files_dict):
        """Загрузка нескольких файлов продаж для анализа оборачиваемости"""
        all_sales_data = {}
        
        for branch_name, file_content in sales_files_dict.items():
            st.info(f"🔄 Обработка файла продаж для {branch_name}...")
            
            try:
                # Читаем Excel файл
                df = pd.read_excel(file_content)
                
                # Очищаем названия колонок
                df.columns = df.columns.str.strip()
                
                # Ищем колонку с наименованиями товаров
                name_col = None
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['наименование', 'номенклатура', 'товар']):
                        name_col = col
                        break
                
                if not name_col:
                    st.error(f"❌ Не найдена колонка с наименованиями в файле {branch_name}")
                    continue
                
                # Ищем колонки с количеством продаж
                qty_cols = []
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['количество', 'кол-во', 'продано', 'qty']):
                        qty_cols.append(col)
                
                if not qty_cols:
                    st.warning(f"⚠️ Не найдены колонки с количеством в файле {branch_name}")
                    # Используем числовые колонки как альтернативу
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    qty_cols = [col for col in numeric_cols if col != name_col]
                
                if qty_cols:
                    # Создаем суммарную колонку продаж
                    df['total_sales'] = df[qty_cols].sum(axis=1, skipna=True)
                    
                    # Убираем пустые строки и нулевые продажи
                    df = df.dropna(subset=[name_col])
                    df = df[df['total_sales'] > 0]
                    
                    if not df.empty:
                        all_sales_data[branch_name] = df[[name_col, 'total_sales']].copy()
                        all_sales_data[branch_name].columns = ['product_name', 'sales_qty']
                        
                        st.success(f"✅ {branch_name}: загружено {len(df)} товаров с продажами")
                    else:
                        st.warning(f"⚠️ {branch_name}: нет данных после фильтрации")
                
            except Exception as e:
                st.error(f"❌ Ошибка обработки {branch_name}: {str(e)}")
                continue
        
        self.sales_data = all_sales_data
        return len(all_sales_data) > 0
    
    def load_stock_file(self, stock_file):
        """Загрузка файла остатков"""
        try:
            df = pd.read_excel(stock_file)
            
            # Очищаем названия колонок
            df.columns = df.columns.str.strip()
            
            # Ищем колонку с наименованиями
            name_col = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['наименование', 'номенклатура', 'товар']):
                    name_col = col
                    break
            
            if not name_col:
                st.error("❌ Не найдена колонка с наименованиями товаров в файле остатков")
                return False
            
            # Находим колонки со складами/магазинами
            stock_cols = []
            for col in df.columns:
                if col != name_col and not col.lower().startswith('unnamed'):
                    # Проверяем, что в колонке есть числовые данные
                    if df[col].dtype in ['int64', 'float64'] or pd.to_numeric(df[col], errors='coerce').notna().any():
                        stock_cols.append(col)
            
            if not stock_cols:
                st.error("❌ Не найдены колонки с остатками")
                return False
            
            # Создаем итоговый DataFrame
            stock_data = df[[name_col] + stock_cols].copy()
            
            # Преобразуем остатки в числовой формат
            for col in stock_cols:
                stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce').fillna(0)
            
            # Убираем строки без наименований
            stock_data = stock_data.dropna(subset=[name_col])
            stock_data = stock_data[stock_data[name_col].str.strip() != '']
            
            # Переименовываем колонку с наименованиями
            stock_data.rename(columns={name_col: 'product_name'}, inplace=True)
            
            self.stock_data = stock_data
            st.success(f"✅ Файл остатков загружен: {len(stock_data)} товаров по {len(stock_cols)} точкам")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Ошибка загрузки файла остатков: {str(e)}")
            return False
    
    def calculate_turnover_and_ads(self, period_days=365):
        """Расчет оборачиваемости и ADS на основе загруженных файлов продаж"""
        
        if not self.sales_data:
            st.error("❌ Нет данных о продажах для расчета")
            return False
        
        st.info("🔄 Расчет оборачиваемости и ADS...")
        
        # Собираем все продажи по товарам
        all_products = {}
        
        for branch_name, branch_data in self.sales_data.items():
            st.write(f"📊 Обработка данных {branch_name}: {len(branch_data)} товаров")
            
            for _, row in branch_data.iterrows():
                product_name = str(row['product_name']).strip()
                sales_qty = float(row['sales_qty']) if pd.notna(row['sales_qty']) else 0
                
                if product_name and sales_qty > 0:
                    if product_name not in all_products:
                        all_products[product_name] = {
                            'total_sales': 0,
                            'branches': {}
                        }
                    
                    all_products[product_name]['total_sales'] += sales_qty
                    all_products[product_name]['branches'][branch_name] = sales_qty
        
        # Рассчитываем ADS и оборачиваемость
        ads_results = []
        turnover_results = []
        
        for product_name, product_data in all_products.items():
            total_sales = product_data['total_sales']
            ads_value = total_sales / period_days
            
            # Рассчитываем оборачиваемость, если есть остатки
            turnover_data = {
                'product_name': product_name,
                'total_sales': total_sales,
                'ads': ads_value,
                'period_days': period_days
            }
            
            if self.stock_data is not None:
                # Ищем товар в остатках
                stock_row = self.stock_data[self.stock_data['product_name'].str.contains(
                    product_name, case=False, na=False, regex=False
                )]
                
                if not stock_row.empty:
                    stock_row = stock_row.iloc[0]
                    
                    # Считаем общий остаток
                    stock_cols = [col for col in self.stock_data.columns if col != 'product_name']
                    total_stock = sum(stock_row[col] for col in stock_cols if pd.notna(stock_row[col]))
                    
                    if total_stock > 0:
                        turnover_ratio = total_sales / total_stock
                        days_of_stock = total_stock / ads_value if ads_value > 0 else 999
                        
                        turnover_data.update({
                            'total_stock': total_stock,
                            'turnover_ratio': turnover_ratio,
                            'days_of_stock': days_of_stock,
                            'turnover_category': self._classify_turnover(turnover_ratio, days_of_stock)
                        })
                    
                    # Добавляем остатки по точкам
                    for col in stock_cols:
                        if pd.notna(stock_row[col]) and stock_row[col] > 0:
                            turnover_data[f'stock_{col}'] = stock_row[col]
            
            ads_results.append({
                'product_name': product_name,
                'ads': ads_value,
                'total_sales': total_sales,
                'sales_per_month': ads_value * 30
            })
            
            turnover_results.append(turnover_data)
        
        # Сохраняем результаты
        self.ads_data = pd.DataFrame(ads_results)
        self.turnover_data = pd.DataFrame(turnover_results)
        
        st.success(f"✅ Рассчитано ADS для {len(ads_results)} товаров")
        
        return True
    
    def _classify_turnover(self, turnover_ratio, days_of_stock):
        """Классификация товаров по оборачиваемости"""
        
        if days_of_stock <= 30:
            return 'Быстрооборачиваемый'
        elif days_of_stock <= 90:
            return 'Среднеоборачиваемый'
        elif days_of_stock <= 180:
            return 'Медленнооборачиваемый'
        else:
            return 'Неликвидный'
    
    def generate_movement_recommendations(self, user_settings=None):
        """Генерация рекомендаций по перемещениям с учетом иерархии и настроек"""
        
        if self.stock_data is None or self.ads_data.empty:
            st.error("❌ Недостаточно данных для генерации рекомендаций")
            return []
        
        st.info("🔄 Генерация рекомендаций по перемещениям...")
        
        recommendations = []
        
        # Получаем настройки пользователя или используем по умолчанию
        settings = user_settings or {
            'min_days_multiplier': 1.0,
            'max_days_multiplier': 1.0,
            'safety_stock_multiplier': 1.0,
            'priority_threshold': 0.8
        }
        
        # Анализируем каждый товар
        for _, product in self.turnover_data.iterrows():
            product_name = product['product_name']
            ads_value = product['ads']
            
            if ads_value <= 0:
                continue
            
            # Анализируем остатки по всем точкам
            stock_analysis = self._analyze_product_stock(product, ads_value, settings)
            
            # Генерируем рекомендации для этого товара
            product_recommendations = self._generate_product_recommendations(
                product_name, stock_analysis, ads_value, settings
            )
            
            recommendations.extend(product_recommendations)
        
        # Сортируем рекомендации по приоритету
        recommendations = sorted(recommendations, key=lambda x: (
            x['priority_score'], 
            x['urgency_level']
        ), reverse=True)
        
        self.recommendations = recommendations
        st.success(f"✅ Сгенерировано {len(recommendations)} рекомендаций")
        
        return recommendations
    
    def _analyze_product_stock(self, product, ads_value, settings):
        """Анализ остатков товара по всем точкам"""
        
        analysis = {}
        
        for location_name, location_config in self.hierarchy.items():
            stock_col = f'stock_{location_name}'
            
            if stock_col in product and pd.notna(product[stock_col]):
                current_stock = float(product[stock_col])
                
                if current_stock <= 0:
                    continue
                
                # Рассчитываем нормативы для этой точки
                location_ads = ads_value * location_config['safety_multiplier']
                min_stock = (location_ads * location_config['min_days'] * 
                           settings['min_days_multiplier'])
                max_stock = (location_ads * location_config['max_days'] * 
                           settings['max_days_multiplier'])
                
                # Определяем статус
                status = 'normal'
                if current_stock < min_stock * 0.5:
                    status = 'critical'
                elif current_stock < min_stock:
                    status = 'low'
                elif current_stock > max_stock:
                    status = 'excess'
                elif current_stock > max_stock * 0.8:
                    status = 'high'
                
                analysis[location_name] = {
                    'current_stock': current_stock,
                    'location_ads': location_ads,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'status': status,
                    'days_of_stock': current_stock / location_ads if location_ads > 0 else 999,
                    'surplus': max(0, current_stock - max_stock),
                    'deficit': max(0, min_stock - current_stock),
                    'config': location_config
                }
        
        return analysis
    
    def _generate_product_recommendations(self, product_name, stock_analysis, ads_value, settings):
        """Генерация рекомендаций для конкретного товара"""
        
        recommendations = []
        
        # Находим точки с излишками и дефицитами
        surplus_locations = []
        deficit_locations = []
        
        for location, analysis in stock_analysis.items():
            if analysis['status'] in ['excess', 'high'] and analysis['surplus'] > 0:
                surplus_locations.append((location, analysis))
            elif analysis['status'] in ['critical', 'low'] and analysis['deficit'] > 0:
                deficit_locations.append((location, analysis))
        
        # Генерируем рекомендации по перемещению
        for deficit_location, deficit_analysis in deficit_locations:
            needed_qty = deficit_analysis['deficit']
            
            # Ищем источники пополнения согласно иерархии
            sources = self._find_supply_sources(deficit_location, surplus_locations, stock_analysis)
            
            for source_location, source_analysis, available_qty in sources:
                move_qty = min(needed_qty, available_qty)
                
                if move_qty > 0:
                    # Определяем приоритет перемещения
                    priority_score = self._calculate_priority(
                        deficit_analysis, source_analysis, move_qty, ads_value
                    )
                    
                    recommendation = {
                        'product_name': product_name,
                        'from_location': source_location,
                        'to_location': deficit_location,
                        'quantity': move_qty,
                        'reason': self._generate_reason(deficit_analysis, source_analysis),
                        'urgency_level': self._determine_urgency(deficit_analysis),
                        'priority_score': priority_score,
                        'estimated_days_coverage': move_qty / deficit_analysis['location_ads'] if deficit_analysis['location_ads'] > 0 else 0,
                        'movement_type': self._determine_movement_type(source_location, deficit_location),
                        'from_city': stock_analysis[source_location]['config']['city'],
                        'to_city': stock_analysis[deficit_location]['config']['city'],
                        'cost_estimate': self._estimate_movement_cost(source_location, deficit_location, move_qty)
                    }
                    
                    recommendations.append(recommendation)
                    needed_qty -= move_qty
                    
                    if needed_qty <= 0:
                        break
            
            # Если дефицит не покрыт - рекомендация заказа у поставщика
            if needed_qty > 0:
                recommendations.append({
                    'product_name': product_name,
                    'from_location': 'Поставщик',
                    'to_location': 'База Склад Фурнитура Комплект',
                    'quantity': needed_qty * 1.2,  # С запасом
                    'reason': f'Заказ у поставщика для покрытия общего дефицита',
                    'urgency_level': 'medium',
                    'priority_score': 0.6,
                    'movement_type': 'supplier_order',
                    'cost_estimate': needed_qty * 10  # Примерная стоимость заказа
                })
        
        return recommendations
    
    def _find_supply_sources(self, deficit_location, surplus_locations, stock_analysis):
        """Поиск источников пополнения согласно иерархии"""
        
        sources = []
        deficit_config = stock_analysis[deficit_location]['config']
        
        # 1. Сначала ищем прямого поставщика по иерархии
        if 'fed_by' in deficit_config:
            direct_supplier = deficit_config['fed_by']
            if direct_supplier in stock_analysis:
                supplier_analysis = stock_analysis[direct_supplier]
                if supplier_analysis['surplus'] > 0:
                    sources.append((direct_supplier, supplier_analysis, supplier_analysis['surplus']))
        
        # 2. Затем ищем среди излишков в том же городе
        deficit_city = deficit_config['city']
        for surplus_location, surplus_analysis in surplus_locations:
            if surplus_analysis['config']['city'] == deficit_city and surplus_location not in [s[0] for s in sources]:
                sources.append((surplus_location, surplus_analysis, surplus_analysis['surplus']))
        
        # 3. Наконец, ищем в других городах (через хаб)
        for surplus_location, surplus_analysis in surplus_locations:
            if surplus_location not in [s[0] for s in sources]:
                sources.append((surplus_location, surplus_analysis, surplus_analysis['surplus']))
        
        return sources
    
    def _calculate_priority(self, deficit_analysis, source_analysis, move_qty, ads_value):
        """Расчет приоритета рекомендации"""
        
        priority = 0
        
        # Критичность дефицита
        if deficit_analysis['status'] == 'critical':
            priority += 0.5
        elif deficit_analysis['status'] == 'low':
            priority += 0.3
        
        # Размер излишка у источника
        if source_analysis['surplus'] > ads_value * 30:  # Больше месячного запаса
            priority += 0.3
        elif source_analysis['surplus'] > ads_value * 7:  # Больше недельного запаса
            priority += 0.2
        
        # Соответствие иерархии
        if 'fed_by' in deficit_analysis['config'] and deficit_analysis['config']['fed_by'] == source_analysis['config'].get('name'):
            priority += 0.2
        
        return priority
    
    def _generate_reason(self, deficit_analysis, source_analysis):
        """Генерация причины рекомендации"""
        
        deficit_status = deficit_analysis['status']
        days_left = deficit_analysis['days_of_stock']
        
        if deficit_status == 'critical':
            return f"КРИТИЧЕСКИЙ дефицит! Остатки на {days_left:.1f} дней"
        elif deficit_status == 'low':
            return f"Низкие остатки на {days_left:.1f} дней"
        else:
            return f"Пополнение запаса (текущие остатки на {days_left:.1f} дней)"
    
    def _determine_urgency(self, deficit_analysis):
        """Определение срочности"""
        
        if deficit_analysis['status'] == 'critical':
            return 'high'
        elif deficit_analysis['status'] == 'low':
            return 'medium'
        else:
            return 'low'
    
    def _determine_movement_type(self, from_location, to_location):
        """Определение типа перемещения"""
        
        if from_location == 'Поставщик':
            return 'supplier_order'
        
        from_config = self.hierarchy.get(from_location, {})
        to_config = self.hierarchy.get(to_location, {})
        
        if from_config.get('city') == to_config.get('city'):
            return 'internal_city'
        else:
            return 'inter_city'
    
    def _estimate_movement_cost(self, from_location, to_location, quantity):
        """Примерная оценка стоимости перемещения"""
        
        movement_type = self._determine_movement_type(from_location, to_location)
        
        base_cost = {
            'internal_city': 50,    # Внутри города
            'inter_city': 200,      # Между городами
            'supplier_order': 10    # Заказ у поставщика (за единицу)
        }
        
        if movement_type == 'supplier_order':
            return quantity * base_cost[movement_type]
        else:
            return base_cost[movement_type] + (quantity * 2)  # Базовая стоимость + за единицу
    
    def generate_summary_report(self):
        """Генерация сводного отчета"""
        
        if not self.recommendations:
            return None
        
        df = pd.DataFrame(self.recommendations)
        
        summary = {
            'total_recommendations': len(df),
            'high_priority': len(df[df['urgency_level'] == 'high']),
            'medium_priority': len(df[df['urgency_level'] == 'medium']),
            'low_priority': len(df[df['urgency_level'] == 'low']),
            'total_cost_estimate': df['cost_estimate'].sum(),
            'movement_types': df['movement_type'].value_counts().to_dict(),
            'top_products': df['product_name'].value_counts().head(10).to_dict(),
            'cities_affected': len(set(df['from_city'].tolist() + df['to_city'].tolist()))
        }
        
        return summary

def create_enhanced_movement_interface():
    """Создание интерфейса для улучшенной системы перемещений"""
    
    st.title("🚚 Улучшенная система рекомендаций по перемещениям")
    st.markdown("---")
    
    # Инициализация системы
    if 'enhanced_movement_system' not in st.session_state:
        st.session_state.enhanced_movement_system = EnhancedMovementSystem()
    
    system = st.session_state.enhanced_movement_system
    
    # Боковая панель с настройками
    st.sidebar.header("⚙️ Настройки системы")
    
    min_days_mult = st.sidebar.slider("Множитель минимальных дней", 0.5, 2.0, 1.0, 0.1)
    max_days_mult = st.sidebar.slider("Множитель максимальных дней", 0.5, 2.0, 1.0, 0.1)
    safety_mult = st.sidebar.slider("Множитель страхового запаса", 0.5, 2.0, 1.0, 0.1)
    
    user_settings = {
        'min_days_multiplier': min_days_mult,
        'max_days_multiplier': max_days_mult,
        'safety_stock_multiplier': safety_mult,
        'priority_threshold': 0.8
    }
    
    # Основной интерфейс
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Загрузка данных", 
        "📊 Анализ оборачиваемости", 
        "🚚 Рекомендации", 
        "📈 Отчеты"
    ])
    
    with tab1:
        st.header("Загрузка файлов данных")
        
        # Загрузка файлов продаж
        st.subheader("📈 Файлы продаж")
        st.info("Загрузите файлы продаж для расчета оборачиваемости и ADS")
        
        sales_files = st.file_uploader(
            "Выберите файлы продаж (несколько файлов)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="sales_files"
        )
        
        if sales_files and st.button("🔄 Обработать файлы продаж"):
            # Создаем словарь файлов с именами
            sales_dict = {}
            for file in sales_files:
                # Используем имя файла как ключ
                branch_name = file.name.replace('.xlsx', '').replace('.xls', '')
                sales_dict[branch_name] = file
            
            success = system.load_sales_files(sales_dict)
            if success:
                st.success("✅ Файлы продаж успешно загружены!")
        
        # Загрузка файла остатков
        st.subheader("📦 Файл остатков")
        
        stock_file = st.file_uploader(
            "Выберите файл с текущими остатками",
            type=['xlsx', 'xls'],
            key="stock_file"
        )
        
        if stock_file and st.button("🔄 Загрузить остатки"):
            success = system.load_stock_file(stock_file)
            if success:
                st.success("✅ Файл остатков успешно загружен!")
    
    with tab2:
        st.header("Анализ оборачиваемости и расчет ADS")
        
        if st.button("🔄 Рассчитать оборачиваемость и ADS"):
            success = system.calculate_turnover_and_ads()
            
            if success and not system.turnover_data.empty:
                st.success("✅ Расчет завершен!")
                
                # Показываем сводку
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Товаров с ADS", len(system.ads_data))
                
                with col2:
                    avg_ads = system.ads_data['ads'].mean()
                    st.metric("Средний ADS", f"{avg_ads:.2f}")
                
                with col3:
                    if 'turnover_category' in system.turnover_data.columns:
                        fast_moving = len(system.turnover_data[
                            system.turnover_data['turnover_category'] == 'Быстрооборачиваемый'
                        ])
                        st.metric("Быстрооборачиваемых", fast_moving)
                
                # Показываем топ товаров
                st.subheader("🔝 Топ товаров по ADS")
                top_ads = system.ads_data.nlargest(10, 'ads')[['product_name', 'ads', 'sales_per_month']]
                st.dataframe(top_ads, use_container_width=True)
    
    with tab3:
        st.header("Рекомендации по перемещениям")
        
        if st.button("🚀 Сгенерировать рекомендации", type="primary"):
            recommendations = system.generate_movement_recommendations(user_settings)
            
            if recommendations:
                st.success(f"✅ Создано {len(recommendations)} рекомендаций")
                
                # Фильтры
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    urgency_filter = st.selectbox(
                        "Фильтр по срочности",
                        ['Все', 'high', 'medium', 'low']
                    )
                
                with col2:
                    movement_filter = st.selectbox(
                        "Тип перемещения",
                        ['Все'] + list(set(r['movement_type'] for r in recommendations))
                    )
                
                # Применяем фильтры
                filtered_recs = recommendations
                if urgency_filter != 'Все':
                    filtered_recs = [r for r in filtered_recs if r['urgency_level'] == urgency_filter]
                if movement_filter != 'Все':
                    filtered_recs = [r for r in filtered_recs if r['movement_type'] == movement_filter]
                
                # Показываем рекомендации
                for i, rec in enumerate(filtered_recs[:20]):  # Ограничиваем 20 записями
                    with st.expander(f"🚚 {rec['product_name']} | {rec['from_location']} → {rec['to_location']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Количество:** {rec['quantity']:.1f}")
                            st.write(f"**Причина:** {rec['reason']}")
                            st.write(f"**Срочность:** {rec['urgency_level']}")
                        
                        with col2:
                            st.write(f"**Покрытие:** {rec['estimated_days_coverage']:.1f} дней")
                            st.write(f"**Стоимость:** {rec['cost_estimate']:.0f} тенге")
                            st.write(f"**Приоритет:** {rec['priority_score']:.2f}")
    
    with tab4:
        st.header("Сводные отчеты")
        
        if system.recommendations:
            summary = system.generate_summary_report()
            
            if summary:
                st.subheader("📊 Общая статистика")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Всего рекомендаций", summary['total_recommendations'])
                
                with col2:
                    st.metric("Высокий приоритет", summary['high_priority'])
                
                with col3:
                    st.metric("Общая стоимость", f"{summary['total_cost_estimate']:,.0f} ₸")
                
                with col4:
                    st.metric("Затронуто городов", summary['cities_affected'])
                
                # Экспорт в Excel
                if st.button("📥 Экспорт в Excel"):
                    df = pd.DataFrame(system.recommendations)
                    
                    # Создаем Excel файл в памяти
                    from io import BytesIO
                    output = BytesIO()
                    
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Рекомендации', index=False)
                        system.ads_data.to_excel(writer, sheet_name='ADS', index=False)
                        system.turnover_data.to_excel(writer, sheet_name='Оборачиваемость', index=False)
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="📥 Скачать отчет Excel",
                        data=output.getvalue(),
                        file_name=f"movement_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("📋 Сначала сгенерируйте рекомендации для создания отчетов")

if __name__ == "__main__":
    create_enhanced_movement_interface()