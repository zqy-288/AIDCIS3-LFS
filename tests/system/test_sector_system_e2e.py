"""
扇形系统端到端测试
测试完整的用户工作流程和系统功能
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer, QEventLoop, QPointF
from PySide6.QtTest import QTest
from PySide6.QtGui import QColor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.graphics.sector_view import SectorOverviewWidget, SectorDetailView
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestSectorSystemEndToEnd(unittest.TestCase):
    """扇形系统端到端测试"""
    
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
        
        # 创建模拟的主窗口环境
        self.main_window = self._create_mock_main_window()
        
        # 建立完整的连接
        self.overview_widget.set_sector_manager(self.sector_manager)
        self.detail_view.set_sector_manager(self.sector_manager)
        self.overview_widget.sector_selected.connect(self._on_sector_selected)
        
        # 创建真实的DXF测试数据
        self.dxf_collection = self._create_realistic_dxf_collection()
    
    def _create_mock_main_window(self):
        """创建模拟主窗口"""
        main_window = QMainWindow()
        main_window.resize(1200, 800)
        
        # 模拟日志方法
        main_window.log_message = Mock()
        
        return main_window
    
    def _create_realistic_dxf_collection(self):
        """创建真实的DXF样式孔位集合"""
        holes = {}
        
        # 模拟真实的管板布局：8x6网格，48个孔位
        rows = 8
        cols = 6
        hole_spacing = 10  # 孔间距
        start_x = -(cols - 1) * hole_spacing / 2
        start_y = -(rows - 1) * hole_spacing / 2
        
        hole_index = 1
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * hole_spacing
                y = start_y + row * hole_spacing
                
                hole_id = f"H{hole_index:05d}"
                
                hole = Mock(spec=HoleData)
                hole.hole_id = hole_id
                hole.center_x = x
                hole.center_y = y
                hole.radius = 2.5
                hole.status = HoleStatus.PENDING
                
                holes[hole_id] = hole
                hole_index += 1
        
        # 创建集合对象
        collection = Mock(spec=HoleCollection)
        collection.holes = holes
        collection.get_bounds.return_value = (start_x - 5, start_y - 5, -start_x + 5, -start_y + 5)
        collection.__iter__ = lambda self: iter(holes.values())
        collection.__len__ = lambda self: len(holes)
        
        return collection
    
    def _on_sector_selected(self, sector):
        """处理扇形选择"""
        self.detail_view.show_sector_detail(sector)
    
    def test_complete_user_workflow(self):
        """测试完整用户工作流程"""
        # 步骤1: 系统初始化 - 加载DXF数据
        self.sector_manager.load_hole_collection(self.dxf_collection)
        
        # 验证数据加载成功
        self.assertEqual(len(self.sector_manager.sector_assignments), 48)
        self.assertIsNotNone(self.sector_manager.center_point)
        
        # 验证4个扇形区域都有孔位分配
        sector_counts = {}
        for hole_id, sector in self.sector_manager.sector_assignments.items():
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        self.assertEqual(len(sector_counts), 4)  # 应该有4个扇形区域
        for sector, count in sector_counts.items():
            self.assertGreater(count, 0)  # 每个扇形都应该有孔位
        
        # 步骤2: 用户查看初始状态
        # 验证概览组件显示初始状态
        for sector in SectorQuadrant:
            progress = self.sector_manager.get_sector_progress(sector)
            self.assertIsNotNone(progress)
            self.assertEqual(progress.completed_holes, 0)  # 初始状态都是待检
        
        # 步骤3: 模拟检测进度推进
        test_scenarios = [
            # 场景1: 右上区域开始检测
            {"sector": SectorQuadrant.SECTOR_1, "completed_ratio": 0.3, "defect_ratio": 0.1},
            # 场景2: 左上区域检测进展
            {"sector": SectorQuadrant.SECTOR_2, "completed_ratio": 0.6, "defect_ratio": 0.05},
            # 场景3: 左下区域检测完成
            {"sector": SectorQuadrant.SECTOR_3, "completed_ratio": 1.0, "defect_ratio": 0.08},
            # 场景4: 右下区域部分检测
            {"sector": SectorQuadrant.SECTOR_4, "completed_ratio": 0.4, "defect_ratio": 0.15},
        ]
        
        for scenario in test_scenarios:
            self._simulate_sector_detection(scenario)
        
        # 步骤4: 验证进度统计正确性
        self._verify_progress_statistics()
        
        # 步骤5: 用户交互测试 - 选择扇形查看详情
        self._test_user_interaction()
    
    def _simulate_sector_detection(self, scenario):
        """模拟扇形区域检测过程"""
        sector = scenario["sector"]
        completed_ratio = scenario["completed_ratio"]
        defect_ratio = scenario["defect_ratio"]
        
        # 获取该扇形的所有孔位
        sector_holes = self.sector_manager.get_sector_holes(sector)
        total_holes = len(sector_holes)
        
        # 计算要完成的孔位数量
        completed_count = int(total_holes * completed_ratio)
        defect_count = int(completed_count * defect_ratio)
        qualified_count = completed_count - defect_count
        
        # 随机选择孔位进行状态更新
        import random
        selected_holes = random.sample(sector_holes, completed_count)
        
        for i, hole in enumerate(selected_holes):
            if i < defect_count:
                new_status = HoleStatus.DEFECTIVE
            else:
                new_status = HoleStatus.QUALIFIED
            
            hole.status = new_status
            self.sector_manager.update_hole_status(hole.hole_id, new_status)
        
        # 验证该扇形的进度被正确更新
        progress = self.sector_manager.get_sector_progress(sector)
        self.assertEqual(progress.completed_holes, completed_count)
        self.assertEqual(progress.qualified_holes, qualified_count)
        self.assertEqual(progress.defective_holes, defect_count)
    
    def _verify_progress_statistics(self):
        """验证进度统计的正确性"""
        # 收集所有扇形的统计数据
        total_holes = 0
        total_completed = 0
        total_qualified = 0
        total_defective = 0
        
        for sector in SectorQuadrant:
            progress = self.sector_manager.get_sector_progress(sector)
            total_holes += progress.total_holes
            total_completed += progress.completed_holes
            total_qualified += progress.qualified_holes
            total_defective += progress.defective_holes
        
        # 验证总数一致性
        self.assertEqual(total_holes, 48)  # 应该等于DXF中的总孔位数
        self.assertEqual(total_completed, total_qualified + total_defective)
        
        # 验证比例计算
        if total_holes > 0:
            overall_completion_rate = (total_completed / total_holes) * 100
            self.assertGreaterEqual(overall_completion_rate, 0)
            self.assertLessEqual(overall_completion_rate, 100)
        
        if total_completed > 0:
            overall_qualification_rate = (total_qualified / total_completed) * 100
            self.assertGreaterEqual(overall_qualification_rate, 0)
            self.assertLessEqual(overall_qualification_rate, 100)
    
    def _test_user_interaction(self):
        """测试用户交互功能"""
        # 测试选择不同扇形区域
        for sector in SectorQuadrant:
            # 模拟用户点击扇形
            self.detail_view.show_sector_detail(sector)
            
            # 验证详细视图更新
            self.assertEqual(self.detail_view.current_sector, sector)
            
            # 验证统计信息显示
            progress = self.sector_manager.get_sector_progress(sector)
            self.assertIsNotNone(progress)
            
            # 验证孔位列表显示
            sector_holes = self.sector_manager.get_sector_holes(sector)
            self.assertGreater(len(sector_holes), 0)
    
    def test_real_time_updates(self):
        """测试实时更新功能"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.dxf_collection)
        
        # 记录更新事件
        update_events = []
        
        def record_update(sector, progress):
            update_events.append({
                'timestamp': time.time(),
                'sector': sector,
                'progress': progress.progress_percentage
            })
        
        self.sector_manager.sector_progress_updated.connect(record_update)
        
        # 模拟连续的状态更新
        test_holes = list(self.dxf_collection.holes.values())[:10]  # 取前10个孔位
        
        for i, hole in enumerate(test_holes):
            hole.status = HoleStatus.QUALIFIED
            self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.QUALIFIED)
            
            # 短暂等待以确保信号处理
            self.app.processEvents()
        
        # 验证实时更新
        self.assertGreater(len(update_events), 0)
        
        # 验证更新的时序性
        for i in range(1, len(update_events)):
            self.assertGreaterEqual(
                update_events[i]['timestamp'], 
                update_events[i-1]['timestamp']
            )
    
    def test_performance_benchmarks(self):
        """测试性能基准"""
        # 测试大量数据的处理性能
        large_collection = self._create_large_test_collection(500)  # 500个孔位
        
        # 测试加载性能
        start_time = time.time()
        self.sector_manager.load_hole_collection(large_collection)
        load_time = time.time() - start_time
        
        # 性能要求：500个孔位应该在0.5秒内加载完成
        self.assertLess(load_time, 0.5)
        
        # 测试批量更新性能
        start_time = time.time()
        
        holes_to_update = list(large_collection.holes.values())[:100]
        for hole in holes_to_update:
            hole.status = HoleStatus.QUALIFIED
            self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.QUALIFIED)
        
        update_time = time.time() - start_time
        
        # 性能要求：100个孔位更新应该在0.2秒内完成
        self.assertLess(update_time, 0.2)
    
    def _create_large_test_collection(self, hole_count):
        """创建大数据集测试集合"""
        holes = {}
        
        import math
        for i in range(hole_count):
            # 在圆形区域内均匀分布
            angle = (i / hole_count) * 2 * math.pi
            radius = 30 + (i % 20) * 2  # 变化半径创建多层分布
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            hole_id = f"H{i+1:05d}"
            
            hole = Mock(spec=HoleData)
            hole.hole_id = hole_id
            hole.center_x = x
            hole.center_y = y
            hole.radius = 2.0
            hole.status = HoleStatus.PENDING
            
            holes[hole_id] = hole
        
        collection = Mock(spec=HoleCollection)
        collection.holes = holes
        collection.get_bounds.return_value = (-80, -80, 80, 80)
        collection.__iter__ = lambda self: iter(holes.values())
        collection.__len__ = lambda self: len(holes)
        
        return collection
    
    def test_error_recovery(self):
        """测试错误恢复能力"""
        # 初始化系统
        self.sector_manager.load_hole_collection(self.dxf_collection)
        
        # 测试1: 无效数据处理
        try:
            self.sector_manager.update_hole_status("NONEXISTENT", HoleStatus.QUALIFIED)
            # 不应该抛出异常
        except Exception as e:
            self.fail(f"处理无效孔位ID时抛出异常: {e}")
        
        # 测试2: 重复加载数据
        try:
            self.sector_manager.load_hole_collection(self.dxf_collection)
            self.sector_manager.load_hole_collection(self.dxf_collection)
            # 不应该抛出异常
        except Exception as e:
            self.fail(f"重复加载数据时抛出异常: {e}")
        
        # 测试3: UI组件错误恢复
        try:
            # 模拟无效扇形选择
            self.detail_view.show_sector_detail(None)
        except Exception as e:
            self.fail(f"处理无效扇形选择时抛出异常: {e}")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建并加载多个大数据集
        for i in range(5):
            large_collection = self._create_large_test_collection(200)
            self.sector_manager.load_hole_collection(large_collection)
            
            # 模拟一些更新操作
            holes = list(large_collection.holes.values())[:50]
            for hole in holes:
                hole.status = HoleStatus.QUALIFIED
                self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.QUALIFIED)
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # 内存使用不应该超过100MB
        self.assertLess(memory_increase, 100)


if __name__ == '__main__':
    unittest.main()