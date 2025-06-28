#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from talker.services.xiaohongshu_summary_service import XiaohongshuSummaryService

def test_likes_parsing():
    """测试点赞数解析功能"""
    print("开始测试点赞数解析功能...")
    
    # 创建服务实例
    service = XiaohongshuSummaryService()
    
    # 测试数据
    test_content = """标题: 三里屯美食探店
作者: 美食达人小王
发布时间: 2024-01-15
点赞数: 1234
链接: https://www.xiaohongshu.com/explore/test123

内容:
今天在三里屯发现了一家超级好吃的咖啡店！
环境很好，咖啡也很香醇。
#三里屯 #咖啡 #美食探店"""
    
    print("测试数据:")
    print(test_content)
    print("\n" + "="*50 + "\n")
    
    # 测试解析
    parsed_data = service._parse_note_content_string(test_content)
    
    print("解析结果:")
    for key, value in parsed_data.items():
        print(f"{key}: {value}")
    
    # 验证点赞数
    if parsed_data.get("likes") == 1234:
        print("\n✅ 点赞数解析成功")
    else:
        print(f"\n❌ 点赞数解析失败，期望: 1234，实际: {parsed_data.get('likes')}")

if __name__ == "__main__":
    test_likes_parsing() 