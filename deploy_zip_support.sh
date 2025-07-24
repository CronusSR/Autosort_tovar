#!/bin/bash

# Скрипт обновления системы для поддержки ZIP файлов
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📦 Обновление системы для поддержки ZIP архивов..."
echo "📅 Время: $(date)"

# Создаем временную директорию
TEMP_DIR="/tmp/zip_support_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "📦 Подготовка файлов с поддержкой ZIP..."

# Новые файлы с поддержкой ZIP
cp webhook_zip_handler.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_zip_handler.py"
cp webhook_receiver_zip_updated.py "$TEMP_DIR/webhook_receiver.py" 2>/dev/null && echo "✅ webhook_receiver.py (обновленный)"

# Обновленный накопитель данных
cp webhook_data_accumulator.py "$TEMP_DIR/" 2>/dev/null && echo "✅ webhook_data_accumulator.py"

# Приложение с полной логикой
cp webhook_enhanced_app.py "$TEMP_DIR/webhook_persistent_app.py" 2>/dev/null && echo "✅ webhook_persistent_app.py (расширенное)"

# Все необходимые модули
cp modular_inventory_system.py "$TEMP_DIR/" 2>/dev/null && echo "✅ modular_inventory_system.py"
cp single_file_ads_processor.py "$TEMP_DIR/" 2>/dev/null && echo "✅ single_file_ads_processor.py"

# Создаем скрипт обновления на сервере
cat > "$TEMP_DIR/update_for_zip.sh" << 'EOF'
#!/bin/bash

echo "🔧 Обновление системы для поддержки ZIP..."

# Активируем виртуальное окружение
source venv/bin/activate

echo "📦 Установка дополнительных зависимостей для ZIP..."
pip install zipfile-deflate64 || echo "Используем стандартный zipfile"

echo "🔄 Остановка сервисов..."
systemctl stop webhook-receiver
systemctl stop webhook-analytics

echo "💾 Создание резервной копии..."
mkdir -p backups
cp webhook_receiver.py backups/webhook_receiver_$(date +%Y%m%d_%H%M%S).py 2>/dev/null || true
cp webhook_persistent_app.py backups/webhook_persistent_app_$(date +%Y%m%d_%H%M%S).py 2>/dev/null || true

echo "🔄 Запуск обновленных сервисов..."
systemctl start webhook-receiver
systemctl start webhook-analytics

sleep 5

echo "📊 Проверка статуса..."
echo "=== Webhook Receiver ==="
systemctl status webhook-receiver --no-pager | head -10

echo ""
echo "=== Webhook Analytics ==="
systemctl status webhook-analytics --no-pager | head -10

echo ""
echo "🔍 Тестирование поддержки ZIP..."
curl -s http://localhost:5000/webhook/status | grep -q "ZIP support" && {
    echo "✅ Поддержка ZIP активна"
} || {
    echo "⚠️  Поддержка ZIP может быть не активна"
}

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "🆕 НОВЫЕ ВОЗМОЖНОСТИ:"
echo "   • Поддержка ZIP архивов в /webhook/sales"
echo "   • Автоматическое извлечение JSON файлов"
echo "   • Обработка новой структуры данных от 1С"
echo "   • Улучшенная категоризация товаров"
echo ""
EOF

chmod +x "$TEMP_DIR/update_for_zip.sh"

# Создаем инструкцию для 1С программиста
cat > "$TEMP_DIR/1C_ZIP_INSTRUCTIONS.md" << 'EOF'
# 📦 ОБНОВЛЕННАЯ ИНСТРУКЦИЯ ДЛЯ 1С - ПОДДЕРЖКА ZIP

## 🆕 ЧТО ИЗМЕНИЛОСЬ

Система теперь поддерживает **ZIP архивы** в дополнение к обычным JSON файлам.

## 📤 СПОСОБЫ ОТПРАВКИ ДАННЫХ

### Способ 1: ZIP архив (РЕКОМЕНДУЕТСЯ)
```http
POST http://217.114.1.117:5000/webhook/sales
Content-Type: application/zip
X-Hub-Signature-256: sha256={подпись}

[ZIP архив с JSON файлами]
```

### Способ 2: Обычный JSON (как раньше)
```http
POST http://217.114.1.117:5000/webhook/sales
Content-Type: application/json
X-Hub-Signature-256: sha256={подпись}

[JSON данные]
```

## 📁 СТРУКТУРА ZIP АРХИВА

```
Выгрузка JSON.zip
└── Выгрузка JSON/
    ├── 2024-01-31.json
    ├── 2024-02-29.json
    └── 2024-03-31.json
```

## 📊 НОВАЯ СТРУКТУРА JSON

