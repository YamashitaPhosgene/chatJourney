# from django.test import TestCase

# # Create your tests here.
# #!/usr/bin/env python
# # encoding: utf-8

# import os
# import sys
# import django
# from dotenv import load_dotenv

# # 自动加载根目录下的 .env 文件
# load_dotenv()
# # 设置Django环境
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
# django.setup()

# from talker.api import VivoGPT, VivoGPTError

# def print_section(title: str):
#     """打印测试章节标题"""
#     print(f"\n{'='*20} {title} {'='*20}")

# def print_subsection(title: str):
#     """打印测试子章节标题"""
#     print(f"\n--- {title} ---")

# def test_prompt_management():
#     """测试预设管理功能"""
#     print_section("预设管理测试")
#     chat = VivoGPT()
    
#     # 测试列出预设
#     print_subsection("列出所有预设")
#     prompts = chat.list_prompts()
#     for type, data in prompts.items():
#         print(f"- {type}: {data.get('description', '')}")
    
#     # 测试获取预设
#     print_subsection("获取预设内容")
#     system_prompt = chat.get_prompt("programmer")
#     print(f"编程助手预设: {system_prompt}")

# def test_basic_chat():
#     """测试基本对话功能（不使用预设）"""
#     print_section("基本对话测试")
#     chat = VivoGPT()
    
#     # 测试简单对话
#     print_subsection("简单对话")
#     response = chat.chat("你好，请介绍一下你自己")
#     print(f"AI回复: {response['data']['content']}")
    
#     # 测试带参数的对话
#     print_subsection("带参数的对话")
#     response = chat.chat(
#         "写一个简单的Python函数",
#         temperature=0.8,
#         max_tokens=1024
#     )
#     print(f"AI回复: {response['data']['content']}")

# def test_prompt_chat():
#     """测试预设对话功能"""
#     print_section("预设对话测试")
#     chat = VivoGPT()
    
#     # 测试编程助手
#     print_subsection("编程助手")
#     response = chat.chat(
#         "写一个Python函数计算斐波那契数列",
#         type="programmer"
#     )
#     print(f"AI回复: {response['data']['content']}")
    
#     # 测试翻译助手
#     print_subsection("翻译助手")
#     response = chat.chat(
#         "将'Hello, how are you?'翻译成中文",
#         type="translator"
#     )
#     print(f"AI回复: {response['data']['content']}")
    
#     # 测试写作助手
#     print_subsection("写作助手")
#     response = chat.chat(
#         "写一首关于春天的诗",
#         type="writer"
#     )
#     print(f"AI回复: {response['data']['content']}")
    
#     # 测试代码审查
#     print_subsection("代码审查")
#     response = chat.chat(
#         """请审查以下Python代码：
# def fibonacci(n):
#     if n <= 0:
#         return 0
#     elif n == 1:
#         return 1
#     else:
#         return fibonacci(n-1) + fibonacci(n-2)""",
#         type="code_review"
#     )
#     print(f"AI回复: {response['data']['content']}")
    
#     # 测试问题诊断
#     print_subsection("问题诊断")
#     response = chat.chat(
#         "我的Python程序运行很慢，可能是什么原因？",
#         type="troubleshooting"
#     )
#     print(f"AI回复: {response['data']['content']}")

# def test_chat_with_history():
#     """测试多轮对话功能"""
#     print_section("多轮对话测试")
#     chat = VivoGPT()
    
#     messages = [
#         {"role": "user", "content": "你好，我想学习Python"},
#         {"role": "assistant", "content": "很高兴帮助你学习Python！Python是一门非常受欢迎的编程语言，它简单易学，功能强大。你想从哪个方面开始学习呢？"},
#         {"role": "user", "content": "我想先学习基础语法"}
#     ]
    
#     print_subsection("多轮对话")
#     response = chat.chat_with_history(messages)
#     print(f"AI回复: {response['data']['content']}")

# def test_error_handling():
#     """测试错误处理"""
#     print_section("错误处理测试")
#     chat = VivoGPT()
    
#     # 测试不存在的预设
#     print_subsection("不存在的预设")
#     try:
#         response = chat.chat(
#             "测试消息",
#             type="non_existent_prompt"
#         )
#     except ValueError as e:
#         print(f"预期的错误: {e}")
    
#     # 测试无效的参数
#     print_subsection("无效的参数")
#     try:
#         response = chat.chat(
#             "测试消息",
#             temperature=2.5  # 超出范围
#         )
#     except ValueError as e:
#         print(f"预期的错误: {e}")

# def main():
#     """运行所有测试"""
#     try:
#         # 首先测试预设管理功能
#         test_prompt_management()
        
#         # 然后测试基本对话功能
#         test_basic_chat()
        
#         # 测试预设对话功能
#         test_prompt_chat()
        
#         # 测试多轮对话功能
#         test_chat_with_history()
        
#         # 最后测试错误处理
#         test_error_handling()
        
#         print("\n所有测试完成！")
#     except Exception as e:
#         print(f"\n测试过程中出现错误: {e}")

# if __name__ == "__main__":
#     main() 

from talker.models import TalkSession
from talker.services.session_control import analyze_and_update_talksession
from django.contrib.auth.models import User
import datetime

def test_analyze_and_update_talksession():
    """测试自动分析历史并更新 TalkSession"""
    # 创建测试用户
    user, _ = User.objects.get_or_create(username="fangsuo")
    # 构造模拟历史
    history = [
        {"role": "user", "content": "工作好累，我想这个周末出去玩。"},
        {"role": "assistant", "content": "好的，请问想玩几天？"},
        {"role": "user", "content": "1天。"},
        {"role": "assistant", "content": "这周六可以嘛？"},
        {"role": "user", "content": "可以。"},
        {"role": "assistant", "content": "有没有具体想去哪里玩呢？"},
        {"role": "user", "content": "没有，为我推荐一个。"},
        {"role": "assistant", "content": "好的，我推荐你去北京故宫博物院。"},
        {"role": "user", "content": "太远了，近点。而且我不喜欢去人多的地方，也不喜欢博物馆。"},
        {"role": "assistant", "content": "好的，那附近的公园怎么样？"}
    ]
    session = TalkSession.objects.create(user=user, history=history)
    success, msg = analyze_and_update_talksession(session)
    print("分析结果：", success, msg)
    session.refresh_from_db()
    print("budget:", session.budget)
    print("locations:", session.locations)
    print("start_date:", session.start_date)
    print("end_date:", session.end_date)
    print("user_profile:", session.user_profile)
    print("state:", session.state)
    assert success is True
    assert session.budget is not None
    assert isinstance(session.locations, list) and len(session.locations) > 0
    assert session.start_date is not None
    assert session.end_date is not None
    assert isinstance(session.user_profile, dict)
    assert isinstance(session.state, dict) 