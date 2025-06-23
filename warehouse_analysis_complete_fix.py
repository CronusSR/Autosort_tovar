#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ===== КОНСТАНТЫ И КОНФИГУРАЦИЯ =====

# Конфигурация складов с персональными настройками
WAREHOUSE_CONFIG = {
    'shymkent_warehouse': {
        'name': 'Шымкент_Склад',
        'short_name': 'Шымкент Склад',
        'city': 'Шымкент',
        'type': 'Склад',
        'column_indicators': ['шымкент', 'склад', 'shymkent'],
        'min_days': 15,
        'max_days': 45,
        'ads_multiplier': 1.0,
        'priority': 1
    },
    'shymkent_store': {
        'name': 'Шымкент_Магазин',
        'short_name': 'Шымкент Магазин',
        'city': 'Шымкент',
        'type': 'Магазин',
        'column_indicators': ['шымкент', 'магазин', 'shymkent', 'store'],
        'min_days': 10,
        'max_days': 30,
        'ads_multiplier': 0.8,
        'priority': 2
    },
    'almaty_warehouse': {
        'name': 'Алматы_Склад',
        'short_name': 'Алматы Склад',
        'city': 'Алматы',
        'type': 'Склад',
        'column_indicators': ['алматы', 'склад', 'almaty'],
        'min_days': 20,
        'max_days': 60,
        'ads_multiplier': 1.2,
        'priority': 1
    },
    'base_complex': {
        'name': 'База_Комплект',
        'short_name': 'База Комплект',
        'city': 'Алматы',
        'type': 'База',
        'column_indicators': ['база', 'комплект', 'base'],
        'min_days': 25,
        'max_days': 75,
        'ads_multiplier': 1.5,
        'priority': 1
    },
    'barys_warehouse': {
        'name': 'Барыс_Склад',
        'short_name': 'Барыс Склад',
        'city': 'Алматы',
        'type': 'Склад',
        'column_indicators': ['барыс', 'склад', 'barys'],
        'min_days': 15,
        'max_days': 40,
        'ads_multiplier': 1.0,
        'priority': 2
    },
    'kazybaeva_warehouse': {
        'name': 'Казыбаева_Склад',
        'short_name': 'Казыбаева Склад',
        'city': 'Алматы',
        'type': 'Склад',
        'column_indicators': ['казыбаева', 'склад', 'kazybaeva'],
        'min_days': 12,
        'max_days': 35,
        'ads_multiplier': 0.9,
        'priority': 2
    },
    'astana_store': {
        'name': 'Астана_Магазин',
        'short_name': 'Астана Магазин',
        'city': 'Астана',
        'type': 'Магазин',
        'column_indicators': ['астана', 'магазин', 'astana', 'store'],
        'min_days': 10,
        'max_days': 30,
        'ads_multiplier': 0.8,
        'priority': 2
    },
    'astana_warehouse': {
        'name': 'Астана_Склад',
        'short_name': 'Астана Склад',
        'city': 'Астана',
        'type': 'Склад',
        'column_indicators': ['астана', 'склад', 'astana'],
        'min_days': 15,
        'max_days': 45,
        'ads_multiplier': 1.0,
        'priority': 1
    },
    'kazybaeva_store': {
        'name': 'Казыбаева_Магазин',
        'short_name': 'Казыбаева Магазин',
        'city': 'Алматы',
        'type': 'Магазин',
        'column_indicators': ['казыбаева', 'магазин', 'kazybaeva', 'store'],
        'min_days': 8,
        'max_days': 25,
        'ads_multiplier': 0.7,
        'priority': 3
    }
}

# ===== КЛАССЫ ДЛЯ ИСПРАВЛЕНИЯ =====

