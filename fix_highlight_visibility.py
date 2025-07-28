#!/usr/bin/env python3
"""
修复高亮可见性问题
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 在导入其他模块之前，先修改 SectorHighlightItem
print("修补 SectorHighlightItem...")

# 动态修改类的 setup_highlight 方法
from src.core_business.graphics.sector_highlight_item import SectorHighlightItem
original_setup = SectorHighlightItem.setup_highlight

def patched_setup_highlight(self):
    """修补后的设置高亮显示样式"""
    original_setup(self)
    # 注释掉这行，让高亮默认可见
    # self.setVisible(False)
    print(f"[修补] 创建了高亮项 {self.sector}，默认可见")

SectorHighlightItem.setup_highlight = patched_setup_highlight

# 现在导入其他模块
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
from src.core_business.graphics.panorama import CompletePanoramaWidgetAdapter
from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.models.hole_data import HoleData, HoleCollection

def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("高亮可见性修复测试")
    window.resize(800, 600)
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    window.setCentralWidget(central_widget)
    
    # 状态标签
    status_label = QLabel("准备测试...")
    layout.addWidget(status_label)
    
    # 全景图
    panorama = CompletePanoramaWidgetAdapter()
    panorama.setMinimumSize(500, 500)
    layout.addWidget(panorama)
    
    # 控制按钮
    btn_layout = QVBoxLayout()
    
    def create_data():
        """创建测试数据"""
        holes = {}
        # 在每个象限创建孔位
        positions = [
            (100, -100), (-100, -100), (-100, 100), (100, 100),
            (0, 0), (50, -50), (-50, -50), (-50, 50), (50, 50)
        ]
        for i, (x, y) in enumerate(positions):
            hole = HoleData(
                center_x=float(x),
                center_y=float(y),
                radius=20.0,
                hole_id=f"hole_{i}"
            )
            holes[hole.hole_id] = hole
        return HoleCollection(holes)
    
    def load_data():
        """加载数据"""
        status_label.setText("加载数据中...")
        collection = create_data()
        panorama.load_complete_view(collection)
        status_label.setText(f"已加载 {len(collection)} 个孔位")
        
        # 延迟检查
        QTimer.singleShot(500, check_highlights)
    
    def check_highlights():
        """检查高亮状态"""
        print("\n=== 检查高亮项 ===")
        if hasattr(panorama, '_panorama_widget'):
            widget = panorama._panorama_widget
            if hasattr(widget, 'controller') and hasattr(widget.controller, 'sector_handler'):
                handler = widget.controller.sector_handler
                if hasattr(handler, 'sector_highlights'):
                    print(f"高亮项数量: {len(handler.sector_highlights)}")
                    for sector, item in handler.sector_highlights.items():
                        visible = item.isVisible()
                        print(f"  {sector}: 可见={visible}, 位置={item.pos()}, Z值={item.zValue()}")
    
    def test_highlight(sector):
        """测试高亮"""
        status_label.setText(f"高亮 {sector.value}")
        print(f"\n尝试高亮 {sector.value}")
        panorama.highlight_sector(sector)
        
        # 检查结果
        QTimer.singleShot(100, lambda: check_highlight_result(sector))
    
    def check_highlight_result(sector):
        """检查高亮结果"""
        if hasattr(panorama, '_panorama_widget'):
            widget = panorama._panorama_widget
            if hasattr(widget, 'controller') and hasattr(widget.controller, 'sector_handler'):
                handler = widget.controller.sector_handler
                current = handler.get_current_highlighted_sector()
                print(f"当前高亮: {current}")
                
                # 检查所有高亮项的可见性
                if hasattr(handler, 'sector_highlights'):
                    for s, item in handler.sector_highlights.items():
                        if s == sector.value:
                            print(f"  {s}: 应该可见={item.isVisible()}")
    
    load_btn = QPushButton("加载数据")
    load_btn.clicked.connect(load_data)
    btn_layout.addWidget(load_btn)
    
    # 高亮按钮
    for sector in [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2,
                  SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]:
        btn = QPushButton(f"高亮 {sector.value}")
        btn.clicked.connect(lambda checked=False, s=sector: test_highlight(s))
        btn_layout.addWidget(btn)
    
    clear_btn = QPushButton("清除高亮")
    clear_btn.clicked.connect(lambda: panorama.clear_sector_highlight())
    btn_layout.addWidget(clear_btn)
    
    layout.addLayout(btn_layout)
    
    # 监听点击事件
    def on_sector_clicked(sector):
        status_label.setText(f"点击了 {sector.value if hasattr(sector, 'value') else sector}")
        print(f"\n🎯 扇形被点击: {sector}")
    
    panorama.sector_clicked.connect(on_sector_clicked)
    
    window.show()
    
    # 自动加载数据
    QTimer.singleShot(100, load_data)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()