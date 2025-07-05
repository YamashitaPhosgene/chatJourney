#!/usr/bin/env python
import os
import sys
import django
import json
import requests
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.services.state_machine import TravelAssistantFSM

def test_sse_stream():
    """测试真正的SSE流式处理"""
    print("=== 测试SSE流式处理 ===")
    
    # 创建会话
    response = requests.post("http://localhost:8000/api/talker/session/", 
                           json={"username": "流式测试用户"})
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"创建会话: {session_id}")
    
    # 发送第一条消息（真正的流式）
    print("\n发送第一条消息（SSE流式）...")
    response = requests.post("http://localhost:8000/api/talker/state-machine/", 
                           json={
                               "session_id": session_id,
                               "message": "我想去成都青羊区",
                               "stream": True,
                               "wants_sse": True  # 明确要求SSE
                           }, stream=True)
    
    if response.status_code == 200:
        print("开始接收流式响应...")
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])  # 去除 'data: ' 前缀
                        if data.get('type') == 'content':
                            full_response += data.get('chunk', '')
                        elif data.get('type') in ['done', 'end', 'completed']:
                            full_response = data.get('full_content', full_response)
                            print(f"流式响应完成: {full_response[:100]}...")
                            break
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"错误: {response.status_code}")
        return
    
    # 等待一秒确保保存完成
    time.sleep(1)
    
    # 检查历史记录
    print("\n检查第一次对话历史...")
    fsm = TravelAssistantFSM()
    if fsm.load_session(session_id):
        history = fsm.get_conversation_history()
        print(f"历史记录长度: {len(history)}")
        for i, msg in enumerate(history):
            print(f"[{i}] {msg['role']}: {msg['content'][:100]}...")
        
        # 检查助手消息数量
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        print(f"助手消息数量: {len(assistant_messages)}")
        
        if len(assistant_messages) == 0:
            print("❌ 流式处理后没有保存助手消息！")
        else:
            print("✅ 流式处理正确保存了助手消息")
    else:
        print("❌ 无法加载会话")
        return
    
    # 发送第二条消息（真正的流式）
    print("\n发送第二条消息（SSE流式）...")
    response = requests.post("http://localhost:8000/api/talker/state-machine/", 
                           json={
                               "session_id": session_id,
                               "message": "很好，为我推荐周边的美食",
                               "stream": True,
                               "wants_sse": True
                           }, stream=True)
    
    if response.status_code == 200:
        print("开始接收第二次流式响应...")
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('type') == 'content':
                            full_response += data.get('chunk', '')
                        elif data.get('type') in ['done', 'end', 'completed']:
                            full_response = data.get('full_content', full_response)
                            print(f"第二次流式响应完成: {full_response[:100]}...")
                            break
                    except json.JSONDecodeError:
                        pass
    
    # 等待一秒确保保存完成
    time.sleep(1)
    
    # 检查最终历史记录
    print("\n检查最终对话历史...")
    if fsm.load_session(session_id):
        history = fsm.get_conversation_history()
        print(f"最终历史记录长度: {len(history)}")
        for i, msg in enumerate(history):
            print(f"[{i}] {msg['role']}: {msg['content'][:100]}...")
        
        # 检查助手消息数量
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        user_messages = [msg for msg in history if msg['role'] == 'user']
        print(f"用户消息数量: {len(user_messages)}")
        print(f"助手消息数量: {len(assistant_messages)}")
        
        if len(assistant_messages) != len(user_messages):
            print(f"❌ 消息数量不匹配！用户:{len(user_messages)}, 助手:{len(assistant_messages)}")
        else:
            print("✅ 消息数量匹配，流式处理正确保存了所有消息")
        
        # 检查重复消息
        seen_content = set()
        duplicates = []
        for i, msg in enumerate(assistant_messages):
            content = msg['content']
            if content in seen_content:
                duplicates.append(i)
            seen_content.add(content)
        
        if duplicates:
            print(f"⚠️  发现重复助手消息: {duplicates}")
        else:
            print("✅ 没有发现重复助手消息")
    
    return session_id

def test_direct_stream():
    """直接测试状态机的流式处理"""
    print("\n=== 直接测试状态机流式处理 ===")
    
    # 创建新会话
    fsm = TravelAssistantFSM()
    session_id = fsm.create_new_session("直接测试用户")
    print(f"创建会话: {session_id}")
    
    # 第一条消息
    print("\n处理第一条消息...")
    chunks = list(fsm.handle_utterance_stream("我想去成都青羊区"))
    print(f"收到 {len(chunks)} 个数据块")
    
    full_content = ""
    for chunk in chunks:
        if chunk.get('type') == 'content':
            full_content += chunk.get('chunk', '')
        elif chunk.get('type') in ['done', 'end', 'completed']:
            full_content = chunk.get('full_content', full_content)
            break
    
    print(f"第一次回复: {full_content[:100]}...")
    
    # 检查历史记录
    history = fsm.get_conversation_history()
    print(f"历史记录长度: {len(history)}")
    for i, msg in enumerate(history):
        print(f"[{i}] {msg['role']}: {msg['content'][:100]}...")
    
    # 第二条消息
    print("\n处理第二条消息...")
    chunks = list(fsm.handle_utterance_stream("很好，为我推荐周边的美食"))
    print(f"收到 {len(chunks)} 个数据块")
    
    full_content = ""
    for chunk in chunks:
        if chunk.get('type') == 'content':
            full_content += chunk.get('chunk', '')
        elif chunk.get('type') in ['done', 'end', 'completed']:
            full_content = chunk.get('full_content', full_content)
            break
    
    print(f"第二次回复: {full_content[:100]}...")
    
    # 检查最终历史记录
    history = fsm.get_conversation_history()
    print(f"最终历史记录长度: {len(history)}")
    for i, msg in enumerate(history):
        print(f"[{i}] {msg['role']}: {msg['content'][:100]}...")
    
    # 统计消息
    assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
    user_messages = [msg for msg in history if msg['role'] == 'user']
    print(f"用户消息数量: {len(user_messages)}")
    print(f"助手消息数量: {len(assistant_messages)}")
    
    if len(assistant_messages) != len(user_messages):
        print(f"❌ 直接调用：消息数量不匹配！")
    else:
        print("✅ 直接调用：消息数量匹配")

if __name__ == "__main__":
    try:
        # 测试真正的SSE流式处理
        test_sse_stream()
        
        # 测试直接调用状态机
        test_direct_stream()
        
    except Exception as e:
        print(f"测试错误: {e}")
        import traceback
        traceback.print_exc() 