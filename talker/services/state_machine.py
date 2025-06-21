#!/usr/bin/env python
# encoding: utf-8

# type: ignore

from transitions import Machine
from typing import Dict, Any, Optional
from talker.models import TalkSession
from talker.services.session_control import analyze_and_update_talksession
import logging

class TravelAssistantFSM:
    """旅行助手状态机，基于简化的槽位填充模式"""
    
    # 定义状态
    states = [
        'INIT',                    # 初始状态
        'SLOT_FILLING_DESTINATION', # 等待目的地
        'SLOT_FILLING_BUDGET',      # 等待预算
        'SLOT_FILLING_DATES',       # 等待日期
        'SLOT_FILLING_PROFILE',     # 等待用户画像（包含同行人员）
        'CONFIRMATION',             # 确认阶段
        'COMPLETED',                # 完成状态
        'ERROR'                     # 错误状态
    ]
    
    def __init__(self, session: TalkSession):
        self.session = session
        
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
    
    def _setup_transitions(self):
        """设置状态转移"""
        # 从初始状态开始
        self.machine.add_transition('start', 'INIT', 'SLOT_FILLING_DESTINATION', after='ask_destination')
        
        # 目的地槽位
        self.machine.add_transition('user_provides_destination', 'SLOT_FILLING_DESTINATION', 'SLOT_FILLING_BUDGET', after='handle_destination')
        self.machine.add_transition('slot_invalid_destination', 'SLOT_FILLING_DESTINATION', 'SLOT_FILLING_DESTINATION', after='ask_destination_again')
        
        # 预算槽位
        self.machine.add_transition('user_provides_budget', 'SLOT_FILLING_BUDGET', 'SLOT_FILLING_DATES', after='handle_budget')
        self.machine.add_transition('slot_invalid_budget', 'SLOT_FILLING_BUDGET', 'SLOT_FILLING_BUDGET', after='ask_budget_again')
        
        # 日期槽位
        self.machine.add_transition('user_provides_dates', 'SLOT_FILLING_DATES', 'SLOT_FILLING_PROFILE', after='handle_dates')
        self.machine.add_transition('slot_invalid_dates', 'SLOT_FILLING_DATES', 'SLOT_FILLING_DATES', after='ask_dates_again')
        
        # 用户画像槽位
        self.machine.add_transition('user_provides_profile', 'SLOT_FILLING_PROFILE', 'CONFIRMATION', after='ask_confirmation')
        self.machine.add_transition('slot_invalid_profile', 'SLOT_FILLING_PROFILE', 'SLOT_FILLING_PROFILE', after='ask_profile_again')
        
        # 确认阶段
        self.machine.add_transition('confirm', 'CONFIRMATION', 'COMPLETED', after='show_plan')
        
        # 全局转移
        self.machine.add_transition('cancel', '*', 'COMPLETED', after='cancel_flow')
        self.machine.add_transition('error', '*', 'ERROR', after='error_handler')
    
    def _setup_event_handlers(self):
        """设置事件处理函数"""
        # 进入状态时的处理
        self.machine.on_enter_SLOT_FILLING_DESTINATION(self._on_enter_fill_destination)
        self.machine.on_enter_SLOT_FILLING_BUDGET(self._on_enter_fill_budget)
        self.machine.on_enter_SLOT_FILLING_DATES(self._on_enter_fill_dates)
        self.machine.on_enter_SLOT_FILLING_PROFILE(self._on_enter_fill_profile)
        self.machine.on_enter_CONFIRMATION(self._on_enter_confirmation)
        self.machine.on_enter_COMPLETED(self._on_enter_completed)
        self.machine.on_enter_ERROR(self._on_enter_error)
    
    # ========== 状态进入处理函数 ==========
    
    def _on_enter_fill_destination(self):
        """进入填充目的地状态"""
        self.session.state = {
            "phase": "slot_filling",
            "intent": "fill_destination",
            "context": "等待用户提供目的地信息"
        }
        self.session.save()
    
    def _on_enter_fill_budget(self):
        """进入填充预算状态"""
        self.session.state = {
            "phase": "slot_filling",
            "intent": "fill_budget",
            "context": "等待用户提供预算信息"
        }
        self.session.save()
    
    def _on_enter_fill_dates(self):
        """进入填充日期状态"""
        self.session.state = {
            "phase": "slot_filling",
            "intent": "fill_dates",
            "context": "等待用户提供出发和返回日期"
        }
        self.session.save()
    
    def _on_enter_fill_profile(self):
        """进入填充用户画像状态"""
        self.session.state = {
            "phase": "slot_filling",
            "intent": "fill_profile",
            "context": "等待用户提供同行人员和偏好信息"
        }
        self.session.save()
    
    def _on_enter_confirmation(self):
        """进入确认状态"""
        self.session.state = {
            "phase": "confirmation",
            "intent": "confirm_info",
            "context": "汇总信息并等待用户确认"
        }
        self.session.save()
    
    def _on_enter_completed(self):
        """进入完成状态"""
        self.session.state = {
            "phase": "completed",
            "intent": "plan_ready",
            "context": "旅行计划已完成"
        }
        self.session.save()
    
    def _on_enter_error(self):
        """进入错误状态"""
        self.session.state = {
            "phase": "error",
            "intent": "handle_error",
            "context": "处理对话中的错误"
        }
        self.session.save()
    
    # ========== 动作函数 ==========
    
    def ask_destination(self):
        """询问目的地"""
        logging.info("询问用户目的地")
        return "您这次想去哪个城市或景区呢？"
    
    def handle_destination(self, value):
        """处理目的地信息"""
        self.slots['destination'] = value
        logging.info(f"目的地已设置: {value}")
    
    def ask_destination_again(self):
        """重新询问目的地"""
        logging.info("重新询问用户目的地")
        return "抱歉，我没有理解您想去的地方。请重新告诉我您的目的地。"
    
    def ask_budget(self):
        """询问预算"""
        logging.info("询问用户预算")
        return "您的预算大概是？比如 3000–5000 元/人。"
    
    def handle_budget(self, value):
        """处理预算信息"""
        self.slots['budget'] = value
        logging.info(f"预算已设置: {value}")
    
    def ask_budget_again(self):
        """重新询问预算"""
        logging.info("重新询问用户预算")
        return "抱歉，我没有理解您的预算信息。请重新告诉我您的预算。"
    
    def ask_dates(self):
        """询问日期"""
        logging.info("询问用户日期")
        return "您计划什么时候出发、什么时候回来？"
    
    def handle_dates(self, value):
        """处理日期信息"""
        self.slots['dates'] = value
        logging.info(f"日期已设置: {value}")
    
    def ask_dates_again(self):
        """重新询问日期"""
        logging.info("重新询问用户日期")
        return "抱歉，我没有理解您的日期信息。请重新告诉我您的出发和返回日期。"
    
    def ask_profile(self):
        """询问用户画像"""
        logging.info("询问用户画像")
        return "最后请告诉我：同行人数和关系，以及您的旅行风格或其他偏好/需求。"
    
    def handle_profile(self, value):
        """处理用户画像信息"""
        self.slots['profile'] = value
        logging.info(f"用户画像已设置: {value}")
    
    def ask_profile_again(self):
        """重新询问用户画像"""
        logging.info("重新询问用户画像")
        return "抱歉，我没有理解您的信息。请重新告诉我同行人员和您的旅行偏好。"
    
    def ask_confirmation(self):
        """询问确认"""
        summary = self._generate_summary()
        logging.info("询问用户确认信息")
        return f"请确认以下信息是否都正确：\n{summary}\n如无误，请回复"确认"。"
    
    def show_plan(self):
        """显示计划"""
        logging.info("显示旅行计划")
        return "好的，正在为您生成行程方案…（此处展示最终方案）"
    
    def cancel_flow(self):
        """取消流程"""
        logging.info("用户取消流程")
        return "好的，已取消当前流程。"
    
    def error_handler(self):
        """错误处理"""
        logging.error("状态机进入错误状态")
        return "抱歉，出现了一些问题。请重新开始。"
    
    # ========== 统一处理入口 ==========
    
    def handle_utterance(self, text: str) -> Dict[str, Any]:
        """统一入口：处理用户话语"""
        # 使用 session_control 分析会话历史并更新 TalkSession
        success, message = analyze_and_update_talksession(self.session)
        if not success:
            logging.error(f"会话分析失败: {message}")
            self.error()
            return self.get_current_state_info()
        
        # 根据更新后的 session 数据判断槽位填充情况
        self._update_slots_from_session()
        
        # 检查是否是确认消息
        if '确认' in text or '正确' in text or '可以' in text:
            if self._are_all_slots_filled():
                if self.state != 'CONFIRMATION':
                    self.machine.set_state('CONFIRMATION')
                    self.ask_confirmation()
                else:
                    self.confirm()
                return self.get_current_state_info()
        
        # 找下一个未填槽位
        next_slot = self._get_next_empty_slot()
        if next_slot:
            state = f"SLOT_FILLING_{next_slot.upper()}"
            if self.state != state:
                self.machine.set_state(state)
                # 触发询问
                if next_slot == 'destination':
                    self.ask_destination()
                elif next_slot == 'budget':
                    self.ask_budget()
                elif next_slot == 'dates':
                    self.ask_dates()
                elif next_slot == 'profile':
                    self.ask_profile()
        else:
            # 全部填完，进入确认
            if self.state != 'CONFIRMATION':
                self.machine.set_state('CONFIRMATION')
                self.ask_confirmation()
        
        return self.get_current_state_info()
    
    def _update_slots_from_session(self):
        """从 session 数据更新槽位"""
        # 更新目的地
        if self.session.locations and len(self.session.locations) > 0:
            self.slots['destination'] = self.session.locations[0] if isinstance(self.session.locations[0], str) else str(self.session.locations[0])
        
        # 更新预算
        if self.session.budget is not None:
            self.slots['budget'] = self.session.budget
        
        # 更新日期
        if self.session.start_date and self.session.end_date:
            self.slots['dates'] = {
                'start_date': self.session.start_date,
                'end_date': self.session.end_date
            }
        
        # 更新用户画像
        if self.session.user_profile:
            profile_info = []
            if self.session.user_profile.get('同行人员'):
                profile_info.append(f"同行人员: {self.session.user_profile['同行人员']}")
            if self.session.user_profile.get('旅行风格'):
                profile_info.append(f"旅行风格: {self.session.user_profile['旅行风格']}")
            if self.session.user_profile.get('兴趣爱好'):
                profile_info.append(f"兴趣爱好: {self.session.user_profile['兴趣爱好']}")
            if profile_info:
                self.slots['profile'] = '; '.join(profile_info)
    
    def _are_all_slots_filled(self) -> bool:
        """检查所有槽位是否都已填充"""
        return all(self.slots.values())
    
    def _get_next_empty_slot(self) -> Optional[str]:
        """获取下一个未填充的槽位"""
        for slot in ['destination', 'budget', 'dates', 'profile']:
            if not self.slots[slot]:
                return slot
        return None
    
    # ========== 辅助函数 ==========
    
    def _generate_summary(self) -> str:
        """生成信息汇总"""
        summary_parts = []
        if self.slots['destination']:
            summary_parts.append(f"• destination: {self.slots['destination']}")
        if self.slots['budget']:
            summary_parts.append(f"• budget: {self.slots['budget']}")
        if self.slots['dates']:
            summary_parts.append(f"• dates: {self.slots['dates']}")
        if self.slots['profile']:
            summary_parts.append(f"• profile: {self.slots['profile']}")
        
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
        return self.handle_utterance(message) 