#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система накопления и инкрементального обновления данных из вебхуков
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List, Optional
import hashlib

class WebhookDataAccumulator:
    """Накапливает данные из вебхуков с сохранением истории"""
    
    def __init__(self, db_path: str = "webhook_data.db", webhook_dir: str = "./webhook_uploads"):
        self.db_path = db_path
        self.webhook_dir = Path(webhook_dir)
        self.logger = logging.getLogger(__name__)
        
        # Инициализация БД
        self._init_database()
        
    def _init_database(self):
        """Создание таблиц для хранения исторических данных"""
        with sqlite3.connect(self.db_path) as conn:
            # Таблица продаж
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    branch TEXT NOT NULL,
                    item_code TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT,
                    category_path TEXT,
                    data_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, branch, item_code, data_hash)
                )
            """)
            
            # Таблица остатков
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    warehouse TEXT NOT NULL,
                    item_code TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, warehouse, item_code)
                )
            """)
            
            # Таблица метаданных загрузок
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upload_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    records_processed INTEGER,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success',
                    error_message TEXT
                )
            """)
            
            # Индексы для быстрого поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_branch ON sales(branch)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_date ON stock(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON stock(warehouse)")
            
    def process_new_sales_file(self, filepath: Path) -> Dict:
        """Обработка нового файла продаж с добавлением в БД"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records_added = 0
            duplicates_skipped = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for branch_data in data:
                    branch = branch_data.get('Филиал', '')
                    daily_sales = branch_data.get('ПродажиПоДням', {})
                    
                    for date_str, sales_items in daily_sales.items():
                        for item in sales_items:
                            # Создаем хеш для определения уникальности записи
                            data_str = f"{date_str}{branch}{item.get('Код', '')}{item.get('Количество', 0)}{item.get('Сумма', 0)}"
                            data_hash = hashlib.md5(data_str.encode()).hexdigest()
                            
                            try:
                                conn.execute("""
                                    INSERT INTO sales (date, branch, item_code, item_name, quantity, amount, category, category_path, data_hash)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    date_str,
                                    branch,
                                    item.get('Код', ''),
                                    item.get('Номенклатура', ''),
                                    float(item.get('Количество', 0)),
                                    float(item.get('Сумма', 0)),
                                    item.get('Категория', 'Без категории'),
                                    item.get('ПутьКатегорий', ''),
                                    data_hash
                                ))
                                records_added += 1
                            except sqlite3.IntegrityError:
                                # Запись уже существует
                                duplicates_skipped += 1
                
                # Сохраняем информацию о загрузке
                start_date = data[0].get('НачалоПериода') if data else None
                end_date = data[0].get('КонецПериода') if data else None
                
                conn.execute("""
                    INSERT INTO upload_history (upload_type, filename, start_date, end_date, records_processed)
                    VALUES (?, ?, ?, ?, ?)
                """, ('sales', filepath.name, start_date, end_date, records_added))
                
            self.logger.info(f"Обработано продаж: {records_added} новых, {duplicates_skipped} пропущено")
            
            return {
                'status': 'success',
                'records_added': records_added,
                'duplicates_skipped': duplicates_skipped,
                'filename': filepath.name
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла продаж: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_new_stock_file(self, filepath: Path) -> Dict:
        """Обработка нового файла остатков с обновлением в БД"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stock_date = data.get('ДатаОстатков', '').split('T')[0]
            records_updated = 0
            
            with sqlite3.connect(self.db_path) as conn:
                # Удаляем старые остатки за эту дату
                conn.execute("DELETE FROM stock WHERE date = ?", (stock_date,))
                
                # Добавляем новые
                for warehouse_data in data.get('ОстаткиПоСкладам', []):
                    warehouse = warehouse_data.get('Склад', '')
                    
                    for item in warehouse_data.get('Остатки', []):
                        conn.execute("""
                            INSERT INTO stock (date, warehouse, item_code, item_name, quantity, price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            stock_date,
                            warehouse,
                            item.get('Код', ''),
                            item.get('Номенклатура', ''),
                            float(item.get('Количество', 0)),
                            float(item.get('Цена', 0)) if 'Цена' in item else None
                        ))
                        records_updated += 1
                
                # Сохраняем информацию о загрузке
                conn.execute("""
                    INSERT INTO upload_history (upload_type, filename, start_date, end_date, records_processed)
                    VALUES (?, ?, ?, ?, ?)
                """, ('stock', filepath.name, stock_date, stock_date, records_updated))
            
            self.logger.info(f"Обновлено остатков: {records_updated} записей")
            
            return {
                'status': 'success',
                'records_updated': records_updated,
                'date': stock_date,
                'filename': filepath.name
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла остатков: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_sales_data(self, start_date: str = None, end_date: str = None, branches: List[str] = None) -> pd.DataFrame:
        """Получение данных о продажах из БД"""
        query = "SELECT * FROM sales WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        if branches:
            placeholders = ','.join(['?' for _ in branches])
            query += f" AND branch IN ({placeholders})"
            params.extend(branches)
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def get_latest_stock(self, warehouses: List[str] = None) -> pd.DataFrame:
        """Получение последних остатков из БД"""
        # Находим последнюю дату остатков
        with sqlite3.connect(self.db_path) as conn:
            latest_date_query = "SELECT MAX(date) as latest_date FROM stock"
            latest_date = pd.read_sql_query(latest_date_query, conn).iloc[0]['latest_date']
            
            if not latest_date:
                return pd.DataFrame()
            
            query = "SELECT * FROM stock WHERE date = ?"
            params = [latest_date]
            
            if warehouses:
                placeholders = ','.join(['?' for _ in warehouses])
                query += f" AND warehouse IN ({placeholders})"
                params.extend(warehouses)
            
            return pd.read_sql_query(query, conn, params=params)
    
    def get_data_summary(self) -> Dict:
        """Получение сводной информации о данных в БД"""
        with sqlite3.connect(self.db_path) as conn:
            summary = {}
            
            # Информация о продажах
            sales_info = pd.read_sql_query("""
                SELECT 
                    COUNT(DISTINCT date) as days_count,
                    COUNT(DISTINCT branch) as branches_count,
                    COUNT(DISTINCT item_code) as items_count,
                    MIN(date) as first_date,
                    MAX(date) as last_date,
                    COUNT(*) as total_records
                FROM sales
            """, conn).to_dict('records')[0]
            
            # Информация об остатках
            stock_info = pd.read_sql_query("""
                SELECT 
                    COUNT(DISTINCT date) as snapshots_count,
                    COUNT(DISTINCT warehouse) as warehouses_count,
                    MAX(date) as latest_date,
                    COUNT(*) as total_records
                FROM stock
            """, conn).to_dict('records')[0]
            
            # История загрузок
            uploads = pd.read_sql_query("""
                SELECT upload_type, COUNT(*) as count, MAX(upload_time) as last_upload
                FROM upload_history
                GROUP BY upload_type
            """, conn)
            
            summary['sales'] = sales_info
            summary['stock'] = stock_info
            summary['uploads'] = uploads.to_dict('records')
            
            return summary
    
    def monitor_and_process_new_files(self):
        """Мониторинг директории вебхуков и обработка новых файлов"""
        processed_files = set()
        
        # Получаем список уже обработанных файлов
        with sqlite3.connect(self.db_path) as conn:
            existing = pd.read_sql_query(
                "SELECT DISTINCT filename FROM upload_history", 
                conn
            )
            if not existing.empty:
                processed_files = set(existing['filename'].tolist())
        
        # Проверяем новые файлы
        for filepath in self.webhook_dir.glob('*.json'):
            if filepath.name not in processed_files:
                self.logger.info(f"Найден новый файл: {filepath.name}")
                
                if filepath.name.startswith('sales_'):
                    self.process_new_sales_file(filepath)
                elif filepath.name.startswith('stock_'):
                    self.process_new_stock_file(filepath)
                
                processed_files.add(filepath.name)
    
    def check_missing_dates(self) -> List[str]:
        """Проверка пропущенных дат в данных"""
        with sqlite3.connect(self.db_path) as conn:
            # Получаем диапазон дат
            date_range = pd.read_sql_query("""
                SELECT MIN(date) as start_date, MAX(date) as end_date
                FROM sales
            """, conn).iloc[0]
            
            if pd.isna(date_range['start_date']):
                return []
            
            # Генерируем полный список дат
            start = pd.to_datetime(date_range['start_date'])
            end = pd.to_datetime(date_range['end_date'])
            all_dates = pd.date_range(start, end, freq='D')
            
            # Получаем существующие даты
            existing_dates = pd.read_sql_query(
                "SELECT DISTINCT date FROM sales", 
                conn
            )['date'].tolist()
            existing_dates = pd.to_datetime(existing_dates)
            
            # Находим пропущенные
            missing_dates = [d.strftime('%Y-%m-%d') for d in all_dates if d not in existing_dates]
            
            return missing_dates


# Функция для интеграции с вебхук-сервером
def setup_auto_processing(accumulator: WebhookDataAccumulator):
    """Настройка автоматической обработки новых файлов"""
    import threading
    import time
    
    def monitor_loop():
        while True:
            try:
                accumulator.monitor_and_process_new_files()
            except Exception as e:
                logging.error(f"Ошибка в мониторинге: {e}")
            
            time.sleep(60)  # Проверка каждую минуту
    
    # Запускаем в отдельном потоке
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    return monitor_thread