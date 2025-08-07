#!/usr/bin/env python3
"""测试扇形统计表格显示修复"""

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

def test_sector_stats_display():
    """测试扇形统计表格显示"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("扇形统计表格显示测试")
    view.resize(1400, 900)
    view.show()
    
    def check_stats():
        """检查统计显示"""
        if view.left_panel:
            logging.info("=== 状态统计（整体）===")
            if hasattr(view.left_panel, 'total_label'):
                logging.info(f"总数标签: {view.left_panel.total_label.text()}")
            
            logging.info("\n=== 扇形统计表格 ===")
            if hasattr(view.left_panel, 'sector_stats_table'):
                table = view.left_panel.sector_stats_table
                logging.info(f"当前扇形: {view.left_panel.current_sector_label.text()}")
                
                # 读取表格内容
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            row_data.append(item.text())
                    logging.info(f"第{row+1}行: {row_data}")
                
                # 检查数据合理性
                if table.item(0, 1):  # 待检数量
                    pending = int(table.item(0, 1).text())
                    if table.item(2, 3):  # 总计
                        total = int(table.item(2, 3).text())
                        if pending > total:
                            logging.warning(f"⚠️ 数据异常：待检({pending}) > 总计({total})")
                        else:
                            logging.info(f"✅ 数据正常：待检({pending}) <= 总计({total})")
    
    def simulate_sector_click():
        """模拟点击扇形"""
        if view.coordinator:
            from src.core_business.graphics.sector_types import SectorQuadrant
            # 模拟点击扇形1
            view.coordinator._on_panorama_sector_clicked(SectorQuadrant.SECTOR_1)
            logging.info("已模拟点击扇形1")
            
            # 2秒后检查
            QTimer.singleShot(2000, check_stats)
    
    # 延迟执行
    QTimer.singleShot(2000, check_stats)
    
    logging.info("""
    ========== 测试步骤 ==========
    1. 点击"加载DXF文件"按钮
    2. 选择CAP1000.dxf文件
    3. 观察扇形统计表格是否显示合理的数据
    4. 点击全景图中的不同扇形
    5. 验证表格数据是否正确更新
    
    预期结果：
    - 待检数量应该小于等于扇形总计
    - 扇形总计应该是该扇形的实际孔位数
    - 不应该显示整体统计数据
    ==============================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_sector_stats_display()