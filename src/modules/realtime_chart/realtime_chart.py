"""
实时图表组件主模块
整合各个子模块，提供统一的接口
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Slot, Signal

# 导入子模块
from .components import ChartWidget, StatusPanel
from .managers import DataManager, CSVManager, EndoscopeManager
from .utils import setup_safe_chinese_font, ChartConfig
from ..endoscope_view import EndoscopeView


class RealtimeChart(QWidget):
    """
    实时图表组件 - 二级页面双面板设计
    面板A: 管孔直径数据实时折线图
    面板B: 内窥镜实时图像显示
    """
    
    # 保持原有的信号接口
    hole_selected = Signal(str)
    measurement_started = Signal(str)
    measurement_stopped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化管理器
        self.data_manager = DataManager()
        self.csv_manager = CSVManager()
        self.endoscope_manager = EndoscopeManager()
        
        # 配置
        self.config = ChartConfig()
        
        # 当前状态
        self.current_hole_id = None
        
        # 设置UI
        self.setup_ui()
        
        # 连接信号
        self.setup_connections()
        
        # 初始化数据
        self.init_hole_data_mapping()
        
    def setup_ui(self):
        """设置用户界面布局"""
        layout = QVBoxLayout(self)
        
        # 状态信息面板
        self.status_panel = StatusPanel()
        layout.addWidget(self.status_panel)
        
        # 创建分割器 - 双面板设计
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 面板A - 图表显示
        self.chart_widget = ChartWidget()
        self.splitter.addWidget(self.chart_widget)
        
        # 面板B - 内窥镜视图
        self.endoscope_view = EndoscopeView()
        self.splitter.addWidget(self.endoscope_view)
        
        # 设置分割比例
        self.splitter.setSizes([800, 400])
        
        layout.addWidget(self.splitter)
        
        # 控制面板（可选）
        # self.controls_panel = ControlsPanel()
        # layout.addWidget(self.controls_panel)
        
    def setup_connections(self):
        """设置信号连接"""
        # 数据管理器信号
        self.data_manager.data_updated.connect(self._update_chart)
        self.data_manager.anomaly_detected.connect(self._on_anomaly_detected)
        self.data_manager.extremes_updated.connect(self.status_panel.update_extremes)
        
        # CSV管理器信号
        self.csv_manager.data_point_ready.connect(self.data_manager.update_data)
        self.csv_manager.playback_finished.connect(self._on_csv_playback_finished)
        self.csv_manager.error_occurred.connect(self._show_error)
        
        # 内窥镜管理器信号
        self.endoscope_manager.image_changed.connect(self._update_endoscope_image)
        self.endoscope_manager.error_occurred.connect(self._show_error)
        
        # 状态面板信号
        self.status_panel.hole_changed.connect(self._on_hole_changed)
        
    def init_hole_data_mapping(self):
        """初始化孔位数据映射"""
        # 获取可用的孔位列表
        hole_ids = ['H00001', 'H00002']  # 可以从配置或数据库加载
        self.status_panel.add_hole_options(hole_ids)
        
    # === 公共接口方法（保持向后兼容） ===
    
    @Slot(float, float)
    def update_data(self, depth, diameter):
        """更新图表数据的槽函数"""
        self.data_manager.update_data(depth, diameter)
        
    @Slot(str, float, str)
    def update_status(self, hole_id, probe_depth, comm_status):
        """更新状态信息的槽函数"""
        self.status_panel.update_depth(probe_depth)
        self.status_panel.update_comm_status(comm_status)
        
    def set_current_hole(self, hole_id):
        """设置当前检测的孔ID"""
        self.current_hole_id = hole_id
        self.data_manager.set_current_hole(hole_id)
        self.status_panel.set_current_hole(hole_id)
        self.endoscope_view.set_hole_id(hole_id)
        
        # 加载内窥镜图像
        self.endoscope_manager.load_images_for_hole(hole_id)
        
        print(f"✅ 设置当前检测孔位: {hole_id}")
        
    def start_measurement_for_hole(self, hole_id):
        """为指定孔开始测量"""
        self.set_current_hole(hole_id)
        self.clear_data()
        
        # 开始内窥镜图像采集（如果有start_acquisition方法）
        if hasattr(self.endoscope_view, 'start_acquisition'):
            self.endoscope_view.start_acquisition()
        self.measurement_started.emit(hole_id)
        
    def stop_measurement(self):
        """停止测量"""
        # 停止内窥镜图像采集（如果有stop_acquisition方法）
        if hasattr(self.endoscope_view, 'stop_acquisition'):
            self.endoscope_view.stop_acquisition()
        self.measurement_stopped.emit()
        
    def clear_data(self):
        """清除所有数据"""
        self.data_manager.clear_data()
        self.chart_widget.clear_chart()
        self.endoscope_view.clear_image()
        self.status_panel.clear_status()
        self.current_hole_id = None
        
    def set_tolerance_limits(self, target, tolerance):
        """设置公差限制"""
        self.data_manager.set_standard_parameters(target, tolerance, tolerance)
        self.chart_widget.draw_error_lines(target, tolerance, tolerance)
        self.status_panel.set_standard_diameter(target)
        
    def get_current_statistics(self):
        """获取当前统计信息"""
        stats = self.data_manager.get_statistics()
        return {
            'count': stats['count'],
            'min': stats['min'],
            'max': stats['max'],
            'avg': stats['avg'],
            'anomaly_count': self.data_manager.get_anomaly_count()
        }
        
    # === CSV数据加载方法 ===
    
    def load_data_for_hole(self, hole_id):
        """加载指定孔位的数据"""
        self.set_current_hole(hole_id)
        
        # 加载CSV数据
        if self.csv_manager.load_csv_for_hole(hole_id):
            print(f"✅ 成功加载 {hole_id} 的CSV数据")
        else:
            print(f"❌ 加载 {hole_id} 的CSV数据失败")
            
    def start_csv_data_import(self, auto_play=False):
        """开始CSV数据导入"""
        if auto_play:
            self.csv_manager.start_playback()
            
    def stop_csv_data_import(self):
        """停止CSV数据导入"""
        self.csv_manager.stop_playback()
        
    # === 内部处理方法 ===
    
    def _update_chart(self):
        """更新图表显示"""
        depth_data, diameter_data = self.data_manager.get_current_data()
        if depth_data and diameter_data:
            self.chart_widget.update_data(depth_data, diameter_data)
            
    def _on_anomaly_detected(self, anomaly_info):
        """处理异常检测"""
        # 可以在这里添加异常提示或记录
        print(f"⚠️ 检测到异常: 深度={anomaly_info['depth']:.1f}mm, "
              f"直径={anomaly_info['diameter']:.3f}mm")
              
    def _on_hole_changed(self, hole_id):
        """处理孔位选择变化"""
        self.load_data_for_hole(hole_id)
        self.hole_selected.emit(hole_id)
        
    def _on_csv_playback_finished(self):
        """CSV播放完成处理"""
        print("✅ CSV数据播放完成")
        
        # 可以自动加载下一个文件
        if self.csv_manager.load_next_file():
            self.csv_manager.start_playback()
            
    def _update_endoscope_image(self, image_index):
        """更新内窥镜图像"""
        image_path = self.endoscope_manager.get_current_image_path()
        if image_path:
            self.endoscope_view.display_image(image_path)
            
    def _show_error(self, error_msg):
        """显示错误消息"""
        QMessageBox.warning(self, "警告", error_msg)
        
    # === 清理方法 ===
    
    def cleanup(self):
        """清理资源"""
        self.chart_widget.cleanup()
        self.csv_manager.stop_playback()
        self.endoscope_manager.stop_auto_switching()
        if hasattr(self.endoscope_view, 'stop_acquisition'):
            self.endoscope_view.stop_acquisition()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.cleanup()
        event.accept()