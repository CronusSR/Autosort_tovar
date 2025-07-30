#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработчик ZIP архивов с данными от 1С
Поддерживает новую структуру данных
"""

import zipfile
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import shutil

class WebhookZipHandler:
    """Обработчик ZIP архивов от 1С"""
    
    def __init__(self, upload_dir: str = "./webhook_uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def process_zip_file(self, zip_data: bytes, filename: str = None) -> Dict:
        """Обработка ZIP архива с данными"""
        try:
            # Создаем временную директорию
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Сохраняем ZIP файл
                zip_path = temp_path / "data.zip"
                with open(zip_path, 'wb') as f:
                    f.write(zip_data)
                
                # Извлекаем архив
                extract_path = temp_path / "extracted"
                extract_path.mkdir()
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Находим JSON файлы
                json_files = list(extract_path.rglob("*.json"))
                
                if not json_files:
                    return {
                        'status': 'error',
                        'message': 'JSON файлы не найдены в архиве'
                    }
                
                processed_files = []
                total_records = 0
                
                # Обрабатываем каждый JSON файл
                for json_file in json_files:
                    result = self._process_single_json(json_file)
                    if result['status'] == 'success':
                        processed_files.append(result)
                        total_records += result.get('records_count', 0)
                
                return {
                    'status': 'success',
                    'message': f'Обработано {len(processed_files)} файлов',
                    'files_processed': len(processed_files),
                    'total_records': total_records,
                    'files': processed_files
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки ZIP файла: {e}")
            return {
                'status': 'error',
                'message': f'Ошибка обработки: {str(e)}'
            }
    
    def _process_single_json(self, json_file_path: Path) -> Dict:
        """Обработка одного JSON файла"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Валидация новой структуры
            if not self._validate_new_structure(data):
                return {
                    'status': 'error',
                    'message': f'Неверная структура файла {json_file_path.name}'
                }
            
            # Преобразуем в стандартный формат
            converted_data = self._convert_to_standard_format(data)
            
            # Определяем имя файла для сохранения
            original_name = json_file_path.name
            if not original_name:
                # Пытаемся определить из данных
                if data and len(data) > 0:
                    start_date = data[0].get('НачалоПериода', '').split('T')[0]
                    end_date = data[0].get('КонецПериода', '').split('T')[0]
                    branch = data[0].get('Филиал', 'unknown')
                    branch_short = branch.replace(' ', '_').replace('"', '')[:20]
                    original_name = f"sales_{start_date}_{end_date}_{branch_short}.json"
                else:
                    original_name = f"sales_{json_file_path.stem}.json"
            
            # Сохраняем в стандартной директории
            save_path = self.upload_dir / original_name
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Обработан файл: {original_name}")
            
            return {
                'status': 'success',
                'filename': original_name,
                'records_count': self._count_records(data),
                'saved_path': str(save_path)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла {json_file_path}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _validate_new_structure(self, data: List) -> bool:
        """Валидация новой структуры данных"""
        try:
            if not isinstance(data, list) or len(data) == 0:
                return False
            
            first_item = data[0]
            required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'Продажи']
            
            for field in required_fields:
                if field not in first_item:
                    return False
            
            # Проверяем структуру продаж
            if not isinstance(first_item['Продажи'], list):
                return False
            
            if len(first_item['Продажи']) > 0:
                sale_day = first_item['Продажи'][0]
                if 'День' not in sale_day or 'ПродажиПоДням' not in sale_day:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _convert_to_standard_format(self, data: List) -> List:
        """Преобразование новой структуры в стандартный формат"""
        converted = []
        
        for branch_data in data:
            # Создаем структуру продаж по дням
            sales_by_days = {}
            
            for sale_period in branch_data.get('Продажи', []):
                day = sale_period.get('День')
                if not day:
                    continue
                
                day_sales = []
                for item in sale_period.get('ПродажиПоДням', []):
                    # Преобразуем в старый формат
                    converted_item = {
                        'Код': item.get('Артикул', ''),
                        'Номенклатура': item.get('Номенклатура', ''),
                        'Количество': item.get('Количество', 0),
                        'Сумма': item.get('Выручка', 0),  # Выручка → Сумма
                        'Категория': self._extract_category(item.get('ПутьКатегорий', '')),
                        'ПутьКатегорий': item.get('ПутьКатегорий', ''),
                        'ЕдиницаИзмерения': item.get('ЕдиницаИзмерения', ''),
                        'Производитель': item.get('Производитель', ''),
                        'Себестоимость': item.get('Себестоимость', 0),
                        'ВаловаяПрибыль': item.get('ВаловаяПрибыль', 0),
                        'Рентабельность': item.get('Рентабельность', 0)
                    }
                    day_sales.append(converted_item)
                
                sales_by_days[day] = day_sales
            
            # Создаем итоги за период
            period_totals = self._calculate_period_totals(sales_by_days)
            
            # Формируем конечную структуру
            converted_branch = {
                'ВерсияФормата': '2.1',  # Помечаем новую версию
                'ДатаВыгрузки': branch_data.get('ДатаВыгрузки'),
                'НачалоПериода': branch_data.get('НачалоПериода'),
                'КонецПериода': branch_data.get('КонецПериода'),
                'Филиал': branch_data.get('Филиал'),
                'ПродажиПоДням': sales_by_days,
                'ИтогиЗаПериод': period_totals
            }
            
            converted.append(converted_branch)
        
        return converted
    
    def _extract_category(self, category_path: str) -> str:
        """Извлечение основной категории из пути категорий"""
        if not category_path:
            return 'Без категории'
        
        # Разбиваем путь и берем последнюю значимую категорию
        parts = [part.strip() for part in category_path.split('/') if part.strip()]
        
        # Исключаем общие категории
        exclude = ['Мебельная фурнитура', '']
        meaningful_parts = [part for part in parts if part not in exclude]
        
        if meaningful_parts:
            return meaningful_parts[-1]  # Последняя значимая категория
        elif parts:
            return parts[-2] if len(parts) > 1 else parts[0]  # Предпоследняя или первая
        
        return 'Без категории'
    
    def _calculate_period_totals(self, sales_by_days: Dict) -> List:
        """Расчет итогов за период"""
        totals = {}
        
        for day_sales in sales_by_days.values():
            for item in day_sales:
                code = item['Код']
                
                if code not in totals:
                    totals[code] = {
                        'Код': code,
                        'Номенклатура': item['Номенклатура'],
                        'ОбщееКоличество': 0,
                        'ОбщаяСумма': 0,
                        'Категория': item['Категория'],
                        'ПутьКатегорий': item['ПутьКатегорий']
                    }
                
                totals[code]['ОбщееКоличество'] += item['Количество']
                totals[code]['ОбщаяСумма'] += item['Сумма']
        
        return list(totals.values())
    
    def _count_records(self, data: List) -> int:
        """Подсчет количества записей"""
        count = 0
        for branch_data in data:
            for sale_period in branch_data.get('Продажи', []):
                count += len(sale_period.get('ПродажиПоДням', []))
        return count


# Функция для интеграции с существующим webhook_receiver
def handle_zip_upload(zip_data: bytes, filename: str = None) -> Dict:
    """Обработка ZIP загрузки"""
    handler = WebhookZipHandler()
    return handler.process_zip_file(zip_data, filename)