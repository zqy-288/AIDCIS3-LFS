"""
P3.1级历史数据主界面 - 模块化架构
高内聚低耦合的模块化设计，完全基于重构前功能恢复
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QFrame, QMessageBox, QLabel, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging

# 导入模块化组件
from .controllers.view_controller import HistoryViewController
from .widgets.status_panel_widget import StatusPanelWidget
from .widgets.data_table_widget import DataTableWidget
from .components.tolerance_chart_widget import ToleranceChartContainer
from .components.manual_review_dialog import ManualReviewDialog


class HistoryMainView(QWidget):
    """
    P3.1级历史数据主界面 - 高内聚低耦合架构
    职责：
    1. 组装和协调各个模块化组件
    2. 管理界面布局和样式
    3. 处理组件间的信号连接
    4. 提供统一的外部接口
    """
    
    # 对外信号
    interface_ready = Signal()  # 界面准备完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 创建控制器 - 作为业务逻辑中心
        self.controller = HistoryViewController()
        
        # 初始化组件
        self.init_components()
        
        # 设置界面
        self.setup_ui()
        
        # 连接信号
        self.connect_signals()
        
        # 初始化数据
        self.init_data()
        
        self.logger.info("P3.1级历史数据主界面初始化完成")
        self.interface_ready.emit()
    
    def init_components(self):
        """初始化各个模块化组件"""
        # 状态面板组件
        self.status_panel = StatusPanelWidget()
        
        # 数据表格组件
        self.data_table = DataTableWidget()
        
        # 图表组件容器
        self.chart_container = ToleranceChartContainer()
        
        self.logger.info("模块化组件初始化完成")
    
    def setup_ui(self):
        """设置界面布局 - 三列布局：状态面板+数据表格+图表区域"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建主分割器（三列布局）
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        
        # 第一列：左侧状态面板（光谱共焦历史数据查看器）
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 第二列：中间数据表格
        middle_panel = self.create_middle_panel()
        main_splitter.addWidget(middle_panel)
        
        # 第三列：右侧图表区域（二维公差带图表和三维模型渲染）
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置三列分割比例 - 基于重构前p2.png的布局比例
        main_splitter.setSizes([200, 350, 550])  # 左窄、中等、右最宽
        
        main_layout.addWidget(main_splitter)
        
        # 应用整体样式
        self.apply_dark_theme()
        
        self.logger.info("三列界面布局设置完成")
    
    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        # 直接使用状态面板组件，调整为更窄的宽度
        self.status_panel.setMaximumWidth(200)
        self.status_panel.setMinimumWidth(180)
        
        return self.status_panel
    
    def create_middle_panel(self) -> QWidget:
        """创建中间数据表格面板"""
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        
        # 直接添加数据表格组件
        middle_layout.addWidget(self.data_table)
        
        return middle_widget
        
    def create_right_panel(self) -> QWidget:
        """创建右侧图表区域面板 - 包含二维公差带图表和三维模型渲染标签页"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建标签页组件
        tab_widget = QTabWidget()
        
        # 设置标签页样式 - 基于重构前的深色主题
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #505869;
                background-color: #313642;
            }
            QTabBar::tab {
                background-color: #3a3d45;
                color: #D3D8E0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #505869;
                border-bottom: none;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #505869;
            }
        """)
        
        # 第一个标签页：二维公差带图表
        tab_widget.addTab(self.chart_container, "二维公差带图表")
        
        # 第二个标签页：三维模型渲染
        model_3d_widget = self.create_3d_model_widget()
        tab_widget.addTab(model_3d_widget, "三维模型渲染")
        
        right_layout.addWidget(tab_widget)
        
        return right_widget
        
    def create_3d_model_widget(self) -> QWidget:
        """创建三维模型渲染组件"""
        model_3d_widget = QWidget()
        model_3d_layout = QVBoxLayout(model_3d_widget)
        model_3d_layout.setContentsMargins(10, 10, 10, 10)
        
        # 占位符内容
        placeholder_label = QLabel("三维模型渲染区域")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                color: #888888; 
                font-size: 16px;
                background-color: #2a2d35;
                border: 2px dashed #505869;
                padding: 50px;
                border-radius: 10px;
            }
        """)
        
        # 功能说明
        info_label = QLabel("将在后续版本中实现管孔三维模型的可视化渲染")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 20px;")
        
        model_3d_layout.addWidget(placeholder_label)
        model_3d_layout.addWidget(info_label)
        model_3d_layout.addStretch()
        
        return model_3d_widget
    
    
    def connect_signals(self):
        """连接各组件间的信号 - 实现组件间通信"""
        # 状态面板信号连接
        self.status_panel.workpiece_changed.connect(self.controller.set_workpiece_id)
        self.status_panel.query_requested.connect(self.controller.query_hole_data)
        self.status_panel.export_requested.connect(self.controller.export_data)
        self.status_panel.review_requested.connect(self.controller.start_manual_review)
        
        # 控制器信号连接
        self.controller.status_updated.connect(self.status_panel.update_status)
        self.controller.error_occurred.connect(self.show_error_message)
        self.controller.table_update_requested.connect(self.data_table.load_measurements)
        self.controller.chart_update_requested.connect(self.update_chart)
        self.controller.export_completed.connect(self.show_export_success)
        self.controller.review_requested.connect(self.show_manual_review_dialog)
        self.controller.data_loaded.connect(self.on_data_loaded)
        
        # 数据表格信号连接
        self.data_table.row_selected.connect(self.on_table_row_selected)
        self.data_table.row_double_clicked.connect(self.on_table_row_double_clicked)
        
        self.logger.info("组件信号连接完成")
    
    def init_data(self):
        """初始化数据"""
        # 设置默认工件ID
        self.status_panel.set_workpiece_id("CAP1000")
        self.controller.set_workpiece_id("CAP1000")
        
        # 获取可用孔位列表
        available_holes = self.controller.get_available_holes()
        self.status_panel.update_available_holes(available_holes)
        
        self.logger.info(f"数据初始化完成，可用孔位: {len(available_holes)} 个")
    
    def apply_dark_theme(self):
        """应用深色主题 - 基于重构前的样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #313642;
                color: #D3D8E0;
                font-family: 'Microsoft YaHei', 'SimHei', Arial;
            }
            QFrame {
                background-color: #313642;
                border: 1px solid #505869;
            }
        """)
    
    def update_chart(self, measurements, hole_id):
        """更新图表显示"""
        try:
            if measurements:
                # 设置公差参数
                tolerance_params = self.controller.get_tolerance_parameters()
                self.chart_container.set_tolerance_parameters(
                    tolerance_params['standard_diameter'],
                    tolerance_params['upper_tolerance'],
                    tolerance_params['lower_tolerance']
                )
                
                # 加载数据到图表
                self.chart_container.load_data(measurements, hole_id)
            else:
                self.chart_container.clear_data()
                
        except Exception as e:
            self.logger.error(f"更新图表时发生错误: {e}")
            self.show_error_message(f"图表更新失败: {e}")
    
    def on_data_loaded(self, measurements, hole_id):
        """数据加载完成处理"""
        # 启用数据操作按钮
        self.status_panel.enable_data_operations(True)
        
        self.logger.info(f"数据加载完成: {hole_id}, {len(measurements)} 条记录")
    
    def on_table_row_selected(self, row_index, measurement):
        """表格行选择处理"""
        self.logger.debug(f"选择表格行: {row_index}")
    
    def on_table_row_double_clicked(self, row_index, measurement):
        """表格行双击处理"""
        self.logger.debug(f"双击表格行: {row_index}")
        # 可以实现详细信息弹窗等功能
    
    def show_error_message(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
        self.logger.error(f"显示错误消息: {message}")
    
    def show_export_success(self, file_path):
        """显示导出成功消息"""
        QMessageBox.information(self, "导出完成", f"数据导出成功！\\n文件路径: {file_path}")
        self.logger.info(f"显示导出成功消息: {file_path}")
    
    def show_manual_review_dialog(self, unqualified_measurements):
        """显示人工复查对话框"""
        try:
            dialog = ManualReviewDialog(unqualified_measurements, self)
            
            if dialog.exec() == dialog.Accepted:
                # 获取复查结果
                review_results = dialog.get_review_results()
                
                # 更新控制器中的数据
                self.controller.update_review_results(review_results)
                
                QMessageBox.information(self, "复查完成", 
                                      f"人工复查完成，更新了 {len(review_results)} 条数据")
                
        except Exception as e:
            self.logger.error(f"显示人工复查对话框时发生错误: {e}")
            self.show_error_message(f"人工复查功能出错: {e}")
    
    # 对外接口方法
    def get_current_data(self):
        """获取当前数据"""
        return self.controller.get_current_hole_data()
    
    def refresh_data(self):
        """刷新数据"""
        available_holes = self.controller.get_available_holes()
        self.status_panel.update_available_holes(available_holes)
    
    def clear_all_data(self):
        """清除所有数据"""
        self.controller.clear_data()
        self.status_panel.clear_selections()
        self.data_table.clear_data()
        self.chart_container.clear_data()
    
    def set_tolerance_parameters(self, standard_diameter, upper_tolerance, lower_tolerance):
        """设置公差参数"""
        self.controller.set_tolerance_parameters(standard_diameter, upper_tolerance, lower_tolerance)
        
        # 更新表格颜色显示
        self.data_table.update_tolerance_colors(standard_diameter, upper_tolerance, lower_tolerance)
        
        # 如果有数据，重新绘制图表
        if self.controller.has_current_data():
            measurements = self.controller.current_measurements
            hole_id = self.controller.current_hole_id
            self.update_chart(measurements, hole_id)