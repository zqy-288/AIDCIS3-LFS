"""
全景图同步系统测试运行器
运行所有相关的单元测试、集成测试和系统测试
"""

import sys
import os
import unittest
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def run_test_suite():
    """运行完整的测试套件"""
    print("=" * 60)
    print("全景图同步系统测试套件")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试套件列表
    test_modules = [
        ('单元测试', 'tests.unit.test_panorama_sync_manager'),
        ('集成测试', 'tests.integration.test_panorama_sync_integration'),
        ('系统测试', 'tests.system.test_panorama_sync_system')
    ]
    
    all_results = []
    total_start_time = time.time()
    
    for test_name, module_name in test_modules:
        print(f"\\n运行 {test_name}...")
        print("-" * 40)
        
        try:
            # 动态导入测试模块
            module = __import__(module_name, fromlist=[''])
            
            # 创建测试套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()
            
            # 记录结果
            test_result = {
                'name': test_name,
                'module': module_name,
                'duration': end_time - start_time,
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success': result.wasSuccessful()
            }
            all_results.append(test_result)
            
            print(f"\\n{test_name} 完成:")
            print(f"  运行时间: {test_result['duration']:.2f}秒")
            print(f"  测试数量: {test_result['tests_run']}")
            print(f"  失败: {test_result['failures']}")
            print(f"  错误: {test_result['errors']}")
            print(f"  跳过: {test_result['skipped']}")
            print(f"  结果: {'✅ 成功' if test_result['success'] else '❌ 失败'}")
            
        except Exception as e:
            print(f"❌ {test_name} 运行失败: {e}")
            test_result = {
                'name': test_name,
                'module': module_name,
                'duration': 0,
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'skipped': 0,
                'success': False,
                'exception': str(e)
            }
            all_results.append(test_result)
    
    # 生成总结报告
    total_duration = time.time() - total_start_time
    
    print("\\n" + "=" * 60)
    print("测试套件总结报告")
    print("=" * 60)
    
    total_tests = sum(r['tests_run'] for r in all_results)
    total_failures = sum(r['failures'] for r in all_results)
    total_errors = sum(r['errors'] for r in all_results)
    total_skipped = sum(r['skipped'] for r in all_results)
    all_successful = all(r['success'] for r in all_results)
    
    print(f"总运行时间: {total_duration:.2f}秒")
    print(f"总测试数量: {total_tests}")
    print(f"总失败数量: {total_failures}")
    print(f"总错误数量: {total_errors}")
    print(f"总跳过数量: {total_skipped}")
    print(f"总体结果: {'✅ 全部成功' if all_successful else '❌ 有失败'}")
    print()
    
    # 详细结果表格
    print("详细结果:")
    print(f"{'测试类型':<12} {'模块':<35} {'测试数':<8} {'失败':<6} {'错误':<6} {'耗时':<8} {'状态':<8}")
    print("-" * 85)
    
    for result in all_results:
        status = "✅ 成功" if result['success'] else "❌ 失败"
        print(f"{result['name']:<12} {result['module']:<35} {result['tests_run']:<8} "
              f"{result['failures']:<6} {result['errors']:<6} {result['duration']:<8.2f} {status}")
    
    print()
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_successful, all_results


def run_single_test(test_type):
    """运行单个测试类型"""
    test_mapping = {
        'unit': 'tests.unit.test_panorama_sync_manager',
        'integration': 'tests.integration.test_panorama_sync_integration', 
        'system': 'tests.system.test_panorama_sync_system'
    }
    
    if test_type not in test_mapping:
        print(f"❌ 未知测试类型: {test_type}")
        print(f"可用类型: {', '.join(test_mapping.keys())}")
        return False
    
    module_name = test_mapping[test_type]
    print(f"运行 {test_type} 测试: {module_name}")
    
    try:
        module = __import__(module_name, fromlist=[''])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False


def create_test_report(results, output_file=None):
    """创建测试报告文件"""
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"panorama_sync_test_report_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("全景图同步系统测试报告\\n")
        f.write("=" * 50 + "\\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        
        # 总体统计
        total_tests = sum(r['tests_run'] for r in results)
        total_failures = sum(r['failures'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        total_duration = sum(r['duration'] for r in results)
        
        f.write("总体统计:\\n")
        f.write(f"  总测试数: {total_tests}\\n")
        f.write(f"  总失败数: {total_failures}\\n")
        f.write(f"  总错误数: {total_errors}\\n")
        f.write(f"  总耗时: {total_duration:.2f}秒\\n")
        f.write(f"  成功率: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%\\n\\n")
        
        # 详细结果
        f.write("详细结果:\\n")
        for result in results:
            f.write(f"\\n{result['name']}:\\n")
            f.write(f"  模块: {result['module']}\\n")
            f.write(f"  测试数: {result['tests_run']}\\n")
            f.write(f"  失败数: {result['failures']}\\n")
            f.write(f"  错误数: {result['errors']}\\n")
            f.write(f"  耗时: {result['duration']:.2f}秒\\n")
            f.write(f"  结果: {'成功' if result['success'] else '失败'}\\n")
            
            if 'exception' in result:
                f.write(f"  异常: {result['exception']}\\n")
    
    print(f"\\n测试报告已保存: {output_file}")
    return output_file


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='全景图同步系统测试运行器')
    parser.add_argument('--type', choices=['unit', 'integration', 'system', 'all'], 
                       default='all', help='要运行的测试类型')
    parser.add_argument('--report', help='生成测试报告文件路径')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.type == 'all':
        success, results = run_test_suite()
        
        if args.report:
            create_test_report(results, args.report)
        
        sys.exit(0 if success else 1)
    else:
        success = run_single_test(args.type)
        sys.exit(0 if success else 1)