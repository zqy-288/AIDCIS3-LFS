#!/usr/bin/env python3
"""
单元测试：HybridDataManager
Unit Tests: HybridDataManager
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.hybrid_manager import HybridDataManager
from modules.models import DatabaseManager, Workpiece, Hole


class TestHybridDataManager(unittest.TestCase):
    """HybridDataManager单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_hybrid_manager_")
        self.test_db = os.path.join(self.temp_dir, "test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 初始化混合数据管理器
        self.hybrid_manager = HybridDataManager(
            data_root=self.temp_dir,
            database_url=self.database_url
        )
        
        # 创建测试DXF文件
        self.test_dxf = Path(self.temp_dir) / "test.dxf"
        self.test_dxf.write_text("dummy dxf content")
        
        # 测试孔位数据
        self.test_holes_data = [
            {
                "hole_id": "H00001",
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            },
            {
                "hole_id": "H00002",
                "position": {"x": 30.0, "y": 40.0},
                "diameter": 8.870,
                "depth": 950.0,
                "tolerance": 0.1
            }
        ]
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.hybrid_manager.project_manager)
        self.assertIsNotNone(self.hybrid_manager.hole_manager)
        self.assertIsNotNone(self.hybrid_manager.db_manager)
        self.assertIsNotNone(self.hybrid_manager.validator)
    
    def test_create_project_from_dxf_success(self):
        """测试成功从DXF创建项目"""
        project_name = "混合管理器测试项目"
        
        project_id, project_path = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), project_name, self.test_holes_data
        )
        
        # 验证返回值
        self.assertIsNotNone(project_id)
        self.assertIsNotNone(project_path)
        self.assertTrue(project_id.startswith("project_test_"))
        
        # 验证文件系统
        self.assertTrue(Path(project_path).exists())
        holes_dir = Path(project_path) / "holes"
        self.assertTrue(holes_dir.exists())
        
        for hole_data in self.test_holes_data:
            hole_dir = holes_dir / hole_data["hole_id"]
            self.assertTrue(hole_dir.exists())
            self.assertTrue((hole_dir / "BISDM").exists())
            self.assertTrue((hole_dir / "CCIDM").exists())
        
        # 验证数据库
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertIsNotNone(workpiece)
            self.assertEqual(workpiece.name, project_name)
            self.assertEqual(workpiece.hole_count, len(self.test_holes_data))
            
            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            self.assertEqual(len(holes), len(self.test_holes_data))
            
            for hole in holes:
                self.assertIn(hole.hole_id, [h["hole_id"] for h in self.test_holes_data])
                self.assertIsNotNone(hole.file_system_path)
                
        finally:
            self.hybrid_manager.db_manager.close_session(session)
    
    def test_create_project_from_dxf_invalid_data(self):
        """测试使用无效数据创建项目"""
        project_name = "无效数据测试项目"
        invalid_holes_data = [
            {
                "hole_id": "H00001",
                # 缺少position字段
                "diameter": 8.865
            }
        ]
        
        project_id, project_path = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), project_name, invalid_holes_data
        )
        
        # 应该创建项目但跳过无效孔位
        self.assertIsNotNone(project_id)
        self.assertIsNotNone(project_path)
        
        # 验证数据库中没有无效孔位
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertIsNotNone(workpiece)
            
            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            self.assertEqual(len(holes), 0)  # 无效孔位被跳过
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
    
    def test_sync_database_to_filesystem(self):
        """测试数据库到文件系统同步"""
        # 先创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "同步测试项目", self.test_holes_data
        )
        
        # 修改数据库数据
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            workpiece.completed_holes = 1
            workpiece.description = "测试描述"
            
            hole = session.query(Hole).filter_by(workpiece_id=workpiece.id).first()
            hole.status = "completed"
            hole.measurement_count = 10
            
            session.commit()
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 执行同步
        success = self.hybrid_manager.sync_database_to_filesystem(project_id)
        self.assertTrue(success)
        
        # 验证文件系统数据已更新
        metadata = self.hybrid_manager.project_manager.get_project_metadata(project_id)
        self.assertEqual(metadata["completed_holes"], 1)
        self.assertEqual(metadata["description"], "测试描述")
        
        hole_status = self.hybrid_manager.hole_manager.get_hole_status(
            project_id, self.test_holes_data[0]["hole_id"]
        )
        self.assertEqual(hole_status["current_status"], "completed")
    
    def test_sync_filesystem_to_database(self):
        """测试文件系统到数据库同步"""
        # 先创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "反向同步测试项目", self.test_holes_data
        )
        
        # 修改文件系统数据
        updates = {
            "completed_holes": 2,
            "description": "文件系统更新的描述"
        }
        self.hybrid_manager.project_manager.update_project_metadata(project_id, updates)
        
        hole_id = self.test_holes_data[0]["hole_id"]
        self.hybrid_manager.hole_manager.update_hole_status(
            project_id, hole_id, "in_progress", "文件系统更新"
        )
        
        # 执行同步
        success = self.hybrid_manager.sync_filesystem_to_database(project_id)
        self.assertTrue(success)
        
        # 验证数据库数据已更新
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertEqual(workpiece.completed_holes, 2)
            self.assertEqual(workpiece.description, "文件系统更新的描述")
            
            hole = session.query(Hole).filter_by(workpiece_id=workpiece.id, hole_id=hole_id).first()
            self.assertEqual(hole.status, "in_progress")
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
    
    def test_get_hole_data_path(self):
        """测试获取孔位数据路径"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "路径测试项目", self.test_holes_data
        )
        
        hole_id = self.test_holes_data[0]["hole_id"]
        
        # 测试通过项目ID获取路径
        path = self.hybrid_manager.get_hole_data_path(hole_id, project_id)
        self.assertIsNotNone(path)
        self.assertTrue(Path(path).exists())
        self.assertIn(hole_id, path)
        
        # 测试只通过孔位ID获取路径（应该从数据库查找）
        path_without_project = self.hybrid_manager.get_hole_data_path(hole_id)
        self.assertEqual(path, path_without_project)
    
    def test_ensure_data_consistency(self):
        """测试确保数据一致性"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "一致性测试项目", self.test_holes_data
        )
        
        # 分别修改数据库和文件系统
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            workpiece.completed_holes = 1
            session.commit()
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        updates = {"description": "文件系统描述"}
        self.hybrid_manager.project_manager.update_project_metadata(project_id, updates)
        
        # 确保数据一致性
        success = self.hybrid_manager.ensure_data_consistency(project_id)
        self.assertTrue(success)
        
        # 验证两边数据都已同步
        metadata = self.hybrid_manager.project_manager.get_project_metadata(project_id)
        self.assertEqual(metadata["completed_holes"], 1)
        self.assertEqual(metadata["description"], "文件系统描述")
        
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertEqual(workpiece.completed_holes, 1)
            self.assertEqual(workpiece.description, "文件系统描述")
        finally:
            self.hybrid_manager.db_manager.close_session(session)
    
    def test_get_project_summary(self):
        """测试获取项目摘要"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "摘要测试项目", self.test_holes_data
        )
        
        # 获取项目摘要
        summary = self.hybrid_manager.get_project_summary(project_id)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary["project_id"], project_id)
        self.assertEqual(summary["project_name"], "摘要测试项目")
        self.assertEqual(summary["status"], "active")
        self.assertIn("created_at", summary)
        self.assertIn("statistics", summary)
        self.assertIn("data_sources", summary)
        
        # 验证统计信息
        stats = summary["statistics"]
        self.assertEqual(stats["total_holes"], len(self.test_holes_data))
        self.assertEqual(stats["completed_holes"], 0)
        
        # 验证数据源
        sources = summary["data_sources"]
        self.assertTrue(sources["database"])
        self.assertTrue(sources["filesystem"])
    
    def test_get_project_summary_nonexistent(self):
        """测试获取不存在项目的摘要"""
        summary = self.hybrid_manager.get_project_summary("nonexistent_project")
        self.assertIsNone(summary)


if __name__ == '__main__':
    unittest.main()
