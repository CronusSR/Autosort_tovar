# 🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ - KeyError: 'quantity'

## Проблема:
После исправления формулы оборачиваемости возникла ошибка:
```
KeyError: 'quantity' в строке 558
```

## Причина:
В функции `calculate_turnover()` мы переименовали поле `quantity` → `total_sales`, но в строке 558 все еще используется старое название.

## ✅ ИСПРАВЛЕНО:

### Строка 558:
```python
# БЫЛО (ошибка):
total_stock_value = (turnover_data['stock_quantity'] * turnover_data['amount'] / turnover_data['quantity']).sum()

# СТАЛО (исправлено):
total_stock_value = (turnover_data['stock_quantity'] * turnover_data['amount'] / turnover_data['total_sales']).sum()
```

## Файлы обновлены:
- ✅ `webhook_persistent_app.py` - исправлен локально
- ✅ `ssh2/webhook_persistent_app.py` - готов для загрузки на сервер

## Действия:
1. Загрузите исправленный файл на сервер:
   ```bash
   scp ssh2/webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/
   ```

2. Перезапустите приложение:
   ```bash
   ssh root@217.114.1.117
   cd /opt/inventory_system  
   pkill -f 'streamlit run webhook_persistent_app.py'
   nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &
   ```

## Проверено:
- ✅ Больше нет ссылок на `turnover_data['quantity']` в коде
- ✅ Формула оборачиваемости работает: `(остатки/продажи)*30.5`
- ✅ Обратная совместимость сохранена