import asyncio
import logging
from typing import Dict, Any, Optional
from ..services.xiaohongshu_service import XiaohongshuService

logger = logging.getLogger(__name__)

class HunterAPI:
    """Hunter API 接口层，提供统一的调用接口"""
    
    def __init__(self):
        self.service = XiaohongshuService()
        logger.info("HunterAPI 已初始化")
    
    async def initialize(self) -> Dict[str, Any]:
        """完整初始化服务（启动浏览器+登录）"""
        try:
            # 1. 启动浏览器
            logger.info("正在启动浏览器...")
            browser_success = await self.service.initialize()
            if not browser_success:
                return {"success": False, "message": "浏览器启动失败"}
            
            logger.info("浏览器启动成功")
            
            # 2. 检查登录状态，如果未登录则进行登录
            logger.info("检查登录状态...")
            if not self.service.is_logged_in():
                logger.info("需要登录，正在启动登录流程...")
                login_result = await self.service.login()
                if "成功" not in login_result and "已登录" not in login_result:
                    return {"success": False, "message": f"登录失败: {login_result}"}
                logger.info("登录流程完成")
            else:
                logger.info("已检测到登录状态")
            
            return {"success": True, "message": "Hunter 服务完整初始化成功（浏览器已启动并已登录）"}
            
        except Exception as e:
            logger.error(f"完整初始化异常: {e}")
            return {"success": False, "message": f"完整初始化异常: {str(e)}"}
    
    async def login(self) -> Dict[str, Any]:
        """单独登录小红书账号（如果只需要登录）"""
        try:
            result = await self.service.login()
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_notes(self, keywords: str, limit: int = 5) -> Dict[str, Any]:
        """搜索笔记"""
        try:
            if not self.service.is_initialized():
                return {"success": False, "error": "服务未初始化，请先调用 initialize()"}
            
            if not self.service.is_logged_in():
                return {"success": False, "error": "未登录，请先调用 initialize() 或 login()"}
            
            result = await self.service.search_notes(keywords, limit)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"搜索笔记异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_note_content(self, url: str) -> Dict[str, Any]:
        """获取笔记内容"""
        try:
            if not self.service.is_initialized():
                return {"success": False, "error": "服务未初始化，请先调用 initialize()"}
            
            if not self.service.is_logged_in():
                return {"success": False, "error": "未登录，请先调用 initialize() 或 login()"}
            
            result = await self.service.get_note_content(url)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取笔记内容异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_note_comments(self, url: str) -> Dict[str, Any]:
        """获取笔记评论"""
        try:
            if not self.service.is_initialized():
                return {"success": False, "error": "服务未初始化，请先调用 initialize()"}
            
            if not self.service.is_logged_in():
                return {"success": False, "error": "未登录，请先调用 initialize() 或 login()"}
            
            result = await self.service.get_note_comments(url)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"获取笔记评论异常: {e}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            status = self.service.get_status()
            return {"success": True, "data": status}
        except Exception as e:
            logger.error(f"获取状态异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def shutdown(self) -> Dict[str, Any]:
        """关闭服务"""
        try:
            await self.service.shutdown()
            return {"success": True, "message": "Hunter 服务已关闭"}
        except Exception as e:
            logger.error(f"关闭服务异常: {e}")
            return {"success": False, "error": str(e)}

# 在模块底部添加全局唯一实例
api = HunterAPI() 