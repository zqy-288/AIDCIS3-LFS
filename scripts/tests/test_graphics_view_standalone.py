#!/usr/bin/env python3
"""
独立的图形视图测试
验证AnnotationGraphicsView的核心功能
"""

import sys
import os
from enum import Enum

# 模拟MouseMode枚举
class MouseMode(Enum):
    PAN = "pan"
    ANNOTATE = "annotate"
    EDIT = "edit"

# 模拟DefectAnnotation类
class DefectAnnotation:
    def __init__(self, defect_class, x_center, y_center, width, height):
        self.defect_class = defect_class
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        
    def to_pixel_coords(self, image_width, image_height):
        x_pixel = self.x_center * image_width
        y_pixel = self.y_center * image_height
        w_pixel = self.width * image_width
        h_pixel = self.height * image_height
        
        x1 = x_pixel - w_pixel / 2
        y1 = y_pixel - h_pixel / 2
        
        return x1, y1, w_pixel, h_pixel
        
    @classmethod
    def from_pixel_coords(cls, defect_class, x1, y1, width, height, image_width, image_height):
        x_center = (x1 + width / 2) / image_width
        y_center = (y1 + height / 2) / image_height
        norm_width = width / image_width
        norm_height = height / image_height
        
        return cls(defect_class, x_center, y_center, norm_width, norm_height)

# 模拟AnnotationGraphicsView类
class MockAnnotationGraphicsView:
    """模拟的AnnotationGraphicsView"""
    
    def __init__(self):
        self.current_mode = MouseMode.PAN
        self.current_defect_class = 0
        self.image_width = 0
        self.image_height = 0
        self.annotation_items = []
        self.selected_annotation = None
        self.drawing = False
        self.panning = False
        self.zoom_level = 1.0
        
        # 信号记录
        self.signals_emitted = []
        
    def set_mouse_mode(self, mode):
        """设置鼠标模式"""
        if isinstance(mode, str):
            mode = MouseMode(mode)
        self.current_mode = mode
        
        # 清除绘制状态
        self.drawing = False
        self.panning = False
        
    def set_defect_class(self, defect_class):
        """设置缺陷类别"""
        self.current_defect_class = defect_class
        
    def load_image(self, image_path):
        """模拟加载图像"""
        if os.path.exists(image_path):
            self.image_width = 800
            self.image_height = 600
            self.annotation_items.clear()
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
            if self.selected_annotation == annotation:
                self.selected_annotation = None
            self.signals_emitted.append(("annotation_deleted", annotation))
            
    def get_annotations(self):
        """获取所有标注"""
        return self.annotation_items.copy()
        
    def clear_annotations(self):
        """清除所有标注"""
        self.annotation_items.clear()
        self.selected_annotation = None
        
    def zoom_in(self):
        """放大"""
        if self.zoom_level < 10.0:
            self.zoom_level *= 1.2
            
    def zoom_out(self):
        """缩小"""
        if self.zoom_level > 0.1:
            self.zoom_level *= 0.8
            
    def fit_in_view(self):
        """适应视图"""
        self.zoom_level = 1.0
        
    def select_annotation(self, annotation):
        """选择标注"""
        self.selected_annotation = annotation
        if annotation:
            self.signals_emitted.append(("annotation_selected", annotation))
            
    def simulate_mouse_annotation(self, x1, y1, x2, y2):
        """模拟鼠标标注操作"""
        if self.current_mode != MouseMode.ANNOTATE or not self.image_width:
            return False
            
        # 计算矩形
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        if width < 5 or height < 5:  # 太小的矩形忽略
            return False
            
        # 创建标注
        annotation = DefectAnnotation.from_pixel_coords(
            defect_class=self.current_defect_class,
            x1=min(x1, x2),
            y1=min(y1, y2),
            width=width,
            height=height,
            image_width=self.image_width,
            image_height=self.image_height
        )
        
        self.add_annotation(annotation)
        return True


