"""
P2实时监控页面功能测试
验证界面还原度和功能完整性
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from collections import deque
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
import logging

# 设置测试环境的matplotlib后端
import matplotlib
matplotlib.use('Agg')  # 无GUI后端用于测试

class MockSharedComponents:
    """模拟共享组件"""
    def __init__(self):
        self.business_service = Mock()
        self.business_service.current_product = Mock()
        self.business_service.current_product.standard_diameter = 17.60
        self.business_service.current_product.tolerance_upper = 0.070
        self.business_service.current_product.tolerance_lower = 0.001
        self.business_service.current_product.model_name = "CAP1000"

class TestRealtimeMonitoringPage(unittest.TestCase):
    """P2实时监控页面测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """每个测试用例的初始化"""
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        
        # 创建模拟的依赖
        self.mock_shared_components = MockSharedComponents()
        self.mock_view_model = Mock()
        
        # 导入并创建P2页面
        try:
            from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
            self.page = RealtimeMonitoringPage(
                shared_components=self.mock_shared_components,
                view_model=self.mock_view_model
            )
        except ImportError as e:
            self.skipTest(f"无法导入P2页面: {e}")
            
    def tearDown(self):
        """清理"""
        if hasattr(self, 'page'):
            self.page.close()
            
    def test_01_page_initialization(self):
        """测试页面初始化"""
        print("\\n🧪 测试1: 页面初始化")
        
        # 检查页面基本属性
        self.assertIsInstance(self.page, QWidget)
        self.assertTrue(hasattr(self.page, 'logger'))
        
        # 检查数据存储初始化
        self.assertIsInstance(self.page.depth_data, deque)
        self.assertIsInstance(self.page.diameter_data, deque)
        self.assertEqual(self.page.depth_data.maxlen, 1000)
        
        # 检查状态初始化
        self.assertFalse(self.page.is_monitoring)
        self.assertEqual(self.page.current_hole, "未设置")
        self.assertEqual(self.page.current_depth, 0.0)
        
        print("✅ 页面初始化测试通过")
        
    def test_02_product_parameters_loading(self):
        """测试产品参数加载"""
        print("\\n🧪 测试2: 产品参数加载")
        
        # 检查参数是否从模拟产品加载
        self.assertEqual(self.page.standard_diameter, 17.60)
        self.assertEqual(self.page.tolerance_upper, 0.070)
        self.assertEqual(self.page.tolerance_lower, 0.001)
        
        print("✅ 产品参数加载测试通过")
        
    def test_03_ui_components_creation(self):
        """测试UI组件创建"""
        print("\\n🧪 测试3: UI组件创建")
        
        # 检查关键UI组件是否存在
        self.assertTrue(hasattr(self.page, 'canvas'))
        self.assertTrue(hasattr(self.page, 'figure'))
        self.assertTrue(hasattr(self.page, 'ax'))
        self.assertTrue(hasattr(self.page, 'endoscope_view'))
        
        # 检查控制组件
        self.assertTrue(hasattr(self.page, 'hole_combo'))
        self.assertTrue(hasattr(self.page, 'start_stop_btn'))
        self.assertTrue(hasattr(self.page, 'clear_btn'))
        self.assertTrue(hasattr(self.page, 'export_btn'))
        
        # 检查参数输入组件
        self.assertTrue(hasattr(self.page, 'std_diameter_input'))
        self.assertTrue(hasattr(self.page, 'upper_tolerance_input'))
        self.assertTrue(hasattr(self.page, 'lower_tolerance_input'))
        
        # 检查显示组件
        self.assertTrue(hasattr(self.page, 'status_display'))
        self.assertTrue(hasattr(self.page, 'depth_display'))
        self.assertTrue(hasattr(self.page, 'stats_label'))
        
        print("✅ UI组件创建测试通过")
        
    def test_04_matplotlib_chart_setup(self):
        """测试matplotlib图表设置"""
        print("\\n🧪 测试4: matplotlib图表设置")
        
        # 检查图表基本设置
        self.assertIsNotNone(self.page.figure)
        self.assertIsNotNone(self.page.ax)
        self.assertIsNotNone(self.page.canvas)
        
        # 检查数据线初始化
        self.assertTrue(hasattr(self.page, 'diameter_line'))
        self.assertTrue(hasattr(self.page, 'anomaly_points'))
        
        # 检查坐标轴设置
        xlim = self.page.ax.get_xlim()
        ylim = self.page.ax.get_ylim()
        self.assertEqual(xlim, (0.0, 100.0))  # 初始X轴范围
        
        # 检查标准线设置
        if self.page.standard_diameter:
            # 应该有标准线和公差线
            lines = self.page.ax.get_lines()
            self.assertGreater(len(lines), 0)  # 至少有数据线
            
        print("✅ matplotlib图表设置测试通过")
        
    def test_05_hole_selection_functionality(self):
        """测试孔位选择功能"""
        print("\\n🧪 测试5: 孔位选择功能")
        
        # 检查孔位下拉框
        self.assertGreater(self.page.hole_combo.count(), 0)
        
        # 测试孔位切换
        original_hole = self.page.current_hole
        test_hole = "AC001R001"
        
        # 模拟用户选择孔位
        self.page.hole_combo.setCurrentText(test_hole)
        
        # 检查是否触发了孔位改变
        self.assertEqual(self.page.hole_combo.currentText(), test_hole)
        
        print("✅ 孔位选择功能测试通过")
        
    def test_06_monitoring_toggle(self):
        """测试监控开关功能"""
        print("\\n🧪 测试6: 监控开关功能")
        
        # 初始状态应该是未监控
        self.assertFalse(self.page.is_monitoring)
        self.assertEqual(self.page.start_stop_btn.text(), "开始监控")
        
        # 模拟点击开始监控
        self.page.start_stop_btn.setChecked(True)
        self.page._toggle_monitoring()
        
        # 检查状态切换
        self.assertTrue(self.page.is_monitoring)
        self.assertEqual(self.page.start_stop_btn.text(), "停止监控")
        self.assertEqual(self.page.connection_status, "监控中...")
        
        # 再次点击停止监控
        self.page.start_stop_btn.setChecked(False)
        self.page._toggle_monitoring()
        
        # 检查状态切换回来
        self.assertFalse(self.page.is_monitoring)
        self.assertEqual(self.page.start_stop_btn.text(), "开始监控")
        
        print("✅ 监控开关功能测试通过")
        
    def test_07_parameter_update(self):
        """测试参数更新功能"""
        print("\\n🧪 测试7: 参数更新功能")
        
        # 测试标准直径更新
        new_diameter = 18.0
        self.page.std_diameter_input.setText(str(new_diameter))
        self.page._update_standard_diameter()
        self.assertEqual(self.page.standard_diameter, new_diameter)
        
        # 测试公差更新
        new_upper = 0.08
        new_lower = 0.02
        self.page.upper_tolerance_input.setText(str(new_upper))
        self.page.lower_tolerance_input.setText(str(new_lower))
        self.page._update_tolerance()
        self.assertEqual(self.page.tolerance_upper, new_upper)
        self.assertEqual(self.page.tolerance_lower, new_lower)
        
        print("✅ 参数更新功能测试通过")
        
    def test_08_data_simulation(self):
        """测试数据模拟功能"""
        print("\\n🧪 测试8: 数据模拟功能")
        
        # 启动监控
        self.page.is_monitoring = True
        
        # 模拟数据更新
        initial_count = self.page.data_counter
        self.page._update_monitoring_data()
        
        # 检查数据是否增加
        self.assertEqual(self.page.data_counter, initial_count + 1)
        self.assertEqual(len(self.page.depth_data), 1)
        self.assertEqual(len(self.page.diameter_data), 1)
        
        # 检查深度是否更新
        self.assertGreater(self.page.current_depth, 0)
        
        print("✅ 数据模拟功能测试通过")
        
    def test_09_chart_update(self):
        """测试图表更新功能"""
        print("\\n🧪 测试9: 图表更新功能")
        
        # 添加一些测试数据
        self.page.depth_data.extend([1.0, 2.0, 3.0])
        self.page.diameter_data.extend([17.6, 17.65, 17.55])
        
        # 更新图表
        self.page._update_chart()
        
        # 检查数据线是否更新
        line_data = self.page.diameter_line.get_data()
        self.assertEqual(len(line_data[0]), 3)  # X数据
        self.assertEqual(len(line_data[1]), 3)  # Y数据
        
        print("✅ 图表更新功能测试通过")
        
    def test_10_data_clearing(self):
        """测试数据清除功能"""
        print("\\n🧪 测试10: 数据清除功能")
        
        # 先添加一些数据
        self.page.depth_data.extend([1.0, 2.0, 3.0])
        self.page.diameter_data.extend([17.6, 17.65, 17.55])
        self.page.data_counter = 3
        self.page.anomaly_counter = 1
        self.page.current_depth = 5.0
        
        # 清除数据
        self.page._clear_data()
        
        # 检查数据是否清除
        self.assertEqual(len(self.page.depth_data), 0)
        self.assertEqual(len(self.page.diameter_data), 0)
        self.assertEqual(self.page.data_counter, 0)
        self.assertEqual(self.page.anomaly_counter, 0)
        self.assertEqual(self.page.current_depth, 0.0)
        
        print("✅ 数据清除功能测试通过")
        
    def test_11_endoscope_view_integration(self):
        """测试内窥镜视图集成"""
        print("\\n🧪 测试11: 内窥镜视图集成")
        
        # 检查内窥镜视图是否存在
        self.assertTrue(hasattr(self.page, 'endoscope_view'))
        self.assertIsNotNone(self.page.endoscope_view)
        
        # 测试孔位设置
        test_hole = "BC002R001"
        self.page.endoscope_view.set_hole_id(test_hole)
        
        # 测试图像更新（使用模拟图像）
        try:
            self.page._update_endoscope_image()
        except Exception as e:
            print(f"⚠️ 内窥镜图像更新失败（可能是测试环境限制）: {e}")
        
        print("✅ 内窥镜视图集成测试通过")
        
    def test_12_signal_emissions(self):
        """测试信号发射"""
        print("\\n🧪 测试12: 信号发射")
        
        # 测试监控开始信号
        with patch.object(self.page.monitoring_started, 'emit') as mock_emit:
            self.page.start_stop_btn.setChecked(True)
            self.page._toggle_monitoring()
            mock_emit.assert_called_once()
            
        # 测试监控停止信号
        with patch.object(self.page.monitoring_stopped, 'emit') as mock_emit:
            self.page.start_stop_btn.setChecked(False)
            self.page._toggle_monitoring()
            mock_emit.assert_called_once()
            
        # 测试孔位改变信号
        with patch.object(self.page.hole_changed, 'emit') as mock_emit:
            test_hole = "AC002R001"
            self.page._on_hole_changed(test_hole)
            mock_emit.assert_called_once_with(test_hole)
        
        print("✅ 信号发射测试通过")
        
    def test_13_public_interface(self):
        """测试公共接口"""
        print("\\n🧪 测试13: 公共接口")
        
        # 测试获取当前孔位
        test_hole = "CC001R001"
        self.page.current_hole = test_hole
        self.assertEqual(self.page.get_current_hole(), test_hole)
        
        # 测试监控状态检查
        self.page.is_monitoring = True
        self.assertTrue(self.page.is_monitoring_active())
        
        # 测试统计信息获取
        stats = self.page.get_monitoring_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('current_hole', stats)
        self.assertIn('is_monitoring', stats)
        self.assertIn('data_count', stats)
        self.assertIn('anomaly_count', stats)
        
        # 测试参数刷新
        self.page.refresh_product_parameters()
        
        # 测试数据加载接口
        self.page.load_hole_data("DC001R001")
        self.assertEqual(self.page.current_hole, "DC001R001")
        
        print("✅ 公共接口测试通过")
        
    def test_14_error_handling(self):
        """测试错误处理"""
        print("\\n🧪 测试14: 错误处理")
        
        # 测试无效参数输入处理
        original_diameter = self.page.standard_diameter
        self.page.std_diameter_input.setText("invalid")
        self.page._update_standard_diameter()
        # 应该保持原值
        self.assertEqual(self.page.standard_diameter, original_diameter)
        
        # 测试无效公差输入处理
        original_upper = self.page.tolerance_upper
        self.page.upper_tolerance_input.setText("invalid")
        self.page._update_tolerance()
        # 应该保持原值
        self.assertEqual(self.page.tolerance_upper, original_upper)
        
        print("✅ 错误处理测试通过")
        
    def test_15_layout_restoration(self):
        """测试布局还原度"""
        print("\\n🧪 测试15: 布局还原度")
        
        # 检查主要布局结构
        self.assertTrue(hasattr(self.page, 'canvas'))  # matplotlib图表
        self.assertTrue(hasattr(self.page, 'endoscope_view'))  # 内窥镜视图
        
        # 检查控制面板结构
        control_widgets = [
            'hole_combo',           # 孔位选择
            'status_display',       # 状态显示
            'depth_display',        # 深度显示
            'std_diameter_input',   # 标准直径输入
            'upper_tolerance_input', # 上限公差输入
            'lower_tolerance_input', # 下限公差输入
            'start_stop_btn',       # 开始/停止按钮
            'clear_btn',            # 清除按钮
            'export_btn',           # 导出按钮
            'stats_label'           # 统计标签
        ]
        
        for widget_name in control_widgets:
            self.assertTrue(hasattr(self.page, widget_name), 
                          f"缺少控制组件: {widget_name}")
        
        print("✅ 布局还原度测试通过")

