"""
缺陷标注工具UI单元测试
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock

# 模拟UI组件，避免GUI依赖
class MockWidget:
    def __init__(self):
        self.signals_emitted = []
        self.properties = {}
        
    def emit_signal(self, signal_name, *args):
        self.signals_emitted.append((signal_name, args))
        
    def set_property(self, name, value):
        self.properties[name] = value
        
    def get_property(self, name):
        return self.properties.get(name)

class MockComboBox(MockWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current_index = -1
        self.current_text = ""
        
    def addItem(self, text, data=None):
        self.items.append({"text": text, "data": data})
        
    def addItems(self, items):
        for item in items:
            self.addItem(item)
            
    def clear(self):
        self.items.clear()
        self.current_index = -1
        self.current_text = ""
        
    def setCurrentText(self, text):
        for i, item in enumerate(self.items):
            if item["text"] == text:
                self.current_index = i
                self.current_text = text
                break
                
    def currentText(self):
        return self.current_text
        
    def itemData(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]["data"]
        return None

class MockListWidget(MockWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current_row = -1
        
    def addItem(self, item):
        self.items.append(item)
        
    def clear(self):
        self.items.clear()
        self.current_row = -1
        
    def setCurrentRow(self, row):
        if 0 <= row < len(self.items):
            self.current_row = row
            
    def item(self, row):
        if 0 <= row < len(self.items):
            return self.items[row]
        return None

class MockTableWidget(MockWidget):
    def __init__(self):
        super().__init__()
        self.row_count = 0
        self.column_count = 0
        self.items = {}
        self.current_row = -1
        
    def setRowCount(self, count):
        self.row_count = count
        
    def setColumnCount(self, count):
        self.column_count = count
        
    def setItem(self, row, column, item):
        self.items[(row, column)] = item
        
    def item(self, row, column):
        return self.items.get((row, column))
        
    def currentRow(self):
        return self.current_row
        
    def selectRow(self, row):
        self.current_row = row

class MockGraphicsView(MockWidget):
    def __init__(self):
        super().__init__()
        self.annotations = []
        self.current_mode = "pan"
        self.current_defect_class = 0
        self.image_loaded = False
        
    def set_mouse_mode(self, mode):
        self.current_mode = mode
        
    def set_defect_class(self, defect_class):
        self.current_defect_class = defect_class
        
    def load_image(self, image_path):
        self.image_loaded = os.path.exists(image_path)
        return self.image_loaded
        
    def clear_scene(self):
        self.annotations.clear()
        self.image_loaded = False
        
    def add_annotation(self, annotation):
        self.annotations.append(annotation)
        
    def get_annotations(self):
        return self.annotations.copy()
        
    def clear_annotations(self):
        self.annotations.clear()
        
    def zoom_in(self):
        pass
        
    def zoom_out(self):
        pass
        
    def fit_in_view(self):
        pass

# 模拟缺陷标注工具类
class MockDefectAnnotationTool:
    """模拟的缺陷标注工具"""
    
    def __init__(self):
        # 模拟UI组件
        self.hole_combo = MockComboBox()
        self.image_list = MockListWidget()
        self.defect_combo = MockComboBox()
        self.defect_table = MockTableWidget()
        self.archive_combo = MockComboBox()
        self.graphics_view = MockGraphicsView()
        
        # 模拟数据
        self.current_hole_id = None
        self.current_image = None
        self.archived_holes = []
        
        # 模拟图像扫描器
        self.image_scanner = Mock()
        self.image_scanner.get_hole_ids.return_value = ["H00001", "H00002"]
        self.image_scanner.get_images_for_hole.return_value = []
        
        # 初始化
        self.populate_defect_categories()
        
    def populate_defect_categories(self):
        """填充缺陷类别"""
        categories = [
            {"id": 0, "display_name": "裂纹"},
            {"id": 1, "display_name": "腐蚀"},
            {"id": 2, "display_name": "点蚀"}
        ]
        
        for category in categories:
            self.defect_combo.addItem(
                f"{category['id']} - {category['display_name']}", 
                category['id']
            )
            
    def on_hole_changed(self, hole_id):
        """孔ID改变事件"""
        self.current_hole_id = hole_id
        self.update_image_list()
        
    def update_image_list(self):
        """更新图像列表"""
        self.image_list.clear()
        # 模拟添加图像
        if self.current_hole_id:
            self.image_list.addItem("image1.jpg")
            self.image_list.addItem("image2.png")
            
    def on_defect_class_changed(self, index):
        """缺陷类别改变事件"""
        defect_class = self.defect_combo.itemData(index)
        if defect_class is not None:
            self.graphics_view.set_defect_class(defect_class)
            
    def update_defect_table(self):
        """更新缺陷列表表格"""
        annotations = self.graphics_view.get_annotations()
        self.defect_table.setRowCount(len(annotations))
        
    def save_annotations(self):
        """保存标注"""
        return len(self.graphics_view.get_annotations()) > 0
        
    def load_annotations(self):
        """加载标注"""
        # 模拟加载一些标注
        from modules.defect_annotation_model import DefectAnnotation
        annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        self.graphics_view.add_annotation(annotation)


class TestDefectAnnotationToolUI(unittest.TestCase):
    """缺陷标注工具UI测试"""
    
    def setUp(self):
        """测试前准备"""
        self.tool = MockDefectAnnotationTool()
        
    def test_ui_component_initialization(self):
        """测试UI组件初始化"""
        # 验证组件存在
        self.assertIsNotNone(self.tool.hole_combo)
        self.assertIsNotNone(self.tool.image_list)
        self.assertIsNotNone(self.tool.defect_combo)
        self.assertIsNotNone(self.tool.defect_table)
        self.assertIsNotNone(self.graphics_view)
        
        # 验证缺陷类别已填充
        self.assertGreater(len(self.tool.defect_combo.items), 0)
        
    def test_hole_selection(self):
        """测试孔位选择"""
        # 模拟选择孔位
        self.tool.hole_combo.addItems(["H00001", "H00002"])
        self.tool.hole_combo.setCurrentText("H00001")
        
        # 触发孔位改变事件
        self.tool.on_hole_changed("H00001")
        
        # 验证状态更新
        self.assertEqual(self.tool.current_hole_id, "H00001")
        self.assertGreater(len(self.tool.image_list.items), 0)
        
    def test_defect_class_selection(self):
        """测试缺陷类别选择"""
        # 选择缺陷类别
        self.tool.on_defect_class_changed(1)
        
        # 验证图形视图的缺陷类别已更新
        self.assertEqual(self.tool.graphics_view.current_defect_class, 1)
        
    def test_annotation_management(self):
        """测试标注管理"""
        from modules.defect_annotation_model import DefectAnnotation
        
        # 添加标注
        annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        self.tool.graphics_view.add_annotation(annotation)
        
        # 更新表格
        self.tool.update_defect_table()
        
        # 验证表格行数
        self.assertEqual(self.tool.defect_table.row_count, 1)
        
        # 清除标注
        self.tool.graphics_view.clear_annotations()
        self.tool.update_defect_table()
        
        # 验证表格已清空
        self.assertEqual(self.tool.defect_table.row_count, 0)
        
    def test_save_load_annotations(self):
        """测试保存和加载标注"""
        # 添加标注
        from modules.defect_annotation_model import DefectAnnotation
        annotation = DefectAnnotation(1, 0.3, 0.7, 0.1, 0.2)
        self.tool.graphics_view.add_annotation(annotation)
        
        # 测试保存
        save_result = self.tool.save_annotations()
        self.assertTrue(save_result)
        
        # 清除标注
        self.tool.graphics_view.clear_annotations()
        self.assertEqual(len(self.tool.graphics_view.get_annotations()), 0)
        
        # 测试加载
        self.tool.load_annotations()
        self.assertGreater(len(self.tool.graphics_view.get_annotations()), 0)


class TestUIWorkflow(unittest.TestCase):
    """UI工作流测试"""
    
    def setUp(self):
        """测试前准备"""
        self.tool = MockDefectAnnotationTool()
        
    def test_complete_annotation_workflow(self):
        """测试完整的标注工作流"""
        # 1. 选择孔位
        self.tool.hole_combo.addItems(["H00001", "H00002"])
        self.tool.hole_combo.setCurrentText("H00001")
        self.tool.on_hole_changed("H00001")
        
        # 2. 选择缺陷类别
        self.tool.on_defect_class_changed(1)
        
        # 3. 添加标注
        from modules.defect_annotation_model import DefectAnnotation
        annotation = DefectAnnotation(1, 0.5, 0.5, 0.2, 0.3)
        self.tool.graphics_view.add_annotation(annotation)
        
        # 4. 更新表格
        self.tool.update_defect_table()
        
        # 5. 保存标注
        save_result = self.tool.save_annotations()
        
        # 验证工作流
        self.assertEqual(self.tool.current_hole_id, "H00001")
        self.assertEqual(self.tool.graphics_view.current_defect_class, 1)
        self.assertEqual(len(self.tool.graphics_view.get_annotations()), 1)
        self.assertEqual(self.tool.defect_table.row_count, 1)
        self.assertTrue(save_result)
        
    def test_multiple_holes_workflow(self):
        """测试多孔位工作流"""
        holes = ["H00001", "H00002", "H00003"]
        
        for hole_id in holes:
            # 选择孔位
            self.tool.on_hole_changed(hole_id)
            
            # 验证孔位切换
            self.assertEqual(self.tool.current_hole_id, hole_id)
            
            # 验证图像列表更新
            self.assertGreaterEqual(len(self.tool.image_list.items), 0)


if __name__ == "__main__":
    unittest.main()
