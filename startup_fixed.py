#!/usr/bin/env python3
"""
修复后的统一启动脚本
解决重复初始化问题，确保组件只被创建一次
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主启动函数 - 确保只有一个初始化路径"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 启动AIDCIS3-LFS (修复版)")
    print("🔧 使用单例模式避免重复初始化")
    
    try:
        # 清理可能的重复实例
        from core.singleton_manager import SingletonManager
        SingletonManager.clear_all()
        
        # 使用ApplicationCore作为唯一入口
        from core.application import get_application
        
        app = get_application()
        
        # 初始化应用程序
        if not app.initialize():
            logger.error("应用程序初始化失败")
            return 1
        
        logger.info("✅ 应用程序初始化成功")
        
        # 运行应用程序
        exit_code = app.run()
        
        # 清理单例
        SingletonManager.clear_all()
        
        return exit_code
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
