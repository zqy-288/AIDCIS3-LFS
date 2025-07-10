"""
测试数据生成器
为报告生成系统测试创建各种格式的样本数据
"""

import json
import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.csv_dir = self.output_dir / "csv"
        self.json_dir = self.output_dir / "json"
        self.images_dir = self.output_dir / "images"
        
        for dir_path in [self.csv_dir, self.json_dir, self.images_dir]:
            dir_path.mkdir(exist_ok=True)
            
    def generate_workpiece_info_samples(self) -> List[Dict]:
        """生成工件信息样本"""
        base_time = datetime.now()
        
        samples = [
            {
                'model': 'CP1400',
                'serial': 'SN-TEST-001',
                'operator': '张工程师',
                'start_time': base_time - timedelta(hours=2),
                'end_time': base_time - timedelta(hours=1),
                'equipment_id': 'AIDCIS-001',
                'batch_number': 'BATCH-2025-001'
            },
            {
                'model': 'CP1500',
                'serial': 'SN-TEST-002',
                'operator': '李技师',
                'start_time': base_time - timedelta(hours=4),
                'end_time': base_time - timedelta(hours=3),
                'equipment_id': 'AIDCIS-002',
                'batch_number': 'BATCH-2025-002'
            },
            {
                'model': 'CP1600',
                'serial': 'SN-TEST-003',
                'operator': '王工程师',
                'start_time': base_time - timedelta(hours=6),
                'end_time': base_time - timedelta(hours=5),
                'equipment_id': 'AIDCIS-001',
                'batch_number': 'BATCH-2025-003'
            }
        ]
        
        # 保存到JSON文件
        output_path = self.json_dir / "workpiece_info_samples.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2, default=str)
            
        return samples
        
    def generate_hole_data_samples(self) -> List[Dict]:
        """生成孔位数据样本"""
        samples = []
        
        # 生成不同规模的数据集
        hole_counts = [50, 100, 200]
        
        for i, total_holes in enumerate(hole_counts):
            hole_data = {
                'dataset_id': f'HOLES_{total_holes:03d}',
                'total_holes': total_holes,
                'checked_holes': total_holes - (i * 2),  # 一些未检测
                'qualified_holes': total_holes - (i * 5),  # 一些不合格
                'unqualified_holes': i * 5,
                'current_hole_id': f'H{total_holes//2:03d}',
                'holes_data': []
            }
            
            # 生成每个孔的数据
            for j in range(total_holes):
                hole_id = f'H{j+1:03d}'
                
                # 基础直径参数
                target_diameter = 17.6
                variation = np.random.normal(0, 0.005)  # 正常变化
                
                # 偶尔添加不合格的孔
                is_qualified = True
                if j % 20 == 0 and j > 0:  # 5%不合格率
                    variation += 0.1 if j % 40 == 0 else -0.1  # 超上限或下限
                    is_qualified = False
                    
                min_diameter = target_diameter + variation - 0.002
                max_diameter = target_diameter + variation + 0.002
                avg_diameter = target_diameter + variation
                
                hole_info = {
                    'hole_id': hole_id,
                    'min_diameter': round(min_diameter, 3),
                    'max_diameter': round(max_diameter, 3),
                    'avg_diameter': round(avg_diameter, 3),
                    'qualified': is_qualified,
                    'surface_defects': 'None' if is_qualified else 'Diameter out of tolerance',
                    'position_x': (j % 10) * 10,  # 网格排列
                    'position_y': (j // 10) * 10,
                    'depth': round(np.random.uniform(50, 200), 1),  # 孔深
                    'roundness': round(np.random.uniform(0.001, 0.005), 4),  # 圆度
                    'straightness': round(np.random.uniform(0.001, 0.003), 4)  # 直线度
                }
                
                hole_data['holes_data'].append(hole_info)
                
            samples.append(hole_data)
            
        # 保存到JSON文件
        output_path = self.json_dir / "hole_data_samples.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
            
        return samples
        
    def generate_measurement_data_samples(self) -> List[Dict]:
        """生成测量数据样本"""
        samples = []
        
        # 生成不同类型的测量数据
        scenarios = [
            ('normal', '正常测量'),
            ('with_outliers', '包含超差点'),
            ('trend_drift', '趋势漂移'),
            ('periodic_variation', '周期性变化')
        ]
        
        for scenario_id, scenario_name in scenarios:
            measurement_data = {
                'scenario_id': scenario_id,
                'scenario_name': scenario_name,
                'hole_id': f'H{scenario_id.upper()}',
                'target_diameter': 17.6,
                'upper_tolerance': 0.05,
                'lower_tolerance': 0.07,
                'measurement_points': []
            }
            
            # 生成测量点
            num_points = 1000
            for i in range(num_points):
                depth = i * 0.5  # 每0.5mm一个测量点
                
                if scenario_id == 'normal':
                    # 正常测量：小幅随机变化
                    diameter = 17.6 + np.random.normal(0, 0.005)
                    
                elif scenario_id == 'with_outliers':
                    # 包含超差点
                    if i in [200, 201, 202, 800, 801]:  # 特定位置有超差
                        diameter = 17.6 + (0.08 if i < 500 else -0.08)
                    else:
                        diameter = 17.6 + np.random.normal(0, 0.005)
                        
                elif scenario_id == 'trend_drift':
                    # 趋势漂移：直径逐渐增大
                    trend = (i / num_points) * 0.02  # 2%的漂移
                    diameter = 17.6 + trend + np.random.normal(0, 0.003)
                    
                elif scenario_id == 'periodic_variation':
                    # 周期性变化：正弦波变化
                    period_variation = 0.01 * np.sin(2 * np.pi * i / 100)
                    diameter = 17.6 + period_variation + np.random.normal(0, 0.002)
                    
                measurement_point = {
                    'depth': round(depth, 1),
                    'diameter': round(diameter, 4),
                    'timestamp': datetime.now().timestamp() + i * 0.1
                }
                
                measurement_data['measurement_points'].append(measurement_point)
                
            samples.append(measurement_data)
            
        # 保存到JSON文件
        output_path = self.json_dir / "measurement_data_samples.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
            
        return samples
        
    def generate_csv_samples(self):
        """生成CSV格式的样本数据"""
        # 1. 基础检测数据CSV
        basic_csv_path = self.csv_dir / "basic_inspection_data.csv"
        with open(basic_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            headers = [
                '孔位ID', '最小直径(mm)', '最大直径(mm)', '平均直径(mm)',
                '圆度(mm)', '直线度(mm)', '表面缺陷', '检测状态', 
                '位置X(mm)', '位置Y(mm)', '深度(mm)', '检测时间'
            ]
            writer.writerow(headers)
            
            # 写入数据
            base_time = datetime.now()
            for i in range(100):
                hole_id = f'H{i+1:03d}'
                is_qualified = i % 15 != 0  # 约6.7%不合格率
                
                if is_qualified:
                    min_dia = round(17.55 + np.random.normal(0, 0.003), 3)
                    max_dia = round(17.65 + np.random.normal(0, 0.003), 3)
                    avg_dia = round((min_dia + max_dia) / 2, 3)
                    defects = 'None'
                    status = '合格'
                else:
                    # 不合格孔位
                    min_dia = round(17.55 + np.random.normal(0, 0.020), 3)
                    max_dia = round(17.65 + np.random.normal(0, 0.020), 3)
                    avg_dia = round((min_dia + max_dia) / 2, 3)
                    defects = 'Diameter deviation'
                    status = '不合格'
                    
                roundness = round(np.random.uniform(0.001, 0.005), 4)
                straightness = round(np.random.uniform(0.001, 0.003), 4)
                pos_x = (i % 10) * 15
                pos_y = (i // 10) * 15
                depth = round(np.random.uniform(80, 150), 1)
                timestamp = (base_time + timedelta(seconds=i*30)).strftime('%Y-%m-%d %H:%M:%S')
                
                row = [
                    hole_id, min_dia, max_dia, avg_dia, roundness, straightness,
                    defects, status, pos_x, pos_y, depth, timestamp
                ]
                writer.writerow(row)
                
        # 2. 详细测量数据CSV
        detailed_csv_path = self.csv_dir / "detailed_measurement_data.csv"
        with open(detailed_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            headers = [
                '孔位ID', '测量深度(mm)', '直径值(mm)', '测量时间戳', 
                '探头角度(°)', '测量速度(mm/s)', '温度(°C)', '湿度(%)'
            ]
            writer.writerow(headers)
            
            # 为前5个孔位生成详细数据
            for hole_idx in range(5):
                hole_id = f'H{hole_idx+1:03d}'
                base_time = datetime.now()
                
                for depth_idx in range(200):  # 每个孔200个测量点
                    depth = depth_idx * 0.5
                    diameter = 17.6 + np.random.normal(0, 0.005)
                    timestamp = (base_time + timedelta(seconds=depth_idx*0.1)).timestamp()
                    angle = (depth_idx % 360)  # 探头旋转角度
                    speed = round(np.random.uniform(5, 15), 1)
                    temperature = round(np.random.uniform(20, 25), 1)
                    humidity = round(np.random.uniform(45, 65), 1)
                    
                    row = [
                        hole_id, round(depth, 1), round(diameter, 4), timestamp,
                        angle, speed, temperature, humidity
                    ]
                    writer.writerow(row)
                    
        # 3. 统计汇总CSV
        summary_csv_path = self.csv_dir / "inspection_summary.csv"
        with open(summary_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 写入表头
            headers = [
                '批次号', '工件型号', '工件序列号', '检测日期', '操作员',
                '总孔数', '已检孔数', '合格孔数', '不合格孔数', '合格率(%)',
                '平均直径(mm)', '直径标准差(mm)', '检测时长(分钟)'
            ]
            writer.writerow(headers)
            
            # 生成多个批次的汇总数据
            for i in range(10):
                batch_id = f'BATCH-2025-{i+1:03d}'
                model = f'CP{1400 + (i % 3) * 100}'
                serial = f'SN-{i+1:03d}'
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                operator = ['张工程师', '李技师', '王工程师'][i % 3]
                
                total_holes = np.random.randint(80, 120)
                checked_holes = total_holes - np.random.randint(0, 5)
                qualified_holes = checked_holes - np.random.randint(2, 8)
                unqualified_holes = checked_holes - qualified_holes
                qualification_rate = round(qualified_holes / checked_holes * 100, 1)
                
                avg_diameter = round(17.6 + np.random.normal(0, 0.002), 3)
                std_diameter = round(np.random.uniform(0.003, 0.008), 4)
                duration = np.random.randint(45, 90)
                
                row = [
                    batch_id, model, serial, date, operator,
                    total_holes, checked_holes, qualified_holes, unqualified_holes, qualification_rate,
                    avg_diameter, std_diameter, duration
                ]
                writer.writerow(row)
                
        return [basic_csv_path, detailed_csv_path, summary_csv_path]
        
    def generate_sample_images(self):
        """生成样本图像"""
        # 1. 模拟包络图
        envelope_img = Image.new('RGB', (1400, 1000), 'white')
        draw = ImageDraw.Draw(envelope_img)
        
        # 绘制坐标轴
        draw.line([(100, 900), (1300, 900)], fill='black', width=2)  # X轴
        draw.line([(100, 100), (100, 900)], fill='black', width=2)   # Y轴
        
        # 绘制数据曲线
        points = []
        for i in range(200):
            x = 100 + i * 6
            y = 500 + int(200 * np.sin(i * 0.1) * np.exp(-i * 0.01))
            points.append((x, y))
            
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill='blue', width=2)
            
        # 添加公差线
        draw.line([(100, 400), (1300, 400)], fill='red', width=2)  # 上限
        draw.line([(100, 600), (1300, 600)], fill='red', width=2)  # 下限
        
        # 添加标题
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
            
        draw.text((600, 50), "孔径包络图示例", fill='black', font=font)
        draw.text((600, 950), "探头深度 (mm)", fill='black', font=font)
        
        envelope_path = self.images_dir / "sample_envelope_chart.png"
        envelope_img.save(envelope_path, 'PNG', quality=95)
        
        # 2. 模拟内窥镜图像
        endoscope_img = Image.new('RGB', (800, 600), 'gray')
        draw = ImageDraw.Draw(endoscope_img)
        
        # 绘制孔壁
        draw.ellipse([(50, 50), (750, 550)], outline='black', width=3)
        
        # 添加一些模拟缺陷
        draw.rectangle([(200, 150), (250, 200)], outline='red', width=3)  # 缺陷1
        draw.rectangle([(500, 300), (550, 350)], outline='red', width=3)  # 缺陷2
        
        # 添加标注
        draw.text((260, 160), "缺陷1", fill='red', font=font)
        draw.text((560, 310), "缺陷2", fill='red', font=font)
        
        endoscope_path = self.images_dir / "sample_endoscope_image.png"
        endoscope_img.save(endoscope_path, 'PNG', quality=95)
        
        # 3. 模拟统计图表
        stats_img = Image.new('RGB', (1200, 800), 'white')
        draw = ImageDraw.Draw(stats_img)
        
        # 绘制直方图
        bars = [30, 45, 60, 80, 95, 75, 50, 25, 15, 10]
        bar_width = 80
        max_height = max(bars)
        
        for i, height in enumerate(bars):
            x1 = 100 + i * (bar_width + 10)
            y1 = 700
            x2 = x1 + bar_width
            y2 = 700 - int(height / max_height * 500)
            
            draw.rectangle([(x1, y2), (x2, y1)], fill='lightblue', outline='blue')
            
        draw.text((500, 50), "直径分布统计图示例", fill='black', font=font)
        
        stats_path = self.images_dir / "sample_statistics_chart.png"
        stats_img.save(stats_path, 'PNG', quality=95)
        
        return [envelope_path, endoscope_path, stats_path]
        
    def generate_mock_database_data(self):
        """生成模拟数据库数据"""
        # 创建SQLite数据文件（文本格式模拟）
        db_data = {
            'workpieces': [],
            'holes': [],
            'measurements': [],
            'defects': []
        }
        
        # 生成工件数据
        for i in range(10):
            workpiece = {
                'id': i + 1,
                'model': f'CP{1400 + (i % 3) * 100}',
                'serial': f'SN-DB-{i+1:03d}',
                'operator': ['张工程师', '李技师', '王工程师'][i % 3],
                'created_at': (datetime.now() - timedelta(days=i)).isoformat(),
                'status': 'completed' if i < 8 else 'in_progress'
            }
            db_data['workpieces'].append(workpiece)
            
        # 生成孔位数据
        hole_id = 1
        for workpiece_id in range(1, 11):
            hole_count = np.random.randint(50, 100)
            for j in range(hole_count):
                hole = {
                    'id': hole_id,
                    'workpiece_id': workpiece_id,
                    'hole_number': f'H{j+1:03d}',
                    'position_x': (j % 10) * 15,
                    'position_y': (j // 10) * 15,
                    'target_diameter': 17.6,
                    'measured_diameter': round(17.6 + np.random.normal(0, 0.005), 3),
                    'qualified': np.random.random() > 0.05,  # 95%合格率
                    'created_at': datetime.now().isoformat()
                }
                db_data['holes'].append(hole)
                hole_id += 1
                
        # 生成测量数据（仅前100个孔位）
        measurement_id = 1
        for hole_id in range(1, 101):
            measurement_count = np.random.randint(100, 500)
            for k in range(measurement_count):
                measurement = {
                    'id': measurement_id,
                    'hole_id': hole_id,
                    'depth': round(k * 0.5, 1),
                    'diameter': round(17.6 + np.random.normal(0, 0.005), 4),
                    'angle': k % 360,
                    'timestamp': datetime.now().timestamp() + k * 0.1
                }
                db_data['measurements'].append(measurement)
                measurement_id += 1
                
        # 生成缺陷数据
        defect_id = 1
        for hole_id in range(1, 101):
            if np.random.random() < 0.1:  # 10%的孔位有缺陷
                defect = {
                    'id': defect_id,
                    'hole_id': hole_id,
                    'defect_type': np.random.choice(['diameter_deviation', 'surface_scratch', 'roundness_error']),
                    'severity': np.random.choice(['minor', 'major', 'critical']),
                    'description': '自动检测发现的缺陷',
                    'detected_at': datetime.now().isoformat()
                }
                db_data['defects'].append(defect)
                defect_id += 1
                
        # 保存模拟数据库数据
        db_path = self.json_dir / "mock_database_data.json"
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
            
        return db_path
        
    def generate_all_samples(self):
        """生成所有样本数据"""
        print("🔄 开始生成测试数据...")
        
        # 生成各种数据
        workpiece_samples = self.generate_workpiece_info_samples()
        hole_samples = self.generate_hole_data_samples()
        measurement_samples = self.generate_measurement_data_samples()
        csv_files = self.generate_csv_samples()
        image_files = self.generate_sample_images()
        db_file = self.generate_mock_database_data()
        
        # 创建数据清单
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'description': '报告生成系统测试数据',
            'files': {
                'workpiece_samples': len(workpiece_samples),
                'hole_data_samples': len(hole_samples),
                'measurement_samples': len(measurement_samples),
                'csv_files': [str(f.name) for f in csv_files],
                'image_files': [str(f.name) for f in image_files],
                'database_file': str(db_file.name)
            },
            'statistics': {
                'total_workpieces': len(workpiece_samples),
                'total_holes': sum(sample['total_holes'] for sample in hole_samples),
                'total_measurement_points': sum(len(sample['measurement_points']) for sample in measurement_samples),
                'total_files': len(csv_files) + len(image_files) + 1
            }
        }
        
        manifest_path = self.output_dir / "data_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            
        print("✅ 测试数据生成完成！")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"📊 工件样本: {manifest['statistics']['total_workpieces']}")
        print(f"🔧 孔位总数: {manifest['statistics']['total_holes']}")
        print(f"📏 测量点总数: {manifest['statistics']['total_measurement_points']}")
        print(f"📄 文件总数: {manifest['statistics']['total_files']}")
        
        return manifest


def generate_test_data():
    """生成测试数据的主函数"""
    # 确定输出目录
    current_dir = Path(__file__).parent
    output_dir = current_dir / "generated"
    
    # 创建生成器并生成数据
    generator = TestDataGenerator(str(output_dir))
    manifest = generator.generate_all_samples()
    
    return manifest


if __name__ == '__main__':
    print("=" * 60)
    print("报告生成系统测试数据生成器")
    print("=" * 60)
    
    manifest = generate_test_data()
    
    print("\n" + "=" * 60)
    print("数据生成完成 ✅")
    print("=" * 60)