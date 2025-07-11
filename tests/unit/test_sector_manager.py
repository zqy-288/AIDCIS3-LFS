"""
扇形管理器单元测试
测试扇形区域划分、进度计算等核心功能
"""

import unittest
import math
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestSectorManager(unittest.TestCase):
    """扇形管理器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.sector_manager = SectorManager()
        self.test_holes = self._create_test_holes()
        self.test_collection = self._create_test_collection()
    
    def _create_test_holes(self):
        """创建测试孔位数据"""
        holes = []
        # 创建4个象限各有孔位的测试数据
        test_positions = [
            (10, 10, "H001"),   # 右上 - SECTOR_1
            (-10, 10, "H002"),  # 左上 - SECTOR_2  
            (-10, -10, "H003"), # 左下 - SECTOR_3
            (10, -10, "H004"),  # 右下 - SECTOR_4
            (15, 15, "H005"),   # 右上 - SECTOR_1
            (-15, 15, "H006"),  # 左上 - SECTOR_2
        ]
        
        for x, y, hole_id in test_positions:
            hole = Mock(spec=HoleData)
            hole.hole_id = hole_id
            hole.center_x = x
            hole.center_y = y
            hole.radius = 2.0
            hole.status = HoleStatus.PENDING
            holes.append(hole)
        
        return holes
    
    def _create_test_collection(self):
        """创建测试孔位集合"""
        # 使用真实的字典而不是Mock来避免迭代问题
        class SimpleHoleCollection:
            def __init__(self, holes_dict):
                self.holes = holes_dict
            
            def get_bounds(self):
                return (-20, -20, 20, 20)
        
        holes_dict = {hole.hole_id: hole for hole in self.test_holes}
        return SimpleHoleCollection(holes_dict)
    
    def test_calculate_center_point(self):
        """测试中心点计算"""
        self.sector_manager.hole_collection = self.test_collection
        center = self.sector_manager._calculate_center_point()
        
        # 应该计算出中心点为 (0, 0)
        self.assertEqual(center.x(), 0.0)
        self.assertEqual(center.y(), 0.0)
    
    def test_get_hole_sector(self):
        """测试孔位扇形区域判断"""
        self.sector_manager.center_point = QPointF(0, 0)
        
        # 测试各象限的孔位分配
        test_cases = [
            (self.test_holes[0], SectorQuadrant.SECTOR_1),  # (10, 10) -> 右上
            (self.test_holes[1], SectorQuadrant.SECTOR_2),  # (-10, 10) -> 左上
            (self.test_holes[2], SectorQuadrant.SECTOR_3),  # (-10, -10) -> 左下
            (self.test_holes[3], SectorQuadrant.SECTOR_4),  # (10, -10) -> 右下
        ]
        
        for hole, expected_sector in test_cases:
            with self.subTest(hole=hole.hole_id):
                sector = self.sector_manager._get_hole_sector(hole)
                self.assertEqual(sector, expected_sector)
    
    def test_assign_holes_to_sectors(self):
        """测试孔位扇形分配"""
        self.sector_manager.hole_collection = self.test_collection
        self.sector_manager.center_point = QPointF(0, 0)
        self.sector_manager._assign_holes_to_sectors()
        
        # 验证分配结果
        assignments = self.sector_manager.sector_assignments
        
        self.assertEqual(assignments["H001"], SectorQuadrant.SECTOR_1)
        self.assertEqual(assignments["H002"], SectorQuadrant.SECTOR_2)
        self.assertEqual(assignments["H003"], SectorQuadrant.SECTOR_3)
        self.assertEqual(assignments["H004"], SectorQuadrant.SECTOR_4)
        self.assertEqual(assignments["H005"], SectorQuadrant.SECTOR_1)  # 也在右上
        self.assertEqual(assignments["H006"], SectorQuadrant.SECTOR_2)  # 也在左上
    
    def test_initialize_sector_progress(self):
        """测试扇形进度初始化"""
        self.sector_manager.hole_collection = self.test_collection
        self.sector_manager.center_point = QPointF(0, 0)
        self.sector_manager._assign_holes_to_sectors()
        self.sector_manager._initialize_sector_progress()
        
        # 验证各扇形的孔位数量统计
        progresses = self.sector_manager.sector_progresses
        
        self.assertEqual(progresses[SectorQuadrant.SECTOR_1].total_holes, 2)  # H001, H005
        self.assertEqual(progresses[SectorQuadrant.SECTOR_2].total_holes, 2)  # H002, H006
        self.assertEqual(progresses[SectorQuadrant.SECTOR_3].total_holes, 1)  # H003
        self.assertEqual(progresses[SectorQuadrant.SECTOR_4].total_holes, 1)  # H004
    
    def test_update_hole_status(self):
        """测试孔位状态更新"""
        # 初始化
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 模拟信号发射
        with patch.object(self.sector_manager, 'sector_progress_updated') as mock_signal:
            # 更新一个孔位状态
            self.test_holes[0].status = HoleStatus.QUALIFIED
            self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)
            
            # 验证信号被发射
            mock_signal.emit.assert_called_once()
            
            # 验证进度计算正确
            sector_1_progress = self.sector_manager.get_sector_progress(SectorQuadrant.SECTOR_1)
            self.assertIsNotNone(sector_1_progress)
    
    def test_get_progress_color(self):
        """测试进度颜色计算"""
        test_cases = [
            (95.0, QColor(76, 175, 80)),    # 绿色 - 高完成度
            (75.0, QColor(255, 193, 7)),    # 黄色 - 中等完成度
            (45.0, QColor(255, 152, 0)),    # 橙色 - 较低完成度
            (15.0, QColor(244, 67, 54)),    # 红色 - 低完成度
        ]
        
        for completion_rate, expected_color in test_cases:
            with self.subTest(rate=completion_rate):
                color = self.sector_manager._get_progress_color(completion_rate)
                self.assertEqual(color.red(), expected_color.red())
                self.assertEqual(color.green(), expected_color.green())
                self.assertEqual(color.blue(), expected_color.blue())
    
    def test_get_sector_holes(self):
        """测试获取扇形区域孔位"""
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 获取右上扇形的孔位
        sector_1_holes = self.sector_manager.get_sector_holes(SectorQuadrant.SECTOR_1)
        
        # 验证孔位数量和ID
        self.assertEqual(len(sector_1_holes), 2)
        hole_ids = [hole.hole_id for hole in sector_1_holes]
        self.assertIn("H001", hole_ids)
        self.assertIn("H005", hole_ids)
    
    def test_angle_calculation_edge_cases(self):
        """测试角度计算的边界情况"""
        self.sector_manager.center_point = QPointF(0, 0)
        
        # 测试边界角度的孔位
        edge_cases = [
            (1, 0, SectorQuadrant.SECTOR_1),    # 0度边界
            (0, 1, SectorQuadrant.SECTOR_2),    # 90度边界
            (-1, 0, SectorQuadrant.SECTOR_3),   # 180度边界
            (0, -1, SectorQuadrant.SECTOR_4),   # 270度边界
        ]
        
        for x, y, expected_sector in edge_cases:
            with self.subTest(x=x, y=y):
                hole = Mock(spec=HoleData)
                hole.center_x = x
                hole.center_y = y
                sector = self.sector_manager._get_hole_sector(hole)
                self.assertEqual(sector, expected_sector)


class TestSectorProgress(unittest.TestCase):
    """扇形进度数据单元测试"""
    
    def test_completion_rate_calculation(self):
        """测试完成率计算"""
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=10,
            completed_holes=7,
            qualified_holes=6,
            defective_holes=1,
            progress_percentage=0.0,
            status_color=QColor(0, 255, 0)
        )
        
        self.assertEqual(progress.completion_rate, 70.0)
    
    def test_qualification_rate_calculation(self):
        """测试合格率计算"""
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=10,
            completed_holes=8,
            qualified_holes=7,
            defective_holes=1,
            progress_percentage=0.0,
            status_color=QColor(0, 255, 0)
        )
        
        self.assertEqual(progress.qualification_rate, 87.5)
    
    def test_zero_division_handling(self):
        """测试零除错误处理"""
        # 测试总孔位为0的情况
        progress_empty = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=0,
            completed_holes=0,
            qualified_holes=0,
            defective_holes=0,
            progress_percentage=0.0,
            status_color=QColor(128, 128, 128)
        )
        
        self.assertEqual(progress_empty.completion_rate, 0.0)
        self.assertEqual(progress_empty.qualification_rate, 0.0)
        
        # 测试完成孔位为0的情况
        progress_pending = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=5,
            completed_holes=0,
            qualified_holes=0,
            defective_holes=0,
            progress_percentage=0.0,
            status_color=QColor(128, 128, 128)
        )
        
        self.assertEqual(progress_pending.completion_rate, 0.0)
        self.assertEqual(progress_pending.qualification_rate, 0.0)


if __name__ == '__main__':
    unittest.main()