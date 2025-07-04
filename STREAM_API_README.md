# 流式接口实现说明

## 概述

本项目已成功实现流式接口，支持前端打字机效果和实时响应。流式接口基于 SSE（Server-Sent Events）协议，实现了从大模型到前端的完整流式数据传递。

## 架构设计

### 数据流向
```
前端/CLI → StateMachine → ChatService → VivoGPT API → 流式响应
```

### 核心组件

1. **VivoGPT API 客户端** (`talker/api/client.py`)
   - 支持流式请求和响应解析
   - 兼容同步和流式两种模式

2. **ChatService** (`talker/services/chat_service.py`)
   - 添加 `stream` 参数支持流式处理
   - 保持向后兼容性

3. **StateMachine** (`talker/services/state_machine.py`)
   - 为每个动作函数添加流式版本（`*_stream`）
   - 实现 `handle_utterance_stream` 统一流式入口

4. **视图接口** (`talker/views.py`)
   - `StateMachineView`: 状态机流式接口
   - `ChatStreamView`: 直接聊天流式接口
   - `SessionView`: 会话管理接口

5. **CLI服务** (`talker/services/cli_service.py`)
   - 支持流式和同步模式切换
   - 实时显示打字机效果

## API 接口

### 1. 状态机流式接口

**URL**: `POST /talker/state-machine/`

**请求体**:
```json
{
    "session_id": "会话ID",
    "message": "用户消息",
    "stream": true
}
```

**响应格式** (SSE):
```
data: {"type": "content", "chunk": "望", "full_content": "望"}

data: {"type": "content", "chunk": "庐", "full_content": "望庐"}

data: {"type": "content", "chunk": "山", "full_content": "望庐山"}

data: {"type": "done", "full_content": "望庐山瀑布，飞流直下三千尺"}

event: close
data: [DONE]
```

### 2. 直接聊天流式接口

**URL**: `POST /talker/chat/stream/`

**请求体**:
```json
{
    "message": "写一首春天的诗",
    "chat_type": "poem",
    "temperature": 0.7,
    "max_tokens": 500
}
```

**响应格式** (SSE):
```
data: {"message": "春"}

data: {"message": "天"}

data: {"message": "来"}

data: {"message": "了"}

event: close
data: [DONE]
```

### 3. 会话管理接口

**创建会话**: `POST /talker/session/`
```json
{
    "username": "用户名"
}
```

**获取会话信息**: `GET /talker/session/{session_id}/`

## 使用方法

### 前端使用示例

```javascript
// 状态机流式接口
function sendMessageStream(sessionId, message) {
    const eventSource = new EventSource(`/talker/state-machine/`);
    
    fetch('/talker/state-machine/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            message: message,
            stream: true
        })
    }).then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        function readStream() {
            reader.read().then(({done, value}) => {
                if (done) return;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'content') {
                                // 显示打字机效果
                                appendToChat(data.chunk);
                            } else if (data.type === 'done') {
                                // 完成
                                console.log('完成:', data.full_content);
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                });
                
                readStream();
            });
        }
        
        readStream();
    });
}
```

### CLI 使用示例

```bash
# 启动CLI服务
python run_cli.py

# 切换流式模式
/stream

# 发送消息（流式显示）
我想去成都旅游

# 切换回同步模式
/stream

# 发送消息（同步显示）
预算5000元
```

## 测试

### 1. API 测试

```bash
# 测试流式接口
python test_stream_api.py

# 测试CLI流式功能
python test_cli_stream.py

# 对比流式和同步模式
python test_cli_stream.py compare
```

### 2. 手动测试

1. 启动Django服务器
2. 使用Postman或curl测试流式接口
3. 运行CLI服务测试流式模式

## 技术特点

### 1. 向后兼容
- 所有现有接口保持兼容
- 通过 `stream` 参数控制模式
- 默认使用同步模式

### 2. 错误处理
- 流式处理失败时自动降级到同步模式
- 完整的错误信息传递
- 优雅的异常处理

### 3. 性能优化
- 实时响应，无需等待完整回复
- 支持长文本流式输出
- 内存使用优化

### 4. 状态管理
- 流式输出完成后自动保存到历史记录
- 状态机状态正确更新
- POI搜索等后台任务正常执行

## 注意事项

1. **网络连接**: 流式接口需要保持长连接，确保网络稳定
2. **超时处理**: 建议设置合理的超时时间
3. **错误重试**: 流式处理失败时建议重试
4. **浏览器兼容**: 确保浏览器支持 EventSource 或 fetch API

## 故障排除

### 常见问题

1. **流式接口无响应**
   - 检查网络连接
   - 确认API密钥配置
   - 查看服务器日志

2. **流式内容不完整**
   - 检查SSE解析逻辑
   - 确认事件处理正确
   - 验证数据格式

3. **CLI流式模式异常**
   - 检查Django环境配置
   - 确认依赖包版本
   - 查看错误日志

### 调试方法

1. 启用调试模式
2. 查看详细日志
3. 使用测试脚本验证
4. 检查网络请求

## 总结

流式接口的实现完全满足了需求：
- ✅ 前端支持打字机效果
- ✅ StateMachine 支持流式响应
- ✅ 大模型通信支持流式接口
- ✅ 保持向后兼容性
- ✅ CLI 支持流式模式
- ✅ 完整的错误处理
- ✅ 详细的文档和测试

所有功能都已实现并经过测试，可以投入生产使用。 