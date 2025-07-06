

"""
ChainToPlannerService 功能测试
"""

from planner.services.chain_to_planner_service import ChainToPlannerService
from django.contrib.auth.models import User
import os
import sys
import django
from datetime import date

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

# 在Django初始化后再导入相关模块


def test_chain_conversion():
    """测试itinerary_chain转换功能"""

    # 测试数据
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

    print("=== 测试ChainToPlannerService ===")

    # 创建或获取测试用户
    try:
        user = User.objects.get(username='test_user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        print(f"创建测试用户: {user.username}")

    # 创建服务实例
    service = ChainToPlannerService()

    # 执行转换
    print("\n1. 执行itinerary_chain转换...")
    result = service.convert_chain_to_planner(
        itinerary_chain=itinerary_chain,
        user=user,
        trip_title="成都2日游测试",
        trip_description="测试转换功能的成都2日游行程",
        start_date=date(2024, 1, 15)
    )

    if result['success']:
        print("✅ 转换成功!")
        print(f"   - Trip ID: {result['summary']['trip_id']}")
        print(f"   - 天数: {result['summary']['total_days']}")
        print(f"   - 事件数: {result['summary']['total_events']}")
        print(f"   - 地点数: {result['summary']['total_locations']}")

        # 测试markdown生成
        print("\n2. 生成Markdown格式...")
        markdown_content = service.get_planner_data_as_markdown(result['trip'])
        print("✅ Markdown生成成功!")
        print("Markdown内容预览:")
        print(markdown_content[:500] +
              "..." if len(markdown_content) > 500 else markdown_content)

        # 测试JSON导出
        print("\n3. 导出JSON格式...")
        json_data = service.export_trip_to_json(result['trip'])
        print("✅ JSON导出成功!")
        print(f"   - JSON包含 {len(json_data['days'])} 天数据")
        print(f"   - 第一天包含 {len(json_data['days'][0]['events'])} 个事件")

        # 验证数据完整性
        print("\n4. 验证数据完整性...")
        from planner.models import Trip, Day, Event, Location

        trip = Trip.objects.get(id=result['summary']['trip_id'])
        days = Day.objects.filter(trip=trip)
        events = Event.objects.filter(trip=trip)
        locations = Location.objects.filter(events__trip=trip).distinct()

        print(f"   - 数据库中的Trip: {trip.title}")
        print(f"   - 数据库中的Day数量: {days.count()}")
        print(f"   - 数据库中的Event数量: {events.count()}")
        print(f"   - 数据库中的Location数量: {locations.count()}")

        # 显示创建的地点
        print("\n5. 创建的地点列表:")
        for location in locations:
            print(f"   - {location.name} ({location.get_category_display()})")

        # 显示第一天的事件
        print("\n6. 第一天的事件安排:")
        day1_events = events.filter(
            date=trip.start_date).order_by('start_time')
        for event in day1_events:
            location_name = event.location.name if event.location else "无地点"
            print(
                f"   - {event.start_time.strftime('%H:%M')} {event.title} @ {location_name}")

        print("\n✅ 所有测试通过!")
        return result

    else:
        print(f"❌ 转换失败: {result['error']}")
        return None


def test_location_creation():
    """测试地点创建逻辑"""
    print("\n=== 测试地点创建逻辑 ===")

    service = ChainToPlannerService()

    test_places = [
        "【青羊宫】",
        "【杜甫草堂】",
        "【武侯祠】和【锦里古街】",
        "【宽窄巷子】",
        "酒店",
        "自行解决",
        "附近"
    ]

    for place in test_places:
        clean_name = service._clean_place_name(place)
        category = service._determine_location_category(clean_name)
        print(f"   - 原始: '{place}' -> 清理: '{clean_name}' -> 分类: {category}")


def test_time_mapping():
    """测试时间映射"""
    print("\n=== 测试时间映射 ===")

    service = ChainToPlannerService()

    for period, time_obj in service.time_period_mapping.items():
        print(f"   - {period}: {time_obj.strftime('%H:%M')}")


if __name__ == "__main__":
    print("开始ChainToPlannerService功能测试...")

    # 测试时间映射
    test_time_mapping()

    # 测试地点创建逻辑
    test_location_creation()

    # 测试完整转换流程
    result = test_chain_conversion()

    if result and result['success']:
        print("\n🎉 所有测试完成，服务功能正常!")
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)
