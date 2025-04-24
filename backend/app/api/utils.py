#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 文件名: utils.py
# 描述: 通用工具API接口

from fastapi import APIRouter
from typing import List, Dict, Any, Optional
import os
import sqlite3
import logging
from app.utils.config import ALL_AIRCRAFT, CONFIG_DIR

# 配置日志
logger = logging.getLogger("phm_system.api.utils")

router = APIRouter(prefix="/utils", tags=["通用工具"])

@router.get("/aircraft-list")
async def get_aircraft_list() -> dict:
    """
    获取所有飞机列表
    
    返回:
        dict: 包含飞机列表的字典
    """
    try:
        return {
            "success": True,
            "data": ALL_AIRCRAFT,
            "message": "获取飞机列表成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": f"获取飞机列表失败: {str(e)}"
        }

# 定义A320MOD查询相关路由
mod_router = APIRouter(prefix="/tools/mod-search", tags=["A320MOD查询"])

def get_db_path() -> str:
    """获取MOD数据库文件路径"""
    # 存放在与config相同的目录
    return os.path.join(CONFIG_DIR, "mod_data.db")

@mod_router.get("/status")
async def get_mod_db_status() -> Dict[str, Any]:
    """
    获取MOD数据库状态
    
    返回:
        dict: 包含数据库状态信息
    """
    try:
        db_path = get_db_path()
        
        if not os.path.exists(db_path):
            return {
                "success": False,
                "message": "数据库文件不存在，请先上传mod_data.db文件到configs目录"
            }
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 获取MOD数量
        c.execute("SELECT COUNT(*) FROM mods")
        mod_count = c.fetchone()[0]
        
        # 关闭连接
        conn.close()
        
        return {
            "success": True,
            "mod_count": mod_count,
            "message": "数据库连接成功"
        }
        
    except Exception as e:
        logger.error(f"检查MOD数据库状态时出错: {str(e)}")
        return {
            "success": False,
            "message": f"检查数据库状态时出错: {str(e)}"
        }

