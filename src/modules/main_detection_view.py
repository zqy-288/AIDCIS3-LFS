"""
一级页面 - 主检测视图
提供整个检测任务的宏观状态概览，采用三栏式布局：信息、预览、操作。
"""

from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QProgressBar, QGroupBox,
                               QLineEdit, QTextEdit, QFrame, QSplitter, QCompleter)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel
from PySide6.QtGui import QFont

from .workpiece_diagram import WorkpieceDiagram, DetectionStatus


class MainDetectionView(QWidget):
    """主检测视图 - 一级页面"""
    
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.setup_ui()
        self.setup_connections()
        self.initialize_data()
        
    def setup_ui(self):
        """设置用户界面 - 三栏式布局"""
        main_layout = QHBoxLayout(self)
        
        # 创建左、中、右三栏
        left_panel = self._create_left_panel()
        middle_panel = self._create_middle_panel()
        right_panel = self._create_right_panel()
        
        # 设置各栏的宽度比例和策略
        # 设置各栏的固定宽度
        left_panel.setFixedWidth(300)  # 左侧固定宽度
        right_panel.setFixedWidth(350) # 右侧固定宽度
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel, 1)  # 中间栏占据更多空间
        main_layout.addWidget(right_panel)

    def _create_left_panel(self):
        """创建左侧信息面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 5, 0)
        layout.setSpacing(10)

        # 1. 文件信息
        self.file_info_panel = QGroupBox("文件信息")
        file_layout = QGridLayout(self.file_info_panel)
        file_layout.addWidget(QLabel("DXF文件:"), 0, 0)
        self.dxf_file_label = QLabel("未加载")
        self.dxf_file_label.setTextFormat(Qt.PlainText)
        self.dxf_file_label.setTextElideMode(Qt.ElideMiddle) # 文本中间显示省略号
        self.dxf_file_label.setWordWrap(False) # 不自动换行
        self.dxf_file_label.setMaximumWidth(200) # 强制最大宽度，确保文本截断
        self.dxf_file_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred) # 宽度固定，高度自适应
        file_layout.addWidget(self.dxf_file_label, 0, 1)
        layout.addWidget(self.file_info_panel)

        # 2. 状态统计
        self.stats_panel = QGroupBox("状态统计")
        stats_layout = QGridLayout(self.stats_panel)
        stats_layout.addWidget(QLabel("总孔数:"), 0, 0)
        self.total_label = QLabel("0")
        stats_layout.addWidget(self.total_label, 0, 1)
        stats_layout.addWidget(QLabel("合格:"), 1, 0)
        self.qualified_label = QLabel("0")
        stats_layout.addWidget(self.qualified_label, 1, 1)
        stats_layout.addWidget(QLabel("不合格:"), 2, 0)
        self.unqualified_label = QLabel("0")
        stats_layout.addWidget(self.unqualified_label, 2, 1)
        stats_layout.addWidget(QLabel("待检:"), 3, 0)
        self.not_detected_label = QLabel("0")
        stats_layout.addWidget(self.not_detected_label, 3, 1)
        layout.addWidget(self.stats_panel)

        # 3. 检测进度
        self.progress_panel = QGroupBox("检测进度")
        progress_layout = QHBoxLayout(self.progress_panel)
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.progress_label = QLabel("0%")
        progress_layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_panel)

        # 4. 孔位信息
        self.hole_info_panel = QGroupBox("孔位信息")
        hole_info_layout = QGridLayout(self.hole_info_panel)
        hole_info_layout.addWidget(QLabel("选中ID:"), 0, 0)
        self.selected_hole_id_label = QLabel("--")
        hole_info_layout.addWidget(self.selected_hole_id_label, 0, 1)
        hole_info_layout.addWidget(QLabel("坐标:"), 1, 0)
        self.selected_hole_pos_label = QLabel("--")
        hole_info_layout.addWidget(self.selected_hole_pos_label, 1, 1)
        hole_info_layout.addWidget(QLabel("状态:"), 2, 0)
        self.selected_hole_status_label = QLabel("--")
        hole_info_layout.addWidget(self.selected_hole_status_label, 2, 1)
        layout.addWidget(self.hole_info_panel)

        layout.addStretch()
        return panel

    def _create_middle_panel(self):
        """创建中间DXF预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 5, 0)

        # 1. 状态图例 (从WorkpieceDiagram中提取)
        self.legend_frame = self._create_status_legend_widget()
        layout.addWidget(self.legend_frame)

        # 2. DXF预览
        self.workpiece_diagram = WorkpieceDiagram()
        layout.addWidget(self.workpiece_diagram, 1)
        
        return panel

    def _create_right_panel(self):
        """创建右侧操作面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(10)

        # 1. 检测操作
        self.control_panel = ControlPanel()
        layout.addWidget(self.control_panel)

        # 2. 视图控制
        view_control_panel = QGroupBox("视图控制")
        view_control_layout = QHBoxLayout(view_control_panel)
        self.zoom_in_button = QPushButton("放大")
        self.zoom_out_button = QPushButton("缩小")
        self.reset_zoom_button = QPushButton("重置")
        view_control_layout.addWidget(self.zoom_in_button)
        view_control_layout.addWidget(self.zoom_out_button)
        view_control_layout.addWidget(self.reset_zoom_button)
        layout.addWidget(view_control_panel)

        # 3. 孔位操作 (带联想搜索)
        hole_op_panel = QGroupBox("孔位操作")
        hole_op_layout = QVBoxLayout(hole_op_panel)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入孔位ID...")
        self.search_button = QPushButton("确定")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        hole_op_layout.addLayout(search_layout)
        layout.addWidget(hole_op_panel)

        # 4. 操作日志
        log_panel = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_panel)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_layout.addWidget(self.log_text_edit)
        layout.addWidget(log_panel)

        layout.addStretch()
        return panel

    def _create_status_legend_widget(self):
        """创建独立的状态图例小部件"""
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(5, 5, 5, 5)
        
        statuses = [
            ("未检测", "#808080"), ("正在检测", "#ffff00"),
            ("合格", "#00ff00"), ("不合格", "#ff0000"),
            ("真实数据", "#ffa500")
        ]
        
        for text, color in statuses:
            color_label = QLabel()
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            legend_layout.addWidget(color_label)
            legend_layout.addWidget(QLabel(text))
            legend_layout.addSpacing(10)
        
        legend_layout.addStretch()
        return legend_frame

    def setup_connections(self):
        """设置所有信号和槽的连接"""
        # 预览图点击
        self.workpiece_diagram.hole_clicked.connect(self.on_hole_clicked)
        
        # 检测操作按钮
        self.control_panel.start_detection.connect(self.on_start_detection)
        self.control_panel.pause_detection.connect(self.on_pause_detection)
        self.control_panel.stop_detection.connect(self.on_stop_detection)
        self.control_panel.reset_detection.connect(self.on_reset_detection)
        
        # 视图控制按钮
        self.zoom_in_button.clicked.connect(self.workpiece_diagram.zoom_in)
        self.zoom_out_button.clicked.connect(self.workpiece_diagram.zoom_out)
        self.reset_zoom_button.clicked.connect(self.workpiece_diagram.reset_zoom)

        # 孔位搜索功能
        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.search_input.returnPressed.connect(self.on_search_button_clicked)
        
        # 定时器更新进度
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress_display)
        self.update_timer.start(1000)

    def initialize_data(self):
        """初始化数据和UI状态"""
        self.log_message("系统初始化完成。")
        self.update_progress_display()
        
        # 初始化联想搜索
        all_holes = self.workpiece_diagram.get_all_holes()
        completer = QCompleter(all_holes, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(completer)
        completer.activated.connect(self.on_search_activated)

    def on_hole_clicked(self, hole_id, status):
        """处理孔点击事件，更新信息面板"""
        self.log_message(f"选中孔位: {hole_id}, 状态: {status.value}")
        self.update_hole_info_panel(hole_id)
        self.workpiece_diagram.highlight_hole(hole_id)

    def on_search_button_clicked(self):
        """处理搜索按钮点击或回车事件"""
        hole_id = self.search_input.text().strip().upper()
        self.handle_search(hole_id)

    def on_search_activated(self, hole_id):
        """处理从联想菜单选择的事件"""
        self.search_input.setText(hole_id)
        self.handle_search(hole_id)

    def handle_search(self, hole_id):
        """统一处理搜索逻辑"""
        if hole_id in self.workpiece_diagram.get_all_holes():
            self.log_message(f"通过搜索定位到孔: {hole_id}")
            self.update_hole_info_panel(hole_id)
            self.workpiece_diagram.highlight_hole(hole_id)
            self.workpiece_diagram.center_on_hole(hole_id)
        else:
            self.log_message(f"警告: 未找到孔位 '{hole_id}'", "orange")

    def update_hole_info_panel(self, hole_id):
        """更新左侧的孔位信息面板"""
        point = self.workpiece_diagram.detection_points.get(hole_id)
        if point:
            self.selected_hole_id_label.setText(hole_id)
            self.selected_hole_pos_label.setText(f"({point.x():.2f}, {point.y():.2f})")
            self.selected_hole_status_label.setText(point.status.value)
            self.current_hole_id = hole_id

    def update_progress_display(self):
        """更新进度和统计信息"""
        data = self.workpiece_diagram.get_detection_progress()
        
        # 更新统计面板
        self.total_label.setText(str(data.get("total", 0)))
        self.qualified_label.setText(str(data.get("qualified", 0)))
        self.unqualified_label.setText(str(data.get("unqualified", 0)))
        self.not_detected_label.setText(str(data.get("not_detected", 0) + data.get("real_data", 0)))

        # 更新进度条
        progress = data.get("progress", 0.0)
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"{progress:.1f}%")

    def log_message(self, message, color="black"):
        """向操作日志面板添加一条带时间戳的消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text_edit.append(f'<font color="{color}">[{timestamp}] {message}</font>')

    # --- 保留旧的控制逻辑 ---
    def on_start_detection(self):
        self.log_message("开始检测流程...", "blue")
        # ... (原有的逻辑)

    def on_pause_detection(self):
        self.log_message("检测暂停。", "orange")
        # ... (原有的逻辑)

    def on_stop_detection(self):
        self.log_message("检测停止。", "red")
        # ... (原有的逻辑)

    def on_reset_detection(self):
        self.workpiece_diagram.reset_all_holes()
        self.log_message("检测已重置。", "purple")
        # ... (原有的逻辑)


class ControlPanel(QGroupBox):
    """(基本无变化) 控制面板组件"""
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    
    def __init__(self, title="检测操作", parent=None):
        super().__init__(title, parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QGridLayout(self)
        self.start_button = QPushButton("开始检测")
        self.pause_button = QPushButton("暂停检测")
        self.stop_button = QPushButton("停止检测")
        self.reset_button = QPushButton("重置")
        
        self.start_button.setStyleSheet("background-color: green; color: white;")
        self.pause_button.setStyleSheet("background-color: orange; color: white;")
        self.stop_button.setStyleSheet("background-color: red; color: white;")
        
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        layout.addWidget(self.start_button, 0, 0)
        layout.addWidget(self.pause_button, 0, 1)
        layout.addWidget(self.stop_button, 1, 0)
        layout.addWidget(self.reset_button, 1, 1)
        
        self.start_button.clicked.connect(self.start_detection.emit)
        self.pause_button.clicked.connect(self.pause_detection.emit)
        self.stop_button.clicked.connect(self.stop_detection.emit)
        self.reset_button.clicked.connect(self.reset_detection.emit)