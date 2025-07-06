# Chain 到 Planner 转换服务使用指南

## 概述

Chain 到 Planner 转换服务 (`ChainToPlannerService`) 是一个专门用于将 `itinerary_chain` 格式的数据转换为 Planner 应用数据结构的服务。该服务完全符合 `PLANNER_MODELS_DOCUMENTATION.md` 中的模型规范。

## 快速开始

### 1. 基本使用

```python
from planner.services.chain_to_planner_service import convert_chain_to_planner

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

# 转换数据
planner_data = convert_chain_to_planner(
    itinerary_chain=itinerary_chain,
    user_id=1,
    title="北京1日游",
    start_date="2024-01-15"
)

print(f"Trip: {planner_data.trip['title']}")
print(f"Days: {len(planner_data.days)} 天")
print(f"Locations: {len(planner_data.locations)} 个")
print(f"Events: {len(planner_data.events)} 个")
```

### 2. 使用服务实例

```python
from planner.services.chain_to_planner_service import ChainToPlannerService

# 创建服务实例
service = ChainToPlannerService(user_id=1)

# 转换数据
planner_data = service.convert(
    itinerary_chain=itinerary_chain,
    title="北京1日游",
    start_date="2024-01-15"
)

# 验证数据
validation_results = service.validate_data(planner_data)
for field, is_valid in validation_results.items():
    print(f"{field}: {'✅' if is_valid else '❌'}")
```

## 输出格式

### 1. JSON 格式

```python
from planner.services.chain_to_planner_service import convert_chain_to_json

# 直接转换为JSON
json_data = convert_chain_to_json(
    itinerary_chain=itinerary_chain,
    user_id=1,
    title="北京1日游",
    start_date="2024-01-15"
)

print(json_data)
```

### 2. Markdown 格式

```python
from planner.services.chain_to_planner_service import convert_chain_to_markdown

# 直接转换为Markdown
markdown_data = convert_chain_to_markdown(
    itinerary_chain=itinerary_chain,
    user_id=1,
    title="北京1日游",
    start_date="2024-01-15"
)

print(markdown_data)
```

## 在 Django 中使用

### 1. 在视图中使用

```python
from django.http import JsonResponse
from planner.services.chain_to_planner_service import ChainToPlannerService

def convert_itinerary_view(request):
    if request.method == 'POST':
        data = request.POST
        itinerary_chain = data.get('itinerary_chain')
        user_id = data.get('user_id', 1)
        title = data.get('title', '旅行计划')
        start_date = data.get('start_date')

        service = ChainToPlannerService(user_id=user_id)
        planner_data = service.convert(
            itinerary_chain=itinerary_chain,
            title=title,
            start_date=start_date
        )

        return JsonResponse({
            'success': True,
            'data': {
                'trip': planner_data.trip,
                'days': planner_data.days,
                'locations': planner_data.locations,
                'events': planner_data.events
            }
        })
```

### 2. 创建 Django 模型实例

```python
from planner.models import Trip, Day, Location, Activity
from planner.services.chain_to_planner_service import ChainToPlannerService

def create_planner_models(itinerary_chain, user):
    service = ChainToPlannerService(user_id=user.id)
    planner_data = service.convert(itinerary_chain)

    # 创建Trip
    trip = Trip.objects.create(
        user=user,
        title=planner_data.trip['title'],
        description=planner_data.trip['description'],
        start_date=planner_data.trip['start_date'],
        end_date=planner_data.trip['end_date']
    )

    # 创建Locations
    locations = {}
    for location_data in planner_data.locations:
        location = Location.objects.create(
            name=location_data['name'],
            category=location_data['category'],
            address=location_data['address']
        )
        locations[location_data['id']] = location

    # 创建Events
    for event_data in planner_data.events:
        location = locations.get(event_data['location_id'])
        Activity.objects.create(
            trip=trip,
            date=event_data['date'],
            start_time=event_data['start_time'],
            duration=event_data['duration'],
            title=event_data['title'],
            description=event_data['description'],
            category=event_data.get('category', 'custom'),
            location=location
        )

    return trip
```

## API 集成

### 1. REST API 端点

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from planner.services.chain_to_planner_service import ChainToPlannerService

