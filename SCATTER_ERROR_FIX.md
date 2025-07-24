# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ SCATTER PLOT

## Проблема
```
ValueError: Invalid element(s) received for the 'size' property of scatter.marker
Invalid elements include: [-169166.0]
```

Ошибка возникает потому что scatter plot не может использовать отрицательные значения для размера точек.

## Быстрое исправление (если SSH доступен)
```bash
./fix_scatter_error.sh
```

## Ручное исправление

### Найти и заменить в файле `/opt/inventory_system/webhook_persistent_app.py`:

**Найти строки около 740-750:**

**БЫЛО:**
```python
fig_calendar = px.scatter(
    daily_sales_full.head(365),
    x='date',
    y='amount',
    size='amount',  # ← Проблема: может быть отрицательным
    hover_data=['formatted_date', 'weekday'],
    title=f'Продажи по дням (последние {min(365, len(daily_sales_full))} дней)',
    labels={'amount': 'Выручка (₸)', 'date': 'Дата'}
)
```

**СТАЛО:**
```python
# Подготавливаем данные для графика
plot_data = daily_sales_full.head(365).copy()

# Исправляем размер точек - убираем отрицательные значения и нормализуем
plot_data['amount_abs'] = plot_data['amount'].abs()
if plot_data['amount_abs'].max() > 0:
    # Нормализуем размер для лучшего отображения (от 5 до 50)
    plot_data['size_normalized'] = 5 + (plot_data['amount_abs'] / plot_data['amount_abs'].max()) * 45
else:
    plot_data['size_normalized'] = 10  # Фиксированный размер если все нули

# График продаж по датам
fig_calendar = px.scatter(
    plot_data,
    x='date',
    y='amount',
    size='size_normalized',  # ← Исправлено: всегда положительные значения
    color='amount',
    hover_data=['formatted_date', 'weekday'],
    title=f'Продажи по дням (последние {min(365, len(daily_sales_full))} дней)',
    labels={'amount': 'Выручка (₸)', 'date': 'Дата'},
    color_continuous_scale='Viridis'
)
```

### Команды на сервере:
```bash
# Остановить сервис
systemctl stop webhook-analytics

# Отредактировать файл
nano /opt/inventory_system/webhook_persistent_app.py
# Заменить код как показано выше

# Запустить сервис
systemctl start webhook-analytics

# Проверить
systemctl status webhook-analytics
```

## Проверка исправления
- Откройте: http://217.114.1.117:8502
- Перейдите на вкладку "📈 Детальная аналитика"  
- График должен отображаться без ошибок

## Что делает исправление
- Преобразует отрицательные значения в положительные через abs()
- Нормализует размеры точек от 5 до 50 пикселей
- Добавляет цветовую схему для лучшей визуализации
- Обрабатывает случай когда все значения равны нулю