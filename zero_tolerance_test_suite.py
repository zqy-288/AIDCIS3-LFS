#!/usr/bin/env python3
"""
零容忍测试套件 - 实时图表包
严格测试所有边界条件和潜在错误场景
"""
import sys
import os
import time
import json
import threading
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.modules.realtime_chart_package import RealtimeChart
import numpy as np


class ZeroToleranceTest:
    """零容忍测试基类"""
    
    def __init__(self, name):
        self.name = name
        self.passed = True
        self.errors = []
        self.warnings = []
        self.assertions = 0
        self.start_time = None
        self.end_time = None
        
    def assert_true(self, condition, message):
        """断言条件为真"""
        self.assertions += 1
        if not condition:
            self.passed = False
            self.errors.append(f"断言失败: {message}")
            raise AssertionError(message)
            
    def assert_equals(self, actual, expected, message):
        """断言相等"""
        self.assertions += 1
        if actual != expected:
            self.passed = False
            error_msg = f"{message}\n  期望: {expected}\n  实际: {actual}"
            self.errors.append(error_msg)
            raise AssertionError(error_msg)
            
    def assert_in_range(self, value, min_val, max_val, message):
        """断言在范围内"""
        self.assertions += 1
        if not (min_val <= value <= max_val):
            self.passed = False
            error_msg = f"{message}\n  值: {value} 不在范围 [{min_val}, {max_val}] 内"
            self.errors.append(error_msg)
            raise AssertionError(error_msg)
            
    def assert_no_exception(self, func, *args, **kwargs):
        """断言不抛出异常"""
        self.assertions += 1
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.passed = False
            error_msg = f"意外异常: {type(e).__name__}: {str(e)}"
            self.errors.append(error_msg)
            raise
            
    def run(self):
        """运行测试"""
        self.start_time = time.time()
        try:
            self.test()
            if not self.errors:
                self.passed = True
        except Exception as e:
            self.passed = False
            if str(e) not in str(self.errors):
                self.errors.append(f"未捕获异常: {type(e).__name__}: {str(e)}")
        finally:
            self.end_time = time.time()
            
    def test(self):
        """子类需要实现的测试方法"""
        raise NotImplementedError
        
    def get_report(self):
        """获取测试报告"""
        duration = (self.end_time - self.start_time) if self.end_time else 0
        return {
            'name': self.name,
            'passed': self.passed,
            'assertions': self.assertions,
            'duration': duration,
            'errors': self.errors,
            'warnings': self.warnings
        }


