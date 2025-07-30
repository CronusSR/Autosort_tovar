#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчик единого файла продаж для ADS анализа
Разделяет данные по филиалам и сохраняет в папку ads/
"""

import pandas as pd
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, Any
import io

class SingleFileADSProcessor:
    """Обработчик единого файла с продажами всех филиалов"""
    
    def __init__(self):
        # Маппинг колонок из файла к системным именам филиалов (ПРОВЕРЕНО!)
        self.branch_column_mapping = {
            r'тд казыбаева.*магазин': 'казыбаева_магазин',
            r'казыбаева.*склад.*trade': 'казыбаева_склад', 
            r'барыс.*склад.*trade': 'барыс',
            r'ао.*склад.*trade': 'ао_склад',
            r'магазин фурнитуры': 'астана_магазин',
            r'склад фурнитура № 1': 'астана_склад',
            r'6.*склад.*овощная база.*магазин': 'шымкент_магазин',
            r'4.*склад.*азм.*шымкент.*овощная база': 'шымкент_склад'
        }
        
        # Создаем папку ads если её нет
        os.makedirs('ads', exist_ok=True)
    
    def process_single_file(self, uploaded_file) -> Dict[str, Any]:
        """Обработка единого файла с филиалами в виде колонок"""
        results = {
            'success': False,
            'branches_data': {},
            'total_branches': 0,
            'total_items': 0,
            'errors': []
        }
        
        try:
            # Читаем файл
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Ищем колонки с данными филиалов
            branch_columns = self.identify_branch_columns(df.columns)
            
            if not branch_columns:
                results['errors'].append("❌ Колонки с данными филиалов не найдены")
                return results
            
            results['total_branches'] = len(branch_columns)
            
            # Обрабатываем каждый филиал (колонку) отдельно
            for column_name, system_name in branch_columns.items():
                # Обрабатываем данные филиала из этой колонки
                branch_data = self.process_branch_column(df, column_name, system_name)
                
                if branch_data['success']:
                    results['branches_data'][system_name] = branch_data
                    results['total_items'] += branch_data['total_items']
                else:
                    results['errors'].append(f"Ошибка обработки филиала {column_name}: {branch_data.get('error', 'Unknown')}")
            
            # Сохраняем объединенные данные ADS
            self.save_combined_ads_data(results['branches_data'])
            
            results['success'] = len(results['branches_data']) > 0
            
        except Exception as e:
            results['errors'].append(f"❌ Общая ошибка: {str(e)}")
        
        return results
    
    def identify_branch_columns(self, columns) -> Dict[str, str]:
        """Определение колонок с данными филиалов"""
        import re
        
        branch_columns = {}
        
        for column in columns:
            column_lower = column.lower()
            
            # Пропускаем служебные колонки
            if any(skip in column_lower for skip in ['категория', 'подкатегория', 'номенклатура']):
                continue
            
            # Ищем соответствие с филиалами по ключевым словам
            for pattern, system_name in self.branch_column_mapping.items():
                if re.search(pattern, column_lower):
                    branch_columns[column] = system_name
                    break
        
        return branch_columns
    
    def preprocess_subcategory_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Обрабатывает структуру Excel где подкатегории находятся в отдельных строках-заголовках
        Структура: A=КАТЕГОРИЯ, B=ПОДКАТЕГОРИЯ, C=Номенклатура
        """
        try:
            # Ищем нужные колонки
            nomenclature_column = None
            category_column = None
            subcategory_column = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'номенклатура' in col_lower:
                    nomenclature_column = col
                elif 'категория' in col_lower and 'подкатегория' not in col_lower:
                    category_column = col
                elif 'подкатегория' in col_lower:
                    subcategory_column = col
            
            print(f"  🔍 Найденные колонки: номенклатура={nomenclature_column}, категория={category_column}, подкатегория={subcategory_column}")
            
            if nomenclature_column is None:
                print("  ⚠️ Колонка номенклатуры не найдена")
                return df
            
            # Если колонка подкатегорий есть, но может быть неправильно заполнена
            if subcategory_column is None:
                print("  ⚠️ Колонка подкатегорий не найдена")
                return df
            
            current_category = None
            current_subcategory = None
            processed_count = 0
            
            # Проходим по всем строкам
            for idx, row in df.iterrows():
                nomenclature_value = row[nomenclature_column]
                category_value = row[category_column] if category_column else None
                subcategory_value = row[subcategory_column] if subcategory_column else None
                
                # Определяем тип строки
                has_nomenclature = not (pd.isna(nomenclature_value) or str(nomenclature_value).strip() == '')
                has_category = not (pd.isna(category_value) or str(category_value).strip() == '')
                has_subcategory = not (pd.isna(subcategory_value) or str(subcategory_value).strip() == '')
                
                if has_category and not has_nomenclature:
                    # Это строка категории или подкатегории
                    current_category = str(category_value).strip()
                    
                    if has_subcategory:
                        # Это строка подкатегории
                        current_subcategory = str(subcategory_value).strip()
                        print(f"  📂 Найдена подкатегория: {current_subcategory} (категория: {current_category})")
                    else:
                        # Это только категория
                        print(f"  📁 Найдена категория: {current_category}")
                
                elif has_nomenclature:
                    # Это строка товара
                    # Заполняем категорию и подкатегорию если они пустые
                    if current_category and (pd.isna(row[category_column]) or str(row[category_column]).strip() == ''):
                        df.at[idx, category_column] = current_category
                    
                    if current_subcategory and (pd.isna(row[subcategory_column]) or str(row[subcategory_column]).strip() == ''):
                        df.at[idx, subcategory_column] = current_subcategory
                        processed_count += 1
            
            print(f"  ✅ Обработано {processed_count} товаров с подкатегориями")
            return df
            
        except Exception as e:
            print(f"  ⚠️ Ошибка предобработки подкатегорий: {e}")
            import traceback
            traceback.print_exc()
            return df
    
    def process_branch_column(self, df: pd.DataFrame, column_name: str, system_name: str) -> Dict[str, Any]:
        """Обработка данных одной колонки (филиала)"""
        result = {
            'success': False,
            'branch_name': column_name,
            'system_name': system_name,
            'total_items': 0,
            'ads_data': {}
        }
        
        try:
            # Проверяем наличие колонки с номенклатурой
            nomenclature_column = None
            for col in df.columns:
                if 'номенклатура' in col.lower():
                    nomenclature_column = col
                    break
            
            if nomenclature_column is None:
                result['error'] = "Колонка с номенклатурой не найдена"
                return result
            
            # НОВАЯ ЛОГИКА: Обрабатываем структуру с подкатегориями в заголовках
            df_processed = self.preprocess_subcategory_headers(df.copy())
            
            # Фильтруем данные: только строки с продажами > 0
            valid_rows = df_processed[df_processed[column_name].notna() & (df_processed[column_name] > 0)]
            
            if len(valid_rows) == 0:
                result['error'] = f"Нет продаж в колонке {column_name}"
                return result
            
            # Предполагаемый период для расчета ADS (год = 365 дней)
            days_period = 365
            
            # Обрабатываем каждый товар
            for _, row in valid_rows.iterrows():
                item_name = str(row[nomenclature_column]).strip()
                sales_value = float(row[column_name])
                
                if item_name and sales_value > 0:
                    # Рассчитываем ADS
                    ads_value = sales_value / days_period
                    
                    item_data = {
                        'название': item_name,
                        'общие_продажи': sales_value,
                        'среднедневные_продажи': round(ads_value, 3),
                        'период_дней': days_period,
                        'филиал_колонка': column_name
                    }
                    
                    # Добавляем категории если есть
                    if 'КАТЕГОРИЯ' in df_processed.columns and not pd.isna(row['КАТЕГОРИЯ']):
                        item_data['категория'] = str(row['КАТЕГОРИЯ'])
                    
                    if 'ПОДКАТЕГОРИЯ' in df_processed.columns and not pd.isna(row['ПОДКАТЕГОРИЯ']):
                        item_data['подкатегория'] = str(row['ПОДКАТЕГОРИЯ'])
                    
                    result['ads_data'][item_name] = item_data
            
            # Применяем заполнение среднего ADS по подкатегориям для товаров без продаж
            result['ads_data'] = self.fill_zero_ads_with_category_average(df_processed, result['ads_data'], column_name, nomenclature_column)
            
            result['total_items'] = len(result['ads_data'])
            result['success'] = True
            
            # Сохраняем данные филиала
            self.save_branch_ads_data(system_name, result['ads_data'])
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def fill_zero_ads_with_category_average(self, df: pd.DataFrame, ads_data: Dict, sales_column: str, nomenclature_column: str) -> Dict:
        """Заполнение нулевых ADS средними значениями по подкатегориям"""
        try:
            # Проверяем наличие колонок категорий
            if 'ПОДКАТЕГОРИЯ' not in df.columns:
                return ads_data  # Если нет подкатегорий, возвращаем как есть
            
            # Создаем словарь средних ADS по подкатегориям
            subcategory_avg_ads = {}
            
            # Рассчитываем средние ADS по подкатегориям для товаров с продажами
            for item_name, item_data in ads_data.items():
                if item_data['среднедневные_продажи'] > 0 and 'подкатегория' in item_data:
                    subcategory = item_data['подкатегория']
                    
                    if subcategory not in subcategory_avg_ads:
                        subcategory_avg_ads[subcategory] = []
                    
                    subcategory_avg_ads[subcategory].append(item_data['среднедневные_продажи'])
            
            # Вычисляем средние значения
            subcategory_averages = {}
            for subcategory, ads_values in subcategory_avg_ads.items():
                if ads_values:
                    subcategory_averages[subcategory] = sum(ads_values) / len(ads_values)
            
            # Обрабатываем товары без продаж (нулевые или отсутствующие в sales_column)
            zero_ads_items = []
            
            for _, row in df.iterrows():
                item_name = str(row[nomenclature_column]).strip()
                
                # Пропускаем пустые наименования
                if not item_name or item_name == 'nan':
                    continue
                
                # Проверяем - есть ли у товара продажи в данном филиале
                sales_value = row[sales_column] if pd.notna(row[sales_column]) else 0
                
                # Если нет продаж, но товар есть в общем списке - добавляем с средним ADS
                if sales_value <= 0 and item_name not in ads_data:
                    subcategory = str(row['ПОДКАТЕГОРИЯ']) if pd.notna(row['ПОДКАТЕГОРИЯ']) else None
                    
                    if subcategory and subcategory in subcategory_averages:
                        # Используем средний ADS по подкатегории
                        avg_ads = subcategory_averages[subcategory]
                        
                        item_data = {
                            'название': item_name,
                            'общие_продажи': 0,
                            'среднедневные_продажи': round(avg_ads, 3),
                            'период_дней': 365,
                            'филиал_колонка': sales_column,
                            'источник_ads': f'средний по подкатегории {subcategory}',
                            'подкатегория': subcategory
                        }
                        
                        # Добавляем категорию если есть
                        if 'КАТЕГОРИЯ' in df.columns and not pd.isna(row['КАТЕГОРИЯ']):
                            item_data['категория'] = str(row['КАТЕГОРИЯ'])
                        
                        ads_data[item_name] = item_data
                        zero_ads_items.append(item_name)
            
            if zero_ads_items:
                print(f"  📈 Заполнено {len(zero_ads_items)} товаров средними ADS по подкатегориям")
                print(f"  📊 Использованы средние по {len(subcategory_averages)} подкатегориям")
            
            return ads_data
            
        except Exception as e:
            print(f"⚠️ Ошибка заполнения средних ADS: {e}")
            return ads_data
    
    def save_branch_ads_data(self, branch_name: str, ads_data: Dict):
        """Сохранение ADS данных филиала"""
        filename = f"ads/{branch_name}_ads.json"
        
        data_to_save = {
            'branch': branch_name,
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items_count': len(ads_data),
            'ads_data': ads_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    
    def save_combined_ads_data(self, all_branches_data: Dict):
        """Сохранение объединенных данных всех филиалов"""
        combined_data = {
            'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'branches_count': len(all_branches_data),
            'branches': {}
        }
        
        for branch_name, branch_data in all_branches_data.items():
            combined_data['branches'][branch_name] = {
                'name': branch_data['branch_name'],
                'items_count': branch_data['total_items'],
                'ads_file': f"{branch_name}_ads.json"
            }
        
        with open('ads/combined_ads_data.json', 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
    
    def integrate_with_main_system(self, branches_data: Dict):
        """Интеграция данных ADS с основной системой для совместимости"""
        import streamlit as st
        import pandas as pd
        
        try:
            # Создаем объединенный DataFrame для совместимости с системой рекомендаций
            all_ads_data = []
            
            for branch_name, branch_data in branches_data.items():
                # Читаем данные филиала
                ads_file = f"ads/{branch_name}_ads.json"
                if os.path.exists(ads_file):
                    with open(ads_file, 'r', encoding='utf-8') as f:
                        branch_ads = json.load(f)
                    
                    for item_name, item_data in branch_ads['ads_data'].items():
                        all_ads_data.append({
                            'номенклатура': item_name,
                            'ads': item_data['среднедневные_продажи'],
                            'общие_продажи': item_data['общие_продажи'],
                            'филиал': branch_name,
                            'категория': item_data.get('категория', ''),
                            'подкатегория': item_data.get('подкатегория', '')
                        })
            
            if all_ads_data:
                # Создаем DataFrame
                ads_df = pd.DataFrame(all_ads_data)
                
                # Группируем по номенклатуре (берем максимальный ADS между филиалами)
                grouped_ads = ads_df.groupby('номенклатура').agg({
                    'ads': 'max',
                    'общие_продажи': 'sum',
                    'категория': 'first',
                    'подкатегория': 'first'
                }).reset_index()
                
                # Интегрируем в основную систему если она есть
                if 'inventory_system' in st.session_state:
                    st.session_state.inventory_system.calculated_ads = grouped_ads
                    st.session_state.inventory_system.ads_by_branches = ads_df
                    
                    st.success(f"✅ **Данные ADS интегрированы в основную систему!** ({len(grouped_ads)} уникальных товаров)")
                else:
                    st.info("ℹ️ Данные ADS сохранены в JSON файлы для дальнейшего использования")
                    
        except Exception as e:
            st.warning(f"⚠️ Не удалось интегрировать с основной системой: {e}")
    
    def create_streamlit_interface(self):
        """Создание интерфейса Streamlit для загрузки файла"""
        st.header("📊 Загрузка единого файла продаж для ADS анализа")
        
        st.info("""
        ℹ️ **Новый формат загрузки:**
        - Загружайте ОДИН файл со всеми филиалами
        - Каждый филиал - отдельная колонка с продажами
        - Система автоматически определит филиалы по названиям колонок
        - Поддерживается структура где подкатегории указаны в отдельных строках-заголовках
        - Структура: КАТЕГОРИЯ | ПОДКАТЕГОРИЯ | Номенклатура | [Филиал 1] | [Филиал 2] | ...
        """)
        
        uploaded_file = st.file_uploader(
            "Загрузите файл продаж (Excel)",
            type=['xlsx', 'xls'],
            key='single_ads_file'
        )
        
        if uploaded_file:
            with st.spinner('Обработка файла...'):
                results = self.process_single_file(uploaded_file)
            
            if results['success']:
                st.success(f"""
                ✅ **Файл успешно обработан!**
                - Найдено филиалов: {results['total_branches']}
                - Всего товаров: {results['total_items']}
                """)
                
                # Показываем детали по филиалам
                st.subheader("📋 Детали по филиалам")
                
                # Создаем таблицу с результатами
                branch_summary = []
                for branch_name, branch_data in results['branches_data'].items():
                    branch_summary.append({
                        'Филиал': branch_data['branch_name'][:50] + '...' if len(branch_data['branch_name']) > 50 else branch_data['branch_name'],
                        'Системное имя': branch_name,
                        'Товаров': branch_data['total_items'],
                        'Файл ADS': f"{branch_name}_ads.json"
                    })
                
                import pandas as pd
                summary_df = pd.DataFrame(branch_summary)
                st.dataframe(summary_df, use_container_width=True)
                
                # Показываем статистику по заполнению нулевых ADS
                st.subheader("📈 Заполнение средними ADS по подкатегориям")
                total_filled = 0
                for branch_name, branch_data in results['branches_data'].items():
                    # Читаем данные филиала чтобы посчитать заполненные
                    try:
                        import json
                        with open(f'ads/{branch_name}_ads.json', 'r', encoding='utf-8') as f:
                            branch_ads = json.load(f)
                        
                        filled_count = sum(1 for item_data in branch_ads['ads_data'].values() 
                                         if 'источник_ads' in item_data)
                        
                        if filled_count > 0:
                            st.write(f"• **{branch_data['branch_name'][:30]}**: {filled_count} товаров заполнено средними ADS")
                            total_filled += filled_count
                    except:
                        pass
                
                if total_filled > 0:
                    st.info(f"🎯 **Итого заполнено {total_filled} товаров** средними ADS по подкатегориям")
                else:
                    st.info("ℹ️ Все товары имели данные о продажах")
                
                # 🔄 ИНТЕГРАЦИЯ С ОСНОВНОЙ СИСТЕМОЙ
                self.integrate_with_main_system(results['branches_data'])
                
                # Добавляем аналитику сразу после успешной обработки
                st.markdown("---")
                st.subheader("📊 Детальная аналитика филиалов")
                
                try:
                    from branch_analytics import BranchAnalytics
                    analytics = BranchAnalytics()
                    
                    # Выбор филиала
                    branch_options = {}
                    for branch_name, branch_data in results['branches_data'].items():
                        display_name = f"{branch_name} ({branch_data['total_items']} товаров)"
                        branch_options[display_name] = branch_name
                    
                    selected_display = st.selectbox(
                        "Выберите филиал для анализа:",
                        options=list(branch_options.keys()),
                        key="branch_selector_main"
                    )
                    
                    if selected_display:
                        selected_branch = branch_options[selected_display]
                        analytics.show_branch_detailed_analysis(selected_branch)
                        
                except ImportError:
                    st.error("❌ Модуль аналитики филиалов не найден")
                except Exception as e:
                    st.error(f"❌ Ошибка аналитики: {e}")
                    
            else:
                st.error("❌ Ошибки при обработке файла:")
                for error in results['errors']:
                    st.error(error)

# Функция для интеграции в существующую систему
def integrate_single_file_processor():
    """Интеграция нового обработчика в существующую систему"""
    processor = SingleFileADSProcessor()
    processor.create_streamlit_interface()

if __name__ == "__main__":
    # Тестовый запуск
    st.set_page_config(page_title="ADS Processor", layout="wide")
    integrate_single_file_processor()