#!/usr/bin/env python3
"""
浮动全景图修改功能测试运行器
运行所有相关的单元测试、集成测试和系统测试
"""

import unittest
import sys
import os
import time
from pathlib import Path
import argparse


def setup_test_environment():
    """设置测试环境"""
    # 添加src路径
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 设置环境变量
    os.environ["TESTING"] = "1"
    os.environ["QT_QPA_PLATFORM"] = "offscreen"  # 无头模式运行Qt


def discover_floating_panorama_tests():
    """发现浮动全景图相关的测试"""
    test_files = [
        "unit.test_floating_panorama_modifications",
        "unit.test_json_concurrent_io",
        "integration.test_floating_panorama_integration",
        "system.test_floating_panorama_system"
    ]
    
    suite = unittest.TestSuite()
    
    for test_module in test_files:
        try:
            # 动态导入测试模块
            module = __import__(f"tests.{test_module}", fromlist=[test_module.split('.')[-1]])
            
            # 添加所有测试类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, unittest.TestCase) and 
                    attr != unittest.TestCase):
                    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(attr))
        
        except ImportError as e:
            print(f"警告: 无法导入测试模块 {test_module}: {e}")
        except Exception as e:
            print(f"错误: 加载测试模块 {test_module} 时出错: {e}")
    
    return suite


def run_test_category(category, verbose=False):
    """运行特定类别的测试"""
    print(f"\n{'='*60}")
    print(f"运行 {category.upper()} 测试")
    print(f"{'='*60}")
    
    if category == "unit":
        test_modules = [
            "tests.unit.test_floating_panorama_modifications",
            "tests.unit.test_json_concurrent_io"
        ]
    elif category == "integration":
        test_modules = [
            "tests.integration.test_floating_panorama_integration"
        ]
    elif category == "system":
        test_modules = [
            "tests.system.test_floating_panorama_system"
        ]
    else:
        print(f"未知的测试类别: {category}")
        return False
    
    suite = unittest.TestSuite()
    
    for test_module in test_modules:
        try:
            module = __import__(test_module, fromlist=[test_module.split('.')[-1]])
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, unittest.TestCase) and 
                    attr != unittest.TestCase):
                    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(attr))
        except ImportError as e:
            print(f"跳过模块 {test_module}: {e}")
        except Exception as e:
            print(f"加载模块 {test_module} 出错: {e}")
    
    if suite.countTestCases() == 0:
        print(f"没有找到 {category} 测试")
        return False
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2 if verbose else 1,
        stream=sys.stdout,
        buffer=True
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 输出结果摘要
    print(f"\n{category.upper()} 测试摘要:")
    print(f"  测试数量: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  耗时: {end_time - start_time:.2f}秒")
    
    return result.wasSuccessful()


def generate_test_report(results):
    """生成测试报告"""
    report_path = Path(__file__).parent / "test_reports"
    report_path.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = report_path / f"floating_panorama_test_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("浮动全景图修改功能测试报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("测试覆盖范围:\n")
        f.write("- 浮动窗口样式修改\n")
        f.write("- 数据同步机制\n")
        f.write("- 扇形区域调整\n")
        f.write("- JSON并发读写修复\n\n")
        
        total_success = 0
        total_tests = 0
        
        for category, success in results.items():
            f.write(f"{category.upper()} 测试: {'通过' if success else '失败'}\n")
            total_tests += 1
            if success:
                total_success += 1
        
        f.write(f"\n总体结果: {total_success}/{total_tests} 类别通过\n")
        
        if total_success == total_tests:
            f.write("\n✅ 所有测试类别都通过，修改功能验证成功！\n")
        else:
            f.write("\n❌ 部分测试失败，需要进一步检查和修复。\n")
    
    print(f"\n测试报告已生成: {report_file}")
    return report_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="浮动全景图修改功能测试运行器")
    parser.add_argument(
        "--category", 
        choices=["unit", "integration", "system", "all"],
        default="all",
        help="要运行的测试类别 (默认: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成测试报告"
    )
    
    args = parser.parse_args()
    
    print("浮动全景图修改功能测试套件")
    print("=" * 40)
    print("测试功能:")
    print("1. 浮动窗口样式优化 (去除绿框、半透明背景、添加标题)")
    print("2. 浮动全景图数据同步 (复用左边栏更新逻辑)")
    print("3. 扇形区域调整 (向右下偏移、缩小尺寸)")
    print("4. JSON并发读写修复 (原子写入、重试机制)")
    print()
    
    # 设置测试环境
    setup_test_environment()
    
    # 运行测试
    start_time = time.time()
    results = {}
    
    if args.category == "all":
        categories = ["unit", "integration", "system"]
    else:
        categories = [args.category]
    
    for category in categories:
        print(f"\n开始运行 {category} 测试...")
        success = run_test_category(category, args.verbose)
        results[category] = success
    
    end_time = time.time()
    
    # 输出总结
    print(f"\n{'='*60}")
    print("测试执行总结")
    print(f"{'='*60}")
    
    for category, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{category.upper():12} 测试: {status}")
    
    total_time = end_time - start_time
    print(f"\n总耗时: {total_time:.2f}秒")
    
    # 生成报告
    if args.report:
        generate_test_report(results)
    
    # 返回退出码
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有测试都通过了！浮动全景图修改功能验证成功。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())