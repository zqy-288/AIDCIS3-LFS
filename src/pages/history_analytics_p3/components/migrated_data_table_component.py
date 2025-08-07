"""
迁移的数据表格组件 - 高内聚
直接从重构前代码迁移，专门负责测量数据的表格显示
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from datetime import datetime


class MigratedDataTableComponent(QWidget):
    """
    迁移的数据表格组件 - 高内聚设计
    职责：专门负责测量数据的表格显示
    直接从重构前的 create_data_table 方法迁移而来
    """
    
    # 信号定义 - 低耦合通信
    row_double_clicked = Signal(int, dict)  # 行双击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements = []
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 直接从重构前代码迁移"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建数据表格分组
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
        
        # 创建表格 - 直接从重构前迁移
        self.data_table = QTableWidget()
        self.data_table.verticalHeader().setVisible(False)  # 隐藏左侧的行号表头
        self.data_table.setColumnCount(10)  # 10列完整结构
        self.data_table.setHorizontalHeaderLabels([
            "序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员", "备注"
        ])
        
        # 设置表格样式 - 直接从重构前迁移
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
                font-size: 10px;
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
        
        # 设置表格属性 - 直接从重构前迁移
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSortingEnabled(True)
        
        # 禁用表格编辑
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置行高和最小高度
        self.data_table.verticalHeader().setDefaultSectionSize(25)
        self.data_table.setMinimumHeight(300)
        
        # 连接双击事件 - 直接从重构前迁移
        self.data_table.cellDoubleClicked.connect(self.on_table_double_clicked)
        
        table_layout.addWidget(self.data_table)
        layout.addWidget(table_group)
        
    def load_measurements(self, measurements):
        """加载测量数据到表格 - 直接从重构前代码迁移"""
        if not measurements:
            self.clear_table()
            return
            
        self.measurements = measurements
        print(f"📊 开始加载 {len(measurements)} 条测量数据到表格")
        
        self.data_table.setRowCount(len(measurements))
        
        for row, measurement in enumerate(measurements):
            self.populate_row(row, measurement)
            
        # 调整列宽 - 直接从重构前迁移
        self.data_table.resizeColumnsToContents()
        
        print(f"✅ 成功加载 {len(measurements)} 条数据到表格")
        
    def populate_row(self, row, measurement):
        """填充表格行数据 - 直接从重构前代码迁移的逻辑"""
        # 序号
        sequence = measurement.get('sequence', row + 1)
        self.data_table.setItem(row, 0, QTableWidgetItem(str(sequence)))
        
        # 位置
        position = measurement.get('position', measurement.get('depth', 0))
        self.data_table.setItem(row, 1, QTableWidgetItem(f"{position:.1f}"))
        
        # 直径 - 根据合格性设置颜色
        diameter = measurement.get('diameter', 0)
        diameter_item = QTableWidgetItem(f"{diameter:.4f}")
        if not measurement.get('is_qualified', True):
            # 不合格数据用红色背景显示
            diameter_item.setBackground(QColor(255, 0, 0))  # 红色背景
            diameter_item.setForeground(QColor(255, 255, 255))  # 白色文字
        self.data_table.setItem(row, 2, diameter_item)
        
        # 通道值 - 直接从重构前迁移
        channel1 = measurement.get('channel1', 0)
        channel2 = measurement.get('channel2', 0)
        channel3 = measurement.get('channel3', 0)
        self.data_table.setItem(row, 3, QTableWidgetItem(f"{channel1:.1f}"))
        self.data_table.setItem(row, 4, QTableWidgetItem(f"{channel2:.1f}"))
        self.data_table.setItem(row, 5, QTableWidgetItem(f"{channel3:.1f}"))
        
        # 合格状态
        is_qualified = measurement.get('is_qualified', True)
        qualified_text = "合格" if is_qualified else "不合格"
        qualified_item = QTableWidgetItem(qualified_text)
        if not is_qualified:
            qualified_item.setBackground(QColor(255, 0, 0))  # 红色背景
            qualified_item.setForeground(QColor(255, 255, 255))  # 白色文字
        self.data_table.setItem(row, 6, qualified_item)
        
        # 时间
        timestamp = measurement.get('timestamp', '')
        if not timestamp and 'time' in measurement:
            timestamp = measurement['time']
        self.data_table.setItem(row, 7, QTableWidgetItem(str(timestamp)))
        
        # 操作员
        operator = measurement.get('operator', '')
        if not operator and 'user' in measurement:
            operator = measurement['user']
        self.data_table.setItem(row, 8, QTableWidgetItem(str(operator)))
        
        # 备注
        notes = measurement.get('notes', measurement.get('remark', ''))
        self.data_table.setItem(row, 9, QTableWidgetItem(str(notes)))
        
    def clear_table(self):
        """清空表格数据"""
        self.data_table.setRowCount(0)
        self.measurements = []
        print("📊 表格数据已清空")
        
    def on_table_double_clicked(self, row, column):
        """表格双击事件处理 - 直接从重构前迁移"""
        if row < len(self.measurements):
            measurement = self.measurements[row]
            print(f"📊 双击表格行 {row}: 位置 {measurement.get('position', 0):.1f}mm")
            self.row_double_clicked.emit(row, measurement)
            
    def get_selected_measurement(self):
        """获取当前选择的测量数据"""
        current_row = self.data_table.currentRow()
        if 0 <= current_row < len(self.measurements):
            return self.measurements[current_row]
        return None
        
    def get_all_measurements(self):
        """获取所有测量数据"""
        return self.measurements
        
    def get_unqualified_measurements(self):
        """获取不合格的测量数据"""
        unqualified = []
        for i, measurement in enumerate(self.measurements):
            if not measurement.get('is_qualified', True):
                unqualified.append((i, measurement))
        return unqualified
        
    def update_measurement_at_row(self, row, updated_measurement):
        """更新指定行的测量数据"""
        if 0 <= row < len(self.measurements):
            self.measurements[row] = updated_measurement
            self.populate_row(row, updated_measurement)
            print(f"📊 更新表格行 {row} 的数据")
            
    def get_statistics(self):
        """获取数据统计信息"""
        if not self.measurements:
            return {}
            
        diameters = [m.get('diameter', 0) for m in self.measurements]
        qualified_count = sum(1 for m in self.measurements if m.get('is_qualified', True))
        
        import numpy as np
        
        return {
            'total_count': len(self.measurements),
            'qualified_count': qualified_count,
            'unqualified_count': len(self.measurements) - qualified_count,
            'pass_rate': (qualified_count / len(self.measurements)) * 100,
            'mean_diameter': np.mean(diameters),
            'std_diameter': np.std(diameters),
            'min_diameter': np.min(diameters),
            'max_diameter': np.max(diameters)
        }
        
    def highlight_unqualified_data(self):
        """高亮显示不合格数据 - 重构前功能"""
        for row in range(self.data_table.rowCount()):
            if row < len(self.measurements):
                measurement = self.measurements[row]
                if not measurement.get('is_qualified', True):
                    # 整行高亮
                    for col in range(self.data_table.columnCount()):
                        item = self.data_table.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 100, 100, 100))  # 淡红色背景
                            
    def export_to_csv(self, file_path):
        """导出表格数据到CSV - 直接从重构前代码迁移"""
        import csv
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头 - 直接从重构前迁移
                headers = ["序号", "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员", "备注"]
                writer.writerow(headers)
                
                # 写入数据 - 直接从重构前迁移
                for measurement in self.measurements:
                    row = [
                        measurement.get('sequence', ''),
                        f"{measurement.get('position', 0):.1f}",
                        f"{measurement.get('diameter', 0):.4f}",
                        f"{measurement.get('channel1', 0):.1f}",
                        f"{measurement.get('channel2', 0):.1f}",
                        f"{measurement.get('channel3', 0):.1f}",
                        "合格" if measurement.get('is_qualified', True) else "不合格",
                        measurement.get('timestamp', ''),
                        measurement.get('operator', ''),
                        measurement.get('notes', '')
                    ]
                    writer.writerow(row)
                    
            print(f"✅ 表格数据导出成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 表格数据导出失败: {e}")
            return False


if __name__ == "__main__":
    # 测试组件
    from PySide6.QtWidgets import QApplication
    import sys
    import numpy as np
    
    app = QApplication(sys.argv)
    
    # 创建测试数据
    test_measurements = []
    base_diameter = 17.73
    
    for i in range(50):
        position = i * 8.36
        diameter = base_diameter + np.random.normal(0, 0.02)
        
        measurement = {
            'sequence': i + 1,
            'position': position,
            'depth': position,
            'diameter': diameter,
            'channel1': diameter * 1000 + np.random.normal(0, 10),
            'channel2': diameter * 1000 + np.random.normal(0, 10),
            'channel3': diameter * 1000 + np.random.normal(0, 10),
            'is_qualified': abs(diameter - base_diameter) <= 0.06,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'operator': '操作员A',
            'notes': f'测试数据{i+1}'
        }
        test_measurements.append(measurement)
    
    # 创建并测试组件
    table_component = MigratedDataTableComponent()
    table_component.load_measurements(test_measurements)
    table_component.show()
    
    print("测试数据统计:", table_component.get_statistics())
    
    sys.exit(app.exec())