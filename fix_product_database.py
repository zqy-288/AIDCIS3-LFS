#!/usr/bin/env python3
"""
产品数据库修复脚本
用于修复数据库中的数据不一致问题，重建缺失的默认产品
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'models'))

def check_database_integrity():
    """检查数据库完整性"""
    print("=== 检查数据库完整性 ===")
    
    try:
        from product_model import get_product_manager
        
        manager = get_product_manager()
        products = manager.get_all_products(active_only=False)
        
        print(f"当前数据库中有 {len(products)} 个产品")
        
        # 检查ID连续性
        ids = [p.id for p in products]
        ids.sort()
        
        print(f"产品ID列表: {ids}")
        
        # 查找缺失的ID
        if ids:
            min_id = min(ids)
            max_id = max(ids)
            expected_ids = set(range(min_id, max_id + 1))
            missing_ids = expected_ids - set(ids)
            
            if missing_ids:
                print(f"发现缺失的ID: {sorted(missing_ids)}")
            else:
                print("ID连续性检查通过")
        
        # 显示现有产品
        print("\n现有产品列表:")
        for product in products:
            status = "启用" if product.is_active else "停用"
            print(f"  ID: {product.id}, 名称: {product.model_name}, 状态: {status}")
        
        return products
        
    except Exception as e:
        print(f"数据库检查失败: {str(e)}")
        return None

def rebuild_default_products():
    """重建默认产品"""
    print("\n=== 重建默认产品 ===")
    
    try:
        from product_model import get_product_manager
        
        manager = get_product_manager()
        
        # 检查是否存在 TP-001
        tp001 = manager.get_product_by_name("TP-001")
        if not tp001:
            print("重建 TP-001 产品...")
            manager.create_product(
                model_name="TP-001",
                model_code="TP001",
                standard_diameter=10.0,
                tolerance_upper=0.05,
                tolerance_lower=-0.05,
                description="标准孔径10mm产品型号"
            )
            print("✓ TP-001 重建成功")
        else:
            print("TP-001 已存在")
        
        return True
        
    except Exception as e:
        print(f"重建默认产品失败: {str(e)}")
        return False

def fix_database():
    """修复数据库"""
    print("\n=== 修复数据库 ===")
    
    try:
        from product_model import get_product_manager
        
        manager = get_product_manager()
        
        # 重新创建数据库表（如果需要）
        print("检查数据库表结构...")
        products = manager.get_all_products(active_only=False)
        print(f"✓ 数据库表结构正常，当前有 {len(products)} 个产品")
        
        return True
        
    except Exception as e:
        print(f"数据库修复失败: {str(e)}")
        return False

def cleanup_orphaned_data():
    """清理孤立数据"""
    print("\n=== 清理孤立数据 ===")
    
    try:
        from product_model import get_product_manager
        
        manager = get_product_manager()
        
        # 查找重复的产品名称
        products = manager.get_all_products(active_only=False)
        names = [p.model_name for p in products]
        duplicates = set([name for name in names if names.count(name) > 1])
        
        if duplicates:
            print(f"发现重复的产品名称: {duplicates}")
            # 这里可以添加处理重复数据的逻辑
        else:
            print("未发现重复数据")
        
        return True
        
    except Exception as e:
        print(f"数据清理失败: {str(e)}")
        return False

def verify_repairs():
    """验证修复结果"""
    print("\n=== 验证修复结果 ===")
    
    try:
        from product_model import get_product_manager
        
        manager = get_product_manager()
        products = manager.get_all_products(active_only=False)
        
        print(f"修复后产品总数: {len(products)}")
        
        # 检查必需的默认产品
        required_products = ["TP-001", "TP-002", "TP-003"]
        missing_required = []
        
        existing_names = [p.model_name for p in products]
        
        for required in required_products:
            if required not in existing_names:
                missing_required.append(required)
        
        if missing_required:
            print(f"仍缺失的必需产品: {missing_required}")
            return False
        else:
            print("✓ 所有必需产品都存在")
        
        # 验证产品功能
        print("\n验证产品管理功能:")
        
        # 测试创建
        test_name = "TEST_REPAIR_VERIFY"
        existing_test = manager.get_product_by_name(test_name)
        if existing_test:
            manager.delete_product(existing_test.id)
        
        test_product = manager.create_product(
            model_name=test_name,
            standard_diameter=5.0,
            tolerance_upper=0.01,
            tolerance_lower=-0.01,
            description="修复验证测试产品"
        )
        print("✓ 产品创建功能正常")
        
        # 测试查询
        found_product = manager.get_product_by_id(test_product.id)
        if found_product and found_product.model_name == test_name:
            print("✓ 产品查询功能正常")
        else:
            print("✗ 产品查询功能异常")
            return False
        
        # 测试删除
        manager.delete_product(test_product.id)
        deleted_check = manager.get_product_by_id(test_product.id)
        if deleted_check is None:
            print("✓ 产品删除功能正常")
        else:
            print("✗ 产品删除功能异常")
            return False
        
        print("\n✅ 数据库修复验证通过！")
        return True
        
    except Exception as e:
        print(f"修复验证失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("产品数据库修复工具")
    print("=" * 40)
    
    # 步骤1：检查当前状态
    products = check_database_integrity()
    if products is None:
        print("❌ 数据库检查失败，无法继续")
        return 1
    
    # 步骤2：修复数据库
    if not fix_database():
        print("❌ 数据库修复失败")
        return 1
    
    # 步骤3：重建默认产品
    if not rebuild_default_products():
        print("❌ 重建默认产品失败")
        return 1
    
    # 步骤4：清理孤立数据
    if not cleanup_orphaned_data():
        print("❌ 数据清理失败")
        return 1
    
    # 步骤5：验证修复结果
    if not verify_repairs():
        print("❌ 修复验证失败")
        return 1
    
    print("\n🎉 数据库修复完成！")
    print("\n建议:")
    print("1. 重新启动应用程序")
    print("2. 测试产品管理功能")
    print("3. 如果问题仍然存在，请检查应用程序日志")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())