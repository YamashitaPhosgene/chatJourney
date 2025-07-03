# QPS 控制功能说明

## 概述

为了遵守高德地图API的QPS限制，我们在POI搜索管道中添加了QPS控制机制，确保API调用不会超过限制。

## 功能特点

### 1. 自动QPS控制
- **请求间隔控制**：自动计算请求间隔，确保不超过QPS限制
- **智能等待**：在请求间隔不足时自动等待
- **线程安全**：支持多线程环境下的QPS控制

### 2. 可配置QPS限制
```python
# 初始化时设置QPS限制
pipeline = POISearchPipeline(qps_limit=2)  # 2次/秒（间隔0.5秒）
```

### 3. 监控和日志
- **详细日志**：记录QPS控制等待时间
- **性能监控**：可选的QPS监控工具

## 使用方法

### 基本使用

```python
from hunter.services.poi_search_pipeline import POISearchPipeline

# 创建管道实例，设置QPS限制
pipeline = POISearchPipeline(qps_limit=2)  # 平衡设置

# 正常使用，QPS控制自动生效
result = pipeline.run(conversation)
```

### 状态机集成

在状态机中已经集成了QPS控制：

```python
# talker/services/state_machine.py
self.poi_search_pipeline = POISearchPipeline(qps_limit=2)  # 2次/秒
```

### 监控QPS使用

```python
from qps_monitor import qps_monitor, print_qps_stats

# 查看当前QPS统计
print_qps_stats()
```

## QPS限制说明

### 高德地图API限制
- **免费版**：300次/天，约0.003 QPS
- **标准版**：300,000次/天，约3.5 QPS
- **企业版**：根据合同约定

### 推荐设置
- **开发环境**：`qps_limit=2`（平衡设置）
- **生产环境**：`qps_limit=2`（标准设置）
- **高并发**：`qps_limit=3`（需要确认API配额）

## 性能影响

### 请求延迟
- QPS限制会增加请求间隔
- 每个请求的延迟 = `1 / qps_limit` 秒
- 例如：QPS=2时，每个请求间隔0.5秒

### 总耗时计算
```
总耗时 = 请求数量 × (1 / QPS限制) + 网络延迟
```

### 示例
- 搜索3个关键词，QPS=2
- 理论最小耗时：3 × 0.5 = 1.5秒
- 实际耗时：约2-3秒（包含网络延迟）

## 错误处理

### QPS超限处理
- 自动等待，不会抛出异常
- 记录详细日志
- 确保请求成功执行

### 降级策略
- 如果某个API调用失败，继续处理其他关键词
- 返回部分结果而不是完全失败

### 重试机制
- 检测到QPS超限错误时自动重试
- 额外等待2秒后重试一次
- 记录重试结果

## 紧急处理方案

### 1. 立即降低QPS
```python
# 如果出现QPS超限，立即降低到0.5
pipeline = POISearchPipeline(qps_limit=0.5)  # 2秒间隔
```

### 2. 减少搜索范围
```python
# 减少关键词数量
keywords = {
    "primary_keywords": ["成都"],  # 只搜索一个关键词
    "interest_keywords": ["美食"],  # 只搜索一个分类
    # ...
}
```

### 3. 使用最小化搜索
```python
# 直接使用最小化搜索
result = pipeline.search_by_kw_and_code(
    ["成都"], 
    {"050000": ["美食"]},  # 只搜索餐饮服务
    adcode="510100"
)
```

### 4. 检查API配额
- 登录高德开放平台
- 查看API使用情况
- 确认配额是否充足

## 最佳实践

### 1. 合理设置QPS限制
```python
# 根据API配额设置
if is_production:
    qps_limit = 2  # 生产环境平衡设置
else:
    qps_limit = 2  # 开发环境平衡设置
```

### 2. 监控API使用
```python
# 定期检查QPS使用情况
stats = qps_monitor.get_stats()
if stats['current_qps'] > 0.8 * qps_limit:
    logging.warning("QPS使用率较高")
```

### 3. 优化搜索策略
```python
# 减少不必要的搜索
keywords = {
    "primary_keywords": ["成都"],  # 减少关键词数量
    "interest_keywords": ["美食"],  # 减少分类数量
    # ...
}
```

### 4. 缓存机制
```python
# 考虑添加缓存，减少重复API调用
# 可以缓存adcode、typecode等不常变化的数据
```

## 故障排除

### 常见问题

1. **搜索速度慢**
   - 检查QPS限制是否过低
   - 确认网络连接正常
   - 考虑减少搜索关键词数量

2. **API调用失败**
   - 检查API密钥是否有效
   - 确认API配额是否充足
   - 查看错误日志

3. **QPS超限**
   - 降低QPS限制设置
   - 增加请求间隔
   - 考虑升级API配额

### 调试模式

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 查看详细的QPS控制日志
pipeline = POISearchPipeline(qps_limit=2)
```

### 紧急测试

```bash
# 运行紧急处理测试
python qps_emergency_fix.py
```

## 更新日志

- **v1.0**：基础QPS控制功能
- **v1.1**：添加监控工具
- **v1.2**：优化错误处理和降级策略
- **v1.3**：集成到状态机，添加详细文档
- **v1.4**：紧急处理方案，降低默认QPS限制
- **v1.5**：添加QPS超限重试机制