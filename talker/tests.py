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















# from talker.models import TalkSession
# from talker.services.session_control import analyze_and_update_talksession
# from django.contrib.auth.models import User
# import datetime

# def test_analyze_and_update_talksession():
#     """测试自动分析历史并更新 TalkSession"""
#     # 创建测试用户
#     user, _ = User.objects.get_or_create(username="fangsuo")
#     # 构造模拟历史
#     history = [
#         {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
#         {"role": "user", "content": "想去云南玩。"},
#         {"role": "assistant", "content": "云南风景超美！请问大概想花多少钱？您可以给个区间~"},
#         {"role": "user", "content": "5000–8000 元/人。"},
#         {"role": "assistant", "content": "好的。那您计划哪天出发？大概几天行程？"},
#         {"role": "user", "content": "8月10日走，8月15日回，一共6天。"},
#         {"role": "assistant", "content": "明白！会有朋友或家人一同出行吗？"},
#         {"role": "user", "content": "我和两个闺蜜。"},
#         {"role": "assistant", "content": "棒！大家更想体验自然风光还是文艺小镇？"},
#         {"role": "user", "content": "自然风光。"}
#     ]

#     session = TalkSession.objects.create(user=user, history=history)
#     success, msg = analyze_and_update_talksession(session)
#     print("分析结果：", success, msg)
#     session.refresh_from_db()
#     print("budget:", session.budget)
#     print("locations:", session.locations)
#     print("start_date:", session.start_date)
#     print("end_date:", session.end_date)
#     print("user_profile:", session.user_profile)
#     print("state:", session.state)
#     assert success is True
#     assert session.budget is None or isinstance(session.budget, (int, float, str))
#     assert isinstance(session.locations, list)  # 允许空数组
#     assert session.start_date is not None
#     assert session.end_date is not None
#     assert isinstance(session.user_profile, dict)
#     assert isinstance(session.state, dict) 

#!/usr/bin/env python
# encoding: utf-8
# type: ignore
import os
import sys
import django
from dotenv import load_dotenv

# 自动加载根目录下的 .env 文件
load_dotenv()
# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.models import TalkSession
from talker.services.state_machine import TravelAssistantFSM
from talker.services.session_control import analyze_and_update_talksession
from django.contrib.auth.models import User
import datetime

