"""
示例插件：Hello World
"""
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from src.core.plugin_system import Plugin, PluginInfo, UIPlugin


class HelloPlugin(UIPlugin):
    """简单的 Hello World 插件示例"""
    
    def __init__(self):
        super().__init__()
        self._widget = None
        
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="HelloPlugin",
            version="1.0.0",
            author="Example Author",
            description="一个简单的 Hello World 插件示例"
        )
    
    def initialize(self) -> None:
        """初始化插件"""
        print(f"[{self.get_info().name}] 正在初始化...")
    
    def start(self) -> None:
        """启动插件"""
        print(f"[{self.get_info().name}] 已启动")
    
    def stop(self) -> None:
        """停止插件"""
        print(f"[{self.get_info().name}] 已停止")
        if self._widget:
            self._widget.deleteLater()
            self._widget = None
    
    def get_menu_actions(self) -> List[Dict[str, Any]]:
        """获取菜单项"""
        return [
            {
                'text': 'Hello Plugin',
                'menu': '插件',
                'action': self._show_hello_dialog,
                'shortcut': 'Ctrl+H',
                'tooltip': '显示 Hello 对话框'
            }
        ]
    
    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """获取工具栏项"""
        return [
            {
                'text': 'Hello',
                'action': self._show_hello_dialog,
                'tooltip': '点击显示 Hello 对话框'
            }
        ]
    
    def get_config_widget(self) -> Optional[QWidget]:
        """获取配置界面"""
        if not self._widget:
            self._widget = self._create_config_widget()
        return self._widget
    
    def _create_config_widget(self) -> QWidget:
        """创建配置界面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Hello Plugin 配置")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        info_label = QLabel(f"版本: {self.get_info().version}\n作者: {self.get_info().author}")
        layout.addWidget(info_label)
        
        test_button = QPushButton("测试插件")
        test_button.clicked.connect(self._show_hello_dialog)
        layout.addWidget(test_button)
        
        layout.addStretch()
        
        return widget
    
    def _show_hello_dialog(self):
        """显示 Hello 对话框"""
        QMessageBox.information(None, "Hello Plugin", "Hello from the plugin system!")


class DataProcessorPlugin(Plugin):
    """数据处理插件示例"""
    
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="DataProcessor",
            version="1.0.0",
            author="Example Author",
            description="数据处理插件示例",
            dependencies=["HelloPlugin"]  # 依赖 HelloPlugin
        )
    
    def initialize(self) -> None:
        """初始化插件"""
        print(f"[{self.get_info().name}] 初始化数据处理器...")
        self._processed_count = 0
    
    def start(self) -> None:
        """启动插件"""
        print(f"[{self.get_info().name}] 数据处理器已就绪")
    
    def stop(self) -> None:
        """停止插件"""
        print(f"[{self.get_info().name}] 已处理 {self._processed_count} 条数据")
    
    def process_data(self, data: Any) -> Any:
        """处理数据的示例方法"""
        self._processed_count += 1
        # 这里可以添加实际的数据处理逻辑
        return f"Processed: {data}"