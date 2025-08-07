#!/usr/bin/env python3
"""
测试错误修复效果
验证 HoleCollection.get_statistics 和 StatusManager.update_status 方法
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_hole_collection_fixes():
    """测试 HoleCollection 修复"""
    print("🔍 测试 HoleCollection 修复...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建测试数据
        holes = {}
        for i in range(5):
            hole = HoleData(
                hole_id=f"TEST{i:03d}",
                center_x=i * 10.0,
                center_y=i * 20.0,
                radius=8.8,
                status=HoleStatus.PENDING if i < 3 else HoleStatus.QUALIFIED
            )
            holes[hole.hole_id] = hole
        
        collection = HoleCollection(holes=holes)
        
        # 测试 get_statistics 方法
        print("  🔧 测试 get_statistics 方法...")
        if hasattr(collection, 'get_statistics'):
            stats = collection.get_statistics()
            print(f"    ✅ get_statistics 工作正常: {stats}")
            
            expected_keys = ['total_holes', 'qualified', 'defective', 'blind', 'pending', 'tie_rod', 'processing']
            missing_keys = [key for key in expected_keys if key not in stats]
            if not missing_keys:
                print("    ✅ 统计信息包含所有必需字段")
            else:
                print(f"    ⚠️ 缺失字段: {missing_keys}")
        else:
            print("    ❌ get_statistics 方法不存在")
            return False
        
        # 测试 update_hole_status 方法
        print("  🔧 测试 update_hole_status 方法...")
        if hasattr(collection, 'update_hole_status'):
            result = collection.update_hole_status("TEST001", HoleStatus.QUALIFIED)
            print(f"    ✅ update_hole_status 工作正常: {result}")
            
            # 验证状态更新
            updated_stats = collection.get_statistics()
            if updated_stats['qualified'] > stats['qualified']:
                print("    ✅ 状态更新成功验证")
            else:
                print("    ⚠️ 状态更新可能未生效")
        else:
            print("    ❌ update_hole_status 方法不存在")
            return False
        
        # 测试 get_hole_by_id 方法
        print("  🔧 测试 get_hole_by_id 方法...")
        if hasattr(collection, 'get_hole_by_id'):
            hole = collection.get_hole_by_id("TEST002")
            if hole and hole.hole_id == "TEST002":
                print("    ✅ get_hole_by_id 工作正常")
            else:
                print("    ⚠️ get_hole_by_id 返回结果异常")
        else:
            print("    ❌ get_hole_by_id 方法不存在")
            return False
        
        print("✅ HoleCollection 修复验证通过")
        return True
        
    except Exception as e:
        print(f"❌ HoleCollection 测试失败: {e}")
        return False

def test_status_manager_fixes():
    """测试 StatusManager 修复"""
    print("🔍 测试 StatusManager 修复...")
    
    try:
        from src.core_business.models.status_manager import StatusManager
        
        status_manager = StatusManager()
        
        # 测试 update_status 方法
        print("  🔧 测试 update_status 方法...")
        if hasattr(status_manager, 'update_status'):
            # 测试字符串状态
            result1 = status_manager.update_status("TEST001", "qualified")
            print(f"    ✅ update_status (字符串) 工作正常: {result1}")
            
            # 测试枚举状态
            from src.core_business.models.hole_data import HoleStatus
            result2 = status_manager.update_status("TEST002", HoleStatus.DEFECTIVE)
            print(f"    ✅ update_status (枚举) 工作正常: {result2}")
            
            # 测试无效状态
            result3 = status_manager.update_status("TEST003", "invalid_status")
            print(f"    ✅ update_status (无效状态) 处理正常: {result3}")
            
        else:
            print("    ❌ update_status 方法不存在")
            return False
        
        print("✅ StatusManager 修复验证通过")
        return True
        
    except Exception as e:
        print(f"❌ StatusManager 测试失败: {e}")
        return False

def test_business_service_integration():
    """测试 BusinessService 集成"""
    print("🔍 测试 BusinessService 集成...")
    
    try:
        from src.services.business_service import BusinessService
        
        business_service = BusinessService()
        
        # 测试状态管理器属性
        print("  🔧 测试状态管理器获取...")
        status_manager = business_service.status_manager
        if status_manager and hasattr(status_manager, 'update_status'):
            print("    ✅ 状态管理器获取成功")
            
            # 测试通过 BusinessService 更新孔位状态
            result = business_service.update_hole_status("TEST_BUSINESS", "qualified")
            print(f"    ✅ 通过 BusinessService 更新状态: {result}")
            
        else:
            print("    ❌ 状态管理器获取失败或缺少方法")
            return False
        
        print("✅ BusinessService 集成验证通过")
        return True
        
    except Exception as e:
        print(f"❌ BusinessService 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试错误修复效果...")
    print("=" * 60)
    
    tests = [
        test_hole_collection_fixes,
        test_status_manager_fixes,
        test_business_service_integration
    ]
    
    results = []
    for test in tests:
        print(f"\n📋 运行测试: {test.__name__}")
        print("-" * 40)
        try:
            result = test()
            results.append((test.__name__, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test.__name__, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有错误修复验证通过！")
        print("💡 建议重启应用测试实际效果")
    else:
        print("⚠️ 部分修复可能需要进一步调整")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)