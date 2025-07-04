#!/usr/bin/env python3
"""
RouteTimeService 增强功能演示
不依赖高德API，仅展示解析功能
"""

import re
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class ActivityInfo:
    """活动信息"""
    name: str
    duration_minutes: int
    location: str

@dataclass
class DayPlan:
    """单日行程计划"""
    day_number: int
    activities: List[ActivityInfo]
    transport_segments: List[Dict[str, Any]]

class RouteTimeServiceDemo:
    """演示版本的 RouteTimeService，仅包含解析功能"""
    
    def parse_multi_day_plan(self, plan_text: str) -> List[DayPlan]:
        """
        解析多天行程文本，支持新格式：
        Day1: 地点A(活动, 时长90分钟) --交通方式-- 地点B(活动, 时长60分钟)
        Day2: 地点C(活动, 时长120分钟)
        """
        day_plans = []
        lines = plan_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('Day'):
                continue
                
            day_plan = self._parse_single_day(line)
            if day_plan:
                day_plans.append(day_plan)
        
        return day_plans

    def _parse_single_day(self, day_line: str) -> Optional[DayPlan]:
        """解析单日行程"""
        # 匹配 DayX: 格式
        day_match = re.match(r'Day(\d+):\s*(.+)', day_line)
        if not day_match:
            return None
            
        day_number = int(day_match.group(1))
        content = day_match.group(2).strip()
        
        # 解析活动和交通
        activities = []
        transport_segments = []
        
        # 分割活动段
        segments = re.split(r'\s*--([^--]+)--\s*', content)
        
        for i, segment in enumerate(segments):
            if i % 2 == 0:  # 活动段
                activity = self._parse_activity(segment.strip())
                if activity:
                    activities.append(activity)
            else:  # 交通方式段
                transport_mode = segment.strip()
                transport_segments.append({"mode": transport_mode})
        
        return DayPlan(
            day_number=day_number,
            activities=activities,
            transport_segments=transport_segments
        )

    def _parse_activity(self, activity_text: str) -> Optional[ActivityInfo]:
        """解析单个活动信息"""
        # 匹配格式：地点A(活动, 时长90分钟)
        pattern = r'(.+?)\((.+?),\s*时长(\d+)分钟\)'
        match = re.match(pattern, activity_text)
        
        if match:
            location = match.group(1).strip()
            activity_name = match.group(2).strip()
            duration = int(match.group(3))
            
            return ActivityInfo(
                name=activity_name,
                duration_minutes=duration,
                location=location
            )
        
        # 如果没有匹配到标准格式，尝试简单格式：地点A(活动)
        simple_pattern = r'(.+?)\((.+?)\)'
        match = re.match(simple_pattern, activity_text)
        
        if match:
            location = match.group(1).strip()
            activity_name = match.group(2).strip()
            
            return ActivityInfo(
                name=activity_name,
                duration_minutes=60,  # 默认60分钟
                location=location
            )
        
        return None

def demo_parsing():
    """演示解析功能"""
    print("=== RouteTimeService 增强功能演示 ===")
    print()
    
    service = RouteTimeServiceDemo()
    
    # 测试用例1：标准格式
    print("📋 测试用例1：标准多天行程")
    plan_text1 = """
    Day1: 武侯祠(三国文化, 时长90分钟) --步行-- 锦里古街(小吃打卡, 时长60分钟)
    Day2: 宽窄巷子(老巷闲逛, 时长120分钟)
    """
    print(f"输入文本:\n{plan_text1.strip()}")
    
    day_plans = service.parse_multi_day_plan(plan_text1)
    print("解析结果:")
    for day_plan in day_plans:
        print(f"  第{day_plan.day_number}天:")
        for j, activity in enumerate(day_plan.activities):
            print(f"    📍 活动{j+1}: {activity.location}")
            print(f"       🎯 内容: {activity.name}")
            print(f"       ⏱️  时长: {activity.duration_minutes}分钟")
        for j, transport in enumerate(day_plan.transport_segments):
            print(f"    🚗 交通{j+1}: {transport['mode']}")
    print()
    
    # 测试用例2：单日活动
    print("📋 测试用例2：单日活动")
    plan_text2 = """
    Day1: 云南植物园(观赏热带植物, 时长360分钟)
    """
    print(f"输入文本:\n{plan_text2.strip()}")
    
    day_plans = service.parse_multi_day_plan(plan_text2)
    print("解析结果:")
    for day_plan in day_plans:
        print(f"  第{day_plan.day_number}天:")
        for j, activity in enumerate(day_plan.activities):
            print(f"    📍 活动{j+1}: {activity.location}")
            print(f"       🎯 内容: {activity.name}")
            print(f"       ⏱️  时长: {activity.duration_minutes}分钟")
    print()
    
    # 测试用例3：复杂多天行程
    print("📋 测试用例3：复杂多天行程")
    plan_text3 = """
    Day1: 天安门广场(升旗仪式, 时长60分钟) --地铁-- 故宫博物院(参观宫殿, 时长180分钟) --步行-- 景山公园(俯瞰故宫, 时长60分钟)
    Day2: 颐和园(游览园林, 时长240分钟) --公交-- 圆明园(遗址参观, 时长120分钟)
    Day3: 长城(登城游览, 时长300分钟)
    """
    print(f"输入文本:\n{plan_text3.strip()}")
    
    day_plans = service.parse_multi_day_plan(plan_text3)
    print("解析结果:")
    for day_plan in day_plans:
        print(f"  第{day_plan.day_number}天:")
        for j, activity in enumerate(day_plan.activities):
            print(f"    📍 活动{j+1}: {activity.location}")
            print(f"       🎯 内容: {activity.name}")
            print(f"       ⏱️  时长: {activity.duration_minutes}分钟")
        for j, transport in enumerate(day_plan.transport_segments):
            print(f"    🚗 交通{j+1}: {transport['mode']}")
    print()

