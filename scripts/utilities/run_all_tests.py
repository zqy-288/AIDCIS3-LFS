#!/usr/bin/env python3
"""
运行所有测试的主脚本
"""

import sys
import unittest
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试")
    print("=" * 50)
    
    # 发现并运行单元测试
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """运行集成测试"""
    print("\n🔗 运行集成测试")
    print("=" * 50)
    
    # 发现并运行集成测试
    loader = unittest.TestLoader()
    suite = loader.discover('tests/integration', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_system_tests():
    """运行端到端测试"""
    print("\n🎯 运行端到端测试")
    print("=" * 50)
    
    # 发现并运行系统测试
    loader = unittest.TestLoader()
    suite = loader.discover('tests/system', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_performance_tests():
    """运行性能测试"""
    print("\n⚡ 运行性能测试")
    print("=" * 50)

    # 发现并运行性能测试
    loader = unittest.TestLoader()
    suite = loader.discover('tests/performance', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_specific_test_suite():
    """运行特定的测试套件"""
    print("🎯 孔位选择和操作功能测试套件")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加单元测试
    from tests.unit.test_hole_selection import TestHoleSelection
    suite.addTest(unittest.makeSuite(TestHoleSelection))

    # 添加集成测试
    from tests.integration.test_hole_operations import TestHoleOperationsIntegration
    suite.addTest(unittest.makeSuite(TestHoleOperationsIntegration))

    # 添加端到端测试
    from tests.system.test_hole_selection_e2e import TestHoleSelectionE2E
    suite.addTest(unittest.makeSuite(TestHoleSelectionE2E))

    # 添加性能测试
    from tests.performance.test_detection_speed import TestDetectionSpeed, TestDetectionFrequencyIntegration
    suite.addTest(unittest.makeSuite(TestDetectionSpeed))
    suite.addTest(unittest.makeSuite(TestDetectionFrequencyIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result

def main():
    """主函数"""
    print("🧪 孔位选择和操作功能 - 完整测试套件")
    print("=" * 60)
    print("测试内容:")
    print("1. 🔵 检测中颜色修复（橙色→蓝色）")
    print("2. 🖥️ 孔位信息显示修复")
    print("3. 🔍 搜索功能测试")
    print("4. 🎮 操作按钮状态测试")
    print("5. 📊 数据可用性检查测试")
    print("6. 🔄 页面跳转功能测试")
    print("7. ⏱️ 检测频率优化（200ms更新）")
    print("8. ⚡ 性能提升测试（7.5倍加速）")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 运行完整测试套件
        result = run_specific_test_suite()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)
        
        if result.wasSuccessful():
            print("✅ 所有测试通过！")
            print(f"🕒 测试耗时: {duration:.2f} 秒")
            print(f"🧪 运行测试: {result.testsRun}")
            print(f"❌ 失败: {len(result.failures)}")
            print(f"⚠️ 错误: {len(result.errors)}")
            print(f"⏭️ 跳过: {len(result.skipped)}")
        else:
            print("❌ 部分测试失败")
            print(f"🕒 测试耗时: {duration:.2f} 秒")
            print(f"🧪 运行测试: {result.testsRun}")
            print(f"❌ 失败: {len(result.failures)}")
            print(f"⚠️ 错误: {len(result.errors)}")
            print(f"⏭️ 跳过: {len(result.skipped)}")
            
            if result.failures:
                print("\n💥 失败的测试:")
                for test, traceback in result.failures:
                    print(f"  - {test}")
            
            if result.errors:
                print("\n⚠️ 错误的测试:")
                for test, traceback in result.errors:
                    print(f"  - {test}")
        
        print("\n🎯 **修复验证**")
        print("=" * 60)
        print("1. 🔵 检测中颜色: 橙色 → 蓝色")
        print("2. 🖥️ 孔位信息显示: 添加UI更新日志")
        print("3. 🔍 搜索功能: 完整的数据关联检查")
        print("4. 🎮 按钮控制: 智能启用/禁用")
        print("5. 📊 数据检查: H00001/H00002有数据，其他无数据")
        print("6. 🔄 页面跳转: 有数据时跳转，无数据时警告")
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试套件运行成功！")
        print("💡 现在可以测试修复后的功能:")
        print("   1. 启动程序: python main.py")
        print("   2. 加载DXF: 按 Ctrl+T")
        print("   3. 搜索H00001: 应显示完整信息")
        print("   4. 运行模拟: 检测中应显示蓝色")
        sys.exit(0)
    else:
        print("💥 测试套件运行失败！")
        print("请检查失败的测试并修复问题。")
        sys.exit(1)
