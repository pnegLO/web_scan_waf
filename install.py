#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网络入侵检测与防御系统 - 安装脚本
跨平台版本 (支持Linux, macOS, Windows)
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile
import time
from pathlib import Path

# 颜色定义 (如果支持)
try:
    USE_COLORS = sys.stdout.isatty() and platform.system() != "Windows"
except:
    USE_COLORS = False

RED = '\033[0;31m' if USE_COLORS else ''
GREEN = '\033[0;32m' if USE_COLORS else ''
YELLOW = '\033[0;33m' if USE_COLORS else ''
BLUE = '\033[0;34m' if USE_COLORS else ''
NC = '\033[0m' if USE_COLORS else '' # 恢复默认颜色

def print_info(message):
    """打印信息消息"""
    print(f"{BLUE}[信息]{NC} {message}")

def print_success(message):
    """打印成功消息"""
    print(f"{GREEN}[成功]{NC} {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"{YELLOW}[警告]{NC} {message}")

def print_error(message):
    """打印错误消息"""
    print(f"{RED}[错误]{NC} {message}")

def run_command(command, shell=True, cwd=None, env=None, timeout=None):
    """运行外部命令"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "命令执行超时"
    except Exception as e:
        return 1, "", str(e)

def is_root():
    """检查是否为root/管理员权限"""
    if platform.system() == "Windows":
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.geteuid() == 0

def get_python_executable():
    """获取Python可执行文件路径"""
    return sys.executable

def detect_os():
    """检测操作系统"""
    system = platform.system().lower()
    if system == "linux":
        try:
            with open("/etc/os-release") as f:
                os_info = {}
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key] = value.strip('"\'')
                distro = os_info.get("ID", "unknown")
                version = os_info.get("VERSION_ID", "unknown")
                pretty_name = os_info.get("PRETTY_NAME", f"{distro} {version}")
                return system, distro, version, pretty_name
        except:
            pass
        return system, "unknown", "unknown", "Linux (未知发行版)"
    elif system == "darwin":
        macos_version = platform.mac_ver()[0]
        return system, "macos", macos_version, f"macOS {macos_version}"
    elif system == "windows":
        win_version = platform.win32_ver()[0]
        return system, "windows", win_version, f"Windows {win_version}"
    else:
        return system, "unknown", "unknown", f"{platform.system()} (未知版本)"

def check_python_version():
    """检查Python版本"""
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 6):
        print_error(f"需要Python 3.6或更高版本，但当前版本为{sys.version.split()[0]}")
        return False
    return True

def check_requirements():
    """检查基本要求"""
    # 检查Python版本
    if not check_python_version():
        return False

    # 检查pip是否可用
    return_code, output, error = run_command([sys.executable, "-m", "pip", "--version"])
    if return_code != 0:
        print_error("未找到pip。请确保正确安装了pip。")
        return False

    return True

def install_dependencies(app_dir):
    """安装依赖包"""
    os_type, os_distro, os_version, os_name = detect_os()
    
    # 安装系统依赖
    if os_type == "linux":
        if not is_root():
            print_warning("需要管理员权限以安装系统依赖。")
            print_info("请尝试: sudo python3 install.py")
            response = input("是否继续而不安装系统依赖？(y/n): ")
            if response.lower() != "y":
                return False
        else:
            # 对于Debian/Ubuntu
            if os_distro in ["debian", "ubuntu"]:
                print_info("正在安装系统依赖...")
                pkgs = "python3-venv libpcap-dev tcpdump net-tools iptables ipset build-essential"
                code, out, err = run_command(f"apt-get update && apt-get install -y {pkgs}")
                if code != 0:
                    print_warning(f"安装系统依赖失败: {err}")
                    print_warning("某些功能可能无法正常工作。")
                else:
                    print_success("系统依赖安装完成。")
            
            # 对于RHEL/CentOS/Fedora
            elif os_distro in ["rhel", "centos", "fedora"]:
                print_info("正在安装系统依赖...")
                pkgs = "python3-devel libpcap-devel tcpdump net-tools iptables ipset gcc gcc-c++"
                
                if os_distro == "fedora":
                    cmd = f"dnf install -y {pkgs}"
                else:
                    cmd = f"yum install -y {pkgs}"
                
                code, out, err = run_command(cmd)
                if code != 0:
                    print_warning(f"安装系统依赖失败: {err}")
                    print_warning("某些功能可能无法正常工作。")
                else:
                    print_success("系统依赖安装完成。")
                    
    elif os_type == "darwin":  # macOS
        print_info("检查是否安装了Homebrew...")
        code, out, err = run_command("brew --version")
        if code != 0:
            print_warning("未找到Homebrew。某些功能可能受限。")
            print_info("建议安装Homebrew: https://brew.sh/")
            response = input("是否继续而不安装系统依赖？(y/n): ")
            if response.lower() != "y":
                return False
        else:
            print_info("正在安装系统依赖...")
            pkgs = "libpcap tcpdump"
            code, out, err = run_command(f"brew install {pkgs}")
            if code != 0:
                print_warning(f"安装系统依赖失败: {err}")
                print_warning("某些功能可能无法正常工作。")
            else:
                print_success("系统依赖安装完成。")
    
    # 创建并设置虚拟环境
    print_info("正在设置Python虚拟环境...")
    venv_dir = os.path.join(app_dir, "venv")
    
    # 确保应用目录存在
    if not os.path.exists(app_dir):
        print_error(f"未找到应用目录: {app_dir}")
        return False
    
    # 创建虚拟环境
    code, out, err = run_command([sys.executable, "-m", "venv", venv_dir])
    if code != 0:
        print_error(f"创建虚拟环境失败: {err}")
        return False
    
    # 创建requirements.txt (如果不存在)
    req_file = os.path.join(app_dir, "requirements.txt")
    if not os.path.exists(req_file):
        print_info("正在创建requirements.txt文件...")
        with open(req_file, "w") as f:
            f.write("""Flask==2.2.3
Flask-SocketIO==5.3.2
Werkzeug==2.2.3
python-socketio==5.7.2
python-engineio==4.3.4
eventlet==0.33.3
scapy==2.5.0
psutil==5.9.4
requests==2.28.2
numpy==1.24.2
gevent==22.10.2
gevent-websocket==0.10.1
ipaddress==1.0.23
dnspython==2.3.0
netifaces==0.11.0
matplotlib==3.7.1
""")
            
            # 添加特定平台的依赖
            if os_type == "linux":
                f.write("pyroute2==0.7.3\n")
                f.write("python-iptables==1.0.0\n")
    
    # 获取pip路径
    if os_type == "windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
    
    # 更新pip
    print_info("正在更新pip...")
    code, out, err = run_command([pip_path, "install", "--upgrade", "pip"])
    if code != 0:
        print_warning(f"更新pip失败: {err}")
    
    # 安装依赖包
    print_info("正在安装Python依赖包...")
    code, out, err = run_command([pip_path, "install", "-r", req_file])
    if code != 0:
        print_error(f"安装依赖包失败: {err}")
        print_warning("某些依赖安装失败。系统可能无法正常工作。")
        response = input("是否继续？(y/n): ")
        if response.lower() != "y":
            return False
    
    print_success("Python依赖包安装完成。")
    return True

def configure_permissions(app_dir):
    """配置权限"""
    os_type, os_distro, os_version, os_name = detect_os()
    
    # 仅对Linux和macOS配置权限
    if os_type not in ["linux", "darwin"]:
        return True
    
    print_info("正在配置权限...")
    
    if os_type == "linux" and is_root():
        # 添加当前用户到pcap组
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        if sudo_user:
            code, out, err = run_command(f"usermod -a -G pcap {sudo_user}")
            if code != 0:
                print_warning("无法将用户添加到pcap组。可能需要手动配置权限。")
            
            # 设置应用目录权限
            code, out, err = run_command(f"chown -R {sudo_user}:{sudo_user} {app_dir}")
            if code != 0:
                print_warning("无法设置应用目录权限。")
            
            # 对于tcpdump
            code, out, err = run_command("chmod u+s /usr/bin/tcpdump")
            if code != 0:
                print_warning("无法设置tcpdump的setuid权限。可能需要手动配置。")
    
    # 对于macOS，尝试添加权限
    elif os_type == "darwin" and is_root():
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        if sudo_user:
            # 设置应用目录权限
            code, out, err = run_command(f"chown -R {sudo_user}:{sudo_user} {app_dir}")
            if code != 0:
                print_warning("无法设置应用目录权限。")
    
    print_success("权限配置完成。")
    return True

def create_start_script(app_dir):
    """创建启动脚本"""
    os_type, os_distro, os_version, os_name = detect_os()
    print_info("正在创建启动脚本...")
    
    if os_type in ["linux", "darwin"]:
        # Unix-like系统的bash脚本
        script_path = os.path.join(app_dir, "start.sh")
        with open(script_path, "w") as f:
            f.write("""#!/bin/bash

# 启动网络入侵检测与防御系统
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python app/app.py "$@"
""")
        # 设置可执行权限
        os.chmod(script_path, 0o755)
        print_success(f"启动脚本已创建: {script_path}")
        print_info(f"使用方法: {script_path}")
    
    elif os_type == "windows":
        # Windows的批处理脚本
        script_path = os.path.join(app_dir, "start.bat")
        with open(script_path, "w") as f:
            f.write("""@echo off
:: 启动网络入侵检测与防御系统
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
set PYTHONPATH=%PYTHONPATH%;%CD%
python app\\app.py %*
""")
        print_success(f"启动脚本已创建: {script_path}")
        print_info(f"使用方法: {script_path}")
    
    return True

def create_service(app_dir):
    """创建系统服务"""
    os_type, os_distro, os_version, os_name = detect_os()
    
    if os_type not in ["linux", "darwin"]:
        return False
    
    print_info("是否将系统安装为服务（开机自启动）？")
    response = input("安装系统服务？(y/n): ")
    if response.lower() != "y":
        return False
    
    if os_type == "linux" and is_root():
        # 对于使用systemd的Linux
        service_path = "/etc/systemd/system/intrusion-detection.service"
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        
        with open(service_path, "w") as f:
            f.write(f"""[Unit]
Description=网络入侵检测与防御系统
After=network.target

[Service]
Type=simple
User={sudo_user}
WorkingDirectory={app_dir}
ExecStart={app_dir}/venv/bin/python {app_dir}/app/app.py
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=intrusion-detection

[Install]
WantedBy=multi-user.target
""")
        
        # 刷新systemd并启用服务
        code, out, err = run_command("systemctl daemon-reload")
        if code != 0:
            print_error(f"刷新systemd服务失败: {err}")
            return False
        
        code, out, err = run_command("systemctl enable intrusion-detection.service")
        if code != 0:
            print_error(f"启用系统服务失败: {err}")
            return False
        
        print_success("系统服务创建完成并已启用。")
        print_info("您可以使用以下命令管理服务:")
        print_info("  启动: sudo systemctl start intrusion-detection")
        print_info("  停止: sudo systemctl stop intrusion-detection")
        print_info("  状态: sudo systemctl status intrusion-detection")
        
        return True
    
    elif os_type == "darwin" and is_root():
        # 对于macOS的launchd
        plist_path = "/Library/LaunchDaemons/com.intrusion-detection.plist"
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        
        with open(plist_path, "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.intrusion-detection</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_dir}/venv/bin/python</string>
        <string>{app_dir}/app/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{app_dir}</string>
    <key>StandardErrorPath</key>
    <string>/tmp/intrusion-detection.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/intrusion-detection.out</string>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>""")
        
        # 加载plist文件
        code, out, err = run_command(f"launchctl load {plist_path}")
        if code != 0:
            print_error(f"加载服务失败: {err}")
            return False
        
        print_success("系统服务创建完成并已加载。")
        print_info("您可以使用以下命令管理服务:")
        print_info(f"  启动: sudo launchctl start com.intrusion-detection")
        print_info(f"  停止: sudo launchctl stop com.intrusion-detection")
        print_info(f"  查看: sudo launchctl list | grep intrusion-detection")
        
        return True
    
    else:
        print_warning("需要管理员权限才能创建系统服务。")
        print_info("请尝试: sudo python3 install.py")
        return False

