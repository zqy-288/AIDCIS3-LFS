#!/usr/bin/env python3
"""
独立的历史数据功能测试
不依赖主程序，避免冲突
"""

import os
import csv
import json
from datetime import datetime
import sqlite3

def analyze_csv_data():
    """分析CSV数据文件"""
    print("📊 分析CSV历史数据...")
    
    results = {}
    data_dirs = {
        "H00001": "Data/H00001/CCIDM",
        "H00002": "Data/H00002/CCIDM"
    }
    
    for hole_id, data_dir in data_dirs.items():
        results[hole_id] = {
            'directory_exists': False,
            'csv_files': [],
            'total_records': 0,
            'data_sample': [],
            'statistics': {}
        }
        
        if os.path.exists(data_dir):
            results[hole_id]['directory_exists'] = True
            print(f"  📁 {hole_id}: {data_dir}")
            
            # 查找CSV文件
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            results[hole_id]['csv_files'] = csv_files
            
            for csv_file in csv_files:
                csv_path = os.path.join(data_dir, csv_file)
                print(f"    📄 处理文件: {csv_file}")
                
                # 尝试读取CSV文件
                data_rows = []
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
                
                for encoding in encodings:
                    try:
                        with open(csv_path, 'r', encoding=encoding) as f:
                            reader = csv.reader(f)
                            data_rows = list(reader)
                        print(f"      ✅ 成功读取 {len(data_rows)} 行 (编码: {encoding})")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"      ❌ 读取失败 ({encoding}): {e}")
                        break
                
                if data_rows:
                    results[hole_id]['total_records'] += len(data_rows)
                    
                    # 分析数据结构
                    if len(data_rows) > 1:
                        header = data_rows[0]
                        data_samples = data_rows[1:6]  # 前5行数据
                        
                        results[hole_id]['data_sample'] = {
                            'header': header,
                            'sample_rows': data_samples
                        }
                        
                        print(f"      📋 表头: {header}")
                        print(f"      📊 数据样本 (前5行):")
                        for i, row in enumerate(data_samples):
                            print(f"        {i+1}. {row}")
                        
                        # 统计分析
                        if len(data_rows) > 10:  # 确保有足够数据进行分析
                            try:
                                # 假设最后一列是直径数据
                                diameters = []
                                for row in data_rows[1:]:  # 跳过表头
                                    if len(row) > 0:
                                        try:
                                            # 尝试解析最后一列作为直径
                                            diameter = float(row[-1])
                                            diameters.append(diameter)
                                        except (ValueError, IndexError):
                                            continue
                                
                                if diameters:
                                    results[hole_id]['statistics'] = {
                                        'count': len(diameters),
                                        'min_diameter': min(diameters),
                                        'max_diameter': max(diameters),
                                        'avg_diameter': sum(diameters) / len(diameters),
                                        'diameter_range': max(diameters) - min(diameters)
                                    }
                                    
                                    stats = results[hole_id]['statistics']
                                    print(f"      📈 统计分析:")
                                    print(f"        数据点数: {stats['count']}")
                                    print(f"        直径范围: {stats['min_diameter']:.3f} - {stats['max_diameter']:.3f} mm")
                                    print(f"        平均直径: {stats['avg_diameter']:.3f} mm")
                                    print(f"        直径变化: {stats['diameter_range']:.3f} mm")
                                    
                            except Exception as e:
                                print(f"      ⚠️ 统计分析失败: {e}")
        else:
            print(f"  ❌ {hole_id}: 目录不存在 - {data_dir}")
    
    return results

def analyze_image_data():
    """分析图像数据"""
    print("🖼️ 分析图像历史数据...")
    
    results = {}
    image_dirs = {
        "H00001": "Data/H00001/BISDM/result",
        "H00002": "Data/H00002/BISDM/result"
    }
    
    for hole_id, image_dir in image_dirs.items():
        results[hole_id] = {
            'directory_exists': False,
            'image_files': [],
            'image_count': 0,
            'file_sizes': {}
        }
        
        if os.path.exists(image_dir):
            results[hole_id]['directory_exists'] = True
            print(f"  📁 {hole_id}: {image_dir}")
            
            # 查找图像文件
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
            image_files = []
            
            for file in os.listdir(image_dir):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(file)
            
            image_files.sort()  # 排序
            results[hole_id]['image_files'] = image_files
            results[hole_id]['image_count'] = len(image_files)
            
            print(f"    📸 找到 {len(image_files)} 张图像:")
            for i, img_file in enumerate(image_files):
                img_path = os.path.join(image_dir, img_file)
                try:
                    file_size = os.path.getsize(img_path)
                    results[hole_id]['file_sizes'][img_file] = file_size
                    print(f"      {i+1}. {img_file} ({file_size/1024:.1f} KB)")
                except Exception as e:
                    print(f"      {i+1}. {img_file} (大小获取失败: {e})")
        else:
            print(f"  ❌ {hole_id}: 图像目录不存在 - {image_dir}")
    
    return results

