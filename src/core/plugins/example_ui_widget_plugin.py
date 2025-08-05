"""
示例UI组件插件
演示如何创建一个可插拔的UI组件插件
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QTextEdit, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

try:
    from ..core.interfaces.ui_plugin_interface import (
        IUIPlugin, UIPluginMetadata, UIPluginType, UIPluginCapability
    )
    from ..core.plugin_system.manager import BasePlugin
except ImportError:
    # 从插件目录运行时的导入路径
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from core.interfaces.ui_plugin_interface import (
        IUIPlugin, UIPluginMetadata, UIPluginType, UIPluginCapability
    )
    from core.plugin_system.manager import BasePlugin


class ExampleUIWidget(QWidget):
    """示例UI组件"""
    
    # 自定义信号
    value_changed = Signal(str)
    button_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        
        # 状态数据
        self._data = {
            'input_text': '',
            'counter': 0,
            'notes': ''
        }
        
        # 定时器用于演示
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_counter)
    
    def _setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("示例UI组件插件")
        self.setMinimumSize(300, 400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("示例UI组件插件")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(separator)
        
        # 输入区域
        input_group = self._create_input_group()
        layout.addWidget(input_group)
        
        # 计数器区域
        counter_group = self._create_counter_group()
        layout.addWidget(counter_group)
        
        # 笔记区域
        notes_group = self._create_notes_group()
        layout.addWidget(notes_group)
        
        # 按钮区域
        button_group = self._create_button_group()
        layout.addWidget(button_group)
        
        # 状态区域
        self.status_label = QLabel("状态: 已初始化")
        self.status_label.setStyleSheet("color: #007ACC; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _create_input_group(self) -> QWidget:
        """创建输入组"""
        group = QWidget()
        layout = QVBoxLayout(group)
        
        label = QLabel("文本输入:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("请输入文本...")
        layout.addWidget(self.input_edit)
        
        return group
    
    def _create_counter_group(self) -> QWidget:
        """创建计数器组"""
        group = QWidget()
        layout = QHBoxLayout(group)
        
        label = QLabel("计数器:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        self.counter_label = QLabel("0")
        self.counter_label.setStyleSheet("font-size: 16px; color: #007ACC;")
        layout.addWidget(self.counter_label)
        
        layout.addStretch()
        
        self.start_btn = QPushButton("开始")
        self.stop_btn = QPushButton("停止")
        self.reset_btn = QPushButton("重置")
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.reset_btn)
        
        return group
    
    def _create_notes_group(self) -> QWidget:
        """创建笔记组"""
        group = QWidget()
        layout = QVBoxLayout(group)
        
        label = QLabel("笔记:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("在这里记录笔记...")
        self.notes_edit.setMaximumHeight(80)
        layout.addWidget(self.notes_edit)
        
        return group
    
    def _create_button_group(self) -> QWidget:
        """创建按钮组"""
        group = QWidget()
        layout = QHBoxLayout(group)
        
        self.action_btn = QPushButton("执行操作")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0099FF;
            }
            QPushButton:pressed {
                background-color: #005C99;
            }
        """)
        
        self.clear_btn = QPushButton("清空")
        
        layout.addWidget(self.action_btn)
        layout.addWidget(self.clear_btn)
        layout.addStretch()
        
        return group
    
    def _connect_signals(self):
        """连接信号"""
        self.input_edit.textChanged.connect(self._on_input_changed)
        self.notes_edit.textChanged.connect(self._on_notes_changed)
        
        self.start_btn.clicked.connect(self._start_counter)
        self.stop_btn.clicked.connect(self._stop_counter)
        self.reset_btn.clicked.connect(self._reset_counter)
        
        self.action_btn.clicked.connect(self._on_action_clicked)
        self.clear_btn.clicked.connect(self._clear_all)
    
    def _on_input_changed(self, text: str):
        """输入文本变化"""
        self._data['input_text'] = text
        self.value_changed.emit(text)
        self._update_status(f"输入文本: {text[:20]}...")
    
    def _on_notes_changed(self):
        """笔记变化"""
        self._data['notes'] = self.notes_edit.toPlainText()
    
    def _start_counter(self):
        """开始计数"""
        self._timer.start(1000)  # 每秒更新
        self._update_status("计数器已启动")
    
    def _stop_counter(self):
        """停止计数"""
        self._timer.stop()
        self._update_status("计数器已停止")
    
    def _reset_counter(self):
        """重置计数"""
        self._timer.stop()
        self._data['counter'] = 0
        self.counter_label.setText("0")
        self._update_status("计数器已重置")
    
    def _update_counter(self):
        """更新计数器"""
        self._data['counter'] += 1
        self.counter_label.setText(str(self._data['counter']))
    
    def _on_action_clicked(self):
        """执行操作"""
        text = self.input_edit.text()
        if text:
            self.notes_edit.append(f"操作执行: {text}")
            self._update_status(f"执行了操作: {text}")
            self.button_clicked.emit()
        else:
            self._update_status("请先输入文本")
    
    def _clear_all(self):
        """清空所有内容"""
        self.input_edit.clear()
        self.notes_edit.clear()
        self._reset_counter()
        self._data = {'input_text': '', 'counter': 0, 'notes': ''}
        self._update_status("所有内容已清空")
    
    def _update_status(self, message: str):
        """更新状态消息"""
        self.status_label.setText(f"状态: {message}")
    
    def get_data(self) -> Dict[str, Any]:
        """获取组件数据"""
        # 更新当前输入
        self._data['input_text'] = self.input_edit.text()
        self._data['notes'] = self.notes_edit.toPlainText()
        return self._data.copy()
    
    def set_data(self, data: Dict[str, Any]):
        """设置组件数据"""
        self._data.update(data)
        
        # 更新UI
        self.input_edit.setText(self._data.get('input_text', ''))
        self.notes_edit.setPlainText(self._data.get('notes', ''))
        
        counter = self._data.get('counter', 0)
        self.counter_label.setText(str(counter))
    
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        """应用主题"""
        try:
            colors = theme_data.get('colors', {})
            
            # 应用背景色
            bg_color = colors.get('background_primary', '#2C313C')
            text_color = colors.get('text_primary', '#D3D8E0')
            accent_color = colors.get('accent_primary', '#007ACC')
            
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QLineEdit, QTextEdit {{
                    background-color: {colors.get('background_secondary', '#313642')};
                    border: 1px solid {colors.get('border_normal', '#404552')};
                    border-radius: 4px;
                    padding: 4px;
                    color: {text_color};
                }}
                QPushButton {{
                    background-color: {accent_color};
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('accent_hover', '#0099FF')};
                }}
            """)
            
            return True
            
        except Exception as e:
            print(f"应用主题失败: {e}")
            return False


class ExampleUIWidgetPlugin(BasePlugin, IUIPlugin):
    """示例UI组件插件"""
    
    def __init__(self, metadata: UIPluginMetadata):
        BasePlugin.__init__(self, metadata)
        IUIPlugin.__init__(self, metadata)
        
        self._widget_instance: Optional[ExampleUIWidget] = None
    
    def load(self) -> bool:
        """加载插件"""
        try:
            print(f"🔌 正在加载插件: {self.metadata.name}")
            self._is_loaded = True
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} load failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动插件"""
        try:
            if not self._is_loaded:
                return False
            
            print(f"🚀 正在启动插件: {self.metadata.name}")
            self._is_started = True
            self._ui_ready = True
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止插件"""
        try:
            print(f"⏹️ 正在停止插件: {self.metadata.name}")
            
            # 销毁UI组件
            if self._widget_instance:
                self.destroy_widget()
            
            self._is_started = False
            self._ui_ready = False
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} stop failed: {e}")
            return False
    
    def unload(self) -> bool:
        """卸载插件"""
        try:
            if self._is_started:
                self.stop()
            
            print(f"📤 正在卸载插件: {self.metadata.name}")
            
            self._is_loaded = False
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Plugin {self.metadata.name} unload failed: {e}")
            return False
    
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """创建UI组件"""
        if self._widget_instance is None:
            self._widget_instance = ExampleUIWidget(parent)
            self._widget = self._widget_instance
            
            # 连接信号
            self._widget_instance.value_changed.connect(self._on_value_changed)
            self._widget_instance.button_clicked.connect(self._on_button_clicked)
            
            print(f"✅ 插件 {self.metadata.name} UI组件已创建")
        
        return self._widget_instance
    
    def destroy_widget(self) -> bool:
        """销毁UI组件"""
        try:
            if self._widget_instance:
                # 保存状态
                self._config.update(self._widget_instance.get_data())
                
                # 销毁组件
                self._widget_instance.deleteLater()
                self._widget_instance = None
                self._widget = None
                
                print(f"🗑️ 插件 {self.metadata.name} UI组件已销毁")
            
            return True
            
        except Exception as e:
            print(f"❌ 销毁插件 {self.metadata.name} UI组件失败: {e}")
            return False
    
    def configure_widget(self, config: Dict[str, Any]) -> bool:
        """配置UI组件"""
        try:
            if self._widget_instance:
                self._widget_instance.set_data(config)
            
            self._config.update(config)
            return True
            
        except Exception:
            return False
    
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        """应用主题"""
        try:
            if self._widget_instance:
                return self._widget_instance.apply_theme(theme_data)
            return True
            
        except Exception:
            return False
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化UI状态"""
        if self._widget_instance:
            return self._widget_instance.get_data()
        return {}
    
    def restore_state(self, state: Dict[str, Any]) -> bool:
        """恢复UI状态"""
        try:
            if self._widget_instance:
                self._widget_instance.set_data(state)
            else:
                # 保存状态，等UI创建后恢复
                self._config.update(state)
            return True
            
        except Exception:
            return False
    
    def _on_value_changed(self, value: str):
        """值变化事件处理"""
        print(f"🔄 插件 {self.metadata.name} 值变化: {value}")
    
    def _on_button_clicked(self):
        """按钮点击事件处理"""
        print(f"🖱️ 插件 {self.metadata.name} 按钮被点击")


# 插件工厂函数
def create_plugin(metadata: UIPluginMetadata) -> ExampleUIWidgetPlugin:
    """创建插件实例"""
    return ExampleUIWidgetPlugin(metadata)


# 插件元数据
PLUGIN_METADATA = UIPluginMetadata(
    name="ExampleUIWidget",
    version="1.0.0",
    description="示例UI组件插件，演示插件系统的基本功能",
    author="AI-2 UI层重构工程师",
    plugin_type="ui_component",
    entry_point="example_ui_widget_plugin",
    ui_type=UIPluginType.WIDGET,
    capabilities=[
        UIPluginCapability.CONFIGURABLE,
        UIPluginCapability.THEMEABLE,
        UIPluginCapability.RESIZABLE
    ],
    default_position="center",
    icon="widget.png",
    menu_text="示例组件",
    tooltip="一个演示用的UI组件插件",
    auto_start=True,
    priority=100
)