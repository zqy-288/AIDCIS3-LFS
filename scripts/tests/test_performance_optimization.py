#!/usr/bin/env python3
"""
性能测试 - 优化效果验证
测试各项优化的性能影响
"""

import sys
import time
import unittest
import gc
from pathlib import Path
from memory_profiler import profile
import psutil
import os

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.hole_item import HoleGraphicsItem
from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.graphics.sector_view import SectorOverviewWidget
from aidcis2.graphics.dynamic_sector_view import SectorGraphicsManager


class TestMemoryOptimization(unittest.TestCase):
    """测试内存优化"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.process = psutil.Process(os.getpid())
        gc.collect()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def tearDown(self):
        """每个测试后的清理"""
        gc.collect()
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - self.initial_memory
        print(f"\n内存增长: {memory_increase:.2f} MB")
    
    def test_hole_item_without_tooltip(self):
        """测试无工具提示的孔位项内存使用"""
        holes_count = 1000
        items = []
        
        # 创建大量孔位项
        for i in range(holes_count):
            hole = HoleData(
                hole_id=f"H{i+1:05d}",
                center_x=i % 100 * 10,
                center_y=i // 100 * 10,
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
            
            item = HoleGraphicsItem(hole)
            items.append(item)
        
        # 验证没有设置工具提示
        for item in items[:10]:  # 抽样检查
            self.assertEqual(item.toolTip(), "")
        
        # 内存应该相对较低
        gc.collect()
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_per_item = (current_memory - self.initial_memory) / holes_count
        
        print(f"每个孔位项平均内存: {memory_per_item:.4f} MB")
        self.assertLess(memory_per_item, 0.1)  # 每个项应该小于0.1MB
    
    def test_sector_view_memory(self):
        """测试扇形视图内存使用"""
        # 创建多个扇形视图实例
        widgets = []
        for i in range(10):
            widget = SectorOverviewWidget()
            widgets.append(widget)
        
        gc.collect()
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - self.initial_memory
        
        print(f"10个扇形视图总内存: {memory_increase:.2f} MB")
        self.assertLess(memory_increase, 50)  # 应该小于50MB


class TestRenderingPerformance(unittest.TestCase):
    """测试渲染性能"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_large_hole_collection_rendering(self):
        """测试大量孔位的渲染性能"""
        # 创建大量孔位
        holes = {}
        hole_count = 5000
        
        start_time = time.time()
        
        for i in range(hole_count):
            hole_id = f"H{i+1:05d}"
            holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=(i % 100 - 50) * 20,
                center_y=(i // 100 - 25) * 20,
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
        
        collection = HoleCollection(holes=holes)
        creation_time = time.time() - start_time
        
        print(f"\n创建 {hole_count} 个孔位耗时: {creation_time:.3f} 秒")
        
        # 加载到视图
        view = OptimizedGraphicsView()
        
        start_time = time.time()
        view.load_holes(collection)
        load_time = time.time() - start_time
        
        print(f"加载到视图耗时: {load_time:.3f} 秒")
        
        # 性能基准
        self.assertLess(creation_time, 1.0)  # 创建应该在1秒内
        self.assertLess(load_time, 5.0)      # 加载应该在5秒内
    
    def test_sector_assignment_performance(self):
        """测试扇形分配性能"""
        # 创建均匀分布的孔位
        holes = {}
        hole_count = 10000
        
        import math
        for i in range(hole_count):
            angle = (i / hole_count) * 2 * math.pi
            radius = 100 + (i % 10) * 10
            
            holes[f"H{i+1:05d}"] = HoleData(
                hole_id=f"H{i+1:05d}",
                center_x=radius * math.cos(angle),
                center_y=radius * math.sin(angle),
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
        
        collection = HoleCollection(holes=holes)
        
        # 测试扇形管理器创建
        start_time = time.time()
        manager = SectorGraphicsManager(collection)
        creation_time = time.time() - start_time
        
        print(f"\n扇形管理器创建耗时: {creation_time:.3f} 秒")
        
        # 验证扇形分配
        total_assigned = 0
        for sector in manager.sector_collections.values():
            total_assigned += len(sector)
        
        self.assertEqual(total_assigned, hole_count)
        self.assertLess(creation_time, 2.0)  # 应该在2秒内完成


class TestUIResponsiveness(unittest.TestCase):
    """测试UI响应性"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_rapid_sector_switching(self):
        """测试快速切换扇形"""
        from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
        from aidcis2.graphics.sector_manager import SectorQuadrant
        
        # 创建测试数据
        holes = {}
        for i in range(100):
            holes[f"H{i+1:03d}"] = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=(i % 10 - 5) * 20,
                center_y=(i // 10 - 5) * 20,
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
        
        collection = HoleCollection(holes=holes)
        
        # 创建显示组件
        widget = DynamicSectorDisplayWidget()
        widget.set_hole_collection(collection)
        
        # 快速切换扇形
        switch_count = 100
        start_time = time.time()
        
        for i in range(switch_count):
            sector = list(SectorQuadrant)[i % 4]
            widget.switch_to_sector(sector)
        
        switch_time = time.time() - start_time
        avg_switch_time = switch_time / switch_count * 1000  # 毫秒
        
        print(f"\n平均切换时间: {avg_switch_time:.2f} ms")
        self.assertLess(avg_switch_time, 50)  # 平均切换应该在50ms内
    
    def test_simulation_update_performance(self):
        """测试模拟更新性能"""
        from main_window.main_window import MainWindow
        
        window = MainWindow()
        
        # 创建测试数据
        holes = {}
        for i in range(100):
            holes[f"H{i+1:03d}"] = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=i * 10,
                center_y=0,
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
        
        window.hole_collection = HoleCollection(holes=holes)
        window.graphics_view.load_holes(window.hole_collection)
        
        # 准备模拟
        window._start_simulation_progress_v2()
        
        # 测量更新时间
        update_times = []
        
        for i in range(10):  # 测试10次更新
            if window.simulation_index_v2 < len(window.holes_list_v2):
                # 创建模拟图形项
                hole = window.holes_list_v2[window.simulation_index_v2]
                from unittest.mock import Mock
                mock_item = Mock()
                window.graphics_view.hole_items[hole.hole_id] = mock_item
                
                start_time = time.time()
                window._update_simulation_v2()
                update_time = time.time() - start_time
                update_times.append(update_time)
        
        # 停止模拟
        if hasattr(window, 'simulation_timer_v2'):
            window.simulation_timer_v2.stop()
        
        window.close()
        
        if update_times:
            avg_update_time = sum(update_times) / len(update_times) * 1000
            print(f"\n平均更新时间: {avg_update_time:.2f} ms")
            self.assertLess(avg_update_time, 100)  # 平均更新应该在100ms内


class TestOptimizationBenchmark(unittest.TestCase):
    """优化效果基准测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_sector_size_impact(self):
        """测试扇形大小对性能的影响"""
        from aidcis2.graphics.sector_view import SectorGraphicsItem
        
        # 测试不同半径的性能
        radii = [10, 15, 20, 25, 30, 40, 50]
        render_times = []
        
        for radius in radii:
            items = []
            start_time = time.time()
            
            # 创建4个扇形
            for i in range(4):
                item = SectorGraphicsItem(
                    list(SectorQuadrant)[i],
                    QPointF(0, 0),
                    radius
                )
                items.append(item)
            
            render_time = time.time() - start_time
            render_times.append(render_time)
            
            print(f"半径 {radius}px: {render_time*1000:.2f} ms")
        
        # 验证较小半径的性能更好
        self.assertLess(render_times[0], render_times[-1])
    
    def test_font_size_impact(self):
        """测试字体大小对渲染的影响"""
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtWidgets import QGraphicsScene
        
        scene = QGraphicsScene()
        font_sizes = [3, 4, 5, 6, 7, 8, 10, 12]
        
        for size in font_sizes:
            start_time = time.time()
            
            # 创建100个文本项
            for i in range(100):
                text = QGraphicsTextItem(f"区域{i%4+1}\n{i}%")
                text.setFont(QFont("Arial", size, QFont.Bold))
                text.setPos(i * 20, 0)
                scene.addItem(text)
            
            render_time = time.time() - start_time
            print(f"字体 {size}pt: {render_time*1000:.2f} ms")
            
            # 清理场景
            scene.clear()
        
        # 较小字体应该渲染更快
        # 这里不做严格断言，因为字体渲染受系统影响较大


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)