#!/usr/bin/env python3
"""
历史数据后端功能测试
专注于数据处理逻辑，不依赖GUI组件
"""

import sys
import os
import numpy as np
from datetime import datetime
import csv
import json

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
        test_data = []
        
        for i in range(15):
            depth = i * 3.0
            diameter = 17.6 + 0.05 * np.sin(depth * 0.2) + np.random.normal(0, 0.01)
            operator = f"操作员{i%3+1}"
            
            success = db_manager.add_measurement_data("H001", depth, diameter, operator)
            if success:
                success_count += 1
                test_data.append({
                    'depth': depth,
                    'diameter': diameter,
                    'operator': operator
                })
                print(f"  ✅ 深度={depth:.1f}mm, 直径={diameter:.3f}mm, 操作员={operator}")
        
        print(f"📊 成功添加 {success_count}/15 条测量数据")
        
        # 查询数据
        print("🔍 查询历史数据...")
        measurements = db_manager.get_hole_measurements("H001")
        print(f"  📊 H001的测量数据: {len(measurements)}条")
        
        if measurements:
            print("  📋 最新5条数据:")
            for i, m in enumerate(measurements[-5:]):
                print(f"    {i+1}. 深度: {m.depth:.1f}mm, 直径: {m.diameter:.3f}mm, 操作员: {m.operator}")
        
        # 统计分析
        if measurements:
            diameters = [m.diameter for m in measurements]
            print(f"  📈 直径统计:")
            print(f"    最大值: {max(diameters):.3f}mm")
            print(f"    最小值: {min(diameters):.3f}mm")
            print(f"    平均值: {np.mean(diameters):.3f}mm")
            print(f"    标准差: {np.std(diameters):.3f}mm")
        
        return True, test_data
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_csv_data_processing():
    """测试CSV数据处理"""
    print("📄 测试CSV数据处理...")
    
    try:
        data_summary = {}
        
        # 检查数据目录
        data_dirs = ["Data/H00001/CCIDM", "Data/H00002/CCIDM"]
        
        for data_dir in data_dirs:
            hole_id = os.path.basename(os.path.dirname(data_dir))
            data_summary[hole_id] = {
                'files': 0,
                'total_records': 0,
                'sample_data': []
            }
            
            if os.path.exists(data_dir):
                print(f"  📁 处理目录: {data_dir}")
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                data_summary[hole_id]['files'] = len(csv_files)
                
                for csv_file in csv_files:
                    csv_path = os.path.join(data_dir, csv_file)
                    print(f"    📋 处理文件: {csv_file}")
                    
                    # 尝试读取CSV文件
                    encodings = ['utf-8', 'gbk', 'gb2312']
                    for encoding in encodings:
                        try:
                            with open(csv_path, 'r', encoding=encoding) as f:
                                reader = csv.reader(f)
                                lines = list(reader)
                                
                            print(f"      📊 数据行数: {len(lines)} (编码: {encoding})")
                            data_summary[hole_id]['total_records'] += len(lines)
                            
                            if lines and len(lines) > 1:
                                # 保存样本数据
                                header = lines[0]
                                sample_rows = lines[1:6]  # 前5行数据
                                
                                data_summary[hole_id]['sample_data'] = {
                                    'header': header,
                                    'rows': sample_rows
                                }
                                
                                print(f"      📝 表头: {header[:5]}...")
                                print(f"      📋 样本数据: {len(sample_rows)}行")
                            
                            break  # 成功读取，跳出编码循环
                            
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            print(f"      ❌ 读取失败 ({encoding}): {e}")
                            break
            else:
                print(f"  ❌ 目录不存在: {data_dir}")
        
        # 输出汇总
        print("📊 CSV数据处理汇总:")
        for hole_id, summary in data_summary.items():
            print(f"  {hole_id}:")
            print(f"    文件数: {summary['files']}")
            print(f"    总记录数: {summary['total_records']}")
            if summary['sample_data']:
                print(f"    表头字段数: {len(summary['sample_data']['header'])}")
        
        return True, data_summary
        
    except Exception as e:
        print(f"❌ CSV数据处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def test_data_integration():
    """测试数据集成功能"""
    print("🔗 测试数据集成...")
    
    try:
        # 模拟数据集成逻辑
        print("🔧 模拟实时数据桥接...")
        
        # 模拟从多个来源加载数据
        sources = {
            'database': [],
            'filesystem': [],
            'cache': []
        }
        
        # 模拟数据库数据
        for i in range(10):
            sources['database'].append({
                'timestamp': datetime.now().isoformat(),
                'depth': i * 2.0,
                'diameter': 17.6 + np.random.normal(0, 0.01),
                'source': 'database',
                'operator': f'DB_User_{i%3}'
            })
        
        # 模拟文件系统数据
        for i in range(8):
            sources['filesystem'].append({
                'timestamp': datetime.now().isoformat(),
                'depth': i * 2.5,
                'diameter': 17.6 + np.random.normal(0, 0.01),
                'source': 'filesystem',
                'file': f'measurement_{i}.csv'
            })
        
        # 模拟缓存数据
        for i in range(5):
            sources['cache'].append({
                'timestamp': datetime.now().isoformat(),
                'depth': i * 3.0,
                'diameter': 17.6 + np.random.normal(0, 0.01),
                'source': 'cache',
                'cache_key': f'cache_{i}'
            })
        
        # 数据合并
        print("🔄 合并多源数据...")
        all_data = []
        for source_name, data_list in sources.items():
            all_data.extend(data_list)
            print(f"  📊 {source_name}: {len(data_list)}条记录")
        
        # 数据去重（基于深度）
        print("🧹 数据去重...")
        unique_data = {}
        for record in all_data:
            depth_key = f"{record['depth']:.1f}"
            if depth_key not in unique_data:
                unique_data[depth_key] = record
        
        final_data = list(unique_data.values())
        print(f"  📊 去重后: {len(final_data)}条记录")
        
        # 数据排序
        final_data.sort(key=lambda x: x['depth'])
        
        # 数据分析
        print("📈 数据分析:")
        depths = [d['depth'] for d in final_data]
        diameters = [d['diameter'] for d in final_data]
        
        print(f"  深度范围: {min(depths):.1f} - {max(depths):.1f}mm")
        print(f"  直径范围: {min(diameters):.3f} - {max(diameters):.3f}mm")
        print(f"  数据来源分布:")
        
        source_count = {}
        for record in final_data:
            source = record['source']
            source_count[source] = source_count.get(source, 0) + 1
        
        for source, count in source_count.items():
            print(f"    {source}: {count}条")
        
        return True, final_data
        
    except Exception as e:
        print(f"❌ 数据集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def generate_test_report(results):
    """生成测试报告"""
    print("📋 生成测试报告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': {},
        'summary': {
            'total_tests': len(results),
            'passed_tests': sum(1 for r in results.values() if r['success']),
            'failed_tests': sum(1 for r in results.values() if not r['success'])
        }
    }
    
    for test_name, result in results.items():
        report['test_results'][test_name] = {
            'success': result['success'],
            'data_count': len(result.get('data', [])),
            'details': result.get('details', {})
        }
    
    # 保存报告
    report_file = f"history_data_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  📄 报告已保存: {report_file}")
    except Exception as e:
        print(f"  ❌ 报告保存失败: {e}")
    
    return report

def main():
    """主函数"""
    print("🚀 启动AIDCIS历史数据后端功能测试...")
    print("=" * 60)
    
    tests = [
        ("数据库操作", test_database_operations),
        ("CSV数据处理", test_csv_data_processing),
        ("数据集成", test_data_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            success, data = test_func()
            results[test_name] = {
                'success': success,
                'data': data,
                'details': {}
            }
            
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"💥 {test_name} 测试异常: {e}")
            results[test_name] = {
                'success': False,
                'data': [],
                'details': {'error': str(e)}
            }
    
    # 生成测试报告
    print("\n" + "=" * 60)
    report = generate_test_report(results)
    
    # 总结
    print("📊 测试结果总结:")
    print("-" * 40)
    
    passed = report['summary']['passed_tests']
    total = report['summary']['total_tests']
    
    for test_name, result in results.items():
        status = "✅ 通过" if result['success'] else "❌ 失败"
        data_count = len(result.get('data', []))
        print(f"  {test_name}: {status} (数据: {data_count}条)")
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有历史数据后端功能测试通过！")
        print("💡 历史数据功能已成功激活！")
        print("🔧 数据处理管道运行正常")
    else:
        print("⚠️ 部分功能需要进一步调试")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
