#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: main.py
# 描述: 应用主入口

import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from datetime import datetime, timedelta
from app.api.utils import mod_router
from app.utils.init_app import init_application

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("phm_system")

# 创建FastAPI应用
app = FastAPI(
    title="飞机健康监控系统",
    description="用于监控和分析飞机状态的系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在实际生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入各模块路由
from app.api import local, ames, scheduler, mail, yht, utils, aircraft

# 导入初始化函数
from app.utils.init_app import init_application

# 注册路由
app.include_router(local.router, prefix="/api", tags=["本地接口"])
app.include_router(ames.router, prefix="/api/ames", tags=["AMES接口"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["定时任务接口"])
app.include_router(mail.router, prefix="/api/mail", tags=["邮件接口"])
app.include_router(yht.router, prefix="/api/yht", tags=["远航通接口"])
app.include_router(utils.router, prefix="/api", tags=["通用工具接口"])
app.include_router(aircraft.router, prefix="/api", tags=["飞机信息接口"])
app.include_router(mod_router, prefix="/api", tags=["A320MOD查询"])

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    # 确保必要的目录存在
    os.makedirs("configs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 初始化应用，包括启动调度器和设置定时任务
    init_application()
    
    logger.info("应用已启动并初始化完成")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作"""
    # 关闭调度器
    from app.utils.scheduler_utils import shutdown_scheduler
    shutdown_scheduler()
    
    logger.info("应用已关闭")

# 挂载静态文件（前端构建后的文件）
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"前端静态文件已挂载，路径: {frontend_dir}")
else:
    logger.warning(f"前端目录不存在: {frontend_dir}，静态文件未挂载")

@app.get("/api/health")
async def health_check():
    """API健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 主程序入口
if __name__ == "__main__":
    # 启动应用服务器
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5010,
        reload=True,
        log_level="info"
    )