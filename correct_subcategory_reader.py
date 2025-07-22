#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИСПРАВЛЕННЫЙ МОДУЛЬ ДЛЯ ЧТЕНИЯ ПОДКАТЕГОРИЙ
Читает файл с правильной логикой определения подкатегорий
"""

import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Tuple, Optional

class CorrectSubcategoryReader:
    """Класс для правильного чтения подкатегорий из Excel файла"""
    
    def __init__(self):
        self.shared_strings = {}
        self.sales_data = []
        
    def read_xlsx_manual(self, file_path: str) -> List[Dict]:
        """Ручное чтение XLSX файла через XML"""
        results = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Читаем shared strings
                self._read_shared_strings(zip_file)
                
                # Читаем данные листа
                with zip_file.open('xl/worksheets/sheet1.xml') as sheet_file:
                    sheet_content = sheet_file.read().decode('utf-8')
                    sheet_root = ET.fromstring(sheet_content)
                    
                    rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                    
                    current_category = None
                    current_subcategory = None
                    
                    for row_idx, row in enumerate(rows[1:], start=2):  # Пропускаем заголовок
                        row_data = self._parse_row(row)
                        
                        if not row_data:
                            continue
                            
                        a_value = row_data.get('A')  # Категория
                        b_value = row_data.get('B')  # Подкатегория
                        c_value = row_data.get('C')  # Номенклатура
                        
                        # Определяем тип строки
                        if a_value and not b_value and not c_value:
                            # Это строка только с категорией
                            current_category = a_value
                            current_subcategory = None
                            continue
                            
                        elif a_value and b_value and not c_value:
                            # Это строка с подкатегорией
                            current_category = a_value
                            current_subcategory = b_value
                            continue
                            
                        elif a_value and c_value:
                            # Это товарная строка
                            current_category = a_value
                            
                            # Собираем данные по всем филиалам (колонки D-K)
                            total_sales = 0
                            branch_sales = {}
                            
                            for col_letter in ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']:
                                sales_value = row_data.get(col_letter, 0)
                                try:
                                    sales_value = float(sales_value) if sales_value else 0
                                except:
                                    sales_value = 0
                                    
                                branch_sales[col_letter] = sales_value
                                total_sales += sales_value
                            
                            # Добавляем запись
                            results.append({
                                'row_number': row_idx,
                                'category': current_category,
                                'subcategory': current_subcategory or 'Без подкатегории',
                                'nomenclature': c_value,
                                'total_sales': total_sales,
                                'branch_sales': branch_sales,
                                'has_subcategory': current_subcategory is not None
                            })
        
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return []
        
        return results
    
    def _read_shared_strings(self, zip_file):
        """Чтение строковых значений"""
        try:
            with zip_file.open('xl/sharedStrings.xml') as ss_file:
                ss_content = ss_file.read().decode('utf-8')
                ss_root = ET.fromstring(ss_content)
                
                for i, si in enumerate(ss_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si')):
                    t_elem = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                    if t_elem is not None:
                        self.shared_strings[i] = t_elem.text
        except Exception as e:
            print(f"Ошибка чтения shared strings: {e}")
    
    def _parse_row(self, row) -> Dict:
        """Парсинг строки XML в словарь значений"""
        cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
        row_data = {}
        
        for cell in cells:
            cell_ref = cell.get('r', '')
            col_letter = ''.join([c for c in cell_ref if c.isalpha()])
            cell_type = cell.get('t', '')
            
            v_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
            if v_elem is not None:
                value = v_elem.text
                
                # Если это ссылка на shared string
                if cell_type == 's' and value and value.isdigit():
                    string_idx = int(value)
                    if string_idx in self.shared_strings:
                        value = self.shared_strings[string_idx]
                
                row_data[col_letter] = value
        
        return row_data
    
    def convert_to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """Конвертация в DataFrame для совместимости"""
        if not data:
            return pd.DataFrame()
        
        df_data = []
        for item in data:
            df_data.append({
                'nomenclature': item['nomenclature'],
                'category': item['category'], 
                'subcategory': item['subcategory'],
                'annual_sales': item['total_sales'],
                'row_number': item['row_number'],
                'has_subcategory': item['has_subcategory']
            })
        
        return pd.DataFrame(df_data)
    
    def analyze_subcategory_structure(self, file_path: str) -> Dict:
        """Анализ структуры подкатегорий в файле"""
        data = self.read_xlsx_manual(file_path)
        
        if not data:
            return {'error': 'Не удалось прочитать данные'}
        
        df = self.convert_to_dataframe(data)
        
        # Статистика по подкатегориям
        subcategory_stats = {}
        
        for category in df['category'].unique():
            cat_data = df[df['category'] == category]
            
            # Подкатегории в этой категории
            subcategories = cat_data['subcategory'].unique()
            
            subcategory_stats[category] = {
                'total_items': len(cat_data),
                'subcategories': list(subcategories),
                'subcategories_count': len(subcategories),
                'items_with_subcategory': len(cat_data[cat_data['has_subcategory']]),
                'items_without_subcategory': len(cat_data[~cat_data['has_subcategory']]),
                'total_sales': cat_data['annual_sales'].sum(),
                'avg_sales_per_item': cat_data['annual_sales'].mean()
            }
        
        # Общая статистика
        summary = {
            'total_items': len(df),
            'total_categories': df['category'].nunique(),
            'total_subcategories': len(df[df['subcategory'] != 'Без подкатегории']['subcategory'].unique()),
            'items_with_subcategory': len(df[df['has_subcategory']]),
            'items_without_subcategory': len(df[~df['has_subcategory']]),
            'subcategory_coverage': len(df[df['has_subcategory']]) / len(df) * 100 if len(df) > 0 else 0
        }
        
        return {
            'summary': summary,
            'by_category': subcategory_stats,
            'sample_data': df.head(10).to_dict('records')
        }

def test_correct_reader():
    """Тест исправленного чтения подкатегорий"""
    print("=" * 80)
    print("ТЕСТ ИСПРАВЛЕННОГО ЧТЕНИЯ ПОДКАТЕГОРИЙ")
    print("=" * 80)
    
    reader = CorrectSubcategoryReader()
    file_path = "общ_продажи_по_всем_складам_с_01_07_2024_01_07_2025_гг.xlsx"
    
    try:
        # Анализируем структуру
        analysis = reader.analyze_subcategory_structure(file_path)
        
        if 'error' in analysis:
            print(f"❌ Ошибка: {analysis['error']}")
            return
        
        summary = analysis['summary']
        print("📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   • Всего товаров: {summary['total_items']}")
        print(f"   • Категорий: {summary['total_categories']}")
        print(f"   • Подкатегорий: {summary['total_subcategories']}")
        print(f"   • Товаров с подкатегорией: {summary['items_with_subcategory']} ({summary['subcategory_coverage']:.1f}%)")
        print(f"   • Товаров без подкатегории: {summary['items_without_subcategory']}")
        
        print("\n📋 ДЕТАЛИ ПО КАТЕГОРИЯМ:")
        for category, stats in analysis['by_category'].items():
            if stats['subcategories_count'] > 1:  # Показываем только категории с подкатегориями
                print(f"\n🏷️ {category}:")
                print(f"   • Всего товаров: {stats['total_items']}")
                print(f"   • Подкатегорий: {stats['subcategories_count']}")
                print(f"   • С подкатегорией: {stats['items_with_subcategory']}")
                print(f"   • Без подкатегории: {stats['items_without_subcategory']}")
                print(f"   • Подкатегории: {', '.join(stats['subcategories'][:5])}{'...' if len(stats['subcategories']) > 5 else ''}")
        
        print("\n📝 ПРИМЕРЫ ТОВАРОВ С ПОДКАТЕГОРИЯМИ:")
        sample_data = analysis['sample_data']
        for item in sample_data[:10]:
            if item['has_subcategory']:
                print(f"   • {item['nomenclature'][:50]}...")
                print(f"     Категория: {item['category']}")
                print(f"     Подкатегория: {item['subcategory']}")
                print(f"     Продажи: {item['annual_sales']:,.0f}")
                print()
        
        print("✅ АНАЛИЗ ЗАВЕРШЕН!")
        
        # Сравниваем со старым методом
        print("\n" + "=" * 80)
        print("СРАВНЕНИЕ СО СТАРЫМ МЕТОДОМ ЧТЕНИЯ:")
        print("=" * 80)
        
        # Пробуем старый метод (если pandas доступен)
        try:
            old_df = pd.read_excel(file_path, engine='openpyxl')
            print("📊 СТАРЫЙ МЕТОД:")
            print(f"   • Размер: {old_df.shape}")
            print(f"   • Колонки: {list(old_df.columns)}")
            
            # Старый метод берет данные с строки 5 и колонки: nomenclature, subcategory, category, annual_sales
            if len(old_df) > 5:
                old_processed = old_df.iloc[5:].copy()
                old_processed.columns = ['nomenclature', 'subcategory', 'category', 'annual_sales'] + list(old_processed.columns[4:])
                
                print(f"📊 СТАРЫЙ МЕТОД (обработанный):")
                print(f"   • Товаров после обработки: {len(old_processed)}")
                print(f"   • Первая 'подкатегория': {old_processed.iloc[0]['subcategory'] if len(old_processed) > 0 else 'N/A'}")
                print(f"   • Первая 'категория': {old_processed.iloc[0]['category'] if len(old_processed) > 0 else 'N/A'}")
                
                print("\n❌ ПРОБЛЕМА СТАРОГО МЕТОДА:")
                print("   Старый код берет:")
                print("   • 'subcategory' = колонка B (ПОДКАТЕГОРИЯ) - но это категория!")
                print("   • 'category' = колонка C (Номенклатура) - но это номенклатура!")
                print("\n✅ НОВЫЙ МЕТОД ПРАВИЛЬНО ОПРЕДЕЛЯЕТ:")
                print("   • Категория = колонка A")
                print("   • Подкатегория = колонка B (только если колонка C пустая)")
                print("   • Номенклатура = колонка C")
                
        except Exception as e:
            print(f"Не удалось выполнить сравнение со старым методом: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_correct_reader()