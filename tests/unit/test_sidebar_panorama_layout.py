#!/usr/bin/env python3
"""
侧边栏全景图布局单元测试
测试侧边栏全景图组件的基本功能和布局正确性
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from main_window.main_window import MainWindow
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestSidebarPanoramaLayout(unittest.TestCase):
    """侧边栏全景图布局测试类"""
    
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
        QTest.qWait(100)  # 等待UI初始化
    
    def tearDown(self):
        """清理每个测试"""
        if self.main_window:
            self.main_window.close()
        QTest.qWait(100)
    
    def test_sidebar_panorama_exists(self):
        """测试侧边栏全景图组件存在"""
        self.assertTrue(hasattr(self.main_window, 'sidebar_panorama'))
        self.assertIsInstance(self.main_window.sidebar_panorama, CompletePanoramaWidget)
        self.assertIsNotNone(self.main_window.sidebar_panorama)
    
    def test_sidebar_panorama_visible(self):
        """测试侧边栏全景图组件可见"""
        self.main_window.show()
        QTest.qWait(100)
        
        self.assertTrue(self.main_window.sidebar_panorama.isVisible())
        self.assertTrue(self.main_window.sidebar_panorama.isEnabled())
    
    def test_sidebar_panorama_size(self):
        """测试侧边栏全景图组件尺寸"""
        size = self.main_window.sidebar_panorama.size()
        self.assertEqual(size.width(), 200)
        self.assertEqual(size.height(), 180)
    
    def test_no_overlaid_panorama(self):
        """测试不再有叠放的全景图"""
        # 确保没有叠放的complete_panorama
        self.assertFalse(hasattr(self.main_window, 'complete_panorama'))
    
    def test_sidebar_panorama_data_loading(self):
        """测试侧边栏全景图数据加载"""
        # 创建测试数据 - 分布在不同象限以确保扇形划分
        test_holes = {}
        positions = [
            (50, 50), (-50, 50), (-50, -50), (50, -50),  # 四个象限各一个
            (60, 60), (-60, 60), (-60, -60), (60, -60),  # 四个象限再各一个
            (30, 40), (-30, 40)  # 上方两个象限再各一个
        ]
        
        for i, (x, y) in enumerate(positions):
            hole = HoleData(
                hole_id=f"H{i:03d}",
                center_x=float(x),
                center_y=float(y),
                radius=2.5,
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test.dxf', 'total_holes': len(test_holes)}
        )
        
        # 设置孔位集合
        self.main_window.hole_collection = test_collection
        
        # 调用更新显示
        self.main_window.update_hole_display()
        
        # 验证侧边栏全景图已加载数据
        panorama_view = self.main_window.sidebar_panorama.panorama_view
        self.assertIsNotNone(panorama_view)
        
        # 验证信息标签更新
        info_text = self.main_window.sidebar_panorama.info_label.text()
        self.assertIn("10 个孔位", info_text)
        
        # 验证动态扇形显示组件已初始化并显示第一个扇形
        self.assertIsNotNone(self.main_window.dynamic_sector_display)
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector.value, "sector_1")
    
    def test_sidebar_panorama_positioning(self):
        """测试侧边栏全景图位置"""
        self.main_window.show()
        QTest.qWait(100)
        
        # 获取左侧面板
        left_panel = None
        for child in self.main_window.findChildren(type(self.main_window.sidebar_panorama.parent())):
            if "全景预览" in str(child.title() if hasattr(child, 'title') else ''):
                left_panel = child
                break
        
        # 验证全景图在左侧面板中
        self.assertIsNotNone(left_panel)
        panorama_parent = self.main_window.sidebar_panorama.parent()
        self.assertIsNotNone(panorama_parent)
    
    def test_sector_stats_label_exists(self):
        """测试扇形统计标签存在"""
        self.assertTrue(hasattr(self.main_window, 'sector_stats_label'))
        self.assertIsNotNone(self.main_window.sector_stats_label)
    
    def test_sector_stats_update(self):
        """测试扇形统计信息更新"""
        from aidcis2.graphics.sector_manager import SectorQuadrant
        
        # 创建测试数据
        test_holes = {}
        for i in range(20):
            hole = HoleData(
                hole_id=f"H{i:03d}",
                center_x=float(i % 4 * 10),  # 分布在不同位置
                center_y=float(i // 4 * 10),
                radius=2.5,
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test.dxf', 'total_holes': len(test_holes)}
        )
        
        # 设置数据
        self.main_window.hole_collection = test_collection
        self.main_window.update_hole_display()
        
        # 模拟选择扇形
        self.main_window.on_sector_selected(SectorQuadrant.SECTOR_1)
        
        # 验证统计信息已更新
        stats_text = self.main_window.sector_stats_label.text()
        self.assertIn("区域1", stats_text)
        self.assertIn("总孔位", stats_text)
    
    def test_dynamic_sector_display_exists(self):
        """测试动态扇形显示组件存在"""
        self.assertTrue(hasattr(self.main_window, 'dynamic_sector_display'))
        self.assertIsNotNone(self.main_window.dynamic_sector_display)
    
    def test_sector_focused_display(self):
        """测试扇形专注显示功能"""
        # 创建分布在不同扇形的测试数据
        test_holes = {}
        sector_positions = {
            'sector_1': [(50, 50), (60, 60), (70, 40)],  # 右上
            'sector_2': [(-50, 50), (-60, 60), (-40, 70)],  # 左上
            'sector_3': [(-50, -50), (-60, -60), (-40, -70)],  # 左下
            'sector_4': [(50, -50), (60, -60), (40, -70)]   # 右下
        }
        
        hole_counter = 0
        for sector, positions in sector_positions.items():
            for x, y in positions:
                hole = HoleData(
                    hole_id=f"H{hole_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_counter += 1
        
        test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test_sector.dxf', 'total_holes': len(test_holes)}
        )
        
        # 设置数据
        self.main_window.hole_collection = test_collection
        self.main_window.update_hole_display()
        
        # 验证主视图显示的是第一个扇形（不是全景）
        main_view = self.main_window.graphics_view
        self.assertIsNotNone(main_view)
        
        # 主视图应该只显示第一个扇形的孔位，而不是全部12个孔位
        if hasattr(main_view, 'hole_items'):
            displayed_holes = len(main_view.hole_items)
            self.assertLess(displayed_holes, 12, "主视图应显示扇形专注内容，而不是完整全景")
            self.assertGreater(displayed_holes, 0, "主视图应显示当前扇形的孔位")
        
        # 验证侧边栏全景图显示所有孔位
        panorama_view = self.main_window.sidebar_panorama.panorama_view
        self.assertIsNotNone(panorama_view)
        info_text = self.main_window.sidebar_panorama.info_label.text()
        self.assertIn("12 个孔位", info_text, "侧边栏全景图应显示所有孔位")
    
    def test_panorama_sync_with_main_view(self):
        """测试全景图与主视图同步"""
        # 创建测试数据 - 分布在第一象限
        test_holes = {}
        for i in range(5):
            hole = HoleData(
                hole_id=f"H{i:03d}",
                center_x=float(20 + i * 10),  # 确保在第一象限
                center_y=float(20 + i * 5),
                radius=2.5,
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'test.dxf', 'total_holes': len(test_holes)}
        )
        
        # 设置数据
        self.main_window.hole_collection = test_collection
        self.main_window.update_hole_display()
        
        # 验证主视图和全景图都有数据
        main_view = self.main_window.graphics_view
        panorama_view = self.main_window.sidebar_panorama.panorama_view
        
        self.assertIsNotNone(main_view)
        self.assertIsNotNone(panorama_view)


def run_tests():
    """运行测试"""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()