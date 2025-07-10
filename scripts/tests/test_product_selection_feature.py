"""
产品型号选择功能测试脚本
测试从"加载文件"到"选择产品"的逻辑转变
"""

import sys
import os

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src')
sys.path.insert(0, src_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

def test_product_model():
    """测试产品型号数据模型"""
    print("=" * 50)
    print("测试产品型号数据模型...")
    
    try:
        from models.product_model import get_product_manager
        
        manager = get_product_manager()
        print("✅ 产品管理器初始化成功")
        
        # 获取所有产品
        products = manager.get_all_products()
        print(f"✅ 获取到 {len(products)} 个产品型号")
        
        for product in products:
            print(f"   - {product.model_name}: 直径{product.standard_diameter}mm, 公差{product.tolerance_range}")
        
        # 测试创建新产品
        test_product = manager.create_product(
            model_name="TEST-001",
            standard_diameter=8.0,
            tolerance_upper=0.03,
            tolerance_lower=-0.03,
            description="测试产品型号"
        )
        print(f"✅ 创建测试产品成功: {test_product.model_name}")
        
        # 测试更新产品
        updated = manager.update_product(test_product.id, description="更新后的测试产品")
        print(f"✅ 更新产品成功: {updated.description}")
        
        # 测试删除产品
        manager.delete_product(test_product.id)
        print("✅ 删除测试产品成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 产品模型测试失败: {str(e)}")
        return False

def test_product_selection_dialog():
    """测试产品选择对话框"""
    print("=" * 50)
    print("测试产品选择对话框...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.product_selection import ProductSelectionDialog
        
        dialog = ProductSelectionDialog()
        print("✅ 产品选择对话框创建成功")
        
        # 测试加载产品列表
        dialog.load_products()
        print("✅ 产品列表加载成功")
        
        # 检查表格是否有数据
        row_count = dialog.product_table.rowCount()
        print(f"✅ 产品表格显示 {row_count} 行数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 产品选择对话框测试失败: {str(e)}")
        return False

def test_product_management_dialog():
    """测试产品管理对话框"""
    print("=" * 50)
    print("测试产品管理对话框...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.product_management import ProductManagementDialog
        
        dialog = ProductManagementDialog()
        print("✅ 产品管理对话框创建成功")
        
        # 测试加载产品列表
        dialog.load_products()
        print("✅ 产品列表加载成功")
        
        # 检查表格是否有数据
        row_count = dialog.product_table.rowCount()
        print(f"✅ 产品表格显示 {row_count} 行数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 产品管理对话框测试失败: {str(e)}")
        return False

def test_main_window_integration():
    """测试主窗口集成"""
    print("=" * 50)
    print("测试主窗口集成...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from main_window import MainWindow
        
        window = MainWindow()
        print("✅ 主窗口创建成功")
        
        # 检查产品选择按钮是否存在
        if hasattr(window, 'product_select_btn'):
            print("✅ 产品选择按钮已正确创建")
            print(f"   按钮文本: {window.product_select_btn.text()}")
        else:
            print("❌ 产品选择按钮不存在")
            return False
        
        # 检查产品管理器是否初始化
        if hasattr(window, 'product_manager'):
            print("✅ 产品管理器已正确初始化")
        else:
            print("❌ 产品管理器未初始化")
            return False
        
        # 检查方法是否存在
        if hasattr(window, 'select_product_model'):
            print("✅ 产品选择方法已正确定义")
        else:
            print("❌ 产品选择方法不存在")
            return False
        
        if hasattr(window, 'open_product_management'):
            print("✅ 产品管理方法已正确定义")
        else:
            print("❌ 产品管理方法不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 主窗口集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("开始产品型号选择功能测试...")
    print("=" * 60)
    
    tests = [
        ("产品型号数据模型", test_product_model),
        ("产品选择对话框", test_product_selection_dialog),
        ("产品管理对话框", test_product_management_dialog),
        ("主窗口集成", test_main_window_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            results[test_name] = False
    
    # 输出测试结果总结
    print("=" * 60)
    print("测试结果总结:")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过! 产品型号选择功能已成功实现")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)