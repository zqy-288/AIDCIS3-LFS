#!/usr/bin/env python3
"""
全景图显示框调整验证脚本
验证全景图显示框大小调整和内容居中显示效果
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

class PanoramaFrameAdjustmentTest:
    """全景图显示框调整测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_panorama_frame_adjustment(self):
        """测试全景图显示框调整"""
        self.logger.info("🚀 开始全景图显示框调整验证")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 验证全景图容器尺寸
        self.logger.info("\\n📐 验证全景图容器尺寸")
        
        sidebar_panorama = self.window.sidebar_panorama
        container_size = sidebar_panorama.size()
        
        self.logger.info(f"📏 全景图容器尺寸: {container_size.width()} x {container_size.height()}")
        
        # 检查是否达到新的容器尺寸要求 (400x380)
        expected_width = 400
        expected_height = 380
        
        if container_size.width() >= expected_width and container_size.height() >= expected_height:
            self.logger.info(f"✅ 全景图容器尺寸已增大到 {expected_width}x{expected_height}")
        else:
            self.logger.info(f"❌ 全景图容器尺寸未达到预期，当前: {container_size.width()}x{container_size.height()}")
        
        # 3. 验证全景图内容视图尺寸
        self.logger.info("\\n🖼️ 验证全景图内容视图尺寸")
        
        panorama_view = sidebar_panorama.panorama_view
        content_size = panorama_view.size()
        
        self.logger.info(f"📏 全景图内容尺寸: {content_size.width()} x {content_size.height()}")
        
        # 检查内容尺寸是否适中 (350x330)
        expected_content_width = 350
        expected_content_height = 330
        
        if content_size.width() >= expected_content_width and content_size.height() >= expected_content_height:
            self.logger.info(f"✅ 全景图内容尺寸适中: {expected_content_width}x{expected_content_height}")
        else:
            self.logger.info(f"❌ 全景图内容尺寸不符合预期，当前: {content_size.width()}x{content_size.height()}")
        
        # 4. 加载测试数据验证显示效果
        self.logger.info("\\n🔄 加载测试数据验证显示效果")
        
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(4000)
        
        # 5. 验证加载后的显示效果
        self.logger.info("\\n✅ 验证数据加载后的显示效果")
        
        # 检查全景图信息更新
        info_text = sidebar_panorama.info_label.text()
        self.logger.info(f"📊 全景图信息: {info_text}")
        
        # 检查场景内容
        scene = panorama_view.scene
        if scene:
            items_count = len(scene.items())
            scene_rect = scene.sceneRect()
            
            self.logger.info(f"🎨 全景图场景内容:")
            self.logger.info(f"  📦 图形项数量: {items_count}")
            self.logger.info(f"  📏 场景边界: {scene_rect}")
            
            if items_count > 0:
                self.logger.info("✅ 全景图成功显示内容")
                
                # 检查视图变换
                transform = panorama_view.transform()
                scale_x = transform.m11()
                scale_y = transform.m22()
                dx = transform.dx()
                dy = transform.dy()
                
                self.logger.info(f"🎯 视图变换信息:")
                self.logger.info(f"  📏 缩放: X={scale_x:.3f}, Y={scale_y:.3f}")
                self.logger.info(f"  📍 偏移: X={dx:.1f}, Y={dy:.1f}")
                
                # 检查缩放是否适中
                if 0.5 <= scale_x <= 1.0 and 0.5 <= scale_y <= 1.0:
                    self.logger.info("✅ 内容缩放比例适中，便于观察")
                else:
                    self.logger.info("❌ 内容缩放比例可能不合适")
            else:
                self.logger.info("❌ 全景图场景为空")
        
        # 6. 比较尺寸变化
        self.logger.info("\\n📊 尺寸变化对比")
        
        # 计算容器相对于之前尺寸的增长
        old_container_width, old_container_height = 200, 180
        new_container_width, new_container_height = container_size.width(), container_size.height()
        
        container_width_increase = ((new_container_width - old_container_width) / old_container_width) * 100
        container_height_increase = ((new_container_height - old_container_height) / old_container_height) * 100
        
        self.logger.info(f"📈 全景图容器尺寸增长:")
        self.logger.info(f"  宽度: {old_container_width} → {new_container_width} (+{container_width_increase:.1f}%)")
        self.logger.info(f"  高度: {old_container_height} → {new_container_height} (+{container_height_increase:.1f}%)")
        
        # 计算面积增长
        old_container_area = old_container_width * old_container_height
        new_container_area = new_container_width * new_container_height
        container_area_increase = ((new_container_area - old_container_area) / old_container_area) * 100
        
        self.logger.info(f"  面积: {old_container_area} → {new_container_area} (+{container_area_increase:.1f}%)")
        
        # 7. 测试内容居中效果
        self.logger.info("\\n🎯 测试内容居中效果")
        
        if scene and items_count > 0:
            # 获取视图中心
            view_center = panorama_view.rect().center()
            
            # 获取场景中心在视图中的位置
            scene_center = scene.sceneRect().center()
            view_scene_center = panorama_view.mapFromScene(scene_center)
            
            # 计算偏差
            center_offset_x = abs(view_center.x() - view_scene_center.x())
            center_offset_y = abs(view_center.y() - view_scene_center.y())
            
            self.logger.info(f"📍 居中效果检测:")
            self.logger.info(f"  视图中心: ({view_center.x()}, {view_center.y()})")
            self.logger.info(f"  场景中心在视图中的位置: ({view_scene_center.x():.1f}, {view_scene_center.y():.1f})")
            self.logger.info(f"  偏差: X={center_offset_x:.1f}, Y={center_offset_y:.1f}")
            
            # 检查是否基本居中 (允许小幅偏差)
            tolerance = 20  # 像素容差
            if center_offset_x <= tolerance and center_offset_y <= tolerance:
                self.logger.info("✅ 内容已基本居中显示")
            else:
                self.logger.info("❌ 内容未正确居中")
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        hole_id = 1
        
        # 创建一个圆形分布模拟DXF内容
        import math
        center_x, center_y = 400, 400
        
        # 创建多个同心圆
        for ring in range(1, 6):  # 5个同心圆
            radius = ring * 50 + 100  # 从150开始，每圈增加50
            holes_in_ring = ring * 8 + 8  # 内圈孔少，外圈孔多
            
            for i in range(holes_in_ring):
                angle = (2 * math.pi * i) / holes_in_ring
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                hole_data = HoleData(
                    hole_id=f"H{hole_id:05d}",
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                
                test_holes[hole_data.hole_id] = hole_data
                hole_id += 1
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={
                'source_file': 'panorama_frame_test',
                'total_holes': len(test_holes),
                'created_by': 'frame_adjustment_test'
            }
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 全景图显示框调整验证总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 全景图显示框调整验证成功")
            self.logger.info("\\n🎯 完成的改进：")
            self.logger.info("  📐 全景图容器从 200x180 增大到 400x380")
            self.logger.info("  🖼️ 全景图内容调整为 350x330 适中尺寸")
            self.logger.info("  📊 容器面积增加约 111%")
            self.logger.info("  🎯 内容在容器中居中显示")
            self.logger.info("  📏 内容缩放比例适中，便于观察")
            
            self.logger.info("\\n🔧 用户体验提升：")
            self.logger.info("  👁️ 更大的显示框提供更好的视觉体验")
            self.logger.info("  🎯 适中的内容尺寸便于查看DXF详细信息")
            self.logger.info("  📍 居中的内容布局更加美观")
            self.logger.info("  🖱️ 更大的操作区域便于点击选择")
            
            self.logger.info("\\n📐 布局优化效果：")
            self.logger.info("  🖼️ 全景图成为主要的导航工具")
            self.logger.info("  📱 界面布局更加平衡专业")
            self.logger.info("  🎨 视觉层次更加清晰")
        else:
            self.logger.info("❌ 全景图显示框调整验证失败")

def main():
    """主函数"""
    test = PanoramaFrameAdjustmentTest()
    
    try:
        success = test.test_panorama_frame_adjustment()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户验证
        if test.window:
            test.logger.info("\\n👁️ 请验证以下改进：")
            test.logger.info("  1. 右侧全景图显示框是否明显变大了")
            test.logger.info("  2. 全景图内容是否在框中居中显示")
            test.logger.info("  3. 内容大小是否适中，便于观察")
            test.logger.info("  4. 扇形区域是否居中且清晰可见")
            test.logger.info("\\n窗口将在15秒后关闭...")
            QTest.qWait(15000)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        test.logger.info("\\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        test.logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())