"""
真实CSV数据读取器 - 从重构前代码直接迁移
专门负责从实际的CSV文件中读取测量数据
路径: D:\AIDCIS3-LFS-master\Data\CAP1000\{hole_id}\CCIDM\{hole_id}.csv
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging


class RealCSVReader:
    """
    真实CSV数据读取器 - 高内聚设计
    职责：专门负责CSV文件的读取和数据解析
    直接从重构前的 load_csv_data_for_hole 和 read_csv_file 方法迁移而来
    """
    
    def __init__(self, data_root_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # 设置数据根路径 - 修复为实际路径
        if data_root_path:
            self.data_root_path = Path(data_root_path)
        else:
            # 首先尝试当前工作目录的Data路径
            current_dir = Path.cwd()
            data_path = current_dir / "Data" / "CAP1000"
            
            if data_path.exists():
                self.data_root_path = data_path
            else:
                # 尝试项目根目录（从当前文件位置推算）
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent.parent  # 到项目根目录
                self.data_root_path = project_root / "Data" / "CAP1000"
            
        self.logger.info(f"CSV数据根路径: {self.data_root_path}")
        
    def load_csv_data_for_hole(self, hole_id: str) -> List[Dict]:
        """根据孔ID加载对应的CSV数据 - 直接从重构前代码迁移"""
        # 构建可能的CSV文件路径 - 直接从重构前迁移
        csv_paths = [
            self.data_root_path / hole_id / "CCIDM",
            self.data_root_path / hole_id,
            Path("D:/AIDCIS3-LFS-master/Data/CAP1000") / hole_id / "CCIDM",  # Windows绝对路径
            Path("D:/AIDCIS3-LFS-master/Data/CAP1000") / hole_id,
        ]
        
        # 添加备用路径
        if self.data_root_path != Path("D:/AIDCIS3-LFS-master/Data/CAP1000"):
            csv_paths.extend([
                Path("D:/AIDCIS3-LFS-master/Data/CAP1000") / hole_id / "CCIDM",
                Path("D:/AIDCIS3-LFS-master/Data/CAP1000") / hole_id,
            ])
        
        csv_files = []
        
        # 查找存在的CSV目录 - 直接从重构前迁移
        for path in csv_paths:
            if path.exists() and path.is_dir():
                self.logger.info(f"找到目录: {path}")
                # 查找CSV文件
                for csv_file in path.glob("*.csv"):
                    csv_files.append(csv_file)
                    self.logger.info(f"找到CSV文件: {csv_file}")
                if csv_files:
                    break
            else:
                self.logger.debug(f"路径不存在: {path}")
        
        if not csv_files:
            # 格式化路径显示 - 直接从重构前迁移
            formatted_paths = [str(path) for path in csv_paths]
            self.logger.warning(f"CSV数据目录不存在或无CSV文件，已检查路径: {formatted_paths}")
            return []
        
        # 按时间排序 - 直接从重构前迁移
        csv_files.sort()
        
        # 选择第一个CSV文件（通常每个孔位只有一个CSV文件）
        selected_file = csv_files[0]
        self.logger.info(f"为孔ID {hole_id} 选择文件: {selected_file}")
        
        # 读取CSV文件数据
        return self.read_csv_file(selected_file)
        
    def read_csv_file(self, file_path: Path) -> List[Dict]:
        """读取CSV文件并返回测量数据 - 直接从重构前代码迁移"""
        measurements = []
        
        try:
            # 尝试不同的编码 - 直接从重构前迁移
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        
                        # 读取表头
                        headers = next(reader, [])
                        self.logger.info(f"CSV文件列头: {headers}")
                        
                        # 查找列索引 - 根据实际CSV文件结构调整，直接从重构前迁移
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径
                        
                        # 验证列数是否足够
                        if len(headers) < 5:
                            self.logger.warning(f"CSV文件列数不足: {len(headers)} < 5")
                            continue
                        
                        # 读取数据行 - 直接从重构前迁移
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])
                                    
                                    # 公差判断 - 直接从重构前迁移
                                    standard_diameter = 17.73
                                    upper_tolerance = 0.07
                                    lower_tolerance = 0.05
                                    
                                    is_qualified = (standard_diameter - lower_tolerance) <= diameter <= (standard_diameter + upper_tolerance)
                                    
                                    # 构造测量数据 - 直接从重构前迁移
                                    measurement = {
                                        'sequence': row_num - 1,  # 序号从1开始
                                        'position': position,
                                        'depth': position,
                                        'diameter': diameter,
                                        'channel1': channel1,
                                        'channel2': channel2,
                                        'channel3': channel3,
                                        'is_qualified': is_qualified,
                                        'timestamp': '',  # CSV中通常没有时间戳
                                        'operator': '',
                                        'notes': ''
                                    }
                                    measurements.append(measurement)
                                    
                            except (ValueError, IndexError) as e:
                                self.logger.warning(f"跳过第{row_num}行数据，解析错误: {e}")
                                continue
                                
                        # 如果成功读取到数据，跳出编码循环
                        if measurements:
                            self.logger.info(f"使用编码 {encoding} 成功读取数据")
                            break
                            
                except UnicodeDecodeError:
                    self.logger.debug(f"编码 {encoding} 解码失败，尝试下一个编码")
                    continue
                except Exception as e:
                    self.logger.error(f"使用编码 {encoding} 读取文件时出错: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"读取CSV文件时出错: {e}")
            return []
        
        self.logger.info(f"成功读取 {len(measurements)} 条测量数据")
        return measurements
        
    def get_available_holes(self, workpiece_id: str = "CAP1000") -> List[str]:
        """获取可用的孔位列表 - 从重构前迁移"""
        available_holes = []
        
        try:
            workpiece_path = self.data_root_path
            if workpiece_path.exists():
                # 扫描目录中的孔位文件夹
                for item in workpiece_path.iterdir():
                    # 严格验证孔位ID格式：必须以R开头并包含C，如R001C001
                    if (item.is_dir() and 
                        item.name.startswith('R') and 
                        'C' in item.name and
                        len(item.name) >= 7):  # 最小长度验证
                        # 检查是否有CCIDM子目录和CSV文件
                        ccidm_path = item / "CCIDM"
                        if ccidm_path.exists():
                            csv_files = list(ccidm_path.glob("*.csv"))
                            if csv_files:
                                available_holes.append(item.name)
                                self.logger.info(f"找到有效孔位: {item.name}")
                        else:
                            # 也检查直接在孔位目录下的CSV文件
                            csv_files = list(item.glob("*.csv"))
                            if csv_files:
                                available_holes.append(item.name)
                                self.logger.info(f"找到有效孔位: {item.name}")
                                
            self.logger.info(f"从文件系统扫描到 {len(available_holes)} 个孔位目录")
            
        except Exception as e:
            self.logger.error(f"扫描孔位目录时出错: {e}")
            
        # 如果没有找到任何孔位，返回空列表而不是默认列表
        if not available_holes:
            self.logger.warning("未找到任何可用的孔位数据文件")
            
        return sorted(available_holes)
        
    def verify_data_path(self) -> bool:
        """验证数据路径是否存在"""
        exists = self.data_root_path.exists()
        self.logger.info(f"数据路径验证: {self.data_root_path} {'存在' if exists else '不存在'}")
        return exists
        
    def get_csv_file_info(self, hole_id: str) -> Optional[Dict]:
        """获取CSV文件信息"""
        csv_paths = [
            self.data_root_path / hole_id / "CCIDM",
            self.data_root_path / hole_id,
        ]
        
        for path in csv_paths:
            if path.exists():
                csv_files = list(path.glob("*.csv"))
                if csv_files:
                    csv_file = csv_files[0]
                    try:
                        stat = csv_file.stat()
                        return {
                            'file_path': str(csv_file),
                            'file_size': stat.st_size,
                            'modified_time': stat.st_mtime,
                            'directory': str(path)
                        }
                    except Exception as e:
                        self.logger.error(f"获取文件信息时出错: {e}")
                        
        return None


class CSVDataController:
    """
    CSV数据控制器 - 高内聚设计
    职责：协调CSV读取器和数据处理
    """
    
    def __init__(self, data_root_path: Optional[str] = None):
        self.csv_reader = RealCSVReader(data_root_path)
        self.logger = logging.getLogger(__name__)
        
    def query_hole_data(self, hole_id: str) -> tuple[List[Dict], Dict]:
        """查询孔位数据并返回数据和统计信息"""
        self.logger.info(f"开始查询孔位数据: {hole_id}")
        
        # 读取CSV数据
        measurements = self.csv_reader.load_csv_data_for_hole(hole_id)
        
        if not measurements:
            self.logger.warning(f"未找到孔位 {hole_id} 的数据")
            return [], {}
            
        # 计算统计信息
        diameters = [m['diameter'] for m in measurements]
        qualified_count = sum(1 for m in measurements if m['is_qualified'])
        
        import numpy as np
        
        statistics = {
            'hole_id': hole_id,
            'total_count': len(measurements),
            'qualified_count': qualified_count,
            'unqualified_count': len(measurements) - qualified_count,
            'pass_rate': (qualified_count / len(measurements)) * 100,
            'mean_diameter': np.mean(diameters),
            'std_diameter': np.std(diameters),
            'min_diameter': np.min(diameters),
            'max_diameter': np.max(diameters)
        }
        
        self.logger.info(f"查询完成: {len(measurements)} 条数据, 合格率 {statistics['pass_rate']:.1f}%")
        
        return measurements, statistics
        
    def get_available_holes(self) -> List[str]:
        """获取可用孔位列表"""
        return self.csv_reader.get_available_holes()
        
    def verify_data_access(self) -> Dict:
        """验证数据访问状态"""
        return {
            'data_path_exists': self.csv_reader.verify_data_path(),
            'data_root_path': str(self.csv_reader.data_root_path),
            'available_holes_count': len(self.get_available_holes())
        }


if __name__ == "__main__":
    # 测试CSV读取器
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    # 创建CSV控制器
    csv_controller = CSVDataController()
    
    # 验证数据访问
    access_info = csv_controller.verify_data_access()
    print("数据访问验证:", access_info)
    
    # 获取可用孔位
    holes = csv_controller.get_available_holes()
    print(f"可用孔位: {len(holes)} 个")
    if holes:
        print(f"前5个孔位: {holes[:5]}")
    
    # 测试读取数据
    if holes:
        test_hole = holes[0]
        measurements, stats = csv_controller.query_hole_data(test_hole)
        print(f"测试读取 {test_hole}: {len(measurements)} 条数据")
        if stats:
            print(f"统计信息: {stats}")