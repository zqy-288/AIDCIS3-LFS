"""
DXF文件导入模块
从DXF文件中提取产品信息，自动识别孔径、布局等信息
"""

import os
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

try:
    import ezdxf
    from ezdxf.document import Drawing
    from ezdxf.entities import Arc, Circle, Line, Polyline, LWPolyline
    EZDXF_AVAILABLE = True
    # 如果ezdxf不可用，定义一个占位符类型
    DrawingType = Drawing
except ImportError:
    EZDXF_AVAILABLE = False
    # 定义占位符类型
    DrawingType = object

from src.models.product_model import get_product_manager

@dataclass
class DXFHoleInfo:
    """DXF文件中的孔信息"""
    center_x: float
    center_y: float
    diameter: float
    hole_type: str = "standard"  # 孔类型: standard, mounting, reference等
    
    @property
    def position(self) -> Tuple[float, float]:
        """孔的位置坐标"""
        return (self.center_x, self.center_y)

@dataclass
class DXFAnalysisResult:
    """DXF文件分析结果"""
    holes: List[DXFHoleInfo]
    suggested_model_name: str
    standard_diameter: float
    tolerance_estimate: float
    boundary_info: Dict
    layer_info: Dict
    total_holes: int
    
    def get_diameter_statistics(self) -> Dict:
        """获取直径统计信息"""
        if not self.holes:
            return {}
        
        diameters = [hole.diameter for hole in self.holes]
        return {
            'min': min(diameters),
            'max': max(diameters),
            'mean': sum(diameters) / len(diameters),
            'count': len(diameters)
        }