@api_view(['POST'])
def convert_itinerary_api(request):
    try:
        itinerary_chain = request.data.get('itinerary_chain')
        user_id = request.data.get('user_id', 1)
        title = request.data.get('title')
        start_date = request.data.get('start_date')

        service = ChainToPlannerService(user_id=user_id)
        planner_data = service.convert(
            itinerary_chain=itinerary_chain,
            title=title,
            start_date=start_date
        )

        return Response({
            'success': True,
            'data': {
                'trip': planner_data.trip,
                'days': planner_data.days,
                'locations': planner_data.locations,
                'events': planner_data.events
            },
            'summary': {
                'total_days': len(planner_data.days),
                'total_locations': len(planner_data.locations),
                'total_events': len(planner_data.events)
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
```

### 2. 批量处理

```python
def batch_convert_itineraries(itineraries_list):
    service = ChainToPlannerService()
    results = []

    for trip_data in itineraries_list:
        try:
            planner_data = service.convert(
                itinerary_chain=trip_data['itinerary_chain'],
                title=trip_data['title'],
                start_date=trip_data['start_date']
            )

            results.append({
                'id': trip_data['id'],
                'success': True,
                'data': planner_data
            })

        except Exception as e:
            results.append({
                'id': trip_data['id'],
                'success': False,
                'error': str(e)
            })

    return results
```

## 自定义配置

### 1. 继承服务类

```python
class CustomChainToPlannerService(ChainToPlannerService):
    # 自定义时间映射
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
custom_service = CustomChainToPlannerService(user_id=1)
planner_data = custom_service.convert(itinerary_chain)
```

### 2. 自定义验证规则

```python
def custom_validation(planner_data):
    service = ChainToPlannerService()
    base_validation = service.validate_data(planner_data)

    # 添加自定义验证
    custom_validation = {
        'has_breakfast': any(
            event['type'] == 'activity' and
            event.get('category') == 'dining' and
            event['start_time'] < '10:00'
            for event in planner_data.events
        ),
        'has_dinner': any(
            event['type'] == 'activity' and
            event.get('category') == 'dining' and
            event['start_time'] > '18:00'
            for event in planner_data.events
        )
    }

    return {**base_validation, **custom_validation}
```

## 数据格式说明

### 输入格式 (itinerary_chain)

```python
itinerary_chain = [
    {
        "day": "Day 1",
        "activities": [
            {
                "time_period": "上午",  # 时间段：清晨/上午/中午/下午/傍晚/夜晚
                "type": "sightseeing",  # 类型：sightseeing/dining/stay/transport
                "place": "【故宫】",     # 地点名称
                "description": "参观故宫博物院"  # 活动描述
            }
        ]
    }
]
```

### 输出格式 (PlannerData)

```python
@dataclass
class PlannerData:
    trip: Dict[str, Any]      # Trip数据
    days: List[Dict[str, Any]]    # Day数据列表
    locations: List[Dict[str, Any]]  # Location数据列表
    events: List[Dict[str, Any]]     # Event数据列表
```

## 错误处理

```python
try:
    planner_data = convert_chain_to_planner(itinerary_chain)
except ValueError as e:
    print(f"数据格式错误: {e}")
except Exception as e:
    print(f"转换失败: {e}")
```

## 性能优化

### 1. 批量处理

```python
# 使用单个服务实例处理多个行程
service = ChainToPlannerService(user_id=1)
results = []

for itinerary in itineraries:
    result = service.convert(itinerary)
    results.append(result)
```

### 2. 缓存地点

```python
# 地点去重，避免重复创建
existing_locations = {}
for location in planner_data.locations:
    if location['name'] not in existing_locations:
        existing_locations[location['name']] = location
```

## 测试

运行测试示例：

```bash
python examples/chain_to_planner_usage.py
```

或者运行简化测试：

```bash
python simple_test_chain.py
```

## 注意事项

1. **时间格式**: 所有时间都使用 "HH:MM" 格式
2. **日期格式**: 使用 "YYYY-MM-DD" 格式
3. **地点清理**: 自动清理【】标记和"和"连接的地点
4. **类型映射**: 自动映射活动类型到 Planner 事件类型
5. **数据验证**: 提供完整的数据验证功能

## 支持的功能

- ✅ 基本数据转换
- ✅ JSON 导出
- ✅ Markdown 导出
- ✅ 数据验证
- ✅ 自定义配置
- ✅ 批量处理
- ✅ Django 集成
- ✅ API 集成
- ✅ 错误处理
- ✅ 性能优化

## 相关文件

- `planner/services/chain_to_planner_service.py` - 核心服务
- `examples/chain_to_planner_usage.py` - 使用示例
- `simple_test_chain.py` - 简化测试
- `PLANNER_MODELS_DOCUMENTATION.md` - 模型文档
