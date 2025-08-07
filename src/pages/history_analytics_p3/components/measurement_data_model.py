"""
测量数据模型组件 - 高内聚低耦合设计
职责：专门负责测量数据的结构定义、验证、格式化和业务逻辑处理
基于重构前代码完全恢复数据结构和验证逻辑
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging


@dataclass
class MeasurementPoint:
    """
    单个测量点数据模型
    高内聚：包含一个测量点的所有相关数据和验证逻辑
    """
    sequence: int = 0                          # 序号
    position: float = 0.0                      # 位置(mm) / 深度
    diameter: float = 0.0                      # 直径(mm)
    channel1: float = 0.0                      # 通道1值(μm)
    channel2: float = 0.0                      # 通道2值(μm)  
    channel3: float = 0.0                      # 通道3值(μm)
    is_qualified: bool = True                  # 合格性
    timestamp: Optional[datetime] = None       # 时间
    operator: str = "--"                       # 操作员
    notes: str = ""                           # 备注
    
    # 人工复查相关
    manual_review_value: Optional[float] = None  # 人工复查值
    reviewer: str = ""                           # 复查员
    
    def __post_init__(self):
        """后处理：数据验证和格式化"""
        # 确保数值类型正确
        self.sequence = int(self.sequence) if self.sequence is not None else 0
        self.position = float(self.position) if self.position is not None else 0.0
        self.diameter = float(self.diameter) if self.diameter is not None else 0.0
        self.channel1 = float(self.channel1) if self.channel1 is not None else 0.0
        self.channel2 = float(self.channel2) if self.channel2 is not None else 0.0
        self.channel3 = float(self.channel3) if self.channel3 is not None else 0.0
        
        # 处理时间戳
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def is_diameter_qualified(self, standard_diameter: float = 17.73, 
                            upper_tolerance: float = 0.070, 
                            lower_tolerance: float = 0.001) -> bool:
        """
        判断直径测量是否合格
        基于重构前代码：非对称公差 +0.070/-0.001
        """
        upper_limit = standard_diameter + upper_tolerance
        lower_limit = standard_diameter + lower_tolerance  # 注意：lower_tolerance是正值
        return lower_limit <= self.diameter <= upper_limit
    
    def get_formatted_time(self) -> str:
        """获取格式化的时间字符串"""
        if self.timestamp:
            return self.timestamp.strftime("%H:%M:%S")
        return "--"
        
    def get_qualified_symbol(self) -> str:
        """获取合格性符号"""
        return "✓" if self.is_qualified else "✗"
        
    def get_notes_display(self) -> str:
        """获取备注显示内容"""
        if self.manual_review_value is not None:
            return f"人工复查: {self.manual_review_value:.4f}mm (复查员: {self.reviewer})"
        return self.notes
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'sequence': self.sequence,
            'position': self.position,
            'diameter': self.diameter,
            'channel1': self.channel1,
            'channel2': self.channel2,
            'channel3': self.channel3,
            'is_qualified': self.is_qualified,
            'timestamp': self.timestamp,
            'operator': self.operator,
            'notes': self.notes,
            'manual_review_value': self.manual_review_value,
            'reviewer': self.reviewer
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeasurementPoint':
        """从字典创建测量点"""
        # 处理时间戳
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.strptime(timestamp, "%H:%M:%S")
            except ValueError:
                timestamp = datetime.now()
        elif timestamp is None:
            timestamp = datetime.now()
            
        return cls(
            sequence=data.get('sequence', 0),
            position=data.get('position', data.get('depth', 0.0)),
            diameter=data.get('diameter', 0.0),
            channel1=data.get('channel1', 0.0),
            channel2=data.get('channel2', 0.0),
            channel3=data.get('channel3', 0.0),
            is_qualified=data.get('is_qualified', True),
            timestamp=timestamp,
            operator=data.get('operator', '--'),
            notes=data.get('notes', ''),
            manual_review_value=data.get('manual_review_value'),
            reviewer=data.get('reviewer', '')
        )


class MeasurementDataset:
    """
    测量数据集管理器
    高内聚：专门负责测量数据集的管理、统计、验证等业务逻辑
    低耦合：通过明确的接口与外部组件交互
    """
    
    def __init__(self, hole_id: str = ""):
        self.hole_id = hole_id
        self.measurements: List[MeasurementPoint] = []
        self.logger = logging.getLogger(__name__)
        
        # 公差参数 - 基于重构前代码默认值
        self.standard_diameter = 17.73
        self.upper_tolerance = 0.070
        self.lower_tolerance = 0.001
        
    def set_tolerance_parameters(self, standard_diameter: float, 
                               upper_tolerance: float, lower_tolerance: float):
        """设置公差参数"""
        self.standard_diameter = standard_diameter
        self.upper_tolerance = upper_tolerance
        self.lower_tolerance = lower_tolerance
        
        # 重新验证所有测量点的合格性
        self._revalidate_all_measurements()
        
    def add_measurement(self, measurement: MeasurementPoint):
        """添加测量点"""
        # 验证合格性
        measurement.is_qualified = measurement.is_diameter_qualified(
            self.standard_diameter, self.upper_tolerance, self.lower_tolerance
        )
        
        self.measurements.append(measurement)
        self.logger.debug(f"添加测量点: 序号{measurement.sequence}, 直径{measurement.diameter:.4f}mm")
        
    def add_measurements(self, measurements: List[MeasurementPoint]):
        """批量添加测量点"""
        for measurement in measurements:
            self.add_measurement(measurement)
            
    def clear_measurements(self):
        """清空所有测量数据"""
        self.measurements.clear()
        self.logger.info("测量数据已清空")
        
    def get_measurement_count(self) -> int:
        """获取测量点数量"""
        return len(self.measurements)
        
    def get_qualified_count(self) -> int:
        """获取合格测量点数量"""
        return sum(1 for m in self.measurements if m.is_qualified)
        
    def get_unqualified_count(self) -> int:
        """获取不合格测量点数量"""
        return sum(1 for m in self.measurements if not m.is_qualified)
        
    def get_qualification_rate(self) -> float:
        """获取合格率（百分比）"""
        total = self.get_measurement_count()
        if total == 0:
            return 0.0
        return (self.get_qualified_count() / total) * 100.0
        
    def get_diameter_statistics(self) -> Dict[str, float]:
        """获取直径统计信息 - 基于重构前代码"""
        if not self.measurements:
            return {
                'count': 0,
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'range': 0.0
            }
            
        diameters = [m.diameter for m in self.measurements]
        
        import numpy as np
        
        return {
            'count': len(diameters),
            'mean': float(np.mean(diameters)),
            'std': float(np.std(diameters)),
            'min': float(np.min(diameters)),
            'max': float(np.max(diameters)),
            'range': float(np.max(diameters) - np.min(diameters))
        }
        
    def get_unqualified_measurements(self) -> List[tuple]:
        """获取不合格的测量点（返回索引和测量点的元组列表）"""
        unqualified = []
        for i, measurement in enumerate(self.measurements):
            if not measurement.is_qualified:
                unqualified.append((i, measurement))
        return unqualified
        
    def get_measurements_for_chart(self) -> List[Dict[str, float]]:
        """获取用于图表绘制的测量数据"""
        return [
            {
                'depth': m.position,
                'diameter': m.diameter
            }
            for m in self.measurements
        ]
        
    def get_table_data(self) -> List[List[str]]:
        """
        获取用于表格显示的数据
        返回格式：[序号, 位置, 直径, 通道1值, 通道2值, 通道3值, 合格, 时间, 操作员, 备注]
        """
        table_data = []
        for measurement in self.measurements:
            row = [
                str(measurement.sequence),                    # 序号
                f"{measurement.position:.1f}",               # 位置(mm)
                f"{measurement.diameter:.4f}",               # 直径(mm) - 4位小数
                f"{measurement.channel1:.2f}",               # 通道1值(μm) - 2位小数
                f"{measurement.channel2:.2f}",               # 通道2值(μm) - 2位小数
                f"{measurement.channel3:.2f}",               # 通道3值(μm) - 2位小数
                measurement.get_qualified_symbol(),          # 合格性符号
                measurement.get_formatted_time(),            # 时间
                measurement.operator,                        # 操作员
                measurement.get_notes_display()              # 备注
            ]
            table_data.append(row)
        return table_data
        
    def _revalidate_all_measurements(self):
        """重新验证所有测量点的合格性"""
        for measurement in self.measurements:
            measurement.is_qualified = measurement.is_diameter_qualified(
                self.standard_diameter, self.upper_tolerance, self.lower_tolerance
            )
        self.logger.info(f"重新验证了 {len(self.measurements)} 个测量点的合格性")
        
    def export_to_csv_data(self) -> List[List[str]]:
        """导出为CSV数据格式 - 基于重构前代码格式"""
        csv_data = []
        
        # 添加表头
        csv_data.append([
            '序号', '位置(mm)', '直径(mm)', '通道1值(μm)', '通道2值(μm)', 
            '通道3值(μm)', '合格', '时间', '操作员', '备注'
        ])
        
        # 添加数据行
        for measurement in self.measurements:
            row = [
                str(measurement.sequence),
                f"{measurement.position:.1f}",
                f"{measurement.diameter:.4f}",
                f"{measurement.channel1:.2f}",
                f"{measurement.channel2:.2f}",
                f"{measurement.channel3:.2f}",
                measurement.get_qualified_symbol(),
                measurement.get_formatted_time(),
                measurement.operator,
                measurement.get_notes_display()
            ]
            csv_data.append(row)
            
        return csv_data
        
    def get_summary_info(self) -> str:
        """获取数据汇总信息"""
        stats = self.get_diameter_statistics()
        qualified_count = self.get_qualified_count()
        total_count = self.get_measurement_count()
        qualification_rate = self.get_qualification_rate()
        
        summary = f"""数据汇总 - {self.hole_id}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测量统计:
  总测量点数: {total_count} 个
  合格点数: {qualified_count} 个
  不合格点数: {total_count - qualified_count} 个
  合格率: {qualification_rate:.1f}%

