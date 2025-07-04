# 基于 run_cli 业务流程的 RESTful API 设计

## 概述

本文档描述了基于 `run_cli` 命令行工具业务流程设计的完整 RESTful API。该 API 将 CLI 的所有功能转换为 Web 接口，支持前端应用和移动端调用。

## 设计原则

1. **RESTful 规范**：遵循 REST 架构风格，使用标准 HTTP 方法
2. **统一响应格式**：所有 API 使用统一的成功/错误响应格式
3. **流式支持**：支持同步和流式两种响应模式
4. **会话管理**：完整的会话生命周期管理
5. **POI 集成**：集成 POI 搜索和管理功能
6. **状态机驱动**：基于状态机的对话流程管理

## API 基础信息

- **基础 URL**: `/api/`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`
- **认证方式**: 支持匿名访问（可扩展为 JWT 认证）

## 统一响应格式

### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        // 具体数据
    }
}
```

### 错误响应
```json
{
    "success": false,
    "message": "错误描述",
    "code": "ERROR_CODE",
    "data": null
}
```

## API 端点详细说明

### 1. 会话管理 API

#### 1.1 创建新会话
- **URL**: `POST /api/sessions/`
- **描述**: 创建新的对话会话
- **请求体**:
```json
{
    "username": "fangsuo"  // 可选，默认 fangsuo
}
```
- **响应**:
```json
{
    "success": true,
    "message": "会话创建成功",
    "data": {
        "session_id": "session_123",
        "session_info": {
            "id": 1,
            "user": "fangsuo",
            "created_at": "2024-01-01T00:00:00Z",
            "state": {
                "phase": "init",
                "intent": "start",
                "context": "初始状态"
            }
        }
    }
}
```

#### 1.2 获取会话信息
- **URL**: `GET /api/sessions/{session_id}/`
- **描述**: 获取指定会话的详细信息
- **响应**:
```json
{
    "success": true,
    "message": "获取会话信息成功",
    "data": {
        "session_info": {
            "id": 1,
            "user": "fangsuo",
            "created_at": "2024-01-01T00:00:00Z",
            "state": {...}
        },
        "current_state": "SLOT_FILLING_DESTINATION",
        "slots": {
            "destination": null,
            "budget": null,
            "dates": null,
            "profile": null
        },
        "history": [
            {
                "role": "user",
                "content": "我想去北京旅游",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "role": "assistant",
                "content": "好的，请告诉我您的预算范围？",
                "timestamp": "2024-01-01T00:00:01Z"
            }
        ]
    }
}
```

### 2. 对话交互 API

#### 2.1 发送消息（同步模式）
- **URL**: `POST /api/chat/`
- **描述**: 发送消息并获取同步回复
- **请求体**:
```json
{
    "session_id": "session_123",
    "message": "我想去北京旅游",
    "stream": false
}
```
- **响应**:
```json
{
    "success": true,
    "message": "消息处理成功",
    "data": {
        "response": "好的，请告诉我您的预算范围？",
        "current_state": "SLOT_FILLING_BUDGET",
        "slots": {
            "destination": "北京",
            "budget": null,
            "dates": null,
            "profile": null
        },
        "state_info": {
            "phase": "slot_filling",
            "intent": "fill_budget",
            "context": "等待用户提供预算信息"
        }
    }
}
```

#### 2.2 发送消息（流式模式）
- **URL**: `POST /api/chat/`
- **描述**: 发送消息并获取流式回复（SSE）
- **请求体**:
```json
{
    "session_id": "session_123",
    "message": "我想去北京旅游",
    "stream": true
}
```
- **响应** (Server-Sent Events):
```
data: {"type": "content", "chunk": "好的", "full_content": "好的"}

data: {"type": "content", "chunk": "，", "full_content": "好的，"}

data: {"type": "content", "chunk": "请告诉我您的预算范围？", "full_content": "好的，请告诉我您的预算范围？"}

data: {"type": "done", "full_content": "好的，请告诉我您的预算范围？"}

event: close
data: [DONE]
```

### 3. POI 管理 API

#### 3.1 获取会话 POI 列表
- **URL**: `GET /api/sessions/{session_id}/pois/`
- **描述**: 获取会话中所有 POI 的列表
- **响应**:
```json
{
    "success": true,
    "message": "获取POI列表成功",
    "data": {
        "pois": [
            {
                "id": 1,
                "name": "故宫博物院",
                "address": "北京市东城区景山前街4号",
                "type": "旅游景点",
                "source": "manual",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "statistics": {
            "total": 1,
            "manual": 1,
            "reverse_search": 0,
            "keyword_search": 0
        }
    }
}
```

#### 3.2 添加 POI 到会话
- **URL**: `POST /api/sessions/{session_id}/pois/`
- **描述**: 将 POI 添加到指定会话
- **请求体**:
```json
{
    "poi_data": {
        "name": "故宫博物院",
        "address": "北京市东城区景山前街4号",
        "type": "旅游景点",
        "poi_id": "B0FFJQ1QKJ"
    },
    "source": "manual"
}
```
- **响应**:
```json
{
    "success": true,
    "message": "POI添加成功",
    "data": {
        "poi_id": 1,
        "name": "故宫博物院"
    }
}
```

