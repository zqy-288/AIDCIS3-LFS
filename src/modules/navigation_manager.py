"""
导航管理器模块
实现页面间的导航功能，支持带参数的页面切换
提供快速跳转到实时监控、历史数据等功能
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


class NavigationTarget(Enum):
    """导航目标枚举"""
    MAIN_DETECTION = "main_detection"
    REALTIME_PREVIEW = "realtime_preview"
    HISTORY_VIEW = "history_view"
    REPORT_OUTPUT = "report_output"


@dataclass
class NavigationContext:
    """导航上下文"""
    target: NavigationTarget
    parameters: Dict[str, Any]
    source_view: Optional[str] = None
    timestamp: Optional[float] = None
    

class NavigationManager(QObject):
    """导航管理器类"""
    
    # 信号定义
    navigation_requested = Signal(str, dict)  # target, parameters
    navigation_completed = Signal(str)  # target
    navigation_failed = Signal(str, str)  # target, error
    back_navigation_available = Signal(bool)  # has_back_history
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 导航历史
        self.navigation_history: List[NavigationContext] = []
        self.current_index = -1
        self.max_history_size = 50
        
        self.logger.info("🧭 导航管理器初始化完成")
    
    def navigate_to_realtime(self, hole_id: Optional[str] = None, **kwargs) -> bool:
        """跳转到实时监控页面"""
        try:
            parameters = {'hole_id': hole_id} if hole_id else {}
            parameters.update(kwargs)
            
            return self._navigate_to(NavigationTarget.REALTIME_PREVIEW, parameters)
            
        except Exception as e:
            self.logger.error(f"❌ 跳转到实时监控失败: {e}")
            self.navigation_failed.emit(NavigationTarget.REALTIME_PREVIEW.value, str(e))
            return False
    
    def navigate_to_history(self, hole_id: Optional[str] = None, batch_id: Optional[str] = None, **kwargs) -> bool:
        """跳转到历史数据页面"""
        try:
            parameters = {}
            if hole_id:
                parameters['hole_id'] = hole_id
            if batch_id:
                parameters['batch_id'] = batch_id
            parameters.update(kwargs)
            
            return self._navigate_to(NavigationTarget.HISTORY_VIEW, parameters)
            
        except Exception as e:
            self.logger.error(f"❌ 跳转到历史数据失败: {e}")
            self.navigation_failed.emit(NavigationTarget.HISTORY_VIEW.value, str(e))
            return False
    
    def navigate_to_report(self, workpiece_id: Optional[str] = None, **kwargs) -> bool:
        """跳转到报告输出页面"""
        try:
            parameters = {'workpiece_id': workpiece_id} if workpiece_id else {}
            parameters.update(kwargs)
            
            return self._navigate_to(NavigationTarget.REPORT_OUTPUT, parameters)
            
        except Exception as e:
            self.logger.error(f"❌ 跳转到报告输出失败: {e}")
            self.navigation_failed.emit(NavigationTarget.REPORT_OUTPUT.value, str(e))
            return False
    
    def navigate_to_main_detection(self, **kwargs) -> bool:
        """跳转到主检测视图"""
        try:
            return self._navigate_to(NavigationTarget.MAIN_DETECTION, kwargs)
            
        except Exception as e:
            self.logger.error(f"❌ 跳转到主检测视图失败: {e}")
            self.navigation_failed.emit(NavigationTarget.MAIN_DETECTION.value, str(e))
            return False
    
    def navigate_back(self) -> bool:
        """返回上一页"""
        try:
            if not self.can_navigate_back():
                self.logger.warning("⚠️ 无法返回上一页，没有历史记录")
                return False
            
            # 移动到上一个位置
            self.current_index -= 1
            if self.current_index >= 0:
                context = self.navigation_history[self.current_index]
                
                # 执行导航但不添加到历史记录
                self._do_navigation(context.target, context.parameters, add_to_history=False)
                
                self.logger.info(f"⬅️ 返回到: {context.target.value}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 返回导航失败: {e}")
            return False
    
    def navigate_forward(self) -> bool:
        """前进到下一页"""
        try:
            if not self.can_navigate_forward():
                return False
            
            # 移动到下一个位置
            self.current_index += 1
            if self.current_index < len(self.navigation_history):
                context = self.navigation_history[self.current_index]
                
                # 执行导航但不添加到历史记录
                self._do_navigation(context.target, context.parameters, add_to_history=False)
                
                self.logger.info(f"➡️ 前进到: {context.target.value}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 前进导航失败: {e}")
            return False
    
    def can_navigate_back(self) -> bool:
        """检查是否可以返回"""
        return self.current_index > 0
    
    def can_navigate_forward(self) -> bool:
        """检查是否可以前进"""
        return self.current_index < len(self.navigation_history) - 1
    
    def get_navigation_history(self) -> List[NavigationContext]:
        """获取导航历史"""
        return self.navigation_history.copy()
    
    def clear_history(self):
        """清空导航历史"""
        self.navigation_history.clear()
        self.current_index = -1
        self.back_navigation_available.emit(False)
        self.logger.info("🗑️ 导航历史已清空")
    
    def get_current_context(self) -> Optional[NavigationContext]:
        """获取当前导航上下文"""
        if 0 <= self.current_index < len(self.navigation_history):
            return self.navigation_history[self.current_index]
        return None
    
    def _navigate_to(self, target: NavigationTarget, parameters: Dict[str, Any]) -> bool:
        """内部导航方法"""
        return self._do_navigation(target, parameters, add_to_history=True)
    
    def _do_navigation(self, target: NavigationTarget, parameters: Dict[str, Any], add_to_history: bool = True) -> bool:
        """执行导航"""
        try:
            import time
            
            # 创建导航上下文
            context = NavigationContext(
                target=target,
                parameters=parameters,
                timestamp=time.time()
            )
            
            # 添加到历史记录
            if add_to_history:
                self._add_to_history(context)
            
            # 发出导航请求信号
            self.navigation_requested.emit(target.value, parameters)
            
            self.logger.info(f"🧭 导航到: {target.value}, 参数: {parameters}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 执行导航失败: {e}")
            return False
    
    def _add_to_history(self, context: NavigationContext):
        """添加到导航历史"""
        try:
            # 如果当前不在历史末尾，移除后续的历史记录
            if self.current_index < len(self.navigation_history) - 1:
                self.navigation_history = self.navigation_history[:self.current_index + 1]
            
            # 添加新的上下文
            self.navigation_history.append(context)
            self.current_index = len(self.navigation_history) - 1
            
            # 限制历史记录大小
            if len(self.navigation_history) > self.max_history_size:
                self.navigation_history.pop(0)
                self.current_index -= 1
            
            # 发出返回可用性信号
            self.back_navigation_available.emit(self.can_navigate_back())
            
        except Exception as e:
            self.logger.error(f"❌ 添加导航历史失败: {e}")
    
    def on_navigation_completed(self, target: str):
        """导航完成回调"""
        self.navigation_completed.emit(target)
        self.logger.debug(f"✅ 导航完成: {target}")


class QuickNavigationHelper:
    """快速导航助手类"""
    
    def __init__(self, navigation_manager: NavigationManager):
        self.nav_manager = navigation_manager
        self.logger = logging.getLogger(__name__)
    
    def quick_jump_to_hole_realtime(self, hole_id: str) -> bool:
        """快速跳转到指定孔位的实时监控"""
        return self.nav_manager.navigate_to_realtime(
            hole_id=hole_id,
            auto_focus=True,
            show_details=True
        )
    
    def quick_jump_to_hole_history(self, hole_id: str) -> bool:
        """快速跳转到指定孔位的历史数据"""
        return self.nav_manager.navigate_to_history(
            hole_id=hole_id,
            auto_focus=True,
            show_timeline=True
        )
    
    def quick_jump_to_batch_history(self, batch_id: str) -> bool:
        """快速跳转到指定批次的历史数据"""
        return self.nav_manager.navigate_to_history(
            batch_id=batch_id,
            view_mode="batch",
            show_summary=True
        )
    
    def quick_generate_hole_report(self, hole_id: str) -> bool:
        """快速生成指定孔位的报告"""
        return self.nav_manager.navigate_to_report(
            workpiece_id=hole_id,
            report_type="hole_detail",
            auto_generate=True
        )
    
    def quick_generate_batch_report(self, batch_id: str) -> bool:
        """快速生成批次报告"""
        return self.nav_manager.navigate_to_report(
            workpiece_id=batch_id,
            report_type="batch_summary",
            auto_generate=True
        )
    
    def create_custom_navigation_shortcut(self, name: str, target: NavigationTarget, parameters: Dict[str, Any]):
        """创建自定义导航快捷方式"""
        def shortcut_func():
            return self.nav_manager._navigate_to(target, parameters)
        
        shortcut_func.__name__ = f"shortcut_{name}"
        return shortcut_func


# 全局导航管理器实例
_global_navigation_manager = None

def get_navigation_manager() -> NavigationManager:
    """获取全局导航管理器实例"""
    global _global_navigation_manager
    if _global_navigation_manager is None:
        _global_navigation_manager = NavigationManager()
    return _global_navigation_manager

def get_quick_navigation_helper() -> QuickNavigationHelper:
    """获取快速导航助手实例"""
    nav_manager = get_navigation_manager()
    return QuickNavigationHelper(nav_manager)


# 导出的公共接口
__all__ = [
    'NavigationManager',
    'NavigationTarget',
    'NavigationContext',
    'QuickNavigationHelper',
    'get_navigation_manager',
    'get_quick_navigation_helper'
]