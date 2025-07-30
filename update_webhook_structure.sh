#!/bin/bash
# Обновление структуры папок вебхука согласно документации Вебхук.md
# Применяет изменения как на сервере, так и локально

echo "📁 Обновление структуры папок вебхука"
echo "===================================="

# Сначала создаем обновленный файл локально
echo "🔧 Создаем обновленный webhook_receiver.py локально..."

cat > webhook_receiver_updated.py << 'LOCAL_PYTHON_EOF'
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
    """Валидация файла продаж"""
    try:
        if not isinstance(data, list) or len(data) == 0:
            return False, "Данные должны быть непустым массивом"
        
        first_item = data[0]
        
        # Поддержка новой структуры из Вебхук.md
        if 'Продажи' in first_item:
            required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'Продажи']
            for field in required_fields:
                if field not in first_item:
                    return False, f"Отсутствует обязательное поле: {field}"
            return True, "OK"
        
        # Поддержка старой структуры
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
    """Валидация файла остатков согласно Вебхук.md"""
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
        # Проверка подписи (опционально)
        signature = request.headers.get('X-Hub-Signature-256')
        if signature and not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook для продаж")
            return jsonify({'error': 'Неверная подпись'}), 401
        
        # Получение данных
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация
        is_valid, message = validate_sales_file(data)
        if not is_valid:
            logging.error(f"Ошибка валидации продаж: {message}")
            return jsonify({'error': message}), 400
        
        # Определение имени файла
        if data and len(data) > 0:
            start_date = data[0].get('НачалоПериода', '').split('T')[0]
            end_date = data[0].get('КонецПериода', '').split('T')[0]
            branch = data[0].get('Филиал', 'unknown')
            branch_short = branch.replace(' ', '_').replace('"', '').replace('/', '_')[:30]
            filename = f"sales_{start_date}_{end_date}_{branch_short}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"sales_{timestamp}.json"
        
        # Сохранение в папку sales/
        file_path = SALES_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📊 Получен файл продаж: {filename} -> {SALES_DIR}")
        
        # Интеграция с накопителем
        try:
            from webhook_data_accumulator import WebhookDataAccumulator
            accumulator = WebhookDataAccumulator()
            result = accumulator.process_new_sales_file(file_path)
            logging.info(f"Накопитель продаж: {result}")
        except Exception as e:
            logging.error(f"Ошибка накопителя продаж: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл продаж получен и сохранен',
            'filename': filename,
            'saved_to': 'sales/',
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении данных продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock', methods=['POST'])
def receive_stock_data():
    """Получение данных об остатках - сохранение в папку stock/"""
    try:
        # Проверка подписи (опционально)
        signature = request.headers.get('X-Hub-Signature-256')
        if signature and not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook для остатков")
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
        if stock_date:
            filename = f"stock_{stock_date}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f"stock_{timestamp}.json"
        
        # Сохранение в папку stock/
        file_path = STOCK_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📦 Получен файл остатков: {filename} -> {STOCK_DIR}")
        
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
            'saved_to': 'stock/',
            'file_path': str(file_path),
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

@app.route('/webhook/files', methods=['GET'])
def list_files():
    """Список загруженных файлов по категориям"""
    try:
        # Файлы продаж
        sales_files = []
        for file_path in SALES_DIR.glob('*.json'):
            stat = file_path.stat()
            sales_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'sales',
                'path': f'sales/{file_path.name}'
            })
        
        # Файлы остатков
        stock_files = []
        for file_path in STOCK_DIR.glob('*.json'):
            stat = file_path.stat()
            stock_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'stock',
                'path': f'stock/{file_path.name}'
            })
        
        return jsonify({
            'sales': {
                'files': sorted(sales_files, key=lambda x: x['modified'], reverse=True),
                'count': len(sales_files)
            },
            'stock': {
                'files': sorted(stock_files, key=lambda x: x['modified'], reverse=True),
                'count': len(stock_files)
            },
            'total_files': len(sales_files) + len(stock_files)
        })
        
    except Exception as e:
        logging.error(f"Ошибка списка файлов: {e}")
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
    # Запуск в продакшене используйте gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)
LOCAL_PYTHON_EOF

echo "✅ Локальный файл webhook_receiver_updated.py создан"

echo "📋 Создаем резервную копию старого файла локально..."
if [ -f "webhook_receiver.py" ]; then
    cp webhook_receiver.py webhook_receiver_backup_local_$(date +%Y%m%d_%H%M%S).py
    echo "✅ Локальная резервная копия создана"
fi

echo "🔧 Проверяем синтаксис локально..."
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_receiver_updated.py', doraise=True)
    print('✅ Синтаксис webhook_receiver_updated.py корректен!')
