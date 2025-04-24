#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: config.py
# 描述: 全局配置

import os
import configparser
import logging
from typing import Optional, Dict, Any, List, Tuple

# 导入加密/解密功能
from app.utils.crypto import encrypt_password, decrypt_password

logger = logging.getLogger("phm_system.config")

# 基础配置
BASE_URL = 'http://10.14.122.12:7080'
LOGIN_URL = f'{BASE_URL}/api/v1/security/loginSC'
MSG_API_URL = f'{BASE_URL}/api/v1/plugins/TIANPAN_PX_SENDMSG'
COOKIE_FILE = 'cookies.pkl'
CONFIG_DIR = 'configs'  # 配置文件目录

# 确保配置目录存在
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# 飞机列表
CFM_AIRCRAFT = [
    'B-1645', 'B-1646', 'B-1647', 'B-1681', 'B-1808', 'B-1857', 'B-1870',
    'B-1871', 'B-1872', 'B-304G', 'B-304H', 'B-6572', 'B-6640', 'B-6717',
    'B-6735', 'B-6736', 'B-6787', 'B-6788', 'B-6860', 'B-6861', 'B-6901',
    'B-6921', 'B-6922', 'B-6948', 'B-6949', 'B-6962', 'B-6963', 'B-6965',
    'B-6966', 'B-8035', 'B-8036', 'B-8068', 'B-8235', 'B-8236', 'B-8317',
    'B-8408', 'B-8536', 'B-8538', 'B-9957', 'B-9978'
]

V2500_AIRCRAFT = [
    'B-1001', 'B-1002', 'B-1003', 'B-1005', 'B-1006', 'B-8315', 'B-8407',
    'B-8457', 'B-8458', 'B-8459', 'B-8537', 'B-8539', 'B-8540', 'B-8587',
    'B-8955', 'B-8956', 'B-8957'
]

PW_AIRCRAFT = [
    'B-30C9', 'B-30CT', 'B-30EP', 'B-30EQ', 'B-30FC', 'B-30FQ', 'B-320Z', 'B-321A', 
    'B-321C', 'B-322E', 'B-323D', 'B-323R', 'B-324C', 'B-324D', 'B-324U', 'B-324V', 
    'B-325L', 'B-326H', 'B-326J', 'B-327D', 'B-327W', 'B-32CJ', 'B-32D9', 'B-32DF', 
    'B-32EA', 'B-32EC', 'B-32EG', 'B-32EH', 'B-32EJ', 'B-32EY', 'B-32HD', 'B-32HT', 
    'B-32HU', 'B-32JE', 'B-32JP', 'B-32JU'
]

# 合并所有飞机列表
ALL_AIRCRAFT = sorted(CFM_AIRCRAFT + V2500_AIRCRAFT + PW_AIRCRAFT)

