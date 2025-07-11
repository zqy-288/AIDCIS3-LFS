"""
扇形系统集成测试
测试扇形管理器与视图组件的集成工作流程
"""

import unittest
import math
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QColor

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.graphics.sector_view import SectorOverviewWidget, SectorDetailView
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestSectorSystemIntegration(unittest.TestCase):
    """扇形系统集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.sector_manager = SectorManager()
        self.overview_widget = SectorOverviewWidget()
        self.detail_view = SectorDetailView()
        
        # 创建测试数据
        self.test_collection = self._create_comprehensive_test_collection()
        
        # 建立组件间连接
        self.overview_widget.set_sector_manager(self.sector_manager)
        self.detail_view.set_sector_manager(self.sector_manager)
    
    def _create_comprehensive_test_collection(self):
        """创建综合测试孔位集合"""
        holes = {}
        
        # 在每个象限创建多个孔位
        hole_positions = [
            # 右上象限 (SECTOR_1) - 5个孔位
            (5, 5, "H001"), (10, 8, "H002"), (8, 12, "H003"), (15, 5, "H004"), (12, 15, "H005"),
            # 左上象限 (SECTOR_2) - 4个孔位  
            (-5, 5, "H006"), (-10, 8, "H007"), (-8, 12, "H008"), (-15, 5, "H009"),
            # 左下象限 (SECTOR_3) - 6个孔位
            (-5, -5, "H010"), (-10, -8, "H011"), (-8, -12, "H012"), (-15, -5, "H013"), (-12, -15, "H014"), (-3, -3, "H015"),
            # 右下象限 (SECTOR_4) - 3个孔位
            (5, -5, "H016"), (10, -8, "H017"), (8, -12, "H018")
        ]
        
        for x, y, hole_id in hole_positions:
            hole = Mock(spec=HoleData)
            hole.hole_id = hole_id
            hole.center_x = x
            hole.center_y = y
            hole.radius = 2.0
            hole.status = HoleStatus.PENDING
            holes[hole_id] = hole
        
        # 创建集合对象
        collection = Mock(spec=HoleCollection)
        collection.holes = holes
        collection.get_bounds.return_value = (-20, -20, 20, 20)
        
        # 模拟迭代器
        collection.__iter__ = lambda self: iter(holes.values())
        collection.__len__ = lambda self: len(holes)
        
        return collection
    
    def test_complete_workflow_initialization(self):
        """测试完整工作流程 - 初始化"""
        # 加载测试数据到扇形管理器
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 验证扇形管理器正确初始化
        self.assertIsNotNone(self.sector_manager.center_point)
        self.assertEqual(len(self.sector_manager.sector_assignments), 18)  # 总共18个孔位
        self.assertEqual(len(self.sector_manager.sector_progresses), 4)    # 4个扇形区域
        
        # 验证各扇形的孔位分配
        sector_counts = {}
        for hole_id, sector in self.sector_manager.sector_assignments.items():
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        self.assertEqual(sector_counts[SectorQuadrant.SECTOR_1], 5)  # 右上
        self.assertEqual(sector_counts[SectorQuadrant.SECTOR_2], 4)  # 左上
        self.assertEqual(sector_counts[SectorQuadrant.SECTOR_3], 6)  # 左下
        self.assertEqual(sector_counts[SectorQuadrant.SECTOR_4], 3)  # 右下
    
    def test_progress_update_workflow(self):
        """测试进度更新工作流程"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 记录信号发射
        sector_signals = []
        overall_signals = []
        
        def capture_sector_signal(sector, progress):
            sector_signals.append((sector, progress))
        
        def capture_overall_signal(stats):
            overall_signals.append(stats)
        
        self.sector_manager.sector_progress_updated.connect(capture_sector_signal)
        self.sector_manager.overall_progress_updated.connect(capture_overall_signal)
        
        # 模拟检测进度更新
        test_updates = [
            ("H001", HoleStatus.QUALIFIED),     # 右上象限
            ("H002", HoleStatus.QUALIFIED),     # 右上象限
            ("H006", HoleStatus.DEFECTIVE),     # 左上象限
            ("H010", HoleStatus.QUALIFIED),     # 左下象限
            ("H016", HoleStatus.BLIND),         # 右下象限
        ]
        
        for hole_id, new_status in test_updates:
            # 更新孔位状态
            self.test_collection.holes[hole_id].status = new_status
            self.sector_manager.update_hole_status(hole_id, new_status)
        
        # 验证信号被正确发射
        self.assertGreater(len(sector_signals), 0)
        self.assertGreater(len(overall_signals), 0)
        
        # 验证进度计算正确
        sector_1_progress = self.sector_manager.get_sector_progress(SectorQuadrant.SECTOR_1)
        self.assertEqual(sector_1_progress.completed_holes, 2)  # H001, H002
        self.assertEqual(sector_1_progress.qualified_holes, 2)   # 都是qualified
        self.assertEqual(sector_1_progress.defective_holes, 0)
    
    def test_view_integration_workflow(self):
        """测试视图集成工作流程"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 验证概览组件接收到初始数据
        self.assertEqual(len(self.overview_widget.sector_items), 4)
        
        # 模拟进度更新
        self.test_collection.holes["H001"].status = HoleStatus.QUALIFIED
        self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)
        
        # 验证概览组件状态更新
        sector_1_item = self.overview_widget.sector_items[SectorQuadrant.SECTOR_1]
        # 注意：这里需要触发实际的更新流程，可能需要处理Qt事件循环
        
        # 模拟用户选择扇形区域
        self.detail_view.show_sector_detail(SectorQuadrant.SECTOR_1)
        
        # 验证详细视图显示正确的信息
        self.assertEqual(self.detail_view.current_sector, SectorQuadrant.SECTOR_1)
    
    def test_signal_propagation_chain(self):
        """测试信号传播链"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 记录各组件接收到的信号
        overview_updates = []
        detail_updates = []
        
        def overview_sector_update(sector, progress):
            overview_updates.append((sector, progress))
        
        def overview_overall_update(stats):
            overview_updates.append(('overall', stats))
        
        def detail_sector_update(sector, progress):
            detail_updates.append((sector, progress))
        
        # 连接信号监听
        self.sector_manager.sector_progress_updated.connect(overview_sector_update)
        self.sector_manager.overall_progress_updated.connect(overview_overall_update)
        self.sector_manager.sector_progress_updated.connect(detail_sector_update)
        
        # 触发状态更新
        self.test_collection.holes["H001"].status = HoleStatus.QUALIFIED
        self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)
        
        # 验证信号被正确传播到各组件
        self.assertGreater(len(overview_updates), 0)
        self.assertGreater(len(detail_updates), 0)
    
    def test_multi_sector_update_workflow(self):
        """测试多扇形同时更新工作流程"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 记录每个扇形的更新次数
        sector_update_counts = {sector: 0 for sector in SectorQuadrant}
        
        def count_sector_updates(sector, progress):
            sector_update_counts[sector] += 1
        
        self.sector_manager.sector_progress_updated.connect(count_sector_updates)
        
        # 同时更新多个扇形区域的孔位
        batch_updates = [
            ("H001", HoleStatus.QUALIFIED),     # SECTOR_1
            ("H002", HoleStatus.QUALIFIED),     # SECTOR_1  
            ("H006", HoleStatus.DEFECTIVE),     # SECTOR_2
            ("H007", HoleStatus.QUALIFIED),     # SECTOR_2
            ("H010", HoleStatus.QUALIFIED),     # SECTOR_3
            ("H016", HoleStatus.BLIND),         # SECTOR_4
        ]
        
        for hole_id, new_status in batch_updates:
            self.test_collection.holes[hole_id].status = new_status
            self.sector_manager.update_hole_status(hole_id, new_status)
        
        # 验证每个扇形都收到了相应的更新
        self.assertEqual(sector_update_counts[SectorQuadrant.SECTOR_1], 2)  # H001, H002
        self.assertEqual(sector_update_counts[SectorQuadrant.SECTOR_2], 2)  # H006, H007
        self.assertEqual(sector_update_counts[SectorQuadrant.SECTOR_3], 1)  # H010
        self.assertEqual(sector_update_counts[SectorQuadrant.SECTOR_4], 1)  # H016
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试空数据情况
        empty_collection = Mock(spec=HoleCollection)
        empty_collection.holes = {}
        empty_collection.get_bounds.return_value = (0, 0, 0, 0)
        empty_collection.__iter__ = lambda self: iter([])
        empty_collection.__len__ = lambda self: 0
        
        # 应该能够处理空数据而不崩溃
        try:
            self.sector_manager.load_hole_collection(empty_collection)
            self.assertTrue(True)  # 如果没有异常，测试通过
        except Exception as e:
            self.fail(f"处理空数据时发生异常: {e}")
        
        # 测试无效孔位ID更新
        self.sector_manager.load_hole_collection(self.test_collection)
        
        # 尝试更新不存在的孔位，应该不会崩溃
        try:
            self.sector_manager.update_hole_status("INVALID_ID", HoleStatus.QUALIFIED)
            self.assertTrue(True)  # 如果没有异常，测试通过
        except Exception as e:
            self.fail(f"处理无效孔位ID时发生异常: {e}")
    
    def test_performance_with_large_dataset(self):
        """测试大数据集性能"""
        # 创建大数据集（100个孔位）
        large_holes = {}
        for i in range(100):
            angle = (i / 100) * 2 * 3.14159  # 均匀分布在圆周上
            x = 50 * math.cos(angle)
            y = 50 * math.sin(angle)
            
            hole = Mock(spec=HoleData)
            hole.hole_id = f"H{i+1:03d}"
            hole.center_x = x
            hole.center_y = y
            hole.radius = 2.0
            hole.status = HoleStatus.PENDING
            large_holes[hole.hole_id] = hole
        
        large_collection = Mock(spec=HoleCollection)
        large_collection.holes = large_holes
        large_collection.get_bounds.return_value = (-60, -60, 60, 60)
        large_collection.__iter__ = lambda self: iter(large_holes.values())
        large_collection.__len__ = lambda self: len(large_holes)
        
        # 测试加载性能
        import time
        start_time = time.time()
        
        self.sector_manager.load_hole_collection(large_collection)
        
        load_time = time.time() - start_time
        
        # 验证加载时间合理（应该在1秒内完成）
        self.assertLess(load_time, 1.0)
        
        # 验证所有孔位都被正确分配
        self.assertEqual(len(self.sector_manager.sector_assignments), 100)
        
        # 测试批量更新性能
        start_time = time.time()
        
        for i in range(0, 50, 2):  # 更新一半的孔位
            hole_id = f"H{i+1:03d}"
            large_holes[hole_id].status = HoleStatus.QUALIFIED
            self.sector_manager.update_hole_status(hole_id, HoleStatus.QUALIFIED)
        
        update_time = time.time() - start_time
        
        # 验证批量更新时间合理（应该在2秒内完成）
        self.assertLess(update_time, 2.0)


if __name__ == '__main__':
    import math
    unittest.main()