"""
DefectAnnotation数据模型单元测试
"""

import unittest
import tempfile
import os
from modules.defect_annotation_model import DefectAnnotation, DefectCategory, YOLOFileManager


class TestDefectAnnotation(unittest.TestCase):
    """DefectAnnotation类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3, 0.9)
        
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.annotation.defect_class, 0)
        self.assertEqual(self.annotation.x_center, 0.5)
        self.assertEqual(self.annotation.y_center, 0.5)
        self.assertEqual(self.annotation.width, 0.2)
        self.assertEqual(self.annotation.height, 0.3)
        self.assertEqual(self.annotation.confidence, 0.9)
        
    def test_yolo_format_conversion(self):
        """测试YOLO格式转换"""
        yolo_str = self.annotation.to_yolo_format()
        expected = "0 0.500000 0.500000 0.200000 0.300000"
        self.assertEqual(yolo_str, expected)
        
    def test_from_yolo_format(self):
        """测试从YOLO格式创建"""
        yolo_str = "1 0.3 0.7 0.4 0.2"
        annotation = DefectAnnotation.from_yolo_format(yolo_str)
        
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.defect_class, 1)
        self.assertAlmostEqual(annotation.x_center, 0.3)
        self.assertAlmostEqual(annotation.y_center, 0.7)
        self.assertAlmostEqual(annotation.width, 0.4)
        self.assertAlmostEqual(annotation.height, 0.2)
        
    def test_from_yolo_format_invalid(self):
        """测试无效YOLO格式"""
        invalid_formats = [
            "",
            "invalid",
            "0 0.5",  # 参数不足
            "a 0.5 0.5 0.2 0.3",  # 非数字
        ]
        
        for invalid_format in invalid_formats:
            annotation = DefectAnnotation.from_yolo_format(invalid_format)
            self.assertIsNone(annotation, f"应该返回None: {invalid_format}")
            
    def test_pixel_coords_conversion(self):
        """测试像素坐标转换"""
        image_width, image_height = 800, 600
        x1, y1, w, h = self.annotation.to_pixel_coords(image_width, image_height)
        
        # 验证转换结果
        expected_x1 = 0.5 * 800 - 0.2 * 800 / 2  # 320
        expected_y1 = 0.5 * 600 - 0.3 * 600 / 2  # 210
        expected_w = 0.2 * 800  # 160
        expected_h = 0.3 * 600  # 180
        
        self.assertAlmostEqual(x1, expected_x1)
        self.assertAlmostEqual(y1, expected_y1)
        self.assertAlmostEqual(w, expected_w)
        self.assertAlmostEqual(h, expected_h)
        
    def test_from_pixel_coords(self):
        """测试从像素坐标创建"""
        annotation = DefectAnnotation.from_pixel_coords(
            defect_class=2,
            x1=100, y1=50,
            width=200, height=150,
            image_width=800, image_height=600
        )
        
        # 验证归一化坐标
        expected_x_center = (100 + 200/2) / 800  # 0.25
        expected_y_center = (50 + 150/2) / 600   # 0.208333
        expected_width = 200 / 800               # 0.25
        expected_height = 150 / 600              # 0.25
        
        self.assertEqual(annotation.defect_class, 2)
        self.assertAlmostEqual(annotation.x_center, expected_x_center)
        self.assertAlmostEqual(annotation.y_center, expected_y_center)
        self.assertAlmostEqual(annotation.width, expected_width)
        self.assertAlmostEqual(annotation.height, expected_height)
        
    def test_is_valid(self):
        """测试有效性验证"""
        # 有效标注
        valid_annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        self.assertTrue(valid_annotation.is_valid())
        
        # 无效标注
        invalid_annotations = [
            DefectAnnotation(-1, 0.5, 0.5, 0.2, 0.3),  # 负类别
            DefectAnnotation(0, 1.5, 0.5, 0.2, 0.3),   # x_center > 1
            DefectAnnotation(0, 0.5, -0.1, 0.2, 0.3),  # y_center < 0
            DefectAnnotation(0, 0.5, 0.5, 0, 0.3),     # width = 0
            DefectAnnotation(0, 0.5, 0.5, 0.2, 1.5),   # height > 1
        ]
        
        for invalid_annotation in invalid_annotations:
            self.assertFalse(invalid_annotation.is_valid())


class TestDefectCategory(unittest.TestCase):
    """DefectCategory类测试"""
    
    def test_get_category_name(self):
        """测试获取类别名称"""
        self.assertEqual(DefectCategory.get_category_name(0), "裂纹")
        self.assertEqual(DefectCategory.get_category_name(1), "腐蚀")
        self.assertEqual(DefectCategory.get_category_name(999), "未知类别999")
        
    def test_get_category_color(self):
        """测试获取类别颜色"""
        self.assertEqual(DefectCategory.get_category_color(0), "#FF0000")
        self.assertEqual(DefectCategory.get_category_color(1), "#FF8000")
        self.assertEqual(DefectCategory.get_category_color(999), "#808080")
        
    def test_get_all_categories(self):
        """测试获取所有类别"""
        categories = DefectCategory.get_all_categories()
        self.assertIsInstance(categories, list)
        self.assertGreater(len(categories), 0)
        
        # 验证第一个类别的结构
        first_category = categories[0]
        self.assertIn("id", first_category)
        self.assertIn("name", first_category)
        self.assertIn("display_name", first_category)
        self.assertIn("color", first_category)


class TestYOLOFileManager(unittest.TestCase):
    """YOLOFileManager类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_annotations = [
            DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
            DefectAnnotation(1, 0.3, 0.7, 0.4, 0.2),
        ]
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_save_and_load_annotations(self):
        """测试保存和加载标注"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        
        # 保存标注
        success = YOLOFileManager.save_annotations(self.test_annotations, file_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(file_path))
        
        # 加载标注
        loaded_annotations = YOLOFileManager.load_annotations(file_path)
        self.assertEqual(len(loaded_annotations), 2)
        
        # 验证第一个标注
        first = loaded_annotations[0]
        self.assertEqual(first.defect_class, 0)
        self.assertAlmostEqual(first.x_center, 0.5)
        self.assertAlmostEqual(first.y_center, 0.5)
        
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        annotations = YOLOFileManager.load_annotations("nonexistent.txt")
        self.assertEqual(len(annotations), 0)
        
    def test_get_annotation_file_path(self):
        """测试获取标注文件路径"""
        image_path = "/path/to/image.jpg"
        annotation_path = YOLOFileManager.get_annotation_file_path(image_path)
        self.assertEqual(annotation_path, "/path/to/image.txt")
        
    def test_has_annotations(self):
        """测试检查标注文件存在性"""
        # 创建测试文件
        image_path = os.path.join(self.temp_dir, "test.jpg")
        annotation_path = os.path.join(self.temp_dir, "test.txt")
        
        # 文件不存在时
        self.assertFalse(YOLOFileManager.has_annotations(image_path))
        
        # 创建标注文件
        with open(annotation_path, 'w') as f:
            f.write("0 0.5 0.5 0.2 0.3\n")
            
        # 文件存在时
        self.assertTrue(YOLOFileManager.has_annotations(image_path))


if __name__ == "__main__":
    unittest.main()
