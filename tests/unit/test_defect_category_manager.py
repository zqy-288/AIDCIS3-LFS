"""
缺陷类别管理器单元测试
"""

import unittest
import tempfile
import os
import shutil
import json
from modules.defect_category_manager import DefectCategoryManager, DefectCategoryInfo


class TestDefectCategoryInfo(unittest.TestCase):
    """DefectCategoryInfo测试"""
    
    def test_category_info_creation(self):
        """测试缺陷类别信息创建"""
        category = DefectCategoryInfo(
            id=0,
            name="test_defect",
            display_name="测试缺陷",
            color="#FF0000",
            description="测试用缺陷类别",
            enabled=True,
            priority=1
        )
        
        self.assertEqual(category.id, 0)
        self.assertEqual(category.name, "test_defect")
        self.assertEqual(category.display_name, "测试缺陷")
        self.assertEqual(category.color, "#FF0000")
        self.assertEqual(category.description, "测试用缺陷类别")
        self.assertTrue(category.enabled)
        self.assertEqual(category.priority, 1)
        
    def test_category_info_to_dict(self):
        """测试转换为字典"""
        category = DefectCategoryInfo(
            id=1,
            name="crack",
            display_name="裂纹",
            color="#FF0000"
        )
        
        category_dict = category.to_dict()
        
        self.assertIsInstance(category_dict, dict)
        self.assertEqual(category_dict['id'], 1)
        self.assertEqual(category_dict['name'], "crack")
        self.assertEqual(category_dict['display_name'], "裂纹")
        self.assertEqual(category_dict['color'], "#FF0000")
        
    def test_category_info_from_dict(self):
        """测试从字典创建"""
        data = {
            'id': 2,
            'name': 'corrosion',
            'display_name': '腐蚀',
            'color': '#FF8000',
            'description': '腐蚀缺陷',
            'enabled': True,
            'priority': 2
        }
        
        category = DefectCategoryInfo.from_dict(data)
        
        self.assertEqual(category.id, 2)
        self.assertEqual(category.name, 'corrosion')
        self.assertEqual(category.display_name, '腐蚀')
        self.assertEqual(category.color, '#FF8000')
        self.assertEqual(category.description, '腐蚀缺陷')
        self.assertTrue(category.enabled)
        self.assertEqual(category.priority, 2)


