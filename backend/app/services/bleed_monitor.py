#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: bleed_monitor.py
# 描述: 飞机引气监控功能业务逻辑

import requests
import re
import logging
import json
from datetime import datetime, timedelta
import concurrent.futures
import urllib3
import traceback
import pickle
import os
import asyncio
from typing import Dict, List, Any, Tuple, Optional, Callable

# 导入相关模块
from app.utils.config import CFM_AIRCRAFT, V2500_AIRCRAFT, ALL_AIRCRAFT, BASE_URL
from app.api.ames import get_aircraft_data
from app.services.emailwechat import send_bleed_notifications

# 配置日志
logger = logging.getLogger("phm_system.services.bleed_monitor")

# 禁用不安全连接警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def run_monitoring(cookies: Dict[str, str], aircraft_type: str, aircraft_no: str, 
                  start_date: str, end_date: str, threshold_value: float, 
                  employees: str, update_progress: Optional[Callable] = None,
                  username: Optional[str] = None) -> Tuple[List[Dict[str, Any]], str]:
    """执行引气监控任务
    
    参数:
        cookies: 请求Cookie
        aircraft_type: 飞机类型 (CFM/V2500)
        aircraft_no: 飞机号 (特定飞机号或"全部")
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        threshold_value: 压力阈值
        employees: 接收通知的员工号，多个以英文逗号分隔
        update_progress: 进度更新回调函数，接收进度百分比和消息两个参数
        username: 用户名，用于获取邮件设置
        
    返回值:
        (results, detailed_info) 元组，results是分析结果列表，detailed_info是详细信息文本
    """
    try:
        logger.info(f"开始监控任务: {aircraft_type}, {aircraft_no}, {start_date} 至 {end_date}, 阈值: {threshold_value}")
        if update_progress:
            update_progress(5, f"开始监控任务: {aircraft_type}, {aircraft_no}")
        
        # 确定要监控的飞机列表
        aircraft_list = []
        if aircraft_no == "全部":
            aircraft_list = CFM_AIRCRAFT if aircraft_type == "CFM" else V2500_AIRCRAFT
        else:
            aircraft_list = [aircraft_no]
        
        # 确定飞机类型对应的sub参数
        sub = "A01" if aircraft_type == "CFM" else "A17"
        
        logger.info(f"开始监控 {len(aircraft_list)} 架 {aircraft_type} 飞机")
        
        # 存储所有分析结果
        aircraft_results = []
        
        # 创建任务列表
        tasks = []
        for acno in aircraft_list:
            logger.info(f"提交分析飞机 {acno} 的任务...")
            tasks.append(process_aircraft(cookies, sub, acno, start_date, end_date, threshold_value))
        
        # 并行执行所有异步任务
        results = await asyncio.gather(*tasks)
        
        # 过滤掉None的结果
        aircraft_results = [result for result in results if result]
        
        if update_progress:
            update_progress(80, "分析完成，准备通知...")
        
        # 生成通知消息
        logger.info("分析完成，准备通知...")
        generated_message, detailed_info = generate_notification_message(aircraft_results, threshold_value, aircraft_type)

        # 发送通知消息 - 获取用户配置中的邮件接收设置
        try:
            # 如果有username，则获取用户配置中的邮件设置
            email_recipients = ''
            if username:
                from app.utils.config import Config
                user_config = Config(username)
                email_recipients = user_config.get_bleed_email_recipients()
                logger.info(f"获取到引气监控邮件接收设置: {email_recipients}")
            else:
                logger.info("没有提供用户名，无法获取邮件接收设置")
            
            # 调用发送通知函数
            if aircraft_results:  # 只要有分析结果，无论是否异常都发送通知
                logger.info(f"准备发送引气监控通知，结果数量: {len(aircraft_results)}, 员工号: {employees}, 邮箱: {email_recipients}")
                notification_sent = await send_bleed_notifications(
                    cookies=cookies,
                    aircraft_results=aircraft_results,
                    threshold_value=threshold_value,
                    aircraft_type=aircraft_type,
                    employees=employees,
                    email_recipients=email_recipients,
                    username=username
                )
                
                if notification_sent:
                    logger.info("成功发送通知消息")
                    if update_progress:
                        update_progress(90, "已发送通知消息")
                else:
                    logger.warning("通知消息发送失败或未配置收件人")
                    if update_progress:
                        update_progress(90, "通知消息发送失败或未配置收件人")
            else:
                logger.warning("没有有效的分析结果，跳过通知发送")
                if update_progress:
                    update_progress(90, "没有有效的分析结果，跳过通知发送")
        except Exception as e:
            error_detail = traceback.format_exc()
            logger.error(f"发送通知消息时出错: {str(e)}\n{error_detail}")
            if update_progress:
                update_progress(90, f"发送通知消息时出错: {str(e)}")
        
        if update_progress:
            update_progress(100, "分析任务已完成")
        
        return aircraft_results, detailed_info
    
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"监控过程中出错: {str(e)}"
        logger.error(f"{error_msg}\n{error_details}")
        if update_progress:
            update_progress(100, f"错误: {error_msg}")
        raise

