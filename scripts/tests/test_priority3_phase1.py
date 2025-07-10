#!/usr/bin/env python3
"""
优先级3阶段1测试：基础架构
Test Priority 3 Phase 1: Basic Infrastructure
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入数据管理组件
from aidcis2.data_management.project_manager import ProjectDataManager
from aidcis2.data_management.hole_manager import HoleDataManager
from aidcis2.data_management.data_templates import DataTemplates, DataValidator


def test_project_manager():
    """测试项目数据管理器"""
    
    print("\n🔧 测试1：ProjectDataManager")
    print("-" * 40)
    
    # 创建临时目录用于测试
    with tempfile.TemporaryDirectory() as temp_dir:
        # 初始化项目管理器
        project_manager = ProjectDataManager(temp_dir)
        
        # 测试1.1：创建项目
        print("   📝 测试1.1：创建项目")
        dxf_file = "test_drawing.dxf"
        project_name = "测试项目"
        
        # 创建临时DXF文件
        temp_dxf = Path(temp_dir) / dxf_file
        temp_dxf.write_text("dummy dxf content")
        
        project_id, project_path = project_manager.create_project(str(temp_dxf), project_name)
        
        assert project_id.startswith("project_test_drawing_")
        assert Path(project_path).exists()
        print(f"      ✅ 项目创建成功: {project_id}")
        
        # 测试1.2：获取项目路径
        print("   📝 测试1.2：获取项目路径")
        retrieved_path = project_manager.get_project_path(project_id)
        assert retrieved_path == project_path
        print(f"      ✅ 项目路径获取成功: {retrieved_path}")
        
        # 测试1.3：获取项目元数据
        print("   📝 测试1.3：获取项目元数据")
        metadata = project_manager.get_project_metadata(project_id)
        assert metadata is not None
        assert metadata["project_name"] == project_name
        print(f"      ✅ 元数据获取成功: {metadata['project_name']}")
        
        # 测试1.4：更新项目元数据
        print("   📝 测试1.4：更新项目元数据")
        updates = {"total_holes": 100, "description": "测试项目描述"}
        success = project_manager.update_project_metadata(project_id, updates)
        assert success
        
        updated_metadata = project_manager.get_project_metadata(project_id)
        assert updated_metadata["total_holes"] == 100
        print(f"      ✅ 元数据更新成功: total_holes={updated_metadata['total_holes']}")
        
        # 测试1.5：列出项目
        print("   📝 测试1.5：列出项目")
        projects = project_manager.list_projects()
        assert len(projects) == 1
        assert projects[0]["project_id"] == project_id
        print(f"      ✅ 项目列表获取成功: {len(projects)} 个项目")
        
        # 测试1.6：获取项目统计
        print("   📝 测试1.6：获取项目统计")
        stats = project_manager.get_project_statistics(project_id)
        assert "total_holes" in stats
        print(f"      ✅ 项目统计获取成功: {stats}")
        
        print("   🎉 ProjectDataManager测试全部通过")


def test_hole_manager():
    """测试孔位数据管理器"""
    
    print("\n🔧 测试2：HoleDataManager")
    print("-" * 40)
    
    # 创建临时目录用于测试
    with tempfile.TemporaryDirectory() as temp_dir:
        # 初始化管理器
        project_manager = ProjectDataManager(temp_dir)
        hole_manager = HoleDataManager(project_manager)
        
        # 先创建一个项目
        dxf_file = "test_drawing.dxf"
        temp_dxf = Path(temp_dir) / dxf_file
        temp_dxf.write_text("dummy dxf content")
        
        project_id, _ = project_manager.create_project(str(temp_dxf), "测试项目")
        
        # 测试2.1：创建孔位目录
        print("   📝 测试2.1：创建孔位目录")
        hole_id = "H00001"
        hole_info = {
            "hole_id": hole_id,
            "position": {"x": 10.0, "y": 20.0},
            "diameter": 8.865,
            "depth": 900.0
        }
        
        success = hole_manager.create_hole_directory(project_id, hole_id, hole_info)
        assert success
        
        hole_path = hole_manager.get_hole_path(project_id, hole_id)
        assert hole_path is not None
        assert Path(hole_path).exists()
        print(f"      ✅ 孔位目录创建成功: {hole_path}")
        
        # 验证目录结构
        bisdm_dir = Path(hole_path) / "BISDM"
        ccidm_dir = Path(hole_path) / "CCIDM"
        assert bisdm_dir.exists()
        assert ccidm_dir.exists()
        print(f"      ✅ 目录结构正确: BISDM + CCIDM")
        
        # 测试2.2：保存和获取孔位信息
        print("   📝 测试2.2：保存和获取孔位信息")
        retrieved_info = hole_manager.get_hole_info(project_id, hole_id)
        assert retrieved_info is not None
        assert retrieved_info["hole_id"] == hole_id
        assert retrieved_info["position"]["x"] == 10.0
        print(f"      ✅ 孔位信息保存和获取成功")
        
        # 测试2.3：保存和获取孔位状态
        print("   📝 测试2.3：保存和获取孔位状态")
        status_data = hole_manager.get_hole_status(project_id, hole_id)
        assert status_data is not None
        assert status_data["current_status"] == "pending"
        print(f"      ✅ 孔位状态保存和获取成功")
        
        # 测试2.4：更新孔位状态
        print("   📝 测试2.4：更新孔位状态")
        success = hole_manager.update_hole_status(project_id, hole_id, "in_progress", "开始测量")
        assert success
        
        updated_status = hole_manager.get_hole_status(project_id, hole_id)
        assert updated_status["current_status"] == "in_progress"
        assert len(updated_status["status_history"]) == 2
        print(f"      ✅ 孔位状态更新成功")
        
        # 测试2.5：保存测量数据
        print("   📝 测试2.5：保存测量数据")
        measurement_data = [
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865},
            {"timestamp": "2025-01-08T10:00:01", "depth": 1.0, "diameter": 8.870},
            {"timestamp": "2025-01-08T10:00:02", "depth": 2.0, "diameter": 8.860}
        ]
        
        success = hole_manager.save_measurement_data(project_id, hole_id, measurement_data)
        assert success
        
        # 测试2.6：获取测量数据文件
        print("   📝 测试2.6：获取测量数据文件")
        csv_files = hole_manager.get_hole_measurements(project_id, hole_id)
        assert len(csv_files) == 1
        print(f"      ✅ 测量数据文件获取成功: {len(csv_files)} 个文件")
        
        # 测试2.7：加载测量数据
        print("   📝 测试2.7：加载测量数据")
        data = hole_manager.load_measurement_data(csv_files[0])
        assert data is not None
        assert len(data) == 3
        assert "depth" in data[0]
        assert "diameter" in data[0]
        print(f"      ✅ 测量数据加载成功: {len(data)} 条记录")
        
        print("   🎉 HoleDataManager测试全部通过")


def test_data_templates():
    """测试数据模板和验证"""
    
    print("\n🔧 测试3：DataTemplates & DataValidator")
    print("-" * 40)
    
    # 测试3.1：项目元数据模板
    print("   📝 测试3.1：项目元数据模板")
    metadata = DataTemplates.create_project_metadata_template(
        "test_project", "测试项目", "test.dxf", 100
    )
    assert metadata["project_id"] == "test_project"
    assert metadata["total_holes"] == 100
    print(f"      ✅ 项目元数据模板创建成功")
    
    # 测试3.2：孔位信息模板
    print("   📝 测试3.2：孔位信息模板")
    hole_info = DataTemplates.create_hole_info_template(
        "H00001", {"x": 10.0, "y": 20.0}
    )
    assert hole_info["hole_id"] == "H00001"
    assert hole_info["position"]["x"] == 10.0
    print(f"      ✅ 孔位信息模板创建成功")
    
    # 测试3.3：孔位状态模板
    print("   📝 测试3.3：孔位状态模板")
    status = DataTemplates.create_hole_status_template()
    assert status["current_status"] == "pending"
    assert len(status["status_history"]) == 1
    print(f"      ✅ 孔位状态模板创建成功")
    
    # 测试3.4：数据验证
    print("   📝 测试3.4：数据验证")
    validator = DataValidator()
    
    # 验证项目元数据
    is_valid, errors = validator.validate_project_metadata(metadata)
    assert is_valid
    assert len(errors) == 0
    print(f"      ✅ 项目元数据验证通过")
    
    # 验证孔位信息
    is_valid, errors = validator.validate_hole_info(hole_info)
    assert is_valid
    assert len(errors) == 0
    print(f"      ✅ 孔位信息验证通过")
    
    # 验证孔位状态
    is_valid, errors = validator.validate_hole_status(status)
    assert is_valid
    assert len(errors) == 0
    print(f"      ✅ 孔位状态验证通过")
    
    # 测试3.5：无效数据验证
    print("   📝 测试3.5：无效数据验证")
    invalid_metadata = {"project_id": "test"}  # 缺少必需字段
    is_valid, errors = validator.validate_project_metadata(invalid_metadata)
    assert not is_valid
    assert len(errors) > 0
    print(f"      ✅ 无效数据验证正确: {len(errors)} 个错误")
    
    print("   🎉 DataTemplates & DataValidator测试全部通过")


def test_integration():
    """集成测试"""
    
    print("\n🔧 测试4：集成测试")
    print("-" * 40)
    
    # 创建临时目录用于测试
    with tempfile.TemporaryDirectory() as temp_dir:
        # 初始化所有组件
        project_manager = ProjectDataManager(temp_dir)
        hole_manager = HoleDataManager(project_manager)
        validator = DataValidator()
        
        # 测试4.1：完整的项目创建流程
        print("   📝 测试4.1：完整的项目创建流程")
        
        # 创建项目
        dxf_file = "integration_test.dxf"
        temp_dxf = Path(temp_dir) / dxf_file
        temp_dxf.write_text("dummy dxf content")
        
        project_id, project_path = project_manager.create_project(str(temp_dxf), "集成测试项目")
        
        # 创建多个孔位
        holes = [
            {"hole_id": "H00001", "position": {"x": 10.0, "y": 20.0}},
            {"hole_id": "H00002", "position": {"x": 30.0, "y": 40.0}},
            {"hole_id": "H00003", "position": {"x": 50.0, "y": 60.0}}
        ]
        
        for hole_data in holes:
            hole_info = DataTemplates.create_hole_info_template(
                hole_data["hole_id"], hole_data["position"]
            )
            
            # 验证数据
            is_valid, errors = validator.validate_hole_info(hole_info)
            assert is_valid, f"孔位信息验证失败: {errors}"
            
            # 创建孔位
            success = hole_manager.create_hole_directory(project_id, hole_data["hole_id"], hole_info)
            assert success, f"孔位创建失败: {hole_data['hole_id']}"
        
        print(f"      ✅ 创建了 {len(holes)} 个孔位")
        
        # 测试4.2：更新项目统计
        print("   📝 测试4.2：更新项目统计")
        project_manager.update_project_metadata(project_id, {"total_holes": len(holes)})
        
        stats = project_manager.get_project_statistics(project_id)
        assert stats["total_holes"] == len(holes)
        print(f"      ✅ 项目统计更新成功: {stats['total_holes']} 个孔位")
        
        # 测试4.3：模拟测量流程
        print("   📝 测试4.3：模拟测量流程")
        for hole_data in holes[:2]:  # 只测量前两个孔位
            hole_id = hole_data["hole_id"]
            
            # 开始测量
            hole_manager.update_hole_status(project_id, hole_id, "in_progress", "开始测量")
            
            # 保存测量数据
            measurement_data = [
                {"timestamp": "2025-01-08T10:00:00", "depth": i, "diameter": 8.865 + i * 0.001}
                for i in range(10)
            ]
            hole_manager.save_measurement_data(project_id, hole_id, measurement_data)
            
            # 完成测量
            hole_manager.update_hole_status(project_id, hole_id, "completed", "测量完成")
        
        print(f"      ✅ 完成了 2 个孔位的测量")
        
        # 测试4.4：验证最终状态
        print("   📝 测试4.4：验证最终状态")
        final_stats = project_manager.get_project_statistics(project_id)
        assert final_stats["completed_holes"] == 2
        assert final_stats["pending_holes"] == 1
        expected_rate = 2 / 3 * 100  # 66.67%
        assert abs(final_stats["completion_rate"] - expected_rate) < 0.1

        print(f"      ✅ 最终统计正确: 完成率 {final_stats['completion_rate']:.1f}%")
        
        print("   🎉 集成测试全部通过")


def main():
    """主函数"""
    
    print("=" * 80)
    print("🎯 优先级3阶段1测试：基础架构")
    print("=" * 80)
    
    try:
        # 运行所有测试
        test_project_manager()
        test_hole_manager()
        test_data_templates()
        test_integration()
        
        print("\n" + "=" * 80)
        print("🎉 阶段1测试全部通过！")
        print("=" * 80)
        
        print("\n✅ 测试结果总结：")
        print("   - ProjectDataManager: 6/6 测试通过")
        print("   - HoleDataManager: 7/7 测试通过")
        print("   - DataTemplates & DataValidator: 5/5 测试通过")
        print("   - 集成测试: 4/4 测试通过")
        print("   - 总计: 22/22 测试通过 (100%)")
        
        print("\n🚀 阶段1基础架构实现完成！")
        print("   - data/目录结构 ✅")
        print("   - ProjectDataManager类 ✅")
        print("   - HoleDataManager类 ✅")
        print("   - 数据模板和验证 ✅")
        
        print("\n📋 下一步：阶段2 - 数据库集成")
        print("   - 扩展workpieces表结构")
        print("   - 扩展holes表结构")
        print("   - 实现HybridDataManager类")
        print("   - 创建数据同步机制")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
