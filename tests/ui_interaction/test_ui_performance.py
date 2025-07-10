#!/usr/bin/env python3
"""
UI性能测试：大规模数据交互性能
UI Performance Tests: Large Scale Data Interaction Performance
"""

import unittest
import time
import sys
import os
from pathlib import Path
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入测试基础组件
from test_dxf_ui_integration import MockInteractionHandler, MockQKeyEvent, MockQt


class TestUIPerformance(unittest.TestCase):
    """UI性能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.interaction_handler = MockInteractionHandler()
        
        # 创建大规模数据适配器
        self.large_scale_adapter = self._create_large_scale_adapter()
        self.interaction_handler.set_dxf_integration(self.large_scale_adapter)
        
        # 性能记录
        self.performance_metrics = {}
    
    def _create_large_scale_adapter(self):
        """创建大规模数据适配器"""
        adapter = Mock()
        
        # 创建大量孔位数据
        hole_counts = [100, 500, 1000, 5000]
        self.hole_datasets = {}
        
        for count in hole_counts:
            holes = []
            for i in range(count):
                hole = {
                    "hole_id": f"H{i+1:05d}",
                    "position": {"x": float(i % 100), "y": float(i // 100)},
                    "status": "pending"
                }
                holes.append(hole)
            self.hole_datasets[count] = holes
        
        # 默认返回1000个孔位
        adapter.get_hole_list.return_value = self.hole_datasets[1000]
        adapter.update_hole_status_ui.return_value = True
        adapter.navigate_to_realtime.return_value = {"success": True}
        
        return adapter
    
    def _measure_performance(self, operation_name, operation_func, *args, **kwargs):
        """测量操作性能"""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        self.performance_metrics[operation_name] = duration
        
        return result, duration
    
    def test_large_scale_selection_performance(self):
        """测试大规模选择性能"""
        print("\n📊 测试大规模选择性能")
        
        for hole_count in [100, 500, 1000, 5000]:
            print(f"\n   测试 {hole_count} 个孔位:")
            
            # 设置对应数量的孔位数据
            self.large_scale_adapter.get_hole_list.return_value = self.hole_datasets[hole_count]
            
            # 测试全选性能
            event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            
            _, duration = self._measure_performance(
                f"select_all_{hole_count}",
                self.interaction_handler.keyPressEvent,
                event
            )
            
            print(f"      全选 {hole_count} 个孔位: {duration:.3f}秒")
            
            # 验证选择结果
            self.assertEqual(len(self.interaction_handler.selected_holes), hole_count)
            
            # 测试清除选择性能
            clear_event = MockQKeyEvent(MockQt.Key_Escape)
            
            _, clear_duration = self._measure_performance(
                f"clear_selection_{hole_count}",
                self.interaction_handler.keyPressEvent,
                clear_event
            )
            
            print(f"      清除 {hole_count} 个孔位: {clear_duration:.3f}秒")
            
            # 验证清除结果
            self.assertEqual(len(self.interaction_handler.selected_holes), 0)
            
            # 性能要求验证
            self.assertLess(duration, 1.0, f"{hole_count}个孔位全选耗时过长")
            self.assertLess(clear_duration, 0.5, f"{hole_count}个孔位清除耗时过长")
        
        print("   ✅ 大规模选择性能测试通过")
    
    def test_rapid_keyboard_input_performance(self):
        """测试快速键盘输入性能"""
        print("\n⚡ 测试快速键盘输入性能")
        
        # 设置中等规模数据
        self.large_scale_adapter.get_hole_list.return_value = self.hole_datasets[1000]
        
        # 模拟快速键盘操作序列
        operations = [
            ("全选", MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)),
            ("清除", MockQKeyEvent(MockQt.Key_Escape)),
            ("全选", MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)),
            ("删除", MockQKeyEvent(MockQt.Key_Delete)),
            ("清除", MockQKeyEvent(MockQt.Key_Escape)),
        ]
        
        # 执行快速操作序列
        start_time = time.time()
        
        for i in range(10):  # 重复10次
            for op_name, event in operations:
                self.interaction_handler.keyPressEvent(event)
        
        total_time = time.time() - start_time
        avg_time_per_operation = total_time / (10 * len(operations))
        
        print(f"   快速操作序列: {total_time:.3f}秒 (50次操作)")
        print(f"   平均每次操作: {avg_time_per_operation:.3f}秒")
        
        # 性能要求
        self.assertLess(avg_time_per_operation, 0.1, "单次操作耗时过长")
        self.assertLess(total_time, 5.0, "快速操作序列总耗时过长")
        
        print("   ✅ 快速键盘输入性能测试通过")
    
    def test_memory_usage_during_interactions(self):
        """测试交互过程中的内存使用"""
        print("\n💾 测试交互内存使用")
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
        except ImportError:
            self.skipTest("psutil not available for memory monitoring")
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   初始内存: {initial_memory:.2f} MB")
        
        # 执行大量交互操作
        self.large_scale_adapter.get_hole_list.return_value = self.hole_datasets[5000]
        
        for i in range(100):  # 100次交互循环
            # 全选
            event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            self.interaction_handler.keyPressEvent(event)
            
            # 清除
            clear_event = MockQKeyEvent(MockQt.Key_Escape)
            self.interaction_handler.keyPressEvent(clear_event)
            
            # 每10次检查一次内存
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"   第{i+1}次循环后内存: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
        
        # 最终内存检查
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"   最终内存: {final_memory:.2f} MB")
        print(f"   总内存增长: {total_increase:.2f} MB")
        
        # 内存使用要求
        self.assertLess(total_increase, 100, "内存增长过多")  # 不超过100MB
        
        print("   ✅ 内存使用测试通过")
    
    def test_concurrent_interaction_performance(self):
        """测试并发交互性能"""
        print("\n🔄 测试并发交互性能")
        
        import threading
        import queue
        
        # 设置数据
        self.large_scale_adapter.get_hole_list.return_value = self.hole_datasets[1000]
        
        # 结果队列
        results_queue = queue.Queue()
        
        def worker_thread(thread_id, operations_count):
            """工作线程"""
            try:
                start_time = time.time()
                
                # 创建独立的交互处理器
                handler = MockInteractionHandler()
                handler.set_dxf_integration(self.large_scale_adapter)
                
                # 执行操作
                for i in range(operations_count):
                    event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
                    handler.keyPressEvent(event)
                    
                    clear_event = MockQKeyEvent(MockQt.Key_Escape)
                    handler.keyPressEvent(clear_event)
                
                duration = time.time() - start_time
                results_queue.put((thread_id, duration, True))
                
            except Exception as e:
                results_queue.put((thread_id, 0, False, str(e)))
        
        # 启动多个并发线程
        num_threads = 5
        operations_per_thread = 20
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=worker_thread,
                args=(i, operations_per_thread)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 收集结果
        successful_threads = 0
        total_thread_time = 0
        
        while not results_queue.empty():
            result = results_queue.get()
            if len(result) >= 3 and result[2]:  # 成功
                successful_threads += 1
                total_thread_time += result[1]
            else:  # 失败
                print(f"   线程 {result[0]} 失败: {result[3] if len(result) > 3 else '未知错误'}")
        
        avg_thread_time = total_thread_time / successful_threads if successful_threads > 0 else 0
        
        print(f"   并发线程数: {num_threads}")
        print(f"   成功线程数: {successful_threads}")
        print(f"   总耗时: {total_time:.3f}秒")
        print(f"   平均线程耗时: {avg_thread_time:.3f}秒")
        
        # 性能要求
        self.assertEqual(successful_threads, num_threads, "存在线程失败")
        self.assertLess(total_time, 10.0, "并发操作总耗时过长")
        
        print("   ✅ 并发交互性能测试通过")
    
    def test_ui_responsiveness_simulation(self):
        """测试UI响应性模拟"""
        print("\n🎯 测试UI响应性模拟")
        
        # 模拟UI刷新频率 (60 FPS = 16.67ms per frame)
        target_frame_time = 1.0 / 60  # 60 FPS
        
        self.large_scale_adapter.get_hole_list.return_value = self.hole_datasets[1000]
        
        # 测试在目标帧时间内能完成多少操作
        operations_in_frame = 0
        frame_start = time.time()
        
        while (time.time() - frame_start) < target_frame_time:
            # 执行轻量级操作
            self.interaction_handler.select_hole(f"H{operations_in_frame % 1000 + 1:05d}")
            operations_in_frame += 1
        
        print(f"   单帧内完成操作数: {operations_in_frame}")
        print(f"   目标帧时间: {target_frame_time * 1000:.2f}ms")
        
        # 测试重量级操作的帧时间影响
        heavy_operations = [
            ("全选1000个孔位", lambda: self.interaction_handler.keyPressEvent(
                MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier))),
            ("清除1000个孔位", lambda: self.interaction_handler.keyPressEvent(
                MockQKeyEvent(MockQt.Key_Escape))),
        ]
        
        for op_name, op_func in heavy_operations:
            start_time = time.time()
            op_func()
            duration = time.time() - start_time
            
            frames_affected = duration / target_frame_time
            print(f"   {op_name}: {duration * 1000:.2f}ms ({frames_affected:.1f} 帧)")
            
            # 响应性要求：重量级操作不应影响超过3帧
            self.assertLess(frames_affected, 3.0, f"{op_name}影响帧数过多")
        
        print("   ✅ UI响应性测试通过")
    
    def print_performance_summary(self):
        """打印性能总结"""
        print("\n📊 性能测试总结")
        print("-" * 50)
        
        for operation, duration in self.performance_metrics.items():
            print(f"   {operation}: {duration:.3f}秒")


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加性能测试
    test_case = TestUIPerformance()
    suite.addTest(TestUIPerformance('test_large_scale_selection_performance'))
    suite.addTest(TestUIPerformance('test_rapid_keyboard_input_performance'))
    suite.addTest(TestUIPerformance('test_memory_usage_during_interactions'))
    suite.addTest(TestUIPerformance('test_concurrent_interaction_performance'))
    suite.addTest(TestUIPerformance('test_ui_responsiveness_simulation'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印性能总结
    if hasattr(test_case, 'performance_metrics'):
        test_case.print_performance_summary()
