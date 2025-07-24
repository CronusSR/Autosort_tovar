#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление webhook_receiver.py для работы с накопителем данных
"""

import os
import sys
from pathlib import Path

def update_webhook_receiver():
    """Добавляет интеграцию с накопителем данных в webhook_receiver.py"""
    
    # Код для добавления после сохранения файлов
    integration_code = '''
        # Интеграция с накопителем данных
        try:
            from webhook_data_accumulator import WebhookDataAccumulator
            accumulator = WebhookDataAccumulator()
            
            # Обрабатываем файл накопителем
            if filename.startswith('sales_'):
                result = accumulator.process_new_sales_file(file_path)
                logging.info(f"Накопитель: {result}")
            elif filename.startswith('stock_'):
                result = accumulator.process_new_stock_file(file_path)
                logging.info(f"Накопитель: {result}")
                
        except ImportError:
            logging.warning("Модуль накопителя данных не найден - работаем в обычном режиме")
        except Exception as e:
            logging.error(f"Ошибка при работе с накопителем: {e}")
'''
    
    # Читаем текущий файл
    receiver_path = Path('./webhook_receiver.py')
    if not receiver_path.exists():
        print("❌ Файл webhook_receiver.py не найден")
        return False
    
    with open(receiver_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, не добавлена ли уже интеграция
    if 'WebhookDataAccumulator' in content:
        print("✅ Интеграция с накопителем уже добавлена")
        return True
    
    # Находим места для вставки кода (после сохранения файлов)
    updated_content = content
    
    # Для эндпоинта продаж
    sales_marker = "logging.info(f\"Получен файл продаж: {filename}\")"
    if sales_marker in updated_content:
        updated_content = updated_content.replace(
            sales_marker,
            sales_marker + "\n" + integration_code
        )
    
    # Для эндпоинта остатков
    stock_marker = "logging.info(f\"Получен файл остатков: {filename}\")"
    if stock_marker in updated_content:
        # Избегаем дублирования кода
        if updated_content.count("WebhookDataAccumulator") < 1:
            updated_content = updated_content.replace(
                stock_marker,
                stock_marker + "\n" + integration_code
            )
    
    # Создаем резервную копию
    backup_path = Path('./webhook_receiver_backup.py')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Создана резервная копия: {backup_path}")
    
    # Сохраняем обновленный файл
    with open(receiver_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ webhook_receiver.py обновлен с поддержкой накопления данных")
    return True

if __name__ == "__main__":
    update_webhook_receiver()