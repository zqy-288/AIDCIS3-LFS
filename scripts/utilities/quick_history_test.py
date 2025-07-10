#!/usr/bin/env python3
"""
快速历史数据功能验证
"""

import sys
import os
import csv
from datetime import datetime

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

def test_csv_files():
    """测试CSV文件读取"""
    print("📄 测试CSV文件读取...")
    
    data_dirs = ["Data/H00001/CCIDM", "Data/H00002/CCIDM"]
    results = {}
    
    for data_dir in data_dirs:
        hole_id = os.path.basename(os.path.dirname(data_dir))
        results[hole_id] = {'files': 0, 'records': 0}
        
        if os.path.exists(data_dir):
            print(f"  📁 {data_dir}")
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            results[hole_id]['files'] = len(csv_files)
            
            for csv_file in csv_files:
                csv_path = os.path.join(data_dir, csv_file)
                try:
                    # 尝试UTF-8编码
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        lines = list(reader)
                    encoding_used = 'utf-8'
                except UnicodeDecodeError:
                    # 尝试GBK编码
                    try:
                        with open(csv_path, 'r', encoding='gbk') as f:
                            reader = csv.reader(f)
                            lines = list(reader)
                        encoding_used = 'gbk'
                    except:
                        lines = []
                        encoding_used = 'failed'
                
                if lines:
                    results[hole_id]['records'] += len(lines)
                    print(f"    📋 {csv_file}: {len(lines)}行 ({encoding_used})")
                    if len(lines) > 1:
                        print(f"      表头: {lines[0][:3]}...")
                        print(f"      样本: {lines[1][:3]}...")
                else:
                    print(f"    ❌ {csv_file}: 读取失败")
        else:
            print(f"  ❌ 目录不存在: {data_dir}")
    
    return results

def test_database_basic():
    """测试基础数据库功能"""
    print("🔧 测试基础数据库功能...")
    
    try:
        from modules.models import db_manager
        
        # 初始化
        print("  📊 初始化数据库...")
        db_manager.create_sample_data()
        
        # 查询孔位
        holes = db_manager.get_workpiece_holes("WP-2024-001")
        print(f"  🕳️ 工件孔数: {len(holes)}个")
        
        if holes:
            for hole in holes[:3]:
                print(f"    - {hole.hole_id}: 目标直径={hole.target_diameter}mm")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 数据库测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 快速历史数据功能验证")
    print("=" * 50)
    
    # 测试CSV文件
    print("\n1. CSV文件测试")
    csv_results = test_csv_files()
    
    # 测试数据库
    print("\n2. 数据库测试")
    db_success = test_database_basic()
    
    # 汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    print("CSV数据:")
    total_files = 0
    total_records = 0
    for hole_id, data in csv_results.items():
        print(f"  {hole_id}: {data['files']}个文件, {data['records']}条记录")
        total_files += data['files']
        total_records += data['records']
    
    print(f"数据库: {'✅ 正常' if db_success else '❌ 异常'}")
    
    print(f"\n🎯 总计: {total_files}个CSV文件, {total_records}条记录")
    
    if total_files > 0 and db_success:
        print("🎉 历史数据功能基础验证通过！")
        print("💡 数据文件和数据库都可以正常访问")
    else:
        print("⚠️ 部分功能需要检查")

if __name__ == "__main__":
    main()
