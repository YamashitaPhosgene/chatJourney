#!/usr/bin/env python
# encoding: utf-8

"""
Hunter API 测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from hunter.api.hunter_api import HunterAPI

async def test_hunter_api():
    """测试Hunter API"""
    print("开始测试 Hunter API...")
    
    # 创建API实例
    api = HunterAPI()
    
    try:
        # 1. 初始化服务
        print("\n1. 初始化服务...")
        init_result = await api.initialize()
        print(f"初始化结果: {init_result.get('success', False)}")
        if init_result.get('success'):
            print("初始化成功！")
        else:
            print(f"初始化失败: {init_result.get('message', '未知错误')}")
            return
        
        # 2. 检查状态
        print("\n2. 检查服务状态...")
        status = api.get_status()
        print(f"状态: {status}")
        
        # 3. 搜索笔记
        print("\n3. 搜索笔记...")
        result = await api.search_notes("旅行", 3)
        print(f"搜索结果: {result.get('success', False)}")
        if result.get('success'):
            print("搜索成功！")
            data = result.get('data', '')
            print(f"结果预览: {data[:200]}..." if len(data) > 200 else data)
        else:
            print(f"搜索失败: {result.get('error', '未知错误')}")
        
        print("\n测试完成！")
        
    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_hunter_api()) 