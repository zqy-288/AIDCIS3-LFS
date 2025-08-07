#!/usr/bin/env python3
"""
详细测试产品选择对话框的具体问题
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_product_dialog_data():
    """测试产品对话框的数据加载"""
    print("=== 详细测试产品选择对话框 ===")
    
    try:
        # 1. 测试产品管理器
        from src.shared.models.product_model import get_product_manager
        manager = get_product_manager()
        
        all_products = manager.get_all_products(active_only=False)
        active_products = manager.get_all_products(active_only=True)
        
        print(f"✅ 总产品数: {len(all_products)}")
        print(f"✅ 启用产品数: {len(active_products)}")
        
        for i, product in enumerate(active_products, 1):
            print(f"  {i}. {product.model_name} ({product.model_code or '无代码'})")
            print(f"     标准直径: {product.standard_diameter}mm")
            print(f"     公差范围: {product.tolerance_range}")
            print(f"     状态: {'启用' if product.is_active else '停用'}")
            print(f"     描述: {product.description or '无描述'}")
            print()
        
        # 2. 测试对话框数据加载
        from src.pages.main_detection_p1.modules.product_selection import ProductSelectionDialog
        
        print("=== 创建产品选择对话框 ===")
        
        # 创建一个最小化的应用程序
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建对话框
        dialog = ProductSelectionDialog()
        
        # 检查对话框的组件
        print(f"✅ 对话框创建成功")
        print(f"✅ 产品表格行数: {dialog.product_table.rowCount()}")
        print(f"✅ 产品表格列数: {dialog.product_table.columnCount()}")
        
        # 检查表格内容
        print("\n=== 表格内容检查 ===")
        for row in range(dialog.product_table.rowCount()):
            name_item = dialog.product_table.item(row, 0)
            diameter_item = dialog.product_table.item(row, 1)
            tolerance_item = dialog.product_table.item(row, 2)
            description_item = dialog.product_table.item(row, 3)
            status_item = dialog.product_table.item(row, 4)
            
            if name_item and diameter_item:
                product_data = name_item.data(0x0100)  # Qt.UserRole
                print(f"第{row+1}行:")
                print(f"  型号名称: {name_item.text()}")
                print(f"  标准直径: {diameter_item.text()}")
                print(f"  公差范围: {tolerance_item.text() if tolerance_item else 'N/A'}")
                print(f"  描述: {description_item.text() if description_item else 'N/A'}")
                print(f"  状态: {status_item.text() if status_item else 'N/A'}")
                print(f"  关联产品对象: {product_data is not None}")
                print()
        
        # 3. 测试选择功能
        print("=== 测试自动选择功能 ===")
        if dialog.product_table.rowCount() > 0:
            # 选择第一行
            dialog.product_table.selectRow(0)
            dialog.on_selection_changed()
            
            if dialog.selected_product:
                print(f"✅ 成功选择产品: {dialog.selected_product.model_name}")
                print(f"   产品ID: {dialog.selected_product.id}")
                print(f"   标准直径: {dialog.selected_product.standard_diameter}")
                print(f"   公差上限: {dialog.selected_product.tolerance_upper}")
                print(f"   公差下限: {dialog.selected_product.tolerance_lower}")
            else:
                print("❌ 选择失败，selected_product为None")
        else:
            print("❌ 没有产品可供选择")
        
        # 4. 检查按钮状态
        print("\n=== 按钮状态检查 ===")
        print(f"选择按钮启用状态: {dialog.select_btn.isEnabled()}")
        print(f"刷新按钮启用状态: {dialog.refresh_btn.isEnabled()}")
        print(f"管理按钮启用状态: {dialog.manage_btn.isEnabled()}")
        
        dialog.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_autocomplete_functionality():
    """测试自动补全功能"""
    print("\n=== 测试自动补全功能 ===")
    
    try:
        from src.shared.models.product_model import get_product_manager
        manager = get_product_manager()
        
        # 获取所有产品名称
        products = manager.get_all_products(active_only=True)
        product_names = [p.model_name for p in products]
        
        print(f"✅ 可用于自动补全的产品名称:")
        for name in product_names:
            print(f"  - {name}")
        
        # 检查是否包含CAP1000等预设型号
        expected_models = ['CAP1000', 'TP-001', 'TP-002']
        missing_models = []
        
        for model in expected_models:
            if model in product_names:
                print(f"✅ 找到预设型号: {model}")
            else:
                missing_models.append(model)
        
        if missing_models:
            print(f"❌ 缺少预设型号: {missing_models}")
        else:
            print("✅ 所有预设型号都存在")
            
    except Exception as e:
        print(f"❌ 自动补全测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("开始详细测试产品选择对话框...")
    
    test_product_dialog_data()
    test_autocomplete_functionality()
    
    print("\n=== 测试总结 ===")
    print("如果上述测试都通过，说明产品选择对话框本身是正常的。")
    print("问题可能出现在:")
    print("1. 产品选择对话框的调用方式")
    print("2. 输入框没有正确绑定自动补全")
    print("3. 预定义产品列表的显示问题")
    print("4. 对话框与父窗口的交互问题")

if __name__ == "__main__":
    main()