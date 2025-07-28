"""
异常检测组件
负责检测直径数据中的异常值
"""
from typing import List, Tuple, Dict, Optional
import numpy as np
from PySide6.QtCore import QObject, Signal
from collections import deque
from ..utils.constants import ANOMALY_THRESHOLD, MAX_ANOMALIES_DISPLAY


class AnomalyDetector(QObject):
    """异常检测器"""
    
    # 信号定义
    anomaly_detected = Signal(int, float, float)  # 索引，深度，直径
    anomalies_updated = Signal(list)  # 异常点索引列表
    threshold_changed = Signal(float)  # 阈值变化
    
    def __init__(self):
        super().__init__()
        
        # 检测参数
        self._threshold = ANOMALY_THRESHOLD
        self._detection_method = 'tolerance'  # 'tolerance', 'statistical', 'gradient'
        
        # 标准直径和公差
        self._standard_diameter = None
        self._tolerance = None
        
        # 统计参数（用于统计方法）
        self._window_size = 20
        self._sigma_multiplier = 3.0
        
        # 梯度参数（用于梯度方法）
        self._gradient_threshold = 0.5
        
        # 异常记录
        self._anomaly_indices = []
        self._anomaly_history = deque(maxlen=1000)  # 历史异常记录
        
        # 缓存
        self._last_data_length = 0
        
    def detect_anomalies(self, depth_data: List[float], diameter_data: List[float]) -> List[int]:
        """检测异常点"""
        if len(depth_data) != len(diameter_data) or not diameter_data:
            return []
            
        # 根据检测方法执行检测
        if self._detection_method == 'tolerance':
            anomalies = self._detect_by_tolerance(diameter_data)
        elif self._detection_method == 'statistical':
            anomalies = self._detect_by_statistics(diameter_data)
        elif self._detection_method == 'gradient':
            anomalies = self._detect_by_gradient(diameter_data)
        else:
            anomalies = []
            
        # 更新异常记录
        self._anomaly_indices = anomalies
        
        # 记录新检测到的异常
        if len(diameter_data) > self._last_data_length:
            for i in range(self._last_data_length, len(diameter_data)):
                if i in anomalies:
                    self._anomaly_history.append({
                        'index': i,
                        'depth': depth_data[i],
                        'diameter': diameter_data[i],
                        'method': self._detection_method
                    })
                    self.anomaly_detected.emit(i, depth_data[i], diameter_data[i])
                    
        self._last_data_length = len(diameter_data)
        
        # 限制显示的异常点数量
        if len(anomalies) > MAX_ANOMALIES_DISPLAY:
            # 保留最新的异常点
            anomalies = anomalies[-MAX_ANOMALIES_DISPLAY:]
            
        # 发送更新信号
        self.anomalies_updated.emit(anomalies)
        
        return anomalies
        
    def set_detection_method(self, method: str):
        """设置检测方法"""
        if method in ['tolerance', 'statistical', 'gradient']:
            self._detection_method = method
            
    def set_tolerance_parameters(self, standard_diameter: float, tolerance: float):
        """设置公差检测参数"""
        self._standard_diameter = standard_diameter
        self._tolerance = tolerance
        self._threshold = tolerance
        self.threshold_changed.emit(tolerance)
        
    def set_statistical_parameters(self, window_size: int, sigma_multiplier: float):
        """设置统计检测参数"""
        self._window_size = window_size
        self._sigma_multiplier = sigma_multiplier
        
    def set_gradient_threshold(self, threshold: float):
        """设置梯度检测阈值"""
        self._gradient_threshold = threshold
        
    def get_anomaly_statistics(self) -> Dict[str, any]:
        """获取异常统计信息"""
        if not self._anomaly_history:
            return {
                'total_count': 0,
                'detection_rate': 0.0,
                'average_deviation': 0.0,
                'max_deviation': 0.0,
                'methods_used': {}
            }
            
        # 计算统计信息
        deviations = []
        methods_count = {}
        
        for anomaly in self._anomaly_history:
            if self._standard_diameter is not None:
                deviation = abs(anomaly['diameter'] - self._standard_diameter)
                deviations.append(deviation)
                
            method = anomaly['method']
            methods_count[method] = methods_count.get(method, 0) + 1
            
        return {
            'total_count': len(self._anomaly_history),
            'detection_rate': len(self._anomaly_indices) / max(1, self._last_data_length),
            'average_deviation': np.mean(deviations) if deviations else 0.0,
            'max_deviation': np.max(deviations) if deviations else 0.0,
            'methods_used': methods_count
        }
        
    def _detect_by_tolerance(self, diameter_data: List[float]) -> List[int]:
        """基于公差的异常检测"""
        if self._standard_diameter is None or self._tolerance is None:
            return []
            
        anomalies = []
        upper_limit = self._standard_diameter + self._tolerance
        lower_limit = self._standard_diameter - self._tolerance
        
        for i, diameter in enumerate(diameter_data):
            if diameter < lower_limit or diameter > upper_limit:
                anomalies.append(i)
                
        return anomalies
        
    def _detect_by_statistics(self, diameter_data: List[float]) -> List[int]:
        """基于统计的异常检测"""
        anomalies = []
        data_array = np.array(diameter_data)
        
        for i in range(len(diameter_data)):
            # 计算局部窗口的统计参数
            start_idx = max(0, i - self._window_size // 2)
            end_idx = min(len(diameter_data), i + self._window_size // 2 + 1)
            
            if end_idx - start_idx < 3:  # 窗口太小，跳过
                continue
                
            window_data = data_array[start_idx:end_idx]
            
            # 排除当前点计算统计参数
            window_without_current = np.concatenate([
                window_data[:i-start_idx],
                window_data[i-start_idx+1:]
            ])
            
            if len(window_without_current) > 0:
                mean = np.mean(window_without_current)
                std = np.std(window_without_current)
                
                # 检查是否超出阈值
                if abs(diameter_data[i] - mean) > self._sigma_multiplier * std:
                    anomalies.append(i)
                    
        return anomalies
        
    def _detect_by_gradient(self, diameter_data: List[float]) -> List[int]:
        """基于梯度的异常检测"""
        if len(diameter_data) < 2:
            return []
            
        anomalies = []
        data_array = np.array(diameter_data)
        
        # 计算梯度
        gradients = np.gradient(data_array)
        
        # 检测梯度异常
        for i, grad in enumerate(gradients):
            if abs(grad) > self._gradient_threshold:
                anomalies.append(i)
                
        return anomalies
        
    def clear_anomalies(self):
        """清除异常记录"""
        self._anomaly_indices = []
        self._anomaly_history.clear()
        self._last_data_length = 0
        self.anomalies_updated.emit([])
        
    def get_anomaly_details(self, index: int) -> Optional[Dict[str, any]]:
        """获取特定异常点的详细信息"""
        for anomaly in self._anomaly_history:
            if anomaly['index'] == index:
                return anomaly
        return None
        
    def export_anomaly_report(self) -> List[Dict[str, any]]:
        """导出异常报告"""
        return list(self._anomaly_history)
        
    def set_custom_detector(self, detector_func):
        """设置自定义检测函数"""
        # 允许用户提供自定义的异常检测函数
        # detector_func应该接受diameter_data并返回异常索引列表
        self._custom_detector = detector_func
        self._detection_method = 'custom'
        
    def batch_detect(self, data_batches: List[Tuple[List[float], List[float]]]) -> List[List[int]]:
        """批量检测多组数据"""
        results = []
        for depth_data, diameter_data in data_batches:
            anomalies = self.detect_anomalies(depth_data, diameter_data)
            results.append(anomalies)
        return results