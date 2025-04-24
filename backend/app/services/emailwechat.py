#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: emailwechat.py
# 描述: 邮件和消息发送业务逻辑

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入工具
from app.utils.emailwechat_utils import send_notification, send_email_notification
from app.utils.config import Config
from app.utils.auto_login import auto_login
import asyncio

# 配置日志
logger = logging.getLogger("phm_system.services.emailwechat")

async def send_monitoring_notifications(cookies: Dict[str, str], warnings: List[Dict[str, Any]], 
                                aircraft: str, psi1_threshold: float, psi2_threshold: float, 
                                employees: str, email_recipients: str = '', username: str = '') -> bool:
    """发送氧气监控通知
    
    参数:
        cookies: 请求Cookie
        warnings: 警告列表
        aircraft: 飞机号
        psi1_threshold: PSI1压力下降阈值
        psi2_threshold: PSI2压力下降阈值
        employees: 接收通知的员工号，多个以英文逗号分隔
        email_recipients: 接收邮件的邮箱地址，多个以英文逗号分隔
        username: 用户名，用于获取邮件服务的凭据
    
    返回值:
        布尔值表示是否成功发送通知
    """
    try:
        # 如果cookies为空且提供了用户名，尝试自动登录
        if (not cookies or len(cookies) == 0) and username:
            logger.info(f"Cookies为空，尝试使用用户 {username} 自动登录以发送氧气监控通知")
            success, new_cookies, message = await auto_login(username)
            if success:
                cookies = new_cookies
                logger.info(f"自动登录成功，已获取新的Cookie用于发送氧气监控通知")
            else:
                logger.error(f"自动登录失败，无法发送氧气监控通知: {message}")
                return False
        
        # 如果员工号为空，尝试从配置中获取
        if not employees or not employees.strip():
            if username:
                try:
                    config = Config(username)
                    config_employees = config.get_oxygen_employees()
                    if config_employees:
                        employees = config_employees
                        logger.info(f"从用户配置中读取氧气监控员工号: {employees}")
                except Exception as e:
                    logger.warning(f"从配置中获取氧气监控员工号失败: {str(e)}")
        
        # 生成通知消息
        message = generate_oxygen_warning_message(warnings, aircraft, psi1_threshold, psi2_threshold)
        logger.debug(f"生成的氧气监控通知消息: {message[:100]}...")
        
        # 发送微信/系统消息通知
        notification_sent = False
        if employees and employees.strip():
            emp_list = [emp.strip() for emp in employees.split(',') if emp.strip()]
            logger.info(f"准备向 {len(emp_list)} 名员工发送氧气监控警告消息")
            
            for emp_no in emp_list:
                logger.debug(f"正在向员工 {emp_no} 发送氧气监控消息...")
                success = send_notification(cookies, emp_no, message)
                if success:
                    notification_sent = True
                    logger.info(f"氧气监控警告消息已发送给员工 {emp_no}")
                else:
                    logger.warning(f"向员工 {emp_no} 发送氧气监控消息失败")
        else:
            logger.info("未配置氧气监控接收员工号，跳过系统消息通知")
        
        # 发送邮件通知
        email_sent = False
        if email_recipients and email_recipients.strip() and username:
            # 获取用户密码
            logger.info(f"准备发送氧气监控邮件通知给: {email_recipients}")
            config = Config(username)
            username_email, password = config.get_login_info()
            
            if username_email and password:
                email_subject = f"[氧气监控警告] 飞机 {aircraft} 氧气压力异常"
                logger.info(f"氧气监控邮件主题: {email_subject}")
                
                success = send_email_notification(username_email, password, email_recipients, email_subject, message)
                if success:
                    email_sent = True
                    logger.info(f"氧气监控警告邮件已发送给 {email_recipients}")
                else:
                    logger.warning(f"发送氧气监控邮件给 {email_recipients} 失败")
            else:
                logger.warning(f"未能获取到用户 {username} 的完整登录信息，无法发送氧气监控邮件")
        else:
            if not email_recipients or not email_recipients.strip():
                logger.info("未配置氧气监控邮件接收地址，跳过邮件通知")
            if not username:
                logger.info("未提供用户名，无法获取氧气监控邮件发送凭据")
        
        result = notification_sent or email_sent
        logger.info(f"氧气监控通知发送结果: {result} (消息通知: {notification_sent}, 邮件通知: {email_sent})")
        return result
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"发送氧气监控通知失败: {str(e)}\n{error_detail}")
        return False

