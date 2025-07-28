"""
Performance benchmark tests for the MainWindow refactoring system.
Tests performance characteristics and identifies bottlenecks.
"""

import unittest
import time
import psutil
import os
import sys
from unittest.mock import Mock, patch
import statistics
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tests.base_test_case import BaseTestCase


class PerformanceBenchmark(BaseTestCase):
    """Base class for performance benchmarking."""
    
    def setUp(self):
        """Set up performance testing environment."""
        super().setUp()
        
        # Performance tracking
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
        self.cpu_usage = []
        
        # Benchmark results
        self.benchmark_results = {}
        
        # Setup mock components for performance testing
        self.setup_performance_mocks()
    
    def setup_performance_mocks(self):
        """Set up mocks for performance testing."""
        # Mock heavy operations
        self.mock_database_operations = Mock()
        self.mock_graphics_rendering = Mock()
        self.mock_file_operations = Mock()
        self.mock_data_processing = Mock()
    
    def start_benchmark(self, test_name):
        """Start performance benchmarking for a test."""
        self.start_time = time.time()
        self.memory_usage = []
        self.cpu_usage = []
        
        # Record initial system state
        self.record_system_metrics()
        
        print(f"Starting benchmark: {test_name}")
    
    def end_benchmark(self, test_name):
        """End performance benchmarking and record results."""
        self.end_time = time.time()
        
        # Record final system state
        self.record_system_metrics()
        
        # Calculate metrics
        execution_time = self.end_time - self.start_time
        avg_memory = statistics.mean(self.memory_usage) if self.memory_usage else 0
        avg_cpu = statistics.mean(self.cpu_usage) if self.cpu_usage else 0
        
        # Store results
        self.benchmark_results[test_name] = {
            "execution_time": execution_time,
            "average_memory_mb": avg_memory,
            "average_cpu_percent": avg_cpu,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Completed benchmark: {test_name}")
        print(f"Execution time: {execution_time:.4f} seconds")
        print(f"Average memory usage: {avg_memory:.2f} MB")
        print(f"Average CPU usage: {avg_cpu:.2f}%")
    
    def record_system_metrics(self):
        """Record current system metrics."""
        try:
            # Memory usage in MB
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
            
            # CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.append(cpu_percent)
        except Exception as e:
            print(f"Warning: Could not record system metrics: {e}")
    
    def assert_performance_threshold(self, test_name, max_time_seconds, max_memory_mb=None):
        """Assert that performance is within acceptable thresholds."""
        if test_name not in self.benchmark_results:
            self.fail(f"No benchmark results found for test: {test_name}")
        
        results = self.benchmark_results[test_name]
        
        # Check execution time
        self.assertLessEqual(
            results["execution_time"],
            max_time_seconds,
            f"Test {test_name} took {results['execution_time']:.4f}s, "
            f"exceeding threshold of {max_time_seconds}s"
        )
        
        # Check memory usage if specified
        if max_memory_mb:
            self.assertLessEqual(
                results["average_memory_mb"],
                max_memory_mb,
                f"Test {test_name} used {results['average_memory_mb']:.2f}MB, "
                f"exceeding threshold of {max_memory_mb}MB"
            )
    
    def save_benchmark_results(self, filename="benchmark_results.json"):
        """Save benchmark results to a file."""
        output_file = os.path.join(self.temp_dir, filename)
        with open(output_file, 'w') as f:
            json.dump(self.benchmark_results, f, indent=2)
        return output_file


class TestApplicationStartupPerformance(PerformanceBenchmark):
    """Test application startup performance."""
    
    def test_application_initialization_performance(self):
        """Test application initialization performance."""
        test_name = "application_initialization"
        self.start_benchmark(test_name)
        
        # Simulate application initialization
        self.simulate_application_startup()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=2.0, max_memory_mb=100.0)
    
    def simulate_application_startup(self):
        """Simulate application startup operations."""
        # Simulate loading configuration
        time.sleep(0.1)
        
        # Simulate database initialization
        for _ in range(10):
            self.mock_database_operations.initialize_table()
        
        # Simulate UI component creation
        for _ in range(50):
            self.mock_graphics_rendering.create_widget()
        
        # Simulate plugin loading
        for _ in range(5):
            self.mock_file_operations.load_plugin()
    
    def test_main_window_creation_performance(self):
        """Test main window creation performance."""
        test_name = "main_window_creation"
        self.start_benchmark(test_name)
        
        # Simulate main window creation
        for _ in range(10):
            mock_window = Mock()
            mock_window.initialize()
            mock_window.setup_ui()
            mock_window.connect_signals()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=1.0)


