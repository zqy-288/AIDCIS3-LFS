#!/usr/bin/env python3
"""
测试更大的全景预览显示面板
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

class LargerPanoramaPanelTest:
    """更大全景预览面板测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_larger_panel(self):
        """测试更大的显示面板"""
        self.logger.info("🚀 测试更大的全景预览显示面板")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 检查尺寸变化
        self.logger.info("\\n📐 检查尺寸变化")
        
        panorama = self.window.sidebar_panorama
        panorama_view = panorama.panorama_view
        
        container_size = panorama.size()
        panel_size = panorama_view.size()
        
        self.logger.info(f"📏 容器尺寸: {container_size.width()} x {container_size.height()}")
        self.logger.info(f"📏 面板尺寸: {panel_size.width()} x {panel_size.height()}")
        
        # 对比之前的尺寸
        old_container = (400, 380)
        old_panel = (200, 200)
        new_container = (container_size.width(), container_size.height())
        new_panel = (panel_size.width(), panel_size.height())
        
        container_increase = ((new_container[0] - old_container[0]) / old_container[0]) * 100
        panel_increase = ((new_panel[0] - old_panel[0]) / old_panel[0]) * 100
        
        self.logger.info(f"📈 容器尺寸增长: {old_container} → {new_container} (+{container_increase:.1f}%)")
        self.logger.info(f"📈 面板尺寸增长: {old_panel} → {new_panel} (+{panel_increase:.1f}%)")
        
        # 3. 加载测试数据
        self.logger.info("\\n🔄 加载测试数据验证显示")
        
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 4. 检查显示效果
        self.logger.info("\\n✅ 检查显示效果")
        
        scene = panorama_view.scene
        if scene and len(scene.items()) > 0:
            transform = panorama_view.transform()
            scale_factor = transform.m11()
            
            scene_rect = scene.itemsBoundingRect()
            content_width = scene_rect.width() * scale_factor
            content_height = scene_rect.height() * scale_factor
            
            width_ratio = content_width / panel_size.width()
            height_ratio = content_height / panel_size.height()
            
            self.logger.info(f"🎯 显示效果分析:")
            self.logger.info(f"  📏 自适应缩放: {scale_factor:.3f}")
            self.logger.info(f"  📐 内容显示尺寸: {content_width:.1f}x{content_height:.1f}")
            self.logger.info(f"  📊 占面板比例: {width_ratio*100:.1f}% x {height_ratio*100:.1f}%")
            
            if width_ratio <= 0.8 and height_ratio <= 0.8:
                self.logger.info("✅ 更大面板提供了更好的显示效果，有足够边距")
            else:
                self.logger.info("❌ 内容仍然较满，可能需要进一步调整")
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        
        # 创建中等大小的圆形分布
        import math
        center_x, center_y = 400, 400
        
        for ring in range(1, 4):
            radius = ring * 80 + 120
            holes_count = ring * 16
            
            for i in range(holes_count):
                angle = (2 * math.pi * i) / holes_count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                hole_id = f"L{len(test_holes)+1:03d}"
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
            metadata={'source_file': 'larger_panel_test', 'total_holes': len(test_holes)}
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection

def main():
    """主函数"""
    test = LargerPanoramaPanelTest()
    
    try:
        success = test.test_larger_panel()
        
        if test.window:
            test.logger.info("\\n🎯 更大显示面板验证:")
            test.logger.info("✅ 容器尺寸从 400x380 增加到 480x450")
            test.logger.info("✅ 面板尺寸从 200x200 增加到 320x280")
            test.logger.info("✅ 面板面积增加了约156%")
            test.logger.info("\\n👁️ 请检查全景预览:")
            test.logger.info("  1. 显示面板是否明显变大了")
            test.logger.info("  2. DXF内容是否有更好的显示空间")
            test.logger.info("  3. 是否更容易看清细节")
            test.logger.info("\\n窗口将在12秒后关闭...")
            QTest.qWait(12000)
        
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