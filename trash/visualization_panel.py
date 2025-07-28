"""
可视化面板组件
从main_window.py重构提取的独立UI组件
负责管孔检测视图、状态图例、视图控制等功能
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, 
    QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

# 导入核心业务组件
from core_business.models.hole_data import HoleStatus
from core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget


class VisualizationPanel(QGroupBox):
    """
    可视化面板组件
    包含状态图例、视图控制按钮和动态扇形显示区域
    """
    
    # 定义信号
    sector_changed = Signal(str)  # 扇形区域变化
    macro_view_requested = Signal()  # 宏观视图请求
    micro_view_requested = Signal()  # 微观视图请求
    orientation_unified = Signal()  # 统一竖向方向
    
    def __init__(self, parent=None):
        super().__init__("管孔检测视图", parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI组件"""
        # 设置面板字体
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        self.setFont(center_panel_font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 状态图例
        self.legend_frame = self._create_status_legend()
        layout.addWidget(self.legend_frame)

        # 视图控制按钮
        self.view_controls_frame = self._create_view_controls()
        layout.addWidget(self.view_controls_frame)

        # 创建主要内容区域
        self._create_main_content_area(layout)
    
    def _create_status_legend(self) -> QWidget:
        """创建状态图例"""
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.StyledPanel)
        legend_frame.setMaximumHeight(50)

        layout = QHBoxLayout(legend_frame)
        layout.setContentsMargins(8, 8, 8, 8)

        # 获取状态颜色
        status_colors = self._get_status_colors()
        status_names = {
            HoleStatus.PENDING: "待检",
            HoleStatus.QUALIFIED: "合格",
            HoleStatus.DEFECTIVE: "异常",
            HoleStatus.BLIND: "盲孔",
            HoleStatus.TIE_ROD: "拉杆孔",
            HoleStatus.PROCESSING: "检测中"
        }

        # 设置图例字体
        legend_font = QFont()
        legend_font.setPointSize(11)

        for status, color in status_colors.items():
            # 颜色指示器
            color_label = QLabel()
            color_label.setFixedSize(16, 16)
            
            # 处理颜色格式
            css_color = self._process_color(color)
            
            # 设置颜色样式
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {css_color};
                    border: 1px solid #999;
                    border-radius: 2px;
                }}
            """)
            color_label.setObjectName("StatusColorLabel")

            # 状态文本
            text_label = QLabel(status_names.get(status, status.value))
            text_label.setFont(legend_font)

            layout.addWidget(color_label)
            layout.addWidget(text_label)
            layout.addSpacing(15)

        layout.addStretch()
        return legend_frame
    
    def _create_view_controls(self) -> QWidget:
        """创建视图控制按钮"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(view_label)
        
        # 宏观区域视图按钮
        self.macro_view_btn = QPushButton("📊 宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(True)
        self.macro_view_btn.setMinimumHeight(35)
        self.macro_view_btn.setMinimumWidth(140)
        self.macro_view_btn.setToolTip("显示整个管板的全貌，适合快速浏览和状态概览")
        self.macro_view_btn.setProperty("class", "PrimaryAction")
        layout.addWidget(self.macro_view_btn)
        
        # 微观管孔视图按钮
        self.micro_view_btn = QPushButton("🔍 微观管孔视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setMinimumHeight(35)
        self.micro_view_btn.setMinimumWidth(140)
        self.micro_view_btn.setToolTip("显示管孔的详细信息，适合精确检查和操作")
        self.micro_view_btn.setProperty("class", "ActionButton")
        layout.addWidget(self.micro_view_btn)
        
        # 添加分隔符
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 方向统一按钮
        self.orient_btn = QPushButton("📐 统一竖向")
        self.orient_btn.setMinimumHeight(35)
        self.orient_btn.setMinimumWidth(100)
        self.orient_btn.setToolTip("确保管板在所有视图中都是竖向摆放")
        self.orient_btn.setProperty("class", "WarningButton")
        layout.addWidget(self.orient_btn)
        
        # 添加当前视图状态指示器
        self.view_status_label = QLabel("当前: 宏观视图")
        self.view_status_label.setFont(QFont("Arial", 10))
        self.view_status_label.setObjectName("ViewStatusLabel")
        layout.addWidget(self.view_status_label)
        
        layout.addStretch()
        
        return control_frame
    
    def _create_main_content_area(self, layout):
        """创建主要内容区域"""
        # 创建主要内容区域
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建扇形显示容器
        sector_container = QWidget()
        sector_container_layout = QVBoxLayout(sector_container)
        sector_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 动态扇形区域显示
        self.dynamic_sector_display = DynamicSectorDisplayWidget()
        self.dynamic_sector_display.setMinimumSize(800, 700)
        
        # 添加到容器
        sector_container_layout.addWidget(self.dynamic_sector_display)
        main_layout.addWidget(sector_container)
        
        # 添加到主布局
        layout.addWidget(main_widget)
        
        # 设置graphics_view引用以保持向后兼容
        self.graphics_view = self.dynamic_sector_display.graphics_view
    
    def setup_connections(self):
        """设置信号连接"""
        # 连接按钮信号
        self.macro_view_btn.clicked.connect(self._on_macro_view_clicked)
        self.micro_view_btn.clicked.connect(self._on_micro_view_clicked)
        self.orient_btn.clicked.connect(self._on_orientation_clicked)
        
        # 连接动态扇形显示信号
        self.dynamic_sector_display.sector_changed.connect(self._on_sector_changed)
    
    def _get_status_colors(self) -> dict:
        """获取状态颜色映射"""
        try:
            from core_business.graphics.hole_graphics_item import HoleGraphicsItem
            return HoleGraphicsItem.STATUS_COLORS
        except:
            # 默认颜色映射
            return {
                HoleStatus.PENDING: "#CCCCCC",
                HoleStatus.QUALIFIED: "#4CAF50",
                HoleStatus.DEFECTIVE: "#F44336",
                HoleStatus.BLIND: "#FF9800",
                HoleStatus.TIE_ROD: "#9C27B0",
                HoleStatus.PROCESSING: "#2196F3"
            }
    
    def _process_color(self, color) -> str:
        """处理颜色格式"""
        if hasattr(color, 'name'):
            # QColor对象，转换为十六进制颜色
            return color.name()
        elif isinstance(color, str):
            # 已经是字符串颜色
            return color if color.startswith('#') else f"#{color}"
        else:
            # 其他类型，尝试转换
            return str(color)
    
    def _on_macro_view_clicked(self):
        """处理宏观视图按钮点击"""
        self.micro_view_btn.setChecked(False)
        self.macro_view_btn.setChecked(True)
        self.view_status_label.setText("当前: 宏观视图")
        self.macro_view_requested.emit()
    
    def _on_micro_view_clicked(self):
        """处理微观视图按钮点击"""
        self.macro_view_btn.setChecked(False)
        self.micro_view_btn.setChecked(True)
        self.view_status_label.setText("当前: 微观视图")
        self.micro_view_requested.emit()
    
    def _on_orientation_clicked(self):
        """处理统一竖向按钮点击"""
        self.orientation_unified.emit()
    
    def _on_sector_changed(self, sector_id: str):
        """处理扇形区域变化"""
        self.sector_changed.emit(sector_id)
    
    # 公共方法
    def switch_to_macro_view(self):
        """切换到宏观视图"""
        self._on_macro_view_clicked()
    
    def switch_to_micro_view(self):
        """切换到微观视图"""
        self._on_micro_view_clicked()
    
    def ensure_vertical_orientation(self):
        """确保垂直方向"""
        self._on_orientation_clicked()
    
    def get_dynamic_sector_display(self):
        """获取动态扇形显示组件"""
        return self.dynamic_sector_display
    
    def get_graphics_view(self):
        """获取图形视图组件"""
        return self.graphics_view
    
    def update_view_status(self, status: str):
        """更新视图状态显示"""
        self.view_status_label.setText(f"当前: {status}")
    
    def set_macro_view_active(self, active: bool):
        """设置宏观视图激活状态"""
        self.macro_view_btn.setChecked(active)
        if active:
            self.micro_view_btn.setChecked(False)
            self.view_status_label.setText("当前: 宏观视图")
    
    def set_micro_view_active(self, active: bool):
        """设置微观视图激活状态"""
        self.micro_view_btn.setChecked(active)
        if active:
            self.macro_view_btn.setChecked(False)
            self.view_status_label.setText("当前: 微观视图")
    
    def get_current_view_mode(self) -> str:
        """获取当前视图模式"""
        if self.macro_view_btn.isChecked():
            return "macro"
        elif self.micro_view_btn.isChecked():
            return "micro"
        else:
            return "unknown"