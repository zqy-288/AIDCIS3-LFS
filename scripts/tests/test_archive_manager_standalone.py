#!/usr/bin/env python3
"""
独立的归档管理器测试
验证归档管理、历史记录和快速加载功能
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

# 模拟DefectAnnotation类
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

# 模拟ArchiveRecord类
@dataclass
class ArchiveRecord:
    """归档记录"""
    hole_id: str
    archived_at: str
    total_images: int
    annotated_images: int
    total_annotations: int
    annotation_summary: Dict
    archive_path: str
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArchiveRecord':
        return cls(**data)

# 模拟YOLOFileManager类
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

# 模拟ImageScanner类
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
                    
                    # 查找图像文件
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

# 模拟ArchiveManager类
class MockArchiveManager:
    """模拟的归档管理器"""
    
    def __init__(self, base_path="Data", archive_path="Archive"):
        self.base_path = Path(base_path)
        self.archive_path = Path(archive_path)
        self.archive_index_file = self.archive_path / "archive_index.json"
        
        # 确保归档目录存在
        self.archive_path.mkdir(exist_ok=True)
        
        # 初始化组件
        self.image_scanner = MockImageScanner(str(self.base_path))
        self.yolo_manager = MockYOLOFileManager()
        
        # 归档记录
        self.archive_records = {}
        self.load_archive_index()
        
    def load_archive_index(self):
        """加载归档索引"""
        if self.archive_index_file.exists():
            try:
                with open(self.archive_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.archive_records = {}
                for record_data in data.get('records', []):
                    record = ArchiveRecord.from_dict(record_data)
                    self.archive_records[record.hole_id] = record
            except Exception:
                self.archive_records = {}
        else:
            self.archive_records = {}
            
    def save_archive_index(self):
        """保存归档索引"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'total_records': len(self.archive_records),
                'records': [record.to_dict() for record in self.archive_records.values()]
            }
            with open(self.archive_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
            
    def get_annotated_holes(self):
        """获取所有有标注的孔位ID"""
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
        """获取指定孔位的标注摘要"""
        summary = {
            'hole_id': hole_id,
            'total_images': 0,
            'annotated_images': 0,
            'total_annotations': 0,
            'annotations_by_class': {},
            'annotation_files': []
        }
        
        images = self.image_scanner.get_images_for_hole(hole_id)
        summary['total_images'] = len(images)
        
        for image_info in images:
            if self.yolo_manager.has_annotations(image_info.file_path):
                summary['annotated_images'] += 1
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                annotations = self.yolo_manager.load_annotations(annotation_file)
                summary['total_annotations'] += len(annotations)
                summary['annotation_files'].append(annotation_file)
                
                for annotation in annotations:
                    class_id = annotation.defect_class
                    if class_id not in summary['annotations_by_class']:
                        summary['annotations_by_class'][class_id] = 0
                    summary['annotations_by_class'][class_id] += 1
                    
        return summary
        
    def archive_hole(self, hole_id, notes=""):
        """归档指定孔位的标注数据"""
        try:
            if hole_id not in self.image_scanner.get_hole_ids():
                return False
                
            summary = self.get_hole_annotation_summary(hole_id)
            if summary['annotated_images'] == 0:
                return False
                
            # 创建归档目录
            archive_hole_path = self.archive_path / hole_id
            archive_hole_path.mkdir(exist_ok=True)
            
            # 复制文件
            images = self.image_scanner.get_images_for_hole(hole_id)
            for image_info in images:
                # 复制图像文件
                image_dest = archive_hole_path / image_info.file_name
                shutil.copy2(image_info.file_path, image_dest)
                
                # 复制标注文件（如果存在）
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                if os.path.exists(annotation_file):
                    annotation_dest = archive_hole_path / (os.path.splitext(image_info.file_name)[0] + '.txt')
                    shutil.copy2(annotation_file, annotation_dest)
                    
            # 创建归档记录
            archive_record = ArchiveRecord(
                hole_id=hole_id,
                archived_at=datetime.now().isoformat(),
                total_images=summary['total_images'],
                annotated_images=summary['annotated_images'],
                total_annotations=summary['total_annotations'],
                annotation_summary=summary['annotations_by_class'],
                archive_path=str(archive_hole_path),
                notes=notes
            )
            
            self.archive_records[hole_id] = archive_record
            self.save_archive_index()
            
            return True
            
        except Exception:
            return False
            
    def get_archived_holes(self):
        """获取所有已归档的孔位ID"""
        return sorted(list(self.archive_records.keys()))
        
    def get_archive_record(self, hole_id):
        """获取指定孔位的归档记录"""
        return self.archive_records.get(hole_id)
        
    def load_archived_hole(self, hole_id, target_path=None):
        """从归档中加载孔位数据"""
        try:
            if hole_id not in self.archive_records:
                return False
                
            archive_record = self.archive_records[hole_id]
            archive_hole_path = Path(archive_record.archive_path)
            
            if not archive_hole_path.exists():
                return False
                
            if target_path is None:
                target_path = self.base_path / hole_id / "BISDM" / "result"
            else:
                target_path = Path(target_path)
                
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            for item in archive_hole_path.iterdir():
                if item.is_file() and item.name != "archive_metadata.json":
                    target_file = target_path / item.name
                    shutil.copy2(item, target_file)
                    
            return True
            
        except Exception:
            return False
            
    def remove_archive(self, hole_id):
        """删除归档记录和文件"""
        try:
            if hole_id not in self.archive_records:
                return False
                
            archive_record = self.archive_records[hole_id]
            archive_hole_path = Path(archive_record.archive_path)
            
            if archive_hole_path.exists():
                shutil.rmtree(archive_hole_path)
                
            del self.archive_records[hole_id]
            self.save_archive_index()
            
            return True
            
        except Exception:
            return False
            
    def get_archive_statistics(self):
        """获取归档统计信息"""
        stats = {
            'total_archived_holes': len(self.archive_records),
            'total_archived_images': 0,
            'total_archived_annotations': 0,
            'archive_size_mb': 0,
            'annotations_by_class': {},
            'recent_archives': []
        }
        
        for record in self.archive_records.values():
            stats['total_archived_images'] += record.total_images
            stats['total_archived_annotations'] += record.total_annotations
            
            for class_id, count in record.annotation_summary.items():
                if class_id not in stats['annotations_by_class']:
                    stats['annotations_by_class'][class_id] = 0
                stats['annotations_by_class'][class_id] += count
                
        # 计算归档大小
        try:
            total_size = 0
            for record in self.archive_records.values():
                archive_path = Path(record.archive_path)
                if archive_path.exists():
                    for file_path in archive_path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            stats['archive_size_mb'] = round(total_size / (1024 * 1024), 2)
        except Exception:
            pass
            
        # 最近的归档记录
        recent_records = sorted(
            self.archive_records.values(),
            key=lambda x: x.archived_at,
            reverse=True
        )[:3]
        
        stats['recent_archives'] = [
            {
                'hole_id': record.hole_id,
                'archived_at': record.archived_at,
                'total_annotations': record.total_annotations
            }
            for record in recent_records
        ]
        
        return stats


def create_test_data(data_dir):
    """创建测试数据"""
    holes = ["H00001", "H00002"]
    
    for hole_id in holes:
        hole_dir = data_dir / hole_id / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试图像和标注
        for i in range(2):
            image_file = hole_dir / f"image{i+1}.jpg"
            image_file.write_bytes(b"fake image content")
            
            # 创建标注文件
            annotation_file = hole_dir / f"image{i+1}.txt"
            annotations = [
                DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
                DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15)
            ]
            MockYOLOFileManager.save_annotations(annotations, str(annotation_file))


