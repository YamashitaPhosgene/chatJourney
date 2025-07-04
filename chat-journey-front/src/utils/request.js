import { baseURL } from "@/config/index.js";

export function request(url, data = {}, method = "GET", headers = {}) {
  return new Promise((resolve, reject) => {
    // 为所有请求添加客户端类型参数
    const finalUrl = url.includes('?') 
      ? `${baseURL}${url}&client_type=uni-app`
      : `${baseURL}${url}?client_type=uni-app`;
    
    uni.request({
      url: finalUrl,
      method,
      data,
      header: { "Content-Type": "application/json", ...headers },
      success: (res) => resolve(res.data),
      fail: (err) => reject(err),
    });
  });
}

/**
 * 流式请求 - uni-app 环境下的流式模拟
 * 注意：uni-app 不支持真正的 SSE，这里使用轮询模拟流式效果
 * @param {string} url - 请求URL
 * @param {Object} data - 请求数据
 * @param {Object} options - 选项
 * @param {Function} options.onChunk - 接收到数据块时的回调
 * @param {Function} options.onDone - 流式完成时的回调
 * @param {Function} options.onError - 错误时的回调
 * @returns {Promise} - 返回一个可以取消的Promise
 */
export function requestStream(url, data = {}, options = {}) {
  // 首先尝试真正的流式请求
  console.log("尝试真正的流式请求");
  return requestStreamReal(url, data, options)
    .catch(err => {
      console.log("真正流式请求失败，降级到模拟流式:", err);
      return requestStreamFallback(url, data, options);
    });
}

/**
 * 真正的流式请求实现
 * @param {string} url - 请求URL
 * @param {Object} data - 请求数据
 * @param {Object} options - 选项
 */
function requestStreamReal(url, data = {}, options = {}) {
  const { onChunk, onDone, onError } = options;
  let isCancelled = false;
  
  return new Promise((resolve, reject) => {
    // 检查是否在浏览器环境中
    const isBrowser = typeof window !== 'undefined' && typeof fetch !== 'undefined';
    
    if (isBrowser) {
      // 浏览器环境：使用真正的SSE
      const finalUrl = `${baseURL}${url}`;
      
      fetch(finalUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(data)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        if (!response.body) {
          throw new Error('ReadableStream not supported');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        const readChunk = () => {
          return reader.read().then(({ done, value }) => {
            if (done) {
              if (onDone) onDone('');
              return;
            }
            
            if (isCancelled) return;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后一行（可能不完整）
            
            for (const line of lines) {
              if (line.trim().startsWith('data:')) {
                const dataContent = line.substring(5).trim();
                
                if (dataContent === '[DONE]') {
                  if (onDone) onDone('');
                  return;
                }
                
                try {
                  const data = JSON.parse(dataContent);
                  if (data.type === 'content' && data.chunk) {
                    if (onChunk) onChunk({
                      type: 'content',
                      chunk: data.chunk,
                      fullContent: data.full_content,
                      data: data
                    });
                  } else if (data.type === 'done') {
                    if (onDone) onDone(data.full_content);
                    return;
                  } else if (data.type === 'error') {
                    if (onError) onError(data.error);
                    return;
                  }
                } catch (e) {
                  console.warn('解析SSE数据失败:', e, dataContent);
                }
              }
            }
            
            return readChunk();
          });
        };
        
        readChunk().catch(err => {
          if (!isCancelled && onError) onError(err);
        });
        
        resolve({ 
          cancel: () => { 
            isCancelled = true;
            reader.cancel();
          } 
        });
      })
      .catch(err => {
        if (!isCancelled && onError) onError(err);
        reject(err);
      });
      
    } else {
      // uni-app环境：使用uni.request
      const finalUrl = url.includes('?') 
        ? `${baseURL}${url}&client_type=uni-app`
        : `${baseURL}${url}?client_type=uni-app`;
      
      const requestTask = uni.request({
        url: finalUrl,
        method: 'POST',
        data: data,
        header: { 
          "Content-Type": "application/json",
          "Accept": "text/event-stream"
        },
        responseType: 'text',
        success: (res) => {
          if (isCancelled) return;
          
          // 检查是否是SSE格式的响应
          if (res.header && res.header['content-type'] && 
              res.header['content-type'].includes('text/event-stream')) {
            // 解析SSE响应
            parseSSEResponse(res.data, { onChunk, onDone, onError });
          } else {
            // 如果不是SSE格式，当作普通响应处理
            const content = res.data?.response || res.data?.reply || res.data?.data?.content || "";
            if (content) {
              // 直接返回完整内容（不模拟打字效果）
              if (onChunk) onChunk({
                type: 'content',
                chunk: content,
                fullContent: content
              });
              if (onDone) onDone(content);
            } else {
              if (onDone) onDone("");
            }
          }
          
          resolve({ 
            cancel: () => { 
              isCancelled = true;
              if (requestTask && requestTask.abort) {
                requestTask.abort();
              }
            } 
          });
        },
        fail: (err) => {
          if (isCancelled) return;
          if (onError) onError(err);
          reject(err);
        }
      });
    }
  });
}

