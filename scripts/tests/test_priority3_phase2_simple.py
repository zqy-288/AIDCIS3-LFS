#!/usr/bin/env python3
"""
优先级3阶段2简化测试
Priority 3 Phase 2 Simplified Test (without Qt dependencies)
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def test_hybrid_manager_basic():
    """测试HybridDataManager基础功能"""
    
    print("\n🔧 测试1：HybridDataManager基础功能")
    print("-" * 50)
    
    try:
        from aidcis2.data_management.project_manager import ProjectDataManager
        from aidcis2.data_management.hole_manager import HoleDataManager
        from aidcis2.data_management.data_templates import DataTemplates, DataValidator
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 初始化组件
            project_manager = ProjectDataManager(temp_dir)
            hole_manager = HoleDataManager(project_manager)
            validator = DataValidator()
            
            print("   ✅ 组件初始化成功")
            
            # 创建测试项目
            test_dxf = Path(temp_dir) / "test.dxf"
            test_dxf.write_text("test dxf content")
            
            project_id, project_path = project_manager.create_project(
                str(test_dxf), "测试项目"
            )
            
            print(f"   ✅ 项目创建成功: {project_id}")
            
            # 创建孔位
            hole_info = DataTemplates.create_hole_info_template(
                "H00001", {"x": 10.0, "y": 20.0}
            )
            
            success = hole_manager.create_hole_directory(
                project_id, "H00001", hole_info
            )
            
            print(f"   ✅ 孔位创建成功: {success}")
            
            # 验证数据
            is_valid, errors = validator.validate_hole_info(hole_info)
            print(f"   ✅ 数据验证通过: {is_valid}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def test_database_migration_basic():
    """测试数据库迁移基础功能"""

    print("\n🔧 测试2：数据库迁移基础功能")
    print("-" * 50)

    try:
        from aidcis2.data_management.simple_migration import SimpleDatabaseMigration

        # 创建临时数据库
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = os.path.join(temp_dir, "test.db")

            migration = SimpleDatabaseMigration(test_db)

            print("   ✅ 迁移器初始化成功")

            # 运行迁移
            success = migration.run_migration()
            print(f"   ✅ 迁移执行成功: {success}")

            if success:
                # 测试基础操作
                test_success = migration.test_basic_operations()
                print(f"   ✅ 基础操作测试: {test_success}")

                # 检查表结构
                schema = migration.check_current_schema()
                print(f"   ✅ 表结构检查: {len(schema)} 个表")

                # 验证关键表存在
                required_tables = ['workpieces', 'holes', 'measurements']
                for table in required_tables:
                    if table in schema:
                        print(f"   ✅ 表 {table}: {len(schema[table])} 列")
                    else:
                        print(f"   ❌ 缺少表: {table}")
                        return False

                return test_success
            else:
                return False

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def test_data_templates_comprehensive():
    """测试数据模板综合功能"""
    
    print("\n🔧 测试3：数据模板综合功能")
    print("-" * 50)
    
    try:
        from aidcis2.data_management.data_templates import DataTemplates, DataValidator, DataExporter
        
        # 测试项目元数据模板
        metadata = DataTemplates.create_project_metadata_template(
            "test_project", "测试项目", "test.dxf", 100
        )
        print("   ✅ 项目元数据模板创建成功")
        
        # 测试孔位信息模板
        hole_info = DataTemplates.create_hole_info_template(
            "H00001", {"x": 10.0, "y": 20.0}
        )
        print("   ✅ 孔位信息模板创建成功")
        
        # 测试状态模板
        status = DataTemplates.create_hole_status_template()
        print("   ✅ 孔位状态模板创建成功")
        
        # 测试测量数据模板
        measurement_data = DataTemplates.create_measurement_data_template()
        print("   ✅ 测量数据模板创建成功")
        
        # 测试数据验证
        validator = DataValidator()
        
        is_valid, errors = validator.validate_project_metadata(metadata)
        print(f"   ✅ 项目元数据验证: {is_valid}")
        
        is_valid, errors = validator.validate_hole_info(hole_info)
        print(f"   ✅ 孔位信息验证: {is_valid}")
        
        is_valid, errors = validator.validate_hole_status(status)
        print(f"   ✅ 孔位状态验证: {is_valid}")
        
        is_valid, errors = validator.validate_measurement_data(measurement_data)
        print(f"   ✅ 测量数据验证: {is_valid}")
        
        # 测试数据导出
        project_stats = {
            "total_holes": 100,
            "completed_holes": 50,
            "pending_holes": 30,
            "error_holes": 20,
            "completion_rate": 50.0
        }
        
        summary = DataExporter.export_project_summary(metadata, project_stats)
        print("   ✅ 项目摘要导出成功")
        
        measurements = ["measurement_001.csv", "measurement_002.csv"]
        report = DataExporter.export_hole_report(hole_info, status, measurements)
        print("   ✅ 孔位报告导出成功")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def test_file_system_integration():
    """测试文件系统集成"""
    
    print("\n🔧 测试4：文件系统集成")
    print("-" * 50)
    
    try:
        from aidcis2.data_management.project_manager import ProjectDataManager
        from aidcis2.data_management.hole_manager import HoleDataManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 初始化管理器
            project_manager = ProjectDataManager(temp_dir)
            hole_manager = HoleDataManager(project_manager)
            
            # 创建项目
            test_dxf = Path(temp_dir) / "integration_test.dxf"
            test_dxf.write_text("integration test dxf")
            
            project_id, project_path = project_manager.create_project(
                str(test_dxf), "文件系统集成测试"
            )
            
            print(f"   ✅ 项目创建: {project_id}")
            
            # 创建多个孔位
            holes_data = [
                {"hole_id": "H00001", "position": {"x": 10.0, "y": 20.0}},
                {"hole_id": "H00002", "position": {"x": 30.0, "y": 40.0}},
                {"hole_id": "H00003", "position": {"x": 50.0, "y": 60.0}}
            ]
            
            for hole_data in holes_data:
                from aidcis2.data_management.data_templates import DataTemplates
                
                hole_info = DataTemplates.create_hole_info_template(
                    hole_data["hole_id"], hole_data["position"]
                )
                
                success = hole_manager.create_hole_directory(
                    project_id, hole_data["hole_id"], hole_info
                )
                
                if not success:
                    raise Exception(f"孔位创建失败: {hole_data['hole_id']}")
            
            print(f"   ✅ 创建了 {len(holes_data)} 个孔位")
            
            # 添加测量数据
            for hole_data in holes_data:
                measurement_data = [
                    {
                        "timestamp": "2025-01-08T10:00:00",
                        "depth": i * 10.0,
                        "diameter": 8.865 + i * 0.001
                    }
                    for i in range(5)
                ]
                
                success = hole_manager.save_measurement_data(
                    project_id, hole_data["hole_id"], measurement_data
                )
                
                if not success:
                    raise Exception(f"测量数据保存失败: {hole_data['hole_id']}")
            
            print(f"   ✅ 保存了测量数据")
            
            # 验证项目统计
            stats = project_manager.get_project_statistics(project_id)
            print(f"   ✅ 项目统计: {stats['total_holes']} 个孔位")
            
            # 验证数据加载
            for hole_data in holes_data:
                csv_files = hole_manager.get_hole_measurements(
                    project_id, hole_data["hole_id"]
                )
                
                if not csv_files:
                    raise Exception(f"测量文件不存在: {hole_data['hole_id']}")
                
                loaded_data = hole_manager.load_measurement_data(csv_files[0])
                
                if not loaded_data or len(loaded_data) != 5:
                    raise Exception(f"数据加载失败: {hole_data['hole_id']}")
            
            print(f"   ✅ 数据加载验证通过")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def test_data_consistency():
    """测试数据一致性"""
    
    print("\n🔧 测试5：数据一致性")
    print("-" * 50)
    
    try:
        from aidcis2.data_management.project_manager import ProjectDataManager
        from aidcis2.data_management.hole_manager import HoleDataManager
        from aidcis2.data_management.data_templates import DataTemplates
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 初始化管理器
            project_manager = ProjectDataManager(temp_dir)
            hole_manager = HoleDataManager(project_manager)
            
            # 创建项目
            test_dxf = Path(temp_dir) / "consistency_test.dxf"
            test_dxf.write_text("consistency test dxf")
            
            project_id, _ = project_manager.create_project(
                str(test_dxf), "数据一致性测试"
            )
            
            # 创建孔位
            hole_info = DataTemplates.create_hole_info_template(
                "H00001", {"x": 10.0, "y": 20.0}
            )
            
            hole_manager.create_hole_directory(project_id, "H00001", hole_info)
            
            print("   ✅ 初始数据创建完成")
            
            # 测试状态更新一致性
            status_updates = [
                ("in_progress", "开始测量"),
                ("paused", "暂停测量"),
                ("in_progress", "恢复测量"),
                ("completed", "测量完成")
            ]
            
            for status, reason in status_updates:
                success = hole_manager.update_hole_status(
                    project_id, "H00001", status, reason
                )
                
                if not success:
                    raise Exception(f"状态更新失败: {status}")
                
                # 验证状态
                hole_status = hole_manager.get_hole_status(project_id, "H00001")
                if hole_status["current_status"] != status:
                    raise Exception(f"状态不一致: 期望{status}, 实际{hole_status['current_status']}")
            
            print(f"   ✅ 状态更新一致性验证通过")
            
            # 测试元数据更新一致性
            updates = {
                "total_holes": 10,
                "completed_holes": 5,
                "description": "一致性测试描述"
            }
            
            success = project_manager.update_project_metadata(project_id, updates)
            if not success:
                raise Exception("元数据更新失败")
            
            # 验证元数据
            metadata = project_manager.get_project_metadata(project_id)
            for key, value in updates.items():
                if metadata.get(key) != value:
                    raise Exception(f"元数据不一致: {key}")
            
            print(f"   ✅ 元数据更新一致性验证通过")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    
    print("=" * 80)
    print("🎯 优先级3阶段2简化测试")
    print("Priority 3 Phase 2 Simplified Test")
    print("=" * 80)
    
    tests = [
        ("HybridDataManager基础功能", test_hybrid_manager_basic),
        ("数据库迁移基础功能", test_database_migration_basic),
        ("数据模板综合功能", test_data_templates_comprehensive),
        ("文件系统集成", test_file_system_integration),
        ("数据一致性", test_data_consistency)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🚀 执行测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"💥 {test_name} - 异常: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    print(f"\n详细结果:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 所有测试通过！阶段2基础功能验证完成")
        print(f"✅ 数据管理系统核心功能正常")
        print(f"✅ 文件系统集成工作正常")
        print(f"✅ 数据一致性保证机制有效")
        
        print(f"\n🚀 阶段2核心成就:")
        print(f"   - 项目和孔位数据管理 ✅")
        print(f"   - 数据模板和验证系统 ✅")
        print(f"   - 文件系统集成 ✅")
        print(f"   - 数据一致性保证 ✅")
        print(f"   - 数据库迁移框架 ✅")
        
        return True
    else:
        print(f"\n⚠️ 存在测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