```json
[{
  "ДатаВыгрузки": "2025-07-23T15:30:18",
  "НачалоПериода": "2024-01-01",
  "КонецПериода": "2024-01-31", 
  "Филиал": "4 Склад фурнитуры АЗМ Шымкент",
  "Продажи": [
    {
      "День": "2024-01-08",
      "ПродажиПоДням": [
        {
          "ПутьКатегорий": "Кромка ПВХ/Кромочные материалы/Мебельная фурнитура/",
          "Номенклатура": "19*0,8мм ПВХ Бетон пайн белый AN",
          "Количество": 206,
          "Выручка": 9064,
          "Артикул": "AK024",
          "Производитель": "Китай",
          "ЕдиницаИзмерения": "Метр"
        }
      ]
    }
  ]
}]
```

## 💻 ПРИМЕР КОДА 1С ДЛЯ ZIP

```1c
Процедура ОтправитьZIPНаСервер(ПутьКZIP)
    
    АдресСервера = "217.114.1.117";
    ПортСервера = "5000"; 
    СекретныйКлюч = "furniture_company_secret_key_2025";
    URL = "http://" + АдресСервера + ":" + ПортСервера + "/webhook/sales";
    
    // Читаем ZIP файл
    ФайлZIP = Новый Файл(ПутьКZIP);
    ЧтениеДанных = Новый ЧтениеДанных(ФайлZIP.ПолноеИмя);
    ДанныеZIP = ЧтениеДанных.Прочитать();
    ЧтениеДанных.Закрыть();
    
    // Создаем подпись
    Подпись = ВычислитьПодписьHMAC(ДанныеZIP, СекретныйКлюч);
    
    // HTTP запрос
    HTTPСоединение = Новый HTTPСоединение(АдресСервера, Число(ПортСервера));
    HTTPЗапрос = Новый HTTPЗапрос("/webhook/sales");
    HTTPЗапрос.УстановитьТелоИзДвоичныхДанных(ДанныеZIP);
    HTTPЗапрос.Заголовки.Вставить("Content-Type", "application/zip");
    HTTPЗапрос.Заголовки.Вставить("X-Hub-Signature-256", "sha256=" + Подпись);
    
    // Отправляем
    HTTPОтвет = HTTPСоединение.ВызватьHTTPМетод("POST", HTTPЗапрос);
    
    Если HTTPОтвет.КодСостояния = 200 Тогда
        Сообщить("ZIP архив успешно отправлен!");
    Иначе
        Сообщить("Ошибка отправки ZIP: " + HTTPОтвет.КодСостояния);
    КонецЕсли;
    
КонецПроцедуры
```

## ✅ ПРЕИМУЩЕСТВА ZIP

- 📦 Отправка множества месяцев за раз
- 🗜️ Сжатие данных (экономия трафика)
- 🔄 Автоматическая обработка всех файлов
- 📊 Улучшенная категоризация товаров

## 🔍 ПРОВЕРКА РАБОТЫ

```bash
# Проверка поддержки ZIP
curl http://217.114.1.117:5000/webhook/status

# Должно вернуть: "supported_formats": ["JSON", "ZIP"]
```
EOF

# Создаем архив
echo -e "\n📦 Создание архива..."
cd "$TEMP_DIR"
tar -czf zip_support_update.tar.gz * || { echo "❌ Ошибка создания архива"; exit 1; }

# Загружаем на сервер
echo -e "\n📤 Загрузка обновления на сервер..."
scp zip_support_update.tar.gz "$USER@$SERVER:$REMOTE_PATH/" || { echo "❌ Ошибка загрузки"; exit 1; }

# Применяем обновление
echo -e "\n🔧 Применение обновления на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH && 
    tar -xzf zip_support_update.tar.gz && 
    rm zip_support_update.tar.gz &&
    chmod +x update_for_zip.sh &&
    ./update_for_zip.sh
"

# Проверяем результат
echo -e "\n🔍 Проверка обновления..."
sleep 5

echo "Проверка webhook с поддержкой ZIP..."
curl -s "http://$SERVER:5000/webhook/status" | grep -q "ZIP support" && {
    echo "✅ Поддержка ZIP активна!"
} || {
    echo "⚠️  Webhook сервер еще запускается..."
}

echo -e "\nПроверка аналитического приложения..."
curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8502" | grep -q "200" && {
    echo "✅ Расширенная аналитика работает!"
} || {
    echo "⚠️  Аналитическое приложение недоступно"
}

# Очистка
rm -rf "$TEMP_DIR"

echo -e "\n🎉 ОБНОВЛЕНИЕ ДЛЯ ZIP ЗАВЕРШЕНО!"
echo ""
echo "🆕 НОВЫЕ ВОЗМОЖНОСТИ:"
echo "   📦 Поддержка ZIP архивов"
echo "   🔄 Автоматическое извлечение файлов"  
echo "   📊 Улучшенная категоризация"
echo "   🏪 Полная логика межфилиальных перемещений"
echo ""
echo "🔗 Адреса:"
echo "   • Webhook (JSON/ZIP): http://$SERVER:5000/webhook/sales"
echo "   • Аналитика: http://$SERVER:8502"
echo ""
echo "📋 Инструкция для 1С загружена на сервер:"
echo "   • 1C_ZIP_INSTRUCTIONS.md"