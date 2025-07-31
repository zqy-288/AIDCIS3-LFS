"""
原生主检测视图 - 完全还原old版本UI布局
使用现有重构后的文件和功能模块，严格按照old版本的三栏式布局实现
采用高内聚、低耦合的设计原则
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QGroupBox,
    QLineEdit, QTextEdit, QFrame, QSplitter, QCompleter,
    QComboBox, QCheckBox, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel
from PySide6.QtGui import QFont, QColor

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入现有的重构后功能模块
try:
    # 控制器和服务 - 使用P1本地版本
    from .controllers.main_window_controller import MainWindowController
    from .controllers.services.search_service import SearchService
    from .controllers.services.status_service import StatusService
    from .controllers.services.file_service import FileService
    
    # UI组件 - 使用P1本地版本
    from .ui.components.toolbar_component import ToolbarComponent
    
    # 图形组件
    from src.core_business.graphics.graphics_view import OptimizedGraphicsView
    from src.pages.main_detection_p1.components.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
    # CompletePanoramaWidget已移至中间栏显示
    
    # 数据模型
    from src.core_business.models.hole_data import HoleCollection
    from src.models.product_model import get_product_manager
    from .modules.product_selection import ProductSelectionDialog
    
    # 扇形协调器
    from src.pages.main_detection_p1.components.panorama_sector_coordinator import PanoramaSectorCoordinator
    
    # 模拟控制器
    from src.pages.main_detection_p1.components.simulation_controller import SimulationController
    
    HAS_REFACTORED_MODULES = True
except ImportError as e:
    logging.warning(f"部分重构模块导入失败: {e}")
    HAS_REFACTORED_MODULES = False


class NativeLeftInfoPanel(QWidget):
    """左侧信息面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_info_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_hole_data = None
        self.detection_stats = {}
        
        # 设置固定宽度 (old版本: 380px)
        self.setFixedWidth(380)
        
        # 初始化UI
        self.setup_ui()
        self.initialize_data()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)

        # 设置全局字体
        panel_font = QFont()
        panel_font.setPointSize(10)
        self.setFont(panel_font)

        # 组标题字体
        group_font = QFont()
        group_font.setPointSize(10)
        group_font.setBold(True)

        # 1. 检测进度组 (恢复old版本的设计)
        self.progress_group = self._create_progress_group(group_font)
        layout.addWidget(self.progress_group)

        # 2. 状态统计组
        self.stats_group = self._create_stats_group(group_font)
        layout.addWidget(self.stats_group)

        # 3. 选中孔位信息组
        self.hole_info_group = self._create_hole_info_group(group_font)
        layout.addWidget(self.hole_info_group)

        # 4. 文件信息组
        self.file_info_group = self._create_file_info_group(group_font)
        layout.addWidget(self.file_info_group)

        # 5. 全景预览组 - 设置为扩展以填充可用空间
        self.panorama_group = self._create_panorama_group(group_font)
        layout.addWidget(self.panorama_group, 1)  # 添加拉伸因子1，使其扩展

        # 6. 选中扇形组
        self.sector_stats_group = self._create_sector_stats_group(group_font)
        layout.addWidget(self.sector_stats_group)

    def _create_progress_group(self, group_font):
        """创建检测进度组 - 恢复old版本设计"""
        group = QGroupBox("检测进度")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)
        layout.addWidget(self.progress_bar)

        # 批次信息
        self.current_batch_label = QLabel("检测批次: 未开始")
        self.current_batch_label.setFont(QFont("", 9))
        layout.addWidget(self.current_batch_label)

        # 已完成和待完成数量
        count_layout = QHBoxLayout()
        count_layout.setSpacing(2)
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")
        self.completed_count_label.setFont(QFont("", 9))
        self.pending_count_label.setFont(QFont("", 9))
        count_layout.addWidget(self.completed_count_label)
        count_layout.addWidget(self.pending_count_label)
        layout.addLayout(count_layout)

        # 合格率和完成率
        rate_layout = QHBoxLayout()
        rate_layout.setSpacing(2)
        self.completion_rate_label = QLabel("完成率: 0%")
        self.qualification_rate_label = QLabel("合格率: 0%")
        self.completion_rate_label.setFont(QFont("", 9))
        self.qualification_rate_label.setFont(QFont("", 9))
        rate_layout.addWidget(self.completion_rate_label)
        rate_layout.addWidget(self.qualification_rate_label)
        layout.addLayout(rate_layout)

        return group

    def _create_stats_group(self, group_font):
        """创建状态统计组"""
        group = QGroupBox("状态统计")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # 状态统计标签 (old版本样式)
        self.total_label = QLabel("总数: 0")
        self.qualified_label = QLabel("合格: 0")
        self.unqualified_label = QLabel("异常: 0")
        self.not_detected_label = QLabel("待检: 0")
        self.blind_label = QLabel("盲孔: 0")
        self.tie_rod_label = QLabel("拉杆: 0")

        for label in [self.total_label, self.qualified_label, self.unqualified_label,
                     self.not_detected_label, self.blind_label, self.tie_rod_label]:
            label.setFont(label_font)

        # 网格布局 (old版本样式: 3列2行)
        layout.addWidget(self.total_label, 0, 0)
        layout.addWidget(self.qualified_label, 0, 1)
        layout.addWidget(self.unqualified_label, 0, 2)
        layout.addWidget(self.not_detected_label, 1, 0)
        layout.addWidget(self.blind_label, 1, 1)
        layout.addWidget(self.tie_rod_label, 1, 2)

        return group

    def _create_hole_info_group(self, group_font):
        """创建孔位信息组"""
        group = QGroupBox("选中孔位信息")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # 孔位信息标签 (两行两列布局)
        # 第一行：ID 和 坐标
        layout.addWidget(QLabel("ID:"), 0, 0)
        self.selected_hole_id_label = QLabel("--")
        self.selected_hole_id_label.setFont(label_font)
        layout.addWidget(self.selected_hole_id_label, 0, 1)

        layout.addWidget(QLabel("坐标:"), 0, 2)
        self.selected_hole_pos_label = QLabel("--")
        self.selected_hole_pos_label.setFont(label_font)
        layout.addWidget(self.selected_hole_pos_label, 0, 3)

        # 第二行：状态 和 描述
        layout.addWidget(QLabel("状态:"), 1, 0)
        self.selected_hole_status_label = QLabel("--")
        self.selected_hole_status_label.setFont(label_font)
        layout.addWidget(self.selected_hole_status_label, 1, 1)

        layout.addWidget(QLabel("描述:"), 1, 2)
        self.selected_hole_desc_label = QLabel("--")
        self.selected_hole_desc_label.setFont(label_font)
        layout.addWidget(self.selected_hole_desc_label, 1, 3)

        return group

    def _create_file_info_group(self, group_font):
        """创建文件信息组"""
        group = QGroupBox("文件信息")
        group.setFont(group_font)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        label_font = QFont()
        label_font.setPointSize(9)

        # DXF文件信息 (old版本样式)
        layout.addWidget(QLabel("DXF文件:"), 0, 0)
        self.dxf_file_label = QLabel("未加载")
        self.dxf_file_label.setFont(label_font)
        self.dxf_file_label.setMaximumWidth(200)
        self.dxf_file_label.setWordWrap(False)
        layout.addWidget(self.dxf_file_label, 0, 1)

        layout.addWidget(QLabel("产品型号:"), 1, 0)
        self.product_label = QLabel("--")
        self.product_label.setFont(label_font)
        layout.addWidget(self.product_label, 1, 1)

        return group
    
    def _create_panorama_group(self, group_font):
        """创建全景预览组"""
        group = QGroupBox("全景预览")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 使用具有用户缩放功能的完整全景图组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        self.sidebar_panorama = CompletePanoramaWidget()
        # 设置默认缩放比例为10%，解决圆形缩放不够的问题
        if hasattr(self.sidebar_panorama, 'set_user_hole_scale_factor'):
            self.sidebar_panorama.set_user_hole_scale_factor(0.1)
        # 设置为自适应大小，使用合适的尺寸策略
        self.sidebar_panorama.setMinimumHeight(200)  # 最小高度
        self.sidebar_panorama.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # 设置样式
        self.sidebar_panorama.setStyleSheet("""
            CompletePanoramaWidget {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(self.sidebar_panorama)
        
        return group


    def _create_sector_stats_group(self, group_font):
        """创建选中扇形组"""
        group = QGroupBox("选中扇形")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 当前扇形标签
        self.current_sector_label = QLabel("当前扇形: 未选择")
        self.current_sector_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.current_sector_label)
        
        # 扇形统计表格
        self.sector_stats_table = QTableWidget(6, 2)  # 6行2列
        self.sector_stats_table.setHorizontalHeaderLabels(["状态", "数量"])
        self.sector_stats_table.verticalHeader().hide()
        self.sector_stats_table.horizontalHeader().setStretchLastSection(True)
        self.sector_stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sector_stats_table.setMinimumHeight(180)
        self.sector_stats_table.setMaximumHeight(200)
        
        # 设置表格样式
        self.sector_stats_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ddd;
                font-size: 10px;
            }
            QTableWidget::item {
                padding: 2px;
            }
        """)
        
        # 初始化表格行
        status_labels = [
            ("pending", "待检"),
            ("qualified", "合格"),
            ("defective", "异常"),
            ("blind", "盲孔"),
            ("tie_rod", "拉杆"),
            ("total", "总计")
        ]
        
        for i, (key, label) in enumerate(status_labels):
            self.sector_stats_table.setItem(i, 0, QTableWidgetItem(label))
            self.sector_stats_table.setItem(i, 1, QTableWidgetItem("0"))
            # 设置总计行为粗体
            if key == "total":
                font = self.sector_stats_table.item(i, 0).font()
                font.setBold(True)
                self.sector_stats_table.item(i, 0).setFont(font)
                self.sector_stats_table.item(i, 1).setFont(font)
        
        layout.addWidget(self.sector_stats_table)
        
        # 保留兼容性
        self.sector_stats_label = self.current_sector_label

        return group


    def initialize_data(self):
        """初始化数据"""
        self.update_progress_display()
        self.logger.info("✅ 左侧信息面板初始化完成")

    def update_progress_display(self, data=None):
        """更新进度显示 - 使用重构后的数据源"""
        # 默认数据
        if data is None:
            data = {
                "total": 0, "qualified": 0, "unqualified": 0, 
                "not_detected": 0, "blind": 0, "tie_rod": 0,
                "progress": 0.0, "completion_rate": 0.0, "qualification_rate": 0.0,
                "completed": 0, "pending": 0
            }

        # 更新进度组
        progress = data.get('progress', 0)
        self.progress_bar.setValue(int(progress))
        
        # 更新已完成和待完成数量
        completed = data.get('completed', data.get('qualified', 0) + data.get('unqualified', 0))
        pending = data.get('pending', data.get('not_detected', 0))
        self.completed_count_label.setText(f"已完成: {completed}")
        self.pending_count_label.setText(f"待完成: {pending}")
        
        # 更新完成率和合格率
        completion_rate = data.get('completion_rate', 0)
        qualification_rate = data.get('qualification_rate', 0)
        self.completion_rate_label.setText(f"完成率: {completion_rate:.1f}%")
        self.qualification_rate_label.setText(f"合格率: {qualification_rate:.1f}%")

        # 更新统计面板
        self.total_label.setText(f"总数: {data.get('total', 0)}")
        self.qualified_label.setText(f"合格: {data.get('qualified', 0)}")
        self.unqualified_label.setText(f"异常: {data.get('unqualified', 0)}")
        self.not_detected_label.setText(f"待检: {data.get('not_detected', 0)}")
        self.blind_label.setText(f"盲孔: {data.get('blind', 0)}")
        self.tie_rod_label.setText(f"拉杆: {data.get('tie_rod', 0)}")

    def update_hole_info(self, hole_data):
        """更新孔位信息"""
        if hole_data:
            self.selected_hole_id_label.setText(hole_data.get('id', '--'))
            self.selected_hole_pos_label.setText(hole_data.get('position', '--'))
            self.selected_hole_status_label.setText(hole_data.get('status', '--'))
            self.selected_hole_desc_label.setText(hole_data.get('description', '--'))
        else:
            self.selected_hole_id_label.setText("--")
            self.selected_hole_pos_label.setText("--")
            self.selected_hole_status_label.setText("--")
            self.selected_hole_desc_label.setText("--")

    def update_file_info(self, dxf_path=None, product_name=None):
        """更新文件信息"""
        if dxf_path:
            file_name = Path(dxf_path).name
            self.dxf_file_label.setText(file_name)
        else:
            self.dxf_file_label.setText("未加载")
            
        if product_name:
            self.product_label.setText(product_name)
        else:
            self.product_label.setText("--")
    
    def update_selected_sector(self, sector):
        """更新选中的扇形信息"""
        if hasattr(self, 'current_sector_label'):
            sector_name = sector.value if hasattr(sector, 'value') else str(sector)
            self.current_sector_label.setText(f"当前扇形: {sector_name}")
    
    def update_sector_stats(self, stats_data):
        """更新扇形统计表格"""
        if hasattr(self, 'sector_stats_table') and stats_data:
            # 更新表格数据
            row_mapping = {
                'pending': 0,
                'qualified': 1,
                'defective': 2,
                'blind': 3,
                'tie_rod': 4,
                'total': 5
            }
            
            for status, row in row_mapping.items():
                count = stats_data.get(status, 0)
                self.sector_stats_table.item(row, 1).setText(str(count))


    def update_sector_stats_text(self, stats_text):
        """更新扇形统计文本（兼容方法）"""
        if hasattr(self, 'current_sector_label') and stats_text:
            # 解析文本并更新表格
            lines = stats_text.strip().split('\n')
            if lines:
                # 更新当前扇形标签
                if lines[0].startswith('当前扇形:'):
                    self.current_sector_label.setText(lines[0])
                
                # 解析统计数据
                stats_dict = {}
                for line in lines[1:]:
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            status = parts[0].strip()
                            count_str = parts[1].strip()
                            # 提取数字
                            count = 0
                            for word in count_str.split():
                                if word.isdigit():
                                    count = int(word)
                                    break
                            
                            # 映射状态名
                            status_map = {
                                'blind': 'blind',
                                '盲孔': 'blind',
                                'defective': 'defective',
                                '异常': 'defective',
                                'pending': 'pending',
                                '待检': 'pending',
                                'qualified': 'qualified',
                                '合格': 'qualified',
                                'tie_rod': 'tie_rod',
                                '拉杆': 'tie_rod',
                                'total': 'total',
                                '总计': 'total'
                            }
                            
                            for key, mapped in status_map.items():
                                if key in status.lower():
                                    stats_dict[mapped] = count
                                    break
                
                # 更新表格
                if stats_dict:
                    self.update_sector_stats(stats_dict)


