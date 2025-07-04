#!/usr/bin/env python
# encoding: utf-8

from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from talker.services.chat_service import ChatService
from talker.services.state_machine import TravelAssistantFSM
from talker.models import TalkSession
import json
from rest_framework import viewsets, permissions, mixins
from .serializers import TalkSessionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .services.xiaohongshu_summary_service import summary_service
import logging

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
            message = data.get('message', '')
            chat_type = data.get('chat_type')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 2048)
            
            if not message:
                return JsonResponse({
                    'error': True,
                    'message': '消息不能为空'
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
                'error': True,
                'message': '无效的JSON格式'
            }, status=400)
        except Exception as e:
            logging.error(f"聊天处理错误: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StateMachineView(View):
    """状态机视图"""
    
    def post(self, request):
        """处理状态机请求
        
        请求体格式：
        {
            "session_id": "会话ID",
            "message": "用户消息",
            "stream": false  // 是否使用流式接口
        }
        """
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            message = data.get('message', '')
            stream = data.get('stream', False)
            
            if not session_id:
                return JsonResponse({
                    'error': True,
                    'message': 'session_id不能为空'
                }, status=400)
            
            if not message:
                return JsonResponse({
                    'error': True,
                    'message': '消息不能为空'
                }, status=400)
            
            # 加载会话
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                return JsonResponse({
                    'error': True,
                    'message': '会话不存在'
                }, status=404)
            
            if stream:
                # 检查Accept头部，如果明确要求SSE，就返回真正的流式
                accept_header = request.META.get('HTTP_ACCEPT', '')
                wants_sse = 'text/event-stream' in accept_header
                
                if wants_sse:
                    # 客户端明确要求SSE，返回真正的流式响应
                    return self._handle_stream_response(fsm, message)
                else:
                    # 否则返回完整结果供前端模拟流式
                    full_content = ""
                    try:
                        for chunk in fsm.handle_utterance_stream(message):
                            if chunk['type'] == 'content':
                                full_content += chunk.get('chunk', '')
                            elif chunk['type'] in ['done', 'end', 'completed']:
                                full_content = chunk.get('full_content', full_content)
                                break
                            elif chunk['type'] == 'error':
                                return JsonResponse({
                                    'error': True,
                                    'message': chunk.get('error', '处理错误'),
                                    'current_state': fsm.state,
                                    'slots': fsm.slots,
                                    'state_info': fsm.session.state
                                }, status=500)
                        
                        return JsonResponse({
                            'response': full_content,
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        })
                    except Exception as e:
                        logging.error(f"模拟流式处理错误: {e}")
                        return JsonResponse({
                            'error': True,
                            'message': str(e),
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        }, status=500)
            else:
                # 同步处理
                response = fsm.handle_utterance(message)
                return JsonResponse({
                    'response': response,
                    'current_state': fsm.state,
                    'slots': fsm.slots,
                    'state_info': fsm.session.state
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': True,
                'message': '无效的JSON格式'
            }, status=400)
        except Exception as e:
            logging.error(f"状态机处理错误: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)
    
    def _handle_stream_response(self, fsm: TravelAssistantFSM, message: str):
        """处理流式响应"""
        def generate():
            try:
                for chunk in fsm.handle_utterance_stream(message):
                    if chunk['type'] == 'content':
                        # 发送内容块
                        yield f"data: {json.dumps({'type': 'content', 'chunk': chunk['chunk'], 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                    elif chunk['type'] == 'done':
                        # 发送完成信号
                        yield f"data: {json.dumps({'type': 'done', 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                    elif chunk['type'] == 'end':
                        # 发送结束信号（用于状态转换）
                        yield f"data: {json.dumps({'type': 'end', 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                    elif chunk['type'] == 'error':
                        # 发送错误信号
                        yield f"data: {json.dumps({'type': 'error', 'error': chunk['error'], 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                        yield "event: error\ndata: [DONE]\n\n"
                        return
                    elif chunk['type'] == 'event':
                        # 发送事件信号
                        yield f"event: {chunk['event']}\ndata: {json.dumps(chunk['data'], ensure_ascii=False)}\n\n"
                    elif chunk['type'] == 'completed':
                        # 发送完成状态信号
                        yield f"data: {json.dumps({'type': 'completed', 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                        
            except Exception as e:
                logging.error(f"流式响应生成错误: {e}")
                error_data = json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
                yield "event: error\ndata: [DONE]\n\n"
        
        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

@method_decorator(csrf_exempt, name='dispatch')
class SessionView(View):
    """会话管理视图"""
    
    def post(self, request):
        """创建新会话
        
        请求体格式：
        {
            "username": "用户名（可选）"
        }
        """
        try:
            data = json.loads(request.body)
            username = data.get('username', 'fangsuo')
            
            fsm = TravelAssistantFSM()
            session_id = fsm.create_new_session(username)
            
            return JsonResponse({
                'session_id': session_id,
                'message': '会话创建成功'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': True,
                'message': '无效的JSON格式'
            }, status=400)
        except Exception as e:
            logging.error(f"创建会话错误: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)
    
    def get(self, request, session_id):
        """获取会话信息"""
        try:
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                return JsonResponse({
                    'error': True,
                    'message': '会话不存在'
                }, status=404)
            
            session_info = fsm.get_session_info()
            slots_info = fsm.get_slots_info()
            
            return JsonResponse({
                'session_info': session_info,
                'slots_info': slots_info,
                'current_state': fsm.state
            })
            
        except Exception as e:
            logging.error(f"获取会话信息错误: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ChatStreamView(View):
    """聊天流式视图（直接与大模型通信）"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    def post(self, request):
        """处理流式聊天请求
        
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
            message = data.get('message', '')
            chat_type = data.get('chat_type')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 2048)
            
            if not message:
                return JsonResponse({
                    'error': True,
                    'message': '消息不能为空'
                }, status=400)
            
            def generate():
                try:
                    response_stream = self.chat_service.process_chat(
                        message=message,
                        chat_type=chat_type,
                temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
            )
            
                    for chunk in response_stream:
                        if chunk['type'] == 'content':
                            # 发送内容块
                            yield f"data: {json.dumps({'message': chunk['chunk']}, ensure_ascii=False)}\n\n"
                        elif chunk['type'] == 'done':
                            # 发送完成信号
                            yield "event: close\ndata: [DONE]\n\n"
                            return
                        elif chunk['type'] == 'event':
                            # 发送事件信号
                            yield f"event: {chunk['event']}\ndata: {json.dumps(chunk['data'], ensure_ascii=False)}\n\n"
                            
                except Exception as e:
                    logging.error(f"流式聊天处理错误: {e}")
                    error_data = json.dumps({'code': -1, 'msg': str(e)}, ensure_ascii=False)
                    yield f"event: error\ndata: {error_data}\n\n"
            
            response = StreamingHttpResponse(
                generate(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': True,
                'message': '无效的JSON格式'
            }, status=400)
        except Exception as e:
            logging.error(f"流式聊天处理错误: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
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

def xiaohongshu_summary(request):
    """小红书总结接口"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url')
            if not url:
                return JsonResponse({'error': 'URL不能为空'}, status=400)
            
            result = summary_service.summarize_url(url)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON格式'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '只支持POST请求'}, status=405)

# -------------------- ChatHistoryView --------------------

@method_decorator(csrf_exempt, name='dispatch')
class ChatHistoryView(View):
    """返回指定会话的完整对话历史"""
    
    def get(self, request):
        """GET /api/chat/history/?session_id=xxx

        返回格式：
        {
          "session_id": "...",
          "history": [ {"role":"user","content":"..."}, ... ]
        }
        """
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({
                'error': True,
                'message': 'session_id 必填'
            }, status=400)

        try:
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                return JsonResponse({
                    'error': True,
                    'message': '会话不存在'
                }, status=404)
            
            history = fsm.get_conversation_history()
            return JsonResponse({
                'session_id': session_id,
                'history': history
            })
        except Exception as e:
            logging.error(f"获取历史失败: {e}")
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)
