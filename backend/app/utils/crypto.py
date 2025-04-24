#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: crypto.py
# 描述: 密码加密和解密工具

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

# 配置日志
logger = logging.getLogger("phm_system.crypto")

# 系统级别的盐值，用于增强安全性
# 这个值最好存储在环境变量中，这里简化处理
SALT = b'PHM_AIRLINE_SYSTEM_SALT'

def get_key(username: str) -> bytes:
    """从用户名生成加密密钥
    
    Args:
        username: 用户名
        
    Returns:
        生成的加密密钥
    """
    # 结合用户名和系统盐值生成密钥
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(username.encode()))
    return key

def encrypt_password(username: str, password: str) -> str:
    """加密密码
    
    Args:
        username: 用户名，用于生成密钥
        password: 要加密的明文密码
        
    Returns:
        加密后的密码（Base64编码的字符串）
    """
    try:
        key = get_key(username)
        f = Fernet(key)
        encrypted_data = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"加密密码失败: {str(e)}")
        # 加密失败时返回空字符串
        return ""

def decrypt_password(username: str, encrypted_password: str) -> str:
    """解密密码
    
    Args:
        username: 用户名，用于生成密钥
        encrypted_password: 已加密的密码（Base64编码的字符串）
        
    Returns:
        解密后的明文密码
    """
    try:
        if not encrypted_password:
            return ""
            
        key = get_key(username)
        f = Fernet(key)
        # 先解Base64，再用Fernet解密
        decoded_data = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted_data = f.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"解密密码失败: {str(e)}")
        # 解密失败时返回空字符串
        return "" 