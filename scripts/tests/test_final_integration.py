#!/usr/bin/env python3
"""
最终集成测试
验证所有修复都已正确实施并工作正常
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_all_error_fixes():
    """测试所有错误修复"""
    print("🔍 测试所有错误修复...")
    
    # 测试 HoleCollection.get_statistics
    try:
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        holes = {}
        for i in range(3):
            hole = HoleData(
                hole_id=f"TEST{i:03d}",
                center_x=i * 10.0,
                center_y=i * 20.0,
                radius=8.8,
                status=HoleStatus.QUALIFIED if i > 0 else HoleStatus.PENDING
            )
            holes[hole.hole_id] = hole
        
        collection = HoleCollection(holes=holes)
        stats = collection.get_statistics()
        print(f"    ✅ HoleCollection.get_statistics: {stats}")
        
    except Exception as e:
        print(f"    ❌ HoleCollection.get_statistics 失败: {e}")
        return False
    
    # 测试 StatusManager.update_status
    try:
        from src.core_business.models.status_manager import StatusManager
        
        status_manager = StatusManager()
        result = status_manager.update_status("TEST001", "qualified")
        print(f"    ✅ StatusManager.update_status: {result}")
        
    except Exception as e:
        print(f"    ❌ StatusManager.update_status 失败: {e}")
        return False
    
    return True

def test_mock_batch_system():
    """测试模拟批次系统"""
    print("🔍 测试模拟批次系统...")
    
    try:
        from src.domain.services.batch_service import BatchService
        from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
        from src.domain.models.detection_batch import DetectionType
        
        repository = BatchRepositoryImpl()
        batch_service = BatchService(repository)
        
        batch = batch_service.create_batch(
            product_id=99,
            product_name="FINAL_TEST",
            operator="test_user",
            is_mock=True
        )
        
        if batch and batch.detection_type == DetectionType.MOCK and "_MOCK" in batch.batch_id:
            print(f"    ✅ 模拟批次系统正常: {batch.batch_id}")
            return True
        else:
            print("    ❌ 模拟批次系统异常")
            return False
            
    except Exception as e:
        print(f"    ❌ 模拟批次系统失败: {e}")
        return False

def test_path_management():
    """测试路径管理"""
    print("🔍 测试路径管理...")
    
    try:
        from src.models.data_path_manager import DataPathManager
        
        path_manager = DataPathManager()
        
        # 测试获取产品路径
        product_path = path_manager.get_product_path("TEST_PRODUCT")
        print(f"    ✅ 产品路径: {product_path}")
        
        # 测试获取批次路径
        batch_path = path_manager.get_inspection_batch_path("TEST_PRODUCT", "TEST_BATCH")
        print(f"    ✅ 批次路径: {batch_path}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 路径管理失败: {e}")
        return False

def test_business_service_integration():
    """测试业务服务集成"""
    print("🔍 测试业务服务集成...")
    
    try:
        from src.services.business_service import BusinessService
        
        business_service = BusinessService()
        
        # 测试状态管理器
        status_manager = business_service.status_manager
        if hasattr(status_manager, 'update_status'):
            result = business_service.update_hole_status("TEST_HOLE", "qualified")
            print(f"    ✅ 业务服务状态更新: {result}")
        else:
            print("    ❌ 业务服务缺少update_status方法")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 业务服务集成失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始最终集成测试...")
    print("=" * 60)
    
    tests = [
        ("错误修复", test_all_error_fixes),
        ("模拟批次系统", test_mock_batch_system),
        ("路径管理", test_path_management),
        ("业务服务集成", test_business_service_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 最终测试结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有修复和集成测试全部通过！")
        print("🔧 已完成的修复:")
        print("   • HoleCollection.get_statistics 方法")
        print("   • StatusManager.update_status 方法")
        print("   • 模拟检测统一批次管理") 
        print("   • 产品信息格式兼容性")
        print("   • 路径管理和目录创建")
        print("   • 业务服务集成")
        print("\n💡 建议重启应用测试完整功能")
    else:
        print("\n⚠️ 部分测试需要进一步检查")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)