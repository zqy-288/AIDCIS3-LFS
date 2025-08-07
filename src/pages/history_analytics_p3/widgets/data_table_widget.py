"""
数据表格组件 - 高内聚低耦合设计
职责：专门负责测量数据的表格显示和交互
基于重构前代码完全恢复表格功能
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from datetime import datetime
from typing import List, Dict, Optional
import logging


class DataTableWidget(QWidget):
    """
    测量数据表格组件 - 高内聚设计
    职责：
    1. 显示10列完整的测量数据结构
    2. 支持数据排序和筛选
    3. 提供行选择和双击事件
    4. 管理表格样式和格式
    """
    
    # 信号定义
    row_selected = Signal(int, dict)    # 行选择信号 (row_index, measurement_data)
    row_double_clicked = Signal(int, dict)  # 行双击信号 (row_index, measurement_data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 当前数据
        self.measurements = []
        
        # 设置界面
        self.setup_ui()
        
        self.logger.info("数据表格组件初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 创建表格分组
        table_group = QGroupBox("测量数据")
        table_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建表格
        self.setup_table(table_layout)
        
        layout.addWidget(table_group)
    
    def setup_table(self, parent_layout):
        """设置数据表格"""
        self.data_table = QTableWidget()
        
        # 设置列数和列头 - 完整的10列结构
        column_count = 10
        headers = [
            "序号", "位置", "直径", "通道1值", "通道2值", 
            "通道3值", "合格", "时间", "操纵员", "备注"
        ]
        
        self.data_table.setColumnCount(column_count)
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # 设置表格样式 - 基于重构前的深色主题
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2d35;
                border: 1px solid #505869;
                selection-background-color: #4A90E2;
                selection-color: white;
                gridline-color: #505869;
                color: #D3D8E0;
            }
            QHeaderView::section {
                background-color: #3a3d45;
                color: #D3D8E0;
                padding: 8px;
                border: 1px solid #505869;
                font-weight: bold;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #505869;
            }
            QTableWidget::item:selected {
                background-color: #4A90E2;
                color: white;
            }
            QScrollBar:vertical {
                background-color: #3a3d45;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #505869;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6d75;
            }
        """)
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.data_table.setSortingEnabled(True)
        self.data_table.setShowGrid(True)
        
        # 设置表格最小高度以显示更多行（基于重构前的显示行数）
        self.data_table.setMinimumHeight(300)
        
        # 设置垂直表头
        vertical_header = self.data_table.verticalHeader()
        vertical_header.setDefaultSectionSize(25)  # 行高设置为25像素，显示更多行
        
        # 设置列宽 - 基于重构前的列宽配置
        self.setup_column_widths()
        
        # 连接信号
        self.data_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.data_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        parent_layout.addWidget(self.data_table)
    
    def setup_column_widths(self):
        """设置列宽"""
        column_widths = {
            0: 60,   # 序号
            1: 80,   # 位置
            2: 90,   # 直径
            3: 90,   # 通道1值
            4: 90,   # 通道2值
            5: 90,   # 通道3值
            6: 60,   # 合格
            7: 130,  # 时间
            8: 80,   # 操纵员
            9: 100   # 备注
        }
        
        for column, width in column_widths.items():
            self.data_table.setColumnWidth(column, width)
        
        # 设置最后一列自适应
        header = self.data_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def load_measurements(self, measurements: List[Dict]):
        """
        加载测量数据到表格
        measurements: 测量数据列表
        """
        self.measurements = measurements
        self.logger.info(f"开始加载 {len(measurements)} 条测量数据到表格")
        
        # 清空现有数据
        self.data_table.setRowCount(0)
        
        if not measurements:
            self.logger.info("没有数据需要显示")
            return
        
        # 设置行数
        self.data_table.setRowCount(len(measurements))
        
        # 填充数据
        for row, measurement in enumerate(measurements):
            self.populate_row(row, measurement)
        
        # 调整列宽 - 完全按照重构前逻辑
        self.data_table.resizeColumnsToContents()
        
        self.logger.info(f"成功加载 {len(measurements)} 条数据到表格")
    
    def populate_row(self, row: int, measurement: Dict):
        """填充单行数据 - 完全基于重构前的update_data_table逻辑"""
        try:
            # 序号列 (第0列) - 完全按照重构前逻辑
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)  # 让序号居中显示
            self.data_table.setItem(row, 0, seq_item)

            # 位置(mm) - 对应测量序号 (现在是第1列)
            position = measurement.get('position', measurement.get('depth', 0))
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{position:.1f}"))

            # 直径(mm) (现在是第2列)
            diameter = measurement.get('diameter', 0)
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{diameter:.4f}"))

            # 通道1值(mm) (现在是第3列)
            channel1 = measurement.get('channel1', 0)
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{channel1:.2f}"))

            # 通道2值(mm) (现在是第4列)
            channel2 = measurement.get('channel2', 0)
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{channel2:.2f}"))

            # 通道3值(mm) (现在是第5列)
            channel3 = measurement.get('channel3', 0)
            self.data_table.setItem(row, 5, QTableWidgetItem(f"{channel3:.2f}"))

            # 合格性 (现在是第6列) - 完全按照重构前显示逻辑
            is_qualified = measurement.get('is_qualified', True)
            qualified_text = "✓" if is_qualified else "✗"
            item = QTableWidgetItem(qualified_text)
            if not is_qualified:
                item.setBackground(Qt.red)
            else:
                item.setBackground(Qt.green)
            self.data_table.setItem(row, 6, item)

            # 时间 (现在是第7列) - 按照重构前的时间显示格式
            timestamp = measurement.get('timestamp', '')
            if timestamp:
                time_str = timestamp.strftime("%H:%M:%S")
            else:
                time_str = "--"
            self.data_table.setItem(row, 7, QTableWidgetItem(time_str))

            # 操作员 (现在是第8列)
            operator = measurement.get('operator', '--')
            self.data_table.setItem(row, 8, QTableWidgetItem(operator))

            # 备注 - 只有实际进行了人工复查的行才显示复查信息 (现在是第9列)
            notes = ""
            if 'manual_review_value' in measurement:
                # 只有存在manual_review_value的行才显示复查信息
                review_value = measurement['manual_review_value']
                reviewer = measurement.get('reviewer', '未知')
                review_time = measurement.get('review_time', '')
                notes = f"人工复查值: {review_value:.4f}mm, 复查员: {reviewer}, 复查时间: {review_time}"

            self.data_table.setItem(row, 9, QTableWidgetItem(notes))
            
        except Exception as e:
            self.logger.error(f"填充第{row}行数据时发生错误: {e}")
    
    def set_diameter_color(self, item: QTableWidgetItem, diameter: float):
        """
        根据公差范围设置直径值的颜色 - 基于重构前的颜色规则
        """
        # 默认公差参数 - 与重构前完全一致（非对称公差）
        standard_diameter = 17.73
        upper_tolerance = 0.07
        lower_tolerance = 0.05
        
        upper_limit = standard_diameter + upper_tolerance  # 17.73 + 0.07 = 17.80
        lower_limit = standard_diameter - lower_tolerance  # 17.73 - 0.05 = 17.68
        
        if diameter > upper_limit or diameter < lower_limit:
            # 超出公差范围 - 红色
            item.setForeground(Qt.red)
        elif diameter > (standard_diameter + upper_tolerance * 0.8) or \
             diameter < (standard_diameter + lower_tolerance * 1.2):
            # 接近公差边界 - 黄色警告
            item.setForeground(Qt.yellow)
        else:
            # 正常范围 - 绿色
            item.setForeground(Qt.green)
    
    def on_selection_changed(self):
        """处理表格选择变化"""
        selected_rows = self.data_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.measurements):
                measurement = self.measurements[row]
                self.row_selected.emit(row, measurement)
    
    def on_item_double_clicked(self, item):
        """处理表格项双击"""
        row = item.row()
        if 0 <= row < len(self.measurements):
            measurement = self.measurements[row]
            self.row_double_clicked.emit(row, measurement)
    
    def clear_data(self):
        """清除表格数据"""
        self.measurements = []
        self.data_table.setRowCount(0)
        self.logger.info("表格数据已清除")
    
    def get_selected_measurement(self) -> Optional[Dict]:
        """获取当前选中的测量数据"""
        selected_rows = self.data_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.measurements):
                return self.measurements[row]
        
        return None
    
    def get_all_measurements(self) -> List[Dict]:
        """获取所有测量数据"""
        return self.measurements.copy()
    
    def update_tolerance_colors(self, standard_diameter: float, 
                              upper_tolerance: float, lower_tolerance: float):
        """
        更新公差颜色显示
        当公差参数改变时，重新设置直径列的颜色
        """
        for row in range(self.data_table.rowCount()):
            diameter_item = self.data_table.item(row, 2)  # 直径列
            if diameter_item:
                diameter = float(diameter_item.text())
                
                upper_limit = standard_diameter + upper_tolerance
                lower_limit = standard_diameter - lower_tolerance
                
                if diameter > upper_limit or diameter < lower_limit:
                    diameter_item.setForeground(Qt.red)
                elif diameter > (standard_diameter + upper_tolerance * 0.8) or \
                     diameter < (standard_diameter + lower_tolerance * 1.2):
                    diameter_item.setForeground(Qt.yellow)
                else:
                    diameter_item.setForeground(Qt.green)
        
        self.logger.info("公差颜色显示已更新")
    
    def export_table_data(self) -> List[List[str]]:
        """
        导出表格数据为二维数组格式
        返回包含表头的完整数据
        """
        data = []
        
        # 添加表头
        headers = []
        for column in range(self.data_table.columnCount()):
            header_item = self.data_table.horizontalHeaderItem(column)
            headers.append(header_item.text() if header_item else f"列{column}")
        data.append(headers)
        
        # 添加数据行
        for row in range(self.data_table.rowCount()):
            row_data = []
            for column in range(self.data_table.columnCount()):
                item = self.data_table.item(row, column)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        return data
    
    def get_statistics_summary(self) -> Dict:
        """获取表格数据的统计摘要"""
        if not self.measurements:
            return {}
        
        diameters = [m.get('diameter', 0) for m in self.measurements]
        qualified_count = sum(1 for m in self.measurements if m.get('is_qualified', True))
        
        import numpy as np
        
        return {
            'total_count': len(self.measurements),
            'qualified_count': qualified_count,
            'qualified_rate': (qualified_count / len(self.measurements)) * 100,
            'min_diameter': min(diameters) if diameters else 0,
            'max_diameter': max(diameters) if diameters else 0,
            'mean_diameter': np.mean(diameters) if diameters else 0,
            'std_diameter': np.std(diameters) if diameters else 0
        }
    
