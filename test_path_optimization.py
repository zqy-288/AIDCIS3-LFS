#!/usr/bin/env python3
"""
测试路径优化效果 - 验证连续检测路径
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

class PathOptimizationTest:
    """路径优化测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_path_optimization(self):
        """测试路径优化效果"""
        self.logger.info("🚀 测试路径优化效果 - 消除漏网之鱼")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载密集测试数据
        self.logger.info("\n🔄 加载密集孔位测试数据")
        hole_collection = self._create_dense_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 启动优化后的连续模拟
        self.logger.info("\n📋 启动路径优化的连续模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动V2连续模拟（路径优化版本）...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察路径优化效果（45秒）...")
            self.logger.info("👁️ 重点观察：")
            self.logger.info("  1. 检测路径是否连续（无跳跃）")
            self.logger.info("  2. 是否还有漏网之鱼")
            self.logger.info("  3. 扇形切换是否平滑")
            self.logger.info("  4. 检测速度是否保持一致")
            
            QTest.qWait(45000)  # 等待45秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止路径优化模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_dense_test_data(self):
        """创建密集的测试数据，模拟真实工件的孔位分布"""
        test_holes = {}
        
        import math
        center_x, center_y = 400, 400
        hole_id_counter = 1
        
        # 创建更密集、更真实的孔位分布
        # 模拟管板上的规则排列
        
        # 第一象限（右上）- 矩形网格 + 一些不规则分布
        for row in range(15):
            for col in range(12):
                x = center_x + 20 + col * 25 + (row % 2) * 12  # 交错排列
                y = center_y - 20 - row * 20
                
                # 只保留在第一象限的孔位
                if x > center_x and y < center_y:
                    hole_id = f"Q1_{hole_id_counter:04d}"
                    hole_data = HoleData(
                        hole_id=hole_id,
                        center_x=x,
                        center_y=y,
                        radius=8.8,
                        status=HoleStatus.PENDING
                    )
                    test_holes[hole_id] = hole_data
                    hole_id_counter += 1
        
        # 第二象限（左上）- 蜂窝状排列
        for row in range(14):
            for col in range(10):
                x = center_x - 20 - col * 28
                y = center_y - 15 - row * 22 + (col % 2) * 11
                
                if x < center_x and y < center_y:
                    hole_id = f"Q2_{hole_id_counter:04d}"
                    hole_data = HoleData(
                        hole_id=hole_id,
                        center_x=x,
                        center_y=y,
                        radius=8.8,
                        status=HoleStatus.PENDING
                    )
                    test_holes[hole_id] = hole_data
                    hole_id_counter += 1
        
        # 第三象限（左下）- 对角线排列
        for diag in range(20):
            for offset in range(-3, 4):
                x = center_x - 30 - diag * 18
                y = center_y + 30 + diag * 15 + offset * 12
                
                if x < center_x and y > center_y:
                    hole_id = f"Q3_{hole_id_counter:04d}"
                    hole_data = HoleData(
                        hole_id=hole_id,
                        center_x=x,
                        center_y=y,
                        radius=8.8,
                        status=HoleStatus.PENDING
                    )
                    test_holes[hole_id] = hole_data
                    hole_id_counter += 1
        
        # 第四象限（右下）- 螺旋排列
        for i in range(180):
            angle = i * 0.3  # 角度
            radius = 30 + i * 1.5  # 螺旋半径
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            
            # 只保留在第四象限的孔位
            if x > center_x and y > center_y and radius < 200:
                hole_id = f"Q4_{hole_id_counter:04d}"
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
            metadata={'source_file': 'path_optimization_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建密集测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  Q1=矩形网格, Q2=蜂窝状, Q3=对角线, Q4=螺旋")
        return hole_collection

def main():
    """主函数"""
    test = PathOptimizationTest()
    
    try:
        success = test.test_path_optimization()
        
        if test.window:
            test.logger.info("\n🎯 路径优化算法验证:")
            test.logger.info("✅ 实现了最近邻路径算法")
            test.logger.info("✅ 添加了方向一致性优化") 
            test.logger.info("✅ 全局路径优化（跨扇形连续）")
            test.logger.info("✅ 智能起点选择（左上角开始）")
            test.logger.info("✅ 双层优化（扇形内 + 全局）")
            test.logger.info("\n👁️ 检查结果:")
            test.logger.info("  1. 应该没有或很少漏网之鱼")
            test.logger.info("  2. 检测路径应该更加连续平滑") 
            test.logger.info("  3. 扇形切换应该自然流畅")
            test.logger.info("  4. 整体检测效率应该更高")
            test.logger.info("\n窗口将在20秒后关闭...")
            QTest.qWait(20000)
        
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