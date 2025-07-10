"""
模块集成测试
测试各模块间的集成和协作功能
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from modules.defect_annotation_model import DefectAnnotation, DefectCategory
from modules.image_scanner import ImageScanner, ImageInfo
from modules.yolo_file_manager import YOLOFileManager
from modules.defect_category_manager import DefectCategoryManager
from modules.archive_manager import ArchiveManager


class TestModuleIntegration(unittest.TestCase):
    """模块集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "Data"
        self.archive_dir = Path(self.temp_dir) / "Archive"
        self.config_dir = Path(self.temp_dir) / "config"
        
        # 创建测试数据结构
        self.create_test_data()
        
        # 初始化各模块
        self.image_scanner = ImageScanner(str(self.data_dir))
        self.yolo_manager = YOLOFileManager()
        self.category_manager = DefectCategoryManager(str(self.config_dir / "categories.json"))
        self.archive_manager = ArchiveManager(str(self.data_dir), str(self.archive_dir))
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_data(self):
        """创建测试数据"""
        # 创建孔位目录结构
        holes = ["H00001", "H00002", "H00003"]
        
        for hole_id in holes:
            hole_dir = self.data_dir / hole_id / "BISDM" / "result"
            hole_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建测试图像文件
            for i in range(3):
                image_file = hole_dir / f"image{i+1}.jpg"
                image_file.write_bytes(b"fake image content")
                
    def test_image_scanner_and_yolo_integration(self):
        """测试图像扫描器与YOLO文件管理器集成"""
        # 1. 扫描图像
        success = self.image_scanner.scan_directories()
        self.assertTrue(success)
        
        hole_ids = self.image_scanner.get_hole_ids()
        self.assertGreater(len(hole_ids), 0)
        
        # 2. 为第一个孔位的图像创建标注
        first_hole = hole_ids[0]
        images = self.image_scanner.get_images_for_hole(first_hole)
        self.assertGreater(len(images), 0)
        
        # 3. 创建标注数据
        annotations = [
            DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
            DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15)
        ]
        
        # 4. 保存标注到第一张图像
        first_image = images[0]
        annotation_file = self.yolo_manager.get_annotation_file_path(first_image.file_path)
        
        success = self.yolo_manager.save_annotations(annotations, annotation_file)
        self.assertTrue(success)
        
        # 5. 验证标注文件存在
        self.assertTrue(self.yolo_manager.has_annotations(first_image.file_path))
        
        # 6. 加载并验证标注
        loaded_annotations = self.yolo_manager.load_annotations(annotation_file)
        self.assertEqual(len(loaded_annotations), len(annotations))
        
        # 7. 验证数据一致性
        for original, loaded in zip(annotations, loaded_annotations):
            self.assertEqual(original.defect_class, loaded.defect_class)
            self.assertAlmostEqual(original.x_center, loaded.x_center, places=6)
            self.assertAlmostEqual(original.y_center, loaded.y_center, places=6)
            
    def test_category_manager_and_annotation_integration(self):
        """测试缺陷类别管理器与标注数据集成"""
        # 1. 获取类别信息
        categories = self.category_manager.get_all_categories()
        self.assertGreater(len(categories), 0)
        
        # 2. 使用类别创建标注
        first_category = categories[0]
        annotation = DefectAnnotation(
            first_category.id, 0.4, 0.6, 0.15, 0.2
        )
        
        # 3. 验证类别信息获取
        category_name = self.category_manager.get_category_name(annotation.defect_class)
        category_color = self.category_manager.get_category_color(annotation.defect_class)
        
        self.assertEqual(category_name, first_category.display_name)
        self.assertEqual(category_color, first_category.color)
        
        # 4. 验证类别ID有效性
        self.assertTrue(self.category_manager.validate_category_id(annotation.defect_class))
        
        # 5. 测试UI组件数据
        ui_items = self.category_manager.create_ui_combo_items()
        self.assertGreater(len(ui_items), 0)
        
        # 验证UI项目格式
        for text, value in ui_items:
            self.assertIsInstance(text, str)
            self.assertIsInstance(value, int)
            self.assertIn(" - ", text)
            
    def test_archive_manager_integration(self):
        """测试归档管理器与其他模块集成"""
        # 1. 创建标注数据
        hole_id = "H00001"
        images = self.image_scanner.get_images_for_hole(hole_id)
        
        # 为前两张图像创建标注
        for i, image_info in enumerate(images[:2]):
            annotations = [
                DefectAnnotation(i % 2, 0.5, 0.5, 0.2, 0.3),
                DefectAnnotation((i + 1) % 2, 0.3, 0.7, 0.1, 0.15)
            ]
            
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            self.yolo_manager.save_annotations(annotations, annotation_file)
            
        # 2. 获取有标注的孔位
        annotated_holes = self.archive_manager.get_annotated_holes()
        self.assertIn(hole_id, annotated_holes)
        
        # 3. 获取标注摘要
        summary = self.archive_manager.get_hole_annotation_summary(hole_id)
        
        self.assertEqual(summary['hole_id'], hole_id)
        self.assertEqual(summary['total_images'], len(images))
        self.assertEqual(summary['annotated_images'], 2)
        self.assertGreater(summary['total_annotations'], 0)
        
        # 4. 归档孔位
        success = self.archive_manager.archive_hole(hole_id, "集成测试归档")
        self.assertTrue(success)
        
        # 5. 验证归档记录
        archived_holes = self.archive_manager.get_archived_holes()
        self.assertIn(hole_id, archived_holes)
        
        record = self.archive_manager.get_archive_record(hole_id)
        self.assertIsNotNone(record)
        self.assertEqual(record.notes, "集成测试归档")
        
        # 6. 删除原始数据
        original_path = self.data_dir / hole_id
        shutil.rmtree(original_path)
        
        # 7. 从归档恢复
        success = self.archive_manager.load_archived_hole(hole_id)
        self.assertTrue(success)
        
        # 8. 验证恢复的数据
        restored_images = self.image_scanner.get_images_for_hole(hole_id)
        self.assertEqual(len(restored_images), len(images))
        
        # 验证标注文件也被恢复
        for image_info in restored_images[:2]:
            self.assertTrue(self.yolo_manager.has_annotations(image_info.file_path))
            
    def test_complete_annotation_workflow(self):
        """测试完整的标注工作流"""
        # 1. 扫描图像
        self.image_scanner.scan_directories()
        hole_ids = self.image_scanner.get_hole_ids()
        
        # 2. 选择第一个孔位
        hole_id = hole_ids[0]
        images = self.image_scanner.get_images_for_hole(hole_id)
        
        # 3. 获取可用的缺陷类别
        categories = self.category_manager.get_all_categories(enabled_only=True)
        
        # 4. 为每张图像创建标注
        total_annotations = 0
        for i, image_info in enumerate(images):
            # 使用不同的缺陷类别
            category_id = categories[i % len(categories)].id
            
            annotations = [
                DefectAnnotation(category_id, 0.2 + i * 0.1, 0.3 + i * 0.1, 0.15, 0.2),
                DefectAnnotation(category_id, 0.6 + i * 0.05, 0.7 - i * 0.05, 0.1, 0.12)
            ]
            
            # 保存标注
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            success = self.yolo_manager.save_annotations(annotations, annotation_file)
            self.assertTrue(success)
            
            total_annotations += len(annotations)
            
        # 5. 验证所有标注都已保存
        for image_info in images:
            self.assertTrue(self.yolo_manager.has_annotations(image_info.file_path))
            
        # 6. 获取标注统计
        summary = self.archive_manager.get_hole_annotation_summary(hole_id)
        self.assertEqual(summary['annotated_images'], len(images))
        self.assertEqual(summary['total_annotations'], total_annotations)
        
        # 7. 归档完成的工作
        success = self.archive_manager.archive_hole(hole_id, "完整工作流测试")
        self.assertTrue(success)
        
        # 8. 验证归档统计
        stats = self.archive_manager.get_archive_statistics()
        self.assertEqual(stats['total_archived_holes'], 1)
        self.assertEqual(stats['total_archived_images'], len(images))
        self.assertEqual(stats['total_archived_annotations'], total_annotations)
        
    def test_batch_operations_integration(self):
        """测试批量操作集成"""
        # 1. 扫描所有图像
        self.image_scanner.scan_directories()
        hole_ids = self.image_scanner.get_hole_ids()
        
        # 2. 收集所有图像路径
        all_image_paths = []
        for hole_id in hole_ids:
            images = self.image_scanner.get_images_for_hole(hole_id)
            all_image_paths.extend([img.file_path for img in images])
            
        # 3. 批量创建标注数据
        annotations_dict = {}
        for i, image_path in enumerate(all_image_paths):
            annotations = [
                DefectAnnotation(i % 3, 0.5, 0.5, 0.2, 0.3),
                DefectAnnotation((i + 1) % 3, 0.3, 0.7, 0.1, 0.15)
            ]
            annotations_dict[image_path] = annotations
            
        # 4. 批量保存标注
        save_results = self.yolo_manager.batch_save_annotations(annotations_dict)
        
        # 验证所有保存都成功
        for image_path, success in save_results.items():
            self.assertTrue(success, f"保存失败: {image_path}")
            
        # 5. 批量加载标注
        load_results = self.yolo_manager.batch_load_annotations(all_image_paths)
        
        # 验证加载的数据
        for image_path, loaded_annotations in load_results.items():
            original_annotations = annotations_dict[image_path]
            self.assertEqual(len(loaded_annotations), len(original_annotations))
            
        # 6. 批量归档所有孔位
        for hole_id in hole_ids:
            success = self.archive_manager.archive_hole(hole_id, f"批量归档 {hole_id}")
            self.assertTrue(success)
            
        # 7. 验证批量归档结果
        archived_holes = self.archive_manager.get_archived_holes()
        for hole_id in hole_ids:
            self.assertIn(hole_id, archived_holes)
            
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 1. 测试无效路径处理
        invalid_scanner = ImageScanner("/nonexistent/path")
        success = invalid_scanner.scan_directories()
        self.assertFalse(success)
        
        # 2. 测试无效标注数据
        invalid_annotation = DefectAnnotation(-1, 1.5, 0.5, 0.2, 0.3)  # 无效数据
        self.assertFalse(invalid_annotation.is_valid())
        
        # 3. 测试保存无效标注
        temp_file = self.temp_dir / "invalid_annotations.txt"
        success = self.yolo_manager.save_annotations([invalid_annotation], str(temp_file))
        self.assertTrue(success)  # 保存应该成功，但无效标注会被过滤
        
        # 验证无效标注被过滤
        loaded_annotations = self.yolo_manager.load_annotations(str(temp_file))
        self.assertEqual(len(loaded_annotations), 0)
        
        # 4. 测试归档不存在的孔位
        success = self.archive_manager.archive_hole("H99999", "不存在的孔位")
        self.assertFalse(success)
        
        # 5. 测试加载不存在的归档
        success = self.archive_manager.load_archived_hole("H99999")
        self.assertFalse(success)
        
    def test_data_consistency_integration(self):
        """测试数据一致性集成"""
        # 1. 创建标注数据
        hole_id = "H00002"
        images = self.image_scanner.get_images_for_hole(hole_id)
        
        original_annotations = []
        for image_info in images:
            annotations = [
                DefectAnnotation(0, 0.25, 0.35, 0.18, 0.22),
                DefectAnnotation(1, 0.75, 0.65, 0.12, 0.16)
            ]
            
            # 保存标注
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            self.yolo_manager.save_annotations(annotations, annotation_file)
            original_annotations.extend(annotations)
            
        # 2. 归档数据
        self.archive_manager.archive_hole(hole_id, "数据一致性测试")
        
        # 3. 删除原始数据
        original_path = self.data_dir / hole_id
        shutil.rmtree(original_path)
        
        # 4. 从归档恢复
        self.archive_manager.load_archived_hole(hole_id)
        
        # 5. 重新扫描并加载标注
        self.image_scanner.scan_directories()
        restored_images = self.image_scanner.get_images_for_hole(hole_id)
        
        restored_annotations = []
        for image_info in restored_images:
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            annotations = self.yolo_manager.load_annotations(annotation_file)
            restored_annotations.extend(annotations)
            
        # 6. 验证数据一致性
        self.assertEqual(len(restored_annotations), len(original_annotations))
        
        # 按类别和位置排序进行比较
        original_sorted = sorted(original_annotations, key=lambda x: (x.defect_class, x.x_center, x.y_center))
        restored_sorted = sorted(restored_annotations, key=lambda x: (x.defect_class, x.x_center, x.y_center))
        
        for original, restored in zip(original_sorted, restored_sorted):
            self.assertEqual(original.defect_class, restored.defect_class)
            self.assertAlmostEqual(original.x_center, restored.x_center, places=6)
            self.assertAlmostEqual(original.y_center, restored.y_center, places=6)
            self.assertAlmostEqual(original.width, restored.width, places=6)
            self.assertAlmostEqual(original.height, restored.height, places=6)


