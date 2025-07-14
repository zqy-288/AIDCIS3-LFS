"""
现代科技蓝主题管理器
提供统一的UI样式和配色方案
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
import logging


class ModernThemeManager:
    """现代科技蓝主题管理器"""
    
    # 现代科技蓝配色方案 - 完全符合UI设计规范文档
    COLORS = {
        # 主背景色 - 按文档规范
        'background_primary': '#2C313C',        # 主背景色 (文档规范)
        'background_secondary': '#313642',      # 面板背景色 (文档规范)
        'background_tertiary': '#3A404E',       # 标题栏/高亮背景 (文档规范)
        
        # 强调色 - 按文档规范
        'accent_primary': '#007ACC',            # 主操作色/主题蓝 (文档规范)
        'accent_secondary': '#4A90E2',          # 辅助蓝色
        'accent_hover': '#0099FF',              # 悬停状态
        'accent_pressed': '#005C99',            # 按下状态
        
        # 文本色 - 按文档规范
        'text_primary': '#D3D8E0',              # 主文本/图标色 (文档规范)
        'text_secondary': '#FFFFFF',            # 标题/醒目文字 (文档规范)
        'text_disabled': '#AAAAAA',             # 禁用文字
        
        # 状态色 - 按文档规范
        'success': '#2ECC71',                   # 成功/合格状态 (文档规范)
        'warning': '#E67E22',                   # 警告/异常状态 (文档规范)
        'error': '#E74C3C',                     # 错误/不合格状态 (文档规范)
        'info': '#007ACC',                      # 信息状态使用主题蓝
        
        # 边框色 - 按文档规范
        'border_normal': '#404552',             # 边框/分割线 (文档规范)
        'border_focus': '#007ACC',              # 焦点边框
        'border_disabled': '#555555',           # 禁用边框
        
        # 特殊背景
        'status_bar': '#1E222B',                # 状态栏背景
        'selection': '#007ACC',                 # 选中背景
        'hover': '#3A404E'                      # 悬停背景
    }
    
    @classmethod
    def get_main_stylesheet(cls) -> str:
        """获取主样式表"""
        return f"""
/* 整体窗口和字体设置 - 按文档规范 */
QWidget {{
    background-color: {cls.COLORS['background_primary']} !important;
    color: {cls.COLORS['text_primary']} !important;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC";  /* 按文档规范 */
    font-size: 15px;  /* 正文/常规字号 (Body) - 按文档规范 */
}}

/* 强制所有QWidget子类使用深色背景 */
QMainWindow, QDialog, QFrame, QGraphicsView {{
    background-color: {cls.COLORS['background_primary']} !important;
}}

/* 确保所有容器组件使用正确的背景色 */
QGroupBox, QTabWidget::pane, QScrollArea {{
    background-color: {cls.COLORS['background_secondary']} !important;
}}

/* 默认按钮样式 - 按文档规范 */
QPushButton {{
    background-color: {cls.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;  /* 按文档规范：8px 20px */
    font-weight: bold;
    min-height: 24px;
}}
QPushButton:hover {{
    background-color: {cls.COLORS['accent_hover']};
}}
QPushButton:pressed {{
    background-color: {cls.COLORS['accent_pressed']};
}}
QPushButton:disabled {{
    background-color: {cls.COLORS['border_disabled']};
    color: {cls.COLORS['text_disabled']};
    opacity: 0.5;
    border: 1px solid {cls.COLORS['border_disabled']};
}}

/* 输入框、下拉框等 */
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    padding: 6px;
    color: {cls.COLORS['text_primary']};
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {cls.COLORS['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

/* 表格和表头 */
QTableWidget {{
    background-color: {cls.COLORS['background_secondary']};
    gridline-color: {cls.COLORS['border_normal']};
    border: 1px solid {cls.COLORS['border_normal']};
    selection-background-color: {cls.COLORS['selection']};
    selection-color: white;
    alternate-background-color: {cls.COLORS['background_tertiary']};
}}
QHeaderView::section {{
    background-color: {cls.COLORS['background_tertiary']};
    color: {cls.COLORS['text_primary']};
    padding: 6px;
    border: none;
    font-weight: bold;
    border-right: 1px solid {cls.COLORS['border_normal']};
    border-bottom: 1px solid {cls.COLORS['border_normal']};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {cls.COLORS['status_bar']};
    color: {cls.COLORS['text_primary']};
    border-top: 1px solid {cls.COLORS['border_normal']};
}}

/* 菜单栏 */
QMenuBar {{
    background-color: {cls.COLORS['background_secondary']};
    color: {cls.COLORS['text_primary']};
    border-bottom: 1px solid {cls.COLORS['border_normal']};
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background-color: {cls.COLORS['accent_primary']};
}}

/* 菜单 */
QMenu {{
    background-color: {cls.COLORS['background_secondary']};
    color: {cls.COLORS['text_primary']};
    border: 1px solid {cls.COLORS['border_normal']};
}}
QMenu::item {{
    padding: 6px 20px;
}}
QMenu::item:selected {{
    background-color: {cls.COLORS['accent_primary']};
}}

/* 组框 */
QGroupBox {{
    background-color: {cls.COLORS['background_secondary']};  /* 面板背景色 - 按文档规范 */
    color: {cls.COLORS['text_primary']};
    border: 1px solid {cls.COLORS['border_normal']};  /* 边框/分割线 - 按文档规范 */
    border-radius: 8px;  /* 按文档规范 */
    margin-top: 10px;  /* 为自定义标题行留出空间 - 按文档规范 */
    margin-bottom: 8px;
    font-weight: bold;
    padding: 10px;  /* 内边距 - 按文档规范 */
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: {cls.COLORS['text_secondary']};  /* 标题/醒目文字 - 按文档规范 */
    font-size: 16px;  /* 面板标题 (L2) - 按文档规范 */
    font-weight: bold;
}}

/* 状态仪表盘样式 */
QGroupBox#StatusDashboard {{
    background-color: {cls.COLORS['background_secondary']};  /* 面板背景色 - 按文档规范 */
    border: 1px solid {cls.COLORS['border_normal']};  /* 边框/分割线 - 按文档规范 */
    border-radius: 8px;
    margin-top: 10px;  /* 按文档规范 */
    padding: 10px;  /* 内边距 - 按文档规范 */
}}
QGroupBox#StatusDashboard::title {{
    color: {cls.COLORS['text_secondary']};  /* 标题/醒目文字 - 按文档规范 */
    font-size: 16px;  /* 面板标题 (L2) - 按文档规范 */
    font-weight: bold;
}}

