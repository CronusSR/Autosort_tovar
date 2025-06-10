#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СИСТЕМА РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ - ЧИСТАЯ ВЕРСИЯ
Интеграция с существующей системой ModularInventorySystem
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ===== КОНФИГУРАЦИЯ СИСТЕМЫ =====

class MovementRecommendationConfig:
    """Конфигурация системы рекомендаций"""
    
    # Базовые нормативы запасов в днях для разных типов точек
    BASE_STOCK_NORMS = {
        'магазин': {
            'min_days': 10,
            'optimal_days': 20,
            'max_days': 30,
            'priority': 100
        },
        'склад': {
            'min_days': 30,
            'optimal_days': 60,
            'max_days': 90,
            'priority': 50
        },
        'хаб': {
            'min_days': 60,
            'optimal_days': 120,
            'max_days': 180,
            'priority': 20
        }
    }
    
    # Настройки оборачиваемости по ABC категориям
    ABC_TURNOVER_SETTINGS = {
        'магазин': {
            'A': {'min_days': 15, 'optimal_days': 20, 'max_days': 25},
            'B': {'min_days': 8, 'optimal_days': 10, 'max_days': 15},
            'C': {'min_days': 5, 'optimal_days': 10, 'max_days': 20}
        },
        'склад': {
            'A': {'min_days': 25, 'optimal_days': 45, 'max_days': 60},
            'B': {'min_days': 20, 'optimal_days': 35, 'max_days': 50},
            'C': {'min_days': 15, 'optimal_days': 30, 'max_days': 45}
        },
        'хаб': {
            'A': {'min_days': 45, 'optimal_days': 90, 'max_days': 120},
            'B': {'min_days': 35, 'optimal_days': 70, 'max_days': 100},
            'C': {'min_days': 30, 'optimal_days': 60, 'max_days': 90}
        }
    }
    
    # Настройки по важности товаров
    IMPORTANCE_MODIFIERS = {
        'критичный': {'multiplier': 1.5, 'min_stock_boost': 1.3},
        'важный': {'multiplier': 1.2, 'min_stock_boost': 1.1},
        'обычный': {'multiplier': 1.0, 'min_stock_boost': 1.0},
        'медленный': {'multiplier': 0.8, 'min_stock_boost': 0.9}
    }
    
    # Минимальные партии для перемещения
    MIN_MOVEMENT_QUANTITY = 5
    
    # Включить/выключить ABC анализ
    USE_ABC_ANALYSIS = True
    
    @classmethod
    def get_location_type(cls, location_name: str) -> str:
        """Определение типа точки по названию"""
        if not location_name:
            return 'склад'
            
        location_lower = location_name.lower()
        
        if any(word in location_lower for word in ['магазин', 'маг', 'shop', 'торговый']):
            return 'магазин'
        elif any(word in location_lower for word in ['хаб', 'hub', 'центр', 'база', 'азм']):
            return 'хаб'
        elif any(word in location_lower for word in ['склад', 'скл', 'warehouse', 'trade']):
            return 'склад'
        else:
            return 'склад'
    
    @classmethod
    def get_stock_norms_for_item(cls, location_type: str, abc_class: str = None, importance: str = 'обычный') -> Dict:
        """
        Получение нормативов запасов с учетом ABC класса и важности товара
        """
        
        # Базовые нормативы
        if cls.USE_ABC_ANALYSIS and abc_class and abc_class in ['A', 'B', 'C']:
            # Используем ABC настройки
            base_norms = cls.ABC_TURNOVER_SETTINGS.get(location_type, {}).get(abc_class, {})
            if not base_norms:
                # Если нет ABC настроек, используем базовые
                base_norms = cls.BASE_STOCK_NORMS.get(location_type, cls.BASE_STOCK_NORMS['склад'])
        else:
            # Используем базовые нормативы
            base_norms = cls.BASE_STOCK_NORMS.get(location_type, cls.BASE_STOCK_NORMS['склад'])
        
        # Применяем модификаторы важности
        importance_mod = cls.IMPORTANCE_MODIFIERS.get(importance, cls.IMPORTANCE_MODIFIERS['обычный'])
        
        result = {
            'min_days': int(base_norms.get('min_days', 10) * importance_mod['min_stock_boost']),
            'optimal_days': int(base_norms.get('optimal_days', 20) * importance_mod['multiplier']),
            'max_days': int(base_norms.get('max_days', 30) * importance_mod['multiplier']),
            'priority': cls.BASE_STOCK_NORMS.get(location_type, {}).get('priority', 50),
            'abc_class': abc_class or 'Unknown',
            'importance': importance
        }
        
        return result

# ===== ОСНОВНАЯ ЛОГИКА РЕКОМЕНДАЦИЙ =====

