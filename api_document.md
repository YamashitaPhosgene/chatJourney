# ChatJourney RESTful API 文档

> 所有接口统一前缀：`/api/v1`，所有请求/响应均为 `application/json`。
> 
> 会话上下文通过 `session_id` 标识，强烈建议前端每次请求都带上 session_id。

---

## 一、对话管理（Chat Sessions）

| 功能         | 方法   | 路径                                               | 请求示例 Body                | 响应示例                      | 描述 |
|--------------|--------|----------------------------------------------------|------------------------------|-------------------------------|------|
| 创建新会话   | POST   | /api/v1/chat/sessions/                             | { "user_id": "u123" }      | { "session_id": "abc123", "created_at": "2025-07-02T11:00Z" } | 初始化 FSM，返回新会话 ID |
| 加载会话     | POST   | /api/v1/chat/sessions/{session_id}/load/           | {}                           | { "loaded": true, "session_info": { … } } | 从持久层加载对话上下文 |
| 获取会话信息 | GET    | /api/v1/chat/sessions/{session_id}/info/           | —                            | { "session_id":"…", "user":"…", "current_state":"…", "slots":{…} } | 返回会话基本属性、当前状态、已填槽位等 |
| 发送消息     | POST   | /api/v1/chat/sessions/{session_id}/message/        | { "text": "我想去成都看看" } | { "message_id":"m1", "role":"assistant", "text":"好的，您想什么时候出发？" } | 将用户话语送入 FSM，返回助手回复 |
| 拉取历史     | GET    | /api/v1/chat/sessions/{session_id}/history/        | —                            | { "messages":[{"role":"user","text":"…"},{"role":"assistant","text":"…"},…]} | 返回本会话从创建以来的所有消息列表 |
| 获取状态     | GET    | /api/v1/chat/sessions/{session_id}/status/         | —                            | { "current_state":"ASK_DESTINATION" } | 仅返回 FSM 当前状态标识 |
| 获取槽位     | GET    | /api/v1/chat/sessions/{session_id}/slots/          | —                            | { "destination":true, "start_date":false, … } | 返回各个业务槽位是否已填及已填值（若有） |
| 保存会话     | POST   | /api/v1/chat/sessions/{session_id}/save/           | {}                           | { "saved": true }            | 强制将内存会话写入数据库或持久层 |
| 删除会话     | DELETE | /api/v1/chat/sessions/{session_id}/                | —                            | { "deleted": true }          | 清理内存和持久层中该会话数据 |

---

## 二、POI 关键词与搜索（POI Management）

| 功能         | 方法   | 路径                                                                 | 请求示例 Query / Body         | 响应示例                      | 描述 |
|--------------|--------|----------------------------------------------------------------------|-------------------------------|-------------------------------|------|
| 获取POI关键词 | GET    | /api/v1/chat/sessions/{session_id}/poi/keywords/                    | —                             | { "primary_keywords":[…], "secondary_keywords":[…], … } | 调用 FSM 关键词回调，返回所有分类的关键词 |
| 搜索POI      | GET    | /api/v1/chat/sessions/{session_id}/poi/search/                       | ?page=1&page_size=4           | { "page":1, "total_pages":3, "total":10, "pois":[{"id":"...","name":"…"},…] } | 按页返回合并去重后的 POI 列表 |
| POI详情      | GET    | /api/v1/chat/sessions/{session_id}/poi/search/{index}/detail/        | —                             | { "id":"B001C07VJ2","name":"成都武侯祠博物馆","address":"…", … } | 根据上次搜索结果中的序号 index ，返回全部字段 |
| 列出POI      | GET    | /api/v1/chat/sessions/{session_id}/poi/                              | —                             | [{"poi_id":12,"name":"…","source":"manual","address":"…",…},…] | 返回所有已保存到数据库的 POI |
| 添加POI      | POST   | /api/v1/chat/sessions/{session_id}/poi/                              | { "poi_data":{…}, "source":"keyword_search" } | { "added": true, "poi_id": 12 } | 将某条搜索结果或任意 POI 对象保存到数据库 |
| 删除POI      | DELETE | /api/v1/chat/sessions/{session_id}/poi/{poi_id}/                     | —                             | { "deleted": true }          | 从数据库移除指定 poi_id |

---

## 三、流式接口（可选）

| 功能         | 方法   | 路径                                               | 请求头/说明                  | 响应格式                      | 描述 |
|--------------|--------|----------------------------------------------------|------------------------------|-------------------------------|------|
| SSE流式回复  | GET    | /api/v1/chat/sessions/{session_id}/stream/         | Accept: text/event-stream    | event: message\ndata: {"chunk":"…"}\n… | 用于前端"边生成边显示"打字机效果 |

---

## 四、接口通用说明

### 1. 状态一致性
- 所有会话操作必须走同一 session_id，后台用内存或 Redis 保持 FSM 实例和 POI 缓存。

### 2. 错误处理
- 统一返回 `{ "error": "描述信息" }` 并设置合适的 HTTP 状态码。
- 例如：
  ```json
  { "error": "会话不存在" }
  ```

### 3. 分页参数
- `page`、`page_size` 均可通过 query string 指定，默认 `page=1`，`page_size=4`。

### 4. 认证与限流
- 推荐 JWT/Cookie 认证，所有接口需认证。
- 建议接口加限流防刷。

### 5. 示例：发送消息

**请求**
```http
POST /api/v1/chat/sessions/abc123/message/
Content-Type: application/json

{
  "text": "我想去成都看看"
}
```

**响应**
```json
{
  "message_id": "m1",
  "role": "assistant",
  "text": "好的，您想什么时候出发？"
}
```

---

## 五、接口变更与维护
- 如需扩展业务字段、支持更多 POI 维度、或增加新功能，请在此文档补充说明。
- 建议前后端约定好 session_id、POI 数据结构等关键字段。

---

如需详细字段定义、业务流程图或 OpenAPI/Swagger 规范，请联系后端开发。 