@mod_router.get("/{mod_number}")
async def search_mod(mod_number: str) -> Dict[str, Any]:
    """
    根据MOD编号搜索MOD信息
    
    参数:
        mod_number: MOD编号
    
    返回:
        dict: 包含MOD信息和执行情况
    """
    try:
        db_path = get_db_path()
        
        if not os.path.exists(db_path):
            return {
                "success": False,
                "message": "数据库文件不存在，请先上传mod_data.db文件到configs目录"
            }
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以按名称访问
        c = conn.cursor()
        
        # 查询MOD基本信息
        c.execute("""
            SELECT * FROM mods WHERE mod_num = ?
        """, (mod_number,))
        mod_data = c.fetchone()
        
        if not mod_data:
            conn.close()
            return {
                "success": True,
                "mod_data": None,
                "message": f"未找到MOD: {mod_number}"
            }
        
        # 转换为字典
        mod_dict = dict(mod_data)
        
        # 查询执行情况 - 明确使用别名确保字段名称正确
        c.execute("""
            SELECT 
                h.col_id, 
                h.reg_num AS reg_num, 
                h.aircraft_type AS aircraft_type, 
                h.fsn AS fsn, 
                h.msn AS msn, 
                e.executed
            FROM headers h
            JOIN executions e ON h.col_id = e.col_id
            WHERE e.mod_id = ? AND e.executed = 1
        """, (mod_data['id'],))
        
        # 显式将查询结果转换为字典列表
        executions = []
        for row in c.fetchall():
            row_dict = dict(row)
            executions.append(row_dict)
        
        # 查询列头信息
        c.execute("SELECT col_id, reg_num, aircraft_type, fsn, msn FROM headers")
        headers = {}
        for row in c.fetchall():
            row_dict = dict(row)
            headers[row_dict['col_id']] = {
                '机号': row_dict['reg_num'],
                '机型': row_dict['aircraft_type'],
                'FSN': row_dict['fsn'],
                'MSN': row_dict['msn']
            }
        
        # 处理全局ALL检查
        b_cols = [col for col, h in headers.items() if str(h['机号']).startswith('B')]
        
        if b_cols:
            c.execute("""
                SELECT COUNT(*) FROM executions 
                WHERE mod_id = ? AND executed = 1 AND col_id IN ({})
            """.format(','.join('?' * len(b_cols))), [mod_data['id']] + b_cols)
            
            executed_count = c.fetchone()[0]
            mod_dict['all_execution_status'] = executed_count == len(b_cols)
        else:
            mod_dict['all_execution_status'] = False
        
        # 处理执行结果 - 使用安全的字段访问
        grouped_data = {}
        for record in executions:
            # 安全获取字段，提供默认值
            aircraft = record.get('aircraft_type', '')
            reg_num = record.get('reg_num', '')
            fsn = record.get('fsn', '')
            msn = record.get('msn', '')
            
            # 如果aircraft字段不存在，尝试其他可能的键
            if not aircraft:
                for key in record.keys():
                    if 'aircraft' in str(key).lower() or '机型' in str(key):
                        aircraft = record[key]
                        break
                # 如果仍未找到，使用默认值
                if not aircraft:
                    aircraft = "未知机型"
            
            # 分组数据
            if aircraft not in grouped_data:
                grouped_data[aircraft] = {'机号': set(), 'FSN': [], 'MSN': set()}
            
            grouped_data[aircraft]['机号'].add(reg_num)
            grouped_data[aircraft]['FSN'].append(fsn)
            grouped_data[aircraft]['MSN'].add(str(msn))
        
        # 检查每个机型是否全部执行
        for aircraft in grouped_data:
            # 获取该机型所有B开头的有效列
            aircraft_cols = [
                col for col, header in headers.items()
                if header['机型'] == aircraft 
                and str(header['机号']).startswith('B')
            ]
            
            if aircraft_cols:
                c.execute("""
                    SELECT COUNT(*) FROM executions 
                    WHERE mod_id = ? AND executed = 1 AND col_id IN ({})
                """.format(','.join('?' * len(aircraft_cols))), [mod_data['id']] + aircraft_cols)
                
                executed_count = c.fetchone()[0]
                grouped_data[aircraft]['ALL'] = executed_count == len(aircraft_cols)
            else:
                grouped_data[aircraft]['ALL'] = False
        
        # 格式化结果
        result_data = []
        for aircraft, group in grouped_data.items():
            # 处理ALL标记
            aircraft_display = aircraft
            if group.get('ALL', False):
                aircraft_display = f"{aircraft} (ALL)"
            
            # 格式化机号 - 确保数据存在
            reg_nums = format_aircraft_numbers(group.get('机号', set()))
            
            # 格式化FSN范围 - 确保数据存在
            fsn_range = format_fsn_ranges(group.get('FSN', []))
            
            # 格式化MSN列表 - 确保数据存在
            msn_list = format_multiline(sorted(group.get('MSN', set()), key=lambda x: int(x) if str(x).isdigit() else 0))
            
            result_data.append({
                'aircraft_type': aircraft_display,
                'reg_nums': reg_nums,
                'fsn_range': fsn_range,
                'msn_list': msn_list
            })
        
        conn.close()
        
        return {
            "success": True,
            "mod_data": mod_dict,
            "executions": result_data,
            "message": "查询成功"
        }
        
    except Exception as e:
        logger.error(f"搜索MOD时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())  # 记录完整的错误堆栈
        return {
            "success": False,
            "message": f"搜索MOD时出错: {str(e)}"
        }

# 辅助函数
def format_aircraft_numbers(numbers):
    """格式化机号范围"""
    if not numbers:
        return ""
    
    processed = []
    for num in sorted(numbers):
        if not num:  # 跳过空值
            continue
            
        if "-" in str(num)[2:]:  # 处理B-XXXX-XXX格式
            parts = str(num).split("-", 2)
            if len(parts) >= 2:
                prefix = parts[0]
                range_part = parts[1]
                start_end = range_part.split("-")
                try:
                    start = int(start_end[0])
                    end = int(start_end[1]) if len(start_end) > 1 else start
                    processed.extend(f"{prefix}-{i:03d}" for i in range(start, end+1))
                except (ValueError, IndexError):
                    # 如果转换失败，直接添加原始值
                    processed.append(str(num))
        else:
            processed.append(str(num))
    
    return format_multiline(sorted(processed))

def format_fsn_ranges(fsn_list):
    """生成FSN区间字符串"""
    if not fsn_list:
        return ""
        
    try:
        # 过滤空值并转换为整数
        valid_fsn = [int(fsn) for fsn in fsn_list if fsn and str(fsn).strip() and str(fsn).strip().isdigit()]
        sorted_fsn = sorted(valid_fsn)
        
        if not sorted_fsn:
            return ""
            
        from itertools import groupby
        from operator import itemgetter
        
        ranges = []
        for _, g in groupby(enumerate(sorted_fsn), lambda x: x[0]-x[1]):
            group = list(map(itemgetter(1), g))
            ranges.append(f"{group[0]}-{group[-1]}" if len(group)>1 else str(group[0]))
        return ', '.join(ranges)
    except Exception as e:
        logger.error(f"格式化FSN范围时出错: {str(e)}")
        return "FSN格式异常"

def format_multiline(items, max_per_line=6, max_lines=5):
    """通用多行格式化"""
    if not items:
        return ""
        
    # 确保所有项都是字符串
    items = [str(item) for item in items if item is not None]
    
    if len(items) > (max_items := max_per_line * max_lines):
        items = items[:max_items] + ["..."]
    
    lines = [", ".join(items[i:i+max_per_line]) 
            for i in range(0, len(items), max_per_line)]
    return '\n'.join(lines)

# 将mod_router包含在全局router中
router.include_router(mod_router)