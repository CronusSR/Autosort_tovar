#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook система для автоматической загрузки файлов от 1С
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import hashlib
import hmac
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Конфигурация
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your_secret_key_here')  # Читаем из .env
UPLOAD_DIR = Path('./webhook_uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

logging.info(f"Webhook сервер настроен. Директория загрузок: {UPLOAD_DIR}")
logging.info(f"Секретный ключ загружен: {'Да' if WEBHOOK_SECRET != 'your_secret_key_here' else 'Нет (используется дефолтный)'}")

def verify_signature(payload_body, signature_header):
    """Проверка подписи webhook для безопасности"""
    if not signature_header:
        return False
    
    try:
        sha_name, signature = signature_header.split('=')
        if sha_name != 'sha256':
            return False
        
        mac = hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256)
        expected_signature = mac.hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logging.error(f"Ошибка проверки подписи: {e}")
        return False

def validate_sales_file(data):
    """Валидация структуры файла продаж"""
    if not isinstance(data, list):
        return False, "Файл продаж должен быть массивом"
    
    for branch_data in data:
        required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'ПродажиПоДням', 'ИтогиЗаПериод']
        for field in required_fields:
            if field not in branch_data:
                return False, f"Отсутствует поле {field} в данных филиала"
    
    return True, "OK"

def validate_stock_file(data):
    """Валидация структуры файла остатков"""
    if not isinstance(data, dict):
        return False, "Файл остатков должен быть объектом"
    
    required_fields = ['ДатаОстатков', 'ДатаВыгрузки', 'ОстаткиПоСкладам']
    for field in required_fields:
        if field not in data:
            return False, f"Отсутствует поле {field}"
    
    if not isinstance(data['ОстаткиПоСкладам'], list):
        return False, "ОстаткиПоСкладам должен быть массивом"
    
    return True, "OK"

@app.route('/webhook/sales', methods=['POST'])
def receive_sales_data():
    """Получение файла продаж от 1С"""
    try:
        # Проверка подписи
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook")
            return jsonify({'error': 'Неверная подпись'}), 401
        
        # Получение данных
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация структуры
        is_valid, message = validate_sales_file(data)
        if not is_valid:
            logging.error(f"Ошибка валидации файла продаж: {message}")
            return jsonify({'error': message}), 400
        
        # Определение периода из данных
        if data and len(data) > 0:
            start_date = data[0].get('НачалоПериода', '')
            end_date = data[0].get('КонецПериода', '')
            filename = f"sales_{start_date}_{end_date}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"sales_{timestamp}.json"
        
        # Сохранение файла
        file_path = UPLOAD_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Получен файл продаж: {filename}")
        
        # Отправляем уведомление (можно добавить интеграцию с Telegram/email)
        return jsonify({
            'status': 'success',
            'message': 'Файл продаж получен и сохранен',
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Ошибка при получении файла продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/stock', methods=['POST'])
def receive_stock_data():
    """Получение файла остатков от 1С"""
    try:
        # Проверка подписи
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook")
            return jsonify({'error': 'Неверная подпись'}), 401
        
        # Получение данных
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация структуры
        is_valid, message = validate_stock_file(data)
        if not is_valid:
            logging.error(f"Ошибка валидации файла остатков: {message}")
            return jsonify({'error': message}), 400
        
        # Определение даты из данных
        stock_date = data.get('ДатаОстатков', '')
        if stock_date:
            # Извлекаем дату в формате YYYY-MM-DD
            date_part = stock_date.split('T')[0] if 'T' in stock_date else stock_date
            filename = f"stock_{date_part}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f"stock_{timestamp}.json"
        
        # Сохранение файла
        file_path = UPLOAD_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Получен файл остатков: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл остатков получен и сохранен',
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Ошибка при получении файла остатков: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Проверка статуса webhook сервиса"""
    # Список последних загруженных файлов
    files = []
    for file_path in UPLOAD_DIR.glob('*.json'):
        stat = file_path.stat()
        files.append({
            'name': file_path.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'upload_dir': str(UPLOAD_DIR),
        'recent_files': files[:10]  # Последние 10 файлов
    })

@app.route('/webhook/files', methods=['GET'])
def list_files():
    """Список всех загруженных файлов"""
    files = {
        'sales': [],
        'stock': []
    }
    
    for file_path in UPLOAD_DIR.glob('*.json'):
        stat = file_path.stat()
        file_info = {
            'name': file_path.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'path': str(file_path)
        }
        
        if file_path.name.startswith('sales_'):
            files['sales'].append(file_info)
        elif file_path.name.startswith('stock_'):
            files['stock'].append(file_info)
    
    # Сортируем по дате изменения
    files['sales'].sort(key=lambda x: x['modified'], reverse=True)
    files['stock'].sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify(files)

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logging.info(f"Запуск webhook сервера на порту {port}")
    logging.info(f"Директория загрузок: {UPLOAD_DIR}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)