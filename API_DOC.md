# ChatJourney 前端可调用 API 文档

## 1. 用户与会话相关

### 1.1 获取会话列表
- **接口**：`GET /api/talk_sessions/`
- **说明**：获取当前用户的所有会话
- **返回示例**：
```json
[
  {
    "id": 1,
    "user": 2,
    "history": [...],
    "budget": 5000.00,
    "locations": ["北京", "颐和园"],
    "start_date": "2024-05-01",
    "end_date": "2024-05-05",
    "created_at": "2024-04-01T12:00:00Z",
    "updated_at": "2024-04-01T12:00:00Z"
  }
]
```

### 1.2 获取单个会话详情
- **接口**：`GET /api/talk_sessions/{session_id}/`
- **说明**：获取指定会话的详细信息

### 1.3 删除会话
- **接口**：`DELETE /api/talk_sessions/{session_id}/`
- **说明**：删除指定会话

### 1.4 发送对话消息（自动拼接历史）
- **接口**：`POST /api/talk_sessions/{session_id}/chat/`
- **请求体**：
```json
{
  "message": "我还想去颐和园"
}
```
- **返回示例**：
```json
{
  "reply": "颐和园是北京著名景点，建议您...",
  "history": [
    {"role": "user", "content": "我想去北京旅游"},
    {"role": "assistant", "content": "请问您的预算和出行时间？"},
    {"role": "user", "content": "预算5000元，5月1日到5月5日"},
    {"role": "assistant", "content": "好的，以下是推荐行程..."},
    {"role": "user", "content": "我还想去颐和园"},
    {"role": "assistant", "content": "颐和园是北京著名景点，建议您..."}
  ]
}
```

### 1.5 删除会话历史中的一条消息
- **接口**：`POST /api/talk_sessions/{session_id}/remove_history/`
- **请求体**：
```json
{
  "index": 3
}
```
- **返回示例**：
```json
{
  "history": [ ... ]
}
```

---

## 2. 行程（Trip）相关

### 2.1 获取行程列表
- **接口**：`GET /api/trips/`

### 2.2 获取行程详情（含所有事件）
- **接口**：`GET /api/trips/{trip_id}/`

### 2.3 获取行程时间线
- **接口**：`GET /api/trips/{trip_id}/timeline/`
- **说明**：获取整个行程的事件时间线

### 2.4 获取行程某一天的时间线
- **接口**：`GET /api/trips/{trip_id}/timeline/{day_index}/`
- **说明**：获取指定天数的事件时间线

---

## 3. 事件（Event）相关

### 3.1 获取事件列表
- **接口**：`GET /api/events/`

### 3.2 获取单个事件详情
- **接口**：`GET /api/events/{event_id}/`

### 3.3 删除事件
- **接口**：`DELETE /api/events/{event_id}/`

---

## 4. 地点（Location）相关

### 4.1 获取地点列表
- **接口**：`GET /api/locations/`

### 4.2 获取单个地点详情
- **接口**：`GET /api/locations/{location_id}/`

### 4.3 删除地点
- **接口**：`DELETE /api/locations/{location_id}/`

---

## 5. 其他说明
- 所有接口均需认证（Token 或 Session）。
- 所有时间均为 ISO 格式。
- 所有 POST/DELETE 请求需带上正确的 session_id 或相关主键。
- 如需更多接口或参数说明，请联系后端开发。 