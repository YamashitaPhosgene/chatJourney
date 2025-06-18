#!/usr/bin/env python
# encoding: utf-8

from typing import Dict, Any, Optional
from talker.api import VivoGPT, VivoGPTError

class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self.vivo_client = VivoGPT()
    
    def process_chat(self, message: str, chat_type: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """处理聊天请求
        
        Args:
            message: 用户消息
            chat_type: 聊天类型（对应预设类型）
            temperature: 温度参数
            max_tokens: 最大生成长度
            
        Returns:
            聊天响应数据
        """
        try:
            response = self.vivo_client.chat(
                prompt=message,
                type=chat_type,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except VivoGPTError as e:
            # 处理API错误
            return {
                "error": True,
                "code": e.code,
                "message": e.message
            }
        except Exception as e:
            # 处理其他错误
            return {
                "error": True,
                "code": -1,
                "message": str(e)
            }
    
    def process_chat_with_history(self, messages: list, temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """处理带历史记录的聊天请求
        
        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大生成长度
            
        Returns:
            聊天响应数据
        """
        try:
            response = self.vivo_client.chat_with_history(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except VivoGPTError as e:
            return {
                "error": True,
                "code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {
                "error": True,
                "code": -1,
                "message": str(e)
            } 