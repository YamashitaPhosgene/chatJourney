# Planner 应用模型存储结构文档

## 概述

Planner 应用采用 Django ORM 设计了一套完整的旅行规划数据模型，支持复杂的行程管理功能。该模型系统使用了模型继承、外键关联等高级 Django 特性，提供了灵活且可扩展的数据存储方案。

## 模型架构图

```
Trip (旅行)
├── Event (事件基类)
│   ├── Activity (活动)
│   ├── Transport (交通)
│   └── Accommodation (住宿)
├── Day (天数)
└── Location (地点)
```

## 详细模型说明

### 1. Trip 模型 (旅行主表)

**用途**: 旅行计划的核心实体，代表一次完整的旅行。

**字段详情**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| user | ForeignKey | CASCADE, related_name='trips' | 关联用户，支持多用户系统 |
| title | CharField | max_length=200 | 旅行标题 |
| description | TextField | blank=True | 旅行描述，可选 |
| start_date | DateField | 必填 | 旅行开始日期 |
| end_date | DateField | 必填 | 旅行结束日期 |
| created_at | DateTimeField | auto_now_add=True | 创建时间 |
| updated_at | DateTimeField | auto_now=True | 更新时间 |

**关系**:
- 一对多关系：一个 Trip 可以有多个 Event 和 Day
- 多对一关系：属于某个用户 (User)

**设计亮点**:
- 支持时间范围管理
- 自动时间戳追踪
- 用户隔离设计

---

### 2. Event 模型 (事件基类)

**用途**: 旅行中所有事件的抽象基类，使用 Django 模型继承实现多态。

**字段详情**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| trip | ForeignKey | CASCADE, related_name='events' | 所属旅行 |
| type | CharField | max_length=20, choices=EVENT_TYPES | 事件类型枚举 |
| date | DateField | 必填 | 事件日期 |
| start_time | TimeField | 必填 | 开始时间 |
| duration | DurationField | default=timedelta(hours=1) | 持续时间 |
| cost | DecimalField | max_digits=10, decimal_places=2, 可选 | 费用 |
| location | ForeignKey | SET_NULL, 可选 | 关联地点 |
| title | CharField | max_length=200 | 事件标题 |
| description | TextField | blank=True | 事件描述 |
| notes | TextField | blank=True | 备注 |
| created_at | DateTimeField | auto_now_add=True | 创建时间 |
| updated_at | DateTimeField | auto_now=True | 更新时间 |

**事件类型枚举**:
```python
EVENT_TYPES = [
    ('activity', '活动'),
    ('departure', '出发'),
    ('arrival', '到达'),
    ('checkin', '入住'),
    ('checkout', '退房'),
    ('stay', '住宿'),
]
```

**特殊特性**:
- 使用 `InheritanceManager` 支持多态查询
- 按日期和时间排序 (`ordering = ['date', 'start_time']`)
- 软删除地点关联 (`SET_NULL`)

---

### 3. Activity 模型 (活动类)

**用途**: 继承自 Event，专门处理旅行中的各种活动。

**额外字段**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| category | CharField | max_length=20, choices=CATEGORY_CHOICES | 活动分类 |

**活动分类枚举**:
```python
CATEGORY_CHOICES = [
    ('sightseeing', '游览'),
    ('dining', '餐饮'),
    ('transport', '交通'),
    ('rest', '休息'),
    ('free', '自由活动'),
    ('custom', '自定义'),
]
```

**自动行为**:
- 保存时自动设置 `type = 'activity'`

---

### 4. Transport 模型 (交通类)

**用途**: 继承自 Event，处理交通相关的事件。

**额外字段**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| mode | CharField | max_length=20, choices=MODE_CHOICES | 交通方式 |
| destination | ForeignKey | SET_NULL, related_name='transport_destinations' | 目的地 |

**交通方式枚举**:
```python
MODE_CHOICES = [
    ('fly', '飞机'),
    ('train', '火车'),
    ('bus', '大巴'),
    ('metro', '地铁'),
    ('taxi', '出租'),
    ('car', '自驾'),
    ('other', '其他'),
]
```

**设计特点**:
- 支持出发地和目的地的双重地点关联
- 默认类型为 'departure'，可手动指定为 'arrival'

---

### 5. Accommodation 模型 (住宿类)

**用途**: 继承自 Event，处理住宿相关的事件。

**额外字段**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| linked_accommodation | ForeignKey | 自引用, SET_NULL, related_name='related_accommodations' | 关联住宿事件 |

**设计特点**:
- 自引用外键支持入住/退房事件关联
- 默认类型为 'stay'，可指定为 'checkin' 或 'checkout'
- 支持复杂的住宿业务逻辑

---

### 6. Location 模型 (地点表)

**用途**: 存储旅行中涉及的所有地理位置信息。

