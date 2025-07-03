# 双循环搜索功能说明

## 概述

双循环搜索功能将原来的"大锅烩"查询拆分为「关键词 × 兴趣类别」的两层循环，既能提高命中率，也能把结果天然地"分门别类"。

## 功能特点

### 1. 精准匹配
- **单一分类码**：每次搜索只使用一个typecode，匹配更精确
- **分类映射**：兴趣关键词自动映射到对应的POI分类码
- **结果分组**：搜索结果按分类码自然分组

### 2. 提高命中率
- **精确搜索**：关键词与分类码一一对应，减少无关结果
- **分类覆盖**：覆盖多个相关分类，提高召回率
- **智能过滤**：只保存非空结果，避免无效数据

### 3. 结构化展示
- **分层显示**：关键词 → 分类码 → POI列表
- **分类统计**：按分类统计POI数量
- **用户友好**：结果一目了然，便于用户选择

## 核心组件

### 1. 分类码映射构建
```python
def build_code_map(int_keywords: List[str]) -> Dict[str, List[str]]:
    """
    构建兴趣关键词到分类码的映射
    
    示例：
    输入: ["川菜", "小笼包", "道教圣地"]
    输出: {
        "050100": ["川菜", "小笼包"],  # 小吃快餐
        "110205": ["道教圣地"]        # 道观景点
    }
    """
```

### 2. 双循环搜索
```python
def search_by_kw_and_code(
    self, 
    primary_keywords: List[str], 
    code_map: Dict[str, List[str]], 
    adcode: str | None = None,
    *, 
    avoid_keywords: List[str] | None = None
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    双循环搜索：关键词 × 兴趣类别
    
    返回结构：
    {
        "青羊宫": {
            "050100": [poi1, poi2, ...],  # 小吃快餐
            "110205": [poi3, poi4, ...]   # 道观景点
        },
        "宽窄巷子": {
            "050600": [poi5, poi6, ...]   # 茶馆咖啡
        }
    }
    """
```

## 使用方法

### 基本使用

```python
from hunter.services.poi_search_pipeline import POISearchPipeline

# 创建管道实例
pipeline = POISearchPipeline(qps_limit=5)

# 对话搜索（自动使用双循环）
conversation = [
    {"role": "user", "content": "我想去成都青羊宫玩，主要是想体验当地美食和道教文化"},
    {"role": "user", "content": "我想吃川菜和小笼包，但是我不吃火锅"},
]

result = pipeline.run(conversation)
```

### 直接关键词搜索

```python
# 直接提供关键词
keywords = {
    "primary_keywords": ["青羊宫", "宽窄巷子"],
    "location_keywords": ["成都"],
    "interest_keywords": ["川菜", "道教圣地", "茶馆"],
    "avoid_keywords": ["火锅"],
    "search_suggestions": ["成都青羊宫美食"]
}

result = pipeline.search_by_keywords(keywords)
```

### 手动双循环搜索

```python
# 手动构建分类码映射
primary_keywords = ["青羊宫", "宽窄巷子"]
code_map = {
    "050100": ["川菜", "小笼包"],  # 小吃快餐
    "110205": ["道教圣地"],       # 道观景点
    "050600": ["茶馆", "咖啡"]     # 茶馆咖啡
}

result = pipeline.search_by_kw_and_code(
    primary_keywords, 
    code_map, 
    adcode="510100",  # 成都
    avoid_keywords=["火锅"]
)
```

## 结果结构

### 新的数据结构
```python
{
    "query": {
        "primary_keywords": ["青羊宫"],
        "interest_keywords": ["川菜", "道教圣地"],
        "avoid_keywords": ["火锅"],
        # ...
    },
    "adcode": "510100",
    "code_map": {
        "050100": ["川菜", "小笼包"],
        "110205": ["道教圣地"]
    },
    "pois": {
        "青羊宫": {
            "050100": [
                {"name": "龙抄手(青羊宫店)", "address": "...", "typecode": "050100"},
                {"name": "钟水饺(西御街店)", "address": "...", "typecode": "050100"}
            ],
            "110205": [
                {"name": "青羊宫", "address": "...", "typecode": "110205"},
                {"name": "三清殿", "address": "...", "typecode": "110205"}
            ]
        }
    }
}
```

### CLI显示效果
```
📍 青羊宫
  ▸ 050100 (川菜)
      1. 龙抄手(青羊宫店)
          地址: 青羊区青羊宫街123号
          类型: 050100
      2. 钟水饺(西御街店)
          地址: 青羊区西御街456号
          类型: 050100
  ▸ 110205 (道教圣地)
      1. 青羊宫
          地址: 青羊区青羊宫街1号
          类型: 110205
      2. 三清殿
          地址: 青羊区青羊宫街2号
          类型: 110205

📈 搜索摘要:
  总POI数量: 4
  成功率: 100.0%

📋 关键词结果统计:
  青羊宫: 4/4 个有效结果
    川菜: 2 个
    道教圣地: 2 个

🏷️  分类统计:
  川菜: 2 个POI
  道教圣地: 2 个POI
```

## 性能优化

### 1. QPS控制
- 每个API调用都有QPS控制
- 自动等待，避免超限
- 可配置QPS限制

### 2. 结果过滤
- 只保存非空结果
- 自动过滤避雷关键词
- 减少无效数据

### 3. 缓存友好
- 分类码映射可以缓存
- 支持增量更新
- 减少重复计算

## 与旧版本对比

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| 搜索方式 | 单次携带多个typecode | 关键词 × 分类码双循环 |
| 结果结构 | 扁平列表 | 分层嵌套 |
| 命中精度 | 较低（混合分类） | 较高（单一分类） |
| 展示效果 | 难区分类别 | 按类别分组 |
| API调用 | 较少 | 较多但精确 |
| 扩展性 | 难以统计 | 天然支持统计 |

## 最佳实践

### 1. 合理设置QPS
```python
# 根据API配额设置
pipeline = POISearchPipeline(qps_limit=3)  # 生产环境
```

### 2. 优化关键词
```python
# 减少不必要的关键词
keywords = {
    "primary_keywords": ["青羊宫"],  # 主要地点
    "interest_keywords": ["川菜", "道教圣地"],  # 核心兴趣
    # ...
}
```

### 3. 利用分类统计
```python
# 获取分类统计信息
summary = pipeline.get_search_summary(result)
for code, stats in summary["category_results"].items():
    print(f"{stats['name']}: {stats['valid']} 个POI")
```

## 故障排除

### 常见问题

1. **分类码映射为空**
   - 检查兴趣关键词是否正确
   - 确认typeresolver配置
   - 查看日志输出

2. **搜索结果为空**
   - 检查adcode是否正确
   - 确认关键词有效性
   - 查看API配额

3. **QPS超限**
   - 降低QPS限制
   - 增加请求间隔
   - 考虑缓存机制

### 调试模式

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 查看详细的搜索日志
pipeline = POISearchPipeline(qps_limit=5)
result = pipeline.run(conversation)
```

## 更新日志

- **v2.0**：实现双循环搜索功能
- **v2.1**：添加分类码映射构建
- **v2.2**：优化结果展示和统计
- **v2.3**：集成QPS控制和错误处理 