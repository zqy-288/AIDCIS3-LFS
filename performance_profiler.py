#!/usr/bin/env python3
"""
Performance Profiler for MVVM Architecture
Analyzes system performance and identifies bottlenecks
"""

import sys
import os
import time
import cProfile
import pstats
import psutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal

from src.controllers import MainBusinessController
from src.ui.view_models.view_model_manager import MainViewModelManager
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus


class PerformanceMonitor(QObject):
    """
    Performance monitoring class
    Tracks CPU, memory usage and execution times
    """
    
    performance_update = Signal(dict)  # Performance metrics
    
    def __init__(self):
        super().__init__()
        self.start_time = time.time()
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.metrics = {
            "cpu_percent": [],
            "memory_usage": [],
            "execution_times": {},
            "signal_counts": {},
            "ui_update_times": []
        }
        
        # Start monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._collect_metrics)
        self.monitor_timer.start(100)  # Collect every 100ms
        
    def _collect_metrics(self):
        """Collect performance metrics"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.metrics["cpu_percent"].append(cpu_percent)
            self.metrics["memory_usage"].append(memory_mb)
            
            # Emit metrics update
            current_metrics = {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "memory_growth": memory_mb - self.initial_memory,
                "uptime": time.time() - self.start_time
            }
            self.performance_update.emit(current_metrics)
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            
    @contextmanager
    def measure_execution_time(self, operation_name: str):
        """Context manager to measure execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            if operation_name not in self.metrics["execution_times"]:
                self.metrics["execution_times"][operation_name] = []
            self.metrics["execution_times"][operation_name].append(elapsed)
            
    def record_signal_emission(self, signal_name: str):
        """Record signal emission for analysis"""
        if signal_name not in self.metrics["signal_counts"]:
            self.metrics["signal_counts"][signal_name] = 0
        self.metrics["signal_counts"][signal_name] += 1
        
    def record_ui_update_time(self, update_time: float):
        """Record UI update time"""
        self.metrics["ui_update_times"].append(update_time)
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        total_time = time.time() - self.start_time
        
        report = {
            "total_runtime": total_time,
            "average_cpu": sum(self.metrics["cpu_percent"]) / len(self.metrics["cpu_percent"]) if self.metrics["cpu_percent"] else 0,
            "peak_cpu": max(self.metrics["cpu_percent"]) if self.metrics["cpu_percent"] else 0,
            "current_memory": self.metrics["memory_usage"][-1] if self.metrics["memory_usage"] else 0,
            "peak_memory": max(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0,
            "memory_growth": (self.metrics["memory_usage"][-1] - self.initial_memory) if self.metrics["memory_usage"] else 0,
            "memory_growth_percent": ((self.metrics["memory_usage"][-1] - self.initial_memory) / self.initial_memory * 100) if self.metrics["memory_usage"] else 0,
            "execution_times": {
                name: {
                    "count": len(times),
                    "total": sum(times),
                    "average": sum(times) / len(times),
                    "max": max(times),
                    "min": min(times)
                } for name, times in self.metrics["execution_times"].items()
            },
            "signal_counts": self.metrics["signal_counts"].copy(),
            "ui_update_stats": {
                "count": len(self.metrics["ui_update_times"]),
                "average": sum(self.metrics["ui_update_times"]) / len(self.metrics["ui_update_times"]) if self.metrics["ui_update_times"] else 0,
                "max": max(self.metrics["ui_update_times"]) if self.metrics["ui_update_times"] else 0,
                "updates_over_100ms": len([t for t in self.metrics["ui_update_times"] if t > 0.1])
            }
        }
        
        return report
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitor_timer.stop()


class PerformanceProfiler:
    """
    Main performance profiler class
    Orchestrates performance testing and analysis
    """
    
    def __init__(self):
        self.monitor = None
        self.profiler = None
        
    def create_large_test_dataset(self, hole_count: int = 10000) -> HoleCollection:
        """Create large test dataset for performance testing"""
        print(f"Creating test dataset with {hole_count} holes...")
        holes = {}
        
        # Create grid pattern for realistic data
        cols = int((hole_count ** 0.5)) + 1
        rows = int(hole_count / cols) + 1
        
        for i in range(hole_count):
            row = i // cols
            col = i % cols
            
            hole_id = f"C{col:03d}R{row:03d}"
            hole = HoleData(
                hole_id=hole_id,
                center_x=col * 10.0,
                center_y=row * 10.0,
                radius=2.5,
                status=HoleStatus.PENDING
            )
            holes[hole_id] = hole
            
        collection = HoleCollection()
        collection.holes = holes
        
        # Add bounds method if not present
        if not hasattr(collection, 'get_bounds'):
            collection.get_bounds = lambda: (0, 0, cols * 10, rows * 10)
            
        print(f"✓ Created {len(holes)} holes")
        return collection
        
    def profile_initialization(self) -> Dict[str, Any]:
        """Profile system initialization performance"""
        print("=== Profiling System Initialization ===")
        
        # Create Qt application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        self.monitor = PerformanceMonitor()
        
        # Profile view model manager creation
        with self.monitor.measure_execution_time("view_model_manager_init"):
            view_model_manager = MainViewModelManager()
            
        # Profile business controller creation
        with self.monitor.measure_execution_time("business_controller_init"):
            controller = MainBusinessController(view_model_manager)
            
        # Profile service initialization
        with self.monitor.measure_execution_time("services_init"):
            controller.detection_service.start()
            controller.file_service.start()
            controller.search_service.start()
            controller.status_service.start()
            
        print("✓ System initialization profiled")
        return controller, view_model_manager
        
    def profile_data_loading(self, controller, view_model_manager) -> None:
        """Profile data loading performance"""
        print("=== Profiling Data Loading ===")
        
        # Test different data sizes
        data_sizes = [100, 1000, 5000, 10000]
        
        for size in data_sizes:
            print(f"Testing with {size} holes...")
            
            with self.monitor.measure_execution_time(f"data_loading_{size}"):
                hole_collection = self.create_large_test_dataset(size)
                
            with self.monitor.measure_execution_time(f"view_model_update_{size}"):
                view_model_manager.update_hole_collection(hole_collection)
                
            # Process events to ensure UI updates
            QApplication.processEvents()
            
        print("✓ Data loading profiled")
        
    def profile_detection_workflow(self, controller) -> None:
        """Profile detection workflow performance"""
        print("=== Profiling Detection Workflow ===")
        
        # Create test data
        hole_collection = self.create_large_test_dataset(1000)
        controller.view_model_manager.update_hole_collection(hole_collection)
        
        # Profile detection operations
        operations = [
            ("start_detection", lambda: controller.handle_user_action("start_detection")),
            ("pause_detection", lambda: controller.handle_user_action("pause_detection")),
            ("resume_detection", lambda: controller.handle_user_action("pause_detection")),
            ("stop_detection", lambda: controller.handle_user_action("stop_detection"))
        ]
        
        for op_name, operation in operations:
            with self.monitor.measure_execution_time(f"detection_{op_name}"):
                operation()
                QApplication.processEvents()
                
        print("✓ Detection workflow profiled")
        
    def profile_search_performance(self, controller) -> None:
        """Profile search performance"""
        print("=== Profiling Search Performance ===")
        
        # Create test data
        hole_collection = self.create_large_test_dataset(5000)
        controller.view_model_manager.update_hole_collection(hole_collection)
        
        # Test different search patterns
        search_queries = [
            "C001",      # Specific search
            "C0",        # Prefix search
            "R001",      # Row search
            "SNAKE_DEMO" # Special command
        ]
        
        for query in search_queries:
            with self.monitor.measure_execution_time(f"search_{query}"):
                controller.handle_user_action("perform_search", search_query=query)
                QApplication.processEvents()
                
        print("✓ Search performance profiled")
        
    def profile_signal_transmission(self, controller) -> None:
        """Profile signal transmission performance"""
        print("=== Profiling Signal Transmission ===")
        
        # Count signal emissions
        original_emit = controller.view_model_changed.emit
        signal_count = 0
        
        def counting_emit(*args, **kwargs):
            nonlocal signal_count
            signal_count += 1
            self.monitor.record_signal_emission("view_model_changed")
            return original_emit(*args, **kwargs)
            
        controller.view_model_changed.emit = counting_emit
        
        # Perform operations that trigger signals
        with self.monitor.measure_execution_time("signal_heavy_operations"):
            for i in range(100):
                controller.add_log_message(f"Test message {i}")
                if i % 10 == 0:
                    QApplication.processEvents()
                    
        print(f"✓ Signal transmission profiled ({signal_count} signals)")
        
    def run_comprehensive_profile(self) -> Dict[str, Any]:
        """Run comprehensive performance profile"""
        print("Starting comprehensive performance profiling...")
        start_time = time.time()
        
        try:
            # Initialize profiler
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            
            # Profile system components
            controller, view_model_manager = self.profile_initialization()
            
            # Wait for initialization to complete
            QApplication.processEvents()
            time.sleep(0.5)
            
            # Profile different scenarios
            self.profile_data_loading(controller, view_model_manager)
            self.profile_detection_workflow(controller)
            self.profile_search_performance(controller)
            self.profile_signal_transmission(controller)
            
            # Stop profiling
            self.profiler.disable()
            
            # Generate report
            total_time = time.time() - start_time
            performance_report = self.monitor.get_performance_report()
            performance_report["total_profiling_time"] = total_time
            
            # Cleanup
            controller.cleanup()
            self.monitor.stop_monitoring()
            
            return performance_report
            
        except Exception as e:
            print(f"Error during profiling: {e}")
            import traceback
            traceback.print_exc()
            return {}
            
    def save_profiling_data(self, output_dir: str = "performance_data") -> None:
        """Save profiling data to files"""
        if not self.profiler:
            print("No profiling data available")
            return
            
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save cProfile data
        profile_file = output_path / "profile.stats"
        self.profiler.dump_stats(str(profile_file))
        
        # Save readable profile report
        stats = pstats.Stats(self.profiler)
        stats.sort_stats('cumulative')
        
        with open(output_path / "profile_report.txt", 'w') as f:
            stats.print_stats(50, file=f)
            
        print(f"✓ Profiling data saved to {output_path}")
        
    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze performance bottlenecks"""
        if not self.profiler:
            return []
            
        stats = pstats.Stats(self.profiler)
        stats.sort_stats('cumulative')
        
        # Get top time-consuming functions
        bottlenecks = []
        for func_info in stats.get_stats().items():
            func_name = func_info[0]
            func_stats = func_info[1]
            
            if func_stats.cumulative > 0.1:  # Functions taking > 100ms
                bottlenecks.append({
                    "function": f"{func_name[0]}:{func_name[1]}({func_name[2]})",
                    "calls": func_stats.callcount,
                    "total_time": func_stats.totaltime,
                    "cumulative_time": func_stats.cumulative,
                    "avg_time": func_stats.cumulative / func_stats.callcount if func_stats.callcount > 0 else 0
                })
                
        # Sort by cumulative time
        bottlenecks.sort(key=lambda x: x["cumulative_time"], reverse=True)
        return bottlenecks[:10]  # Top 10 bottlenecks


def main():
    """Main profiling execution"""
    print("MVVM Architecture Performance Profiling")
    print("=" * 50)
    
    profiler = PerformanceProfiler()
    
    try:
        # Run comprehensive profiling
        performance_report = profiler.run_comprehensive_profile()
        
        if performance_report:
            print("\n=== Performance Report ===")
            print(f"Total Runtime: {performance_report.get('total_runtime', 0):.2f}s")
            print(f"Average CPU: {performance_report.get('average_cpu', 0):.1f}%")
            print(f"Peak CPU: {performance_report.get('peak_cpu', 0):.1f}%")
            print(f"Current Memory: {performance_report.get('current_memory', 0):.1f}MB")
            print(f"Memory Growth: {performance_report.get('memory_growth', 0):.1f}MB ({performance_report.get('memory_growth_percent', 0):.1f}%)")
            
            # Check performance requirements
            startup_time = performance_report.get('execution_times', {}).get('view_model_manager_init', {}).get('average', 0)
            ui_response_time = performance_report.get('ui_update_stats', {}).get('average', 0)
            memory_growth_percent = performance_report.get('memory_growth_percent', 0)
            
            print(f"\n=== Performance Requirements Check ===")
            print(f"Startup Time: {startup_time*1000:.1f}ms {'✓' if startup_time < 5.0 else '✗'} (requirement: <5s)")
            print(f"UI Response: {ui_response_time*1000:.1f}ms {'✓' if ui_response_time < 0.1 else '✗'} (requirement: <100ms)")
            print(f"Memory Growth: {memory_growth_percent:.1f}% {'✓' if memory_growth_percent < 20 else '✗'} (requirement: <20%)")
            
            # Analyze bottlenecks
            bottlenecks = profiler.analyze_bottlenecks()
            if bottlenecks:
                print(f"\n=== Top Performance Bottlenecks ===")
                for i, bottleneck in enumerate(bottlenecks[:5], 1):
                    print(f"{i}. {bottleneck['function']}")
                    print(f"   Calls: {bottleneck['calls']}, Time: {bottleneck['cumulative_time']:.3f}s")
            
            # Save profiling data
            profiler.save_profiling_data()
            
        return 0
        
    except Exception as e:
        print(f"Profiling failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)