#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: oxygen_monitor.py
# 描述: 飞机氧气监控功能业务逻辑

import logging
import re
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Callable

# 导入相关模块
from app.utils.config import ALL_AIRCRAFT
from app.api.ames import get_flb_list, get_flb_parts
from app.services.emailwechat import send_notification, send_monitoring_notifications

# 配置日志
logger = logging.getLogger("phm_system.services.oxygen_monitor")

async def run_monitoring(cookies: Dict[str, str], aircraft: str, start_date: str, end_date: str, 
                  psi1_threshold: float, psi2_threshold: float, employees: str, 
                  update_progress: Optional[Callable] = None,
                  username: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """执行氧气监控任务
    
    参数:
        cookies: 请求Cookie
        aircraft: 飞机号或"ALL"表示所有飞机
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        psi1_threshold: PSI1压力下降阈值
        psi2_threshold: PSI2压力下降阈值
        employees: 接收通知的员工号，多个以英文逗号分隔
        update_progress: 进度更新回调函数，接收进度百分比和消息两个参数
        username: 用户名，用于获取邮件设置
        
    返回值:
        (results, warnings) 元组，results是所有氧气数据，warnings是警告列表
    """
    try:
        if update_progress:
            update_progress(5, f"开始查询飞机 {aircraft} 的氧气数据...")
        
        logger.info(f"开始查询飞机 {aircraft} 的氧气数据 ({start_date} 至 {end_date})...")
        
        # 如果选择ALL，则需要查询所有飞机
        if aircraft == "ALL":
            aircraft_list = ALL_AIRCRAFT
        else:
            aircraft_list = [aircraft]
        
        # 存储所有飞机的所有氧气数据的列表
        all_oxygen_data = []
        # 记录所有警告的问题
        all_warnings = []
        
        # 如果员工号为空且提供了用户名，尝试从配置中获取
        if (not employees or not employees.strip()) and username:
            try:
                from app.utils.config import Config
                user_config = Config(username)
                config_employees = user_config.get_oxygen_employees()
                if config_employees:
                    employees = config_employees
                    logger.info(f"从用户配置中读取氧气监控员工号: {employees}")
            except Exception as e:
                logger.warning(f"从配置中获取氧气监控员工号失败: {str(e)}")
        
        logger.info(f"氧气监控任务使用的员工号: {employees}")
        
        # 遍历所有飞机
        total_aircraft = len(aircraft_list)
        for idx, ac in enumerate(aircraft_list, 1):
            progress_msg = f"正在处理飞机 {ac} ({idx}/{total_aircraft})"
            logger.info(progress_msg)
            
            if update_progress:
                progress = 10 + (idx / total_aircraft) * 70
                update_progress(int(progress), progress_msg)
            
            # 第一步：获取飞行日志列表
            flb_data = await get_flb_list(cookies, ac, start_date, end_date)
            if not flb_data:
                logger.info(f"没有找到飞机 {ac} 在指定日期范围内的飞行日志")
                continue
            
            logger.info(f"找到 {len(flb_data)} 条飞行日志记录")
            
            # 处理单架飞机的数据
            oxygen_data, warnings = await process_aircraft_data(cookies, ac, flb_data, psi1_threshold, psi2_threshold)
            
            # 合并数据
            all_oxygen_data.extend(oxygen_data)
            all_warnings.extend(warnings)
        
        # 发送警告通知
        if update_progress:
            update_progress(85, "处理完成，准备发送通知...")
        
        # 获取邮件接收设置
        email_recipients = ''
        if username:
            from app.utils.config import Config
            user_config = Config(username)
            email_recipients = user_config.get_oxygen_email_recipients()
            logger.info(f"获取到氧气监控邮件接收设置: {email_recipients}")
        
        # 使用邮件和消息通知服务发送通知
        try:
            if all_warnings:
                logger.info(f"发现 {len(all_warnings)} 条氧气压力下降警告，准备发送通知...")
                
                # 为每架有警告的飞机发送通知
                notification_sent = await send_monitoring_notifications(
                    cookies=cookies,
                    warnings=all_warnings,
                    aircraft=aircraft if aircraft != "ALL" else "所有飞机",
                    psi1_threshold=psi1_threshold,
                    psi2_threshold=psi2_threshold,
                    employees=employees,
                    email_recipients=email_recipients,
                    username=username
                )
                
                if notification_sent:
                    logger.info("成功发送氧气监控警告通知")
                    if update_progress:
                        update_progress(90, "已发送警告通知")
                else:
                    logger.warning("氧气监控警告通知发送失败或未配置收件人")
                    if update_progress:
                        update_progress(90, "通知发送失败或未配置收件人")
            
            elif not all_warnings and employees and aircraft_list:
                # 生成正常情况的通知消息
                if len(aircraft_list) == 1:
                    ac = aircraft_list[0]
                    normal_message = generate_normal_message(ac)
                else:
                    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
                    normal_message = f"[{current_datetime}] 所有飞机氧气压力正常，未发现异常下降。"
                
                logger.info(f"氧气压力正常，准备发送正常状态通知。员工号:{employees}, 邮箱:{email_recipients}")
                
                # 发送通知
                emp_list = [emp.strip() for emp in employees.split(',') if emp.strip()]
                notification_sent = False
                
                for emp_no in emp_list:
                    logger.debug(f"正在向员工 {emp_no} 发送氧气监控正常消息...")
                    success = send_notification(cookies, emp_no, normal_message)
                    if success:
                        notification_sent = True
                        logger.info(f"氧气监控正常消息已发送给员工 {emp_no}")
                    else:
                        logger.warning(f"向员工 {emp_no} 发送氧气监控正常消息失败")
                
                # 发送邮件通知
                if email_recipients and username:
                    from app.utils.config import Config
                    from app.utils.emailwechat_utils import send_email_notification
                    
                    user_config = Config(username)
                    username_email, password = user_config.get_login_info()
                    
                    if username_email and password:
                        email_subject = f"[氧气监控] 飞机{aircraft if aircraft != 'ALL' else ''}氧气压力正常"
                        logger.info(f"准备发送氧气监控正常邮件，主题: {email_subject}")
                        
                        # 注意这里直接使用 username_email 而不是 username，因为前者才是完整的邮箱地址
                        success = send_email_notification(username_email, password, email_recipients, email_subject, normal_message)
                        if success:
                            notification_sent = True
                            logger.info(f"氧气监控正常邮件已发送给 {email_recipients}")
                        else:
                            logger.warning(f"发送氧气监控正常邮件给 {email_recipients} 失败")
                    else:
                        logger.warning(f"未能获取到用户 {username} 的完整登录信息，无法发送氧气监控邮件")
                
                if notification_sent:
                    if update_progress:
                        update_progress(90, "已发送正常状态通知")
                else:
                    if update_progress:
                        update_progress(90, "通知发送失败或未配置收件人")
            else:
                if not all_warnings:
                    logger.info("未发现氧气压力异常")
                if not employees:
                    logger.info("未配置接收员工号，跳过通知")
                if not aircraft_list:
                    logger.info("没有处理任何飞机的数据，跳过通知")
                
                if update_progress:
                    update_progress(90, "未发现异常，无需发送通知")
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"发送氧气监控通知时出错: {str(e)}\n{error_details}")
            if update_progress:
                update_progress(90, f"发送通知时出错: {str(e)}")
        
        logger.info(f"氧气数据查询完成，共 {len(all_oxygen_data)} 条记录")
        if update_progress:
            status_msg = f"查询完成，共 {len(all_oxygen_data)} 条记录"
            if all_warnings:
                status_msg += f"，发现 {len(all_warnings)} 条警告"
            update_progress(100, status_msg)
        
        return all_oxygen_data, all_warnings
    
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"氧气监控过程中出错: {str(e)}"
        logger.error(f"{error_msg}\n{error_details}")
        if update_progress:
            update_progress(100, f"错误: {error_msg}")
        raise

