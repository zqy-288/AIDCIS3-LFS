#!/usr/bin/env python3
"""测试简化后的扇形统计表格"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView

def test_simplified_table():
    """测试简化后的表格"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("简化扇形统计表格测试")
    view.resize(1400, 900)
    view.show()
    
    # 设置测试数据
    if view.left_panel and hasattr(view.left_panel, 'update_sector_stats'):
        test_data = {
            'pending': 6356,    # 待检
            'qualified': 0,     # 合格
            'defective': 0,     # 异常
            'total': 6356       # 总计
        }
        view.left_panel.update_sector_stats(test_data)
        view.left_panel.current_sector_label.setText("当前扇形: sector_1")
    
    print("""
    ========== 简化后的表格 ==========
    已移除：
    - 盲孔行
    - 拉杆行
    
    保留：
    第1行：待检 | 数量 | 合格 | 数量
    第2行：异常 | 数量 | 总计 | 数量
    
    表格高度：80-100px（原100-120px）
    ==================================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_simplified_table()