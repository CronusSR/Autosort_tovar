# Руководство по автоматизированным отчетам

## 🎯 Что делает система

Автоматизированная система ежедневно:
1. **Получает файлы** от 1С через webhook
2. **Анализирует данные** (межфилиальные перемещения, ABC анализ, оборачиваемость)  
3. **Генерирует полный отчет** Excel + JSON
4. **Отправляет отчет** по Email и/или Telegram

## 📋 Что включает отчет

### 📊 Основные показатели
- Количество филиалов, товаров
- Общие продажи и остатки
- Период анализа

### 🔄 Рекомендации по перемещению
- Откуда → Куда перемещать
- Количество товара
- Причина перемещения
- Приоритет (high/medium/low)
- Текущая оборачиваемость

### 📈 ABC анализ по категориям
- Категория товаров
- Продажи и остатки
- Оборачиваемость в днях
- Класс ABC (A/B/C)

### 🏢 Статистика по филиалам
- Тип филиала (хаб/склад/магазин)
- Продажи и остатки
- Оборачиваемость
- Количество товаров

## ⚙️ Установка и настройка

### 1. Установка зависимостей
```bash
pip install schedule jinja2 requests xlsxwriter
```

### 2. Настройка конфигурации
Отредактируйте `report_config.json`:

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com", 
    "smtp_port": 587,
    "username": "your_email@gmail.com",
    "password": "your_app_password",
    "recipients": ["manager@company.com"]
  },
  "telegram": {
    "enabled": true,
    "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    "chat_ids": ["-123456789"]
  },
  "schedule": {
    "time": "09:00",
    "enabled": true
  }
}
```

### 3. Настройка Email

#### Gmail:
1. Включите 2FA в аккаунте Google
2. Создайте пароль приложения: https://myaccount.google.com/apppasswords
3. Используйте этот пароль в конфигурации

#### Другие провайдеры:
```json
"smtp_server": "smtp.mail.ru",
"smtp_port": 587
```

### 4. Настройка Telegram

#### Создание бота:
1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Получите токен бота

#### Получение Chat ID:
1. Добавьте бота в группу или напишите ему
2. Откройте: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Найдите `chat.id` в ответе

## 🚀 Запуск системы

### Одноразовая генерация отчета
```bash
python automated_report_system.py generate
```

### Запуск планировщика (ежедневно)
```bash
python automated_report_system.py schedule
```

### Как Windows сервис
```bash
# Установка NSSM (Non-Sucking Service Manager)
# Скачать с https://nssm.cc/

nssm install AutoReportSystem
nssm set AutoReportSystem Application "C:\Python\python.exe"
nssm set AutoReportSystem AppParameters "C:\path\to\automated_report_system.py schedule"
nssm set AutoReportSystem AppDirectory "C:\path\to\project"
nssm start AutoReportSystem
```

### Как Linux сервис
```ini
# /etc/systemd/system/auto-reports.service
[Unit]
Description=Automated Reports System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 automated_report_system.py schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable auto-reports.service
sudo systemctl start auto-reports.service
```

## 📁 Структура файлов

```
project/
├── automated_report_system.py     # Основная система
├── report_config.json            # Конфигурация
├── webhook_receiver.py           # Webhook сервер
├── enhanced_data_parser.py       # Парсер данных
├── webhook_uploads/              # Входящие файлы от 1С
│   ├── sales_2025-01-15_2025-01-15.json
│   └── stock_2025-01-15.json
├── automated_reports/            # Готовые отчеты
│   ├── report_20250115_090001.json
│   └── report_20250115_090001.xlsx
└── automated_reports.log         # Логи системы
```

## 📊 Пример отчета

### Email уведомление:
```
📊 Автоматический отчет по складам
Дата: 2025-01-15
Период анализа: 30 дней

📈 Основные показатели:
• Филиалов: 9
• Товаров: 1,247
• Общие продажи: 15,234,567
• Общие остатки: 45,678,901
• Рекомендаций: 23

🚨 Приоритетные рекомендации:
• Склад А → Магазин Б: Товар X (50 шт.) - Избыток на 45 дней
• Хаб → Склад В: Товар Y (30 шт.) - Недостаток на 12 дней
```

### Excel файл содержит листы:
- **Сводка** - общие показатели
- **Рекомендации** - детальный список перемещений
- **ABC Анализ** - анализ по категориям
- **Статистика филиалов** - показатели по каждому филиалу

## 🔧 Настройка расписания

### Разное время для разных отчетов:
```python
# В коде можно изменить:
schedule.every().day.at("09:00").do(system.generate_full_report)
schedule.every().monday.at("08:00").do(system.generate_weekly_report)
schedule.every().day.at("18:00").do(system.generate_end_of_day_report)
```

### Проверка работы планировщика:
```bash
# Посмотреть логи
tail -f automated_reports.log

# Проверить статус сервиса
systemctl status auto-reports.service
```

## 🚨 Мониторинг и алерты

### Проверка работы системы:
1. **Логи** - смотрите `automated_reports.log`
2. **Файлы отчетов** - проверяйте директорию `automated_reports/`
3. **Уведомления** - настройте алерты при ошибках

### Типичные проблемы:
- **Нет файлов данных** - проверьте webhook сервер
- **Ошибки отправки Email** - проверьте пароль приложения
- **Telegram не работает** - проверьте токен и chat_id

## 🔄 Интеграция с существующей системой

Система полностью совместима с:
- ✅ Webhook сервером (`webhook_receiver.py`)
- ✅ Парсером данных (`enhanced_data_parser.py`)
- ✅ Основным приложением Streamlit
- ✅ Всеми существующими функциями анализа

Не требует изменений в существующем коде!