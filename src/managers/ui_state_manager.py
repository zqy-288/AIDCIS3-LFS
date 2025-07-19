"""
UI状态管理器
负责管理和持久化用户界面状态，包括窗口大小、位置、分割器位置等
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QTabWidget, QTableWidget,
    QTreeWidget, QHeaderView, QApplication
)
from PySide6.QtCore import QObject, Signal, QSettings, QTimer, QRect, QSize, QPoint
from PySide6.QtGui import QScreen


class UIState:
    """UI状态数据类"""
    
    def __init__(self):
        # 窗口状态
        self.window_geometry: Optional[QRect] = None
        self.window_state: Optional[bytes] = None
        self.is_maximized: bool = False
        self.is_fullscreen: bool = False
        
        # 分割器状态
        self.splitter_sizes: Dict[str, List[int]] = {}
        
        # 选项卡状态
        self.active_tab_index: int = 0
        self.tab_order: List[str] = []
        
        # 表格状态
        self.table_column_widths: Dict[str, List[int]] = {}
        self.table_column_order: Dict[str, List[int]] = {}
        self.table_sort_column: Dict[str, int] = {}
        self.table_sort_order: Dict[str, int] = {}
        
        # 树状视图状态
        self.tree_expanded_items: Dict[str, List[str]] = {}
        self.tree_column_widths: Dict[str, List[int]] = {}
        
        # 用户偏好设置
        self.preferences: Dict[str, Any] = {}
        
        # 自定义数据
        self.custom_data: Dict[str, Any] = {}


class UIStateManager(QObject):
    """UI状态管理器类"""
    
    # 信号定义
    state_saved = Signal(str)  # 状态保存完成信号
    state_restored = Signal(str)  # 状态恢复完成信号
    preferences_changed = Signal(dict)  # 偏好设置改变信号
    
    def __init__(self, app_name: str = "AIDCIS3-LFS", parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 基础配置
        self.app_name = app_name
        self.settings = QSettings("AIDCIS", app_name)
        
        # 状态管理
        self._ui_state = UIState()
        self._monitored_widgets: Dict[str, QWidget] = {}
        self._splitter_widgets: Dict[str, QSplitter] = {}
        self._table_widgets: Dict[str, QTableWidget] = {}
        self._tree_widgets: Dict[str, QTreeWidget] = {}
        
        # 自动保存配置
        self._auto_save_enabled = True
        self._auto_save_interval = 5000  # 5秒
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save_state)
        
        # 状态变化跟踪
        self._state_changed = False
        self._last_save_time = None
        
        # 多显示器支持
        self._screen_geometries: Dict[int, QRect] = {}
        self._update_screen_info()
        
        # 默认偏好设置
        self._default_preferences = {
            'auto_save_state': True,
            'restore_window_position': True,
            'restore_splitter_sizes': True,
            'restore_table_columns': True,
            'remember_last_tab': True,
            'save_custom_layouts': True,
            'theme': 'dark',
            'language': 'zh_CN',
            'check_updates': True,
            'show_tips': True,
            'confirm_exit': True
        }
        
        self.logger.info("UI状态管理器初始化完成")
    
    def save_window_state(self, window: QMainWindow, window_id: str = "main") -> bool:
        """保存窗口状态"""
        try:
            if not isinstance(window, QMainWindow):
                self.logger.warning("只支持QMainWindow类型的窗口")
                return False
            
            # 保存窗口几何信息
            self._ui_state.window_geometry = window.geometry()
            self._ui_state.window_state = window.saveState()
            self._ui_state.is_maximized = window.isMaximized()
            self._ui_state.is_fullscreen = window.isFullScreen()
            
            # 保存到QSettings
            self.settings.beginGroup(f"window/{window_id}")
            
            if not window.isMaximized() and not window.isFullScreen():
                self.settings.setValue("geometry", window.geometry())
            
            self.settings.setValue("state", window.saveState())
            self.settings.setValue("maximized", window.isMaximized())
            self.settings.setValue("fullscreen", window.isFullScreen())
            
            # 保存多显示器信息
            screen = window.screen()
            if screen:
                screen_name = screen.name()
                self.settings.setValue("screen", screen_name)
                self.settings.setValue("screen_geometry", screen.geometry())
            
            self.settings.endGroup()
            
            self.logger.info(f"窗口状态已保存: {window_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存窗口状态失败: {e}")
            return False
    
    def restore_window_state(self, window: QMainWindow, window_id: str = "main") -> bool:
        """恢复窗口状态"""
        try:
            if not isinstance(window, QMainWindow):
                self.logger.warning("只支持QMainWindow类型的窗口")
                return False
            
            self.settings.beginGroup(f"window/{window_id}")
            
            # 恢复窗口几何信息
            geometry = self.settings.value("geometry")
            state = self.settings.value("state")
            maximized = self.settings.value("maximized", False, type=bool)
            fullscreen = self.settings.value("fullscreen", False, type=bool)
            
            # 多显示器支持
            saved_screen = self.settings.value("screen", "")
            saved_screen_geometry = self.settings.value("screen_geometry")
            
            self.settings.endGroup()
            
            # 验证屏幕配置
            if geometry and self._is_geometry_valid(geometry, saved_screen, saved_screen_geometry):
                window.setGeometry(geometry)
            else:
                # 使用默认大小并居中
                self._center_window(window)
            
            # 恢复窗口状态
            if state:
                window.restoreState(state)
            
            # 恢复最大化/全屏状态
            if fullscreen:
                window.showFullScreen()
            elif maximized:
                window.showMaximized()
            
            self.logger.info(f"窗口状态已恢复: {window_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复窗口状态失败: {e}")
            return False
    
    def save_splitter_state(self, splitter: QSplitter, splitter_id: str):
        """保存分割器状态"""
        try:
            sizes = splitter.sizes()
            self._ui_state.splitter_sizes[splitter_id] = sizes
            
            self.settings.beginGroup("splitters")
            self.settings.setValue(splitter_id, sizes)
            self.settings.endGroup()
            
            self.logger.debug(f"分割器状态已保存: {splitter_id} -> {sizes}")
            
        except Exception as e:
            self.logger.error(f"保存分割器状态失败: {e}")
    
    def restore_splitter_state(self, splitter: QSplitter, splitter_id: str) -> bool:
        """恢复分割器状态"""
        try:
            self.settings.beginGroup("splitters")
            sizes = self.settings.value(splitter_id)
            self.settings.endGroup()
            
            if sizes and isinstance(sizes, list) and len(sizes) == splitter.count():
                # 确保所有大小都是正数
                valid_sizes = [max(size, 50) for size in sizes if isinstance(size, int)]
                if len(valid_sizes) == len(sizes):
                    splitter.setSizes(valid_sizes)
                    self._ui_state.splitter_sizes[splitter_id] = valid_sizes
                    self.logger.debug(f"分割器状态已恢复: {splitter_id} -> {valid_sizes}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"恢复分割器状态失败: {e}")
            return False
    
    def save_table_state(self, table: QTableWidget, table_id: str):
        """保存表格状态"""
        try:
            header = table.horizontalHeader()
            
            # 保存列宽
            column_widths = []
            for i in range(table.columnCount()):
                column_widths.append(header.sectionSize(i))
            
            self._ui_state.table_column_widths[table_id] = column_widths
            
            # 保存列顺序
            column_order = []
            for i in range(table.columnCount()):
                column_order.append(header.visualIndex(i))
            
            self._ui_state.table_column_order[table_id] = column_order
            
            # 保存排序状态
            self._ui_state.table_sort_column[table_id] = table.sortColumn()
            self._ui_state.table_sort_order[table_id] = table.sortOrder()
            
            # 保存到QSettings
            self.settings.beginGroup(f"tables/{table_id}")
            self.settings.setValue("column_widths", column_widths)
            self.settings.setValue("column_order", column_order)
            self.settings.setValue("sort_column", table.sortColumn())
            self.settings.setValue("sort_order", int(table.sortOrder()))
            self.settings.endGroup()
            
            self.logger.debug(f"表格状态已保存: {table_id}")
            
        except Exception as e:
            self.logger.error(f"保存表格状态失败: {e}")
    
    def restore_table_state(self, table: QTableWidget, table_id: str) -> bool:
        """恢复表格状态"""
        try:
            self.settings.beginGroup(f"tables/{table_id}")
            
            column_widths = self.settings.value("column_widths")
            column_order = self.settings.value("column_order")
            sort_column = self.settings.value("sort_column", -1, type=int)
            sort_order = self.settings.value("sort_order", 0, type=int)
            
            self.settings.endGroup()
            
            header = table.horizontalHeader()
            
            # 恢复列宽
            if column_widths and len(column_widths) == table.columnCount():
                for i, width in enumerate(column_widths):
                    if isinstance(width, int) and width > 0:
                        header.resizeSection(i, width)
            
            # 恢复列顺序
            if column_order and len(column_order) == table.columnCount():
                for logical_index, visual_index in enumerate(column_order):
                    if isinstance(visual_index, int):
                        header.moveSection(header.visualIndex(logical_index), visual_index)
            
            # 恢复排序状态
            if sort_column >= 0 and sort_column < table.columnCount():
                table.sortByColumn(sort_column, sort_order)
            
            self.logger.debug(f"表格状态已恢复: {table_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复表格状态失败: {e}")
            return False
    
    def save_tab_state(self, tab_widget: QTabWidget, tab_id: str = "main"):
        """保存选项卡状态"""
        try:
            current_index = tab_widget.currentIndex()
            self._ui_state.active_tab_index = current_index
            
            # 保存选项卡顺序
            tab_order = []
            for i in range(tab_widget.count()):
                tab_text = tab_widget.tabText(i)
                tab_order.append(tab_text)
            
            self._ui_state.tab_order = tab_order
            
            self.settings.beginGroup(f"tabs/{tab_id}")
            self.settings.setValue("current_index", current_index)
            self.settings.setValue("tab_order", tab_order)
            self.settings.endGroup()
            
            self.logger.debug(f"选项卡状态已保存: {tab_id} -> 索引{current_index}")
            
        except Exception as e:
            self.logger.error(f"保存选项卡状态失败: {e}")
    
    def restore_tab_state(self, tab_widget: QTabWidget, tab_id: str = "main") -> bool:
        """恢复选项卡状态"""
        try:
            self.settings.beginGroup(f"tabs/{tab_id}")
            
            current_index = self.settings.value("current_index", 0, type=int)
            tab_order = self.settings.value("tab_order", [])
            
            self.settings.endGroup()
            
            # 恢复当前选项卡
            if 0 <= current_index < tab_widget.count():
                tab_widget.setCurrentIndex(current_index)
                self._ui_state.active_tab_index = current_index
            
            # 恢复选项卡顺序（如果需要的话）
            self._ui_state.tab_order = tab_order
            
            self.logger.debug(f"选项卡状态已恢复: {tab_id} -> 索引{current_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复选项卡状态失败: {e}")
            return False
    
    def save_preferences(self, preferences: Dict[str, Any]):
        """保存用户偏好设置"""
        try:
            self._ui_state.preferences.update(preferences)
            
            self.settings.beginGroup("preferences")
            for key, value in preferences.items():
                self.settings.setValue(key, value)
            self.settings.endGroup()
            
            self.preferences_changed.emit(preferences)
            self.logger.info(f"偏好设置已保存: {len(preferences)} 项")
            
        except Exception as e:
            self.logger.error(f"保存偏好设置失败: {e}")
    
    def restore_preferences(self) -> Dict[str, Any]:
        """恢复用户偏好设置"""
        try:
            preferences = self._default_preferences.copy()
            
            self.settings.beginGroup("preferences")
            for key in self.settings.allKeys():
                value = self.settings.value(key)
                if key in preferences:
                    # 保持默认值的类型
                    if isinstance(preferences[key], bool):
                        value = self.settings.value(key, False, type=bool)
                    elif isinstance(preferences[key], int):
                        value = self.settings.value(key, 0, type=int)
                    elif isinstance(preferences[key], float):
                        value = self.settings.value(key, 0.0, type=float)
                
                preferences[key] = value
            
            self.settings.endGroup()
            
            self._ui_state.preferences = preferences
            self.logger.info(f"偏好设置已恢复: {len(preferences)} 项")
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"恢复偏好设置失败: {e}")
            return self._default_preferences.copy()
    
    def register_widget(self, widget_id: str, widget: QWidget):
        """注册要监控的组件"""
        self._monitored_widgets[widget_id] = widget
        
        # 根据组件类型进行特殊处理
        if isinstance(widget, QSplitter):
            self._splitter_widgets[widget_id] = widget
            widget.splitterMoved.connect(lambda: self._on_splitter_moved(widget_id))
        
        elif isinstance(widget, QTableWidget):
            self._table_widgets[widget_id] = widget
            # 监控表格状态变化
            header = widget.horizontalHeader()
            header.sectionResized.connect(lambda: self._on_table_changed(widget_id))
            header.sectionMoved.connect(lambda: self._on_table_changed(widget_id))
        
        elif isinstance(widget, QTreeWidget):
            self._tree_widgets[widget_id] = widget
            widget.itemExpanded.connect(lambda: self._on_tree_changed(widget_id))
            widget.itemCollapsed.connect(lambda: self._on_tree_changed(widget_id))
        
        self.logger.debug(f"组件已注册: {widget_id} ({type(widget).__name__})")
    
    def unregister_widget(self, widget_id: str):
        """取消注册组件"""
        self._monitored_widgets.pop(widget_id, None)
        self._splitter_widgets.pop(widget_id, None)
        self._table_widgets.pop(widget_id, None)
        self._tree_widgets.pop(widget_id, None)
    
    def save_all_states(self):
        """保存所有状态"""
        try:
            # 保存分割器状态
            for splitter_id, splitter in self._splitter_widgets.items():
                self.save_splitter_state(splitter, splitter_id)
            
            # 保存表格状态
            for table_id, table in self._table_widgets.items():
                self.save_table_state(table, table_id)
            
            # 保存自定义数据
            if self._ui_state.custom_data:
                self.settings.beginGroup("custom_data")
                for key, value in self._ui_state.custom_data.items():
                    self.settings.setValue(key, value)
                self.settings.endGroup()
            
            # 同步到磁盘
            self.settings.sync()
            
            from datetime import datetime
            self._last_save_time = datetime.now()
            self._state_changed = False
            
            self.state_saved.emit("all")
            self.logger.info("所有状态已保存")
            
        except Exception as e:
            self.logger.error(f"保存所有状态失败: {e}")
    
    def restore_all_states(self):
        """恢复所有状态"""
        try:
            # 恢复分割器状态
            for splitter_id, splitter in self._splitter_widgets.items():
                self.restore_splitter_state(splitter, splitter_id)
            
            # 恢复表格状态
            for table_id, table in self._table_widgets.items():
                self.restore_table_state(table, table_id)
            
            # 恢复自定义数据
            self.settings.beginGroup("custom_data")
            for key in self.settings.allKeys():
                value = self.settings.value(key)
                self._ui_state.custom_data[key] = value
            self.settings.endGroup()
            
            self.state_restored.emit("all")
            self.logger.info("所有状态已恢复")
            
        except Exception as e:
            self.logger.error(f"恢复所有状态失败: {e}")
    
    def set_custom_data(self, key: str, value: Any):
        """设置自定义数据"""
        self._ui_state.custom_data[key] = value
        self._mark_state_changed()
    
    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """获取自定义数据"""
        return self._ui_state.custom_data.get(key, default)
    
    def enable_auto_save(self, enabled: bool, interval: int = 5000):
        """启用/禁用自动保存"""
        self._auto_save_enabled = enabled
        self._auto_save_interval = max(1000, interval)  # 最小1秒
        
        if enabled:
            self._auto_save_timer.start(self._auto_save_interval)
            self.logger.info(f"自动保存已启用，间隔: {interval}ms")
        else:
            self._auto_save_timer.stop()
            self.logger.info("自动保存已禁用")
    
    def clear_all_states(self):
        """清除所有保存的状态"""
        try:
            self.settings.clear()
            self._ui_state = UIState()
            self.logger.info("所有状态已清除")
            
        except Exception as e:
            self.logger.error(f"清除状态失败: {e}")
    
    def export_settings(self, file_path: str) -> bool:
        """导出设置到文件"""
        try:
            # 这里可以实现设置导出功能
            self.logger.info(f"设置导出功能待实现: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出设置失败: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """从文件导入设置"""
        try:
            # 这里可以实现设置导入功能
            self.logger.info(f"设置导入功能待实现: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导入设置失败: {e}")
            return False
    
    def _update_screen_info(self):
        """更新屏幕信息"""
        try:
            app = QApplication.instance()
            if app:
                screens = app.screens()
                self._screen_geometries.clear()
                
                for i, screen in enumerate(screens):
                    self._screen_geometries[i] = screen.geometry()
                
                self.logger.debug(f"屏幕信息已更新: {len(screens)} 个屏幕")
        
        except Exception as e:
            self.logger.error(f"更新屏幕信息失败: {e}")
    
    def _is_geometry_valid(self, geometry: QRect, screen_name: str = "", 
                          saved_screen_geometry: QRect = None) -> bool:
        """验证几何信息是否有效"""
        try:
            app = QApplication.instance()
            if not app:
                return False
            
            # 检查是否在任何屏幕范围内
            screens = app.screens()
            for screen in screens:
                screen_rect = screen.geometry()
                
                # 检查窗口是否至少有一部分在屏幕内
                if screen_rect.intersects(geometry):
                    # 检查窗口大小是否合理
                    if (geometry.width() >= 100 and geometry.height() >= 100 and
                        geometry.width() <= screen_rect.width() * 2 and
                        geometry.height() <= screen_rect.height() * 2):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"验证几何信息失败: {e}")
            return False
    
    def _center_window(self, window: QMainWindow):
        """将窗口居中显示"""
        try:
            app = QApplication.instance()
            if app:
                screen = app.primaryScreen()
                if screen:
                    screen_geometry = screen.geometry()
                    
                    # 设置默认大小（屏幕的80%）
                    width = int(screen_geometry.width() * 0.8)
                    height = int(screen_geometry.height() * 0.8)
                    
                    # 计算居中位置
                    x = (screen_geometry.width() - width) // 2
                    y = (screen_geometry.height() - height) // 2
                    
                    window.setGeometry(x, y, width, height)
                    
        except Exception as e:
            self.logger.error(f"居中窗口失败: {e}")
    
    def _mark_state_changed(self):
        """标记状态已改变"""
        self._state_changed = True
    
    def _on_splitter_moved(self, splitter_id: str):
        """处理分割器移动事件"""
        self._mark_state_changed()
        if self._auto_save_enabled:
            splitter = self._splitter_widgets.get(splitter_id)
            if splitter:
                self.save_splitter_state(splitter, splitter_id)
    
    def _on_table_changed(self, table_id: str):
        """处理表格状态改变事件"""
        self._mark_state_changed()
        if self._auto_save_enabled:
            # 延迟保存以避免频繁操作
            QTimer.singleShot(1000, lambda: self._save_table_delayed(table_id))
    
    def _on_tree_changed(self, tree_id: str):
        """处理树状视图改变事件"""
        self._mark_state_changed()
    
    def _save_table_delayed(self, table_id: str):
        """延迟保存表格状态"""
        table = self._table_widgets.get(table_id)
        if table:
            self.save_table_state(table, table_id)
    
    def _auto_save_state(self):
        """自动保存状态"""
        if self._state_changed:
            self.save_all_states()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取偏好设置"""
        return self._ui_state.preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """设置偏好设置"""
        self._ui_state.preferences[key] = value
        self.save_preferences({key: value})
    
    def cleanup(self):
        """清理资源"""
        if self._auto_save_enabled and self._state_changed:
            self.save_all_states()
        
        self._auto_save_timer.stop()
        self._monitored_widgets.clear()
        self._splitter_widgets.clear()
        self._table_widgets.clear()
        self._tree_widgets.clear()
        
        self.logger.info("UI状态管理器清理完成")