#!/usr/bin/env python
import os
import sys
import django
import logging

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.services.state_machine import TravelAssistantFSM

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

def test_direct_stream():
    """直接测试状态机的流式处理"""
    print("=== 直接测试状态机流式处理 ===")
    
    # 创建新会话
    fsm = TravelAssistantFSM()
    session_id = fsm.create_new_session("直接测试用户")
    print(f"创建会话: {session_id}")
    print(f"初始状态: {fsm.state}")
    
    # 检查方法是否存在
    print(f"handle_utterance_stream 方法存在: {hasattr(fsm, 'handle_utterance_stream')}")
    
    # 第一条消息
    print("\n处理第一条消息...")
    try:
        print("开始调用 handle_utterance_stream...")
        chunks = list(fsm.handle_utterance_stream("我想去成都青羊区"))
        print(f"成功调用，收到 {len(chunks)} 个数据块")
        
        full_content = ""
        for i, chunk in enumerate(chunks):
            print(f"  数据块 {i}: {chunk}")
            if chunk.get('type') == 'content':
                full_content += chunk.get('chunk', '')
            elif chunk.get('type') in ['done', 'end', 'completed']:
                full_content = chunk.get('full_content', full_content)
                break
        
        print(f"第一次回复: {full_content[:100]}...")
        
    except Exception as e:
        print(f"调用 handle_utterance_stream 时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 检查历史记录
    history = fsm.get_conversation_history()
    print(f"历史记录长度: {len(history)}")
    for i, msg in enumerate(history):
        print(f"[{i}] {msg['role']}: {msg['content'][:100]}...")
    
    # 统计消息
    assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
    user_messages = [msg for msg in history if msg['role'] == 'user']
    print(f"用户消息数量: {len(user_messages)}")
    print(f"助手消息数量: {len(assistant_messages)}")
    
    if len(assistant_messages) == 0:
        print("❌ 第一条消息：助手消息没有保存！")
    else:
        print("✅ 第一条消息：助手消息正确保存")

if __name__ == "__main__":
    try:
        test_direct_stream()
    except Exception as e:
        print(f"测试错误: {e}")
        import traceback
        traceback.print_exc() 