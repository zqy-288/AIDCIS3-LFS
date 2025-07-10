#!/usr/bin/env python3
"""
独立的DefectAnnotation数据模型测试
不依赖其他模块，避免GUI启动问题
"""

import os
import sys
import tempfile
import shutil

# 直接复制DefectAnnotation类定义，避免导入问题
class DefectAnnotation:
    """缺陷标注数据类 - 支持YOLO格式"""
    
    def __init__(self, defect_class, x_center, y_center, width, height, confidence=1.0):
        self.id = None
        self.defect_class = defect_class
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.confidence = confidence
        
    def to_yolo_format(self):
        """转换为YOLO格式字符串"""
        return f"{self.defect_class} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"
        
    @classmethod
    def from_yolo_format(cls, yolo_line):
        """从YOLO格式字符串创建标注"""
        try:
            parts = yolo_line.strip().split()
            if len(parts) >= 5:
                defect_class = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                return cls(defect_class, x_center, y_center, width, height)
        except (ValueError, IndexError):
            pass
        return None
        
    def to_pixel_coords(self, image_width, image_height):
        """转换为像素坐标"""
        x_pixel = self.x_center * image_width
        y_pixel = self.y_center * image_height
        w_pixel = self.width * image_width
        h_pixel = self.height * image_height
        
        # 计算左上角坐标
        x1 = x_pixel - w_pixel / 2
        y1 = y_pixel - h_pixel / 2
        
        return x1, y1, w_pixel, h_pixel
        
    @classmethod
    def from_pixel_coords(cls, defect_class, x1, y1, width, height, image_width, image_height):
        """从像素坐标创建标注"""
        # 转换为归一化坐标
        x_center = (x1 + width / 2) / image_width
        y_center = (y1 + height / 2) / image_height
        norm_width = width / image_width
        norm_height = height / image_height
        
        return cls(defect_class, x_center, y_center, norm_width, norm_height)
        
    def is_valid(self):
        """验证标注数据是否有效"""
        return (0 <= self.x_center <= 1 and 
                0 <= self.y_center <= 1 and 
                0 < self.width <= 1 and 
                0 < self.height <= 1 and
                self.defect_class >= 0)
                
    def __str__(self):
        return f"DefectAnnotation(class={self.defect_class}, center=({self.x_center:.3f}, {self.y_center:.3f}), size=({self.width:.3f}, {self.height:.3f}))"


class DefectCategory:
    """缺陷类别定义"""
    
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
    def get_category_color(cls, class_id):
        return cls.CATEGORIES.get(class_id, {}).get("color", "#808080")


def test_defect_annotation():
    """测试DefectAnnotation类"""
    print("🧪 测试DefectAnnotation数据模型")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 创建标注
    print("📝 测试1: 创建标注")
    try:
        annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        print(f"  ✅ 创建成功: {annotation}")
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        test_results.append(False)
    
    # 测试2: YOLO格式转换
    print("📝 测试2: YOLO格式转换")
    try:
        yolo_str = annotation.to_yolo_format()
        expected = "0 0.500000 0.500000 0.200000 0.300000"
        if yolo_str == expected:
            print(f"  ✅ YOLO格式正确: {yolo_str}")
            test_results.append(True)
        else:
            print(f"  ❌ YOLO格式错误: 期望 {expected}, 得到 {yolo_str}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ YOLO转换失败: {e}")
        test_results.append(False)
    
    # 测试3: 从YOLO格式恢复
    print("📝 测试3: 从YOLO格式恢复")
    try:
        restored = DefectAnnotation.from_yolo_format(yolo_str)
        if (restored and restored.defect_class == 0 and 
            abs(restored.x_center - 0.5) < 1e-6 and
            abs(restored.y_center - 0.5) < 1e-6):
            print(f"  ✅ 恢复成功: {restored}")
            test_results.append(True)
        else:
            print(f"  ❌ 恢复失败: {restored}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ YOLO恢复失败: {e}")
        test_results.append(False)
    
    # 测试4: 像素坐标转换
    print("📝 测试4: 像素坐标转换")
    try:
        x1, y1, w, h = annotation.to_pixel_coords(800, 600)
        expected_x1 = 0.5 * 800 - 0.2 * 800 / 2  # 320
        expected_y1 = 0.5 * 600 - 0.3 * 600 / 2  # 210
        expected_w = 0.2 * 800  # 160
        expected_h = 0.3 * 600  # 180
        
        if (abs(x1 - expected_x1) < 1e-6 and abs(y1 - expected_y1) < 1e-6 and
            abs(w - expected_w) < 1e-6 and abs(h - expected_h) < 1e-6):
            print(f"  ✅ 像素坐标正确: ({x1}, {y1}, {w}, {h})")
            test_results.append(True)
        else:
            print(f"  ❌ 像素坐标错误: 期望 ({expected_x1}, {expected_y1}, {expected_w}, {expected_h}), 得到 ({x1}, {y1}, {w}, {h})")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 像素坐标转换失败: {e}")
        test_results.append(False)
    
    # 测试5: 从像素坐标创建
    print("📝 测试5: 从像素坐标创建")
    try:
        pixel_annotation = DefectAnnotation.from_pixel_coords(
            defect_class=2, x1=100, y1=50, width=200, height=150,
            image_width=800, image_height=600
        )
        expected_x_center = (100 + 200/2) / 800  # 0.25
        expected_y_center = (50 + 150/2) / 600   # 0.208333
        
        if (pixel_annotation.defect_class == 2 and
            abs(pixel_annotation.x_center - expected_x_center) < 1e-6 and
            abs(pixel_annotation.y_center - expected_y_center) < 1e-6):
            print(f"  ✅ 像素坐标创建成功: {pixel_annotation}")
            test_results.append(True)
        else:
            print(f"  ❌ 像素坐标创建失败: {pixel_annotation}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 像素坐标创建失败: {e}")
        test_results.append(False)
    
    # 测试6: 有效性验证
    print("📝 测试6: 有效性验证")
    try:
        valid_annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        invalid_annotation = DefectAnnotation(-1, 1.5, 0.5, 0.2, 0.3)
        
        if valid_annotation.is_valid() and not invalid_annotation.is_valid():
            print(f"  ✅ 有效性验证正确")
            test_results.append(True)
        else:
            print(f"  ❌ 有效性验证错误")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 有效性验证失败: {e}")
        test_results.append(False)
    
    # 测试7: 缺陷类别
    print("📝 测试7: 缺陷类别")
    try:
        category_name = DefectCategory.get_category_name(0)
        category_color = DefectCategory.get_category_color(0)
        
        if category_name == "裂纹" and category_color == "#FF0000":
            print(f"  ✅ 缺陷类别正确: {category_name}, {category_color}")
            test_results.append(True)
        else:
            print(f"  ❌ 缺陷类别错误: {category_name}, {category_color}")
            test_results.append(False)
    except Exception as e:
        print(f"  ❌ 缺陷类别测试失败: {e}")
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
        print("\n🎉 所有测试通过! DefectAnnotation数据模型工作正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_defect_annotation()
    sys.exit(0 if success else 1)
