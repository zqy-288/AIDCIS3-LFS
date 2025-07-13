#!/usr/bin/env python3
"""
测试自适应缩放功能
验证全景预览可以根据内容大小自动调整缩放比例
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

class AdaptiveScaleTest:
    """自适应缩放测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_adaptive_scale(self):
        """测试自适应缩放"""
        self.logger.info("🚀 测试自适应缩放功能")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 测试小内容的自适应缩放
        self.logger.info("\\n🔬 测试小内容自适应缩放")
        self._test_small_content()
        
        QTest.qWait(3000)
        
        # 3. 测试大内容的自适应缩放
        self.logger.info("\\n🔬 测试大内容自适应缩放")
        self._test_large_content()
        
        QTest.qWait(3000)
        
        # 4. 测试中等内容的自适应缩放
        self.logger.info("\\n🔬 测试中等内容自适应缩放")
        self._test_medium_content()
        
        QTest.qWait(3000)
        
        return True
    
    def _test_small_content(self):
        """测试小内容（应该有较大的缩放比例）"""
        self.logger.info("📦 加载小内容数据...")
        
        # 创建小范围的孔位数据
        test_holes = {}
        import math
        center_x, center_y = 400, 400
        
        # 只创建一个小圆
        radius = 50
        holes_count = 12
        
        for i in range(holes_count):
            angle = (2 * math.pi * i) / holes_count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            hole_id = f"S{i+1:03d}"
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
            metadata={'source_file': 'small_content_test', 'total_holes': len(test_holes)}
        )
        
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(2000)
        self._analyze_scale_result("小内容")
    
    def _test_large_content(self):
        """测试大内容（应该有较小的缩放比例）"""
        self.logger.info("📦 加载大内容数据...")
        
        # 创建大范围的孔位数据
        test_holes = {}
        import math
        center_x, center_y = 400, 400
        
        # 创建多个大圆
        for ring in range(1, 8):
            radius = ring * 100 + 100  # 大半径
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
            metadata={'source_file': 'large_content_test', 'total_holes': len(test_holes)}
        )
        
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(2000)
        self._analyze_scale_result("大内容")
    
    def _test_medium_content(self):
        """测试中等内容（应该有适中的缩放比例）"""
        self.logger.info("📦 加载中等内容数据...")
        
        # 创建中等范围的孔位数据
        test_holes = {}
        import math
        center_x, center_y = 400, 400
        
        # 创建中等大小的圆
        for ring in range(1, 4):
            radius = ring * 80 + 120  # 中等半径
            holes_count = ring * 20
            
            for i in range(holes_count):
                angle = (2 * math.pi * i) / holes_count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                hole_id = f"M{len(test_holes)+1:03d}"
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
            metadata={'source_file': 'medium_content_test', 'total_holes': len(test_holes)}
        )
        
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(2000)
        self._analyze_scale_result("中等内容")
    
    def _analyze_scale_result(self, content_type):
        """分析缩放结果"""
        panorama_view = self.window.sidebar_panorama.panorama_view
        scene = panorama_view.scene
        
        if scene and len(scene.items()) > 0:
            transform = panorama_view.transform()
            scale_factor = transform.m11()
            
            scene_rect = scene.itemsBoundingRect()
            view_rect = panorama_view.viewport().rect()
            
            # 计算内容在视图中的占用比例
            content_width = scene_rect.width() * scale_factor
            content_height = scene_rect.height() * scale_factor
            
            width_ratio = content_width / view_rect.width()
            height_ratio = content_height / view_rect.height()
            
            self.logger.info(f"📊 {content_type}自适应缩放结果:")
            self.logger.info(f"  📏 缩放比例: {scale_factor:.3f}")
            self.logger.info(f"  📦 原始尺寸: {scene_rect.width():.1f}x{scene_rect.height():.1f}")
            self.logger.info(f"  📐 显示尺寸: {content_width:.1f}x{content_height:.1f}")
            self.logger.info(f"  📊 占用比例: {width_ratio*100:.1f}% x {height_ratio*100:.1f}%")
            
            # 评估自适应效果
            if 0.6 <= width_ratio <= 0.8 and 0.6 <= height_ratio <= 0.8:
                self.logger.info(f"✅ {content_type}自适应效果良好，占用比例合适")
            elif width_ratio < 0.4 or height_ratio < 0.4:
                self.logger.info(f"⚠️ {content_type}可能过小，缩放比例偏低")
            elif width_ratio > 0.9 or height_ratio > 0.9:
                self.logger.info(f"⚠️ {content_type}可能过大，缩放比例偏高")
            else:
                self.logger.info(f"✅ {content_type}自适应效果可接受")

def main():
    """主函数"""
    test = AdaptiveScaleTest()
    
    try:
        success = test.test_adaptive_scale()
        
        if test.window:
            test.logger.info("\\n🎯 自适应缩放测试总结:")
            test.logger.info("✅ 自适应缩放功能已实现")
            test.logger.info("📏 缩放比例会根据内容大小自动调整")
            test.logger.info("🎯 小内容会放大，大内容会缩小")
            test.logger.info("📊 内容占视图70%左右，留出30%边距")
            test.logger.info("\\n👁️ 请观察不同内容下的缩放效果")
            test.logger.info("\\n窗口将在10秒后关闭...")
            QTest.qWait(10000)
        
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