/* 无边框面板样式 */
QWidget#PanelAWidget {{
    background-color: {cls.COLORS['background_primary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 6px;
}}
QWidget#ChartWidget {{
    background-color: {cls.COLORS['background_primary']};
}}
QWidget#RightPanel {{
    background-color: {cls.COLORS['background_primary']};
}}
QWidget#EndoscopeWidget {{
    background-color: {cls.COLORS['background_primary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 6px;
}}

/* ===== 通用的面板标题栏样式 ===== */
QWidget#PanelHeader {{
    background-color: {cls.COLORS['background_secondary']};
    min-height: 40px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    /* border-bottom: 1px solid {cls.COLORS['border_normal']}; */ /* 移除底部边框实现无边框效果 */
}}

QLabel#PanelHeaderText {{
    font-size: 16px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    padding: 0;
}}

QToolButton#HeaderToolButton {{
    background: transparent;
    border: none;
    padding: 8px;
    font-size: 16px;
    color: {cls.COLORS['text_secondary']};
    border-radius: 4px;
    min-width: 32px;
    min-height: 32px;
}}

QToolButton#HeaderToolButton:hover {{
    background-color: {cls.COLORS['hover']};
    color: {cls.COLORS['text_primary']};
}}

QToolButton#HeaderToolButton:pressed {{
    background-color: {cls.COLORS['selection']};
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid {cls.COLORS['border_normal']};
    background-color: {cls.COLORS['background_primary']};
}}
QTabBar::tab {{
    background-color: {cls.COLORS['background_secondary']};
    color: {cls.COLORS['text_primary']};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background-color: {cls.COLORS['accent_primary']};
    color: white;
}}
QTabBar::tab:hover {{
    background-color: {cls.COLORS['hover']};
}}

/* 滚动条 */
QScrollBar:vertical {{
    background-color: {cls.COLORS['background_secondary']};
    width: 12px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical {{
    background-color: {cls.COLORS['accent_primary']};
    border-radius: 6px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {cls.COLORS['accent_hover']};
}}

/* 滚动区域内容悬停效果 */
QScrollArea {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
}}

/* 异常列表项悬停效果 */
QWidget#anomaly_content QLabel:hover {{
    background-color: {cls.COLORS['hover']};
    border-radius: 3px;
    padding: 2px;
}}

/* 列表项通用悬停效果 */
QListWidget::item:hover {{
    background-color: {cls.COLORS['hover']};
    border-radius: 3px;
}}

QListWidget::item:selected {{
    background-color: {cls.COLORS['selection']};
    color: white;
}}

/* 进度条 */
QProgressBar {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    text-align: center;
    color: {cls.COLORS['text_primary']};
}}
QProgressBar::chunk {{
    background-color: {cls.COLORS['accent_primary']};
    border-radius: 3px;
}}

/* 文本编辑器 */
QTextEdit, QPlainTextEdit {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    color: {cls.COLORS['text_primary']};
    selection-background-color: {cls.COLORS['selection']};
}}

