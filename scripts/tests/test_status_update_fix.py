#!/usr/bin/env python3
"""
测试状态更新修复
验证StatusManager实际更新HoleCollection中的孔位状态
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_status_manager_actual_update():
    """测试StatusManager实际更新孔位状态"""
    print("🔍 测试StatusManager实际更新孔位状态...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.core_business.models.status_manager import StatusManager
        from src.core.shared_data_manager import SharedDataManager
        
        # 创建测试孔位
        holes = {}
        test_holes = [
            ("TEST_001", HoleStatus.PENDING),
            ("TEST_002", HoleStatus.PENDING),
            ("TEST_003", HoleStatus.PENDING)
        ]
        
        for hole_id, status in test_holes:
            hole = HoleData(
                hole_id=hole_id,
                center_x=10.0,
                center_y=20.0,
                radius=8.0,
                status=status
            )
            holes[hole_id] = hole
        
        # 创建孔位集合
        collection = HoleCollection(holes=holes)
        
        # 设置到共享数据管理器
        shared_data = SharedDataManager()
        shared_data.set_hole_collection(collection)
        
        # 创建状态管理器
        status_manager = StatusManager()
        
        # 测试初始统计
        initial_stats = collection.get_statistics()
        print(f"    📊 初始统计: {initial_stats}")
        
        if initial_stats['pending'] != 3:
            print(f"    ❌ 初始pending计数错误: {initial_stats['pending']} != 3")
            return False
        
        # 更新孔位状态
        test_updates = [
            ("TEST_001", "qualified"),
            ("TEST_002", "defective"),
            ("TEST_003", "blind")
        ]
        
        for hole_id, new_status in test_updates:
            print(f"    🔄 更新 {hole_id} -> {new_status}")
            result = status_manager.update_status(hole_id, new_status, "测试更新")
            
            if not result:
                print(f"    ❌ 状态更新失败: {hole_id}")
                return False
            
            # 验证孔位实际状态是否更新
            actual_status = collection.holes[hole_id].status
            expected_status = {
                'qualified': HoleStatus.QUALIFIED,
                'defective': HoleStatus.DEFECTIVE,
                'blind': HoleStatus.BLIND
            }[new_status]
            
            if actual_status == expected_status:
                print(f"    ✅ {hole_id} 状态实际更新: {actual_status.value}")
            else:
                print(f"    ❌ {hole_id} 状态未实际更新: {actual_status.value} != {expected_status.value}")
                return False
        
        # 测试更新后的统计
        final_stats = collection.get_statistics()
        print(f"    📊 最终统计: {final_stats}")
        
        expected_final = {
            'total_holes': 3,
            'qualified': 1,
            'defective': 1,
            'blind': 1,
            'pending': 0,
            'tie_rod': 0,
            'processing': 0
        }
        
        if final_stats == expected_final:
            print("    ✅ 统计信息正确反映状态更新")
            return True
        else:
            print(f"    ❌ 统计信息不正确")
            print(f"    期望: {expected_final}")
            print(f"    实际: {final_stats}")
            return False
        
    except Exception as e:
        print(f"    ❌ StatusManager实际更新测试失败: {e}")
        return False

def test_status_manager_with_collection():
    """测试StatusManager直接关联HoleCollection"""
    print("🔍 测试StatusManager直接关联HoleCollection...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.core_business.models.status_manager import StatusManager
        
        # 创建测试孔位
        holes = {}
        for i in range(5):
            hole = HoleData(
                hole_id=f"DIRECT_{i:03d}",
                center_x=i * 10.0,
                center_y=i * 15.0,
                radius=8.0,
                status=HoleStatus.PENDING
            )
            holes[hole.hole_id] = hole
        
        # 创建孔位集合
        collection = HoleCollection(holes=holes)
        
        # 创建状态管理器并直接关联孔位集合
        status_manager = StatusManager()
        status_manager.hole_collection = collection
        
        # 测试更新
        update_result = status_manager.update_status("DIRECT_000", HoleStatus.QUALIFIED, "直接关联测试")
        
        if update_result:
            # 检查实际状态
            actual_status = collection.holes["DIRECT_000"].status
            if actual_status == HoleStatus.QUALIFIED:
                print("    ✅ 直接关联孔位集合更新成功")
                
                # 检查统计
                stats = collection.get_statistics()
                print(f"    📊 更新后统计: {stats}")
                
                if stats['qualified'] == 1 and stats['pending'] == 4:
                    print("    ✅ 统计信息正确")
                    return True
                else:
                    print("    ❌ 统计信息错误")
                    return False
            else:
                print(f"    ❌ 状态未实际更新: {actual_status.value}")
                return False
        else:
            print("    ❌ 状态更新失败")
            return False
        
    except Exception as e:
        print(f"    ❌ 直接关联测试失败: {e}")
        return False

def test_controller_statistics_integration():
    """测试控制器统计信息集成"""
    print("🔍 测试控制器统计信息集成...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.core_business.models.status_manager import StatusManager
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        
        # 创建测试数据
        holes = {}
        for i in range(3):
            hole = HoleData(
                hole_id=f"CTRL_{i:03d}",
                center_x=i * 10.0,
                center_y=i * 15.0,
                radius=8.0,
                status=HoleStatus.PENDING
            )
            holes[hole.hole_id] = hole
        
        collection = HoleCollection(holes=holes)
        
        # 创建控制器并设置孔位集合
        controller = MainWindowController()
        controller.hole_collection = collection
        
        # 创建状态管理器并关联孔位集合
        status_manager = StatusManager()
        status_manager.hole_collection = collection
        
        # 测试初始统计
        initial_stats = controller.get_statistics()
        print(f"    📊 控制器初始统计: {initial_stats}")
        
        # 更新状态
        status_manager.update_status("CTRL_000", HoleStatus.QUALIFIED, "集成测试")
        status_manager.update_status("CTRL_001", HoleStatus.DEFECTIVE, "集成测试")
        
        # 测试更新后统计
        final_stats = controller.get_statistics()
        print(f"    📊 控制器最终统计: {final_stats}")
        
        # 验证统计
        if final_stats['qualified'] == 1 and final_stats['defective'] == 1 and final_stats['pending'] == 1:
            print("    ✅ 控制器统计信息正确反映状态更新")
            return True
        else:
            print("    ❌ 控制器统计信息不正确")
            return False
        
    except Exception as e:
        print(f"    ❌ 控制器统计集成测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 测试状态更新修复...")
    print("=" * 60)
    
    tests = [
        ("StatusManager实际更新测试", test_status_manager_actual_update),
        ("StatusManager直接关联测试", test_status_manager_with_collection),
        ("控制器统计信息集成测试", test_controller_statistics_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 状态更新修复验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 ✨ 状态更新问题已彻底修复！ ✨")
        print("\n🔧 修复内容:")
        print("   ✅ StatusManager.update_status()现在实际更新HoleCollection中的孔位状态")
        print("   ✅ 支持通过hole_collection属性直接关联")
        print("   ✅ 支持通过SharedDataManager获取孔位集合")
        print("   ✅ 确保统计信息能正确反映状态变更")
        print("\n💡 现在孔位状态更新应该能正确反映在统计信息中了")
    else:
        failed_tests = [name for name, status in results if status != "PASS"]
        print(f"\n⚠️ 需要进一步检查: {failed_tests}")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)