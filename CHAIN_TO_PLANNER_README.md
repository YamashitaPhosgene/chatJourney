# ChainToPlannerService 使用文档

## 概述

`ChainToPlannerService` 是一个将 `itinerary_chain` 格式的行程数据转换为 Planner 应用数据结构的服务。该服务能够自动创建 Trip、Day、Event、Activity 和 Location 等数据模型，并提供多种输出格式。

## 功能特性

- 🔄 **数据转换**: 将 itinerary_chain 转换为完整的 Planner 数据结构
- 🕐 **时间映射**: 自动将时间段（如"上午"、"下午"）映射为具体时间
- 📍 **地点管理**: 智能创建和管理 Location 对象，支持地点分类
- 📊 **多格式输出**: 支持 Markdown 和 JSON 格式导出
- 🔗 **API 集成**: 提供完整的 REST API 接口
- 🛡️ **错误处理**: 完善的异常处理和错误报告机制

## 数据结构映射

### 输入格式 (itinerary_chain)

```json
[
  {
    "day": "Day 1",
    "activities": [
      {
        "time_period": "上午",
        "type": "sightseeing",
        "place": "【青羊宫】",
        "description": "体验成都道教文化与静谧氛围"
      }
    ]
  }
]
```

### 输出格式 (Planner 数据结构)

- **Trip**: 旅行主表
- **Day**: 天数管理
- **Activity**: 活动事件
- **Location**: 地点信息

## 时间映射规则

| 时间段 | 映射时间 | 说明     |
| ------ | -------- | -------- |
| 清晨   | 07:00    | 早餐时间 |
| 上午   | 09:00    | 上午活动 |
| 中午   | 12:00    | 午餐时间 |
| 下午   | 14:00    | 下午活动 |
| 傍晚   | 17:00    | 晚餐时间 |
| 夜晚   | 20:00    | 休息时间 |

## 地点分类规则

| 关键词                                   | 分类       | 说明   |
| ---------------------------------------- | ---------- | ------ |
| 宫、寺、祠、堂、园、公园、博物馆、纪念馆 | sight      | 景点   |
| 酒店、宾馆、客栈、民宿                   | hotel      | 住宿   |
| 餐厅、饭店、小吃、美食                   | restaurant | 餐饮   |
| 机场、车站、地铁、公交                   | transport  | 交通   |
| 其他                                     | custom     | 自定义 |

## 使用方法

### 1. 基本使用

```python
from planner.services.chain_to_planner_service import ChainToPlannerService
from datetime import date

# 创建服务实例
service = ChainToPlannerService()

# 转换数据
result = service.convert_chain_to_planner(
    itinerary_chain=itinerary_chain,
    user=user,
    trip_title="成都2日游",
    trip_description="体验成都文化",
    start_date=date(2024, 1, 15)
)

if result['success']:
    print(f"转换成功! Trip ID: {result['summary']['trip_id']}")
else:
    print(f"转换失败: {result['error']}")
```

### 2. 生成 Markdown

```python
# 获取 Trip 对象
trip = result['trip']

# 生成 Markdown 格式
markdown_content = service.get_planner_data_as_markdown(trip)
print(markdown_content)
```

### 3. 导出 JSON

```python
# 导出 JSON 格式
json_data = service.export_trip_to_json(trip)
print(json_data)
```

## API 接口

### 1. 转换行程链

**POST** `/planner/api/convert-chain/`

**请求体**:

```json
{
    "itinerary_chain": [...],
    "trip_title": "旅行标题",
    "trip_description": "旅行描述",
    "start_date": "2024-01-15"
}
```

**响应**:

```json
{
  "success": true,
  "trip_id": 1,
  "summary": {
    "trip_id": 1,
    "total_days": 2,
    "total_events": 10,
    "total_locations": 4
  },
  "message": "行程转换成功"
}
```

### 2. 获取 Markdown 格式

**GET** `/planner/api/trips/{trip_id}/markdown/`

**响应**:

```json
{
  "success": true,
  "trip_id": 1,
  "markdown": "# 成都2日游\n\n..."
}
```

### 3. 获取 JSON 格式

**GET** `/planner/api/trips/{trip_id}/json/`

**响应**:

```json
{
    "success": true,
    "trip_id": 1,
    "data": {
        "id": 1,
        "title": "成都2日游",
        "days": [...]
    }
}
```

### 4. 获取用户行程列表

**GET** `/planner/api/trips/`

**响应**:

```json
{
    "success": true,
    "trips": [...],
    "total": 5
}
```

## 与 TimelineService 集成

```python
from talker.services.timeline_service import TimelineService
from planner.services.chain_to_planner_service import ChainToPlannerService

# 1. 使用 TimelineService 生成行程链
timeline_service = TimelineService()
timeline_result = timeline_service.generate_timeline(session)

if timeline_result['success']:
    # 2. 转换为 Planner 数据结构
    chain_service = ChainToPlannerService()
    planner_result = chain_service.convert_chain_to_planner(
        itinerary_chain=timeline_result['itinerary_chain'],
        user=user,
        trip_title="AI生成的行程",
        start_date=date.today()
    )

    if planner_result['success']:
        print("✅ 成功从 TimelineService 转换到 Planner!")
```

## 测试

运行测试脚本：

```bash
python test_chain_to_planner.py
```

测试内容包括：

- 时间映射验证
- 地点创建逻辑
- 完整转换流程
- 数据完整性检查

## 错误处理

服务提供详细的错误信息：

```python
if not result['success']:
    print(f"错误类型: {result['error_type']}")
    print(f"错误信息: {result['error']}")
```

常见错误类型：

- `ValueError`: 数据验证错误
- `RuntimeError`: 服务调用错误
- `KeyError`: 数据字段缺失
- `JSONDecodeError`: JSON 解析错误

## 配置说明

### 时间映射配置

可以在服务初始化时自定义时间映射：

```python
service = ChainToPlannerService()
service.time_period_mapping = {
    "清晨": time(6, 0),    # 自定义时间
    "上午": time(9, 30),   # 自定义时间
    # ...
}
```

### 地点分类配置

可以扩展地点分类规则：

```python
def custom_location_category(self, place_name: str) -> str:
    # 自定义分类逻辑
    if "温泉" in place_name:
        return "leisure"
    return super()._determine_location_category(place_name)
```

## 注意事项

1. **用户权限**: 所有操作都需要用户登录
2. **数据清理**: 地点名称会自动清理【】等标记
3. **重复处理**: 相同名称的地点会被复用
4. **时间冲突**: 同一时间段的活动会按顺序排列
5. **数据持久化**: 转换后的数据会保存到数据库

## 扩展功能

### 自定义事件类型

可以扩展支持更多事件类型：

```python
# 在 Activity 模型中添加新的分类
CATEGORY_CHOICES = [
    ('sightseeing', '游览'),
    ('dining', '餐饮'),
    ('shopping', '购物'),  # 新增
    ('entertainment', '娱乐'),  # 新增
    # ...
]
```

### 地理坐标支持

可以为 Location 添加地理坐标：

```python
location = Location.objects.create(
    name="青羊宫",
    category="sight",
    latitude=30.6586,
    longitude=104.0657
)
```

## 总结

`ChainToPlannerService` 提供了一个完整的解决方案，将 AI 生成的行程链数据转换为结构化的 Planner 应用数据。通过合理的映射规则和错误处理机制，确保了数据转换的准确性和可靠性。
