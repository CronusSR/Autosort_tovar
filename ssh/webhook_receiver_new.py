#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный webhook_receiver с поддержкой ZIP файлов
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
from webhook_zip_handler import handle_zip_upload

# Загружаем переменные окружения
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
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'furniture_company_secret_key_2025')
UPLOAD_DIR = Path('./webhook_uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

logging.info(f"Webhook сервер запущен. Директория: {UPLOAD_DIR}")

def verify_signature(payload_body, signature_header):
    """Проверка подписи webhook"""
    if not signature_header:
        return False
    
    try:
        sha_name, signature = signature_header.split('=')
        if sha_name != 'sha256':
            return False
        
        mac = hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), signature)
    except Exception as e:
        logging.error(f"Ошибка проверки подписи: {e}")
        return False

def validate_sales_file(data):
    """Валидация файла продаж (поддержка обеих структур)"""
    try:
        if not isinstance(data, list) or len(data) == 0:
            return False, "Данные должны быть непустым массивом"
        
        first_item = data[0]
        
        # Проверяем новую структуру (с ZIP)
        if 'Продажи' in first_item:
            required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'Продажи']
            for field in required_fields:
                if field not in first_item:
                    return False, f"Отсутствует обязательное поле: {field}"
            return True, "OK"
        
        # Проверяем старую структуру
        elif 'ПродажиПоДням' in first_item:
            required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'ПродажиПоДням']
            for field in required_fields:
                if field not in first_item:
                    return False, f"Отсутствует обязательное поле: {field}"
            return True, "OK"
        
        else:
            return False, "Неизвестная структура данных"
            
    except Exception as e:
        return False, f"Ошибка валидации: {str(e)}"

def validate_stock_file(data):
    """Валидация файла остатков"""
    try:
        required_fields = ['ДатаОстатков', 'ДатаВыгрузки', 'ОстаткиПоСкладам']
        for field in required_fields:
            if field not in data:
                return False, f"Отсутствует обязательное поле: {field}"
        
        if not isinstance(data['ОстаткиПоСкладам'], list):
            return False, "ОстаткиПоСкладам должно быть массивом"
        
        return True, "OK"
    except Exception as e:
        return False, f"Ошибка валидации: {str(e)}"

@app.route('/webhook/sales', methods=['POST'])
def receive_sales_data():
    """Получение данных о продажах (поддержка JSON и ZIP)"""
    try:
        # Проверка подписи
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook")
            return jsonify({'error': 'Неверная подпись'}), 401
        
        content_type = request.headers.get('Content-Type', '')
        
        # Обработка ZIP файла
        if 'application/zip' in content_type or 'application/x-zip' in content_type:
            logging.info("Получен ZIP архив с данными продаж")
            
            zip_data = request.data
            if not zip_data:
                return jsonify({'error': 'Пустой ZIP архив'}), 400
            
            # Обрабатываем ZIP
            result = handle_zip_upload(zip_data, "sales_data.zip")
            
            if result['status'] == 'error':
                logging.error(f"Ошибка обработки ZIP: {result['message']}")
                return jsonify({'error': result['message']}), 400
            
            logging.info(f"ZIP обработан: {result['files_processed']} файлов, {result['total_records']} записей")
            
            # Интеграция с накопителем данных
            try:
                from webhook_data_accumulator import WebhookDataAccumulator
                accumulator = WebhookDataAccumulator()
                
                # Обрабатываем каждый файл накопителем
                for file_info in result.get('files', []):
                    file_path = Path(file_info['saved_path'])
                    acc_result = accumulator.process_new_sales_file(file_path)
                    logging.info(f"Накопитель обработал {file_info['filename']}: {acc_result}")
                    
            except ImportError:
                logging.warning("Модуль накопителя данных не найден")
            except Exception as e:
                logging.error(f"Ошибка при работе с накопителем: {e}")
            
            return jsonify({
                'status': 'success',
                'message': 'ZIP архив обработан успешно',
                'files_processed': result['files_processed'],
                'total_records': result['total_records'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Обработка обычного JSON
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Нет данных'}), 400
            
            # Валидация
            is_valid, message = validate_sales_file(data)
            if not is_valid:
                logging.error(f"Ошибка валидации: {message}")
                return jsonify({'error': message}), 400
            
            # Определение имени файла
            if data and len(data) > 0:
                start_date = data[0].get('НачалоПериода', '').split('T')[0]
                end_date = data[0].get('КонецПериода', '').split('T')[0]
                branch = data[0].get('Филиал', 'unknown')
                branch_short = branch.replace(' ', '_').replace('"', '')[:20]
                filename = f"sales_{start_date}_{end_date}_{branch_short}.json"
            else:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filename = f"sales_{timestamp}.json"
            
            # Сохранение
            file_path = UPLOAD_DIR / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Получен JSON файл продаж: {filename}")
            
            # Интеграция с накопителем
            try:
                from webhook_data_accumulator import WebhookDataAccumulator
                accumulator = WebhookDataAccumulator()
                result = accumulator.process_new_sales_file(file_path)
                logging.info(f"Накопитель: {result}")
            except Exception as e:
                logging.error(f"Ошибка накопителя: {e}")
            
            return jsonify({
                'status': 'success',
                'message': 'JSON файл продаж получен и сохранен',
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logging.error(f"Ошибка при получении данных продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/stock', methods=['POST'])
def receive_stock_data():
    """Получение данных об остатках"""
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
        
        # Валидация
        is_valid, message = validate_stock_file(data)
        if not is_valid:
            logging.error(f"Ошибка валидации остатков: {message}")
            return jsonify({'error': message}), 400
        
        # Определение имени файла
        stock_date = data.get('ДатаОстатков', '').split('T')[0]
        filename = f"stock_{stock_date}.json" if stock_date else f"stock_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        # Сохранение
        file_path = UPLOAD_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Получен файл остатков: {filename}")
        
        # Интеграция с накопителем
        try:
            from webhook_data_accumulator import WebhookDataAccumulator
            accumulator = WebhookDataAccumulator()
            result = accumulator.process_new_stock_file(file_path)
            logging.info(f"Накопитель остатков: {result}")
        except Exception as e:
            logging.error(f"Ошибка накопителя остатков: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл остатков получен и сохранен',
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении остатков: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Проверка статуса webhook сервера"""
    try:
        # Список файлов
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
            'upload_directory': str(UPLOAD_DIR),
            'recent_files': files[:10],
            'total_files': len(files),
            'supported_formats': ['JSON', 'ZIP'],
            'version': '2.0 (ZIP support)'
        })
        
    except Exception as e:
        logging.error(f"Ошибка статуса: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/files', methods=['GET'])
def list_files():
    """Список загруженных файлов"""
    try:
        files = []
        for file_path in UPLOAD_DIR.glob('*.json'):
            stat = file_path.stat()
            files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'sales' if 'sales' in file_path.name else 'stock'
            })
        
        return jsonify({
            'files': sorted(files, key=lambda x: x['modified'], reverse=True),
            'total': len(files)
        })
        
    except Exception as e:
        logging.error(f"Ошибка списка файлов: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Запуск в продакшене используйте gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)