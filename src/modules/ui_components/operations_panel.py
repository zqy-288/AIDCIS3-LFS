"""
操作面板组件
从main_window.py重构提取的独立UI组件
负责检测控制、模拟功能、视图控制、孔位操作和操作日志等功能
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QTextEdit, QGroupBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

# 导入插件系统
from plugins.ui.hole_view_filter_plugin import HoleViewFilterPlugin, HoleViewFilterComponent


class OperationsPanel(QScrollArea):
    """
    操作面板组件
    包含检测控制、模拟功能、视图控制、孔位操作和操作日志等功能
    """
    
    # 定义信号
    # 检测控制信号
    start_detection_requested = Signal()
    pause_detection_requested = Signal()
    stop_detection_requested = Signal()
    
    # 模拟功能信号
    simulate_requested = Signal()
    
    # 视图控制信号
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    fit_view_requested = Signal()
    reset_view_requested = Signal()
    
    # 孔位操作信号
    goto_realtime_requested = Signal()
    goto_history_requested = Signal()
    mark_defective_requested = Signal()
    goto_report_requested = Signal()
    
    # 过滤器信号
    view_filter_changed = Signal(dict)
    filter_status_updated = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
        # 过滤器组件已移动到顶部，不再在操作面板中初始化
        # self.view_filter_plugin = HoleViewFilterPlugin()
        # self.view_filter_component = None
        # self.setup_view_filter()
    
    def setup_ui(self):
        """设置UI组件"""
        self.setWidgetResizable(True)
        self.setMaximumWidth(350)  # 设置最大宽度
        
        # 创建主要内容区域
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 设置字体
        self.setup_fonts()
        
        # 创建各功能组
        self.create_detection_control_group(layout)
        self.create_simulation_group(layout)
        # self.create_view_filter_group(layout)  # 移除过滤器组，现在在顶部显示
        self.create_view_control_group(layout)
        self.create_hole_operations_group(layout)
        self.create_log_group(layout)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 设置主要内容区域
        self.setWidget(content_widget)
    
    def setup_fonts(self):
        """设置字体"""
        self.panel_font = QFont()
        self.panel_font.setPointSize(11)
        
        self.group_title_font = QFont()
        self.group_title_font.setPointSize(12)
        self.group_title_font.setBold(True)
        
        self.button_font = QFont()
        self.button_font.setPointSize(11)
    
    def create_detection_control_group(self, layout):
        """创建检测控制组"""
        detection_group = QGroupBox("检测控制")
        detection_group.setFont(self.group_title_font)
        detection_layout = QVBoxLayout(detection_group)
        
        # 开始检测按钮
        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setMinimumHeight(45)
        self.start_detection_btn.setFont(self.button_font)
        self.start_detection_btn.setEnabled(False)
        
        # 暂停检测按钮
        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setMinimumHeight(45)
        self.pause_detection_btn.setFont(self.button_font)
        self.pause_detection_btn.setEnabled(False)
        
        # 停止检测按钮
        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setMinimumHeight(45)
        self.stop_detection_btn.setFont(self.button_font)
        self.stop_detection_btn.setEnabled(False)
        
        detection_layout.addWidget(self.start_detection_btn)
        detection_layout.addWidget(self.pause_detection_btn)
        detection_layout.addWidget(self.stop_detection_btn)
        
        layout.addWidget(detection_group)
    
    def create_simulation_group(self, layout):
        """创建模拟功能组"""
        simulation_group = QGroupBox("模拟功能")
        simulation_group.setFont(self.group_title_font)
        simulation_layout = QVBoxLayout(simulation_group)
        
        # 模拟按钮
        self.simulate_btn = QPushButton("使用模拟进度")
        self.simulate_btn.setMinimumHeight(45)
        self.simulate_btn.setFont(self.button_font)
        self.simulate_btn.setEnabled(False)
        
        simulation_layout.addWidget(self.simulate_btn)
        layout.addWidget(simulation_group)
    
    def create_view_filter_group(self, layout):
        """创建视图过滤器组"""
        self.filter_group = QGroupBox("孔位过滤")
        self.filter_group.setFont(self.group_title_font)
        self.filter_layout = QVBoxLayout(self.filter_group)
        
        # 初始化时添加占位标签
        placeholder_label = QLabel("过滤器加载中...")
        placeholder_label.setFont(self.panel_font)
        self.filter_layout.addWidget(placeholder_label)
        
        layout.addWidget(self.filter_group)
    
    def create_view_control_group(self, layout):
        """创建视图控制组"""
        view_control_group = QGroupBox("视图控制")
        view_control_group.setFont(self.group_title_font)
        view_control_layout = QGridLayout(view_control_group)
        
        # 视图控制按钮
        self.zoom_in_btn = QPushButton("放大")
        self.zoom_out_btn = QPushButton("缩小")
        self.fit_view_btn = QPushButton("适应窗口")
        self.reset_view_btn = QPushButton("重置视图")
        
        # 设置视图控制按钮字体和高度
        view_control_buttons = [self.zoom_in_btn, self.zoom_out_btn, self.fit_view_btn, self.reset_view_btn]
        for btn in view_control_buttons:
            btn.setFont(self.button_font)
            btn.setMinimumHeight(40)
            btn.setEnabled(False)
        
        view_control_layout.addWidget(self.zoom_in_btn, 0, 0)
        view_control_layout.addWidget(self.zoom_out_btn, 0, 1)
        view_control_layout.addWidget(self.fit_view_btn, 1, 0)
        view_control_layout.addWidget(self.reset_view_btn, 1, 1)
        
        layout.addWidget(view_control_group)
    
    def create_hole_operations_group(self, layout):
        """创建孔位操作组"""
        hole_ops_group = QGroupBox("孔位操作")
        hole_ops_group.setFont(self.group_title_font)
        hole_ops_layout = QVBoxLayout(hole_ops_group)
        
        # 实时监控按钮
        self.goto_realtime_btn = QPushButton("实时监控")
        self.goto_realtime_btn.setMinimumHeight(40)
        self.goto_realtime_btn.setFont(self.button_font)
        self.goto_realtime_btn.setEnabled(False)
        
        # 历史数据按钮
        self.goto_history_btn = QPushButton("历史数据")
        self.goto_history_btn.setMinimumHeight(40)
        self.goto_history_btn.setFont(self.button_font)
        self.goto_history_btn.setEnabled(False)
        
        # 标记异常按钮
        self.mark_defective_btn = QPushButton("标记异常")
        self.mark_defective_btn.setMinimumHeight(40)
        self.mark_defective_btn.setFont(self.button_font)
        self.mark_defective_btn.setEnabled(False)
        
        # 生成报告按钮
        self.goto_report_btn = QPushButton("生成报告")
        self.goto_report_btn.setMinimumHeight(40)
        self.goto_report_btn.setFont(self.button_font)
        # 使用主题管理器的警告色样式
        self.goto_report_btn.setObjectName("WarningButton")
        self.goto_report_btn.setEnabled(True)  # 报告生成总是可用
        
        hole_ops_layout.addWidget(self.goto_realtime_btn)
        hole_ops_layout.addWidget(self.goto_history_btn)
        hole_ops_layout.addWidget(self.mark_defective_btn)
        hole_ops_layout.addWidget(self.goto_report_btn)
        
        layout.addWidget(hole_ops_group)
    
    def create_log_group(self, layout):
        """创建操作日志组"""
        log_group = QGroupBox("操作日志")
        log_group.setFont(self.group_title_font)
        log_layout = QVBoxLayout(log_group)
        
        # 日志文本编辑器
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.panel_font)
        
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
    
    # 过滤器相关方法已移除，因为过滤器现在在顶部显示
    # def setup_view_filter(self):
    #     """设置视图过滤器"""
    #     try:
    #         # 初始化视图过滤器组件
    #         if self.view_filter_plugin.initialize():
    #             self.view_filter_component = self.view_filter_plugin.get_component()
    #             if self.view_filter_component and self.view_filter_component.initialize():
    #                 filter_widget = self.view_filter_component.get_widget()
    #                 if filter_widget:
    #                     # 清空原有内容
    #                     for i in reversed(range(self.filter_layout.count())):
    #                         self.filter_layout.itemAt(i).widget().setParent(None)
    #                     
    #                     # 添加过滤器widget
    #                     self.filter_layout.addWidget(filter_widget)
    #                     
    #                     # 连接过滤器信号
    #                     self.view_filter_component.filter_changed.connect(self._on_view_filter_changed)
    #                     self.view_filter_component.status_updated.connect(self._on_filter_status_updated)
    #                     return True
    #                 
    #     except Exception as e:
    #         print(f"过滤器初始化失败: {e}")
    #     
    #     # 如果初始化失败，显示错误信息
    #     self._show_filter_error()
    #     return False
    
    # def _show_filter_error(self):
    #     """显示过滤器错误信息"""
    #     # 清空原有内容
    #     for i in reversed(range(self.filter_layout.count())):
    #         self.filter_layout.itemAt(i).widget().setParent(None)
    #     
    #     # 添加错误标签
    #     error_label = QLabel("过滤器加载失败")
    #     error_label.setFont(self.panel_font)
    #     self.filter_layout.addWidget(error_label)
    
    def setup_connections(self):
        """设置信号连接"""
        # 检测控制信号
        self.start_detection_btn.clicked.connect(self.start_detection_requested.emit)
        self.pause_detection_btn.clicked.connect(self.pause_detection_requested.emit)
        self.stop_detection_btn.clicked.connect(self.stop_detection_requested.emit)
        
        # 模拟功能信号
        self.simulate_btn.clicked.connect(self.simulate_requested.emit)
        
        # 视图控制信号
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        self.fit_view_btn.clicked.connect(self.fit_view_requested.emit)
        self.reset_view_btn.clicked.connect(self.reset_view_requested.emit)
        
        # 孔位操作信号
        self.goto_realtime_btn.clicked.connect(self.goto_realtime_requested.emit)
        self.goto_history_btn.clicked.connect(self.goto_history_requested.emit)
        self.mark_defective_btn.clicked.connect(self.mark_defective_requested.emit)
        self.goto_report_btn.clicked.connect(self.goto_report_requested.emit)
    
    # 过滤器相关事件处理方法已移除
    # def _on_view_filter_changed(self, filter_data):
    #     """处理过滤器变化"""
    #     self.view_filter_changed.emit(filter_data)
    
    # def _on_filter_status_updated(self, status):
    #     """处理过滤器状态更新"""
    #     self.filter_status_updated.emit(status)
    
    # 公共方法
    def set_detection_enabled(self, enabled: bool):
        """设置检测控制按钮状态"""
        self.start_detection_btn.setEnabled(enabled)
        self.pause_detection_btn.setEnabled(enabled)
        self.stop_detection_btn.setEnabled(enabled)
    
    def set_simulation_enabled(self, enabled: bool):
        """设置模拟功能按钮状态"""
        self.simulate_btn.setEnabled(enabled)
    
    def set_view_control_enabled(self, enabled: bool):
        """设置视图控制按钮状态"""
        self.zoom_in_btn.setEnabled(enabled)
        self.zoom_out_btn.setEnabled(enabled)
        self.fit_view_btn.setEnabled(enabled)
        self.reset_view_btn.setEnabled(enabled)
    
    def set_hole_operations_enabled(self, enabled: bool):
        """设置孔位操作按钮状态"""
        self.goto_realtime_btn.setEnabled(enabled)
        self.goto_history_btn.setEnabled(enabled)
        self.mark_defective_btn.setEnabled(enabled)
        # 报告生成总是可用
        # self.goto_report_btn.setEnabled(True)
    
    def append_log(self, message: str):
        """追加日志信息"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.moveCursor(self.log_text.textCursor().End)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def get_log_text(self) -> str:
        """获取日志文本"""
        return self.log_text.toPlainText()
    
    # 过滤器组件获取方法已移除
    # def get_view_filter_component(self):
    #     """获取视图过滤器组件"""
    #     return self.view_filter_component
    
    def set_detection_button_states(self, started: bool, paused: bool):
        """设置检测按钮状态"""
        if started:
            self.start_detection_btn.setEnabled(False)
            self.pause_detection_btn.setEnabled(True)
            self.stop_detection_btn.setEnabled(True)
        elif paused:
            self.start_detection_btn.setEnabled(True)
            self.pause_detection_btn.setEnabled(False)
            self.stop_detection_btn.setEnabled(True)
        else:
            self.start_detection_btn.setEnabled(True)
            self.pause_detection_btn.setEnabled(False)
            self.stop_detection_btn.setEnabled(False)
    
    def update_detection_button_text(self, start_text: str = "开始检测", pause_text: str = "暂停检测", stop_text: str = "停止检测"):
        """更新检测按钮文本"""
        self.start_detection_btn.setText(start_text)
        self.pause_detection_btn.setText(pause_text)
        self.stop_detection_btn.setText(stop_text)