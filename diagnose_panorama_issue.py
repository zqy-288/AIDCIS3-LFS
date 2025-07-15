#!/usr/bin/env python3
"""诊断全景图显示问题"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.dxf_parser import DXFParser
from aidcis2.graphics.sector_manager import SectorQuadrant

def diagnose_panorama():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = QMainWindow()
    window.setWindowTitle("全景图诊断")
    window.resize(800, 600)
    
    # 创建中心部件
    central = QWidget()
    layout = QVBoxLayout()
    central.setLayout(layout)
    window.setCentralWidget(central)
    
    # 创建全景图组件
    panorama = CompletePanoramaWidget()
    layout.addWidget(panorama)
    
    # 加载数据
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    parser = DXFParser()
    hole_collection = parser.parse_file(dxf_path)
    
    if hole_collection:
        print(f"📊 加载了 {len(hole_collection.holes)} 个孔位")
        
        # 加载完整视图
        panorama.load_complete_view(hole_collection)
        
        # 创建控制按钮
        btn_layout = QVBoxLayout()
        
        # 检查场景内容
        def check_scene():
            scene = panorama.panorama_view.scene
            if scene:
                items = scene.items()
                print(f"\n场景内容检查:")
                print(f"- 总图形项数: {len(items)}")
                
                # 统计不同类型的图形项
                hole_items = 0
                highlight_items = 0
                other_items = 0
                
                for item in items:
                    if hasattr(item, 'hole_data'):
                        hole_items += 1
                    elif hasattr(item, 'sector'):  # SectorHighlightItem
                        highlight_items += 1
                        print(f"  - 高亮项: {item.sector.value}, 可见={item.isVisible()}")
                    else:
                        other_items += 1
                
                print(f"- 孔位图形项: {hole_items}")
                print(f"- 高亮图形项: {highlight_items}")
                print(f"- 其他图形项: {other_items}")
        
        check_btn = QPushButton("检查场景内容")
        check_btn.clicked.connect(check_scene)
        btn_layout.addWidget(check_btn)
        
        # 高亮各个扇形
        for sector in SectorQuadrant:
            btn = QPushButton(f"高亮 {sector.value}")
            btn.clicked.connect(lambda checked, s=sector: panorama.highlight_sector(s))
            btn_layout.addWidget(btn)
        
        # 清除高亮
        clear_btn = QPushButton("清除高亮")
        clear_btn.clicked.connect(panorama.clear_highlight)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
    
    window.show()
    
    # 初始检查
    print("\n初始状态:")
    check_scene()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(diagnose_panorama())