#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import random
import logging
import threading
import subprocess
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class IntrusionPrevention:
    def __init__(self, mode='auto'):
        self.is_running = False
        self.prevention_thread = None
        self.mode = mode  # 'monitor', 'auto', 'strict'
        
        # 威胁数据
        self.threats = []
        self.blocked_ips = set()
        self.ip_threats = defaultdict(int)
        self.block_threshold = 3  # 默认阻止阈值
        self.block_duration = 60  # 默认阻止时间（分钟）
        
        # 创建数据目录
        os.makedirs('data/threats', exist_ok=True)
    
    def start_prevention(self):
        """启动入侵防御"""
        if not self.is_running:
            self.is_running = True
            self.prevention_thread = threading.Thread(target=self._prevention_worker)
            self.prevention_thread.daemon = True
            self.prevention_thread.start()
            logger.info(f"入侵防御已启动，模式: {self.mode}")
    
    def stop_prevention(self):
        """停止入侵防御"""
        if self.is_running:
            self.is_running = False
            if self.prevention_thread:
                self.prevention_thread.join(timeout=2)
            self._save_threat_data()
            logger.info("入侵防御已停止")
    
    def _prevention_worker(self):
        """防御工作线程"""
        last_cleanup_time = time.time()
        
        while self.is_running:
            try:
                # 模拟检测威胁
                self._simulate_threat_detection()
                
                # 每小时清理一次过期的IP阻止
                current_time = time.time()
                if current_time - last_cleanup_time >= 3600:  # 3600秒 = 1小时
                    self._cleanup_blocks()
                    last_cleanup_time = current_time
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"入侵防御错误: {str(e)}")
                time.sleep(10)  # 出错后等待10秒重试
    
    def _simulate_threat_detection(self):
        """模拟威胁检测（用于演示）"""
        # 30%的概率生成威胁
        if random.random() < 0.3:
            threat_types = [
                'SQL注入', 'XSS攻击', 'DDoS攻击', '端口扫描', 
                '暴力破解', '异常流量', '病毒/木马'
            ]
            
            threat_type = random.choice(threat_types)
            severity = random.choice(['低', '中', '高'])
            src_ip = f"192.168.1.{random.randint(2, 254)}"
            dst_ip = f"10.0.0.{random.randint(2, 254)}"
            
            # 创建威胁数据
            threat = {
                'threat_id': f"THREAT-{int(time.time())}-{random.randint(1000, 9999)}",
                'timestamp': datetime.now().isoformat(),
                'threat_type': threat_type,
                'severity': severity,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'port': random.randint(1, 65535),
                'protocol': random.choice(['TCP', 'UDP', 'HTTP']),
                'details': f"检测到{threat_type}攻击尝试",
                'blocked': False,
                'action_taken': '监控'
            }
            
            # 添加到威胁列表
            self.threats.append(threat)
            
            # 限制威胁列表大小
            if len(self.threats) > 1000:
                self.threats = self.threats[-1000:]
            
            # 增加IP威胁计数
            self.ip_threats[src_ip] += 1
            
            # 根据防御模式执行操作
            if self.mode != 'monitor':
                # 自动模式：超过阈值自动阻止
                if self.mode == 'auto' and self.ip_threats[src_ip] >= self.block_threshold:
                    self.block_ip(src_ip, threat['threat_id'])
                    threat['blocked'] = True
                    threat['action_taken'] = '已阻止'
                
                # 严格模式：高危威胁直接阻止
                elif self.mode == 'strict' and severity == '高':
                    self.block_ip(src_ip, threat['threat_id'])
                    threat['blocked'] = True
                    threat['action_taken'] = '已阻止'
            
            logger.info(f"检测到威胁: {threat_type}, 来源: {src_ip}, 严重性: {severity}, 操作: {threat['action_taken']}")
    
    def block_ip(self, ip_address, threat_id=None):
        """阻止指定的IP地址"""
        if ip_address in self.blocked_ips:
            return False
        
        try:
            # 记录阻止操作
            self.blocked_ips.add(ip_address)
            
            # 实际环境中，这里应该调用系统防火墙命令阻止IP
            if os.name == 'posix':  # Linux/Mac系统
                # 这里仅为示例，实际使用时应确保命令安全
                # subprocess.run(['iptables', '-A', 'INPUT', '-s', ip_address, '-j', 'DROP'])
                pass
            elif os.name == 'nt':  # Windows系统
                # subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', 
                #                 'name=IDS_Block', 'dir=in', 'action=block', f'remoteip={ip_address}'])
                pass
            
            logger.info(f"已阻止IP地址: {ip_address}")
            
            # 记录阻止事件
            block_event = {
                'ip': ip_address,
                'timestamp': datetime.now().isoformat(),
                'threat_id': threat_id,
                'duration': self.block_duration,
                'expiry': datetime.now().timestamp() + self.block_duration * 60
            }
            
            # 保存阻止事件
            try:
                blocks_file = 'data/threats/blocked_ips.json'
                blocks = []
                
                if os.path.exists(blocks_file):
                    with open(blocks_file, 'r') as f:
                        try:
                            blocks = json.load(f)
                        except json.JSONDecodeError:
                            blocks = []
                
                blocks.append(block_event)
                
                with open(blocks_file, 'w') as f:
                    json.dump(blocks, f, indent=2)
            
            except Exception as e:
                logger.error(f"保存IP阻止记录失败: {str(e)}")
            
            return True
        
        except Exception as e:
            logger.error(f"阻止IP地址失败: {str(e)}")
            return False
    
    def unblock_ip(self, ip_address):
        """解除对IP地址的阻止"""
        if ip_address not in self.blocked_ips:
            return False
        
        try:
            # 从阻止集合中移除
            self.blocked_ips.remove(ip_address)
            
            # 实际环境中，这里应该调用系统防火墙命令解除阻止
            if os.name == 'posix':  # Linux/Mac系统
                # subprocess.run(['iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP'])
                pass
            elif os.name == 'nt':  # Windows系统
                # subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule', 
                #                 'name=IDS_Block', f'remoteip={ip_address}'])
                pass
            
            logger.info(f"已解除对IP地址的阻止: {ip_address}")
            return True
        
        except Exception as e:
            logger.error(f"解除IP地址阻止失败: {str(e)}")
            return False
    
    def _cleanup_blocks(self):
        """清理过期的IP阻止"""
        current_time = time.time()
        blocks_file = 'data/threats/blocked_ips.json'
        
        try:
            if os.path.exists(blocks_file):
                with open(blocks_file, 'r') as f:
                    try:
                        blocks = json.load(f)
                    except json.JSONDecodeError:
                        blocks = []
                
                # 找出过期的阻止
                expired_blocks = [b for b in blocks if b.get('expiry', 0) <= current_time]
                active_blocks = [b for b in blocks if b.get('expiry', 0) > current_time]
                
                # 解除过期的阻止
                for block in expired_blocks:
                    if block['ip'] in self.blocked_ips:
                        self.unblock_ip(block['ip'])
                
                # 更新阻止文件
                with open(blocks_file, 'w') as f:
                    json.dump(active_blocks, f, indent=2)
                
                logger.info(f"已清理 {len(expired_blocks)} 个过期的IP阻止")
        
        except Exception as e:
            logger.error(f"清理过期IP阻止失败: {str(e)}")
    
    def _save_threat_data(self):
        """保存威胁数据到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/threats/threats_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(self.threats, f, indent=2)
            
            logger.info(f"已保存威胁数据到 {filename}，共 {len(self.threats)} 条记录")
        except Exception as e:
            logger.error(f"保存威胁数据失败: {str(e)}")
    
    def set_mode(self, mode):
        """设置防御模式"""
        if mode in ['monitor', 'auto', 'strict']:
            self.mode = mode
            logger.info(f"防御模式已设置为: {mode}")
            return True
        return False
    
    def set_block_threshold(self, threshold):
        """设置阻止阈值"""
        try:
            threshold = int(threshold)
            if threshold > 0:
                self.block_threshold = threshold
                logger.info(f"阻止阈值已设置为: {threshold}")
                return True
        except (ValueError, TypeError):
            pass
        return False
    
    def set_block_duration(self, duration):
        """设置阻止持续时间（分钟）"""
        try:
            duration = int(duration)
            if duration >= 0:
                self.block_duration = duration
                logger.info(f"阻止持续时间已设置为: {duration}分钟")
                return True
        except (ValueError, TypeError):
            pass
        return False
    
    def get_recent_threats(self, limit=100):
        """获取最近的威胁数据"""
        return self.threats[-limit:] if self.threats else []
    
    def get_blocked_ips(self):
        """获取当前被阻止的IP列表"""
        return list(self.blocked_ips)
    
    def get_ip_threat_count(self, ip_address):
        """获取特定IP的威胁计数"""
        return self.ip_threats.get(ip_address, 0)

# 用于测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prevention = IntrusionPrevention(mode='auto')
    prevention.start_prevention()
    
    try:
        # 持续运行30秒
        time.sleep(30)
    finally:
        prevention.stop_prevention()
        print("入侵防御已停止")
        print(f"检测到的威胁: {len(prevention.threats)}")
        print(f"阻止的IP数量: {len(prevention.blocked_ips)}")
