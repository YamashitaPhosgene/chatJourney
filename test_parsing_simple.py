#!/usr/bin/env python3
"""
简单测试笔记内容解析功能
"""

import re
import json

def parse_note_content_for_info(content: str):
    """从笔记内容中解析结构化信息"""
    try:
        parsed_info = {}
        
        # 解析标题
        title_match = re.search(r'标题: (.+)', content)
        if title_match:
            parsed_info["title"] = title_match.group(1).strip()
        
        # 解析作者
        author_match = re.search(r'作者: (.+)', content)
        if author_match:
            parsed_info["author"] = author_match.group(1).strip()
        
        # 解析发布时间
        publish_time_match = re.search(r'发布时间: (.+)', content)
        if publish_time_match:
            parsed_info["publish_time"] = publish_time_match.group(1).strip()
        
        # 解析IP地址
        ip_match = re.search(r'IP地址: (.+)', content)
        if ip_match:
            parsed_info["ip"] = ip_match.group(1).strip()
        
        # 解析标签
        tag_match = re.findall(r'#([^#\s]+)', content)
        if tag_match:
            parsed_info["tags"] = [tag.strip() for tag in tag_match]
        
        return parsed_info
        
    except Exception as e:
        print(f"解析笔记内容结构化信息失败: {e}")
        return {}

def test_content_parsing():
    """测试内容解析功能"""
    print("=== 测试笔记内容解析功能 ===")
    
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
    parsed_info = parse_note_content_for_info(test_content)
    
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