/* 分割器 */
QSplitter::handle {{
    background-color: {cls.COLORS['border_normal']};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}

/* 框架 */
QFrame {{
    border: 1px solid {cls.COLORS['border_normal']};
    background-color: {cls.COLORS['background_secondary']};
}}

/* 用于显示关键数据的 QLabel */
QLabel#ImportantDataLabel {{
    color: {cls.COLORS['accent_secondary']};
    font-size: 24px;
    font-weight: bold;
    background-color: {cls.COLORS['background_secondary']};
    padding: 8px;
    border-radius: 4px;
}}

/* 用于显示报警状态的 QLabel */
QLabel#AlarmLabel {{
    background-color: {cls.COLORS['error']};
    color: white;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}}

/* 成功状态标签 */
QLabel#SuccessLabel {{
    background-color: {cls.COLORS['success']};
    color: white;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}}

/* 警告状态标签 */
QLabel#WarningLabel {{
    background-color: {cls.COLORS['warning']};
    color: white;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}}

/* 信息状态标签 */
QLabel#InfoLabel {{
    background-color: {cls.COLORS['info']};
    color: white;
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}}

/* 状态栏标签样式 */
QLabel#StatusLabel {{
    color: {cls.COLORS['text_primary']};
    font-size: 14px;
    padding: 4px 8px;
    background-color: {cls.COLORS['background_tertiary']};
    border-radius: 4px;
    border: 1px solid {cls.COLORS['border_normal']};
}}

QLabel#CommStatusLabel {{
    color: {cls.COLORS['text_primary']};
    font-size: 14px;
    font-weight: bold;
    padding: 4px 8px;
    background-color: {cls.COLORS['background_tertiary']};
    border-radius: 4px;
    border: 1px solid {cls.COLORS['border_normal']};
}}

QLabel#StaticInfoLabel {{
    color: {cls.COLORS['text_secondary']};
    font-size: 14px;
    padding: 4px 8px;
    background-color: {cls.COLORS['background_tertiary']};
    border-radius: 4px;
    border: 1px solid {cls.COLORS['border_normal']};
}}

/* ===== 异常监控面板的统计区域样式 ===== */

/* 整个统计信息区域的容器背景 */
QWidget#AnomalyStatsWidget {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 6px;
    margin: 2px;
}}

/* 大号数字 "0" 的样式 */
QLabel#AnomalyCountLabel {{
    font-size: 48px;
    font-weight: bold;
    color: {cls.COLORS['warning']};
    background-color: transparent;
    border: none;
    min-width: 60px;
    padding: 0;
}}

/* "个异常点" 标签的样式 */
QLabel#AnomalyUnitLabel {{
    font-size: 14px;
    font-weight: bold;
    color: {cls.COLORS['warning']};
    background-color: transparent;
    border: none;
    padding-left: 5px;
}}

/* "异常率" 标签的样式 */
QLabel#AnomalyRateLabel {{
    font-size: 14px;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
}}

/* 控制按钮统一样式 - 使用图标颜色区分状态 */
QPushButton#StartButton,
QPushButton#StopButton,
QPushButton#ClearDataButton {{
    background-color: {cls.COLORS['background_tertiary']};
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
    font-size: 14px;
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 120px;  /* 设置最小宽度确保文字完整显示 */
    height: 35px;      /* 设置固定高度保持一致性 */
}}

QPushButton#StartButton:hover,
QPushButton#StopButton:hover,
QPushButton#ClearDataButton:hover {{
    background-color: {cls.COLORS['hover']};
    border-color: {cls.COLORS['accent_primary']};
}}

QPushButton#StartButton:pressed,
QPushButton#StopButton:pressed,
QPushButton#ClearDataButton:pressed {{
    background-color: {cls.COLORS['selection']};
}}

/* 按钮状态指示 - 通过文字颜色区分 */
QPushButton#StartButton {{
    color: {cls.COLORS['success']};
}}

QPushButton#StopButton {{
    color: {cls.COLORS['error']};
}}

/* 清除数据按钮专门样式 - 只设置颜色，尺寸已在统一样式中设置 */
QPushButton#ClearDataButton {{
    color: {cls.COLORS['warning']};
}}

/* 特殊按钮样式 */
QPushButton#WarningButton {{
    background-color: {cls.COLORS['warning']};
    color: white;
    font-weight: bold;
}}
QPushButton#WarningButton:hover {{
    background-color: #D35400;
}}
QPushButton#WarningButton:pressed {{
    background-color: #A04000;
}}

QPushButton#SuccessButton {{
    background-color: {cls.COLORS['success']};
    color: white;
    font-weight: bold;
}}
QPushButton#SuccessButton:hover {{
    background-color: #27AE60;
}}
QPushButton#SuccessButton:pressed {{
    background-color: #1E8449;
}}

