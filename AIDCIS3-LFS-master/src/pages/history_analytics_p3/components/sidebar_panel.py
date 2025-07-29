"""
侧边栏面板组件
基于重构前的HistoryViewer侧边栏实现
"""

import csv
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QGroupBox, QToolButton, QMenu, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from .scrollable_text_label import ScrollableTextLabel
from .manual_review_dialog import ManualReviewDialog


class SidebarPanel(QWidget):
    """
    侧边栏面板 - 完全按照重构前的设计
    包含数据筛选、操作命令、当前状态显示
    """
    
    # 信号定义
    workpiece_selected = Signal(str)  # 工件选择信号
    qualified_hole_selected = Signal(str)  # 合格孔选择信号
    unqualified_hole_selected = Signal(str)  # 不合格孔选择信号
    query_requested = Signal()  # 查询数据信号
    export_requested = Signal()  # 导出数据信号
    manual_review_requested = Signal()  # 人工复查信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据存储
        self.workpiece_data = []
        self.qualified_holes_data = []
        self.unqualified_holes_data = []
        self.current_workpiece = ""
        self.current_qualified_hole = ""
        self.current_unqualified_hole = ""

        # 当前孔位数据 - 用于按钮功能
        self.current_hole_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 完全按照重构前的布局"""
        self.setObjectName("Sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(25)  # 按照重构前的间距
        
        # 标题 - 按照重构前的样式
        title_label = QLabel("光谱共焦历史数据查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("HistoryViewerTitle")
        layout.addWidget(title_label)
        
        # 数据筛选部分 - 按照重构前的设计
        self.create_filter_section(layout)
        
        # 添加弹性空间
        layout.addStretch(1)
        
        # 操作命令部分 - 按照重构前的设计
        self.create_action_section(layout)
        
        # 添加弹性空间
        layout.addStretch(1)
        
        # 当前状态部分 - 按照重构前的设计
        self.create_status_section(layout)
        
    def create_filter_section(self, parent_layout):
        """创建数据筛选部分 - 按照重构前的精确布局"""
        filter_group = QGroupBox("数据筛选")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(10, 15, 10, 15)
        filter_layout.setSpacing(15)  # 按照重构前的间距
        
        # 工件ID筛选
        workpiece_label = QLabel("工件ID:")
        workpiece_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wp_display = ScrollableTextLabel()
        self.wp_display.setPlaceholderText("请选择工件ID")
        self.wp_button = QToolButton()
        self.wp_button.setText("▼")
        self.wp_button.setMinimumWidth(30)
        self.wp_button.setStyleSheet(self.get_button_style())
        self.wp_button.clicked.connect(self.show_workpiece_menu)
        
        # 工件ID布局
        wp_combo_layout = QHBoxLayout()
        wp_combo_layout.setSpacing(0)
        wp_combo_layout.setContentsMargins(0, 0, 0, 0)
        wp_combo_layout.addWidget(self.wp_display)
        wp_combo_layout.addWidget(self.wp_button)
        
        # 合格孔ID筛选
        qualified_label = QLabel("合格孔ID:")
        qualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ql_display = ScrollableTextLabel()
        self.ql_display.setPlaceholderText("请选择合格孔ID")
        self.ql_button = QToolButton()
        self.ql_button.setText("▼")
        self.ql_button.setMinimumWidth(30)
        self.ql_button.setStyleSheet(self.get_button_style())
        self.ql_button.clicked.connect(self.show_qualified_hole_menu)
        
        # 合格孔ID布局
        ql_combo_layout = QHBoxLayout()
        ql_combo_layout.setSpacing(0)
        ql_combo_layout.setContentsMargins(0, 0, 0, 0)
        ql_combo_layout.addWidget(self.ql_display)
        ql_combo_layout.addWidget(self.ql_button)
        
        # 不合格孔ID筛选
        unqualified_label = QLabel("不合格孔ID:")
        unqualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.uql_display = ScrollableTextLabel()
        self.uql_display.setPlaceholderText("请选择不合格孔ID")
        self.uql_button = QToolButton()
        self.uql_button.setText("▼")
        self.uql_button.setMinimumWidth(30)
        self.uql_button.setStyleSheet(self.get_button_style())
        self.uql_button.clicked.connect(self.show_unqualified_hole_menu)
        
        # 不合格孔ID布局
        uql_combo_layout = QHBoxLayout()
        uql_combo_layout.setSpacing(0)
        uql_combo_layout.setContentsMargins(0, 0, 0, 0)
        uql_combo_layout.addWidget(self.uql_display)
        uql_combo_layout.addWidget(self.uql_button)
        
        # 添加到网格布局 - 按照重构前的布局
        filter_layout.addWidget(workpiece_label, 0, 0)
        filter_layout.addLayout(wp_combo_layout, 0, 1)
        filter_layout.addWidget(qualified_label, 1, 0)
        filter_layout.addLayout(ql_combo_layout, 1, 1)
        filter_layout.addWidget(unqualified_label, 2, 0)
        filter_layout.addLayout(uql_combo_layout, 2, 1)
        
        filter_layout.setColumnStretch(1, 1)
        parent_layout.addWidget(filter_group)
        
    def create_action_section(self, parent_layout):
        """创建操作命令部分 - 按照重构前的设计"""
        action_group = QGroupBox("操作命令")
        action_layout = QVBoxLayout(action_group)
        action_layout.setSpacing(18)  # 按照重构前的间距
        
        # 查询数据按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.clicked.connect(self.query_data)
        action_layout.addWidget(self.query_button)

        # 导出数据按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        action_layout.addWidget(self.export_button)

        # 人工复查按钮
        self.manual_review_button = QPushButton("人工复查")
        self.manual_review_button.clicked.connect(self.open_manual_review)
        action_layout.addWidget(self.manual_review_button)
        
        parent_layout.addWidget(action_group)
        
    def create_status_section(self, parent_layout):
        """创建当前状态部分 - 按照重构前的设计"""
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout(status_group)
        
        self.current_hole_label = QLabel("当前管孔: --")
        self.current_hole_label.setObjectName("CurrentHoleLabel")
        status_layout.addWidget(self.current_hole_label)
        
        parent_layout.addWidget(status_group)
        
    def get_button_style(self):
        """获取按钮样式 - 按照重构前的样式"""
        return """
            QToolButton {
                border: 1px solid #505869;
                background-color: #2a2d35;
                color: #D3D8E0;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #3a3d45;
            }
            QToolButton:pressed {
                background-color: #1a1d25;
            }
        """
        
    def get_menu_style(self):
        """获取菜单样式 - 按照重构前的样式"""
        return """
            QMenu {
                background-color: #2a2d35;
                color: #D3D8E0;
                border: 1px solid #505869;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3a3d45;
            }
        """

    def show_workpiece_menu(self):
        """显示工件选择菜单 - 按照重构前的实现"""
        menu = QMenu(self)
        menu.setStyleSheet(self.get_menu_style())

        for item_text in self.workpiece_data:
            action = QAction(item_text, self)
            action.triggered.connect(lambda checked=False, text=item_text: self.select_workpiece(text))
            menu.addAction(action)

        if not self.workpiece_data:
            action = QAction("暂无数据", self)
            action.setEnabled(False)
            menu.addAction(action)

        menu.exec(self.wp_button.mapToGlobal(self.wp_button.rect().bottomLeft()))

    def show_qualified_hole_menu(self):
        """显示合格孔选择菜单 - 按照重构前的实现"""
        menu = QMenu(self)
        menu.setStyleSheet(self.get_menu_style())

        for item_text in self.qualified_holes_data:
            action = QAction(item_text, self)
            action.triggered.connect(lambda checked=False, text=item_text: self.select_qualified_hole(text))
            menu.addAction(action)

        if not self.qualified_holes_data:
            action = QAction("暂无数据", self)
            action.setEnabled(False)
            menu.addAction(action)

        menu.exec(self.ql_button.mapToGlobal(self.ql_button.rect().bottomLeft()))

    def show_unqualified_hole_menu(self):
        """显示不合格孔选择菜单 - 按照重构前的实现"""
        menu = QMenu(self)
        menu.setStyleSheet(self.get_menu_style())

        for item_text in self.unqualified_holes_data:
            action = QAction(item_text, self)
            action.triggered.connect(lambda checked=False, text=item_text: self.select_unqualified_hole(text))
            menu.addAction(action)

        if not self.unqualified_holes_data:
            action = QAction("暂无数据", self)
            action.setEnabled(False)
            menu.addAction(action)

        menu.exec(self.uql_button.mapToGlobal(self.uql_button.rect().bottomLeft()))

    def select_workpiece(self, workpiece_id):
        """选择工件"""
        self.current_workpiece = workpiece_id
        self.wp_display.setText(workpiece_id)
        self.workpiece_selected.emit(workpiece_id)

    def select_qualified_hole(self, hole_id):
        """选择合格孔"""
        self.current_qualified_hole = hole_id
        self.ql_display.setText(hole_id)
        self.qualified_hole_selected.emit(hole_id)

    def select_unqualified_hole(self, hole_id):
        """选择不合格孔"""
        self.current_unqualified_hole = hole_id
        self.uql_display.setText(hole_id)
        self.unqualified_hole_selected.emit(hole_id)

    def update_workpiece_data(self, workpiece_list):
        """更新工件数据"""
        self.workpiece_data = workpiece_list

    def update_qualified_holes_data(self, holes_list):
        """更新合格孔数据"""
        self.qualified_holes_data = holes_list

    def update_unqualified_holes_data(self, holes_list):
        """更新不合格孔数据"""
        self.unqualified_holes_data = holes_list

    def update_current_hole_status(self, hole_info):
        """更新当前管孔状态显示"""
        if hole_info:
            self.current_hole_label.setText(f"当前管孔: {hole_info}")
        else:
            self.current_hole_label.setText("当前管孔: --")

    def clear_selections(self):
        """清除所有选择"""
        self.current_workpiece = ""
        self.current_qualified_hole = ""
        self.current_unqualified_hole = ""
        self.wp_display.setText("")
        self.ql_display.setText("")
        self.uql_display.setText("")
        self.current_hole_label.setText("当前管孔: --")

    def get_current_hole_id(self):
        """获取当前选择的孔位ID"""
        if self.current_qualified_hole:
            return self.current_qualified_hole
        elif self.current_unqualified_hole:
            return self.current_unqualified_hole
        return ""

    def set_current_hole_data(self, hole_data):
        """设置当前孔位数据 - 用于按钮功能"""
        self.current_hole_data = hole_data

    def query_data(self):
        """查询数据 - 完全按照重构前的实现"""
        print("🔍 开始查询数据...")

        # 获取选择的参数
        workpiece_id = self.current_workpiece
        qualified_hole_id = self.current_qualified_hole
        unqualified_hole_id = self.current_unqualified_hole

        # 确定要查询的孔位ID
        hole_id = ""
        if qualified_hole_id and qualified_hole_id != "请选择合格孔ID":
            hole_id = qualified_hole_id
        elif unqualified_hole_id and unqualified_hole_id != "请选择不合格孔ID":
            hole_id = unqualified_hole_id

        print(f"📋 查询参数: 工件ID='{workpiece_id}', 合格孔ID='{qualified_hole_id}', 不合格孔ID='{unqualified_hole_id}', 选择的孔ID='{hole_id}'")

        if not workpiece_id:
            print("❌ 工件ID未选择")
            QMessageBox.warning(self, "警告", "请选择工件ID")
            return

        if not hole_id:
            print("❌ 孔ID未选择")
            QMessageBox.warning(self, "警告", "请选择合格孔ID或不合格孔ID")
            return

        # 验证孔ID格式（应该是RxxxCxxx格式）
        if not self.is_valid_hole_id(hole_id):
            print("❌ 孔ID格式错误")
            QMessageBox.warning(self, "警告", "孔ID格式错误，请输入RxxxCxxx格式的孔ID")
            return

        # 发射查询信号，让主页面处理具体的数据加载
        self.query_requested.emit()

    def is_valid_hole_id(self, hole_id):
        """验证孔位ID格式是否为RxxxCxxx"""
        import re
        pattern = r'^R\d+C\d+$'
        return re.match(pattern, hole_id) is not None

    def export_data(self):
        """导出数据到CSV文件 - 完全按照重构前的实现"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询数据后再导出")
            return

        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出测量数据",
            f"{self.current_hole_data['hole_id']}_测量数据.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if not file_path:
            return

        try:
            measurements = self.current_hole_data['measurements']
            workpiece_id = self.current_hole_data['workpiece_id']
            hole_id = self.current_hole_data['hole_id']

            # 计算统计信息 - 按照重构前的逻辑
            diameters = [m['diameter'] for m in measurements]
            standard_diameter = 17.6
            upper_tolerance = 0.05
            lower_tolerance = 0.07

            qualified_count = sum(1 for d in diameters
                                if standard_diameter - lower_tolerance <= d <= standard_diameter + upper_tolerance)
            total_count = len(diameters)
            qualification_rate = qualified_count / total_count * 100 if total_count > 0 else 0

            max_diameter = max(diameters) if diameters else 0
            min_diameter = min(diameters) if diameters else 0
            avg_diameter = sum(diameters) / len(diameters) if diameters else 0

            # 写入CSV文件 - 按照重构前的格式
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # 写入统计信息头部
                writer.writerow(['测量数据统计信息'])
                writer.writerow(['工件ID', workpiece_id])
                writer.writerow(['孔位ID', hole_id])
                writer.writerow(['标准直径(mm)', standard_diameter])
                writer.writerow(['公差范围(mm)', f'-{lower_tolerance}~+{upper_tolerance}'])
                writer.writerow(['最大直径(mm)', f'{max_diameter:.4f}'])
                writer.writerow(['最小直径(mm)', f'{min_diameter:.4f}'])
                writer.writerow(['平均直径(mm)', f'{avg_diameter:.4f}'])
                writer.writerow(['合格率', f'{qualified_count}/{total_count} ({qualification_rate:.1f}%)'])
                writer.writerow([])  # 空行分隔

                # 写入测量数据表头
                writer.writerow(['位置(mm)', '直径(mm)', '通道1值(μm)', '通道2值(μm)', '通道3值(μm)', '合格', '时间', '操作员', '备注'])

                # 写入测量数据
                for i, measurement in enumerate(measurements):
                    diameter = measurement['diameter']
                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)
                    qualified_text = '✓' if is_qualified else '✗'

                    # 检查是否有人工复查值
                    notes = ""
                    if 'manual_review_value' in measurement:
                        notes = f"人工复查值: {measurement['manual_review_value']:.4f}mm"
                        if 'reviewer' in measurement:
                            notes += f", 复查员: {measurement['reviewer']}"
                        if 'review_time' in measurement:
                            notes += f", 复查时间: {measurement['review_time']}"

                    # 获取位置信息
                    position = measurement.get('position', measurement.get('depth', 0))

                    # 时间格式化
                    timestamp = measurement.get('timestamp', '')
                    if timestamp:
                        time_str = timestamp.strftime("%H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp)
                    else:
                        time_str = "--"

                    # 操作员信息
                    operator = measurement.get('operator', '--')

                    writer.writerow([
                        f"{position:.1f}",
                        f"{diameter:.4f}",
                        f"{measurement.get('channel1', 0):.2f}",
                        f"{measurement.get('channel2', 0):.2f}",
                        f"{measurement.get('channel3', 0):.2f}",
                        qualified_text,
                        time_str,
                        operator,
                        notes
                    ])

            QMessageBox.information(self, "成功", f"数据已成功导出到:\n{file_path}")

            # 发射导出信号
            self.export_requested.emit()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出数据失败:\n{str(e)}")

    def open_manual_review(self):
        """打开人工复查窗口 - 完全按照重构前的实现"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "请先查询数据后再进行人工复查")
            return

        # 检查是否有不合格数据
        measurements = self.current_hole_data['measurements']
        standard_diameter = 17.6
        upper_tolerance = 0.05
        lower_tolerance = 0.07

        unqualified_measurements = []
        for i, measurement in enumerate(measurements):
            diameter = measurement['diameter']
            if not (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance):
                unqualified_measurements.append((i, measurement))

        if not unqualified_measurements:
            QMessageBox.information(self, "信息", "当前数据中没有不合格的测量值，无需人工复查")
            return

        # 打开人工复查对话框
        dialog = ManualReviewDialog(unqualified_measurements, self)
        if dialog.exec() == QMessageBox.Accepted:
            # 获取复查结果并更新数据
            review_results = dialog.get_review_results()
            self.apply_manual_review_results(review_results)

    def apply_manual_review_results(self, review_results):
        """应用人工复查结果 - 完全按照重构前的实现"""
        if not self.current_hole_data:
            return

        measurements = self.current_hole_data['measurements']
        updated_count = 0

        for index, review_data in review_results.items():
            if index < len(measurements):
                measurements[index]['manual_review_value'] = review_data['diameter']
                measurements[index]['reviewer'] = review_data['reviewer']
                measurements[index]['review_time'] = review_data['review_time']
                updated_count += 1

        if updated_count > 0:
            QMessageBox.information(self, "成功", f"已更新 {updated_count} 条人工复查记录")

            # 发射人工复查信号，让主页面更新显示
            self.manual_review_requested.emit()
