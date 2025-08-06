"""
P2 智能异常检测器
整合自 modules/realtime_chart_p2/components/anomaly_detector.py
提供多种异常检测算法和智能分析
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal


class AnomalyType(Enum):
    """异常类型枚举"""
    TOLERANCE_EXCEEDED = "tolerance_exceeded"  # 超出公差
    STATISTICAL_OUTLIER = "statistical_outlier"  # 统计离群值
    TREND_ANOMALY = "trend_anomaly"  # 趋势异常
    SPIKE = "spike"  # 尖峰
    DRIFT = "drift"  # 漂移
    PATTERN_BREAK = "pattern_break"  # 模式破坏


class DetectionMethod(Enum):
    """检测方法枚举"""
    TOLERANCE_BASED = "tolerance_based"  # 基于公差
    STATISTICAL = "statistical"  # 统计方法
    ISOLATION_FOREST = "isolation_forest"  # 孤立森林
    LOCAL_OUTLIER = "local_outlier"  # 局部异常因子
    COMBINED = "combined"  # 组合方法


@dataclass
class AnomalyResult:
    """异常检测结果"""
    index: int
    depth: float
    diameter: float
    anomaly_type: AnomalyType
    confidence: float  # 置信度 0-1
    severity: str  # low, medium, high
    description: str
    timestamp: datetime
    
    
@dataclass
class DetectionConfig:
    """检测配置"""
    method: DetectionMethod = DetectionMethod.COMBINED
    tolerance: float = 0.2
    statistical_threshold: float = 3.0  # 标准差倍数
    window_size: int = 50  # 滑动窗口大小
    min_samples: int = 10  # 最小样本数
    sensitivity: float = 0.5  # 敏感度 0-1
    enable_trend_detection: bool = True
    enable_pattern_detection: bool = True


class SmartAnomalyDetector(QObject):
    """
    智能异常检测器
    
    功能：
    1. 多种异常检测算法
    2. 自适应阈值调整
    3. 趋势分析和预测
    4. 异常分类和严重性评估
    5. 实时检测和历史分析
    """
    
    # 信号定义
    anomaly_detected = Signal(dict)  # 检测到异常
    threshold_updated = Signal(float, float)  # 阈值更新
    pattern_detected = Signal(str, dict)  # 模式检测
    
    def __init__(self, standard_diameter: float = 17.6, 
                 tolerance: float = 0.2, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 基本参数
        self.standard_diameter = standard_diameter
        self.tolerance = tolerance
        
        # 检测配置
        self.config = DetectionConfig()
        
        # 历史数据缓存
        self.historical_data = []
        self.anomaly_history = []
        
        # 统计信息
        self.running_stats = {
            'mean': standard_diameter,
            'std': 0.1,
            'min': standard_diameter - tolerance,
            'max': standard_diameter + tolerance,
            'count': 0
        }
        
        # 自适应阈值
        self.adaptive_threshold = {
            'upper': standard_diameter + tolerance,
            'lower': standard_diameter - tolerance,
            'update_count': 0
        }
        
        # 趋势分析
        self.trend_buffer = []
        self.trend_window = 20
        
        # 模式检测
        self.pattern_buffer = []
        self.pattern_templates = {}
        
        self.logger.debug(f"异常检测器初始化: 标准直径={standard_diameter}, 公差={tolerance}")
        
    def detect_anomalies(self, depths: List[float], diameters: List[float], 
                        timestamps: Optional[List[datetime]] = None) -> List[AnomalyResult]:
        """
        检测异常
        
        Args:
            depths: 深度数据
            diameters: 直径数据
            timestamps: 时间戳（可选）
            
        Returns:
            List[AnomalyResult]: 异常结果列表
        """
        if len(depths) != len(diameters):
            raise ValueError("深度和直径数据长度不匹配")
            
        if timestamps is None:
            timestamps = [datetime.now()] * len(diameters)
            
        anomalies = []
        
        try:
            # 更新历史数据
            for depth, diameter in zip(depths, diameters):
                self.historical_data.append((depth, diameter))
                
            # 更新统计信息
            self._update_statistics(diameters)
            
            # 根据配置的方法进行检测
            if self.config.method == DetectionMethod.TOLERANCE_BASED:
                anomalies.extend(self._detect_tolerance_based(depths, diameters, timestamps))
            elif self.config.method == DetectionMethod.STATISTICAL:
                anomalies.extend(self._detect_statistical(depths, diameters, timestamps))
            elif self.config.method == DetectionMethod.ISOLATION_FOREST:
                anomalies.extend(self._detect_isolation_forest(depths, diameters, timestamps))
            elif self.config.method == DetectionMethod.LOCAL_OUTLIER:
                anomalies.extend(self._detect_local_outlier(depths, diameters, timestamps))
            elif self.config.method == DetectionMethod.COMBINED:
                anomalies.extend(self._detect_combined(depths, diameters, timestamps))
                
            # 趋势检测
            if self.config.enable_trend_detection:
                trend_anomalies = self._detect_trend_anomalies(depths, diameters, timestamps)
                anomalies.extend(trend_anomalies)
                
            # 模式检测
            if self.config.enable_pattern_detection:
                pattern_anomalies = self._detect_pattern_anomalies(depths, diameters, timestamps)
                anomalies.extend(pattern_anomalies)
                
            # 去重和排序
            anomalies = self._deduplicate_anomalies(anomalies)
            anomalies.sort(key=lambda x: x.index)
            
            # 更新异常历史
            self.anomaly_history.extend(anomalies)
            
            # 发射信号
            for anomaly in anomalies:
                self.anomaly_detected.emit(self._anomaly_to_dict(anomaly))
                
            self.logger.debug(f"检测完成: {len(anomalies)} 个异常")
            return anomalies
            
        except Exception as e:
            self.logger.error(f"异常检测失败: {e}")
            return []
            
    def _detect_tolerance_based(self, depths: List[float], diameters: List[float], 
                               timestamps: List[datetime]) -> List[AnomalyResult]:
        """基于公差的检测"""
        anomalies = []
        
        for i, (depth, diameter, timestamp) in enumerate(zip(depths, diameters, timestamps)):
            deviation = abs(diameter - self.standard_diameter)
            
            if deviation > self.tolerance:
                severity = self._calculate_severity(deviation, self.tolerance)
                confidence = min(1.0, deviation / self.tolerance)
                
                anomaly = AnomalyResult(
                    index=i,
                    depth=depth,
                    diameter=diameter,
                    anomaly_type=AnomalyType.TOLERANCE_EXCEEDED,
                    confidence=confidence,
                    severity=severity,
                    description=f"直径偏差 {deviation:.3f}mm 超出公差 ±{self.tolerance}mm",
                    timestamp=timestamp
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    def _detect_statistical(self, depths: List[float], diameters: List[float], 
                           timestamps: List[datetime]) -> List[AnomalyResult]:
        """统计方法检测"""
        anomalies = []
        
        if len(diameters) < self.config.min_samples:
            return anomalies
            
        # 计算统计参数
        mean_val = np.mean(diameters)
        std_val = np.std(diameters)
        threshold = self.config.statistical_threshold * std_val
        
        for i, (depth, diameter, timestamp) in enumerate(zip(depths, diameters, timestamps)):
            deviation = abs(diameter - mean_val)
            
            if deviation > threshold:
                confidence = min(1.0, deviation / threshold)
                severity = self._calculate_severity(deviation, threshold)
                
                anomaly = AnomalyResult(
                    index=i,
                    depth=depth,
                    diameter=diameter,
                    anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                    confidence=confidence,
                    severity=severity,
                    description=f"统计离群值: 偏差 {deviation:.3f}mm > {threshold:.3f}mm",
                    timestamp=timestamp
                )
                anomalies.append(anomaly)
                
        return anomalies
        
    def _detect_isolation_forest(self, depths: List[float], diameters: List[float], 
                                timestamps: List[datetime]) -> List[AnomalyResult]:
        """孤立森林检测"""
        anomalies = []
        
        try:
            from sklearn.ensemble import IsolationForest
            
            if len(diameters) < self.config.min_samples:
                return anomalies
                
            # 准备数据
            X = np.column_stack([depths, diameters])
            
            # 创建模型
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso_forest.fit_predict(X)
            scores = iso_forest.score_samples(X)
            
            for i, (depth, diameter, timestamp, pred, score) in enumerate(
                zip(depths, diameters, timestamps, predictions, scores)):
                
                if pred == -1:  # 异常
                    confidence = abs(score)
                    severity = self._calculate_severity_from_score(score)
                    
                    anomaly = AnomalyResult(
                        index=i,
                        depth=depth,
                        diameter=diameter,
                        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                        confidence=confidence,
                        severity=severity,
                        description=f"孤立森林检测异常: 分数 {score:.3f}",
                        timestamp=timestamp
                    )
                    anomalies.append(anomaly)
                    
        except ImportError:
            self.logger.warning("sklearn不可用，跳过孤立森林检测")
        except Exception as e:
            self.logger.error(f"孤立森林检测失败: {e}")
            
        return anomalies
        
    def _detect_local_outlier(self, depths: List[float], diameters: List[float], 
                             timestamps: List[datetime]) -> List[AnomalyResult]:
        """局部异常因子检测"""
        anomalies = []
        
        try:
            from sklearn.neighbors import LocalOutlierFactor
            
            if len(diameters) < self.config.min_samples:
                return anomalies
                
            # 准备数据
            X = np.column_stack([depths, diameters])
            
            # 创建模型
            lof = LocalOutlierFactor(n_neighbors=min(20, len(diameters) // 2))
            predictions = lof.fit_predict(X)
            scores = lof.negative_outlier_factor_
            
            for i, (depth, diameter, timestamp, pred, score) in enumerate(
                zip(depths, diameters, timestamps, predictions, scores)):
                
                if pred == -1:  # 异常
                    confidence = abs(score)
                    severity = self._calculate_severity_from_score(score)
                    
                    anomaly = AnomalyResult(
                        index=i,
                        depth=depth,
                        diameter=diameter,
                        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                        confidence=confidence,
                        severity=severity,
                        description=f"局部异常因子检测: LOF分数 {score:.3f}",
                        timestamp=timestamp
                    )
                    anomalies.append(anomaly)
                    
        except ImportError:
            self.logger.warning("sklearn不可用，跳过LOF检测")
        except Exception as e:
            self.logger.error(f"LOF检测失败: {e}")
            
        return anomalies
        
    def _detect_combined(self, depths: List[float], diameters: List[float], 
                        timestamps: List[datetime]) -> List[AnomalyResult]:
        """组合方法检测"""
        all_anomalies = []
        
        # 收集所有方法的结果
        all_anomalies.extend(self._detect_tolerance_based(depths, diameters, timestamps))
        all_anomalies.extend(self._detect_statistical(depths, diameters, timestamps))
        
        # 如果数据量足够，使用机器学习方法
        if len(diameters) >= self.config.min_samples:
            all_anomalies.extend(self._detect_isolation_forest(depths, diameters, timestamps))
            all_anomalies.extend(self._detect_local_outlier(depths, diameters, timestamps))
            
        return all_anomalies
        
    def _detect_trend_anomalies(self, depths: List[float], diameters: List[float], 
                               timestamps: List[datetime]) -> List[AnomalyResult]:
        """趋势异常检测"""
        anomalies = []
        
        if len(diameters) < self.trend_window:
            return anomalies
            
        try:
            # 使用滑动窗口检测趋势变化
            for i in range(self.trend_window, len(diameters)):
                window_data = diameters[i-self.trend_window:i]
                
                # 计算趋势
                x = np.arange(len(window_data))
                coeffs = np.polyfit(x, window_data, 1)
                slope = coeffs[0]
                
                # 检测异常趋势
                if abs(slope) > 0.01:  # 阈值可配置
                    trend_type = AnomalyType.DRIFT if abs(slope) > 0.02 else AnomalyType.TREND_ANOMALY
                    
                    anomaly = AnomalyResult(
                        index=i,
                        depth=depths[i],
                        diameter=diameters[i],
                        anomaly_type=trend_type,
                        confidence=min(1.0, abs(slope) * 100),
                        severity=self._calculate_severity(abs(slope), 0.01),
                        description=f"趋势异常: 斜率 {slope:.4f}",
                        timestamp=timestamps[i]
                    )
                    anomalies.append(anomaly)
                    
        except Exception as e:
            self.logger.error(f"趋势检测失败: {e}")
            
        return anomalies
        
    def _detect_pattern_anomalies(self, depths: List[float], diameters: List[float], 
                                 timestamps: List[datetime]) -> List[AnomalyResult]:
        """模式异常检测"""
        anomalies = []
        
        # 检测尖峰
        spike_anomalies = self._detect_spikes(depths, diameters, timestamps)
        anomalies.extend(spike_anomalies)
        
        return anomalies
        
    def _detect_spikes(self, depths: List[float], diameters: List[float], 
                      timestamps: List[datetime]) -> List[AnomalyResult]:
        """尖峰检测"""
        anomalies = []
        
        if len(diameters) < 5:
            return anomalies
            
        try:
            # 使用中位数绝对偏差检测尖峰
            median = np.median(diameters)
            mad = np.median(np.abs(np.array(diameters) - median))
            threshold = 3 * mad
            
            for i, (depth, diameter, timestamp) in enumerate(zip(depths, diameters, timestamps)):
                if abs(diameter - median) > threshold:
                    # 检查是否为局部尖峰
                    if self._is_local_spike(diameters, i):
                        anomaly = AnomalyResult(
                            index=i,
                            depth=depth,
                            diameter=diameter,
                            anomaly_type=AnomalyType.SPIKE,
                            confidence=min(1.0, abs(diameter - median) / threshold),
                            severity=self._calculate_severity(abs(diameter - median), threshold),
                            description=f"尖峰异常: 偏差 {abs(diameter - median):.3f}mm",
                            timestamp=timestamp
                        )
                        anomalies.append(anomaly)
                        
        except Exception as e:
            self.logger.error(f"尖峰检测失败: {e}")
            
        return anomalies
        
    def _is_local_spike(self, diameters: List[float], index: int, window: int = 3) -> bool:
        """检查是否为局部尖峰"""
        start = max(0, index - window)
        end = min(len(diameters), index + window + 1)
        
        local_data = diameters[start:end]
        current_value = diameters[index]
        
        # 检查是否为局部极值
        local_median = np.median([d for i, d in enumerate(local_data) if i != index - start])
        return abs(current_value - local_median) > abs(current_value - np.mean(local_data))
        
    def _update_statistics(self, diameters: List[float]):
        """更新统计信息"""
        if not diameters:
            return
            
        # 更新运行统计
        new_data = np.array(diameters)
        
        if self.running_stats['count'] == 0:
            self.running_stats['mean'] = np.mean(new_data)
            self.running_stats['std'] = np.std(new_data)
        else:
            # 增量更新
            old_count = self.running_stats['count']
            new_count = old_count + len(new_data)
            
            old_mean = self.running_stats['mean']
            new_mean = (old_mean * old_count + np.sum(new_data)) / new_count
            
            self.running_stats['mean'] = new_mean
            self.running_stats['count'] = new_count
            
        self.running_stats['min'] = min(self.running_stats['min'], np.min(new_data))
        self.running_stats['max'] = max(self.running_stats['max'], np.max(new_data))
        
        # 更新自适应阈值
        self._update_adaptive_threshold()
        
    def _update_adaptive_threshold(self):
        """更新自适应阈值"""
        if self.running_stats['count'] < 10:
            return
            
        # 基于历史数据调整阈值
        mean = self.running_stats['mean']
        std = self.running_stats['std']
        
        # 计算新的阈值
        new_upper = mean + 2 * std
        new_lower = mean - 2 * std
        
        # 平滑更新
        alpha = 0.1  # 学习率
        self.adaptive_threshold['upper'] = (1 - alpha) * self.adaptive_threshold['upper'] + alpha * new_upper
        self.adaptive_threshold['lower'] = (1 - alpha) * self.adaptive_threshold['lower'] + alpha * new_lower
        
        self.adaptive_threshold['update_count'] += 1
        
        # 发射阈值更新信号
        self.threshold_updated.emit(self.adaptive_threshold['lower'], self.adaptive_threshold['upper'])
        
    def _calculate_severity(self, deviation: float, threshold: float) -> str:
        """计算严重程度"""
        ratio = deviation / threshold if threshold > 0 else float('inf')
        
        if ratio < 1.5:
            return "low"
        elif ratio < 3.0:
            return "medium"
        else:
            return "high"
            
    def _calculate_severity_from_score(self, score: float) -> str:
        """从分数计算严重程度"""
        abs_score = abs(score)
        
        if abs_score < 0.1:
            return "low"
        elif abs_score < 0.2:
            return "medium"
        else:
            return "high"
            
    def _deduplicate_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """去除重复的异常"""
        if not anomalies:
            return anomalies
            
        # 按索引分组
        index_groups = {}
        for anomaly in anomalies:
            if anomaly.index not in index_groups:
                index_groups[anomaly.index] = []
            index_groups[anomaly.index].append(anomaly)
            
        # 每个索引保留置信度最高的异常
        deduplicated = []
        for index, group in index_groups.items():
            best_anomaly = max(group, key=lambda x: x.confidence)
            deduplicated.append(best_anomaly)
            
        return deduplicated
        
    def _anomaly_to_dict(self, anomaly: AnomalyResult) -> Dict[str, Any]:
        """将异常结果转换为字典"""
        return {
            'index': anomaly.index,
            'depth': anomaly.depth,
            'diameter': anomaly.diameter,
            'type': anomaly.anomaly_type.value,
            'confidence': anomaly.confidence,
            'severity': anomaly.severity,
            'description': anomaly.description,
            'timestamp': anomaly.timestamp.isoformat()
        }
        
    # 配置方法
    def set_parameters(self, standard_diameter: float, tolerance: float):
        """设置检测参数"""
        self.standard_diameter = standard_diameter
        self.tolerance = tolerance
        self.logger.debug(f"设置检测参数: {standard_diameter}±{tolerance}mm")
        
    def set_detection_method(self, method: DetectionMethod):
        """设置检测方法"""
        self.config.method = method
        self.logger.debug(f"设置检测方法: {method.value}")
        
    def set_sensitivity(self, sensitivity: float):
        """设置敏感度"""
        self.config.sensitivity = max(0.0, min(1.0, sensitivity))
        # 根据敏感度调整阈值
        self.config.statistical_threshold = 2.0 + (1.0 - self.config.sensitivity) * 2.0
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取检测统计信息"""
        return {
            'running_stats': self.running_stats.copy(),
            'adaptive_threshold': self.adaptive_threshold.copy(),
            'total_anomalies': len(self.anomaly_history),
            'config': {
                'method': self.config.method.value,
                'sensitivity': self.config.sensitivity,
                'statistical_threshold': self.config.statistical_threshold
            }
        }
        
    def clear_history(self):
        """清除历史数据"""
        self.historical_data.clear()
        self.anomaly_history.clear()
        self.trend_buffer.clear()
        self.pattern_buffer.clear()
        
        # 重置统计信息
        self.running_stats = {
            'mean': self.standard_diameter,
            'std': 0.1,
            'min': self.standard_diameter - self.tolerance,
            'max': self.standard_diameter + self.tolerance,
            'count': 0
        }
        
        self.logger.info("异常检测历史数据已清除")