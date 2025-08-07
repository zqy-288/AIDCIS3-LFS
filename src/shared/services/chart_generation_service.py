"""
统一图表生成服务
提取自P4增强报告生成器的图表功能
为跨页面的图表生成提供统一服务
"""

import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# 确保线程安全的matplotlib后端
import matplotlib
if threading.current_thread() != threading.main_thread():
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from PySide6.QtCore import QObject, Signal


class ChartGenerationService(QObject):
    """
    统一图表生成服务
    
    功能：
    1. 包络图生成 (从P4提取)
    2. 统计图表生成 (折线图、柱状图、散点图)
    3. 质量分析图表
    4. 趋势分析图表
    5. 多维度对比图表
    6. 图表样式统一管理
    """
    
    # 信号定义
    chart_generated = Signal(str, str)  # chart_type, file_path
    generation_progress = Signal(int, str)  # percentage, status
    generation_error = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 临时文件目录
        self.temp_dir = Path(tempfile.gettempdir()) / "chart_generation"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 图表样式配置
        self.setup_matplotlib_style()
        
        # 统计信息
        self.generation_stats = {
            'total_charts_generated': 0,
            'envelope_charts': 0,
            'statistics_charts': 0,
            'trend_charts': 0,
            'comparison_charts': 0
        }
        
        self.logger.info("图表生成服务初始化完成")
        
    def setup_matplotlib_style(self):
        """设置matplotlib样式"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置默认样式
        plt.style.use('default')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['savefig.facecolor'] = 'white'
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['figure.dpi'] = 100
        
    def generate_envelope_chart(self, measurement_data: List[Dict], 
                              target_diameter: float,
                              upper_tolerance: float, 
                              lower_tolerance: float,
                              hole_id: str = "",
                              output_path: Optional[str] = None) -> str:
        """
        生成包络图
        
        Args:
            measurement_data: 测量数据 [{'depth': float, 'diameter': float}, ...]
            target_diameter: 目标直径
            upper_tolerance: 上公差
            lower_tolerance: 下公差
            hole_id: 孔位ID
            output_path: 输出路径，如果为None则自动生成
            
        Returns:
            生成的图表文件路径
        """
        try:
            self.generation_progress.emit(10, "准备数据...")
            
            if not measurement_data:
                # 生成模拟数据用于演示
                measurement_data = self._generate_demo_measurement_data(target_diameter)
                
            # 准备数据
            depths = [d.get('depth', i * 0.1) for i, d in enumerate(measurement_data)]
            diameters = [d.get('diameter', target_diameter + np.random.normal(0, 0.01)) 
                        for d in measurement_data]
            
            self.generation_progress.emit(30, "创建图形...")
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # 绘制测量数据
            ax.plot(depths, diameters, 'b-', linewidth=2.5, label='实测直径', alpha=0.8)
            ax.scatter(depths[::max(1, len(depths)//20)], diameters[::max(1, len(depths)//20)], 
                      color='blue', s=20, alpha=0.6, zorder=5)
            
            self.generation_progress.emit(50, "添加公差带...")
            
            # 计算公差带
            upper_limit = target_diameter + upper_tolerance
            lower_limit = target_diameter - lower_tolerance
            
            # 绘制公差带
            ax.axhline(y=upper_limit, color='red', linestyle='--', linewidth=2, 
                      label=f'上限 {upper_limit:.3f}mm (+{upper_tolerance:.3f})', alpha=0.8)
            ax.axhline(y=lower_limit, color='red', linestyle='--', linewidth=2, 
                      label=f'下限 {lower_limit:.3f}mm (-{lower_tolerance:.3f})', alpha=0.8)
            ax.axhline(y=target_diameter, color='green', linestyle='-', linewidth=2, 
                      label=f'目标直径 {target_diameter:.3f}mm', alpha=0.8)
            
            # 填充合格区域
            ax.fill_between(depths, upper_limit, lower_limit, alpha=0.15, color='green', 
                           label='合格区域')
            
            self.generation_progress.emit(70, "标记异常点...")
            
            # 标记超差点
            out_of_spec_count = 0
            for i, (depth, diameter) in enumerate(zip(depths, diameters)):
                if diameter > upper_limit or diameter < lower_limit:
                    out_of_spec_count += 1
                    ax.scatter(depth, diameter, color='red', s=80, zorder=10, 
                              marker='X', linewidths=2, edgecolors='darkred')
                    
                    # 添加标注（限制数量避免过密）
                    if out_of_spec_count <= 10:
                        deviation = max(diameter - upper_limit, lower_limit - diameter)
                        ax.annotate(f'{diameter:.3f}mm\\n(超差{deviation:.3f})', 
                                   (depth, diameter), 
                                   xytext=(10, 10), textcoords='offset points',
                                   bbox=dict(boxstyle='round,pad=0.5', 
                                           facecolor='red', alpha=0.8, edgecolor='darkred'),
                                   color='white', fontweight='bold', fontsize=9,
                                   arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
            
            self.generation_progress.emit(85, "添加统计信息...")
            
            # 添加统计信息文本框
            stats_text = self._generate_envelope_statistics_text(
                diameters, target_diameter, upper_tolerance, lower_tolerance
            )
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', horizontalalignment='left',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8),
                   fontsize=10, fontweight='bold')
            
            # 设置图形属性
            ax.set_xlabel('探头深度 (mm)', fontsize=14, fontweight='bold')
            ax.set_ylabel('孔径直径 (mm)', fontsize=14, fontweight='bold')
            
            title = f'孔径包络图 - 公差带分析'
            if hole_id:
                title += f' (孔位: {hole_id})'
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
            
            # 设置坐标轴范围
            y_margin = max(upper_tolerance, lower_tolerance) * 0.5
            ax.set_ylim(lower_limit - y_margin, upper_limit + y_margin)
            
            self.generation_progress.emit(95, "保存图表...")
            
            # 保存图表
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"envelope_chart_{hole_id}_{timestamp}.png"
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.generation_progress.emit(100, "完成")
            self.generation_stats['envelope_charts'] += 1
            self.generation_stats['total_charts_generated'] += 1
            
            self.chart_generated.emit("envelope", str(output_path))
            self.logger.info(f"包络图生成完成: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"包络图生成失败: {e}")
            self.generation_error.emit(f"包络图生成失败: {str(e)}")
            if 'fig' in locals():
                plt.close()
            return ""
            
    def generate_statistics_chart(self, data: Dict[str, Any], 
                                chart_type: str = "line",
                                title: str = "统计图表",
                                output_path: Optional[str] = None) -> str:
        """
        生成统计图表
        
        Args:
            data: 数据字典 {'x': [values], 'y': [values], 'labels': [labels]}
            chart_type: 图表类型 ("line", "bar", "scatter", "histogram")  
            title: 图表标题
            output_path: 输出路径
            
        Returns:
            图表文件路径
        """
        try:
            self.generation_progress.emit(20, f"生成{chart_type}图表...")
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            labels = data.get('labels', [])
            
            if chart_type == "line":
                ax.plot(x_data, y_data, 'b-', linewidth=2, marker='o', markersize=4)
                ax.set_xlabel('X轴')
                ax.set_ylabel('Y轴')
                
            elif chart_type == "bar":
                bars = ax.bar(range(len(y_data)), y_data, color='skyblue', alpha=0.8)
                if labels:
                    ax.set_xticks(range(len(labels)))
                    ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.set_ylabel('数值')
                
                # 在柱子上添加数值标签
                for bar, value in zip(bars, y_data):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(y_data)*0.01,
                           f'{value:.2f}', ha='center', va='bottom')
                
            elif chart_type == "scatter":
                ax.scatter(x_data, y_data, alpha=0.6, s=50)
                ax.set_xlabel('X轴')
                ax.set_ylabel('Y轴')
                
            elif chart_type == "histogram":
                ax.hist(y_data, bins=20, alpha=0.7, color='lightgreen', edgecolor='darkgreen')
                ax.set_xlabel('数值')
                ax.set_ylabel('频次')
                
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            
            # 保存图表
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"{chart_type}_chart_{timestamp}.png"
                
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.generation_stats['statistics_charts'] += 1
            self.generation_stats['total_charts_generated'] += 1
            
            self.chart_generated.emit(chart_type, str(output_path))
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"统计图表生成失败: {e}")
            self.generation_error.emit(f"统计图表生成失败: {str(e)}")
            if 'fig' in locals():
                plt.close()
            return ""
            
    def generate_trend_chart(self, time_series_data: List[Dict],
                           value_key: str = "value",
                           time_key: str = "timestamp",
                           title: str = "趋势分析图",
                           output_path: Optional[str] = None) -> str:
        """
        生成趋势分析图
        
        Args:
            time_series_data: 时间序列数据
            value_key: 数值字段名
            time_key: 时间字段名  
            title: 图表标题
            output_path: 输出路径
            
        Returns:
            图表文件路径
        """
        try:
            self.generation_progress.emit(30, "生成趋势图...")
            
            if not time_series_data:
                raise ValueError("时间序列数据为空")
                
            # 提取数据
            times = [item[time_key] for item in time_series_data]
            values = [item[value_key] for item in time_series_data]
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # 绘制趋势线
            ax.plot(times, values, 'b-', linewidth=2, alpha=0.7, label='实际值')
            ax.scatter(times[::max(1, len(times)//50)], values[::max(1, len(times)//50)], 
                      color='red', s=20, alpha=0.8, zorder=5)
            
            # 计算并绘制趋势线
            if len(values) > 1:
                x_numeric = np.arange(len(values))
                coeffs = np.polyfit(x_numeric, values, 1)
                trend_line = np.polyval(coeffs, x_numeric)
                ax.plot(times, trend_line, 'r--', linewidth=2, alpha=0.8, label='趋势线')
                
                # 添加趋势信息
                slope = coeffs[0]
                trend_info = f"趋势: {'上升' if slope > 0 else '下降' if slope < 0 else '平稳'}"
                ax.text(0.02, 0.98, trend_info, transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                       verticalalignment='top')
            
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('时间', fontsize=12)
            ax.set_ylabel('数值', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 保存图表
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"trend_chart_{timestamp}.png"
                
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.generation_stats['trend_charts'] += 1
            self.generation_stats['total_charts_generated'] += 1
            
            self.chart_generated.emit("trend", str(output_path))
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"趋势图生成失败: {e}")
            self.generation_error.emit(f"趋势图生成失败: {str(e)}")
            if 'fig' in locals():
                plt.close()
            return ""
            
    def generate_comparison_chart(self, datasets: List[Dict[str, Any]],
                                labels: List[str],
                                title: str = "对比分析图",
                                chart_type: str = "line",
                                output_path: Optional[str] = None) -> str:
        """
        生成对比分析图
        
        Args:
            datasets: 数据集列表，每个数据集包含x和y数据
            labels: 数据集标签
            title: 图表标题
            chart_type: 图表类型
            output_path: 输出路径
            
        Returns:
            图表文件路径
        """
        try:
            self.generation_progress.emit(40, "生成对比图...")
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
            
            for i, (dataset, label) in enumerate(zip(datasets, labels)):
                color = colors[i % len(colors)]
                x_data = dataset.get('x', range(len(dataset.get('y', []))))
                y_data = dataset.get('y', [])
                
                if chart_type == "line":
                    ax.plot(x_data, y_data, color=color, linewidth=2, 
                           label=label, marker='o', markersize=4, alpha=0.8)
                elif chart_type == "bar":
                    width = 0.8 / len(datasets)
                    offset = (i - len(datasets)/2) * width
                    ax.bar([x + offset for x in x_data], y_data, width, 
                          color=color, label=label, alpha=0.8)
                          
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 保存图表
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.temp_dir / f"comparison_chart_{timestamp}.png"
                
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.generation_stats['comparison_charts'] += 1
            self.generation_stats['total_charts_generated'] += 1
            
            self.chart_generated.emit("comparison", str(output_path))
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"对比图生成失败: {e}")
            self.generation_error.emit(f"对比图生成失败: {str(e)}")
            if 'fig' in locals():
                plt.close()
            return ""
            
    def _generate_demo_measurement_data(self, target_diameter: float = 17.6) -> List[Dict]:
        """生成演示用测量数据"""
        data = []
        np.random.seed(42)  # 确保可重现
        
        for i in range(900):  # 900个测量点
            depth = i * 1.0  # 每毫米一个点
            # 基础直径加上一些变化和噪声
            base_variation = 0.05 * np.sin(depth * 0.01) + 0.02 * np.sin(depth * 0.05)
            noise = np.random.normal(0, 0.01)
            diameter = target_diameter + base_variation + noise
            
            # 在某些深度添加异常值
            if 200 <= depth <= 220 or 500 <= depth <= 510:
                diameter += np.random.choice([-0.15, 0.15])
                
            data.append({
                'depth': depth,
                'diameter': diameter
            })
            
        return data
        
    def _generate_envelope_statistics_text(self, diameters: List[float], 
                                         target_diameter: float,
                                         upper_tolerance: float, 
                                         lower_tolerance: float) -> str:
        """生成包络图统计文本"""
        mean_dia = np.mean(diameters)
        std_dia = np.std(diameters)
        min_dia = np.min(diameters)
        max_dia = np.max(diameters)
        
        upper_limit = target_diameter + upper_tolerance
        lower_limit = target_diameter - lower_tolerance
        
        out_of_spec = sum(1 for d in diameters if d > upper_limit or d < lower_limit)
        conformity_rate = (len(diameters) - out_of_spec) / len(diameters) * 100
        
        stats_text = f"""统计信息:
测量点数: {len(diameters)}
平均直径: {mean_dia:.3f}mm
标准偏差: {std_dia:.4f}mm
最小值: {min_dia:.3f}mm
最大值: {max_dia:.3f}mm
合格率: {conformity_rate:.1f}%
超差点数: {out_of_spec}"""

        return stats_text
        
    def get_generation_stats(self) -> Dict[str, int]:
        """获取生成统计信息"""
        return self.generation_stats.copy()
        
    def clear_temp_files(self):
        """清理临时文件"""
        try:
            for file_path in self.temp_dir.glob("*.png"):
                if file_path.is_file():
                    file_path.unlink()
            self.logger.info("临时文件清理完成")
        except Exception as e:
            self.logger.error(f"清理临时文件失败: {e}")
            
    def cleanup(self):
        """清理资源"""
        self.clear_temp_files()
        self.logger.info("图表生成服务清理完成")


# 单例模式访问
_chart_service_instance = None

def get_chart_generation_service() -> ChartGenerationService:
    """获取图表生成服务实例（单例）"""
    global _chart_service_instance
    if _chart_service_instance is None:
        _chart_service_instance = ChartGenerationService()
    return _chart_service_instance