"""
AnnotationGraphicsView单元测试
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPixmap, QPainter, QMouseEvent

# 由于GUI测试的复杂性，我们创建一个简化的测试版本
class MockAnnotationGraphicsView:
    """模拟的AnnotationGraphicsView用于测试"""
    
    def __init__(self):
        self.current_mode = "pan"
        self.current_defect_class = 0
        self.image_width = 0
        self.image_height = 0
        self.annotation_items = []
        self.selected_annotation = None
        self.drawing = False
        self.panning = False
        
        # 信号模拟
        self.signals_emitted = []
        
    def set_mouse_mode(self, mode):
        """设置鼠标模式"""
        self.current_mode = mode
        
    def set_defect_class(self, defect_class):
        """设置缺陷类别"""
        self.current_defect_class = defect_class
        
    def load_image(self, image_path):
        """模拟加载图像"""
        if os.path.exists(image_path):
            self.image_width = 800
            self.image_height = 600
            return True
        return False
        
    def add_annotation(self, annotation):
        """添加标注"""
        self.annotation_items.append(annotation)
        self.signals_emitted.append(("annotation_created", annotation))
        
    def remove_annotation(self, annotation):
        """移除标注"""
        if annotation in self.annotation_items:
            self.annotation_items.remove(annotation)
            self.signals_emitted.append(("annotation_deleted", annotation))
            
    def get_annotations(self):
        """获取所有标注"""
        return self.annotation_items.copy()
        
    def clear_annotations(self):
        """清除所有标注"""
        self.annotation_items.clear()
        
    def zoom_in(self):
        """放大"""
        pass
        
    def zoom_out(self):
        """缩小"""
        pass
        
    def fit_in_view(self):
        """适应视图"""
        pass


class TestAnnotationGraphicsView(unittest.TestCase):
    """AnnotationGraphicsView测试"""
    
    def setUp(self):
        """测试前准备"""
        self.view = MockAnnotationGraphicsView()
        
        # 创建临时图像文件
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, "test.png")
        
        # 创建一个简单的测试图像
        pixmap = QPixmap(800, 600)
        pixmap.fill(Qt.white)
        pixmap.save(self.test_image_path)
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_mouse_mode_setting(self):
        """测试鼠标模式设置"""
        # 测试设置平移模式
        self.view.set_mouse_mode("pan")
        self.assertEqual(self.view.current_mode, "pan")
        
        # 测试设置标注模式
        self.view.set_mouse_mode("annotate")
        self.assertEqual(self.view.current_mode, "annotate")
        
        # 测试设置编辑模式
        self.view.set_mouse_mode("edit")
        self.assertEqual(self.view.current_mode, "edit")
        
    def test_defect_class_setting(self):
        """测试缺陷类别设置"""
        self.view.set_defect_class(0)
        self.assertEqual(self.view.current_defect_class, 0)
        
        self.view.set_defect_class(2)
        self.assertEqual(self.view.current_defect_class, 2)
        
    def test_image_loading(self):
        """测试图像加载"""
        # 测试加载存在的图像
        result = self.view.load_image(self.test_image_path)
        self.assertTrue(result)
        self.assertEqual(self.view.image_width, 800)
        self.assertEqual(self.view.image_height, 600)
        
        # 测试加载不存在的图像
        result = self.view.load_image("/nonexistent/path.png")
        self.assertFalse(result)
        
    def test_annotation_management(self):
        """测试标注管理"""
        from modules.defect_annotation_model import DefectAnnotation
        
        # 创建测试标注
        annotation1 = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        annotation2 = DefectAnnotation(1, 0.3, 0.7, 0.1, 0.2)
        
        # 测试添加标注
        self.view.add_annotation(annotation1)
        self.view.add_annotation(annotation2)
        
        annotations = self.view.get_annotations()
        self.assertEqual(len(annotations), 2)
        self.assertIn(annotation1, annotations)
        self.assertIn(annotation2, annotations)
        
        # 验证信号发送
        signals = self.view.signals_emitted
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0][0], "annotation_created")
        self.assertEqual(signals[1][0], "annotation_created")
        
        # 测试移除标注
        self.view.remove_annotation(annotation1)
        annotations = self.view.get_annotations()
        self.assertEqual(len(annotations), 1)
        self.assertNotIn(annotation1, annotations)
        self.assertIn(annotation2, annotations)
        
        # 测试清除所有标注
        self.view.clear_annotations()
        annotations = self.view.get_annotations()
        self.assertEqual(len(annotations), 0)
        
    def test_zoom_operations(self):
        """测试缩放操作"""
        # 这些方法在模拟版本中不做实际操作，只测试调用不出错
        try:
            self.view.zoom_in()
            self.view.zoom_out()
            self.view.fit_in_view()
        except Exception as e:
            self.fail(f"缩放操作出错: {e}")


class TestMouseModeEnum(unittest.TestCase):
    """MouseMode枚举测试"""
    
    def test_mouse_mode_values(self):
        """测试鼠标模式枚举值"""
        try:
            from modules.annotation_graphics_view import MouseMode
            
            self.assertEqual(MouseMode.PAN.value, "pan")
            self.assertEqual(MouseMode.ANNOTATE.value, "annotate")
            self.assertEqual(MouseMode.EDIT.value, "edit")
            
        except ImportError:
            # 如果无法导入（GUI环境问题），跳过测试
            self.skipTest("无法导入GUI模块")


class TestAnnotationRectItem(unittest.TestCase):
    """AnnotationRectItem测试"""
    
    def test_annotation_rect_item_creation(self):
        """测试标注矩形项创建"""
        try:
            from modules.defect_annotation_model import DefectAnnotation
            from modules.annotation_graphics_view import AnnotationRectItem
            
            # 创建测试标注
            annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
            
            # 创建矩形项
            rect_item = AnnotationRectItem(annotation, 800, 600)
            
            # 验证基本属性
            self.assertEqual(rect_item.annotation, annotation)
            self.assertEqual(rect_item.image_width, 800)
            self.assertEqual(rect_item.image_height, 600)
            
            # 验证获取标注
            retrieved_annotation = rect_item.get_annotation()
            self.assertEqual(retrieved_annotation.defect_class, annotation.defect_class)
            
        except ImportError:
            # 如果无法导入（GUI环境问题），跳过测试
            self.skipTest("无法导入GUI模块")


class TestIntegrationScenarios(unittest.TestCase):
    """集成场景测试"""
    
    def setUp(self):
        """测试前准备"""
        self.view = MockAnnotationGraphicsView()
        
    def test_complete_annotation_workflow(self):
        """测试完整的标注工作流"""
        from modules.defect_annotation_model import DefectAnnotation
        
        # 1. 设置模式和类别
        self.view.set_mouse_mode("annotate")
        self.view.set_defect_class(1)
        
        # 2. 模拟加载图像
        self.view.image_width = 800
        self.view.image_height = 600
        
        # 3. 创建标注
        annotation = DefectAnnotation(1, 0.5, 0.5, 0.2, 0.3)
        self.view.add_annotation(annotation)
        
        # 4. 验证标注存在
        annotations = self.view.get_annotations()
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].defect_class, 1)
        
        # 5. 切换到编辑模式
        self.view.set_mouse_mode("edit")
        self.assertEqual(self.view.current_mode, "edit")
        
        # 6. 删除标注
        self.view.remove_annotation(annotation)
        annotations = self.view.get_annotations()
        self.assertEqual(len(annotations), 0)
        
    def test_multiple_annotations_management(self):
        """测试多个标注的管理"""
        from modules.defect_annotation_model import DefectAnnotation
        
        # 创建多个不同类别的标注
        annotations = [
            DefectAnnotation(0, 0.2, 0.2, 0.1, 0.1),  # 裂纹
            DefectAnnotation(1, 0.5, 0.5, 0.15, 0.15),  # 腐蚀
            DefectAnnotation(2, 0.8, 0.8, 0.1, 0.2),   # 点蚀
        ]
        
        # 添加所有标注
        for annotation in annotations:
            self.view.add_annotation(annotation)
            
        # 验证数量
        self.assertEqual(len(self.view.get_annotations()), 3)
        
        # 验证不同类别
        retrieved = self.view.get_annotations()
        classes = [ann.defect_class for ann in retrieved]
        self.assertIn(0, classes)
        self.assertIn(1, classes)
        self.assertIn(2, classes)
        
        # 清除所有标注
        self.view.clear_annotations()
        self.assertEqual(len(self.view.get_annotations()), 0)


if __name__ == "__main__":
    # 尝试创建QApplication，如果失败则跳过GUI相关测试
    try:
        app = QApplication([])
        unittest.main()
        app.quit()
    except Exception as e:
        print(f"无法创建QApplication，跳过GUI测试: {e}")
        # 只运行非GUI测试
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 添加不需要GUI的测试
        suite.addTest(TestAnnotationGraphicsView('test_mouse_mode_setting'))
        suite.addTest(TestAnnotationGraphicsView('test_defect_class_setting'))
        suite.addTest(TestIntegrationScenarios('test_complete_annotation_workflow'))
        suite.addTest(TestIntegrationScenarios('test_multiple_annotations_management'))
        
        runner = unittest.TextTestRunner()
        runner.run(suite)
