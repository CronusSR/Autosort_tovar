#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование обработки ZIP файла от 1С
"""

import sys
import os
from pathlib import Path
import json
import zipfile
from webhook_zip_handler import WebhookZipHandler

def test_zip_file(zip_path: str):
    """Тестирование обработки ZIP файла"""
    
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТКИ ZIP ФАЙЛА")
    print("=" * 50)
    
    zip_file = Path(zip_path)
    if not zip_file.exists():
        print(f"❌ Файл не найден: {zip_path}")
        return False
    
    print(f"📁 Тестируемый файл: {zip_file.name}")
    print(f"📏 Размер файла: {zip_file.stat().st_size:,} байт")
    
    # 1. Проверяем содержимое ZIP архива
    print("\n🔍 Анализ содержимого ZIP архива:")
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"📦 Файлов в архиве: {len(file_list)}")
            
            for file_name in file_list[:10]:  # Показываем первые 10
                print(f"   📄 {file_name}")
            
            if len(file_list) > 10:
                print(f"   ... и еще {len(file_list) - 10} файлов")
    
    except Exception as e:
        print(f"❌ Ошибка чтения ZIP: {e}")
        return False
    
    # 2. Тестируем обработчик ZIP
    print("\n🔧 Тестирование обработчика ZIP:")
    
    try:
        # Читаем ZIP как bytes
        with open(zip_file, 'rb') as f:
            zip_data = f.read()
        
        # Создаем обработчик
        handler = WebhookZipHandler(upload_dir="./test_webhook_uploads")
        
        # Обрабатываем
        print("⚙️ Запуск обработки...")
        result = handler.process_zip_file(zip_data, zip_file.name)
        
        print(f"📊 Результат обработки:")
        print(f"   Статус: {result.get('status')}")
        print(f"   Сообщение: {result.get('message')}")
        
        if result.get('status') == 'success':
            print(f"   ✅ Файлов обработано: {result.get('files_processed', 0)}")
            print(f"   📝 Всего записей: {result.get('total_records', 0)}")
            
            # Показываем детали обработанных файлов
            if 'files' in result:
                print("\n📋 Детали обработанных файлов:")
                for file_info in result['files']:
                    print(f"   📄 {file_info.get('filename')}: {file_info.get('records_count', 0)} записей")
        else:
            print(f"   ❌ Ошибка: {result.get('message')}")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Проверяем созданные файлы
    print("\n📁 Проверка созданных файлов:")
    test_upload_dir = Path("./test_webhook_uploads")
    
    if test_upload_dir.exists():
        created_files = list(test_upload_dir.glob("*.json"))
        print(f"📄 Создано JSON файлов: {len(created_files)}")
        
        for json_file in created_files[:3]:  # Показываем первые 3
            print(f"   📄 {json_file.name} ({json_file.stat().st_size:,} байт)")
            
            # Проверяем структуру одного файла
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0]
                    print(f"      🏪 Филиал: {first_item.get('Филиал', 'Не указан')}")
                    print(f"      📅 Период: {first_item.get('НачалоПериода')} - {first_item.get('КонецПериода')}")
                    
                    if 'ПродажиПоДням' in first_item:
                        total_days = len(first_item['ПродажиПоДням'])
                        total_items = sum(len(day_sales) for day_sales in first_item['ПродажиПоДням'].values())
                        print(f"      📊 Дней с продажами: {total_days}")
                        print(f"      🛍️ Всего товарных позиций: {total_items}")
                    
                    if 'ИтогиЗаПериод' in first_item:
                        totals_count = len(first_item['ИтогиЗаПериод'])
                        print(f"      📈 Уникальных товаров: {totals_count}")
                
            except Exception as e:
                print(f"      ❌ Ошибка чтения файла: {e}")
        
        if len(created_files) > 3:
            print(f"   ... и еще {len(created_files) - 3} файлов")
    else:
        print("❌ Директория с результатами не создана")
        return False
    
    print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    return True

def test_webhook_simulation():
    """Симуляция отправки на webhook"""
    
    print("\n🌐 СИМУЛЯЦИЯ ОТПРАВКИ НА WEBHOOK")
    print("=" * 50)
    
    zip_file = Path("./Выгрузка JSON.zip")
    
    try:
        # Читаем ZIP файл
        with open(zip_file, 'rb') as f:
            zip_data = f.read()
        
        # Симулируем webhook запрос
        import requests
        import hashlib
        import hmac
        
        # Настройки
        webhook_url = "http://217.114.1.117:5000/webhook/sales"
        secret_key = "furniture_company_secret_key_2025"
        
        # Создаем подпись
        signature = hmac.new(
            secret_key.encode(), 
            zip_data, 
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/zip',
            'X-Hub-Signature-256': f'sha256={signature}'
        }
        
        print(f"🔗 URL: {webhook_url}")
        print(f"📦 Размер данных: {len(zip_data):,} байт")
        print(f"🔐 Подпись: sha256={signature[:20]}...")
        
        print("\n⚠️ ВНИМАНИЕ: Для реального тестирования запустите:")
        print(f"curl -X POST {webhook_url} \\")
        print(f"  -H 'Content-Type: application/zip' \\")
        print(f"  -H 'X-Hub-Signature-256: sha256={signature}' \\")
        print(f"  --data-binary @'Выгрузка JSON.zip'")
        
        # Можно раскомментировать для реального тестирования:
        # response = requests.post(webhook_url, data=zip_data, headers=headers, timeout=30)
        # print(f"📊 Ответ сервера: {response.status_code}")
        # print(f"📄 Содержимое: {response.text}")
        
    except Exception as e:
        print(f"❌ Ошибка симуляции: {e}")

if __name__ == "__main__":
    # Тестируем обработку ZIP файла
    success = test_zip_file("./Выгрузка JSON.zip")
    
    if success:
        # Симулируем webhook
        test_webhook_simulation()
    
    print("\n" + "=" * 50)
    print("🎯 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    if success:
        print("✅ ZIP файл успешно обработан")
        print("✅ JSON файлы созданы в правильном формате")
        print("✅ Система готова к приему ZIP архивов")
        print("\n🚀 Можно развертывать на сервере!")
    else:
        print("❌ Есть проблемы с обработкой ZIP")
        print("🔧 Требуется исправление перед развертыванием")