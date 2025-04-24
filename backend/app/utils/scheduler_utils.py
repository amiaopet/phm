#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: scheduler_utils.py
# 描述: 定时任务工具函数

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, List
from fastapi import FastAPI

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# 配置日志
logger = logging.getLogger("phm_system.scheduler")

# 全局调度器
scheduler = BackgroundScheduler()

def init_scheduler():
    """初始化调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("后台调度器已启动")

def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("后台调度器已关闭")

def add_cron_job(job_id: str, func: Callable, hour: str, minute: str, 
                 second: str = '0', args: Optional[tuple] = None, 
                 kwargs: Optional[Dict[str, Any]] = None) -> bool:
    """添加定时任务
    
    参数:
        job_id: 任务ID
        func: 要执行的函数
        hour: 小时 (0-23)
        minute: 分钟 (0-59)
        second: 秒 (0-59)
        args: 函数参数
        kwargs: 函数关键字参数
    
    返回值:
        布尔值表示是否成功添加任务
    """
    try:
        if not scheduler.running:
            init_scheduler()
        
        # 如果任务已存在，先移除
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        # 检查func是否是协程函数，如果是则创建一个包装函数
        import asyncio
        import inspect
        
        if inspect.iscoroutinefunction(func):
            # 创建一个非协程的包装函数来运行协程
            def async_wrapper(*a, **kw):
                # 创建一个新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 在事件循环中运行协程函数
                    result = loop.run_until_complete(func(*a, **kw))
                    return result
                finally:
                    loop.close()
            
            # 使用包装函数替代原函数
            scheduler_func = async_wrapper
        else:
            # 如果不是协程函数，直接使用
            scheduler_func = func
        
        # 添加定时任务
        scheduler.add_job(
            func=scheduler_func,
            trigger=CronTrigger(hour=hour, minute=minute, second=second),
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True
        )
        
        logger.info(f"添加定时任务成功: {job_id}, 执行时间: {hour}:{minute}:{second}")
        return True
    except Exception as e:
        logger.error(f"添加定时任务失败: {job_id}, 错误: {str(e)}")
        return False

def remove_job(job_id: str) -> bool:
    """移除定时任务
    
    参数:
        job_id: 任务ID
    
    返回值:
        布尔值表示是否成功移除任务
    """
    try:
        if scheduler.running and scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"移除定时任务成功: {job_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"移除定时任务失败: {job_id}, 错误: {str(e)}")
        return False

def get_job_status(job_id: str) -> Dict[str, Any]:
    """获取定时任务状态
    
    参数:
        job_id: 任务ID
    
    返回值:
        任务状态信息
    """
    job = scheduler.get_job(job_id) if scheduler.running else None
    
    if job:
        return {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "active": job.next_run_time is not None
        }
    
    return {
        "id": job_id,
        "next_run_time": None,
        "active": False
    }

def get_all_jobs() -> Dict[str, Dict[str, Any]]:
    """获取所有定时任务
    
    返回值:
        所有任务的状态信息
    """
    jobs = {}
    
    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs[job.id] = {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "active": job.next_run_time is not None
            }
    
    return jobs

def init_auto_tasks():
    """初始化所有用户的自动监控任务"""
    logger.info("开始初始化自动监控任务...")
    
    try:
        # 确保调度器已启动
        init_scheduler()
        
        # 导入配置
        from app.utils.config import CONFIG_DIR, Config
        
        # 导入调度函数
        from app.services.scheduler import setup_bleed_monitor_job
        
        # 获取配置目录下的所有用户目录
        user_dirs = [d for d in os.listdir(CONFIG_DIR) if os.path.isdir(os.path.join(CONFIG_DIR, d))]
        logger.info(f"找到 {len(user_dirs)} 个用户配置目录")
        
        # 记录初始化的任务数量
        bleed_jobs_count = 0
        
        # 遍历每个用户配置
        for username in user_dirs:
            try:
                user_config = Config(username)
                
                # 获取登录信息
                login_username, login_password = user_config.get_login_info()
                
                if not login_username or not login_password:
                    logger.warning(f"用户 {username} 未配置有效的登录信息，跳过")
                    continue
                
                # 初始化引气监控任务
                bleed_auto_enabled, bleed_auto_hour, bleed_auto_minute, bleed_auto_date_range = user_config.get_bleed_auto_settings()
                
                if bleed_auto_enabled:
                    # 获取CFM配置
                    cfm_threshold = user_config.get_cfm_threshold()
                    # 获取员工号和邮箱配置
                    employees = user_config.get_employees()
                    email_recipients = user_config.get_bleed_email_recipients()
                    
                    # 设置CFM引气监控任务
                    cfm_job_id = setup_bleed_monitor_job(
                        username=login_username,
                        password=login_password,
                        aircraft_type="CFM",
                        aircraft_no="全部",
                        threshold_value=float(cfm_threshold),
                        employees=employees,
                        email_recipients=email_recipients,
                        hour=bleed_auto_hour,
                        minute=bleed_auto_minute
                    )
                    
                    # 获取V2500配置
                    v2500_threshold = user_config.get_v2500_threshold()
                    
                    # 设置V2500引气监控任务
                    v2500_job_id = setup_bleed_monitor_job(
                        username=login_username,
                        password=login_password,
                        aircraft_type="V2500",
                        aircraft_no="全部",
                        threshold_value=float(v2500_threshold),
                        employees=employees,
                        email_recipients=email_recipients,
                        hour=bleed_auto_hour,
                        minute=bleed_auto_minute
                    )
                    
                    bleed_jobs_count += 2
                    logger.info(f"用户 {username} 的引气监控任务已设置: CFM({cfm_job_id}), V2500({v2500_job_id})")
            
            except Exception as e:
                logger.error(f"初始化用户 {username} 的自动任务时出错: {str(e)}")
        
        # 输出初始化结果
        logger.info(f"自动任务初始化完成，共设置 {bleed_jobs_count} 个引气监控任务")
        
        # 显示当前所有任务状态
        all_jobs = get_all_jobs()
        logger.info(f"当前所有调度任务: {json.dumps(all_jobs, indent=2)}")
        
        return True
    
    except Exception as e:
        logger.error(f"初始化自动任务时出错: {str(e)}")
        return False

def init_app(app: FastAPI):
    """初始化应用"""
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行"""
        try:
            logger.info("应用启动，正在初始化...")
            
            # 初始化调度器
            init_scheduler()
            logger.info("调度器已初始化")
            
            # 延迟1秒以确保应用其他部分已初始化
            await asyncio.sleep(1)
            
            # 初始化自动任务
            init_auto_tasks()
            logger.info("自动任务已初始化")
            
        except Exception as e:
            logger.error(f"应用初始化时出错: {str(e)}")
    
    @app.on_event("shutdown")
    def shutdown_event():
        """应用关闭时执行"""
        try:
            logger.info("应用关闭，正在清理资源...")
            
            # 关闭调度器
            shutdown_scheduler()
            logger.info("调度器已关闭")
            
        except Exception as e:
            logger.error(f"应用关闭清理时出错: {str(e)}")