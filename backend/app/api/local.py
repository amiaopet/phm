#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: local.py
# 描述: 本地API接口

import logging
import pickle
import os
import secrets
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header, Body, status, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel

# 导入工具
from app.utils.config import Config, COOKIE_FILE
from app.services.scheduler import check_task_status, get_task_result, update_task_progress
# 导入数据模型 
from app.schemas.monitor import (
    LoginRequest, LoginResponse, 
    ConfigRequest, ConfigResponse,
    BleedMonitorRequest, OxygenMonitorRequest, 
    TaskResponse, TaskStatus, TaskResult
)
from app.api.ames import login_ames
from app.services.bleed_monitor import run_monitoring as run_bleed_monitoring

# 配置路由
router = APIRouter()

# 配置日志
logger = logging.getLogger("phm_system.api.local")

# 用于存储用户会话和任务状态的字典
user_sessions = {}
monitoring_tasks = {}

# 工具函数：验证会话
def verify_session(session_id: str = Header(...)):
    """验证用户会话是否有效
    
    参数:
        session_id: 会话ID
    
    返回值:
        用户会话信息
    
    异常:
        HTTPException: 如果会话无效或已过期
    """
    if session_id not in user_sessions:
        raise HTTPException(
            status_code=401,
            detail="未登录或会话已过期"
        )
    
    return user_sessions[session_id]

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """登录接口"""
    try:
        username = request.username
        password = request.password
        
        if not username or not password:
            return {"success": False, "message": "用户名和密码不能为空"}
        
        # 使用用户特定的配置
        user_config = Config(username)
        # 保存登录信息
        user_config.set_login_info(username, password)
        
        # 尝试登录并获取Cookie
        login_result = await login_ames(request)
        
        if login_result["success"]:
            # 生成唯一会话ID
            session_id = secrets.token_hex(16)
            user_sessions[session_id] = {
                'username': username,
                'cookies': login_result["cookies"],
                'timestamp': datetime.now().isoformat()
            }
            
            return {
                "success": True, 
                "message": "登录成功", 
                "data": {"sessionId": session_id}
            }
        else:
            return {"success": False, "message": login_result["message"]}
    
    except Exception as e:
        logger.error(f"登录过程出错: {str(e)}")
        return {"success": False, "message": f"登录过程出错: {str(e)}"}

@router.get("/config", response_model=ConfigResponse)
async def get_user_config(session: Dict[str, Any] = Depends(verify_session)):
    """获取用户配置"""
    try:
        # 获取当前登录用户
        username = session['username']
        # 创建用户特定的配置对象
        user_config = Config(username)
        
        # 获取配置
        cfm_threshold = user_config.get_cfm_threshold()
        v2500_threshold = user_config.get_v2500_threshold()
        employees = user_config.get_employees()
        
        # 获取引气监控的邮箱和自动运行设置
        bleed_email = user_config.get_bleed_email_recipients()
        bleed_auto_enabled, bleed_auto_hour, bleed_auto_minute, bleed_auto_date_range = user_config.get_bleed_auto_settings()
        
        # 获取氧气监控配置
        last_aircraft = user_config.get_last_oxygen_aircraft()
        days_range = user_config.get_oxygen_days_range()
        psi1_threshold, psi2_threshold = user_config.get_oxygen_thresholds()
        
        # 获取氧气监控员工号和邮箱
        oxygen_employees = user_config.get_oxygen_employees()
        oxygen_email = user_config.get_oxygen_email_recipients() 
        
        # 氧气自动监控功能已移除，使用硬编码默认值
        oxygen_auto_enabled = False
        oxygen_auto_hour = "08"
        oxygen_auto_minute = "00" 
        oxygen_auto_date_range = "最近三天"
        
        return {
            "success": True,
            "data": {
                "bleedSettings": {
                    "cfmThreshold": cfm_threshold,
                    "v2500Threshold": v2500_threshold,
                    "employees": employees,
                    "emailRecipients": bleed_email,
                    "autoRun": {
                        "enabled": bleed_auto_enabled,
                        "hour": bleed_auto_hour,
                        "minute": bleed_auto_minute,
                        "dateRange": bleed_auto_date_range
                    }
                },
                "oxygenSettings": {
                    "lastAircraft": last_aircraft,
                    "daysRange": days_range,
                    "psi1Threshold": psi1_threshold,
                    "psi2Threshold": psi2_threshold,
                    "employees": oxygen_employees,
                    "emailRecipients": oxygen_email,
                    "autoRun": {
                        "enabled": oxygen_auto_enabled,
                        "hour": oxygen_auto_hour,
                        "minute": oxygen_auto_minute,
                        "dateRange": oxygen_auto_date_range
                    }
                }
            }
        }
    
    except Exception as e:
        logger.error(f"获取用户配置时出错: {str(e)}")
        return {"success": False, "message": f"获取用户配置时出错: {str(e)}"}

