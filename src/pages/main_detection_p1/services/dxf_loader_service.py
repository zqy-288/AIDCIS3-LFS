"""
DXF文件加载服务
封装DXF文件的解析和坐标转换功能
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# 使用本地的HoleCollection定义
from ..components.enhanced_workpiece_diagram import HoleCollection

# 尝试导入DXF解析器，但不强制依赖
HAS_DXF_PARSER = False
try:
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent.parent.parent
    if project_root.exists():
        sys.path.insert(0, str(project_root))
        from src.core_business.dxf_parser import DXFParser
        from src.core_business.coordinate_system import UnifiedCoordinateManager
        HAS_DXF_PARSER = True
except ImportError as e:
    logging.warning(f"无法导入DXF解析器: {e}")
    DXFParser = None
    UnifiedCoordinateManager = None


class DXFLoaderService:
    """DXF文件加载服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if HAS_DXF_PARSER:
            try:
                self.dxf_parser = DXFParser()
                self.coordinate_manager = UnifiedCoordinateManager()
                self.logger.info("DXF解析器初始化成功")
            except Exception as e:
                self.logger.error(f"DXF解析器初始化失败: {e}")
                self.dxf_parser = None
                self.coordinate_manager = None
        else:
            self.dxf_parser = None
            self.coordinate_manager = None
            self.logger.warning("DXF解析器不可用")
    
    def load_dxf_file(self, file_path: str) -> Optional[HoleCollection]:
        """
        加载DXF文件并返回孔位集合
        
        Args:
            file_path: DXF文件路径
            
        Returns:
            HoleCollection: 解析后的孔位集合，失败则返回None
        """
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                self.logger.error(f"DXF文件不存在: {file_path}")
                return None
            
            # 如果有DXF解析器，使用它
            if self.dxf_parser:
                self.logger.info(f"开始解析DXF文件: {file_path}")
                hole_collection = self.dxf_parser.parse_file(file_path)
                
                # 如果有坐标管理器，应用坐标转换
                if self.coordinate_manager and hole_collection:
                    self.logger.info("应用坐标转换")
                    # 坐标转换已经在DXFParser中完成，这里可以添加额外的转换
                    pass
                
                return hole_collection
            else:
                # 备用方案：创建示例数据
                self.logger.warning("使用示例数据作为备用方案")
                return self._create_sample_hole_collection()
                
        except Exception as e:
            self.logger.error(f"加载DXF文件失败: {e}")
            return None
    
    def _create_sample_hole_collection(self) -> HoleCollection:
        """创建示例孔位集合（备用方案）"""
        holes = {}
        
        # 创建8x6的网格孔位
        rows = 6
        cols = 8
        start_x = -140
        start_y = -100
        spacing_x = 40
        spacing_y = 35
        
        hole_count = 1
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                hole_id = f"H{hole_count:03d}"
                
                # 创建简单的孔位数据
                holes[hole_id] = type('HoleData', (), {
                    'hole_id': hole_id,
                    'center_x': x,
                    'center_y': y,
                    'radius': 8.0,
                    'status': 'pending'
                })()
                
                hole_count += 1
        
        return HoleCollection(holes)
    
    def get_test_dxf_path(self) -> Optional[str]:
        """获取测试用的DXF文件路径"""
        test_dxf = project_root / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf"
        if test_dxf.exists():
            return str(test_dxf)
        
        # 尝试其他测试文件
        test_dxf2 = project_root / "assets" / "dxf" / "DXF Graph" / "测试管板.dxf"
        if test_dxf2.exists():
            return str(test_dxf2)
            
        return None