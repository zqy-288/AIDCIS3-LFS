"""
监控控制器
管理实时监控的核心业务逻辑
"""

from PySide6.QtCore import QObject, Signal, QTimer
import logging
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime
import random


class MonitoringController(QObject):
    """
    监控控制器
    
    负责：
    1. 管理监控状态
    2. 协调数据采集
    3. 控制监控流程
    4. 生成模拟数据
    """
    
    # 信号定义
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    data_received = Signal(dict)  # 接收到新数据
    status_changed = Signal(str)  # 状态改变
    error_occurred = Signal(str)  # 发生错误
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 监控状态
        self.is_monitoring = False
        self.current_hole_id = None
        self.monitoring_mode = "simulation"  # simulation/real
        
        # 数据采集参数
        self.sampling_rate = 10  # Hz
        self.standard_diameter = 376.0  # mm
        self.tolerance = 0.15  # mm
        
        # 探头状态
        self.probe_depth = 0.0  # mm
        self.probe_speed = 10.0  # mm/s
        
        # 定时器
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self._generate_data)
        
        # 数据缓存
        self.data_buffer = []
        
    def start_monitoring(self, hole_id: str = None):
        """开始监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在进行中")
            return
            
        self.current_hole_id = hole_id or "A-001"
        self.is_monitoring = True
        self.probe_depth = 0.0
        self.data_buffer.clear()
        
        # 启动数据生成
        interval = int(1000 / self.sampling_rate)  # 转换为毫秒
        self.data_timer.start(interval)
        
        self.monitoring_started.emit()
        self.status_changed.emit(f"开始监控孔位: {self.current_hole_id}")
        self.logger.info(f"监控已启动 - 孔位: {self.current_hole_id}, 采样率: {self.sampling_rate}Hz")
        
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        self.data_timer.stop()
        
        self.monitoring_stopped.emit()
        self.status_changed.emit("监控已停止")
        self.logger.info(f"监控已停止 - 采集数据点: {len(self.data_buffer)}")
        
    def pause_monitoring(self):
        """暂停监控"""
        if self.is_monitoring:
            self.data_timer.stop()
            self.status_changed.emit("监控已暂停")
            
    def resume_monitoring(self):
        """恢复监控"""
        if self.is_monitoring:
            interval = int(1000 / self.sampling_rate)
            self.data_timer.start(interval)
            self.status_changed.emit("监控已恢复")
            
    def _generate_data(self):
        """生成模拟数据"""
        if self.monitoring_mode == "simulation":
            # 生成模拟直径数据
            base_diameter = self.standard_diameter
            
            # 添加一些随机变化
            noise = np.random.normal(0, 0.05)
            
            # 偶尔产生异常
            if random.random() < 0.05:  # 5%概率
                noise = random.choice([-1, 1]) * (self.tolerance + random.uniform(0.1, 0.3))
                
            # 根据深度添加一些趋势
            depth_factor = np.sin(self.probe_depth * 0.01) * 0.1
            
            diameter = base_diameter + noise + depth_factor
            
            # 更新探头深度
            self.probe_depth += self.probe_speed / self.sampling_rate
            
            # 创建数据点
            data_point = {
                'timestamp': datetime.now(),
                'hole_id': self.current_hole_id,
                'probe_depth': self.probe_depth,
                'diameter': diameter,
                'temperature': 20 + random.uniform(-2, 2),  # 模拟温度
                'data_quality': random.uniform(0.9, 1.0),  # 数据质量指标
                'source': 'simulation'
            }
            
        else:
            # 实际数据采集模式
            # 这里应该从实际硬件读取数据
            data_point = self._read_hardware_data()
            
        # 添加到缓冲区
        self.data_buffer.append(data_point)
        
        # 发送数据
        self.data_received.emit(data_point)
        
    def _read_hardware_data(self) -> Dict:
        """从硬件读取数据"""
        # 这里应该实现实际的硬件通信
        # 目前返回模拟数据
        self.logger.warning("硬件模式未实现，使用模拟数据")
        return {
            'timestamp': datetime.now(),
            'hole_id': self.current_hole_id,
            'probe_depth': self.probe_depth,
            'diameter': self.standard_diameter,
            'temperature': 20.0,
            'data_quality': 1.0,
            'source': 'hardware'
        }
        
    def set_hole_id(self, hole_id: str):
        """设置当前孔位"""
        self.current_hole_id = hole_id
        self.status_changed.emit(f"当前孔位: {hole_id}")
        
    def set_sampling_rate(self, rate: int):
        """设置采样率"""
        self.sampling_rate = max(1, min(100, rate))  # 限制在1-100Hz
        if self.is_monitoring:
            self.data_timer.stop()
            interval = int(1000 / self.sampling_rate)
            self.data_timer.start(interval)
        self.logger.info(f"采样率设置为: {self.sampling_rate}Hz")
        
    def set_monitoring_mode(self, mode: str):
        """设置监控模式"""
        if mode in ["simulation", "real"]:
            self.monitoring_mode = mode
            self.logger.info(f"监控模式设置为: {mode}")
        else:
            self.logger.error(f"无效的监控模式: {mode}")
            
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        return {
            'is_monitoring': self.is_monitoring,
            'hole_id': self.current_hole_id,
            'mode': self.monitoring_mode,
            'sampling_rate': self.sampling_rate,
            'probe_depth': self.probe_depth,
            'data_count': len(self.data_buffer)
        }
        
    def get_data_buffer(self) -> List[Dict]:
        """获取数据缓冲区"""
        return self.data_buffer.copy()
        
    def clear_data_buffer(self):
        """清空数据缓冲区"""
        self.data_buffer.clear()
        self.logger.info("数据缓冲区已清空")