except Exception as e:
    print(f'❌ Ошибка синтаксиса: {e}')
    exit(1)
"

echo "📁 Обновляем локальный файл..."
cp webhook_receiver_updated.py webhook_receiver.py
echo "✅ Локальный файл обновлен"

echo ""
echo "🌐 Теперь применяем изменения на SSH сервере..."

ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "📋 Создаем резервную копию webhook_receiver.py..."
cp webhook_receiver.py webhook_receiver_backup_$(date +%Y%m%d_%H%M%S).py

echo "📁 Создаем отдельные папки для продаж и остатков..."
mkdir -p webhook_uploads/sales
mkdir -p webhook_uploads/stock
mkdir -p webhook_uploads/archive

echo "✅ Структура папок создана:"
ls -la webhook_uploads/

echo "🔧 Обновляем webhook_receiver.py для поддержки раздельных папок..."

cat > webhook_receiver_updated.py << 'PYTHON_EOF'
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
    """Валидация файла продаж"""
    try:
        if not isinstance(data, list) or len(data) == 0:
            return False, "Данные должны быть непустым массивом"
        
        first_item = data[0]
        
        # Поддержка новой структуры из Вебхук.md
        if 'Продажи' in first_item:
            required_fields = ['ДатаВыгрузки', 'НачалоПериода', 'КонецПериода', 'Филиал', 'Продажи']
            for field in required_fields:
                if field not in first_item:
                    return False, f"Отсутствует обязательное поле: {field}"
            return True, "OK"
        
        # Поддержка старой структуры
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
    """Валидация файла остатков согласно Вебхук.md"""
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
        # Проверка подписи (опционально)
        signature = request.headers.get('X-Hub-Signature-256')
        if signature and not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook для продаж")
            return jsonify({'error': 'Неверная подпись'}), 401
        
        # Получение данных
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        # Валидация
        is_valid, message = validate_sales_file(data)
        if not is_valid:
            logging.error(f"Ошибка валидации продаж: {message}")
            return jsonify({'error': message}), 400
        
        # Определение имени файла
        if data and len(data) > 0:
            start_date = data[0].get('НачалоПериода', '').split('T')[0]
            end_date = data[0].get('КонецПериода', '').split('T')[0]
            branch = data[0].get('Филиал', 'unknown')
            branch_short = branch.replace(' ', '_').replace('"', '').replace('/', '_')[:30]
            filename = f"sales_{start_date}_{end_date}_{branch_short}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"sales_{timestamp}.json"
        
        # Сохранение в папку sales/
        file_path = SALES_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📊 Получен файл продаж: {filename} -> {SALES_DIR}")
        
        # Интеграция с накопителем
        try:
            from webhook_data_accumulator import WebhookDataAccumulator
            accumulator = WebhookDataAccumulator()
            result = accumulator.process_new_sales_file(file_path)
            logging.info(f"Накопитель продаж: {result}")
        except Exception as e:
            logging.error(f"Ошибка накопителя продаж: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Файл продаж получен и сохранен',
            'filename': filename,
            'saved_to': 'sales/',
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Ошибка при получении данных продаж: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stock', methods=['POST'])
def receive_stock_data():
    """Получение данных об остатках - сохранение в папку stock/"""
    try:
        # Проверка подписи (опционально)
        signature = request.headers.get('X-Hub-Signature-256')
        if signature and not verify_signature(request.data, signature):
            logging.warning("Неверная подпись webhook для остатков")
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
        if stock_date:
            filename = f"stock_{stock_date}.json"
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f"stock_{timestamp}.json"
        
        # Сохранение в папку stock/
        file_path = STOCK_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"📦 Получен файл остатков: {filename} -> {STOCK_DIR}")
        
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
            'saved_to': 'stock/',
            'file_path': str(file_path),
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

@app.route('/webhook/files', methods=['GET'])
def list_files():
    """Список загруженных файлов по категориям"""
    try:
        # Файлы продаж
        sales_files = []
        for file_path in SALES_DIR.glob('*.json'):
            stat = file_path.stat()
            sales_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'sales',
                'path': f'sales/{file_path.name}'
            })
        
        # Файлы остатков
        stock_files = []
        for file_path in STOCK_DIR.glob('*.json'):
            stat = file_path.stat()
            stock_files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': 'stock',
                'path': f'stock/{file_path.name}'
            })
        
        return jsonify({
            'sales': {
                'files': sorted(sales_files, key=lambda x: x['modified'], reverse=True),
                'count': len(sales_files)
            },
            'stock': {
                'files': sorted(stock_files, key=lambda x: x['modified'], reverse=True),
                'count': len(stock_files)
            },
            'total_files': len(sales_files) + len(stock_files)
        })
        
    except Exception as e:
        logging.error(f"Ошибка списка файлов: {e}")
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
    # Запуск в продакшене используйте gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)
