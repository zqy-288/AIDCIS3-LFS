#!/usr/bin/env python3
"""
独立的YOLO文件IO测试
验证YOLO格式文件的读写、验证和管理功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 模拟DefectAnnotation类
class DefectAnnotation:
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
        
    def is_valid(self):
        """验证标注数据是否有效"""
        return (0 <= self.x_center <= 1 and 
                0 <= self.y_center <= 1 and 
                0 < self.width <= 1 and 
                0 < self.height <= 1 and
                self.defect_class >= 0)
                
    def __str__(self):
        return f"DefectAnnotation(class={self.defect_class}, center=({self.x_center:.3f}, {self.y_center:.3f}), size=({self.width:.3f}, {self.height:.3f}))"

# 模拟YOLOFileManager类
class MockYOLOFileManager:
    """模拟的YOLO文件管理器"""
    
    SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def __init__(self, base_path="Data"):
        self.base_path = Path(base_path)
        
    @staticmethod
    def save_annotations(annotations, file_path):
        """保存标注到YOLO格式文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            valid_annotations = [ann for ann in annotations if ann.is_valid()]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# YOLO format annotations\n")
                f.write(f"# Total annotations: {len(valid_annotations)}\n")
                f.write(f"# Format: class_id x_center y_center width height\n")
                f.write(f"#\n")
                
                for annotation in valid_annotations:
                    f.write(annotation.to_yolo_format() + '\n')
                    
            return True
            
        except Exception as e:
            print(f"保存标注文件失败 {file_path}: {e}")
            return False
            
    @staticmethod
    def load_annotations(file_path):
        """从YOLO格式文件加载标注"""
        annotations = []
        
        if not os.path.exists(file_path):
            return annotations
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                        
                    annotation = DefectAnnotation.from_yolo_format(line)
                    if annotation and annotation.is_valid():
                        annotation.id = len(annotations)
                        annotations.append(annotation)
                    else:
                        print(f"警告: {file_path} 第{line_num}行格式错误: {line}")
                        
        except Exception as e:
            print(f"加载标注文件失败 {file_path}: {e}")
            
        return annotations
        
    @staticmethod
    def get_annotation_file_path(image_path):
        """根据图像路径获取对应的标注文件路径"""
        base_path = os.path.splitext(image_path)[0]
        return base_path + '.txt'
        
    @staticmethod
    def has_annotations(image_path):
        """检查图像是否有对应的标注文件"""
        annotation_path = MockYOLOFileManager.get_annotation_file_path(image_path)
        return os.path.exists(annotation_path) and os.path.getsize(annotation_path) > 0
        
    @staticmethod
    def validate_annotation_file(file_path):
        """验证YOLO标注文件格式"""
        errors = []
        
        if not os.path.exists(file_path):
            errors.append(f"文件不存在: {file_path}")
            return False, errors
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                        
                    parts = line.split()
                    if len(parts) < 5:
                        errors.append(f"第{line_num}行: 字段数量不足 ({len(parts)}/5)")
                        continue
                        
                    try:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        if class_id < 0:
                            errors.append(f"第{line_num}行: 类别ID不能为负数")
                            
                        if not (0 <= x_center <= 1):
                            errors.append(f"第{line_num}行: x_center超出范围 [0,1]: {x_center}")
                            
                        if not (0 <= y_center <= 1):
                            errors.append(f"第{line_num}行: y_center超出范围 [0,1]: {y_center}")
                            
                        if not (0 < width <= 1):
                            errors.append(f"第{line_num}行: width超出范围 (0,1]: {width}")
                            
                        if not (0 < height <= 1):
                            errors.append(f"第{line_num}行: height超出范围 (0,1]: {height}")
                            
                    except ValueError as e:
                        errors.append(f"第{line_num}行: 数值格式错误: {e}")
                        
        except Exception as e:
            errors.append(f"读取文件失败: {e}")
            
        return len(errors) == 0, errors
        
    def find_annotation_files(self, directory):
        """查找目录下的所有标注文件"""
        annotation_files = []
        
        try:
            for txt_file in Path(directory).rglob("*.txt"):
                if txt_file.is_file():
                    annotation_files.append(str(txt_file))
        except Exception as e:
            print(f"搜索标注文件失败 {directory}: {e}")
            
        return sorted(annotation_files)
        
    def get_annotation_statistics(self, directory):
        """获取目录下标注文件的统计信息"""
        stats = {
            'total_annotation_files': 0,
            'total_annotations': 0,
            'annotations_by_class': {},
            'valid_files': 0,
            'invalid_files': 0
        }
        
        annotation_files = self.find_annotation_files(directory)
        stats['total_annotation_files'] = len(annotation_files)
        
        for annotation_file in annotation_files:
            is_valid, _ = self.validate_annotation_file(annotation_file)
            
            if is_valid:
                stats['valid_files'] += 1
                annotations = self.load_annotations(annotation_file)
                stats['total_annotations'] += len(annotations)
                
                for annotation in annotations:
                    class_id = annotation.defect_class
                    if class_id not in stats['annotations_by_class']:
                        stats['annotations_by_class'][class_id] = 0
                    stats['annotations_by_class'][class_id] += 1
            else:
                stats['invalid_files'] += 1
                
        return stats