QPushButton#ErrorButton {{
    background-color: {cls.COLORS['error']};
    color: white;
    font-weight: bold;
}}
QPushButton#ErrorButton:hover {{
    background-color: #C0392B;
}}
QPushButton#ErrorButton:pressed {{
    background-color: #922B21;
}}

/* ===== 第二级界面特殊样式 ===== */

/* 状态标签样式 */
QLabel#StatusLabel {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 13px;
    color: {cls.COLORS['text_primary']};
}}

/* 面板A样式 - 光谱共焦传感器数据 */
QGroupBox#PanelA {{
    background-color: {cls.COLORS['background_secondary']};  /* 面板背景色 - 按文档规范 */
    border: 1px solid {cls.COLORS['border_normal']};  /* 边框/分割线 - 按文档规范 */
    border-radius: 8px;
    margin-top: 10px;  /* 按文档规范 */
    padding: 10px;  /* 内边距 - 按文档规范 */
    font-weight: bold;
    font-size: 15px;  /* 正文/常规 (Body) - 按文档规范 */
}}
QGroupBox#PanelA::title {{
    color: {cls.COLORS['text_secondary']};  /* 标题/醒目文字 - 按文档规范 */
    background-color: {cls.COLORS['background_secondary']};
    font-size: 16px;  /* 面板标题 (L2) - 按文档规范 */
    font-weight: bold;
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 10px 0 10px;
}}

/* 面板B样式 - 内窥镜图像 */
QGroupBox#PanelB {{
    background-color: {cls.COLORS['background_secondary']};  /* 面板背景色 - 按文档规范 */
    border: 1px solid {cls.COLORS['border_normal']};  /* 边框/分割线 - 按文档规范 */
    border-radius: 8px;
    margin-top: 10px;  /* 按文档规范 */
    padding: 10px;  /* 内边距 - 按文档规范 */
    font-weight: bold;
    font-size: 15px;  /* 正文/常规 (Body) - 按文档规范 */
}}
QGroupBox#PanelB::title {{
    color: {cls.COLORS['text_secondary']};  /* 标题/醒目文字 - 按文档规范 */
    background-color: {cls.COLORS['background_secondary']};
    font-size: 16px;  /* 面板标题 (L2) - 按文档规范 */
    font-weight: bold;
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 10px 0 10px;
}}

/* "查看下一个样品" 按钮的特殊样式 */
QPushButton#next_sample_button {{
    background-color: {cls.COLORS['success']};
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    min-height: 40px;
    font-size: 14px;
}}
QPushButton#next_sample_button:hover {{
    background-color: #27AE60;
}}
QPushButton#next_sample_button:pressed {{
    background-color: #1E8449;
}}

/* ===== 异常监控面板样式 ===== */
QGroupBox#anomaly_widget {{
    background-color: {cls.COLORS['background_secondary']};  /* 面板背景色 - 按文档规范 */
    border: 1px solid {cls.COLORS['border_normal']};  /* 边框/分割线 - 按文档规范 */
    border-radius: 8px;
    margin-top: 10px;  /* 按文档规范 */
    padding: 10px;  /* 内边距 - 按文档规范 */
    font-size: 15px;  /* 正文/常规 (Body) - 按文档规范 */
    font-weight: bold;
}}
QGroupBox#anomaly_widget::title {{
    color: {cls.COLORS['warning']};  /* 保持警告色用于异常监控 */
    background-color: {cls.COLORS['background_secondary']};
    font-size: 16px;  /* 面板标题 (L2) - 按文档规范 */
    font-weight: bold;
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
}}

/* 异常监控标题 */
QLabel#AnomalyTitle {{
    font-weight: bold;
    color: {cls.COLORS['error']};
    font-size: 13px;
    background-color: transparent;
}}

/* 异常滚动区域 */
QScrollArea#anomaly_scroll {{
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 3px;
    background-color: {cls.COLORS['background_secondary']};
}}

/* 异常内容区域 */
QWidget#anomaly_content {{
    background-color: transparent;
}}
QWidget#anomaly_content > QWidget {{
    background-color: #4F3A3A;
    border-radius: 4px;
    margin-bottom: 4px;
}}
QWidget#anomaly_content QLabel {{
    color: #FFC0CB;
    background-color: transparent;
}}

/* 异常统计区域 */
QWidget#AnomalyStats {{
    background-color: {cls.COLORS['background_tertiary']};
    border-top: 1px solid {cls.COLORS['border_normal']};
    border-radius: 3px;
}}

/* 异常统计标题 */
QLabel#AnomalyStatsTitle {{
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    font-size: 12px;
    background-color: transparent;
}}

/* 异常统计数值 */
QLabel#AnomalyStatsValue {{
    font-size: 11px;
    color: {cls.COLORS['text_secondary']};
    font-weight: bold;
    background-color: transparent;
}}

