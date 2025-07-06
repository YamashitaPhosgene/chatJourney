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
from talker.services.timeline_service import TimelineService
from django.views.decorators.http import require_http_methods, require_POST, require_GET


@method_decorator(csrf_exempt, name="dispatch")
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
            message = data.get("message", "")
            chat_type = data.get("chat_type")
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 2048)
            
            if not message:
                return JsonResponse(
                    {"error": True, "message": "消息不能为空"}, status=400
                )
            
            response = self.chat_service.process_chat(
                message=message,
                chat_type=chat_type,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"聊天处理错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
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
            session_id = data.get("session_id")
            message = data.get("message", "")
            stream = data.get("stream", False)
            
            if not session_id:
                return JsonResponse(
                    {"error": True, "message": "session_id不能为空"}, status=400
                )
            
            if not message:
                return JsonResponse(
                    {"error": True, "message": "消息不能为空"}, status=400
                )
            
            # 加载会话
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )
            
            if stream:
                # 检查Accept头部，如果明确要求SSE，就返回真正的流式
                accept_header = request.META.get("HTTP_ACCEPT", "")
                wants_sse = "text/event-stream" in accept_header
                
                if wants_sse:
                    # 客户端明确要求SSE，返回真正的流式响应
                    return self._handle_stream_response(fsm, message)
                else:
                    # 否则返回完整结果供前端模拟流式
                    full_content = ""
                    try:
                        for chunk in fsm.handle_utterance_stream(message):
                            if chunk["type"] == "content":
                                full_content += chunk.get("chunk", "")
                            elif chunk["type"] in ["done", "end", "completed"]:
                                full_content = chunk.get("full_content", full_content)
                                break
                            elif chunk["type"] == "error":
                                return JsonResponse(
                                    {
                                        "error": True,
                                        "message": chunk.get("error", "处理错误"),
                                        "current_state": fsm.state,
                                        "slots": fsm.slots,
                                        "state_info": fsm.session.state,
                                    },
                                    status=500,
                                )

                        # 注意：流式方法内部已经保存了消息，这里不需要重复保存
                        # 但为了确保一致性，如果full_content不为空且历史记录中没有对应的助手消息，则保存
                        if full_content:
                            conversation = fsm.get_conversation_history()
                            # 检查最后一条消息是否是助手消息且内容匹配
                            if not conversation or conversation[-1].get('role') != 'assistant' or conversation[-1].get('content') != full_content:
                                logging.warning(f"流式处理后发现助手消息未保存，手动保存: {full_content[:50]}...")
                                fsm.add_assistant_message(full_content)

                        return JsonResponse(
                            {
                                "response": full_content,
                                "current_state": fsm.state,
                                "slots": fsm.slots,
                                "state_info": fsm.session.state,
                            }
                        )
                    except Exception as e:
                        logging.error(f"模拟流式处理错误: {e}")
                        return JsonResponse(
                            {
                                "error": True,
                                "message": str(e),
                                "current_state": fsm.state,
                                "slots": fsm.slots,
                                "state_info": fsm.session.state,
                            },
                            status=500,
                        )
            else:
                # 同步处理
                response = fsm.handle_utterance(message)
                
                # 注意：handle_utterance内部已经保存了消息，不需要重复保存
                
                return JsonResponse(
                    {
                        "response": response,
                        "current_state": fsm.state,
                        "slots": fsm.slots,
                        "state_info": fsm.session.state,
                    }
                )
                
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"状态机处理错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)
    
    def _handle_stream_response(self, fsm: TravelAssistantFSM, message: str):
        """处理流式响应"""

        def generate():
            try:
                for chunk in fsm.handle_utterance_stream(message):
                    if chunk["type"] == "content":
                        # 发送内容块
                        yield f"data: {json.dumps({'type': 'content', 'chunk': chunk['chunk'], 'full_content': chunk['full_content']}, ensure_ascii=False)}\n\n"
                    elif chunk["type"] == "done":
                        # 发送完成信号，包含状态信息
                        response_data = {
                            'type': 'done', 
                            'full_content': chunk['full_content'],
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                    elif chunk["type"] == "end":
                        # 发送结束信号（用于状态转换），包含状态信息
                        response_data = {
                            'type': 'end', 
                            'full_content': chunk['full_content'],
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                    elif chunk["type"] == "error":
                        # 发送错误信号，包含状态信息
                        response_data = {
                            'type': 'error', 
                            'error': chunk['error'], 
                            'full_content': chunk['full_content'],
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
                        yield "event: error\ndata: [DONE]\n\n"
                        return
                    elif chunk["type"] == "event":
                        # 发送事件信号
                        yield f"event: {chunk['event']}\ndata: {json.dumps(chunk['data'], ensure_ascii=False)}\n\n"
                    elif chunk["type"] == "completed":
                        # 发送完成状态信号，包含状态信息
                        response_data = {
                            'type': 'completed', 
                            'full_content': chunk['full_content'],
                            'current_state': fsm.state,
                            'slots': fsm.slots,
                            'state_info': fsm.session.state
                        }
                        yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
                        yield "event: close\ndata: [DONE]\n\n"
                        return
                        
            except Exception as e:
                logging.error(f"流式响应生成错误: {e}")
                error_data = json.dumps(
                    {"type": "error", "error": str(e)}, ensure_ascii=False
                )
                yield f"data: {error_data}\n\n"
                yield "event: error\ndata: [DONE]\n\n"
        
        response = StreamingHttpResponse(generate(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


@method_decorator(csrf_exempt, name="dispatch")
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
            username = data.get("username", "fangsuo")
            
            fsm = TravelAssistantFSM()
            session_id = fsm.create_new_session(username)
            
            return JsonResponse({"session_id": session_id, "message": "会话创建成功"})
            
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"创建会话错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)
    
    def get(self, request, session_id):
        """获取会话信息"""
        try:
            logging.info(f"获取会话信息请求: session_id={session_id}")
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                logging.warning(f"会话不存在: session_id={session_id}")
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )
            
            session_info = fsm.get_session_info()
            slots_info = fsm.get_slots_info()
            
            logging.info(
                f"获取会话信息成功: session_id={session_id}, state={fsm.state}, session.state={fsm.session.state}"
            )

            return JsonResponse(
                {
                    "session_info": session_info,
                    "slots_info": slots_info,
                    "current_state": fsm.state,
                }
            )
            
        except Exception as e:
            logging.error(f"获取会话信息错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
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
            message = data.get("message", "")
            chat_type = data.get("chat_type")
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 2048)
            
            if not message:
                return JsonResponse(
                    {"error": True, "message": "消息不能为空"}, status=400
                )
            
            def generate():
                try:
                    response_stream = self.chat_service.process_chat(
                        message=message,
                        chat_type=chat_type,
                temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True,
            )
            
                    for chunk in response_stream:
                        if chunk["type"] == "content":
                            # 发送内容块
                            yield f"data: {json.dumps({'message': chunk['chunk']}, ensure_ascii=False)}\n\n"
                        elif chunk["type"] == "done":
                            # 发送完成信号
                            yield "event: close\ndata: [DONE]\n\n"
                            return
                        elif chunk["type"] == "event":
                            # 发送事件信号
                            yield f"event: {chunk['event']}\ndata: {json.dumps(chunk['data'], ensure_ascii=False)}\n\n"
                            
                except Exception as e:
                    logging.error(f"流式聊天处理错误: {e}")
                    error_data = json.dumps(
                        {"code": -1, "msg": str(e)}, ensure_ascii=False
                    )
                    yield f"event: error\ndata: {error_data}\n\n"
            
            response = StreamingHttpResponse(
                generate(), content_type="text/event-stream"
            )
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response
            
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"流式聊天处理错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


class TalkSessionViewSet(
    mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = TalkSession.objects.all().order_by("-created_at")
    serializer_class = TalkSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回当前用户的会话
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        """
        用户只需提交最新一条消息，后端自动拼接历史并返回AI回复和完整历史
        请求体：{"message": "..."}
        """
        session = self.get_object()
        history = session.history or []
        user_message = request.data.get("message")
        if not user_message:
            return Response({"error": True, "message": "消息不能为空"}, status=400)
        # 拼接历史
        history.append({"role": "user", "content": user_message})
        chat_service = ChatService()
        ai_response = chat_service.process_chat_with_history(
            messages=history, state=session.state if session.state else None
        )
        if ai_response.get("error"):
            return Response(ai_response, status=500)
        ai_content = (
            ai_response["data"]["content"]
            if "data" in ai_response and "content" in ai_response["data"]
            else ""
        )
        history.append({"role": "assistant", "content": ai_content})
        session.history = history
        session.save()
        return Response({"reply": ai_content, "history": history})


def xiaohongshu_summary(request):
    """小红书总结接口"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            url = data.get("url")
            if not url:
                return JsonResponse({"error": "URL不能为空"}, status=400)
            
            result = summary_service.summarize_url(url)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "无效的JSON格式"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "只支持POST请求"}, status=405)

@method_decorator(csrf_exempt, name="dispatch")
class BudgetAnalysisView(View):
    """预算分析视图"""
    
    def __init__(self):
        from talker.services.poi_management import POIManagementService
        self.poi_service = POIManagementService()
    
    def get(self, request):
        """获取预算分析
        
        参数：
        - session_id: 会话ID
        """
        try:
            session_id = request.GET.get("session_id")
            
            if not session_id:
                return JsonResponse(
                    {"error": True, "message": "session_id参数是必需的"}, status=400
                )
            
            # 验证会话是否存在并获取预算信息
            try:
                session = TalkSession.objects.get(id=session_id)
                fsm = TravelAssistantFSM()
                fsm.load_session(session_id)
                
                # 获取预算信息
                budget_value = None
                budget_type = "empty"  # empty, specific, range, unlimited, limited
                budget_min = 0
                budget_max = 0
                
                if fsm.slots and 'budget' in fsm.slots:
                    budget_str = str(fsm.slots['budget']).strip()
                    if budget_str and budget_str.lower() not in ['null', 'none', '']:
                        if budget_str in ['任意', '不限', '无限制']:
                            budget_type = "unlimited"
                        elif budget_str in ['有限', '预算有限', '钱不多']:
                            budget_type = "limited"
                        elif '-' in budget_str:
                            # 范围预算，如 "5000-7000"
                            try:
                                parts = budget_str.split('-')
                                budget_min = float(parts[0])
                                budget_max = float(parts[1]) if len(parts) > 1 else budget_min * 1.5
                                budget_type = "range"
                            except ValueError:
                                budget_type = "empty"
                        else:
                            # 具体数字
                            try:
                                budget_value = float(budget_str)
                                budget_type = "specific"
                                budget_max = budget_value
                            except ValueError:
                                budget_type = "empty"
                
            except TalkSession.DoesNotExist:
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )
            
            # 获取会话的POI列表并计算已考虑的预算
            poi_items = self.poi_service.get_session_pois(session)
            
            # 按类型分类计算预算
            budget_breakdown = {
                "住宿": 0,
                "餐饮": 0,
                "景点": 0,
                "娱乐": 0,
                "购物": 0,
                "交通": 0,  # 预留给后续交通API计算
            }
            
            poi_costs = []  # 记录每个POI的费用信息
            
            for poi_item in poi_items:
                if poi_item.raw_data:
                    try:
                        raw_data = poi_item.raw_data
                        business = raw_data.get("business", {})
                        cost_str = business.get("cost", "")
                        
                        if cost_str and cost_str != "":
                            # 解析费用信息，提取数字
                            cost_value = self._extract_cost_value(cost_str)
                            if cost_value > 0:
                                # 根据POI类型分类
                                poi_category = self._categorize_poi(poi_item, raw_data)
                                budget_breakdown[poi_category] += cost_value
                                
                                poi_costs.append({
                                    "name": poi_item.name,
                                    "category": poi_category,
                                    "cost": cost_value,
                                    "cost_str": cost_str,
                                    "type": poi_item.type
                                })
                    except (TypeError, AttributeError):
                        continue
            
            # 计算总的已考虑预算
            total_considered = sum(budget_breakdown.values())
            
            # 构建图表数据
            chart_data = []
            colors = {
                "住宿": "#e6c36f",
                "餐饮": "#8fd3c7", 
                "景点": "#f7a35c",
                "娱乐": "#ff9999",
                "购物": "#c7a9dd",
                "交通": "#95d4f4"
            }
            
            for category, amount in budget_breakdown.items():
                if amount > 0:  # 只显示有费用的类别
                    chart_data.append({
                        "name": category,
                        "value": amount,
                        "color": colors.get(category, "#cccccc")
                    })
            
            # 如果有预算限制，添加剩余预算
            remaining_budget = 0
            if budget_type in ["specific", "range"] and budget_max > 0:
                remaining_budget = max(0, budget_max - total_considered)
                if remaining_budget > 0:
                    chart_data.append({
                        "name": "剩余预算",
                        "value": remaining_budget,
                        "color": "#e0e0e0"
                    })
            
            # 如果没有任何数据，显示一个完整的圆环
            if not chart_data:
                chart_data = [{
                    "name": "预算待分配",
                    "value": budget_max if budget_max > 0 else 1000,
                    "color": "#e0e0e0"
                }]
            
            return JsonResponse({
                "budget_type": budget_type,
                "budget_value": budget_value,
                "budget_min": budget_min,
                "budget_max": budget_max,
                "total_considered": total_considered,
                "remaining_budget": remaining_budget,
                "budget_breakdown": budget_breakdown,
                "chart_data": chart_data,
                "poi_costs": poi_costs,
                "poi_count": len(poi_items)
            })
            
        except Exception as e:
            logging.error(f"预算分析失败: {e}")
            return JsonResponse(
                {"error": True, "message": f"预算分析失败: {str(e)}"}, status=500
            )
    
    def _extract_cost_value(self, cost_str: str) -> float:
        """从费用字符串中提取数字值"""
        import re
        
        # 移除常见的货币符号和单位
        cost_str = cost_str.replace('¥', '').replace('元', '').replace('￥', '')
        cost_str = cost_str.replace('人均', '').replace('约', '').strip()
        
        # 查找数字
        numbers = re.findall(r'\d+\.?\d*', cost_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return 0
    
    def _categorize_poi(self, poi_item, raw_data: dict) -> str:
        """根据POI信息判断类别"""
        poi_type = poi_item.type or ""
        poi_name = poi_item.name or ""
        
        # 根据type字段判断
        if "住宿" in poi_type or "酒店" in poi_type or "宾馆" in poi_type:
            return "住宿"
        elif "餐饮" in poi_type or "美食" in poi_type or "饭店" in poi_type or "餐厅" in poi_type:
            return "餐饮"
        elif "景点" in poi_type or "旅游" in poi_type or "博物馆" in poi_type or "公园" in poi_type:
            return "景点"
        elif "购物" in poi_type or "商场" in poi_type or "超市" in poi_type:
            return "购物"
        elif "娱乐" in poi_type or "KTV" in poi_type or "酒吧" in poi_type:
            return "娱乐"
        
        # 根据名称判断
        if any(keyword in poi_name for keyword in ["酒店", "宾馆", "客栈", "民宿"]):
            return "住宿"
        elif any(keyword in poi_name for keyword in ["饭店", "餐厅", "食府", "茶楼", "火锅", "小吃"]):
            return "餐饮"
        elif any(keyword in poi_name for keyword in ["景区", "公园", "博物馆", "寺庙", "古迹"]):
            return "景点"
        elif any(keyword in poi_name for keyword in ["商场", "超市", "店铺", "市场"]):
            return "购物"
        elif any(keyword in poi_name for keyword in ["KTV", "酒吧", "夜店", "娱乐"]):
            return "娱乐"
        
        # 默认分类为景点
        return "景点"


@method_decorator(csrf_exempt, name="dispatch")
class DestinationRecommendationView(View):
    """目的地推荐接口"""
    
    def __init__(self):
        from django.core.cache import cache
        self.cache = cache
    
    def get(self, request, session_id=None):
        """获取目的地推荐
        
        URL参数：
        - session_id: 会话ID（可选）
        
        查询参数：
        - count: 推荐数量，默认3
        - user_profile: 用户画像，如"亲子游"、"美食爱好者"等
        - budget_range: 预算范围，如"low"、"medium"、"high"
        """
        try:
            count = int(request.GET.get("count", 3))
            user_profile = request.GET.get("user_profile", "")
            budget_range = request.GET.get("budget_range", "medium")
            
            # 限制推荐数量
            count = min(max(count, 1), 10)
            
            # 如果有session_id，获取会话信息
            session_info = {}
            conversation = []
            
            if session_id:
                try:
                    fsm = TravelAssistantFSM()
                    if fsm.load_session(session_id):
                        session_info = fsm.get_session_info()
                        conversation = fsm.get_conversation_history()
                        
                        # 从会话状态中获取用户画像
                        if fsm.slots.get("profile") and not user_profile:
                            user_profile = fsm.slots["profile"]
                            
                        logging.info(f"获取会话 {session_id} 信息成功")
                    else:
                        logging.warning(f"会话 {session_id} 不存在，使用默认推荐")
                except Exception as e:
                    logging.error(f"获取会话信息失败: {e}")
            
            # 构建推荐请求的对话历史
            if not conversation:
                # 如果没有对话历史，构建一个基于用户画像的虚拟对话
                conversation = [
                    {
                        "role": "user",
                        "content": f"我想要{user_profile}的旅游推荐，预算{budget_range}",
                    }
                ]
            
            # 使用POI搜索管道进行目的地推荐
            from hunter.services.poi_search_pipeline import POISearchPipeline

            print(
                f"[DEBUG] 开始POI搜索管道, conversation: {conversation[:1] if conversation else []}"
            )
            print(f"[DEBUG] session_info: {session_info}")
            
            pipeline = POISearchPipeline()
            result = pipeline.search_by_conversation(conversation, session_info)
            
            print(
                f"[DEBUG] POI搜索管道完成, result keys: {list(result.keys()) if result else 'None'}"
            )
            print(
                f"[DEBUG] POI搜索结果: pois数量={len(result.get('pois', {}))}, adcode={result.get('adcode')}"
            )
            if result.get("error"):
                print(f"[DEBUG] POI搜索出错: {result['error']}")

            # 处理搜索结果，转换为推荐格式
            recommendations, cached_pois = self._process_search_result(
                result, count, user_profile, budget_range
            )

            print(
                f"[DEBUG] 推荐结果处理完成, recommendations数量: {len(recommendations)}"
            )

            # 缓存搜索结果供后续添加POI使用
            if session_id and cached_pois:
                cache_key = f"poi_search_result_{session_id}"
                self.cache.set(cache_key, cached_pois, timeout=3600)  # 缓存1小时
                print(f"[DEBUG] 已缓存 {len(cached_pois)} 个POI搜索结果，key: {cache_key}")

            return JsonResponse(
                {
                    "recommendations": recommendations,
                    "total": len(recommendations),
                    "user_profile": user_profile,
                    "budget_range": budget_range,
                    "source": "poi_pipeline",
                }
            )
            
        except Exception as e:
            logging.error(f"目的地推荐处理错误: {e}")
            return JsonResponse(
                {"error": True, "message": str(e), "recommendations": []}, status=500
            )

    def _process_search_result(
        self, search_result: dict, count: int, user_profile: str, budget_range: str
    ) -> tuple:
        """处理POI搜索结果，转换为推荐格式（简化版：直接收集所有POI并去重）
        
        Returns:
            tuple: (recommendations, cached_pois) 推荐列表和用于缓存的POI数据
        """
        recommendations = []
        cached_pois = []  # 用于缓存的完整POI数据
        seen_pois = set()  # 用于去重，基于POI的name+address
        pois = search_result.get("pois", {})

        print(
            f"[DEBUG] 开始处理POI搜索结果, pois结构: {list(pois.keys()) if pois else 'empty'}"
        )

        # 收集所有POI（不按分组处理）
        all_pois = []
        for keyword, keyword_bucket in pois.items():
            print(f"[DEBUG] 处理关键词: {keyword}")
            if keyword_bucket:
                for code, code_pois in keyword_bucket.items():
                    if code_pois:
                        all_pois.extend(code_pois)

        print(f"[DEBUG] 收集到的POI总数: {len(all_pois)}")

        # 直接处理所有POI
        poi_index = 0
        for poi in all_pois:
            if "error" in poi:
                print(f"[DEBUG] 跳过错误POI: {poi.get('error', '未知错误')}")
                continue

            poi_name = poi.get("name", "未知")
            poi_address = poi.get("address", "")
            poi_key = f"{poi_name}|{poi_address}"  # 使用name+address作为唯一标识

            print(
                f"[DEBUG] 处理POI: {poi_name}, typecode: {poi.get('typecode', 'N/A')}"
            )

            # 检查是否已经处理过这个POI
            if poi_key in seen_pois:
                print(f"[DEBUG] 跳过重复POI: {poi_name}")
                continue
                    
            # 格式化POI为推荐
            recommendation = self._format_recommendation(
                poi, user_profile, budget_range
            )
            if recommendation:
                # 添加POI索引到推荐中
                recommendation['poi_index'] = poi_index
                
                recommendations.append(recommendation)
                cached_pois.append(poi)  # 保存完整的POI数据用于缓存
                seen_pois.add(poi_key)
                
                print(f"[DEBUG] 添加推荐: {recommendation.get('title', '未知')}, index: {poi_index}")
                
                poi_index += 1
                
                # 检查是否达到数量上限
                if len(recommendations) >= count:
                    print(f"[DEBUG] 达到请求数量上限: {count}")
                    break
            else:
                print(f"[DEBUG] 格式化失败: {poi_name}")
        
        # 返回推荐列表和缓存数据
        print(f"[DEBUG] POI搜索结果处理完成, 最终推荐数量: {len(recommendations)}, 缓存POI数量: {len(cached_pois)}")
        return recommendations, cached_pois
    
    def _is_destination_poi(self, poi: dict) -> bool:
        """判断POI是否为目的地类型"""
        typecode = poi.get("typecode", "")
        name = poi.get("name", "").lower()
        
        # 目的地相关的分类码
        destination_codes = [
            "11",  # 风景名胜
            "12",  # 旅游景点
            "13",  # 公园广场
            "14",  # 文化场所
            "15",  # 体育休闲
            "16",  # 娱乐场所
        ]
        
        # 检查分类码
        for code in destination_codes:
            if typecode.startswith(code):
                logging.debug(
                    f"POI {name} 匹配目的地分类码: {code} (完整码: {typecode})"
                )
                return True
        
        # 检查名称关键词
        destination_keywords = [
            "景区",
            "公园",
            "广场",
            "博物馆",
            "寺庙",
            "古镇",
            "山",
            "湖",
            "海",
            "岛",
        ]
        for keyword in destination_keywords:
            if keyword in name:
                logging.debug(f"POI {name} 匹配目的地关键词: {keyword}")
                return True
        
        logging.debug(f"POI {name} 不匹配目的地类型, typecode: {typecode}")
        return False
    
    def _format_recommendation(
        self, poi: dict, user_profile: str, budget_range: str
    ) -> dict:
        """格式化推荐信息"""

        try:
            # 添加调试信息
            poi_id = poi.get("id", "")
            poi_name = poi.get("name", "未知景点")
            logging.info(f"格式化POI推荐: name={poi_name}, id={poi_id}")
            logging.info(f"POI原始数据字段: {list(poi.keys())}")

            # 根据预算范围设置评分
            score_map = {"low": 4.2, "medium": 4.5, "high": 4.8}
            base_score = score_map.get(budget_range, 4.5)
            
            # 处理图片信息
            image_url = "/static/images/flower.jpg"  # 默认图片
            photos = poi.get("photos", [])
            if photos and len(photos) > 0:
                # 取第一张图片
                first_photo = photos[0]
                if isinstance(first_photo, dict) and "url" in first_photo:
                    image_url = first_photo["url"]
                elif isinstance(first_photo, str):
                    image_url = first_photo
            
            # 处理评分信息
            rating = (
                poi.get("business", {}).get("rating", None) if poi.get("business") else None
            )
            if rating is not None:
                try:
                    score = float(rating)
                except (ValueError, TypeError):
                    score = round(base_score + (hash(poi.get("name", "")) % 6) / 10, 1)
            else:
                score = round(base_score + (hash(poi.get("name", "")) % 6) / 10, 1)
            
            # 处理电话信息
            tel = poi.get("tel", "")
            if not tel and poi.get("business"):
                tel = poi.get("business", {}).get("tel", "")

            # 如果POI ID为空，生成一个基于名称和地址的唯一ID
            if not poi_id:
                import hashlib

                poi_address = poi.get("address", "")
                poi_location = poi.get("location", "")
                # 使用名称+地址+位置生成唯一ID
                unique_string = f"{poi_name}|{poi_address}|{poi_location}"
                poi_id = hashlib.md5(unique_string.encode("utf-8")).hexdigest()[:16]
                logging.info(f"生成POI ID: {poi_id} (基于 {unique_string})")

            result = {
                "title": poi_name,
                "score": score,
                "type": poi.get("type", ""),  # 展示POI类型
                "image": image_url,  # 使用高德API返回的图片或默认图片
                "address": poi.get("address", ""),
                "location": poi.get("location", ""),
                "typecode": poi.get("typecode", ""),
                "poi_id": poi_id,
                "distance": poi.get("distance", ""),
                "tel": tel,
            }

            logging.info(f"格式化完成: {result}")
            return result
            
        except Exception as e:
            logging.error(f"格式化POI推荐失败: {e}, POI数据: {poi}")
            print(f"[DEBUG] 格式化异常: {e}")
            return None


# -------------------- ChatHistoryView --------------------


@method_decorator(csrf_exempt, name="dispatch")
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
        session_id = request.GET.get("session_id")
        if not session_id:
            return JsonResponse(
                {"error": True, "message": "session_id 必填"}, status=400
            )

        try:
            fsm = TravelAssistantFSM()
            if not fsm.load_session(session_id):
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )
            
            history = fsm.get_conversation_history()
            return JsonResponse({"session_id": session_id, "history": history})
        except Exception as e:
            logging.error(f"获取历史失败: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class AddPOIView(View):
    """添加POI到会话"""

    def __init__(self):
        from talker.services.poi_management import POIManagementService
        from django.core.cache import cache

        self.poi_service = POIManagementService()
        self.cache = cache

    def post(self, request):
        """添加POI到会话

        请求体格式：
        {
            "session_id": "会话ID",
            "poi_index": POI在搜索结果中的索引
        }
        """
        try:
            data = json.loads(request.body)
            session_id = data.get("session_id")
            poi_index = data.get("poi_index")

            # 添加调试信息
            logging.info(
                f"收到POI添加请求: session_id={session_id}, poi_index={poi_index}"
            )

            if not session_id:
                return JsonResponse(
                    {"error": True, "message": "session_id不能为空"}, status=400
                )

            if poi_index is None:
                return JsonResponse(
                    {"error": True, "message": "poi_index不能为空"}, status=400
                )

            # 获取会话
            try:
                session = TalkSession.objects.get(id=session_id)
                logging.info(f"找到会话: {session.id}")
            except TalkSession.DoesNotExist:
                logging.error(f"会话不存在: {session_id}")
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )

            # 从缓存中获取POI数据
            cache_key = f"poi_search_result_{session_id}"
            cached_pois = self.cache.get(cache_key)
            
            if not cached_pois:
                return JsonResponse(
                    {"error": True, "message": "POI搜索结果已过期，请重新搜索"}, status=400
                )
                
            if poi_index >= len(cached_pois):
                return JsonResponse(
                    {"error": True, "message": f"POI索引无效: {poi_index}"}, status=400
                )
                
            # 获取对应的POI数据
            poi_data = cached_pois[poi_index]
            poi_name = poi_data.get("name", "")
            
            logging.info(f"从缓存获取POI数据: name={poi_name}, index={poi_index}")

            if not poi_name:
                return JsonResponse(
                    {"error": True, "message": "POI名称不能为空"}, status=400
                )

            # 将POI名称添加到session.locations（如果还没有的话）
            locations = session.locations or []
            if poi_name not in locations:
                locations.append(poi_name)
                session.locations = locations
                session.save()
                logging.info(f"已将POI名称添加到locations: {poi_name}")

            # 直接使用缓存的POI数据添加到数据库，无需重新调用API
            logging.info("开始添加缓存的POI数据到数据库...")
            success = self.poi_service.add_poi_from_search_result(session, poi_data, 'recommendation')
            logging.info(f"POI添加结果: {success}")

            if success:
                return JsonResponse(
                    {"success": True, "message": f"成功添加POI: {poi_name}"}
                )
            else:
                return JsonResponse(
                    {
                        "error": True,
                        "message": "添加POI失败",
                    },
                    status=500,
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"添加POI错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class RemovePOIView(View):
    """从会话中删除POI"""

    def __init__(self):
        from talker.services.poi_management import POIManagementService

        self.poi_service = POIManagementService()

    def post(self, request):
        """删除会话中的POI

        请求体格式：
        {
            "session_id": "会话ID",
            "poi_id": "POI ID"
        }
        """
        try:
            data = json.loads(request.body)
            session_id = data.get("session_id")
            poi_id = data.get("poi_id")

            if not session_id:
                return JsonResponse(
                    {"error": True, "message": "session_id不能为空"}, status=400
                )

            if not poi_id:
                return JsonResponse(
                    {"error": True, "message": "poi_id不能为空"}, status=400
                )

            # 获取会话
            try:
                session = TalkSession.objects.get(id=session_id)
            except TalkSession.DoesNotExist:
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )

            # 删除POI
            success = self.poi_service.remove_poi(session=session, poi_id=poi_id)

            if success:
                return JsonResponse({"success": True, "message": "成功删除POI"})
            else:
                return JsonResponse(
                    {"error": True, "message": "POI不存在或删除失败"}, status=404
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": True, "message": "无效的JSON格式"}, status=400
            )
        except Exception as e:
            logging.error(f"删除POI错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class ListPOIView(View):
    """获取会话中的POI列表"""

    def __init__(self):
        from talker.services.poi_management import POIManagementService

        self.poi_service = POIManagementService()

    def get(self, request):
        """获取会话中的POI列表

        查询参数：
        - session_id: 会话ID
        - source: 来源过滤（可选）
        """
        session_id = request.GET.get("session_id")
        source = request.GET.get("source")

        if not session_id:
            return JsonResponse(
                {"error": True, "message": "session_id不能为空"}, status=400
            )

        try:
            # 获取会话
            try:
                session = TalkSession.objects.get(id=session_id)
            except TalkSession.DoesNotExist:
                return JsonResponse(
                    {"error": True, "message": "会话不存在"}, status=404
                )

            # 获取POI列表
            poi_items = self.poi_service.get_session_pois(
                session=session, source=source
            )

            # 格式化POI数据
            pois = []
            for poi_item in poi_items:
                poi_data = {
                    "id": poi_item.id,
                    "poi_id": poi_item.poi_id,
                    "name": poi_item.name,
                    "address": poi_item.address,
                    "location": poi_item.location,
                    "type": poi_item.type,
                    "tel": poi_item.tel,
                    "distance": poi_item.distance,
                    "created_at": (
                        poi_item.created_at.isoformat() if poi_item.created_at else None
                    ),
                    "raw_data": poi_item.raw_data,
                }

                # 从raw_data中提取额外信息
                if poi_item.raw_data:
                    raw_data = poi_item.raw_data

                    # 提取图片URL - 优先使用photos中的第一张图片
                    image_url = "/static/images/flower.jpg"  # 默认图片
                    photos = raw_data.get("photos", [])
                    if photos and len(photos) > 0:
                        # 取第一张图片
                        first_photo = photos[0]
                        if isinstance(first_photo, dict) and "url" in first_photo:
                            image_url = first_photo["url"]
                        elif isinstance(first_photo, str):
                            image_url = first_photo

                    # 处理评分数据：从raw_data.business.rating获取评分
                    business = raw_data.get("business", {})
                    rating = business.get("rating") if business else None
                    if rating is not None:
                        try:
                            score = float(rating)
                        except (ValueError, TypeError):
                            score = 0
                    else:
                        score = 0
                    
                    poi_data.update(
                        {
                            "score": score,
                            "image": image_url,
                            "typecode": raw_data.get("typecode", ""),
                        }
                    )

                pois.append(poi_data)

            # 获取统计信息
            stats = self.poi_service.get_poi_statistics(session)

            return JsonResponse(
                {"success": True, "pois": pois, "total": len(pois), "statistics": stats}
            )

        except Exception as e:
            logging.error(f"获取POI列表错误: {e}")
            return JsonResponse({"error": True, "message": str(e)}, status=500)


@csrf_exempt
@require_POST
def state_machine_api(request):
    """状态机对话API"""
    try:
        # 解析请求数据
        data = json.loads(request.body)
        session_id = data.get('session_id')
        message = data.get('message', '')
        is_stream = data.get('stream', False)
        
        if not session_id:
            return JsonResponse({'error': '缺少session_id参数'}, status=400)
        
        # 获取会话
        try:
            session = TalkSession.objects.get(id=session_id)
        except TalkSession.DoesNotExist:
            return JsonResponse({'error': '会话不存在'}, status=404)
        
        # 初始化状态机
        state_machine = TalkStateMachine(session)
        
        if is_stream:
            # 流式响应
            response_generator = state_machine.handle_message_stream(message)
            
            def generate_sse():
                try:
                    for chunk in response_generator:
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logging.error(f"流式生成出错: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
            
            from django.http import StreamingHttpResponse
            response = StreamingHttpResponse(generate_sse(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            return response
        else:
            # 非流式响应
            try:
                result = state_machine.handle_message(message)
                return JsonResponse({
                    'response': result,
                    'success': True
                })
            except Exception as e:
                logging.error(f"处理消息失败: {e}")
                return JsonResponse({
                    'error': str(e),
                    'success': False
                }, status=500)
                
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        logging.error(f"状态机API出错: {e}")
        return JsonResponse({'error': '服务器内部错误'}, status=500)

@csrf_exempt
@require_GET
def timeline_api(request, session_id):
    """Timeline服务API - 生成行程链"""
    try:
        # 获取会话
        try:
            session = TalkSession.objects.get(id=session_id)
        except TalkSession.DoesNotExist:
            return JsonResponse({'error': '会话不存在'}, status=404)
        
        # 初始化Timeline服务
        timeline_service = TimelineService()
        
        # 生成Timeline
        logging.info(f"开始为会话 {session_id} 生成Timeline")
        timeline_data = timeline_service.generate_timeline(session)
        
        if timeline_data.get('success'):
            logging.info(f"Timeline生成成功: 会话 {session_id}")
            return JsonResponse({
                'success': True,
                'timeline_data': timeline_data,
                'message': '行程链生成成功'
            })
        else:
            logging.error(f"Timeline生成失败: 会话 {session_id}, 错误: {timeline_data.get('error', '未知错误')}")
            return JsonResponse({
                'success': False,
                'error': timeline_data.get('error', '行程链生成失败'),
                'timeline_data': None
            }, status=500)
            
    except Exception as e:
        logging.error(f"Timeline API出错: 会话 {session_id}, 错误: {e}")
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}',
            'timeline_data': None
        }, status=500)

@csrf_exempt
@require_GET
def session_state_api(request, session_id):
    """获取会话状态API"""
    try:
        # 获取会话
        try:
            session = TalkSession.objects.get(id=session_id)
        except TalkSession.DoesNotExist:
            return JsonResponse({'error': '会话不存在'}, status=404)
        
        # 初始化状态机获取状态
        state_machine = TalkStateMachine(session)
        
        # 获取会话信息
        session_info = {
            'id': session.id,
            'locations': session.locations,
            'budget': session.budget,
            'start_date': session.start_date.isoformat() if session.start_date else None,
            'end_date': session.end_date.isoformat() if session.end_date else None,
            'user_profile': session.user_profile,
            'state': session.state,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
        }
        
        # 获取槽位信息
        slots_info = state_machine._get_slot_status()
        
        # 获取当前状态
        current_state = state_machine._get_current_state()
        
        return JsonResponse({
            'session_info': session_info,
            'slots_info': slots_info,
            'current_state': current_state,
            'success': True
        })
        
    except Exception as e:
        logging.error(f"获取会话状态失败: 会话 {session_id}, 错误: {e}")
        return JsonResponse({
            'error': f'获取会话状态失败: {str(e)}',
            'success': False
        }, status=500)

@csrf_exempt
@require_POST
def timeline_stream_api(request):
    """Timeline服务SSE接口 - 按阶段推送进度"""
    try:
        data = json.loads(request.body or '{}')
        session_id = data.get('session_id')
        if not session_id:
            return JsonResponse({'error': '缺少session_id'}, status=400)

        try:
            session = TalkSession.objects.get(id=session_id)
        except TalkSession.DoesNotExist:
            return JsonResponse({'error': '会话不存在'}, status=404)

        timeline_service = TimelineService()

        def gen():
            """生成SSE数据流"""
            try:
                # Stage 1: 用户画像整合
                yield f"data: {json.dumps({'type':'stage','stage':'profile_consolidation'})}\n\n"
                profile_data = timeline_service._stage_1_profile_consolidation(session)

                # Stage 1.5: 地理聚类
                yield f"data: {json.dumps({'type':'stage','stage':'geographic_clustering'})}\n\n"
                clusters = timeline_service._stage_1_5_geographic_clustering(session, profile_data['radius_km'])

                # Stage 2: 行程草案生成
                yield f"data: {json.dumps({'type':'stage','stage':'itinerary_drafting'})}\n\n"
                daily_itinerary = timeline_service._stage_2_itinerary_drafting(profile_data['user_profile_text'], clusters)

                # Stage 3: 行程评审
                yield f"data: {json.dumps({'type':'stage','stage':'itinerary_review'})}\n\n"
                review_feedback = timeline_service._stage_3_itinerary_review(profile_data['user_profile_text'], daily_itinerary)

                # Stage 3.5: 草案修订
                yield f"data: {json.dumps({'type':'stage','stage':'itinerary_revision'})}\n\n"
                revised_itinerary = timeline_service._stage_3_5_itinerary_revision(profile_data['user_profile_text'], daily_itinerary, review_feedback)

                # Stage 4: 链式结构生成
                yield f"data: {json.dumps({'type':'stage','stage':'chain_generation'})}\n\n"
                itinerary_chain = timeline_service._stage_4_chain_generation(revised_itinerary)

                result = {
                    'success': True,
                    'timeline_data': {
                        'success': True,
                        'itinerary_chain': itinerary_chain,
                        'final_text': revised_itinerary
                    }
                }
                yield f"data: {json.dumps({'type':'done','result': result})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = str(e)
                yield f"data: {json.dumps({'type':'error','error': error_msg})}\n\n"
                yield "data: [DONE]\n\n"

        from django.http import StreamingHttpResponse
        response = StreamingHttpResponse(gen(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        return response

    except json.JSONDecodeError:
        return JsonResponse({'error': '无效JSON'}, status=400)
    except Exception as e:
        logging.error(f"Timeline SSE接口错误: {e}")
        return JsonResponse({'error': str(e)}, status=500)
