"""
依赖注入框架性能测试
验证容器初始化<10ms，依赖解析<1ms的要求
"""

import time
import threading
from typing import Dict, List
from dependency_injection import DependencyContainer, ServiceLifetime, injectable


class PerformanceTestRunner:
    """性能测试运行器"""
    
    def __init__(self):
        self.results: Dict[str, List[float]] = {}
    
    def run_test(self, test_name: str, test_func, iterations: int = 1000):
        """运行性能测试"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            test_func()
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            times.append(execution_time)
        
        self.results[test_name] = times
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n{test_name}:")
        print(f"  平均时间: {avg_time:.3f}ms")
        print(f"  最小时间: {min_time:.3f}ms")
        print(f"  最大时间: {max_time:.3f}ms")
        print(f"  迭代次数: {iterations}")
        
        return avg_time
    
    def get_summary(self):
        """获取性能测试摘要"""
        summary = {}
        for test_name, times in self.results.items():
            summary[test_name] = {
                'avg': sum(times) / len(times),
                'min': min(times),
                'max': max(times),
                'count': len(times)
            }
        return summary


def test_container_initialization():
    """测试容器初始化性能"""
    container = DependencyContainer()
    container.reset()


def test_simple_dependency_resolution():
    """测试简单依赖解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class SimpleService:
        def __init__(self):
            self.value = "test"
    
    container.register(SimpleService)
    container.resolve(SimpleService)


def test_complex_dependency_resolution():
    """测试复杂依赖解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class ServiceD:
        def __init__(self):
            self.value = "test"
    
    class ServiceC:
        def __init__(self, d: ServiceD):
            self.d = d
    
    class ServiceB:
        def __init__(self, c: ServiceC):
            self.c = c
    
    class ServiceA:
        def __init__(self, b: ServiceB):
            self.b = b
    
    container.register(ServiceA)
    container.register(ServiceB)
    container.register(ServiceC)
    container.register(ServiceD)
    
    container.resolve(ServiceA)


def test_singleton_resolution():
    """测试单例解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class SingletonService:
        def __init__(self):
            self.value = "singleton"
    
    container.register_singleton(SingletonService)
    container.resolve(SingletonService)


def test_transient_resolution():
    """测试临时服务解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class TransientService:
        def __init__(self):
            self.value = "transient"
    
    container.register_transient(TransientService)
    container.resolve(TransientService)


def test_scoped_resolution():
    """测试作用域服务解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class ScopedService:
        def __init__(self):
            self.value = "scoped"
    
    container.register_scoped(ScopedService)
    container.resolve(ScopedService, scope_id=1)


def test_factory_resolution():
    """测试工厂函数解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class FactoryService:
        def __init__(self, value: str):
            self.value = value
    
    def factory() -> FactoryService:
        return FactoryService("factory")
    
    container.register(FactoryService, factory=factory)
    container.resolve(FactoryService)


def test_concurrent_resolution():
    """测试并发解析性能"""
    container = DependencyContainer()
    container.reset()
    
    class ConcurrentService:
        def __init__(self):
            self.value = "concurrent"
    
    container.register_singleton(ConcurrentService)
    
    def resolve_service():
        container.resolve(ConcurrentService)
    
    # 创建10个线程并发解析
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=resolve_service)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()


def test_memory_usage():
    """测试内存使用情况"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    container = DependencyContainer()
    container.reset()
    
    # 注册大量服务
    for i in range(1000):
        exec(f"""
class TestService{i}:
    def __init__(self):
        self.value = {i}
        
container.register(TestService{i})
""")
    
    # 解析一些服务
    for i in range(100):
        exec(f"container.resolve(TestService{i})")
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_usage = final_memory - initial_memory
    
    print(f"\n内存使用测试:")
    print(f"  初始内存: {initial_memory:.2f}MB")
    print(f"  最终内存: {final_memory:.2f}MB")
    print(f"  容器内存使用: {memory_usage:.2f}MB")
    
    return memory_usage


def run_performance_tests():
    """运行所有性能测试"""
    print("=" * 50)
    print("依赖注入框架性能测试")
    print("=" * 50)
    
    runner = PerformanceTestRunner()
    
    # 运行各种性能测试
    container_init_time = runner.run_test(
        "容器初始化性能", 
        test_container_initialization, 
        iterations=10000
    )
    
    simple_resolve_time = runner.run_test(
        "简单依赖解析性能", 
        test_simple_dependency_resolution, 
        iterations=10000
    )
    
    complex_resolve_time = runner.run_test(
        "复杂依赖解析性能", 
        test_complex_dependency_resolution, 
        iterations=1000
    )
    
    singleton_resolve_time = runner.run_test(
        "单例解析性能", 
        test_singleton_resolution, 
        iterations=10000
    )
    
    transient_resolve_time = runner.run_test(
        "临时服务解析性能", 
        test_transient_resolution, 
        iterations=10000
    )
    
    scoped_resolve_time = runner.run_test(
        "作用域服务解析性能", 
        test_scoped_resolution, 
        iterations=10000
    )
    
    factory_resolve_time = runner.run_test(
        "工厂函数解析性能", 
        test_factory_resolution, 
        iterations=10000
    )
    
    concurrent_resolve_time = runner.run_test(
        "并发解析性能", 
        test_concurrent_resolution, 
        iterations=100
    )
    
    # 内存使用测试
    memory_usage = test_memory_usage()
    
    print("\n" + "=" * 50)
    print("性能测试结果摘要")
    print("=" * 50)
    
    # 验证性能要求
    print(f"\n性能要求验证:")
    print(f"  容器初始化 < 10ms: {'✓' if container_init_time < 10 else '✗'} ({container_init_time:.3f}ms)")
    print(f"  简单依赖解析 < 1ms: {'✓' if simple_resolve_time < 1 else '✗'} ({simple_resolve_time:.3f}ms)")
    print(f"  复杂依赖解析 < 5ms: {'✓' if complex_resolve_time < 5 else '✗'} ({complex_resolve_time:.3f}ms)")
    print(f"  内存使用 < 5MB: {'✓' if memory_usage < 5 else '✗'} ({memory_usage:.2f}MB)")
    
    # 详细结果
    print(f"\n详细性能结果:")
    for test_name, result in runner.get_summary().items():
        print(f"  {test_name}: {result['avg']:.3f}ms (min: {result['min']:.3f}ms, max: {result['max']:.3f}ms)")
    
    # 性能建议
    print(f"\n性能建议:")
    if simple_resolve_time > 0.5:
        print("  - 简单依赖解析时间较长，考虑优化依赖分析逻辑")
    if complex_resolve_time > 3:
        print("  - 复杂依赖解析时间较长，考虑添加依赖缓存机制")
    if memory_usage > 3:
        print("  - 内存使用较高，考虑优化实例存储和弱引用")
    
    # 总体评估
    passed = all([
        container_init_time < 10,
        simple_resolve_time < 1,
        complex_resolve_time < 5,
        memory_usage < 5
    ])
    
    print(f"\n总体评估: {'通过' if passed else '需要优化'}")


if __name__ == "__main__":
    run_performance_tests()