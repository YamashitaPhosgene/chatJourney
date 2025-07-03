# Hunter TypeResolver 使用指南

## 概述

`hunter_typeresolver.py` 是一个升级版的POI分类码解析器，支持多种匹配策略，具有高性能和易扩展性。

## 功能特性

### 1. 多层匹配策略
- **A. 数据库别名表**: 自定义同义词 → 官方code
- **B. 精确匹配字典**: 常用词快速匹配
- **C. 官方分类名精确匹配**: 从高德官方分类表匹配
- **D. SequenceMatcher模糊匹配**: 相似度 > 0.70 #改用句向量
- **E. Dynamic Probe**: 调用高德API动态探测

### 2. 性能优化
- **LRU缓存**: 4096个缓存项，高并发低延迟
- **内存预加载**: 官方分类名一次性加载到内存
- **批量处理**: 支持兴趣词列表批量解析

### 3. 易扩展性
- Django Admin管理界面
- 支持动态添加别名
- 缓存清理和重载功能

## 使用方法

### 1. 基本使用

```python
from hunter.services.hunter_typeresolver import (
    resolve_typecode, 
    interest_to_typecodes,
    search_poi_by_keywords
)

# 单个关键词解析
code = resolve_typecode("小笼包")
print(code)  # 输出: 050118

# 兴趣词列表解析
keywords = ["小笼包", "Citywalk", "老字号小吃"]
types_param = interest_to_typecodes(keywords)
print(types_param)  # 输出: 050116|050118|110000

# 直接搜索POI
result = search_poi_by_keywords(
    keywords="小笼包",
    region="310000",  # 上海
    page_size=10
)
```

### 2. 与高德API集成

```python
from hunter.api.amap_api import AmapPlaceAPI

place_api = AmapPlaceAPI(key=settings.AMAP_KEY)

# 解析关键词到分类码
interest_words = ["小笼包", "Citywalk", "老字号小吃"]
types_param = interest_to_typecodes(interest_words)

# 使用分类码搜索
data = place_api.text_search(
    keywords="小笼包",
    types=types_param,
    region="310000",
    city_limit=True
)
```

### 3. 获取分类信息

```python
from hunter.services.hunter_typeresolver import get_poi_category_info

# 根据分类码获取详细信息
info = get_poi_category_info("050118")
print(info)
# 输出: {
#     "code": "050118",
#     "big_cn": "餐饮服务",
#     "mid_cn": "中餐厅",
#     "sub_cn": "特色/地方风味餐厅",
#     "big_en": "Food & Beverage",
#     "mid_en": "Chinese Restaurant",
#     "sub_en": "Specialty/Local Cuisine"
# }
```

## 管理功能

### 1. Django Admin管理

访问 Django Admin 可以管理：
- **POI分类**: 查看和编辑官方分类表
- **POI关键词别名**: 添加自定义同义词

### 2. 缓存管理

```python
from hunter.services.hunter_typeresolver import clear_cache, reload_official_names

# 清空LRU缓存
clear_cache()

# 重新加载官方分类名到内存
reload_official_names()
```

## 扩展和维护

### 1. 添加新别名

**方法一: Django Admin**
1. 访问 Django Admin → POI关键词别名
2. 点击"添加POI关键词别名"
3. 填写别名和对应的分类码

**方法二: 代码添加**
```python
from hunter.models import POIKeywordAlias

# 添加新别名
POIKeywordAlias.objects.create(
    alias="city walk",
    code="110000"
)
```

### 2. 更新官方分类表

```bash
# 重新导入Excel文件
python manage.py import_poi_types --file="高德POI分类与编码（中英文）_V1.06_20230208.xlsx" --truncate

# 重载到内存
python manage.py shell -c "from hunter.services.hunter_typeresolver import reload_official_names; reload_official_names()"
```

### 3. 自定义精确匹配字典

在 `hunter/services/hunter_typeresolver.py` 中修改 `EXACT_DICT`：

```python
EXACT_DICT = {
    # 添加新的精确匹配项
    "新关键词": "分类码",
    # ... 其他项
}
```

## 性能说明

### 1. 缓存策略
- **LRU缓存**: 最多缓存4096个关键词解析结果
- **内存预加载**: 官方分类名在模块加载时一次性读取
- **数据库索引**: 别名表建有索引，查询速度快

### 2. 匹配优先级
1. 数据库别名表 (最快)
2. 精确匹配字典 (很快)
3. 官方分类名精确匹配 (快)
4. SequenceMatcher模糊匹配 (中等)
5. Dynamic Probe API调用 (最慢，仅在前4层都miss时)

### 3. 并发性能
- 支持高并发访问
- LRU缓存保证热点数据快速响应
- 异常处理确保单个失败不影响整体

## 测试

运行测试脚本验证功能：

```bash
python test_typeresolver.py
```

## 注意事项

1. **API调用限制**: Dynamic Probe会调用高德API，注意调用频率限制
2. **内存使用**: 官方分类名预加载到内存，约占用几MB内存
3. **数据库依赖**: 别名表需要数据库连接，建议配置连接池
4. **缓存一致性**: 修改别名表后需要清空缓存或重启服务

## 故障排除

### 1. 解析失败
- 检查数据库连接
- 确认官方分类表已导入
- 查看日志中的错误信息

### 2. 性能问题
- 检查缓存命中率
- 考虑增加精确匹配字典
- 优化数据库查询

### 3. API调用失败
- 检查高德API密钥配置
- 确认网络连接正常
- 查看API调用频率限制 