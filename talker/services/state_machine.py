#!/usr/bin/env python
# encoding: utf-8

# type: ignore

from transitions import Machine
from typing import Dict, Any, Optional, List, Generator
from talker.models import TalkSession
import logging
from talker.services.chat_service import ChatService
from django.contrib.auth.models import User
from talker.services.session_control import analyze_and_update_talksession

class TravelAssistantFSM:
    """旅行助手状态机，基于简化的槽位填充模式"""
    
    # 定义状态
    states = [
        'INIT',                    # 初始状态
        'SLOT_FILLING_DESTINATION', # 等待目的地
        'SLOT_FILLING_DESTINATION_DEEP', # 深化目的地询问
        'SLOT_FILLING_DESTINATION_CONFIRM', # 确认目的地
        'SLOT_FILLING_BUDGET',      # 等待预算
        'SLOT_FILLING_DATES',       # 等待日期
        'SLOT_FILLING_PROFILE',     # 等待用户画像（包含同行人员）
        'CONFIRMATION',             # 确认阶段
        'COMPLETED',                # 完成状态
        'ERROR'                     # 错误状态
    ]
    
    def __init__(self, session: Optional[TalkSession] = None):
        self.session = session
        self.current_user = None
        
        # 初始化槽位（合并 travelers 到 profile）
        self.slots = {
            'destination': None,
            'budget': None,
            'dates': None,
            'profile': None
        }
        
        # 状态机初始化
        self.machine = Machine(
            model=self,
            states=TravelAssistantFSM.states,
            initial='INIT'
        )
        
        # 定义转移
        self._setup_transitions()
        
        # 绑定事件处理函数
        self._setup_event_handlers()
        
        # 初始化槽位数据
        if self.session:
            self._update_slots_from_session()
        self.chat_service = ChatService()
        
        # 初始化用户画像询问标记
        self._profile_asked_basic = False
        self._profile_asked_again = False
        
        # 初始化POI搜索回调
        self._poi_search_callback = None
    
    def _setup_transitions(self):
        """设置状态转移"""
        # 从初始状态开始
        self.machine.add_transition('start', 'INIT', 'SLOT_FILLING_DESTINATION')
        
        # 目的地槽位 - 修改为多阶段流程
        self.machine.add_transition('user_provides_destination', 'SLOT_FILLING_DESTINATION', 'SLOT_FILLING_DESTINATION_DEEP')
        self.machine.add_transition('slot_invalid_destination', 'SLOT_FILLING_DESTINATION', 'SLOT_FILLING_DESTINATION')
        
        # 深化目的地询问
        self.machine.add_transition('destination_deep_complete', 'SLOT_FILLING_DESTINATION_DEEP', 'SLOT_FILLING_DESTINATION_CONFIRM')
        self.machine.add_transition('destination_deep_continue', 'SLOT_FILLING_DESTINATION_DEEP', 'SLOT_FILLING_DESTINATION_DEEP')
        
        # 确认目的地
        self.machine.add_transition('destination_confirmed', 'SLOT_FILLING_DESTINATION_CONFIRM', 'SLOT_FILLING_BUDGET')
        self.machine.add_transition('destination_not_confirmed', 'SLOT_FILLING_DESTINATION_CONFIRM', 'SLOT_FILLING_DESTINATION_DEEP')
        
        # 预算槽位
        self.machine.add_transition('user_provides_budget', 'SLOT_FILLING_BUDGET', 'SLOT_FILLING_DATES')
        self.machine.add_transition('slot_invalid_budget', 'SLOT_FILLING_BUDGET', 'SLOT_FILLING_BUDGET')
        
        # 日期槽位
        self.machine.add_transition('user_provides_dates', 'SLOT_FILLING_DATES', 'SLOT_FILLING_PROFILE')
        self.machine.add_transition('slot_invalid_dates', 'SLOT_FILLING_DATES', 'SLOT_FILLING_DATES')
        
        # 用户画像槽位
        self.machine.add_transition('user_provides_profile', 'SLOT_FILLING_PROFILE', 'CONFIRMATION')
        self.machine.add_transition('slot_invalid_profile', 'SLOT_FILLING_PROFILE', 'SLOT_FILLING_PROFILE')
        
        # 确认阶段
        self.machine.add_transition('confirm', 'CONFIRMATION', 'COMPLETED', after='show_plan')
        
        # 全局转移
        self.machine.add_transition('cancel', '*', 'COMPLETED', after='cancel_flow')
        self.machine.add_transition('error', '*', 'ERROR', after='error_handler')
    
    def _setup_event_handlers(self):
        """设置事件处理函数"""
        # 进入状态时的处理
        self.machine.on_enter_SLOT_FILLING_DESTINATION(self._on_enter_fill_destination)
        self.machine.on_enter_SLOT_FILLING_DESTINATION_DEEP(self._on_enter_fill_destination_deep)
        self.machine.on_enter_SLOT_FILLING_DESTINATION_CONFIRM(self._on_enter_fill_destination_confirm)
        self.machine.on_enter_SLOT_FILLING_BUDGET(self._on_enter_fill_budget)
        self.machine.on_enter_SLOT_FILLING_DATES(self._on_enter_fill_dates)
        self.machine.on_enter_SLOT_FILLING_PROFILE(self._on_enter_fill_profile)
        self.machine.on_enter_CONFIRMATION(self._on_enter_confirmation)
        self.machine.on_enter_COMPLETED(self._on_enter_completed)
        self.machine.on_enter_ERROR(self._on_enter_error)
    
    # ========== 状态进入处理函数 ==========
    
    def _on_enter_fill_destination(self, *args, **kwargs):
        """进入填充目的地状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_destination",
            "context": "等待用户提供目的地信息"
        })
    
    def _on_enter_fill_destination_deep(self, *args, **kwargs):
        """进入深化目的地询问状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_destination_deep",
            "context": "深化目的地询问"
        })
    
    def _on_enter_fill_destination_confirm(self, *args, **kwargs):
        """进入确认目的地状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_destination_confirm",
            "context": "确认目的地"
        })
    
    def _on_enter_fill_budget(self, *args, **kwargs):
        """进入填充预算状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_budget",
            "context": "等待用户提供预算信息"
        })
    
    def _on_enter_fill_dates(self, *args, **kwargs):
        """进入填充日期状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_dates",
            "context": "等待用户提供出发和返回日期"
        })
    
    def _on_enter_fill_profile(self, *args, **kwargs):
        """进入填充用户画像状态"""
        self._set_session_state({
            "phase": "slot_filling",
            "intent": "fill_profile",
            "context": "等待用户提供同行人员和用户画像"
        })
    
    def _on_enter_confirmation(self, *args, **kwargs):
        """进入确认状态"""
        self._set_session_state({
            "phase": "confirmation",
            "intent": "confirm_info",
            "context": "汇总信息并等待用户确认"
        })
    
    def _on_enter_completed(self, *args, **kwargs):
        """进入完成状态"""
        self._set_session_state({
            "phase": "completed",
            "intent": "plan_ready",
            "context": "旅行计划已完成"
        })
    
    def _on_enter_error(self, *args, **kwargs):
        """进入错误状态"""
        self._set_session_state({
            "phase": "error",
            "intent": "handle_error",
            "context": "处理对话中的错误"
        })
    
    def _set_session_state(self, state_info: Dict[str, Any]):
        """设置会话状态"""
        self.session.state = state_info
        self.session.save()
        logging.info(f"状态机设置会话状态: {state_info}")
    
    # ========== 动作函数 ==========
    
    def ask_destination(self, *args, **kwargs):
        """询问目的地"""
        logging.info("询问用户目的地")
        # 准备上下文信息
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="ask_destination",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '您这次想去哪里？')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_destination_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """询问目的地（流式版本）"""
        logging.info("询问用户目的地（流式）")
        # 准备上下文信息
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        full_content = ""
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="ask_destination",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk['type'] == 'content':
                    full_content += chunk['chunk']
                    yield {
                        'type': 'content',
                        'chunk': chunk['chunk'],
                        'full_content': full_content
                    }
                elif chunk['type'] == 'done':
                    # 流式内容完成，添加到历史记录
                    self.add_assistant_message(full_content)
                    yield {
                        'type': 'done',
                        'full_content': full_content
                    }
                    return
                elif chunk['type'] == 'event':
                    yield chunk
                    
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            # 如果流式处理失败，使用默认回复
            default_response = '您这次想去哪里？'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_destination_again(self, user_input: str = "", *args, **kwargs):
        """重新询问目的地"""
        logging.info("重新询问用户目的地")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的目的地信息，请重新引导用户说明想去的地方。"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_destination_again",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请重新告诉我您的目的地。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_destination_deep(self, user_input: str = "", *args, **kwargs):
        """深化询问目的地"""
        logging.info("深化询问用户目的地")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_destination_deep",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请告诉我更多关于您想去的地方的信息。')
        
        # 检查大模型是否返回了"END"
        if response_text.strip().upper() == "END":
            # 大模型确认了目的地信息，不添加消息到历史记录，直接返回"END"
            return "END"
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)

        # 在大模型回复后，自动进行关键词生成和POI搜索，仅缓存结果
        try:
            from hunter.services.poi_search_pipeline import POISearchPipeline
            conversation = self.get_conversation_history()
            session_info = self.get_session_info()
            pipeline = POISearchPipeline()
            result = pipeline.search_by_conversation(conversation, session_info)
            # 缓存结果并通过回调传递
            self._latest_poi_search_result = result
            if self._poi_search_callback:
                self._poi_search_callback(result)
        except Exception as e:
            logging.error(f"自动POI搜索失败: {e}")
            self._latest_poi_search_result = None
        
        return response_text
    
    def ask_destination_confirm(self, user_input: str = "", *args, **kwargs):
        """确认目的地信息"""
        logging.info("确认用户目的地信息")
        
        # 硬编码检测用户确认关键词
        if user_input:
            confirm_keywords = ['确认', '是的', '对的', '可以', '进入下一阶段']
            if any(keyword in user_input for keyword in confirm_keywords):
                logging.info(f"用户确认目的地信息: {user_input}")
                return "END"
        
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_destination_confirm",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请确认您的目的地信息。')
        
        # 检查大模型是否返回了"END"
        if response_text.strip().upper() == "END":
            # 大模型确认了目的地信息，不添加消息到历史记录，直接返回"END"
            return "END"
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_budget(self, *args, **kwargs):
        """询问预算"""
        logging.info("询问用户预算")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="ask_budget",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '您的预算大概是多少？')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_budget_again(self, user_input: str = "", *args, **kwargs):
        """重新询问预算"""
        logging.info("重新询问用户预算")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的预算信息，请重新引导用户说明预算。"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_budget_again",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请重新告诉我您的预算。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_dates(self, *args, **kwargs):
        """询问日期"""
        logging.info("询问用户日期")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="ask_dates",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '您计划什么时候出发、什么时候回来？')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_dates_again(self, user_input: str = "", *args, **kwargs):
        """重新询问日期"""
        logging.info("重新询问用户日期")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的日期信息，请重新引导用户说明出发和返回日期。"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_dates_again",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请重新告诉我您的出发和返回日期。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_profile(self, *args, **kwargs):
        """询问用户画像"""
        logging.info("询问用户画像")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="ask_profile",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请告诉我您的同行人员和旅行偏好。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_profile_again(self, user_input: str = "", *args, **kwargs):
        """重新询问用户画像"""
        logging.info("重新询问用户画像")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中缺少一些信息，请自然地引导用户提供更多关于同行人员和旅行偏好的信息。"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_profile_again",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请重新告诉我您的同行人员和旅行偏好。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_profile_extend(self, user_input: str = "", *args, **kwargs):
        """深化询问用户画像 - 根据用户回答进行纵向和横向拓展"""
        logging.info("深化询问用户画像")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n任务：根据用户的回答，进行纵向和横向拓展询问。纵向：深入询问用户提到的具体偏好（如具体的美食类型、具体的文化景点等）。横向：询问用户未提及但相关的信息（如年龄、职业、特殊需求等）。"
        
        response = self.chat_service.process_chat(
            context_info + additional_context, 
            chat_type="ask_profile_extend",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '请告诉我更多关于您的旅行偏好。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def ask_confirmation(self, *args, **kwargs):
        """询问确认"""
        summary = self._generate_summary()
        logging.info("询问用户确认信息")
        context_info = self._prepare_context_info(summary=summary)
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="ask_confirmation",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info,
            summary=summary
        )
        response_text = response.get('data', {}).get('content', f'请确认以下信息是否都正确：\n{summary}\n如无误，请回复"确认"。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def show_plan(self, *args, **kwargs):
        """显示计划"""
        logging.info("显示旅行计划")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="show_plan",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '好的，正在为您生成行程方案…')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        # 使用 RouteTimeService 解析行程并保存到数据库
        try:
            from planner.services.route_time_service import RouteTimeService
            from planner.services.trip_service import TripService
            from datetime import date
            
            # 初始化 RouteTimeService
            route_service = RouteTimeService()
            
            # 从会话中获取用户信息
            user = self.session.user
            
            # 从槽位中获取开始日期
            start_date = None
            if self.slots.get('dates') and isinstance(self.slots['dates'], dict):
                start_date_str = self.slots['dates'].get('start_date')
                if start_date_str:
                    try:
                        start_date = date.fromisoformat(start_date_str)
                    except ValueError:
                        start_date = date.today()
            else:
                start_date = date.today()
            
            # 从槽位中获取目的地信息作为城市提示
            city_hint = None
            if self.slots.get('destination'):
                destination = self.slots['destination']
                if isinstance(destination, list) and destination:
                    city_hint = destination[0]  # 使用第一个目的地作为城市提示
                elif isinstance(destination, str):
                    city_hint = destination
            
            # 生成行程标题
            trip_title = f"AI规划行程_{self.session.id}"
            if self.slots.get('destination'):
                dest_str = str(self.slots['destination'])
                trip_title = f"{dest_str}之旅"
            
            # 生成行程描述
            trip_description = "AI智能规划的个性化旅行行程"
            if self.slots.get('profile'):
                profile = self.slots['profile']
                if isinstance(profile, dict):
                    interests = profile.get('兴趣爱好', [])
                    if interests:
                        trip_description = f"适合{', '.join(interests)}爱好者的个性化行程"
            
            # 保存行程到数据库
            trip = route_service.save_plan_to_db(
                plan_text=response_text,
                user=user,
                trip_title=trip_title,
                trip_description=trip_description,
                city_hint=city_hint,
                start_date=start_date
            )
            
            logging.info(f"行程已保存到数据库，Trip ID: {trip.id}")
            
            # 使用 TripService 生成时间线
            timeline_data = TripService.generate_timeline(trip)
            
            # 将时间线数据添加到回复中
            timeline_summary = self._format_timeline_summary(timeline_data)
            response_text += f"\n\n📅 详细时间安排：\n{timeline_summary}"
            
            # 更新会话状态，记录已保存的行程ID
            if not self.session.state:
                self.session.state = {}
            self.session.state['saved_trip_id'] = trip.id
            self.session.save()
            
        except Exception as e:
            logging.error(f"保存行程到数据库失败: {e}")
            response_text += "\n\n⚠️ 行程已生成，但保存到数据库时遇到问题。"
        
        return response_text
    
    def _format_timeline_summary(self, timeline_data: Dict[str, Any]) -> str:
        """格式化时间线摘要，增强交通方式 emoji 映射"""
        if not timeline_data:
            return "暂无时间安排"
        summary_parts = []
        # 行程基本信息
        trip_info = timeline_data.get('trip', {})
        if trip_info:
            summary_parts.append(f"🗓️ 行程：{trip_info.get('title', '未知')}")
            summary_parts.append(f"📅 日期：{trip_info.get('start_date', '')} 至 {trip_info.get('end_date', '')}")
            summary_parts.append(f"⏱️ 总天数：{trip_info.get('total_days', 0)} 天")
        # 交通方式 emoji 映射
        TRANSPORT_EMOJI = {
            "步行": "🚶",
            "walking": "🚶",
            "骑行": "🚴",
            "bicycling": "🚴",
            "打车": "🚗",
            "驾车": "🚗",
            "driving": "🚗",
            "公交": "🚌",
            "transit": "🚌",
            "地铁": "🚇",
            "高铁": "🚄",
            "火车": "🚄",
            "飞机": "✈️",
            "other": "🚙"
        }
        # 每日安排
        timeline = timeline_data.get('timeline', [])
        if timeline:
            summary_parts.append("\n📋 每日安排：")
            current_day = None
            for event in timeline:
                day_index = event.get('day_index', 0)
                if day_index != current_day:
                    current_day = day_index
                    summary_parts.append(f"\n第{day_index}天：")
                event_type = event.get('type', '')
                title = event.get('title', '未知活动')
                start_time = event.get('start_time', '')
                end_time = event.get('end_time', '')
                if event_type == 'activity':
                    summary_parts.append(f"  📍 {start_time} - {end_time} {title}")
                elif event_type in ['departure', 'arrival']:
                    mode = event.get('mode', '')
                    emoji = TRANSPORT_EMOJI.get(mode, "🚙")
                    summary_parts.append(f"  {emoji} {start_time} - {end_time} {title} ({mode})")
        return "\n".join(summary_parts)
    
    def cancel_flow(self, *args, **kwargs):
        """取消流程"""
        logging.info("用户取消流程")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="cancel_flow",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '好的，已取消当前流程。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def error_handler(self, *args, **kwargs):
        """错误处理"""
        logging.info("处理错误")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        response = self.chat_service.process_chat(
            context_info, 
            chat_type="error_handler",
            phase=state_info.get('phase', '未知'),
            intent=state_info.get('intent', '未知'),
            context=state_info.get('context', '未知'),
            collected_info=collected_info
        )
        response_text = response.get('data', {}).get('content', '抱歉，我遇到了一些问题，请重新开始。')
        
        # 添加助手消息到历史记录
        self.add_assistant_message(response_text)
        
        return response_text
    
    def _prepare_context_info(self, summary: str = None) -> str:
        """准备上下文信息，用于传递给大模型"""
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        context_parts = [
            f"当前阶段：{state_info.get('phase', '未知')}",
            f"用户意图：{state_info.get('intent', '未知')}",
            f"上下文：{state_info.get('context', '未知')}",
            f"已收集信息：{collected_info}"
        ]
        
        if summary:
            context_parts.append(f"信息汇总：{summary}")
        
        return "\n".join(context_parts)
    
    def _format_collected_info(self) -> str:
        """格式化已收集的信息"""
        info_parts = []
        
        if self.slots['destination']:
            info_parts.append(f"目的地：{self.slots['destination']}")
        if self.slots['budget']:
            info_parts.append(f"预算：{self.slots['budget']}")
        if self.slots['dates']:
            dates = self.slots['dates']
            if isinstance(dates, dict):
                start_date = dates.get('start_date', '未设置')
                end_date = dates.get('end_date', '未设置')
                info_parts.append(f"出发日期：{start_date}")
                info_parts.append(f"返回日期：{end_date}")
            else:
                info_parts.append(f"日期：{dates}")
        if self.slots['profile']:
            info_parts.append(f"用户画像：{self.slots['profile']}")
        
        return "；".join(info_parts) if info_parts else "暂无信息"
    
    # ========== 统一处理入口 ==========
    
    def handle_utterance(self, text: str) -> str:
        """统一入口：处理用户话语，返回回复内容"""
        if not self.session:
            raise ValueError("没有活跃的会话")
        
        # 添加用户消息到历史记录
        self.add_user_message(text)
        
        # 分析会话历史并更新 TalkSession
        success, analysis_msg = analyze_and_update_talksession(self.session)
        if not success:
            logging.warning(f"会话分析警告: {analysis_msg}")
        
        # 更新槽位数据（从session_control分析后的数据）
        self._update_slots_from_session()
        
        # 检查是否是确认消息
        if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步']):
            if self.state == 'SLOT_FILLING_DESTINATION_CONFIRM':
                # 在目的地确认状态下，用户确认了目的地信息
                self.destination_confirmed()
                return self.ask_budget()
            elif self._are_all_slots_filled():
                if self.state != 'CONFIRMATION':
                    self.machine.set_state('CONFIRMATION')
                    return self.ask_confirmation()
                else:
                    self.confirm()
                    return self.show_plan()
        
        # 基于当前状态和用户输入判断是否回答了当前问题
        current_state = self.state
        
        if current_state == 'SLOT_FILLING_DESTINATION':
            # 检查用户是否提供了目的地信息
            if self._has_destination_info(text, check_deep_process=False):
                # 用户提供了目的地信息，转移到深化询问状态
                self.user_provides_destination(text)  # type: ignore
                return self.ask_destination_deep(text)
            else:
                # 用户没有提供目的地信息，重新询问
                self.slot_invalid_destination(text)  # type: ignore
                return self.ask_destination_again(text)
                
        elif current_state == 'SLOT_FILLING_DESTINATION_DEEP':
            # 深化目的地询问状态
            # 首先检查用户是否表达了确认或进入下一阶段的意图
            if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步', '差不多了', '就这样']):
                # 用户表达了确认意图，转移到确认状态
                self.destination_deep_complete()
                return self.ask_destination_confirm()
            
            response = self.ask_destination_deep(text)
            
            # 检查大模型是否返回了"END"
            if response == "END":
                # 大模型确认了目的地信息，转移到确认状态
                self.destination_deep_complete()
                return self.ask_destination_confirm()
            else:
                # 继续深化询问
                self.destination_deep_continue()
                return response
                
        elif current_state == 'SLOT_FILLING_DESTINATION_CONFIRM':
            # 确认目的地状态
            response = self.ask_destination_confirm(text)
            
            # 检查大模型是否返回了"END"
            if response == "END":
                # 大模型确认了目的地信息，转移到下一个状态
                self.destination_confirmed()
                # 检查下一个槽位是否已经填充
                if self._has_budget_info(text):
                    # 预算也已填充，继续检查下一个
                    if self._has_dates_info(text):
                        # 日期也已填充，继续检查下一个
                        if self._has_profile_info(text):
                            # 用户画像也已填充，直接进入确认状态
                            self.machine.set_state('CONFIRMATION')
                            return self.ask_confirmation()
                        else:
                            # 用户画像未填充，转移到用户画像状态
                            self.machine.set_state('SLOT_FILLING_PROFILE')
                            # 手动触发状态进入回调
                            self._on_enter_fill_profile()
                            return self.ask_profile()
                    else:
                        # 日期未填充，转移到日期状态
                        self.machine.set_state('SLOT_FILLING_DATES')
                        # 手动触发状态进入回调
                        self._on_enter_fill_dates()
                        return self.ask_dates()
                else:
                    # 预算未填充，转移到预算状态
                    return self.ask_budget()
            else:
                # 用户没有确认，继续深化询问
                self.destination_not_confirmed()
                return response
        
        elif current_state == 'SLOT_FILLING_BUDGET':
            # 检查用户是否提供了预算信息
            if self._has_budget_info(text):
                # 用户提供了预算信息，转移到下一个状态
                self.user_provides_budget(text)  # type: ignore
                # 检查下一个槽位是否已经填充
                if self._has_dates_info(text):
                    # 日期也已填充，继续检查下一个
                    if self._has_profile_info(text):
                        # 用户画像也已填充，直接进入确认状态
                        self.machine.set_state('CONFIRMATION')
                        return self.ask_confirmation()
                    else:
                        # 用户画像未填充，转移到用户画像状态
                        self.machine.set_state('SLOT_FILLING_PROFILE')
                        # 手动触发状态进入回调
                        self._on_enter_fill_profile()
                        return self.ask_profile()
                else:
                    # 日期未填充，转移到日期状态
                    return self.ask_dates()
            else:
                # 用户没有提供预算信息，重新询问
                self.slot_invalid_budget(text)  # type: ignore
                return self.ask_budget_again(text)
                
        elif current_state == 'SLOT_FILLING_DATES':
            # 检查用户是否提供了日期信息
            if self._has_dates_info(text):
                # 用户提供了日期信息，转移到下一个状态
                self.user_provides_dates(text)  # type: ignore
                # 检查下一个槽位是否已经填充
                if self._has_profile_info(text):
                    # 用户画像也已填充，直接进入确认状态
                    self.machine.set_state('CONFIRMATION')
                    return self.ask_confirmation()
                else:
                    # 用户画像未填充，转移到用户画像状态
                    return self.ask_profile()
            else:
                # 用户没有提供日期信息，重新询问
                self.slot_invalid_dates(text)  # type: ignore
                return self.ask_dates_again(text)
                
        elif current_state == 'SLOT_FILLING_PROFILE':
            # 检查用户是否提供了用户画像信息
            if self._has_profile_info(text):
                # 用户提供了用户画像信息，检查是否已经进行过深化询问
                if not self._profile_asked_basic:
                    # 第一次回答，标记已询问基础信息，进行深化询问
                    self._profile_asked_basic = True
                    return self.ask_profile_extend(text)
                elif self._profile_asked_basic and not self._profile_asked_again:
                    # 已经进行过基础询问，但还没有进行过again询问，进行深化询问
                    self._profile_asked_again = True
                    return self.ask_profile_extend(text)
                else:
                    # 已经进行过深化询问，转移到确认状态
                    self.user_provides_profile(text)  # type: ignore
                    return self.ask_confirmation()
            else:
                # 用户没有提供用户画像信息，检查是否已经进行过基础询问
                if not self._profile_asked_basic:
                    # 第一次询问，标记已询问基础信息
                    self._profile_asked_basic = True
                    self.slot_invalid_profile(text)  # type: ignore
                    return self.ask_profile_again(text)
                else:
                    # 已经询问过基础信息，进行深化询问
                    return self.ask_profile_extend(text)
        
        # 特殊处理INIT状态
        if current_state == 'INIT':
            # 首次对话，强制进入目的地询问流程
            self.machine.set_state('SLOT_FILLING_DESTINATION')
            # 检查用户输入是否已经包含目的地信息
            if self._has_destination_info(text, check_deep_process=False):
                # 用户提供了目的地信息，转移到深化询问状态
                self.user_provides_destination(text)  # type: ignore
                return self.ask_destination_deep(text)
            else:
                # 用户没有提供目的地信息，询问目的地
                return self.ask_destination()
        
        # 如果不在槽位填充状态，找下一个未填槽位
        next_slot = self._get_next_empty_slot()
        if next_slot:
            # 还有未填充的槽位，转移到对应状态
            if next_slot == 'destination':
                # 目的地需要特殊处理，根据当前状态决定下一步
                if self.state == 'SLOT_FILLING_DESTINATION':
                    return self.ask_destination()
                elif self.state == 'SLOT_FILLING_DESTINATION_DEEP':
                    return self.ask_destination_deep()
                elif self.state == 'SLOT_FILLING_DESTINATION_CONFIRM':
                    return self.ask_destination_confirm()
                else:
                    # 如果不在目的地相关状态，转移到初始目的地状态
                    self.machine.set_state('SLOT_FILLING_DESTINATION')
                    return self.ask_destination()
            elif next_slot == 'budget':
                target_state = 'SLOT_FILLING_BUDGET'
                if self.state != target_state:
                    self.machine.set_state(target_state)
                return self.ask_budget()
            elif next_slot == 'dates':
                target_state = 'SLOT_FILLING_DATES'
                if self.state != target_state:
                    self.machine.set_state(target_state)
                return self.ask_dates()
            elif next_slot == 'profile':
                target_state = 'SLOT_FILLING_PROFILE'
                if self.state != target_state:
                    self.machine.set_state(target_state)
                return self.ask_profile()
        else:
            # 所有槽位都已填充，进入确认状态
            if self.state != 'CONFIRMATION':
                self.machine.set_state('CONFIRMATION')
                return self.ask_confirmation()
        
        # 如果当前已经在确认状态，返回确认询问
        if self.state == 'CONFIRMATION':
            return self.ask_confirmation()
        elif self.state == 'COMPLETED':
            return self.show_plan()
        elif self.state == 'ERROR':
            return self.error_handler()
        
        response = "抱歉，我不太理解您的意思。"
        self.add_assistant_message(response)
        return response
    
    def _has_destination_info(self, text: str, check_deep_process: bool = True) -> bool:
        """检查用户输入是否包含目的地信息"""
        # 优先检查session中是否已经提取到目的地信息
        if self.session.locations and len(self.session.locations) > 0:
            location = self.session.locations[0]
            if location and str(location).strip():
                # 如果需要检查深化流程，确保不在深化询问状态
                if check_deep_process and self.state in ['SLOT_FILLING_DESTINATION_DEEP', 'SLOT_FILLING_DESTINATION_CONFIRM']:
                    return False
                return True
        
        # 如果session中没有目的地信息，返回False
        # 不再进行简单的关键词匹配，因为这会误判
        return False
    
    def _has_budget_info(self, text: str) -> bool:
        """检查用户输入是否包含预算信息"""
        # 优先检查session中是否已经提取到预算信息
        if self.session.budget is not None and str(self.session.budget).strip():
            return True
        
        # 如果session中没有预算信息，返回False
        return False
    
    def _has_dates_info(self, text: str) -> bool:
        """检查用户输入是否包含日期信息"""
        # 优先检查session中是否已经提取到日期信息
        if self.session.start_date and self.session.end_date:
            return True
        
        # 如果session中没有日期信息，返回False
        return False
    
    def _has_profile_info(self, text: str) -> bool:
        """检查用户输入是否包含用户画像信息"""
        # 优先检查session中是否已经提取到用户画像信息
        if self.session.user_profile:
            # 检查必须的关键字段
            required_fields = ["同行人员", "旅行风格"]
            has_required_fields = True
            
            for field in required_fields:
                value = self.session.user_profile.get(field)
                if not value or value == "未提及" or not str(value).strip():
                    has_required_fields = False
                    break
            
            if not has_required_fields:
                return False
            
            # 检查是否有其他有效字段
            profile_info = []
            expected_fields = [
                "情感状态", "同行人员", "旅行风格", "兴趣爱好", "避雷", 
                "饮食习惯", "年龄", "性别", "职业", "特殊需求"
            ]
            
            for field in expected_fields:
                value = self.session.user_profile.get(field)
                if value and value != "未提及" and str(value).strip():
                    profile_info.append(f"{field}: {value}")
            
            if profile_info:
                return True
        
        # 如果session中没有用户画像信息，返回False
        return False
    
    def _update_slots_from_session(self):
        """从 session 数据更新槽位"""
        # 更新目的地
        if self.session.locations and len(self.session.locations) > 0:
            # 处理多个目的地的情况
            valid_locations = []
            for location in self.session.locations:
                if location and str(location).strip():
                    valid_locations.append(str(location))
            
            if valid_locations:
                if len(valid_locations) == 1:
                    self.slots['destination'] = valid_locations[0]
                else:
                    # 多个目的地用"、"连接
                    self.slots['destination'] = "、".join(valid_locations)
            else:
                self.slots['destination'] = None
        else:
            self.slots['destination'] = None
        
        # 更新预算
        if self.session.budget is not None and str(self.session.budget).strip():
            self.slots['budget'] = self.session.budget
        else:
            self.slots['budget'] = None
        
        # 更新日期
        if self.session.start_date and self.session.end_date:
            self.slots['dates'] = {
                'start_date': self.session.start_date,
                'end_date': self.session.end_date
            }
        else:
            self.slots['dates'] = None
        
        # 更新用户画像 - 与session_control中的字段保持一致
        if self.session.user_profile:
            # 检查必须的关键字段
            required_fields = ["同行人员", "旅行风格"]
            has_required_fields = True
            
            for field in required_fields:
                value = self.session.user_profile.get(field)
                if not value or value == "未提及" or not str(value).strip():
                    has_required_fields = False
                    break
            
            if not has_required_fields:
                self.slots['profile'] = None
            else:
                profile_info = []
                expected_fields = [
                    "情感状态", "同行人员", "旅行风格", "兴趣爱好", "避雷", 
                    "饮食习惯", "年龄", "性别", "职业", "特殊需求"
                ]
                
                for field in expected_fields:
                    value = self.session.user_profile.get(field)
                    if value and value != "未提及" and str(value).strip():
                        profile_info.append(f"{field}: {value}")
                
                if profile_info:
                    self.slots['profile'] = '; '.join(profile_info)
                else:
                    self.slots['profile'] = None
        else:
            self.slots['profile'] = None
    
    def _get_next_empty_slot(self) -> Optional[str]:
        """获取下一个未填充的槽位"""
        # 检查目的地是否已完成（包括深化询问和确认）
        if not self._has_destination_info("", check_deep_process=True) or self.state in ['SLOT_FILLING_DESTINATION', 'SLOT_FILLING_DESTINATION_DEEP', 'SLOT_FILLING_DESTINATION_CONFIRM']:
            return 'destination'
        
        for slot in ['budget', 'dates', 'profile']:
            value = self.slots[slot]
            if value is None:
                return slot
            elif isinstance(value, str) and not value.strip():
                return slot
            elif isinstance(value, dict) and slot == 'dates':
                # 日期槽位是字典，需要检查start_date和end_date
                if not value.get('start_date') or not value.get('end_date'):
                    return slot
        return None
    
    def _are_all_slots_filled(self) -> bool:
        """检查所有槽位是否都已填充"""
        # 检查目的地是否已完成（包括深化询问和确认）
        if not self._has_destination_info("", check_deep_process=True) or self.state in ['SLOT_FILLING_DESTINATION', 'SLOT_FILLING_DESTINATION_DEEP', 'SLOT_FILLING_DESTINATION_CONFIRM']:
            return False
        
        for slot_name, value in self.slots.items():
            if slot_name == 'destination':
                # 目的地槽位需要特殊处理，确保已经完成深化询问和确认
                continue
            if value is None:
                return False
            elif isinstance(value, str) and not value.strip():
                return False
            elif isinstance(value, dict) and slot_name == 'dates':
                # 日期槽位是字典，需要检查start_date和end_date
                if not value.get('start_date') or not value.get('end_date'):
                    return False
        return True
    
    # ========== 辅助函数 ==========
    
    def _generate_summary(self) -> str:
        """生成信息汇总"""
        summary_parts = []
        if self.slots['destination']:
            summary_parts.append(f"• destination: {self.slots['destination']}")
        if self.slots['budget']:
            summary_parts.append(f"• budget: {self.slots['budget']}")
        if self.slots['dates']:
            dates = self.slots['dates']
            if isinstance(dates, dict):
                start_date = dates.get('start_date', '未设置')
                end_date = dates.get('end_date', '未设置')
                summary_parts.append(f"• start_date: {start_date}")
                summary_parts.append(f"• end_date: {end_date}")
            else:
                summary_parts.append(f"• dates: {dates}")
        if self.slots['profile']:
            # 用户画像信息可能包含多个字段，分行显示
            profile_lines = self.slots['profile'].split('; ')
            for line in profile_lines:
                summary_parts.append(f"• {line}")
        
        return "\n".join(summary_parts) if summary_parts else "暂无信息"
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        return {
            "current_state": self.state,
            "slots": self.slots,
            "state_info": self.session.state,
            "can_transition_to": self.machine.get_triggers(self.state)
        }
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """处理用户消息（兼容旧接口）"""
        response = self.handle_utterance(message)
        return {
            "response": response,
            "current_state": self.state,
            "slots": self.slots,
            "state_info": self.session.state
        }
    
    # ========== Session管理功能 ==========
    
    def create_new_session(self, username: str = 'fangsuo') -> str:
        """创建新的对话会话"""
        try:
            # 获取或创建用户
            self.current_user = self._get_or_create_user(username)
            
            # 创建新的 TalkSession
            self.session = TalkSession.objects.create(
                user=self.current_user,
                history=[],
                state={},
                budget=None,
                locations=[],
                start_date=None,
                end_date=None,
                user_profile={}
            )
            
            # 重新初始化状态机
            self._update_slots_from_session()
            
            logging.info(f"创建新会话成功: {self.session.id}")
            return str(self.session.id)
            
        except Exception as e:
            logging.error(f"创建会话失败: {e}")
            raise e
    
    def load_session(self, session_id: str) -> bool:
        """加载现有的对话会话"""
        try:
            self.session = TalkSession.objects.get(id=session_id)
            self.current_user = self.session.user
            self._update_slots_from_session()
            
            logging.info(f"加载会话成功: {session_id}")
            return True
            
        except TalkSession.DoesNotExist:
            logging.error(f"会话不存在: {session_id}")
            return False
        except Exception as e:
            logging.error(f"加载会话失败: {e}")
            return False
    
    def save_session(self) -> bool:
        """保存当前会话"""
        if not self.session:
            logging.error("没有活跃的会话")
            return False
        
        try:
            self.session.save()
            logging.info(f"保存会话成功: {self.session.id}")
            return True
        except Exception as e:
            logging.error(f"保存会话失败: {e}")
            return False
    
    def add_user_message(self, message: str) -> None:
        """添加用户消息到历史记录"""
        if not self.session:
            raise ValueError("没有活跃的会话")
        
        if not self.session.history:
            self.session.history = []
        
        self.session.history.append({
            "role": "user",
            "content": message
        })
        self.session.save()
    
    def add_assistant_message(self, message: str) -> None:
        """添加助手消息到历史记录"""
        if not self.session:
            raise ValueError("没有活跃的会话")
        
        if not self.session.history:
            self.session.history = []
        
        self.session.history.append({
            "role": "assistant",
            "content": message
        })
        self.session.save()
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        if not self.session:
            return {}
        
        return {
            "session_id": str(self.session.id),
            "user": self.current_user.username if self.current_user else None,
            "created_at": self.session.created_at,
            "updated_at": self.session.updated_at,
            "conversation_rounds": len(self.session.history) // 2 if self.session.history else 0,
            "current_state": self.state,
            "collected_info": self._get_collected_info()
        }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        if not self.session or not self.session.history:
            return []
        
        return self.session.history.copy()
    
    def get_slots_info(self) -> Dict[str, Any]:
        """获取槽位信息"""
        slots_info = {}
        for slot_name, slot_value in self.slots.items():
            status = "已填充" if slot_value else "未填充"
            slots_info[slot_name] = {
                "status": status,
                "value": slot_value
            }
        return slots_info
    
    def _get_or_create_user(self, username: str) -> User:
        """获取或创建用户"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@example.com',
                password=f'{username}_password_123'
            )
            logging.info(f"创建用户: {username}")
        
        return user
    
    def _get_collected_info(self) -> List[str]:
        """获取已收集的信息"""
        collected = []
        if self.slots['destination']:
            collected.append(f"目的地: {self.slots['destination']}")
        if self.slots['budget']:
            collected.append(f"预算: {self.slots['budget']}")
        if self.slots['dates']:
            dates = self.slots['dates']
            if isinstance(dates, dict):
                start_date = dates.get('start_date', '未设置')
                end_date = dates.get('end_date', '未设置')
                collected.append(f"日期: {start_date} 至 {end_date}")
        if self.slots['profile']:
            collected.append(f"用户画像: {self.slots['profile']}")
        
        return collected
    
    def set_poi_search_callback(self, callback):
        """设置POI搜索结果回调函数"""
        self._poi_search_callback = callback

    def get_latest_poi_search_result(self) -> Optional[Dict[str, Any]]:
        """获取最近一次POI搜索结果"""
        if hasattr(self, '_latest_poi_search_result'):
            return self._latest_poi_search_result
        return None
    
    # ========== 流式处理方法 ==========
    
    def _process_stream_response(self, response_stream, default_response: str, check_end: bool = False) -> Generator[Dict[str, Any], None, None]:
        """通用流式响应处理方法
        
        Args:
            response_stream: 流式响应流
            default_response: 默认响应文本
            check_end: 是否检查END标记
        """
        full_content = ""
        try:
            for chunk in response_stream:
                if chunk['type'] == 'content':
                    full_content += chunk['chunk']
                    
                    # 如果需要检查END标记
                    if check_end and full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    yield {
                        'type': 'content',
                        'chunk': chunk['chunk'],
                        'full_content': full_content
                    }
                elif chunk['type'] == 'done':
                    # 如果需要检查END标记
                    if check_end and full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    # 流式内容完成，添加到历史记录
                    self.add_assistant_message(full_content)
                    yield {
                        'type': 'done',
                        'full_content': full_content
                    }
                    return
                elif chunk['type'] == 'event':
                    yield chunk
                    
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            # 如果流式处理失败，使用默认回复
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_destination_again_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """重新询问目的地（流式版本）"""
        logging.info("重新询问用户目的地（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的目的地信息，请重新引导用户说明想去的地方。"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_destination_again",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请重新告诉我您的目的地。', check_end=True)
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请重新告诉我您的目的地。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_destination_deep_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """深化询问目的地（流式版本）"""
        logging.info("深化询问用户目的地（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_destination_deep",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            full_content = ""
            for chunk in response_stream:
                if chunk['type'] == 'content':
                    full_content += chunk['chunk']
                    
                    # 检查大模型是否返回了"END"
                    if full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    yield {
                        'type': 'content',
                        'chunk': chunk['chunk'],
                        'full_content': full_content
                    }
                elif chunk['type'] == 'done':
                    # 再次检查大模型是否返回了"END"（以防万一）
                    if full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    # 流式内容完成，添加到历史记录
                    self.add_assistant_message(full_content)
                    yield {
                        'type': 'done',
                        'full_content': full_content
                    }
                    
                    # 在大模型回复后，自动进行关键词生成和POI搜索，仅缓存结果
                    try:
                        from hunter.services.poi_search_pipeline import POISearchPipeline
                        conversation = self.get_conversation_history()
                        session_info = self.get_session_info()
                        pipeline = POISearchPipeline()
                        result = pipeline.search_by_conversation(conversation, session_info)
                        # 缓存结果并通过回调传递
                        self._latest_poi_search_result = result
                        if self._poi_search_callback:
                            self._poi_search_callback(result)
                    except Exception as e:
                        logging.error(f"自动POI搜索失败: {e}")
                        self._latest_poi_search_result = None
                    
                    return
                elif chunk['type'] == 'event':
                    yield chunk
                    
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请告诉我更多关于您想去的地方的信息。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_destination_confirm_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """确认目的地信息（流式版本）"""
        logging.info("确认用户目的地信息（流式）")
        
        # 硬编码检测用户确认关键词
        if user_input:
            confirm_keywords = ['确认', '是的', '对的', '可以', '进入下一阶段']
            if any(keyword in user_input for keyword in confirm_keywords):
                logging.info(f"用户确认目的地信息: {user_input}")
                yield {
                    'type': 'end',
                    'full_content': 'END'
                }
                return
        
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_destination_confirm",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            full_content = ""
            for chunk in response_stream:
                if chunk['type'] == 'content':
                    full_content += chunk['chunk']
                    
                    # 检查大模型是否返回了"END"
                    if full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    yield {
                        'type': 'content',
                        'chunk': chunk['chunk'],
                        'full_content': full_content
                    }
                elif chunk['type'] == 'done':
                    # 再次检查大模型是否返回了"END"（以防万一）
                    if full_content.strip().upper() == "END":
                        yield {
                            'type': 'end',
                            'full_content': full_content
                        }
                        return
                    
                    # 流式内容完成，添加到历史记录
                    self.add_assistant_message(full_content)
                    yield {
                        'type': 'done',
                        'full_content': full_content
                    }
                    return
                elif chunk['type'] == 'event':
                    yield chunk
                    
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请确认您的目的地信息。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_budget_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """询问预算（流式版本）"""
        logging.info("询问用户预算（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="ask_budget",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '您的预算大概是多少？')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '您的预算大概是多少？'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_budget_again_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """重新询问预算（流式版本）"""
        logging.info("重新询问用户预算（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的预算信息，请重新引导用户说明预算。"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_budget_again",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请重新告诉我您的预算。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请重新告诉我您的预算。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_dates_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """询问日期（流式版本）"""
        logging.info("询问用户日期（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="ask_dates",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '您计划什么时候出发、什么时候回来？')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '您计划什么时候出发、什么时候回来？'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_dates_again_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """重新询问日期（流式版本）"""
        logging.info("重新询问用户日期（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中没有明确的日期信息，请重新引导用户说明出发和返回日期。"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_dates_again",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请重新告诉我您的出发和返回日期。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请重新告诉我您的出发和返回日期。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_profile_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """询问用户画像（流式版本）"""
        logging.info("询问用户画像（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="ask_profile",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请告诉我您的同行人员和旅行偏好。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请告诉我您的同行人员和旅行偏好。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_profile_again_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """重新询问用户画像（流式版本）"""
        logging.info("重新询问用户画像（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n注意：用户刚才的回答中缺少一些信息，请自然地引导用户提供更多关于同行人员和旅行偏好的信息。"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_profile_again",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请重新告诉我您的同行人员和旅行偏好。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请重新告诉我您的同行人员和旅行偏好。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_profile_extend_stream(self, user_input: str = "", *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """深化询问用户画像（流式版本）"""
        logging.info("深化询问用户画像（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        # 构建包含用户刚才回答的上下文
        additional_context = ""
        if user_input:
            additional_context = f"\n用户刚才的回答：{user_input}\n任务：根据用户的回答，进行纵向和横向拓展询问。纵向：深入询问用户提到的具体偏好（如具体的美食类型、具体的文化景点等）。横向：询问用户未提及但相关的信息（如年龄、职业、特殊需求等）。"
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info + additional_context, 
                chat_type="ask_profile_extend",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '请告诉我更多关于您的旅行偏好。', check_end=True)
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '请告诉我更多关于您的旅行偏好。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def ask_confirmation_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """询问确认（流式版本）"""
        summary = self._generate_summary()
        logging.info("询问用户确认信息（流式）")
        context_info = self._prepare_context_info(summary=summary)
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="ask_confirmation",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                summary=summary,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, f'请确认以下信息是否都正确：\n{summary}\n如无误，请回复"确认"。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = f'请确认以下信息是否都正确：\n{summary}\n如无误，请回复"确认"。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def show_plan_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """显示计划（流式版本）"""
        logging.info("显示旅行计划（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        full_response = ""
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="show_plan",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            # 收集完整的响应内容
            for chunk in self._process_stream_response(response_stream, '好的，正在为您生成行程方案…'):
                if chunk.get('type') == 'content':
                    full_response += chunk.get('chunk', '')
                yield chunk
            
            # 添加助手消息到历史记录
            self.add_assistant_message(full_response)
            
            # 使用 RouteTimeService 解析行程并保存到数据库
            try:
                from planner.services.route_time_service import RouteTimeService
                from planner.services.trip_service import TripService
                from datetime import date
                
                # 初始化 RouteTimeService
                route_service = RouteTimeService()
                
                # 从会话中获取用户信息
                user = self.session.user
                
                # 从槽位中获取开始日期
                start_date = None
                if self.slots.get('dates') and isinstance(self.slots['dates'], dict):
                    start_date_str = self.slots['dates'].get('start_date')
                    if start_date_str:
                        try:
                            start_date = date.fromisoformat(start_date_str)
                        except ValueError:
                            start_date = date.today()
                else:
                    start_date = date.today()
                
                # 从槽位中获取目的地信息作为城市提示
                city_hint = None
                if self.slots.get('destination'):
                    destination = self.slots['destination']
                    if isinstance(destination, list) and destination:
                        city_hint = destination[0]  # 使用第一个目的地作为城市提示
                    elif isinstance(destination, str):
                        city_hint = destination
                
                # 生成行程标题
                trip_title = f"AI规划行程_{self.session.id}"
                if self.slots.get('destination'):
                    dest_str = str(self.slots['destination'])
                    trip_title = f"{dest_str}之旅"
                
                # 生成行程描述
                trip_description = "AI智能规划的个性化旅行行程"
                if self.slots.get('profile'):
                    profile = self.slots['profile']
                    if isinstance(profile, dict):
                        interests = profile.get('兴趣爱好', [])
                        if interests:
                            trip_description = f"适合{', '.join(interests)}爱好者的个性化行程"
                
                # 保存行程到数据库
                trip = route_service.save_plan_to_db(
                    plan_text=full_response,
                    user=user,
                    trip_title=trip_title,
                    trip_description=trip_description,
                    city_hint=city_hint,
                    start_date=start_date
                )
                
                logging.info(f"行程已保存到数据库，Trip ID: {trip.id}")
                
                # 使用 TripService 生成时间线
                timeline_data = TripService.generate_timeline(trip)
                
                # 将时间线数据添加到回复中
                timeline_summary = self._format_timeline_summary(timeline_data)
                timeline_response = f"\n\n📅 详细时间安排：\n{timeline_summary}"
                
                # 更新会话状态，记录已保存的行程ID
                if not self.session.state:
                    self.session.state = {}
                self.session.state['saved_trip_id'] = trip.id
                self.session.save()
                
                # 流式输出时间线
                yield {
                    'type': 'timeline',
                    'content': timeline_response,
                    'trip_id': trip.id
                }
                
            except Exception as e:
                logging.error(f"保存行程到数据库失败: {e}")
                error_response = "\n\n⚠️ 行程已生成，但保存到数据库时遇到问题。"
                yield {
                    'type': 'error',
                    'content': error_response,
                    'error': str(e)
                }
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '好的，正在为您生成行程方案…'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def cancel_flow_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """取消流程（流式版本）"""
        logging.info("用户取消流程（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="cancel_flow",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '好的，已取消当前流程。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '好的，已取消当前流程。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    def error_handler_stream(self, *args, **kwargs) -> Generator[Dict[str, Any], None, None]:
        """错误处理（流式版本）"""
        logging.info("处理错误（流式）")
        context_info = self._prepare_context_info()
        state_info = self.session.state or {}
        collected_info = self._format_collected_info()
        
        try:
            response_stream = self.chat_service.process_chat(
                context_info, 
                chat_type="error_handler",
                phase=state_info.get('phase', '未知'),
                intent=state_info.get('intent', '未知'),
                context=state_info.get('context', '未知'),
                collected_info=collected_info,
                stream=True
            )
            
            yield from self._process_stream_response(response_stream, '抱歉，我遇到了一些问题，请重新开始。')
            
        except Exception as e:
            logging.error(f"流式处理错误: {e}")
            default_response = '抱歉，我遇到了一些问题，请重新开始。'
            self.add_assistant_message(default_response)
            yield {
                'type': 'error',
                'error': str(e),
                'full_content': default_response
            }
    
    # ========== 流式统一处理入口 ==========
    
    def handle_utterance_stream(self, text: str) -> Generator[Dict[str, Any], None, None]:
        """统一入口：处理用户话语，返回流式回复内容"""
        if not self.session:
            raise ValueError("没有活跃的会话")
        
        # 添加用户消息到历史记录
        self.add_user_message(text)
        
        # 分析会话历史并更新 TalkSession
        success, analysis_msg = analyze_and_update_talksession(self.session)
        if not success:
            logging.warning(f"会话分析警告: {analysis_msg}")
        
        # 更新槽位数据（从session_control分析后的数据）
        self._update_slots_from_session()
        
        # 检查是否是确认消息
        if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步', '差不多了', '就这样']):
            if self.state == 'SLOT_FILLING_DESTINATION_CONFIRM':
                # 在目的地确认状态下，用户确认了目的地信息
                self.destination_confirmed()
                yield from self.ask_budget_stream()
                return
            elif self._are_all_slots_filled():
                if self.state != 'CONFIRMATION':
                    self.machine.set_state('CONFIRMATION')
                    yield from self.ask_confirmation_stream()
                    return
                else:
                    self.confirm()
                    yield from self.show_plan_stream()
                    return
        
        # 基于当前状态和用户输入判断是否回答了当前问题
        current_state = self.state
        
        # 基于当前状态和用户输入判断是否回答了当前问题
        if current_state == 'SLOT_FILLING_DESTINATION':
            # 检查用户是否提供了目的地信息
            if self._has_destination_info(text, check_deep_process=False):
                # 用户提供了目的地信息，转移到深化询问状态
                self.user_provides_destination(text)  # type: ignore
                yield from self.ask_destination_deep_stream(text)
                return
            else:
                # 用户没有提供目的地信息，重新询问
                self.slot_invalid_destination(text)  # type: ignore
                yield from self.ask_destination_again_stream(text)
                return
                
        elif current_state == 'SLOT_FILLING_DESTINATION_DEEP':
            # 深化目的地询问状态
            # 首先检查用户是否表达了确认或进入下一阶段的意图
            if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步', '差不多了', '就这样']):
                # 用户表达了确认意图，转移到确认状态
                self.destination_deep_complete()
                yield from self.ask_destination_confirm_stream()
                return
            
            # 收集完整的响应流，检查是否有END标记
            full_content = ""
            has_end = False
            
            for chunk in self.ask_destination_deep_stream(text):
                if chunk['type'] == 'end':
                    # 大模型确认了目的地信息，转移到确认状态
                    has_end = True
                    break
                elif chunk['type'] == 'content':
                    full_content += chunk.get('chunk', '')
                    yield chunk
                else:
                    yield chunk
            
            # 如果检测到END，进行状态转换
            if has_end:
                self.destination_deep_complete()
                yield from self.ask_destination_confirm_stream()
                return
            
        elif current_state == 'SLOT_FILLING_DESTINATION_CONFIRM':
            # 目的地确认状态
            if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步', '差不多了', '就这样']):
                # 用户确认了目的地信息
                self.destination_confirmed()
                yield from self.ask_budget_stream()
                return
            else:
                # 用户没有确认，继续深化询问
                yield from self.ask_destination_confirm_stream(text)
                return
                
        elif current_state == 'SLOT_FILLING_BUDGET':
            # 检查用户是否提供了预算信息
            if self._has_budget_info(text):
                # 用户提供了预算信息，转移到日期询问状态
                self.user_provides_budget(text)  # type: ignore
                yield from self.ask_dates_stream()
                return
            else:
                # 用户没有提供预算信息，重新询问
                self.slot_invalid_budget(text)  # type: ignore
                yield from self.ask_budget_again_stream(text)
                return
                
        elif current_state == 'SLOT_FILLING_DATES':
            # 检查用户是否提供了日期信息
            if self._has_dates_info(text):
                # 用户提供了日期信息，转移到用户画像询问状态
                self.user_provides_dates(text)  # type: ignore
                yield from self.ask_profile_stream()
                return
            else:
                # 用户没有提供日期信息，重新询问
                self.slot_invalid_dates(text)  # type: ignore
                yield from self.ask_dates_again_stream(text)
                return
                
        elif current_state == 'SLOT_FILLING_PROFILE':
            # 检查用户是否提供了用户画像信息
            if self._has_profile_info(text):
                # 用户提供了用户画像信息，检查是否已经进行过深化询问
                if not self._profile_asked_basic:
                    # 第一次回答，标记已询问基础信息，进行深化询问
                    self._profile_asked_basic = True
                    yield from self.ask_profile_extend_stream(text)
                    return
                elif self._profile_asked_basic and not self._profile_asked_again:
                    # 已经进行过基础询问，但还没有进行过again询问，进行深化询问
                    self._profile_asked_again = True
                    yield from self.ask_profile_extend_stream(text)
                    return
                else:
                    # 已经进行过深化询问，转移到确认状态
                    self.user_provides_profile(text)  # type: ignore
                    yield from self.ask_confirmation_stream()
                    return
            else:
                # 用户没有提供用户画像信息，检查是否已经进行过基础询问
                if not self._profile_asked_basic:
                    self._profile_asked_basic = False
                
                if not self._profile_asked_basic:
                    # 第一次询问，标记已询问基础信息
                    self._profile_asked_basic = True
                    self.slot_invalid_profile(text)  # type: ignore
                    yield from self.ask_profile_again_stream(text)
                    return
                else:
                    # 已经询问过基础信息，进行深化询问
                    yield from self.ask_profile_extend_stream(text)
                    return
                
        elif current_state == 'CONFIRMATION':
            # 确认状态
            if any(keyword in text for keyword in ['确认', '正确', '可以', '是的', '对的', '进入下一阶段', '继续', '下一步', '差不多了', '就这样']):
                # 用户确认了所有信息
                self.confirm()
                yield from self.show_plan_stream()
                return
            else:
                # 用户没有确认，重新询问
                yield from self.ask_confirmation_stream()
                return
                
        elif current_state == 'COMPLETED':
            # 完成状态，可以重新开始或处理其他请求
            yield {
                'type': 'completed',
                'full_content': '旅行计划已完成，如需重新规划请告诉我。'
            }
            return
            
        elif current_state == 'ERROR':
            # 错误状态
            yield from self.error_handler_stream()
            return
        
        else:
            # 处理其他状态（包括INIT）
            # 特殊处理INIT状态
            if current_state == 'INIT':
                # 首次对话，强制进入目的地询问流程
                self.machine.set_state('SLOT_FILLING_DESTINATION')
                # 检查用户输入是否已经包含目的地信息
                if self._has_destination_info(text, check_deep_process=False):
                    # 用户提供了目的地信息，转移到深化询问状态
                    self.user_provides_destination(text)  # type: ignore
                    yield from self.ask_destination_deep_stream(text)
                    return
                else:
                    # 用户没有提供目的地信息，询问目的地
                    yield from self.ask_destination_stream()
                    return
            
            # 如果不在槽位填充状态，找下一个未填槽位
            next_slot = self._get_next_empty_slot()
            if next_slot:
                # 还有未填充的槽位，转移到对应状态
                if next_slot == 'destination':
                    # 目的地需要特殊处理，根据当前状态决定下一步
                    if self.state == 'SLOT_FILLING_DESTINATION':
                        yield from self.ask_destination_stream()
                        return
                    elif self.state == 'SLOT_FILLING_DESTINATION_DEEP':
                        yield from self.ask_destination_deep_stream()
                        return
                    elif self.state == 'SLOT_FILLING_DESTINATION_CONFIRM':
                        yield from self.ask_destination_confirm_stream()
                        return
                    else:
                        # 如果不在目的地相关状态，转移到初始目的地状态
                        self.machine.set_state('SLOT_FILLING_DESTINATION')
                        yield from self.ask_destination_stream()
                        return
                elif next_slot == 'budget':
                    target_state = 'SLOT_FILLING_BUDGET'
                    if self.state != target_state:
                        self.machine.set_state(target_state)
                    yield from self.ask_budget_stream()
                    return
                elif next_slot == 'dates':
                    target_state = 'SLOT_FILLING_DATES'
                    if self.state != target_state:
                        self.machine.set_state(target_state)
                    yield from self.ask_dates_stream()
                    return
                elif next_slot == 'profile':
                    target_state = 'SLOT_FILLING_PROFILE'
                    if self.state != target_state:
                        self.machine.set_state(target_state)
                    yield from self.ask_profile_stream()
                    return
            else:
                # 所有槽位都已填充，进入确认状态
                if self.state != 'CONFIRMATION':
                    self.machine.set_state('CONFIRMATION')
                    yield from self.ask_confirmation_stream()
                    return
            
            # 如果当前已经在确认状态，返回确认询问
            if self.state == 'CONFIRMATION':
                yield from self.ask_confirmation_stream()
                return
            elif self.state == 'COMPLETED':
                yield from self.show_plan_stream()
                return
            elif self.state == 'ERROR':
                yield from self.error_handler_stream()
                return
            
            # 未知状态，使用错误处理
            yield from self.error_handler_stream()
            return 