# 🔄 ПЕРЕЗАПУСК STREAMLIT НА СЕРВЕРЕ

## Файл загружен ✅, но нужно перезапустить приложение!

### Подключитесь к серверу и выполните:

```bash
ssh root@217.114.1.117
cd /opt/inventory_system
```

### 1. Остановите старое приложение:
```bash
pkill -f 'streamlit run webhook_persistent_app.py'
```

### 2. Подождите 2-3 секунды:
```bash
sleep 3
```

### 3. Запустите новое приложение:
```bash
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > streamlit_8502.log 2>&1 &
```

### 4. Проверьте что запустилось:
```bash
ps aux | grep streamlit
```

### 5. Проверьте доступность:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8502
```
(должно вернуть 200)

## После перезапуска:
- Откройте http://217.114.1.117:8502
- Перейдите в "Анализ оборачиваемости"  
- Товар "19*0,8мм ПВХ Маренго AN" должен показывать **73.08 дней**

## Если что-то пошло не так:
Посмотрите логи:
```bash
tail -f streamlit_8502.log
```