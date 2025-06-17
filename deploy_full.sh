#!/bin/bash
# 🚀 Деплой для Windows Git Bash (без sshpass)
# Для root@217.114.1.117

set -e

# ===== КОНФИГУРАЦИЯ =====
REMOTE_USER="root"
REMOTE_HOST="217.114.1.117"
REMOTE_PASSWORD="W5M%gSswG2y%"
REMOTE_PATH="/opt/inventory_system"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# ===== ФУНКЦИЯ SSH БЕЗ SSHPASS =====
# Создаем expect скрипт для автоматического ввода пароля
create_expect_script() {
    cat > ssh_expect.exp << EOF
#!/usr/bin/expect -f
set timeout 30
set host [lindex \$argv 0]
set user [lindex \$argv 1]
set password [lindex \$argv 2]
set command [lindex \$argv 3]

spawn ssh -o StrictHostKeyChecking=no \$user@\$host \$command
expect {
    "*password*" {
        send "\$password\r"
        exp_continue
    }
    "*Password*" {
        send "\$password\r"
        exp_continue
    }
    eof
}
EOF
    chmod +x ssh_expect.exp
}

create_scp_expect_script() {
    cat > scp_expect.exp << EOF
#!/usr/bin/expect -f
set timeout 30
set file [lindex \$argv 0]
set user [lindex \$argv 1]
set host [lindex \$argv 2]
set remote_path [lindex \$argv 3]
set password [lindex \$argv 4]

spawn scp -o StrictHostKeyChecking=no \$file \$user@\$host:\$remote_path
expect {
    "*password*" {
        send "\$password\r"
        exp_continue
    }
    "*Password*" {
        send "\$password\r"
        exp_continue
    }
    eof
}
EOF
    chmod +x scp_expect.exp
}

# ===== АЛЬТЕРНАТИВНЫЙ МЕТОД - СОЗДАНИЕ SSH КЛЮЧЕЙ =====
setup_ssh_key() {
    log_step "Настраиваем SSH ключи для беспарольного доступа..."
    
    # Проверяем есть ли уже ключ
    if [ -f ~/.ssh/id_rsa ]; then
        log_info "SSH ключ уже существует"
    else
        log_info "Создаем новый SSH ключ..."
        ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""
    fi
    
    # Копируем ключ на сервер
    log_info "Копируем ключ на сервер (введите пароль когда попросит)..."
    ssh-copy-id -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" || {
        log_warn "ssh-copy-id не работает, копируем ключ вручную..."
        
        # Читаем публичный ключ
        PUB_KEY=$(cat ~/.ssh/id_rsa.pub)
        
        log_info "Вставьте этот ключ на сервер:"
        echo "================================"
        echo "$PUB_KEY"
        echo "================================"
        
        log_info "Выполните на сервере эти команды:"
        echo "ssh $REMOTE_USER@$REMOTE_HOST"
        echo "mkdir -p ~/.ssh"
        echo "echo '$PUB_KEY' >> ~/.ssh/authorized_keys"
        echo "chmod 700 ~/.ssh"
        echo "chmod 600 ~/.ssh/authorized_keys"
        echo "exit"
        
        read -p "Нажмите Enter после настройки ключей..."
    }
}