class TestComponentInitialization(ZeroToleranceTest):
    """测试组件初始化"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 测试正常初始化
        chart = self.assert_no_exception(RealtimeChart)
        
        # 验证所有必需组件
        required_components = [
            'chart_widget', 'data_manager', 'csv_processor',
            'anomaly_detector', 'endoscope_manager', 'process_controller'
        ]
        
        for comp in required_components:
            self.assert_true(
                hasattr(chart, comp),
                f"组件 {comp} 必须存在"
            )
            self.assert_true(
                getattr(chart, comp) is not None,
                f"组件 {comp} 不能为 None"
            )
            
        # 验证UI组件
        ui_elements = [
            'status_label', 'data_count_label', 'anomaly_count_label',
            'process_status_label', 'start_button', 'stop_button',
            'clear_button', 'export_button'
        ]
        
        for elem in ui_elements:
            self.assert_true(
                hasattr(chart, elem),
                f"UI元素 {elem} 必须存在"
            )
            
        # 测试多次初始化
        for i in range(5):
            chart2 = self.assert_no_exception(RealtimeChart)
            self.assert_true(
                chart2 is not chart,
                f"第 {i+1} 次初始化必须创建新实例"
            )


class TestDataManagerBoundaries(ZeroToleranceTest):
    """测试数据管理器边界条件"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        dm = chart.data_manager
        
        # 测试空数据
        depths, diameters = dm.get_display_data()
        self.assert_equals(len(depths), 0, "初始深度数据必须为空")
        self.assert_equals(len(diameters), 0, "初始直径数据必须为空")
        
        # 测试单个数据点
        dm.add_data_point(0, 17.6)
        self.assert_equals(dm.get_buffer_info()['buffer_size'], 1, "必须有1个数据点")
        
        # 测试负值
        dm.clear_data()
        dm.add_data_point(-100, -17.6)
        depths, diameters = dm.get_display_data()
        self.assert_equals(depths[0], -100, "必须接受负深度值")
        self.assert_equals(diameters[0], -17.6, "必须接受负直径值")
        
        # 测试极大值
        dm.clear_data()
        large_value = 1e6
        dm.add_data_point(large_value, large_value)
        depths, diameters = dm.get_display_data()
        self.assert_equals(depths[0], large_value, "必须处理大数值")
        
        # 测试数据长度不匹配
        try:
            dm.add_data_batch([1, 2, 3], [1, 2])
            self.assert_true(False, "长度不匹配应该抛出异常")
        except ValueError:
            pass  # 预期的异常
            
        # 测试大批量数据
        dm.clear_data()
        large_batch_size = 10000
        large_depths = list(range(large_batch_size))
        large_diameters = [17.6] * large_batch_size
        
        start_time = time.time()
        dm.add_data_batch(large_depths, large_diameters)
        batch_time = time.time() - start_time
        
        self.assert_in_range(
            batch_time, 0, 1.0,
            f"添加 {large_batch_size} 个数据点必须在1秒内完成"
        )
        
        # 测试缓冲区限制
        buffer_info = dm.get_buffer_info()
        self.assert_true(
            buffer_info['buffer_size'] <= buffer_info['buffer_capacity'],
            "缓冲区大小不能超过容量"
        )


