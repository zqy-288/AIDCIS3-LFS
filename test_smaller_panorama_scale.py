#!/usr/bin/env python3
"""
验证更小全景预览缩放的测试脚本
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

class SmallerPanoramaScaleTest:
    """更小全景预览缩放测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_smaller_scale(self):
        """测试更小的缩放比例"""
        self.logger.info("🚀 测试全景预览更小缩放比例")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 检查全景预览尺寸
        self.logger.info("\\n📐 检查全景预览尺寸")
        
        panorama = self.window.sidebar_panorama
        panorama_view = panorama.panorama_view
        
        container_size = panorama.size()
        view_size = panorama_view.size()
        
        self.logger.info(f"📏 容器尺寸: {container_size.width()} x {container_size.height()}")
        self.logger.info(f"📏 视图尺寸: {view_size.width()} x {view_size.height()}")
        
        # 3. 加载测试数据
        self.logger.info("\\n🔄 加载测试数据")
        
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(4000)
        
        # 4. 检查缩放效果
        self.logger.info("\\n🎯 检查缩放效果")
        
        scene = panorama_view.scene
        if scene and len(scene.items()) > 0:
            # 获取变换信息
            transform = panorama_view.transform()
            scale_factor = transform.m11()
            
            # 获取场景边界
            scene_rect = scene.itemsBoundingRect()
            
            # 计算内容在视图中的实际尺寸
            content_width = scene_rect.width() * scale_factor
            content_height = scene_rect.height() * scale_factor
            
            # 计算占用比例
            width_ratio = content_width / view_size.width()
            height_ratio = content_height / view_size.height()
            
            self.logger.info(f"📊 缩放分析:")
            self.logger.info(f"  📏 缩放比例: {scale_factor:.3f}")
            self.logger.info(f"  📦 场景原始尺寸: {scene_rect.width():.1f} x {scene_rect.height():.1f}")
            self.logger.info(f"  📐 内容显示尺寸: {content_width:.1f} x {content_height:.1f}")
            self.logger.info(f"  📊 占视图比例: {width_ratio*100:.1f}% x {height_ratio*100:.1f}%")
            
            # 评估效果
            if scale_factor <= 0.3 and width_ratio <= 0.7 and height_ratio <= 0.7:
                self.logger.info("✅ 全景预览DXF内容现在足够小，留有充足边距")
            elif scale_factor <= 0.3:
                self.logger.info("✅ 缩放比例合适，但可能需要调整视图尺寸")
            else:
                self.logger.info("❌ 全景预览DXF内容仍然较大")
                
            # 检查是否居中
            scene_center = scene_rect.center()
            scene_center_in_view = panorama_view.mapFromScene(scene_center)
            view_center_x = view_size.width() / 2
            view_center_y = view_size.height() / 2
            
            offset_x = abs(scene_center_in_view.x() - view_center_x)
            offset_y = abs(scene_center_in_view.y() - view_center_y)
            
            self.logger.info(f"  🎯 居中偏差: X={offset_x:.1f}px, Y={offset_y:.1f}px")
            
            if offset_x <= 10 and offset_y <= 10:
                self.logger.info("✅ 内容已正确居中")
            else:
                self.logger.info("❌ 内容未正确居中")
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        
        # 创建一个中等大小的圆形分布
        import math
        center_x, center_y = 400, 400
        
        for ring in range(1, 5):  # 4个圆
            radius = ring * 70 + 120  # 从190开始
            holes_count = ring * 20
            
            for i in range(holes_count):
                angle = (2 * math.pi * i) / holes_count
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                hole_id = f"H{len(test_holes)+1:05d}"
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
            metadata={
                'source_file': 'smaller_scale_test',
                'total_holes': len(test_holes)
            }
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection

def main():
    """主函数"""
    test = SmallerPanoramaScaleTest()
    
    try:
        success = test.test_smaller_scale()
        
        if test.window:
            test.logger.info("\\n👁️ 请观察全景预览效果：")
            test.logger.info("  1. DXF圆形图案是否变得更小了")
            test.logger.info("  2. 是否在200x200的框中留有更多空白边距")
            test.logger.info("  3. 内容是否居中显示")
            test.logger.info("\\n如果效果合适，这个修改就完成了")
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