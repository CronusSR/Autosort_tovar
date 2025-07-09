# warehouse_analysis_fixed_mapping.py
"""
Анализ складов с исправленным маппингом
Точное соответствие колонок и структуры
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from io import BytesIO


class WarehouseAnalyzer:
    """Класс для анализа остатков по складам с точным маппингом"""
    
    def __init__(self):
        # Маппинг названий филиалов к складам (по названиям из branch_name)
        self.ads_file_mapping = {
            'барыс': ['Барыс TRADE'],
            'казыбаева': ['Казыбаева TRADE', 'Казыбаева магазин'],  # Объединяем оба склада Казыбаева
            # ИСПРАВЛЕНО: Разделяем склад и магазин Шымкент на разные ADS
            'шымкент_склад': ['Шымкент Овощная'],                   # Только склад
            'шымкент_магазин': ['Овощная Магазин'],                 # Только магазин
            'астана': ['Магазин Астана'],                           # Только магазин Астана
            'астана_склад': ['Склад №1'],                           # Только склад Астана
            # База Комплект и другие используют общий ADS
            'общий': ['База Комплект', 'АО TRADE', 'Комсомольская', 'Алматинский']
        }
        
        # Точный маппинг колонок к складам (индекс колонки -> информация о складе)
        self.warehouse_mapping = {
            3: {
                'name': 'Шымкент Овощная',
                'full_name': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'level': 'secondary',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_to': ['Овощная Магазин'],
                'feeds_from': 'База Комплект',
                'type': 'Склад второго уровня'
            },
            4: {
                'name': 'Овощная Магазин',
                'full_name': '6 Склад фурнитуры "Овощная база" Магазин',
                'level': 'store',
                'multiplier': 1.0,  # БЕЗ ИЗМЕНЕНИЙ
                'feeds_from': 'Шымкент Овощная',
                'type': 'Магазин'
            },
            5: {
                'name': 'Комсомольская',
                'full_name': 'Комсомольская Фурнитура',
                'level': 'regional',
                'multiplier': 1.0,  # УБРАН множитель
                'type': 'Региональный склад'
            },
            6: {
                'name': 'АО TRADE',
                'full_name': 'АО Склад Фурнитура TRADE',
                'level': 'secondary',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_from': 'База Комплект',
                'type': 'Склад второго уровня',
                'note': 'Только кромочные материалы'
            },
            7: {
                'name': 'Алматинский',
                'full_name': 'Алматинский филиал фурнитура',
                'level': 'regional',
                'multiplier': 1.0,  # УБРАН множитель
                'type': 'Региональный склад'
            },
            8: {
                'name': 'База Комплект',
                'full_name': 'База Склад Фурнитура Комплект',
                'level': 'hub',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_to': ['Казыбаева TRADE', 'Барыс TRADE', 'АО TRADE', 'Шымкент Овощная', 'Склад №1'],
                'type': 'Главный ХАБ',
                'note': '95% всех приходов'
            },
            9: {
                'name': 'Барыс TRADE',
                'full_name': 'Барыс Склад Фурнитура TRADE',
                'level': 'secondary',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_from': 'База Комплект',
                'type': 'Склад второго уровня'
            },
            10: {
                'name': 'Казыбаева TRADE',
                'full_name': 'Казыбаева Склад Фурнитура TRADE',
                'level': 'secondary',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_to': ['Казыбаева магазин'],
                'feeds_from': 'База Комплект',
                'type': 'Склад второго уровня'
            },
            11: {
                'name': 'Магазин Астана',
                'full_name': 'Магазин фурнитуры г.Астана',
                'level': 'store',
                'multiplier': 1.0,
                'feeds_from': 'Склад №1',
                'type': 'Магазин'
            },
            12: {
                'name': 'Склад №1',
                'full_name': 'склад фурнитура № 1',
                'level': 'secondary',
                'multiplier': 1.0,  # УБРАН множитель
                'feeds_to': ['Магазин Астана'],
                'feeds_from': 'База Комплект',
                'type': 'Склад второго уровня'
            },
            13: {
                'name': 'Казыбаева магазин',
                'full_name': 'ТД Казыбаева ФУРНИТУРА магазин',
                'level': 'store',
                'multiplier': 1.0,
                'feeds_from': 'Казыбаева TRADE',
                'type': 'Магазин'
            }
        }
    
    def read_remains_file(self, uploaded_file):
        """Читает файл остатков с правильной структурой"""
        try:
            # Читаем Excel файл без заголовков
            df_raw = pd.read_excel(uploaded_file, header=None)
            
            # Проверяем размер
            if df_raw.shape[0] < 10:
                st.error("Файл слишком мал. Нужно минимум 10 строк.")
                return None
            
            # Берем заголовки из 7й строки (индекс 6)
            headers = df_raw.iloc[6].tolist() if len(df_raw) > 6 else None
            if headers is None:
                st.error("Не найдена строка с заголовками (строка 7)")
                return None
            
            # Берем данные начиная с 10й строки (индекс 9)
            data_df = df_raw.iloc[9:].copy()
            data_df.columns = headers
            
            # Убираем пустые строки
            data_df = data_df.dropna(subset=[data_df.columns[0]])
            
            st.success(f"✅ Загружено {len(data_df)} товаров")
            
            return data_df
            
        except Exception as e:
            st.error(f"Ошибка чтения файла: {str(e)}")
            return None
    
    def auto_fill_ads_with_subcategory_averages(self, ads_data):
        """
        Автоматически заполняет ADS=0 средними значениями по подкатегории
        Работает прямо в ADS данных, добавляя подкатегории из названий товаров
        """
        filled_count = 0
        
        if isinstance(ads_data, dict):
            # Множественная загрузка - обрабатываем каждый филиал
            for branch_name, branch_result in ads_data.items():
                # ИСПРАВЛЕНО: Извлекаем processed data из результата integration_patch
                if isinstance(branch_result, dict) and 'data' in branch_result:
                    branch_ads = branch_result['data']  # Берем processed DataFrame
                else:
                    branch_ads = branch_result  # Для совместимости с прямыми DataFrame
                
                if branch_ads is None or branch_ads.empty:
                    continue
                
                # Проверяем наличие нужных колонок
                if 'номенклатура' not in branch_ads.columns or 'ads' not in branch_ads.columns:
                    st.warning(f"⚠️ Филиал {branch_name}: отсутствуют необходимые колонки для автозаполнения")
                    continue
                
                # Определяем подкатегории из названий товаров ТОЛЬКО ДЛЯ ТЕКУЩЕГО ФИЛИАЛА
                subcategory_ads = {}
                processed_items = 0
                
                st.info(f"🔍 Анализируем подкатегории для филиала {branch_name}...")
                
                for _, row in branch_ads.iterrows():
                    try:
                        item_name = str(row['номенклатура'])
                        ads_value = float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0
                        processed_items += 1
                    except (KeyError, ValueError, TypeError):
                        continue  # Пропускаем строки с проблемными данными
                    
                    if ads_value > 0:
                        # Извлекаем подкатегорию из названия (первые 2-3 слова)
                        words = item_name.split()
                        subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                        
                        if subcategory not in subcategory_ads:
                            subcategory_ads[subcategory] = []
                        subcategory_ads[subcategory].append(ads_value)
                
                # Рассчитываем средние по подкатегориям ТОЛЬКО ДЛЯ ЭТОГО ФИЛИАЛА
                subcategory_averages = {}
                for subcategory, ads_values in subcategory_ads.items():
                    if ads_values:
                        avg_ads = sum(ads_values) / len(ads_values)
                        subcategory_averages[subcategory] = avg_ads
                
                st.info(f"📊 {branch_name}: найдено {len(subcategory_averages)} подкатегорий с ADS>0 из {processed_items} товаров")
                
                # Показываем топ-5 подкатегорий для этого филиала
                if subcategory_averages:
                    top_subcategories = sorted(subcategory_averages.items(), key=lambda x: x[1], reverse=True)[:5]
                    subcats_text = ", ".join([f"{name}: {avg:.3f}" for name, avg in top_subcategories])
                    st.info(f"🏆 Топ подкатегории {branch_name}: {subcats_text}")
                
                # Заполняем нулевые ADS средними значениями
                branch_filled = 0
                for idx, row in branch_ads.iterrows():
                    try:
                        ads_value = float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0
                        
                        if ads_value == 0:
                            item_name = str(row['номенклатура'])
                            words = item_name.split()
                            
                            # Пробуем несколько вариантов автозаполнения
                            found_replacement = False
                            
                            # 1. Точная подкатегория (первые 2 слова)
                            subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                            if subcategory in subcategory_averages:
                                branch_ads.at[idx, 'ads'] = subcategory_averages[subcategory]
                                filled_count += 1
                                branch_filled += 1
                                found_replacement = True
                            
                            # 2. Если не найдено, пробуем первое слово
                            elif not found_replacement and words:
                                first_word = words[0]
                                if first_word in subcategory_averages:
                                    branch_ads.at[idx, 'ads'] = subcategory_averages[first_word]
                                    filled_count += 1
                                    branch_filled += 1
                                    found_replacement = True
                            
                            # 3. Минимальный ADS для товаров без аналогов
                            if not found_replacement and subcategory_averages:
                                overall_avg = sum(subcategory_averages.values()) / len(subcategory_averages)
                                if overall_avg > 0:
                                    branch_ads.at[idx, 'ads'] = max(0.01, overall_avg * 0.05)  # 5% от среднего, минимум 0.01
                                    filled_count += 1
                                    branch_filled += 1
                    except (KeyError, ValueError, TypeError):
                        continue  # Пропускаем строки с проблемными данными
                
                if subcategory_averages:
                    st.info(f"📊 Филиал {branch_name}: найдено {len(subcategory_averages)} подкатегорий, заполнено {branch_filled} товаров")
                    
                # Показываем статистику товаров с ADS=0 для филиала
                zero_ads_after_fill = (branch_ads['ads'] == 0).sum()
                total_branch_items = len(branch_ads)
                st.info(f"ℹ️ {branch_name}: после автозаполнения ADS=0: {zero_ads_after_fill} из {total_branch_items} ({zero_ads_after_fill/total_branch_items*100:.1f}%)")
        
        elif isinstance(ads_data, pd.DataFrame):
            # Одиночная загрузка - обрабатываем ОБЩИЙ DataFrame для всех складов
            subcategory_ads = {}
            processed_items = 0
            
            st.info(f"🔍 Анализируем подкатегории из ОБЩЕГО файла ADS...")
            
            # Определяем подкатегории и собираем ADS > 0 ИЗ ОБЩЕГО ПУЛА
            for _, row in ads_data.iterrows():
                item_name = str(row['номенклатура'])
                ads_value = float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0
                processed_items += 1
                
                if ads_value > 0:
                    words = item_name.split()
                    subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                    
                    if subcategory not in subcategory_ads:
                        subcategory_ads[subcategory] = []
                    subcategory_ads[subcategory].append(ads_value)
            
            # Рассчитываем средние ИЗ ОБЩЕГО ПУЛА
            subcategory_averages = {}
            for subcategory, ads_values in subcategory_ads.items():
                if ads_values:
                    subcategory_averages[subcategory] = sum(ads_values) / len(ads_values)
            
            st.info(f"📊 ОБЩИЙ анализ: найдено {len(subcategory_averages)} подкатегорий с ADS>0 из {processed_items} товаров")
            
            # Показываем топ-5 подкатегорий из общего пула
            if subcategory_averages:
                top_subcategories = sorted(subcategory_averages.items(), key=lambda x: x[1], reverse=True)[:5]
                subcats_text = ", ".join([f"{name}: {avg:.3f}" for name, avg in top_subcategories])
                st.info(f"🏆 Топ подкатегории ОБЩИЕ: {subcats_text}")
            
            # Заполняем нулевые ADS
            for idx, row in ads_data.iterrows():
                ads_value = float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0
                
                if ads_value == 0:
                    item_name = str(row['номенклатура'])
                    words = item_name.split()
                    
                    # Улучшенное автозаполнение для одиночной загрузки
                    found_replacement = False
                    
                    # 1. Точная подкатегория
                    subcategory = ' '.join(words[:2]) if len(words) >= 2 else words[0] if words else 'Общая'
                    if subcategory in subcategory_averages:
                        ads_data.at[idx, 'ads'] = subcategory_averages[subcategory]
                        filled_count += 1
                        found_replacement = True
                    
                    # 2. Первое слово
                    elif not found_replacement and words:
                        first_word = words[0]
                        if first_word in subcategory_averages:
                            ads_data.at[idx, 'ads'] = subcategory_averages[first_word]
                            filled_count += 1
                            found_replacement = True
                    
                    # 3. Общий средний ADS (минимальный)
                    if not found_replacement and subcategory_averages:
                        overall_avg = sum(subcategory_averages.values()) / len(subcategory_averages)
                        if overall_avg > 0:
                            ads_data.at[idx, 'ads'] = max(0.01, overall_avg * 0.05)
                            filled_count += 1
            
            if subcategory_averages:
                st.success(f"🔄 Автозаполнение: найдено {len(subcategory_averages)} подкатегорий, заполнено {filled_count} товаров с ADS=0")
                
            # Показываем итоговую статистику
            zero_ads_after_fill = (ads_data['ads'] == 0).sum()
            total_items = len(ads_data)
            st.info(f"ℹ️ После автозаполнения ADS=0: {zero_ads_after_fill} из {total_items} ({zero_ads_after_fill/total_items*100:.1f}%)")
        
        return filled_count

    def get_subcategory_average_ads(self, ads_data, subcategory_data=None):
        """Рассчитывает средний ADS по подкатегориям для каждого филиала (устаревшая версия)"""
        # Теперь используется auto_fill_ads_with_subcategory_averages
        return {}

    def analyze_warehouses(self, remains_df, ads_data=None, subcategory_data=None, min_days=15, max_days=45):
        """Анализ складов с использованием точного маппинга"""
        
        if remains_df is None or remains_df.empty:
            return None
        
        results = []
        nomenclature_col = remains_df.columns[0]
        
        # Автоматически заполняем ADS=0 средними по подкатегориям
        if ads_data is not None:
            filled_count = self.auto_fill_ads_with_subcategory_averages(ads_data)
            if filled_count > 0:
                st.success(f"🔄 Автозаполнено {filled_count} товаров с ADS=0 средними значениями по подкатегориям")
            
            # Показываем статистику товаров с ADS=0
            if isinstance(ads_data, pd.DataFrame):
                zero_ads_count = (ads_data['ads'] == 0).sum()
                total_count = len(ads_data)
                if zero_ads_count > 0:
                    st.info(f"ℹ️ Товаров с ADS=0: {zero_ads_count} из {total_count} ({zero_ads_count/total_count*100:.1f}%)")
            elif isinstance(ads_data, dict):
                for file_key, ads_result in ads_data.items():
                    if isinstance(ads_result, dict) and 'data' in ads_result:
                        ads_df = ads_result['data']
                        if ads_df is not None and not ads_df.empty:
                            zero_ads_count = (ads_df['ads'] == 0).sum()
                            total_count = len(ads_df)
                            if zero_ads_count > 0:
                                st.info(f"ℹ️ {file_key}: товаров с ADS=0: {zero_ads_count} из {total_count} ({zero_ads_count/total_count*100:.1f}%)")
        
        # Создаем словарь для быстрого поиска ADS по филиалам
        ads_lookup_by_branch = {}
        
        if ads_data is not None:
            # ads_data может быть либо DataFrame (одиночная загрузка), либо словарь филиалов (множественная)
            if isinstance(ads_data, pd.DataFrame):
                # Одиночная загрузка ADS - один файл для всех складов
                st.info("📊 Используются общие ADS данные для всех складов")
                
                # Создаем общий lookup
                general_lookup = {}
                price_count = 0
                
                for _, row in ads_data.iterrows():
                    item_name = str(row['номенклатура'])
                    price_val = float(row['last_purchase_price']) if 'last_purchase_price' in row and pd.notna(row['last_purchase_price']) else 0.0
                    if price_val > 0:
                        price_count += 1
                        
                    general_lookup[item_name] = {
                        'ads': float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0,
                        'price': price_val
                    }
                
                st.success(f"✅ Загружено товаров с ценами: {price_count} из {len(ads_data)}")
                
                # Применяем общий lookup ко всем складам
                for branches in self.ads_file_mapping.values():
                    for branch in branches:
                        ads_lookup_by_branch[branch] = general_lookup
                        
            elif isinstance(ads_data, dict):
                # Множественная загрузка - словарь с ADS по филиалам
                st.info("📊 Загружены ADS данные по филиалам:")
                
                for file_key, ads_result in ads_data.items():
                    # ИСПРАВЛЕНО: Извлекаем processed data из результата integration_patch
                    if isinstance(ads_result, dict) and 'data' in ads_result:
                        ads_df = ads_result['data']  # Берем processed DataFrame
                    else:
                        ads_df = ads_result  # Для совместимости с прямыми DataFrame
                    
                    if ads_df is None or ads_df.empty:
                        continue
                        
                    # Создаем lookup для этого файла
                    file_lookup = {}
                    price_count = 0
                    
                    for _, row in ads_df.iterrows():
                        item_name = str(row['номенклатура'])
                        price_val = float(row['last_purchase_price']) if 'last_purchase_price' in row and pd.notna(row['last_purchase_price']) else 0.0
                        if price_val > 0:
                            price_count += 1
                        
                        file_lookup[item_name] = {
                            'ads': float(row['ads']) if 'ads' in row and pd.notna(row['ads']) else 0.0,
                            'price': price_val
                        }
                    
                    # Применяем к соответствующим складам
                    if file_key in self.ads_file_mapping:
                        for branch in self.ads_file_mapping[file_key]:
                            ads_lookup_by_branch[branch] = file_lookup
                        st.success(f"  ✓ {file_key}: {len(ads_df)} товаров, {price_count} с ценами → {', '.join(self.ads_file_mapping[file_key])}")
                    else:
                        # Если нет специфичного маппинга, применяем к складам без ADS
                        st.info(f"  📋 {file_key}: применяется к складам без специфичного ADS")
                        
                        # Находим склады без ADS данных
                        all_warehouses = set()
                        mapped_warehouses = set()
                        
                        for branches in self.ads_file_mapping.values():
                            for branch in branches:
                                all_warehouses.add(branch)
                        
                        for existing_branch in ads_lookup_by_branch.keys():
                            mapped_warehouses.add(existing_branch)
                        
                        unmapped_warehouses = all_warehouses - mapped_warehouses
                        
                        for branch in unmapped_warehouses:
                            ads_lookup_by_branch[branch] = file_lookup
                        
                        if unmapped_warehouses:
                            st.success(f"    → {', '.join(unmapped_warehouses)}")
        
        # Прогресс
        progress_bar = st.progress(0)
        total_items = len(remains_df)
        
        for idx, (_, row) in enumerate(remains_df.iterrows()):
            progress_bar.progress((idx + 1) / total_items)
            
            item_name = str(row[nomenclature_col])
            if pd.isna(item_name) or item_name == '':
                continue
            
            # Анализ по каждому складу
            item_warehouses = {}
            total_stock = 0.0
            total_order = 0.0
            
            for col_idx, wh_info in self.warehouse_mapping.items():
                wh_name = wh_info['name']
                
                # Получаем ADS и цену для конкретного склада
                if wh_name in ads_lookup_by_branch and item_name in ads_lookup_by_branch[wh_name]:
                    wh_ads_data = ads_lookup_by_branch[wh_name][item_name]
                    ads_value = wh_ads_data['ads']
                    price = wh_ads_data['price']
                else:
                    # Если нет данных для этого склада, используем 0
                    ads_value = 0.0
                    price = 0.0
                
                # Получаем остаток
                try:
                    if col_idx < len(row):
                        current_stock = float(row.iloc[col_idx]) if pd.notna(row.iloc[col_idx]) else 0.0
                    else:
                        current_stock = 0.0
                except:
                    current_stock = 0.0
                
                total_stock += current_stock
                
                # Рассчитываем MIN/MAX с учетом уровня склада
                multiplier = wh_info['multiplier']
                min_stock = ads_value * min_days * multiplier
                max_stock = ads_value * max_days * multiplier
                
                # Определяем статус
                if ads_value == 0:
                    # Если нет продаж, анализируем остатки
                    if current_stock == 0:
                        status = 'no_ads'
                        status_text = 'Нет продаж - OK'
                    elif current_stock > 0:
                        status = 'no_ads_stock'
                        status_text = f'Нет продаж, остаток {current_stock:.1f}'
                    else:
                        status = 'no_ads'
                        status_text = 'Нет ADS данных'
                elif current_stock == 0 and ads_value > 0.5:  # Критично только если есть хорошие продажи
                    status = 'critical'
                    status_text = 'Критично'
                elif current_stock < min_stock * 0.3 and ads_value > 0.5:  # Критично только при активных продажах
                    status = 'critical'
                    status_text = 'Критично'
                elif current_stock < min_stock * 0.7:
                    status = 'warning'
                    status_text = 'Внимание'
                elif current_stock < min_stock:
                    status = 'low'
                    status_text = 'Низкий запас'
                elif current_stock <= max_stock:
                    status = 'good'
                    status_text = 'В норме'
                else:
                    status = 'excess'
                    status_text = 'Избыток'
                
                # Количество к заказу (до MIN)
                order_qty = max(0, min_stock - current_stock) if status in ['critical', 'warning'] else 0
                total_order += order_qty
                
                # Определяем источник пополнения
                source = "Поставщик"
                if 'feeds_from' in wh_info:
                    source = f"от {wh_info['feeds_from']}"
                
                # Стоимость заказа = цена × количество к заказу
                order_value = price * order_qty if price > 0 else 0
                
                item_warehouses[wh_info['name']] = {
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'max_stock': max_stock,
                    'ads': ads_value,
                    'price': price,
                    'status': status,
                    'status_text': status_text,
                    'order_quantity': order_qty,
                    'order_value': order_value,
                    'source': source,
                    'level': wh_info['level'],
                    'type': wh_info['type'],
                    'multiplier': multiplier
                }
            
            # Добавляем только если есть остатки или нужен заказ
            if total_stock > 0 or total_order > 0:
                results.append({
                    'nomenclature': item_name,
                    'warehouses': item_warehouses,
                    'total_stock': total_stock,
                    'total_order': total_order
                })
        
        progress_bar.empty()
        return results
    
    def display_analysis_results(self, results):
        """Отображение результатов анализа с табами для каждого склада"""
        
        if not results:
            st.warning("Нет данных для отображения")
            return
        
        # Общая статистика
        st.subheader("📊 Общая статистика")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_items = len(results)
        critical_count = sum(1 for item in results 
                           for wh in item['warehouses'].values() 
                           if wh['status'] == 'critical')
        warning_count = sum(1 for item in results 
                          for wh in item['warehouses'].values() 
                          if wh['status'] == 'warning')
        total_order_value = sum(wh['order_value'] for item in results 
                              for wh in item['warehouses'].values() 
                              if wh['source'] == 'Поставщик')
        
        with col1:
            st.metric("Товаров проанализировано", f"{total_items:,}")
        with col2:
            st.metric("Критических позиций", f"{critical_count:,}")
        with col3:
            st.metric("Требуют внимания", f"{warning_count:,}")
        with col4:
            st.metric("Стоимость заказов", f"{total_order_value:,.0f} ₸")
        
        # Табы для анализа по складам
        st.subheader("📦 Анализ по складам")
        
        # Создаем табы для каждого склада
        tab_names = []
        for col_idx, wh_info in sorted(self.warehouse_mapping.items()):
            tab_names.append(wh_info['name'])
        
        tabs = st.tabs(tab_names)
        
        # Анализ для каждого склада
        for tab_idx, (col_idx, wh_info) in enumerate(sorted(self.warehouse_mapping.items())):
            with tabs[tab_idx]:
                wh_name = wh_info['name']
                
                # Статистика по складу
                wh_stats = {
                    'total_items': 0,
                    'critical': 0,
                    'warning': 0,
                    'low': 0,
                    'good': 0,
                    'excess': 0,
                    'no_ads': 0,
                    'no_ads_stock': 0,  # ДОБАВЛЕН новый статус
                    'total_stock': 0,
                    'total_order': 0,
                    'total_value': 0
                }
                
                # Собираем данные по складу
                wh_items = []
                for item in results:
                    if wh_name in item['warehouses']:
                        wh_data = item['warehouses'][wh_name]
                        wh_stats['total_items'] += 1
                        wh_stats[wh_data['status']] += 1
                        wh_stats['total_stock'] += wh_data['current_stock']
                        wh_stats['total_order'] += wh_data['order_quantity']
                        # Считаем стоимость для всех заказов, независимо от источника
                        wh_stats['total_value'] += wh_data['order_value']
                        
                        if wh_data['current_stock'] > 0 or wh_data['order_quantity'] > 0:
                            wh_items.append({
                                'Товар': item['nomenclature'][:50] + "..." if len(item['nomenclature']) > 50 else item['nomenclature'],
                                'Остаток': f"{wh_data['current_stock']:.0f}",
                                'MIN': f"{wh_data['min_stock']:.1f}",
                                'MAX': f"{wh_data['max_stock']:.1f}",
                                'ADS': f"{wh_data['ads']:.2f}",
                                'К заказу': f"{wh_data['order_quantity']:.0f}",
                                'Источник': wh_data['source'],
                                'Цена': f"{wh_data['price']:.0f} ₸" if wh_data['price'] > 0 else "-",
                                'Стоимость': f"{wh_data['order_value']:.0f} ₸" if wh_data['order_value'] > 0 else "-",
                                'Статус': wh_data['status_text']
                            })
                
                # Информация о складе
                info_text = f"""
                **{wh_info['full_name']}**
                - Тип: {wh_info['type']}
                - Уровень: {wh_info['level'].upper()}
                - Множитель запасов: {wh_info['multiplier']}x
                """
                
                # Добавляем дополнительную информацию если есть
                if 'note' in wh_info:
                    info_text += f"\n- Примечание: {wh_info['note']}"
                if 'feeds_from' in wh_info:
                    info_text += f"\n- Питается от: {wh_info['feeds_from']}"
                if 'feeds_to' in wh_info:
                    info_text += f"\n- Снабжает: {', '.join(wh_info['feeds_to'])}"
                
                st.markdown(info_text)
                
                # Метрики склада
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Всего товаров", f"{wh_stats['total_items']:,}")
                with col2:
                    st.metric("Общий остаток", f"{wh_stats['total_stock']:,.0f}")
                with col3:
                    st.metric("К заказу", f"{wh_stats['total_order']:,.0f}")
                with col4:
                    st.metric("Сумма заказов", f"{wh_stats['total_value']:,.0f} ₸")
                
                # График статусов
                if wh_stats['total_items'] > 0:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=['Критично', 'Внимание', 'Низкий запас', 'В норме', 'Избыток', 'Без ADS', 'Остатки без продаж'],
                            y=[wh_stats['critical'], wh_stats['warning'], wh_stats['low'], 
                               wh_stats['good'], wh_stats['excess'], wh_stats['no_ads'], wh_stats['no_ads_stock']],
                            marker_color=['red', 'orange', 'yellow', 'green', 'blue', 'gray', 'lightgray']
                        )
                    ])
                    fig.update_layout(
                        title=f"Распределение статусов товаров",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{wh_name}")
                
                # Таблица товаров
                if wh_items:
                    st.markdown("**Детальная информация по товарам:**")
                    
                    # Фильтр по статусу
                    status_filter = st.selectbox(
                        "Фильтр по статусу:",
                        ['Все', 'Критично', 'Внимание', 'Низкий запас', 'В норме', 'Избыток'],
                        key=f"status_filter_{wh_name}"
                    )
                    
                    # Применяем фильтр
                    if status_filter != 'Все':
                        wh_items = [item for item in wh_items if item['Статус'] == status_filter]
                    
                    if wh_items:
                        df = pd.DataFrame(wh_items)
                        st.dataframe(df, use_container_width=True)
                        
                        # Кнопка экспорта
                        if st.button(f"📥 Экспорт {wh_name}", key=f"export_{wh_name}"):
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, sheet_name=wh_name, index=False)
                            
                            st.download_button(
                                label=f"💾 Скачать {wh_name}.xlsx",
                                data=output.getvalue(),
                                file_name=f"analysis_{wh_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_{wh_name}"
                            )
                    else:
                        st.info(f"Нет товаров с статусом '{status_filter}'")
                else:
                    st.info("Нет данных для отображения")
        
        # Рекомендации по перемещениям
        st.subheader("🔄 Рекомендации по перемещениям")
        
        transfer_recommendations = []
        
        # Ищем возможности для перемещений
        for item in results:
            # Находим склады с избытком и дефицитом
            for wh_name, wh_data in item['warehouses'].items():
                if wh_data['status'] in ['critical', 'warning']:
                    # Этот склад нуждается в пополнении
                    needed_qty = wh_data['order_quantity']
                    
                    # Ищем склады с избытком этого товара
                    for source_name, source_data in item['warehouses'].items():
                        if source_name != wh_name and source_data['status'] == 'excess':
                            # Проверяем связь между складами
                            source_info = None
                            target_info = None
                            
                            for col_idx, info in self.warehouse_mapping.items():
                                if info['name'] == source_name:
                                    source_info = info
                                if info['name'] == wh_name:
                                    target_info = info
                            
                            # Проверяем может ли source питать target
                            can_transfer = False
                            if source_info and target_info:
                                if 'feeds_to' in source_info and wh_name in source_info.get('feeds_to', []):
                                    can_transfer = True
                                elif 'feeds_from' in target_info and source_name == target_info.get('feeds_from'):
                                    can_transfer = True
                            
                            if can_transfer:
                                available_qty = source_data['current_stock'] - source_data['max_stock']
                                if available_qty > 0 and needed_qty > 0:
                                    transfer_qty = min(available_qty, needed_qty)
                                    
                                    transfer_recommendations.append({
                                        'Товар': item['nomenclature'][:40] + "...",
                                        'Откуда': source_name,
                                        'Куда': wh_name,
                                        'Количество': f"{transfer_qty:.0f}",
                                        'Текущий остаток (откуда)': f"{source_data['current_stock']:.0f}",
                                        'Текущий остаток (куда)': f"{wh_data['current_stock']:.0f}",
                                        'Приоритет': 'Высокий' if wh_data['status'] == 'critical' else 'Средний'
                                    })
        
        if transfer_recommendations:
            df_transfers = pd.DataFrame(transfer_recommendations)
            st.dataframe(df_transfers, use_container_width=True)
            
            # Экспорт рекомендаций
            if st.button("📥 Экспорт рекомендаций по перемещениям"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_transfers.to_excel(writer, sheet_name='Перемещения', index=False)
                
                st.download_button(
                    label="💾 Скачать рекомендации.xlsx",
                    data=output.getvalue(),
                    file_name="transfer_recommendations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("Рекомендации по перемещениям не найдены. Возможные причины:")
            st.markdown("""
            - Нет складов с избытком товаров
            - Нет связей между складами для перемещений
            - Все товары находятся в оптимальном количестве
            """)


def warehouse_analysis_page(system):
    """Главная страница анализа складов"""
    
    st.header("🏭 Анализ складов")
    st.markdown("*Анализ остатков по складам с расчетом MIN/MAX запасов на основе ADS*")
    
    # Всегда создаем новый анализатор для избежания конфликтов
    system.warehouse_analyzer = WarehouseAnalyzer()
    
    # Проверяем статус ADS
    ads_available = False
    ads_count = 0
    ads_data = None
    
    
    # Проверяем множественные файлы ADS (приоритет)
    if hasattr(system, 'multiple_files_data') and system.multiple_files_data:
        if 'processed_results' in system.multiple_files_data:
            # Собираем ADS данные по филиалам ИЗ calculated_ads с информацией о ветках
            ads_data = {}
            
            # Если в calculated_ads есть колонка 'branch', используем её
            if hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
                if 'branch' in system.calculated_ads.columns:
                    # Разделяем объединенные данные обратно по филиалам
                    for branch in system.calculated_ads['branch'].unique():
                        if pd.notna(branch) and branch.strip():
                            # Фильтруем данные по филиалу
                            branch_data = system.calculated_ads[
                                system.calculated_ads['branch'].str.contains(branch, na=False)
                            ].copy()
                            if not branch_data.empty:
                                ads_data[branch] = branch_data
                                ads_count += len(branch_data)
                
                if ads_data:
                    ads_available = True
                    st.success(f"✅ Загружены ADS данные по филиалам из объединенного файла: {list(ads_data.keys())}")
                else:
                    # Если не удалось разделить, берем данные из отдельных результатов
                    for filename, result in system.multiple_files_data['processed_results'].items():
                        if result and isinstance(result, dict) and result.get('success', False):
                            # Ищем обработанные данные с рассчитанным ADS
                            ads_df = None
                            if 'data' in result:
                                ads_df = result['data']  # Обработанные данные с ADS
                            elif 'ads_data' in result:
                                ads_df = result['ads_data']
                            elif 'processed_data' in result:
                                ads_df = result['processed_data']
                            
                            if ads_df is not None and not ads_df.empty:
                                branch_name = system.multiple_files_data['uploaded_files'][filename]['branch_name']
                                
                                # Отладка: проверяем структуру данных
                                st.write(f"🔍 {filename} колонки: {list(ads_df.columns)}")
                                
                                # Проверяем наличие нужных колонок
                                has_nomenclature = 'номенклатура' in ads_df.columns
                                has_ads = 'ads' in ads_df.columns
                                
                                if has_nomenclature and has_ads:
                                    zero_ads_count = (ads_df['ads'] == 0).sum()
                                    positive_ads_count = (ads_df['ads'] > 0).sum()
                                    
                                    ads_data[branch_name] = ads_df
                                    ads_count += len(ads_df)
                                    st.write(f"  ✓ {filename} → {branch_name}: {len(ads_df)} товаров (ADS>0: {positive_ads_count}, ADS=0: {zero_ads_count})")
                                else:
                                    st.warning(f"  ⚠️ {filename}: отсутствуют стандартные колонки")
                                    
                                    # Ищем правильные колонки по содержимому
                                    ads_df_fixed = ads_df.copy()
                                    
                                    # Находим колонку с названиями товаров
                                    if 'Наименование' in ads_df.columns:
                                        ads_df_fixed = ads_df_fixed.rename(columns={'Наименование': 'номенклатура'})
                                    
                                    # Находим колонку с ценами
                                    if 'Посл. закупка' in ads_df.columns:
                                        ads_df_fixed = ads_df_fixed.rename(columns={'Посл. закупка': 'last_purchase_price'})
                                    
                                    # Для ADS нужно рассчитать из продаж (колонки 13-28 примерно)
                                    # Ищем колонки с числовыми данными для расчета ADS
                                    numeric_cols = []
                                    for col in ads_df.columns:
                                        if 'Unnamed:' in col and ads_df[col].dtype in ['float64', 'int64']:
                                            numeric_cols.append(col)
                                    
                                    if len(numeric_cols) >= 12:  # Если есть достаточно колонок для расчета
                                        # Берем колонки с продажами (примерно 13-28)
                                        sales_cols = numeric_cols[12:28] if len(numeric_cols) >= 28 else numeric_cols[12:]
                                        
                                        # Рассчитываем ADS как среднее / 30
                                        ads_df_fixed['ads'] = ads_df[sales_cols].mean(axis=1) / 30
                                        
                                        # Проверяем результат
                                        if 'номенклатура' in ads_df_fixed.columns and 'ads' in ads_df_fixed.columns:
                                            zero_ads_count = (ads_df_fixed['ads'] == 0).sum()
                                            positive_ads_count = (ads_df_fixed['ads'] > 0).sum()
                                            
                                            ads_data[branch_name] = ads_df_fixed
                                            ads_count += len(ads_df_fixed)
                                            st.write(f"  ✓ {filename} → {branch_name} (рассчитан ADS): {len(ads_df_fixed)} товаров (ADS>0: {positive_ads_count}, ADS=0: {zero_ads_count})")
                                        else:
                                            st.error(f"  ❌ {filename}: не удалось подготовить данные")
                                    else:
                                        st.error(f"  ❌ {filename}: недостаточно числовых колонок для расчета ADS")
                    
                    if ads_data:
                        ads_available = True
                        st.success(f"✅ Загружены ADS данные по филиалам из отдельных результатов: {list(ads_data.keys())}")
                    else:
                        st.error("❌ Не удалось извлечь данные по филиалам")
            else:
                st.warning("⚠️ Множественные файлы есть, но данные не в calculated_ads")
    
    
    # Если нет множественных файлов, проверяем обычный ADS
    if not ads_available and hasattr(system, 'calculated_ads') and system.calculated_ads is not None:
        if not system.calculated_ads.empty:
            ads_count = len(system.calculated_ads)
            ads_available = True
            ads_data = system.calculated_ads
            st.info("📊 Используется общий ADS для всех складов")
    
    # Статус панель
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Статус ADS", "✅ Рассчитан" if ads_available else "❌ Не рассчитан")
    with col2:
        st.metric("Товаров с ADS", f"{ads_count:,}")
    with col3:
        st.metric("Складов в системе", "11")
    
    if not ads_available:
        st.warning("⚠️ ADS не рассчитан. Для полноценного анализа сначала рассчитайте ADS в разделе '📊 ADS расчет'.")
    
    # Проверяем наличие данных о подкатегориях
    subcategory_data = None
    if hasattr(system, 'abc_data') and system.abc_data is not None:
        subcategory_data = system.abc_data
        st.info(f"📋 Найдены данные о подкатегориях: {len(subcategory_data)} товаров")
    else:
        st.warning("⚠️ Данные о подкатегориях не найдены. Автозаполнение ADS=0 не будет работать.")
    
    # Параметры анализа
    with st.expander("⚙️ Параметры анализа", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            min_days = st.number_input("MIN дней запаса:", min_value=5, max_value=60, value=15)
        with col2:
            max_days = st.number_input("MAX дней запаса:", min_value=20, max_value=120, value=45)
    
    # Загрузка файла
    st.subheader("📂 Загрузка файла остатков")
    
    remains_file = st.file_uploader(
        "Выберите файл остатков:",
        type=['xlsx', 'xls'],
        help="Excel файл с остатками. Строка 7 = заголовки, строки 10+ = данные"
    )
    
    # Анализ
    if remains_file:
        if st.button("🚀 Запустить анализ", type="primary"):
            with st.spinner("Выполняем анализ..."):
                
                # Читаем файл остатков
                remains_df = system.warehouse_analyzer.read_remains_file(remains_file)
                
                if remains_df is not None:
                    # Выполняем анализ с данными о подкатегориях
                    results = system.warehouse_analyzer.analyze_warehouses(
                        remains_df, ads_data, subcategory_data, min_days, max_days
                    )
                    
                    if results:
                        # Отображаем результаты
                        system.warehouse_analyzer.display_analysis_results(results)
                        
                        # Сохраняем результаты
                        system._last_warehouse_analysis = results
                        
                        st.success(f"✅ Анализ завершен! Проанализировано {len(results)} товаров.")
                    else:
                        st.error("❌ Не удалось выполнить анализ")
                else:
                    st.error("❌ Не удалось прочитать файл остатков")
    else:
        st.info("📁 Загрузите файл остатков для начала анализа")


def add_warehouse_analysis_to_system(system):
    """Добавляет анализ складов в систему"""
    # Всегда переинициализируем анализатор
    system.warehouse_analyzer = WarehouseAnalyzer()
    
    # Применяем исправление для загрузки цен из ADS
    try:
        from ads_price_fix import fix_ads_loading_with_prices
        fix_ads_loading_with_prices(system)
        print("✅ Применено исправление загрузки цен из ADS")
    except ImportError:
        print("⚠️ ads_price_fix не найден - цены могут не загружаться")


if __name__ == "__main__":
    print("🏭 Система анализа складов с исправленным маппингом загружена")