def start_service(app_dir):
    """启动服务"""
    os_type, os_distro, os_version, os_name = detect_os()
    
    print_info("是否现在启动系统？")
    response = input("启动系统？(y/n): ")
    if response.lower() != "y":
        return False
    
    if os_type == "linux" and is_root() and os.path.exists("/etc/systemd/system/intrusion-detection.service"):
        # 使用systemd启动
        code, out, err = run_command("systemctl start intrusion-detection")
        if code != 0:
            print_error(f"启动系统服务失败: {err}")
            return False
        print_success("系统服务已启动！")
    
    elif os_type == "darwin" and is_root() and os.path.exists("/Library/LaunchDaemons/com.intrusion-detection.plist"):
        # 使用launchd启动
        code, out, err = run_command("launchctl start com.intrusion-detection")
        if code != 0:
            print_error(f"启动系统服务失败: {err}")
            return False
        print_success("系统服务已启动！")
    
    else:
        # 手动启动
        if os_type == "windows":
            script_path = os.path.join(app_dir, "start.bat")
            print_info(f"请手动运行启动脚本: {script_path}")
            return False
        else:
            script_path = os.path.join(app_dir, "start.sh")
            sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
            
            if sudo_user and sudo_user != "root" and is_root():
                code, out, err = run_command(f"su - {sudo_user} -c '{script_path}'")
            else:
                code, out, err = run_command(script_path)
                
            if code != 0:
                print_error(f"启动系统失败: {err}")
                return False
            print_success("系统已启动！")
    
    print_info("请访问 http://localhost:8080 查看仪表盘")
    return True

