#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: emailwechat_utils.py
# 描述: 邮件和消息发送工具函数

import requests
import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import Dict, Optional, Tuple, List, Any

# 导入配置
from app.utils.config import BASE_URL, MSG_API_URL

# 配置日志
logger = logging.getLogger("phm_system.emailwechat")

def send_notification(cookies: Dict[str, str], emp_no: str, message: str, log_func: Optional[callable] = None) -> bool:
    """发送通知消息
    
    参数:
        cookies: 请求Cookies
        emp_no: 接收员工号，如果为空则只返回消息而不发送
        message: 发送的消息内容
        log_func: 日志函数，可选
    
    返回值:
        如果emp_no为空，返回True
        否则返回布尔值表示发送是否成功
    """
    # 如果员工号为空，则只记录消息但不发送
    if not emp_no:
        if log_func:
            log_func(f"生成的消息内容：{message}")
        else:
            logger.info(f"生成的消息内容：{message}")
        return True
    
    # 发送消息
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/views/sjfx/px/sentTextMessage.shtml',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'empNo': emp_no,
        'content': message,
        'FunctionCode': 'TIANPAN_PX_SENDMSG'
    }
    
    try:
        response = requests.post(
            MSG_API_URL,
            headers=headers,
            cookies=cookies,
            data=data,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            if log_func:
                log_func(f"消息已成功发送给员工 {emp_no}: {message}")
            else:
                logger.info(f"消息已成功发送给员工 {emp_no}")
                logger.debug(f"消息内容: {message}")
            return True
        else:
            if log_func:
                log_func(f"发送消息给员工 {emp_no} 失败，状态码: {response.status_code}")
            else:
                logger.error(f"发送消息给员工 {emp_no} 失败，状态码: {response.status_code}")
            return False
    
    except Exception as e:
        if log_func:
            log_func(f"发送消息给员工 {emp_no} 时出错: {str(e)}")
        else:
            logger.error(f"发送消息给员工 {emp_no} 时出错: {str(e)}")
        return False

def send_email_notification(username: str, password: str, recipients: str, subject: str, message: str, log_func: Optional[callable] = None) -> bool:
    """发送邮件通知
    
    参数:
        username: 登录用户名（可以包含@juneyaoair.com，也可以不包含）
        password: 登录密码
        recipients: 收件人列表，多个收件人用逗号分隔
        subject: 邮件主题
        message: 邮件内容
        log_func: 日志函数，可选
    
    返回值:
        布尔值表示发送是否成功
    """
    if not username or not password or not recipients:
        if log_func:
            log_func("邮件发送失败：用户名、密码或收件人为空")
        else:
            logger.error("邮件发送失败：用户名、密码或收件人为空")
        return False
    
    # 处理用户名格式，确保有完整的邮箱地址
    if '@' not in username:
        sender = f"{username}@juneyaoair.com"
    else:
        sender = username
    
    # 构建邮件内容
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = recipients
    
    try:
        # 连接到SMTP服务器
        smtp_server = "smtp.juneyaoair.com"
        smtp_port = 465
        
        # 使用SSL连接
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        
        # 登录时，如果username包含@，则直接使用；否则添加域名
        login_username = sender
        server.login(login_username, password)
        
        # 发送邮件
        server.sendmail(sender, recipients.split(','), msg.as_string())
        server.quit()
        
        if log_func:
            log_func(f"邮件已成功发送给: {recipients}")
        else:
            logger.info(f"邮件已成功发送给: {recipients}")
        return True
        
    except Exception as e:
        if log_func:
            log_func(f"邮件发送失败: {str(e)}")
        else:
            logger.error(f"邮件发送失败: {str(e)}")
        return False