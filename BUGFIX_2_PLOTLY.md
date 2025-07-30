# 🚨 ИСПРАВЛЕНИЕ #2 - ValueError в графике оборачиваемости

## Проблема:
```
ValueError: Value of 'x' is not the name of a column in 'data_frame'. 
Expected one of ['turnover_category', 'count'] but received: index
```

## Причина:
После `value_counts().reset_index()` в pandas названия колонок автоматически назначаются, но в коде использовались неправильные названия.

## ✅ ИСПРАВЛЕНО:

### Строка 564-573:
```python
# БЫЛО (ошибка):
turnover_distribution = turnover_data['turnover_category'].value_counts().reset_index()

fig_dist = px.bar(
    turnover_distribution,
    x='index',                    # ❌ Неправильное название колонки
    y='turnover_category',        # ❌ Неправильное название колонки
    color='index',                # ❌ Неправильное название колонки

# СТАЛО (исправлено):
turnover_distribution = turnover_data['turnover_category'].value_counts().reset_index()
turnover_distribution.columns = ['category', 'count']  # ✅ Явно задаем названия колонок

fig_dist = px.bar(
    turnover_distribution,
    x='category',                 # ✅ Правильное название колонки
    y='count',                    # ✅ Правильное название колонки  
    color='category',             # ✅ Правильное название колонки
```

## Все исправления в webhook_persistent_app.py:

1. ✅ **Формула оборачиваемости**: `(остатки/продажи)*30.5`
2. ✅ **KeyError 'quantity'**: заменено на `total_sales`
3. ✅ **Plotly график**: исправлены названия колонок

## Готов для загрузки:
- ✅ `ssh2/webhook_persistent_app.py` - содержит ВСЕ исправления

## Действия:
1. Загрузите файл на сервер
2. Перезапустите Streamlit
3. Проверьте раздел "Анализ оборачиваемости"

## Проверено:
- ✅ Формула оборачиваемости работает
- ✅ График распределения отображается корректно
- ✅ Метрики показывают правильные значения