/* ===== 3.1界面（历史数据查看器）专用样式 ===== */

/* QTabWidget 标签页样式 */
QTabWidget::pane {{
    border: 1px solid {cls.COLORS['border_normal']};
    border-top: none;
    border-radius: 0 0 8px 8px;
    background-color: {cls.COLORS['background_primary']};
}}

QTabBar::tab {{
    background-color: {cls.COLORS['background_secondary']};
    color: {cls.COLORS['text_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-bottom: none;
    padding: 10px 25px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: {cls.COLORS['background_primary']};
    color: {cls.COLORS['text_primary']};
    border-color: {cls.COLORS['border_normal']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    background-color: {cls.COLORS['hover']};
    color: {cls.COLORS['text_primary']};
}}

/* QTableWidget 表格样式 */
QTableWidget {{
    background-color: {cls.COLORS['background_secondary']};
    gridline-color: {cls.COLORS['border_normal']};
    border: 1px solid {cls.COLORS['border_normal']};
    color: {cls.COLORS['text_primary']};
    selection-background-color: {cls.COLORS['selection']};
    alternate-background-color: {cls.COLORS['background_tertiary']};
    border-radius: 6px;
}}

QHeaderView::section {{
    background-color: {cls.COLORS['background_tertiary']};
    color: {cls.COLORS['text_primary']};
    padding: 8px 12px;
    border: 1px solid {cls.COLORS['border_normal']};
    font-weight: bold;
    font-size: 13px;
}}

QHeaderView::section:hover {{
    background-color: {cls.COLORS['hover']};
}}

QTableWidget::item {{
    padding: 8px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {cls.COLORS['selection']};
    color: white;
}}

QTableWidget::item:hover {{
    background-color: {cls.COLORS['hover']};
}}

/* 历史数据查看器专用标题样式 */
QLabel#HistoryViewerTitle {{
    font-size: 18px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
    padding: 10px;
}}

/* 当前孔位显示标签样式 */
QLabel#CurrentHoleLabel {{
    font-weight: bold;
    color: {cls.COLORS['accent_primary']};
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 13px;
}}

/* 3D模型控制面板标题样式 */
QLabel#Model3DTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
}}

/* ===== 侧边栏样式 ===== */
QWidget#Sidebar {{
    background-color: {cls.COLORS['background_secondary']};
    max-width: 280px;
    min-width: 220px;
    border-right: 1px solid {cls.COLORS['border_normal']};
}}

/* 侧边栏收缩按钮样式 */
QToolButton#SidebarToggleButton {{
    background-color: {cls.COLORS['background_secondary']};
    border: none;
    width: 15px;
    color: {cls.COLORS['text_primary']};
}}

QToolButton#SidebarToggleButton:hover {{
    background-color: {cls.COLORS['accent_primary']};
}}

QToolButton#SidebarToggleButton:pressed {{
    background-color: {cls.COLORS['accent_pressed']};
}}

/* ===== 第四级【报告输出】界面专用样式 ===== */

/* 主标题样式 */
QLabel#MainTitle {{
    font-size: 20px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
    margin: 15px;
}}

/* ===== 定义通用的操作按钮样式 ===== */
/* 适用于"预览报告"、"查询数据"等次要操作按钮 */
QPushButton[class="ActionButton"] {{
    background-color: {cls.COLORS['background_tertiary']};
    color: {cls.COLORS['text_primary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 5px;
    padding: 8px 20px; /* 统一左右内边距 */
    min-height: 28px;
    font-weight: bold;
}}
QPushButton[class="ActionButton"]:hover {{
    background-color: {cls.COLORS['hover']};
    border-color: {cls.COLORS['accent_primary']};
}}
QPushButton[class="ActionButton"]:pressed {{
    background-color: {cls.COLORS['selection']};
}}

/* 适用于"生成报告"等主要操作按钮 */
QPushButton[class="PrimaryAction"] {{
    background-color: {cls.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px; /* 保证内边距与上面完全一致 */
    min-height: 28px;
    font-weight: bold;
}}
QPushButton[class="PrimaryAction"]:hover {{
    background-color: {cls.COLORS['accent_hover']};
}}
QPushButton[class="PrimaryAction"]:pressed {{
    background-color: {cls.COLORS['accent_pressed']};
}}

/* 删除按钮样式 */
QPushButton#DeleteButton {{
    background-color: {cls.COLORS['error']};
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    padding: 5px 10px;
}}
QPushButton#DeleteButton:hover {{
    background-color: #C0392B;
}}
QPushButton#DeleteButton:pressed {{
    background-color: #922B21;
}}

