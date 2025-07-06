"""
Django环境下的ChainToPlannerService使用示例
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


def create_sample_trip():
    """创建示例行程"""

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

    print("=== Django环境下的ChainToPlannerService使用示例 ===")

    # 创建或获取测试用户
    try:
        user = User.objects.get(username='demo_user')
        print(f"使用现有用户: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='demo_user',
            email='demo@example.com',
            password='demopass123'
        )
        print(f"创建新用户: {user.username}")

    # 创建服务实例
    service = ChainToPlannerService()

    # 执行转换
    print("\n1. 执行itinerary_chain转换...")
    result = service.convert_chain_to_planner(
        itinerary_chain=itinerary_chain,
        user=user,
        trip_title="成都2日游演示",
        trip_description="演示ChainToPlannerService功能的成都2日游行程",
        start_date=date(2024, 1, 15)
    )

    if result['success']:
        print("✅ 转换成功!")
        print(f"   - Trip ID: {result['summary']['trip_id']}")
        print(f"   - 天数: {result['summary']['total_days']}")
        print(f"   - 事件数: {result['summary']['total_events']}")
        print(f"   - 地点数: {result['summary']['total_locations']}")

        # 生成markdown
        print("\n2. 生成Markdown格式...")
        markdown_content = service.get_planner_data_as_markdown(result['trip'])
        print("✅ Markdown生成成功!")
        print("Markdown内容预览:")
        print(markdown_content[:500] +
              "..." if len(markdown_content) > 500 else markdown_content)

        # 导出JSON
        print("\n3. 导出JSON格式...")
        json_data = service.export_trip_to_json(result['trip'])
        print("✅ JSON导出成功!")
        print(f"   - JSON包含 {len(json_data['days'])} 天数据")

        # 显示数据库中的实际数据
        print("\n4. 数据库中的数据:")
        from planner.models import Trip, Day, Event, Location

        trip = Trip.objects.get(id=result['summary']['trip_id'])
        days = Day.objects.filter(trip=trip)
        events = Event.objects.filter(trip=trip)
        locations = Location.objects.filter(events__trip=trip).distinct()

        print(f"   - Trip: {trip.title} (ID: {trip.id})")
        print(f"   - Days: {days.count()} 天")
        print(f"   - Events: {events.count()} 个事件")
        print(f"   - Locations: {locations.count()} 个地点")

        # 显示创建的地点
        print("\n5. 创建的地点:")
        for location in locations:
            print(f"   - {location.name} ({location.get_category_display()})")

        # 显示第一天的事件安排
        print("\n6. 第一天的事件安排:")
        day1_events = events.filter(
            date=trip.start_date).order_by('start_time')
        for event in day1_events:
            location_name = event.location.name if event.location else "无地点"
            print(
                f"   - {event.start_time.strftime('%H:%M')} {event.title} @ {location_name}")

        print("\n✅ 示例完成!")
        return result

    else:
        print(f"❌ 转换失败: {result['error']}")
        return None


def show_api_usage():
    """显示API使用示例"""
    print("\n=== API使用示例 ===")

    print("1. 转换行程链 (POST /planner/api/convert-chain/):")
    print("""
curl -X POST http://localhost:8000/planner/api/convert-chain/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "itinerary_chain": [
      {
        "day": "Day 1",
        "activities": [
          {
            "time_period": "上午",
            "type": "sightseeing",
            "place": "【青羊宫】",
            "description": "体验成都道教文化"
          }
        ]
      }
    ],
    "trip_title": "成都1日游",
    "trip_description": "体验成都文化",
    "start_date": "2024-01-15"
  }'
""")

    print("2. 获取Markdown格式 (GET /planner/api/trips/{trip_id}/markdown/):")
    print("""
curl -X GET http://localhost:8000/planner/api/trips/1/markdown/ \\
  -H "Authorization: Bearer YOUR_TOKEN"
""")

    print("3. 获取JSON格式 (GET /planner/api/trips/{trip_id}/json/):")
    print("""
curl -X GET http://localhost:8000/planner/api/trips/1/json/ \\
  -H "Authorization: Bearer YOUR_TOKEN"
""")


if __name__ == "__main__":
    try:
        # 创建示例行程
        result = create_sample_trip()

        # 显示API使用示例
        show_api_usage()

        if result and result['success']:
            print("\n🎉 Django环境测试完成，服务功能正常!")
        else:
            print("\n❌ Django环境测试失败")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
