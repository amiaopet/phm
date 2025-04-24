#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: aircraft.py
# 描述: 飞机详情API接口

from fastapi import APIRouter, Header
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
import random
import requests
import httpx
import asyncio

# 配置路由
router = APIRouter(prefix="/aircraft", tags=["飞机信息"])

# 配置日志
logger = logging.getLogger("phm_system.api.aircraft")

# AMES 相关常量
AMES_BASE_URL = "https://ames.juneyaoair.com"
ACREG_LIST_API_URL = f"{AMES_BASE_URL}/api/v1/plugins/DA_ACREG_LIST"

# 飞机状态映射
aircraft_status_map = {
    "1": "运行中",
    "2": "待引进",
    "4": "已退出",
    "": "未知"
}

# 机场代码
airports = ["PVG", "PEK", "CAN", "CTU", "XIY", "SHA", "SZX", "KMG", "HGH", "CKG"]

@router.get("/detail/{ac_reg}")
async def get_aircraft_detail(ac_reg: str, session_id: Optional[str] = Header(None, alias="Session-Id")):
    """获取飞机详细信息
    
    参数:
        ac_reg: 飞机注册号
        session_id: 会话ID
    
    返回:
        飞机详细信息
    """
    try:
        # 加载会话cookies
        cookies = None
        if session_id:
            # 从本地导入用户会话
            try:
                from app.api.local import user_sessions
                if session_id in user_sessions:
                    cookies = user_sessions[session_id].get('cookies', {})
            except ImportError:
                logger.warning("无法导入用户会话模块")
        
        # 从AMES接口获取飞机信息
        aircraft_data = await fetch_aircraft_from_ames(ac_reg, cookies)
        
        if aircraft_data:
            # 格式化飞机数据
            formatted_data = format_aircraft_data(aircraft_data)
            return {
                "success": True,
                "data": formatted_data
            }
        else:
            # 未找到飞机信息
            return {
                "success": False,
                "message": f"未找到飞机 {ac_reg} 的信息"
            }
    except Exception as e:
        logger.error(f"获取飞机详情出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取飞机详情失败: {str(e)}"
        }

