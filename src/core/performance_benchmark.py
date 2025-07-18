"""
应用程序性能基准测试
验证重构后的应用程序是否满足性能要求
"""

import time
import psutil
import os
import sys
from pathlib import Path
from typing import Dict, Any
import threading

# 添加模块路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from core.application import Application, get_application
from core.dependency_injection import DependencyContainer


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.process = psutil.Process(os.getpid())
    
    def measure_startup_time(self) -> float:
        """测量启动时间"""
        print("📊 测量应用程序启动时间...")
        
        start_time = time.time()
        
        try:
            # 创建应用程序实例
            app = Application()
            
            # 模拟初始化过程
            from unittest.mock import patch
            with patch('PySide6.QtWidgets.QApplication'):
                with patch.object(app, '_core') as mock_core:
                    mock_core._create_qt_application.return_value = True
                    mock_core._check_dependencies.return_value = True
                    success = app.initialize()
            
            end_time = time.time()
            startup_time = end_time - start_time
            
            print(f"✅ 启动时间: {startup_time:.3f}秒")
            
            # 清理
            try:
                app.shutdown()
            except:
                pass
            
            return startup_time
            
        except Exception as e:
            print(f"❌ 启动时间测量失败: {e}")
            return float('inf')
    
    def measure_memory_usage(self) -> Dict[str, float]:
        """测量内存使用"""
        print("📊 测量内存使用...")
        
        # 记录初始内存
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            # 创建多个应用程序组件
            containers = []
            for i in range(10):
                container = DependencyContainer()
                
                # 注册一些测试服务
                class TestService:
                    def __init__(self):
                        self.data = list(range(1000))  # 一些测试数据
                
                container.register(TestService)
                container.resolve(TestService)
                containers.append(container)
            
            # 测量峰值内存
            peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # 清理
            for container in containers:
                container.reset()
            
            # 测量清理后内存
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            memory_overhead = peak_memory - initial_memory
            memory_recovered = peak_memory - final_memory
            
            results = {
                'initial_memory': initial_memory,
                'peak_memory': peak_memory,
                'final_memory': final_memory,
                'memory_overhead': memory_overhead,
                'memory_recovered': memory_recovered
            }
            
            print(f"✅ 初始内存: {initial_memory:.2f}MB")
            print(f"✅ 峰值内存: {peak_memory:.2f}MB")
            print(f"✅ 内存开销: {memory_overhead:.2f}MB")
            print(f"✅ 内存回收: {memory_recovered:.2f}MB")
            
            return results
            
        except Exception as e:
            print(f"❌ 内存使用测量失败: {e}")
            return {}
    
    def measure_dependency_injection_performance(self) -> Dict[str, float]:
        """测量依赖注入性能"""
        print("📊 测量依赖注入性能...")
        
        try:
            container = DependencyContainer()
            
            # 定义测试服务
            class ServiceA:
                def __init__(self, b: 'ServiceB'):
                    self.b = b
            
            class ServiceB:
                def __init__(self, c: 'ServiceC'):
                    self.c = c
            
            class ServiceC:
                def __init__(self):
                    self.value = "test"
            
            # 注册服务
            start_time = time.time()
            container.register(ServiceA)
            container.register(ServiceB)
            container.register(ServiceC)
            registration_time = time.time() - start_time
            
            # 测量解析时间
            resolution_times = []
            for i in range(1000):
                start_time = time.time()
                service = container.resolve(ServiceA)
                end_time = time.time()
                resolution_times.append((end_time - start_time) * 1000)  # 转换为毫秒
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
            max_resolution_time = max(resolution_times)
            min_resolution_time = min(resolution_times)
            
            results = {
                'registration_time': registration_time * 1000,  # 转换为毫秒
                'avg_resolution_time': avg_resolution_time,
                'max_resolution_time': max_resolution_time,
                'min_resolution_time': min_resolution_time
            }
            
            print(f"✅ 服务注册时间: {results['registration_time']:.3f}ms")
            print(f"✅ 平均解析时间: {avg_resolution_time:.3f}ms")
            print(f"✅ 最大解析时间: {max_resolution_time:.3f}ms")
            print(f"✅ 最小解析时间: {min_resolution_time:.3f}ms")
            
            container.reset()
            return results
            
        except Exception as e:
            print(f"❌ 依赖注入性能测量失败: {e}")
            return {}
    
    def measure_event_system_performance(self) -> Dict[str, float]:
        """测量事件系统性能"""
        print("📊 测量事件系统性能...")
        
        try:
            from core.application import EventBus, ApplicationEvent
            
            event_bus = EventBus()
            
            # 事件处理器
            events_received = []
            def event_handler(event):
                events_received.append(event.event_type)
            
            # 注册多个处理器
            for i in range(100):
                event_bus.subscribe("test_event", event_handler)
            
            # 测量事件发布性能
            event_times = []
            for i in range(1000):
                event = ApplicationEvent("test_event", {"data": f"test_{i}"})
                
                start_time = time.time()
                event_bus.post_event(event)
                end_time = time.time()
                
                event_times.append((end_time - start_time) * 1000)  # 转换为毫秒
            
            avg_event_time = sum(event_times) / len(event_times)
            max_event_time = max(event_times)
            min_event_time = min(event_times)
            
            results = {
                'avg_event_time': avg_event_time,
                'max_event_time': max_event_time,
                'min_event_time': min_event_time,
                'total_events_handled': len(events_received)
            }
            
            print(f"✅ 平均事件处理时间: {avg_event_time:.3f}ms")
            print(f"✅ 最大事件处理时间: {max_event_time:.3f}ms")
            print(f"✅ 事件处理总数: {len(events_received)}")
            
            return results
            
        except Exception as e:
            print(f"❌ 事件系统性能测量失败: {e}")
            return {}
    
    def measure_concurrent_performance(self) -> Dict[str, float]:
        """测量并发性能"""
        print("📊 测量并发性能...")
        
        try:
            container = DependencyContainer()
            
            class ConcurrentService:
                def __init__(self):
                    self.thread_id = threading.current_thread().ident
            
            container.register_singleton(ConcurrentService)
            
            # 并发解析测试
            results = []
            threads = []
            
            def resolve_service():
                start_time = time.time()
                service = container.resolve(ConcurrentService)
                end_time = time.time()
                results.append((end_time - start_time) * 1000)  # 毫秒
            
            # 创建并启动多个线程
            for i in range(50):
                thread = threading.Thread(target=resolve_service)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            avg_concurrent_time = sum(results) / len(results)
            max_concurrent_time = max(results)
            thread_count = len(threads)
            
            concurrent_results = {
                'avg_concurrent_time': avg_concurrent_time,
                'max_concurrent_time': max_concurrent_time,
                'thread_count': thread_count,
                'total_resolutions': len(results)
            }
            
            print(f"✅ 并发线程数: {thread_count}")
            print(f"✅ 平均并发解析时间: {avg_concurrent_time:.3f}ms")
            print(f"✅ 最大并发解析时间: {max_concurrent_time:.3f}ms")
            
            container.reset()
            return concurrent_results
            
        except Exception as e:
            print(f"❌ 并发性能测量失败: {e}")
            return {}
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试"""
        print("🚀 开始性能基准测试...")
        print("=" * 60)
        
        # 启动时间测试
        startup_time = self.measure_startup_time()
        self.results['startup_time'] = startup_time
        
        print("\n" + "-" * 40)
        
        # 内存使用测试
        memory_results = self.measure_memory_usage()
        self.results['memory'] = memory_results
        
        print("\n" + "-" * 40)
        
        # 依赖注入性能测试
        di_results = self.measure_dependency_injection_performance()
        self.results['dependency_injection'] = di_results
        
        print("\n" + "-" * 40)
        
        # 事件系统性能测试
        event_results = self.measure_event_system_performance()
        self.results['event_system'] = event_results
        
        print("\n" + "-" * 40)
        
        # 并发性能测试
        concurrent_results = self.measure_concurrent_performance()
        self.results['concurrent'] = concurrent_results
        
        print("\n" + "=" * 60)
        print("📋 性能基准测试完成")
        
        return self.results
    
    def evaluate_performance_requirements(self) -> Dict[str, bool]:
        """评估性能要求"""
        print("\n🎯 评估性能要求:")
        print("-" * 40)
        
        requirements = {}
        
        # 启动时间要求: < 3秒
        startup_ok = self.results.get('startup_time', float('inf')) < 3.0
        requirements['startup_time'] = startup_ok
        print(f"启动时间 < 3秒: {'✅' if startup_ok else '❌'} ({self.results.get('startup_time', 0):.3f}s)")
        
        # 依赖注入性能要求: < 1ms
        di_time = self.results.get('dependency_injection', {}).get('avg_resolution_time', float('inf'))
        di_ok = di_time < 1.0
        requirements['dependency_injection'] = di_ok
        print(f"依赖解析 < 1ms: {'✅' if di_ok else '❌'} ({di_time:.3f}ms)")
        
        # 内存使用要求: 开销 < 20MB
        memory_overhead = self.results.get('memory', {}).get('memory_overhead', float('inf'))
        memory_ok = memory_overhead < 20.0
        requirements['memory_usage'] = memory_ok
        print(f"内存开销 < 20MB: {'✅' if memory_ok else '❌'} ({memory_overhead:.2f}MB)")
        
        # 事件处理性能: < 0.1ms
        event_time = self.results.get('event_system', {}).get('avg_event_time', float('inf'))
        event_ok = event_time < 0.1
        requirements['event_processing'] = event_ok
        print(f"事件处理 < 0.1ms: {'✅' if event_ok else '❌'} ({event_time:.3f}ms)")
        
        # 并发性能: < 2ms
        concurrent_time = self.results.get('concurrent', {}).get('avg_concurrent_time', float('inf'))
        concurrent_ok = concurrent_time < 2.0
        requirements['concurrent_performance'] = concurrent_ok
        print(f"并发解析 < 2ms: {'✅' if concurrent_ok else '❌'} ({concurrent_time:.3f}ms)")
        
        # 总体评估
        all_passed = all(requirements.values())
        requirements['overall'] = all_passed
        
        print("\n" + "-" * 40)
        print(f"总体评估: {'✅ 通过' if all_passed else '❌ 未通过'}")
        passed_count = sum(1 for passed in requirements.values() if passed)
        total_count = len(requirements) - 1  # 排除overall
        print(f"通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
        
        return requirements
    
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        report = []
        report.append("# 应用程序性能基准测试报告")
        report.append("=" * 50)
        report.append("")
        
        # 测试环境信息
        report.append("## 测试环境")
        report.append(f"- Python版本: {sys.version}")
        report.append(f"- 平台: {sys.platform}")
        report.append(f"- CPU核心数: {psutil.cpu_count()}")
        report.append(f"- 内存总量: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f}GB")
        report.append("")
        
        # 性能结果
        report.append("## 性能测试结果")
        report.append("")
        
        if 'startup_time' in self.results:
            report.append(f"### 启动时间: {self.results['startup_time']:.3f}秒")
        
        if 'memory' in self.results:
            memory = self.results['memory']
            report.append(f"### 内存使用:")
            report.append(f"- 内存开销: {memory.get('memory_overhead', 0):.2f}MB")
            report.append(f"- 峰值内存: {memory.get('peak_memory', 0):.2f}MB")
        
        if 'dependency_injection' in self.results:
            di = self.results['dependency_injection']
            report.append(f"### 依赖注入性能:")
            report.append(f"- 平均解析时间: {di.get('avg_resolution_time', 0):.3f}ms")
            report.append(f"- 服务注册时间: {di.get('registration_time', 0):.3f}ms")
        
        if 'event_system' in self.results:
            events = self.results['event_system']
            report.append(f"### 事件系统性能:")
            report.append(f"- 平均事件处理时间: {events.get('avg_event_time', 0):.3f}ms")
            report.append(f"- 事件处理总数: {events.get('total_events_handled', 0)}")
        
        if 'concurrent' in self.results:
            concurrent = self.results['concurrent']
            report.append(f"### 并发性能:")
            report.append(f"- 平均并发解析时间: {concurrent.get('avg_concurrent_time', 0):.3f}ms")
            report.append(f"- 并发线程数: {concurrent.get('thread_count', 0)}")
        
        return "\n".join(report)


def run_performance_benchmark():
    """运行性能基准测试"""
    benchmark = PerformanceBenchmark()
    
    # 运行测试
    results = benchmark.run_full_benchmark()
    
    # 评估要求
    requirements = benchmark.evaluate_performance_requirements()
    
    # 生成报告
    report = benchmark.generate_performance_report()
    
    # 保存报告
    report_file = Path("performance_benchmark_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 性能报告已保存到: {report_file}")
    
    return results, requirements


if __name__ == "__main__":
    results, requirements = run_performance_benchmark()
    
    # 返回退出码
    exit_code = 0 if requirements.get('overall', False) else 1
    sys.exit(exit_code)