class TestCSVProcessorEdgeCases(ZeroToleranceTest):
    """测试CSV处理器边界情况"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        csv_proc = chart.csv_processor
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试空CSV文件
            empty_csv = os.path.join(temp_dir, 'empty.csv')
            open(empty_csv, 'w').close()
            
            depths, diameters = csv_proc.read_csv_data(empty_csv)
            self.assert_equals(len(depths), 0, "空CSV文件应返回空数据")
            
            # 测试只有标题的CSV
            header_only_csv = os.path.join(temp_dir, 'header_only.csv')
            with open(header_only_csv, 'w') as f:
                f.write('深度,直径\n')
                
            depths, diameters = csv_proc.read_csv_data(header_only_csv)
            self.assert_equals(len(depths), 0, "只有标题的CSV应返回空数据")
            
            # 测试格式错误的CSV
            malformed_csv = os.path.join(temp_dir, 'malformed.csv')
            with open(malformed_csv, 'w') as f:
                f.write('深度,直径\n')
                f.write('10,17.6\n')
                f.write('20\n')  # 缺少列
                f.write('30,17.7\n')
                
            depths, diameters = csv_proc.read_csv_data(malformed_csv)
            # 应该能够处理格式错误
            
            # 测试特殊字符
            special_csv = os.path.join(temp_dir, 'special.csv')
            with open(special_csv, 'w', encoding='utf-8') as f:
                f.write('深度,直径\n')
                f.write('10,17.6\n')
                f.write('20,17.7\n')
                f.write('30,"17.8"\n')  # 带引号
                
            depths, diameters = csv_proc.read_csv_data(special_csv)
            self.assert_equals(len(depths), 3, "必须正确处理带引号的数据")
            
            # 测试不存在的文件
            nonexistent = os.path.join(temp_dir, 'nonexistent.csv')
            depths, diameters = csv_proc.read_csv_data(nonexistent)
            self.assert_equals(len(depths), 0, "不存在的文件应返回空数据")
            
            # 测试文件权限（仅在类Unix系统上）
            if os.name != 'nt':
                readonly_csv = os.path.join(temp_dir, 'readonly.csv')
                with open(readonly_csv, 'w') as f:
                    f.write('深度,直径\n10,17.6\n')
                os.chmod(readonly_csv, 0o444)  # 只读
                
                depths, diameters = csv_proc.read_csv_data(readonly_csv)
                self.assert_true(len(depths) > 0, "必须能读取只读文件")


class TestAnomalyDetectorAccuracy(ZeroToleranceTest):
    """测试异常检测器准确性"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        detector = chart.anomaly_detector
        
        # 测试公差检测
        detector.set_tolerance_parameters(17.6, 0.2)
        detector.set_detection_method('tolerance')
        
        # 边界值测试
        test_cases = [
            (17.6, False),      # 标准值
            (17.8, False),      # 上限边界
            (17.4, False),      # 下限边界
            (17.81, True),      # 刚超上限
            (17.39, True),      # 刚超下限
            (18.0, True),       # 明显超上限
            (17.0, True),       # 明显超下限
        ]
        
        for diameter, should_be_anomaly in test_cases:
            anomalies = detector.detect_anomalies([0], [diameter])
            is_anomaly = len(anomalies) > 0
            self.assert_equals(
                is_anomaly, should_be_anomaly,
                f"直径 {diameter} 异常检测结果错误"
            )
            
        # 测试统计检测
        detector.clear_anomalies()
        detector.set_detection_method('statistical')
        detector.set_statistical_parameters(window_size=5, sigma_multiplier=2.0)
        
        # 正常数据序列
        normal_data = [17.6] * 20
        anomalies = detector.detect_anomalies(list(range(20)), normal_data)
        self.assert_equals(len(anomalies), 0, "正常数据不应有异常")
        
        # 带离群值的数据
        data_with_outlier = normal_data.copy()
        data_with_outlier[10] = 18.5  # 明显的离群值
        
        detector.clear_anomalies()
        anomalies = detector.detect_anomalies(list(range(20)), data_with_outlier)
        self.assert_true(10 in anomalies, "必须检测到离群值")
        
        # 测试梯度检测
        detector.clear_anomalies()
        detector.set_detection_method('gradient')
        detector.set_gradient_threshold(0.3)
        
        # 平滑数据
        smooth_data = [17.6 + i * 0.01 for i in range(10)]
        anomalies = detector.detect_anomalies(list(range(10)), smooth_data)
        self.assert_equals(len(anomalies), 0, "平滑数据不应有梯度异常")
        
        # 突变数据
        jump_data = [17.6, 17.6, 17.6, 18.2, 17.6, 17.6]  # 突变
        detector.clear_anomalies()
        anomalies = detector.detect_anomalies(list(range(6)), jump_data)
        self.assert_true(len(anomalies) > 0, "必须检测到突变")


class TestChartWidgetInteraction(ZeroToleranceTest):
    """测试图表组件交互"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        widget = chart.chart_widget
        
        # 测试初始状态
        self.assert_equals(len(widget.depth_data), 0, "初始深度数据必须为空")
        self.assert_equals(len(widget.diameter_data), 0, "初始直径数据必须为空")
        
        # 测试数据更新
        test_depths = [0, 10, 20, 30, 40]
        test_diameters = [17.5, 17.6, 17.7, 17.6, 17.5]
        
        widget.update_data(test_depths, test_diameters)
        self.assert_equals(len(widget.depth_data), 5, "数据更新后长度错误")
        
        # 测试公差线
        widget.set_standard_diameter(17.6, 0.2)
        self.assert_true(widget.show_tolerance_lines, "公差线应该显示")
        self.assert_equals(widget.standard_diameter, 17.6, "标准直径设置错误")
        self.assert_equals(widget.tolerance, 0.2, "公差设置错误")
        
        # 测试异常点
        widget.update_anomaly_points([1, 3])
        # 验证异常点已设置（具体渲染测试需要GUI环境）
        
        # 测试清除
        widget.clear_chart()
        self.assert_equals(len(widget.depth_data), 0, "清除后深度数据必须为空")
        self.assert_equals(len(widget.diameter_data), 0, "清除后直径数据必须为空")
        
        # 测试缩放级别
        initial_zoom = widget._zoom_level
        self.assert_equals(initial_zoom, 1.0, "初始缩放级别必须为1.0")
        
        # 测试获取范围
        xlim, ylim = widget.get_current_range()
        self.assert_true(isinstance(xlim, tuple), "X范围必须是元组")
        self.assert_true(isinstance(ylim, tuple), "Y范围必须是元组")


class TestProcessControllerSafety(ZeroToleranceTest):
    """测试进程控制器安全性"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        controller = chart.process_controller
        
        # 测试初始状态
        status = controller.get_status()
        self.assert_equals(status['status'], 'stopped', "初始状态必须是stopped")
        self.assert_true(status['pid'] is None, "初始PID必须为None")
        
        # 测试空命令
        controller.set_command("")
        status = controller.get_status()
        self.assert_equals(status['command'], "", "必须接受空命令")
        
        # 测试危险命令（不实际执行）
        dangerous_commands = [
            "rm -rf /",
            "format c:",
            "; shutdown -h now",
            "| dd if=/dev/zero of=/dev/sda"
        ]
        
        for cmd in dangerous_commands:
            controller.set_command(cmd)
            status = controller.get_status()
            self.assert_equals(status['command'], cmd, "必须能设置命令（但不执行）")
            
        # 测试状态转换
        self.assert_true(not controller.is_running(), "初始不应运行")
        
        # 测试获取进程列表（不应崩溃）
        processes = self.assert_no_exception(
            controller.get_process_list,
            'python'
        )
        self.assert_true(isinstance(processes, list), "进程列表必须是列表")


