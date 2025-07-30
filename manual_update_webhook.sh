#!/bin/bash
# Ручное обновление webhook на сервере

echo "🔧 Ручное обновление webhook на сервере"
echo "======================================="

echo "📋 Инструкции для обновления:"
echo ""
echo "1. Подключитесь к серверу:"
echo "   ssh root@217.114.1.117"
echo ""
echo "2. Перейдите в папку проекта:"
echo "   cd /opt/inventory_system"
echo ""
echo "3. Создайте резервную копию:"
echo "   cp webhook_receiver.py webhook_receiver_backup_\$(date +%Y%m%d_%H%M%S).py"
echo ""
echo "4. Создайте папки для раздельного хранения:"
echo "   mkdir -p webhook_uploads/sales"
echo "   mkdir -p webhook_uploads/stock"
echo "   mkdir -p webhook_uploads/archive"
echo ""
echo "5. Скопируйте код ниже в файл webhook_receiver.py:"
echo ""

# Выводим обновленный код
cat << 'MANUAL_CODE'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный webhook_receiver с раздельными папками для продаж и остатков
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
SALES_DIR = UPLOAD_DIR / 'sales'
STOCK_DIR = UPLOAD_DIR / 'stock'
ARCHIVE_DIR = UPLOAD_DIR / 'archive'

# Создаем папки если их нет
UPLOAD_DIR.mkdir(exist_ok=True)
SALES_DIR.mkdir(exist_ok=True)
STOCK_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)

logging.info(f"Webhook сервер запущен с раздельными папками:")
logging.info(f"  Продажи: {SALES_DIR}")
logging.info(f"  Остатки: {STOCK_DIR}")
logging.info(f"  Архив: {ARCHIVE_DIR}")

@app.route('/', methods=['GET'])
def index():
    """Главная страница с информацией о системе"""
    return jsonify({
        'service': 'Webhook для системы анализа складов',
        'version': '2.1 (раздельные папки)',
        'endpoints': {
            'sales': '/sales - прием данных о продажах',
            'stock': '/stock - прием данных об остатках',
            'status': '/webhook/status - статус системы',
            'files': '/webhook/files - список файлов'
        },
        'upload_structure': {
            'sales': str(SALES_DIR),
            'stock': str(STOCK_DIR),
            'archive': str(ARCHIVE_DIR)
        }
    })

