"""
P2 实时数据管理器
整合自 modules/realtime_chart_p2/components/data_manager.py
负责数据缓存、统计分析和持久化
"""

import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer


@dataclass
class DataPoint:
    """数据点结构"""
    depth: float
    diameter: float
    timestamp: datetime
    hole_id: Optional[str] = None
    batch_id: Optional[str] = None
    quality: str = "normal"  # normal, anomaly, outlier


@dataclass
class StatisticsInfo:
    """统计信息结构"""
    count: int
    mean: float
    std: float
    min_val: float
    max_val: float
    median: float
    q25: float
    q75: float
    anomaly_count: int
    anomaly_rate: float


class RealtimeDataManager(QObject):
    """
    实时数据管理器
    
    功能：
    1. 数据缓存和管理
    2. 统计分析和计算
    3. 数据过滤和查询
    4. 数据持久化
    5. 性能监控
    """
    
    # 信号定义
    data_added = Signal(dict)  # 数据添加信号
    statistics_updated = Signal(dict)  # 统计更新信号
    buffer_full = Signal(int)  # 缓冲区满信号
    data_exported = Signal(str)  # 数据导出信号
    
    def __init__(self, max_size: int = 50000, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 数据存储
        self.max_size = max_size
        self.data_points = deque(maxlen=max_size)
        self.anomaly_points = deque(maxlen=max_size // 10)
        
        # 索引和缓存
        self.depth_index = {}  # 深度索引
        self.time_index = {}   # 时间索引
        self.hole_index = {}   # 孔位索引
        
        # 统计缓存
        self._stats_cache = None
        self._stats_cache_time = None
        self._stats_cache_size = 0
        self.stats_cache_timeout = 5.0  # 秒
        
        # 当前会话信息
        self.current_hole_id = None
        self.current_batch_id = None
        self.session_start_time = datetime.now()
        
        # 配置参数
        self.standard_diameter = 17.6
        self.tolerance = 0.2
        self.outlier_threshold = 3.0  # 标准差倍数
        
        # 性能监控
        self.performance_stats = {
            'total_points': 0,
            'add_operations': 0,
            'query_operations': 0,
            'export_operations': 0,
            'last_add_time': None,
            'average_add_time': 0.0
        }
        
        # 定期统计更新
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics_cache)
        self.stats_timer.start(2000)  # 2秒更新一次统计
        
    def add_data_point(self, depth: float, diameter: float, 
                      timestamp: Optional[datetime] = None,
                      hole_id: Optional[str] = None,
                      batch_id: Optional[str] = None) -> bool:
        """
        添加数据点
        
        Args:
            depth: 深度值
            diameter: 直径值
            timestamp: 时间戳
            hole_id: 孔位ID
            batch_id: 批次ID
            
        Returns:
            bool: 是否成功添加
        """
        try:
            start_time = datetime.now()
            
            if timestamp is None:
                timestamp = datetime.now()
                
            # 使用当前会话信息作为默认值
            if hole_id is None:
                hole_id = self.current_hole_id
            if batch_id is None:
                batch_id = self.current_batch_id
                
            # 数据质量检查
            quality = self._assess_data_quality(diameter)
            
            # 创建数据点
            data_point = DataPoint(
                depth=depth,
                diameter=diameter,
                timestamp=timestamp,
                hole_id=hole_id,
                batch_id=batch_id,
                quality=quality
            )
            
            # 添加到缓存
            self.data_points.append(data_point)
            
            # 如果是异常点，同时添加到异常缓存
            if quality in ['anomaly', 'outlier']:
                self.anomaly_points.append(data_point)
                
            # 更新索引
            self._update_indices(data_point)
            
            # 清除统计缓存
            self._invalidate_stats_cache()
            
            # 更新性能统计
            add_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(add_time)
            
            # 发射信号
            self.data_added.emit(asdict(data_point))
            
            # 检查缓冲区状态
            if len(self.data_points) >= self.max_size * 0.9:
                self.buffer_full.emit(len(self.data_points))
                
            return True
            
        except Exception as e:
            self.logger.error(f"添加数据点失败: {e}")
            return False
            
    def add_data_batch(self, depths: List[float], diameters: List[float],
                      timestamps: Optional[List[datetime]] = None,
                      hole_id: Optional[str] = None,
                      batch_id: Optional[str] = None) -> int:
        """
        批量添加数据点
        
        Returns:
            int: 成功添加的数据点数量
        """
        if len(depths) != len(diameters):
            raise ValueError("深度和直径数据长度不匹配")
            
        if timestamps is None:
            timestamps = [datetime.now()] * len(depths)
        elif len(timestamps) != len(depths):
            raise ValueError("时间戳数据长度不匹配")
            
        success_count = 0
        for depth, diameter, timestamp in zip(depths, diameters, timestamps):
            if self.add_data_point(depth, diameter, timestamp, hole_id, batch_id):
                success_count += 1
                
        self.logger.debug(f"批量添加数据点: {success_count}/{len(depths)}")
        return success_count
        
    def _assess_data_quality(self, diameter: float) -> str:
        """评估数据质量"""
        # 异常检测（超出公差）
        if abs(diameter - self.standard_diameter) > self.tolerance:
            return "anomaly"
            
        # 离群值检测（基于历史数据的标准差）
        if len(self.data_points) > 30:
            diameters = [dp.diameter for dp in list(self.data_points)[-30:]]
            mean_val = np.mean(diameters)
            std_val = np.std(diameters)
            
            if abs(diameter - mean_val) > self.outlier_threshold * std_val:
                return "outlier"
                
        return "normal"
        
    def _update_indices(self, data_point: DataPoint):
        """更新索引"""
        # 深度索引
        depth_key = round(data_point.depth, 1)
        if depth_key not in self.depth_index:
            self.depth_index[depth_key] = []
        self.depth_index[depth_key].append(data_point)
        
        # 时间索引（按小时）
        time_key = data_point.timestamp.replace(minute=0, second=0, microsecond=0)
        if time_key not in self.time_index:
            self.time_index[time_key] = []
        self.time_index[time_key].append(data_point)
        
        # 孔位索引
        if data_point.hole_id:
            if data_point.hole_id not in self.hole_index:
                self.hole_index[data_point.hole_id] = []
            self.hole_index[data_point.hole_id].append(data_point)
            
    def get_statistics(self, force_update: bool = False) -> StatisticsInfo:
        """
        获取统计信息
        
        Args:
            force_update: 是否强制更新缓存
            
        Returns:
            StatisticsInfo: 统计信息
        """
        try:
            current_time = datetime.now()
            current_size = len(self.data_points)
            
            # 检查缓存是否有效
            if (not force_update and 
                self._stats_cache is not None and
                self._stats_cache_time is not None and
                self._stats_cache_size == current_size and
                (current_time - self._stats_cache_time).total_seconds() < self.stats_cache_timeout):
                return self._stats_cache
                
            # 计算新的统计信息
            if len(self.data_points) == 0:
                return StatisticsInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                
            diameters = [dp.diameter for dp in self.data_points]
            anomaly_count = sum(1 for dp in self.data_points if dp.quality in ['anomaly', 'outlier'])
            
            stats = StatisticsInfo(
                count=len(diameters),
                mean=float(np.mean(diameters)),
                std=float(np.std(diameters)),
                min_val=float(np.min(diameters)),
                max_val=float(np.max(diameters)),
                median=float(np.median(diameters)),
                q25=float(np.percentile(diameters, 25)),
                q75=float(np.percentile(diameters, 75)),
                anomaly_count=anomaly_count,
                anomaly_rate=anomaly_count / len(diameters) * 100 if len(diameters) > 0 else 0
            )
            
            # 更新缓存
            self._stats_cache = stats
            self._stats_cache_time = current_time
            self._stats_cache_size = current_size
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算统计信息失败: {e}")
            return StatisticsInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            
    def _update_statistics_cache(self):
        """定期更新统计缓存"""
        stats = self.get_statistics()
        self.statistics_updated.emit(asdict(stats))
        
    def _invalidate_stats_cache(self):
        """使统计缓存失效"""
        self._stats_cache = None
        self._stats_cache_time = None
        self._stats_cache_size = 0
        
    def query_data(self, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  depth_range: Optional[Tuple[float, float]] = None,
                  hole_id: Optional[str] = None,
                  quality_filter: Optional[List[str]] = None) -> List[DataPoint]:
        """
        查询数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间  
            depth_range: 深度范围 (min_depth, max_depth)
            hole_id: 孔位ID
            quality_filter: 质量过滤器 ['normal', 'anomaly', 'outlier']
            
        Returns:
            List[DataPoint]: 匹配的数据点列表
        """
        try:
            self.performance_stats['query_operations'] += 1
            
            results = []
            
            for data_point in self.data_points:
                # 时间过滤
                if start_time and data_point.timestamp < start_time:
                    continue
                if end_time and data_point.timestamp > end_time:
                    continue
                    
                # 深度过滤
                if depth_range:
                    min_depth, max_depth = depth_range
                    if data_point.depth < min_depth or data_point.depth > max_depth:
                        continue
                        
                # 孔位过滤
                if hole_id and data_point.hole_id != hole_id:
                    continue
                    
                # 质量过滤
                if quality_filter and data_point.quality not in quality_filter:
                    continue
                    
                results.append(data_point)
                
            self.logger.debug(f"查询结果: {len(results)} 个数据点")
            return results
            
        except Exception as e:
            self.logger.error(f"查询数据失败: {e}")
            return []
            
    def get_recent_data(self, seconds: int = 60) -> List[DataPoint]:
        """获取最近N秒的数据"""
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        return self.query_data(start_time=cutoff_time)
        
    def get_anomaly_data(self) -> List[DataPoint]:
        """获取所有异常数据"""
        return list(self.anomaly_points)
        
    def clear_data(self):
        """清除所有数据"""
        self.data_points.clear()
        self.anomaly_points.clear()
        self.depth_index.clear()
        self.time_index.clear()
        self.hole_index.clear()
        self._invalidate_stats_cache()
        
        self.logger.info("数据已清除")
        
    def export_to_csv(self, filepath: str, include_anomalies_only: bool = False) -> bool:
        """
        导出数据到CSV文件
        
        Args:
            filepath: 文件路径
            include_anomalies_only: 是否只导出异常数据
            
        Returns:
            bool: 是否成功导出
        """
        try:
            self.performance_stats['export_operations'] += 1
            
            if include_anomalies_only:
                data_to_export = list(self.anomaly_points)
            else:
                data_to_export = list(self.data_points)
                
            if not data_to_export:
                self.logger.warning("没有数据可导出")
                return False
                
            # 转换为DataFrame
            df_data = []
            for dp in data_to_export:
                df_data.append({
                    'timestamp': dp.timestamp.isoformat(),
                    'depth': dp.depth,
                    'diameter': dp.diameter,
                    'hole_id': dp.hole_id,
                    'batch_id': dp.batch_id,
                    'quality': dp.quality
                })
                
            df = pd.DataFrame(df_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            self.data_exported.emit(filepath)
            self.logger.info(f"数据已导出到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False
            
    def export_statistics(self, filepath: str) -> bool:
        """导出统计信息"""
        try:
            stats = self.get_statistics()
            stats_data = asdict(stats)
            
            # 添加性能统计
            stats_data.update(self.performance_stats.copy())
            stats_data['export_time'] = datetime.now().isoformat()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"统计信息已导出到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出统计信息失败: {e}")
            return False
            
    def _update_performance_stats(self, add_time: float):
        """更新性能统计"""
        self.performance_stats['total_points'] = len(self.data_points)
        self.performance_stats['add_operations'] += 1
        self.performance_stats['last_add_time'] = add_time
        
        # 计算平均添加时间
        current_avg = self.performance_stats['average_add_time']
        operations = self.performance_stats['add_operations']
        self.performance_stats['average_add_time'] = (current_avg * (operations - 1) + add_time) / operations
        
    # 配置方法
    def set_standard_parameters(self, diameter: float, tolerance: float):
        """设置标准参数"""
        self.standard_diameter = diameter
        self.tolerance = tolerance
        self.logger.debug(f"设置标准参数: {diameter}±{tolerance}mm")
        
    def set_current_session(self, hole_id: str, batch_id: str = None):
        """设置当前会话"""
        self.current_hole_id = hole_id
        self.current_batch_id = batch_id
        self.session_start_time = datetime.now()
        self.logger.debug(f"设置当前会话: 孔位={hole_id}, 批次={batch_id}")
        
    def get_data_count(self) -> int:
        """获取数据总数"""
        return len(self.data_points)
        
    def get_anomaly_count(self) -> int:
        """获取异常数据总数"""
        return len(self.anomaly_points)
        
    def get_performance_info(self) -> Dict[str, Any]:
        """获取性能信息"""
        return self.performance_stats.copy()