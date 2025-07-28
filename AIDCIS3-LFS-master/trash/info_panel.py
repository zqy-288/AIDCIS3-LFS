"""
信息面板组件
从main_window.py重构提取的独立UI组件
负责显示检测进度、状态统计、孔位信息、文件信息、全景预览等
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QProgressBar
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

# 导入扇形显示组件
from core_business.graphics.dynamic_sector_view import CompletePanoramaWidget


class InfoPanel(QWidget):
    """
    信息面板组件
    包含检测进度、状态统计、孔位信息、文件信息、全景预览、扇形统计等功能区
    """
    
    # 定义信号
    hole_selected = Signal(str)  # 孔位被选中
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI组件"""
        self.setFixedWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)

        # 设置全局字体
        panel_font = QFont()
        panel_font.setPointSize(10)
        self.setFont(panel_font)

        # 1. 检测进度组
        self._create_progress_section(layout)
        
        # 2. 状态统计组
        self._create_status_section(layout)
        
        # 3. 孔位信息组
        self._create_hole_info_section(layout)
        
        
        # 5. 全景预览组
        self._create_panorama_section(layout)
        
        # 6. 扇形统计组
        self._create_sector_stats_section(layout)
        
        layout.addStretch()
    
    def _create_progress_section(self, layout):
        """创建检测进度区"""
        progress_group = QGroupBox("检测进度")
        progress_group_font = QFont()
        progress_group_font.setPointSize(10)
        progress_group_font.setBold(True)
        progress_group.setFont(progress_group_font)
        
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(4)
        progress_layout.setContentsMargins(4, 4, 4, 4)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)
        progress_layout.addWidget(self.progress_bar)

        # 统计信息网格
        stats_grid_layout = QGridLayout()
        stats_grid_layout.setSpacing(2)
        stats_grid_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签
        label_font = QFont()
        label_font.setPointSize(9)
        
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")
        self.detection_time_label = QLabel("检测时间: 00:00:00")
        self.estimated_time_label = QLabel("预计用时: 00:00:00")
        
        # 设置字体
        for label in [self.completed_count_label, self.pending_count_label,
                     self.detection_time_label, self.estimated_time_label]:
            label.setFont(label_font)
        
        # 布局
        stats_grid_layout.addWidget(self.completed_count_label, 0, 0)
        stats_grid_layout.addWidget(self.pending_count_label, 0, 1)
        stats_grid_layout.addWidget(self.detection_time_label, 1, 0)
        stats_grid_layout.addWidget(self.estimated_time_label, 1, 1)

        progress_layout.addLayout(stats_grid_layout)

        # 完成率和合格率
        rate_layout = QHBoxLayout()
        rate_layout.setSpacing(10)

        self.completion_rate_label = QLabel("完成率: 0%")
        self.qualification_rate_label = QLabel("合格率: 0%")
        
        self.completion_rate_label.setFont(label_font)
        self.qualification_rate_label.setFont(label_font)

        rate_layout.addWidget(self.completion_rate_label)
        rate_layout.addWidget(self.qualification_rate_label)
        rate_layout.addStretch()

        progress_layout.addLayout(rate_layout)
        layout.addWidget(progress_group)
    
    def _create_status_section(self, layout):
        """创建状态统计区"""
        stats_group = QGroupBox("状态统计")
        stats_group_font = QFont()
        stats_group_font.setPointSize(10)
        stats_group_font.setBold(True)
        stats_group.setFont(stats_group_font)
        
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(4)
        stats_layout.setContentsMargins(8, 8, 8, 8)

        # 创建状态标签
        self.pending_status_count_label = QLabel("待检: 0")
        self.qualified_count_label = QLabel("合格: 0")
        self.defective_count_label = QLabel("异常: 0")
        self.blind_count_label = QLabel("盲孔: 0")
        self.tie_rod_count_label = QLabel("拉杆孔: 0")
        self.processing_count_label = QLabel("检测中: 0")

        # 设置字体
        status_font = QFont()
        status_font.setPointSize(10)
        
        status_labels = [
            self.pending_status_count_label, self.qualified_count_label,
            self.defective_count_label, self.blind_count_label,
            self.tie_rod_count_label, self.processing_count_label
        ]
        for label in status_labels:
            label.setFont(status_font)

        # 布局
        stats_layout.addWidget(self.pending_status_count_label, 0, 0)
        stats_layout.addWidget(self.qualified_count_label, 0, 1)
        stats_layout.addWidget(self.defective_count_label, 1, 0)
        stats_layout.addWidget(self.blind_count_label, 1, 1)
        stats_layout.addWidget(self.tie_rod_count_label, 2, 0)
        stats_layout.addWidget(self.processing_count_label, 2, 1)

        layout.addWidget(stats_group)
    
    def _create_hole_info_section(self, layout):
        """创建孔位信息区"""
        hole_info_group = QGroupBox("孔位信息")
        hole_info_group_font = QFont()
        hole_info_group_font.setPointSize(10)
        hole_info_group_font.setBold(True)
        hole_info_group.setFont(hole_info_group_font)
        
        hole_info_layout = QGridLayout(hole_info_group)
        hole_info_layout.setSpacing(4)
        hole_info_layout.setContentsMargins(8, 8, 8, 8)

        # 创建标签
        self.selected_hole_id_label = QLabel("未选择")
        self.selected_hole_position_label = QLabel("-")
        self.selected_hole_status_label = QLabel("-")
        self.selected_hole_radius_label = QLabel("-")

        # 描述标签
        hole_id_desc_label = QLabel("孔位ID:")
        position_desc_label = QLabel("位置:")
        status_desc_label = QLabel("状态:")
        radius_desc_label = QLabel("半径:")

        # 设置字体
        hole_info_font = QFont()
        hole_info_font.setPointSize(10)
        
        hole_info_labels = [
            hole_id_desc_label, position_desc_label, status_desc_label, radius_desc_label,
            self.selected_hole_id_label, self.selected_hole_position_label,
            self.selected_hole_status_label, self.selected_hole_radius_label
        ]
        for label in hole_info_labels:
            label.setFont(hole_info_font)

        # 布局
        hole_info_layout.addWidget(hole_id_desc_label, 0, 0)
        hole_info_layout.addWidget(self.selected_hole_id_label, 0, 1)
        hole_info_layout.addWidget(position_desc_label, 1, 0)
        hole_info_layout.addWidget(self.selected_hole_position_label, 1, 1)
        hole_info_layout.addWidget(status_desc_label, 2, 0)
        hole_info_layout.addWidget(self.selected_hole_status_label, 2, 1)
        hole_info_layout.addWidget(radius_desc_label, 3, 0)
        hole_info_layout.addWidget(self.selected_hole_radius_label, 3, 1)

        layout.addWidget(hole_info_group)
    
    
    def _create_panorama_section(self, layout):
        """创建全景预览区"""
        panorama_group = QGroupBox("全景预览")
        panorama_group_font = QFont()
        panorama_group_font.setPointSize(10)
        panorama_group_font.setBold(True)
        panorama_group.setFont(panorama_group_font)
        
        panorama_layout = QVBoxLayout(panorama_group)
        panorama_layout.setContentsMargins(5, 5, 5, 5)

        # 创建全景预览组件
        self.sidebar_panorama = CompletePanoramaWidget()
        self.sidebar_panorama.setFixedSize(360, 420)
        self.sidebar_panorama.setObjectName("PanoramaWidget")
        panorama_layout.addWidget(self.sidebar_panorama)
        
        layout.addWidget(panorama_group)
    
    def _create_sector_stats_section(self, layout):
        """创建扇形统计区"""
        sector_stats_group = QGroupBox("选中扇形")
        sector_stats_group_font = QFont()
        sector_stats_group_font.setPointSize(10)
        sector_stats_group_font.setBold(True)
        sector_stats_group.setFont(sector_stats_group_font)
        
        sector_stats_layout = QVBoxLayout(sector_stats_group)
        sector_stats_layout.setContentsMargins(5, 5, 5, 5)
        
        self.sector_stats_label = QLabel("扇形统计信息")
        self.sector_stats_label.setFont(QFont("Arial", 10))
        self.sector_stats_label.setWordWrap(True)
        self.sector_stats_label.setMinimumHeight(120)
        self.sector_stats_label.setAlignment(Qt.AlignTop)
        self.sector_stats_label.setObjectName("SectorStatsLabel")
        
        sector_stats_layout.addWidget(self.sector_stats_label)
        layout.addWidget(sector_stats_group)
    
    def setup_connections(self):
        """设置信号连接"""
        # 可以在这里添加内部信号连接
        pass
    
    # 进度相关方法
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_completion_stats(self, completed: int, pending: int):
        """更新完成统计"""
        self.completed_count_label.setText(f"已完成: {completed}")
        self.pending_count_label.setText(f"待完成: {pending}")
    
    
    def update_time_info(self, detection_time: str, estimated_time: str):
        """更新时间信息"""
        self.detection_time_label.setText(f"检测时间: {detection_time}")
        self.estimated_time_label.setText(f"预计用时: {estimated_time}")
    
    def update_rates(self, completion_rate: float, qualification_rate: float):
        """更新完成率和合格率"""
        self.completion_rate_label.setText(f"完成率: {completion_rate:.1f}%")
        self.qualification_rate_label.setText(f"合格率: {qualification_rate:.1f}%")
    
    # 状态统计相关方法
    def update_status_counts(self, counts: dict):
        """更新状态统计"""
        self.pending_status_count_label.setText(f"待检: {counts.get('pending', 0)}")
        self.qualified_count_label.setText(f"合格: {counts.get('qualified', 0)}")
        self.defective_count_label.setText(f"异常: {counts.get('defective', 0)}")
        self.blind_count_label.setText(f"盲孔: {counts.get('blind', 0)}")
        self.tie_rod_count_label.setText(f"拉杆孔: {counts.get('tie_rod', 0)}")
        self.processing_count_label.setText(f"检测中: {counts.get('processing', 0)}")
    
    # 孔位信息相关方法
    def update_selected_hole_info(self, hole_id: str, position: str, status: str, radius: str):
        """更新选中孔位信息"""
        self.selected_hole_id_label.setText(hole_id)
        self.selected_hole_position_label.setText(position)
        self.selected_hole_status_label.setText(status)
        self.selected_hole_radius_label.setText(radius)
    
    def clear_selected_hole_info(self):
        """清空选中孔位信息"""
        self.selected_hole_id_label.setText("未选择")
        self.selected_hole_position_label.setText("-")
        self.selected_hole_status_label.setText("-")
        self.selected_hole_radius_label.setText("-")
    
    
    # 扇形统计相关方法
    def update_sector_stats(self, stats_text: str):
        """更新扇形统计信息"""
        self.sector_stats_label.setText(stats_text)
    
    def clear_sector_stats(self):
        """清空扇形统计信息"""
        self.sector_stats_label.setText("扇形统计信息")
    
    # 全景预览相关方法
    def get_panorama_widget(self):
        """获取全景预览组件"""
        return self.sidebar_panorama