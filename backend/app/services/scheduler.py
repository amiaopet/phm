#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: scheduler.py
# 描述: 定时任务业务逻辑

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

# 导入工具
from app.utils.scheduler_utils import add_cron_job, remove_job
from app.utils.config import Config
from app.utils.auto_login import auto_login

# 配置日志
logger = logging.getLogger("phm_system.services.scheduler")


# 存储任务状态
monitoring_tasks = {}

def update_task_progress(task_id: str, progress: int, message: str) -> None:
    """更新任务进度
    
    参数:
        task_id: 任务ID
        progress: 进度百分比
        message: 进度消息
    """
    if task_id in monitoring_tasks:
        monitoring_tasks[task_id]['progress'] = progress
        monitoring_tasks[task_id]['message'] = message
        monitoring_tasks[task_id]['timestamp'] = datetime.now().isoformat()

def check_task_status(task_id: str) -> Dict[str, Any]:
    """检查任务状态
    
    参数:
        task_id: 任务ID
    
    返回值:
        任务状态信息
    """
    if task_id not in monitoring_tasks:
        return {
            "status": "not_found",
            "progress": 0,
            "message": "任务不存在",
            "timestamp": datetime.now().isoformat()
        }
    
    return monitoring_tasks[task_id]

def get_task_result(task_id: str) -> Dict[str, Any]:
    """获取任务结果
    
    参数:
        task_id: 任务ID
    
    返回值:
        任务结果
    """
    if task_id not in monitoring_tasks:
        return {
            "status": "not_found",
            "message": "任务不存在"
        }
    
    task = monitoring_tasks[task_id]
    
    if task['status'] != 'completed':
        return {
            "status": task['status'],
            "message": "任务尚未完成"
        }
    
    return {
        "status": "completed",
        "results": task.get('results', []),
        "timestamp": task.get('timestamp', datetime.now().isoformat())
    }

async def run_scheduled_bleed_monitor(username: str, aircraft_type: str, aircraft_no: str, 
                                    threshold_value: float, employees: str, 
                                    email_recipients: str, date_range: str):
    """执行计划的引气监控任务
    
    参数:
        username: 用户名
        aircraft_type: 飞机类型
        aircraft_no: 飞机号
        threshold_value: 阈值
        employees: 接收通知的员工号
        email_recipients: 接收邮件的邮箱地址
        date_range: 日期范围
    """
    logger.info(f"开始执行计划的引气监控: {aircraft_type} {aircraft_no}, 阈值: {threshold_value}")
    
    try:
        # 自动登录获取cookies
        success, cookies, message = await auto_login(username)
        
        if success and cookies:
            # 创建临时任务ID - 添加时间戳确保唯一性
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y%m%d%H%M%S%f')[:18]  # 毫秒精度确保唯一
            task_id = f"bleed_auto_{timestamp}"
            
            # 初始化任务状态 - 确保在字典中创建记录
            from app.api.local import monitoring_tasks
            
            monitoring_tasks[task_id] = {
                'status': 'starting',
                'progress': 0,
                'message': '开始自动监控任务...',
                'results': None,
                'timestamp': current_time.isoformat(),
                'username': username,
                'threshold': threshold_value
            }
            
            # 设置日期范围
            end_date = current_time.strftime("%Y-%m-%d")
            
            if date_range == "最近一天":
                start_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_range == "一周":
                start_date = (current_time - timedelta(days=7)).strftime("%Y-%m-%d")
            elif date_range == "一个月":
                start_date = (current_time - timedelta(days=30)).strftime("%Y-%m-%d")
            elif date_range == "三个月":
                start_date = (current_time - timedelta(days=90)).strftime("%Y-%m-%d")
            elif date_range == "半年":
                start_date = (current_time - timedelta(days=180)).strftime("%Y-%m-%d")
            else:
                # 默认三个月
                start_date = (current_time - timedelta(days=90)).strftime("%Y-%m-%d")
            
            logger.info(f"计划的引气监控使用时间范围: {start_date} 至 {end_date}")
            
            try:
                # 从模块导入运行监控的函数
                from app.api.local import run_bleed_monitoring_thread
                
                # 执行监控
                # 使用线程避免阻塞调度器
                thread = threading.Thread(
                    target=run_bleed_monitoring_thread,
                    args=(
                        task_id, 
                        cookies, 
                        aircraft_type, 
                        aircraft_no, 
                        start_date, 
                        end_date, 
                        threshold_value, 
                        employees,
                        email_recipients,
                        username
                    )
                )
                thread.daemon = True
                thread.start()
                
                # 更新上次运行时间
                config = Config(username)
                config.update_bleed_last_run_date(current_time.isoformat())
                
                logger.info(f"自动引气监控任务已启动: {task_id}")
            except Exception as e:
                logger.error(f"创建引气监控线程失败: {str(e)}")
                import traceback
                logger.error(f"异常详情: {traceback.format_exc()}")
        else:
            logger.error(f"自动引气监控登录失败: {message}")
    
    except Exception as e:
        logger.error(f"执行计划的引气监控时出错: {str(e)}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")

def setup_bleed_monitor_job(username: str, password: str, aircraft_type: str, aircraft_no: str, 
                           threshold_value: float, employees: str, email_recipients: str,
                           hour: str, minute: str) -> str:
    """设置引气监控定时任务
    
    参数:
        username: 用户名
        password: 密码
        aircraft_type: 飞机类型
        aircraft_no: 飞机号
        threshold_value: 阈值
        employees: 接收通知的员工号
        email_recipients: 接收邮件的邮箱地址
        hour: 小时
        minute: 分钟
    
    返回值:
        任务ID
    """
    # 创建任务ID
    job_id = f"bleed_auto_{username}_{aircraft_type}"
    
    # 确保配置已保存
    config = Config(username)
    config.set_login_info(username, password)
    
    # 获取日期范围设置
    _, _, _, date_range = config.get_bleed_auto_settings()
    
    # 定义任务执行函数的封装
    async def job_wrapper():
        await run_scheduled_bleed_monitor(
            username=username,
            aircraft_type=aircraft_type,
            aircraft_no=aircraft_no,
            threshold_value=threshold_value,
            employees=employees,
            email_recipients=email_recipients,
            date_range=date_range
        )
    
    # 添加定时任务
    success = add_cron_job(
        job_id=job_id,
        func=job_wrapper,
        hour=hour,
        minute=minute,
        second='0'
    )
    
    if success:
        logger.info(f"引气监控定时任务已设置: {job_id}, 执行时间: {hour}:{minute}")
    else:
        logger.error(f"设置引气监控定时任务失败: {job_id}")
    
    return job_id