class NativeCenterVisualizationPanel(QWidget):
    """中间可视化面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_selected = Signal(str)
    view_mode_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_view_mode = "micro"  # 默认为微观扇形视图
        self.current_sector = None
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        # 主组框 (old版本样式)
        panel = QGroupBox("管孔检测视图")
        
        # 设置组标题字体
        center_panel_font = QFont()
        center_panel_font.setPointSize(12)
        center_panel_font.setBold(True)
        panel.setFont(center_panel_font)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # 1. 状态图例已移除 (按用户要求删除)

        # 2. 视图控制 (old版本的层级化显示控制)
        view_controls_frame = self._create_view_controls()
        layout.addWidget(view_controls_frame)

        # 3. 主显示区域 (old版本: DynamicSectorDisplayWidget, 800×700px)
        main_display_widget = self._create_main_display_area()
        layout.addWidget(main_display_widget)

        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(panel)


    def _create_view_controls(self):
        """创建视图控制 - old版本的层级化显示控制"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # 视图模式标签
        view_label = QLabel("视图模式:")
        view_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(view_label)
        
        # 宏观区域视图按钮 (显示完整圆形全景)
        self.macro_view_btn = QPushButton("📊 宏观区域视图")
        self.macro_view_btn.setCheckable(True)
        self.macro_view_btn.setChecked(False)  # 不再默认选中
        self.macro_view_btn.setMinimumHeight(35)
        self.macro_view_btn.setMinimumWidth(140)
        self.macro_view_btn.setToolTip("显示整个管板的全貌，适合快速浏览和状态概览")
        
        # 微观孔位视图按钮（默认选中）
        self.micro_view_btn = QPushButton("🔍 微观孔位视图")
        self.micro_view_btn.setCheckable(True)
        self.micro_view_btn.setChecked(True)  # 默认选中扇形视图
        self.micro_view_btn.setMinimumHeight(35)
        self.micro_view_btn.setMinimumWidth(140)
        self.micro_view_btn.setToolTip("显示孔位的详细信息，适合精确检测和分析")
        
        
        layout.addWidget(self.macro_view_btn)
        layout.addWidget(self.micro_view_btn)
        
        layout.addSpacing(20)
        
        
        layout.addStretch()
        return control_frame

    def _create_main_display_area(self):
        """创建主显示区域 - 初始为空白，等待加载CAP1000 DXF"""
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # 创建空白的图形视图，准备加载CAP1000数据
        if HAS_REFACTORED_MODULES:
            try:
                self.graphics_view = OptimizedGraphicsView()
                self.graphics_view.setMinimumSize(800, 700)
                main_layout.addWidget(self.graphics_view)
                
                # 获取或创建scene
                scene = None
                if hasattr(self.graphics_view, 'scene'):
                    scene = self.graphics_view.scene
                    if scene is None:
                        # 如果scene属性存在但为None，创建新的
                        from PySide6.QtWidgets import QGraphicsScene
                        scene = QGraphicsScene()
                        self.graphics_view.setScene(scene)
                else:
                    # scene是方法
                    try:
                        scene = self.graphics_view.scene()
                    except:
                        from PySide6.QtWidgets import QGraphicsScene
                        scene = QGraphicsScene()
                        self.graphics_view.setScene(scene)
                    
                from PySide6.QtWidgets import QGraphicsTextItem
                from PySide6.QtGui import QFont
                
                info_text = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
                font = QFont()
                font.setPointSize(14)
                info_text.setFont(font)
                info_text.setPos(250, 350)
                scene.addItem(info_text)
                
                self.logger.info("✅ 创建空白视图，等待CAP1000数据")
            except Exception as e:
                self.logger.warning(f"OptimizedGraphicsView创建失败: {e}")
                self.graphics_view = self._create_fallback_graphics_view()
                main_layout.addWidget(self.graphics_view)
        else:
            self.graphics_view = self._create_fallback_graphics_view()
            main_layout.addWidget(self.graphics_view)
        
        # 保留workpiece_diagram引用以兼容
        self.workpiece_diagram = None
        
        return main_widget
    
    def _on_hole_clicked(self, hole_id, status):
        """处理孔位点击事件"""
        self.logger.info(f"孔位点击: {hole_id}, 状态: {status}")
        # 发射信号给上层
        self.hole_selected.emit(hole_id)

    def _create_fallback_graphics_view(self):
        """创建备用图形视图"""
        # 最终备用方案
        from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
        from PySide6.QtGui import QFont
        
        view = QGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.setMinimumSize(800, 700)
        
        # 显示初始提示信息
        text_item = QGraphicsTextItem("请选择产品型号 (CAP1000) 或加载DXF文件")
        font = QFont()
        font.setPointSize(14)
        text_item.setFont(font)
        text_item.setPos(250, 350)
        scene.addItem(text_item)
        
        return view

    def setup_connections(self):
        """设置信号连接"""
        # 视图模式按钮连接
        self.macro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("macro"))
        self.micro_view_btn.clicked.connect(lambda: self._on_view_mode_changed("micro"))
        

    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        # 更新按钮状态
        self.macro_view_btn.setChecked(mode == "macro")
        self.micro_view_btn.setChecked(mode == "micro")
        
        self.current_view_mode = mode
        self.view_mode_changed.emit(mode)
        self.logger.info(f"🔄 视图模式切换到: {mode}")