def test_yolo_file_io():
    """测试YOLO文件IO功能"""
    print("📁 YOLO文件IO功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    manager = MockYOLOFileManager(temp_dir)
    
    try:
        # 测试1: 创建测试标注
        print("📝 测试1: 创建测试标注")
        try:
            test_annotations = [
                DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
                DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15),
                DefectAnnotation(2, 0.8, 0.2, 0.12, 0.25)
            ]
            
            print(f"  ✅ 创建了 {len(test_annotations)} 个测试标注")
            for i, ann in enumerate(test_annotations):
                print(f"    {i+1}. {ann}")
            test_results.append(True)
        except Exception as e:
            print(f"  ❌ 创建测试标注失败: {e}")
            test_results.append(False)
        
        # 测试2: 保存标注文件
        print("📝 测试2: 保存标注文件")
        try:
            test_file = os.path.join(temp_dir, "test_annotations.txt")
            success = manager.save_annotations(test_annotations, test_file)
            
            if success and os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print(f"  ✅ 标注文件保存成功: {test_file}")
                print(f"    文件大小: {file_size} 字节")
                test_results.append(True)
            else:
                print(f"  ❌ 标注文件保存失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 保存标注文件异常: {e}")
            test_results.append(False)
        
        # 测试3: 加载标注文件
        print("📝 测试3: 加载标注文件")
        try:
            loaded_annotations = manager.load_annotations(test_file)
            
            if len(loaded_annotations) == len(test_annotations):
                print(f"  ✅ 标注文件加载成功: {len(loaded_annotations)} 个标注")
                
                # 验证数据一致性
                all_match = True
                for original, loaded in zip(test_annotations, loaded_annotations):
                    if (original.defect_class != loaded.defect_class or
                        abs(original.x_center - loaded.x_center) > 1e-6 or
                        abs(original.y_center - loaded.y_center) > 1e-6):
                        all_match = False
                        break
                        
                if all_match:
                    print(f"  ✅ 数据一致性验证通过")
                    test_results.append(True)
                else:
                    print(f"  ❌ 数据一致性验证失败")
                    test_results.append(False)
            else:
                print(f"  ❌ 加载的标注数量不匹配: {len(loaded_annotations)}/{len(test_annotations)}")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 加载标注文件异常: {e}")
            test_results.append(False)
        
        # 测试4: 文件路径处理
        print("📝 测试4: 文件路径处理")
        try:
            image_path = "/path/to/image.jpg"
            annotation_path = manager.get_annotation_file_path(image_path)
            expected_path = "/path/to/image.txt"
            
            if annotation_path == expected_path:
                print(f"  ✅ 文件路径处理正确: {annotation_path}")
                test_results.append(True)
            else:
                print(f"  ❌ 文件路径处理错误: 期望 {expected_path}, 得到 {annotation_path}")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 文件路径处理异常: {e}")
            test_results.append(False)
        
        # 测试5: 标注文件验证
        print("📝 测试5: 标注文件验证")
        try:
            # 验证有效文件
            is_valid, errors = manager.validate_annotation_file(test_file)
            
            if is_valid and len(errors) == 0:
                print(f"  ✅ 有效文件验证通过")
                
                # 创建无效文件进行测试
                invalid_file = os.path.join(temp_dir, "invalid.txt")
                with open(invalid_file, 'w') as f:
                    f.write("0 0.5 0.5\n")  # 缺少字段
                    f.write("invalid line\n")  # 格式错误
                    f.write("0 1.5 0.5 0.2 0.3\n")  # 数值超出范围
                    
                is_invalid, invalid_errors = manager.validate_annotation_file(invalid_file)
                
                if not is_invalid and len(invalid_errors) > 0:
                    print(f"  ✅ 无效文件验证通过: {len(invalid_errors)} 个错误")
                    test_results.append(True)
                else:
                    print(f"  ❌ 无效文件验证失败")
                    test_results.append(False)
            else:
                print(f"  ❌ 有效文件验证失败: {errors}")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 文件验证异常: {e}")
            test_results.append(False)
        
        # 测试6: 查找标注文件
        print("📝 测试6: 查找标注文件")
        try:
            # 创建更多测试文件
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir, exist_ok=True)
            
            additional_files = [
                os.path.join(subdir, "test2.txt"),
                os.path.join(temp_dir, "test3.txt")
            ]
            
            for file_path in additional_files:
                manager.save_annotations([test_annotations[0]], file_path)
                
            # 查找所有标注文件
            found_files = manager.find_annotation_files(temp_dir)
            
            if len(found_files) >= 3:  # 至少应该找到3个文件
                print(f"  ✅ 查找标注文件成功: {len(found_files)} 个文件")
                test_results.append(True)
            else:
                print(f"  ❌ 查找标注文件失败: 只找到 {len(found_files)} 个文件")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 查找标注文件异常: {e}")
            test_results.append(False)
        
        # 测试7: 统计信息
        print("📝 测试7: 统计信息")
        try:
            stats = manager.get_annotation_statistics(temp_dir)
            
            if (stats['total_annotation_files'] > 0 and 
                stats['total_annotations'] > 0 and
                stats['valid_files'] > 0):
                print(f"  ✅ 统计信息正确:")
                print(f"    标注文件总数: {stats['total_annotation_files']}")
                print(f"    标注总数: {stats['total_annotations']}")
                print(f"    有效文件: {stats['valid_files']}")
                print(f"    无效文件: {stats['invalid_files']}")
                print(f"    按类别分布: {stats['annotations_by_class']}")
                test_results.append(True)
            else:
                print(f"  ❌ 统计信息错误: {stats}")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 统计信息异常: {e}")
            test_results.append(False)
        
        # 测试8: 检查标注存在性
        print("📝 测试8: 检查标注存在性")
        try:
            # 创建图像文件和对应的标注文件
            image_with_annotation = os.path.join(temp_dir, "with_annotation.jpg")
            with open(image_with_annotation, 'w') as f:
                f.write("fake image")
                
            annotation_file = manager.get_annotation_file_path(image_with_annotation)
            manager.save_annotations([test_annotations[0]], annotation_file)
            
            # 创建没有标注的图像文件
            image_without_annotation = os.path.join(temp_dir, "without_annotation.jpg")
            with open(image_without_annotation, 'w') as f:
                f.write("fake image")
                
            # 测试检查功能
            has_annotation = manager.has_annotations(image_with_annotation)
            no_annotation = manager.has_annotations(image_without_annotation)
            
            if has_annotation and not no_annotation:
                print(f"  ✅ 标注存在性检查正确")
                test_results.append(True)
            else:
                print(f"  ❌ 标注存在性检查错误: {has_annotation}, {no_annotation}")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 标注存在性检查异常: {e}")
            test_results.append(False)
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
    
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
        print("\n🎉 所有测试通过! YOLO文件IO功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_yolo_file_io()
    sys.exit(0 if success else 1)
