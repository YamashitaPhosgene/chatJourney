# Timeline服务文档

## 📋 概述

Timeline服务是一个智能行程链生成服务，专为ChatJourney项目设计，用于替换状态机中show_plan阶段的route_time_service。该服务通过6个阶段的流水线处理，生成完整的旅行行程链，专门用于前端行程部分的灵感拼图渲染。

## 🏗️ 架构设计

### 核心文件
- **主服务**: `talker/services/timeline_service.py`
- **状态机集成**: `talker/services/state_machine.py`
- **配置文件**: `talker/config/prompts.yaml`

### 设计原则
- ✅ **不保存数据库**: 最终结果不保存到数据库，直接用于前端渲染
- ✅ **6阶段流水线**: 严格按照业务逻辑分阶段处理
- ✅ **地理聚类**: 基于DBSCAN算法的智能POI聚类
- ✅ **错误处理**: 完善的错误处理和降级机制
- ✅ **流式支持**: 支持普通和流式两种调用方式

## 🔄 6阶段流水线

### Stage 1: 用户画像整合 (Profile Consolidation)
**目标**: 从TalkSession中提取用户信息，生成自然语言描述和推荐聚类半径

**输入**:
```python
collected_slots_with_official_names = {
    "collected_slots": {
        "locations": ["青羊宫", "锦里古街"],
        "budget": "2000",
        "dates": {"start_date": "2025-08-10", "end_date": "2025-08-12"},
        "user_profile": {"情感状态": ["放松"], "旅行风格": ["文化深度游"]}
    },
    "official_poi_names": ["青羊宫", "锦里古街", "宽窄巷子"]
}
```

**输出**:
```python
{
    "user_profile_text": "这是一位28岁的女性学生，计划于2025年8月10日至12日独自前往成都旅行...",
    "radius_km": "2-4"
}
```

### Stage 1.5: 地理聚类 (Geographic Clustering)
**目标**: 对POI进行地理聚类，生成每日游览地点组

**算法**: DBSCAN + Haversine距离计算
- 自适应半径调节
- 目标聚类数量: 2-5个
- 支持单POI场景

**输入**:
```python
pois = [
    {"name": "青羊宫", "lng": 104.0451, "lat": 30.6605},
    {"name": "锦里古街", "lng": 104.0590, "lat": 30.6540},
    {"name": "宽窄巷子", "lng": 104.0610, "lat": 30.6620}
]
radius_km_text = "2-4"
```

**输出**:
```python
clusters = [
    {
        "id": 1,
        "centroid": "104.055033,30.658833",
        "places": ["青羊宫", "杜甫草堂"]
    },
    {
        "id": 2,
        "centroid": "104.060000,30.658000",
        "places": ["锦里古街", "宽窄巷子"]
    }
]
```

### Stage 2: 旅行草案生成 (Itinerary Drafting)
**目标**: 基于用户画像和地理聚类，生成初步行程草案

**Prompt**: `itinerary_drafting`

**输入**:
- 用户画像文本
- 格式化的聚类信息

**输出**: 自然语言的行程草案文本

### Stage 3: 结构化行程评审 (Itinerary Review)
**目标**: 对行程草案进行结构化评审，识别问题

**Prompt**: `itinerary_review_structured`

**输出**: 结构化的评审反馈

### Stage 3.5: 草案修订生成 (Itinerary Revision)
**目标**: 基于评审反馈修订行程草案

**Prompt**: `itinerary_revision`

**输出**: 修订后的行程草案

### Stage 4: 链式结构生成 (Chain Generation)
**目标**: 生成结构化的行程链数据

**Prompt**: `itinerary_chain_generation`

**输出**:
```python
[
    {
        "day": "Day 1",
        "activities": [
            {
                "time": "上午",
                "activity": "参观青羊宫",
                "location": "青羊宫",
                "description": "体验道教文化"
            }
        ]
    }
]
```

## 📖 使用方法

### 基本使用

