#!/usr/bin/env python3
"""
快速测试高亮功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.core_business.graphics.sector_highlight_item import SectorHighlightItem
from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.graphics.panorama import CompletePanoramaWidgetAdapter
from src.core_business.models.hole_data import HoleData, HoleCollection

def test():
    app = QApplication(sys.argv)
    
    print("=== 测试高亮修复 ===")
    
    # 1. 测试SectorHighlightItem的画笔设置
    print("\n1. 检查SectorHighlightItem画笔设置:")
    from PySide6.QtCore import QPointF
    item = SectorHighlightItem(SectorQuadrant.SECTOR_1, QPointF(0, 0), 100)
    pen = item.pen()
    print(f"   线宽: {pen.width()}")
    print(f"   颜色: {pen.color().name()}")
    print(f"   透明度: {pen.color().alpha()}")
    print(f"   是否Cosmetic: {pen.isCosmetic()}")
    
    # 2. 测试适配器
    print("\n2. 测试适配器高亮功能:")
    adapter = CompletePanoramaWidgetAdapter()
    
    # 创建简单数据
    holes = {"test": HoleData(0, 0, 20, "test")}
    collection = HoleCollection(holes)
    adapter.load_complete_view(collection)
    
    # 测试高亮
    print("   尝试高亮SECTOR_1...")
    adapter.highlight_sector(SectorQuadrant.SECTOR_1)
    
    # 检查状态
    def check():
        if hasattr(adapter, '_panorama_widget'):
            widget = adapter._panorama_widget
            if hasattr(widget, 'controller') and hasattr(widget.controller, 'sector_handler'):
                handler = widget.controller.sector_handler
                current = handler.get_current_highlighted_sector()
                print(f"   当前高亮: {current}")
                
                if hasattr(handler, 'sector_highlights'):
                    for sector, item in handler.sector_highlights.items():
                        if item.isVisible():
                            print(f"   ✅ {sector} 可见")
                            pen = item.pen()
                            print(f"      画笔: 宽度={pen.width()}, Cosmetic={pen.isCosmetic()}")
        
        print("\n测试完成！")
        app.quit()
    
    # 增加延迟，确保定时器触发
    QTimer.singleShot(500, check)
    app.exec()

if __name__ == "__main__":
    test()