/**
 * 解析 SSE 响应文本
 * @param {string} responseText - 响应文本
 * @param {Object} callbacks - 回调函数
 */
function parseSSEResponse(responseText, callbacks) {
  const { onChunk, onDone, onError } = callbacks;
  
  if (!responseText) return;
  
  // 按行分割响应
  const lines = responseText.split('\n');
  let fullContent = "";
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line.startsWith('data:')) {
      const dataContent = line.substring(5).trim();
      
      // 检查是否是结束标记
      if (dataContent === '[DONE]') {
        if (onDone) onDone(fullContent);
        return;
      }
      
      try {
        // 解析JSON数据
        const data = JSON.parse(dataContent);
        const chunk = data.message || data.reply || data.chunk || "";
        
        if (chunk) {
          fullContent += chunk;
          if (onChunk) onChunk({
            type: 'content',
            chunk: chunk,
            fullContent: fullContent,
            data: data
          });
        }
      } catch (e) {
        // 如果不是JSON，直接作为文本处理
        if (dataContent) {
          fullContent += dataContent;
          if (onChunk) onChunk({
            type: 'content',
            chunk: dataContent,
            fullContent: fullContent
          });
        }
      }
    } else if (line.startsWith('event:')) {
      // 处理事件类型
      const eventType = line.substring(6).trim();
      
      // 读取下一行的data
      if (i + 1 < lines.length && lines[i + 1].startsWith('data:')) {
        const eventData = lines[i + 1].substring(5).trim();
        try {
          const data = JSON.parse(eventData);
          if (onChunk) onChunk({
            type: 'event',
            event: eventType,
            data: data,
            fullContent: fullContent
          });
          
          // 如果是错误事件
          if (eventType === 'error' && onError) {
            onError(data);
          }
        } catch (e) {
          if (onChunk) onChunk({
            type: 'event',
            event: eventType,
            data: eventData,
            fullContent: fullContent
          });
        }
        i++; // 跳过下一行
      }
    }
  }
  
  // 如果没有明确的结束标记，认为流式已完成
  if (onDone) onDone(fullContent);
}

/**
 * 模拟流式请求 (用于uni-app环境或降级场景)
 * @param {string} url - 请求URL
 * @param {Object} data - 请求数据
 * @param {Object} options - 选项
 */
export function requestStreamFallback(url, data = {}, options = {}) {
  const { onChunk, onDone, onError } = options;
  let isCancelled = false;
  
  return new Promise((resolve, reject) => {
    // 保持流式标记，让后端知道这是流式请求
    const streamData = { ...data };
    
    request(url, streamData, "POST")
      .then(res => {
        if (isCancelled) return;
        
        const content = res.response || res.reply || res.data?.content || "";
        
        if (content) {
          // 模拟打字机效果
          let currentIndex = 0;
          const chunkSize = 2; // 每次显示2个字符
          const delay = 30; // 30ms延迟模拟打字效果
          
          const showNextChunk = () => {
            if (isCancelled) return;
            
            if (currentIndex < content.length) {
              const chunk = content.substring(currentIndex, currentIndex + chunkSize);
              const fullContent = content.substring(0, currentIndex + chunkSize);
              
              if (onChunk) onChunk({
                type: 'content',
                chunk: chunk,
                fullContent: fullContent
              });
              
              currentIndex += chunkSize;
              setTimeout(showNextChunk, delay);
            } else {
              if (onDone) onDone(content);
            }
          };
          
          // 延迟开始，让UI有时间准备
          setTimeout(showNextChunk, 100);
        } else {
          if (onDone) onDone("");
        }
        
        resolve({ 
          cancel: () => { 
            isCancelled = true; 
          } 
        });
      })
      .catch(err => {
        if (isCancelled) return;
        if (onError) onError(err);
        reject(err);
      });
  });
} 