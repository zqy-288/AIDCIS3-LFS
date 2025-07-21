"""
归档管理模块
实现已标注孔位的归档、历史记录和快速加载功能
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict

from .yolo_file_manager import YOLOFileManager
from .image_scanner import ImageScanner


@dataclass
class ArchiveRecord:
    """归档记录"""
    hole_id: str                    # 孔位ID
    archived_at: str               # 归档时间
    total_images: int              # 总图像数量
    annotated_images: int          # 已标注图像数量
    total_annotations: int         # 总标注数量
    annotation_summary: Dict       # 标注摘要（按类别统计）
    archive_path: str              # 归档路径
    notes: str = ""                # 备注
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArchiveRecord':
        """从字典创建"""
        return cls(**data)


class ArchiveManager:
    """归档管理器"""
    
    def __init__(self, base_path: str = "Data", archive_path: str = "Archive", image_scanner=None):
        """
        初始化归档管理器

        Args:
            base_path: 数据基础路径
            archive_path: 归档基础路径
            image_scanner: 可选的外部ImageScanner实例
        """
        self.base_path = Path(base_path)
        self.archive_path = Path(archive_path)
        self.archive_index_file = self.archive_path / "archive_index.json"

        # 确保归档目录存在
        self.archive_path.mkdir(exist_ok=True)

        # 初始化组件
        if image_scanner is not None:
            self.image_scanner = image_scanner
        else:
            self.image_scanner = ImageScanner(str(self.base_path))
        self.yolo_manager = YOLOFileManager()
        
        # 加载归档索引
        self.archive_records: Dict[str, ArchiveRecord] = {}
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
                    
                print(f"加载了 {len(self.archive_records)} 个归档记录")
                
            except Exception as e:
                print(f"加载归档索引失败: {e}")
                self.archive_records = {}
        else:
            print("归档索引文件不存在，创建新索引")
            self.archive_records = {}
            
    def save_archive_index(self) -> bool:
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
            
        except Exception as e:
            print(f"保存归档索引失败: {e}")
            return False
            
    def get_annotated_holes(self) -> List[str]:
        """
        获取所有有标注的孔位ID
        
        Returns:
            List[str]: 有标注的孔位ID列表
        """
        annotated_holes = []
        
        # 扫描图像
        if self.image_scanner.scan_directories():
            for hole_id in self.image_scanner.get_hole_ids():
                images = self.image_scanner.get_images_for_hole(hole_id)
                
                # 检查是否有任何图像有标注
                has_annotations = False
                for image_info in images:
                    if self.yolo_manager.has_annotations(image_info.file_path):
                        has_annotations = True
                        break
                        
                if has_annotations:
                    annotated_holes.append(hole_id)
                    
        return sorted(annotated_holes)
        
    def get_hole_annotation_summary(self, hole_id: str) -> Dict:
        """
        获取指定孔位的标注摘要
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Dict: 标注摘要信息
        """
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
                
                # 加载标注
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                annotations = self.yolo_manager.load_annotations(annotation_file)
                
                summary['total_annotations'] += len(annotations)
                summary['annotation_files'].append(annotation_file)
                
                # 按类别统计
                for annotation in annotations:
                    class_id = annotation.defect_class
                    if class_id not in summary['annotations_by_class']:
                        summary['annotations_by_class'][class_id] = 0
                    summary['annotations_by_class'][class_id] += 1
                    
        return summary
        
    def archive_hole(self, hole_id: str, notes: str = "") -> bool:
        """
        归档指定孔位的标注数据
        
        Args:
            hole_id: 孔位ID
            notes: 归档备注
            
        Returns:
            bool: 归档是否成功
        """
        try:
            # 检查孔位是否存在
            if hole_id not in self.image_scanner.get_hole_ids():
                print(f"孔位 {hole_id} 不存在")
                return False
                
            # 获取标注摘要
            summary = self.get_hole_annotation_summary(hole_id)
            
            if summary['annotated_images'] == 0:
                print(f"孔位 {hole_id} 没有标注数据")
                return False
                
            # 创建归档目录
            archive_hole_path = self.archive_path / hole_id
            archive_hole_path.mkdir(exist_ok=True)
            
            # 复制图像和标注文件
            images = self.image_scanner.get_images_for_hole(hole_id)
            copied_files = []
            
            for image_info in images:
                # 复制图像文件
                image_dest = archive_hole_path / image_info.file_name
                shutil.copy2(image_info.file_path, image_dest)
                copied_files.append(str(image_dest))
                
                # 复制标注文件（如果存在）
                annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                if os.path.exists(annotation_file):
                    annotation_dest = archive_hole_path / (os.path.splitext(image_info.file_name)[0] + '.txt')
                    shutil.copy2(annotation_file, annotation_dest)
                    copied_files.append(str(annotation_dest))
                    
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
            
            # 保存归档记录
            self.archive_records[hole_id] = archive_record
            
            # 创建归档元数据文件
            metadata = {
                'archive_record': archive_record.to_dict(),
                'summary': summary,
                'copied_files': copied_files,
                'created_at': datetime.now().isoformat()
            }
            
            metadata_file = archive_hole_path / "archive_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            # 保存归档索引
            self.save_archive_index()
            
            print(f"孔位 {hole_id} 归档成功: {summary['annotated_images']}/{summary['total_images']} 张图像，{summary['total_annotations']} 个标注")
            return True
            
        except Exception as e:
            print(f"归档孔位 {hole_id} 失败: {e}")
            return False
            
    def get_archived_holes(self) -> List[str]:
        """
        获取所有已归档的孔位ID
        
        Returns:
            List[str]: 已归档的孔位ID列表
        """
        return sorted(list(self.archive_records.keys()))
        
    def get_archive_record(self, hole_id: str) -> Optional[ArchiveRecord]:
        """
        获取指定孔位的归档记录
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[ArchiveRecord]: 归档记录，如果不存在则返回None
        """
        return self.archive_records.get(hole_id)
        
    def load_archived_hole(self, hole_id: str, target_path: Optional[str] = None) -> bool:
        """
        从归档中加载孔位数据
        
        Args:
            hole_id: 孔位ID
            target_path: 目标路径，如果为None则加载到原始位置
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if hole_id not in self.archive_records:
                print(f"归档中不存在孔位 {hole_id}")
                return False
                
            archive_record = self.archive_records[hole_id]
            archive_hole_path = Path(archive_record.archive_path)
            
            if not archive_hole_path.exists():
                print(f"归档路径不存在: {archive_hole_path}")
                return False
                
            # 确定目标路径
            if target_path is None:
                target_path = self.base_path / hole_id / "BISDM" / "result"
            else:
                target_path = Path(target_path)
                
            # 创建目标目录
            target_path.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            copied_count = 0
            for item in archive_hole_path.iterdir():
                if item.is_file() and item.name != "archive_metadata.json":
                    target_file = target_path / item.name
                    shutil.copy2(item, target_file)
                    copied_count += 1
                    
            print(f"从归档加载孔位 {hole_id}: {copied_count} 个文件")
            return True
            
        except Exception as e:
            print(f"加载归档孔位 {hole_id} 失败: {e}")
            return False
            
    def remove_archive(self, hole_id: str) -> bool:
        """
        删除归档记录和文件
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if hole_id not in self.archive_records:
                print(f"归档中不存在孔位 {hole_id}")
                return False
                
            archive_record = self.archive_records[hole_id]
            archive_hole_path = Path(archive_record.archive_path)
            
            # 删除归档文件夹
            if archive_hole_path.exists():
                shutil.rmtree(archive_hole_path)
                
            # 删除记录
            del self.archive_records[hole_id]
            
            # 保存索引
            self.save_archive_index()
            
            print(f"删除归档 {hole_id} 成功")
            return True
            
        except Exception as e:
            print(f"删除归档 {hole_id} 失败: {e}")
            return False
            
    def get_archive_statistics(self) -> Dict:
        """
        获取归档统计信息
        
        Returns:
            Dict: 归档统计信息
        """
        stats = {
            'total_archived_holes': len(self.archive_records),
            'total_archived_images': 0,
            'total_archived_annotations': 0,
            'archive_size_mb': 0,
            'annotations_by_class': {},
            'recent_archives': []
        }
        
        # 统计归档数据
        for record in self.archive_records.values():
            stats['total_archived_images'] += record.total_images
            stats['total_archived_annotations'] += record.total_annotations
            
            # 按类别统计
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
        except Exception as e:
            print(f"计算归档大小失败: {e}")
            
        # 最近的归档记录
        recent_records = sorted(
            self.archive_records.values(),
            key=lambda x: x.archived_at,
            reverse=True
        )[:5]
        
        stats['recent_archives'] = [
            {
                'hole_id': record.hole_id,
                'archived_at': record.archived_at,
                'total_annotations': record.total_annotations
            }
            for record in recent_records
        ]
        
        return stats
        
    def export_archive_report(self, output_file: str) -> bool:
        """
        导出归档报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': self.get_archive_statistics(),
                'archive_records': [record.to_dict() for record in self.archive_records.values()]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"导出归档报告失败: {e}")
            return False


