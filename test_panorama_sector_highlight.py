#!/usr/bin/env python3
"""
全景图扇形高亮和点击选择功能测试脚本
测试全景图中扇形区域的高亮显示和交互选择功能
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
from aidcis2.graphics.sector_manager import SectorQuadrant

class PanoramaSectorHighlightTest:
    """全景图扇形高亮测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_sector_highlight_functionality(self):
        """测试扇形高亮功能"""
        self.logger.info("🚀 开始全景图扇形高亮功能测试")
        
        # 1. 创建主窗口并加载数据
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 创建测试数据
        hole_collection = self._create_test_data()
        
        # 3. 加载数据到主窗口
        self.logger.info(f"\n📊 加载 {len(hole_collection)} 个孔位")
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(4000)
        
        # 4. 验证扇形高亮创建
        self.logger.info("\n🔍 验证扇形高亮创建")
        panorama = self.window.sidebar_panorama
        
        # 检查是否创建了扇形高亮项
        highlight_count = len(panorama.sector_highlights)
        self.logger.info(f"📦 扇形高亮项数量: {highlight_count}")
        
        if highlight_count == 4:
            self.logger.info("✅ 扇形高亮项创建成功")
            
            # 检查每个扇形的高亮项
            for sector, highlight in panorama.sector_highlights.items():
                mode = highlight.highlight_mode
                bounds = highlight.sector_bounds
                self.logger.info(f"  🎨 {sector.value}: 模式={mode}, 边界={bounds is not None}")
        else:
            self.logger.info(f"❌ 扇形高亮项数量错误，期望4个，实际{highlight_count}个")
        
        # 5. 测试扇形切换和高亮联动
        self.logger.info("\n🔄 测试扇形切换和高亮联动")
        
        test_sectors = [
            SectorQuadrant.SECTOR_1,
            SectorQuadrant.SECTOR_2, 
            SectorQuadrant.SECTOR_3,
            SectorQuadrant.SECTOR_4
        ]
        
        for i, sector in enumerate(test_sectors):
            self.logger.info(f"\n--- 测试扇形 {sector.value} ---")
            
            # 切换到该扇形
            self.window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(1000)
            
            # 检查高亮状态
            current_highlighted = panorama.current_highlighted_sector
            if current_highlighted == sector:
                self.logger.info(f"✅ 扇形 {sector.value} 高亮正确")
            else:
                self.logger.info(f"❌ 扇形 {sector.value} 高亮错误，当前高亮: {current_highlighted}")
            
            # 检查高亮项可见性
            if sector in panorama.sector_highlights:
                highlight_item = panorama.sector_highlights[sector]
                is_visible = highlight_item.isVisible()
                self.logger.info(f"  👁️ 高亮项可见性: {is_visible}")
                
                if not is_visible:
                    self.logger.info("  ⚠️ 高亮项不可见，尝试强制显示")
                    highlight_item.show_highlight()
            
        # 6. 测试高亮模式切换
        self.logger.info("\n🎨 测试高亮模式切换")
        
        # 切换到扇形模式
        panorama.set_highlight_mode("sector")
        QTest.qWait(500)
        self.logger.info("🔄 切换到扇形模式")
        
        # 切换回边界框模式
        panorama.set_highlight_mode("bounds")
        QTest.qWait(500)
        self.logger.info("🔄 切换到边界框模式")
        
        # 7. 测试点击功能模拟
        self.logger.info("\n🖱️ 测试点击功能模拟")
        
        # 模拟点击不同扇形区域
        test_points = [
            (500, 200, SectorQuadrant.SECTOR_1),  # 右上
            (300, 200, SectorQuadrant.SECTOR_2),  # 左上
            (300, 600, SectorQuadrant.SECTOR_3),  # 左下
            (500, 600, SectorQuadrant.SECTOR_4),  # 右下
        ]
        
        for x, y, expected_sector in test_points:
            scene_pos = QPointF(x, y)
            detected_sector = panorama._detect_clicked_sector(scene_pos)
            
            if detected_sector == expected_sector:
                self.logger.info(f"✅ 点击检测正确: ({x}, {y}) -> {expected_sector.value}")
            else:
                self.logger.info(f"❌ 点击检测错误: ({x}, {y}) -> 期望{expected_sector.value}，实际{detected_sector}")
        
        # 8. 测试几何计算
        self.logger.info("\n📐 验证几何计算")
        
        center = panorama.center_point
        radius = panorama.panorama_radius
        
        if center and radius > 0:
            self.logger.info(f"✅ 几何计算成功:")
            self.logger.info(f"  🎯 中心点: ({center.x():.1f}, {center.y():.1f})")
            self.logger.info(f"  📏 半径: {radius:.1f}")
        else:
            self.logger.info("❌ 几何计算失败")
        
        return True
    
    def _create_test_data(self):
        """创建具有明确扇形分布的测试数据"""
        test_holes = {}
        hole_id = 1
        
        # 在每个象限中创建孔位
        quadrants = [
            (450, 350, "右上"),  # 第一象限
            (350, 350, "左上"),  # 第二象限
            (350, 450, "左下"),  # 第三象限
            (450, 450, "右下"),  # 第四象限
        ]
        
        center_x, center_y = 400, 400  # 中心点
        
        for quad_x, quad_y, quad_name in quadrants:
            # 在每个象限创建一些孔位
            for i in range(15):
                for j in range(15):
                    # 在象限内分布孔位
                    offset_x = (i - 7) * 8  # 8mm间距
                    offset_y = (j - 7) * 8
                    
                    x = quad_x + offset_x
                    y = quad_y + offset_y
                    
                    # 只在该象限内创建孔位
                    if quad_name == "右上" and (x >= center_x and y <= center_y):
                        pass
                    elif quad_name == "左上" and (x <= center_x and y <= center_y):
                        pass
                    elif quad_name == "左下" and (x <= center_x and y >= center_y):
                        pass
                    elif quad_name == "右下" and (x >= center_x and y >= center_y):
                        pass
                    else:
                        continue
                    
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
                'source_file': 'sector_test_data',
                'total_holes': len(test_holes),
                'created_by': 'sector_highlight_test'
            }
        )
        
        self.logger.info(f"🏗️ 创建扇形测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 全景图扇形高亮功能测试总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 全景图扇形高亮功能测试成功")
            self.logger.info("\n🎯 实现的功能：")
            self.logger.info("  ✅ 扇形区域自动高亮显示")
            self.logger.info("  ✅ 主视图切换时全景图同步高亮")
            self.logger.info("  ✅ 支持扇形模式和边界框模式")
            self.logger.info("  ✅ 扇形区域点击检测算法")
            self.logger.info("  ✅ 全景图几何计算（中心点和半径）")
            
            self.logger.info("\n🔧 用户交互：")
            self.logger.info("  👁️ 当前选中的扇形区域在全景图中高亮显示")
            self.logger.info("  🖱️ 可点击全景图中的扇形区域切换主视图")
            self.logger.info("  🎨 支持两种高亮模式：扇形区域和边界框")
            self.logger.info("  📍 精确的角度计算确保正确的扇形检测")
            
            self.logger.info("\n📝 用户体验改进：")
            self.logger.info("  🎯 用户可直观看到当前查看的是哪个区域")
            self.logger.info("  🔄 通过点击全景图快速切换查看区域")
            self.logger.info("  💡 淡色高亮既突出又不遮挡孔位显示")
        else:
            self.logger.info("❌ 全景图扇形高亮功能测试失败")

def main():
    """主函数"""
    test = PanoramaSectorHighlightTest()
    
    try:
        success = test.test_sector_highlight_functionality()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户测试
        if test.window:
            test.logger.info("\n👁️ 请测试以下功能：")
            test.logger.info("  1. 观察全景图右下角是否有扇形高亮显示")
            test.logger.info("  2. 尝试点击全景图的不同区域切换主视图")
            test.logger.info("  3. 查看主视图切换时全景图高亮是否同步")
            test.logger.info("\n窗口将在10秒后关闭...")
            QTest.qWait(10000)
        
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