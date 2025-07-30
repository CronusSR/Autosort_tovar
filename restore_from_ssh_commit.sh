#\!/bin/bash
# Восстановление файлов из коммита "ssh"

echo "🔄 Восстановление файлов из коммита 'ssh'"
echo "========================================"

# Проверяем текущее состояние
echo "📋 Текущий коммит:"
git log --oneline -1

echo ""
echo "🎯 Восстанавливаем файлы из коммита bd668a7 'ssh'..."

# Восстанавливаем основные файлы из коммита ssh
git checkout bd668a7 -- webhook_persistent_app.py
git checkout bd668a7 -- webhook_data_accumulator.py
git checkout bd668a7 -- modular_inventory_system.py

echo "✅ Файлы восстановлены из коммита 'ssh'"

# Проверяем какие файлы восстановлены
echo ""
echo "📄 Восстановленные файлы:"
ls -la webhook_persistent_app.py webhook_data_accumulator.py modular_inventory_system.py 2>/dev/null || echo "Некоторые файлы не найдены"

# Проверяем синтаксис основного файла
echo ""
echo "🔍 Проверяем синтаксис webhook_persistent_app.py..."
python3 -c "
import py_compile
try:
    py_compile.compile('webhook_persistent_app.py', doraise=True)
    print('✅ Синтаксис корректен')
except py_compile.PyCompileError as e:
    print(f'❌ Ошибка синтаксиса: {e}')
"

# Копируем файлы на сервер
echo ""
echo "📤 Копируем файлы на сервер..."

# Список файлов для копирования
FILES=(
    "webhook_persistent_app.py"
    "webhook_data_accumulator.py"
    "modular_inventory_system.py"
)

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   📄 Копируем $file..."
        scp "$file" "$SERVER:$TARGET_DIR"
    else
        echo "   ⚠️  Файл $file не найден"
    fi
done

# Перезапускаем приложение на сервере
echo ""
echo "🔄 Перезапускаем приложение на сервере..."
ssh "$SERVER" "cd $TARGET_DIR && pkill -f webhook_persistent_app && sleep 2 && nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 & echo 'PID: \$\!'"

echo ""
echo "✅ ГОТОВО\! Файлы из коммита 'ssh' восстановлены и развернуты на сервере"
echo ""
echo "📋 Для проверки логов:"
echo "   ssh $SERVER 'tail -f $TARGET_DIR/webhook_8502.log'"
echo ""
echo "🌐 Приложение доступно на порту 8502"
