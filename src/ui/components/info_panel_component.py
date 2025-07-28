"""
Info panel component for the main window.

This module implements the left information panel widget extracted from 
the original main window, displaying detection progress, status statistics,
and hole information.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..view_models.main_view_model import MainViewModel


class InfoPanelComponent(QWidget):
    """
    Information panel component showing detection progress and statistics.
    
    This component displays:
    - Detection progress and timing information
    - Status statistics for different hole types
    - Selected hole information
    """
    
    def __init__(self, parent: Optional = None):
        """
        Initialize the info panel component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking widgets
        self.progress_bar: Optional[QProgressBar] = None
        self.completed_count_label: Optional[QLabel] = None
        self.pending_count_label: Optional[QLabel] = None
        self.detection_time_label: Optional[QLabel] = None
        self.estimated_time_label: Optional[QLabel] = None
        self.completion_rate_label: Optional[QLabel] = None
        self.qualification_rate_label: Optional[QLabel] = None
        
        # Status statistics widgets
        self.pending_status_count_label: Optional[QLabel] = None
        self.qualified_count_label: Optional[QLabel] = None
        self.defective_count_label: Optional[QLabel] = None
        self.blind_count_label: Optional[QLabel] = None
        self.tie_rod_count_label: Optional[QLabel] = None
        self.processing_count_label: Optional[QLabel] = None
        
        # Hole information widgets
        self.selected_hole_id_label: Optional[QLabel] = None
        self.selected_hole_position_label: Optional[QLabel] = None
        self.selected_hole_status_label: Optional[QLabel] = None
        self.selected_hole_radius_label: Optional[QLabel] = None
        
        self._setup_ui()
        self.logger.debug("Info panel component initialized")
    
    def _setup_ui(self) -> None:
        """Setup the info panel UI layout."""
        self.setFixedWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Setup fonts
        panel_font = QFont()
        panel_font.setPointSize(10)
        self.setFont(panel_font)
        
        group_title_font = QFont()
        group_title_font.setPointSize(10)
        group_title_font.setBold(True)
        
        # 1. Detection progress group
        progress_group = self._create_progress_group(group_title_font)
        layout.addWidget(progress_group)
        
        # 2. Status statistics group
        stats_group = self._create_status_statistics_group(group_title_font)
        layout.addWidget(stats_group)
        
        # 3. Hole information group
        hole_info_group = self._create_hole_info_group(group_title_font)
        layout.addWidget(hole_info_group)
        
        # Add stretch to push content to top
        layout.addStretch()
    
    def _create_progress_group(self, title_font: QFont) -> QGroupBox:
        """Create the detection progress group."""
        progress_group = QGroupBox("检测进度")
        progress_group.setFont(title_font)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(4)
        progress_layout.setContentsMargins(4, 4, 4, 4)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)
        progress_layout.addWidget(self.progress_bar)
        
        # Statistics grid
        stats_grid_layout = QGridLayout()
        stats_grid_layout.setSpacing(2)
        stats_grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Count labels
        self.completed_count_label = QLabel("已完成: 0")
        self.pending_count_label = QLabel("待完成: 0")
        
        # Time labels
        self.detection_time_label = QLabel("检测时间: 00:00:00")
        self.estimated_time_label = QLabel("预计用时: 00:00:00")
        
        # Set font for labels
        label_font = QFont()
        label_font.setPointSize(9)
        for label in [self.completed_count_label, self.pending_count_label,
                     self.detection_time_label, self.estimated_time_label]:
            label.setFont(label_font)
        
        stats_grid_layout.addWidget(self.completed_count_label, 0, 0)
        stats_grid_layout.addWidget(self.pending_count_label, 0, 1)
        stats_grid_layout.addWidget(self.detection_time_label, 1, 0)
        stats_grid_layout.addWidget(self.estimated_time_label, 1, 1)
        
        progress_layout.addLayout(stats_grid_layout)
        
        # Rate labels in horizontal layout
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
        
        return progress_group
    
    def _create_status_statistics_group(self, title_font: QFont) -> QGroupBox:
        """Create the status statistics group."""
        stats_group = QGroupBox("状态统计")
        stats_group.setFont(title_font)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(4)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        
        # Status count labels
        self.pending_status_count_label = QLabel("待检: 0")
        self.qualified_count_label = QLabel("合格: 0")
        self.defective_count_label = QLabel("异常: 0")
        self.blind_count_label = QLabel("盲孔: 0")
        self.tie_rod_count_label = QLabel("拉杆孔: 0")
        self.processing_count_label = QLabel("检测中: 0")
        
        # Set font for status labels
        status_font = QFont()
        status_font.setPointSize(10)
        status_labels = [
            self.pending_status_count_label, self.qualified_count_label,
            self.defective_count_label, self.blind_count_label,
            self.tie_rod_count_label, self.processing_count_label
        ]
        for label in status_labels:
            label.setFont(status_font)
        
        # Arrange in grid
        stats_layout.addWidget(self.pending_status_count_label, 0, 0)
        stats_layout.addWidget(self.qualified_count_label, 0, 1)
        stats_layout.addWidget(self.defective_count_label, 1, 0)
        stats_layout.addWidget(self.blind_count_label, 1, 1)
        stats_layout.addWidget(self.tie_rod_count_label, 2, 0)
        stats_layout.addWidget(self.processing_count_label, 2, 1)
        
        return stats_group
    
    def _create_hole_info_group(self, title_font: QFont) -> QGroupBox:
        """Create the hole information group."""
        hole_info_group = QGroupBox("孔位信息")
        hole_info_group.setFont(title_font)
        hole_info_layout = QGridLayout(hole_info_group)
        hole_info_layout.setSpacing(4)
        hole_info_layout.setContentsMargins(8, 8, 8, 8)
        
        # Info labels
        self.selected_hole_id_label = QLabel("未选择")
        self.selected_hole_position_label = QLabel("-")
        self.selected_hole_status_label = QLabel("-")
        self.selected_hole_radius_label = QLabel("-")
        
        # Description labels
        hole_id_desc_label = QLabel("孔位ID:")
        position_desc_label = QLabel("位置:")
        status_desc_label = QLabel("状态:")
        radius_desc_label = QLabel("半径:")
        
        # Set font for hole info labels
        hole_info_font = QFont()
        hole_info_font.setPointSize(10)
        hole_info_labels = [
            hole_id_desc_label, position_desc_label, status_desc_label, radius_desc_label,
            self.selected_hole_id_label, self.selected_hole_position_label,
            self.selected_hole_status_label, self.selected_hole_radius_label
        ]
        for label in hole_info_labels:
            label.setFont(hole_info_font)
        
        # Arrange in grid
        hole_info_layout.addWidget(hole_id_desc_label, 0, 0)
        hole_info_layout.addWidget(self.selected_hole_id_label, 0, 1)
        hole_info_layout.addWidget(position_desc_label, 1, 0)
        hole_info_layout.addWidget(self.selected_hole_position_label, 1, 1)
        hole_info_layout.addWidget(status_desc_label, 2, 0)
        hole_info_layout.addWidget(self.selected_hole_status_label, 2, 1)
        hole_info_layout.addWidget(radius_desc_label, 3, 0)
        hole_info_layout.addWidget(self.selected_hole_radius_label, 3, 1)
        
        return hole_info_group
    
    def update_from_view_model(self, view_model: MainViewModel) -> None:
        """
        Update info panel from view model.
        
        Args:
            view_model: Current view model state
        """
        try:
            # Update progress bar
            if self.progress_bar:
                self.progress_bar.setValue(int(view_model.detection_progress))
            
            # Update count labels
            if self.completed_count_label:
                self.completed_count_label.setText(f"已完成: {view_model.completed_count}")
            
            if self.pending_count_label:
                self.pending_count_label.setText(f"待完成: {view_model.pending_count}")
            
            # Update time labels
            if self.detection_time_label:
                time_str = view_model.get_detection_time_formatted()
                self.detection_time_label.setText(f"检测时间: {time_str}")
            
            if self.estimated_time_label:
                time_str = view_model.get_estimated_time_formatted()
                self.estimated_time_label.setText(f"预计用时: {time_str}")
            
            # Update rate labels
            if self.completion_rate_label:
                self.completion_rate_label.setText(f"完成率: {view_model.completion_rate:.1f}%")
            
            if self.qualification_rate_label:
                self.qualification_rate_label.setText(f"合格率: {view_model.qualification_rate:.1f}%")
            
            # Update status statistics
            status_summary = view_model.status_summary
            
            if self.pending_status_count_label:
                self.pending_status_count_label.setText(f"待检: {status_summary.get('pending', 0)}")
            
            if self.qualified_count_label:
                self.qualified_count_label.setText(f"合格: {status_summary.get('qualified', 0)}")
            
            if self.defective_count_label:
                self.defective_count_label.setText(f"异常: {status_summary.get('defective', 0)}")
            
            if self.blind_count_label:
                self.blind_count_label.setText(f"盲孔: {status_summary.get('blind', 0)}")
            
            if self.tie_rod_count_label:
                self.tie_rod_count_label.setText(f"拉杆孔: {status_summary.get('tie_rod', 0)}")
            
            if self.processing_count_label:
                self.processing_count_label.setText(f"检测中: {status_summary.get('processing', 0)}")
            
            # Update hole information
            if view_model.current_hole_id:
                if self.selected_hole_id_label:
                    self.selected_hole_id_label.setText(view_model.current_hole_id)
                
                # If hole collection is available, get more details
                if view_model.hole_collection and hasattr(view_model.hole_collection, 'get_hole'):
                    try:
                        hole = view_model.hole_collection.get_hole(view_model.current_hole_id)
                        if hole:
                            if self.selected_hole_position_label and hasattr(hole, 'position'):
                                pos = hole.position
                                self.selected_hole_position_label.setText(f"({pos.x:.1f}, {pos.y:.1f})")
                            
                            if self.selected_hole_status_label and hasattr(hole, 'status'):
                                status_map = {
                                    'pending': '待检',
                                    'qualified': '合格',
                                    'defective': '异常',
                                    'blind': '盲孔',
                                    'tie_rod': '拉杆孔',
                                    'processing': '检测中'
                                }
                                status_text = status_map.get(hole.status, str(hole.status))
                                self.selected_hole_status_label.setText(status_text)
                            
                            if self.selected_hole_radius_label and hasattr(hole, 'radius'):
                                self.selected_hole_radius_label.setText(f"{hole.radius:.2f}mm")
                    except Exception as e:
                        self.logger.warning(f"Failed to get hole details: {e}")
            else:
                # No hole selected
                if self.selected_hole_id_label:
                    self.selected_hole_id_label.setText("未选择")
                if self.selected_hole_position_label:
                    self.selected_hole_position_label.setText("-")
                if self.selected_hole_status_label:
                    self.selected_hole_status_label.setText("-")
                if self.selected_hole_radius_label:
                    self.selected_hole_radius_label.setText("-")
            
            self.logger.debug("Info panel updated from view model")
            
        except Exception as e:
            self.logger.error(f"Failed to update info panel from view model: {e}")
    
    def reset_display(self) -> None:
        """Reset all displays to initial state."""
        try:
            # Reset progress
            if self.progress_bar:
                self.progress_bar.setValue(0)
            
            # Reset counts
            if self.completed_count_label:
                self.completed_count_label.setText("已完成: 0")
            if self.pending_count_label:
                self.pending_count_label.setText("待完成: 0")
            
            # Reset times
            if self.detection_time_label:
                self.detection_time_label.setText("检测时间: 00:00:00")
            if self.estimated_time_label:
                self.estimated_time_label.setText("预计用时: 00:00:00")
            
            # Reset rates
            if self.completion_rate_label:
                self.completion_rate_label.setText("完成率: 0%")
            if self.qualification_rate_label:
                self.qualification_rate_label.setText("合格率: 0%")
            
            # Reset status counts
            status_labels = [
                self.pending_status_count_label, self.qualified_count_label,
                self.defective_count_label, self.blind_count_label,
                self.tie_rod_count_label, self.processing_count_label
            ]
            status_texts = ["待检: 0", "合格: 0", "异常: 0", "盲孔: 0", "拉杆孔: 0", "检测中: 0"]
            
            for label, text in zip(status_labels, status_texts):
                if label:
                    label.setText(text)
            
            # Reset hole info
            if self.selected_hole_id_label:
                self.selected_hole_id_label.setText("未选择")
            if self.selected_hole_position_label:
                self.selected_hole_position_label.setText("-")
            if self.selected_hole_status_label:
                self.selected_hole_status_label.setText("-")
            if self.selected_hole_radius_label:
                self.selected_hole_radius_label.setText("-")
            
            self.logger.debug("Info panel display reset")
            
        except Exception as e:
            self.logger.error(f"Failed to reset info panel display: {e}")