"""
统一路径配置模块
为AIDCIS3-LFS系统提供统一的路径解析和管理策略
"""

import os
from pathlib import Path
from typing import Optional, Union, Dict, List
from enum import Enum


class PathType(Enum):
    """路径类型枚举"""
    DATA = "data"
    CSV = "csv"
    IMAGE = "image"
    BISDM = "bisdm"
    CCIDM = "ccidm"
    RESULT = "result"
    CONFIG = "config"
    LOG = "log"


class PathConfig:
    """统一路径配置管理器"""
    
    # 默认路径配置
    DEFAULT_PATHS = {
        PathType.DATA: "Data",
        PathType.CONFIG: "config",
        PathType.LOG: "logs"
    }
    
    # 孔位子目录结构
    HOLE_SUBDIRS = {
        PathType.BISDM: "BISDM",
        PathType.CCIDM: "CCIDM",
        PathType.RESULT: "result"
    }
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        初始化路径配置管理器
        
        Args:
            project_root: 项目根目录，如果为None则自动检测
        """
        self._project_root = self._resolve_project_root(project_root)
        self._path_cache: Dict[str, Path] = {}
        
    def _resolve_project_root(self, project_root: Optional[Union[str, Path]] = None) -> Path:
        """
        解析项目根目录
        
        Args:
            project_root: 指定的项目根目录
            
        Returns:
            Path: 解析后的项目根目录路径
        """
        if project_root:
            return Path(project_root).resolve()
        
        # 自动检测项目根目录
        # 从当前文件位置开始，向上查找项目根目录
        current_dir = Path(__file__).parent
        
        # 项目根目录标识文件/目录
        project_markers = [
            "Data",     # 数据目录 
            "src",      # 源代码目录
            "config",   # 配置目录
            "requirements.txt",
            "setup.py",
            ".git"
        ]
        
        # 向上查找包含项目标识的目录
        for parent in [current_dir] + list(current_dir.parents):
            # 检查是否包含多个项目标识（更可靠的检测）
            marker_count = sum(1 for marker in project_markers if (parent / marker).exists())
            
            # 如果找到包含Data和src的目录，需要进一步验证
            if (parent / "Data").exists() and (parent / "src").exists():
                # 验证Data目录是否包含实际的孔位数据（而不是其他文件）
                data_dir = parent / "Data"
                has_holes = any(item.is_dir() and item.name.startswith(('C', 'H')) for item in data_dir.iterdir())
                
                if has_holes:
                    return parent
                    
            # 如果找到包含至少3个标识的目录，很可能是项目根目录
            if marker_count >= 3:
                return parent
        
        # 如果没有找到明确的项目根目录，使用当前工作目录
        return Path.cwd()
    
    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return self._project_root
    
    def get_base_path(self, path_type: PathType) -> Path:
        """
        获取基础路径
        
        Args:
            path_type: 路径类型
            
        Returns:
            Path: 基础路径
        """
        cache_key = f"base_{path_type.value}"
        
        if cache_key not in self._path_cache:
            relative_path = self.DEFAULT_PATHS.get(path_type, path_type.value)
            absolute_path = self._project_root / relative_path
            self._path_cache[cache_key] = absolute_path
            
        return self._path_cache[cache_key]
    
    def get_hole_path(self, hole_id: str, subdir_type: Optional[PathType] = None) -> Path:
        """
        获取孔位路径
        
        Args:
            hole_id: 孔位ID
            subdir_type: 子目录类型 (BISDM, CCIDM, RESULT等)
            
        Returns:
            Path: 孔位路径
        """
        cache_key = f"hole_{hole_id}_{subdir_type.value if subdir_type else 'base'}"
        
        if cache_key not in self._path_cache:
            data_path = self.get_base_path(PathType.DATA)
            hole_path = data_path / hole_id
            
            if subdir_type and subdir_type in self.HOLE_SUBDIRS:
                hole_path = hole_path / self.HOLE_SUBDIRS[subdir_type]
                
                # 如果是BISDM类型，还需要添加result子目录
                if subdir_type == PathType.BISDM:
                    hole_path = hole_path / self.HOLE_SUBDIRS[PathType.RESULT]
            
            self._path_cache[cache_key] = hole_path
            
        return self._path_cache[cache_key]
    
    def get_csv_path(self, hole_id: str) -> Path:
        """
        获取孔位CSV数据路径
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Path: CSV数据路径
        """
        return self.get_hole_path(hole_id, PathType.CCIDM)
    
    def get_image_path(self, hole_id: str) -> Path:
        """
        获取孔位图像路径
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Path: 图像路径
        """
        return self.get_hole_path(hole_id, PathType.BISDM)
    
    def ensure_path_exists(self, path: Union[str, Path], create_if_missing: bool = False) -> bool:
        """
        确保路径存在
        
        Args:
            path: 要检查的路径
            create_if_missing: 如果路径不存在是否创建
            
        Returns:
            bool: 路径是否存在
        """
        path_obj = Path(path)
        
        if path_obj.exists():
            return True
        
        if create_if_missing:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                return True
            except Exception as e:
                print(f"⚠️ 创建路径失败 {path}: {e}")
                return False
        
        return False
    
    def find_csv_files(self, hole_id: str) -> List[Path]:
        """
        查找孔位的CSV文件
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            List[Path]: CSV文件路径列表
        """
        csv_path = self.get_csv_path(hole_id)
        
        if not csv_path.exists():
            return []
        
        return [f for f in csv_path.iterdir() if f.suffix.lower() == '.csv']
    
    def find_image_files(self, hole_id: str, extensions: Optional[List[str]] = None) -> List[Path]:
        """
        查找孔位的图像文件
        
        Args:
            hole_id: 孔位ID
            extensions: 支持的图像扩展名列表
            
        Returns:
            List[Path]: 图像文件路径列表
        """
        if extensions is None:
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        image_path = self.get_image_path(hole_id)
        
        if not image_path.exists():
            return []
        
        image_files = []
        for ext in extensions:
            image_files.extend(image_path.rglob(f"*{ext}"))
            image_files.extend(image_path.rglob(f"*{ext.upper()}"))
        
        return sorted(image_files)
    
    def get_all_hole_ids(self) -> List[str]:
        """
        获取所有孔位ID，排除非孔位目录
        
        Returns:
            List[str]: 孔位ID列表
        """
        data_path = self.get_base_path(PathType.DATA)
        
        if not data_path.exists():
            return []
        
        hole_ids = []
        for item in data_path.iterdir():
            if item.is_dir():
                # 排除明显不是孔位的目录
                if item.name not in ['Products', '.git', '__pycache__', 'repositories', 'templates']:
                    hole_ids.append(item.name)
        
        return sorted(hole_ids)
    
    def validate_hole_structure(self, hole_id: str) -> Dict[str, bool]:
        """
        验证孔位目录结构
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Dict[str, bool]: 验证结果字典
        """
        result = {
            'hole_dir': False,
            'bisdm_dir': False,
            'ccidm_dir': False,
            'result_dir': False,
            'has_csv': False,
            'has_images': False
        }
        
        hole_path = self.get_hole_path(hole_id)
        result['hole_dir'] = hole_path.exists()
        
        if not result['hole_dir']:
            return result
        
        bisdm_path = hole_path / self.HOLE_SUBDIRS[PathType.BISDM]
        ccidm_path = hole_path / self.HOLE_SUBDIRS[PathType.CCIDM]
        result_path = bisdm_path / self.HOLE_SUBDIRS[PathType.RESULT]
        
        result['bisdm_dir'] = bisdm_path.exists()
        result['ccidm_dir'] = ccidm_path.exists()
        result['result_dir'] = result_path.exists()
        
        # 检查CSV文件
        if result['ccidm_dir']:
            csv_files = self.find_csv_files(hole_id)
            result['has_csv'] = len(csv_files) > 0
        
        # 检查图像文件
        if result['result_dir']:
            image_files = self.find_image_files(hole_id)
            result['has_images'] = len(image_files) > 0
        
        return result
    
    def clear_cache(self):
        """清除路径缓存"""
        self._path_cache.clear()
    
    def __str__(self) -> str:
        return f"PathConfig(project_root={self._project_root})"
    
    def __repr__(self) -> str:
        return f"PathConfig(project_root='{self._project_root}')"


# 全局路径配置实例
_global_path_config: Optional[PathConfig] = None


def get_path_config() -> PathConfig:
    """
    获取全局路径配置实例
    
    Returns:
        PathConfig: 路径配置实例
    """
    global _global_path_config
    
    if _global_path_config is None:
        _global_path_config = PathConfig()
    
    return _global_path_config


def set_path_config(config: PathConfig):
    """
    设置全局路径配置实例
    
    Args:
        config: 路径配置实例
    """
    global _global_path_config
    _global_path_config = config


# 便捷函数
def get_project_root() -> Path:
    """获取项目根目录"""
    return get_path_config().project_root


def get_data_path() -> Path:
    """获取数据目录路径"""
    return get_path_config().get_base_path(PathType.DATA)


def get_hole_csv_path(hole_id: str) -> Path:
    """获取孔位CSV路径"""
    return get_path_config().get_csv_path(hole_id)


def get_hole_image_path(hole_id: str) -> Path:
    """获取孔位图像路径"""
    return get_path_config().get_image_path(hole_id)


def validate_data_structure() -> Dict[str, any]:
    """
    验证整个数据结构
    
    Returns:
        Dict: 验证结果
    """
    config = get_path_config()
    data_path = config.get_base_path(PathType.DATA)
    
    result = {
        'data_dir_exists': data_path.exists(),
        'hole_count': 0,
        'valid_holes': 0,
        'holes': {}
    }
    
    if not result['data_dir_exists']:
        return result
    
    hole_ids = config.get_all_hole_ids()
    result['hole_count'] = len(hole_ids)
    
    for hole_id in hole_ids:
        validation = config.validate_hole_structure(hole_id)
        result['holes'][hole_id] = validation
        
        if validation['hole_dir'] and (validation['has_csv'] or validation['has_images']):
            result['valid_holes'] += 1
    
    return result


if __name__ == "__main__":
    # 简单测试
    print("🔍 路径配置测试")
    print("=" * 50)
    
    config = PathConfig()
    print(f"项目根目录: {config.project_root}")
    print(f"数据目录: {config.get_base_path(PathType.DATA)}")
    
    # 验证数据结构
    validation = validate_data_structure()
    print(f"\n📊 数据结构验证:")
    print(f"  数据目录存在: {validation['data_dir_exists']}")
    print(f"  孔位总数: {validation['hole_count']}")
    print(f"  有效孔位: {validation['valid_holes']}")
    
    # 显示前几个孔位的详细信息
    hole_ids = list(validation['holes'].keys())[:3]
    for hole_id in hole_ids:
        info = validation['holes'][hole_id]
        print(f"\n  {hole_id}:")
        print(f"    孔位目录: {'✅' if info['hole_dir'] else '❌'}")
        print(f"    BISDM目录: {'✅' if info['bisdm_dir'] else '❌'}")
        print(f"    CCIDM目录: {'✅' if info['ccidm_dir'] else '❌'}")
        print(f"    Result目录: {'✅' if info['result_dir'] else '❌'}")
        print(f"    CSV文件: {'✅' if info['has_csv'] else '❌'}")
        print(f"    图像文件: {'✅' if info['has_images'] else '❌'}")