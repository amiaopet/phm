#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: monitor.py
# 描述: 监控功能数据模型

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 用户登录请求模型
class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

# 用户登录响应模型
class LoginResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")

# 用户配置请求模型
class ConfigRequest(BaseModel):
    bleedSettings: Optional[Dict[str, Any]] = Field(None, description="引气监控设置")
    oxygenSettings: Optional[Dict[str, Any]] = Field(None, description="氧气监控设置")

# 用户配置响应模型
class ConfigResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="消息")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")

# 引气监控请求模型
class BleedMonitorRequest(BaseModel):
    aircraftType: str = Field(..., description="飞机类型")
    aircraftNo: str = Field(..., description="飞机号")
    startDate: str = Field(..., description="开始日期")
    endDate: str = Field(..., description="结束日期")
    thresholdValue: float = Field(..., description="阈值")
    employees: str = Field("", description="接收通知的员工号")
    emailRecipients: Optional[str] = Field("", description="接收邮件的邮箱地址")
    autoRun: Optional[Dict[str, Any]] = Field(None, description="自动运行设置")

# 氧气监控请求模型
class OxygenMonitorRequest(BaseModel):
    aircraft: str = Field(..., description="飞机号")
    startDate: str = Field(..., description="开始日期")
    endDate: str = Field(..., description="结束日期")
    psi1Threshold: float = Field(..., description="PSI1阈值")
    psi2Threshold: float = Field(..., description="PSI2阈值")
    employees: str = Field("", description="接收通知的员工号")
    emailRecipients: Optional[str] = Field("", description="接收邮件的邮箱地址")

# 任务响应模型
class TaskResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")

# 任务状态模型
class TaskStatus(BaseModel):
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    message: str = Field(..., description="状态消息")
    timestamp: str = Field(..., description="时间戳")
    resultSummary: Optional[Dict[str, Any]] = Field(None, description="结果摘要")

# 任务结果模型
class TaskResult(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="结果数据")
    threshold: Optional[float] = Field(None, description="阈值")
    taskType: str = Field(..., description="任务类型")