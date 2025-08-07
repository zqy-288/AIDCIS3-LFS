"""
图像扫描与管理模块
负责扫描Data/H{数字}/BISDM/result目录结构，提取孔ID和图像文件列表
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ImageInfo:
    """图像文件信息"""
    file_path: str          # 完整文件路径
    file_name: str          # 文件名
    hole_id: str           # 所属孔ID
    file_size: int         # 文件大小（字节）
    extension: str         # 文件扩展名
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.file_name:
            self.file_name = os.path.basename(self.file_path)
        if not self.extension:
            self.extension = os.path.splitext(self.file_path)[1].lower()


class ImageScanner:
    """图像扫描器 - 扫描指定目录结构，提取孔ID和图像文件列表"""
    
    # 支持的图像格式
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # 孔ID模式匹配（新格式：R开头，包含C）
    HOLE_ID_PATTERN = re.compile(r'^R\d+C\d+$')
    
    def __init__(self, base_path: str = "Data"):
        """
        初始化图像扫描器
        
        Args:
            base_path: 基础扫描路径，默认为"Data"
        """
        self.base_path = Path(base_path)
        self.hole_ids: Set[str] = set()
        self.images_by_hole: Dict[str, List[ImageInfo]] = {}
        self.all_images: List[ImageInfo] = []
        
    def scan_directories(self) -> bool:
        """
        扫描目录结构，查找所有孔ID和图像文件
        
        Returns:
            bool: 扫描是否成功
        """
        try:
            self._reset_data()
            
            if not self.base_path.exists():
                print(f"警告: 基础路径不存在: {self.base_path}")
                return False
                
            # 扫描所有新格式孔位目录（R开头且包含C）
            for item in self.base_path.iterdir():
                if item.is_dir() and self.HOLE_ID_PATTERN.match(item.name):
                    hole_id = item.name
                    self.hole_ids.add(hole_id)

                    # 扫描该孔ID下的图像文件
                    images = self._scan_hole_images(hole_id, item)
                    self.images_by_hole[hole_id] = images
                    self.all_images.extend(images)
                    
            print(f"扫描完成: 找到 {len(self.hole_ids)} 个孔位，{len(self.all_images)} 张图像")
            return True
            
        except Exception as e:
            print(f"扫描目录时出错: {e}")
            return False
            
    def _reset_data(self):
        """重置扫描数据"""
        self.hole_ids.clear()
        self.images_by_hole.clear()
        self.all_images.clear()
        
    def _scan_hole_images(self, hole_id: str, hole_dir: Path) -> List[ImageInfo]:
        """
        扫描指定孔位目录下的图像文件
        
        Args:
            hole_id: 孔位ID
            hole_dir: 孔位目录路径
            
        Returns:
            List[ImageInfo]: 图像文件信息列表
        """
        images = []
        
        # 查找BISDM/result目录
        bisdm_result_path = hole_dir / "BISDM" / "result"
        
        if bisdm_result_path.exists() and bisdm_result_path.is_dir():
            # 递归扫描BISDM/result目录下的所有图像文件
            for image_path in self._find_images_recursive(bisdm_result_path):
                try:
                    file_size = image_path.stat().st_size
                    image_info = ImageInfo(
                        file_path=str(image_path),
                        file_name=image_path.name,
                        hole_id=hole_id,
                        file_size=file_size,
                        extension=image_path.suffix.lower()
                    )
                    images.append(image_info)
                except Exception as e:
                    print(f"处理图像文件时出错 {image_path}: {e}")
                    
        else:
            print(f"警告: 孔位 {hole_id} 的BISDM/result目录不存在: {bisdm_result_path}")
            
        return images
        
    def _find_images_recursive(self, directory: Path) -> List[Path]:
        """
        递归查找目录下的所有图像文件
        
        Args:
            directory: 要搜索的目录
            
        Returns:
            List[Path]: 图像文件路径列表
        """
        image_files = []
        
        try:
            for item in directory.rglob("*"):
                if (item.is_file() and 
                    item.suffix.lower() in self.SUPPORTED_EXTENSIONS):
                    image_files.append(item)
        except Exception as e:
            print(f"递归搜索图像文件时出错 {directory}: {e}")
            
        return sorted(image_files)  # 按文件名排序
        
    def get_hole_ids(self) -> List[str]:
        """
        获取所有孔位ID列表
        
        Returns:
            List[str]: 排序后的孔位ID列表
        """
        return sorted(list(self.hole_ids))
        
    def get_images_for_hole(self, hole_id: str) -> List[ImageInfo]:
        """
        获取指定孔位的图像文件列表
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            List[ImageInfo]: 图像文件信息列表
        """
        return self.images_by_hole.get(hole_id, [])
        
    def get_all_images(self) -> List[ImageInfo]:
        """
        获取所有图像文件列表
        
        Returns:
            List[ImageInfo]: 所有图像文件信息列表
        """
        return self.all_images.copy()
        
    def has_images(self, hole_id: str) -> bool:
        """
        检查指定孔位是否有图像文件
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            bool: 是否有图像文件
        """
        return len(self.get_images_for_hole(hole_id)) > 0
        
    def get_image_count(self, hole_id: Optional[str] = None) -> int:
        """
        获取图像文件数量
        
        Args:
            hole_id: 孔位ID，如果为None则返回总数量
            
        Returns:
            int: 图像文件数量
        """
        if hole_id is None:
            return len(self.all_images)
        else:
            return len(self.get_images_for_hole(hole_id))
            
    def get_statistics(self) -> Dict[str, any]:
        """
        获取扫描统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_size = sum(img.file_size for img in self.all_images)
        
        # 按扩展名统计
        ext_count = {}
        for img in self.all_images:
            ext_count[img.extension] = ext_count.get(img.extension, 0) + 1
            
        # 按孔位统计
        hole_stats = {}
        for hole_id in self.hole_ids:
            images = self.get_images_for_hole(hole_id)
            hole_stats[hole_id] = {
                'count': len(images),
                'size': sum(img.file_size for img in images)
            }
            
        return {
            'total_holes': len(self.hole_ids),
            'total_images': len(self.all_images),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'extensions': ext_count,
            'holes': hole_stats
        }
        
    def find_image_by_name(self, image_name: str, hole_id: Optional[str] = None) -> Optional[ImageInfo]:
        """
        根据文件名查找图像
        
        Args:
            image_name: 图像文件名
            hole_id: 限制在指定孔位内搜索，如果为None则在所有图像中搜索
            
        Returns:
            Optional[ImageInfo]: 找到的图像信息，如果未找到则返回None
        """
        search_list = self.get_images_for_hole(hole_id) if hole_id else self.all_images
        
        for img in search_list:
            if img.file_name == image_name:
                return img
                
        return None
        
    def validate_image_file(self, file_path: str) -> bool:
        """
        验证图像文件是否有效
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            bool: 文件是否有效
        """
        try:
            path = Path(file_path)
            return (path.exists() and 
                    path.is_file() and 
                    path.suffix.lower() in self.SUPPORTED_EXTENSIONS and
                    path.stat().st_size > 0)
        except Exception:
            return False


if __name__ == "__main__":
    # 简单测试
    print("🔍 图像扫描器测试")
    print("=" * 50)
    
    scanner = ImageScanner()
    
    if scanner.scan_directories():
        stats = scanner.get_statistics()
        
        print(f"📊 扫描统计:")
        print(f"  孔位数量: {stats['total_holes']}")
        print(f"  图像总数: {stats['total_images']}")
        print(f"  总大小: {stats['total_size_mb']} MB")
        print(f"  支持格式: {list(stats['extensions'].keys())}")
        
        print(f"\n📁 孔位详情:")
        for hole_id in scanner.get_hole_ids():
            count = scanner.get_image_count(hole_id)
            print(f"  {hole_id}: {count} 张图像")
            
        # 显示第一个孔位的图像示例
        if scanner.get_hole_ids():
            first_hole = scanner.get_hole_ids()[0]
            images = scanner.get_images_for_hole(first_hole)
            if images:
                print(f"\n📷 {first_hole} 图像示例:")
                for i, img in enumerate(images[:3]):  # 只显示前3张
                    print(f"  {i+1}. {img.file_name} ({img.file_size} bytes)")
                    
    else:
        print("❌ 扫描失败")
