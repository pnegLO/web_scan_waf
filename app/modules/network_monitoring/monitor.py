#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import random
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class NetworkMonitor:
    def __init__(self, socketio=None):
        self.socketio = socketio  # Socket.IO连接，用于实时发送数据
        self.is_running = False
        self.monitor_thread = None
        
        # 网络状态数据
        self.traffic_history = []
        self.protocol_stats = {
            'TCP': 0,
            'UDP': 0,
            'HTTP': 0,
            'HTTPS': 0,
            'ICMP': 0,
            'DNS': 0,
            'Other': 0
        }
        self.attack_stats = {
            'SQL注入': 0,
            'XSS攻击': 0,
            'DDoS攻击': 0,
            '端口扫描': 0,
            '暴力破解': 0,
            '异常流量': 0,
            '病毒/木马': 0
        }
        self.ip_data = defaultdict(lambda: {
            'in_traffic': 0,
            'out_traffic': 0,
            'threats': 0,
            'last_seen': datetime.now().isoformat(),
            'is_blocked': False
        })
        
        # 创建数据目录
        os.makedirs('data/monitoring', exist_ok=True)
    
    def start_monitoring(self):
        """启动网络监控"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_network)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("网络监控已启动")
    
    def stop_monitoring(self):
        """停止网络监控"""
        if self.is_running:
            self.is_running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            self._save_monitoring_data()
            logger.info("网络监控已停止")
    
    def _monitor_network(self):
        """网络监控线程函数"""
        last_emit_time = time.time()
        
        while self.is_running:
            try:
                # 模拟获取网络数据
                self._simulate_network_data()
                
                # 每秒发送一次数据到前端
                current_time = time.time()
                if current_time - last_emit_time >= 1 and self.socketio:
                    self._emit_monitoring_data()
                    last_emit_time = current_time
                
                # 每分钟保存一次监控数据
                if len(self.traffic_history) >= 60:
                    self._save_monitoring_data()
                
                time.sleep(1)  # 每秒更新一次
                
            except Exception as e:
                logger.error(f"网络监控错误: {str(e)}")
                time.sleep(5)  # 出错后等待5秒重试
    
    def _simulate_network_data(self):
        """模拟生成网络监控数据（用于演示）"""
        # 生成流量数据
        timestamp = datetime.now().isoformat()
        incoming = random.randint(100, 1500)  # 100KB - 1.5MB
        outgoing = random.randint(50, 800)    # 50KB - 800KB
        
        # 添加到历史数据中
        self.traffic_history.append({
            'timestamp': timestamp,
            'incoming': incoming,
            'outgoing': outgoing
        })
        
        # 限制历史记录大小
        if len(self.traffic_history) > 300:  # 保留最近300个数据点
            self.traffic_history = self.traffic_history[-300:]
        
        # 更新协议统计
        protocols = list(self.protocol_stats.keys())
        for _ in range(3):  # 随机更新几个协议的计数
            protocol = random.choice(protocols)
            self.protocol_stats[protocol] += random.randint(1, 10)
        
        # 更新攻击类型统计
        if random.random() < 0.3:  # 30%概率生成攻击数据
            attack_types = list(self.attack_stats.keys())
            attack_type = random.choice(attack_types)
            self.attack_stats[attack_type] += 1
            
            # 生成告警数据
            alert_data = {
                'timestamp': timestamp,
                'alert_id': f"ALERT-{int(time.time())}-{random.randint(1000, 9999)}",
                'alert_type': attack_type,
                'severity': random.choice(['低', '中', '高']),
                'src_ip': f"192.168.1.{random.randint(2, 254)}",
                'dst_ip': f"10.0.0.{random.randint(2, 254)}",
                'port': random.randint(1, 65535),
                'protocol': random.choice(['TCP', 'UDP', 'HTTP']),
                'details': f"检测到{attack_type}攻击尝试"
            }
            
            # 更新IP数据
            src_ip = alert_data['src_ip']
            self.ip_data[src_ip]['threats'] += 1
            self.ip_data[src_ip]['last_seen'] = timestamp
            
            # 发送告警数据到前端
            if self.socketio:
                self.socketio.emit('new_alert', alert_data)
        
        # 随机更新一些IP统计数据
        for _ in range(5):
            ip = f"192.168.1.{random.randint(2, 254)}"
            self.ip_data[ip]['in_traffic'] += random.randint(1, 100)
            self.ip_data[ip]['out_traffic'] += random.randint(1, 50)
            self.ip_data[ip]['last_seen'] = timestamp
    
    def _emit_monitoring_data(self):
        """向前端发送监控数据"""
        try:
            if not self.socketio:
                return
            
            # 获取最新流量数据点
            current_traffic = self.traffic_history[-1] if self.traffic_history else {
                'timestamp': datetime.now().isoformat(),
                'incoming': 0,
                'outgoing': 0
            }
            
            # 计算总流量统计
            total_in = sum(point['incoming'] for point in self.traffic_history[-60:] if point)
            total_out = sum(point['outgoing'] for point in self.traffic_history[-60:] if point)
            
            # 获取TOP 5 IP列表
            top_ips = sorted(
                self.ip_data.items(), 
                key=lambda x: x[1]['in_traffic'] + x[1]['out_traffic'], 
                reverse=True
            )[:5]
            
            # 准备网络状态数据
            network_stats = {
                'timestamp': current_traffic['timestamp'],
                'traffic_in': current_traffic['incoming'] * 1024,  # 转换为字节
                'traffic_out': current_traffic['outgoing'] * 1024,  # 转换为字节
                'connections': random.randint(10, 100),
                'packets_processed': random.randint(100, 1000),
                'threats_detected': sum(self.attack_stats.values()),
                'ips_blocked': sum(1 for ip_data in self.ip_data.values() if ip_data['is_blocked']),
                'protocol_stats': self.protocol_stats,
                'attack_stats': self.attack_stats,
                'ip_data': dict(top_ips)
            }
            
            # 发送网络统计数据
            self.socketio.emit('network_stats', network_stats)
            
            # 发送流量历史数据
            traffic_data = {
                'history': self.traffic_history[-60:],  # 最近60个数据点
                'protocols': self.protocol_stats
            }
            self.socketio.emit('traffic_update', traffic_data)
            
            # 保存监控数据
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/monitoring/monitoring_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(network_stats, f)
            logger.info(f"已保存监控数据到 {filename}")
            
        except Exception as e:
            logger.error(f"发送监控数据错误: {str(e)}")
    
    def _save_monitoring_data(self):
        """保存监控数据到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/monitoring/monitoring_{timestamp}.json'
            
            # 准备保存的数据
            data_to_save = {
                'traffic_history': self.traffic_history,
                'protocol_stats': self.protocol_stats,
                'attack_stats': self.attack_stats,
                'ip_data': {k: v for k, v in self.ip_data.items()}
            }
            
            # 写入文件
            with open(filename, 'w') as f:
                json.dump(data_to_save, f)
            
            logger.info(f"已保存监控数据到 {filename}")
        except Exception as e:
            logger.error(f"保存监控数据失败: {str(e)}")
    
    def get_network_stats(self):
        """获取网络统计信息"""
        return {
            'traffic': {
                'history': self.traffic_history[-60:],  # 最近60个数据点
                'total_in': sum(point['incoming'] for point in self.traffic_history[-60:]),
                'total_out': sum(point['outgoing'] for point in self.traffic_history[-60:])
            },
            'protocols': self.protocol_stats,
            'attacks': self.attack_stats
        }
    
    def get_ip_data(self, limit=20):
        """获取IP数据列表"""
        sorted_ips = sorted(
            self.ip_data.items(),
            key=lambda x: x[1]['in_traffic'] + x[1]['out_traffic'],
            reverse=True
        )[:limit]
        
        return {ip: data for ip, data in sorted_ips}
    
    def block_ip(self, ip_address):
        """阻止特定IP地址"""
        if ip_address in self.ip_data:
            self.ip_data[ip_address]['is_blocked'] = True
            logger.info(f"已阻止IP地址: {ip_address}")
            return True
        return False
    
    def unblock_ip(self, ip_address):
        """解除对特定IP的阻止"""
        if ip_address in self.ip_data:
            self.ip_data[ip_address]['is_blocked'] = False
            logger.info(f"已解除对IP地址的阻止: {ip_address}")
            return True
        return False
    
    def get_traffic_by_timeframe(self, timeframe='hour'):
        """按不同时间范围获取流量数据"""
        now = datetime.now()
        if timeframe == 'hour':
            # 过去一小时的数据（每分钟一个数据点）
            start_time = now - timedelta(hours=1)
            return [p for p in self.traffic_history if datetime.fromisoformat(p['timestamp']) >= start_time]
        elif timeframe == 'day':
            # 过去24小时的数据（每小时一个数据点）
            start_time = now - timedelta(days=1)
            return self._aggregate_traffic_data(
                [p for p in self.traffic_history if datetime.fromisoformat(p['timestamp']) >= start_time],
                'hour'
            )
        elif timeframe == 'week':
            # 过去一周的数据（每天一个数据点）
            start_time = now - timedelta(days=7)
            return self._aggregate_traffic_data(
                [p for p in self.traffic_history if datetime.fromisoformat(p['timestamp']) >= start_time],
                'day'
            )
        else:
            return self.traffic_history[-60:]  # 默认返回最近60个数据点
    
    def _aggregate_traffic_data(self, data, interval):
        """聚合流量数据，按指定间隔（小时/天）"""
        if not data:
            return []
        
        aggregated = {}
        for point in data:
            timestamp = datetime.fromisoformat(point['timestamp'])
            if interval == 'hour':
                key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
            elif interval == 'day':
                key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            else:
                key = point['timestamp']
            
            if key not in aggregated:
                aggregated[key] = {'timestamp': key, 'incoming': 0, 'outgoing': 0, 'count': 0}
            
            aggregated[key]['incoming'] += point['incoming']
            aggregated[key]['outgoing'] += point['outgoing']
            aggregated[key]['count'] += 1
        
        # 计算平均值
        for key, value in aggregated.items():
            if value['count'] > 0:
                value['incoming'] = value['incoming'] // value['count']
                value['outgoing'] = value['outgoing'] // value['count']
            del value['count']
        
        # 按时间排序
        return sorted(aggregated.values(), key=lambda x: x['timestamp'])

# 用于测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = NetworkMonitor()
    monitor.start_monitoring()
    
    try:
        # 持续运行30秒
        time.sleep(30)
    finally:
        monitor.stop_monitoring()
        print("网络监控已停止")
