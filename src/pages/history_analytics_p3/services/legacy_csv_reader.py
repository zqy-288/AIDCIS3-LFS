"""
传统CSV读取器 - 直接基于重构前代码，不依赖其他模块
专门解决数据读取不完整的问题
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class LegacyCSVReader:
    """
    传统CSV读取器 - 完全复制重构前的read_csv_file方法
    确保能读取完整的836条数据
    """
    
    def __init__(self, data_root_path=None):
        if data_root_path:
            self.data_root_path = Path(data_root_path)
        else:
            # 自动检测数据目录
            possible_paths = [
                Path("D:\\AIDCIS3-LFS-master\\Data\\CAP1000"),
                Path("/mnt/d/AIDCIS3-LFS-master/Data/CAP1000"),
                Path("D:/AIDCIS3-LFS-master/Data/CAP1000"),
            ]
            
            for path in possible_paths:
                if path.exists():
                    self.data_root_path = path
                    break
            else:
                self.data_root_path = Path("/mnt/d/AIDCIS3-LFS-master/Data/CAP1000")
    
    def load_csv_data_for_hole(self, hole_id):
        """根据孔ID加载对应的CSV数据 - 完全基于重构前逻辑"""
        # 查找CSV文件路径
        csv_paths = [
            self.data_root_path / hole_id / "CCIDM",
            self.data_root_path / hole_id,
        ]

        csv_files = []
        csv_dir = None

        # 查找存在的CSV目录
        for path in csv_paths:
            if path.exists():
                csv_dir = path
                # 查找CSV文件
                for csv_file in path.iterdir():
                    if csv_file.suffix.lower() == '.csv':
                        csv_files.append(csv_file)
                if csv_files:
                    break

        if not csv_files:
            print(f"CSV数据目录不存在或无CSV文件，已检查路径: {csv_paths}")
            return []

        # 按时间排序
        csv_files.sort()

        # 选择第一个CSV文件（通常每个孔位只有一个CSV文件）
        selected_file = csv_files[0]
        print(f"为孔ID {hole_id} 选择文件: {selected_file}")

        # 读取CSV文件数据
        return self.read_csv_file(selected_file)

    def read_csv_file(self, file_path):
        """读取CSV文件并返回测量数据 - 完全复制重构前逻辑"""
        measurements = []

        try:
            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        print(f"成功使用编码 {encoding} 读取文件")
                        print(f"CSV文件列头: {headers}")

                        # 查找列索引 - 根据实际CSV文件结构调整
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径

                        # 验证列数是否足够
                        if len(headers) < 5:
                            print(f"CSV文件列数不足: {len(headers)} < 5")
                            continue

                        # 读取数据行 - 在同一个with块中，确保读取所有行
                        data_count = 0  # 添加计数器跟踪
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) >= 5:  # 改用>=确保至少有5列
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])
                                    
                                    data_count += 1  # 计数成功解析的行

                                    # 判断是否合格（标准直径17.73mm，非对称公差+0.07/-0.05mm）
                                    standard_diameter = 17.73
                                    upper_tolerance = 0.07
                                    lower_tolerance = 0.05
                                    is_qualified = (standard_diameter - lower_tolerance <= diameter <= standard_diameter + upper_tolerance)

                                    # 模拟时间（基于文件修改时间）
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
                                print(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环
                        print(f"📊 实际解析成功的数据行数: {data_count}")
                        break

                except UnicodeDecodeError:
                    continue
            else:
                print(f"无法使用任何编码读取文件: {file_path}")
                return []

        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            return []

        print(f"成功读取 {len(measurements)} 条测量数据")
        return measurements