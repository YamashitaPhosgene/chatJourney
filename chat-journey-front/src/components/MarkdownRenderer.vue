<template>
  <view class="markdown-content" v-html="renderedContent"></view>
</template>

<script>
import { marked } from 'marked'

export default {
  name: 'MarkdownRenderer',
  props: {
    content: {
      type: String,
      default: ''
    }
  },
  computed: {
    renderedContent() {
      if (!this.content) return ''
      
      // 配置marked选项
      marked.setOptions({
        breaks: true, // 支持换行
        gfm: true, // 支持GitHub风格的Markdown
        sanitize: false, // 不过滤HTML（在受信任的内容中）
        smartypants: true // 智能标点符号
      })
      
      try {
        return marked(this.content)
      } catch (error) {
        console.error('Markdown渲染错误:', error)
        return this.content // 如果渲染失败，返回原始内容
      }
    }
  }
}
</script>

<style scoped>
.markdown-content {
  line-height: 1.6;
  word-wrap: break-word;
}

/* 标题样式 */
.markdown-content :deep(h1) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 16px 0 12px 0;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 1.3em;
  font-weight: bold;
  margin: 14px 0 10px 0;
  color: #34495e;
  border-bottom: 1px solid #bdc3c7;
  padding-bottom: 6px;
}

.markdown-content :deep(h3) {
  font-size: 1.2em;
  font-weight: bold;
  margin: 12px 0 8px 0;
  color: #2c3e50;
}

.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-size: 1.1em;
  font-weight: bold;
  margin: 10px 0 6px 0;
  color: #34495e;
}

/* 段落样式 */
.markdown-content :deep(p) {
  margin: 8px 0;
  text-align: justify;
}

/* 列表样式 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(ul li) {
  list-style-type: disc;
}

.markdown-content :deep(ol li) {
  list-style-type: decimal;
}

/* 嵌套列表 */
.markdown-content :deep(ul ul),
.markdown-content :deep(ol ol),
.markdown-content :deep(ul ol),
.markdown-content :deep(ol ul) {
  margin: 4px 0;
}

/* 强调样式 */
.markdown-content :deep(strong),
.markdown-content :deep(b) {
  font-weight: bold;
  color: #2c3e50;
}

.markdown-content :deep(em),
.markdown-content :deep(i) {
  font-style: italic;
  color: #34495e;
}

/* 链接样式 */
.markdown-content :deep(a) {
  color: #3498db;
  text-decoration: none;
  border-bottom: 1px solid #3498db;
}

.markdown-content :deep(a:hover) {
  color: #2980b9;
  border-bottom-color: #2980b9;
}

/* 代码样式 */
.markdown-content :deep(code) {
  background-color: #f8f9fa;
  color: #e74c3c;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background-color: #f8f9fa;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  padding: 12px;
  margin: 12px 0;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  color: #2c3e50;
  padding: 0;
  border-radius: 0;
  font-size: 0.85em;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
  border-left: 4px solid #3498db;
  background-color: #f8f9fa;
  margin: 12px 0;
  padding: 8px 12px;
  color: #555;
  font-style: italic;
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

/* 表格样式 */
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 0.9em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f2f2f2;
  font-weight: bold;
}

.markdown-content :deep(tr:nth-child(even)) {
  background-color: #f9f9f9;
}

/* 分割线样式 */
.markdown-content :deep(hr) {
  border: none;
  height: 2px;
  background-color: #bdc3c7;
  margin: 20px 0;
}

/* 图片样式 */
.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 8px 0;
}

/* 删除线样式 */
.markdown-content :deep(del) {
  text-decoration: line-through;
  color: #7f8c8d;
}

/* 旅游相关的特殊样式 */
.markdown-content :deep(.day-title) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  margin: 16px 0 12px 0;
  font-weight: bold;
}

.markdown-content :deep(.poi-item) {
  background-color: #e8f5e8;
  border-left: 4px solid #27ae60;
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 4px 4px 0;
}

.markdown-content :deep(.time-marker) {
  color: #e74c3c;
  font-weight: bold;
  background-color: #fdf2f2;
  padding: 2px 6px;
  border-radius: 3px;
}
</style> 