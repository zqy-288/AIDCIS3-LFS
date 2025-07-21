#!/usr/bin/env python3
"""
优先级3阶段2测试运行器
Priority 3 Phase 2 Test Runner - Database Integration
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
    print("🧪 单元测试 (Unit Tests) - 阶段2")
    print("=" * 80)
    
    # 导入单元测试模块
    from tests.unit.test_hybrid_manager import TestHybridDataManager
    from tests.unit.test_realtime_bridge import TestRealTimeDataBridge
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加HybridDataManager测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHybridDataManager))
    
    # 添加RealTimeDataBridge测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealTimeDataBridge))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_integration_tests():
    """运行集成测试"""
    print("\n" + "=" * 80)
    print("🔗 集成测试 (Integration Tests) - 阶段2")
    print("=" * 80)
    
    # 导入集成测试模块
    from tests.integration.test_database_integration_phase2 import TestDatabaseIntegrationPhase2
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseIntegrationPhase2))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_system_tests():
    """运行系统测试"""
    print("\n" + "=" * 80)
    print("🏗️ 系统测试 (System Tests) - 阶段2")
    print("=" * 80)
    
    # 导入系统测试模块
    from tests.system.test_priority3_phase2_system import TestPriority3Phase2System
    
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPriority3Phase2System))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_database_migration_test():
    """运行数据库迁移测试"""
    print("\n" + "=" * 80)
    print("🔄 数据库迁移测试 (Database Migration Test)")
    print("=" * 80)
    
    try:
        from aidcis2.data_management.database_migration import DatabaseMigration
        import tempfile
        import os
        
        # 创建临时数据库进行迁移测试
        temp_dir = tempfile.mkdtemp(prefix="migration_test_")
        test_db = os.path.join(temp_dir, "migration_test.db")
        database_url = f"sqlite:///{test_db}"
        
        migration = DatabaseMigration(database_url)
        
        print("执行数据库迁移...")
        start_time = time.time()
        success = migration.run_migration()
        migration_time = time.time() - start_time
        
        if success:
            print(f"✅ 数据库迁移成功 (耗时: {migration_time:.2f}秒)")
            
            # 验证迁移结果
            schema = migration.check_current_schema()
            print(f"📊 迁移后表结构:")
            for table, columns in schema.items():
                print(f"   {table}: {len(columns)} 列")
            
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
        else:
            print("❌ 数据库迁移失败")
            return False
            
    except Exception as e:
        print(f"💥 数据库迁移测试失败: {e}")
        return False


def print_test_summary(unit_result, integration_result, system_result, migration_success):
    """打印测试总结"""
    print("\n" + "=" * 80)
    print("📊 阶段2测试结果总结")
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
    
    print(f"\n🔄 数据库迁移测试:")
    print(f"   结果: {'✅ 成功' if migration_success else '❌ 失败'}")
    
    print(f"\n📈 总计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功: {total_success}")
    print(f"   失败: {total_failures}")
    print(f"   错误: {total_errors}")
    print(f"   成功率: {(total_success / total_tests * 100):.1f}%")
    print(f"   迁移测试: {'通过' if migration_success else '失败'}")
    
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
    all_success = (total_failures == 0 and total_errors == 0 and migration_success)
    
    if all_success:
        print(f"\n🎉 阶段2所有测试通过！数据库集成完成")
        print(f"✅ 混合数据管理系统已准备就绪")
        print(f"✅ 实时数据桥梁功能正常")
        print(f"✅ 数据库迁移系统可用")
    else:
        print(f"\n⚠️ 存在测试失败，需要修复后重新测试")
    
    return all_success


def print_phase2_achievements():
    """打印阶段2成就"""
    print("\n" + "=" * 80)
    print("🏆 优先级3阶段2成就总结")
    print("=" * 80)
    
    print("\n✅ 已完成的核心功能:")
    print("   🗄️ 数据库表结构扩展")
    print("      - workpieces表：添加7个新字段")
    print("      - holes表：添加5个新字段")
    print("      - 支持项目数据路径和文件系统集成")
    
    print("\n   🔄 HybridDataManager类")
    print("      - 统一管理数据库和文件系统")
    print("      - 双向数据同步机制")
    print("      - 数据一致性保证")
    print("      - 项目摘要和统计")
    
    print("\n   🌉 RealTimeDataBridge类")
    print("      - DXF预览到实时监控的无缝跳转")
    print("      - 历史数据加载和整合")
    print("      - 实时测量数据保存")
    print("      - 回调机制支持")
    
    print("\n   🔧 数据库迁移系统")
    print("      - 自动表结构升级")
    print("      - 数据备份和恢复")
    print("      - 迁移验证和回滚")
    
    print("\n📊 测试覆盖:")
    print("   - 单元测试：HybridDataManager + RealTimeDataBridge")
    print("   - 集成测试：数据库集成 + 同步机制")
    print("   - 系统测试：大规模 + 并发 + 压力 + 资源监控")
    print("   - 迁移测试：数据库升级验证")
    
    print("\n🚀 下一步：阶段3 - DXF加载集成")
    print("   - 修改load_dxf_file方法")
    print("   - 集成项目创建流程")
    print("   - 实现孔位数据初始化")
    print("   - 更新UI状态显示")


def main():
    """主函数"""
    print("🎯 优先级3阶段2：数据库集成测试")
    print("Priority 3 Phase 2: Database Integration Tests")
    
    start_time = time.time()
    
    try:
        # 运行数据库迁移测试
        migration_success = run_database_migration_test()
        
        # 运行所有测试
        unit_result = run_unit_tests()
        integration_result = run_integration_tests()
        system_result = run_system_tests()
        
        # 打印总结
        success = print_test_summary(unit_result, integration_result, system_result, migration_success)
        
        # 打印成就
        if success:
            print_phase2_achievements()
        
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
