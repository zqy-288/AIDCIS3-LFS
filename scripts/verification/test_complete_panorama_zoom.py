#!/usr/bin/env python3
"""
测试完整全景图组件的缩放功能
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QSlider
from PySide6.QtCore import Qt

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
        self.setWindowTitle("完整全景图缩放测试")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 创建检测视图
        self.detection_view = NativeMainDetectionView()
        layout.addWidget(self.detection_view)
        
        # 加载测试数据
        self.load_test_data()
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("全景图缩放控制")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # 缩放滑块
        zoom_label = QLabel("孔位缩放比例: 10%")
        self.zoom_label = zoom_label
        layout.addWidget(zoom_label)
        
        zoom_slider = QSlider(Qt.Horizontal)
        zoom_slider.setMinimum(1)  # 0.1% - 100%
        zoom_slider.setMaximum(1000)
        zoom_slider.setValue(100)  # 默认10%
        zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_slider = zoom_slider
        layout.addWidget(zoom_slider)
        
        # 预设按钮
        preset_layout = QVBoxLayout()
        
        btn_1_percent = QPushButton("1% (超密集)")
        btn_1_percent.clicked.connect(lambda: self.set_zoom(0.01))
        preset_layout.addWidget(btn_1_percent)
        
        btn_5_percent = QPushButton("5% (密集)")
        btn_5_percent.clicked.connect(lambda: self.set_zoom(0.05))
        preset_layout.addWidget(btn_5_percent)
        
        btn_10_percent = QPushButton("10% (推荐)")
        btn_10_percent.clicked.connect(lambda: self.set_zoom(0.1))
        preset_layout.addWidget(btn_10_percent)
        
        btn_20_percent = QPushButton("20% (稀疏)")
        btn_20_percent.clicked.connect(lambda: self.set_zoom(0.2))
        preset_layout.addWidget(btn_20_percent)
        
        btn_50_percent = QPushButton("50% (超大)")
        btn_50_percent.clicked.connect(lambda: self.set_zoom(0.5))
        preset_layout.addWidget(btn_50_percent)
        
        layout.addLayout(preset_layout)
        
        # 信息标签
        self.info_label = QLabel("等待加载数据...")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.info_label)
        
        panel.setMaximumHeight(300)
        return panel
        
    def on_zoom_changed(self, value):
        """缩放滑块变化"""
        scale_factor = value / 1000.0  # 转换为0.001到1.0
        self.zoom_label.setText(f"孔位缩放比例: {scale_factor*100:.1f}%")
        
        # 应用到全景图
        if hasattr(self.detection_view, 'left_info_panel') and hasattr(self.detection_view.left_info_panel, 'sidebar_panorama'):
            panorama = self.detection_view.left_info_panel.sidebar_panorama
            if hasattr(panorama, 'set_user_hole_scale_factor'):
                panorama.set_user_hole_scale_factor(scale_factor)
                # 重新调整孔位大小
                if hasattr(panorama, '_adjust_hole_display_size'):
                    panorama._adjust_hole_display_size()
                self.logger.info(f"✅ 设置缩放比例: {scale_factor*100:.1f}%")
            else:
                self.logger.warning("❌ 全景图组件不支持 set_user_hole_scale_factor")
                
    def set_zoom(self, scale_factor):
        """设置缩放比例"""
        value = int(scale_factor * 1000)
        self.zoom_slider.setValue(value)
        
    def load_test_data(self):
        """加载测试数据"""
        try:
            # 使用CAP1000数据
            dxf_path = Path("Data/Products/CAP1000/dxf/CAP1000.dxf")
            if not dxf_path.exists():
                self.logger.warning(f"DXF文件不存在: {dxf_path}")
                self.info_label.setText("❌ DXF文件不存在")
                return
                
            # 加载DXF
            dxf_service = DXFLoaderService()
            hole_collection = dxf_service.load_dxf(str(dxf_path))
            
            if hole_collection and len(hole_collection.holes) > 0:
                hole_count = len(hole_collection.holes)
                self.logger.info(f"✅ 成功加载 {hole_count} 个孔位")
                self.info_label.setText(f"✅ 已加载 {hole_count} 个孔位\n使用滑块或按钮调整缩放比例")
                
                # 加载到检测视图
                self.detection_view.load_hole_collection(hole_collection)
                
                # 设置初始缩放
                self.set_zoom(0.1)  # 默认10%
                
            else:
                self.logger.error("❌ 加载孔位数据失败")
                self.info_label.setText("❌ 加载孔位数据失败")
                
        except Exception as e:
            self.logger.error(f"❌ 加载测试数据失败: {e}")
            self.info_label.setText(f"❌ 加载失败: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示窗口
    window = TestWindow()
    window.show()
    
    # 显示提示
    print("\n" + "="*60)
    print("完整全景图缩放功能测试")
    print("="*60)
    print("功能说明:")
    print("1. 使用滑块调整孔位显示大小（0.1% - 100%）")
    print("2. 点击预设按钮快速设置常用缩放比例")
    print("3. 观察左侧全景图中孔位大小的变化")
    print("4. 推荐使用10%左右的缩放比例")
    print("="*60 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()