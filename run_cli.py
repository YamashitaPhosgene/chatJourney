#!/usr/bin/env python
# encoding: utf-8

"""
旅行助手命令行服务启动脚本
使用方法: python run_cli.py
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')

if __name__ == "__main__":
    try:
        # 导入并运行 CLI 服务
        from talker.services.cli_service import CLIService
        
        print("🚀 正在启动旅行助手命令行服务...")
        cli_service = CLIService()
        cli_service.run()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖项")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc() 