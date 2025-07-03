#!/usr/bin/env python
# encoding: utf-8

"""
Django管理命令：测试小红书总结服务
使用方法: python manage.py test_xiaohongshu_summary
"""

import asyncio
import json
import subprocess
import time
import threading
from django.core.management.base import BaseCommand
from django.conf import settings
from talker.services.xiaohongshu_summary_service import summary_service
from hunter.api.hunter_api import api as hunter_api

class Command(BaseCommand):
    help = '测试小红书内容总结服务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keyword',
            type=str,
            default='三里屯 咖啡',
            help='搜索关键词'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='搜索笔记数量限制'
        )
        parser.add_argument(
            '--type',
            type=str,
            default='food',
            choices=['general', 'food', 'travel', 'shopping', 'beauty'],
            help='总结类型'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='运行所有测试用例'
        )
        parser.add_argument(
            '--start-hunter',
            action='store_true',
            help='自动启动Hunter服务器'
        )

    def handle(self, *args, **options):
        if options['all']:
            asyncio.run(self.run_all_tests(options))
        else:
            asyncio.run(self.run_single_test(options))

    def check_vivogpt_config(self):
        """检查VivoGPT配置"""
        self.stdout.write("检查VivoGPT配置...")
        
        app_id = getattr(settings, 'VIVO_APP_ID', None)
        app_key = getattr(settings, 'VIVO_APP_KEY', None)
        
        if not app_id:
            self.stdout.write(self.style.ERROR("❌ VIVO_APP_ID 未配置"))
            return False
        if not app_key:
            self.stdout.write(self.style.ERROR("❌ VIVO_APP_KEY 未配置"))
            return False
            
        self.stdout.write(self.style.SUCCESS(f"✅ VIVO_APP_ID: {app_id[:8]}..."))
        self.stdout.write(self.style.SUCCESS(f"✅ VIVO_APP_KEY: {app_key[:8]}..."))
        return True

    def start_hunter_server(self):
        """启动Hunter服务器"""
        try:
            self.stdout.write("正在启动Hunter服务器...")
            
            # 使用subprocess启动Hunter服务器
            process = subprocess.Popen(
                ['python', 'hunter/startup/hunter_server.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待一段时间让服务器启动
            time.sleep(5)
            
            # 检查进程是否还在运行
            if process.poll() is None:
                self.stdout.write(self.style.SUCCESS("✅ Hunter服务器启动成功"))
                return process
            else:
                stdout, stderr = process.communicate()
                self.stdout.write(self.style.ERROR(f"❌ Hunter服务器启动失败"))
                self.stdout.write(f"stdout: {stdout}")
                self.stdout.write(f"stderr: {stderr}")
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 启动Hunter服务器异常: {e}"))
            return None

    async def run_single_test(self, options):
        """运行单个测试"""
        keyword = options['keyword']
        limit = options['limit']
        summary_type = options['type']
        start_hunter = options['start_hunter']
        
        self.stdout.write(f"=== 测试小红书总结服务 ===\n")
        self.stdout.write(f"关键词: {keyword}")
        self.stdout.write(f"类型: {summary_type}")
        self.stdout.write(f"数量: {limit}\n")
        
        hunter_process = None
        
        try:
            # 1. 检查VivoGPT配置
            if not self.check_vivogpt_config():
                self.stdout.write(self.style.ERROR("❌ VivoGPT配置检查失败，测试终止"))
                return
            
            # 2. 检查HunterAPI状态
            self.stdout.write("2. 检查HunterAPI状态...")
            status = hunter_api.get_status()
            
            if not status["success"]:
                if start_hunter:
                    self.stdout.write("HunterAPI未初始化，正在启动Hunter服务器...")
                    hunter_process = self.start_hunter_server()
                    if hunter_process is None:
                        self.stdout.write(self.style.ERROR("❌ 无法启动Hunter服务器，测试终止"))
                        return
                    
                    # 等待服务器完全启动
                    time.sleep(10)
                    
                    # 再次检查状态
                    status = hunter_api.get_status()
                    if not status["success"]:
                        self.stdout.write(self.style.ERROR("❌ HunterAPI仍然未就绪，请手动启动Hunter服务器"))
                        return
                else:
                    self.stdout.write(self.style.ERROR("❌ HunterAPI未初始化，请先启动Hunter服务器或使用 --start-hunter 参数"))
                    return
            
            self.stdout.write(self.style.SUCCESS("✅ HunterAPI已就绪"))
            
            # 3. 检查并初始化HunterAPI服务
            self.stdout.write("3. 检查HunterAPI服务状态...")
            service_status = status["data"]
            if not service_status.get("initialized") or not service_status.get("logged_in"):
                self.stdout.write("HunterAPI服务需要初始化...")
                init_result = await hunter_api.initialize()
                if not init_result["success"]:
                    self.stdout.write(self.style.ERROR(f"❌ HunterAPI初始化失败: {init_result.get('message', '未知错误')}"))
                    return
                self.stdout.write(self.style.SUCCESS("✅ HunterAPI服务初始化成功"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ HunterAPI服务已就绪"))
            
            # 4. 执行搜索总结
            try:
                result = await summary_service.search_and_summarize(
                    keyword=keyword,
                    limit=limit,
                    summary_type=summary_type
                )
                
                if result["success"]:
                    data = result["data"]
                    self.stdout.write(self.style.SUCCESS(f"✅ 成功获取 {data['notes_count']} 条笔记"))
                    self.stdout.write("总结内容:")
                    self.stdout.write("-" * 50)
                    self.stdout.write(data['summary'])
                    self.stdout.write("-" * 50)
                    
                    # 保存结果
                    filename = f"summary_{summary_type}_{keyword.replace(' ', '_')}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self.stdout.write(f"详细结果已保存到: {filename}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ 失败: {result.get('error', '未知错误')}")
                    )
                    # 即使失败也保存数据（如果有的话）
                    if "data" in result:
                        filename = f"summary_{summary_type}_{keyword.replace(' ', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(result["data"], f, ensure_ascii=False, indent=2)
                        self.stdout.write(f"失败结果已保存到: {filename}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ 异常: {str(e)}")
                )
                
        finally:
            # 5. 关闭Hunter服务器（如果是由我们启动的）
            if hunter_process:
                self.stdout.write("\n5. 关闭Hunter服务器...")
                try:
                    hunter_process.terminate()
                    hunter_process.wait(timeout=10)
                    self.stdout.write(self.style.SUCCESS("✅ Hunter服务器已关闭"))
                except subprocess.TimeoutExpired:
                    hunter_process.kill()
                    self.stdout.write(self.style.WARNING("⚠️ 强制关闭Hunter服务器"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ 关闭Hunter服务器失败: {e}"))

    async def run_all_tests(self, options):
        """运行所有测试用例"""
        self.stdout.write("=== 小红书内容总结服务完整测试 ===\n")
        
        start_hunter = options['start_hunter']
        hunter_process = None
        
        try:
            # 1. 检查VivoGPT配置
            if not self.check_vivogpt_config():
                self.stdout.write(self.style.ERROR("❌ VivoGPT配置检查失败，测试终止"))
                return
            
            # 2. 检查HunterAPI状态
            self.stdout.write("2. 检查HunterAPI状态...")
            status = hunter_api.get_status()
            
            if not status["success"]:
                if start_hunter:
                    self.stdout.write("HunterAPI未初始化，正在启动Hunter服务器...")
                    hunter_process = self.start_hunter_server()
                    if hunter_process is None:
                        self.stdout.write(self.style.ERROR("❌ 无法启动Hunter服务器，测试终止"))
                        return
                    
                    # 等待服务器完全启动
                    time.sleep(10)
                    
                    # 再次检查状态
                    status = hunter_api.get_status()
                    if not status["success"]:
                        self.stdout.write(self.style.ERROR("❌ HunterAPI仍然未就绪，请手动启动Hunter服务器"))
                        return
                else:
                    self.stdout.write(self.style.ERROR("❌ HunterAPI未初始化，请先启动Hunter服务器或使用 --start-hunter 参数"))
                    return
            
            self.stdout.write(self.style.SUCCESS("✅ HunterAPI已就绪"))
            
            # 3. 检查并初始化HunterAPI服务
            self.stdout.write("3. 检查HunterAPI服务状态...")
            service_status = status["data"]
            if not service_status.get("initialized") or not service_status.get("logged_in"):
                self.stdout.write("HunterAPI服务需要初始化...")
                init_result = await hunter_api.initialize()
                if not init_result["success"]:
                    self.stdout.write(self.style.ERROR(f"❌ HunterAPI初始化失败: {init_result.get('message', '未知错误')}"))
                    return
                self.stdout.write(self.style.SUCCESS("✅ HunterAPI服务初始化成功"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ HunterAPI服务已就绪"))
            
            # 4. 测试用例
            test_cases = [
                {
                    "keyword": "三里屯 咖啡",
                    "limit": 3,
                    "summary_type": "poi",
                    "description": "美食类总结"
                },
                {
                    "keyword": "北京 旅游",
                    "limit": 3,
                    "summary_type": "poi",
                    "description": "旅行类总结"
                },
                {
                    "keyword": "口红 推荐",
                    "limit": 3,
                    "summary_type": "poi",
                    "description": "美妆类总结"
                },
                {
                    "keyword": "手机 购买",
                    "limit": 3,
                    "summary_type": "poi",
                    "description": "购物类总结"
                },
                {
                    "keyword": "健身 减肥",
                    "limit": 3,
                    "summary_type": "poi",
                    "description": "通用类总结"
                }
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                self.stdout.write(f"\n{i}. 测试 {test_case['description']}")
                self.stdout.write(f"   关键词: {test_case['keyword']}")
                self.stdout.write(f"   类型: {test_case['summary_type']}")
                self.stdout.write(f"   数量: {test_case['limit']}")
                
                try:
                    result = await summary_service.search_and_summarize(
                        keyword=test_case['keyword'],
                        limit=test_case['limit'],
                        summary_type=test_case['summary_type']
                    )
                    
                    if result["success"]:
                        data = result["data"]
                        self.stdout.write(self.style.SUCCESS(f"   ✅ 成功获取 {data['notes_count']} 条笔记"))
                        self.stdout.write(f"   总结预览: {data['summary'][:200]}...")
                        
                        # 保存详细结果到文件
                        filename = f"summary_{test_case['summary_type']}_{test_case['keyword'].replace(' ', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        self.stdout.write(f"   详细结果已保存到: {filename}")
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ 失败: {result.get('error', '未知错误')}")
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ 异常: {str(e)}")
                    )
                    
        finally:
            # 5. 关闭Hunter服务器（如果是由我们启动的）
            if hunter_process:
                self.stdout.write("\n5. 关闭Hunter服务器...")
                try:
                    hunter_process.terminate()
                    hunter_process.wait(timeout=10)
                    self.stdout.write(self.style.SUCCESS("✅ Hunter服务器已关闭"))
                except subprocess.TimeoutExpired:
                    hunter_process.kill()
                    self.stdout.write(self.style.WARNING("⚠️ 强制关闭Hunter服务器"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ 关闭Hunter服务器失败: {e}")) 