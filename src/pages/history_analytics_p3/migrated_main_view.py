"""
迁移的主界面 - 高内聚低耦合架构
将重构前的完整功能按照职责拆分为独立组件，然后通过信号槽机制连接
保持三列布局：侧边栏 + 数据表格 + 图表区域
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
                               QMessageBox, QFileDialog, QDialog, QToolButton)
from PySide6.QtCore import Qt, Signal
from datetime import datetime
import numpy as np
import csv

# 导入迁移的组件
from .components.migrated_sidebar_component import MigratedSidebarComponent
from .components.migrated_data_table_component import MigratedDataTableComponent  
from .components.migrated_chart_component import MigratedChartComponent

# 导入真实CSV数据读取器
from .services.real_csv_reader import CSVDataController


class DataController:
    """
    数据控制器 - 高内聚设计
    职责：专门负责数据的加载、处理和管理
    从重构前的数据处理逻辑中提取而来，集成真实CSV数据读取
    """
    
    def __init__(self):
        self.current_measurements = []
        self.current_hole_id = ""
        self.workpiece_id = "CAP1000"
        
        # 创建真实CSV数据控制器
        self.csv_controller = CSVDataController()
        
        # 验证数据访问
        self.data_access_info = self.csv_controller.verify_data_access()
        print(f"📁 数据访问验证: {self.data_access_info}")
        
    def load_real_data(self, hole_id: str):
        """加载真实CSV数据"""
        print(f"📊 尝试加载真实数据: {hole_id}")
        
        measurements, statistics = self.csv_controller.query_hole_data(hole_id)
        
        if measurements:
            self.current_measurements = measurements
            self.current_hole_id = hole_id
            print(f"✅ 成功加载真实数据: {len(measurements)} 条记录")
            return measurements
        else:
            print(f"❌ 未找到孔位 {hole_id} 的真实数据")
            return []
            
        
    def get_current_data(self):
        """获取当前数据"""
        return self.current_measurements, self.current_hole_id
        
    def get_statistics(self):
        """获取数据统计信息"""
        if not self.current_measurements:
            return {}
            
        diameters = [m['diameter'] for m in self.current_measurements]
        qualified_count = sum(1 for m in self.current_measurements if m['is_qualified'])
        
        return {
            'hole_id': self.current_hole_id,
            'total_count': len(self.current_measurements),
            'qualified_count': qualified_count,
            'unqualified_count': len(self.current_measurements) - qualified_count,
            'pass_rate': (qualified_count / len(self.current_measurements)) * 100,
            'mean_diameter': np.mean(diameters),
            'std_diameter': np.std(diameters),
            'min_diameter': np.min(diameters),
            'max_diameter': np.max(diameters)
        }
        


class MigratedMainView(QWidget):
    """
    迁移的主界面 - 高内聚低耦合架构
    职责：
    1. 组装和协调各个迁移的组件
    2. 管理组件间的信号连接（低耦合通信）
    3. 提供统一的外部接口
    4. 保持重构前的三列布局结构
    """
    
    # 对外信号
    interface_ready = Signal()
    data_loaded = Signal(str, int)  # hole_id, data_count
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建数据控制器
        self.data_controller = DataController()
        
        # 查询状态标志
        self.is_querying = False
        
        # 初始化组件
        self.init_components()
        
        # 设置界面布局
        self.setup_ui()
        
        # 连接组件间的信号 - 低耦合通信
        self.connect_signals()
        
        print("✅ 迁移的主界面初始化完成")
        self.interface_ready.emit()
        
    def init_components(self):
        """初始化各个迁移的组件"""
        # 创建迁移的组件实例
        self.sidebar_component = MigratedSidebarComponent()
        self.data_table_component = MigratedDataTableComponent()
        self.chart_component = MigratedChartComponent()
        
        # 加载真实的孔位列表
        self.load_real_hole_list()
        
        print("📦 迁移组件初始化完成")
        
    def load_real_hole_list(self):
        """加载真实的孔位列表"""
        try:
            available_holes = self.data_controller.csv_controller.get_available_holes()
            print(f"📁 发现 {len(available_holes)} 个真实数据孔位")
            
            if available_holes:
                # 侧边栏组件会自己处理孔位分类和加载
                print("✅ 孔位列表将由侧边栏组件根据数据质量自动分类")
            else:
                print("⚠️ 未找到任何真实数据文件，请检查数据路径")
                
        except Exception as e:
            print(f"❌ 加载真实孔位列表失败: {e}")
        
    def setup_ui(self):
        """设置界面布局 - 保持重构前的三列结构并添加侧边栏隐藏功能"""
        # 主水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 第一列：左侧侧边栏（数据筛选和操作）- 直接从重构前迁移
        main_layout.addWidget(self.sidebar_component)
        
        # 创建侧边栏隐藏/显示按钮 - 直接从重构前迁移  
        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("SidebarToggleButton")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)  # 默认展开
        self.toggle_button.setArrowType(Qt.LeftArrow)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                background-color: #3a3d45;
                border: 1px solid #505869;
                color: #D3D8E0;
                padding: 5px 3px;
                margin: 0px;
            }
            QToolButton:hover {
                background-color: #4a4d55;
            }
            QToolButton:pressed {
                background-color: #2a2d35;
            }
        """)
        main_layout.addWidget(self.toggle_button)
        
        # 创建主内容区分割器（表格和图表）
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # 第二列：中间数据表格
        content_splitter.addWidget(self.data_table_component)
        
        # 第三列：右侧图表区域（二维图表和三维模型标签页）
        content_splitter.addWidget(self.chart_component)
        
        # 设置表格和图表的分割比例
        content_splitter.setSizes([400, 600])  # 中等、右宽
        
        main_layout.addWidget(content_splitter, 1)  # 让内容区占据大部分空间
        
        # 应用深色主题
        self.apply_dark_theme()
        
        print("🎨 三列界面布局设置完成，已添加侧边栏隐藏功能")
        
    def apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #313642;
                color: #D3D8E0;
                font-family: 'Microsoft YaHei', 'SimHei', Arial;
            }
            QSplitter::handle {
                background-color: #505869;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
        
    def connect_signals(self):
        """连接组件间的信号 - 实现低耦合通信"""
        # 侧边栏信号连接
        self.sidebar_component.workpiece_selected.connect(self.on_workpiece_selected)
        self.sidebar_component.hole_selected.connect(self.on_hole_selected)
        self.sidebar_component.query_requested.connect(self.on_query_requested)
        self.sidebar_component.export_requested.connect(self.on_export_requested)
        self.sidebar_component.review_requested.connect(self.on_review_requested)
        
        # 数据表格信号连接
        self.data_table_component.row_double_clicked.connect(self.on_table_row_double_clicked)
        
        # 图表组件信号连接
        self.chart_component.chart_updated.connect(self.on_chart_updated)
        self.chart_component.point_clicked.connect(self.on_chart_point_clicked)
        self.chart_component.tab_changed.connect(self.on_chart_tab_changed)
        
        print("🔗 组件信号连接完成")
        
    # === 事件处理方法 - 组件间协调 ===
    
    def on_workpiece_selected(self, workpiece_id):
        """工件选择处理"""
        print(f"🔧 工件选择: {workpiece_id}")
        self.data_controller.workpiece_id = workpiece_id
        self.update_status(f"已选择工件: {workpiece_id}")
        
    def on_hole_selected(self, hole_id):
        """孔位选择处理"""
        print(f"🎯 孔位选择: {hole_id}")
        self.update_status(f"已选择孔位: {hole_id}，请点击查询数据")
        
    def on_query_requested(self, hole_id):
        """查询数据请求处理"""
        # 检查是否正在查询中
        if self.is_querying:
            print("⚠️ 查询正在进行中，请等待...")
            self.sidebar_component.update_status("查询正在进行中，请等待...")
            return
            
        print(f"🔍 查询孔位数据: {hole_id}")
        
        # 设置查询状态为进行中
        self.is_querying = True
        self.sidebar_component.update_status("正在查询数据...")
        
        # 禁用查询按钮防止重复点击
        if hasattr(self.sidebar_component, 'query_button'):
            self.sidebar_component.query_button.setEnabled(False)
            self.sidebar_component.query_button.setText("查询中...")
        
        try:
            # 加载真实数据
            measurements = self.data_controller.load_real_data(hole_id)
            
            # 只处理真实存在的数据，无数据时直接跳过
            if measurements:
                # 更新各个组件的数据显示
                self.data_table_component.load_measurements(measurements)
                self.chart_component.load_data(measurements, hole_id)
                
                # 启用操作按钮
                self.sidebar_component.enable_operations(True)
                
                # 更新状态显示
                stats = self.data_controller.get_statistics()
                status_text = (
                    f"已加载孔位: {hole_id}\n"
                    f"数据点数: {stats['total_count']}\n"
                    f"合格点数: {stats['qualified_count']}\n"
                    f"合格率: {stats['pass_rate']:.1f}%"
                )
                self.sidebar_component.update_status(status_text)
                
                # 发射数据加载信号
                self.data_loaded.emit(hole_id, stats['total_count'])
                
                print(f"✅ 数据查询完成: {hole_id}, {stats['total_count']} 条记录")
            
        finally:
            # 无论成功还是失败，都要恢复查询状态
            self.is_querying = False
            if hasattr(self.sidebar_component, 'query_button'):
                self.sidebar_component.query_button.setEnabled(True)
                self.sidebar_component.query_button.setText("查询数据")
        
    def on_export_requested(self):
        """数据导出请求处理"""
        print("📤 处理数据导出请求")
        
        measurements, hole_id = self.data_controller.get_current_data()
        if not measurements:
            QMessageBox.warning(self, "警告", "没有数据可以导出")
            return
            
        # 获取保存路径 - 使用重构前的文件名格式
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", f"{hole_id}_测量数据.csv",
            "CSV文件 (*.csv);;所有文件 (*)")
            
        if not file_path:
            return
            
        # 导出数据 - 使用重构前的完整格式
        if self._export_data_with_full_format(file_path):
            self._show_styled_message_box("导出成功", f"数据已导出到:\n{file_path}", QMessageBox.Information)
            print(f"✅ 数据导出成功: {file_path}")
        else:
            self._show_styled_message_box("导出失败", "导出数据时发生错误", QMessageBox.Critical)
            
    def on_review_requested(self):
        """打开人工复查窗口 - 直接从重构前代码迁移"""
        if not hasattr(self.data_table_component, 'measurements') or not self.data_table_component.measurements:
            self._show_styled_message_box("警告", "请先查询数据后再进行人工复查", QMessageBox.Warning)
            return

        # 检查是否有不合格数据 - 使用重构前的公差判断逻辑
        measurements = self.data_table_component.measurements
        standard_diameter = 17.73
        upper_tolerance = 0.07
        lower_tolerance = 0.05

        unqualified_measurements = []
        for i, measurement in enumerate(measurements):
            diameter = measurement.get('diameter', 0)
            if not (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance):
                unqualified_measurements.append((i, measurement))

        if not unqualified_measurements:
            self._show_styled_message_box("信息", "当前数据中没有不合格的测量值，无需人工复查", QMessageBox.Information)
            return

        # 打开人工复查对话框
        from .components.manual_review_dialog import ManualReviewDialog
        dialog = ManualReviewDialog(unqualified_measurements, self)
        if dialog.exec() == QDialog.Accepted:
            # 获取复查结果并更新数据
            review_results = dialog.get_review_results()
            self.apply_manual_review_results(review_results)
            
    def apply_manual_review_results(self, review_results):
        """应用人工复查结果 - 直接从重构前代码迁移"""
        if not hasattr(self.data_table_component, 'measurements') or not self.data_table_component.measurements:
            return

        measurements = self.data_table_component.measurements
        updated_count = 0

        for index, review_data in review_results.items():
            if index < len(measurements):
                measurements[index]['manual_review_value'] = review_data['diameter']
                measurements[index]['reviewer'] = review_data['reviewer']
                measurements[index]['review_time'] = review_data['review_time']
                updated_count += 1

        if updated_count > 0:
            # 更新显示 - 使用重构前的更新逻辑
            self.data_table_component.load_measurements(measurements)
            
            # 如果有图表，也更新图表
            if hasattr(self, 'chart_component') and self.chart_component:
                try:
                    self.chart_component.update_chart_data(measurements)
                except Exception as e:
                    print(f"更新图表时出错: {e}")
            
            # 保存人工复查结果到原始数据文件 - 补充重构前缺失的持久化功能
            try:
                if hasattr(self.data_controller, 'save_review_results'):
                    self.data_controller.save_review_results(measurements)
                    print(f"✅ 人工复查结果已保存到文件")
            except Exception as e:
                print(f"⚠️ 保存复查结果时出错: {e}")

            self._show_styled_message_box("成功", f"已更新 {updated_count} 条人工复查记录", QMessageBox.Information)
        
    def on_table_row_double_clicked(self, row, measurement):
        """表格行双击处理"""
        position = measurement.get('position', 0)
        diameter = measurement.get('diameter', 0)
        print(f"📊 双击表格行 {row}: 位置 {position:.1f}mm, 直径 {diameter:.4f}mm")
        
        # 可以在这里实现数据详情显示等功能
        
    def on_chart_updated(self):
        """图表更新处理"""
        print("📈 图表已更新")
        
    def on_chart_point_clicked(self, index, depth, diameter):
        """图表数据点点击处理"""
        print(f"📊 点击图表数据点 {index}: 深度 {depth:.1f}mm, 直径 {diameter:.4f}mm")
        
        # 同步选择表格行
        if hasattr(self.data_table_component.data_table, 'selectRow'):
            self.data_table_component.data_table.selectRow(index)
            
    def on_chart_tab_changed(self, index, tab_name):
        """图表标签页切换处理"""
        print(f"📊 图表标签页切换: {tab_name}")
        
    # === 外部接口方法 ===
    
    def load_data_for_hole(self, hole_id):
        """为指定孔位加载数据 - 外部接口"""
        print(f"🎯 外部请求加载孔位数据: {hole_id}")
        self.on_query_requested(hole_id)
        
    def get_current_data(self):
        """获取当前数据 - 外部接口"""
        return self.data_controller.get_current_data()
        
    def get_statistics(self):
        """获取统计信息 - 外部接口"""
        return self.data_controller.get_statistics()
        
    def clear_all_data(self):
        """清除所有数据 - 外部接口"""
        self.data_controller.current_measurements = []
        self.data_controller.current_hole_id = ""
        
        self.data_table_component.clear_table()
        self.chart_component.clear_data()
        self.sidebar_component.enable_operations(False)
        self.sidebar_component.update_status("请选择孔位加载数据")
        
        print("🗑️ 所有数据已清除")
        
    def refresh_data(self):
        """刷新数据 - 外部接口"""
        measurements, hole_id = self.data_controller.get_current_data()
        if measurements and hole_id:
            self.load_data_for_hole(hole_id)
        
    def update_status(self, message):
        """更新状态显示"""
        self.sidebar_component.update_status(message)
        
    def export_current_chart(self, file_path):
        """导出当前图表"""
        return self.chart_component.export_current_chart(file_path)
    
    def _show_styled_message_box(self, title, text, icon=QMessageBox.Information):
        """显示带有统一按钮样式的消息框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon)
        
        # 添加标准按钮确保按钮存在
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 应用白字蓝底样式 - 与查询数据按钮保持一致
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: normal;
                min-height: 20px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """
        
        # 为所有按钮应用样式
        for button in msg_box.buttons():
            button.setStyleSheet(button_style)
        
        msg_box.exec()
        
    def switch_to_2d_chart(self):
        """切换到二维图表"""
        self.chart_component.switch_to_2d_chart()
        
    def switch_to_3d_model(self):
        """切换到三维模型"""
        self.chart_component.switch_to_3d_model()
        
    def toggle_sidebar(self, checked):
        """切换侧边栏显示/隐藏 - 直接从重构前代码迁移"""
        if checked:
            self.sidebar_component.show()
            self.toggle_button.setArrowType(Qt.LeftArrow)
            print("📋 侧边栏已展开")
        else:
            self.sidebar_component.hide()
            self.toggle_button.setArrowType(Qt.RightArrow)
            print("📋 侧边栏已隐藏")
    
    def _export_data_with_full_format(self, file_path):
        """使用重构前的完整CSV格式导出数据"""
        try:
            measurements, hole_id = self.data_controller.get_current_data()
            if not measurements:
                return False
                
            # 计算统计信息 - 使用重构前的逻辑
            diameters = [m['diameter'] for m in measurements]
            standard_diameter = 17.73
            upper_tolerance = 0.07
            lower_tolerance = 0.05
            
            qualified_count = sum(1 for d in diameters
                                if standard_diameter - lower_tolerance <= d <= standard_diameter + upper_tolerance)
            total_count = len(diameters)
            qualification_rate = qualified_count / total_count * 100 if total_count > 0 else 0
            
            max_diameter = max(diameters) if diameters else 0
            min_diameter = min(diameters) if diameters else 0
            avg_diameter = sum(diameters) / len(diameters) if diameters else 0

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入统计信息头部 - 完全按照重构前格式
                writer.writerow(['测量数据统计信息'])
                writer.writerow(['工件ID', 'CAP1000'])
                writer.writerow(['孔位ID', hole_id])
                writer.writerow(['标准直径(mm)', standard_diameter])
                writer.writerow(['公差范围(mm)', f'-{lower_tolerance}~+{upper_tolerance}'])
                writer.writerow(['最大直径(mm)', f'{max_diameter:.4f}'])
                writer.writerow(['最小直径(mm)', f'{min_diameter:.4f}'])
                writer.writerow(['平均直径(mm)', f'{avg_diameter:.4f}'])
                writer.writerow(['合格率', f'{qualified_count}/{total_count} ({qualification_rate:.1f}%)'])
                writer.writerow([])  # 空行分隔
                
                # 写入测量数据表头 - 完全按照重构前格式
                writer.writerow(['位置(mm)', '直径(mm)', '通道1值(μm)', '通道2值(μm)', '通道3值(μm)', '合格', '时间', '操作员', '备注'])
                
                # 写入测量数据 - 完全按照重构前格式
                for measurement in measurements:
                    diameter = measurement['diameter']
                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)
                    qualified_text = '✓' if is_qualified else '✗'  # 使用与重构前相同的符号
                    
                    # 检查是否有人工复查值 - 完全按照重构前格式
                    notes = ""
                    if 'manual_review_value' in measurement:
                        notes = f"人工复查值: {measurement['manual_review_value']:.4f}mm"
                        if 'reviewer' in measurement:
                            notes += f", 复查员: {measurement['reviewer']}"
                        if 'review_time' in measurement:
                            notes += f", 复查时间: {measurement['review_time']}"
                    
                    # 获取位置信息（兼容两种键名）
                    position = measurement.get('position', measurement.get('depth', 0))
                    
                    # 时间格式化
                    timestamp = measurement.get('timestamp', '')
                    if timestamp:
                        time_str = timestamp.strftime("%H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp)
                    else:
                        time_str = ""
                    
                    # 操作员信息
                    operator = measurement.get('operator', '')
                    
                    writer.writerow([
                        f"{position:.1f}",           # 位置(mm) - 1位小数
                        f"{diameter:.4f}",           # 直径(mm) - 4位小数
                        f"{measurement.get('channel1', 0):.2f}",  # 通道1值(μm) - 2位小数
                        f"{measurement.get('channel2', 0):.2f}",  # 通道2值(μm) - 2位小数
                        f"{measurement.get('channel3', 0):.2f}",  # 通道3值(μm) - 2位小数
                        qualified_text,              # 合格 - ✓ 或 ✗
                        time_str,                    # 时间 - HH:MM:SS
                        operator,                    # 操作员
                        notes                        # 备注
                    ])
                    
            return True
            
        except Exception as e:
            print(f"❌ 导出数据时发生异常: {e}")
            return False


if __name__ == "__main__":
    # 测试主界面
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 应用深色主题
    app.setStyleSheet("""
        QWidget {
            background-color: #313642;
            color: #D3D8E0;
            font-family: 'Microsoft YaHei', 'SimHei', Arial;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #505869;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    # 创建并显示主界面
    main_view = MigratedMainView()
    main_view.setWindowTitle("P3.1 管孔直径历史数据查看器 - 重构前功能完整迁移")
    main_view.resize(1400, 800)
    main_view.show()
    
    print("🚀 迁移的主界面测试启动")
    
    sys.exit(app.exec())