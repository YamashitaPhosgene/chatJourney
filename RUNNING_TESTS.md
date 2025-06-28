# 运行小红书总结API测试

## 问题说明

在Django项目外部直接运行Python脚本会遇到Django设置未配置的错误：

```
django.core.exceptions.ImproperlyConfigured: Requested setting BASE_DIR, but settings are not configured.
```

这是因为脚本需要Django环境才能正确导入和使用Django相关的模块。

另外，HunterAPI需要先启动Hunter服务器才能正常工作，因为HunterAPI依赖于独立的Hunter服务器进程。

## 解决方案

### 方法1：使用Django管理命令（推荐）

这是最推荐的方法，因为它完全集成在Django环境中，并且可以自动启动Hunter服务器：

```bash
# 运行单个测试（自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --keyword "三里屯 咖啡" --type food --limit 3 --start-hunter

# 运行所有测试用例（自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --all --start-hunter

# 查看帮助
python manage.py test_xiaohongshu_summary --help
```

**参数说明：**
- `--keyword`: 搜索关键词（默认：三里屯 咖啡）
- `--type`: 总结类型（默认：food，可选：general, food, travel, shopping, beauty）
- `--limit`: 搜索笔记数量限制（默认：3）
- `--all`: 运行所有预设测试用例
- `--start-hunter`: 自动启动Hunter服务器

### 方法2：手动启动Hunter服务器

如果你想要更精细的控制，可以手动启动Hunter服务器：

```bash
# 1. 启动Hunter服务器
python start_hunter.py

# 2. 在另一个终端运行测试（不自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --all
```

### 方法3：使用原有的Hunter启动方式

如果你习惯使用原有的启动方式：

```bash
# 1. 启动Hunter服务器
hunter start hunter server

# 2. 在另一个终端运行测试
python manage.py test_xiaohongshu_summary --all
```

### 方法4：在Django Shell中运行

```bash
# 启动Django shell
python manage.py shell

# 在shell中运行测试脚本
exec(open('test_xiaohongshu_summary_django.py').read())
```

## 测试脚本说明

### 1. Django管理命令
**文件**: `talker/management/commands/test_xiaohongshu_summary.py`

**特点：**
- 完全集成在Django环境中
- 支持命令行参数
- 彩色输出（成功/错误状态）
- 可以运行单个测试或所有测试
- 支持自动启动Hunter服务器

**使用示例：**
```bash
# 测试美食总结（自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --keyword "北京 火锅" --type food --limit 5 --start-hunter

# 测试旅行总结（自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --keyword "上海 旅游" --type travel --limit 3 --start-hunter

# 运行所有测试（自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --all --start-hunter
```

### 2. Hunter服务器启动脚本
**文件**: `start_hunter.py`

**特点：**
- 独立的Hunter服务器启动脚本
- 提供进程状态监控
- 支持优雅关闭

**使用示例：**
```bash
python start_hunter.py
```

### 3. Django环境脚本
**文件**: `test_xiaohongshu_summary_django.py`

**特点：**
- 自动设置Django环境
- 可以独立运行
- 包含完整的测试用例

## 测试流程

所有测试脚本都遵循以下流程：

1. **检查HunterAPI状态**
   - 如果未初始化，根据参数决定是否自动启动Hunter服务器
   - 如果已就绪，直接使用

2. **执行搜索总结**
   - 根据参数搜索小红书笔记
   - 获取笔记详细内容和评论
   - 生成AI总结

3. **保存结果**
   - 将结果保存为JSON文件
   - 显示总结内容预览

4. **关闭Hunter服务器**
   - 如果是由测试脚本启动的，自动关闭
   - 释放浏览器资源

## 输出示例

```
=== 小红书内容总结服务完整测试 ===

1. 检查HunterAPI状态...
HunterAPI未初始化，正在启动Hunter服务器...
正在启动Hunter服务器...
✅ Hunter服务器启动成功
✅ HunterAPI已就绪

1. 测试 美食类总结
   关键词: 三里屯 咖啡
   类型: food
   数量: 3
   ✅ 成功获取 3 条笔记
   总结预览: 基于小红书用户分享，三里屯咖啡店整体评价如下：1. 推荐度最高的咖啡店：- %店名%：用户评价环境优雅，咖啡品质上乘...
   详细结果已保存到: summary_food_三里屯_咖啡.json

3. 关闭Hunter服务器...
✅ Hunter服务器已关闭
```

## 注意事项

1. **Django环境**: 确保在Django项目根目录下运行命令
2. **依赖安装**: 确保所有依赖包已正确安装
3. **网络连接**: 确保网络连接稳定，能够访问小红书
4. **浏览器环境**: 确保系统支持Playwright浏览器自动化
5. **VivoGPT配置**: 确保VivoGPT服务已正确配置
6. **Hunter服务器**: 确保Hunter服务器能够正常启动和运行

## 故障排除

### 常见错误

1. **Django设置错误**
   ```
   ImproperlyConfigured: Requested setting BASE_DIR, but settings are not configured.
   ```
   **解决**: 使用Django管理命令或在Django环境中运行

2. **HunterAPI未初始化**
   ```
   服务未初始化，请先调用 initialize()
   ```
   **解决**: 使用 `--start-hunter` 参数或手动启动Hunter服务器

3. **Hunter服务器启动失败**
   ```
   Hunter服务器启动失败
   ```
   **解决**: 检查Hunter项目配置和依赖

4. **VivoGPT连接失败**
   ```
   总结生成失败: 连接超时
   ```
   **解决**: 检查VivoGPT服务配置和网络连接

### 调试技巧

1. **查看详细日志**
   ```bash
   python manage.py test_xiaohongshu_summary --keyword "测试" --limit 1 --start-hunter
   ```

2. **检查HunterAPI状态**
   ```bash
   python manage.py shell
   >>> from hunter.api.hunter_api import api as hunter_api
   >>> hunter_api.get_status()
   ```

3. **手动启动Hunter服务器**
   ```bash
   python start_hunter.py
   ```

4. **测试ChatService**
   ```bash
   python manage.py shell
   >>> from talker.services.chat_service import ChatService
   >>> service = ChatService()
   >>> response = service.process_chat("测试消息")
   >>> print(response)
   ```

## 推荐使用方式

对于日常测试和开发，推荐使用Django管理命令并自动启动Hunter服务器：

```bash
# 快速测试单个功能
python manage.py test_xiaohongshu_summary --keyword "测试关键词" --type general --start-hunter

# 完整测试所有功能
python manage.py test_xiaohongshu_summary --all --start-hunter
```

这种方式最稳定、最方便，也是Django项目的最佳实践。

## 手动启动Hunter服务器

如果你需要手动控制Hunter服务器：

```bash
# 启动Hunter服务器
python start_hunter.py

# 在另一个终端运行测试（不自动启动Hunter服务器）
python manage.py test_xiaohongshu_summary --all
```

这样可以更好地控制Hunter服务器的生命周期。 