async def send_bleed_notifications(cookies: Dict[str, str], aircraft_results: List[Dict[str, Any]], 
                            threshold_value: float, aircraft_type: str, 
                            employees: str, email_recipients: str = '', username: str = '') -> bool:
    """发送引气监控通知
    
    参数:
        cookies: 请求Cookie
        aircraft_results: 飞机分析结果列表
        threshold_value: 阈值
        aircraft_type: 飞机类型
        employees: 接收通知的员工号，多个以英文逗号分隔
        email_recipients: 接收邮件的邮箱地址，多个以英文逗号分隔
        username: 用户名，用于获取邮件服务的凭据
    
    返回值:
        布尔值表示是否成功发送通知
    """
    try:
        # 如果cookies为空且提供了用户名，尝试自动登录
        if (not cookies or len(cookies) == 0) and username:
            logger.info(f"Cookies为空，尝试使用用户 {username} 自动登录")
            success, new_cookies, message = await auto_login(username)
            if success:
                cookies = new_cookies
                logger.info(f"自动登录成功，已获取新的Cookie用于发送引气监控通知")
            else:
                logger.error(f"自动登录失败，无法发送引气监控通知: {message}")
                return False
                
        # 生成通知消息
        message, detailed_info = generate_bleed_notification_message(aircraft_results, threshold_value, aircraft_type)
        logger.debug(f"生成的引气监控通知消息: {message[:100]}...")
        
        # 检查是否有异常
        has_abnormal = "异常" in message
        
        # 发送微信/系统消息通知
        notification_sent = False
        if employees and employees.strip():
            emp_list = [emp.strip() for emp in employees.split(',') if emp.strip()]
            logger.info(f"准备向 {len(emp_list)} 名员工发送引气监控{'警告' if has_abnormal else '正常'}消息")
            
            for emp_no in emp_list:
                logger.debug(f"正在向员工 {emp_no} 发送消息...")
                success = send_notification(cookies, emp_no, message)
                if success:
                    notification_sent = True
                    logger.info(f"引气监控{' 警告' if has_abnormal else '正常'}消息已发送给员工 {emp_no}")
                else:
                    logger.warning(f"向员工 {emp_no} 发送引气监控消息失败")
        else:
            logger.info("未配置接收员工号，跳过系统消息通知")
        
        # 发送邮件通知
        email_sent = False
        if email_recipients and email_recipients.strip() and username:
            # 获取用户密码
            logger.info(f"准备发送引气监控邮件通知给: {email_recipients}")
            config = Config(username)
            username_email, password = config.get_login_info()
            
            if username_email and password:
                # 获取飞机号
                if len(aircraft_results) == 1:
                    acno = aircraft_results[0]['acno']
                    if has_abnormal:
                        email_subject = f"[引气监控警告] {acno} {aircraft_type}飞机引气压力异常"
                    else:
                        email_subject = f"[引气监控通知] {acno} {aircraft_type}飞机引气压力正常"
                else:
                    # 多架飞机的情况
                    if has_abnormal:
                        # 提取异常飞机号
                        abnormal_acnos = [aircraft['acno'] for aircraft in aircraft_results 
                                        if aircraft['t1_avg'] <= threshold_value or aircraft['t2_avg'] <= threshold_value]
                        if abnormal_acnos:
                            abnormal_acnos_str = ','.join(abnormal_acnos)
                            email_subject = f"[引气监控警告] {abnormal_acnos_str} {aircraft_type}飞机引气压力异常"
                        else:
                            email_subject = f"[引气监控警告] {aircraft_type}飞机引气压力异常"
                    else:
                        email_subject = f"[引气监控通知] {aircraft_type}飞机引气压力正常"
                
                logger.info(f"引气监控邮件主题: {email_subject}")
                
                # 发送邮件通知
                email_content = detailed_info if detailed_info else message
                success = send_email_notification(username_email, password, email_recipients, email_subject, email_content)
                if success:
                    email_sent = True
                    logger.info(f"引气监控{' 警告' if has_abnormal else '正常'}邮件已发送给 {email_recipients}")
                else:
                    logger.warning(f"发送引气监控邮件给 {email_recipients} 失败")
            else:
                logger.warning(f"未能获取到用户 {username} 的完整登录信息，无法发送邮件")
        else:
            if not email_recipients or not email_recipients.strip():
                logger.info("未配置邮件接收地址，跳过邮件通知")
            if not username:
                logger.info("未提供用户名，无法获取邮件发送凭据")
        
        result = notification_sent or email_sent
        logger.info(f"引气监控通知发送结果: {result} (消息通知: {notification_sent}, 邮件通知: {email_sent})")
        return result
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"发送引气监控通知失败: {str(e)}\n{error_detail}")
        return False