class TestDefectCategoryManager(unittest.TestCase):
    """DefectCategoryManager测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_categories.json")
        
        # 创建管理器
        self.manager = DefectCategoryManager(self.config_file)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_manager_initialization(self):
        """测试管理器初始化"""
        # 验证默认类别已加载
        categories = self.manager.get_all_categories()
        self.assertGreater(len(categories), 0)
        
        # 验证默认类别包含预期的类别
        category_names = [cat.name for cat in categories]
        expected_names = ["crack", "corrosion", "pit", "scratch", "deposit", "other"]
        
        for name in expected_names:
            self.assertIn(name, category_names)
            
    def test_get_category(self):
        """测试获取单个类别"""
        # 获取存在的类别
        category = self.manager.get_category(0)
        self.assertIsNotNone(category)
        self.assertEqual(category.id, 0)
        
        # 获取不存在的类别
        category = self.manager.get_category(999)
        self.assertIsNone(category)
        
    def test_get_all_categories(self):
        """测试获取所有类别"""
        # 获取所有类别
        all_categories = self.manager.get_all_categories()
        self.assertGreater(len(all_categories), 0)
        
        # 获取只启用的类别
        enabled_categories = self.manager.get_all_categories(enabled_only=True)
        self.assertGreaterEqual(len(all_categories), len(enabled_categories))
        
        # 验证排序（按优先级）
        priorities = [cat.priority for cat in enabled_categories]
        self.assertEqual(priorities, sorted(priorities))
        
    def test_get_category_name_and_color(self):
        """测试获取类别名称和颜色"""
        # 获取存在类别的名称和颜色
        name = self.manager.get_category_name(0)
        color = self.manager.get_category_color(0)
        
        self.assertIsInstance(name, str)
        self.assertIsInstance(color, str)
        self.assertTrue(color.startswith('#'))
        
        # 获取不存在类别的名称和颜色
        unknown_name = self.manager.get_category_name(999)
        unknown_color = self.manager.get_category_color(999)
        
        self.assertIn("未知类别", unknown_name)
        self.assertEqual(unknown_color, "#808080")
        
    def test_get_category_by_name(self):
        """测试根据名称查找类别"""
        # 根据英文名称查找
        category = self.manager.get_category_by_name("crack")
        self.assertIsNotNone(category)
        self.assertEqual(category.name, "crack")
        
        # 根据中文名称查找
        category = self.manager.get_category_by_name("裂纹")
        self.assertIsNotNone(category)
        self.assertEqual(category.display_name, "裂纹")
        
        # 查找不存在的名称
        category = self.manager.get_category_by_name("不存在的类别")
        self.assertIsNone(category)
        
    def test_add_category(self):
        """测试添加类别"""
        # 添加新类别
        new_category = DefectCategoryInfo(
            id=100,
            name="new_defect",
            display_name="新缺陷",
            color="#123456"
        )
        
        success = self.manager.add_category(new_category)
        self.assertTrue(success)
        
        # 验证类别已添加
        retrieved = self.manager.get_category(100)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "new_defect")
        
        # 尝试添加重复ID的类别
        duplicate_category = DefectCategoryInfo(
            id=100,
            name="another_defect",
            display_name="另一个缺陷",
            color="#654321"
        )
        
        success = self.manager.add_category(duplicate_category)
        self.assertFalse(success)
        
    def test_update_category(self):
        """测试更新类别"""
        # 更新存在的类别
        success = self.manager.update_category(0, display_name="更新的裂纹", color="#FF1111")
        self.assertTrue(success)
        
        # 验证更新结果
        category = self.manager.get_category(0)
        self.assertEqual(category.display_name, "更新的裂纹")
        self.assertEqual(category.color, "#FF1111")
        
        # 尝试更新不存在的类别
        success = self.manager.update_category(999, display_name="不存在")
        self.assertFalse(success)
        
        # 尝试更新不存在的字段
        success = self.manager.update_category(0, invalid_field="无效")
        self.assertFalse(success)
        
    def test_remove_category(self):
        """测试移除类别"""
        # 添加一个测试类别
        test_category = DefectCategoryInfo(
            id=200,
            name="temp_defect",
            display_name="临时缺陷",
            color="#AAAAAA"
        )
        self.manager.add_category(test_category)
        
        # 验证类别存在
        self.assertIsNotNone(self.manager.get_category(200))
        
        # 移除类别
        success = self.manager.remove_category(200)
        self.assertTrue(success)
        
        # 验证类别已移除
        self.assertIsNone(self.manager.get_category(200))
        
        # 尝试移除不存在的类别
        success = self.manager.remove_category(999)
        self.assertFalse(success)
        
    def test_enable_disable_category(self):
        """测试启用/禁用类别"""
        # 禁用类别
        success = self.manager.enable_category(0, False)
        self.assertTrue(success)
        
        category = self.manager.get_category(0)
        self.assertFalse(category.enabled)
        
        # 重新启用类别
        success = self.manager.enable_category(0, True)
        self.assertTrue(success)
        
        category = self.manager.get_category(0)
        self.assertTrue(category.enabled)
        
    def test_validate_category_id(self):
        """测试验证类别ID"""
        # 验证有效的启用类别
        self.assertTrue(self.manager.validate_category_id(0))
        
        # 禁用类别后验证
        self.manager.enable_category(0, False)
        self.assertFalse(self.manager.validate_category_id(0))
        
        # 验证不存在的类别
        self.assertFalse(self.manager.validate_category_id(999))
        
    def test_get_next_available_id(self):
        """测试获取下一个可用ID"""
        next_id = self.manager.get_next_available_id()
        self.assertIsInstance(next_id, int)
        self.assertGreater(next_id, 0)
        
        # 验证ID确实可用
        self.assertIsNone(self.manager.get_category(next_id))
        
    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.manager.get_statistics()
        
        # 验证统计信息结构
        self.assertIn('total_categories', stats)
        self.assertIn('enabled_categories', stats)
        self.assertIn('disabled_categories', stats)
        self.assertIn('category_list', stats)
        
        # 验证数值
        self.assertGreater(stats['total_categories'], 0)
        self.assertGreaterEqual(stats['enabled_categories'], 0)
        self.assertGreaterEqual(stats['disabled_categories'], 0)
        self.assertEqual(
            stats['total_categories'], 
            stats['enabled_categories'] + stats['disabled_categories']
        )
        
    def test_create_ui_combo_items(self):
        """测试创建UI下拉菜单项目"""
        # 获取所有启用类别的UI项目
        ui_items = self.manager.create_ui_combo_items(enabled_only=True)
        
        self.assertIsInstance(ui_items, list)
        self.assertGreater(len(ui_items), 0)
        
        # 验证项目格式
        for text, value in ui_items:
            self.assertIsInstance(text, str)
            self.assertIsInstance(value, int)
            self.assertIn(" - ", text)  # 格式应该是 "ID - 显示名称"
            
    def test_save_and_load_categories(self):
        """测试保存和加载类别配置"""
        # 添加一个自定义类别
        custom_category = DefectCategoryInfo(
            id=300,
            name="custom_defect",
            display_name="自定义缺陷",
            color="#CUSTOM1",
            description="测试保存加载功能"
        )
        self.manager.add_category(custom_category)
        
        # 保存配置
        success = self.manager.save_categories()
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.config_file))
        
        # 创建新的管理器实例加载配置
        new_manager = DefectCategoryManager(self.config_file)
        
        # 验证自定义类别已加载
        loaded_category = new_manager.get_category(300)
        self.assertIsNotNone(loaded_category)
        self.assertEqual(loaded_category.name, "custom_defect")
        self.assertEqual(loaded_category.display_name, "自定义缺陷")
        self.assertEqual(loaded_category.color, "#CUSTOM1")
        
    def test_export_import_categories(self):
        """测试导出和导入类别配置"""
        export_file = os.path.join(self.temp_dir, "exported_categories.json")
        
        # 导出配置
        success = self.manager.export_categories(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))
        
        # 验证导出文件格式
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn('version', data)
        self.assertIn('categories', data)
        self.assertIsInstance(data['categories'], list)
        
        # 清空当前配置
        self.manager.categories.clear()
        self.assertEqual(len(self.manager.get_all_categories()), 0)
        
        # 导入配置
        success = self.manager.import_categories(export_file)
        self.assertTrue(success)
        
        # 验证配置已恢复
        categories = self.manager.get_all_categories()
        self.assertGreater(len(categories), 0)
        
    def test_reset_to_default(self):
        """测试重置为默认配置"""
        # 添加自定义类别
        custom_category = DefectCategoryInfo(
            id=400,
            name="temp_custom",
            display_name="临时自定义",
            color="#TEMP123"
        )
        self.manager.add_category(custom_category)
        
        # 验证自定义类别存在
        self.assertIsNotNone(self.manager.get_category(400))
        
        # 重置为默认配置
        self.manager.reset_to_default()
        
        # 验证自定义类别已移除，默认类别存在
        self.assertIsNone(self.manager.get_category(400))
        self.assertIsNotNone(self.manager.get_category(0))  # 默认类别应该存在


class TestDefectCategoryManagerIntegration(unittest.TestCase):
    """缺陷类别管理器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "integration_test.json")
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 创建管理器
        manager = DefectCategoryManager(self.config_file)
        
        # 2. 验证默认类别
        initial_count = len(manager.get_all_categories())
        self.assertGreater(initial_count, 0)
        
        # 3. 添加自定义类别
        custom_category = DefectCategoryInfo(
            id=500,
            name="workflow_test",
            display_name="工作流测试",
            color="#WORKFLOW",
            description="完整工作流测试类别"
        )
        
        success = manager.add_category(custom_category)
        self.assertTrue(success)
        
        # 4. 更新类别
        success = manager.update_category(500, priority=10)
        self.assertTrue(success)
        
        # 5. 保存配置
        success = manager.save_categories()
        self.assertTrue(success)
        
        # 6. 重新加载验证
        new_manager = DefectCategoryManager(self.config_file)
        loaded_category = new_manager.get_category(500)
        
        self.assertIsNotNone(loaded_category)
        self.assertEqual(loaded_category.name, "workflow_test")
        self.assertEqual(loaded_category.priority, 10)
        
        # 7. 导出配置
        export_file = os.path.join(self.temp_dir, "workflow_export.json")
        success = new_manager.export_categories(export_file)
        self.assertTrue(success)
        
        # 8. 验证导出内容
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        category_ids = [cat['id'] for cat in data['categories']]
        self.assertIn(500, category_ids)


if __name__ == "__main__":
    unittest.main()