@router.post("/config", response_model=ConfigResponse)
async def save_user_config(request: ConfigRequest, session: Dict[str, Any] = Depends(verify_session)):
    """保存用户配置"""
    try:
        # 获取当前登录用户
        username = session['username']
        # 创建用户特定的配置对象
        user_config = Config(username)
        
        # 保存引气监控设置
        if request.bleedSettings:
            bleed = request.bleedSettings
            user_config.set_bleed_settings(
                str(bleed.get('cfmThreshold', '38')), 
                str(bleed.get('v2500Threshold', '38')), 
                bleed.get('employees', '')
            )
            
            # 保存引气监控的邮箱设置
            if 'emailRecipients' in bleed:
                user_config.set_bleed_email_recipients(bleed['emailRecipients'])
            
            # 保存引气监控的自动运行设置
            if 'autoRun' in bleed:
                auto = bleed['autoRun']
                date_range = auto.get('dateRange', '三个月')
                enabled = auto.get('enabled', True)
                hour = str(auto.get('hour', '08'))
                minute = str(auto.get('minute', '00'))
                
                # 保存配置
                user_config.set_bleed_auto_settings(
                    enabled,
                    hour,
                    minute,
                    date_range
                )
                
                # 在配置保存后，重新设置调度任务
                password = user_config.get_login_info()[1]
                
                # 导入需要的函数
                from app.utils.scheduler_utils import remove_job
                from app.services.scheduler import setup_bleed_monitor_job
                
                # 获取任务ID
                cfm_job_id = f"bleed_auto_{username}_CFM"
                v2500_job_id = f"bleed_auto_{username}_V2500"
                
                # 如果禁用了自动运行，则移除现有任务
                if not enabled:
                    logger.info(f"用户 {username} 禁用了自动引气监控，正在移除调度任务")
                    remove_job(cfm_job_id)
                    remove_job(v2500_job_id)
                    logger.info(f"已成功移除用户 {username} 的引气监控调度任务")
                else:
                    # 重新设置CFM引气监控任务
                    logger.info(f"用户 {username} 更新了引气监控配置，正在重新设置调度任务")
                    cfm_result = setup_bleed_monitor_job(
                        username=username,
                        password=password,
                        aircraft_type="CFM",
                        aircraft_no="全部",
                        threshold_value=float(user_config.get_cfm_threshold()),
                        employees=user_config.get_employees(),
                        email_recipients=user_config.get_bleed_email_recipients(),
                        hour=hour,
                        minute=minute
                    )
                    
                    # 重新设置V2500引气监控任务
                    v2500_result = setup_bleed_monitor_job(
                        username=username,
                        password=password,
                        aircraft_type="V2500",
                        aircraft_no="全部",
                        threshold_value=float(user_config.get_v2500_threshold()),
                        employees=user_config.get_employees(),
                        email_recipients=user_config.get_bleed_email_recipients(),
                        hour=hour,
                        minute=minute
                    )
                    
                    logger.info(f"已成功更新用户 {username} 的引气监控调度任务: CFM({cfm_result}), V2500({v2500_result})")
        
        # 保存氧气监控设置
        if request.oxygenSettings:
            oxygen = request.oxygenSettings
            user_config.set_oxygen_thresholds(
                str(oxygen.get('psi1Threshold', '50')), 
                str(oxygen.get('psi2Threshold', '50'))
            )
            
            if 'lastAircraft' in oxygen:
                user_config.set_last_oxygen_aircraft(oxygen['lastAircraft'])
                
            if 'daysRange' in oxygen:
                user_config.set_oxygen_days_range(str(oxygen['daysRange']))
            
            # 保存氧气监控的邮箱设置
            if 'emailRecipients' in oxygen:
                user_config.set_oxygen_email_recipients(oxygen['emailRecipients'])
                
            # 保存氧气监控的员工号设置
            if 'employees' in oxygen:
                user_config.set_oxygen_employees(oxygen['employees'])
        
        return {"success": True, "message": "配置已保存"}
    
    except Exception as e:
        logger.error(f"保存用户配置时出错: {str(e)}")
        return {"success": False, "message": f"保存用户配置时出错: {str(e)}"}