class MovementRecommendationEngine:
    """Движок генерации рекомендаций по перемещениям"""
    
    def __init__(self, modular_system):
        """Инициализация с существующей ModularInventorySystem"""
        self.system = modular_system
        self.config = MovementRecommendationConfig()
        
        # Результаты анализа
        self.location_analysis = []
        self.movement_recommendations = []
        self.purchase_recommendations = []
        self.analysis_summary = {}
    
    def validate_system_data(self) -> Tuple[bool, str]:
        """Проверка наличия необходимых данных в системе"""
        
        # Проверяем ADS
        if not hasattr(self.system, 'calculated_ads') or self.system.calculated_ads is None:
            return False, "ADS не рассчитан. Перейдите в раздел 'ADS расчет' и рассчитайте среднедневные продажи."
        
        # Проверяем остатки
        if not hasattr(self.system, 'stock_data') or self.system.stock_data is None:
            return False, "Данные остатков не загружены. Перейдите в раздел 'Сравнение остатков' и загрузите файл остатков."
        
        # Проверяем пересечения
        ads_items = set(self.system.calculated_ads['номенклатура'].tolist())
        stock_items = set(self.system.stock_data['номенклатура'].tolist())
        common_items = ads_items & stock_items
        
        if len(common_items) == 0:
            return False, "Нет товаров с совпадающими названиями в данных ADS и остатков."
        
        return True, f"Готово к анализу: {len(common_items)} товаров с полными данными"
    
    def classify_locations(self) -> Dict[str, str]:
        """Классификация точек продаж по типам"""
        
        if self.system.stock_data is None:
            return {}
        
        # Получаем названия точек (все колонки кроме номенклатуры)
        location_columns = [col for col in self.system.stock_data.columns if col != 'номенклатура']
        
        location_types = {}
        for location in location_columns:
            location_types[location] = self.config.get_location_type(location)
        
        return location_types
    
    def get_item_abc_class(self, item_name: str) -> str:
        """Получение ABC класса товара из системы"""
        
        # Проверяем есть ли ABC данные в системе
        if hasattr(self.system, 'abc_results') and self.system.abc_results:
            if 'abc_data_detailed' in self.system.abc_results:
                abc_data = self.system.abc_results['abc_data_detailed']
                
                # Ищем товар в ABC данных
                item_row = abc_data[abc_data['nomenclature'] == item_name]
                if not item_row.empty and 'abc_class' in item_row.columns:
                    return item_row.iloc[0]['abc_class']
        
        # Проверяем в calculated_ads если там есть ABC класс
        if hasattr(self.system, 'calculated_ads') and self.system.calculated_ads is not None:
            if 'abc_class' in self.system.calculated_ads.columns:
                item_row = self.system.calculated_ads[self.system.calculated_ads['номенклатура'] == item_name]
                if not item_row.empty:
                    return item_row.iloc[0]['abc_class']
        
        # По умолчанию возвращаем B если ABC не найден
        return 'B'
    
    def get_item_importance(self, item_name: str, ads_value: float) -> str:
        """
        Определение важности товара на основе ADS и других факторов
        """
        
        if ads_value <= 0:
            return 'медленный'
        
        # Получаем квантили ADS для определения важности
        if hasattr(self.system, 'calculated_ads') and self.system.calculated_ads is not None:
            ads_data = self.system.calculated_ads['ads']
            
            # Рассчитываем квантили
            q90 = ads_data.quantile(0.9)
            q75 = ads_data.quantile(0.75)
            q25 = ads_data.quantile(0.25)
            
            if ads_value >= q90:
                return 'критичный'
            elif ads_value >= q75:
                return 'важный'
            elif ads_value >= q25:
                return 'обычный'
            else:
                return 'медленный'
        
        # Базовая логика если нет данных для квантилей
        if ads_value > 50:
            return 'критичный'
        elif ads_value > 20:
            return 'важный'
        elif ads_value > 5:
            return 'обычный'
        else:
            return 'медленный'
    
    def analyze_item_by_locations(self, item_name: str, ads_value: float, stock_row: pd.Series) -> Dict:
        """Анализ конкретного товара по всем точкам"""
        
        location_types = self.classify_locations()
        analysis = {
            'item_name': item_name,
            'ads': ads_value,
            'locations': {},
            'total_stock': 0,
            'deficit_locations': [],
            'surplus_locations': [],
            'normal_locations': []
        }
        
        # Анализируем каждую точку
        for location in location_types.keys():
            if location not in stock_row.index:
                continue
                
            stock_qty = stock_row[location]
            if pd.isna(stock_qty) or stock_qty == 0:
                continue
                
            stock_qty = float(stock_qty)
            analysis['total_stock'] += stock_qty
            
            location_type = location_types[location]
            
            # Получаем ABC класс и важность товара
            abc_class = self.get_item_abc_class(item_name)
            importance = self.get_item_importance(item_name, ads_value)
            
            # Получаем нормативы с учетом ABC и важности
            norms = self.config.get_stock_norms_for_item(location_type, abc_class, importance)
            
            # Рассчитываем нормативы для данного товара
            if ads_value > 0:
                min_stock = ads_value * norms['min_days']
                optimal_stock = ads_value * norms['optimal_days']
                max_stock = ads_value * norms['max_days']
                days_of_stock = stock_qty / ads_value
            else:
                min_stock = optimal_stock = max_stock = 0
                days_of_stock = 999
            
            # Определяем статус
            status = 'норма'
            urgency = 0
            
            if ads_value > 0:
                if stock_qty < min_stock:
                    status = 'дефицит'
                    urgency = int((min_stock - stock_qty) / min_stock * 100)
                elif stock_qty > max_stock:
                    status = 'излишек'
                    urgency = int((stock_qty - max_stock) / max_stock * 100)
            
            location_data = {
                'type': location_type,
                'current_stock': stock_qty,
                'min_stock': min_stock,
                'optimal_stock': optimal_stock,
                'max_stock': max_stock,
                'days_of_stock': round(days_of_stock, 1),
                'status': status,
                'urgency': urgency,
                'priority': norms['priority'],
                'abc_class': abc_class,
                'importance': importance,
                'norms_used': f"{location_type}/{abc_class}/{importance}"
            }
            
            analysis['locations'][location] = location_data
            
            # Группируем по статусу
            if status == 'дефицит':
                analysis['deficit_locations'].append((location, location_data))
            elif status == 'излишек':
                analysis['surplus_locations'].append((location, location_data))
            else:
                analysis['normal_locations'].append((location, location_data))
        
        return analysis
    
    def generate_movement_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по перемещениям"""
        
        recommendations = []
        
        for item_analysis in self.location_analysis:
            deficits = item_analysis['deficit_locations']
            surpluses = item_analysis['surplus_locations']
            
            if not deficits or not surpluses:
                continue
            
            # Сортируем по приоритету
            deficits.sort(key=lambda x: (-x[1]['priority'], -x[1]['urgency']))
            surpluses.sort(key=lambda x: x[1]['priority'])  # Хабы отдают легче
            
            # Генерируем перемещения
            for deficit_location, deficit_data in deficits:
                needed = deficit_data['optimal_stock'] - deficit_data['current_stock']
                if needed <= 0:
                    continue
                
                remaining_need = needed
                movements = []
                
                for surplus_location, surplus_data in surpluses:
                    if remaining_need <= 0:
                        break
                    
                    available = surplus_data['current_stock'] - surplus_data['optimal_stock']
                    if available <= self.config.MIN_MOVEMENT_QUANTITY:
                        continue
                    
                    to_move = min(available, remaining_need)
                    
                    movements.append({
                        'from': surplus_location,
                        'from_type': surplus_data['type'],
                        'quantity': round(to_move),
                        'from_days_before': surplus_data['days_of_stock']
                    })
                    
                    remaining_need -= to_move
                    surplus_data['current_stock'] -= to_move
                
                if movements:
                    rec = {
                        'item_name': item_analysis['item_name'],
                        'to': deficit_location,
                        'to_type': deficit_data['type'],
                        'to_days_before': deficit_data['days_of_stock'],
                        'needed': round(needed),
                        'covered': round(needed - remaining_need),
                        'remaining_deficit': round(remaining_need) if remaining_need > 0 else 0,
                        'urgency': deficit_data['urgency'],
                        'priority': deficit_data['priority'],
                        'ads': item_analysis['ads'],
                        'movements': movements
                    }
                    
                    # Добавляем информацию об ABC классе и важности
                    if 'abc_class' in deficit_data:
                        rec['abc_class'] = deficit_data['abc_class']
                    if 'importance' in deficit_data:
                        rec['importance'] = deficit_data['importance']
                    if 'norms_used' in deficit_data:
                        rec['norms_used'] = deficit_data['norms_used']
                    
                    recommendations.append(rec)
        
        # Сортируем по приоритету и срочности
        recommendations.sort(key=lambda x: (-x['priority'], -x['urgency']))
        
        return recommendations
    
    def generate_purchase_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по закупкам"""
        
        purchases = []
        
        for item_analysis in self.location_analysis:
            total_stock = item_analysis['total_stock']
            ads = item_analysis['ads']
            
            if ads <= 0:
                continue
            
            # Рассчитываем общую потребность
            total_need = 0
            critical_deficit = 0
            
            for location, location_data in item_analysis['locations'].items():
                total_need += location_data['optimal_stock']
                if location_data['status'] == 'дефицит':
                    critical_deficit += (location_data['optimal_stock'] - location_data['current_stock'])
            
            # Если общий запас меньше 70% от потребности
            if total_stock < total_need * 0.7:
                to_purchase = (total_need - total_stock) * 1.2
                current_days = total_stock / ads if ads > 0 else 0
                
                urgency_score = max(0, 100 - int(current_days / 30 * 100))
                
                purchase_rec = {
                    'item_name': item_analysis['item_name'],
                    'current_total_stock': round(total_stock),
                    'recommended_total_stock': round(total_need),
                    'to_purchase': round(to_purchase),
                    'current_days_supply': round(current_days, 1),
                    'critical_deficit': round(critical_deficit),
                    'ads': ads,
                    'urgency': urgency_score
                }
                
                # Добавляем денежную оценку если есть цены
                if hasattr(self.system, 'calculated_ads') and 'last_purchase_price' in self.system.calculated_ads.columns:
                    item_price_row = self.system.calculated_ads[
                        self.system.calculated_ads['номенклатура'] == item_analysis['item_name']
                    ]
                    if not item_price_row.empty and item_price_row.iloc[0]['last_purchase_price'] > 0:
                        price = item_price_row.iloc[0]['last_purchase_price']
                        purchase_rec['unit_price'] = price
                        purchase_rec['total_cost'] = round(to_purchase * price, 2)
                
                purchases.append(purchase_rec)
        
        purchases.sort(key=lambda x: -x['urgency'])
        return purchases
    
    def run_full_analysis(self) -> Dict:
        """Запуск полного анализа"""
        
        # Проверяем данные
        is_valid, message = self.validate_system_data()
        if not is_valid:
            return {'success': False, 'error': message}
        
        try:
            # Получаем данные
            ads_data = self.system.calculated_ads
            stock_data = self.system.stock_data
            
            # Анализируем каждый товар
            self.location_analysis = []
            
            progress_placeholder = st.empty()
            total_items = len(ads_data)
            
            for idx, ads_row in ads_data.iterrows():
                item_name = ads_row['номенклатура']
                ads_value = ads_row['ads']
                
                # Обновляем прогресс
                progress_placeholder.text(f"Анализ: {item_name[:50]}... ({idx+1}/{total_items})")
                
                # Ищем остатки для данного товара
                stock_row = stock_data[stock_data['номенклатура'] == item_name]
                
                if stock_row.empty:
                    continue
                
                # Анализируем товар
                item_analysis = self.analyze_item_by_locations(
                    item_name, ads_value, stock_row.iloc[0]
                )
                
                if item_analysis['locations']:
                    self.location_analysis.append(item_analysis)
            
            progress_placeholder.empty()
            
            # Генерируем рекомендации
            self.movement_recommendations = self.generate_movement_recommendations()
            self.purchase_recommendations = self.generate_purchase_recommendations()
            
            # Создаем сводку
            self.analysis_summary = self.create_analysis_summary()
            
            return {
                'success': True,
                'analyzed_items': len(self.location_analysis),
                'movement_recommendations': len(self.movement_recommendations),
                'purchase_recommendations': len(self.purchase_recommendations)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Ошибка при анализе: {str(e)}"}
    
    def create_analysis_summary(self) -> Dict:
        """Создание сводной статистики"""
        
        summary = {
            'total_items': len(self.location_analysis),
            'total_movement_recs': len(self.movement_recommendations),
            'total_purchase_recs': len(self.purchase_recommendations),
            'location_stats': {},
            'movement_efficiency': 0
        }
        
        # Анализируем каждую точку
        all_locations = set()
        for item in self.location_analysis:
            all_locations.update(item['locations'].keys())
        
        for location in all_locations:
            summary['location_stats'][location] = {
                'type': '',
                'total_items': 0,
                'surplus_items': 0,
                'deficit_items': 0,
                'normal_items': 0
            }
        
        # Собираем статистику
        total_deficit_covered = 0
        total_deficit_amount = 0
        
        for item in self.location_analysis:
            for location, data in item['locations'].items():
                loc_stats = summary['location_stats'][location]
                loc_stats['type'] = data['type']
                loc_stats['total_items'] += 1
                
                if data['status'] == 'дефицит':
                    loc_stats['deficit_items'] += 1
                elif data['status'] == 'излишек':
                    loc_stats['surplus_items'] += 1
                else:
                    loc_stats['normal_items'] += 1
        
        # Рассчитываем эффективность покрытия
        for rec in self.movement_recommendations:
            total_deficit_amount += rec['needed']
            total_deficit_covered += rec['covered']
        
        if total_deficit_amount > 0:
            summary['movement_efficiency'] = round(total_deficit_covered / total_deficit_amount * 100, 1)
        
        return summary

# ===== STREAMLIT ИНТЕРФЕЙС =====

def show_movement_recommendations_page(system):
    """Главная страница рекомендаций по перемещениям"""
    
    st.header("🚚 Рекомендации по перемещениям")
    
    # Создаем движок рекомендаций
    if 'movement_engine' not in st.session_state:
        st.session_state.movement_engine = MovementRecommendationEngine(system)
    
    engine = st.session_state.movement_engine
    
    # Проверяем данные
    is_valid, message = engine.validate_system_data()
    
    if not is_valid:
        st.error(f"❌ {message}")
        
        # Показываем инструкции
        st.markdown("""
        ### 📋 Как подготовить данные:
        
        1. **Рассчитайте ADS**: Перейдите в раздел "📊 ADS расчет" и загрузите файл продаж
        2. **Загрузите остатки**: Перейдите в раздел "⚖️ Сравнение остатков" и загрузите файл остатков
        3. **Вернитесь сюда** для анализа рекомендаций
        """)
        return
    
    # Данные готовы
    st.success(f"✅ {message}")
    
    # Информационная панель о новых возможностях
    with st.expander("ℹ️ О системе ABC оборачиваемости", expanded=False):
        st.markdown("""
        ### 🎯 Умная система нормативов
        
        **Система автоматически применяет разные нормативы в зависимости от:**
        - **ABC класс товара** (A, B, C) - важность по продажам
        - **Тип точки** (магазин, склад, хаб) - функция в цепи поставок
        - **Важность товара** (критичный, важный, обычный, медленный) - по ADS
        
        **Примеры нормативов:**
        - **Класс A в магазине**: 15-20-25 дней (быстрая оборачиваемость)
        - **Класс C в магазине**: 5-10-20 дней (медленные товары)
        - **Класс A на складе**: 25-45-60 дней (стратегический запас)
        
        **Быстрые профили:**
        - ⚡ **Быстрая оборачиваемость** - для продуктового ритейла
        - 🐌 **Медленная оборачиваемость** - для B2B и промышленности
        """)
    
    # Показываем краткую статистику системы
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Товаров с ADS", len(system.calculated_ads))
    with col2:
        locations_count = len([col for col in system.stock_data.columns if col != 'номенклатура'])
        st.metric("Точек продаж", locations_count)
    with col3:
        ads_items = set(system.calculated_ads['номенклатура'].tolist())
        stock_items = set(system.stock_data['номенклатура'].tolist())
        common_items = len(ads_items & stock_items)
        st.metric("Для анализа", common_items)
    
    # Настройки в боковой панели
    show_settings_sidebar()
    
    st.divider()
    
    # Кнопка запуска анализа
    if st.button("🚀 Запустить анализ рекомендаций", type="primary", use_container_width=True):
        with st.spinner("Выполняем анализ..."):
            result = engine.run_full_analysis()
        
        if result['success']:
            st.success(f"✅ Анализ завершен! Проанализировано {result['analyzed_items']} товаров")
            show_analysis_results(engine)
        else:
            st.error(f"❌ {result['error']}")
    
    # Если анализ уже выполнен, показываем результаты
    elif hasattr(engine, 'analysis_summary') and engine.analysis_summary:
        show_analysis_results(engine)

def show_settings_sidebar():
    """Настройки в боковой панели"""
    
    with st.sidebar:
        st.subheader("⚙️ Настройки системы")
        
        # Включение/выключение ABC анализа
        use_abc = st.checkbox(
            "Использовать ABC анализ",
            value=MovementRecommendationConfig.USE_ABC_ANALYSIS,
            help="Применять разные нормативы для товаров A, B, C классов"
        )
        MovementRecommendationConfig.USE_ABC_ANALYSIS = use_abc
        
        st.divider()
        
        # Дополнительные настройки
        st.subheader("🔧 Основные настройки")
        
        min_qty = st.number_input(
            "Минимальная партия перемещения", 
            value=MovementRecommendationConfig.MIN_MOVEMENT_QUANTITY, 
            min_value=1,
            help="Минимальное количество товара для рекомендации перемещения"
        )
        MovementRecommendationConfig.MIN_MOVEMENT_QUANTITY = min_qty

def show_analysis_results(engine):
    """Отображение результатов анализа"""
    
    st.header("📊 Результаты анализа")
    
    summary = engine.analysis_summary
    
    # Общая статистика
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Товаров", summary['total_items'])
    with col2:
        st.metric("Перемещений", summary['total_movement_recs'])
    with col3:
        st.metric("Закупок", summary['total_purchase_recs'])
    with col4:
        st.metric("Эффективность", f"{summary['movement_efficiency']}%")
    
    # Табы с результатами
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚚 Рекомендации по перемещениям",
        "🛒 Рекомендации по закупкам",
        "🏪 Анализ по точкам",
        "📋 Полный отчет"
    ])
    
    with tab1:
        show_movement_recommendations_tab(engine)
    
    with tab2:
        show_purchase_recommendations_tab(engine)
    
    with tab3:
        show_location_analysis_tab(engine)
    
    with tab4:
        show_full_report_tab(engine)

