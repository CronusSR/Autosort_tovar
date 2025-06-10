#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СИСТЕМА РЕКОМЕНДАЦИЙ ПО СКЛАДСКИМ ПЕРЕМЕЩЕНИЯМ
Модуль для анализа и генерации рекомендаций по перемещению товаров между точками продаж
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional
import io
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ===== КОНФИГУРАЦИЯ СИСТЕМЫ =====

class MovementConfig:
    """Конфигурация системы рекомендаций"""
    
    # Нормативы запасов в днях для разных типов точек
    STOCK_NORMS = {
        'магазин': {
            'min_days': 10,      # Минимальный запас
            'optimal_days': 20,  # Оптимальный запас  
            'max_days': 30,      # Максимальный запас (после которого излишек)
            'priority': 100      # Приоритет получения товара
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
    
    # Минимальные партии для перемещения
    MIN_MOVEMENT_QUANTITY = 5
    
    # Коэффициент безопасности для закупок
    SAFETY_FACTOR = 1.2
    
    @classmethod
    def get_location_type(cls, location_name: str) -> str:
        """Определение типа точки по названию"""
        if not location_name:
            return 'склад'
            
        location_lower = location_name.lower()
        
        # Проверяем ключевые слова в названии
        if any(word in location_lower for word in ['магазин', 'маг', 'shop', 'торговый']):
            return 'магазин'
        elif any(word in location_lower for word in ['хаб', 'hub', 'центр', 'база', 'азм']):
            return 'хаб'
        elif any(word in location_lower for word in ['склад', 'скл', 'warehouse', 'trade']):
            return 'склад'
        else:
            return 'склад'  # По умолчанию

# ===== ОСНОВНОЙ КЛАСС СИСТЕМЫ РЕКОМЕНДАЦИЙ =====

class MovementRecommendationEngine:
    """Движок генерации рекомендаций по перемещениям товаров"""
    
    def __init__(self, inventory_system):
        """
        Инициализация системы рекомендаций
        
        Args:
            inventory_system: Экземпляр ModularInventorySystem
        """
        self.system = inventory_system
        self.config = MovementConfig()
        
        # Результаты анализа
        self.location_analysis = None
        self.movement_recommendations = []
        self.purchase_recommendations = []
        self.analysis_summary = {}
        
        # Статистика
        self.total_analyzed_items = 0
        self.total_locations = 0
        self.locations_with_surplus = 0
        self.locations_with_deficit = 0
        
    def validate_data(self) -> Tuple[bool, str]:
        """Проверка наличия необходимых данных"""
        
        if not hasattr(self.system, 'calculated_ads') or self.system.calculated_ads is None:
            return False, "ADS не рассчитан. Загрузите файл продаж и рассчитайте ADS."
        
        if not hasattr(self.system, 'stock_data') or self.system.stock_data is None:
            return False, "Данные остатков не загружены. Загрузите файл остатков."
            
        ads_data = self.system.calculated_ads
        stock_data = self.system.stock_data
        
        if len(ads_data) == 0:
            return False, "ADS данные пусты."
            
        if len(stock_data) == 0:
            return False, "Данные остатков пусты."
            
        # Проверяем наличие нужных колонок
        required_ads_cols = ['номенклатура', 'ads']
        missing_ads_cols = [col for col in required_ads_cols if col not in ads_data.columns]
        if missing_ads_cols:
            return False, f"В ADS данных отсутствуют колонки: {missing_ads_cols}"
            
        # Для stock_data проверяем наличие колонок номенклатуры и остатков
        stock_cols = stock_data.columns.tolist()
        if 'номенклатура' not in stock_cols:
            return False, "В данных остатков отсутствует колонка 'номенклатура'"
            
        # Ищем колонки с остатками (все кроме номенклатуры)
        stock_location_cols = [col for col in stock_cols if col != 'номенклатура']
        if len(stock_location_cols) == 0:
            return False, "В данных остатков не найдены колонки с точками продаж"
            
        return True, "Данные корректны"
    
    def classify_locations(self) -> Dict[str, str]:
        """Классификация точек по типам"""
        
        if self.system.stock_data is None:
            return {}
            
        location_columns = [col for col in self.system.stock_data.columns if col != 'номенклатура']
        
        location_types = {}
        for location in location_columns:
            location_types[location] = self.config.get_location_type(location)
            
        return location_types
    
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
        for location, stock_qty in stock_row.items():
            if location == 'номенклатура' or pd.isna(stock_qty) or stock_qty == 0:
                continue
                
            stock_qty = float(stock_qty)
            analysis['total_stock'] += stock_qty
            
            location_type = location_types.get(location, 'склад')
            norms = self.config.STOCK_NORMS[location_type]
            
            # Рассчитываем нормативы для данного товара
            if ads_value > 0:
                min_stock = ads_value * norms['min_days']
                optimal_stock = ads_value * norms['optimal_days'] 
                max_stock = ads_value * norms['max_days']
                days_of_stock = stock_qty / ads_value
            else:
                # Если ADS = 0, используем средние значения
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
                'priority': norms['priority']
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
        
        if self.location_analysis is None:
            return recommendations
        
        for item_analysis in self.location_analysis:
            deficits = item_analysis['deficit_locations']
            surpluses = item_analysis['surplus_locations']
            
            if not deficits or not surpluses:
                continue
                
            # Сортируем: магазины получают приоритет
            deficits.sort(key=lambda x: (-x[1]['priority'], -x[1]['urgency']))
            # Хабы и склады отдают легче
            surpluses.sort(key=lambda x: x[1]['priority'])
            
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
                        'from_days_before': surplus_data['days_of_stock'],
                        'from_urgency': surplus_data['urgency']
                    })
                    
                    remaining_need -= to_move
                    # Обновляем доступность для следующих итераций
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
                    
                    recommendations.append(rec)
        
        # Сортируем по приоритету и срочности
        recommendations.sort(key=lambda x: (-x['priority'], -x['urgency']))
        
        return recommendations
    
    def generate_purchase_recommendations(self) -> List[Dict]:
        """Генерация рекомендаций по закупкам (логика вытягивания)"""
        
        purchases = []
        
        if self.location_analysis is None:
            return purchases
        
        for item_analysis in self.location_analysis:
            total_stock = item_analysis['total_stock']
            ads = item_analysis['ads']
            
            if ads <= 0:
                continue
            
            # Рассчитываем общую потребность по всем точкам
            total_need = 0
            critical_deficit = 0
            
            for location, location_data in item_analysis['locations'].items():
                total_need += location_data['optimal_stock']
                if location_data['status'] == 'дефицит':
                    critical_deficit += (location_data['optimal_stock'] - location_data['current_stock'])
            
            # Если общий запас меньше 70% от потребности - нужна закупка
            if total_stock < total_need * 0.7:
                to_purchase = (total_need - total_stock) * self.config.SAFETY_FACTOR
                current_days = total_stock / ads if ads > 0 else 0
                
                urgency_score = max(0, 100 - int(current_days / 30 * 100))  # Чем меньше дней, тем срочнее
                
                purchase_rec = {
                    'item_name': item_analysis['item_name'],
                    'current_total_stock': round(total_stock),
                    'recommended_total_stock': round(total_need),
                    'to_purchase': round(to_purchase),
                    'current_days_supply': round(current_days, 1),
                    'critical_deficit': round(critical_deficit),
                    'ads': ads,
                    'urgency': urgency_score,
                    'reason': 'Общий дефицит по сети' if critical_deficit > 0 else 'Низкий общий запас'
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
        
        # Сортируем по срочности
        purchases.sort(key=lambda x: -x['urgency'])
        
        return purchases
    
    def run_full_analysis(self) -> Dict:
        """Запуск полного анализа системы"""
        
        # Проверяем данные
        is_valid, error_msg = self.validate_data()
        if not is_valid:
            return {
                'success': False,
                'error': error_msg,
                'recommendations': [],
                'purchases': []
            }
        
        try:
            st.info("🔍 Анализируем товары по точкам продаж...")
            
            # Получаем данные
            ads_data = self.system.calculated_ads
            stock_data = self.system.stock_data
            
            # Анализируем каждый товар
            self.location_analysis = []
            analyzed_items = 0
            
            progress_bar = st.progress(0)
            total_items = len(ads_data)
            
            for idx, ads_row in ads_data.iterrows():
                item_name = ads_row['номенклатура']
                ads_value = ads_row['ads']
                
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
                    analyzed_items += 1
                
                # Обновляем прогресс
                progress_bar.progress((idx + 1) / total_items)
            
            progress_bar.empty()
            
            self.total_analyzed_items = analyzed_items
            
            st.info("🚚 Генерируем рекомендации по перемещениям...")
            
            # Генерируем рекомендации
            self.movement_recommendations = self.generate_movement_recommendations()
            
            st.info("🛒 Генерируем рекомендации по закупкам...")
            
            self.purchase_recommendations = self.generate_purchase_recommendations()
            
            # Создаем сводку
            self.analysis_summary = self.create_analysis_summary()
            
            return {
                'success': True,
                'analyzed_items': analyzed_items,
                'movement_recommendations': len(self.movement_recommendations),
                'purchase_recommendations': len(self.purchase_recommendations),
                'summary': self.analysis_summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Ошибка при анализе: {str(e)}",
                'recommendations': [],
                'purchases': []
            }
    
    def create_analysis_summary(self) -> Dict:
        """Создание сводной статистики"""
        
        if not self.location_analysis:
            return {}
        
        summary = {
            'total_items': len(self.location_analysis),
            'total_movement_recs': len(self.movement_recommendations),
            'total_purchase_recs': len(self.purchase_recommendations),
            'location_stats': {},
            'deficit_stats': {
                'total_items_with_deficit': 0,
                'total_deficit_quantity': 0,
                'critical_deficits': 0  # urgency > 80
            },
            'surplus_stats': {
                'total_items_with_surplus': 0,
                'total_surplus_quantity': 0,
                'high_surplus': 0  # urgency > 50
            },
            'movement_efficiency': 0,  # Процент покрытия дефицитов перемещениями
            'money_stats': {}
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
            has_deficit = False
            has_surplus = False
            
            for location, data in item['locations'].items():
                loc_stats = summary['location_stats'][location]
                loc_stats['type'] = data['type']
                loc_stats['total_items'] += 1
                
                if data['status'] == 'дефицит':
                    loc_stats['deficit_items'] += 1
                    has_deficit = True
                    deficit_qty = data['optimal_stock'] - data['current_stock']
                    summary['deficit_stats']['total_deficit_quantity'] += deficit_qty
                    
                    if data['urgency'] > 80:
                        summary['deficit_stats']['critical_deficits'] += 1
                        
                elif data['status'] == 'излишек':
                    loc_stats['surplus_items'] += 1
                    has_surplus = True
                    surplus_qty = data['current_stock'] - data['optimal_stock']
                    summary['surplus_stats']['total_surplus_quantity'] += surplus_qty
                    
                    if data['urgency'] > 50:
                        summary['surplus_stats']['high_surplus'] += 1
                        
                else:
                    loc_stats['normal_items'] += 1
            
            if has_deficit:
                summary['deficit_stats']['total_items_with_deficit'] += 1
            if has_surplus:
                summary['surplus_stats']['total_items_with_surplus'] += 1
        
        # Рассчитываем эффективность покрытия
        for rec in self.movement_recommendations:
            total_deficit_amount += rec['needed']
            total_deficit_covered += rec['covered']
        
        if total_deficit_amount > 0:
            summary['movement_efficiency'] = round(total_deficit_covered / total_deficit_amount * 100, 1)
        
        # Денежная статистика (если доступна)
        if hasattr(self.system, 'calculated_ads') and 'last_purchase_price' in self.system.calculated_ads.columns:
            total_movement_cost = 0
            total_purchase_cost = 0
            
            for rec in self.movement_recommendations:
                if 'total_cost' in rec:
                    total_movement_cost += rec.get('total_cost', 0)
            
            for rec in self.purchase_recommendations:
                if 'total_cost' in rec:
                    total_purchase_cost += rec.get('total_cost', 0)
            
            summary['money_stats'] = {
                'movement_cost': total_movement_cost,
                'purchase_cost': total_purchase_cost,
                'total_cost': total_movement_cost + total_purchase_cost
            }
        
        return summary

# ===== STREAMLIT ИНТЕРФЕЙС =====

def show_movement_recommendations_page():
    """Главная страница системы рекомендаций"""
    
    st.set_page_config(
        page_title="Система рекомендаций по перемещениям",
        page_icon="🚚",
        layout="wide"
    )
    
    st.title("🚚 Система рекомендаций по складским перемещениям")
    
    # Проверяем наличие системы в session_state
    if 'inventory_system' not in st.session_state:
        st.error("❌ Система не инициализирована. Сначала загрузите данные в основном приложении.")
        st.info("👉 Перейдите на главную страницу и загрузите файлы ADS и остатков.")
        return
    
    system = st.session_state.inventory_system
    
    # Создаем движок рекомендаций
    if 'movement_engine' not in st.session_state:
        st.session_state.movement_engine = MovementRecommendationEngine(system)
    
    engine = st.session_state.movement_engine
    
    # Боковая панель с настройками
    with st.sidebar:
        st.header("⚙️ Настройки системы")
        
        # Настройка нормативов
        st.subheader("📊 Нормативы запасов (дни)")
        
        for loc_type, norms in MovementConfig.STOCK_NORMS.items():
            st.write(f"**{loc_type.title()}:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                min_days = st.number_input(f"Мин {loc_type}", value=norms['min_days'], min_value=1, key=f"min_{loc_type}")
            with col2:
                opt_days = st.number_input(f"Опт {loc_type}", value=norms['optimal_days'], min_value=min_days, key=f"opt_{loc_type}")
            with col3:
                max_days = st.number_input(f"Макс {loc_type}", value=norms['max_days'], min_value=opt_days, key=f"max_{loc_type}")
            
            # Обновляем конфигурацию
            MovementConfig.STOCK_NORMS[loc_type]['min_days'] = min_days
            MovementConfig.STOCK_NORMS[loc_type]['optimal_days'] = opt_days
            MovementConfig.STOCK_NORMS[loc_type]['max_days'] = max_days
        
        st.divider()
        
        # Другие настройки
        min_qty = st.number_input("Минимальная партия перемещения", value=MovementConfig.MIN_MOVEMENT_QUANTITY, min_value=1)
        MovementConfig.MIN_MOVEMENT_QUANTITY = min_qty
        
        safety_factor = st.number_input("Коэффициент безопасности для закупок", value=MovementConfig.SAFETY_FACTOR, min_value=1.0, max_value=3.0, step=0.1)
        MovementConfig.SAFETY_FACTOR = safety_factor
    
    # Проверка данных
    is_valid, error_msg = engine.validate_data()
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Информация о загруженных данных
    st.success("✅ Данные успешно загружены и готовы к анализу")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Товаров с ADS", len(system.calculated_ads))
    with col2:
        stock_locations = len([col for col in system.stock_data.columns if col != 'номенклатура'])
        st.metric("Точек продаж", stock_locations)
    with col3:
        common_items = len(set(system.calculated_ads['номенклатура']) & set(system.stock_data['номенклатура']))
        st.metric("Товаров для анализа", common_items)
    
    st.divider()
    
    # Кнопка запуска анализа
    if st.button("🚀 Запустить анализ рекомендаций", type="primary", use_container_width=True):
        with st.spinner("Выполняем анализ..."):
            result = engine.run_full_analysis()
        
        if result['success']:
            st.success(f"✅ Анализ завершен! Проанализировано {result['analyzed_items']} товаров")
            
            # Показываем результаты
            show_analysis_results(engine)
            
        else:
            st.error(f"❌ Ошибка анализа: {result['error']}")
    
    # Если анализ уже выполнен, показываем результаты
    elif hasattr(engine, 'analysis_summary') and engine.analysis_summary:
        show_analysis_results(engine)

def show_analysis_results(engine: MovementRecommendationEngine):
    """Отображение результатов анализа"""
    
    st.header("📊 Результаты анализа")
    
    # Общая статистика
    summary = engine.analysis_summary
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Товаров проанализировано", summary['total_items'])
    with col2:
        st.metric("Рекомендаций по перемещению", summary['total_movement_recs'])
    with col3:
        st.metric("Рекомендаций по закупке", summary['total_purchase_recs'])
    with col4:
        st.metric("Эффективность покрытия", f"{summary['movement_efficiency']}%")
    
    # Табы с разными разделами
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚚 Рекомендации по перемещениям",
        "🛒 Рекомендации по закупкам", 
        "🏪 Анализ по точкам",
        "📈 Визуализация",
        "📋 Полный отчет"
    ])
    
    with tab1:
        show_movement_recommendations_tab(engine)
    
    with tab2:
        show_purchase_recommendations_tab(engine)
    
    with tab3:
        show_location_analysis_tab(engine)
        
    with tab4:
        show_visualization_tab(engine)
    
    with tab5:
        show_full_report_tab(engine)

def show_movement_recommendations_tab(engine: MovementRecommendationEngine):
    """Вкладка с рекомендациями по перемещениям"""
    
    recommendations = engine.movement_recommendations
    
    if not recommendations:
        st.info("📝 Рекомендации по перемещениям не найдены. Возможно, у вас оптимальное распределение товаров!")
        return
    
    st.subheader(f"🚚 Найдено {len(recommendations)} рекомендаций по перемещениям")
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        priority_filter = st.selectbox("Приоритет получателя", ["Все", "Высокий (100)", "Средний (50)", "Низкий (20)"])
    with col2:
        urgency_filter = st.slider("Минимальная срочность (%)", 0, 100, 0)
    with col3:
        min_quantity = st.number_input("Минимальное количество", min_value=0, value=0)
    
    # Применяем фильтры
    filtered_recs = recommendations.copy()
    
    if priority_filter != "Все":
        priority_map = {"Высокий (100)": 100, "Средний (50)": 50, "Низкий (20)": 20}
        filtered_recs = [r for r in filtered_recs if r['urgency'] >= urgency_filter]
    filtered_recs = [r for r in filtered_recs if r['covered'] >= min_quantity]
    
    st.info(f"Показано {len(filtered_recs)} из {len(recommendations)} рекомендаций")
    
    # Отображаем рекомендации
    for i, rec in enumerate(filtered_recs[:20], 1):  # Показываем топ-20
        with st.expander(f"#{i} {rec['item_name']} → {rec['to']} ({rec['to_type']})"):
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**📍 Получатель:** {rec['to']} ({rec['to_type']})")
                st.write(f"**📦 Текущий запас:** {rec['to_days_before']} дней")
                st.write(f"**🎯 Требуется:** {rec['needed']} шт")
                st.write(f"**✅ Покроется:** {rec['covered']} шт")
                
                if rec['remaining_deficit'] > 0:
                    st.warning(f"⚠️ Остается дефицит: {rec['remaining_deficit']} шт")
                
                st.write("**🚛 Перемещения:**")
                for j, movement in enumerate(rec['movements'], 1):
                    st.write(f"   {j}. Из **{movement['from']}** ({movement['from_type']}) → **{movement['quantity']} шт**")
                    st.write(f"      У донора было: {movement['from_days_before']} дней запаса")
            
            with col2:
                # Метрики
                st.metric("Срочность", f"{rec['urgency']}%")
                st.metric("Приоритет", rec['priority'])
                st.metric("ADS", f"{rec['ads']:.2f}")
                
                # Цветовой индикатор срочности
                if rec['urgency'] > 80:
                    st.error("🔴 Критично")
                elif rec['urgency'] > 50:
                    st.warning("🟡 Срочно")
                else:
                    st.success("🟢 Нормально")

def show_purchase_recommendations_tab(engine: MovementRecommendationEngine):
    """Вкладка с рекомендациями по закупкам"""
    
    purchases = engine.purchase_recommendations
    
    if not purchases:
        st.info("📝 Рекомендации по закупкам не найдены. У вас достаточно товаров в системе!")
        return
    
    st.subheader(f"🛒 Найдено {len(purchases)} рекомендаций по закупкам")
    
    # Сводная статистика по закупкам
    total_to_purchase = sum(p['to_purchase'] for p in purchases)
    total_cost = sum(p.get('total_cost', 0) for p in purchases if 'total_cost' in p)
    critical_purchases = len([p for p in purchases if p['urgency'] > 80])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Общее количество к закупке", f"{total_to_purchase:,.0f} шт")
    with col2:
        if total_cost > 0:
            st.metric("Общая стоимость", f"{total_cost:,.2f} ₽")
        else:
            st.metric("Общая стоимость", "Нет данных о ценах")
    with col3:
        st.metric("Критичных закупок", critical_purchases)
    
    # Фильтры
    col1, col2 = st.columns(2)
    with col1:
        urgency_filter_p = st.slider("Минимальная срочность закупки (%)", 0, 100, 0, key="purchase_urgency")
    with col2:
        min_cost_filter = st.number_input("Минимальная стоимость", min_value=0.0, value=0.0, key="min_cost")
    
    # Применяем фильтры
    filtered_purchases = purchases.copy()
    filtered_purchases = [p for p in filtered_purchases if p['urgency'] >= urgency_filter_p]
    if min_cost_filter > 0:
        filtered_purchases = [p for p in filtered_purchases if p.get('total_cost', 0) >= min_cost_filter]
    
    st.info(f"Показано {len(filtered_purchases)} из {len(purchases)} рекомендаций")
    
    # Таблица закупок
    if filtered_purchases:
        purchase_data = []
        for p in filtered_purchases:
            row = {
                'Товар': p['item_name'],
                'К закупке (шт)': p['to_purchase'],
                'Текущий запас (шт)': p['current_total_stock'],
                'Текущий запас (дни)': p['current_days_supply'],
                'ADS': f"{p['ads']:.2f}",
                'Срочность (%)': p['urgency'],
                'Причина': p['reason']
            }
            
            if 'total_cost' in p:
                row['Стоимость (₽)'] = f"{p['total_cost']:,.2f}"
                row['Цена за шт (₽)'] = f"{p['unit_price']:.2f}"
            
            purchase_data.append(row)
        
                        
                df_purchases = pd.DataFrame(purchase_data)
                df_purchases.to_excel(writer, sheet_name='Рекомендации_закупки', index=False)
            
            # Лист 4: Анализ по точкам
            location_stats = engine.analysis_summary['location_stats']
            if location_stats:
                location_data = []
                for location, stats in location_stats.items():
                    location_data.append({
                        'Точка': location,
                        'Тип': stats['type'],
                        'Всего товаров': stats['total_items'],
                        'С излишками': stats['surplus_items'],
                        'С дефицитом': stats['deficit_items'],
                        'В норме': stats['normal_items'],
                        'Проблемных (%)': round((stats['surplus_items'] + stats['deficit_items']) / max(stats['total_items'], 1) * 100, 1)
                    })
                
                df_locations = pd.DataFrame(location_data)
                df_locations = df_locations.sort_values('Проблемных (%)', ascending=False)
                df_locations.to_excel(writer, sheet_name='Анализ_по_точкам', index=False)
            
            # Лист 5: Детальный анализ товаров
            if engine.location_analysis:
                detailed_data = []
                for item in engine.location_analysis:
                    for location, data in item['locations'].items():
                        detailed_data.append({
                            'Товар': item['item_name'],
                            'Точка': location,
                            'Тип точки': data['type'],
                            'Текущий остаток (шт)': data['current_stock'],
                            'Минимальный норматив (шт)': data['min_stock'],
                            'Оптимальный норматив (шт)': data['optimal_stock'],
                            'Максимальный норматив (шт)': data['max_stock'],
                            'Дни запаса': data['days_of_stock'],
                            'Статус': data['status'],
                            'Срочность (%)': data['urgency'],
                            'ADS': item['ads']
                        })
                
                df_detailed = pd.DataFrame(detailed_data)
                df_detailed.to_excel(writer, sheet_name='Детальный_анализ', index=False)
            
            # Лист 6: Ключевые выводы
            conclusions = generate_key_conclusions(engine)
            conclusion_data = []
            for i, conclusion in enumerate(conclusions, 1):
                conclusion_data.append({
                    '№': i,
                    'Тип': conclusion['type'],
                    'Вывод': conclusion['text']
                })
            
            if conclusion_data:
                df_conclusions = pd.DataFrame(conclusion_data)
                df_conclusions.to_excel(writer, sheet_name='Ключевые_выводы', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Ошибка создания Excel отчета: {str(e)}")
        return None

# ===== ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ЗАПУСКА =====

def main():
    """Основная функция для запуска страницы рекомендаций"""
    show_movement_recommendations_page()

if __name__ == "__main__":
    main()

# ===== ИНТЕГРАЦИЯ С ОСНОВНЫМ ПРИЛОЖЕНИЕМ =====

def add_movement_recommendations_to_main_app():
    """
    Функция для интеграции с основным приложением
    Добавьте эту функцию в ваш main streamlit app
    """
    
    # В основном приложении добавьте в меню:
    page_selection = st.sidebar.selectbox(
        "Выберите страницу",
        ["Главная", "ABC анализ", "Остатки", "🚚 Рекомендации по перемещениям"]
    )
    
    if page_selection == "🚚 Рекомендации по перемещениям":
        show_movement_recommendations_page()

# ===== ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ =====

def integration_instructions():
    """Инструкция по интеграции с существующей системой"""
    
    st.markdown("""
    ## 🔧 Инструкция по интеграции
    
    ### 1. Добавление в существующее приложение
    
    1. Сохраните этот файл как `movement_recommendations.py` в папке с вашим проектом
    
    2. В главном файле `streamlit_modular_app.py` добавьте импорт:
    ```python
    from movement_recommendations import show_movement_recommendations_page
    ```
    
    3. Добавьте новую страницу в навигацию:
    ```python
    page_selection = st.sidebar.selectbox(
        "Выберите страницу",
        ["Главная", "ABC анализ", "Остатки", "🚚 Рекомендации по перемещениям"]
    )
    
    if page_selection == "🚚 Рекомендации по перемещениям":
        show_movement_recommendations_page()
    ```
    
    ### 2. Требования к данным
    
    Система требует наличия в `st.session_state.inventory_system`:
    - `calculated_ads` - DataFrame с колонками ['номенклатура', 'ads']
    - `stock_data` - DataFrame с колонками ['номенклатура', 'точка1', 'точка2', ...]
    
    ### 3. Настройка под ваш бизнес
    
    Отредактируйте `MovementConfig.STOCK_NORMS` для ваших нормативов:
    ```python
    STOCK_NORMS = {
        'магазин': {'min_days': 7, 'optimal_days': 14, 'max_days': 21},
        'склад': {'min_days': 30, 'optimal_days': 60, 'max_days': 90},
        'хаб': {'min_days': 60, 'optimal_days': 120, 'max_days': 180}
    }
    ```
    
    ### 4. Интеграция с Telegram ботом
    
    Добавьте в `telegram_bot.py`:
    ```python
    from movement_recommendations import MovementRecommendationEngine
    
    @bot.message_handler(commands=['movements'])
    def handle_movements_command(message):
        if 'inventory_system' in globals():
            engine = MovementRecommendationEngine(inventory_system)
            result = engine.run_full_analysis()
            
            if result['success']:
                report = f"📊 Анализ завершен!\\n"
                report += f"Товаров: {result['analyzed_items']}\\n"
                report += f"Перемещений: {result['movement_recommendations']}\\n"
                report += f"Закупок: {result['purchase_recommendations']}"
                bot.send_message(message.chat.id, report)
            else:
                bot.send_message(message.chat.id, f"❌ {result['error']}")
    ```
    
    ### 5. Автоматические отчеты
    
    Для ежедневных автоматических отчетов добавьте:
    ```python
    import schedule
    import time
    
    def daily_movement_report():
        # Запуск анализа и отправка отчета
        pass
    
    schedule.every().day.at("09:00").do(daily_movement_report)
    ```
    
    ### 6. Кастомизация классификации точек
    
    Отредактируйте `get_location_type()` под ваши названия:
    ```python
    @classmethod
    def get_location_type(cls, location_name: str) -> str:
        location_lower = location_name.lower()
        
        # Добавьте ваши ключевые слова
        if any(word in location_lower for word in ['ваши_магазины']):
            return 'магазин'
        # ...
    ```
    """)

if __name__ == "__main__":
    # Если запускается напрямую, показываем инструкцию
    st.title("🚚 Система рекомендаций по перемещениям")
    st.subheader("Модуль для интеграции с существующей системой")
    integration_instructions()
        st.dataframe(df_purchases, use_container_width=True)
        
        # Детализация по каждой закупке
        st.subheader("📋 Детализация закупок")
        
        for i, purchase in enumerate(filtered_purchases[:10], 1):
            with st.expander(f"#{i} {purchase['item_name']} - {purchase['to_purchase']} шт"):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**📦 К закупке:** {purchase['to_purchase']} шт")
                    st.write(f"**📊 Текущий общий запас:** {purchase['current_total_stock']} шт ({purchase['current_days_supply']} дней)")
                    st.write(f"**🎯 Рекомендуемый запас:** {purchase['recommended_total_stock']} шт")
                    st.write(f"**📈 ADS:** {purchase['ads']:.2f} шт/день")
                    st.write(f"**⚠️ Причина:** {purchase['reason']}")
                    
                    if purchase['critical_deficit'] > 0:
                        st.warning(f"🚨 Критичный дефицит: {purchase['critical_deficit']} шт")
                    
                    if 'total_cost' in purchase:
                        st.write(f"**💰 Стоимость:** {purchase['total_cost']:,.2f} ₽ ({purchase['unit_price']:.2f} ₽/шт)")
                
                with col2:
                    st.metric("Срочность", f"{purchase['urgency']}%")
                    st.metric("Дней до нуля", f"{purchase['current_days_supply']:.1f}")
                    
                    if purchase['urgency'] > 80:
                        st.error("🔴 Критично")
                    elif purchase['urgency'] > 50:
                        st.warning("🟡 Срочно")
                    else:
                        st.info("🔵 Планово")

def show_location_analysis_tab(engine: MovementRecommendationEngine):
    """Вкладка с анализом по точкам"""
    
    if not engine.analysis_summary:
        st.info("Анализ не выполнен")
        return
    
    st.subheader("🏪 Анализ по точкам продаж")
    
    location_stats = engine.analysis_summary['location_stats']
    
    if not location_stats:
        st.info("Нет данных по точкам")
        return
    
    # Создаем DataFrame для отображения
    location_data = []
    for location, stats in location_stats.items():
        location_data.append({
            'Точка': location,
            'Тип': stats['type'],
            'Всего товаров': stats['total_items'],
            'С излишками': stats['surplus_items'],
            'С дефицитом': stats['deficit_items'],
            'В норме': stats['normal_items'],
            'Проблемных (%)': round((stats['surplus_items'] + stats['deficit_items']) / max(stats['total_items'], 1) * 100, 1)
        })
    
    df_locations = pd.DataFrame(location_data)
    df_locations = df_locations.sort_values('Проблемных (%)', ascending=False)
    
    # Отображаем таблицу
    st.dataframe(df_locations, use_container_width=True)
    
    # Статистика по типам точек
    st.subheader("📊 Статистика по типам точек")
    
    type_stats = {}
    for location, stats in location_stats.items():
        loc_type = stats['type']
        if loc_type not in type_stats:
            type_stats[loc_type] = {
                'locations': 0,
                'total_items': 0,
                'surplus_items': 0,
                'deficit_items': 0,
                'normal_items': 0
            }
        
        type_stats[loc_type]['locations'] += 1
        type_stats[loc_type]['total_items'] += stats['total_items']
        type_stats[loc_type]['surplus_items'] += stats['surplus_items']
        type_stats[loc_type]['deficit_items'] += stats['deficit_items']
        type_stats[loc_type]['normal_items'] += stats['normal_items']
    
    # Отображаем по типам
    for loc_type, stats in type_stats.items():
        with st.expander(f"📍 {loc_type.title()} ({stats['locations']} точек)"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего товаров", stats['total_items'])
            with col2:
                st.metric("С излишками", stats['surplus_items'])
            with col3:
                st.metric("С дефицитом", stats['deficit_items'])
            with col4:
                problem_pct = round((stats['surplus_items'] + stats['deficit_items']) / max(stats['total_items'], 1) * 100, 1)
                st.metric("Проблемных (%)", f"{problem_pct}%")

def show_visualization_tab(engine: MovementRecommendationEngine):
    """Вкладка с визуализацией"""
    
    if not engine.analysis_summary:
        st.info("Анализ не выполнен")
        return
    
    st.subheader("📈 Визуализация результатов")
    
    # График по типам проблем
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение проблем")
        
        summary = engine.analysis_summary
        
        problem_data = {
            'Тип': ['Товары с излишками', 'Товары с дефицитом', 'Товары в норме'],
            'Количество': [
                summary['surplus_stats']['total_items_with_surplus'],
                summary['deficit_stats']['total_items_with_deficit'],
                summary['total_items'] - summary['surplus_stats']['total_items_with_surplus'] - summary['deficit_stats']['total_items_with_deficit']
            ]
        }
        
        fig_problems = px.pie(
            values=problem_data['Количество'],
            names=problem_data['Тип'],
            title="Распределение товаров по статусу"
        )
        st.plotly_chart(fig_problems, use_container_width=True)
    
    with col2:
        st.subheader("Эффективность системы")
        
        efficiency = summary['movement_efficiency']
        
        fig_efficiency = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=efficiency,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Покрытие дефицитов (%)"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    # График по точкам
    st.subheader("Анализ по точкам продаж")
    
    location_stats = engine.analysis_summary['location_stats']
    
    if location_stats:
        # Подготавливаем данные для графика
        locations = []
        types = []
        surplus_counts = []
        deficit_counts = []
        normal_counts = []
        
        for location, stats in location_stats.items():
            locations.append(location[:20] + '...' if len(location) > 20 else location)  # Обрезаем длинные названия
            types.append(stats['type'])
            surplus_counts.append(stats['surplus_items'])
            deficit_counts.append(stats['deficit_items'])
            normal_counts.append(stats['normal_items'])
        
        # Создаем stacked bar chart
        fig_locations = go.Figure()
        
        fig_locations.add_trace(go.Bar(
            name='Излишки',
            x=locations,
            y=surplus_counts,
            marker_color='orange'
        ))
        
        fig_locations.add_trace(go.Bar(
            name='Дефициты',
            x=locations,
            y=deficit_counts,
            marker_color='red'
        ))
        
        fig_locations.add_trace(go.Bar(
            name='В норме',
            x=locations,
            y=normal_counts,
            marker_color='green'
        ))
        
        fig_locations.update_layout(
            barmode='stack',
            title='Распределение статусов товаров по точкам',
            xaxis_title='Точки продаж',
            yaxis_title='Количество товаров',
            xaxis={'tickangle': 45}
        )
        
        st.plotly_chart(fig_locations, use_container_width=True)

def show_full_report_tab(engine: MovementRecommendationEngine):
    """Полный отчет с возможностью экспорта"""
    
    st.subheader("📋 Полный отчет системы рекомендаций")
    
    if not engine.analysis_summary:
        st.info("Анализ не выполнен")
        return
    
    # Кнопка экспорта
    if st.button("📥 Экспорт полного отчета в Excel", type="primary"):
        excel_buffer = create_full_excel_report(engine)
        if excel_buffer:
            st.download_button(
                label="📁 Скачать отчет",
                data=excel_buffer,
                file_name=f"movement_recommendations_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.divider()
    
    # Исполнительная сводка
    st.subheader("📊 Исполнительная сводка")
    
    summary = engine.analysis_summary
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Товаров проанализировано", summary['total_items'])
        st.metric("🚚 Рекомендаций по перемещению", summary['total_movement_recs'])
        st.metric("🛒 Рекомендаций по закупке", summary['total_purchase_recs'])
    
    with col2:
        st.metric("📈 Товаров с излишками", summary['surplus_stats']['total_items_with_surplus'])
        st.metric("📉 Товаров с дефицитом", summary['deficit_stats']['total_items_with_deficit'])
        st.metric("⚠️ Критичных дефицитов", summary['deficit_stats']['critical_deficits'])
    
    with col3:
        st.metric("✅ Эффективность покрытия", f"{summary['movement_efficiency']}%")
        if 'money_stats' in summary and summary['money_stats']:
            st.metric("💰 Стоимость закупок", f"{summary['money_stats']['purchase_cost']:,.2f} ₽")
        
        # Общая оценка системы
        if summary['movement_efficiency'] > 80:
            st.success("🟢 Отличная эффективность")
        elif summary['movement_efficiency'] > 60:
            st.warning("🟡 Хорошая эффективность")
        else:
            st.error("🔴 Требует внимания")
    
    # Ключевые выводы
    st.subheader("🎯 Ключевые выводы и рекомендации")
    
    conclusions = generate_key_conclusions(engine)
    for conclusion in conclusions:
        if conclusion['type'] == 'success':
            st.success(conclusion['text'])
        elif conclusion['type'] == 'warning':
            st.warning(conclusion['text'])
        elif conclusion['type'] == 'error':
            st.error(conclusion['text'])
        else:
            st.info(conclusion['text'])
    
    # Детальная таблица всех рекомендаций
    st.subheader("📋 Все рекомендации по перемещениям")
    
    if engine.movement_recommendations:
        movement_table_data = []
        for i, rec in enumerate(engine.movement_recommendations, 1):
            for j, movement in enumerate(rec['movements']):
                movement_table_data.append({
                    '№': i if j == 0 else '',
                    'Товар': rec['item_name'] if j == 0 else '',
                    'Получатель': rec['to'] if j == 0 else '',
                    'Тип получателя': rec['to_type'] if j == 0 else '',
                    'Дефицит (шт)': rec['needed'] if j == 0 else '',
                    'Донор': movement['from'],
                    'Тип донора': movement['from_type'],
                    'Количество': movement['quantity'],
                    'Срочность (%)': rec['urgency'] if j == 0 else '',
                    'ADS': f"{rec['ads']:.2f}" if j == 0 else ''
                })
        
        df_movements = pd.DataFrame(movement_table_data)
        st.dataframe(df_movements, use_container_width=True)
    else:
        st.info("Рекомендации по перемещениям отсутствуют")
    
    # Детальная таблица закупок
    st.subheader("🛒 Все рекомендации по закупкам")
    
    if engine.purchase_recommendations:
        purchase_table_data = []
        for i, purchase in enumerate(engine.purchase_recommendations, 1):
            row = {
                '№': i,
                'Товар': purchase['item_name'],
                'К закупке (шт)': purchase['to_purchase'],
                'Текущий запас (шт)': purchase['current_total_stock'],
                'Рекомендуемый запас (шт)': purchase['recommended_total_stock'],
                'Текущий запас (дни)': purchase['current_days_supply'],
                'ADS': f"{purchase['ads']:.2f}",
                'Срочность (%)': purchase['urgency'],
                'Причина': purchase['reason']
            }
            
            if 'total_cost' in purchase:
                row['Стоимость (₽)'] = f"{purchase['total_cost']:,.2f}"
            
            purchase_table_data.append(row)
        
        df_purchases = pd.DataFrame(purchase_table_data)
        st.dataframe(df_purchases, use_container_width=True)
    else:
        st.info("Рекомендации по закупкам отсутствуют")

def generate_key_conclusions(engine: MovementRecommendationEngine) -> List[Dict]:
    """Генерация ключевых выводов"""
    
    conclusions = []
    summary = engine.analysis_summary
    
    # Анализ общей ситуации
    if summary['total_movement_recs'] == 0 and summary['total_purchase_recs'] == 0:
        conclusions.append({
            'type': 'success',
            'text': '🎉 Отлично! Ваша система складов работает оптимально. Критичных перемещений и закупок не требуется.'
        })
    
    # Анализ перемещений
    if summary['total_movement_recs'] > 0:
        efficiency = summary['movement_efficiency']
        if efficiency > 80:
            conclusions.append({
                'type': 'success',
                'text': f'✅ Высокая эффективность перемещений: {efficiency}% дефицитов можно покрыть внутренними ресурсами.'
            })
        elif efficiency > 50:
            conclusions.append({
                'type': 'warning',
                'text': f'⚠️ Средняя эффективность перемещений: {efficiency}%. Рекомендуется оптимизировать распределение товаров.'
            })
        else:
            conclusions.append({
                'type': 'error',
                'text': f'🚨 Низкая эффективность перемещений: {efficiency}%. Необходимо увеличить закупки.'
            })
    
    # Анализ дефицитов
    critical_deficits = summary['deficit_stats']['critical_deficits']
    if critical_deficits > 0:
        conclusions.append({
            'type': 'error',
            'text': f'🚨 Обнаружено {critical_deficits} критичных дефицитов! Требуется немедленное внимание.'
        })
    
    # Анализ излишков
    high_surplus = summary['surplus_stats']['high_surplus']
    if high_surplus > 0:
        conclusions.append({
            'type': 'warning',
            'text': f'📦 Обнаружено {high_surplus} значительных излишков. Рассмотрите перераспределение или снижение закупок.'
        })
    
    # Анализ по типам точек
    location_stats = summary['location_stats']
    
    # Анализируем магазины
    magazine_problems = 0
    total_magazines = 0
    
    for location, stats in location_stats.items():
        if stats['type'] == 'магазин':
            total_magazines += 1
            if stats['deficit_items'] > 0:
                magazine_problems += 1
    
    if magazine_problems > 0:
        conclusions.append({
            'type': 'error',
            'text': f'🏪 {magazine_problems} из {total_magazines} магазинов имеют дефициты. Приоритет - обеспечение магазинов!'
        })
    
    # Рекомендации по закупкам
    if summary['total_purchase_recs'] > 0:
        urgent_purchases = len([p for p in engine.purchase_recommendations if p['urgency'] > 80])
        if urgent_purchases > 0:
            conclusions.append({
                'type': 'error',
                'text': f'🛒 {urgent_purchases} срочных закупок из {summary["total_purchase_recs"]}. Планируйте закупки заранее!'
            })
        else:
            conclusions.append({
                'type': 'info',
                'text': f'📋 {summary["total_purchase_recs"]} плановых закупок. Хорошее планирование запасов.'
            })
    
    # Денежный анализ
    if 'money_stats' in summary and summary['money_stats']:
        money = summary['money_stats']
        if money['purchase_cost'] > 0:
            conclusions.append({
                'type': 'info',
                'text': f'💰 Общая стоимость рекомендуемых закупок: {money["purchase_cost"]:,.2f} ₽'
            })
    
    return conclusions

def create_full_excel_report(engine: MovementRecommendationEngine) -> bytes:
    """Создание полного Excel отчета"""
    
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Лист 1: Сводка
            summary_data = []
            summary = engine.analysis_summary
            
            summary_data.append(['ОТЧЕТ СИСТЕМЫ РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ', ''])
            summary_data.append(['Дата создания', datetime.now().strftime('%Y-%m-%d %H:%M')])
            summary_data.append(['', ''])
            summary_data.append(['ОБЩАЯ СТАТИСТИКА', ''])
            summary_data.append(['Товаров проанализировано', summary['total_items']])
            summary_data.append(['Рекомендаций по перемещению', summary['total_movement_recs']])
            summary_data.append(['Рекомендаций по закупке', summary['total_purchase_recs']])
            summary_data.append(['Эффективность покрытия (%)', summary['movement_efficiency']])
            summary_data.append(['', ''])
            summary_data.append(['ПРОБЛЕМЫ', ''])
            summary_data.append(['Товаров с излишками', summary['surplus_stats']['total_items_with_surplus']])
            summary_data.append(['Товаров с дефицитом', summary['deficit_stats']['total_items_with_deficit']])
            summary_data.append(['Критичных дефицитов', summary['deficit_stats']['critical_deficits']])
            summary_data.append(['Значительных излишков', summary['surplus_stats']['high_surplus']])
            
            df_summary = pd.DataFrame(summary_data, columns=['Показатель', 'Значение'])
            df_summary.to_excel(writer, sheet_name='Сводка', index=False)
            
            # Лист 2: Рекомендации по перемещениям
            if engine.movement_recommendations:
                movement_data = []
                for i, rec in enumerate(engine.movement_recommendations, 1):
                    for j, movement in enumerate(rec['movements']):
                        movement_data.append({
                            '№': i if j == 0 else '',
                            'Товар': rec['item_name'] if j == 0 else '',
                            'Получатель': rec['to'] if j == 0 else '',
                            'Тип получателя': rec['to_type'] if j == 0 else '',
                            'Дни запаса до': rec['to_days_before'] if j == 0 else '',
                            'Дефицит (шт)': rec['needed'] if j == 0 else '',
                            'Покроется (шт)': rec['covered'] if j == 0 else '',
                            'Остается дефицит': rec['remaining_deficit'] if j == 0 else '',
                            'Донор': movement['from'],
                            'Тип донора': movement['from_type'],
                            'Количество к перемещению': movement['quantity'],
                            'Дни запаса у донора': movement['from_days_before'],
                            'Срочность (%)': rec['urgency'] if j == 0 else '',
                            'Приоритет': rec['priority'] if j == 0 else '',
                            'ADS': rec['ads'] if j == 0 else ''
                        })
                
                df_movements = pd.DataFrame(movement_data)
                df_movements.to_excel(writer, sheet_name='Рекомендации_перемещения', index=False)
            
            # Лист 3: Рекомендации по закупкам
            if engine.purchase_recommendations:
                purchase_data = []
                for i, purchase in enumerate(engine.purchase_recommendations, 1):
                    row = {
                        '№': i,
                        'Товар': purchase['item_name'],
                        'К закупке (шт)': purchase['to_purchase'],
                        'Текущий общий запас (шт)': purchase['current_total_stock'],
                        'Рекомендуемый запас (шт)': purchase['recommended_total_stock'],
                        'Текущий запас (дни)': purchase['current_days_supply'],
                        'Критичный дефицит (шт)': purchase['critical_deficit'],
                        'ADS': purchase['ads'],
                        'Срочность (%)': purchase['urgency'],
                        'Причина': purchase['reason']
                    }
                    
                    if 'total_cost' in purchase:
                        row['Стоимость (₽)'] = purchase['total_cost']
                        row['Цена за шт (₽)'] = purchase['unit_price']
                    
                    purchase_data.append(row) for r in filtered_recs if r['priority'] == priority_map[priority_filter]]
    
    filtered_recs = [r