# ===== ПРОСТОЙ МЕТОД БЕЗ АВТОМАТИЗАЦИИ =====
manual_deploy() {
    log_step "РУЧНОЙ ДЕПЛОЙ (будете вводить пароль несколько раз)"
    
    # Проверяем подключение
    log_info "Тестируем подключение..."
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" 'echo "Connection OK"'; then
        log_info "✅ SSH подключение работает"
    else
        log_error "❌ Не удается подключиться"
        exit 1
    fi
    
    # Создаем бэкап
    log_step "Создаем бэкап (введите пароль)..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "cd /opt && cp -r inventory_system inventory_backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'Backup skipped'"
    
    # Подготавливаем директории
    log_step "Подготавливаем директории..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_PATH"
    
    # Загружаем файлы
    log_step "Загружаем файлы (будете вводить пароль для каждого файла)..."
    
    files_to_upload=(
        "modular_inventory_system.py"
        "streamlit_modular_app.py"
        "requirements.txt"
        "subcategory_abc.py"
        "integration_patch.py"
        "json_download_fix.py"
        "movement_recommendations.py"
        "price_integration_fix.py"
        "streamlit_deficit_money_update.py"
        "ads_category_fix.py"
        "streamlit_category_ads_ui.py"
        "ads_category_fix_improved.py"
        "streamlit_improved_ads_ui.py"
        "complete_price_integration.py"
        "max_stock_feature.py"
        "warehouse_analysis.py"
        "warehouse_ui.py"
        "real_fix_for_your_system.py"
        "column_names_fix_correct.py"
    )
    
    uploaded_count=0
    for file in "${files_to_upload[@]}"; do
        if [ -f "$file" ]; then
            log_info "Загружаем: $file"
            if scp -o StrictHostKeyChecking=no "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"; then
                ((uploaded_count++))
            else
                log_warn "Не удалось загрузить $file"
            fi
        fi
    done
    
    log_info "✅ Загружено файлов: $uploaded_count"
    
    # Обновляем зависимости и перезапускаем
    log_step "Обновляем систему на сервере..."
    ssh "$REMOTE_USER@$REMOTE_HOST" bash << 'EOF'
        cd /opt/inventory_system
        
        # Проверяем Python
        if ! command -v python3 &> /dev/null; then
            apt update && apt install -y python3 python3-pip python3-venv
        fi
        
        # Создаем/обновляем виртуальное окружение
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        # Устанавливаем зависимости
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Перезапускаем сервис
        systemctl restart inventory-system.service 2>/dev/null || {
            echo "Сервис не найден, создаем..."
            
            # Создаем systemd сервис
            cat > /etc/systemd/system/inventory-system.service << 'SERVICE_EOF'
[Unit]
Description=Inventory Analysis System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory_system
Environment=PATH=/opt/inventory_system/venv/bin
ExecStart=/opt/inventory_system/venv/bin/streamlit run streamlit_modular_app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF
            
            systemctl daemon-reload
            systemctl enable inventory-system.service
            systemctl start inventory-system.service
        }
        
        # Проверяем статус
        sleep 5
        if systemctl is-active --quiet inventory-system.service; then
            echo "✅ Сервис запущен успешно"
        else
            echo "❌ Ошибка запуска сервиса"
            systemctl status inventory-system.service --no-pager
        fi
        
        # Проверяем порт
        if netstat -tlnp 2>/dev/null | grep ':8501' > /dev/null; then
            echo "✅ Порт 8501 открыт"
        else
            echo "⚠️ Порт 8501 не прослушивается"
        fi
EOF
    
    log_info "=== ДЕПЛОЙ ЗАВЕРШЕН ==="
    log_info "🌐 Откройте: http://$REMOTE_HOST:8501"
}

# ===== ИНТЕРАКТИВНОЕ МЕНЮ =====
show_menu() {
    echo "🚀 ДЕПЛОЙ ДЛЯ WINDOWS"
    echo "====================="
    echo ""
    echo "Выберите способ:"
    echo "1) Ручной деплой (вводить пароль несколько раз)"
    echo "2) Настроить SSH ключи (один раз, потом без пароля)"
    echo "3) Только проверить подключение"
    echo "4) Выход"
    echo ""
    read -p "Ваш выбор (1-4): " choice
    
    case $choice in
        1)
            manual_deploy
            ;;
        2)
            setup_ssh_key
            manual_deploy
            ;;
        3)
            log_info "Тестируем подключение..."
            if ssh -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_HOST" 'echo "✅ Подключение работает!"'; then
                log_info "SSH подключение успешно"
            else
                log_error "Подключение не работает"
            fi
            ;;
        4)
            exit 0
            ;;
        *)
            log_error "Неверный выбор"
            show_menu
            ;;
    esac
}

# ===== ПРОСТАЯ ВЕРСИЯ БЕЗ МЕНЮ =====
simple_deploy() {
    echo "🚀 ПРОСТОЙ ДЕПЛОЙ ДЛЯ WINDOWS"
    echo "============================="
    echo ""
    echo "⚠️ Вам нужно будет ввести пароль несколько раз: $REMOTE_PASSWORD"
    echo ""
    read -p "Продолжить? (y/n): " confirm
    
    if [[ $confirm != "y" && $confirm != "Y" ]]; then
        exit 0
    fi
    
    manual_deploy
}

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
main() {
    # Проверяем файлы
    required_files=("modular_inventory_system.py" "streamlit_modular_app.py" "requirements.txt")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "❌ Файл $file не найден!"
            exit 1
        fi
    done
    
    log_info "✅ Основные файлы найдены"
    
    # Запускаем простой деплой
    simple_deploy
}

# Запуск
main "$@"