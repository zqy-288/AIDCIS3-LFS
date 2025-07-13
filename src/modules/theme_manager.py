"""
现代科技蓝主题管理器
提供统一的UI样式和配色方案
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
import logging


class ModernThemeManager:
    """现代科技蓝主题管理器"""
    
    # 现代科技蓝配色方案
    COLORS = {
        # 主背景色
        'background_primary': '#2C313C',
        'background_secondary': '#3A404E',
        'background_tertiary': '#505869',
        
        # 强调色
        'accent_primary': '#007ACC',
        'accent_secondary': '#4A90E2',
        'accent_hover': '#0099FF',
        'accent_pressed': '#005C99',
        
        # 文本色
        'text_primary': '#F0F0F0',
        'text_secondary': '#CCCCCC',
        'text_disabled': '#AAAAAA',
        
        # 状态色
        'success': '#2ECC71',
        'warning': '#E67E22',
        'error': '#E74C3C',
        'info': '#4A90E2',
        
        # 边框色
        'border_normal': '#505869',
        'border_focus': '#007ACC',
        'border_disabled': '#555555',
        
        # 特殊背景
        'status_bar': '#1E222B',
        'selection': '#007ACC',
        'hover': '#3A404E'
    }
    
    @classmethod
    def get_main_stylesheet(cls) -> str:
        """获取主样式表"""
        return f"""
/* 整体窗口和字体设置 */
QWidget {{
    background-color: {cls.COLORS['background_primary']};
    color: {cls.COLORS['text_primary']};
    font-family: "Segoe UI", "Microsoft YaHei";
    font-size: 15px;  /* 从14px增大到15px，提升可读性 */
}}

/* 按钮样式 */
QPushButton {{
    background-color: {cls.COLORS['accent_primary']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
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
    color: {cls.COLORS['text_primary']};
    border: 2px solid {cls.COLORS['border_normal']};
    border-radius: 6px;
    margin-top: 12px;
    margin-bottom: 8px;  /* 增加底部外边距，提升空间感 */
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: {cls.COLORS['accent_secondary']};
}}

/* 状态仪表盘样式 */
QGroupBox#StatusDashboard {{
    border: 2px solid {cls.COLORS['accent_primary']};
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 10px;
    background-color: {cls.COLORS['background_secondary']};
}}
QGroupBox#StatusDashboard::title {{
    color: {cls.COLORS['accent_primary']};
    font-size: 16px;
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
    background-color: {cls.COLORS['background_secondary']};
    border: 2px solid {cls.COLORS['success']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    font-size: 15px;
}}
QGroupBox#PanelA::title {{
    color: {cls.COLORS['success']};
    background-color: {cls.COLORS['background_secondary']};
    font-size: 15px;
    font-weight: bold;
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 10px 0 10px;
}}

/* 面板B样式 - 内窥镜图像 */
QGroupBox#PanelB {{
    background-color: {cls.COLORS['background_secondary']};
    border: 2px solid {cls.COLORS['accent_primary']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
    font-size: 15px;
}}
QGroupBox#PanelB::title {{
    color: {cls.COLORS['accent_primary']};
    background-color: {cls.COLORS['background_secondary']};
    font-size: 15px;
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
    background-color: #3A3232;
    border: 2px solid {cls.COLORS['warning']};
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 8px;
    font-size: 14px;
    font-weight: bold;
}}
QGroupBox#anomaly_widget::title {{
    color: {cls.COLORS['warning']};
    background-color: #3A3232;
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
"""

    @classmethod
    def apply_theme(cls, app: QApplication):
        """应用主题到应用程序"""
        app.setStyleSheet(cls.get_main_stylesheet())
        logging.info("现代科技蓝主题已应用")


# 全局主题管理器实例
theme_manager = ModernThemeManager()
