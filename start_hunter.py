#!/usr/bin/env python
# encoding: utf-8

"""
Hunter服务器启动脚本
使用方法: python start_hunter.py
"""

import os
import sys
import subprocess
import time

def start_hunter_server():
    """启动Hunter服务器"""
    print("🚀 正在启动Hunter服务器...")
    
    try:
        # 启动Hunter服务器
        process = subprocess.Popen(
            ['python', 'hunter/startup/hunter_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("✅ Hunter服务器启动成功")
        print("📝 进程ID:", process.pid)
        print("⏳ 等待服务器初始化...")
        
        # 等待一段时间让服务器启动
        time.sleep(10)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print("✅ Hunter服务器运行正常")
            print("💡 现在可以运行测试命令了:")
            print("   python manage.py test_xiaohongshu_summary --all --start-hunter")
            print("\n🛑 按 Ctrl+C 停止服务器")
            
            try:
                # 保持进程运行
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 收到停止信号，正在关闭服务器...")
                process.terminate()
                process.wait(timeout=10)
                print("✅ Hunter服务器已关闭")
        else:
            stdout, stderr = process.communicate()
            print("❌ Hunter服务器启动失败")
            print("stdout:", stdout)
            print("stderr:", stderr)
            
    except Exception as e:
        print(f"❌ 启动Hunter服务器异常: {e}")

if __name__ == "__main__":
    start_hunter_server() 