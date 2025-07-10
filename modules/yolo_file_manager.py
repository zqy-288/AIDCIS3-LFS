"""
YOLO文件IO管理模块
实现YOLO格式标注文件的读取、保存、验证和批量处理功能
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime

from .defect_annotation_model import DefectAnnotation, DefectCategory


class YOLOFileManager:
    """增强版YOLO格式文件管理器"""
    
    # 支持的图像格式
    SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def __init__(self, base_path: str = "Data"):
        """
        初始化YOLO文件管理器
        
        Args:
            base_path: 基础路径，默认为"Data"
        """
        self.base_path = Path(base_path)
        
    @staticmethod
    def save_annotations(annotations: List[DefectAnnotation], file_path: str) -> bool:
        """
        保存标注到YOLO格式文件
        
        Args:
            annotations: 标注列表
            file_path: 保存文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 过滤有效标注
            valid_annotations = [ann for ann in annotations if ann.is_valid()]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入文件头注释
                f.write(f"# YOLO format annotations\n")
                f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total annotations: {len(valid_annotations)}\n")
                f.write(f"# Format: class_id x_center y_center width height\n")
                f.write(f"#\n")
                
                # 写入标注数据
                for annotation in valid_annotations:
                    f.write(annotation.to_yolo_format() + '\n')
                    
            return True
            
        except Exception as e:
            print(f"保存标注文件失败 {file_path}: {e}")
            return False
            
    @staticmethod
    def load_annotations(file_path: str) -> List[DefectAnnotation]:
        """
        从YOLO格式文件加载标注
        
        Args:
            file_path: 标注文件路径
            
        Returns:
            List[DefectAnnotation]: 标注列表
        """
        annotations = []
        
        if not os.path.exists(file_path):
            return annotations
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
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
    def get_annotation_file_path(image_path: str) -> str:
        """
        根据图像路径获取对应的标注文件路径
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            str: 标注文件路径
        """
        base_path = os.path.splitext(image_path)[0]
        return base_path + '.txt'
        
    @staticmethod
    def has_annotations(image_path: str) -> bool:
        """
        检查图像是否有对应的标注文件且包含有效标注

        Args:
            image_path: 图像文件路径

        Returns:
            bool: 是否存在有效标注
        """
        annotation_path = YOLOFileManager.get_annotation_file_path(image_path)

        if not os.path.exists(annotation_path) or os.path.getsize(annotation_path) == 0:
            return False

        # 检查是否有有效的标注行（非注释行）
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    # 找到有效的标注行
                    return True
            return False  # 只有注释行，没有有效标注
        except Exception:
            return False
        
    @staticmethod
    def validate_annotation_file(file_path: str) -> Tuple[bool, List[str]]:
        """
        验证YOLO标注文件格式
        
        Args:
            file_path: 标注文件路径
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        if not os.path.exists(file_path):
            errors.append(f"文件不存在: {file_path}")
            return False, errors
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                        
                    # 验证格式
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
                        
                        # 验证数值范围
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
        
    def batch_save_annotations(self, annotations_dict: Dict[str, List[DefectAnnotation]]) -> Dict[str, bool]:
        """
        批量保存标注文件
        
        Args:
            annotations_dict: {图像路径: 标注列表} 的字典
            
        Returns:
            Dict[str, bool]: {图像路径: 保存结果} 的字典
        """
        results = {}
        
        for image_path, annotations in annotations_dict.items():
            annotation_file = self.get_annotation_file_path(image_path)
            results[image_path] = self.save_annotations(annotations, annotation_file)
            
        return results
        
    def batch_load_annotations(self, image_paths: List[str]) -> Dict[str, List[DefectAnnotation]]:
        """
        批量加载标注文件
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            Dict[str, List[DefectAnnotation]]: {图像路径: 标注列表} 的字典
        """
        results = {}
        
        for image_path in image_paths:
            annotation_file = self.get_annotation_file_path(image_path)
            results[image_path] = self.load_annotations(annotation_file)
            
        return results
        
    def find_annotation_files(self, directory: str) -> List[str]:
        """
        查找目录下的所有标注文件
        
        Args:
            directory: 搜索目录
            
        Returns:
            List[str]: 标注文件路径列表
        """
        annotation_files = []
        
        try:
            for txt_file in Path(directory).rglob("*.txt"):
                if txt_file.is_file():
                    annotation_files.append(str(txt_file))
        except Exception as e:
            print(f"搜索标注文件失败 {directory}: {e}")
            
        return sorted(annotation_files)
        
    def find_orphaned_annotations(self, directory: str) -> List[str]:
        """
        查找没有对应图像文件的标注文件
        
        Args:
            directory: 搜索目录
            
        Returns:
            List[str]: 孤立标注文件路径列表
        """
        orphaned = []
        annotation_files = self.find_annotation_files(directory)
        
        for annotation_file in annotation_files:
            base_path = os.path.splitext(annotation_file)[0]
            
            # 检查是否存在对应的图像文件
            has_image = False
            for ext in self.SUPPORTED_IMAGE_EXTENSIONS:
                image_path = base_path + ext
                if os.path.exists(image_path):
                    has_image = True
                    break
                    
            if not has_image:
                orphaned.append(annotation_file)
                
        return orphaned
        
    def find_unannotated_images(self, directory: str) -> List[str]:
        """
        查找没有标注文件的图像
        
        Args:
            directory: 搜索目录
            
        Returns:
            List[str]: 未标注图像路径列表
        """
        unannotated = []
        
        try:
            for ext in self.SUPPORTED_IMAGE_EXTENSIONS:
                pattern = f"**/*{ext}"
                for image_file in Path(directory).rglob(pattern):
                    if image_file.is_file():
                        if not self.has_annotations(str(image_file)):
                            unannotated.append(str(image_file))
        except Exception as e:
            print(f"搜索未标注图像失败 {directory}: {e}")
            
        return sorted(unannotated)
        
    def get_annotation_statistics(self, directory: str) -> Dict:
        """
        获取目录下标注文件的统计信息
        
        Args:
            directory: 统计目录
            
        Returns:
            Dict: 统计信息
        """
        stats = {
            'total_annotation_files': 0,
            'total_annotations': 0,
            'annotations_by_class': {},
            'valid_files': 0,
            'invalid_files': 0,
            'orphaned_files': 0,
            'unannotated_images': 0
        }
        
        # 统计标注文件
        annotation_files = self.find_annotation_files(directory)
        stats['total_annotation_files'] = len(annotation_files)
        
        # 统计标注数量和类别分布
        for annotation_file in annotation_files:
            is_valid, _ = self.validate_annotation_file(annotation_file)
            
            if is_valid:
                stats['valid_files'] += 1
                annotations = self.load_annotations(annotation_file)
                stats['total_annotations'] += len(annotations)
                
                # 按类别统计
                for annotation in annotations:
                    class_id = annotation.defect_class
                    if class_id not in stats['annotations_by_class']:
                        stats['annotations_by_class'][class_id] = 0
                    stats['annotations_by_class'][class_id] += 1
            else:
                stats['invalid_files'] += 1
                
        # 统计孤立文件和未标注图像
        stats['orphaned_files'] = len(self.find_orphaned_annotations(directory))
        stats['unannotated_images'] = len(self.find_unannotated_images(directory))
        
        return stats
        
    def backup_annotations(self, source_dir: str, backup_dir: str) -> bool:
        """
        备份标注文件
        
        Args:
            source_dir: 源目录
            backup_dir: 备份目录
            
        Returns:
            bool: 备份是否成功
        """
        try:
            # 创建备份目录
            os.makedirs(backup_dir, exist_ok=True)
            
            # 复制所有标注文件
            annotation_files = self.find_annotation_files(source_dir)
            
            for annotation_file in annotation_files:
                # 计算相对路径
                rel_path = os.path.relpath(annotation_file, source_dir)
                backup_path = os.path.join(backup_dir, rel_path)
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(annotation_file, backup_path)
                
            return True
            
        except Exception as e:
            print(f"备份标注文件失败: {e}")
            return False


if __name__ == "__main__":
    # 简单测试
    print("🗂️ YOLO文件管理器测试")
    print("=" * 50)
    
    manager = YOLOFileManager()
    
    # 测试统计功能
    if os.path.exists("Data"):
        stats = manager.get_annotation_statistics("Data")
        print(f"📊 标注统计:")
        print(f"  标注文件总数: {stats['total_annotation_files']}")
        print(f"  标注总数: {stats['total_annotations']}")
        print(f"  有效文件: {stats['valid_files']}")
        print(f"  无效文件: {stats['invalid_files']}")
        print(f"  按类别分布: {stats['annotations_by_class']}")
    else:
        print("⚠️ Data目录不存在，跳过统计测试")
