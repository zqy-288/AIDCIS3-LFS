#!/usr/bin/env python3
"""
综合测试套件 - 完整测试重构后的实时图表模块
"""
import sys
import os
import time
import csv
import json
import threading
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QThread, Signal
from src.modules.realtime_chart import RealtimeChart


class TestResult:
    """测试结果类"""
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0
        self.details = []
        
    def add_detail(self, detail):
        self.details.append(detail)
        
    def to_dict(self):
        return {
            'name': self.name,
            'passed': self.passed,
            'error': str(self.error) if self.error else None,
            'duration': self.duration,
            'details': self.details
        }


class ComprehensiveTestSuite:
    """综合测试套件"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始综合测试套件")
        print("=" * 60)
        
        tests = [
            ("组件初始化", self.test_component_initialization),
            ("数据管理器", self.test_data_manager),
            ("CSV处理器", self.test_csv_processor),
            ("异常检测器", self.test_anomaly_detector),
            ("图表组件", self.test_chart_widget),
            ("内窥镜管理器", self.test_endoscope_manager),
            ("进程控制器", self.test_process_controller),
            ("集成功能", self.test_integration),
            ("性能测试", self.test_performance),
            ("错误处理", self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 测试: {test_name}")
            print("-" * 50)
            
            result = TestResult(test_name)
            start_time = time.time()
            
            try:
                test_func(result)
                result.passed = True
                print(f"✅ {test_name} 通过")
            except Exception as e:
                result.passed = False
                result.error = e
                print(f"❌ {test_name} 失败: {e}")
                import traceback
                traceback.print_exc()
                
            result.duration = time.time() - start_time
            self.results.append(result)
            
        self.generate_report()
        
    def test_component_initialization(self, result):
        """测试组件初始化"""
        chart = RealtimeChart()
        
        # 验证所有组件
        components = [
            'chart_widget', 'data_manager', 'csv_processor',
            'anomaly_detector', 'endoscope_manager', 'process_controller'
        ]
        
        for comp in components:
            if not hasattr(chart, comp):
                raise AssertionError(f"组件 {comp} 未初始化")
            result.add_detail(f"✓ {comp} 已初始化")
            
        # 验证UI元素
        ui_elements = [
            'status_label', 'data_count_label', 'anomaly_count_label',
            'process_status_label', 'start_button', 'stop_button',
            'clear_button', 'export_button'
        ]
        
        for elem in ui_elements:
            if not hasattr(chart, elem):
                raise AssertionError(f"UI元素 {elem} 未找到")
            result.add_detail(f"✓ UI元素 {elem} 已创建")
            
    def test_data_manager(self, result):
        """测试数据管理器"""
        chart = RealtimeChart()
        dm = chart.data_manager
        
        # 测试单点添加
        dm.add_data_point(10, 17.6)
        buffer_info = dm.get_buffer_info()
        assert buffer_info['buffer_size'] == 1
        result.add_detail("✓ 单点数据添加成功")
        
        # 测试批量添加
        depths = list(range(20, 120, 10))
        diameters = [17.6] * 10
        dm.add_data_batch(depths, diameters)
        
        buffer_info = dm.get_buffer_info()
        assert buffer_info['buffer_size'] == 11
        result.add_detail("✓ 批量数据添加成功")
        
        # 测试统计信息
        stats = dm.get_statistics()
        assert stats['count'] == 11
        assert abs(stats['mean'] - 17.6) < 0.001
        result.add_detail("✓ 统计信息计算正确")
        
        # 测试数据清除
        dm.clear_data()
        buffer_info = dm.get_buffer_info()
        assert buffer_info['buffer_size'] == 0
        result.add_detail("✓ 数据清除成功")
        
    def test_csv_processor(self, result):
        """测试CSV处理器"""
        chart = RealtimeChart()
        csv_proc = chart.csv_processor
        
        # 创建测试CSV
        test_file = 'test_comprehensive.csv'
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['深度', '直径'])
            for i in range(5):
                writer.writerow([i * 10, 17.5 + i * 0.1])
                
        # 测试读取
        depths, diameters = csv_proc.read_csv_data(test_file)
        assert len(depths) == 5
        assert len(diameters) == 5
        result.add_detail("✓ CSV读取成功")
        
        # 测试文件监控
        csv_proc.set_csv_file(test_file)
        current_file = csv_proc.get_current_file()
        assert current_file == test_file
        result.add_detail("✓ CSV文件监控设置成功")
        
        # 测试导出
        export_file = 'test_export.csv'
        success = csv_proc.export_data_to_csv(
            [0, 10, 20], [17.5, 17.6, 17.7], export_file
        )
        assert success
        assert os.path.exists(export_file)
        result.add_detail("✓ CSV导出成功")
        
        # 清理
        os.remove(test_file)
        os.remove(export_file)
        
    def test_anomaly_detector(self, result):
        """测试异常检测器"""
        chart = RealtimeChart()
        detector = chart.anomaly_detector
        
        # 设置公差参数
        detector.set_tolerance_parameters(17.6, 0.2)
        detector.set_detection_method('tolerance')
        
        # 测试数据
        depths = [0, 10, 20, 30, 40]
        diameters = [17.6, 17.5, 18.0, 17.3, 17.7]  # 18.0和17.3是异常
        
        # 检测异常
        anomalies = detector.detect_anomalies(depths, diameters)
        assert len(anomalies) == 2
        assert 2 in anomalies  # 18.0的索引
        assert 3 in anomalies  # 17.3的索引
        result.add_detail("✓ 公差异常检测正确")
        
        # 测试统计方法
        detector.set_detection_method('statistical')
        detector.set_statistical_parameters(3, 2.0)
        
        # 清除之前的异常记录
        detector.clear_anomalies()
        
        # 创建有明显离群值的数据
        normal_data = [17.6] * 10
        normal_data[5] = 18.5  # 离群值
        
        anomalies = detector.detect_anomalies(list(range(10)), normal_data)
        assert 5 in anomalies
        result.add_detail("✓ 统计异常检测正确")
        
    def test_chart_widget(self, result):
        """测试图表组件"""
        chart = RealtimeChart()
        widget = chart.chart_widget
        
        # 测试数据更新
        test_depths = [0, 10, 20, 30]
        test_diameters = [17.5, 17.6, 17.7, 17.6]
        
        widget.update_data(test_depths, test_diameters)
        assert len(widget.depth_data) == 4
        assert len(widget.diameter_data) == 4
        result.add_detail("✓ 图表数据更新成功")
        
        # 测试公差线设置
        widget.set_standard_diameter(17.6, 0.2)
        assert widget.show_tolerance_lines == True
        assert widget.standard_diameter == 17.6
        assert widget.tolerance == 0.2
        result.add_detail("✓ 公差线设置成功")
        
        # 测试异常点更新
        widget.update_anomaly_points([1, 3])
        result.add_detail("✓ 异常点标记成功")
        
        # 测试图表清除
        widget.clear_chart()
        assert len(widget.depth_data) == 0
        assert len(widget.diameter_data) == 0
        result.add_detail("✓ 图表清除成功")
        
    def test_endoscope_manager(self, result):
        """测试内窥镜管理器"""
        chart = RealtimeChart()
        manager = chart.endoscope_manager
        
        # 测试孔位设置
        positions = ['A1', 'B2', 'C3']
        for pos in positions:
            manager.set_current_position(pos)
            assert manager._current_position == pos
        result.add_detail("✓ 孔位设置成功")
        
        # 测试探头切换
        manager.set_current_probe(2)
        status = manager.get_probe_status()
        assert status['current_probe'] == 2
        result.add_detail("✓ 探头切换成功")
        
        # 测试自动切换
        manager.start_auto_switch(500)
        status = manager.get_probe_status()
        assert status['auto_switch_enabled'] == True
        
        manager.stop_auto_switch()
        status = manager.get_probe_status()
        assert status['auto_switch_enabled'] == False
        result.add_detail("✓ 自动切换控制成功")
        
    def test_process_controller(self, result):
        """测试进程控制器"""
        chart = RealtimeChart()
        controller = chart.process_controller
        
        # 测试命令设置
        test_command = 'echo "test"'
        controller.set_command(test_command)
        status = controller.get_status()
        assert status['command'] == test_command
        result.add_detail("✓ 命令设置成功")
        
        # 测试进程状态
        assert status['status'] == 'stopped'
        result.add_detail("✓ 进程状态正确")
        
        # 注意：不实际启动进程以避免副作用
        
    def test_integration(self, result):
        """测试集成功能"""
        chart = RealtimeChart()
        
        # 设置标准直径
        chart.set_standard_diameter(17.6, 0.2)
        
        # 添加测试数据
        depths = list(range(0, 50, 5))
        diameters = [17.6, 17.5, 17.7, 18.0, 17.4, 17.6, 17.3, 17.5, 17.6, 17.7]
        
        chart.data_manager.add_data_batch(depths, diameters)
        
        # 触发更新
        chart._update_chart()
        
        # 验证数据流
        display_depths, display_diameters = chart.data_manager.get_display_data()
        assert len(display_depths) == 10
        result.add_detail("✓ 数据流集成正常")
        
        # 验证异常检测
        anomaly_stats = chart.anomaly_detector.get_anomaly_statistics()
        assert anomaly_stats['total_count'] > 0
        result.add_detail("✓ 异常检测集成正常")
        
        # 测试监控启动/停止
        chart.start_monitoring()
        assert chart._is_monitoring == True
        
        chart.stop_monitoring()
        assert chart._is_monitoring == False
        result.add_detail("✓ 监控控制正常")
        
    def test_performance(self, result):
        """测试性能"""
        chart = RealtimeChart()
        
        # 测试大数据集
        large_data_size = 1000
        start_time = time.time()
        
        depths = list(range(large_data_size))
        diameters = [17.6] * large_data_size
        
        chart.data_manager.add_data_batch(depths, diameters)
        
        add_time = time.time() - start_time
        assert add_time < 1.0  # 应该在1秒内完成
        result.add_detail(f"✓ 添加{large_data_size}个数据点用时: {add_time:.3f}秒")
        
        # 测试更新性能
        start_time = time.time()
        chart._update_chart()
        update_time = time.time() - start_time
        
        assert update_time < 0.5  # 应该在0.5秒内完成
        result.add_detail(f"✓ 更新图表用时: {update_time:.3f}秒")
        
    def test_error_handling(self, result):
        """测试错误处理"""
        chart = RealtimeChart()
        
        # 测试无效CSV文件
        chart.csv_processor.set_csv_file('nonexistent.csv')
        result.add_detail("✓ 处理不存在的文件未崩溃")
        
        # 测试无效数据
        try:
            chart.data_manager.add_data_batch([1, 2], [1, 2, 3])  # 长度不匹配
        except ValueError:
            result.add_detail("✓ 正确处理无效数据输入")
            
        # 测试无效孔位
        chart.endoscope_manager.set_current_position('ZZ99')  # 无效孔位
        result.add_detail("✓ 处理无效孔位未崩溃")
        
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # 打印摘要
        print(f"\n总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        # 打印详细结果
        print("\n详细结果:")
        print("-" * 60)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} - {result.name} ({result.duration:.3f}秒)")
            
            if result.details:
                for detail in result.details:
                    print(f"  {detail}")
                    
            if result.error:
                print(f"  错误: {result.error}")
                
        # 保存JSON报告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests/total_tests
            },
            'results': [r.to_dict() for r in self.results]
        }
        
        with open('comprehensive_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 详细报告已保存到: comprehensive_test_report.json")
        
        # 返回是否全部通过
        return failed_tests == 0


def main():
    """主函数"""
    print("🧪 综合测试套件 - 实时图表模块")
    print("=" * 60)
    
    suite = ComprehensiveTestSuite()
    suite.run_all_tests()
    
    # 检查是否所有测试通过
    all_passed = all(r.passed for r in suite.results)
    
    if all_passed:
        print("\n🎉 所有测试通过! 重构成功!")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，需要修复")
        sys.exit(1)


if __name__ == '__main__':
    main()