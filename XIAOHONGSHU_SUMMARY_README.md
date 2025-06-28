# 小红书内容总结 API 实现

## 项目概述

本项目实现了一个智能的小红书内容总结API，能够自动搜索小红书笔记、提取关键信息，并使用AI生成结构化的内容总结。该API结合了HunterAPI的内容获取能力和ChatService的AI分析能力。

## 核心功能

### 🔍 智能内容获取
- 基于关键词搜索小红书笔记
- 自动提取笔记详细内容和用户评论
- 支持批量处理多条笔记

### 🤖 AI智能总结
- 使用大语言模型生成专业内容分析
- 支持多种总结类型（美食、旅行、购物、美妆、通用）
- 提供结构化的总结报告

### 📊 分类总结
- **美食总结**: 餐厅推荐、口味特点、价格区间、用餐建议
- **旅行总结**: 景点推荐、路线规划、住宿交通、预算参考
- **购物总结**: 商品推荐、价格分析、购买渠道、注意事项
- **美妆总结**: 产品推荐、使用效果、购买建议、真实体验
- **通用总结**: 全面分析、观点总结、优缺点识别

## 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django API    │    │  HunterAPI      │    │TalkerChatService│
│   (REST接口)    │◄──►│  (内容获取)      │◄──►│    (AI分析)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Xiaohongshu   │    │   Playwright    │    │   VivoGPT       │
│   Summary API   │    │   (浏览器自动化) │    │   (大语言模型)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 文件结构

```
chatJourney/
├── talker/
│   ├── services/
│   │   ├── xiaohongshu_summary_service.py  # 核心总结服务
│   │   └── chat_service.py                 # AI聊天服务
│   ├── views.py                            # API视图
│   └── urls.py                             # URL路由
├── hunter/
│   ├── api/
│   │   └── hunter_api.py                   # 小红书内容获取API
│   └── services/
│       └── xiaohongshu_service.py          # 小红书服务
├── test_xiaohongshu_summary.py             # 测试脚本
├── example_xiaohongshu_summary.py          # 使用示例
├── XIAOHONGSHU_SUMMARY_API.md              # API文档
├── XiaohongshuSummary.postman_collection.json  # Postman集合
└── XIAOHONGSHU_SUMMARY_README.md           # 本文件
```

## 核心组件

### 1. XiaohongshuSummaryService
**文件**: `talker/services/xiaohongshu_summary_service.py`

核心服务类，负责：
- 初始化HunterAPI和ChatService
- 协调内容获取和AI总结流程
- 提供统一的API接口

**主要方法**:
```python
async def initialize() -> Dict[str, Any]
async def search_and_summarize(keyword: str, limit: int, summary_type: str) -> Dict[str, Any]
async def shutdown() -> Dict[str, Any]
```

### 2. API视图
**文件**: `talker/views.py`

提供REST API接口：
- `xiaohongshu_init()`: 初始化服务
- `xiaohongshu_summary()`: 搜索并总结内容
- `xiaohongshu_shutdown()`: 关闭服务

### 3. URL配置
**文件**: `talker/urls.py` 和 `chatJourney/urls.py`

API路由配置：
- `/api/talker/xhs/init/`: 初始化
- `/api/talker/xhs/summary/`: 内容总结
- `/api/talker/xhs/shutdown/`: 关闭服务

## API使用流程

### 1. 初始化服务
```bash
POST /api/talker/xhs/init/
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

### 3. 关闭服务
```bash
POST /api/talker/xhs/shutdown/
```

## 使用示例

### Python代码示例
```python
import asyncio
from talker.services.xiaohongshu_summary_service import summary_service

async def main():
    # 1. 初始化
    await summary_service.initialize()
    
    # 2. 搜索总结
    result = await summary_service.search_and_summarize(
        keyword="三里屯 咖啡",
        limit=5,
        summary_type="food"
    )
    
    if result["success"]:
        print(result["data"]["summary"])
    
    # 3. 关闭
    await summary_service.shutdown()

asyncio.run(main())
```

### cURL示例
```bash
# 初始化
curl -X POST http://localhost:8000/api/talker/xhs/init/

# 搜索总结
curl -X POST http://localhost:8000/api/talker/xhs/summary/ \
  -H "Content-Type: application/json" \
  -d '{"keyword": "三里屯 咖啡", "limit": 5, "summary_type": "food"}'

# 关闭
curl -X POST http://localhost:8000/api/talker/xhs/shutdown/
```

## 测试工具

### 1. 自动化测试脚本
```bash
python test_xiaohongshu_summary.py
```

### 2. 交互式示例
```bash
python example_xiaohongshu_summary.py
```

### 3. Postman集合
导入 `XiaohongshuSummary.postman_collection.json` 到Postman进行API测试。

## 配置要求

### 环境依赖
- Python 3.8+
- Django 4.2+
- Playwright (浏览器自动化)
- VivoGPT (大语言模型服务)

### 配置步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 配置VivoGPT服务
3. 启动Django服务: `python manage.py runserver`
4. 运行测试脚本验证功能

## 总结类型详解

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

API提供完善的错误处理机制：
- 参数验证错误
- 服务初始化错误
- 网络连接错误
- AI服务错误

所有错误都返回标准化的JSON格式：
```json
{
    "success": false,
    "error": "错误描述"
}
```

## 性能优化

### 1. 并发处理
- 异步处理多个笔记内容获取
- 并行处理评论数据

### 2. 缓存机制
- 浏览器会话复用
- 登录状态保持

### 3. 资源管理
- 自动关闭浏览器实例
- 内存使用优化

## 扩展性

### 1. 新增总结类型
在 `XiaohongshuSummaryService` 中添加新的总结模板方法。

### 2. 自定义提示词
修改 `_build_summary_prompt` 方法支持自定义提示词。

### 3. 多平台支持
可以扩展支持其他内容平台（如微博、抖音等）。

## 注意事项

1. **初始化顺序**: 使用总结API前必须先调用初始化接口
2. **资源管理**: 使用完毕后建议调用关闭接口释放资源
3. **请求频率**: 避免过于频繁的请求，建议间隔适当时间
4. **数据限制**: 单次搜索建议不超过10条笔记，避免响应时间过长
5. **网络环境**: 确保网络连接稳定，避免请求超时

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 参与讨论

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和平台使用条款。 