async def fetch_aircraft_from_ames(ac_reg: str, cookies: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """从AMES接口获取飞机信息
    
    参数:
        ac_reg: 飞机注册号
        cookies: 会话cookie
    
    返回:
        飞机信息字典或None
    """
    try:
        # 准备请求头
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': AMES_BASE_URL,
            'Referer': f"{AMES_BASE_URL}/views/daAcreg/pm_daacreg_list.shtml",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # 如果没有提供cookies，使用通用cookies
        if not cookies:
            cookies = {
                '_udid': 'ca55384ddd78475cbacf8c840bfeff95',
                'i18next': 'zh',
                'JSESSIONID': '1CCACF248A5E943F3360CFEE82D511F2',
                'sfFilter': '8abcad82db547adb6986544becc954cd',
                '_amro_sk': 'c81cbcff-d115-402e-bc61-f5299d01b63e'
            }
        
        # 准备表单数据
        data = {
            'page': '1',
            'rows': '200'  # 请求足够多的记录以找到特定飞机
        }
        
        # 发送GET请求
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                ACREG_LIST_API_URL, 
                headers=headers, 
                cookies=cookies, 
                data=data
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                
                # 检查API返回码
                if result.get('code') == 200:
                    aircraft_list = result.get('data', [])
                    
                    # 查找匹配的飞机
                    for aircraft in aircraft_list:
                        if aircraft.get('ACNO') == ac_reg:
                            return aircraft
                    
                    # 如果没有找到完全匹配，尝试查找包含该注册号的飞机
                    for aircraft in aircraft_list:
                        if ac_reg in aircraft.get('ACNO', ''):
                            return aircraft
                    
                    # 如果仍然没有找到，记录信息
                    logger.warning(f"从AMES未找到飞机: {ac_reg}")
                    return None
                else:
                    logger.error(f"AMES API错误: {result.get('msg', '')}")
                    return None
            else:
                logger.error(f"请求AMES失败, 状态码: {response.status_code}")
                return None
    
    except Exception as e:
        logger.error(f"从AMES获取飞机信息时出错: {str(e)}")
        return None

def format_aircraft_data(aircraft_data: Dict[str, Any]) -> Dict[str, Any]:
    """格式化从AMES获取的飞机数据
    
    参数:
        aircraft_data: 从AMES获取的原始飞机数据
    
    返回:
        格式化后的飞机数据
    """
    # 提取状态并获取对应的文字描述
    status_code = aircraft_data.get('VALID_STATUS', '')
    status = aircraft_status_map.get(status_code, '未知')
    
    # 格式化日期（如果有）
    first_fly_date = aircraft_data.get('FIRST_FLY_DATE001', '')
    deliver_date = aircraft_data.get('DELIVER_DATE', '')
    if deliver_date and len(deliver_date) > 10:
        deliver_date = deliver_date[:10]  # 只保留日期部分
    
    # 构建格式化后的数据
    return {
        "aircraft_type": aircraft_data.get('CONF_ACTYPE', ''),
        "msn": aircraft_data.get('MSN', ''),
        "wv": aircraft_data.get('WV1', ''),
        "seat_layout": aircraft_data.get('ZZWBJ', ''),
        "status": status,
        "first_fly_date": first_fly_date,
        "deliver_date": deliver_date,
        "max_weight_landing": aircraft_data.get('MAX_WEIGHT_LANDING', ''),
        "max_weight_takeoff": aircraft_data.get('MAX_WEIGHT_TAKEOFF', ''),
        "max_weight_oilless": aircraft_data.get('MAX_WEIGHT_OILLESS', ''),
        "engine_type": aircraft_data.get('ZTRU_LV', ''),
        "left_engine_sn": aircraft_data.get('LESN', ''),
        "right_engine_sn": aircraft_data.get('RESN', ''),
        "apu_type": aircraft_data.get('APU_TYPE', ''),
        "apu_sn": aircraft_data.get('ASN', ''),
        "fsn": aircraft_data.get('IPC_NO', '')
    }

@router.get("/recent-flights/{ac_reg}")
async def get_recent_flights(
    ac_reg: str, 
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_all: bool = False,
    session_id: Optional[str] = Header(None, alias="Session-Id")
):
    """获取飞机近期航班记录
    
    参数:
        ac_reg: 飞机注册号
        limit: 返回记录数量限制
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        include_all: 是否包含所有符合条件的航班
        session_id: 会话ID
    
    返回:
        近期航班记录列表
    """
    try:
        # 处理日期范围
        today = datetime.now()
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "message": "开始日期格式错误，应为YYYY-MM-DD"
                }
        else:
            # 默认为今天往前10天
            start_date_obj = today - timedelta(days=10)
            
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "message": "结束日期格式错误，应为YYYY-MM-DD"
                }
        else:
            # 默认为今天
            end_date_obj = today
            
        # 确保end_date不早于start_date
        if end_date_obj < start_date_obj:
            return {
                "success": False,
                "message": "结束日期不能早于开始日期"
            }
        
        # 获取用户会话cookies
        cookies = None
        if session_id:
            try:
                from app.api.local import user_sessions
                if session_id in user_sessions:
                    cookies = user_sessions[session_id].get('cookies', {})
            except ImportError:
                logger.warning("无法导入用户会话模块")
        
        # 如果没有cookies，尝试从本地加载通用cookies
        if not cookies:
            try:
                from app.api.ames import load_cookies
                cookies = load_cookies()
            except (ImportError, Exception) as e:
                logger.warning(f"无法加载cookies: {str(e)}")
                
            # 如果仍然没有cookies，使用默认cookies
            if not cookies:
                cookies = {
                    '_udid': 'ca55384ddd78475cbacf8c840bfeff95',
                    'i18next': 'zh',
                    'JSESSIONID': '1CCACF248A5E943F3360CFEE82D511F2',
                    'sfFilter': '8abcad82db547adb6986544becc954cd',
                    '_amro_sk': 'c81cbcff-d115-402e-bc61-f5299d01b63e'
                }
        
        # 准备请求头
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': AMES_BASE_URL,
            'Referer': f"{AMES_BASE_URL}/views/tianpan/sjfxrpt/rpt_tjfx_flightinfo.shtml",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # 计算日期范围内的天数
        delta = (end_date_obj - start_date_obj).days + 1
        
        # 从AMES API获取航班数据
        try:
            from app.api.ames import FLIGHT_INFO_API_URL
        except ImportError:
            FLIGHT_INFO_API_URL = "https://ames.juneyaoair.com/api/v1/plugins/TIANPAN_SJFX_FLIGHTINFO_LIST"
        
        # 存储所有航班数据
        all_flights = []
        
        # 对日期范围内的每一天单独请求数据
        current_date = start_date_obj
        for i in range(delta):
            current_date_str = current_date.strftime("%Y-%m-%d")
            
            # 为每一天构建查询数据
            data = {
                'ACNO': ac_reg,  # 飞机注册号
                'flightDate': current_date_str,  # 查询日期
                'page': '1',
                'rows': '20'  # 每天请求足够多的记录
            }
            
            logger.info(f"获取 {ac_reg} 在 {current_date_str} 的航班记录")
            
            # 发送POST请求
            try:
                async with httpx.AsyncClient(verify=False, timeout=30) as client:
                    response = await client.post(
                        FLIGHT_INFO_API_URL,
                        headers=headers,
                        cookies=cookies,
                        data=data
                    )
                    
                    # 检查响应状态
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 检查API返回码
                        if result.get('code') == 200 or result.get('code') == '200':
                            flight_data = result.get('data', [])
                            
                            # 格式化并添加当前日期的航班数据
                            for flight in flight_data:
                                # 提取航班日期，通常格式为 "2025-04-22 00:00:00"
                                flight_date = flight.get('FLIGHT_DATE', '').split()[0] if flight.get('FLIGHT_DATE') else current_date_str
                                
                                # 添加航班记录
                                all_flights.append({
                                    "flight_no": flight.get('FLIGHT_NO', ''),
                                    "flight_date": flight_date,
                                    "dep_code": flight.get('DEP3CODE', ''),
                                    "arr_code": flight.get('ARR3CODE', ''),
                                    "std": flight.get('STD', ''),
                                    "atd": flight.get('ATD', ''),
                                    "sta": flight.get('STA', ''),
                                    "eta": flight.get('ETA', '')
                                })
                            
                            logger.info(f"成功获取 {len(flight_data)} 条 {current_date_str} 的航班记录")
                        else:
                            logger.warning(f"获取 {current_date_str} 航班记录失败: {result.get('msg', '未知错误')}")
                    else:
                        logger.warning(f"请求 {current_date_str} 航班记录失败, 状态码: {response.status_code}")
            except Exception as day_error:
                logger.error(f"获取 {current_date_str} 航班记录时出错: {str(day_error)}")
            
            # 递增日期
            current_date += timedelta(days=1)
            
            # 添加一个小延迟，避免频繁请求
            await asyncio.sleep(0.5)
        
        # 排序航班记录
        all_flights.sort(key=lambda x: (x['flight_date'], x['std']))
        
        # 如果不是include_all模式，限制返回的记录数量
        if not include_all and len(all_flights) > limit:
            all_flights = all_flights[:limit]
        
        # 返回航班记录
        return {
            "success": True,
            "data": all_flights
        }
    except Exception as e:
        logger.error(f"获取飞机近期航班记录出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取航班记录失败: {str(e)}"
        } 
    
