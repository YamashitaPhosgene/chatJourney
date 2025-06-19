#!/usr/bin/env python
# encoding: utf-8

from typing import Dict, Any, Optional, Union
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
    
    def _format_state_message(self, state: Dict[str, Any]) -> str:
        """将状态信息格式化为system message
        
        Args:
            state: 状态信息字典
            
        Returns:
            格式化后的状态信息
        """
        # 这里可以根据实际需求自定义格式化逻辑
        parts = []
        if state.get('stage'):
            parts.append(f"当前阶段：{state['stage']}")
        if state.get('intent'):
            parts.append(f"用户意图：{state['intent']}")
        if state.get('context'):
            parts.append(f"上下文：{state['context']}")
        return '；'.join(parts)
    
    def process_chat_with_history(self, messages: list, state: Optional[Dict[str, Any]] = None, temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        """处理带历史记录的聊天请求
        
        Args:
            messages: 消息历史列表
            state: 当前对话状态字典
            temperature: 温度参数
            max_tokens: 最大生成长度
            
        Returns:
            聊天响应数据
        """
        try:
            # 如果有状态信息，将其格式化并作为system message添加到历史记录的开头
            if state:
                state_message = self._format_state_message(state)
                if state_message:
                    messages = [{"role": "system", "content": state_message}] + messages
                
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