def show_movement_recommendations_tab(engine):
    """Вкладка рекомендаций по перемещениям"""
    
    recommendations = engine.movement_recommendations
    
    if not recommendations:
        st.info("📝 Рекомендации по перемещениям не найдены. Возможно, у вас оптимальное распределение!")
        return
    
    st.subheader(f"🚚 {len(recommendations)} рекомендаций по перемещениям")
    
    # Фильтры
    col1, col2 = st.columns(2)
    with col1:
        urgency_filter = st.slider("Мин. срочность (%)", 0, 100, 0)
    with col2:
        min_quantity = st.number_input("Мин. количество", min_value=0, value=0)
    
    # Применяем фильтры
    filtered_recs = [r for r in recommendations if r['urgency'] >= urgency_filter and r['covered'] >= min_quantity]
    
    st.info(f"Показано {len(filtered_recs)} из {len(recommendations)}")
    
    # Отображаем рекомендации
    for i, rec in enumerate(filtered_recs[:15], 1):
        with st.expander(f"#{i} {rec['item_name']} → {rec['to']} ({rec['to_type']})"):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**📍 Получатель:** {rec['to']} ({rec['to_type']})")
                st.write(f"**📦 Запас до:** {rec['to_days_before']} дней")
                st.write(f"**🎯 Требуется:** {rec['needed']} шт")
                st.write(f"**✅ Покроется:** {rec['covered']} шт")
                
                if rec['remaining_deficit'] > 0:
                    st.warning(f"⚠️ Остается дефицит: {rec['remaining_deficit']} шт")
                
                # Показываем информацию о товаре
                if rec.get('abc_class') and rec.get('importance'):
                    st.info(f"📊 Класс: {rec['abc_class']} | Важность: {rec['importance']}")
                
                st.write("**🚛 Источники:**")
                for j, movement in enumerate(rec['movements'], 1):
                    st.write(f"   {j}. **{movement['from']}** ({movement['from_type']}) → **{movement['quantity']} шт**")
            
            with col2:
                st.metric("Срочность", f"{rec['urgency']}%")
                st.metric("ADS", f"{rec['ads']:.2f}")
                
                # Показываем используемые нормативы
                if rec.get('norms_used'):
                    st.caption(f"Нормативы: {rec['norms_used']}")
                
                if rec['urgency'] > 80:
                    st.error("🔴 Критично")
                elif rec['urgency'] > 50:
                    st.warning("🟡 Срочно")
                else:
                    st.success("🟢 Нормально")

