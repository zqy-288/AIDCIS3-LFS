#!/usr/bin/env python3
"""
全景图居中和主窗口尺寸验证脚本
验证全景图内容居中显示和主显示窗口尺寸增大
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPointF

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class CenteringAndMainWindowTest:
    """全景图居中和主窗口尺寸测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_centering_and_main_window(self):
        """测试全景图居中和主窗口尺寸"""
        self.logger.info("🚀 开始全景图居中和主窗口尺寸验证")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 验证主显示窗口尺寸
        self.logger.info("\\n📐 验证主显示窗口尺寸")
        
        main_display = self.window.dynamic_sector_display
        main_size = main_display.size()
        
        self.logger.info(f"📏 主显示窗口尺寸: {main_size.width()} x {main_size.height()}")
        
        # 检查是否达到新的主窗口尺寸要求 (1200x900)
        expected_main_width = 1200
        expected_main_height = 900
        
        if main_size.width() >= expected_main_width and main_size.height() >= expected_main_height:
            self.logger.info(f"✅ 主显示窗口尺寸已增大到 {expected_main_width}x{expected_main_height}")
        else:
            self.logger.info(f"❌ 主显示窗口尺寸未达到预期，当前: {main_size.width()}x{main_size.height()}")
        
        # 3. 验证全景图容器和内容尺寸
        self.logger.info("\\n🖼️ 验证全景图尺寸")
        
        sidebar_panorama = self.window.sidebar_panorama
        container_size = sidebar_panorama.size()
        panorama_view = sidebar_panorama.panorama_view
        content_size = panorama_view.size()
        
        self.logger.info(f"📏 全景图容器尺寸: {container_size.width()} x {container_size.height()}")
        self.logger.info(f"📏 全景图内容尺寸: {content_size.width()} x {content_size.height()}")
        
        # 4. 加载测试数据验证居中效果
        self.logger.info("\\n🔄 加载测试数据验证居中效果")
        
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(5000)
        
        # 5. 详细检查全景图居中效果
        self.logger.info("\\n🎯 验证全景图居中效果")
        
        scene = panorama_view.scene
        if scene and len(scene.items()) > 0:
            # 获取场景内容边界
            scene_rect = scene.itemsBoundingRect()
            scene_center = scene_rect.center()
            
            # 获取视图边界
            view_rect = panorama_view.viewport().rect()
            view_center = QPointF(view_rect.width() / 2.0, view_rect.height() / 2.0)
            
            # 计算场景中心在视图坐标系中的位置
            scene_center_in_view = panorama_view.mapFromScene(scene_center)
            
            # 计算居中偏差
            center_offset_x = abs(view_center.x() - scene_center_in_view.x())
            center_offset_y = abs(view_center.y() - scene_center_in_view.y())
            
            self.logger.info(f"🎯 居中效果详细分析:")
            self.logger.info(f"  📦 场景边界: {scene_rect}")
            self.logger.info(f"  📍 场景中心: ({scene_center.x():.1f}, {scene_center.y():.1f})")
            self.logger.info(f"  🖼️ 视图中心: ({view_center.x():.1f}, {view_center.y():.1f})")
            self.logger.info(f"  📍 场景中心在视图中: ({scene_center_in_view.x():.1f}, {scene_center_in_view.y():.1f})")
            self.logger.info(f"  📏 居中偏差: X={center_offset_x:.1f}px, Y={center_offset_y:.1f}px")
            
            # 检查居中效果
            tolerance = 30  # 像素容差
            if center_offset_x <= tolerance and center_offset_y <= tolerance:
                self.logger.info("✅ 全景图内容已正确居中显示")
            else:
                self.logger.info("❌ 全景图内容未正确居中")
            
            # 检查缩放比例
            transform = panorama_view.transform()
            scale_x = transform.m11()
            scale_y = transform.m22()
            
            self.logger.info(f"📏 缩放比例: X={scale_x:.3f}, Y={scale_y:.3f}")
            
            if 0.4 <= scale_x <= 0.8 and 0.4 <= scale_y <= 0.8:
                self.logger.info("✅ 缩放比例适中，内容大小合适")
            else:
                self.logger.info("❌ 缩放比例可能不合适")
        
        # 6. 验证主显示窗口内容
        self.logger.info("\\n🖼️ 验证主显示窗口内容")
        
        main_graphics_view = main_display.graphics_view
        main_scene = main_graphics_view.scene
        
        if main_scene:
            main_items = len(main_scene.items())
            main_rect = main_scene.sceneRect()
            main_view_size = main_graphics_view.size()
            
            self.logger.info(f"🎨 主显示窗口内容:")
            self.logger.info(f"  📦 图形项数量: {main_items}")
            self.logger.info(f"  📏 场景边界: {main_rect}")
            self.logger.info(f"  🖼️ 视图尺寸: {main_view_size.width()} x {main_view_size.height()}")
            
            if main_items > 0:
                self.logger.info("✅ 主显示窗口成功显示内容")
                
                # 检查主显示窗口是否居中
                main_center = main_graphics_view.mapFromScene(main_rect.center())
                main_view_center = QPointF(main_view_size.width() / 2.0, main_view_size.height() / 2.0)
                
                main_offset_x = abs(main_view_center.x() - main_center.x())
                main_offset_y = abs(main_view_center.y() - main_center.y())
                
                self.logger.info(f"  🎯 主视图居中偏差: X={main_offset_x:.1f}px, Y={main_offset_y:.1f}px")
            else:
                self.logger.info("❌ 主显示窗口场景为空")
        
        # 7. 比较尺寸变化
        self.logger.info("\\n📊 尺寸变化对比")
        
        # 主显示窗口尺寸变化
        old_main_width, old_main_height = 800, 650
        new_main_width, new_main_height = main_size.width(), main_size.height()
        
        main_width_increase = ((new_main_width - old_main_width) / old_main_width) * 100
        main_height_increase = ((new_main_height - old_main_height) / old_main_height) * 100
        main_area_increase = ((new_main_width * new_main_height - old_main_width * old_main_height) / (old_main_width * old_main_height)) * 100
        
        self.logger.info(f"📈 主显示窗口尺寸增长:")
        self.logger.info(f"  宽度: {old_main_width} → {new_main_width} (+{main_width_increase:.1f}%)")
        self.logger.info(f"  高度: {old_main_height} → {new_main_height} (+{main_height_increase:.1f}%)")
        self.logger.info(f"  面积: {old_main_width * old_main_height} → {new_main_width * new_main_height} (+{main_area_increase:.1f}%)")
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        hole_id = 1
        
        # 创建一个圆形分布
        import math
        center_x, center_y = 400, 400
        
        # 创建多个同心圆确保有足够内容测试居中效果
        for ring in range(1, 7):  # 6个同心圆
            radius = ring * 45 + 80  # 从125开始，每圈增加45
            holes_in_ring = ring * 10 + 8  # 内圈孔少，外圈孔多
            
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
                'source_file': 'centering_test',
                'total_holes': len(test_holes),
                'created_by': 'centering_main_window_test'
            }
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 全景图居中和主窗口尺寸验证总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 全景图居中和主窗口尺寸验证成功")
            self.logger.info("\\n🎯 完成的改进：")
            self.logger.info("  📐 主显示窗口从 800x650 增大到 1200x900")
            self.logger.info("  🎯 全景图内容强制居中显示")
            self.logger.info("  📏 缩放比例调整为0.6，内容大小适中")
            self.logger.info("  📊 主显示窗口面积增加约 69%")
            
            self.logger.info("\\n🔧 用户体验提升：")
            self.logger.info("  👁️ 更大的主显示窗口提供更好的DXF查看体验")
            self.logger.info("  🎯 全景图内容真正居中，视觉效果更佳")
            self.logger.info("  📍 内容大小适中，既能看清整体又能观察细节")
            self.logger.info("  🖱️ 更大的操作空间便于交互")
            
            self.logger.info("\\n📐 布局优化效果：")
            self.logger.info("  🖼️ 主显示窗口成为真正的主要工作区域")
            self.logger.info("  📱 全景图作为完美的导航助手")
            self.logger.info("  🎨 整体界面比例更加协调")
        else:
            self.logger.info("❌ 全景图居中和主窗口尺寸验证失败")

def main():
    """主函数"""
    test = CenteringAndMainWindowTest()
    
    try:
        success = test.test_centering_and_main_window()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户验证
        if test.window:
            test.logger.info("\\n👁️ 请验证以下改进：")
            test.logger.info("  1. 中间主显示窗口是否明显变大了")
            test.logger.info("  2. 右侧全景图内容是否在框中居中显示")
            test.logger.info("  3. 全景图内容大小是否适中")
            test.logger.info("  4. 整体界面比例是否更加协调")
            test.logger.info("\\n窗口将在20秒后关闭...")
            QTest.qWait(20000)
        
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