async def process_aircraft(cookies: Dict[str, str], sub: str, acno: str, 
                    start_date: str, end_date: str, 
                    threshold_value: float) -> Optional[Dict[str, Any]]:
    """处理单个飞机数据"""
    try:
        logger.info(f"正在分析飞机 {acno}...")
        
        # 获取飞机数据 - 添加await关键字获取实际数据而不是协程对象
        data = await get_aircraft_data(cookies, sub, acno, start_date, end_date)
        if not data:
            logger.info(f"没有找到飞机 {acno} 的数据")
            return None
        
        # 分析数据
        result = analyze_data(data, acno, threshold_value)
        if not result:
            return None
        
        t1_avg, t2_avg, max_flights, all_flights = result
        
        # 返回分析结果
        return {
            'acno': acno,
            't1_avg': t1_avg,
            't2_avg': t2_avg,
            'max_flights': max_flights,  # 最大值航班
            'all_flights': all_flights,  # 所有航班数据
            'threshold': threshold_value
        }
    except Exception as e:
        logger.error(f"处理飞机 {acno} 时出错: {str(e)}")
        return None

def analyze_data(data: List[Dict[str, Any]], acno: str, 
                threshold_value: float) -> Optional[Tuple[float, float, List[Dict[str, Any]], List[Dict[str, Any]]]]:
    """分析飞机数据，计算T1和T2的平均值，找出最大值对应的航班"""
    if not data:
        return None
    
    t1_values = []
    t2_values = []
    flight_data = []
    
    # 从第一条数据的PLF_SUB判断飞机类型
    plf_sub = data[0].get('PLF_SUB', '') if data else ''
    aircraft_type = "CFM" if plf_sub == "A01" else "V2500"
    logger.info(f"分析 {acno} 数据: 检测到飞机类型为 {aircraft_type} (PLF_SUB: {plf_sub})")
    
    # 记录T1和T2的最大值及对应航班
    max_t1 = -1
    max_t2 = -1
    max_t1_flight = None
    max_t2_flight = None
    
    for item in data:
        raw_msg = item.get('RAW_MSG', '')
        flight_no = item.get('FLIGHT_NO', '')
        date = item.get('UTC_DATE', '')
        utc_time = item.get('UTC_TIME', '')
        dep_station = item.get('DEP_STATION', '')
        arr_station = item.get('ARR_STATION', '')
        ph = item.get('PH', '')  # 航段信息
        
        t1_value = None
        t2_value = None
        s_line_found = None  # 用于记录匹配到的S行
        
        if aircraft_type == "CFM":
            # CFM机型使用正则表达式提取T1和T2值
            t1_match = re.search(r'T1(\d{3}),(\d{3}),(\d{3}),(\d+),', raw_msg)
            t2_match = re.search(r'T2(\d{3}),(\d{3}),(\d{3}),(\d+),', raw_msg)
            
            if t1_match and t2_match:
                t1_value = int(t1_match.group(4))
                t2_value = int(t2_match.group(4))
                logger.debug(f"CFM格式匹配: T1={t1_value}, T2={t2_value}")
        else:
            # V2500机型，处理S行数据
            # 首先尝试匹配S0-S9所有可能的行
            s_matches = []
            
            # 使用正则表达式匹配所有可能的S行格式 S[0-9]xxx0xxx
            pattern = r'S([0-9])(\d{3})0(\d{3})'
            matches = re.finditer(pattern, raw_msg)
            
            for match in matches:
                try:
                    s_num = match.group(1)
                    t1_str = match.group(2)
                    t2_str = match.group(3)
                    
                    if t1_str.isdigit() and t2_str.isdigit():
                        s_t1 = float(t1_str) / 10
                        s_t2 = float(t2_str) / 10
                        
                        s_matches.append({
                            'line': f'S{s_num}',
                            't1': s_t1,
                            't2': s_t2,
                            'raw': match.group(0)
                        })
                        
                        logger.debug(f"V2500格式匹配: S{s_num}, T1={s_t1}, T2={s_t2}")
                except Exception as e:
                    logger.error(f"V2500格式解析错误: {str(e)}")
            
            # 如果找到了S行数据
            if s_matches:
                # 优先使用S1行的数据，如果没有S1则按照优先级S1 > S2 > ... > S9 > S0
                priorities = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S0']
                
                selected_s = None
                for p in priorities:
                    match = next((s for s in s_matches if s['line'] == p), None)
                    if match:
                        selected_s = match
                        break
                
                # 如果找不到任何优先级的匹配，使用第一个匹配
                if not selected_s and s_matches:
                    selected_s = s_matches[0]
                
                if selected_s:
                    t1_value = selected_s['t1']
                    t2_value = selected_s['t2']
                    s_line_found = selected_s['line']
                    logger.debug(f"使用{selected_s['line']}行数据: T1={t1_value}, T2={t2_value}")
        
        if t1_value is not None and t2_value is not None:
            t1_values.append(t1_value)
            t2_values.append(t2_value)
            
            # 记录当前航班信息
            flight_info = {
                'flight_no': flight_no,
                'date': date,
                'time': utc_time,
                'dep_station': dep_station,
                'arr_station': arr_station,
                'ph': ph,
                't1': t1_value,
                't2': t2_value,
                's_line': s_line_found  # 记录匹配到的S行
            }
            
            flight_data.append(flight_info)
            
            # 更新T1最大值记录
            if t1_value > max_t1:
                max_t1 = t1_value
                max_t1_flight = flight_info.copy()
            
            # 更新T2最大值记录
            if t2_value > max_t2:
                max_t2 = t2_value
                max_t2_flight = flight_info.copy()
    
    if not t1_values or not t2_values:
        logger.error(f"无法从飞机 {acno} 的数据中提取T1和T2值")
        return None
    
    # 计算平均值
    t1_avg = sum(t1_values) / len(t1_values)
    t2_avg = sum(t2_values) / len(t2_values)
    
    # 记录统计信息
    stats_info = f"飞机 {acno} 数据统计: 共 {len(flight_data)} 条记录, T1平均值: {t1_avg:.1f}, T2平均值: {t2_avg:.1f}"
    logger.info(stats_info)
    
    # 最大值信息
    t1_max_info = f"T1最大值: {max_t1}, 航班: {max_t1_flight['flight_no']}, 日期: {max_t1_flight['date']}"
    t2_max_info = f"T2最大值: {max_t2}, 航班: {max_t2_flight['flight_no']}, 日期: {max_t2_flight['date']}"
    
    # 如果有S行信息，添加到输出
    if 's_line' in max_t1_flight and max_t1_flight['s_line']:
        t1_max_info += f", S行: {max_t1_flight['s_line']}"
    
    if 's_line' in max_t2_flight and max_t2_flight['s_line']:
        t2_max_info += f", S行: {max_t2_flight['s_line']}"
    
    logger.info(t1_max_info)
    logger.info(t2_max_info)
    
    # 收集最大值对应的航班信息
    max_flights = []
    
    if max_t1_flight:
        max_flights.append({
            'type': 'T1',
            'flight_no': max_t1_flight['flight_no'],
            'date': max_t1_flight['date'],
            't1': max_t1,
            't2': max_t1_flight['t2'],
            's_line': max_t1_flight.get('s_line', '')
        })
    
    if max_t2_flight and max_t2_flight != max_t1_flight:
        max_flights.append({
            'type': 'T2',
            'flight_no': max_t2_flight['flight_no'],
            'date': max_t2_flight['date'],
            't1': max_t2_flight['t1'],
            't2': max_t2,
            's_line': max_t2_flight.get('s_line', '')
        })
    
    # 返回值：T1平均值、T2平均值、最大值航班信息、所有航班数据
    return t1_avg, t2_avg, max_flights, flight_data

