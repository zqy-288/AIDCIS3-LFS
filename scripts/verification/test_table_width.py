#!/usr/bin/env python3
"""测试扇形统计表格宽度调整"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView

def test_table_width():
    """测试表格宽度调整"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("扇形统计表格宽度测试")
    view.resize(1400, 900)
    view.show()
    
    # 设置一些测试数据
    if view.left_panel and hasattr(view.left_panel, 'sector_stats_table'):
        table = view.left_panel.sector_stats_table
        
        # 更新一些测试数据
        test_data = {
            (0, 1): "6356",  # 待检
            (0, 3): "0",     # 合格
            (1, 1): "0",     # 异常
            (1, 3): "0",     # 盲孔
            (2, 1): "0",     # 拉杆
            (2, 3): "6356"   # 总计
        }
        
        for (row, col), value in test_data.items():
            item = table.item(row, col)
            if item:
                item.setText(value)
    
    print("""
    ========== 表格宽度调整 ==========
    已调整：
    - 状态列宽度: 45px → 60px
    - 数量列宽度: 50px → 65px
    - 字体大小: 10px → 11px
    - 单元格内边距: 2px → 4px
    - 添加了表头样式
    
    总表格宽度: 约 250px
    ==================================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_table_width()