class FixedWarehouseFileReader:
    """
    ИСПРАВЛЕННЫЙ класс для чтения файлов остатков складов
    Решает проблему с колонкой 'номенклатура'
    """
    
    def __init__(self):
        self.debug_mode = False
    
    def enable_debug(self):
        """Включить режим отладки"""
        self.debug_mode = True
    
    def read_warehouse_file(self, uploaded_file):
        """
        ИСПРАВЛЕННОЕ чтение файла остатков складов
        Автоматически определяет структуру и склады
        """
        
        try:
            if self.debug_mode:
                st.info("🔍 Начинаю анализ структуры файла...")
            
            # Читаем весь файл для анализа структуры
            df_full = pd.read_excel(uploaded_file, sheet_name=0, header=None)
            
            if self.debug_mode:
                st.write("📋 Первые 10 строк файла:")
                st.dataframe(df_full.head(10))
            
            # Ищем строку с заголовком "Номенклатура"
            nomenclature_row = self._find_nomenclature_row(df_full)
            
            if nomenclature_row is None:
                st.error("❌ Не найден заголовок 'Номенклатура' в файле")
                return None
            
            if self.debug_mode:
                st.success(f"✅ Заголовок найден в строке {nomenclature_row + 1}")
            
            # Читаем файл с правильным заголовком
            df = pd.read_excel(uploaded_file, sheet_name=0, header=nomenclature_row)
            
            # Очищаем данные
            df_cleaned = self._clean_dataframe(df)
            
            if self.debug_mode:
                st.write("🧹 Очищенные данные:")
                st.dataframe(df_cleaned.head())
            
            # Определяем склады
            warehouse_columns = self._identify_warehouse_columns(df_cleaned)
            
            if self.debug_mode:
                st.write("🏪 Найденные склады:")
                for col, info in warehouse_columns.items():
                    st.write(f"  - {col}: {info['warehouse_key']} ({info['config']['city']})")
            
            if not warehouse_columns:
                st.error("❌ Не найдены колонки складов в файле")
                return None
            
            # Формируем итоговый DataFrame
            result_df = self._create_result_dataframe(df_cleaned, warehouse_columns)
            
            if self.debug_mode:
                st.success(f"✅ Обработано {len(result_df)} товаров из {len(warehouse_columns)} складов")
            
            return result_df
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            if self.debug_mode:
                st.exception(e)
            return None
    
    def _find_nomenclature_row(self, df):
        """Находит строку с заголовком 'Номенклатура'"""
        
        for idx, row in df.iterrows():
            for col_idx, cell in enumerate(row):
                if pd.notna(cell) and isinstance(cell, str):
                    if 'номенклатура' in cell.lower():
                        return idx
        return None
    
    def _clean_dataframe(self, df):
        """Очищает DataFrame от пустых строк и столбцов"""
        
        # Удаляем полностью пустые строки
        df_cleaned = df.dropna(how='all')
        
        # Удаляем полностью пустые столбцы
        df_cleaned = df_cleaned.dropna(axis=1, how='all')
        
        # Сбрасываем индекс
        df_cleaned = df_cleaned.reset_index(drop=True)
        
        return df_cleaned
    
    def _identify_warehouse_columns(self, df):
        """Определяет колонки складов и их конфигурацию"""
        
        warehouse_columns = {}
        
        for col in df.columns:
            if pd.isna(col):
                continue
                
            col_lower = str(col).lower()
            
            # Ищем соответствие в конфигурации складов
            for warehouse_key, config in WAREHOUSE_CONFIG.items():
                for indicator in config['column_indicators']:
                    if indicator.lower() in col_lower:
                        warehouse_columns[col] = {
                            'warehouse_key': warehouse_key,
                            'config': config
                        }
                        break
                if col in warehouse_columns:
                    break
        
        return warehouse_columns
    
    def _create_result_dataframe(self, df, warehouse_columns):
        """Создает итоговый DataFrame с данными остатков"""
        
        # Находим колонку с номенклатурой
        nomenclature_col = None
        for col in df.columns:
            if pd.notna(col) and 'номенклатура' in str(col).lower():
                nomenclature_col = col
                break
        
        if nomenclature_col is None:
            # Берем первую колонку
            nomenclature_col = df.columns[0]
        
        # Создаем результирующий DataFrame
        result_data = []
        
        for idx, row in df.iterrows():
            item_name = row[nomenclature_col]
            
            # Пропускаем пустые наименования
            if pd.isna(item_name) or str(item_name).strip() == '':
                continue
            
            # Собираем данные по складам
            item_data = {'Наименование': str(item_name).strip()}
            
            for col, warehouse_info in warehouse_columns.items():
                warehouse_key = warehouse_info['warehouse_key']
                config = warehouse_info['config']
                
                # Получаем количество
                qty = row[col] if col in row.index else 0
                
                try:
                    qty = float(qty) if pd.notna(qty) else 0
                except:
                    qty = 0
                
                item_data[config['short_name']] = qty
            
            result_data.append(item_data)
        
        return pd.DataFrame(result_data)


