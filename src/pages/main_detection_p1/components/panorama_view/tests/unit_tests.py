"""
全景图组件单元测试
演示如何对拆分后的组件进行单元测试
"""

import unittest
from unittest.mock import Mock, MagicMock
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsScene

from .data_model import PanoramaDataModel
from .geometry_calculator import PanoramaGeometryCalculator
from .status_manager import PanoramaStatusManager
from ..core.event_bus import PanoramaEventBus, PanoramaEvent
from src.shared.models.hole_data import HoleData, HoleStatus, HoleCollection


class TestPanoramaDataModel(unittest.TestCase):
    """测试数据模型"""
    
    def setUp(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.data_model = PanoramaDataModel()
    
    def test_load_hole_collection(self):
        """测试加载孔位集合"""
        # 创建测试数据
        holes = {
            "H001": HoleData("H001", 100, 100, HoleStatus.PENDING),
            "H002": HoleData("H002", 200, 200, HoleStatus.PENDING)
        }
        
        hole_collection = HoleCollection()
        hole_collection.holes = holes
        
        # 监听信号
        signal_received = False
        def on_data_loaded():
            nonlocal signal_received
            signal_received = True
        
        self.data_model.data_loaded.connect(on_data_loaded)
        
        # 加载数据
        self.data_model.load_hole_collection(hole_collection)
        
        # 验证
        self.assertTrue(signal_received)
        self.assertEqual(len(self.data_model.get_holes()), 2)
        self.assertIn("H001", self.data_model.get_holes())
    
    def test_update_hole_status(self):
        """测试更新孔位状态"""
        # 先加载数据
        holes = {"H001": HoleData("H001", 100, 100, HoleStatus.PENDING)}
        hole_collection = HoleCollection()
        hole_collection.holes = holes
        self.data_model.load_hole_collection(hole_collection)
        
        # 监听状态变更信号
        status_changed = False
        def on_status_changed(hole_id, status):
            nonlocal status_changed
            status_changed = True
            self.assertEqual(hole_id, "H001")
            self.assertEqual(status, HoleStatus.COMPLETED)
        
        self.data_model.hole_status_changed.connect(on_status_changed)
        
        # 更新状态
        result = self.data_model.update_hole_status("H001", HoleStatus.COMPLETED)
        
        # 验证
        self.assertTrue(result)
        self.assertTrue(status_changed)
        self.assertEqual(self.data_model.get_hole("H001").status, HoleStatus.COMPLETED)


class TestPanoramaGeometryCalculator(unittest.TestCase):
    """测试几何计算器"""
    
    def setUp(self):
        self.calculator = PanoramaGeometryCalculator()
    
    def test_calculate_center(self):
        """测试中心点计算"""
        holes = {
            "H001": HoleData("H001", 0, 0, HoleStatus.PENDING),
            "H002": HoleData("H002", 100, 100, HoleStatus.PENDING),
            "H003": HoleData("H003", 200, 0, HoleStatus.PENDING)
        }
        
        center = self.calculator.calculate_center(holes)
        
        # 验证中心点
        self.assertAlmostEqual(center.x(), 100.0, places=1)
        self.assertAlmostEqual(center.y(), 33.33, places=1)
    
    def test_calculate_radius(self):
        """测试半径计算"""
        holes = {
            "H001": HoleData("H001", 0, 0, HoleStatus.PENDING),
            "H002": HoleData("H002", 100, 0, HoleStatus.PENDING)
        }
        
        center = QPointF(50, 0)  # 中心点
        radius = self.calculator.calculate_radius(holes, center)
        
        # 验证半径（50 * 1.2 = 60）
        self.assertAlmostEqual(radius, 60.0, places=1)
    
    def test_calculate_hole_display_size(self):
        """测试孔位显示大小计算"""
        # 测试小数据集
        size = self.calculator.calculate_hole_display_size(30, 100, 0.001)
        self.assertEqual(size, self.calculator.max_hole_radius)
        
        # 测试大数据集
        size = self.calculator.calculate_hole_display_size(10000, 1000, 0.01)
        self.assertLess(size, self.calculator.max_hole_radius)
        self.assertGreaterEqual(size, self.calculator.min_hole_radius)
    
    def test_detect_data_scale(self):
        """测试数据规模检测"""
        self.assertEqual(self.calculator.detect_data_scale(50), "small")
        self.assertEqual(self.calculator.detect_data_scale(500), "medium")
        self.assertEqual(self.calculator.detect_data_scale(5000), "large")
        self.assertEqual(self.calculator.detect_data_scale(50000), "massive")


class TestPanoramaStatusManager(unittest.TestCase):
    """测试状态管理器"""
    
    def setUp(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.data_model = Mock()
        self.status_manager = PanoramaStatusManager(self.data_model)
    
    def test_queue_status_update(self):
        """测试队列状态更新"""
        # 队列更新
        self.status_manager.queue_status_update("H001", HoleStatus.COMPLETED)
        
        # 验证队列
        self.assertEqual(self.status_manager.get_pending_count(), 1)
        self.assertIn("H001", self.status_manager.pending_updates)
    
    def test_flush_updates(self):
        """测试刷新更新"""
        # 设置数据模型mock
        self.data_model.update_hole_status.return_value = True
        
        # 队列一些更新
        self.status_manager.queue_status_update("H001", HoleStatus.COMPLETED)
        self.status_manager.queue_status_update("H002", HoleStatus.FAILED)
        
        # 刷新更新
        count = self.status_manager.flush_updates()
        
        # 验证
        self.assertEqual(count, 2)
        self.assertEqual(self.status_manager.get_pending_count(), 0)
        self.assertEqual(self.data_model.update_hole_status.call_count, 2)


class TestPanoramaEventBus(unittest.TestCase):
    """测试事件总线"""
    
    def setUp(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.event_bus = PanoramaEventBus()
    
    def test_publish_subscribe(self):
        """测试发布订阅"""
        # 订阅事件
        received_events = []
        
        def callback(event_data):
            received_events.append(event_data)
        
        self.event_bus.subscribe(PanoramaEvent.DATA_LOADED, callback)
        
        # 发布事件
        self.event_bus.publish(PanoramaEvent.DATA_LOADED, "test_data")
        
        # 处理Qt事件循环
        self.app.processEvents()
        
        # 验证
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].event_type, PanoramaEvent.DATA_LOADED)
        self.assertEqual(received_events[0].data, "test_data")
    
    def test_unsubscribe(self):
        """测试取消订阅"""
        received_events = []
        
        def callback(event_data):
            received_events.append(event_data)
        
        # 订阅然后取消订阅
        self.event_bus.subscribe(PanoramaEvent.DATA_LOADED, callback)
        self.event_bus.unsubscribe(PanoramaEvent.DATA_LOADED, callback)
        
        # 发布事件
        self.event_bus.publish(PanoramaEvent.DATA_LOADED, "test_data")
        self.app.processEvents()
        
        # 验证没有收到事件
        self.assertEqual(len(received_events), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 创建组件
        event_bus = PanoramaEventBus()
        data_model = PanoramaDataModel()
        geometry_calculator = PanoramaGeometryCalculator()
        status_manager = PanoramaStatusManager(data_model)
        
        # 创建测试数据
        holes = {
            "H001": HoleData("H001", 100, 100, HoleStatus.PENDING),
            "H002": HoleData("H002", 200, 200, HoleStatus.IN_PROGRESS)
        }
        
        hole_collection = HoleCollection()
        hole_collection.holes = holes
        
        # 加载数据
        data_model.load_hole_collection(hole_collection)
        
        # 计算几何信息
        center = geometry_calculator.calculate_center(holes)
        radius = geometry_calculator.calculate_radius(holes, center)
        
        # 更新状态
        status_manager.queue_status_update("H001", HoleStatus.COMPLETED)
        updated_count = status_manager.flush_updates()
        
        # 验证结果
        self.assertEqual(len(data_model.get_holes()), 2)
        self.assertIsInstance(center, QPointF)
        self.assertGreater(radius, 0)
        self.assertEqual(updated_count, 1)
        self.assertEqual(data_model.get_hole("H001").status, HoleStatus.COMPLETED)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTest(unittest.makeSuite(TestPanoramaDataModel))
    suite.addTest(unittest.makeSuite(TestPanoramaGeometryCalculator))
    suite.addTest(unittest.makeSuite(TestPanoramaStatusManager))
    suite.addTest(unittest.makeSuite(TestPanoramaEventBus))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n测试结果:")
    print(f"运行: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")