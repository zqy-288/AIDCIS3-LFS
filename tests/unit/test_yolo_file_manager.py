"""
YOLO文件管理器单元测试
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from modules.yolo_file_manager import YOLOFileManager
from modules.defect_annotation_model import DefectAnnotation


class TestYOLOFileManager(unittest.TestCase):
    """YOLO文件管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.manager = YOLOFileManager(self.temp_dir)
        
        # 创建测试数据
        self.test_annotations = [
            DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
            DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15),
            DefectAnnotation(2, 0.8, 0.2, 0.12, 0.25)
        ]
        
        # 创建测试文件结构
        self.create_test_structure()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_structure(self):
        """创建测试目录结构"""
        # 创建测试目录
        test_dirs = [
            "H00001/BISDM/result",
            "H00002/BISDM/result"
        ]
        
        for dir_path in test_dirs:
            full_path = Path(self.temp_dir) / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
        # 创建测试图像文件
        test_images = [
            "H00001/BISDM/result/image1.jpg",
            "H00001/BISDM/result/image2.png",
            "H00002/BISDM/result/image3.jpg"
        ]
        
        for image_path in test_images:
            full_path = Path(self.temp_dir) / image_path
            full_path.write_bytes(b"fake image content")
            
    def test_save_and_load_annotations(self):
        """测试保存和加载标注"""
        test_file = os.path.join(self.temp_dir, "test_annotations.txt")
        
        # 测试保存
        success = YOLOFileManager.save_annotations(self.test_annotations, test_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(test_file))
        
        # 测试加载
        loaded_annotations = YOLOFileManager.load_annotations(test_file)
        self.assertEqual(len(loaded_annotations), len(self.test_annotations))
        
        # 验证数据一致性
        for original, loaded in zip(self.test_annotations, loaded_annotations):
            self.assertEqual(original.defect_class, loaded.defect_class)
            self.assertAlmostEqual(original.x_center, loaded.x_center, places=6)
            self.assertAlmostEqual(original.y_center, loaded.y_center, places=6)
            self.assertAlmostEqual(original.width, loaded.width, places=6)
            self.assertAlmostEqual(original.height, loaded.height, places=6)
            
    def test_get_annotation_file_path(self):
        """测试获取标注文件路径"""
        image_path = "/path/to/image.jpg"
        expected_path = "/path/to/image.txt"
        
        result_path = YOLOFileManager.get_annotation_file_path(image_path)
        self.assertEqual(result_path, expected_path)
        
    def test_has_annotations(self):
        """测试检查标注文件存在性"""
        # 创建测试图像和标注文件
        image_path = os.path.join(self.temp_dir, "test_image.jpg")
        annotation_path = os.path.join(self.temp_dir, "test_image.txt")
        
        # 创建图像文件
        with open(image_path, 'w') as f:
            f.write("fake image")
            
        # 测试没有标注文件的情况
        self.assertFalse(YOLOFileManager.has_annotations(image_path))
        
        # 创建空标注文件
        with open(annotation_path, 'w') as f:
            pass
            
        # 空文件应该返回False
        self.assertFalse(YOLOFileManager.has_annotations(image_path))
        
        # 创建有内容的标注文件
        YOLOFileManager.save_annotations([self.test_annotations[0]], annotation_path)
        
        # 有内容的文件应该返回True
        self.assertTrue(YOLOFileManager.has_annotations(image_path))
        
    def test_validate_annotation_file(self):
        """测试标注文件验证"""
        # 测试有效文件
        valid_file = os.path.join(self.temp_dir, "valid.txt")
        YOLOFileManager.save_annotations(self.test_annotations, valid_file)
        
        is_valid, errors = YOLOFileManager.validate_annotation_file(valid_file)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 测试无效文件
        invalid_file = os.path.join(self.temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("0 0.5 0.5\n")  # 缺少字段
            f.write("invalid line\n")  # 格式错误
            f.write("0 1.5 0.5 0.2 0.3\n")  # 数值超出范围
            
        is_valid, errors = YOLOFileManager.validate_annotation_file(invalid_file)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
    def test_batch_operations(self):
        """测试批量操作"""
        # 准备测试数据
        image_paths = [
            os.path.join(self.temp_dir, "image1.jpg"),
            os.path.join(self.temp_dir, "image2.jpg")
        ]
        
        annotations_dict = {
            image_paths[0]: [self.test_annotations[0]],
            image_paths[1]: [self.test_annotations[1], self.test_annotations[2]]
        }
        
        # 测试批量保存
        save_results = self.manager.batch_save_annotations(annotations_dict)
        
        for image_path in image_paths:
            self.assertTrue(save_results[image_path])
            
        # 测试批量加载
        load_results = self.manager.batch_load_annotations(image_paths)
        
        self.assertEqual(len(load_results[image_paths[0]]), 1)
        self.assertEqual(len(load_results[image_paths[1]]), 2)
        
    def test_find_annotation_files(self):
        """测试查找标注文件"""
        # 创建一些标注文件
        annotation_files = [
            "test1.txt",
            "subdir/test2.txt",
            "subdir/deep/test3.txt"
        ]
        
        for annotation_file in annotation_files:
            full_path = Path(self.temp_dir) / annotation_file
            full_path.parent.mkdir(parents=True, exist_ok=True)
            YOLOFileManager.save_annotations([self.test_annotations[0]], str(full_path))
            
        # 查找标注文件
        found_files = self.manager.find_annotation_files(self.temp_dir)
        
        # 验证找到的文件数量
        self.assertEqual(len(found_files), len(annotation_files))
        
        # 验证文件路径
        for annotation_file in annotation_files:
            expected_path = str(Path(self.temp_dir) / annotation_file)
            self.assertIn(expected_path, found_files)
            
    def test_find_orphaned_annotations(self):
        """测试查找孤立标注文件"""
        # 创建有对应图像的标注文件
        image_with_annotation = Path(self.temp_dir) / "with_image.jpg"
        annotation_with_image = Path(self.temp_dir) / "with_image.txt"
        
        image_with_annotation.write_bytes(b"fake image")
        YOLOFileManager.save_annotations([self.test_annotations[0]], str(annotation_with_image))
        
        # 创建没有对应图像的标注文件
        orphaned_annotation = Path(self.temp_dir) / "orphaned.txt"
        YOLOFileManager.save_annotations([self.test_annotations[1]], str(orphaned_annotation))
        
        # 查找孤立文件
        orphaned_files = self.manager.find_orphaned_annotations(self.temp_dir)
        
        # 验证结果
        self.assertEqual(len(orphaned_files), 1)
        self.assertIn(str(orphaned_annotation), orphaned_files)
        self.assertNotIn(str(annotation_with_image), orphaned_files)
        
    def test_find_unannotated_images(self):
        """测试查找未标注图像"""
        # 创建有标注的图像
        annotated_image = Path(self.temp_dir) / "annotated.jpg"
        annotation_file = Path(self.temp_dir) / "annotated.txt"
        
        annotated_image.write_bytes(b"fake image")
        YOLOFileManager.save_annotations([self.test_annotations[0]], str(annotation_file))
        
        # 创建没有标注的图像
        unannotated_image = Path(self.temp_dir) / "unannotated.jpg"
        unannotated_image.write_bytes(b"fake image")
        
        # 查找未标注图像
        unannotated_images = self.manager.find_unannotated_images(self.temp_dir)
        
        # 验证结果
        self.assertIn(str(unannotated_image), unannotated_images)
        self.assertNotIn(str(annotated_image), unannotated_images)
        
    def test_get_annotation_statistics(self):
        """测试获取标注统计"""
        # 创建测试数据
        test_files = [
            ("image1.jpg", "image1.txt", [self.test_annotations[0]]),
            ("image2.jpg", "image2.txt", [self.test_annotations[1], self.test_annotations[2]])
        ]
        
        for image_name, annotation_name, annotations in test_files:
            image_path = Path(self.temp_dir) / image_name
            annotation_path = Path(self.temp_dir) / annotation_name
            
            image_path.write_bytes(b"fake image")
            YOLOFileManager.save_annotations(annotations, str(annotation_path))
            
        # 获取统计信息
        stats = self.manager.get_annotation_statistics(self.temp_dir)
        
        # 验证统计结果
        self.assertEqual(stats['total_annotation_files'], 2)
        self.assertEqual(stats['total_annotations'], 3)
        self.assertEqual(stats['valid_files'], 2)
        self.assertEqual(stats['invalid_files'], 0)
        
        # 验证类别分布
        expected_class_distribution = {0: 1, 1: 1, 2: 1}
        self.assertEqual(stats['annotations_by_class'], expected_class_distribution)
        
    def test_backup_annotations(self):
        """测试备份标注文件"""
        # 创建源标注文件
        source_dir = Path(self.temp_dir) / "source"
        backup_dir = Path(self.temp_dir) / "backup"
        
        source_dir.mkdir(exist_ok=True)
        
        # 创建测试标注文件
        test_annotation = source_dir / "test.txt"
        YOLOFileManager.save_annotations([self.test_annotations[0]], str(test_annotation))
        
        # 执行备份
        success = self.manager.backup_annotations(str(source_dir), str(backup_dir))
        
        # 验证备份结果
        self.assertTrue(success)
        
        backup_file = backup_dir / "test.txt"
        self.assertTrue(backup_file.exists())
        
        # 验证备份文件内容
        original_annotations = YOLOFileManager.load_annotations(str(test_annotation))
        backup_annotations = YOLOFileManager.load_annotations(str(backup_file))
        
        self.assertEqual(len(original_annotations), len(backup_annotations))


class TestYOLOFileManagerIntegration(unittest.TestCase):
    """YOLO文件管理器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = YOLOFileManager(self.temp_dir)
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 1. 创建图像文件
        image_path = Path(self.temp_dir) / "test_image.jpg"
        image_path.write_bytes(b"fake image content")
        
        # 2. 创建标注
        annotations = [
            DefectAnnotation(0, 0.2, 0.3, 0.1, 0.15),
            DefectAnnotation(1, 0.7, 0.8, 0.12, 0.18)
        ]
        
        # 3. 保存标注
        annotation_path = YOLOFileManager.get_annotation_file_path(str(image_path))
        success = YOLOFileManager.save_annotations(annotations, annotation_path)
        self.assertTrue(success)
        
        # 4. 验证文件存在
        self.assertTrue(YOLOFileManager.has_annotations(str(image_path)))
        
        # 5. 加载标注
        loaded_annotations = YOLOFileManager.load_annotations(annotation_path)
        self.assertEqual(len(loaded_annotations), 2)
        
        # 6. 验证标注文件
        is_valid, errors = YOLOFileManager.validate_annotation_file(annotation_path)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 7. 获取统计信息
        stats = self.manager.get_annotation_statistics(self.temp_dir)
        self.assertEqual(stats['total_annotations'], 2)
        self.assertEqual(stats['valid_files'], 1)


if __name__ == "__main__":
    unittest.main()
