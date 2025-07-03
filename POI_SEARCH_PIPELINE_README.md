# POI 搜索管道使用指南

## 概述

`POISearchPipeline` 是一个完整的POI搜索管道服务，将「大模型关键词生成 → 高德POI查询」的四步流程打通，并集成了项目中已有的 `talker.services.poi_keywords_service` 和 `hunter_typeresolver`。

## 功能特性

### 1. 四步流程
- **Step 1**: 调用LLM生成关键词JSON (使用 `talker.services.poi_keywords_service`)
- **Step 2**: 根据 `location_keywords` → `adcode` (AmapDistrictAPI)
- **Step 3**: `interest_keywords` → `typecode` (hunter_typeresolver)
- **Step 4**: `keywords+typecode+adcode` → AmapPlaceAPI.text_search()

### 2. 集成优势
- 使用项目中已有的POI关键词生成服务
- 复用升级版的hunter_typeresolver
- 完整的错误处理和日志记录
- 灵活的输入方式（对话历史或直接关键词）

### 3. 返回结构
```json
{
  "query": {...LLM 输出...},
  "adcode": "110108",
  "types": "050118|050000",
  "pois": {
      "小笼包": [ {name, location, ...}, ... ],
      "外滩": [ {name, location, ...}, ... ]
  }
}
```

## 使用方法

### 1. 基本使用

```python
from hunter.services.poi_search_pipeline import POISearchPipeline

# 创建管道实例
pipeline = POISearchPipeline()

# 对话历史
conversation = [
    {"role": "user", "content": "我想去上海玩，主要是想体验本帮菜和小笼包"},
    {"role": "assistant", "content": "好的，还有别的想法吗？"},
    {"role": "user", "content": "想在外滩看夜景，然后去南京路购物"},
]

# 执行搜索
result = pipeline.run(conversation)

# 查看结果
print("行政区划代码:", result["adcode"])
print("POI分类码:", result["types"])
print("POI数量:", sum(len(poi_list) for poi_list in result["pois"].values()))
```

### 2. 使用会话信息

```python
# 提供会话信息以增强LLM上下文
session_info = {
    "locations": "上海",
    "budget": "5000元",
    "start_date": "2024-01-01",
    "end_date": "2024-01-03",
    "user_profile": {"同行人员": "情侣", "旅行风格": "美食文化"}
}

result = pipeline.run(conversation, session_info)
```

### 3. 直接使用关键词

```python
# 如果已经得到LLM生成的关键词，可以直接使用
keywords = {
    "primary_keywords": ["小笼包", "外滩"],
    "location_keywords": ["上海"],
    "interest_keywords": ["美食", "景点"],
    "search_suggestions": ["上海小笼包", "外滩夜景"]
}

result = pipeline.search_by_keywords(keywords)
```

### 4. 便捷方法

```python
# 根据对话历史搜索（便捷方法）
result = pipeline.search_by_conversation(conversation, session_info)

# 获取搜索结果摘要
summary = pipeline.get_search_summary(result)
print(f"总POI数量: {summary['total_pois']}")
print(f"成功率: {summary['success_rate']:.1%}")
```

## 详细API说明

### POISearchPipeline 类

#### 初始化
```python
pipeline = POISearchPipeline(amap_key=None)
```
- `amap_key`: 高德API密钥，默认从 `settings.AMAP_KEY` 获取

#### 主要方法

##### run()
```python
def run(
    self,
    conversation: List[Dict[str, str]],
    session_info: Dict[str, Any] = None,
    llm_keywords: Dict[str, Any] = None,
) -> Dict[str, Any]
```

**参数:**
- `conversation`: 用户与AI的对话历史 (role/user/assistant结构)
- `session_info`: 会话信息，用于LLM上下文
- `llm_keywords`: 如果已经得到大模型JSON，可直接传入，跳过Step-1

**返回:**
```json
{
  "query": {
    "primary_keywords": ["小笼包", "外滩"],
    "location_keywords": ["上海"],
    "interest_keywords": ["美食", "景点"],
    "search_suggestions": ["上海小笼包", "外滩夜景"]
  },
  "adcode": "310000",
  "types": "050118|110000",
  "pois": {
    "小笼包": [
      {
        "name": "鼎泰丰(新天地店)",
        "address": "上海市黄浦区新天地",
        "typecode": "050118",
        "location": "121.123456,31.123456"
      }
    ],
    "外滩": [...]
  }
}
```