直径统计:
  平均直径: {stats['mean']:.4f} mm
  标准偏差: {stats['std']:.4f} mm
  最小直径: {stats['min']:.4f} mm
  最大直径: {stats['max']:.4f} mm
  测量范围: {stats['range']:.4f} mm

公差标准:
  标准直径: {self.standard_diameter:.3f} mm
  上公差: +{self.upper_tolerance:.3f} mm
  下公差: +{self.lower_tolerance:.3f} mm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        return summary


class MeasurementDataGenerator:
    """
    测量数据生成器 - 用于生成测试数据和模拟真实测量数据
    高内聚：专门负责各种类型的测量数据生成
    """
    
    @staticmethod
    def generate_sample_data(hole_id: str, count: int = 50) -> MeasurementDataset:
        """生成示例测量数据 - 基于重构前代码的真实数据特征"""
        import numpy as np
        import random
        
        dataset = MeasurementDataset(hole_id)
        
        # 基于重构前代码的实际参数
        standard_diameter = 17.73  # 标准直径
        
        for i in range(count):
            # 生成位置：从0到count*10的等间距分布
            position = i * 10.0
            
            # 生成直径：围绕标准直径的正态分布，添加一些趋势和噪声
            base_diameter = standard_diameter
            trend = 0.02 * np.sin(i / 8)  # 周期性趋势
            noise = 0.01 * np.random.randn()  # 随机噪声
            
            # 偶尔产生一些超出公差的值（约10%概率）
            if random.random() < 0.1:
                outlier = random.choice([-0.08, 0.08])  # 明显超出公差的值
                diameter = base_diameter + outlier
            else:
                diameter = base_diameter + trend + noise
                
            # 生成通道值：基于重构前代码的μm单位
            channel1 = 1200 + i * 5 + random.uniform(-50, 50)
            channel2 = 1300 + i * 4 + random.uniform(-40, 40)
            channel3 = 1400 + i * 3 + random.uniform(-30, 30)
            
            # 创建测量点
            measurement = MeasurementPoint(
                sequence=i + 1,
                position=position,
                diameter=diameter,
                channel1=channel1,
                channel2=channel2,
                channel3=channel3,
                timestamp=datetime.now(),
                operator="操作员A" if i % 2 == 0 else "操作员B",
                notes="" if i % 10 != 0 else f"第{i+1}次测量备注"
            )
            
            dataset.add_measurement(measurement)
            
        return dataset
        
    @staticmethod 
    def create_from_csv_data(hole_id: str, csv_data: List[List[str]]) -> MeasurementDataset:
        """从CSV数据创建测量数据集"""
        dataset = MeasurementDataset(hole_id)
        
        for i, row in enumerate(csv_data):
            if i == 0:  # 跳过表头
                continue
                
            try:
                # 解析CSV行数据
                measurement = MeasurementPoint(
                    sequence=int(row[0]) if len(row) > 0 else i,
                    position=float(row[1]) if len(row) > 1 else 0.0,
                    diameter=float(row[2]) if len(row) > 2 else 0.0,
                    channel1=float(row[3]) if len(row) > 3 else 0.0,
                    channel2=float(row[4]) if len(row) > 4 else 0.0,
                    channel3=float(row[5]) if len(row) > 5 else 0.0,
                    operator=row[8] if len(row) > 8 else '--',
                    notes=row[9] if len(row) > 9 else ''
                )
                
                dataset.add_measurement(measurement)
                
            except (ValueError, IndexError) as e:
                logging.warning(f"跳过无效的CSV行 {i}: {e}")
                continue
                
        return dataset