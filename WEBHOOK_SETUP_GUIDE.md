# Руководство по настройке системы с webhook

## Обзор архитектуры

У нас есть **два отдельных приложения**:

1. **Основное приложение** (`streamlit_modular_app.py`) - ручная загрузка файлов
2. **Webhook приложение** (`webhook_app.py`) - автоматическая обработка данных от 1С

## 1. Запуск основного приложения (ручная загрузка)

```bash
# Запуск основного приложения
streamlit run streamlit_modular_app.py --server.port 8501
```

**Функции:**
- Ручная загрузка файлов JSON
- Поддержка старого и нового формата файлов
- Все существующие функции анализа
- Работает независимо от webhook

## 2. Запуск webhook системы

### 2.1 Запуск webhook сервера (для приема данных от 1С)

```bash
# Установка зависимостей
pip install flask

# Настройка секретного ключа
export WEBHOOK_SECRET="your_secret_key_here"
export WEBHOOK_PORT=5000

# Запуск webhook сервера
python webhook_receiver.py
```

### 2.2 Запуск автоматического приложения

```bash
# В отдельном терминале
streamlit run webhook_app.py --server.port 8502
```

## 3. Настройка для программиста 1С

### 3.1 Endpoints для отправки данных

```
POST http://your-server:5000/webhook/sales
Content-Type: application/json
X-Hub-Signature-256: sha256=<signature>

[JSON данные продаж с новой структурой]
```

```
POST http://your-server:5000/webhook/stock  
Content-Type: application/json
X-Hub-Signature-256: sha256=<signature>

{JSON данные остатков}
```

### 3.2 Проверка статуса

```
GET http://your-server:5000/webhook/status
```

### 3.3 Список файлов

```
GET http://your-server:5000/webhook/files
```

## 4. Структура файлов

### 4.1 Файл продаж (новый формат)
```json
[
  {
    "ДатаВыгрузки": "2025-07-17T18:19:48",
    "НачалоПериода": "2025-06-01", 
    "КонецПериода": "2025-06-30",
    "Филиал": "Название филиала",
    "ПродажиПоДням": {
      "2025-06-01": [...],
      "2025-06-02": [...]
    },
    "ИтогиЗаПериод": [...]
  }
]
```

### 4.2 Файл остатков (без изменений)
```json
{
  "ДатаОстатков": "2025-06-30T23:59:59",
  "ДатаВыгрузки": "2025-07-20T16:56:12", 
  "ОстаткиПоСкладам": [...]
}
```

## 5. Безопасность

### 5.1 Настройка HMAC подписи

```python
import hmac
import hashlib

secret = "your_secret_key_here"
payload = json.dumps(data).encode()
signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
headers = {'X-Hub-Signature-256': f'sha256={signature}'}
```

## 6. Мониторинг

### 6.1 Логи webhook сервера
```bash
tail -f webhook.log
```

### 6.2 Статус приложений
- Основное: http://localhost:8501
- Webhook: http://localhost:8502
- API статус: http://localhost:5000/webhook/status

## 7. Развертывание в продакшен

### 7.1 Systemd сервис для webhook

```ini
[Unit]
Description=Webhook Receiver
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/app
Environment=WEBHOOK_SECRET=your_secret
Environment=WEBHOOK_PORT=5000
ExecStart=/usr/bin/python3 webhook_receiver.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 7.2 Nginx конфигурация

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /webhook/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /app/ {
        proxy_pass http://localhost:8502;
        proxy_set_header Host $host;
    }
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
    }
}
```

## 8. Отличия приложений

| Функция | Основное приложение | Webhook приложение |
|---------|-------------------|-------------------|
| Загрузка файлов | Ручная | Автоматическая |
| Поддержка форматов | Старый + новый | Только новый |
| Зависимости | Минимальные | Flask + enhanced_parser |
| Порт по умолчанию | 8501 | 8502 |
| Целевая аудитория | Аналитики | Автоматизация |

## 9. Устранение неполадок

### 9.1 Webhook сервер не запускается
- Проверьте занятость порта: `netstat -tlnp | grep 5000`
- Проверьте права доступа к директории
- Установите Flask: `pip install flask`

### 9.2 Файлы не обрабатываются
- Проверьте структуру JSON
- Проверьте подпись HMAC
- Посмотрите логи: `tail -f webhook.log`

### 9.3 Приложение не видит файлы
- Проверьте путь к `./webhook_uploads`
- Убедитесь что файлы имеют правильные имена
- Перезапустите приложение