#!/usr/bin/env python3
"""
测试统计信息同步问题修复
验证控制器和HoleCollection的统计信息一致性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_statistics_consistency():
    """测试统计信息一致性"""
    print("🔍 测试统计信息一致性...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        
        # 创建测试孔位数据
        holes = {}
        test_statuses = [
            HoleStatus.QUALIFIED,    # 2个
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,    # 2个  
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,        # 1个
            HoleStatus.TIE_ROD,      # 1个
            HoleStatus.PROCESSING,   # 1个
            HoleStatus.PENDING,      # 3个
            HoleStatus.PENDING,
            HoleStatus.PENDING
        ]
        
        for i, status in enumerate(test_statuses):
            hole = HoleData(
                hole_id=f"TEST_{i:03d}",
                center_x=i * 10.0,
                center_y=i * 15.0,
                radius=8.0,
                status=status
            )
            holes[hole.hole_id] = hole
        
        collection = HoleCollection(holes=holes)
        
        # 测试HoleCollection的统计
        collection_stats = collection.get_statistics()
        print(f"    📊 HoleCollection统计: {collection_stats}")
        
        # 创建控制器并设置孔位集合
        controller = MainWindowController()
        controller.hole_collection = collection
        
        # 测试控制器的统计
        controller_stats = controller.get_statistics()
        print(f"    📊 Controller统计: {controller_stats}")
        
        # 验证一致性
        if collection_stats == controller_stats:
            print("    ✅ 统计信息完全一致")
            return True
        else:
            print("    ❌ 统计信息不一致")
            print(f"    差异: Collection={collection_stats}")
            print(f"         Controller={controller_stats}")
            
            # 检查具体差异
            for key in collection_stats:
                if collection_stats[key] != controller_stats.get(key, 0):
                    print(f"    🔍 {key}: Collection={collection_stats[key]}, Controller={controller_stats.get(key, 0)}")
            
            return False
        
    except Exception as e:
        print(f"    ❌ 统计信息一致性测试失败: {e}")
        return False

def test_status_update_sync():
    """测试状态更新后的统计同步"""
    print("🔍 测试状态更新后的统计同步...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        
        # 创建初始孔位（全部为PENDING）
        holes = {}
        for i in range(5):
            hole = HoleData(
                hole_id=f"SYNC_{i:03d}",
                center_x=i * 10.0,
                center_y=i * 15.0,
                radius=8.0,
                status=HoleStatus.PENDING
            )
            holes[hole.hole_id] = hole
        
        collection = HoleCollection(holes=holes)
        controller = MainWindowController()
        controller.hole_collection = collection
        
        # 初始统计
        initial_stats = controller.get_statistics()
        print(f"    📊 初始统计: {initial_stats}")
        
        if initial_stats['pending'] != 5:
            print(f"    ❌ 初始pending数量错误: {initial_stats['pending']} != 5")
            return False
        
        # 更新孔位状态
        test_updates = [
            ("SYNC_000", HoleStatus.QUALIFIED),
            ("SYNC_001", HoleStatus.DEFECTIVE),
            ("SYNC_002", HoleStatus.BLIND)
        ]
        
        for hole_id, new_status in test_updates:
            # 更新孔位状态
            if hole_id in collection.holes:
                collection.holes[hole_id].status = new_status
                print(f"    🔄 更新 {hole_id} -> {new_status.value}")
        
        # 获取更新后的统计
        updated_stats = controller.get_statistics()
        print(f"    📊 更新后统计: {updated_stats}")
        
        # 验证更新结果
        expected = {
            'total_holes': 5,
            'qualified': 1,
            'defective': 1,
            'blind': 1,
            'pending': 2,
            'tie_rod': 0,
            'processing': 0
        }
        
        if updated_stats == expected:
            print("    ✅ 状态更新后统计正确")
            return True
        else:
            print("    ❌ 状态更新后统计错误")
            print(f"    期望: {expected}")
            print(f"    实际: {updated_stats}")
            return False
        
    except Exception as e:
        print(f"    ❌ 状态更新同步测试失败: {e}")
        return False

def test_empty_collection_handling():
    """测试空集合处理"""
    print("🔍 测试空集合处理...")
    
    try:
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        
        controller = MainWindowController()
        controller.hole_collection = None
        
        stats = controller.get_statistics()
        print(f"    📊 空集合统计: {stats}")
        
        expected = {
            'total_holes': 0,
            'qualified': 0,
            'defective': 0,
            'blind': 0,
            'pending': 0,
            'tie_rod': 0,
            'processing': 0
        }
        
        if stats == expected:
            print("    ✅ 空集合处理正确")
            return True
        else:
            print("    ❌ 空集合处理错误")
            return False
        
    except Exception as e:
        print(f"    ❌ 空集合处理测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 测试统计信息同步修复...")
    print("=" * 60)
    
    tests = [
        ("统计信息一致性测试", test_statistics_consistency),
        ("状态更新同步测试", test_status_update_sync),
        ("空集合处理测试", test_empty_collection_handling)
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
    print("📊 统计信息同步修复验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 ✨ 统计信息同步问题已修复！ ✨")
        print("\n🔧 修复内容:")
        print("   ✅ 控制器get_statistics()现在直接使用HoleCollection.get_statistics()")
        print("   ✅ 确保了统计信息的一致性和实时性")
        print("   ✅ 包含了所有状态类型(qualified, defective, blind, pending, tie_rod, processing)")
        print("   ✅ 添加了空集合的安全处理")
        print("\n💡 现在状态更新应该能正确反映在统计信息中了")
    else:
        failed_tests = [name for name, status in results if status != "PASS"]
        print(f"\n⚠️ 需要进一步检查: {failed_tests}")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)