#!/usr/bin/env python3
"""
测试模拟进度时全景预览同步
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

class SimulationSyncTest:
    """模拟进度同步测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_simulation_sync(self):
        """测试模拟进度同步"""
        self.logger.info("🚀 测试模拟进度时全景预览同步")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载测试数据
        self.logger.info("\n🔄 加载四象限测试数据")
        hole_collection = self._create_four_quadrant_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 检查全景预览初始状态
        self.logger.info("\n🎨 检查全景预览初始状态")
        panorama = self.window.sidebar_panorama
        
        if hasattr(panorama, 'sector_highlights') and panorama.sector_highlights:
            self.logger.info(f"✅ 全景预览有 {len(panorama.sector_highlights)} 个高亮项")
        else:
            self.logger.info("❌ 全景预览高亮项缺失，尝试手动创建")
            panorama._create_sector_highlights()
            QTest.qWait(1000)
        
        # 4. 手动测试扇形切换信号
        self.logger.info("\n📡 手动测试扇形切换信号")
        from aidcis2.graphics.sector_manager import SectorQuadrant
        
        for sector in [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]:
            self.logger.info(f"  🎯 手动切换到扇形: {sector.value}")
            # 直接调用主视图切换
            self.window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(1500)  # 等待足够时间观察变化
        
        # 5. 启动模拟进度测试
        self.logger.info("\n🎮 启动模拟进度测试")
        self.logger.info("请观察全景预览是否跟随扇形切换高亮...")
        
        # 点击模拟按钮
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 点击模拟进度按钮...")
            self.window.simulate_btn.click()
            
            # 等待模拟进度运行一段时间
            self.logger.info("⏳ 模拟进度运行中，观察全景预览是否跟随...")
            QTest.qWait(10000)  # 等待10秒观察
            
            # 停止模拟
            self.logger.info("⏹️ 停止模拟进度")
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.window.simulate_btn.click()  # 再次点击停止
        
        return True
    
    def _create_four_quadrant_data(self):
        """创建四象限测试数据"""
        test_holes = {}
        
        import math
        center_x, center_y = 400, 400
        
        # 第一象限（右上）- 更多孔位
        for i in range(30):
            angle = (math.pi/2) * i / 30
            radius = 80 + i * 3
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
            hole_id = f"Q1_{i+1:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
        
        # 第二象限（左上）
        for i in range(25):
            angle = math.pi/2 + (math.pi/2) * i / 25
            radius = 75 + i * 4
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
            hole_id = f"Q2_{i+1:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
        
        # 第三象限（左下）
        for i in range(28):
            angle = math.pi + (math.pi/2) * i / 28
            radius = 85 + i * 3.5
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
            hole_id = f"Q3_{i+1:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
        
        # 第四象限（右下）
        for i in range(32):
            angle = 3*math.pi/2 + (math.pi/2) * i / 32
            radius = 90 + i * 2.5
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            
            hole_id = f"Q4_{i+1:03d}"
            hole_data = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.8,
                status=HoleStatus.PENDING
            )
            test_holes[hole_id] = hole_data
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'simulation_sync_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建四象限测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  Q1(右上): 30个, Q2(左上): 25个, Q3(左下): 28个, Q4(右下): 32个")
        return hole_collection

def main():
    """主函数"""
    test = SimulationSyncTest()
    
    try:
        success = test.test_simulation_sync()
        
        if test.window:
            test.logger.info("\n🎯 模拟进度同步测试总结:")
            test.logger.info("✅ 添加了详细的调试日志")
            test.logger.info("✅ 实现了手动同步机制") 
            test.logger.info("✅ 增强了信号传播跟踪")
            test.logger.info("✅ 提供了四象限测试数据")
            test.logger.info("\n👁️ 观察要点:")
            test.logger.info("  1. 查看控制台日志中的扇形切换信号")
            test.logger.info("  2. 观察全景预览高亮区域是否变化")
            test.logger.info("  3. 模拟进度时左侧日志显示的同步状态")
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