@router.get("/outstation-faults/{ac_reg}")
async def get_outstation_faults(
    ac_reg: str,
    session_id: Optional[str] = Header(None, alias="Session-Id")
):
    """获取飞机外站故障保留信息
    
    参数:
        ac_reg: 飞机注册号
        session_id: 会话ID
    
    返回:
        外站故障保留信息列表
    """
    try:
        # 如果传入的飞机号没有包含"B-"前缀，添加前缀
        formatted_ac_reg = ac_reg
        if not formatted_ac_reg.startswith("B-"):
            formatted_ac_reg = f"B-{formatted_ac_reg}"
        
        # 获取用户会话cookies
        cookies = None
        if session_id:
            try:
                from app.api.local import user_sessions
                if session_id in user_sessions:
                    cookies = user_sessions[session_id].get('cookies', {})
            except ImportError:
                logger.warning("无法导入用户会话模块")
                
        # 如果没有cookies，使用默认cookies
        if not cookies:
            cookies = {
                '_udid': 'ca55384ddd78475cbacf8c840bfeff95',
                'i18next': 'zh',
                'JSESSIONID': '1CCACF248A5E943F3360CFEE82D511F2',
                'sfFilter': '8abcad82db547adb6986544becc954cd',
                '_amro_sk': 'c81cbcff-d115-402e-bc61-f5299d01b63e'
            }
            
        # 准备请求头
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': AMES_BASE_URL,
            'Referer': f"{AMES_BASE_URL}/views/pmDdsDdBase/pm_dds_dd_base_list.shtml",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # 准备请求数据
        data = {
            'notcloseout': 'Y',
            'outNo': '',
            'acno1': formatted_ac_reg,  # 使用格式化后的飞机号
            'ata1': '',
            'ata2': '',
            'status1': '',
            'startDate': '',
            'endDate': '',
            'flightSite': '',
            'outDesc': '',
            'mel': '',
            'corrAction': '',
            'creatBy': '',
            'closeBy': '',
            'page': '1',
            'rows': '100'  # 一次请求足够多的数据
        }
        
        # 发送请求
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                "https://ames.juneyaoair.com/api/v1/plugins/MC_OUTSTATION_LIST",
                headers=headers,
                cookies=cookies,
                data=data
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 获取所有外站故障保留记录
                    all_faults = result.get('data', [])
                    
                    # 筛选出STATUS不是"YGB"的记录
                    filtered_faults = [f for f in all_faults if f.get('STATUS') != 'YGB']
                    
                    # 格式化返回数据
                    formatted_faults = []
                    for fault in filtered_faults:
                        # 提取日期，通常格式为 "2025-04-18 00:00:00"
                        out_date = fault.get('OUT_DATE', '').split()[0] if fault.get('OUT_DATE') else ''
                        
                        formatted_faults.append({
                            "out_no": fault.get('OUT_NO', ''),
                            "out_date": out_date,
                            "ata": fault.get('ATA', ''),
                            "mel": fault.get('MEL', ''),
                            "out_desc": fault.get('OUT_DESC', ''),
                            "flight_site": fault.get('FLIGHT_SITE', ''),
                            "status": fault.get('STATUS', ''),
                            "ac_reg": fault.get('ACNO', '')  # 原始飞机号（带B-前缀）
                        })
                    
                    return {
                        "success": True,
                        "data": formatted_faults
                    }
                else:
                    return {
                        "success": False,
                        "message": f"获取外站故障保留信息失败: {result.get('msg', '未知错误')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"请求外站故障保留信息失败, 状态码: {response.status_code}"
                }
    except Exception as e:
        logger.error(f"获取外站故障保留信息出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取外站故障保留信息失败: {str(e)}"
        }
    