/* 状态标签样式 */
QLabel#StatusLabel {{
    font-size: 11px;
    margin: 5px;
    padding: 3px 6px;
    border-radius: 3px;
}}
QLabel#StatusLabel[status="success"] {{
    color: {cls.COLORS['success']};
    background-color: rgba(46, 204, 113, 0.1);
}}
QLabel#StatusLabel[status="warning"] {{
    color: {cls.COLORS['warning']};
    background-color: rgba(230, 126, 34, 0.1);
}}
QLabel#StatusLabel[status="error"] {{
    color: {cls.COLORS['error']};
    background-color: rgba(231, 76, 60, 0.1);
}}
QLabel#StatusLabel[status="info"] {{
    color: {cls.COLORS['info']};
    background-color: rgba(74, 144, 226, 0.1);
}}

/* 数据状态标签样式 */
QLabel#DataStatusLabel {{
    font-weight: bold;
    font-size: 13px;
    padding: 5px 10px;
    border-radius: 4px;
}}
QLabel#DataStatusLabel[status="loading"] {{
    color: {cls.COLORS['warning']};
    background-color: rgba(230, 126, 34, 0.1);
}}
QLabel#DataStatusLabel[status="success"] {{
    color: {cls.COLORS['success']};
    background-color: rgba(46, 204, 113, 0.1);
}}
QLabel#DataStatusLabel[status="warning"] {{
    color: {cls.COLORS['warning']};
    background-color: rgba(230, 126, 34, 0.1);
}}
QLabel#DataStatusLabel[status="error"] {{
    color: {cls.COLORS['error']};
    background-color: rgba(231, 76, 60, 0.1);
}}

/* 状态栏样式 */
QFrame#StatusFrame {{
    background-color: {cls.COLORS['status_bar']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    padding: 5px;
}}

QLabel#StatusBarLabel {{
    font-size: 14px;
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
}}

/* 报告进度条样式 */
QProgressBar#ReportProgressBar {{
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 5px;
    text-align: center;
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
    font-size: 13px;
    min-height: 25px;
}}
QProgressBar#ReportProgressBar::chunk {{
    background-color: {cls.COLORS['accent_primary']};
    border-radius: 4px;
}}

/* 对话框标题样式 */
QLabel#DialogTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
    margin: 10px;
}}

/* ===== QCheckBox 复选框样式 ===== */
QCheckBox {{
    spacing: 10px;
    color: {cls.COLORS['text_primary']};
    font-size: 14px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {cls.COLORS['border_normal']};
    background-color: {cls.COLORS['background_secondary']};
}}
QCheckBox::indicator:hover {{
    border-color: {cls.COLORS['accent_primary']};
}}
QCheckBox::indicator:checked {{
    background-color: {cls.COLORS['accent_primary']};
    border-color: {cls.COLORS['accent_primary']};
}}
QCheckBox::indicator:checked:hover {{
    background-color: {cls.COLORS['accent_hover']};
}}

/* 工具按钮样式 (用于表格操作等) */
QToolButton {{
    background: transparent;
    border: none;
    padding: 5px;
    border-radius: 4px;
    color: {cls.COLORS['text_secondary']};
}}
QToolButton:hover {{
    background-color: {cls.COLORS['hover']};
    color: {cls.COLORS['text_primary']};
}}
QToolButton:pressed {{
    background-color: {cls.COLORS['selection']};
}}

/* ===== 数据仪表盘样式 ===== */

/* 仪表盘大号数字样式 */
QLabel#DashboardNumber {{
    font-size: 36px;
    font-weight: bold;
    color: {cls.COLORS['text_primary']};
    background-color: transparent;
    border: none;
    padding: 5px;
    qproperty-alignment: 'AlignCenter';
}}

/* 仪表盘中的普通标签样式 */
QGroupBox QGridLayout QLabel {{
    font-size: 14px;
    color: {cls.COLORS['text_secondary']};
    background-color: transparent;
    border: none;
    padding: 2px;
}}

/* 仪表盘进度条的特定样式 */
QProgressBar#DashboardRateBar {{
    border: 2px solid {cls.COLORS['border_normal']};
    border-radius: 8px;
    text-align: center;
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
    font-size: 14px;
    min-height: 20px;
    max-height: 20px;
    background-color: {cls.COLORS['background_secondary']};
}}
QProgressBar#DashboardRateBar::chunk {{
    background-color: {cls.COLORS['success']};
    border-radius: 6px;
    margin: 1px;
}}

/* 仪表盘工件信息标签样式 */
QLabel[objectName*="db_workpiece"] {{
    font-size: 15px;
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
    background-color: transparent;
    border: none;
    padding: 3px;
}}

/* ===== 步骤序号样式 ===== */

/* 步骤序号标签样式 */
QLabel#StepNumberLabel {{
    font-size: 16px;
    font-weight: bold;
    color: white;
    background-color: {cls.COLORS['accent_primary']};
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    border-radius: 12px;
    qproperty-alignment: 'AlignCenter';
    margin-right: 8px;
}}

