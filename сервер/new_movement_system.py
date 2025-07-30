#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
НОВАЯ СИСТЕМА РЕКОМЕНДАЦИЙ ПО ПЕРЕМЕЩЕНИЯМ ТОВАРОВ
Полная переработка с учетом оборачиваемости, ADS и иерархии складов
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class NewMovementSystem:
    """Новая система рекомендаций по перемещениям товаров"""
    
    def __init__(self):
        self.sales_data_by_branch = {}
        self.stock_data = None
        self.ads_by_product = {}
        self.turnover_analysis = {}
        self.recommendations = []
        
        # Иерархия складов согласно ПРАВИЛЬНОЙ структуре организации
        self.warehouse_hierarchy = {
            # ГЛАВНЫЙ ХАБ в г.Алматы - пополняет все склады второго уровня
            'База Склад Фурнитура Комплект': {
                'type': 'hub',
                'level': 1,
                'city': 'Алматы',
                'parent': None,
                'children': [
                    'Казыбаева Склад Фурнитура TRADE',  # склад 2-го уровня
                    'склад фурнитура № 1',              # склад 2-го уровня
                    '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',  # склад 2-го уровня
                    'Барыс Склад Фурнитура TRADE',      # магазин напрямую от хаба
                    'АО Склад Фурнитура TRADE'          # магазин напрямую от хаба
                ],
                'ads_multiplier': 1.5,
                'min_days': 45,
                'max_days': 90
            },
            
            # === СКЛАДЫ ВТОРОГО УРОВНЯ (питаются от хаба) ===
            
            # 1 филиал: Казыбаева (г.Алматы) - склад второго уровня
            'Казыбаева Склад Фурнитура TRADE': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'children': ['ТД Казыбаева ФУРНИТУРА магазин'],  # пополняет магазин
                'ads_multiplier': 1.2,
                'min_days': 20,
                'max_days': 45
            },
            
            # 4 филиал: г.Астана - склад второго уровня
            'склад фурнитура № 1': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Астана',
                'parent': 'База Склад Фурнитура Комплект',
                'children': ['Магазин фурнитуры'],  # пополняет магазин в Астане
                'ads_multiplier': 1.2,
                'min_days': 20,
                'max_days': 45
            },
            
            # 5 филиал: Шымкент - склад второго уровня
            '4 Склад фурнитуры АЗМ Шымкент "Овощная база"': {
                'type': 'warehouse',
                'level': 2,
                'city': 'Шымкент',
                'parent': 'База Склад Фурнитура Комплект',
                'children': ['6 Склад фурнитуры "Овощная база" Магазин'],  # пополняет магазин в Шымкенте
                'ads_multiplier': 1.2,
                'min_days': 20,
                'max_days': 45,
                'exclude_categories': True  # НЕ считаем категории для Шымкента
            },
            
            # === МАГАЗИНЫ НАПРЯМУЮ ОТ ХАБА ===
            
            # 2 филиал: Барыс (нет склада) - питается напрямую от хаба
            'Барыс Склад Фурнитура TRADE': {
                'type': 'store',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'children': [],
                'ads_multiplier': 1.0,
                'min_days': 15,
                'max_days': 35
            },
            
            # 3 филиал: Алтын Орда (нет склада) - питается напрямую от хаба
            'АО Склад Фурнитура TRADE': {
                'type': 'store',
                'level': 2,
                'city': 'Алматы',
                'parent': 'База Склад Фурнитура Комплект',
                'children': [],
                'ads_multiplier': 1.0,
                'min_days': 15,
                'max_days': 35,
                'exclude_categories': True  # НЕ считаем категории для АО
            },
            
            # === МАГАЗИНЫ ТРЕТЬЕГО УРОВНЯ (питаются от складов 2-го уровня) ===
            
            # 1 филиал: магазин Казыбаева (г.Алматы)
            'ТД Казыбаева ФУРНИТУРА магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Алматы',
                'parent': 'Казыбаева Склад Фурнитура TRADE',
                'children': [],
                'ads_multiplier': 1.0,
                'min_days': 10,
                'max_days': 25
            },
            
            # 4 филиал: магазин г.Астана
            'Магазин фурнитуры': {
                'type': 'store',
                'level': 3,
                'city': 'Астана',
                'parent': 'склад фурнитура № 1',
                'children': [],
                'ads_multiplier': 1.0,
                'min_days': 10,
                'max_days': 25
            },
            
            # 5 филиал: магазин г.Шымкент
            '6 Склад фурнитуры "Овощная база" Магазин': {
                'type': 'store',
                'level': 3,
                'city': 'Шымкент',
                'parent': '4 Склад фурнитуры АЗМ Шымкент "Овощная база"',
                'children': [],
                'ads_multiplier': 1.0,
                'min_days': 10,
                'max_days': 25,
                'exclude_categories': True  # НЕ считаем категории для Шымкента
            }
        }
    
    def load_sales_files(self, sales_files_dict):
        """Загрузка файлов продаж по филиалам для расчета ADS и оборачиваемости"""
        
        st.info("🔄 Обработка файлов продаж для расчета оборачиваемости...")
        
        all_sales_data = {}
        
        for branch_file_name, file_content in sales_files_dict.items():
            
            # Определяем филиал по имени файла
            branch_name = self._extract_branch_from_filename(branch_file_name)
            
            st.write(f"📁 Обработка: {branch_file_name} → {branch_name}")
            
            try:
                # Читаем Excel файл без заголовков
                df = pd.read_excel(file_content, header=None)
                
                st.write(f"📊 Размер файла: {df.shape[0]} строк x {df.shape[1]} колонок")
                
                # Извлекаем период из строки 4 (индекс 3)
                period_info = self._extract_period_from_file(df)
                
                # Ищем строку 9 (индекс 8) с заголовками
                if len(df) <= 8:
                    st.error(f"❌ Файл слишком мал для анализа (менее 9 строк): {branch_file_name}")
                    continue
                
                # Проверяем строку 9 на наличие ключевых заголовков
                row_9 = df.iloc[8]  # Строка 9 (индекс 8)
                headers_found = self._validate_headers_row_9(row_9)
                
                if not headers_found['valid']:
                    st.error(f"❌ Строка 9 не содержит ожидаемых заголовков в {branch_file_name}")
                    continue
                
                # Устанавливаем заголовки из строки 9
                df.columns = [str(h).strip() if pd.notna(h) else f"Col_{i}" for i, h in enumerate(row_9)]
                df = df.iloc[9:].reset_index(drop=True)  # Данные начинаются с строки 10
                
                # Находим колонки
                columns_map = self._find_columns_in_headers(df.columns)
                
                if not columns_map['nomenclature']:
                    st.error(f"❌ Не найдена колонка 'Номенклатура' в {branch_file_name}")
                    continue
                
                if not (columns_map['quantity'] or columns_map['revenue']):
                    st.error(f"❌ Не найдены колонки продаж в {branch_file_name}")
                    continue
                
                
                # Ищем итоговую строку в файле для сравнения
                file_total = self._find_total_in_file(df, columns_map)
                
                # Анализируем иерархию товаров и извлекаем только конечные товары
                branch_data = self._extract_products_with_hierarchy(df, columns_map, period_info['days'], file_total)
                
                if branch_data:
                    all_sales_data[branch_name] = pd.DataFrame(branch_data)
                    
                    # Проверяем расчеты против итога в файле
                    our_total = sum(item['revenue'] for item in branch_data)
                    avg_ads = sum(item['ads'] for item in branch_data) / len(branch_data) if branch_data else 0
                    
                    if file_total and abs(our_total - file_total) > file_total * 0.01:  # Расхождение больше 1%
                        st.error(f"❌ {branch_name}: РАСХОЖДЕНИЕ! Наш расчет: {our_total:,.0f} vs Файл: {file_total:,.0f}")
                        st.error("🔍 Детальный анализ включен - смотрите лог выше")
                    else:
                        st.success(f"✅ {branch_name}: {len(branch_data)} товаров | Выручка: {our_total:,.0f} | Файл: {file_total:,.0f} | ADS: {avg_ads:.0f}")
                else:
                    st.warning(f"⚠️ {branch_name}: нет товаров после анализа")
                    
            except Exception as e:
                st.error(f"❌ Ошибка обработки {branch_file_name}: {str(e)}")
                continue
        
        self.sales_data_by_branch = all_sales_data
        
        # Агрегируем ADS по товарам
        self._aggregate_ads_by_product()
        
        return len(all_sales_data) > 0
    
    def _find_total_in_file(self, df, columns_map):
        """Поиск итоговой строки в файле"""
        
        if not columns_map['revenue']:
            return None
        
        # Ищем строки с "итого", "всего", "total" в последних 10 строках
        for idx in range(max(0, len(df) - 10), len(df)):
            nomenclature = str(df.iloc[idx][columns_map['nomenclature']])
            
            if any(keyword in nomenclature.lower() for keyword in ['итого', 'всего', 'total']):
                total_value = self._safe_numeric(df.iloc[idx][columns_map['revenue']])
                if total_value > 0:
                    st.info(f"📊 Найден итог в файле: '{nomenclature}' = {total_value:,.0f}")
                    return total_value
        
        return None
    
    def _extract_period_from_file(self, df):
        """Извлечение периода из строки 4 файла"""
        
        try:
            if len(df) > 3:
                row_4 = df.iloc[3]  # Строка 4 (индекс 3)
                
                # Ищем текст с периодом
                for cell in row_4:
                    if pd.notna(cell):
                        cell_str = str(cell).lower()
                        if 'период' in cell_str and '-' in cell_str:
                            # Извлекаем даты
                            import re
                            date_pattern = r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})'
                            match = re.search(date_pattern, str(cell))
                            
                            if match:
                                start_date_str = match.group(1)
                                end_date_str = match.group(2)
                                
                                # Вычисляем количество дней
                                from datetime import datetime
                                start_date = datetime.strptime(start_date_str, '%d.%m.%Y')
                                end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
                                days = (end_date - start_date).days + 1
                                
                                return {
                                    'period_str': f"{start_date_str} - {end_date_str}",
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'days': days
                                }
            
            # Если не найден, используем год (365 дней)
            return {
                'period_str': 'Не найден (принят год)',
                'start_date': None,
                'end_date': None,
                'days': 365
            }
            
        except Exception as e:
            st.warning(f"⚠️ Ошибка извлечения периода: {e}")
            return {
                'period_str': 'Ошибка извлечения (принят год)',
                'start_date': None,
                'end_date': None,
                'days': 365
            }
    
    def _validate_headers_row_9(self, row_9):
        """Проверка наличия ожидаемых заголовков в строке 9"""
        
        expected_headers = ['номенклатура', 'количество', 'выручка', 'себестоимость', 'валовая', 'рентабельность']
        found_headers = []
        
        for cell in row_9:
            if pd.notna(cell):
                cell_str = str(cell).lower().strip()
                for expected in expected_headers:
                    if expected in cell_str:
                        found_headers.append(expected)
        
        # Требуем минимум номенклатуру и один показатель продаж
        has_nomenclature = 'номенклатура' in found_headers
        has_sales_data = any(header in found_headers for header in ['количество', 'выручка'])
        
        return {
            'valid': has_nomenclature and has_sales_data,
            'found_headers': found_headers,
            'has_nomenclature': has_nomenclature,
            'has_sales_data': has_sales_data
        }
    
    def _find_columns_in_headers(self, columns):
        """Поиск нужных колонок в заголовках"""
        
        columns_map = {
            'nomenclature': None,
            'quantity': None,
            'revenue': None,
            'cost': None,
            'profit': None,
            'profitability': None
        }
        
        for col in columns:
            if pd.notna(col):
                col_str = str(col).lower().strip()
                
                if 'номенклатура' in col_str:
                    columns_map['nomenclature'] = col
                elif 'количество' in col_str:
                    columns_map['quantity'] = col
                elif 'выручка' in col_str:
                    columns_map['revenue'] = col
                elif 'себестоимость' in col_str:
                    columns_map['cost'] = col
                elif 'валовая' in col_str or 'прибыль' in col_str:
                    columns_map['profit'] = col
                elif 'рентабельность' in col_str or '%' in col_str:
                    columns_map['profitability'] = col
        
        return columns_map
    
    def _extract_products_with_hierarchy(self, df, columns_map, period_days, file_total=None):
        """Извлечение товаров с учетом иерархии категорий"""
        
        products = []
        detailed_log = []  # Для детального анализа
        
        # Первый проход - собираем все товары
        for idx, row in df.iterrows():
            nomenclature_raw = str(row[columns_map['nomenclature']])
            
            # Пропускаем пустые строки
            if pd.isna(row[columns_map['nomenclature']]) or nomenclature_raw.strip() == '' or nomenclature_raw == 'nan':
                continue
            
                # Анализ отступов
            leading_spaces = len(nomenclature_raw) - len(nomenclature_raw.lstrip(' \t'))
            clean_name = nomenclature_raw.strip()
            
            # Получаем данные по колонкам
            quantity = self._safe_numeric(row[columns_map['quantity']]) if columns_map['quantity'] else 0
            revenue = self._safe_numeric(row[columns_map['revenue']]) if columns_map['revenue'] else 0
            cost = self._safe_numeric(row[columns_map['cost']]) if columns_map['cost'] else 0
            
            # ДЕТАЛЬНАЯ КЛАССИФИКАЦИЯ
            classification = self._detailed_product_classification(clean_name, quantity, revenue, cost, leading_spaces)
            
            # Определяем уровень иерархии
            hierarchy_level = self._determine_hierarchy_level(leading_spaces, clean_name, classification)
            
            # Принимаем решение - добавляем только товары, ИСКЛЮЧАЕМ категории
            # Особенно исключаем категории с нулевыми отступами для складов фурнитуры
            should_add_product = False
            
            if classification['type'] == 'ТОВАР':
                # Обычные товары добавляем
                should_add_product = True
            elif classification['type'] == 'КАТЕГОРИЯ' and leading_spaces == 0:
                # Категории с нулевыми отступами ТОЧНО НЕ добавляем
                should_add_product = False
            else:
                # Остальное - по классификации
                should_add_product = (classification['type'] == 'ТОВАР')
            
            if should_add_product:
                # Это товар - добавляем
                total_sales = revenue if revenue > 0 else (quantity * 100 if quantity > 0 else 0)
                ads_value = total_sales / period_days if period_days > 0 else 0
                
                products.append({
                    'product_name': clean_name,
                    'total_sales': total_sales,
                    'ads': ads_value,
                    'quantity': quantity,
                    'revenue': revenue,
                    'cost': cost,
                    'hierarchy_level': hierarchy_level,
                    'leading_spaces': leading_spaces,
                    'classification': classification
                })
                
                # Логируем все товары для детального анализа С ПОДРОБНОСТЯМИ
                detailed_log.append({
                    'row': idx + 10,
                    'name': clean_name,
                    'revenue': revenue,
                    'spaces': leading_spaces,
                    'type': 'ТОВАР',
                    'confidence': classification['confidence'],
                    'reasons': classification.get('reasons', []),
                    'added': True
                })
            
            else:
                # Логируем пропущенные элементы С ПОДРОБНОЙ ИНФОРМАЦИЕЙ 
                detailed_log.append({
                    'row': idx + 10,
                    'name': clean_name,
                    'revenue': revenue,
                    'spaces': leading_spaces,
                    'type': classification['type'],
                    'confidence': classification['confidence'],
                    'reasons': classification.get('reasons', []),
                    'added': False
                })
        
        # Проверяем, нужен ли детальный анализ
        our_total = sum(item['revenue'] for item in products)
        
        if file_total and abs(our_total - file_total) > file_total * 0.01:
            skipped_total = sum(log['revenue'] for log in detailed_log if not log['added'] and log['revenue'] > 0)
            
            st.error(f"🚨 КРИТИЧЕСКОЕ РАСХОЖДЕНИЕ!")
            st.error(f"📊 Наш расчет: {our_total:,.0f}")
            st.error(f"📊 Файл показывает: {file_total:,.0f}")
            st.error(f"📊 Расхождение: {abs(our_total - file_total):,.0f}")
            st.error(f"📊 Пропущено элементов с выручкой: {skipped_total:,.0f}")
            
            st.error("📋 ЧТО МЫ СЧИТАЕМ КАК ТОВАРЫ (первые 20):")
            
            added_count = 0
            for log_entry in detailed_log:
                if log_entry['added'] and added_count < 20:
                    st.write(f"✅ Строка {log_entry['row']:3d}: {log_entry['name'][:40]:<40} | {log_entry['revenue']:>12,.0f} | Отступ: {log_entry['spaces']:2d}")
                    added_count += 1
            
            if added_count >= 20:
                remaining = sum(1 for log in detailed_log if log['added']) - 20
                st.write(f"... и еще {remaining} товаров")
            
            st.error("📋 ВСЕ ЧТО МЫ ПРОПУСКАЕМ (в порядке строк файла):")
            skipped_items = [log for log in detailed_log if not log['added'] and log['revenue'] > 0]
            
            # Сортируем по НОМЕРУ СТРОКИ (как в файле)
            skipped_items.sort(key=lambda x: x['row'])
            
            st.error(f"🔍 Найдено {len(skipped_items)} пропущенных элементов с выручкой:")
            
            # Группируем по типам для анализа
            by_type = {}
            for item in skipped_items:
                item_type = item['type']
                if item_type not in by_type:
                    by_type[item_type] = []
                by_type[item_type].append(item)
            
            # Сначала показываем общую статистику по типам
            st.error("📊 СТАТИСТИКА ПО ТИПАМ:")
            for item_type, items in by_type.items():
                st.error(f"   {item_type}: {len(items)} элементов, общая выручка: {sum(item['revenue'] for item in items):,.0f}")
            
            st.error("📋 ДЕТАЛЬНЫЙ СПИСОК ПО ПОРЯДКУ СТРОК В ФАЙЛЕ:")
            
            # Показываем ВСЕ элементы в порядке строк файла
            for log_entry in skipped_items:
                confidence = log_entry.get('confidence', 'N/A')
                reasons = log_entry.get('reasons', [])
                reasons_str = '; '.join(reasons[:2]) if reasons else 'Нет причин'
                
                st.write(f"❌ Строка {log_entry['row']:3d}: **{log_entry['name'][:50]}** | {log_entry['revenue']:>12,.0f} | Отступ: {log_entry['spaces']:2d} | {log_entry['type']} | Уверенность: {confidence}")
                if reasons:
                    st.write(f"   🔍 Причины: {reasons_str}")
        
        return products
    
    def _is_category_by_name_logic(self, name_lower):
        """Определение категории по логике названия - категории это ОБЩИЕ названия без детализации"""
        
        # ПОЛНЫЙ СПИСОК категорий для исключения (включая страны и итоги)
        exact_categories = [
            # Кромки (все варианты со странами)
            'кромка пвх', 'кромка пвх китай', 'кромка пвх россия', 'кромка пвх турция',
            'кромка', 'кромочные материалы',
            # Размеры ПВХ без детализации (включая страны)
            '19*0,8мм пвх', '19*0,8мм пвх китай', '19*0,8мм пвх россия', '19*0,8мм пвх турция',
            '19*1,5мм пвх', '19*1,5мм пвх китай', '19*1,5мм пвх россия', '19*1,5мм пвх турция',
            '19*2мм пвх', '19*2мм пвх китай', '19*2мм пвх россия', '19*2мм пвх турция',
            '22*1мм пвх', '22*1мм пвх китай', '22*1мм пвх россия', '22*1мм пвх турция',
            '22*2мм пвх', '22*2мм пвх китай', '22*2мм пвх россия', '22*2мм пвх турция',
            '43*2мм пвх', '28*1,5мм пвх', '16*1,5мм пвх',
            # Плинтусы общие
            'плинтус пластиковый 3м', 'плинтус пластиковый', 'плинтус',
            'плинтус напольный', 'плинтусы',
            # Посудосушители
            'посудосушители', 'посудосушители сетчатые', 
            'посудосушители сетчатые полимерное покрытие',
            # Общие категории
            'фурнитура', 'материалы', 'аксессуары', 'комплектующие', 'товары',
            'мебельная фурнитура', 'кромочные материалы',
            'столешницы', 'минеральные плиты', 'древесноволокнистые плиты',
            # Метизы и крепеж
            'метизы', 'крепеж', 'саморезы', 'винты', 'болты', 'гайки',
            # Ручки и фурнитура
            'ручки', 'ручки мебельные', 'петли', 'направляющие',
            # Другие материалы
            'пластик', 'металл', 'дерево', 'стекло',
            # ИТОГОВЫЕ СТРОКИ (ОБЯЗАТЕЛЬНО ИСКЛЮЧАТЬ!)
            'итого', 'всего', 'total', 'общий итог', 'сумма', 'результат'
        ]
        
        # Проверяем точные совпадения
        for category in exact_categories:
            if name_lower == category:
                return True
        
        # Логика: если название содержит базовые характеристики БЕЗ детализации
        # Например: "19*1,5мм ПВХ" - категория, "19*1,5мм ПВХ Белый AN" - товар
        
        # Паттерны категорий (короткие, общие названия)
        category_patterns = [
            # Размеры без детализации цвета/кода
            r'^\d+\*\d+[,.]?\d*мм\s+пвх$',  # 19*1,5мм ПВХ
            r'^кромка\s+пвх$',               # Кромка ПВХ
            r'^кромка\s+пвх\s+китай$',       # Кромка ПВХ Китай
            r'^плинтус\s+пластиковый\s+\d+м$', # Плинтус пластиковый 3м
            r'^посудосушители$',             # Посудосушители
            r'^посудосушители\s+сетчатые',   # Посудосушители сетчатые...
        ]
        
        import re
        for pattern in category_patterns:
            if re.match(pattern, name_lower):
                return True
        
        # Дополнительная логика: если название очень короткое и общее
        if len(name_lower) <= 15 and any(word in name_lower for word in ['пвх', 'плинтус', 'фурнитура']):
            # Но НЕ содержит детализации (цвета, коды)
            detail_indicators = ['белый', 'черный', 'коричневый', 'an', 'ap', 'tp', 'k0', 'pr']
            if not any(detail in name_lower for detail in detail_indicators):
                return True
        
        return False
    
    def _detailed_product_classification(self, name, quantity, revenue, cost, leading_spaces):
        """ДЕТАЛЬНАЯ классификация элемента на товар/категорию/подкатегорию"""
        
        # ВАЖНО: В файлах продаж категории тоже имеют суммарную выручку!
        # Нужно различать по структуре названия, а не только по наличию продаж
        
        reasons = []
        confidence = 0
        
        # 1. АНАЛИЗ НАЗВАНИЯ - ЭТО ГЛАВНОЕ!
        name_lower = name.lower()
        
        # НОВАЯ ЛОГИКА: Категории vs Товары НЕ зависят от отступов!
        # Категории - это ОБЩИЕ названия (19*1,5мм ПВХ)
        # Товары - это КОНКРЕТНЫЕ спецификации (19*1,5мм ПВХ Белый AN)
        
        # Проверяем - это товар или категория по ЛОГИКЕ НАЗВАНИЯ
        is_likely_category = self._is_category_by_name_logic(name_lower)
        
        if is_likely_category:
            confidence -= 100  # Максимальное исключение категорий
            reasons.append(f"Определена как КАТЕГОРИЯ по логике названия")
        
        # Размеры и единицы измерения - явный признак товара
        size_indicators = ['мм', 'см', 'м', 'кг', 'г', 'шт', 'л', 'кв.м', 'п.м']
        found_sizes = [ind for ind in size_indicators if ind in name_lower]
        if found_sizes and not is_likely_category:
            confidence += 40
            reasons.append(f"Единицы измерения: {found_sizes}")
        
        # Математические символы и размеры - явный признак товара
        math_symbols = ['*', 'x', '×', '/', '+']
        found_math = [sym for sym in math_symbols if sym in name]
        if found_math and not is_likely_category:
            confidence += 35
            reasons.append(f"Математические символы: {found_math}")
        
        # Коды товаров (AP740, AN, TP и т.д.) - явный признак товара
        import re
        # Ищем паттерны вида AP740, K001, R023 и т.п.
        code_patterns = re.findall(r'[A-Z]{1,2}\d{3,4}', name)
        if code_patterns and not is_likely_category:
            confidence += 40
            reasons.append(f"Товарные коды: {code_patterns}")
        
        # Общие коды товаров
        product_codes = ['ap', 'an', 'tp', 'pr', 'k0', 'r0']
        found_codes = [code for code in product_codes if code in name_lower]
        if found_codes and not is_likely_category:
            confidence += 20
            reasons.append(f"Коды: {found_codes}")
        
        # 2. АНАЛИЗ НА КАТЕГОРИИ - ключевые слова БЕЗ специфики
        category_keywords = [
            'фурнитура', 'материалы', 'аксессуары', 'комплектующие', 
            'кромочные', 'мебельная', 'столешниц'
        ]
        
        # Проверяем: есть ли ключевое слово категории БЕЗ дополнительной специфики
        is_pure_category = False
        for cat_keyword in category_keywords:
            if cat_keyword in name_lower:
                # Проверяем, есть ли после ключевого слова еще специфика
                remaining = name_lower.replace(cat_keyword, '').strip()
                if len(remaining) < 5 or not any(char.isdigit() for char in remaining):
                    is_pure_category = True
                    confidence -= 50
                    reasons.append(f"Чистая категория: {cat_keyword}")
                    break
        
        # 3. АНАЛИЗ ОТСТУПОВ (теперь вторичный критерий)
        if leading_spaces == 0 and (is_pure_category or is_likely_category):
            confidence -= 30
            reasons.append("Главная категория (0 отступов)")
        elif leading_spaces > 0 and leading_spaces <= 8 and not found_sizes and not found_math:
            confidence -= 20
            reasons.append(f"Подкатегория (отступы: {leading_spaces})")
        elif leading_spaces > 8:
            confidence += 20
            reasons.append(f"Товар (большие отступы: {leading_spaces})")
        
        # 4. СПЕЦИФИЧЕСКИЕ ПАТТЕРНЫ
        # Плинтус с конкретными характеристиками = товар
        if 'плинтус' in name_lower and (found_sizes or code_patterns or len(name) > 30) and not is_likely_category:
            confidence += 30
            reasons.append("Плинтус с характеристиками")
        
        # Числа в начале обычно = товар (19*0,8мм)
        if name and name[0].isdigit() and not is_likely_category:
            confidence += 25
            reasons.append("Начинается с цифры")
        
        # 5. ОКОНЧАТЕЛЬНАЯ КЛАССИФИКАЦИЯ - ГЛАВНОЕ НЕ ОТСТУПЫ, А ЛОГИКА НАЗВАНИЯ!
        if is_likely_category:
            # Определено как категория по логике названия - ИСКЛЮЧАЕМ!
            classification_type = 'КАТЕГОРИЯ'
        elif confidence >= 40:
            # Высокая уверенность в том что это товар
            classification_type = 'ТОВАР'
        elif confidence <= -40:
            # Высокая уверенность в том что это категория
            classification_type = 'КАТЕГОРИЯ'
        elif found_sizes and found_math:
            # Есть размеры И математические символы = скорее всего товар
            classification_type = 'ТОВАР'
        elif code_patterns:
            # Есть коды товаров = точно товар
            classification_type = 'ТОВАР'
        elif len(name) > 25 and any(char.isdigit() for char in name):
            # Длинное название с цифрами = скорее всего товар с характеристиками
            classification_type = 'ТОВАР'
        else:
            # В остальных случаях смотрим на отступы как дополнительный критерий
            if leading_spaces > 8:
                classification_type = 'ТОВАР'
            elif leading_spaces == 0:
                classification_type = 'КАТЕГОРИЯ'
            else:
                classification_type = 'ПОДКАТЕГОРИЯ'
        
        return {
            'type': classification_type,
            'confidence': max(0, min(100, confidence + 50)),
            'reasons': reasons,
            'name_length': len(name),
            'leading_spaces': leading_spaces,
            'has_sizes': len(found_sizes) > 0,
            'has_codes': len(code_patterns) > 0 or len(found_codes) > 0
        }
    
    def _determine_hierarchy_level(self, leading_spaces, name, classification):
        """Определение уровня иерархии элемента"""
        
        if leading_spaces == 0:
            return 1  # Главная категория
        elif leading_spaces <= 4:
            return 2  # Подкатегория 1-го уровня
        elif leading_spaces <= 8:
            return 3  # Подкатегория 2-го уровня
        elif leading_spaces <= 16:
            return 4  # Товары или подкатегории 3-го уровня
        else:
            return 5  # Глубоко вложенные товары
    
    def _is_product_not_category(self, name, row, columns_map):
        """Определение, является ли элемент товаром или категорией"""
        
        # Если есть значимые продажи - это товар
        revenue = self._safe_numeric(row[columns_map['revenue']]) if columns_map['revenue'] else 0
        quantity = self._safe_numeric(row[columns_map['quantity']]) if columns_map['quantity'] else 0
        
        # Товары имеют конкретные продажи или количество
        has_sales_data = revenue > 0 or quantity > 0
        
        # Характерные признаки товаров в названии
        product_indicators = ['мм', 'см', 'кг', 'шт', 'м', '*', 'x', '№', 'ap', 'an', 'tp']
        has_product_indicators = any(indicator in name.lower() for indicator in product_indicators)
        
        # Длинные названия с конкретными характеристиками обычно товары
        is_detailed_name = len(name) > 20 and any(char.isdigit() for char in name)
        
        # Названия категорий обычно общие и короткие
        category_keywords = ['фурнитура', 'материалы', 'аксессуары', 'комплектующие']
        is_likely_category = any(keyword in name.lower() for keyword in category_keywords) and len(name) < 30
        
        # Решение: товар, если есть продажи ИЛИ характерные признаки, НО НЕ категория
        return (has_sales_data or has_product_indicators or is_detailed_name) and not is_likely_category
    
    def _safe_numeric(self, value):
        """Безопасное преобразование в число"""
        try:
            if pd.isna(value):
                return 0
            return float(pd.to_numeric(value, errors='coerce'))
        except:
            return 0
    
    def _extract_branch_from_filename(self, filename):
        """Извлечение названия филиала из имени файла согласно структуре"""
        
        name = filename.lower()
        
        # ПОРЯДОК ВАЖЕН! Проверяем ПО ПОРЯДКУ
        
        # 1. СНАЧАЛА самые специфичные названия
        if '6_склад_фурнитуры_овощная_база_магазин' in name:
            return '6 Склад фурнитуры "Овощная база" Магазин'
        
        elif '4_склад_фурнитуры_азм_шымкент_овощная_база' in name:
            return '4 Склад фурнитуры АЗМ Шымкент "Овощная база"'
        
        # 2. Казыбаева
        elif 'тд_казыбаева_фурнитура_магазин' in name:
            return 'ТД Казыбаева ФУРНИТУРА магазин'
        elif 'казыбаева_склад_фурнитура_trade' in name:
            return 'Казыбаева Склад Фурнитура TRADE'
        
        # 3. Астана - сначала магазин!
        elif 'магазин_фурнитуры' in name:
            return 'Магазин фурнитуры'
        elif 'склад_фурнитура_№_1' in name or 'склад_фурнитура_1' in name:
            return 'склад фурнитура № 1'
        
        # 4. Магазины Без складов
        elif 'барыс_склад_фурнитура_trade' in name:
            return 'Барыс Склад Фурнитура TRADE'
        elif 'ао_склад_фурнитура_trade' in name:
            return 'АО Склад Фурнитура TRADE'
        
        # 5. Главный хаб
        elif 'база_склад_фурнитура_комплект' in name:
            return 'База Склад Фурнитура Комплект'
        
        # 6. Общие проверки (менее специфичные)
        elif 'шымкент' in name or 'овощная' in name:
            if 'магазин' in name:
                return '6 Склад фурнитуры "Овощная база" Магазин'
            else:
                return '4 Склад фурнитуры АЗМ Шымкент "Овощная база"'
        elif 'казыбаева' in name:
            if 'магазин' in name or 'тд' in name:
                return 'ТД Казыбаева ФУРНИТУРА магазин'
            else:
                return 'Казыбаева Склад Фурнитура TRADE'
        elif 'барыс' in name:
            return 'Барыс Склад Фурнитура TRADE'
        elif 'ао' in name:
            return 'АО Склад Фурнитура TRADE'
        elif 'астана' in name:
            if 'магазин' in name:
                return 'Магазин фурнитуры'
            else:
                return 'склад фурнитура № 1'
        elif 'база' in name or 'комплект' in name:
            return 'База Склад Фурнитура Комплект'
        
        # 7. Последняя попытка
        else:
            return f"Неизвестный_филиал_{filename[:20]}"
    
    def _find_nomenclature_column(self, df):
        """Поиск колонки с наименованиями товаров"""
        
        # Сначала ищем по ключевым словам
        for col in df.columns:
            col_name = str(col).lower()
            if any(keyword in col_name for keyword in ['наименование', 'номенклатура', 'товар', 'name']):
                st.info(f"🔍 Найдена колонка по ключевому слову: {repr(col)}")
                return col
        
        # Анализируем каждую колонку на предмет того, что она содержит наименования
        st.info("🔍 Анализируем колонки на предмет наименований товаров...")
        
        for i, col in enumerate(df.columns):
            st.write(f"Анализ колонки {i}: {repr(col)}")
            
            # Проверяем колонки Unnamed: X - они могут содержать данные
            if str(col).startswith('Unnamed'):
                # Для Unnamed колонок смотрим на содержимое
                sample_data = df[col].dropna().head(20)
                if len(sample_data) == 0:
                    st.write(f"  ❌ Колонка {col} пустая")
                    continue
                    
                # Проверяем, содержит ли колонка текстовые данные, похожие на наименования
                text_samples = []
                for val in sample_data:
                    str_val = str(val).strip()
                    if str_val and str_val != 'nan' and len(str_val) > 3:
                        text_samples.append(str_val)
                
                if text_samples:
                    st.write(f"  📝 Примеры из {col}: {text_samples[:3]}")
                    
                    # Проверяем признаки товарных наименований
                    has_product_signs = False
                    for sample in text_samples[:5]:
                        # Ищем характерные признаки товаров
                        if any(sign in sample.lower() for sign in ['мм', 'см', 'кг', 'шт', '*', 'x', '№']):
                            has_product_signs = True
                            break
                        # Или просто длинные названия с буквами
                        if len(sample) > 10 and any(c.isalpha() for c in sample):
                            has_product_signs = True
                            break
                    
                    if has_product_signs:
                        st.success(f"✅ Найдена колонка с наименованиями в {col}")
                        return col
                        
                st.write(f"  ❌ {col} не содержит наименований товаров")
                continue
            
            # Пропускаем явно пустые колонки
            if pd.isna(col) or str(col).strip() == '':
                st.write(f"  ❌ Пропускаем пустую колонку")
                continue
            
            # Получаем образцы данных из колонки
            sample_data = df[col].dropna().head(10)
            
            if len(sample_data) == 0:
                st.write(f"  ❌ Колонка пустая")
                continue
            
            # Анализируем содержимое
            text_items = []
            for val in sample_data:
                str_val = str(val).strip()
                if str_val and str_val != 'nan':
                    text_items.append(str_val)
            
            st.write(f"  📝 Примеры значений: {text_items[:3]}")
            
            if not text_items:
                st.write(f"  ❌ Нет валидных текстовых значений")
                continue
            
            # Проверяем признаки наименований товаров
            score = 0
            
            # 1. Проверяем, что это текстовые данные
            if df[col].dtype == 'object':
                score += 3
                st.write(f"  ✅ Текстовый тип данных (+3)")
            
            # 2. Проверяем длину значений (наименования обычно длинные)
            avg_length = sum(len(item) for item in text_items) / len(text_items)
            if avg_length > 10:
                score += 2
                st.write(f"  ✅ Средняя длина {avg_length:.1f} символов (+2)")
            
            # 3. Проверяем уникальность (должно быть много разных товаров)
            unique_ratio = len(set(text_items)) / len(text_items)
            if unique_ratio > 0.8:
                score += 2
                st.write(f"  ✅ Высокая уникальность {unique_ratio:.2f} (+2)")
            
            # 4. Проверяем, что это не числа
            non_numeric_count = 0
            for item in text_items:
                # Убираем пробелы и проверяем, что это не чистое число
                clean_item = item.replace(' ', '').replace(',', '.').replace('-', '')
                try:
                    float(clean_item)
                except:
                    non_numeric_count += 1
            
            if non_numeric_count > len(text_items) * 0.7:
                score += 2
                st.write(f"  ✅ Не числовые данные {non_numeric_count}/{len(text_items)} (+2)")
            
            # 5. Проверяем наличие характерных слов товаров
            product_keywords = ['мм', 'см', 'кг', 'шт', 'м', 'л', 'г']
            keyword_matches = sum(1 for item in text_items for keyword in product_keywords if keyword.lower() in item.lower())
            if keyword_matches > 0:
                score += 1
                st.write(f"  ✅ Найдены товарные ключевые слова ({keyword_matches}) (+1)")
            
            st.write(f"  📊 Общий рейтинг: {score}")
            
            # Если рейтинг достаточно высокий, считаем это колонкой с наименованиями
            if score >= 6:
                st.success(f"✅ Найдена колонка с наименованиями: {repr(col)} (рейтинг {score})")
                return col
        
        # Если автоматический поиск не сработал, берем первую непустую колонку
        st.warning("⚠️ Автоматический поиск не дал результата, используем первую колонку")
        
        for col in df.columns:
            if not pd.isna(col) and str(col).strip() and not str(col).startswith('Unnamed'):
                st.warning(f"⚠️ Принудительно используем колонку: {repr(col)}")
                return col
        
        # В крайнем случае - первая колонка
        return df.columns[0] if len(df.columns) > 0 else None
    
    def _find_sales_columns(self, df):
        """Поиск колонок с данными продаж"""
        
        sales_cols = []
        
        st.write("🔍 Анализ колонок на предмет данных продаж:")
        st.write(f"Всего колонок в файле: {len(df.columns)}")
        
        for i, col in enumerate(df.columns):
            col_name = str(col).lower()
            st.write(f"Колонка {i}: {repr(col)}")
            
            # Пропускаем колонку с наименованиями
            if 'unnamed: 0' in col_name or i == 0:
                st.write(f"  ❌ Пропускаем колонку с наименованиями")
                continue
            
            # Ищем колонки с ключевыми словами
            if any(keyword in col_name for keyword in ['количество', 'кол-во', 'продано', 'qty', 'sales', 'сумма', 'итого']):
                sales_cols.append(col)
                st.write(f"  ✅ Найдена по ключевому слову")
                continue
            
            # Проверяем числовые колонки
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                non_null_count = numeric_data.notna().sum()
                total_sum = numeric_data.sum()
                
                st.write(f"  📊 Числовых значений: {non_null_count}, Сумма: {total_sum}")
                
                if non_null_count > 0 and total_sum > 0:
                    # Проверяем, что это не индексы или коды
                    max_value = numeric_data.max()
                    min_value = numeric_data.min()
                    
                    st.write(f"  📈 Диапазон: {min_value} - {max_value}")
                    
                    # Если значения выглядят как продажи (не слишком маленькие и не ID)
                    if max_value > 1 and (max_value < 999999 or total_sum > 100):
                        sales_cols.append(col)
                        st.write(f"  ✅ Добавлена как колонка продаж")
                    else:
                        st.write(f"  ❌ Не похоже на продажи")
                else:
                    st.write(f"  ❌ Нет положительных значений")
                    
            except Exception as e:
                st.write(f"  ❌ Ошибка анализа: {e}")
        
        st.write(f"📋 Итого найдено колонок с продажами: {len(sales_cols)}")
        if sales_cols:
            st.write(f"Колонки: {[str(col) for col in sales_cols]}")
        
        return sales_cols
    
    def _aggregate_ads_by_product(self):
        """Агрегация ADS по товарам из всех филиалов"""
        
        all_products = {}
        
        for branch_name, branch_df in self.sales_data_by_branch.items():
            for _, row in branch_df.iterrows():
                product_name = row['product_name']
                ads_value = row['ads']
                
                if product_name not in all_products:
                    all_products[product_name] = {
                        'total_ads': 0,
                        'branches': [],
                        'total_sales': 0
                    }
                
                all_products[product_name]['total_ads'] += ads_value
                all_products[product_name]['branches'].append(branch_name)
                all_products[product_name]['total_sales'] += row['total_sales']
        
        self.ads_by_product = all_products
        
        st.success(f"✅ Агрегированы данные по {len(all_products)} товарам")
    
    def load_stock_file(self, stock_file):
        """Загрузка файла остатков с учетом специфики формата"""
        
        try:
            # Читаем файл
            df = pd.read_excel(stock_file)
            
            st.info(f"📊 Загружен файл размером {df.shape[0]} строк x {df.shape[1]} колонок")
            
            # Отладочная информация о структуре файла
            with st.expander("🔍 Отладочная информация о файле"):
                st.write("**Первые 15 строк файла:**")
                for i in range(min(15, len(df))):
                    row_values = [str(val)[:50] for val in df.iloc[i].values]
                    st.write(f"Строка {i}: {row_values}")
                
                st.write("\n**Исходные заголовки колонок:**")
                for i, col in enumerate(df.columns):
                    st.write(f"Колонка {i}: {repr(col)}")
            
            # Проверяем специфику файла "остатки на 08.07.2025.xlsx"
            # Согласно анализу: данные начинаются со строки 10 (индекс 9)
            
            # Ищем строку с заголовками складов
            header_row_idx = None
            for i in range(min(15, len(df))):
                row_values = [str(val) for val in df.iloc[i].values if pd.notna(val)]
                row_text = ' '.join(row_values).lower()
                
                st.write(f"Анализ строки {i}: {row_text[:100]}...")
                
                # Ищем характерные названия складов в заголовках
                warehouse_keywords = ['склад', 'магазин', 'база', 'trade']
                keyword_count = sum(1 for keyword in warehouse_keywords if keyword in row_text)
                
                if keyword_count >= 2:  # Снижаем порог
                    header_row_idx = i
                    st.info(f"🔍 Найдена строка с заголовками складов: строка {i+1} (найдено {keyword_count} ключевых слов)")
                    break
            
            if header_row_idx is not None:
                # Используем найденную строку как заголовки
                new_headers = df.iloc[header_row_idx].values
                df.columns = [str(h).strip() if pd.notna(h) else f"Col_{i}" for i, h in enumerate(new_headers)]
                
                # Берем данные начиная с следующей строки
                df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                
                st.success(f"✅ Обновлены заголовки и данные. Осталось {len(df)} строк данных")
                
                # Показываем новые заголовки
                st.write("**Новые заголовки:**")
                for i, col in enumerate(df.columns):
                    st.write(f"  {i}: {repr(col)}")
                    
            else:
                # Стандартная обработка - пропускаем первые несколько строк
                st.warning("⚠️ Не найдена строка с заголовками, пропускаем первые 6 строк")
                
                # Согласно анализу, заголовки на строке 7 (индекс 6)
                if len(df) > 6:
                    new_headers = df.iloc[6].values
                    df.columns = [str(h).strip() if pd.notna(h) else f"Col_{i}" for i, h in enumerate(new_headers)]
                    df = df.iloc[7:].reset_index(drop=True)  # Данные с строки 8
                    st.success("✅ Использованы заголовки со строки 7, данные с строки 8")
                else:
                    df.columns = df.columns.str.strip()
            
            # Показываем итоговые заголовки
            st.write("**Итоговые заголовки колонок:**")
            for i, col in enumerate(df.columns):
                st.write(f"  {i}: {repr(col)}")
            
            # Ищем колонку с наименованиями
            name_col = self._find_nomenclature_column(df)
            if not name_col:
                st.error("❌ Не найдена колонка с наименованиями в файле остатков")
                
                # Дополнительная отладка
                st.write("**Анализ первых 5 колонок на предмет наименований:**")
                for i in range(min(5, len(df.columns))):
                    col = df.columns[i]
                    sample_values = df[col].dropna().head(5).tolist()
                    st.write(f"Колонка {i} ({repr(col)}): {sample_values}")
                
                # Пробуем первую колонку принудительно
                if len(df.columns) > 0:
                    name_col = df.columns[0]
                    st.warning(f"⚠️ Принудительно используем первую колонку: {repr(name_col)}")
                else:
                    st.error("❌ Нет доступных колонок")
                    return False
            
            st.success(f"✅ Найдена колонка с наименованиями: {repr(name_col)}")
            
            # Находим колонки со складами
            stock_cols = []
            for col in df.columns:
                if col != name_col and not str(col).lower().startswith('unnamed') and str(col).strip():
                    # Проверяем, что в колонке есть числовые данные
                    numeric_values = pd.to_numeric(df[col], errors='coerce')
                    if numeric_values.notna().sum() > 0 and numeric_values.sum() > 0:
                        # Исключаем колонку "Итого" если она есть
                        if 'итого' not in str(col).lower() and 'total' not in str(col).lower():
                            stock_cols.append(col)
            
            if not stock_cols:
                st.error("❌ Не найдены колонки с остатками")
                st.write("Все колонки:", list(df.columns))
                return False
            
            st.info(f"📋 Найдено {len(stock_cols)} колонок со складами:")
            for i, col in enumerate(stock_cols):
                st.write(f"  {i+1}. {col}")
            
            # Обрабатываем данные остатков
            processed_data = []
            
            for _, row in df.iterrows():
                product_name = str(row[name_col]).strip()
                
                # Фильтруем валидные наименования
                if (product_name and 
                    product_name != 'nan' and 
                    len(product_name) > 2 and
                    not product_name.lower().startswith('итого') and
                    not product_name.isdigit()):
                    
                    stock_row = {'product_name': product_name}
                    
                    for col in stock_cols:
                        stock_value = pd.to_numeric(row[col], errors='coerce')
                        stock_row[col] = stock_value if not pd.isna(stock_value) else 0
                    
                    # Проверяем, что есть хотя бы один ненулевой остаток
                    total_stock = sum(stock_row[col] for col in stock_cols)
                    if total_stock > 0:
                        processed_data.append(stock_row)
            
            if not processed_data:
                st.error("❌ Не найдено товаров с остатками")
                return False
            
            self.stock_data = pd.DataFrame(processed_data)
            
            st.success(f"✅ Загружены остатки: {len(processed_data)} товаров по {len(stock_cols)} точкам")
            
            # Показываем примеры данных
            with st.expander("📋 Примеры загруженных данных"):
                st.dataframe(self.stock_data.head(10))
            
            return True
            
        except Exception as e:
            st.error(f"❌ Ошибка загрузки остатков: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return False
    
    def calculate_turnover_and_recommendations(self, min_multiplier=1.0, max_multiplier=1.0, safety_multiplier=1.0):
        """Расчет оборачиваемости и генерация рекомендаций"""
        
        if not self.ads_by_product or self.stock_data is None:
            st.error("❌ Недостаточно данных для анализа")
            return []
        
        st.info("🔄 Расчет оборачиваемости и генерация рекомендаций...")
        
        recommendations = []
        
        # Анализируем каждый товар
        for product_name, ads_data in self.ads_by_product.items():
            total_ads = ads_data['total_ads']
            
            if total_ads <= 0:
                continue
            
            # Ищем товар в остатках
            stock_matches = self.stock_data[
                self.stock_data['product_name'].str.contains(
                    product_name, case=False, na=False, regex=False
                )
            ]
            
            if stock_matches.empty:
                # Пробуем поиск по первым словам
                words = product_name.split()[:3]
                if words:
                    pattern = '|'.join(words)
                    stock_matches = self.stock_data[
                        self.stock_data['product_name'].str.contains(
                            pattern, case=False, na=False, regex=False
                        )
                    ]
            
            if not stock_matches.empty:
                stock_row = stock_matches.iloc[0]
                
                # Анализируем остатки по складам
                product_recommendations = self._analyze_product_stocks(
                    product_name, total_ads, stock_row, 
                    min_multiplier, max_multiplier, safety_multiplier
                )
                
                recommendations.extend(product_recommendations)
        
        # Сортируем рекомендации по приоритету
        recommendations = sorted(
            recommendations, 
            key=lambda x: (x['urgency_score'], x['quantity']), 
            reverse=True
        )
        
        self.recommendations = recommendations
        
        st.success(f"✅ Создано {len(recommendations)} рекомендаций по перемещениям")
        
        return recommendations
    
    def _analyze_product_stocks(self, product_name, ads_value, stock_row, min_mult, max_mult, safety_mult):
        """Анализ остатков товара по складам и генерация рекомендаций"""
        
        recommendations = []
        warehouse_states = {}
        
        # Анализируем состояние каждого склада
        stock_cols = [col for col in stock_row.index if col != 'product_name']
        
        for warehouse_col in stock_cols:
            current_stock = float(stock_row[warehouse_col]) if pd.notna(stock_row[warehouse_col]) else 0
            
            if current_stock <= 0:
                continue
            
            # Находим конфигурацию склада
            warehouse_config = self._find_warehouse_config(warehouse_col)
            
            # Рассчитываем нормативы
            warehouse_ads = ads_value * warehouse_config['ads_multiplier'] * safety_mult
            min_stock = warehouse_ads * warehouse_config['min_days'] * min_mult
            max_stock = warehouse_ads * warehouse_config['max_days'] * max_mult
            
            # Определяем статус
            if current_stock < min_stock * 0.5:
                status = 'critical'
                urgency = 10
            elif current_stock < min_stock:
                status = 'low'
                urgency = 7
            elif current_stock > max_stock:
                status = 'excess'
                urgency = 3
            elif current_stock > max_stock * 0.8:
                status = 'high'
                urgency = 2
            else:
                status = 'normal'
                urgency = 1
            
            warehouse_states[warehouse_col] = {
                'current_stock': current_stock,
                'min_stock': min_stock,
                'max_stock': max_stock,
                'status': status,
                'urgency': urgency,
                'config': warehouse_config,
                'surplus': max(0, current_stock - max_stock),
                'deficit': max(0, min_stock - current_stock)
            }
        
        # Генерируем рекомендации по перемещению
        recommendations.extend(self._generate_movement_recommendations(
            product_name, warehouse_states
        ))
        
        return recommendations
    
    def _find_warehouse_config(self, warehouse_name):
        """Поиск конфигурации склада в иерархии"""
        
        # Точное совпадение
        if warehouse_name in self.warehouse_hierarchy:
            return self.warehouse_hierarchy[warehouse_name]
        
        # Поиск по частичному совпадению
        warehouse_lower = warehouse_name.lower()
        
        for config_name, config in self.warehouse_hierarchy.items():
            config_lower = config_name.lower()
            if config_lower in warehouse_lower or warehouse_lower in config_lower:
                return config
        
        # Поиск по ключевым словам
        if 'база' in warehouse_lower and 'комплект' in warehouse_lower:
            return self.warehouse_hierarchy['База Склад Фурнитура Комплект']
        elif 'казыбаева' in warehouse_lower:
            if 'магазин' in warehouse_lower or 'тд' in warehouse_lower:
                return self.warehouse_hierarchy['ТД Казыбаева ФУРНИТУРА магазин']
            else:
                return self.warehouse_hierarchy['Казыбаева Склад Фурнитура TRADE']
        elif 'шымкент' in warehouse_lower or 'овощная' in warehouse_lower:
            if 'магазин' in warehouse_lower:
                return self.warehouse_hierarchy['6 Склад фурнитуры "Овощная база" Магазин']
            else:
                return self.warehouse_hierarchy['4 Склад фурнитуры АЗМ Шымкент "Овощная база"']
        elif 'астана' in warehouse_lower:
            if 'склад' in warehouse_lower:
                return self.warehouse_hierarchy['склад фурнитура № 1']
            else:
                return self.warehouse_hierarchy['Магазин фурнитуры']
        elif 'барыс' in warehouse_lower:
            return self.warehouse_hierarchy['Барыс Склад Фурнитура TRADE']
        elif 'ао' in warehouse_lower:
            return self.warehouse_hierarchy['АО Склад Фурнитура TRADE']
        
        # По умолчанию - конфигурация магазина
        return {
            'type': 'store',
            'level': 3,
            'city': 'Неизвестно',
            'parent': None,
            'children': [],
            'ads_multiplier': 1.0,
            'min_days': 10,
            'max_days': 25
        }
    
    def _generate_movement_recommendations(self, product_name, warehouse_states):
        """Генерация рекомендаций по перемещению для товара"""
        
        recommendations = []
        
        # Находим точки с дефицитом и излишком
        deficit_points = []
        surplus_points = []
        
        for warehouse, state in warehouse_states.items():
            if state['status'] in ['critical', 'low'] and state['deficit'] > 0:
                deficit_points.append((warehouse, state))
            elif state['status'] in ['excess', 'high'] and state['surplus'] > 0:
                surplus_points.append((warehouse, state))
        
        # Сортируем по приоритету
        deficit_points.sort(key=lambda x: x[1]['urgency'], reverse=True)
        surplus_points.sort(key=lambda x: x[1]['urgency'])
        
        # Создаем рекомендации
        for deficit_warehouse, deficit_state in deficit_points:
            needed = deficit_state['deficit']
            
            for surplus_warehouse, surplus_state in surplus_points:
                if needed <= 0:
                    break
                
                available = surplus_state['surplus']
                if available <= 0:
                    continue
                
                # Проверяем логику перемещения (согласно иерархии)
                move_allowed, move_type = self._check_movement_logic(
                    surplus_state['config'], deficit_state['config']
                )
                
                if move_allowed:
                    move_qty = min(needed, available)
                    
                    if move_qty > 0:
                        recommendation = {
                            'product_name': product_name,
                            'from_warehouse': surplus_warehouse,
                            'to_warehouse': deficit_warehouse,
                            'quantity': move_qty,
                            'urgency_score': deficit_state['urgency'],
                            'movement_type': move_type,
                            'reason': self._generate_movement_reason(deficit_state, surplus_state),
                            'from_city': surplus_state['config']['city'],
                            'to_city': deficit_state['config']['city'],
                            'days_coverage': move_qty / (deficit_state['deficit'] / deficit_state['config']['min_days']) if deficit_state['deficit'] > 0 else 0
                        }
                        
                        recommendations.append(recommendation)
                        
                        # Обновляем остатки
                        needed -= move_qty
                        surplus_state['surplus'] -= move_qty
            
            # Если дефицит не покрыт - рекомендация заказа
            if needed > 0:
                recommendations.append({
                    'product_name': product_name,
                    'from_warehouse': 'Поставщик',
                    'to_warehouse': 'База Склад Фурнитура Комплект',
                    'quantity': needed * 1.2,  # С запасом
                    'urgency_score': deficit_state['urgency'],
                    'movement_type': 'supplier_order',
                    'reason': f'Заказ поставщику для покрытия дефицита',
                    'from_city': 'Внешний',
                    'to_city': 'Алматы',
                    'days_coverage': 0
                })
        
        return recommendations
    
    def _check_movement_logic(self, from_config, to_config):
        """Проверка логики перемещения согласно иерархии"""
        
        # Разрешенные типы перемещений:
        # 1. Из хаба в склады и магазины
        # 2. Из складов в подчиненные магазины
        # 3. Внутри одного города между точками одного уровня
        
        from_level = from_config['level']
        to_level = to_config['level']
        from_city = from_config['city']
        to_city = to_config['city']
        
        # Перемещение вниз по иерархии (разрешено)
        if from_level < to_level:
            return True, 'down_hierarchy'
        
        # Перемещение внутри города на одном уровне (разрешено)
        if from_level == to_level and from_city == to_city:
            return True, 'internal_city'
        
        # Перемещение между городами на одном уровне (через хаб)
        if from_level == to_level and from_city != to_city:
            return True, 'inter_city'
        
        # Перемещение вверх по иерархии (ограниченно)
        if from_level > to_level:
            # Только при критическом дефиците
            return True, 'up_hierarchy'
        
        return False, 'not_allowed'
    
    def _generate_movement_reason(self, deficit_state, surplus_state):
        """Генерация причины рекомендации"""
        
        if deficit_state['status'] == 'critical':
            return f"КРИТИЧЕСКИЙ дефицит! Остаток {deficit_state['current_stock']:.0f}, нужно {deficit_state['min_stock']:.0f}"
        elif deficit_state['status'] == 'low':
            return f"Низкие остатки: {deficit_state['current_stock']:.0f}, норма {deficit_state['min_stock']:.0f}"
        else:
            return f"Оптимизация запасов"
    
    def get_summary_statistics(self):
        """Получение сводной статистики"""
        
        if not self.recommendations:
            return None
        
        df = pd.DataFrame(self.recommendations)
        
        return {
            'total_recommendations': len(df),
            'critical_items': len(df[df['urgency_score'] >= 8]),
            'movement_types': df['movement_type'].value_counts().to_dict(),
            'cities_involved': len(set(df['from_city'].tolist() + df['to_city'].tolist())),
            'total_products': df['product_name'].nunique(),
            'avg_quantity': df['quantity'].mean()
        }

def create_new_movement_interface():
    """Создание интерфейса новой системы рекомендаций"""
    
    st.title("🚚 Новая система рекомендаций по перемещениям")
    st.markdown("---")
    
    # Инициализация системы
    if 'new_movement_system' not in st.session_state:
        st.session_state.new_movement_system = NewMovementSystem()
    
    system = st.session_state.new_movement_system
    
    # Вкладки интерфейса
    tab1, tab2, tab3 = st.tabs([
        "📁 Загрузка данных",
        "🚚 Рекомендации", 
        "📊 Статистика"
    ])
    
    with tab1:
        st.header("🔥 ЗАГРУЗКА ФАЙЛОВ ДЛЯ НОВОЙ СИСТЕМЫ")
        
        # Большое предупреждение
        st.error("""
        ⚠️ ВНИМАНИЕ! ЭТО НОВАЯ НЕЗАВИСИМАЯ СИСТЕМА!
        
        Если вы видите ошибку "Не найдена колонка с наименованиями товаров",
        значит вы пытаетесь загрузить файлы в СТАРОЙ системе.
        
        Используйте ТОЛЬКО эту страницу для загрузки файлов!
        """)
        
        # Загрузка файлов продаж
        st.subheader("📈 Файлы продаж по филиалам")
        st.info("Загрузите файлы продаж для расчета оборачиваемости и ADS")
        
        st.warning("🔍 Файлы типа: '6_Склад_фурнитуры_Овощная_база_Магазин_продажи_01_07_2024_01_07.xlsx'")
        
        sales_files = st.file_uploader(
            "Выберите файлы продаж (несколько файлов)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="new_sales_files"
        )
        
        if sales_files and st.button("🔄 Обработать файлы продаж", key="process_sales"):
            sales_dict = {}
            for file in sales_files:
                sales_dict[file.name] = file
            
            success = system.load_sales_files(sales_dict)
            if success:
                st.success("✅ Файлы продаж обработаны!")
                
                # Показываем ДЕТАЛЬНУЮ статистику по каждому филиалу ОТДЕЛЬНО
                st.subheader("📊 Детальная статистика по филиалам")
                
                for branch, data in system.sales_data_by_branch.items():
                    with st.expander(f"📍 {branch} - {len(data)} товаров", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Количество товаров", len(data))
                            avg_ads = data['ads'].mean() if len(data) > 0 else 0
                            st.metric("Средний ADS", f"{avg_ads:.2f}")
                        
                        with col2:
                            total_sales = data['total_sales'].sum()
                            st.metric("Общие продажи", f"{total_sales:,.0f}")
                            total_revenue = data['revenue'].sum()
                            st.metric("Общая выручка", f"{total_revenue:,.0f}")
                        
                        with col3:
                            if len(data) > 0:
                                max_ads_product = data.loc[data['ads'].idxmax()]
                                st.write(f"**Топ товар по ADS:**")
                                st.write(f"{max_ads_product['product_name'][:30]}...")
                                st.write(f"ADS: {max_ads_product['ads']:.2f}")
                        
                        # Аналитика оборачиваемости для филиала
                        if 'turnover_days' in data.columns:
                            st.markdown("**📊 Анализ оборачиваемости:**")
                            
                            # Классификация товаров по оборачиваемости
                            fast_moving = data[data['turnover_days'] <= 30]
                            medium_moving = data[(data['turnover_days'] > 30) & (data['turnover_days'] <= 90)]
                            slow_moving = data[(data['turnover_days'] > 90) & (data['turnover_days'] <= 365)]
                            very_slow_moving = data[data['turnover_days'] > 365]
                            no_movement = data[data['turnover_days'] == float('inf')]
                            
                            col_t1, col_t2, col_t3 = st.columns(3)
                            with col_t1:
                                st.metric("🚀 Быстрые (<30д)", len(fast_moving))
                                st.metric("🐌 Очень медленные (>365д)", len(very_slow_moving))
                            with col_t2:
                                st.metric("🚶 Средние (30-90д)", len(medium_moving))
                                st.metric("❌ Без движения", len(no_movement))
                            with col_t3:
                                st.metric("🐢 Медленные (90-365д)", len(slow_moving))
                                avg_turnover = data[data['turnover_days'] != float('inf')]['turnover_days'].mean()
                                st.metric("Средняя оборачиваемость", f"{avg_turnover:.1f} дней")
                        
                        # Показываем топ-10 товаров по продажам
                        st.write("**🔥 Топ-10 товаров по продажам:**")
                        top_products = data.nlargest(10, 'revenue')[['product_name', 'revenue', 'ads']]
                        if 'turnover_days' in data.columns:
                            top_products = data.nlargest(10, 'revenue')[['product_name', 'revenue', 'ads', 'turnover_days']]
                            for idx, (_, row) in enumerate(top_products.iterrows(), 1):
                                turnover_text = f"| Оборот: {row['turnover_days']:.1f}д" if row['turnover_days'] != float('inf') else "| Без движения"
                                st.write(f"{idx}. {row['product_name'][:40]} | {row['revenue']:,.0f} | ADS: {row['ads']:.1f} {turnover_text}")
                        else:
                            for idx, (_, row) in enumerate(top_products.iterrows(), 1):
                                st.write(f"{idx}. {row['product_name'][:40]} | {row['revenue']:,.0f} | ADS: {row['ads']:.1f}")
        
        # Загрузка остатков
        st.subheader("📦 Файл остатков")
        
        st.warning("🔍 Конкретно файл: 'остатки на 08.07.2025.xlsx'")
        st.info("🔧 Новая система автоматически найдет правильную структуру файла!")
        
        stock_file = st.file_uploader(
            "Выберите файл с текущими остатками",
            type=['xlsx', 'xls'],
            key="new_stock_file"
        )
        
        if stock_file and st.button("🔄 Загрузить остатки", key="load_stock"):
            success = system.load_stock_file(stock_file)
            if success:
                st.success("✅ Остатки загружены!")
    
    with tab2:
        st.header("Генерация рекомендаций по перемещениям")
        
        if not system.ads_by_product or system.stock_data is None:
            st.warning("⚠️ Сначала загрузите файлы продаж и остатков")
        else:
            # Настройки
            st.subheader("⚙️ Настройки расчета")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_mult = st.slider("Множитель минимальных запасов", 0.5, 2.0, 1.0, 0.1, key="new_min_mult")
            
            with col2:
                max_mult = st.slider("Множитель максимальных запасов", 0.5, 2.0, 1.0, 0.1, key="new_max_mult")
            
            with col3:
                safety_mult = st.slider("Коэффициент безопасности", 0.5, 2.0, 1.0, 0.1, key="new_safety_mult")
            
            # Генерация рекомендаций
            if st.button("🚀 Сгенерировать рекомендации", type="primary", key="generate_recs"):
                recommendations = system.calculate_turnover_and_recommendations(
                    min_mult, max_mult, safety_mult
                )
                
                if recommendations:
                    st.success(f"✅ Создано {len(recommendations)} рекомендаций!")
                    
                    # Фильтры
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        urgency_filter = st.selectbox(
                            "Фильтр по срочности",
                            ['Все'] + sorted(list(set(r['urgency_score'] for r in recommendations)), reverse=True),
                            key="urgency_filter"
                        )
                    
                    with col2:
                        movement_filter = st.selectbox(
                            "Тип перемещения",
                            ['Все'] + list(set(r['movement_type'] for r in recommendations)),
                            key="movement_filter"
                        )
                    
                    # Применяем фильтры
                    filtered_recs = recommendations
                    if urgency_filter != 'Все':
                        filtered_recs = [r for r in filtered_recs if r['urgency_score'] >= urgency_filter]
                    if movement_filter != 'Все':
                        filtered_recs = [r for r in filtered_recs if r['movement_type'] == movement_filter]
                    
                    # Отображаем рекомендации
                    st.subheader(f"📋 Рекомендации ({len(filtered_recs)} из {len(recommendations)})")
                    
                    for i, rec in enumerate(filtered_recs[:20]):  # Ограничиваем 20 записями
                        urgency_icon = "🔴" if rec['urgency_score'] >= 8 else "🟡" if rec['urgency_score'] >= 5 else "🟢"
                        
                        with st.expander(f"{urgency_icon} {rec['product_name']} | {rec['from_warehouse']} → {rec['to_warehouse']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Количество:** {rec['quantity']:.1f}")
                                st.write(f"**Причина:** {rec['reason']}")
                                st.write(f"**Срочность:** {rec['urgency_score']}/10")
                            
                            with col2:
                                st.write(f"**Маршрут:** {rec['from_city']} → {rec['to_city']}")
                                st.write(f"**Тип:** {rec['movement_type']}")
                                st.write(f"**Покрытие:** {rec['days_coverage']:.1f} дней")
                    
                    # Экспорт
                    st.markdown("---")
                    if st.button("📥 Экспорт в Excel", key="export_excel"):
                        # Создаем Excel файл
                        from io import BytesIO
                        output = BytesIO()
                        
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Рекомендации
                            rec_df = pd.DataFrame(recommendations)
                            rec_df.to_excel(writer, sheet_name='Рекомендации', index=False)
                            
                            # ADS данные
                            ads_df = pd.DataFrame([
                                {'product_name': k, 'total_ads': v['total_ads'], 'branches_count': len(v['branches'])}
                                for k, v in system.ads_by_product.items()
                            ])
                            ads_df.to_excel(writer, sheet_name='ADS', index=False)
                            
                            # Остатки
                            system.stock_data.to_excel(writer, sheet_name='Остатки', index=False)
                        
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 Скачать отчет Excel",
                            data=output.getvalue(),
                            file_name=f"new_movement_recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    with tab3:
        st.header("📊 Статистика и аналитика оборачиваемости")
        
        # Аналитика оборачиваемости для всех товаров
        if system.sales_data_by_branch:
            st.subheader("🔄 Общая аналитика оборачиваемости")
            
            # Собираем данные по всем товарам
            all_turnover_data = []
            for branch, data in system.sales_data_by_branch.items():
                if 'turnover_days' in data.columns:
                    for _, row in data.iterrows():
                        all_turnover_data.append({
                            'product_name': row['product_name'],
                            'branch': branch,
                            'turnover_days': row['turnover_days'],
                            'turnover_rate': row.get('turnover_rate', 0),
                            'ads': row['ads'],
                            'revenue': row['revenue']
                        })
            
            if all_turnover_data:
                turnover_df = pd.DataFrame(all_turnover_data)
                
                # Классификация по оборачиваемости
                fast_moving = turnover_df[turnover_df['turnover_days'] <= 30]
                medium_moving = turnover_df[(turnover_df['turnover_days'] > 30) & (turnover_df['turnover_days'] <= 90)]
                slow_moving = turnover_df[(turnover_df['turnover_days'] > 90) & (turnover_df['turnover_days'] <= 365)]
                very_slow_moving = turnover_df[turnover_df['turnover_days'] > 365]
                no_movement = turnover_df[turnover_df['turnover_days'] == float('inf')]
                
                # Визуализация
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🚀 Быстрооборачиваемые (<30 дней)", len(fast_moving))
                    st.metric("🐢 Медленные (90-365 дней)", len(slow_moving))
                
                with col2:
                    st.metric("🚶 Средние (30-90 дней)", len(medium_moving))
                    st.metric("🐌 Очень медленные (>365 дней)", len(very_slow_moving))
                
                with col3:
                    st.metric("❌ Без движения", len(no_movement))
                    avg_turnover = turnover_df[turnover_df['turnover_days'] != float('inf')]['turnover_days'].mean()
                    st.metric("Средняя оборачиваемость", f"{avg_turnover:.1f} дней")
                
                # График распределения оборачиваемости
                st.subheader("📈 Распределение товаров по оборачиваемости")
                
                turnover_categories = ['Быстрые (<30д)', 'Средние (30-90д)', 'Медленные (90-365д)', 'Очень медленные (>365д)', 'Без движения']
                turnover_counts = [len(fast_moving), len(medium_moving), len(slow_moving), len(very_slow_moving), len(no_movement)]
                
                import plotly.express as px
                import plotly.graph_objects as go
                
                fig = go.Figure(data=[go.Bar(
                    x=turnover_categories,
                    y=turnover_counts,
                    marker_color=['#00ff00', '#ffff00', '#ff8000', '#ff0000', '#800080']
                )])
                
                fig.update_layout(
                    title="Распределение товаров по скорости оборачиваемости",
                    xaxis_title="Категория оборачиваемости",
                    yaxis_title="Количество товаров"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Топ товары по разным метрикам
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏆 Топ-10 быстрооборачиваемых товаров")
                    if len(fast_moving) > 0:
                        top_fast = fast_moving.nsmallest(10, 'turnover_days')
                        for idx, (_, row) in enumerate(top_fast.iterrows(), 1):
                            st.write(f"{idx}. {row['product_name'][:40]} - {row['turnover_days']:.1f} дней")
                    else:
                        st.info("Нет быстрооборачиваемых товаров")
                
                with col2:
                    st.subheader("🐌 Топ-10 медленнооборачиваемых товаров")
                    slow_with_movement = turnover_df[turnover_df['turnover_days'] != float('inf')]
                    if len(slow_with_movement) > 0:
                        top_slow = slow_with_movement.nlargest(10, 'turnover_days')
                        for idx, (_, row) in enumerate(top_slow.iterrows(), 1):
                            st.write(f"{idx}. {row['product_name'][:40]} - {row['turnover_days']:.1f} дней")
                    else:
                        st.info("Нет данных по медленным товарам")
        
        # Статистика рекомендаций
        if system.recommendations:
            st.subheader("📋 Статистика рекомендаций")
            stats = system.get_summary_statistics()
            
            if stats:
                # Основные метрики
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Всего рекомендаций", stats['total_recommendations'])
                
                with col2:
                    st.metric("Критические", stats['critical_items'])
                
                with col3:
                    st.metric("Товаров", stats['total_products'])
                
                with col4:
                    st.metric("Городов", stats['cities_involved'])
                
                # Распределение по типам
                st.subheader("📊 Распределение по типам перемещений")
                movement_df = pd.DataFrame(list(stats['movement_types'].items()), 
                                         columns=['Тип', 'Количество'])
                st.bar_chart(movement_df.set_index('Тип'))
                
                # Детальная статистика
                st.subheader("📋 Детальная статистика")
                st.write(f"- Среднее количество в рекомендации: {stats['avg_quantity']:.1f}")
                st.write(f"- Типы перемещений: {list(stats['movement_types'].keys())}")
        else:
            st.info("📊 Статистика будет доступна после генерации рекомендаций")
    
    # Боковая панель с информацией
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ О новой системе")
    
    st.sidebar.markdown("""
    **Особенности:**
    - ✅ Анализ оборачиваемости по филиалам
    - ✅ Иерархия складов
    - ✅ Умные рекомендации
    - ✅ Приоритизация по срочности
    - ✅ Экспорт отчетов
    """)
    
    # Статус системы
    if system.ads_by_product:
        st.sidebar.success(f"📊 ADS: {len(system.ads_by_product)} товаров")
    else:
        st.sidebar.error("❌ ADS не рассчитан")
    
    if system.stock_data is not None:
        st.sidebar.success(f"📦 Остатки: {len(system.stock_data)} товаров")
    else:
        st.sidebar.error("❌ Остатки не загружены")
    
    if system.recommendations:
        st.sidebar.success(f"🚚 Рекомендации: {len(system.recommendations)}")
    else:
        st.sidebar.info("ℹ️ Рекомендации не созданы")

if __name__ == "__main__":
    create_new_movement_interface()