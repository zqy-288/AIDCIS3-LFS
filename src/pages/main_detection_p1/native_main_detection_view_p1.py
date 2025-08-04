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
        
        # 设置固定宽度，增大以适应更大的全景预览
        self.setFixedWidth(400)  # 从380px增加到400px
        
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

        # 4. 全景预览组 - 设置为扩展以填充可用空间
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
        print(f"🏷️ [LeftPanel] 创建批次标签，初始文本: {self.current_batch_label.text()}")

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

    
    def _create_panorama_group(self, group_font):
        """创建全景预览组"""
        group = QGroupBox("全景预览")
        group.setFont(group_font)
        # 设置组框的最小高度，确保能容纳大的全景预览
        group.setMinimumHeight(400)  # 增加组框高度
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 使用具有用户缩放功能的完整全景图组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        self.sidebar_panorama = CompletePanoramaWidget()
        # 设置默认缩放比例为10%，解决圆形缩放不够的问题
        if hasattr(self.sidebar_panorama, 'set_user_hole_scale_factor'):
            self.sidebar_panorama.set_user_hole_scale_factor(0.1)
        # 设置固定大小，使全景预览更大更清晰
        self.sidebar_panorama.setFixedSize(380, 380)  # 增大到380x380的正方形，留出边距
        # 或者设置最小尺寸
        # self.sidebar_panorama.setMinimumSize(350, 350)
        # self.sidebar_panorama.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
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
        
        # 扇形统计表格 - 改为4列更紧凑的布局
        self.sector_stats_table = QTableWidget(2, 4)  # 2行4列（去掉盲孔和拉杆）
        self.sector_stats_table.setHorizontalHeaderLabels(["状态", "数量", "状态", "数量"])
        self.sector_stats_table.verticalHeader().hide()
        # 设置列宽比例 - 增加宽度以适应内容
        header = self.sector_stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.sector_stats_table.setColumnWidth(0, 90)  # 状态列（增加到90）
        self.sector_stats_table.setColumnWidth(1, 100)  # 数量列（增加到100，适应5位数）
        self.sector_stats_table.setColumnWidth(2, 90)  # 状态列（增加到90）
        self.sector_stats_table.setColumnWidth(3, 100)  # 数量列（增加到100）
        # 设置紧凑的行高
        self.sector_stats_table.verticalHeader().setDefaultSectionSize(24)  # 设置行高为24像素
        self.sector_stats_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 固定行高
        # 根据内容计算精确高度：header(24) + 2 rows(24*2) + borders(4)
        total_height = 24 + 24 * 2 + 4
        self.sector_stats_table.setFixedHeight(total_height)
        
        # 设置表格的整体背景色
        self.sector_stats_table.setAlternatingRowColors(False)  # 禁用交替行颜色
        from PySide6.QtGui import QPalette
        palette = self.sector_stats_table.palette()
        palette.setColor(QPalette.Base, QColor("#e8e8e8"))
        palette.setColor(QPalette.AlternateBase, QColor("#e8e8e8"))
        self.sector_stats_table.setPalette(palette)
        
        # 设置表格样式 - 确保背景色正确应用
        self.sector_stats_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #ddd;
                font-size: 11px;
                background-color: #e8e8e8;
                alternate-background-color: #e8e8e8;
            }
            QTableWidget::item {
                padding: 2px;
                text-align: center;
                background-color: #e8e8e8;
                color: #333;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #d0d0d0;
                color: #333;
            }
            QHeaderView::section {
                background-color: #d0d0d0;
                font-weight: bold;
                padding: 2px;
                border: 1px solid #bbb;
                font-size: 11px;
            }
        """)
        
        # 初始化表格行 - 4列布局（去掉盲孔和拉杆）
        status_labels = [
            ("待检", "0", "合格", "0"),
            ("异常", "0", "总计", "0")
        ]
        
        # 保存状态映射，用于更新
        self.status_cells = {
            "pending": (0, 1),     # 待检
            "qualified": (0, 3),   # 合格
            "defective": (1, 1),   # 异常
            "total": (1, 3)        # 总计（移到第二行）
        }
        
        for row, (label1, val1, label2, val2) in enumerate(status_labels):
            # 创建表格项
            item1 = QTableWidgetItem(label1)
            item2 = QTableWidgetItem(val1)
            item3 = QTableWidgetItem(label2)
            item4 = QTableWidgetItem(val2)
            
            # 设置每个单元格的背景色
            background_color = QColor("#e8e8e8")
            item1.setBackground(background_color)
            item2.setBackground(background_color)
            item3.setBackground(background_color)
            item4.setBackground(background_color)
            
            # 设置到表格
            self.sector_stats_table.setItem(row, 0, item1)
            self.sector_stats_table.setItem(row, 1, item2)
            self.sector_stats_table.setItem(row, 2, item3)
            self.sector_stats_table.setItem(row, 3, item4)
            
            # 设置总计为粗体
            if row == 1:  # 第二行（最后一行）
                font = QFont()
                font.setBold(True)
                self.sector_stats_table.item(row, 2).setFont(font)
                self.sector_stats_table.item(row, 3).setFont(font)
        
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
        print(f"📊 [LeftPanel] 更新进度条: {progress}% -> setValue({int(progress)})")
        
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
        
        # 注意：不要在这里更新扇形统计表格，它应该只显示当前扇形的数据

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

    
    def update_batch_info(self, batch_id: str):
        """更新批次信息"""
        if hasattr(self, 'current_batch_label'):
            self.current_batch_label.setText(f"检测批次: {batch_id}")
            print(f"📝 [LeftPanel] 批次标签已更新: {batch_id}")
            self.logger.info(f"批次信息已更新: {batch_id}")
    
    def update_selected_sector(self, sector):
        """更新选中的扇形信息"""
        if hasattr(self, 'current_sector_label'):
            sector_name = sector.value if hasattr(sector, 'value') else str(sector)
            self.current_sector_label.setText(f"当前扇形: {sector_name}")
    
    def update_sector_stats(self, stats_data):
        """更新扇形统计表格 - 适配4列布局"""
        self.logger.info(f"📊 update_sector_stats called with data: {stats_data}")
        if hasattr(self, 'sector_stats_table') and hasattr(self, 'status_cells') and stats_data:
            # 更新表格数据
            for status, (row, col) in self.status_cells.items():
                if status in stats_data:
                    value = stats_data.get(status, 0)
                    # 确保单元格存在
                    if row < self.sector_stats_table.rowCount() and col < self.sector_stats_table.columnCount():
                        item = self.sector_stats_table.item(row, col)
                        if item:
                            item.setText(str(value))
                        else:
                            item = QTableWidgetItem(str(value))
                            item.setBackground(QColor("#e8e8e8"))
                            self.sector_stats_table.setItem(row, col, item)
                            
            # 使用提供的total值，如果有的话
            if 'total' in stats_data:
                row, col = self.status_cells['total']
                if row < self.sector_stats_table.rowCount() and col < self.sector_stats_table.columnCount():
                    item = self.sector_stats_table.item(row, col)
                    if item:
                        item.setText(str(stats_data['total']))
                    else:
                        item = QTableWidgetItem(str(stats_data['total']))
                        item.setBackground(QColor("#e8e8e8"))
                        self.sector_stats_table.setItem(row, col, item)
            else:
                # 计算总计（如果没有提供）- 只统计待检、合格、异常
                total = sum(stats_data.get(k, 0) for k in ['pending', 'qualified', 'defective'])
                row, col = self.status_cells['total']
                if row < self.sector_stats_table.rowCount() and col < self.sector_stats_table.columnCount():
                    item = self.sector_stats_table.item(row, col)
                    if item:
                        item.setText(str(total))
                    else:
                        item = QTableWidgetItem(str(total))
                        item.setBackground(QColor("#e8e8e8"))
                        self.sector_stats_table.setItem(row, col, item)


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
        
        # 创建按钮组确保单选
        from PySide6.QtWidgets import QButtonGroup
        self.view_button_group = QButtonGroup()
        
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
        
        # 添加到按钮组
        self.view_button_group.addButton(self.macro_view_btn)
        self.view_button_group.addButton(self.micro_view_btn)
        
        layout.addWidget(self.macro_view_btn)
        layout.addWidget(self.micro_view_btn)
        
        # 添加分隔空间
        layout.addSpacing(12)
        
        # 添加颜色图例
        try:
            from .components.color_legend_widget import CompactColorLegendWidget
            legend_widget = CompactColorLegendWidget()
            legend_widget.setStyleSheet("""
                CompactColorLegendWidget {
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    padding: 2px;
                }
            """)
            layout.addWidget(legend_widget)
            self.logger.info("✅ 添加颜色图例成功")
        except Exception as e:
            self.logger.warning(f"⚠️ 添加颜色图例失败: {e}")
        
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
    file_operation_requested = Signal(str, dict)  # 文件操作信号
    # 导航信号
    realtime_detection_requested = Signal()  # 跳转到P2页面
    history_statistics_requested = Signal()  # 跳转到P3页面
    report_generation_requested = Signal()   # 跳转到P4页面
    
    # 页面导航信号 - 添加缺失的信号
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str)  
    navigate_to_report = Signal()
    
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

        # 3. 页面导航组 (替换文件操作组)
        navigation_group = self._create_navigation_group(group_title_font, button_font)
        layout.addWidget(navigation_group)

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

    def _create_navigation_group(self, group_font, button_font):
        """创建页面导航组"""
        group = QGroupBox("页面导航")
        group.setFont(group_font)
        layout = QVBoxLayout(group)

        # 导航按钮
        self.realtime_btn = QPushButton("实时检测")
        self.realtime_btn.setMinimumHeight(40)
        self.realtime_btn.setFont(button_font)
        self.realtime_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; border-radius: 5px; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:pressed { background-color: #0D47A1; }"
        )

        self.history_btn = QPushButton("历史统计")
        self.history_btn.setMinimumHeight(40)
        self.history_btn.setFont(button_font)
        self.history_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; }"
            "QPushButton:hover { background-color: #388E3C; }"
            "QPushButton:pressed { background-color: #1B5E20; }"
        )

        self.report_btn = QPushButton("报告生成")
        self.report_btn.setMinimumHeight(40)
        self.report_btn.setFont(button_font)
        self.report_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; border-radius: 5px; }"
            "QPushButton:hover { background-color: #F57C00; }"
            "QPushButton:pressed { background-color: #E65100; }"
        )

        layout.addWidget(self.realtime_btn)
        layout.addWidget(self.history_btn)
        layout.addWidget(self.report_btn)

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

        # 导航信号
        self.realtime_btn.clicked.connect(self.realtime_detection_requested.emit)
        self.history_btn.clicked.connect(self.history_statistics_requested.emit)
        self.report_btn.clicked.connect(self.report_generation_requested.emit)
        
        # 连接导航请求信号到导航信号
        self.realtime_detection_requested.connect(lambda: self.navigate_to_realtime.emit(""))
        self.history_statistics_requested.connect(lambda: self.navigate_to_history.emit(""))
        self.report_generation_requested.connect(self.navigate_to_report.emit)

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
        self._initial_sector_loaded = False  # 防止重复加载初始扇形
        
        # 扇形协调器 - 提前初始化
        self.coordinator = None
        if HAS_REFACTORED_MODULES:
            try:
                self.coordinator = PanoramaSectorCoordinator()
                self.logger.info("✅ 扇形协调器预初始化成功")
                
                # 设置默认扇形为sector_1
                from src.core_business.graphics.sector_types import SectorQuadrant
                self.coordinator.current_sector = SectorQuadrant.SECTOR_1
                self.logger.info("✅ 设置默认扇形为sector_1")
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
            
            # 页面导航信号连接 - 重要！连接右侧面板的导航信号到主视图信号
            self.right_panel.navigate_to_realtime.connect(self.navigate_to_realtime.emit)
            self.right_panel.navigate_to_history.connect(self.navigate_to_history.emit)  
            self.right_panel.navigate_to_report.connect(self.navigate_to_report.emit)
        
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
                # 连接扇形聚焦信号以更新统计
                self.simulation_controller.sector_focused.connect(self._on_simulation_sector_focused)
                
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
        self.logger.info(f"🔄 视图模式切换到: {mode}")
        
        if not self.center_panel or not hasattr(self.center_panel, 'graphics_view'):
            return
            
        graphics_view = self.center_panel.graphics_view
        
        if mode == "macro":
            self.logger.info("🌍 切换到宏观全景视图")
            # 宏观视图显示所有孔位
            graphics_view.current_view_mode = 'macro'
            graphics_view.disable_auto_fit = False  # 宏观视图允许自动适配
            graphics_view.show_all_holes()
        else:  # micro
            self.logger.info("🔍 切换到微观扇形视图")
            # 微观视图显示当前扇形
            graphics_view.current_view_mode = 'micro'
            graphics_view.disable_auto_fit = True  # 微观视图禁止自动适配
            
            if self.coordinator and self.coordinator.current_sector:
                self._show_sector_in_view(self.coordinator.current_sector)
            else:
                # 如果没有选中扇形，默认选择sector1
                self.logger.info("📍 没有选中扇形，默认选择sector1")
                from src.core_business.graphics.sector_types import SectorQuadrant
                if self.coordinator and hasattr(self.coordinator, 'select_sector'):
                    self.coordinator.select_sector(SectorQuadrant.SECTOR_1)

    
    def _on_panorama_sector_clicked(self, sector):
        """处理全景图扇形点击"""
        from src.core_business.graphics.sector_types import SectorQuadrant
        
        # 安全获取扇形值，处理字符串和枚举两种情况
        sector_str = sector.value if hasattr(sector, 'value') else str(sector)
        self.logger.info(f"🎯 全景图扇形点击: {sector_str}")
        
        # 使用协调器处理扇形点击
        if self.coordinator:
            self.coordinator._on_panorama_sector_clicked(sector)
        
        # 自动切换到微观视图模式
        if self.center_panel:
            # 更新按钮状态
            self.center_panel.micro_view_btn.setChecked(True)
            self.center_panel.macro_view_btn.setChecked(False)
            self.center_panel.current_view_mode = "micro"
            
            # 触发视图模式变化
            self.center_panel.view_mode_changed.emit("micro")
            
        # 显示选中的扇形
        self._show_sector_in_view(sector)
            
        # 更新选中扇形信息
        if self.left_panel and hasattr(self.left_panel, 'update_selected_sector'):
            self.left_panel.update_selected_sector(sector)
    
    def _show_sector_in_view(self, sector):
        """在视图中显示指定扇形（不重新加载数据）"""
        if not self.coordinator:
            self.logger.warning("❌ 协调器未初始化")
            return
            
        # 获取当前扇形的孔位
        holes = self.coordinator.get_current_sector_holes()
        if not holes:
            self.logger.warning(f"❌ 扇形 {sector} 没有孔位数据")
            return
        
        self.logger.info(f"📊 扇形 {sector} 包含 {len(holes)} 个孔位")
            
        # 使用场景过滤而非重新加载
        if self.center_panel and hasattr(self.center_panel, 'graphics_view'):
            graphics_view = self.center_panel.graphics_view
            
            # 确保视图处于微观模式
            graphics_view.current_view_mode = 'micro'
            graphics_view.disable_auto_fit = True
            
            # 获取场景
            scene = None
            if hasattr(graphics_view, 'scene'):
                scene = graphics_view.scene
            elif hasattr(graphics_view, 'scene') and callable(graphics_view.scene):
                scene = graphics_view.scene()
                
            if scene:
                # 获取扇形孔位ID集合
                sector_hole_ids = {hole.hole_id for hole in holes}
                self.logger.info(f"📋 扇形孔位ID数量: {len(sector_hole_ids)}")
                
                # 获取场景中的所有项
                all_items = scene.items()
                self.logger.info(f"🎯 场景中总项数: {len(all_items)}")
                
                # 过滤显示
                visible_items = []
                hidden_count = 0
                for item in all_items:
                    hole_id = item.data(0)  # Qt.UserRole = 0
                    if hole_id:
                        is_visible = hole_id in sector_hole_ids
                        item.setVisible(is_visible)
                        if is_visible:
                            visible_items.append(item)
                        else:
                            hidden_count += 1
                
                # 适配视图到可见项
                if visible_items:
                    # 使用sceneBoundingRect获取准确的场景坐标
                    scene_rects = [item.sceneBoundingRect() for item in visible_items]
                    
                    if scene_rects:
                        # 计算所有可见项的边界
                        min_x = min(rect.left() for rect in scene_rects)
                        max_x = max(rect.right() for rect in scene_rects)
                        min_y = min(rect.top() for rect in scene_rects)
                        max_y = max(rect.bottom() for rect in scene_rects)
                        
                        from PySide6.QtCore import QRectF
                        # 增加边距以获得更合适的显示比例
                        margin = 200  # 增加边距从50到200
                        bounding_rect = QRectF(
                            min_x - margin, 
                            min_y - margin, 
                            max_x - min_x + 2 * margin, 
                            max_y - min_y + 2 * margin
                        )
                        
                        # 完全禁用自动适配，避免任何重复缩放
                        graphics_view.disable_auto_fit = True
                        
                        # 停止所有待处理的定时器
                        if hasattr(graphics_view, '_fit_timer') and graphics_view._fit_timer:
                            graphics_view._fit_timer.stop()
                            graphics_view._fit_pending = False
                        
                        # 清除任何可能的定时器
                        if hasattr(graphics_view, '_auto_fit_timer'):
                            graphics_view._auto_fit_timer.stop()
                        
                        # 设置缩放锁
                        graphics_view._is_fitting = True
                        
                        # 适配视图到扇形区域（只调用一次）
                        graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
                        
                        # 设置标志，告诉 set_micro_view_scale 跳过额外缩放
                        graphics_view._fitted_to_sector = True
                        
                        self.logger.info(f"✅ 视图已适配到扇形区域，边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")
                        
                        # 延迟更长时间恢复状态，或者在微观模式下保持禁用
                        # 只有在切换到宏观视图时才恢复
                        QTimer.singleShot(1000, lambda: setattr(graphics_view, '_is_fitting', False))
                        # 注意：不恢复 disable_auto_fit，让它在微观模式下保持 True
                
                self.logger.info(f"✅ 视图已过滤：显示 {len(visible_items)} 个，隐藏 {hidden_count} 个")
                self.logger.info(f"✅ 扇形 {sector.value if hasattr(sector, 'value') else str(sector)} 视图更新完成")
                
                # 调试验证：检查第一个可见项和第一个隐藏项
                if visible_items:
                    first_visible = visible_items[0]
                    self.logger.debug(f"🔍 第一个可见项: ID={first_visible.data(0)}, 位置=({first_visible.x()}, {first_visible.y()}), isVisible={first_visible.isVisible()}")
                
                # 验证过滤效果
                total_after_filter = sum(1 for item in scene.items() if item.isVisible())
                self.logger.info(f"🎯 过滤验证：场景中实际可见项数={total_after_filter}, 预期={len(visible_items)}")
                
                # 强制刷新场景
                scene.update()
                graphics_view.viewport().update()
    
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
            
            # 通知父页面更新批次状态为暂停
            if hasattr(self.parent(), 'controller') and hasattr(self.parent().controller, 'current_batch_id'):
                batch_id = self.parent().controller.current_batch_id
                if batch_id:
                    try:
                        # 获取当前检测状态
                        detection_state = {
                            'current_index': getattr(self.simulation_controller, 'current_index', 0),
                            'total_holes': getattr(self.simulation_controller, 'total_holes_processed', 0),
                            'pause_time': __import__('datetime').datetime.now().isoformat()
                        }
                        self.parent().controller.batch_service.pause_batch(batch_id, detection_state)
                        print(f"⏸️ [NativeView] 批次已暂停: {batch_id}")
                    except Exception as e:
                        print(f"❌ [NativeView] 暂停批次失败: {e}")
    
    def _on_stop_simulation(self):
        """处理停止模拟"""
        self.logger.info("⏹️ 停止模拟")
        if self.simulation_controller:
            self.simulation_controller.stop_simulation()
            
            # 通知父页面更新批次状态为终止，并清除当前批次ID
            if hasattr(self.parent(), 'controller') and hasattr(self.parent().controller, 'current_batch_id'):
                batch_id = self.parent().controller.current_batch_id
                if batch_id:
                    try:
                        self.parent().controller.batch_service.terminate_batch(batch_id)
                        print(f"🛑 [NativeView] 批次已终止: {batch_id}")
                        # 清除当前批次ID，下次开始时会创建新批次
                        self.parent().controller.current_batch_id = None
                    except Exception as e:
                        print(f"❌ [NativeView] 终止批次失败: {e}")
    
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
        self.logger.info(f"模拟进度: {current}/{total} 个孔位 ({progress}%)")
        
        # 更新左侧面板进度
        if self.left_panel and hasattr(self.left_panel, 'update_progress_display'):
            # 重新计算完整的统计数据，包括状态统计
            if self.current_hole_collection:
                stats_data = self._calculate_overall_stats()
                # 更新进度相关字段
                stats_data['progress'] = progress
                stats_data['completed'] = current
                stats_data['pending'] = total - current
                self.left_panel.update_progress_display(stats_data)
            else:
                # 如果没有孔位集合，使用最小数据
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
            'defective': defective,  # 添加这个键用于扇形统计表格
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
        
        # 重置初始扇形加载标志，确保新文件可以加载默认扇形
        self._initial_sector_loaded = False
        
        # 1. 首先强制设置为微观视图模式（在加载数据之前）
        if self.center_panel:
            self.center_panel.micro_view_btn.setChecked(True)
            self.center_panel.macro_view_btn.setChecked(False)
            self.center_panel.current_view_mode = "micro"
            self.logger.info("✅ 强制设置为微观视图模式")
            
            # 确保 graphics_view 也处于微观模式
            if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
                graphics_view = self.center_panel.graphics_view
                graphics_view.current_view_mode = 'micro'
                graphics_view.disable_auto_fit = True
                
                # 停止所有可能的适配定时器
                if hasattr(graphics_view, '_fit_timer'):
                    graphics_view._fit_timer.stop()
                    graphics_view._fit_pending = False
                self.logger.info("✅ graphics_view 已设置为微观模式，禁用自动适配")
        
        # 2. 加载到协调器触发扇形分配
        if self.coordinator and hole_collection:
            self.coordinator.load_hole_collection(hole_collection)
            self.logger.info("✅ 数据已加载到协调器，扇形分配完成")
        
        # 更新状态统计显示
        if self.left_panel and hole_collection:
            overall_stats = self._calculate_overall_stats()
            self.left_panel.update_progress_display(overall_stats)
            self.logger.info(f"✅ 状态统计已更新: 总数 {overall_stats.get('total', 0)}")
            
            # 如果有当前扇形，更新扇形统计
            if self.coordinator and self.coordinator.current_sector:
                sector_holes = self.coordinator.get_current_sector_holes()
                if sector_holes:
                    sector_stats = self.coordinator._calculate_sector_stats(sector_holes)
                    self.logger.info(f"📊 扇形统计数据: total={sector_stats.get('total', 0)}, "
                                   f"pending={sector_stats.get('pending', 0)}, "
                                   f"扇形孔位数={len(sector_holes)}")
                    if hasattr(self.left_panel, 'update_sector_stats'):
                        self.left_panel.update_sector_stats(sector_stats)
                        self.logger.info(f"✅ 扇形统计已更新: {self.coordinator.current_sector.value}")
        
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
                
                # 检查当前视图模式 - 默认应该是微观视图
                # 如果按钮状态还未初始化，默认使用微观视图
                is_micro_view = True  # 默认使用微观视图
                if self.center_panel and hasattr(self.center_panel, 'micro_view_btn'):
                    # 如果按钮已初始化，则使用按钮状态
                    is_micro_view = self.center_panel.micro_view_btn.isChecked()
                    # 但如果两个按钮都未选中（初始状态），强制使用微观视图
                    if (hasattr(self.center_panel, 'macro_view_btn') and 
                        not self.center_panel.macro_view_btn.isChecked() and 
                        not self.center_panel.micro_view_btn.isChecked()):
                        is_micro_view = True
                        # 同时更新按钮状态
                        self.center_panel.micro_view_btn.setChecked(True)
                        self.center_panel.macro_view_btn.setChecked(False)
                
                # 加载数据到中间面板的graphics_view
                if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
                    graphics_view = self.center_panel.graphics_view
                    
                    if is_micro_view:
                        # 微观视图模式：加载数据但不显示，等待扇形选择
                        self.logger.info("🔍 微观视图模式，加载数据但暂不显示")
                        if hasattr(graphics_view, 'load_holes'):
                            # 确保在微观视图模式下加载
                            graphics_view.current_view_mode = 'micro'
                            graphics_view.disable_auto_fit = True
                            
                            # 加载数据
                            graphics_view.load_holes(self.current_hole_collection)
                            self.logger.info("✅ 数据已加载到场景")
                            
                            # 立即隐藏所有项，等待扇形选择
                            if hasattr(graphics_view, 'scene') and callable(graphics_view.scene):
                                scene = graphics_view.scene()
                                if scene:
                                    for item in scene.items():
                                        item.setVisible(False)
                                    self.logger.info("✅ 已隐藏所有孔位，等待扇形选择")
                            
                            # 保持 disable_auto_fit = True，不要立即恢复
                            # 让它在扇形显示完成后再恢复
                    else:
                        # 宏观视图模式：正常加载并显示所有数据
                        self.logger.info("🌍 宏观视图模式，显示全部孔位")
                        if hasattr(graphics_view, 'load_holes'):
                            graphics_view.load_holes(self.current_hole_collection)
                            self.logger.info("✅ 中间面板graphics_view数据加载完成")
                            
                            # 确保数据加载后正确显示
                            if hasattr(graphics_view, 'fit_in_view_with_margin'):
                                graphics_view.fit_in_view_with_margin()
                                self.logger.info("✅ 视图已调整到合适大小")
                else:
                    self.logger.warning("⚠️ 中间面板没有 graphics_view 属性")
                
                # 5. 立即显示默认扇形（不延迟）
                if is_micro_view:
                    self.logger.info("🔍 准备加载默认扇形sector1")
                    # 使用与视图切换相同的逻辑
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self._on_view_mode_changed("micro"))
                    
            except Exception as e:
                self.logger.error(f"加载孔位数据失败: {e}")
    
    def _load_default_sector1(self):
        """加载默认的sector1区域到中间视图 - 增强版"""
        # 检查是否已经加载过
        if self._initial_sector_loaded:
            self.logger.info("✅ 初始扇形已加载，跳过重复加载")
            return
            
        try:
            self.logger.info("🎯 开始加载默认sector1区域")
            
            # 导入所需的枚举
            from src.core_business.graphics.sector_types import SectorQuadrant
            
            # 检查必要组件是否就绪
            if not self.coordinator:
                self.logger.warning("⚠️ 协调器未初始化，尝试延迟重试")
                # 延迟1秒重试（减少延迟时间）
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, self._load_default_sector1)
                return
            
            if not hasattr(self.coordinator, 'select_sector'):
                self.logger.error("❌ 协调器缺少select_sector方法")
                return
                
            # 检查孔位数据是否已加载
            if not self.current_hole_collection or len(self.current_hole_collection.holes) == 0:
                self.logger.warning("⚠️ 孔位数据未加载，无法加载默认sector1")
                return
            
            # 检查是否已经在显示 sector1，但即使已选中也需要显示
            if self.coordinator.current_sector == SectorQuadrant.SECTOR_1:
                self.logger.info("✅ sector1已选中，强制刷新显示")
                # 不要返回，继续执行显示逻辑
            
            # 确保中间面板按钮状态正确（微观视图）
            if self.center_panel:
                self.center_panel.micro_view_btn.setChecked(True)
                self.center_panel.macro_view_btn.setChecked(False)
                self.center_panel.current_view_mode = "micro"
                
                # 更新graphics_view的视图模式
                if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
                    graphics_view = self.center_panel.graphics_view
                    if hasattr(graphics_view, 'current_view_mode'):
                        graphics_view.current_view_mode = 'micro'
                        self.logger.info("✅ 已设置graphics_view为微观视图模式")
            
            # 选择sector1 - coordinator.select_sector 会自动触发视图更新
            self.coordinator.select_sector(SectorQuadrant.SECTOR_1)
            self.logger.info("✅ 已选择sector1区域")
            
            # 标记初始扇形已加载
            self._initial_sector_loaded = True
            
            # 强制触发扇形显示
            self._show_sector_in_view(SectorQuadrant.SECTOR_1)
            self.logger.info("✅ 已触发sector1显示")
                    
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
            if total > 0:
                # 使用浮点数计算，保留2位小数，最小显示0.01%
                progress_float = (current / total) * 100
                progress_percent = max(0.01, round(progress_float, 2)) if current > 0 else 0
                # 对于显示，如果小于1%但大于0，显示"<1%"
                if 0 < progress_percent < 1:
                    progress_display = "<1%"
                else:
                    progress_display = f"{progress_percent:.1f}%"
            else:
                progress_percent = 0
                progress_display = "0%"
            self.logger.info(f"📊 进度更新: {current}/{total} = {progress_display}")
            print(f"📊 [NativeView] 进度计算: {current}/{total} = {progress_float:.2f}% 显示为: {progress_display}")
        else:
            # 处理百分比格式
            progress_percent = float(progress)
            progress_display = f"{progress_percent:.1f}%"
            self.logger.info(f"📊 进度更新: {progress_display}")
        
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
        
        # 重新计算并更新状态统计
        if self.left_panel and self.current_hole_collection:
            overall_stats = self._calculate_overall_stats()
            self.left_panel.update_progress_display(overall_stats)
            self.logger.debug(f"✅ 状态统计已更新")
    
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
                self.logger.info(f"📊 准备更新扇形统计表格，数据: total={stats.get('total', 0)}, "
                               f"pending={stats.get('pending', 0)}, qualified={stats.get('qualified', 0)}")
                self.left_panel.update_sector_stats(stats)
                self.logger.info(f"📊 扇形统计表格已更新")
            elif hasattr(self.left_panel, 'update_sector_stats_text'):
                # 向后兼容：如果还需要文本格式
                stats_text = self._format_sector_stats_text(stats)
                self.left_panel.update_sector_stats_text(stats_text)
                self.logger.info(f"📊 扇形统计文本已更新")
    
    def _on_simulation_sector_focused(self, sector):
        """处理模拟过程中的扇形聚焦事件"""
        self.logger.info(f"🎯 模拟扇形聚焦: {sector.value if hasattr(sector, 'value') else str(sector)}")
        
        # 更新协调器的当前扇形
        if self.coordinator:
            # 使用协调器的set_current_sector方法，这会触发所有相关更新
            self.coordinator.set_current_sector(sector)
    
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