#### 3.3 从会话删除 POI
- **URL**: `DELETE /api/sessions/{session_id}/pois/{poi_id}/`
- **描述**: 从会话中删除指定 POI
- **响应**:
```json
{
    "success": true,
    "message": "POI删除成功"
}
```

### 4. POI 搜索 API

#### 4.1 POI 搜索
- **URL**: `POST /api/poi/search/`
- **描述**: 搜索 POI 信息
- **请求体**:
```json
{
    "session_id": "session_123",
    "keywords": "故宫",
    "location": "北京",
    "page": 1
}
```
- **响应**:
```json
{
    "success": true,
    "message": "搜索成功",
    "data": {
        "pois": [
            {
                "id": 1,
                "name": "故宫博物院",
                "address": "北京市东城区景山前街4号",
                "type": "旅游景点",
                "distance": "100m",
                "tel": "010-85007421"
            }
        ],
        "total": 10,
        "page": 1,
        "has_next": true
    }
}
```

### 5. 状态查询 API

#### 5.1 获取会话状态
- **URL**: `GET /api/sessions/{session_id}/status/`
- **描述**: 获取当前会话的状态信息
- **响应**:
```json
{
    "success": true,
    "message": "获取状态成功",
    "data": {
        "current_state": "SLOT_FILLING_DESTINATION",
        "state_info": {
            "phase": "slot_filling",
            "intent": "fill_destination",
            "context": "等待用户提供目的地信息"
        },
        "slots": {
            "destination": null,
            "budget": null,
            "dates": null,
            "profile": null
        },
        "next_slot": "destination"
    }
}
```

### 6. 历史记录 API

#### 6.1 获取对话历史
- **URL**: `GET /api/sessions/{session_id}/history/`
- **描述**: 获取会话的对话历史记录
- **响应**:
```json
{
    "success": true,
    "message": "获取历史记录成功",
    "data": {
        "history": [
            {
                "role": "user",
                "content": "我想去北京旅游",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "role": "assistant",
                "content": "好的，请告诉我您的预算范围？",
                "timestamp": "2024-01-01T00:00:01Z"
            }
        ]
    }
}
```

### 7. 命令执行 API

#### 7.1 执行命令
- **URL**: `POST /api/sessions/{session_id}/commands/`
- **描述**: 执行各种命令（对应 CLI 命令）
- **请求体**:
```json
{
    "command": "save",
    "params": {}
}
```
- **响应**:
```json
{
    "success": true,
    "message": "命令执行成功",
    "data": {
        "command": "save",
        "result": "会话保存成功"
    }
}
```

#### 支持的命令列表

| 命令 | 参数 | 描述 |
|------|------|------|
| `save` | 无 | 保存当前会话 |
| `new` | 无 | 创建新会话 |
| `info` | 无 | 显示会话信息 |
| `slots` | 无 | 显示槽位信息 |
| `addpoi` | `{"index": 1}` | 添加POI（按序号） |
| `removepoi` | `{"poi_id": 1}` | 删除POI（按ID） |
| `poi` | `{"poi_id": 1}` | 查看POI详情（按ID） |
| `detail` | `{"index": 1}` | 查看POI详情（按序号） |

## 业务流程映射

### CLI 命令到 API 的映射

| CLI 命令 | API 端点 | HTTP 方法 | 描述 |
|----------|----------|-----------|------|
| `/new` | `/api/sessions/` | POST | 创建新会话 |
| `/load <session_id>` | `/api/sessions/{session_id}/` | GET | 加载会话 |
| `/save` | `/api/sessions/{session_id}/commands/` | POST | 保存会话 |
| `/info` | `/api/sessions/{session_id}/` | GET | 获取会话信息 |
| `/status` | `/api/sessions/{session_id}/status/` | GET | 获取状态 |
| `/slots` | `/api/sessions/{session_id}/status/` | GET | 获取槽位信息 |
| `/history` | `/api/sessions/{session_id}/history/` | GET | 获取历史记录 |
| `/pois` | `/api/sessions/{session_id}/pois/` | GET | 获取POI列表 |
| `/addpoi <index>` | `/api/sessions/{session_id}/commands/` | POST | 添加POI |
| `/removepoi <id>` | `/api/sessions/{session_id}/pois/{poi_id}/` | DELETE | 删除POI |
| `/poi <id>` | `/api/sessions/{session_id}/commands/` | POST | 查看POI详情 |
| `/detail <index>` | `/api/sessions/{session_id}/commands/` | POST | 查看POI详情 |
| 普通消息 | `/api/chat/` | POST | 发送消息 |

### 状态机状态映射

| 状态机状态 | API 状态 | 描述 |
|------------|----------|------|
| `INIT` | `init` | 初始状态 |
| `SLOT_FILLING_DESTINATION` | `slot_filling_destination` | 等待目的地 |
| `SLOT_FILLING_BUDGET` | `slot_filling_budget` | 等待预算 |
| `SLOT_FILLING_DATES` | `slot_filling_dates` | 等待日期 |
| `SLOT_FILLING_PROFILE` | `slot_filling_profile` | 等待用户画像 |
| `CONFIRMATION` | `confirmation` | 确认阶段 |
| `COMPLETED` | `completed` | 完成状态 |
| `ERROR` | `error` | 错误状态 |

