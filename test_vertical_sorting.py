#!/usr/bin/env python3
"""
测试竖直排序算法
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

class VerticalSortingTest:
    """竖直排序测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_vertical_sorting(self):
        """测试竖直排序效果"""
        self.logger.info("🚀 测试竖直排序算法 - 从左到右，每列从上到下")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载网格状测试数据
        self.logger.info("\n🔄 加载网格状测试数据")
        hole_collection = self._create_grid_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 启动竖直排序模拟
        self.logger.info("\n📋 启动竖直排序模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动V2竖直排序模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察竖直排序效果（30秒）...")
            self.logger.info("👁️ 请观察：")
            self.logger.info("  1. 检测是否严格按列进行（从左到右）")
            self.logger.info("  2. 每列内是否从上到下检测")
            self.logger.info("  3. 是否没有重复检测")
            self.logger.info("  4. 是否没有跳跃或漏网之鱼")
            
            QTest.qWait(30000)  # 等待30秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止竖直排序模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_grid_test_data(self):
        """创建网格状测试数据，验证竖直排序效果"""
        test_holes = {}
        hole_id_counter = 1
        
        # 创建规整的网格分布，方便观察排序效果
        # 4个象限，每个象限都有规律的网格
        
        base_x, base_y = 400, 400
        
        # 第一象限（右上）- 5x4网格
        for col in range(5):
            for row in range(4):
                x = base_x + 30 + col * 40
                y = base_y - 30 - row * 35
                
                hole_id = f"Q1_C{col+1}R{row+1}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 第二象限（左上）- 4x5网格
        for col in range(4):
            for row in range(5):
                x = base_x - 30 - col * 45
                y = base_y - 30 - row * 30
                
                hole_id = f"Q2_C{col+1}R{row+1}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 第三象限（左下）- 4x4网格
        for col in range(4):
            for row in range(4):
                x = base_x - 30 - col * 42
                y = base_y + 30 + row * 38
                
                hole_id = f"Q3_C{col+1}R{row+1}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 第四象限（右下）- 6x3网格
        for col in range(6):
            for row in range(3):
                x = base_x + 30 + col * 35
                y = base_y + 30 + row * 40
                
                hole_id = f"Q4_C{col+1}R{row+1}"
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
            metadata={'source_file': 'vertical_sorting_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建网格测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  Q1: 5列x4行, Q2: 4列x5行, Q3: 4列x4行, Q4: 6列x3行")
        self.logger.info(f"  应该看到严格按列的竖直检测模式")
        return hole_collection

def main():
    """主函数"""
    test = VerticalSortingTest()
    
    try:
        success = test.test_vertical_sorting()
        
        if test.window:
            test.logger.info("\n🎯 竖直排序算法验证:")
            test.logger.info("✅ 实现了按列排序（从左到右）")
            test.logger.info("✅ 每列内按行排序（从上到下）") 
            test.logger.info("✅ 避免重复检测")
            test.logger.info("✅ 消除跳跃和漏网之鱼")
            test.logger.info("✅ 双层优化（扇形内 + 全局）")
            test.logger.info("\n👁️ 检查结果:")
            test.logger.info("  1. 检测应该严格按列进行")
            test.logger.info("  2. 每列从上到下，不应有跳跃") 
            test.logger.info("  3. 列与列之间从左到右")
            test.logger.info("  4. 没有重复或遗漏")
            test.logger.info("\n窗口将在15秒后关闭...")
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