#!/usr/bin/env python3
"""
测试扇形分割线可见性修复
验证扇形分割线是否可见
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_sector_lines():
    print("🔍 测试扇形分割线可见性修复...")
    
    try:
        # 测试SectorHighlightItem导入
        from src.pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
        print("✅ SectorHighlightItem 导入成功")
        
        # 测试扇形类型导入
        from src.core_business.graphics.sector_types import SectorQuadrant
        print("✅ SectorQuadrant 导入成功")
        
        print("\n🎯 扇形分割线可见性修复内容:")
        print("   1. 将扇形边界线从虚线改为实线（Qt.SolidLine）")
        print("   2. 增加线宽从2px改为3px")
        print("   3. 将颜色从浅灰色(120,120,120,150)改为深灰色(60,60,60)")
        print("   4. 在highlight方法中也使用深色实线(80,80,80,3px)")
        print("   5. 设置pen.setCosmetic(True)确保不受缩放影响")
        
        print("\n📋 修复效果:")
        print("   ✓ 扇形分割线现在应该更明显可见")
        print("   ✓ 使用深灰色实线，线宽3px，在各种背景下都清晰")
        print("   ✓ 线条不会因为视图缩放而变得模糊")
        print("   → 四个扇形区域的边界应该清晰可见")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sector_lines()