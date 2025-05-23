# 🚀 Руководство по развертыванию системы автоматизации товарных запасов

## 📋 Обзор системы

Система предоставляет два интерфейса:
1. **Web-приложение** (Streamlit) - для работы через браузер
2. **Telegram-бот** - для мобильного доступа

## 🛠️ Установка и настройка

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий или создайте папку проекта
mkdir inventory_system
cd inventory_system

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Структура проекта

```
inventory_system/
├── inventory_automation.py    # Основная система
├── excel_processor.py        # Обработчик Excel данных
├── telegram_bot.py          # Telegram бот
├── requirements.txt          # Зависимости
├── README.md                # Инструкция пользователя
├── DEPLOYMENT.md            # Это руководство
└── .env                     # Переменные окружения (создать)
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Токен Telegram бота (получить от @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Настройки приложения
DEBUG=False
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=xlsx,xls
```

## 🌐 Запуск Web-приложения

### Локальный запуск

```bash
# Запуск Streamlit приложения
streamlit run inventory_automation.py

# Приложение будет доступно по адресу:
# http://localhost:8501
```

### Развертывание на сервере

#### Вариант 1: Использование Streamlit Cloud

1. Загрузите код в GitHub репозиторий
2. Зайдите на [share.streamlit.io](https://share.streamlit.io)
3. Подключите ваш репозиторий
4. Укажите файл `inventory_automation.py` как main file
5. Добавьте secrets в настройках (если нужно)

#### Вариант 2: VPS/сервер с Docker

Создайте `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "inventory_automation.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Запуск:

```bash
# Сборка образа
docker build -t inventory-system .

# Запуск контейнера
docker run -p 8501:8501 inventory-system
```

#### Вариант 3: Обычный VPS с nginx

1. Установите зависимости на сервер
2. Настройте nginx как reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Запустите приложение как systemd service

## 🤖 Настройка Telegram бота

### 1. Создание бота

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен и добавьте его в `.env`

### 2. Настройка команд бота

Отправьте @BotFather команду `/setcommands` и укажите:

```
start - Начать работу с системой
help - Подробная инструкция
settings - Настройки параметров
status - Статус обработки данных
```

### 3. Запуск бота

#### Локальный запуск

```bash
# Установите токен в переменную окружения
export TELEGRAM_BOT_TOKEN="your_bot_token"

# Запустите бота
python telegram_bot.py
```

#### Запуск на сервере

Создайте systemd service `/etc/systemd/system/inventory-bot.service`:

```ini
[Unit]
Description=Inventory Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/inventory_system
Environment=TELEGRAM_BOT_TOKEN=your_bot_token
ExecStart=/path/to/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl enable inventory-bot
sudo systemctl start inventory-bot
sudo systemctl status inventory-bot
```

## 🔧 Конфигурация и настройка

### Настройки по умолчанию

```python
DEFAULT_SETTINGS = {
    'days_supply': 10,          # Дней запаса
    'total_shelves': 786,       # Общее количество полок
    'safety_factor': 1.2,       # Коэффициент безопасности
    'package_multiple': 4,      # Кратность упаковки
    'use_package_multiples': False  # Учитывать кратность
}
```

### Ограничения файлов

- Максимальный размер файла: 50MB
- Поддерживаемые форматы: .xlsx, .xls
- Максимальное количество строк: 100,000
- Максимальное количество колонок: 100

## 📊 Мониторинг и логирование

### Логи Web-приложения

Streamlit автоматически выводит логи в консоль. Для сохранения в файл:

```bash
streamlit run inventory_automation.py > logs/app.log 2>&1
```

### Логи Telegram бота

Бот использует стандартный модуль logging Python:

```python
# В telegram_bot.py уже настроено логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
```

### Мониторинг производительности

Для мониторинга можно использовать:

- **htop** - мониторинг ресурсов сервера
- **journalctl** - просмотр логов systemd
- **nginx access logs** - статистика веб-доступа

```bash
# Просмотр логов бота
journalctl -u inventory-bot -f

# Просмотр использования ресурсов
htop

# Логи nginx
tail -f /var/log/nginx/access.log
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Переменные окружения**: Никогда не добавляйте токены в код
2. **HTTPS**: Используйте SSL сертификаты для web-приложения
3. **Ограничения доступа**: Настройте firewall для ограничения доступа
4. **Обновления**: Регулярно обновляйте зависимости

### Настройка SSL (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚨 Уст