class Config:
    """配置管理类，处理应用程序配置的保存和加载，支持多用户配置"""
    def __init__(self, username: Optional[str] = None):
        """初始化配置对象，支持指定用户名
        
        参数:
            username: 用户名，如果提供则使用用户特定的配置文件
        """
        self.username = username
        self.config = configparser.ConfigParser()
        self.config_file = self._get_config_file()
        self.load_config()
        
    def _get_config_file(self) -> str:
        """获取配置文件路径，根据是否有用户名返回不同的配置文件"""
        if self.username:
            # 用户名中可能包含特殊字符，将其转换为安全的文件名
            safe_username = ''.join(c if c.isalnum() else '_' for c in self.username)
            return os.path.join(CONFIG_DIR, f'config_{safe_username}.ini')
        else:
            return os.path.join(CONFIG_DIR, 'config_default.ini')
    
    def load_config(self) -> None:
        """加载配置文件，如果不存在则创建默认配置"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
            # 迁移旧配置到新配置结构
            self._migrate_config()
        else:
            self.config['Login'] = {'username': self.username or '', 'password': ''}
            self.config['BleedSettings'] = {
                'cfm_threshold': '38', 
                'v2500_threshold': '38',
                'employees': 'HO00-0012625',
                'email_recipients': '',
                'auto_enabled': 'True',
                'auto_hour': '08',
                'auto_minute': '00',
                'auto_date_range': '三个月',
                'last_run_date': ''
            }
            self.config['OxygenMonitor'] = {
                'last_aircraft': '',
                'days_range': '3',
                'psi1_threshold': '50',
                'psi2_threshold': '50',
                'email_recipients': '',
                'auto_enabled': 'True',
                'auto_hour': '08',
                'auto_minute': '00',
                'auto_date_range': '最近三天',
                'last_run_date': ''
            }
            self.save_config()
    
    def _migrate_config(self) -> None:
        """将旧配置结构迁移到新配置结构"""
        # 1. 从Email迁移到各模块的email_recipients
        if 'Email' in self.config and 'recipients' in self.config['Email']:
            email = self.config['Email']['recipients']
            if 'BleedSettings' in self.config and not self.config['BleedSettings'].get('email_recipients'):
                self.config['BleedSettings']['email_recipients'] = email
            if 'OxygenMonitor' in self.config and not self.config['OxygenMonitor'].get('email_recipients'):
                self.config['OxygenMonitor']['email_recipients'] = email
        
        # 2. 从AutoRun迁移到各模块的auto_*
        if 'AutoRun' in self.config:
            enabled = self.config['AutoRun'].get('enabled', 'True')
            hour = self.config['AutoRun'].get('hour', '08')
            minute = self.config['AutoRun'].get('minute', '00')
            
            # 迁移到BleedSettings
            if 'BleedSettings' in self.config:
                if not self.config['BleedSettings'].get('auto_enabled'):
                    self.config['BleedSettings']['auto_enabled'] = enabled
                if not self.config['BleedSettings'].get('auto_hour'):
                    self.config['BleedSettings']['auto_hour'] = hour
                if not self.config['BleedSettings'].get('auto_minute'):
                    self.config['BleedSettings']['auto_minute'] = minute
                if not self.config['BleedSettings'].get('auto_date_range'):
                    self.config['BleedSettings']['auto_date_range'] = '三个月'
            
            # 迁移到OxygenMonitor
            if 'OxygenMonitor' in self.config:
                if not self.config['OxygenMonitor'].get('auto_enabled'):
                    self.config['OxygenMonitor']['auto_enabled'] = enabled
                if not self.config['OxygenMonitor'].get('auto_hour'):
                    self.config['OxygenMonitor']['auto_hour'] = hour
                if not self.config['OxygenMonitor'].get('auto_minute'):
                    self.config['OxygenMonitor']['auto_minute'] = minute
                if not self.config['OxygenMonitor'].get('auto_date_range'):
                    self.config['OxygenMonitor']['auto_date_range'] = '最近三天'
        
        # 3. 迁移明文密码到加密密码，仅在有用户名的情况下
        if 'Login' in self.config and self.username:
            stored_password = self.config['Login'].get('password', '')
            if stored_password and not stored_password.startswith('enc:'):
                # 如果密码不是以'enc:'开头（即未加密），则进行加密
                encrypted_pwd = encrypt_password(self.username, stored_password)
                if encrypted_pwd:
                    self.config['Login']['password'] = f"enc:{encrypted_pwd}"
                    logger.info(f"用户 {self.username} 的密码已加密")
                    
        # 保存配置
        self.save_config()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_login_info(self) -> Tuple[str, str]:
        """获取登录信息
        
        Returns:
            包含用户名和密码的元组
        """
        if 'Login' in self.config:
            username = self.config['Login'].get('username', '')
            password = self.config['Login'].get('password', '')
            
            # 如果密码是加密的，解密并返回
            if password.startswith('enc:') and self.username:
                encrypted_pwd = password[4:]  # 去掉'enc:'前缀
                password = decrypt_password(self.username, encrypted_pwd)
                logger.debug(f"用户 {self.username} 的密码已解密")
            
            return username, password
        return '', ''
    
    def set_login_info(self, username: str, password: str) -> None:
        """设置登录信息，密码会自动加密
        
        Args:
            username: 用户名
            password: 密码（明文）
        """
        if 'Login' not in self.config:
            self.config['Login'] = {}
        
        self.config['Login']['username'] = username
        
        # 加密存储密码
        if password and self.username:
            encrypted_pwd = encrypt_password(self.username, password)
            if encrypted_pwd:
                self.config['Login']['password'] = f"enc:{encrypted_pwd}"
                logger.info(f"用户 {username} 的密码已加密保存")
            else:
                # 加密失败时，保存空密码
                self.config['Login']['password'] = ""
                logger.error(f"用户 {username} 的密码加密失败")
        else:
            self.config['Login']['password'] = password
        
        self.save_config()
    
    def get_cfm_threshold(self) -> str:
        """获取CFM引气压力阈值"""
        if 'BleedSettings' in self.config:
            return self.config['BleedSettings'].get('cfm_threshold', '38')
        return '38'
    
    def get_v2500_threshold(self) -> str:
        """获取V2500引气压力阈值"""
        if 'BleedSettings' in self.config:
            return self.config['BleedSettings'].get('v2500_threshold', '38')
        return '38'
    
    def get_employees(self) -> str:
        """获取接收员工列表"""
        if 'BleedSettings' in self.config:
            return self.config['BleedSettings'].get('employees', 'HO00-0012625')
        return 'HO00-0012625'
    
    def set_bleed_settings(self, cfm_threshold: str, v2500_threshold: str, employees: str) -> None:
        """设置引气监控参数"""
        if 'BleedSettings' not in self.config:
            self.config['BleedSettings'] = {}
        self.config['BleedSettings']['cfm_threshold'] = cfm_threshold
        self.config['BleedSettings']['v2500_threshold'] = v2500_threshold
        self.config['BleedSettings']['employees'] = employees
        self.save_config()
    
    def get_bleed_email_recipients(self) -> str:
        """获取引气监控的接收邮箱设置"""
        if 'BleedSettings' in self.config:
            return self.config['BleedSettings'].get('email_recipients', '')
        return ''
    
    def set_bleed_email_recipients(self, recipients: str) -> None:
        """设置引气监控的接收邮箱"""
        if 'BleedSettings' not in self.config:
            self.config['BleedSettings'] = {}
        self.config['BleedSettings']['email_recipients'] = recipients
        self.save_config()
    
    def get_bleed_auto_settings(self) -> Tuple[bool, str, str, str]:
        """获取引气监控的自动运行设置"""
        if 'BleedSettings' in self.config:
            enabled = self.config['BleedSettings'].get('auto_enabled', 'True').lower() == 'true'
            hour = self.config['BleedSettings'].get('auto_hour', '08')
            minute = self.config['BleedSettings'].get('auto_minute', '00')
            date_range = self.config['BleedSettings'].get('auto_date_range', '三个月')
            return enabled, hour, minute, date_range
        return True, '08', '00', '三个月'
    
    def set_bleed_auto_settings(self, enabled: bool, hour: str, minute: str, date_range: str = '三个月') -> None:
        """设置引气监控的自动运行参数"""
        if 'BleedSettings' not in self.config:
            self.config['BleedSettings'] = {}
        self.config['BleedSettings']['auto_enabled'] = str(enabled)
        self.config['BleedSettings']['auto_hour'] = hour
        self.config['BleedSettings']['auto_minute'] = minute
        self.config['BleedSettings']['auto_date_range'] = date_range
        self.save_config()
    
    def update_bleed_last_run_date(self, date_str: str) -> None:
        """更新引气监控上次运行日期"""
        if 'BleedSettings' not in self.config:
            self.config['BleedSettings'] = {}
        self.config['BleedSettings']['last_run_date'] = date_str
        self.save_config()
    
    def get_last_oxygen_aircraft(self) -> str:
        """获取上次氧气监控的飞机号"""
        if 'OxygenMonitor' in self.config:
            return self.config['OxygenMonitor'].get('last_aircraft', '')
        return ''
    
    def set_last_oxygen_aircraft(self, aircraft: str) -> None:
        """设置上次氧气监控的飞机号"""
        if 'OxygenMonitor' not in self.config:
            self.config['OxygenMonitor'] = {}
        self.config['OxygenMonitor']['last_aircraft'] = aircraft
        self.save_config()
        
    def get_oxygen_days_range(self) -> str:
        """获取氧气监控的天数范围"""
        if 'OxygenMonitor' in self.config:
            return self.config['OxygenMonitor'].get('days_range', '3')
        return '3'
    
    def set_oxygen_days_range(self, days: str) -> None:
        """设置氧气监控的天数范围"""
        if 'OxygenMonitor' not in self.config:
            self.config['OxygenMonitor'] = {}
        self.config['OxygenMonitor']['days_range'] = days
        self.save_config()
    
    def get_oxygen_thresholds(self) -> Tuple[str, str]:
        """获取氧气阈值设置"""
        if 'OxygenMonitor' in self.config:
            psi1 = self.config['OxygenMonitor'].get('psi1_threshold', '50')
            psi2 = self.config['OxygenMonitor'].get('psi2_threshold', '50')
            return psi1, psi2
        return '50', '50'
    
    def set_oxygen_thresholds(self, psi1_threshold: str, psi2_threshold: str) -> None:
        """设置氧气阈值"""
        if 'OxygenMonitor' not in self.config:
            self.config['OxygenMonitor'] = {}
        self.config['OxygenMonitor']['psi1_threshold'] = psi1_threshold
        self.config['OxygenMonitor']['psi2_threshold'] = psi2_threshold
        self.save_config()
        
    def get_oxygen_email_recipients(self) -> str:
        """获取氧气监控的接收邮箱设置"""
        if 'OxygenMonitor' in self.config:
            return self.config['OxygenMonitor'].get('email_recipients', '')
        return ''
        
    def set_oxygen_email_recipients(self, recipients: str) -> None:
        """设置氧气监控的接收邮箱"""
        if 'OxygenMonitor' not in self.config:
            self.config['OxygenMonitor'] = {}
        self.config['OxygenMonitor']['email_recipients'] = recipients
        self.save_config()
    
    def get_oxygen_employees(self) -> str:
        """获取氧气监控的接收员工号"""
        if 'OxygenMonitor' in self.config:
            return self.config['OxygenMonitor'].get('employees', '')
        return ''
        
    def set_oxygen_employees(self, employees: str) -> None:
        """设置氧气监控的接收员工号"""
        if 'OxygenMonitor' not in self.config:
            self.config['OxygenMonitor'] = {}
        self.config['OxygenMonitor']['employees'] = employees
        self.save_config()

    def get_email_recipients(self) -> str:
        """获取通用接收邮件的邮箱地址列表（兼容旧版本）"""
        # 先尝试从 BleedSettings 和 OxygenMonitor 获取
        bleed_recipients = self.get_bleed_email_recipients()
        oxygen_recipients = self.get_oxygen_email_recipients()
        
        if bleed_recipients:
            return bleed_recipients
        elif oxygen_recipients:
            return oxygen_recipients
        
        # 如果都没有，再尝试旧版的 Email 字段
        if 'Email' in self.config:
            return self.config['Email'].get('recipients', '')
        return ''
    
    def set_email_recipients(self, recipients: str) -> None:
        """设置通用接收邮件的邮箱地址列表（兼容旧版本）"""
        # 设置到两个监控模块
        self.set_bleed_email_recipients(recipients)
        self.set_oxygen_email_recipients(recipients)
        
        # 为兼容旧版本，也保存到 Email 字段
        if 'Email' not in self.config:
            self.config['Email'] = {}
        self.config['Email']['recipients'] = recipients
        self.save_config()