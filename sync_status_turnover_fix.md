# Статус синхронизации после исправления формулы оборачиваемости

## Текущий статус файлов:

### ✅ webhook_receiver.py
- **Локально**: версия 2.1 (раздельные папки) - 14854 байт
- **На сервере**: версия 2.1 (раздельные папки) 
- **Статус**: ✅ СИНХРОНИЗИРОВАНО

### ⚠️ webhook_persistent_app.py 
- **Локально**: ИСПРАВЛЕНО - новая формула оборачиваемости (62593 байт)
- **На сервере**: старая формула (размер неизвестен)
- **Статус**: ❌ ТРЕБУЕТСЯ СИНХРОНИЗАЦИЯ

### ✅ webhook_data_accumulator.py
- **Локально**: 16038 байт
- **На сервере**: предположительно синхронизирован
- **Статус**: ✅ ВЕРОЯТНО СИНХРОНИЗИРОВАНО

## Исправление в webhook_persistent_app.py:

### Что изменено:
- **Функция**: `calculate_turnover()` (строка ~96)
- **Старая формула**: `(stock_quantity / daily_sales) * period_days`
- **Новая формула**: `(остатки / продажи) * 30.5`

### Детали изменения:
```python
# БЫЛО:
turnover_data['turnover_days'] = np.where(
    turnover_data['daily_sales'] > 0,
    (turnover_data['stock_quantity'] / turnover_data['daily_sales']) * period_days,
    999999
)

# СТАЛО:
turnover_data['turnover_days'] = np.where(
    turnover_data['total_sales'] > 0,
    (turnover_data['stock_quantity'] / turnover_data['total_sales']) * 30.5,
    999999
)
```

## Готовые файлы для загрузки:

### 📁 ssh2/webhook_persistent_app.py
- ✅ Содержит исправленную формулу оборачиваемости
- ✅ Готов для загрузки на сервер
- ✅ Обратная совместимость сохранена

## Действия для синхронизации:

1. **Загрузите файл на сервер**:
   ```bash
   scp ssh2/webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/
   ```

2. **Перезапустите Streamlit приложение**:
   ```bash
   ssh root@217.114.1.117
   cd /opt/inventory_system
   pkill -f 'streamlit run webhook_persistent_app.py'
   nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &
   ```

3. **Проверьте работу**:
   - Откройте http://217.114.1.117:8502
   - Перейдите в раздел "Анализ оборачиваемости"
   - Убедитесь что формула работает как (остатки/продажи)*30.5

## Резервные копии:
- `webhook_persistent_app_backup_*.py` - локальные резервные копии
- Рекомендуется создать резервную копию на сервере перед применением

## Проверка синхронизации:
После загрузки используйте:
```bash
./quick_check.sh
```
Чтобы убедиться что файлы синхронизированы.