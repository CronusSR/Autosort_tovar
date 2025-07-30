#\!/bin/bash
# Исправление синтаксической ошибки

echo "🔧 Исправление синтаксической ошибки"
echo "===================================="

# Исправляем прямо на сервере
ssh root@217.114.1.117 << 'REMOTE_EOF'
cd /opt/inventory_system

echo "🔍 Проверяем строку 998..."
sed -n '995,1005p' webhook_persistent_app.py

echo ""
echo "🔧 Исправляем синтаксическую ошибку..."

# Используем sed для исправления
sed -i 's/st\.session_state\.expanded_categories = set()        def build_category_tree(_df):/st.session_state.expanded_categories = set()\
\
        def build_category_tree(_df):/' webhook_persistent_app.py

echo "✅ Исправление применено"

echo "🔍 Проверяем результат..."
sed -n '995,1005p' webhook_persistent_app.py

echo ""
echo "🔄 Перезапускаем приложение..."
pkill -f webhook_persistent_app
sleep 2
nohup streamlit run webhook_persistent_app.py --server.port 8502 --server.address 0.0.0.0 > webhook_8502.log 2>&1 &
echo "PID: $\!"

echo ""
echo "✅ ГОТОВО\!"
REMOTE_EOF

echo ""
echo "📋 Для проверки логов:"
echo "   ssh root@217.114.1.117 'tail -f /opt/inventory_system/webhook_8502.log'"
