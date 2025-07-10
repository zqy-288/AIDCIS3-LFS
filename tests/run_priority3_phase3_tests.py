#!/usr/bin/env python3
"""
优先级3阶段3测试运行器
Priority 3 Phase 3 Test Runner - DXF Loading Integration
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
    print("🧪 单元测试 (Unit Tests) - 阶段3")
    print("=" * 80)
    
    # 导入单元测试模块
    from tests.unit.test_dxf_integration import TestDXFIntegrationManager
    from tests.unit.test_ui_integration_adapter import TestUIIntegrationAdapter
    from tests.unit.test_legacy_dxf_loader import TestLegacyDXFLoader
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加DXF集成管理器测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDXFIntegrationManager))
    
    # 添加UI集成适配器测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUIIntegrationAdapter))
    
    # 添加向后兼容加载器测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLegacyDXFLoader))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "=" * 80)
    print("🔗 集成测试 (Integration Tests) - 阶段3")
    print("=" * 80)
    
    # 导入集成测试模块
    from tests.integration.test_dxf_to_database_integration import TestDXFToDatabaseIntegration
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDXFToDatabaseIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_system_tests():
    """运行系统测试"""
    print("\n" + "=" * 80)
    print("🏗️ 系统测试 (System Tests) - 阶段3")
    print("=" * 80)
    
    # 导入系统测试模块
    from tests.system.test_priority3_phase3_system import TestPriority3Phase3System
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPriority3Phase3System))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_compatibility_verification():
    """运行兼容性验证"""
    print("\n" + "=" * 80)
    print("🔄 兼容性验证 (Compatibility Verification)")
    print("=" * 80)
    
    try:
        # 验证阶段1组件
        print("验证阶段1组件...")
        from aidcis2.data_management.project_manager import ProjectDataManager
        from aidcis2.data_management.hole_manager import HoleDataManager
        from aidcis2.data_management.data_templates import DataTemplates
        print("   ✅ 阶段1组件导入成功")
        
        # 验证阶段2组件
        print("验证阶段2组件...")
        from aidcis2.data_management.hybrid_manager import HybridDataManager
        from aidcis2.data_management.realtime_bridge import RealTimeDataBridge
        print("   ✅ 阶段2组件导入成功")
        
        # 验证阶段3组件
        print("验证阶段3组件...")
        from aidcis2.integration.dxf_integration_manager import DXFIntegrationManager
        from aidcis2.integration.ui_integration_adapter import UIIntegrationAdapter
        from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
        print("   ✅ 阶段3组件导入成功")
        
        # 验证组件集成
        print("验证组件集成...")
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="compatibility_test_")
        
        try:
            # 创建集成管理器
            manager = DXFIntegrationManager(temp_dir)
            print("   ✅ DXF集成管理器创建成功")
            
            # 创建UI适配器
            adapter = UIIntegrationAdapter(temp_dir)
            print("   ✅ UI集成适配器创建成功")
            
            # 创建向后兼容加载器
            loader = LegacyDXFLoader(temp_dir)
            print("   ✅ 向后兼容加载器创建成功")
            
            # 测试模式切换
            loader.set_mode("legacy")
            loader.set_mode("integrated")
            print("   ✅ 模式切换功能正常")
            
            # 清理
            manager.cleanup()
            adapter.cleanup()
            loader.cleanup()
            print("   ✅ 资源清理成功")
            
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        print("✅ 兼容性验证完成")
        return True
        
    except Exception as e:
        print(f"❌ 兼容性验证失败: {e}")
        return False


def print_test_summary(unit_result, integration_result, system_result, compatibility_success):
    """打印测试总结"""
    print("\n" + "=" * 80)
    print("📊 阶段3测试结果总结")
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
    
    print(f"\n🔄 兼容性验证:")
    print(f"   结果: {'✅ 成功' if compatibility_success else '❌ 失败'}")
    
    print(f"\n📈 总计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功: {total_success}")
    print(f"   失败: {total_failures}")
    print(f"   错误: {total_errors}")
    print(f"   成功率: {(total_success / total_tests * 100):.1f}%")
    print(f"   兼容性: {'通过' if compatibility_success else '失败'}")
    
    # 打印失败和错误详情
    if total_failures > 0 or total_errors > 0:
        print(f"\n❌ 失败和错误详情:")
        
        if unit_result.failures:
            print(f"\n单元测试失败:")
            for test, traceback in unit_result.failures:
                print(f"   - {test}")
        
        if unit_result.errors:
            print(f"\n单元测试错误:")
            for test, traceback in unit_result.errors:
                print(f"   - {test}")
        
        if integration_result.failures:
            print(f"\n集成测试失败:")
            for test, traceback in integration_result.failures:
                print(f"   - {test}")
        
        if integration_result.errors:
            print(f"\n集成测试错误:")
            for test, traceback in integration_result.errors:
                print(f"   - {test}")
        
        if system_result.failures:
            print(f"\n系统测试失败:")
            for test, traceback in system_result.failures:
                print(f"   - {test}")
        
        if system_result.errors:
            print(f"\n系统测试错误:")
            for test, traceback in system_result.errors:
                print(f"   - {test}")
    
    # 最终状态
    all_success = (total_failures == 0 and total_errors == 0 and compatibility_success)
    
    if all_success:
        print(f"\n🎉 阶段3所有测试通过！DXF加载集成完成")
        print(f"✅ DXF集成管理器功能正常")
        print(f"✅ UI集成适配器功能正常")
        print(f"✅ 向后兼容性保证")
        print(f"✅ 完整工作流验证通过")
    else:
        print(f"\n⚠️ 存在测试失败，需要修复后重新测试")
    
    return all_success


def print_phase3_achievements():
    """打印阶段3成就"""
    print("\n" + "=" * 80)
    print("🏆 优先级3阶段3成就总结")
    print("=" * 80)
    
    print("\n✅ 已完成的核心功能:")
    print("   🔧 DXFIntegrationManager类")
    print("      - 统一DXF解析和项目创建")
    print("      - 进度回调和错误处理")
    print("      - 数据一致性保证")
    print("      - 孔位位置搜索优化")
    
    print("\n   🎨 UIIntegrationAdapter类")
    print("      - UI友好的接口封装")
    print("      - 回调机制支持")
    print("      - 项目信息管理")
    print("      - 实时监控导航")
    
    print("\n   🔄 LegacyDXFLoader类")
    print("      - 向后兼容性保证")
    print("      - 双模式支持（传统/集成）")
    print("      - 无缝模式切换")
    print("      - 现有代码保护")
    
    print("\n   🌉 完整集成架构")
    print("      - DXF → 数据库 → 实时监控")
    print("      - 文件系统 + 数据库双轨存储")
    print("      - 错误处理和恢复机制")
    print("      - 性能优化和监控")
    
    print("\n📊 测试覆盖:")
    print("   - 单元测试：3个核心类的完整测试")
    print("   - 集成测试：DXF到数据库完整流程")
    print("   - 系统测试：大规模、并发、兼容性、端到端")
    print("   - 兼容性验证：阶段1-3组件集成")
    
    print("\n🚀 技术亮点:")
    print("   - 模块化设计：清晰的职责分离")
    print("   - 向后兼容：保护现有投资")
    print("   - 性能优化：大规模数据处理")
    print("   - 错误恢复：健壮的异常处理")
    print("   - 测试驱动：100%功能验证")
    
    print("\n🎯 集成效果:")
    print("   - DXF文件 → 自动项目创建")
    print("   - 孔位数据 → 数据库同步")
    print("   - UI操作 → 实时监控跳转")
    print("   - 历史兼容 → 无缝升级")
    
    print("\n🏁 优先级3完整实现:")
    print("   ✅ 阶段1：基础架构 (ProjectManager + HoleManager)")
    print("   ✅ 阶段2：数据库集成 (HybridManager + RealTimeBridge)")
    print("   ✅ 阶段3：DXF加载集成 (完整工作流)")


def main():
    """主函数"""
    print("🎯 优先级3阶段3：DXF加载集成测试")
    print("Priority 3 Phase 3: DXF Loading Integration Tests")
    
    start_time = time.time()
    
    try:
        # 运行兼容性验证
        compatibility_success = run_compatibility_verification()
        
        # 运行所有测试
        unit_result = run_unit_tests()
        integration_result = run_integration_tests()
        system_result = run_system_tests()
        
        # 打印总结
        success = print_test_summary(unit_result, integration_result, system_result, compatibility_success)
        
        # 打印成就
        if success:
            print_phase3_achievements()
        
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
