#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки webhook (прямое подключение)
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime

# Настройки (должны совпадать с .env)
WEBHOOK_URL = "http://127.0.0.1:5000"  # Прямое подключение
SECRET_KEY = "your_secret_key_123456"  # Замените на ваш ключ из .env

# Отключаем proxy для локальных запросов
session = requests.Session()
session.proxies = {}

def create_signature(payload):
    """Создает подпись для webhook"""
    mac = hmac.new(SECRET_KEY.encode(), payload, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"

def test_sales_webhook():
    """Тестирует отправку данных продаж"""
    print("🔄 Тестируем webhook продаж...")
    
    # Тестовые данные продаж - ТОЧНАЯ СТРУКТУРА из ТЗ
    test_data = [
        {
            "ДатаВыгрузки": datetime.now().isoformat(),
            "НачалоПериода": "2025-01-01",
            "КонецПериода": "2025-01-15",
            "Филиал": "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"",
            "ПродажиПоДням": {
                "2025-01-01": [],
                "2025-01-02": [
                    {
                        "ПутьКатегорий": "Плинтус пластиковый 3м/Аксессуары для столешниц/Мебельная фурнитура/",
                        "Номенклатура": "Плинтус пластик 3м Черный глянец AP740 TP",
                        "Количество": 5,
                        "Выручка": 16825,
                        "Себестоимость": 12430.52,
                        "ВаловаяПрибыль": 4394.48,
                        "Рентабельность": 26.13,
                        "ЕдиницаИзмерения": "Штука",
                        "Артикул": "AP740.1905F3",
                        "Производитель": "Польша"
                    }
                ],
                "2025-01-03": [],
                "2025-01-04": [],
                "2025-01-05": [
                    {
                        "ПутьКатегорий": "Плинтус пластиковый 3м/Аксессуары для столешниц/Мебельная фурнитура/",
                        "Номенклатура": "Плинтус пластик 3м Черный глянец AP740 TP",
                        "Количество": 7,
                        "Выручка": 23555,
                        "Себестоимость": 17398.72,
                        "ВаловаяПрибыль": 6156.28,
                        "Рентабельность": 26.13,
                        "ЕдиницаИзмерения": "Штука",
                        "Артикул": "AP740.1905F3",
                        "Производитель": "Польша"
                    }
                ]
            },
            "ИтогиЗаПериод": [
                {
                    "ПутьКатегорий": "Плинтус пластиковый 3м/Аксессуары для столешниц/Мебельная фурнитура/",
                    "Номенклатура": "Плинтус пластик 3м Черный глянец AP740 TP",
                    "ОбщееКоличество": 12,
                    "ОбщаяВыручка": 40380,
                    "ОбщаяСебестоимость": 29829.24,  # ВАЖНО для расчетов!
                    "ОбщаяПрибыль": 10550.76,
                    "СредняяРентабельность": 26.13,
                    "ЕдиницаИзмерения": "Штука",
                    "Артикул": "AP740.1905F3",
                    "Производитель": "Польша"
                }
            ]
        }
    ]
    
    # Преобразуем в JSON
    payload = json.dumps(test_data, ensure_ascii=False).encode('utf-8')
    
    # Создаем подпись
    signature = create_signature(payload)
    
    # Отправляем запрос
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': signature
    }
    
    try:
        response = session.post(
            f"{WEBHOOK_URL}/webhook/sales",
            data=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Успешно! Ответ сервера:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к webhook серверу")
        print("   Убедитесь что сервер запущен: python webhook_receiver.py")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_stock_webhook():
    """Тестирует отправку данных остатков"""
    print("\n🔄 Тестируем webhook остатков...")
    
    # Тестовые данные остатков - ТОЧНАЯ СТРУКТУРА из ТЗ
    test_data = {
        "ДатаОстатков": "2025-01-15T23:59:59",
        "ДатаВыгрузки": datetime.now().isoformat(),
        "ОстаткиПоСкладам": [
            {
                "Склад": "4 Склад фурнитуры АЗМ Шымкент \"Овощная база\"",
                "Город": "",
                "Остатки": [
                    {
                        "ПутьКатегорий": "Плинтус пластиковый 3м/Аксессуары для столешниц/Мебельная фурнитура/",
                        "Номенклатура": "Плинтус пластик 3м Кастилло темный AP740 TP",
                        "Количество": 127,
                        "Стоимость": 314963.33,  # Себестоимость остатков
                        "СредняяЦена": "2 480,03",
                        "ЕдиницаИзмерения": "Штука",
                        "Артикул": "AP740.1242F3",
                        "Производитель": "Польша"
                    }
                ]
            }
        ]
    }
    
    # Преобразуем в JSON
    payload = json.dumps(test_data, ensure_ascii=False).encode('utf-8')
    
    # Создаем подпись
    signature = create_signature(payload)
    
    # Отправляем запрос
    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': signature
    }
    
    try:
        response = session.post(
            f"{WEBHOOK_URL}/webhook/stock",
            data=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Успешно! Ответ сервера:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к webhook серверу")
        print("   Убедитесь что сервер запущен: python webhook_receiver.py")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_webhook_status():
    """Проверяет статус webhook сервера"""
    print("🔍 Проверяем статус webhook сервера...")
    
    try:
        response = session.get(f"{WEBHOOK_URL}/webhook/status", timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook сервер работает!")
            data = response.json()
            print(f"📁 Директория загрузок: {data.get('upload_dir')}")
            print(f"⏰ Время: {data.get('timestamp')}")
            if data.get('recent_files'):
                print("📄 Последние файлы:")
                for file in data['recent_files'][:5]:
                    print(f"   - {file['name']} ({file['size']} байт)")
            else:
                print("📄 Пока нет загруженных файлов")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Webhook сервер не доступен")
        print("   Запустите: python webhook_receiver.py")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("=== ТЕСТ WEBHOOK СИСТЕМЫ (ПРЯМОЕ ПОДКЛЮЧЕНИЕ) ===\n")
    
    # Проверяем статус
    check_webhook_status()
    
    # Тестируем endpoints
    test_sales_webhook()
    test_stock_webhook()
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")
    print("\nЕсли тесты прошли успешно:")
    print("✅ Webhook система готова к работе!")
    print("📋 Передайте программисту 1С:")
    print("   - Файл: 1C_INTEGRATION_FULL_GUIDE.md")
    print("   - URL: http://ваш-сервер:5000")
    print("   - Секретный ключ из .env файла")