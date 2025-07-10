"""
图像扫描器单元测试
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from modules.image_scanner import ImageScanner, ImageInfo


class TestImageInfo(unittest.TestCase):
    """ImageInfo类测试"""
    
    def test_image_info_creation(self):
        """测试ImageInfo创建"""
        img_info = ImageInfo(
            file_path="/path/to/image.jpg",
            file_name="image.jpg",
            hole_id="H00001",
            file_size=1024,
            extension=".jpg"
        )
        
        self.assertEqual(img_info.file_path, "/path/to/image.jpg")
        self.assertEqual(img_info.file_name, "image.jpg")
        self.assertEqual(img_info.hole_id, "H00001")
        self.assertEqual(img_info.file_size, 1024)
        self.assertEqual(img_info.extension, ".jpg")
        
    def test_image_info_auto_fill(self):
        """测试ImageInfo自动填充"""
        img_info = ImageInfo(
            file_path="/path/to/test.png",
            file_name="",
            hole_id="H00001",
            file_size=2048,
            extension=""
        )
        
        # 应该自动从file_path提取file_name和extension
        self.assertEqual(img_info.file_name, "test.png")
        self.assertEqual(img_info.extension, ".png")


class TestImageScanner(unittest.TestCase):
    """ImageScanner类测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录结构
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = Path(self.temp_dir) / "TestData"
        
        # 创建测试目录结构
        self._create_test_structure()
        
        # 创建扫描器
        self.scanner = ImageScanner(str(self.test_base_path))
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_test_structure(self):
        """创建测试目录结构"""
        # 创建基础目录
        self.test_base_path.mkdir(parents=True, exist_ok=True)
        
        # 创建H00001目录结构
        h1_dir = self.test_base_path / "H00001" / "BISDM" / "result"
        h1_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建H00002目录结构
        h2_dir = self.test_base_path / "H00002" / "BISDM" / "result"
        h2_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建H00003目录但没有BISDM/result
        h3_dir = self.test_base_path / "H00003"
        h3_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建非孔位目录（应该被忽略）
        other_dir = self.test_base_path / "other_folder"
        other_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试图像文件
        test_images = [
            (h1_dir / "image1.jpg", b"fake jpg content 1"),
            (h1_dir / "image2.png", b"fake png content 1"),
            (h1_dir / "subdir" / "image3.bmp", b"fake bmp content"),
            (h2_dir / "image4.jpg", b"fake jpg content 2"),
            (h2_dir / "image5.tiff", b"fake tiff content"),
            (h1_dir / "not_image.txt", b"text file content"),  # 非图像文件
        ]
        
        for img_path, content in test_images:
            img_path.parent.mkdir(parents=True, exist_ok=True)
            img_path.write_bytes(content)
            
    def test_scan_directories_success(self):
        """测试成功扫描目录"""
        result = self.scanner.scan_directories()
        
        self.assertTrue(result)
        self.assertEqual(len(self.scanner.get_hole_ids()), 3)  # H00001, H00002, H00003
        self.assertIn("H00001", self.scanner.get_hole_ids())
        self.assertIn("H00002", self.scanner.get_hole_ids())
        self.assertIn("H00003", self.scanner.get_hole_ids())
        
    def test_scan_nonexistent_directory(self):
        """测试扫描不存在的目录"""
        scanner = ImageScanner("/nonexistent/path")
        result = scanner.scan_directories()
        
        self.assertFalse(result)
        self.assertEqual(len(scanner.get_hole_ids()), 0)
        
    def test_get_images_for_hole(self):
        """测试获取指定孔位的图像"""
        self.scanner.scan_directories()
        
        # H00001应该有3张图像（排除txt文件）
        h1_images = self.scanner.get_images_for_hole("H00001")
        self.assertEqual(len(h1_images), 3)
        
        # 验证图像信息
        image_names = [img.file_name for img in h1_images]
        self.assertIn("image1.jpg", image_names)
        self.assertIn("image2.png", image_names)
        self.assertIn("image3.bmp", image_names)
        self.assertNotIn("not_image.txt", image_names)
        
        # H00002应该有2张图像
        h2_images = self.scanner.get_images_for_hole("H00002")
        self.assertEqual(len(h2_images), 2)
        
        # H00003应该没有图像（没有BISDM/result目录）
        h3_images = self.scanner.get_images_for_hole("H00003")
        self.assertEqual(len(h3_images), 0)
        
    def test_has_images(self):
        """测试检查孔位是否有图像"""
        self.scanner.scan_directories()
        
        self.assertTrue(self.scanner.has_images("H00001"))
        self.assertTrue(self.scanner.has_images("H00002"))
        self.assertFalse(self.scanner.has_images("H00003"))
        self.assertFalse(self.scanner.has_images("H99999"))  # 不存在的孔位
        
    def test_get_image_count(self):
        """测试获取图像数量"""
        self.scanner.scan_directories()
        
        # 总数量
        total_count = self.scanner.get_image_count()
        self.assertEqual(total_count, 5)  # 3 + 2 = 5张图像
        
        # 指定孔位数量
        self.assertEqual(self.scanner.get_image_count("H00001"), 3)
        self.assertEqual(self.scanner.get_image_count("H00002"), 2)
        self.assertEqual(self.scanner.get_image_count("H00003"), 0)
        
    def test_get_statistics(self):
        """测试获取统计信息"""
        self.scanner.scan_directories()
        stats = self.scanner.get_statistics()
        
        # 验证统计信息结构
        self.assertIn('total_holes', stats)
        self.assertIn('total_images', stats)
        self.assertIn('total_size', stats)
        self.assertIn('total_size_mb', stats)
        self.assertIn('extensions', stats)
        self.assertIn('holes', stats)
        
        # 验证数值
        self.assertEqual(stats['total_holes'], 3)
        self.assertEqual(stats['total_images'], 5)
        self.assertGreater(stats['total_size'], 0)
        
        # 验证扩展名统计
        extensions = stats['extensions']
        self.assertIn('.jpg', extensions)
        self.assertIn('.png', extensions)
        self.assertIn('.bmp', extensions)
        self.assertIn('.tiff', extensions)
        
    def test_find_image_by_name(self):
        """测试根据文件名查找图像"""
        self.scanner.scan_directories()
        
        # 在所有图像中查找
        img = self.scanner.find_image_by_name("image1.jpg")
        self.assertIsNotNone(img)
        self.assertEqual(img.hole_id, "H00001")
        self.assertEqual(img.file_name, "image1.jpg")
        
        # 在指定孔位中查找
        img = self.scanner.find_image_by_name("image4.jpg", "H00002")
        self.assertIsNotNone(img)
        self.assertEqual(img.hole_id, "H00002")
        
        # 在错误的孔位中查找
        img = self.scanner.find_image_by_name("image1.jpg", "H00002")
        self.assertIsNone(img)
        
        # 查找不存在的图像
        img = self.scanner.find_image_by_name("nonexistent.jpg")
        self.assertIsNone(img)
        
    def test_validate_image_file(self):
        """测试验证图像文件"""
        self.scanner.scan_directories()
        
        # 获取一个有效的图像文件路径
        h1_images = self.scanner.get_images_for_hole("H00001")
        if h1_images:
            valid_path = h1_images[0].file_path
            self.assertTrue(self.scanner.validate_image_file(valid_path))
        
        # 测试无效路径
        self.assertFalse(self.scanner.validate_image_file("/nonexistent/path.jpg"))
        self.assertFalse(self.scanner.validate_image_file(""))
        
    def test_hole_id_pattern(self):
        """测试孔位ID模式匹配"""
        # 创建额外的测试目录
        valid_holes = ["H001", "H1234", "H00001"]
        invalid_holes = ["h001", "H", "H001a", "hole001", "001"]
        
        for hole_id in valid_holes:
            hole_dir = self.test_base_path / hole_id
            hole_dir.mkdir(exist_ok=True)
            
        for hole_id in invalid_holes:
            hole_dir = self.test_base_path / hole_id
            hole_dir.mkdir(exist_ok=True)
            
        # 重新扫描
        self.scanner.scan_directories()
        found_holes = self.scanner.get_hole_ids()
        
        # 验证只有有效的孔位ID被识别
        for hole_id in valid_holes:
            self.assertIn(hole_id, found_holes)
            
        for hole_id in invalid_holes:
            self.assertNotIn(hole_id, found_holes)
            
    def test_supported_extensions(self):
        """测试支持的图像格式"""
        expected_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.assertEqual(ImageScanner.SUPPORTED_EXTENSIONS, expected_extensions)
        
    def test_get_all_images(self):
        """测试获取所有图像"""
        self.scanner.scan_directories()
        all_images = self.scanner.get_all_images()
        
        self.assertEqual(len(all_images), 5)
        
        # 验证返回的是副本（修改不影响原数据）
        all_images.clear()
        self.assertEqual(len(self.scanner.get_all_images()), 5)


if __name__ == "__main__":
    unittest.main()
