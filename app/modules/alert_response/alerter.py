#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import random
import logging
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self, socketio=None):
        self.is_running = False
        self.alert_thread = None
        self.socketio = socketio
        
        # 告警配置
        self.config = {
            'web_notification': True,
            'email_notification': False,
            'email_recipients': [],
            'min_severity': 'medium',  # low, medium, high
            'alert_throttling': True,  # 限制告警频率
            'throttle_period': 300,    # 5分钟内相同IP的相同类型告警只发送一次
        }
        
        # 告警数据
        self.alerts = []
        self.recent_alerts = {}  # 用于告警频率限制
        
        # 创建数据目录
        os.makedirs('data/alerts', exist_ok=True)
    
    def start_alerting(self):
        """启动告警系统"""
        if not self.is_running:
            self.is_running = True
            self.alert_thread = threading.Thread(target=self._alert_worker)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            logger.info("告警系统已启动")
    
    def stop_alerting(self):
        """停止告警系统"""
        if self.is_running:
            self.is_running = False
            if self.alert_thread:
                self.alert_thread.join(timeout=2)
            self._save_alerts()
            logger.info("告警系统已停止")
    
    def _alert_worker(self):
        """告警处理线程"""
        last_save_time = time.time()
        
        while self.is_running:
            try:
                # 模拟告警生成
                self._simulate_alerts()
                
                # 每小时保存一次告警数据
                current_time = time.time()
                if current_time - last_save_time >= 3600:  # 3600秒 = 1小时
                    self._save_alerts()
                    last_save_time = current_time
                
                # 清理过时的告警频率限制记录
                self._cleanup_throttling()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"告警处理错误: {str(e)}")
                time.sleep(10)  # 出错后等待10秒重试
    
    def _simulate_alerts(self):
        """模拟生成告警（用于演示）"""
        # 20%的概率生成告警
        if random.random() < 0.2:
            alert_types = [
                'SQL注入攻击', 'XSS攻击', 'DDoS攻击', '端口扫描', 
                '暴力破解', '异常流量', '可疑文件下载'
            ]
            
            severity_map = {
                0: '低',
                1: '中',
                2: '高'
            }
            
            alert_type = random.choice(alert_types)
            severity_level = random.randint(0, 2)
            severity = severity_map[severity_level]
            src_ip = f"192.168.1.{random.randint(2, 254)}"
            dst_ip = f"10.0.0.{random.randint(2, 254)}"
            
            # 创建告警数据
            alert = {
                'alert_id': f"ALERT-{int(time.time())}-{random.randint(1000, 9999)}",
                'timestamp': datetime.now().isoformat(),
                'alert_type': alert_type,
                'severity': severity,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'port': random.randint(1, 65535),
                'protocol': random.choice(['TCP', 'UDP', 'HTTP']),
                'details': f"检测到{alert_type}攻击尝试",
                'action_taken': random.choice(['已阻止', '已记录'])
            }
            
            # 处理告警
            self.process_alert(alert)
    
    def process_alert(self, alert_data):
        """处理告警数据"""
        try:
            # 添加到告警列表
            self.alerts.append(alert_data)
            
            # 限制告警列表大小
            if len(self.alerts) > 10000:
                self.alerts = self.alerts[-10000:]
            
            # 检查是否需要发送通知
            should_notify = self._should_send_notification(alert_data)
            
            if should_notify:
                # 发送Web通知
                if self.config['web_notification'] and self.socketio:
                    self.socketio.emit('new_alert', alert_data)
                
                # 发送邮件通知
                if self.config['email_notification'] and self.config['email_recipients']:
                    self._send_email_notification(alert_data)
            
            logger.info(f"处理告警: {alert_data['alert_type']}, 严重性: {alert_data['severity']}, 来源: {alert_data['src_ip']}")
            
            return True
        
        except Exception as e:
            logger.error(f"处理告警失败: {str(e)}")
            return False
    
    def _should_send_notification(self, alert_data):
        """检查是否应该发送通知"""
        # 检查严重程度
        severity_levels = {'低': 0, '中': 1, '高': 2}
        min_severity_levels = {'low': 0, 'medium': 1, 'high': 2}
        
        alert_severity = severity_levels.get(alert_data['severity'], 0)
        config_min_severity = min_severity_levels.get(self.config['min_severity'], 1)
        
        if alert_severity < config_min_severity:
            return False
        
        # 检查告警频率限制
        if self.config['alert_throttling']:
            alert_key = f"{alert_data['src_ip']}_{alert_data['alert_type']}"
            current_time = time.time()
            
            if alert_key in self.recent_alerts:
                last_time = self.recent_alerts[alert_key]
                if current_time - last_time < self.config['throttle_period']:
                    return False
            
            self.recent_alerts[alert_key] = current_time
        
        return True
    
    def _send_email_notification(self, alert_data):
        """发送邮件通知"""
        # 实际应用中，这里应该连接SMTP服务器发送邮件
        # 这里只做日志记录
        recipients = ', '.join(self.config['email_recipients'])
        logger.info(f"发送邮件告警到: {recipients}, 告警类型: {alert_data['alert_type']}")
        
        # 以下是实际发送邮件的代码，需要在配置中添加SMTP设置
        '''
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.config['smtp_sender']
            msg['To'] = ', '.join(self.config['email_recipients'])
            msg['Subject'] = f"安全告警: {alert_data['severity']} - {alert_data['alert_type']}"
            
            # 邮件正文
            body = f"""
            <html>
            <body>
                <h2>安全告警</h2>
                <p><strong>时间:</strong> {alert_data['timestamp']}</p>
                <p><strong>类型:</strong> {alert_data['alert_type']}</p>
                <p><strong>严重程度:</strong> {alert_data['severity']}</p>
                <p><strong>源IP:</strong> {alert_data['src_ip']}</p>
                <p><strong>目标IP:</strong> {alert_data['dst_ip']}</p>
                <p><strong>端口:</strong> {alert_data['port']}</p>
                <p><strong>协议:</strong> {alert_data['protocol']}</p>
                <p><strong>详情:</strong> {alert_data['details']}</p>
                <p><strong>操作:</strong> {alert_data['action_taken']}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['smtp_username'], self.config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件告警发送成功: {msg['Subject']}")
            
        except Exception as e:
            logger.error(f"发送邮件告警失败: {str(e)}")
        '''
    
    def _cleanup_throttling(self):
        """清理过时的告警频率限制记录"""
        current_time = time.time()
        expired_keys = [k for k, v in self.recent_alerts.items() 
                       if current_time - v >= self.config['throttle_period']]
        
        for key in expired_keys:
            del self.recent_alerts[key]
    
    def _save_alerts(self):
        """保存告警数据到文件"""
        try:
            if not self.alerts:
                return
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/alerts/alerts_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(self.alerts[-1000:], f, indent=2)  # 只保存最近1000条
            
            logger.info(f"已保存告警数据到 {filename}")
        except Exception as e:
            logger.error(f"保存告警数据失败: {str(e)}")
    
    def get_recent_alerts(self, limit=100):
        """获取最近的告警数据"""
        return self.alerts[-limit:] if self.alerts else []
    
    def get_alerts_by_severity(self, severity, limit=100):
        """按严重程度获取告警"""
        filtered = [a for a in self.alerts if a['severity'] == severity]
        return filtered[-limit:] if filtered else []
    
    def get_alerts_by_type(self, alert_type, limit=100):
        """按告警类型获取告警"""
        filtered = [a for a in self.alerts if a['alert_type'] == alert_type]
        return filtered[-limit:] if filtered else []
    
    def get_alerts_by_ip(self, ip_address, limit=100):
        """按IP地址获取告警"""
        filtered = [a for a in self.alerts if a['src_ip'] == ip_address or a['dst_ip'] == ip_address]
        return filtered[-limit:] if filtered else []
    
    def get_alerts_by_timeframe(self, hours=24, limit=1000):
        """获取指定时间范围内的告警"""
        start_time = datetime.now() - timedelta(hours=hours)
        start_time_str = start_time.isoformat()
        
        filtered = [a for a in self.alerts if a['timestamp'] >= start_time_str]
        return filtered[-limit:] if filtered else []
    
    def get_alert_stats(self):
        """获取告警统计数据"""
        total_alerts = len(self.alerts)
        
        # 按严重程度统计
        severity_stats = {
            '低': 0,
            '中': 0,
            '高': 0
        }
        
        # 按类型统计
        type_stats = {}
        
        # 按IP统计
        ip_stats = {}
        
        # 计算统计数据
        for alert in self.alerts:
            # 严重程度统计
            severity = alert['severity']
            if severity in severity_stats:
                severity_stats[severity] += 1
            
            # 类型统计
            alert_type = alert['alert_type']
            if alert_type not in type_stats:
                type_stats[alert_type] = 0
            type_stats[alert_type] += 1
            
            # IP统计
            src_ip = alert['src_ip']
            if src_ip not in ip_stats:
                ip_stats[src_ip] = 0
            ip_stats[src_ip] += 1
        
        # 获取前10个最活跃的IP
        top_ips = sorted(ip_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total': total_alerts,
            'severity': severity_stats,
            'types': type_stats,
            'top_ips': dict(top_ips)
        }
    
    def update_config(self, new_config):
        """更新告警配置"""
        if new_config:
            # 更新Web通知设置
            if 'web_notification' in new_config:
                self.config['web_notification'] = bool(new_config['web_notification'])
            
            # 更新邮件通知设置
            if 'email_notification' in new_config:
                self.config['email_notification'] = bool(new_config['email_notification'])
            
            # 更新邮件接收者
            if 'email_recipients' in new_config:
                if isinstance(new_config['email_recipients'], list):
                    self.config['email_recipients'] = new_config['email_recipients']
                elif isinstance(new_config['email_recipients'], str):
                    # 如果是字符串，按逗号分隔
                    recipients = [r.strip() for r in new_config['email_recipients'].split(',') if r.strip()]
                    self.config['email_recipients'] = recipients
            
            # 更新最低严重程度
            if 'min_severity' in new_config and new_config['min_severity'] in ['low', 'medium', 'high']:
                self.config['min_severity'] = new_config['min_severity']
            
            # 更新告警频率限制
            if 'alert_throttling' in new_config:
                self.config['alert_throttling'] = bool(new_config['alert_throttling'])
            
            # 更新限制周期
            if 'throttle_period' in new_config:
                try:
                    period = int(new_config['throttle_period'])
                    if period > 0:
                        self.config['throttle_period'] = period
                except (ValueError, TypeError):
                    pass
            
            logger.info("告警配置已更新")
            return True
        
        return False

# 用于测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    alert_system = AlertSystem()
    
    # 配置告警系统
    test_config = {
        'web_notification': True,
        'email_notification': False,
        'email_recipients': ['admin@example.com'],
        'min_severity': 'medium'
    }
    alert_system.update_config(test_config)
    
    # 启动告警系统
    alert_system.start_alerting()
    
    try:
        # 持续运行30秒
        time.sleep(30)
        
        # 获取统计数据
        stats = alert_system.get_alert_stats()
        print(f"告警统计: {stats}")
        
        # 获取最近告警
        recent = alert_system.get_recent_alerts(5)
        if recent:
            print("\n最近5条告警:")
            for alert in recent:
                print(f"  {alert['timestamp']} - {alert['severity']} - {alert['alert_type']}")
    finally:
        alert_system.stop_alerting()
        print("告警系统已停止")
