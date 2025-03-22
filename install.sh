#!/bin/bash

# 网络入侵检测与防御系统 - 安装脚本
# 适用于Ubuntu/Debian系统

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 恢复默认颜色

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$(id -u)" != "0" ]; then
        print_error "此脚本需要root权限才能运行。请使用sudo运行此脚本。"
        exit 1
    fi
}

# 检查操作系统是否为Ubuntu/Debian
check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [ "$ID" != "ubuntu" ] && [ "$ID" != "debian" ]; then
            print_warning "此脚本设计用于Ubuntu/Debian系统，但检测到您运行的是 $PRETTY_NAME"
            read -p "是否继续安装？(y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            print_info "检测到操作系统: $PRETTY_NAME"
        fi
    else
        print_warning "无法确定操作系统类型。此脚本设计用于Ubuntu/Debian系统。"
        read -p "是否继续安装？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 安装依赖包
install_dependencies() {
    print_info "正在更新软件包列表..."
    apt-get update -q || {
        print_error "无法更新软件包列表。"
        exit 1
    }

    print_info "正在安装依赖包..."
    apt-get install -y python3 python3-pip python3-venv libpcap-dev tcpdump net-tools iptables ipset || {
        print_error "安装依赖包失败。"
        exit 1
    }
    
    # 检查是否需要安装开发工具
    if ! command -v gcc &> /dev/null; then
        print_info "正在安装编译工具..."
        apt-get install -y build-essential || {
            print_error "安装编译工具失败。"
            exit 1
        }
    fi
    
    print_success "依赖包安装完成。"
}

# 设置Python虚拟环境
setup_virtualenv() {
    print_info "正在设置Python虚拟环境..."
    
    # 检查目标目录是否存在
    APP_DIR="$(pwd)/intrusion_detection_system"
    if [ ! -d "$APP_DIR" ]; then
        print_error "未找到应用目录 $APP_DIR"
        exit 1
    fi
    
    # 创建并激活虚拟环境
    python3 -m venv "$APP_DIR/venv" || {
        print_error "创建Python虚拟环境失败。"
        exit 1
    }
    
    print_info "正在安装Python依赖包..."
    
    # 创建requirements.txt文件（如果不存在）
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        print_info "正在创建requirements.txt文件..."
        cat > "$APP_DIR/requirements.txt" << 'EOF'
Flask==2.2.3
Flask-SocketIO==5.3.2
Werkzeug==2.2.3
python-socketio==5.7.2
python-engineio==4.3.4
eventlet==0.33.3
scapy==2.5.0
psutil==5.9.4
pyroute2==0.7.3
requests==2.28.2
numpy==1.24.2
gevent==22.10.2
gevent-websocket==0.10.1
ipaddress==1.0.23
dnspython==2.3.0
netifaces==0.11.0
matplotlib==3.7.1
python-iptables==1.0.0
EOF
    fi
    
    # 安装Python依赖
    "$APP_DIR/venv/bin/pip" install --upgrade pip || {
        print_error "更新pip失败。"
    }
    
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" || {
        print_error "安装Python依赖包失败。某些功能可能无法正常工作。"
        read -p "是否继续安装？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    print_success "Python虚拟环境设置完成。"
}

# 配置网络抓包权限
configure_permissions() {
    print_info "正在配置网络抓包权限..."
    
    # 添加当前用户到pcap组
    usermod -a -G pcap $SUDO_USER || {
        print_warning "无法将用户添加到pcap组。可能需要手动配置权限。"
    }
    
    # 设置tcpdump setuid权限
    chmod u+s /usr/bin/tcpdump || {
        print_warning "无法设置tcpdump的setuid权限。可能需要手动配置权限。"
    }
    
    # 设置应用目录权限
    APP_DIR="$(pwd)/intrusion_detection_system"
    chown -R $SUDO_USER:$SUDO_USER "$APP_DIR" || {
        print_warning "无法设置应用目录权限。"
    }
    
    print_success "权限配置完成。"
}

# 创建启动脚本
create_start_script() {
    print_info "正在创建启动脚本..."
    
    APP_DIR="$(pwd)/intrusion_detection_system"
    START_SCRIPT="$APP_DIR/start.sh"
    
    cat > "$START_SCRIPT" << EOF
#!/bin/bash

# 启动网络入侵检测与防御系统
cd "\$(dirname "\$0")"
source venv/bin/activate
export PYTHONPATH="\$PYTHONPATH:\$(pwd)"
python app/app.py "\$@"
EOF

    chmod +x "$START_SCRIPT" || {
        print_error "无法设置启动脚本权限。"
    }
    
    chown $SUDO_USER:$SUDO_USER "$START_SCRIPT" || {
        print_warning "无法设置启动脚本所有权。"
    }
    
    print_success "启动脚本创建完成。"
}

# 创建系统服务（可选）
create_systemd_service() {
    print_info "是否将系统安装为系统服务？(开机自启动)"
    read -p "安装系统服务？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    APP_DIR="$(pwd)/intrusion_detection_system"
    SERVICE_FILE="/etc/systemd/system/intrusion-detection.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=网络入侵检测与防御系统
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app/app.py
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=intrusion-detection

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload || {
        print_error "刷新systemd服务失败。"
    }
    
    systemctl enable intrusion-detection.service || {
        print_error "启用系统服务失败。"
    }
    
    print_success "系统服务创建完成并已启用。"
    print_info "您可以使用以下命令管理服务:"
    print_info "  启动: sudo systemctl start intrusion-detection"
    print_info "  停止: sudo systemctl stop intrusion-detection"
    print_info "  状态: sudo systemctl status intrusion-detection"
}

# 完成安装
finish_installation() {
    APP_DIR="$(pwd)/intrusion_detection_system"
    print_success "安装完成！"
    print_info "您可以通过以下方式启动系统:"
    print_info "  1. 使用启动脚本: $APP_DIR/start.sh"
    
    if [ -f "/etc/systemd/system/intrusion-detection.service" ]; then
        print_info "  2. 使用系统服务: sudo systemctl start intrusion-detection"
    fi
    
    print_info "启动后，您可以通过浏览器访问: http://localhost:8080"
    print_info ""
    print_info "要获取更多信息和帮助，请参阅README文档。"
    
    # 询问是否立即启动
    read -p "是否现在启动系统？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "/etc/systemd/system/intrusion-detection.service" ]; then
            systemctl start intrusion-detection || {
                print_error "启动系统服务失败。请尝试手动启动。"
            }
            print_success "系统服务已启动！"
        else
            # 使用su命令以正确的用户运行脚本
            su - $SUDO_USER -c "$APP_DIR/start.sh" &
            print_success "系统已启动！"
        fi
        print_info "请访问 http://localhost:8080 查看仪表盘"
    fi
}

# 主函数
main() {
    echo "============================================="
    echo "  网络入侵检测与防御系统 - 安装脚本"
    echo "============================================="
    echo ""
    
    check_root
    check_os
    install_dependencies
    setup_virtualenv
    configure_permissions
    create_start_script
    create_systemd_service
    finish_installation
}

# 执行主函数
main 