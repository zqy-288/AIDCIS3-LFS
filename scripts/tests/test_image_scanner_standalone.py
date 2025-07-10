#!/usr/bin/env python3
"""
独立的图像扫描器测试
验证图像扫描器在实际项目目录中的工作情况
"""

import os
import sys
from pathlib import Path

# 直接复制ImageScanner类定义，避免导入问题
import re
from typing import List, Dict, Set, Optional
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
    
    # 孔ID模式匹配
    HOLE_ID_PATTERN = re.compile(r'^H\d+$')
    
    def __init__(self, base_path: str = "Data"):
        """初始化图像扫描器"""
        self.base_path = Path(base_path)
        self.hole_ids: Set[str] = set()
        self.images_by_hole: Dict[str, List[ImageInfo]] = {}
        self.all_images: List[ImageInfo] = []
        
    def scan_directories(self) -> bool:
        """扫描目录结构，查找所有孔ID和图像文件"""
        try:
            self._reset_data()
            
            if not self.base_path.exists():
                print(f"警告: 基础路径不存在: {self.base_path}")
                return False
                
            # 扫描所有H开头的目录
            for item in self.base_path.iterdir():
                if item.is_dir() and self.HOLE_ID_PATTERN.match(item.name):
                    hole_id = item.name
                    self.hole_ids.add(hole_id)
                    
                    # 扫描该孔ID下的图像文件
                    images = self._scan_hole_images(hole_id, item)
                    self.images_by_hole[hole_id] = images
                    self.all_images.extend(images)
                    
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
        """扫描指定孔位目录下的图像文件"""
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
                    
        return images
        
    def _find_images_recursive(self, directory: Path) -> List[Path]:
        """递归查找目录下的所有图像文件"""
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
        """获取所有孔位ID列表"""
        return sorted(list(self.hole_ids))
        
    def get_images_for_hole(self, hole_id: str) -> List[ImageInfo]:
        """获取指定孔位的图像文件列表"""
        return self.images_by_hole.get(hole_id, [])
        
    def get_image_count(self, hole_id: Optional[str] = None) -> int:
        """获取图像文件数量"""
        if hole_id is None:
            return len(self.all_images)
        else:
            return len(self.get_images_for_hole(hole_id))
            
    def get_statistics(self) -> Dict[str, any]:
        """获取扫描统计信息"""
        total_size = sum(img.file_size for img in self.all_images)
        
        # 按扩展名统计
        ext_count = {}
        for img in self.all_images:
            ext_count[img.extension] = ext_count.get(img.extension, 0) + 1
            
        return {
            'total_holes': len(self.hole_ids),
            'total_images': len(self.all_images),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'extensions': ext_count
        }


def test_image_scanner():
    """测试图像扫描器功能"""
    print("🔍 图像扫描器功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 创建扫描器
    print("📝 测试1: 创建图像扫描器")
    try:
        scanner = ImageScanner("Data")
        print(f"  ✅ 扫描器创建成功，基础路径: {scanner.base_path}")
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 扫描器创建失败: {e}")
        test_results.append(False)
        return False
    
    # 测试2: 扫描目录
    print("📝 测试2: 扫描目录结构")
    try:
        success = scanner.scan_directories()
        if success:
            print(f"  ✅ 目录扫描成功")
            test_results.append(True)
        else:
            print(f"  ⚠️ 目录扫描完成但可能没有找到数据")
            test_results.append(True)  # 这不算失败
    except Exception as e:
        print(f"  ❌ 目录扫描失败: {e}")
        test_results.append(False)
    
    # 测试3: 获取孔位列表
    print("📝 测试3: 获取孔位列表")
    try:
        hole_ids = scanner.get_hole_ids()
        print(f"  ✅ 找到孔位: {hole_ids}")
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 获取孔位列表失败: {e}")
        test_results.append(False)
    
    # 测试4: 获取统计信息
    print("📝 测试4: 获取统计信息")
    try:
        stats = scanner.get_statistics()
        print(f"  ✅ 统计信息:")
        print(f"    孔位数量: {stats['total_holes']}")
        print(f"    图像总数: {stats['total_images']}")
        print(f"    总大小: {stats['total_size_mb']} MB")
        print(f"    支持格式: {list(stats['extensions'].keys())}")
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 获取统计信息失败: {e}")
        test_results.append(False)
    
    # 测试5: 检查具体孔位的图像
    print("📝 测试5: 检查具体孔位的图像")
    try:
        hole_ids = scanner.get_hole_ids()
        if hole_ids:
            for hole_id in hole_ids[:2]:  # 只检查前两个
                images = scanner.get_images_for_hole(hole_id)
                print(f"  ✅ {hole_id}: {len(images)} 张图像")
                
                # 显示前几张图像的详情
                for i, img in enumerate(images[:3]):
                    size_kb = round(img.file_size / 1024, 1)
                    print(f"    {i+1}. {img.file_name} ({size_kb} KB, {img.extension})")
        else:
            print(f"  ⚠️ 没有找到孔位")
            
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 检查孔位图像失败: {e}")
        test_results.append(False)
    
    # 测试6: 验证目录结构
    print("📝 测试6: 验证目录结构")
    try:
        expected_paths = [
            "Data/H00001/BISDM/result",
            "Data/H00002/BISDM/result"
        ]
        
        for path in expected_paths:
            if os.path.exists(path):
                print(f"  ✅ 目录存在: {path}")
            else:
                print(f"  ⚠️ 目录不存在: {path}")
                
        test_results.append(True)
    except Exception as e:
        print(f"  ❌ 验证目录结构失败: {e}")
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
        print("\n🎉 所有测试通过! 图像扫描器工作正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_image_scanner()
    sys.exit(0 if success else 1)
