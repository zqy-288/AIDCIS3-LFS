"""
插件管理器实现
"""
import logging
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from .interfaces import Plugin, PluginInfo, PluginState
from .lifecycle import PluginLifecycle
from .utils import PluginError, PluginValidator


logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    _instance: Optional['PluginManager'] = None
    
    def __new__(cls) -> 'PluginManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化插件管理器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._plugins: Dict[str, Plugin] = {}
            self._lifecycles: Dict[str, PluginLifecycle] = {}
            self._plugin_paths: List[Path] = []
            self._validator = PluginValidator()
            logger.info("插件管理器初始化完成")
    
    def add_plugin_path(self, path: Path) -> None:
        """添加插件搜索路径"""
        if path not in self._plugin_paths:
            self._plugin_paths.append(path)
            logger.info(f"添加插件路径: {path}")
    
    def register_plugin(self, plugin: Plugin) -> None:
        """注册插件"""
        # 验证插件
        if not self._validator.validate(plugin):
            raise PluginError(f"插件验证失败")
        
        info = plugin.get_info()
        
        # 检查重复
        if info.name in self._plugins:
            raise PluginError(f"插件已存在: {info.name}")
        
        # 检查依赖
        for dep in info.dependencies:
            if dep not in self._plugins:
                raise PluginError(f"缺少依赖: {dep}")
        
        # 创建生命周期管理器
        lifecycle = PluginLifecycle(plugin)
        
        # 注册插件
        self._plugins[info.name] = plugin
        self._lifecycles[info.name] = lifecycle
        
        logger.info(f"注册插件: {info.name} v{info.version}")
    
    def unregister_plugin(self, name: str) -> None:
        """注销插件"""
        if name not in self._plugins:
            raise PluginError(f"插件不存在: {name}")
        
        # 停止插件
        lifecycle = self._lifecycles[name]
        if lifecycle.state == PluginState.RUNNING:
            lifecycle.stop()
        
        # 移除插件
        del self._plugins[name]
        del self._lifecycles[name]
        
        logger.info(f"注销插件: {name}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件实例"""
        return self._plugins.get(name)
    
    def get_plugins(self, plugin_type: Optional[Type[Plugin]] = None) -> List[Plugin]:
        """获取所有插件或指定类型的插件"""
        plugins = list(self._plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if isinstance(p, plugin_type)]
        
        return plugins
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        plugin = self._plugins.get(name)
        return plugin.get_info() if plugin else None
    
    def get_plugin_state(self, name: str) -> Optional[PluginState]:
        """获取插件状态"""
        lifecycle = self._lifecycles.get(name)
        return lifecycle.state if lifecycle else None
    
    def initialize_plugin(self, name: str) -> None:
        """初始化插件"""
        if name not in self._lifecycles:
            raise PluginError(f"插件不存在: {name}")
        
        self._lifecycles[name].initialize()
    
    def start_plugin(self, name: str) -> None:
        """启动插件"""
        if name not in self._lifecycles:
            raise PluginError(f"插件不存在: {name}")
        
        # 先启动依赖
        info = self._plugins[name].get_info()
        for dep in info.dependencies:
            if self._lifecycles[dep].state != PluginState.RUNNING:
                self.start_plugin(dep)
        
        # 如果插件未初始化，先初始化
        lifecycle = self._lifecycles[name]
        if lifecycle.state == PluginState.UNLOADED:
            lifecycle.initialize()
        
        lifecycle.start()
    
    def stop_plugin(self, name: str) -> None:
        """停止插件"""
        if name not in self._lifecycles:
            raise PluginError(f"插件不存在: {name}")
        
        # 先停止依赖它的插件
        for plugin_name, plugin in self._plugins.items():
            if name in plugin.get_info().dependencies:
                if self._lifecycles[plugin_name].state == PluginState.RUNNING:
                    self.stop_plugin(plugin_name)
        
        self._lifecycles[name].stop()
    
    def initialize_all(self) -> None:
        """初始化所有插件"""
        for name in self._plugins:
            try:
                self.initialize_plugin(name)
            except Exception as e:
                logger.error(f"初始化插件失败 {name}: {e}")
    
    def start_all(self) -> None:
        """启动所有插件"""
        # 按依赖顺序启动
        started = set()
        
        def start_with_deps(name: str):
            if name in started:
                return
            
            info = self._plugins[name].get_info()
            for dep in info.dependencies:
                start_with_deps(dep)
            
            try:
                self.start_plugin(name)
                started.add(name)
            except Exception as e:
                logger.error(f"启动插件失败 {name}: {e}")
        
        for name in self._plugins:
            start_with_deps(name)
    
    def stop_all(self) -> None:
        """停止所有插件"""
        # 按反向依赖顺序停止
        for name in reversed(list(self._plugins.keys())):
            if self._lifecycles[name].state == PluginState.RUNNING:
                try:
                    self.stop_plugin(name)
                except Exception as e:
                    logger.error(f"停止插件失败 {name}: {e}")
    
    def reload_plugin(self, name: str) -> None:
        """重新加载插件"""
        if name not in self._plugins:
            raise PluginError(f"插件不存在: {name}")
        
        # 保存插件实例
        plugin = self._plugins[name]
        
        # 停止并注销
        if self._lifecycles[name].state == PluginState.RUNNING:
            self.stop_plugin(name)
        self.unregister_plugin(name)
        
        # 重新注册并启动
        self.register_plugin(plugin)
        self.initialize_plugin(name)
        self.start_plugin(name)
        
        logger.info(f"重新加载插件: {name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        return {
            'total': len(self._plugins),
            'running': sum(1 for lc in self._lifecycles.values() if lc.state == PluginState.RUNNING),
            'stopped': sum(1 for lc in self._lifecycles.values() if lc.state == PluginState.STOPPED),
            'error': sum(1 for lc in self._lifecycles.values() if lc.state == PluginState.ERROR),
            'plugins': {
                name: {
                    'state': lc.state.value,
                    'version': self._plugins[name].get_info().version
                }
                for name, lc in self._lifecycles.items()
            }
        }


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager