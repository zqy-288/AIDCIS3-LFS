"""
统一统计分析服务
合并P2实时数据管理和P3统计引擎功能
提供跨页面的数据统计和分析能力
"""

import numpy as np
import pandas as pd
import threading
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


class UnifiedStatisticsService(QObject):
    """
    统一统计分析服务
    
    功能：
    1. 实时数据缓存和管理 (P2功能)
    2. 统计分析和计算 (P2+P3功能)
    3. 历史数据分析 (P3功能)
    4. 数据过滤和查询
    5. 数据持久化和导出
    6. 异常检测和质量评估
    """
    
    # 信号定义
    data_added = Signal(dict)  # 数据添加信号
    statistics_updated = Signal(dict)  # 统计更新信号
    analysis_started = Signal()  # 分析开始信号
    analysis_progress = Signal(int, str)  # 分析进度 (percentage, status)
    analysis_completed = Signal(dict)  # 分析完成信号
    analysis_failed = Signal(str)  # 分析失败信号
    buffer_full = Signal(int)  # 缓冲区满信号
    
    def __init__(self, max_size: int = 50000, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 实时数据存储 (P2功能)
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
        
        # 分析状态 (P3功能)
        self.is_analyzing = False
        self.current_analysis = None
        
        # 当前会话信息
        self.current_hole_id = None
        self.current_batch_id = None
        self.session_start_time = datetime.now()
        
        # 配置参数
        self.standard_diameter = 17.6
        self.tolerance = 0.2
        self.outlier_threshold = 3.0  # 标准差倍数
        self.confidence_level = 0.95
        
        # 性能监控
        self.performance_stats = {
            'total_points': 0,
            'add_operations': 0,
            'query_operations': 0,
            'export_operations': 0,
            'analysis_operations': 0,
            'last_add_time': None,
            'average_add_time': 0.0
        }
        
        # 定期统计更新
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics_cache)
        self.stats_timer.start(2000)  # 2秒更新一次统计
        
        self.logger.info("统计分析服务初始化完成")
        
    # ==================== 实时数据管理功能 (P2) ====================
    
    def add_data_point(self, depth: float, diameter: float, 
                      timestamp: Optional[datetime] = None,
                      hole_id: Optional[str] = None,
                      batch_id: Optional[str] = None) -> bool:
        """添加数据点"""
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
            self._update_performance_stats('add', add_time)
            
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
        """批量添加数据点"""
        if len(depths) != len(diameters):
            raise ValueError("深度和直径数据长度不匹配")
            
        if timestamps is None:
            timestamps = [datetime.now() + timedelta(seconds=i) for i in range(len(depths))]
        elif len(timestamps) != len(depths):
            raise ValueError("时间戳数据长度不匹配")
            
        success_count = 0
        for depth, diameter, timestamp in zip(depths, diameters, timestamps):
            if self.add_data_point(depth, diameter, timestamp, hole_id, batch_id):
                success_count += 1
                
        self.logger.debug(f"批量添加数据点: {success_count}/{len(depths)}")
        return success_count
        
    def get_realtime_statistics(self, force_update: bool = False) -> StatisticsInfo:
        """获取实时统计信息"""
        # 检查缓存
        current_time = datetime.now()
        if (not force_update and self._stats_cache is not None and
            self._stats_cache_time is not None and
            (current_time - self._stats_cache_time).total_seconds() < self.stats_cache_timeout and
            self._stats_cache_size == len(self.data_points)):
            return self._stats_cache
            
        # 计算统计信息
        if not self.data_points:
            return StatisticsInfo(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)
            
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
            anomaly_rate=anomaly_count / len(diameters) if diameters else 0.0
        )
        
        # 更新缓存
        self._stats_cache = stats
        self._stats_cache_time = current_time
        self._stats_cache_size = len(self.data_points)
        
        return stats
        
    # ==================== 历史数据分析功能 (P3) ====================
    
    def start_comprehensive_analysis(self, filters: Dict[str, Any] = None):
        """启动综合统计分析"""
        if self.is_analyzing:
            self.logger.warning("分析正在进行中...")
            return
            
        try:
            self.logger.info("启动综合统计分析...")
            self.is_analyzing = True
            self.analysis_started.emit()
            
            # 在后台线程执行分析
            analysis_thread = threading.Thread(
                target=self._execute_comprehensive_analysis,
                args=(filters or {},),
                daemon=True
            )
            analysis_thread.start()
            
        except Exception as e:
            self.logger.error(f"分析启动失败: {e}")
            self.analysis_failed.emit(str(e))
            self.is_analyzing = False
            
    def _execute_comprehensive_analysis(self, filters: Dict[str, Any]):
        """执行综合分析过程"""
        try:
            start_time = datetime.now()
            
            # 步骤1: 数据准备
            self.analysis_progress.emit(10, "准备数据...")
            df = self._prepare_analysis_data(filters)
            
            # 步骤2: 基础统计
            self.analysis_progress.emit(30, "计算基础统计...")
            basic_stats = self._calculate_comprehensive_statistics(df)
            
            # 步骤3: 质量分析
            self.analysis_progress.emit(50, "分析质量指标...")
            quality_stats = self._analyze_quality_metrics(df)
            
            # 步骤4: 趋势分析
            self.analysis_progress.emit(70, "分析趋势...")
            trend_stats = self._analyze_trends(df)
            
            # 步骤5: 异常检测
            self.analysis_progress.emit(85, "检测异常...")
            anomaly_stats = self._detect_comprehensive_anomalies(df)
            
            # 步骤6: 整合结果
            self.analysis_progress.emit(95, "整合结果...")
            results = self._compile_analysis_results(
                basic_stats, quality_stats, trend_stats, anomaly_stats
            )
            
            # 添加性能信息
            analysis_time = (datetime.now() - start_time).total_seconds()
            results['performance'] = {
                'analysis_time': analysis_time,
                'data_points_analyzed': len(df),
                'analysis_speed': len(df) / analysis_time if analysis_time > 0 else 0
            }
            
            # 完成
            self.analysis_progress.emit(100, "分析完成")
            self.analysis_completed.emit(results)
            
            self._update_performance_stats('analysis', analysis_time)
            
        except Exception as e:
            self.logger.error(f"分析执行失败: {e}")
            self.analysis_failed.emit(str(e))
        finally:
            self.is_analyzing = False
            
    def _prepare_analysis_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """准备分析数据"""
        # 从内存数据点创建DataFrame
        data_list = []
        for dp in self.data_points:
            data_list.append({
                'depth': dp.depth,
                'diameter': dp.diameter,
                'timestamp': dp.timestamp,
                'hole_id': dp.hole_id,
                'batch_id': dp.batch_id,
                'quality': dp.quality
            })
            
        df = pd.DataFrame(data_list)
        
        # 应用过滤器
        if filters:
            df = self._apply_filters(df, filters)
            
        # 数据清洗
        df = self._clean_analysis_data(df)
        
        return df
        
    def _clean_analysis_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        # 移除空值
        df = df.dropna(subset=['depth', 'diameter'])
        
        # 数据类型转换
        if 'depth' in df.columns:
            df['depth'] = pd.to_numeric(df['depth'], errors='coerce')
        if 'diameter' in df.columns:
            df['diameter'] = pd.to_numeric(df['diameter'], errors='coerce')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
        return df
        
    def _calculate_comprehensive_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算综合统计信息"""
        stats = {
            'total_count': len(df),
            'depth_stats': {},
            'diameter_stats': {},
            'time_stats': {},
            'quality_distribution': {}
        }
        
        # 深度统计
        if 'depth' in df.columns and not df['depth'].empty:
            depth_series = df['depth']
            stats['depth_stats'] = {
                'mean': float(depth_series.mean()),
                'median': float(depth_series.median()),
                'std': float(depth_series.std()),
                'min': float(depth_series.min()),
                'max': float(depth_series.max()),
                'q25': float(depth_series.quantile(0.25)),
                'q75': float(depth_series.quantile(0.75)),
                'range': float(depth_series.max() - depth_series.min())
            }
            
        # 直径统计
        if 'diameter' in df.columns and not df['diameter'].empty:
            diameter_series = df['diameter']
            stats['diameter_stats'] = {
                'mean': float(diameter_series.mean()),
                'median': float(diameter_series.median()),
                'std': float(diameter_series.std()),
                'min': float(diameter_series.min()),
                'max': float(diameter_series.max()),
                'q25': float(diameter_series.quantile(0.25)),
                'q75': float(diameter_series.quantile(0.75)),
                'range': float(diameter_series.max() - diameter_series.min()),
                'coefficient_of_variation': float(diameter_series.std() / diameter_series.mean()) if diameter_series.mean() != 0 else 0
            }
            
        # 时间统计
        if 'timestamp' in df.columns and not df['timestamp'].empty:
            time_series = df['timestamp']
            duration = (time_series.max() - time_series.min()).total_seconds()
            stats['time_stats'] = {
                'start_time': time_series.min().isoformat(),
                'end_time': time_series.max().isoformat(),
                'duration_seconds': duration,
                'duration_hours': duration / 3600,
                'data_rate': len(df) / duration if duration > 0 else 0
            }
            
        # 质量分布
        if 'quality' in df.columns:
            quality_counts = df['quality'].value_counts()
            total = len(df)
            stats['quality_distribution'] = {
                quality: {
                    'count': int(count),
                    'percentage': float(count / total * 100)
                } for quality, count in quality_counts.items()
            }
            
        return stats
        
    # ==================== 工具方法 ====================
    
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
            
    def _invalidate_stats_cache(self):
        """清除统计缓存"""
        self._stats_cache = None
        self._stats_cache_time = None
        self._stats_cache_size = 0
        
    def _update_statistics_cache(self):
        """更新统计缓存"""
        if self.data_points:
            self.get_realtime_statistics(force_update=True)
            stats_dict = asdict(self._stats_cache)
            self.statistics_updated.emit(stats_dict)
            
    def _update_performance_stats(self, operation: str, processing_time: float):
        """更新性能统计"""
        self.performance_stats['total_points'] = len(self.data_points)
        self.performance_stats[f'{operation}_operations'] += 1
        self.performance_stats[f'last_{operation}_time'] = processing_time
        
        if operation == 'add':
            old_avg = self.performance_stats['average_add_time']
            self.performance_stats['average_add_time'] = (old_avg * 0.8 + processing_time * 0.2)
            
    def _analyze_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析质量指标"""
        quality_metrics = {
            'total_measurements': len(df),
            'normal_count': 0,
            'anomaly_count': 0,
            'outlier_count': 0,
            'quality_score': 0.0
        }
        
        if 'quality' in df.columns:
            quality_counts = df['quality'].value_counts()
            quality_metrics['normal_count'] = quality_counts.get('normal', 0)
            quality_metrics['anomaly_count'] = quality_counts.get('anomaly', 0)
            quality_metrics['outlier_count'] = quality_counts.get('outlier', 0)
            
            total = len(df)
            quality_metrics['quality_score'] = quality_metrics['normal_count'] / total * 100 if total > 0 else 0
            
        return quality_metrics
        
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """趋势分析"""
        trends = {}
        
        if 'diameter' in df.columns and len(df) > 1:
            diameter_values = df['diameter'].values
            
            # 线性趋势
            x = np.arange(len(diameter_values))
            coeffs = np.polyfit(x, diameter_values, 1)
            trends['linear_trend'] = {
                'slope': float(coeffs[0]),
                'intercept': float(coeffs[1]),
                'trend_direction': 'increasing' if coeffs[0] > 0 else 'decreasing' if coeffs[0] < 0 else 'stable'
            }
            
        return trends
        
    def _detect_comprehensive_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """综合异常检测"""
        anomalies = {
            'total_anomalies': 0,
            'anomaly_types': {},
            'anomaly_rate': 0.0
        }
        
        if 'quality' in df.columns:
            anomaly_data = df[df['quality'].isin(['anomaly', 'outlier'])]
            anomalies['total_anomalies'] = len(anomaly_data)
            anomalies['anomaly_rate'] = len(anomaly_data) / len(df) * 100 if len(df) > 0 else 0
            
            anomaly_types = anomaly_data['quality'].value_counts()
            anomalies['anomaly_types'] = {
                atype: int(count) for atype, count in anomaly_types.items()
            }
            
        return anomalies
        
    def _compile_analysis_results(self, basic_stats, quality_stats, trend_stats, anomaly_stats) -> Dict[str, Any]:
        """整合分析结果"""
        return {
            'basic_statistics': basic_stats,
            'quality_metrics': quality_stats,
            'trend_analysis': trend_stats,
            'anomaly_detection': anomaly_stats,
            'analysis_timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_points': basic_stats.get('total_count', 0),
                'quality_score': quality_stats.get('quality_score', 0),
                'anomaly_rate': anomaly_stats.get('anomaly_rate', 0)
            }
        }
        
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """应用过滤器"""
        # 这里可以根据需要实现各种过滤逻辑
        return df
        
    # ==================== 公共接口 ====================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.performance_stats.copy()
        
    def export_statistics(self, file_path: str, format: str = 'json') -> bool:
        """导出统计结果"""
        try:
            stats = self.get_realtime_statistics()
            stats_dict = asdict(stats)
            
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats_dict, f, ensure_ascii=False, indent=2)
            elif format.lower() == 'csv':
                df = pd.DataFrame([stats_dict])
                df.to_csv(file_path, index=False)
            else:
                raise ValueError(f"不支持的格式: {format}")
                
            self._update_performance_stats('export', 0)
            return True
            
        except Exception as e:
            self.logger.error(f"导出统计失败: {e}")
            return False
            
    def clear_data(self):
        """清除所有数据"""
        self.data_points.clear()
        self.anomaly_points.clear()
        self.depth_index.clear()
        self.time_index.clear()
        self.hole_index.clear()
        self._invalidate_stats_cache()
        self.logger.info("数据已清除")
        
    def set_configuration(self, **kwargs):
        """设置配置参数"""
        if 'standard_diameter' in kwargs:
            self.standard_diameter = kwargs['standard_diameter']
        if 'tolerance' in kwargs:
            self.tolerance = kwargs['tolerance']
        if 'outlier_threshold' in kwargs:
            self.outlier_threshold = kwargs['outlier_threshold']
        if 'confidence_level' in kwargs:
            self.confidence_level = kwargs['confidence_level']
            
    def cleanup(self):
        """清理资源"""
        self.stats_timer.stop()
        self.clear_data()
        self.logger.info("统计服务清理完成")


# 单例模式访问
_statistics_service_instance = None

def get_statistics_service() -> UnifiedStatisticsService:
    """获取统计服务实例（单例）"""
    global _statistics_service_instance
    if _statistics_service_instance is None:
        _statistics_service_instance = UnifiedStatisticsService()
    return _statistics_service_instance