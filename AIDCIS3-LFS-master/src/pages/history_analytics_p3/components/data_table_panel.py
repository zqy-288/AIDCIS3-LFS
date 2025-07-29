"""
数据表格面板组件
基于重构前的HistoryViewer数据表格实现
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class DataTablePanel(QWidget):
    """
    数据表格面板 - 完全按照重构前的设计
    显示测量数据的详细表格
    """
    
    # 信号定义
    row_double_clicked = Signal(int)  # 行双击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据存储
        self.measurements_data = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 完全按照重构前的布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建数据表格组 - 按照重构前的设计
        table_group = QGroupBox("测量数据")
        table_layout = QVBoxLayout(table_group)
        
        # 创建表格 - 按照重构前的精确配置
        self.data_table = QTableWidget()
        self.data_table.verticalHeader().setVisible(False)  # 隐藏左侧的行号表头
        self.data_table.setColumnCount(10)  # 按照重构前的10列
        self.data_table.setHorizontalHeaderLabels([
            "序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", 
            "通道3值(μm)", "合格", "时间", "操作员", "备注"
        ])
        
        # 设置表格属性 - 按照重构前的配置
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSortingEnabled(True)
        
        # 禁用表格编辑
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 连接双击事件
        self.data_table.cellDoubleClicked.connect(self.on_table_double_clicked)
        
        table_layout.addWidget(self.data_table)
        layout.addWidget(table_group)
        
    def on_table_double_clicked(self, row, column):
        """处理表格双击事件 - 按照重构前的实现"""
        print(f"🔍 双击事件触发: 行{row}, 列{column}")
        self.row_double_clicked.emit(row)
        
    def update_table_data(self, measurements):
        """更新数据表格 - 完全按照重构前的实现"""
        self.update_data(measurements)

    def update_data(self, measurements):
        """更新数据表格 - 完全按照重构前的实现"""
        self.measurements_data = measurements
        self.data_table.setRowCount(len(measurements))
        
        for row, measurement in enumerate(measurements):
            # 序号列 (第0列)
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row, 0, seq_item)
            
            # 位置(mm) - 对应测量序号 (第1列)
            position = measurement.get('position', measurement.get('depth', 0))
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{position:.1f}"))
            
            # 直径(mm) (第2列)
            diameter = measurement.get('diameter', 0)
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{diameter:.4f}"))
            
            # 通道1值(μm) (第3列)
            channel1 = measurement.get('channel1', 0)
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{channel1:.2f}"))
            
            # 通道2值(μm) (第4列)
            channel2 = measurement.get('channel2', 0)
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{channel2:.2f}"))
            
            # 通道3值(μm) (第5列)
            channel3 = measurement.get('channel3', 0)
            self.data_table.setItem(row, 5, QTableWidgetItem(f"{channel3:.2f}"))
            
            # 合格性 (第6列) - 按照重构前的样式
            is_qualified = measurement.get('is_qualified', True)
            qualified_text = "✓" if is_qualified else "✗"
            item = QTableWidgetItem(qualified_text)
            item.setTextAlignment(Qt.AlignCenter)
            if not is_qualified:
                item.setBackground(QColor(255, 0, 0, 100))  # 红色背景
            else:
                item.setBackground(QColor(0, 255, 0, 100))  # 绿色背景
            self.data_table.setItem(row, 6, item)
            
            # 时间 (第7列)
            timestamp = measurement.get('timestamp', '')
            if timestamp:
                if hasattr(timestamp, 'strftime'):
                    time_str = timestamp.strftime("%H:%M:%S")
                else:
                    time_str = str(timestamp)
            else:
                time_str = "--"
            self.data_table.setItem(row, 7, QTableWidgetItem(time_str))
            
            # 操作员 (第8列)
            operator = measurement.get('operator', '--')
            self.data_table.setItem(row, 8, QTableWidgetItem(operator))
            
            # 备注 - 只有实际进行了人工复查的行才显示复查信息 (第9列)
            notes = ""
            if 'manual_review_value' in measurement:
                review_value = measurement['manual_review_value']
                reviewer = measurement.get('reviewer', '未知')
                review_time = measurement.get('review_time', '')
                notes = f"人工复查值: {review_value:.4f}mm, 复查员: {reviewer}, 复查时间: {review_time}"
            
            self.data_table.setItem(row, 9, QTableWidgetItem(notes))
            
        # 调整列宽 - 按照重构前的实现
        self.data_table.resizeColumnsToContents()
        
    def clear_data(self):
        """清除表格数据"""
        self.measurements_data = []
        self.data_table.setRowCount(0)
        
    def get_selected_row(self):
        """获取当前选中的行"""
        current_row = self.data_table.currentRow()
        return current_row if current_row >= 0 else None
        
    def get_measurement_at_row(self, row):
        """获取指定行的测量数据"""
        if 0 <= row < len(self.measurements_data):
            return self.measurements_data[row]
        return None
        
    def get_all_measurements(self):
        """获取所有测量数据"""
        return self.measurements_data.copy()
        
    def export_data_to_csv(self, file_path):
        """导出数据到CSV文件 - 按照重构前的格式"""
        import csv
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = [
                    "序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", 
                    "通道3值(μm)", "合格", "时间", "操作员", "备注"
                ]
                writer.writerow(headers)
                
                # 写入数据
                for row in range(self.data_table.rowCount()):
                    row_data = []
                    for col in range(self.data_table.columnCount()):
                        item = self.data_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                    
            return True
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return False
            
    def get_statistics(self):
        """获取数据统计信息 - 按照重构前的实现"""
        if not self.measurements_data:
            return {}
            
        diameters = [m.get('diameter', 0) for m in self.measurements_data]
        qualified_count = sum(1 for m in self.measurements_data if m.get('is_qualified', True))
        total_count = len(self.measurements_data)
        
        stats = {
            'total_count': total_count,
            'qualified_count': qualified_count,
            'unqualified_count': total_count - qualified_count,
            'qualification_rate': (qualified_count / total_count * 100) if total_count > 0 else 0,
            'max_diameter': max(diameters) if diameters else 0,
            'min_diameter': min(diameters) if diameters else 0,
            'avg_diameter': sum(diameters) / len(diameters) if diameters else 0
        }
        
        return stats