## 错误处理

### 常见错误代码

| 错误代码 | HTTP 状态码 | 描述 |
|----------|-------------|------|
| `MISSING_SESSION_ID` | 400 | 缺少会话ID |
| `MISSING_MESSAGE` | 400 | 缺少消息内容 |
| `MISSING_COMMAND` | 400 | 缺少命令 |
| `SESSION_NOT_FOUND` | 404 | 会话不存在 |
| `SESSION_CREATE_ERROR` | 500 | 创建会话失败 |
| `SESSION_GET_ERROR` | 500 | 获取会话失败 |
| `CHAT_ERROR` | 500 | 聊天处理失败 |
| `POI_LIST_ERROR` | 500 | 获取POI列表失败 |
| `POI_ADD_ERROR` | 400/500 | 添加POI失败 |
| `POI_DELETE_ERROR` | 400/500 | 删除POI失败 |
| `POI_SEARCH_ERROR` | 500 | POI搜索失败 |
| `STATUS_ERROR` | 500 | 获取状态失败 |
| `HISTORY_ERROR` | 500 | 获取历史记录失败 |
| `COMMAND_ERROR` | 500 | 命令执行失败 |

## 使用示例

### 完整对话流程示例

```javascript
// 1. 创建新会话
const createSession = async () => {
    const response = await fetch('/api/sessions/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: 'fangsuo'})
    });
    const data = await response.json();
    return data.data.session_id;
};

// 2. 发送消息（同步模式）
const sendMessage = async (sessionId, message) => {
    const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            message: message,
            stream: false
        })
    });
    return await response.json();
};

// 3. 发送消息（流式模式）
const sendMessageStream = async (sessionId, message, onChunk) => {
    const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            message: message,
            stream: true
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
            }
        }
    }
};

// 4. 获取会话状态
const getStatus = async (sessionId) => {
    const response = await fetch(`/api/sessions/${sessionId}/status/`);
    return await response.json();
};

// 5. 添加POI
const addPOI = async (sessionId, poiData) => {
    const response = await fetch(`/api/sessions/${sessionId}/pois/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            poi_data: poiData,
            source: 'manual'
        })
    });
    return await response.json();
};
```

### Python 客户端示例

```python
import requests
import json

class TravelAssistantAPI:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
    
    def create_session(self, username="fangsuo"):
        """创建新会话"""
        response = requests.post(f"{self.base_url}/sessions/", json={
            "username": username
        })
        return response.json()
    
    def send_message(self, session_id, message, stream=False):
        """发送消息"""
        response = requests.post(f"{self.base_url}/chat/", json={
            "session_id": session_id,
            "message": message,
            "stream": stream
        })
        return response.json()
    
    def get_status(self, session_id):
        """获取会话状态"""
        response = requests.get(f"{self.base_url}/sessions/{session_id}/status/")
        return response.json()
    
    def get_pois(self, session_id):
        """获取POI列表"""
        response = requests.get(f"{self.base_url}/sessions/{session_id}/pois/")
        return response.json()
    
    def add_poi(self, session_id, poi_data, source="manual"):
        """添加POI"""
        response = requests.post(f"{self.base_url}/sessions/{session_id}/pois/", json={
            "poi_data": poi_data,
            "source": source
        })
        return response.json()

# 使用示例
api = TravelAssistantAPI()

# 创建会话
session_data = api.create_session()
session_id = session_data['data']['session_id']

# 发送消息
response = api.send_message(session_id, "我想去北京旅游")
print(response['data']['response'])

# 获取状态
status = api.get_status(session_id)
print(f"当前状态: {status['data']['current_state']}")
```

## 部署和配置

### 1. URL 配置

在主项目的 `urls.py` 中添加：

```python
from django.urls import path, include

urlpatterns = [
    # ... 其他 URL 配置
    path('api/', include('talker.api.urls')),
]
```

### 2. 权限配置

默认支持匿名访问，如需认证可修改：

```python
# 在 restful_api.py 中修改
permission_classes = [permissions.IsAuthenticated]
```

### 3. CORS 配置

如需跨域访问，安装并配置 `django-cors-headers`：

```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

CORS_ALLOW_ALL_ORIGINS = True  # 开发环境
```

## 总结

这套 RESTful API 完整地将 `run_cli` 的业务流程转换为 Web 接口，支持：

1. **完整的会话管理**：创建、加载、保存、查询会话
2. **灵活的对话交互**：支持同步和流式两种模式
3. **POI 集成管理**：搜索、添加、删除、查询 POI
4. **状态查询**：实时获取会话状态和槽位信息
5. **历史记录**：完整的对话历史管理
6. **命令执行**：将 CLI 命令转换为 API 调用

API 设计遵循 RESTful 规范，提供统一的响应格式和错误处理，便于前端集成和扩展。 