@router.post("/bleed-monitor", response_model=TaskResponse)
async def start_bleed_monitor(request: BleedMonitorRequest, session: Dict[str, Any] = Depends(verify_session)):
    """执行引气监控"""
    try:
        # 获取当前用户的cookies
        cookies = session['cookies']
        username = session['username']
        
        # 创建任务ID
        task_id = f"bleed_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        
        # 初始化任务状态
        monitoring_tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'message': '开始监控任务...',
            'results': None,
            'timestamp': datetime.now().isoformat(),
            'username': username
        }
        
        # 启动监控线程
        import threading
        thread = threading.Thread(
            target=run_bleed_monitoring_thread,
            args=(
                task_id, 
                cookies, 
                request.aircraftType, 
                request.aircraftNo, 
                request.startDate, 
                request.endDate, 
                float(request.thresholdValue), 
                request.employees,
                request.emailRecipients,
                username
            )
        )
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "message": "引气监控任务已启动",
            "data": {"taskId": task_id}
        }
    
    except Exception as e:
        logger.error(f"启动引气监控任务时出错: {str(e)}")
        return {"success": False, "message": f"启动引气监控任务时出错: {str(e)}"}

@router.post("/oxygen-monitor", response_model=TaskResponse)
async def start_oxygen_monitor(request: OxygenMonitorRequest, session: Dict[str, Any] = Depends(verify_session)):
    """执行氧气监控"""
    try:
        # 获取当前用户的cookies
        cookies = session['cookies']
        username = session['username']
        
        # 创建任务ID
        task_id = f"oxygen_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        
        # 初始化任务状态
        monitoring_tasks[task_id] = {
            'status': 'starting',
            'progress': 0,
            'message': '开始氧气监控任务...',
            'results': None,
            'timestamp': datetime.now().isoformat(),
            'username': username
        }
        
        # 启动监控线程
        import threading
        thread = threading.Thread(
            target=run_oxygen_monitoring_thread,
            args=(
                task_id, 
                cookies, 
                request.aircraft, 
                request.startDate,
                request.endDate,
                float(request.psi1Threshold), 
                float(request.psi2Threshold), 
                request.employees,
                request.emailRecipients,
                username
            )
        )
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "message": "氧气监控任务已启动",
            "data": {"taskId": task_id}
        }
    
    except Exception as e:
        logger.error(f"启动氧气监控任务时出错: {str(e)}")
        return {"success": False, "message": f"启动氧气监控任务时出错: {str(e)}"}

