# ChatJourney 项目

一个基于Django的智能旅行助手系统，集成了聊天机器人、旅行规划和内容采集功能。

## 项目结构

```
chatJourney/
├── chatJourney/          # Django项目配置
├── talker/              # 聊天机器人模块
├── planner/             # 旅行规划模块  
├── hunter/              # 内容采集模块
├── requirements.txt     # 项目依赖
└── manage.py           # Django管理脚本
```

## 功能模块

### 1. Talker (聊天机器人)
- 智能对话系统
- 状态机管理
- 会话控制
- VivoGPT API集成

### 2. Planner (旅行规划)
- 行程管理
- 事件规划
- 活动安排
- 交通住宿

### 3. Hunter (内容采集)
- 小红书内容采集
- 浏览器自动化
- 数据提取

## 安装说明

### 1. 环境要求
- Python 3.8+
- Django 4.2+

### 2. 安装依赖
```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装hunter模块特有依赖
pip install -r hunter/requirements.txt

playwright install

```


### 3. 初始化数据库
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 安装Playwright浏览器
```bash
playwright install chromium
```

### 5. 环境变量配置
创建 `.env` 文件：
```
VIVO_APP_ID=your_vivo_app_id
VIVO_APP_KEY=your_vivo_app_key
```

## 运行项目

### 启动开发服务器
```bash
python manage.py runserver
```

### 访问接口
- 管理后台: http://localhost:8000/admin/
- API文档: http://localhost:8000/api/

## API接口

### 聊天相关
- `POST /api/chat/` - 发送聊天消息
- `GET /api/chat/history/` - 获取聊天历史
- `GET /api/talk_sessions/` - 获取会话列表

### 旅行规划
- `GET /api/trips/` - 获取行程列表
- `POST /api/trips/` - 创建新行程
- `GET /api/events/` - 获取事件列表
- `POST /api/events/` - 创建新事件

### 内容采集 (Hunter)
- `POST /api/hunter/xhs/login/` - 小红书登录
- `POST /api/hunter/xhs/search/` - 搜索笔记
- `POST /api/hunter/xhs/note_content/` - 获取笔记内容
- `POST /api/hunter/xhs/note_comments/` - 获取笔记评论

## 使用示例

### 小红书内容采集
```bash
# 登录小红书
curl -X POST http://localhost:8000/api/hunter/xhs/login/

# 搜索笔记
curl -X POST http://localhost:8000/api/hunter/xhs/search/ \
  -H "Content-Type: application/json" \
  -d '{"keywords": "旅行", "limit": 5}'

# 获取笔记内容
curl -X POST http://localhost:8000/api/hunter/xhs/note_content/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.xiaohongshu.com/..."}'
```

## 注意事项

1. **浏览器数据**: Hunter模块会在 `hunter/browser_data/` 目录下存储浏览器缓存，包含登录状态等敏感信息，请勿上传到公共仓库。

2. **环境变量**: 请确保正确配置 `.env` 文件中的API密钥。

3. **依赖管理**: 项目使用分层依赖管理，核心依赖在根目录 `requirements.txt`，模块特有依赖在各自目录下。

## 开发说明

### 添加新模块
1. 创建Django应用: `python manage.py startapp your_app_name`
2. 在 `settings.py` 中注册应用
3. 在 `urls.py` 中添加路由
4. 创建模块特有的 `requirements.txt`（如需要）

### 代码规范
- 使用Python类型提示
- 遵循Django最佳实践
- 异步操作使用 `asyncio`
- API接口使用RESTful设计

## 许可证

MIT License 