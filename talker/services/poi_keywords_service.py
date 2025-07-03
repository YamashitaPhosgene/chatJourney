#!/usr/bin/env python
# encoding: utf-8

import threading
import json
import logging
from typing import Dict, Any, Optional
from talker.services.chat_service import ChatService

class POIKeywordsService:
    """POI关键词生成服务"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def generate_keywords_async(self, conversation_history: list, session_info: Dict[str, Any], callback_func=None):
        """异步生成POI关键词
        
        Args:
            conversation_history: 对话历史
            session_info: 会话信息
            callback_func: 回调函数，用于处理生成的关键词
        """
        def _generate():
            try:
                keywords = self._generate_keywords(conversation_history, session_info)
                if callback_func:
                    callback_func(keywords)
            except Exception as e:
                logging.error(f"生成POI关键词失败: {e}")
                if callback_func:
                    callback_func(None)
        
        # 启动异步线程
        thread = threading.Thread(target=_generate)
        thread.daemon = True
        thread.start()
    
    def _generate_keywords(self, conversation_history: list, session_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成POI关键词
        
        Args:
            conversation_history: 对话历史
            session_info: 会话信息
            
        Returns:
            关键词字典或None
        """
        try:
            # 准备上下文信息
            context_info = self._prepare_context_info(session_info)
            
            # 格式化对话历史
            formatted_history = self._format_conversation_history(conversation_history)
            
            # 调用大模型生成关键词
            response = self.chat_service.process_chat(
                message=formatted_history,
                chat_type="generate_poi_keywords",
                phase=session_info.get('phase', '未知'),
                intent=session_info.get('intent', '未知'),
                context=session_info.get('context', '未知'),
                collected_info=session_info.get('collected_info', ''),
                temperature=0.3,  # 使用较低的温度以获得更稳定的输出
                max_tokens=1024
            )
            
            if response.get('error'):
                logging.error(f"大模型调用失败: {response.get('message')}")
                return None
            
            # 解析响应
            content = response.get('data', {}).get('content', '')
            if not content:
                return None
            
            # 尝试解析JSON格式的关键词
            try:
                keywords = json.loads(content)
                return keywords
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试提取关键词
                return self._extract_keywords_from_text(content)
                
        except Exception as e:
            logging.error(f"生成POI关键词时发生错误: {e}")
            return None
    
    def _prepare_context_info(self, session_info: Dict[str, Any]) -> str:
        """准备上下文信息"""
        context_parts = []
        
        if session_info.get('locations'):
            context_parts.append(f"目的地: {session_info['locations']}")
        
        if session_info.get('budget'):
            context_parts.append(f"预算: {session_info['budget']}")
        
        if session_info.get('start_date') and session_info.get('end_date'):
            context_parts.append(f"时间: {session_info['start_date']} 到 {session_info['end_date']}")
        
        if session_info.get('user_profile'):
            context_parts.append(f"用户画像: {session_info['user_profile']}")
        
        return '; '.join(context_parts) if context_parts else "暂无收集信息"
    
    def _format_conversation_history(self, conversation_history: list) -> str:
        """格式化对话历史"""
        if not conversation_history:
            return "暂无对话历史"
        
        formatted_messages = []
        for message in conversation_history:
            role = "用户" if message.get("role") == "user" else "助手"
            content = message.get("content", "")
            formatted_messages.append(f"{role}: {content}")
        
        return "\n".join(formatted_messages)
    
    def _extract_keywords_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取关键词（备用方案）"""
        # 简单的关键词提取逻辑
        keywords = {
            "primary_keywords": [],
            "secondary_keywords": [],
            "city_keywords": [],
            "interest_keywords": [],
            "search_suggestions": []
        }
        
        # 这里可以添加更复杂的文本解析逻辑
        # 暂时返回空的关键词结构
        return keywords 