if __name__ == "__main__":
    # 简单测试
    print("📦 归档管理器测试")
    print("=" * 50)
    
    manager = ArchiveManager()
    
    # 获取有标注的孔位
    annotated_holes = manager.get_annotated_holes()
    print(f"📋 有标注的孔位 ({len(annotated_holes)} 个):")
    for hole_id in annotated_holes:
        summary = manager.get_hole_annotation_summary(hole_id)
        print(f"  {hole_id}: {summary['annotated_images']}/{summary['total_images']} 张图像，{summary['total_annotations']} 个标注")
        
    # 获取已归档的孔位
    archived_holes = manager.get_archived_holes()
    print(f"\n📦 已归档的孔位 ({len(archived_holes)} 个):")
    for hole_id in archived_holes:
        record = manager.get_archive_record(hole_id)
        if record:
            print(f"  {hole_id}: 归档于 {record.archived_at[:19]}")
            
    # 显示统计信息
    stats = manager.get_archive_statistics()
    print(f"\n📊 归档统计:")
    print(f"  已归档孔位: {stats['total_archived_holes']}")
    print(f"  已归档图像: {stats['total_archived_images']}")
    print(f"  已归档标注: {stats['total_archived_annotations']}")
    print(f"  归档大小: {stats['archive_size_mb']} MB")
