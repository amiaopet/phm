# app/utils/auth.py
from fastapi import Header, HTTPException, status
from typing import Dict, Optional
import logging

# 用于存储用户会话的字典
user_sessions = {}

logger = logging.getLogger("phm_system.auth")

async def get_current_user(session_id: Optional[str] = Header(None, alias="Session-Id")):
    """验证会话并返回当前用户信息
    
    Args:
        session_id: 从请求头中获取的会话ID
        
    Returns:
        用户会话信息
    
    Raises:
        HTTPException: 如果会话ID无效或不存在
    """
    logger.info(f"接收到会话ID: {session_id}")
    logger.info(f"当前活动会话: {list(user_sessions.keys())}")
    
    if not session_id:
        logger.warning("请求缺少Session-Id头部")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if session_id not in user_sessions:
        logger.warning(f"无效的会话ID: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"会话验证成功: {session_id}, 用户: {user_sessions[session_id].get('username')}")
    return user_sessions[session_id]