"""
插件系统工具类
"""
import importlib
import importlib.util
import logging
import inspect
from pathlib import Path
from typing import List, Type, Optional, Any
from .interfaces import Plugin, PluginInfo


logger = logging.getLogger(__name__)


class PluginError(Exception):
    """插件系统错误"""
    pass


class PluginValidator:
    """插件验证器"""
    
    def validate(self, plugin: Any) -> bool:
        """验证插件是否符合接口要求"""
        # 检查是否实现了必要的方法
        required_methods = ['get_info', 'initialize', 'start', 'stop']
        
        for method in required_methods:
            if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                logger.error(f"插件缺少必要方法: {method}")
                return False
        
        # 验证插件信息
        try:
            info = plugin.get_info()
            if not isinstance(info, PluginInfo):
                logger.error("get_info() 必须返回 PluginInfo 实例")
                return False
            
            # 验证必填字段
            if not info.name or not info.version:
                logger.error("插件名称和版本不能为空")
                return False
                
        except Exception as e:
            logger.error(f"获取插件信息失败: {e}")
            return False
        
        return True


class PluginLoader:
    """插件加载器"""
    
    @staticmethod
    def load_plugin_from_file(file_path: Path) -> Optional[Type[Plugin]]:
        """从文件加载插件类"""
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                file_path.stem, 
                file_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找插件类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        obj.__module__ == module.__name__ and
                        hasattr(obj, 'get_info') and
                        hasattr(obj, 'initialize') and
                        hasattr(obj, 'start') and
                        hasattr(obj, 'stop')):
                        logger.info(f"从 {file_path} 加载插件类: {name}")
                        return obj
                        
                logger.warning(f"在 {file_path} 中未找到有效的插件类")
                
        except Exception as e:
            logger.error(f"加载插件文件失败 {file_path}: {e}")
        
        return None
    
    @staticmethod
    def load_plugins_from_directory(directory: Path) -> List[Type[Plugin]]:
        """从目录加载所有插件"""
        plugins = []
        
        if not directory.exists():
            logger.warning(f"插件目录不存在: {directory}")
            return plugins
        
        # 查找所有 Python 文件
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith('_'):
                continue
                
            plugin_class = PluginLoader.load_plugin_from_file(file_path)
            if plugin_class:
                plugins.append(plugin_class)
        
        logger.info(f"从 {directory} 加载了 {len(plugins)} 个插件")
        return plugins
    
    @staticmethod
    def create_plugin_instance(plugin_class: Type[Plugin], *args, **kwargs) -> Plugin:
        """创建插件实例"""
        try:
            return plugin_class(*args, **kwargs)
        except Exception as e:
            raise PluginError(f"创建插件实例失败: {e}") from e


class PluginLogger:
    """插件日志工具"""
    
    @staticmethod
    def get_logger(plugin: Plugin) -> logging.Logger:
        """获取插件专用的日志记录器"""
        info = plugin.get_info()
        return logging.getLogger(f"plugin.{info.name}")
    
    @staticmethod
    def setup_plugin_logging(log_dir: Path) -> None:
        """设置插件日志"""
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置插件日志处理器
        handler = logging.FileHandler(log_dir / "plugins.log")
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        
        # 添加到插件日志记录器
        plugin_logger = logging.getLogger("plugin")
        plugin_logger.addHandler(handler)
        plugin_logger.setLevel(logging.INFO)