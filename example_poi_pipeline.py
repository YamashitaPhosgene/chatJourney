#!/usr/bin/env python
# encoding: utf-8

"""
POI搜索管道使用示例
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from hunter.services.poi_search_pipeline import POISearchPipeline

def example_basic_usage():
    """基本使用示例"""
    print("=" * 50)
    print("基本使用示例")
    print("=" * 50)
    
    # 创建管道实例
    pipeline = POISearchPipeline()
    
    # 模拟用户对话
    conversation = [
        {"role": "user", "content": "我想去北京玩，主要是想体验烤鸭和故宫"},
        {"role": "assistant", "content": "好的，北京烤鸭和故宫都是必去的。还有别的想法吗？"},
        {"role": "user", "content": "想去天安门广场看看，然后去王府井购物"},
    ]
    
    # 执行搜索
    result = pipeline.run(conversation)
    
    # 显示结果
    print(f"📍 行政区划代码: {result['adcode']}")
    print(f"🏷️  POI分类码: {result['types']}")
    
    # 显示POI结果
    pois = result['pois']
    for keyword, poi_list in pois.items():
        print(f"\n🏪 {keyword}:")
        for i, poi in enumerate(poi_list[:3], 1):
            print(f"  {i}. {poi.get('name', '未知')}")
            print(f"     地址: {poi.get('address', '未知地址')}")

def example_with_session_info():
    """使用会话信息的示例"""
    print("\n" + "=" * 50)
    print("使用会话信息示例")
    print("=" * 50)
    
    pipeline = POISearchPipeline()
    
    conversation = [
        {"role": "user", "content": "我想去杭州玩，主要是想体验西湖和龙井茶"},
    ]
    
    # 提供会话信息
    session_info = {
        "locations": "杭州",
        "budget": "3000元",
        "start_date": "2024-01-15",
        "end_date": "2024-01-17",
        "user_profile": {"同行人员": "朋友", "旅行风格": "文化体验"}
    }
    
    result = pipeline.run(conversation, session_info)
    
    print(f"📍 行政区划代码: {result['adcode']}")
    print(f"🏷️  POI分类码: {result['types']}")
    
    # 显示摘要
    summary = pipeline.get_search_summary(result)
    print(f"📊 总POI数量: {summary['total_pois']}")
    print(f"📈 成功率: {summary['success_rate']:.1%}")

def example_direct_keywords():
    """直接使用关键词的示例"""
    print("\n" + "=" * 50)
    print("直接使用关键词示例")
    print("=" * 50)
    
    pipeline = POISearchPipeline()
    
    # 直接提供关键词
    keywords = {
        "primary_keywords": ["火锅", "咖啡"],
        "city_keywords": ["成都"],
        "interest_keywords": ["美食", "饮品"],
        "search_suggestions": ["成都火锅", "成都咖啡店"]
    }
    
    result = pipeline.search_by_keywords(keywords)
    
    print(f"📍 行政区划代码: {result['adcode']}")
    print(f"🏷️  POI分类码: {result['types']}")
    
    pois = result['pois']
    for keyword, poi_list in pois.items():
        print(f"\n🏪 {keyword}: {len(poi_list)} 个结果")
        for i, poi in enumerate(poi_list[:2], 1):
            print(f"  {i}. {poi.get('name', '未知')}")

def example_error_handling():
    """错误处理示例"""
    print("\n" + "=" * 50)
    print("错误处理示例")
    print("=" * 50)
    
    pipeline = POISearchPipeline()
    
    # 测试无效输入
    invalid_conversation = []
    result = pipeline.run(invalid_conversation)
    
    print("空对话处理:")
    print(f"  query: {result['query']}")
    print(f"  adcode: {result['adcode']}")
    print(f"  types: {result['types']}")
    print(f"  pois: {result['pois']}")
    
    # 测试无效关键词
    invalid_keywords = {
        "primary_keywords": [],
        "city_keywords": ["不存在的城市"],
        "interest_keywords": ["不存在的兴趣"],
    }
    
    result = pipeline.search_by_keywords(invalid_keywords)
    print(f"\n无效关键词处理:")
    print(f"  adcode: {result['adcode']}")
    print(f"  types: {result['types']}")

def main():
    """主函数"""
    print("POI搜索管道使用示例")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_with_session_info()
        example_direct_keywords()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"示例执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 