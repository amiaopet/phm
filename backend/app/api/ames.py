#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: ames.py
# 描述: AMES系统接口

import requests
import logging
import urllib3
import pickle
import os
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, Any, List, Optional, Tuple
import httpx
from pydantic import BaseModel

# 禁用不安全连接警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入配置
from app.utils.config import BASE_URL, CONFIG_DIR

# 定义 AMES 相关常量
LOGIN_URL = f'{BASE_URL}/api/v1/security/loginSC'
COOKIE_FILE = os.path.join(CONFIG_DIR, 'cookies.pkl')
FLB_LIST_API_URL = f'{BASE_URL}/api/v1/plugins/LM_FLB_LIST'  # 飞行日志API
FLB_PART_API_URL = f'{BASE_URL}/api/v1/plugins/LM_FLB_PART_LIST'  # 部件详情API
ACMS_API_URL = f'{BASE_URL}/api/v1/plugins/MC_XNMONITOR_ACMS'  # ACMS数据API
FLIGHT_INFO_API_URL = f'{BASE_URL}/api/v1/plugins/TIANPAN_SJFX_FLIGHTINFO_LIST'  # 航班信息API

# 配置路由
router = APIRouter()

# 配置日志
logger = logging.getLogger("phm_system.api.ames")

def save_cookies(cookies: Dict[str, str]) -> None:
    """保存cookies到本地文件"""
    try:
        with open(COOKIE_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info(f"Cookie已保存到 {COOKIE_FILE}")
    except Exception as e:
        logger.error(f"保存Cookie失败: {str(e)}")

def load_cookies() -> Optional[Dict[str, str]]:
    """从本地文件加载cookies"""
    try:
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        logger.error(f"加载Cookie失败: {str(e)}")
    return None

def check_cookie_valid(cookies: Dict[str, str]) -> Tuple[bool, str]:
    """检查cookies是否有效
    
    参数:
        cookies: Cookie字典
        
    返回值:
        (success, message) 元组
    """
    try:
        # 使用一个简单的API端点来测试cookies是否有效
        test_url = f'{BASE_URL}/api/v1/user/info'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
        response = requests.get(test_url, cookies=cookies, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            return True, "Cookie有效"
        else:
            return False, f"Cookie无效，状态码: {response.status_code}"
    except Exception as e:
        return False, f"检查Cookie时出错: {str(e)}"

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

class FlightInfoRequest(BaseModel):
    flight_date: str
    ac_reg: Optional[str] = None
    flight_no: Optional[str] = None
    dep_code: Optional[str] = None
    arr_code: Optional[str] = None
    page: int = 1
    rows: int = 50

# 路由API端点
@router.post("/login")
async def login_ames(request: LoginRequest):
    """登录AMES系统"""
    try:
        login_data = {
            'username': request.username,
            'userPassword': request.password
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{BASE_URL}/views/login.shtml'
        }
        
        session = requests.Session()
        response = session.post(
            LOGIN_URL, 
            data=login_data, 
            headers=headers, 
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('code') == 0 or 'success' in response.text.lower():
                    cookies = session.cookies.get_dict()
                    logger.info(f"登录成功！已获取有效Cookie")
                    return {"success": True, "cookies": cookies, "message": "成功获取登录凭据"}
                else:
                    error_msg = f"登录失败，服务器返回: {result.get('msg', '未知错误')}"
                    logger.error(error_msg)
                    return {"success": False, "cookies": None, "message": error_msg}
            except Exception as e:
                # 尝试直接获取cookies
                cookies = session.cookies.get_dict()
                if cookies:
                    logger.info(f"登录成功！已获取有效Cookie")
                    return {"success": True, "cookies": cookies, "message": "成功获取登录凭据"}
                
                error_msg = f"解析登录响应失败: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "cookies": None, "message": error_msg}
        else:
            error_msg = f"登录请求失败，状态码: {response.status_code}"
            logger.error(error_msg)
            return {"success": False, "cookies": None, "message": error_msg}
    
    except Exception as e:
        error_msg = f"登录过程出错: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "cookies": None, "message": error_msg}

@router.post("/aircraft-data")
async def get_aircraft_data(cookies: Dict[str, str], sub: str, acno: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """获取飞机ACMS数据"""
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/views/mc/technicalHandover/mc_tec_xn_monitor.shtml',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'sub': sub,
        'ata': '36',
        'stdate': start_date,
        'endate': end_date,
        'acno': acno,
        'page': '1',
        'rows': '500'  # 请求更多行数以获取更多数据
    }
    
    try:
        response = requests.post(
            ACMS_API_URL,
            headers=headers,
            cookies=cookies,
            data=data,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', [])
        else:
            logger.error(f"获取飞机数据失败，状态码: {response.status_code}")
            return []
    
    except Exception as e:
        logger.error(f"获取飞机数据时出错: {str(e)}")
        return []

@router.post("/flb/list")
async def get_flb_list(cookies: Dict[str, str], aircraft: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """获取飞行日志列表"""
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/views/lm/flb/lm_flb_list.shtml',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'tab': 'tab2',
        'flbDate1': start_date,
        'flbDate2': end_date,
        'flbNo': '',
        'acType': '',
        'acno': aircraft,
        'state': '',
        'flightSort': '',
        'flightNo': '',
        'pfReleaseEtops': '',
        'releaseMan': '',
        'releaseManAF': '',
        'page': '1',
        'rows': '1000'  # 使用较大的行数以获取更多记录
    }
    
    try:
        response = requests.post(
            FLB_LIST_API_URL,
            headers=headers,
            cookies=cookies,
            data=data,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', [])
        else:
            logger.error(f"获取飞行日志列表失败，状态码: {response.status_code}")
            return []
    
    except Exception as e:
        logger.error(f"获取飞行日志列表时出错: {str(e)}")
        return []

@router.post("/flb/parts")
async def get_flb_parts(cookies: Dict[str, str], flb_id: str) -> List[Dict[str, Any]]:
    """获取飞行日志的部件详情"""
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/views/lm/flb/lm_flb_modify.shtml',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'FunctionCode': 'LM_FLB_PART_LIST',
        'flbId': str(flb_id)
    }
    
    try:
        response = requests.post(
            FLB_PART_API_URL,
            headers=headers,
            cookies=cookies,
            data=data,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('data', [])
        else:
            logger.error(f"获取飞行日志部件详情失败，状态码: {response.status_code}")
            return []
    
    except Exception as e:
        logger.error(f"获取飞行日志部件详情时出错: {str(e)}")
        return []

@router.post("/flight-info")
async def get_flight_info(request: FlightInfoRequest, session_id: Optional[str] = Header(None, alias="Session-Id")):
    """获取航班信息
    
    参数:
        request: 请求参数
            flight_date: 航班日期 (YYYY-MM-DD)
            ac_reg: 飞机号 (可选)
            flight_no: 航班号 (可选)
            dep_code: 起飞机场 (可选)
            arr_code: 降落机场 (可选)
            page: 页码，默认1
            rows: 每页行数，默认50
        session_id: 会话ID
    
    返回值:
        航班信息数据
    """
    try:
        # 从本地导入用户会话
        from app.api.local import user_sessions
        
        # 获取cookies
        cookies = None
        if session_id and session_id in user_sessions:
            cookies = user_sessions[session_id].get('cookies')
        
        # 如果没有session_id或者cookies为空，尝试加载本地cookies
        if not cookies:
            cookies = load_cookies()
            
            # 如果仍然没有cookies，返回错误
            if not cookies:
                return {"success": False, "message": "未登录或会话已过期"}
        
        # 构建请求参数
        data = {
            'flightDate': request.flight_date,
            'page': request.page,
            'rows': request.rows
        }
        
        # 添加可选参数
        if request.ac_reg:
            data['ACNO'] = request.ac_reg
        if request.flight_no:
            data['FLIGHT_NO'] = request.flight_no
        if request.dep_code:
            data['ZXDD'] = request.dep_code
        if request.arr_code:
            data['DDHZ'] = request.arr_code
        
        # 发送请求
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response = await client.post(
                FLIGHT_INFO_API_URL,
                data=data,
                cookies=cookies,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 处理API响应
                if result.get('code') == 200 or result.get('code') == '200':
                    flight_data = result.get('data', [])
                    
                    # 格式化数据，将需要的字段提取出来
                    formatted_data = []
                    for flight in flight_data:
                        formatted_flight = {
                            'ac_reg': flight.get('AC_REG', ''),
                            'flight_no': flight.get('FLIGHT_NO', ''),
                            'flight_date': flight.get('FLIGHT_DATE', '').split()[0] if flight.get('FLIGHT_DATE') else '',
                            'arr_code': flight.get('ARR3CODE', ''),
                            'dep_code': flight.get('DEP3CODE', ''),
                            'std': flight.get('STD', ''),
                            'atd': flight.get('ATD', ''),
                            'close_door_time': flight.get('CLOSE_DOOR_TIME', ''),
                            'data_out': flight.get('DATA_OUT', ''),
                            'dep_delay_time': flight.get('DEP_DELAY_TIME', ''),
                            'sta': flight.get('STA', ''),
                            'eta': flight.get('ETA', '')
                        }
                        formatted_data.append(formatted_flight)
                    
                    return {
                        "success": True,
                        "data": {
                            "flights": formatted_data,
                            "total": result.get('total', 0),
                            "page": result.get('page', 1)
                        }
                    }
                else:
                    return {"success": False, "message": f"获取航班信息失败: {result.get('msg', '未知错误')}"}
            else:
                return {"success": False, "message": f"获取航班信息请求失败，状态码: {response.status_code}"}
    
    except Exception as e:
        logger.error(f"获取航班信息出错: {str(e)}")
        return {"success": False, "message": f"获取航班信息出错: {str(e)}"}