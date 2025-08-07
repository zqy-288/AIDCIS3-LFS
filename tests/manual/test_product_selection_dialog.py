#!/usr/bin/env python3
"""
测试产品选择对话框
用于检查ProductSelectionDialog的功能是否正常
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

def test_product_manager():
    """测试产品管理器"""
    print("=== 测试产品管理器 ===")
    try:
        from src.shared.models.product_model import get_product_manager
        
        manager = get_product_manager()
        print(f"✅ 产品管理器初始化成功")
        
        # 获取所有产品
        products = manager.get_all_products(active_only=True)
        print(f"✅ 获取到 {len(products)} 个启用的产品")
        
        for product in products:
            print(f"  - {product.model_name}: {product.standard_diameter}mm (公差: {product.tolerance_range})")
            
    except Exception as e:
        print(f"❌ 产品管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_product_selection_dialog():
    """测试产品选择对话框"""
    print("\n=== 测试产品选择对话框 ===")
    try:
        # 方法1：测试P1页面版本
        from src.pages.main_detection_p1.modules.product_selection import ProductSelectionDialog
        print("✅ P1页面版本ProductSelectionDialog导入成功")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        class TestWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("产品选择对话框测试")
                self.setGeometry(100, 100, 400, 200)
                
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                
                btn1 = QPushButton("测试P1页面版本ProductSelectionDialog")
                btn1.clicked.connect(self.test_p1_dialog)
                layout.addWidget(btn1)
                
                btn2 = QPushButton("测试modules版本ProductSelectionDialog")
                btn2.clicked.connect(self.test_modules_dialog)
                layout.addWidget(btn2)
                
            def test_p1_dialog(self):
                """测试P1页面版本"""
                try:
                    from src.pages.main_detection_p1.modules.product_selection import ProductSelectionDialog
                    dialog = ProductSelectionDialog(self)
                    
                    # 检查对话框是否正确创建
                    if hasattr(dialog, 'product_table'):
                        print("✅ P1版本对话框创建成功，包含product_table")
                    else:
                        print("❌ P1版本对话框缺少product_table")
                    
                    # 检查产品数据是否加载
                    row_count = dialog.product_table.rowCount()
                    print(f"✅ P1版本对话框加载了 {row_count} 个产品")
                    
                    # 显示对话框
                    if dialog.exec():
                        if dialog.selected_product:
                            QMessageBox.information(
                                self, "选择成功", 
                                f"选择了产品: {dialog.selected_product.model_name}"
                            )
                        else:
                            QMessageBox.warning(self, "警告", "没有选择产品")
                    else:
                        print("用户取消了对话框")
                        
                except Exception as e:
                    print(f"❌ P1版本对话框测试失败: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "错误", f"P1版本对话框测试失败: {str(e)}")
            
            def test_modules_dialog(self):
                """测试modules版本"""
                try:
                    from src.modules.product_selection import ProductSelectionDialog
                    dialog = ProductSelectionDialog(self)
                    
                    # 检查对话框是否正确创建
                    if hasattr(dialog, 'product_table'):
                        print("✅ modules版本对话框创建成功，包含product_table")
                    else:
                        print("❌ modules版本对话框缺少product_table")
                    
                    # 检查产品数据是否加载
                    row_count = dialog.product_table.rowCount()
                    print(f"✅ modules版本对话框加载了 {row_count} 个产品")
                    
                    # 显示对话框
                    if dialog.exec():
                        if dialog.selected_product:
                            QMessageBox.information(
                                self, "选择成功", 
                                f"选择了产品: {dialog.selected_product.model_name}"
                            )
                        else:
                            QMessageBox.warning(self, "警告", "没有选择产品")
                    else:
                        print("用户取消了对话框")
                        
                except Exception as e:
                    print(f"❌ modules版本对话框测试失败: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(self, "错误", f"modules版本对话框测试失败: {str(e)}")
        
        window = TestWindow()
        window.show()
        
        print("✅ 测试窗口已显示，请点击按钮测试对话框")
        return window
        
    except Exception as e:
        print(f"❌ 产品选择对话框测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("开始测试产品选择对话框...")
    
    # 测试产品管理器
    test_product_manager()
    
    # 测试产品选择对话框
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = test_product_selection_dialog()
    
    if window:
        sys.exit(app.exec())

if __name__ == "__main__":
    main()