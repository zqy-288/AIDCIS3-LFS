#!/usr/bin/env python3
"""测试状态统计修复"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_stats_fix():
    """测试状态统计修复"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("状态统计修复测试")
    view.resize(1400, 900)
    view.show()
    
    def check_stats():
        """检查统计显示"""
        if view.left_panel:
            # 检查状态统计标签
            labels = {
                'total': view.left_panel.total_label,
                'qualified': view.left_panel.qualified_label,
                'unqualified': view.left_panel.unqualified_label,
                'pending': view.left_panel.not_detected_label,
                'blind': view.left_panel.blind_label,
                'tie_rod': view.left_panel.tie_rod_label
            }
            
            logging.info("=== 状态统计 ===")
            for name, label in labels.items():
                if label:
                    logging.info(f"{name}: {label.text()}")
            
            # 检查扇形统计表格
            if hasattr(view.left_panel, 'sector_stats_table'):
                table = view.left_panel.sector_stats_table
                logging.info("\n=== 扇形统计表格 ===")
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            header = table.horizontalHeaderItem(col)
                            row_data.append(header.text() if header else "")
                    logging.info(f"第{row+1}行: {row_data}")
            
            # 再次检查5秒后
            QTimer.singleShot(5000, check_stats)
    
    # 延迟检查，等待界面初始化
    QTimer.singleShot(2000, check_stats)
    
    logging.info("""
    ========== 测试步骤 ==========
    1. 点击"加载DXF文件"按钮
    2. 选择CAP1000.dxf文件
    3. 观察左侧状态统计是否显示正确的总数（25270）
    4. 观察扇形统计表格数据
    5. 可选：点击"开始模拟"测试运行中的统计更新
    ==============================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_stats_fix()