#!/bin/bash

# Скрипт для синхронизации исправленных файлов иерархии складов на SSH сервер
# Использовать: bash sync_hierarchy_to_ssh.sh

echo "🔄 Синхронизация файлов иерархии складов на SSH сервер..."

# Файлы для копирования
FILES=(
    "webhook_persistent_app.py"
    "hierarchical_movement_system.py"
    "enhanced_warehouse_analysis.py"
    "warehouse_hierarchy_system.py"
    "new_movement_system.py"
    "movement_recommendations.py"
    "warehouse_analysis.py"
)

SERVER="root@217.114.1.117"
TARGET_DIR="/opt/inventory_system/"

echo "📋 Файлы для копирования:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (не найден)"
    fi
done

echo ""
echo "🚀 Начинаем копирование..."

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📤 Копируем $file..."
        scp "$file" "$SERVER:$TARGET_DIR"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ $file успешно скопирован"
        else
            echo "  ❌ Ошибка копирования $file"
        fi
    else
        echo "  ⚠️  Пропускаем $file (файл не найден)"
    fi
done

echo ""
echo "✨ Синхронизация завершена!"
echo ""
echo "📝 Основные изменения:"
echo "  🏢 База Склад Фурнитура Комплект - теперь главный хаб"
echo "  📦 Казыбаева, Астана, Шымкент - склады 2-го уровня"
echo "  🏪 Барыс, АО - магазины напрямую от хаба"
echo "  🛒 Магазины в Астане и Шымкенте - 3-й уровень"
echo ""
echo "🔧 Для применения изменений на сервере:"
echo "  ssh $SERVER"
echo "  cd $TARGET_DIR"
echo "  python3 -c \"from hierarchical_movement_system import HierarchicalMovementSystem; print('✅ Система работает')\""