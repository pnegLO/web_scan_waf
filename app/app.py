#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

# 导入自定义模块
from modules.traffic_detection.detector import TrafficDetector
from modules.intrusion_prevention.prevention import IntrusionPrevention
from modules.alert_response.alerter import AlertSystem
from modules.network_monitoring.monitor import NetworkMonitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/ids_system.log')
    ]
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

# 创建数据目录
os.makedirs('data', exist_ok=True)

# 初始化系统模块
traffic_detector = TrafficDetector()
intrusion_prevention = IntrusionPrevention()
alert_system = AlertSystem()
network_monitor = NetworkMonitor(socketio)

# 管理系统状态
system_status = {
    'is_running': False,
    'start_time': None,
    'processed_packets': 0,
    'detected_threats': 0,
    'blocked_attacks': 0
}

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logs')
def logs():
    return render_template('logs.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# API路由
@app.route('/api/status')
def get_status():
    return jsonify(system_status)

@app.route('/api/start', methods=['POST'])
def start_system():
    if not system_status['is_running']:
        system_status['is_running'] = True
        system_status['start_time'] = time.time()
        
        # 启动各个模块
        threading.Thread(target=traffic_detector.start_capture).start()
        threading.Thread(target=intrusion_prevention.start_prevention).start()
        threading.Thread(target=alert_system.start_alerting).start()
        threading.Thread(target=network_monitor.start_monitoring).start()
        
        logger.info("系统已启动")
        return jsonify({'success': True, 'message': '系统已启动'})
    
    return jsonify({'success': False, 'message': '系统已在运行中'})

@app.route('/api/stop', methods=['POST'])
def stop_system():
    if system_status['is_running']:
        system_status['is_running'] = False
        
        # 停止各个模块
        traffic_detector.stop_capture()
        intrusion_prevention.stop_prevention()
        alert_system.stop_alerting()
        network_monitor.stop_monitoring()
        
        logger.info("系统已停止")
        return jsonify({'success': True, 'message': '系统已停止'})
    
    return jsonify({'success': False, 'message': '系统未运行'})

@app.route('/api/logs')
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    return jsonify({'logs': alert_system.get_recent_alerts(limit)})

@app.route('/api/threats')
def get_threats():
    return jsonify({'threats': intrusion_prevention.get_recent_threats()})

# Socket.IO 事件
@socketio.on('connect')
def handle_connect():
    logger.info(f"客户端已连接: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"客户端已断开连接: {request.sid}")

# 主函数
if __name__ == '__main__':
    try:
        logger.info("网络入侵检测与防御系统启动中...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        logger.error(f"系统启动失败: {str(e)}")
