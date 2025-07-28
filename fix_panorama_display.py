#!/usr/bin/env python3
"""
修复全景图显示问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QGraphicsView


def fix_panorama_viewport_update():
    """修复全景图视口更新模式"""
    print("🔧 修复全景图视口更新问题")
    print("=" * 40)
    
    # 修改 CompletePanoramaWidget 的设置
    file_path = "src/core_business/graphics/dynamic_sector_view.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找需要修改的行
    old_line = "self.panorama_view.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)"
    new_line = "self.panorama_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已将 MinimalViewportUpdate 改为 FullViewportUpdate")
        print("   这将确保旋转后的内容正确显示")
    else:
        print("❌ 未找到需要修改的代码")
    
    # 建议的其他修复
    print("\n💡 其他建议：")
    print("1. 在 load_complete_view 成功后，强制刷新视口：")
    print("   self.panorama_view.viewport().update()")
    print("   self.panorama_view.scene.update()")
    print("\n2. 在应用旋转后，触发重绘：")
    print("   self.panorama_view.repaint()")


if __name__ == "__main__":
    fix_panorama_viewport_update()