/* 步骤标题标签样式 */
QLabel#StepTitleLabel {{
    font-size: 16px;
    font-weight: bold;
    color: {cls.COLORS['accent_primary']};
    background-color: transparent;
    border: none;
    padding: 2px 0px;
}}

/* ===== 主窗口特殊组件样式 ===== */

/* 全景预览组件 */
QWidget#PanoramaWidget {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
}}

/* 扇形统计标签 */
QLabel#SectorStatsLabel {{
    background-color: {cls.COLORS['background_secondary']};
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 4px;
    padding: 12px;
    color: {cls.COLORS['text_primary']};
}}

/* 状态颜色标签 */
QLabel#StatusColorLabel {{
    border: 1px solid {cls.COLORS['border_normal']};
    border-radius: 2px;
    min-width: 16px;
    min-height: 16px;
}}

/* 视图状态标签 */
QLabel#ViewStatusLabel {{
    color: {cls.COLORS['text_secondary']};
    font-style: italic;
}}

/* 选中孔位状态标签 */
QLabel#SelectedHoleStatusLabel {{
    color: {cls.COLORS['text_primary']};
    font-weight: bold;
}}
QLabel#SelectedHoleStatusLabel[status_type="qualified"] {{
    color: {cls.COLORS['success']};
}}
QLabel#SelectedHoleStatusLabel[status_type="unqualified"] {{
    color: {cls.COLORS['error']};
}}
QLabel#SelectedHoleStatusLabel[status_type="warning"] {{
    color: {cls.COLORS['warning']};
}}

/* ===== 特殊组件强制深色主题 ===== */

/* 内窥镜视图 */
QGraphicsView#EndoscopeGraphicsView {{
    background-color: {cls.COLORS['background_secondary']} !important;
    border: 2px solid {cls.COLORS['border_normal']} !important;
    border-radius: 5px;
}}

/* 强制覆盖所有白色背景 */
* {{
    background-color: transparent;
}}

/* 主要容器必须使用深色背景 */
QMainWindow > QWidget {{
    background-color: {cls.COLORS['background_primary']} !important;
}}

/* 中央部件深色背景 */
QMainWindow > QWidget > QWidget {{
    background-color: {cls.COLORS['background_primary']} !important;
}}

/* 表格深色主题 */
QTableWidget, QTableView {{
    background-color: {cls.COLORS['background_secondary']} !important;
    gridline-color: {cls.COLORS['border_normal']} !important;
    color: {cls.COLORS['text_primary']} !important;
}}

/* 输入框深色主题 */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {cls.COLORS['background_secondary']} !important;
    color: {cls.COLORS['text_primary']} !important;
    border: 1px solid {cls.COLORS['border_normal']} !important;
}}

/* 列表深色主题 */
QListWidget, QListView {{
    background-color: {cls.COLORS['background_secondary']} !important;
    color: {cls.COLORS['text_primary']} !important;
}}

