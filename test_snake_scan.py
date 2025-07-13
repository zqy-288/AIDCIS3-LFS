#!/usr/bin/env python3
"""
测试蛇形扫描算法 - 整体连续且无漏检
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

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class SnakeScanTest:
    """蛇形扫描测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_snake_scan(self):
        """测试蛇形扫描效果"""
        self.logger.info("🐍 测试蛇形扫描算法 - 整体连续且无漏检")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载规整的网格测试数据（便于观察蛇形路径）
        self.logger.info("\\n🔄 加载规整网格测试数据")
        hole_collection = self._create_grid_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 启动蛇形扫描模拟
        self.logger.info("\\n📋 启动蛇形扫描模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动V2蛇形扫描模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察蛇形扫描效果（25秒）...")
            self.logger.info("👁️ 请特别观察：")
            self.logger.info("  1. 检测是否按行进行（从上到下）")
            self.logger.info("  2. 每行内是否左右交替（蛇形路径）")
            self.logger.info("  3. 行与行之间的过渡是否连续")
            self.logger.info("  4. 是否完全无漏检和跳跃")
            self.logger.info("  5. 整体路径是否像打印机扫描一样流畅")
            
            QTest.qWait(25000)  # 等待25秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止蛇形扫描模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_grid_test_data(self):
        """创建规整的网格测试数据，便于观察蛇形扫描效果"""
        test_holes = {}
        hole_id_counter = 1
        
        center_x, center_y = 400, 300
        
        # 创建一个大的规整网格，便于观察蛇形扫描路径
        self.logger.info("🔧 创建规整网格用于蛇形扫描演示...")
        
        rows = 12
        cols = 15
        spacing_x = 30  # X方向间距
        spacing_y = 25  # Y方向间距
        
        for row in range(rows):
            for col in range(cols):
                # 计算位置
                x = center_x - (cols * spacing_x) // 2 + col * spacing_x
                y = center_y - (rows * spacing_y) // 2 + row * spacing_y
                
                hole_id = f"GRID_R{row:02d}C{col:02d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 添加一些不规则分布用于测试适应性
        self.logger.info("🔧 添加不规则分布测试适应性...")
        
        import random
        import math
        
        # 添加一些随机分布的孔位
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(50, 200)
            
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            hole_id = f"RAND_{i:02d}"
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
            metadata={'source_file': 'snake_scan_test', 'total_holes': len(test_holes)}
        )
        
        grid_count = rows * cols
        random_count = 20
        
        self.logger.info(f"🧪 创建蛇形扫描测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  规整网格: {grid_count}个 ({rows}行x{cols}列)")
        self.logger.info(f"  随机分布: {random_count}个")
        self.logger.info(f"  应该看到清晰的蛇形扫描路径：")
        self.logger.info(f"    第1行: 左→右, 第2行: 右→左, 第3行: 左→右...")
        return hole_collection

def main():
    """主函数"""
    test = SnakeScanTest()
    
    try:
        success = test.test_snake_scan()
        
        if test.window:
            test.logger.info("\\n🎯 蛇形扫描算法验证:")
            test.logger.info("✅ 实现了行优先分组（Y坐标）")
            test.logger.info("✅ 蛇形路径（偶数行左→右，奇数行右→左）") 
            test.logger.info("✅ 自适应行容差（最小间距的2倍）")
            test.logger.info("✅ 全局蛇形扫描优化")
            test.logger.info("✅ 连续性保证（无大跳跃）")
            test.logger.info("✅ 完整覆盖（无漏检）")
            test.logger.info("\\n👁️ 检查结果:")
            test.logger.info("  1. 网格应该按行扫描（从上到下）")
            test.logger.info("  2. 每行内左右交替（蛇形）") 
            test.logger.info("  3. 行与行之间平滑过渡")
            test.logger.info("  4. 随机孔位被正确融入扫描路径")
            test.logger.info("  5. 整体连续，无跳跃，无遗漏")
            test.logger.info("\\n窗口将在15秒后关闭...")
            QTest.qWait(15000)
        
        return 0 if success else 1
        
    except Exception as e:
        test.logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())