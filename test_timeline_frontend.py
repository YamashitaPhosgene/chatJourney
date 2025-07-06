#!/usr/bin/env python

import os
import sys
import django
import requests
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.models import TalkSession, POIItem
from talker.services.timeline_service import TimelineService
from datetime import datetime, timedelta

def test_timeline_api():
    """测试Timeline API是否正常工作"""
    
    # 创建测试会话
    session = TalkSession.objects.create(
        budget=3000,
        start_date=datetime.now().date(),
        end_date=datetime.now().date() + timedelta(days=3),
        locations=['成都', '三里屯'],
        user_profile={'travel_type': 'leisure', 'budget_level': 'medium'},
        state='COMPLETED'
    )
    
    print(f"创建测试会话: {session.id}")
    
    # 创建几个测试POI
    pois_data = [
        {
            'name': '成都大熊猫繁育研究基地',
            'location': '104.146,30.732',
            'address': '成都市成华区外北熊猫大道1375号',
            'type': '景点'
        },
        {
            'name': '宽窄巷子',
            'location': '104.061,30.664',
            'address': '成都市青羊区宽窄巷子',
            'type': '景点'
        },
        {
            'name': '三里屯太古里',
            'location': '116.455,39.936',
            'address': '北京市朝阳区三里屯路',
            'type': '购物'
        }
    ]
    
    for poi_data in pois_data:
        POIItem.objects.create(
            session=session,
            name=poi_data['name'],
            location=poi_data['location'],
            address=poi_data['address'],
            type=poi_data['type'],
            raw_data=poi_data
        )
    
    print(f"创建了 {len(pois_data)} 个测试POI")
    
    # 测试Timeline服务
    print("\n=== 测试Timeline服务 ===")
    timeline_service = TimelineService()
    result = timeline_service.generate_timeline(session)
    
    print(f"Timeline生成结果: {result.get('success', False)}")
    if result.get('success'):
        print(f"用户画像: {result.get('user_profile_text', '')[:100]}...")
        print(f"地理聚类: {len(result.get('clusters', []))} 个")
        print(f"行程链: {len(result.get('itinerary_chain', []))} 天")
        
        # 检查行程链数据结构
        chain = result.get('itinerary_chain', [])
        if chain:
            print(f"第一天行程: {chain[0]}")
    else:
        print(f"Timeline生成失败: {result.get('error', '未知错误')}")
    
    # 测试Timeline API端点
    print("\n=== 测试Timeline API端点 ===")
    try:
        # 启动Django测试服务器
        from django.test import Client
        client = Client()
        
        response = client.get(f'/api/talker/timeline/{session.id}/')
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API响应成功: {data.get('success', False)}")
            if data.get('success'):
                timeline_data = data.get('timeline_data', {})
                print(f"Timeline数据包含字段: {list(timeline_data.keys())}")
                
                # 检查前端需要的字段
                chain = timeline_data.get('itinerary_chain', [])
                print(f"行程链数据: {len(chain)} 天")
                if chain:
                    print(f"第一天数据结构: {list(chain[0].keys())}")
            else:
                print(f"API返回错误: {data.get('error', '未知错误')}")
        else:
            print(f"API请求失败: {response.status_code}")
            print(f"响应内容: {response.content.decode()}")
    except Exception as e:
        print(f"API测试失败: {e}")
    
    # 清理测试数据
    session.delete()
    print("\n测试完成，已清理测试数据")

if __name__ == '__main__':
    test_timeline_api() 