class TestEndoscopeManagerValidation(ZeroToleranceTest):
    """测试内窥镜管理器验证"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        manager = chart.endoscope_manager
        
        # 测试有效孔位
        valid_positions = ['A1', 'B2', 'C3', 'H12']
        for pos in valid_positions:
            manager.set_current_position(pos)
            self.assert_equals(manager._current_position, pos, f"孔位 {pos} 设置失败")
            
        # 测试无效孔位
        invalid_positions = ['Z99', 'AA1', '1A', '', None]
        for pos in invalid_positions:
            if pos:
                manager.set_current_position(pos)
                # 不应崩溃，但可能不设置
                
        # 测试探头切换
        manager.set_current_probe(1)
        self.assert_equals(
            manager.get_probe_status()['current_probe'], 1,
            "探头1设置失败"
        )
        
        manager.set_current_probe(2)
        self.assert_equals(
            manager.get_probe_status()['current_probe'], 2,
            "探头2设置失败"
        )
        
        # 测试无效探头号
        manager.set_current_probe(0)  # 无效
        manager.set_current_probe(3)  # 无效
        # 不应崩溃
        
        # 测试自动切换
        manager.start_auto_switch(100)
        status = manager.get_probe_status()
        self.assert_true(status['auto_switch_enabled'], "自动切换未启动")
        
        manager.stop_auto_switch()
        status = manager.get_probe_status()
        self.assert_true(not status['auto_switch_enabled'], "自动切换未停止")
        
        # 测试图像统计
        stats = manager.get_image_statistics()
        self.assert_true(isinstance(stats, dict), "图像统计必须是字典")
        self.assert_true('total_images' in stats, "必须包含总图像数")


class TestIntegrationStress(ZeroToleranceTest):
    """集成压力测试"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        chart = RealtimeChart()
        
        # 模拟实际使用场景
        chart.set_standard_diameter(17.6, 0.2)
        chart.set_detection_method('tolerance')
        
        # 快速添加大量数据
        for i in range(100):
            depth = i * 10
            diameter = 17.6 + np.random.normal(0, 0.1)
            chart.data_manager.add_data_point(depth, diameter)
            
        # 多次更新图表
        for _ in range(10):
            chart._update_chart()
            
        # 检查状态
        buffer_info = chart.data_manager.get_buffer_info()
        self.assert_equals(buffer_info['buffer_size'], 100, "数据点数量错误")
        
        # 测试清除和重新加载
        chart.clear_data()
        buffer_info = chart.data_manager.get_buffer_info()
        self.assert_equals(buffer_info['buffer_size'], 0, "清除后仍有数据")
        
        # 测试快速启停
        for _ in range(5):
            chart.start_monitoring()
            chart.stop_monitoring()
            
        self.assert_true(not chart._is_monitoring, "最终应该是停止状态")
        
        # 测试并发操作
        def add_data_thread():
            for i in range(50):
                chart.data_manager.add_data_point(i, 17.6)
                
        threads = []
        for _ in range(3):
            t = threading.Thread(target=add_data_thread)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # 验证线程安全
        buffer_info = chart.data_manager.get_buffer_info()
        self.assert_true(buffer_info['buffer_size'] > 0, "并发添加数据失败")


