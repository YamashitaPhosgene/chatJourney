# 小红书内容总结 API 文档

## 概述

小红书内容总结API是一个智能服务，能够自动搜索小红书笔记、提取关键信息，并生成结构化的内容总结。该API结合了HunterAPI的内容获取能力和ChatService的AI分析能力。

**重要说明**: 总结服务直接使用HunterAPI的接口，不重复初始化浏览器服务。HunterAPI的初始化和关闭应该独立管理。

## 功能特点

- 🔍 **智能搜索**: 根据关键词搜索相关小红书笔记
- 📝 **内容提取**: 自动获取笔记详细内容和用户评论
- 🤖 **AI总结**: 使用大语言模型生成专业的内容分析
- 🎯 **分类总结**: 支持美食、旅行、购物、美妆等不同领域的专业总结
- 📊 **结构化输出**: 提供完整的笔记数据和AI总结报告

## API 端点

### 内容总结

**POST** `/api/talker/xhs/summary/`

搜索关键词并生成内容总结。

**请求参数:**
```json
{
    "keyword": "三里屯 咖啡",
    "limit": 5,
    "summary_type": "food"
}
```

**参数说明:**
- `keyword` (必需): 搜索关键词
- `limit` (可选): 搜索笔记数量限制，默认5
- `summary_type` (可选): 总结类型，默认"general"
  - `general`: 通用总结
  - `food`: 美食总结
  - `travel`: 旅行总结
  - `shopping`: 购物总结
  - `beauty`: 美妆总结

**响应示例:**
```json
{
    "keyword": "三里屯 咖啡",
    "summary": "基于小红书用户分享，三里屯咖啡店整体评价如下：\n\n1. 推荐度最高的咖啡店：\n- %店名%：用户评价环境优雅，咖啡品质上乘\n- %店名%：性价比高，适合日常消费\n\n2. 价格区间：\n- 精品咖啡：35-60元/杯\n- 普通咖啡：20-35元/杯\n\n3. 热门推荐：\n- 手冲咖啡\n- 拿铁系列\n- 特色甜点\n\n4. 用户评价：\n- 优点：环境好、服务周到、咖啡品质稳定\n- 缺点：部分店铺价格偏高、周末人流量大\n\n5. 用餐建议：\n- 最佳时间：工作日午后\n- 适合人群：情侣约会、朋友聚会、商务洽谈",
    "notes_count": 5,
    "notes": [
        {
            "title": "三里屯必打卡的咖啡店",
            "author": "咖啡达人",
            "likes": 1234,
            "content": "今天给大家推荐三里屯一家超棒的咖啡店...",
            "comments": [
                {
                    "content": "环境真的很棒！",
                    "author": "用户A",
                    "likes": 12
                }
            ]
        }
    ]
}
```

## 使用流程

### 1. 初始化HunterAPI（必需）
在使用总结API之前，需要先初始化HunterAPI：

```bash
POST /api/hunter/xhs/login/
```

### 2. 搜索并总结
```bash
POST /api/talker/xhs/summary/
Content-Type: application/json

{
    "keyword": "三里屯 咖啡",
    "limit": 5,
    "summary_type": "food"
}
```

### 3. 关闭HunterAPI（可选）
使用完毕后可以关闭HunterAPI：

```bash
POST /api/hunter/xhs/shutdown/
```

## 使用示例

### Python 示例

```python
import requests
import json

# 1. 初始化HunterAPI
init_response = requests.post('http://localhost:8000/api/hunter/xhs/login/')
print("HunterAPI初始化结果:", init_response.json())

# 2. 搜索并总结
summary_data = {
    "keyword": "三里屯 咖啡",
    "limit": 5,
    "summary_type": "food"
}

summary_response = requests.post(
    'http://localhost:8000/api/talker/xhs/summary/',
    json=summary_data
)

result = summary_response.json()
print("总结结果:", result['summary'])

# 3. 关闭HunterAPI（可选）
shutdown_response = requests.post('http://localhost:8000/api/hunter/xhs/shutdown/')
print("关闭结果:", shutdown_response.json())
```

### cURL 示例

```bash
# 初始化HunterAPI
curl -X POST http://localhost:8000/api/hunter/xhs/login/

# 搜索并总结
curl -X POST http://localhost:8000/api/talker/xhs/summary/ \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "三里屯 咖啡",
    "limit": 5,
    "summary_type": "food"
  }'

# 关闭HunterAPI（可选）
curl -X POST http://localhost:8000/api/hunter/xhs/shutdown/
```

## 总结类型说明

### 1. 通用总结 (general)
适用于各种类型的内容，提供全面的分析：
- 用户关注点和热门话题
- 主要观点和评价
- 优缺点和争议点
- 实用建议和洞察

### 2. 美食总结 (food)
专门针对美食相关内容：
- 推荐度最高的餐厅/美食
- 口味特点和价格区间
- 热门菜品和避雷建议
- 用餐建议（时间、人数、预算等）
- 用户整体评价和情感倾向

### 3. 旅行总结 (travel)
专门针对旅行相关内容：
- 最佳游玩时间和季节
- 必去景点和推荐路线
- 住宿和交通建议
- 预算参考和消费水平
- 用户体验和注意事项

### 4. 购物总结 (shopping)
专门针对购物相关内容：
- 推荐度最高的商品/品牌
- 价格区间和性价比
- 购买渠道和优惠信息
- 购买建议和注意事项
- 用户满意度评价

### 5. 美妆总结 (beauty)
专门针对美妆相关内容：
- 推荐度最高的产品/品牌
- 适用肤质和使用效果
- 价格区间和购买渠道
- 使用建议和注意事项
- 用户真实体验评价

## 错误处理

API 返回的错误格式：

```json
{
    "success": false,
    "error": "错误描述"
}
```

常见错误：
- `关键词不能为空`: 搜索关键词为空
- `总结类型必须是以下之一: general, food, travel, shopping, beauty`: 总结类型无效
- `HunterAPI状态检查失败`: HunterAPI未正确初始化
- `搜索失败`: 搜索过程中出现错误

## 注意事项

1. **HunterAPI依赖**: 使用总结API前必须先初始化HunterAPI
2. **资源管理**: HunterAPI的初始化和关闭应该独立管理
3. **请求频率**: 避免过于频繁的请求，建议间隔适当时间
4. **数据限制**: 单次搜索建议不超过10条笔记，避免响应时间过长
5. **网络环境**: 确保网络连接稳定，避免请求超时

## 测试工具

项目提供了测试脚本 `test_xiaohongshu_summary.py`，可以用于测试API功能：

```bash
python test_xiaohongshu_summary.py
```

测试脚本会自动检查HunterAPI状态，并在需要时进行初始化。

## 技术架构

该API基于以下技术栈构建：
- **Django**: Web框架
- **HunterAPI**: 小红书内容获取
- **ChatService**: AI内容分析
- **Playwright**: 浏览器自动化
- **VivoGPT**: 大语言模型服务

## 架构说明

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django API    │    │  HunterAPI      │    │  ChatService    │
│   (REST接口)    │◄──►│  (内容获取)     │◄──►│  (AI分析)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Xiaohongshu   │    │   Playwright    │    │   VivoGPT       │
│   Summary API   │    │   (浏览器自动化) │    │   (大语言模型)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

总结服务直接使用HunterAPI的接口，不重复初始化浏览器服务，确保资源的高效利用。 