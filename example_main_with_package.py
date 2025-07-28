#!/usr/bin/env python3
"""
示例：如何在主程序中使用实时图表包
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QMenu
from PySide6.QtCore import Qt

# 导入实时图表包
from src.modules.realtime_chart_package import RealtimeChart

# 或者如果包已安装，可以直接导入
# from realtime_chart_package import RealtimeChart


class MainWindow(QMainWindow):
    """主窗口示例"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("实时监测系统")
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建实时图表实例
        self.realtime_chart = RealtimeChart()
        layout.addWidget(self.realtime_chart)
        
        # 初始化设置
        self.initialize_chart()
        
        # 连接信号
        self.connect_signals()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入CSV动作
        import_action = file_menu.addAction('导入CSV')
        import_action.triggered.connect(self.import_csv)
        
        # 导出数据动作
        export_action = file_menu.addAction('导出数据')
        export_action.triggered.connect(self.export_data)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = file_menu.addAction('退出')
        exit_action.triggered.connect(self.close)
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        # 标准直径设置
        diameter_action = settings_menu.addAction('设置标准直径')
        diameter_action.triggered.connect(self.set_standard_diameter)
        
        # 检测方法设置
        detection_menu = settings_menu.addMenu('检测方法')
        
        tolerance_action = detection_menu.addAction('公差检测')
        tolerance_action.triggered.connect(lambda: self.set_detection_method('tolerance'))
        
        statistical_action = detection_menu.addAction('统计检测')
        statistical_action.triggered.connect(lambda: self.set_detection_method('statistical'))
        
        gradient_action = detection_menu.addAction('梯度检测')
        gradient_action.triggered.connect(lambda: self.set_detection_method('gradient'))
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        # 清除数据
        clear_action = view_menu.addAction('清除数据')
        clear_action.triggered.connect(self.realtime_chart.clear_data)
        
        # 重置缩放
        reset_zoom_action = view_menu.addAction('重置缩放')
        reset_zoom_action.triggered.connect(self.reset_zoom)
        
    def initialize_chart(self):
        """初始化图表设置"""
        # 设置默认标准直径
        self.realtime_chart.set_standard_diameter(17.6, 0.2)
        
        # 设置默认检测方法
        self.realtime_chart.set_detection_method('tolerance')
        
        # 如果有默认CSV文件，可以加载
        # self.realtime_chart.set_csv_file('default_data.csv')
        
    def connect_signals(self):
        """连接信号和槽"""
        # 数据更新信号
        self.realtime_chart.data_updated.connect(self.on_data_updated)
        
        # 异常检测信号
        self.realtime_chart.anomaly_detected.connect(self.on_anomaly_detected)
        
        # 进程状态信号
        self.realtime_chart.process_status_changed.connect(self.on_process_status_changed)
        
    def import_csv(self):
        """导入CSV文件"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择CSV文件",
            "",
            "CSV文件 (*.csv)"
        )
        
        if file_path:
            self.realtime_chart.set_csv_file(file_path)
            self.realtime_chart.start_monitoring()
            self.statusBar().showMessage(f"已加载: {file_path}")
            
    def export_data(self):
        """导出数据"""
        self.realtime_chart.export_data()
        self.statusBar().showMessage("数据已导出")
        
    def set_standard_diameter(self):
        """设置标准直径"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("设置标准直径")
        
        layout = QFormLayout(dialog)
        
        # 直径输入
        diameter_spinbox = QDoubleSpinBox()
        diameter_spinbox.setRange(10.0, 30.0)
        diameter_spinbox.setValue(17.6)
        diameter_spinbox.setSingleStep(0.1)
        diameter_spinbox.setDecimals(1)
        layout.addRow("标准直径 (mm):", diameter_spinbox)
        
        # 公差输入
        tolerance_spinbox = QDoubleSpinBox()
        tolerance_spinbox.setRange(0.1, 1.0)
        tolerance_spinbox.setValue(0.2)
        tolerance_spinbox.setSingleStep(0.1)
        tolerance_spinbox.setDecimals(1)
        layout.addRow("公差 (mm):", tolerance_spinbox)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            diameter = diameter_spinbox.value()
            tolerance = tolerance_spinbox.value()
            self.realtime_chart.set_standard_diameter(diameter, tolerance)
            self.statusBar().showMessage(
                f"标准直径: {diameter}mm, 公差: ±{tolerance}mm"
            )
            
    def set_detection_method(self, method: str):
        """设置检测方法"""
        self.realtime_chart.set_detection_method(method)
        method_names = {
            'tolerance': '公差检测',
            'statistical': '统计检测',
            'gradient': '梯度检测'
        }
        self.statusBar().showMessage(f"检测方法: {method_names.get(method, method)}")
        
    def reset_zoom(self):
        """重置图表缩放"""
        self.realtime_chart.chart_widget.reset_zoom()
        self.statusBar().showMessage("缩放已重置")
        
    def on_data_updated(self, depths, diameters):
        """数据更新回调"""
        count = len(depths)
        if count > 0:
            self.statusBar().showMessage(f"数据点: {count}")
            
    def on_anomaly_detected(self, index, depth, diameter):
        """异常检测回调"""
        self.statusBar().showMessage(
            f"检测到异常: 深度={depth:.1f}mm, 直径={diameter:.2f}mm",
            5000  # 显示5秒
        )
        
    def on_process_status_changed(self, status):
        """进程状态变化回调"""
        self.statusBar().showMessage(f"进程状态: {status}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("实时监测系统")
    app.setOrganizationName("AIDCIS3")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 显示欢迎信息
    window.statusBar().showMessage("欢迎使用实时监测系统 v2.0")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()