#!/usr/bin/env python3
"""
侧边栏全景图布局集成测试
测试侧边栏全景图与扇形管理器、动态显示组件的集成
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorQuadrant


class TestSidebarPanoramaIntegration(unittest.TestCase):
    """侧边栏全景图集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        self.main_window = MainWindow()
        self.main_window.show()
        QTest.qWait(500)  # 等待UI完全初始化
        
        # 创建标准测试数据集
        self.create_test_data()
    
    def tearDown(self):
        """清理每个测试"""
        if self.main_window:
            self.main_window.close()
        QTest.qWait(100)
    
    def create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        
        # 创建分布在四个象限的孔位数据
        positions = [
            # 第一象限 (右上) - 8个孔位
            [(50, 50), (60, 60), (70, 50), (50, 70), (65, 55), (55, 65), (75, 75), (45, 55)],
            # 第二象限 (左上) - 6个孔位  
            [(-50, 50), (-60, 60), (-70, 50), (-50, 70), (-65, 55), (-55, 65)],
            # 第三象限 (左下) - 7个孔位
            [(-50, -50), (-60, -60), (-70, -50), (-50, -70), (-65, -55), (-55, -65), (-45, -45)],
            # 第四象限 (右下) - 5个孔位
            [(50, -50), (60, -60), (70, -50), (50, -70), (65, -55)]
        ]
        
        hole_counter = 0
        for quadrant_positions in positions:
            for x, y in quadrant_positions:
                hole = HoleData(
                    hole_id=f"H{hole_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_counter += 1
        
        self.test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test_integration.dxf', 'total_holes': len(test_holes)}
        )
        
        # 加载测试数据到主窗口
        self.main_window.hole_collection = self.test_collection
        self.main_window.update_hole_display()
        QTest.qWait(200)
    
    def test_panorama_sector_manager_integration(self):
        """测试全景图与扇形管理器集成"""
        # 验证扇形管理器已加载数据
        self.assertIsNotNone(self.main_window.sector_manager)
        
        # 验证各扇形都有孔位分配
        for sector in SectorQuadrant:
            sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
            self.assertGreater(len(sector_holes), 0, f"扇形 {sector} 应该有孔位")
        
        # 验证侧边栏全景图显示完整数据
        panorama_info = self.main_window.sidebar_panorama.info_label.text()
        self.assertIn("26 个孔位", panorama_info)  # 8+6+7+5=26个孔位
    
    def test_sector_selection_panorama_sync(self):
        """测试扇形选择与全景图同步"""
        # 选择第一个扇形
        self.main_window.on_sector_selected(SectorQuadrant.SECTOR_1)
        QTest.qWait(100)
        
        # 验证动态扇形显示切换到正确区域
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector, SectorQuadrant.SECTOR_1)
        
        # 验证主视图只显示当前扇形的孔位（专注显示）
        main_view = self.main_window.graphics_view
        if hasattr(main_view, 'hole_items'):
            displayed_holes = len(main_view.hole_items)
            # 扇形1应该有8个孔位
            self.assertEqual(displayed_holes, 8, f"主视图应显示扇形1的8个孔位，实际显示{displayed_holes}个")
        
        # 验证扇形统计信息更新
        stats_text = self.main_window.sector_stats_label.text()
        self.assertIn("区域1 (右上)", stats_text)
        self.assertIn("总孔位: 8", stats_text)
        
        # 选择另一个扇形验证切换
        self.main_window.on_sector_selected(SectorQuadrant.SECTOR_3)
        QTest.qWait(100)
        
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector, SectorQuadrant.SECTOR_3)
        
        # 验证主视图切换到扇形3的孔位
        if hasattr(main_view, 'hole_items'):
            displayed_holes = len(main_view.hole_items)
            # 扇形3应该有7个孔位
            self.assertEqual(displayed_holes, 7, f"主视图应显示扇形3的7个孔位，实际显示{displayed_holes}个")
        
        stats_text = self.main_window.sector_stats_label.text()
        self.assertIn("区域3 (左下)", stats_text)
        self.assertIn("总孔位: 7", stats_text)
    
    def test_dynamic_sector_change_integration(self):
        """测试动态扇形切换集成"""
        # 直接切换动态扇形显示
        self.main_window.dynamic_sector_display.switch_to_sector(SectorQuadrant.SECTOR_2)
        QTest.qWait(100)
        
        # 验证统计信息同步更新
        stats_text = self.main_window.sector_stats_label.text()
        self.assertIn("区域2 (左上)", stats_text)
        self.assertIn("总孔位: 6", stats_text)
    
    def test_panorama_status_sync(self):
        """测试全景图状态同步"""
        # 更改一些孔位状态
        test_holes = list(self.test_collection.holes.values())
        test_holes[0].status = HoleStatus.QUALIFIED
        test_holes[1].status = HoleStatus.DEFECTIVE
        test_holes[2].status = HoleStatus.BLIND
        
        # 更新状态显示
        self.main_window.update_status_display()
        QTest.qWait(100)
        
        # 验证扇形管理器更新
        for hole in test_holes[:3]:
            self.main_window.sector_manager.update_hole_status(hole.hole_id, hole.status)
        
        # 验证全景图状态同步（通过测试不会抛出异常来验证）
        try:
            self.main_window._update_panorama_hole_status(test_holes[0].hole_id, QColor(76, 175, 80))
            self.main_window._update_panorama_hole_status(test_holes[1].hole_id, QColor(244, 67, 54))
            panorama_sync_success = True
        except Exception:
            panorama_sync_success = False
        
        self.assertTrue(panorama_sync_success, "全景图状态同步应该成功")
    
    def test_layout_integrity(self):
        """测试布局完整性"""
        # 验证侧边栏全景图在正确位置
        self.assertTrue(self.main_window.sidebar_panorama.isVisible())
        
        # 验证主视图区域没有叠放的全景图
        main_display = self.main_window.dynamic_sector_display
        self.assertIsNotNone(main_display)
        
        # 验证扇形概览控制存在且可用
        sector_overview = self.main_window.sector_overview
        self.assertIsNotNone(sector_overview)
        self.assertTrue(sector_overview.isVisible())
        
        # 验证扇形统计标签存在
        stats_label = self.main_window.sector_stats_label
        self.assertIsNotNone(stats_label)
        self.assertTrue(stats_label.isVisible())
    
    def test_data_consistency_across_components(self):
        """测试组件间数据一致性"""
        # 获取扇形管理器中各扇形的孔位数
        sector_hole_counts = {}
        total_managed_holes = 0
        
        for sector in SectorQuadrant:
            sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
            sector_hole_counts[sector] = len(sector_holes)
            total_managed_holes += len(sector_holes)
        
        # 验证总数一致
        self.assertEqual(total_managed_holes, len(self.test_collection))
        
        # 验证动态扇形显示组件的数据一致性
        for sector in SectorQuadrant:
            sector_info = self.main_window.dynamic_sector_display.get_sector_info(sector)
            if sector_info:
                self.assertEqual(sector_info['hole_count'], sector_hole_counts[sector])
    
    def test_simulation_sector_tracking(self):
        """测试模拟系统的扇形追踪功能"""
        # 模拟扇形顺序检测
        sector_sequence = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                          SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
        
        for i, sector in enumerate(sector_sequence):
            # 模拟检测点移动到该扇形
            self.main_window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(100)
            
            # 验证主视图切换到对应扇形
            current_sector = self.main_window.dynamic_sector_display.get_current_sector()
            self.assertEqual(current_sector, sector, f"步骤{i+1}: 主视图应切换到{sector.value}")
            
            # 验证主视图只显示该扇形的孔位
            main_view = self.main_window.graphics_view
            if hasattr(main_view, 'hole_items'):
                displayed_holes = len(main_view.hole_items)
                sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
                expected_holes = len(sector_holes)
                self.assertEqual(displayed_holes, expected_holes, 
                               f"主视图应显示{sector.value}的{expected_holes}个孔位，实际{displayed_holes}个")
        
        # 验证侧边栏全景图始终显示完整数据
        panorama_info = self.main_window.sidebar_panorama.info_label.text()
        self.assertIn("26 个孔位", panorama_info, "侧边栏全景图应始终显示所有孔位")
    
    def test_performance_with_large_dataset(self):
        """测试大数据集性能"""
        # 创建更大的数据集
        large_holes = {}
        
        # 创建100个孔位分布在四个象限
        for i in range(100):
            x = (i % 10 - 5) * 20  # -100 到 100
            y = ((i // 10) % 10 - 5) * 20  # -100 到 100
            
            hole = HoleData(
                hole_id=f"HL{i:03d}",
                center_x=float(x),
                center_y=float(y),
                radius=2.5,
                status=HoleStatus.PENDING
            )
            large_holes[hole.hole_id] = hole
        
        large_collection = HoleCollection(
            holes=large_holes,
            metadata={'source_file': 'test_large.dxf', 'total_holes': len(large_holes)}
        )
        
        # 测试加载性能
        import time
        start_time = time.time()
        
        self.main_window.hole_collection = large_collection
        self.main_window.update_hole_display()
        QTest.qWait(500)  # 等待处理完成
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        # 验证加载时间合理（应小于5秒）
        self.assertLess(loading_time, 5.0, f"大数据集加载时间过长: {loading_time:.2f}秒")
        
        # 验证数据正确加载
        panorama_info = self.main_window.sidebar_panorama.info_label.text()
        self.assertIn("100 个孔位", panorama_info)


def run_tests():
    """运行测试"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()