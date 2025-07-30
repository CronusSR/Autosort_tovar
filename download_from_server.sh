#\!/bin/bash
# Скрипт для загрузки актуальных файлов с сервера

echo "📥 Загрузка файлов с сервера..."
echo "================================"

SERVER="root@217.114.1.117"
REMOTE_DIR="/opt/inventory_system/"
LOCAL_DIR="./ssh/"

# Создаем директорию если её нет
mkdir -p $LOCAL_DIR

# Список файлов для загрузки
FILES=(
    "webhook_persistent_app.py"
    "webhook_data_accumulator.py"
    "modular_inventory_system.py"
)

echo "🔄 Загружаем файлы с сервера..."
for file in "${FILES[@]}"; do
    echo "   📄 $file"
    scp $SERVER:$REMOTE_DIR$file $LOCAL_DIR
done

echo ""
echo "✅ Файлы загружены в папку $LOCAL_DIR"
echo ""
echo "🔧 Теперь можно использовать файлы из папки ssh/"

# Создаем резервную копию текущего файла
if [ -f "webhook_persistent_app.py" ]; then
    echo "📋 Создаем резервную копию текущего webhook_persistent_app.py"
    cp webhook_persistent_app.py webhook_persistent_app.py.backup_$(date +%Y%m%d_%H%M%S)
fi

echo ""
echo "Для замены текущего файла на версию с сервера выполните:"
echo "   cp ssh/webhook_persistent_app.py webhook_persistent_app.py"