def generate_oxygen_warning_message(warnings: List[Dict[str, Any]], aircraft: str, psi1_threshold: float, psi2_threshold: float) -> str:
    """生成氧气监控警告消息
    
    参数:
        warnings: 警告列表
        aircraft: 飞机号
        psi1_threshold: PSI1压力下降阈值
        psi2_threshold: PSI2压力下降阈值
    
    返回值:
        格式化的警告消息
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[{current_datetime}] 飞机 {aircraft} 氧气压力下降异常警告:\n\n"
    
    # 按航班和日期分组
    warnings_by_flight = {}
    for warning in warnings:
        key = f"{warning['flight_no']} {warning['date']}"
        if key not in warnings_by_flight:
            warnings_by_flight[key] = []
        warnings_by_flight[key].append(warning)
    
    # 添加每个航班的警告信息
    for flight_key, flight_warnings in warnings_by_flight.items():
        message += f"航班: {flight_key}\n"
        
        for warning in flight_warnings:
            psi1_drop = warning.get('psi1_drop', 0)
            psi2_drop = warning.get('psi2_drop', 0)
            
            if psi1_drop >= psi1_threshold:
                message += f"- PSI1压力下降值: {psi1_drop:.1f}，超过阈值 {psi1_threshold}\n"
            
            if psi2_drop >= psi2_threshold:
                message += f"- PSI2压力下降值: {psi2_drop:.1f}，超过阈值 {psi2_threshold}\n"
        
        message += "\n"
    
    # 添加阈值信息
    message += f"警告阈值设置：PSI1 = {psi1_threshold}，PSI2 = {psi2_threshold}"
    
    return message

def generate_oxygen_normal_message(aircraft: str) -> str:
    """生成氧气监控正常情况的通知消息
    
    参数:
        aircraft: 飞机号
    
    返回值:
        格式化的正常消息
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[{current_datetime}] 飞机 {aircraft} 氧气压力正常，未发现异常下降。"
    return message

def generate_bleed_notification_message(aircraft_results: List[Dict[str, Any]], threshold_value: float, aircraft_type: str) -> tuple:
    """生成引气监控通知消息
    
    参数:
        aircraft_results: 飞机分析结果列表
        threshold_value: 阈值
        aircraft_type: 飞机类型
    
    返回值:
        元组 (message, detailed_info)
    """
    detailed_info = ""
    abnormal_found = False
    abnormal_aircrafts = []

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[{current_datetime}] 引气压力异常机号:"

    detailed_info += f"【{aircraft_type}飞机引气压力监控报告】\n"
    detailed_info += "------------------------------------\n"
    detailed_info += f"监控时间: {current_datetime}\n"
    detailed_info += f"监控阈值: {threshold_value}\n"
    detailed_info += "------------------------------------\n\n"
    detailed_info += "【各飞机数据统计】\n"

    for aircraft in aircraft_results:
        acno = aircraft['acno']
        t1_avg = aircraft['t1_avg']
        t2_avg = aircraft['t2_avg']
        threshold = aircraft.get('threshold', threshold_value)

        is_t1_abnormal = t1_avg <= threshold
        is_t2_abnormal = t2_avg <= threshold
        is_abnormal = is_t1_abnormal or is_t2_abnormal

        # 生成详细信息行
        detailed_info += f"• 飞机 {acno}:\n"
        if is_t1_abnormal:
            detailed_info += f"  - T1平均值: 【{t1_avg:.1f}】(低于阈值{threshold})\n"
        else:
            detailed_info += f"  - T1平均值: {t1_avg:.1f}\n"
            
        if is_t2_abnormal:
            detailed_info += f"  - T2平均值: 【{t2_avg:.1f}】(低于阈值{threshold})\n"
        else:
            detailed_info += f"  - T2平均值: {t2_avg:.1f}\n"
        
        if 'max_flights' in aircraft and aircraft['max_flights']:
            detailed_info += "  - 最大值详情:\n"
            for flight_info in aircraft['max_flights']:
                flight_date = flight_info.get('date', '')
                flight_no = flight_info.get('flight_no', '')
                t1 = flight_info.get('t1', '')
                t2 = flight_info.get('t2', '')
                
                if flight_info.get('type') == 'T1' and t1:
                    detailed_info += f"    T1最大值: {t1}, 航班: {flight_no}, 日期: {flight_date}\n"
                
                if flight_info.get('type') == 'T2' and t2:
                    detailed_info += f"    T2最大值: {t2}, 航班: {flight_no}, 日期: {flight_date}\n"
        
        detailed_info += "\n"
        
        if is_abnormal:
            abnormal_found = True
            abnormal_aircrafts.append(acno)

    # 生成简短消息
    if abnormal_found:
        message += " " + ", ".join(abnormal_aircrafts)
        message += f"，阈值({threshold_value})"
        detailed_info += "❌ 警告：检测到以下飞机引气压力异常！\n"
        for abnormal in abnormal_aircrafts:
            detailed_info += f"  - {abnormal}\n"
    else:
        if len(aircraft_results) == 1:
            acno = aircraft_results[0]['acno']
            message = f"[{current_datetime}] 飞机 {acno} 引气压力正常。{aircraft_type}阈值：{threshold_value}。"
            detailed_info += f"✅ 飞机 {acno} 引气压力正常\n"
        else:
            message = f"[{current_datetime}] 所有{aircraft_type}飞机引气压力正常。阈值：{threshold_value}。"
            detailed_info += "✅ 所有监控的飞机引气压力正常\n"

    return message, detailed_info