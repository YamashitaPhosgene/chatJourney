#!/usr/bin/env python
# encoding: utf-8
#type: ignore

import sys
import os
import json
from typing import Optional, Dict, Any
from django.core.management import execute_from_command_line
from django.conf import settings
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.services.state_machine import TravelAssistantFSM
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CLIService:
    """命令行服务类，提供与状态机系统交互的界面"""
    
    def __init__(self):
        self.fsm: Optional[TravelAssistantFSM] = None
    
    def start_new_session(self) -> None:
        """开始新的对话会话"""
        try:
            # 创建新的状态机实例（会自动创建session）
            self.fsm = TravelAssistantFSM()
            session_id = self.fsm.create_new_session()
            
            # 启动状态机并获取初始回复
            self.fsm.start()  # type: ignore  # 使用状态转移而不是直接设置状态
            initial_response = self.fsm.ask_destination()
            
            print(f"\n🎉 新会话已创建 (ID: {session_id})")
            print("=" * 50)
            print("欢迎使用旅行助手！我将帮助您规划完美的旅行。")
            print("=" * 50)
            print(f"🤖 {initial_response}")
            
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            logging.error(f"创建会话失败: {e}")
    
    def load_session(self, session_id: str) -> bool:
        """加载现有的对话会话"""
        try:
            # 创建状态机实例并加载session
            self.fsm = TravelAssistantFSM()
            if self.fsm.load_session(session_id):
                session_info = self.fsm.get_session_info()
                
                print(f"\n📂 会话已加载 (ID: {session_id})")
                print("=" * 50)
                self._show_session_info(session_info)
                print("=" * 50)
                
                return True
            else:
                print(f"❌ 会话 {session_id} 不存在")
                return False
            
        except Exception as e:
            print(f"❌ 加载会话失败: {e}")
            logging.error(f"加载会话失败: {e}")
            return False
    
    def send_message(self, message: str) -> None:
        """发送消息给状态机"""
        if not self.fsm:
            print("❌ 没有活跃的会话，请先创建或加载会话")
            return
        
        try:
            # 处理用户消息（状态机会自动处理session操作）
            response = self.fsm.handle_utterance(message)
            
            print(f"\n🤖 {response}")
            
            # 显示当前状态信息
            self._show_current_status()
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            logging.error(f"处理消息失败: {e}")
    
    def _show_session_info(self, session_info: Dict[str, Any]) -> None:
        """显示会话信息"""
        if not session_info:
            return
        
        print(f"会话ID: {session_info.get('session_id', '未知')}")
        print(f"用户: {session_info.get('user', '未知')}")
        print(f"创建时间: {session_info.get('created_at', '未知')}")
        print(f"最后更新: {session_info.get('updated_at', '未知')}")
        print(f"对话轮数: {session_info.get('conversation_rounds', 0)}")
        
        # 显示已收集的信息
        collected_info = session_info.get('collected_info', [])
        if collected_info:
            print("已收集信息:")
            for info in collected_info:
                print(f"  - {info}")
        else:
            print("已收集信息: 暂无")
    
    def _show_current_status(self) -> None:
        """显示当前状态"""
        if not self.fsm:
            return
        
        session_info = self.fsm.get_session_info()
        current_state = session_info.get('current_state', '未知')
        
        print(f"\n📊 当前状态: {current_state}")
    
    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
🤖 旅行助手命令行服务

可用命令:
  /new          - 创建新会话
  /load <id>    - 加载现有会话
  /save         - 保存当前会话
  /info         - 显示会话信息
  /status       - 显示当前状态
  /slots        - 显示已收集的槽位信息
  /history      - 显示对话历史
  /help         - 显示此帮助信息
  /quit         - 退出程序

使用示例:
  /new                    # 开始新对话
  /load 123              # 加载ID为123的会话
  /info                   # 查看当前会话信息
  我想去成都旅游          # 发送消息给助手
  /quit                   # 退出程序

提示:
  - 直接输入文本即可与助手对话
  - 使用 / 开头的命令执行系统操作
  - 会话会自动保存，可以随时加载继续对话
        """
        print(help_text)
    
    def show_slots(self) -> None:
        """显示槽位信息"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        slots_info = self.fsm.get_slots_info()
        print("\n📋 槽位信息:")
        print("=" * 30)
        for slot_name, slot_data in slots_info.items():
            status = "✅ 已填充" if slot_data['status'] == "已填充" else "❌ 未填充"
            print(f"{slot_name:12}: {status}")
            if slot_data['value']:
                print(f"{'':12}  值: {slot_data['value']}")
        print("=" * 30)
    
    def show_history(self) -> None:
        """显示对话历史"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        history = self.fsm.get_conversation_history()
        if not history:
            print("❌ 没有对话历史")
            return
        
        print("\n💬 对话历史:")
        print("=" * 50)
        for i, message in enumerate(history, 1):
            role = "👤 用户" if message["role"] == "user" else "🤖 助手"
            content = message["content"]
            print(f"{i:2d}. {role}: {content}")
        print("=" * 50)
    
    def save_session(self) -> None:
        """保存当前会话"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        try:
            if self.fsm.save_session():
                session_info = self.fsm.get_session_info()
                session_id = session_info.get('session_id', '未知')
                print(f"✅ 会话已保存 (ID: {session_id})")
            else:
                print("❌ 保存会话失败")
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
            logging.error(f"保存会话失败: {e}")
    
    def run(self) -> None:
        """运行命令行服务"""
        print("🚀 启动旅行助手命令行服务...")
        print("输入 /help 查看帮助信息")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 请输入消息或命令: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    # 处理普通消息
                    self.send_message(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except EOFError:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                logging.error(f"CLI服务错误: {e}")
    
    def _handle_command(self, command: str) -> None:
        """处理命令"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == '/help':
            self.show_help()
        elif cmd == '/new':
            self.start_new_session()
        elif cmd == '/load' and len(parts) > 1:
            self.load_session(parts[1])
        elif cmd == '/save':
            self.save_session()
        elif cmd == '/info':
            if self.fsm:
                session_info = self.fsm.get_session_info()
                self._show_session_info(session_info)
            else:
                print("❌ 没有活跃的会话")
        elif cmd == '/status':
            self._show_current_status()
        elif cmd == '/slots':
            self.show_slots()
        elif cmd == '/history':
            self.show_history()
        elif cmd == '/quit':
            print("👋 再见！")
            sys.exit(0)
        else:
            print("❌ 未知命令，输入 /help 查看帮助信息")


def main():
    """主函数"""
    cli_service = CLIService()
    cli_service.run()


if __name__ == "__main__":
    main() 