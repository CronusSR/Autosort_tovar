#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный парсер для новой структуры файлов от 1С с поддержкой webhook
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDataParser:
    """Парсер для новой структуры файлов от 1С"""
    
    def __init__(self, webhook_dir="./webhook_uploads"):
        self.webhook_dir = Path(webhook_dir)
        self.webhook_dir.mkdir(exist_ok=True)
    
    def parse_new_sales_data(self, sales_data):
        """
        Парсит новую структуру файла продаж с ПродажиПоДням и ИтогиЗаПериод
        """
        sales_records = []
        
        try:
            for branch_data in sales_data:
                branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
                start_date = branch_data.get('НачалоПериода')
                end_date = branch_data.get('КонецПериода')
                
                # Используем ИтогиЗаПериод для агрегированных данных
                # Это более эффективно чем обработка ПродажиПоДням
                for item in branch_data.get('ИтогиЗаПериод', []):
                    record = {
                        'branch': branch_name,
                        'category_path': item.get('ПутьКатегорий', ''),
                        'product': item.get('Номенклатура', ''),
                        'article': item.get('Артикул', ''),
                        'quantity': item.get('ОбщееКоличество', 0),
                        'revenue': item.get('ОбщаяВыручка', 0),
                        'cost': item.get('ОбщаяСебестоимость', 0),  # Ключевое поле для расчетов
                        'profit': item.get('ОбщаяПрибыль', 0),
                        'margin': item.get('СредняяРентабельность', 0),
                        'unit': item.get('ЕдиницаИзмерения', ''),
                        'manufacturer': item.get('Производитель', ''),
                        'period_start': start_date,
                        'period_end': end_date
                    }
                    sales_records.append(record)
            
            df = pd.DataFrame(sales_records)
            
            # Определяем период в днях
            if sales_records and start_date and end_date:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                period_days = (end - start).days + 1
            else:
                period_days = 30  # По умолчанию
            
            logger.info(f"Обработано {len(sales_records)} записей продаж за {period_days} дней")
            return df, period_days
            
        except Exception as e:
            logger.error(f"Ошибка парсинга файла продаж: {e}")
            return pd.DataFrame(), 30
    
    def parse_daily_sales_data(self, sales_data):
        """
        Парсит детальные продажи по дням из ПродажиПоДням (если нужна детализация)
        """
        daily_records = []
        
        try:
            for branch_data in sales_data:
                branch_name = branch_data.get('Филиал', 'Неизвестный филиал')
                sales_by_day = branch_data.get('ПродажиПоДням', {})
                
                for date_str, day_sales in sales_by_day.items():
                    for item in day_sales:
                        record = {
                            'branch': branch_name,
                            'date': date_str,
                            'category_path': item.get('ПутьКатегорий', ''),
                            'product': item.get('Номенклатура', ''),
                            'article': item.get('Артикул', ''),
                            'quantity': item.get('Количество', 0),
                            'revenue': item.get('Выручка', 0),
                            'cost': item.get('Себестоимость', 0),
                            'profit': item.get('ВаловаяПрибыль', 0),
                            'margin': item.get('Рентабельность', 0),
                            'unit': item.get('ЕдиницаИзмерения', ''),
                            'manufacturer': item.get('Производитель', '')
                        }
                        daily_records.append(record)
            
            df = pd.DataFrame(daily_records)
            logger.info(f"Обработано {len(daily_records)} ежедневных записей продаж")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ежедневных продаж: {e}")
            return pd.DataFrame()
    
    def parse_stock_data(self, stock_data):
        """
        Парсит файл остатков (структура остается прежней)
        """
        stock_records = []
        
        try:
            for warehouse in stock_data.get('ОстаткиПоСкладам', []):
                warehouse_name = warehouse.get('Склад', 'Неизвестный склад')
                
                for item in warehouse.get('Остатки', []):
                    record = {
                        'branch': warehouse_name,
                        'category_path': item.get('ПутьКатегорий', ''),
                        'product': item.get('Номенклатура', ''),
                        'article': item.get('Артикул', ''),
                        'quantity': item.get('Количество', 0),
                        'cost': item.get('Стоимость', 0),  # Себестоимость остатков
                        'average_price': self._parse_price(item.get('СредняяЦена', '0')),
                        'unit': item.get('ЕдиницаИзмерения', ''),
                        'manufacturer': item.get('Производитель', ''),
                        'stock_date': stock_data.get('ДатаОстатков', '')
                    }
                    stock_records.append(record)
            
            df = pd.DataFrame(stock_records)
            logger.info(f"Обработано {len(stock_records)} записей остатков")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка парсинга файла остатков: {e}")
            return pd.DataFrame()
    
    def _parse_price(self, price_str):
        """Парсит строку цены в число"""
        try:
            return float(str(price_str).replace(' ', '').replace(',', '.'))
        except:
            return 0.0
    
    def get_latest_files(self):
        """Получает последние файлы из директории webhook"""
        files = {
            'sales': None,
            'stock': None
        }
        
        # Ищем последние файлы
        sales_files = list(self.webhook_dir.glob('sales_*.json'))
        stock_files = list(self.webhook_dir.glob('stock_*.json'))
        
        if sales_files:
            files['sales'] = max(sales_files, key=lambda x: x.stat().st_mtime)
        
        if stock_files:
            files['stock'] = max(stock_files, key=lambda x: x.stat().st_mtime)
        
        return files
    
    def load_and_parse_latest_data(self):
        """Загружает и парсит последние данные из webhook директории"""
        files = self.get_latest_files()
        
        sales_df = pd.DataFrame()
        stock_df = pd.DataFrame()
        period_days = 30
        
        # Загружаем и парсим продажи
        if files['sales']:
            try:
                with open(files['sales'], 'r', encoding='utf-8') as f:
                    sales_data = json.load(f)
                sales_df, period_days = self.parse_new_sales_data(sales_data)
                logger.info(f"Загружен файл продаж: {files['sales'].name}")
            except Exception as e:
                logger.error(f"Ошибка загрузки файла продаж {files['sales']}: {e}")
        
        # Загружаем и парсим остатки
        if files['stock']:
            try:
                with open(files['stock'], 'r', encoding='utf-8') as f:
                    stock_data = json.load(f)
                stock_df = self.parse_stock_data(stock_data)
                logger.info(f"Загружен файл остатков: {files['stock'].name}")
            except Exception as e:
                logger.error(f"Ошибка загрузки файла остатков {files['stock']}: {e}")
        
        return sales_df, stock_df, period_days
    
    def get_file_info(self):
        """Получает информацию о доступных файлах"""
        files = self.get_latest_files()
        info = {}
        
        for file_type, file_path in files.items():
            if file_path:
                stat = file_path.stat()
                info[file_type] = {
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
            else:
                info[file_type] = {
                    'filename': None,
                    'exists': False
                }
        
        return info

# Глобальный экземпляр парсера
enhanced_parser = EnhancedDataParser()

def parse_enhanced_sales_data(sales_data):
    """Функция-обертка для совместимости"""
    return enhanced_parser.parse_new_sales_data(sales_data)

def parse_enhanced_stock_data(stock_data):
    """Функция-обертка для совместимости"""
    return enhanced_parser.parse_stock_data(stock_data)