```python
from talker.services.timeline_service import TimelineService
from talker.models import TalkSession

# 初始化服务
timeline_service = TimelineService()

# 生成完整行程链
session = TalkSession.objects.get(id=session_id)
result = timeline_service.generate_timeline(session)

if result['success']:
    # 获取格式化显示文本
    display_text = timeline_service.format_timeline_for_display(result)
    
    # 获取结构化行程链
    itinerary_chain = timeline_service.get_timeline_chain(result)
    
    print(display_text)
else:
    print(f"生成失败: {result['error']}")
```

### 在状态机中使用

```python
from talker.services.state_machine import TalkStateMachine

# 普通调用
state_machine = TalkStateMachine(session)
result = state_machine.show_plan()

# 流式调用
for chunk in state_machine.show_plan_stream():
    print(chunk)
```

### 分阶段调用

```python
# Stage 1: 用户画像整合
profile_data = timeline_service._stage_1_profile_consolidation(session)

# Stage 1.5: 地理聚类
clusters = timeline_service._stage_1_5_geographic_clustering(session, profile_data['radius_km'])

# Stage 2: 旅行草案生成
daily_itinerary = timeline_service._stage_2_itinerary_drafting(
    profile_data['user_profile_text'], 
    clusters
)

# ... 其他阶段
```

## ⚙️ 配置说明

### 必需的Prompts配置

在`talker/config/prompts.yaml`中需要配置以下prompts:

```yaml
profile_consolidation:
  template: |
    基于以下用户信息，生成用户画像和推荐聚类半径:
    {collected_slots_with_official_names}
    
    请返回JSON格式:
    {
      "user_profile_text": "用户画像描述",
      "radius_km": "推荐半径范围"
    }

itinerary_drafting:
  template: |
    基于用户画像和地点分组，生成旅行草案:
    用户画像: {user_profile_text}
    地点分组: {daily_place_groups}

itinerary_review_structured:
  template: |
    对以下行程进行结构化评审:
    用户画像: {user_profile_text}
    行程内容: {daily_itinerary}

itinerary_revision:
  template: |
    基于评审意见修订行程:
    用户画像: {user_profile_text}
    原始行程: {original_itinerary}
    评审反馈: {review_feedback}

itinerary_chain_generation:
  template: |
    将以下行程转换为结构化JSON:
    {confirmed_itinerary}
    
    返回格式:
    [
      {
        "day": "Day 1",
        "activities": [...]
      }
    ]
```

### 地理聚类参数

```python
# 可调整的参数
target_min = 2      # 最小聚类数量
target_max = 5      # 最大聚类数量  
max_iter = 5        # 最大迭代次数
```

## 🔧 数据模型

### TalkSession字段要求

```python
class TalkSession(models.Model):
    locations = models.JSONField(default=list)         # 地点列表
    budget = models.CharField(max_length=50)           # 预算
    start_date = models.DateField()                    # 开始日期
    end_date = models.DateField()                      # 结束日期
    user_profile = models.JSONField(default=dict)      # 用户画像
```

### POI数据结构

```python
class POIItem(models.Model):
    poi_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)  # 格式: "lng,lat"
    
class POISession(models.Model):
    session = models.ForeignKey(TalkSession)
    poi = models.ForeignKey(POIItem)
    source = models.CharField(max_length=20)
```

## 🔍 返回数据格式

### 完整Timeline数据

```python
{
    "success": True,
    "user_profile_text": "用户画像描述",
    "radius_km": "2-4",
    "clusters": [...],
    "daily_itinerary": "草案文本",
    "review_feedback": "评审反馈",
    "revised_itinerary": "修订后草案",
    "itinerary_chain": [...],
    "final_text": "最终显示文本"
}
```

### 地理聚类结果

```python
[
    {
        "id": 1,
        "centroid": "104.055033,30.658833",
        "places": ["青羊宫", "杜甫草堂"]
    }
]
```

### 行程链结构

```python
[
    {
        "day": "Day 1",
        "activities": [
            {
                "time": "上午",
                "activity": "参观青羊宫",
                "location": "青羊宫",
                "description": "体验道教文化"
            }
        ]
    }
]
```

