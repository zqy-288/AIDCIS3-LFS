#!/usr/bin/env python3
"""
简化的历史数据功能测试
专注于数据处理逻辑，不依赖GUI
"""

import sys
import os
import numpy as np
from datetime import datetime
import csv

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))
sys.path.insert(0, os.path.join(current_dir, 'aidcis2'))

def test_database_operations():
    """测试数据库操作"""
    print("🔧 测试数据库操作...")
    
    try:
        from modules.models import db_manager
        
        # 初始化数据库
        print("📊 初始化数据库...")
        db_manager.create_sample_data()
        
        # 添加测试数据
        print("📝 添加测试数据...")
        success_count = 0
        for i in range(20):
            depth = i * 2.0
            diameter = 25.0 + 0.1 * np.sin(depth * 0.1) + np.random.normal(0, 0.02)
            success = db_manager.add_measurement_data("H001", depth, diameter, f"操作员{i%3+1}")
            if success:
                success_count += 1
                print(f"  ✅ 添加测量数据: 深度={depth:.1f}mm, 直径={diameter:.3f}mm")
        
        print(f"📊 成功添加 {success_count}/20 条测量数据")
        
        # 查询数据
        print("🔍 查询历史数据...")
        measurements = db_manager.get_hole_measurements("H001")
        print(f"  📊 H001的测量数据: {len(measurements)}条")
        
        if measurements:
            print("  📋 数据样例:")
            for i, m in enumerate(measurements[:5]):
                print(f"    {i+1}. 深度: {m.depth:.1f}mm, 直径: {m.diameter:.3f}mm, 操作员: {m.operator}")
        
        holes = db_manager.get_workpiece_holes("WP-2024-001")
        print(f"  🕳️ 工件孔数: {len(holes)}个")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csv_data_loading():
    """测试CSV数据加载"""
    print("📄 测试CSV数据加载...")
    
    try:
        # 检查数据目录
        data_dirs = ["Data/H00001/CCIDM", "Data/H00002/CCIDM"]
        
        total_records = 0
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                print(f"  📁 找到数据目录: {data_dir}")
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                print(f"    📄 CSV文件: {len(csv_files)}个")
                
                for csv_file in csv_files:
                    csv_path = os.path.join(data_dir, csv_file)
                    print(f"      📋 {csv_file}")
                    
                    # 尝试读取CSV文件
                    try:
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            lines = list(reader)
                            print(f"        📊 数据行数: {len(lines)}")
                            total_records += len(lines)
                            
                            if lines:
                                print(f"        📝 表头: {lines[0][:5]}...")  # 显示前5列
                                
                                # 显示几行数据样例
                                if len(lines) > 1:
                                    print("        📋 数据样例:")
                                    for i, line in enumerate(lines[1:6]):  # 显示前5行数据
                                        print(f"          {i+1}. {line[:3]}...")
                                        
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        try:
                            with open(csv_path, 'r', encoding='gbk') as f:
                                reader = csv.reader(f)
                                lines = list(reader)
                                print(f"        📊 数据行数: {len(lines)} (编码: gbk)")
                                total_records += len(lines)
                        except Exception as e2:
                            print(f"        ❌ 读取失败 (多种编码): {e2}")
                    except Exception as e:
                        print(f"        ❌ 读取失败: {e}")
            else:
                print(f"  ❌ 数据目录不存在: {data_dir}")
        
        print(f"📊 总计加载 {total_records} 行数据")
        return True
        
    except Exception as e:
        print(f"❌ CSV数据加载测试失败: {e}")
        return False

def test_realtime_bridge():
    """测试实时数据桥接"""
    print("🌉 测试实时数据桥接...")
    
    try:
        from aidcis2.data_management.realtime_bridge import RealtimeBridge
        
        # 创建实时桥接实例
        print("🔧 创建实时桥接实例...")
        bridge = RealtimeBridge()
        
        # 测试历史数据加载
        print("📚 加载历史数据...")
        historical_data = bridge.load_historical_data("H00001", "WP-2024-001")
        print(f"  📊 加载历史数据: {len(historical_data)}条")
        
        # 显示部分数据
        if historical_data:
            print("  📋 数据样例:")
            for i, data in enumerate(historical_data[:5]):
                depth = data.get('depth', 'N/A')
                diameter = data.get('diameter', 'N/A')
                source = data.get('source', 'N/A')
                print(f"    {i+1}. 深度: {depth}, 直径: {diameter}, 来源: {source}")
        
        return True
        
    except Exception as e:
        print(f"❌ 实时桥接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hole_manager():
    """测试孔位管理器"""
    print("🕳️ 测试孔位管理器...")
    
    try:
        from aidcis2.data_management.hole_manager import HoleManager
        
        # 创建孔位管理器
        print("🔧 创建孔位管理器...")
        hole_manager = HoleManager()
        
        # 测试孔位数据获取
        print("📊 获取孔位测量数据...")
        measurements = hole_manager.get_hole_measurements("WP-2024-001", "H00001")
        print(f"  📊 H00001测量文件: {len(measurements)}个")
        
        for i, measurement_file in enumerate(measurements[:3]):
            print(f"    {i+1}. {measurement_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 孔位管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_templates():
    """测试数据模板"""
    print("📋 测试数据模板...")
    
    try:
        from aidcis2.data_management.data_templates import DataTemplates
        
        # 创建数据模板实例
        print("🔧 创建数据模板...")
        templates = DataTemplates()
        
        # 测试孔位模板
        print("🕳️ 获取孔位模板...")
        hole_template = templates.get_hole_template()
        print(f"  📋 孔位模板字段: {list(hole_template.keys())}")
        
        # 测试测量模板
        print("📊 获取测量模板...")
        measurement_template = templates.get_measurement_template()
        print(f"  📋 测量模板字段: {list(measurement_template.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据模板测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 启动AIDCIS历史数据功能测试...")
    print("=" * 60)
    
    tests = [
        ("数据库操作", test_database_operations),
        ("CSV数据加载", test_csv_data_loading),
        ("实时数据桥接", test_realtime_bridge),
        ("孔位管理器", test_hole_manager),
        ("数据模板", test_data_templates),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results[test_name] = success
            
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("-" * 40)
    
    passed = 0
    total = len(tests)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有历史数据功能测试通过！")
        print("💡 历史数据功能已成功激活！")
    else:
        print("⚠️ 部分功能需要进一步调试")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
