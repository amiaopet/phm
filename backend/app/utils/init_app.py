#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: init_app.py
# 描述: 应用程序初始化工具函数

import logging
import os
import glob
from typing import List, Dict, Any
import configparser

# 导入工具
from app.utils.scheduler_utils import init_scheduler
from app.services.scheduler import setup_bleed_monitor_job
from app.utils.config import CONFIG_DIR

# 配置日志
logger = logging.getLogger("phm_system.init_app")

def init_application():
    """初始化应用程序
    
    - 启动调度器
    - 从配置文件中恢复所有定时任务
    """
    logger.info("开始初始化应用程序...")
    
    # 确保配置目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # 初始化调度器
    init_scheduler()
    
    # 从配置文件恢复定时任务
    setup_auto_tasks_from_configs()
    
    logger.info("应用程序初始化完成")

def setup_auto_tasks_from_configs():
    """从配置文件中设置自动任务"""
    # 获取所有用户配置文件
    config_files = glob.glob(os.path.join(CONFIG_DIR, 'config_*.ini'))
    
    for config_file in config_files:
        try:
            # 从文件名提取用户名
            filename = os.path.basename(config_file)
            if filename.startswith('config_') and filename.endswith('.ini'):
                # 如果是默认配置文件，跳过
                if filename == 'config_default.ini':
                    continue
                    
                # 提取用户名
                user_part = filename[7:-4]  # 去掉'config_'前缀和'.ini'后缀
                
                # 读取配置文件
                config = configparser.ConfigParser()
                config.read(config_file, encoding='utf-8')
                
                # 检查登录信息
                if 'Login' in config and 'username' in config['Login'] and 'password' in config['Login']:
                    username = config['Login']['username']
                    password = config['Login']['password']
                    
                    if not username or not password:
                        logger.warning(f"配置文件 {filename} 中的登录信息不完整，跳过设置定时任务")
                        continue
                    
                    # 设置引气监控定时任务
                    if 'BleedSettings' in config:
                        bleed_settings = config['BleedSettings']
                        auto_enabled = bleed_settings.get('auto_enabled', 'True').lower() == 'true'
                        
                        if auto_enabled:
                            # 获取引气监控自动设置
                            hour = bleed_settings.get('auto_hour', '08')
                            minute = bleed_settings.get('auto_minute', '00')
                            cfm_threshold = bleed_settings.get('cfm_threshold', '38')
                            v2500_threshold = bleed_settings.get('v2500_threshold', '38')
                            employees = bleed_settings.get('employees', '')
                            email_recipients = bleed_settings.get('email_recipients', '')
                            
                            # 设置CFM引气监控
                            setup_bleed_monitor_job(
                                username=username,
                                password=password,
                                aircraft_type='CFM',
                                aircraft_no='ALL',
                                threshold_value=float(cfm_threshold),
                                employees=employees,
                                email_recipients=email_recipients,
                                hour=hour,
                                minute=minute
                            )
                            
                            # 设置V2500引气监控
                            setup_bleed_monitor_job(
                                username=username,
                                password=password,
                                aircraft_type='V2500',
                                aircraft_no='ALL',
                                threshold_value=float(v2500_threshold),
                                employees=employees,
                                email_recipients=email_recipients,
                                hour=hour,
                                minute=minute
                            )
                            
                            logger.info(f"已为用户 {username} 设置自动引气监控任务，执行时间: {hour}:{minute}")
                    
                    # 注意：已删除氧气监控的自动运行功能
        except Exception as e:
            logger.error(f"从配置文件 {config_file} 设置定时任务时出错: {str(e)}")
            continue 