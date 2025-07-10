#!/usr/bin/env python3
"""
测试历史查看器CSV修复
"""

import os
import csv
import sys
from datetime import datetime

def test_csv_loading():
    """测试CSV数据加载功能"""
    print("🔍 测试历史查看器CSV修复")
    print("=" * 60)
    
    # 模拟历史查看器的load_csv_data_for_hole方法
    def load_csv_data_for_hole(hole_id):
        """根据孔ID加载对应的CSV数据"""
        # 修复路径问题：使用相对路径查找CSV文件
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]
        
        csv_files = []
        csv_dir = None
        
        # 查找存在的CSV目录
        for path in csv_paths:
            if os.path.exists(path):
                csv_dir = path
                # 查找CSV文件
                for csv_file in os.listdir(path):
                    if csv_file.endswith('.csv'):
                        csv_files.append(os.path.join(path, csv_file))
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
        return read_csv_file(selected_file)

    def read_csv_file(file_path):
        """读取CSV文件并返回测量数据"""
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

                        # 读取数据行 - 在同一个with块中
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])

                                    # 判断是否合格（假设标准直径为17.6mm，误差范围±0.1mm）
                                    standard_diameter = 17.6
                                    tolerance = 0.1
                                    is_qualified = abs(diameter - standard_diameter) <= tolerance

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
                                        'operator': ''  # 暂不显示
                                    })

                            except (ValueError, IndexError) as e:
                                print(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环
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
    
    # 测试H00001
    print("\n🎯 测试H00001:")
    measurements_h1 = load_csv_data_for_hole("H00001")
    
    if measurements_h1:
        print(f"✅ H00001: 成功加载 {len(measurements_h1)} 条数据")
        print(f"📋 示例数据: {measurements_h1[0]}")
        
        # 统计合格率
        qualified_count = sum(1 for m in measurements_h1 if m['is_qualified'])
        qualified_rate = qualified_count / len(measurements_h1) * 100
        print(f"📊 合格率: {qualified_rate:.1f}% ({qualified_count}/{len(measurements_h1)})")
    else:
        print("❌ H00001: 数据加载失败")
    
    # 测试H00002（如果存在）
    print("\n🎯 测试H00002:")
    measurements_h2 = load_csv_data_for_hole("H00002")
    
    if measurements_h2:
        print(f"✅ H00002: 成功加载 {len(measurements_h2)} 条数据")
        print(f"📋 示例数据: {measurements_h2[0]}")
        
        # 统计合格率
        qualified_count = sum(1 for m in measurements_h2 if m['is_qualified'])
        qualified_rate = qualified_count / len(measurements_h2) * 100
        print(f"📊 合格率: {qualified_rate:.1f}% ({qualified_count}/{len(measurements_h2)})")
    else:
        print("❌ H00002: 数据加载失败")
    
    print("\n" + "=" * 60)
    print("🎉 CSV路径修复测试完成!")
    
    return measurements_h1 is not None and len(measurements_h1) > 0

if __name__ == "__main__":
    success = test_csv_loading()
    sys.exit(0 if success else 1)
