#!/usr/bin/env python3
"""诊断扇形统计总数问题"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
from src.core_business.graphics.sector_types import SectorQuadrant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def diagnose_sector_total():
    """诊断扇形统计总数"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("扇形统计总数诊断")
    view.resize(1400, 900)
    view.show()
    
    def check_after_load():
        """加载后检查"""
        if view.coordinator and view.coordinator.sector_holes_map:
            logging.info("\n=== 扇形孔位分配 ===")
            for sector, holes in view.coordinator.sector_holes_map.items():
                logging.info(f"{sector.value}: {len(holes)} 个孔位")
            
            # 检查当前扇形统计
            if view.coordinator.current_sector:
                current_holes = view.coordinator.get_current_sector_holes()
                logging.info(f"\n当前扇形 {view.coordinator.current_sector.value}: {len(current_holes)} 个孔位")
            
            # 检查表格显示
            if view.left_panel and hasattr(view.left_panel, 'sector_stats_table'):
                table = view.left_panel.sector_stats_table
                logging.info("\n=== 扇形统计表格内容 ===")
                for row in range(table.rowCount()):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            row_data.append(item.text())
                    logging.info(f"第{row+1}行: {row_data}")
                
                # 特别检查总计值
                if table.item(1, 3):  # 总计在第2行第4列
                    total_text = table.item(1, 3).text()
                    logging.info(f"\n表格中的总计值: {total_text}")
                    
                    # 如果总计值大于10000，说明可能是整体统计
                    if total_text.isdigit() and int(total_text) > 10000:
                        logging.warning("⚠️ 总计值异常大，可能显示的是整体统计而不是扇形统计！")
    
    def simulate_sector_click():
        """模拟点击扇形并检查"""
        if view.coordinator:
            # 清空当前扇形，强制重新选择
            view.coordinator.current_sector = None
            
            # 模拟点击扇形1
            logging.info("\n=== 模拟点击扇形1 ===")
            view.coordinator._on_panorama_sector_clicked(SectorQuadrant.SECTOR_1)
            
            # 延迟检查结果
            QTimer.singleShot(500, check_after_load)
    
    # 延迟执行
    QTimer.singleShot(3000, simulate_sector_click)
    
    logging.info("""
    ========== 诊断步骤 ==========
    1. 加载CAP1000.dxf文件
    2. 等待3秒后自动模拟点击扇形1
    3. 检查扇形统计表格的总计值
    
    预期：
    - sector_1应该有约6356个孔位
    - 表格总计应该显示6356，而不是25270
    ==============================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    diagnose_sector_total()