def print_section(title: str):
    """打印测试章节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def print_subsection(title: str):
    """打印测试子章节标题"""
    print(f"\n--- {title} ---")

def test_state_machine_initialization():
    """测试状态机初始化"""
    print_section("状态机初始化测试")
    
    # 创建测试用户和会话
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    
    # 初始化状态机
    fsm = TravelAssistantFSM(session)
    
    # 验证初始状态
    assert fsm.state == 'INIT'
    assert fsm.slots == {
        'destination': None,
        'budget': None,
        'dates': None,
        'profile': None
    }
    
    print("✓ 状态机初始化成功")
    print(f"  初始状态: {fsm.state}")
    print(f"  初始槽位: {fsm.slots}")

def test_state_transitions():
    """测试状态转换"""
    print_section("状态转换测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 测试开始对话
    print_subsection("开始对话")
    fsm.start()
    assert fsm.state == 'SLOT_FILLING_DESTINATION'
    print(f"✓ 成功转换到目的地填充状态: {fsm.state}")
    
    # 测试目的地填充
    print_subsection("目的地填充")
    fsm.user_provides_destination("云南")
    assert fsm.state == 'SLOT_FILLING_BUDGET'
    assert fsm.slots['destination'] == "云南"
    print(f"✓ 成功转换到预算填充状态: {fsm.state}")
    
    # 测试预算填充
    print_subsection("预算填充")
    fsm.user_provides_budget("5000-8000")
    assert fsm.state == 'SLOT_FILLING_DATES'
    assert fsm.slots['budget'] == "5000-8000"
    print(f"✓ 成功转换到日期填充状态: {fsm.state}")
    
    # 测试日期填充
    print_subsection("日期填充")
    fsm.user_provides_dates({"start_date": "2024-08-10", "end_date": "2024-08-15"})
    assert fsm.state == 'SLOT_FILLING_PROFILE'
    assert fsm.slots['dates'] == {"start_date": "2024-08-10", "end_date": "2024-08-15"}
    print(f"✓ 成功转换到用户画像填充状态: {fsm.state}")
    
    # 测试用户画像填充
    print_subsection("用户画像填充")
    fsm.user_provides_profile("和两个闺蜜，喜欢自然风光")
    assert fsm.state == 'CONFIRMATION'
    assert fsm.slots['profile'] == "和两个闺蜜，喜欢自然风光"
    print(f"✓ 成功转换到确认状态: {fsm.state}")
    
    # 测试确认
    print_subsection("确认")
    fsm.confirm()
    assert fsm.state == 'COMPLETED'
    print(f"✓ 成功转换到完成状态: {fsm.state}")

def test_slot_validation():
    """测试槽位校验"""
    print_section("槽位校验测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    fsm.start()
    
    # 测试无效目的地
    print_subsection("无效目的地")
    fsm.slot_invalid_destination()
    assert fsm.state == 'SLOT_FILLING_DESTINATION'
    print("✓ 无效目的地保持在原状态")
    
    # 测试无效预算
    print_subsection("无效预算")
    fsm.user_provides_destination("云南")
    fsm.slot_invalid_budget()
    assert fsm.state == 'SLOT_FILLING_BUDGET'
    print("✓ 无效预算保持在原状态")
    
    # 测试无效日期
    print_subsection("无效日期")
    fsm.user_provides_budget("5000")
    fsm.slot_invalid_dates()
    assert fsm.state == 'SLOT_FILLING_DATES'
    print("✓ 无效日期保持在原状态")
    
    # 测试无效用户画像
    print_subsection("无效用户画像")
    fsm.user_provides_dates({"start_date": "2024-08-10", "end_date": "2024-08-15"})
    fsm.slot_invalid_profile()
    assert fsm.state == 'SLOT_FILLING_PROFILE'
    print("✓ 无效用户画像保持在原状态")

def test_global_transitions():
    """测试全局状态转换"""
    print_section("全局状态转换测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 测试取消操作
    print_subsection("取消操作")
    fsm.start()
    fsm.cancel()
    assert fsm.state == 'COMPLETED'
    print("✓ 取消操作成功转换到完成状态")
    
    # 测试错误处理
    print_subsection("错误处理")
    fsm = TravelAssistantFSM(session)
    fsm.start()
    fsm.error()
    assert fsm.state == 'ERROR'
    print("✓ 错误处理成功转换到错误状态")

def test_slot_management():
    """测试槽位管理"""
    print_section("槽位管理测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 测试槽位更新
    print_subsection("槽位更新")
    fsm._update_slots_from_session()
    assert fsm.slots == {
        'destination': None,
        'budget': None,
        'dates': None,
        'profile': None
    }
    print("✓ 空会话的槽位更新正确")
    
    # 测试槽位填充检查
    print_subsection("槽位填充检查")
    assert not fsm._are_all_slots_filled()
    print("✓ 空槽位检查正确")
    
    # 测试获取下一个空槽位
    print_subsection("获取下一个空槽位")
    next_slot = fsm._get_next_empty_slot()
    assert next_slot == 'destination'
    print(f"✓ 下一个空槽位: {next_slot}")
    
    # 测试部分填充的槽位
    print_subsection("部分填充槽位")
    fsm.slots['destination'] = "云南"
    fsm.slots['budget'] = "5000"
    next_slot = fsm._get_next_empty_slot()
    assert next_slot == 'dates'
    print(f"✓ 部分填充后下一个空槽位: {next_slot}")

def test_session_integration():
    """测试与session的集成"""
    print_section("Session集成测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    
    # 逐步构建对话历史
    session = TalkSession.objects.create(user=user)
    
    # 第一轮：目的地
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～"},
        {"role": "user", "content": "想去云南玩。"}
    ]
    session.save()
    
    # 第二轮：预算
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "请问预算大概是多少？"},
        {"role": "user", "content": "5000–8000 元/人。"}
    ]
    session.save()
    
    # 第三轮：日期
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "请问预算大概是多少？"},
        {"role": "user", "content": "5000–8000 元/人。"},
        {"role": "assistant", "content": "计划什么时候出发？"},
        {"role": "user", "content": "8月10日走，8月15日回。"}
    ]
    session.save()
    
    # 第四轮：同行人员和偏好
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "请问预算大概是多少？"},
        {"role": "user", "content": "5000–8000 元/人。"},
        {"role": "assistant", "content": "计划什么时候出发？"},
        {"role": "user", "content": "8月10日走，8月15日回。"},
        {"role": "assistant", "content": "和谁一起旅行？"},
        {"role": "user", "content": "我和两个闺蜜，喜欢自然风光和摄影。"}
    ]
    session.save()
    
    # 让analyze_and_update_talksession真正分析对话历史
    print_subsection("分析对话历史")
    success, message = analyze_and_update_talksession(session)
    print(f"分析结果: {success}, {message}")
    
    # 刷新session数据
    session.refresh_from_db()
    print(f"提取的locations: {session.locations}")
    print(f"提取的budget: {session.budget}")
    print(f"提取的start_date: {session.start_date}")
    print(f"提取的end_date: {session.end_date}")
    print(f"提取的user_profile: {session.user_profile}")
    
    fsm = TravelAssistantFSM(session)
    
    # 测试从session更新槽位
    print_subsection("从session更新槽位")
    fsm._update_slots_from_session()
    
    print(f"更新后的槽位: {fsm.slots}")
    
    # 验证槽位是否正确填充（基于实际提取的结果）
    if session.locations:
        assert fsm.slots['destination'] is not None
    if session.budget:
        assert fsm.slots['budget'] is not None
    if session.start_date and session.end_date:
        assert fsm.slots['dates'] is not None
    if session.user_profile:
        assert fsm.slots['profile'] is not None
    
    print("✓ 从session更新槽位成功")
    
    # 测试槽位填充状态
    print_subsection("槽位填充状态检查")
    filled_slots = sum(1 for slot in fsm.slots.values() if slot is not None)
    print(f"已填充槽位数量: {filled_slots}/{len(fsm.slots)}")
    print("✓ 槽位填充状态检查完成")

def test_state_info():
    """测试状态信息获取"""
    print_section("状态信息测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 测试获取当前状态信息
    print_subsection("获取当前状态信息")
    state_info = fsm.get_current_state_info()
    
    assert 'current_state' in state_info
    assert 'slots' in state_info
    assert 'state_info' in state_info
    assert 'can_transition_to' in state_info
    
    print(f"✓ 状态信息获取成功")
    print(f"  当前状态: {state_info['current_state']}")
    print(f"  可用转换: {state_info['can_transition_to']}")

def test_summary_generation():
    """测试信息汇总生成"""
    print_section("信息汇总测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 测试空槽位汇总
    print_subsection("空槽位汇总")
    summary = fsm._generate_summary()
    assert summary == "暂无信息"
    print("✓ 空槽位汇总正确")
    
    # 测试部分填充汇总
    print_subsection("部分填充汇总")
    fsm.slots['destination'] = "云南"
    fsm.slots['budget'] = "5000-8000"
    summary = fsm._generate_summary()
    assert "destination: 云南" in summary
    assert "budget: 5000-8000" in summary
    print("✓ 部分填充汇总正确")
    
    # 测试完整汇总
    print_subsection("完整汇总")
    fsm.slots['dates'] = {"start_date": "2024-08-10", "end_date": "2024-08-15"}
    fsm.slots['profile'] = "同行人员: 两个闺蜜; 旅行风格: 自然风光; 兴趣爱好: 摄影"
    summary = fsm._generate_summary()
    assert "destination: 云南" in summary
    assert "budget: 5000-8000" in summary
    assert "dates: " in summary
    assert "同行人员: 两个闺蜜" in summary
    assert "旅行风格: 自然风光" in summary
    assert "兴趣爱好: 摄影" in summary
    print("✓ 完整汇总正确")

def test_handle_utterance_with_history():
    """测试handle_utterance方法与对话历史"""
    print_section("Handle Utterance测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 模拟逐步构建对话历史
    print_subsection("逐步构建对话历史")
    
    # 第一轮对话：询问目的地
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
        {"role": "user", "content": "想去云南玩。"}
    ]
    session.save()
    
    result1 = fsm.handle_utterance("想去云南玩。")
    print(f"第一轮结果 - 状态: {result1['current_state']}, 槽位: {result1['slots']}")
    
    # 第二轮对话：询问预算
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "云南风景超美！请问大概想花多少钱？您可以给个区间~"},
        {"role": "user", "content": "5000–8000 元/人。"}
    ]
    session.save()
    
    result2 = fsm.handle_utterance("5000–8000 元/人。")
    print(f"第二轮结果 - 状态: {result2['current_state']}, 槽位: {result2['slots']}")
    
    # 第三轮对话：询问日期
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "云南风景超美！请问大概想花多少钱？您可以给个区间~"},
        {"role": "user", "content": "5000–8000 元/人。"},
        {"role": "assistant", "content": "好的。那您计划哪天出发？大概几天行程？"},
        {"role": "user", "content": "8月10日走，8月15日回，一共6天。"}
    ]
    session.save()
    
    result3 = fsm.handle_utterance("8月10日走，8月15日回，一共6天。")
    print(f"第三轮结果 - 状态: {result3['current_state']}, 槽位: {result3['slots']}")
    
    # 第四轮对话：询问同行人员
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "云南风景超美！请问大概想花多少钱？您可以给个区间~"},
        {"role": "user", "content": "5000–8000 元/人。"},
        {"role": "assistant", "content": "好的。那您计划哪天出发？大概几天行程？"},
        {"role": "user", "content": "8月10日走，8月15日回，一共6天。"},
        {"role": "assistant", "content": "明白！会有朋友或家人一同出行吗？"},
        {"role": "user", "content": "我和两个闺蜜。"}
    ]
    session.save()
    
    result4 = fsm.handle_utterance("我和两个闺蜜。")
    print(f"第四轮结果 - 状态: {result4['current_state']}, 槽位: {result4['slots']}")
    
    # 第五轮对话：询问偏好
    session.history = [
        {"role": "assistant", "content": "您好！我是您的智能旅行助理～今天想一起规划一次怎样的旅行呢？"},
        {"role": "user", "content": "想去云南玩。"},
        {"role": "assistant", "content": "云南风景超美！请问大概想花多少钱？您可以给个区间~"},
        {"role": "user", "content": "5000–8000 元/人。"},
        {"role": "assistant", "content": "好的。那您计划哪天出发？大概几天行程？"},
        {"role": "user", "content": "8月10日走，8月15日回，一共6天。"},
        {"role": "assistant", "content": "明白！会有朋友或家人一同出行吗？"},
        {"role": "user", "content": "我和两个闺蜜。"},
        {"role": "assistant", "content": "棒！大家更想体验自然风光还是文艺小镇？"},
        {"role": "user", "content": "自然风光。"}
    ]
    session.save()
    
    result5 = fsm.handle_utterance("自然风光。")
    print(f"第五轮结果 - 状态: {result5['current_state']}, 槽位: {result5['slots']}")
    
    # 最终确认
    result6 = fsm.handle_utterance("确认")
    print(f"确认结果 - 状态: {result6['current_state']}, 槽位: {result6['slots']}")
    
    # 验证结果结构
    assert 'current_state' in result6
    assert 'slots' in result6
    assert 'state_info' in result6
    assert 'can_transition_to' in result6
    
    # 验证状态机正常工作
    assert isinstance(result6['current_state'], str)
    assert isinstance(result6['slots'], dict)
    assert isinstance(result6['state_info'], dict)
    assert isinstance(result6['can_transition_to'], list)
    
    print("✓ handle_utterance方法测试通过")
    print(f"  最终状态: {result6['current_state']}")
    print(f"  最终槽位: {result6['slots']}")
    print(f"  已填充槽位: {sum(1 for v in result6['slots'].values() if v is not None)}/{len(result6['slots'])}")

def test_complete_conversation_flow():
    """测试完整对话流程"""
    print_section("完整对话流程测试")
    
    user, _ = User.objects.get_or_create(username="test_user")
    session = TalkSession.objects.create(user=user)
    fsm = TravelAssistantFSM(session)
    
    # 模拟完整的对话流程
    print_subsection("模拟对话流程")
    
    # 开始对话
    fsm.start()
    assert fsm.state == 'SLOT_FILLING_DESTINATION'
    
    # 填充所有槽位
    fsm.user_provides_destination("云南")
    fsm.user_provides_budget("5000-8000")
    fsm.user_provides_dates({"start_date": "2024-08-10", "end_date": "2024-08-15"})
    fsm.user_provides_profile("和两个闺蜜，喜欢自然风光")
    
    # 确认
    fsm.confirm()
    
    # 验证最终状态
    assert fsm.state == 'COMPLETED'
    assert fsm._are_all_slots_filled()
    
    print("✓ 完整对话流程测试通过")
    print(f"  最终状态: {fsm.state}")
    print(f"  最终槽位: {fsm.slots}")

def main():
    """运行所有状态机测试"""
    try:
        print("开始状态机测试...")
        
        test_state_machine_initialization()
        test_state_transitions()
        test_slot_validation()
        test_global_transitions()
        test_slot_management()
        test_session_integration()
        test_state_info()
        test_summary_generation()
        test_handle_utterance_with_history()
        test_complete_conversation_flow()
        
        print("\n🎉 所有状态机测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 