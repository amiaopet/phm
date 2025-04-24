#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: auto_login.py
# 描述: 自动登录工具函数

import logging
import httpx
from typing import Dict, Any, Tuple, Optional

# 导入配置
from app.utils.config import BASE_URL, Config

# 配置日志
logger = logging.getLogger("phm_system.auto_login")
logger = logging.getLogger("phm_system.cookie_validator")

async def auto_login(username: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
    """根据用户名自动登录并获取cookie
    
    参数:
        username: 用户名
    
    返回值:
        元组 (success, cookies, message)
        success: 是否成功登录
        cookies: 如果成功，返回cookie字典；否则为None
        message: 状态消息
    """
    try:
        # 从配置文件获取登录信息
        config = Config(username)
        username, password = config.get_login_info()
        
        if not username or not password:
            return False, None, "配置文件中未找到有效的登录信息"
        
        # 构建登录请求
        login_url = f'{BASE_URL}/api/v1/security/loginSC'
        login_data = {
            'username': username,
            'userPassword': password
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{BASE_URL}/views/login.shtml'
        }
        
        # 发送登录请求
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                login_url,
                data=login_data,
                headers=headers
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('code') == 0 or 'success' in response.text.lower():
                        # 提取cookies
                        cookies = {cookie.name: cookie.value for cookie in response.cookies.jar}
                        logger.info(f"用户 {username} 自动登录成功，已获取有效Cookie")
                        return True, cookies, "成功获取登录凭据"
                    else:
                        error_msg = f"自动登录失败，服务器返回: {result.get('msg', '未知错误')}"
                        logger.error(error_msg)
                        return False, None, error_msg
                except Exception as e:
                    # 尝试直接获取cookies
                    cookies = {cookie.name: cookie.value for cookie in response.cookies.jar}
                    if cookies:
                        logger.info(f"用户 {username} 自动登录成功，已获取有效Cookie")
                        return True, cookies, "成功获取登录凭据"
                    
                    error_msg = f"解析登录响应失败: {str(e)}"
                    logger.error(error_msg)
                    return False, None, error_msg
            else:
                error_msg = f"登录请求失败，状态码: {response.status_code}"
                logger.error(error_msg)
                return False, None, error_msg
    
    except Exception as e:
        error_msg = f"自动登录过程出错: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg 
    
async def validate_and_refresh_cookies(username: str, cookies: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[Dict[str, str]], str]:
    """验证Cookie有效性，如果无效则尝试自动登录刷新
    
    参数:
        username: 用户名
        cookies: 要验证的Cookie字典，如果为None则直接尝试登录
    
    返回值:
        元组 (success, cookies, message)
        success: 是否成功获取有效的Cookie
        cookies: 如果成功，返回有效的cookie字典；否则为None
        message: 状态消息
    """
    # 如果提供了cookie，先测试其有效性
    if cookies:
        try:
            # 使用一个简单的API端点来测试cookies是否有效
            test_url = f'{BASE_URL}/api/v1/user/info'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            async with httpx.AsyncClient(verify=False, timeout=10) as client:
                response = await client.get(
                    test_url,
                    cookies=cookies,
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"用户 {username} 的Cookie有效")
                    return True, cookies, "Cookie有效"
                else:
                    logger.warning(f"用户 {username} 的Cookie已过期，状态码: {response.status_code}")
                    # Cookie无效，尝试自动登录
        except Exception as e:
            logger.error(f"验证Cookie时出错: {str(e)}")
            # 出错时也尝试自动登录
    
    # Cookie无效或未提供，尝试自动登录
    logger.info(f"尝试为用户 {username} 自动登录获取Cookie")
    success, new_cookies, message = await auto_login(username)
    
    if success and new_cookies:
        logger.info(f"用户 {username} 自动登录成功，已获取新Cookie")
        return True, new_cookies, "成功获取新Cookie"
    else:
        logger.error(f"用户 {username} 自动登录失败: {message}")
        return False, None, f"自动登录失败: {message}"