#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from modules.panorama_view.core.di_container import PanoramaDIContainer
from modules.panorama_view.components.panorama_widget import PanoramaWidget

class SectorTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形分隔线显示测试")
        self.setGeometry(100, 100, 700, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        try:
            # 创建DI容器和全景图组件
            container = PanoramaDIContainer()
            controller = container.get_view_controller()
            self.panorama_widget = PanoramaWidget(controller)
            layout.addWidget(self.panorama_widget)
            
            print("✅ 全景图组件已创建")
            print("🔍 请查看窗口中是否显示：")
            print("   - 深灰色十字分隔线（将圆分成4个象限）")
            print("   - 灰色虚线扇形边界")
            print("   - 四个清晰的扇形区域")
            
        except Exception as e:
            print(f"❌ 创建全景图组件失败: {e}")
            # 降级方案：显示错误信息
            from PySide6.QtWidgets import QLabel
            error_label = QLabel(f"全景图加载失败:\n{str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SectorTestWindow()
    window.show()
    
    print("\n🎯 扇形显示测试窗口已打开")
    print("📸 请截图确认扇形分隔线是否可见")
    
    app.exec()