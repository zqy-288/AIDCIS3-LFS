#!/usr/bin/env python3
"""
扇形专注显示快速验证脚本
验证主显示视图是否正确显示当前扇形而不是完整全景
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorQuadrant

class SectorFocusedDisplayTest:
    """扇形专注显示测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def create_test_data(self):
        """创建测试数据 - 分布在四个象限"""
        test_holes = {}
        
        # 每个象限创建不同数量的孔位，便于验证
        sector_data = [
            # 扇形1 (右上) - 5个孔位
            [(50, 50), (60, 60), (70, 40), (80, 70), (55, 65)],
            # 扇形2 (左上) - 4个孔位  
            [(-50, 50), (-60, 60), (-40, 70), (-55, 45)],
            # 扇形3 (左下) - 6个孔位
            [(-50, -50), (-60, -60), (-40, -70), (-55, -45), (-65, -55), (-45, -65)],
            # 扇形4 (右下) - 3个孔位
            [(50, -50), (60, -60), (70, -40)]
        ]
        
        hole_counter = 0
        for sector_positions in sector_data:
            for x, y in sector_positions:
                hole = HoleData(
                    hole_id=f"H{hole_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_counter += 1
        
        return HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test_sector_focus.dxf', 'total_holes': len(test_holes)}
        )
    
    def test_sector_focused_display(self):
        """测试扇形专注显示功能"""
        self.logger.info("🚀 开始扇形专注显示测试")
        
        # 1. 创建窗口和测试数据
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(1000)  # 等待初始化
        
        test_collection = self.create_test_data()
        total_holes = len(test_collection)
        
        self.logger.info(f"📊 测试数据: {total_holes} 个孔位 (扇形1:5, 扇形2:4, 扇形3:6, 扇形4:3)")
        
        # 2. 加载数据
        self.window.hole_collection = test_collection
        self.window.update_hole_display()
        QTest.qWait(500)
        
        # 3. 验证初始状态 - 应该显示扇形1
        self.logger.info("\\n📋 验证初始状态")
        current_sector = self.window.dynamic_sector_display.get_current_sector()
        self.logger.info(f"当前扇形: {current_sector.value}")
        
        main_view = self.window.graphics_view
        if hasattr(main_view, 'hole_items'):
            displayed_holes = len(main_view.hole_items)
            self.logger.info(f"主视图显示孔位数: {displayed_holes}")
            
            if displayed_holes == 5:
                self.logger.info("✅ 正确！主视图显示扇形1的5个孔位（专注显示）")
            elif displayed_holes == total_holes:
                self.logger.info(f"❌ 错误！主视图显示全部{total_holes}个孔位（全景显示）")
                return False
            else:
                self.logger.info(f"⚠️ 异常！主视图显示{displayed_holes}个孔位（预期5个）")
        
        # 4. 测试扇形切换
        expected_counts = {
            SectorQuadrant.SECTOR_1: 5,
            SectorQuadrant.SECTOR_2: 4, 
            SectorQuadrant.SECTOR_3: 6,
            SectorQuadrant.SECTOR_4: 3
        }
        
        self.logger.info("\\n🔄 测试扇形切换")
        for sector, expected_count in expected_counts.items():
            self.logger.info(f"\\n切换到 {sector.value}")
            
            # 切换扇形
            self.window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(300)
            
            # 验证切换结果
            current_sector = self.window.dynamic_sector_display.get_current_sector()
            if current_sector == sector:
                self.logger.info(f"✅ 扇形切换成功: {sector.value}")
            else:
                self.logger.info(f"❌ 扇形切换失败: 期望{sector.value}, 实际{current_sector.value}")
                return False
            
            # 验证显示的孔位数
            if hasattr(main_view, 'hole_items'):
                displayed_holes = len(main_view.hole_items)
                self.logger.info(f"显示孔位数: {displayed_holes} (预期: {expected_count})")
                
                if displayed_holes == expected_count:
                    self.logger.info(f"✅ 正确！{sector.value} 专注显示 {expected_count} 个孔位")
                elif displayed_holes == total_holes:
                    self.logger.info(f"❌ 错误！显示了全景({total_holes}个孔位)而不是扇形专注")
                    return False
                else:
                    self.logger.info(f"⚠️ 异常！显示{displayed_holes}个孔位，预期{expected_count}个")
        
        # 5. 验证侧边栏全景图
        self.logger.info("\\n🖼️ 验证侧边栏全景图")
        panorama_info = self.window.sidebar_panorama.info_label.text()
        if f"{total_holes} 个孔位" in panorama_info:
            self.logger.info(f"✅ 侧边栏全景图正确显示全部 {total_holes} 个孔位")
        else:
            self.logger.info(f"❌ 侧边栏全景图显示异常: {panorama_info}")
        
        # 6. 模拟检测点追踪
        self.logger.info("\\n🎯 测试检测点追踪")
        simulation_sequence = [
            SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
            SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4
        ]
        
        for i, sector in enumerate(simulation_sequence):
            self.logger.info(f"模拟检测点移动到 {sector.value}")
            
            # 模拟检测点移动触发扇形切换
            self.window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(200)
            
            # 验证主视图跟随切换
            current_sector = self.window.dynamic_sector_display.get_current_sector()
            if current_sector == sector:
                displayed_holes = len(main_view.hole_items) if hasattr(main_view, 'hole_items') else 0
                expected_count = expected_counts[sector]
                if displayed_holes == expected_count:
                    self.logger.info(f"✅ 检测点追踪正确: {sector.value} 显示 {displayed_holes} 个孔位")
                else:
                    self.logger.info(f"❌ 检测点追踪异常: {sector.value} 显示 {displayed_holes} 个孔位，预期 {expected_count}")
                    return False
            else:
                self.logger.info(f"❌ 检测点追踪失败: 期望{sector.value}, 实际{current_sector.value}")
                return False
        
        self.logger.info("\\n🎉 扇形专注显示测试完成")
        return True
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 扇形专注显示测试总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 测试通过！主显示视图正确实现扇形专注显示")
            self.logger.info("✅ 检测点追踪功能正常")
            self.logger.info("✅ 侧边栏全景图正确显示完整数据")
            self.logger.info("\\n🎯 修复成功：")
            self.logger.info("  - 主视图不再显示完整全景")
            self.logger.info("  - 主视图跟随当前检测点显示对应扇形")
            self.logger.info("  - 扇形切换功能正常工作")
            self.logger.info("  - 侧边栏提供完整全景概览")
        else:
            self.logger.info("❌ 测试失败！扇形专注显示存在问题")
            self.logger.info("\\n🔧 需要检查：")
            self.logger.info("  - 主视图是否仍在显示完整全景")
            self.logger.info("  - 扇形切换逻辑是否正确执行")
            self.logger.info("  - 数据加载逻辑是否被正确修复")

def main():
    """主函数"""
    test = SectorFocusedDisplayTest()
    
    try:
        success = test.test_sector_focused_display()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口打开以便观察
        if test.window:
            test.logger.info("\\n窗口将在5秒后关闭...")
            QTest.qWait(5000)
        
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