#!/usr/bin/env python
# encoding: utf-8

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from talker.services.chat_service import ChatService
import json
from rest_framework import viewsets, permissions, mixins
from .models import TalkSession
from .serializers import TalkSessionSerializer
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .services.xiaohongshu_summary_service import summary_service

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

class TalkSessionViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    queryset = TalkSession.objects.all().order_by('-created_at')
    serializer_class = TalkSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回当前用户的会话
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """
        用户只需提交最新一条消息，后端自动拼接历史并返回AI回复和完整历史
        请求体：{"message": "..."}
        """
        session = self.get_object()
        history = session.history or []
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": True, "message": "消息不能为空"}, status=400)
        # 拼接历史
        history.append({"role": "user", "content": user_message})
        chat_service = ChatService()
        ai_response = chat_service.process_chat_with_history(
            messages=history,
            state=session.state if session.state else None
        )
        if ai_response.get('error'):
            return Response(ai_response, status=500)
        ai_content = ai_response['data']['content'] if 'data' in ai_response and 'content' in ai_response['data'] else ''
        history.append({"role": "assistant", "content": ai_content})
        session.history = history
        session.save()
        return Response({
            "reply": ai_content,
            "history": history
        })

    @action(detail=True, methods=['post'])
    def remove_history(self, request, pk=None):
        """
        按索引删除会话历史中的一条消息
        请求体：{"index": 3}
        """
        session = self.get_object()
        index = request.data.get('index')
        try:
            index = int(index)
        except (TypeError, ValueError):
            return Response({"error": True, "message": "索引无效"}, status=400)
        history = session.history or []
        if 0 <= index < len(history):
            history.pop(index)
            session.history = history
            session.save()
            return Response({"history": history})
        return Response({"error": True, "message": "索引超出范围"}, status=400)

    @action(detail=False, methods=['post'])
    def new(self, request):
        """
        创建一个新的会话，返回新会话id
        """
        session = TalkSession.objects.create(user=request.user)
        return Response({"id": session.id})

@api_view(['POST'])
def xiaohongshu_summary(request):
    """小红书内容总结API
    
    请求参数:
    - keyword: 搜索关键词 (必需)
    - limit: 搜索笔记数量限制 (可选，默认5)
    - summary_type: 总结类型 (可选，默认general)
        - general: 通用总结
        - food: 美食总结
        - travel: 旅行总结
        - shopping: 购物总结
        - beauty: 美妆总结
    """
    try:
        data = request.data
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return Response({
                'success': False,
                'error': '关键词不能为空'
            }, status=400)
        
        limit = int(data.get('limit', 5))
        summary_type = data.get('summary_type', 'general')
        
        # 验证总结类型
        valid_types = ['general', 'food', 'travel', 'shopping', 'beauty']
        if summary_type not in valid_types:
            return Response({
                'success': False,
                'error': f'总结类型必须是以下之一: {", ".join(valid_types)}'
            }, status=400)
        
        # 异步调用总结服务
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                summary_service.search_and_summarize(keyword, limit, summary_type)
            )
        finally:
            loop.close()
        
        if result['success']:
            return Response(result['data'])
        else:
            return Response({
                'success': False,
                'error': result.get('error', '未知错误')
            }, status=500)
            
    except ValueError as e:
        return Response({
            'success': False,
            'error': f'参数错误: {str(e)}'
        }, status=400)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }, status=500)
