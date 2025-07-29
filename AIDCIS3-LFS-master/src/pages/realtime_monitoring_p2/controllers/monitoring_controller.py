"""
监控控制器
负责协调各个组件之间的交互和数据流
"""

import os
import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox


class MonitoringController(QObject):
    """
    监控控制器
    协调状态面板、图表面板、异常面板和内窥镜面板之间的交互
    """
    
    # 信号定义
    status_updated = Signal(str, str)  # status_type, message
    data_point_added = Signal(float, float)  # depth, diameter
    hole_changed = Signal(str)  # hole_id
    monitoring_state_changed = Signal(bool)  # is_monitoring
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 当前状态
        self.current_hole_id = None
        self.is_monitoring = False
        self.is_data_loaded = False
        
        # 数据统计
        self.max_diameter = None
        self.min_diameter = None
        
        # 标准参数
        self.standard_diameter = 17.73
        self.upper_tolerance = 0.07
        self.lower_tolerance = 0.05
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 组件引用
        self.status_panel = None
        self.chart_panel = None
        self.anomaly_panel = None
        self.endoscope_panel = None
        
    def set_components(self, status_panel, chart_panel, anomaly_panel, endoscope_panel):
        """设置组件引用"""
        self.status_panel = status_panel
        self.chart_panel = chart_panel
        self.anomaly_panel = anomaly_panel
        self.endoscope_panel = endoscope_panel
        
        # 连接组件信号
        self.setup_component_connections()
        
    def setup_component_connections(self):
        """设置组件间的信号连接"""
        if self.status_panel:
            self.status_panel.start_clicked.connect(self.start_monitoring)
            self.status_panel.stop_clicked.connect(self.stop_monitoring)
            self.status_panel.clear_clicked.connect(self.clear_data)
            
        if self.chart_panel:
            self.chart_panel.export_requested.connect(self.export_chart)
            self.chart_panel.refresh_requested.connect(self.refresh_chart)
            
        if self.anomaly_panel:
            self.anomaly_panel.next_sample_clicked.connect(self.view_next_sample)
            
        if self.endoscope_panel:
            self.endoscope_panel.save_snapshot_requested.connect(self.save_endoscope_snapshot)
            self.endoscope_panel.fullscreen_requested.connect(self.show_endoscope_fullscreen)
            
    def start_monitoring(self):
        """开始监控"""
        try:
            self.logger.info("开始监控")
            self.is_monitoring = True
            
            # 更新状态面板
            if self.status_panel:
                self.status_panel.set_monitoring_state(True)
                
            # 发射状态变化信号
            self.monitoring_state_changed.emit(True)
            self.status_updated.emit("info", "监控已开始")
            
        except Exception as e:
            self.logger.error(f"开始监控失败: {e}")
            self.status_updated.emit("error", f"开始监控失败: {e}")
            
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.logger.info("停止监控")
            self.is_monitoring = False
            
            # 更新状态面板
            if self.status_panel:
                self.status_panel.set_monitoring_state(False)
                
            # 发射状态变化信号
            self.monitoring_state_changed.emit(False)
            self.status_updated.emit("info", "监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
            self.status_updated.emit("error", f"停止监控失败: {e}")
            
    def clear_data(self):
        """清除数据"""
        try:
            self.logger.info("清除数据")
            
            # 清除图表数据
            if self.chart_panel:
                self.chart_panel.clear_data()
                
            # 清除异常数据
            if self.anomaly_panel:
                self.anomaly_panel.clear_anomalies()
                
            # 清除内窥镜图像
            if self.endoscope_panel:
                self.endoscope_panel.clear_image()
                
            # 重置统计数据
            self.max_diameter = None
            self.min_diameter = None
            
            # 更新状态显示
            self.update_diameter_statistics()
            self.status_updated.emit("info", "数据已清除")
            
        except Exception as e:
            self.logger.error(f"清除数据失败: {e}")
            self.status_updated.emit("error", f"清除数据失败: {e}")
            
    def add_measurement_point(self, depth: float, diameter: float):
        """添加测量点"""
        try:
            # 更新图表
            if self.chart_panel:
                self.chart_panel.add_data_point(depth, diameter)
                
            # 检查异常并更新异常面板
            if self.anomaly_panel:
                self.anomaly_panel.add_measurement_point(depth, diameter)
                
            # 更新统计数据
            self.update_statistics(diameter)
            
            # 发射数据点添加信号
            self.data_point_added.emit(depth, diameter)
            
        except Exception as e:
            self.logger.error(f"添加测量点失败: {e}")
            
    def update_statistics(self, diameter: float):
        """更新统计数据"""
        # 更新最大最小直径
        if self.max_diameter is None or diameter > self.max_diameter:
            self.max_diameter = diameter
            
        if self.min_diameter is None or diameter < self.min_diameter:
            self.min_diameter = diameter
            
        # 更新状态面板显示
        self.update_diameter_statistics()
        
    def update_diameter_statistics(self):
        """更新直径统计显示"""
        if self.status_panel:
            self.status_panel.update_max_diameter(self.max_diameter)
            self.status_panel.update_min_diameter(self.min_diameter)
            
    def set_current_hole(self, hole_id: str):
        """设置当前孔位"""
        self.current_hole_id = hole_id
        
        # 更新状态面板
        if self.status_panel:
            self.status_panel.update_current_hole(hole_id)
            
        # 更新内窥镜面板
        if self.endoscope_panel:
            self.endoscope_panel.set_hole_id(hole_id)
            
        # 发射孔位变化信号
        self.hole_changed.emit(hole_id)
        self.logger.info(f"设置当前孔位: {hole_id}")
        
    def set_standard_diameter(self, diameter: float, upper_tol: float = 0.07, lower_tol: float = 0.05):
        """设置标准直径和公差"""
        self.standard_diameter = diameter
        self.upper_tolerance = upper_tol
        self.lower_tolerance = lower_tol
        
        # 更新状态面板
        if self.status_panel:
            self.status_panel.update_standard_diameter(diameter)
            
        # 更新图表面板
        if self.chart_panel:
            self.chart_panel.set_standard_diameter(diameter, upper_tol, lower_tol)
            
        # 更新异常面板
        if self.anomaly_panel:
            self.anomaly_panel.set_tolerance_parameters(diameter, upper_tol, lower_tol)
            
        self.logger.info(f"设置标准直径: {diameter}mm, 公差: +{upper_tol}/-{lower_tol}")
        
    def export_chart(self):
        """导出图表"""
        try:
            # 实现图表导出逻辑
            self.status_updated.emit("info", "图表导出功能待实现")
        except Exception as e:
            self.logger.error(f"导出图表失败: {e}")
            
    def refresh_chart(self):
        """刷新图表"""
        try:
            if self.chart_panel:
                self.chart_panel.canvas.draw()
            self.status_updated.emit("info", "图表已刷新")
        except Exception as e:
            self.logger.error(f"刷新图表失败: {e}")
            
    def view_next_sample(self):
        """查看下一个样品"""
        try:
            # 实现查看下一个样品的逻辑
            self.status_updated.emit("info", "查看下一个样品功能待实现")
        except Exception as e:
            self.logger.error(f"查看下一个样品失败: {e}")
            
    def save_endoscope_snapshot(self):
        """保存内窥镜快照"""
        try:
            # 实现保存快照逻辑
            self.status_updated.emit("info", "保存快照功能待实现")
        except Exception as e:
            self.logger.error(f"保存快照失败: {e}")
            
    def show_endoscope_fullscreen(self):
        """全屏显示内窥镜"""
        try:
            # 实现全屏显示逻辑
            self.status_updated.emit("info", "全屏显示功能待实现")
        except Exception as e:
            self.logger.error(f"全屏显示失败: {e}")
            
    def get_monitoring_state(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'current_hole_id': self.current_hole_id,
            'is_data_loaded': self.is_data_loaded,
            'max_diameter': self.max_diameter,
            'min_diameter': self.min_diameter,
            'standard_diameter': self.standard_diameter,
            'upper_tolerance': self.upper_tolerance,
            'lower_tolerance': self.lower_tolerance
        }
