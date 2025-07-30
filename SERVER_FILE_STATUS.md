# 🚨 СТАТУС ФАЙЛА НА СЕРВЕРЕ

## Проблема:
Расчет оборачиваемости все еще неправильный:
- Остатки: 22
- Продажи: 9.18  
- Показывает: 2.4 (неверно)
- Должно быть: (22/9.18)*30.5 = **73.08 дней**

## ✅ Локальный файл ИСПРАВЛЕН:
```bash
grep -n "stock_quantity.*total_sales.*30.5" webhook_persistent_app.py
99:        (turnover_data['stock_quantity'] / turnover_data['total_sales']) * 30.5,
289:        (city_turnover['stock_quantity'] / city_turnover['total_sales']) * 30.5,
```

## 📁 Файл готов для загрузки:
- `ssh2/webhook_persistent_app.py` (62905 байт, обновлен 05:31)
- Содержит исправления ОБЕИХ функций расчета

## ❌ На сервере все еще старая версия!

### Что нужно сделать:
1. **Загрузить исправленный файл:**
   ```bash
   scp ssh2/webhook_persistent_app.py root@217.114.1.117:/opt/inventory_system/
   ```

2. **Перезапустить Streamlit на сервере:**
   ```bash
   ssh root@217.114.1.117
   cd /opt/inventory_system
   pkill -f 'streamlit run webhook_persistent_app.py'
   nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &
   ```

3. **Проверить что приложение запустилось:**
   ```bash
   ps aux | grep streamlit
   curl -s -o /dev/null -w "%{http_code}" http://217.114.1.117:8502
   ```

## Все исправления в файле:
1. ✅ Основная функция `calculate_turnover()` - строка 99
2. ✅ Функция по городам `calculate_turnover_by_city()` - строка 289  
3. ✅ Исправлен KeyError 'quantity' → 'total_sales'
4. ✅ Исправлен график распределения Plotly

## После загрузки и перезапуска:
Товар "19*0,8мм ПВХ Маренго AN" должен показывать:
**73.08 дней** вместо 2.4