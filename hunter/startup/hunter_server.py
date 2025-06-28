#!/usr/bin/env python
# encoding: utf-8

import asyncio
import signal
import sys
import logging
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from hunter.api.hunter_api import HunterAPI
from hunter.config.settings import HunterConfig

# 配置日志
logging.basicConfig(
    level=getattr(logging, HunterConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(HunterConfig.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class HunterServer:
    """Hunter 独立服务器"""
    
    def __init__(self):
        self.api = HunterAPI()
        self.running = False
        self._shutdown_event = asyncio.Event()
        
        # 确保目录存在
        HunterConfig.ensure_directories()
    
    async def start(self):
        """启动服务"""
        logger.info("启动 Hunter 服务...")
        
        try:
            # 完整初始化服务（启动浏览器+登录）
            logger.info("开始完整初始化流程...")
            init_result = await self.api.initialize()
            if not init_result.get("success", False):
                logger.error(f"完整初始化失败: {init_result.get('message', '未知错误')}")
                return False
            
            logger.info(f"{init_result.get('message', '服务初始化成功')}")
            
            # 设置信号处理
            self._setup_signal_handlers()
            
            self.running = True
            logger.info("Hunter 服务已启动，等待调用...")
            logger.info("服务状态:")
            await self._print_status()
            
            # 保持服务运行
            while self.running and not self._shutdown_event.is_set():
                await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"启动服务失败: {e}")
            return False
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在关闭服务...")
            self.running = False
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _print_status(self):
        """打印服务状态"""
        try:
            status = self.api.get_status()
            if status.get("success", False):
                data = status.get("data", {})
                logger.info(f"   - 初始化状态: {'OK' if data.get('initialized') else 'FAIL'}")
                logger.info(f"   - 登录状态: {'OK' if data.get('logged_in') else 'FAIL'}")
                logger.info(f"   - 浏览器状态: {'OK' if data.get('browser_ready') else 'FAIL'}")
            else:
                logger.warning(f"   - 状态获取失败: {status.get('error', '未知错误')}")
        except Exception as e:
            logger.error(f"   - 状态获取异常: {e}")
    
    async def stop(self):
        """停止服务"""
        logger.info("正在停止 Hunter 服务...")
        
        try:
            # 关闭服务
            shutdown_result = await self.api.shutdown()
            if shutdown_result.get("success", False):
                logger.info("服务关闭成功")
            else:
                logger.warning(f"服务关闭警告: {shutdown_result.get('error', '未知错误')}")
                
        except Exception as e:
            logger.error(f"关闭服务异常: {e}")
        
        logger.info("Hunter 服务已停止")

async def main():
    """主函数"""
    server = HunterServer()
    
    try:
        success = await server.start()
        if not success:
            logger.error("服务启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
    except Exception as e:
        logger.error(f"服务运行异常: {e}")
    finally:
        await server.stop()

def run():
    """运行入口"""
    print("=" * 60)
    print("Hunter 独立服务")
    print("=" * 60)
    print(f"项目路径: {project_root}")
    print(f"浏览器数据: {HunterConfig.BROWSER_DATA_DIR}")
    print(f"日志文件: {HunterConfig.LOG_FILE}")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n再见！")
    except Exception as e:
        print(f"程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run() 