**字段详情**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| name | CharField | max_length=200 | 地点名称 |
| address | CharField | max_length=300, blank=True | 详细地址 |
| latitude | DecimalField | max_digits=9, decimal_places=6, 可选 | 纬度坐标 |
| longitude | DecimalField | max_digits=9, decimal_places=6, 可选 | 经度坐标 |
| category | CharField | max_length=20, choices=CATEGORY_CHOICES | 地点分类 |
| phone | CharField | max_length=50, blank=True | 联系电话 |
| notes | TextField | blank=True | 备注信息 |
| created_at | DateTimeField | auto_now_add=True | 创建时间 |
| updated_at | DateTimeField | auto_now=True | 更新时间 |

**地点分类枚举**:
```python
CATEGORY_CHOICES = [
    ('sight', '景点'),
    ('hotel', '酒店'),
    ('restaurant', '餐厅'),
    ('transport', '交通枢纽'),
    ('custom', '自定义'),
]
```

**设计亮点**:
- 支持精确的地理坐标存储
- 分类管理便于筛选和展示
- 独立于具体旅行的通用地点库

---

### 7. Day 模型 (天数表)

**用途**: 管理旅行的日程安排，提供天数级别的组织结构。

**字段详情**:

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| trip | ForeignKey | CASCADE, related_name='days' | 所属旅行 |
| date | DateField | 必填 | 具体日期 |
| day_index | PositiveIntegerField | 必填 | 天数索引 (第几天) |
| notes | TextField | blank=True | 当日备注 |

**约束设计**:
```python
unique_together = (('trip', 'day_index'), ('trip', 'date'))
ordering = ['trip', 'day_index']
```

**设计特点**:
- 双重唯一约束确保数据一致性
- 支持非连续日期的旅行安排
- 便于按天组织和查询事件

---

## 关系图谱

### 数据库关系
```
User (Django 内置)
  ↓ (1:N)
Trip
  ↓ (1:N)
  ├── Event
  │   ├── Activity
  │   ├── Transport ──→ Location (destination)
  │   └── Accommodation ──→ self (linked_accommodation)
  ├── Day
  └── ──→ Location (多个 Event 可共享 Location)
```

### 继承关系
```
Event (abstract base)
  ├── Activity (concrete)
  ├── Transport (concrete)
  └── Accommodation (concrete)
```

## 核心设计原则

### 1. 模型继承策略
- **基类设计**: Event 作为抽象基类，包含所有事件的通用字段
- **具体子类**: Activity、Transport、Accommodation 扩展特定业务逻辑
- **多态支持**: 使用 InheritanceManager 实现运行时类型识别

### 2. 关系设计原则
- **级联删除**: Trip 删除时自动清理相关 Event 和 Day
- **软删除**: Location 删除时，Event 中的地点引用设为 NULL
- **自引用**: Accommodation 支持入住/退房事件关联

### 3. 数据完整性
- **唯一约束**: Day 模型确保日期和索引的一致性
- **枚举选择**: 使用 choices 限制字段值的合法范围
- **时间管理**: 自动记录创建和更新时间

### 4. 扩展性考虑
- **分类系统**: Event 和 Location 都支持分类扩展
- **自定义字段**: notes 和 description 提供灵活的文本存储
- **坐标支持**: Location 支持地理信息系统集成

## 使用示例

### 创建完整旅行
```python
# 创建旅行
trip = Trip.objects.create(
    user=user,
    title="北京3日游",
    start_date="2024-01-01",
    end_date="2024-01-03"
)

# 创建地点
location = Location.objects.create(
    name="天安门广场",
    category="sight",
    latitude=39.9042,
    longitude=116.4074
)

# 创建活动
activity = Activity.objects.create(
    trip=trip,
    title="参观天安门",
    date="2024-01-01",
    start_time="09:00",
    category="sightseeing",
    location=location
)
```

### 复杂查询示例
```python
# 查询某个旅行的所有活动类事件
activities = Activity.objects.filter(trip=trip)

# 查询某个地点的所有相关事件
events = Event.objects.filter(location=location).select_subclasses()

# 按天组织事件
from collections import defaultdict
events_by_day = defaultdict(list)
for event in trip.events.all():
    events_by_day[event.date].append(event)
```

## 总结

该模型设计充分考虑了旅行规划的复杂性和多样性，通过合理的继承关系和外键设计，实现了数据的有效组织和管理。主要优势包括：

1. **灵活性**: 模型继承支持不同类型事件的特殊需求
2. **完整性**: 多层次约束确保数据一致性
3. **扩展性**: 预留了分类和自定义字段的扩展空间
4. **性能**: 合理的索引和查询优化设计

该设计为旅行规划应用提供了坚实的数据基础，能够支撑复杂的业务逻辑和用户需求。 