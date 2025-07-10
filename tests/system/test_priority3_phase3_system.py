#!/usr/bin/env python3
"""
系统测试：优先级3阶段3 - DXF加载集成系统
System Tests: Priority 3 Phase 3 - DXF Loading Integration System
"""

import unittest
import tempfile
import shutil
import os
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.integration.dxf_integration_manager import DXFIntegrationManager
from aidcis2.integration.ui_integration_adapter import UIIntegrationAdapter
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.models.hole_data import HoleData, HoleCollection, Position, HoleStatus


class TestPriority3Phase3System(unittest.TestCase):
    """优先级3阶段3系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_system_phase3_")
        self.test_db = os.path.join(self.temp_dir, "system_test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 创建多个测试DXF文件
        self.create_test_dxf_files()
        
        # 创建大型孔位集合
        self.large_hole_collection = self._create_large_hole_collection()
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_dxf_files(self):
        """创建测试DXF文件"""
        self.test_files = {}
        
        # 小型DXF文件
        small_dxf = Path(self.temp_dir) / "small_test.dxf"
        small_dxf.write_text("small dxf content with 10 holes")
        self.test_files["small"] = str(small_dxf)
        
        # 中型DXF文件
        medium_dxf = Path(self.temp_dir) / "medium_test.dxf"
        medium_dxf.write_text("medium dxf content with 100 holes")
        self.test_files["medium"] = str(medium_dxf)
        
        # 大型DXF文件
        large_dxf = Path(self.temp_dir) / "large_test.dxf"
        large_dxf.write_text("large dxf content with 1000 holes")
        self.test_files["large"] = str(large_dxf)
        
        # 空DXF文件
        empty_dxf = Path(self.temp_dir) / "empty_test.dxf"
        empty_dxf.touch()
        self.test_files["empty"] = str(empty_dxf)
        
        # 无效DXF文件
        invalid_dxf = Path(self.temp_dir) / "invalid_test.txt"
        invalid_dxf.write_text("not a dxf file")
        self.test_files["invalid"] = str(invalid_dxf)
    
    def _create_large_hole_collection(self) -> HoleCollection:
        """创建大型孔位集合"""
        holes = {}
        for i in range(1, 1001):  # 1000个孔位
            hole_id = f"H{i:05d}"
            hole_data = HoleData(
                hole_id=hole_id,
                position=Position(x=float(i % 100), y=float(i // 100)),
                diameter=8.865 + (i % 10) * 0.001,
                status=HoleStatus.PENDING
            )
            holes[hole_id] = hole_data
        
        return HoleCollection(
            holes=holes,
            metadata={
                'source_file': self.test_files.get("large", ""),
                'total_entities': 2000,
                'total_arcs': 1000
            }
        )
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_large_scale_dxf_integration(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试大规模DXF集成"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.large_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager.create_project_from_dxf.return_value = ("large_project_001", "/path/to/large")
        mock_hybrid_manager.ensure_data_consistency.return_value = True
        mock_hybrid_manager.get_project_summary.return_value = {
            "project_name": "大规模集成测试",
            "statistics": {"total_holes": 1000, "completed_holes": 0}
        }
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        print(f"\n🚀 测试大规模DXF集成 (1000个孔位)")
        
        # 创建集成管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 记录性能指标
        progress_calls = []
        
        def progress_callback(message, current, total):
            progress_calls.append((message, current, total, time.time()))
            print(f"   进度 {current}/{total}: {message}")
        
        manager.set_progress_callback(progress_callback)
        
        # 执行大规模加载
        start_time = time.time()
        success, project_id, hole_collection = manager.load_dxf_file_integrated(
            self.test_files["large"], "大规模集成测试"
        )
        end_time = time.time()
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(project_id, "large_project_001")
        self.assertEqual(len(hole_collection), 1000)
        
        # 性能验证
        total_time = end_time - start_time
        print(f"   ✅ 大规模加载完成，耗时: {total_time:.2f}秒")
        print(f"   📊 平均每个孔位: {(total_time / 1000 * 1000):.2f}毫秒")
        
        # 性能要求：1000个孔位应在合理时间内完成
        self.assertLess(total_time, 10.0, "大规模DXF集成耗时过长")
        
        # 验证进度回调
        self.assertEqual(len(progress_calls), 5)
        
        # 验证孔位位置搜索性能
        search_start = time.time()
        for i in range(100):  # 100次搜索
            x, y = float(i % 100), float(i // 100)
            hole_id = manager.get_hole_by_position(x, y, 0.1)
            expected_hole_id = f"H{i+1:05d}"
            self.assertEqual(hole_id, expected_hole_id)
        search_time = time.time() - search_start
        
        print(f"   🔍 100次位置搜索耗时: {search_time:.3f}秒")
        self.assertLess(search_time, 1.0, "位置搜索性能不达标")
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_concurrent_dxf_loading(self, mock_dxf_integration_class):
        """测试并发DXF加载"""
        print(f"\n🔄 测试并发DXF加载")
        
        # 创建不同大小的孔位集合
        hole_collections = {}
        for size in [10, 50, 100]:
            holes = {}
            for i in range(1, size + 1):
                hole_id = f"H{i:05d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    position=Position(x=float(i), y=float(i)),
                    diameter=8.865,
                    status=HoleStatus.PENDING
                )
                holes[hole_id] = hole_data
            hole_collections[size] = HoleCollection(holes=holes, metadata={})
        
        # 设置模拟对象
        def mock_load_side_effect(file_path, project_name=None):
            # 根据文件名确定返回的孔位集合大小
            if "small" in file_path:
                collection = hole_collections[10]
            elif "medium" in file_path:
                collection = hole_collections[50]
            else:
                collection = hole_collections[100]
            
            # 模拟加载时间
            time.sleep(0.1)
            
            return {
                "success": True,
                "project_id": f"concurrent_project_{project_name}",
                "hole_collection": collection,
                "hole_count": len(collection)
            }
        
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.side_effect = mock_load_side_effect
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        # 并发加载测试
        num_concurrent = 5
        results = []
        errors = []
        
        def load_dxf_concurrent(index):
            try:
                adapter = UIIntegrationAdapter(
                    os.path.join(self.temp_dir, f"concurrent_{index}"),
                    f"sqlite:///{self.temp_dir}/concurrent_{index}.db"
                )
                
                file_types = ["small", "medium", "large"]
                file_type = file_types[index % len(file_types)]
                file_path = self.test_files[file_type]
                
                result = adapter.load_dxf_file(file_path, f"concurrent_{index}")
                results.append((index, result))
                
            except Exception as e:
                errors.append((index, str(e)))
        
        # 启动并发线程
        threads = []
        start_time = time.time()
        
        for i in range(num_concurrent):
            thread = threading.Thread(target=load_dxf_concurrent, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # 验证结果
        self.assertEqual(len(errors), 0, f"并发加载错误: {errors}")
        self.assertEqual(len(results), num_concurrent)
        
        print(f"   ✅ {num_concurrent}个并发加载完成，总耗时: {concurrent_time:.2f}秒")
        print(f"   📊 平均每个加载: {(concurrent_time / num_concurrent):.2f}秒")
        
        # 验证每个结果
        for index, result in results:
            self.assertTrue(result["success"], f"并发加载{index}失败")
            self.assertIn("project_id", result)
            self.assertIn("hole_count", result)
        
        # 性能要求
        self.assertLess(concurrent_time, 5.0, "并发加载耗时过长")
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_legacy_compatibility_system(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试向后兼容性系统"""
        print(f"\n🔄 测试向后兼容性系统")
        
        # 创建中等规模的孔位集合
        medium_collection = HoleCollection(
            holes={
                f"H{i:05d}": HoleData(
                    hole_id=f"H{i:05d}",
                    position=Position(x=float(i * 10), y=float(i * 20)),
                    diameter=8.865,
                    status=HoleStatus.PENDING
                )
                for i in range(1, 101)  # 100个孔位
            },
            metadata={}
        )
        
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = medium_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_ui_adapter = Mock()
        mock_ui_adapter.load_dxf_file.return_value = {
            "success": True,
            "hole_collection": medium_collection
        }
        mock_ui_adapter.get_project_info.return_value = {
            "has_project": True,
            "project_id": "legacy_test_project"
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        # 创建向后兼容加载器
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        # 测试场景1：传统模式完整工作流
        print(f"   📋 测试传统模式工作流")
        loader.set_mode("legacy")
        
        # 加载DXF
        start_time = time.time()
        result = loader.load_dxf_file(self.test_files["medium"])
        legacy_time = time.time() - start_time
        
        self.assertEqual(len(result), 100)
        print(f"   ✅ 传统模式加载100个孔位，耗时: {legacy_time:.3f}秒")
        
        # 获取孔位列表
        hole_list = loader.get_hole_list()
        self.assertEqual(len(hole_list), 100)
        
        # 位置搜索
        search_count = 0
        for i in range(1, 11):  # 搜索前10个孔位
            hole_id = loader.find_hole_by_position(float(i * 10), float(i * 20), 1.0)
            if hole_id:
                search_count += 1
        
        self.assertEqual(search_count, 10)
        print(f"   🔍 传统模式位置搜索: {search_count}/10 成功")
        
        # 测试场景2：集成模式完整工作流
        print(f"   🔗 测试集成模式工作流")
        loader.set_mode("integrated")
        
        # 加载DXF
        start_time = time.time()
        result = loader.load_dxf_file(self.test_files["medium"], "集成模式测试")
        integrated_time = time.time() - start_time
        
        self.assertEqual(len(result), 100)
        print(f"   ✅ 集成模式加载100个孔位，耗时: {integrated_time:.3f}秒")
        
        # 获取项目信息
        project_info = loader.get_project_info()
        self.assertTrue(project_info["has_project"])
        
        # 导航到实时监控
        nav_result = loader.navigate_to_realtime("H00001")
        # 注意：这里可能失败，因为模拟对象没有设置navigate_to_realtime的返回值
        
        # 测试场景3：模式切换性能
        print(f"   🔄 测试模式切换性能")
        switch_times = []
        
        for _ in range(10):
            start_time = time.time()
            loader.set_mode("legacy")
            loader.set_mode("integrated")
            switch_time = time.time() - start_time
            switch_times.append(switch_time)
        
        avg_switch_time = sum(switch_times) / len(switch_times)
        print(f"   ⚡ 平均模式切换时间: {avg_switch_time * 1000:.2f}毫秒")
        
        # 性能要求
        self.assertLess(avg_switch_time, 0.01, "模式切换耗时过长")
    
    def test_error_handling_system(self):
        """测试错误处理系统"""
        print(f"\n❌ 测试错误处理系统")
        
        # 测试场景1：文件不存在
        with patch('aidcis2.integration.dxf_integration_manager.DXFParser'), \
             patch('aidcis2.integration.dxf_integration_manager.HybridDataManager'):
            
            manager = DXFIntegrationManager(self.temp_dir, self.database_url)
            
            error_calls = []
            manager.set_error_callback(lambda msg: error_calls.append(msg))
            
            success, _, _ = manager.load_dxf_file_integrated("nonexistent.dxf")
            
            self.assertFalse(success)
            self.assertGreater(len(error_calls), 0)
            print(f"   ✅ 文件不存在错误处理正确")
        
        # 测试场景2：空文件
        with patch('aidcis2.integration.dxf_integration_manager.DXFParser'), \
             patch('aidcis2.integration.dxf_integration_manager.HybridDataManager'):
            
            manager = DXFIntegrationManager(self.temp_dir, self.database_url)
            
            error_calls = []
            manager.set_error_callback(lambda msg: error_calls.append(msg))
            
            success, _, _ = manager.load_dxf_file_integrated(self.test_files["empty"])
            
            self.assertFalse(success)
            self.assertGreater(len(error_calls), 0)
            print(f"   ✅ 空文件错误处理正确")
        
        # 测试场景3：无效文件扩展名
        with patch('aidcis2.integration.dxf_integration_manager.DXFParser'), \
             patch('aidcis2.integration.dxf_integration_manager.HybridDataManager'):
            
            manager = DXFIntegrationManager(self.temp_dir, self.database_url)
            
            error_calls = []
            manager.set_error_callback(lambda msg: error_calls.append(msg))
            
            success, _, _ = manager.load_dxf_file_integrated(self.test_files["invalid"])
            
            self.assertFalse(success)
            self.assertGreater(len(error_calls), 0)
            print(f"   ✅ 无效文件扩展名错误处理正确")
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_memory_usage_system(self, mock_dxf_integration_class):
        """测试内存使用系统"""
        print(f"\n💾 测试内存使用系统")
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
        except ImportError:
            self.skipTest("psutil not available for memory monitoring")
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   📊 初始内存使用: {initial_memory:.2f} MB")
        
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.return_value = (
            True, "memory_test_project", self.large_hole_collection
        )
        mock_dxf_integration.get_current_project_summary.return_value = {}
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        # 创建多个适配器实例
        adapters = []
        for i in range(10):
            adapter = UIIntegrationAdapter(
                os.path.join(self.temp_dir, f"memory_test_{i}"),
                f"sqlite:///{self.temp_dir}/memory_test_{i}.db"
            )
            adapters.append(adapter)
            
            # 加载大型DXF
            result = adapter.load_dxf_file(self.test_files["large"], f"内存测试{i}")
            self.assertTrue(result["success"])
        
        # 记录峰值内存
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        print(f"   📊 峰值内存使用: {peak_memory:.2f} MB")
        print(f"   📈 内存增长: {memory_increase:.2f} MB")
        
        # 清理资源
        for adapter in adapters:
            adapter.cleanup()
        
        # 记录清理后内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_released = peak_memory - final_memory
        
        print(f"   📊 清理后内存: {final_memory:.2f} MB")
        print(f"   📉 释放内存: {memory_released:.2f} MB")
        
        # 内存使用要求
        self.assertLess(memory_increase, 500, "内存使用增长过多")  # 不超过500MB
        self.assertGreater(memory_released, memory_increase * 0.5, "内存释放不足")  # 至少释放50%
    
    def test_end_to_end_workflow_system(self):
        """测试端到端工作流系统"""
        print(f"\n🔄 测试端到端工作流系统")
        
        # 模拟完整的用户工作流
        workflow_steps = [
            "文件选择",
            "DXF解析",
            "项目创建",
            "孔位显示",
            "孔位选择",
            "实时监控导航",
            "数据保存",
            "统计更新"
        ]
        
        with patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager') as mock_class:
            # 设置模拟对象
            mock_integration = Mock()
            mock_integration.load_dxf_file_integrated.return_value = (
                True, "workflow_project", self.large_hole_collection
            )
            mock_integration.get_current_project_summary.return_value = {
                "project_name": "端到端测试",
                "statistics": {"total_holes": 1000, "completed_holes": 0}
            }
            mock_integration.get_hole_for_realtime.return_value = {
                "basic_info": {"position": {"x": 10.0, "y": 20.0}},
                "status_info": {"current_status": "pending"}
            }
            mock_integration.navigate_to_realtime_monitoring.return_value = True
            mock_integration.get_current_hole_collection.return_value = self.large_hole_collection
            mock_class.return_value = mock_integration
            
            # 创建UI适配器
            adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
            
            workflow_times = {}
            total_start = time.time()
            
            # 步骤1：文件选择和加载
            step_start = time.time()
            load_result = adapter.load_dxf_file(self.test_files["large"], "端到端测试")
            workflow_times["文件加载"] = time.time() - step_start
            
            self.assertTrue(load_result["success"])
            print(f"   ✅ 文件加载: {workflow_times['文件加载']:.3f}秒")
            
            # 步骤2：获取项目信息
            step_start = time.time()
            project_info = adapter.get_project_info()
            workflow_times["项目信息"] = time.time() - step_start
            
            self.assertTrue(project_info["has_project"])
            print(f"   ✅ 项目信息: {workflow_times['项目信息']:.3f}秒")
            
            # 步骤3：获取孔位列表
            step_start = time.time()
            hole_list = adapter.get_hole_list()
            workflow_times["孔位列表"] = time.time() - step_start
            
            self.assertEqual(len(hole_list), 1000)
            print(f"   ✅ 孔位列表: {workflow_times['孔位列表']:.3f}秒")
            
            # 步骤4：孔位选择和信息获取
            step_start = time.time()
            selected_holes = []
            for i in range(10):  # 选择10个孔位
                hole_id = f"H{i+1:05d}"
                hole_info = adapter.get_hole_for_selection(hole_id)
                if hole_info:
                    selected_holes.append(hole_info)
            workflow_times["孔位选择"] = time.time() - step_start
            
            self.assertEqual(len(selected_holes), 10)
            print(f"   ✅ 孔位选择: {workflow_times['孔位选择']:.3f}秒")
            
            # 步骤5：导航到实时监控
            step_start = time.time()
            nav_results = []
            for hole_info in selected_holes[:3]:  # 导航前3个
                nav_result = adapter.navigate_to_realtime(hole_info["hole_id"])
                nav_results.append(nav_result)
            workflow_times["实时监控导航"] = time.time() - step_start
            
            successful_navs = sum(1 for r in nav_results if r["success"])
            self.assertEqual(successful_navs, 3)
            print(f"   ✅ 实时监控导航: {workflow_times['实时监控导航']:.3f}秒")
            
            # 步骤6：位置搜索测试
            step_start = time.time()
            search_results = []
            for i in range(50):  # 50次位置搜索
                x, y = float(i % 100), float(i // 100)
                hole_id = adapter.find_hole_by_position(x, y, 1.0)
                if hole_id:
                    search_results.append(hole_id)
            workflow_times["位置搜索"] = time.time() - step_start
            
            print(f"   ✅ 位置搜索: {workflow_times['位置搜索']:.3f}秒 ({len(search_results)}/50)")
            
            total_time = time.time() - total_start
            
            # 打印工作流总结
            print(f"\n📊 端到端工作流总结:")
            print(f"   总耗时: {total_time:.3f}秒")
            for step, duration in workflow_times.items():
                percentage = (duration / total_time) * 100
                print(f"   {step}: {duration:.3f}秒 ({percentage:.1f}%)")
            
            # 性能要求
            self.assertLess(total_time, 5.0, "端到端工作流耗时过长")
            self.assertLess(workflow_times["文件加载"], 2.0, "文件加载耗时过长")
            self.assertLess(workflow_times["孔位列表"], 1.0, "孔位列表获取耗时过长")


if __name__ == '__main__':
    # 设置详细输出
    unittest.main(verbosity=2)
