#!/usr/bin/env python3
"""
扇形显示组件单元测试
测试pages目录下修复后的组件是否能正常加载和显示
"""

import sys
import os
from pathlib import Path
import traceback

# 添加项目路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor

def test_sector_highlight_import():
    """测试扇形高亮组件导入"""
    try:
        from pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
        from core_business.graphics.sector_types import SectorQuadrant
        print("✅ SectorHighlightItem 导入成功")
        return True, SectorHighlightItem, SectorQuadrant
    except Exception as e:
        print(f"❌ SectorHighlightItem 导入失败: {e}")
        traceback.print_exc()
        return False, None, None

def test_panorama_widget_import():
    """测试全景图组件导入"""
    try:
        from pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        print("✅ CompletePanoramaWidget 导入成功")
        return True, CompletePanoramaWidget
    except Exception as e:
        print(f"❌ CompletePanoramaWidget 导入失败: {e}")
        traceback.print_exc()
        return False, None

def test_sector_highlight_creation():
    """测试扇形高亮组件创建"""
    success, SectorHighlightItem, SectorQuadrant = test_sector_highlight_import()
    if not success:
        return False
    
    try:
        # 创建扇形高亮项
        center = QPointF(300, 300)
        radius = 200
        # 获取第一个扇形区域
        sector = list(SectorQuadrant)[0]  # 使用list()避免属性错误
        
        highlight_item = SectorHighlightItem(sector, center, radius)
        
        # 检查基本属性
        assert highlight_item.sector == sector
        assert highlight_item.center == center
        assert highlight_item.radius == radius
        assert highlight_item.isVisible() == True  # 应该默认可见
        
        # 检查样式设置
        pen = highlight_item.pen()
        assert pen.color().alpha() > 0  # 应该有透明度
        # 注意：Qt.DashLine 的值是 2
        assert pen.style() == 2  # 应该是虚线
        
        print("✅ SectorHighlightItem 创建和样式测试通过")
        return True
    except Exception as e:
        print(f"❌ SectorHighlightItem 创建测试失败: {e}")
        traceback.print_exc()
        return False

class SectorDisplayTestWindow(QMainWindow):
    """扇形显示测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形显示组件单元测试")
        self.setGeometry(100, 100, 800, 800)
        
        # 测试结果
        self.test_results = []
        
        # 创建UI
        self.setup_ui()
        
        # 5秒后自动运行测试
        QTimer.singleShot(1000, self.run_component_tests)
    
    def setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("扇形显示组件单元测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 测试状态显示
        self.status_label = QLabel("准备运行测试...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("margin: 10px; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # 测试组件容器
        self.test_container = QWidget()
        self.test_layout = QVBoxLayout(self.test_container)
        layout.addWidget(self.test_container)
    
    def run_component_tests(self):
        """运行组件测试"""
        self.status_label.setText("🔍 运行组件测试中...")
        
        # 测试1: 导入测试
        print("\n=== 扇形显示组件单元测试 ===")
        
        # 测试扇形高亮组件
        sector_success = test_sector_highlight_creation()
        self.test_results.append(("扇形高亮组件", sector_success))
        
        # 测试全景图组件导入
        panorama_success, PanoramaWidget = test_panorama_widget_import()
        self.test_results.append(("全景图组件导入", panorama_success))
        
        # 测试全景图组件创建
        if panorama_success:
            try:
                panorama_widget = PanoramaWidget()
                panorama_widget.setFixedSize(600, 600)
                self.test_layout.addWidget(panorama_widget)
                print("✅ CompletePanoramaWidget 创建成功")
                self.test_results.append(("全景图组件创建", True))
                
                # 测试分隔线方法
                if hasattr(panorama_widget, '_create_sector_dividers'):
                    panorama_widget._create_sector_dividers()
                    print("✅ 扇形分隔线创建方法调用成功")
                    self.test_results.append(("分隔线创建", True))
                else:
                    print("⚠️ 找不到_create_sector_dividers方法")
                    self.test_results.append(("分隔线创建", False))
                    
            except Exception as e:
                print(f"❌ CompletePanoramaWidget 创建失败: {e}")
                traceback.print_exc()
                self.test_results.append(("全景图组件创建", False))
        
        # 显示测试结果
        self.display_test_results()
    
    def display_test_results(self):
        """显示测试结果"""
        results_text = "📊 测试结果总结:\n\n"
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            results_text += f"{test_name}: {status}\n"
            if success:
                passed += 1
        
        results_text += f"\n总计: {passed}/{total} 项测试通过"
        
        if passed == total:
            results_text += "\n\n🎉 所有测试通过! 组件应该能正常显示扇形分隔线。"
        else:
            results_text += f"\n\n⚠️ 有 {total-passed} 项测试失败，可能影响扇形显示。"
        
        self.status_label.setText(results_text)
        print(f"\n{results_text}")

def main():
    """主函数"""
    print("🚀 启动扇形显示组件单元测试")
    
    app = QApplication(sys.argv)
    
    # 先运行基础测试
    print("\n=== 基础导入测试 ===")
    test_sector_highlight_import()
    test_panorama_widget_import()
    
    # 创建测试窗口
    window = SectorDisplayTestWindow()
    window.show()
    
    print("\n📋 测试窗口已打开，将自动运行组件测试")
    print("🔍 请观察:")
    print("  1. 组件是否成功加载")
    print("  2. 扇形分隔线是否可见")
    print("  3. 测试结果总结")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()