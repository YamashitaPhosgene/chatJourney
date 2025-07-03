#!/usr/bin/env python
# encoding: utf-8
#type: ignore

import sys
import os
import json
from typing import Optional, Dict, Any
from django.core.management import execute_from_command_line
from django.conf import settings
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.services.state_machine import TravelAssistantFSM
from talker.services.poi_management import POIManagementService
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CLIService:
    """命令行服务类，提供与状态机系统交互的界面"""
    
    def __init__(self):
        self.fsm: Optional[TravelAssistantFSM] = None
        self.poi_service = POIManagementService()
    
    def print_poi_keywords(self, keywords: Dict[str, Any]) -> None:
        """打印POI关键词到命令行
        
        Args:
            keywords: 关键词字典
        """
        if not keywords:
            print("\n🔍 POI关键词生成失败")
            return
        
        print("\n🔍 生成的POI关键词:")
        print("=" * 50)
        
        # 打印主要关键词
        if keywords.get('primary_keywords'):
            print("📍 主要关键词:")
            for keyword in keywords['primary_keywords']:
                print(f"  • {keyword}")
            print()
        
        # 打印次要关键词
        if keywords.get('secondary_keywords'):
            print("🔖 次要关键词:")
            for keyword in keywords['secondary_keywords']:
                print(f"  • {keyword}")
            print()
        
        # 打印地点关键词
        if keywords.get('city_keywords'):
            print("🗺️  地点关键词:")
            for keyword in keywords['city_keywords']:
                print(f"  • {keyword}")
            print()
        
        # 打印兴趣关键词
        if keywords.get('interest_keywords'):
            print("🎯 兴趣关键词:")
            for keyword in keywords['interest_keywords']:
                print(f"  • {keyword}")
            print()
        
        # 打印搜索建议
        if keywords.get('search_suggestions'):
            print("💡 搜索建议:")
            for suggestion in keywords['search_suggestions']:
                print(f"  • {suggestion}")
            print()
        
        print("=" * 50)
    
    def print_poi_search_results(self, result: Dict[str, Any], page: int = 1) -> None:
        """分页打印POI搜索结果到命令行，每页4个，合并去重"""
        if not result:
            print("\n🔍 POI搜索失败")
            return

        print("\n🔍 POI搜索结果:")
        print("=" * 60)

        # 显示LLM生成的关键词
        query = result.get("query", {})
        if query:
            print("📝 LLM生成的关键词:")
            for key, value in query.items():
                if isinstance(value, list) and value:
                    print(f"  {key}: {value}")
            print()

        # 显示解析结果
        adcode = result.get("adcode")
        code_map = result.get("code_map", {})
        print(f"📍 行政区划代码: {adcode or '未找到'}")
        print(f"🏷️  分类码映射: {len(code_map)} 个分类")
        for code, words in code_map.items():
            print(f"    {code}: {', '.join(words)}")
        print()

        # 显示过滤信息
        avoid_keywords = query.get("avoid_keywords", [])
        if avoid_keywords:
            print(f"🚫 避雷关键词: {avoid_keywords}")
            print(f"🚫 避雷分类码: ['050117'] (火锅店)")
            print()

        # 合并所有POI到一个列表，去重
        pois = result.get("pois", {})
        all_pois = []
        seen = set()
        for keyword_bucket in pois.values():
            for code_pois in keyword_bucket.values():
                for poi in code_pois:
                    if "error" in poi:
                        continue
                    key = (poi.get("name"), poi.get("address"), poi.get("typecode"))
                    if key not in seen:
                        seen.add(key)
                        all_pois.append(poi)

        total = len(all_pois)
        if total == 0:
            print("❌ 未找到任何POI结果")
            print("=" * 60)
            return

        # 分页
        page_size = 4
        total_pages = (total + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start = (page - 1) * page_size
        end = start + page_size
        page_pois = all_pois[start:end]

        print(f"🏪 POI列表（第{page}/{total_pages}页, 共{total}个）:")
        print("-" * 40)
        for i, poi in enumerate(page_pois, start=start+1):
            name = poi.get("name", "未知")
            address = poi.get("address", "未知地址")
            typecode = poi.get("typecode", "未知类型")
            print(f"  {i}. {name}")
            print(f"     地址: {address}")
            print(f"     类型: {typecode}")
        print("-" * 40)
        if page < total_pages:
            print(f"输入 /nextpage 查看下一页（当前{page}/{total_pages}）")
        else:
            print("已显示全部POI。")
        print("=" * 60)

        # 缓存分页数据，供/nextpage命令使用
        self._poi_page = page
        self._poi_page_data = {
            "all_pois": all_pois,
            "total_pages": total_pages,
            "result": result
        }

    def show_next_poi_page(self):
        """显示下一页POI"""
        if not hasattr(self, "_poi_page_data") or not self._poi_page_data:
            print("未找到POI分页数据，请先执行一次POI搜索。")
            return
        page = self._poi_page + 1
        total_pages = self._poi_page_data["total_pages"]
        if page > total_pages:
            print("已显示全部POI。")
            return
        self.print_poi_search_results(self._poi_page_data["result"], page=page)
    
    def start_new_session(self) -> None:
        """开始新的对话会话"""
        try:
            # 创建新的状态机实例（会自动创建session）
            self.fsm = TravelAssistantFSM()
            session_id = self.fsm.create_new_session()
            
            # 启动状态机并获取初始回复
            self.fsm.start()  # type: ignore  # 使用状态转移而不是直接设置状态
            initial_response = self.fsm.ask_destination()
            
            print(f"\n🎉 新会话已创建 (ID: {session_id})")
            print("=" * 50)
            print("欢迎使用旅行助手！我将帮助您规划完美的旅行。")
            print("=" * 50)
            print(f"🤖 {initial_response}")
            
        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            logging.error(f"创建会话失败: {e}")
    
    def load_session(self, session_id: str) -> bool:
        """加载现有的对话会话"""
        try:
            # 创建状态机实例并加载session
            self.fsm = TravelAssistantFSM()
            if self.fsm.load_session(session_id):
                session_info = self.fsm.get_session_info()
                
                print(f"\n📂 会话已加载 (ID: {session_id})")
                print("=" * 50)
                self._show_session_info(session_info)
                print("=" * 50)
                
                return True
            else:
                print(f"❌ 会话 {session_id} 不存在")
                return False
            
        except Exception as e:
            print(f"❌ 加载会话失败: {e}")
            logging.error(f"加载会话失败: {e}")
            return False
    
    def send_message(self, message: str) -> None:
        """发送消息给状态机"""
        if not self.fsm:
            print("❌ 没有活跃的会话，请先创建或加载会话")
            return
        
        try:
            # 处理用户消息（状态机会自动处理session操作）
            response = self.fsm.handle_utterance(message)
            
            print(f"\n🤖 {response}")
            
            # 显示当前状态信息
            self._show_current_status()
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            logging.error(f"处理消息失败: {e}")
    
    def _show_session_info(self, session_info: Dict[str, Any]) -> None:
        """显示会话信息"""
        if not session_info:
            return
        
        print(f"会话ID: {session_info.get('session_id', '未知')}")
        print(f"用户: {session_info.get('user', '未知')}")
        print(f"创建时间: {session_info.get('created_at', '未知')}")
        print(f"最后更新: {session_info.get('updated_at', '未知')}")
        print(f"对话轮数: {session_info.get('conversation_rounds', 0)}")
        
        # 显示已收集的信息
        collected_info = session_info.get('collected_info', [])
        if collected_info:
            print("已收集信息:")
            for info in collected_info:
                print(f"  - {info}")
        else:
            print("已收集信息: 暂无")
    
    def _show_current_status(self) -> None:
        """显示当前状态"""
        if not self.fsm:
            return
        
        session_info = self.fsm.get_session_info()
        current_state = session_info.get('current_state', '未知')
        
        print(f"\n📊 当前状态: {current_state}")
    
    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
🤖 旅行助手命令行服务

📝 基本命令:
  /help          - 显示此帮助信息
  /new           - 开始新会话
  /load <ID>     - 加载指定会话
  /save          - 保存当前会话
  /info          - 显示会话信息
  /status        - 显示当前状态
  /slots         - 显示槽位信息
  /history       - 显示对话历史
  /quit          - 退出程序

🗺️ POI相关命令:
  /pois          - 显示会话所有POI
  /addpoi <序号> - 添加搜索结果POI到数据库
  /removepoi <ID> - 删除指定POI
  /poi <ID>      - 显示指定POI详情
  /nextpage      - 显示下一页POI搜索结果
  /detail <序号> - 显示搜索结果POI的高德详情
  /recpoi        - 显示最近一次推荐POI搜索结果（第一页）

💬 使用说明:
  - 直接输入文本与AI对话
  - 使用 / 开头的命令执行特殊操作
  - POI搜索后可使用 /addpoi 添加到数据库
  - 使用 /pois 查看所有已保存的POI
        """
        print(help_text)
    
    def show_slots(self) -> None:
        """显示槽位信息"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        slots_info = self.fsm.get_slots_info()
        print("\n📋 槽位信息:")
        print("=" * 30)
        for slot_name, slot_data in slots_info.items():
            status = "✅ 已填充" if slot_data['status'] == "已填充" else "❌ 未填充"
            print(f"{slot_name:12}: {status}")
            if slot_data['value']:
                print(f"{'':12}  值: {slot_data['value']}")
        print("=" * 30)
    
    def show_history(self) -> None:
        """显示对话历史"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        history = self.fsm.get_conversation_history()
        if not history:
            print("❌ 没有对话历史")
            return
        
        print("\n💬 对话历史:")
        print("=" * 50)
        for i, message in enumerate(history, 1):
            role = "👤 用户" if message["role"] == "user" else "🤖 助手"
            content = message["content"]
            print(f"{i:2d}. {role}: {content}")
        print("=" * 50)
    
    def save_session(self) -> None:
        """保存当前会话"""
        if not self.fsm:
            print("❌ 没有活跃的会话")
            return
        
        try:
            if self.fsm.save_session():
                session_info = self.fsm.get_session_info()
                session_id = session_info.get('session_id', '未知')
                print(f"✅ 会话已保存 (ID: {session_id})")
            else:
                print("❌ 保存会话失败")
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
            logging.error(f"保存会话失败: {e}")
    
    def run(self) -> None:
        """运行命令行服务"""
        print("🚀 启动旅行助手命令行服务...")
        print("输入 /help 查看帮助信息")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 请输入消息或命令: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    # 处理普通消息
                    self.send_message(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except EOFError:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                logging.error(f"CLI服务错误: {e}")
    
    def _handle_command(self, command: str) -> None:
        """处理命令"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == '/help':
            self.show_help()
        elif cmd == '/new':
            self.start_new_session()
        elif cmd == '/load' and len(parts) > 1:
            self.load_session(parts[1])
        elif cmd == '/save':
            self.save_session()
        elif cmd == '/info':
            if self.fsm:
                session_info = self.fsm.get_session_info()
                self._show_session_info(session_info)
            else:
                print("❌ 没有活跃的会话")
        elif cmd == '/status':
            self._show_current_status()
        elif cmd == '/slots':
            self.show_slots()
        elif cmd == '/history':
            self.show_history()
        elif cmd == '/quit':
            print("👋 再见！")
            sys.exit(0)
        elif cmd == '/nextpage':
            self.show_next_poi_page()
        elif cmd == '/pois':
            self.show_session_pois()
        elif cmd.startswith("/addpoi"):
            parts = command.strip().split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("用法: /addpoi <序号>")
                return
            idx = int(parts[1])
            self.add_selected_poi_by_index(idx)
        elif cmd.startswith("/removepoi"):
            parts = command.strip().split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("用法: /removepoi <ID>")
                return
            poi_id = int(parts[1])
            self.remove_poi_by_id(poi_id)
        elif cmd.startswith("/poi"):
            parts = command.strip().split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("用法: /poi <ID>")
                return
            poi_id = int(parts[1])
            self.show_poi_detail_by_id(poi_id)
        elif cmd.startswith("/detail"):
            parts = command.strip().split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("用法: /detail <序号>")
                return
            idx = int(parts[1])
            self.show_poi_detail_by_index(idx)
        elif cmd == '/recpoi':
            self.show_last_poi_search()
        else:
            print("❌ 未知命令，输入 /help 查看帮助信息")

    def add_selected_poi_by_index(self, idx: int):
        """将当前分页POI列表中指定序号的POI添加到数据库POI表"""
        if not hasattr(self, "_poi_page_data") or not self._poi_page_data:
            print("未找到POI分页数据，请先执行一次POI搜索。")
            return
        
        if not hasattr(self, "fsm") or not self.fsm.session:
            print("未找到有效的会话，无法添加POI。")
            return
        
        all_pois = self._poi_page_data["all_pois"]
        if idx < 1 or idx > len(all_pois):
            print(f"序号超出范围（1~{len(all_pois)}），请重新输入。")
            return
        
        poi = all_pois[idx-1]
        
        # 使用POI管理服务添加POI
        success = self.poi_service.add_poi_from_search_result(
            session=self.fsm.session,
            poi_data=poi,
            source='manual'
        )
        
        if success:
            print(f"✅ 已将POI添加到数据库：{poi.get('name', '未知')}")
        else:
            print(f"❌ 添加POI失败：{poi.get('name', '未知')}")

    def show_session_pois(self):
        """显示会话的所有POI"""
        if not hasattr(self, "fsm") or not self.fsm.session:
            print("❌ 没有活跃的会话")
            return
        
        # 通过POISession获取会话的所有POI
        from talker.models import POISession
        poi_relations = POISession.objects.filter(session=self.fsm.session).select_related('poi').order_by('-created_at')
        
        if not poi_relations:
            print("❌ 会话中没有POI")
            return
        
        print("\n🗺️ 会话POI列表:")
        print("=" * 80)
        print(f"{'ID':<4} {'名称':<20} {'来源':<12} {'地址':<30} {'类型':<15}")
        print("-" * 80)
        
        for rel in poi_relations:
            poi = rel.poi
            source_map = {
                'manual': '手动添加',
                'reverse_search': '逆搜索',
                'keyword_search': '关键词搜索'
            }
            source_text = source_map.get(rel.source, rel.source)
            address = poi.address[:27] + "..." if len(poi.address) > 30 else poi.address
            poi_type = poi.type[:12] + "..." if len(poi.type) > 15 else poi.type
            
            print(f"{poi.id:<4} {poi.name:<20} {source_text:<12} {address:<30} {poi_type:<15}")
        
        print("=" * 80)
        
        # 显示统计信息
        stats = self.poi_service.get_poi_statistics(self.fsm.session)
        print(f"\n📊 POI统计: 总计{stats['total']}个 (手动{stats['manual']}个, 逆搜索{stats['reverse_search']}个, 关键词搜索{stats['keyword_search']}个)")

    def remove_poi_by_id(self, poi_id: int):
        """根据ID删除POI"""
        if not hasattr(self, "fsm") or not self.fsm.session:
            print("❌ 没有活跃的会话")
            return
        
        success = self.poi_service.remove_poi(self.fsm.session, poi_id)
        if success:
            print(f"✅ 成功删除POI (ID: {poi_id})")
        else:
            print(f"❌ 删除POI失败 (ID: {poi_id})")

    def show_poi_detail_by_id(self, poi_id: int):
        """根据数据库ID显示POI详情（递归美化输出全部字段）"""
        if not hasattr(self, "fsm") or not self.fsm.session:
            print("❌ 没有活跃的会话")
            return
        
        # 通过POISession获取会话的POI
        from talker.models import POISession
        rel = POISession.objects.filter(session=self.fsm.session, poi_id=poi_id).select_related('poi').first()
        
        if not rel:
            print(f"❌ 未找到POI (ID: {poi_id})")
            return
        
        poi = rel.poi
        print(f"\n📋 POI详情 (ID: {poi_id}):")
        print("=" * 60)
        print(f"名称: {poi.name}")
        print(f"来源: {rel.source}")
        print(f"地址: {poi.address}")
        print(f"类型: {poi.type}")
        print(f"电话: {poi.tel}")
        print(f"坐标: {poi.location}")
        print(f"创建时间: {poi.created_at}")
        print("-" * 60)
        print("原始高德API数据（全部字段）：")
        self._print_dict_recursive(poi.raw_data)
        print("=" * 60)

    def show_poi_detail_by_index(self, idx: int):
        """显示当前分页POI列表中指定序号POI的高德官方详情（全字段递归美化输出）"""
        if not hasattr(self, "_poi_page_data") or not self._poi_page_data:
            print("未找到POI分页数据，请先执行一次POI搜索。")
            return
        all_pois = self._poi_page_data["all_pois"]
        if idx < 1 or idx > len(all_pois):
            print(f"序号超出范围（1~{len(all_pois)}），请重新输入。")
            return
        poi = all_pois[idx-1]
        poi_id = poi.get("id")
        if not poi_id:
            print("该POI无高德ID，无法查询详情。")
            return
        from hunter.api.amap_api import AmapPlaceAPI, AmapAPIError
        from chatJourney import settings
        place_api = AmapPlaceAPI(key=settings.AMAP_KEY)
        try:
            detail = place_api.get_poi_detail(poi_id, fields="all")
            print("\n📋 POI官方详情（全部字段）：")
            print("="*60)
            self._print_dict_recursive(detail)
            print("="*60)
        except AmapAPIError as e:
            print(f"❌ 查询失败: {e}")
        except Exception as e:
            print(f"❌ 查询异常: {e}")

    def _print_dict_recursive(self, d, indent=0):
        """递归美化打印字典/列表所有字段"""
        prefix = "  " * indent
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (dict, list)):
                    print(f"{prefix}{k}:")
                    self._print_dict_recursive(v, indent+1)
                else:
                    print(f"{prefix}{k}: {v}")
        elif isinstance(d, list):
            for i, item in enumerate(d, 1):
                print(f"{prefix}- 第{i}项:")
                self._print_dict_recursive(item, indent+1)
        else:
            print(f"{prefix}{d}")

    def show_last_poi_search(self):
        """展示最近一次POI搜索结果（第一页）"""
        if not hasattr(self, "_poi_page_data") or not self._poi_page_data:
            print("未找到POI搜索结果，请先进行一次POI搜索。")
            return
        self.print_poi_search_results(self._poi_page_data["result"], page=1)


def main():
    """主函数"""
    cli_service = CLIService()
    cli_service.run()


if __name__ == "__main__":
    main() 