#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import threading
import logging
import json
from datetime import datetime
from scapy.all import sniff, IP, TCP, UDP, ICMP
from scapy.layers.http import HTTP

logger = logging.getLogger(__name__)

class TrafficDetector:
    def __init__(self, interface=None):
        self.interface = interface  # 如果为None，则会监听所有接口
        self.is_running = False
        self.capture_thread = None
        self.packet_stats = {
            'total': 0,
            'tcp': 0,
            'udp': 0,
            'icmp': 0,
            'http': 0,
            'other': 0
        }
        self.traffic_data = []
        self.suspicious_ips = set()
        self.packet_callback = None  # 可以设置回调来处理捕获的数据包
        
        # 创建保存流量数据的目录
        os.makedirs('data/traffic', exist_ok=True)
    
    def set_packet_callback(self, callback):
        """设置数据包处理回调函数"""
        self.packet_callback = callback
    
    def process_packet(self, packet):
        """处理捕获的数据包"""
        # 更新计数
        self.packet_stats['total'] += 1
        
        # 提取和分析数据包
        packet_info = self._extract_packet_info(packet)
        
        # 保存流量数据
        if packet_info:
            self.traffic_data.append(packet_info)
            
            # 定期保存流量数据，防止内存占用过多
            if len(self.traffic_data) >= 1000:
                self._save_traffic_data()
                self.traffic_data = []
        
        # 如果有设置回调，调用回调函数
        if self.packet_callback:
            self.packet_callback(packet)
    
    def _extract_packet_info(self, packet):
        """提取数据包的关键信息"""
        packet_type = 'other'
        src_ip = dst_ip = 'unknown'
        src_port = dst_port = 0
        protocol = 'unknown'
        payload_size = 0
        
        try:
            # 检查是否包含IP层
            if IP in packet:
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                
                # TCP数据包
                if TCP in packet:
                    packet_type = 'tcp'
                    self.packet_stats['tcp'] += 1
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    protocol = 'TCP'
                    
                    # 检查是否是HTTP
                    if packet.haslayer(HTTP) or dst_port == 80 or dst_port == 443:
                        packet_type = 'http'
                        self.packet_stats['http'] += 1
                        protocol = 'HTTP/HTTPS'
                
                # UDP数据包
                elif UDP in packet:
                    packet_type = 'udp'
                    self.packet_stats['udp'] += 1
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                    protocol = 'UDP'
                
                # ICMP数据包
                elif ICMP in packet:
                    packet_type = 'icmp'
                    self.packet_stats['icmp'] += 1
                    protocol = 'ICMP'
                
                # 计算载荷大小
                if hasattr(packet, 'payload'):
                    payload_size = len(packet.payload)
                
                # 返回数据包信息
                return {
                    'timestamp': datetime.now().isoformat(),
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'protocol': protocol,
                    'size': payload_size,
                    'type': packet_type
                }
            
        except Exception as e:
            logger.error(f"数据包处理错误: {str(e)}")
        
        return None
    
    def _save_traffic_data(self):
        """保存流量数据到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/traffic/traffic_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.traffic_data, f)
            logger.info(f"已保存流量数据到 {filename}，共 {len(self.traffic_data)} 条记录")
        except Exception as e:
            logger.error(f"保存流量数据失败: {str(e)}")
    
    def start_capture(self):
        """开始捕获网络流量"""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_traffic)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            logger.info(f"流量捕获已启动，监听接口: {self.interface or '所有'}")
    
    def _capture_traffic(self):
        """捕获网络流量的线程函数"""
        try:
            sniff(
                iface=self.interface,
                prn=self.process_packet,
                store=0,  # 不存储数据包，以节省内存
                stop_filter=lambda p: not self.is_running  # 当self.is_running为False时停止
            )
        except Exception as e:
            logger.error(f"流量捕获错误: {str(e)}")
            self.is_running = False
    
    def stop_capture(self):
        """停止捕获网络流量"""
        if self.is_running:
            self.is_running = False
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            self._save_traffic_data()  # 保存剩余的流量数据
            logger.info("流量捕获已停止")
    
    def get_traffic_stats(self):
        """获取流量统计信息"""
        return self.packet_stats
    
    def get_recent_traffic(self, limit=100):
        """获取最近的流量数据"""
        return self.traffic_data[-limit:] if self.traffic_data else []


# 用于测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    detector = TrafficDetector()
    detector.start_capture()
    
    try:
        # 持续运行10秒
        time.sleep(10)
    finally:
        detector.stop_capture()
        print("流量统计:", detector.get_traffic_stats())

