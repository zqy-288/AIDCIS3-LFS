"""
实时图表组件模块
面板A使用matplotlib实现稳定的误差线显示，其他功能保持不变
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import numpy as np

# 设置matplotlib支持中文显示 - 安全版本
def setup_safe_chinese_font():
    """设置安全的中文字体支持"""
    try:
        # 使用简化的字体配置，避免复杂的字体检测
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        print("✅ 安全字体配置完成")
    except Exception as e:
        print(f"⚠️ 字体配置失败，使用默认: {e}")
        # 使用最基本的配置
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# 初始化安全字体配置
setup_safe_chinese_font()
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QSplitter, QGroupBox, QLineEdit, QMessageBox, QComboBox)
from PySide6.QtCore import Qt, Slot, QTimer
from collections import deque
from .endoscope_view import EndoscopeView


class RealtimeChart(QWidget):
    """
    实时图表组件 - 二级页面双面板设计
    面板A: 管孔直径数据实时折线图
    面板B: 内窥镜实时图像显示
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_id = None
        self.is_data_loaded = False  # 标记是否已加载数据
        self.setup_ui()
        self.setup_chart()
        self.init_data_buffers()
        self.setup_waiting_state()  # 设置等待状态
        
    def setup_ui(self):
        """设置用户界面布局 - 双面板设计"""
        layout = QVBoxLayout(self)

        # 状态信息面板 - 优化样式
        status_group = QGroupBox("检测状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
        """)
        status_layout = QHBoxLayout(status_group)

        # 当前孔位显示 - 改为文本显示，增大字体
        self.current_hole_label = QLabel("当前孔位：未选择")
        self.current_hole_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2196F3;
                padding: 8px 12px;
                background-color: #f0f8ff;
                border: 2px solid #2196F3;
                border-radius: 6px;
            }
        """)
        self.current_hole_label.setMinimumWidth(140)

        # 标准直径显示
        self.standard_diameter_label = QLabel("标准直径：17.6mm")
        self.standard_diameter_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #4CAF50;
                padding: 8px 12px;
                background-color: #f8fff8;
                border: 2px solid #4CAF50;
                border-radius: 6px;
            }
        """)
        self.standard_diameter_label.setMinimumWidth(140)

        # 其他状态标签 - 增大字体
        self.depth_label = QLabel("探头深度: -- mm")
        self.comm_status_label = QLabel("通信状态: --")
        self.max_diameter_label = QLabel("最大圆直径: --")
        self.min_diameter_label = QLabel("最小圆直径: --")

        # 设置状态标签样式 - 增大字体和内边距
        status_label_style = """
            QLabel {
                font-size: 13px;
                padding: 6px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
        """
        self.depth_label.setStyleSheet(status_label_style)
        self.comm_status_label.setStyleSheet(status_label_style)
        self.max_diameter_label.setStyleSheet(status_label_style)
        self.min_diameter_label.setStyleSheet(status_label_style)

        status_layout.addWidget(self.current_hole_label)
        status_layout.addWidget(self.standard_diameter_label)
        status_layout.addWidget(self.depth_label)
        status_layout.addWidget(self.comm_status_label)
        status_layout.addWidget(self.max_diameter_label)
        status_layout.addWidget(self.min_diameter_label)
        status_layout.addStretch()

        layout.addWidget(status_group)

        # 添加分隔线用于清晰区分状态区域和监测区域
        separator_line = QWidget()
        separator_line.setFixedHeight(3)
        separator_line.setStyleSheet("background-color: #ddd; margin: 5px 0px;")
        layout.addWidget(separator_line)

        # 双面板区域 - 改为垂直布局（A在上，B在下）
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)  # 设置分隔器手柄宽度
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #cccccc;
                border: 1px solid #999999;
                border-radius: 3px;
                margin: 2px;
            }
            QSplitter::handle:hover {
                background-color: #bbbbbb;
            }
        """)

        # 面板A: 孔径监测图区域 - 明确标题和边框
        panel_a = QGroupBox("孔径监测图")
        panel_a.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 3px solid #4CAF50;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8fff8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px 5px 15px;
                color: #2E7D32;
                background-color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
        """)
        panel_a_layout = QHBoxLayout(panel_a)  # 水平布局：图表在左，异常窗口在右

        # 面板A左侧：图表区域（matplotlib）
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        # 添加孔径监测图的说明信息
        chart_info_widget = QWidget()
        chart_info_layout = QHBoxLayout(chart_info_widget)
        chart_info_layout.setContentsMargins(10, 5, 10, 5)
        
        chart_info_label = QLabel("光谱共焦传感器孔径监测数据")
        chart_info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2E7D32;
                background-color: #e8f5e8;
                padding: 8px 15px;
                border: 1px solid #4CAF50;
                border-radius: 6px;
            }
        """)
        
        chart_info_layout.addWidget(chart_info_label)
        chart_info_layout.addStretch()
        
        chart_layout.addWidget(chart_info_widget)

        # 创建matplotlib图形，优化尺寸以最大化显示区域
        self.figure = Figure(figsize=(24, 12), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)

        # 连接鼠标事件用于缩放和重置
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)

        # 创建子图 - 增大字体
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('探头深度 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('孔径直径 (mm)', fontsize=14, fontweight='bold')
        self.ax.set_title('实时孔径监测数据', fontsize=16, fontweight='bold', pad=20,
                         bbox=dict(boxstyle="round,pad=0.3", facecolor="#e8f5e8", edgecolor="#4CAF50"))
        self.ax.grid(True, alpha=0.3)

        # 设置坐标轴刻度字体大小
        self.ax.tick_params(axis='both', which='major', labelsize=12)
        self.ax.tick_params(axis='both', which='minor', labelsize=10)

        # 设置初始范围
        self.ax.set_ylim(16.5, 20.5)
        self.ax.set_xlim(0, 950)

        # 初始化数据线
        self.data_line, = self.ax.plot([], [], 'b-', linewidth=3, label='直径数据')

        # 设置图形样式，确保所有标签都能完整显示
        self.figure.subplots_adjust(left=0.12, bottom=0.15, right=0.95, top=0.85)

        # 设置图例位置，确保不被遮挡 - 增大字体
        self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=12)

        # 在图表下方添加面板A专用控制按钮（移除标准直径输入）
        self.create_panel_a_controls(chart_layout)

        panel_a_layout.addWidget(chart_widget)

        # 面板A右侧：异常数据显示区域和按钮
        right_panel = QWidget()
        right_panel.setMinimumWidth(320)  # 设置最小宽度而不是固定宽度
        right_panel.setMaximumWidth(400)  # 设置最大宽度，允许适度调整
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        right_layout.setSpacing(8)  # 设置组件间距

        # 异常监控窗口 - 使用stretch factor占据大部分空间
        self.create_anomaly_panel(right_layout)

        # 添加固定间距，确保按钮不会紧贴异常面板
        right_layout.addSpacing(15)

        # 添加【查看下一个样品】按钮 - 增大字体和尺寸
        self.next_sample_button = QPushButton("查看下一个样品")
        self.next_sample_button.clicked.connect(self.view_next_sample)
        self.next_sample_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px 16px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: #4CAF50;
                color: white;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        from PySide6.QtWidgets import QSizePolicy
        self.next_sample_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        right_layout.addWidget(self.next_sample_button)

        # 添加底部间距，确保按钮不会贴底
        right_layout.addSpacing(10)

        panel_a_layout.addWidget(right_panel)
        splitter.addWidget(panel_a)

        # 面板B: 内窥镜展开图区域 - 明确标题和边框
        panel_b = QGroupBox("内窥镜展开图")
        panel_b.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 3px solid #2196F3;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f0f8ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 5px 15px 5px 15px;
                color: #1976D2;
                background-color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 8px;
            }
        """)
        panel_b_layout = QVBoxLayout(panel_b)
        
        # 添加内窥镜展开图的说明信息
        endoscope_info_widget = QWidget()
        endoscope_info_layout = QHBoxLayout(endoscope_info_widget)
        endoscope_info_layout.setContentsMargins(10, 5, 10, 5)
        
        info_label = QLabel("内窥镜实时展开图像显示区域")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #1976D2;
                background-color: #e3f2fd;
                padding: 8px 15px;
                border: 1px solid #2196F3;
                border-radius: 6px;
            }
        """)
        
        endoscope_info_layout.addWidget(info_label)
        endoscope_info_layout.addStretch()
        
        panel_b_layout.addWidget(endoscope_info_widget)

        self.endoscope_view = EndoscopeView()
        panel_b_layout.addWidget(self.endoscope_view)

        splitter.addWidget(panel_b)

        # 设置分割器比例，使用相对比例而不是固定像素
        # 面板A占65%，面板B占35%
        layout.addWidget(splitter)

        # 保存分割器引用，用于后续调整
        self.main_splitter = splitter

        # 延迟设置分割器比例，确保窗口已完全初始化
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.safe_adjust_splitter_sizes(splitter))

        # 初始化孔位数据映射
        self.init_hole_data_mapping()

        # 控制按钮 - 增大字体和尺寸
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("开始测量")
        self.stop_button = QPushButton("停止测量")
        self.clear_button = QPushButton("清除数据")

        # 设置按钮样式 - 增大字体和尺寸
        button_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """

        self.start_button.setStyleSheet(button_style)
        self.stop_button.setStyleSheet(button_style)
        self.clear_button.setStyleSheet(button_style)

        # 初始状态下禁用按钮，等待从主检测界面跳转
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # 设置按钮提示
        self.start_button.setToolTip("请先从主检测界面选择孔位")
        self.stop_button.setToolTip("请先从主检测界面选择孔位")
        self.clear_button.setToolTip("请先从主检测界面选择孔位")

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 连接按钮信号
        self.start_button.clicked.connect(self.start_csv_data_import)
        self.stop_button.clicked.connect(self.stop_csv_data_import)
        self.clear_button.clicked.connect(self.clear_data)

    def create_panel_a_controls(self, parent_layout):
        """创建面板A专用控制按钮"""
        # 不再创建面板A的启动、停止按钮和状态标签
        # 这些控制功能已被移除
        pass

    def init_hole_data_mapping(self):
        """初始化孔位数据映射"""
        import os

        # 获取当前工作目录
        base_dir = os.getcwd()

        self.hole_to_csv_map = {
            "H00001": "Data/H00001/CCIDM",
            "H00002": "Data/H00002/CCIDM"
        }

        self.hole_to_image_map = {
            "H00001": os.path.join(base_dir, "Data/H00001/BISDM/result"),
            "H00002": os.path.join(base_dir, "Data/H00002/BISDM/result")
        }

        # 打印路径信息用于调试
        print("🔧 孔位数据映射初始化:")
        for hole_id, csv_path in self.hole_to_csv_map.items():
            image_path = self.hole_to_image_map[hole_id]
            print(f"  {hole_id}:")
            print(f"    📄 CSV: {csv_path}")
            print(f"    🖼️ 图像: {image_path}")
            print(f"    📂 图像目录存在: {os.path.exists(image_path)}")

    def set_current_hole_display(self, hole_id):
        """设置当前孔位显示"""
        if hole_id:
            self.current_hole_label.setText(f"当前孔位：{hole_id}")
            self.current_hole_id = hole_id
            print(f"🔄 设置当前孔位显示: {hole_id}")
            # 如果有对应的数据文件，自动加载
            if hole_id in ["H00001", "H00002"]:
                self.load_data_for_hole(hole_id)
        else:
            self.current_hole_label.setText("当前孔位：未选择")
            self.current_hole_id = None

    def setup_waiting_state(self):
        """设置等待状态 - 等待从主检测界面跳转"""
        # 显示等待提示
        self.current_hole_label.setText("当前孔位：未选择")
        self.depth_label.setText("探头深度: -- mm")
        self.comm_status_label.setText("通信状态: 等待选择孔位")
        self.max_diameter_label.setText("最大直径: -- mm")
        self.min_diameter_label.setText("最小直径: -- mm")

        # 在图表中显示等待提示
        self.show_waiting_message()

        print("⏳ 实时监控界面等待状态 - 请从主检测界面选择孔位后跳转")

    def show_waiting_message(self):
        """在图表区域显示等待状态（无提示文字）"""
        try:
            # 清除现有数据
            self.ax.clear()

            # 设置图表标题
            self.ax.set_title("管孔直径实时监测", fontsize=16, fontweight='bold', pad=20)

            # 设置基本的坐标轴
            self.ax.set_xlabel("深度 (mm)", fontsize=12)
            self.ax.set_ylabel("直径 (mm)", fontsize=12)
            self.ax.grid(True, alpha=0.3)

            # 设置默认的坐标轴范围
            self.ax.set_xlim(0, 100)
            self.ax.set_ylim(16, 20)

            # 刷新画布
            self.canvas.draw()

        except Exception as e:
            print(f"⚠️ 显示等待状态失败: {e}")

    def enable_controls_after_data_load(self):
        """数据加载后启用控制按钮"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)

        # 更新按钮提示
        self.start_button.setToolTip("开始播放测量数据")
        self.stop_button.setToolTip("停止播放测量数据")
        self.clear_button.setToolTip("清除当前数据")

        print("✅ 控制按钮已启用")

    def setup_chart_for_data(self):
        """为数据显示设置图表"""
        try:
            # 清除现有内容
            self.ax.clear()

            # 设置图表标题
            self.ax.set_title("管孔直径实时监测", fontsize=16, fontweight='bold', pad=20)

            # 设置坐标轴标签
            self.ax.set_xlabel("深度 (mm)", fontsize=12)
            self.ax.set_ylabel("直径 (mm)", fontsize=12)

            # 设置网格
            self.ax.grid(True, alpha=0.3)

            # 初始化数据线
            self.data_line, = self.ax.plot([], [], 'b-', linewidth=2, label='测量数据')

            # 重新绘制误差线（如果标准直径已设置）
            if hasattr(self, 'standard_diameter') and self.standard_diameter is not None:
                self.draw_error_lines_and_adjust_y_axis()
                print("✅ 误差线已重新绘制")
            else:
                # 设置图例（无误差线时）
                self.ax.legend(loc='upper right')

            # 刷新画布
            self.canvas.draw()

            print("✅ 图表已准备好显示数据")

        except Exception as e:
            print(f"⚠️ 设置图表失败: {e}")





    def start_endoscope_image_switching(self):
        """启动内窥镜图像切换功能"""
        print("🖼️ 启动面板B图像切换功能")

        # 检查是否有图像数据
        if not hasattr(self, 'current_images') or not self.current_images:
            print("⚠️ 没有可用的内窥镜图像数据")
            return

        # 标记图像切换功能已启用
        self.endoscope_switching_enabled = True

        # 如果CSV数据正在播放，图像会自动根据进度切换
        # 如果没有播放，显示第一张图像
        if not hasattr(self, 'is_csv_playing') or not self.is_csv_playing:
            if self.current_images:
                self.display_endoscope_image(0)
                print("📸 显示第一张内窥镜图像")

        print(f"✅ 图像切换功能已启用，共 {len(self.current_images)} 张图像")

    def stop_endoscope_image_switching(self):
        """停止内窥镜图像切换功能"""
        print("⏹️ 停止面板B图像切换功能")

        # 标记图像切换功能已禁用
        self.endoscope_switching_enabled = False

        print("✅ 图像切换功能已停止")

    def create_anomaly_panel(self, parent_layout):
        """创建异常数据显示面板 - 增大字体"""
        anomaly_widget = QGroupBox("异常直径监控")
        anomaly_widget.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #FF5722;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #fff5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #D32F2F;
                background-color: white;
            }
        """)
        anomaly_widget.setMinimumWidth(310)  # 设置最小宽度
        anomaly_widget.setMaximumWidth(390)  # 设置最大宽度，允许适度调整
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(8, 8, 8, 8)
        anomaly_layout.setSpacing(5)  # 设置组件间距

        # 标题 - 增大字体
        title_label = QLabel("超出公差的测量点")
        title_label.setStyleSheet("font-weight: bold; color: red; margin-bottom: 3px; font-size: 13px;")
        title_label.setFixedHeight(25)  # 增加标题高度
        anomaly_layout.addWidget(title_label)

        # 滚动区域用于显示异常数据
        from PySide6.QtWidgets import QScrollArea
        self.anomaly_scroll = QScrollArea()
        self.anomaly_scroll.setWidgetResizable(True)
        self.anomaly_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #fafafa;
            }
        """)

        self.anomaly_content = QWidget()
        self.anomaly_content_layout = QVBoxLayout(self.anomaly_content)
        self.anomaly_content_layout.setContentsMargins(5, 5, 5, 5)
        self.anomaly_scroll.setWidget(self.anomaly_content)

        # 滚动区域占据可用空间，但为统计信息预留足够空间
        anomaly_layout.addWidget(self.anomaly_scroll, 1)

        # 统计信息 - 固定在底部，确保始终可见
        stats_widget = QWidget()
        stats_widget.setFixedHeight(50)  # 减少统计区域高度
        stats_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                border-radius: 3px;
            }
        """)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(5, 3, 5, 3)
        stats_layout.setSpacing(2)

        stats_label = QLabel("异常统计")
        stats_label.setStyleSheet("font-weight: bold; color: #333; font-size: 12px;")
        stats_label.setFixedHeight(18)
        stats_layout.addWidget(stats_label)

        # 统计信息水平布局，节省空间
        stats_info_layout = QHBoxLayout()
        stats_info_layout.setContentsMargins(0, 0, 0, 0)
        stats_info_layout.setSpacing(10)

        self.anomaly_count_label = QLabel("异常点数: 0")
        self.anomaly_count_label.setStyleSheet("font-size: 11px; color: #666; font-weight: bold;")
        self.anomaly_rate_label = QLabel("异常率: 0.0%")
        self.anomaly_rate_label.setStyleSheet("font-size: 11px; color: #666; font-weight: bold;")

        stats_info_layout.addWidget(self.anomaly_count_label)
        stats_info_layout.addWidget(self.anomaly_rate_label)
        stats_info_layout.addStretch()

        stats_layout.addLayout(stats_info_layout)

        # 添加统计区域，不使用stretch factor，保持固定位置
        anomaly_layout.addWidget(stats_widget, 0)

        # 让异常面板占据可用空间，但为按钮预留空间
        parent_layout.addWidget(anomaly_widget, 1)  # 使用stretch factor





    def set_standard_diameter(self, diameter):
        """设置标准直径并绘制公差线"""
        self.standard_diameter = diameter

        # 误差范围：+0.05/-0.07mm
        self.upper_tolerance = 0.05
        self.lower_tolerance = 0.07

        # 更新目标直径（用于异常检测）
        self.target_diameter = diameter
        self.tolerance = max(self.upper_tolerance, self.lower_tolerance)  # 使用最大误差进行异常检测

        # 绘制误差线并调整Y轴范围
        self.draw_error_lines_and_adjust_y_axis()

    def draw_error_lines_and_adjust_y_axis(self):
        """绘制误差线并调整Y轴范围（matplotlib版本）"""
        if not hasattr(self, 'standard_diameter') or self.standard_diameter is None:
            return

        # 移除现有的误差线
        self.remove_error_lines_and_reset_y_axis()

        # 计算误差线位置
        max_error_line_y = self.standard_diameter + self.upper_tolerance  # +0.05mm
        min_error_line_y = self.standard_diameter - self.lower_tolerance  # -0.07mm

        # 计算Y轴显示范围：标准直径 ± 0.15mm
        y_margin = 0.15
        y_min = self.standard_diameter - y_margin
        y_max = self.standard_diameter + y_margin

        # 设置Y轴范围
        self.ax.set_ylim(y_min, y_max)

        # 使用matplotlib绘制误差线
        try:
            # 绘制上误差线（红色虚线）
            self.max_error_line = self.ax.axhline(
                y=max_error_line_y,
                color='red',
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                label=f'上限 {max_error_line_y:.2f}mm'
            )

            # 绘制下误差线（红色虚线）
            self.min_error_line = self.ax.axhline(
                y=min_error_line_y,
                color='red',
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                label=f'下限 {min_error_line_y:.2f}mm'
            )

            # 更新图例，设置位置确保不被遮挡
            self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=10)

            # 更新图表并强制刷新布局
            self.figure.canvas.draw_idle()

            print(f"matplotlib误差线绘制成功:")
            print(f"  上误差线: y = {max_error_line_y:.3f}mm")
            print(f"  下误差线: y = {min_error_line_y:.3f}mm")
            print(f"  Y轴范围: {y_min:.2f} ~ {y_max:.2f}mm")

        except Exception as e:
            print(f"matplotlib误差线绘制失败: {e}")

    def remove_error_lines_and_reset_y_axis(self):
        """移除误差线并重置Y轴范围（matplotlib版本）"""
        # 移除最大直径误差线
        if hasattr(self, 'max_error_line') and self.max_error_line:
            try:
                self.max_error_line.remove()
            except:
                pass
            self.max_error_line = None

        # 移除最小直径误差线
        if hasattr(self, 'min_error_line') and self.min_error_line:
            try:
                self.min_error_line.remove()
            except:
                pass
            self.min_error_line = None

        # 重置图例（只有在data_line存在时）
        if hasattr(self, 'data_line') and self.data_line:
            try:
                self.ax.legend([self.data_line], ['测量数据'], loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=10)
            except:
                # 如果data_line不可用，创建空图例
                self.ax.legend(loc='upper right', bbox_to_anchor=(0.95, 0.95), fontsize=10)

        # 恢复默认Y轴范围
        self.ax.set_ylim(16.5, 20.5)

        # 更新图表并强制刷新布局
        self.figure.canvas.draw_idle()

        print("移除误差线，恢复默认Y轴范围: 16.5 - 20.5mm")

    # 删除移除公差线方法

    def safe_adjust_splitter_sizes(self, splitter):
        """安全地调整分割器大小比例，检查对象有效性"""
        try:
            # 检查对象是否仍然有效
            if hasattr(self, 'height') and callable(self.height):
                self.adjust_splitter_sizes(splitter)
        except RuntimeError as e:
            # 对象已被删除，忽略错误
            print(f"对象已删除，跳过分割器调整: {e}")
        except Exception as e:
            # 其他错误也忽略
            print(f"分割器调整失败: {e}")

    def adjust_splitter_sizes(self, splitter):
        """调整分割器大小比例"""
        total_height = self.height()
        if total_height > 0:
            # 面板A占65%，面板B占35%
            panel_a_height = int(total_height * 0.65)
            panel_b_height = int(total_height * 0.35)
            splitter.setSizes([panel_a_height, panel_b_height])

            # 同时调整异常面板的高度
            self.adjust_anomaly_panel_height(panel_a_height)

    def adjust_anomaly_panel_height(self, panel_a_height):
        """动态调整异常面板高度，确保按钮不遮挡统计信息"""
        if hasattr(self, 'anomaly_scroll') and hasattr(self, 'next_sample_button'):
            # 计算可用高度：面板A高度 - 状态面板高度 - 按钮高度 - 间距
            available_height = panel_a_height - 80  # 减去状态面板和其他组件的高度
            button_height = 35  # 按钮高度
            spacing = 30  # 间距
            stats_height = 50  # 统计信息高度
            title_height = 25  # 标题高度

            # 计算滚动区域的最大高度
            max_scroll_height = available_height - button_height - spacing - stats_height - title_height

            # 设置最小高度，确保基本可用性
            min_scroll_height = 150
            scroll_height = max(min_scroll_height, max_scroll_height)

            # 应用高度限制
            if scroll_height > 0:
                self.anomaly_scroll.setMaximumHeight(int(scroll_height))
                self.anomaly_scroll.setMinimumHeight(min(min_scroll_height, int(scroll_height)))

    def resizeEvent(self, event):
        """窗口大小变化事件处理"""
        super().resizeEvent(event)
        # 延迟调整布局，确保窗口大小变化完成
        if hasattr(self, 'main_splitter'):
            QTimer.singleShot(50, lambda: self.adjust_splitter_sizes(self.main_splitter))

    def setup_chart(self):
        """设置图表属性和样式（matplotlib版本）"""
        # 固定标准直径为17.6mm
        self.standard_diameter = 17.6
        self.target_diameter = 17.6  # 目标直径，用于Y轴范围设置
        self.tolerance = 0.5  # 默认公差，用于异常检测
        self.upper_tolerance = 0.05  # 上公差 +0.05mm
        self.lower_tolerance = 0.07  # 下公差 -0.07mm

        # 初始化误差线
        self.max_error_line = None  # 最大直径误差线
        self.min_error_line = None  # 最小直径误差线

        # 设置更新定时器 - 使用更安全的频率
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(200)  # 每1秒更新一次，更加安全

        # 初始化缩放参数
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

        # 自动设置标准直径并绘制误差线
        self.set_standard_diameter(17.6)
        print(f"✅ 自动设置标准直径为: {self.standard_diameter}mm")

    def update_plot(self):
        """更新matplotlib图表显示 - 超级安全版本"""
        try:
            # 检查所有必要的属性是否存在
            if not hasattr(self, 'depth_data') or not hasattr(self, 'diameter_data'):
                return
            if not hasattr(self, 'data_line') or not hasattr(self, 'ax') or not hasattr(self, 'canvas'):
                return

            # 检查数据是否有效
            if not self.depth_data or not self.diameter_data:
                return
            if len(self.depth_data) == 0 or len(self.diameter_data) == 0:
                return
            if len(self.depth_data) != len(self.diameter_data):
                return

            # 安全地更新数据线
            try:
                depth_list = list(self.depth_data)
                diameter_list = list(self.diameter_data)
                self.data_line.set_data(depth_list, diameter_list)
            except Exception:
                return

            # 安全地调整坐标轴范围
            try:
                if len(depth_list) > 1:
                    x_min = min(depth_list)
                    x_max = max(depth_list)
                    x_range = x_max - x_min

                    if x_range > 0:
                        margin = max(x_range * 0.1, 50)
                        # 确保X轴最小值不小于0（深度不能为负）
                        x_min_display = max(0, x_min - margin)
                        self.ax.set_xlim(x_min_display, x_max + margin)
                    else:
                        # 确保X轴最小值不小于0
                        x_min_display = max(0, x_min - 50)
                        self.ax.set_xlim(x_min_display, x_min + 50)
            except Exception:
                pass

            # 安全地重绘画布
            try:
                self.canvas.draw_idle()
            except Exception:
                pass

        except Exception as e:
            # 完全静默处理，确保不影响主程序
            pass

    def cleanup(self):
        """清理资源，停止定时器"""
        try:
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            if hasattr(self, 'csv_timer') and self.csv_timer:
                self.csv_timer.stop()
        except Exception:
            pass

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.cleanup()
        super().closeEvent(event)

    def on_scroll(self, event):
        """处理鼠标滚轮缩放事件"""
        if event.inaxes != self.ax:
            return

        # 获取当前坐标轴范围
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        # 获取鼠标位置
        x_mouse = event.xdata
        y_mouse = event.ydata

        if x_mouse is None or y_mouse is None:
            return

        # 设置缩放因子
        if event.button == 'up':
            # 向上滚动，放大
            scale_factor = 0.9
        elif event.button == 'down':
            # 向下滚动，缩小
            scale_factor = 1.1
        else:
            return

        # 计算新的坐标范围，以鼠标位置为中心缩放
        x_range = x_max - x_min
        y_range = y_max - y_min

        new_x_range = x_range * scale_factor
        new_y_range = y_range * scale_factor

        # 计算新的坐标范围
        new_x_min = x_mouse - (x_mouse - x_min) * scale_factor
        new_x_max = x_mouse + (x_max - x_mouse) * scale_factor
        new_y_min = y_mouse - (y_mouse - y_min) * scale_factor
        new_y_max = y_mouse + (y_max - y_mouse) * scale_factor

        # 限制缩放范围，避免过度缩放
        if new_x_range < 10:  # X轴最小范围10mm
            return
        if new_x_range > 2000:  # X轴最大范围2000mm
            return
        if new_y_range < 0.1:  # Y轴最小范围0.1mm
            return
        if new_y_range > 10:  # Y轴最大范围10mm
            return

        # 应用新的坐标范围
        self.ax.set_xlim(new_x_min, new_x_max)
        self.ax.set_ylim(new_y_min, new_y_max)

        # 重绘图表
        self.canvas.draw_idle()

        print(f"缩放: X轴[{new_x_min:.1f}, {new_x_max:.1f}], Y轴[{new_y_min:.3f}, {new_y_max:.3f}]")

    def on_mouse_press(self, event):
        """处理鼠标点击事件"""
        if event.inaxes != self.ax:
            return

        # 双击重置缩放
        if event.dblclick:
            self.reset_zoom()

    def reset_zoom(self):
        """重置缩放到默认视图"""
        if hasattr(self, 'standard_diameter') and self.standard_diameter:
            # 如果设置了标准直径，使用聚焦视图
            y_margin = 0.15
            y_min = self.standard_diameter - y_margin
            y_max = self.standard_diameter + y_margin
            self.ax.set_ylim(y_min, y_max)
        else:
            # 否则使用默认范围
            self.ax.set_ylim(16.5, 20.5)

        # X轴范围根据数据自动调整
        if len(self.depth_data) > 0:
            x_min = min(self.depth_data)
            x_max = max(self.depth_data)
            x_range = x_max - x_min

            if x_range > 0:
                margin = max(x_range * 0.1, 50)
                # 确保X轴最小值不小于0（深度不能为负）
                x_min_display = max(0, x_min - margin)
                self.ax.set_xlim(x_min_display, x_max + margin)
            else:
                self.ax.set_xlim(0, 950)
        else:
            self.ax.set_xlim(0, 950)

        # 重绘图表
        self.canvas.draw_idle()
        print("缩放已重置到默认视图")

    def reset_to_standard_view(self):
        """还原到标准直径设置后的坐标轴显示范围"""
        if hasattr(self, 'standard_diameter') and self.standard_diameter:
            # 还原到标准直径的聚焦视图
            y_margin = 0.15
            y_min = self.standard_diameter - y_margin
            y_max = self.standard_diameter + y_margin
            self.ax.set_ylim(y_min, y_max)

            # X轴范围根据当前数据自动调整
            if len(self.depth_data) > 0:
                x_min = min(self.depth_data)
                x_max = max(self.depth_data)
                x_range = x_max - x_min

                if x_range > 0:
                    margin = max(x_range * 0.1, 50)
                    # 确保X轴最小值不小于0（深度不能为负）
                    x_min_display = max(0, x_min - margin)
                    self.ax.set_xlim(x_min_display, x_max + margin)
                else:
                    self.ax.set_xlim(0, 950)
            else:
                self.ax.set_xlim(0, 950)

            # 重绘图表
            self.canvas.draw_idle()
            print(f"视图已还原到标准直径 {self.standard_diameter}mm 的显示范围")
        else:
            # 如果没有设置标准直径，还原到默认视图
            self.ax.set_ylim(16.5, 20.5)
            self.ax.set_xlim(0, 950)
            self.canvas.draw_idle()
            print("视图已还原到默认显示范围")
        
    def init_data_buffers(self):
        """初始化数据缓冲区"""
        # 注意：孔位数据映射现在在init_hole_data_mapping()中初始化
        # 这里只初始化基本的数据缓冲区

        # 内窥镜图片相关变量
        self.current_images = []  # 当前孔位的图片列表
        self.current_image_index = 0  # 当前显示的图片索引
        self.image_switch_points = []  # 图片切换的数据点位置
        self.endoscope_switching_enabled = False  # 图像切换功能是否启用
        self.current_hole_id = None  # 当前选中的孔位ID
        self.endoscope_switching_enabled = False  # 图像切换功能是否启用
        self.max_points = 2000  # 最大显示点数
        self.depth_data = deque(maxlen=self.max_points)
        self.diameter_data = deque(maxlen=self.max_points)

        # 样品管理
        self.current_sample_index = 0
        self.sample_data_history = {}  # 存储多个样品的数据

        # 异常数据管理
        self.anomaly_data = []  # 存储异常数据点

        # 最大最小直径跟踪
        self.max_diameter = None  # 当前样品的最大直径
        self.min_diameter = None  # 当前样品的最小直径

        # CSV数据导入相关
        self.csv_data = []  # 存储CSV数据
        self.csv_data_index = 0  # 当前播放位置
        self.csv_timer = None  # CSV数据播放定时器
        self.is_csv_playing = False  # CSV数据播放状态

        # 多文件管理（向后兼容，但主要使用新的孔位映射）
        self.csv_file_list = []
        self.current_file_index = 0  # 当前文件索引
        self.csv_base_path = "Data/H00001/CCIDM"  # 使用相对路径
        
    @Slot(float, float)
    def update_data(self, depth, diameter):
        """
        更新图表数据的槽函数
        由工作线程的信号触发
        """
        # 添加新数据点
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)

        # 检测异常数据
        self.check_anomaly(depth, diameter)

        # 保存当前样品数据
        self.save_current_sample_data(depth, diameter)

        # 更新最大最小直径
        self.update_diameter_extremes(diameter)

        # 更新图表（matplotlib版本在update_plot中处理）
        # matplotlib的数据更新由定时器驱动的update_plot方法处理

    def update_diameter_extremes(self, diameter):
        """更新最大最小直径"""
        # 更新最大直径
        if self.max_diameter is None or diameter > self.max_diameter:
            self.max_diameter = diameter

        # 更新最小直径
        if self.min_diameter is None or diameter < self.min_diameter:
            self.min_diameter = diameter

        # 更新状态栏显示
        self.update_diameter_display()

    def update_diameter_display(self):
        """更新直径显示"""
        if self.max_diameter is not None:
            self.max_diameter_label.setText(f"最大圆直径: {self.max_diameter:.3f} mm")
        else:
            self.max_diameter_label.setText("最大圆直径: --")

        if self.min_diameter is not None:
            self.min_diameter_label.setText(f"最小圆直径: {self.min_diameter:.3f} mm")
        else:
            self.min_diameter_label.setText("最小圆直径: --")

    @Slot(str, float, str)
    def update_status(self, hole_id, probe_depth, comm_status):
        """
        更新状态信息的槽函数
        """
        # 更新当前孔位显示
        if hole_id and hole_id != "未知样品" and hole_id != "当前样品":
            self.current_hole_label.setText(f"当前孔位：{hole_id}")
            self.current_hole_id = hole_id

        self.depth_label.setText(f"探头深度: {probe_depth:.1f} mm")
        self.comm_status_label.setText(f"通信状态: {comm_status}")

        # 根据通信状态改变标签颜色
        if comm_status == "连接正常":
            self.comm_status_label.setStyleSheet("color: green;")
        else:
            self.comm_status_label.setStyleSheet("color: red;")
    
    def clear_data(self):
        """清除所有数据"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.data_line.set_data([], [])
        self.canvas.draw()

        # 清除异常数据
        self.anomaly_data.clear()
        self.update_anomaly_display()

        # 清除内窥镜图像
        self.endoscope_view.clear_image()

        # 重置状态显示
        self.depth_label.setText("探头深度: -- mm")
        self.comm_status_label.setText("通信状态: --")
        self.comm_status_label.setStyleSheet("")

        # 注意：不重置孔位显示，保持当前选中的孔位
        # 只有在完全重置时才清除孔位信息

        # 重置最大最小直径
        self.max_diameter = None
        self.min_diameter = None
        self.update_diameter_display()

    def reset_to_waiting_state(self):
        """完全重置到等待状态"""
        # 清除数据
        self.clear_data()

        # 重置孔位显示
        self.current_hole_label.setText("当前孔位：未选择")
        self.current_hole_id = None
        self.is_data_loaded = False

        # 禁用按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # 显示等待状态
        self.setup_waiting_state()

    def set_current_hole(self, hole_id):
        """设置当前检测的孔ID"""
        self.current_hole_id = hole_id
        self.current_hole_label.setText(f"当前孔位：{hole_id}")
        self.endoscope_view.set_hole_id(hole_id)
        print(f"✅ 设置当前检测孔位: {hole_id}")

    def start_measurement_for_hole(self, hole_id):
        """为指定孔开始测量"""
        self.set_current_hole(hole_id)
        self.clear_data()

        # 开始内窥镜图像采集
        self.endoscope_view.start_acquisition()

    def stop_measurement(self):
        """停止测量"""
        # 停止内窥镜图像采集
        self.endoscope_view.stop_acquisition()

    def check_anomaly(self, depth, diameter):
        """检测异常数据点"""
        # 只有在设置了标准直径时才进行异常检测
        if hasattr(self, 'standard_diameter') and self.standard_diameter is not None:
            # 检查是否超出上下公差范围
            upper_limit = self.standard_diameter + self.upper_tolerance
            lower_limit = self.standard_diameter - self.lower_tolerance

            if diameter > upper_limit or diameter < lower_limit:
                # 计算偏差（相对于最近的公差边界）
                if diameter > upper_limit:
                    deviation = diameter - upper_limit
                else:
                    deviation = lower_limit - diameter

                # 添加到异常数据列表
                anomaly_info = {
                    'depth': depth,
                    'diameter': diameter,
                    'deviation': deviation,
                    'standard_diameter': self.standard_diameter,
                    'upper_limit': upper_limit,
                    'lower_limit': lower_limit,
                    'sample_id': self.current_hole_id or f"Sample_{self.current_sample_index}"
                }
                self.anomaly_data.append(anomaly_info)

                # 更新异常显示
                self.update_anomaly_display()

    def update_anomaly_display(self):
        """更新异常数据显示"""
        # 清除现有显示
        for i in reversed(range(self.anomaly_content_layout.count())):
            child = self.anomaly_content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 显示最近的异常数据（最多显示10个）
        recent_anomalies = self.anomaly_data[-10:] if len(self.anomaly_data) > 10 else self.anomaly_data

        for anomaly in recent_anomalies:
            anomaly_widget = QWidget()
            anomaly_layout = QHBoxLayout(anomaly_widget)
            anomaly_layout.setContentsMargins(5, 2, 5, 2)

            # 深度和直径信息
            info_label = QLabel(f"深度: {anomaly['depth']:.1f}mm\n直径: {anomaly['diameter']:.3f}mm")
            info_label.setStyleSheet("font-size: 10px; color: red;")
            anomaly_layout.addWidget(info_label)

            # 偏差信息
            deviation_label = QLabel(f"偏差: {anomaly['deviation']:.3f}mm")
            deviation_label.setStyleSheet("font-size: 10px; font-weight: bold; color: red;")
            anomaly_layout.addWidget(deviation_label)

            self.anomaly_content_layout.addWidget(anomaly_widget)

        # 更新统计信息
        total_points = len(self.depth_data)
        anomaly_count = len(self.anomaly_data)
        anomaly_rate = (anomaly_count / total_points * 100) if total_points > 0 else 0

        self.anomaly_count_label.setText(f"异常点数: {anomaly_count}")
        self.anomaly_rate_label.setText(f"异常率: {anomaly_rate:.1f}%")

    def save_current_sample_data(self, depth, diameter):
        """保存当前样品数据"""
        sample_key = self.current_hole_id or f"Sample_{self.current_sample_index}"
        if sample_key not in self.sample_data_history:
            self.sample_data_history[sample_key] = {
                'depths': [],
                'diameters': [],
                'anomalies': []
            }

        self.sample_data_history[sample_key]['depths'].append(depth)
        self.sample_data_history[sample_key]['diameters'].append(diameter)

        # 如果是异常点，也保存到样品的异常列表中
        deviation = abs(diameter - self.target_diameter)
        if deviation > self.tolerance:
            self.sample_data_history[sample_key]['anomalies'].append({
                'depth': depth,
                'diameter': diameter,
                'deviation': deviation
            })

    def view_next_sample(self):
        """查看下一个样品 - 基于孔位ID切换（H00001 → H00002 → H00001...）"""
        # 停止当前播放
        if self.is_csv_playing:
            self.stop_csv_data_import()

        # 定义孔位切换顺序
        hole_sequence = ["H00001", "H00002"]

        # 获取当前孔位ID
        current_hole = self.current_hole_id

        # 确定下一个孔位
        next_hole = None
        if current_hole in hole_sequence:
            current_index = hole_sequence.index(current_hole)
            next_index = (current_index + 1) % len(hole_sequence)  # 循环切换
            next_hole = hole_sequence[next_index]
        else:
            # 如果当前孔位不在序列中，默认切换到第一个
            next_hole = hole_sequence[0]

        print(f"🔄 切换样品: {current_hole} → {next_hole}")

        # 检查下一个孔位是否有数据
        if next_hole not in self.hole_to_csv_map:
            print(f"❌ 孔位 {next_hole} 没有关联的数据文件")
            QMessageBox.information(self, "信息", f"孔位 {next_hole} 没有可用的数据文件")
            return

        # 加载下一个孔位的数据
        try:
            self.load_data_for_hole(next_hole)

            # 更新主窗口状态栏显示
            self.update_main_window_status(next_hole)

            print(f"✅ 成功切换到孔位: {next_hole}")
        except Exception as e:
            print(f"❌ 切换到孔位 {next_hole} 失败: {e}")
            QMessageBox.warning(self, "错误", f"切换到孔位 {next_hole} 失败:\n{str(e)}")

    def update_main_window_status(self, hole_id):
        """更新主窗口状态栏显示"""
        try:
            # 查找主窗口
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'status_label'):
                    main_window = parent
                    break
                parent = parent.parent()

            # 更新状态栏
            if main_window and hasattr(main_window, 'status_label'):
                main_window.status_label.setText(f"实时监控 - {hole_id}")
                print(f"✅ 更新主窗口状态栏: 实时监控 - {hole_id}")
            else:
                print("⚠️ 未找到主窗口状态栏，无法更新")

        except Exception as e:
            print(f"⚠️ 更新主窗口状态栏失败: {e}")

    def load_sample_data(self, sample_key):
        """加载指定样品的数据"""
        if sample_key not in self.sample_data_history:
            return

        sample_data = self.sample_data_history[sample_key]

        # 清除当前显示
        self.depth_data.clear()
        self.diameter_data.clear()
        self.anomaly_data.clear()

        # 加载历史数据
        for depth, diameter in zip(sample_data['depths'], sample_data['diameters']):
            self.depth_data.append(depth)
            self.diameter_data.append(diameter)

        # 加载异常数据
        self.anomaly_data = sample_data['anomalies'].copy()

        # 更新显示
        if len(self.depth_data) > 0:
            self.data_curve.setData(
                x=list(self.depth_data),
                y=list(self.diameter_data)
            )

        self.update_anomaly_display()
        self.current_hole_id = sample_key

    def set_tolerance_limits(self, target, tolerance):
        """设置公差限制 - 已废弃，删除目标线引用"""
        self.target_diameter = target
        self.tolerance = tolerance

        # 删除所有公差线和目标线相关代码
        # 调整Y轴范围
        margin = tolerance * 3
        self.plot_widget.setYRange(target - margin, target + margin)
        
    def get_current_statistics(self):
        """获取当前数据的统计信息"""
        if len(self.diameter_data) == 0:
            return None
            
        diameters = list(self.diameter_data)
        return {
            'count': len(diameters),
            'mean': np.mean(diameters),
            'std': np.std(diameters),
            'min': np.min(diameters),
            'max': np.max(diameters),
            'in_tolerance': sum(
                1 for d in diameters 
                if abs(d - self.target_diameter) <= self.tolerance
            ),
            'out_of_tolerance': sum(
                1 for d in diameters 
                if abs(d - self.target_diameter) > self.tolerance
            )
        }

    def load_data_for_hole(self, hole_id):
        """为指定的孔加载并显示其对应的CSV数据和内窥镜图片"""
        import os

        if hole_id not in self.hole_to_csv_map:
            QMessageBox.information(self, "信息", f"孔 {hole_id} 没有关联的CSV数据文件。")
            return

        csv_dir = self.hole_to_csv_map[hole_id]
        print(f"🔄 为孔 {hole_id} 加载数据目录: {csv_dir}")

        # 查找目录中的CSV文件
        csv_file = None
        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    csv_file = os.path.join(csv_dir, file)
                    break

        if not csv_file:
            QMessageBox.warning(self, "错误", f"在目录 {csv_dir} 中未找到CSV文件")
            return

        print(f"📄 找到CSV文件: {csv_file}")

        # 停止当前可能正在播放的任何数据
        if hasattr(self, 'is_csv_playing') and self.is_csv_playing:
            self.stop_csv_data_import()

        # 清除旧数据
        self.clear_data()

        # 加载新的CSV文件
        if self.load_csv_data(file_path=csv_file):
            self.set_current_hole(hole_id)

            # 设置当前孔位ID，用于状态显示
            self.current_hole_id = hole_id
            self.is_data_loaded = True  # 标记数据已加载

            # 加载对应的内窥镜图片
            self.load_endoscope_images_for_hole(hole_id)

            # 设置图表用于数据显示
            self.setup_chart_for_data()

            # 启用控制按钮
            self.enable_controls_after_data_load()

            # 自动开始播放
            self.start_csv_data_import(auto_play=True)

            print(f"✅ 成功从主检测界面加载孔位 {hole_id} 的数据")
        else:
            QMessageBox.warning(self, "错误", f"无法加载文件: \n{csv_file}")

    def start_csv_data_import(self, auto_play=False):
        """开始CSV数据导入"""
        # 如果是自动播放模式，数据应该已经加载了
        if auto_play:
            if not self.csv_data:
                print("❌ 自动播放模式下没有可用的CSV数据")
                return
        else:
            # 手动模式：如果没有数据，尝试从文件列表加载
            if not self.csv_data:
                if not hasattr(self, 'csv_file_list') or not self.csv_file_list:
                    print("❌ 没有可用的CSV文件列表")
                    return
                current_file = self.csv_file_list[self.current_file_index]
                print(f"🚀 开始CSV数据导入 - 文件: {current_file}")
                if not self.load_csv_data():
                    print("❌ CSV数据加载失败")
                    return

        # 清除现有数据
        self.clear_data()

        # 重置播放位置
        self.csv_data_index = 0

        # 设置标准直径
        self.set_standard_diameter_for_csv()

        # 开始播放 - 降低频率提高稳定性
        self.is_csv_playing = True
        self.csv_timer = QTimer()
        self.csv_timer.timeout.connect(self.update_csv_data_point)
        self.csv_timer.start(50)  # 每100ms更新一个数据点，提高稳定性

        # 更新按钮状态
        self.start_button.setText("测量中...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        print(f"📊 开始播放CSV数据，共{len(self.csv_data)}个数据点")

    def stop_csv_data_import(self):
        """停止CSV数据导入"""
        print("⏸️ 停止CSV数据导入")

        if self.csv_timer:
            self.csv_timer.stop()
            self.csv_timer = None

        self.is_csv_playing = False

        # 更新按钮状态
        self.start_button.setText("开始测量")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # 显示当前进度
        if self.csv_data:
            progress = (self.csv_data_index / len(self.csv_data)) * 100
            print(f"📊 数据导入已暂停，进度: {progress:.1f}%")

    def load_csv_data(self, file_path=None):
        """加载CSV数据文件"""
        import csv
        import os

        # 如果未提供路径，则使用文件列表中的当前文件
        if file_path is None:
            if self.current_file_index >= len(self.csv_file_list):
                print(f"❌ 文件索引超出范围: {self.current_file_index}")
                return False
            filename = self.csv_file_list[self.current_file_index]
            file_path = os.path.join(self.csv_base_path, filename)

        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False

            print(f"📁 加载CSV文件: {file_path}")

            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        # 找到目标列
                        measurement_col = None
                        diameter_col = None

                        for i, header in enumerate(headers):
                            if '测量序号' in header:
                                measurement_col = i
                            elif '计算直径' in header:
                                diameter_col = i

                        if measurement_col is None or diameter_col is None:
                            print(f"⚠️ 未找到必要的列: 测量序号={measurement_col}, 计算直径={diameter_col}")
                            # 尝试使用默认列索引
                            measurement_col = 0
                            diameter_col = 4  # 根据之前的分析，计算直径在第5列（索引4）

                        # 读取数据
                        self.csv_data = []
                        for row in reader:
                            if len(row) > max(measurement_col, diameter_col):
                                try:
                                    measurement_num = int(row[measurement_col])
                                    diameter_value = float(row[diameter_col])

                                    # 模拟深度数据（基于测量序号）
                                    depth_value = measurement_num * 1.0  # 每个测量点1.0mm深度

                                    self.csv_data.append({
                                        'measurement': measurement_num,
                                        'depth': depth_value,
                                        'diameter': diameter_value
                                    })
                                except (ValueError, IndexError):
                                    continue

                        print(f"✅ 成功加载 {len(self.csv_data)} 个数据点 (编码: {encoding})")
                        return True

                except UnicodeDecodeError:
                    continue

            print(f"❌ 无法使用任何编码读取文件: {file_path}")
            return False

        except Exception as e:
            print(f"❌ 加载CSV文件失败: {e}")
            return False

    def load_csv_data_by_index(self, file_index):
        """按索引加载CSV数据文件"""
        import csv
        import os

        if file_index >= len(self.csv_file_list):
            print(f"❌ 文件索引超出范围: {file_index}")
            return False

        filename = self.csv_file_list[file_index]
        file_path = os.path.join(self.csv_base_path, filename)

        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False

            print(f"📁 加载CSV文件: {file_path}")

            with open(file_path, 'r', encoding='gbk') as file:
                reader = csv.reader(file)
                headers = next(reader)

                # 找到目标列
                measurement_col = None
                diameter_col = None

                for i, header in enumerate(headers):
                    if '测量序号' in header:
                        measurement_col = i
                    if '计算直径' in header:
                        diameter_col = i

                if measurement_col is None or diameter_col is None:
                    print(f"❌ 找不到必需的列")
                    return False

                # 读取数据
                self.csv_data = []
                for row in reader:
                    try:
                        if len(row) > max(measurement_col, diameter_col):
                            measurement_num = int(row[measurement_col])
                            diameter = float(row[diameter_col])
                            # 每个测量点对应1.0mm深度
                            depth = measurement_num * 1.0
                            self.csv_data.append((depth, diameter))
                    except (ValueError, IndexError):
                        continue

                if len(self.csv_data) == 0:
                    print("❌ 没有有效数据")
                    return False

                # 计算统计信息
                depths = [d[0] for d in self.csv_data]
                diameters = [d[1] for d in self.csv_data]

                min_depth = min(depths)
                max_depth = max(depths)
                min_diameter = min(diameters)
                max_diameter = max(diameters)
                avg_diameter = sum(diameters) / len(diameters)

                print(f"✅ CSV数据加载成功:")
                print(f"   数据点数量: {len(self.csv_data)}")
                print(f"   深度范围: {min_depth:.0f} - {max_depth:.0f} mm")
                print(f"   直径范围: {min_diameter:.3f} - {max_diameter:.3f} mm")
                print(f"   平均直径: {avg_diameter:.3f} mm")

                self.csv_avg_diameter = avg_diameter
                return True

        except Exception as e:
            print(f"❌ CSV加载错误: {e}")
            return False

    def set_standard_diameter_for_csv(self):
        """为CSV数据设置标准直径"""
        # 标准直径已固定为17.6mm，无需额外设置
        print(f"🎯 使用固定标准直径: {self.standard_diameter} mm")

    def update_csv_data_point(self):
        """更新CSV数据点"""
        if self.csv_data_index >= len(self.csv_data):
            # 播放完成
            print("✅ CSV数据播放完成")
            self.stop_csv_data_import()

            # 显示最终统计
            final_max = self.max_diameter if self.max_diameter else 0
            final_min = self.min_diameter if self.min_diameter else 0

            print(f"📊 最终统计:")
            print(f"   最大圆直径: {final_max:.3f} mm")
            print(f"   最小圆直径: {final_min:.3f} mm")
            print(f"   直径范围: {final_max - final_min:.3f} mm")

            return

        # 获取当前数据点 - 支持两种数据格式
        data_point = self.csv_data[self.csv_data_index]
        if isinstance(data_point, dict):
            # 新格式：字典
            depth = data_point['depth']
            diameter = data_point['diameter']
        else:
            # 旧格式：元组
            depth, diameter = data_point

        # 更新图表
        self.update_data(depth, diameter)

        # 确定样品名称 - 兼容新旧两种模式
        if hasattr(self, 'current_hole_id') and self.current_hole_id:
            # 新模式：使用当前选中的孔位ID
            sample_name = self.current_hole_id
        elif hasattr(self, 'csv_file_list') and self.csv_file_list and hasattr(self, 'current_file_index'):
            # 旧模式：使用文件列表索引
            try:
                current_file = self.csv_file_list[self.current_file_index]
                sample_name = f"H0{self.current_file_index + 1}"
            except (IndexError, AttributeError):
                sample_name = "未知样品"
        else:
            # 默认模式
            sample_name = "当前样品"

        self.update_status(sample_name, depth, "测量中")

        # 输出进度（每100个数据点输出一次）
        if self.csv_data_index % 100 == 0:
            progress = ((self.csv_data_index + 1) / len(self.csv_data)) * 100
            current_max = self.max_diameter if self.max_diameter else 0
            current_min = self.min_diameter if self.min_diameter else 0
            print(f"📊 测量进度: {progress:.1f}% - 深度: {depth:.0f}mm, 直径: {diameter:.3f}mm | "
                  f"最大: {current_max:.3f}mm, 最小: {current_min:.3f}mm")

        self.csv_data_index += 1

        # 检查是否需要切换内窥镜图片
        self.update_endoscope_image_by_progress()

    def load_endoscope_images_for_hole(self, hole_id):
        """为指定孔位加载内窥镜图片"""
        import os
        import glob

        if hole_id not in self.hole_to_image_map:
            print(f"⚠️ 孔位 {hole_id} 没有关联的内窥镜图片目录")
            self.current_images = []
            return

        images_dir = self.hole_to_image_map[hole_id]
        if not os.path.exists(images_dir):
            print(f"⚠️ 图片目录不存在: {images_dir}")
            self.current_images = []
            return

        # 获取所有PNG图片文件
        image_files = glob.glob(os.path.join(images_dir, "*.png"))

        if not image_files:
            print(f"⚠️ 目录中没有找到PNG图片: {images_dir}")
            self.current_images = []
            return

        # 按文件名排序（确保按数值从小到大）
        def extract_number(filename):
            """从文件名中提取数值用于排序"""
            import re
            basename = os.path.basename(filename)
            # 提取文件名中的数字部分，如 "1-1.2.png" -> 1.2, "2-3.0.png" -> 3.0
            match = re.search(r'-(\d+\.?\d*)', basename)
            if match:
                return float(match.group(1))
            return 0

        image_files.sort(key=extract_number)
        self.current_images = image_files
        self.current_image_index = 0

        print(f"✅ 为孔位 {hole_id} 加载了 {len(image_files)} 张内窥镜图片:")
        for i, img in enumerate(image_files):
            print(f"   {i+1}. {os.path.basename(img)}")

        # 计算图片切换点
        self.calculate_image_switch_points()

        # 显示第一张图片
        if self.current_images:
            print("📸 自动显示第一张内窥镜图像")
            self.display_endoscope_image(0)
        else:
            print("❌ 没有图像可显示")

    def calculate_image_switch_points(self):
        """计算图片切换的数据点位置"""
        if not self.current_images or not self.csv_data:
            self.image_switch_points = []
            return

        total_data_points = len(self.csv_data)
        num_images = len(self.current_images)

        # 将数据点均匀分配给每张图片
        points_per_image = total_data_points / num_images

        self.image_switch_points = []
        for i in range(num_images):
            switch_point = int(i * points_per_image)
            self.image_switch_points.append(switch_point)

        print(f"📊 图片切换点计算完成:")
        print(f"   总数据点: {total_data_points}, 图片数量: {num_images}")
        print(f"   每张图片约 {points_per_image:.1f} 个数据点")
        print(f"   切换点: {self.image_switch_points}")

    def update_endoscope_image_by_progress(self):
        """根据CSV播放进度更新内窥镜图片"""
        # 只要有图像数据就允许切换，不需要等待"启动算法"
        if not self.current_images or not self.image_switch_points:
            return

        current_progress = self.csv_data_index

        # 确定当前应该显示哪张图片
        target_image_index = 0
        for i, switch_point in enumerate(self.image_switch_points):
            if current_progress >= switch_point:
                target_image_index = i
            else:
                break

        # 如果需要切换图片
        if target_image_index != self.current_image_index:
            self.current_image_index = target_image_index
            self.display_endoscope_image(target_image_index)

            progress_percent = (current_progress / len(self.csv_data)) * 100
            print(f"🖼️ 切换内窥镜图片: 第{target_image_index + 1}张 "
                  f"(进度: {progress_percent:.1f}%, 数据点: {current_progress})")

    def display_endoscope_image(self, image_index):
        """显示指定索引的内窥镜图片"""
        import os

        print(f"🔍 调试: 尝试显示图像索引 {image_index}")
        print(f"🔍 调试: 当前图像列表长度 {len(self.current_images) if self.current_images else 0}")

        if not self.current_images:
            print("❌ 调试: 图像列表为空")
            return

        if image_index >= len(self.current_images):
            print(f"❌ 调试: 索引超出范围 {image_index}/{len(self.current_images)}")
            return

        image_path = self.current_images[image_index]
        print(f"🔍 调试: 图像路径 {image_path}")
        print(f"🔍 调试: 文件存在 {os.path.exists(image_path)}")

        try:
            # 使用内窥镜视图组件显示图片
            self.endoscope_view.update_image(image_path)
            print(f"✅ 显示内窥镜图片: {os.path.basename(image_path)}")

        except Exception as e:
            print(f"❌ 显示内窥镜图片失败: {e}")
            import traceback
            print(f"🔍 详细错误信息: {traceback.format_exc()}")


if __name__ == "__main__":
    """测试代码"""
    import sys
    from PySide6.QtWidgets import QApplication
    from worker_thread import WorkerThread
    
    app = QApplication(sys.argv)
    
    # 创建图表组件
    chart = RealtimeChart()
    chart.show()
    
    # 创建数据源
    worker = WorkerThread()
    worker.data_updated.connect(chart.update_data)
    worker.status_updated.connect(chart.update_status)
    
    # 注意：按钮已经连接到CSV数据导入功能
    # 如果需要使用worker线程，请注释掉CSV功能的按钮连接
    # chart.start_button.clicked.connect(lambda: worker.start_measurement("TEST_001"))
    # chart.stop_button.clicked.connect(worker.stop_measurement)
    
    sys.exit(app.exec())
