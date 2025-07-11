#!/usr/bin/env python3
"""
产品管理界面测试（使用系统库）
验证产品管理和DXF导入界面的基本功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'models'))

# 检查GUI库
GUI_AVAILABLE = False
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
    from PySide6.QtCore import Qt
    GUI_AVAILABLE = True
    print("✓ PySide6 GUI库可用")
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
        from PyQt5.QtCore import Qt
        GUI_AVAILABLE = True
        print("✓ PyQt5 GUI库可用")
    except ImportError:
        print("✗ 未找到GUI库（PySide6或PyQt5）")

def test_console_mode():
    """控制台模式测试"""
    print("\n=== 控制台模式测试 ===")
    
    try:
        from product_model import get_product_manager
        from dxf_import import get_dxf_importer
        
        # 测试产品管理器
        manager = get_product_manager()
        products = manager.get_all_products()
        print(f"✓ 当前系统中有 {len(products)} 个产品型号")
        
        for product in products:
            print(f"  - {product.model_name}: {product.standard_diameter:.2f}mm {product.tolerance_range}")
        
        # 测试DXF导入器
        importer = get_dxf_importer()
        dxf_file = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
        
        if os.path.exists(dxf_file):
            preview = importer.get_import_preview(dxf_file)
            if 'error' not in preview:
                print(f"✓ DXF文件解析成功: {preview['suggested_model_name']}")
                print(f"  检测到 {preview['total_holes']} 个孔，标准直径 {preview['standard_diameter']:.2f}mm")
            else:
                print(f"✗ DXF解析错误: {preview['error']}")
        else:
            print("✗ DXF测试文件不存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 控制台测试失败: {str(e)}")
        return False

class ProductTestWindow:
    """产品管理测试窗口"""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            print("GUI库不可用，无法创建窗口")
            return
            
        self.app = QApplication(sys.argv)
        self.setup_ui()
        
    def setup_ui(self):
        """初始化界面"""
        self.window = QMainWindow()
        self.window.setWindowTitle("产品管理功能测试")
        self.window.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 测试按钮
        self.test_product_mgmt_btn = QPushButton("打开产品管理界面")
        self.test_product_mgmt_btn.clicked.connect(self.test_product_management)
        layout.addWidget(self.test_product_mgmt_btn)
        
        self.test_product_selection_btn = QPushButton("打开产品选择界面")
        self.test_product_selection_btn.clicked.connect(self.test_product_selection)
        layout.addWidget(self.test_product_selection_btn)
        
        self.test_dxf_import_btn = QPushButton("测试DXF导入功能")
        self.test_dxf_import_btn.clicked.connect(self.test_dxf_import)
        layout.addWidget(self.test_dxf_import_btn)
        
    def test_product_management(self):
        """测试产品管理界面"""
        try:
            from product_management import ProductManagementDialog
            
            dialog = ProductManagementDialog(self.window)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self.window, "错误", f"产品管理界面打开失败: {str(e)}")
    
    def test_product_selection(self):
        """测试产品选择界面"""
        try:
            from product_selection import ProductSelectionDialog
            
            dialog = ProductSelectionDialog(self.window)
            result = dialog.exec()
            
            if result == dialog.Accepted and dialog.selected_product:
                QMessageBox.information(
                    self.window, "选择结果", 
                    f"已选择产品: {dialog.selected_product.model_name}"
                )
            
        except Exception as e:
            QMessageBox.critical(self.window, "错误", f"产品选择界面打开失败: {str(e)}")
    
    def test_dxf_import(self):
        """测试DXF导入功能"""
        try:
            from dxf_import import get_dxf_importer
            
            dxf_file = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
            
            if not os.path.exists(dxf_file):
                QMessageBox.warning(self.window, "警告", "DXF测试文件不存在")
                return
            
            importer = get_dxf_importer()
            preview = importer.get_import_preview(dxf_file)
            
            if 'error' in preview:
                QMessageBox.critical(self.window, "错误", f"DXF解析失败: {preview['error']}")
                return
            
            # 显示解析结果
            msg = f"""DXF文件解析成功！

文件: {os.path.basename(dxf_file)}
建议产品型号: {preview['suggested_model_name']}
检测孔数量: {preview['total_holes']}
标准直径: {preview['standard_diameter']:.2f} mm
建议公差: ±{preview['tolerance_estimate']:.3f} mm"""
            
            QMessageBox.information(self.window, "DXF解析结果", msg)
            
        except Exception as e:
            QMessageBox.critical(self.window, "错误", f"DXF导入测试失败: {str(e)}")
    
    def run(self):
        """运行应用"""
        if not GUI_AVAILABLE:
            return False
            
        self.window.show()
        return self.app.exec()

def main():
    """主函数"""
    print("产品管理系统功能测试")
    print("=" * 40)
    
    # 总是运行控制台测试
    console_result = test_console_mode()
    
    if GUI_AVAILABLE:
        print("\n=== GUI模式测试 ===")
        print("启动图形界面测试...")
        
        try:
            test_window = ProductTestWindow()
            test_window.run()
        except Exception as e:
            print(f"GUI测试失败: {str(e)}")
    else:
        print("\n=== GUI模式不可用 ===")
        print("请安装 PySide6 或 PyQt5 来使用图形界面:")
        print("  pip install PySide6")
        print("  或")
        print("  pip install PyQt5")
    
    print("\n=== 测试完成 ===")
    if console_result:
        print("✓ 核心功能测试通过")
    else:
        print("✗ 核心功能测试失败")
    
    return 0 if console_result else 1

if __name__ == "__main__":
    sys.exit(main())