class TestDataProcessingPerformance(PerformanceBenchmark):
    """Test data processing performance."""
    
    def test_large_dataset_loading_performance(self):
        """Test loading large datasets performance."""
        test_name = "large_dataset_loading"
        self.start_benchmark(test_name)
        
        # Simulate loading large dataset
        self.simulate_large_dataset_processing()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=5.0, max_memory_mb=200.0)
    
    def simulate_large_dataset_processing(self):
        """Simulate processing of large datasets."""
        # Simulate loading 10000 hole records
        for i in range(10000):
            hole_data = {
                "id": i,
                "x": i * 0.1,
                "y": i * 0.2,
                "diameter": 5.0 + (i % 10) * 0.1
            }
            self.mock_data_processing.process_hole(hole_data)
            
            # Record metrics every 1000 iterations
            if i % 1000 == 0:
                self.record_system_metrics()
    
    def test_dxf_parsing_performance(self):
        """Test DXF file parsing performance."""
        test_name = "dxf_parsing"
        self.start_benchmark(test_name)
        
        # Simulate DXF file parsing
        for _ in range(100):
            self.mock_file_operations.parse_dxf_entity()
            self.mock_data_processing.validate_entity()
            self.mock_data_processing.transform_coordinates()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=3.0)
    
    def test_database_operations_performance(self):
        """Test database operations performance."""
        test_name = "database_operations"
        self.start_benchmark(test_name)
        
        # Simulate database operations
        for i in range(1000):
            # Simulate INSERT
            self.mock_database_operations.insert_record(f"record_{i}")
            
            # Simulate SELECT every 10 insertions
            if i % 10 == 0:
                self.mock_database_operations.select_records()
            
            # Record metrics every 100 operations
            if i % 100 == 0:
                self.record_system_metrics()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=2.0)


class TestGraphicsRenderingPerformance(PerformanceBenchmark):
    """Test graphics rendering performance."""
    
    def test_hole_rendering_performance(self):
        """Test hole rendering performance."""
        test_name = "hole_rendering"
        self.start_benchmark(test_name)
        
        # Simulate rendering many holes
        for i in range(5000):
            self.mock_graphics_rendering.render_hole(i, i*0.1, i*0.2)
            
            # Record metrics every 500 holes
            if i % 500 == 0:
                self.record_system_metrics()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=4.0)
    
    def test_panorama_rendering_performance(self):
        """Test panorama rendering performance."""
        test_name = "panorama_rendering"
        self.start_benchmark(test_name)
        
        # Simulate panorama rendering
        for sector in range(8):
            for hole in range(100):
                self.mock_graphics_rendering.render_sector_hole(sector, hole)
            self.mock_graphics_rendering.compose_sector(sector)
        
        self.mock_graphics_rendering.compose_panorama()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=6.0)
    
    def test_zoom_and_pan_performance(self):
        """Test zoom and pan operations performance."""
        test_name = "zoom_pan_operations"
        self.start_benchmark(test_name)
        
        # Simulate zoom and pan operations
        for i in range(100):
            # Simulate zoom operation
            zoom_factor = 1.0 + (i % 10) * 0.1
            self.mock_graphics_rendering.zoom(zoom_factor)
            
            # Simulate pan operation
            pan_x = i * 10
            pan_y = i * 5
            self.mock_graphics_rendering.pan(pan_x, pan_y)
            
            # Simulate redraw
            self.mock_graphics_rendering.redraw()
            
            # Record metrics every 10 operations
            if i % 10 == 0:
                self.record_system_metrics()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=2.0)


