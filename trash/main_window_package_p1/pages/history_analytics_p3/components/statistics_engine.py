"""
统计分析引擎
负责执行各种统计计算和数据分析
"""

import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Signal, QTimer
import numpy as np
import pandas as pd


class StatisticsEngine(QObject):
    """
    统计分析引擎
    
    功能:
    1. 描述性统计分析
    2. 时间序列分析
    3. 质量趋势分析
    4. 异常检测统计
    5. 多维度对比分析
    """
    
    # 信号定义
    analysis_started = Signal()
    analysis_progress = Signal(int, str)  # 进度, 状态描述
    analysis_completed = Signal(dict)     # 分析结果
    analysis_failed = Signal(str)        # 错误信息
    
    def __init__(self, data_model=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.data_model = data_model
        
        # 分析状态
        self.is_analyzing = False
        self.current_analysis = None
        
        # 统计配置
        self.confidence_level = 0.95
        self.outlier_threshold = 3.0  # 标准差倍数
        
    def start_analysis(self, filters: Dict[str, Any]):
        """启动统计分析"""
        if self.is_analyzing:
            self.logger.warning("⚠️ 分析正在进行中...")
            return
            
        try:
            self.logger.info("🔬 启动统计分析...")
            self.is_analyzing = True
            self.analysis_started.emit()
            
            # 在后台线程执行分析
            analysis_thread = threading.Thread(
                target=self._execute_analysis,
                args=(filters,),
                daemon=True
            )
            analysis_thread.start()
            
        except Exception as e:
            self.logger.error(f"❌ 分析启动失败: {e}")
            self.analysis_failed.emit(str(e))
            self.is_analyzing = False
            
    def _execute_analysis(self, filters: Dict[str, Any]):
        """执行分析过程"""
        try:
            # 步骤1: 数据准备
            self.analysis_progress.emit(10, "准备数据...")
            raw_data = self._prepare_data(filters)
            
            # 步骤2: 基础统计
            self.analysis_progress.emit(30, "计算基础统计...")
            basic_stats = self._calculate_basic_statistics(raw_data)
            
            # 步骤3: 质量分析
            self.analysis_progress.emit(50, "分析质量指标...")
            quality_stats = self._analyze_quality_metrics(raw_data)
            
            # 步骤4: 趋势分析
            self.analysis_progress.emit(70, "分析趋势...")
            trend_stats = self._analyze_trends(raw_data)
            
            # 步骤5: 异常检测
            self.analysis_progress.emit(85, "检测异常...")
            anomaly_stats = self._detect_anomalies(raw_data)
            
            # 步骤6: 整合结果
            self.analysis_progress.emit(95, "整合结果...")
            results = self._compile_results(
                basic_stats, quality_stats, trend_stats, anomaly_stats
            )
            
            # 完成
            self.analysis_progress.emit(100, "分析完成")
            self.analysis_completed.emit(results)
            
        except Exception as e:
            self.logger.error(f"❌ 分析执行失败: {e}")
            self.analysis_failed.emit(str(e))
        finally:
            self.is_analyzing = False
            
    def _prepare_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """准备分析数据"""
        if not self.data_model:
            return pd.DataFrame()
            
        # 从数据模型获取数据
        raw_data = self.data_model.get_filtered_data(filters)
        
        # 转换为DataFrame
        if isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict):
            df = pd.DataFrame([raw_data])
        else:
            df = raw_data
            
        # 数据清洗
        df = self._clean_data(df)
        
        return df
        
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
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
            
        # 移除异常值
        df = self._remove_outliers(df)
        
        return df
        
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除异常值"""
        for column in ['depth', 'diameter']:
            if column in df.columns:
                mean = df[column].mean()
                std = df[column].std()
                threshold = self.outlier_threshold * std
                
                # 保留在合理范围内的数据
                df = df[abs(df[column] - mean) <= threshold]
                
        return df
        
    def _calculate_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算基础统计信息"""
        stats = {
            'total_count': len(df),
            'depth_stats': {},
            'diameter_stats': {},
            'time_stats': {}
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
                'q75': float(depth_series.quantile(0.75))
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
                'q75': float(diameter_series.quantile(0.75))
            }
            
        # 时间统计
        if 'timestamp' in df.columns and not df['timestamp'].empty:
            time_series = df['timestamp']
            stats['time_stats'] = {
                'start_time': time_series.min().isoformat(),
                'end_time': time_series.max().isoformat(),
                'duration_days': (time_series.max() - time_series.min()).days
            }
            
        return stats
        
    def _analyze_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析质量指标"""
        quality_stats = {
            'qualified_count': 0,
            'defective_count': 0,
            'qualified_rate': 0.0,
            'defect_rate': 0.0,
            'quality_distribution': {}
        }
        
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            
            qualified_count = status_counts.get('qualified', 0)
            defective_count = status_counts.get('defective', 0)
            total_count = len(df)
            
            quality_stats.update({
                'qualified_count': int(qualified_count),
                'defective_count': int(defective_count),
                'qualified_rate': float(qualified_count / total_count * 100) if total_count > 0 else 0.0,
                'defect_rate': float(defective_count / total_count * 100) if total_count > 0 else 0.0,
                'quality_distribution': status_counts.to_dict()
            })
            
        return quality_stats
        
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析趋势"""
        trend_stats = {
            'depth_trend': None,
            'diameter_trend': None,
            'quality_trend': None,
            'time_series': []
        }
        
        if 'timestamp' in df.columns and len(df) > 1:
            # 按时间排序
            df_sorted = df.sort_values('timestamp')
            
            # 深度趋势
            if 'depth' in df_sorted.columns:
                depth_trend = self._calculate_trend(df_sorted['depth'].values)
                trend_stats['depth_trend'] = depth_trend
                
            # 直径趋势
            if 'diameter' in df_sorted.columns:
                diameter_trend = self._calculate_trend(df_sorted['diameter'].values)
                trend_stats['diameter_trend'] = diameter_trend
                
            # 时间序列数据
            trend_stats['time_series'] = self._generate_time_series(df_sorted)
            
        return trend_stats
        
    def _calculate_trend(self, values: np.ndarray) -> Dict[str, float]:
        """计算趋势"""
        if len(values) < 2:
            return {'slope': 0.0, 'correlation': 0.0}
            
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        correlation = np.corrcoef(x, values)[0, 1]
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'correlation': float(correlation)
        }
        
    def _generate_time_series(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """生成时间序列数据"""
        time_series = []
        
        # 按天分组
        if 'timestamp' in df.columns:
            df['date'] = df['timestamp'].dt.date
            daily_stats = df.groupby('date').agg({
                'depth': ['mean', 'count'],
                'diameter': ['mean', 'count']
            }).reset_index()
            
            for _, row in daily_stats.iterrows():
                time_series.append({
                    'date': row['date'].isoformat(),
                    'avg_depth': float(row[('depth', 'mean')]),
                    'avg_diameter': float(row[('diameter', 'mean')]),
                    'count': int(row[('depth', 'count')])
                })
                
        return time_series
        
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检测异常"""
        anomaly_stats = {
            'anomaly_count': 0,
            'anomaly_rate': 0.0,
            'anomalies': []
        }
        
        # 基于统计的异常检测
        for column in ['depth', 'diameter']:
            if column in df.columns:
                series = df[column]
                mean = series.mean()
                std = series.std()
                
                # 异常定义：超过3个标准差
                anomalies = df[abs(series - mean) > 3 * std]
                
                for _, anomaly in anomalies.iterrows():
                    anomaly_stats['anomalies'].append({
                        'type': f'{column}_anomaly',
                        'value': float(anomaly[column]),
                        'expected_range': [float(mean - 3*std), float(mean + 3*std)],
                        'timestamp': anomaly.get('timestamp', '').isoformat() if 'timestamp' in anomaly else None
                    })
                    
        anomaly_stats['anomaly_count'] = len(anomaly_stats['anomalies'])
        anomaly_stats['anomaly_rate'] = float(anomaly_stats['anomaly_count'] / len(df) * 100) if len(df) > 0 else 0.0
        
        return anomaly_stats
        
    def _compile_results(self, basic_stats, quality_stats, trend_stats, anomaly_stats) -> Dict[str, Any]:
        """整合分析结果"""
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'basic_statistics': basic_stats,
            'quality_metrics': quality_stats,
            'trend_analysis': trend_stats,
            'anomaly_detection': anomaly_stats,
            
            # 为UI准备的汇总数据
            'key_metrics': {
                'total_holes': basic_stats.get('total_count', 0),
                'qualified_rate': quality_stats.get('qualified_rate', 0.0),
                'defect_rate': quality_stats.get('defect_rate', 0.0),
                'avg_depth': basic_stats.get('depth_stats', {}).get('mean', 0.0),
                'avg_diameter': basic_stats.get('diameter_stats', {}).get('mean', 0.0)
            },
            
            'trend_data': trend_stats.get('time_series', []),
            'quality_data': quality_stats.get('quality_distribution', {}),
            'table_data': self._prepare_table_data(basic_stats, quality_stats)
        }
        
    def _prepare_table_data(self, basic_stats, quality_stats) -> List[Dict[str, Any]]:
        """准备表格数据"""
        table_data = []
        
        # 基础统计行
        depth_stats = basic_stats.get('depth_stats', {})
        diameter_stats = basic_stats.get('diameter_stats', {})
        
        table_data.extend([
            {'指标': '深度均值', '数值': f"{depth_stats.get('mean', 0):.2f} mm"},
            {'指标': '深度标准差', '数值': f"{depth_stats.get('std', 0):.2f} mm"},
            {'指标': '直径均值', '数值': f"{diameter_stats.get('mean', 0):.2f} mm"},
            {'指标': '直径标准差', '数值': f"{diameter_stats.get('std', 0):.2f} mm"},
            {'指标': '合格率', '数值': f"{quality_stats.get('qualified_rate', 0):.1f}%"},
            {'指标': '缺陷率', '数值': f"{quality_stats.get('defect_rate', 0):.1f}%"}
        ])
        
        return table_data