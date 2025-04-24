#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: FaultDiagnosis.py
# 描述: 故障分析诊断功能数据模型

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础故障模型
class Fault(BaseModel):
    id: Optional[str] = Field(None, description="故障ID")
    aircraft: str = Field(..., description="飞机号")
    date: str = Field(..., description="日期")
    faultCode: str = Field(..., description="故障代码")
    description: str = Field(..., description="故障描述")
    status: str = Field(..., description="状态")
    priority: str = Field(..., description="优先级")

# 氧气压力数据模型
class OxygenPressureData(BaseModel):
    aircraft: str = Field(..., description="飞机号")
    date: str = Field(..., description="日期")
    flight_no: str = Field(..., description="航班号")
    takeoff_time: str = Field(..., description="起飞时间")
    step: str = Field(..., description="阶段")
    psi1: Optional[str] = Field(None, description="PSI1值")
    psi2: Optional[str] = Field(None, description="PSI2值")
    psi1_drop: float = Field(0, description="PSI1下降值")
    psi2_drop: float = Field(0, description="PSI2下降值")
    status: str = Field("正常", description="状态")

# 引气压力数据模型
class BleedAirData(BaseModel):
    acno: str = Field(..., description="飞机号")
    t1_avg: float = Field(..., description="T1平均值")
    t2_avg: float = Field(..., description="T2平均值")
    max_flights: List[Dict[str, Any]] = Field(..., description="最大值航班")
    all_flights: List[Dict[str, Any]] = Field(..., description="所有航班数据")
    threshold: float = Field(..., description="阈值")