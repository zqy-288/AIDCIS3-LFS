#!/usr/bin/env python3
"""
测试扇形统计表格更新功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_sector_stats_update():
    """测试扇形统计表格更新"""
    print("🔍 测试扇形统计表格更新功能\n")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeLeftInfoPanel
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建左侧面板
        panel = NativeLeftInfoPanel()
        panel.show()
        
        print("1. 检查表格初始状态:")
        if hasattr(panel, 'sector_stats_table'):
            table = panel.sector_stats_table
            print(f"   - 表格高度: {table.height()} (应该是约76像素)")
            print(f"   - 行高: {table.verticalHeader().defaultSectionSize()} (应该是24像素)")
            
            # 读取初始值
            print("\n   初始值:")
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        row_data.append(item.text())
                print(f"   第{row+1}行: {row_data}")
                
        print("\n2. 测试更新功能:")
        # 模拟更新数据
        test_data = {
            'pending': 100,
            'qualified': 200,
            'defective': 50,
            'total': 350
        }
        
        print(f"   发送测试数据: {test_data}")
        panel.update_sector_stats(test_data)
        
        # 等待一下让更新生效
        app.processEvents()
        
        print("\n   更新后的值:")
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    row_data.append(item.text())
            print(f"   第{row+1}行: {row_data}")
            
        # 检查是否正确更新
        if table.item(0, 1).text() == "100" and table.item(0, 3).text() == "200":
            print("\n   ✅ 表格更新成功！")
        else:
            print("\n   ❌ 表格更新失败！")
            
        print("\n3. 测试样式:")
        print(f"   - 背景色: {table.palette().color(table.palette().ColorRole.Base).name()}")
        print(f"   - 表格固定高度: {table.height()}像素")
        
        # 保持窗口打开一会儿
        print("\n保持窗口打开3秒...")
        QTimer.singleShot(3000, app.quit)
        app.exec()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sector_stats_update()