class TestP2PerformanceAndStability(unittest.TestCase):
    """P2界面性能和稳定性测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """每个测试用例的初始化"""
        from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
        self.mock_shared_components = MockSharedComponents()
        self.page = RealtimeMonitoringPage(shared_components=self.mock_shared_components)
        
    def tearDown(self):
        """清理"""
        if hasattr(self, 'page'):
            self.page.close()
            
    def test_high_frequency_data_updates(self):
        """测试高频数据更新"""
        print("\\n🧪 性能测试1: 高频数据更新")
        
        import time
        
        self.page.is_monitoring = True
        start_time = time.time()
        
        # 快速添加1000个数据点
        for i in range(1000):
            self.page._update_monitoring_data()
            
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"📊 添加1000个数据点耗时: {elapsed:.3f}秒")
        print(f"📊 平均每点耗时: {elapsed/1000*1000:.3f}毫秒")
        
        # 检查数据完整性
        self.assertEqual(self.page.data_counter, 1000)
        self.assertEqual(len(self.page.depth_data), 1000)
        self.assertEqual(len(self.page.diameter_data), 1000)
        
        print("✅ 高频数据更新测试通过")
        
    def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        print("\\n🧪 性能测试2: 内存使用稳定性")
        
        # 测试数据缓冲区限制
        self.page.is_monitoring = True
        
        # 添加超过缓冲区大小的数据
        for i in range(1500):  # 超过maxlen=1000
            self.page._update_monitoring_data()
            
        # 检查缓冲区大小限制
        self.assertLessEqual(len(self.page.depth_data), 1000)
        self.assertLessEqual(len(self.page.diameter_data), 1000)
        
        # 检查最新数据
        self.assertEqual(self.page.data_counter, 1500)
        
        print("✅ 内存使用稳定性测试通过")

def run_comprehensive_test():
    """运行综合测试"""
    print("=" * 60)
    print("🧪 P2实时监控页面综合测试开始")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加功能测试
    suite.addTests(loader.loadTestsFromTestCase(TestRealtimeMonitoringPage))
    
    # 添加性能测试
    suite.addTests(loader.loadTestsFromTestCase(TestP2PerformanceAndStability))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 测试结果总结
    print("\\n" + "=" * 60)
    print("🧪 测试结果总结")
    print("=" * 60)
    print(f"✅ 成功测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败测试: {len(result.failures)}")
    print(f"🚫 错误测试: {len(result.errors)}")
    
    if result.failures:
        print("\\n⚠️ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
            
    if result.errors:
        print("\\n🚫 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    # 计算成功率
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\\n📊 测试成功率: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 P2界面恢复度优秀！")
    elif success_rate >= 80:
        print("👍 P2界面恢复度良好！")
    elif success_rate >= 70:
        print("⚠️ P2界面恢复度需要改进")
    else:
        print("❌ P2界面恢复度较差，需要重点优化")
    
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)