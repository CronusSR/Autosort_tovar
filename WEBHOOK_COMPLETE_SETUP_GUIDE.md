# 📡 ПОЛНАЯ ИНСТРУКЦИЯ НАСТРОЙКИ ВЕБХУКОВ

## 🎯 Что такое вебхук и зачем он нужен?

**Вебхук** - это URL-адрес на вашем сервере, который принимает данные от 1С автоматически.

**Схема работы:**
```
1С Предприятие → HTTP POST запрос → Ваш сервер (217.114.1.117) → База данных → Аналитика
     ↑                                         ↓
     └─────── Автоматически каждый день ───────┘
```

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ

### ШАГ 1: Подготовка сервера

1. **Подключитесь к серверу по SSH:**
```bash
ssh root@217.114.1.117
```

2. **Перейдите в директорию проекта:**
```bash
cd /opt/inventory_system
```

3. **Создайте файл с секретным ключом:**
```bash
echo "WEBHOOK_SECRET=your_very_secret_key_12345" > .env
chmod 600 .env
```

### ШАГ 2: Установка вебхук-сервера

1. **Создайте скрипт установки:**
```bash
nano setup_webhook_server.sh
```

2. **Вставьте следующий код:**
```bash
#!/bin/bash

# Установка зависимостей
pip install flask python-dotenv

# Создание директорий
mkdir -p webhook_uploads
mkdir -p logs

# Создание systemd сервиса для вебхука
cat > /etc/systemd/system/webhook-receiver.service << EOF
[Unit]
Description=Webhook Receiver for 1C
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory_system
Environment="PATH=/opt/inventory_system/venv/bin"
ExecStart=/opt/inventory_system/venv/bin/python webhook_receiver.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создание systemd сервиса для аналитики
cat > /etc/systemd/system/webhook-analytics.service << EOF
[Unit]
Description=Webhook Analytics Application
After=network.target webhook-receiver.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory_system
Environment="PATH=/opt/inventory_system/venv/bin"
ExecStart=/opt/inventory_system/venv/bin/streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

# Запуск сервисов
systemctl enable webhook-receiver.service
systemctl enable webhook-analytics.service
systemctl start webhook-receiver.service
systemctl start webhook-analytics.service

echo "✅ Установка завершена!"
```

3. **Запустите установку:**
```bash
chmod +x setup_webhook_server.sh
./setup_webhook_server.sh
```

### ШАГ 3: Настройка файрвола

```bash
# Открыть порты для вебхука и аналитики
ufw allow 5000/tcp  # Для вебхука
ufw allow 8502/tcp  # Для аналитики
ufw reload
```

### ШАГ 4: Проверка работы

1. **Проверьте статус сервисов:**
```bash
systemctl status webhook-receiver
systemctl status webhook-analytics
```

2. **Проверьте доступность вебхука:**
```bash
curl http://217.114.1.117:5000/webhook/status
```

3. **Откройте аналитику в браузере:**
```
http://217.114.1.117:8502
```

## 🔗 ВАШИ ВЕБХУК-АДРЕСА

После установки у вас будут следующие адреса:

### Для 1С программиста:
- **Продажи:** `http://217.114.1.117:5000/webhook/sales`
- **Остатки:** `http://217.114.1.117:5000/webhook/stock`
- **Проверка:** `http://217.114.1.117:5000/webhook/status`

### Для просмотра аналитики:
- **Постоянная ссылка:** `http://217.114.1.117:8502`

## 📝 ИНСТРУКЦИЯ ДЛЯ 1С ПРОГРАММИСТА

Отправьте это вашему 1С программисту:

```
НАСТРОЙКА ОТПРАВКИ ДАННЫХ ИЗ 1С

1. URL для отправки:
   - Продажи: http://217.114.1.117:5000/webhook/sales
   - Остатки: http://217.114.1.117:5000/webhook/stock

2. Метод: POST

3. Заголовки:
   Content-Type: application/json
   X-Hub-Signature-256: sha256=<подпись>

4. Секретный ключ для подписи: your_very_secret_key_12345

5. Формат данных - см. файлы:
   - Продажи: API_СПЕЦИФИКАЦИЯ_ВЕБХУКИ.md
   - Остатки: API_СПЕЦИФИКАЦИЯ_ВЕБХУКИ.md

6. Пример кода 1С:
   См. файл: 1c_webhook_example.txt
```

## 🔧 УПРАВЛЕНИЕ СИСТЕМОЙ

### Перезапуск сервисов:
```bash
systemctl restart webhook-receiver
systemctl restart webhook-analytics
```

### Просмотр логов:
```bash
# Логи вебхука
tail -f /opt/inventory_system/webhook.log

# Логи systemd
journalctl -u webhook-receiver -f
journalctl -u webhook-analytics -f
```

### Резервное копирование базы данных:
```bash
cp webhook_data.db webhook_data_backup_$(date +%Y%m%d).db
```

## 🚨 УСТРАНЕНИЕ ПРОБЛЕМ

### Если вебхук не принимает данные:
1. Проверьте логи: `tail -f webhook.log`
2. Проверьте порт: `netstat -tlnp | grep 5000`
3. Проверьте файрвол: `ufw status`

### Если аналитика не открывается:
1. Проверьте статус: `systemctl status webhook-analytics`
2. Проверьте порт: `netstat -tlnp | grep 8502`
3. Перезапустите: `systemctl restart webhook-analytics`

## 📊 КАК РАБОТАЕТ НАКОПЛЕНИЕ ДАННЫХ

1. **Первая загрузка:** 1С отправляет данные за 3 года
2. **Ежедневное обновление:** Каждый день в 1:00 новые данные
3. **Накопление:** Все данные сохраняются в БД
4. **Анализ:** Можно анализировать любой период

### Структура базы данных:
- `sales` - таблица продаж (дата, филиал, товар, количество, сумма)
- `stock` - таблица остатков (дата, склад, товар, количество)
- `upload_history` - история загрузок

## ✅ ПРОВЕРОЧНЫЙ ЧЕКЛИСТ

- [ ] Сервер доступен по SSH
- [ ] Создан файл .env с секретным ключом
- [ ] Установлены все зависимости
- [ ] Запущены оба сервиса
- [ ] Открыты порты 5000 и 8502
- [ ] Вебхук отвечает на /webhook/status
- [ ] Аналитика открывается в браузере
- [ ] 1С программист получил инструкцию

## 📞 КОНТАКТЫ

При возникновении проблем:
1. Проверьте логи
2. Следуйте разделу "Устранение проблем"
3. Сохраните эту инструкцию для справки

---
Дата создания: 2025-07-24
Версия: 1.0