class TestMemoryUsagePerformance(PerformanceBenchmark):
    """Test memory usage and potential memory leaks."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        test_name = "memory_leak_detection"
        self.start_benchmark(test_name)
        
        initial_memory = self.get_current_memory_usage()
        
        # Perform repeated operations that might cause memory leaks
        for iteration in range(100):
            # Simulate creating and destroying objects
            mock_objects = []
            for i in range(100):
                mock_obj = Mock()
                mock_obj.data = list(range(100))  # Simulate some data
                mock_objects.append(mock_obj)
            
            # Clear objects
            mock_objects.clear()
            
            # Record memory usage
            self.record_system_metrics()
        
        final_memory = self.get_current_memory_usage()
        memory_growth = final_memory - initial_memory
        
        self.end_benchmark(test_name)
        
        # Assert memory growth is reasonable (less than 50MB)
        self.assertLess(
            memory_growth,
            50.0,
            f"Memory usage grew by {memory_growth:.2f}MB, indicating potential memory leak"
        )
    
    def get_current_memory_usage(self):
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def test_large_object_creation_performance(self):
        """Test performance when creating large objects."""
        test_name = "large_object_creation"
        self.start_benchmark(test_name)
        
        # Create large objects
        large_objects = []
        for i in range(10):
            # Simulate large data structure
            large_data = {
                "holes": [{"id": j, "data": list(range(1000))} for j in range(1000)],
                "metadata": {"created": time.time(), "size": 1000}
            }
            large_objects.append(large_data)
            
            self.record_system_metrics()
        
        # Clear objects
        large_objects.clear()
        
        self.end_benchmark(test_name)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=5.0, max_memory_mb=500.0)


class TestConcurrentOperationsPerformance(PerformanceBenchmark):
    """Test performance under concurrent operations."""
    
    def test_concurrent_data_access_performance(self):
        """Test performance of concurrent data access."""
        import threading
        
        test_name = "concurrent_data_access"
        self.start_benchmark(test_name)
        
        # Shared data structure
        shared_data = {"counter": 0}
        lock = threading.Lock()
        
        def worker_thread(thread_id):
            for i in range(100):
                with lock:
                    shared_data["counter"] += 1
                
                # Simulate some work
                self.mock_data_processing.process_item(f"thread_{thread_id}_item_{i}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        self.end_benchmark(test_name)
        
        # Verify all operations completed
        self.assertEqual(shared_data["counter"], 500)
        
        # Assert performance thresholds
        self.assert_performance_threshold(test_name, max_time_seconds=3.0)


class PerformanceBenchmarkRunner:
    """Runner for executing all performance benchmarks."""
    
    def __init__(self):
        self.test_suite = unittest.TestSuite()
        self.results = {}
    
    def add_benchmark_tests(self):
        """Add all benchmark test classes to the suite."""
        benchmark_classes = [
            TestApplicationStartupPerformance,
            TestDataProcessingPerformance,
            TestGraphicsRenderingPerformance,
            TestMemoryUsagePerformance,
            TestConcurrentOperationsPerformance
        ]
        
        for test_class in benchmark_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            self.test_suite.addTests(tests)
    
    def run_benchmarks(self):
        """Run all performance benchmarks."""
        print("Starting Performance Benchmark Suite")
        print("=" * 50)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(self.test_suite)
        
        print("=" * 50)
        print("Performance Benchmark Suite Completed")
        
        return result
    
    def generate_report(self, output_file="performance_report.json"):
        """Generate a performance report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count(),
            },
            "benchmark_results": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Performance report saved to: {output_file}")


if __name__ == '__main__':
    # Run performance benchmarks
    runner = PerformanceBenchmarkRunner()
    runner.add_benchmark_tests()
    result = runner.run_benchmarks()
    runner.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)