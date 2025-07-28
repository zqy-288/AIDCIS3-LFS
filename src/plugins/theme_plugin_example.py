"""
主题插件示例
演示如何创建一个主题插件，提供完整的UI主题支持
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt

try:
    from ..interfaces.ui_plugin_interface import (
        IUIThemePlugin, UIPluginMetadata, UIPluginType, UIPluginCapability
    )
    from ..core.plugin_system.manager import BasePlugin
except ImportError:
    # 从插件目录运行时的导入路径
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    from interfaces.ui_plugin_interface import (
        IUIThemePlugin, UIPluginMetadata, UIPluginType, UIPluginCapability
    )
    from core.plugin_system.manager import BasePlugin


class ModernDarkTheme:
    """现代深色主题定义"""
    
    @staticmethod
    def get_colors() -> Dict[str, str]:
        """获取主题颜色配置"""
        return {
            # 主背景色
            'background_primary': '#1E1E1E',      # VS Code深色主题背景
            'background_secondary': '#252526',    # 面板背景色
            'background_tertiary': '#2D2D30',     # 标题栏/高亮背景
            
            # 强调色
            'accent_primary': '#0E7ACC',          # VS Code蓝色
            'accent_secondary': '#4FC3F7',        # 辅助蓝色
            'accent_hover': '#1177BB',            # 悬停状态
            'accent_pressed': '#094771',          # 按下状态
            
            # 文本色
            'text_primary': '#CCCCCC',            # 主文本色
            'text_secondary': '#FFFFFF',          # 醒目文字
            'text_disabled': '#808080',           # 禁用文字
            'text_muted': '#969696',              # 次要文字
            
            # 状态色
            'success': '#4CAF50',                 # 成功状态
            'warning': '#FF9800',                 # 警告状态
            'error': '#F44336',                   # 错误状态
            'info': '#2196F3',                    # 信息状态
            
            # 边框色
            'border_normal': '#3C3C3C',           # 普通边框
            'border_focus': '#0E7ACC',            # 焦点边框
            'border_disabled': '#555555',         # 禁用边框
            'border_hover': '#464647',            # 悬停边框
            
            # 特殊背景
            'status_bar': '#007ACC',              # 状态栏背景
            'selection': '#264F78',               # 选中背景
            'hover': '#2A2D2E',                   # 悬停背景
            'active': '#094771',                  # 活跃背景
        }
    
    @staticmethod
    def get_fonts() -> Dict[str, Any]:
        """获取字体配置"""
        return {
            'family': 'Segoe UI',
            'size': 9,
            'weight': 'normal',
            'line_height': 1.4
        }
    
    @staticmethod
    def get_spacing() -> Dict[str, int]:
        """获取间距配置"""
        return {
            'margin_small': 4,
            'margin_medium': 8,
            'margin_large': 16,
            'padding_small': 4,
            'padding_medium': 8,
            'padding_large': 12,
            'border_radius': 3
        }


class ModernDarkThemePlugin(BasePlugin, IUIThemePlugin):
    """现代深色主题插件"""
    
    def __init__(self, metadata: UIPluginMetadata):
        BasePlugin.__init__(self, metadata)
        IUIThemePlugin.__init__(self, metadata)
        
        self._theme = ModernDarkTheme()
        self._applied_widgets = set()
    
    def load(self) -> bool:
        """加载插件"""
        try:
            print(f"🎨 正在加载主题插件: {self.metadata.name}")
            self._is_loaded = True
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Theme plugin {self.metadata.name} load failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动插件"""
        try:
            if not self._is_loaded:
                return False
            
            print(f"🎨 正在启动主题插件: {self.metadata.name}")
            self._is_started = True
            self._ui_ready = True
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Theme plugin {self.metadata.name} start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止插件"""
        try:
            print(f"⏹️ 正在停止主题插件: {self.metadata.name}")
            
            # 清理应用的组件
            self._applied_widgets.clear()
            
            self._is_started = False
            self._ui_ready = False
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Theme plugin {self.metadata.name} stop failed: {e}")
            return False
    
    def unload(self) -> bool:
        """卸载插件"""
        try:
            if self._is_started:
                self.stop()
            
            print(f"📤 正在卸载主题插件: {self.metadata.name}")
            
            self._is_loaded = False
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Theme plugin {self.metadata.name} unload failed: {e}")
            return False
    
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """创建主题配置UI组件（可选）"""
        # 主题插件通常不需要独立的UI组件
        # 这里返回一个简单的配置面板
        widget = QWidget(parent)
        widget.setWindowTitle(f"{self.get_theme_name()} 主题设置")
        return widget
    
    def destroy_widget(self) -> bool:
        """销毁UI组件"""
        return True
    
    def get_theme_name(self) -> str:
        """获取主题名称"""
        return "现代深色主题"
    
    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置"""
        return self._theme.get_colors()
    
    def get_stylesheet(self) -> str:
        """获取样式表"""
        colors = self._theme.get_colors()
        fonts = self._theme.get_fonts()
        spacing = self._theme.get_spacing()
        
        return f"""
        /* 全局样式 */
        QApplication {{
            background-color: {colors['background_primary']};
            color: {colors['text_primary']};
            font-family: "{fonts['family']}";
            font-size: {fonts['size']}pt;
        }}
        
        /* 主窗口 */
        QMainWindow {{
            background-color: {colors['background_primary']};
            color: {colors['text_primary']};
        }}
        
        /* 按钮样式 */
        QPushButton {{
            background-color: {colors['accent_primary']};
            color: {colors['text_secondary']};
            border: 1px solid {colors['border_normal']};
            border-radius: {spacing['border_radius']}px;
            padding: {spacing['padding_medium']}px {spacing['padding_large']}px;
            font-weight: bold;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
            border-color: {colors['border_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent_pressed']};
        }}
        
        QPushButton:disabled {{
            background-color: {colors['border_disabled']};
            color: {colors['text_disabled']};
            border-color: {colors['border_disabled']};
        }}
        
        /* 输入框样式 */
        QLineEdit {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border_normal']};
            border-radius: {spacing['border_radius']}px;
            padding: {spacing['padding_small']}px {spacing['padding_medium']}px;
            selection-background-color: {colors['selection']};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {colors['border_focus']};
        }}
        
        QLineEdit:hover {{
            border-color: {colors['border_hover']};
        }}
        
        QLineEdit:disabled {{
            background-color: {colors['background_primary']};
            color: {colors['text_disabled']};
            border-color: {colors['border_disabled']};
        }}
        
        /* 文本编辑器样式 */
        QTextEdit {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border_normal']};
            border-radius: {spacing['border_radius']}px;
            padding: {spacing['padding_medium']}px;
            selection-background-color: {colors['selection']};
        }}
        
        QTextEdit:focus {{
            border: 2px solid {colors['border_focus']};
        }}
        
        /* 标签样式 */
        QLabel {{
            color: {colors['text_primary']};
            background: transparent;
        }}
        
        QLabel[class="title"] {{
            color: {colors['text_secondary']};
            font-weight: bold;
            font-size: {fonts['size'] + 2}pt;
        }}
        
        QLabel[class="subtitle"] {{
            color: {colors['text_muted']};
            font-size: {fonts['size'] - 1}pt;
        }}
        
        /* 组合框样式 */
        QComboBox {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border_normal']};
            border-radius: {spacing['border_radius']}px;
            padding: {spacing['padding_small']}px {spacing['padding_medium']}px;
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            background-color: {colors['hover']};
            border-color: {colors['border_hover']};
        }}
        
        QComboBox:focus {{
            border-color: {colors['border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border: 5px solid transparent;
            border-top: 5px solid {colors['text_primary']};
            margin-right: 5px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border_normal']};
            selection-background-color: {colors['selection']};
        }}
        
        /* 表格样式 */
        QTableWidget {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            gridline-color: {colors['border_normal']};
            selection-background-color: {colors['selection']};
            alternate-background-color: {colors['background_tertiary']};
        }}
        
        QHeaderView::section {{
            background-color: {colors['background_tertiary']};
            color: {colors['text_secondary']};
            border: 1px solid {colors['border_normal']};
            padding: {spacing['padding_medium']}px;
            font-weight: bold;
        }}
        
        QTableWidget::item {{
            padding: {spacing['padding_small']}px;
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors['selection']};
        }}
        
        QTableWidget::item:hover {{
            background-color: {colors['hover']};
        }}
        
        /* 分组框样式 */
        QGroupBox {{
            color: {colors['text_secondary']};
            border: 2px solid {colors['border_normal']};
            border-radius: {spacing['border_radius'] * 2}px;
            margin-top: 1ex;
            font-weight: bold;
            padding-top: {spacing['padding_large']}px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {spacing['margin_medium']}px;
            padding: 0 {spacing['padding_small']}px 0 {spacing['padding_small']}px;
        }}
        
        /* 状态栏样式 */
        QStatusBar {{
            background-color: {colors['status_bar']};
            color: {colors['text_secondary']};
            border-top: 1px solid {colors['border_normal']};
        }}
        
        /* 工具栏样式 */
        QToolBar {{
            background-color: {colors['background_tertiary']};
            border: 1px solid {colors['border_normal']};
            spacing: {spacing['margin_small']}px;
        }}
        
        QToolBar::separator {{
            background-color: {colors['border_normal']};
            width: 1px;
            margin: 0 {spacing['margin_small']}px;
        }}
        
        /* 菜单样式 */
        QMenuBar {{
            background-color: {colors['background_primary']};
            color: {colors['text_primary']};
        }}
        
        QMenuBar::item {{
            background: transparent;
            padding: {spacing['padding_small']}px {spacing['padding_medium']}px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['hover']};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {colors['active']};
        }}
        
        QMenu {{
            background-color: {colors['background_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border_normal']};
        }}
        
        QMenu::item {{
            padding: {spacing['padding_medium']}px {spacing['padding_large']}px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors['selection']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors['border_normal']};
            margin: {spacing['margin_small']}px 0;
        }}
        
        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {colors['background_primary']};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['border_normal']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['border_hover']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors['background_primary']};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['border_normal']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['border_hover']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}
        
        /* 进度条样式 */
        QProgressBar {{
            background-color: {colors['background_secondary']};
            border: 1px solid {colors['border_normal']};
            border-radius: {spacing['border_radius']}px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['accent_primary']};
            border-radius: {spacing['border_radius']}px;
        }}
        
        /* 分割线样式 */
        QFrame[frameShape="4"] {{ /* HLine */
            color: {colors['border_normal']};
        }}
        
        QFrame[frameShape="5"] {{ /* VLine */
            color: {colors['border_normal']};
        }}
        """
    
    def apply_to_widget(self, widget: QWidget) -> bool:
        """应用主题到指定组件"""
        try:
            if widget:
                stylesheet = self.get_stylesheet()
                widget.setStyleSheet(stylesheet)
                self._applied_widgets.add(widget)
                return True
            return False
            
        except Exception as e:
            print(f"❌ 应用主题到组件失败: {e}")
            return False
    
    def apply_theme(self, theme_data: Dict[str, Any]) -> bool:
        """应用主题（继承自IUIPlugin）"""
        # 对于主题插件，这个方法可以用于配置主题本身
        return True
    
    def get_theme_data(self) -> Dict[str, Any]:
        """获取完整主题数据"""
        return {
            'name': self.get_theme_name(),
            'colors': self.get_theme_colors(),
            'fonts': self._theme.get_fonts(),
            'spacing': self._theme.get_spacing(),
            'stylesheet': self.get_stylesheet()
        }
    
    def apply_global_theme(self) -> bool:
        """应用全局主题"""
        try:
            app = QApplication.instance()
            if app:
                stylesheet = self.get_stylesheet()
                app.setStyleSheet(stylesheet)
                print(f"✅ 全局主题 {self.get_theme_name()} 应用成功")
                return True
            return False
            
        except Exception as e:
            print(f"❌ 应用全局主题失败: {e}")
            return False


# 插件工厂函数
def create_plugin(metadata: UIPluginMetadata) -> ModernDarkThemePlugin:
    """创建主题插件实例"""
    return ModernDarkThemePlugin(metadata)


# 插件元数据
PLUGIN_METADATA = UIPluginMetadata(
    name="ModernDarkTheme",
    version="1.0.0",
    description="现代深色主题插件，提供专业的深色UI主题",
    author="AI-2 UI层重构工程师",
    plugin_type="ui_component",
    entry_point="theme_plugin_example",
    ui_type=UIPluginType.THEME,
    capabilities=[
        UIPluginCapability.CONFIGURABLE,
        UIPluginCapability.THEMEABLE
    ],
    default_position="center",
    icon="theme.png",
    menu_text="现代深色主题",
    tooltip="现代专业的深色UI主题",
    auto_start=True,
    priority=50  # 主题插件优先级较高
)