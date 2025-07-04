# 旅行助手 CLI/状态机驱动 API 设计草案

---

## 1. 会话管理

### 1.1 创建/恢复会话
- **POST `/api/session/`**
  - 创建新会话，或用用户名恢复历史会话。
  - **参数**：
    ```json
    { "username": "可选，用户名" }
    ```
  - **返回**：
    ```json
    { "session_id": "...", ... }
    ```

### 1.2 加载会话
- **GET `/api/session/<session_id>/`**
  - 加载指定会话，返回当前槽位、历史、状态等。
  - **返回**：
    ```json
    { "session_info": {...}, "slots": {...}, "state": "...", ... }
    ```

---

## 2. 多轮对话与槽位推进

### 2.1 用户输入/AI回复（同步）
- **POST `/api/message/`**
  - 用户输入一句话，自动推进状态机，返回AI回复和当前槽位/状态。
  - **参数**：
    ```json
    { "session_id": "...", "message": "..." }
    ```
  - **返回**：
    ```json
    { "reply": "...", "slots": {...}, "state": "...", "history": [...] }
    ```

### 2.2 用户输入/AI回复（流式）
- **POST `/api/message/stream/`**
  - 同上，但AI回复为流式（SSE/WebSocket），适合大模型长回复。
  - **参数**：同上
  - **返回**：流式数据块，每块如
    ```json
    { "message": "...", "full_content": "..." }
    ```

---

## 3. 槽位/状态/历史查询

### 3.1 查询当前槽位
- **GET `/api/session/<session_id>/slots/`**
  - 返回当前所有槽位（destination, budget, dates, profile等）及其填充情况。

### 3.2 查询对话历史
- **GET `/api/session/<session_id>/history/`**
  - 返回完整对话历史（用户+AI）。

### 3.3 查询当前状态
- **GET `/api/session/<session_id>/state/`**
  - 返回当前状态机状态（如SLOT_FILLING_DESTINATION等）。

---

## 4. POI搜索与管理

### 4.1 自动POI搜索（pipeline）
- **POST `/api/poi/search/`**
  - 根据当前会话的对话历史、槽位、用户画像等自动生成关键词并批量搜索POI，用户无需手动输入关键词。
  - **参数**：
    ```json
    { "session_id": "会话ID" }
    ```
  - **返回**：
    ```json
    {
      "success": true,
      "query": {         // pipeline自动生成的关键词、兴趣、城市等
        "primary_keywords": [...],
        "interest_keywords": [...],
        "city_keywords": [...],
        ...
      },
      "adcode": "110105",
      "code_map": { ... }, // 兴趣-类型码映射
      "pois": {            // 结构化分组POI结果
        "美食": {
          "050100": [ { ...POI... }, ... ],
          ...
        },
        ...
      },
      "total": 23
    }
    ```
  - **说明**：
    - 用户只需触发一次POI搜索，pipeline会自动分析对话历史、用户需求、兴趣、城市等，生成最优关键词并批量搜索。
    - 返回结构包含pipeline推理过程（如LLM生成的关键词、兴趣、城市、类型码等），便于前端展示和调试。
    - 支持分页、过滤、收藏等后续操作。

### 4.2 分页浏览POI
- **GET `/api/poi/search/page/?session_id=...&page=2`**
  - 分页返回上次搜索结果。

### 4.3 收藏/添加POI到会话
- **POST `/api/poi/collect/`**
  - 收藏POI到当前会话（如用户选中某POI）。
  - **参数**：
    ```json
    { "session_id": "...", "poi_id": "..." }
    ```
  - **返回**：
    ```json
    { "success": true, ... }
    ```

### 4.4 查询会话POI列表
- **GET `/api/session/<session_id>/pois/`**
  - 返回当前会话已收藏/选中的POI列表。

### 4.5 删除会话POI
- **DELETE `/api/session/<session_id>/pois/<poi_id>/`**
  - 移除某POI。

---

## 5. 行程推荐与保存

### 5.1 行程生成并返回时间线
- **POST `/api/plan/generate/`**
  - 根据当前会话的槽位与对话历史触发状态机 `show_plan` 流程，
    内部调用 `RouteTimeService.save_plan_to_db` 保存 Trip，
    然后使用 `planner.services.trip_service.TripService.generate_timeline` 生成时间线数据。
  - **参数**：
    ```json
    { "session_id": "会话ID" }
    ```
  - **返回**：
    ```json
    {
      "success": true,
      "trip": {
        "trip_id": 123,
        "title": "成都之旅",
        "start_date": "2025-08-01",
        "end_date": "2025-08-03",
        ...
      },
      "timeline": [   // TripService.generate_timeline 的完整结构
        {
          "day_index": 1,
          "date": "2025-08-01",
          "events": [ ... ]
        },
        ...
      ]
    }
    ```

### 5.2 保存当前行程
- **POST `/api/plan/save/`**
  - 保存当前会话的行程（可选自定义标题/备注）。
  - **参数**：
    ```json
    { "session_id": "...", "plan": {...}, "title": "...", "notes": "..." }
    ```

### 5.3 查询历史行程
- **GET `/api/session/<session_id>/plans/`**
  - 返回该会话下所有已保存行程。

### 5.4 查询行程详情
- **GET `/api/plan/<plan_id>/`**
  - 返回单个行程的详细结构。

---

## 6. 其它辅助命令（CLI常用）

### 6.1 查看帮助
- **GET `/api/help/`**
  - 返回所有可用命令及用法说明。

### 6.2 取消/重置会话
- **POST `/api/session/<session_id>/cancel/`**
  - 取消当前会话流程，状态机转为COMPLETED。

---

## 设计说明

- 所有接口都需带`session_id`，保证多会话隔离。
- 所有多轮对话、槽位推进、AI回复、POI搜索、行程推荐等都严格走状态机推进，接口只做"命令式"触发和查询。
- 流式接口建议用SSE或WebSocket，普通接口用RESTful。
- 所有接口返回结构应包含`success`、`message`、`data`或具体业务字段。
- 分页、收藏、历史、帮助、取消等CLI常用命令均有对应API。 