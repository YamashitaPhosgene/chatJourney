"""
Chain到Planner数据转换服务

该服务负责将itinerary_chain格式的数据转换为Planner应用的数据结构，
完全符合PLANNER_MODELS_DOCUMENTATION.md中的模型规范。
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PlannerData:
    """Planner数据结构"""
    trip: Dict[str, Any]
    days: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    events: List[Dict[str, Any]]


class ChainToPlannerService:
    """Chain到Planner数据转换服务"""

    # 时间映射
    TIME_PERIOD_MAPPING = {
        "清晨": "07:00",
        "上午": "09:00",
        "中午": "12:00",
        "下午": "14:00",
        "傍晚": "17:00",
        "夜晚": "20:00",
    }

    # 事件类型枚举
    EVENT_TYPES = [
        'activity', 'departure', 'arrival', 'checkin', 'checkout', 'stay'
    ]

    # 地点分类枚举
    LOCATION_CATEGORIES = [
        'sight', 'hotel', 'restaurant', 'transport', 'custom'
    ]

    # 活动分类枚举
    ACTIVITY_CATEGORIES = [
        'sightseeing', 'dining', 'transport', 'rest', 'free', 'custom'
    ]

    def __init__(self, user_id: int = 1):
        """
        初始化服务

        Args:
            user_id: 用户ID，默认为1
        """
        self.user_id = user_id
        self.location_id_counter = 1
        self.event_id_counter = 1

    def clean_place_name(self, place_name: str) -> str:
        """
        清理地点名称

        Args:
            place_name: 原始地点名称

        Returns:
            清理后的地点名称
        """
        clean_name = place_name.replace("【", "").replace("】", "")
        if "和" in clean_name:
            clean_name = clean_name.split("和")[0].strip()
        return clean_name.strip()

    def get_location_category(self, place_name: str) -> str:
        """
        获取地点分类

        Args:
            place_name: 地点名称

        Returns:
            地点分类
        """
        if any(keyword in place_name for keyword in ["宫", "寺", "祠", "堂", "园"]):
            return "sight"
        elif "酒店" in place_name:
            return "hotel"
        elif "餐厅" in place_name or "饭店" in place_name:
            return "restaurant"
        else:
            return "custom"

    def get_event_type_and_category(self, activity_type: str) -> tuple[str, str]:
        """
        获取事件类型和分类

        Args:
            activity_type: 活动类型

        Returns:
            (事件类型, 活动分类)
        """
        if activity_type == "sightseeing":
            return "activity", "sightseeing"
        elif activity_type == "dining":
            return "activity", "dining"
        elif activity_type == "stay":
            return "stay", "rest"
        elif activity_type == "transport":
            return "activity", "transport"
        else:
            return "activity", "custom"

    def create_trip(self, itinerary_chain: List[Dict], title: str = None,
                    start_date: str = None) -> Dict[str, Any]:
        """
        创建Trip数据

        Args:
            itinerary_chain: 行程链数据
            title: 旅行标题
            start_date: 开始日期

        Returns:
            Trip数据字典
        """
        if not title:
            title = f"旅行{len(itinerary_chain)}日游"

        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        end_date = (datetime.strptime(start_date, "%Y-%m-%d") +
                    timedelta(days=len(itinerary_chain) - 1)).strftime("%Y-%m-%d")

        current_time = datetime.now().isoformat() + "Z"

        return {
            "user_id": self.user_id,
            "title": title,
            "description": f"基于itinerary_chain生成的{len(itinerary_chain)}日游",
            "start_date": start_date,
            "end_date": end_date,
            "created_at": current_time,
            "updated_at": current_time
        }

    def create_locations(self, itinerary_chain: List[Dict]) -> List[Dict[str, Any]]:
        """
        创建Location数据

        Args:
            itinerary_chain: 行程链数据

        Returns:
            Location数据列表
        """
        locations = []
        current_time = datetime.now().isoformat() + "Z"

        for day_data in itinerary_chain:
            for activity in day_data['activities']:
                place = activity['place']
                if place not in ["自行解决", "附近"]:
                    clean_place = self.clean_place_name(place)
                    # 检查是否已存在
                    existing_location = next(
                        (loc for loc in locations if loc['name']
                         == clean_place),
                        None
                    )
                    if not existing_location:
                        category = self.get_location_category(clean_place)
                        location = {
                            "id": self.location_id_counter,
                            "name": clean_place,
                            "address": "",
                            "latitude": None,
                            "longitude": None,
                            "category": category,
                            "phone": "",
                            "notes": "",
                            "created_at": current_time,
                            "updated_at": current_time
                        }
                        locations.append(location)
                        self.location_id_counter += 1

        return locations

    def create_days(self, itinerary_chain: List[Dict], trip_id: int,
                    start_date: str) -> List[Dict[str, Any]]:
        """
        创建Day数据

        Args:
            itinerary_chain: 行程链数据
            trip_id: 旅行ID
            start_date: 开始日期

        Returns:
            Day数据列表
        """
        days = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        for day_index, day_data in enumerate(itinerary_chain, 1):
            current_date = (
                start_dt + timedelta(days=day_index - 1)).strftime("%Y-%m-%d")
            day = {
                "id": day_index,
                "trip_id": trip_id,
                "date": current_date,
                "day_index": day_index,
                "notes": f"第{day_index}天行程"
            }
            days.append(day)

        return days

    def create_events(self, itinerary_chain: List[Dict], trip_id: int,
                      locations: List[Dict], start_date: str) -> List[Dict[str, Any]]:
        """
        创建Event数据

        Args:
            itinerary_chain: 行程链数据
            trip_id: 旅行ID
            locations: Location数据列表
            start_date: 开始日期

        Returns:
            Event数据列表
        """
        events = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        current_time = datetime.now().isoformat() + "Z"

        for day_index, day_data in enumerate(itinerary_chain):
            current_date = (start_dt + timedelta(days=day_index)
                            ).strftime("%Y-%m-%d")

            for activity in day_data['activities']:
                # 获取时间
                time_period = activity['time_period']
                start_time = self.TIME_PERIOD_MAPPING.get(time_period, "09:00")

                # 获取地点
                place = activity['place']
                location_id = None
                if place not in ["自行解决", "附近"]:
                    clean_place = self.clean_place_name(place)
                    location = next(
                        (loc for loc in locations if loc['name']
                         == clean_place),
                        None
                    )
                    if location:
                        location_id = location['id']

                # 确定事件类型和分类
                event_type, category = self.get_event_type_and_category(
                    activity['type'])

                # 创建Event
                event = {
                    "id": self.event_id_counter,
                    "trip_id": trip_id,
                    "type": event_type,
                    "date": current_date,
                    "start_time": start_time,
                    "duration": "02:00:00",
                    "cost": None,
                    "location_id": location_id,
                    "title": activity['description'],
                    "description": activity['description'],
                    "notes": "",
                    "created_at": current_time,
                    "updated_at": current_time
                }

                # 如果是Activity类型，添加category字段
                if event_type == "activity":
                    event["category"] = category

                events.append(event)
                self.event_id_counter += 1

        return events

    def convert(self, itinerary_chain: List[Dict], title: str = None,
                start_date: str = None) -> PlannerData:
        """
        转换itinerary_chain为Planner数据结构

        Args:
            itinerary_chain: 行程链数据
            title: 旅行标题
            start_date: 开始日期

        Returns:
            PlannerData对象
        """
        # 1. 创建Trip
        trip = self.create_trip(itinerary_chain, title, start_date)
        trip_id = 1  # 模拟ID

        # 2. 创建Locations
        locations = self.create_locations(itinerary_chain)

        # 3. 创建Days
        days = self.create_days(itinerary_chain, trip_id, trip['start_date'])

        # 4. 创建Events
        events = self.create_events(
            itinerary_chain, trip_id, locations, trip['start_date'])

        return PlannerData(
            trip=trip,
            days=days,
            locations=locations,
            events=events
        )

    def to_json(self, planner_data: PlannerData) -> str:
        """
        转换为JSON格式

        Args:
            planner_data: PlannerData对象

        Returns:
            JSON字符串
        """
        return json.dumps({
            "trip": planner_data.trip,
            "days": planner_data.days,
            "locations": planner_data.locations,
            "events": planner_data.events
        }, ensure_ascii=False, indent=2)

    def to_markdown(self, planner_data: PlannerData) -> str:
        """
        转换为Markdown格式

        Args:
            planner_data: PlannerData对象

        Returns:
            Markdown字符串
        """
        md_lines = []

        # 标题
        md_lines.append(f"# {planner_data.trip['title']}")
        md_lines.append("")
        md_lines.append(f"**描述**: {planner_data.trip['description']}")
        md_lines.append("")
        md_lines.append(
            f"**日期**: {planner_data.trip['start_date']} - {planner_data.trip['end_date']}")
        md_lines.append("")

        # 按天组织事件
        events_by_day = {}
        for event in planner_data.events:
            date = event['date']
            if date not in events_by_day:
                events_by_day[date] = []
            events_by_day[date].append(event)

        # 按日期排序
        sorted_dates = sorted(events_by_day.keys())

        for i, date in enumerate(sorted_dates, 1):
            day_events = events_by_day[date]
            day_events.sort(key=lambda x: x['start_time'])

            md_lines.append(f"## Day {i} (第{i}天)")
            md_lines.append("")

            for event in day_events:
                md_lines.append(
                    f"### {event['start_time']} - {event['title']}")
                md_lines.append("")
                md_lines.append(event['description'])
                md_lines.append("")

                # 添加地点信息
                if event['location_id']:
                    location = next(
                        (loc for loc in planner_data.locations if loc['id'] == event['location_id']),
                        None
                    )
                    if location:
                        md_lines.append(f"**地点**: {location['name']}")
                        md_lines.append("")

                # 添加类型信息
                if event['type'] == 'activity' and 'category' in event:
                    category_map = {
                        'sightseeing': '游览',
                        'dining': '餐饮',
                        'transport': '交通',
                        'rest': '休息',
                        'free': '自由活动',
                        'custom': '自定义'
                    }
                    category_name = category_map.get(
                        event['category'], event['category'])
                    md_lines.append(f"**类型**: {category_name}")
                    md_lines.append("")

                md_lines.append("---")
                md_lines.append("")

        return "\n".join(md_lines)

    def validate_data(self, planner_data: PlannerData) -> Dict[str, bool]:
        """
        验证数据完整性

        Args:
            planner_data: PlannerData对象

        Returns:
            验证结果字典
        """
        results = {}

        # Trip字段验证
        required_trip_fields = ['user_id', 'title', 'description',
                                'start_date', 'end_date', 'created_at', 'updated_at']
        results['trip_fields'] = all(
            field in planner_data.trip for field in required_trip_fields)

        # Day字段验证
        required_day_fields = ['trip_id', 'date', 'day_index', 'notes']
        results['day_fields'] = all(
            all(field in day for field in required_day_fields)
            for day in planner_data.days
        )

        # Location字段验证
        required_location_fields = ['name', 'address', 'latitude', 'longitude',
                                    'category', 'phone', 'notes', 'created_at', 'updated_at']
        results['location_fields'] = all(
            all(field in location for field in required_location_fields)
            for location in planner_data.locations
        )

        # Event字段验证
        required_event_fields = ['trip_id', 'type', 'date', 'start_time', 'duration',
                                 'cost', 'location_id', 'title', 'description', 'notes', 'created_at', 'updated_at']
        results['event_fields'] = all(
            all(field in event for field in required_event_fields)
            for event in planner_data.events
        )

        # 事件类型验证
        results['event_types'] = all(
            event['type'] in self.EVENT_TYPES
            for event in planner_data.events
        )

        # 地点分类验证
        results['location_categories'] = all(
            location['category'] in self.LOCATION_CATEGORIES
            for location in planner_data.locations
        )

        return results


# 便捷函数
def convert_chain_to_planner(itinerary_chain: List[Dict], user_id: int = 1,
                             title: str = None, start_date: str = None) -> PlannerData:
    """
    便捷转换函数

    Args:
        itinerary_chain: 行程链数据
        user_id: 用户ID
        title: 旅行标题
        start_date: 开始日期

    Returns:
        PlannerData对象
    """
    service = ChainToPlannerService(user_id)
    return service.convert(itinerary_chain, title, start_date)


def convert_chain_to_json(itinerary_chain: List[Dict], user_id: int = 1,
                          title: str = None, start_date: str = None) -> str:
    """
    转换为JSON的便捷函数

    Args:
        itinerary_chain: 行程链数据
        user_id: 用户ID
        title: 旅行标题
        start_date: 开始日期

    Returns:
        JSON字符串
    """
    service = ChainToPlannerService(user_id)
    planner_data = service.convert(itinerary_chain, title, start_date)
    return service.to_json(planner_data)


def convert_chain_to_markdown(itinerary_chain: List[Dict], user_id: int = 1,
                              title: str = None, start_date: str = None) -> str:
    """
    转换为Markdown的便捷函数

    Args:
        itinerary_chain: 行程链数据
        user_id: 用户ID
        title: 旅行标题
        start_date: 开始日期

    Returns:
        Markdown字符串
    """
    service = ChainToPlannerService(user_id)
    planner_data = service.convert(itinerary_chain, title, start_date)
    return service.to_markdown(planner_data)
