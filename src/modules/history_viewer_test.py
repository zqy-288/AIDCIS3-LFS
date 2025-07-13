"""
测试版本的历史数据查看器 - 不使用pandas
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
import os
import csv
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QTextEdit, QMessageBox, QCompleter,
                               QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
                               QFileDialog, QHeaderView, QScrollArea)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.optimize import least_squares

from .models import db_manager


class ManualReviewDialog(QDialog):
    """人工复查对话框"""
    
    def __init__(self, hole_id, measurements, parent=None):
        super().__init__(parent)
        self.hole_id = hole_id
        self.measurements = measurements
        self.manual_values = {}  # 存储人工复查值
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle(f"人工复查 - {self.hole_id}")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明文本
        info_label = QLabel("对于判为不合格的测量点，您可以录入人工复检的直径值：")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 为每个不合格的测量点创建输入框
        self.input_widgets = {}
        for i, measurement in enumerate(self.measurements):
            position = measurement.get('position', i + 1)
            diameter = measurement.get('diameter', 0)
            is_qualified = measurement.get('qualified', True)
            
            # 只为不合格的点创建输入框
            if not is_qualified:
                group = QGroupBox(f"位置 {position}mm")
                group_layout = QFormLayout(group)
                
                # 显示原始直径
                original_label = QLabel(f"原始直径: {diameter:.4f}mm")
                group_layout.addRow("", original_label)
                
                # 人工复查输入框
                manual_input = QDoubleSpinBox()
                manual_input.setRange(10.0, 25.0)  # 设置合理的直径范围
                manual_input.setDecimals(4)
                manual_input.setSuffix(" mm")
                manual_input.setValue(diameter)  # 默认值为原始直径
                
                group_layout.addRow("人工复查直径:", manual_input)
                
                self.input_widgets[position] = manual_input
                scroll_layout.addWidget(group)
        
        if not self.input_widgets:
            no_data_label = QLabel("该孔位所有测量点均合格，无需人工复查。")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            scroll_layout.addWidget(no_data_label)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_manual_values(self):
        """获取人工复查值"""
        result = {}
        for position, widget in self.input_widgets.items():
            result[position] = widget.value()
        return result


class HistoryViewer(QWidget):
    """历史数据查看器 - 测试版本"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_data = None
        self.manual_review_data = {}  # 存储人工复查数据
        self.standard_diameter = 17.6  # 标准直径
        self.upper_tolerance = 0.05  # 上公差 (+0.05mm)
        self.lower_tolerance = 0.07  # 下公差 (-0.07mm)
        self.setup_ui()
        self.load_workpiece_data()  # 加载工件数据
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 查询面板
        self.create_query_panel(layout)
        
        # 数据表格
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
        
    def create_query_panel(self, layout):
        """创建查询面板"""
        query_group = QGroupBox("查询条件")
        query_layout = QGridLayout(query_group)
        
        # 设置更紧凑的布局间距
        query_layout.setHorizontalSpacing(8)   # 设置水平间距为8像素
        query_layout.setVerticalSpacing(10)    # 设置垂直间距为10像素
        query_layout.setContentsMargins(10, 15, 10, 10)  # 设置边距

        # 工件ID
        workpiece_label = QLabel("工件ID:")
        workpiece_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        query_layout.addWidget(workpiece_label, 0, 0)
        self.workpiece_combo = QComboBox()
        self.workpiece_combo.setFixedWidth(150)  # 设置固定宽度
        query_layout.addWidget(self.workpiece_combo, 0, 1)

        # 合格管孔选择
        qualified_label = QLabel("合格管孔:")
        qualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        query_layout.addWidget(qualified_label, 0, 2)
        self.qualified_hole_combo = QComboBox()
        self.qualified_hole_combo.setFixedWidth(120)  # 设置固定宽度
        self.qualified_hole_combo.setPlaceholderText("选择合格管孔")
        query_layout.addWidget(self.qualified_hole_combo, 0, 3)

        # 不合格管孔选择
        unqualified_label = QLabel("不合格管孔:")
        unqualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        query_layout.addWidget(unqualified_label, 0, 4)
        self.unqualified_hole_combo = QComboBox()
        self.unqualified_hole_combo.setFixedWidth(120)  # 设置固定宽度
        self.unqualified_hole_combo.setPlaceholderText("选择不合格管孔")
        query_layout.addWidget(self.unqualified_hole_combo, 0, 5)

        # 查询按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.setFixedSize(80, 30)  # 设置固定大小
        self.query_button.clicked.connect(self.query_hole_data)
        query_layout.addWidget(self.query_button, 0, 6)

        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.setFixedSize(80, 30)  # 设置固定大小
        self.export_button.clicked.connect(self.export_data)
        query_layout.addWidget(self.export_button, 0, 7)

        # 人工复查按钮
        self.manual_review_button = QPushButton("人工复查")
        self.manual_review_button.setFixedSize(80, 30)  # 设置固定大小
        self.manual_review_button.clicked.connect(self.open_manual_review)
        query_layout.addWidget(self.manual_review_button, 0, 8)

        # 当前选择的孔ID显示
        current_hole_id_label = QLabel("当前孔ID:")
        current_hole_id_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        query_layout.addWidget(current_hole_id_label, 0, 9)
        self.current_hole_label = QLabel("未选择")
        self.current_hole_label.setStyleSheet("font-weight: bold; color: #2E7D32;")
        query_layout.addWidget(self.current_hole_label, 0, 10)

        # 添加弹性空间，让控件靠左对齐
        query_layout.setColumnStretch(11, 1)

        layout.addWidget(query_group)
    
    def open_manual_review(self):
        """打开人工复查窗口"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询孔位数据")
            return
            
        hole_id = self.current_hole_data['hole_id']
        measurements = self.current_hole_data['measurements']
        
        # 创建人工复查对话框
        dialog = ManualReviewDialog(hole_id, measurements, self)
        if dialog.exec() == QDialog.Accepted:
            manual_values = dialog.get_manual_values()
            if manual_values:
                # 存储人工复查数据
                if hole_id not in self.manual_review_data:
                    self.manual_review_data[hole_id] = {}
                self.manual_review_data[hole_id].update(manual_values)
                
                QMessageBox.information(self, "成功", f"已保存 {len(manual_values)} 个人工复查值")
                print(f"✅ 保存人工复查数据: {hole_id} -> {manual_values}")
            else:
                QMessageBox.information(self, "提示", "未录入任何人工复查值")
    
    def export_data(self):
        """导出数据到CSV文件"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询孔位数据")
            return
            
        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出测量数据",
            f"测量数据_{self.current_hole_data['hole_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            self._export_to_csv(file_path)
            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")
    
    def _export_to_csv(self, file_path):
        """执行CSV导出"""
        # 简化的导出实现
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['测试数据导出成功'])
            writer.writerow(['文件路径', file_path])
            writer.writerow(['导出时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        print(f"✅ 数据导出完成: {file_path}")

    def load_workpiece_data(self):
        """加载工件数据"""
        try:
            # 简化为添加默认工件
            self.workpiece_combo.clear()
            self.workpiece_combo.addItem("WP-2025-001")

            # 连接工件选择变化事件
            self.workpiece_combo.currentTextChanged.connect(self.on_workpiece_changed)

            # 自动加载第一个工件
            self.on_workpiece_changed()

        except Exception as e:
            print(f"❌ 加载工件数据失败: {e}")

    def on_workpiece_changed(self):
        """工件选择变化时的处理"""
        try:
            workpiece_id = self.workpiece_combo.currentText()
            if not workpiece_id:
                return

            # 获取可用的孔位列表（从Data目录扫描）
            available_holes = self.get_available_holes(workpiece_id)

            # 分类合格和不合格孔位
            qualified_holes = []
            unqualified_holes = []

            for hole_id in available_holes:
                if self.is_hole_qualified(hole_id):
                    qualified_holes.append(hole_id)
                else:
                    unqualified_holes.append(hole_id)

            # 更新下拉框
            self.qualified_hole_combo.clear()
            self.qualified_hole_combo.addItems(qualified_holes)

            self.unqualified_hole_combo.clear()
            self.unqualified_hole_combo.addItems(unqualified_holes)

            # 连接孔位选择事件
            self.qualified_hole_combo.currentTextChanged.connect(self.on_hole_selected)
            self.unqualified_hole_combo.currentTextChanged.connect(self.on_hole_selected)

            print(f"✅ 工件 {workpiece_id}: 合格孔位 {len(qualified_holes)} 个，不合格孔位 {len(unqualified_holes)} 个")

        except Exception as e:
            print(f"❌ 加载孔位数据失败: {e}")

    def on_hole_selected(self):
        """孔位选择变化时的处理"""
        sender = self.sender()
        hole_id = sender.currentText()

        if hole_id:
            # 清除另一个下拉框的选择
            if sender == self.qualified_hole_combo:
                self.unqualified_hole_combo.setCurrentIndex(-1)
            else:
                self.qualified_hole_combo.setCurrentIndex(-1)

            # 更新当前孔ID显示
            self.current_hole_label.setText(hole_id)

    def query_hole_data(self):
        """查询孔位数据"""
        # 获取当前选择的孔位
        hole_id = None
        if self.qualified_hole_combo.currentText():
            hole_id = self.qualified_hole_combo.currentText()
        elif self.unqualified_hole_combo.currentText():
            hole_id = self.unqualified_hole_combo.currentText()

        if not hole_id:
            QMessageBox.warning(self, "警告", "请先选择一个孔位")
            return

        try:
            # 直接从CSV文件加载数据（与原始版本保持一致）
            measurements = self.load_csv_data_for_hole(hole_id)
            if not measurements:
                QMessageBox.warning(self, "警告", f"孔位 {hole_id} 没有测量数据")
                return

            # 保存当前孔位数据
            self.current_hole_data = {
                'hole_id': hole_id,
                'measurements': measurements
            }

            # 更新数据表格显示
            self.update_data_table(measurements)

            print(f"✅ 成功查询孔位 {hole_id} 的数据，共 {len(measurements)} 个测量点")

        except Exception as e:
            print(f"❌ 查询孔位数据失败: {e}")
            QMessageBox.critical(self, "错误", f"查询数据失败: {str(e)}")

    def update_data_table(self, measurements):
        """更新数据表格显示"""
        try:
            # 设置表格列数和行数
            self.data_table.setColumnCount(6)
            self.data_table.setRowCount(len(measurements))

            # 设置表头
            headers = ['位置(mm)', '直径(mm)', '通道值', '合格状态', '时间', '操作员']
            self.data_table.setHorizontalHeaderLabels(headers)

            # 填充数据
            for row, measurement in enumerate(measurements):
                # 位置
                self.data_table.setItem(row, 0, QTableWidgetItem(str(measurement['position'])))

                # 直径
                diameter_item = QTableWidgetItem(f"{measurement['diameter']:.4f}")
                if not measurement['qualified']:
                    diameter_item.setBackground(Qt.red)  # 不合格的用红色背景
                self.data_table.setItem(row, 1, diameter_item)

                # 通道值
                self.data_table.setItem(row, 2, QTableWidgetItem(str(measurement['channel_value'])))

                # 合格状态
                status_text = "合格" if measurement['qualified'] else "不合格"
                status_item = QTableWidgetItem(status_text)
                if not measurement['qualified']:
                    status_item.setBackground(Qt.red)
                self.data_table.setItem(row, 3, status_item)

                # 时间
                self.data_table.setItem(row, 4, QTableWidgetItem(str(measurement['timestamp'])))

                # 操作员
                self.data_table.setItem(row, 5, QTableWidgetItem(str(measurement['operator'])))

            # 调整列宽
            self.data_table.resizeColumnsToContents()

        except Exception as e:
            print(f"❌ 更新数据表格失败: {e}")

    def load_csv_data_for_hole(self, hole_id):
        """根据孔ID加载对应的CSV数据（与原始版本完全一致）"""
        # 修复路径问题：使用相对路径查找CSV文件
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]

        csv_files = []

        # 查找存在的CSV目录
        for path in csv_paths:
            if os.path.exists(path):
                # 查找CSV文件
                for csv_file in os.listdir(path):
                    if csv_file.endswith('.csv'):
                        csv_files.append(os.path.join(path, csv_file))
                if csv_files:
                    break

        if not csv_files:
            print(f"CSV数据目录不存在或无CSV文件，已检查路径: {csv_paths}")
            return []

        # 按时间排序
        csv_files.sort()

        # 选择第一个CSV文件（通常每个孔位只有一个CSV文件）
        selected_file = csv_files[0]
        print(f"为孔ID {hole_id} 选择文件: {selected_file}")

        # 读取CSV文件数据
        return self.read_csv_file(selected_file)

    def read_csv_file(self, file_path):
        """读取CSV文件并返回测量数据（与原始版本完全一致）"""
        measurements = []

        try:
            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        print(f"成功使用编码 {encoding} 读取文件")
                        print(f"CSV文件列头: {headers}")

                        # 查找列索引 - 根据实际CSV文件结构调整
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径

                        # 验证列数是否足够
                        if len(headers) < 5:
                            print(f"CSV文件列数不足: {len(headers)} < 5")
                            continue

                        # 读取数据行 - 在同一个with块中
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])

                                    # 判断是否合格（标准直径17.6mm，非对称公差+0.05/-0.07mm）
                                    standard_diameter = 17.6
                                    upper_tolerance = 0.05
                                    lower_tolerance = 0.07
                                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)

                                    # 模拟时间（基于文件修改时间）
                                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                    # 为每个数据点添加秒数偏移，正确处理分钟进位
                                    total_seconds = file_time.second + (row_num - 2)
                                    additional_minutes = total_seconds // 60
                                    new_seconds = total_seconds % 60

                                    # 计算新的分钟数，也要处理小时进位
                                    total_minutes = file_time.minute + additional_minutes
                                    additional_hours = total_minutes // 60
                                    new_minutes = total_minutes % 60

                                    # 计算新的小时数
                                    new_hours = (file_time.hour + additional_hours) % 24

                                    data_time = file_time.replace(hour=new_hours, minute=new_minutes, second=new_seconds)

                                    measurements.append({
                                        'position': position,
                                        'diameter': diameter,
                                        'channel1': channel1,
                                        'channel2': channel2,
                                        'channel3': channel3,
                                        'is_qualified': is_qualified,
                                        'qualified': is_qualified,  # 兼容性
                                        'timestamp': data_time,
                                        'operator': ''  # 暂不显示
                                    })

                            except (ValueError, IndexError) as e:
                                print(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环
                        break

                except UnicodeDecodeError:
                    continue
            else:
                print(f"无法使用任何编码读取文件: {file_path}")
                return []

        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            return []

        print(f"成功读取 {len(measurements)} 条测量数据")
        return measurements

    def get_available_holes(self, workpiece_id):
        """获取可用的孔位列表"""
        try:
            data_dir = "Data"
            if not os.path.exists(data_dir):
                print(f"❌ 数据目录不存在: {data_dir}")
                return []

            holes = []
            # 扫描Data目录下的所有H开头的文件夹
            for item in os.listdir(data_dir):
                item_path = os.path.join(data_dir, item)
                if os.path.isdir(item_path) and item.startswith('H'):
                    # 检查是否有对应的CSV文件
                    csv_file = os.path.join(item_path, "BISDM", "result", f"{item}.csv")
                    if os.path.exists(csv_file):
                        holes.append(item)

            holes.sort()  # 排序
            print(f"✅ 找到 {len(holes)} 个可用孔位: {holes}")
            return holes

        except Exception as e:
            print(f"❌ 获取可用孔位失败: {e}")
            return []

    def is_hole_qualified(self, hole_id):
        """判断管孔是否合格"""
        try:
            # 加载孔位的测量数据
            measurements = self.load_csv_data_for_hole(hole_id)
            if not measurements:
                print(f"⚠️ 孔位 {hole_id} 无测量数据")
                return False

            # 计算合格率
            qualified_count = 0
            total_count = len(measurements)

            for measurement in measurements:
                if measurement.get('qualified', False):
                    qualified_count += 1

            qualified_rate = qualified_count / total_count * 100
            print(f"📊 孔位 {hole_id} 合格率: {qualified_rate:.1f}% ({qualified_count}/{total_count})")

            # 合格率大于等于95%认为合格
            return qualified_rate >= 95.0

        except Exception as e:
            print(f"❌ 判断孔位 {hole_id} 合格性失败: {e}")
            return False
