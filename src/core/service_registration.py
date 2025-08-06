"""
服务注册模块
负责在应用启动时注册所有必要的服务到依赖注入容器
"""

import logging
from .dependency_injection import get_container, ServiceLifetime


def register_core_services():
    """注册核心服务到依赖注入容器"""
    logger = logging.getLogger(__name__)
    container = get_container()
    
    try:
        # 数据访问层和仓库已移除，使用新的数据管理方式
        
        # 业务缓存和规则引擎已整合到其他服务中
        
        logger.info("🎯 所有核心服务注册完成")
        
    except Exception as e:
        logger.error(f"❌ 服务注册失败: {e}")
        raise


def register_application_services():
    """注册应用程序级别的服务"""
    logger = logging.getLogger(__name__)
    container = get_container()
    
    try:
        # 这里可以注册应用程序特定的服务
        # 比如：主题管理器、数据监控器等
        
        # 注册数据监控器
        from src.shared.utils.monitoring.data_monitor import DataFolderMonitor
        container.register_singleton(DataFolderMonitor)
        logger.info("✅ DataFolderMonitor 注册成功")
        
    except Exception as e:
        logger.error(f"❌ 应用服务注册失败: {e}")


def initialize_services():
    """初始化所有服务"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 开始注册核心服务...")
        register_core_services()
        
        logger.info("🚀 开始注册应用服务...")
        register_application_services()
        
        logger.info("✅ 所有服务初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        return False