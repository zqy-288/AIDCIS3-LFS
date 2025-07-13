"""数据管理器模块"""
from collections import deque
from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import QObject, Signal, Slot


class DataManager(QObject):
    """
    实时图表数据管理器
    负责数据缓冲、异常检测和统计
    """
    
    # 信号定义
    data_updated = Signal()
    anomaly_detected = Signal(dict)
    extremes_updated = Signal(float, float)  # min, max
    
    def __init__(self, buffer_size: int = 1000):
        super().__init__()
        self.buffer_size = buffer_size
        
        # 数据缓冲区
        self.depth_data = deque(maxlen=buffer_size)
        self.diameter_data = deque(maxlen=buffer_size)
        
        # 样品管理
        self.current_sample_index = 0
        self.sample_data_history: Dict[str, Dict] = {}
        
        # 异常数据管理
        self.anomaly_data: List[Dict] = []
        
        # 直径统计
        self.max_diameter: Optional[float] = None
        self.min_diameter: Optional[float] = None
        
        # 标准参数
        self.standard_diameter: Optional[float] = None
        self.upper_tolerance: float = 0.2
        self.lower_tolerance: float = 0.2
        
        # 当前孔位
        self.current_hole_id: Optional[str] = None
        
    def set_standard_parameters(self, diameter: float, upper_tol: float, lower_tol: float):
        """设置标准直径和公差"""
        self.standard_diameter = diameter
        self.upper_tolerance = upper_tol
        self.lower_tolerance = lower_tol
        
    @Slot(float, float)
    def update_data(self, depth: float, diameter: float):
        """更新数据"""
        # 添加新数据点
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)
        
        # 检测异常
        self._check_anomaly(depth, diameter)
        
        # 保存样品数据
        self._save_current_sample_data(depth, diameter)
        
        # 更新统计
        self._update_diameter_extremes(diameter)
        
        # 发送更新信号
        self.data_updated.emit()
        
    def _check_anomaly(self, depth: float, diameter: float):
        """检测异常数据点"""
        if self.standard_diameter is None:
            return
            
        upper_limit = self.standard_diameter + self.upper_tolerance
        lower_limit = self.standard_diameter - self.lower_tolerance
        
        if diameter > upper_limit or diameter < lower_limit:
            # 计算偏差
            if diameter > upper_limit:
                deviation = diameter - upper_limit
            else:
                deviation = lower_limit - diameter
                
            # 创建异常记录
            anomaly_info = {
                'depth': depth,
                'diameter': diameter,
                'deviation': deviation,
                'standard_diameter': self.standard_diameter,
                'upper_limit': upper_limit,
                'lower_limit': lower_limit,
                'sample_id': self.current_hole_id or f"Sample_{self.current_sample_index}"
            }
            
            self.anomaly_data.append(anomaly_info)
            self.anomaly_detected.emit(anomaly_info)
            
    def _save_current_sample_data(self, depth: float, diameter: float):
        """保存当前样品数据"""
        sample_key = self.current_hole_id or f"Sample_{self.current_sample_index}"
        
        if sample_key not in self.sample_data_history:
            self.sample_data_history[sample_key] = {
                'depths': [],
                'diameters': [],
                'anomalies': []
            }
            
        self.sample_data_history[sample_key]['depths'].append(depth)
        self.sample_data_history[sample_key]['diameters'].append(diameter)
        
    def _update_diameter_extremes(self, diameter: float):
        """更新直径极值"""
        if self.max_diameter is None or diameter > self.max_diameter:
            self.max_diameter = diameter
            
        if self.min_diameter is None or diameter < self.min_diameter:
            self.min_diameter = diameter
            
        if self.max_diameter is not None and self.min_diameter is not None:
            self.extremes_updated.emit(self.min_diameter, self.max_diameter)
            
    def clear_data(self):
        """清除所有数据"""
        self.depth_data.clear()
        self.diameter_data.clear()
        self.anomaly_data.clear()
        self.max_diameter = None
        self.min_diameter = None
        self.data_updated.emit()
        
    def set_current_hole(self, hole_id: str):
        """设置当前孔位"""
        self.current_hole_id = hole_id
        self.current_sample_index += 1
        
    def get_current_data(self) -> Tuple[list, list]:
        """获取当前数据"""
        return list(self.depth_data), list(self.diameter_data)
        
    def get_anomaly_count(self) -> int:
        """获取异常数量"""
        return len(self.anomaly_data)
        
    def get_recent_anomalies(self, count: int = 10) -> List[Dict]:
        """获取最近的异常"""
        return self.anomaly_data[-count:] if len(self.anomaly_data) > count else self.anomaly_data
        
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.diameter_data:
            return {
                'count': 0,
                'min': None,
                'max': None,
                'avg': None
            }
            
        diameters = list(self.diameter_data)
        return {
            'count': len(diameters),
            'min': min(diameters),
            'max': max(diameters),
            'avg': sum(diameters) / len(diameters)
        }
        
    def load_sample_data(self, sample_key: str):
        """加载样品数据"""
        if sample_key in self.sample_data_history:
            data = self.sample_data_history[sample_key]
            self.depth_data = deque(data['depths'], maxlen=self.buffer_size)
            self.diameter_data = deque(data['diameters'], maxlen=self.buffer_size)
            self.data_updated.emit()
            return True
        return False