async def process_aircraft_data(cookies: Dict[str, str], aircraft: str, flb_data: List[Dict[str, Any]], 
                         psi1_threshold: float, psi2_threshold: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """处理单架飞机的氧气数据，计算连续记录间的压力下降"""
    all_parts_data = []
    logger.info(f"开始处理飞机 {aircraft} 的 {len(flb_data)} 条飞行日志...")

    # 1. 收集所有阶段的数据
    for flb in flb_data:
        flb_id = flb.get('PKID')
        flb_date = flb.get('FLB_DATE', '').split(' ')[0] if flb.get('FLB_DATE') else ''
        flight_no = flb.get('FLIGHT_NO', '')
        # 使用起飞时间作为主要排序依据，若无则用一个早期时间替代以保持顺序
        takeoff_time_str = flb.get('TAKEOFF_TIME', '00:00')
        try:
            # 添加日期以进行正确的 datetime 排序
            sort_key_time = datetime.strptime(f"{flb_date} {takeoff_time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            logger.warning(f"无法解析日期时间: {flb_date} {takeoff_time_str} for FLB ID {flb_id}. Using default time.")
            # 提供一个默认时间，或根据需要处理错误
            sort_key_time = datetime.strptime(f"{flb_date} 00:00", "%Y-%m-%d %H:%M") if flb_date else datetime.min


        if not flb_id:
            logger.warning(f"跳过缺少 PKID 的 FLB 记录: {flb}")
            continue

        parts_data = await get_flb_parts(cookies, flb_id)
        if not parts_data:
            logger.debug(f"FLB ID {flb_id} 没有找到相关部件数据")
            continue

        for part in parts_data:
            # 添加必要的信息到每个 part 记录中
            part_info = {
                'aircraft': aircraft,
                'date': flb_date,
                'flight_no': flight_no,
                'takeoff_time': takeoff_time_str, # 保留原始起飞时间字符串用于显示
                'sort_key_time': sort_key_time, # 使用 datetime 对象进行排序
                'step': part.get('RELEASE_STEP', ''),
                'psi1': part.get('PSI1', ''),
                'psi2': part.get('PSI2', ''),
                'psi1_drop': 0, # 初始化压降
                'psi2_drop': 0, # 初始化压降
                'status': '正常' # 初始化状态
            }
            # 确保只添加包含 PSI 数据的记录
            if part_info['psi1'] or part_info['psi2']:
                 all_parts_data.append(part_info)
            else:
                logger.debug(f"跳过缺少 PSI 数据的部件记录: {part} from FLB ID {flb_id}")


    if not all_parts_data:
        logger.info(f"飞机 {aircraft} 在指定日期内没有有效的氧气部件数据。")
        return [], []

    # 2. 排序：按日期和起飞时间排序
    # 注意：如果一个 FLB 有多个 part (TR, AF等)，它们会有相同的 sort_key_time
    # 可能需要更精细的排序逻辑，例如根据 step 的顺序（TR -> PF -> AF?），但目前API似乎不提供此信息
    all_parts_data.sort(key=lambda x: x['sort_key_time'])
    logger.info(f"飞机 {aircraft} 共收集到 {len(all_parts_data)} 条有效部件记录，已排序。")


    oxygen_data = []
    warnings = []

    # 3. 遍历计算压降
    for i in range(len(all_parts_data)):
        current_part = all_parts_data[i]
        psi1_drop = 0
        psi2_drop = 0
        status = '正常'

        if i > 0:
            previous_part = all_parts_data[i-1]

            # 尝试计算 PSI1 下降
            try:
                # 确保 PSI 值存在且可转换为浮点数
                if previous_part.get('psi1') and current_part.get('psi1'):
                    prev_psi1 = float(previous_part['psi1'])
                    curr_psi1 = float(current_part['psi1'])
                    drop = prev_psi1 - curr_psi1
                    psi1_drop = max(0, drop) # 压降不能为负
                else:
                    psi1_drop = 0 # 如果任一值为无效/空，则压降为0
            except (ValueError, TypeError) as e:
                psi1_drop = 0
                logger.warning(f"计算 PSI1 压降时出错 (记录 {i-1} -> {i}): {e}. Prev='{previous_part.get('psi1')}', Curr='{current_part.get('psi1')}'")

            # 尝试计算 PSI2 下降
            try:
                 # 确保 PSI 值存在且可转换为浮点数
                if previous_part.get('psi2') and current_part.get('psi2'):
                    prev_psi2 = float(previous_part['psi2'])
                    curr_psi2 = float(current_part['psi2'])
                    drop = prev_psi2 - curr_psi2
                    psi2_drop = max(0, drop) # 压降不能为负
                else:
                    psi2_drop = 0 # 如果任一值为无效/空，则压降为0
            except (ValueError, TypeError) as e:
                psi2_drop = 0
                logger.warning(f"计算 PSI2 压降时出错 (记录 {i-1} -> {i}): {e}. Prev='{previous_part.get('psi2')}', Curr='{current_part.get('psi2')}'")

        # 4. 状态判断
        if psi1_drop >= psi1_threshold or psi2_drop >= psi2_threshold:
            status = '警告'

        # 记录最终结果
        current_part['psi1_drop'] = round(psi1_drop, 2) # 保留两位小数
        current_part['psi2_drop'] = round(psi2_drop, 2) # 保留两位小数
        current_part['status'] = status

        # 从结果中移除用于排序的临时键
        current_part.pop('sort_key_time', None)

        oxygen_data.append(current_part)

        # 5. 收集警告
        if status == '警告':
            warnings.append(current_part)
            logger.warning(f"检测到警告: 飞机={aircraft}, 日期={current_part['date']}, 航班={current_part['flight_no']}, "
                           f"阶段={current_part['step']}, PSI1={current_part['psi1']}, PSI2={current_part['psi2']}, "
                           f"PSI1降={psi1_drop}, PSI2降={psi2_drop}")

    logger.info(f"飞机 {aircraft} 数据处理完成，生成 {len(oxygen_data)} 条记录，发现 {len(warnings)} 条警告。")
    return oxygen_data, warnings

def generate_normal_message(aircraft: str) -> str:
    """生成正常情况的通知消息"""
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[{current_datetime}] 飞机 {aircraft} 氧气压力正常，未发现异常下降。"
    return message

def generate_warning_message(warnings: List[Dict[str, Any]], aircraft: str, psi1_threshold: float, psi2_threshold: float) -> str:
    """生成警告通知消息"""
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