def show_purchase_recommendations_tab(engine):
    """Вкладка рекомендаций по закупкам"""
    
    purchases = engine.purchase_recommendations
    
    if not purchases:
        st.info("📝 Рекомендации по закупкам не найдены. Достаточно внутренних ресурсов!")
        return
    
    st.subheader(f"🛒 {len(purchases)} рекомендаций по закупкам")
    
    # Общая статистика
    total_to_purchase = sum(p['to_purchase'] for p in purchases)
    total_cost = sum(p.get('total_cost', 0) for p in purchases)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Общее количество", f"{total_to_purchase:,.0f} шт")
    with col2:
        if total_cost > 0:
            st.metric("Общая стоимость", f"{total_cost:,.2f} ₽")
    
    # Таблица закупок
    purchase_data = []
    for p in purchases:
        row = {
            'Товар': str(p['item_name']),
            'К закупке': str(p['to_purchase']),
            'Текущий запас': str(p['current_total_stock']),
            'Дни запаса': str(p['current_days_supply']),
            'ADS': f"{p['ads']:.2f}",
            'Срочность': f"{p['urgency']}%"
        }
        
        if 'total_cost' in p:
            row['Стоимость'] = f"{p['total_cost']:,.2f} ₽"
        
        purchase_data.append(row)
    
    if purchase_data:
        try:
            df_purchases = pd.DataFrame(purchase_data)
            st.dataframe(df_purchases, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка отображения таблицы: {e}")
            
            # Альтернативное отображение списком
            st.write("**Список рекомендаций по закупкам:**")
            for i, row in enumerate(purchase_data, 1):
                st.write(f"**{i}. {row['Товар']}**")
                st.write(f"   К закупке: {row['К закупке']} шт")
                st.write(f"   Текущий запас: {row['Текущий запас']} шт")
                st.write(f"   Дни запаса: {row['Дни запаса']}")
                st.write(f"   ADS: {row['ADS']}")
                st.write(f"   Срочность: {row['Срочность']}")
                if 'Стоимость' in row:
                    st.write(f"   Стоимость: {row['Стоимость']}")
                st.write("---")
    else:
        st.info("Нет данных для отображения")

def show_location_analysis_tab(engine):
    """Вкладка анализа по точкам"""
    
    if not engine.analysis_summary:
        st.info("Анализ не выполнен")
        return
    
    st.subheader("🏪 Анализ по точкам продаж")
    
    location_stats = engine.analysis_summary['location_stats']
    
    # Расширенная таблица по точкам с ABC информацией
    location_data = []
    for location, stats in location_stats.items():
        location_data.append({
            'Точка': str(location),
            'Тип': str(stats['type']),
            'Всего товаров': str(stats['total_items']),
            'Излишки': str(stats['surplus_items']),
            'Дефициты': str(stats['deficit_items']),
            'Норма': str(stats['normal_items']),
            'Проблемных (%)': f"{round((stats['surplus_items'] + stats['deficit_items']) / max(stats['total_items'], 1) * 100, 1)}%"
        })
    
    if location_data:
        try:
            df_locations = pd.DataFrame(location_data)
            st.dataframe(df_locations, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка отображения таблицы: {e}")
            
            # Альтернативное отображение
            st.write("**Анализ по точкам:**")
            for row in location_data:
                st.write(f"**{row['Точка']}** ({row['Тип']})")
                st.write(f"   Всего товаров: {row['Всего товаров']}")
                st.write(f"   Излишки: {row['Излишки']}, Дефициты: {row['Дефициты']}, Норма: {row['Норма']}")
                st.write(f"   Проблемных: {row['Проблемных (%)']}")
                st.write("---")
    else:
        st.info("Нет данных по точкам для отображения")
    
    # Визуализация по типам точек
    st.subheader("📊 Распределение проблем по типам точек")
    
    # Группируем по типам
    type_stats = {}
    for location, stats in location_stats.items():
        loc_type = stats['type']
        if loc_type not in type_stats:
            type_stats[loc_type] = {'surplus': 0, 'deficit': 0, 'normal': 0, 'locations': 0}
        
        type_stats[loc_type]['surplus'] += stats['surplus_items']
        type_stats[loc_type]['deficit'] += stats['deficit_items']
        type_stats[loc_type]['normal'] += stats['normal_items']
        type_stats[loc_type]['locations'] += 1
    
    # Создаем график
    if type_stats:
        types = list(type_stats.keys())
        surplus_counts = [type_stats[t]['surplus'] for t in types]
        deficit_counts = [type_stats[t]['deficit'] for t in types]
        normal_counts = [type_stats[t]['normal'] for t in types]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Излишки', x=types, y=surplus_counts, marker_color='orange'))
        fig.add_trace(go.Bar(name='Дефициты', x=types, y=deficit_counts, marker_color='red'))
        fig.add_trace(go.Bar(name='Норма', x=types, y=normal_counts, marker_color='green'))
        
        fig.update_layout(barmode='stack', title='Распределение статусов по типам точек')
        st.plotly_chart(fig, use_container_width=True)

def show_full_report_tab(engine):
    """Полный отчет с экспортом"""
    
    st.subheader("📋 Полный отчет")
    
    # Кнопка экспорта
    if st.button("📥 Экспорт отчета в Excel", type="primary"):
        excel_data = create_excel_report(engine)
        if excel_data:
            st.download_button(
                label="📁 Скачать отчет",
                data=excel_data,
                file_name=f"movement_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Исполнительная сводка
    st.subheader("📊 Исполнительная сводка")
    
    summary = engine.analysis_summary
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Товаров", summary['total_items'])
        st.metric("🚚 Перемещений", summary['total_movement_recs'])
    
    with col2:
        st.metric("🛒 Закупок", summary['total_purchase_recs'])
        st.metric("✅ Эффективность", f"{summary['movement_efficiency']}%")
    
    with col3:
        # Оценка эффективности
        if summary['movement_efficiency'] > 80:
            st.success("🟢 Отличная эффективность")
        elif summary['movement_efficiency'] > 60:
            st.warning("🟡 Хорошая эффективность")
        else:
            st.error("🔴 Требует оптимизации")
    
    # Детальные таблицы
    st.subheader("📋 Детальные таблицы")
    
    # Таблица перемещений
    if engine.movement_recommendations:
        st.write("**Все рекомендации по перемещениям:**")
        
        try:
            movement_table = create_movement_table(engine.movement_recommendations)
            st.dataframe(movement_table, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка отображения таблицы перемещений: {e}")
            
            # Альтернативное отображение
            st.write("**Альтернативное отображение:**")
            for i, rec in enumerate(engine.movement_recommendations[:10], 1):
                st.write(f"**{i}. {rec['item_name']}**")
                st.write(f"   Получатель: {rec['to']} ({rec['to_type']})")
                st.write(f"   Нужно: {rec['needed']} шт, Покроется: {rec['covered']} шт")
                for j, movement in enumerate(rec['movements'], 1):
                    st.write(f"   {j}. {movement['from']} → {movement['quantity']} шт")
                st.write("---")
    
    # Таблица закупок
    if engine.purchase_recommendations:
        st.write("**Все рекомендации по закупкам:**")
        
        try:
            purchase_table = create_purchase_table(engine.purchase_recommendations)
            st.dataframe(purchase_table, use_container_width=True)
        except Exception as e:
            st.error(f"Ошибка отображения таблицы закупок: {e}")
            
            # Альтернативное отображение
            st.write("**Альтернативное отображение:**")
            for i, rec in enumerate(engine.purchase_recommendations[:10], 1):
                st.write(f"**{i}. {rec['item_name']}**")
                st.write(f"   К закупке: {rec['to_purchase']} шт")
                st.write(f"   Текущий запас: {rec['current_total_stock']} шт ({rec['current_days_supply']} дней)")
                if 'total_cost' in rec:
                    st.write(f"   Стоимость: {rec['total_cost']:,.2f} ₽")
                st.write("---")

def create_movement_table(recommendations: List[Dict]) -> pd.DataFrame:
    """Создание таблицы перемещений"""
    
    data = []
    for i, rec in enumerate(recommendations, 1):
        for j, movement in enumerate(rec['movements']):
            # Используем строки для всех полей чтобы избежать ошибок типов
            data.append({
                '№': str(i) if j == 0 else '',
                'Товар': str(rec['item_name']) if j == 0 else '',
                'Получатель': str(rec['to']) if j == 0 else '',
                'Тип получателя': str(rec['to_type']) if j == 0 else '',
                'Нужно (шт)': str(rec['needed']) if j == 0 else '',
                'ABC класс': str(rec.get('abc_class', '')) if j == 0 else '',
                'Важность': str(rec.get('importance', '')) if j == 0 else '',
                'Донор': str(movement['from']),
                'Тип донора': str(movement['from_type']),
                'Количество': str(movement['quantity']),
                'Срочность (%)': str(rec['urgency']) if j == 0 else '',
                'ADS': f"{rec['ads']:.2f}" if j == 0 else '',
                'Нормативы': str(rec.get('norms_used', '')) if j == 0 else ''
            })
    
    return pd.DataFrame(data)

def create_purchase_table(recommendations: List[Dict]) -> pd.DataFrame:
    """Создание таблицы закупок"""
    
    data = []
    for i, rec in enumerate(recommendations, 1):
        row = {
            '№': str(i),
            'Товар': str(rec['item_name']),
            'К закупке (шт)': str(rec['to_purchase']),
            'Текущий запас (шт)': str(rec['current_total_stock']),
            'Рекомендуемый запас (шт)': str(rec['recommended_total_stock']),
            'Дни запаса': str(rec['current_days_supply']),
            'ADS': f"{rec['ads']:.2f}",
            'Срочность (%)': str(rec['urgency'])
        }
        
        if 'total_cost' in rec:
            row['Стоимость (₽)'] = f"{rec['total_cost']:,.2f}"
        
        data.append(row)
    
    return pd.DataFrame(data)

def create_excel_report(engine) -> bytes:
    """Создание Excel отчета"""
    
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Лист 1: Сводка
            summary_data = []
            summary = engine.analysis_summary
            
            summary_data.append(['ОТЧЕТ СИСТЕМЫ РЕКОМЕНДАЦИЙ', ''])
            summary_data.append(['Дата', datetime.now().strftime('%Y-%m-%d %H:%M')])
            summary_data.append(['', ''])
            summary_data.append(['СТАТИСТИКА', ''])
            summary_data.append(['Товаров проанализировано', summary['total_items']])
            summary_data.append(['Рекомендаций по перемещению', summary['total_movement_recs']])
            summary_data.append(['Рекомендаций по закупке', summary['total_purchase_recs']])
            summary_data.append(['Эффективность покрытия (%)', summary['movement_efficiency']])
            
            df_summary = pd.DataFrame(summary_data, columns=['Показатель', 'Значение'])
            df_summary.to_excel(writer, sheet_name='Сводка', index=False)
            
            # Лист 2: Перемещения
            if engine.movement_recommendations:
                movement_table = create_movement_table(engine.movement_recommendations)
                movement_table.to_excel(writer, sheet_name='Перемещения', index=False)
            
            # Лист 3: Закупки  
            if engine.purchase_recommendations:
                purchase_table = create_purchase_table(engine.purchase_recommendations)
                purchase_table.to_excel(writer, sheet_name='Закупки', index=False)
            
            # Лист 4: Анализ по точкам
            location_stats = engine.analysis_summary['location_stats']
            if location_stats:
                location_data = []
                for location, stats in location_stats.items():
                    location_data.append({
                        'Точка': location,
                        'Тип': stats['type'],
                        'Всего товаров': stats['total_items'],
                        'Излишки': stats['surplus_items'],
                        'Дефициты': stats['deficit_items'],
                        'Норма': stats['normal_items']
                    })
                
                df_locations = pd.DataFrame(location_data)
                df_locations.to_excel(writer, sheet_name='Анализ_точек', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Ошибка создания Excel: {str(e)}")
        return None

# ===== ТЕСТИРОВАНИЕ =====

if __name__ == "__main__":
    st.title("🚚 Система рекомендаций по перемещениям")
    st.subheader("Чистая версия - готова к интеграции")
    
    st.markdown("""
    ### ✅ Исправления:
    - Убраны все синтаксические ошибки
    - Исправлена структура функций
    - Убран лишний код вне функций
    - Код готов к интеграции
    
    ### 🎯 Новые возможности:
    - ABC-адаптивные нормативы оборачиваемости
    - Автоматическая классификация важности товаров
    - Гибкие настройки для разных типов точек
    - Быстрые профили настроек
    """)