@router.get("/fault-retentions/{ac_reg}")
async def get_fault_retentions(
    ac_reg: str,
    session_id: Optional[str] = Header(None, alias="Session-Id")
):
    """获取飞机故障保留信息
    
    参数:
        ac_reg: 飞机注册号
        session_id: 会话ID
    
    返回:
        故障保留信息列表
    """
    try:
        # 如果传入的飞机号没有包含"B-"前缀，添加前缀
        formatted_ac_reg = ac_reg
        if not formatted_ac_reg.startswith("B-"):
            formatted_ac_reg = f"B-{formatted_ac_reg}"
        
        # 获取用户会话cookies
        cookies = None
        if session_id:
            try:
                from app.api.local import user_sessions
                if session_id in user_sessions:
                    cookies = user_sessions[session_id].get('cookies', {})
            except ImportError:
                logger.warning("无法导入用户会话模块")
                
        # 如果没有cookies，使用默认cookies
        if not cookies:
            cookies = {
                '_udid': 'ca55384ddd78475cbacf8c840bfeff95',
                'i18next': 'zh',
                'JSESSIONID': '1CCACF248A5E943F3360CFEE82D511F2',
                'sfFilter': '8abcad82db547adb6986544becc954cd',
                '_amro_sk': 'c81cbcff-d115-402e-bc61-f5299d01b63e'
            }
            
        # 准备请求头
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': AMES_BASE_URL,
            'Referer': f"{AMES_BASE_URL}/views/pmDdsDdBase/pm_dds_dd_base_list.shtml",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # 准备请求数据
        data = {
            'type': 'DD',
            'category': 'pmDdsDdBaseService',
            'notClosed': 'Y',
            'ddfNo': '',
            'acno': formatted_ac_reg,  # 使用格式化后的飞机号
            'ata1': '',
            'ata2': '',
            'status': '',
            'faurep': '',
            'startDate1': '',
            'endDate1': '',
            'xfqx': '',
            'blrea': '',
            'acType': '',
            'unitOperationMeasures': '',
            'observationProject': '',
            'operationalRestrictions': '',
            'warningSign': '',
            'repeatCheck': '',
            'page': '1',
            'rows': '100'  # 一次请求足够多的数据
        }
        
        # 发送请求
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                "https://ames.juneyaoair.com/api/v1/plugins/PM_DDS_DD_BASE_LIST",
                headers=headers,
                cookies=cookies,
                data=data
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 获取所有故障保留记录
                    all_faults = result.get('data', [])
                    
                    # 格式化返回数据
                    formatted_faults = []
                    for fault in all_faults:
                        # 提取申请日期
                        apply_date = fault.get('APPLY_DATE', '').split()[0] if fault.get('APPLY_DATE') else ''
                        
                        formatted_faults.append({
                            "ddf_no": fault.get('DDF_NO', ''),
                            "apply_date": apply_date,
                            "ata": fault.get('ATA', ''),
                            "blbs_no": fault.get('BLBS_NO', ''),  # MEL编号
                            "faurep": fault.get('FAUREP', ''),  # 故障描述
                            "terminal": fault.get('TERMINAL', ''),  # 航站
                            "status": fault.get('STATUS', ''),
                            "ac_reg": fault.get('ACNO', ''),  # 原始飞机号（带B-前缀）
                            "dyd": fault.get('DYD', ''),  # 保留天数
                            "working_date": fault.get('WORKING_DATE', '')  # 工作日期
                        })
                    
                    return {
                        "success": True,
                        "data": formatted_faults
                    }
                else:
                    return {
                        "success": False,
                        "message": f"获取故障保留信息失败: {result.get('msg', '未知错误')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"请求故障保留信息失败, 状态码: {response.status_code}"
                }
    except Exception as e:
        logger.error(f"获取故障保留信息出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取故障保留信息失败: {str(e)}"
        }

