"""左侧信息面板组件"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, 
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor

from aidcis2.models.hole_data import HoleData


class InfoPanel(QWidget):
    """
    左侧信息面板
    显示文件信息、孔位统计和选中孔位详情
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 设置固定宽度
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        
        # 文件信息组
        self.file_info_group = self._create_file_info_group()
        layout.addWidget(self.file_info_group)
        
        # 孔位统计组
        self.statistics_group = self._create_statistics_group()
        layout.addWidget(self.statistics_group)
        
        # 选中孔位信息组
        self.selected_hole_group = self._create_selected_hole_group()
        layout.addWidget(self.selected_hole_group)
        
        layout.addStretch()
        
    def _create_file_info_group(self) -> QGroupBox:
        """创建文件信息组"""
        group = QGroupBox("文件信息")
        layout = QGridLayout(group)
        
        # 产品型号
        layout.addWidget(QLabel("产品型号:"), 0, 0)
        self.product_model_label = QLabel("未选择")
        layout.addWidget(self.product_model_label, 0, 1)
        
        # 文件名
        layout.addWidget(QLabel("文件名:"), 1, 0)
        self.file_name_label = QLabel("未加载")
        layout.addWidget(self.file_name_label, 1, 1)
        
        # 文件路径
        layout.addWidget(QLabel("路径:"), 2, 0)
        self.file_path_label = QLabel("未加载")
        self.file_path_label.setWordWrap(True)
        layout.addWidget(self.file_path_label, 2, 1)
        
        return group
        
    def _create_statistics_group(self) -> QGroupBox:
        """创建孔位统计组"""
        group = QGroupBox("孔位统计")
        layout = QGridLayout(group)
        
        # 创建状态标签
        status_info = [
            ("总数:", "total_count_label", 0, 0),
            ("待检:", "pending_count_label", 1, 0),
            ("检测中:", "processing_count_label", 2, 0),
            ("合格:", "qualified_count_label", 0, 2),
            ("异常:", "defective_count_label", 1, 2),
            ("盲孔:", "blind_count_label", 2, 2),
            ("拉杆孔:", "tie_rod_count_label", 3, 0)
        ]
        
        for label_text, attr_name, row, col in status_info:
            label = QLabel(label_text)
            layout.addWidget(label, row, col)
            
            count_label = QLabel("0")
            count_label.setAlignment(Qt.AlignRight)
            setattr(self, attr_name, count_label)
            layout.addWidget(count_label, row, col + 1)
            
        return group
        
    def _create_selected_hole_group(self) -> QGroupBox:
        """创建选中孔位信息组"""
        group = QGroupBox("选中孔位")
        layout = QGridLayout(group)
        
        # 孔位ID
        layout.addWidget(QLabel("ID:"), 0, 0)
        self.selected_hole_id_label = QLabel("未选择")
        self.selected_hole_id_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.selected_hole_id_label, 0, 1)
        
        # 位置
        layout.addWidget(QLabel("位置:"), 1, 0)
        self.selected_hole_position_label = QLabel("--")
        layout.addWidget(self.selected_hole_position_label, 1, 1)
        
        # 状态
        layout.addWidget(QLabel("状态:"), 2, 0)
        self.selected_hole_status_label = QLabel("--")
        layout.addWidget(self.selected_hole_status_label, 2, 1)
        
        # 半径
        layout.addWidget(QLabel("半径:"), 3, 0)
        self.selected_hole_radius_label = QLabel("--")
        layout.addWidget(self.selected_hole_radius_label, 3, 1)
        
        return group
        
    def update_product_info(self, product):
        """更新产品信息"""
        if product:
            self.product_model_label.setText(product.model_name)
        else:
            self.product_model_label.setText("未选择")
            
    def update_file_info(self, file_path: str):
        """更新文件信息"""
        if file_path:
            from pathlib import Path
            path = Path(file_path)
            self.file_name_label.setText(path.name)
            self.file_path_label.setText(str(path))
            self.file_path_label.setToolTip(str(path))
        else:
            self.file_name_label.setText("未加载")
            self.file_path_label.setText("未加载")
            
    def update_statistics(self, stats: dict):
        """更新统计信息"""
        self.total_count_label.setText(str(stats.get('total', 0)))
        self.pending_count_label.setText(str(stats.get('pending', 0)))
        self.processing_count_label.setText(str(stats.get('processing', 0)))
        self.qualified_count_label.setText(str(stats.get('qualified', 0)))
        self.defective_count_label.setText(str(stats.get('defective', 0)))
        self.blind_count_label.setText(str(stats.get('blind', 0)))
        self.tie_rod_count_label.setText(str(stats.get('tie_rod', 0)))
        
    def update_hole_info(self, hole: HoleData):
        """更新选中孔位信息"""
        if hole:
            self.selected_hole_id_label.setText(hole.hole_id)
            self.selected_hole_position_label.setText(
                f"({hole.center_x:.1f}, {hole.center_y:.1f})"
            )
            self.selected_hole_status_label.setText(hole.status.value)
            self.selected_hole_radius_label.setText(f"{hole.radius:.3f} mm")
            
            # 根据状态设置颜色
            status_colors = {
                "待检": "#808080",
                "检测中": "#0080FF",
                "合格": "#00FF00",
                "异常": "#FF0000",
                "盲孔": "#FFFF00",
                "拉杆孔": "#00FFFF"
            }
            
            color = status_colors.get(hole.status.value, "#000000")
            self.selected_hole_status_label.setStyleSheet(f"color: {color};")
        else:
            self.selected_hole_id_label.setText("未选择")
            self.selected_hole_position_label.setText("--")
            self.selected_hole_status_label.setText("--")
            self.selected_hole_radius_label.setText("--")
            self.selected_hole_status_label.setStyleSheet("")