PYTHON_EOF

echo "🔍 Проверяем синтаксис обновленного файла..."
python3 -c "
try:
    import py_compile
    py_compile.compile('webhook_receiver_updated.py', doraise=True)
    print('✅ Синтаксис webhook_receiver_updated.py корректен!')
except Exception as e:
    print(f'❌ Ошибка синтаксиса: {e}')
"

echo "🔄 Заменяем основной файл..."
cp webhook_receiver.py webhook_receiver_old.py
cp webhook_receiver_updated.py webhook_receiver.py

echo "🛑 Перезапускаем webhook сервер..."
pkill -f "webhook_receiver"
sleep 3

echo "🚀 Запускаем обновленный webhook сервер..."
nohup python3 webhook_receiver.py > webhook_5000.log 2>&1 &
WEBHOOK_PID=$!
echo "Webhook сервер запущен с PID: $WEBHOOK_PID"

echo "⏳ Ждем запуска..."
sleep 3

echo "🔍 Проверяем статус нового сервера..."
curl -s http://localhost:5000/webhook/status | python3 -m json.tool || echo "Сервер еще запускается..."

echo "📁 Проверяем структуру папок..."
ls -la webhook_uploads/

echo "📋 Логи запуска:"
tail -n 10 webhook_5000.log

echo ""
echo "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📊 Новые эндпоинты:"
echo "   POST /sales - данные о продажах -> webhook_uploads/sales/"
echo "   POST /stock - данные об остатках -> webhook_uploads/stock/"
echo "   GET /webhook/status - статус с информацией о папках"
echo "   GET /webhook/files - списки файлов по категориям"
echo ""
echo "🔗 Обратная совместимость сохранена:"
echo "   POST /webhook/sales -> перенаправление на /sales"
echo "   POST /webhook/stock -> перенаправление на /stock"

REMOTE_EOF

echo ""
echo "📥 Синхронизируем обновленные файлы с сервера обратно в локальную папку..."

# Создаем папку для синхронизации
mkdir -p ssh2

# Загружаем обновленные файлы с сервера
echo "📋 Загружаем обновленные файлы..."
scp root@217.114.1.117:/opt/inventory_system/webhook_receiver.py ./ssh2/
scp root@217.114.1.117:/opt/inventory_system/webhook_data_accumulator.py ./ssh2/
scp root@217.114.1.117:/opt/inventory_system/webhook_persistent_app.py ./ssh2/
scp root@217.114.1.117:/opt/inventory_system/requirements.txt ./ssh2/

echo "📋 Загружаем логи для проверки..."
scp root@217.114.1.117:/opt/inventory_system/webhook_5000.log ./ssh2/ 2>/dev/null || echo "webhook_5000.log не найден"
scp root@217.114.1.117:/opt/inventory_system/webhook_8502.log ./ssh2/ 2>/dev/null || echo "webhook_8502.log не найден"

echo "📋 Загружаем структуру папок..."
ssh root@217.114.1.117 "cd /opt/inventory_system && find webhook_uploads -type d" > ./ssh2/folder_structure.txt
ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/" > ./ssh2/uploads_listing.txt
ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/sales/ 2>/dev/null || echo 'sales папка пуста'" > ./ssh2/sales_listing.txt
ssh root@217.114.1.117 "cd /opt/inventory_system && ls -la webhook_uploads/stock/ 2>/dev/null || echo 'stock папка пуста'" > ./ssh2/stock_listing.txt

echo "✅ Файлы синхронизированы в папку ssh2/"

echo ""
echo "📊 Структура обновленного проекта:"
echo "======================================"
echo "Локально:"
ls -la webhook_receiver*.py 2>/dev/null || echo "  - webhook файлы отсутствуют"
echo ""
echo "На сервере (ssh2/):"
ls -la ssh2/

echo ""
echo "🎉 ПОЛНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "======================================"
echo "✅ Локальные файлы обновлены"
echo "✅ Серверные файлы обновлены"
echo "✅ Синхронизация выполнена"
echo ""
echo "📊 Новая структура:"
echo "   • Продажи: webhook_uploads/sales/"
echo "   • Остатки: webhook_uploads/stock/"
echo "   • Архив данных: webhook_uploads/archive/"
echo ""
echo "🔗 Новые эндпоинты:"
echo "   POST /sales - данные о продажах"
echo "   POST /stock - данные об остатках"
echo "   GET /webhook/status - статус системы"
echo "   GET /webhook/files - файлы по категориям"
echo ""
echo "🔍 Тестирование:"
echo "   curl http://217.114.1.117:5000/"
echo "   curl http://217.114.1.117:5000/webhook/status"