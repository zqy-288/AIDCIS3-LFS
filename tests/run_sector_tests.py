#!/usr/bin/env python3
"""
扇形系统测试套件执行脚本
运行所有层级的测试并生成报告
"""

import unittest
import sys
import os
import time
from io import StringIO
import argparse

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestResult:
    """测试结果统计"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.execution_time = 0
        self.failures = []
        self.errors = []

def run_test_suite(test_module_path, suite_name):
    """运行指定的测试套件"""
    print(f"\n{'='*60}")
    print(f"运行 {suite_name} 测试套件")
    print(f"{'='*60}")
    
    # 导入测试模块
    try:
        spec = importlib.util.spec_from_file_location("test_module", test_module_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
    except Exception as e:
        print(f"❌ 无法导入测试模块 {test_module_path}: {e}")
        return None
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    # 运行测试
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 收集结果
    test_result = TestResult()
    test_result.total_tests = result.testsRun
    test_result.passed_tests = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    test_result.failed_tests = len(result.failures)
    test_result.error_tests = len(result.errors)
    test_result.skipped_tests = len(result.skipped)
    test_result.execution_time = end_time - start_time
    test_result.failures = result.failures
    test_result.errors = result.errors
    
    # 打印结果
    print(f"测试数量: {test_result.total_tests}")
    print(f"✅ 通过: {test_result.passed_tests}")
    print(f"❌ 失败: {test_result.failed_tests}")
    print(f"💥 错误: {test_result.error_tests}")
    print(f"⏭️ 跳过: {test_result.skipped_tests}")
    print(f"⏱️ 执行时间: {test_result.execution_time:.2f}秒")
    
    # 显示失败和错误的详细信息
    if test_result.failures:
        print(f"\n❌ 失败的测试:")
        for test, traceback in test_result.failures:
            print(f"  - {test}")
            print(f"    {traceback.split(chr(10))[-2]}")  # 显示最后一行错误信息
    
    if test_result.errors:
        print(f"\n💥 错误的测试:")
        for test, traceback in test_result.errors:
            print(f"  - {test}")
            print(f"    {traceback.split(chr(10))[-2]}")  # 显示最后一行错误信息
    
    return test_result

def generate_test_report(unit_result, integration_result, system_result, output_file=None):
    """生成测试报告"""
    report_lines = []
    report_lines.append("# 扇形区域化进度管理系统 - 测试报告")
    report_lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # 总体统计
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_time = 0
    
    results = [
        ("单元测试", unit_result),
        ("集成测试", integration_result),
        ("系统测试", system_result)
    ]
    
    for name, result in results:
        if result:
            total_tests += result.total_tests
            total_passed += result.passed_tests
            total_failed += result.failed_tests
            total_errors += result.error_tests
            total_time += result.execution_time
    
    report_lines.append("## 📊 总体统计")
    report_lines.append(f"- 总测试数: {total_tests}")
    report_lines.append(f"- ✅ 通过: {total_passed}")
    report_lines.append(f"- ❌ 失败: {total_failed}")
    report_lines.append(f"- 💥 错误: {total_errors}")
    report_lines.append(f"- ⏱️ 总执行时间: {total_time:.2f}秒")
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        report_lines.append(f"- 🎯 成功率: {success_rate:.1f}%")
    
    report_lines.append("")
    
    # 详细结果
    report_lines.append("## 📋 详细结果")
    
    for name, result in results:
        if result:
            report_lines.append(f"\n### {name}")
            report_lines.append(f"- 测试数量: {result.total_tests}")
            report_lines.append(f"- ✅ 通过: {result.passed_tests}")
            report_lines.append(f"- ❌ 失败: {result.failed_tests}")
            report_lines.append(f"- 💥 错误: {result.error_tests}")
            report_lines.append(f"- ⏱️ 执行时间: {result.execution_time:.2f}秒")
            
            if result.failed_tests == 0 and result.error_tests == 0:
                report_lines.append("- 🎉 **全部通过!**")
            else:
                report_lines.append("- ⚠️ **存在问题**")
        else:
            report_lines.append(f"\n### {name}")
            report_lines.append("- ❌ **未能执行**")
    
    # 质量评估
    report_lines.append("\n## 🔍 质量评估")
    
    if total_tests > 0:
        if success_rate >= 95:
            report_lines.append("- 🟢 **优秀** - 测试覆盖全面，质量很高")
        elif success_rate >= 85:
            report_lines.append("- 🟡 **良好** - 测试基本通过，存在少量问题")
        elif success_rate >= 70:
            report_lines.append("- 🟠 **一般** - 存在一些问题需要修复")
        else:
            report_lines.append("- 🔴 **需要改进** - 存在较多问题，需要重点关注")
    
    # 建议
    report_lines.append("\n## 💡 建议")
    
    if total_failed > 0 or total_errors > 0:
        report_lines.append("- 🔧 优先修复失败和错误的测试用例")
        report_lines.append("- 📊 分析失败原因，改进代码质量")
        report_lines.append("- 🔄 建立持续集成流程，确保代码质量")
    else:
        report_lines.append("- ✅ 所有测试通过，继续保持代码质量")
        report_lines.append("- 📈 考虑增加更多边界情况的测试")
        report_lines.append("- 🚀 可以考虑进行性能优化测试")
    
    report_content = "\n".join(report_lines)
    
    # 输出报告
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"\n📋 测试报告已保存到: {output_file}")
    
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    print(report_content)
    
    return report_content

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='扇形系统测试套件')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--system', action='store_true', help='只运行系统测试')
    parser.add_argument('--report', help='测试报告输出文件路径')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 确定要运行的测试
    run_unit = args.unit or not (args.integration or args.system)
    run_integration = args.integration or not (args.unit or args.system)
    run_system = args.system or not (args.unit or args.integration)
    
    # 如果指定了具体类型，只运行指定的测试
    if args.unit or args.integration or args.system:
        run_unit = args.unit
        run_integration = args.integration
        run_system = args.system
    
    print("🧪 扇形区域化进度管理系统 - 测试套件")
    print("🚀 开始执行测试...")
    
    # 获取测试文件路径
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    unit_result = None
    integration_result = None
    system_result = None
    
    # 运行测试
    if run_unit:
        unit_tests = [
            (os.path.join(test_dir, "unit", "test_sector_manager.py"), "单元测试 - 扇形管理器"),
            (os.path.join(test_dir, "unit", "test_sector_view.py"), "单元测试 - 扇形视图"),
        ]
        
        for test_file, test_name in unit_tests:
            if os.path.exists(test_file):
                result = run_test_suite(test_file, test_name)
                if unit_result is None:
                    unit_result = result
                elif result:
                    # 合并结果
                    unit_result.total_tests += result.total_tests
                    unit_result.passed_tests += result.passed_tests
                    unit_result.failed_tests += result.failed_tests
                    unit_result.error_tests += result.error_tests
                    unit_result.execution_time += result.execution_time
                    unit_result.failures.extend(result.failures)
                    unit_result.errors.extend(result.errors)
    
    if run_integration:
        integration_file = os.path.join(test_dir, "integration", "test_sector_system_integration.py")
        if os.path.exists(integration_file):
            integration_result = run_test_suite(integration_file, "集成测试")
    
    if run_system:
        system_file = os.path.join(test_dir, "system", "test_sector_system_e2e.py")
        if os.path.exists(system_file):
            system_result = run_test_suite(system_file, "系统测试")
    
    # 生成测试报告
    generate_test_report(unit_result, integration_result, system_result, args.report)
    
    # 返回退出码
    total_failed = 0
    total_errors = 0
    
    for result in [unit_result, integration_result, system_result]:
        if result:
            total_failed += result.failed_tests
            total_errors += result.error_tests
    
    if total_failed > 0 or total_errors > 0:
        print(f"\n❌ 测试失败! 失败: {total_failed}, 错误: {total_errors}")
        sys.exit(1)
    else:
        print(f"\n✅ 所有测试通过!")
        sys.exit(0)

if __name__ == '__main__':
    import importlib.util
    main()