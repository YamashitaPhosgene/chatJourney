# Hunter 独立服务

## 启动服务
```bash
python -m hunter.startup.hunter_server
```

## 在其他模块中调用
```python
from hunter.api.hunter_api import HunterAPI

api = HunterAPI()
# 完整初始化（启动浏览器+登录）
await api.initialize()
result = await api.search_notes("关键词", 5)
```

## 主要接口
- `initialize()` - 完整初始化（启动浏览器+登录）
- `login()` - 单独登录
- `search_notes(keywords, limit)` - 搜索笔记
- `get_note_content(url)` - 获取内容
- `get_status()` - 获取状态 