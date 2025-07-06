

"""
ChainToPlannerService 使用示例
"""

from datetime import date
from django.contrib.auth.models import User
from planner.services.chain_to_planner_service import ChainToPlannerService


def example_usage():
    """使用示例"""

    # 示例itinerary_chain数据
    itinerary_chain = [
        {
            "day": "Day 1",
            "activities": [
                {
                    "time_period": "清晨",
                    "type": "dining",
                    "place": "自行解决",
                    "description": "早餐自行解决"
                },
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【青羊宫】",
                    "description": "体验成都道教文化与静谧氛围"
                },
                {
                    "time_period": "中午",
                    "type": "dining",
                    "place": "附近",
                    "description": "由系统推荐合适餐厅"
                },
                {
                    "time_period": "下午",
                    "type": "sightseeing",
                    "place": "【杜甫草堂】",
                    "description": "探访诗人故居，感受唐代文化遗韵"
                },
                {
                    "time_period": "夜晚",
                    "type": "stay",
                    "place": "酒店",
                    "description": "返回酒店休息，结束一天行程"
                }
            ]
        },
        {
            "day": "Day 2",
            "activities": [
                {
                    "time_period": "清晨",
                    "type": "dining",
                    "place": "自行解决",
                    "description": "早餐自行解决"
                },
                {
                    "time_period": "上午",
                    "type": "sightseeing",
                    "place": "【武侯祠】和【锦里古街】",
                    "description": "逛特色小吃与手工艺店，可顺便午餐"
                },
                {
                    "time_period": "下午",
                    "type": "sightseeing",
                    "place": "【宽窄巷子】",
                    "description": "感受老成都的街巷生活"
                },
                {
                    "time_period": "傍晚",
                    "type": "dining",
                    "place": "附近",
                    "description": "稍作散步后回酒店休息"
                },
                {
                    "time_period": "夜晚",
                    "type": "stay",
                    "place": "酒店",
                    "description": "返回酒店休息，结束一天行程"
                }
            ]
        }
    ]

    # 创建服务实例
    service = ChainToPlannerService()

    # 获取用户（这里需要实际的用户对象）
    # user = User.objects.get(username='example_user')

    # 转换itinerary_chain为planner数据结构
    result = service.convert_chain_to_planner(
        itinerary_chain=itinerary_chain,
        user=None,  # 实际使用时需要提供用户对象
        trip_title="成都2日游",
        trip_description="体验成都道教文化、历史遗迹和特色小吃",
        start_date=date(2024, 1, 15)  # 示例开始日期
    )

    if result['success']:
        print("✅ 转换成功!")
        print(f"创建了 {result['summary']['total_days']} 天行程")
        print(f"创建了 {result['summary']['total_events']} 个事件")
        print(f"创建了 {result['summary']['total_locations']} 个地点")

        # 生成markdown格式
        markdown_content = service.get_planner_data_as_markdown(result['trip'])
        print("\n📝 Markdown格式:")
        print(markdown_content)

        # 导出JSON格式
        json_data = service.export_trip_to_json(result['trip'])
        print(f"\n📊 JSON数据包含 {len(json_data['days'])} 天")

    else:
        print(f"❌ 转换失败: {result['error']}")


def example_with_timeline_service_integration():
    """与TimelineService集成的示例"""

    # 模拟从TimelineService获取的数据
    timeline_data = {
        'success': True,
        'itinerary_chain': [
            {
                "day": "Day 1",
                "activities": [
                    {
                        "time_period": "上午",
                        "type": "sightseeing",
                        "place": "【天安门广场】",
                        "description": "参观天安门广场，感受首都的庄严氛围"
                    },
                    {
                        "time_period": "中午",
                        "type": "dining",
                        "place": "【全聚德烤鸭】",
                        "description": "品尝北京特色烤鸭"
                    },
                    {
                        "time_period": "下午",
                        "type": "sightseeing",
                        "place": "【故宫博物院】",
                        "description": "游览故宫，了解明清历史"
                    }
                ]
            }
        ]
    }

    # 检查timeline数据是否成功
    if timeline_data.get('success') and 'itinerary_chain' in timeline_data:
        service = ChainToPlannerService()

        result = service.convert_chain_to_planner(
            itinerary_chain=timeline_data['itinerary_chain'],
            user=None,  # 实际使用时需要提供用户对象
            trip_title="北京1日游",
            trip_description="从TimelineService生成的行程",
            start_date=date(2024, 1, 20)
        )

        if result['success']:
            print("✅ TimelineService集成成功!")
            return result
        else:
            print(f"❌ TimelineService集成失败: {result['error']}")
            return None
    else:
        print("❌ TimelineService数据无效")
        return None


if __name__ == "__main__":
    print("=== ChainToPlannerService 使用示例 ===")
    example_usage()
    print("\n=== TimelineService 集成示例 ===")
    example_with_timeline_service_integration()
