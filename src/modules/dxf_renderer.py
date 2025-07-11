"""
DXF文件渲染和编号模块
提供DXF文件的可视化渲染和孔位编号功能
"""

import os
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import ezdxf
    from ezdxf.document import Drawing
    EZDXF_AVAILABLE = True
    DrawingType = Drawing
except ImportError:
    EZDXF_AVAILABLE = False
    DrawingType = object

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import Circle, Arc
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from dxf_import import get_dxf_importer, DXFHoleInfo, DXFAnalysisResult

@dataclass
class HoleAnnotation:
    """孔位标注信息"""
    hole: DXFHoleInfo
    number: int
    label: str
    label_position: Tuple[float, float]
    
@dataclass
class DXFRenderResult:
    """DXF渲染结果"""
    holes: List[DXFHoleInfo]
    annotations: List[HoleAnnotation]
    boundary_info: Dict
    rendered_image_path: Optional[str] = None
    hole_table_data: List[Dict] = None

class DXFRenderer:
    """DXF文件渲染器"""
    
    def __init__(self):
        self.dxf_importer = get_dxf_importer()
        self.hole_numbering_strategies = {
            'left_to_right': self._number_left_to_right,
            'top_to_bottom': self._number_top_to_bottom,
            'spiral': self._number_spiral,
            'distance_from_center': self._number_distance_from_center
        }
        
    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖库"""
        return {
            'ezdxf': EZDXF_AVAILABLE,
            'matplotlib': MATPLOTLIB_AVAILABLE
        }
    
    def render_dxf_with_numbering(self, dxf_file_path: str, 
                                numbering_strategy: str = 'left_to_right',
                                output_path: Optional[str] = None) -> DXFRenderResult:
        """渲染DXF文件并添加孔位编号"""
        
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf库未安装。请运行: pip install ezdxf")
        
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib库未安装。请运行: pip install matplotlib")
        
        # 1. 解析DXF文件
        analysis_result = self.dxf_importer.import_from_dxf(dxf_file_path)
        if not analysis_result:
            raise ValueError("DXF文件解析失败")
        
        # 2. 对孔位进行编号
        annotations = self._create_hole_annotations(
            analysis_result.holes, numbering_strategy
        )
        
        # 3. 渲染图形
        rendered_image_path = None
        if output_path:
            rendered_image_path = self._render_to_image(
                analysis_result, annotations, output_path
            )
        
        # 4. 生成孔位表数据
        hole_table_data = self._generate_hole_table(annotations)
        
        return DXFRenderResult(
            holes=analysis_result.holes,
            annotations=annotations,
            boundary_info=analysis_result.boundary_info,
            rendered_image_path=rendered_image_path,
            hole_table_data=hole_table_data
        )
    
    def _create_hole_annotations(self, holes: List[DXFHoleInfo], 
                               strategy: str) -> List[HoleAnnotation]:
        """创建孔位标注"""
        
        if strategy not in self.hole_numbering_strategies:
            strategy = 'left_to_right'
        
        # 使用指定策略对孔位排序
        numbering_func = self.hole_numbering_strategies[strategy]
        numbered_holes = numbering_func(holes)
        
        annotations = []
        for i, hole in enumerate(numbered_holes):
            # 计算标注位置（在孔的右上方）
            label_offset_x = hole.diameter * 0.6
            label_offset_y = hole.diameter * 0.6
            label_position = (
                hole.center_x + label_offset_x,
                hole.center_y + label_offset_y
            )
            
            annotation = HoleAnnotation(
                hole=hole,
                number=i + 1,
                label=f"H{i + 1:02d}",  # H01, H02, H03...
                label_position=label_position
            )
            annotations.append(annotation)
        
        return annotations
    
    def _number_left_to_right(self, holes: List[DXFHoleInfo]) -> List[DXFHoleInfo]:
        """从左到右编号"""
        return sorted(holes, key=lambda h: (h.center_x, h.center_y))
    
    def _number_top_to_bottom(self, holes: List[DXFHoleInfo]) -> List[DXFHoleInfo]:
        """从上到下编号"""
        return sorted(holes, key=lambda h: (-h.center_y, h.center_x))
    
    def _number_spiral(self, holes: List[DXFHoleInfo]) -> List[DXFHoleInfo]:
        """螺旋编号（从中心开始）"""
        if not holes:
            return holes
        
        # 计算中心点
        center_x = sum(h.center_x for h in holes) / len(holes)
        center_y = sum(h.center_y for h in holes) / len(holes)
        
        # 按距离中心的角度排序
        def spiral_key(hole):
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            # 螺旋排序：先按距离分层，再按角度
            return (int(distance / 50), angle)  # 50是分层间距
        
        return sorted(holes, key=spiral_key)
    
    def _number_distance_from_center(self, holes: List[DXFHoleInfo]) -> List[DXFHoleInfo]:
        """按距离中心的远近编号"""
        if not holes:
            return holes
        
        # 计算中心点
        center_x = sum(h.center_x for h in holes) / len(holes)
        center_y = sum(h.center_y for h in holes) / len(holes)
        
        # 按距离中心的距离排序
        def distance_key(hole):
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            return math.sqrt(dx*dx + dy*dy)
        
        return sorted(holes, key=distance_key)
    
    def _render_to_image(self, analysis_result: DXFAnalysisResult, 
                        annotations: List[HoleAnnotation], 
                        output_path: str) -> str:
        """渲染到图像文件"""
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # 设置坐标轴
        all_x = [h.center_x for h in analysis_result.holes]
        all_y = [h.center_y for h in analysis_result.holes]
        
        if all_x and all_y:
            margin = 50  # 边距
            x_min, x_max = min(all_x) - margin, max(all_x) + margin
            y_min, y_max = min(all_y) - margin, max(all_y) + margin
            
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
        
        # 绘制边界（如果有）
        if analysis_result.boundary_info.get('has_boundary'):
            boundary = analysis_result.boundary_info
            if boundary['boundary_type'] == 'circle':
                dims = boundary['dimensions']
                boundary_circle = Circle(
                    dims['center'], dims['radius'],
                    fill=False, color='gray', linewidth=2, linestyle='--'
                )
                ax.add_patch(boundary_circle)
        
        # 绘制孔位
        for annotation in annotations:
            hole = annotation.hole
            
            # 绘制孔位圆圈
            hole_circle = Circle(
                (hole.center_x, hole.center_y), hole.diameter/2,
                fill=False, color='blue', linewidth=2
            )
            ax.add_patch(hole_circle)
            
            # 绘制中心点
            ax.plot(hole.center_x, hole.center_y, 'bo', markersize=3)
            
            # 绘制编号标注
            ax.annotate(
                annotation.label,
                xy=(hole.center_x, hole.center_y),
                xytext=annotation.label_position,
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='red', lw=1)
            )
        
        # 设置图形属性
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X 坐标 (mm)')
        ax.set_ylabel('Y 坐标 (mm)')
        ax.set_title(f'DXF孔位图 - 共{len(annotations)}个孔')
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _generate_hole_table(self, annotations: List[HoleAnnotation]) -> List[Dict]:
        """生成孔位表数据"""
        table_data = []
        
        for annotation in annotations:
            hole = annotation.hole
            row = {
                '编号': annotation.label,
                '序号': annotation.number,
                'X坐标(mm)': round(hole.center_x, 3),
                'Y坐标(mm)': round(hole.center_y, 3),
                '直径(mm)': round(hole.diameter, 3),
                '孔类型': hole.hole_type,
                '位置': f"({hole.center_x:.1f}, {hole.center_y:.1f})"
            }
            table_data.append(row)
        
        return table_data
    
    def export_hole_data(self, render_result: DXFRenderResult, 
                        export_path: str, format: str = 'csv') -> str:
        """导出孔位数据"""
        
        if format.lower() == 'csv':
            return self._export_to_csv(render_result.hole_table_data, export_path)
        elif format.lower() == 'excel':
            return self._export_to_excel(render_result.hole_table_data, export_path)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_to_csv(self, table_data: List[Dict], export_path: str) -> str:
        """导出到CSV文件"""
        import csv
        
        if not export_path.endswith('.csv'):
            export_path += '.csv'
        
        if table_data:
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = table_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in table_data:
                    writer.writerow(row)
        
        return export_path
    
    def _export_to_excel(self, table_data: List[Dict], export_path: str) -> str:
        """导出到Excel文件"""
        try:
            import pandas as pd
            
            if not export_path.endswith('.xlsx'):
                export_path += '.xlsx'
            
            if table_data:
                df = pd.DataFrame(table_data)
                df.to_excel(export_path, index=False)
            
            return export_path
            
        except ImportError:
            raise ImportError("pandas库未安装。请运行: pip install pandas openpyxl")
    
    def create_numbered_dxf(self, original_dxf_path: str, 
                          output_dxf_path: str,
                          numbering_strategy: str = 'left_to_right') -> str:
        """创建带编号的DXF文件"""
        
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf库未安装")
        
        # 读取原DXF文件
        doc = ezdxf.readfile(original_dxf_path)
        
        # 解析和编号
        analysis_result = self.dxf_importer.import_from_dxf(original_dxf_path)
        annotations = self._create_hole_annotations(
            analysis_result.holes, numbering_strategy
        )
        
        # 在DXF中添加文本标注
        modelspace = doc.modelspace()
        
        for annotation in annotations:
            # 添加文本标注
            modelspace.add_text(
                annotation.label,
                dxfattribs={
                    'insert': annotation.label_position,
                    'height': annotation.hole.diameter * 0.3,  # 文字高度
                    'color': 1,  # 红色
                    'layer': 'HOLE_NUMBERS'
                }
            )
            
            # 添加引线（可选）
            modelspace.add_line(
                (annotation.hole.center_x, annotation.hole.center_y),
                annotation.label_position,
                dxfattribs={'color': 1, 'layer': 'HOLE_NUMBERS'}
            )
        
        # 保存新DXF文件
        doc.saveas(output_dxf_path)
        
        return output_dxf_path

# 单例实例
_dxf_renderer = None

def get_dxf_renderer():
    """获取DXF渲染器单例"""
    global _dxf_renderer
    if _dxf_renderer is None:
        _dxf_renderer = DXFRenderer()
    return _dxf_renderer