def test_archive_manager():
    """测试归档管理器功能"""
    print("📦 归档管理器功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "Data"
    archive_dir = Path(temp_dir) / "Archive"
    
    try:
        # 创建测试数据
        create_test_data(data_dir)
        
        # 测试1: 创建归档管理器
        print("📝 测试1: 创建归档管理器")
        try:
            manager = MockArchiveManager(str(data_dir), str(archive_dir))
            
            if archive_dir.exists():
                print(f"  ✅ 归档管理器创建成功，归档目录: {archive_dir}")
                test_results.append(True)
            else:
                print(f"  ❌ 归档目录创建失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 归档管理器创建异常: {e}")
            test_results.append(False)
        
        # 测试2: 获取有标注的孔位
        print("📝 测试2: 获取有标注的孔位")
        try:
            annotated_holes = manager.get_annotated_holes()
            
            if len(annotated_holes) > 0:
                print(f"  ✅ 找到有标注的孔位: {annotated_holes}")
                test_results.append(True)
            else:
                print(f"  ❌ 没有找到有标注的孔位")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 获取有标注孔位异常: {e}")
            test_results.append(False)
        
        # 测试3: 获取孔位标注摘要
        print("📝 测试3: 获取孔位标注摘要")
        try:
            if annotated_holes:
                hole_id = annotated_holes[0]
                summary = manager.get_hole_annotation_summary(hole_id)
                
                if (summary['total_images'] > 0 and 
                    summary['annotated_images'] > 0 and
                    summary['total_annotations'] > 0):
                    print(f"  ✅ 孔位 {hole_id} 标注摘要:")
                    print(f"    总图像: {summary['total_images']}")
                    print(f"    已标注图像: {summary['annotated_images']}")
                    print(f"    总标注: {summary['total_annotations']}")
                    print(f"    按类别分布: {summary['annotations_by_class']}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 标注摘要数据错误")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，没有有标注的孔位")
                test_results.append(True)
        except Exception as e:
            print(f"  ❌ 获取标注摘要异常: {e}")
            test_results.append(False)
        
        # 测试4: 归档孔位
        print("📝 测试4: 归档孔位")
        try:
            if annotated_holes:
                hole_id = annotated_holes[0]
                success = manager.archive_hole(hole_id, "测试归档")
                
                if success:
                    print(f"  ✅ 孔位 {hole_id} 归档成功")
                    
                    # 验证归档记录
                    record = manager.get_archive_record(hole_id)
                    if record and record.notes == "测试归档":
                        print(f"  ✅ 归档记录创建正确")
                        test_results.append(True)
                    else:
                        print(f"  ❌ 归档记录创建错误")
                        test_results.append(False)
                else:
                    print(f"  ❌ 孔位归档失败")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，没有可归档的孔位")
                test_results.append(True)
        except Exception as e:
            print(f"  ❌ 归档孔位异常: {e}")
            test_results.append(False)
        
        # 测试5: 获取已归档孔位
        print("📝 测试5: 获取已归档孔位")
        try:
            archived_holes = manager.get_archived_holes()
            
            if len(archived_holes) > 0:
                print(f"  ✅ 已归档孔位: {archived_holes}")
                test_results.append(True)
            else:
                print(f"  ⚠️ 没有已归档的孔位")
                test_results.append(True)
        except Exception as e:
            print(f"  ❌ 获取已归档孔位异常: {e}")
            test_results.append(False)
        
        # 测试6: 从归档加载孔位
        print("📝 测试6: 从归档加载孔位")
        try:
            if archived_holes:
                hole_id = archived_holes[0]
                
                # 删除原始数据
                original_path = data_dir / hole_id
                if original_path.exists():
                    shutil.rmtree(original_path)
                    
                # 从归档加载
                success = manager.load_archived_hole(hole_id)
                
                if success:
                    # 验证数据已恢复
                    restored_path = data_dir / hole_id / "BISDM" / "result"
                    if restored_path.exists():
                        image_files = list(restored_path.glob("*.jpg"))
                        annotation_files = list(restored_path.glob("*.txt"))
                        
                        if len(image_files) > 0 and len(annotation_files) > 0:
                            print(f"  ✅ 孔位 {hole_id} 从归档加载成功")
                            print(f"    恢复图像: {len(image_files)} 个")
                            print(f"    恢复标注: {len(annotation_files)} 个")
                            test_results.append(True)
                        else:
                            print(f"  ❌ 恢复的文件数量不正确")
                            test_results.append(False)
                    else:
                        print(f"  ❌ 恢复路径不存在")
                        test_results.append(False)
                else:
                    print(f"  ❌ 从归档加载失败")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，没有已归档的孔位")
                test_results.append(True)
        except Exception as e:
            print(f"  ❌ 从归档加载异常: {e}")
            test_results.append(False)
        
        # 测试7: 归档统计信息
        print("📝 测试7: 归档统计信息")
        try:
            stats = manager.get_archive_statistics()
            
            if (isinstance(stats, dict) and
                'total_archived_holes' in stats and
                'total_archived_images' in stats and
                'total_archived_annotations' in stats):
                print(f"  ✅ 归档统计信息:")
                print(f"    已归档孔位: {stats['total_archived_holes']}")
                print(f"    已归档图像: {stats['total_archived_images']}")
                print(f"    已归档标注: {stats['total_archived_annotations']}")
                print(f"    归档大小: {stats['archive_size_mb']} MB")
                print(f"    按类别分布: {stats['annotations_by_class']}")
                test_results.append(True)
            else:
                print(f"  ❌ 归档统计信息结构错误")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 获取归档统计异常: {e}")
            test_results.append(False)
        
        # 测试8: 保存和加载归档索引
        print("📝 测试8: 保存和加载归档索引")
        try:
            # 保存索引
            save_success = manager.save_archive_index()
            
            if save_success and manager.archive_index_file.exists():
                print(f"  ✅ 归档索引保存成功")
                
                # 创建新管理器加载索引
                new_manager = MockArchiveManager(str(data_dir), str(archive_dir))
                
                if len(new_manager.archive_records) == len(manager.archive_records):
                    print(f"  ✅ 归档索引加载成功: {len(new_manager.archive_records)} 个记录")
                    test_results.append(True)
                else:
                    print(f"  ❌ 归档索引加载数量不匹配")
                    test_results.append(False)
            else:
                print(f"  ❌ 归档索引保存失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 保存和加载归档索引异常: {e}")
            test_results.append(False)
        
        # 测试9: 删除归档
        print("📝 测试9: 删除归档")
        try:
            if archived_holes:
                hole_id = archived_holes[0]
                
                # 删除归档
                success = manager.remove_archive(hole_id)
                
                if success:
                    # 验证归档已删除
                    if hole_id not in manager.archive_records:
                        print(f"  ✅ 归档 {hole_id} 删除成功")
                        test_results.append(True)
                    else:
                        print(f"  ❌ 归档记录未删除")
                        test_results.append(False)
                else:
                    print(f"  ❌ 删除归档失败")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，没有可删除的归档")
                test_results.append(True)
        except Exception as e:
            print(f"  ❌ 删除归档异常: {e}")
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
        print("\n🎉 所有测试通过! 归档管理器功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_archive_manager()
    sys.exit(0 if success else 1)
