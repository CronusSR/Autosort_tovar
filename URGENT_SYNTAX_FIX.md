# 🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ

## Проблема
В файле `/opt/inventory_system/webhook_persistent_app.py` строка 441 содержит синтаксическую ошибку Python.

## Быстрое исправление

### Вариант 1: Замена одной строки
Найдите строку 441:
```python
'amount': 'sum' if 'amount' in sales_data.columns else 'total_amount': 'sum'
```

Замените на:
```python
**Удалите строки 440-442 и вставьте:**
```python
                if 'amount' in sales_data.columns:
                    top_items_revenue = sales_data.groupby(['item_code', 'item_name']).agg({
                        'amount': 'sum'
                    }).reset_index()
                else:
                    top_items_revenue = sales_data.groupby(['item_code', 'item_name']).agg({
                        'total_amount': 'sum'
                    }).reset_index()
```

### Вариант 2: Полная замена файла
Скопируйте исправленный файл `webhook_app_enhanced_analytics.py` как `webhook_persistent_app.py`

## Команды для администратора сервера

```bash
# 1. Остановить сервис
systemctl stop webhook-analytics

# 2. Сделать резервную копию
cp /opt/inventory_system/webhook_persistent_app.py /opt/inventory_system/webhook_persistent_app_backup_$(date +%Y%m%d_%H%M%S).py

# 3. Исправить файл (вариант 1)
nano /opt/inventory_system/webhook_persistent_app.py
# Найти строку 441 и заменить как указано выше

# 4. Запустить сервис
systemctl start webhook-analytics

# 5. Проверить статус
systemctl status webhook-analytics
```

## Проверка исправления
После исправления сервис должен запуститься без ошибок:
- Проверьте: http://217.114.1.117:8502
- Логи: `journalctl -u webhook-analytics -f`

## Контакты
Если нужна помощь с исправлением, свяжитесь с разработчиком.