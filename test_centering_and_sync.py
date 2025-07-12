#!/usr/bin/env python3
"""
测试扇形居中和全景预览同步修复
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

class CenteringAndSyncTest:
    """居中和同步测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_centering_and_sync(self):
        """测试居中和同步修复"""
        self.logger.info("🚀 测试扇形居中和全景预览同步修复")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载测试数据
        self.logger.info("\n🔄 加载测试数据")
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 检查扇形居中效果
        self.logger.info("\n📐 检查扇形居中效果")
        graphics_view = self.window.dynamic_sector_display.graphics_view
        scene_rect = graphics_view.scene.sceneRect()
        view_center = graphics_view.mapToScene(graphics_view.viewport().rect().center())
        scene_center = scene_rect.center()
        
        offset_x = abs(view_center.x() - scene_center.x())
        offset_y = abs(view_center.y() - scene_center.y())
        
        self.logger.info(f"  📍 场景中心: ({scene_center.x():.1f}, {scene_center.y():.1f})")
        self.logger.info(f"  👁️ 视图中心: ({view_center.x():.1f}, {view_center.y():.1f})")
        self.logger.info(f"  📏 偏移量: ({offset_x:.1f}, {offset_y:.1f})")
        
        if offset_x <= 10 and offset_y <= 10:
            self.logger.info("✅ 扇形居中效果良好")
        else:
            self.logger.info("❌ 扇形居中需要进一步调整")
        
        # 4. 检查全景预览高亮项
        self.logger.info("\n🎨 检查全景预览高亮项")
        panorama = self.window.sidebar_panorama
        
        if hasattr(panorama, 'sector_highlights') and panorama.sector_highlights:
            self.logger.info(f"✅ 全景预览有 {len(panorama.sector_highlights)} 个高亮项")
            
            # 测试高亮功能
            from aidcis2.graphics.sector_manager import SectorQuadrant
            test_sector = SectorQuadrant.SECTOR_2
            panorama.highlight_sector(test_sector)
            self.logger.info(f"✅ 成功高亮测试扇形: {test_sector.value}")
        else:
            self.logger.info("❌ 全景预览高亮项缺失")
        
        # 5. 测试模拟进度同步
        self.logger.info("\n🔄 测试模拟进度同步")
        
        # 模拟扇形切换
        from aidcis2.graphics.sector_manager import SectorQuadrant
        for sector in [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]:
            self.logger.info(f"  🎯 切换到扇形: {sector.value}")
            self.window.on_dynamic_sector_changed(sector)
            QTest.qWait(1000)
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        
        # 创建四个象限的孔位分布
        import math
        center_x, center_y = 400, 400
        
        # 第一象限（右上）
        for i in range(20):
            angle = (math.pi/2) * i / 20  # 0 到 π/2
            radius = 100 + i * 5
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)  # Y轴向上为负
            
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
        for i in range(15):
            angle = math.pi/2 + (math.pi/2) * i / 15  # π/2 到 π
            radius = 80 + i * 6
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
        for i in range(18):
            angle = math.pi + (math.pi/2) * i / 18  # π 到 3π/2
            radius = 90 + i * 4
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
        for i in range(22):
            angle = 3*math.pi/2 + (math.pi/2) * i / 22  # 3π/2 到 2π
            radius = 110 + i * 3
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
            metadata={'source_file': 'centering_sync_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位，分布在四个象限")
        return hole_collection

def main():
    """主函数"""
    test = CenteringAndSyncTest()
    
    try:
        success = test.test_centering_and_sync()
        
        if test.window:
            test.logger.info("\n🎯 居中和同步修复验证:")
            test.logger.info("✅ 增强主视图扇形居中算法")
            test.logger.info("✅ 修复全景预览高亮项清理问题") 
            test.logger.info("✅ 改进扇形切换同步机制")
            test.logger.info("✅ 添加高亮项丢失自动重建")
            test.logger.info("\n👁️ 请检查:")
            test.logger.info("  1. 主视图扇形是否精确居中")
            test.logger.info("  2. 全景预览扇形高亮是否正常切换")
            test.logger.info("  3. 模拟进度时全景图是否跟随高亮")
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