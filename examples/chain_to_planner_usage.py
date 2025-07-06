"""
Chain到Planner转换服务使用示例

展示如何在不同场景下调用ChainToPlannerService进行数据转换。
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入服务类，避免Django配置问题
try:
    from planner.services.chain_to_planner_service import (
        ChainToPlannerService,
        convert_chain_to_planner,
        convert_chain_to_json,
        convert_chain_to_markdown
    )
except ImportError:
    # 如果导入失败，创建一个简化的服务类用于演示
    print("注意: 使用简化版服务类进行演示")

    class ChainToPlannerService:
        def __init__(self, user_id=1):
            self.user_id = user_id

        def convert(self, itinerary_chain, title=None, start_date=None):
            # 简化的转换逻辑
            return {
                'trip': {'title': title or '旅行计划', 'user_id': self.user_id},
                'days': [{'day_index': 1, 'date': start_date or '2024-01-01'}],
                'locations': [],
                'events': []
            }

        def validate_data(self, planner_data):
            return {'trip_fields': True, 'day_fields': True}

    def convert_chain_to_planner(itinerary_chain, user_id=1, title=None, start_date=None):
        service = ChainToPlannerService(user_id)
        return service.convert(itinerary_chain, title, start_date)

    def convert_chain_to_json(itinerary_chain, user_id=1, title=None, start_date=None):
        service = ChainToPlannerService(user_id)
        data = service.convert(itinerary_chain, title, start_date)
        return json.dumps(data, ensure_ascii=False, indent=2)

    def convert_chain_to_markdown(itinerary_chain, user_id=1, title=None, start_date=None):
        service = ChainToPlannerService(user_id)
        data = service.convert(itinerary_chain, title, start_date)
        return f"# {data['trip']['title']}\n\n转换成功！"


def example_1_basic_usage():
    """示例1: 基本使用"""
    print("=== 示例1: 基本使用 ===")

    # 示例数据
    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【故宫】",
                    "description": "参观故宫博物院"
                },
                {
                    "time_period": "中午",
                    "type": "dining",
                    "place": "附近",
                    "description": "在附近餐厅用餐"
                }
            ]
        }
    ]

    # 使用便捷函数
    planner_data = convert_chain_to_planner(
        itinerary_chain=itinerary_chain,
        user_id=1,
        title="北京1日游",
        start_date="2024-01-15"
    )

    print(f"转换结果:")
    print(f"  - Trip: {planner_data.trip['title']}")
    print(f"  - Days: {len(planner_data.days)} 天")
    print(f"  - Locations: {len(planner_data.locations)} 个")
    print(f"  - Events: {len(planner_data.events)} 个")
    print()


def example_2_service_instance():
    """示例2: 使用服务实例"""
    print("=== 示例2: 使用服务实例 ===")

    # 创建服务实例
    service = ChainToPlannerService(user_id=2)

    # 示例数据
    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "清晨",
                    "type": "dining",
                    "place": "酒店",
                    "description": "酒店早餐"
                },
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【天安门广场】",
                    "description": "参观天安门广场"
                },
                {
                    "time_period": "下午",
                    "type": "sightseeing",
                    "place": "【颐和园】",
                    "description": "游览颐和园"
                }
            ]
        }
    ]

    # 转换数据
    planner_data = service.convert(
        itinerary_chain=itinerary_chain,
        title="北京经典游",
        start_date="2024-01-20"
    )

    # 验证数据
    validation_results = service.validate_data(planner_data)
    print(f"数据验证结果:")
    for field, is_valid in validation_results.items():
        print(f"  - {field}: {'✅' if is_valid else '❌'}")
    print()


def example_3_json_export():
    """示例3: 导出为JSON"""
    print("=== 示例3: 导出为JSON ===")

    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【西湖】",
                    "description": "游览西湖"
                },
                {
                    "time_period": "中午",
                    "type": "dining",
                    "place": "【楼外楼】",
                    "description": "在楼外楼用餐"
                }
            ]
        }
    ]

    # 直接转换为JSON
    json_data = convert_chain_to_json(
        itinerary_chain=itinerary_chain,
        user_id=3,
        title="杭州1日游",
        start_date="2024-01-25"
    )

    print("JSON数据:")
    print(json_data[:500] + "..." if len(json_data) > 500 else json_data)
    print()


def example_4_markdown_export():
    """示例4: 导出为Markdown"""
    print("=== 示例4: 导出为Markdown ===")

    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【外滩】",
                    "description": "游览外滩"
                },
                {
                    "time_period": "中午",
                    "type": "dining",
                    "place": "【豫园】",
                    "description": "在豫园品尝小笼包"
                },
                {
                    "time_period": "下午",
                    "type": "sightseeing",
                    "place": "【南京路】",
                    "description": "逛南京路步行街"
                }
            ]
        }
    ]

    # 直接转换为Markdown
    markdown_data = convert_chain_to_markdown(
        itinerary_chain=itinerary_chain,
        user_id=4,
        title="上海1日游",
        start_date="2024-01-30"
    )

    print("Markdown数据:")
    print(markdown_data)
    print()


def example_5_django_integration():
    """示例5: Django集成"""
    print("=== 示例5: Django集成 ===")

    # 模拟Django环境下的使用
    try:
        import django
        from django.conf import settings

        # 设置Django环境
        if not settings.configured:
            django.setup()

        from planner.models import Trip, Day, Location, Activity

        itinerary_chain = [
            {
                "day": "Day 1",
                "activities": [
                    {
                        "time_period": "上午",
                        "type": "sightseeing",
                        "place": "【兵马俑】",
                        "description": "参观兵马俑博物馆"
                    }
                ]
            }
        ]

        # 转换数据
        service = ChainToPlannerService(user_id=5)
        planner_data = service.convert(
            itinerary_chain=itinerary_chain,
            title="西安1日游",
            start_date="2024-02-01"
        )

        print("Django模型数据:")
        print(f"  - Trip数据: {planner_data.trip}")
        print(f"  - 可以用于创建Django模型实例")
        print()

    except ImportError:
        print("Django未安装，跳过Django集成示例")
        print()


def example_6_api_usage():
    """示例6: API使用"""
    print("=== 示例6: API使用 ===")

    # 模拟API请求数据
    api_request = {
        "user_id": 6,
        "title": "成都2日游",
        "start_date": "2024-02-05",
        "itinerary_chain": [
            {
                "day": "Day 1",
                "activities": [
                    {
                        "time_period": "上午",
                        "type": "sightseeing",
                        "place": "【青羊宫】",
                        "description": "体验成都道教文化"
                    },
                    {
                        "time_period": "下午",
                        "type": "sightseeing",
                        "place": "【杜甫草堂】",
                        "description": "探访诗人故居"
                    }
                ]
            },
            {
                "day": "Day 2",
                "activities": [
                    {
                        "time_period": "上午",
                        "type": "sightseeing",
                        "place": "【武侯祠】",
                        "description": "参观武侯祠"
                    },
                    {
                        "time_period": "下午",
                        "type": "sightseeing",
                        "place": "【宽窄巷子】",
                        "description": "感受老成都生活"
                    }
                ]
            }
        ]
    }

    # 处理API请求
    service = ChainToPlannerService(user_id=api_request["user_id"])
    planner_data = service.convert(
        itinerary_chain=api_request["itinerary_chain"],
        title=api_request["title"],
        start_date=api_request["start_date"]
    )

    # 返回API响应
    api_response = {
        "success": True,
        "data": {
            "trip": planner_data.trip,
            "days": planner_data.days,
            "locations": planner_data.locations,
            "events": planner_data.events
        },
        "summary": {
            "total_days": len(planner_data.days),
            "total_locations": len(planner_data.locations),
            "total_events": len(planner_data.events)
        }
    }

    print("API响应:")
    print(json.dumps(api_response, ensure_ascii=False, indent=2))
    print()


def example_7_batch_processing():
    """示例7: 批量处理"""
    print("=== 示例7: 批量处理 ===")

    # 多个行程数据
    batch_itineraries = [
        {
            "id": "trip_1",
            "title": "北京2日游",
            "start_date": "2024-02-10",
            "itinerary_chain": [
                {
                    "day": "Day 1",
                    "activities": [
                        {
                            "time_period": "上午",
                            "type": "sightseeing",
                            "place": "【故宫】",
                            "description": "参观故宫"
                        }
                    ]
                }
            ]
        },
        {
            "id": "trip_2",
            "title": "上海1日游",
            "start_date": "2024-02-15",
            "itinerary_chain": [
                {
                    "day": "Day 1",
                    "activities": [
                        {
                            "time_period": "上午",
                            "type": "sightseeing",
                            "place": "【外滩】",
                            "description": "游览外滩"
                        }
                    ]
                }
            ]
        }
    ]

    service = ChainToPlannerService(user_id=7)
    results = []

    for trip_data in batch_itineraries:
        try:
            planner_data = service.convert(
                itinerary_chain=trip_data["itinerary_chain"],
                title=trip_data["title"],
                start_date=trip_data["start_date"]
            )

            results.append({
                "id": trip_data["id"],
                "success": True,
                "data": planner_data
            })

        except Exception as e:
            results.append({
                "id": trip_data["id"],
                "success": False,
                "error": str(e)
            })

    print("批量处理结果:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(
            f"  {status} {result['id']}: {'成功' if result['success'] else result['error']}")
    print()


def example_8_custom_configuration():
    """示例8: 自定义配置"""
    print("=== 示例8: 自定义配置 ===")

    # 自定义时间映射
    class CustomChainToPlannerService(ChainToPlannerService):
        TIME_PERIOD_MAPPING = {
            "清晨": "06:00",
            "上午": "08:00",
            "中午": "12:00",
            "下午": "15:00",
            "傍晚": "18:00",
            "夜晚": "21:00",
        }

        def get_location_category(self, place_name: str) -> str:
            """自定义地点分类逻辑"""
            if "公园" in place_name:
                return "sight"
            elif "商场" in place_name:
                return "custom"
            else:
                return super().get_location_category(place_name)

    # 使用自定义服务
    custom_service = CustomChainToPlannerService(user_id=8)

    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "清晨",
                    "type": "sightseeing",
                    "place": "【中央公园】",
                    "description": "晨练"
                },
                {
                    "time_period": "下午",
                    "type": "sightseeing",
                    "place": "【购物中心】",
                    "description": "购物"
                }
            ]
        }
    ]

    planner_data = custom_service.convert(
        itinerary_chain=itinerary_chain,
        title="纽约1日游",
        start_date="2024-02-20"
    )

    print("自定义配置结果:")
    print(f"  - 第一个事件时间: {planner_data.events[0]['start_time']}")
    print(f"  - 中央公园分类: {planner_data.locations[0]['category']}")
    print(f"  - 购物中心分类: {planner_data.locations[1]['category']}")
    print()


if __name__ == "__main__":
    print("Chain到Planner转换服务使用示例")
    print("=" * 50)

    # 运行所有示例
    example_1_basic_usage()
    example_2_service_instance()
    example_3_json_export()
    example_4_markdown_export()
    example_5_django_integration()
    example_6_api_usage()
    example_7_batch_processing()
    example_8_custom_configuration()

    print("所有示例运行完成！")
