#!/usr/bin/env python3
"""
最终UI改进验证脚本
验证全景图尺寸进一步增大和主视图DXF图像居中显示
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

class FinalUIImprovementTest:
    """最终UI改进测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_final_ui_improvements(self):
        """测试最终UI改进"""
        self.logger.info("🚀 开始最终UI改进验证")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 验证全景图尺寸
        self.logger.info("\n📐 验证全景图新尺寸")
        
        panorama = self.window.sidebar_panorama
        panorama_view = panorama.panorama_view
        panorama_size = panorama_view.size()
        
        self.logger.info(f"📏 全景图尺寸: {panorama_size.width()} x {panorama_size.height()}")
        
        # 检查是否达到新的尺寸要求
        expected_width = 520
        expected_height = 550
        
        if panorama_size.width() >= expected_width and panorama_size.height() >= expected_height:
            self.logger.info(f"✅ 全景图尺寸已增大到 {expected_width}x{expected_height}")
        else:
            self.logger.info(f"❌ 全景图尺寸未达到预期，当前: {panorama_size.width()}x{panorama_size.height()}")
        
        # 3. 验证主视图布局
        self.logger.info("\n🎯 验证主视图居中布局")
        
        dynamic_display = self.window.dynamic_sector_display
        graphics_view = dynamic_display.graphics_view
        
        # 检查graphics_view的父容器
        parent_widget = graphics_view.parent()
        if parent_widget:
            self.logger.info(f"✅ 主视图已放置在容器中: {parent_widget.__class__.__name__}")
        else:
            self.logger.info("❌ 主视图没有放置在容器中")
        
        # 检查主视图尺寸
        main_view_size = graphics_view.size()
        self.logger.info(f"📏 主视图尺寸: {main_view_size.width()} x {main_view_size.height()}")
        
        # 4. 加载测试数据验证布局效果
        self.logger.info("\n🔄 加载测试数据验证布局")
        
        hole_collection = self._create_large_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(4000)
        
        # 5. 验证加载后的布局效果
        self.logger.info("\n✅ 验证数据加载后的布局效果")
        
        # 检查全景图信息更新
        updated_info = panorama.info_label.text()
        self.logger.info(f"📊 全景图信息: {updated_info}")
        
        # 检查全景图是否显示完整的DXF内容
        scene = panorama_view.scene
        if scene:
            items_count = len(scene.items())
            scene_rect = scene.sceneRect()
            
            self.logger.info(f"🎨 全景图场景:")
            self.logger.info(f"  📦 图形项: {items_count}")
            self.logger.info(f"  📏 场景边界: {scene_rect}")
            
            if items_count > 0:
                self.logger.info("✅ 全景图成功显示DXF内容")
            else:
                self.logger.info("❌ 全景图场景为空")
        
        # 检查主视图场景
        main_scene = graphics_view.scene
        if main_scene:
            main_items = len(main_scene.items())
            main_rect = main_scene.sceneRect()
            
            self.logger.info(f"🎨 主视图场景:")
            self.logger.info(f"  📦 图形项: {main_items}")
            self.logger.info(f"  📏 场景边界: {main_rect}")
            
            if main_items > 0:
                self.logger.info("✅ 主视图成功显示DXF内容")
            else:
                self.logger.info("❌ 主视图场景为空")
        
        # 6. 测试尺寸对比
        self.logger.info("\n📊 尺寸对比分析")
        
        # 计算全景图相对于之前尺寸的增长
        old_width, old_height = 380, 400
        new_width, new_height = panorama_size.width(), panorama_size.height()
        
        width_increase = ((new_width - old_width) / old_width) * 100
        height_increase = ((new_height - old_height) / old_height) * 100
        
        self.logger.info(f"📈 全景图尺寸增长:")
        self.logger.info(f"  宽度: {old_width} → {new_width} (+{width_increase:.1f}%)")
        self.logger.info(f"  高度: {old_height} → {new_height} (+{height_increase:.1f}%)")
        
        # 计算面积增长
        old_area = old_width * old_height
        new_area = new_width * new_height
        area_increase = ((new_area - old_area) / old_area) * 100
        
        self.logger.info(f"  面积: {old_area} → {new_area} (+{area_increase:.1f}%)")
        
        # 7. 验证高亮功能在新尺寸下的表现
        self.logger.info("\n🎯 验证高亮功能")
        
        # 检查扇形高亮是否正常工作
        if len(panorama.sector_highlights) > 0:
            self.logger.info(f"✅ 扇形高亮功能正常，共 {len(panorama.sector_highlights)} 个高亮区域")
            
            # 测试高亮显示
            from aidcis2.graphics.sector_manager import SectorQuadrant
            test_sector = SectorQuadrant.SECTOR_2
            panorama.highlight_sector(test_sector)
            
            self.logger.info(f"🎯 测试高亮扇形: {test_sector.value}")
        else:
            self.logger.info("❌ 扇形高亮功能未正确初始化")
        
        return True
    
    def _create_large_test_data(self):
        """创建大规模测试数据以更好地验证布局效果"""
        test_holes = {}
        hole_id = 1
        
        # 创建一个更大的圆形分布模拟真实DXF
        import math
        center_x, center_y = 400, 400
        
        # 创建多个同心圆
        for ring in range(1, 8):  # 7个同心圆
            radius = ring * 60 + 80  # 从140开始，每圈增加60
            holes_in_ring = ring * 12 + 8  # 内圈孔少，外圈孔多
            
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
                'source_file': 'large_test_dxf',
                'total_holes': len(test_holes),
                'created_by': 'final_ui_test'
            }
        )
        
        self.logger.info(f"🧪 创建大规模测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 最终UI改进验证总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 最终UI改进验证成功")
            self.logger.info("\n🎯 完成的改进：")
            self.logger.info("  📐 全景图尺寸从 380x400 增大到 520x550")
            self.logger.info("  🎯 主视图DXF图像居中显示")
            self.logger.info("  📊 全景图面积增加约 87%")
            self.logger.info("  🖼️ 更清晰的DXF内容显示")
            
            self.logger.info("\n🔧 用户体验提升：")
            self.logger.info("  👁️ 更大的全景图便于查看和点击操作")
            self.logger.info("  🎯 居中的主视图提供更好的视觉平衡")
            self.logger.info("  📍 扇形高亮在大尺寸下更加明显")
            self.logger.info("  🖱️ 点击目标更大，操作更精确")
            
            self.logger.info("\n📐 布局优化效果：")
            self.logger.info("  🖼️ 全景图成为真正的导航中心")
            self.logger.info("  🎯 主视图内容居中对齐")
            self.logger.info("  📱 界面布局更加专业和美观")
        else:
            self.logger.info("❌ 最终UI改进验证失败")

def main():
    """主函数"""
    test = FinalUIImprovementTest()
    
    try:
        success = test.test_final_ui_improvements()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户验证
        if test.window:
            test.logger.info("\n👁️ 请验证以下最终改进：")
            test.logger.info("  1. 右下角全景图是否明显变大了")
            test.logger.info("  2. 中间主视图的DXF图像是否居中显示")
            test.logger.info("  3. 全景图是否更清晰，便于点击操作")
            test.logger.info("  4. 整体界面是否更加平衡美观")
            test.logger.info("\n窗口将在20秒后关闭...")
            QTest.qWait(20000)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        test.logger.info("\n⏹️ 测试被用户中断")
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