##### search_by_conversation()
```python
def search_by_conversation(
    self, 
    conversation: List[Dict[str, str]], 
    session_info: Dict[str, Any] = None
) -> Dict[str, Any]
```
根据对话历史搜索POI的便捷方法。

##### search_by_keywords()
```python
def search_by_keywords(self, keywords: Dict[str, Any]) -> Dict[str, Any]
```
根据已生成的关键词搜索POI的便捷方法。

##### get_search_summary()
```python
def get_search_summary(self, result: Dict[str, Any]) -> Dict[str, Any]
```
获取搜索结果摘要。

**返回:**
```json
{
  "total_pois": 25,
  "success_rate": 0.8,
  "keyword_results": {
    "小笼包": {
      "total": 10,
      "valid": 10,
      "sample_names": ["鼎泰丰", "南翔馒头店", "老正兴菜馆"]
    },
    "外滩": {
      "total": 15,
      "valid": 10,
      "sample_names": ["外滩", "外滩观光平台", "外滩历史建筑群"]
    }
  }
}
```

## 内部流程详解

### Step 1: LLM关键词生成
- 使用 `talker.services.poi_keywords_service._generate_keywords()`
- 调用 `generate_poi_keywords` prompt
- 返回结构化的关键词JSON

### Step 2: 地名解析
- 遍历 `location_keywords`
- 调用 `AmapDistrictAPI.query()` 获取adcode
- 返回第一个匹配的行政区划代码

### Step 3: 兴趣词解析
- 使用 `hunter_typeresolver.interest_to_typecodes()`
- 多层匹配策略：别名表 → 精确字典 → 官方分类 → 模糊匹配 → API探测
- 返回用`|`分隔的分类码字符串

### Step 4: POI搜索
- 遍历 `primary_keywords`
- 调用 `AmapPlaceAPI.text_search()`
- 应用 `types` 和 `adcode` 过滤
- 返回每个关键词的POI列表

## 错误处理

### 1. API调用失败
- 自动跳过失败的API调用
- 记录详细错误日志
- 返回错误信息而不是崩溃

### 2. LLM生成失败
- 返回默认的空关键词结构
- 继续执行后续步骤
- 记录错误日志

### 3. 数据解析失败
- 使用备用解析方案
- 返回部分结果
- 保持服务稳定性

## 性能优化

### 1. 缓存机制
- 复用 `hunter_typeresolver` 的LRU缓存
- 减少重复的API调用
- 提高响应速度

### 2. 批量处理
- 一次性处理多个关键词
- 减少网络请求次数
- 提高整体效率

### 3. 异步支持
- 可以集成异步处理
- 支持并发搜索
- 适合高并发场景

## 测试

运行测试脚本验证功能：

```bash
python test_poi_pipeline.py
```

测试内容包括：
- 完整的四步流程测试
- 直接关键词搜索测试
- 错误处理测试
- 结果摘要生成测试

## 集成示例

### 在Django View中使用

```python
from django.http import JsonResponse
from hunter.services.poi_search_pipeline import POISearchPipeline

def search_poi_view(request):
    conversation = request.POST.get('conversation', [])
    session_info = request.POST.get('session_info', {})
    
    pipeline = POISearchPipeline()
    result = pipeline.run(conversation, session_info)
    
    return JsonResponse(result)
```

### 在Celery任务中使用

```python
from celery import shared_task
from hunter.services.poi_search_pipeline import POISearchPipeline

@shared_task
def search_poi_task(conversation, session_info):
    pipeline = POISearchPipeline()
    result = pipeline.run(conversation, session_info)
    
    # 处理结果...
    return result
```

## 注意事项

1. **API密钥配置**: 确保 `settings.AMAP_KEY` 已正确配置
2. **网络连接**: 需要稳定的网络连接访问高德API
3. **调用频率**: 注意高德API的调用频率限制
4. **数据质量**: LLM生成的关键词质量影响最终搜索结果
5. **错误处理**: 建议在生产环境中添加更详细的错误处理

## 扩展建议

1. **缓存优化**: 可以添加Redis缓存存储搜索结果
2. **异步处理**: 对于大量搜索可以使用Celery异步处理
3. **结果排序**: 可以根据相关性对搜索结果进行排序
4. **个性化推荐**: 结合用户画像进行个性化POI推荐
5. **多语言支持**: 扩展支持多语言关键词解析 