def generate_notification_message(aircraft_results: List[Dict[str, Any]], 
                                threshold_value: float, 
                                aircraft_type: str) -> Tuple[str, str]:
    """生成通知消息内容"""
    detailed_info = ""
    abnormal_found = False
    abnormal_aircrafts = []

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[{current_datetime}] 引气压力异常机号:"

    detailed_info += "【各飞机数据统计】\n"

    for aircraft in aircraft_results:
        acno = aircraft['acno']
        t1_avg = aircraft['t1_avg']
        t2_avg = aircraft['t2_avg']
        threshold = aircraft.get('threshold', threshold_value)

        is_t1_abnormal = t1_avg <= threshold
        is_t2_abnormal = t2_avg <= threshold
        is_abnormal = is_t1_abnormal or is_t2_abnormal

        detailed_info += f"• 飞机 {acno}: "
        if is_t1_abnormal:
            detailed_info += f"T1平均值=【{t1_avg:.1f}】(低于阈值{threshold}), "
        else:
            detailed_info += f"T1平均值={t1_avg:.1f}, "

        if is_t2_abnormal:
            detailed_info += f"T2平均值=【{t2_avg:.1f}】(低于阈值{threshold})"
        else:
            detailed_info += f"T2平均值={t2_avg:.1f}"

        detailed_info += "\n"

        if is_abnormal:
            abnormal_found = True
            message += f" {acno}"
            abnormal_info = f"{acno}: "
            if is_t1_abnormal:
                message += f"(T1={t1_avg:.1f})"
                abnormal_info += f"T1={t1_avg:.1f} "
            if is_t2_abnormal:
                message += f"(T2={t2_avg:.1f})"
                abnormal_info += f"T2={t2_avg:.1f}"
            message += ","
            abnormal_aircrafts.append(abnormal_info)

    if message.endswith(','):
        message = message[:-1]
    message += f"。{aircraft_type}阈值：{threshold_value}。"
    
    if abnormal_found:
        detailed_info += "❌ 警告：检测到引气压力异常！\n"
        for abnormal in abnormal_aircrafts:
            detailed_info += f"  - {abnormal}\n"
    else:
        if len(aircraft_results) == 1:
            acno = aircraft_results[0]['acno']
            detailed_info += f"✅ 飞机 {acno} 引气压力正常\n"
            message = f"[{current_datetime}] 飞机 {acno} 引气压力正常。"
        else:
            detailed_info += "✅ 所有飞机引气压力正常\n"
            message = f"[{current_datetime}] 所有飞机引气压力正常。"

    return (message, detailed_info)