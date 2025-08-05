"""
历史数据查看器 - 3.1界面
用于查看管孔直径历史数据
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QGroupBox,
    QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class HistoryViewer(QWidget):
    """历史数据查看器"""
    
    # 信号定义
    data_loaded = Signal(str)  # 数据加载完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 当前加载的孔位ID
        self.current_hole_id = None
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("历史数据查看器")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建标题区域
        self.create_header(main_layout)
        
        # 创建内容区域
        self.create_content_area(main_layout)
        
    def create_header(self, parent_layout):
        """创建标题区域"""
        header_group = QGroupBox("管孔直径历史数据")
        header_layout = QHBoxLayout(header_group)
        
        # 当前孔位标签
        self.hole_label = QLabel("当前孔位: 未选择")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.hole_label.setFont(font)
        
        # 数据状态标签
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("color: #2E7D32;")
        
        header_layout.addWidget(self.hole_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(header_group)
        
    def create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据表格
        self.create_data_table(splitter)
        
        # 右侧：详细信息
        self.create_detail_panel(splitter)
        
        # 设置分割比例
        splitter.setSizes([600, 300])
        
        parent_layout.addWidget(splitter)
        
    def create_data_table(self, parent):
        """创建数据表格"""
        table_group = QGroupBox("历史测量数据")
        table_layout = QVBoxLayout(table_group)
        
        # 创建表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels([
            "测量时间", "管孔直径(mm)", "深度(mm)", "质量等级", "备注"
        ])
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        
        table_layout.addWidget(self.data_table)
        parent.addWidget(table_group)
        
    def create_detail_panel(self, parent):
        """创建详细信息面板"""
        detail_group = QGroupBox("详细信息")
        detail_layout = QVBoxLayout(detail_group)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_count_label = QLabel("总测量次数: 0")
        self.avg_diameter_label = QLabel("平均直径: 0.00 mm")
        self.min_diameter_label = QLabel("最小直径: 0.00 mm")
        self.max_diameter_label = QLabel("最大直径: 0.00 mm")
        
        stats_layout.addWidget(self.total_count_label)
        stats_layout.addWidget(self.avg_diameter_label)
        stats_layout.addWidget(self.min_diameter_label)
        stats_layout.addWidget(self.max_diameter_label)
        stats_layout.addStretch()
        
        # 备注信息
        notes_group = QGroupBox("备注信息")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setPlaceholderText("选择测量记录查看备注...")
        self.notes_text.setReadOnly(True)
        
        notes_layout.addWidget(self.notes_text)
        
        detail_layout.addWidget(stats_group)
        detail_layout.addWidget(notes_group)
        detail_layout.addStretch()
        
        parent.addWidget(detail_group)
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        print(f"📊 历史数据查看器: 加载孔位 {hole_id} 的数据")
        
        self.current_hole_id = hole_id
        self.hole_label.setText(f"当前孔位: {hole_id}")
        self.status_label.setText("状态: 加载中...")
        self.status_label.setStyleSheet("color: #FF9800;")
        
        # 模拟加载历史数据
        self._load_mock_data(hole_id)
        
        # 发射数据加载完成信号
        self.data_loaded.emit(hole_id)
        
    def _load_mock_data(self, hole_id: str):
        """加载模拟数据"""
        # 清空现有数据
        self.data_table.setRowCount(0)
        
        # 模拟历史数据
        mock_data = [
            ["2024-01-15 09:30:00", "12.50", "25.0", "优秀", "正常测量"],
            ["2024-01-14 14:20:00", "12.48", "24.8", "良好", "轻微偏差"],
            ["2024-01-13 11:45:00", "12.52", "25.2", "优秀", "标准范围内"],
            ["2024-01-12 16:10:00", "12.49", "24.9", "良好", "正常测量"],
            ["2024-01-11 10:25:00", "12.51", "25.1", "优秀", "质量良好"],
        ]
        
        # 填充表格数据
        self.data_table.setRowCount(len(mock_data))
        for row, data in enumerate(mock_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)
        
        # 更新统计信息
        diameters = [float(data[1]) for data in mock_data]
        self.total_count_label.setText(f"总测量次数: {len(mock_data)}")
        self.avg_diameter_label.setText(f"平均直径: {sum(diameters)/len(diameters):.2f} mm")
        self.min_diameter_label.setText(f"最小直径: {min(diameters):.2f} mm")
        self.max_diameter_label.setText(f"最大直径: {max(diameters):.2f} mm")
        
        # 更新状态
        self.status_label.setText("状态: 数据加载完成")
        self.status_label.setStyleSheet("color: #2E7D32;")
        
        print(f"✅ 历史数据查看器: 孔位 {hole_id} 数据加载完成 ({len(mock_data)} 条记录)")
        
    def cleanup(self):
        """清理资源"""
        print("🧹 历史数据查看器: 清理资源")
        self.current_hole_id = None
        self.data_table.clear()