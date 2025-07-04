# RouteTimeService 使用说明

## 概述

`RouteTimeService` 是一个增强的行程规划服务，能够解析大模型生成的行程文本，计算交通时间，并将完整的行程保存到数据库中。

## 主要功能

### 1. 解析多天行程
支持解析大模型 `show_plan` 生成的行程格式：
```
Day1: 武侯祠(三国文化, 时长90分钟) --步行-- 锦里古街(小吃打卡, 时长60分钟)
Day2: 宽窄巷子(老巷闲逛, 时长120分钟)
```

### 2. 计算交通时间
自动计算各段路程的交通时间，支持多种交通方式：
- 步行、骑行
- 地铁、公交
- 打车、自驾
- 高铁、飞机、火车

### 3. 数据库保存
将解析的行程保存到 Django 数据库模型中：
- `Trip`: 行程基本信息
- `Day`: 每日安排
- `Activity`: 活动详情
- `Transport`: 交通信息
- `Location`: 地点信息

## 基本使用

### 初始化服务

```python
from planner.services.route_time_service import RouteTimeService

# 使用环境变量中的 AMAP_KEY
service = RouteTimeService()

# 或指定 API 密钥
service = RouteTimeService(amap_key="your_amap_key")
```

### 解析行程文本

```python
plan_text = """
Day1: 武侯祠(三国文化, 时长90分钟) --步行-- 锦里古街(小吃打卡, 时长60分钟)
Day2: 宽窄巷子(老巷闲逛, 时长120分钟)
"""

# 解析多天行程
day_plans = service.parse_multi_day_plan(plan_text)

for day_plan in day_plans:
    print(f"第{day_plan.day_number}天:")
    for activity in day_plan.activities:
        print(f"  {activity.location}: {activity.name} ({activity.duration_minutes}分钟)")
```

### 计算详细时间安排

```python
# 计算完整的时间安排
result = service.compute_multi_day_plan(
    plan_text=plan_text,
    city_hint="成都",
    start_date=date(2025, 1, 1)
)

print(f"总天数: {result['total_days']}")
print(f"总活动数: {result['total_activities']}")
print(f"总交通时间: {result['total_transport_time']}秒")
print(f"总活动时间: {result['total_activity_time']}秒")

# 查看每天的详细安排
for day in result['days']:
    print(f"\n第{day['day_number']}天:")
    for item in day['schedule']:
        if item['type'] == 'activity':
            print(f"  📍 {item['start_time']} - {item['end_time']}: {item['location']}")
        else:
            print(f"  🚗 {item['start_time']} - {item['end_time']}: {item['from']} → {item['to']}")
```

### 保存到数据库

```python
from django.contrib.auth.models import User
from datetime import date

# 获取用户
user = User.objects.get(username='your_username')

# 保存行程到数据库
trip = service.save_plan_to_db(
    plan_text=plan_text,
    user=user,
    trip_title="成都两日游",
    trip_description="体验成都三国文化和美食",
    city_hint="成都",
    start_date=date(2025, 1, 1)
)

print(f"行程已保存，ID: {trip.id}")
print(f"行程标题: {trip.title}")
print(f"开始日期: {trip.start_date}")
print(f"结束日期: {trip.end_date}")
```

## 数据库模型关系

保存后的数据结构：

```
Trip (行程)
├── Day (天数)
│   ├── Activity (活动)
│   │   └── Location (地点)
│   └── Transport (交通)
│       ├── Location (起点)
│       └── Location (终点)
```

### 查询保存的数据

```python
from planner.models import Trip, Activity, Transport, Location, Day

# 查询用户的行程
trips = Trip.objects.filter(user=user)

# 查询行程的所有活动
activities = Activity.objects.filter(trip=trip).order_by('date', 'start_time')

# 查询行程的所有交通
transports = Transport.objects.filter(trip=trip).order_by('date', 'start_time')

# 查询行程涉及的所有地点
locations = Location.objects.filter(activity__trip=trip).distinct()
```

## 支持的交通方式

| 中文名称 | 英文标识 | 说明 |
|---------|---------|------|
| 步行 | walking | 步行导航 |
| 地铁 | transit | 公共交通 |
| 公交 | transit | 公共交通 |
| 打车 | driving | 驾车导航 |
| 自驾 | driving | 驾车导航 |
| 骑行 | bicycling | 骑行导航 |
| 高铁 | driving | 高铁站间交通 |
| 飞机 | driving | 机场间交通 |
| 火车 | driving | 火车站间交通 |

## 错误处理

```python
try:
    trip = service.save_plan_to_db(plan_text, user, "测试行程")
except ValueError as e:
    print(f"解析错误: {e}")
except AmapAPIError as e:
    print(f"高德API错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 注意事项

1. **API 密钥**: 需要配置有效的高德地图 API 密钥
2. **网络连接**: 需要网络连接以调用高德 API
3. **数据格式**: 行程文本必须严格按照指定格式
4. **用户权限**: 保存到数据库需要有效的用户对象
5. **时间计算**: 交通时间基于实时路况计算，可能因时段而异

## 与 show_plan 的集成

在 `state_machine.py` 中的 `show_plan` 方法可以集成 `RouteTimeService`：

```python
def show_plan(self, *args, **kwargs):
    """显示计划"""
    # ... 现有代码 ...
    
    # 获取大模型生成的行程文本
    response_text = response.get('data', {}).get('content', '')
    
    # 解析行程文本并保存到数据库
    try:
        service = RouteTimeService()
        trip = service.save_plan_to_db(
            plan_text=response_text,
            user=self.session.user,
            trip_title=f"行程_{self.session.id}",
            trip_description="AI生成的行程计划"
        )
        print(f"行程已保存到数据库，ID: {trip.id}")
    except Exception as e:
        print(f"保存行程失败: {e}")
    
    return response_text
```

## 测试

运行测试脚本：

```bash
# 测试解析功能（不依赖API）
python route_time_demo.py

# 测试数据库保存功能（需要API密钥）
python test_db_save.py
```

## 扩展功能

### 自定义交通方式映射

```python
# 扩展交通方式映射
service.TRANSPORT_MODE_MAP.update({
    "轮渡": "other",
    "缆车": "other",
})
```

### 自定义时间计算

```python
# 重写交通时间计算方法
def custom_transport_duration(self, from_location, to_location, transport_mode, city_hint):
    # 自定义逻辑
    return 1800  # 返回秒数
```

## 性能优化

1. **批量地理编码**: 对相同地点只编码一次
2. **缓存机制**: 可以添加 Redis 缓存减少 API 调用
3. **异步处理**: 对于复杂行程可以使用异步处理
4. **数据库优化**: 使用 `bulk_create` 批量创建记录 