class DXFImporter:
    """DXF文件导入器"""
    
    def __init__(self):
        self.product_manager = get_product_manager()
        self.tolerance_threshold = 0.5  # 直径差异阈值，用于分组
        
    def check_ezdxf_availability(self) -> bool:
        """检查ezdxf库是否可用"""
        return EZDXF_AVAILABLE
    
    def import_from_dxf(self, dxf_file_path: str) -> Optional[DXFAnalysisResult]:
        """从DXF文件导入产品信息"""
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf库未安装。请运行: pip install ezdxf")
        
        if not os.path.exists(dxf_file_path):
            raise FileNotFoundError(f"DXF文件不存在: {dxf_file_path}")
        
        try:
            # 打开DXF文件
            doc = ezdxf.readfile(dxf_file_path)
            
            # 分析文件内容
            analysis_result = self._analyze_dxf_content(doc, dxf_file_path)
            
            return analysis_result
            
        except Exception as e:
            raise ValueError(f"DXF文件解析失败: {str(e)}")
    
    def _analyze_dxf_content(self, doc: 'DrawingType', file_path: str) -> DXFAnalysisResult:
        """分析DXF文件内容"""
        modelspace = doc.modelspace()
        
        # 提取孔信息
        holes = self._extract_holes(modelspace)
        
        # 分析边界信息
        boundary_info = self._analyze_boundary(modelspace)
        
        # 分析图层信息
        layer_info = self._analyze_layers(doc)
        
        # 计算标准直径和公差
        standard_diameter, tolerance_estimate = self._calculate_standard_diameter(holes)
        
        # 生成建议的产品型号名称
        suggested_model_name = self._generate_model_name(file_path, holes, standard_diameter)
        
        return DXFAnalysisResult(
            holes=holes,
            suggested_model_name=suggested_model_name,
            standard_diameter=standard_diameter,
            tolerance_estimate=tolerance_estimate,
            boundary_info=boundary_info,
            layer_info=layer_info,
            total_holes=len(holes)
        )
    
    def _extract_holes(self, modelspace) -> List[DXFHoleInfo]:
        """提取DXF文件中的孔信息"""
        holes = []
        
        # 遍历所有实体
        for entity in modelspace:
            if entity.dxftype() == 'CIRCLE':
                # 圆形孔
                center = entity.dxf.center
                diameter = entity.dxf.radius * 2
                
                holes.append(DXFHoleInfo(
                    center_x=center.x,
                    center_y=center.y,
                    diameter=diameter,
                    hole_type="standard"
                ))
                
            elif entity.dxftype() == 'ARC':
                # 弧形（可能是部分圆）
                center = entity.dxf.center
                diameter = entity.dxf.radius * 2
                
                # 检查是否是完整圆（360度）
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                
                if abs(end_angle - start_angle) >= 359 or abs(end_angle - start_angle) <= 1:
                    # 近似完整圆
                    holes.append(DXFHoleInfo(
                        center_x=center.x,
                        center_y=center.y,
                        diameter=diameter,
                        hole_type="standard"
                    ))
        
        return holes
    
    def _analyze_boundary(self, modelspace) -> Dict:
        """分析边界信息"""
        boundary_info = {
            'has_boundary': False,
            'boundary_type': None,
            'dimensions': None
        }
        
        # 寻找边界线或边界圆
        for entity in modelspace:
            if entity.dxftype() == 'CIRCLE':
                # 可能是圆形边界
                if hasattr(entity, 'layer') and 'boundary' in entity.layer.lower():
                    boundary_info['has_boundary'] = True
                    boundary_info['boundary_type'] = 'circle'
                    boundary_info['dimensions'] = {
                        'radius': entity.dxf.radius,
                        'diameter': entity.dxf.radius * 2,
                        'center': (entity.dxf.center.x, entity.dxf.center.y)
                    }
                    break
        
        return boundary_info
    
    def _analyze_layers(self, doc: 'DrawingType') -> Dict:
        """分析图层信息"""
        layer_info = {}
        
        for layer in doc.layers:
            layer_info[layer.dxf.name] = {
                'color': layer.dxf.color,
                'linetype': layer.dxf.linetype,
                'lineweight': getattr(layer.dxf, 'lineweight', None)
            }
        
        return layer_info
    
    def _calculate_standard_diameter(self, holes: List[DXFHoleInfo]) -> Tuple[float, float]:
        """计算标准直径和公差估计"""
        if not holes:
            return 0.0, 0.0
        
        # 按直径分组
        diameter_groups = defaultdict(list)
        for hole in holes:
            # 四舍五入到最接近的0.1mm
            rounded_diameter = round(hole.diameter, 1)
            diameter_groups[rounded_diameter].append(hole)
        
        # 找到最大的组作为标准直径
        main_diameter = max(diameter_groups.keys(), key=lambda k: len(diameter_groups[k]))
        
        # 计算公差估计
        all_diameters = [hole.diameter for hole in holes]
        diameter_range = max(all_diameters) - min(all_diameters)
        tolerance_estimate = diameter_range / 2 if diameter_range > 0 else 0.05
        
        return main_diameter, tolerance_estimate
    
    def _generate_model_name(self, file_path: str, holes: List[DXFHoleInfo], 
                           standard_diameter: float) -> str:
        """生成建议的产品型号名称"""
        # 从文件名提取信息
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 清理文件名
        clean_name = file_name.replace(' ', '_').replace('-', '_')
        
        # 生成型号名称
        hole_count = len(holes)
        diameter_str = f"{standard_diameter:.0f}mm"
        
        # 格式: 文件名_直径_孔数量
        if hole_count > 0:
            suggested_name = f"{clean_name}_{diameter_str}_{hole_count}holes"
        else:
            suggested_name = f"{clean_name}_{diameter_str}"
        
        return suggested_name
    
    def create_product_from_dxf(self, analysis_result: DXFAnalysisResult, 
                              dxf_file_path: str, **kwargs) -> bool:
        """基于DXF分析结果创建产品型号"""
        try:
            # 获取用户自定义参数或使用默认值
            model_name = kwargs.get('model_name', analysis_result.suggested_model_name)
            model_code = kwargs.get('model_code', None)
            description = kwargs.get('description', 
                                   f"从DXF文件 '{os.path.basename(dxf_file_path)}' 导入的产品型号")
            
            # 设置公差
            tolerance = kwargs.get('tolerance', analysis_result.tolerance_estimate)
            tolerance_upper = kwargs.get('tolerance_upper', tolerance)
            tolerance_lower = kwargs.get('tolerance_lower', -tolerance)
            
            # 创建产品
            product = self.product_manager.create_product(
                model_name=model_name,
                model_code=model_code,
                standard_diameter=analysis_result.standard_diameter,
                tolerance_upper=tolerance_upper,
                tolerance_lower=tolerance_lower,
                description=description,
                dxf_file_path=dxf_file_path
            )
            
            return True
            
        except Exception as e:
            raise ValueError(f"创建产品失败: {str(e)}")
    
    def get_import_preview(self, dxf_file_path: str) -> Dict:
        """获取DXF导入预览信息"""
        if not EZDXF_AVAILABLE:
            return {'error': 'ezdxf库未安装'}
        
        try:
            analysis_result = self.import_from_dxf(dxf_file_path)
            
            if not analysis_result:
                return {'error': '无法分析DXF文件'}
            
            # 统计信息
            diameter_stats = analysis_result.get_diameter_statistics()
            
            return {
                'success': True,
                'file_path': dxf_file_path,
                'suggested_model_name': analysis_result.suggested_model_name,
                'standard_diameter': analysis_result.standard_diameter,
                'tolerance_estimate': analysis_result.tolerance_estimate,
                'total_holes': analysis_result.total_holes,
                'diameter_stats': diameter_stats,
                'boundary_info': analysis_result.boundary_info,
                'layer_count': len(analysis_result.layer_info)
            }
            
        except Exception as e:
            return {'error': str(e)}

# 单例实例
_dxf_importer = None

def get_dxf_importer():
    """获取DXF导入器单例"""
    global _dxf_importer
    if _dxf_importer is None:
        _dxf_importer = DXFImporter()
    return _dxf_importer