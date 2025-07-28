"""
数据管理组件
负责数据缓冲、统计计算和数据访问
"""
from typing import List, Tuple, Optional, Dict
from collections import deque
import numpy as np
from PySide6.QtCore import QObject, Signal
import threading
from ..utils.constants import MAX_DATA_POINTS, DATA_BUFFER_SIZE


class DataManager(QObject):
    """数据管理器"""
    
    # 信号定义
    data_updated = Signal()  # 数据更新
    buffer_overflow = Signal(int)  # 缓冲区溢出，参数为丢弃的数据点数
    statistics_updated = Signal(dict)  # 统计信息更新
    
    def __init__(self):
        super().__init__()
        
        # 数据缓冲区
        self._depth_buffer = deque(maxlen=DATA_BUFFER_SIZE)
        self._diameter_buffer = deque(maxlen=DATA_BUFFER_SIZE)
        
        # 当前显示数据
        self._display_depth = []
        self._display_diameter = []
        
        # 统计信息
        self._statistics = {
            'count': 0,
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'last_value': 0.0
        }
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 数据点计数器
        self._total_points = 0
        self._discarded_points = 0
        
    def add_data_point(self, depth: float, diameter: float):
        """添加单个数据点"""
        with self._lock:
            # 检查缓冲区溢出
            if len(self._depth_buffer) == DATA_BUFFER_SIZE:
                self._discarded_points += 1
                
            # 添加到缓冲区
            self._depth_buffer.append(depth)
            self._diameter_buffer.append(diameter)
            self._total_points += 1
            
            # 更新显示数据
            self._update_display_data()
            
            # 更新统计信息
            self._update_statistics()
            
        # 发送信号
        self.data_updated.emit()
        
    def add_data_batch(self, depths: List[float], diameters: List[float]):
        """批量添加数据"""
        if len(depths) != len(diameters):
            raise ValueError("深度和直径数据长度不匹配")
            
        with self._lock:
            # 检查缓冲区溢出
            overflow_count = max(0, len(self._depth_buffer) + len(depths) - DATA_BUFFER_SIZE)
            if overflow_count > 0:
                self._discarded_points += overflow_count
                self.buffer_overflow.emit(overflow_count)
                
            # 批量添加
            self._depth_buffer.extend(depths)
            self._diameter_buffer.extend(diameters)
            self._total_points += len(depths)
            
            # 更新显示数据
            self._update_display_data()
            
            # 更新统计信息
            self._update_statistics()
            
        # 发送信号
        self.data_updated.emit()
        
    def get_display_data(self) -> Tuple[List[float], List[float]]:
        """获取用于显示的数据"""
        with self._lock:
            return self._display_depth.copy(), self._display_diameter.copy()
            
    def get_recent_data(self, count: int) -> Tuple[List[float], List[float]]:
        """获取最近的N个数据点"""
        with self._lock:
            if count >= len(self._depth_buffer):
                return list(self._depth_buffer), list(self._diameter_buffer)
            else:
                depths = list(self._depth_buffer)[-count:]
                diameters = list(self._diameter_buffer)[-count:]
                return depths, diameters
                
    def get_data_range(self, start_depth: float, end_depth: float) -> Tuple[List[float], List[float]]:
        """获取指定深度范围内的数据"""
        with self._lock:
            depths = []
            diameters = []
            
            for i, depth in enumerate(self._depth_buffer):
                if start_depth <= depth <= end_depth:
                    depths.append(depth)
                    diameters.append(self._diameter_buffer[i])
                    
            return depths, diameters
            
    def get_statistics(self) -> Dict[str, float]:
        """获取统计信息"""
        with self._lock:
            return self._statistics.copy()
            
    def get_buffer_info(self) -> Dict[str, int]:
        """获取缓冲区信息"""
        with self._lock:
            return {
                'buffer_size': len(self._depth_buffer),
                'buffer_capacity': DATA_BUFFER_SIZE,
                'total_points': self._total_points,
                'discarded_points': self._discarded_points,
                'display_points': len(self._display_depth)
            }
            
    def clear_data(self):
        """清除所有数据"""
        with self._lock:
            self._depth_buffer.clear()
            self._diameter_buffer.clear()
            self._display_depth.clear()
            self._display_diameter.clear()
            
            # 重置统计信息
            self._statistics = {
                'count': 0,
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'last_value': 0.0
            }
            
            # 重置计数器
            self._total_points = 0
            self._discarded_points = 0
            
        self.data_updated.emit()
        
    def set_max_display_points(self, max_points: int):
        """设置最大显示点数"""
        with self._lock:
            self._max_display_points = max_points
            self._update_display_data()
            
        self.data_updated.emit()
        
    def _update_display_data(self):
        """更新显示数据（内部方法，需要在锁内调用）"""
        # 限制显示点数
        if len(self._depth_buffer) > MAX_DATA_POINTS:
            self._display_depth = list(self._depth_buffer)[-MAX_DATA_POINTS:]
            self._display_diameter = list(self._diameter_buffer)[-MAX_DATA_POINTS:]
        else:
            self._display_depth = list(self._depth_buffer)
            self._display_diameter = list(self._diameter_buffer)
            
    def _update_statistics(self):
        """更新统计信息（内部方法，需要在锁内调用）"""
        if self._diameter_buffer:
            diameter_array = np.array(self._diameter_buffer)
            self._statistics = {
                'count': len(self._diameter_buffer),
                'mean': float(np.mean(diameter_array)),
                'std': float(np.std(diameter_array)),
                'min': float(np.min(diameter_array)),
                'max': float(np.max(diameter_array)),
                'last_value': float(self._diameter_buffer[-1])
            }
            
            # 发送统计信息更新信号
            self.statistics_updated.emit(self._statistics)
            
    def export_data(self) -> Dict[str, List[float]]:
        """导出所有数据"""
        with self._lock:
            return {
                'depth': list(self._depth_buffer),
                'diameter': list(self._diameter_buffer)
            }
            
    def import_data(self, depths: List[float], diameters: List[float]):
        """导入数据（会清除现有数据）"""
        if len(depths) != len(diameters):
            raise ValueError("深度和直径数据长度不匹配")
            
        with self._lock:
            # 清除现有数据
            self._depth_buffer.clear()
            self._diameter_buffer.clear()
            
            # 导入新数据
            self._depth_buffer.extend(depths[-DATA_BUFFER_SIZE:])  # 只保留最后的数据
            self._diameter_buffer.extend(diameters[-DATA_BUFFER_SIZE:])
            
            # 更新显示数据和统计信息
            self._update_display_data()
            self._update_statistics()
            
            # 重置计数器
            self._total_points = len(depths)
            self._discarded_points = max(0, len(depths) - DATA_BUFFER_SIZE)
            
        self.data_updated.emit()
        
    def get_data_at_index(self, index: int) -> Optional[Tuple[float, float]]:
        """获取指定索引的数据点"""
        with self._lock:
            if 0 <= index < len(self._depth_buffer):
                return self._depth_buffer[index], self._diameter_buffer[index]
            return None
            
    def find_nearest_point(self, target_depth: float) -> Optional[Tuple[int, float, float]]:
        """查找最接近目标深度的数据点"""
        with self._lock:
            if not self._depth_buffer:
                return None
                
            # 转换为numpy数组进行快速查找
            depths = np.array(self._depth_buffer)
            index = np.argmin(np.abs(depths - target_depth))
            
            return index, self._depth_buffer[index], self._diameter_buffer[index]