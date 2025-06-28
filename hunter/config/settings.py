import os
from pathlib import Path

class HunterConfig:
    """Hunter 模块配置类"""
    
    # 基础路径配置
    BASE_DIR = Path(__file__).resolve().parent.parent
    BROWSER_DATA_DIR = BASE_DIR / "browser_data"
    DATA_DIR = BASE_DIR / "data"
    
    # 浏览器配置
    BROWSER_HEADLESS = False
    BROWSER_TIMEOUT = 60000
    BROWSER_VIEWPORT = {"width": 1280, "height": 800}
    
    # 服务配置
    SERVICE_HOST = "localhost"
    SERVICE_PORT = 8001
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = BASE_DIR / "hunter.log"
    
    # 小红书配置
    XIAOHONGSHU_BASE_URL = "https://www.xiaohongshu.com"
    XIAOHONGSHU_LOGIN_TIMEOUT = 180  # 登录等待时间（秒）
    
    # 搜索配置
    DEFAULT_SEARCH_LIMIT = 5
    SEARCH_WAIT_TIME = 5  # 搜索页面等待时间
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        cls.BROWSER_DATA_DIR.mkdir(exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOG_FILE.parent.mkdir(exist_ok=True) 