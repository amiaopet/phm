#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: migrate_passwords.py
# 描述: 用于迁移现有配置中的明文密码到加密密码

import os
import sys
import configparser
import logging
import glob
from app.utils.crypto import encrypt_password

# 设置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("password_migration")

# 配置文件目录
CONFIG_DIR = 'configs'

def migrate_passwords():
    """迁移所有配置文件中的明文密码到加密密码"""
    # 获取所有配置文件
    config_files = glob.glob(os.path.join(CONFIG_DIR, 'config_*.ini'))
    
    if not config_files:
        logger.warning(f"未找到配置文件，目录: {CONFIG_DIR}")
        return
    
    logger.info(f"发现 {len(config_files)} 个配置文件")
    
    migrated_count = 0
    for config_file in config_files:
        try:
            # 从文件名提取用户名
            filename = os.path.basename(config_file)
            if not filename.startswith('config_') or not filename.endswith('.ini'):
                continue
                
            # 解析用户名
            username = filename[7:-4]  # 去掉'config_'前缀和'.ini'后缀
            
            # 读取配置文件
            config = configparser.ConfigParser()
            config.read(config_file, encoding='utf-8')
            
            # 检查并加密密码
            if 'Login' in config and 'password' in config['Login']:
                password = config['Login']['password']
                
                # 检查密码是否已经加密
                if password and not password.startswith('enc:'):
                    # 加密密码
                    encrypted_pwd = encrypt_password(username, password)
                    if encrypted_pwd:
                        config['Login']['password'] = f"enc:{encrypted_pwd}"
                        
                        # 保存配置
                        with open(config_file, 'w', encoding='utf-8') as f:
                            config.write(f)
                            
                        logger.info(f"已加密用户 {username} 的密码")
                        migrated_count += 1
                    else:
                        logger.error(f"加密用户 {username} 的密码失败")
                else:
                    logger.info(f"用户 {username} 的密码已加密或为空，跳过")
            else:
                logger.warning(f"用户 {username} 的配置文件中未找到登录信息")
        
        except Exception as e:
            logger.error(f"处理配置文件 {config_file} 时出错: {str(e)}")
    
    logger.info(f"密码迁移完成，共迁移了 {migrated_count} 个用户的密码")

if __name__ == "__main__":
    logger.info("开始迁移密码...")
    migrate_passwords()
    logger.info("密码迁移完成") 