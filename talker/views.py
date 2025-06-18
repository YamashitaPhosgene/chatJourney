#!/usr/bin/env python
# encoding: utf-8

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from talker.services.chat_service import ChatService
import json

@method_decorator(csrf_exempt, name='dispatch')
class ChatView(View):
    """聊天视图"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def post(self, request):
        """处理聊天请求
        
        请求体格式：
        {
            "message": "用户消息",
            "chat_type": "聊天类型（可选）",
            "temperature": 0.7,
            "max_tokens": 2048
        }
        """
        try:
            data = json.loads(request.body)
            message = data.get('message')
            chat_type = data.get('chat_type')
            temperature = float(data.get('temperature', 0.7))
            max_tokens = int(data.get('max_tokens', 2048))
            
            if not message:
                return JsonResponse({
                    "error": True,
                    "message": "消息不能为空"
                }, status=400)
            
            response = self.chat_service.process_chat(
                message=message,
                chat_type=chat_type,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "error": True,
                "message": "无效的JSON格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": True,
                "message": str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatHistoryView(View):
    """带历史记录的聊天视图"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def post(self, request):
        """处理带历史记录的聊天请求
        
        请求体格式：
        {
            "messages": [
                {"role": "user", "content": "用户消息1"},
                {"role": "assistant", "content": "助手回复1"},
                {"role": "user", "content": "用户消息2"}
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        """
        try:
            data = json.loads(request.body)
            messages = data.get('messages', [])
            temperature = float(data.get('temperature', 0.7))
            max_tokens = int(data.get('max_tokens', 2048))
            
            if not messages:
                return JsonResponse({
                    "error": True,
                    "message": "消息历史不能为空"
                }, status=400)
            
            response = self.chat_service.process_chat_with_history(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "error": True,
                "message": "无效的JSON格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "error": True,
                "message": str(e)
            }, status=500)
