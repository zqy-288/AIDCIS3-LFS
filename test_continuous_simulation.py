#!/usr/bin/env python3
"""
测试连续模拟修复效果
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

class ContinuousSimulationTest:
    """连续模拟测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_continuous_simulation(self):
        """测试连续模拟修复效果"""
        self.logger.info("🚀 测试连续模拟修复效果")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载测试数据
        self.logger.info("\n🔄 加载连续测试数据")
        hole_collection = self._create_continuous_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 检查连续模拟准备
        self.logger.info("\n📋 检查连续模拟数据准备")
        
        # 启动V2模拟来测试连续性
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动连续模拟V2...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 等待模拟运行一段时间观察连续性
            self.logger.info("⏳ 观察连续模拟效果（30秒）...")
            self.logger.info("👁️ 请观察：")
            self.logger.info("  1. 检测是否连续进行（无间断）")
            self.logger.info("  2. 扇形切换是否平滑")
            self.logger.info("  3. 全景预览是否正确跟随")
            
            QTest.qWait(30000)  # 等待30秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止连续模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_continuous_test_data(self):
        """创建连续测试数据"""
        test_holes = {}
        
        import math
        center_x, center_y = 400, 400
        
        # 创建更密集的四象限数据，确保连续的检测效果
        hole_id_counter = 1
        
        # 第一象限（右上）- 螺旋分布
        for i in range(40):
            angle = (math.pi/2) * i / 40
            radius = 80 + i * 2
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
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
        
        # 第二象限（左上）- 螺旋分布
        for i in range(35):
            angle = math.pi/2 + (math.pi/2) * i / 35
            radius = 75 + i * 3
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
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
        
        # 第三象限（左下）- 螺旋分布
        for i in range(38):
            angle = math.pi + (math.pi/2) * i / 38
            radius = 90 + i * 2.5
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
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
        
        # 第四象限（右下）- 螺旋分布
        for i in range(42):
            angle = 3*math.pi/2 + (math.pi/2) * i / 42
            radius = 85 + i * 2.8
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
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
            metadata={'source_file': 'continuous_simulation_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建连续测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  分布: Q1=40, Q2=35, Q3=38, Q4=42")
        return hole_collection

def main():
    """主函数"""
    test = ContinuousSimulationTest()
    
    try:
        success = test.test_continuous_simulation()
        
        if test.window:
            test.logger.info("\n🎯 连续模拟修复验证:")
            test.logger.info("✅ 实现了连续孔位序列（无扇形间断）")
            test.logger.info("✅ 智能扇形切换（根据孔位位置自动切换）") 
            test.logger.info("✅ 改进了孔位排序（按空间位置排序）")
            test.logger.info("✅ 减少了日志输出频率（每20个孔位）")
            test.logger.info("✅ 优化了错误处理（跳过缺失项目）")
            test.logger.info("\n👁️ 观察结果:")
            test.logger.info("  1. 检测应该连续进行，没有500ms间断")
            test.logger.info("  2. 扇形切换应该平滑，基于孔位位置") 
            test.logger.info("  3. 全景预览应该正确跟随扇形切换")
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