"""
扇形视图组件单元测试
测试扇形可视化组件的显示和交互功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidcis2.graphics.sector_view import SectorOverviewWidget, SectorDetailView, SectorGraphicsItem
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress


class TestSectorGraphicsItem(unittest.TestCase):
    """扇形图形项单元测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.center = QPointF(0, 0)
        self.radius = 100
        self.sector_item = SectorGraphicsItem(
            SectorQuadrant.SECTOR_1, 
            self.center, 
            self.radius
        )
    
    def test_sector_item_initialization(self):
        """测试扇形图形项初始化"""
        self.assertEqual(self.sector_item.sector, SectorQuadrant.SECTOR_1)
        self.assertEqual(self.sector_item.center, self.center)
        self.assertEqual(self.sector_item.radius, self.radius)
        self.assertEqual(self.sector_item.start_angle, 0)  # SECTOR_1 应该从0度开始
        self.assertEqual(self.sector_item.span_angle, 90)
    
    def test_start_angle_mapping(self):
        """测试各扇形的起始角度映射"""
        test_cases = [
            (SectorQuadrant.SECTOR_1, 0),
            (SectorQuadrant.SECTOR_2, 90),
            (SectorQuadrant.SECTOR_3, 180),
            (SectorQuadrant.SECTOR_4, 270),
        ]
        
        for sector, expected_angle in test_cases:
            with self.subTest(sector=sector):
                item = SectorGraphicsItem(sector, self.center, self.radius)
                self.assertEqual(item.start_angle, expected_angle)
    
    def test_sector_name_mapping(self):
        """测试扇形名称映射"""
        test_cases = [
            (SectorQuadrant.SECTOR_1, "区域1"),
            (SectorQuadrant.SECTOR_2, "区域2"),
            (SectorQuadrant.SECTOR_3, "区域3"),
            (SectorQuadrant.SECTOR_4, "区域4"),
        ]
        
        for sector, expected_name in test_cases:
            with self.subTest(sector=sector):
                item = SectorGraphicsItem(sector, self.center, self.radius)
                self.assertEqual(item._get_sector_name(), expected_name)
    
    def test_update_progress(self):
        """测试进度更新"""
        # 创建测试进度数据
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=10,
            completed_holes=7,
            qualified_holes=6,
            defective_holes=1,
            progress_percentage=70.0,
            status_color=QColor(76, 175, 80)
        )
        
        # 更新进度
        self.sector_item.update_progress(progress)
        
        # 验证进度值被正确设置
        self.assertEqual(self.sector_item.progress, 70.0)
        self.assertEqual(self.sector_item.sector_color, progress.status_color)
        
        # 验证文本内容被更新
        expected_text = "区域1\n70.0%"
        self.assertEqual(self.sector_item.text_item.toPlainText(), expected_text)