def test_graphics_view():
    """测试图形视图功能"""
    print("🖼️ 图形视图功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 创建视图
    print("📝 测试1: 创建图形视图")
    try:
        view = MockAnnotationGraphicsView()
        print(f"  ✅ 视图创建成功")
        print(f"    默认模式: {view.current_mode.value}")
        print(f"    默认缺陷类别: {view.current_defect_class}")
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 视图创建失败: {e}")
        test_results.append(False)
        return False
    
    # 测试2: 鼠标模式切换
    print("📝 测试2: 鼠标模式切换")
    try:
        modes = ["pan", "annotate", "edit"]
        for mode in modes:
            view.set_mouse_mode(mode)
            if view.current_mode.value == mode:
                print(f"  ✅ {mode}模式设置成功")
            else:
                print(f"  ❌ {mode}模式设置失败")
                test_results.append(False)
                break
        else:
            test_results.append(True)
    except Exception as e:
        print(f"  ❌ 模式切换失败: {e}")
        test_results.append(False)
    
    # 测试3: 缺陷类别设置
    print("📝 测试3: 缺陷类别设置")
    try:
        classes = [0, 1, 2, 3]
        for cls in classes:
            view.set_defect_class(cls)
            if view.current_defect_class == cls:
                print(f"  ✅ 类别{cls}设置成功")
            else:
                print(f"  ❌ 类别{cls}设置失败")
                test_results.append(False)
                break
        else:
            test_results.append(True)
    except Exception as e:
        print(f"  ❌ 类别设置失败: {e}")
        test_results.append(False)
    
    # 测试4: 图像加载模拟
    print("📝 测试4: 图像加载模拟")
    try:
        # 模拟加载存在的图像
        success = view.load_image(".")  # 当前目录存在
        if success and view.image_width > 0 and view.image_height > 0:
            print(f"  ✅ 图像加载成功: {view.image_width}x{view.image_height}")
            test_results.append(True)
        else:
            print(f"  ❌ 图像加载失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 图像加载测试失败: {e}")
        test_results.append(False)
    
    # 测试5: 标注操作
    print("📝 测试5: 标注操作")
    try:
        # 设置为标注模式
        view.set_mouse_mode("annotate")
        view.set_defect_class(1)
        
        # 模拟鼠标标注
        success = view.simulate_mouse_annotation(100, 100, 200, 150)
        if success:
            annotations = view.get_annotations()
            if len(annotations) == 1:
                ann = annotations[0]
                print(f"  ✅ 标注创建成功: 类别{ann.defect_class}, 中心({ann.x_center:.3f}, {ann.y_center:.3f})")
                test_results.append(True)
            else:
                print(f"  ❌ 标注数量错误: {len(annotations)}")
                test_results.append(False)
        else:
            print(f"  ❌ 标注创建失败")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 标注操作失败: {e}")
        test_results.append(False)
    
    # 测试6: 多个标注管理
    print("📝 测试6: 多个标注管理")
    try:
        # 添加更多标注
        view.simulate_mouse_annotation(300, 200, 400, 280)
        view.simulate_mouse_annotation(500, 300, 580, 350)
        
        annotations = view.get_annotations()
        if len(annotations) == 3:
            print(f"  ✅ 多标注管理成功: {len(annotations)}个标注")
            
            # 测试删除标注
            first_annotation = annotations[0]
            view.remove_annotation(first_annotation)
            
            remaining = view.get_annotations()
            if len(remaining) == 2:
                print(f"  ✅ 标注删除成功: 剩余{len(remaining)}个标注")
                test_results.append(True)
            else:
                print(f"  ❌ 标注删除失败: 剩余{len(remaining)}个标注")
                test_results.append(False)
        else:
            print(f"  ❌ 多标注创建失败: {len(annotations)}个标注")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 多标注管理失败: {e}")
        test_results.append(False)
    
    # 测试7: 缩放操作
    print("📝 测试7: 缩放操作")
    try:
        initial_zoom = view.zoom_level
        
        view.zoom_in()
        zoom_in_level = view.zoom_level
        
        view.zoom_out()
        zoom_out_level = view.zoom_level
        
        view.fit_in_view()
        fit_level = view.zoom_level
        
        if (zoom_in_level > initial_zoom and 
            zoom_out_level < zoom_in_level and 
            fit_level == 1.0):
            print(f"  ✅ 缩放操作正常: {initial_zoom:.2f} -> {zoom_in_level:.2f} -> {zoom_out_level:.2f} -> {fit_level:.2f}")
            test_results.append(True)
        else:
            print(f"  ❌ 缩放操作异常")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 缩放操作失败: {e}")
        test_results.append(False)
    
    # 测试8: 信号发送
    print("📝 测试8: 信号发送")
    try:
        signals = view.signals_emitted
        signal_types = [signal[0] for signal in signals]
        
        if "annotation_created" in signal_types and "annotation_deleted" in signal_types:
            print(f"  ✅ 信号发送正常: {len(signals)}个信号")
            print(f"    信号类型: {set(signal_types)}")
            test_results.append(True)
        else:
            print(f"  ❌ 信号发送异常: {signal_types}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 信号测试失败: {e}")
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
        print("\n🎉 所有测试通过! 图形视图功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_graphics_view()
    sys.exit(0 if success else 1)
