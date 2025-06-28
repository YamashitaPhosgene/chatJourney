#!/usr/bin/env python3
"""
测试笔记内容解析功能
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from talker.services.xiaohongshu_summary_service import XiaohongshuSummaryService

def test_content_parsing():
    """测试内容解析功能"""
    print("=== 测试笔记内容解析功能 ===")
    
    # 创建服务实例
    service = XiaohongshuSummaryService()
    
    # 测试内容
    test_content = """标题: 北京！三里屯街头呆着舒服的咖啡新店！！
作者: 嗆_嗆
发布时间: 昨天 20:54 北京
IP地址: 北京
链接: https://www.xiaohongshu.com/search_result/685e94980000000012020eca?xsec_token=ABMWaknBzpi90GPnjdAmy3e-Gxk2bjgIwjGB6DoMtnPOc=&xsec_source=

内容:
大鹅带着松弛感来屯子了！！特调好喝！
巨清新的🈚️咖啡果茶也好喝！
旁边是精酿和简餐！还有鸡尾酒🍸
晚上坐户外可太惬意了！！

#北京周末去哪儿 #北京探店 #北京美食 #北京新店 #COTD咖啡探店 #我的咖啡日记 #可以呆一下午的小店 #北京咖啡店 #三里屯"""
    
    print("测试内容:")
    print("-" * 50)
    print(test_content)
    print("-" * 50)
    
    # 解析内容
    parsed_info = service._parse_note_content_for_info(test_content)
    
    print("\n解析结果:")
    print("-" * 50)
    print(json.dumps(parsed_info, ensure_ascii=False, indent=2))
    print("-" * 50)
    
    # 验证解析结果
    expected_fields = ['title', 'author', 'publish_time', 'ip', 'tags']
    for field in expected_fields:
        if field in parsed_info:
            print(f"✅ {field}: {parsed_info[field]}")
        else:
            print(f"❌ {field}: 未找到")

if __name__ == "__main__":
    test_content_parsing() 