/* 标签深色主题 */
QLabel {{
    background-color: transparent;
    color: {cls.COLORS['text_primary']} !important;
}}
"""

    @classmethod
    def apply_dark_theme_2d(cls, figure, axes):
        """应用2D图表的深色主题样式 - 按UI设计规范文档"""
        figure.patch.set_facecolor(cls.COLORS['background_secondary'])  # 面板背景色
        axes.set_facecolor(cls.COLORS['background_secondary'])  # 面板背景色
        axes.spines['bottom'].set_color(cls.COLORS['border_normal'])  # 边框/分割线
        axes.spines['top'].set_color(cls.COLORS['border_normal'])
        axes.spines['left'].set_color(cls.COLORS['border_normal'])
        axes.spines['right'].set_color(cls.COLORS['border_normal'])
        axes.tick_params(axis='x', colors=cls.COLORS['text_primary'])  # 主文本/图标色
        axes.tick_params(axis='y', colors=cls.COLORS['text_primary'])
        axes.xaxis.label.set_color(cls.COLORS['text_primary'])
        axes.yaxis.label.set_color(cls.COLORS['text_primary'])
        axes.title.set_color(cls.COLORS['text_secondary'])  # 标题/醒目文字
        axes.grid(True, color=cls.COLORS['border_normal'], linestyle='--', alpha=0.5)

    @classmethod
    def apply_dark_theme_3d(cls, figure, axes):
        """应用3D图表的深色主题样式 - 按UI设计规范文档"""
        figure.patch.set_facecolor(cls.COLORS['background_primary'])  # 主背景色
        axes.set_facecolor(cls.COLORS['background_primary'])
        axes.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        axes.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        axes.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        # 设置轴线颜色
        axes.xaxis.line.set_color(cls.COLORS['border_normal'])
        axes.yaxis.line.set_color(cls.COLORS['border_normal'])
        axes.zaxis.line.set_color(cls.COLORS['border_normal'])
        # 设置刻度标签颜色
        axes.tick_params(axis='x', colors=cls.COLORS['text_primary'])
        axes.tick_params(axis='y', colors=cls.COLORS['text_primary'])
        axes.tick_params(axis='z', colors=cls.COLORS['text_primary'])
        # 设置轴标签颜色
        axes.set_xlabel(axes.get_xlabel(), color=cls.COLORS['text_primary'])
        axes.set_ylabel(axes.get_ylabel(), color=cls.COLORS['text_primary'])
        axes.set_zlabel(axes.get_zlabel(), color=cls.COLORS['text_primary'])
        # 设置标题颜色
        axes.set_title(axes.get_title(), color=cls.COLORS['text_secondary'])

    @classmethod
    def apply_theme(cls, app: QApplication, theme_type="dark"):
        """应用主题到应用程序"""
        if theme_type == "dark":
            cls.apply_dark_theme(app)
        else:
            cls.apply_light_theme(app)
    
    @classmethod
    def apply_dark_theme(cls, app: QApplication):
        """应用深色主题（默认主题）"""
        # 获取完整的样式表
        stylesheet = cls.get_main_stylesheet()
        
        # 应用到应用程序
        app.setStyleSheet(stylesheet)
        
        # 设置应用程序调色板为深色
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        palette = QPalette()
        # 窗口背景
        palette.setColor(QPalette.Window, QColor(cls.COLORS['background_primary']))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS['text_primary']))
        # 基础背景
        palette.setColor(QPalette.Base, QColor(cls.COLORS['background_secondary']))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLORS['background_tertiary']))
        # 文本
        palette.setColor(QPalette.Text, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.BrightText, QColor(cls.COLORS['text_secondary']))
        # 按钮
        palette.setColor(QPalette.Button, QColor(cls.COLORS['background_tertiary']))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLORS['text_primary']))
        # 高亮
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS['accent_primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        
        logging.info("现代科技蓝深色主题已应用（默认主题）")
    
    @classmethod
    def apply_light_theme(cls, app: QApplication):
        """应用浅色主题（可选主题）"""
        # 浅色主题样式表
        light_stylesheet = cls.get_light_stylesheet()
        app.setStyleSheet(light_stylesheet)
        
        # 设置浅色调色板
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtCore import Qt
        
        palette = QPalette()
        # 浅色主题颜色
        palette.setColor(QPalette.Window, QColor("#F5F5F5"))
        palette.setColor(QPalette.WindowText, QColor("#2C2C2C"))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.AlternateBase, QColor("#F0F0F0"))
        palette.setColor(QPalette.Text, QColor("#2C2C2C"))
        palette.setColor(QPalette.BrightText, QColor("#000000"))
        palette.setColor(QPalette.Button, QColor("#E0E0E0"))
        palette.setColor(QPalette.ButtonText, QColor("#2C2C2C"))
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS['accent_primary']))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        
        app.setPalette(palette)
        
        logging.info("浅色主题已应用（可选主题）")
    
    @classmethod
    def get_light_stylesheet(cls) -> str:
        """获取浅色主题样式表"""
        return f"""
/* 浅色主题样式表 */
QWidget {{
    background-color: #F5F5F5;
    color: #2C2C2C;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC";
    font-size: 15px;
}}

QMainWindow, QDialog, QFrame {{
    background-color: #F5F5F5;
}}

QGroupBox {{
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
}}

QGroupBox::title {{
    color: #2C2C2C;
    font-size: 16px;
    font-weight: bold;
}}

QPushButton {{
    background-color: {cls.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {cls.COLORS['accent_hover']};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #FFFFFF;
    color: #2C2C2C;
    border: 1px solid #D0D0D0;
    border-radius: 4px;
    padding: 6px;
}}

QTableWidget, QTableView {{
    background-color: #FFFFFF;
    gridline-color: #E0E0E0;
    color: #2C2C2C;
}}

QLabel {{
    color: #2C2C2C;
}}
"""
    
    @classmethod
    def force_dark_theme(cls, widget):
        """强制为特定widget应用深色主题"""
        # 如果widget有内联样式，清除它
        if widget.styleSheet():
            widget.setStyleSheet("")
            
        # 应用深色调色板
        from PySide6.QtGui import QPalette, QColor
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(cls.COLORS['background_primary']))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.Base, QColor(cls.COLORS['background_secondary']))
        palette.setColor(QPalette.Text, QColor(cls.COLORS['text_primary']))
        widget.setPalette(palette)
        
        # 强制更新
        widget.update()


# 全局主题管理器实例
theme_manager = ModernThemeManager()
