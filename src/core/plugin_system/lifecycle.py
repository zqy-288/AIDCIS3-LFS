"""
插件生命周期管理
"""
import logging
import time
from typing import Optional, Callable, Dict, Any
from .interfaces import Plugin, PluginState
from .utils import PluginError


logger = logging.getLogger(__name__)


class PluginLifecycle:
    """插件生命周期管理器"""
    
    def __init__(self, plugin: Plugin):
        """初始化生命周期管理器"""
        self._plugin = plugin
        self._state = PluginState.UNLOADED
        self._error: Optional[Exception] = None
        self._start_time: Optional[float] = None
        self._hooks: Dict[str, Callable] = {}
        
    @property
    def state(self) -> PluginState:
        """获取当前状态"""
        return self._state
    
    @property
    def error(self) -> Optional[Exception]:
        """获取错误信息"""
        return self._error
    
    @property
    def uptime(self) -> float:
        """获取运行时间（秒）"""
        if self._start_time and self._state == PluginState.RUNNING:
            return time.time() - self._start_time
        return 0.0
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """添加生命周期钩子"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
    
    def _trigger_hook(self, event: str, **kwargs) -> None:
        """触发钩子"""
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(self._plugin, **kwargs)
                except Exception as e:
                    logger.error(f"钩子执行失败 {event}: {e}")
    
    def _transition_to(self, state: PluginState) -> None:
        """状态转换"""
        old_state = self._state
        self._state = state
        logger.info(f"插件 {self._plugin.get_info().name} 状态转换: {old_state.value} -> {state.value}")
        self._trigger_hook('state_changed', old_state=old_state, new_state=state)
    
    def initialize(self) -> None:
        """初始化插件"""
        if self._state not in [PluginState.UNLOADED, PluginState.LOADED]:
            raise PluginError(f"无法从 {self._state.value} 状态初始化")
        
        try:
            logger.info(f"初始化插件: {self._plugin.get_info().name}")
            self._trigger_hook('before_initialize')
            
            self._plugin.initialize()
            self._transition_to(PluginState.INITIALIZED)
            
            self._trigger_hook('after_initialize')
            
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")
            self._error = e
            self._transition_to(PluginState.ERROR)
            raise PluginError(f"初始化失败: {e}") from e
    
    def start(self) -> None:
        """启动插件"""
        if self._state == PluginState.RUNNING:
            logger.warning(f"插件已在运行: {self._plugin.get_info().name}")
            return
            
        if self._state not in [PluginState.INITIALIZED, PluginState.STOPPED]:
            raise PluginError(f"无法从 {self._state.value} 状态启动，请先初始化插件")
        
        try:
            logger.info(f"启动插件: {self._plugin.get_info().name}")
            self._trigger_hook('before_start')
            
            self._plugin.start()
            self._start_time = time.time()
            self._transition_to(PluginState.RUNNING)
            
            self._trigger_hook('after_start')
            
        except Exception as e:
            logger.error(f"插件启动失败: {e}")
            self._error = e
            self._transition_to(PluginState.ERROR)
            raise PluginError(f"启动失败: {e}") from e
    
    def stop(self) -> None:
        """停止插件"""
        if self._state != PluginState.RUNNING:
            logger.warning(f"插件未在运行: {self._plugin.get_info().name}")
            return
        
        try:
            logger.info(f"停止插件: {self._plugin.get_info().name}")
            self._trigger_hook('before_stop')
            
            self._plugin.stop()
            self._start_time = None
            self._transition_to(PluginState.STOPPED)
            
            self._trigger_hook('after_stop')
            
        except Exception as e:
            logger.error(f"插件停止失败: {e}")
            self._error = e
            self._transition_to(PluginState.ERROR)
            raise PluginError(f"停止失败: {e}") from e
    
    def restart(self) -> None:
        """重启插件"""
        logger.info(f"重启插件: {self._plugin.get_info().name}")
        
        if self._state == PluginState.RUNNING:
            self.stop()
        
        # 清除错误状态
        self._error = None
        
        # 重新初始化并启动
        if self._state in [PluginState.STOPPED, PluginState.ERROR]:
            self._transition_to(PluginState.UNLOADED)
        
        self.initialize()
        self.start()
    
    def get_status(self) -> Dict[str, Any]:
        """获取插件状态信息"""
        info = self._plugin.get_info()
        return {
            'name': info.name,
            'version': info.version,
            'state': self._state.value,
            'uptime': self.uptime,
            'error': str(self._error) if self._error else None,
            'dependencies': info.dependencies
        }