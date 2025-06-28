import asyncio
import logging
import threading
from typing import Optional, Dict, Any
from .browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class XiaohongshuService:
    """小红书服务单例类，管理浏览器实例和状态"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.browser_manager = BrowserManager()
            self._initialized = True
            logger.info("XiaohongshuService 单例已创建")
    
    async def initialize(self) -> bool:
        """初始化浏览器实例"""
        try:
            success = await self.browser_manager.initialize()
            if success:
                logger.info("XiaohongshuService 初始化成功")
            else:
                logger.error("XiaohongshuService 初始化失败")
            return success
        except Exception as e:
            logger.error(f"XiaohongshuService 初始化异常: {e}")
            return False
    
    async def login(self) -> str:
        """登录小红书账号"""
        try:
            result = await self.browser_manager.login()
            logger.info(f"登录结果: {result}")
            return result
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return f"登录异常: {str(e)}"
    
    async def search_notes(self, keywords: str, limit: int = 5) -> str:
        """搜索笔记"""
        try:
            result = await self.browser_manager.search_notes(keywords, limit)
            logger.info(f"搜索完成，关键词: {keywords}, 结果数量: {limit}")
            return result
        except Exception as e:
            logger.error(f"搜索异常: {e}")
            return f"搜索异常: {str(e)}"
    
    async def get_note_content(self, url: str) -> str:
        """获取笔记内容"""
        try:
            result = await self.browser_manager.get_note_content(url)
            logger.info(f"获取笔记内容完成，URL: {url}")
            return result
        except Exception as e:
            logger.error(f"获取笔记内容异常: {e}")
            return f"获取笔记内容异常: {str(e)}"
    
    async def get_note_comments(self, url: str) -> str:
        """获取笔记评论"""
        try:
            result = await self.browser_manager.get_note_comments(url)
            logger.info(f"获取笔记评论完成，URL: {url}")
            return result
        except Exception as e:
            logger.error(f"获取笔记评论异常: {e}")
            return f"获取笔记评论异常: {str(e)}"
    
    async def shutdown(self):
        """关闭服务"""
        try:
            await self.browser_manager.shutdown()
            logger.info("XiaohongshuService 已关闭")
        except Exception as e:
            logger.error(f"关闭服务异常: {e}")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.browser_manager.is_initialized()
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.browser_manager.is_logged_in
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "initialized": self.is_initialized(),
            "logged_in": self.is_logged_in(),
            "browser_ready": self.browser_manager.browser_context is not None
        } 