class TestCrossModuleCompatibility(unittest.TestCase):
    """跨模块兼容性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_defect_category_compatibility(self):
        """测试缺陷类别在各模块间的兼容性"""
        # 1. 创建类别管理器
        config_file = Path(self.temp_dir) / "categories.json"
        category_manager = DefectCategoryManager(str(config_file))
        
        # 2. 获取所有类别
        categories = category_manager.get_all_categories()
        
        # 3. 使用每个类别创建标注
        annotations = []
        for category in categories:
            annotation = DefectAnnotation(
                category.id, 0.5, 0.5, 0.2, 0.3
            )
            self.assertTrue(annotation.is_valid())
            annotations.append(annotation)
            
        # 4. 保存和加载标注
        annotation_file = Path(self.temp_dir) / "compatibility_test.txt"
        yolo_manager = YOLOFileManager()
        
        success = yolo_manager.save_annotations(annotations, str(annotation_file))
        self.assertTrue(success)
        
        loaded_annotations = yolo_manager.load_annotations(str(annotation_file))
        self.assertEqual(len(loaded_annotations), len(annotations))
        
        # 5. 验证类别信息一致性
        for original, loaded in zip(annotations, loaded_annotations):
            self.assertEqual(original.defect_class, loaded.defect_class)
            
            # 验证类别名称和颜色可以正确获取
            name = category_manager.get_category_name(loaded.defect_class)
            color = category_manager.get_category_color(loaded.defect_class)
            
            self.assertIsInstance(name, str)
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith('#'))
            
    def test_file_path_compatibility(self):
        """测试文件路径在各模块间的兼容性"""
        # 1. 创建测试图像文件
        test_image = Path(self.temp_dir) / "test_image.jpg"
        test_image.write_bytes(b"fake image content")
        
        # 2. 使用YOLOFileManager获取标注文件路径
        yolo_manager = YOLOFileManager()
        annotation_path = yolo_manager.get_annotation_file_path(str(test_image))
        
        # 3. 验证路径格式
        expected_path = str(test_image).replace('.jpg', '.txt')
        self.assertEqual(annotation_path, expected_path)
        
        # 4. 创建和保存标注
        annotations = [DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)]
        success = yolo_manager.save_annotations(annotations, annotation_path)
        self.assertTrue(success)
        
        # 5. 验证文件存在性检查
        self.assertTrue(yolo_manager.has_annotations(str(test_image)))
        
        # 6. 验证文件验证功能
        is_valid, errors = yolo_manager.validate_annotation_file(annotation_path)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
