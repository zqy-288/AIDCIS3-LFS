#!/usr/bin/env python3
"""
单元测试：ProjectDataManager
Unit Tests: ProjectDataManager
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.project_manager import ProjectDataManager


class TestProjectDataManager(unittest.TestCase):
    """ProjectDataManager单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_project_manager_")
        self.project_manager = ProjectDataManager(self.temp_dir)
        
        # 创建测试DXF文件
        self.test_dxf = Path(self.temp_dir) / "test.dxf"
        self.test_dxf.write_text("dummy dxf content")
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertEqual(str(self.project_manager.data_root), self.temp_dir)
    
    def test_create_project_success(self):
        """测试成功创建项目"""
        project_name = "测试项目"
        project_id, project_path = self.project_manager.create_project(
            str(self.test_dxf), project_name
        )
        
        # 验证项目ID格式
        self.assertTrue(project_id.startswith("project_test_"))
        self.assertIn(datetime.now().strftime("%Y%m%d"), project_id)
        
        # 验证项目路径
        self.assertTrue(Path(project_path).exists())
        
        # 验证目录结构
        project_dir = Path(project_path)
        self.assertTrue((project_dir / "holes").exists())
        self.assertTrue((project_dir / "metadata.json").exists())
        self.assertTrue((project_dir / "test.dxf").exists())
    
    def test_create_project_metadata(self):
        """测试项目元数据创建"""
        project_name = "元数据测试项目"
        project_id, project_path = self.project_manager.create_project(
            str(self.test_dxf), project_name
        )
        
        # 读取元数据
        metadata_file = Path(project_path) / "metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 验证元数据内容
        self.assertEqual(metadata["project_id"], project_id)
        self.assertEqual(metadata["project_name"], project_name)
        self.assertEqual(metadata["dxf_file"], "test.dxf")
        self.assertEqual(metadata["total_holes"], 0)
        self.assertEqual(metadata["completed_holes"], 0)
        self.assertEqual(metadata["status"], "active")
        self.assertEqual(metadata["version"], "1.0")
        self.assertIn("created_at", metadata)
    
    def test_get_project_path_exists(self):
        """测试获取存在的项目路径"""
        project_id, expected_path = self.project_manager.create_project(
            str(self.test_dxf), "路径测试项目"
        )
        
        actual_path = self.project_manager.get_project_path(project_id)
        self.assertEqual(actual_path, expected_path)
    
    def test_get_project_path_not_exists(self):
        """测试获取不存在的项目路径"""
        result = self.project_manager.get_project_path("nonexistent_project")
        self.assertIsNone(result)
    
    def test_get_project_metadata_exists(self):
        """测试获取存在的项目元数据"""
        project_name = "元数据获取测试"
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), project_name
        )
        
        metadata = self.project_manager.get_project_metadata(project_id)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["project_name"], project_name)
    
    def test_get_project_metadata_not_exists(self):
        """测试获取不存在的项目元数据"""
        result = self.project_manager.get_project_metadata("nonexistent_project")
        self.assertIsNone(result)
    
    def test_update_project_metadata_success(self):
        """测试成功更新项目元数据"""
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), "更新测试项目"
        )
        
        updates = {
            "total_holes": 100,
            "description": "测试描述",
            "custom_field": "自定义值"
        }
        
        success = self.project_manager.update_project_metadata(project_id, updates)
        self.assertTrue(success)
        
        # 验证更新结果
        metadata = self.project_manager.get_project_metadata(project_id)
        self.assertEqual(metadata["total_holes"], 100)
        self.assertEqual(metadata["description"], "测试描述")
        self.assertEqual(metadata["custom_field"], "自定义值")
        self.assertIn("last_updated", metadata)
    
    def test_update_project_metadata_not_exists(self):
        """测试更新不存在的项目元数据"""
        success = self.project_manager.update_project_metadata(
            "nonexistent_project", {"total_holes": 100}
        )
        self.assertFalse(success)
    
    def test_list_projects_empty(self):
        """测试列出空项目列表"""
        projects = self.project_manager.list_projects()
        self.assertEqual(len(projects), 0)
    
    def test_list_projects_multiple(self):
        """测试列出多个项目"""
        # 创建多个项目
        project_names = ["项目1", "项目2", "项目3"]
        created_projects = []

        for name in project_names:
            # 为每个项目创建独立的DXF文件
            test_dxf = Path(self.temp_dir) / f"{name}.dxf"
            test_dxf.write_text(f"dummy dxf content for {name}")

            project_id, _ = self.project_manager.create_project(str(test_dxf), name)
            created_projects.append(project_id)

        # 获取项目列表
        projects = self.project_manager.list_projects()
        self.assertEqual(len(projects), 3)
        
        # 验证项目按创建时间倒序排列
        for i in range(len(projects) - 1):
            self.assertGreaterEqual(
                projects[i]["created_at"], 
                projects[i + 1]["created_at"]
            )
    
    def test_delete_project_exists(self):
        """测试删除存在的项目"""
        project_id, project_path = self.project_manager.create_project(
            str(self.test_dxf), "删除测试项目"
        )
        
        # 确认项目存在
        self.assertTrue(Path(project_path).exists())
        
        # 删除项目
        success = self.project_manager.delete_project(project_id)
        self.assertTrue(success)
        
        # 确认项目已删除
        self.assertFalse(Path(project_path).exists())
    
    def test_delete_project_not_exists(self):
        """测试删除不存在的项目"""
        success = self.project_manager.delete_project("nonexistent_project")
        self.assertFalse(success)
    
    def test_get_holes_directory_exists(self):
        """测试获取存在的孔位目录"""
        project_id, project_path = self.project_manager.create_project(
            str(self.test_dxf), "孔位目录测试"
        )
        
        holes_dir = self.project_manager.get_holes_directory(project_id)
        expected_dir = str(Path(project_path) / "holes")
        self.assertEqual(holes_dir, expected_dir)
    
    def test_get_holes_directory_not_exists(self):
        """测试获取不存在的孔位目录"""
        result = self.project_manager.get_holes_directory("nonexistent_project")
        self.assertIsNone(result)
    
    def test_get_project_statistics_empty(self):
        """测试获取空项目统计"""
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), "统计测试项目"
        )
        
        stats = self.project_manager.get_project_statistics(project_id)
        expected_stats = {
            "total_holes": 0,
            "completed_holes": 0,
            "pending_holes": 0,
            "error_holes": 0,
            "completion_rate": 0.0
        }
        self.assertEqual(stats, expected_stats)


if __name__ == '__main__':
    unittest.main()