class FixedWarehouseAnalyzer:
    """
    ИСПРАВЛЕННЫЙ анализатор складов с поддержкой цен и персональных настроек
    """
    
    def __init__(self):
        self.warehouse_config = WAREHOUSE_CONFIG
        self.analysis_results = None
        self.warehouse_recommendations = None
        self.has_prices = False
    
    def analyze_warehouse_stock_detailed(self, remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
        """
        ИСПРАВЛЕННЫЙ детальный анализ складов с ценами
        """
        
        try:
            st.info("🔍 Запускаю детальный анализ складов...")
            
            # Проверяем наличие цен в ADS
            self.has_prices = self._check_price_availability(ads_data)
            
            if self.has_prices:
                st.success("💰 Цены найдены в ADS данных - будет полный финансовый анализ")
            else:
                st.warning("⚠️ Цены не найдены - анализ без денежного выражения")
            
            # Объединяем данные остатков с ADS
            merged_data = self._merge_remains_with_ads(remains_df, ads_data)
            
            if merged_data is None or merged_data.empty:
                st.error("❌ Не удалось объединить данные остатков с ADS")
                return None
            
            st.info(f"📊 Объединено {len(merged_data)} товаров для анализа")
            
            # Анализируем каждый товар по каждому складу
            analysis_results = []
            
            # Определяем колонки складов
            warehouse_columns = [col for col in merged_data.columns 
                               if any(config['short_name'] == col for config in WAREHOUSE_CONFIG.values())]
            
            if not warehouse_columns:
                st.error("❌ Не найдены колонки складов в данных")
                return None
            
            st.info(f"🏪 Найдено складов для анализа: {len(warehouse_columns)}")
            
            # Прогресс бар для анализа
            progress_bar = st.progress(0)
            total_items = len(merged_data)
            
            for idx, row in merged_data.iterrows():
                item_name = row['Наименование']
                ads_value = row.get('ADS', 0)
                price = row.get('last_purchase_price', 0) if self.has_prices else 0
                
                # Анализ по каждому складу
                item_analysis = {
                    'item_name': item_name,
                    'ads': ads_value,
                    'price': price,
                    'warehouses': {},
                    'total_stock': 0,
                    'total_stock_value': 0,
                    'total_deficit_qty': 0,
                    'total_deficit_value': 0
                }
                
                for col in warehouse_columns:
                    # Находим конфигурацию склада
                    warehouse_key = None
                    for wh_key, config in WAREHOUSE_CONFIG.items():
                        if config['short_name'] == col:
                            warehouse_key = wh_key
                            break
                    
                    if warehouse_key is None:
                        continue
                    
                    config = WAREHOUSE_CONFIG[warehouse_key]
                    current_stock = row.get(col, 0)
                    
                    try:
                        current_stock = float(current_stock) if pd.notna(current_stock) else 0
                    except:
                        current_stock = 0
                    
                    # Рассчитываем потребности для этого склада
                    warehouse_ads = ads_value * config['ads_multiplier']
                    min_stock = warehouse_ads * config['min_days']
                    max_stock = warehouse_ads * config['max_days']
                    
                    # Анализируем статус
                    status = self._get_warehouse_status(current_stock, min_stock, max_stock)
                    
                    # Рассчитываем дефицит/излишек
                    deficit_qty = max(0, min_stock - current_stock)
                    surplus_qty = max(0, current_stock - max_stock)
                    
                    # Денежные расчеты
                    stock_value = current_stock * price if self.has_prices else 0
                    deficit_value = deficit_qty * price if self.has_prices else 0
                    
                    # Месяцы запаса
                    months_of_stock = (current_stock / warehouse_ads) if warehouse_ads > 0 else 999
                    
                    warehouse_analysis = {
                        'warehouse_key': warehouse_key,
                        'name': config['name'],
                        'short_name': config['short_name'],
                        'city': config['city'],
                        'type': config['type'],
                        'current_stock': current_stock,
                        'min_stock': min_stock,
                        'max_stock': max_stock,
                        'warehouse_ads': warehouse_ads,
                        'status': status,
                        'deficit_qty': deficit_qty,
                        'surplus_qty': surplus_qty,
                        'stock_value': stock_value,
                        'deficit_value': deficit_value,
                        'months_of_stock': months_of_stock,
                        'min_days': config['min_days'],
                        'max_days': config['max_days'],
                        'priority': config['priority']
                    }
                    
                    item_analysis['warehouses'][warehouse_key] = warehouse_analysis
                    item_analysis['total_stock'] += current_stock
                    item_analysis['total_stock_value'] += stock_value
                    item_analysis['total_deficit_qty'] += deficit_qty
                    item_analysis['total_deficit_value'] += deficit_value
                
                analysis_results.append(item_analysis)
                
                # Обновляем прогресс
                progress = (idx + 1) / total_items
                progress_bar.progress(progress)
            
            progress_bar.empty()
            
            self.analysis_results = analysis_results
            
            # Генерируем рекомендации по складам
            self._generate_warehouse_recommendations()
            
            st.success(f"✅ Детальный анализ завершен: {len(analysis_results)} товаров проанализированы")
            
            return analysis_results
            
        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")
            st.exception(e)
            return None
    
    def _check_price_availability(self, ads_data):
        """Проверяет наличие ценовых данных"""
        
        if ads_data is None or ads_data.empty:
            return False
        
        price_columns = ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']
        
        for col in price_columns:
            if col in ads_data.columns:
                # Проверяем есть ли реальные цены
                non_zero_prices = (ads_data[col] > 0).sum()
                if non_zero_prices > 0:
                    return True
        
        return False
    
    def _merge_remains_with_ads(self, remains_df, ads_data):
        """Объединяет данные остатков с ADS"""
        
        if remains_df is None or ads_data is None:
            return None
        
        # Стандартизируем названия колонок
        remains_df_copy = remains_df.copy()
        ads_data_copy = ads_data.copy()
        
        # Если есть цены, добавляем их
        if self.has_prices:
            price_column = None
            for col in ['last_purchase_price', 'цена', 'price', 'стоимость', 'закупочная_цена']:
                if col in ads_data_copy.columns:
                    price_column = col
                    break
            
            if price_column:
                ads_data_copy['last_purchase_price'] = ads_data_copy[price_column]
        
        # Объединяем данные
        merged = pd.merge(
            remains_df_copy,
            ads_data_copy[['Наименование', 'ADS'] + (['last_purchase_price'] if self.has_prices else [])],
            on='Наименование',
            how='inner'
        )
        
        return merged
    
    def _get_warehouse_status(self, current_stock, min_stock, max_stock):
        """Определяет статус склада"""
        
        if current_stock <= min_stock * 0.5:
            return 'Критично'
        elif current_stock <= min_stock:
            return 'Мало'
        elif current_stock <= max_stock:
            return 'Норма'
        else:
            return 'Избыток'
    
    def _generate_warehouse_recommendations(self):
        """Генерирует рекомендации по складам"""
        
        if not self.analysis_results:
            return
        
        self.warehouse_recommendations = {}
        
        # Группируем по складам
        for warehouse_key, config in WAREHOUSE_CONFIG.items():
            recommendations = {
                'warehouse_key': warehouse_key,
                'name': config['name'],
                'short_name': config['short_name'],
                'city': config['city'],
                'type': config['type'],
                'critical_items': [],
                'warning_items': [],
                'good_items': [],
                'excess_items': [],
                'total_order_value': 0,
                'total_stock_value': 0,
                'total_min_deficit': 0,
                'total_max_deficit': 0
            }
            
            for item in self.analysis_results:
                if warehouse_key not in item['warehouses']:
                    continue
                
                wh_data = item['warehouses'][warehouse_key]
                
                # Классифицируем товары
                if wh_data['status'] == 'Критично':
                    recommendations['critical_items'].append({
                        'name': item['item_name'],
                        'current_stock': wh_data['current_stock'],
                        'min_stock': wh_data['min_stock'],
                        'deficit': wh_data['deficit_qty'],
                        'deficit_value': wh_data['deficit_value'],
                        'months_stock': wh_data['months_of_stock']
                    })
                elif wh_data['status'] == 'Мало':
                    recommendations['warning_items'].append({
                        'name': item['item_name'],
                        'current_stock': wh_data['current_stock'],
                        'min_stock': wh_data['min_stock'],
                        'deficit': wh_data['deficit_qty'],
                        'deficit_value': wh_data['deficit_value'],
                        'months_stock': wh_data['months_of_stock']
                    })
                elif wh_data['status'] == 'Норма':
                    recommendations['good_items'].append({
                        'name': item['item_name'],
                        'current_stock': wh_data['current_stock'],
                        'months_stock': wh_data['months_of_stock']
                    })
                else:  # Избыток
                    recommendations['excess_items'].append({
                        'name': item['item_name'],
                        'current_stock': wh_data['current_stock'],
                        'max_stock': wh_data['max_stock'],
                        'surplus': wh_data['surplus_qty'],
                        'months_stock': wh_data['months_of_stock']
                    })
                
                # Суммируем финансовые показатели
                recommendations['total_order_value'] += wh_data['deficit_value']
                recommendations['total_stock_value'] += wh_data['stock_value']
                recommendations['total_min_deficit'] += wh_data['deficit_qty']
            
            self.warehouse_recommendations[warehouse_key] = recommendations
    
    def get_warehouse_recommendations(self):
        """Возвращает рекомендации по складам"""
        return self.warehouse_recommendations
    
    def get_analysis_results(self):
        """Возвращает результаты анализа"""
        return self.analysis_results


# ===== ФУНКЦИИ ИНТЕГРАЦИИ =====

def apply_warehouse_complete_fix(system):
    """
    Применяет полное исправление системы анализа складов
    """
    
    try:
        # Добавляем исправленный анализатор
        system.warehouse_analyzer = FixedWarehouseAnalyzer()
        
        # Добавляем исправленный ридер файлов
        system.warehouse_file_reader = FixedWarehouseFileReader()
        
        # Добавляем отсутствующие методы
        def analyze_warehouse_stock_with_details(remains_df, ads_data, store_ads_by_city=None, min_days=10, max_days=50):
            return system.warehouse_analyzer.analyze_warehouse_stock_detailed(
                remains_df, ads_data, store_ads_by_city, min_days, max_days
            )
        
        system.analyze_warehouse_stock_with_details = analyze_warehouse_stock_with_details
        
        # Отмечаем что исправления применены
        system._warehouse_fix_applied = True
        
        st.success("✅ Полные исправления анализа складов применены!")
        return True
        
    except Exception as e:
        st.error(f"❌ Ошибка применения исправлений: {str(e)}")
        return False


def create_fixed_warehouse_analysis_page():
    """
    Создает ИСПРАВЛЕННУЮ страницу анализа складов
    """
    
    def fixed_warehouse_analysis_page(system):
        """
        ИСПРАВЛЕННАЯ страница анализа складов с ценами и персональными настройками
        """
        
        st.header("📦 Анализ складов - ИСПРАВЛЕННАЯ ВЕРСИЯ")
        st.caption("✅ С поддержкой цен и персональными настройками складов")
        
        # Применяем исправления если еще не применены
        if not hasattr(system, '_warehouse_fix_applied'):
            apply_warehouse_complete_fix(system)
        
        # Проверяем ADS данные
        if not hasattr(system, 'calculated_ads') or system.calculated_ads is None:
            st.warning("⚠️ Для анализа сначала рассчитайте ADS в разделе 'ADS расчет'")
            return
        
        # Показываем информацию о складах
        with st.expander("🏪 Конфигурация складов"):
            st.markdown("### Персональные настройки складов:")
            
            config_data = []
            for warehouse_key, config in WAREHOUSE_CONFIG.items():
                config_data.append({
                    'Склад': config['name'],
                    'Город': config['city'],
                    'Тип': config['type'],
                    'Мин. дни': config['min_days'],
                    'Макс. дни': config['max_days'],
                    'ADS множитель': config['ads_multiplier'],
                    'Приоритет': config['priority']
                })
            
            config_df = pd.DataFrame(config_data)
            st.dataframe(config_df, use_container_width=True)
        
        # Загрузка файла остатков
        st.subheader("📁 Загрузка файла остатков")
        
        uploaded_file = st.file_uploader(
            "Выберите файл остатков складов",
            type=['xlsx', 'xls'],
            help="Файл должен содержать колонку 'Номенклатура' и колонки складов"
        )
        
        if uploaded_file is None:
            st.info("📤 Загрузите файл остатков для начала анализа")
            return
        
        # Настройки анализа
        st.subheader("⚙️ Параметры анализа")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            debug_mode = st.checkbox("🔍 Режим отладки", help="Показывает детали обработки файла")
        
        with col2:
            auto_analysis = st.checkbox("🚀 Автоматический анализ", value=True, help="Запустить анализ сразу после загрузки")
        
        with col3:
            show_details = st.checkbox("📊 Показать детали", value=True, help="Подробные результаты анализа")
        
        # Читаем файл остатков
        if debug_mode:
            system.warehouse_file_reader.enable_debug()
        
        with st.spinner("📖 Читаю файл остатков..."):
            remains_df = system.warehouse_file_reader.read_warehouse_file(uploaded_file)
        
        if remains_df is None:
            st.error("❌ Не удалось прочитать файл остатков")
            return
        
        st.success(f"✅ Файл загружен: {len(remains_df)} товаров")
        
        # Показываем превью данных
        with st.expander("👀 Превью данных остатков"):
            st.dataframe(remains_df.head(10))
        
        # Кнопка анализа или автоматический запуск
        run_analysis = auto_analysis
        
        if not auto_analysis:
            run_analysis = st.button("🔍 Запустить детальный анализ складов", type="primary")
        
        if run_analysis:
            st.markdown("---")
            st.subheader("📊 Результаты анализа")
            
            # Запускаем анализ
            with st.spinner("🔄 Выполняю детальный анализ складов..."):
                analysis_results = system.analyze_warehouse_stock_with_details(
                    remains_df, 
                    system.calculated_ads,
                    None,  # store_ads_by_city не используется в новой версии
                    10,    # min_days - будет переопределено для каждого склада
                    50     # max_days - будет переопределено для каждого склада
                )
            
            if analysis_results is None:
                st.error("❌ Анализ не выполнен")
                return
            
            # Получаем рекомендации
            recommendations = system.warehouse_analyzer.get_warehouse_recommendations()
            
            if recommendations is None:
                st.error("❌ Рекомендации не сгенерированы")
                return
            
            # Отображаем результаты
            display_warehouse_analysis_results(analysis_results, recommendations, system.warehouse_analyzer.has_prices, show_details)
            
            # Экспорт результатов
            st.markdown("---")
            st.subheader("📤 Экспорт результатов")
            
            if st.button("📊 Экспортировать детальный отчет", type="secondary"):
                export_warehouse_analysis_results(analysis_results, recommendations, system.warehouse_analyzer.has_prices)
    
    return fixed_warehouse_analysis_page


def display_warehouse_analysis_results(analysis_results, recommendations, has_prices, show_details=True):
    """
    Отображает результаты анализа складов
    """
    
    # Общая статистика
    st.markdown("### 📈 Общая статистика")
    
    total_items = len(analysis_results)
    total_warehouses = len(recommendations)
    
    # Считаем общие показатели
    total_critical = sum(len(rec['critical_items']) for rec in recommendations.values())
    total_warning = sum(len(rec['warning_items']) for rec in recommendations.values())
    total_good = sum(len(rec['good_items']) for rec in recommendations.values())
    total_excess = sum(len(rec['excess_items']) for rec in recommendations.values())
    
    total_order_value = sum(rec['total_order_value'] for rec in recommendations.values())
    total_stock_value = sum(rec['total_stock_value'] for rec in recommendations.values())
    
    # Отображаем метрики
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📦 Товаров", total_items)
    with col2:
        st.metric("🏪 Складов", total_warehouses)
    with col3:
        st.metric("🔴 Критичных позиций", total_critical)
    with col4:
        st.metric("🟡 Требуют внимания", total_warning)
    with col5:
        if has_prices:
            st.metric("💰 К заказу", f"{total_order_value:,.0f} ₸")
        else:
            st.metric("✅ В норме", total_good)
    
    if has_prices:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💎 Стоимость остатков", f"{total_stock_value:,.0f} ₸")
        with col2:
            st.metric("✅ В норме", total_good)
        with col3:
            st.metric("📈 Избыток", total_excess)
    
    # Сводка по складам
    st.markdown("### 🏪 Статистика по складам")
    
    warehouse_summary = []
    for warehouse_key, rec in recommendations.items():
        warehouse_summary.append({
            'Склад': rec['short_name'],
            'Город': rec['city'],
            'Тип': rec['type'],
            'Критично': len(rec['critical_items']),
            'Внимание': len(rec['warning_items']),
            'Норма': len(rec['good_items']),
            'Избыток': len(rec['excess_items']),
            'К заказу (₸)': f"{rec['total_order_value']:,.0f}" if has_prices else "Нет цен",
            'Остатки (₸)': f"{rec['total_stock_value']:,.0f}" if has_prices else "Нет цен"
        })
    
    summary_df = pd.DataFrame(warehouse_summary)
    st.dataframe(summary_df, use_container_width=True)
    
    if show_details:
        # Детальный анализ по складам
        st.markdown("### 🔍 Детальный анализ по складам")
        
        selected_warehouse = st.selectbox(
            "Выберите склад для детального просмотра:",
            options=list(recommendations.keys()),
            format_func=lambda x: recommendations[x]['short_name']
        )
        
        if selected_warehouse:
            show_warehouse_detailed_analysis(recommendations[selected_warehouse], has_prices)
        
        # Критичные товары по всем складам
        st.markdown("### 🚨 Критичные товары по всем складам")
        
        critical_items_all = []
        for warehouse_key, rec in recommendations.items():
            for item in rec['critical_items']:
                critical_items_all.append({
                    'Склад': rec['short_name'],
                    'Товар': item['name'],
                    'Остаток': item['current_stock'],
                    'Минимум': item['min_stock'],
                    'Дефицит': item['deficit'],
                    'Дефицит (₸)': f"{item['deficit_value']:,.0f}" if has_prices else "Нет цен",
                    'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "∞"
                })
        
        if critical_items_all:
            critical_df = pd.DataFrame(critical_items_all)
            st.dataframe(critical_df, use_container_width=True)
            
            if has_prices:
                total_critical_value = sum(item.get('deficit_value', 0) for warehouse_key, rec in recommendations.items() for item in rec['critical_items'])
                st.error(f"🚨 Общий дефицит критичных товаров: {total_critical_value:,.0f} ₸")
        else:
            st.success("✅ Критичных товаров не найдено!")


def show_warehouse_detailed_analysis(warehouse_rec, has_prices):
    """
    Показывает детальный анализ конкретного склада
    """
    
    st.markdown(f"#### 🏪 {warehouse_rec['name']} ({warehouse_rec['city']})")
    
    # Метрики по складу
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(warehouse_rec['critical_items']) + len(warehouse_rec['warning_items']) + len(warehouse_rec['good_items']) + len(warehouse_rec['excess_items'])
    
    with col1:
        st.metric("📦 Всего товаров", total_items)
    with col2:
        st.metric("🔴 Критично", len(warehouse_rec['critical_items']))
    with col3:
        st.metric("🟡 Внимание", len(warehouse_rec['warning_items']))
    with col4:
        if has_prices:
            st.metric("💰 К заказу", f"{warehouse_rec['total_order_value']:,.0f} ₸")
        else:
            st.metric("✅ Норма", len(warehouse_rec['good_items']))
    
    # Табы для разных категорий
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 Критично", "🟡 Внимание", "✅ Норма", "📈 Избыток"])
    
    with tab1:
        if warehouse_rec['critical_items']:
            critical_data = []
            for item in warehouse_rec['critical_items']:
                critical_data.append({
                    'Товар': item['name'],
                    'Остаток': item['current_stock'],
                    'Минимум': item['min_stock'],
                    'Дефицит': item['deficit'],
                    'Дефицит (₸)': f"{item['deficit_value']:,.0f}" if has_prices else "Нет цен",
                    'Месяцев': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "0"
                })
            
            critical_df = pd.DataFrame(critical_data)
            st.dataframe(critical_df, use_container_width=True)
        else:
            st.success("✅ Критичных товаров нет")
    
    with tab2:
        if warehouse_rec['warning_items']:
            warning_data = []
            for item in warehouse_rec['warning_items']:
                warning_data.append({
                    'Товар': item['name'],
                    'Остаток': item['current_stock'],
                    'Минимум': item['min_stock'],
                    'Дефицит': item['deficit'],
                    'Дефицит (₸)': f"{item['deficit_value']:,.0f}" if has_prices else "Нет цен",
                    'Месяцев': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "0"
                })
            
            warning_df = pd.DataFrame(warning_data)
            st.dataframe(warning_df, use_container_width=True)
        else:
            st.success("✅ Товаров требующих внимания нет")
    
    with tab3:
        if warehouse_rec['good_items']:
            good_data = []
            for item in warehouse_rec['good_items']:
                good_data.append({
                    'Товар': item['name'],
                    'Остаток': item['current_stock'],
                    'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "∞"
                })
            
            good_df = pd.DataFrame(good_data)
            st.dataframe(good_df, use_container_width=True)
        else:
            st.info("ℹ️ Товаров в норме нет")
    
    with tab4:
        if warehouse_rec['excess_items']:
            excess_data = []
            for item in warehouse_rec['excess_items']:
                excess_data.append({
                    'Товар': item['name'],
                    'Остаток': item['current_stock'],
                    'Максимум': item['max_stock'],
                    'Избыток': item['surplus'],
                    'Месяцев запаса': f"{item['months_stock']:.1f}" if item['months_stock'] < 999 else "∞"
                })
            
            excess_df = pd.DataFrame(excess_data)
            st.dataframe(excess_df, use_container_width=True)
        else:
            st.success("✅ Избыточных товаров нет")


def export_warehouse_analysis_results(analysis_results, recommendations, has_prices):
    """
    Экспортирует результаты анализа в Excel
    """
    
    try:
        from io import BytesIO
        import xlsxwriter
        
        # Создаем Excel файл в памяти
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Форматы
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        critical_format = workbook.add_format({
            'bg_color': '#FF9999',
            'border': 1
        })
        
        warning_format = workbook.add_format({
            'bg_color': '#FFCC99',
            'border': 1
        })
        
        # Лист общей статистики
        summary_sheet = workbook.add_worksheet('Общая статистика')
        
        # Заголовки
        headers = ['Склад', 'Город', 'Тип', 'Критично', 'Внимание', 'Норма', 'Избыток']
        if has_prices:
            headers.extend(['К заказу (₸)', 'Остатки (₸)'])
        
        for col, header in enumerate(headers):
            summary_sheet.write(0, col, header, header_format)
        
        # Данные по складам
        row = 1
        for warehouse_key, rec in recommendations.items():
            summary_sheet.write(row, 0, rec['short_name'])
            summary_sheet.write(row, 1, rec['city'])
            summary_sheet.write(row, 2, rec['type'])
            summary_sheet.write(row, 3, len(rec['critical_items']))
            summary_sheet.write(row, 4, len(rec['warning_items']))
            summary_sheet.write(row, 5, len(rec['good_items']))
            summary_sheet.write(row, 6, len(rec['excess_items']))
            
            if has_prices:
                summary_sheet.write(row, 7, rec['total_order_value'])
                summary_sheet.write(row, 8, rec['total_stock_value'])
            
            row += 1
        
        # Листы по каждому складу
        for warehouse_key, rec in recommendations.items():
            sheet_name = rec['short_name'][:30]  # Ограничение длины имени листа
            sheet = workbook.add_worksheet(sheet_name)
            
            # Критичные товары
            row = 0
            sheet.write(row, 0, 'КРИТИЧНЫЕ ТОВАРЫ', header_format)
            row += 1
            
            if rec['critical_items']:
                critical_headers = ['Товар', 'Остаток', 'Минимум', 'Дефицит']
                if has_prices:
                    critical_headers.append('Дефицит (₸)')
                critical_headers.append('Месяцев запаса')
                
                for col, header in enumerate(critical_headers):
                    sheet.write(row, col, header, header_format)
                row += 1
                
                for item in rec['critical_items']:
                    sheet.write(row, 0, item['name'], critical_format)
                    sheet.write(row, 1, item['current_stock'], critical_format)
                    sheet.write(row, 2, item['min_stock'], critical_format)
                    sheet.write(row, 3, item['deficit'], critical_format)
                    
                    col_idx = 4
                    if has_prices:
                        sheet.write(row, col_idx, item['deficit_value'], critical_format)
                        col_idx += 1
                    
                    months = item['months_stock'] if item['months_stock'] < 999 else 0
                    sheet.write(row, col_idx, months, critical_format)
                    row += 1
            
            row += 2
            
            # Товары требующие внимания
            sheet.write(row, 0, 'ТРЕБУЮТ ВНИМАНИЯ', header_format)
            row += 1
            
            if rec['warning_items']:
                for col, header in enumerate(critical_headers):
                    sheet.write(row, col, header, header_format)
                row += 1
                
                for item in rec['warning_items']:
                    sheet.write(row, 0, item['name'], warning_format)
                    sheet.write(row, 1, item['current_stock'], warning_format)
                    sheet.write(row, 2, item['min_stock'], warning_format)
                    sheet.write(row, 3, item['deficit'], warning_format)
                    
                    col_idx = 4
                    if has_prices:
                        sheet.write(row, col_idx, item['deficit_value'], warning_format)
                        col_idx += 1
                    
                    months = item['months_stock'] if item['months_stock'] < 999 else 0
                    sheet.write(row, col_idx, months, warning_format)
                    row += 1
        
        workbook.close()
        output.seek(0)
        
        # Кнопка скачивания
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"warehouse_analysis_{timestamp}.xlsx"
        
        st.download_button(
            label="📥 Скачать детальный отчет",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Отчет готов к скачиванию: {filename}")
        
    except Exception as e:
        st.error(f"❌ Ошибка создания отчета: {str(e)}")


# ===== ИНСТРУКЦИИ ПО ИНТЕГРАЦИИ =====

def get_integration_instructions():
    """
    Возвращает инструкции по интеграции исправлений
    """
    
    return f"""
# 🚀 ИНСТРУКЦИИ ПО ИНТЕГРАЦИИ ИСПРАВЛЕНИЙ

## ❌ РЕШАЕМЫЕ ПРОБЛЕМЫ:

1. **❌ Ошибка 'номенклатура'** - неправильное чтение структуры файла остатков
2. **❌ Отсутствующие методы** - analyze_warehouse_stock_with_details и другие
3. **❌ Неправильная обработка файлов** - сложная структура Excel файлов
4. **❌ Отсутствие цен** - интеграция с ценами из ADS
5. **❌ Плохое отображение результатов** - улучшенная визуализация

## 🚀 БЫСТРАЯ ИНТЕГРАЦИЯ:

### Шаг 1: Создайте файл `warehouse_complete_fix.py`
Скопируйте весь код из артефакта

### Шаг 2: Добавьте в ваш основной streamlit файл

```python
# В начале файла добавьте импорт:
from warehouse_complete_fix import (
    apply_warehouse_complete_fix,
    create_fixed_warehouse_analysis_page
)

# В функции где определяются страницы добавьте:
elif page == "📦 Анализ складов":
    warehouse_analysis_page_fixed = create_fixed_warehouse_analysis_page()
    warehouse_analysis_page_fixed(system)
```

### Шаг 3: ИЛИ замените существующую функцию

Если у вас уже есть `warehouse_analysis_page`, замените её на:

```python
def warehouse_analysis_page(system):
    # Применяем исправления
    if not hasattr(system, '_warehouse_fix_applied'):
        from warehouse_complete_fix import apply_warehouse_complete_fix
        apply_warehouse_complete_fix(system)
    
    # Вызываем исправленную версию
    from warehouse_complete_fix import create_fixed_warehouse_analysis_page
    fixed_page = create_fixed_warehouse_analysis_page()
    fixed_page(system)
```

## ✅ РЕЗУЛЬТАТ ПОСЛЕ ПРИМЕНЕНИЯ:

1. **Правильное чтение файлов остатков** любой структуры
2. **Автоматическое определение складов** и их настроек
3. **Интеграция с ценами** из ADS данных
4. **Детальный анализ** по каждому складу
5. **Красивое отображение результатов** с фильтрами
6. **Excel экспорт** с детальными отчетами
7. **Рекомендации по заказам** в денежном выражении

## 📊 СТРУКТУРА ПОДДЕРЖИВАЕМЫХ ФАЙЛОВ:

Код автоматически определяет:
- Строку с заголовком "Номенклатура"
- Колонки складов (содержащие "склад" или "магазин")
- Строки с данными товаров
- Дополнительные заголовки ("Количество", "Остаток")

## 🎯 ИСПОЛЬЗОВАНИЕ:

1. Рассчитайте ADS в разделе "ADS расчет"
2. Перейдите в "Анализ складов"
3. Загрузите файл остатков (любой структуры)
4. Настройте параметры анализа
5. Запустите анализ
6. Просмотрите результаты и экспортируйте отчет

## 🔧 ОТЛАДКА:

Включите "Режим отладки" для просмотра:
- Процесса чтения файла
- Найденных заголовков и складов
- Обработанных данных
- Подробностей анализа
"""


if __name__ == "__main__":
    print("🔧 Модуль исправлений анализа складов загружен")
    print(get_integration_instructions())