@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status_api(task_id: str, session: Dict[str, Any] = Depends(verify_session)):
    """获取任务状态"""
    try:
        logger.info(f"正在获取任务状态: {task_id}")
        
        # 检查任务ID是否有效
        if not task_id:
            logger.warning("请求的任务ID为空")
            return {"success": False, "message": "无效的任务ID"}
            
        # 检查任务是否存在
        if task_id not in monitoring_tasks:
            logger.warning(f"任务不存在: {task_id}")
            return {"success": False, "message": "任务不存在"}
        
        # 获取任务数据，使用深拷贝避免线程安全问题
        import copy
        task = copy.deepcopy(monitoring_tasks.get(task_id, {}))
        
        # 记录任务状态
        logger.info(f"任务 {task_id} 当前状态: {task.get('status', 'unknown')}, 进度: {task.get('progress', 0)}%")
        
        # 检查任务数据是否有效
        if not task:
            logger.warning(f"任务数据无效: {task_id}")
            return {"success": False, "message": "任务数据无效"}
        
        # 检查任务是否属于当前用户
        current_username = session.get('username')
        if not current_username:
            logger.warning("用户会话无效")
            return {"success": False, "message": "用户会话无效"}
            
        task_username = task.get('username')
        
        # 如果任务有关联用户，确保当前用户有权限查看
        if task_username and task_username != current_username:
            logger.warning(f"用户 {current_username} 无权查看任务 {task_id} (属于 {task_username})")
            return {"success": False, "message": "无权查看该任务"}
        
        # 确保任务包含所需的基本字段
        if 'status' not in task:
            task['status'] = 'unknown'
        if 'progress' not in task:
            task['progress'] = 0
        if 'message' not in task:
            task['message'] = '未知状态'
        if 'timestamp' not in task:
            task['timestamp'] = datetime.now().isoformat()
        
        # 返回基本的任务状态信息 - 注意这里添加了message字段
        return {
            "success": True,
            "message": "获取任务状态成功",  # 添加这一行
            "data": {
                "status": task['status'],
                "progress": task['progress'],
                "message": task['message'],
                "timestamp": task['timestamp']
            }
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"获取任务状态时出错: {str(e)}\n{error_details}")
        return {"success": False, "message": f"获取任务状态时出错: {str(e)}"}
    
@router.get("/task/{task_id}/result", response_model=TaskResponse)
async def get_task_result_api(task_id: str, session: Dict[str, Any] = Depends(verify_session)):
    """获取任务完整结果"""
    try:
        logger.info(f"正在获取任务结果: {task_id}")
        
        # 检查任务ID是否有效
        if not task_id:
            logger.warning("请求的任务ID为空")
            return {"success": False, "message": "无效的任务ID"}
            
        # 检查任务是否存在
        if task_id not in monitoring_tasks:
            logger.warning(f"任务不存在: {task_id}")
            return {"success": False, "message": "任务不存在"}
        
        # 获取任务数据，使用深拷贝避免线程安全问题
        import copy
        task = copy.deepcopy(monitoring_tasks.get(task_id, {}))
        
        # 检查任务数据是否有效
        if not task:
            logger.warning(f"任务数据无效: {task_id}")
            return {"success": False, "message": "任务数据无效"}
        
        # 检查任务是否属于当前用户
        current_username = session.get('username')
        if not current_username:
            logger.warning("用户会话无效")
            return {"success": False, "message": "用户会话无效"}
            
        task_username = task.get('username')
        
        # 如果任务有关联用户，确保当前用户有权限查看
        if task_username and task_username != current_username:
            logger.warning(f"用户 {current_username} 无权查看任务 {task_id} (属于 {task_username})")
            return {"success": False, "message": "无权查看该任务"}
        
        # 检查任务状态
        if task.get('status') != 'completed':
            logger.warning(f"任务 {task_id} 尚未完成，当前状态: {task.get('status')}")
            return {"success": False, "message": "任务尚未完成"}
        
        # 确保结果字段存在
        if 'results' not in task:
            logger.warning(f"任务 {task_id} 没有结果字段")
            return {"success": False, "message": "任务没有结果数据"}
        
        # 返回简化的结果数据 - 注意这里添加了message字段
        return {
            "success": True,
            "message": "获取任务结果成功",  # 添加这一行
            "data": {
                "results": task['results'],
                "threshold": task.get('threshold'),
                "taskType": "bleed" if task_id.startswith("bleed") else "oxygen"
            }
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"获取任务结果时出错: {str(e)}\n{error_details}")
        return {"success": False, "message": f"获取任务结果时出错: {str(e)}"}