class TestSectorOverviewWidget(unittest.TestCase):
    """扇形概览组件单元测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.overview_widget = SectorOverviewWidget()
        self.mock_sector_manager = Mock(spec=SectorManager)
    
    def test_widget_initialization(self):
        """测试组件初始化"""
        # 验证UI组件存在
        self.assertIsNotNone(self.overview_widget.graphics_view)
        self.assertIsNotNone(self.overview_widget.graphics_scene)
        self.assertIsNotNone(self.overview_widget.overall_progress_label)
        self.assertIsNotNone(self.overview_widget.overall_qualified_label)
        
        # 验证扇形图形项被创建
        self.assertEqual(len(self.overview_widget.sector_items), 4)
        
        # 验证所有扇形区域都有对应的图形项
        for sector in SectorQuadrant:
            self.assertIn(sector, self.overview_widget.sector_items)
    
    def test_set_sector_manager(self):
        """测试设置扇形管理器"""
        self.overview_widget.set_sector_manager(self.mock_sector_manager)
        self.assertEqual(self.overview_widget.sector_manager, self.mock_sector_manager)
    
    def test_update_sector_progress(self):
        """测试扇形进度更新"""
        # 创建测试进度数据
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=10,
            completed_holes=8,
            qualified_holes=7,
            defective_holes=1,
            progress_percentage=80.0,
            status_color=QColor(76, 175, 80)
        )
        
        # 更新进度
        self.overview_widget.update_sector_progress(SectorQuadrant.SECTOR_1, progress)
        
        # 验证对应的图形项被更新
        sector_item = self.overview_widget.sector_items[SectorQuadrant.SECTOR_1]
        self.assertEqual(sector_item.progress, 80.0)
    
    def test_update_overall_display(self):
        """测试整体显示更新"""
        overall_stats = {
            'total_holes': 40,
            'completed_holes': 30,
            'qualified_holes': 27,
            'defective_holes': 3
        }
        
        self.overview_widget.update_overall_display(overall_stats)
        
        # 验证标签文本被正确更新
        self.assertEqual(self.overview_widget.overall_progress_label.text(), "整体进度: 75.0%")
        self.assertEqual(self.overview_widget.overall_qualified_label.text(), "整体合格率: 90.0%")
    
    def test_update_overall_display_zero_cases(self):
        """测试零值情况的整体显示更新"""
        # 测试总孔位为0的情况
        overall_stats_empty = {
            'total_holes': 0,
            'completed_holes': 0,
            'qualified_holes': 0,
            'defective_holes': 0
        }
        
        self.overview_widget.update_overall_display(overall_stats_empty)
        self.assertEqual(self.overview_widget.overall_progress_label.text(), "整体进度: 0%")
        self.assertEqual(self.overview_widget.overall_qualified_label.text(), "整体合格率: 0%")
        
        # 测试完成孔位为0的情况
        overall_stats_pending = {
            'total_holes': 10,
            'completed_holes': 0,
            'qualified_holes': 0,
            'defective_holes': 0
        }
        
        self.overview_widget.update_overall_display(overall_stats_pending)
        self.assertEqual(self.overview_widget.overall_progress_label.text(), "整体进度: 0.0%")
        self.assertEqual(self.overview_widget.overall_qualified_label.text(), "整体合格率: 0%")


class TestSectorDetailView(unittest.TestCase):
    """扇形详细视图单元测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.detail_view = SectorDetailView()
        self.mock_sector_manager = Mock(spec=SectorManager)
    
    def test_widget_initialization(self):
        """测试组件初始化"""
        # 验证UI组件存在
        self.assertIsNotNone(self.detail_view.sector_title_label)
        self.assertIsNotNone(self.detail_view.progress_label)
        self.assertIsNotNone(self.detail_view.total_label)
        self.assertIsNotNone(self.detail_view.completed_label)
        self.assertIsNotNone(self.detail_view.qualified_label)
        self.assertIsNotNone(self.detail_view.defective_label)
        self.assertIsNotNone(self.detail_view.hole_list_widget)
    
    def test_set_sector_manager(self):
        """测试设置扇形管理器"""
        self.detail_view.set_sector_manager(self.mock_sector_manager)
        self.assertEqual(self.detail_view.sector_manager, self.mock_sector_manager)
    
    def test_update_sector_display(self):
        """测试扇形显示更新"""
        # 设置当前选中扇形
        self.detail_view.current_sector = SectorQuadrant.SECTOR_2
        
        # 创建测试进度数据
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_2,
            total_holes=12,
            completed_holes=9,
            qualified_holes=8,
            defective_holes=1,
            progress_percentage=75.0,
            status_color=QColor(255, 193, 7)
        )
        
        # 更新显示
        self.detail_view.update_sector_display(SectorQuadrant.SECTOR_2, progress)
        
        # 验证标签被正确更新
        self.assertEqual(self.detail_view.sector_title_label.text(), "区域2 (左上)")
        self.assertEqual(self.detail_view.progress_label.text(), "进度: 75.0%")
        self.assertEqual(self.detail_view.total_label.text(), "总数: 12")
        self.assertEqual(self.detail_view.completed_label.text(), "完成: 9")
        self.assertEqual(self.detail_view.qualified_label.text(), "合格: 8")
        self.assertEqual(self.detail_view.defective_label.text(), "异常: 1")
    
    def test_show_sector_detail(self):
        """测试显示扇形详情"""
        # 模拟扇形管理器
        mock_progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_3,
            total_holes=8,
            completed_holes=6,
            qualified_holes=5,
            defective_holes=1,
            progress_percentage=75.0,
            status_color=QColor(255, 152, 0)
        )
        
        self.mock_sector_manager.get_sector_progress.return_value = mock_progress
        self.mock_sector_manager.get_sector_holes.return_value = []
        
        self.detail_view.set_sector_manager(self.mock_sector_manager)
        self.detail_view.show_sector_detail(SectorQuadrant.SECTOR_3)
        
        # 验证当前扇形被设置
        self.assertEqual(self.detail_view.current_sector, SectorQuadrant.SECTOR_3)
        
        # 验证管理器方法被调用
        self.mock_sector_manager.get_sector_progress.assert_called_with(SectorQuadrant.SECTOR_3)
        self.mock_sector_manager.get_sector_holes.assert_called_with(SectorQuadrant.SECTOR_3)
    
    def test_display_hole_list_empty(self):
        """测试显示空孔位列表"""
        self.detail_view._display_hole_list([])
        self.assertEqual(self.detail_view.hole_list_widget.text(), "该区域暂无孔位")
    
    def test_display_hole_list_with_holes(self):
        """测试显示包含孔位的列表"""
        from aidcis2.models.hole_data import HoleStatus
        
        # 创建模拟孔位
        mock_holes = []
        for i in range(5):
            hole = Mock()
            hole.hole_id = f"H{i+1:03d}"
            hole.status = HoleStatus.QUALIFIED if i < 3 else HoleStatus.PENDING
            mock_holes.append(hole)
        
        self.detail_view._display_hole_list(mock_holes)
        
        # 验证列表文本包含孔位信息
        list_text = self.detail_view.hole_list_widget.text()
        self.assertIn("该区域包含 5 个孔位", list_text)
        self.assertIn("qualified: 3 个", list_text)
        self.assertIn("pending: 2 个", list_text)


if __name__ == '__main__':
    unittest.main()