#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABC анализ по подкатегориям для системы автоматизации товарных запасов
ИСПРАВЛЕННАЯ ВЕРСИЯ: подкатегории во 2-м столбце, категории в 3-м
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class SubcategoryABCAnalyzer:
    """Класс для ABC анализа по подкатегориям"""
    
    def __init__(self):
        self.abc_data = None
        self.subcategory_results = None
        self.category_subcategory_mapping = {}
        self.pareto_analysis = None
        
    def load_data_with_subcategories(self, abc_data: pd.DataFrame) -> Dict:
        """
        Загрузка данных с поддержкой подкатегорий
        ИСПРАВЛЕНО: подкатегории во 2-м столбце, категории в 3-м
        
        Args:
            abc_data: DataFrame с данными ABC анализа
            
        Returns:
            Dict с информацией о загруженных данных
        """
        try:
            if abc_data is None or abc_data.empty:
                return {'success': False, 'error': 'Нет данных для анализа'}
            
            # Проверяем наличие необходимых колонок
            required_columns = ['nomenclature', 'annual_sales']
            missing_columns = [col for col in required_columns if col not in abc_data.columns]
            
            if missing_columns:
                return {'success': False, 'error': f'Отсутствуют колонки: {missing_columns}'}
            
            # Обрабатываем подкатегории с ИСПРАВЛЕННЫМ порядком колонок
            self.abc_data = abc_data.copy()
            
            print("🔍 Анализ структуры данных:")
            print(f"Колонки: {list(self.abc_data.columns)}")
            print(f"Количество колонок: {len(self.abc_data.columns)}")
            
            # ИСПРАВЛЕННАЯ логика определения колонок
            if len(self.abc_data.columns) >= 4:
                # Ожидаемый порядок: nomenclature, subcategory, category, annual_sales
                col_names = list(self.abc_data.columns)
                
                # Определяем колонки по позиции
                nomenclature_col = col_names[0]  # 1-я колонка
                subcategory_col = col_names[1]   # 2-я колонка - ПОДКАТЕГОРИИ
                category_col = col_names[2]      # 3-я колонка - КАТЕГОРИИ  
                sales_col = col_names[3]         # 4-я колонка - продажи
                
                print(f"📋 Определены колонки:")
                print(f"  Номенклатура: {nomenclature_col}")
                print(f"  Подкатегория: {subcategory_col} (2-я колонка)")
                print(f"  Категория: {category_col} (3-я колонка)")
                print(f"  Продажи: {sales_col}")
                
                # Переименовываем колонки в стандартные названия
                column_mapping = {
                    nomenclature_col: 'nomenclature',
                    subcategory_col: 'subcategory', 
                    category_col: 'category',
                    sales_col: 'annual_sales'
                }
                
                # Применяем только для существующих колонок
                existing_mapping = {k: v for k, v in column_mapping.items() if k in self.abc_data.columns}
                self.abc_data = self.abc_data.rename(columns=existing_mapping)
                
            else:
                # Если недостаточно колонок, создаем базовую структуру
                if 'subcategory' not in self.abc_data.columns:
                    if 'category' in self.abc_data.columns:
                        self.abc_data['subcategory'] = self.abc_data['category'].astype(str) + '_подкат'
                    else:
                        self.abc_data['subcategory'] = 'Общая подкатегория'
                        self.abc_data['category'] = 'Общая категория'
                
                if 'category' not in self.abc_data.columns:
                    # Пытаемся извлечь категорию из подкатегории
                    self.abc_data['category'] = self.abc_data['subcategory'].apply(
                        lambda x: str(x).split('_')[0] if '_' in str(x) else str(x)
                    )
            
            # Очистка данных
            self.abc_data = self._clean_subcategory_data()
            
            # Создаем маппинг категория -> подкатегории
            self._create_category_mapping()
            
            # Статистика загруженных данных
            total_items = len(self.abc_data)
            categories_count = self.abc_data['category'].nunique()
            subcategories_count = self.abc_data['subcategory'].nunique()
            items_with_sales = len(self.abc_data[self.abc_data['annual_sales'] > 0])
            total_sales = self.abc_data['annual_sales'].sum()
            
            print(f"✅ Данные загружены:")
            print(f"  Товаров: {total_items}")
            print(f"  Категорий: {categories_count}")
            print(f"  Подкатегорий: {subcategories_count}")
            print(f"  С продажами: {items_with_sales}")
            
            return {
                'success': True,
                'total_items': total_items,
                'categories_count': categories_count,
                'subcategories_count': subcategories_count,
                'items_with_sales': items_with_sales,
                'items_with_zero_sales': total_items - items_with_sales,
                'total_sales': float(total_sales),
                'average_sales': float(self.abc_data['annual_sales'].mean()),
                'subcategories_per_category': round(subcategories_count / categories_count, 1) if categories_count > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Ошибка загрузки данных: {str(e)}'}
    
    def _clean_subcategory_data(self) -> pd.DataFrame:
        """Очистка данных для анализа подкатегорий"""
        df = self.abc_data.copy()
        
        # Очистка подкатегорий
        df['subcategory'] = df['subcategory'].astype(str).str.strip()
        df['subcategory'] = df['subcategory'].replace(['nan', 'None', ''], 'Без подкатегории')
        
        # Очистка категорий
        df['category'] = df['category'].astype(str).str.strip()
        df['category'] = df['category'].replace(['nan', 'None', ''], 'Без категории')
        
        # Заполнение пустых подкатегорий из категорий
        mask_empty_subcategory = df['subcategory'] == 'Без подкатегории'
        mask_valid_category = df['category'] != 'Без категории'
        
        df.loc[mask_empty_subcategory & mask_valid_category, 'subcategory'] = \
            df.loc[mask_empty_subcategory & mask_valid_category, 'category'] + '_основная'
        
        # Убеждаемся что продажи в правильном формате
        df['annual_sales'] = pd.to_numeric(df['annual_sales'], errors='coerce').fillna(0)
        
        return df
    
    def _create_category_mapping(self):
        """Создание маппинга категорий и подкатегорий"""
        for _, row in self.abc_data.iterrows():
            category = row['category']
            subcategory = row['subcategory']
            
            if category not in self.category_subcategory_mapping:
                self.category_subcategory_mapping[category] = set()
            
            self.category_subcategory_mapping[category].add(subcategory)
        
        # Преобразуем в список для удобства
        for category in self.category_subcategory_mapping:
            self.category_subcategory_mapping[category] = list(self.category_subcategory_mapping[category])
    
    def perform_subcategory_abc_analysis(self) -> Dict:
        """
        Выполнение ABC анализа по подкатегориям
        
        Returns:
            Dict с результатами анализа
        """
        if self.abc_data is None:
            return {'success': False, 'error': 'Данные не загружены'}
        
        try:
            results = {}
            
            print(f"🔄 Начинаем ABC анализ для {self.abc_data['subcategory'].nunique()} подкатегорий...")
            
            # Анализ по каждой подкатегории
            for subcategory in self.abc_data['subcategory'].unique():
                if pd.isna(subcategory) or str(subcategory).strip() == '':
                    continue
                
                subcategory_data = self.abc_data[self.abc_data['subcategory'] == subcategory].copy()
                
                if len(subcategory_data) == 0:
                    continue
                
                # Сортируем по продажам
                subcategory_data = subcategory_data.sort_values('annual_sales', ascending=False)
                
                # Рассчитываем проценты
                total_subcategory_sales = subcategory_data['annual_sales'].sum()
                
                if total_subcategory_sales > 0:
                    subcategory_data['sales_percentage'] = (subcategory_data['annual_sales'] / total_subcategory_sales) * 100
                    subcategory_data['cumulative_percentage'] = subcategory_data['sales_percentage'].cumsum()
                    
                    # Присваиваем ABC классы
                    subcategory_data['abc_class'] = subcategory_data['cumulative_percentage'].apply(
                        lambda x: 'A' if x <= 80 else 'B' if x <= 95 else 'C'
                    )
                else:
                    # Для подкатегорий без продаж
                    subcategory_data['sales_percentage'] = 0
                    subcategory_data['cumulative_percentage'] = 100
                    subcategory_data['abc_class'] = 'C'
                
                # Статистика по подкатегории
                abc_distribution = subcategory_data['abc_class'].value_counts().to_dict()
                category = subcategory_data['category'].iloc[0] if len(subcategory_data) > 0 else 'Неизвестно'
                
                # ОТЛАДКА: проверяем логику ABC классификации
                print(f"🔍 ABC для '{subcategory}':")
                print(f"   Товаров: {len(subcategory_data)}")
                print(f"   ABC распределение: {abc_distribution}")
                print(f"   Проверка: A={abc_distribution.get('A', 0)}, B={abc_distribution.get('B', 0)}, C={abc_distribution.get('C', 0)}")
                print(f"   Сумма: {abc_distribution.get('A', 0) + abc_distribution.get('B', 0) + abc_distribution.get('C', 0)}")
                
                # Проверяем что сумма ABC равна общему количеству товаров
                abc_sum = abc_distribution.get('A', 0) + abc_distribution.get('B', 0) + abc_distribution.get('C', 0)
                if abc_sum != len(subcategory_data):
                    print(f"⚠️ ПРОБЛЕМА: Сумма ABC ({abc_sum}) не равна количеству товаров ({len(subcategory_data)})")
                
                results[subcategory] = {
                    'category': category,
                    'total_items': len(subcategory_data),
                    'total_sales': float(total_subcategory_sales),
                    'average_sales': float(subcategory_data['annual_sales'].mean()),
                    'abc_distribution': {
                        'A': abc_distribution.get('A', 0),
                        'B': abc_distribution.get('B', 0),
                        'C': abc_distribution.get('C', 0)
                    },
                    'items_with_sales': len(subcategory_data[subcategory_data['annual_sales'] > 0]),
                    'items_with_zero_sales': len(subcategory_data[subcategory_data['annual_sales'] == 0]),
                    'top_items': subcategory_data.head(3)[['nomenclature', 'annual_sales', 'abc_class']].to_dict('records'),
                    'abc_data': subcategory_data
                }
            
            self.subcategory_results = results
            
            # Общая статистика
            total_subcategories = len(results)
            total_items = sum(r['total_items'] for r in results.values())
            total_sales = sum(r['total_sales'] for r in results.values())
            
            print(f"✅ ABC анализ завершен:")
            print(f"  Подкатегорий: {total_subcategories}")
            print(f"  Товаров: {total_items}")
            print(f"  Общие продажи: {total_sales:,.0f}")
            
            return {
                'success': True,
                'total_subcategories': total_subcategories,
                'total_items': total_items,
                'total_sales': float(total_sales),
                'subcategory_results': results,
                'categories_analyzed': len(set(r['category'] for r in results.values()))
            }
            
        except Exception as e:
            print(f"❌ Ошибка ABC анализа: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Ошибка ABC анализа: {str(e)}'}
    
    def get_subcategory_analysis_by_category(self) -> Dict:
        """Получение анализа подкатегорий, сгруппированного по категориям"""
        if not self.subcategory_results:
            return {}
        
        category_analysis = {}
        
        for subcategory, data in self.subcategory_results.items():
            category = data['category']
            
            if category not in category_analysis:
                category_analysis[category] = {
                    'subcategories': [],
                    'total_items': 0,
                    'total_sales': 0,
                    'subcategories_count': 0,
                    'abc_distribution_total': {'A': 0, 'B': 0, 'C': 0}
                }
            
            category_analysis[category]['subcategories'].append({
                'name': subcategory,
                'items': data['total_items'],
                'sales': data['total_sales'],
                'abc_distribution': data['abc_distribution'],
                'items_with_sales': data['items_with_sales']
            })
            
            category_analysis[category]['total_items'] += data['total_items']
            category_analysis[category]['total_sales'] += data['total_sales']
            category_analysis[category]['subcategories_count'] += 1
            
            # Суммируем ABC распределение
            for abc_class in ['A', 'B', 'C']:
                category_analysis[category]['abc_distribution_total'][abc_class] += data['abc_distribution'][abc_class]
        
        return category_analysis
    
    def create_subcategory_visualizations(self) -> Dict:
        """Создание визуализаций для анализа подкатегорий"""
        if not self.subcategory_results:
            return {}
        
        visualizations = {}
        
        # 1. Распределение товаров по подкатегориям
        subcategory_items = []
        subcategory_sales = []
        subcategory_names = []
        
        for subcategory, data in self.subcategory_results.items():
            subcategory_names.append(subcategory[:30] + '...' if len(subcategory) > 30 else subcategory)
            subcategory_items.append(data['total_items'])
            subcategory_sales.append(data['total_sales'])
        
        # График количества товаров по подкатегориям
        fig_items = px.bar(
            x=subcategory_items[:20],  # Топ-20
            y=subcategory_names[:20],
            orientation='h',
            title='Топ-20 подкатегорий по количеству товаров',
            labels={'x': 'Количество товаров', 'y': 'Подкатегория'},
            color=subcategory_items[:20],
            color_continuous_scale='Blues'
        )
        fig_items.update_layout(height=600)
        visualizations['subcategory_items'] = fig_items
        
        # График продаж по подкатегориям
        sales_sorted = sorted(zip(subcategory_names, subcategory_sales), key=lambda x: x[1], reverse=True)
        top_sales_names, top_sales_values = zip(*sales_sorted[:20])
        
        fig_sales = px.bar(
            x=list(top_sales_values),
            y=list(top_sales_names),
            orientation='h',
            title='Топ-20 подкатегорий по объему продаж',
            labels={'x': 'Объем продаж', 'y': 'Подкатегория'},
            color=list(top_sales_values),
            color_continuous_scale='Reds'
        )
        fig_sales.update_layout(height=600)
        visualizations['subcategory_sales'] = fig_sales
        
        # 2. ABC распределение по подкатегориям
        abc_summary = {'A': 0, 'B': 0, 'C': 0}
        for data in self.subcategory_results.values():
            for abc_class, count in data['abc_distribution'].items():
                abc_summary[abc_class] += count
        
        fig_abc_pie = px.pie(
            values=list(abc_summary.values()),
            names=list(abc_summary.keys()),
            title='ABC распределение товаров по подкатегориям',
            color_discrete_map={'A': '#ff4444', 'B': '#ffaa00', 'C': '#00aa44'}
        )
        visualizations['abc_distribution'] = fig_abc_pie
        
        # 3. Парето-анализ подкатегорий
        subcategory_sales_sorted = sorted(
            [(name, data['total_sales']) for name, data in self.subcategory_results.items()],
            key=lambda x: x[1], reverse=True
        )
        
        if subcategory_sales_sorted:
            names, sales = zip(*subcategory_sales_sorted[:30])  # Топ-30
            total_sales = sum(sales)
            
            cumulative_percentage = []
            cumsum = 0
            for sale in sales:
                cumsum += sale
                cumulative_percentage.append((cumsum / total_sales) * 100)
            
            fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Столбцы продаж
            fig_pareto.add_trace(
                go.Bar(x=list(range(len(names))), y=sales, name='Продажи'),
                secondary_y=False,
            )
            
            # Линия накопительного процента
            fig_pareto.add_trace(
                go.Scatter(x=list(range(len(names))), y=cumulative_percentage, 
                          mode='lines+markers', name='Накопительный %', line=dict(color='red')),
                secondary_y=True,
            )
            
            fig_pareto.update_xaxes(title_text="Подкатегории")
            fig_pareto.update_yaxes(title_text="Объем продаж", secondary_y=False)
            fig_pareto.update_yaxes(title_text="Накопительный процент (%)", secondary_y=True, range=[0, 100])
            fig_pareto.update_layout(title_text="Парето-анализ подкатегорий", height=500)
            
            visualizations['pareto'] = fig_pareto
        
        return visualizations
    
    def get_subcategory_recommendations(self) -> List[str]:
        """Получение рекомендаций по управлению подкатегориями"""
        if not self.subcategory_results:
            return ["Выполните анализ подкатегорий для получения рекомендаций"]
        
        recommendations = []
        
        # Анализ количества подкатегорий
        total_subcategories = len(self.subcategory_results)
        categories_count = len(set(data['category'] for data in self.subcategory_results.values()))
        avg_subcategories_per_category = total_subcategories / categories_count if categories_count > 0 else 0
        
        if avg_subcategories_per_category > 10:
            recommendations.append(
                f"Высокая детализация: {avg_subcategories_per_category:.1f} подкатегорий на категорию. "
                "Рассмотрите возможность консолидации мелких подкатегорий."
            )
        
        # Анализ подкатегорий без продаж
        zero_sales_subcategories = sum(
            1 for data in self.subcategory_results.values() 
            if data['total_sales'] == 0
        )
        
        if zero_sales_subcategories > 0:
            zero_percentage = (zero_sales_subcategories / total_subcategories) * 100
            recommendations.append(
                f"Найдено {zero_sales_subcategories} подкатегорий без продаж ({zero_percentage:.1f}%). "
                "Проанализируйте их актуальность в ассортименте."
            )
        
        # Анализ концентрации продаж
        sales_by_subcategory = [data['total_sales'] for data in self.subcategory_results.values()]
        total_sales = sum(sales_by_subcategory)
        
        if total_sales > 0:
            sales_sorted = sorted(sales_by_subcategory, reverse=True)
            top_20_percent_count = max(1, int(total_subcategories * 0.2))
            top_20_percent_sales = sum(sales_sorted[:top_20_percent_count])
            concentration_percentage = (top_20_percent_sales / total_sales) * 100
            
            if concentration_percentage > 80:
                recommendations.append(
                    f"Высокая концентрация продаж: топ 20% подкатегорий дают {concentration_percentage:.1f}% продаж. "
                    "Сосредоточьте внимание на ключевых подкатегориях."
                )
        
        # Анализ A товаров по подкатегориям
        subcategories_with_a_items = sum(
            1 for data in self.subcategory_results.values() 
            if data['abc_distribution']['A'] > 0
        )
        
        if subcategories_with_a_items / total_subcategories < 0.3:
            recommendations.append(
                f"Только {subcategories_with_a_items} из {total_subcategories} подкатегорий содержат A товары. "
                "Пересмотрите ассортиментную стратегию."
            )
        
        # Анализ размера подкатегорий
        small_subcategories = sum(
            1 for data in self.subcategory_results.values() 
            if data['total_items'] < 5
        )
        
        if small_subcategories > total_subcategories * 0.3:
            recommendations.append(
                f"Много мелких подкатегорий ({small_subcategories} с менее чем 5 товарами). "
                "Рассмотрите возможность объединения или переклассификации."
            )
        
        if not recommendations:
            recommendations.append("Структура подкатегорий выглядит сбалансированной. Продолжайте мониторинг.")
        
        return recommendations
    
    def export_subcategory_analysis(self) -> pd.DataFrame:
        """Экспорт результатов анализа подкатегорий в DataFrame"""
        if not self.subcategory_results:
            return pd.DataFrame()
        
        export_data = []
        
        print("🔍 ОТЛАДКА: Начинаем экспорт данных подкатегорий...")
        
        for subcategory, data in self.subcategory_results.items():
            # ИСПРАВЛЕННЫЙ расчет доли A товаров с отладкой
            total_items = data['total_items']
            a_items = data['abc_distribution']['A']
            
            # Правильный расчет процента A товаров (не может быть больше 100%)
            if total_items > 0:
                a_percentage = (a_items / total_items) * 100
            else:
                a_percentage = 0
            
            # ОТЛАДКА: выводим расчеты
            print(f"📊 {subcategory[:30]}: A={a_items}, Всего={total_items}, Доля={a_percentage:.1f}%")
            
            # Ограничиваем процент до 100% на всякий случай
            a_percentage = min(a_percentage, 100.0)
            
            export_data.append({
                'Подкатегория': subcategory,
                'Категория': data['category'],
                'Всего товаров': total_items,
                'Товаров с продажами': data['items_with_sales'],
                'Товаров без продаж': data['items_with_zero_sales'],
                'Общие продажи': data['total_sales'],
                'Средние продажи': data['average_sales'],
                'A товары': a_items,
                'B товары': data['abc_distribution']['B'],
                'C товары': data['abc_distribution']['C'],
                'Доля A товаров (%)': round(a_percentage, 1),  # ИСПРАВЛЕНО
                'Эффективность': 'Высокая' if a_percentage > 20.0
                                           else 'Средняя' if a_percentage > 5.0
                                           else 'Низкая'
            })
        
        df = pd.DataFrame(export_data)
        
        # Дополнительная проверка данных
        print(f"📊 ОТЛАДКА: Создан DataFrame с {len(df)} подкатегориями")
        print(f"📊 ОТЛАДКА: Диапазон долей A: {df['Доля A товаров (%)'].min():.1f}% - {df['Доля A товаров (%)'].max():.1f}%")
        
        # Проверяем на аномальные значения
        anomalies = df[df['Доля A товаров (%)'] > 100]
        if len(anomalies) > 0:
            print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Найдены аномальные доли A товаров:")
            for _, row in anomalies.iterrows():
                print(f"   {row['Подкатегория']}: {row['Доля A товаров (%)']}%")
        
        # Сортируем по общим продажам
        df = df.sort_values('Общие продажи', ascending=False)
        
        return df
    
    def get_subcategory_pareto_analysis(self) -> Dict:
        """Парето-анализ подкатегорий"""
        if not self.subcategory_results:
            return {}
        
        # Сортируем подкатегории по продажам
        subcategory_sales = [
            (name, data['total_sales']) 
            for name, data in self.subcategory_results.items()
        ]
        subcategory_sales.sort(key=lambda x: x[1], reverse=True)
        
        total_sales = sum(sales for _, sales in subcategory_sales)
        
        if total_sales == 0:
            return {'pareto_80': [], 'pareto_95': [], 'pareto_100': []}
        
        cumulative_sales = 0
        pareto_80 = []
        pareto_95 = []
        pareto_100 = []
        
        for name, sales in subcategory_sales:
            cumulative_sales += sales
            cumulative_percentage = (cumulative_sales / total_sales) * 100
            
            subcategory_info = {
                'name': name,
                'sales': sales,
                'cumulative_percentage': cumulative_percentage,
                'category': self.subcategory_results[name]['category'],
                'items_count': self.subcategory_results[name]['total_items']
            }
            
            if cumulative_percentage <= 80:
                pareto_80.append(subcategory_info)
            elif cumulative_percentage <= 95:
                pareto_95.append(subcategory_info)
            else:
                pareto_100.append(subcategory_info)
        
        self.pareto_analysis = {
            'pareto_80': pareto_80,
            'pareto_95': pareto_95, 
            'pareto_100': pareto_100,
            'total_subcategories': len(subcategory_sales),
            'total_sales': total_sales
        }
        
        return self.pareto_analysis

def create_subcategory_abc_interface(abc_data: pd.DataFrame = None):
    """
    Создание интерфейса для ABC анализа по подкатегориям в Streamlit
    ИСПРАВЛЕННАЯ ВЕРСИЯ без SelectColumn
    """
    st.header("🔤📊 ABC анализ по подкатегориям")
    
    st.markdown("""
    **Расширенный ABC анализ** с детализацией до подкатегорий позволяет:
    - 🎯 Более точно управлять ассортиментом на уровне подгрупп
    - 📈 Выявлять эффективные и неэффективные подкатегории
    - 🔍 Анализировать концентрацию продаж внутри категорий
    - 💡 Получать рекомендации по оптимизации структуры товаров
    
    **📋 Структура данных:** подкатегории во 2-м столбце, категории в 3-м столбце
    """)
    
    # Инициализация анализатора
    if 'subcategory_analyzer' not in st.session_state:
        st.session_state.subcategory_analyzer = SubcategoryABCAnalyzer()
    
    analyzer = st.session_state.subcategory_analyzer
    
    # Загрузка данных
    if abc_data is not None and not abc_data.empty:
        if analyzer.abc_data is None:
            with st.spinner("Загрузка данных для анализа подкатегорий..."):
                load_result = analyzer.load_data_with_subcategories(abc_data)
                
                if load_result['success']:
                    st.success("✅ Данные загружены для анализа подкатегорий!")
                    
                    # Показываем статистику загруженных данных
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Товаров", load_result['total_items'])
                    with col2:
                        st.metric("Категорий", load_result['categories_count'])
                    with col3:
                        st.metric("Подкатегорий", load_result['subcategories_count'])
                    with col4:
                        st.metric("Подкат./Категория", load_result['subcategories_per_category'])
                    
                    # Дополнительная информация
                    st.info(f"""
                    📊 **Структура данных:**
                    - С продажами: {load_result['items_with_sales']} товаров
                    - Без продаж: {load_result['items_with_zero_sales']} товаров
                    - Общие продажи: {load_result['total_sales']:,.0f}
                    - Средние продажи на товар: {load_result['average_sales']:,.0f}
                    """)
                    
                    
                    
                else:
                    st.error(f"❌ {load_result['error']}")
                    return
    else:
        st.info("Загрузите данные ABC анализа для начала работы с подкатегориями")
        return
    
    # Выполнение анализа
    if analyzer.abc_data is not None and analyzer.subcategory_results is None:
        if st.button("🔤 Выполнить ABC анализ по подкатегориям"):
            with st.spinner("Выполнение ABC анализа по подкатегориям..."):
                analysis_result = analyzer.perform_subcategory_abc_analysis()
                
                if analysis_result['success']:
                    st.success("✅ ABC анализ по подкатегориям завершен!")
                    st.rerun()
                else:
                    st.error(f"❌ {analysis_result['error']}")
    
    # Отображение результатов анализа
    if analyzer.subcategory_results:
        st.subheader("📊 Результаты ABC анализа по подкатегориям")
        
        # Общая статистика
        total_subcategories = len(analyzer.subcategory_results)
        total_items = sum(data['total_items'] for data in analyzer.subcategory_results.values())
        total_sales = sum(data['total_sales'] for data in analyzer.subcategory_results.values())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Подкатегорий", total_subcategories)
        with col2:
            st.metric("Товаров", total_items)
        with col3:
            st.metric("Общие продажи", f"{total_sales:,.0f}")
        with col4:
            avg_items = total_items / total_subcategories if total_subcategories > 0 else 0
            st.metric("Товаров/Подкатегория", f"{avg_items:.1f}")
        
        # Табы для разных видов анализа
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Сводная таблица",
            "📊 Визуализации", 
            "🎯 Парето-анализ",
            "🏷️ По категориям",
            "💡 Рекомендации"
        ])
        
        with tab1:
            st.subheader("📋 Детальная таблица по подкатегориям")
            
            # Экспортируем данные в таблицу
            export_df = analyzer.export_subcategory_analysis()
            
            # ДОБАВЛЯЕМ ДИАГНОСТИКУ
            with st.expander("🔍 Диагностика расчетов (для отладки)"):
                st.write("**Проверка расчетов доли A товаров:**")
                
                if not export_df.empty:
                    # Показываем первые 5 записей с детальными расчетами
                    for i, (_, row) in enumerate(export_df.head().iterrows()):
                        st.write(f"**{i+1}. {row['Подкатегория']}:**")
                        st.write(f"   - A товары: {row['A товары']}")
                        st.write(f"   - Всего товаров: {row['Всего товаров']}")
                        calculated_percentage = (row['A товары'] / row['Всего товаров'] * 100) if row['Всего товаров'] > 0 else 0
                        st.write(f"   - Расчет: {row['A товары']} ÷ {row['Всего товаров']} × 100 = {calculated_percentage:.1f}%")
                        st.write(f"   - Результат в таблице: {row['Доля A товаров (%)']}%")
                        st.write("---")
                
                # Проверяем исходные данные ABC анализа
                if hasattr(analyzer, 'subcategory_results') and analyzer.subcategory_results:
                    st.write("**Проверка исходных ABC результатов:**")
                    
                    # Берем первую подкатегорию для детального анализа
                    first_subcategory = list(analyzer.subcategory_results.keys())[0]
                    first_data = analyzer.subcategory_results[first_subcategory]
                    
                    st.write(f"**Подкатегория '{first_subcategory}':**")
                    st.write(f"- Всего товаров: {first_data['total_items']}")
                    st.write(f"- ABC распределение: {first_data['abc_distribution']}")
                    
                    if 'abc_data' in first_data:
                        abc_check = first_data['abc_data']['abc_class'].value_counts()
                        st.write(f"- Проверка через value_counts: {abc_check.to_dict()}")
            
            if not export_df.empty:
                # ИСПРАВЛЕННЫЕ ФИЛЬТРЫ: по подкатегориям вместо категорий
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # ИЗМЕНЕНО: Фильтр по подкатегориям
                    subcategory_filter = st.selectbox(
                        "Фильтр по подкатегории:",
                        options=['Все подкатегории'] + sorted(export_df['Подкатегория'].unique().tolist())
                    )
                
                with col2:
                    efficiency_filter = st.selectbox(
                        "Фильтр по эффективности:",
                        options=['Все', 'Высокая', 'Средняя', 'Низкая']
                    )
                
                with col3:
                    min_items = st.number_input(
                        "Минимум товаров:",
                        min_value=0,
                        value=0,
                        help="Показать подкатегории с количеством товаров больше указанного"
                    )
                
                # Применяем фильтры
                filtered_df = export_df.copy()
                
                # ИЗМЕНЕНО: Фильтрация по подкатегориям
                if subcategory_filter != 'Все подкатегории':
                    filtered_df = filtered_df[filtered_df['Подкатегория'] == subcategory_filter]
                
                if efficiency_filter != 'Все':
                    filtered_df = filtered_df[filtered_df['Эффективность'] == efficiency_filter]
                
                if min_items > 0:
                    filtered_df = filtered_df[filtered_df['Всего товаров'] >= min_items]
                
                # Отображаем таблицу с ИСПРАВЛЕННОЙ конфигурацией колонок
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    column_config={
                        'Общие продажи': st.column_config.NumberColumn(
                            "Общие продажи",
                            format="%.0f"
                        ),
                        'Средние продажи': st.column_config.NumberColumn(
                            "Средние продажи", 
                            format="%.0f"
                        ),
                        'Доля A товаров (%)': st.column_config.NumberColumn(
                            "Доля A товаров (%)",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100
                        )
                        # УБРАЛИ ProgressColumn - он некорректно отображает проценты
                    }
                )
                
                if len(filtered_df) != len(export_df):
                    st.info(f"Показано {len(filtered_df)} из {len(export_df)} подкатегорий")
                
                # Показываем статистику по отфильтрованным данным
                if len(filtered_df) > 0:
                    st.markdown("### 📊 Статистика по отфильтрованным данным:")
                    
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    
                    with stat_col1:
                        total_items_filtered = filtered_df['Всего товаров'].sum()
                        st.metric("Всего товаров", total_items_filtered)
                    
                    with stat_col2:
                        total_a_items = filtered_df['A товары'].sum()
                        st.metric("A товары", total_a_items)
                    
                    with stat_col3:
                        avg_a_percentage = filtered_df['Доля A товаров (%)'].mean()
                        st.metric("Средняя доля A (%)", f"{avg_a_percentage:.1f}%")
                    
                    with stat_col4:
                        total_sales = filtered_df['Общие продажи'].sum()
                        st.metric("Общие продажи", f"{total_sales:,.0f}")
                
                # Кнопка экспорта
                st.download_button(
                    label="📥 Скачать отфильтрованную таблицу CSV",
                    data=filtered_df.to_csv(index=False, encoding='utf-8-sig'),
                    file_name=f"subcategory_abc_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with tab2:
            st.subheader("📊 Визуализации анализа подкатегорий")
            
            # Создаем визуализации
            visualizations = analyzer.create_subcategory_visualizations()
            
            if visualizations:
                # График товаров по подкатегориям
                if 'subcategory_items' in visualizations:
                    st.plotly_chart(
                        visualizations['subcategory_items'], 
                        use_container_width=True,
                        key="subcategory_items_chart"
                    )
                
                # График продаж по подкатегориям
                if 'subcategory_sales' in visualizations:
                    st.plotly_chart(
                        visualizations['subcategory_sales'], 
                        use_container_width=True,
                        key="subcategory_sales_chart"
                    )
                
                # ABC распределение
                if 'abc_distribution' in visualizations:
                    st.plotly_chart(
                        visualizations['abc_distribution'], 
                        use_container_width=True,
                        key="subcategory_abc_distribution_chart"
                    )
                
                # Парето-анализ
                if 'pareto' in visualizations:
                    st.plotly_chart(
                        visualizations['pareto'], 
                        use_container_width=True,
                        key="subcategory_pareto_chart"
                    )
            else:
                st.warning("Не удалось создать визуализации")
        
        with tab3:
            st.subheader("🎯 Парето-анализ подкатегорий")
            
            # Выполняем парето-анализ
            pareto_data = analyzer.get_subcategory_pareto_analysis()
            
            if pareto_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Парето 80% (A)",
                        f"{len(pareto_data['pareto_80'])} подкат.",
                        help="Подкатегории, дающие 80% продаж"
                    )
                
                with col2:
                    st.metric(
                        "Парето 80-95% (B)", 
                        f"{len(pareto_data['pareto_95'])} подкат.",
                        help="Подкатегории, дающие 15% продаж"
                    )
                
                with col3:
                    st.metric(
                        "Парето 95-100% (C)",
                        f"{len(pareto_data['pareto_100'])} подкат.",
                        help="Подкатегории, дающие 5% продаж"
                    )
                
                # Детализация по группам Парето
                pareto_tab1, pareto_tab2, pareto_tab3 = st.tabs(["🔴 A подкатегории", "🟡 B подкатегории", "🟢 C подкатегории"])
                
                with pareto_tab1:
                    if pareto_data['pareto_80']:
                        st.write("**Ключевые подкатегории (80% продаж):**")
                        a_df = pd.DataFrame(pareto_data['pareto_80'])
                        a_df.columns = ['Подкатегория', 'Продажи', 'Накопительный %', 'Категория', 'Товаров']
                        st.dataframe(a_df, use_container_width=True)
                    else:
                        st.info("Нет подкатегорий в группе A")
                
                with pareto_tab2:
                    if pareto_data['pareto_95']:
                        st.write("**Важные подкатегории (15% продаж):**")
                        b_df = pd.DataFrame(pareto_data['pareto_95'])
                        b_df.columns = ['Подкатегория', 'Продажи', 'Накопительный %', 'Категория', 'Товаров']
                        st.dataframe(b_df, use_container_width=True)
                    else:
                        st.info("Нет подкатегорий в группе B")
                
                with pareto_tab3:
                    if pareto_data['pareto_100']:
                        st.write("**Второстепенные подкатегории (5% продаж):**")
                        c_df = pd.DataFrame(pareto_data['pareto_100'])
                        c_df.columns = ['Подкатегория', 'Продажи', 'Накопительный %', 'Категория', 'Товаров']
                        st.dataframe(c_df, use_container_width=True)
                    else:
                        st.info("Нет подкатегорий в группе C")
        
        with tab4:
            st.subheader("🏷️ Анализ по категориям")
            
            # Группируем по категориям
            category_analysis = analyzer.get_subcategory_analysis_by_category()
            
            if category_analysis:
                # Выбор категории для детального анализа
                selected_category = st.selectbox(
                    "Выберите категорию для детального анализа:",
                    options=list(category_analysis.keys())
                )
                
                if selected_category:
                    category_data = category_analysis[selected_category]
                    
                    # Статистика по выбранной категории
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Подкатегорий", category_data['subcategories_count'])
                    with col2:
                        st.metric("Товаров", category_data['total_items'])
                    with col3:
                        st.metric("Продажи", f"{category_data['total_sales']:,.0f}")
                    with col4:
                        avg_per_subcat = category_data['total_items'] / category_data['subcategories_count']
                        st.metric("Товаров/Подкат.", f"{avg_per_subcat:.1f}")
                    
                    # ABC распределение по категории
                    st.write(f"**ABC распределение в категории '{selected_category}':**")
                    abc_total = category_data['abc_distribution_total']
                    
                    abc_col1, abc_col2, abc_col3 = st.columns(3)
                    with abc_col1:
                        st.metric("A товары", abc_total['A'])
                    with abc_col2:
                        st.metric("B товары", abc_total['B'])
                    with abc_col3:
                        st.metric("C товары", abc_total['C'])
                    
                    # Таблица подкатегорий в выбранной категории
                    st.write("**Подкатегории в выбранной категории:**")
                    
                    subcategory_table_data = []
                    for subcat in category_data['subcategories']:
                        subcategory_table_data.append({
                            'Подкатегория': subcat['name'],
                            'Товаров': subcat['items'],
                            'С продажами': subcat['items_with_sales'],
                            'Продажи': subcat['sales'],
                            'A товары': subcat['abc_distribution']['A'],
                            'B товары': subcat['abc_distribution']['B'],
                            'C товары': subcat['abc_distribution']['C']
                        })
                    
                    subcat_df = pd.DataFrame(subcategory_table_data)
                    subcat_df = subcat_df.sort_values('Продажи', ascending=False)
                    st.dataframe(subcat_df, use_container_width=True)
                    
                    # График подкатегорий в выбранной категории
                    if len(subcat_df) > 1:
                        fig_category = px.bar(
                            subcat_df,
                            x='Подкатегория',
                            y='Продажи',
                            title=f'Продажи по подкатегориям в категории "{selected_category}"',
                            color='Продажи',
                            color_continuous_scale='Blues'
                        )
                        fig_category.update_xaxes(tickangle=45)
                        st.plotly_chart(
                            fig_category, 
                            use_container_width=True,
                            key=f"category_chart_{selected_category.replace(' ', '_')}"
                        )
        
        with tab5:
            st.subheader("💡 Рекомендации по управлению подкатегориями")
            
            # Получаем рекомендации
            recommendations = analyzer.get_subcategory_recommendations()
            
            if recommendations:
                for i, recommendation in enumerate(recommendations, 1):
                    st.info(f"**{i}.** {recommendation}")
            
            # Дополнительная аналитика
            st.subheader("📈 Дополнительная аналитика")
            
            # Анализ эффективности подкатегорий
            efficiency_analysis = {}
            for name, data in analyzer.subcategory_results.items():
                if data['total_items'] > 0:
                    a_percentage = (data['abc_distribution']['A'] / data['total_items']) * 100
                    efficiency_analysis[name] = {
                        'category': data['category'],
                        'a_percentage': a_percentage,
                        'sales_per_item': data['total_sales'] / data['total_items'],
                        'total_items': data['total_items']
                    }
            
            if efficiency_analysis:
                # Топ и низ по эффективности
                sorted_by_efficiency = sorted(
                    efficiency_analysis.items(),
                    key=lambda x: x[1]['a_percentage'],
                    reverse=True
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**🏆 Топ-5 самых эффективных подкатегорий:**")
                    for i, (name, data) in enumerate(sorted_by_efficiency[:5], 1):
                        st.write(f"{i}. **{name}** ({data['category']})")
                        st.write(f"   A товары: {data['a_percentage']:.1f}%, Продажи на товар: {data['sales_per_item']:,.0f}")
                
                with col2:
                    st.write("**📉 Топ-5 наименее эффективных подкатегорий:**")
                    for i, (name, data) in enumerate(sorted_by_efficiency[-5:], 1):
                        st.write(f"{i}. **{name}** ({data['category']})")
                        st.write(f"   A товары: {data['a_percentage']:.1f}%, Продажи на товар: {data['sales_per_item']:,.0f}")
                
                # График эффективности vs размера
                if len(sorted_by_efficiency) > 10:
                    efficiency_df = pd.DataFrame([
                        {
                            'Подкатегория': name[:20],
                            'Доля A товаров (%)': data['a_percentage'],
                            'Продажи на товар': data['sales_per_item'],
                            'Количество товаров': data['total_items']
                        }
                        for name, data in sorted_by_efficiency
                    ])
                    
                    fig_efficiency = px.scatter(
                        efficiency_df,
                        x='Количество товаров',
                        y='Доля A товаров (%)',
                        size='Продажи на товар',
                        hover_name='Подкатегория',
                        title='Эффективность подкатегорий: Размер vs Доля A товаров',
                        labels={
                            'Количество товаров': 'Размер подкатегории (товаров)',
                            'Доля A товаров (%)': 'Эффективность (% A товаров)'
                        }
                    )
                    st.plotly_chart(
                        fig_efficiency, 
                        use_container_width=True,
                        key="efficiency_scatter_chart"
                    )
        
        # Экспорт всех результатов
        st.subheader("📤 Экспорт результатов")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Создать полный отчет Excel"):
                with st.spinner("Создание Excel отчета..."):
                    excel_buffer = create_subcategory_excel_report(analyzer)
                    
                    if excel_buffer:
                        st.download_button(
                            label="💾 Скачать полный отчет Excel",
                            data=excel_buffer,
                            file_name=f"subcategory_abc_full_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        
        with col2:
            if st.button("🔄 Очистить результаты"):
                analyzer.subcategory_results = None
                analyzer.abc_data = None
                analyzer.pareto_analysis = None
                st.success("✅ Результаты очищены!")
                st.rerun()

def create_subcategory_excel_report(analyzer: SubcategoryABCAnalyzer) -> bytes:
    """Создание полного Excel отчета по анализу подкатегорий"""
    try:
        import io
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Сводная таблица
            summary_df = analyzer.export_subcategory_analysis()
            summary_df.to_excel(writer, sheet_name='Сводка_подкатегорий', index=False)
            
            # 2. Анализ по категориям
            category_analysis = analyzer.get_subcategory_analysis_by_category()
            if category_analysis:
                category_summary = []
                for category, data in category_analysis.items():
                    category_summary.append({
                        'Категория': category,
                        'Подкатегорий': data['subcategories_count'],
                        'Товаров': data['total_items'],
                        'Продажи': data['total_sales'],
                        'A товары': data['abc_distribution_total']['A'],
                        'B товары': data['abc_distribution_total']['B'],
                        'C товары': data['abc_distribution_total']['C']
                    })
                
                category_df = pd.DataFrame(category_summary)
                category_df.to_excel(writer, sheet_name='Анализ_категорий', index=False)
            
            # 3. Парето-анализ
            pareto_data = analyzer.get_subcategory_pareto_analysis()
            if pareto_data:
                # A подкатегории
                if pareto_data['pareto_80']:
                    a_df = pd.DataFrame(pareto_data['pareto_80'])
                    a_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_процент', 'Категория', 'Товаров']
                    a_df.to_excel(writer, sheet_name='A_подкатегории_80%', index=False)
                
                # B подкатегории
                if pareto_data['pareto_95']:
                    b_df = pd.DataFrame(pareto_data['pareto_95'])
                    b_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_процент', 'Категория', 'Товаров']
                    b_df.to_excel(writer, sheet_name='B_подкатегории_15%', index=False)
                
                # C подкатегории
                if pareto_data['pareto_100']:
                    c_df = pd.DataFrame(pareto_data['pareto_100'])
                    c_df.columns = ['Подкатегория', 'Продажи', 'Накопительный_процент', 'Категория', 'Товаров']
                    c_df.to_excel(writer, sheet_name='C_подкатегории_5%', index=False)
            
            # 4. Детальные данные по товарам в подкатегориях
            if analyzer.subcategory_results:
                all_items_data = []
                for subcategory, data in analyzer.subcategory_results.items():
                    if 'abc_data' in data:
                        subcategory_items = data['abc_data'].copy()
                        subcategory_items['subcategory_name'] = subcategory
                        all_items_data.append(subcategory_items)
                
                if all_items_data:
                    all_items_df = pd.concat(all_items_data, ignore_index=True)
                    cols_to_export = ['nomenclature', 'category', 'subcategory_name', 'annual_sales', 'abc_class']
                    existing_cols = [col for col in cols_to_export if col in all_items_df.columns]
                    
                    all_items_df[existing_cols].to_excel(writer, sheet_name='Детали_товаров', index=False)
            
            # 5. Рекомендации
            recommendations = analyzer.get_subcategory_recommendations()
            if recommendations:
                rec_df = pd.DataFrame({
                    'Номер': range(1, len(recommendations) + 1),
                    'Рекомендация': recommendations
                })
                rec_df.to_excel(writer, sheet_name='Рекомендации', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        st.error(f"Ошибка создания Excel отчета: {str(e)}")
        return None

# Функция для интеграции с существующей системой
def integrate_subcategory_abc_to_existing_system():
    """
    Функция для интеграции анализа подкатегорий в существующую систему
    Добавляет новую вкладку в основное приложение
    """
    
    # Проверяем наличие данных ABC в сессии
    abc_data = None
    
    # Попытка получить данные из разных возможных источников
    if 'inventory_system' in st.session_state:
        system = st.session_state.inventory_system
        
        # Проверяем разные возможные источники ABC данных
        if hasattr(system, 'abc_results') and system.abc_results:
            if 'abc_data_detailed' in system.abc_results:
                abc_data = system.abc_results['abc_data_detailed']
        
        elif hasattr(system, 'processor') and hasattr(system.processor, 'processed_data'):
            if 'abc_analysis' in system.processor.processed_data:
                abc_data = system.processor.processed_data['abc_analysis']
        
        elif hasattr(system, 'abc_data') and system.abc_data is not None:
            abc_data = system.abc_data
    
    # Проверяем другие возможные источники в session_state
    if abc_data is None:
        for key in st.session_state:
            if 'abc' in key.lower() and isinstance(st.session_state[key], pd.DataFrame):
                abc_data = st.session_state[key]
                break
    
    # Создаем интерфейс
    if abc_data is not None and not abc_data.empty:
        create_subcategory_abc_interface(abc_data)
    else:
        st.warning("""
        ⚠️ **Данные ABC анализа не найдены**
        
        Для использования анализа подкатегорий необходимо:
        1. Загрузить данные ABC анализа в основной системе
        2. Выполнить ABC анализ
        3. Перейти на эту вкладку
        
        **ВАЖНО:** Убедитесь что у вас есть данные со структурой:
        - **1-я колонка:** `nomenclature` (название товара)
        - **2-я колонка:** `subcategory` (подкатегория) 🔸
        - **3-я колонка:** `category` (категория) 🔸
        - **4-я колонка:** `annual_sales` (годовые продажи)
        
        **🔸 ИСПРАВЛЕНО:** Подкатегории во 2-м столбце, категории в 3-м
        """)
        
        # Кнопка для перехода к основному ABC анализу
        if st.button("🔤 Перейти к основному ABC анализу"):
            st.info("Переключитесь на вкладку 'ABC анализ' для загрузки данных")

# Основная функция для использования как отдельной страницы
def main():
    """Основная функция для запуска как отдельной страницы"""
    st.set_page_config(
        page_title="ABC анализ по подкатегориям",
        page_icon="🔤📊",
        layout="wide"
    )
    
    st.title("🔤📊 ABC анализ по подкатегориям")
    st.markdown("*Расширенный ABC анализ с детализацией до подкатегорий товаров*")
    st.markdown("**🔸 ИСПРАВЛЕННАЯ ВЕРСИЯ:** подкатегории во 2-м столбце, категории в 3-м")
    
    # Пытаемся интегрироваться с существующей системой
    integrate_subcategory_abc_to_existing_system()

if __name__ == "__main__":
    main()