@app.route('/sales', methods=['POST'])
def receive_sales_data():
    """Получение данных о продажах - сохранение в папку sales/"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Определение имени файла
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"sales_{timestamp}.json"
        
        # Сохранение в папку sales/
        file_path = SALES_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📊 Получен файл продаж: {filename} -> {SALES_DIR}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл продаж получен и сохранен',
            'filename': filename,
            'saved_to': 'sales/',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении данных продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock', methods=['POST'])
def receive_stock_data():
    """Получение данных об остатках - сохранение в папку stock/"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Определение имени файла
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"stock_{timestamp}.json"
        
        # Сохранение в папку stock/
        file_path = STOCK_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📦 Получен файл остатков: {filename} -> {STOCK_DIR}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл остатков получен и сохранен',
            'filename': filename,
            'saved_to': 'stock/',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении остатков: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Проверка статуса webhook сервера с информацией о папках"""
    try:
        # Список файлов продаж
        sales_files = []
        for file_path in SALES_DIR.glob('*.json'):
            stat = file_path.stat()
            sales_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'sales'
            })
        
        # Список файлов остатков
        stock_files = []
        for file_path in STOCK_DIR.glob('*.json'):
            stat = file_path.stat()
            stock_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'stock'
            })
        
        # Общий список (последние 10)
        all_files = sales_files + stock_files
        all_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'status': 'active',
            'version': '2.1 (раздельные папки)',
            'timestamp': datetime.now().isoformat(),
            'structure': {
                'upload_directory': str(UPLOAD_DIR),
                'sales_directory': str(SALES_DIR),
                'stock_directory': str(STOCK_DIR),
                'archive_directory': str(ARCHIVE_DIR)
            },
            'statistics': {
                'total_files': len(all_files),
                'sales_files': len(sales_files),
                'stock_files': len(stock_files)
            },
            'recent_files': all_files[:10],
            'supported_formats': ['JSON'],
            'endpoints': ['/sales', '/stock', '/webhook/status', '/webhook/files']
        })
        
    except Exception as e:
        logging.error(f"Ошибка статуса: {e}")
        return jsonify({'error': str(e)}), 500

# Обратная совместимость - старые эндпоинты
@app.route('/webhook/sales', methods=['POST'])
def old_sales_endpoint():
    """Старый эндпоинт для продаж - перенаправление"""
    return receive_sales_data()

@app.route('/webhook/stock', methods=['POST'])
def old_stock_endpoint():
    """Старый эндпоинт для остатков - перенаправление"""
    return receive_stock_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
MANUAL_CODE

echo ""
echo "6. Перезапустите webhook сервер:"
echo "   pkill -f webhook_receiver"
echo "   sleep 2"
echo "   nohup python3 webhook_receiver.py > webhook_5000.log 2>&1 &"
echo ""
echo "7. Проверьте работу:"
echo "   curl http://217.114.1.117:5000/"
echo "   curl http://217.114.1.117:5000/webhook/status"
echo "   ls -la webhook_uploads/"
echo ""
echo "✅ После этого система будет использовать новую структуру папок!"

# Также создаем файл с кодом для копирования
cat > webhook_receiver_new_version.py << 'FILE_CODE'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновленный webhook_receiver с раздельными папками для продаж и остатков
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
SALES_DIR = UPLOAD_DIR / 'sales'
STOCK_DIR = UPLOAD_DIR / 'stock'
ARCHIVE_DIR = UPLOAD_DIR / 'archive'

# Создаем папки если их нет
UPLOAD_DIR.mkdir(exist_ok=True)
SALES_DIR.mkdir(exist_ok=True)
STOCK_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)

logging.info(f"Webhook сервер запущен с раздельными папками:")
logging.info(f"  Продажи: {SALES_DIR}")
logging.info(f"  Остатки: {STOCK_DIR}")
logging.info(f"  Архив: {ARCHIVE_DIR}")

@app.route('/', methods=['GET'])
def index():
    """Главная страница с информацией о системе"""
    return jsonify({
        'service': 'Webhook для системы анализа складов',
        'version': '2.1 (раздельные папки)',
        'endpoints': {
            'sales': '/sales - прием данных о продажах',
            'stock': '/stock - прием данных об остатках',
            'status': '/webhook/status - статус системы',
            'files': '/webhook/files - список файлов'
        },
        'upload_structure': {
            'sales': str(SALES_DIR),
            'stock': str(STOCK_DIR),
            'archive': str(ARCHIVE_DIR)
        }
    })

@app.route('/sales', methods=['POST'])
def receive_sales_data():
    """Получение данных о продажах - сохранение в папку sales/"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Определение имени файла
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"sales_{timestamp}.json"
        
        # Сохранение в папку sales/
        file_path = SALES_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📊 Получен файл продаж: {filename} -> {SALES_DIR}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл продаж получен и сохранен',
            'filename': filename,
            'saved_to': 'sales/',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении данных продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock', methods=['POST'])
def receive_stock_data():
    """Получение данных об остатках - сохранение в папку stock/"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Определение имени файла
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"stock_{timestamp}.json"
        
        # Сохранение в папку stock/
        file_path = STOCK_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📦 Получен файл остатков: {filename} -> {STOCK_DIR}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл остатков получен и сохранен',
            'filename': filename,
            'saved_to': 'stock/',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении остатков: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/status', methods=['GET'])
def webhook_status():
    """Проверка статуса webhook сервера с информацией о папках"""
    try:
        # Список файлов продаж
        sales_files = []
        for file_path in SALES_DIR.glob('*.json'):
            stat = file_path.stat()
            sales_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'sales'
            })
        
        # Список файлов остатков
        stock_files = []
        for file_path in STOCK_DIR.glob('*.json'):
            stat = file_path.stat()
            stock_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'stock'
            })
        
        # Общий список (последние 10)
        all_files = sales_files + stock_files
        all_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'status': 'active',
            'version': '2.1 (раздельные папки)',
            'timestamp': datetime.now().isoformat(),
            'structure': {
                'upload_directory': str(UPLOAD_DIR),
                'sales_directory': str(SALES_DIR),
                'stock_directory': str(STOCK_DIR),
                'archive_directory': str(ARCHIVE_DIR)
            },
            'statistics': {
                'total_files': len(all_files),
                'sales_files': len(sales_files),
                'stock_files': len(stock_files)
            },
            'recent_files': all_files[:10],
            'supported_formats': ['JSON'],
            'endpoints': ['/sales', '/stock', '/webhook/status', '/webhook/files']
        })
        
    except Exception as e:
        logging.error(f"Ошибка статуса: {e}")
        return jsonify({'error': str(e)}), 500

# Обратная совместимость - старые эндпоинты
@app.route('/webhook/sales', methods=['POST'])
def old_sales_endpoint():
    """Старый эндпоинт для продаж - перенаправление"""
    return receive_sales_data()

@app.route('/webhook/stock', methods=['POST'])
def old_stock_endpoint():
    """Старый эндпоинт для остатков - перенаправление"""
    return receive_stock_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
FILE_CODE

echo ""
echo "📁 Создан файл webhook_receiver_new_version.py с обновленным кодом"
echo "Можете скопировать его на сервер для применения обновления."