#!/usr/bin/env python3
"""
模拟检测功能单元测试
不需要GUI交互的自动化测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.pages.main_detection_p1.components.simulation_controller import SimulationController


class TestSimulationFixes(unittest.TestCase):
    """模拟检测修复的单元测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = QApplication.instance() or QApplication([])
    
    def setUp(self):
        """每个测试前的准备"""
        self.main_view = NativeMainDetectionView()
        
        # 创建测试数据
        self.test_holes = {}
        for i in range(10):
            hole = HoleData(
                center_x=100 + (i % 5) * 50.0,
                center_y=100 + (i // 5) * 50.0,
                radius=15.0,
                hole_id=f"TEST_{i:03d}",
                status=HoleStatus.PENDING
            )
            self.test_holes[hole.hole_id] = hole
        
        self.test_collection = HoleCollection(self.test_holes)
    
    def test_sector_stats_table_exists(self):
        """测试1: 扇形统计表格是否存在"""
        # 检查左侧面板是否有扇形统计表格
        self.assertTrue(hasattr(self.main_view.left_panel, 'sector_stats_table'),
                       "左侧面板应该有sector_stats_table属性")
        
        # 检查表格结构
        table = self.main_view.left_panel.sector_stats_table
        self.assertEqual(table.rowCount(), 6, "表格应该有6行")
        self.assertEqual(table.columnCount(), 2, "表格应该有2列")
        
        # 检查表头
        headers = [table.horizontalHeaderItem(i).text() for i in range(2)]
        self.assertEqual(headers, ["状态", "数量"], "表头应该是['状态', '数量']")
        
        print("✅ 测试1通过: 扇形统计表格正确创建")
    
    def test_simulation_controller_integration(self):
        """测试2: 模拟控制器集成"""
        # 检查模拟控制器是否存在
        self.assertTrue(hasattr(self.main_view, 'simulation_controller'),
                       "主视图应该有simulation_controller属性")
        self.assertIsNotNone(self.main_view.simulation_controller,
                           "simulation_controller应该被初始化")
        
        # 检查信号处理方法
        required_methods = [
            '_on_simulation_progress',
            '_on_hole_status_updated',
            '_on_simulation_completed',
            '_on_start_simulation',
            '_on_pause_simulation',
            '_on_stop_simulation'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.main_view, method),
                          f"主视图应该有{method}方法")
        
        print("✅ 测试2通过: 模拟控制器正确集成")
    
    def test_progress_signal_connections(self):
        """测试3: 进度信号连接"""
        # 检查左侧面板的进度更新方法
        self.assertTrue(hasattr(self.main_view.left_panel, 'update_progress_display'),
                       "左侧面板应该有update_progress_display方法")
        
        # 测试进度更新
        test_data = {
            'progress': 75,
            'completed': 15,
            'total': 20,
            'pending': 5,
            'qualified': 14,
            'unqualified': 1
        }
        
        # 调用方法不应该抛出异常
        try:
            self.main_view.left_panel.update_progress_display(test_data)
            print("✅ 测试3通过: 进度更新功能正常")
        except Exception as e:
            self.fail(f"进度更新失败: {e}")
    
    def test_color_update_mechanism(self):
        """测试4: 颜色更新机制"""
        # 创建独立的模拟控制器进行测试
        controller = SimulationController()
        controller.load_hole_collection(self.test_collection)
        
        # 检查_update_hole_status方法的color_override参数
        # 模拟蓝色状态
        from PySide6.QtGui import QColor
        blue_color = QColor(33, 150, 243)
        
        # 这个测试主要验证方法签名正确
        try:
            # 测试带颜色覆盖的更新
            controller._update_hole_status("TEST_001", HoleStatus.PENDING, color_override=blue_color)
            # 测试清除颜色覆盖
            controller._update_hole_status("TEST_001", HoleStatus.QUALIFIED, color_override=None)
            print("✅ 测试4通过: 颜色更新机制正常")
        except Exception as e:
            self.fail(f"颜色更新机制测试失败: {e}")
    
    def test_sector_stats_update(self):
        """测试5: 扇形统计更新功能"""
        # 加载数据
        self.main_view.load_hole_collection(self.test_collection)
        
        # 测试扇形统计更新
        test_stats = {
            'total': 10,
            'qualified': 6,
            'defective': 2,
            'pending': 2,
            'blind': 1,
            'tie_rod': 1
        }
        
        # 检查更新方法
        self.assertTrue(hasattr(self.main_view.left_panel, 'update_sector_stats'),
                       "左侧面板应该有update_sector_stats方法")
        
        try:
            self.main_view.left_panel.update_sector_stats(test_stats)
            
            # 验证表格内容
            table = self.main_view.left_panel.sector_stats_table
            # 检查总计行
            total_item = table.item(5, 1)  # 总计在第6行
            self.assertEqual(total_item.text(), "10", "总计应该是10")
            
            print("✅ 测试5通过: 扇形统计更新功能正常")
        except Exception as e:
            self.fail(f"扇形统计更新失败: {e}")
    
    def test_simulation_workflow(self):
        """测试6: 完整的模拟工作流程"""
        # 加载数据
        self.main_view.load_hole_collection(self.test_collection)
        
        # 检查是否可以启动模拟
        if self.main_view.simulation_controller:
            try:
                # 测试启动模拟
                self.main_view._on_start_simulation()
                
                # 使用事件循环等待一小段时间
                loop = QEventLoop()
                QTimer.singleShot(100, loop.quit)
                loop.exec()
                
                # 检查模拟是否在运行
                self.assertTrue(self.main_view.simulation_controller.is_running,
                              "模拟应该在运行中")
                
                # 停止模拟
                self.main_view._on_stop_simulation()
                
                print("✅ 测试6通过: 模拟工作流程正常")
            except Exception as e:
                self.fail(f"模拟工作流程测试失败: {e}")
        else:
            self.skipTest("模拟控制器未初始化")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSimulationFixes)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过！")
        return True
    else:
        print("\n❌ 有测试失败")
        return False


if __name__ == "__main__":
    print("="*60)
    print("模拟检测修复单元测试")
    print("="*60)
    
    success = run_tests()
    sys.exit(0 if success else 1)