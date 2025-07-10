#!/usr/bin/env python3
"""
系统测试：优先级3阶段1 - 数据管理系统
System Tests: Priority 3 Phase 1 - Data Management System
"""

import unittest
import tempfile
import shutil
import json
import time
import threading
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.project_manager import ProjectDataManager
from aidcis2.data_management.hole_manager import HoleDataManager
from aidcis2.data_management.data_templates import DataTemplates, DataValidator, DataExporter


class TestPriority3Phase1System(unittest.TestCase):
    """优先级3阶段1系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_system_priority3_")
        self.project_manager = ProjectDataManager(self.temp_dir)
        self.hole_manager = HoleDataManager(self.project_manager)
        self.validator = DataValidator()
        
        # 创建大型测试DXF文件
        self.large_dxf = Path(self.temp_dir) / "large_project.dxf"
        self.large_dxf.write_text("large dummy dxf content for system test")
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_large_scale_project_management(self):
        """测试大规模项目管理"""
        # 创建大型项目
        project_name = "大规模系统测试项目"
        project_id, project_path = self.project_manager.create_project(
            str(self.large_dxf), project_name
        )
        
        # 创建大量孔位（模拟真实项目规模）
        num_holes = 1000
        hole_ids = [f"H{i:05d}" for i in range(1, num_holes + 1)]
        
        print(f"\n创建 {num_holes} 个孔位...")
        start_time = time.time()
        
        created_count = 0
        for i, hole_id in enumerate(hole_ids):
            hole_info = DataTemplates.create_hole_info_template(
                hole_id, {"x": float(i % 100), "y": float(i // 100)}
            )
            
            success = self.hole_manager.create_hole_directory(
                project_id, hole_id, hole_info
            )
            if success:
                created_count += 1
            
            # 每100个孔位报告一次进度
            if (i + 1) % 100 == 0:
                print(f"已创建 {i + 1} 个孔位")
        
        creation_time = time.time() - start_time
        print(f"孔位创建完成，耗时: {creation_time:.2f}秒")
        
        # 验证创建结果
        self.assertEqual(created_count, num_holes)
        
        # 更新项目统计
        self.project_manager.update_project_metadata(
            project_id, {"total_holes": num_holes}
        )
        
        # 验证项目统计性能
        start_time = time.time()
        stats = self.project_manager.get_project_statistics(project_id)
        stats_time = time.time() - start_time
        
        print(f"统计计算耗时: {stats_time:.2f}秒")
        
        self.assertEqual(stats["total_holes"], num_holes)
        self.assertEqual(stats["pending_holes"], num_holes)
        self.assertEqual(stats["completed_holes"], 0)
        
        # 性能要求：统计计算应在合理时间内完成
        self.assertLess(stats_time, 5.0, "统计计算耗时过长")
    
    def test_measurement_data_scalability(self):
        """测试测量数据可扩展性"""
        # 创建项目
        project_id, _ = self.project_manager.create_project(
            str(self.large_dxf), "测量数据可扩展性测试"
        )
        
        # 创建孔位
        hole_id = "H00001"
        hole_info = DataTemplates.create_hole_info_template(
            hole_id, {"x": 10.0, "y": 20.0}
        )
        
        success = self.hole_manager.create_hole_directory(
            project_id, hole_id, hole_info
        )
        self.assertTrue(success)
        
        # 生成大量测量数据
        num_measurements = 10000
        print(f"\n生成 {num_measurements} 条测量数据...")
        
        measurement_data = []
        for i in range(num_measurements):
            measurement_data.append({
                "timestamp": f"2025-01-08T{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}",
                "depth": i * 0.1,
                "diameter": 8.865 + (i % 100) * 0.001,
                "temperature": 25.0 + (i % 50) * 0.1,
                "pressure": 1013.25
            })
        
        # 保存测量数据
        start_time = time.time()
        success = self.hole_manager.save_measurement_data(
            project_id, hole_id, measurement_data, "large_measurement.csv"
        )
        save_time = time.time() - start_time
        
        print(f"数据保存耗时: {save_time:.2f}秒")
        self.assertTrue(success)
        
        # 加载测量数据
        csv_files = self.hole_manager.get_hole_measurements(project_id, hole_id)
        self.assertEqual(len(csv_files), 1)
        
        start_time = time.time()
        loaded_data = self.hole_manager.load_measurement_data(csv_files[0])
        load_time = time.time() - start_time
        
        print(f"数据加载耗时: {load_time:.2f}秒")
        
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), num_measurements)
        
        # 性能要求
        self.assertLess(save_time, 10.0, "数据保存耗时过长")
        self.assertLess(load_time, 5.0, "数据加载耗时过长")
    
    def test_concurrent_project_operations(self):
        """测试并发项目操作"""
        num_projects = 10
        projects_created = []
        creation_errors = []
        
        def create_project(index):
            try:
                # 创建测试DXF文件
                dxf_file = Path(self.temp_dir) / f"concurrent_test_{index}.dxf"
                dxf_file.write_text(f"concurrent test dxf {index}")
                
                # 创建项目
                project_id, project_path = self.project_manager.create_project(
                    str(dxf_file), f"并发测试项目{index}"
                )
                
                # 创建一些孔位
                for i in range(10):
                    hole_id = f"H{i:03d}"
                    hole_info = DataTemplates.create_hole_info_template(
                        hole_id, {"x": float(i), "y": float(index)}
                    )
                    
                    self.hole_manager.create_hole_directory(
                        project_id, hole_id, hole_info
                    )
                
                projects_created.append(project_id)
                
            except Exception as e:
                creation_errors.append(f"项目{index}创建失败: {e}")
        
        # 并发创建项目
        print(f"\n并发创建 {num_projects} 个项目...")
        threads = []
        
        start_time = time.time()
        for i in range(num_projects):
            thread = threading.Thread(target=create_project, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        print(f"并发操作耗时: {concurrent_time:.2f}秒")
        
        # 验证结果
        self.assertEqual(len(creation_errors), 0, f"并发创建错误: {creation_errors}")
        self.assertEqual(len(projects_created), num_projects)
        
        # 验证所有项目都正确创建
        all_projects = self.project_manager.list_projects()
        self.assertEqual(len(all_projects), num_projects)
        
        # 验证每个项目的完整性
        for project_id in projects_created:
            metadata = self.project_manager.get_project_metadata(project_id)
            self.assertIsNotNone(metadata)
            
            stats = self.project_manager.get_project_statistics(project_id)
            self.assertEqual(stats["total_holes"], 10)
    
    def test_data_integrity_under_stress(self):
        """测试压力下的数据完整性"""
        # 创建项目
        project_id, _ = self.project_manager.create_project(
            str(self.large_dxf), "数据完整性压力测试"
        )
        
        # 创建孔位
        hole_id = "H00001"
        hole_info = DataTemplates.create_hole_info_template(
            hole_id, {"x": 10.0, "y": 20.0}
        )
        
        success = self.hole_manager.create_hole_directory(
            project_id, hole_id, hole_info
        )
        self.assertTrue(success)
        
        # 压力测试：频繁状态更新
        status_updates = [
            ("in_progress", "开始测量"),
            ("paused", "暂停测量"),
            ("in_progress", "恢复测量"),
            ("completed", "测量完成"),
            ("error", "发现错误"),
            ("in_progress", "重新测量"),
            ("completed", "最终完成")
        ]
        
        print(f"\n执行 {len(status_updates)} 次状态更新...")
        
        for i, (status, reason) in enumerate(status_updates):
            success = self.hole_manager.update_hole_status(
                project_id, hole_id, status, f"{reason} (第{i+1}次)"
            )
            self.assertTrue(success, f"状态更新失败: {status}")
            
            # 验证状态更新
            current_status = self.hole_manager.get_hole_status(project_id, hole_id)
            self.assertEqual(current_status["current_status"], status)
            self.assertEqual(len(current_status["status_history"]), i + 2)  # +1 for initial, +1 for current
        
        # 验证最终数据完整性
        final_status = self.hole_manager.get_hole_status(project_id, hole_id)
        self.assertEqual(final_status["current_status"], "completed")
        self.assertEqual(len(final_status["status_history"]), len(status_updates) + 1)
        
        # 验证状态历史的完整性
        for i, (expected_status, expected_reason) in enumerate(status_updates):
            history_entry = final_status["status_history"][i + 1]  # +1 to skip initial
            self.assertEqual(history_entry["status"], expected_status)
            self.assertIn(expected_reason, history_entry["reason"])
    
    def test_system_resource_usage(self):
        """测试系统资源使用"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        
        # 记录初始资源使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        print(f"\n初始内存使用: {initial_memory:.2f} MB")
        print(f"初始CPU使用: {initial_cpu:.2f}%")
        
        # 执行资源密集型操作
        num_projects = 5
        holes_per_project = 200
        
        for project_idx in range(num_projects):
            # 创建项目
            dxf_file = Path(self.temp_dir) / f"resource_test_{project_idx}.dxf"
            dxf_file.write_text(f"resource test dxf {project_idx}")
            
            project_id, _ = self.project_manager.create_project(
                str(dxf_file), f"资源测试项目{project_idx}"
            )
            
            # 创建孔位
            for hole_idx in range(holes_per_project):
                hole_id = f"H{hole_idx:05d}"
                hole_info = DataTemplates.create_hole_info_template(
                    hole_id, {"x": float(hole_idx % 20), "y": float(hole_idx // 20)}
                )
                
                self.hole_manager.create_hole_directory(
                    project_id, hole_id, hole_info
                )
                
                # 添加一些测量数据
                if hole_idx % 10 == 0:  # 每10个孔位添加测量数据
                    measurement_data = [
                        {
                            "timestamp": f"2025-01-08T10:{hole_idx//60:02d}:{hole_idx%60:02d}",
                            "depth": j * 1.0,
                            "diameter": 8.865 + j * 0.001
                        }
                        for j in range(100)
                    ]
                    
                    self.hole_manager.save_measurement_data(
                        project_id, hole_id, measurement_data
                    )
        
        # 记录最终资源使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        memory_increase = final_memory - initial_memory
        
        print(f"最终内存使用: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        print(f"最终CPU使用: {final_cpu:.2f}%")
        
        # 资源使用要求
        self.assertLess(memory_increase, 500, "内存使用增长过多")  # 不超过500MB增长
        
        # 验证数据完整性
        all_projects = self.project_manager.list_projects()
        self.assertEqual(len(all_projects), num_projects)
        
        total_holes = 0
        for project in all_projects:
            stats = self.project_manager.get_project_statistics(project["project_id"])
            total_holes += stats["total_holes"]
        
        expected_total_holes = num_projects * holes_per_project
        self.assertEqual(total_holes, expected_total_holes)
    
    def test_data_export_system(self):
        """测试数据导出系统"""
        # 创建完整的测试项目
        project_id, _ = self.project_manager.create_project(
            str(self.large_dxf), "数据导出测试项目"
        )
        
        # 创建孔位并添加测量数据
        hole_ids = [f"H{i:03d}" for i in range(1, 11)]
        
        for hole_id in hole_ids:
            hole_info = DataTemplates.create_hole_info_template(
                hole_id, {"x": float(hole_id[1:3]), "y": 0.0}
            )
            
            self.hole_manager.create_hole_directory(project_id, hole_id, hole_info)
            
            # 添加测量数据
            measurement_data = DataTemplates.create_measurement_data_template()
            self.hole_manager.save_measurement_data(project_id, hole_id, measurement_data)
            
            # 完成测量
            self.hole_manager.update_hole_status(project_id, hole_id, "completed", "测试完成")
        
        # 导出项目摘要
        project_metadata = self.project_manager.get_project_metadata(project_id)
        project_stats = self.project_manager.get_project_statistics(project_id)
        
        project_summary = DataExporter.export_project_summary(project_metadata, project_stats)
        
        # 验证导出数据
        self.assertIn("project_info", project_summary)
        self.assertIn("statistics", project_summary)
        self.assertEqual(project_summary["statistics"]["total_holes"], len(hole_ids))
        self.assertEqual(project_summary["statistics"]["completed_holes"], len(hole_ids))
        
        # 导出孔位报告
        for hole_id in hole_ids[:3]:  # 导出前3个孔位的报告
            hole_info = self.hole_manager.get_hole_info(project_id, hole_id)
            hole_status = self.hole_manager.get_hole_status(project_id, hole_id)
            measurements = self.hole_manager.get_hole_measurements(project_id, hole_id)
            
            hole_report = DataExporter.export_hole_report(hole_info, hole_status, measurements)
            
            # 验证报告数据
            self.assertEqual(hole_report["hole_info"]["hole_id"], hole_id)
            self.assertEqual(hole_report["current_status"], "completed")
            self.assertEqual(hole_report["total_measurements"], 1)
        
        print(f"\n成功导出项目摘要和 {len(hole_ids)} 个孔位报告")


if __name__ == '__main__':
    # 设置详细输出
    unittest.main(verbosity=2)
