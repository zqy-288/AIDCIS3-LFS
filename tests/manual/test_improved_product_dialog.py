#!/usr/bin/env python3
"""
测试改进后的产品选择对话框
验证搜索功能和自动补全功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

def test_improved_dialog():
    """测试改进后的产品选择对话框"""
    print("=== 测试改进后的产品选择对话框 ===")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("测试改进后的产品选择对话框")
            self.setGeometry(100, 100, 500, 300)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            info_label = QWidget()
            info_layout = QVBoxLayout(info_label)
            info_layout.addWidget(QPushButton("测试说明:"))
            info_layout.addWidget(QPushButton("1. 点击下面的按钮打开产品选择对话框"))
            info_layout.addWidget(QPushButton("2. 在搜索框中输入产品名称 (如: CAP, TP-001)"))
            info_layout.addWidget(QPushButton("3. 观察自动补全功能和表格过滤"))
            info_layout.addWidget(QPushButton("4. 选择产品并确认"))
            layout.addWidget(info_label)
            
            btn_p1 = QPushButton("测试P1版本 (带搜索功能)")
            btn_p1.clicked.connect(self.test_p1_version)
            btn_p1.setStyleSheet("QPushButton { background-color: #2ECC71; color: white; font-weight: bold; padding: 10px; }")
            layout.addWidget(btn_p1)
            
            btn_modules = QPushButton("测试Modules版本 (带搜索功能)")
            btn_modules.clicked.connect(self.test_modules_version)
            btn_modules.setStyleSheet("QPushButton { background-color: #3498DB; color: white; font-weight: bold; padding: 10px; }")
            layout.addWidget(btn_modules)
            
        def test_p1_version(self):
            """测试P1版本"""
            try:
                from src.pages.main_detection_p1.modules.product_selection import ProductSelectionDialog
                
                dialog = ProductSelectionDialog(self)
                print("✅ P1版本对话框创建成功")
                
                # 检查是否有搜索输入框
                if hasattr(dialog, 'search_input'):
                    print("✅ 搜索输入框已添加")
                    print(f"   占位符文本: {dialog.search_input.placeholderText()}")
                    
                    # 检查自动补全
                    completer = dialog.search_input.completer()
                    if completer:
                        print("✅ 自动补全功能已设置")
                        model = completer.model()
                        if model:
                            print(f"   自动补全项目数: {model.rowCount()}")
                            # 显示前几个补全项目
                            for i in range(min(3, model.rowCount())):
                                item = model.data(model.index(i, 0))
                                print(f"     - {item}")
                    else:
                        print("❌ 自动补全功能未设置")
                else:
                    print("❌ 搜索输入框未找到")
                
                # 显示对话框
                result = dialog.exec()
                if result and dialog.selected_product:
                    QMessageBox.information(
                        self, "选择成功", 
                        f"选择了产品: {dialog.selected_product.model_name}\n"
                        f"标准直径: {dialog.selected_product.standard_diameter}mm\n"
                        f"公差范围: {dialog.selected_product.tolerance_range}"
                    )
                    print(f"✅ 成功选择产品: {dialog.selected_product.model_name}")
                else:
                    print("用户取消了选择")
                    
            except Exception as e:
                print(f"❌ P1版本测试失败: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "错误", f"P1版本测试失败: {str(e)}")
        
        def test_modules_version(self):
            """测试Modules版本"""
            try:
                from src.modules.product_selection import ProductSelectionDialog
                
                dialog = ProductSelectionDialog(self)
                print("✅ Modules版本对话框创建成功")
                
                # 检查搜索功能
                if hasattr(dialog, 'search_input'):
                    print("✅ 搜索输入框已添加")
                    print(f"   占位符文本: {dialog.search_input.placeholderText()}")
                    
                    # 检查自动补全
                    completer = dialog.search_input.completer()
                    if completer:
                        print("✅ 自动补全功能已设置")
                        model = completer.model()
                        if model:
                            print(f"   自动补全项目数: {model.rowCount()}")
                    else:
                        print("❌ 自动补全功能未设置")
                else:
                    print("❌ 搜索输入框未找到")
                
                # 显示对话框
                result = dialog.exec()
                if result and dialog.selected_product:
                    QMessageBox.information(
                        self, "选择成功", 
                        f"选择了产品: {dialog.selected_product.model_name}\n"
                        f"标准直径: {dialog.selected_product.standard_diameter}mm\n"
                        f"公差范围: {dialog.selected_product.tolerance_range}"
                    )
                    print(f"✅ 成功选择产品: {dialog.selected_product.model_name}")
                else:
                    print("用户取消了选择")
                    
            except Exception as e:
                print(f"❌ Modules版本测试失败: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "错误", f"Modules版本测试失败: {str(e)}")
    
    window = TestWindow()
    window.show()
    
    print("✅ 测试窗口已显示")
    print("请点击按钮测试改进后的对话框功能:")
    print("- 搜索输入框")
    print("- 自动补全功能")
    print("- 实时表格过滤")
    
    return window

def main():
    """主函数"""
    print("开始测试改进后的产品选择对话框...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = test_improved_dialog()
    
    if window:
        sys.exit(app.exec())

if __name__ == "__main__":
    main()