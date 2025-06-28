#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hunter.services.browser_manager import BrowserManager
from hunter.config.settings import HunterConfig

async def test_likes_extraction():
    """测试点赞数提取功能"""
    print("开始测试点赞数提取功能...")
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager()
    
    try:
        # 初始化浏览器
        print("正在初始化浏览器...")
        if not await browser_manager.initialize():
            print("浏览器初始化失败")
            return
        
        # 测试URL（请替换为实际的小红书笔记URL）
        test_url = "https://www.xiaohongshu.com/explore/65f8b8b8000000001e01c123"
        
        print(f"正在获取笔记内容: {test_url}")
        
        # 获取笔记内容（包含点赞数）
        content = await browser_manager.get_note_content(test_url)
        
        print("\n=== 获取到的笔记内容 ===")
        print(content)
        
        # 检查是否包含点赞数
        if "点赞数:" in content:
            print("\n✅ 成功获取到点赞数信息")
        else:
            print("\n❌ 未获取到点赞数信息")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
    finally:
        # 关闭浏览器
        await browser_manager.shutdown()
        print("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(test_likes_extraction()) 