class NativeRightOperationsPanel(QScrollArea):
    """右侧操作面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    start_detection = Signal()
    pause_detection = Signal()
    stop_detection = Signal()
    reset_detection = Signal()
    start_simulation = Signal()  # 模拟检测信号
    pause_simulation = Signal()
    stop_simulation = Signal()
    file_operation_requested = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.detection_running = False
        
        # 设置滚动区域属性 (old版本样式)
        self.setWidgetResizable(True)
        self.setMaximumWidth(350)  # old版本精确宽度
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI布局 - 严格按照old版本结构"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 设置字体
        panel_font = QFont()
        panel_font.setPointSize(11)
        
        group_title_font = QFont()
        group_title_font.setPointSize(12)
        group_title_font.setBold(True)
        
        button_font = QFont()
        button_font.setPointSize(11)

        # 1. 检测控制组 (old版本第一组)
        detection_group = self._create_detection_control_group(group_title_font, button_font)
        layout.addWidget(detection_group)

        # 2. 模拟检测组 (恢复模拟检测功能)
        simulation_group = self._create_simulation_group(group_title_font, button_font)
        layout.addWidget(simulation_group)

        # 3. 文件操作组 (old版本第三组)
        file_group = self._create_file_operations_group(group_title_font, button_font)
        layout.addWidget(file_group)

        # 4. 视图控制组 (old版本第四组)
        view_group = self._create_view_control_group(group_title_font, button_font)
        layout.addWidget(view_group)

        # 5. 孔位操作组已删除 (按用户要求)

        # 6. 其他操作组
        other_group = self._create_other_operations_group(group_title_font, button_font)
        layout.addWidget(other_group)

        layout.addStretch()
        self.setWidget(content_widget)

    def _create_detection_control_group(self, group_font, button_font):
        """创建检测控制组 - old版本样式"""
        group = QGroupBox("检测控制")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 检测按钮 (old版本样式和尺寸)
        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setMinimumHeight(45)
        self.start_detection_btn.setFont(button_font)
        self.start_detection_btn.setEnabled(False)  # old版本初始状态
        self.start_detection_btn.setStyleSheet("background-color: green; color: white;")

        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setMinimumHeight(45)
        self.pause_detection_btn.setFont(button_font)
        self.pause_detection_btn.setEnabled(False)
        self.pause_detection_btn.setStyleSheet("background-color: orange; color: white;")

        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setMinimumHeight(45)
        self.stop_detection_btn.setFont(button_font)
        self.stop_detection_btn.setEnabled(False)
        self.stop_detection_btn.setStyleSheet("background-color: red; color: white;")

        layout.addWidget(self.start_detection_btn)
        layout.addWidget(self.pause_detection_btn)
        layout.addWidget(self.stop_detection_btn)

        return group

    def _create_simulation_group(self, group_font, button_font):
        """创建模拟检测组"""
        group = QGroupBox("模拟检测")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 模拟检测按钮
        self.start_simulation_btn = QPushButton("开始模拟")
        self.start_simulation_btn.setMinimumHeight(40)
        self.start_simulation_btn.setFont(button_font)
        self.start_simulation_btn.setToolTip("启动模拟检测，按蛇形路径顺序渲染")

        self.pause_simulation_btn = QPushButton("暂停模拟")
        self.pause_simulation_btn.setMinimumHeight(40)
        self.pause_simulation_btn.setFont(button_font)
        self.pause_simulation_btn.setEnabled(False)

        self.stop_simulation_btn = QPushButton("停止模拟")
        self.stop_simulation_btn.setMinimumHeight(40)
        self.stop_simulation_btn.setFont(button_font)
        self.stop_simulation_btn.setEnabled(False)

        layout.addWidget(self.start_simulation_btn)
        layout.addWidget(self.pause_simulation_btn)
        layout.addWidget(self.stop_simulation_btn)

        return group

    def _create_file_operations_group(self, group_font, button_font):
        """创建文件操作组"""
        group = QGroupBox("文件操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 文件操作按钮
        self.load_dxf_btn = QPushButton("加载DXF文件")
        self.load_dxf_btn.setMinimumHeight(40)
        self.load_dxf_btn.setFont(button_font)

        self.load_product_btn = QPushButton("选择产品型号")
        self.load_product_btn.setMinimumHeight(40)
        self.load_product_btn.setFont(button_font)

        self.export_data_btn = QPushButton("导出数据")
        self.export_data_btn.setMinimumHeight(40)
        self.export_data_btn.setFont(button_font)

        layout.addWidget(self.load_dxf_btn)
        layout.addWidget(self.load_product_btn)
        layout.addWidget(self.export_data_btn)

        return group

    def _create_view_control_group(self, group_font, button_font):
        """创建视图控制组"""
        group = QGroupBox("视图控制")
        group.setFont(group_font)
        layout = QHBoxLayout(group)

        self.zoom_in_button = QPushButton("放大")
        self.zoom_out_button = QPushButton("缩小")  
        self.reset_zoom_button = QPushButton("重置")

        for btn in [self.zoom_in_button, self.zoom_out_button, self.reset_zoom_button]:
            btn.setMinimumHeight(35)
            btn.setFont(button_font)

        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.reset_zoom_button)

        return group


    def _create_other_operations_group(self, group_font, button_font):
        """创建其他操作组"""
        group = QGroupBox("其他操作")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 报告相关按钮
        self.generate_report_btn = QPushButton("生成报告")
        self.generate_report_btn.setMinimumHeight(40)
        self.generate_report_btn.setFont(button_font)

        self.export_report_btn = QPushButton("导出报告")
        self.export_report_btn.setMinimumHeight(40)
        self.export_report_btn.setFont(button_font)

        layout.addWidget(self.generate_report_btn)
        layout.addWidget(self.export_report_btn)

        return group

    def setup_connections(self):
        """设置信号连接"""
        # 检测控制信号
        self.start_detection_btn.clicked.connect(self.start_detection.emit)
        self.pause_detection_btn.clicked.connect(self.pause_detection.emit)
        self.stop_detection_btn.clicked.connect(self.stop_detection.emit)

        # 模拟控制信号
        self.start_simulation_btn.clicked.connect(self.start_simulation.emit)
        self.pause_simulation_btn.clicked.connect(self.pause_simulation.emit)
        self.stop_simulation_btn.clicked.connect(self.stop_simulation.emit)

        # 文件操作信号
        self.load_dxf_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_dxf", {}))
        self.load_product_btn.clicked.connect(lambda: self.file_operation_requested.emit("load_product", {}))
        self.export_data_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_data", {}))

        # 其他操作信号
        self.generate_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("generate_report", {}))
        self.export_report_btn.clicked.connect(lambda: self.file_operation_requested.emit("export_report", {}))


    def update_detection_state(self, running=False):
        """更新检测状态"""
        self.detection_running = running
        
        # 更新按钮状态 (old版本逻辑)
        self.start_detection_btn.setEnabled(not running)
        self.pause_detection_btn.setEnabled(running)
        self.stop_detection_btn.setEnabled(running)


class NativeMainDetectionView(QWidget):
    """
    原生主检测视图 - 完全还原old版本三栏式布局
    使用现有重构后的文件和功能模块
    采用高内聚、低耦合的设计原则
    """
    
    # 页面导航信号 (old版本信号)
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)
    navigate_to_report = Signal()
    
    # 状态更新信号
    status_updated = Signal(str, str)
    file_loaded = Signal(str)
    detection_progress = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 集成重构后的控制器和服务 (低耦合)
        self.controller = None
        self.search_service = None
        self.status_service = None
        self.file_service = None
        
        if HAS_REFACTORED_MODULES:
            try:
                self.controller = MainWindowController()
                self.search_service = SearchService()
                self.status_service = StatusService()
                self.file_service = FileService()
                self.logger.info("✅ 重构后的服务模块集成成功")
            except Exception as e:
                self.logger.warning(f"服务模块集成失败: {e}")
        
        # UI组件引用 (高内聚组件)
        self.left_panel = None
        self.center_panel = None
        self.right_panel = None
        self.toolbar = None
        
        # 数据状态
        self.current_hole_collection = None
        self.selected_hole = None
        self.detection_running = False
        
        # 扇形协调器 - 提前初始化
        self.coordinator = None
        if HAS_REFACTORED_MODULES:
            try:
                self.coordinator = PanoramaSectorCoordinator()
                self.logger.info("✅ 扇形协调器预初始化成功")
            except Exception as e:
                self.logger.error(f"扇形协调器预初始化失败: {e}")
        
        # 模拟控制器
        self.simulation_controller = None
        
        # 设置UI
        self.setup_ui()
        self.setup_connections()
        self.initialize_components()
        
    def setup_ui(self):
        """设置UI布局 - 完全还原old版本三栏式布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 1. 工具栏 (old版本顶部工具栏)
        self.toolbar = self._create_native_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 2. 主内容区域 - 三栏分割器布局 (old版本核心结构)
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：信息面板 (380px固定宽度)
        self.left_panel = NativeLeftInfoPanel()
        content_splitter.addWidget(self.left_panel)
        
        # 中间：可视化面板 (主要伸缩区域)
        self.center_panel = NativeCenterVisualizationPanel()
        content_splitter.addWidget(self.center_panel)
        
        # 右侧：操作面板 (350px最大宽度)
        self.right_panel = NativeRightOperationsPanel()
        content_splitter.addWidget(self.right_panel)
        
        # 设置分割器比例 (old版本精确比例: 380, 700, 280)
        content_splitter.setSizes([380, 700, 280])
        
        # 设置拖动策略 (old版本设置)
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setStretchFactor(0, 0)  # 左侧固定
        content_splitter.setStretchFactor(1, 1)  # 中间主要伸缩
        content_splitter.setStretchFactor(2, 0)  # 右侧固定
        
        # 禁用左侧分割线拖动 (old版本设置)
        content_splitter.handle(1).setEnabled(False)
        
        main_layout.addWidget(content_splitter)

    def _create_native_toolbar(self):
        """创建原生工具栏 - old版本样式"""
        if HAS_REFACTORED_MODULES:
            try:
                # 使用重构后的ToolbarComponent (低耦合集成)
                toolbar = ToolbarComponent()
                self.logger.info("✅ 使用重构后的ToolbarComponent")
                return toolbar
            except Exception as e:
                self.logger.warning(f"ToolbarComponent创建失败: {e}")
        
        # 备用工具栏实现 - 创建带有信号的自定义QFrame
        from PySide6.QtCore import Signal
        
        class BackupToolbar(QFrame):
            product_selection_requested = Signal()
            search_requested = Signal(str)
            
            def __init__(self):
                super().__init__()
                self.setFrameStyle(QFrame.StyledPanel)
                self.setMaximumHeight(70)
                
                layout = QHBoxLayout(self)
                
                # 产品选择按钮
                product_btn = QPushButton("产品型号选择")
                product_btn.setMinimumSize(140, 45)
                product_btn.clicked.connect(self.product_selection_requested.emit)
                layout.addWidget(product_btn)
                
                layout.addSpacing(20)
                
                # 搜索区域
                layout.addWidget(QLabel("搜索:"))
                self.search_input = QLineEdit()
                self.search_input.setPlaceholderText("输入孔位ID...")
                self.search_input.setMinimumSize(220, 35)
                layout.addWidget(self.search_input)
                
                search_btn = QPushButton("搜索")
                search_btn.setMinimumSize(70, 35)
                search_btn.clicked.connect(self._on_search_clicked)
                layout.addWidget(search_btn)
                
                layout.addSpacing(20)
                
                # 视图控制
                layout.addWidget(QLabel("视图:"))
                view_combo = QComboBox()
                view_combo.addItems(["全部孔位", "待检孔位", "合格孔位", "异常孔位"])
                view_combo.setMinimumHeight(35)
                layout.addWidget(view_combo)
                
                layout.addStretch()
            
            def _on_search_clicked(self):
                query = self.search_input.text().strip()
                self.search_requested.emit(query)
        
        toolbar = BackupToolbar()
        return toolbar

    def setup_connections(self):
        """设置信号连接 - 高内聚组件间通信"""
        # 左侧面板信号连接
        if self.left_panel:
            self.left_panel.hole_info_updated.connect(self._on_hole_info_updated)
            
            # 连接全景图扇形点击信号
            if hasattr(self.left_panel, 'sidebar_panorama'):
                if hasattr(self.left_panel.sidebar_panorama, 'sector_clicked'):
                    self.left_panel.sidebar_panorama.sector_clicked.connect(self._on_panorama_sector_clicked)
        
        # 中间面板信号连接
        if self.center_panel:
            self.center_panel.hole_selected.connect(self._on_hole_selected)
            self.center_panel.view_mode_changed.connect(self._on_view_mode_changed)
        
        # 右侧面板信号连接
        if self.right_panel:
            self.right_panel.start_detection.connect(self._on_start_detection)
            self.right_panel.pause_detection.connect(self._on_pause_detection)
            self.right_panel.stop_detection.connect(self._on_stop_detection)
            # 模拟控制信号连接
            self.right_panel.start_simulation.connect(self._on_start_simulation)
            self.right_panel.pause_simulation.connect(self._on_pause_simulation)
            self.right_panel.stop_simulation.connect(self._on_stop_simulation)
            self.right_panel.file_operation_requested.connect(self._on_file_operation)
        
        # 重构后服务信号连接 (低耦合集成)
        if self.search_service:
            self.search_service.search_completed.connect(self._on_search_completed)
        
        if self.status_service:
            self.status_service.status_updated.connect(self._on_status_updated)

    def initialize_components(self):
        """初始化组件状态"""
        self.logger.info("🚀 原生主检测视图初始化完成")
        
        # 初始化左侧面板数据
        if self.left_panel:
            self.left_panel.update_progress_display()
        
        # 初始化控制器
        if self.controller:
            try:
                self.controller.initialize()
            except Exception as e:
                self.logger.warning(f"控制器初始化失败: {e}")
                
        # 完成扇形协调器的设置（协调器已在__init__中创建）
        if self.coordinator:
            try:
                # 设置图形视图
                if hasattr(self.center_panel, 'graphics_view'):
                    self.coordinator.set_graphics_view(self.center_panel.graphics_view)
                
                # 设置全景组件
                if hasattr(self.left_panel, 'sidebar_panorama'):
                    self.coordinator.set_panorama_widget(self.left_panel.sidebar_panorama)
                    
                # 连接信号（coordinator内部会处理panorama的信号）
                self.coordinator.sector_stats_updated.connect(self._on_sector_stats_updated)
                
                self.logger.info("✅ 扇形协调器设置完成")
            except Exception as e:
                self.logger.error(f"扇形协调器设置失败: {e}")
        
        # 初始化模拟控制器
        if HAS_REFACTORED_MODULES:
            try:
                self.simulation_controller = SimulationController()
                
                # 设置图形视图
                if hasattr(self.center_panel, 'graphics_view'):
                    self.simulation_controller.set_graphics_view(self.center_panel.graphics_view)
                
                # 设置全景组件
                if hasattr(self.left_panel, 'sidebar_panorama'):
                    self.simulation_controller.set_panorama_widget(self.left_panel.sidebar_panorama)
                
                # 设置扇形分配管理器（如果协调器有的话）
                if self.coordinator and hasattr(self.coordinator, 'sector_assignment_manager'):
                    self.simulation_controller.set_sector_assignment_manager(
                        self.coordinator.sector_assignment_manager
                    )
                
                # 连接模拟控制器信号
                self.simulation_controller.simulation_progress.connect(self._on_simulation_progress)
                self.simulation_controller.hole_status_updated.connect(self._on_hole_status_updated)
                self.simulation_controller.simulation_completed.connect(self._on_simulation_completed)
                self.simulation_controller.simulation_started.connect(self._on_simulation_started)
                self.simulation_controller.simulation_paused.connect(self._on_simulation_paused)
                self.simulation_controller.simulation_stopped.connect(self._on_simulation_stopped)
                
                self.logger.info("✅ 模拟控制器初始化成功")
            except Exception as e:
                self.logger.error(f"模拟控制器初始化失败: {e}")

    # === 事件处理方法 (高内聚逻辑) ===
    
    def _on_hole_selected(self, hole_id):
        """处理孔位选择事件"""
        self.logger.info(f"🎯 选中孔位: {hole_id}")
        
        # 更新左侧面板孔位信息
        hole_data = {
            'id': hole_id,
            'position': f"({100}, {200})",  # 示例坐标
            'status': '待检',
            'description': '正常孔位'
        }
        
        if self.left_panel:
            self.left_panel.update_hole_info(hole_data)

    def _on_view_mode_changed(self, mode):
        """处理视图模式变化"""
        self.logger.info(f"🔄 视图模式变化: {mode}")
        
        # 中间面板已经处理了视图切换，这里不需要额外操作
        if mode == "macro":
            self.logger.info("🌍 切换到宏观全景视图")
        else:  # micro
            self.logger.info("🔍 切换到微观扇形视图")

    
    def _on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击"""
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        # 安全获取扇形值，处理字符串和枚举两种情况
        sector_str = sector.value if hasattr(sector, 'value') else str(sector)
        self.logger.info(f"🎯 全景图扇形点击: {sector_str}")
        
        # 使用协调器处理扇形点击
        if self.coordinator:
            self.coordinator._on_panorama_sector_clicked(sector)
            
            # 获取当前扇形的孔位
            holes = self.coordinator.get_current_sector_holes()
            
            if holes:
                # 创建新的HoleCollection只包含该扇形的孔位
                from src.core_business.models.hole_data import HoleCollection
                filtered_dict = {hole.hole_id: hole for hole in holes}
                filtered_collection = HoleCollection(filtered_dict)
                
                # 加载到中间视图
                if self.center_panel and hasattr(self.center_panel, 'graphics_view'):
                    if hasattr(self.center_panel.graphics_view, 'load_holes'):
                        self.center_panel.graphics_view.load_holes(filtered_collection)
                        sector_str = sector.value if hasattr(sector, 'value') else str(sector)
                        self.logger.info(f"✅ 中间视图已加载扇形 {sector_str} 的 {len(holes)} 个孔位")
                        
                        # 让graphics_view的内置自适应机制处理，避免额外的fitInView调用
                        # 这样可以防止视图大小的反复变化
                            
            # 更新选中扇形信息
            if self.left_panel and hasattr(self.left_panel, 'update_selected_sector'):
                self.left_panel.update_selected_sector(sector)
    
    def _filter_holes_by_sector(self, hole_collection, sector):
        """根据扇形过滤孔位"""
        try:
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            if not hole_collection:
                return []
            
            # 获取孔位列表
            holes_list = []
            if hasattr(hole_collection, 'holes'):
                if hasattr(hole_collection.holes, 'values'):
                    holes_list = list(hole_collection.holes.values())
                else:
                    holes_list = list(hole_collection.holes)
            
            if not holes_list:
                return []
            
            # 计算数据中心点
            min_x = min(hole.center_x for hole in holes_list)
            max_x = max(hole.center_x for hole in holes_list)
            min_y = min(hole.center_y for hole in holes_list)
            max_y = max(hole.center_y for hole in holes_list)
            
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # 根据扇形过滤孔位
            filtered = []
            for hole in holes_list:
                # 使用SectorQuadrant的from_position方法判断孔位所属扇形
                hole_sector = SectorQuadrant.from_position(
                    hole.center_x, hole.center_y, center_x, center_y
                )
                if hole_sector == sector:
                    filtered.append(hole)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"过滤扇形孔位失败: {e}")
            return []
    
    def _get_center_scene(self):
        """安全获取中间视图的scene"""
        if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
            if hasattr(self.center_panel.graphics_view, 'scene'):
                return self.center_panel.graphics_view.scene
            else:
                try:
                    return self.center_panel.graphics_view.scene()
                except:
                    return None
        return None

    def _on_start_detection(self):
        """处理开始检测"""
        self.logger.info("🚀 开始检测")
        self.detection_running = True
        
        # 更新右侧面板状态
        if self.right_panel:
            self.right_panel.update_detection_state(running=True)
        
        # 集成重构后的检测服务
        if self.controller and hasattr(self.controller, 'start_detection'):
            try:
                self.controller.start_detection()
            except Exception as e:
                self.logger.error(f"检测启动失败: {e}")

    def _on_pause_detection(self):
        """处理暂停检测"""
        self.logger.info("⏸️ 暂停检测")

    def _on_stop_detection(self):
        """处理停止检测"""
        self.logger.info("⏹️ 停止检测")
        self.detection_running = False
        
        # 更新右侧面板状态
        if self.right_panel:
            self.right_panel.update_detection_state(running=False)
    
    def _on_start_simulation(self):
        """处理开始模拟"""
        self.logger.info("🚀 开始模拟检测")
        if self.simulation_controller and self.current_hole_collection:
            # 加载孔位数据到模拟控制器
            self.simulation_controller.load_hole_collection(self.current_hole_collection)
            # 开始模拟
            self.simulation_controller.start_simulation()
        else:
            self.logger.warning("模拟控制器未初始化或无孔位数据")
    
    def _on_pause_simulation(self):
        """处理暂停模拟"""
        self.logger.info("⏸️ 暂停模拟")
        if self.simulation_controller:
            self.simulation_controller.pause_simulation()
    
    def _on_stop_simulation(self):
        """处理停止模拟"""
        self.logger.info("⏹️ 停止模拟")
        if self.simulation_controller:
            self.simulation_controller.stop_simulation()
    
    def _on_simulation_started(self):
        """处理模拟开始事件"""
        self.logger.info("模拟已开始")
        # 更新按钮状态
        if self.right_panel:
            self.right_panel.start_simulation_btn.setEnabled(False)
            self.right_panel.pause_simulation_btn.setEnabled(True)
            self.right_panel.stop_simulation_btn.setEnabled(True)
    
    def _on_simulation_paused(self):
        """处理模拟暂停事件"""
        self.logger.info("模拟已暂停")
        # 更新按钮状态
        if self.right_panel:
            self.right_panel.start_simulation_btn.setEnabled(True)
            self.right_panel.pause_simulation_btn.setEnabled(False)
    
    def _on_simulation_stopped(self):
        """处理模拟停止事件"""
        self.logger.info("模拟已停止")
        # 更新按钮状态
        if self.right_panel:
            self.right_panel.start_simulation_btn.setEnabled(True)
            self.right_panel.pause_simulation_btn.setEnabled(False)
            self.right_panel.stop_simulation_btn.setEnabled(False)
    
    def _on_simulation_progress(self, current, total):
        """处理模拟进度更新"""
        progress = int((current / total * 100) if total > 0 else 0)
        self.logger.info(f"模拟进度: {current}/{total} ({progress}%)")
        
        # 更新左侧面板进度
        if self.left_panel and hasattr(self.left_panel, 'update_progress_display'):
            # 构造进度数据
            progress_data = {
                'progress': progress,
                'completed': current,
                'total': total,
                'pending': total - current
            }
            self.left_panel.update_progress_display(progress_data)
    
    def _on_hole_status_updated(self, hole_id, status):
        """处理孔位状态更新"""
        self.logger.info(f"孔位状态更新: {hole_id} -> {status}")
        
        # 更新扇形统计信息
        if self.coordinator and self.coordinator.current_sector:
            # 获取当前扇形的孔位
            sector_holes = self.coordinator.get_current_sector_holes()
            if sector_holes:
                # 重新计算统计
                stats = self.coordinator._calculate_sector_stats(sector_holes)
                self._on_sector_stats_updated(stats)
        
        # 更新整体进度统计
        if self.current_hole_collection:
            stats_data = self._calculate_overall_stats()
            if self.left_panel and hasattr(self.left_panel, 'update_progress_display'):
                self.left_panel.update_progress_display(stats_data)
    
    def _on_simulation_completed(self):
        """处理模拟完成事件"""
        self.logger.info("🏁 模拟检测完成")
        # 更新按钮状态
        if self.right_panel:
            self.right_panel.start_simulation_btn.setEnabled(True)
            self.right_panel.pause_simulation_btn.setEnabled(False)
            self.right_panel.stop_simulation_btn.setEnabled(False)
    
    def _calculate_overall_stats(self):
        """计算整体统计数据"""
        if not self.current_hole_collection:
            return {}
        
        from src.core_business.models.hole_data import HoleStatus
        
        total = len(self.current_hole_collection.holes)
        qualified = 0
        defective = 0
        pending = 0
        blind = 0
        tie_rod = 0
        
        for hole in self.current_hole_collection.holes.values():
            # 统计状态
            if hole.status == HoleStatus.QUALIFIED:
                qualified += 1
            elif hole.status == HoleStatus.DEFECTIVE:
                defective += 1
            else:
                pending += 1
            
            # 统计类型
            if hasattr(hole, 'is_blind') and hole.is_blind:
                blind += 1
            if hasattr(hole, 'is_tie_rod') and hole.is_tie_rod:
                tie_rod += 1
        
        completed = qualified + defective
        progress = int((completed / total * 100) if total > 0 else 0)
        qualification_rate = int((qualified / completed * 100) if completed > 0 else 0)
        
        return {
            'total': total,
            'qualified': qualified,
            'unqualified': defective,
            'not_detected': pending,
            'completed': completed,
            'pending': pending,
            'progress': progress,
            'completion_rate': progress,
            'qualification_rate': qualification_rate,
            'blind': blind,
            'tie_rod': tie_rod
        }

    
    def load_hole_collection(self, hole_collection):
        """加载孔位数据到视图 - 支持CAP1000和其他DXF"""
        # 更新当前孔位集合
        self.current_hole_collection = hole_collection
        
        # 加载到协调器触发扇形分配
        if self.coordinator and hole_collection:
            self.coordinator.load_hole_collection(hole_collection)
            self.logger.info("✅ 数据已加载到协调器，扇形分配完成")
        
        # 清空初始提示文本
        if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
            try:
                # 获取scene - 兼容属性和方法两种方式，添加详细调试
                scene = None
                if hasattr(self.center_panel.graphics_view, 'scene'):
                    scene_attr = getattr(self.center_panel.graphics_view, 'scene')
                    self.logger.debug(f"scene_attr类型: {type(scene_attr)}, 值: {scene_attr}")
                    
                    if callable(scene_attr):
                        try:
                            scene = scene_attr()
                            self.logger.debug(f"调用scene()后获得: {type(scene)}")
                        except Exception as e:
                            self.logger.error(f"调用scene()失败: {e}")
                    else:
                        scene = scene_attr
                        self.logger.debug(f"直接使用scene属性: {type(scene)}")
                        
                if scene:
                    self.logger.debug(f"准备清空scene: {type(scene)}, hasattr(clear): {hasattr(scene, 'clear')}")
                    if hasattr(scene, 'clear') and callable(getattr(scene, 'clear')):
                        scene.clear()
                        self.logger.debug("scene.clear()执行成功")
                    else:
                        self.logger.warning(f"scene没有可调用的clear方法: {type(scene)}")
                
                        # 加载数据到中间面板（同时适用于扇形和全景视图）
                if hasattr(self.center_panel, 'load_hole_collection'):
                    self.center_panel.load_hole_collection(self.current_hole_collection)
                    self.logger.info("✅ 中间面板数据加载完成")
                
                # 延迟加载默认扇形，等待扇形分配完成
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, self._load_default_sector1)
                
                self.logger.info("✅ 中间视图准备显示默认扇形")
                    
            except Exception as e:
                self.logger.error(f"加载孔位数据失败: {e}")
    
    def _load_default_sector1(self):
        """加载默认的sector1区域到中间视图 - 增强版"""
        try:
            self.logger.info("🎯 开始加载默认sector1区域")
            
            # 导入所需的枚举
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            # 检查必要组件是否就绪
            if not self.coordinator:
                self.logger.warning("⚠️ 协调器未初始化，尝试延迟重试")
                # 延迟3秒重试
                from PySide6.QtCore import QTimer
                QTimer.singleShot(3000, self._load_default_sector1)
                return
            
            if not hasattr(self.coordinator, 'select_sector'):
                self.logger.error("❌ 协调器缺少select_sector方法")
                return
                
            # 检查孔位数据是否已加载
            if not self.current_hole_collection or len(self.current_hole_collection.holes) == 0:
                self.logger.warning("⚠️ 孔位数据未加载，无法加载默认sector1")
                return
            
            # 触发sector1区域选择
            self.coordinator.select_sector(SectorQuadrant.SECTOR_1)
            self.logger.info("✅ 已自动选择sector1区域")
            
            # 确保中间视图正确更新
            if self.center_panel and hasattr(self.center_panel, 'graphics_view'):
                    # 中间视图已通过load_hole_collection加载数据
                self.logger.info("✅ 中间视图已准备显示sector1区域")
                    
        except Exception as e:
            self.logger.error(f"❌ 加载默认sector1失败: {e}")
            import traceback
            traceback.print_exc()
                
        # 全景显示已集成到中间面板的宏观视图中
        
        # 更新状态统计
        if self.left_panel and self.current_hole_collection:
            # 计算整体统计
            overall_stats = self._calculate_overall_stats()
            
            # 更新状态统计显示
            self.left_panel.update_progress_display(overall_stats)
            
            # 同时更新扇形统计（如果有选中的扇形）
            if self.coordinator and self.coordinator.current_sector:
                sector_holes = self.coordinator.get_current_sector_holes()
                if sector_holes:
                    sector_stats = self.coordinator._calculate_sector_stats(sector_holes)
                    self._on_sector_stats_updated(sector_stats)
    
    def _draw_holes_to_scene(self, scene, hole_collection):
        """手动绘制孔位到场景"""
        from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPen, QBrush, QColor
        
        try:
            # 获取孔位列表
            holes_list = []
            if hasattr(hole_collection, 'holes'):
                if hasattr(hole_collection.holes, 'values'):
                    holes_list = list(hole_collection.holes.values())
                else:
                    holes_list = list(hole_collection.holes)
                    
            # 设置画笔和画刷
            pen = QPen(QColor(0, 100, 200), 2)
            brush = QBrush(QColor(200, 220, 255, 100))
            
            # 绘制每个孔位
            for hole in holes_list:
                x = hole.center_x
                y = hole.center_y
                radius = getattr(hole, 'radius', 5.0)
                
                # 创建圆形
                circle = QGraphicsEllipseItem(QRectF(x-radius, y-radius, 2*radius, 2*radius))
                circle.setPen(pen)
                circle.setBrush(brush)
                scene.addItem(circle)
                
                # 添加孔位编号
                if hasattr(hole, 'hole_id'):
                    text = QGraphicsTextItem(str(hole.hole_id))
                    text.setPos(x - 10, y - 10)
                    scene.addItem(text)
                    
            # 调整视图
            scene.setSceneRect(scene.itemsBoundingRect())
            if hasattr(self.center_panel.graphics_view, 'fitInView'):
                self.center_panel.graphics_view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
                
            self.logger.info(f"✅ 手动绘制了 {len(holes_list)} 个孔位")
            
        except Exception as e:
            self.logger.error(f"手动绘制孔位失败: {e}")

    def _on_file_operation(self, operation, params):
        """处理文件操作"""
        self.logger.info(f"📁 文件操作: {operation}")
        
        if operation == "load_product":
            self._show_product_selection()
        elif operation == "load_dxf":
            self._load_dxf_file()

    def _on_hole_info_updated(self, info):
        """处理孔位信息更新"""
        pass

    def _on_search_completed(self, query, results):
        """处理搜索完成"""
        pass

    def _on_status_updated(self, hole_id, status):
        """处理状态更新"""
        pass
    
    def update_detection_progress(self, progress):
        """更新检测进度 - 接收来自main_detection_page的进度更新"""
        if isinstance(progress, tuple) and len(progress) == 2:
            # 处理 (current, total) 格式
            current, total = progress
            progress_percent = int(current / total * 100) if total > 0 else 0
            self.logger.info(f"📊 进度更新: {current}/{total} = {progress_percent}%")
        else:
            # 处理百分比格式
            progress_percent = int(progress)
            self.logger.info(f"📊 进度更新: {progress_percent}%")
        
        # 更新左侧面板的进度显示
        if self.left_panel:
            # 获取当前统计数据
            stats_data = {
                'progress': progress_percent,
                'completion_rate': progress_percent,
                'qualification_rate': 99.5  # 模拟合格率
            }
            
            # 如果有hole_collection，获取真实统计数据
            if hasattr(self, 'center_panel') and hasattr(self.center_panel, 'graphics_view'):
                graphics_view = self.center_panel.graphics_view
                if hasattr(graphics_view, 'hole_collection'):
                    hole_collection = graphics_view.hole_collection
                    if hole_collection:
                        stats = hole_collection.get_statistics()
                        stats_data.update({
                            'total': stats.get('total', 0),
                            'qualified': stats.get('qualified', 0),
                            'unqualified': stats.get('unqualified', 0),
                            'not_detected': stats.get('not_detected', 0),
                            'blind': stats.get('blind', 0),
                            'tie_rod': stats.get('tie_rod', 0),
                            'completed': stats.get('qualified', 0) + stats.get('unqualified', 0),
                            'pending': stats.get('not_detected', 0)
                        })
            
            self.left_panel.update_progress_display(stats_data)
    
    def _on_hole_status_updated(self, hole_id, status):
        """处理孔位状态更新 - 确保左侧面板信息同步"""
        self.logger.debug(f"孔位状态更新: {hole_id} -> {status}")
        
        # 更新左侧面板信息
        if self.left_panel and hasattr(self.left_panel, 'update_hole_info'):
            try:
                # 获取孔位数据
                if self.current_hole_collection and hole_id in self.current_hole_collection.holes:
                    hole_data = self.current_hole_collection.holes[hole_id]
                    
                    # 构建信息字典
                    hole_info = {
                        'id': hole_id,
                        'position': f'({hole_data.center_x:.1f}, {hole_data.center_y:.1f})',
                        'status': str(status.value if hasattr(status, 'value') else status),
                        'description': '检测更新'
                    }
                    
                    # 更新左侧面板
                    self.left_panel.update_hole_info(hole_info)
                    self.logger.debug(f"✅ 左侧面板已更新孔位信息: {hole_id}")
                    
            except Exception as e:
                self.logger.warning(f"更新左侧面板失败: {e}")
    
    def _on_sector_stats_updated(self, stats):
        """处理扇形统计更新"""
        if self.left_panel:
            # 更新当前扇形标签
            if hasattr(self.left_panel, 'current_sector_label'):
                if self.coordinator and self.coordinator.current_sector:
                    self.left_panel.current_sector_label.setText(f"当前扇形: {self.coordinator.current_sector.value}")
                else:
                    self.left_panel.current_sector_label.setText("当前扇形: 未选择")
            
            # 更新扇形统计表格
            if hasattr(self.left_panel, 'update_sector_stats') and stats:
                self.left_panel.update_sector_stats(stats)
                self.logger.info(f"📊 扇形统计表格已更新")
            elif hasattr(self.left_panel, 'update_sector_stats_text'):
                # 向后兼容：如果还需要文本格式
                stats_text = self._format_sector_stats_text(stats)
                self.left_panel.update_sector_stats_text(stats_text)
                self.logger.info(f"📊 扇形统计文本已更新")
    
    def _format_sector_stats_text(self, stats):
        """格式化扇形统计为文本（向后兼容）"""
        if not stats:
            return "扇形统计信息加载中..."
        
        # 检查stats的格式
        if isinstance(stats, dict):
            # 如果是扇形->数量的映射
            if any(hasattr(k, 'value') for k in stats.keys()):
                stats_text = ""
                for sector, count in stats.items():
                    sector_name = sector.value if hasattr(sector, 'value') else str(sector)
                    stats_text += f"{sector_name}: {count} 个孔位\n"
                return stats_text.strip()
            # 如果是状态统计格式
            else:
                return (f"待检: {stats.get('pending', 0)}\n"
                       f"合格: {stats.get('qualified', 0)}\n"
                       f"异常: {stats.get('defective', 0)}\n"
                       f"盲孔: {stats.get('blind', 0)}\n"
                       f"拉杆: {stats.get('tie_rod', 0)}\n"
                       f"总计: {stats.get('total', 0)}")
        return "扇形统计信息格式错误"

    # === 业务逻辑方法 (集成重构后功能) ===
    
    def _show_product_selection(self):
        """显示产品选择对话框"""
        if HAS_REFACTORED_MODULES:
            try:
                dialog = ProductSelectionDialog(self)
                if dialog.exec():
                    product = dialog.selected_product
                    if product:
                        self.logger.info(f"✅ 选择产品: {product}")
                        
                        # 更新左侧面板文件信息
                        if self.left_panel:
                            self.left_panel.update_file_info(product_name=str(product))
                        
                        # 关键：加载产品数据到控制器和视图
                        if self.controller and hasattr(self.controller, 'load_product'):
                            try:
                                self.controller.load_product(product)
                                self.logger.info(f"✅ 产品数据加载请求已发送: {product}")
                            except Exception as e:
                                self.logger.error(f"加载产品数据失败: {e}")
                        else:
                            self.logger.warning("⚠️ 控制器不可用或没有load_product方法")
                            
            except Exception as e:
                self.logger.error(f"产品选择失败: {e}")

    def _load_dxf_file(self):
        """加载DXF文件"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DXF文件", "", "DXF Files (*.dxf)"
        )
        
        if file_path:
            self.logger.info(f"📁 加载DXF文件: {file_path}")
            if self.left_panel:
                self.left_panel.update_file_info(dxf_path=file_path)
            
            # 使用DXF加载服务加载文件
            try:
                from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
                loader = DXFLoaderService()
                hole_collection = loader.load_dxf_file(file_path)
                
                if hole_collection:
                    self.logger.info(f"✅ DXF加载成功: {len(hole_collection.holes)} 个孔位")
                    
                    # 加载到视图（内部会处理协调器和扇形分配）
                    self.load_hole_collection(hole_collection)
                    
                else:
                    self.logger.error("❌ DXF文件加载失败")
                    
            except Exception as e:
                self.logger.error(f"❌ 加载DXF文件出错: {e}")
                import traceback
                traceback.print_exc()
                
            self.file_loaded.emit(file_path)

    # === 公共接口方法 ===
    
    def get_current_state(self):
        """获取当前状态"""
        return {
            'detection_running': self.detection_running,
            'selected_hole': self.selected_hole,
            'has_data': self.current_hole_collection is not None
        }

    def update_hole_collection(self, hole_collection):
        """更新孔位集合"""
        self.current_hole_collection = hole_collection
        self.logger.info("📊 孔位集合已更新")

    def cleanup(self):
        """清理资源"""
        if self.controller:
            try:
                self.controller.cleanup()
            except:
                pass
        
        self.logger.info("🧹 原生主检测视图资源已清理")