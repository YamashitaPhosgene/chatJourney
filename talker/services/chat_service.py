#!/usr/bin/env python
# encoding: utf-8

from typing import Dict, Any, Optional, Union
from talker.api import VivoGPT, VivoGPTError
from requests import Response
import logging

class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self.vivo_client = VivoGPT()
    
    def process_chat(self, message: str, chat_type: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> Union[Dict[str, Any], Response]:
        """处理聊天请求
        
        Args:
            message: 用户消息
            chat_type: 聊天类型（对应预设类型）
            temperature: 温度参数
            max_tokens: 最大生成长度
            **kwargs: 其他参数，用于模板变量替换
            
        Returns:
            聊天响应数据
        """
        try:
            # 如果提供了 chat_type，先获取并处理模板
            if chat_type:
                system_prompt = self.vivo_client.get_prompt(chat_type)
                if system_prompt:
                    # 将 kwargs 中的参数添加到 message 中，用于模板替换
                    template_data = {
                        'input': message,
                        **kwargs
                    }
                    
                    # 尝试进行模板替换
                    try:
                        formatted_prompt = system_prompt.format(**template_data)
                        # 使用格式化后的 prompt 作为完整的 prompt
                        response = self.vivo_client.chat(
                            prompt=formatted_prompt,
                            type=None,  # 不使用 type，因为我们已经处理了模板
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                    except KeyError as e:
                        # 如果模板变量不匹配，使用原始方式
                        logging.warning(f"模板变量替换失败: {e}，使用原始方式")
                        response = self.vivo_client.chat(
                            prompt=message,
                            type=chat_type,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                else:
                    raise ValueError(f"预设 {chat_type} 不存在")
            else:
                # 没有 chat_type，直接调用
                response = self.vivo_client.chat(
                    prompt=message,
                    type=None,
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
    
    def process_chat_with_history(self, messages: list, state: Optional[Dict[str, Any]] = None, temperature: float = 0.7, max_tokens: int = 2048) -> Union[Dict[str, Any], Response]:
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