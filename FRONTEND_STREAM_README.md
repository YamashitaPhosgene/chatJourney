# 前端流式接口实现说明

## 概述

本项目为 ChatJourney 前端实现了流式接口功能，提供实时的打字机效果，提升用户体验。

## 技术架构

### 1. 流式请求层 (`src/utils/request.js`)

```javascript
// 主要函数
export function requestStream(url, data, options)
export function requestStreamFallback(url, data, options)
```

**特点：**
- 针对 uni-app 环境优化
- 自动降级到模拟流式（因为 uni-app 不支持真正的 SSE）
- 支持取消操作

### 2. 页面集成 (`src/pages/index/index.vue`)

**新增数据属性：**
```javascript
data() {
  return {
    isStreamMode: true,              // 是否启用流式模式
    streamingMessageIndex: -1,       // 正在流式输出的消息索引
    streamingContent: "",            // 流式输出的累积内容
    streamController: null,          // 流式请求控制器
    // ...
  }
}
```

**核心方法：**
- `_sendToBackendStream()` - 流式发送消息
- `_handleStreamChunk()` - 处理流式数据块
- `_handleStreamDone()` - 处理流式完成
- `_handleStreamError()` - 处理流式错误
- `toggleStreamMode()` - 切换流式/同步模式
- `cancelStreamGeneration()` - 取消流式生成

## 使用方法

### 1. 启用/关闭流式模式

在页面右上角点击"流式"/"同步"按钮切换模式。

### 2. 流式消息显示

流式消息会显示：
- 绿色脉动圆点动画
- "生成中..."文字
- "取消"按钮

### 3. 取消流式生成

点击消息下方的"取消"按钮可以中断流式生成。

## 后端接口对接

### 流式接口 URL
```
POST /api/message/
```

### 请求体
```json
{
  "session_id": "会话ID",
  "message": "用户消息",
  "stream": true
}
```

### 响应格式（模拟流式）
由于 uni-app 限制，前端使用模拟流式：
1. 发送同步请求到后端
2. 获取完整响应
3. 在前端按字符分块显示，模拟打字机效果

## 样式说明

### 流式相关 CSS 类

```scss
.stream-toggle {
  // 导航栏右侧的模式切换按钮
}

.streaming-indicator {
  // 流式状态指示器
  .streaming-dot {
    // 脉动圆点动画
  }
  .streaming-text {
    // "生成中..."文字
  }
  .cancel-stream-btn {
    // 取消按钮
  }
}

.message-footer {
  // 消息底部区域（包含时间和流式状态）
}
```

## 配置参数

### 流式模拟参数
```javascript
const chunkSize = 2;    // 每次显示的字符数
const delay = 30;       // 字符间延迟（毫秒）
```

### 动画参数
```scss
@keyframes pulse {
  // 脉动动画：1.5秒循环
}
```

## 兼容性说明

### uni-app 限制
- uni-app 不支持真正的 Server-Sent Events (SSE)
- 不支持 `fetch` 的流式读取
- 使用模拟流式作为替代方案

### 降级策略
1. 优先尝试流式请求（实际会直接使用模拟流式）
2. 失败时显示错误信息
3. 用户可以手动切换到同步模式

## 开发调试

### 控制台日志
- `收到流式数据块:` - 显示每个数据块的内容
- `uni-app环境，使用模拟流式请求` - 确认使用模拟模式

### 测试步骤
1. 启动前端应用
2. 确保后端服务运行
3. 发送消息观察流式效果
4. 测试取消功能
5. 测试模式切换

## 性能优化

### 内存管理
- 流式完成后自动清理状态
- 取消操作时立即停止定时器
- 避免内存泄漏

### 用户体验
- 自动滚动到最新消息
- 平滑的打字机动画
- 清晰的状态提示

## 扩展建议

### 未来改进
1. 支持真正的 SSE（在 Web 环境下）
2. 可配置的流式参数
3. 更丰富的动画效果
4. 语音合成集成

### 自定义配置
可以通过修改以下参数来调整流式效果：
- `chunkSize`: 调整每次显示的字符数
- `delay`: 调整字符间延迟
- 动画持续时间和样式 