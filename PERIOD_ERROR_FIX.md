# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ PERIOD

## Проблема
```
TypeError: Object of type Period is not JSON serializable
```

Ошибка возникает в тепловой карте из-за использования pandas Period объектов.

## Быстрое исправление (если SSH доступен)
```bash
./fix_period_error.sh
```

## Ручное исправление

### Найти и заменить в файле `/opt/inventory_system/webhook_persistent_app.py`:

**Строка примерно 718:**

**БЫЛО:**
```python
sales_data['month_year'] = pd.to_datetime(sales_data['date']).dt.to_period('M')
```

**СТАЛО:**
```python
sales_data['month_year'] = pd.to_datetime(sales_data['date']).dt.strftime('%Y-%m')
```

### Команды на сервере:
```bash
# Остановить сервис
systemctl stop webhook-analytics

# Отредактировать файл
nano /opt/inventory_system/webhook_persistent_app.py
# Найти строку с .to_period('M') и заменить на .strftime('%Y-%m')

# Запустить сервис
systemctl start webhook-analytics

# Проверить
systemctl status webhook-analytics
```

## Проверка исправления
- Откройте: http://217.114.1.117:8502
- Перейдите на вкладку "📈 Детальная аналитика"  
- Тепловая карта должна отображаться без ошибок

## Что делает исправление
- Заменяет Period объекты на обычные строки в формате "YYYY-MM"
- Устраняет проблему JSON сериализации в Plotly
- Сохраняет всю функциональность тепловой карты