# 后台任务执行函数
def run_bleed_monitoring_thread(task_id: str, cookies: Dict[str, str], aircraft_type: str, aircraft_no: str, 
                             start_date: str, end_date: str, threshold_value: float, employees: str,
                             email_recipients: str = '', username: str = None):
    """后台执行引气监控任务"""
    try:
        # 更新任务状态
        monitoring_tasks[task_id]['status'] = 'running'
        monitoring_tasks[task_id]['message'] = f'正在监控 {aircraft_type} {aircraft_no}...'
        monitoring_tasks[task_id]['threshold'] = threshold_value
        
        # 创建一个新的事件循环
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 执行监控任务
        try:
            results, detailed_info = loop.run_until_complete(run_bleed_monitoring(
                cookies=cookies,
                aircraft_type=aircraft_type,
                aircraft_no=aircraft_no,
                start_date=start_date,
                end_date=end_date,
                threshold_value=threshold_value,
                employees=employees,
                update_progress=lambda progress, message: update_task_progress(task_id, progress, message),
                username=username
            ))
            
            # 更新任务状态为完成
            monitoring_tasks[task_id]['status'] = 'completed'
            monitoring_tasks[task_id]['progress'] = 100
            monitoring_tasks[task_id]['message'] = '分析任务已完成'
            monitoring_tasks[task_id]['results'] = results
            monitoring_tasks[task_id]['timestamp'] = datetime.now().isoformat()
        
        finally:
            # 关闭事件循环
            loop.close()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in monitoring task: {str(e)}\n{error_details}")
        
        # 更新任务状态为错误
        monitoring_tasks[task_id]['status'] = 'error'
        monitoring_tasks[task_id]['message'] = f'错误: {str(e)}'
        monitoring_tasks[task_id]['timestamp'] = datetime.now().isoformat()

# 后台执行氧气监控任务
def run_oxygen_monitoring_thread(task_id: str, cookies: Dict[str, str], aircraft: str, 
                               start_date: str, end_date: str, psi1_threshold: float, psi2_threshold: float, 
                               employees: str, email_recipients: str = '', username: str = None):
    """后台执行氧气监控任务
    
    参数:
        task_id: 任务ID
        cookies: Cookie
        aircraft: 飞机号
        start_date: 开始日期
        end_date: 结束日期
        psi1_threshold: PSI1压力下降阈值
        psi2_threshold: PSI2压力下降阈值
        employees: 接收通知的员工号
        email_recipients: 接收邮件的邮箱地址
        username: 用户名，用于自动登录和发送邮件
    """
    try:
        # 更新任务状态
        monitoring_tasks[task_id]['status'] = 'running'
        monitoring_tasks[task_id]['message'] = f'正在监控飞机 {aircraft} 的氧气系统...'
        
        # 从用户配置中获取员工号（如果请求中未提供）
        if not employees and username:
            try:
                from app.utils.config import Config
                user_config = Config(username)
                config_employees = user_config.get_oxygen_employees()
                if config_employees:
                    employees = config_employees
                    logger.info(f"从用户配置中读取氧气监控员工号: {employees}")
            except Exception as e:
                logger.warning(f"从配置中获取氧气监控员工号失败: {str(e)}")
        
        # 创建一个新的事件循环
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 执行监控任务
        try:
            # 导入氧气监控服务
            from app.services.OxygenMonitor import run_monitoring
            
            logger.info(f"开始执行氧气监控，飞机:{aircraft}, 员工号:{employees}, 邮箱:{email_recipients}")
            results, warnings = loop.run_until_complete(run_monitoring(
                cookies=cookies,
                aircraft=aircraft,
                start_date=start_date,
                end_date=end_date,
                psi1_threshold=psi1_threshold,
                psi2_threshold=psi2_threshold,
                employees=employees,
                update_progress=lambda progress, message: update_task_progress(task_id, progress, message),
                username=username
            ))
            
            # 更新任务状态为完成
            monitoring_tasks[task_id]['status'] = 'completed'
            monitoring_tasks[task_id]['progress'] = 100
            monitoring_tasks[task_id]['message'] = '氧气监控分析任务已完成'
            monitoring_tasks[task_id]['results'] = results
            monitoring_tasks[task_id]['timestamp'] = datetime.now().isoformat()
            
        finally:
            # 关闭事件循环
            loop.close()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in oxygen monitoring task: {str(e)}\n{error_details}")
        
        # 更新任务状态为错误
        monitoring_tasks[task_id]['status'] = 'error'
        monitoring_tasks[task_id]['message'] = f'错误: {str(e)}'
        monitoring_tasks[task_id]['timestamp'] = datetime.now().isoformat()