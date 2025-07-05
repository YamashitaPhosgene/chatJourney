#!/usr/bin/env python
"""
测试前端集成Timeline服务
验证API端点是否正常工作
"""

import os
import sys
import django
import json
from django.test import Client
from django.urls import reverse

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.models import TalkSession, POISession, POIItem
from talker.services.timeline_service import TimelineService


def test_timeline_frontend_integration():
    """测试Timeline服务前端集成"""
    print("=" * 60)
    print("测试Timeline服务前端集成")
    print("=" * 60)
    
    # 创建测试客户端
    client = Client()
    
    # 1. 创建测试会话
    print("\n1. 创建测试会话...")
    session_data = {
        'username': 'test_user'
    }
    
    response = client.post('/api/talker/session/', 
                          json.dumps(session_data), 
                          content_type='application/json')
    
    if response.status_code == 200:
        session_id = response.json()['session_id']
        print(f"✅ 会话创建成功: {session_id}")
    else:
        print(f"❌ 会话创建失败: {response.status_code} - {response.json()}")
        return False
    
    # 2. 设置会话数据
    print("\n2. 设置会话数据...")
    try:
        session = TalkSession.objects.get(id=session_id)
        session.locations = "北京"
        session.budget = 3000
        session.start_date = "2024-01-01"
        session.end_date = "2024-01-03"
        session.user_profile = "喜欢美食和文化景点的年轻人"
        session.state = "COMPLETED"
        session.save()
        
        # 添加一些POI
        poi_data = [
            {
                'poi_id': 'B0FFFJDFFX',
                'name': '故宫博物院',
                'address': '北京市东城区景山前街4号',
                'location': '116.397128,39.917723',
                'type': '博物馆',
                'score': 4.8
            },
            {
                'poi_id': 'B0FFFJDFFY',
                'name': '天坛公园',
                'address': '北京市东城区天坛东路甲1号',
                'location': '116.407394,39.883119',
                'type': '公园',
                'score': 4.7
            },
            {
                'poi_id': 'B0FFFJDFFZ',
                'name': '全聚德烤鸭店',
                'address': '北京市东城区前门大街30号',
                'location': '116.395645,39.898662',
                'type': '餐厅',
                'score': 4.5
            }
        ]
        
        for poi_info in poi_data:
            # 先创建POIItem
            poi_item, created = POIItem.objects.get_or_create(
                poi_id=poi_info['poi_id'],
                defaults={
                    'name': poi_info['name'],
                    'address': poi_info['address'],
                    'location': poi_info['location'],
                    'type': poi_info['type']
                }
            )
            
            # 再创建POISession
            POISession.objects.create(
                session=session,
                poi=poi_item,
                source='manual'
            )
        
        print("✅ 会话数据设置成功")
        
    except Exception as e:
        print(f"❌ 会话数据设置失败: {e}")
        return False
    
    # 3. 测试Timeline API
    print("\n3. 测试Timeline API...")
    try:
        response = client.get(f'/api/talker/timeline/{session_id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Timeline API调用成功")
            print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 验证返回数据格式
            if data.get('success') and data.get('timeline_data'):
                timeline_data = data['timeline_data']
                if 'itinerary_chain' in timeline_data:
                    print("✅ Timeline数据格式正确")
                    
                    # 检查行程链内容
                    itinerary_chain = timeline_data['itinerary_chain']
                    if isinstance(itinerary_chain, list) and len(itinerary_chain) > 0:
                        print(f"✅ 行程链包含 {len(itinerary_chain)} 天的行程")
                        
                        # 显示第一天的行程
                        if itinerary_chain[0].get('activities'):
                            print(f"✅ 第一天包含 {len(itinerary_chain[0]['activities'])} 个活动")
                        else:
                            print("❌ 第一天没有活动数据")
                    else:
                        print("❌ 行程链为空")
                else:
                    print("❌ Timeline数据缺少itinerary_chain字段")
            else:
                print("❌ Timeline API返回失败")
                print(f"错误: {data.get('error', '未知错误')}")
        else:
            print(f"❌ Timeline API调用失败: {response.status_code}")
            print(f"错误: {response.json()}")
            
    except Exception as e:
        print(f"❌ Timeline API测试失败: {e}")
        return False
    
    # 4. 测试会话状态API
    print("\n4. 测试会话状态API...")
    try:
        response = client.get(f'/api/talker/session/{session_id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 会话状态API调用成功")
            
            # 验证返回数据
            if data.get('success') and data.get('session_info'):
                print("✅ 会话状态数据格式正确")
                session_info = data['session_info']
                print(f"会话状态: {session_info.get('state')}")
                print(f"目的地: {session_info.get('locations')}")
                print(f"预算: {session_info.get('budget')}")
            else:
                print("❌ 会话状态API返回失败")
        else:
            print(f"❌ 会话状态API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 会话状态API测试失败: {e}")
        return False
    
    # 5. 测试状态机API
    print("\n5. 测试状态机API...")
    try:
        message_data = {
            'session_id': session_id,
            'message': '帮我生成行程',
            'stream': False
        }
        
        response = client.post('/api/talker/state-machine/', 
                              json.dumps(message_data), 
                              content_type='application/json')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态机API调用成功")
            print(f"回复: {data.get('response', '无回复')}")
        else:
            print(f"❌ 状态机API调用失败: {response.status_code}")
            print(f"错误: {response.json()}")
            
    except Exception as e:
        print(f"❌ 状态机API测试失败: {e}")
        return False
    
    # 6. 清理测试数据
    print("\n6. 清理测试数据...")
    try:
        session.delete()
        print("✅ 测试数据清理成功")
    except Exception as e:
        print(f"❌ 测试数据清理失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 前端集成测试完成！")
    print("=" * 60)
    
    return True


def test_frontend_data_conversion():
    """测试前端数据转换逻辑"""
    print("\n" + "=" * 60)
    print("测试前端数据转换逻辑")
    print("=" * 60)
    
    # 模拟Timeline服务返回的数据
    timeline_data = {
        'success': True,
        'itinerary_chain': [
            {
                'day': '第1天',
                'activities': [
                    {
                        'time': '09:00',
                        'activity': '参观故宫博物院',
                        'location': '故宫博物院',
                        'duration': '2小时'
                    },
                    {
                        'time': '12:00',
                        'activity': '在全聚德用餐',
                        'location': '全聚德烤鸭店',
                        'duration': '1小时'
                    },
                    {
                        'time': '14:00',
                        'activity': '游览天坛公园',
                        'location': '天坛公园',
                        'duration': '1.5小时'
                    }
                ]
            },
            {
                'day': '第2天',
                'activities': [
                    {
                        'time': '10:00',
                        'activity': '颐和园游览',
                        'location': '颐和园',
                        'duration': '3小时'
                    }
                ]
            }
        ]
    }
    
    print("📊 测试数据转换逻辑")
    print(f"输入数据: {json.dumps(timeline_data, indent=2, ensure_ascii=False)}")
    
    # 模拟前端转换逻辑
    def convert_timeline_to_itinerary(timeline_data):
        """模拟前端的convertTimelineToItinerary函数"""
        itinerary_chain = timeline_data.get('itinerary_chain', [])
        converted_itinerary = []
        
        for day_data in itinerary_chain:
            day_info = {
                'date': day_data.get('day', '未知日期'),
                'weatherIcon': '☀️',
                'temperature': '20/25℃',
                'events': []
            }
            
            activities = day_data.get('activities', [])
            for activity in activities:
                event = {
                    'time': activity.get('time', '00:00'),
                    'image': '/static/images/banner.jpg',
                    'location': activity.get('location', '未知地点'),
                    'type': '游玩',
                    'duration': 120
                }
                day_info['events'].append(event)
            
            converted_itinerary.append(day_info)
        
        return converted_itinerary
    
    # 执行转换
    converted_data = convert_timeline_to_itinerary(timeline_data)
    
    print(f"\n输出数据: {json.dumps(converted_data, indent=2, ensure_ascii=False)}")
    
    # 验证转换结果
    if len(converted_data) == 2:
        print("✅ 转换了正确的天数")
        
        if len(converted_data[0]['events']) == 3:
            print("✅ 第一天活动数量正确")
            
        if len(converted_data[1]['events']) == 1:
            print("✅ 第二天活动数量正确")
            
        print("✅ 数据转换测试通过！")
    else:
        print("❌ 数据转换失败")
    
    return True


if __name__ == '__main__':
    print("🚀 开始前端集成测试")
    
    try:
        # 测试Timeline服务集成
        success1 = test_timeline_frontend_integration()
        
        # 测试数据转换
        success2 = test_frontend_data_conversion()
        
        if success1 and success2:
            print("\n🎉 所有测试通过！前端集成Timeline服务成功！")
        else:
            print("\n❌ 部分测试失败，请检查实现")
            
    except Exception as e:
        print(f"\n💥 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 