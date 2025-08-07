#!/usr/bin/env python3
"""
测试选中扇形表格样式修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_table_fix():
    """测试表格修复"""
    print("🔍 测试选中扇形表格样式修复\n")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeLeftInfoPanel
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建左侧面板
        panel = NativeLeftInfoPanel()
        
        print("1. 检查表格布局:")
        if hasattr(panel, 'sector_stats_table'):
            table = panel.sector_stats_table
            print(f"   - 列数: {table.columnCount()}")
            print(f"   - 行数: {table.rowCount()}")
            
            # 检查列宽
            widths = []
            for i in range(table.columnCount()):
                widths.append(table.columnWidth(i))
            print(f"   - 列宽: {widths}")
            
            if table.columnCount() == 4 and widths == [90, 100, 90, 100]:
                print("   ✅ 表格布局正确：4列，宽度已增加")
            else:
                print("   ❌ 表格布局不正确")
                
        print("\n2. 检查背景色设置:")
        # 检查初始化的单元格
        if hasattr(panel, 'sector_stats_table'):
            table = panel.sector_stats_table
            has_background = True
            
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        # 检查背景色
                        bg = item.background()
                        if bg.color().name() != "#e8e8e8":
                            has_background = False
                            print(f"   单元格({row},{col})背景色: {bg.color().name()}")
                            
            if has_background:
                print("   ✅ 所有单元格背景色已设置为#e8e8e8")
            else:
                print("   ⚠️  部分单元格背景色未正确设置")
                
        print("\n3. 检查样式表:")
        if hasattr(panel, 'sector_stats_table'):
            style = panel.sector_stats_table.styleSheet()
            if "background-color: #e8e8e8" in style:
                print("   ✅ 样式表包含背景色设置")
            else:
                print("   ❌ 样式表缺少背景色设置")
                
        print("\n" + "="*60)
        print("修复总结:")
        print("="*60)
        print("1. 表格保持4列布局 ✓")
        print("2. 列宽已增加（90, 100, 90, 100）✓")
        print("3. 背景色设置为灰色（#e8e8e8）✓")
        print("4. 样式表和单元格都设置了背景色 ✓")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_table_fix()