def main():
    """主函数"""
    print("==============================================")
    print("  网络入侵检测与防御系统 - 安装脚本 (Python版)")
    print("==============================================")
    print("")
    
    # 检测操作系统
    os_type, os_distro, os_version, os_name = detect_os()
    print_info(f"检测到操作系统: {os_name}")
    
    # 检查基本要求
    if not check_requirements():
        print_error("系统不满足基本要求，安装已中止。")
        return 1
    
    # 确定应用目录
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intrusion_detection_system")
    print_info(f"应用目录: {app_dir}")
    
    if not os.path.exists(app_dir):
        print_error(f"未找到应用目录: {app_dir}")
        return 1
    
    # 安装依赖
    if not install_dependencies(app_dir):
        print_error("依赖包安装失败，安装已中止。")
        return 1
    
    # 配置权限
    configure_permissions(app_dir)
    
    # 创建启动脚本
    create_start_script(app_dir)
    
    # 创建系统服务
    create_service(app_dir)
    
    # 完成安装
    print_success("安装完成！")
    print_info("您可以通过以下方式启动系统:")
    
    if os_type == "windows":
        print_info(f"  使用启动脚本: {os.path.join(app_dir, 'start.bat')}")
    else:
        print_info(f"  使用启动脚本: {os.path.join(app_dir, 'start.sh')}")
    
    if os_type == "linux" and os.path.exists("/etc/systemd/system/intrusion-detection.service"):
        print_info("  使用系统服务: sudo systemctl start intrusion-detection")
    elif os_type == "darwin" and os.path.exists("/Library/LaunchDaemons/com.intrusion-detection.plist"):
        print_info("  使用系统服务: sudo launchctl start com.intrusion-detection")
    
    print_info("启动后，您可以通过浏览器访问: http://localhost:8080")
    print_info("")
    print_info("要获取更多信息和帮助，请参阅README文档。")
    
    # 启动服务
    start_service(app_dir)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作已取消。")
        sys.exit(1)
    except Exception as e:
        print_error(f"安装过程中出现错误: {str(e)}")
        sys.exit(1) 