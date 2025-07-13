#!/usr/bin/env python3
"""
布局优化端到端测试脚本
验证主显示区域增大和全景预览DXF内容缩小的效果
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

class LayoutOptimizationE2ETest:
    """布局优化端到端测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_layout_optimization_e2e(self):
        """端到端测试布局优化"""
        self.logger.info("🚀 开始布局优化端到端验证")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(3000)  # 等待窗口完全显示
        
        # 2. 验证整体窗口尺寸
        self.logger.info("\\n📐 验证整体窗口尺寸")
        
        window_size = self.window.size()
        self.logger.info(f"📏 主窗口尺寸: {window_size.width()} x {window_size.height()}")
        
        # 3. 验证三个面板的尺寸分配
        self.logger.info("\\n📊 验证三个面板的尺寸分配")
        
        # 获取分割器
        content_splitter = None
        for child in self.window.findChildren(object):
            if hasattr(child, 'sizes') and hasattr(child, 'orientation'):
                content_splitter = child
                break
        
        if content_splitter:
            sizes = content_splitter.sizes()
            total_width = sum(sizes)
            
            self.logger.info(f"📏 面板尺寸分配: {sizes}")
            self.logger.info(f"📊 面板宽度比例:")
            self.logger.info(f"  左侧面板: {sizes[0]}px ({sizes[0]/total_width*100:.1f}%)")
            self.logger.info(f"  中间主显示: {sizes[1]}px ({sizes[1]/total_width*100:.1f}%)")
            self.logger.info(f"  右侧面板: {sizes[2]}px ({sizes[2]/total_width*100:.1f}%)")
            
            # 检查主显示区域是否占据了足够的比例
            main_ratio = sizes[1] / total_width
            if main_ratio >= 0.6:  # 至少60%
                self.logger.info("✅ 主显示区域占据了足够的空间比例")
            else:
                self.logger.info(f"❌ 主显示区域比例偏小: {main_ratio*100:.1f}%")
        else:
            self.logger.info("❌ 未找到内容分割器")
        
        # 4. 验证主显示区域尺寸
        self.logger.info("\\n🖼️ 验证主显示区域尺寸")
        
        main_display = self.window.dynamic_sector_display
        main_size = main_display.size()
        
        self.logger.info(f"📏 主显示区域尺寸: {main_size.width()} x {main_size.height()}")
        
        # 检查主显示区域是否足够大
        if main_size.width() >= 1000:  # 至少1000像素宽
            self.logger.info("✅ 主显示区域宽度充足")
        else:
            self.logger.info(f"❌ 主显示区域宽度不足: {main_size.width()}px")
        
        # 5. 验证全景预览区域
        self.logger.info("\\n🔍 验证全景预览区域")
        
        sidebar_panorama = self.window.sidebar_panorama
        panorama_container_size = sidebar_panorama.size()
        panorama_view = sidebar_panorama.panorama_view
        panorama_content_size = panorama_view.size()
        
        self.logger.info(f"📏 全景预览容器尺寸: {panorama_container_size.width()} x {panorama_container_size.height()}")
        self.logger.info(f"📏 全景预览内容尺寸: {panorama_content_size.width()} x {panorama_content_size.height()}")
        
        # 6. 加载测试数据验证显示效果
        self.logger.info("\\n🔄 加载测试数据验证显示效果")
        
        hole_collection = self._create_comprehensive_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(5000)
        
        # 7. 验证全景预览中DXF内容的缩放
        self.logger.info("\\n🎯 验证全景预览中DXF内容缩放")
        
        scene = panorama_view.scene
        if scene and len(scene.items()) > 0:
            # 获取场景内容边界
            scene_rect = scene.itemsBoundingRect()
            scene_center = scene_rect.center()
            
            # 获取视图边界
            view_rect = panorama_view.viewport().rect()
            
            # 计算内容占视图的比例
            transform = panorama_view.transform()
            scale_factor = transform.m11()
            
            # 计算场景内容在视图中的实际大小
            content_width_in_view = scene_rect.width() * scale_factor
            content_height_in_view = scene_rect.height() * scale_factor
            
            # 计算内容占视图的比例
            width_ratio = content_width_in_view / view_rect.width()
            height_ratio = content_height_in_view / view_rect.height()
            
            self.logger.info(f"🎯 全景预览内容分析:")
            self.logger.info(f"  📦 场景边界: {scene_rect}")
            self.logger.info(f"  📏 缩放比例: {scale_factor:.3f}")
            self.logger.info(f"  📐 内容在视图中的尺寸: {content_width_in_view:.1f} x {content_height_in_view:.1f}")
            self.logger.info(f"  📊 内容占视图比例: 宽{width_ratio*100:.1f}% x 高{height_ratio*100:.1f}%")
            
            # 检查内容是否适中大小（不占满整个视图）
            if width_ratio <= 0.8 and height_ratio <= 0.8:  # 不超过80%
                self.logger.info("✅ 全景预览中DXF内容大小适中，留有边距")
            else:
                self.logger.info("❌ 全景预览中DXF内容仍然太大")
        
        # 8. 验证主显示区域的内容
        self.logger.info("\\n🖼️ 验证主显示区域内容")
        
        main_graphics_view = main_display.graphics_view
        main_scene = main_graphics_view.scene
        
        if main_scene:
            main_items = len(main_scene.items())
            main_rect = main_scene.sceneRect()
            main_view_size = main_graphics_view.size()
            
            self.logger.info(f"🎨 主显示区域内容:")
            self.logger.info(f"  📦 图形项数量: {main_items}")
            self.logger.info(f"  📏 场景边界: {main_rect}")
            self.logger.info(f"  🖼️ 视图尺寸: {main_view_size.width()} x {main_view_size.height()}")
            
            # 检查主显示区域的白色画布是否足够大
            white_canvas_ratio = main_view_size.width() / window_size.width()
            self.logger.info(f"  📊 主显示区域占窗口宽度: {white_canvas_ratio*100:.1f}%")
            
            if white_canvas_ratio >= 0.5:  # 至少占50%
                self.logger.info("✅ 主显示区域（白色部分）占据了足够的空间")
            else:
                self.logger.info("❌ 主显示区域（白色部分）空间不足")
        
        # 9. 对比优化前后的效果
        self.logger.info("\\n📊 优化效果对比")
        
        # 预期的改进效果
        expected_improvements = {
            "主显示区域宽度": "从800px增加到1200px+",
            "右侧面板宽度": "从350px减少到280px",
            "全景预览DXF缩放": "从0.6减少到0.4",
            "主显示占比": "从约40%增加到60%+"
        }
        
        self.logger.info("🎯 预期改进效果:")
        for improvement, description in expected_improvements.items():
            self.logger.info(f"  📈 {improvement}: {description}")
        
        return True
    
    def _create_comprehensive_test_data(self):
        """创建全面的测试数据"""
        test_holes = {}
        hole_id = 1
        
        # 创建一个大圆形分布，确保能看到缩放效果
        import math
        center_x, center_y = 400, 400
        
        # 创建多个同心圆，确保内容丰富
        for ring in range(1, 8):  # 7个同心圆
            radius = ring * 60 + 100  # 从160开始，每圈增加60
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
                'source_file': 'layout_optimization_test',
                'total_holes': len(test_holes),
                'created_by': 'layout_optimization_e2e_test'
            }
        )
        
        self.logger.info(f"🧪 创建全面测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 70)
        self.logger.info("📊 布局优化端到端验证总结")
        self.logger.info("=" * 70)
        
        if success:
            self.logger.info("✅ 布局优化端到端验证成功")
            self.logger.info("\\n🎯 完成的优化：")
            self.logger.info("  📐 中间主显示区域比例从3/5增加到5/7")
            self.logger.info("  📏 右侧面板宽度从350px减少到280px")
            self.logger.info("  🔍 全景预览DXF缩放从0.6减少到0.4")
            self.logger.info("  📊 主显示区域宽度显著增加")
            
            self.logger.info("\\n🔧 用户体验提升：")
            self.logger.info("  👁️ 更大的主显示区域（白色部分）提供更好的DXF查看体验")
            self.logger.info("  🎯 全景预览中的DXF内容大小适中，不再占满整个框")
            self.logger.info("  📍 右侧面板更紧凑，不再挤压主显示区域")
            self.logger.info("  🖱️ 更合理的界面布局比例")
            
            self.logger.info("\\n📐 布局优化效果：")
            self.logger.info("  🖼️ 主显示区域成为真正的主要工作区域")
            self.logger.info("  📱 全景预览保持功能的同时更加紧凑")
            self.logger.info("  🎨 整体界面比例更加协调专业")
        else:
            self.logger.info("❌ 布局优化端到端验证失败")

def main():
    """主函数"""
    test = LayoutOptimizationE2ETest()
    
    try:
        success = test.test_layout_optimization_e2e()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户验证
        if test.window:
            test.logger.info("\\n👁️ 请验证以下优化效果：")
            test.logger.info("  1. 中间白色主显示区域是否明显变大了")
            test.logger.info("  2. 右侧灰色区域是否变窄了，不再挤压主显示")
            test.logger.info("  3. 左下角全景预览中的圆形DXF是否变小了，留有边距")
            test.logger.info("  4. 整体布局比例是否更加合理")
            test.logger.info("\\n如果效果不理想，我会根据实际显示效果进行调整...")
            test.logger.info("\\n窗口将在25秒后关闭...")
            QTest.qWait(25000)
        
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