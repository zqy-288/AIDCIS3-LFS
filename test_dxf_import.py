#!/usr/bin/env python3
"""
测试DXF导入功能
验证DXF文件解析和产品型号创建功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'models'))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

# 检查是否安装了ezdxf
try:
    import ezdxf
    EZDXF_AVAILABLE = True
    print("✓ ezdxf库已安装")
except ImportError:
    EZDXF_AVAILABLE = False
    print("✗ ezdxf库未安装，请运行: pip install ezdxf")

class DXFTestWindow(QMainWindow):
    """DXF导入功能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("DXF导入功能测试")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 测试按钮
        self.test_dxf_import_btn = QPushButton("测试DXF导入器")
        self.test_dxf_import_btn.clicked.connect(self.test_dxf_import)
        layout.addWidget(self.test_dxf_import_btn)
        
        self.test_product_mgmt_btn = QPushButton("测试产品管理界面")
        self.test_product_mgmt_btn.clicked.connect(self.test_product_management)
        layout.addWidget(self.test_product_mgmt_btn)
        
        self.test_sample_dxf_btn = QPushButton("测试示例DXF文件")
        self.test_sample_dxf_btn.clicked.connect(self.test_sample_dxf)
        layout.addWidget(self.test_sample_dxf_btn)
        
    def test_dxf_import(self):
        """测试DXF导入器基本功能"""
        try:
            from dxf_import import get_dxf_importer
            
            print("\n=== 测试DXF导入器 ===")
            
            # 获取导入器实例
            importer = get_dxf_importer()
            print("✓ DXF导入器初始化成功")
            
            # 检查ezdxf可用性
            if importer.check_ezdxf_availability():
                print("✓ ezdxf库检查通过")
            else:
                print("✗ ezdxf库不可用")
                QMessageBox.warning(self, "警告", "ezdxf库不可用，请安装: pip install ezdxf")
                return
            
            QMessageBox.information(self, "成功", "DXF导入器测试通过!")
            
        except Exception as e:
            error_msg = f"DXF导入器测试失败: {str(e)}"
            print(f"✗ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def test_product_management(self):
        """测试产品管理界面"""
        try:
            from product_management import ProductManagementDialog
            
            print("\n=== 测试产品管理界面 ===")
            
            # 创建对话框
            dialog = ProductManagementDialog(self)
            print("✓ 产品管理对话框创建成功")
            
            # 显示对话框
            dialog.show()
            print("✓ 产品管理界面显示成功")
            
        except Exception as e:
            error_msg = f"产品管理界面测试失败: {str(e)}"
            print(f"✗ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def test_sample_dxf(self):
        """测试示例DXF文件解析"""
        try:
            from dxf_import import get_dxf_importer
            
            # 示例DXF文件路径
            dxf_file_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
            
            if not os.path.exists(dxf_file_path):
                QMessageBox.warning(self, "警告", f"DXF文件不存在: {dxf_file_path}")
                return
            
            print(f"\n=== 测试DXF文件解析: {os.path.basename(dxf_file_path)} ===")
            
            # 获取导入器
            importer = get_dxf_importer()
            
            if not importer.check_ezdxf_availability():
                QMessageBox.warning(self, "警告", "ezdxf库不可用，请安装: pip install ezdxf")
                return
            
            # 获取预览信息
            print("正在分析DXF文件...")
            preview_info = importer.get_import_preview(dxf_file_path)
            
            if 'error' in preview_info:
                error_msg = f"DXF分析失败: {preview_info['error']}"
                print(f"✗ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
                return
            
            # 显示分析结果
            print("✓ DXF文件分析成功")
            print(f"  - 建议产品型号: {preview_info.get('suggested_model_name', 'N/A')}")
            print(f"  - 检测孔数量: {preview_info.get('total_holes', 0)}")
            print(f"  - 标准直径: {preview_info.get('standard_diameter', 0):.2f} mm")
            print(f"  - 建议公差: ±{preview_info.get('tolerance_estimate', 0):.3f} mm")
            print(f"  - 图层数量: {preview_info.get('layer_count', 0)}")
            
            # 显示详细统计
            if 'diameter_stats' in preview_info:
                stats = preview_info['diameter_stats']
                print(f"  - 直径统计:")
                print(f"    最小: {stats.get('min', 0):.3f} mm")
                print(f"    最大: {stats.get('max', 0):.3f} mm")
                print(f"    平均: {stats.get('mean', 0):.3f} mm")
            
            # 构建显示消息
            msg = f"""DXF文件分析结果:

文件: {os.path.basename(dxf_file_path)}
建议产品型号: {preview_info.get('suggested_model_name', 'N/A')}
检测孔数量: {preview_info.get('total_holes', 0)}
标准直径: {preview_info.get('standard_diameter', 0):.2f} mm
建议公差: ±{preview_info.get('tolerance_estimate', 0):.3f} mm
图层数量: {preview_info.get('layer_count', 0)}"""
            
            if 'diameter_stats' in preview_info:
                stats = preview_info['diameter_stats']
                msg += f"""

直径统计:
最小: {stats.get('min', 0):.3f} mm
最大: {stats.get('max', 0):.3f} mm
平均: {stats.get('mean', 0):.3f} mm"""
            
            QMessageBox.information(self, "DXF分析结果", msg)
            
        except Exception as e:
            error_msg = f"DXF文件测试失败: {str(e)}"
            print(f"✗ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)

def main():
    """主函数"""
    print("启动DXF导入功能测试...")
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = DXFTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()