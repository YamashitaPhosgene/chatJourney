#!/usr/bin/env python
# encoding: utf-8

import requests
import json
import uuid
import os
from typing import Optional, Dict, Any, Union
from django.conf import settings
from .auth import AuthUtils
from .exceptions import VivoGPTError
from talker.config import load_prompts
from requests import Response

class VivoGPT:
    """蓝心大模型API客户端"""
    
    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None):
        """初始化API客户端
        
        Args:
            app_id: 应用ID，如果不提供则从Django设置读取
            app_key: 应用密钥，如果不提供则从Django设置读取
        """
        # 获取应用ID和密钥
        self.app_id = app_id or getattr(settings, 'VIVO_APP_ID')
        self.app_key = app_key or getattr(settings, 'VIVO_APP_KEY')
        
        if not self.app_id or not self.app_key:
            raise ValueError("请设置VIVO_APP_ID和VIVO_APP_KEY配置，或通过参数提供")
            
        self.base_url = "https://api-ai.vivo.com.cn"
        self.debug_mode = False
        self.session_id = str(uuid.uuid4())  # 在初始化时生成session_id
        
        # 加载预设
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> dict:
        """加载prompt配置，优先YAML格式"""
        return load_prompts()
    
    def set_debug_mode(self, mode: bool = True) -> None:
        """设置调试模式"""
        self.debug_mode = mode
    
    def list_prompts(self) -> Dict[str, Dict[str, str]]:
        """列出所有可用的预设"""
        return self.prompts
    
    def get_prompt(self, type: str) -> Optional[str]:
        """获取指定预设的system prompt"""
        return self.prompts.get(type, {}).get('system')
    
    def _validate_parameters(self, temperature, max_tokens):
        """验证参数"""
        if not 0 < temperature < 2.0:
            raise ValueError("temperature必须在(0,2.0)范围内")
        if not 0 < max_tokens <= 8000:
            raise ValueError("max_tokens必须在(0,8000]范围内")
    
    def _validate_messages(self, messages):
        """验证消息格式"""
        if not messages:
            raise ValueError("messages不能为空")
        
        if len(messages) % 2 == 0:
            raise ValueError("messages必须为奇数个成员")
        
        for i, msg in enumerate(messages):
            if msg.get("role") not in ["user", "assistant"]:
                raise ValueError(f"消息 {i+1} 的role必须是user或assistant")
            if i > 0 and msg["role"] == messages[i-1]["role"]:
                raise ValueError("相邻消息的role不能相同")
        
        if messages[0]["role"] != "user":
            raise ValueError("第一条消息的role必须是user")
    
    def chat(self, prompt: str, type: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2048, stream: bool = False) -> Union[Dict[str, Any], Response]:
        """同步调用蓝心大模型API（单轮对话）"""
        self._validate_parameters(temperature, max_tokens)
        
        if type:
            system_prompt = self.get_prompt(type)
            if system_prompt:
                prompt = f"{system_prompt}\n\n{prompt}"
            else:
                raise ValueError(f"预设 {type} 不存在")
        
        request_id = str(uuid.uuid4())
        uri = "/vivogpt/completions/stream" if stream else "/vivogpt/completions"
        url = f"{self.base_url}{uri}"
        
        query = {"requestId": request_id}
        url_with_params = f"{url}?{AuthUtils.gen_canonical_query_string(query)}"
        
        headers = AuthUtils.gen_sign_headers(self.app_id, self.app_key, "POST", uri, query)
        headers["Content-Type"] = "application/json"
        
        data = {
            "model": "vivo-BlueLM-TB-Pro",
            "prompt": prompt,
            "sessionId": self.session_id,
            "extra": {
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        }
        
        if self.debug_mode:
            print("\n调试信息:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if stream:
            response = requests.post(url_with_params, headers=headers, json=data, stream=True)
            return response
        else:
            response = requests.post(url_with_params, headers=headers, json=data)
            response_data = response.json()
            
            if response_data.get("code") != 0:
                raise VivoGPTError(
                    response_data.get("code"),
                    response_data.get("msg", "未知错误")
                )
            
            return response_data
    
    def chat_with_history(self, messages, temperature=0.7, max_tokens=2048, stream=False):
        """使用多轮对话历史调用蓝心大模型API"""
        self._validate_parameters(temperature, max_tokens)
        self._validate_messages(messages)
        
        request_id = str(uuid.uuid4())
        uri = "/vivogpt/completions/stream" if stream else "/vivogpt/completions"
        url = f"{self.base_url}{uri}"
        
        query = {"requestId": request_id}
        url_with_params = f"{url}?{AuthUtils.gen_canonical_query_string(query)}"
        
        headers = AuthUtils.gen_sign_headers(self.app_id, self.app_key, "POST", uri, query)
        headers["Content-Type"] = "application/json"
        
        data = {
            "model": "vivo-BlueLM-TB-Pro",
            "messages": messages,
            "sessionId": self.session_id,
            "extra": {
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        }
        
        if self.debug_mode:
            print("\n调试信息:")
            print(f"请求URL: {url_with_params}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if stream:
            response = requests.post(url_with_params, headers=headers, json=data, stream=True)
            return response
        else:
            response = requests.post(url_with_params, headers=headers, json=data)
            response_data = response.json()
            
            if response_data.get("code") != 0:
                raise VivoGPTError(
                    response_data.get("code"),
                    response_data.get("msg", "未知错误")
                )
            
            return response_data 