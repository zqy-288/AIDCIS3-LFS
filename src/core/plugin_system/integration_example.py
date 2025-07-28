"""
插件系统集成示例
展示如何在 main_window.py 中集成新的插件系统
"""
from typing import List, Dict, Any
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QAction
from .manager import get_plugin_manager
from .interfaces import UIPlugin
from .utils import PluginLoader, PluginLogger


class PluginIntegration:
    """插件系统集成助手类"""
    
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.plugin_manager = get_plugin_manager()
        self.plugin_actions: Dict[str, List[QAction]] = {}
        
    def initialize_plugins(self, plugin_dirs: List[Path] = None):
        """初始化插件系统"""
        # 设置插件日志
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        PluginLogger.setup_plugin_logging(log_dir)
        
        # 加载插件
        if plugin_dirs:
            for plugin_dir in plugin_dirs:
                self._load_plugins_from_directory(plugin_dir)
        
        # 默认加载内置插件目录
        default_plugin_dir = Path(__file__).parent.parent.parent / "plugins"
        if default_plugin_dir.exists():
            self._load_plugins_from_directory(default_plugin_dir)
        
        # 初始化所有插件
        self.plugin_manager.initialize_all()
        
        # 启动所有插件
        self.plugin_manager.start_all()
        
        # 集成UI插件
        self._integrate_ui_plugins()
    
    def _load_plugins_from_directory(self, directory: Path):
        """从目录加载插件"""
        plugin_classes = PluginLoader.load_plugins_from_directory(directory)
        
        for plugin_class in plugin_classes:
            try:
                plugin = PluginLoader.create_plugin_instance(plugin_class)
                self.plugin_manager.register_plugin(plugin)
            except Exception as e:
                print(f"加载插件失败 {plugin_class.__name__}: {e}")
    
    def _integrate_ui_plugins(self):
        """集成UI插件到主窗口"""
        ui_plugins = self.plugin_manager.get_plugins(UIPlugin)
        
        for plugin in ui_plugins:
            plugin_name = plugin.get_info().name
            self.plugin_actions[plugin_name] = []
            
            # 添加菜单项
            self._add_menu_actions(plugin)
            
            # 添加工具栏项
            self._add_toolbar_actions(plugin)
            
            # 添加停靠窗口
            self._add_dock_widget(plugin)
    
    def _add_menu_actions(self, plugin: UIPlugin):
        """添加插件菜单项"""
        menu_actions = plugin.get_menu_actions()
        
        for action_def in menu_actions:
            # 获取或创建菜单
            menu_name = action_def.get('menu', '插件')
            menu = self._get_or_create_menu(menu_name)
            
            # 创建动作
            action = QAction(action_def['text'], self.main_window)
            action.triggered.connect(action_def['action'])
            
            # 设置快捷键
            if 'shortcut' in action_def:
                action.setShortcut(action_def['shortcut'])
            
            # 设置提示
            if 'tooltip' in action_def:
                action.setToolTip(action_def['tooltip'])
            
            # 添加到菜单
            menu.addAction(action)
            self.plugin_actions[plugin.get_info().name].append(action)
    
    def _add_toolbar_actions(self, plugin: UIPlugin):
        """添加插件工具栏项"""
        toolbar_actions = plugin.get_toolbar_actions()
        
        if toolbar_actions:
            # 获取或创建插件工具栏
            toolbar = self._get_or_create_toolbar("插件工具栏")
            
            for action_def in toolbar_actions:
                action = QAction(action_def['text'], self.main_window)
                action.triggered.connect(action_def['action'])
                
                if 'tooltip' in action_def:
                    action.setToolTip(action_def['tooltip'])
                
                toolbar.addAction(action)
                self.plugin_actions[plugin.get_info().name].append(action)
    
    def _add_dock_widget(self, plugin: UIPlugin):
        """添加插件停靠窗口"""
        dock_widget = plugin.get_dock_widget()
        if dock_widget:
            from PySide6.QtWidgets import QDockWidget
            from PySide6.QtCore import Qt
            
            dock = QDockWidget(plugin.get_info().name, self.main_window)
            dock.setWidget(dock_widget)
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
    
    def _get_or_create_menu(self, menu_name: str):
        """获取或创建菜单"""
        menu_bar = self.main_window.menuBar()
        
        # 查找现有菜单
        for action in menu_bar.actions():
            if action.menu() and action.text() == menu_name:
                return action.menu()
        
        # 创建新菜单
        return menu_bar.addMenu(menu_name)
    
    def _get_or_create_toolbar(self, toolbar_name: str):
        """获取或创建工具栏"""
        # 查找现有工具栏
        for toolbar in self.main_window.findChildren(type(self.main_window).toolBar):
            if toolbar.windowTitle() == toolbar_name:
                return toolbar
        
        # 创建新工具栏
        toolbar = self.main_window.addToolBar(toolbar_name)
        toolbar.setWindowTitle(toolbar_name)
        return toolbar
    
    def shutdown(self):
        """关闭插件系统"""
        # 停止所有插件
        self.plugin_manager.stop_all()
        
        # 移除所有插件动作
        for actions in self.plugin_actions.values():
            for action in actions:
                action.deleteLater()
        
        self.plugin_actions.clear()


def setup_plugin_system(main_window: QMainWindow) -> PluginIntegration:
    """
    在主窗口中设置插件系统的便捷函数
    
    使用示例：
    ```python
    # 在 MainWindow.__init__ 中
    self.plugin_integration = setup_plugin_system(self)
    
    # 在 MainWindow.closeEvent 中
    self.plugin_integration.shutdown()
    ```
    """
    integration = PluginIntegration(main_window)
    
    # 设置插件目录
    plugin_dirs = [
        Path("src/plugins"),
        Path("plugins"),  # 用户插件目录
    ]
    
    # 过滤存在的目录
    existing_dirs = [d for d in plugin_dirs if d.exists()]
    
    # 初始化插件
    integration.initialize_plugins(existing_dirs)
    
    return integration