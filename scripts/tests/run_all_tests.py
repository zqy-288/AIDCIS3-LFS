#!/usr/bin/env python3
"""
运行所有测试
包括单元测试、集成测试、端到端测试和性能测试
"""

import sys
import unittest
import time
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def run_test_suite(test_module_name, suite_name):
    """运行单个测试套件"""
    print(f"\n{'='*60}")
    print(f"运行 {suite_name}")
    print(f"{'='*60}")
    
    try:
        # 导入测试模块
        test_module = __import__(test_module_name)
        
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # 返回结果
        return {
            'name': suite_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
    except Exception as e:
        print(f"错误: 无法运行 {suite_name}")
        print(f"原因: {str(e)}")
        return {
            'name': suite_name,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'success': False
        }


def main():
    """主函数"""
    print("="*80)
    print("AIDCIS3 测试套件")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 定义测试套件
    test_suites = [
        ('test_unit_sector_display', '单元测试 - 扇形显示组件'),
        ('test_unit_dxf_rotation', '单元测试 - DXF旋转功能'),
        ('test_integration_simulation', '集成测试 - 模拟进度功能'),
        ('test_e2e_complete_workflow', '端到端测试 - 完整工作流程'),
        ('test_performance_optimization', '性能测试 - 优化效果验证')
    ]
    
    # 运行所有测试
    results = []
    start_time = time.time()
    
    for module_name, suite_name in test_suites:
        result = run_test_suite(module_name, suite_name)
        results.append(result)
    
    total_time = time.time() - start_time
    
    # 显示总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    total_tests = sum(r['tests_run'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    
    print(f"\n总测试数: {total_tests}")
    print(f"成功: {total_tests - total_failures - total_errors}")
    print(f"失败: {total_failures}")
    print(f"错误: {total_errors}")
    print(f"总耗时: {total_time:.2f} 秒")
    
    # 详细结果
    print("\n详细结果:")
    print("-"*80)
    print(f"{'测试套件':<40} {'测试数':>8} {'失败':>8} {'错误':>8} {'状态':>10}")
    print("-"*80)
    
    for result in results:
        status = "✓ 通过" if result['success'] else "✗ 失败"
        print(f"{result['name']:<40} {result['tests_run']:>8} "
              f"{result['failures']:>8} {result['errors']:>8} {status:>10}")
    
    print("-"*80)
    
    # 测试覆盖的功能
    print("\n测试覆盖的主要功能:")
    print("1. ✓ 扇形显示组件（半径10px，字体3pt）")
    print("2. ✓ DXF文件90度逆时针预旋转")
    print("3. ✓ 扇形区域严格对应")
    print("4. ✓ 移除鼠标悬停工具提示")
    print("5. ✓ 模拟进度数据同步到多个面板")
    print("6. ✓ 大扇形显示位置（左上角）")
    print("7. ✓ 内存和性能优化")
    
    # 返回退出码
    all_passed = all(r['success'] for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    # 设置Python路径
    import os
    os.environ['PYTHONPATH'] = str(Path(__file__).parent.parent.parent / "src")
    
    # 运行测试
    exit_code = main()
    sys.exit(exit_code)