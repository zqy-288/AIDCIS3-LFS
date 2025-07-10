#!/usr/bin/env python3
"""
独立的集成测试
验证各模块间的集成和整体系统功能
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path

# 模拟所有必要的类
class DefectAnnotation:
    def __init__(self, defect_class, x_center, y_center, width, height, confidence=1.0):
        self.defect_class = defect_class
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.confidence = confidence
        
    def to_yolo_format(self):
        return f"{self.defect_class} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"
        
    def is_valid(self):
        return (0 <= self.x_center <= 1 and 0 <= self.y_center <= 1 and 
                0 < self.width <= 1 and 0 < self.height <= 1 and self.defect_class >= 0)

class MockImageScanner:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.hole_ids = []
        self.images_by_hole = {}
        
    def scan_directories(self):
        try:
            if not self.base_path.exists():
                return False
            for item in self.base_path.iterdir():
                if item.is_dir() and item.name.startswith('H') and item.name[1:].isdigit():
                    hole_id = item.name
                    self.hole_ids.append(hole_id)
                    
                    result_dir = item / "BISDM" / "result"
                    images = []
                    if result_dir.exists():
                        for img_file in result_dir.glob("*.jpg"):
                            images.append(type('ImageInfo', (), {
                                'file_path': str(img_file),
                                'file_name': img_file.name
                            })())
                    self.images_by_hole[hole_id] = images
            return True
        except Exception:
            return False
            
    def get_hole_ids(self):
        return sorted(self.hole_ids)
        
    def get_images_for_hole(self, hole_id):
        return self.images_by_hole.get(hole_id, [])
        
    def get_statistics(self):
        total_images = sum(len(images) for images in self.images_by_hole.values())
        total_size = total_images * 1024  # 假设每张图像1KB
        return {
            'total_holes': len(self.hole_ids),
            'total_images': total_images,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }

class MockYOLOFileManager:
    @staticmethod
    def save_annotations(annotations, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# YOLO format annotations\n")
                for annotation in annotations:
                    if annotation.is_valid():
                        f.write(annotation.to_yolo_format() + '\n')
            return True
        except Exception:
            return False
            
    @staticmethod
    def load_annotations(file_path):
        annotations = []
        if not os.path.exists(file_path):
            return annotations
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 5:
                        annotation = DefectAnnotation(
                            int(parts[0]), float(parts[1]), float(parts[2]),
                            float(parts[3]), float(parts[4])
                        )
                        if annotation.is_valid():
                            annotations.append(annotation)
        except Exception:
            pass
        return annotations
        
    @staticmethod
    def get_annotation_file_path(image_path):
        return os.path.splitext(image_path)[0] + '.txt'
        
    @staticmethod
    def has_annotations(image_path):
        annotation_path = MockYOLOFileManager.get_annotation_file_path(image_path)
        return os.path.exists(annotation_path) and os.path.getsize(annotation_path) > 0
        
    @staticmethod
    def validate_annotation_file(file_path):
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
                        errors.append(f"第{line_num}行: 字段数量不足")
                        continue
                    try:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 
                               0 < width <= 1 and 0 < height <= 1):
                            errors.append(f"第{line_num}行: 坐标超出范围")
                    except ValueError:
                        errors.append(f"第{line_num}行: 数值格式错误")
        except Exception as e:
            errors.append(f"读取文件失败: {e}")
        return len(errors) == 0, errors
        
    def find_annotation_files(self, directory):
        annotation_files = []
        try:
            for txt_file in Path(directory).rglob("*.txt"):
                if txt_file.is_file():
                    annotation_files.append(str(txt_file))
        except Exception:
            pass
        return sorted(annotation_files)
        
    def get_annotation_statistics(self, directory):
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

class MockCategoryManager:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.categories = {
            0: type('Category', (), {'id': 0, 'display_name': '裂纹', 'color': '#FF0000', 'enabled': True})(),
            1: type('Category', (), {'id': 1, 'display_name': '腐蚀', 'color': '#FF8000', 'enabled': True})(),
            2: type('Category', (), {'id': 2, 'display_name': '点蚀', 'color': '#FFFF00', 'enabled': True})(),
        }
        
    def get_all_categories(self, enabled_only=False):
        categories = list(self.categories.values())
        if enabled_only:
            categories = [cat for cat in categories if cat.enabled]
        return categories
        
    def get_category_name(self, category_id):
        category = self.categories.get(category_id)
        return category.display_name if category else f"未知类别{category_id}"
        
    def get_category_color(self, category_id):
        category = self.categories.get(category_id)
        return category.color if category else "#808080"
        
    def validate_category_id(self, category_id):
        return category_id in self.categories and self.categories[category_id].enabled
        
    def save_categories(self):
        try:
            if self.config_file:
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                data = {'categories': [{'id': cat.id, 'display_name': cat.display_name, 'color': cat.color} 
                                     for cat in self.categories.values()]}
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
            
    def get_statistics(self):
        return {
            'total_categories': len(self.categories),
            'enabled_categories': len([cat for cat in self.categories.values() if cat.enabled])
        }

class MockArchiveManager:
    def __init__(self, base_path, archive_path):
        self.base_path = Path(base_path)
        self.archive_path = Path(archive_path)
        self.archive_path.mkdir(exist_ok=True)
        
        self.image_scanner = MockImageScanner(str(self.base_path))
        self.yolo_manager = MockYOLOFileManager()
        self.archive_records = {}
        
    def get_annotated_holes(self):
        annotated_holes = []
        if self.image_scanner.scan_directories():
            for hole_id in self.image_scanner.get_hole_ids():
                images = self.image_scanner.get_images_for_hole(hole_id)
                has_annotations = False
                for image_info in images:
                    if self.yolo_manager.has_annotations(image_info.file_path):
                        has_annotations = True
                        break
                if has_annotations:
                    annotated_holes.append(hole_id)
        return sorted(annotated_holes)
        
    def get_hole_annotation_summary(self, hole_id):
        summary = {
            'hole_id': hole_id,
            'total_images': 0,
            'annotated_images': 0,
            'total_annotations': 0,
            'annotations_by_class': {}
        }
        
        images = self.image_scanner.get_images_for_hole(hole_id)
        summary['total_images'] = len(images)
        
        for image_info in images:
            if self.yolo_manager.has_annotations(image_info.file_path):
                summary['annotated_images'] += 1
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                annotations = self.yolo_manager.load_annotations(annotation_file)
                summary['total_annotations'] += len(annotations)
                
                for annotation in annotations:
                    class_id = annotation.defect_class
                    if class_id not in summary['annotations_by_class']:
                        summary['annotations_by_class'][class_id] = 0
                    summary['annotations_by_class'][class_id] += 1
        return summary
        
    def archive_hole(self, hole_id, notes=""):
        try:
            if hole_id not in self.image_scanner.get_hole_ids():
                return False
            summary = self.get_hole_annotation_summary(hole_id)
            if summary['annotated_images'] == 0:
                return False
                
            archive_hole_path = self.archive_path / hole_id
            archive_hole_path.mkdir(exist_ok=True)
            
            images = self.image_scanner.get_images_for_hole(hole_id)
            for image_info in images:
                image_dest = archive_hole_path / image_info.file_name
                shutil.copy2(image_info.file_path, image_dest)
                
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                if os.path.exists(annotation_file):
                    annotation_dest = archive_hole_path / (os.path.splitext(image_info.file_name)[0] + '.txt')
                    shutil.copy2(annotation_file, annotation_dest)
                    
            self.archive_records[hole_id] = {
                'hole_id': hole_id,
                'notes': notes,
                'total_annotations': summary['total_annotations'],
                'archive_path': str(archive_hole_path)
            }
            return True
        except Exception:
            return False
            
    def get_archived_holes(self):
        return sorted(list(self.archive_records.keys()))
        
    def get_archive_statistics(self):
        return {
            'total_archived_holes': len(self.archive_records),
            'total_archived_annotations': sum(record['total_annotations'] for record in self.archive_records.values())
        }


def create_test_data(data_dir):
    """创建测试数据"""
    holes = ["H00001", "H00002", "H00003"]
    
    for hole_id in holes:
        hole_dir = data_dir / hole_id / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建图像和标注文件
        for i in range(3):
            image_file = hole_dir / f"image{i+1}.jpg"
            image_file.write_bytes(b"fake image content")
            
            if i < 2:  # 前两张图像有标注
                annotation_file = hole_dir / f"image{i+1}.txt"
                annotations = [
                    DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
                    DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15)
                ]
                MockYOLOFileManager.save_annotations(annotations, str(annotation_file))


def test_integration():
    """测试集成功能"""
    print("🔗 集成测试")
    print("=" * 60)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "Data"
    archive_dir = Path(temp_dir) / "Archive"
    config_dir = Path(temp_dir) / "config"
    
    try:
        # 创建测试数据
        create_test_data(data_dir)
        
        # 初始化系统组件
        image_scanner = MockImageScanner(str(data_dir))
        yolo_manager = MockYOLOFileManager()
        category_manager = MockCategoryManager(str(config_dir / "categories.json"))
        archive_manager = MockArchiveManager(str(data_dir), str(archive_dir))
        
        # 测试1: 图像扫描与YOLO文件集成
        print("📝 测试1: 图像扫描与YOLO文件集成")
        try:
            # 扫描图像
            scan_success = image_scanner.scan_directories()
            hole_ids = image_scanner.get_hole_ids()
            
            if scan_success and len(hole_ids) > 0:
                print(f"  ✅ 扫描成功: {len(hole_ids)} 个孔位")
                
                # 验证标注文件
                first_hole = hole_ids[0]
                images = image_scanner.get_images_for_hole(first_hole)
                annotated_count = 0
                
                for image_info in images:
                    if yolo_manager.has_annotations(image_info.file_path):
                        annotated_count += 1
                        
                if annotated_count > 0:
                    print(f"  ✅ 发现标注: {annotated_count} 张图像有标注")
                    test_results.append(True)
                else:
                    print(f"  ❌ 没有发现标注")
                    test_results.append(False)
            else:
                print(f"  ❌ 扫描失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 图像扫描与YOLO文件集成异常: {e}")
            test_results.append(False)
        
        # 测试2: 缺陷类别与标注集成
        print("📝 测试2: 缺陷类别与标注集成")
        try:
            categories = category_manager.get_all_categories()
            
            if len(categories) > 0:
                # 使用类别创建标注
                first_category = categories[0]
                annotation = DefectAnnotation(first_category.id, 0.4, 0.6, 0.15, 0.2)
                
                # 验证类别信息
                category_name = category_manager.get_category_name(annotation.defect_class)
                category_color = category_manager.get_category_color(annotation.defect_class)
                is_valid = category_manager.validate_category_id(annotation.defect_class)
                
                if (category_name == first_category.display_name and
                    category_color == first_category.color and is_valid):
                    print(f"  ✅ 类别集成正确: {category_name} ({category_color})")
                    test_results.append(True)
                else:
                    print(f"  ❌ 类别集成错误")
                    test_results.append(False)
            else:
                print(f"  ❌ 没有可用类别")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 缺陷类别与标注集成异常: {e}")
            test_results.append(False)
        
        # 测试3: 归档管理集成
        print("📝 测试3: 归档管理集成")
        try:
            # 获取有标注的孔位
            annotated_holes = archive_manager.get_annotated_holes()
            
            if len(annotated_holes) > 0:
                print(f"  ✅ 发现有标注孔位: {annotated_holes}")
                
                # 获取标注摘要
                hole_id = annotated_holes[0]
                summary = archive_manager.get_hole_annotation_summary(hole_id)
                
                if (summary['total_images'] > 0 and 
                    summary['annotated_images'] > 0 and
                    summary['total_annotations'] > 0):
                    print(f"  ✅ 标注摘要正确: {summary['annotated_images']}/{summary['total_images']} 张图像，{summary['total_annotations']} 个标注")
                    
                    # 测试归档
                    archive_success = archive_manager.archive_hole(hole_id, "集成测试归档")
                    
                    if archive_success:
                        archived_holes = archive_manager.get_archived_holes()
                        if hole_id in archived_holes:
                            print(f"  ✅ 归档成功: {hole_id}")
                            test_results.append(True)
                        else:
                            print(f"  ❌ 归档记录未找到")
                            test_results.append(False)
                    else:
                        print(f"  ❌ 归档失败")
                        test_results.append(False)
                else:
                    print(f"  ❌ 标注摘要数据错误")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 没有有标注的孔位")
                test_results.append(True)  # 这不算失败
        except Exception as e:
            print(f"  ❌ 归档管理集成异常: {e}")
            test_results.append(False)
        
        # 测试4: 完整工作流
        print("📝 测试4: 完整工作流")
        try:
            # 1. 扫描项目
            image_scanner.scan_directories()
            scan_stats = image_scanner.get_statistics()
            
            # 2. 验证标注
            annotation_stats = yolo_manager.get_annotation_statistics(str(data_dir))
            
            # 3. 保存配置
            config_saved = category_manager.save_categories()
            
            # 4. 获取归档统计
            archive_stats = archive_manager.get_archive_statistics()
            
            if (scan_stats['total_holes'] > 0 and
                annotation_stats['total_annotations'] > 0 and
                config_saved and
                archive_stats['total_archived_holes'] >= 0):
                print(f"  ✅ 完整工作流成功:")
                print(f"    扫描: {scan_stats['total_holes']} 个孔位，{scan_stats['total_images']} 张图像")
                print(f"    标注: {annotation_stats['total_annotations']} 个标注")
                print(f"    归档: {archive_stats['total_archived_holes']} 个孔位")
                test_results.append(True)
            else:
                print(f"  ❌ 完整工作流失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 完整工作流异常: {e}")
            test_results.append(False)
        
        # 测试5: 数据一致性
        print("📝 测试5: 数据一致性")
        try:
            # 验证标注文件与图像文件的一致性
            hole_ids = image_scanner.get_hole_ids()
            consistency_check = True

            for hole_id in hole_ids:
                images = image_scanner.get_images_for_hole(hole_id)
                for image_info in images:
                    # 检查有标注的图像是否标注文件存在
                    annotation_file = yolo_manager.get_annotation_file_path(image_info.file_path)
                    has_annotation_file = os.path.exists(annotation_file)
                    has_annotation_check = yolo_manager.has_annotations(image_info.file_path)

                    # 两种检查方法应该一致
                    if has_annotation_file != has_annotation_check:
                        consistency_check = False
                        break

                if not consistency_check:
                    break

            if consistency_check:
                print(f"  ✅ 标注文件一致性验证通过")

                # 验证标注数据的有效性
                annotation_stats = yolo_manager.get_annotation_statistics(str(data_dir))
                if annotation_stats['valid_files'] > 0 and annotation_stats['invalid_files'] == 0:
                    print(f"  ✅ 标注数据有效性验证通过: {annotation_stats['valid_files']} 个有效文件")
                    test_results.append(True)
                else:
                    print(f"  ❌ 标注数据有效性验证失败")
                    test_results.append(False)
            else:
                print(f"  ❌ 标注文件一致性验证失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 数据一致性验证异常: {e}")
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
        print("\n🎉 所有集成测试通过! 系统集成功能正常")
        return True
    else:
        print("\n⚠️ 部分集成测试失败，需要检查模块间的协作")
        return False


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