@router.get("/defect-retentions/{ac_reg}")
async def get_defect_retentions(
    ac_reg: str,
    session_id: Optional[str] = Header(None, alias="Session-Id")
):
    """获取飞机缺陷保留信息
    
    参数:
        ac_reg: 飞机注册号
        session_id: 会话ID
    
    返回:
        缺陷保留信息列表
    """
    try:
        # 如果传入的飞机号没有包含"B-"前缀，添加前缀
        formatted_ac_reg = ac_reg
        if not formatted_ac_reg.startswith("B-"):
            formatted_ac_reg = f"B-{formatted_ac_reg}"
        
        # 获取用户会话cookies
        cookies = None
        if session_id:
            try:
                from app.api.local import user_sessions
                if session_id in user_sessions:
                    cookies = user_sessions[session_id].get('cookies', {})
            except ImportError:
                logger.warning("无法导入用户会话模块")
                
        # 如果没有cookies，使用默认cookies
        if not cookies:
            cookies = {
                '_udid': 'ca55384ddd78475cbacf8c840bfeff95',
                'i18next': 'zh',
                'JSESSIONID': '1CCACF248A5E943F3360CFEE82D511F2',
                'sfFilter': '8abcad82db547adb6986544becc954cd',
                '_amro_sk': 'c81cbcff-d115-402e-bc61-f5299d01b63e'
            }
            
        # 准备请求头
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': AMES_BASE_URL,
            'Referer': f"{AMES_BASE_URL}/views/pmDdsFcBase/pm_dds_fc_base_list.shtml",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # 准备请求数据
        data = {
            'type': 'FC',
            'category': 'pmDdsFcBaseService',
            'notClosed': 'Y',
            'ddfNo': '',
            'acno': formatted_ac_reg,  # 使用格式化后的飞机号
            'ata1': '',
            'ata2': '',
            'status': '',
            'faurep': '',
            'startDate1': '',
            'endDate1': '',
            'xfqx': '',
            'blrea': '',
            'acType': '',
            'unitOperationMeasures': '',
            'observationProject': '',
            'operationalRestrictions': '',
            'warningSign': '',
            'repeatCheck': '',
            'pSourceAta': '',
            'page': '1',
            'rows': '100'  # 一次请求足够多的数据
        }
        
        # 发送请求
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                "https://ames.juneyaoair.com/api/v1/plugins/PM_DDS_DD_BASE_LIST",
                headers=headers,
                cookies=cookies,
                data=data
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    # 获取所有缺陷保留记录
                    all_defects = result.get('data', [])
                    
                    # 格式化返回数据
                    formatted_defects = []
                    for defect in all_defects:
                        # 提取申请日期
                        apply_date = defect.get('APPLY_DATE', '').split()[0] if defect.get('APPLY_DATE') else ''
                        # 提取修复日期
                        repair_date = defect.get('REPAIR_DATE', '').split()[0] if defect.get('REPAIR_DATE') else ''
                        
                        formatted_defects.append({
                            "ddf_no": defect.get('DDF_NO', ''),
                            "apply_date": apply_date,
                            "ata": defect.get('ATA', ''),
                            "blbs_no": defect.get('BLBS_NO', ''),  # 依据文件
                            "faurep": defect.get('FAUREP', ''),  # 故障描述
                            "terminal": defect.get('TERMINAL', ''),  # 航站
                            "status": defect.get('STATUS', ''),
                            "ac_reg": defect.get('ACNO', ''),  # 原始飞机号（带B-前缀）
                            "fc": defect.get('FC', ''),  # 飞行循环
                            "repair_date": repair_date,  # 修复日期
                            "working_date": defect.get('WORKING_DATE', '')  # 工作日期
                        })
                    
                    return {
                        "success": True,
                        "data": formatted_defects
                    }
                else:
                    return {
                        "success": False,
                        "message": f"获取缺陷保留信息失败: {result.get('msg', '未知错误')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"请求缺陷保留信息失败, 状态码: {response.status_code}"
                }
    except Exception as e:
        logger.error(f"获取缺陷保留信息出错: {str(e)}")
        return {
            "success": False,
            "message": f"获取缺陷保留信息失败: {str(e)}"
        }