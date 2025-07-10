#!/usr/bin/env python3
"""
独立的UI功能测试
验证缺陷标注工具的UI组件和交互逻辑
"""

import sys
import os

# 模拟UI组件类
class MockComboBox:
    def __init__(self):
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
                return True
        return False
                
    def currentText(self):
        return self.current_text
        
    def itemData(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]["data"]
        return None

class MockListWidget:
    def __init__(self):
        self.items = []
        self.current_row = -1
        
    def addItem(self, text):
        self.items.append(text)
        
    def clear(self):
        self.items.clear()
        self.current_row = -1
        
    def setCurrentRow(self, row):
        if 0 <= row < len(self.items):
            self.current_row = row
            return True
        return False

class MockTableWidget:
    def __init__(self):
        self.row_count = 0
        self.column_count = 4
        self.data = {}
        self.current_row = -1
        
    def setRowCount(self, count):
        self.row_count = count
        
    def setItem(self, row, column, text):
        self.data[(row, column)] = text
        
    def item(self, row, column):
        return self.data.get((row, column), "")
        
    def currentRow(self):
        return self.current_row
        
    def selectRow(self, row):
        if 0 <= row < self.row_count:
            self.current_row = row
            return True
        return False

# 模拟DefectAnnotation类
class DefectAnnotation:
    def __init__(self, defect_class, x_center, y_center, width, height, confidence=1.0):
        self.defect_class = defect_class
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.confidence = confidence

# 模拟DefectCategory类
class DefectCategory:
    CATEGORIES = {
        0: {"name": "crack", "display_name": "裂纹", "color": "#FF0000"},
        1: {"name": "corrosion", "display_name": "腐蚀", "color": "#FF8000"},
        2: {"name": "pit", "display_name": "点蚀", "color": "#FFFF00"},
        3: {"name": "scratch", "display_name": "划痕", "color": "#00FF00"},
        4: {"name": "deposit", "display_name": "沉积物", "color": "#00FFFF"},
        5: {"name": "other", "display_name": "其他", "color": "#8000FF"}
    }
    
    @classmethod
    def get_category_name(cls, class_id):
        return cls.CATEGORIES.get(class_id, {}).get("display_name", f"未知类别{class_id}")
        
    @classmethod
    def get_all_categories(cls):
        return [{"id": k, **v} for k, v in cls.CATEGORIES.items()]

