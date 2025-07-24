#!/bin/bash

# Обработка ZIP напрямую на сервере (обход webhook)
SERVER="217.114.1.117"
USER="root"
REMOTE_PATH="/opt/inventory_system"

echo "📦 ПРЯМАЯ ОБРАБОТКА ZIP НА СЕРВЕРЕ"
echo "📅 Время: $(date)"
echo ""

# Проверяем что ZIP уже загружен или загружаем
echo "📤 Проверка ZIP файла на сервере..."
ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    
    if [ -f 'test_zip.zip' ]; then
        echo '✅ ZIP файл уже на сервере'
    else
        echo '❌ ZIP файл не найден, загрузите его:'
        echo '   scp \"Выгрузка JSON.zip\" root@$SERVER:$REMOTE_PATH/test_zip.zip'
        exit 1
    fi
"

echo ""
echo "🔧 Обработка ZIP файла напрямую..."

ssh "$USER@$SERVER" "
    cd $REMOTE_PATH
    source venv/bin/activate
    
    echo '🧪 Запуск обработки ZIP...'
    python3 << 'PYTHON_SCRIPT'
import sys
sys.path.append('.')

try:
    from webhook_zip_handler import WebhookZipHandler
    from webhook_data_accumulator import WebhookDataAccumulator
    
    print('📦 Чтение ZIP файла...')
    with open('test_zip.zip', 'rb') as f:
        zip_data = f.read()
    
    print(f'📏 Размер: {len(zip_data):,} байт')
    
    # Обработка ZIP
    handler = WebhookZipHandler(upload_dir='./webhook_uploads')
    result = handler.process_zip_file(zip_data, 'test_zip.zip')
    
    print(f'\\n📊 Результат обработки:')
    print(f'   Статус: {result.get(\"status\")}')
    print(f'   Файлов: {result.get(\"files_processed\", 0)}')
    print(f'   Записей: {result.get(\"total_records\", 0)}')
    
    if result.get('status') == 'success':
        print('\\n✅ ZIP успешно обработан!')
        
        # Обработка накопителем
        print('\\n🔄 Обработка накопителем данных...')
        accumulator = WebhookDataAccumulator()
        
        processed_count = 0
        for file_info in result.get('files', []):
            from pathlib import Path
            file_path = Path(file_info['saved_path'])
            if file_path.exists():
                acc_result = accumulator.process_new_sales_file(file_path)
                if acc_result['status'] == 'success':
                    processed_count += 1
                    print(f'   ✅ {file_info[\"filename\"]}: {acc_result[\"records_added\"]} новых записей')
        
        print(f'\\n📊 Итого обработано накопителем: {processed_count} файлов')
        
        # Статистика БД
        summary = accumulator.get_data_summary()
        print(f'\\n📈 Статистика базы данных:')
        print(f'   Всего записей: {summary[\"sales\"][\"total_records\"]}')
        print(f'   Период: {summary[\"sales\"].get(\"first_date\")} - {summary[\"sales\"].get(\"last_date\")}')
        print(f'   Филиалов: {summary[\"sales\"][\"branches_count\"]}')
        print(f'   Товаров: {summary[\"sales\"][\"items_count\"]}')
        
    else:
        print(f'\\n❌ Ошибка: {result.get(\"message\")}')
        
except Exception as e:
    import traceback
    print(f'\\n❌ Ошибка обработки: {e}')
    traceback.print_exc()
PYTHON_SCRIPT
"

echo ""
echo "🌐 Проверка аналитики:"
echo "Откройте: http://$SERVER:8502"
echo ""
echo "✅ Обработка завершена!"