## 📊 性能指标

### 地理聚类性能
- **算法**: DBSCAN + Haversine距离
- **时间复杂度**: O(n²) 其中n为POI数量
- **空间复杂度**: O(n)
- **推荐POI数量**: 3-20个

### 聚类半径参考
- **市区游**: 1-3 km
- **城际游**: 3-8 km  
- **跨城游**: 8-20 km

## 🚨 错误处理

### 常见错误场景

1. **无POI数据**
   ```python
   # 自动从locations创建模拟坐标
   if not pois and session.locations:
       for i, dest in enumerate(locations):
           pois.append({
               'name': str(dest),
               'lng': 104.06 + i * 0.01,
               'lat': 30.67 + i * 0.01
           })
   ```

2. **AI服务调用失败**
   ```python
   # 返回默认值
   return {
       "user_profile_text": "用户计划进行一次旅行，希望体验当地文化和美食。",
       "radius_km": "3-5"
   }
   ```

3. **聚类失败**
   ```python
   # 返回单个聚类
   return [{
       "id": 1,
       "centroid": f"{pois[0]['lng']:.6f},{pois[0]['lat']:.6f}",
       "places": [poi['name'] for poi in pois]
   }]
   ```

## 🧪 测试

### 单元测试

```python
def test_geographic_clustering():
    service = TimelineService()
    pois = [
        {"name": "青羊宫", "lng": 104.0451, "lat": 30.6605},
        {"name": "锦里古街", "lng": 104.0590, "lat": 30.6540}
    ]
    
    clusters = service._cluster_pois_stage_1_5(pois, "2-4")
    assert len(clusters) >= 1
    assert all('places' in c for c in clusters)
```

### 集成测试

```python
def test_full_timeline_generation():
    service = TimelineService()
    session = create_test_session()
    
    result = service.generate_timeline(session)
    
    assert result['success'] == True
    assert 'final_text' in result
    assert 'itinerary_chain' in result
```

## 🔧 故障排查

### 常见问题

1. **聚类结果异常**
   - 检查POI坐标格式是否正确
   - 调整target_min/target_max参数
   - 验证半径单位是否为千米

2. **AI调用失败**
   - 检查prompts.yaml配置
   - 验证模板变量名称
   - 查看ChatService连接状态

3. **数据格式错误**
   - 检查TalkSession字段名称
   - 验证POI数据结构
   - 确认JSON格式正确

### 日志分析

```python
import logging

# 查看Timeline服务日志
logger = logging.getLogger('talker.services.timeline_service')
logger.setLevel(logging.DEBUG)

# 关键日志信息
# - "用户画像整合完成"
# - "地理聚类完成，生成X个聚类"
# - "链式结构生成完成，生成X天行程"
```

## 🚀 部署建议

### 依赖检查

```bash
# 确保以下依赖已安装
pip install scikit-learn numpy django

# 验证依赖
python -c "from sklearn.cluster import DBSCAN; print('✅ scikit-learn OK')"
python -c "import numpy; print('✅ numpy OK')"
```

### 性能优化

1. **POI数量控制**: 建议单次处理POI数量不超过50个
2. **缓存机制**: 考虑缓存地理聚类结果
3. **异步处理**: 对于大量POI，考虑异步处理

### 监控指标

- Timeline生成成功率
- 各阶段处理时间
- 聚类算法性能
- AI服务调用延迟

## 📝 版本历史

### v1.0.0 (2025-01-28)
- ✅ 实现完整的6阶段流水线
- ✅ 集成DBSCAN地理聚类算法
- ✅ 支持普通和流式调用
- ✅ 完善的错误处理机制
- ✅ 与状态机完全集成

## 🤝 贡献指南

1. 新增功能请遵循现有的6阶段架构
2. 修改聚类算法需要充分测试
3. 更新配置文件需要同步更新文档
4. 提交前请运行完整测试套件

## 📞 支持

如有问题或建议，请提交Issue或联系开发团队。

---

*Timeline服务 - 为ChatJourney提供智能行程链生成能力* 