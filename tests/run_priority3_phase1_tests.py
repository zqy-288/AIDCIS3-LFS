#!/usr/bin/env python3
"""
优先级3阶段1测试运行器
Priority 3 Phase 1 Test Runner
"""

import unittest
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """运行单元测试"""
    print("=" * 80)
    print("🧪 单元测试 (Unit Tests)")
    print("=" * 80)
    
    # 导入单元测试模块
    from tests.unit.test_project_manager import TestProjectDataManager
    from tests.unit.test_hole_manager import TestHoleDataManager
    from tests.unit.test_data_templates import TestDataTemplates, TestDataValidator, TestDataExporter
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加ProjectDataManager测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProjectDataManager))
    
    # 添加HoleDataManager测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHoleDataManager))
    
    # 添加DataTemplates测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataTemplates))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataValidator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataExporter))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "=" * 80)
    print("🔗 集成测试 (Integration Tests)")
    print("=" * 80)
    
    # 导入集成测试模块
    from tests.integration.test_data_management_integration import TestDataManagementIntegration
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataManagementIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_system_tests():
    """运行系统测试"""
    print("\n" + "=" * 80)
    print("🏗️ 系统测试 (System Tests)")
    print("=" * 80)
    
    # 导入系统测试模块
    from tests.system.test_priority3_phase1_system import TestPriority3Phase1System
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPriority3Phase1System))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def print_test_summary(unit_result, integration_result, system_result):
    """打印测试总结"""
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    # 计算总计
    total_tests = unit_result.testsRun + integration_result.testsRun + system_result.testsRun
    total_failures = len(unit_result.failures) + len(integration_result.failures) + len(system_result.failures)
    total_errors = len(unit_result.errors) + len(integration_result.errors) + len(system_result.errors)
    total_success = total_tests - total_failures - total_errors
    
    # 打印详细结果
    print(f"\n🧪 单元测试结果:")
    print(f"   测试数量: {unit_result.testsRun}")
    print(f"   成功: {unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)}")
    print(f"   失败: {len(unit_result.failures)}")
    print(f"   错误: {len(unit_result.errors)}")
    
    print(f"\n🔗 集成测试结果:")
    print(f"   测试数量: {integration_result.testsRun}")
    print(f"   成功: {integration_result.testsRun - len(integration_result.failures) - len(integration_result.errors)}")
    print(f"   失败: {len(integration_result.failures)}")
    print(f"   错误: {len(integration_result.errors)}")
    
    print(f"\n🏗️ 系统测试结果:")
    print(f"   测试数量: {system_result.testsRun}")
    print(f"   成功: {system_result.testsRun - len(system_result.failures) - len(system_result.errors)}")
    print(f"   失败: {len(system_result.failures)}")
    print(f"   错误: {len(system_result.errors)}")
    
    print(f"\n📈 总计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功: {total_success}")
    print(f"   失败: {total_failures}")
    print(f"   错误: {total_errors}")
    print(f"   成功率: {(total_success / total_tests * 100):.1f}%")
    
    # 打印失败和错误详情
    if total_failures > 0 or total_errors > 0:
        print(f"\n❌ 失败和错误详情:")
        
        if unit_result.failures:
            print(f"\n单元测试失败:")
            for test, traceback in unit_result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if unit_result.errors:
            print(f"\n单元测试错误:")
            for test, traceback in unit_result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        if integration_result.failures:
            print(f"\n集成测试失败:")
            for test, traceback in integration_result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if integration_result.errors:
            print(f"\n集成测试错误:")
            for test, traceback in integration_result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        if system_result.failures:
            print(f"\n系统测试失败:")
            for test, traceback in system_result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if system_result.errors:
            print(f"\n系统测试错误:")
            for test, traceback in system_result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # 最终状态
    if total_failures == 0 and total_errors == 0:
        print(f"\n🎉 所有测试通过！优先级3阶段1基础架构测试完成")
        print(f"✅ 数据管理系统已准备就绪")
    else:
        print(f"\n⚠️ 存在测试失败，需要修复后重新测试")
    
    return total_failures == 0 and total_errors == 0


def main():
    """主函数"""
    print("🎯 优先级3阶段1：数据管理系统测试")
    print("Priority 3 Phase 1: Data Management System Tests")
    
    start_time = time.time()
    
    try:
        # 运行所有测试
        unit_result = run_unit_tests()
        integration_result = run_integration_tests()
        system_result = run_system_tests()
        
        # 打印总结
        success = print_test_summary(unit_result, integration_result, system_result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n⏱️ 总测试时间: {total_time:.2f}秒")
        print("=" * 80)
        
        return success
        
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
