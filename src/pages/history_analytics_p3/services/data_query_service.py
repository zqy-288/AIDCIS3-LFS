"""
数据查询服务组件 - 高内聚低耦合设计
职责：专门负责从CAP1000数据目录查询和加载CSV测量数据
基于重构前代码完全恢复数据查询功能
"""

import os
import csv
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime


class DataQueryService:
    """
    数据查询服务 - 高内聚设计
    职责：
    1. 查找并加载孔位的CSV测量数据
    2. 解析CSV文件内容
    3. 提供数据格式转换
    4. 管理数据目录路径
    """
    
    def __init__(self, data_root_path: str = None):
        """
        初始化数据查询服务
        data_root_path: 数据根目录路径，默认为项目Data/CAP1000目录
        """
        self.logger = logging.getLogger(__name__)
        
        # 设置数据根目录 - 修复为正确的CAP1000路径
        if data_root_path:
            self.data_root_path = Path(data_root_path)
        else:
            # 自动检测数据目录
            self.data_root_path = self._detect_data_root()
            
        self.logger.info(f"数据查询服务初始化，数据根目录: {self.data_root_path}")
        
    def _detect_data_root(self) -> Path:
        """自动检测数据根目录 - 重点查找D:\AIDCIS3-LFS-master\Data\CAP1000"""
        # 尝试多个可能的路径，优先使用D盘路径
        possible_paths = [
            Path("D:\\AIDCIS3-LFS-master\\Data\\CAP1000"),    # Windows D盘路径（主要）
            Path("/mnt/d/AIDCIS3-LFS-master/Data/CAP1000"),  # WSL访问D盘路径
            Path("D:/AIDCIS3-LFS-master/Data/CAP1000"),      # Windows正斜杠路径
            Path("./Data/CAP1000"),                          # 相对路径
            Path("../../../Data/CAP1000"),                   # 从src目录的相对路径
        ]
        
        for path in possible_paths:
            if path.exists():
                self.logger.info(f"检测到CAP1000数据目录: {path}")
                return path
                
        # 如果都不存在，使用D盘默认路径
        default_path = Path("D:\\AIDCIS3-LFS-master\\Data\\CAP1000")
        self.logger.warning(f"未找到CAP1000数据目录，使用默认D盘路径: {default_path}")
        return default_path
    
    def query_hole_data(self, hole_id: str) -> List[Dict]:
        """
        查询指定孔位的测量数据 - 使用传统CSV读取器确保完整性
        hole_id: 孔位ID，格式如 R001C001
        返回: 测量数据列表
        """
        self.logger.info(f"开始查询孔位数据: {hole_id}")
        
        # 验证孔位ID格式
        if not self._validate_hole_id(hole_id):
            self.logger.error(f"无效的孔位ID格式: {hole_id}")
            return []
        
        try:
            # 使用传统CSV读取器，确保完整读取
            from .legacy_csv_reader import LegacyCSVReader
            reader = LegacyCSVReader(str(self.data_root_path))
            measurements = reader.load_csv_data_for_hole(hole_id)
            
            self.logger.info(f"孔位 {hole_id} 查询完成，共 {len(measurements)} 条数据")
            return measurements
            
        except Exception as e:
            self.logger.error(f"查询孔位数据时发生异常: {e}")
            return []
    
    def _validate_hole_id(self, hole_id: str) -> bool:
        """验证孔位ID格式"""
        if not hole_id:
            return False
        return hole_id.startswith('R') and 'C' in hole_id
    
    def _find_csv_file(self, hole_id: str) -> Optional[Path]:
        """
        查找孔位对应的CSV文件
        基于重构前的路径查找逻辑
        """
        # 可能的CSV文件路径
        search_paths = [
            self.data_root_path / hole_id / "CCIDM",
            self.data_root_path / hole_id,
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            # 查找CSV文件
            csv_files = list(search_path.glob("*.csv"))
            if csv_files:
                # 按修改时间排序，选择最新的文件
                csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                selected_file = csv_files[0]
                self.logger.info(f"找到CSV文件: {selected_file}")
                return selected_file
                
        return None
    
    def _read_csv_file(self, file_path: Path) -> List[Dict]:
        """
        读取CSV文件并解析数据 - 完全基于重构前的read_csv_file方法
        """
        measurements = []

        try:
            # 尝试不同的编码 - 与重构前完全一致
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        self.logger.info(f"成功使用编码 {encoding} 读取文件")
                        self.logger.info(f"CSV文件列头: {headers}")

                        # 查找列索引 - 根据实际CSV文件结构调整
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径

                        # 验证列数是否足够
                        if len(headers) < 5:
                            self.logger.warning(f"CSV文件列数不足: {len(headers)} < 5")
                            continue

                        # 读取数据行 - 在同一个with块中 - 完全按重构前逻辑
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])

                                    # 判断是否合格（标准直径17.73mm，非对称公差+0.07/-0.05mm）
                                    standard_diameter = 17.73
                                    upper_tolerance = 0.07
                                    lower_tolerance = 0.05
                                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)

                                    # 模拟时间（基于文件修改时间）
                                    import os
                                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                    # 为每个数据点添加秒数偏移，正确处理分钟进位
                                    total_seconds = file_time.second + (row_num - 2)
                                    additional_minutes = total_seconds // 60
                                    new_seconds = total_seconds % 60

                                    # 计算新的分钟数，也要处理小时进位
                                    total_minutes = file_time.minute + additional_minutes
                                    additional_hours = total_minutes // 60
                                    new_minutes = total_minutes % 60

                                    # 计算新的小时数
                                    new_hours = (file_time.hour + additional_hours) % 24

                                    data_time = file_time.replace(hour=new_hours, minute=new_minutes, second=new_seconds)

                                    # 按重构前完全一致的数据结构
                                    measurements.append({
                                        'position': position,
                                        'diameter': diameter,
                                        'channel1': channel1,
                                        'channel2': channel2,
                                        'channel3': channel3,
                                        'is_qualified': is_qualified,
                                        'timestamp': data_time,
                                        'operator': '',  # 暂不显示
                                        'sequence': row_num - 1,  # 序号
                                        'depth': position,        # 深度与位置相同
                                        'notes': ''               # 备注
                                    })

                            except (ValueError, IndexError) as e:
                                self.logger.warning(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环 - 重构前逻辑
                        break

                except UnicodeDecodeError:
                    continue
            else:
                self.logger.error(f"无法使用任何编码读取文件: {file_path}")
                return []

        except Exception as e:
            self.logger.error(f"读取CSV文件时出错: {e}")
            return []

        self.logger.info(f"成功读取 {len(measurements)} 条测量数据")
        return measurements
    
    def get_available_holes(self) -> List[str]:
        """获取所有可用的孔位ID列表"""
        available_holes = []
        
        try:
            if not self.data_root_path.exists():
                self.logger.warning(f"数据根目录不存在: {self.data_root_path}")
                return []
                
            # 遍历数据目录
            for hole_dir in self.data_root_path.iterdir():
                if hole_dir.is_dir() and self._validate_hole_id(hole_dir.name):
                    # 检查是否有CCIDM目录或CSV文件
                    ccidm_dir = hole_dir / "CCIDM"
                    has_csv = False
                    
                    if ccidm_dir.exists():
                        has_csv = bool(list(ccidm_dir.glob("*.csv")))
                    else:
                        has_csv = bool(list(hole_dir.glob("*.csv")))
                        
                    if has_csv:
                        available_holes.append(hole_dir.name)
                        
            available_holes.sort()
            self.logger.info(f"找到 {len(available_holes)} 个可用孔位")
            
        except Exception as e:
            self.logger.error(f"获取可用孔位时发生异常: {e}")
            
        return available_holes
    
    def get_data_statistics(self, hole_id: str) -> Dict:
        """
        导出孔位数据到CSV文件
        hole_id: 孔位ID
        export_path: 导出文件路径
        include_statistics: 是否包含统计信息
        """
        try:
            measurements = self.query_hole_data(hole_id)
            if not measurements:
                self.logger.error(f"孔位 {hole_id} 没有数据可导出")
                return False
                
            # 计算统计信息 - 使用重构前的逻辑
            diameters = [m['diameter'] for m in measurements]
            standard_diameter = 17.73
            upper_tolerance = 0.07
            lower_tolerance = 0.05
            
            qualified_count = sum(1 for d in diameters
                                if standard_diameter - lower_tolerance <= d <= standard_diameter + upper_tolerance)
            total_count = len(diameters)
            qualification_rate = qualified_count / total_count * 100 if total_count > 0 else 0
            
            max_diameter = max(diameters) if diameters else 0
            min_diameter = min(diameters) if diameters else 0
            avg_diameter = sum(diameters) / len(diameters) if diameters else 0

            with open(export_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入统计信息头部 - 完全按照重构前格式
                writer.writerow(['测量数据统计信息'])
                writer.writerow(['工件ID', 'CAP1000'])
                writer.writerow(['孔位ID', hole_id])
                writer.writerow(['标准直径(mm)', standard_diameter])
                writer.writerow(['公差范围(mm)', f'-{lower_tolerance}~+{upper_tolerance}'])
                writer.writerow(['最大直径(mm)', f'{max_diameter:.4f}'])
                writer.writerow(['最小直径(mm)', f'{min_diameter:.4f}'])
                writer.writerow(['平均直径(mm)', f'{avg_diameter:.4f}'])
                writer.writerow(['合格率', f'{qualified_count}/{total_count} ({qualification_rate:.1f}%)'])
                writer.writerow([])  # 空行分隔
                
                # 写入测量数据表头 - 完全按照重构前格式
                writer.writerow(['位置(mm)', '直径(mm)', '通道1值(μm)', '通道2值(μm)', '通道3值(μm)', '合格', '时间', '操作员', '备注'])
                
                # 写入测量数据 - 完全按照重构前格式
                for measurement in measurements:
                    diameter = measurement['diameter']
                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)
                    qualified_text = '✓' if is_qualified else '✗'  # 使用与重构前相同的符号
                    
                    # 检查是否有人工复查值 - 完全按照重构前格式
                    notes = ""
                    if 'manual_review_value' in measurement:
                        notes = f"人工复查值: {measurement['manual_review_value']:.4f}mm"
                        if 'reviewer' in measurement:
                            notes += f", 复查员: {measurement['reviewer']}"
                        if 'review_time' in measurement:
                            notes += f", 复查时间: {measurement['review_time']}"
                    
                    # 获取位置信息（兼容两种键名）
                    position = measurement.get('position', measurement.get('depth', 0))
                    
                    # 时间格式化
                    timestamp = measurement.get('timestamp', '')
                    if timestamp:
                        time_str = timestamp.strftime("%H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp)
                    else:
                        time_str = ""
                    
                    # 操作员信息
                    operator = measurement.get('operator', '')
                    
                    writer.writerow([
                        f"{position:.1f}",           # 位置(mm) - 1位小数
                        f"{diameter:.4f}",           # 直径(mm) - 4位小数
                        f"{measurement.get('channel1', 0):.2f}",  # 通道1值(μm) - 2位小数
                        f"{measurement.get('channel2', 0):.2f}",  # 通道2值(μm) - 2位小数
                        f"{measurement.get('channel3', 0):.2f}",  # 通道3值(μm) - 2位小数
                        qualified_text,              # 合格 - ✓ 或 ✗
                        time_str,                    # 时间 - HH:MM:SS
                        operator,                    # 操作员
                        notes                        # 备注
                    ])
                    
            self.logger.info(f"数据导出成功: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据时发生异常: {e}")
            return False
    
    def get_data_statistics(self, hole_id: str) -> Dict:
        """获取孔位数据统计信息"""
        measurements = self.query_hole_data(hole_id)
        if not measurements:
            return {}
            
        diameters = [m['diameter'] for m in measurements]
        
        import numpy as np
        
        stats = {
            'total_count': len(measurements),
            'min_diameter': min(diameters),
            'max_diameter': max(diameters),
            'mean_diameter': np.mean(diameters),
            'std_diameter': np.std(diameters),
            'qualified_count': sum(1 for m in measurements if m.get('is_qualified', True)),
        }
        
        stats['qualified_rate'] = (stats['qualified_count'] / stats['total_count']) * 100
        
        return stats