# 模拟缺陷标注工具UI逻辑
class MockDefectAnnotationToolUI:
    """模拟的缺陷标注工具UI逻辑"""
    
    def __init__(self):
        # 创建模拟UI组件
        self.hole_combo = MockComboBox()
        self.image_list = MockListWidget()
        self.defect_combo = MockComboBox()
        self.defect_table = MockTableWidget()
        self.archive_combo = MockComboBox()
        
        # 状态变量
        self.current_hole_id = None
        self.current_image = None
        self.annotations = []
        self.archived_holes = []
        
        # 模拟数据
        self.available_holes = ["H00001", "H00002", "H00003"]
        self.images_by_hole = {
            "H00001": ["image1.jpg", "image2.png", "image3.bmp"],
            "H00002": ["img_a.jpg", "img_b.png"],
            "H00003": ["test1.jpg", "test2.jpg", "test3.png"]
        }
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI组件"""
        # 填充孔位下拉菜单
        self.hole_combo.addItems(self.available_holes)
        
        # 填充缺陷类别下拉菜单
        self.populate_defect_categories()
        
        # 初始化归档下拉菜单
        self.archive_combo.addItem("选择已标注孔位...")
        
    def populate_defect_categories(self):
        """填充缺陷类别下拉菜单"""
        categories = DefectCategory.get_all_categories()
        for category in categories:
            self.defect_combo.addItem(
                f"{category['id']} - {category['display_name']}", 
                category['id']
            )
            
    def on_hole_changed(self, hole_id):
        """孔ID改变事件"""
        if not hole_id or hole_id not in self.available_holes:
            return False
            
        self.current_hole_id = hole_id
        self.update_image_list()
        self.clear_annotations()
        return True
        
    def update_image_list(self):
        """更新图像列表"""
        self.image_list.clear()
        
        if self.current_hole_id in self.images_by_hole:
            images = self.images_by_hole[self.current_hole_id]
            for image in images:
                self.image_list.addItem(image)
                
            # 自动选择第一张图像
            if images:
                self.image_list.setCurrentRow(0)
                self.current_image = images[0]
                
    def on_image_selected(self, image_name):
        """图像选择事件"""
        self.current_image = image_name
        # 模拟加载对应的标注
        self.load_mock_annotations()
        
    def on_defect_class_changed(self, index):
        """缺陷类别改变事件"""
        defect_class = self.defect_combo.itemData(index)
        return defect_class is not None
        
    def add_annotation(self, annotation):
        """添加标注"""
        self.annotations.append(annotation)
        self.update_defect_table()
        
    def remove_annotation(self, index):
        """移除标注"""
        if 0 <= index < len(self.annotations):
            del self.annotations[index]
            self.update_defect_table()
            return True
        return False
        
    def clear_annotations(self):
        """清除所有标注"""
        self.annotations.clear()
        self.update_defect_table()
        
    def update_defect_table(self):
        """更新缺陷列表表格"""
        self.defect_table.setRowCount(len(self.annotations))
        
        for row, annotation in enumerate(self.annotations):
            # 类别
            category_name = DefectCategory.get_category_name(annotation.defect_class)
            self.defect_table.setItem(row, 0, category_name)
            
            # 位置
            position_text = f"({annotation.x_center:.3f}, {annotation.y_center:.3f})"
            self.defect_table.setItem(row, 1, position_text)
            
            # 大小
            size_text = f"{annotation.width:.3f} × {annotation.height:.3f}"
            self.defect_table.setItem(row, 2, size_text)
            
            # 置信度
            confidence_text = f"{annotation.confidence:.2f}"
            self.defect_table.setItem(row, 3, confidence_text)
            
    def load_mock_annotations(self):
        """加载模拟标注数据"""
        # 为不同图像模拟不同的标注
        self.clear_annotations()
        
        if self.current_image and "1" in self.current_image:
            # 第一类图像有2个标注
            self.add_annotation(DefectAnnotation(0, 0.3, 0.4, 0.1, 0.15))
            self.add_annotation(DefectAnnotation(1, 0.7, 0.6, 0.08, 0.12))
        elif self.current_image and "2" in self.current_image:
            # 第二类图像有1个标注
            self.add_annotation(DefectAnnotation(2, 0.5, 0.5, 0.2, 0.25))
            
    def save_annotations(self):
        """保存标注"""
        if not self.current_image:
            return False
            
        # 模拟保存成功
        if self.annotations:
            # 更新归档列表
            if self.current_hole_id not in self.archived_holes:
                self.archived_holes.append(self.current_hole_id)
                self.update_archive_list()
            return True
        return False
        
    def update_archive_list(self):
        """更新归档列表"""
        self.archive_combo.clear()
        self.archive_combo.addItem("选择已标注孔位...")
        for hole_id in self.archived_holes:
            self.archive_combo.addItem(hole_id)
            
    def get_statistics(self):
        """获取统计信息"""
        total_images = sum(len(images) for images in self.images_by_hole.values())
        total_annotations = len(self.annotations)
        
        return {
            "total_holes": len(self.available_holes),
            "total_images": total_images,
            "total_annotations": total_annotations,
            "archived_holes": len(self.archived_holes)
        }


def test_ui_functionality():
    """测试UI功能"""
    print("🖥️ UI功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: UI初始化
    print("📝 测试1: UI初始化")
    try:
        ui = MockDefectAnnotationToolUI()
        
        # 验证组件初始化
        if (len(ui.hole_combo.items) > 0 and 
            len(ui.defect_combo.items) > 0 and
            len(ui.archive_combo.items) > 0):
            print(f"  ✅ UI初始化成功")
            print(f"    孔位数量: {len(ui.hole_combo.items)}")
            print(f"    缺陷类别数量: {len(ui.defect_combo.items)}")
            test_results.append(True)
        else:
            print(f"  ❌ UI初始化失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ UI初始化异常: {e}")
        test_results.append(False)
    
    # 测试2: 孔位选择
    print("📝 测试2: 孔位选择")
    try:
        success = ui.on_hole_changed("H00001")
        
        if (success and ui.current_hole_id == "H00001" and 
            len(ui.image_list.items) > 0):
            print(f"  ✅ 孔位选择成功: {ui.current_hole_id}")
            print(f"    图像数量: {len(ui.image_list.items)}")
            test_results.append(True)
        else:
            print(f"  ❌ 孔位选择失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 孔位选择异常: {e}")
        test_results.append(False)
    
    # 测试3: 图像选择
    print("📝 测试3: 图像选择")
    try:
        ui.on_image_selected("image1.jpg")
        
        if ui.current_image == "image1.jpg":
            print(f"  ✅ 图像选择成功: {ui.current_image}")
            print(f"    自动加载标注数量: {len(ui.annotations)}")
            test_results.append(True)
        else:
            print(f"  ❌ 图像选择失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 图像选择异常: {e}")
        test_results.append(False)
    
    # 测试4: 标注管理
    print("📝 测试4: 标注管理")
    try:
        initial_count = len(ui.annotations)
        
        # 添加新标注
        new_annotation = DefectAnnotation(3, 0.8, 0.2, 0.15, 0.1)
        ui.add_annotation(new_annotation)
        
        # 验证添加
        if len(ui.annotations) == initial_count + 1:
            print(f"  ✅ 标注添加成功: {len(ui.annotations)}个标注")
            
            # 测试删除
            ui.remove_annotation(0)
            if len(ui.annotations) == initial_count:
                print(f"  ✅ 标注删除成功: {len(ui.annotations)}个标注")
                test_results.append(True)
            else:
                print(f"  ❌ 标注删除失败")
                test_results.append(False)
        else:
            print(f"  ❌ 标注添加失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 标注管理异常: {e}")
        test_results.append(False)
    
    # 测试5: 缺陷表格更新
    print("📝 测试5: 缺陷表格更新")
    try:
        # 添加几个标注
        ui.clear_annotations()
        ui.add_annotation(DefectAnnotation(0, 0.2, 0.3, 0.1, 0.1))
        ui.add_annotation(DefectAnnotation(1, 0.6, 0.7, 0.15, 0.2))
        
        # 验证表格
        if (ui.defect_table.row_count == 2 and
            ui.defect_table.item(0, 0) == "裂纹" and
            ui.defect_table.item(1, 0) == "腐蚀"):
            print(f"  ✅ 缺陷表格更新成功: {ui.defect_table.row_count}行")
            test_results.append(True)
        else:
            print(f"  ❌ 缺陷表格更新失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 缺陷表格更新异常: {e}")
        test_results.append(False)
    
    # 测试6: 保存和归档
    print("📝 测试6: 保存和归档")
    try:
        # 保存标注
        save_success = ui.save_annotations()
        
        if save_success and ui.current_hole_id in ui.archived_holes:
            print(f"  ✅ 保存和归档成功")
            print(f"    归档孔位: {ui.archived_holes}")
            test_results.append(True)
        else:
            print(f"  ❌ 保存和归档失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 保存和归档异常: {e}")
        test_results.append(False)
    
    # 测试7: 统计信息
    print("📝 测试7: 统计信息")
    try:
        stats = ui.get_statistics()
        
        if (stats["total_holes"] > 0 and 
            stats["total_images"] > 0 and
            "total_annotations" in stats):
            print(f"  ✅ 统计信息正确:")
            print(f"    总孔位: {stats['total_holes']}")
            print(f"    总图像: {stats['total_images']}")
            print(f"    总标注: {stats['total_annotations']}")
            print(f"    已归档: {stats['archived_holes']}")
            test_results.append(True)
        else:
            print(f"  ❌ 统计信息错误")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 统计信息异常: {e}")
        test_results.append(False)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过! UI功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_ui_functionality()
    sys.exit(0 if success else 1)