def demo_activity_parsing():
    """演示活动解析功能"""
    print("=== 活动解析功能演示 ===")
    print()
    
    service = RouteTimeServiceDemo()
    
    test_cases = [
        "武侯祠(三国文化, 时长90分钟)",
        "锦里古街(小吃打卡, 时长60分钟)",
        "云南植物园(观赏热带植物, 时长360分钟)",
        "天安门广场(升旗仪式, 时长60分钟)",
        "故宫博物院(参观宫殿, 时长180分钟)",
        "景山公园(俯瞰故宫, 时长60分钟)",
        "颐和园(游览园林, 时长240分钟)",
        "圆明园(遗址参观, 时长120分钟)",
        "长城(登城游览, 时长300分钟)",
        "宽窄巷子(老巷闲逛, 时长120分钟)",
    ]
    
    print("测试各种活动格式解析:")
    for test_case in test_cases:
        activity = service._parse_activity(test_case)
        if activity:
            print(f"  ✅ {test_case}")
            print(f"     地点: {activity.location}")
            print(f"     活动: {activity.name}")
            print(f"     时长: {activity.duration_minutes}分钟")
        else:
            print(f"  ❌ {test_case} -> 解析失败")
    print()

def demo_format_compatibility():
    """演示格式兼容性"""
    print("=== 格式兼容性演示 ===")
    print()
    
    service = RouteTimeServiceDemo()
    
    # 测试不同格式的活动
    formats = [
        "标准格式: 武侯祠(三国文化, 时长90分钟)",
        "简单格式: 锦里古街(小吃打卡)",
        "长时长: 云南植物园(观赏热带植物, 时长360分钟)",
        "短时长: 天安门广场(升旗仪式, 时长30分钟)",
    ]
    
    print("支持的活动格式:")
    for format_desc in formats:
        activity_text = format_desc.split(": ")[1]
        activity = service._parse_activity(activity_text)
        if activity:
            print(f"  ✅ {format_desc}")
            print(f"     解析结果: {activity.location} | {activity.name} | {activity.duration_minutes}分钟")
        else:
            print(f"  ❌ {format_desc} -> 不支持")
    print()

def demo_transport_modes():
    """演示交通方式支持"""
    print("=== 交通方式支持演示 ===")
    print()
    
    transport_modes = [
        "步行", "地铁", "公交", "打车", "自驾", "骑行", "高铁", "飞机", "火车"
    ]
    
    print("支持的交通方式:")
    for mode in transport_modes:
        print(f"  🚗 {mode}")
    print()

if __name__ == "__main__":
    demo_parsing()
    demo_activity_parsing()
    demo_format_compatibility()
    demo_transport_modes()
    
    print("🎉 演示完成！")
    print()
    print("主要增强功能:")
    print("1. ✅ 支持多天行程解析")
    print("2. ✅ 支持活动时长解析")
    print("3. ✅ 支持复杂交通方式")
    print("4. ✅ 向后兼容原有格式")
    print("5. ✅ 生成详细时间安排")
    print("6. ✅ 支持地理编码和路径规划") 