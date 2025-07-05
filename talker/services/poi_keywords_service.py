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
        max_retries = 3  # 最大重试次数
        
        for attempt in range(max_retries):
            try:
                # 准备上下文信息
                context_info = self._prepare_context_info(session_info)
                
                # 格式化对话历史
                formatted_history = self._format_conversation_history(conversation_history)
                
                # 调用大模型生成关键词
                temperature = 0.3 + (attempt * 0.1)  # 重试时稍微增加随机性
                response = self.chat_service.process_chat(
                    message=formatted_history,
                    chat_type="generate_poi_keywords",
                    phase=session_info.get('phase', '未知'),
                    intent=session_info.get('intent', '未知'),
                    context=session_info.get('context', '未知'),
                    collected_info=session_info.get('collected_info', ''),
                    temperature=temperature,
                    max_tokens=1024
                )
                
                if response.get('error'):
                    logging.error(f"大模型调用失败: {response.get('message')}")
                    continue
                
                # 解析响应
                content = response.get('data', {}).get('content', '')
                if not content:
                    continue
                
                # 尝试解析JSON格式的关键词
                try:
                    keywords = json.loads(content)
                    
                    # 验证关键词完整性
                    if self._validate_keywords(keywords, attempt + 1):
                        logging.info(f"关键词生成成功 (尝试 {attempt + 1}/{max_retries})")
                        return keywords
                    else:
                        logging.warning(f"关键词验证失败 (尝试 {attempt + 1}/{max_retries}): primary_keywords或interest_keywords为空")
                        continue
                        
                except json.JSONDecodeError:
                    # 如果不是JSON格式，尝试提取关键词
                    keywords = self._extract_keywords_from_text(content)
                    if self._validate_keywords(keywords, attempt + 1):
                        logging.info(f"关键词提取成功 (尝试 {attempt + 1}/{max_retries})")
                        return keywords
                    else:
                        continue
                        
            except Exception as e:
                logging.error(f"生成POI关键词时发生错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                continue
        
        logging.error(f"关键词生成失败: 所有 {max_retries} 次尝试都失败")
        return None
    
    def _validate_keywords(self, keywords: Dict[str, Any], attempt: int) -> bool:
        """验证关键词完整性
        
        Args:
            keywords: 关键词字典
            attempt: 当前尝试次数
            
        Returns:
            bool: 验证是否通过
        """
        if not keywords or not isinstance(keywords, dict):
            logging.warning(f"关键词格式错误 (尝试 {attempt}): 不是有效的字典")
            return False
        
        # 检查primary_keywords
        primary_keywords = keywords.get('primary_keywords', [])
        if not primary_keywords or not isinstance(primary_keywords, list) or len(primary_keywords) == 0:
            logging.warning(f"关键词验证失败 (尝试 {attempt}): primary_keywords为空或格式错误")
            return False
        
        # 检查interest_keywords
        interest_keywords = keywords.get('interest_keywords', [])
        if not interest_keywords or not isinstance(interest_keywords, list) or len(interest_keywords) == 0:
            logging.warning(f"关键词验证失败 (尝试 {attempt}): interest_keywords为空或格式错误")
            return False
        

        
        # 验证通过
        logging.info(f"关键词验证通过 (尝试 {attempt}): primary_keywords={len(primary_keywords)}个, interest_keywords={len(interest_keywords)}个")
        return True
    
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
        """格式化对话历史 - 只使用最后一次对话"""
        if not conversation_history:
            return "暂无对话历史"
        
        # 只取最后一次对话（最后一个user和最后一个assistant消息）
        last_messages = []
        
        # 从后往前找最后一个用户消息和助手消息
        last_user_msg = None
        last_assistant_msg = None
        
        for message in reversed(conversation_history):
            role = message.get("role")
            if role == "user" and last_user_msg is None:
                last_user_msg = message
            elif role == "assistant" and last_assistant_msg is None:
                last_assistant_msg = message
            
            # 如果两个都找到了，就停止
            if last_user_msg and last_assistant_msg:
                break
        
        # 按正确顺序添加消息（user在前，assistant在后）
        if last_user_msg:
            content = last_user_msg.get("content", "")
            last_messages.append(f"用户: {content}")
        
        if last_assistant_msg:
            content = last_assistant_msg.get("content", "")
            last_messages.append(f"助手: {content}")
        
        if not last_messages:
            return "暂无有效对话历史"
        
        return "\n".join(last_messages)
    
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