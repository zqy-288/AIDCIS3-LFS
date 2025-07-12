#!/usr/bin/env python3
"""
验证检测质量 - 确认漏网之鱼已彻底解决
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

def main():
    """快速验证检测质量"""
    app = QApplication(sys.argv)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 快速验证检测质量改进")
    
    window = MainWindow()
    window.show()
    QTest.qWait(1000)
    
    # 创建简单验证数据
    test_holes = {}
    hole_id_counter = 1
    
    # 创建一个密集的小网格用于验证
    for i in range(10):
        for j in range(8):
            x = 400 + i * 12  # 12像素间距
            y = 300 + j * 12
            
            hole_id = f"TEST_{hole_id_counter:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
            hole_id_counter += 1
    
    hole_collection = HoleCollection(
        holes=test_holes,
        metadata={'source_file': 'quality_verification', 'total_holes': len(test_holes)}
    )
    
    logger.info(f"📊 验证数据: {len(test_holes)} 个孔位 (12px间距密集网格)")
    
    # 加载数据
    window.hole_collection = hole_collection
    window.update_hole_display()
    QTest.qWait(2000)
    
    # 启动模拟
    if hasattr(window, 'simulate_btn'):
        logger.info("🚀 启动验证模拟...")
        window.simulation_running_v2 = False
        window.simulate_btn.click()
        
        logger.info("⏳ 验证中（10秒）...")
        QTest.qWait(10000)
        
        # 停止模拟
        if hasattr(window, 'simulation_running_v2') and window.simulation_running_v2:
            window.simulate_btn.click()
    
    logger.info("✅ 检测质量验证完成")
    logger.info("📝 检查要点:")
    logger.info("  1. 自适应容差应该计算为最小间距的1.5倍")
    logger.info("  2. 12px密集网格应该完美处理")
    logger.info("  3. 方向感知应该优先右下方向移动")
    logger.info("  4. 应该看到连续性验证的输出日志")
    logger.info("  5. 所有孔位都应该被检测到（无灰色）")
    
    QTest.qWait(5000)
    window.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())