class TestMemoryLeaks(ZeroToleranceTest):
    """内存泄漏测试"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 多次创建和销毁实例
        instances = []
        for i in range(10):
            chart = RealtimeChart()
            # 添加一些数据
            chart.data_manager.add_data_batch(
                list(range(100)),
                [17.6] * 100
            )
            instances.append(chart)
            
        # 清理引用
        instances.clear()
        
        # 创建新实例确保能正常工作
        chart = RealtimeChart()
        chart.set_standard_diameter(17.6, 0.2)
        self.assert_true(chart is not None, "新实例创建失败")


class TestBackwardCompatibility(ZeroToleranceTest):
    """向后兼容性测试"""
    
    def test(self):
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 测试旧名称
        from src.modules.realtime_chart_package import RealTimeChart
        
        chart = RealTimeChart()
        self.assert_true(chart is not None, "旧类名实例化失败")
        
        # 测试基本功能
        chart.set_standard_diameter(17.6, 0.2)
        chart.clear_data()
        
        # 验证是新类的实例
        from src.modules.realtime_chart_package import RealtimeChart
        self.assert_true(
            isinstance(chart, RealtimeChart),
            "旧类名必须是新类的实例"
        )


def run_zero_tolerance_tests():
    """运行零容忍测试套件"""
    print("🔬 零容忍测试套件")
    print("=" * 70)
    print("测试标准：所有测试必须通过，任何失败都不可接受")
    print("=" * 70)
    
    # 定义测试列表
    test_classes = [
        TestComponentInitialization,
        TestDataManagerBoundaries,
        TestCSVProcessorEdgeCases,
        TestAnomalyDetectorAccuracy,
        TestChartWidgetInteraction,
        TestProcessControllerSafety,
        TestEndoscopeManagerValidation,
        TestIntegrationStress,
        TestMemoryLeaks,
        TestBackwardCompatibility
    ]
    
    results = []
    total_assertions = 0
    
    for test_class in test_classes:
        test = test_class(test_class.__name__)
        print(f"\n运行测试: {test.name}")
        print("-" * 50)
        
        test.run()
        report = test.get_report()
        results.append(report)
        total_assertions += report['assertions']
        
        if report['passed']:
            print(f"✅ 通过 ({report['assertions']} 个断言, {report['duration']:.3f}秒)")
        else:
            print(f"❌ 失败")
            for error in report['errors']:
                print(f"  错误: {error}")
                
    # 生成总结报告
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed_count = sum(1 for r in results if r['passed'])
    failed_count = len(results) - passed_count
    
    print(f"\n总测试数: {len(results)}")
    print(f"✅ 通过: {passed_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"总断言数: {total_assertions}")
    print(f"总耗时: {sum(r['duration'] for r in results):.3f}秒")
    
    # 保存详细报告
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'passed': passed_count,
        'failed': failed_count,
        'total_assertions': total_assertions,
        'results': results
    }
    
    with open('zero_tolerance_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 详细报告已保存到: zero_tolerance_test_report.json")
    
    # 零容忍判定
    if failed_count == 0:
        print("\n🎉 零容忍测试通过！所有测试完美通过！")
        return True
    else:
        print("\n❌ 零容忍测试失败！存在测试未通过！")
        print("\n失败的测试:")
        for r in results:
            if not r['passed']:
                print(f"  - {r['name']}")
                for error in r['errors']:
                    print(f"    • {error}")
        return False


if __name__ == '__main__':
    success = run_zero_tolerance_tests()
    sys.exit(0 if success else 1)