#!/usr/bin/env python3
"""
测试全景图自适应窗口大小功能
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
from src.core_business.models.hole_data import HoleCollection
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 设置窗口
        self.setWindowTitle("全景图自适应测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 控制按钮
        control_layout = QVBoxLayout()
        
        # 窗口大小控制
        size_label = QLabel("窗口大小控制:")
        control_layout.addWidget(size_label)
        
        btn_small = QPushButton("小窗口 (800x600)")
        btn_small.clicked.connect(lambda: self.resize(800, 600))
        control_layout.addWidget(btn_small)
        
        btn_medium = QPushButton("中窗口 (1200x800)")
        btn_medium.clicked.connect(lambda: self.resize(1200, 800))
        control_layout.addWidget(btn_medium)
        
        btn_large = QPushButton("大窗口 (1600x1000)")
        btn_large.clicked.connect(lambda: self.resize(1600, 1000))
        control_layout.addWidget(btn_large)
        
        btn_fullscreen = QPushButton("全屏/退出全屏")
        btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        control_layout.addWidget(btn_fullscreen)
        
        # 状态标签
        self.status_label = QLabel("当前窗口大小: ")
        control_layout.addWidget(self.status_label)
        
        layout.addLayout(control_layout)
        
        # 创建检测视图
        self.detection_view = NativeMainDetectionView()
        layout.addWidget(self.detection_view)
        
        # 加载测试数据
        self.load_test_data()
        
        # 定时更新状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(500)  # 每500ms更新一次
        
    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def update_status(self):
        """更新状态显示"""
        size = self.size()
        self.status_label.setText(f"当前窗口大小: {size.width()} x {size.height()}")
        
        # 检查左侧面板全景图的实际大小
        if hasattr(self.detection_view, 'left_info_panel') and hasattr(self.detection_view.left_info_panel, 'sidebar_panorama'):
            panorama = self.detection_view.left_info_panel.sidebar_panorama
            panorama_size = panorama.size()
            self.logger.info(f"左侧全景图大小: {panorama_size.width()} x {panorama_size.height()}")
            
    def load_test_data(self):
        """加载测试数据"""
        try:
            # 使用CAP1000数据
            dxf_path = Path("data/CAP1000堆内构件.dxf")
            if not dxf_path.exists():
                self.logger.warning(f"DXF文件不存在: {dxf_path}")
                return
                
            # 加载DXF
            dxf_service = DXFLoaderService()
            hole_collection = dxf_service.load_dxf(str(dxf_path))
            
            if hole_collection and len(hole_collection.holes) > 0:
                self.logger.info(f"✅ 成功加载 {len(hole_collection.holes)} 个孔位")
                
                # 加载到检测视图
                self.detection_view.load_hole_collection(hole_collection)
                
                # 确保协调器初始化
                QTimer.singleShot(100, self.detection_view.ensure_coordinator_initialized)
                
            else:
                self.logger.error("❌ 加载孔位数据失败")
                
        except Exception as e:
            self.logger.error(f"❌ 加载测试数据失败: {e}")
            import traceback
            traceback.print_exc()
            
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.logger.info(f"窗口大小改变: {event.size().width()} x {event.size().height()}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示窗口
    window = TestWindow()
    window.show()
    
    # 显示提示
    print("\n" + "="*50)
    print("全景图自适应测试")
    print("="*50)
    print("操作说明:")
    print("1. 点击按钮改变窗口大小")
    print("2. 拖动窗口边缘调整大小")
    print("3. 观察左侧全景图是否自适应")
    print("4. 查看日志中的尺寸信息")
    print("="*50 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()