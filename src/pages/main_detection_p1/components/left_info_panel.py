"""
左侧信息面板组件 - 独立高内聚模块
负责显示检测进度、状态统计、孔位信息、文件信息、全景预览等
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class LeftInfoPanel(QWidget):
    """左侧信息面板 - 完全还原old版本 (高内聚组件)"""
    
    # 信号定义
    hole_info_updated = Signal(dict)
    sector_clicked = Signal(object)  # SectorQuadrant
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 组件状态
        self.current_hole_data = None
        self.detection_stats = {}
        self.sidebar_panorama = None
        
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

        # 5. 全景预览组 (old版本关键组件: 360×420px)
        self.panorama_group = self._create_panorama_group(group_font)
        layout.addWidget(self.panorama_group)

        # 6. 选中扇形组
        self.sector_stats_group = self._create_sector_stats_group(group_font)
        layout.addWidget(self.sector_stats_group)

        layout.addStretch()

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
        """创建全景预览组 - old版本关键组件 (360×420px)"""
        group = QGroupBox("全景预览")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建占位符，等待外部设置panorama widget
        placeholder = QLabel("全景图组件\n加载中...")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        placeholder.setFixedSize(360, 420)  # 保持old版本尺寸
        layout.addWidget(placeholder)
        
        self._panorama_placeholder = placeholder

        return group

    def _create_sector_stats_group(self, group_font):
        """创建选中扇形组"""
        group = QGroupBox("选中扇形")
        group.setFont(group_font)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(5, 5, 5, 5)

        # 扇形统计信息标签 (old版本样式)
        self.sector_stats_label = QLabel("扇形统计信息")
        self.sector_stats_label.setFont(QFont("Arial", 10))
        self.sector_stats_label.setWordWrap(True)
        self.sector_stats_label.setMinimumHeight(120)
        self.sector_stats_label.setAlignment(Qt.AlignTop)
        self.sector_stats_label.setObjectName("SectorStatsLabel")
        layout.addWidget(self.sector_stats_label)

        return group

    def initialize_data(self):
        """初始化数据"""
        self.update_progress_display()
        self.logger.info("✅ 左侧信息面板初始化完成")

    def set_panorama_widget(self, panorama_widget):
        """设置全景图组件"""
        if self.sidebar_panorama:
            # 如果已有组件，先移除
            self.sidebar_panorama.setParent(None)
            
        self.sidebar_panorama = panorama_widget
        
        # 替换占位符
        if hasattr(self, '_panorama_placeholder'):
            layout = self.panorama_group.layout()
            layout.removeWidget(self._panorama_placeholder)
            self._panorama_placeholder.deleteLater()
            layout.addWidget(self.sidebar_panorama)
            
        # 连接信号
        if hasattr(self.sidebar_panorama, 'sector_clicked'):
            self.sidebar_panorama.sector_clicked.connect(self.sector_clicked.emit)
            
        self.logger.info("✅ 全景图组件已设置")

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

    def update_sector_stats(self, sector_stats_text):
        """更新扇形统计信息"""
        self.sector_stats_label.setText(sector_stats_text)

    def update_batch_info(self, batch_id=None):
        """更新批次信息"""
        if batch_id:
            self.current_batch_label.setText(f"检测批次: {batch_id}")
        else:
            self.current_batch_label.setText("检测批次: 未开始")