def check_database():
    """检查数据库文件"""
    print("🗄️ 检查数据库文件...")
    
    db_files = ['detection_system.db']
    results = {}
    
    for db_file in db_files:
        results[db_file] = {
            'exists': False,
            'size': 0,
            'tables': [],
            'record_counts': {}
        }
        
        if os.path.exists(db_file):
            results[db_file]['exists'] = True
            results[db_file]['size'] = os.path.getsize(db_file)
            
            print(f"  📄 {db_file}: {results[db_file]['size']/1024:.1f} KB")
            
            try:
                # 连接数据库并查询表信息
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                results[db_file]['tables'] = tables
                
                print(f"    📊 数据表: {len(tables)}个")
                
                # 统计每个表的记录数
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table};")
                        count = cursor.fetchone()[0]
                        results[db_file]['record_counts'][table] = count
                        print(f"      {table}: {count}条记录")
                    except Exception as e:
                        print(f"      {table}: 查询失败 ({e})")
                
                conn.close()
                
            except Exception as e:
                print(f"    ❌ 数据库访问失败: {e}")
        else:
            print(f"  ❌ {db_file}: 文件不存在")
    
    return results

def generate_summary_report(csv_results, image_results, db_results):
    """生成汇总报告"""
    print("📋 生成历史数据功能汇总报告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'csv_analysis': csv_results,
        'image_analysis': image_results,
        'database_analysis': db_results,
        'summary': {
            'total_csv_files': 0,
            'total_csv_records': 0,
            'total_images': 0,
            'total_db_tables': 0,
            'total_db_records': 0
        }
    }
    
    # 计算汇总统计
    for hole_data in csv_results.values():
        report['summary']['total_csv_files'] += len(hole_data.get('csv_files', []))
        report['summary']['total_csv_records'] += hole_data.get('total_records', 0)
    
    for hole_data in image_results.values():
        report['summary']['total_images'] += hole_data.get('image_count', 0)
    
    for db_data in db_results.values():
        report['summary']['total_db_tables'] += len(db_data.get('tables', []))
        for count in db_data.get('record_counts', {}).values():
            report['summary']['total_db_records'] += count
    
    # 保存报告
    report_filename = f"history_data_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  📄 报告已保存: {report_filename}")
    except Exception as e:
        print(f"  ❌ 报告保存失败: {e}")
    
    return report

def main():
    """主函数"""
    print("🚀 AIDCIS 历史数据功能独立分析")
    print("=" * 60)
    print(f"📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 工作目录: {os.getcwd()}")
    
    # 1. 分析CSV数据
    print("\n" + "="*60)
    csv_results = analyze_csv_data()
    
    # 2. 分析图像数据
    print("\n" + "="*60)
    image_results = analyze_image_data()
    
    # 3. 检查数据库
    print("\n" + "="*60)
    db_results = check_database()
    
    # 4. 生成汇总报告
    print("\n" + "="*60)
    report = generate_summary_report(csv_results, image_results, db_results)
    
    # 5. 显示最终汇总
    print("\n" + "="*60)
    print("📊 历史数据功能分析汇总:")
    print("-" * 40)
    
    summary = report['summary']
    print(f"📄 CSV文件: {summary['total_csv_files']}个")
    print(f"📊 CSV记录: {summary['total_csv_records']}条")
    print(f"🖼️ 图像文件: {summary['total_images']}张")
    print(f"🗄️ 数据库表: {summary['total_db_tables']}个")
    print(f"📋 数据库记录: {summary['total_db_records']}条")
    
    # 功能状态评估
    print("\n🎯 功能状态评估:")
    csv_ok = summary['total_csv_files'] > 0 and summary['total_csv_records'] > 0
    image_ok = summary['total_images'] > 0
    db_ok = summary['total_db_tables'] > 0
    
    print(f"  CSV数据处理: {'✅ 正常' if csv_ok else '❌ 异常'}")
    print(f"  图像数据管理: {'✅ 正常' if image_ok else '❌ 异常'}")
    print(f"  数据库功能: {'✅ 正常' if db_ok else '❌ 异常'}")
    
    if csv_ok and image_ok:
        print("\n🎉 历史数据功能分析完成！")
        print("💡 主要功能组件都已就绪并包含数据")
        print("🔧 系统具备完整的历史数据处理能力")
    else:
        print("\n⚠️ 部分功能组件需要检查")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ 分析被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 分析过程出现异常: {e}")
        exit(1)
